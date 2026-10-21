#!/usr/bin/env python3
"""Eigen metingen: een vooraf vastgelegde telling als bron (eigenaarsbesluit 2026-10-16).

De eigenaar wil zelf onderzoek kunnen doen: een eigen meting telt als bewijs, "het moet een tool
zijn waarmee je zelf dat kan bepalen", "zolang je aan journalistieke codes houdt".

Een meting telt welke organisatie of deskundige in welk medium aan het woord komt, over welk
onderwerp, met welk standpunt, en of de financiering vermeld wordt. De levensloop:

  opzet       de selectieregel (media, periode, zoektermen, hoe artikelen gevonden worden), de
              groepen, de vragen met hun opties, de uitkomstmaat en de stopregel; bewerkbaar.
  vastgelegd  de opzet is bevroren (opzet_hash) vóór de eerste waarneming; nu worden de
              waarnemingen ingevoerd (url, datum, medium, groep, wie, letterlijk citaat, codes) en
              blind gecontroleerd door een ander account.
  afgerond    de dataset (waarnemingen en controles) is bevroren (data_hash), de samenvatting
              staat vast. Alleen nu is de meting publiek en kan ze als bron dienen.

De samenvatting bestaat uit vaste, deterministische tekstregels, bijvoorbeeld
"Clingendael (n=34) · standpunt: tegen 25 (74%), voor 3 (9%), neutraal 6 (18%)". Een argument
citeert er letterlijk één (methode verbatim_quote) uit de bron "Eigen meting #<id>" (brontype
dataset, cluster 'meting:<id>'). Hoe zwaar die bron weegt, bepaalt de eigenaar met de gewone
bronclassificatie (PATCH /api/sources/<id>/classificatie).

De journalistieke codes (Leidraad van de Raad voor de Journalistiek, NVJ-code) zijn harde
voorwaarden, als punten a–h van code_check():
  a. methode vooraf (transparantie)       e. hoor en wederhoor
  b. volledigheid (geen cherry-picking)   f. feit en mening gescheiden (de claim)
  c. juistheid en herleidbaarheid         g. privacy (alleen publieke rollen)
  d. verificatie door een ander           h. correctie (rectificatielink op de pagina)
Afronden eist a–d; een meting als bewijs gebruiken eist a–h.

Pure stdlib, leest alleen. Gedeeld door server.py (API en pagina), scripts/metingcheck.py (de
deterministische A1), scripts/meting_controle.py en scripts/test_metingen.py.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGINA = ROOT / "web" / "meting.html"

STATUSSEN = ("opzet", "vastgelegd", "afgerond")
WEDERHOOR_SOORTEN = ("reactie", "verzoek_zonder_reactie", "gepubliceerd_standpunt")
WEDERHOOR_LABELS = {"reactie": "reactie", "verzoek_zonder_reactie": "verzoek zonder reactie",
                    "gepubliceerd_standpunt": "gepubliceerd standpunt"}
# De bron van een meting: brontype dataset, eigen cluster (M1.2: één meting is één bewijslijn)
CLUSTER_PREFIX = "meting:"
BRON_PUBLISHER = "Propagandamodel (eigen meting)"
BRON_TITEL = "Eigen meting #{id}: {titel}"
# Verificatie door een ander (punt d)
CONTROLE_FRACTIE = 0.20
CONTROLE_MINIMUM = 5
OVEREENSTEMMING_DREMPEL = 80.0      # procent; daaronder een waarschuwing
MIN_SELECTIEREGEL = 20              # tekens: de selectieregel beschrijft hoe artikelen gevonden zijn
RECTIFICATIE_LINK = "/tip?betreft=meting:"
SCHEIDING = " · "
SLEUTEL_RE = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
DATUM_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_RE = re.compile(r"^https?://[^\s/$.?#][^\s]*$", re.IGNORECASE)

OPZET_VELDEN = ("selectie", "groepen", "vragen", "uitkomst", "stopregel")
SELECTIE_VELDEN = ("media", "periode", "zoektermen", "regel")
# Velden van een waarneming die de dataset vormen (de data_hash); citaat_gevonden is
# controlemetadata en hoort er niet bij
DATA_VELDEN = ("id", "groep", "wie", "entity_id", "medium_entity_id", "url", "archief_url",
               "datum", "citaat", "codes", "notitie", "contributed_by")

# (sleutel, titel, de regel zoals de pagina hem uitlegt)
CODE_PUNTEN = (
    ("a", "Methode vooraf (transparantie)",
     "De opzet ligt vast vóór de eerste waarneming: een selectieregel (media, periode, zoektermen "
     "of regel), groepen, vragen met opties, een uitkomstmaat en een stopregel."),
    ("b", "Volledigheid (geen cherry-picking)",
     "Elke waarneming valt binnen de selectieregel (periode en media), en de selectieregel "
     "beschrijft hoe de artikelen gevonden zijn."),
    ("c", "Juistheid en herleidbaarheid",
     "Elke waarneming heeft een url, een datum, een letterlijk citaat en een code voor elke vraag, "
     "en het citaat is op de url (of de archiefkopie) letterlijk teruggevonden."),
    ("d", "Verificatie door een ander",
     "Minstens 20% van de waarnemingen (minimaal 5, of alle bij minder dan 5) is blind opnieuw "
     "gecodeerd door een ander account dan de invoerder. De overeenstemming per vraag staat erbij; "
     "onder 80% is dat een waarschuwing met de afwijkingen."),
    ("e", "Hoor en wederhoor",
     "Voor elke groep met een benoemde organisatie en voor elk medium is er minstens één "
     "wederhoorregel: een reactie, een verzoek zonder reactie (met datum) of een gepubliceerd "
     "standpunt (met bron)."),
    ("f", "Feit en mening gescheiden",
     "De claim van het bewijsargument beschrijft alleen wat gemeten is en geeft geen oordeel "
     "(getoetst met het strenge lexicon van de eigen stem)."),
    ("g", "Privacy",
     "Wie geciteerd wordt, doet dat in een publieke rol: naam en functie zoals in het artikel, of "
     "een knoop in het model. Geen privépersonen."),
    ("h", "Correctie",
     "De publieke metingpagina heeft een link om een onjuistheid te melden "
     "(/tip?betreft=meting:<id>)."),
)
AFRONDEN_EIST = ("a", "b", "c", "d")
BEWIJS_EIST = tuple(p[0] for p in CODE_PUNTEN)

# Wie zo omschreven wordt, spreekt niet in een publieke rol (punt g)
PRIVE_PATROON = re.compile(
    r"\b(?:buurtbewoners?|omwonenden?|voorbijgangers?|ooggetuigen?|inwoners?|bewoners?|"
    r"lezers?|kijkers?|luisteraars?|anoniem\w*|privépersoon|privepersoon|particulier\w*|"
    r"scholieren?|nabestaanden?|een man|een vrouw|een jongen|een meisje|een moeder|een vader)\b",
    re.IGNORECASE)
# Een functie na de naam: "Rob de Wijk, oprichter HCSS", "Rob de Wijk (HCSS)", "… – hoogleraar"
FUNCTIE_SCHEIDING = re.compile(r",|\(|\s[–—-]\s")

# Oordeelwoorden die in een meting-claim een verdict zijn, bovenop het strenge lexicon van de eigen
# stem (validation.EIGEN_STEM_STRENG). Buiten citaten en toeschrijvingen, net als daar.
OORDEEL_METING = (
    (r"\beenzijdig\w*", "eenzijdig"),
    (r"\bonevenwichtig\w*", "onevenwichtig"),
    (r"\bpartijdig\w*", "partijdig"),
    (r"\bbevooroordeeld\w*", "bevooroordeeld"),
    (r"\bspreekbuis\w*", "spreekbuis"),
    (r"\bverzw[ie]\w*|\bdoodgezwegen\b|\bdoodzw[ie]\w*", "verzwijgt"),
    (r"\bmanipul\w*", "manipuleert"),
    (r"\bpropaganda\w*", "propaganda"),
)
_OORDEEL_METING_RE = [(re.compile(p, re.IGNORECASE), label) for p, label in OORDEEL_METING]


# ------------------------------------------------------------------ hulpjes
def canoniek(obj) -> str:
    """Vaste JSON-vorm (gesorteerde sleutels, geen witruimte) voor de hashes."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def opzet_hash(opzet) -> str:
    return sha256(canoniek(opzet))


