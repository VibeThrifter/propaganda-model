#!/usr/bin/env python3
"""Datamigratie "instituut of persoon" (eigenaarsbesluit 2026-10-19): het bestaande bewijs naar het
verband waar het hoort.

Het onderzoek van 2026-10-16 vond van de 146 goedgekeurde verbanden organisatie → medium met een
expert- of bronmechanisme er 56 waarvan (een deel van) het bewijs over een optreden van één
medewerker ging (Clingendael: 5 van de 6), zes keer hetzelfde optreden op een instituuts- én een
persoonsverband, en drie instituutsverbanden gedragen door een oud-medewerker of een andere pet. De
regel (DOCUMENTATIE.md § "Instituut of persoon"): wie is de bron van de uitspraak? Spreekt het
instituut zelf (rapport, cijfers, standpunt, partnerschap, of iemand die namens het instituut
spreekt), dan instituut → medium; geeft een persoon eigen duiding met het instituut als herkomst,
dan persoon → medium met namens_id = het instituut; een oud-medewerker of andere pet: persoon →
medium zonder namens_id. Eén optreden, één verband.

De beslissing per argument staat hieronder als data (handmatig beoordeeld op 2026-10-19, op de
eigen bewering en bron van elk argument). Twee wegen:

1. Direct, gelogd onder `assistent` (backup + de lock van de uurronde), alleen wat al door
   goedgekeurd bewijs gedragen wordt:
   a. de hoedanigheid (namens_id) op bestaande persoonsverbanden waarvan het eigen bewijs de
      organisatie als herkomst noemt;
   b. mechanismen: persoon → medium met `expert_framing` (een denktankmechanisme) wordt
      `expert_legitimatie`; de band persoon — universiteit met `denktank_levert_expert` wordt
      `academische_autoriteit`;
   c. een oprichtingsjaar als begin van een instituutsverband dat blijft: het begin van dít verband
      is onbekend (looptijdregel 2026-10-09), dus leeg; de datumzoeker zoekt het;
   d. argument #10514 (het AD als mediapartner van de Clingendael Buitenland Barometer) terug naar
      'voorgesteld': het werd verworpen omdat de bron drie keer HTTP 429 gaf, geen inhoudelijk
      oordeel.
2. Via de API onder `assistent` (bijdrager): alles landt 'voorgesteld' en doorloopt de gewone
   controles (bronchecker, smaadtoets, stemtoets, aanklager). Nieuwe personen, hun band met het
   instituut, het verband persoon → medium met namens_id, en elk optreden opnieuw als argument met
   dezelfde bron en reasoning "Overgezet van #<oud> …". Voor wie namens het instituut spreekt
   (CBS-hoofdeconoom, DNB-president, …) andersom, naar instituut → medium. Stap 10e van de uurronde
   vervangt het oude argument zodra de nieuwe route goedgekeurd is en wijst het oude verband af als
   het daarna niets meer draagt. Weigert de API het nieuwe argument als bijna-dubbel (409: hetzelfde
   optreden staat al op het preciezere, goedgekeurde verband), dan gaat het oude meteen op
   vervangen, met dezelfde regel en reden als stap 10e.

Idempotent: wat al gedaan is (de marker bestaat, namens_id staat, het mechanisme klopt) wordt
overgeslagen. Standaard een droogloop.

Gebruik:
    python3 scripts/migrate_instituut_via_persoon.py                      # droogloop, alles
    python3 scripts/migrate_instituut_via_persoon.py --alleen-clingendael # droogloop, de proef
    python3 scripts/migrate_instituut_via_persoon.py --uitvoeren [--alleen-clingendael]
"""
from __future__ import annotations

import argparse
import fcntl
import json
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import opschonen  # noqa: E402
import via_medewerkers  # noqa: E402

DB = ROOT / "data" / "propaganda_model.db"
LOCK_PATH = ROOT / "data" / "locks" / "automatische-beoordeling.lock"
TOKEN = ROOT / "data" / "tokens" / "assistent.token"
ACCOUNT = "assistent"
BESLUIT = "eigenaarsbesluit 2026-10-19, instituut of persoon"
CLINGENDAEL = 43
BRON = "bron"   # namens = de organisatie van het oude verband

