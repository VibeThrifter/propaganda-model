"""Openbare agenda's van bewindspersonen — uitgave ophalen en lezen (eigenaar 2026-10-19).

Rijksoverheid.nl publiceert per bewindspersoon per week de agenda (/actueel/agenda/<j>/<m>/<d>/
agenda-<functie>-<naam>-week-<n>): gesprekken, ontvangsten, werkbezoeken. Wie een bewindspersoon
herhaaldelijk spreekt, is een lobbycontact met diens ministerie (mechanisme
`departementale_lobby`). Dit is de registerkant: afspraken bewaren en lezen, zonder AI.

Twee herkomsten, één formaat (data/registers/agenda/agenda_<datum>.json + .sha256):
  - openlobby: de eenmalige achterstand (aug. 2023 – juni 2026) uit Open Lobby van de Open State
    Foundation (openlobby.nl, de gestructureerde paginadata), die dezelfde agenda's verzamelt; de
    uitgave heet naar de nieuwste afspraak erin;
  - rijksoverheid: elke volgende uitgave bevat alleen de afspraken die er nog niet waren, gelezen
    van de weekpagina's die de sitemap van rijksoverheid.nl noemt.
Een record is één afspraak; de recordsleutel hangt alleen af van datum, bewindspersoon en tekst,
dus dezelfde afspraak uit beide herkomsten is hetzelfde record. De recordregel is het citaat.

Geen schrijfacties op het model (dat doet agenda_naar_model.py via de REST-API).

    python3 tools/registers/agenda.py haal [--max-paginas 400]
    python3 tools/registers/agenda.py lees
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
import urllib.request
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, UA, noemt, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "agenda"
URL = "https://www.rijksoverheid.nl/actueel/agenda"
MAP = DATA / BRON
UITGEVER = "Rijksoverheid"
TITEL = "Rijksoverheid, openbare agenda's van bewindspersonen ({herkomst}), uitgave {uitgave}"
HERKOMST = {"openlobby": "verzameld door Open Lobby, Open State Foundation",
            "rijksoverheid": "weekpagina's op rijksoverheid.nl"}
OPENLOBBY = "https://openlobby.nl/analytics/__data.json?keyword=&date_from=2023-01-01&date_to={tot}&page={p}"
SITEMAP = "https://www.rijksoverheid.nl/sitemap.xml"
MAX_PAGINAS = 1000   # Open Lobby: hooguit 10.000 treffers per zoekvraag
PAUZE = 1.5   # seconden tussen verzoeken (beide sites zijn klein en publiek)

# Ministerie (zoals de agenda's het noemen, zonder "Ministerie van") → id in het register van
# overheidsorganisaties; het model koppelt via die externe id, nooit op naam.
MINISTERIES = {
    "Algemene Zaken": "123", "Buitenlandse Zaken": "2515", "Defensie": "4958",
    "Volksgezondheid, Welzijn en Sport": "8591", "Binnenlandse Zaken en Koninkrijksrelaties": "9632",
    "Economische Zaken en Klimaat": "10621", "Economische Zaken": "10621",
    "Justitie en Veiligheid": "11906", "Sociale Zaken en Werkgelegenheid": "19087",
    "Financiën": "68820", "Onderwijs, Cultuur en Wetenschap": "71852",
    "Infrastructuur en Waterstaat": "112773",
    "Landbouw, Visserij, Voedselzekerheid en Natuur": "22387697",
    "Landbouw, Natuur en Voedselkwaliteit": "22387697",
    "Asiel en Migratie": "29481986", "Volkshuisvesting en Ruimtelijke Ordening": "29481991",
    "Klimaat en Groene Groei": "29481996",
}
FUNCTIES = ("viceminister-president", "minister-president", "staatssecretaris", "minister")
MAANDEN = {m: i for i, m in enumerate(("januari", "februari", "maart", "april", "mei", "juni", "juli",
                                       "augustus", "september", "oktober", "november", "december"), 1)}


class FormaatFout(Exception):
    """De uitgave of de pagina heeft niet het verwachte formaat."""


def _get(url: str, timeout: int = 60) -> str:
    for poging in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            if poging == 3:
                raise
            time.sleep(30 * (poging + 1) if e.code == 429 else 5)
        except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError):
            if poging == 3:
                raise
            time.sleep(10)
    raise FormaatFout(f"niet op te halen: {url}")


def normaliseer_url(url: str) -> str:
    """Rijksoverheid.nl verhuisde de agenda van /regering/agenda/ naar /actueel/agenda/."""
    return (url or "").replace("/regering/agenda/", "/actueel/agenda/").split("#")[0]


def ministeries_uit(tekst: str | None) -> list[str]:
    """'Ministerie van Buitenlandse ZakenMinisterie van Asiel en Migratie' → beide namen."""
    return [d.strip() for d in re.split(r"Ministerie van ", tekst or "") if d.strip()]


def maak_record(datum: str, naam: str, functie: str, ministeries: list[str], soort: str,
                tekst: str, url: str) -> dict:
    tekst = schoon(tekst)
    s = "afspraak:" + hashlib.sha1(f"{datum}|{sleutel(naam)}|{sleutel(tekst)}".encode()).hexdigest()[:16]
    regel = (f"Openbare agenda {functie} {naam} ({'; '.join('Ministerie van ' + m for m in ministeries) or '?'}), "
             f"{datum}: {tekst}")
    return {"sleutel": s, "soort": "afspraak", "datum": datum, "bewindspersoon": naam, "functie": functie,
            "ministeries": ministeries, "type": soort, "tekst": tekst, "url": normaliseer_url(url),
            "regel": regel}


# ── uitgaven ────────────────────────────────────────────────────────────────
def uitgaven() -> list[Path]:
    return sorted(MAP.glob("agenda_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"agenda_{uitgave}.json"


def _schrijf(records: dict, herkomst: str, uitgave: str) -> Path:
    MAP.mkdir(parents=True, exist_ok=True)
    pad = pad_van(uitgave)
    pad.write_text(json.dumps({"bron": BRON, "uitgave": uitgave, "herkomst": herkomst,
                               "opgehaald": datetime.date.today().isoformat(), "records": records},
                              ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    (MAP / f"agenda_{uitgave}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def bekend() -> tuple[set[str], set[str]]:
    """(recordsleutels, weekpagina's) uit alle bewaarde uitgaven."""
    sleutels, urls = set(), set()
    for p in uitgaven():
        for s, r in lees(p)["records"].items():
            sleutels.add(s)
            urls.add(r["url"])
    return sleutels, urls


# ── herkomst 1: Open Lobby (eenmalige achterstand) ──────────────────────────
def _devalue(node: dict):
    """SvelteKit-paginadata (devalue): een platte lijst met verwijzingen naar indexen."""
    d, memo = node["data"], {}

    def h(i):
        if not isinstance(i, int) or i < 0:
            return None
        if i in memo:
            return memo[i]
        v = d[i]
        r = [h(x) for x in v] if isinstance(v, list) else (
            {k: h(x) for k, x in v.items()} if isinstance(v, dict) else v)
        memo[i] = r
        return r
    return h(0)


def haal_openlobby(meld=print) -> Path:
    """Alle pagina's van Open Lobby (10 afspraken per pagina, nieuwste eerst); hervat na een
    onderbreking via het ruwe bestand. De zoekindex geeft hooguit 10.000 treffers per zoekvraag
    (pagina 1000), dus per venster: is dat vol, dan het volgende venster tot de oudste datum
    die binnen is (de grensdag komt dubbel binnen; de recordsleutel ontdubbelt). Alleen nodig
    zolang er nog geen uitgave is."""
    MAP.mkdir(parents=True, exist_ok=True)
    ruw = MAP / "openlobby_ruw.jsonl"
    gezien: dict[str, set[int]] = defaultdict(set)
    oudste: dict[str, str] = {}
    vandaag = datetime.date.today().isoformat()
    if ruw.exists():
        for regel in ruw.read_text(encoding="utf-8").splitlines():
            r = json.loads(regel)
            v = r.get("venster", "2026-10-19")
            gezien[v].add(r["pagina"])
            for a in r["afspraken"]:
                oudste[v] = min(oudste.get(v, a["start"][:10]), a["start"][:10])
    tot = min(gezien) if gezien else vandaag
    with ruw.open("a", encoding="utf-8") as f:
        while True:
            def pagina(p):
                return _devalue(json.loads(_get(OPENLOBBY.format(tot=tot, p=p)))["nodes"][1])
            eerste = pagina(1)
            totaal = eerste["pagination"]["totalPages"]
            for p in range(1, min(totaal, MAX_PAGINAS) + 1):
                if p in gezien[tot]:
                    continue
                data = eerste if p == 1 else pagina(p)
                afspraken = [a["_source"] for a in data["appointments"]]
                f.write(json.dumps({"venster": tot, "pagina": p, "afspraken": afspraken}, ensure_ascii=False) + "\n")
                f.flush()
                gezien[tot].add(p)
                for a in afspraken:
                    oudste[tot] = min(oudste.get(tot, a["start"][:10]), a["start"][:10])
                if p % 100 == 0:
                    meld(f"  openlobby: venster tot {tot}, pagina {p}/{totaal}")
                time.sleep(PAUZE)
            if totaal <= MAX_PAGINAS or oudste.get(tot, tot) >= tot:
                break
            tot = oudste[tot]
    records = {}
    for regel in ruw.read_text(encoding="utf-8").splitlines():
        for a in json.loads(regel)["afspraken"]:
            functie = (a.get("minister_title") or "").strip()
            naam = a.get("minister_full_name") or a.get("minister_surname") or ""   # Rutte IV: alleen de achternaam
            rec = maak_record(a["start"][:10], naam, functie,
                              ministeries_uit(a.get("minister_ministry")), a.get("type") or "",
                              a.get("raw_text") or "", a.get("url") or "")
            records[rec["sleutel"]] = rec
    if not records:
        raise FormaatFout("Open Lobby gaf geen afspraken")
    return _schrijf(records, "openlobby", max(r["datum"] for r in records.values()))


# ── herkomst 2: weekpagina's op rijksoverheid.nl ───────────────────────────
class _Week(HTMLParser):
    """Per datumkop (h2 in een rich-text-blok) de bovenste lijstitems, met geneste lijsten erin."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.naam_spans, self._meta, self._span = [], 0, False
        self.kop, self._in_h2, self.items = None, False, []
        self._diepte, self._li, self._strong, self._soort = 0, None, False, ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "meta-data" in (a.get("class") or "").split():
            self._meta = 1
        elif self._meta and tag == "div":
            self._meta += 1
        elif self._meta and tag == "span":
            self._span = True
            self.naam_spans.append("")
        if tag == "h2":
            self._in_h2, self.kop = True, ""
        elif tag == "ul":
            self._diepte += 1
        elif tag == "li" and self._diepte == 1:
            self._li, self._soort = [], ""
        elif tag == "strong" and self._li is not None and not self._li:
            self._strong = True
        elif tag == "br" and self._li is not None:
            self._li.append(" ")

    def handle_endtag(self, tag):
        if self._meta and tag == "div":
            self._meta -= 1
        elif tag == "span":
            self._span = False
        if tag == "h2":
            self._in_h2 = False
        elif tag == "ul":
            self._diepte = max(0, self._diepte - 1)
        elif tag == "li" and self._diepte == 1 and self._li is not None:
            self.items.append((self.kop, self._soort, "".join(self._li)))
            self._li = None
        elif tag == "li" and self._li is not None:
            self._li.append(", ")
        elif tag == "strong":
            self._strong = False

    def handle_data(self, data):
        if self._span and self.naam_spans:
            self.naam_spans[-1] += data
        if self._in_h2:
            self.kop += data
        if self._li is not None:
            if self._strong:
                self._soort += data
            self._li.append(data)


def _datum(kop: str, jaar: int, maand_url: int) -> str | None:
    """'12 oktober', '15-16 oktober', '30 september - 2 oktober' → de eerste dag."""
    m = re.search(r"(\d{1,2})\s*(?:-\s*\d{1,2}\s*)?([a-z]+)?", kop.lower())
    if not m:
        return None
    maand = MAANDEN.get(m.group(2) or "")
    if maand is None:
        maand = next((MAANDEN[w] for w in re.findall(r"[a-z]+", kop.lower()) if w in MAANDEN), None)
    if maand is None:
        return None
    if maand < maand_url - 6:      # week rond de jaarwisseling
        jaar += 1
    try:
        return datetime.date(jaar, maand, int(m.group(1))).isoformat()
    except ValueError:
        return None


def _functie(url: str) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1].removeprefix("agenda-")
    return next((f for f in FUNCTIES if slug.startswith(f + "-")), "")


def ministerie_van_persoon(naam: str, functie: str, cache: dict) -> list[str]:
    """Het ministerie van een bewindspersoon: wat de agenda's eerder gaven, anders de pagina
    /regering/bewindspersonen/<naam> (het vaakst genoemde ministerie; Algemene Zaken alleen voor
    de minister-president, want de paginarand noemt het overal)."""
    if naam in cache:
        return cache[naam]
    slug = re.sub(r"[^a-z0-9]+", "-", sleutel(naam)).strip("-")
    try:
        pagina = _get(f"https://www.rijksoverheid.nl/regering/bewindspersonen/{slug}")
    except urllib.error.HTTPError:
        cache[naam] = []
        return []
    tel = Counter(m for m in re.findall(r"Ministerie van ([A-Z][^<\"\\]{3,70})", pagina) if m in MINISTERIES)
    if functie != "minister-president":
        tel.pop("Algemene Zaken", None)
    cache[naam] = [tel.most_common(1)[0][0]] if tel else (["Algemene Zaken"] if functie == "minister-president" else [])
    time.sleep(PAUZE)
    return cache[naam]


def lees_weekpagina(url: str, pagina: str, ministerie_cache: dict) -> list[dict]:
    p = _Week()
    p.feed(pagina)
    m = re.search(r"/agenda/(\d{4})/(\d{2})/\d{2}/", url)
    if not m:
        raise FormaatFout(f"geen datum in {url}")
    namen = [schoon(s) for s in p.naam_spans if schoon(s) and schoon(s) != "Agenda"]
    if not namen:
        raise FormaatFout(f"geen bewindspersoon op {url}")
    naam, functie = namen[0], _functie(url)
    ministeries = ministerie_van_persoon(naam, functie, ministerie_cache)
    uit = []
    for kop, soort, tekst in p.items:
        datum = _datum(kop or "", int(m.group(1)), int(m.group(2)))
        tekst = schoon(html.unescape(re.sub(r"\s*,\s*,", ",", tekst)))
        if datum and tekst:
            uit.append(maak_record(datum, naam, functie, ministeries, schoon(soort).rstrip(":").strip(),
                                   tekst, url))
    return uit


def weekpaginas() -> list[str]:
    index = _get(SITEMAP)
    uit = []
    for deel in re.findall(r"<loc>([^<]+)</loc>", index):
        if "/sitemap/" not in deel:
            continue
        uit += [u for u in re.findall(r"<loc>([^<]*/actueel/agenda/\d{4}/[^<]*-week-\d+)</loc>", _get(deel))
                if re.search(r"/agenda-(" + "|".join(FUNCTIES) + r")-", u)]
        time.sleep(0.3)
    return sorted(set(uit))


def haal_rijksoverheid(max_paginas: int = 400, meld=print) -> Path | None:
    sleutels, urls = bekend()
    cache = {}
    for p in uitgaven():   # het ministerie dat eerdere uitgaven per bewindspersoon gaven (het nieuwste)
        for r in sorted(lees(p)["records"].values(), key=lambda r: r["datum"]):
            if r["ministeries"]:
                cache[r["bewindspersoon"]] = r["ministeries"]
    nieuw = [u for u in weekpaginas() if u not in urls]
    meld(f"  rijksoverheid: {len(nieuw)} weekpagina's nog niet gelezen (max {max_paginas} per keer)")
    records = {}
    for u in sorted(nieuw, reverse=True)[:max_paginas]:
        try:
            for rec in lees_weekpagina(u, _get(u), cache):
                if rec["sleutel"] not in sleutels:
                    records[rec["sleutel"]] = rec
        except (urllib.error.URLError, http.client.HTTPException, OSError, FormaatFout) as e:
            meld(f"  ! {u}: {e}")
        time.sleep(PAUZE)
    if not records:
        return None
    return _schrijf(records, "rijksoverheid", datetime.date.today().isoformat())


def haal(max_paginas: int = 400, meld=print) -> Path:
    """Geen uitgave → eerst de achterstand uit Open Lobby; dan de nieuwe weekpagina's."""
    if not uitgaven():
        meld(f"agenda: achterstand uit Open Lobby → {haal_openlobby(meld).name}")
    vandaag = pad_van(datetime.date.today().isoformat())
    if vandaag.exists():
        return vandaag
    return haal_rijksoverheid(max_paginas, meld) or uitgaven()[-1]


# ── lezen (ook voor de registercheck) ──────────────────────────────────────
def lees(pad: Path) -> dict:
    data = json.loads(pad.read_text(encoding="utf-8"))
    if data.get("bron") != BRON or not isinstance(data.get("records"), dict):
        raise FormaatFout(f"{pad.name} is geen agenda-uitgave")
    herkomst = data.get("herkomst", "rijksoverheid")
    return {**data, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "titel": TITEL.format(herkomst=HERKOMST.get(herkomst, herkomst), uitgave=data["uitgave"])}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"agenda_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """'lobbyt' naar het ministerie van de bewindspersoon (oo-id), en de andere kant staat in
    de afspraak."""
    oo_ids = {MINISTERIES[m] for m in rec.get("ministeries") or [] if m in MINISTERIES}
    ministerie = [e for e in eindpunten if any(("oo", i) in e["ids"] for i in oo_ids)]
    if relatie_type != "lobbyt" or not ministerie:
        return "een agendafeit is 'lobbyt' met het ministerie van de bewindspersoon als doel"
    ander = [e for e in eindpunten if e is not ministerie[0]][0]
    if not noemt(rec["tekst"], ander["name"]):
        return f"'{ander['name']}' staat niet in de afspraak {sleutel_r}"
    return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Openbare agenda's van bewindspersonen ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--max-paginas", type=int, default=400)
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal(a.max_paginas))
    else:
        tel = Counter()
        for p in uitgaven():
            d = lees(p)
            tel[f"{d['uitgave']} ({d['herkomst']})"] = len(d["records"])
        print(json.dumps(tel, ensure_ascii=False, indent=1))