def datum_ok(waarde) -> bool:
    if not isinstance(waarde, str) or not DATUM_RE.match(waarde):
        return False
    try:
        datetime.date.fromisoformat(waarde)
    except ValueError:
        return False
    return True


def url_ok(waarde) -> bool:
    return isinstance(waarde, str) and bool(URL_RE.match(waarde.strip()))


def _is_id(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool) and x > 0


def _tekst(x) -> str:
    return x.strip() if isinstance(x, str) else ""


def _norm(tekst) -> str:
    t = unicodedata.normalize("NFKD", tekst or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^\w\s]", " ", t).split())


def _json(waarde, standaard):
    if waarde is None or waarde == "":
        return standaard
    if isinstance(waarde, (dict, list)):
        return waarde
    try:
        return json.loads(waarde)
    except (TypeError, ValueError):
        return standaard


def pct(k: int, n: int) -> int:
    """Percentage, half naar boven afgerond (25/34 → 74)."""
    return int(k * 100 / n + 0.5) if n else 0


def _ids_tekst(ids) -> str:
    return ", ".join(f"#{i}" for i in ids)


def selectie(opzet) -> dict:
    s = (opzet or {}).get("selectie")
    return s if isinstance(s, dict) else {}


def periode(opzet) -> tuple[str | None, str | None]:
    p = selectie(opzet).get("periode")
    p = p if isinstance(p, dict) else {}
    return p.get("van"), p.get("tot")


def media(opzet) -> list[int]:
    m = selectie(opzet).get("media")
    return [x for x in m if _is_id(x)] if isinstance(m, list) else []


def groepen(opzet) -> list[dict]:
    g = (opzet or {}).get("groepen")
    return [x for x in g if isinstance(x, dict)] if isinstance(g, list) else []


def vragen(opzet) -> list[dict]:
    v = (opzet or {}).get("vragen")
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


