"""AFM-meldingenregisters — uitgave ophalen en lezen (eigendoms- en bestuursnetwerken, 2026-10-20).

De Autoriteit Financiële Markten houdt openbare meldingenregisters bij (www.afm.nl/nl-nl/sector/
registers/meldingenregisters; het in de opdracht genoemde registers.afm.nl bestaat niet in DNS).
Elk register heeft een export als CSV en als XML (/export.aspx?type=<guid>&format=xml); alleen de
XML draagt het meldingid, dat ook de detailpagina noemt (…/details?id=<meldingid>). Drie registers
hebben netwerkwaarde:

  sd   substantiële deelnemingen (Wft 5.3, sinds 2006-11-01): wie houdt ≥ 3% van het kapitaal of de
       stemmen van een uitgevende instelling, met de datum waarop de meldingsplicht ontstond (een
       drempel van 3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 75 of 95% werd bereikt, over- of
       onderschreden). Per melding een rij per soort aandeel × (kapitaalbelang, stemrecht); hier één
       record per melding met de totalen en de verdeling reëel/potentieel, rechtstreeks/middellijk.
  bc   bestuurders en commissarissen (art. 5:48 Wft): alleen bestuurders en commissarissen van een
       uitgevende instelling zijn meldplichtig, dus een melding bevestigt dat de persoon op die datum
       bestuurder of commissaris was. Alleen datum, instelling en naam worden bewaard (geen posities).
  mar  transacties leidinggevenden (MAR art. 19): de persoon met leidinggevende verantwoordelijkheid,
       zijn functie en de LEI van de instelling. Meldingen van nauw gelieerde personen (familie,
       eigen vennootschappen: veld <nauwgelieerdaan>) worden NIET bewaard; de transacties zelf ook
       niet (alleen datum, instelling, LEI, naam en functie).

Formaat van de uitgave: data/registers/afm/afm_<datum>.json (+ .sha256, kale hash) met
{"bron", "uitgave", "opgehaald", "bronbestanden": {register: {url, sha256, bytes}}, "weggelaten",
"records": {sleutel: record}}. De recordsleutel is '<register>:<meldingid>'; de recordregel
('regel') is het citaat en bestaat alleen uit letterlijke veldwaarden van de melding.

Licentie: "Uitsluitend met uitdrukkelijke bronvermelding van de AFM is het toegestaan de informatie
op deze website geheel of gedeeltelijk op enigerlei wijze over te nemen en/of te verspreiden"
(afm.nl, Over deze website). robots.txt van www.afm.nl: alles toegestaan behalve /sitecore.

Geen schrijfacties op het model (dat doet afm_naar_model.py via de REST-API).

    python3 tools/registers/afm.py haal [--ruw <map met sd.xml/bc.xml/mar.xml>]
    python3 tools/registers/afm.py lees
"""
from __future__ import annotations

import datetime
import html
import http.client
import io
import json
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, UA, noemt, ontleed_naam, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "afm"
URL = "https://www.afm.nl/nl-nl/sector/registers/meldingenregisters"
MAP = DATA / BRON
KOPPELINGEN = Path(__file__).resolve().parent / "afm_koppelingen.json"
UITGEVER = "Autoriteit Financiële Markten (AFM)"
TITEL = ("AFM, openbare meldingenregisters (substantiële deelnemingen; bestuurders en commissarissen; "
         "transacties leidinggevenden MAR 19), uitgave {uitgave}")
