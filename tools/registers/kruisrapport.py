#!/usr/bin/env python3
"""Kruisrapport over alle registerbronnen (2026-10-20): per organisatie en per publieke persoon in
het model, in welke registers ze opduikt, via welke kanalen, bij welke tegenpartij en in welk
beleidsdomein.

Alleen lezen. Het script leest de bewaarde uitgaven in data/registers/<bron>/ en koppelt met de
Plannen van de importers (<bron>_naar_model.py, in droogloop) — dezelfde koppelregels, niets op
naam alleen. Elk signaal haalt daarna dezelfde controle als scripts/registercheck.py
(<bron>.controleer: het record noemt de organisatie of persoon echt); wat die zou afkeuren, telt
niet. De DB wordt alleen gelezen (mode=ro); er gaat niets naar de REST-API.

Registers en wat een signaal is:
  lobby          vaste toegangspas tot de Tweede Kamer (eigen pas, of opdrachtgever van een pashouder)
  agenda         afspraak (gesprek, ontvangst, werkbezoek) met een bewindspersoon → ministerie
  tk_inspraak    position paper, genodigde of tegenpartij bij een Kamercommissie, namens de organisatie
  ep_netwerk     vergadering met een Nederlands EP-lid; betaalde deelname; functie in de belangenopgave
                 van een EP-lid; commissiezetel van het EP-lid
  giften         gift aan een politieke partij (Wfpp-overzichten), met bedragen
  staatscourant  benoeming, herbenoeming of ontslag (Kroon of bewindspersoon)
  rechtspraak    nevenbetrekking of eerdere functie van een rechter
  tk             Kamerlid; nevenfunctie, loopbaan, betaalde reis of geschenk; commissiezetel
  ser            zetel in de SER
  afm            aandeelhouder ≥ 3% (substantiële deelnemingen) of bestuurder/commissaris (5:48 Wft, MAR 19) van
                 een uitgevende instelling, gekoppeld zoals afm_naar_model.Plan (eigendommen, besturen); eigen
                 aandelen tellen niet; bij de instelling alleen houders en bestuurders die zelf in het model
                 staan
  oo / ep / cbs  aanwezigheid in het register van overheidsorganisaties (organisatie of ambtsdrager),
                 het Europees Parlement (lid) en de CBS-gemeentelijke indeling

Kanalen (voor de domeinscore, alleen organisaties):
  met domein   agenda (ministerie), tk_inspraak (Kamercommissie), ep_vergadering (procedure, titel of
               commissie van het EP-lid), ser (sociale zaken en economie)
  zonder domein lobby (toegangspas), gift (partij), ep_deelname (betaalde deelname EP-lid),
               tk_geschenk (betaalde reis of geschenk aan een Kamerlid), eigendom (de organisatie meldde een
               belang van ≥ 3% in een uitgevende instelling, AFM)
Een kanaal zonder domein telt mee in elk domein waarin de organisatie via een domeinkanaal actief is.
Functies en nevenfuncties van personen bij een organisatie zijn geen kanaal van de organisatie: ze
staan bij de registers en in de sectie benoemingen.

Score per organisatie en domein D:
    kanalen(D) × log2(1 + signalen(D)) / breedte
  kanalen(D)  = domeinkanalen met een signaal in D + de kanalen zonder domein van de organisatie;
  signalen(D) = signalen van de domeinkanalen in D + 1 per kanaal zonder domein;
  breedte     = log2(1 + N), N = exp(H): het effectieve aantal domeinen (H = Shannon-entropie van de
                verdeling van de domeinsignalen; een signaal bij een tegenpartij met twee domeinen
                telt voor de helft in elk). Eén domein → N = 1, factor 1; gelijk verdeeld over acht →
                N = 8, factor 3,17. Een losse afspraak elders verschuift N nauwelijks (90/10 → 1,38).
  Waarom zo: het aantal kanalen is het kernsignaal; log2 van het volume voorkomt dat alleen volume
  telt; de breedtefactor deelt door hoe verspreid de organisatie is, zodat een koepel die bij elk
  ministerie en elke commissie zit (VNG, VNO-NCW, FNV) niet vanzelf bovenaan staat, maar niet zo
  hard dat haar sterkste domein verdwijnt. Wie effectief over vier of meer domeinen verspreid is,
  staat ook in de aparte sectie 'Breed aanwezig'.
Secties naast de rangschikking: 'Breed aanwezig'; 4 draaideur en benoemingen (persoon met een functie uit
staatscourant, rechtspraak, ep_netwerk of afm én een band met een organisatie die in lobby, agenda of
tk_inspraak staat; een vergadering, geschenk of gift is geen band); 5 geld en toegang (gevers, en AFM-houders,
met een ander kanaal); 6 gaten (≥ 3 registers, ≤ 1 goedgekeurd verband).
Overheid, partijen en media staan wel in de JSON, maar niet in de rangschikking (bij inspraak is hun
inbreng verantwoording of verslag, en de agenda- en EP-importers nemen ze niet mee).

Uitvoer: data/registers/kruisrapport.md en data/registers/kruisrapport.json. Elke regel is te
herleiden: de JSON draagt per entiteit, register en domeinkanaal de verwijzingen
'<register>/<uitgave>#<recordsleutel>' (zoals citations.page en .section).

Gebruik:
    python3 tools/registers/kruisrapport.py [--top 40]
"""
from __future__ import annotations

import argparse
import datetime
import functools
import json
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import agenda  # noqa: E402
import afm  # noqa: E402
import afm_naar_model as afmm  # noqa: E402
import agenda_naar_model as agm  # noqa: E402
import cbs  # noqa: E402
import ep  # noqa: E402
import ep_netwerk as en  # noqa: E402
import ep_netwerk_naar_model as enm  # noqa: E402
import giften  # noqa: E402
import giften_naar_model as gm  # noqa: E402
import lobby  # noqa: E402
import lobby_naar_model as lnm  # noqa: E402
import oo  # noqa: E402
import rechtspraak  # noqa: E402
import rechtspraak_naar_model as rnm  # noqa: E402
import ser  # noqa: E402
import ser_naar_model as serm  # noqa: E402
import staatscourant as sc  # noqa: E402
import staatscourant_naar_model as scm  # noqa: E402
import tk  # noqa: E402
import tk_inspraak as tki  # noqa: E402
import tk_inspraak_naar_model as tkim  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ROOT, ontleed_naam, sleutel  # noqa: E402

# tk.schrijfwijzen leest koppelingen.json bij elke aanroep; de controles roepen haar duizenden keren
# aan. Alleen in dit proces gecachet (de module zelf blijft ongewijzigd).
tk.schrijfwijzen = functools.lru_cache(maxsize=None)(tk.schrijfwijzen)
giften.schrijfwijzen = functools.lru_cache(maxsize=None)(giften.schrijfwijzen) \
    if hasattr(giften, "schrijfwijzen") else None

DB_PATH = ROOT / "data" / "propaganda_model.db"
UIT = ROOT / "data" / "registers"
TOP = 40

# ── beleidsdomeinen ─────────────────────────────────────────────────────────
DOMEINEN = {
    "landbouw": "landbouw, visserij, voedsel en natuur",
    "zorg": "zorg, welzijn en sport",
    "sociale_zaken": "sociale zaken en werk",
    "onderwijs": "onderwijs, cultuur en wetenschap",
    "defensie": "defensie",
    "financien": "financiën",
    "digitaal": "digitale zaken",
    "klimaat_energie": "klimaat en energie",
    "infrastructuur": "infrastructuur en waterstaat",
    "buitenland": "buitenlandse zaken, handel en ontwikkeling",
    "justitie": "justitie en veiligheid",
    "binnenland_wonen": "binnenlands bestuur en wonen",
    "migratie": "asiel en migratie",
    "economie": "economische zaken",
    "algemeen": "algemene zaken (geen beleidsdomein)",
}
GEEN_SCORE = {"algemeen"}   # telt niet in de domeinscore of de breedte

