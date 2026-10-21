"""Giften aan politieke partijen (Wet financiering politieke partijen) — uitgaven ophalen en lezen
(eigenaar 2026-10-20).

De Wfpp (geldend sinds 06-06-2026; de Wet op de politieke partijen, Kamerstuk 36742, ligt nog in de
Tweede Kamer) verplicht partijen en hun neveninstellingen tot drie openbare overzichten, die de
minister van BZK als spreadsheet (ods) publiceert:
  - substantieel-<jaar>: giften van € 10.000 of meer per gever per jaar, binnen drie dagen gemeld
    (art. 25a, sinds 2023), "periodiek" bijgewerkt op rijksoverheid.nl;
  - jaar-<jaar>: het jaaroverzicht van giften van in totaal € 1.000 of meer per gever (art. 25 lid
    1 sub b; tot en met verslagjaar 2023 € 4.500), met het financieel verslag vóór 1 juli ingediend
    en in het najaar openbaar gemaakt;
  - tk<jaar>-voor / tk<jaar>-na: de overzichten rond een Tweede Kamerverkiezing.
Bron: de documentpagina's op rijksoverheid.nl (de nieuwste versies; robots.txt: geen Disallow).
Oudere overzichten die rijksoverheid.nl niet meer linkt, en wat sinds 28 april 2026 alleen op
open.overheid.nl verschijnt, haalt dit script NIET op: open.overheid.nl staat in robots.txt geen
andere robot dan Googlebot toe ('User-agent: * / Disallow: /', gezien 2026-10-20). Een mens
downloadt zo'n ods in de browser en `voeg-toe` neemt het op als uitgave (herkomst 'handmatig').

Een uitgave is één ods-bestand zoals de minister het publiceerde:
data/registers/giften/giften_<reeks>_<versie>.ods (+ .sha256, + .json met titel en vindplaats).
Een record is één gever bij één partij (of neveninstelling) in die uitgave: 'gift:<hash>', de
hash hangt alleen af van reeks, partij, neveninstelling en gever, zodat een nieuwere versie van
hetzelfde overzicht dezelfde sleutels houdt. De recordregel is het citaat.

PRIVACY. De overzichten noemen van natuurlijke personen voorletters, achternaam en woonplaats, van
rechtspersonen het adres en de uiteindelijk belanghebbende (UBO, met woonplaats). Een record
bevat nooit een adres, woonplaats of UBO: die worden alleen gelezen om te bepalen of de gever een
natuurlijk persoon, een organisatie of een persoonlijke vennootschap is (`gever_soort`). Of een
natuurlijk persoon het model in mag, beslist giften_naar_model.py (alleen wie er al als publieke
persoon in staat). De achternamen van UBO's staan alleen in `data["_ubo"]` (in het geheugen, nooit
weggeschreven), voor de tiplijst met publieke personen die al in het model staan.

Geen schrijfacties op het model (dat doet giften_naar_model.py via de REST-API).

    python3 tools/registers/giften.py haal
    python3 tools/registers/giften.py voeg-toe <ods> --url <vindplaats> [--titel …] [--versie JJJJ-MM-DD]
    python3 tools/registers/giften.py lees
"""
from __future__ import annotations

import datetime
import hashlib
import html
import http.client
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, PARTIJEN, UA, noemt, ontleed_naam, partij_naam, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "giften"
MAP = DATA / BRON
URL = ("https://www.rijksoverheid.nl/themas/overheid-en-democratie/democratie/rol-politieke-partijen/"
       "giften-en-subsidies-politieke-partijen")
UITGEVER = "Ministerie van Binnenlandse Zaken en Koninkrijksrelaties (Rijksoverheid.nl)"
TITEL = "Ministerie van BZK, {titel} (uitgave {uitgave})"
RIJK = "https://www.rijksoverheid.nl"
# Documentpagina's op rijksoverheid.nl (uit de sitemap, 2026-10-20); nieuwe worden gevonden via de
# themapagina en de links 'Meer over dit onderwerp' op deze pagina's.
PAGINAS = (
    "/documenten/2023/01/27/overzicht-substantiele-giften-aan-politieke-partijen-2023",
    "/documenten/2023/09/25/overzicht-van-giften-aan-politieke-partijen-en-hun-neveninstellingen-2022",
    "/documenten/2023/11/15/overzicht-giften-en-schulden-politieke-partijen-tweede-kamerverkiezing-2023",
    "/documenten/2024/01/11/overzicht-substantiele-giften-aan-politieke-partijen-2024",
    "/documenten/2024/01/22/aanvullend-overzicht-giften-en-schulden-politieke-partijen-tweede-kamerverkiezing-2023",
    "/documenten/2024/10/22/overzicht-giften-aan-politieke-partijen-2023",
    "/documenten/2025/01/31/overzicht-substantiele-giften-aan-politieke-partijen-2025",
    "/documenten/2025/10/22/giften-en-schulden-van-partijen-en-kandidaten-voor-de-tweede-kamerverkiezing-2025",
    "/documenten/2025/10/22/overzicht-van-giften-aan-politieke-partijen-en-hun-neveninstellingen-in-2024",
    "/documenten/2025/12/19/giften-en-schulden-van-partijen-en-kandidaten-na-de-tweede-kamerverkiezing-2025",
    "/documenten/2026/01/21/overzicht-substantiele-giften-aan-politieke-partijen-2026",
)
PAUZE = 1.0
MAANDEN = {m: i for i, m in enumerate(("januari", "februari", "maart", "april", "mei", "juni", "juli",
                                       "augustus", "september", "oktober", "november", "december"), 1)}
