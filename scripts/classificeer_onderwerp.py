#!/usr/bin/env python3
"""Eenmalig hulpscript: zet de relevantie-as (sources.onderwerp) van alle bronnen,
en corrigeert en passant 8 reliability-klassen die niet bij hun brontype pasten.

Classificeren is reviewer-werk (PATCH /api/sources/<id>/classificatie, @require_user('reviewer'))
en mensenwerk — Claude Code mag het niet doen en niet met jouw token authenticeren. Daarom is dit
een client die JIJ draait onder je eigen account: het leest data/tokens/maxime.token en praat met
de draaiende server (python3 server.py). Attributie + edit_log volgen zo je eigen gebruiker.

Rubriek (scoring.py RELEVANTIE_FACTOR):
  nl_systeem  ×1,15 — over het Nederlandse mediasysteem/-context (NL media, politiek, recht, elite)
  algemeen    ×1,00 — landneutraal raamwerk/theorie of internationaal kader (bv. Manufacturing Consent)
  buitenlands ×0,85 — over een specifiek buitenlands(e) systeem/casus (VS, VK, Hongarije, EU-event, …)
  onbepaald   ×1,00 — onbepaald (we zetten dit nergens; alles krijgt een oordeel)

Let op: de endpoint hervalideert de bestaande reliability (validation.klasse_consistentie). Bronnen
waarvan de reliability nú al inconsistent is (vindplaats mist bij een hoge klasse, of klasse past niet
bij het brontype) worden door de poort geweigerd (400). Dit script slaat die over en rapporteert ze,
zodat je eerst hun reliability/vindplaats kunt repareren.

Gebruik:   python3 scripts/classificeer_onderwerp.py            # voer uit
           python3 scripts/classificeer_onderwerp.py --dry-run  # toon alleen wat het zou doen
"""
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "propaganda_model.db"
TOKEN_FILE = ROOT / "data" / "tokens" / "maxime.token"
BASE = "http://localhost:5000"

# Expliciete oordelen; al het overige is nl_systeem (NL media/politiek/recht/elite — de NL-casus).
BUITENLANDS = {
    19,  # US House Judiciary — Foreign Censorship Threat (VS)
    39,  # BBC — What is the Great Reset (VK; buiten de EU sinds Brexit)
    92,  # CEU verdreven uit Hongarije (binnenlandse casus; set met #93/#94)
    93,  # Brazilië/Bolsonaro — humanities
    94,  # DeSantis/Florida — SB 266
}
ALGEMEEN = {
    2,   # Manufacturing Consent — het landneutrale raamwerk zelf
    18,  # GIFCT — Borderline Content (mondiaal moderatiekader)
    20,  # Brussels Signal — big tech & EU-verkiezingen (EU-niveau; NL is deel van de EU)
    22,  # Positive Money — EIB-obligaties / Eurosystem (EU-instituties)
    23,  # Central Banking — BlackRock ESG / Europese Ombudsman (EU-instituties)
    35,  # Sendai Framework (UN, mondiaal kader)
    36,  # OECD — Building back better (internationaal kader)
    37,  # WEF — Great Reset (mondiaal elitekader)
    40,  # El-Erian — New Normal in Industrial Countries (landneutrale macro)
    42,  # WHO/Europe — Pan-European Commission Climate & Health (internationaal)
    46,  # BMJ — exaggeration in health science news (algemene methode)
    48,  # Hallin — Uncensored War (drie sferen; theorie, VS-data)
    49,  # Chomsky — The Common Good (spectrum van toegestane opinie)
    53,  # Galtung & Ruge — Structure of Foreign News (nieuwswaarden-theorie)
    54,  # Harcup & O'Neill — News values revisited (theorie, VK-data)
    55,  # Bennett — Press-State Relations (indexing-hypothese, VS-data)
    56,  # Vliegenthart & Walgrave — intermedia agenda-setting (methode, BE-data)
    58,  # Baker — Advertising and a Democratic Press (theorie)
    59,  # Hall e.a. — Policing the Crisis (primary definers; theorie, VK-data)
    60,  # Nechushtai — infrastructural capture (theorie)
    61,  # Gans — Deciding What's News (bron-journalist-tango; theorie, VS-data)
    62,  # Jacobs & Townsley — Space of Opinion (theorie, VS-data)
    63,  # Entman — Cascading Activation (frame-theorie, VS-data)
}