# Ministeries (namen zoals agenda.MINISTERIES, de Staatscourant en het register van
# overheidsorganisaties ze geven), Kamercommissies en bewindspersoontitels → domein. De sleutel is
# de naam in sleutelvorm zonder 'Ministerie van', 'Vaste commissie voor', 'Minister van/voor'.
# Een tegenpartij met twee portefeuilles telt in beide domeinen (EZK tot juli 2024).
NAAM_DOMEIN: dict[str, tuple[str, ...]] = {
    # ministeries
    "algemene zaken": ("algemeen",),
    "buitenlandse zaken": ("buitenland",),
    "buitenlandse handel en ontwikkelingssamenwerking": ("buitenland",),
    "buitenlandse handel en ontwikkelingshulp": ("buitenland",),
    "defensie": ("defensie",),
    "volksgezondheid welzijn en sport": ("zorg",),
    "medische zorg": ("zorg",), "medische zorg en sport": ("zorg",), "langdurige zorg en sport": ("zorg",),
    "jeugd preventie en sport": ("zorg",),
    "binnenlandse zaken en koninkrijksrelaties": ("binnenland_wonen",),
    "volkshuisvesting en ruimtelijke ordening": ("binnenland_wonen",),
    "economische zaken en klimaat": ("economie", "klimaat_energie"),
    "economische zaken": ("economie",),
    "klimaat en groene groei": ("klimaat_energie",),
    "klimaat en energie": ("klimaat_energie",),
    "justitie en veiligheid": ("justitie",),
    "rechtsbescherming": ("justitie",),
    "asiel en migratie": ("migratie",),
    "sociale zaken en werkgelegenheid": ("sociale_zaken",),
    "armoedebeleid participatie en pensioenen": ("sociale_zaken",),
    "financien": ("financien",),
    "onderwijs cultuur en wetenschap": ("onderwijs",),
    "primair en voortgezet onderwijs": ("onderwijs",),
    "infrastructuur en waterstaat": ("infrastructuur",),
    "landbouw visserij voedselzekerheid en natuur": ("landbouw",),
    "landbouw natuur en voedselkwaliteit": ("landbouw",),
    "natuur en stikstof": ("landbouw",),
    # Kamercommissies die geen ministerie volgen
    "binnenlandse zaken": ("binnenland_wonen",),
    "koninkrijksrelaties": ("binnenland_wonen",),
    "digitale zaken": ("digitaal",),
    "europese zaken": ("buitenland",),
    "rijksuitgaven": ("financien",),
    "verzoekschriften en de burgerinitiatieven": ("algemeen",),
    "grondrechten en constitutionele toetsing": ("binnenland_wonen",),
    "werkwijze": ("algemeen",),
}
# Commissies van het Europees Parlement (afkorting) → domein
EP_COMMISSIE_DOMEIN: dict[str, tuple[str, ...]] = {
    "AGRI": ("landbouw",), "PECH": ("landbouw",),
    "ENVI": ("klimaat_energie",), "ITRE": ("klimaat_energie", "economie"),
    "SANT": ("zorg",), "EMPL": ("sociale_zaken",),
    "CULT": ("onderwijs",), "FEMM": ("onderwijs",),   # emancipatie valt in Nederland onder OCW
    "SEDE": ("defensie",),
    "ECON": ("financien",), "FISC": ("financien",), "BUDG": ("financien",), "CONT": ("financien",),
    "IMCO": ("economie", "digitaal"),
    "TRAN": ("infrastructuur",),
    "AFET": ("buitenland",), "DROI": ("buitenland",), "INTA": ("buitenland",), "DEVE": ("buitenland",),
    "LIBE": ("justitie", "migratie"), "JURI": ("justitie",),
    "AFCO": ("binnenland_wonen",), "REGI": ("binnenland_wonen",), "HOUS": ("binnenland_wonen",),
    "EUDS": ("binnenland_wonen",),
    "PETI": ("algemeen",),
}
# Trefwoorden (sleutelvorm, Nederlands en Engels): alleen als laatste middel voor de titel van een
# EP-vergadering of een onbekende naam, en alleen als precies één domein past.
DOMEIN_WOORDEN: dict[str, str] = {
    "landbouw": r"landbouw|agricult\w*|farm\w*|boer\w*|visserij|fisher\w*|fish|voedsel\w*|food|veehouderij|livestock|"
                r"dierenwelzijn|animal welfare|pesticid\w*|gewasbescherming|stikstof|mest|glastuinbouw|cap",
    "zorg": r"zorg\w*|gezondheid\w*|health\w*|medic\w*|genees\w*|pharma\w*|patient\w*|tabak|tobacco|ziekenhui\w*",
    "sociale_zaken": r"werkgelegenheid|employment|arbeids?\w*|labou?r|pensioen\w*|pension\w*|sociale zekerheid|"
                     r"social security|uitkering\w*|armoede|poverty|minimumloon|platform work\w*",
    "onderwijs": r"onderwijs|education|school\w*|universit\w*|cultuur|culture|cultural|wetenschap\w*|erasmus",
    "defensie": r"defensie|defen[cs]e|militair\w*|military|navo|nato|krijgsmacht|wapen\w*|weapon\w*|munition\w*",
    "financien": r"financ\w*|belasting\w*|tax\w*|bank\w*|fiscal\w*|begroting\w*|budget\w*|verzeker\w*|insurance|"
                 r"betaal\w*|payment\w*|capital markets?|monetary|kapitaalmarkt\w*",
    "digitaal": r"digita\w*|data|cyber\w*|artificial intelligence|kunstmatige intelligentie|ai|telecom\w*|"
                r"algoritm\w*|chips?|semiconductor\w*",
    "klimaat_energie": r"klimaat\w*|climate|energie\w*|energy|emissi\w*|waterstof|hydrogen|renewable\w*|"
                       r"kernenergie|nuclear|ets|milieu\w*|environment\w*|circula\w*",
    "infrastructuur": r"infrastructu\w*|transport\w*|vervoer|luchtvaart|aviation|spoor\w*|rail\w*|scheepvaart|"
                      r"shipping|maritime|haven\w*|ports?|mobiliteit|mobility|automotive",
    "buitenland": r"buitenland\w*|foreign|handel\w*|trade|ontwikkelingssamenwerking|development cooperation|"
                  r"oekraine|ukraine|mercosur|sancti\w*|gaza|israel",
    "justitie": r"justitie|justice|strafrecht\w*|criminal|politie|police|rechtsstaat|rule of law|witwas\w*|"
                r"money laundering|terroris\w*",
    "binnenland_wonen": r"wonen|woning\w*|housing|huur\w*|ruimtelijke ordening|democrat\w*|verkiezing\w*|"
                        r"election\w*|grondwet",
    "migratie": r"migrat\w*|migrant\w*|asiel\w*|asylum|vreemdeling\w*|visa|visum|vluchteling\w*|refugee\w*|border\w*",
    "economie": r"econom\w*|ondernem\w*|industr\w*|concurrentie\w*|competiti\w*|single market|internal market|"
                r"interne markt|consument\w*|consumer\w*|mkb|sme|smes|innovati\w*",
}
_WOORD_RE = {d: re.compile(rf"(?<![\w])(?:{p})(?![\w])") for d, p in DOMEIN_WOORDEN.items()}
_VOORVOEGSEL = re.compile(
    r"^(?:(?:koninklijk besluit op voordracht van de|vaste commissie voor|tijdelijke commissie|commissie voor de|"
    r"commissie voor|ministerie van|minister van|minister voor|staatssecretaris van|staatssecretaris voor|"
    r"minister president|de)\s+)+")


def woord_domein(tekst: str) -> tuple[str, ...]:
    """Het ene domein waarvan een trefwoord in de tekst staat; () als geen of meer dan één."""
    s = sleutel(tekst)
    treffers = tuple(d for d, p in _WOORD_RE.items() if p.search(s))
    return treffers if len(treffers) == 1 else ()


def naam_domein(naam: str | None) -> tuple[tuple[str, ...], str]:
    """Ministerie, Kamercommissie of bewindspersoontitel → (domeinen, hoe)."""
    if not naam:
        return (), "onbepaald"
    for deel in re.split(r";", naam):
        raw = re.sub(r"\s*\([^)]*\)\s*$", "", deel.strip())
        k = _VOORVOEGSEL.sub("", sleutel(raw))
        if k in NAAM_DOMEIN:
            return NAAM_DOMEIN[k], "tabel"
    d = woord_domein(_VOORVOEGSEL.sub("", sleutel(naam)))
    return (d, "trefwoord") if d else ((), "onbepaald")


# ── kanalen ─────────────────────────────────────────────────────────────────
KANAAL = {
    "agenda": "afspraak met bewindspersoon",
    "tk_inspraak": "inbreng bij Kamercommissie",
    "ep_vergadering": "vergadering met EP-lid",
    "ser": "SER-zetel",
    "lobby": "toegangspas Tweede Kamer",
    "gift": "gift aan partij",
    "ep_deelname": "betaalde deelname EP-lid",
    "tk_geschenk": "betaalde reis of geschenk Kamerlid",
    "eigendom": "eigendom ≥ 3% (AFM)",
}
DOMEINLOOS = {"lobby", "gift", "ep_deelname", "tk_geschenk", "eigendom"}
TOEGANG = ("lobby", "agenda", "tk_inspraak")       # secties 4 en 5
OVERHEID_TYPES = {"overheidsinstelling", "rechterlijke_macht", "toezichthouder"}
MEDIA_TYPES = {"mediaorganisatie", "omroep", "persbureau"}
AFFILIATIE = {"personeel", "bestuurder", "adviseur", "lidmaatschap", "dienstverband", "draaideur",
              "woordvoerder_van", "eigendom"}
FUNCTIE_REGISTERS = ("staatscourant", "rechtspraak", "ep_netwerk", "afm")
BREED_N = 4.0


def _log2(x: float) -> float:
    return math.log2(x) if x > 0 else 0.0


def _rond(x: float, n: int = 2) -> float:
    return round(x + 0.0, n)


# ── Plannen die elk verband melden vóór ze ontdubbelen ──────────────────────
class _Log:
    """Meldt elke aanroep van _rel (één per record), vóór de ontdubbeling van tk_naar_model.Plan."""

    def _rel(self, bron, doel, rtype, mech, rec, claim, functie=None, start=None, eind=None):
        self.__dict__.setdefault("log", []).append(
            {"bron": bron, "doel": doel, "type": rtype, "rec": rec, "functie": functie,
             "start": start, "eind": eind, "persoon": self._persoon_eid(bron) or self._persoon_eid(doel)})
        return super()._rel(bron, doel, rtype, mech, rec, claim, functie=functie, start=start, eind=eind)

    def _persoon_eid(self, ref):
        return None


class LobbyPlan(_Log, lnm.Plan):
    pass


class SerPlan(_Log, serm.Plan):
    pass


class TkPlan(_Log, tkm.Plan):
    def _persoon_eid(self, ref):
        if ref[0] == "persoon":
            p = self.personen.get(ref[1]) or {}
            return ("tk", ref[1], p.get("bestaand"), p.get("naam"))
        return None


class RsPlan(_Log, rnm.Plan):
    def _persoon_eid(self, ref):
        if ref[0] == "persoon":
            p = self.personen_rs.get(ref[1]) or {}
            return ("rechtspraak", ref[1], p.get("bestaand"), p.get("naam"))
        return None


class EpPlan(enm.Plan):
    """Meldt elke aanroep van _plan (commissie, belang, deelname); de vergaderingen leest
    Kruis.ep_netwerk zelf per record, met dezelfde hulpfuncties als Plan.vergaderingen."""

    def _plan(self, bron, doel, rtype, mech, rec, claim, **kw):
        if kw.get("soort") != "vergadering":
            self.__dict__.setdefault("log", []).append(
                {"bron": bron, "doel": doel, "type": rtype, "rec": rec, "soort": kw.get("soort"),
                 "naam_bron": self._naam(bron), "naam_doel": self._naam(doel)})
        return super()._plan(bron, doel, rtype, mech, rec, claim, **kw)