# Partijlabels in de overzichten die common.partij_naam niet kent → naam van de partijknoop.
EXTRA_PARTIJEN = {"gl": "GroenLinks", "pvdd": "Partij voor de Dieren", "bij1": "BIJ1", "nl plan": "NL PLAN",
                  "volt nederland": "Volt Nederland", "progressief nederland": "Progressief Nederland (PRO)",
                  "partij van de arbeid p v d a": "PvdA", "vereniging politieke partij democraten 66": "D66"}
# Partijen zonder knoop in het model (wel een label in de overzichten): als sectiekop een partij.
ANDERE_PARTIJEN = {"bvnl", "belang van nederland", "opnl", "onafhankelijke politiek nederland", "goud",
                   "code oranje", "lp", "libertaire partij", "piratenpartij", "fnp", "vrij verbond",
                   "de linie", "ellect", "partij voor de rechtsstaat", "vrede voor dieren", "nida", "jong",
                   "splinter", "nlbeter", "lijst henk krol", "oprecht", "jezus leeft", "trots op nederland",
                   "u buntu connected front", "partij voor de eenheid", "de feestpartij", "modern nederland",
                   "vrij en sociaal nederland", "wij zijn nederland", "de groenen", "partij voor de republiek"}
RECHTSVORM = re.compile(r"\b(b\.?\s?v\.?|n\.?\s?v\.?|stichting|vereniging|co[öo]peratie\w*|fonds|foundation|"
                        r"holding|beheer|groep|group|investments?|participaties|vastgoed|maatschappij|"
                        r"management|consultancy|kantoor|praktijk|ltd|gmbh|inc|v\.?o\.?f\.?|c\.?v\.?)\b", re.I)
POSTCODE = re.compile(r"\b\d{4}\s?[A-Z]{2}\b|\bpostbus\b", re.I)
INITIAAL = re.compile(r"^(?:[A-ZÀ-Ý][a-z]{0,2}\.?){1,6}$")
UBO_NAAM = re.compile(r"(?:[A-ZÀ-Ý][a-z]{0,2}\.\s?){1,6}\s*((?:(?:van|de|der|den|het|ter|ten|te|in|'t|du|la|le)\s+)*"
                      r"[A-ZÀ-Ý][\w'’-]+)")
VEILIGE_TOELICHTING = re.compile(r"^[^\d@]{0,120}$|€")
AFKORTINGEN = {"stg.", "st.", "fa.", "mij.", "mr.", "dr.", "drs.", "ir.", "prof.", "ing."}
TUSSEN = r"(?:van|de|der|den|het|ter|ten|te|in|op|'t|du|la|le)"
HOLDING_W = {"beheer", "holding", "holdings", "participaties", "participatie", "invest", "investment",
             "investments", "management", "vermogensbeheer", "ventures", "office", "familie", "family"}
VORM_W = re.compile(r"\b(stichting|stg|st|vereniging|cooperatie\w*|b\s?v|n\s?v|bv|nv|u\s?a|ua|the|de|het|"
                    r"nederland|nl|international|group|groep)\b")


def kern_sleutel(naam: str) -> str:
    """'Stg. Nederlands Ondernemersklimaat' ~ 'Stichting Nederlands Ondernemersklimaat', 'Metterwoon
    Vastgoed BV' ~ 'Metterwoon Vastgoed B.V.', 'AH lnvestment' ~ 'AH Investment': zonder rechtsvorm,
    lidwoord, 'Nederland'/'NL'/'Group' en spaties, met een 'l' voor een medeklinker aan het begin van een
    woord als 'i' (een I die als l is overgetikt)."""
    s = re.sub(r"\bl(?=[bcdfghjklmnpqrstvwxz])", "i", sleutel(naam))
    return re.sub(r"\s+", "", VORM_W.sub(" ", s)) or re.sub(r"\s+", "", s)


def zelfde_gever(a: str, b: str) -> bool:
    return noemt(a, b) or kern_sleutel(a) == kern_sleutel(b)


def namenlijsten(namen) -> tuple[set[str], set[str]]:
    """Eerste voornamen en achternamen (zonder tussenvoegsel) van natuurlijke personen."""
    voornamen, achternamen = set(), set()
    for naam in namen:
        n = ontleed_naam(naam)
        eerste = (n["voornamen"] or "").split()[0].lower() if n["voornamen"] else ""
        if re.fullmatch(r"[a-zà-ÿ'-]{3,}", eerste):
            voornamen.add(eerste)
        if n["achternaam"] and not n["tussenvoegsel"] and re.fullmatch(r"[a-zà-ÿ'-]{4,}", n["achternaam"].lower()):
            achternamen.add(n["achternaam"].lower())
    return voornamen, achternamen


