#!/usr/bin/env python3
"""Bronchecker — de onafhankelijke A1-bronherverificatie van de automatische beoordeling
(eigenaarsbesluit 2026-10-06: de eigenaar beoordeelt niets meer met de hand).

Per 'voorgesteld' evidentieel argument doet dit script wat een mens-reviewer zou doen:

1. de bron opnieuw ophalen (live, anders de archiefkopie; een LinkedIn-profiel uit de
   eigen scrape in data/linkedin/);
2. het citaat **letterlijk** terugzoeken in de opgehaalde tekst (deterministisch, geen
   model: genormaliseerde vergelijking, met een kleine marge voor spelling/leestekens);
3. een taalmodel (Claude Sonnet, via de `claude`-CLI zonder tools) laten oordelen of het
   gevonden fragment de bewering *zoals geformuleerd* draagt;
4. het oordeel schrijven als A1-herverificatie (`POST /api/arguments/<id>/herverificatie`)
   onder het eigen account `bronchecker`: klopt / twijfel / klopt-niet.

Ondergravingen (contradicting replies met reasoning) krijgen dezelfde behandeling: houdt
het bezwaar stand tegen de bron van de parent? Dan 'klopt'.

Het oordeel telt nergens in de score: het is procesmetadata voor de immuunpoort (A7) en
de opruimstap van scripts/automatische_beoordeling.py. Conservatief: een citaat dat niet
terug te vinden is, is 'twijfel', nooit 'klopt'; 'klopt-niet' alleen als de bron wél gelezen
is en de bewering niet draagt.

Versie 2 (2026-10-06, na de eerste ronde):
- het model beoordeelt alleen de FEITELIJKE inhoud; de duiding van het model zelf (welk
  mechanisme, "draaideur", "tegenmacht", "invloed") hoeft een bron niet te noemen, en kleine
  verschillen die de kern niet raken (publicatie- vs. ingangsdatum) maken het niet 'deels';
- is een bron live niet te lezen of staat het citaat er niet (meer), dan ook de Wayback-kopie;
- een technische storing (site blokkeert, time-out) geeft géén oordeel: het argument komt
  een volgende ronde terug, en pas na 3 vergeefse pogingen wordt het 'twijfel';
- ``--herzien`` bekijkt voorgestelde argumenten met een eerder twijfel-oordeel van versie 1
  opnieuw en werkt dat eigen oordeel bij (``"herzien": true``, nooit een tweede stem).

Agents doen alles (eigenaarsbesluit 2026-10-06, vervolg): ook wat al gemerged is maar nooit
gecontroleerd werd, krijgt een oordeel.
- ``--controle`` bekijkt gemergede argumenten zonder oordeel ('ongecontroleerd', of
  'bronvermelding_nodig' met een bron); scripts/automatische_beoordeling.py zet op dat
  oordeel hun status ('geverifieerd', of 'bronvermelding_nodig' als de bron de bewering niet
  draagt — dan zoekt scripts/bronzoeker.py een betere bron);
- ``--heropenen`` bekijkt wat de beoordeling verwierp op een oordeel van versie 1 opnieuw;
  bevestigt versie 2 de bron, dan heropent de beoordeling haar eigen afwijzing;
- pdf-bronnen worden gelezen via macOS PDFKit (JavaScript for Automation, geen installatie);
  ``--pdf`` bekijkt wat eerder 'twijfel' kreeg omdat de pdf niet te lezen was.
Wat lezers van de nieuws-aggregator zien (nieuws_voorrang, nieuws_doelen) gaat steeds voor.

Gebruik:
    python3 scripts/bronchecker.py --droog            # toon oordelen, schrijf niets
    python3 scripts/bronchecker.py --max 40 --json    # echt, hooguit 40 argumenten
    python3 scripts/bronchecker.py --ids 3912,3913    # alleen deze argumenten
    python3 scripts/bronchecker.py --controle --max 60  # gemerged, nooit gecontroleerd
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import difflib
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
ACCOUNT = "bronchecker"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / f"{ACCOUNT}.token"
DEFAULT_API = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "bronchecker_log.jsonl"
POGINGEN_PATH = ROOT / "data" / "bronchecker_pogingen.json"
VERSIE = "[bronchecker v2]"
MAX_POGINGEN = 3
LINKEDIN_DIR = ROOT / "data" / "linkedin"
CLAUDE = shutil.which("claude") or "/usr/local/bin/claude"
MODEL = "sonnet"
FETCH_TIMEOUT_S = 25
FETCH_MAX_BYTES = 4_000_000
LLM_TIMEOUT_S = 240
FRAGMENT_TEKENS = 1600       # tekst rond het citaat die het model ziet (elke kant)
PAGINA_TEKENS = 9000         # zonder citaat: zoveel van de pagina
MIN_PAGINA_TEKENS = 600      # minder leesbare tekst = geen bruikbare bron (JS-pagina, muur)
BIJNA_LETTERLIJK = 0.9       # difflib-ratio voor "bijna letterlijk" (spelling, leestekens)
MAX_CITATIES = 3
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36 propagandamodel-bronchecker")

SYSTEM_PROMPT = (
    "Je bent een nauwgezette bronchecker voor een onderzoeksdatabase over het Nederlandse "
    "mediasysteem. Je beoordeelt uitsluitend of een gegeven brontekst de FEITELIJKE inhoud van "
    "een bewering draagt: wie, wat, wanneer, waar. De duiding die de database eraan geeft (een "
    "mechanisme, 'draaideur', 'tegenmacht', 'invloed') is analyse van de database zelf; die hoeft "
    "een bron niet te noemen en speelt in je oordeel geen rol. Je voegt geen kennis van buiten de "
    "bron toe. Let op overdrijving, een andere persoon of organisatie, een andere periode, en "
    "feitelijke conclusies die verder gaan dan de bron. Antwoord alleen met het gevraagde JSON."
)
SCHEMA_ARGUMENT = {
    "type": "object",
    "properties": {"oordeel": {"type": "string", "enum": ["draagt", "deels", "draagt_niet"]},
                   "reden": {"type": "string"}},
    "required": ["oordeel", "reden"],
    "additionalProperties": False,
}
SCHEMA_BEZWAAR = {
    "type": "object",
    "properties": {"oordeel": {"type": "string",
                               "enum": ["houdt_stand", "deels", "houdt_geen_stand"]},
                   "reden": {"type": "string"}},
    "required": ["oordeel", "reden"],
    "additionalProperties": False,
}


# ------------------------------------------------------------------ tekst
_VERVANG = {" ": " ", "‘": "'", "’": "'", "‚": "'", "“": '"',
            "”": '"', "„": '"', "–": "-", "—": "-", "…": "...",
            "­": ""}


def normaliseer(tekst: str | None) -> str:
    """Vergelijkbare vorm: NFKC, typografische tekens vereenvoudigd, kleine letters,
    witruimte samengevouwen."""
    t = unicodedata.normalize("NFKC", tekst or "")
    for oud, nieuw in _VERVANG.items():
        t = t.replace(oud, nieuw)
    return " ".join(t.lower().split())


def html_naar_tekst(ruw: str) -> str:
    """Leesbare tekst uit HTML: scripts/stijlen weg, blokgrenzen als regels, tags weg."""
    t = re.sub(r"(?is)<(script|style|noscript|svg|template)\b.*?</\1>", " ", ruw)
    t = re.sub(r"(?is)<!--.*?-->", " ", t)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr|section|article|blockquote)>", "\n", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t)
    regels = [" ".join(r.split()) for r in t.splitlines()]
    return "\n".join(r for r in regels if r)


def zoek_citaat(citaat: str | None, tekst: str | None):
    """(gevonden, letterlijk, positie_in_genormaliseerde_tekst). Eerst exact (genormaliseerd),
    daarna 'bijna letterlijk' rond het zeldzaamste woordtrio van het citaat."""
    q, t = normaliseer(citaat), normaliseer(tekst)
    if len(q) < 12 or not t:
        return (False, False, None)
    pos = t.find(q)
    if pos >= 0:
        return (True, True, pos)
    woorden = q.split()
    if len(woorden) < 4:
        return (False, False, None)
    beste = (0.0, None)
    gezien = set()
    for i in range(len(woorden) - 2):
        trio = " ".join(woorden[i:i + 3])
        if trio in gezien:
            continue
        gezien.add(trio)
        start = t.find(trio)
        n = 0
        while start >= 0 and n < 5:
            begin = max(0, start - len(" ".join(woorden[:i])) - 5)
            venster = t[begin:begin + len(q) + 10]
            ratio = difflib.SequenceMatcher(None, q, venster).ratio()
            if ratio > beste[0]:
                beste = (ratio, begin)
            start = t.find(trio, start + 1)
            n += 1
        if beste[0] >= 0.97:
            break
    if beste[0] >= BIJNA_LETTERLIJK:
        return (True, False, beste[1])
    return (False, False, None)


def fragment(tekst: str, pos: int | None, lengte: int) -> str:
    t = normaliseer(tekst)
    if pos is None:
        return t[:PAGINA_TEKENS]
    begin = max(0, pos - FRAGMENT_TEKENS)
    return t[begin:pos + lengte + FRAGMENT_TEKENS]


def host_van(url: str | None) -> str:
    try:
        return (urlsplit(url or "").hostname or "").lower()
    except ValueError:
        return ""


# ------------------------------------------------------------------ bronnen
class _Omleiding(urllib.request.HTTPRedirectHandler):
    """Volg ook 308 (permanente omleiding met behoud van methode): Python 3.9 doet dat niet,
    en o.a. nos.nl stuurt zo door."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, 307 if code == 308 else code, msg, headers,
                                        newurl)

    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_302