# ── het kruisrapport ────────────────────────────────────────────────────────
class Kruis:
    def __init__(self, conn: sqlite3.Connection, koppelingen: dict, log=print):
        self.conn, self.k, self.log = conn, koppelingen, log
        self.ent: dict[int, dict] = {}
        for i, n, t, st, laag, rol in conn.execute("""
                SELECT e.id, e.name, e.type, e.status, e.bestuurslaag, r.name FROM entities e
                LEFT JOIN roles r ON r.id = e.primary_role_id
                WHERE NOT e.vervangen AND e.status <> 'afgewezen'"""):
            self.ent[i] = {"naam": n, "type": t, "status": st, "bestuurslaag": laag, "rol": rol}
        self.ext: dict[int, set] = defaultdict(set)
        self.ext_rev: dict[tuple[str, str], int] = {}
        for eid, st, w in conn.execute("SELECT entity_id, stelsel, waarde FROM externe_ids"):
            self.ext[eid].add((st, w))
            self.ext_rev[(st, w)] = eid
        # het model: goedgekeurde verbanden per type, voorgestelde, paren en banden
        self.rel_goed: dict[int, Counter] = defaultdict(Counter)
        self.rel_voor: Counter = Counter()
        self.goed_paren: set[tuple[int, int]] = set()
        self.paar_rel: dict[tuple[int, int], list[tuple]] = defaultdict(list)
        self.banden: dict[int, list[dict]] = defaultdict(list)
        for rid, s, t, typ, st, functie, van, tot in conn.execute("""
                SELECT id, source_id, target_id, relation_type, status, functie, active_from, active_until
                FROM relations WHERE NOT vervangen AND status <> 'afgewezen'"""):
            paar = (min(s, t), max(s, t))
            self.paar_rel[paar].append((rid, typ, st))
            if st == "goedgekeurd":
                self.rel_goed[s][typ] += 1
                if t != s:
                    self.rel_goed[t][typ] += 1
                self.goed_paren.add(paar)
                if typ in AFFILIATIE:
                    for p, o in ((s, t), (t, s)):
                        if self.ent.get(p, {}).get("type") == "persoon" and self.ent.get(o, {}).get("type") != "persoon":
                            self.banden[p].append({"relation_id": rid, "org": o, "type": typ, "functie": functie,
                                                   "van": van, "tot": tot})
            else:
                self.rel_voor[s] += 1
                self.rel_voor[t] += 1
        self.sig: dict[int, list[dict]] = defaultdict(list)
        self._gezien: set[tuple] = set()
        self.dekking: dict[str, Counter] = defaultdict(Counter)
        self.uitgaven: dict[str, set[str]] = defaultdict(set)
        self.giftbedrag: dict[int, dict[str, dict[str, float]]] = defaultdict(dict)
        self.eigendom: dict[int, list[dict]] = defaultdict(list)
        self.genoemd_index = self._persoonsnamen()

    # ── hulp ──────────────────────────────────────────────────────────────
    def eindpunt(self, eid: int | None, naam: str | None = None, typ: str | None = None, ids=()) -> dict:
        if eid and eid in self.ent:
            e = self.ent[eid]
            return {"id": eid, "name": e["naam"], "type": e["type"], "ids": set(self.ext.get(eid, ())) | set(ids)}
        return {"id": eid, "name": naam, "type": typ, "ids": set(ids)}

    def publiek(self, eid: int | None) -> bool:
        """In het model, en een persoon alleen als hij goedgekeurd is (privacy: geen voorstel)."""
        e = self.ent.get(eid) if eid else None
        return bool(e) and (e["type"] != "persoon" or e["status"] == "goedgekeurd")

    def naam(self, eid: int | None, anders: str) -> str:
        """Naam van een tegenpartij; een persoon die niet (goedgekeurd) in het model staat, nooit."""
        return self.ent[eid]["naam"] if self.publiek(eid) else anders

    def org_soort(self, eid: int) -> str:
        e = self.ent[eid]
        if e["type"] == "persoon":
            return "persoon"
        if e["type"] in OVERHEID_TYPES or e["bestuurslaag"]:
            return "overheid"
        if e["type"] == "partij":
            return "partij"
        if e["type"] in MEDIA_TYPES:
            return "media"
        return "maatschappelijk"

    def keur(self, register: str, reden: str | None) -> bool:
        if reden:
            self.dekking[register]["registercheck zou afkeuren (niet meegeteld)"] += 1
            return False
        return True

    def voeg(self, eid: int | None, register: str, uitgave: str, sleutel_r: str, *, soort: str,
             kanaal: str | None = None, datum: str | None = None, stand: str | None = None,
             tegen: str | None = None, tegen_id: int | None = None, domeinen=(), domein_via: str | None = None,
             bedrag: float | None = None, detail: str | None = None, org_id: int | None = None,
             functie: str | None = None, tot: str | None = None) -> bool:
        if not eid or eid not in self.ent:
            self.dekking[register]["niet in het model (niet opgenomen)"] += 1
            return False
        if not self.publiek(eid):
            self.dekking[register]["persoon niet goedgekeurd in het model (niet opgenomen)"] += 1
            return False
        ref = f"{register}/{uitgave}#{sleutel_r}"
        k = (eid, ref, soort, tegen_id or tegen, kanaal)
        if k in self._gezien:
            return False
        self._gezien.add(k)
        s = {"register": register, "kanaal": kanaal, "soort": soort, "ref": ref, "datum": datum or None,
             "tegenpartij": tegen, "tegenpartij_id": tegen_id if self.publiek(tegen_id) else None,
             "domeinen": list(domeinen), "domein_via": domein_via if domeinen else None}
        for veld, w in (("stand", stand), ("tot", tot), ("bedrag", bedrag), ("detail", detail),
                        ("organisatie_id", org_id if self.publiek(org_id) else None), ("functie", functie)):
            if w is not None:
                s[veld] = w
        self.sig[eid].append(s)
        self.uitgaven[register].add(uitgave)
        self.dekking[register]["signalen"] += 1
        return True

    def _persoonsnamen(self) -> dict[str, list[tuple[list[str], int]]]:
        """Volledige namen (voornaam + achternaam, uniek in het model) van goedgekeurde personen, om
        ze in een afspraak of genodigdenregel terug te vinden naast hun organisatie."""
        tel: Counter = Counter()
        kandidaat: dict[str, int] = {}
        for eid, e in self.ent.items():
            if e["type"] != "persoon":
                continue
            kaal = tkm.zonder_haakjes(e["naam"])
            n = ontleed_naam(kaal)
            k = sleutel(kaal)
            tel[k] += 1
            if e["status"] == "goedgekeurd" and n["volledig"] and len(k.split()) >= 2:
                kandidaat[k] = eid
        index: dict[str, list[tuple[list[str], int]]] = defaultdict(list)
        for k, eid in kandidaat.items():
            if tel[k] == 1:
                index[k.split()[0]].append((k.split(), eid))
        return index

    def genoemd(self, tekst: str, org: int) -> list[int]:
        """Personen met hun volledige naam in de tekst die een goedgekeurd verband met de organisatie
        uit hetzelfde record hebben (volledige naam + passende rol, README § Regels)."""
        woorden = sleutel(tekst).split()
        uit = []
        for i, w in enumerate(woorden):
            for kw, pid in self.genoemd_index.get(w, ()):
                if woorden[i:i + len(kw)] == kw and (min(pid, org), max(pid, org)) in self.goed_paren:
                    uit.append(pid)
        return uit

    # ── registers ─────────────────────────────────────────────────────────
    def lobby(self):
        u = lobby.uitgaven()[-1].stem.split("_", 1)[1]
        data = lobby.lees_uitgave(u)
        lp = LobbyPlan(data, self.conn, self.k).maak()
        self.dekking["lobby"]["records"] = len(data["records"])
        for r in getattr(lp, "log", []):
            if r["bron"][0] != "bestaand":
                continue
            eid, rec = r["bron"][1], r["rec"]
            if not self.keur("lobby", lobby.controleer(data, rec["sleutel"], rec, "lobbyt",
                                                       [self.eindpunt(eid), self.eindpunt(lp.tweede_kamer)])):
                continue
            eigen = not (r["functie"] or "").startswith("Via ")
            self.voeg(eid, "lobby", u, rec["sleutel"], kanaal="lobby", stand=u,
                      soort="eigen toegangspas" if eigen else "opdrachtgever van een pashouder",
                      tegen="Tweede Kamer", tegen_id=lp.tweede_kamer,
                      detail=None if eigen else f"via {rec['werkzaam']}")

    def agenda(self):
        records = agm.alle_records()
        ap = agm.Plan(records, self.conn, self.k).maak()
        self.dekking["agenda"]["records"] = len(records)
        for (eid, mid), recs in ap.paren.items():
            for rec in recs:
                data = agenda.lees_uitgave(rec["_uitgave"])
                if not self.keur("agenda", agenda.controleer(data, rec["sleutel"], rec, "lobbyt",
                                                             [self.eindpunt(eid), self.eindpunt(mid)])):
                    continue
                dom, via = naam_domein(rec["ministeries"][0])
                wie = f"{rec['functie']} {rec['bewindspersoon']}"
                self.voeg(eid, "agenda", rec["_uitgave"], rec["sleutel"], kanaal="agenda", soort=rec["type"].lower(),
                          datum=rec["datum"], tegen=self.naam(mid, "ministerie"), tegen_id=mid,
                          domeinen=dom, domein_via=f"ministerie ({via})", detail=wie)
                for pid in self.genoemd(rec["tekst"], eid):
                    self.voeg(pid, "agenda", rec["_uitgave"], rec["sleutel"], soort="genoemd bij een afspraak",
                              datum=rec["datum"], tegen=self.naam(mid, "ministerie"), tegen_id=mid,
                              domeinen=dom, domein_via=f"ministerie ({via})", org_id=eid,
                              detail=f"namens {self.ent[eid]['naam']}; {wie}")

    def tk_inspraak(self):
        u = tki.uitgaven()[-1].stem.split("_")[-1]
        data = tki.lees_uitgave(u)
        ip = tkim.Plan(data, self.conn, self.k).maak()
        self.dekking["tk_inspraak"]["records"] = len(data["records"])
        for (eid, naam_c), lijst in ip.optredens.items():
            cid = ip.op_naam_type.get((naam_c, "overheidsinstelling"))
            dom, via = naam_domein(naam_c)
            rtype = ip.mechanisme(eid)[0] or "lobbyt"
            for x in lijst:
                rec = x["rec"]
                doel = self.eindpunt(cid) if cid else {"id": None, "name": naam_c, "type": "overheidsinstelling",
                                                        "ids": set()}
                reden = tki.controleer(data, rec["sleutel"], rec, rtype, [self.eindpunt(eid), doel])
                if reden and "eigen titel" in reden:
                    self.dekking["tk_inspraak"]["optreden op eigen titel (persoonsroute, geen kanaal)"] += 1
                    continue
                if not self.keur("tk_inspraak", reden):
                    continue
                soort = {"positionpaper": "position paper", "genodigde": "genodigde",
                         "tegenpartij": "tegenpartij"}[rec["soort"]]
                act = (rec.get("activiteit_soort") or "").lower()
                self.voeg(eid, "tk_inspraak", u, rec["sleutel"], kanaal="tk_inspraak", soort=soort,
                          datum=rec.get("datum"), tegen=naam_c.replace(" (Tweede Kamer)", ""), tegen_id=cid,
                          domeinen=dom, domein_via=f"commissie ({via})", detail=act or None)
                if rec["soort"] == "genodigde":
                    for pid in self.genoemd(rec.get("wie") or "", eid):
                        self.voeg(pid, "tk_inspraak", u, rec["sleutel"], soort="genodigde namens een organisatie",
                                  datum=rec.get("datum"), tegen=naam_c.replace(" (Tweede Kamer)", ""), tegen_id=cid,
                                  domeinen=dom, domein_via=f"commissie ({via})", org_id=eid,
                                  detail=f"namens {self.ent[eid]['naam']}; {act}")

    def ep_netwerk(self):
        u = en.uitgaven()[-1].stem.rsplit("_", 1)[1]
        data = en.lees_uitgave(u)
        epp = EpPlan(data, self.conn, self.k).maak()
        self.dekking["ep_netwerk"]["records"] = len(data["records"])
        recs = data["records"]
        # commissies per procedure (verklaringen van (schaduw)rapporteurs) en per lid (volle zetels)
        proc_comm: dict[str, set[str]] = defaultdict(set)
        lid_comm: dict[str, set[str]] = defaultdict(set)
        for r in recs.values():
            if r["soort"] == "rapporteur" and r.get("procedure_sleutel") and r.get("commissie"):
                proc_comm[r["procedure_sleutel"]].add(r["commissie"])
            if r["soort"] == "commissie" and r.get("rol") in ("Lid", "Voorzitter", "Vicevoorzitter") and r.get("afkorting"):
                lid_comm[r["persoon_id"]].add(r["afkorting"])

        def lid_ep(pid_ep):
            return self.eindpunt(epp.ext_ep.get(pid_ep), ids={("ep_mep", pid_ep)})

        # commissiezetels, belangen en deelnames: zoals het Plan ze koppelde
        for r in getattr(epp, "log", []):
            rec, soort = r["rec"], r["soort"]
            lid = r["bron"] if soort != "deelname" else r["doel"]
            ander = r["doel"] if soort != "deelname" else r["bron"]
            lid_id = lid[1] if lid[0] == "bestaand" else None
            ander_id = ander[1] if ander[0] == "bestaand" and ander[1] > 0 else None
            ander_naam = r["naam_doel"] if soort != "deelname" else r["naam_bron"]
            ander_e = self.eindpunt(ander_id, naam=ander_naam, typ="overheidsinstelling" if soort == "commissie" else None)
            eind = [lid_ep(rec["persoon_id"]), ander_e] if soort != "deelname" else [ander_e, lid_ep(rec["persoon_id"])]
            if not self.keur("ep_netwerk", en.controleer(data, rec["sleutel"], rec, r["type"], eind)):
                continue
            lidnaam = self.naam(lid_id, "EP-lid")
            if soort == "commissie":
                dom = EP_COMMISSIE_DOMEIN.get(rec.get("afkorting") or "", ())
                self.voeg(lid_id, "ep_netwerk", u, rec["sleutel"], soort=f"commissiezetel ({rec['rol'].lower()})",
                          datum=rec.get("van"), tegen=ander_naam.replace(" (Europees Parlement)", f" ({rec.get('afkorting')})"),
                          tegen_id=ander_id, domeinen=dom, domein_via="EP-commissie", functie=rec["rol"])
            elif soort in ("nevenfunctie", "loopbaan"):
                van, tot = enm._jaar_maand(rec["tekst"])
                wat = "functie vóór het mandaat (rubriek A)" if rec["rubriek"] == "A" else f"belang rubriek {rec['rubriek']}"
                self.voeg(lid_id, "ep_netwerk", u, rec["sleutel"], soort=wat, datum=van, tot=tot, tegen=ander_naam,
                          tegen_id=ander_id, functie=rec["tekst"][:200])
                self.voeg(ander_id, "ep_netwerk", u, rec["sleutel"], soort=f"EP-lid vermeldt {wat}", datum=van, tot=tot,
                          tegen=lidnaam, tegen_id=lid_id)
            elif soort == "deelname":
                self.voeg(ander_id, "ep_netwerk", u, rec["sleutel"], kanaal="ep_deelname",
                          soort="betaalde deelname van een EP-lid", datum=rec.get("van"), tegen=lidnaam, tegen_id=lid_id)
                self.voeg(lid_id, "ep_netwerk", u, rec["sleutel"], soort="deelname betaald door", datum=rec.get("van"),
                          tegen=ander_naam, tegen_id=ander_id)
        # vergaderingen: per record, met de hulpfuncties van ep_netwerk_naar_model.Plan.vergaderingen
        epp.tel.clear()
        paren: Counter = Counter()
        for rec in recs.values():
            if rec["soort"] != "vergadering" or rec["persoon_id"] not in epp.ext_ep:
                continue
            kand = [rec["aanwezig"]] + list(rec.get("tr_namen") or [])
            gevonden = None
            for k in kand:
                k = epp._schoon_naam(k)
                if len(sleutel(k)) >= 3:
                    gevonden = epp._bestaand(k, ruim=True)
                    if gevonden:
                        break
            if not gevonden or epp._alleen_afkorting(gevonden[0], kand) or \
                    epp._uitgesloten_org(gevonden[0], "vergadering"):
                continue
            o, lid_id = gevonden[0], epp.ext_ep[rec["persoon_id"]]
            paren[(o, rec["persoon_id"])] += 1
            if o < 0 or not self.keur("ep_netwerk", en.controleer(
                    data, rec["sleutel"], rec, "lobbyt", [self.eindpunt(o), lid_ep(rec["persoon_id"])])):
                continue
            ps = en.procedure_sleutel(rec.get("procedure"))
            dom, via = (), None
            if ps and len(proc_comm.get(ps, ())) == 1:
                dom, via = EP_COMMISSIE_DOMEIN.get(next(iter(proc_comm[ps])), ()), f"procedure ({next(iter(proc_comm[ps]))})"
            if not dom:
                dom, via = woord_domein(rec.get("titel") or ""), "titel (trefwoord)"
            if not dom and len(lid_comm.get(rec["persoon_id"], ())) == 1:
                afk = next(iter(lid_comm[rec["persoon_id"]]))
                dom, via = EP_COMMISSIE_DOMEIN.get(afk, ()), f"commissie van het EP-lid ({afk})"
            lidnaam = self.naam(lid_id, "EP-lid")
            self.voeg(o, "ep_netwerk", u, rec["sleutel"], kanaal="ep_vergadering", soort="vergadering",
                      datum=rec["datum"], tegen=lidnaam, tegen_id=lid_id, domeinen=dom, domein_via=via,
                      detail=rec.get("hoedanigheid"))
            self.voeg(lid_id, "ep_netwerk", u, rec["sleutel"], soort="vergadering met een organisatie", datum=rec["datum"],
                      tegen=self.ent[o]["naam"] if o in self.ent else None, tegen_id=o, domeinen=dom, domein_via=via)
        # zelfcontrole: dezelfde paren als het Plan (analyse) telde
        verwacht = Counter({(a["org_id"], a["lid_id"]): a["vergaderingen"] for a in epp.analyse})
        if verwacht != paren:
            self.log(f"! ep_netwerk: vergaderingen wijken af van het Plan ({sum(paren.values())} tegen "
                     f"{sum(verwacht.values())})")
            self.dekking["ep_netwerk"]["afwijking van het Plan (vergaderingen)"] += 1

    def giften(self):
        data = gm.lees_alle()
        gp = gm.Plan(data, self.conn, self.k)
        gp.signalen()
        gp.maak()
        self.dekking["giften"]["records"] = sum(len(d["records"]) for d in data.values())
        for (ref, pid), recs in gp.gift_paren.items():
            if ref[0] != "bestaand":
                continue
            eid, partij = ref[1], gp.org[pid][0]
            goed = []
            for rec in recs:
                if not self.keur("giften", giften.controleer(data[rec["_uitgave"]], rec["sleutel"], rec, "donor",
                                                             [self.eindpunt(eid), self.eindpunt(pid)])):
                    continue
                if self.voeg(eid, "giften", rec["_uitgave"], rec["sleutel"], kanaal="gift", soort="gift aan partij",
                             datum=rec.get("laatste") or rec.get("eerste") or rec.get("jaar"), tegen=partij,
                             tegen_id=pid, bedrag=rec.get("totaal")):
                    goed.append(rec)
            if goed:
                self.giftbedrag[eid][partij] = gm.jaartotalen(goed)

    def staatscourant(self):
        records = scm.alle_records()
        sp = scm.Plan(records, self.conn, self.k).maak()
        self.dekking["staatscourant"]["records"] = len(records)
        for kd in sp.kandidaten:
            rec = sp.records[kd["sleutel"]]
            pid, oid = kd["persoon_id"], kd["org_id"]
            if not (pid or oid):
                continue
            if oid:
                pe = self.eindpunt(pid) if pid else {"id": None, "name": rec.get("weergave") or rec["persoon"],
                                                     "type": "persoon", "ids": set()}
                rtype = sp._rtype(rec, ("bestaand", oid))
                if not self.keur("staatscourant", sc.controleer({}, rec["sleutel"], rec, rtype, [pe, self.eindpunt(oid)])):
                    continue
            benoemer = rec.get("ministerie") or rec.get("benoemer") or ("Kroon" if rec.get("kb") else None)
            dom, via = naam_domein(rec.get("ministerie") or rec.get("benoemer"))
            org_naam = self.naam(oid, rec.get("oo_naam") or rec["organisatie"] or "?") if oid else \
                (rec.get("oo_naam") or rec["organisatie"])
            datum = rec.get("van") or rec.get("publicatiedatum")
            cat = kd.get("categorie")
            self.voeg(pid, "staatscourant", rec["_uitgave"], rec["sleutel"], soort=rec["soort"], datum=datum,
                      tot=rec.get("tot"), tegen=benoemer, domeinen=dom, domein_via=f"benoemer ({via})", org_id=oid,
                      functie=f"{rec['functie']} {org_naam}"[:200], detail=cat)
            self.voeg(oid, "staatscourant", rec["_uitgave"], rec["sleutel"], soort=f"{rec['soort']} bij de organisatie",
                      datum=datum, tot=rec.get("tot"), tegen=benoemer, domeinen=dom, domein_via=f"benoemer ({via})",
                      functie=rec["functie"][:120],
                      detail=(f"{self.ent[pid]['naam']}; " if self.publiek(pid) else "") + (cat or ""))

    def rechtspraak(self):
        u = rechtspraak.uitgaven()[-1].stem.split("_", 1)[1]
        data = rechtspraak.lees_uitgave(u)
        rp = RsPlan(data, self.conn, self.k).maak()
        self.dekking["rechtspraak"]["records"] = len(data["records"])
        for r in getattr(rp, "log", []):
            _reg, rs_id, rechter, plannaam = r["persoon"]
            rec, doel = r["rec"], r["doel"]
            oid = doel[1] if doel[0] == "bestaand" and doel[1] > 0 else None
            if not oid:
                continue   # een nieuwe organisatie staat nog niet in het model
            re_e = self.eindpunt(rechter, naam=plannaam, typ="persoon", ids={("rechtspraak", rs_id)})
            if not self.keur("rechtspraak", rechtspraak.controleer(data, rec["sleutel"], rec, r["type"],
                                                                   [re_e, self.eindpunt(oid)])):
                continue
            wat = "nevenbetrekking" if rec["soort"] == "nevenfunctie" else "functie buiten de rechtspraak"
            gerecht = "; ".join(dict.fromkeys(f"{a}, {b}" for a, b, _ in rec.get("functies") or []))
            self.voeg(rechter, "rechtspraak", u, rec["sleutel"], soort=wat, datum=rec.get("van"), tot=rec.get("tot"),
                      tegen=self.ent[oid]["naam"], tegen_id=oid, functie=(rec.get("functie") or "")[:200],
                      detail=gerecht[:200] or None)
            self.voeg(oid, "rechtspraak", u, rec["sleutel"], soort=f"rechter met {wat}", datum=rec.get("van"),
                      tot=rec.get("tot"), tegen=self.naam(rechter, "rechter (niet in het model)"), tegen_id=rechter,
                      functie=(rec.get("functie") or "")[:120])

    def tk(self):
        u = tk.uitgaven()[-1].stem.split("_", 1)[1]
        data = tk.lees_uitgave(u)
        tp = TkPlan(data, self.conn, self.k).maak()
        self.dekking["tk"]["records"] = len(data["records"])
        for r in getattr(tp, "log", []):
            if not r["persoon"]:
                continue
            _reg, tk_id, kamerlid, plannaam = r["persoon"]
            rec = r["rec"]
            ander = r["doel"] if r["bron"][0] == "persoon" else r["bron"]
            if ander[0] == "bestaand":
                aid, anaam = ander[1], self.ent.get(ander[1], {}).get("naam")
            elif ander[0] == "nieuw":
                aid, anaam = None, tp.nieuwe_orgs[ander[1]]["naam"]
            else:
                continue
            ae = self.eindpunt(aid, naam=anaam, typ="overheidsinstelling" if rec["soort"] == "commissiezetel" else None)
            pe = self.eindpunt(kamerlid, naam=plannaam, typ="persoon", ids={("tk_persoon", tk_id)})
            if not self.keur("tk", tk.controleer(data, rec["sleutel"], rec, r["type"], [pe, ae])):
                continue
            soort = rec["soort"]
            dom, via = (naam_domein(anaam) if soort == "commissiezetel" else ((), None))
            wat = {"kamerlid": "Kamerlid" if r["type"] == "ambt" else "fractie", "commissiezetel": "commissiezetel",
                   "nevenfunctie": "nevenfunctie", "loopbaan": "eerdere functie", "reis": "reis betaald door",
                   "geschenk": "geschenk van"}[soort]
            self.voeg(kamerlid, "tk", u, rec["sleutel"], soort=wat, datum=r["start"], tot=r["eind"],
                      tegen=anaam, tegen_id=aid, domeinen=dom, domein_via=f"commissie ({via})" if dom else None,
                      functie=(r["functie"] or "")[:200] or None)
            if aid and self.ent.get(aid, {}).get("type") not in ("partij", "persoon") and soort in (
                    "nevenfunctie", "loopbaan", "reis", "geschenk") and aid != tp.tweede_kamer:
                kanaal = "tk_geschenk" if soort in ("reis", "geschenk") else None
                owat = {"nevenfunctie": "Kamerlid met nevenfunctie", "loopbaan": "Kamerlid met eerdere functie",
                        "reis": "betaalde reis van een Kamerlid", "geschenk": "geschenk aan een Kamerlid"}[soort]
                self.voeg(aid, "tk", u, rec["sleutel"], kanaal=kanaal, soort=owat, datum=r["start"], tot=r["eind"],
                          tegen=self.naam(kamerlid, "Kamerlid"), tegen_id=kamerlid,
                          functie=(r["functie"] or "")[:120] or None)

    def ser(self):
        u = ser.uitgaven()[-1].stem.split("_", 1)[1]
        data = ser.lees_uitgave(u)
        sp = SerPlan(data, self.conn, self.k).maak()
        self.dekking["ser"]["records"] = len(data["records"])
        for r in getattr(sp, "log", []):
            if r["bron"][0] != "bestaand":
                continue
            eid, rec = r["bron"][1], r["rec"]
            if not self.keur("ser", ser.controleer(data, rec["sleutel"], rec, "lidmaatschap",
                                                   [self.eindpunt(eid), self.eindpunt(sp.ser_id)])):
                continue
            self.voeg(eid, "ser", u, rec["sleutel"], kanaal="ser", soort="SER-zetel", stand=u, tegen="SER",
                      tegen_id=sp.ser_id, domeinen=("sociale_zaken", "economie"), domein_via="SER", detail=r["functie"])

    def afm(self):
        """AFM: eigendom (sd) per paar houder–instelling zoals afm_naar_model.Plan.eigendommen het
        koppelde (analyse), bestuur (bc, mar) per persoon en instelling zoals Plan.besturen."""
        u = afm.uitgaven()[-1].stem.split("_", 1)[1]
        data = afm.lees_uitgave(u)
        ap = afmm.Plan(data, self.conn, self.k).maak()
        recs = data["records"]
        self.dekking["afm"]["records"] = len(recs)
        per_paar: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for r in recs.values():
            if r["register"] == "sd":
                per_paar[(sleutel(r["meldingsplichtige"]), sleutel(r["uitgevende_instelling"]))].append(r)
        for a in ap.analyse:
            hid = a["houder_id"] if a["houder_id"] in self.ent else None
            iid = a["instelling_id"] if a["instelling_id"] in self.ent else None
            if not (hid or iid):
                self.dekking["afm"]["paren houder–instelling buiten het model (niet opgenomen)"] += 1
                continue
            if hid and hid == iid:
                self.dekking["afm"]["paren met eigen aandelen (niet meegeteld)"] += 1
                continue
            persoon = a["natuurlijk_persoon"] or (hid and self.ent[hid]["type"] == "persoon")
            houder = self.naam(hid, "natuurlijk persoon (niet in het model)" if persoon else a["houder"]) if hid else \
                ("natuurlijk persoon (niet in het model)" if persoon else a["houder"])
            inst = self.ent[iid]["naam"] if iid else a["instelling"]
            he = self.eindpunt(hid) if hid else {"id": None, "name": a["houder"], "type": "persoon" if persoon else "bedrijf",
                                                 "ids": set()}
            ie = self.eindpunt(iid) if iid else {"id": None, "name": a["instelling"], "type": "bedrijf", "ids": set()}
            mech = {"strategische_zeggenschap": "strategisch", "systemisch_eigenaarschap": "gespreid",
                    "certificaatconstructie": "administratiekantoor"}.get(a["mechanisme"], a["mechanisme"])
            refs = []
            for r in per_paar[(sleutel(a["houder"]), sleutel(a["instelling"]))]:
                if not self.keur("afm", afm.controleer(data, r["sleutel"], r, "eigendom", [he, ie])):
                    continue
                pct = f"kapitaal {r['kapitaal']['totaal']}, stemrecht {r['stemrecht']['totaal']}"
                if hid and self.voeg(hid, "afm", u, r["sleutel"], kanaal=None if persoon else "eigendom",
                                     soort="aandeelhouder (melding ≥ 3%)", datum=r["datum"], tegen=inst, tegen_id=iid,
                                     detail=f"{pct}; {mech}", org_id=iid):
                    refs.append(f"afm/{u}#{r['sleutel']}")
                # bij de instelling alleen houders die zelf in het model staan (anders telt elke indexbelegger mee)
                if iid and self.publiek(hid):
                    self.voeg(iid, "afm", u, r["sleutel"], soort="melding van een aandeelhouder", datum=r["datum"],
                              tegen=houder, tegen_id=hid, detail=f"{pct}; {mech}")
            if hid and refs and not persoon:
                self.eigendom[hid].append({
                    "instelling": inst, "instelling_id": iid if self.publiek(iid) else None,
                    "hoogste_reeel_pct": a["max_reeel"], "laatste_totaal_pct": a["laatste_totaal"],
                    "kapitaal_reeel_pct": a["kap_reeel"], "stemrecht_reeel_pct": a["stem_reeel"],
                    "eerste_melding": min(recs[x.split("#", 1)[1]]["datum"] for x in refs),
                    "laatste_melding": a["laatste_melding"], "einde": a["einde"], "soort": mech,
                    "meldingen": len(refs), "refs": sorted(refs)})
        groepen: dict[tuple[str, int], list[dict]] = defaultdict(list)
        for r in recs.values():
            if r["register"] not in ("bc", "mar") or not r.get("achternaam") or \
                    not re.sub(r"[^a-z]", "", sleutel(r.get("voorletters") or "")):
                continue
            if r["register"] == "mar" and not afm.is_bestuursfunctie(r["functie"], r["uitgevende_instelling"]):
                continue
            inst_id, _hoe = ap.koppel_org(r["uitgevende_instelling"], "ondernemingen", [("lei", r.get("lei") or "")])
            if inst_id and inst_id in self.ent and ap.org[inst_id][1] in afmm.INSTELLING_TYPES:
                groepen[(afm.persoonsleutel(r), inst_id)].append(r)
        gekoppeld = {(b["persoonsleutel"], b["instelling_id"]): b["persoon_id"] for b in ap.bestuur_analyse}
        for (pk, inst), lijst in groepen.items():
            pid = gekoppeld.get((pk, inst))
            pid = pid if pid in self.ent else None
            if not self.publiek(pid):
                self.dekking["afm"]["bestuursmeldingen van personen buiten het model of niet goedgekeurd (niet opgenomen)"] += len(lijst)
                continue
            pe = self.eindpunt(pid) if pid else {"id": None, "name": afmm.afm_persoonsnaam(lijst[-1]), "type": "persoon",
                                                 "ids": set()}
            for r in lijst:
                if not self.keur("afm", afm.controleer(data, r["sleutel"], r, "bestuurder", [pe, self.eindpunt(inst)])):
                    continue
                wat = "bestuurder of commissaris (MAR 19)" if r["register"] == "mar" else "bestuurder of commissaris (5:48 Wft)"
                self.voeg(pid, "afm", u, r["sleutel"], soort=wat, datum=r["datum"], tegen=self.ent[inst]["naam"],
                          tegen_id=inst, functie=(r.get("functie") or None), org_id=inst)
                self.voeg(inst, "afm", u, r["sleutel"], soort=f"melding: {wat}", datum=r["datum"],
                          tegen=self.naam(pid, "bestuurder of commissaris (niet in het model)"), tegen_id=pid,
                          functie=(r.get("functie") or None))

    def aanwezigheid(self):
        """Register van overheidsorganisaties, Europees Parlement en CBS: via de externe id."""
        u = oo.uitgaven()[-1].stem.split("_", 1)[1]
        od = oo.lees_uitgave(u)
        self.dekking["oo"]["records"] = len(od["organisaties"]) + len(od["functies"])
        per_mw: dict[str, list[dict]] = defaultdict(list)
        for k, f in od["functies"].items():
            per_mw[k.rsplit(":", 1)[-1]].append(f)
        orgs = od["organisaties"]
        for eid, ids in self.ext.items():
            for st, w in ids:
                if st != "oo":
                    continue
                if w.startswith("m:"):
                    for f in per_mw.get(w[2:], []):
                        o = orgs.get(f["oo_id"]) or {}
                        dom, via = naam_domein(o.get("ministerie_naam") or f["org_naam"])
                        self.voeg(eid, "oo", u, f["sleutel"], soort="ambt", datum=f.get("start"), tot=f.get("eind"),
                                  tegen=f["org_naam"], tegen_id=self.ext_rev.get(("oo", f["oo_id"])),
                                  domeinen=dom, domein_via=f"ministerie ({via})", functie=f["functie"])
                elif w in orgs:
                    o = orgs[w]
                    dom, via = naam_domein(o.get("ministerie_naam") or o["naam"])
                    self.voeg(eid, "oo", u, f"org:{w}", soort=f"overheidsorganisatie ({', '.join(o['types'])})",
                              datum=o.get("start"), tot=o.get("eind"), stand=u,
                              tegen=o.get("ministerie_naam") or o.get("ouder_naam"),
                              tegen_id=self.ext_rev.get(("oo", o.get("ministerie_oo") or "")),
                              domeinen=dom, domein_via=f"ministerie ({via})")
        u = ep.uitgaven()[-1].stem.split("_", 1)[1]
        ed = ep.lees_uitgave(u)
        self.dekking["ep"]["records"] = len(ed["records"])
        for eid, ids in self.ext.items():
            for st, w in ids:
                if st == "ep_mep" and f"persoon:{w}" in ed["records"]:
                    self.voeg(eid, "ep", u, f"persoon:{w}", soort="Europarlementariër", stand=u,
                              tegen="Europees Parlement", tegen_id=self.ext_rev.get(("wikidata", "Q8889")))
        u = cbs.uitgaven()[-1].stem.split("_", 1)[1]
        cd = cbs.lees_uitgave(u)
        self.dekking["cbs"]["records"] = len(cd["records"])
        hand = {k.lower(): v for k, v in self.k.get("cbs_gemeenten", {}).items() if not k.startswith("_")}
        for s, rec in cd["records"].items():
            code = rec["gemeentecode"].lower()
            gid = self.ext_rev.get(("tooi", code)) or (self.ext_rev.get(("oo", str(hand[code]))) if code in hand else None)
            pid = self.ext_rev.get(("oo", cbs.PROVINCIES.get(rec["provinciecode"], ("", ""))[1]))
            self.voeg(gid, "cbs", u, s, soort="gemeente in de indeling", stand=u, tegen=rec["provincie"], tegen_id=pid)
            self.voeg(pid, "cbs", u, s, soort="provincie van een gemeente", stand=u, tegen=rec["gemeente"], tegen_id=gid)

    def lees(self):
        for stap in (self.lobby, self.agenda, self.tk_inspraak, self.ep_netwerk, self.giften, self.staatscourant,
                     self.rechtspraak, self.tk, self.ser, self.afm, self.aanwezigheid):
            self.log(f"  {stap.__name__} …")
            stap()
        return self