def _persoonlijk(naam: str, voornamen: set[str], achternamen: set[str]) -> bool:
    """Een rechtspersoon die naar een natuurlijk persoon heet: 'Holding W. Muurmans BV', 'MF van Eck
    Beheer BV', 'Maarten de Gruijter Beheer BV', 'Van den Hoff Beheer B.V.', 'Ribbink Van den Hoek
    Familie Stichting', 'Wouter Keller Stichting', of '<achternaam> Beheer B.V.' als een gever met die
    achternaam in een overzicht staat. `voornamen`/`achternamen`: van de natuurlijke personen in de
    overzichten. Twijfel valt naar privé (giften_naar_model.py laat een publieke persoon uit het
    model door)."""
    woorden = naam.replace("&", " ").split()
    klein = [w.lower().strip(".,") for w in woorden]
    if {"familie", "family"} & set(klein) or re.search(r"familie\w*stichting", naam.lower()):
        return True
    if re.search(r"(?:^|\s)[A-Z]\.\s+(?:[a-z']+\s+)*[A-Z][a-z]", naam):        # 'W. Muurmans'
        return True
    if re.search(rf"(?:^|\s)[A-Z]{{1,3}}\s+{TUSSEN}\s+[A-Z][a-z]", naam):          # 'MF van Eck'
        return True
    holding = bool(HOLDING_W & set(klein))
    stichting = bool({"stichting", "stg", "foundation", "fonds"} & set(klein))
    if not (holding or stichting):
        return False
    kern = [w for w, k in zip(woorden, klein) if k not in HOLDING_W and not RECHTSVORM.fullmatch(k)
            and k not in ("stichting", "stg", "st", "bv", "b.v", "nv")]
    if not kern:
        return False
    i = 0
    while i < len(kern) and re.fullmatch(TUSSEN, kern[i].lower()):
        i += 1
    if holding and 0 < i < len(kern) and kern[i][:1].isupper():
        return True                                                                  # 'Van den Hoff Beheer'
    if holding and len(kern) >= 3 and re.fullmatch(r"[A-ZÀ-Ý][a-zà-ÿ]+", kern[0]) and \
            re.fullmatch(TUSSEN, kern[1].lower()) and kern[2][:1].isupper():
        return True                                                                  # 'Maarten de Gruijter Beheer'
    if kern[0].lower() in voornamen and len(kern) >= 2 and (kern[1][:1].isupper() or re.fullmatch(TUSSEN, kern[1].lower())):
        return True                                                                  # 'Maarten de Gruijter Beheer'
    return holding and len(kern) == 1 and len(kern[0]) >= 4 and kern[0].lower() in achternamen  # 'Wolters Beheer'


class FormaatFout(Exception):
    """De uitgave of de pagina heeft niet het verwachte formaat."""


# ── ophalen ─────────────────────────────────────────────────────────────────
def _get(url: str, timeout: int = 60, binair: bool = False):
    for poging in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                if binair:
                    return data, r.headers.get("Content-Disposition") or ""
                return data.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404) or poging == 3:
                raise
            time.sleep(30 * (poging + 1) if e.code in (429, 503) else 5)
        except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError):
            if poging == 3:
                raise
            time.sleep(10)
    raise FormaatFout(f"niet op te halen: {url}")


def reeks_van(titel: str) -> str | None:
    """Documenttitel → reeks: 'substantieel-2026', 'jaar-2024', 'tk2025-voor', 'tk2025-na'; None voor
    overzichten van kandidaten of schulden."""
    t = schoon(titel).lower()
    laatste = t.split(" - ")[-1]
    if "gift" not in t or re.search(r"kandidat|schulden", laatste):
        return None
    jaren = re.findall(r"\b(20\d\d)\b", t)
    if not jaren:
        return None
    if "substanti" in t:
        return f"substantieel-{jaren[-1]}"
    m = re.search(r"kamerverkiezing(?:en)?\s+(?:d\.d\.\s+\d+\s+\w+\s+)?(20\d\d)", t)
    if m:
        na = "aanvullend" in t or re.search(r"\bna\b", t) or re.search(r"\b\d+ tot en met \d+ \w+ 20\d\d$", laatste)
        return f"tk{m.group(1)}-{'na' if na else 'voor'}"
    return f"jaar-{jaren[-1]}"


def _versie(tekst: str) -> str | None:
    """'29-06-2026', 'versie 20250408', 'versie 9 januari 2025', '15-11-2023', '171123' → ISO-datum."""
    t = schoon(tekst).lower()
    m = re.search(r"\b(\d{1,2})-(\d{1,2})-(20\d\d)\b", t)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.search(r"\b(20\d\d)(\d\d)(\d\d)\b", t)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"\b(\d{1,2})\s+(" + "|".join(MAANDEN) + r")\s+(20\d\d)\b", t)
    if m:
        return f"{m.group(3)}-{MAANDEN[m.group(2)]:02d}-{int(m.group(1)):02d}"
    m = re.search(r"\b(\d\d)(\d\d)(\d\d)(?=\D*$)", t)
    if m and 1 <= int(m.group(2)) <= 12:
        return f"20{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return None


def _rijk_pagina(pad: str) -> tuple[list[dict], set[str]]:
    """De ods-downloads op een documentpagina (titel, versie, url) en de links naar verwante
    giftenpagina's."""
    pagina = _get(RIJK + pad)
    uit = []
    for m in re.finditer(r'<a class="download-list__link" href="([^"]+)"[^>]*>(.*?)</a>', pagina, re.S):
        href, blok = m.group(1), m.group(2)
        if not href.lower().endswith(".ods"):
            continue
        titel = schoon(html.unescape(re.sub(r"<[^>]+>", " ", (re.search(r'class="title">(.*?)</span>', blok, re.S)
                                                                  or [None, ""])[1])))
        meta = re.findall(r"<span>([^<]*)</span>", blok)
        versie = next((_versie(s) for s in meta if _versie(s)), None) or _versie(urllib.parse.unquote_plus(href))
        # de paginatitel (uit het pad) vóór de downloadtitel: 'aanvullend … tweede kamerverkiezing 2023 - …'
        titel = f"{pad.rsplit('/', 1)[-1].replace('-', ' ')} - {titel}"
        uit.append({"titel": titel, "versie": versie, "url": href if href.startswith("http") else RIJK + href,
                    "pagina": RIJK + pad, "herkomst": "rijksoverheid.nl"})
    links = {l for l in re.findall(r'href="(/documenten/\d{4}/\d\d/\d\d/[^"#?]*gift[^"#?]*)"', pagina)}
    return uit, links