OPENER = urllib.request.build_opener(_Omleiding)
# Eén verzoek tegelijk per website, met een korte pauze: anders weigeren sites (429)
_HOST_SLOTEN: dict[str, threading.Lock] = {}
_HOST_SLOTEN_LOCK = threading.Lock()
HOST_PAUZE_S = 1.5


def _host_slot(url: str) -> threading.Lock:
    host = host_van(url)
    with _HOST_SLOTEN_LOCK:
        return _HOST_SLOTEN.setdefault(host, threading.Lock())


def haal_linkedin(url: str) -> tuple[str | None, str]:
    """Een LinkedIn-profiel uit de eigen scrape (data/linkedin/*.json); LinkedIn zelf is
    achter een inlogmuur en wordt hier nooit opgehaald."""
    pad = urlsplit(url).path.rstrip("/")
    slug = pad.split("/")[-1] if pad else ""
    if not slug or not LINKEDIN_DIR.exists():
        return None, "linkedin: geen scrape gevonden"
    for bestand in sorted(LINKEDIN_DIR.glob("*.json")):
        try:
            inhoud = bestand.read_text(encoding="utf-8")
        except OSError:
            continue
        if slug.lower() in inhoud.lower() or slug.lower() in bestand.stem.lower():
            return inhoud, f"linkedin-scrape {bestand.name}"
    return None, "linkedin: geen scrape gevonden"