# ── samenvatten ─────────────────────────────────────────────────────────────
def _periode(signalen: list[dict]) -> list:
    datums = sorted(d for s in signalen for d in (s.get("datum"), s.get("tot")) if d)
    standen = sorted({s["stand"] for s in signalen if s.get("stand")})
    return [datums[0] if datums else None, datums[-1] if datums else None, standen[-1] if standen else None]


def _tegenpartijen(signalen: list[dict], n: int = 8) -> list[dict]:
    c = Counter((s.get("tegenpartij"), s.get("tegenpartij_id")) for s in signalen if s.get("tegenpartij"))
    return [{"naam": k[0], "id": k[1], "aantal": v} for k, v in c.most_common(n)]


def register_overzicht(kr: Kruis, eid: int) -> dict:
    per: dict[str, list[dict]] = defaultdict(list)
    for s in kr.sig[eid]:
        per[s["register"]].append(s)
    uit = {}
    for reg, lijst in sorted(per.items()):
        refs = sorted({s["ref"] for s in lijst})
        tegen = _tegenpartijen(lijst)
        for t in tegen:
            if t["id"]:
                rels = kr.paar_rel.get((min(eid, t["id"]), max(eid, t["id"])), [])
                t["in_model"] = sorted({f"{typ} ({st})" for _r, typ, st in rels}) or None
        uit[reg] = {"aantal": len(refs), "periode": _periode(lijst), "soorten": dict(Counter(s["soort"] for s in lijst)),
                    "tegenpartijen": tegen, "refs": refs}
        bedrag = [s["bedrag"] for s in lijst if s.get("bedrag")]
        if reg == "giften" and eid in kr.giftbedrag:
            uit[reg]["bedragen_per_partij"] = kr.giftbedrag[eid]
            uit[reg]["totaal"] = _rond(sum(sum(j.values()) for j in kr.giftbedrag[eid].values()))
        elif bedrag:
            uit[reg]["totaal_records"] = _rond(sum(bedrag))
    return uit


