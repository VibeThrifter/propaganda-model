#!/usr/bin/env python3
"""Bronklasse — de betrouwbaarheid en het onderwerp van een bron, beslist door agents
(eigenaarsbesluit 2026-10-06: "niks door mensen, alles door agents"; opgeschoond 2026-10-07).

De klasse van een bron stuurt de score (bronfactor = reliabilitygewicht × relevantiefactor),
maar alleen een reviewer kon een classificatievoorstel bevestigen (PATCH
/api/sources/<id>/classificatie). Op 2026-10-07 lagen er 1.963 voorstellen en stonden 2.242
bronnen op 'onbeoordeeld' (gewicht 0,15). Nu beslist de automatische beoordeling, met twee
onafhankelijke oordelen per bron:

- een bron met een voorstel van een ander account (meestal wie de bron registreerde): het
  voorstel plus een eigen oordeel van Claude Sonnet;
- een bron zonder voorstel die door levend werk geciteerd wordt: een oordeel van Claude
  Sonnet en een van Claude Opus, los van elkaar.

Zijn de twee het eens, dan geldt dat; anders de voorzichtigste: de klasse met het laagste
gewicht en het onderwerp met de laagste relevantiefactor. De poort van de server
(validation.klasse_consistentie: de klasse past bij het brontype, een hoge klasse vereist een
vindplaats) blijft gelden; past de keuze niet, dan de eerstvolgende lagere klasse die wel past.
Het besluit gaat via PATCH /api/sources/<id>/classificatie (merge-service, reviewer-tier), met
beide oordelen in de motivatie (edit_log). Een mens kan het altijd wijzigen.

Een eigen meting (bron met cluster_key 'meting:<id>', eigenaarsbesluit 2026-10-16) slaat dit
script over: hoe zwaar die weegt, bepaalt de eigenaar zelf (de server laat alleen een maintainer
haar classificeren).

Gebruik:
    python3 scripts/bronklasse.py --droog --max 40     # oordelen tonen, niets schrijven
    python3 scripts/bronklasse.py --max 160 --json     # echt
    python3 scripts/bronklasse.py --ids 2268,2269
    python3 scripts/bronklasse.py --herzien            # eigen besluiten opnieuw, met de huidige
                                                       # instructies (het voorstel uit het logboek)
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import bronchecker as bc  # noqa: E402
import validation  # noqa: E402
from scoring import RELIABILITY_WEIGHT  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / "merge-service.token"
DEFAULT_API = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "bronklasse_log.jsonl"
POGINGEN_PATH = ROOT / "data" / "bronklasse_pogingen.json"
REDEN = "automatische beoordeling: bronklasse"
PER_VRAAG = 40                 # bronnen per model-aanroep
OPNIEUW_NA_DAGEN = 30          # na een besluit dat de poort niet haalde
FOUT_OPNIEUW_NA_UREN = 20      # na een technische fout van het model
# Wat een agent kan kiezen; 'eigen_synthese' (projectmateriaal) en 'onbeoordeeld' niet
KLASSEN = ("primair", "academisch", "institutioneel", "kwaliteitsjournalistiek", "regulier",
           "opinie", "grijs")
ONDERWERPEN = ("nl_systeem", "algemeen", "buitenlands", "onbepaald")
# Voorzichtig = laagste relevantiefactor; bij gelijke factor het minst stellige
ONDERWERP_VOLGORDE = ("buitenlands", "onbepaald", "algemeen", "nl_systeem")

SYSTEM_PROMPT = (
    "Je classificeert bronnen voor een onderzoeksdatabase over het Nederlandse media- en "
    "bestuurssysteem (het propagandamodel van Herman & Chomsky plus besluitvorming). Per bron geef je twee dingen.\n"
    "reliability — de betrouwbaarheid van het soort bron:\n"
    "- primair: het originele document zelf: wet- of regelgeving, officieel register (KvK, "
    "Staatscourant), dataset, transcript, jaarverslag, persbericht of eigen verklaring van de "
    "partij zelf — ook de eigen website van een organisatie OVER ZICHZELF (bestuur, directie, "
    "statuten, organisatie, 'over ons', leden, financiers): dat is het originele document over "
    "die organisatie, geen grijze bron;\n"
    "- academisch: peer-reviewed artikel, proefschrift, wetenschappelijk boek;\n"
    "- institutioneel: rapport of publicatie van een overheids- of kennisinstituut (WRR, CPB, "
    "PBL, SCP, ACM, SER, Rekenkamer, Commissariaat voor de Media, ministeries, toezichthouders);\n"
    "- kwaliteitsjournalistiek: onderzoeksjournalistiek, longread, onthulling of analyse van "
    "een redactie met eigen onderzoek (Follow the Money, De Groene, Investico, onderzoeksdesks "
    "van kranten en omroepen);\n"
    "- regulier: een gewoon nieuwsbericht van een dagblad, omroep, persbureau (ANP) of "
    "nieuwssite, ook van NOS, NRC of de Volkskrant;\n"
    "- opinie: column, essay, commentaar, opiniestuk, recensie, interview als "
    "meningsuiting;\n"
    "- grijs: blog, podcast, sociale media, LinkedIn, Wikipedia, en sites zonder redactie die "
    "over ANDEREN schrijven (een persoonlijke site, een actiesite, een forum).\n"
    "Regels van de database: 'academisch' alleen bij brontype academisch_artikel of boek; "
    "'primair' alleen bij dataset, wetgeving, transcript, interview, persbericht of overig; "
    "'institutioneel' alleen bij rapport, dataset, wetgeving, boek, website of overig. "
    "Twijfel je tussen twee klassen, kies de lagere.\n"
    "onderwerp — hoe specifiek de bron over het onderwerp van de database gaat:\n"
    "- nl_systeem: over Nederland: de Nederlandse media, politiek, overheid, organisaties of "
    "personen;\n"
    "- algemeen: een landneutraal raamwerk of theorie, of internationaal zonder één land;\n"
    "- buitenlands: over een ander land, zonder Nederlandse partij;\n"
    "- onbepaald: niet te zeggen.\n"
    "Je oordeelt alleen op wat er staat (titel, uitgever, soort, url); verzin niets. "
    "Antwoord alleen met het gevraagde JSON, één oordeel per bron-id.")
SCHEMA = {
    "type": "object",
    "properties": {"oordelen": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "integer"},
                       "reliability": {"type": "string", "enum": list(KLASSEN)},
                       "onderwerp": {"type": "string", "enum": list(ONDERWERPEN)},
                       "reden": {"type": "string"}},
        "required": ["id", "reliability", "onderwerp", "reden"],
        "additionalProperties": False}}},
    "required": ["oordelen"],
    "additionalProperties": False,
}


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------------------------ kandidaten
def kandidaten(conn, ids=None) -> list[dict]:
    """Bronnen met een openstaand classificatievoorstel, en bronnen op 'onbeoordeeld' die
    levend werk citeert. Wat het nieuws toont eerst, dan wat het vaakst geciteerd wordt."""
    filt, params = "", []
    if ids:
        filt = f" AND s.id IN ({','.join('?' * len(ids))})"
        params = list(ids)
    rijen = [dict(r) for r in conn.execute(f"""
        SELECT s.id, s.title, s.author, s.publisher, s.source_type, s.date_published,
               s.reliability, s.onderwerp, s.reliability_voorgesteld, s.onderwerp_voorgesteld,
               s.classificatie_voorgesteld_door,
               (SELECT location FROM source_locations l WHERE l.source_id = s.id
                  AND l.location_type = 'url' ORDER BY l.id LIMIT 1) AS url,
               EXISTS (SELECT 1 FROM source_locations l WHERE l.source_id = s.id) AS heeft_loc,
               (SELECT COUNT(*) FROM citations c JOIN arguments a ON a.id = c.argument_id
                  WHERE c.source_id = s.id AND NOT a.vervangen
                    AND a.status NOT IN ('verworpen', 'verouderd')) AS n_levend
        FROM sources s
        WHERE s.reliability <> 'eigen_synthese'
          AND COALESCE(s.cluster_key, '') NOT LIKE 'meting:%'
          AND (s.classificatie_voorgesteld_door IS NOT NULL
               OR s.reliability = 'onbeoordeeld'){filt}""", params)]  # noqa: S608
    rijen = [r for r in rijen if r["classificatie_voorgesteld_door"] or r["n_levend"]]
    relaties, _ = bc.nieuws_voorrang(conn)
    in_nieuws = set()
    if relaties:
        lijst = list(relaties)
        in_nieuws = {r[0] for r in conn.execute(f"""
            SELECT DISTINCT c.source_id FROM citations c JOIN arguments a ON a.id = c.argument_id
            WHERE a.relation_id IN ({','.join('?' * len(lijst))})""", lijst)}  # noqa: S608
    for r in rijen:
        r["voorrang"] = 0 if r["id"] in in_nieuws else 1
    rijen.sort(key=lambda r: (r["voorrang"], -r["n_levend"], -r["id"]))
    return rijen


def herzien_kandidaten(conn, ids=None) -> list[dict]:
    """Bronnen waarvan de klasse nog van een eigen besluit komt (de laatste classificatie in
    edit_log is van deze agent, geen mens kwam erna), met het voorstel van toen uit het
    logboek als eerste oordeel (``voorstel_toen``)."""
    toen = {}
    try:
        for regel in LOG_PATH.read_text(encoding="utf-8").splitlines():
            rec = json.loads(regel)
            if rec.get("http") == 200:
                toen[rec["source_id"]] = next((o for o in rec.get("oordelen") or []
                                               if o.get("reden") == "voorstel"), None)
    except (OSError, ValueError):
        return []
    wie = [sid for sid in toen if not ids or sid in ids]
    if not wie:
        return []
    laatste = {r[0]: r[1] for r in conn.execute(f"""
        SELECT l.record_id, l.reason FROM edit_log l
        WHERE l.table_name = 'sources' AND l.record_id IN ({','.join('?' * len(wie))})
          AND l.id = (SELECT MAX(l2.id) FROM edit_log l2 WHERE l2.table_name = 'sources'
                      AND l2.record_id = l.record_id
                      AND l2.new_value LIKE '%"reliability"%')""", wie)}  # noqa: S608
    eigen = [sid for sid in wie if (laatste.get(sid) or "").startswith(REDEN)]
    if not eigen:
        return []
    rijen = [dict(r) for r in conn.execute(f"""
        SELECT s.id, s.title, s.author, s.publisher, s.source_type, s.date_published,
               s.reliability, s.onderwerp, NULL AS reliability_voorgesteld,
               NULL AS onderwerp_voorgesteld, NULL AS classificatie_voorgesteld_door,
               (SELECT location FROM source_locations l WHERE l.source_id = s.id
                  AND l.location_type = 'url' ORDER BY l.id LIMIT 1) AS url,
               EXISTS (SELECT 1 FROM source_locations l WHERE l.source_id = s.id) AS heeft_loc,
               0 AS n_levend, 1 AS voorrang
        FROM sources s WHERE s.id IN ({','.join('?' * len(eigen))})
          AND COALESCE(s.cluster_key, '') NOT LIKE 'meting:%'""", eigen)]  # noqa: S608
    for r in rijen:
        r["voorstel_toen"] = toen.get(r["id"])
    return rijen


# ------------------------------------------------------------------ besluit
def voorstel_van(bron: dict) -> dict | None:
    """Het openstaande voorstel als oordeel, of None (geen voorstel, of geen klasse erin). Bij
    ``--herzien``: het voorstel van toen, uit het logboek."""
    if "voorstel_toen" in bron:
        return bron["voorstel_toen"]
    if not bron.get("classificatie_voorgesteld_door"):
        return None
    rel = bron.get("reliability_voorgesteld")
    if not rel or rel == "onbeoordeeld":
        return None
    return {"wie": bron["classificatie_voorgesteld_door"], "reliability": rel,
            "onderwerp": bron.get("onderwerp_voorgesteld") or bron.get("onderwerp")
            or "onbepaald", "reden": "voorstel"}


def beslis(bron: dict, oordelen: list[dict]) -> tuple[str | None, str | None, str, str]:
    """Twee oordelen → (reliability, onderwerp, uitkomst, uitleg); uitkomst is 'eens',
    'oneens' (de voorzichtigste) of 'lager' (de voorzichtigste haalde de poort niet: de
    eerstvolgende lagere klasse die wel past). Geen enkele → (None, None, 'poort', reden)."""
    klassen = sorted({o["reliability"] for o in oordelen},
                     key=lambda k: RELIABILITY_WEIGHT.get(k, 0))
    laagste = klassen[0]
    ladder = sorted((k for k, w in RELIABILITY_WEIGHT.items()
                     if w <= RELIABILITY_WEIGHT[laagste] and k != "onbeoordeeld"
                     and (k != "eigen_synthese" or laagste == "eigen_synthese")),
                    key=lambda k: -RELIABILITY_WEIGHT[k])
    reliability = next((k for k in ladder if not validation.klasse_consistentie(
        bron["source_type"], k, bool(bron.get("heeft_loc")))), None)
    if reliability is None:
        return None, None, "poort", "geen klasse haalt de poort (brontype/vindplaats)"
    onderwerpen = {o["onderwerp"] for o in oordelen if o["onderwerp"] in ONDERWERPEN}
    onderwerp = min(onderwerpen or {"onbepaald"}, key=ONDERWERP_VOLGORDE.index)
    if reliability != laagste:
        uitkomst = "lager"
        uitleg = (f"'{laagste}' past niet bij brontype '{bron['source_type']}'"
                  f"{'' if bron.get('heeft_loc') else ' of mist een vindplaats'}: "
                  "de eerstvolgende lagere klasse")
    elif len(klassen) == 1:
        uitkomst, uitleg = "eens", "beide oordelen eens"
    else:
        uitkomst, uitleg = "oneens", "oneens: de voorzichtigste"
    if len(onderwerpen) > 1:
        uitleg += "; onderwerp oneens: het voorzichtigste"
    return reliability, onderwerp, uitkomst, uitleg


def motivatie(bron: dict, oordelen: list[dict], reliability: str, onderwerp: str,
              uitleg: str) -> str:
    delen = "; ".join(f"{o['wie']}: {o['reliability']}/{o['onderwerp']}"
                      + (f" ({o['reden'][:120]})" if o.get("reden") and o["reden"] != "voorstel"
                         else "") for o in oordelen)
    return f"{REDEN} — {delen} → {reliability}/{onderwerp} ({uitleg})"[:900]


# ------------------------------------------------------------------ oordelen vragen
def regel_voor(bron: dict) -> str:
    return json.dumps({"id": bron["id"], "titel": (bron.get("title") or "")[:200],
                       "auteur": (bron.get("author") or "")[:80],
                       "uitgever": (bron.get("publisher") or "")[:80],
                       "soort": bron.get("source_type"), "datum": bron.get("date_published"),
                       "url": (bron.get("url") or "")[:160]}, ensure_ascii=False)


def vraag_oordelen(bronnen: list[dict], model: str) -> dict[int, dict]:
    """Eén model-aanroep voor een groep bronnen → {bron-id: oordeel}."""
    prompt = ("Classificeer deze bronnen (één JSON-object per regel):\n"
              + "\n".join(regel_voor(b) for b in bronnen))
    uit = bc.vraag_model(prompt, SCHEMA, systeem=SYSTEM_PROMPT, model=model) or {}
    geldig = {}
    ids = {b["id"] for b in bronnen}
    for o in uit.get("oordelen") or []:
        if (isinstance(o, dict) and o.get("id") in ids and o.get("reliability") in KLASSEN
                and o.get("onderwerp") in ONDERWERPEN):
            geldig[o["id"]] = {"wie": model, "reliability": o["reliability"],
                               "onderwerp": o["onderwerp"], "reden": (o.get("reden") or "")}
    return geldig


# ------------------------------------------------------------------ pogingen
def laad_pogingen() -> dict:
    try:
        return json.loads(POGINGEN_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def bewaar_pogingen(pogingen: dict) -> None:
    POGINGEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    POGINGEN_PATH.write_text(json.dumps(pogingen, indent=1), encoding="utf-8")


def mag_weer(poging: dict | None, nu: datetime.datetime) -> bool:
    if not poging:
        return True
    try:
        op = datetime.datetime.fromisoformat(str(poging.get("op")))
    except ValueError:
        return True
    wacht = (datetime.timedelta(hours=FOUT_OPNIEUW_NA_UREN) if poging.get("uitkomst") == "fout"
             else datetime.timedelta(days=OPNIEUW_NA_DAGEN))
    return nu - op >= wacht


# ------------------------------------------------------------------ schrijven
def zet_klasse(api, token, sid, body) -> tuple[int, dict]:
    req = urllib.request.Request(f"{api}/api/sources/{sid}/classificatie",
                                 data=json.dumps(body).encode(), method="PATCH",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except json.JSONDecodeError:
            return e.code, {}


def draai(*, api=DEFAULT_API, token=None, token_pad=DEFAULT_TOKEN, max_n=160, droog=False,
          ids=None, parallel=2, herzien=False, meld=print) -> dict:
    """Eén ronde → {bekeken, besloten, eens, oneens, lager, poort, fout, ongewijzigd}.
    ``herzien``: eigen eerdere besluiten opnieuw, met de huidige instructies."""
    if not droog and token is None:
        token = Path(token_pad).read_text().strip() if Path(token_pad).exists() else None
        if not token:
            raise SystemExit(f"Token niet gevonden: {token_pad}")
    nu = datetime.datetime.now()
    pogingen = laad_pogingen()
    conn = db()
    try:
        alle = herzien_kandidaten(conn, ids) if herzien else kandidaten(conn, ids)
    finally:
        conn.close()
    bronnen = [b for b in alle if ids or herzien
               or mag_weer(pogingen.get(str(b["id"])), nu)][:max_n]
    meld(f"Bronklassen: {len(bronnen)} van {len(alle)} bron(nen) zonder besluit"
         f"{' (droog)' if droog else ''}")
    tel = {"bekeken": len(bronnen), "besloten": 0, "eens": 0, "oneens": 0, "lager": 0,
           "poort": 0, "fout": 0, "ongewijzigd": 0}
    if not bronnen:
        return tel
    # Sonnet voor elke bron; Opus als tweede oordeel waar geen voorstel van een ander ligt
    zonder_voorstel = [b for b in bronnen if voorstel_van(b) is None]
    taken = [("sonnet", bronnen[i:i + PER_VRAAG]) for i in range(0, len(bronnen), PER_VRAAG)]
    taken += [("opus", zonder_voorstel[i:i + PER_VRAAG])
              for i in range(0, len(zonder_voorstel), PER_VRAAG)]
    oordelen: dict[int, list[dict]] = {b["id"]: [] for b in bronnen}
    for b in bronnen:
        if voorstel_van(b):
            oordelen[b["id"]].append(voorstel_van(b))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        for antwoord in pool.map(lambda taak: vraag_oordelen(taak[1], taak[0]), taken):
            for sid, oordeel in antwoord.items():
                oordelen[sid].append(oordeel)
    for bron in bronnen:
        sid = bron["id"]
        if len(oordelen[sid]) < 2:
            tel["fout"] += 1
            if not droog:
                pogingen[str(sid)] = {"op": nu.isoformat(timespec="seconds"), "uitkomst": "fout"}
            continue
        reliability, onderwerp, uitkomst, uitleg = beslis(bron, oordelen[sid])
        regel = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "source_id": sid,
                 "oordelen": oordelen[sid], "reliability": reliability, "onderwerp": onderwerp,
                 "uitkomst": uitkomst, "uitleg": uitleg}
        tel[uitkomst] += 1
        if herzien and (reliability, onderwerp) == (bron["reliability"], bron["onderwerp"]):
            tel["ongewijzigd"] += 1
            continue
        if reliability is None:
            if not droog:
                pogingen[str(sid)] = {"op": nu.isoformat(timespec="seconds"), "uitkomst": "poort"}
        else:
            if not droog:
                status, antwoord = zet_klasse(api, token, sid, {
                    "reliability": reliability, "onderwerp": onderwerp,
                    "motivatie": motivatie(bron, oordelen[sid], reliability, onderwerp, uitleg)})
                regel["http"] = status
                if status == 200:
                    tel["besloten"] += 1
                    pogingen.pop(str(sid), None)
                else:
                    tel["fout"] += 1
                    regel["fout"] = antwoord.get("error")
                    pogingen[str(sid)] = {"op": nu.isoformat(timespec="seconds"),
                                          "uitkomst": "poort" if status == 400 else "fout"}
        if not droog:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as log:
                log.write(json.dumps(regel, ensure_ascii=False) + "\n")
    if not droog:
        bewaar_pogingen(pogingen)
    meld(f"Bronklassen: {tel['besloten']} besloten ({tel['eens']} eens, {tel['oneens']} "
         f"oneens → de voorzichtigste, {tel['lager']} lager om de poort), {tel['poort']} "
         f"zonder passende klasse, {tel['fout']} fout")
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--max", type=int, default=160, help="hooguit zoveel bronnen per ronde")
    ap.add_argument("--ids", default="", help="alleen deze bron-id's (komma's)")
    ap.add_argument("--droog", action="store_true", help="oordelen, maar niets schrijven")
    ap.add_argument("--herzien", action="store_true",
                    help="eigen eerdere besluiten opnieuw, met de huidige instructies")
    ap.add_argument("--json", action="store_true", help="eindig met één JSON-regel")
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",") if x.strip().isdigit()] or None
    tel = draai(api=args.api, token_pad=args.token, max_n=args.max, droog=args.droog, ids=ids,
                herzien=args.herzien)
    print(json.dumps(tel, ensure_ascii=False) if args.json else f"Klaar: {tel}")


if __name__ == "__main__":
    main()
