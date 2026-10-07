#!/usr/bin/env python3
"""Bronzoeker — zoekt een bron waar die ontbreekt of niet volstaat (eigenaarsbesluit
2026-10-06: "als er geen bronnen zijn moet een agent op zoek gaan"; "haal de mens uit de loop
en laat agents alles doen in het propagandamodel").

Drie soorten werk (``soort``), wat lezers van de nieuws-aggregator zien eerst (nieuws_voorrang,
nieuws_doelen):
- ``voorstel``: een voorgesteld argument (praktijk-root, supporting/contradicting) waarvan de
  bronchecker zei dat de bron het niet (volledig) draagt ('twijfel'/'klopt-niet'). Wat de
  zoeker vindt, wordt een vervangend voorstel (POST /api/arguments, reasoning "Betere bron
  voor #…"); de automatische beoordeling verwerpt daarna het origineel ("vervangen door #…",
  of zonder vervanger "geen betere bron gevonden"). Zo blijft niets 14 dagen dood liggen;
- ``verband``: een goedgekeurd (of voorgesteld, met mechanisme) verband zonder enig levend
  steunend argument. Wat de zoeker vindt, wordt een nieuw steunend argument (reasoning "Bron
  voor verband #…") met beide partijen bij naam;
- ``gemerged``: een gemerged argument zonder echte bron, of waarvan de bronchecker zei dat de
  bron het niet (volledig) draagt. Wat de zoeker vindt, wordt een REVISIE (POST
  /api/arguments/<id>/revisie): dezelfde bewering — of een eerlijker, zwakkere als de bron
  alleen die draagt — met de bron als letterlijk citaat.

Per stuk:
1. een taalmodel (Claude Sonnet via de `claude`-CLI, met alleen WebSearch en WebFetch) zoekt
   een openbare, betrouwbare bron die de FEITELIJKE inhoud draagt, met een letterlijk citaat;
2. het script haalt elke voorgestelde bron zelf op en zoekt het citaat letterlijk terug
   (bronchecker.haal_bron/zoek_citaat): een citaat dat niet in de bron staat, telt niet;
3. wat standhoudt landt 'voorgesteld' (account 'bronzoeker') en gaat langs de gewone poorten:
   de bronchecker (A1, onafhankelijk), zo nodig de smaadtoets en de aanklager, en de
   immuunpoort (A7: een bronrevisie met dezelfde bewering merget op A1 alleen);
4. niets gevonden: gelogd (data/bronzoeker_pogingen.json), en het stuk komt pas na 30 dagen
   terug. Wat de bronzoeker zelf indiende, krijgt geen tweede reparatie.

Nooit: een bron verzinnen of een citaat parafraseren (het script controleert dat), het
propagandamodel, Wikipedia of sociale media als bron, iets anders schrijven dan bronnen en
argumenten.

Gebruik:
    python3 scripts/bronzoeker.py --droog --max 3     # zoeken en natrekken, niets schrijven
    python3 scripts/bronzoeker.py --max 8 --json      # echt
    python3 scripts/bronzoeker.py --ids 223           # alleen dit argument
    python3 scripts/bronzoeker.py --relaties 1714     # alleen dit verband zonder argument
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import bronchecker as bc  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
ACCOUNT = "bronzoeker"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / f"{ACCOUNT}.token"
DEFAULT_API = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "bronzoeker_log.jsonl"
POGINGEN_PATH = ROOT / "data" / "bronzoeker_pogingen.json"
MODEL = "sonnet"
LLM_TIMEOUT_S = 600
OPNIEUW_NA_DAGEN = 30          # na 'niets gevonden' of een revisie die het niet haalde
FOUT_OPNIEUW_NA_UREN = 20      # na een technische fout (model of web)
MAX_BRONNEN = 2
MIN_CITAAT_TEKENS = 20
BRONSOORTEN = ("nieuwsartikel", "rapport", "persbericht", "website", "academisch_artikel",
               "wetgeving", "dataset", "transcript", "interview", "overig")
# Nooit als bron: het model zelf, encyclopedieën en sociale media (wel als wegwijzer)
VERBODEN_HOSTS = ("wikipedia.org", "wikiwand.com", "localhost", "127.0.0.1", "twitter.com",
                  "x.com", "facebook.com", "instagram.com", "tiktok.com", "linkedin.com",
                  "reddit.com", "youtube.com")

SYSTEM_PROMPT = (
    "Je bent bronzoeker voor een onderzoeksdatabase over het Nederlandse mediasysteem. Je "
    "zoekt op het web een openbare, betrouwbare bron die de FEITELIJKE inhoud van een "
    "bewering draagt (wie, wat, wanneer) en neemt daaruit letterlijk een citaat over. Je "
    "verzint nooit een bron, url of citaat: je gebruikt alleen pagina's die je met WebFetch "
    "werkelijk hebt geopend, en je kopieert het citaat teken voor teken zoals het op de pagina "
    "staat. De duiding van de database (een mechanisme, 'invloed', 'draaideur') hoeft een bron "
    "niet te noemen. Antwoord alleen met het gevraagde JSON."
)
SCHEMA = {
    "type": "object",
    "properties": {
        "gevonden": {"type": "boolean"},
        "bewering": {"type": "string"},
        "bronnen": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "titel": {"type": "string"},
                    "uitgever": {"type": "string"},
                    "datum": {"type": "string"},
                    "soort": {"type": "string", "enum": list(BRONSOORTEN)},
                    "citaat": {"type": "string"},
                },
                "required": ["url", "titel", "uitgever", "datum", "soort", "citaat"],
                "additionalProperties": False,
            },
        },
        "toelichting": {"type": "string"},
    },
    "required": ["gevonden", "bewering", "bronnen", "toelichting"],
    "additionalProperties": False,
}


# ------------------------------------------------------------------ database (alleen-lezen)
def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# Waarom een argument 'betwist' werd (edit_log-reden): om een ontbrekende of zwakke bron —
# dan kan een betere bron het oplossen — of om de inhoud (perifeer, weerlegd, buiten het
# model): dan nooit, want een bron beslecht dat niet.
BRONREDEN = re.compile(r"sourc|geen bron|geen (?:verifieerbaar|verbatim)|"
                       r"alleen (?:een |generiek|aggregaat)|enige gevonden bron|fetchbaar|"
                       r"paywall", re.IGNORECASE)
INHOUDSREDEN = re.compile(r"perifeer|weerlegd|valt buiten|retoriek|structureel\s*!=|"
                          r"afgewezen|onjuist|klopt niet|tegenbewijs", re.IGNORECASE)


def bronprobleem(reden: str | None) -> bool:
    """Werd dit argument betwist omdat er geen (goede) bron voor was, niet om de inhoud?"""
    if not reden:
        return True  # oud corpuswerk zonder logregel: de status zegt niets over de inhoud
    return bool(BRONREDEN.search(reden)) and not INHOUDSREDEN.search(reden)


def probleem(rij) -> str | None:
    """Waarom dit argument een (betere) bron nodig heeft, of None als het dat niet heeft."""
    if rij["status"] == "betwist":
        # Alleen als het om de bron ging en er nog geen is; betwist om de inhoud of door
        # tegenargumenten beslecht een extra bron niet
        return "geen_bron" if not rij["n_echt"] and bronprobleem(rij["betwist_reden"]) else None
    if not rij["n_echt"]:
        return "geen_bron"
    if rij["a1"] == "klopt-niet":
        return "draagt_niet"
    if rij["a1"] == "twijfel":
        return "twijfel"
    return None


PROBLEEM_VOLGORDE = {"geen_argument": 0, "geen_bron": 0, "draagt_niet": 1, "twijfel": 2}
# Een voorstel wacht op dit besluit (het blokkeert nieuw werk), dan een verband zonder enig
# argument, dan wat al gemerged is
SOORT_VOLGORDE = {"voorstel": 0, "verband": 1, "gemerged": 2}
# Merktekens in de reasoning van wat de bronzoeker indient (de beoordeling herkent ze)
VERVANGING = "Betere bron voor #{id}"
VERBAND = "Bron voor verband #{id}"

_ARGUMENT_KOLOMMEN = """
        SELECT a.id, a.claim, a.reasoning, a.stance, a.property, a.property_value, a.status,
               a.relation_id, a.entity_id, a.contributed_by, r.source_id AS rel_bron,
               r.target_id AS rel_doel, r.relation_type, r.description AS rel_omschrijving,
               s.name AS bron_naam, t.name AS doel_naam,
               m.name AS mechanisme, e.name AS entiteit_naam,
               (SELECT COUNT(*) FROM citations c WHERE c.argument_id = a.id AND (
                    TRIM(COALESCE(c.quote, '')) <> ''
                    OR EXISTS (SELECT 1 FROM source_locations sl
                               WHERE sl.source_id = c.source_id))) AS n_echt,
               (SELECT verdict FROM immuun_oordelen o WHERE o.argument_id = a.id
                  AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC
                  LIMIT 1) AS a1,
               (SELECT detail FROM immuun_oordelen o WHERE o.argument_id = a.id
                  AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC
                  LIMIT 1) AS a1_detail,
               (SELECT l.reason FROM edit_log l WHERE l.table_name = 'arguments'
                  AND l.record_id = a.id AND l.action = 'disputed'
                  ORDER BY l.id DESC LIMIT 1) AS betwist_reden
        FROM arguments a
        LEFT JOIN relations r ON r.id = a.relation_id
        LEFT JOIN entities s ON s.id = r.source_id
        LEFT JOIN entities t ON t.id = r.target_id
        LEFT JOIN mechanisms m ON m.id = r.mechanism_id
        LEFT JOIN entities e ON e.id = a.entity_id
        WHERE a.parent_argument_id IS NULL AND NOT a.vervangen
          AND COALESCE(a.smaad_hold, 0) = 0
          AND a.stance IN ('supporting', 'contradicting')
          AND COALESCE(a.property, 'existence') IN ('existence', 'influence')
          AND (a.relation_id IS NOT NULL OR a.entity_id IS NOT NULL)"""


def sleutel(item: dict) -> str:
    """De sleutel in data/bronzoeker_pogingen.json: het argument-id, of 'relatie:<id>'."""
    return f"relatie:{item['relation_id']}" if item["soort"] == "verband" else str(item["id"])


def kandidaten(conn, ids=None, relaties_ids=None) -> list[dict]:
    """Alles wat een (betere) bron nodig heeft (zie de docstring bovenaan), zonder openstaande
    revisie of vervanger: wat het nieuws toont eerst, dan voorstellen, verbanden zonder
    argument en gemerged werk; binnen elk eerst zonder bron, dan 'klopt-niet', dan 'twijfel'.
    ``ids`` beperkt tot deze argumenten, ``relaties_ids`` tot deze verbanden."""
    filt, params = "", []
    if ids:
        filt = f" AND a.id IN ({','.join('?' * len(ids))})"
        params = list(ids)
    zonder_verbanden = bool(ids) and not relaties_ids
    zonder_argumenten = bool(relaties_ids) and not ids
    rijen = [] if zonder_argumenten else conn.execute(f"""{_ARGUMENT_KOLOMMEN}
          AND a.status IN ('ongecontroleerd', 'bronvermelding_nodig', 'betwist')
          AND (a.relation_id IS NULL OR r.status = 'goedgekeurd')
          AND (a.entity_id IS NULL OR e.status = 'goedgekeurd')
          AND NOT EXISTS (SELECT 1 FROM arguments v WHERE v.reviseert_id = a.id
                          AND v.status = 'voorgesteld' AND NOT v.vervangen){filt}""",
                                                  params).fetchall()  # noqa: S608
    voorstellen = [] if zonder_argumenten else conn.execute(f"""{_ARGUMENT_KOLOMMEN}
          AND a.status = 'voorgesteld' AND COALESCE(a.contributed_by, '') <> ?
          AND (a.relation_id IS NULL OR r.status IN ('goedgekeurd', 'voorgesteld'))
          AND (a.entity_id IS NULL OR e.status IN ('goedgekeurd', 'voorgesteld')){filt}""",
                                                       [ACCOUNT, *params]).fetchall()  # noqa: S608
    relaties, entiteiten = bc.nieuws_voorrang(conn)

    def voorrang(item):
        return (0 if item["relation_id"] in relaties else
                1 if {item["rel_bron"], item["rel_doel"], item.get("entity_id")} & entiteiten
                else 2)

    uit = []
    for rij in rijen:
        waarom = probleem(rij)
        if waarom is None:
            continue
        uit.append({**dict(rij), "soort": "gemerged", "probleem": waarom})
    for rij in voorstellen:
        # Alleen wat de bronchecker al las en niet (volledig) gedragen vond
        waarom = {"klopt-niet": "draagt_niet", "twijfel": "twijfel"}.get(rij["a1"])
        if waarom:
            uit.append({**dict(rij), "soort": "voorstel", "probleem": waarom})
    if not zonder_verbanden:
        uit += verbanden_zonder_argument(conn, relaties_ids)
    for item in uit:
        item["bronnen"] = bc.bronnen_van(conn, item["id"]) if item["id"] else []
        item["voorrang"] = voorrang(item)
        item["gemeld"] = relaties.get(item["relation_id"], "")
    uit.sort(key=lambda a: -(a["id"] or a["relation_id"]))
    uit.sort(key=lambda a: a["gemeld"], reverse=True)
    uit.sort(key=lambda a: (a["voorrang"], SOORT_VOLGORDE[a["soort"]],
                            PROBLEEM_VOLGORDE[a["probleem"]]))
    return uit


def verbanden_zonder_argument(conn, relaties_ids=None) -> list[dict]:
    """Verbanden zonder enig levend steunend argument (gemerged of nog in behandeling):
    goedgekeurd, of voorgesteld mét mechanisme (een kandidaat zonder mechanisme gaat eerst
    langs de mechanisme-toewijzer). Nooit wat een maintainer introk."""
    filt, params = "", []
    if relaties_ids:
        filt = f" AND r.id IN ({','.join('?' * len(relaties_ids))})"
        params = list(relaties_ids)
    return [{**dict(r), "id": None, "soort": "verband", "probleem": "geen_argument",
             "claim": "", "reasoning": None, "stance": "supporting", "property": None,
             "property_value": None, "entity_id": None, "entiteit_naam": None,
             "status": r["rel_status"], "a1": None, "a1_detail": None, "betwist_reden": None,
             "n_echt": 0}
            for r in conn.execute(f"""
        SELECT r.id AS relation_id, r.status AS rel_status, r.relation_type,
               r.description AS rel_omschrijving, r.source_id AS rel_bron,
               r.target_id AS rel_doel, s.name AS bron_naam, t.name AS doel_naam,
               m.name AS mechanisme
        FROM relations r
        JOIN entities s ON s.id = r.source_id
        JOIN entities t ON t.id = r.target_id
        JOIN mechanisms m ON m.id = r.mechanism_id
        WHERE NOT r.vervangen AND r.status IN ('goedgekeurd', 'voorgesteld')
          AND NOT EXISTS (SELECT 1 FROM arguments a WHERE a.relation_id = r.id
                          AND a.parent_argument_id IS NULL AND a.stance = 'supporting'
                          AND NOT a.vervangen AND a.status NOT IN ('verworpen', 'verouderd'))
          AND NOT EXISTS (SELECT 1 FROM edit_log l WHERE l.table_name = 'relations'
                          AND l.record_id = r.id AND l.reason LIKE 'intrekken%'){filt}""",
                                  params)]  # noqa: S608 - alleen placeholders


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
    """Na 'niets'/'gevonden' pas na 30 dagen opnieuw, na een fout na 20 uur."""
    if not poging:
        return True
    try:
        op = datetime.datetime.fromisoformat(str(poging.get("op")))
    except ValueError:
        return True
    wacht = (datetime.timedelta(hours=FOUT_OPNIEUW_NA_UREN) if poging.get("uitkomst") == "fout"
             else datetime.timedelta(days=OPNIEUW_NA_DAGEN))
    return nu - op >= wacht


# ------------------------------------------------------------------ zoeken
def prompt_voor(arg: dict) -> str:
    rol = "steunt" if arg["stance"] == "supporting" else "spreekt tegen"
    if arg["relation_id"]:
        hoe = (arg["mechanisme"] or arg["relation_type"] or "").replace("_", " ")
        doel = f"het verband '{arg['bron_naam']} → {arg['doel_naam']}' ({hoe})"
    else:
        doel = f"de entiteit '{arg['entiteit_naam']}'"
    if arg.get("soort") == "verband":
        regels = [f"Verband in de database: {arg['bron_naam']} → {arg['doel_naam']}, "
                  f"relatietype '{arg['relation_type']}', mechanisme '{hoe}'."]
        if (arg.get("rel_omschrijving") or "").strip():
            regels.append(f"Omschrijving in de database: {arg['rel_omschrijving'].strip()[:800]}")
        regels.append("Er is nog geen argument met een bron voor dit verband. Formuleer in "
                      "'bewering' de feitelijke bewering die het verband draagt (wie, wat, "
                      f"wanneer), met {arg['bron_naam']} en {arg['doel_naam']} allebei bij "
                      "naam, en zoek een bron die haar draagt.")
        return "\n".join(regels + [OPDRACHT])
    regels = [f"Bewering: {arg['claim']}",
              f"Context: dit argument {rol} {doel} in de database."]
    if (arg.get("reasoning") or "").strip():
        regels.append(f"Toelichting bij de bewering: {arg['reasoning'].strip()[:800]}")
    if arg["probleem"] == "geen_bron":
        regels.append("Er is nog geen bron voor deze bewering.")
        if arg.get("status") == "betwist" and (arg.get("betwist_reden") or "").strip():
            regels.append("Eerder bronnenonderzoek liep vast; gebruik dit als aanwijzing waar je "
                          f"(niet) moet zoeken: {arg['betwist_reden'].strip()[:900]}")
    else:
        oud = "; ".join(f"{b.get('title') or '?'} ({b.get('url') or 'geen url'})"
                        for b in arg["bronnen"]) or "?"
        waarom = (arg.get("a1_detail") or "").replace(bc.VERSIE, "").strip()
        regels.append(f"De huidige bron ({oud}) volstaat niet volgens de bronchecker: "
                      f"{waarom[:400] or 'de bron draagt de bewering niet'}. Zoek een betere.")
    return "\n".join(regels + [OPDRACHT])


OPDRACHT = (
    "\nOpdracht:\n"
    "1. Zoek (WebSearch) en lees (WebFetch) bronnen die de feiten van deze bewering dragen. "
    "Voorkeur: onafhankelijke Nederlandse kwaliteitsmedia, officiële documenten en "
    "registers, onderzoeksrapporten, wetenschappelijke publicaties. Een bron van de partij "
    "zelf (eigen site, persbericht) mag, maar zoek dan ook een onafhankelijke.\n"
    "2. Niet als bron: deze database zelf, Wikipedia (wel om naar de echte bron te zoeken), "
    "sociale media, fora, LinkedIn.\n"
    "3. Per bron: de url die je opende, de titel, de uitgever, de publicatiedatum "
    "(JJJJ-MM-DD, of JJJJ als alleen het jaar bekend is; leeg als onbekend), de soort, en een "
    "LETTERLIJK citaat van één of twee zinnen (hooguit 300 tekens) dat de feiten draagt — "
    "precies zoals het op de pagina staat.\n"
    "4. Een onafhankelijke controle leest daarna je bron en keurt elke bewering af die verder "
    "gaat dan de bron. Zorg dus dat ELK feit in 'bewering' (wie, wat, welke rol, wanneer, "
    "hoeveel, hoe vaak) in je citaat of elders op de pagina staat; laat weg wat de bron niet "
    "zegt. Draagt geen bron de bewering zoals ze er staat, maar wel een duidelijk zwakkere of "
    "preciezere versie OVER DEZELFDE PARTIJEN, die bij naam genoemd blijven, en met dezelfde "
    "strekking (het verband bestaat of bestond), geef die dan als 'bewering' en de bronnen die "
    "haar dragen. Anders is 'bewering' de oorspronkelijke tekst, ongewijzigd.\n"
    "5. Niet goed genoeg, dus gevonden = false: een algemene bewering over een sector of groep "
    "('Nederlandse nieuwssites', 'de media') in plaats van deze partijen; een bron die laat zien "
    "dat het verband niet klopt of voorbij is (noem dat dan in 'toelichting' — tegenbewijs gaat "
    "langs een andere weg het model in).\n"
    "6. Niets betrouwbaars gevonden: gevonden = false, bronnen = [], en zeg in 'toelichting' "
    "kort wat je zocht.\n"
    f"Hooguit {MAX_BRONNEN} bronnen; liever één goede dan twee matige.")


def vraag_zoeker(prompt: str) -> dict | None:
    """Eén `claude -p`-sessie met alleen WebSearch/WebFetch; het abonnement van de eigenaar."""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = [bc.CLAUDE, "-p", "--output-format", "json", "--tools", "WebSearch,WebFetch",
           "--allowedTools", "WebSearch,WebFetch", "--strict-mcp-config",
           "--setting-sources", "", "--no-session-persistence", "--model", MODEL,
           "--system-prompt", SYSTEM_PROMPT, "--json-schema", json.dumps(SCHEMA)]
    with tempfile.TemporaryDirectory(prefix="bronzoeker-") as leeg:
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


def datum_van(waarde: str | None) -> str | None:
    """'2021-03-04', '2021-03' of '2021' uit wat het model gaf; anders None."""
    m = re.search(r"\b((?:19|20)\d{2})(?:-(\d{2}))?(?:-(\d{2}))?\b", waarde or "")
    if not m:
        return None
    return "-".join(deel for deel in m.groups() if deel)


LIDWOORDEN = ("de ", "het ", "een ")


def namen_van(naam: str | None) -> set[str]:
    """Hoe een partij in een bewering genoemd wordt: haar naam zonder lidwoord, de delen tussen
    haakjes ("Meta (Facebook/Instagram)" → meta, facebook, instagram; "AD (Algemeen Dagblad)" →
    ad, algemeen dagblad) en een afkorting vooraan ("DPG Media" → dpg)."""
    buiten, _, binnen = (naam or "").partition("(")
    buiten = buiten.strip()
    for lidwoord in LIDWOORDEN:
        if buiten.lower().startswith(lidwoord):
            buiten = buiten[len(lidwoord):]
    namen = {buiten}
    namen.update(deel.strip() for deel in binnen.rstrip(") ").split("/"))
    eerste = buiten.split(" ")[0] if " " in buiten else ""
    if len(eerste) >= 2 and eerste.isupper():
        namen.add(eerste)
    return {bc.normaliseer(n) for n in namen if len(n.strip()) >= 2}


def noemt(tekst: str | None, naam: str | None) -> bool:
    """Noemt de tekst deze partij (als heel woord)?"""
    gewoon = bc.normaliseer(tekst)
    return any(re.search(rf"(?<![\w]){re.escape(n)}(?![\w])", gewoon) for n in namen_van(naam))


def verboden(url: str) -> bool:
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return True
    return (not host or "propagandamodel" in host
            or any(host == v or host.endswith("." + v) for v in VERBODEN_HOSTS))


def natrekken(bron: dict) -> tuple[dict | None, str]:
    """Haal de bron zelf op en zoek het citaat letterlijk terug. → (bron, reden)."""
    url = (bron.get("url") or "").strip()
    citaat = (bron.get("citaat") or "").strip()
    if not url.startswith(("http://", "https://")):
        return None, "geen bruikbare url"
    if verboden(url):
        return None, f"geen toegestane bron ({bc.host_van(url)})"
    if len(bc.normaliseer(citaat)) < MIN_CITAAT_TEKENS:
        return None, "citaat te kort"
    tekst, toelichting, gelezen = bc.haal_bron({"url": url}, citaat)
    if tekst is None:
        return None, f"bron niet te lezen: {toelichting}"
    gevonden, letterlijk, _pos = bc.zoek_citaat(citaat, tekst)
    if not gevonden:
        return None, f"citaat niet teruggevonden ({bc.host_van(gelezen or url)})"
    return {**bron, "url": url, "citaat": citaat, "letterlijk": letterlijk,
            "datum": datum_van(bron.get("datum"))}, "ok"


def zoek(arg: dict) -> dict:
    """→ {uitkomst: gevonden|niets|fout, bronnen, bewering, toelichting, afgevallen}."""
    antwoord = vraag_zoeker(prompt_voor(arg))
    if not antwoord:
        return {"uitkomst": "fout", "toelichting": "model gaf geen bruikbaar antwoord"}
    gehouden, afgevallen = [], []
    for bron in (antwoord.get("bronnen") or [])[:MAX_BRONNEN + 1]:
        goed, reden = natrekken(bron)
        if goed:
            if len(gehouden) < MAX_BRONNEN:
                gehouden.append(goed)
        else:
            afgevallen.append({"url": bron.get("url"), "reden": reden})
    bewering = (antwoord.get("bewering") or "").strip() or arg["claim"]
    if gehouden and not bewering:
        afgevallen.append({"url": None, "reden": "geen bewering geformuleerd"})
        gehouden = []
    # Een herformulering (en de bewering bij een verband zonder argument) blijft over dezelfde
    # partijen, bij naam (geen algemene uitspraak over een sector)
    partijen = ([arg["bron_naam"], arg["doel_naam"]] if arg["relation_id"]
                else [arg["entiteit_naam"]])
    ontbreekt = [naam for naam in partijen if naam and not noemt(bewering, naam)]
    nieuw = (arg.get("soort") == "verband"
             or bc.normaliseer(bewering) != bc.normaliseer(arg["claim"]))
    if gehouden and ontbreekt and nieuw:
        afgevallen.append({"url": None, "reden": f"bewering noemt {', '.join(ontbreekt)} niet"})
        gehouden = []
    return {"uitkomst": "gevonden" if gehouden else "niets", "bronnen": gehouden,
            "bewering": bewering, "toelichting": (antwoord.get("toelichting") or "")[:600],
            "afgevallen": afgevallen}


# ------------------------------------------------------------------ schrijven
def api_post(api, token, pad, body) -> tuple[int, dict]:
    req = urllib.request.Request(f"{api}{pad}", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    for poging in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and poging == 1:
                time.sleep(62)  # flood-rem van het bijdragers-account
                continue
            try:
                return e.code, json.loads(e.read().decode() or "{}")
            except json.JSONDecodeError:
                return e.code, {}
    return 429, {}


def registreer_bron(api, token, bron: dict) -> int | None:
    """Bron aanmaken (of de bestaande met dezelfde titel hergebruiken, met deze url erbij)."""
    body = {"title": bron["titel"].strip()[:300] or bron["url"], "source_type": bron["soort"]
            if bron.get("soort") in BRONSOORTEN else "website",
            "location": {"type": "url", "value": bron["url"]}}
    if (bron.get("uitgever") or "").strip():
        body["publisher"] = bron["uitgever"].strip()[:200]
    if bron.get("datum"):
        body["date_published"] = bron["datum"]
    status, antwoord = api_post(api, token, "/api/sources", body)
    if status not in (200, 201) or not antwoord.get("id"):
        return None
    if antwoord.get("hergebruikt"):
        api_post(api, token, f"/api/sources/{antwoord['id']}/locations",
                 {"type": "url", "value": bron["url"]})
    return int(antwoord["id"])


def indiening(arg: dict, gevonden: dict, citaties: list[dict]) -> tuple[str, dict]:
    """Wat de bronzoeker indient, per soort → (pad, body): een revisie van gemerged werk, een
    vervangend voorstel, of een nieuw steunend argument voor een verband zonder argument."""
    bewering = gevonden["bewering"].strip()
    toelichting = (gevonden.get("toelichting") or "").strip()
    if arg["soort"] == "gemerged":
        body = {"citations": citaties}
        if bc.normaliseer(bewering) != bc.normaliseer(arg["claim"]):
            body["claim"] = bewering
        return f"/api/arguments/{arg['id']}/revisie", body
    if arg["soort"] == "verband":
        merk = VERBAND.format(id=arg["relation_id"])
        return "/api/arguments", {
            "relation_id": arg["relation_id"], "stance": "supporting", "claim": bewering,
            "reasoning": f"{merk} zonder argument (bronzoeker): {toelichting}"[:1500],
            "citations": citaties, "negeer_duplicaten": True}
    waarom = (arg.get("a1_detail") or "").replace(bc.VERSIE, "").strip()
    merk = VERVANGING.format(id=arg["id"])
    body = {"stance": arg["stance"], "claim": bewering, "citations": citaties,
            "reasoning": (f"{merk} (de bronchecker: {waarom[:300] or 'bron draagt het niet'}). "
                          f"{toelichting}")[:1500],
            "negeer_duplicaten": True}
    for kolom in ("relation_id", "entity_id", "property", "property_value"):
        if arg.get(kolom) is not None:
            body[kolom] = arg[kolom]
    return "/api/arguments", body


def dien_in(api, token, arg: dict, gevonden: dict) -> tuple[int | None, str | None]:
    citaties = []
    for bron in gevonden["bronnen"]:
        sid = registreer_bron(api, token, bron)
        if sid:
            citaties.append({"source_id": sid, "quote": bron["citaat"],
                             "methode": "verbatim_quote"})
    if not citaties:
        return None, "bron niet te registreren"
    pad, body = indiening(arg, gevonden, citaties)
    status, antwoord = api_post(api, token, pad, body)
    if status != 201:
        return None, f"geweigerd ({status}): {antwoord.get('error')}"
    return antwoord.get("id"), None


# ------------------------------------------------------------------ ronde
def wacht_op_zoeker(conn, pogingen: dict | None = None) -> set[int]:
    """Voorgestelde argumenten die op een poging van de bronzoeker wachten (nog geen poging,
    of alleen een technische fout): de opruimstap verwerpt ze pas daarna."""
    pogingen = laad_pogingen() if pogingen is None else pogingen
    return {a["id"] for a in kandidaten(conn) if a["soort"] == "voorstel"
            and (pogingen.get(str(a["id"])) or {}).get("uitkomst") in (None, "fout")}


def draai(*, api=DEFAULT_API, token_pad=DEFAULT_TOKEN, max_n=8, droog=False, ids=None,
          relaties_ids=None, parallel=2, meld=print) -> dict:
    """Eén ronde. → {bekeken, gevonden, niets, fout, ingediend, per_soort}."""
    token = None
    if not droog:
        token = Path(token_pad).read_text().strip() if Path(token_pad).exists() else None
        if not token:
            raise SystemExit(f"Token niet gevonden: {token_pad} (scripts/create_user.py "
                             f"{ACCOUNT} --kind agent --provenance ... --new-token --save)")
    nu = datetime.datetime.now()
    pogingen = laad_pogingen()
    conn = db()
    try:
        alle = kandidaten(conn, ids, relaties_ids)
    finally:
        conn.close()
    gericht = bool(ids or relaties_ids)
    rijen = [a for a in alle if gericht or mag_weer(pogingen.get(sleutel(a)), nu)][:max_n]
    per_soort = {s: sum(1 for a in alle if a["soort"] == s) for s in SOORT_VOLGORDE}
    meld(f"Bronzoeker: {len(rijen)} van {len(alle)} zonder (goede) bron ("
         f"{per_soort['voorstel']} voorstel(len), {per_soort['verband']} verband(en) zonder "
         f"argument, {per_soort['gemerged']} gemerged){' (droog)' if droog else ''}")
    tel = {"bekeken": 0, "gevonden": 0, "niets": 0, "fout": 0, "ingediend": 0,
           "per_soort": {s: 0 for s in SOORT_VOLGORDE}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        toekomst = {pool.submit(zoek, a): a for a in rijen}
        for f in concurrent.futures.as_completed(toekomst):
            arg = toekomst[f]
            try:
                uitkomst = f.result()
            except Exception as exc:  # noqa: BLE001 - één fout stopt de ronde niet
                uitkomst = {"uitkomst": "fout", "toelichting": str(exc)[:300]}
            tel["bekeken"] += 1
            tel["per_soort"][arg["soort"]] += 1
            regel = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                     "soort": arg["soort"], "argument_id": arg["id"],
                     "relation_id": arg["relation_id"], "probleem": arg["probleem"], **uitkomst}
            if uitkomst["uitkomst"] == "gevonden" and not droog:
                nieuw_id, fout = dien_in(api, token, arg, uitkomst)
                regel["nieuw_id"], regel["fout"] = nieuw_id, fout
                if nieuw_id:
                    tel["ingediend"] += 1
                else:
                    uitkomst["uitkomst"] = "fout"  # niets ingediend: later opnieuw
            tel[uitkomst["uitkomst"]] += 1
            bronnen = ", ".join(bc.host_van(b["url"]) for b in uitkomst.get("bronnen") or [])
            wat = (f"verband #{arg['relation_id']}" if arg["soort"] == "verband"
                   else f"#{arg['id']}")
            meld(f"  · {wat} ({arg['soort']}, {arg['probleem']}): {uitkomst['uitkomst']}"
                 f"{' — ' + bronnen if bronnen else ''}"
                 f"{' → #' + str(regel['nieuw_id']) if regel.get('nieuw_id') else ''}")
            if not droog:
                pogingen[sleutel(arg)] = {"op": nu.isoformat(timespec="seconds"),
                                          "uitkomst": uitkomst["uitkomst"],
                                          "nieuw_id": regel.get("nieuw_id")}
                LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(LOG_PATH, "a", encoding="utf-8") as log:
                    log.write(json.dumps(regel, ensure_ascii=False) + "\n")
    if not droog:
        bewaar_pogingen(pogingen)
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--max", type=int, default=8, help="hooguit zoveel argumenten per ronde")
    ap.add_argument("--ids", default="", help="alleen deze argument-id's (komma's)")
    ap.add_argument("--relaties", default="", help="alleen deze verbanden zonder argument")
    ap.add_argument("--parallel", type=int, default=2, help="gelijktijdige zoeksessies")
    ap.add_argument("--droog", action="store_true", help="zoek en trek na, maar schrijf niets")
    ap.add_argument("--json", action="store_true", help="eindig met één JSON-regel")
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",") if x.strip().isdigit()] or None
    relaties = [int(x) for x in args.relaties.split(",") if x.strip().isdigit()] or None
    tel = draai(api=args.api, token_pad=args.token, max_n=args.max, droog=args.droog, ids=ids,
                relaties_ids=relaties, parallel=args.parallel)
    print(json.dumps(tel, ensure_ascii=False) if args.json else f"Klaar: {tel}")


if __name__ == "__main__":
    main()