# ------------------------------------------------------------------ opzet
def valideer_opzet(opzet, *, bestaat=None, volledig: bool = False) -> list[str]:
    """Fouten in een opzet (leeg = in orde). Altijd de vorm; met ``volledig`` ook of alles er is
    wat punt a eist (bij het vastleggen). ``bestaat(entity_id) -> bool`` controleert verwijzingen
    naar knopen in het model."""
    if not isinstance(opzet, dict):
        return ["'opzet' moet een object zijn"]
    fouten = []
    onbekend = sorted(set(opzet) - set(OPZET_VELDEN))
    if onbekend:
        fouten.append(f"onbekende velden in de opzet: {', '.join(onbekend)} "
                      f"(toegestaan: {', '.join(OPZET_VELDEN)})")
    sel = opzet.get("selectie", {})
    if sel is None:
        sel = {}
    media_ids, van, tot, regel, zoektermen = [], None, None, "", ""
    if not isinstance(sel, dict):
        fouten.append("'selectie' moet een object zijn")
    else:
        onbekend = sorted(set(sel) - set(SELECTIE_VELDEN))
        if onbekend:
            fouten.append(f"onbekende velden in de selectie: {', '.join(onbekend)} "
                          f"(toegestaan: {', '.join(SELECTIE_VELDEN)})")
        m = sel.get("media", [])
        if m is None:
            m = []
        if not isinstance(m, list) or not all(_is_id(x) for x in m):
            fouten.append("'selectie.media' moet een lijst entiteit-id's (gehele getallen) zijn")
        elif len(set(m)) != len(m):
            fouten.append("'selectie.media' noemt een medium twee keer")
        else:
            media_ids = m
            if bestaat:
                for x in m:
                    if not bestaat(x):
                        fouten.append(f"medium #{x} bestaat niet in het model")
        p = sel.get("periode", {})
        if p is None:
            p = {}
        if not isinstance(p, dict):
            fouten.append("'selectie.periode' moet een object {van, tot} zijn")
        else:
            onbekend = sorted(set(p) - {"van", "tot"})
            if onbekend:
                fouten.append(f"onbekende velden in de periode: {', '.join(onbekend)}")
            van, tot = p.get("van"), p.get("tot")
            for naam, w in (("van", van), ("tot", tot)):
                if w is not None and not datum_ok(w):
                    fouten.append(f"'selectie.periode.{naam}' moet JJJJ-MM-DD of null zijn")
            if datum_ok(van) and datum_ok(tot) and van > tot:
                fouten.append("de periode eindigt vóór ze begint ('van' ligt na 'tot')")
        for veld in ("zoektermen", "regel"):
            if sel.get(veld) is not None and not isinstance(sel.get(veld), str):
                fouten.append(f"'selectie.{veld}' moet tekst zijn")
        regel, zoektermen = _tekst(sel.get("regel")), _tekst(sel.get("zoektermen"))
    grs = opzet.get("groepen", [])
    if grs is None:
        grs = []
    groepnamen = []
    if not isinstance(grs, list):
        fouten.append("'groepen' moet een lijst zijn")
        grs = []
    for i, gr in enumerate(grs, 1):
        if not isinstance(gr, dict):
            fouten.append(f"groep {i} moet een object {{naam, entity_ids}} zijn")
            continue
        onbekend = sorted(set(gr) - {"naam", "entity_ids"})
        if onbekend:
            fouten.append(f"groep {i}: onbekende velden {', '.join(onbekend)}")
        naam = _tekst(gr.get("naam"))
        if not naam:
            fouten.append(f"groep {i} heeft geen naam")
        elif len(naam) > 120:
            fouten.append(f"groep {i}: de naam is langer dan 120 tekens")
        elif _norm(naam) in {_norm(n) for n in groepnamen}:
            fouten.append(f"de groepsnaam '{naam}' komt twee keer voor")
        else:
            groepnamen.append(naam)
        ids = gr.get("entity_ids", [])
        if ids is None:
            ids = []
        if not isinstance(ids, list) or not all(_is_id(x) for x in ids):
            fouten.append(f"groep {i}: 'entity_ids' moet een lijst entiteit-id's zijn")
        elif bestaat:
            for x in ids:
                if not bestaat(x):
                    fouten.append(f"groep {i}: knoop #{x} bestaat niet in het model")
    vrs = opzet.get("vragen", [])
    if vrs is None:
        vrs = []
    sleutels = []
    if not isinstance(vrs, list):
        fouten.append("'vragen' moet een lijst zijn")
        vrs = []
    for i, v in enumerate(vrs, 1):
        if not isinstance(v, dict):
            fouten.append(f"vraag {i} moet een object {{sleutel, vraag, opties}} zijn")
            continue
        onbekend = sorted(set(v) - {"sleutel", "vraag", "opties"})
        if onbekend:
            fouten.append(f"vraag {i}: onbekende velden {', '.join(onbekend)}")
        s = v.get("sleutel")
        if not isinstance(s, str) or not SLEUTEL_RE.match(s):
            fouten.append(f"vraag {i}: de sleutel moet een korte naam zijn van kleine letters, "
                          "cijfers en '_' (bijvoorbeeld 'standpunt')")
        elif s in sleutels:
            fouten.append(f"de sleutel '{s}' komt twee keer voor")
        else:
            sleutels.append(s)
        if not _tekst(v.get("vraag")):
            fouten.append(f"vraag {i} heeft geen vraagtekst")
        opties = v.get("opties")
        if not isinstance(opties, list) or not all(isinstance(o, str) and o.strip()
                                                   for o in opties):
            fouten.append(f"vraag {i}: 'opties' moet een lijst niet-lege teksten zijn")
        elif len(opties) < 2:
            fouten.append(f"vraag {i}: geef minstens twee opties")
        elif len({o.strip().lower() for o in opties}) != len(opties):
            fouten.append(f"vraag {i}: een optie komt twee keer voor")
        elif any(o != o.strip() for o in opties):
            fouten.append(f"vraag {i}: een optie begint of eindigt met een spatie")
    for veld in ("uitkomst", "stopregel"):
        if opzet.get(veld) is not None and not isinstance(opzet.get(veld), str):
            fouten.append(f"'{veld}' moet tekst zijn")
    if volledig:
        if not media_ids:
            fouten.append("de selectie noemt geen media")
        if not datum_ok(van):
            fouten.append("de periode heeft geen begindatum ('van')")
        if not (zoektermen or regel):
            fouten.append("de selectie heeft geen zoektermen en geen regel")
        if len(regel) < MIN_SELECTIEREGEL:
            fouten.append("de selectieregel beschrijft niet hoe de artikelen gevonden worden "
                          f"(archief, zoekmachine, zoektermen; minstens {MIN_SELECTIEREGEL} tekens)")
        if not groepnamen:
            fouten.append("de opzet heeft geen groepen")
        if not sleutels:
            fouten.append("de opzet heeft geen vragen")
        if not _tekst(opzet.get("uitkomst")):
            fouten.append("de opzet heeft geen uitkomstmaat")
        if not _tekst(opzet.get("stopregel")):
            fouten.append("de opzet heeft geen stopregel")
    return fouten