EXPORT = "https://www.afm.nl/export.aspx?type={guid}&format=xml"
DETAIL = URL + "/{register}/details?id={id}"
REGISTERS = {
    "sd": ("substantiele-deelnemingen", "1331d46f-3fb6-4a36-b903-9584972675af"),
    "bc": ("bestuurders-commissarissen", "1b934036-12ad-4950-9773-31361d5adbd9"),
    "mar": ("transacties-leidinggevenden-mar19-", "0ee836dc-5520-459d-bcf4-a4a689de6614"),
}
PAUZE = 1.5   # seconden tussen verzoeken
DREMPEL = 3.0   # laagste meldingsdrempel (sinds 2013-07-01; daarvoor 5%)
# Dagen waarop de meldingsplicht door een wetswijziging ontstond, niet doordat het belang een
# drempel passeerde: de start van het register (Wft, 2006-11-01) en de verlaging van de
# drempel van 5 naar 3% (2013-07-01). Een eerste melding op zo'n dag is geen begin.
OVERGANGSDAGEN = {"2006-11-01": "start van het register onder de Wft",
                  "2013-07-01": "verlaging van de eerste drempel naar 3%"}
# Een functie uit het MAR-register die bestuur of toezicht is (geen 'General Manager', 'Head of …').
TOEZICHT = re.compile(r"\b(commissaris\w*|raad van (toezicht|commissarissen)|supervisory|non[- ]?executive|"
                      r"toezichthouder)\b", re.I)
BESTUUR = re.compile(r"\b(bestuurder|raad van bestuur|statutair directeur|management board|executive board|"
                     r"board of management|managing board|executive director|board of directors|director of the issuer|"
                     r"chairman|chairwoman|chair of the board|ceo|chief executive officer|cfo|chief financial officer|"
                     r"voorzitter|president and ceo|member of the board|board member|lid van de raad van bestuur)\b", re.I)


class FormaatFout(Exception):
    """De uitgave of de export heeft niet het verwachte formaat."""


# ── ophalen ─────────────────────────────────────────────────────────────────
def _get(url: str, doel: Path, timeout: int = 900) -> Path:
    """Beleefd downloaden: vier pogingen, langer wachten bij 429/5xx."""
    doel.parent.mkdir(parents=True, exist_ok=True)
    tijdelijk = doel.with_suffix(doel.suffix + ".tmp")
    for poging in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r, open(tijdelijk, "wb") as f:
                while True:
                    blok = r.read(1 << 20)
                    if not blok:
                        break
                    f.write(blok)
            tijdelijk.replace(doel)
            return doel
        except urllib.error.HTTPError as e:
            if e.code == 404 or poging == 3:
                raise
            time.sleep(60 * (poging + 1) if e.code in (429, 503) else 10)
        except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError):
            if poging == 3:
                raise
            time.sleep(20)
    raise FormaatFout(f"niet op te halen: {url}")


class _Schoon(io.RawIOBase):
    """De export bevat tekenverwijzingen naar stuurtekens ('&#x5;') die geen geldige XML zijn;
    die worden weggelaten terwijl het bestand stroomt (de grens van een blok wordt bewaakt)."""
    _REF = re.compile(rb"&#(x[0-9A-Fa-f]+|[0-9]+);")

    def __init__(self, pad: Path):
        self.f = open(pad, "rb")
        self.rest = b""

    def readable(self):
        return True

    def _vervang(self, m):
        v = m.group(1)
        n = int(v[1:], 16) if v[:1] == b"x" else int(v)
        return b"" if n < 32 and n not in (9, 10, 13) else m.group(0)

    def readinto(self, b):
        blok = self.f.read(max(1, len(b) - len(self.rest)))
        data = self.rest + blok
        self.rest = b""
        if blok:
            amp = data.rfind(b"&")
            if amp != -1 and b";" not in data[amp:] and len(data) - amp < 16:
                data, self.rest = data[:amp], data[amp:]
        data = self._REF.sub(self._vervang, data)
        n = len(data)
        if n > len(b):   # kan niet: vervangen maakt nooit langer
            raise FormaatFout("sanering maakte het blok langer")
        b[:n] = data
        return n

    def close(self):
        self.f.close()
        super().close()


def _vermeldingen(pad: Path):
    """Elke <vermelding> van het hoogste niveau als element (het geneste <vermelding> is een label)."""
    diepte = 0
    for ev, el in ET.iterparse(io.BufferedReader(_Schoon(pad), 1 << 20), events=("start", "end")):
        if el.tag == "vermelding":
            if ev == "start":
                diepte += 1
                continue
            diepte -= 1
            if diepte == 0:
                yield el
                el.clear()