def domein_overzicht(kr: Kruis, eid: int) -> dict:
    """Kanalen per domein, effectief aantal domeinen, score (zie de module-uitleg)."""
    per_dom: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    gewicht: Counter = Counter()
    vrij: dict[str, list[dict]] = defaultdict(list)
    zonder: Counter = Counter()
    for s in kr.sig[eid]:
        k = s.get("kanaal")
        if not k:
            continue
        if k in DOMEINLOOS:
            vrij[k].append(s)
            continue
        doms = [d for d in s["domeinen"] if d not in GEEN_SCORE]
        if not doms:
            zonder[k] += 1
            continue
        for d in doms:
            per_dom[d][k].append(s)
            gewicht[d] += 1 / len(doms)
    tot = sum(gewicht.values())
    h = -sum((g / tot) * math.log(g / tot) for g in gewicht.values() if g) if tot else 0.0
    n_eff = math.exp(h) if tot else 0.0
    breedte = _log2(1 + n_eff) if tot else 1.0
    vrij_samen = {k: {"aantal": len({s["ref"] for s in v}), "periode": _periode(v),
                      "tegenpartijen": _tegenpartijen(v, 5), "refs": sorted({s["ref"] for s in v})}
                  for k, v in sorted(vrij.items())}
    domeinen = {}
    for d, kan in per_dom.items():
        n_dom = sum(len({s["ref"] for s in v}) for v in kan.values())
        kanalen = sorted(set(kan) | set(vrij))
        n = n_dom + len(vrij)
        score = len(kanalen) * _log2(1 + n) / breedte
        domeinen[d] = {
            "score": _rond(score), "kanalen": kanalen, "domeinkanalen": sorted(kan), "signalen": n_dom,
            "kern": len(kan) >= 2 or len(kanalen) >= 3,
            "per_kanaal": {k: {"aantal": len({s["ref"] for s in v}), "periode": _periode(v),
                               "tegenpartijen": _tegenpartijen(v, 5),
                               "domein_via": dict(Counter(s.get("domein_via") or "-" for s in v)),
                               "refs": sorted({s["ref"] for s in v})} for k, v in sorted(kan.items())}}
    top = max(domeinen, key=lambda d: (domeinen[d]["score"], domeinen[d]["signalen"])) if domeinen else None
    return {"score": domeinen[top]["score"] if top else 0.0, "topdomein": top,
            "effectieve_domeinen": _rond(n_eff), "breedtefactor": _rond(breedte),
            "domeinen": dict(sorted(domeinen.items(), key=lambda kv: -kv[1]["score"])),
            "kanalen_zonder_domein": vrij_samen, "domeinsignalen_zonder_domein": dict(zonder)}