def valideer_codes(opzet, codes, *, volledig: bool = False) -> list[str]:
    """Fouten in een codering {sleutel: optie} tegen de vragen van de opzet. Met ``volledig``
    moet elke vraag een code hebben (de blinde controle codeert alles)."""
    if codes is None:
        codes = {}
    if not isinstance(codes, dict):
        return ["'codes' moet een object {sleutel: optie} zijn"]
    per = {v.get("sleutel"): v for v in vragen(opzet)}
    fouten = []
    for s, o in codes.items():
        if s not in per:
            fouten.append(f"onbekende vraag '{s}'")
        elif o is not None and o not in (per[s].get("opties") or []):
            fouten.append(f"'{o}' is geen optie van '{s}' (kies uit: "
                          f"{', '.join(per[s].get('opties') or [])})")
    if volledig:
        for s in per:
            if codes.get(s) is None:
                fouten.append(f"geen code voor '{s}'")
    return fouten


# ------------------------------------------------------------------ laden
def laad(conn, meting_id: int) -> dict | None:
    """Een meting met alles erbij, of None. ``conn.row_factory`` moet sqlite3.Row zijn."""
    rij = conn.execute("SELECT * FROM metingen WHERE id = ?", (meting_id,)).fetchone()
    if rij is None:
        return None
    m = dict(rij)
    m["opzet"] = _json(m.get("opzet"), {})
    m["samenvatting"] = _json(m.get("samenvatting"), None)
    m["waarnemingen"] = []
    for r in conn.execute("SELECT * FROM meting_waarnemingen WHERE meting_id = ? ORDER BY id",
                          (meting_id,)):
        w = dict(r)
        w["codes"] = _json(w.get("codes"), {})
        m["waarnemingen"].append(w)
    m["controles"] = []
    for r in conn.execute("""SELECT c.* FROM meting_controles c
                             JOIN meting_waarnemingen w ON w.id = c.waarneming_id
                             WHERE w.meting_id = ? ORDER BY c.id""", (meting_id,)):
        c = dict(r)
        c["codes"] = _json(c.get("codes"), {})
        m["controles"].append(c)
    m["wederhoor"] = [dict(r) for r in conn.execute(
        "SELECT * FROM meting_wederhoor WHERE meting_id = ? ORDER BY id", (meting_id,))]
    ids = set(media(m["opzet"]))
    for gr in groepen(m["opzet"]):
        ids.update(x for x in (gr.get("entity_ids") or []) if _is_id(x))
    for w in m["waarnemingen"]:
        ids.update(x for x in (w.get("entity_id"), w.get("medium_entity_id")) if x)
    ids.update(r["entity_id"] for r in m["wederhoor"] if r.get("entity_id"))
    m["entiteiten"] = {}
    lijst = sorted(ids)
    for start in range(0, len(lijst), 500):
        deel = lijst[start:start + 500]
        for r in conn.execute(f"SELECT id, name, type, status FROM entities WHERE id IN "  # noqa: S608
                              f"({','.join('?' * len(deel))})", deel):
            m["entiteiten"][r["id"]] = {"naam": r["name"], "type": r["type"],
                                        "status": r["status"]}
    return m


def naam_van(m, entity_id) -> str:
    e = (m.get("entiteiten") or {}).get(entity_id)
    return e["naam"] if e else f"knoop #{entity_id}"


# ------------------------------------------------------------------ dataset en hashes
def dataset(m) -> dict:
    """De bevroren dataset: de opzet-hash, de waarnemingen (zonder controlemetadata) en de
    blinde controles. Grondslag van de data_hash."""
    ws = sorted(m["waarnemingen"], key=lambda w: w["id"])
    cs = sorted(m["controles"], key=lambda c: (c["waarneming_id"], c["door"]))
    return {"opzet_hash": m.get("opzet_hash"),
            "waarnemingen": [{k: w.get(k) for k in DATA_VELDEN} for w in ws],
            "controles": [{"waarneming_id": c["waarneming_id"], "codes": c.get("codes") or {},
                           "door": c["door"]} for c in cs]}