OSASCRIPT = shutil.which("osascript")
PDF_TIMEOUT_S = 90
# macOS PDFKit via JavaScript for Automation: leest de tekstlaag van een pdf, zonder installatie
PDF_JXA = ('ObjC.import("PDFKit"); function run(argv) { var d = $.PDFDocument.alloc'
           '.initWithURL($.NSURL.fileURLWithPath(argv[0])); return d.isNil() ? "" : '
           'ObjC.unwrap(d.string) || ""; }')


def pdf_naar_tekst(ruw: bytes) -> str | None:
    """De tekst van een pdf (macOS PDFKit); None als dat niet kan (geen macOS, scan zonder
    tekstlaag, beschadigd bestand)."""
    if not OSASCRIPT or not ruw:
        return None
    with tempfile.NamedTemporaryFile(suffix=".pdf") as bestand:
        bestand.write(ruw)
        bestand.flush()
        try:
            r = subprocess.run([OSASCRIPT, "-l", "JavaScript", "-e", PDF_JXA, bestand.name],
                               capture_output=True, text=True, timeout=PDF_TIMEOUT_S)
        except (subprocess.TimeoutExpired, OSError):
            return None
    tekst = " ".join((r.stdout or "").split())
    return tekst if r.returncode == 0 and tekst else None


def haal_url(url: str) -> tuple[str | None, str]:
    """(leesbare tekst, toelichting). None bij een fout of een niet-leesbaar formaat."""
    if "linkedin.com" in host_van(url):
        return haal_linkedin(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "nl,en;q=0.8",
                                               "Accept": "text/html,text/plain,*/*;q=0.5"})
    with _host_slot(url):
        try:
            with OPENER.open(req, timeout=FETCH_TIMEOUT_S) as r:
                soort = (r.headers.get("Content-Type") or "").lower()
                ruw = r.read(FETCH_MAX_BYTES)
                charset = r.headers.get_content_charset() or "utf-8"
        except urllib.error.HTTPError as e:
            return None, f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            return None, f"onbereikbaar ({type(e).__name__})"
        finally:
            time.sleep(HOST_PAUZE_S)
    if "pdf" in soort or ruw[:5] == b"%PDF-":
        tekst = pdf_naar_tekst(ruw)
        if not tekst:
            return None, "pdf: niet automatisch leesbaar"
        return tekst, f"pdf opgehaald ({len(tekst)} tekens)"
    tekst = ruw.decode(charset, errors="replace")
    if "html" in soort or "<html" in tekst[:2000].lower():
        tekst = html_naar_tekst(tekst)
    return tekst, f"opgehaald ({len(tekst)} tekens)"


def wayback_url(url: str | None) -> str | None:
    """De dichtstbijzijnde Wayback-kopie (ruwe pagina, zonder balk), of None."""
    if not url or "linkedin.com" in host_van(url):
        return None
    api = "https://archive.org/wayback/available?url=" + urllib.request.quote(url, safe="")
    try:
        with OPENER.open(urllib.request.Request(api, headers={"User-Agent": UA}),
                         timeout=FETCH_TIMEOUT_S) as r:
            data = json.loads(r.read().decode("utf-8", errors="replace") or "{}")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None
    kopie = (data.get("archived_snapshots") or {}).get("closest") or {}
    if not kopie.get("available") or not kopie.get("timestamp"):
        return None
    return f"https://web.archive.org/web/{kopie['timestamp']}id_/{url}"


def haal_bron(bron: dict, citaat: str | None = None) -> tuple[str | None, str, str | None]:
    """Probeer de live-url, de eigen archiefkopie en zo nodig de Wayback-kopie. Met een
    citaat gaat de zoektocht door tot een versie waarin het citaat staat (pagina's veranderen,
    en sommige sites tonen bots maar een deel). → (tekst, toelichting, gebruikte url)."""
    toelichting = "geen url"
    beste: tuple[str | None, str, str | None] = (None, toelichting, None)
    kandidaten = [bron.get("url"), bron.get("archive_url")]
    geprobeerd_wayback = False
    i = 0
    while i < len(kandidaten):
        url = kandidaten[i]
        i += 1
        if url:
            tekst, toelichting = haal_url(url)
            if tekst and len(tekst) >= MIN_PAGINA_TEKENS:
                if not citaat or zoek_citaat(citaat, tekst)[0]:
                    return tekst, toelichting, url
                if beste[0] is None:
                    beste = (tekst, toelichting, url)
            elif tekst is not None:
                toelichting = f"te weinig leesbare tekst ({len(tekst)} tekens)"
        if i == len(kandidaten) and not geprobeerd_wayback:
            geprobeerd_wayback = True
            kandidaten.append(wayback_url(bron.get("url")))
    if beste[0] is not None:
        return beste
    return None, toelichting, None


