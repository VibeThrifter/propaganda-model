"""LittleSis (littlesis.org) — uitgave ophalen en lezen (onderzoek 2026-10-20).

LittleSis ("zusje van Big Brother", Public Accountability Initiative) is een open database van
wie-kent-wie bij machtige personen en organisaties: functies, lidmaatschappen, donaties,
eigendom, transacties. Geen officieel register maar een SECUNDAIRE bron: onderzoekers en
vrijwilligers voeren relaties in, meestal met een of meer bronlinks (jaarverslag, persbericht,
nieuwsartikel). Licentie CC BY-SA 4.0 (naamsvermelding LittleSis, gelijk delen). Het zwaartepunt
is de VS (twee derde van de 1,9 mln relaties zijn Amerikaanse campagnegiften); Nederland komt er
via multinationals, elite-fora en een handvol politici in voor.

Toegang (zie robots.txt: Crawl-delay 10, dus PAUZE = 10 s tussen verzoeken aan littlesis.org):
  - bulkdata (database/public_data/entities.json.gz en relationships.json.gz, CC BY-SA 4.0):
    alle entiteiten en relaties, zonder bronlinks; twee verzoeken;
  - API (api/entities/:id, api/relationships/:id, geen sleutel; 503 bij te veel verzoeken):
    dezelfde velden, ook zonder bronlinks;
  - de relatiepagina (relationships/:id, html) noemt de bronlinks ("Source Links"). LET OP: de
    gebruiksvoorwaarden (database/terms_of_use) verbieden "any robot, spider, or other automatic
    device … other than as specifically permitted by the documented functionality of the LittleSis
    API". robots.txt staat het toe (Crawl-delay 10), de voorwaarden niet. Daarom haalt haal() de
    bronlinks standaard NIET (--max-bronnen 0); alleen met toestemming van LittleSis (of een
    API-route voor references) een getal opgeven. De uitgave van 2026-10-20 bevat de bronlinks
    van 285 relaties (eenmalig onderzoek, 10 s per pagina).

De uitgave is één json-bestand: data/registers/littlesis/littlesis_<ophaaldatum>.json (+ .sha256)
met de sha256 van beide dumps, de entiteiten die erin voorkomen en per relatie een record
('relatie:<id>'). De recordregel is LittleSis' eigen omschrijving van de relatie, letterlijk
(witruimte samengevoegd), zoals de API en de relatiepagina hem geven. Familie- en sociale relaties
worden nooit bewaard (privé).

Selectie (wat in de uitgave komt): relaties met minstens één kant die in littlesis_koppelingen.json
staat (met de hand gekoppeld aan een knoop in het model), Nederlands is (blurb/samenvatting noemt
Nederland, website op .nl) of een elite-forum is (HUBS). Donaties alleen als één kant zo'n kant is
en niet alleen via een Amerikaanse naamgenoot.

Geen schrijfacties op het model (dat doet littlesis_naar_model.py via de REST-API).

    python3 tools/registers/littlesis.py haal [--dumps <map met de .json.gz>] [--max-bronnen 0]
    python3 tools/registers/littlesis.py lees
"""
from __future__ import annotations

import datetime
import gzip
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
from common import DATA, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "littlesis"
BASIS = "https://littlesis.org"
URL = "https://littlesis.org/database/bulk_data"
DUMPS = {"entities": f"{BASIS}/database/public_data/entities.json.gz",
         "relationships": f"{BASIS}/database/public_data/relationships.json.gz"}
MAP = DATA / BRON
RUW = MAP / "ruw"
KOPPELINGEN = HIER / "littlesis_koppelingen.json"
UITGEVER = "LittleSis (Public Accountability Initiative), CC BY-SA 4.0"
LICENTIE = "CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)"
TITEL = "LittleSis, bulkdata (entiteiten en relaties) met bronlinks per relatie, opgehaald {uitgave}"
UA = "propagandamodel-registers (onderzoek; 1 verzoek per 10 s)"
PAUZE = 10.0   # robots.txt van littlesis.org: Crawl-delay: 10

CATEGORIE = {1: "positie", 2: "opleiding", 3: "lidmaatschap", 4: "familie", 5: "donatie", 6: "transactie",
             7: "lobby", 8: "sociaal", 9: "professioneel", 10: "eigendom", 11: "hiërarchie", 12: "generiek"}