# Reliability-correcties: bronnen waarvan de huidige klasse niet bij het brontype paste.
# We zetten de klasse die wél bij het type past (zie validation.TYPE_PER_KLASSE). Vindplaatsen
# voor de hoge klassen zijn vooraf toegevoegd (POST /api/sources/<id>/locations), dus de poort
# laat deze nu door. Aparte score-impact staat in de begeleidende toelichting.
RELIABILITY_FIX = {
    7:  "primair",        # persbericht (EIB) — origineel document van de uitgever
    12: "primair",        # persbericht (ACM-eindmededeling) — officieel besluit
    13: "primair",        # persbericht (EIB) — origineel document
    26: "primair",        # persbericht (Min. Financiën / KLM-Kamerbrief) — primair overheidsdoc
    37: "opinie",         # website (WEF/Schwab) — agenda-essay, geen 'primair'-website toegestaan
    # #49 niet meer hier: brontype is gecorrigeerd naar 'interview' (migrate_fix_bron_metadata.py),
    #     waardoor 'primair' geldig blijft — een interviewbundel is een primaire bron.
    66: "institutioneel", # rapport (ECHR-griffie) — 'primair' mag niet bij rapport
    70: "institutioneel", # rapport (WoJS-landenrapport) — 'academisch' mag niet bij rapport
}


def onderwerp_voor(sid: int) -> str:
    if sid in BUITENLANDS:
        return "buitenlands"
    if sid in ALGEMEEN:
        return "algemeen"
    return "nl_systeem"


def main():
    dry = "--dry-run" in sys.argv
    token = TOKEN_FILE.read_text().strip()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, title, onderwerp, reliability FROM sources ORDER BY id").fetchall()
    conn.close()

    ok, geblokkeerd, ongewijzigd, fout = [], [], [], []
    for r in rows:
        sid, doel = r["id"], onderwerp_voor(r["id"])
        fix_rel = RELIABILITY_FIX.get(sid)
        ond_klaar = r["onderwerp"] == doel
        rel_klaar = fix_rel is None or r["reliability"] == fix_rel
        if ond_klaar and rel_klaar:
            ongewijzigd.append(sid)
            continue
        # toon onderwerp + (eventueel) de reliability-correctie
        label = doel if not fix_rel else f"{doel} + rel={fix_rel}"
        if dry:
            ok.append((sid, label, r["title"][:55]))
            continue
        payload = {"onderwerp": doel,
                   "motivatie": "relevantie-as gezet (batch onderwerp-classificatie)"}
        if fix_rel:
            payload["reliability"] = fix_rel
            payload["motivatie"] = ("relevantie-as + reliability gecorrigeerd "
                                    f"(klasse paste niet bij brontype -> {fix_rel})")
        body = json.dumps(payload).encode()
        req = urllib.request.Request(f"{BASE}/api/sources/{sid}/classificatie",
                                     data=body, headers=headers, method="PATCH")
        try:
            urllib.request.urlopen(req)
            ok.append((sid, label, r["title"][:55]))
        except urllib.error.HTTPError as e:
            msg = e.read().decode()
            try:
                msg = json.loads(msg).get("error", msg)
            except Exception:
                pass
            (geblokkeerd if e.code == 400 else fout).append((sid, label, r["title"][:55], e.code, msg))

    label = "ZOU ZETTEN" if dry else "GEZET"
    print(f"\n== {label} ({len(ok)}) ==")
    for sid, doel, titel in ok:
        print(f"  #{sid:<3} -> {doel:<11} {titel}")
    if ongewijzigd:
        print(f"\n== AL GOED, overgeslagen ({len(ongewijzigd)}): {ongewijzigd}")
    if geblokkeerd:
        print(f"\n== GEBLOKKEERD door reliability-poort ({len(geblokkeerd)}) — repareer eerst "
              "reliability/vindplaats ==")
        for sid, doel, titel, code, msg in geblokkeerd:
            print(f"  #{sid:<3} -> {doel:<11} {titel}\n        {msg}")
    if fout:
        print(f"\n== ONVERWACHTE FOUT ({len(fout)}) ==")
        for sid, doel, titel, code, msg in fout:
            print(f"  #{sid:<3} [{code}] {titel}: {msg}")
    print()


if __name__ == "__main__":
    main()
