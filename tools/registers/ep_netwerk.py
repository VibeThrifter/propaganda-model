"""Het netwerk rond de Nederlandse Europarlementariërs — uitgave ophalen en lezen (Uitbreiding C;
onderzoek 2026-10-20, aanvullend op ep.py).

ep.py legt de zetel, de fractie en de nationale partij van de zittende Nederlandse leden vast. Dit
register voegt toe wat de verbanden rond die zetel laat zien, telkens gekoppeld via het EP-id van
het lid (externe id `ep_mep`, in de open data `person/<id>`, in de vergaderingen `member_id`):

  1. EP open data, API v2 (data.europarl.europa.eu; robots.txt: `*` toegestaan, Crawl-delay 2):
     de commissielidmaatschappen met rol en periode (`meps/<id>`, `corporate-bodies/<id>`) en de
     verklaringen over belangenconflicten (`meps-declarations?person-id=<id>`): per (schaduw)rapport-
     of adviesrapporteurschap de procedure, de commissie en of het lid een belangenconflict meldt.
     Van het lid alleen naam, fractie en lidmaatschappen: geen geboortedatum, e-mail, telefoon of
     kantoor.
  2. De verklaringenpagina van het lid op europarl.europa.eu (`/meps/en/<id>/<naam>/declarations`):
     de links naar de opgave van particuliere belangen (DPI) en de verklaringen van deelname aan
     evenementen van derden (de open data heeft die niet). De DPI (nieuwste versie) wordt gelezen:
     rubriek A (beroep en besturen in de drie jaar vóór het mandaat), B (bezoldigde
     nevenactiviteiten), C (lopende bestuurs- en comitéfuncties), D (deelnemingen), E (steun van
     derden). Rubriek F en G niet (daar staan ook gegevens over familieleden). Van een verklaring van
     deelname alleen de betalende derde (zonder adres), de data en de plaats; bijlagen niet.
  3. De vergaderingen die leden publiceren (europarl.europa.eu/meps/en/search-meetings, CSV-export
     per lid): datum, hoedanigheid, procedure, wie er aanwezig was en diens nummer in het
     EU-transparantieregister.
  4. Uit het EU-transparantieregister (XML-export, open data van de Commissie) alleen de
     organisaties die in die vergaderingen voorkomen en die met hoofdkantoor in Nederland: naam,
     afkorting, categorie, land, aantal EP-toegangspassen, lobbykosten van het laatste afgesloten jaar.

Robots.txt wordt per host gelezen en gevolgd zoals voor ClaudeBot (de groep 'ClaudeBot' of
'anthropic-ai' als die er is, anders '*'), met wildcards en Crawl-delay; een verboden pad stopt het
ophalen. Tussen twee verzoeken aan dezelfde host zit minstens PAUZE seconden. De robots.txt-
bestanden (sha256, gekozen groep, Crawl-delay) staan in de uitgave.

De uitgave is één JSON-bestand data/registers/ep_netwerk/ep_netwerk_<ophaaldatum>.json (+ .sha256).
Recordsleutels: 'persoon:<ep-id>', 'commissie:<ep-id>:<lidmaatschap>', 'rapporteur:<ep-id>:<DCI-id>',
'belang:<ep-id>:<rubriek>:<nr>', 'deelname:<ep-id>:<hash>', 'vergadering:<hash>', 'tr:<tr-id>'. De
recordregel is het citaat in het model. Geen schrijfacties op het model (ep_netwerk_naar_model.py).
PyMuPDF is nodig om de pdf's te lezen (zoals lobby.py); zonder blijven rubrieken A–E leeg.

    python3 tools/registers/ep_netwerk.py haal
    python3 tools/registers/ep_netwerk.py lees
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import html
import io
import json
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, UA, noemt, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "ep_netwerk"
API = "https://data.europarl.europa.eu/api/v2"
URL = f"{API}/meps/show-current"
WWW = "https://www.europarl.europa.eu"
VERGADERING_URL = WWW + "/meps/en/search-meetings?exportFormat=CSV&memberIds={}"
VERGADERING_PAGINA = WWW + "/meps/en/search-meetings"
TR_URL = "https://transparency-register.europa.eu/odplastorganisationxml_en"
MAP = DATA / BRON
LAND = "NL"
TR_LAND = "NETHERLANDS"
PAUZE = 2.0                         # minimaal per host; een hogere Crawl-delay uit robots.txt wint
ROBOT_AGENTS = ("claudebot", "anthropic-ai")
FORMAAT = "format=application%2Fld%2Bjson"
COMMISSIE_SOORTEN = ("COMMITTEE_PARLIAMENTARY_STANDING", "COMMITTEE_PARLIAMENTARY_TEMPORARY",
                     "COMMITTEE_PARLIAMENTARY_SUB", "COMMITTEE_PARLIAMENTARY_SPECIAL")
# Per soort record: titel, uitgever en vindplaats van de bron in het model (één cluster
# register:ep_netwerk, zodat het samen één bewijslijn is).
BRONNEN = {
    "open_data": ("Europees Parlement, open data (API v2): commissielidmaatschappen en verklaringen over "
                  "belangenconflicten van de Nederlandse leden, uitgave {uitgave}", "Europees Parlement", URL),
    "verklaring": ("Europees Parlement, verklaringen van leden (opgave van particuliere belangen en deelname "
                   "aan evenementen van derden), uitgave {uitgave}", "Europees Parlement", WWW + "/meps/en/home"),
    "vergadering": ("Europees Parlement, gepubliceerde vergaderingen van leden (Nederlandse "
                    "Europarlementariërs), uitgave {uitgave}", "Europees Parlement", VERGADERING_PAGINA),
}
TITEL = BRONNEN["open_data"][0]
UITGEVER = BRONNEN["open_data"][1]
SOORT_BRON = {"persoon": "open_data", "commissie": "open_data", "rapporteur": "open_data", "tr": "vergadering",
              "belang": "verklaring", "deelname": "verklaring", "vergadering": "vergadering"}


class FormaatFout(Exception):
    """De uitgave of een bron heeft niet het verwachte formaat (of robots.txt verbiedt het pad)."""


# ── robots.txt ──────────────────────────────────────────────────────────────
_ROBOTS: dict[str, dict] = {}
_LAATSTE: dict[str, float] = {}


def lees_robots(tekst: str) -> dict:
    """{'groep', 'regels': [(allow, patroon)], 'crawl_delay'} voor ClaudeBot: de groep die ClaudeBot
    of anthropic-ai noemt, anders '*'. Een groep = opeenvolgende User-agent-regels + hun regels."""
    groepen, agents, regels, vorige_ua = [], [], [], False
    for ruw in tekst.splitlines():
        regel = ruw.split("#", 1)[0].strip()
        if ":" not in regel:
            continue
        veld, waarde = (s.strip() for s in regel.split(":", 1))
        veld = veld.lower()
        if veld == "user-agent":
            if not vorige_ua and agents:
                groepen.append((agents, regels))
                agents, regels = [], []
            agents.append(waarde.lower())
            vorige_ua = True
            continue
        vorige_ua = False
        if veld in ("allow", "disallow", "crawl-delay"):
            regels.append((veld, waarde))
    if agents:
        groepen.append((agents, regels))
    gekozen = [g for g in groepen if any(a in ROBOT_AGENTS for a in g[0])]
    naam = "claudebot" if gekozen else "*"
    if not gekozen:
        gekozen = [g for g in groepen if "*" in g[0]]
    uit, vertraging = [], None
    for _agents, rs in gekozen:
        for veld, waarde in rs:
            if veld == "crawl-delay":
                try:
                    vertraging = max(vertraging or 0.0, float(waarde))
                except ValueError:
                    pass
            elif waarde or veld == "allow":
                uit.append((veld == "allow", waarde))
    return {"groep": naam, "regels": uit, "crawl_delay": vertraging}


def robots_staat_toe(robots: dict, pad: str) -> bool:
    """Langste passende regel wint, bij gelijke lengte Allow; '*' = alles, '$' = einde."""
    beste = (-1, True)
    for allow, patroon in robots["regels"]:
        if not patroon:
            continue
        rx = "".join(".*" if c == "*" else re.escape(c) for c in patroon.rstrip("$"))
        if re.match(rx + ("$" if patroon.endswith("$") else ""), pad):
            if len(patroon) > beste[0] or (len(patroon) == beste[0] and allow):
                beste = (len(patroon), allow)
    return beste[1]


def _robots(host: str) -> dict:
    if host not in _ROBOTS:
        try:
            data = _http(f"https://{host}/robots.txt", robots=False)[0]
        except urllib.error.HTTPError as e:
            if e.code not in (404, 410):
                raise FormaatFout(f"robots.txt van {host} niet te lezen ({e.code}); niets opgehaald")
            data = b""
        _ROBOTS[host] = {**lees_robots(data.decode("utf-8", "replace")),
                         "sha256": hashlib.sha256(data).hexdigest(),
                         "opgehaald": datetime.date.today().isoformat()}
    return _ROBOTS[host]


# ── ophalen ─────────────────────────────────────────────────────────────────
class _GeenDoorverwijzing(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _http(url: str, timeout: int = 120, robots: bool = True, volg: bool = True) -> tuple[bytes, dict]:
    """GET met robots.txt-controle en minstens PAUZE (of de Crawl-delay) per host."""
    deel = urllib.parse.urlsplit(url)
    host = deel.netloc
    wacht = PAUZE
    if robots:
        r = _robots(host)
        pad = deel.path + (f"?{deel.query}" if deel.query else "")
        if not robots_staat_toe(r, pad):
            raise FormaatFout(f"robots.txt van {host} ({r['groep']}) verbiedt {pad}")
        wacht = max(PAUZE, r["crawl_delay"] or 0.0)
    for poging in range(4):
        rust = wacht - (time.time() - _LAATSTE.get(host, 0.0))
        if rust > 0:
            time.sleep(rust)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            opener = urllib.request.build_opener() if volg else urllib.request.build_opener(_GeenDoorverwijzing)
            with opener.open(req, timeout=timeout) as resp:
                data, kop, code = resp.read(), dict(resp.headers), resp.status
            _LAATSTE[host] = time.time()
            if code == 202 and not data and poging < 3:   # europarl.europa.eu: 'nog bezig', leeg
                time.sleep(10)
                continue
            return data, kop
        except urllib.error.HTTPError as e:
            _LAATSTE[host] = time.time()
            if e.code in (301, 302, 303, 307, 308) and not volg:
                return b"", dict(e.headers)
            if e.code in (403, 404, 410) or poging == 3:
                raise
            time.sleep(30 * (poging + 1) if e.code in (429, 503) else 5)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            _LAATSTE[host] = time.time()
            if poging == 3:
                raise
            time.sleep(10)
    raise FormaatFout(f"niet op te halen: {url}")


def _api(pad: str) -> dict:
    teken = "&" if "?" in pad else "?"
    return json.loads(_http(f"{API}/{pad}{teken}{FORMAAT}", timeout=120)[0])


def _download(url: str, doel: Path):
    """Groot bestand (transparantieregister) in stukken naar schijf, met dezelfde robots-controle."""
    deel = urllib.parse.urlsplit(url)
    r = _robots(deel.netloc)
    if not robots_staat_toe(r, deel.path + (f"?{deel.query}" if deel.query else "")):
        raise FormaatFout(f"robots.txt van {deel.netloc} verbiedt {deel.path}")
    rust = max(PAUZE, r["crawl_delay"] or 0.0) - (time.time() - _LAATSTE.get(deel.netloc, 0.0))
    if rust > 0:
        time.sleep(rust)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=900) as resp, open(doel, "wb") as f:
        shutil.copyfileobj(resp, f, 1 << 20)
    _LAATSTE[deel.netloc] = time.time()


def _dag(waarde: str | None) -> str | None:
    """'2024-07-19T00:00:00' → '2024-07-19'; '9999-12-31…' → None (loopt); '16-07-2024' of
    '16/07/2024' → '2024-07-16'."""
    w = (waarde or "").strip()
    if w.startswith("9999"):
        return None
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", w)
    if m:
        return m.group(1)
    m = re.search(r"(\d{2})[-/.](\d{2})[-/.](\d{4})", w)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


# ── open data: leden, commissies, rapporteurschappen ────────────────────────
def _lid(m: dict, detail: dict) -> dict:
    """Alleen naam, fractie en de commissielidmaatschappen (zonder contactgegevens)."""
    commissies = []
    for x in detail.get("hasMembership") or []:
        soort = (x.get("membershipClassification") or "").rsplit("/", 1)[-1]
        if soort not in COMMISSIE_SOORTEN:
            continue
        p = x.get("memberDuring") or {}
        commissies.append({"lidmaatschap": x.get("identifier"), "org": x.get("organization"),
                           "rol": (x.get("role") or "").rsplit("/", 1)[-1], "soort": soort,
                           "van": p.get("startDate"), "tot": p.get("endDate")})
    return {"id": m["identifier"], "label": m.get("label"), "voornaam": detail.get("givenName"),
            "achternaam": detail.get("familyName"), "fractie": m.get("api:political-group"),
            "commissies": commissies}


def _rapporteurschappen(uid: str) -> list[dict]:
    uit, offset = [], 0
    while True:
        d = _api(f"meps-declarations?person-id={uid}&offset={offset}&limit=200")
        for r in d.get("data") or []:
            if not (r.get("work_type") or "").endswith("MEMBER_DECLARATION_INTEREST_CONFLICT"):
                continue
            cap = next((p.get("inCapacityOf") or {} for p in r.get("workHadParticipation") or []
                        if f"person/{uid}" in (p.get("had_participant_person") or [])), {})
            titels = r.get("title_dcterms") or {}
            if "en" not in titels:
                titels = next((e.get("title") or {} for e in r.get("is_realized_by") or []), {})
            pdf = next((m.get("is_exemplified_by") for e in r.get("is_realized_by") or []
                        for m in e.get("is_embodied_by") or []), None)
            uit.append({"id": r.get("identifier"), "datum": r.get("document_date"),
                        "titel": schoon(titels.get("en") or next(iter(titels.values()), "")),
                        "rol": (cap.get("capacityRole") or "").rsplit("/", 1)[-1] or None,
                        "procedure": cap.get("capacityActivityLabel"),
                        "commissie": (cap.get("capacityOrganization") or "").rsplit("/", 1)[-1] or None,
                        "conflict": r.get("awarenessOfConflict"),
                        "pdf": f"https://data.europarl.europa.eu/{pdf}" if pdf else None})
        offset += 200
        if offset >= int((d.get("meta") or {}).get("total") or 0):
            return uit


# ── europarl.europa.eu: verklaringenpagina en pdf's ─────────────────────────
def _verklaringenpagina(uid: str) -> str:
    """De pagina met verklaringen; het adres heeft de naam van het lid erin, en /meps/en/<id>
    verwijst ernaar door."""
    kop = _http(f"{WWW}/meps/en/{uid}", volg=False)[1]
    loc = kop.get("Location") or kop.get("location") or ""
    m = re.match(rf"^(?:{re.escape(WWW)})?(/meps/en/{uid}/[^/]+)/", loc)
    if not m:
        raise FormaatFout(f"geen doorverwijzing naar de pagina van lid {uid} ({loc!r})")
    return WWW + m.group(1) + "/declarations"


def lees_verklaringenpagina(tekst: str) -> dict[str, list[dict]]:
    """{kop: [{'url', 'titel'}]} per blok ('Declaration of private interests', 'Declarations of
    participation …'); bijlagen ('/attachments/') niet."""
    uit: dict[str, list[dict]] = {}
    delen = re.split(r'<h4 class="es_title-h4">(.*?)</h4>', tekst, flags=re.S)
    for i in range(1, len(delen), 2):
        kop, body = schoon(html.unescape(re.sub(r"<[^>]+>", " ", delen[i]))), delen[i + 1]
        for m in re.finditer(r'<a [^>]*href="([^"]+\.pdf)"[^>]*>.*?<span class="t-x">\s*(.*?)<span', body, re.S):
            if "/attachments/" in m.group(1):
                continue
            uit.setdefault(kop, []).append({"url": m.group(1), "titel": schoon(html.unescape(m.group(2)))})
    return uit


def _nieuwste_dpi(lijst: list[dict]) -> dict | None:
    """De nieuwste opgave van particuliere belangen ('Revision no 2 - 13-07-2026')."""
    if not lijst:
        return None
    return max(lijst, key=lambda d: (_dag(d.get("titel")) or "", d.get("titel") or ""))


_WAARDE = re.compile(
    r"^(x|€\s*\d[\d .,]*.*|\d[\d .,]*\s*(eur|euro|€).*|openbare informatie.*|publieke informatie.*|public information.*|"
    r"(per |every )?(maand|jaar|week|kwartaal|month|year|quarter|monthly|yearly|annually|quarterly|weekly)|"
    r"maandelijks|jaarlijks|eenmalig|one[- ]off|once|n\.?v\.?t\.?|n/a)$", re.I)
_TAAL = re.compile(r"^[A-Z]{2}$")


def _pdf_tekst(data: bytes) -> str | None:
    try:
        import fitz  # PyMuPDF, zoals lobby.py
    except ImportError:
        return None
    with fitz.open(stream=data, filetype="pdf") as doc:
        return "\n".join(p.get_text() for p in doc)


def lees_dpi(tekst: str) -> dict:
    """{'A': [{'nr', 'tekst', 'waarde'}], …, 'datum'} uit de tekst van de opgave; rubriek F en G niet."""
    uit: dict = {r: [] for r in "ABCDE"}
    delen = re.split(r"\n\(([A-G])\)\s", "\n" + tekst)
    for i in range(1, len(delen), 2):
        rubriek, body = delen[i], delen[i + 1]
        if rubriek not in uit:
            continue
        regels = [schoon(r) for r in body.split("\n")]
        regels = [r for r in regels if r and not _TAAL.match(r)]
        # de kop van de tabel eindigt bij 'Periodicity'/'Periodiciteit'; rubriek E heeft geen tabel
        kop = max((j for j, r in enumerate(regels) if re.match(r"^(Periodicity|Periodiciteit|Periodicité)$", r, re.I)),
                  default=None)
        start = kop + 1 if kop is not None else 0
        item = None
        for r in regels[start:]:
            m = re.match(r"^(\d{1,2})\.\s*(.*)$", r)
            if m and (item is None or int(m.group(1)) == item["nr"] + 1):
                item = {"nr": int(m.group(1)), "tekst": m.group(2), "waarde": []}
                uit[rubriek].append(item)
                continue
            if item is None or r.startswith("(*) Ident") or r.startswith("(*) Identit"):
                continue
            if r == "(*)":
                item["waarde"].append("(*)")
            elif item["waarde"] or _WAARDE.match(r):
                item["waarde"].append(r)
            else:
                item["tekst"] = schoon(f"{item['tekst']} {r}")
        for it in uit[rubriek]:
            it["waarde"] = schoon(" ".join(it["waarde"]).replace("(*)", " ")) or None
    m = re.search(r"(?:datum|date|Date)\s*:\s*(\d{2}/\d{2}/\d{4})", tekst)
    uit["datum"] = _dag(m.group(1)) if m else None
    return uit


TR_ID = re.compile(r"\b(\d{9,12}-\d{2})\b")


def _label(*zinnen: str) -> str:
    """Een vaste formulierzin als regex die over regeleinden heen past."""
    return "(?:" + "|".join(r"\s+".join(re.escape(w) for w in z.split()) for z in zinnen) + ")"


_STRAAT = re.compile(r"(weg|straat|laan|plein|kade|gracht|singel|dreef|steeg|rue|street|avenue|road|strasse|straße|"
                     r"boulevard|chaussee|square|place)\b", re.I)


def zonder_adres(derde: str | None) -> str | None:
    """'Nederlandse Zuivel Organisatie, Benoordenhoutseweg' → 'Nederlandse Zuivel Organisatie': een
    deel na een komma dat een straatnaam is, valt weg (een adres hoort niet in het citaat)."""
    if not derde:
        return derde
    delen = [d.strip() for d in derde.split(",")]
    def straat(deel: str) -> bool:
        w = deel.split()
        return bool(w) and (bool(_STRAAT.fullmatch(w[0])) or bool(_STRAAT.search(w[-1])))
    while len(delen) > 1 and straat(delen[-1]):
        delen.pop()
    return ", ".join(delen)


def lees_deelname(tekst: str) -> dict:
    """De derde die betaalde, de data en de plaats uit een verklaring van deelname (EN of NL).
    Van de derde alleen de naam: een stuk met een cijfer (adres, postcode) en alles daarna niet,
    een nummer uit het transparantieregister apart."""
    t = "\n".join(schoon(r) for r in tekst.split("\n") if schoon(r))

    def na(label: str, tot: str) -> str | None:
        m = re.search(label + r"\s*\n(.*?)\n(?:" + tot + ")", t, re.S | re.I)
        return schoon(m.group(1).replace("\n", " ")) if m else None
    derde, tr_ids = None, []
    m = re.search(_label("paid the expenses of the Member", "de kosten van het lid heeft betaald of vergoed",
                         "de uitgaven van het lid heeft betaald of vergoed", "de kosten van het lid",
                         "de uitgaven van het lid")
                  + r"2?\s*\n(.*?)\n(?:Yes|No|Ja|Nee|Travel:|Reis:|Reiskosten:)", t, re.S | re.I)
    if m:
        tr_ids = TR_ID.findall(m.group(1))
        regels = TR_ID.sub(" ", m.group(1)).split("\n")
        eerste = next((i for i, r in enumerate(regels) if re.search(r"\d", r)), len(regels))
        staart = []
        for deel in re.split(r",\s*", " ".join(regels[eerste:eerste + 1])):
            if re.search(r"\d", deel):
                break
            staart.append(deel)
        derde = zonder_adres(schoon(" ".join(regels[:eerste]) + " " + ", ".join(staart)).strip(" ,")) or None
    data = na(_label("of the Member's attendance at the event:", "aanwezigheid van het lid op het evenement:"),
              r"Type of event|Soort evenement|Aard van het evenement|Type evenement")
    plaats = na(_label("Venue (country, city):", "Locatie (land, stad):", "Plaats (land, stad):"),
                r"OPTIONAL|FACULTATIEVE|FACULTATIEF|COMMENTS|OPMERKINGEN")
    soort = na(r"(?:Type of event|Soort evenement|Type evenement)[^\n]*(?:\n[^\n]*){0,2}?:",
               r"DETAILS|GEGEVENS|Venue|Locatie|Plaats")
    m = re.search(r"Date:\s*(\d{2}/\d{2}/\d{4})|Datum:\s*(\d{2}/\d{2}/\d{4})", t)
    return {"derde": derde, "tr_ids": tr_ids, "data": data, "plaats": plaats, "soort": soort,
            "datum": _dag((m.group(1) or m.group(2)) if m else None)}


# ── transparantieregister ───────────────────────────────────────────────────
_ONGELDIG_TEKEN = re.compile(rb"&#(?:x0*(?:[0-8bBcCeEfF]|1[0-9a-fA-F])|0*(?:[0-8]|1[124-9]|2[0-9]|3[01]));")


def _xml_elementen(pad: Path):
    """iterparse, maar zonder tekenverwijzingen die XML 1.0 (expat) niet toestaat: de export is
    XML 1.1 en bevat soms '&#x1;' en dergelijke in vrije tekst."""
    parser = ET.XMLPullParser(events=("end",))
    rest = b""
    with open(pad, "rb") as f:
        while True:
            blok = f.read(1 << 20)
            data = rest + blok
            if blok:
                knip = data.rfind(b"&")
                knip = knip if knip >= 0 and len(data) - knip < 16 else len(data)
                data, rest = data[:knip], data[knip:]
            else:
                rest = b""
            parser.feed(_ONGELDIG_TEKEN.sub(b" ", data))
            for _ev, el in parser.read_events():
                yield el
            if not blok:
                break
    parser.close()


def _tr_subset(pad: Path, ids: set[str]) -> tuple[dict, str | None]:
    uit, export = {}, None
    for el in _xml_elementen(pad):
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "exportDate":
            export = (el.text or "")[:10]
        if tag != "interestRepresentative":
            continue
        tid = schoon(el.findtext("identificationCode"))
        land = schoon(el.findtext("headOffice/country"))
        if tid in ids or land == TR_LAND:
            kosten = el.find("financialData/closedYear/costs")
            kost = None
            if kosten is not None:
                lo, hi = kosten.findtext("range/min"), kosten.findtext("range/max")
                kost = schoon(kosten.findtext("absoluteCost")) or (f"{lo or 0}–{hi}" if hi else (f"≥{lo}" if lo else None))
            uit[tid] = {"id": tid, "naam": schoon(el.findtext("name/originalName")),
                        "afkorting": schoon(el.findtext("acronym")) or None,
                        "categorie": schoon(el.findtext("registrationCategory")) or None,
                        "land": land or None, "ep_passen": schoon(el.findtext("EPAccreditedNumber")) or None,
                        "geregistreerd": (el.findtext("registrationDate") or "")[:10] or None,
                        "kosten_eur": kost}
        el.clear()
    return uit, export


# ── haal ────────────────────────────────────────────────────────────────────
def haal(meld=print) -> Path:
    """Open data (leden, commissies, rapporteurschappen) → verklaringenpagina's (DPI, deelname) →
    vergaderingen → het transparantieregister voor wie ze spraken."""
    MAP.mkdir(parents=True, exist_ok=True)
    vandaag = datetime.date.today().isoformat()
    lijst = [m for m in _api("meps/show-current?offset=0&limit=1000")["data"]
             if m.get("api:country-of-representation") == LAND]
    if not lijst:
        raise FormaatFout("geen zittende Nederlandse leden in de open data")
    leden, commissies, rapporteurs = [], {}, {}
    for m in lijst:
        lid = _lid(m, _api(f"meps/{m['identifier']}")["data"][0])
        leden.append(lid)
        for c in lid["commissies"]:
            org = c["org"]
            if org and org not in commissies:
                b = _api(f"corporate-bodies/{org.split('/')[-1]}")["data"][0]
                commissies[org] = {"id": org, "afkorting": b.get("label"),
                                   "naam_en": schoon((b.get("prefLabel") or {}).get("en")),
                                   "naam_nl": schoon((b.get("prefLabel") or {}).get("nl")),
                                   "van": (b.get("temporal") or {}).get("startDate"),
                                   "tot": (b.get("temporal") or {}).get("endDate")}
        rapporteurs[lid["id"]] = _rapporteurschappen(lid["id"])
    meld(f"open data: {len(leden)} leden, {len(commissies)} commissies, "
         f"{sum(len(v) for v in rapporteurs.values())} verklaringen over belangenconflicten")
    verklaringen: dict[str, dict] = {}
    vergaderingen: list[dict] = []
    for lid in leden:
        uid = lid["id"]
        pagina = _verklaringenpagina(uid)
        blokken = lees_verklaringenpagina(_http(pagina)[0].decode("utf-8", "replace"))
        dpi = _nieuwste_dpi(next((v for k, v in blokken.items() if k.lower().startswith("declaration of private")), []))
        v = {"pagina": pagina, "dpi": None, "deelname": []}
        if dpi:
            data = _http(dpi["url"])[0]
            tekst = _pdf_tekst(data)
            v["dpi"] = {"titel": dpi["titel"], "url": dpi["url"], "sha256": hashlib.sha256(data).hexdigest(),
                        "gelezen": tekst is not None, **(lees_dpi(tekst) if tekst else {})}
        for d in next((v2 for k, v2 in blokken.items() if k.lower().startswith("declarations of participation")), []):
            data = _http(d["url"])[0]
            tekst = _pdf_tekst(data)
            v["deelname"].append({"titel": d["titel"], "url": d["url"], "sha256": hashlib.sha256(data).hexdigest(),
                                  **(lees_deelname(tekst) if tekst else {})})
        verklaringen[uid] = v
        data = _http(VERGADERING_URL.format(uid))[0]
        rijen = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
        if rijen and "member_id" not in rijen[0]:
            raise FormaatFout(f"vergaderingen van {uid}: onverwachte kolommen {list(rijen[0])}")
        vergaderingen.extend(r for r in rijen if r.get("member_id") == uid)
    meld(f"verklaringen gelezen; {len(vergaderingen)} vergaderingen")
    tr_ids = {schoon(x) for r in vergaderingen for x in re.split(r"[;,]", r.get("lobbyist_id") or "") if schoon(x)}
    with tempfile.TemporaryDirectory() as tmp:
        tr_pad = Path(tmp) / "tr.xml"
        _download(TR_URL, tr_pad)
        tr, tr_export = _tr_subset(tr_pad, tr_ids)
    meld(f"transparantieregister: {len(tr)} organisaties bewaard (export {tr_export})")
    data = {"bron": BRON, "uitgave": vandaag, "opgehaald": vandaag, "robots": _ROBOTS, "tr_export": tr_export,
            "leden": leden, "commissies": commissies, "rapporteurschappen": rapporteurs,
            "verklaringen": verklaringen, "vergaderingen": vergaderingen, "transparantieregister": tr}
    pad = pad_van(vandaag)
    pad.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (MAP / f"{BRON}_{vandaag}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def uitgaven() -> list[Path]:
    return sorted(MAP.glob(f"{BRON}_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"{BRON}_{uitgave}.json"


# ── lezen ───────────────────────────────────────────────────────────────────
def _hash(*delen) -> str:
    return hashlib.sha1("|".join(sleutel(str(d or "")) for d in delen).encode()).hexdigest()[:16]


def naam_van(lid: dict) -> str:
    """Zoals ep.py: ep.nl_naam(voornaam, achternaam)."""
    from ep import nl_naam
    return nl_naam(schoon(lid.get("voornaam")), schoon(lid.get("achternaam"))) or schoon(lid.get("label"))


def procedure_sleutel(ref: str | None) -> str | None:
    """'2022/0051(COD)' en 'eli/dl/proc/2022-0051' → '2022/0051'."""
    m = re.search(r"(\d{4})[/-](\d{4})", ref or "")
    return f"{m.group(1)}/{m.group(2)}" if m else None


RUBRIEK = {"A": "beroep of bestuursfunctie in de drie jaar vóór het mandaat",
           "B": "bezoldigde nevenactiviteit", "C": "lopende deelname aan een bestuur, comité of andere activiteit",
           "D": "deelneming in een onderneming", "E": "steun van derden"}
CAPACITEIT = {"Member": "lid", "Rapporteur": "rapporteur", "Shadow rapporteur": "schaduwrapporteur",
              "Rapporteur for opinion": "rapporteur voor advies", "Committee chair": "commissievoorzitter",
              "Delegation chair": "delegatievoorzitter"}
COMMISSIE_ROL = {"MEMBER": "Lid", "MEMBER_SUBSTITUTE": "Plaatsvervangend lid", "CHAIR": "Voorzitter",
                 "CHAIR_VICE": "Vicevoorzitter", "CHAIR_CO": "Covoorzitter"}
# rol in een verklaring over belangenconflicten → (hoedanigheid, gewicht); andere rollen (delegatie,
# officiële reis) zijn geen rapporteurschap
RAPPORTEUR_ROL = {"RAPPORTEUR_REPORT": ("rapporteur", 1.0), "RAPPORTEUR_SHADOW_REPORT": ("schaduwrapporteur", 1.0),
                  "RAPPORTEUR_OPINION": ("rapporteur voor advies", 0.75),
                  "RAPPORTEUR_SHADOW_OPINION": ("schaduwrapporteur voor advies", 0.75)}


def rapporteur_rol(rol: str | None) -> tuple[str, float] | None:
    if not rol or "RAPPORTEUR" not in rol:
        return None
    if rol in RAPPORTEUR_ROL:
        return RAPPORTEUR_ROL[rol]
    advies = "OPINION" in rol
    return (("schaduwrapporteur" if "SHADOW" in rol else "rapporteur") + (" voor advies" if advies else ""),
            0.75 if advies else 1.0)


def commissie_naam(org: str) -> str:
    """Naam van de commissieknoop: de Engelse naam uit het EP met '(Europees Parlement)' erachter
    (zoals '<commissie> (Tweede Kamer)' in tk.commissie_naam)."""
    return f"{schoon(org)} (Europees Parlement)"


def lees(pad: Path) -> dict:
    ruw = json.loads(pad.read_text(encoding="utf-8"))
    for veld in ("leden", "commissies", "rapporteurschappen", "verklaringen", "vergaderingen", "transparantieregister"):
        if veld not in ruw:
            raise FormaatFout(f"veld '{veld}' ontbreekt in {pad.name}")
    uitgave = ruw["uitgave"]
    tr, cm = ruw["transparantieregister"], ruw["commissies"]
    personen, records = {}, {}
    for lid in ruw["leden"]:
        uid = str(lid["id"])
        naam = naam_van(lid)
        p = {"id": uid, "naam": naam, "volledig": schoon(lid.get("label")), "roepnaam": schoon(lid.get("voornaam")),
             "achternaam": schoon(lid.get("achternaam")), "fractie": lid.get("fractie")}
        personen[uid] = p
        records[f"persoon:{uid}"] = {**p, "sleutel": f"persoon:{uid}", "soort": "persoon", "persoon_id": uid,
                                     "regel": f"Europees Parlement, open data (API v2), zittende leden voor Nederland "
                                              f"({uitgave}): {p['volledig']} · fractie {p['fractie'] or '?'}"}
        for c in lid.get("commissies") or []:
            o = cm.get(c["org"]) or {}
            if c.get("tot") or not o.get("naam_en"):
                continue  # alleen wat nu loopt
            rol = COMMISSIE_ROL.get(c["rol"], schoon(c["rol"]).replace("_", " ").capitalize() or "Lid")
            s = f"commissie:{uid}:{c['lidmaatschap']}"
            records[s] = {"sleutel": s, "soort": "commissie", "persoon_id": uid, "naam": naam,
                          "commissie": o["naam_en"], "afkorting": o.get("afkorting"), "rol": rol, "van": c.get("van"),
                          "regel": f"Europees Parlement, open data (API v2), lidmaatschap {c['lidmaatschap']}: "
                                   f"{p['volledig']} · {o['naam_en']}"
                                   + (f" ({o['afkorting']})" if o.get("afkorting") else "")
                                   + f" · {rol} · sinds {c.get('van') or '?'}"}
        for d in ruw["rapporteurschappen"].get(uid) or []:
            hoed = rapporteur_rol(d.get("rol"))
            if not hoed:
                continue
            s = f"rapporteur:{uid}:{d['id']}"
            records[s] = {"sleutel": s, "soort": "rapporteur", "persoon_id": uid, "naam": naam,
                          "hoedanigheid": hoed[0], "gewicht": hoed[1], "procedure": d.get("procedure"),
                          "procedure_sleutel": procedure_sleutel(d.get("procedure")),
                          "commissie": d.get("commissie"), "datum": d.get("datum"), "conflict": d.get("conflict"),
                          "regel": f"Europees Parlement, open data (API v2), verklaring over belangenconflicten "
                                   f"{d['id']}: {d['titel']}"}
        v = ruw["verklaringen"].get(uid) or {}
        dpi = v.get("dpi") or {}
        for rub in "ABCDE":
            for it in dpi.get(rub) or []:
                s = f"belang:{uid}:{rub}:{it['nr']}"
                records[s] = {"sleutel": s, "soort": "belang", "persoon_id": uid, "naam": naam, "rubriek": rub,
                              "nr": it["nr"], "tekst": it["tekst"], "waarde": it.get("waarde"),
                              "opgave": dpi.get("titel"), "opgave_datum": dpi.get("datum") or _dag(dpi.get("titel")),
                              "regel": f"Europees Parlement, opgave van particuliere belangen van {p['volledig']} "
                                       f"({dpi.get('titel')}): rubriek {rub} ({RUBRIEK[rub]}) nr. {it['nr']}: "
                                       f"{it['tekst']}" + (f" · {it['waarde']}" if it.get("waarde") else "")}
        for d in v.get("deelname") or []:
            if not d.get("derde"):
                continue
            d = {**d, "derde": zonder_adres(d["derde"])}
            s = f"deelname:{uid}:{_hash(d.get('url'))}"
            records[s] = {"sleutel": s, "soort": "deelname", "persoon_id": uid, "naam": naam,
                          "derde": d["derde"], "tr_ids": d.get("tr_ids") or [], "data": d.get("data"),
                          "plaats": d.get("plaats"), "soort_evenement": d.get("soort"), "titel": d.get("titel"),
                          "van": _dag(d.get("data")) or d.get("datum"),
                          "regel": f"Europees Parlement, verklaring van deelname aan een evenement van derden van "
                                   f"{p['volledig']} ({d.get('titel')}): betaald door: {d['derde']}"
                                   + (f" (transparantieregister {', '.join(d['tr_ids'])})" if d.get("tr_ids") else "")
                                   + (f" · {d['data']}" if d.get("data") else "")
                                   + (f" · {d['plaats']}" if d.get("plaats") else "")}
    for r in ruw["vergaderingen"]:
        uid = r["member_id"]
        if uid not in personen:
            continue
        tids = [schoon(x) for x in re.split(r"[;,]", r.get("lobbyist_id") or "") if schoon(x)]
        s = f"vergadering:{_hash(uid, r['meeting_date'], r['title'], r['attendees'], r['procedure_reference'], r['member_capacity'])}"
        if s in records:
            continue
        cap = CAPACITEIT.get(r["member_capacity"], schoon(r["member_capacity"]).lower())
        records[s] = {"sleutel": s, "soort": "vergadering", "persoon_id": uid, "naam": personen[uid]["naam"],
                      "datum": r["meeting_date"], "titel": schoon(r["title"]), "hoedanigheid": cap,
                      "procedure": schoon(r["procedure_reference"]) or None, "aanwezig": schoon(r["attendees"]),
                      "tr_ids": tids, "tr_namen": [tr[t]["naam"] for t in tids if t in tr],
                      "regel": f"Europees Parlement, vergaderingen van leden: {r['meeting_date']} · "
                               f"{schoon(r['member_name'])} ({cap}"
                               + (f", {schoon(r['procedure_reference'])}" if schoon(r["procedure_reference"]) else "")
                               + f") · {schoon(r['title'])} · met: {schoon(r['attendees'])}"
                               + (f" · transparantieregister: {', '.join(tids)}" if tids else "")}
    for tid, o in tr.items():
        records[f"tr:{tid}"] = {"sleutel": f"tr:{tid}", "soort": "tr", **o,
                                "regel": f"EU-transparantieregister (export {ruw.get('tr_export')}): {o['naam']}"
                                         + (f" ({o['afkorting']})" if o.get("afkorting") else "")
                                         + f" · {o.get('categorie')} · {o.get('land')} · nr. {tid}"}
    if not personen:
        raise FormaatFout("geen leden gelezen")
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "titel": TITEL.format(uitgave=uitgave), "tr_export": ruw.get("tr_export"), "robots": ruw.get("robots"),
            "personen": personen, "records": records, "tr": tr}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"{BRON}_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


RELATIETYPES = {
    "commissie": {"ambt"},
    "belang": {"bestuurder", "adviseur", "lidmaatschap", "personeel", "eigendom", "dienstverband", "ambt"},
    "deelname": {"geschenk"},
    "vergadering": {"lobbyt"},
}


def _past_bij_lid(p: dict, naam: str) -> bool:
    woorden = sleutel(naam).split()
    delen = [d for d in sleutel(p["achternaam"]).split() if len(d) >= 3]
    return bool(woorden and any(d in woorden for d in delen) and woorden[0][:1] == sleutel(p["roepnaam"])[:1])


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """De ene kant is het lid (externe id ep_mep en een passende naam), de andere de commissie,
    organisatie of derde die het record noemt. None = klopt; anders de reden."""
    if rec["soort"] not in RELATIETYPES or relatie_type not in RELATIETYPES[rec["soort"]]:
        return f"een ep_netwerkrecord '{rec['soort']}' draagt geen verband van type '{relatie_type}'"
    lid = [e for e in eindpunten if ("ep_mep", rec["persoon_id"]) in e["ids"]]
    if not lid:
        return f"geen eindpunt is Europarlementariër ep_mep:{rec['persoon_id']}"
    p = data["personen"][rec["persoon_id"]]
    if not _past_bij_lid(p, lid[0]["name"]):
        return f"'{lid[0]['name']}' past niet bij '{p['naam']}'"
    ander = [e for e in eindpunten if e is not lid[0]][0]
    if rec["soort"] == "commissie":
        return None if ander["name"] == commissie_naam(rec["commissie"]) else \
            f"eindpunt #{ander['id']} is niet '{commissie_naam(rec['commissie'])}'"
    from tk import schrijfwijzen
    namen = [ander["name"]] + [v for v, m in schrijfwijzen().items() if sleutel(m) == sleutel(ander["name"])]
    velden = {"belang": [rec.get("tekst") or ""], "deelname": [rec.get("derde") or ""],
              "vergadering": [rec.get("aanwezig") or ""] + list(rec.get("tr_namen") or [])}[rec["soort"]]
    if not any(noemt(v, n) for v in velden for n in namen):
        return f"'{ander['name']}' staat niet in het record {sleutel_r}"
    return None


if __name__ == "__main__":
    import argparse
    from collections import Counter
    ap = argparse.ArgumentParser(description="EP open data + verklaringen en vergaderingen van Nederlandse Europarlementariërs")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--uitgave")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal())
    else:
        d = lees(pad_van(a.uitgave) if a.uitgave else uitgaven()[-1])
        tel = Counter(r["soort"] for r in d["records"].values())
        print(json.dumps({"uitgave": d["uitgave"], "tr_export": d["tr_export"], "leden": len(d["personen"]),
                          "robots": {h: (r["groep"], r["crawl_delay"]) for h, r in (d.get("robots") or {}).items()},
                          **tel}, ensure_ascii=False))
