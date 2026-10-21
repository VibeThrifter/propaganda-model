"""Tweede Kamer, wie mag inspreken — uitgave ophalen en lezen (2026-10-20).

Het parlementaire spiegelbeeld van de agenda's van bewindspersonen (agenda.py): welke
organisaties een Kamercommissie hoort. De open data van de Tweede Kamer (gegevensmagazijn,
OData v4, zoals tk.py) heeft daarvoor:
  - Activiteit met Soort 'Rondetafelgesprek', 'Hoorzitting', 'Technische briefing', 'Gesprek' en
    'Petitie' (sinds SINDS, alleen wat al geweest is), met de voortouwcommissie
    (Voortouwcommissie_Id) en de agendapunten. De genodigden staan NIET in ActiviteitActor (dat
    zijn de Kamerleden; gasten staan er zonder naam in) maar als lijst in Agendapunt.Noot
    ("Naam, functie, organisatie"), soms in Agendapunt.Onderwerp ("Blok 2: …"); bij een gesprek,
    petitie of briefing staat de tegenpartij vaak in het onderwerp ("Gesprek met …", "… door …");
  - Zaak met Soort 'Position paper' (sinds SINDS): de indiener staat in het onderwerp ("Position
    paper <indiener> t.b.v. rondetafelgesprek …"), de commissie in ZaakActor (Relatie
    'Voortouwcommissie'), het rondetafelgesprek via Agendapunt.Activiteit_Id;
  - Commissie: naam, rubriek (Inhoudsopgave), DatumActief/DatumInactief;
  - Kamerstukdossier van de zaken van een activiteit: het dossier.
Dat gaat als één JSON-uitgave naar data/registers/tk_inspraak/tk_inspraak_<datum>.json (+ .sha256).

Records (de recordregel is het citaat; `wie` is het deel van de regel waarin de organisatie moet
staan, zodat een onderwerp als "rondetafelgesprek over Schiphol" Schiphol niet tot gast maakt):
  - positionpaper:<zaak-id>                   — één position paper; wie = de indiener;
  - genodigde:<activiteitnummer>:<hash>       — één genodigde uit de lijst van een agendapunt;
                                                 wie = de regel zelf ("Naam, functie, organisatie");
  - tegenpartij:<activiteitnummer>            — de tegenpartij uit het onderwerp van een gesprek,
                                                 petitie of technische briefing.
De hash hangt alleen af van de activiteit en de tekst van de regel. Elk record zegt ook in welke
hoedanigheid iemand er zat (`pet`: 'namens' = de organisatie spreekt, zoals een directeur of
beleidsadviseur; 'persoonlijk' = een onderzoeker of hoogleraar met eigen duiding, eigenaarsbesluit
2026-10-19 "instituut of persoon"; 'oud' = een vorige pet) en of het om een privépersoon gaat
(`prive`: ervaringsdeskundige, burger, ouder …; nooit naar het model).

Geen schrijfacties op het model (dat doet tk_inspraak_naar_model.py via de REST-API).

    python3 tools/registers/tk_inspraak.py haal [--sinds 2023-01-01]
    python3 tools/registers/tk_inspraak.py lees [--uitgave JJJJ-MM-DD]
"""
from __future__ import annotations

import datetime
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tk  # noqa: E402
from common import DATA, get_json, namen_van, noemt, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "tk_inspraak"
API = tk.API
URL = "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/"
MAP = DATA / BRON
TITEL = ("Tweede Kamer der Staten-Generaal, open data (gegevensmagazijn): rondetafelgesprekken, "
         "hoorzittingen, technische briefings, gesprekken, petities en position papers, uitgave {uitgave}")
UITGEVER = "Tweede Kamer der Staten-Generaal"
SINDS = "2023-01-01"
SOORTEN = ("Rondetafelgesprek", "Hoorzitting", "Technische briefing", "Gesprek", "Petitie")
PAUZE = 1.0   # seconden tussen verzoeken (beleefd: de server is publiek en gedeeld)


class FormaatFout(Exception):
    """De uitgave mist velden die deze lezer verwacht."""


# ── ophalen ─────────────────────────────────────────────────────────────────
def _get(url: str) -> dict:
    for poging in range(4):
        try:
            return get_json(url, timeout=120)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if poging == 3:
                raise
            time.sleep(5 * (poging + 1))
            print(f"  opnieuw ({e})", file=sys.stderr)
    return {}