def kandidaten(meld=print) -> list[dict]:
    """Alle giftenoverzichten (ods) die nu te vinden zijn: de themapagina en de bekende
    documentpagina's op rijksoverheid.nl (één stap verder via hun links)."""
    themapagina = _get(URL)
    paden = set(PAGINAS) | set(re.findall(r'href="(/documenten/\d{4}/\d\d/\d\d/[^"#?]*gift[^"#?]*)"', themapagina))
    gelezen, uit = set(), []
    for ronde in range(2):
        for pad in sorted(paden - gelezen):
            gelezen.add(pad)
            try:
                downloads, links = _rijk_pagina(pad)
            except urllib.error.HTTPError as e:
                meld(f"  ! {pad}: {e.code}")
                continue
            uit += [d for d in downloads if reeks_van(d["titel"]) or reeks_van(d["url"].rsplit("/", 1)[-1])]
            paden |= links
            time.sleep(PAUZE)
    for d in uit:
        d["reeks"] = reeks_van(d["titel"]) or reeks_van(urllib.parse.unquote(d["url"].rsplit("/", 1)[-1]))
    return [d for d in uit if d["reeks"]]


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("giften_*_????-??-??*.ods"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"giften_{uitgave}.ods"


def uitgave_van(pad: Path) -> str:
    return pad.stem.split("_", 1)[1]


def _bekend() -> set[str]:
    return {(MAP / f"giften_{uitgave_van(p)}.sha256").read_text().strip() for p in uitgaven()
            if (MAP / f"giften_{uitgave_van(p)}.sha256").exists()}


def _bewaar(inhoud: bytes, d: dict, naam: str, meld=print) -> Path | None:
    """Eén ods als nieuwe uitgave giften_<reeks>_<versie>.ods (+ .sha256 + .json)."""
    h = hashlib.sha256(inhoud).hexdigest()
    versie = (_versie(naam) if "versie" in naam.lower() else None) or d["versie"] or datetime.date.today().isoformat()
    uitgave = f"{d['reeks']}_{versie}"
    n = 2
    while pad_van(uitgave).exists():
        uitgave = f"{d['reeks']}_{versie}-{n}"
        n += 1
    pad = pad_van(uitgave)
    pad.write_bytes(inhoud)
    try:
        titel = _ods_titel(pad)
    except (zipfile.BadZipFile, ET.ParseError, KeyError) as e:
        pad.unlink()
        meld(f"  ! {d['url']}: geen leesbare ods ({e})")
        return None
    (MAP / f"giften_{uitgave}.sha256").write_text(h + "\n")
    (MAP / f"giften_{uitgave}.json").write_text(json.dumps(
        {"uitgave": uitgave, "reeks": d["reeks"], "versie": versie, "documenttitel": d["titel"],
         "titel": titel, "url": d["url"], "pagina": d["pagina"], "herkomst": d["herkomst"],
         "bestandsnaam": naam or None, "opgehaald": datetime.date.today().isoformat()},
        ensure_ascii=False, indent=1), encoding="utf-8")
    meld(f"  + {uitgave} ({d['herkomst']})")
    return pad


def haal(meld=print) -> list[Path]:
    """Elk overzicht dat nog niet (met deze sha256) bewaard is, wordt een nieuwe uitgave
    giften_<reeks>_<versie>.ods (+ .sha256 + .json). Geeft de nieuwe uitgaven terug."""
    MAP.mkdir(parents=True, exist_ok=True)
    bekend = _bekend()
    nieuw = []
    for d in kandidaten(meld):
        try:
            inhoud, schijf = _get(d["url"], timeout=120, binair=True)
        except urllib.error.HTTPError as e:
            meld(f"  ! {d['url']}: {e.code}")
            continue
        time.sleep(PAUZE)
        h = hashlib.sha256(inhoud).hexdigest()
        if h in bekend or not inhoud.startswith(b"PK"):
            continue
        naam = urllib.parse.unquote(re.sub(r'.*filename="?([^";]+)"?.*', r"\1", schijf)) if schijf else ""
        pad = _bewaar(inhoud, d, naam, meld)
        if pad:
            bekend.add(h)
            nieuw.append(pad)
    return nieuw


def voeg_toe(bestand: Path, url: str, titel: str | None = None, versie: str | None = None,
             meld=print) -> Path | None:
    """Een ods die een mens zelf downloadde (bijv. van open.overheid.nl, waar robots.txt dit
    script weert) opnemen als uitgave, met de vindplaats als url."""
    MAP.mkdir(parents=True, exist_ok=True)
    inhoud = bestand.read_bytes()
    if not inhoud.startswith(b"PK"):
        raise ValueError(f"{bestand} is geen ods")
    if hashlib.sha256(inhoud).hexdigest() in _bekend():
        meld(f"  = {bestand.name}: al bewaard")
        return None
    reeks = reeks_van(titel or "") or reeks_van(bestand.name)
    if not reeks:
        raise ValueError("reeks onbekend: geef --titel met de documenttitel van het overzicht")
    d = {"titel": titel or bestand.name, "versie": versie, "url": url, "pagina": url, "reeks": reeks,
         "herkomst": "handmatig"}
    return _bewaar(inhoud, d, bestand.name, meld)


# ── ods lezen (stdlib) ──────────────────────────────────────────────────────
_T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
_O = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
_X = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"


def _p(e) -> str:
    delen = [e.text or ""]
    for k in e:
        if k.tag == _X + "s":
            delen.append(" " * int(k.get(_X + "c", "1")))
        elif k.tag in (_X + "line-break", _X + "tab"):
            delen.append(" ")
        else:
            delen.append(_p(k))
        delen.append(k.tail or "")
    return "".join(delen)


def ods_rijen(pad: Path) -> list[list]:
    """Alle rijen van alle tabbladen; een cel is (tekst, waarde) met waarde een float, een
    ISO-datum of None."""
    with zipfile.ZipFile(pad) as z:
        root = ET.fromstring(z.read("content.xml"))
    rijen = []
    for t in root.iter(_T + "table"):
        for r in t.iter(_T + "table-row"):
            cellen = []
            for c in r:
                if c.tag not in (_T + "table-cell", _T + "covered-table-cell"):
                    continue
                n = min(int(c.get(_T + "number-columns-repeated", "1")), 64)
                vt = c.get(_O + "value-type")
                tekst = schoon(" ".join(_p(p) for p in c.findall(_X + "p")))
                waarde = None
                if vt in ("float", "currency", "percentage"):
                    try:
                        waarde = float(c.get(_O + "value"))
                    except (TypeError, ValueError):
                        waarde = None
                elif vt == "date":
                    waarde = (c.get(_O + "date-value") or "")[:10]
                cellen.extend([(tekst, waarde)] * n)
            while cellen and not cellen[-1][0] and cellen[-1][1] is None:
                cellen.pop()
            if cellen:
                rep = min(int(r.get(_T + "number-rows-repeated", "1")), 3)
                rijen.extend([cellen] * rep)
            else:
                rijen.append([])
    return rijen


def _ods_titel(pad: Path) -> str:
    for r in ods_rijen(pad):
        if r and r[0][0]:
            return r[0][0]
    raise FormaatFout("lege spreadsheet")


# ── records ─────────────────────────────────────────────────────────────────
def _bedrag(cel) -> float | None:
    tekst, waarde = cel
    if isinstance(waarde, float):
        return round(waarde, 2)
    t = tekst.replace("€", "").replace(" ", "")
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?|-?\d+(,\d+)?", t):
        return round(float(t.replace(".", "").replace(",", ".")), 2)
    if re.fullmatch(r"-?\d+\.\d+", t):
        return round(float(t), 2)
    return None


def _datum(cel) -> str | None:
    tekst, waarde = cel
    if isinstance(waarde, str) and re.match(r"^\d{4}-\d\d-\d\d$", waarde):
        return waarde
    t = tekst.lower()
    m = re.match(r"^(\d{4})-(\d\d)-(\d\d)", t)
    if m:
        return m.group(0)
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", t)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{1,2})\s+(" + "|".join(MAANDEN) + r")\s+(\d{4})$", t)
    if m:
        return f"{m.group(3)}-{MAANDEN[m.group(2)]:02d}-{int(m.group(1)):02d}"
    return None