def model_overzicht(kr: Kruis, eid: int) -> dict:
    goed = kr.rel_goed.get(eid, Counter())
    return {"goedgekeurd": sum(goed.values()), "per_type": dict(goed.most_common()),
            "voorgesteld": kr.rel_voor.get(eid, 0)}


def _band_org(s: dict) -> int | None:
    """De organisatie waarmee een persoonssignaal een band aangeeft (functie, nevenfunctie, loopbaan,
    benoeming, bestuur, optreden namens), of None (vergadering, geschenk, commissiezetel, gift)."""
    if s.get("organisatie_id"):
        return s["organisatie_id"]
    reg, soort = s["register"], s["soort"]
    if (reg == "ep_netwerk" and soort.startswith(("functie vóór", "belang"))) or reg == "rechtspraak" or \
            (reg == "tk" and soort in ("eerdere functie", "nevenfunctie")) or (reg == "oo" and soort == "ambt"):
        return s.get("tegenpartij_id")
    return None


def _functie_org(s: dict) -> int | None:
    """De organisatie van de functie zelf (benoemd bij, bestuurder van, belang bij); bij een rechter
    het gerecht, dat geen entiteit-id draagt."""
    if s["register"] == "rechtspraak":
        return None
    return s.get("organisatie_id") or s.get("tegenpartij_id")


def _functie_regel(s: dict) -> dict:
    uit = {"register": s["register"], "wat": s["soort"], "functie": s.get("functie"), "bij": s.get("tegenpartij"),
           "benoemer": None, "van": s.get("datum"), "tot": s.get("tot"), "domeinen": s["domeinen"], "ref": s["ref"]}
    if s["register"] == "staatscourant":
        uit["bij"], uit["benoemer"] = None, s.get("tegenpartij")
    elif s["register"] == "rechtspraak":
        # de positie is rechter (gerecht uit hetzelfde record); de nevenbetrekking zelf is de band
        uit.update(wat="rechter", functie=s.get("detail"), bij=None, van=None, tot=None)
    return uit


def draaideur(kr: Kruis, ent: dict) -> list[dict]:
    """Personen met een functie in staatscourant, rechtspraak, ep_netwerk of afm én een band met een
    organisatie die in lobby, agenda of tk_inspraak opduikt."""
    toegang: dict[int, dict] = {}
    for eid, e in ent.items():
        if e["soort"] != "maatschappelijk":
            continue
        lijst = [s for s in kr.sig[eid] if s.get("kanaal") in TOEGANG]
        if lijst:
            per = defaultdict(list)
            for s in lijst:
                per[s["kanaal"]].append(s)
            toegang[eid] = {
                "kanalen": {k: {"aantal": len({s["ref"] for s in v}), "periode": _periode(v),
                                "tegenpartijen": _tegenpartijen(v, 3), "refs": sorted({s["ref"] for s in v})[:12]}
                            for k, v in sorted(per.items())},
                "domeinen": sorted({d for s in lijst for d in s["domeinen"] if d not in GEEN_SCORE})}
    uit = []
    for pid, e in ent.items():
        if e["soort"] != "persoon":
            continue
        functies = []
        for s in kr.sig[pid]:
            if s["register"] == "staatscourant" and s.get("detail") != "ruis":
                functies.append(s)
            elif s["register"] == "rechtspraak":
                functies.append(s)
            elif s["register"] == "ep_netwerk" and s["soort"].startswith(("commissiezetel", "functie vóór", "belang")):
                functies.append(s)
            elif s["register"] == "afm" and s["soort"].startswith("bestuurder"):
                functies.append(s)
        if not functies:
            continue
        banden: dict[int, list[dict]] = defaultdict(list)
        for s in kr.sig[pid]:
            x = _band_org(s)
            if x and x in toegang:
                banden[x].append({"via": f"register {s['register']}", "wat": s["soort"], "functie": s.get("functie"),
                                  "van": s.get("datum"), "tot": s.get("tot"), "ref": s["ref"]})
        for b in kr.banden.get(pid, []):
            if b["org"] in toegang:
                banden[b["org"]].append({"via": "model", "wat": b["type"], "functie": b["functie"], "van": b["van"],
                                         "tot": b["tot"], "relation_id": b["relation_id"]})
        if not banden:
            continue
        for x, bewijs in banden.items():
            t = toegang[x]
            # een functie bij x zelf (benoemd bij, bestuurder van, belang bij x) is de band, geen tweede positie
            fx = [s for s in functies if _functie_org(s) != x]
            if not fx:
                continue
            fdom = {d for s in fx for d in s["domeinen"] if d not in GEEN_SCORE}
            overlap = sorted(fdom & set(t["domeinen"]))
            uit.append({
                "persoon": e["naam"], "persoon_id": pid, "organisatie": ent[x]["naam"], "organisatie_id": x,
                "functies": list({(f["register"], f["wat"], f["functie"], f["bij"], f["ref"] if f["register"] != "rechtspraak"
                                   else ""): f for f in map(_functie_regel, sorted(fx, key=lambda s: s.get("datum") or ""))
                                  }.values()),
                "banden": bewijs, "organisatie_kanalen": t["kanalen"], "organisatie_domeinen": t["domeinen"],
                "zelfde_domein": overlap,
                "_sort": (bool(overlap), len(t["kanalen"]), sum(k["aantal"] for k in t["kanalen"].values()))})
    uit.sort(key=lambda r: r["_sort"], reverse=True)
    for r in uit:
        del r["_sort"]
    return uit


def geld_en_toegang(kr: Kruis, ent: dict) -> list[dict]:
    uit = []
    for eid, e in ent.items():
        if eid not in kr.giftbedrag:
            continue
        per = defaultdict(list)
        for s in kr.sig[eid]:
            if s.get("kanaal") in TOEGANG + ("ep_vergadering",) or (s["register"] in ("agenda", "tk_inspraak")
                                                                      and e["soort"] == "persoon"):
                per[s.get("kanaal") or s["register"]].append(s)
        if not per:
            continue
        bedragen = kr.giftbedrag[eid]
        totaal = sum(sum(j.values()) for j in bedragen.values())
        gift_refs = sorted({s["ref"] for s in kr.sig[eid] if s.get("kanaal") == "gift"})
        uit.append({
            "gever": e["naam"], "id": eid, "type": ent[eid]["type"], "totaal": _rond(totaal),
            "per_partij": {p: {"totaal": _rond(sum(j.values())), "per_jaar": j} for p, j in bedragen.items()},
            "gift_refs": gift_refs,
            "kanalen": {k: {"aantal": len({s["ref"] for s in v}), "periode": _periode(v),
                            "tegenpartijen": _tegenpartijen(v, 4),
                            "domeinen": sorted({d for s in v for d in s["domeinen"]}),
                            "refs": sorted({s["ref"] for s in v})} for k, v in sorted(per.items())}})
    uit.sort(key=lambda r: (-len(r["kanalen"]), -r["totaal"]))
    return uit


