#!/usr/bin/env python3
"""Datumzoeker — elk verband krijgt zijn looptijd (eigenaarsbesluit 2026-10-09: "vul bij alles de
goede jaartallen in he want het model kijkt gewoon per tijdsvak wat de relaties zijn.. zorg ook
dat dit overal wordt gehandhaafd en dat alle agents dit weten").

Voor verbanden zonder begin (active_from), wat het nieuws toont eerst, dan verbanden rond
entiteiten uit het nieuws, dan personen, dan de rest, en registerfeiten waarvan het register
geen begin noemt als laatste:
  1. EIGEN BRONNEN (goedkoop, één aanroep voor een hele portie, zonder tools): de citaten die
     het verband al draagt ("(2011–2020)", "per 1 juni 2023"). Alleen een citaat telt, nooit de
     beschrijving of de bewering van het model zelf.
  2. HET WEB (Sonnet met alleen WebSearch/WebFetch, zoals de bronzoeker): een openbare bron
     die beide partijen noemt en zegt wanneer het verband begon (en of en wanneer het eindigde).
     Het script haalt de bron zelf op en vindt het citaat letterlijk terug.
Wat gevonden is, wordt een aspect-argument op het verband (property active_from/active_until,
property_value JJJJ[-MM[-DD]] zo precies als de bron geeft, letterlijk citaat). Daarna beslist
de uurronde: de bronchecker (A1, een ander account) toetst het, de stemtoets toetst de woorden,
en stap 10c zet de datum op het verband (POST /api/beoordeling/looptijd/<id>: alleen een leeg
veld, oud/nieuw in edit_log, terug te draaien). Niets gevonden → looptijd_onderzoek
'niets_gevonden' (de enige reden waarom een verband zonder begin mag blijven) en pas na 30 dagen
opnieuw; een technische fout → na 20 uur opnieuw.

Daarna (2026-10-13) het BESTAAN van organisaties: een goedgekeurde organisatie met verbanden maar
zonder oprichtingsdatum krijgt een web-zoektocht (`--max-web-org` per ronde, eigen dagplafond
DAG_PLAFOND_ORG) naar haar oprichting en eventuele opheffing. Dat wordt een aspect-argument op de
entiteit (entity_id, property active_from/active_until); stap 10c zet het na A1. De stand staat in
data/datumzoeker_organisaties.json (zelfde wachttijden).

Account `datumzoeker` (bijdrager, eigen token). Stap 1b van scripts/automatische_beoordeling.py.
Los:
    python3 scripts/datumzoeker.py [--droog] [--max-eigen 20] [--max-web 8] [--ids 1879,1880]
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import bronchecker as bc  # noqa: E402
import bronzoeker as bz  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
ACCOUNT = "datumzoeker"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / f"{ACCOUNT}.token"
DEFAULT_API = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "datumzoeker_log.jsonl"
MODEL = "sonnet"
LLM_TIMEOUT_S = 600
OPNIEUW_NA_DAGEN = 30
FOUT_OPNIEUW_NA_UREN = 20
DAG_PLAFOND = 150            # web-zoektochten per dag
DAG_PLAFOND_ORG = 48         # en apart voor het bestaan van organisaties (2026-10-13)
MERK = "Looptijd voor verband #{id}"
DATUM_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")

REGELS = (
    "Je zoekt de LOOPTIJD van een verband in een onderzoeksdatabase over het Nederlandse media- "
    "en bestuurssysteem: wanneer het begon (en, als het voorbij is, wanneer het eindigde), zo "
    "precies als de bron het zegt (jaar, jaar-maand of datum; nooit preciezer dan de bron). "
    "Een datum telt alleen met een letterlijk citaat dat het jaartal noemt en over dit verband "
    "tussen deze twee partijen gaat. Een datum over iets anders (de oprichting van een "
    "organisatie, een ander ambt van dezelfde persoon, de publicatiedatum van het artikel) is "
    "geen begin van dit verband. Raad nooit. 'Sinds 2019' is een begin; 'in 2019 was hij al …' "
    "is geen begin (hoogstens 'actief in 2019': geef dan niets). Het begin hoort bij de SOORT "
    "band: bij een lidmaatschap het lid worden (niet het begin van een functie als leider of "
    "voorzitter binnen de partij), bij een dienstverband of personeel de indiensttreding, bij "
    "een bestuurszetel de benoeming in het bestuur, bij een ambt de ambtsaanvaarding, bij "
    "eigendom de overname. Schrijf de bewering neutraal: "
    "wie, welke functie of band, bij wie, sinds wanneer (en tot wanneer). Antwoord alleen met "
    "het gevraagde JSON."
)
# Organisaties (2026-10-13): hun bestaan begrenst elk verband ermee (looptijd.py), dus ook dat
# wordt opgezocht: oprichting en, als ze niet meer bestaat, opheffing of fusie.
REGELS_ORG = (
    "Je zoekt het BESTAAN van een organisatie in een onderzoeksdatabase over het Nederlandse "
    "media- en bestuurssysteem: wanneer ze werd opgericht (en, als ze niet meer bestaat, wanneer "
    "ze werd opgeheven of opging in een andere organisatie), zo precies als de bron het zegt "
    "(jaar, jaar-maand of datum; nooit preciezer dan de bron). Een datum telt alleen met een "
    "letterlijk citaat dat het jaartal noemt en over deze organisatie gaat. Bij een naamswijziging "
    "of fusie: het begin van de organisatie zoals ze hier heet als die naam bij een nieuwe "
    "organisatie hoort, anders de oprichting van de organisatie zelf; zeg het in de toelichting. "
    "Raad nooit. Schrijf de bewering neutraal: de organisatie, opgericht (opgeheven) op/in. "
    "Antwoord alleen met het gevraagde JSON."
)
ORG_STAND_PAD = ROOT / "data" / "datumzoeker_organisaties.json"
ORG_TYPES_NIET = ("persoon",)

EIGEN_SCHEMA = {
    "type": "object",
    "properties": {"uitkomsten": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "nr": {"type": "integer"},
            "begin": {"type": "string"}, "begin_citaat_nr": {"type": "integer"},
            "begin_citaat": {"type": "string"},
            "eind": {"type": "string"}, "eind_citaat_nr": {"type": "integer"},
            "eind_citaat": {"type": "string"},
            "bewering": {"type": "string"},
        },
        "required": ["nr", "begin", "begin_citaat_nr", "begin_citaat", "eind", "eind_citaat_nr",
                     "eind_citaat", "bewering"],
        "additionalProperties": False}}},
    "required": ["uitkomsten"], "additionalProperties": False,
}
_BRON = {"type": "object", "properties": {
    "url": {"type": "string"}, "titel": {"type": "string"}, "uitgever": {"type": "string"},
    "datum": {"type": "string"}, "soort": {"type": "string", "enum": list(bz.BRONSOORTEN)},
    "citaat": {"type": "string"}},
    "required": ["url", "titel", "uitgever", "datum", "soort", "citaat"], "additionalProperties": False}
WEB_SCHEMA = {
    "type": "object",
    "properties": {
        "gevonden": {"type": "boolean"},
        "begin": {"type": "string"}, "begin_bron": _BRON,
        "eind": {"type": "string"}, "eind_bron": _BRON,
        "bewering": {"type": "string"}, "toelichting": {"type": "string"},
    },
    "required": ["gevonden", "begin", "begin_bron", "eind", "eind_bron", "bewering", "toelichting"],
    "additionalProperties": False,
}


# ------------------------------------------------------------------ database (alleen-lezen)
def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def onderzoek(conn) -> dict[int, dict]:
    if not bc.heeft_tabel(conn, "looptijd_onderzoek"):
        return {}
    return {r["relation_id"]: dict(r) for r in conn.execute("SELECT * FROM looptijd_onderzoek")}


def mag_weer(stand: dict | None, nu: datetime.datetime) -> bool:
    """Wanneer een verband (opnieuw) aan de beurt is."""
    if not stand:
        return True
    if stand["status"] in ("gevonden",):
        return False
    try:
        op = datetime.datetime.fromisoformat(str(stand["laatste_poging"])[:19])
    except ValueError:
        return True
    if stand["status"] == "fout":
        return nu - op >= datetime.timedelta(hours=FOUT_OPNIEUW_NA_UREN)
    if stand["status"] in ("niets_gevonden", "gezocht"):
        return nu - op >= datetime.timedelta(days=OPNIEUW_NA_DAGEN)
    return True  # register_zonder_datum: aan de beurt (als laatste)


def kandidaten(conn, ids=None, nu=None) -> list[dict]:
    """Verbanden zonder begin die aan de beurt zijn, in volgorde van voorrang."""
    nu = nu or datetime.datetime.now()
    filt, params = "", []
    if ids:
        filt = f" AND r.id IN ({','.join('?' * len(ids))})"
        params = list(ids)
    rijen = [dict(r) for r in conn.execute(f"""
        SELECT r.id, r.relation_type, r.functie, r.description, r.active_from, r.active_until,
               r.status, s.id AS bron_id, s.name AS bron_naam, s.type AS bron_type,
               t.id AS doel_id, t.name AS doel_naam, t.type AS doel_type, m.name AS mechanisme
        FROM relations r JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
        LEFT JOIN mechanisms m ON m.id = r.mechanism_id
        WHERE NOT r.vervangen AND TRIM(COALESCE(r.active_from, '')) = ''
          AND (r.status = 'goedgekeurd' OR (r.status = 'voorgesteld' AND r.mechanism_id IS NOT NULL))
          AND NOT EXISTS (SELECT 1 FROM arguments a WHERE a.relation_id = r.id
                          AND a.property = 'active_from' AND NOT a.vervangen
                          AND a.status NOT IN ('verworpen'))
          {filt}""", params)]  # noqa: S608 - alleen placeholders
    stand = onderzoek(conn)
    nieuws, ent = bc.nieuws_voorrang(conn)
    uit = []
    for r in rijen:
        st = stand.get(r["id"])
        if not ids and not mag_weer(st, nu):
            continue
        register = bool(st and st["status"] == "register_zonder_datum")
        r["voorrang"] = (4 if register else 0 if r["id"] in nieuws
                         else 1 if (r["bron_id"] in ent or r["doel_id"] in ent)
                         else 2 if "persoon" in (r["bron_type"], r["doel_type"]) else 3)
        r["register"] = register
        uit.append(r)
    uit.sort(key=lambda r: (r["voorrang"], -r["id"]))
    return uit


def eigen_citaten(conn, rid) -> list[dict]:
    """De citaten die het verband al draagt (levende steunende roots), met hun bron."""
    return [dict(r) for r in conn.execute("""
        SELECT DISTINCT c.source_id, c.quote, s.title, s.publisher
        FROM arguments a JOIN citations c ON c.argument_id = a.id JOIN sources s ON s.id = c.source_id
        WHERE a.relation_id = ? AND a.parent_argument_id IS NULL AND a.stance = 'supporting'
          AND NOT a.vervangen AND a.status NOT IN ('verworpen', 'voorgesteld')
          AND TRIM(COALESCE(c.quote, '')) <> '' AND COALESCE(s.reliability, '') <> 'eigen_synthese'
        ORDER BY c.id LIMIT 6""", (rid,))]


SOORT_BAND = {
    "lidmaatschap": "lid van", "personeel": "werkt/werkte bij", "dienstverband": "in dienst van",
    "bestuurder": "bestuurder bij", "adviseur": "adviseur van", "woordvoerder_van": "woordvoerder van",
    "draaideur": "stapte over naar", "eigendom": "eigenaar van", "ambt": "ambt bij",
    "zeggenschap": "zeggenschap over", "financiering": "financiert", "lobbyt": "lobbyt bij",
}


def verband_zin(r: dict) -> str:
    functie = f" (functie: {r['functie']})" if r.get("functie") else ""
    eind = f"; het model heeft als einde {r['active_until']}" if r.get("active_until") else ""
    soort = SOORT_BAND.get(r["relation_type"], r["relation_type"].replace("_", " "))
    return (f"{r['bron_naam']} — {r['relation_type'].replace('_', ' ')} ({soort}){functie} — "
            f"{r['doel_naam']}{' (mechanisme ' + r['mechanisme'] + ')' if r.get('mechanisme') else ''}{eind}")


# ------------------------------------------------------------------ het model vragen
def vraag(prompt: str, schema: dict, tools: bool, regels: str = REGELS) -> dict | None:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = [bc.CLAUDE, "-p", "--output-format", "json", "--strict-mcp-config",
           "--setting-sources", "", "--no-session-persistence", "--model", MODEL,
           "--system-prompt", regels, "--json-schema", json.dumps(schema)]
    cmd += (["--tools", "WebSearch,WebFetch", "--allowedTools", "WebSearch,WebFetch"] if tools
            else ["--tools", ""])
    with tempfile.TemporaryDirectory(prefix="datumzoeker-") as leeg:
        try:
            r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=leeg,
                               env=env, timeout=LLM_TIMEOUT_S)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
    try:
        envelope = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return None
    if envelope.get("is_error"):
        return None
    uit = envelope.get("structured_output")
    if isinstance(uit, dict):
        return uit
    tekst = str(envelope.get("result") or "")
    try:
        uit = json.loads(tekst[tekst.find("{"):tekst.rfind("}") + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return uit if isinstance(uit, dict) else None


def schone_datum(waarde: str | None, vandaag: datetime.date | None = None) -> str | None:
    """'2023-06-01', '2023-06' of '2023' — alleen als het kan (1800 … vandaag)."""
    tekst = (waarde or "").strip()
    if not DATUM_RE.match(tekst):
        tekst = bz.datum_van(tekst) or ""
    if not DATUM_RE.match(tekst):
        return None
    vandaag = vandaag or datetime.date.today()
    if not 1800 <= int(tekst[:4]) or tekst > vandaag.isoformat()[:len(tekst)]:
        return None
    return tekst


def noemt_jaar(citaat: str | None, datum: str) -> bool:
    return bool(citaat) and datum[:4] in citaat


def eigen_ronde(conn, portie: list[dict]) -> dict[int, dict]:
    """Stap 1: één aanroep zonder tools over de eigen citaten van een portie verbanden.
    → {relatie-id: {begin, eind, bewering, citaten: [{source_id, quote}]}} (alleen gecontroleerd)."""
    items, citaten_van = [], {}
    for nr, r in enumerate(portie, 1):
        cit = eigen_citaten(conn, r["id"])
        if not cit:
            continue
        citaten_van[nr] = (r, cit)
        regels = "\n".join(f"    citaat {i}: “{c['quote']}” ({c['publisher'] or c['title']})"
                           for i, c in enumerate(cit, 1))
        items.append(f"{nr}. Verband: {verband_zin(r)}\n{regels}")
    if not items:
        return {}
    prompt = ("Zoek per verband in de gegeven citaten het begin (en eventueel het einde) van "
              "precies dit verband. Gebruik alleen deze citaten, geen kennis van buiten. Geef het "
              "nummer van het citaat en neem het relevante stuk letterlijk over. Staat het er "
              "niet in: laat begin/eind leeg en citaat_nr 0.\n\n" + "\n\n".join(items))
    antwoord = vraag(prompt, EIGEN_SCHEMA, tools=False)
    if not antwoord:
        return {"_fout": True}
    uit = {}
    for u in antwoord.get("uitkomsten") or []:
        if u.get("nr") not in citaten_van:
            continue
        r, cit = citaten_van[u["nr"]]
        gevonden = {}
        for veld, citveld, nrveld in (("begin", "begin_citaat", "begin_citaat_nr"),
                                      ("eind", "eind_citaat", "eind_citaat_nr")):
            datum = schone_datum(u.get(veld))
            idx = (u.get(nrveld) or 0) - 1
            if not datum or not 0 <= idx < len(cit):
                continue
            stuk = (u.get(citveld) or "").strip()
            bron = cit[idx]
            # Het stuk moet letterlijk in het bestaande citaat staan en het jaartal noemen
            if not stuk or bc.normaliseer(stuk) not in bc.normaliseer(bron["quote"]) \
                    or not noemt_jaar(stuk, datum):
                continue
            gevonden[veld] = {"datum": datum, "source_id": bron["source_id"], "quote": stuk}
        if "begin" in gevonden or "eind" in gevonden:
            uit[r["id"]] = {**gevonden, "bewering": (u.get("bewering") or "").strip()}
    return uit


def web_prompt(r: dict, eigen: list[dict]) -> str:
    al = ("\nWat het model al citeert (zonder datum):\n" + "\n".join(
        f"  - “{c['quote'][:200]}”" for c in eigen)) if eigen else ""
    return (f"Verband: {verband_zin(r)}.{al}\n\nZoek op het web wanneer dit verband begon "
            f"(en of en wanneer het eindigde). Een bron moet {r['bron_naam']} én {r['doel_naam']} "
            "bij naam noemen. Open de pagina met WebFetch en neem het citaat dat de datum geeft "
            "teken voor teken over. Wikipedia, sociale media en deze database zelf zijn geen bron "
            "(Wikipedia mag als vindplaats: volg de voetnoot naar de echte bron). Primaire "
            "bronnen eerst: Parlement.com, Kiesraad, persberichten, jaarverslagen, het colofon "
            "of de eigen site, nieuwsberichten over de benoeming of het vertrek. Geen datum "
            "gevonden: gevonden=false en lege velden.")


def web_ronde(r: dict, eigen: list[dict]) -> dict:
    """Stap 2: zoeken op het web. → {uitkomst: gevonden|niets|fout, begin?, eind?, bewering, …}"""
    antwoord = vraag(web_prompt(r, eigen), WEB_SCHEMA, tools=True)
    if not antwoord:
        return {"uitkomst": "fout", "toelichting": "model gaf geen bruikbaar antwoord"}
    partijen = [r["bron_naam"], r["doel_naam"]]
    afgevallen: list[dict] = []
    uit = {"uitkomst": "niets", "afgevallen": afgevallen,
           "toelichting": (antwoord.get("toelichting") or "")[:600]}
    if not antwoord.get("gevonden"):
        return uit
    for veld in ("begin", "eind"):
        datum = schone_datum(antwoord.get(veld))
        bron = antwoord.get(f"{veld}_bron") or {}
        if not datum or not (bron.get("url") or "").strip():
            continue
        if not noemt_jaar(bron.get("citaat"), datum):
            afgevallen.append({"url": bron.get("url"), "reden": f"citaat noemt {datum[:4]} niet"})
            continue
        goed, reden = bz.natrekken(bron, partijen)
        if not goed:
            afgevallen.append({"url": bron.get("url"), "reden": reden})
            continue
        uit[veld] = {"datum": datum, "bron": goed}
    if "begin" in uit or "eind" in uit:
        uit["uitkomst"] = "gevonden"
        uit["bewering"] = (antwoord.get("bewering") or "").strip()
    return uit


# ------------------------------------------------------------------ schrijven
def bewering_voor(r: dict, veld: str, datum: str, voorstel: str | None) -> str:
    """De bewering van het argument: die van het model als ze het jaartal en beide partijen
    noemt, anders een vaste neutrale zin."""
    if voorstel and datum[:4] in voorstel and bz.noemt(voorstel, r["bron_naam"]) \
            and bz.noemt(voorstel, r["doel_naam"]):
        return voorstel[:600]
    band = (r.get("functie") or r["relation_type"].replace("_", " "))
    if veld == "active_from":
        return f"Het verband tussen {r['bron_naam']} en {r['doel_naam']} ({band}) begon in {datum}."
    return f"Het verband tussen {r['bron_naam']} en {r['doel_naam']} ({band}) eindigde in {datum}."


def dien_in(api, token, r: dict, veld: str, datum: str, citatie: dict, voorstel, waar: str):
    body = {"relation_id": r["id"], "property": veld, "property_value": datum,
            "stance": "supporting", "claim": bewering_voor(r, veld, datum, voorstel),
            "reasoning": f"{MERK.format(id=r['id'])} ({'begin' if veld == 'active_from' else 'einde'}"
                         f", {waar}): het citaat noemt {datum[:4]}.",
            "citations": [citatie], "negeer_duplicaten": True}
    status, res = bz.api_post(api, token, "/api/arguments", body)
    return (res.get("id") if status == 201 else None), (None if status == 201 else f"{status} {res.get('error')}")


def leg_vast(api, token, rid: int, status: str, detail: str) -> None:
    bz.api_post(api, token, "/api/looptijd_onderzoek",
                {"relation_id": rid, "status": status, "detail": detail[:900]})


# ------------------------------------------------------------------ organisaties (2026-10-13)
def org_stand() -> dict:
    try:
        return json.loads(ORG_STAND_PAD.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def org_stand_zet(eid: int, status: str, detail: str) -> None:
    stand = org_stand()
    oud = stand.get(str(eid)) or {}
    stand[str(eid)] = {"status": status, "laatste_poging": datetime.datetime.now().isoformat(
        timespec="seconds"), "pogingen": int(oud.get("pogingen", 0)) + 1, "detail": detail[:400]}
    ORG_STAND_PAD.parent.mkdir(parents=True, exist_ok=True)
    tmp = ORG_STAND_PAD.with_suffix(".tmp")
    tmp.write_text(json.dumps(stand, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ORG_STAND_PAD)


def organisatie_kandidaten(conn, ids=None, nu=None) -> list[dict]:
    """Goedgekeurde organisaties met een goedgekeurd verband maar zonder oprichtingsdatum, zonder
    lopend active_from-argument, die aan de beurt zijn: wat het nieuws toont eerst, dan wie de
    meeste verbanden heeft."""
    nu = nu or datetime.datetime.now()
    filt, params = "", []
    if ids:
        filt = f" AND e.id IN ({','.join('?' * len(ids))})"
        params = list(ids)
    rijen = [dict(r) for r in conn.execute(f"""
        SELECT e.id, e.name, e.type, e.description, e.active_until,
               (SELECT COUNT(*) FROM relations r WHERE (r.source_id = e.id OR r.target_id = e.id)
                  AND r.status = 'goedgekeurd' AND NOT r.vervangen) AS n_rel
        FROM entities e
        WHERE e.status = 'goedgekeurd' AND NOT e.vervangen AND e.type <> 'persoon'
          AND TRIM(COALESCE(e.active_from, '')) = ''
          AND NOT EXISTS (SELECT 1 FROM arguments a WHERE a.entity_id = e.id
                          AND a.property = 'active_from' AND NOT a.vervangen
                          AND a.status <> 'verworpen')
          {filt}""", params) if r["n_rel"]]  # noqa: S608 - alleen placeholders
    stand = org_stand()
    _, ent = bc.nieuws_voorrang(conn)
    uit = [r for r in rijen if ids or mag_weer(stand.get(str(r["id"])), nu)]
    uit.sort(key=lambda r: (0 if r["id"] in ent else 1, -r["n_rel"], r["id"]))
    return uit


def web_ronde_organisatie(e: dict) -> dict:
    """Wanneer bestaat deze organisatie? → {uitkomst: gevonden|niets|fout, begin?, eind?, …}"""
    oms = f" ({e['description'][:200]})" if e.get("description") else ""
    prompt = (f"Organisatie: {e['name']} (soort: {e['type']}){oms}.\n\nZoek op het web wanneer "
              f"deze organisatie werd opgericht, en of en wanneer ze werd opgeheven of opging in "
              f"een andere organisatie. Een bron moet {e['name']} bij naam noemen. Open de pagina "
              "met WebFetch en neem het citaat dat de datum geeft teken voor teken over. "
              "Wikipedia, sociale media en deze database zelf zijn geen bron (Wikipedia mag als "
              "vindplaats: volg de voetnoot). Primaire bronnen eerst: de eigen site (over ons, "
              "geschiedenis), het register van overheidsorganisaties, Parlement.com, DNPP, "
              "KvK-nieuws, jaarverslagen, persberichten. Geen datum gevonden: gevonden=false.")
    antwoord = vraag(prompt, WEB_SCHEMA, tools=True, regels=REGELS_ORG)
    if not antwoord:
        return {"uitkomst": "fout", "toelichting": "model gaf geen bruikbaar antwoord"}
    afgevallen: list[dict] = []
    uit = {"uitkomst": "niets", "afgevallen": afgevallen,
           "toelichting": (antwoord.get("toelichting") or "")[:600]}
    if not antwoord.get("gevonden"):
        return uit
    for veld in ("begin", "eind"):
        datum = schone_datum(antwoord.get(veld))
        bron = antwoord.get(f"{veld}_bron") or {}
        if not datum or not (bron.get("url") or "").strip():
            continue
        if veld == "eind" and e.get("active_until"):
            continue
        if not noemt_jaar(bron.get("citaat"), datum):
            afgevallen.append({"url": bron.get("url"), "reden": f"citaat noemt {datum[:4]} niet"})
            continue
        goed, reden = bz.natrekken(bron, [e["name"]])
        if not goed:
            afgevallen.append({"url": bron.get("url"), "reden": reden})
            continue
        uit[veld] = {"datum": datum, "bron": goed}
    if "begin" in uit or "eind" in uit:
        uit["uitkomst"] = "gevonden"
        uit["bewering"] = (antwoord.get("bewering") or "").strip()
    return uit


def dien_in_organisatie(api, token, e: dict, veld: str, datum: str, citatie: dict, voorstel):
    if not (voorstel and datum[:4] in voorstel and bz.noemt(voorstel, e["name"])):
        voorstel = (f"{e['name']} werd opgericht in {datum}." if veld == "active_from"
                    else f"{e['name']} werd opgeheven in {datum}.")
    body = {"entity_id": e["id"], "property": veld, "property_value": datum,
            "stance": "supporting", "claim": voorstel[:600],
            "reasoning": f"Bestaan van organisatie #{e['id']} ({'oprichting' if veld == 'active_from' else 'einde'}): "
                         f"het citaat noemt {datum[:4]}.",
            "citations": [citatie], "negeer_duplicaten": True}
    status, res = bz.api_post(api, token, "/api/arguments", body)
    return (res.get("id") if status == 201 else None), (None if status == 201 else f"{status} {res.get('error')}")


def organisatie_ronde(api, token, max_web_org, ruimte, droog, meld, ids=None) -> dict:
    tel = {"organisaties_aan_de_beurt": 0, "organisaties_gevonden": 0, "organisaties_niets": 0,
           "organisaties_ingediend": 0, "organisaties_fout": 0, "web_gezocht": 0}
    if max_web_org <= 0 or ruimte <= 0:
        return tel
    conn = db()
    try:
        alle = organisatie_kandidaten(conn, ids)
    finally:
        conn.close()
    tel["organisaties_aan_de_beurt"] = len(alle)
    for e in alle[:min(max_web_org, ruimte)]:
        tel["web_gezocht"] += 1
        uit = web_ronde_organisatie(e)
        log({"organisatie": e["id"], "waar": "web", "uitkomst": uit["uitkomst"], "web_org": True,
             **{k: uit[k] for k in ("begin", "eind", "toelichting", "afgevallen") if k in uit}}, droog)
        if uit["uitkomst"] in ("fout", "niets"):
            tel["organisaties_fout" if uit["uitkomst"] == "fout" else "organisaties_niets"] += 1
            if not droog:
                org_stand_zet(e["id"], "fout" if uit["uitkomst"] == "fout" else "niets_gevonden",
                              uit.get("toelichting", ""))
            continue
        tel["organisaties_gevonden"] += 1
        for veld, sleutel in (("active_from", "begin"), ("active_until", "eind")):
            if sleutel not in uit:
                continue
            item = uit[sleutel]
            if droog:
                meld(f"  (droog) organisatie #{e['id']} {e['name']}: {veld} = {item['datum']} — "
                     f"{item['bron']['url']}")
                continue
            bron_id = bz.registreer_bron(api, token, item["bron"])
            if not bron_id:
                tel["organisaties_fout"] += 1
                continue
            citatie = {"source_id": bron_id, "quote": item["bron"]["citaat"], "methode": "verbatim_quote"}
            nieuw, fout = dien_in_organisatie(api, token, e, veld, item["datum"], citatie, uit.get("bewering"))
            tel["organisaties_ingediend" if nieuw else "organisaties_fout"] += 1
            if fout:
                meld(f"  ✗ organisatie #{e['id']}: {fout}")
        if not droog:
            org_stand_zet(e["id"], "gezocht", "datum van het web ingediend")
    return tel


def web_vandaag(sleutel: str = "web") -> int:
    vandaag = datetime.date.today().isoformat()
    try:
        with open(LOG_PATH, encoding="utf-8") as f:
            return sum(1 for regel in f if f'"ts": "{vandaag}' in regel and f'"{sleutel}": true' in regel)
    except OSError:
        return 0


def log(regel: dict, droog: bool = False) -> None:
    if droog:
        return
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"), **regel},
                           ensure_ascii=False) + "\n")


def draai(*, api=DEFAULT_API, token_pad=None, max_eigen=20, max_web=8, droog=False,
          ids=None, meld=print, dag_plafond=DAG_PLAFOND, max_web_org=0, org_ids=None) -> dict:
    conn = db()
    try:
        alle = kandidaten(conn, ids)
        eigen_cit = {}
        portie = []
        for r in alle:  # de eigen-bronnenronde: alleen verbanden die citaten dragen
            if len(portie) >= max_eigen and len(eigen_cit) >= max_eigen + max_web:
                break
            eigen_cit[r["id"]] = eigen_citaten(conn, r["id"])
            if eigen_cit[r["id"]] and len(portie) < max_eigen:
                portie.append(r)
        eigen = eigen_ronde(conn, portie) if max_eigen > 0 else {}
    finally:
        conn.close()
    tel = {"kandidaten": len(alle), "uit_eigen_bronnen": 0, "van_het_web": 0, "niets": 0,
           "fout": 0, "ingediend": 0, "web_gezocht": 0}
    if eigen.pop("_fout", False):
        tel["fout"] += 1
        meld("Datumzoeker: het model gaf geen antwoord op de eigen bronnen")
    token = None if droog else (token_pad or DEFAULT_TOKEN).read_text().strip()
    gedaan = set()
    for r in portie:
        g = eigen.get(r["id"])
        if not g:
            continue
        gedaan.add(r["id"])
        tel["uit_eigen_bronnen"] += 1
        for veld, sleutel in (("active_from", "begin"), ("active_until", "eind")):
            if sleutel not in g or (veld == "active_until" and r.get("active_until")):
                continue
            item = g[sleutel]
            citatie = {"source_id": item["source_id"], "quote": item["quote"], "methode": "verbatim_quote"}
            if droog:
                meld(f"  (droog) #{r['id']} {verband_zin(r)}: {veld} = {item['datum']} — “{item['quote'][:120]}”")
                continue
            nieuw, fout = dien_in(api, token, r, veld, item["datum"], citatie, g.get("bewering"), "eigen bron")
            tel["ingediend" if nieuw else "fout"] += 1
            if fout:
                meld(f"  ✗ #{r['id']}: {fout}")
        if not droog:
            leg_vast(api, token, r["id"], "gezocht", f"datum uit een eigen bron ingediend")
        log({"relatie": r["id"], "waar": "eigen", "gevonden": g, "web": False}, droog)
    # Stap 2: het web, voor wat de eigen bronnen niet gaven (begrensd per ronde en per dag)
    over = [r for r in alle if r["id"] not in gedaan]
    ruimte = max(0, min(max_web, dag_plafond - web_vandaag()))
    for r in over[:ruimte]:
        tel["web_gezocht"] += 1
        uit = web_ronde(r, eigen_cit.get(r["id"], []))
        log({"relatie": r["id"], "waar": "web", "uitkomst": uit["uitkomst"], "web": True,
             **{k: uit[k] for k in ("begin", "eind", "toelichting", "afgevallen") if k in uit}}, droog)
        if uit["uitkomst"] == "fout":
            tel["fout"] += 1
            if not droog:
                leg_vast(api, token, r["id"], "fout", uit.get("toelichting", ""))
            continue
        if uit["uitkomst"] == "niets":
            tel["niets"] += 1
            meld(f"  · #{r['id']} {verband_zin(r)}: geen datum gevonden")
            if not droog:
                leg_vast(api, token, r["id"], "niets_gevonden",
                         f"web: {uit.get('toelichting', '')}; afgevallen: "
                         + "; ".join(a["reden"] for a in uit.get("afgevallen", []))[:400])
            continue
        tel["van_het_web"] += 1
        for veld, sleutel in (("active_from", "begin"), ("active_until", "eind")):
            if sleutel not in uit or (veld == "active_until" and r.get("active_until")):
                continue
            item = uit[sleutel]
            if droog:
                meld(f"  (droog) #{r['id']} {verband_zin(r)}: {veld} = {item['datum']} — "
                     f"{item['bron']['url']} “{item['bron']['citaat'][:120]}”")
                continue
            bron_id = bz.registreer_bron(api, token, item["bron"])
            if not bron_id:
                tel["fout"] += 1
                continue
            citatie = {"source_id": bron_id, "quote": item["bron"]["citaat"], "methode": "verbatim_quote"}
            nieuw, fout = dien_in(api, token, r, veld, item["datum"], citatie, uit.get("bewering"), "web")
            tel["ingediend" if nieuw else "fout"] += 1
            if fout:
                meld(f"  ✗ #{r['id']}: {fout}")
        if not droog:
            leg_vast(api, token, r["id"], "gezocht", "datum van het web ingediend")
    # Stap 3 (2026-10-13): het bestaan van organisaties, met wat er van het dagbudget over is
    if max_web_org > 0:
        org = organisatie_ronde(api, token, max_web_org, max(0, DAG_PLAFOND_ORG - web_vandaag("web_org")),
                                droog, meld, org_ids)
        tel.update({k: v for k, v in org.items() if k != "web_gezocht"})
        tel["web_gezocht"] += org["web_gezocht"]
        meld(f"Datumzoeker (organisaties): {org['organisaties_aan_de_beurt']} zonder oprichtingsdatum "
             f"aan de beurt; {org['organisaties_gevonden']} gevonden, {org['organisaties_niets']} niets, "
             f"{org['organisaties_ingediend']} argument(en) ingediend{' (droog)' if droog else ''}")
    meld(f"Datumzoeker: {tel['kandidaten']} verband(en) zonder begin aan de beurt; "
         f"{tel['uit_eigen_bronnen']} uit eigen bronnen, {tel['van_het_web']} van het web, "
         f"{tel['niets']} niets gevonden, {tel['ingediend']} argument(en) ingediend"
         f"{' (droog)' if droog else ''}")
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--max-eigen", type=int, default=20, help="verbanden in de eigen-bronnenronde")
    ap.add_argument("--max-web", type=int, default=8, help="web-zoektochten per ronde")
    ap.add_argument("--max-web-org", type=int, default=2,
                    help="web-zoektochten per ronde naar het bestaan van organisaties (2026-10-13)")
    ap.add_argument("--ids", help="alleen deze verbanden (komma's), ongeacht de wachttijd")
    ap.add_argument("--org-ids", help="alleen deze organisaties (komma's), ongeacht de wachttijd")
    ap.add_argument("--droog", action="store_true", help="niets indienen of vastleggen")
    a = ap.parse_args()
    ids = [int(x) for x in a.ids.split(",")] if a.ids else None
    org_ids = [int(x) for x in a.org_ids.split(",")] if a.org_ids else None
    tel = draai(api=a.api, token_pad=Path(a.token), max_eigen=a.max_eigen, max_web=a.max_web,
                droog=a.droog, ids=ids, max_web_org=a.max_web_org, org_ids=org_ids)
    print(json.dumps(tel, ensure_ascii=False))


if __name__ == "__main__":
    main()