NOOIT = {4, 8}   # familie en sociaal: privé, nooit bewaren
# Elite-fora en hun LittleSis-id's (een relatie ermee is altijd interessant)
HUBS = {36952: "Bilderberg Group", 43853: "American Friends of Bilderberg", 33496: "Trilateral Commission",
        223013: "Trilateral Commission - Italian Group", 41410: "World Economic Forum",
        37583: "World Economic Forum Foundation", 40361: "WEF International Business Council",
        179057: "World Economic Forum USA", 151148: "European Round Table of Industrialists",
        401931: "European Round Table for Industrialists", 33359: "Atlantic Council",
        426104: "Munich Security Conference", 110602: "Chatham House", 34966: "German Marshall Fund",
        348694: "European Council on Foreign Relations"}
_NL_TEKST = re.compile(r"\b(dutch|netherlands|nederland\w*|amsterdam|rotterdam|the hague|den haag|utrecht|eindhoven|"
                       r"leiden|groningen|nijmegen|tilburg|wageningen|delft|maastricht)\b", re.I)
_NL_VORM = re.compile(r"\b(N\.V\.|B\.V\.|Koninklijke|Stichting|Coöperatie(ve)?)\b")


class FormaatFout(Exception):
    """De dump, de pagina of de uitgave heeft niet het verwachte formaat."""


# ── lezen van de dumps ──────────────────────────────────────────────────────
_WS = re.compile(r"[\s,]*")


def stroom(pad: Path, blok: int = 1 << 22):
    """Elementen van een grote JSON-array (gzip) één voor één; de relatiedump is ± 1,3 GB."""
    dec = json.JSONDecoder()
    with gzip.open(pad, "rt", encoding="utf-8") as f:
        buf = f.read(blok)
        i = _WS.match(buf, 0).end()
        if buf[i:i + 1] != "[":
            raise FormaatFout(f"{pad.name} is geen JSON-array")
        i += 1
        eof = False
        while True:
            i = _WS.match(buf, i).end()
            if i >= len(buf) - 1 and not eof:
                meer = f.read(blok)
                eof = not meer
                buf, i = buf[i:] + meer, 0
                continue
            if buf[i:i + 1] == "]":
                return
            try:
                obj, j = dec.raw_decode(buf, i)
            except json.JSONDecodeError:
                if eof:
                    raise FormaatFout(f"{pad.name}: kapotte JSON bij positie {i}")
                meer = f.read(blok)
                eof = not meer
                buf, i = buf[i:] + meer, 0
                continue
            yield obj
            i = j


def nl_bewijs(e: dict) -> list[str]:
    """Waarom een LittleSis-entiteit Nederlands lijkt: 'tekst' (blurb/samenvatting/naam noemt
    Nederland), 'website.nl', 'rechtsvorm' (N.V., B.V., Koninklijke, Stichting). Alleen een
    aanwijzing voor de selectie, nooit een koppeling."""
    uit = []
    tekst = " ".join(filter(None, [e.get("name"), e.get("blurb"), (e.get("summary") or "")[:600]]))
    if _NL_TEKST.search(tekst):
        uit.append("tekst")
    w = (e.get("website") or "").lower().split("?")[0]
    if re.search(r"\.nl(/|$)", w):
        uit.append("website.nl")
    if _NL_VORM.search(e.get("name") or ""):
        uit.append("rechtsvorm")
    return uit


def koppelingen() -> dict[int, dict]:
    if not KOPPELINGEN.exists():
        return {}
    d = json.loads(KOPPELINGEN.read_text(encoding="utf-8"))
    return {int(k): v for k, v in d.get("koppelingen", {}).items()}


def regel_van(a: dict) -> str:
    """De recordregel: LittleSis' eigen zin, letterlijk (witruimte samengevoegd)."""
    return schoon(a.get("description") or "")


# ── ophalen ─────────────────────────────────────────────────────────────────
def _get(url: str, timeout: int = 60) -> bytes:
    for poging in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 410) or poging == 3:
                raise
            time.sleep(60 * (poging + 1) if e.code in (429, 503) else 15)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if poging == 3:
                raise
            time.sleep(30)
    raise FormaatFout(f"niet op te halen: {url}")


def _download(url: str, doel: Path) -> Path:
    doel.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tijdelijk = doel.with_suffix(doel.suffix + ".tmp")
    with urllib.request.urlopen(req, timeout=600) as r, open(tijdelijk, "wb") as f:
        while True:
            blok = r.read(1 << 20)
            if not blok:
                break
            f.write(blok)
    tijdelijk.replace(doel)
    return doel


def haal_dumps(meld=print) -> Path:
    """Beide dumps naar data/registers/littlesis/ruw/ (± 190 MB, niet de uitgave zelf)."""
    for i, (naam, url) in enumerate(DUMPS.items()):
        if i:
            time.sleep(PAUZE)
        meld(f"  littlesis: {url}")
        _download(url, RUW / f"{naam}.json.gz")
    return RUW