def _alles(pad: str, params: dict) -> list[dict]:
    url = f"{API}/{pad}?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe="$,'()")
    uit = []
    while url:
        d = _get(url)
        uit += d.get("value", [])
        url = d.get("@odata.nextLink")
        time.sleep(PAUZE)
    return uit


def _jaren(sinds: str, tot: str) -> list[tuple[str, str]]:
    """[(van, tot)] per kalenderjaar, de laatste tot en met gisteren (alleen wat geweest is)."""
    uit, jaar = [], int(sinds[:4])
    while f"{jaar}-01-01" < tot:
        van = max(sinds, f"{jaar}-01-01")
        uit.append((van, min(f"{jaar + 1}-01-01", tot)))
        jaar += 1
    return uit


def haal(sinds: str = SINDS, meld=print) -> Path:
    vandaag = datetime.date.today().isoformat()
    commissies = _alles("Commissie", {
        "$filter": "Verwijderd eq false",
        "$select": "Id,Nummer,Afkorting,NaamNL,Soort,Inhoudsopgave,DatumActief,DatumInactief"})
    meld(f"tk_inspraak: {len(commissies)} commissies")
    activiteiten = []
    for soort in SOORTEN:
        for van, tot in _jaren(sinds, vandaag):
            deel = _alles("Activiteit", {
                "$filter": f"Soort eq '{soort}' and Verwijderd eq false and Datum ge {van}T00:00:00Z "
                           f"and Datum lt {tot}T00:00:00Z",
                "$select": "Id,Nummer,Soort,Onderwerp,Datum,Status,Besloten,Voortouwnaam,Voortouwafkorting,"
                           "Voortouwcommissie_Id,Noot",
                "$expand": "Agendapunt($select=Id,Nummer,Onderwerp,Volgorde,Noot;$filter=Verwijderd eq false),"
                           "Zaak($select=Id,Nummer,Soort,Onderwerp;$filter=Verwijderd eq false;"
                           "$expand=Kamerstukdossier($select=Id,Nummer,Toevoeging,Titel))"})
            meld(f"tk_inspraak: {soort} {van}–{tot}: {len(deel)}")
            activiteiten += deel
    papers = []
    for van, tot in _jaren(sinds, vandaag):
        deel = _alles("Zaak", {
            "$filter": f"Soort eq 'Position paper' and Verwijderd eq false and GestartOp ge {van}T00:00:00Z "
                       f"and GestartOp lt {tot}T00:00:00Z",
            "$select": "Id,Nummer,Onderwerp,GestartOp,Status",
            "$expand": "ZaakActor($select=ActorNaam,ActorAfkorting,Relatie,Commissie_Id;$filter=Verwijderd eq false),"
                       "Agendapunt($select=Id,Activiteit_Id;$filter=Verwijderd eq false),"
                       "Document($select=Id,DocumentNummer,Onderwerp,Datum;$filter=Verwijderd eq false)"})
        meld(f"tk_inspraak: position papers {van}–{tot}: {len(deel)}")
        papers += deel
    data = {"bron": BRON, "opgehaald": vandaag, "sinds": sinds, "soorten": list(SOORTEN),
            "commissies": commissies, "activiteiten": activiteiten, "positionpapers": papers}
    MAP.mkdir(parents=True, exist_ok=True)
    pad = pad_van(vandaag)
    pad.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (MAP / f"{BRON}_{vandaag}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def uitgaven() -> list[Path]:
    return sorted(MAP.glob(f"{BRON}_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"{BRON}_{uitgave}.json"


# ── tekst ontleden (deterministisch: de registercheck leest met dezelfde regels) ──
_KOP = re.compile(r"^(?:blok|ronde|sessie|panel|deel|block|onderdeel|programma|sprekers(?:lijst)?|deelnemers|"
                  r"genodigden(?:lijst)?|lijst van genodigden|blokindeling|scope|toelichting|agenda)\b", re.I)
_PROZA = re.compile(r"\?|\b(?:wordt|worden|werd|zal|zullen|heeft|hebben|wil|willen|kan|kunnen|wenst|gaat|gaan|"
                    r"zijn|is|vindt|vinden)\b", re.I)
_DOOR = re.compile(r"\b(?:verzorgd|gegeven|gehouden|toegelicht|gepresenteerd|ingeleid)\s+door\s+", re.I)
_OPSOMMING = re.compile(r"^(?:[-–—•*·▪>]+|\d{1,2}[.)]|[a-z][.)]|[ivx]{1,4}[.)])\s*")
MAX_WOORDEN = 40   # een genodigde is een korte regel; langer is toelichting
_VERWIJZING = re.compile(r"^(?:zie|meer informatie|link|bijlage|let op|n\.?b\.?)\b|https?:|www\.|\b\w+\.(?:nl|com|org|eu)\b",
                         re.I)


_QUOTES = re.compile(r"[‘'\"“”„«][^’'\"“”»]{2,}[’'\"“”»]")
_ONDERWERP_EIND = re.compile(
    r"\s+(?:over|inzake|m\.\s?b\.\s?t\.?|mbt|met betrekking tot|betreffende|n\.\s?a\.\s?v\.?|naar aanleiding van|"
    r"t\.\s?a\.\s?v\.?|ten aanzien van|in het kader van|i\.\s?h\.\s?k\.\s?v\.?|ihkv|omtrent|aangaande|rondom|"
    r"t\.\s?b\.\s?v\.?|ten behoeve van|in verband met|i\.\s?v\.\s?m\.?)\s+.*$", re.I)

def _regels(noot: str | None) -> list[str]:
    """Agendapuntnoot (html) → losse regels zonder opsommingsteken."""
    t = html.unescape(noot or "").replace("\xa0", " ")
    t = re.sub(r"(?i)<\s*/?\s*(?:br|li|p|div|ol|ul|h\d|tr|table|tbody)\b[^>]*>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    uit = []
    for r in t.split("\n"):
        r = schoon(_OPSOMMING.sub("", schoon(r)))
        if r and re.search(r"[A-Za-zÀ-ÿ]", r):
            uit.append(r)
    return uit


def _genodigde(regel: str) -> str | None:
    """Het deel van een notitieregel waarin een genodigde staat, of None (kop, toelichting)."""
    m = _DOOR.search(regel)
    if m:                                    # "De briefing wordt verzorgd door X, functie bij Y (over …)"
        return schoon(_ONDERWERP_EIND.sub("", regel[m.end():])).rstrip(" .") or None
    if _KOP.match(regel) or regel.endswith(":") or len(regel.split()) > MAX_WOORDEN or _PROZA.search(regel) \
            or _VERWIJZING.search(regel):
        return None
    return regel


_MET = re.compile(r"^(?:openbaar\s+|besloten\s+|informeel\s+|informele\s+)?(?:gesprek(?:ken)?|kennismaking\w*|"
                  r"ontmoeting|overleg|bijeenkomst|ontbijt\w*|lunch\w*|werkontbijt|werklunch)\s+(?:\S+\s+){0,3}?met\s+",
                  re.I)


def tegenpartij(soort: str, onderwerp: str | None) -> str | None:
    """De tegenpartij uit het onderwerp van een gesprek, petitie of technische briefing: na 'door' of
    'namens', na 'Gesprek met', vóór 'biedt … aan' of een gedachtestreepje; zonder het onderwerp
    ('over …', 'inzake …') en zonder titels tussen aanhalingstekens ('Stop de Postcodeloterij'). Bij een
    briefing zonder zo'n teken is het onderwerp geen tegenpartij ('… omwonenden Tata Steel')."""
    t = schoon(_QUOTES.sub(" ", onderwerp or ""))
    t = schoon(re.sub(r"\((?:gewijzigd|herzien|verplaatst|geannuleerd|uitgesteld|besloten|openbaar|digitaal|"
                      r"aanpassing|nieuw)[^)]*\)", " ", t, flags=re.I))
    door = list(re.finditer(r"\b(?:verzorgd door|aangeboden door|door|namens)\s+", t, re.I))
    met = _MET.match(t)
    biedt = re.search(r"\s+(?:bied(?:t|en)|overhandig(?:t|en))\b", t, re.I)
    streep = re.search(r"\s+[-–—]\s+", t)
    if door:
        wie = t[door[-1].end():]
    elif met:
        wie = t[met.end():]
    elif biedt:
        wie = t[:biedt.start()]
    elif streep:
        wie = t[:streep.start()]
    elif soort in ("Gesprek", "Petitie"):
        wie = t
    else:
        m = _ONDERWERP_EIND.search(t)
        wie = t[:m.start()] if m and len(t[:m.start()].split()) <= 6 else ""
    wie = schoon(_ONDERWERP_EIND.sub("", wie)).strip(" :;,.-–")
    return wie or None


_PP = re.compile(r"^(?:aanvullende\s+|aanvullend\s+|voorlopig(?:e)?\s+|herziene\s+|tweede\s+)?position\s?papers?\s+"
                 r"(?:van\s+)?(?P<wie>.+?)\s+(?:t\.\s?b\.\s?v\.?|tbv|ten behoeve van)\s+(?P<rest>.*)$", re.I)
_TITEL = r"(?:(?:prof|dr|mr|ir|drs|ing|dhr|mw|mevr|em|ds)\.?\s*)"
_TUSSEN = r"(?:(?:van|de|der|den|het|ten|ter|te|in|'t|op|von|la|le|du|da|di|el|al|v\.d\.)\s+)"
_PERSOON = re.compile(rf"^{_TITEL}*(?:[A-ZÀ-Ý][a-z]{{0,2}}\.\s?)+{_TUSSEN}*[A-ZÀ-Ý][\w'’\-]+(?:\s*\([^)]*\))?$"
                      rf"|^{_TITEL}+[A-ZÀ-Ý][\w'’\-]+(?:\s+{_TUSSEN}*[A-ZÀ-Ý][\w'’\-]+){{0,2}}$")


def indiener(onderwerp: str | None) -> tuple[str | None, bool]:
    """'Position paper Instituut Clingendael t.b.v. rondetafelgesprek …' → ('Instituut Clingendael', False);
    'Position paper G. Bos t.b.v. …' → ('G. Bos', True): een persoon (voorletters of titel) op eigen naam."""
    m = _PP.match(schoon(onderwerp))
    if not m:
        return None, False
    wie = schoon(m.group("wie"))
    return wie, bool(_PERSOON.match(wie))


# ── hoedanigheid en privacy (eigenaarsbesluit 2026-10-19 "instituut of persoon"; privépersonen nooit) ──
PRIVE = re.compile(
    r"\b(?:ervaringsdeskundig\w*|ervaringsverha\w*|persoonlijke titel|burger|burgers|inwoner|inwoners|bewoner|"
    r"bewoners|omwonende|omwonenden|ouder van|ouders van|moeder|vader|pleegouder\w*|patient|patienten|client|"
    r"clienten|nabestaande\w*|slachtoffer\w*|gedupeerde\w*|getroffene\w*|mantelzorger\w*|scholier\w*|leerling|"
    r"leerlingen|student|studenten|jongere|jongeren|kind|kinderen|bezorgde|betrokkene|betrokkenen|"
    r"particulier\w*|melder|klokkenluider\w*)\b")
KOP_PRIVE = re.compile(r"\b(?:ervaring\w*|verhalen|persoonlijk\w*|ouders|slachtoffers|nabestaanden|gedupeerden|"
                       r"burgers|inwoners|bewoners|omwonenden|patienten|clienten|jongeren|kinderen|scholieren|"
                       r"studenten|mantelzorgers|betrokkenen|getroffenen)\b")
KOP_GEMENGD = re.compile(r"\b(?:organisaties|aanbieders|instellingen|professionals|verzekeraars|branche\w*|koepel\w*|"
                         r"vertegenwoordigers|belangenorganisaties|belangenbehartigers|bedrijven|sector|veld\w*|"
                         r"overheden|gemeenten|wetenschap|experts|deskundigen)\b")
KOP_KENNIS = re.compile(r"\b(?:wetenschap\w*|kennis\w*|academ\w*|onderzoek\w*|experts?|deskundig\w*|duiding|"
                        r"juridisch\w*|juristen|economen|gedragseconomen)\b")
OUD = re.compile(r"\b(?:oud|voormalig\w*|ex|emeritus|em|gepensioneerd\w*)\b")
LEIDING = re.compile(r"\b(?:\w*directeur\w*|director|directie|\w*voorzitter\w*|chair\w*|president|\w*bestuurder\w*|"
                     r"bestuurslid|bestuursleden|ceo|cfo|coo|cto|cio|cco|cso|hoofd|afdelingshoofd|hoofdeconoom|chief|"
                     r"managing|woordvoerder\w*|spokesperson|algemeen secretaris|secretaris generaal|commandant|"
                     r"kwartiermaker|inspecteur generaal|ombudsman|ombudsvrouw|kinderombudsman|kinderombudsvrouw)\b")
STAF = re.compile(r"\b(?:beleidsadviseur\w*|beleidsmedewerker\w*|beleidsverantwoordelijke|policy|public affairs|"
                  r"belangenbehartig\w*|lobbyist\w*|projectleider\w*|programmaleider\w*|programmamanager\w*|"
                  r"\w*manager|\w*coordinator|campagne\w*|campaigner|advocacy|vertegenwoordiger\w*|namens)\b")
PERSOONLIJK = re.compile(r"\b(?:hoogleraar\w*|professor\w*|prof|docent\w*|hoofddocent|lector\w*|onderzoeker\w*|"
                         r"researcher\w*|research|fellow\w*|promovend\w*|phd|postdoc\w*|wetenschapper\w*|"
                         r"wetenschappelijk\w*|academic\w*|econoom|economist|analist\w*|analyst\w*|expert\w*|deskundige\w*|"
                         r"advocaat|advocaten|lawyer|jurist|arts|huisarts|\w+arts|psychiater|psycholoog|"
                         r"\w+loog|\w+iater|chirurg\w*|specialist\w*|verpleegkundige\w*|journalist\w*|auteur|schrijver|"
                         r"zelfstandig\w*|zzp\w*|ondernemer)\b")


def _zonder(tekst: str, org_namen) -> str:
    """De tekst in sleutelvorm, met de naam van de organisatie eruit ('Jongeren Organisatie
    Beroepsonderwijs' of 'Stichting Onderzoek X' maakt niemand tot jongere of onderzoeker)."""
    t = f" {sleutel(tekst)} "
    for naam in org_namen or ():
        for k in sorted(namen_van(naam), key=len, reverse=True):
            t = t.replace(f" {k} ", " ")
    return schoon(t)


def hoedanigheid(rec: dict, org_namen=()) -> tuple[str, bool]:
    """→ (pet, prive). pet: 'leiding' (directeur, voorzitter, woordvoerder: de organisatie spreekt),
    'namens' (een medewerker of een organisatie zonder functie erbij), 'persoonlijk' (hoogleraar,
    onderzoeker, advocaat, arts: eigen duiding) of 'oud' (een vorige pet). Een position paper of de
    tegenpartij van een gesprek is de organisatie zelf ('namens'), behalve een paper op eigen naam.
    prive: een ervaringsdeskundige, burger, ouder, patiënt … in de regel of in de blokkop."""
    tekst = _zonder(rec.get("wie") or "", org_namen)
    kop = sleutel(rec.get("kop"))
    prive = bool(PRIVE.search(tekst)) or bool(kop and KOP_PRIVE.search(kop) and not KOP_GEMENGD.search(kop))
    if rec["soort"] == "positionpaper":
        return ("persoonlijk" if rec.get("indiener_persoon") else "namens"), prive
    if rec["soort"] == "tegenpartij":
        return "namens", prive
    if OUD.search(tekst):
        return "oud", prive
    if LEIDING.search(tekst):
        return "leiding", prive
    if STAF.search(tekst):
        return "namens", prive
    if PERSOONLIJK.search(tekst):
        return "persoonlijk", prive
    if kop and KOP_KENNIS.search(kop) and not re.search(r"[,–—-]|\bbij\b|\bvan\b", rec.get("wie") or ""):
        return "persoonlijk", prive   # een kale naam in het blok 'Wetenschap'
    return "namens", prive


# ── lezen ───────────────────────────────────────────────────────────────────
def _datum(waarde) -> str | None:
    return (waarde or "")[:10] or None


def _commissie(c: dict | None, naam_reserve: str | None) -> dict:
    c = c or {}
    return {"commissie": schoon(c.get("NaamNL") or naam_reserve) or None, "commissie_id": c.get("Id"),
            "commissie_afkorting": c.get("Afkorting"), "commissie_soort": schoon(c.get("Inhoudsopgave")) or None,
            "commissie_actief": _datum(c.get("DatumActief")), "commissie_inactief": _datum(c.get("DatumInactief"))}


def lees(pad: Path) -> dict:
    """→ {bron, uitgave, sha256, bestand, url, titel, records{sleutel: rec}, activiteiten{nummer: …},
    telling}. Alleen activiteiten met status 'Uitgevoerd' en een voortouwcommissie."""
    ruw = json.loads(pad.read_text(encoding="utf-8"))
    for veld in ("commissies", "activiteiten", "positionpapers", "opgehaald"):
        if veld not in ruw:
            raise FormaatFout(f"veld '{veld}' ontbreekt in {pad.name}")
    uitgave = ruw["opgehaald"]
    commissies = {c["Id"]: c for c in ruw["commissies"]}
    records: dict[str, dict] = {}
    activiteiten: dict[str, dict] = {}
    per_id: dict[str, dict] = {}
    tel: dict[str, int] = {}

    def tel_(k):
        tel[k] = tel.get(k, 0) + 1

    for a in ruw["activiteiten"]:
        if a.get("Status") != "Uitgevoerd":
            tel_(f"activiteit niet uitgevoerd ({a.get('Status')})")
            continue
        c = _commissie(commissies.get(a.get("Voortouwcommissie_Id")), a.get("Voortouwnaam"))
        if not c["commissie"]:
            tel_("activiteit zonder voortouwcommissie")
            continue
        dossiers = sorted({f"{k['Nummer']}{('-' + k['Toevoeging']) if k.get('Toevoeging') else ''} {schoon(k.get('Titel'))}"
                           for z in a.get("Zaak") or [] for k in z.get("Kamerstukdossier") or [] if k.get("Nummer")})
        act = {"nummer": a["Nummer"], "soort": a["Soort"], "onderwerp": schoon(a.get("Onderwerp")),
               "datum": _datum(a.get("Datum")), "besloten": a.get("Besloten"), "dossiers": dossiers, **c}
        activiteiten[a["Nummer"]] = act
        per_id[a["Id"]] = act
        basis = {**c, "activiteit": a["Nummer"], "activiteit_soort": a["Soort"], "onderwerp": act["onderwerp"],
                 "datum": act["datum"], "dossiers": dossiers}
        kop_regel = f"Tweede Kamer · {c['commissie']} · {a['Soort'].lower()} '{act['onderwerp']}' ({act['datum']}, {a['Nummer']})"
        if a["Soort"] in ("Gesprek", "Petitie", "Technische briefing"):
            wie = tegenpartij(a["Soort"], a.get("Onderwerp"))
            if wie:
                s = f"tegenpartij:{a['Nummer']}"
                records[s] = {**basis, "sleutel": s, "soort": "tegenpartij", "wie": wie, "kop": None,
                              "regel": f"Tweede Kamer · {c['commissie']} · {a['Soort'].lower()} ({act['datum']}, "
                                       f"{a['Nummer']}): {act['onderwerp']}"}
                tel_("record tegenpartij")
        for ap in sorted(a.get("Agendapunt") or [], key=lambda x: (x.get("Volgorde") or 0, x.get("Id") or "")):
            kop = schoon(ap.get("Onderwerp")) if _KOP.match(schoon(ap.get("Onderwerp"))) else None
            for regel in _regels(ap.get("Noot")):
                if _KOP.match(regel) and not _DOOR.search(regel):
                    kop = regel
                    continue
                wie = _genodigde(regel)
                if not wie:
                    tel_("notitieregel geen genodigde")
                    continue
                h = hashlib.sha1(f"{a['Nummer']}|{sleutel(regel)}".encode()).hexdigest()[:10]
                s = f"genodigde:{a['Nummer']}:{h}"
                if s in records:
                    continue
                records[s] = {**basis, "sleutel": s, "soort": "genodigde", "wie": wie, "kop": kop,
                              "regel": f"{kop_regel} · genodigde: {regel}"}
                tel_("record genodigde")
    for z in ruw["positionpapers"]:
        voortouw = [x for x in z.get("ZaakActor") or [] if x.get("Relatie") == "Voortouwcommissie"]
        c = _commissie(commissies.get(voortouw[0].get("Commissie_Id")) if voortouw else None,
                       voortouw[0].get("ActorNaam") if voortouw else None)
        if not c["commissie"]:
            tel_("position paper zonder commissie")
            continue
        wie, persoon = indiener(z.get("Onderwerp"))
        if not wie:
            tel_("position paper zonder herkenbare indiener")
            continue
        act = next((per_id[ap["Activiteit_Id"]] for ap in z.get("Agendapunt") or []
                    if ap.get("Activiteit_Id") in per_id), None)
        docs = sorted(z.get("Document") or [], key=lambda d: d.get("DocumentNummer") or "")
        datum = _datum(docs[0].get("Datum")) if docs else None
        datum = datum or _datum(z.get("GestartOp"))
        s = f"positionpaper:{z['Id']}"
        records[s] = {**c, "sleutel": s, "soort": "positionpaper", "wie": wie, "kop": None,
                      "indiener_persoon": persoon, "zaak": z.get("Nummer"),
                      "document": docs[0].get("DocumentNummer") if docs else None,
                      "activiteit": act["nummer"] if act else None,
                      "activiteit_soort": act["soort"] if act else None,
                      "onderwerp": schoon(z.get("Onderwerp")), "datum": datum,
                      "dossiers": act["dossiers"] if act else [],
                      "regel": f"Tweede Kamer · {c['commissie']} · position paper ({datum}, {z.get('Nummer')}): "
                               f"{schoon(z.get('Onderwerp'))}"}
        tel_("record position paper" + (" (persoon)" if persoon else ""))
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "titel": TITEL.format(uitgave=uitgave), "records": records, "activiteiten": activiteiten,
            "telling": dict(sorted(tel.items()))}


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


RELATIETYPES = {"lobbyt", "adviseur"}


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """Een inspraakfeit is organisatie → commissie ('lobbyt' of 'adviseur'): het doel is de
    voortouwcommissie uit het record (tk.commissie_naam), de bron staat in het deel van de regel waar
    de indiener, genodigde of tegenpartij staat (niet in het onderwerp), en die sprak namens de
    organisatie: geen privépersoon, geen onderzoeker of hoogleraar op eigen titel, geen oud-functie."""
    if relatie_type not in RELATIETYPES:
        return "een inspraakfeit is 'lobbyt' of 'adviseur' van de organisatie naar de commissie"
    if len(eindpunten) != 2 or not rec.get("commissie"):
        return "verband zonder twee eindpunten of record zonder commissie"
    bron_e, doel_e = eindpunten
    naam_c = tk.commissie_naam(rec)
    if doel_e["type"] != "overheidsinstelling" or doel_e["name"] != naam_c:
        return f"het doel #{doel_e['id']} is niet de {naam_c}"
    namen = [bron_e["name"]] + [v for v, m in tk.schrijfwijzen().items() if sleutel(m) == sleutel(bron_e["name"])]
    if not any(noemt(rec.get("wie") or "", n) for n in namen):
        return f"'{bron_e['name']}' staat niet als indiener, genodigde of tegenpartij in {sleutel_r}"
    pet, prive = hoedanigheid(rec, [bron_e["name"]])
    if prive:
        return f"{sleutel_r} gaat over een privépersoon"
    if pet not in ("leiding", "namens"):
        return f"{sleutel_r} is een optreden op eigen titel ({pet}), geen optreden namens de organisatie"
    if bron_e["type"] == "denktank" and rec["soort"] == "genodigde" and pet != "leiding":
        return f"{sleutel_r}: bij een denktank spreekt alleen de leiding namens het instituut (RfC 118)"
    return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Tweede Kamer: wie mag inspreken — uitgave ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--uitgave")
    ap.add_argument("--sinds", default=SINDS)
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal(a.sinds))
    else:
        d = lees(pad_van(a.uitgave) if a.uitgave else uitgaven()[-1])
        print(json.dumps({"uitgave": d["uitgave"], "activiteiten": len(d["activiteiten"]),
                          "records": len(d["records"]), **d["telling"]}, ensure_ascii=False, indent=1))