# ── 1. Persoonsgedragen bewijs op instituut → medium: (oude argumenten, persoon, namens) ──
# Het eerste id is het optreden zelf; volgende ids zijn verzamelargumenten die hetzelfde optreden
# (mede) dragen. namens = BRON (de organisatie van het oude verband) of None (oud-medewerker,
# andere pet zoals de bron hem aankondigt).
NAAR_PERSOON = [
    # Clingendael Instituut (de proef)
    ([1259, 36], "Erik Stijnman", BRON),          # → NOS, defensie-expert
    ([1260, 36], "Louise van Schaik", BRON),      # → NOS (Nieuwsuur)
    ([2167], "Ko Colijn", None),                  # → NRC, "oud-directeur van Clingendael" (2022)
    ([2296], "Bart van den Berg", BRON),          # → EenVandaag
    ([2297], "Bob Deen", BRON),                   # → Buitenhof
    ([2298], "Adriaan Schout", BRON),             # → BNR
    # ABN AMRO Group Economics
    ([3434], "Sandra Phlippen", BRON),            # → BNR
    ([2393], "Philip Bokeloh", BRON),             # → NOS
    ([2394], "Piet Rietman", BRON),               # → NOS (nieuwe persoon)
    ([3436], "Sandra Phlippen", BRON),            # → Nieuwsuur
    ([3437], "Sandra Phlippen", BRON),            # → Nieuwsuur
    ([2395], "Sandra Phlippen", BRON),            # → WNL
    ([3435], "Han de Jong", None),                # → BNR, "oud-ABN AMRO-hoofdeconoom"
    # Overige denktanks, kennisinstituten, banken en ngo's
    ([2919], "Willem Wagenaar", BRON),            # Anne Frank Stichting → Medialogica
    ([2505], "Timo Koster", None),                # Atlantic Council → NPO Radio 1, "oud-NAVO-topambtenaar"
    ([2307], "Anna van Zoest", BRON),             # Atlantische Commissie → Nieuwsuur, als duider
    ([777], "Jair Schalkwijk", BRON),             # Controle Alt Delete → Het Parool (nieuwe persoon)
    ([774], "Jair Schalkwijk", BRON),             # Controle Alt Delete → NOS
    ([776], "Jair Schalkwijk", BRON),             # Controle Alt Delete → NOS
    ([2166], "Peter Wijninga", BRON),             # HCSS → AD
    ([2216], "Peter Wijninga", BRON),             # HCSS → BNR
    ([2218], "Peter Wijninga", BRON),             # HCSS → EenVandaag (staat al op #2141)
    ([2223], "Han ten Broeke", BRON),             # HCSS → Buitenhof
    ([2140], "Rob de Wijk", BRON),                # HCSS → De Telegraaf
    ([37], "Rob de Wijk", BRON),                  # HCSS → NOS
    ([2165], "Tim Sweijs", BRON),                 # HCSS → NRC
    ([2217], "Tim Sweijs", BRON),                 # HCSS → Nieuwsuur
    ([2222], "Rob de Wijk", BRON),                # HCSS → Op1 (samen met Ten Broeke)
    ([2222], "Han ten Broeke", BRON),             # HCSS → Op1
    ([2123], "Frederik Mertens", BRON),           # HCSS → RTL Nederland (nieuwe persoon)
    ([2220], "Tim Sweijs", BRON),                 # HCSS → Trouw
    ([2221], "Han ten Broeke", BRON),             # HCSS → WNL
    ([2139], "Lucia van Geuns", BRON),            # HCSS → de Volkskrant (nieuwe persoon)
    ([2383], "Thomas Renard", BRON),              # ICCT → NOS, als duider
    ([3432], "Carsten Brzeski", BRON),            # ING Research → BNR
    ([3433], "Marieke Blom", BRON),               # ING Research → BNR
    ([3430], "Marieke Blom", BRON),               # ING Research → FD
    ([3431], "Carsten Brzeski", BRON),            # ING Research → FD
    ([2349], "Marieke Blom", BRON),               # ING Research → NOS
    ([2350], "Maurice van Sante", BRON),          # ING Research → NOS
    ([2351], "Marieke Blom", BRON),               # ING Research → WNL
    ([2466], "Yvonne Koldenhof", BRON),           # MARIN → NOS
    ([2407], "Rémy Limpach", BRON),               # NIMH → NOS
    ([7877], "Han Bouwmeester", BRON),            # NLDA → NOS
    ([584], "Rolien Sasse", BRON),                # PAX → NOS (nieuwe persoon)
    ([584], "Wim Zwijnenburg", BRON),             # PAX → NOS (nieuwe persoon)
    ([2345], "Stefan Groot", BRON),               # RaboResearch → BNR
    ([2388], "Bas ter Weel", BRON),               # SEO → NPO Radio 1, als duider
    ([2335], "André Faaij", BRON),                # TNO → NOS, als duider
    ([2267], "Patrick van Schie", BRON),          # Teldersstichting → NPO Radio 1, als duider
    ([1285], "Martin Jelsma", BRON),              # TNI → NOS (nieuwe persoon)
    ([2283], "Tim 'S Jongers", BRON),             # WBS → EW
    ([2282], "Tim 'S Jongers", BRON),             # WBS → NRC
    ([2281], "Tim 'S Jongers", BRON),             # WBS → Trouw
]
# Een column is een positie (nieuws_scout_brief: mediaplatform, functie columnist), geen optreden:
# (oud argument, persoon, medium-id via het oude verband)
NAAR_COLUMN = [
    (2219, "Rob de Wijk"),                        # HCSS → Trouw: "vaste wekelijkse column in Trouw"
]
# ── 2. Wie namens het instituut spreekt: van persoon → medium naar instituut → medium ──
# (oude argumenten op het persoonsverband, instituut-id, mechanisme bij een nieuw instituutsverband)
NAAR_INSTITUUT = [
    ([2635, 3938], 602, None),                    # Van Mulligen (CBS-hoofdeconoom, eigen cijfers) → CBS → NOS
    ([2637], 307, None),                          # Knot (DNB-president) → DNB → Nieuwsuur
    ([2638], 307, None),                          # Sleijpen (DNB-president) → DNB → Nieuwsuur
    ([2639], 865, None),                          # Hekkert (PBL-directeur) → PBL → NOS
    ([2636], 83, "institutioneel_gezag"),         # Hasekamp (CPB-directeur, CPB-doorrekeningen) → CPB → Nieuwsuur
    ([2640], 827, "institutioneel_gezag"),        # Van Oudenhoven (SCP-directeur) → SCP → Nieuwsuur
    ([2657], 1023, None),                         # Van den Heuvel (CNV-voorzitter) → CNV → NOS
    ([2652], 1022, "expert_framing"),             # Megens (AWVN, "namens de werkgevers") → AWVN → NPO Radio 1
]
# ── 3. Hoedanigheid op bestaande persoonsverbanden, uit hun eigen bewijs ──
NAMENS = {
    2138: 43,     # Bob Deen → Nieuwsuur: "Oost-Europadeskundige bij Clingendael"
    1432: 43,     # Danny Pronk → Nieuwsuur: "Clingendael-onderzoeker"
    1323: 383,    # Diederik Gommers → Jinek: "hoogleraar Intensive Care (Erasmus MC)"
    2140: 906,    # Edwin Bakker → Nieuwsuur: "Leiden/ISGA"
    1429: 44,     # Han ten Broeke → Op1: "HCSS-directeur … als veiligheidsexpert"
    1207: 106,    # Jan Kluytmans → Op1: "een van de OMT-leden … als medisch duider"
    2144: 1162,   # Jelle Postma → Buitenhof: "directeur van Justice for Prosperity"
    2155: 1162,   # Jelle Postma → Pauw & De Wit
    1166: 76,     # Marieke Blom → Nieuwsuur: "hoofdeconoom van ING"
    1430: 44,     # Patrick Bolder → De Telegraaf: "HCSS-defensiespecialist"
    2141: 44,     # Peter Wijninga → EenVandaag: "HCSS defensiespecialist"
    1210: 44,     # Peter Wijninga → Op1: "als HCSS-defensiespecialist"
    1186: 44,     # Rob de Wijk → Pauw & De Wit: "HCSS-oprichter … als vaste duider"
    1221: 44,     # Rob de Wijk → WNL op Zondag: "directeur van … HCSS"
}
CLINGENDAEL_NAMENS = {2138, 1432}
# ── Nieuwe personen: naam → functie bij de organisatie zoals de bron hem noemt ──
NIEUWE_PERSONEN = {
    "Erik Stijnman": "defensie-expert",
    "Piet Rietman": "econoom",
    "Frederik Mertens": "strategisch analist",
    "Lucia van Geuns": "energiespecialist",
    "Martin Jelsma": "onderzoeker",
    "Rolien Sasse": "directeur",
    "Wim Zwijnenburg": "onderzoeker",
    "Jair Schalkwijk": "medeoprichter",
}
# Beweringen die niet ongewijzigd over kunnen: een etiket in eigen stem, of het instituut als
# handelende partij ("Clingendael levert … (o.a. X)") waar het optreden van de persoon is. Alleen
# feiten uit de oude bewering zelf (dezelfde bron draagt ze).
CLAIM = {
    37: "HCSS-directeur Rob de Wijk treedt bij de NOS op als veiligheidscommentator.",
    2281: "WBS-directeur Tim 'S Jongers werd door Trouw geïnterviewd (5 februari 2024).",
    2296: "Clingendael-programmaleider Bart van den Berg trad op 12 maart 2026 bij EenVandaag op als "
          "duider van veiligheid en defensie.",
    2298: "Adriaan Schout (Clingendael) trad op als duider van Europa en veiligheid in BNR's The Big Five.",
    2167: "Een NRC-essay (27 december 2022) baseerde zich mede op Ko Colijn, oud-directeur van Clingendael.",
    2166: "HCSS-defensie-expert Peter Wijninga werd op 11 februari 2023 in het AD opgevoerd over de dienstplicht.",
    2165: "HCSS-strateeg Tim Sweijs werd in NRC (22 september 2022) geciteerd over de escalatie rond Oekraïne.",
    2217: "HCSS-defensie-expert Tim Sweijs analyseerde in Nieuwsuur (15 maart 2022) hoe oorlogen eindigen.",
    2123: "HCSS-analist Frederik Mertens duidde bij RTL Nieuws (januari 2023) de westerse wapenleveranties aan "
          "Oekraïne ('Het is geen tank, want het is niet genoeg gepantserd, maar het is wel een heel bruikbaar "
          "voertuig').",
    2139: "HCSS-energiespecialist Lucia van Geuns becommentarieerde in de Volkskrant (8 juli 2022) de "
          "effectiviteit van de olieboycot tegen Rusland.",
    2140: "Rob de Wijk (HCSS) trad op 12 juli 2022 op in een video van De Telegraaf over de Oekraïense "
          "wapenbehoefte.",
    1285: "De NOS voerde Martin Jelsma, drugsonderzoeker voor het Transnational Institute, op als duider van "
          "het Nederlandse drugsbeleid.",
}
# Een verzamelbewering over twee personen: per persoon de eigen bewering en de eigen citaten
# (index in de citaties van het oude argument, op volgorde van id)
CLAIM_PERSOON = {
    (584, "Rolien Sasse"): ("PAX-directeur Rolien Sasse duidde op 31 maart 2024 in NOS Nieuwsuur de nieuwe "
                            "wapenwedloop.", [0]),
    (584, "Wim Zwijnenburg"): ("PAX-onderzoeker Wim Zwijnenburg duidde op 16 februari 2026 in NOS Nieuwsuur de "
                               "wapen- en milieuschade in conflictgebieden.", [1]),
}
HEROPENEN = [10514]
# De datum van het optreden waar bewering en bronrecord er geen noemen: de publicatiedatum van de
# bronpagina zelf (JSON-LD datePublished, opgehaald 2026-10-19). Wat niet op te halen was, zoekt
# de datumzoeker.
DATUM = {1259: "2025-12-22", 1260: "2025-11-09", 1285: "2016-04-19", 2636: "2023-08-18"}