_BRONTABEL = re.compile(r'<table[^>]*id="source-links-table"[^>]*>(.*?)</table>', re.S)


def lees_bronlinks(pagina: str) -> list[dict]:
    """De bronlinks van een relatiepagina: [{'url', 'titel'}]. Geen tabel = geen bron."""
    m = _BRONTABEL.search(pagina)
    if not m:
        return []
    uit = []
    for href, tekst in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', m.group(1), re.S):
        url = html.unescape(href).strip()
        if url.startswith("http"):
            uit.append({"url": url, "titel": schoon(html.unescape(re.sub(r"<[^>]+>", " ", tekst)))})
    return uit


def bronlinks(rel_ids: list[int], cache: dict, max_n: int, meld=print) -> dict:
    """Bronlinks voor relaties die nog niet in de cache staan, hooguit max_n per keer, 10 s ertussen."""
    open_ = [r for r in rel_ids if str(r) not in cache][:max_n]
    meld(f"  littlesis: bronlinks voor {len(open_)} relaties (≈ {len(open_) * PAUZE / 60:.0f} min)")
    pad = MAP / "bronlinks_cache.json"
    for n, rid in enumerate(open_, 1):
        try:
            pagina = _get(f"{BASIS}/relationships/{rid}").decode("utf-8", "replace")
            cache[str(rid)] = {"links": lees_bronlinks(pagina), "gelezen": datetime.date.today().isoformat()}
        except urllib.error.HTTPError as e:
            cache[str(rid)] = {"links": [], "fout": e.code, "gelezen": datetime.date.today().isoformat()}
        if n % 25 == 0 or n == len(open_):
            pad.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            meld(f"    {n}/{len(open_)}")
        time.sleep(PAUZE)
    return cache