def data_hash(m) -> str:
    return sha256(canoniek(dataset(m)))


def nodig_controles(n: int) -> int:
    """20% van de waarnemingen, minimaal 5; alle bij minder dan 5."""
    if n < CONTROLE_MINIMUM:
        return n
    return max(CONTROLE_MINIMUM, math.ceil(CONTROLE_FRACTIE * n))


def gecontroleerd(m) -> set[int]:
    """Waarnemingen met minstens één volledige blinde controle door een ander dan de invoerder."""
    per_w = {w["id"]: w for w in m["waarnemingen"]}
    sleutels = [v.get("sleutel") for v in vragen(m["opzet"])]
    uit = set()
    for c in m["controles"]:
        w = per_w.get(c["waarneming_id"])
        if w is None or c["door"] == w["contributed_by"]:
            continue
        codes = c.get("codes") or {}
        if all(codes.get(s) is not None for s in sleutels):
            uit.add(w["id"])
    return uit


# ------------------------------------------------------------------ samenvatting
def _blok(label, ws, opzet, namen) -> dict:
    """Telling voor één groep (of alle groepen samen) en haar vaste tekstregels."""
    selectie_media = media(opzet)
    per_medium = {}
    for w in ws:
        per_medium[w.get("medium_entity_id")] = per_medium.get(w.get("medium_entity_id"), 0) + 1
    volgorde = list(selectie_media) + sorted(
        (x for x in per_medium if x not in selectie_media), key=lambda x: (x is None, x or 0))

    def medium_naam(mid):
        if mid is None:
            return "zonder medium"
        return namen.get(str(mid)) or f"medium #{mid}"

    media_lijst = [{"medium_id": mid, "naam": medium_naam(mid), "aantal": per_medium.get(mid, 0)}
                   for mid in volgorde]
    regels = [f"{label} (n={len(ws)}){SCHEIDING}media: "
              + ", ".join(f"{x['naam']} {x['aantal']}" for x in media_lijst)]
    vragen_uit = []
    for v in vragen(opzet):
        s, opties = v.get("sleutel"), v.get("opties") or []
        codes = [(w.get("codes") or {}).get(s) for w in ws]
        gecodeerd = [c for c in codes if c is not None]
        n = len(gecodeerd)
        tellingen = [{"optie": o, "aantal": sum(1 for c in gecodeerd if c == o),
                      "pct": pct(sum(1 for c in gecodeerd if c == o), n)} for o in opties]
        if n:
            tekst = (f"{label} (n={n}){SCHEIDING}{s}: "
                     + ", ".join(f"{t['optie']} {t['aantal']} ({t['pct']}%)" for t in tellingen))
        else:
            tekst = f"{label} (n=0){SCHEIDING}{s}: geen waarnemingen"
        zonder = len(ws) - n
        if zonder and n:
            tekst += f"{SCHEIDING}zonder code {zonder}"
        regels.append(tekst)
        vragen_uit.append({"sleutel": s, "vraag": v.get("vraag"), "n": n, "zonder_code": zonder,
                           "opties": tellingen, "regel": tekst})
    return {"naam": label, "n": len(ws), "media": media_lijst, "vragen": vragen_uit,
            "regels": regels}


def samenvatting(m, namen: dict | None = None) -> dict:
    """De samenvatting per groep × vraag × optie (n, aantal, %), met per groep het aantal per
    medium, en de vaste tekstregels. ``namen`` {str(medium-id): naam} legt de mediumnamen vast
    (bij het afronden bevroren, zodat een latere hernoeming de regels niet verandert)."""
    opzet = m["opzet"]
    if namen is None:
        ids = set(media(opzet)) | {w.get("medium_entity_id") for w in m["waarnemingen"]
                                   if w.get("medium_entity_id")}
        namen = {str(i): naam_van(m, i) for i in sorted(ids)}
    per_groep: dict[str, list] = {gr.get("naam"): [] for gr in groepen(opzet) if gr.get("naam")}
    for w in m["waarnemingen"]:
        per_groep.setdefault(w.get("groep"), []).append(w)
    blokken = [_blok(label, ws, opzet, namen) for label, ws in per_groep.items()]
    totaal = (_blok("Alle groepen", list(m["waarnemingen"]), opzet, namen)
              if len(per_groep) >= 2 else None)
    regels = [r for b in blokken for r in b["regels"]] + (totaal["regels"] if totaal else [])
    return {"n": len(m["waarnemingen"]), "namen": namen, "groepen": blokken, "totaal": totaal,
            "regels": regels}


def regels_van(m) -> list[str]:
    """De samenvattingsregels: bevroren bij een afgeronde meting, anders live berekend."""
    if m.get("status") == "afgerond" and m.get("samenvatting"):
        return list(m["samenvatting"].get("regels") or [])
    return samenvatting(m)["regels"]


# ------------------------------------------------------------------ overeenstemming
def kappa(paren) -> float | None:
    """Cohen's kappa over (eerste, controle)-paren. None als er geen paren zijn of als beide
    codeurs alles in één en dezelfde categorie zetten (dan is kappa niet gedefinieerd)."""
    n = len(paren)
    if not n:
        return None
    po = sum(1 for a, b in paren if a == b) / n
    cats = {a for a, _ in paren} | {b for _, b in paren}
    pe = sum((sum(1 for a, _ in paren if a == c) / n) * (sum(1 for _, b in paren if b == c) / n)
             for c in cats)
    if pe >= 1:
        return None
    return round((po - pe) / (1 - pe), 3)