INVLOED_KANALEN = ("lobby", "agenda", "tk_inspraak", "ep_vergadering", "ser", "gift", "tk_geschenk", "ep_deelname")


def eigendom_en_toegang(kr: Kruis, ent: dict) -> list[dict]:
    """Houders van ≥ 3% in een uitgevende instelling (AFM) die ook lobbyen, inspreken, spreken met
    bewindspersonen of EP-leden, in de SER zitten of geven."""
    uit = []
    for eid, belangen in kr.eigendom.items():
        if eid not in ent:
            continue
        per = defaultdict(list)
        for s in kr.sig[eid]:
            if s.get("kanaal") in INVLOED_KANALEN:
                per[s["kanaal"]].append(s)
        if not per:
            continue
        samen: dict = {}
        for b in belangen:
            k = b["instelling_id"] or b["instelling"]
            if k not in samen:
                samen[k] = dict(b, refs=list(b["refs"]))
                continue
            x = samen[k]
            x["meldingen"] += b["meldingen"]
            x["refs"] = sorted(set(x["refs"]) | set(b["refs"]))
            x["eerste_melding"] = min(x["eerste_melding"], b["eerste_melding"])
            if b["laatste_melding"] >= x["laatste_melding"]:
                x.update(laatste_melding=b["laatste_melding"], einde=b["einde"], laatste_totaal_pct=b["laatste_totaal_pct"])
            for v in ("hoogste_reeel_pct", "kapitaal_reeel_pct", "stemrecht_reeel_pct"):
                x[v] = max(x[v], b[v])
        uit.append({
            "houder": ent[eid]["naam"], "id": eid, "type": ent[eid]["type"], "soort": ent[eid]["soort"],
            "belangen": sorted(samen.values(), key=lambda b: -b["hoogste_reeel_pct"]),
            "kanalen": {k: {"aantal": len({s["ref"] for s in v}), "periode": _periode(v),
                            "tegenpartijen": _tegenpartijen(v, 4),
                            "domeinen": sorted({d for s in v for d in s["domeinen"] if d not in GEEN_SCORE}),
                            "refs": sorted({s["ref"] for s in v})} for k, v in sorted(per.items())},
            "giften": kr.giftbedrag.get(eid)})
    uit.sort(key=lambda r: (-len(r["kanalen"]), -len(r["belangen"])))
    return uit


def gaten(kr: Kruis, ent: dict) -> list[dict]:
    uit = []
    for eid, e in ent.items():
        if e["type"] == "persoon":
            continue
        regs = sorted({s["register"] for s in kr.sig[eid]})
        goed = sum(kr.rel_goed.get(eid, Counter()).values())
        if len(regs) >= 3 and goed <= 1:
            uit.append({"organisatie": e["naam"], "id": eid, "type": e["type"], "soort": e["soort"],
                        "status": kr.ent[eid]["status"], "registers": regs,
                        "signalen": {r: len({s["ref"] for s in kr.sig[eid] if s["register"] == r}) for r in regs},
                        "kanalen": sorted({s["kanaal"] for s in kr.sig[eid] if s.get("kanaal")}),
                        "goedgekeurde_verbanden": goed, "voorgestelde_verbanden": kr.rel_voor.get(eid, 0),
                        "voorbeeld_refs": {r: sorted({s["ref"] for s in kr.sig[eid] if s["register"] == r})[:5]
                                           for r in regs}})
    uit.sort(key=lambda r: (r["soort"] != "maatschappelijk", -len(r["registers"]), -sum(r["signalen"].values())))
    return uit


def bouw(kr: Kruis) -> dict:
    ent = {}
    for eid, lijst in kr.sig.items():
        if not lijst:
            continue
        e = kr.ent[eid]
        ent[eid] = {"naam": e["naam"], "type": e["type"], "status": e["status"], "soort": kr.org_soort(eid)}
    entiteiten = {}
    for eid, e in ent.items():
        entiteiten[eid] = {**e, "registers": register_overzicht(kr, eid), "model": model_overzicht(kr, eid)}
        if e["type"] != "persoon":
            entiteiten[eid]["domeinen"] = domein_overzicht(kr, eid)
    rang = sorted((eid for eid, e in entiteiten.items()
                   if e["soort"] == "maatschappelijk" and e.get("domeinen", {}).get("topdomein")),
                  key=lambda eid: (-entiteiten[eid]["domeinen"]["score"],
                                   -sum(r["aantal"] for r in entiteiten[eid]["registers"].values())))
    breed = sorted((eid for eid, e in entiteiten.items() if e["soort"] == "maatschappelijk"
                    and e.get("domeinen", {}).get("effectieve_domeinen", 0) >= BREED_N),
                   key=lambda eid: -entiteiten[eid]["domeinen"]["effectieve_domeinen"])
    return {"entiteiten": entiteiten, "rangschikking": rang, "breed_aanwezig": breed,
            "draaideur_en_benoemingen": draaideur(kr, ent), "geld_en_toegang": geld_en_toegang(kr, ent),
            "eigendom_en_toegang": eigendom_en_toegang(kr, ent),
            "gaten": gaten(kr, ent)}


# ── markdown ────────────────────────────────────────────────────────────────
def _per(p) -> str:
    van, tot, stand = (p + [None, None, None])[:3] if p else (None, None, None)
    if van and tot and van != tot:
        return f"{van} – {tot}"
    if van:
        return van
    return f"stand {stand}" if stand else "zonder datum"


def _euro(x: float) -> str:
    return giften.euro(x) if hasattr(giften, "euro") else f"€ {x:,.0f}".replace(",", ".")


def _tp(lijst, n=3) -> str:
    return ", ".join(f"{t['naam']} {t['aantal']}×" for t in lijst[:n])


def _kanaalregel(k: str, v: dict) -> str:
    return f"{KANAAL[k]} {v['aantal']}× ({_per(v['periode'])}; {_tp(v['tegenpartijen'])})"


def _functie_tekst(s: dict) -> str:
    t = s["wat"]
    if s.get("functie") and s["functie"].lower() not in t.lower():
        t += f" {s['functie']}"
    if s.get("bij"):
        t += f" bij {s['bij']}"
    if s.get("benoemer"):
        t += f", benoemer {s['benoemer']}"
    return t + f" ({s['van'] or '?'}{' – ' + s['tot'] if s.get('tot') else ''}; {s['ref']})"