MAANDEN = {"jan": 1, "feb": 2, "mrt": 3, "maart": 3, "apr": 4, "april": 4, "mei": 5, "jun": 6,
           "juni": 6, "jul": 7, "juli": 7, "aug": 8, "sep": 9, "sept": 9, "okt": 10, "nov": 11,
           "dec": 12, "januari": 1, "februari": 2, "augustus": 8, "september": 9, "oktober": 10,
           "november": 11, "december": 12}


# ------------------------------------------------------------------ hulpjes
def db(schrijven=False):
    conn = sqlite3.connect(f"file:{DB}?mode={'rw' if schrijven else 'ro'}", uri=True, timeout=60)
    conn.row_factory = sqlite3.Row
    return conn


class Api:
    def __init__(self, basis, token_pad):
        self.basis = basis.rstrip("/")
        self.token = token_pad.read_text().strip()

    def __call__(self, methode, pad, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.basis + pad, data=data, method=methode, headers={
            "Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read() or b"{}")
            except ValueError:
                return e.code, {}


def datum_uit(tekst) -> str | None:
    """De vroegste datum in een Nederlandse tekst: '13 okt 2022', '5 april en 10 mei 2026' (het
    jaar geldt voor beide), '11-02-2023', '2022-12-27', of alleen een jaartal."""
    tekst = tekst or ""
    gevonden = []
    for m in re.finditer(r"\b(\d{1,2})\s+([a-z]{3,9})\.?(?:\s+(\d{4}))?\b", tekst, flags=re.I):
        maand = MAANDEN.get(m.group(2).lower())
        if not maand:
            continue
        jaar = m.group(3) or (re.search(r"\b((?:19|20)\d{2})\b", tekst[m.end():]) or [None, None])[1]
        if jaar:
            gevonden.append(f"{jaar}-{maand:02d}-{int(m.group(1)):02d}")
    for d, m, j in re.findall(r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b", tekst):
        gevonden.append(f"{j}-{int(m):02d}-{int(d):02d}")
    gevonden += re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", tekst)
    if not gevonden:
        gevonden = re.findall(r"\b((?:19|20)\d{2})\b", tekst)
    return min(gevonden) if gevonden else None


def citaties(conn, arg_id) -> list[dict]:
    return [dict(r) for r in conn.execute(
        """SELECT c.source_id, c.quote, c.methode, s.date_published FROM citations c
           JOIN sources s ON s.id = c.source_id WHERE c.argument_id = ? ORDER BY c.id""", (arg_id,))]


def arg_rij(conn, arg_id):
    return conn.execute("""SELECT a.*, r.source_id AS rel_bron, r.target_id AS rel_doel, r.status AS rel_status,
                                  s.name AS bron_naam, s.type AS bron_type, t.name AS doel_naam
                           FROM arguments a JOIN relations r ON r.id = a.relation_id
                           JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
                           WHERE a.id = ?""", (arg_id,)).fetchone()


def persoon_id(conn, naam):
    r = conn.execute("""SELECT id FROM entities WHERE name = ? AND type = 'persoon' AND NOT vervangen
                        AND status IN ('goedgekeurd', 'voorgesteld') ORDER BY status = 'goedgekeurd' DESC, id
                        LIMIT 1""", (naam,)).fetchone()
    return r["id"] if r else None


def band(conn, p, o):
    """Een levende (goedgekeurde of voorgestelde) richtingloze band tussen persoon en organisatie."""
    r = conn.execute(f"""SELECT id, status FROM relations WHERE NOT vervangen
                         AND status IN ('goedgekeurd', 'voorgesteld')
                         AND relation_type IN ({','.join('?' * len(via_medewerkers.BAND_TYPES))})
                         AND ((source_id = ? AND target_id = ?) OR (source_id = ? AND target_id = ?))
                         ORDER BY status = 'goedgekeurd' DESC, id LIMIT 1""",
                     (*via_medewerkers.BAND_TYPES, p, o, o, p)).fetchone()
    return dict(r) if r else None


def optreden(conn, p, m, namens, typen=("beinvloeding", "bron_van")):
    """Een levend verband persoon → medium met deze hoedanigheid (of zonder, als er een zonder
    namens is en de nieuwe pet erop gezet mag worden). → (id, status, namens_id) of None."""
    rijen = conn.execute(f"""SELECT id, status, namens_id FROM relations WHERE source_id = ? AND target_id = ?
                             AND NOT vervangen AND status IN ('goedgekeurd', 'voorgesteld')
                             AND relation_type IN ({','.join('?' * len(typen))})
                             ORDER BY status = 'goedgekeurd' DESC, id""", (p, m, *typen)).fetchall()
    for r in rijen:
        if r["namens_id"] == namens:
            return dict(r)
    for r in rijen:
        if r["namens_id"] is None:
            return dict(r)
    return None


def al_overgezet(conn, rel_id, oud_id) -> int | None:
    for r in conn.execute("""SELECT id, reasoning FROM arguments WHERE relation_id = ? AND NOT vervangen
                             AND status <> 'verworpen' AND reasoning LIKE ?""",
                          (rel_id, f"Overgezet van %#{oud_id}%")):
        if oud_id in opschonen.overgezet_van(r["reasoning"]):
            return r["id"]
    return None


def mech_id(conn, naam):
    return conn.execute("SELECT id FROM mechanisms WHERE name = ? AND NOT vervangen", (naam,)).fetchone()["id"]


def rol_id(conn, naam):
    r = conn.execute("SELECT id FROM roles WHERE name = ? AND NOT vervangen", (naam,)).fetchone()
    return r["id"] if r else None


def log(conn, tabel, rid, oud, nieuw, reden):
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
                    VALUES (?, ?, 'updated', ?, ?, ?, ?)""",
                 (tabel, rid, ACCOUNT, json.dumps(oud, ensure_ascii=False), json.dumps(nieuw, ensure_ascii=False),
                  reden[:500]))


# ------------------------------------------------------------------ fase 1: direct
def fase_direct(conn, alleen_clingendael, uitvoeren, meld) -> dict:
    tel = {"namens": 0, "mechanisme": 0, "datum_leeg": 0, "heropend": 0}
    # a. namens_id op bestaande persoonsverbanden
    for rid, org in NAMENS.items():
        if alleen_clingendael and rid not in CLINGENDAEL_NAMENS:
            continue
        r = conn.execute("SELECT r.*, s.type AS bron_type FROM relations r JOIN entities s ON s.id = r.source_id "
                         "WHERE r.id = ?", (rid,)).fetchone()
        if r is None or r["namens_id"] == org:
            continue
        n = conn.execute("SELECT type, vervangen FROM entities WHERE id = ?", (org,)).fetchone()
        fout = via_medewerkers.namens_fout(r["bron_type"], r["relation_type"], r["source_id"], r["target_id"],
                                           org, n["type"] if n else None, bool(n["vervangen"]) if n else False)
        if fout:
            meld(f"  ✗ namens #{org} op #{rid} kan niet: {fout}")
            continue
        meld(f"  namens #{org} op relatie #{rid}")
        if uitvoeren:
            conn.execute("UPDATE relations SET namens_id = ? WHERE id = ?", (org, rid))
            log(conn, "relations", rid, {"namens_id": r["namens_id"]}, {"namens_id": org},
                f"{BESLUIT}: de hoedanigheid uit het eigen bewijs van dit verband (migrate_instituut_via_persoon.py)")
        tel["namens"] += 1
    # b. mechanismen
    nieuw_mech = {"expert_legitimatie": mech_id(conn, "expert_legitimatie"),
                  "academische_autoriteit": mech_id(conn, "academische_autoriteit")}
    oud_ef, oud_dle = mech_id(conn, "expert_framing"), mech_id(conn, "denktank_levert_expert")
    media = via_medewerkers.MEDIA_TYPES
    kandidaten = [(r["id"], oud_ef, nieuw_mech["expert_legitimatie"], "persoon → medium: expert_framing is "
                   "het mechanisme van een denktank als bron, de persoon is expert_legitimatie")
                  for r in conn.execute(f"""SELECT r.id FROM relations r JOIN entities s ON s.id = r.source_id
                        JOIN entities t ON t.id = r.target_id WHERE r.mechanism_id = ? AND s.type = 'persoon'
                        AND t.type IN ({','.join('?' * len(media))}) AND NOT r.vervangen
                        AND r.status IN ('goedgekeurd', 'voorgesteld')""", (oud_ef, *media))]
    if not alleen_clingendael:
        kandidaten += [(r["id"], oud_dle, nieuw_mech["academische_autoriteit"], "band persoon — universiteit: "
                        "academische_autoriteit is het mechanisme waarmee een universiteit haar experts gezag geeft "
                        "(denktank_levert_expert is dat van een denktank)")
                       for r in conn.execute("""SELECT r.id FROM relations r JOIN entities s ON s.id = r.source_id
                             JOIN entities t ON t.id = r.target_id WHERE r.mechanism_id = ? AND NOT r.vervangen
                             AND r.status IN ('goedgekeurd', 'voorgesteld')
                             AND ((s.type = 'persoon' AND t.type = 'onderwijsinstelling')
                                  OR (t.type = 'persoon' AND s.type = 'onderwijsinstelling'))""", (oud_dle,))]
    else:
        kandidaten = [k for k in kandidaten if k[0] == 1754]
    for rid, oud, nieuw, waarom in kandidaten:
        meld(f"  mechanisme #{oud} → #{nieuw} op relatie #{rid}")
        if uitvoeren:
            conn.execute("UPDATE relations SET mechanism_id = ? WHERE id = ?", (nieuw, rid))
            conn.execute("DELETE FROM instantiations WHERE relation_id = ? AND mechanism_id = ?", (rid, oud))
            conn.execute("INSERT OR IGNORE INTO instantiations (mechanism_id, relation_id) VALUES (?, ?)", (nieuw, rid))
            log(conn, "relations", rid, {"mechanism_id": oud}, {"mechanism_id": nieuw}, f"{BESLUIT}: {waarom}")
        tel["mechanisme"] += 1
    # c. een oprichtingsjaar als begin van een instituutsverband dat blijft
    verhuisd = {a for oud, _, _ in NAAR_PERSOON for a in oud} | {a for a, _ in NAAR_COLUMN}
    mechs = via_medewerkers.EXPERT_MECHANISMEN
    for r in conn.execute(f"""SELECT r.id, r.active_from, s.name, s.active_from AS opgericht, s.id AS org
            FROM relations r JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
            JOIN mechanisms m ON m.id = r.mechanism_id
            WHERE r.status = 'goedgekeurd' AND NOT r.vervangen AND s.type <> 'persoon'
              AND t.type IN ({','.join('?' * len(media))}) AND m.name IN ({','.join('?' * len(mechs))})
              AND r.active_from IS NOT NULL AND r.active_from = s.active_from""", (*media, *mechs)).fetchall():
        if alleen_clingendael and r["org"] != CLINGENDAEL:
            continue
        blijft = [a["id"] for a in conn.execute("""SELECT id FROM arguments WHERE relation_id = ?
                 AND parent_argument_id IS NULL AND NOT vervangen AND stance = 'supporting'
                 AND COALESCE(property, 'existence') = 'existence'
                 AND status IN ('ongecontroleerd', 'geverifieerd', 'betwist', 'bronvermelding_nodig')""",
                                                    (r["id"],)) if a["id"] not in verhuisd]
        mens = conn.execute("""SELECT 1 FROM edit_log l JOIN users u ON u.username = l.changed_by
                               WHERE l.table_name = 'relations' AND l.record_id = ? AND u.kind = 'mens'
                                 AND l.new_value LIKE '%active_from%' LIMIT 1""", (r["id"],)).fetchone()
        # Noemt het eigen bewijs dat jaar (bewering, citaat of publicatiedatum)? Dan kan het het
        # echte begin zijn (OMT 2020): laten staan.
        jaar = str(r["active_from"])[:4]
        gedragen = conn.execute("""SELECT 1 FROM arguments a LEFT JOIN citations c ON c.argument_id = a.id
                                   LEFT JOIN sources s ON s.id = c.source_id
                                   WHERE a.relation_id = ? AND NOT a.vervangen AND a.status <> 'verworpen'
                                     AND (a.claim LIKE ? OR COALESCE(c.quote, '') LIKE ?
                                          OR COALESCE(s.date_published, '') LIKE ? OR a.property_value LIKE ?)
                                   LIMIT 1""", (r["id"], f"%{jaar}%", f"%{jaar}%", f"{jaar}%", f"{jaar}%")).fetchone()
        if not blijft or mens or gedragen:
            continue
        meld(f"  begin {r['active_from']} (= oprichting van {r['name']}) leeg op relatie #{r['id']}")
        if uitvoeren:
            conn.execute("UPDATE relations SET active_from = NULL WHERE id = ?", (r["id"],))
            log(conn, "relations", r["id"], {"active_from": r["active_from"]}, {"active_from": None},
                f"{BESLUIT}: {r['active_from']} is de oprichting van {r['name']}, niet het begin van dit verband "
                "(looptijdregel 2026-10-09); de datumzoeker zoekt het begin")
        tel["datum_leeg"] += 1
    # d. heropenen wat om een storing werd verworpen
    for aid in HEROPENEN:
        a = conn.execute("SELECT status FROM arguments WHERE id = ?", (aid,)).fetchone()
        if a is None or a["status"] != "verworpen":
            continue
        meld(f"  argument #{aid} terug naar 'voorgesteld' (verworpen om HTTP 429, geen inhoudelijk oordeel)")
        if uitvoeren:
            conn.execute("UPDATE arguments SET status = 'voorgesteld' WHERE id = ?", (aid,))
            log(conn, "arguments", aid, {"status": "verworpen"}, {"status": "voorgesteld"},
                f"heropend ({BESLUIT}): verworpen omdat de bron drie keer HTTP 429 gaf — een storing, geen "
                "inhoudelijk oordeel; de bronchecker kijkt opnieuw")
        tel["heropend"] += 1
    return tel


# ------------------------------------------------------------------ fase 2: via de API
def nieuw_argument(api, conn, rel_id, oud_ids, claim, cits, waarom, uitvoeren, meld):
    """Dien het optreden opnieuw in op het preciezere verband. → ('nieuw'|'bestond'|'dubbel'|'fout', id)"""
    if rel_id is not None:
        al = al_overgezet(conn, rel_id, oud_ids[0])
        if al:
            return "bestond", al
    reasoning = (opschonen.OVERGEZET.format(id=oud_ids[0])
                 + "".join(f", #{x}" for x in oud_ids[1:]) + f" ({waarom}; {BESLUIT}).")
    body = {"relation_id": rel_id, "stance": "supporting", "claim": claim, "reasoning": reasoning,
            "citations": [{k: v for k, v in (("source_id", c["source_id"]), ("quote", c["quote"]),
                                             ("methode", c["methode"])) if v} for c in cits]}
    if not uitvoeren:
        meld(f"      + argument: {claim[:110]}")
        return "nieuw", None
    status, j = api("POST", "/api/arguments", body)
    if status == 201:
        meld(f"      + argument #{j['id']}: {claim[:100]}")
        return "nieuw", j["id"]
    if status == 409 and j.get("duplicaat_kandidaten"):
        return "dubbel", j["duplicaat_kandidaten"][0]["id"]
    meld(f"      ✗ argument niet ingediend ({status}): {j.get('error')}")
    return "fout", None


def fase_api(api, conn, alleen_clingendael, uitvoeren, meld) -> dict:
    tel = {"personen": 0, "banden": 0, "verbanden": 0, "argumenten": 0, "bestond": 0, "dubbel": [], "fouten": 0}
    gezag = rol_id(conn, "gezagsexpert")
    m_expert, m_denktank = mech_id(conn, "expert_legitimatie"), mech_id(conn, "denktank_levert_expert")
    m_universiteit, m_podium = mech_id(conn, "academische_autoriteit"), mech_id(conn, "podiumverlening")
    nep = {"n": -1}

    def nep_id():
        nep["n"] -= 1
        return nep["n"]

    def zorg_persoon(naam):
        pid = persoon_id(conn, naam)
        if pid:
            return pid
        meld(f"    + persoon {naam} (rol gezagsexpert)")
        tel["personen"] += 1
        if not uitvoeren:
            return nep_id()
        status, j = api("POST", "/api/entities", {"name": naam, "type": "persoon", "primary_role_id": gezag})
        if status != 201:
            meld(f"    ✗ persoon {naam} niet aangemaakt ({status}): {j.get('error')}")
            tel["fouten"] += 1
            return None
        return j["id"]

    def zorg_band(pid, org, org_naam, org_type, naam, cits, oud_claim):
        if pid > 0:
            b = band(conn, pid, org)
            if b:
                return b
        functie = NIEUWE_PERSONEN.get(naam) or "medewerker"
        mech = m_universiteit if org_type == "onderwijsinstelling" else m_denktank
        meld(f"    + band {naam} — {org_naam} (personeel, {functie})")
        tel["banden"] += 1
        if not uitvoeren:
            return {"id": nep_id(), "status": "voorgesteld"}
        status, j = api("POST", "/api/relations", {"source_id": pid, "target_id": org, "relation_type": "personeel",
                                                     "mechanism_id": mech, "functie": functie})
        if status != 201:
            meld(f"    ✗ band niet aangemaakt ({status}): {j.get('error')}")
            tel["fouten"] += 1
            return None
        claim = f"{naam} is {functie} bij {org_naam}."
        status2, j2 = api("POST", "/api/arguments", {
            "relation_id": j["id"], "stance": "supporting", "claim": claim,
            "reasoning": f"De bron noemt {naam} als {functie} van {org_naam} ({oud_claim[:200]}). "
                         f"De begindatum van de band zoekt de datumzoeker ({BESLUIT}).",
            "citations": [{"source_id": c["source_id"], "quote": c["quote"]} for c in cits if c["quote"]]
                         or [{"source_id": cits[0]["source_id"]}]})
        if status2 != 201:
            meld(f"    ✗ bandargument niet ingediend ({status2}): {j2.get('error')}")
        return {"id": j["id"], "status": "voorgesteld"}

    # 1. persoonsgedragen bewijs → persoon → medium
    for oud_ids, naam, namens_soort in NAAR_PERSOON:
        a = arg_rij(conn, oud_ids[0])
        if a is None:
            meld(f"  ✗ argument #{oud_ids[0]} bestaat niet")
            continue
        if alleen_clingendael and a["rel_bron"] != CLINGENDAEL:
            continue
        if a["vervangen"] or a["status"] in ("verworpen", "voorgesteld"):
            meld(f"  · #{oud_ids[0]} is al {a['status']}{' (vervangen)' if a['vervangen'] else ''} — overgeslagen")
            continue
        org, medium = a["rel_bron"], a["rel_doel"]
        namens = org if namens_soort == BRON else None
        cits = citaties(conn, oud_ids[0])
        claim = CLAIM.get(oud_ids[0]) or a["claim"]
        if (oud_ids[0], naam) in CLAIM_PERSOON:
            claim, keuze = CLAIM_PERSOON[(oud_ids[0], naam)]
            cits = [cits[i] for i in keuze if i < len(cits)]
        meld(f"  #{oud_ids[0]} {a['bron_naam']} → {a['doel_naam']}  ⇒  {naam} → {a['doel_naam']}"
             f"{' namens ' + a['bron_naam'] if namens else ' (zonder namens)'}")
        pid = zorg_persoon(naam)
        if pid is None:
            continue
        org_type = conn.execute("SELECT type FROM entities WHERE id = ?", (org,)).fetchone()["type"]
        if namens is not None or pid < 0 or not (pid > 0 and band(conn, pid, org)):
            if zorg_band(pid, org, a["bron_naam"], org_type, naam, cits, a["claim"]) is None:
                continue
        bestaand = optreden(conn, pid, medium, namens) if pid > 0 else None
        if bestaand and bestaand["namens_id"] != namens and namens is not None:
            meld(f"    namens #{namens} op bestaand verband #{bestaand['id']}")
            if uitvoeren:
                conn.execute("UPDATE relations SET namens_id = ? WHERE id = ?", (namens, bestaand["id"]))
                log(conn, "relations", bestaand["id"], {"namens_id": None}, {"namens_id": namens},
                    f"{BESLUIT}: hoedanigheid uit het overgezette argument #{oud_ids[0]}")
                conn.commit()
        if bestaand:
            rel_id = bestaand["id"]
        else:
            # De datum van het optreden: wat de bewering noemt, anders de publicatiedatum van de bron
            van = (datum_uit(claim) or datum_uit(" ".join(c["date_published"] or "" for c in cits))
                   or DATUM.get(oud_ids[0]))
            meld(f"    + verband {naam} → {a['doel_naam']} (beinvloeding, expert_legitimatie"
                 f"{', namens ' + a['bron_naam'] if namens else ''}, begin {van or '—'})")
            tel["verbanden"] += 1
            rel_id = None
            if uitvoeren:
                body = {"source_id": pid, "target_id": medium, "relation_type": "beinvloeding",
                        "mechanism_id": m_expert, "namens_id": namens}
                if van:
                    body["active_from"] = van
                status, j = api("POST", "/api/relations", body)
                if status != 201:
                    meld(f"    ✗ verband niet aangemaakt ({status}): {j.get('error')}")
                    tel["fouten"] += 1
                    continue
                rel_id = j["id"]
        uitkomst, aid = nieuw_argument(api, conn, rel_id, oud_ids, claim, cits,
                                       f"{a['bron_naam']} → {a['doel_naam']}: een optreden met eigen duiding "
                                       "hoort op persoon → medium", uitvoeren, meld)
        tel_uitkomst(tel, uitkomst, oud_ids, rel_id, aid)
    # 1b. een column is een positie
    for oud_id, naam in ([] if alleen_clingendael else NAAR_COLUMN):
        a = arg_rij(conn, oud_id)
        if a is None or a["vervangen"] or a["status"] in ("verworpen", "voorgesteld"):
            continue
        pid = persoon_id(conn, naam)
        medium = a["rel_doel"]
        cits = citaties(conn, oud_id)
        meld(f"  #{oud_id} {a['bron_naam']} → {a['doel_naam']}  ⇒  {a['doel_naam']} → {naam} (mediaplatform, columnist)")
        r = conn.execute("""SELECT id FROM relations WHERE source_id = ? AND target_id = ? AND relation_type = 'mediaplatform'
                            AND NOT vervangen AND status IN ('goedgekeurd', 'voorgesteld')""", (medium, pid)).fetchone()
        rel_id = r["id"] if r else None
        if rel_id is None:
            tel["verbanden"] += 1
            meld(f"    + columnistplek {a['doel_naam']} → {naam} (mediaplatform, podiumverlening)")
            if uitvoeren:
                status, j = api("POST", "/api/relations", {"source_id": medium, "target_id": pid,
                                                            "relation_type": "mediaplatform", "mechanism_id": m_podium,
                                                            "functie": "columnist",
                                                            **({"active_from": datum_uit(a['claim'])} if datum_uit(a['claim']) else {})})
                if status != 201:
                    meld(f"    ✗ columnistplek niet aangemaakt ({status}): {j.get('error')}")
                    continue
                rel_id = j["id"]
        uitkomst, aid = nieuw_argument(api, conn, rel_id, [oud_id], a["claim"], cits,
                                       f"{a['bron_naam']} → {a['doel_naam']}: een column is een positie bij het "
                                       "medium", uitvoeren, meld)
        tel_uitkomst(tel, uitkomst, [oud_id], rel_id, aid)
    # 2. wie namens het instituut spreekt → instituut → medium
    for oud_ids, org, nieuw_mech in ([] if alleen_clingendael else NAAR_INSTITUUT):
        a = arg_rij(conn, oud_ids[0])
        if a is None or a["vervangen"] or a["status"] in ("verworpen", "voorgesteld"):
            continue
        medium = a["rel_doel"]
        org_naam = conn.execute("SELECT name FROM entities WHERE id = ?", (org,)).fetchone()["name"]
        meld(f"  #{','.join(map(str, oud_ids))} {a['bron_naam']} → {a['doel_naam']}  ⇒  {org_naam} → {a['doel_naam']} "
             "(het instituut spreekt)")
        r = conn.execute("""SELECT r.id FROM relations r WHERE r.source_id = ? AND r.target_id = ? AND NOT r.vervangen
                            AND r.status = 'goedgekeurd' AND r.relation_type IN ('beinvloeding', 'bron_van')
                            ORDER BY r.id DESC LIMIT 1""", (org, medium)).fetchone()
        rel_id = r["id"] if r else None
        if rel_id is None:
            van = (datum_uit(a["claim"])
                   or datum_uit(" ".join(c["date_published"] or "" for c in citaties(conn, oud_ids[0])))
                   or DATUM.get(oud_ids[0]))
            meld(f"    + verband {org_naam} → {a['doel_naam']} (beinvloeding, {nieuw_mech}, begin {van or '—'})")
            tel["verbanden"] += 1
            if uitvoeren:
                body = {"source_id": org, "target_id": medium, "relation_type": "beinvloeding",
                        "mechanism_id": mech_id(conn, nieuw_mech or "institutioneel_gezag")}
                if van:
                    body["active_from"] = van
                status, j = api("POST", "/api/relations", body)
                if status != 201:
                    meld(f"    ✗ verband niet aangemaakt ({status}): {j.get('error')}")
                    continue
                rel_id = j["id"]
        for oud in oud_ids:
            ao = arg_rij(conn, oud)
            uitkomst, aid = nieuw_argument(api, conn, rel_id, [oud], ao["claim"], citaties(conn, oud),
                                           f"{ao['bron_naam']} → {ao['doel_naam']}: wie namens het instituut spreekt, "
                                           "hoort op instituut → medium", uitvoeren, meld)
            tel_uitkomst(tel, uitkomst, [oud], rel_id, aid)
    return tel


def tel_uitkomst(tel, uitkomst, oud_ids, rel_id, aid):
    if uitkomst == "nieuw":
        tel["argumenten"] += 1
    elif uitkomst == "bestond":
        tel["bestond"] += 1
    elif uitkomst == "dubbel":
        tel["dubbel"].append((oud_ids, rel_id, aid))
    else:
        tel["fouten"] += 1


def vervang_dubbel(conn, dubbels, uitvoeren, meld) -> int:
    """Een optreden dat als bijna dezelfde bewering al op het preciezere, goedgekeurde verband staat
    (409): het oude argument gaat meteen op vervangen; draagt het oude verband dan niets meer, dan
    wordt het afgewezen — dezelfde regel en reden als stap 10e."""
    n = 0
    for oud_ids, rel_id, kandidaat in dubbels:
        k = conn.execute("""SELECT a.status, r.status AS rel_status FROM arguments a JOIN relations r ON r.id = a.relation_id
                            WHERE a.id = ?""", (kandidaat,)).fetchone()
        if k is None or k["status"] not in ("ongecontroleerd", "geverifieerd") or k["rel_status"] != "goedgekeurd":
            meld(f"  · #{oud_ids[0]}: het bestaande argument #{kandidaat} op verband #{rel_id} is nog niet "
                 "gemerged of zijn verband niet goedgekeurd — blijft staan")
            continue
        for oud in oud_ids:
            a = conn.execute("SELECT * FROM arguments WHERE id = ?", (oud,)).fetchone()
            if a is None or a["vervangen"]:
                continue
            meld(f"  #{oud} vervangen door het bestaande #{kandidaat} (verband #{rel_id})")
            if not uitvoeren:
                continue
            conn.execute("UPDATE arguments SET status = 'verouderd', vervangen = 1 WHERE id = ?", (oud,))
            log(conn, "arguments", oud, {"status": a["status"], "vervangen": False}, {"status": "verouderd", "vervangen": True},
                f"{opschonen.OVERGEZET_REDEN} naar #{kandidaat} (verband #{rel_id}; hetzelfde optreden stond er al; {BESLUIT})")
            n += 1
            rel = a["relation_id"]
            levend = conn.execute("""SELECT COUNT(*) FROM arguments WHERE relation_id = ? AND parent_argument_id IS NULL
                                     AND NOT vervangen AND stance = 'supporting' AND COALESCE(property, 'existence') = 'existence'
                                     AND status IN ('ongecontroleerd', 'geverifieerd', 'betwist', 'bronvermelding_nodig')""",
                                  (rel,)).fetchone()[0]
            st = conn.execute("SELECT status FROM relations WHERE id = ?", (rel,)).fetchone()["status"]
            if levend == 0 and st == "goedgekeurd":
                meld(f"    verband #{rel} afgewezen: het draagt geen eigen bewijs meer")
                conn.execute("UPDATE relations SET status = 'afgewezen' WHERE id = ?", (rel,))
                log(conn, "relations", rel, {"status": "goedgekeurd"}, {"status": "afgewezen"},
                    f"{opschonen.OVERGEZET_REDEN}: het bewijs staat op verband #{rel_id} ({BESLUIT}); dit verband "
                    "draagt geen eigen bewijs meer")
                for ar in conn.execute("""WITH RECURSIVE boom(id) AS (
                        SELECT id FROM arguments WHERE relation_id = ? AND parent_argument_id IS NULL
                        UNION ALL SELECT x.id FROM arguments x JOIN boom b ON x.parent_argument_id = b.id)
                        SELECT a.id, a.status FROM arguments a WHERE a.id IN (SELECT id FROM boom)
                          AND a.status <> 'verworpen' AND NOT a.vervangen""", (rel,)).fetchall():
                    conn.execute("UPDATE arguments SET status = 'verworpen' WHERE id = ?", (ar["id"],))
                    log(conn, "arguments", ar["id"], {"status": ar["status"]}, {"status": "verworpen"},
                        f"mee-afgewezen met relations #{rel}")
    return n


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--uitvoeren", action="store_true", help="echt schrijven (anders een droogloop)")
    ap.add_argument("--alleen-clingendael", action="store_true", help="eerst de proef: alleen Clingendael")
    ap.add_argument("--api", default="http://localhost:5000")
    args = ap.parse_args()
    meld = print
    api = Api(args.api, TOKEN)
    if args.uitvoeren:
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        lock = open(LOCK_PATH, "a+")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit("De automatische beoordeling draait nu; probeer het zo opnieuw.")
        doel = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        bron = sqlite3.connect(DB, timeout=60)
        kopie = sqlite3.connect(doel)
        bron.backup(kopie)
        kopie.close()
        bron.close()
        meld(f"Backup: {doel.name}")
    conn = db(schrijven=args.uitvoeren)
    try:
        meld(f"== 1. Direct ({'uitvoeren' if args.uitvoeren else 'droogloop'}"
             f"{', alleen Clingendael' if args.alleen_clingendael else ''})")
        t1 = fase_direct(conn, args.alleen_clingendael, args.uitvoeren, meld)
        if args.uitvoeren:
            conn.commit()
        meld(f"   → {t1}")
        meld("== 2. Via de API (assistent; alles voorgesteld)")
        t2 = fase_api(api, conn, args.alleen_clingendael, args.uitvoeren, meld)
        meld(f"   → personen {t2['personen']}, banden {t2['banden']}, verbanden {t2['verbanden']}, "
             f"argumenten {t2['argumenten']}, al gedaan {t2.get('bestond', 0)}, bijna-dubbel {len(t2['dubbel'])}, "
             f"fouten {t2['fouten']}")
        if t2["dubbel"]:
            meld("== 3. Bijna-dubbel: hetzelfde optreden staat al op het preciezere verband")
            n = vervang_dubbel(conn, t2["dubbel"], args.uitvoeren, meld)
            if args.uitvoeren:
                conn.commit()
            meld(f"   → {n} oud(e) argument(en) vervangen")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