def overeenstemming(m) -> dict:
    """Per vraag: n paren, aantal gelijk, percentage, Cohen's kappa en de afwijkingen tussen de
    eerste codering en de blinde controle (alleen controles door een ander dan de invoerder)."""
    per_w = {w["id"]: w for w in m["waarnemingen"]}
    uit = {}
    for v in vragen(m["opzet"]):
        s = v.get("sleutel")
        paren, afwijkingen = [], []
        for c in m["controles"]:
            w = per_w.get(c["waarneming_id"])
            if w is None or c["door"] == w["contributed_by"]:
                continue
            a, b = (w.get("codes") or {}).get(s), (c.get("codes") or {}).get(s)
            if a is None or b is None:
                continue
            paren.append((a, b))
            if a != b:
                afwijkingen.append({"waarneming_id": w["id"], "eerste": a, "controle": b,
                                    "door": c["door"]})
        n = len(paren)
        gelijk = n - len(afwijkingen)
        p = round(100 * gelijk / n, 1) if n else None
        uit[s] = {"n": n, "gelijk": gelijk, "pct": p, "kappa": kappa(paren),
                  "afwijkingen": afwijkingen,
                  "waarschuwing": bool(n) and p < OVEREENSTEMMING_DREMPEL}
    return uit


# ------------------------------------------------------------------ claim (punt f)
def claim_treffers(claim: str | None) -> list[str]:
    """Oordelen of etiketten in de eigen stem van een meting-claim: het strenge lexicon van de
    eigen stem (validation.EIGEN_STEM_STRENG, met dezelfde uitzondering voor citaten en
    toeschrijvingen), plus een paar oordeelwoorden die bij tellingen horen ('eenzijdig')."""
    import validation  # hier, niet bovenaan: validation leest zelf metingen (integriteitscheck)
    treffers = list(validation.eigen_stem_treffers(claim or "", streng=True))
    splits = getattr(validation, "_ZINSDEEL_SPLIT", re.compile(r"(?<=[.!?:;])\s+"))
    citaat = getattr(validation, "_CITAAT_SPAN", None)
    toeschrijving = getattr(validation, "_TOESCHRIJVING", None)
    for deel in splits.split(claim or ""):
        kaal = citaat.sub(" ", deel) if citaat else deel
        if toeschrijving and toeschrijving.search(kaal):
            continue
        for regex, label in _OORDEEL_METING_RE:
            if regex.search(kaal) and label not in treffers:
                treffers.append(label)
    return treffers


# ------------------------------------------------------------------ journalistieke codes
def _groepeer(problemen: dict) -> list[str]:
    """{probleem: [waarneming-id's]} → leesbare regels, in de volgorde van eerste voorkomen."""
    return [f"{probleem}: {_ids_tekst(ids)}" for probleem, ids in problemen.items()]


def _wh_geldig(r) -> bool:
    soort = r.get("soort")
    if soort == "reactie":
        return bool(_tekst(r.get("tekst")))
    if soort == "verzoek_zonder_reactie":
        return datum_ok(r.get("datum"))
    if soort == "gepubliceerd_standpunt":
        return url_ok(r.get("bron_url"))
    return False


def wederhoor_eisen(m) -> list[dict]:
    """Wie wederhoor moet krijgen: elke groep met een benoemde organisatie en elk medium uit de
    selectie. Per eis: label, de id's en naam die een wederhoorregel kunnen dragen, en of er een
    geldige regel is."""
    eisen = []
    for gr in groepen(m["opzet"]):
        ids = [x for x in (gr.get("entity_ids") or []) if _is_id(x)]
        if ids:
            eisen.append({"soort": "groep", "label": gr.get("naam"), "ids": ids,
                          "namen": [gr.get("naam")] + [naam_van(m, i) for i in ids]})
    for mid in media(m["opzet"]):
        eisen.append({"soort": "medium", "label": naam_van(m, mid), "ids": [mid],
                      "namen": [naam_van(m, mid)]})
    for eis in eisen:
        namen = {_norm(n) for n in eis["namen"] if n}
        eis["regels"] = [r["id"] for r in m["wederhoor"] if _wh_geldig(r) and (
            (r.get("entity_id") and r["entity_id"] in eis["ids"])
            or (_norm(r.get("partij")) and _norm(r.get("partij")) in namen))]
        eis["voldaan"] = bool(eis["regels"])
    return eisen


def _privacy_probleem(m, w) -> str | None:
    wie = _tekst(w.get("wie"))
    if not wie:
        return "geen naam en functie"
    if PRIVE_PATROON.search(wie):
        return "omschreven als privépersoon"
    if w.get("entity_id"):
        if w["entity_id"] in (m.get("entiteiten") or {}):
            return None
        return "de gekoppelde knoop bestaat niet"
    delen = FUNCTIE_SCHEIDING.split(wie, maxsplit=1)
    if len(delen) < 2 or not _tekst(re.sub(r"[)\s]+$", "", delen[1])):
        return "geen functie bij de naam (zoals in het artikel), en geen knoop in het model"
    return None