def euro(x: float | None) -> str:
    if x is None:
        return "€ ?"
    s = f"{x:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return "€ " + (s[:-3] if s.endswith(",00") else s)


def schoon_gever(naam: str) -> str:
    """'M.J. Ligthart - p/a Van Gastel Notarissen' → 'M.J. Ligthart' (p/a is een postadres);
    komma's en spaties aan het eind weg."""
    naam = re.split(r"\s*-?\s*\bp/a\b", naam, flags=re.I)[0]
    return schoon(naam).strip(" ,;")


def partij_model(label: str) -> str | None:
    """Partijlabel uit een overzicht ('GL', '02. PvdA', 'Volt ', 'Partij van de Arbeid (P.v.d.A.)')
    → naam van de partijknoop in het model; None voor een partij zonder knoop."""
    kaal = re.sub(r"^\d+\.\s*", "", schoon(label))
    if sleutel(kaal) in EXTRA_PARTIJEN:
        return EXTRA_PARTIJEN[sleutel(kaal)]
    return partij_naam(kaal)


def _is_partijkop(tekst: str, labels: set[str]) -> bool:
    kaal = re.sub(r"^\d+\.\s*", "", tekst)
    if re.match(r"^\d+\.", tekst):
        return True
    s = sleutel(kaal)
    return bool(partij_model(kaal)) or s in labels or s in ANDERE_PARTIJEN or s in PARTIJEN


def _gever_soort(naam: str, adres: str, ubo: str) -> tuple[str, list[str]]:
    """→ ('persoon' | 'organisatie' | 'persoonlijke_vennootschap', UBO-achternamen). Een natuurlijk
    persoon heeft alleen een woonplaats (toelichting bij elk overzicht), een organisatie een adres
    met postcode of postbus, een rechtsvorm of een UBO. Twijfel = persoon (privacy)."""
    eerste = naam.split()[0] if naam.split() else ""
    initialen = bool(INITIAAL.match(eerste)) and len(naam.split()) >= 2 and (
        "." in eerste or len(eerste) == 1) and eerste.lower() not in AFKORTINGEN
    ubo_namen = [schoon(m.group(0)).strip(" ,") for m in UBO_NAAM.finditer(ubo or "")]
    if initialen and not POSTCODE.search(adres or ""):
        return "persoon", ubo_namen
    if not (POSTCODE.search(adres or "") or RECHTSVORM.search(naam) or (ubo or "").strip()):
        return "persoon", ubo_namen
    woorden = sleutel(naam).split()
    eigen = any(sleutel(a).split()[-1] in woorden for a in ubo_namen if sleutel(a) and len(sleutel(a).split()[-1]) >= 4)
    # voorletters in de naam ('C.P.G. van Oostrom Beheer', 'H.J. van Bentum … B.V.'), niet 'B.V.' zelf
    voorletters = re.search(r"(?:^|\s)(?!(?:B\.V\.|N\.V\.|U\.A\.|C\.V\.|V\.O\.F\.)(?:\s|$))(?:[A-Z]\.){2,}"
                            r"\s*(?:[a-z']+\s+)*[A-Z][a-z]", naam)
    if initialen or eigen or voorletters:
        return "persoonlijke_vennootschap", ubo_namen
    return "organisatie", ubo_namen