def selecteer(dumps: Path, meld=print) -> tuple[dict, dict]:
    """(entiteiten, relaties) uit de dumps: zie de selectieregel bovenaan."""
    gekoppeld = set(koppelingen())
    ent_alle: dict[int, dict] = {}
    nl: dict[int, list[str]] = {}
    for o in stroom(dumps / "entities.json.gz"):
        a = o["attributes"]
        e = {k: a.get(k) for k in ("name", "blurb", "website", "primary_ext", "qid", "aliases", "types",
                                    "start_date", "end_date", "parent_id")}
        e["summary"] = (a.get("summary") or "")[:600]
        e["link"] = (o.get("links") or {}).get("self")
        ent_alle[a["id"]] = e
        b = nl_bewijs(e)
        if b:
            nl[a["id"]] = b
    meld(f"  littlesis: {len(ent_alle)} entiteiten, {len(nl)} met een Nederlandse aanwijzing")
    sterk = {i for i, b in nl.items() if set(b) & {"tekst", "website.nl"}}
    kern = gekoppeld | set(HUBS) | sterk
    zwak = {i for i, b in nl.items() if b == ["rechtsvorm"]}
    rels, tel = {}, Counter()
    for o in stroom(dumps / "relationships.json.gz"):
        a = o["attributes"]
        tel["relaties"] += 1
        e1, e2, cat = a["entity1_id"], a["entity2_id"], a["category_id"]
        if cat in NOOIT:
            continue
        hier = {e1, e2} & kern
        if not hier and not ({e1, e2} & zwak and cat != 5):
            continue
        if cat == 5 and not ({e1, e2} & (gekoppeld | set(HUBS))) and not (e1 in sterk and e2 in sterk):
            # Amerikaanse campagnegiften van naamgenoten ('Dutch' Ruppersberger, Holland MI): ruis
            tel["donatie zonder gekoppelde kant overgeslagen"] += 1
            continue
        rels[a["id"]] = {**{k: a.get(k) for k in ("entity1_id", "entity2_id", "category_id", "description1",
                                                   "description2", "amount", "currency", "goods", "start_date",
                                                   "end_date", "is_current", "updated_at", "description",
                                                   "category_attributes")},
                         "link": o.get("self") or f"{BASIS}/relationships/{a['id']}"}
        tel[CATEGORIE[cat]] += 1
    nodig = {r["entity1_id"] for r in rels.values()} | {r["entity2_id"] for r in rels.values()}
    ent = {i: {**ent_alle[i], "nl": nl.get(i, [])} for i in nodig if i in ent_alle}
    meld(f"  littlesis: {tel['relaties']} relaties in de dump, {len(rels)} geselecteerd "
         f"({', '.join(f'{k} {v}' for k, v in tel.most_common() if k != 'relaties')})")
    return ent, rels


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("littlesis_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"littlesis_{uitgave}.json"


def haal(dumps: Path | None = None, max_bronnen: int = 0, meld=print) -> Path:
    """Dumps ophalen (of een map met dumps gebruiken), selecteren, bronlinks lezen voor de relaties
    die het model zou gebruiken (littlesis_naar_model.kandidaten), en de uitgave schrijven."""
    if dumps is None:
        dumps = haal_dumps(meld)
    ent, rels = selecteer(dumps, meld)
    cache_pad = MAP / "bronlinks_cache.json"
    MAP.mkdir(parents=True, exist_ok=True)
    cache = json.loads(cache_pad.read_text(encoding="utf-8")) if cache_pad.exists() else {}
    import littlesis_naar_model as lnm   # de keuze welke relaties een bron nodig hebben
    kand = lnm.kandidaat_ids(ent, rels)
    if max_bronnen:
        time.sleep(PAUZE)
        cache = bronlinks(kand, cache, max_bronnen, meld)
    records = {}
    for rid, r in rels.items():
        c = cache.get(str(rid))
        rec = {**r, "sleutel": f"relatie:{rid}", "id": rid, "categorie": CATEGORIE[r["category_id"]],
               "regel": regel_van(r), "bronlinks": c["links"] if c else None}
        if rec["regel"]:
            records[rec["sleutel"]] = rec
    uitgave = datetime.date.today().isoformat()
    pad = pad_van(uitgave)
    pad.write_text(json.dumps({
        "bron": BRON, "uitgave": uitgave, "licentie": LICENTIE,
        "dumps": {n: {"url": u, "sha256": sha256_bestand(dumps / f"{n}.json.gz"),
                      "bytes": (dumps / f"{n}.json.gz").stat().st_size} for n, u in DUMPS.items()},
        "entiteiten": {str(k): v for k, v in sorted(ent.items())}, "records": records},
        ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    (MAP / f"littlesis_{uitgave}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


# ── lezen (ook voor een controle à la registercheck) ───────────────────────
def lees(pad: Path) -> dict:
    data = json.loads(pad.read_text(encoding="utf-8"))
    if data.get("bron") != BRON or not isinstance(data.get("records"), dict):
        raise FormaatFout(f"{pad.name} is geen LittleSis-uitgave")
    data["entiteiten"] = {int(k): v for k, v in data["entiteiten"].items()}
    return {**data, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "titel": TITEL.format(uitgave=data["uitgave"])}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"littlesis_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


# Welke relatietypes in het model bij welke LittleSis-categorie passen (ook voor een extra bron)
PASSEND = {1: {"bestuurder", "personeel", "adviseur", "lidmaatschap", "dienstverband", "draaideur"},
           3: {"lidmaatschap", "bestuurder", "alliantie"},
           5: {"financiering", "donor"},
           6: {"financiering", "investering", "eigendom"},
           10: {"eigendom", "investering"},
           11: {"eigendom", "zeggenschap"}}


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """Beide eindpunten zijn de knopen waaraan littlesis_koppelingen.json de twee LittleSis-
    entiteiten van het record koppelt (op id, niet op naam), en het relatietype past bij de
    categorie. Eindpunten: [{'id', 'name', 'ids'}] zoals scripts/registercheck.py ze geeft."""
    k = koppelingen()
    doelen = set()
    for kant in ("entity1_id", "entity2_id"):
        m = k.get(rec[kant])
        if not m:
            return f"LittleSis-entiteit {rec[kant]} is niet gekoppeld (littlesis_koppelingen.json)"
        doelen.add(m["model"])
    if {e.get("id") for e in eindpunten} != doelen:
        return f"de eindpunten zijn niet de gekoppelde knopen {sorted(doelen)} van {sleutel_r}"
    if relatie_type not in PASSEND.get(rec["category_id"], set()):
        return f"'{relatie_type}' past niet bij de LittleSis-categorie '{rec['categorie']}'"
    return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="LittleSis-bulkdata ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--dumps", type=Path, help="map met entities.json.gz en relationships.json.gz (niet opnieuw downloaden)")
    ap.add_argument("--max-bronnen", type=int, default=0,
                    help="hooguit zoveel relatiepagina's (10 s per stuk); 0 = geen (gebruiksvoorwaarden, zie boven)")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal(a.dumps, a.max_bronnen))
    else:
        d = lees(uitgaven()[-1])
        tel = Counter(r["categorie"] for r in d["records"].values())
        print(json.dumps({"uitgave": d["uitgave"], "entiteiten": len(d["entiteiten"]),
                          "records": len(d["records"]), "per_categorie": dict(tel.most_common()),
                          "met_bronlinks": sum(1 for r in d["records"].values() if r.get("bronlinks"))},
                         ensure_ascii=False, indent=1))