def code_check(m, *, claim: str | None = None, pagina: str | None = None) -> list[dict]:
    """De journalistieke codes als lijst punten {sleutel, titel, regel, ok, uitleg, open,
    waarschuwingen}. ``ok`` is True, False, of None (nog niet te toetsen: punt f zonder claim).
    ``pagina`` is de tekst van de metingpagina (standaard web/meting.html), voor punt h."""
    opzet = m["opzet"]
    ws = m["waarnemingen"]
    vrs = vragen(opzet)
    groepnamen = [gr.get("naam") for gr in groepen(opzet)]
    selectie_media = media(opzet)
    van, tot = periode(opzet)
    punten = {}

    # a. Methode vooraf
    open_a = []
    if m.get("status") == "opzet":
        open_a.append("de opzet is nog niet vastgelegd")
    else:
        if not m.get("vastgelegd_at") or not m.get("opzet_hash"):
            open_a.append("het vastlegmoment of de opzet-hash ontbreekt")
        elif opzet_hash(opzet) != m["opzet_hash"]:
            open_a.append("de opzet is gewijzigd na het vastleggen (de opzet-hash klopt niet)")
        te_vroeg = [w["id"] for w in ws if m.get("vastgelegd_at")
                    and str(w.get("created_at") or "") < str(m["vastgelegd_at"])]
        if te_vroeg:
            open_a.append(f"ingevoerd vóór het vastleggen: {_ids_tekst(te_vroeg)}")
    open_a += valideer_opzet(opzet, volledig=True)
    punten["a"] = (not open_a, open_a, [],
                   (f"Opzet vastgelegd op {str(m.get('vastgelegd_at'))[:16]} (UTC; sha256 "
                    f"{(m.get('opzet_hash') or '')[:12]}…), vóór de eerste waarneming: "
                    f"selectieregel, {len(groepnamen)} groep(en), {len(vrs)} vraag/vragen, "
                    "uitkomstmaat en stopregel.") if not open_a else
                   "Nog open: " + "; ".join(open_a[:3]) + ("; …" if len(open_a) > 3 else ""))

    # b. Volledigheid
    open_b = []
    if len(_tekst(selectie(opzet).get("regel"))) < MIN_SELECTIEREGEL:
        open_b.append("de selectieregel beschrijft niet hoe de artikelen gevonden zijn")
    prob_b: dict[str, list] = {}
    for w in ws:
        d = w.get("datum")
        if datum_ok(d):
            if datum_ok(van) and d < van:
                prob_b.setdefault(f"vóór de periode ({van})", []).append(w["id"])
            if datum_ok(tot) and d > tot:
                prob_b.setdefault(f"na de periode ({tot})", []).append(w["id"])
        if not w.get("medium_entity_id"):
            prob_b.setdefault("geen medium", []).append(w["id"])
        elif w["medium_entity_id"] not in selectie_media:
            prob_b.setdefault("medium buiten de selectie", []).append(w["id"])
        if w.get("groep") not in groepnamen:
            prob_b.setdefault("groep staat niet in de opzet", []).append(w["id"])
    open_b += _groepeer(prob_b)
    punten["b"] = (not open_b, open_b, [],
                   (f"Alle {len(ws)} waarnemingen vallen binnen de periode en de media van de "
                    "selectie; de selectieregel beschrijft hoe artikelen gevonden zijn.")
                   if not open_b else "Nog open: " + "; ".join(open_b[:3]))

    # c. Juistheid en herleidbaarheid
    prob_c: dict[str, list] = {}
    for w in ws:
        if not url_ok(w.get("url")):
            prob_c.setdefault("geen geldige url", []).append(w["id"])
        if not datum_ok(w.get("datum")):
            prob_c.setdefault("geen datum (JJJJ-MM-DD)", []).append(w["id"])
        if not _tekst(w.get("citaat")):
            prob_c.setdefault("geen citaat", []).append(w["id"])
        codes = w.get("codes") or {}
        for v in vrs:
            s = v.get("sleutel")
            if codes.get(s) is None:
                prob_c.setdefault(f"geen code voor '{s}'", []).append(w["id"])
            elif codes[s] not in (v.get("opties") or []):
                prob_c.setdefault(f"ongeldige code voor '{s}'", []).append(w["id"])
        if w.get("citaat_gevonden") == 0:
            prob_c.setdefault("citaat niet letterlijk teruggevonden op de url of de archiefkopie",
                              []).append(w["id"])
        elif w.get("citaat_gevonden") is None:
            prob_c.setdefault("citaat nog niet op de url gecontroleerd (metingcheck)",
                              []).append(w["id"])
    open_c = _groepeer(prob_c)
    if m.get("status") == "afgerond":
        if not m.get("data_hash") or data_hash(m) != m["data_hash"]:
            open_c.append("de dataset is gewijzigd na het afronden (de data-hash klopt niet)")
        bevroren = m.get("samenvatting") or {}
        if not bevroren or samenvatting(m, bevroren.get("namen") or {})["regels"] != \
                bevroren.get("regels"):
            open_c.append("de samenvatting klopt niet met de bevroren dataset")
    gevonden = sum(1 for w in ws if w.get("citaat_gevonden") == 1)
    punten["c"] = (not open_c, open_c, [],
                   (f"Alle {len(ws)} waarnemingen hebben url, datum, letterlijk citaat en een code "
                    f"voor elke vraag; {gevonden} citaten letterlijk teruggevonden op de url.")
                   if not open_c else "Nog open: " + "; ".join(open_c[:3]))

    # d. Verificatie door een ander
    n = len(ws)
    nodig = nodig_controles(n)
    gedaan = len(gecontroleerd(m))
    over = overeenstemming(m)
    open_d = [] if gedaan >= nodig else [
        f"nog {nodig - gedaan} blinde controle(s) nodig ({gedaan} van {nodig}: 20% van {n}, "
        f"minimaal {CONTROLE_MINIMUM})"]
    waarschuwingen_d = []
    for s, o in over.items():
        if o["waarschuwing"]:
            afw = ", ".join(f"#{a['waarneming_id']} ({a['eerste']} / {a['controle']})"
                            for a in o["afwijkingen"])
            waarschuwingen_d.append(
                f"'{s}': {str(o['pct']).replace('.', ',')}% overeenstemming"
                f"{' (κ ' + str(o['kappa']).replace('.', ',') + ')' if o['kappa'] is not None else ''}"
                f" over {o['n']} controles; afwijkingen {afw}")
    stand = "; ".join(f"{s} {str(o['pct']).replace('.', ',')}%"
                      + (f" (κ {str(o['kappa']).replace('.', ',')})" if o["kappa"] is not None else "")
                      for s, o in over.items() if o["n"])
    punten["d"] = (not open_d, open_d, waarschuwingen_d,
                   f"{gedaan} van {n} waarnemingen blind gecontroleerd door een ander (nodig: "
                   f"{nodig})" + (f"; overeenstemming: {stand}" if stand else "") + ".")

    # e. Hoor en wederhoor
    eisen = wederhoor_eisen(m)
    open_e = [f"geen wederhoor voor {'groep' if e['soort'] == 'groep' else 'medium'} "
              f"{e['label']}" for e in eisen if not e["voldaan"]]
    punten["e"] = (not open_e, open_e, [],
                   (f"Wederhoor voor alle {len(eisen)} partijen (groepen met een benoemde "
                    "organisatie en media).") if not open_e else
                   "Nog open: " + "; ".join(open_e[:3]) + ("; …" if len(open_e) > 3 else ""))

    # f. Feit en mening gescheiden
    if claim is None:
        punten["f"] = (None, [], [], "Wordt getoetst bij 'Gebruik als bewijs': de claim beschrijft "
                                     "alleen wat gemeten is.")
    else:
        treffers = claim_treffers(claim)
        if not _tekst(claim):
            open_f = ["de claim is leeg"]
        else:
            open_f = [f"oordeel of etiket in de eigen stem: {t}" for t in treffers]
        punten["f"] = (not open_f, open_f, [],
                       "De claim beschrijft wat gemeten is, zonder oordeel." if not open_f
                       else "Nog open: " + "; ".join(open_f))

    # g. Privacy
    prob_g: dict[str, list] = {}
    for w in ws:
        p = _privacy_probleem(m, w)
        if p:
            prob_g.setdefault(p, []).append(w["id"])
    open_g = _groepeer(prob_g)
    punten["g"] = (not open_g, open_g, [],
                   f"Alle {len(ws)} geciteerden spreken in een publieke rol (functie of knoop)."
                   if not open_g else "Nog open: " + "; ".join(open_g[:3]))

    # h. Correctie
    if pagina is None:
        try:
            pagina = PAGINA.read_text(encoding="utf-8")
        except OSError:
            pagina = ""
    ok_h = RECTIFICATIE_LINK in pagina
    punten["h"] = (ok_h, [] if ok_h else ["de metingpagina mist de rectificatielink"], [],
                   f"De pagina linkt naar {RECTIFICATIE_LINK}{m.get('id')} om een onjuistheid te "
                   "melden." if ok_h else "De metingpagina mist de rectificatielink.")

    uit = []
    for sleutel, titel, regel in CODE_PUNTEN:
        ok, open_, waarsch, uitleg = punten[sleutel]
        uit.append({"sleutel": sleutel, "titel": titel, "regel": regel, "ok": ok,
                    "uitleg": uitleg, "open": open_, "waarschuwingen": waarsch})
    return uit


def open_punten(punten, sleutels=BEWIJS_EIST) -> list[str]:
    """De open punten (ok is niet True) als leesbare regels: 'a. Methode vooraf: …'."""
    uit = []
    for p in punten:
        if p["sleutel"] not in sleutels or p["ok"] is True:
            continue
        details = p["open"] or ([p["uitleg"]] if p["ok"] is None else [])
        for d in details or ["niet in orde"]:
            uit.append(f"{p['sleutel']}. {p['titel']}: {d}")
    return uit


def in_orde(punten, sleutels) -> bool:
    return all(p["ok"] is True for p in punten if p["sleutel"] in sleutels)


# ------------------------------------------------------------------ bron
def bron_titel(m) -> str:
    return BRON_TITEL.format(id=m["id"], titel=m.get("titel") or "")


def cluster_key(meting_id) -> str:
    return f"{CLUSTER_PREFIX}{meting_id}"


def meting_id_uit_cluster(cluster) -> int | None:
    if not isinstance(cluster, str) or not cluster.startswith(CLUSTER_PREFIX):
        return None
    rest = cluster[len(CLUSTER_PREFIX):]
    return int(rest) if rest.isdigit() else None