def _kop(rij: list) -> dict | None:
    """De kopregel van de tabel met giften: kolomindexen per veld."""
    teksten = [sleutel(t) for t, _ in rij]
    if not any(t.startswith(("naam gever", "naam donateur")) for t in teksten):
        return None
    k: dict = {"jaren": {}}
    for i, t in enumerate(teksten):
        if t == "politieke partij":
            k["partij"] = i
        elif t == "neveninstelling":
            k["nev"] = i
        elif t.startswith(("naam gever", "naam donateur")):
            k["gever"] = i
        elif t.startswith("adres"):
            k["adres"] = i
        elif t in ("ubo", "naam ubo"):
            k["ubo"] = i
        elif re.fullmatch(r"totaal 20\d\d", t):
            k["jaren"][t[-4:]] = i
        elif t in ("eindtotaal", "totaalbedrag", "totaal"):
            k.setdefault("totaal", i)
        elif t.startswith(("bedrag", "losse bedragen")):
            k["bedrag"] = i
        elif t.startswith("datum"):
            k["datum"] = i
        elif t.startswith(("toelichting", "bijzonderhe")):
            k["toel"] = i
    if "totaal" not in k and len(k["jaren"]) == 1:
        k["totaal"] = next(iter(k["jaren"].values()))
        k["jaren"] = {}
    return k


def _cel(rij: list, i: int | None):
    return rij[i] if i is not None and i < len(rij) else ("", None)