def _veld(el, tag: str) -> str:
    x = el.find(tag)
    return schoon(html.unescape(x.text or "")) if x is not None and x.text else ""


def _datum(waarde: str) -> str | None:
    """'10/16/2026 12:00:00 AM' of '10/16/2026' → '2026-10-16'."""
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", waarde or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(3)), int(m.group(1)), int(m.group(2))).isoformat()
    except ValueError:
        return None


def procent(waarde: str | None) -> float | None:
    """'3,14 %' → 3.14."""
    m = re.match(r"^\s*(-?\d+(?:[.,]\d+)?)\s*%?\s*$", waarde or "")
    return float(m.group(1).replace(",", ".")) if m else None


def _via(wijze: str) -> list[str]:
    """'Middellijk<BR>(DWS Investment GmbH)' → ['DWS Investment GmbH']."""
    return [schoon(v) for v in re.findall(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)", html.unescape(wijze or "")) if schoon(v)]


# ── per register: rijen → records ─────────────────────────────────────────
def lees_sd(pad: Path, tel: Counter) -> dict[str, dict]:
    meldingen: dict[str, dict] = {}
    for el in _vermeldingen(pad):
        mid = _veld(el, "meldingid")
        if not mid:
            raise FormaatFout("substantiële deelneming zonder meldingid")
        m = meldingen.get(mid)
        if m is None:
            m = meldingen[mid] = {
                "sleutel": f"sd:{mid}", "register": "sd", "meldingid": mid,
                "datum": _datum(_veld(el, "datumontstaanmelding")),
                "uitgevende_instelling": _veld(el, "uitgevende-instelling"), "kvk": _veld(el, "kvk"),
                "plaats": _veld(el, "plaats"), "meldingsplichtige": _veld(el, "meldingsplichtige"),
                "kapitaal": None, "stemrecht": None, "via": [], "soorten": []}
        proc = _veld(el, "soort-aandeel-proc")
        verdeling = {"totaal": _veld(el, "totale-deelneming"),
                     "reeel_rechtstreeks": _veld(el, "rechtstreeks-reeel"),
                     "reeel_middellijk": _veld(el, "middellijk-reeel"),
                     "potentieel_rechtstreeks": _veld(el, "rechtstreeks-potentieel"),
                     "potentieel_middellijk": _veld(el, "middellijk-potentieel")}
        veld = {"Kapitaalbelang": "kapitaal", "Stemrecht": "stemrecht"}.get(proc)
        if veld is None:
            raise FormaatFout(f"melding {mid}: onbekende verdeling '{proc}'")
        if m[veld] is None:
            m[veld] = verdeling
        elif m[veld] != verdeling:
            tel["sd: verdeling verschilt binnen een melding"] += 1
        for v in _via(_veld(el, "wijze-van-beschikken")):
            if v not in m["via"]:
                m["via"].append(v)
        soort = _veld(el, "soort-aandeel")
        if soort and soort not in m["soorten"]:
            m["soorten"].append(soort)
        tel["sd: rijen"] += 1
    for m in meldingen.values():
        if not (m["datum"] and m["uitgevende_instelling"] and m["meldingsplichtige"] and m["kapitaal"]
                and m["stemrecht"]):
            raise FormaatFout(f"melding {m['meldingid']} is onvolledig")
        m["url"] = DETAIL.format(register=REGISTERS["sd"][0], id=m["meldingid"])
        m["regel"] = regel_sd(m)
    return {m["sleutel"]: m for m in meldingen.values()}


def _verdeling_tekst(v: dict) -> str:
    return (f"{v['totaal']} (reëel {v['reeel_rechtstreeks']} rechtstreeks, {v['reeel_middellijk']} middellijk; "
            f"potentieel {v['potentieel_rechtstreeks']} rechtstreeks, {v['potentieel_middellijk']} middellijk)")


def regel_sd(m: dict) -> str:
    plaats = ", ".join(x for x in (m["plaats"], f"KvK {m['kvk']}" if m["kvk"] else "") if x)
    via = f"; middellijk via {', '.join(m['via'])}" if m["via"] else ""
    return (f"AFM-register substantiële deelnemingen, melding {m['meldingid']} (datum meldingsplicht "
            f"{m['datum']}): meldingsplichtige {m['meldingsplichtige']}; uitgevende instelling "
            f"{m['uitgevende_instelling']}{f' ({plaats})' if plaats else ''}; kapitaalbelang "
            f"{_verdeling_tekst(m['kapitaal'])}; stemrecht {_verdeling_tekst(m['stemrecht'])}{via}")


def lees_bc(pad: Path, tel: Counter) -> dict[str, dict]:
    uit = {}
    for el in _vermeldingen(pad):
        mid = _veld(el, "meldingid")
        naam = _veld(el, "Meldingsplichtige")
        n = ontleed_naam(naam)
        rec = {"sleutel": f"bc:{mid}", "register": "bc", "meldingid": mid,
               "datum": _datum(_veld(el, "DatumMeldingsplicht")),
               "uitgevende_instelling": _veld(el, "UitgevendeInstelling"), "persoon": naam,
               "voorletters": n["voorletters"] or "", "tussenvoegsel": n["tussenvoegsel"] or "",
               "achternaam": n["achternaam"] or "", "functie": "",
               "url": DETAIL.format(register=REGISTERS["bc"][0], id=mid)}
        if not (mid and rec["datum"] and rec["uitgevende_instelling"] and naam):
            raise FormaatFout(f"bestuurders/commissarissen: melding {mid or '?'} is onvolledig")
        rec["regel"] = (f"AFM-register bestuurders en commissarissen (art. 5:48 Wft), melding {mid} (datum "
                        f"meldingsplicht {rec['datum']}): meldingsplichtige {naam}; uitgevende instelling "
                        f"{rec['uitgevende_instelling']}")
        uit[rec["sleutel"]] = rec
        tel["bc: meldingen"] += 1
    return uit


_INITIAAL = re.compile(r"^(?:[A-ZÀ-Ý][a-zà-ý]?\.?-?)+\.$|^[A-ZÀ-Ý]\.?$")
_TUSSEN = {"van", "de", "der", "den", "het", "ten", "ter", "te", "von", "zu", "di", "da", "del", "dos", "du",
           "la", "le", "el", "al", "'t"}


def mar_naam(ruw: str, achternaam: str = "") -> dict:
    """'Dassen R.J.M.', 'Rueda Gamboa, de J.', 'Does, van der P.W.' → voorletters, tussenvoegsel,
    achternaam (het veld meldingsplichtigeachternaam gaat voor als het er is)."""
    naam = schoon(ruw)
    if "," in naam:
        achter, rest = [schoon(x) for x in naam.split(",", 1)]
    else:
        tokens = naam.split()
        i = len(tokens)
        while i > 1 and _INITIAAL.match(tokens[i - 1]):
            i -= 1
        achter, rest = " ".join(tokens[:i]), " ".join(tokens[i:])
    letters, tussen, voornamen = [], [], []
    for tok in rest.split():
        if _INITIAAL.match(tok):
            letters.append(tok)
        elif tok.lower() in _TUSSEN:
            tussen.append(tok.lower())
        else:
            voornamen.append(tok)
    achter = schoon(achternaam) or achter
    return {"voorletters": "".join(letters) or ("".join(v[0] + "." for v in voornamen) if voornamen else ""),
            "tussenvoegsel": " ".join(tussen), "achternaam": achter, "voornamen": " ".join(voornamen)}


def lees_mar(pad: Path, tel: Counter) -> dict[str, dict]:
    uit = {}
    for el in _vermeldingen(pad):
        mid = _veld(el, "meldingid")
        if _veld(el, "nauwgelieerdaan"):
            tel["mar: nauw gelieerde persoon (niet bewaard)"] += 1
            continue
        naam = _veld(el, "meldingsplichtige")
        n = mar_naam(naam, _veld(el, "meldingsplichtigeachternaam"))
        rec = {"sleutel": f"mar:{mid}", "register": "mar", "meldingid": mid,
               "datum": _datum(_veld(el, "transactiedatum")),
               "uitgevende_instelling": _veld(el, "uitgevendeinstelling"), "lei": _veld(el, "lei"),
               "persoon": naam, "voorletters": n["voorletters"], "tussenvoegsel": n["tussenvoegsel"],
               "achternaam": n["achternaam"], "functie": _veld(el, "functie"),
               "url": DETAIL.format(register=REGISTERS["mar"][0], id=mid)}
        if not (mid and rec["datum"] and rec["uitgevende_instelling"] and naam):
            raise FormaatFout(f"MAR 19: melding {mid or '?'} is onvolledig")
        lei = f" (LEI {rec['lei']})" if rec["lei"] else ""
        functie = f"; functie {rec['functie']}" if rec["functie"] else ""
        rec["regel"] = (f"AFM-register transacties leidinggevenden (MAR art. 19), melding {mid} (transactiedatum "
                        f"{rec['datum']}): meldingsplichtige {naam}{functie}; uitgevende instelling "
                        f"{rec['uitgevende_instelling']}{lei}")
        uit[rec["sleutel"]] = rec
        tel["mar: meldingen"] += 1
    return uit


LEZERS = {"sd": lees_sd, "bc": lees_bc, "mar": lees_mar}


# ── uitgaven ────────────────────────────────────────────────────────────────
def uitgaven() -> list[Path]:
    return sorted(MAP.glob("afm_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"afm_{uitgave}.json"


def haal(ruw: Path | None = None, meld=print) -> Path:
    """De drie XML-exports ophalen (of uit `ruw`: sd.xml, bc.xml, mar.xml) en als één uitgave
    bewaren. De ruwe exports (samen ± 400 MB) blijven buiten data/registers."""
    vandaag = datetime.date.today().isoformat()
    map_ = Path(ruw) if ruw else Path(tempfile.mkdtemp(prefix="afm_"))
    records, tel, bronbestanden = {}, Counter(), {}
    for kort, (register, guid) in REGISTERS.items():
        pad = map_ / f"{kort}.xml"
        url = EXPORT.format(guid=guid)
        if not pad.exists():
            meld(f"  afm: {register} ophalen")
            _get(url, pad)
            time.sleep(PAUZE)
        bronbestanden[kort] = {"register": register, "url": url, "sha256": sha256_bestand(pad),
                               "bytes": pad.stat().st_size}
        deel = LEZERS[kort](pad, tel)
        if not deel:
            raise FormaatFout(f"{register}: geen meldingen")
        records.update(deel)
    MAP.mkdir(parents=True, exist_ok=True)
    pad = pad_van(vandaag)
    pad.write_text(json.dumps({"bron": BRON, "uitgave": vandaag, "opgehaald": vandaag,
                               "bronbestanden": bronbestanden, "telling": dict(sorted(tel.items())),
                               "records": records}, ensure_ascii=False, indent=0, sort_keys=True),
                   encoding="utf-8")
    (MAP / f"afm_{vandaag}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


# ── lezen (ook voor de registercheck) ──────────────────────────────────────
def lees(pad: Path) -> dict:
    data = json.loads(pad.read_text(encoding="utf-8"))
    if data.get("bron") != BRON or not isinstance(data.get("records"), dict):
        raise FormaatFout(f"{pad.name} is geen AFM-uitgave")
    return {**data, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "titel": TITEL.format(uitgave=data["uitgave"])}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"afm_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


# ── controle (registercheck) ───────────────────────────────────────────────
def koppelingen() -> dict:
    """afm_koppelingen.json: met de hand nagelopen AFM-naam → entiteit-id (ondernemingen, houders,
    personen). Dezelfde lijst voor de import en de registercheck."""
    if not KOPPELINGEN.exists():
        return {}
    data = json.loads(KOPPELINGEN.read_text(encoding="utf-8"))
    return {soort: {sleutel(k): v for k, v in (data.get(soort) or {}).items() if not k.startswith("_")}
            for soort in ("ondernemingen", "houders", "personen", "houdersoorten")}


# Wat na het weghalen van 'of the Issuer', 'Board of Directors' e.d. nog naar een ánder orgaan wijst
# (dochter, divisie, fonds, beheerder): dan is het geen bestuur of toezicht bij de instelling zelf.
_EIGEN_ORGAAN = re.compile(r"\b(of|van|from) (the |het |de )?(issuer|company|vennootschap|board( of (directors|management))?|"
                           r"directors|(management|executive|supervisory|managing) board|raad van (bestuur|commissarissen|toezicht))\b",
                           re.I)
_ANDER_ORGAAN = re.compile(r"\b(of|for|van|bij|at)\b|groepsmaatschappij|subsidiar|investment manager|beheerder|"
                           r"business (unit|group)|division|fund|fonds|also associated|"
                           r"\b(limited|ltd|b\.v\.|n\.v\.|gmbh|inc|plc|s\.a\.)(?=\W|$)", re.I)


def is_bestuursfunctie(functie: str | None, instelling: str | None = None) -> str | None:
    """'commissaris' | 'bestuurder' | None. Alleen bestuur of toezicht bij de uitgevende instelling
    zelf: 'Non-executive Director', 'Lid Raad van Commissarissen', 'CEO', 'Chief Financial Officer
    (Director)', 'Member Board of Directors', 'Aegon N.V. Management Board member'; niet 'CEO of
    Airbus Helicopters', 'Bestuurder Groepsmaatschappij', 'Chief Executive Officer of Cintra' of
    'General Manager, Germany'."""
    if not functie:
        return None
    rest = _EIGEN_ORGAAN.sub(" ", re.sub(r"\([^)]*\)", " ", functie))
    if instelling:
        kaal = re.sub(r"\s+(N\.?V\.?|Ltd\.?|plc|SE|S\.?A\.?|AG)$", "", instelling, flags=re.I)
        for n in sorted({instelling, kaal}, key=len, reverse=True):
            rest = re.sub(r"(\b(of|van|bij|at|for)\s+)?" + re.escape(n) + r"(?=\W|$)", " ", rest, flags=re.I)
    if _ANDER_ORGAAN.search(rest):
        return None
    if TOEZICHT.search(functie):
        return "commissaris"
    if BESTUUR.search(functie):
        return "bestuurder"
    return None


def org_past(naam_record: str, e: dict, ids: list[tuple[str, str]], soort: str) -> bool:
    """De organisatie uit het record is dit eindpunt: een externe id uit het record (kvk, lei),
    de vastgelegde koppeling, of de naam van het eindpunt staat als hele woorden in de recordnaam."""
    if any(i in e["ids"] for i in ids if i[1]):
        return True
    if koppelingen().get(soort, {}).get(sleutel(naam_record)) == e["id"]:
        return True
    return e["type"] != "persoon" and noemt(naam_record, e["name"])


def persoon_past(rec: dict, e: dict) -> str | None:
    """De achternaam uit het record staat in de naam, en de voornaam begint met de eerste voorletter
    (of de vastgelegde koppeling noemt dit eindpunt). None = past."""
    pk = persoonsleutel(rec)
    if koppelingen().get("personen", {}).get(sleutel(pk)) == e["id"]:
        return None
    achter = sleutel(rec.get("achternaam") or "")
    naam = sleutel(re.sub(r"\([^)]*\)", " ", e["name"]))
    delen = [d for d in re.split(r"[\s\-]+", achter) if len(d) > 2]
    if not achter or (f" {achter} " not in f" {naam} " and not (delen and f" {delen[0]} " in f" {naam} ")):
        return f"de achternaam '{rec.get('achternaam')}' staat niet in '{e['name']}'"
    letters = re.sub(r"[^a-z]", "", sleutel(rec.get("voorletters") or ""))
    eerste = naam.split()[0] if naam.split() else ""
    if letters and eerste[:1] != letters[:1]:
        return f"de voornaam van '{e['name']}' past niet bij '{rec['persoon']}'"
    return None


def persoonsleutel(rec: dict) -> str:
    """'dassen|rjm': achternaam (zonder tussenvoegsel) en voorletters, zoals beide registers ze geven."""
    letters = re.sub(r"[^a-z]", "", sleutel(rec.get("voorletters") or ""))
    return f"{sleutel(rec.get('achternaam') or '')}|{letters}"


EIGENDOMSTYPES = ("eigendom", "zeggenschap", "investering")


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """sd: 'eigendom'/'zeggenschap'/'investering' van de meldingsplichtige (bron) naar de uitgevende
    instelling (doel; KvK uit het record, vastgelegde koppeling of naam).
    bc/mar: 'bestuurder' tussen de persoon uit het record (achternaam en eerste voorletter) en de
    uitgevende instelling (mar: LEI, koppeling of naam); bij mar moet de functie bestuur of toezicht
    zijn en is een melding van een nauw gelieerde persoon nooit in de uitgave."""
    reg = rec.get("register")
    if reg == "sd":
        if relatie_type not in EIGENDOMSTYPES:
            return f"een melding van een substantiële deelneming is eigendom/zeggenschap, niet '{relatie_type}'"
        bron, doel = eindpunten[0], eindpunten[1]
        if not org_past(rec["uitgevende_instelling"], doel, [("kvk", rec.get("kvk") or "")], "ondernemingen"):
            return f"'{doel['name']}' is niet de uitgevende instelling '{rec['uitgevende_instelling']}' uit {sleutel_r}"
        if bron["type"] == "persoon":
            if persoon_past({**mar_naam(rec["meldingsplichtige"]), "persoon": rec["meldingsplichtige"]}, bron):
                return f"'{bron['name']}' is niet de meldingsplichtige '{rec['meldingsplichtige']}' uit {sleutel_r}"
            return None
        if not org_past(rec["meldingsplichtige"], bron, [], "houders"):
            return f"'{bron['name']}' is niet de meldingsplichtige '{rec['meldingsplichtige']}' uit {sleutel_r}"
        return None
    if reg in ("bc", "mar"):
        if relatie_type != "bestuurder":
            return f"een melding van een bestuurder of commissaris is 'bestuurder', niet '{relatie_type}'"
        if reg == "mar" and not is_bestuursfunctie(rec.get("functie"), rec.get("uitgevende_instelling")):
            return f"de functie '{rec.get('functie')}' uit {sleutel_r} is geen bestuur of toezicht"
        personen = [e for e in eindpunten if e["type"] == "persoon"]
        if len(personen) != 1:
            return "precies één eindpunt moet een persoon zijn"
        reden = persoon_past(rec, personen[0])
        if reden:
            return reden
        org = [e for e in eindpunten if e is not personen[0]][0]
        if not org_past(rec["uitgevende_instelling"], org, [("lei", rec.get("lei") or "")], "ondernemingen"):
            return f"'{org['name']}' is niet de uitgevende instelling '{rec['uitgevende_instelling']}' uit {sleutel_r}"
        return None
    return f"onbekend AFM-register in {sleutel_r}"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="AFM-meldingenregisters ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--ruw", help="map met al opgehaalde exports (sd.xml, bc.xml, mar.xml)")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal(Path(a.ruw) if a.ruw else None))
    else:
        for p in uitgaven():
            d = lees(p)
            print(json.dumps({"uitgave": d["uitgave"], "records": dict(Counter(r["register"] for r in d["records"].values())),
                              "telling": d.get("telling")}, ensure_ascii=False, indent=1))