# ------------------------------------------------------------------ model
def vraag_model(prompt: str, schema: dict, systeem: str | None = None,
                model: str | None = None) -> dict | None:
    """Eén `claude -p`-aanroep zonder tools/context; het abonnement van de eigenaar."""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = [CLAUDE, "-p", "--output-format", "json", "--tools", "", "--strict-mcp-config",
           "--setting-sources", "", "--no-session-persistence", "--model", model or MODEL,
           "--system-prompt", systeem or SYSTEM_PROMPT, "--json-schema", json.dumps(schema)]
    with tempfile.TemporaryDirectory(prefix="bronchecker-") as leeg:
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
    tekst = str(envelope.get("result") or "").strip().strip("`")
    if tekst.startswith("json"):
        tekst = tekst[4:]
    try:
        uit = json.loads(tekst[tekst.find("{"):tekst.rfind("}") + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return uit if isinstance(uit, dict) else None


# ------------------------------------------------------------------ database (alleen-lezen)
def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def doel_tekst(conn, arg) -> str:
    gezien = set()
    while arg["parent_argument_id"] is not None and arg["id"] not in gezien:
        gezien.add(arg["id"])
        ouder = conn.execute("SELECT * FROM arguments WHERE id = ?",
                             (arg["parent_argument_id"],)).fetchone()
        if ouder is None:
            break
        arg = ouder
    for kolom, tabel in (("role_id", "roles"), ("mechanism_id", "mechanisms"),
                         ("emergent_effect_id", "emergent_effects")):
        if arg[kolom]:
            r = conn.execute(f"SELECT name FROM {tabel} WHERE id = ?",  # noqa: S608
                             (arg[kolom],)).fetchone()
            if r:
                return f"het theorie-element '{r['name']}' en zijn plaats in het model"
    if arg["relation_id"]:
        r = conn.execute("""SELECT s.name AS bron, t.name AS doel, r.relation_type,
                                   m.name AS mech, r.description
                            FROM relations r JOIN entities s ON s.id = r.source_id
                            JOIN entities t ON t.id = r.target_id
                            LEFT JOIN mechanisms m ON m.id = r.mechanism_id
                            WHERE r.id = ?""", (arg["relation_id"],)).fetchone()
        if r:
            return f"{r['bron']} en {r['doel']}"
    if arg["entity_id"]:
        e = conn.execute("SELECT name, type FROM entities WHERE id = ?",
                         (arg["entity_id"],)).fetchone()
        if e:
            return f"{e['name']} en de wereld om haar heen"
    return "de betrokkenen"


def bronnen_van(conn, arg_id) -> list[dict]:
    rijen = conn.execute("""
        SELECT c.quote, s.id AS bron_id, s.title, s.publisher, s.date_published,
               (SELECT location FROM source_locations l WHERE l.source_id = s.id
                  AND l.location_type = 'url' ORDER BY l.id LIMIT 1) AS url,
               (SELECT location FROM source_locations l WHERE l.source_id = s.id
                  AND l.location_type = 'archive_url' ORDER BY l.id LIMIT 1) AS archive_url
        FROM citations c JOIN sources s ON s.id = c.source_id
        WHERE c.argument_id = ? ORDER BY c.id""", (arg_id,)).fetchall()
    return [dict(r) for r in rijen][:MAX_CITATIES]


def kandidaten(conn, ids=None) -> list[sqlite3.Row]:
    """Voorgestelde argumenten zonder oordeel van de bronchecker: evidentiële roots, duiding,
    aspecten, theorie-argumenten en reacties (agents doen alles, 2026-10-06). Ook onder
    smaad_hold: dit oordeel is intern en de smaadtoets bouwt erop."""
    filt, params = "", [ACCOUNT, ACCOUNT]
    if ids:
        filt = f" AND a.id IN ({','.join('?' * len(ids))})"
        params += list(ids)
    return conn.execute(f"""
        SELECT a.* FROM arguments a
        WHERE a.status = 'voorgesteld' AND NOT a.vervangen
          AND COALESCE(a.contributed_by, '') <> ?
          AND NOT EXISTS (SELECT 1 FROM immuun_oordelen o WHERE o.argument_id = a.id
                          AND o.fase = 'herverificatie' AND o.door = ?){filt}
        ORDER BY a.id DESC""", params).fetchall()  # noqa: S608 - alleen placeholders


def herzien_kandidaten(conn, ids=None) -> list[sqlite3.Row]:
    """Voorgestelde argumenten waarop de bronchecker v1 'twijfel' gaf: opnieuw bekijken."""
    filt, params = "", [ACCOUNT, VERSIE + "%"]
    if ids:
        filt = f" AND a.id IN ({','.join('?' * len(ids))})"
        params += list(ids)
    return conn.execute(f"""
        SELECT a.* FROM arguments a JOIN immuun_oordelen o ON o.argument_id = a.id
          AND o.fase = 'herverificatie' AND o.door = ?
        WHERE a.status = 'voorgesteld' AND NOT a.vervangen AND o.verdict = 'twijfel'
          AND COALESCE(o.detail, '') NOT LIKE ?{filt}
        ORDER BY a.id DESC""", params).fetchall()  # noqa: S608 - alleen placeholders


def heeft_tabel(conn, naam: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                        (naam,)).fetchone() is not None


def nieuws_voorrang(conn) -> tuple[dict[int, str], set[int]]:
    """Wat lezers van de nieuws-aggregator zien: {relatie-id: laatste melding} (nieuws_voorrang
    en de bewijsdoelen) en de entiteiten daaromheen (eindpunten, plus de namen uit het nieuws
    die de nieuws-scout onderzocht)."""
    relaties: dict[int, str] = {}
    entiteiten: set[int] = set()
    if heeft_tabel(conn, "nieuws_voorrang"):
        for r in conn.execute("SELECT relation_id, gevraagd_op FROM nieuws_voorrang"):
            relaties[r[0]] = r[1] or ""
    if heeft_tabel(conn, "nieuws_doelen"):
        for r in conn.execute("SELECT relation_id, entity_id, bijgewerkt FROM nieuws_doelen"):
            if r[0]:
                relaties[r[0]] = max(relaties.get(r[0], ""), r[2] or "")
            if r[1]:
                entiteiten.add(r[1])
    if relaties:
        ids = list(relaties)
        for start in range(0, len(ids), 500):
            deel = ids[start:start + 500]
            for r in conn.execute(f"SELECT source_id, target_id FROM relations WHERE id IN "  # noqa: S608
                                  f"({','.join('?' * len(deel))})", deel):
                entiteiten.update((r[0], r[1]))
    return relaties, entiteiten


def sorteer_op_voorrang(conn, rijen) -> list:
    """Wat het nieuws toont eerst (laatst gemeld eerst), dan wat er direct omheen ligt, dan
    de rest; binnen elke groep het nieuwste argument eerst. Rijen hebben rel_bron/rel_doel."""
    relaties, entiteiten = nieuws_voorrang(conn)

    def groep(a):
        if a["relation_id"] in relaties:
            return 0
        if {a["rel_bron"], a["rel_doel"], a["entity_id"]} & entiteiten:
            return 1
        return 2

    rijen = sorted(rijen, key=lambda a: -a["id"])
    rijen = sorted(rijen, key=lambda a: relaties.get(a["relation_id"], ""), reverse=True)
    return sorted(rijen, key=groep)


def controle_kandidaten(conn, ids=None) -> list[sqlite3.Row]:
    """Gemergede argumenten die nooit gecontroleerd zijn ('ongecontroleerd', of
    'bronvermelding_nodig' mét een bron) — evidentieel, duiding, aspect, theorie of reactie;
    onder een relatie/entiteit alleen als die goedgekeurd is — zonder oordeel van de
    bronchecker en zonder bevestiging van een ander: wat het nieuws toont eerst."""
    filt, params = "", [ACCOUNT, ACCOUNT]
    if ids:
        filt = f" AND a.id IN ({','.join('?' * len(ids))})"
        params += list(ids)
    rijen = conn.execute(f"""
        SELECT a.*, r.source_id AS rel_bron, r.target_id AS rel_doel FROM arguments a
        LEFT JOIN relations r ON r.id = a.relation_id
        LEFT JOIN entities e ON e.id = a.entity_id
        WHERE a.status IN ('ongecontroleerd', 'bronvermelding_nodig') AND NOT a.vervangen
          AND COALESCE(a.smaad_hold, 0) = 0
          AND (a.relation_id IS NULL OR r.status = 'goedgekeurd')
          AND (a.entity_id IS NULL OR e.status = 'goedgekeurd')
          AND COALESCE(a.contributed_by, '') <> ?
          AND EXISTS (SELECT 1 FROM citations c WHERE c.argument_id = a.id)
          AND NOT EXISTS (SELECT 1 FROM immuun_oordelen o WHERE o.argument_id = a.id
                          AND o.fase = 'herverificatie'
                          AND (o.door = ? OR o.verdict = 'klopt')){filt}""",
                         params).fetchall()  # noqa: S608 - alleen placeholders
    return sorteer_op_voorrang(conn, rijen)


def heropen_kandidaten(conn, ids=None) -> list[sqlite3.Row]:
    """Argumenten die de automatische beoordeling verwierp op een niet-'klopt'-oordeel van
    bronchecker v1 (die eiste ten onrechte dat een bron ook de duiding van het model noemde):
    met v2 opnieuw bekijken."""
    filt, params = "", [ACCOUNT, VERSIE + "%"]
    if ids:
        filt = f" AND a.id IN ({','.join('?' * len(ids))})"
        params += list(ids)
    return conn.execute(f"""
        SELECT a.* FROM arguments a JOIN immuun_oordelen o ON o.argument_id = a.id
          AND o.fase = 'herverificatie' AND o.door = ?
        WHERE a.status = 'verworpen' AND NOT a.vervangen AND COALESCE(a.smaad_hold, 0) = 0
          AND o.verdict <> 'klopt' AND COALESCE(o.detail, '') NOT LIKE ?
          AND (SELECT l.reason FROM edit_log l WHERE l.table_name = 'arguments'
                 AND l.record_id = a.id AND l.action = 'disputed'
                 AND l.new_value LIKE '%verworpen%' ORDER BY l.id DESC LIMIT 1)
              LIKE 'automatische beoordeling%'{filt}
        ORDER BY a.id DESC""", params).fetchall()  # noqa: S608 - alleen placeholders


def buiten_kandidaten(conn, ids=None) -> list[sqlite3.Row]:
    """Argumenten die de opruimstap na 14 dagen verwierp terwijl de bronchecker ze nooit las
    (duiding, aspecten, theorie: vóór 2026-10-06 buiten de poort): nu alsnog een oordeel;
    bevestigt het de bron, dan heropent de beoordeling haar afwijzing."""
    filt, params = "", [ACCOUNT]
    if ids:
        filt = f" AND a.id IN ({','.join('?' * len(ids))})"
        params += list(ids)
    rijen = conn.execute(f"""
        SELECT a.*, r.source_id AS rel_bron, r.target_id AS rel_doel FROM arguments a
        LEFT JOIN relations r ON r.id = a.relation_id
        WHERE a.status = 'verworpen' AND NOT a.vervangen
          AND EXISTS (SELECT 1 FROM citations c WHERE c.argument_id = a.id)
          AND NOT EXISTS (SELECT 1 FROM immuun_oordelen o WHERE o.argument_id = a.id
                          AND o.fase = 'herverificatie' AND o.door = ?)
          AND (SELECT l.reason FROM edit_log l WHERE l.table_name = 'arguments'
                 AND l.record_id = a.id AND l.action = 'disputed'
                 AND l.new_value LIKE '%verworpen%' ORDER BY l.id DESC LIMIT 1)
              LIKE 'automatische beoordeling: na % dagen niet te bevestigen%'{filt}""",
                         params).fetchall()  # noqa: S608 - alleen placeholders
    return sorteer_op_voorrang(conn, rijen)


def pdf_kandidaten(conn, ids=None) -> list[sqlite3.Row]:
    """Voorgestelde en gemergede argumenten die 'twijfel' kregen omdat hun pdf-bron niet te
    lezen was (vóór de pdf-ondersteuning via PDFKit): opnieuw, wat het nieuws toont eerst."""
    filt, params = "", [ACCOUNT, "%pdf: niet automatisch leesbaar%"]
    if ids:
        filt = f" AND a.id IN ({','.join('?' * len(ids))})"
        params += list(ids)
    rijen = conn.execute(f"""
        SELECT a.*, r.source_id AS rel_bron, r.target_id AS rel_doel FROM arguments a
        JOIN immuun_oordelen o ON o.argument_id = a.id AND o.fase = 'herverificatie'
          AND o.door = ?
        LEFT JOIN relations r ON r.id = a.relation_id
        WHERE a.status IN ('voorgesteld', 'ongecontroleerd', 'bronvermelding_nodig')
          AND NOT a.vervangen AND o.verdict = 'twijfel' AND o.detail LIKE ?{filt}""",
                         params).fetchall()  # noqa: S608 - alleen placeholders
    return sorteer_op_voorrang(conn, rijen)


# Welke argumenten een ronde bekijkt, en of het eigen eerdere oordeel wordt herzien
MODI = {
    "nieuw": (kandidaten, False),
    "herzien": (herzien_kandidaten, True),
    "controle": (controle_kandidaten, False),
    "heropenen": (heropen_kandidaten, True),
    "pdf": (pdf_kandidaten, True),
    "buiten": (buiten_kandidaten, False),
}


def _laad_pogingen() -> dict:
    try:
        return json.loads(POGINGEN_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _bewaar_pogingen(pogingen: dict) -> None:
    POGINGEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    POGINGEN_PATH.write_text(json.dumps(pogingen, indent=1), encoding="utf-8")


# ------------------------------------------------------------------ beoordelen
def beoordeel_argument(conn, arg) -> dict:
    """→ {verdict, detail, verbatim_span, bron_id}."""
    doel = doel_tekst(conn, arg)
    rol = {"supporting": "steunt", "contradicting": "spreekt tegen"}.get(arg["stance"],
                                                                       "nuanceert")
    bronnen = bronnen_van(conn, arg["id"])
    if not bronnen:
        return {"verdict": "twijfel", "detail": "geen bron aan dit argument gekoppeld"}
    uitkomsten = []
    for bron in bronnen:
        citaat = (bron.get("quote") or "").strip()
        tekst, toelichting, url = haal_bron(bron, citaat or None)
        if tekst is None:
            # Technische storing: geen oordeel, het argument komt een volgende ronde terug
            uitkomsten.append({"verdict": None, "bron_id": bron["bron_id"],
                               "detail": f"bron niet te lezen: {toelichting}"})
            continue
        gevonden, letterlijk, pos = zoek_citaat(citaat, tekst) if citaat else (False, False, None)
        if citaat and not gevonden:
            uitkomsten.append({"verdict": "twijfel", "bron_id": bron["bron_id"],
                               "detail": f"citaat niet teruggevonden in de bron ({host_van(url)})"})
            continue
        stuk = fragment(tekst, pos, len(normaliseer(citaat)))
        prompt = (f"Bewering: {arg['claim']}\n"
                  f"Dit argument {rol} een verband tussen {doel}.\n"
                  f"Bron: {bron.get('title') or '?'} ({bron.get('publisher') or host_van(url)}, "
                  f"{bron.get('date_published') or 'datum onbekend'}) {url}\n"
                  + (f"Aangehaald citaat (in de bron teruggevonden"
                     f"{'' if letterlijk else ', bijna letterlijk'}): \"{citaat}\"\n"
                     if citaat else "Geen citaat opgegeven; beoordeel de bron zelf.\n")
                  + f"\nTekst uit de bron:\n<<<\n{stuk}\n>>>\n\n"
                  "Vraag: draagt deze bron de FEITELIJKE inhoud van de bewering?\n"
                  "- 'draagt': de bron zegt deze feiten of laat ze onmiskenbaar zien. Kleine "
                  "verschillen die de kern niet raken (publicatiedatum in plaats van ingangsdatum, "
                  "afronding, een functietitel in andere woorden) maken het niet 'deels'. De "
                  "duiding van de database (mechanisme, 'draaideur', 'tegenmacht', 'invloed') "
                  "hoeft de bron niet te noemen.\n"
                  "- 'deels': de bron draagt een duidelijk zwakkere of andere feitelijke bewering "
                  "(overdrijving, een andere persoon of periode, een conclusie die verder gaat).\n"
                  "- 'draagt_niet': de bron zegt het niet of zegt iets anders.\n"
                  "Geef in 'reden' één korte zin.")
        antwoord = vraag_model(prompt, SCHEMA_ARGUMENT)
        if not antwoord:
            uitkomsten.append({"verdict": "twijfel", "bron_id": bron["bron_id"],
                               "detail": "model gaf geen bruikbaar oordeel"})
            continue
        oordeel = antwoord.get("oordeel")
        verdict = {"draagt": "klopt", "deels": "twijfel", "draagt_niet": "klopt-niet"}.get(
            oordeel, "twijfel")
        uitkomsten.append({
            "verdict": verdict, "bron_id": bron["bron_id"],
            "verbatim_span": citaat if (verdict == "klopt" and citaat) else None,
            "detail": (f"{'citaat letterlijk' if letterlijk else 'citaat bijna letterlijk' if citaat else 'zonder citaat'}"
                       f" gevonden ({host_van(url)}); {antwoord.get('reden', '').strip()}"),
        })
    rang = {"klopt": 0, "twijfel": 1, "klopt-niet": 2, None: 3}
    return min(uitkomsten, key=lambda u: rang[u["verdict"]])


def beoordeel_bezwaar(conn, reply) -> dict:
    """Ondergraving: houdt het bezwaar stand tegen de bron van de parent?"""
    ouder = conn.execute("SELECT * FROM arguments WHERE id = ?",
                         (reply["parent_argument_id"],)).fetchone()
    if ouder is None:
        return {"verdict": "twijfel", "detail": "parent niet gevonden"}
    doel = doel_tekst(conn, ouder)
    delen = []
    for bron in bronnen_van(conn, ouder["id"]):
        citaat = (bron.get("quote") or "").strip()
        tekst, toelichting, url = haal_bron(bron, citaat or None)
        regel = (f"- Bron: {bron.get('title') or '?'} ({bron.get('publisher') or host_van(url)}) "
                 f"{bron.get('url') or ''}\n  Citaat: \"{citaat}\"")
        if tekst:
            _g, _l, pos = zoek_citaat(citaat, tekst) if citaat else (False, False, None)
            regel += f"\n  Tekst uit die bron:\n<<<\n{fragment(tekst, pos, len(citaat))[:4000]}\n>>>"
        else:
            regel += f"\n  (bron zelf niet te lezen: {toelichting})"
        delen.append(regel)
    prompt = (f"Argument in de database (over een verband tussen {doel}): {ouder['claim']}\n"
              + ("\n".join(delen) if delen else "(geen bron bij dit argument)")
              + f"\n\nBezwaar tegen dat argument: {reply['claim']}\n"
              f"Redenering van het bezwaar: {reply['reasoning']}\n\n"
              "Vraag: houdt het bezwaar stand? 'houdt_stand' als de bron het argument inderdaad "
              "niet (of niet volledig) draagt zoals het bezwaar zegt, of als de aangewezen "
              "redeneerfout er echt is; 'houdt_geen_stand' als de bron het argument wel draagt; "
              "'deels' bij twijfel. Geef in 'reden' één korte zin.")
    antwoord = vraag_model(prompt, SCHEMA_BEZWAAR)
    if not antwoord:
        return {"verdict": "twijfel", "detail": "model gaf geen bruikbaar oordeel"}
    verdict = {"houdt_stand": "klopt", "deels": "twijfel",
               "houdt_geen_stand": "klopt-niet"}.get(antwoord.get("oordeel"), "twijfel")
    return {"verdict": verdict,
            "detail": f"bezwaar {'houdt stand' if verdict == 'klopt' else 'getoetst'}: "
                      f"{antwoord.get('reden', '').strip()}"}


def beoordeel(conn, arg) -> dict:
    if (arg["parent_argument_id"] is not None and arg["stance"] == "contradicting"
            and (arg["reasoning"] or "").strip()):
        return beoordeel_bezwaar(conn, arg)
    return beoordeel_argument(conn, arg)


# ------------------------------------------------------------------ schrijven
def post_oordeel(api, token, arg_id, uitkomst, herzien=False) -> tuple[int, dict]:
    body = {"verdict": uitkomst["verdict"],
            "detail": (f"{VERSIE} " + (uitkomst.get("detail") or ""))[:1500]}
    if herzien:
        body["herzien"] = True
    if uitkomst.get("verbatim_span"):
        body["verbatim_span"] = uitkomst["verbatim_span"]
    if uitkomst.get("bron_id"):
        body["bron_id"] = uitkomst["bron_id"]
    req = urllib.request.Request(f"{api}/api/arguments/{arg_id}/herverificatie",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    for poging in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and poging == 1:
                time.sleep(62)  # flood-rem van het bijdragers-account: wacht en probeer opnieuw
                continue
            try:
                return e.code, json.loads(e.read().decode() or "{}")
            except json.JSONDecodeError:
                return e.code, {}
    return 429, {}


def draai(*, api=DEFAULT_API, token_pad=DEFAULT_TOKEN, max_n=60, droog=False, ids=None,
          parallel=3, herzien=False, modus=None, meld=print) -> dict:
    """Eén ronde. → samenvatting {bekeken, klopt, twijfel, klopt_niet, technisch,
    geschreven, fouten}. ``modus`` (zie MODI): 'nieuw' (voorgesteld, standaard), 'herzien'
    (v1-twijfel op voorgesteld; ook via ``herzien=True``), 'controle' (gemerged, nooit
    gecontroleerd) of 'heropenen' (verworpen op een v1-oordeel)."""
    modus = modus or ("herzien" if herzien else "nieuw")
    selectie, herzien = MODI[modus]
    token = None
    if not droog:
        token = Path(token_pad).read_text().strip() if Path(token_pad).exists() else None
        if not token:
            raise SystemExit(f"Token niet gevonden: {token_pad} (scripts/create_user.py "
                             f"{ACCOUNT} --kind agent --new-token --save)")
    conn = db()
    try:
        rijen = selectie(conn, ids)[:max_n]
        meld(f"Bronchecker ({modus}): {len(rijen)} argument(en)"
             f"{' (droog)' if droog else ''}")
        tel = {"bekeken": 0, "klopt": 0, "twijfel": 0, "klopt-niet": 0, "technisch": 0,
               "geschreven": 0, "fouten": 0}
        pogingen = _laad_pogingen()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
            toekomst = {pool.submit(_beoordeel_los, a["id"]): a for a in rijen}
            for f in concurrent.futures.as_completed(toekomst):
                arg = toekomst[f]
                try:
                    uitkomst = f.result()
                except Exception as exc:  # noqa: BLE001 - één fout stopt de ronde niet
                    tel["fouten"] += 1
                    meld(f"  ✗ #{arg['id']}: {exc}")
                    continue
                tel["bekeken"] += 1
                if uitkomst["verdict"] is None:
                    # Technische storing: pas na MAX_POGINGEN rondes een twijfel-oordeel
                    sleutel = str(arg["id"])
                    pogingen[sleutel] = pogingen.get(sleutel, 0) + (0 if droog else 1)
                    if pogingen[sleutel] < MAX_POGINGEN:
                        tel["technisch"] += 1
                        meld(f"  · #{arg['id']}: later opnieuw — {uitkomst.get('detail')}")
                        continue
                    uitkomst = {**uitkomst, "verdict": "twijfel",
                                "detail": f"{MAX_POGINGEN} keer {uitkomst.get('detail')}"}
                tel[uitkomst["verdict"]] += 1
                regel = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                         "argument_id": arg["id"], "herzien": herzien, "modus": modus,
                         **uitkomst}
                if not droog:
                    status, antwoord = post_oordeel(api, token, arg["id"], uitkomst,
                                                    herzien=herzien)
                    regel["http"] = status
                    if status in (200, 201):
                        tel["geschreven"] += 1
                    elif status != 409:
                        tel["fouten"] += 1
                        regel["fout"] = antwoord.get("error")
                    time.sleep(0.3)
                meld(f"  · #{arg['id']}: {uitkomst['verdict']} — {(uitkomst.get('detail') or '')[:110]}")
                if not droog:
                    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with open(LOG_PATH, "a", encoding="utf-8") as log:
                        log.write(json.dumps(regel, ensure_ascii=False) + "\n")
        if not droog:
            _bewaar_pogingen(pogingen)
        tel["klopt_niet"] = tel.pop("klopt-niet")
        return tel
    finally:
        conn.close()


def _beoordeel_los(arg_id):
    """Elke draad zijn eigen alleen-lezen verbinding (sqlite3-objecten zijn draadgebonden)."""
    conn = db()
    try:
        arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
        return beoordeel(conn, arg)
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--max", type=int, default=60, help="hooguit zoveel argumenten per ronde")
    ap.add_argument("--ids", default="", help="alleen deze argument-id's (komma's)")
    ap.add_argument("--parallel", type=int, default=3, help="gelijktijdige modelaanroepen")
    ap.add_argument("--droog", action="store_true", help="beoordeel, maar schrijf niets")
    groep = ap.add_mutually_exclusive_group()
    groep.add_argument("--herzien", action="store_true",
                       help="voorgestelde argumenten met een v1-twijfeloordeel opnieuw bekijken")
    groep.add_argument("--controle", action="store_true",
                       help="gemergede argumenten die nooit gecontroleerd zijn")
    groep.add_argument("--heropenen", action="store_true",
                       help="argumenten die op een v1-oordeel verworpen zijn opnieuw bekijken")
    groep.add_argument("--pdf", action="store_true",
                       help="argumenten met een onleesbare pdf-bron opnieuw (nu via PDFKit)")
    groep.add_argument("--buiten", action="store_true",
                       help="wat na 14 dagen werd opgeruimd zonder dat een poort besliste")
    ap.add_argument("--json", action="store_true", help="eindig met één JSON-regel")
    args = ap.parse_args()
    ids = [int(x) for x in args.ids.split(",") if x.strip().isdigit()] or None
    modus = ("herzien" if args.herzien else "controle" if args.controle
             else "heropenen" if args.heropenen else "pdf" if args.pdf
             else "buiten" if args.buiten else "nieuw")
    tel = draai(api=args.api, token_pad=args.token, max_n=args.max, droog=args.droog,
                ids=ids, parallel=args.parallel, modus=modus)
    if args.json:
        print(json.dumps(tel, ensure_ascii=False))
    else:
        print(f"Klaar: {tel}")


if __name__ == "__main__":
    main()