def lees(pad: Path) -> dict:
    uitgave = uitgave_van(pad)
    meta_pad = MAP / f"giften_{uitgave}.json"
    meta = json.loads(meta_pad.read_text(encoding="utf-8")) if meta_pad.exists() else {}
    reeks, versie = uitgave.split("_", 1)
    rijen = ods_rijen(pad)
    titel = next((r[0][0] for r in rijen if r and r[0][0]), "")
    if "gift" not in titel.lower():
        raise FormaatFout(f"{pad.name}: geen giftenoverzicht ('{titel[:80]}')")
    kopnr = next((i for i, r in enumerate(rijen) if _kop(r)), None)
    if kopnr is None:
        raise FormaatFout(f"{pad.name}: geen kopregel met 'Naam gever'/'Naam donateur'")
    kop = _kop(rijen[kopnr])
    labels = {sleutel(re.sub(r"^\d+\.\s*", "", r[0][0])) for r in rijen[:kopnr]
              if len(r) >= 2 and r[0][0] and (r[1][0].lower().startswith(("ja", "nee")) or _bedrag(r[-1]) is not None)}
    labels -= {"totaal", "eindtotaal", "politieke partij"}
    tabel = "partij" in kop
    sectie_heuristiek = not tabel and not kop["jaren"]   # 2019–2021: kolomkoppen kloppen niet altijd
    groepen: list[dict] = []
    partij, nev, huidig = None, "", None
    for rij in rijen[kopnr + 1:]:
        tekst = [t for t, _ in rij]
        if not any(tekst) and not any(w is not None for _, w in rij):
            continue
        if tabel:
            p = re.sub(r"^\d+\.\s*", "", _cel(rij, kop["partij"])[0]).strip()
            if not p:
                continue
            partij, nev = p, _cel(rij, kop.get("nev"))[0]
        else:
            gevuld = [t for t in tekst if t]
            if len(gevuld) == 1 and tekst[0] and all(w is None or isinstance(w, str) and not w for _, w in rij):
                kopje = tekst[0]
                if len(kopje.split()) > 7 or re.search(r"\bheeft\b|\bgeen\b.*\bgiften\b", kopje.lower()):
                    continue   # een mededeling ('De PVV heeft één anonieme gift ontvangen …')
                if _is_partijkop(kopje, labels):
                    partij, nev, huidig = re.sub(r"^\d+\.\s*", "", kopje).strip() or kopje, "", None
                elif partij and partij_model(re.sub(r"(?i)^vereniging\s+", "", kopje)) == partij_model(partij):
                    nev, huidig = "", None   # 'Vereniging VVD': de partij zelf
                elif partij:
                    nev, huidig = kopje, None
                continue
        if partij is None:
            continue
        gever = schoon_gever(_cel(rij, kop["gever"])[0])
        totaal_cel = None if sectie_heuristiek else _bedrag(_cel(rij, kop.get("totaal")))
        if sectie_heuristiek:
            is_totaal = any(t.lower().startswith("totaal") for t in tekst)
            getallen = [(i, _bedrag(c)) for i, c in enumerate(rij) if i > 1 and _bedrag(c) is not None]
            datums = [_datum(c) for i, c in enumerate(rij) if i > 1 and _datum(c)]
            bedrag = None if is_totaal else (getallen[0][1] if getallen else None)
            totaal_cel = getallen[-1][1] if is_totaal and getallen else None
            datum = datums[0] if datums else None
            toel = next((t for i, t in enumerate(tekst) if i > 1 and t and _bedrag(rij[i]) is None
                         and not _datum(rij[i]) and not t.lower().startswith("totaal")), "")
        else:
            bedrag = _bedrag(_cel(rij, kop.get("bedrag")))
            datum = _datum(_cel(rij, kop.get("datum")))
            toel = _cel(rij, kop.get("toel"))[0]
        nieuwe_groep = bool(gever) and (huidig is None or sleutel(gever) != sleutel(huidig["gever"])
                                        or (tabel and totaal_cel is not None and huidig["totaal"] is not None)
                                        or (huidig["partij"], huidig["nev"]) != (partij, nev))
        if nieuwe_groep:
            soort, ubo = _gever_soort(gever, _cel(rij, kop.get("adres"))[0], _cel(rij, kop.get("ubo"))[0])
            huidig = {"partij": partij, "nev": nev, "gever": gever, "soort": soort, "ubo": ubo,
                      "totaal": None, "jaren": {}, "bedragen": [], "toel": []}
            groepen.append(huidig)
        if huidig is None or (not gever and huidig["partij"] != partij):
            continue
        if totaal_cel is not None and huidig["totaal"] is None:
            huidig["totaal"] = totaal_cel
        for j, i in kop["jaren"].items():
            b = _bedrag(_cel(rij, i))
            if b:
                huidig["jaren"][j] = b
        if bedrag is not None and bedrag > 0:
            huidig["bedragen"].append([bedrag, datum])
        if toel and VEILIGE_TOELICHTING.search(toel) and not POSTCODE.search(toel) and toel not in huidig["toel"]:
            huidig["toel"].append(toel)
    # voor- en achternamen van de natuurlijke personen in dit overzicht: een holding die zo heet is privé
    voornamen, achternamen = namenlijsten(g["gever"] for g in groepen if g["soort"] == "persoon" and g["gever"])
    for g in groepen:
        if g["soort"] == "organisatie" and g["gever"] and _persoonlijk(g["gever"], voornamen, achternamen):
            g["soort"] = "persoonlijke_vennootschap"
    records: dict[str, dict] = {}
    ubo: dict[str, list[str]] = {}
    for g in groepen:
        if not g["gever"] or sleutel(g["gever"]) in ("anoniem", "anonieme gift"):
            continue
        s = "gift:" + hashlib.sha1(f"{reeks}|{sleutel(g['partij'])}|{sleutel(g['nev'])}|{sleutel(g['gever'])}"
                                   .encode()).hexdigest()[:16]
        if s in records:   # dezelfde gever twee keer onder dezelfde partij: samenvoegen
            r = records[s]
            r["totaal"] = round((r["totaal"] or 0) + (g["totaal"] or 0), 2) or None
            r["bedragen"] += g["bedragen"]
            for j, b in g["jaren"].items():
                r["per_jaar"][j] = round(r["per_jaar"].get(j, 0) + b, 2)
            r["toelichting"] = "; ".join(dict.fromkeys([t for t in (r["toelichting"] or "").split("; ") if t] + g["toel"]))
        else:
            records[s] = {"sleutel": s, "soort": "gift", "reeks": reeks, "partij_label": g["partij"],
                          "partij": partij_model(g["partij"]), "neveninstelling": g["nev"], "gever": g["gever"],
                          "gever_soort": g["soort"], "totaal": g["totaal"], "per_jaar": dict(g["jaren"]),
                          "bedragen": g["bedragen"], "toelichting": "; ".join(g["toel"])}
        if g["ubo"]:
            ubo.setdefault(s, []).extend(g["ubo"])
    for r in records.values():
        if r["totaal"] is None:
            r["totaal"] = round(sum(b for b, _ in r["bedragen"]), 2) or (round(sum(r["per_jaar"].values()), 2) or None)
        r["bedragen"] = sorted(r["bedragen"], key=lambda b: (b[1] or "", b[0]))
        datums = [d for _, d in r["bedragen"] if d]
        r["eerste"], r["laatste"] = (min(datums), max(datums)) if datums else (None, None)
        r["jaar"] = _jaar(reeks, r)
        r["regel"] = _regel(titel, versie, r)
    if not records:
        raise FormaatFout(f"{pad.name}: geen giften gelezen")
    return {"bron": BRON, "uitgave": uitgave, "reeks": reeks, "versie": versie, "sha256": sha256_bestand(pad),
            "bestand": str(pad), "url": meta.get("url") or URL, "pagina": meta.get("pagina") or URL,
            "titel": TITEL.format(titel=titel, uitgave=uitgave), "overzicht": titel,
            "drempel": _drempel(titel, reeks), "records": records, "_ubo": ubo}


def _jaar(reeks: str, r: dict) -> str | None:
    """Het kalenderjaar van de gift: uit de reeks (substantieel-/jaar-), anders het jaar van de
    laatste datum of het laatste jaar met een totaal."""
    m = re.match(r"^(?:substantieel|jaar)-(\d{4})$", reeks)
    if m:
        return m.group(1)
    if r["per_jaar"]:
        return max(j for j, b in r["per_jaar"].items() if b) if any(r["per_jaar"].values()) else None
    return r["laatste"][:4] if r["laatste"] else (re.search(r"(\d{4})", reeks).group(1) if re.search(r"(\d{4})", reeks) else None)