def markdown(rap: dict, top: int) -> str:
    E = rap["entiteiten"]
    r = ["# Kruisrapport registers: wie duikt waar op", "",
         f"Gemaakt {rap['gemaakt']} door `tools/registers/kruisrapport.py` (alleen lezen). Bron per regel: "
         "`data/registers/kruisrapport.json`, met per entiteit, register en kanaal de verwijzingen "
         "`<register>/<uitgave>#<recordsleutel>`.", "",
         "Elk signaal is gekoppeld met de koppelregels van de importers (`<bron>_naar_model.py`, droogloop) en "
         "doorstaat dezelfde controle als `scripts/registercheck.py`. Personen alleen als ze goedgekeurd in het "
         "model staan.", "",
         "## Registers", "",
         "| register | uitgave(n) | records | signalen | entiteiten | niet meegeteld |", "|---|---|---|---|---|---|"]
    for reg, d in rap["dekking"].items():
        niet = "; ".join(f"{k}: {v}" for k, v in d.items() if k not in ("records", "signalen", "entiteiten", "uitgaven"))
        r.append(f"| {reg} | {', '.join(d.get('uitgaven', [])[-3:])}{' …' if len(d.get('uitgaven', [])) > 3 else ''} | "
                 f"{d.get('records', '')} | {d.get('signalen', 0)} | {d.get('entiteiten', 0)} | {niet or '-'} |")
    r += ["", "## Methode", "",
          "- **Kanalen met een domein**: afspraak met een bewindspersoon (domein van het ministerie), inbreng bij een "
          "Kamercommissie namens de organisatie (domein van de commissie), vergadering met een Nederlands EP-lid "
          "(domein van de commissie van de procedure, anders een trefwoord in de titel, anders de enige commissie van "
          "het EP-lid), SER-zetel (sociale zaken en economie).",
          "- **Kanalen zonder domein**: toegangspas Tweede Kamer, gift aan een partij, betaalde deelname van een EP-lid, "
          "betaalde reis of geschenk aan een Kamerlid, eigendom van 3% of meer in een uitgevende instelling (AFM). Ze "
          "tellen mee in elk domein waarin de organisatie via een domeinkanaal actief is.",
          "- **Bestuur (AFM)**: een bestuurder of commissaris van een beursonderneming (melding 5:48 Wft of MAR 19) is "
          "een functie van een persoon en telt in sectie 4, niet als kanaal van de onderneming.",
          "- **Score** = kanalen in het domein × log2(1 + signalen in het domein) / breedtefactor. Signalen = records "
          "van de domeinkanalen, plus 1 per kanaal zonder domein.",
          "- **Breedtefactor** = log2(1 + N), met N het effectieve aantal domeinen (exp van de Shannon-entropie van de "
          "domeinsignalen). Eén domein: factor 1; acht gelijke domeinen: 3,17. Zo deelt een koepel die bij elk "
          "ministerie en elke commissie zit door haar spreiding, zonder dat haar sterkste domein wegvalt. Wie "
          f"effectief over {BREED_N:.0f} of meer domeinen verspreid is, staat ook onder 'Breed aanwezig'.",
          "- **Kernsignaal**: in één domein twee of meer domeinkanalen, of drie of meer kanalen in totaal.",
          "- Overheid, partijen en media staan in de JSON maar niet in de rangschikking.", "",
          "Domeinen: " + "; ".join(f"`{k}` {v}" for k, v in DOMEINEN.items()) + ".", "",
          f"## 1–3. Meerdere kanalen in hetzelfde domein (top {top})", "",
          "| # | organisatie | score | domein | kanalen in dat domein | breedte (N) | goedgekeurde verbanden |",
          "|---|---|---|---|---|---|---|"]
    for i, eid in enumerate(rap["rangschikking"][:top], 1):
        e = E[eid]
        d = e["domeinen"]
        td = d["domeinen"][d["topdomein"]]
        r.append(f"| {i} | {e['naam']} ({e['type']}) | {d['score']} | {DOMEINEN[d['topdomein']]}"
                 f"{' · kern' if td['kern'] else ''} | {', '.join(KANAAL[k] for k in td['kanalen'])} | "
                 f"{d['effectieve_domeinen']} | {e['model']['goedgekeurd']} |")
    r += ["", "### Per organisatie", ""]
    for i, eid in enumerate(rap["rangschikking"][:top], 1):
        e = E[eid]
        d = e["domeinen"]
        r.append(f"**{i}. {e['naam']}** ({e['type']}{', voorgesteld' if e['status'] != 'goedgekeurd' else ''}) — "
                 f"score {d['score']}, effectief {d['effectieve_domeinen']} domeinen (factor {d['breedtefactor']}); "
                 f"JSON `entiteiten[\"{eid}\"]`")
        for dk, dv in list(d["domeinen"].items())[:3]:
            delen = [_kanaalregel(k, v) for k, v in dv["per_kanaal"].items()]
            r.append(f"- {DOMEINEN[dk]} (score {dv['score']}{', kern' if dv['kern'] else ''}): " + "; ".join(delen))
        if len(d["domeinen"]) > 3:
            r.append("- verder: " + ", ".join(f"{DOMEINEN[k]} ({v['signalen']})" for k, v in list(d["domeinen"].items())[3:]))
        if d["kanalen_zonder_domein"]:
            r.append("- zonder domein: " + "; ".join(_kanaalregel(k, v) for k, v in d["kanalen_zonder_domein"].items()))
        overig = {k: v for k, v in e["registers"].items() if k not in ("agenda", "tk_inspraak", "lobby", "giften", "ser")}
        if overig:
            r.append("- verder in registers: " + "; ".join(
                f"{k} {v['aantal']}× ({', '.join(f'{s} {n}' for s, n in list(v['soorten'].items())[:2])})"
                for k, v in overig.items()))
        if "giften" in e["registers"] and e["registers"]["giften"].get("bedragen_per_partij"):
            r.append("- giften: " + "; ".join(f"{p} {_euro(sum(j.values()))} ({', '.join(j)})"
                                               for p, j in e["registers"]["giften"]["bedragen_per_partij"].items()))
        m = e["model"]
        r.append(f"- in het model: {m['goedgekeurd']} goedgekeurd ("
                 + (", ".join(f"{t} {n}" for t, n in m["per_type"].items()) or "-") + f"), {m['voorgesteld']} voorgesteld")
        r.append("")
    r += ["## Breed aanwezig", "",
          f"Effectief {BREED_N:.0f} of meer domeinen. Hun score is door de breedtefactor gedeeld; hier staat de spreiding.", "",
          "| organisatie | N | factor | signalen per domein | kanalen zonder domein |", "|---|---|---|---|---|"]
    for eid in rap["breed_aanwezig"]:
        e = E[eid]
        d = e["domeinen"]
        r.append(f"| {e['naam']} | {d['effectieve_domeinen']} | {d['breedtefactor']} | "
                 + ", ".join(f"{k} {v['signalen']}" for k, v in sorted(d["domeinen"].items(), key=lambda kv: -kv[1]["signalen"]))
                 + f" | {', '.join(KANAAL[k] for k in d['kanalen_zonder_domein']) or '-'} |")
    rijen = rap["draaideur_en_benoemingen"]
    r += ["", "## 4. Draaideur en benoemingen", "",
          "Personen met een functie uit de Staatscourant (benoeming, herbenoeming, ontslag), het nevenfunctieregister "
          "van de Rechtspraak (rechter), het EP-netwerk (commissiezetel of belangenopgave) of het AFM-register "
          "(bestuurder of commissaris van een beursonderneming), en een band met een organisatie die in het "
          "lobbyistenregister, de agenda's of de Kamerinspraak staat. De band is een functie, nevenfunctie, eerdere "
          "functie, benoeming of bestuurszetel bij die organisatie volgens een register, een goedgekeurd verband in het "
          "model (relation_id), of een optreden namens de organisatie (volledige naam in een afspraak of genodigdenregel, "
          "met een goedgekeurd verband). Een vergadering, geschenk of gift is geen band. Een functie bij de organisatie "
          "zelf telt niet als tweede positie. Eerst de gevallen waarin het domein van de functie en dat van de "
          f"organisatie overeenkomen. {len(rijen)} paren; hier de eerste {min(len(rijen), top)}.", ""]
    for x in rijen[:top]:
        f = "; ".join(_functie_tekst(s) for s in x["functies"][:3])
        b = "; ".join(f"{bb['wat']}{' ' + bb['functie'] if bb.get('functie') else ''} ({bb.get('van') or '?'}"
                      f"{' – ' + bb['tot'] if bb.get('tot') else ''}; " + (bb.get("ref") or f"relation #{bb.get('relation_id')}") + ")"
                      for bb in x["banden"][:3])
        k = "; ".join(_kanaalregel(kk, vv) for kk, vv in x["organisatie_kanalen"].items())
        r.append(f"- **{x['persoon']}** — functie: {f}. Band met **{x['organisatie']}**: {b}. {x['organisatie']}: {k}."
                 + (f" Zelfde domein: {', '.join(DOMEINEN[d] for d in x['zelfde_domein'])}." if x["zelfde_domein"] else ""))
    rijen = rap["geld_en_toegang"]
    r += ["", "## 5. Geld en toegang", "",
          "Gevers (Wfpp-overzichten) die ook een toegangspas hebben, in de agenda's van bewindspersonen staan, inbreng "
          f"leveren bij een Kamercommissie of EP-leden spreken. {len(rijen)} gevers.", "",
          "| gever | giften (partij: totaal, jaren) | kanalen |", "|---|---|---|"]
    for x in rijen:
        g = "; ".join(f"{p} {_euro(v['totaal'])} ({', '.join(v['per_jaar'])})" for p, v in x["per_partij"].items())
        k = "; ".join(f"{KANAAL.get(kk, kk)} {vv['aantal']}× ({_per(vv['periode'])}; {_tp(vv['tegenpartijen'], 2)})"
                      for kk, vv in x["kanalen"].items())
        r.append(f"| {x['gever']} ({x['type']}) | {g} | {k} |")
    rijen = rap["eigendom_en_toegang"]
    r += ["", "### Eigendom en toegang (AFM)", "",
          "Organisaties die in het AFM-register substantiële deelnemingen een belang van 3% of meer in een uitgevende "
          "instelling meldden, en die ook via een ander kanaal opduiken (toegangspas, afspraak, Kamerinspraak, EP-lid, "
          "SER, gift, geschenk). Percentages: het hoogste reële belang (kapitaal of stemrecht, zonder opties en "
          "swaps) in de laatste meldingenreeks, zoals `afm_naar_model.py` ze berekent; eigen aandelen tellen niet. "
          f"{len(rijen)} organisaties.", "",
          "| houder | belangen (hoogste reëel %, meldingen, periode) | kanalen |", "|---|---|---|"]
    for x in rijen:
        b = "; ".join(f"{bb['instelling']} {str(bb['hoogste_reeel_pct']).replace('.', ',')}% ({bb['meldingen']}×, "
                      f"{bb['eerste_melding']}{' – ' + bb['laatste_melding'] if bb['laatste_melding'] != bb['eerste_melding'] else ''}"
                      f"{', einde ' + bb['einde'] if bb.get('einde') else ''})" for bb in x["belangen"][:6])
        if len(x["belangen"]) > 6:
            b += f"; en {len(x['belangen']) - 6} andere"
        k = "; ".join(f"{KANAAL.get(kk, kk)} {vv['aantal']}× ({_per(vv['periode'])}; {_tp(vv['tegenpartijen'], 2)})"
                      for kk, vv in x["kanalen"].items())
        r.append(f"| {x['houder']} ({x['type']}) | {b} | {k} |")
    rijen = rap["gaten"]
    r += ["", "## 6. Gaten: in drie of meer registers, in het model hooguit één goedgekeurd verband", "",
          f"{len(rijen)} organisaties (eerst de maatschappelijke). Kandidaten voor de scout.", "",
          "| organisatie | soort | registers (signalen) | kanalen | verbanden goedgekeurd / voorgesteld |", "|---|---|---|---|---|"]
    for x in rijen:
        r.append(f"| {x['organisatie']} ({x['type']}{', voorgesteld' if x['status'] != 'goedgekeurd' else ''}) | "
                 f"{x['soort']} | {', '.join(f'{k} {v}' for k, v in x['signalen'].items())} | "
                 f"{', '.join(KANAAL[k] for k in x['kanalen']) or '-'} | {x['goedgekeurde_verbanden']} / "
                 f"{x['voorgestelde_verbanden']} |")
    personen = sorted((eid for eid, e in E.items() if e["type"] == "persoon" and len(e["registers"]) >= 3),
                      key=lambda eid: (-len(E[eid]["registers"]), E[eid]["naam"]))
    r += ["", "## Bijlage: publieke personen in drie of meer registers", "",
          "| persoon | registers (signalen) | goedgekeurde verbanden |", "|---|---|---|"]
    for eid in personen:
        e = E[eid]
        regs = ", ".join(f"{k} {v['aantal']}" for k, v in e["registers"].items())
        r.append(f"| {e['naam']} | {regs} | {e['model']['goedgekeurd']} |")
    r += ["", "## Bijlage: domeintabel", "",
          "Ministeries en Kamercommissies (sleutel zonder 'Ministerie van' of 'Vaste commissie voor'):", ""]
    r += [f"- {k} → {', '.join(v)}" for k, v in NAAM_DOMEIN.items()]
    r += ["", "Commissies van het Europees Parlement:", ""]
    r += [f"- {k} → {', '.join(v)}" for k, v in EP_COMMISSIE_DOMEIN.items()]
    return "\n".join(r) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--top", type=int, default=TOP)
    a = ap.parse_args()
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    print("Registers lezen (droogloop van de Plannen):")
    kr = Kruis(conn, koppelingen).lees()
    rap = bouw(kr)
    for reg in kr.dekking:
        kr.dekking[reg]["entiteiten"] = sum(1 for eid in kr.sig if any(s["register"] == reg for s in kr.sig[eid]))
    volgorde = ["lobby", "agenda", "tk_inspraak", "ep_netwerk", "giften", "staatscourant", "rechtspraak", "tk", "ser",
                "afm", "oo", "ep", "cbs"]
    dekking = {reg: {**dict(kr.dekking[reg]), "uitgaven": sorted(kr.uitgaven.get(reg, ()))}
               for reg in volgorde if reg in kr.dekking}
    rap = {"gemaakt": datetime.datetime.now().isoformat(timespec="seconds"),
           "ref_vorm": "<register>/<uitgave>#<recordsleutel> (zoals citations.page en citations.section)",
           "methode": __doc__, "domeinen": DOMEINEN, "domeintabel": {"namen": NAAM_DOMEIN, "ep_commissies": EP_COMMISSIE_DOMEIN,
                                                                     "trefwoorden": DOMEIN_WOORDEN},
           "kanalen": KANAAL, "dekking": dekking, **rap}
    UIT.mkdir(parents=True, exist_ok=True)
    # JSON-sleutels zijn tekst: de lijsten noemen dezelfde id's als tekst
    jrap = {**rap, "rangschikking": [str(x) for x in rap["rangschikking"]],
            "breed_aanwezig": [str(x) for x in rap["breed_aanwezig"]]}
    (UIT / "kruisrapport.json").write_text(json.dumps(jrap, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    (UIT / "kruisrapport.md").write_text(markdown(rap, a.top), encoding="utf-8")
    print(json.dumps({reg: {k: v for k, v in d.items() if k != "uitgaven"} for reg, d in dekking.items()},
                     ensure_ascii=False, indent=1))
    print(f"entiteiten: {len(rap['entiteiten'])} · gerangschikt: {len(rap['rangschikking'])} · breed: "
          f"{len(rap['breed_aanwezig'])} · draaideur: {len(rap['draaideur_en_benoemingen'])} · geld en toegang: "
          f"{len(rap['geld_en_toegang'])} · gaten: {len(rap['gaten'])}")
    print(f"rapport: {UIT / 'kruisrapport.md'} en .json")


if __name__ == "__main__":
    main()
