"""Gedeelde hulp voor de registerpijplijn (Uitbreiding C, eigenaarsbesluit 2026-10-07).

Pure stdlib. Paden, downloaden met sha256, naamontleding van registernamen en
tekstnormalisatie. Geen DB-toegang en geen schrijfacties op het model: dat doet
naar_model.py via de REST-API.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "registers"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import looptijd  # noqa: E402  (ROOT/looptijd.py: dezelfde tijdlogica als de server)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36 propagandamodel-registers")


def sha256_bestand(pad: Path) -> str:
    h = hashlib.sha256()
    with open(pad, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def download(url: str, doel: Path, timeout: int = 300) -> Path:
    doel.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tijdelijk = doel.with_suffix(doel.suffix + ".tmp")
    with urllib.request.urlopen(req, timeout=timeout) as r, open(tijdelijk, "wb") as f:
        while True:
            blok = r.read(1 << 20)
            if not blok:
                break
            f.write(blok)
    tijdelijk.replace(doel)
    return doel


def get_json(url: str, timeout: int = 60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def schoon(tekst: str | None) -> str:
    """Witruimte samenvoegen en zachte afbreekstreepjes (U+00AD) weghalen."""
    return " ".join((tekst or "").replace("\xad", "").split())


def sleutel(tekst: str | None) -> str:
    """Hoofdletter-, diakriet- en leestekenongevoelige vorm (zoals server._naam_sleutel)."""
    s = unicodedata.normalize("NFKD", tekst or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^\w]+", " ", s).split())


def _afkorting(tekst: str) -> bool:
    """'CPB', 'CvdM', 'SBS6' — geen spatie en minstens twee hoofdletters."""
    return " " not in tekst.strip() and sum(c.isupper() for c in tekst) >= 2


def namen_van(naam: str, afkorting: str | None = None) -> list[str]:
    """Sleutels waaronder een organisatie in vrije tekst genoemd kan zijn: de hele naam, de naam
    zonder toevoeging tussen haakjes, en de toevoeging zelf alleen als het om een afkorting gaat
    ('Centraal Planbureau (CPB)', 'CPB (Centraal Planbureau)'). Een omschrijving zoals in
    'HUMAN (omroep)' of 'ISGA (Universiteit Leiden)' is geen naam van die organisatie.
    `afkorting` (entities.metadata.afkorting, 2026-10-14) telt mee onder dezelfde regel als een
    afkorting tussen haakjes: minstens drie tekens ('OM' is in vrije tekst het woord 'om')."""
    uit = [sleutel(naam)]
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", naam or "")
    if m:
        hoofd, toevoeging = m.group(1), m.group(2)
        uit.append(sleutel(hoofd))
        if (_afkorting(hoofd) or _afkorting(toevoeging)) and len(sleutel(toevoeging)) >= 3:
            uit.append(sleutel(toevoeging))
    if afkorting and len(sleutel(afkorting)) >= 3:
        uit.append(sleutel(afkorting))
    return [u for u in dict.fromkeys(uit) if u]


def noemt(tekst: str, naam: str, afkorting: str | None = None) -> bool:
    """Staat de organisatie (een van namen_van) als hele woorden in de tekst?"""
    t = f" {sleutel(tekst)} "
    return any(f" {n} " in t for n in namen_van(naam, afkorting))


# ── Afkortingen (entities.metadata.afkorting, eigenaarsbesluit 2026-10-14) ───
# Het model kent geen aliassen; een organisatie die het nieuws bij haar afkorting noemt (RWS,
# IND, CJIB, NVWA) is vindbaar via metadata.afkorting. Een afkorting is van één organisatie:
# botst ze met een andere levende knoop (naam, afkorting tussen haakjes of eigen afkorting),
# dan krijgt geen van beide haar (AP = Associated Press, NH = de omroep, RvS ~ RVS).
def _haakjes(naam: str | None) -> tuple[str, str] | None:
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", naam or "")
    return (m.group(1), m.group(2)) if m else None


def afkorting_sleutels(naam: str | None, afkorting: str | None = None) -> set[str]:
    """Alle sleutels waarmee deze knoop kort genoemd kan worden, voor de botsingsregel: de naam,
    de naam zonder haakjes, wat tussen haakjes staat (ook korter dan drie tekens, maar alleen als
    één van beide een afkorting is) en de eigen afkorting."""
    uit = {sleutel(naam)}
    h = _haakjes(naam)
    if h:
        uit.add(sleutel(h[0]))
        if _afkorting(h[0]) or _afkorting(h[1]):
            uit.add(sleutel(h[1]))
    if afkorting:
        uit.add(sleutel(afkorting))
    return {u for u in uit if u}


def _initialen(naam: str) -> str:
    return "".join(w[:1] for w in sleutel(naam).split())


def _deelreeks(kort: str, lang: str) -> bool:
    it = iter(lang)
    return all(c in it for c in kort)


def geen_afkorting(afkorting: str | None, naam: str) -> str | None:
    """Is dit een echte afkorting die nog niet in de naam staat? None = ja; anders de reden.
    Echt: één woord, en minstens twee hoofdletters/cijfers ('NVWA', 'CvdM', 'aCBG') of de letters
    volgen de beginletters van de naam ('Ctgb', 'Rli'). Niet: de naam zelf (een gemeente heeft haar
    naam als 'afkorting'), een omschrijving ('DG Douane', 'Nederlands Filmfonds') of iets wat al
    in de naam staat ('Centraal Planbureau (CPB)')."""
    afk = schoon(afkorting)
    if not afk:
        return "geen afkorting"
    k = sleutel(afk)
    if not k or k == sleutel(naam):
        return "afkorting is de naam zelf"
    if k in afkorting_sleutels(naam) or f" {k} " in f" {sleutel(naam)} ":
        return "staat al in de naam"
    if " " in afk or len(afk) > 15:
        return "geen afkorting (meer woorden)"
    hoofdletters = sum(c.isupper() or c.isdigit() for c in afk)
    if hoofdletters < 2 and not _deelreeks(k.replace(" ", ""), _initialen(naam)):
        return "geen afkorting (volgt de naam niet)"
    return None


def afkorting_botst(afkorting: str, eid: int | None, entiteiten) -> str | None:
    """Botst deze afkorting met een andere levende knoop? `entiteiten`: (id, naam, afkorting)
    van de levende knopen (niet vervangen, niet afgewezen). None = vrij; anders de reden."""
    k = sleutel(afkorting)
    for i, naam, eigen in entiteiten:
        if i == eid:
            continue
        if k in afkorting_sleutels(naam, eigen):
            return f"botst met #{i} '{naam}'"
    return None


# ── Namen uit het register ontleden ─────────────────────────────────────────
# Registernamen zijn vrij: "dhr. drs. A.C.C. (Christiaan) Rebergen", "Mw. A. van Dam",
# "Vice-admiraal Ad van de Sande", "Drs. Johannes Hermanus Roedolph Pierik", "Dhr. Fortuin".
RANGEN = {"vice-admiraal", "luitenant-admiraal", "schout-bij-nacht", "admiraal", "generaal",
          "luitenant-generaal", "generaal-majoor", "brigade-generaal", "bgen", "kolonel",
          "lkol", "luitenant-kolonel", "commandeur", "majoor", "kapitein", "commodore"}
TITELS = {"mr", "dr", "drs", "ir", "ing", "prof", "bc", "ds", "lic", "em", "dra"}
ACHTER = {"msc", "ma", "ba", "mba", "llm", "mpa", "med", "phd", "ra", "mphil", "bsc", "mdr",
          "aa", "emba", "llb", "msc.", "cpa", "rc", "emoc",
          # 2026-10-09: "Erik Akerboom MPM" werd een tweede knoop naast "Erik Akerboom"
          "mpm", "mpp", "mcm", "mres", "dba", "bba", "mlitt", "mjur", "mmc"}
TUSSEN = {"van", "de", "der", "den", "het", "ten", "ter", "te", "in", "'t", "‘t", "’t", "op",
          "d'", "du", "la", "le", "von", "zu", "di", "da", "del", "dos", "el", "al", "uit"}
_INITIAAL = re.compile(r"^(?:[A-ZÀ-Ý][a-z]{0,2}\.)+[A-ZÀ-Ý]?\.?$|^[A-ZÀ-Ý]{1,3}\.(?:[A-ZÀ-Ý][a-z]?\.)*$")


def _is_titel(tok: str) -> bool:
    kaal = tok.lower().strip(".,")
    if kaal in TITELS:
        return True
    # samengestelde titels zonder spatie: "mr.dr.", "Prof.dr.I.J." (titeldeel), "ir.drs."
    delen = [d for d in kaal.split(".") if d]
    return bool(delen) and all(d in TITELS for d in delen)


def _splits_samengesteld(tok: str) -> list[str]:
    """'Prof.dr.I.J.' → ['Prof.', 'dr.', 'I.J.']: titels die tegen voorletters aan staan."""
    delen = [d + "." for d in tok.split(".") if d]
    if len(delen) < 2 or not tok.endswith("."):
        return [tok]
    uit, rest = [], []
    for d in delen:
        if not rest and d.lower().strip(".") in TITELS:
            uit.append(d)
        else:
            rest.append(d)
    return uit + (["".join(rest)] if rest else [])


def ontleed_naam(ruw: str | None) -> dict:
    """Ontleed een registernaam. Retourneert
    {register, roepnaam, voornamen, voorletters, tussenvoegsel, achternaam, weergave,
     volledig (bool: er is een voornaam), alleen_achternaam (bool)}.

    Regel voor namen zonder voorletters of roepnaam: staat er een aanhef voor ("Mw. Olde
    Meule", "Dhr. Fortuin"), dan is de rest de achternaam; zonder aanhef ("Michel van der
    Koogh") is het eerste deel de voornaam."""
    naam = schoon(ruw)
    roepnaam = None
    for m in list(re.finditer(r"\(([^)]+)\)", naam)):
        inhoud = schoon(m.group(1))
        # "(Christiaan)" is een roepnaam; "(b.d.)" of "(waarnemend)" niet
        if inhoud[:1].isupper() and "." not in inhoud and roepnaam is None:
            roepnaam = inhoud
    naam = schoon(re.sub(r"\([^)]*\)", " ", naam))
    tokens: list[str] = []
    for tok in naam.split():
        tokens.extend(_splits_samengesteld(tok))
    aanhef = False
    while tokens:
        kop = tokens[0].lower().strip(".,")
        if kop == "de" and len(tokens) > 1 and tokens[1].lower().strip(".,") == "heer":
            tokens = tokens[2:]
            aanhef = True
        elif kop in {"dhr", "mw", "mevr", "mevrouw", "heer", "hr", "jhr", "jkvr", "jonkheer",
                     "jonkvrouw"}:
            tokens.pop(0)
            aanhef = True
        elif kop in RANGEN or _is_titel(tokens[0]) or tokens[0].lower() in {"(b.d.)", "b.d."}:
            tokens.pop(0)
        else:
            break
    # Een titel achter de naam ("MSc", "MPM"), maar nooit de achternaam zelf ("A. van Ma")
    while (len(tokens) > 2 and tokens[-1].lower().strip(".,") in ACHTER
           and tokens[-2].lower() not in TUSSEN):
        tokens.pop()
    voorletters = ""
    while tokens and _INITIAAL.match(tokens[0]):
        voorletters += tokens.pop(0)
    voornamen = []
    if not voorletters and not aanhef:
        while len(tokens) > 1 and tokens[0].lower() not in TUSSEN:
            voornamen.append(tokens.pop(0))
    tussen = []
    while len(tokens) > 1 and tokens[0].lower() in TUSSEN:
        tussen.append(tokens.pop(0))
    achternaam = " ".join(tokens)
    tussenvoegsel = " ".join(tussen)
    volle_achternaam = schoon(f"{tussenvoegsel} {achternaam}")
    if roepnaam:
        weergave = f"{roepnaam} {volle_achternaam}"
    elif voornamen:
        weergave = f"{' '.join(voornamen)} {volle_achternaam}"
    elif voorletters:
        weergave = f"{voorletters} {volle_achternaam}"
    else:
        weergave = volle_achternaam
    return {
        "register": schoon(ruw),
        "roepnaam": roepnaam,
        "voornamen": " ".join(voornamen) or None,
        "voorletters": voorletters or None,
        "tussenvoegsel": tussenvoegsel or None,
        "achternaam": achternaam or None,
        "weergave": schoon(weergave),
        "volledig": bool(roepnaam or voornamen),
        "alleen_achternaam": not (roepnaam or voornamen or voorletters),
    }


# Partijnamen uit het register → partij-entiteit (op naam). Lokale partijen: geen knoop.
PARTIJEN = {
    "vvd": "VVD", "volkspartij voor vrijheid en democratie": "VVD",
    "cda": "CDA", "christen democratisch appel": "CDA", "christen-democratisch appèl": "CDA",
    "d66": "D66", "democraten 66": "D66", "pvda": "PvdA", "partij van de arbeid": "PvdA",
    "groenlinks": "GroenLinks", "sp": "SP", "socialistische partij": "SP",
    "christenunie": "ChristenUnie", "cu": "ChristenUnie", "sgp": "SGP",
    "staatkundig gereformeerde partij": "SGP", "pvv": "PVV", "partij voor de vrijheid": "PVV",
    "ja21": "JA21", "bbb": "BBB (BoerBurgerBeweging)", "boerburgerbeweging": "BBB (BoerBurgerBeweging)",
    "pvdd": "Partij voor de Dieren", "partij voor de dieren": "Partij voor de Dieren",
    "fvd": "Forum voor Democratie", "forum voor democratie": "Forum voor Democratie",
    "volt": "Volt Nederland", "denk": "DENK", "50plus": "50PLUS",
    "nsc": "NSC (Nieuw Sociaal Contract)", "nieuw sociaal contract": "NSC (Nieuw Sociaal Contract)",
    # GroenLinks en PvdA gingen samen verder als Progressief Nederland (PRO); de Eerste
    # Kamerfractie heet in het register nog "GroenLinks-PvdA".
    "pro": "Progressief Nederland (PRO)", "progressief nederland": "Progressief Nederland (PRO)",
    "groenlinks pvda": "Progressief Nederland (PRO)",
}


def partij_naam(registernaam: str) -> str | None:
    """Partijnaam uit het register ('CDA', 'Volkspartij voor Vrijheid en Democratie (VVD)') →
    naam van de partij-entiteit; None voor lokale of onbekende partijen."""
    kandidaten = [registernaam]
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", registernaam)
    if m:
        kandidaten += [m.group(2), m.group(1)]
    for k in kandidaten:
        s = sleutel(k)
        if s in PARTIJEN:
            return PARTIJEN[s]
        if s.replace(" ", "") in PARTIJEN:
            return PARTIJEN[s.replace(" ", "")]
    return None


# ── Bestaan begrenst (eigenaarsbesluit 2026-10-13) ──────────────────────────
def klem_relaties(relaties: list[dict], bestaan_van, tel) -> None:
    """Een verband loopt nooit buiten het bestaan van zijn eindpunten (looptijd.py): het begin
    wordt het laatste van het begin uit het record en het begin van bron en doel, het einde het
    vroegste. Zo begint het ambt van een burgemeester sinds 2019 bij een gemeente die in 2023
    ontstond pas in 2023, en de zeggenschap van een ministerie in zijn huidige vorm (EZK
    2010-10-14) over een ouder agentschap pas in 2010. Een ontbrekend begin blijft ontbreken (nooit
    een begin verzinnen). `bestaan_van(ref)` → (van, tot) of (None, None) voor wie niet begrenst
    (een persoon, een nieuwe knoop zonder datum). Telt in `tel` wat geklemd is en wat de
    bestaanspoort (looptijd.conflicten) daarna nog zou weigeren."""
    for r in relaties:
        grenzen = [bestaan_van(r["bron"]), bestaan_van(r["doel"])]
        start, eind = r.get("start"), r.get("eind")
        for van, tot in grenzen:
            if start and van and looptijd.voor(start, van):
                start = van
                tel["bestaan: begin naar het begin van een eindpunt"] += 1
            if eind and tot and looptijd.voor(tot, eind):
                eind = tot
                tel["bestaan: einde naar het einde van een eindpunt"] += 1
        if start != r.get("start"):
            r["start_record"] = r.get("start")
        r["start"], r["eind"] = start, eind
        ents = [{"type": "organisatie", "active_from": van, "active_until": tot, "name": "eindpunt"}
                for van, tot in grenzen]
        if looptijd.conflicten({"active_from": start, "active_until": eind}, ents[0], ents[1]):
            tel["bestaan: de poort zou weigeren"] += 1