def _drempel(titel: str, reeks: str) -> str:
    m = re.search(r"€\s?([\d.]+)", titel)
    if m:
        return f"€ {m.group(1)}"
    return "€ 10.000" if reeks.startswith("substantieel") else "€ 1.000"


def _regel(titel: str, versie: str, r: dict) -> str:
    """De recordregel (het citaat): zonder adres, woonplaats of UBO."""
    ontvanger = r["partij_label"] + (f" (neveninstelling {r['neveninstelling']})" if r["neveninstelling"] else "")
    delen = [f"{titel} (versie {versie})", f"ontvanger: {ontvanger}", f"gever: {r['gever']}",
             f"totaal {euro(r['totaal'])}"]
    if r["per_jaar"]:
        delen.append("per jaar: " + "; ".join(f"{j} {euro(b)}" for j, b in sorted(r["per_jaar"].items()) if b))
    if r["bedragen"]:
        delen.append("bedragen: " + "; ".join(f"{euro(b)}" + (f" op {d}" if d else "") for b, d in r["bedragen"]))
    if r["toelichting"]:
        delen.append(r["toelichting"])
    return "Rijksoverheid, giften aan politieke partijen (Wfpp) · " + " · ".join(delen)


# ── uitgaven ────────────────────────────────────────────────────────────────
_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"giften_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


def nieuwste_per_reeks() -> dict[str, str]:
    """reeks → de nieuwste uitgave (versie) van dat overzicht."""
    uit: dict[str, str] = {}
    for p in uitgaven():
        u = uitgave_van(p)
        reeks = u.split("_", 1)[0]
        if reeks not in uit or u > uit[reeks]:
            uit[reeks] = u
    return uit


def schrijfwijzen() -> dict[str, str]:
    """Schrijfwijze van een gever in de overzichten → naam in het model, met de hand vastgelegd
    in koppelingen.json ('giften_namen'), net als 'tk_namen' bij de Kamerregisters."""
    pad = Path(__file__).resolve().parent / "koppelingen.json"
    if not pad.exists():
        return {}
    return {k: v for k, v in json.loads(pad.read_text(encoding="utf-8")).get("giften_namen", {}).items()
            if not k.startswith("_")}


def past_persoon(rec: dict, naam: str) -> bool:
    """Past een modelnaam bij de gever (natuurlijk persoon)? De achternaam als hele woorden en de
    eerste voorletter als eerste letter (zoals tk.past_naam)."""
    from common import ontleed_naam
    n = ontleed_naam(rec["gever"])
    achter = sleutel(f"{n['tussenvoegsel'] or ''} {n['achternaam'] or ''}")
    letter = sleutel(n["voorletters"] or n["voornamen"] or n["roepnaam"] or "")[:1]
    woorden = f" {sleutel(naam)} "
    delen = [d for d in achter.split("-") if d] if "-" in (n["achternaam"] or "") else [achter]
    return bool(achter) and any(f" {d.strip()} " in woorden for d in delen) and \
        bool(letter) and sleutel(naam)[:1] == letter


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """'donor' (of 'financiering') van de gever naar de partij uit het record: de partij via
    dezelfde partijtabel als de import, de gever onder zijn naam in het model (of een vastgelegde
    schrijfwijze) in het record, een natuurlijk persoon met achternaam en voorletter."""
    if relatie_type not in ("donor", "financiering"):
        return f"een giftfeit is 'donor' of 'financiering', niet '{relatie_type}'"
    verwacht = rec.get("partij")
    partij = [e for e in eindpunten if e["type"] == "partij" and verwacht and e["name"] == verwacht]
    if not partij:
        return f"geen eindpunt is de partij '{rec.get('partij_label')}' uit het record"
    ander = [e for e in eindpunten if e is not partij[0]][0]
    if rec["gever_soort"] == "persoon":
        if ander["type"] != "persoon" or not past_persoon(rec, ander["name"]):
            return f"'{ander['name']}' past niet bij de gever '{rec['gever']}'"
        return None
    if ander["type"] == "persoon":
        return f"de gever '{rec['gever']}' is geen natuurlijk persoon"
    from tk import schrijfwijzen as tk_namen
    alle = {**tk_namen(), **schrijfwijzen()}
    namen = [ander["name"]] + [v for v, m in alle.items() if sleutel(m) == sleutel(ander["name"])]
    if not any(zelfde_gever(rec["gever"], n) for n in namen):
        return f"'{ander['name']}' staat niet als gever in het record {sleutel_r}"
    return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Giften aan politieke partijen (Wfpp) ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees", "voeg-toe"])
    ap.add_argument("bestand", nargs="?", help="voeg-toe: de zelf gedownloade ods")
    ap.add_argument("--url", help="voeg-toe: de vindplaats van het overzicht")
    ap.add_argument("--titel", help="voeg-toe: de documenttitel (voor de reeks)")
    ap.add_argument("--versie", help="voeg-toe: JJJJ-MM-DD, als de bestandsnaam haar niet noemt")
    a = ap.parse_args()
    if a.actie == "haal":
        for p in haal():
            print(p)
    elif a.actie == "voeg-toe":
        if not (a.bestand and a.url):
            ap.error("voeg-toe vraagt een bestand en --url")
        print(voeg_toe(Path(a.bestand), a.url, a.titel, a.versie))
    else:
        for p in uitgaven():
            d = lees(p)
            tel = Counter(r["gever_soort"] for r in d["records"].values())
            print(json.dumps({"uitgave": d["uitgave"], "records": len(d["records"]), **tel,
                              "overzicht": d["overzicht"][:90]}, ensure_ascii=False))
