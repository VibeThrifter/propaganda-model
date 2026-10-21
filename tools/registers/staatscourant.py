"""Staatscourant: benoemingsbesluiten — uitgave ophalen en lezen (eigen idee hoofdsessie 2026-10-20).

De Kroon, de ministerraad en de ministers benoemen de leden van adviescolleges, de besturen en
raden van toezicht van zbo's en toezichthouders, de raad van toezicht van de NPO en de leden van
staatscommissies. Die besluiten staan in de Staatscourant (voorbeeld: Stcrt. 2026, 26015, KB van
1 juli 2026: Aalbersberg voorzitter en Bredenoord lid van de raad van toezicht van de NPO).

Toegang: de open SRU-API van officielebekendmakingen.nl (KOOP), https://repository.overheid.nl/sru,
CQL op de metadata; per publicatie het XML-bestand uit de FRBR-repository. Officiële publicaties
zijn vrij van auteursrecht (art. 11 Auteurswet); hergebruik is vrij. Beleefd: één verzoek per
PAUZE seconden, eigen User-Agent. Zoekvragen (ZOEKVRAGEN):
  1. rubriek 'benoeming of ontslag' (dcterms.type, scheme OVERHEIDop.Rubriek);
  2. buiten die rubriek: een titel met benoeming/herbenoeming/benoemd/benoemen (veel ministeriële
     benoemingen staan onder 'ander besluit van algemene strekking' of 'interne regeling').
Privézaken vallen er vooraf uit (PRIVE: vereffenaars van nalatenschappen, curatoren, voogdij,
stembureauleden, gerechtelijke oproepingen).

Wat bewaard wordt (data/registers/staatscourant/staatscourant_<ophaaldatum>.json + .sha256): per
publicatie de metadata en de werkende tekst (de alinea's van het besluit, zonder toelichting) en
per benoeming, herbenoeming of ontslag één record. Woonplaats ('te Wassenaar'), geboortedatum en
-plaats, adressen en contactgegevens worden vóór het bewaren uit de tekst gehaald en nooit bewaard.
Een volgende uitgave bevat alleen publicaties die er nog niet waren (zoals agenda.py). De
recordsleutel hangt alleen af van publicatie, persoon, functie en organisatie. De recordregel is
het citaat: 'Staatscourant <jaar>, <nr> (<datum>; <benoemer>): <letterlijke besluittekst>'.

Extractie (deterministisch, geen AI): de besluitartikelen hebben vaste formuleringen ('wordt
benoemd tot …', 'te benoemen tot … van …', 'Tot lid van … wordt benoemd …', 'met ingang van …
voor een periode van …', 'De benoeming gaat in op … en eindigt op …'). Een alinea met een
benoemwerkwoord is een besluitalinea; functie en organisatie komen uit 'tot|als <functie> van
<organisatie>'; de personen staan in dezelfde alinea of in de opsomming erna (of, bij een
koninklijk besluit in uittreksel, in de alinea's ervoor). Wat niet eenduidig te lezen is, wordt geen
record maar staat met reden in 'overgeslagen' in de uitgave.

Geen schrijfacties op het model (dat doet staatscourant_naar_model.py via de REST-API).

    python3 tools/registers/staatscourant.py haal [--van 2023-01-01] [--cache DIR] [--max N]
    python3 tools/registers/staatscourant.py lees
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, UA, namen_van, noemt, ontleed_naam, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "staatscourant"
SRU = "https://repository.overheid.nl/sru"
URL = "https://zoek.officielebekendmakingen.nl"
MAP = DATA / BRON
UITGEVER = "Staatscourant (officielebekendmakingen.nl, KOOP)"
TITEL = ("Staatscourant, benoemingsbesluiten (rubriek 'benoeming of ontslag' en titels met benoeming), "
         "via de SRU-API van officielebekendmakingen.nl, uitgave {uitgave}")
LICENTIE = "Officiële publicatie: geen auteursrecht (art. 11 Auteurswet), hergebruik vrij"
BEGIN = "2023-01-01"
PAUZE = 1.0
OVERLAP_DAGEN = 21   # een volgende uitgave kijkt zo ver terug (late publicatie van metadata)
ZOEKVRAGEN = (
    'c.product-area==officielepublicaties AND w.publicatienaam=="Staatscourant" '
    'AND dt.type=="benoeming of ontslag" AND dt.date>={van}',
    'c.product-area==officielepublicaties AND w.publicatienaam=="Staatscourant" '
    'AND dt.title any "benoeming benoemingen herbenoeming herbenoemingen benoemd benoemen benoemingsbesluit" '
    'AND dt.type<>"benoeming of ontslag" AND dt.date>={van}',
)
PRIVE = re.compile(r"vereffenaar|nalatenschap|curator|voogdij|bewindvoerder|bewind\b|stembureau|"
                   r"oproep|erfgenam|faillissement|schuldsanering|ondercuratele|vermissing|vermist", re.I)
PRIVE_TYPES = {"gerechtelijke oproeping belanghebbenden"}
NS = {"sru": "http://docs.oasis-open.org/ns/search-ws/sruResponse", "dcterms": "http://purl.org/dc/terms/",
      "ow": "http://standaarden.overheid.nl/wetgeving/", "gzd": "http://standaarden.overheid.nl/sru"}


class FormaatFout(Exception):
    """De uitgave, de zoekvraag of een publicatie heeft niet het verwachte formaat."""


# ── tekst: datums, privacy ──────────────────────────────────────────────────
MAANDEN = {m: i for i, m in enumerate(("januari", "februari", "maart", "april", "mei", "juni", "juli",
                                       "augustus", "september", "oktober", "november", "december"), 1)}
_MAAND = "|".join(MAANDEN) + "|maaart"   # tikfout in Stcrt. 2023, 7023
DATUM = rf"(?:\d{{1,2}}(?:e|ste)?\s+(?:{_MAAND})\s+\d{{4}}|\d{{1,2}}-\d{{1,2}}-\d{{4}})"
GETALLEN = {"een": 1, "één": 1, "twee": 2, "drie": 3, "vier": 4, "vijf": 5, "zes": 6, "zeven": 7,
            "acht": 8, "negen": 9, "tien": 10, "twaalf": 12}


def iso(datum: str | None) -> str | None:
    """'1 juli 2026' / '13-5-2024' → '2026-07-01'; anders None."""
    if not datum:
        return None
    d = datum.lower().replace("maaart", "maart")
    m = re.match(r"(\d{1,2})(?:e|ste)?\s+([a-z]+)\s+(\d{4})", d)
    try:
        if m and m.group(2) in MAANDEN:
            return datetime.date(int(m.group(3)), MAANDEN[m.group(2)], int(m.group(1))).isoformat()
        m = re.match(r"(\d{1,2})-(\d{1,2})-(\d{4})", d)
        if m:
            return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None
    return None


_PLAATS = (r"(?:Berkel en Rodenrijs|Berg en Dal|Hoek van Holland|Nuenen, Gerwen en Nederwetten|Wijk en Aalburg|"
           r"(?:'s-|’s-|‘s-|'t\s|’t\s)?[A-ZÀ-Ý][\w’'\-]*(?:(?:\s+(?:aan|op|in|bij|de|den|der|het|ter|ten|a/d|"
           r"a\.d\.))*[\s\-]+[A-ZÀ-Ý][\w’'\-]*)*)")
_GEBOREN = re.compile(rf",?\s*geboren\s+(?:op\s+)?(?:{DATUM}|\d{{1,2}}-\d{{1,2}}-\d{{4}})(?:,?\s*(?:te|in)\s+{_PLAATS})?\s*,?",
                      re.I)
# 'te Wassenaar' na een naam: woonplaats. Niet na voorletters ('H.F.M. te Brake' is een tussenvoegsel).
_WOONPLAATS = re.compile(rf"(?<![A-ZÀ-Ý]\.)(?<!\))\s*,?\s+(?:wonende\s+|woonachtig\s+|wonend\s+|woonplaats:?\s+)?te\s+{_PLAATS}"
                         rf"(?:\s*\(gemeente\s+[^)]*\))?"
                         rf"(?=\s*(?:[,;:.()–•]|-\s|$|\s+(?:tot|als|met|en|per|voor|wordt|worden|benoemd|herbenoemd|"
                         rf"te\s+(?:her)?benoemen|in|op|onder|tevens|eervol|ontslag|werkzaam|namens|vanaf)\b))")
_WOONPLAATS_HAAKJES = re.compile(r"\s*\((?:woonplaats|wonende te|woonachtig te)[^)]*\)", re.I)
_WOONPLAATS_LOS = re.compile(rf",?\s*woonplaats\b:?(?:\s+{_PLAATS})?", re.I)
_POSTCODE = re.compile(r"\b[1-9]\d{3}\s?[A-Z]{2}\s+[A-ZÀ-Ý'’][\w'’\-]+")   # hoofdlettergevoelig: '2028 te' is geen postcode
_CONTACT = re.compile(r"\S+@\S+\.\w+|\b(?:tel(?:efoon)?|e-?mail|postbus)\b[.:]?\s*\d|\b0\d{1,3}[\s-]?\d{6,8}\b", re.I)


def contact(tekst: str) -> bool:
    """Staat er een adres, e-mailadres of telefoonnummer in? Zo'n alinea wordt nooit bewaard."""
    return bool(_POSTCODE.search(tekst) or _CONTACT.search(tekst))


def zonder_prive(tekst: str) -> str:
    """Woonplaats, geboortedatum en -plaats uit een alinea; 'te benoemen' blijft staan."""
    t = _GEBOREN.sub(",", tekst)
    t = _WOONPLAATS_HAAKJES.sub("", t)
    t = _WOONPLAATS.sub("", t)
    t = _WOONPLAATS_LOS.sub("", t)
    # 'De heer prof. dr. B.J. Kullberg, Nijmegen.': een opsommingsitem dat eindigt op een losse plaatsnaam
    m = PERSOON.match(re.sub(r"^\s*(?:[a-z]\.|\d+[.)°]|[–\-•·])\s*", "", t))
    if m:
        kop = len(t) - len(re.sub(r"^\s*(?:[a-z]\.|\d+[.)°]|[–\-•·])\s*", "", t))
        rest = t[kop + m.end():]
        if re.fullmatch(rf"\s*,\s*{_PLAATS}\s*[.;]?\s*", rest) and not re.search(
                r"(?i)raad|college|commissie|stichting|ministerie|universiteit|bank|autoriteit", rest):
            t = t[:kop + m.end()] + (";" if rest.strip().endswith(";") else "")
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r",\s*,", ",", t)
    return schoon(t).strip(" ,") if t.strip().endswith(",") and not tekst.strip().endswith(",") else schoon(t)


# ── personen ────────────────────────────────────────────────────────────────
_AANHEF = r"(?:[Dd]e\s+heer|[Hh]eer|[Mm]evrouw|[Mm]w\.|[Dd]hr\.|[Mm]evr\.|[Jj]hr\.|[Jj]onkheer|[Jj]onkvrouw|[Jj]kvr\.)"
_TITEL = (r"(?:(?:[Pp]rof|[Pp]rofessor|[Dd]r|[Mm]r|[Dd]rs|[Ii]r|[Ii]ng|[Dd]s|[Bb]c|[Ll]ic|[Ee]m)\.?\s*(?<=[.\s])|"
          r"(?:vice-?admiraal|luitenant-generaal|generaal-majoor|brigadegeneraal|generaal|admiraal|kolonel|"
          r"commodore|schout-bij-nacht|luitenant-admiraal|commandeur)\s+(?:b\.d\.\s+)?)")
_INIT = r"(?:(?:[A-ZÀ-Ý][a-z]{0,2}\.|IJ\.)\s?){1,7}(?:[A-ZÀ-Ý](?=\s+[A-ZÀ-Ý][a-z]))?"
_ROEP = r"(?:\(\s*[A-ZÀ-Ý][\w’'\-]+(?:\s[A-ZÀ-Ý][\w’'\-]+)?\s*\)\s*)"
_TUSSEN = (r"(?:(?:van|de|der|den|het|ten|ter|te|in|'t|’t|op|du|la|le|von|zu|da|di|del|dos|el|al|"
           r"Van|De|Der|Den|Ten|Ter|Te|In|Op|Du|La|Le|Von|Da|Di|Del|VAN|DE|DER|DEN|TEN|TER|TE)\s+)*")
_ACHTER = (r"[A-ZÀ-Ý][\w’'´`]*(?:-(?:(?:van|de|der|den|ten|ter|te|in|'t|’t|op)\s+)*[A-ZÀ-Ý][\w’'´`]*)*")
_NA = r"(?:\s+(?:MSc|MA|BA|MBA|LLM|LL\.M\.|RA|MPA|PhD|MD|MPH|MPM|BSc|EMIA|MCM|RC|MMC|CPA|EMFC|EMoC)\b\.?)*"
PERSOON = re.compile(
    rf"(?:{_AANHEF}\s+)?(?:{_TITEL})*{_INIT}\s*{_ROEP}?{_TUSSEN}{_ACHTER}{_NA}"
    rf"|{_AANHEF}\s+(?:{_TITEL})*(?:[A-ZÀ-Ý][a-zà-ÿ\-]+\s+){{1,3}}{_TUSSEN}{_ACHTER}{_NA}")
# Een alinea die alleen een volledige naam is (koninklijk besluit in uittreksel: 'Simone Margreet Roos,')
VOLLE_NAAM = re.compile(rf"^(?:{_AANHEF}\s+)?(?:{_TITEL})*((?:[A-ZÀ-Ý][a-zà-ÿ\-]+\s+){{1,4}}{_TUSSEN}{_ACHTER}){_NA}\s*[,;.]?$")
GEEN_ACHTERNAAM = {"minister", "staatssecretaris", "staatscourant", "raad", "college", "stichting", "commissie",
                   "besluit", "artikel", "koninkrijk", "nederland", "wet", "kaderwet", "onze", "de", "het", "nr",
                   "kenmerk", "bijlage", "afdeling", "directie", "ministerie", "dit", "deze", "lid", "leden",
                   "voorzitter", "secretaris", "president", "mevrouw", "heer", "bv", "nv", "ua", "vereniging",
                   "regeling", "instellingsbesluit", "benoemingsbesluit", "stcrt", "tevens", "werkzaam"}


def personen_in(tekst: str) -> list[tuple[int, int, str]]:
    """Persoonsvermeldingen (begin, eind, tekst) in een alinea, zonder 'Onze Minister' en wat geen
    achternaam heeft."""
    uit = []
    for m in PERSOON.finditer(tekst):
        s = m.group(0).strip()
        n = ontleed_naam(s)
        achter = sleutel(n["achternaam"] or "")
        if not achter or achter.split()[-1] in GEEN_ACHTERNAAM or len(achter) < 2:
            continue
        if not (n["voorletters"] or n["roepnaam"] or n["voornamen"]):
            continue
        # 'B.V.' / 'N.V.' / 'U.A.' is geen voorletter
        if re.fullmatch(r"(?:[BNU]\.?[VA]\.?)", (n["voorletters"] or "").replace(" ", "")):
            continue
        uit.append((m.start(), m.end(), s))
    return uit


_ITEM_REST = re.compile(r"^(?:tevens|als|tot|werkzaam|namens|op voordracht|voorgedragen|in de functie|lid|voorzitter|"
                        r"vicevoorzitter|plaatsvervangend|(?:met|en)\s|voor\s|vanaf|per\s|\(|vertegenwoordig|in zijn|"
                        r"in haar|vanuit|van\s|bij\s|deskundige|op grond|conform|[a-z]+\s+lid\b|ter\s|"
                        r"hem\s|haar\s|zijnde|thans|eerder|vertegenwoordiger)", re.I)
_NAAMSTAART = re.compile(r"(?:\s*(?:[–\-]\s*)?(?:(?:van|de|der|den|el|al|ten|ter|te|da|di|le|la|du)\s+)*"
                         r"[A-ZÀ-Ý][\w’'´`\-]*)+(?=\s*(?:[,;.(]|$|\s+(?:tevens|als|werkzaam|namens|en\s)))")
_ITEM_PERIODE = re.compile(rf"^(?:voor\s+)?(?:de\s+)?(?:periode\s+)?(?:van|vanaf|met ingang van|per)\s+{DATUM}"
                           rf"(?:\s+(?:tot(?:\s+en\s+met)?|t/m)\s+{DATUM})?\s*:\s*", re.I)


def persoon_item(tekst: str) -> list[str]:
    """Een opsommingsitem met één of meer personen ('de heer H.J. Dannenberg;', 'prof. mr. L. TIMMERMAN,
    tevens voorzitter;', 'Mevrouw E.C. Maas, werkzaam bij …', 'voor de periode van … tot …: de heer A en
    mevrouw B (beeldend kunstenaar);'): de namen, anders []."""
    t = re.sub(r"^\s*(?:[a-z]\.|\d+[.)°]|[–\-•·])\s*", "", tekst).strip()
    t = _ITEM_PERIODE.sub("", t)
    m = PERSOON.match(t)
    if m and personen_in(m.group(0)):
        rest = t[m.end():].strip(" ,;.")
        staart = _NAAMSTAART.match(rest) if rest and not _ITEM_REST.match(rest) else None
        if staart:   # 'Klein Nagelvoort – Schuit', 'Riani el Achhab': de naam loopt door
            rest2 = rest[staart.end():].strip(" ,;.")
            if not rest2 or _ITEM_REST.match(rest2):
                naam = schoon(f"{m.group(0)} {staart.group(0)}")
                return [naam]
        if not rest or _ITEM_REST.match(rest):
            namen = [m.group(0).strip()]
            # meer personen in hetzelfde item: 'de heer A (numismaat) en de heer B (beeldend kunstenaar)'
            for deel in re.split(r"\s*(?:;|,|\ben\b)\s*(?=(?:de heer|mevrouw|mw\.|dhr\.|mevr\.)\s)", rest, flags=re.I)[1:]:
                m2 = PERSOON.match(deel)
                if m2 and personen_in(m2.group(0)):
                    namen.append(m2.group(0).strip())
            return namen
        return []
    m = VOLLE_NAAM.match(t)
    if m and sleutel(m.group(1)).split()[-1] not in GEEN_ACHTERNAAM and not BENOEM.search(t) and not ORGDEEL.search(t):
        return [t.rstrip(",;.")]
    return []


# een kopje tussen de namen ('Beoordelingscommissie Beeldende Kunst') is geen persoon
ORGDEEL = re.compile(r"(?i)commissie|\braad\b|\braden\b|college|stichting|fonds|ministerie|instituut|bureau|autoriteit|"
                     r"vereniging|\bbank\b|universiteit|\bdienst\b|inspectie|agentschap|centrum|orgaan|platform|"
                     r"afdeling|sectie|directie|bestuur|\bkamer\b|\bteam\b|federatie|genootschap|academie|omroep")


# 'Jan-Willem Duijzer wordt herbenoemd als …': een volledige naam zonder voorletters vooraan de zin
NAAM_WORDT = re.compile(rf"^(?:{_AANHEF}\s+)?(?:{_TITEL})*((?:[A-ZÀ-Ý][a-zà-ÿ\-]+\s+){{1,3}}{_TUSSEN}{_ACHTER}){_NA}"
                        r"(?=\s*,?\s+(?:wordt|is)\b)")


# ── besluitalinea's ─────────────────────────────────────────────────────────
BENOEM = re.compile(r"\b(?:her)?benoem(?:d|en|t|ing)\b|\bbenoemingen\b|\bherbenoemingen\b", re.I)
HERBENOEM = re.compile(r"\bherbenoem|\bwordt?\s+(?:opnieuw|wederom)\s+benoemd|\bopnieuw\s+te\s+benoemen", re.I)
ONTSLAG = re.compile(r"\bontslag\b|\bontslagen\b|\bontslaan\b|\bontheven\b|\bontheffing van (?:de|het) (?:functie|lidmaatschap)", re.I)
SLOT = re.compile(r"^(?:dit besluit (?:treedt|wordt|zal)|onze minister|afschrift|een afschrift|"
                  r"dit besluit wordt|het besluit|de staatscourant)", re.I)
FUNCTIEWOORD = re.compile(
    r"\b(?:voorzitter|vicevoorzitter|vice-voorzitter|ondervoorzitter|lid|leden|bestuurder|directeur|"
    r"directeur-bestuurder|president|vicepresident|secretaris|secretaris-directeur|griffier|commissaris|"
    r"raadslid|kroonlid|collegelid|bestuurslid|staatsraad|ombudsman|toezichthouder|lid-beroepsgenoot|"
    r"lid-jurist|beroepslid|deskundige|adviseur|rapporteur|inspecteur-generaal|kwartiermaker|"
    r"plaatsvervanger|onderzoeker|commissielid|regeringscommissaris|gezant|ambassadeur|"
    r"(?:secretaris|directeur|inspecteur)-generaal|procureur-generaal|ombudsvrouw|ombudsman|rechter|raadsheer|"
    r"rechter-plaatsvervanger|raadsheer-plaatsvervanger|lid-deskundige|kamerlid|senator|vertegenwoordiger|"
    r"penningmeester|bestuursvoorzitter|algemeen directeur|hoofdingenieur-directeur|nationale ombudsman|"
    r"minister|staatssecretaris|ethicus|arts|jurist|gouverneur|gedeputeerde|burgemeester|"
    r"commissaris van de koning|rijksvertegenwoordiger|landsadvocaat|kanselier)\b", re.I)
LICHAAM = re.compile(r"^(?:de\s+|het\s+)?(?P<lichaam>raad van toezicht|raad van bestuur|raad van commissarissen|"
                     r"raad van advies|college van bestuur|dagelijks bestuur|algemeen bestuur|bestuur|directie|"
                     r"afdeling [\w\-]+|kamer [\w\-]+|sectie [\w\-]+|commissie van toezicht|"
                     r"auditcommissie|audit committee|selectie- en benoemingscommissie|benoemingscommissie|"
                     r"adviescommissie|(?:vaste\s+)?kamer)\s+(?:van|bij)\s+(?P<rest>.+)$", re.I)
_KOMMA = (r",(?!\s*tevens\b)(?!\s+[A-ZÀ-Ý][\w\-]+(?:,\s+[A-ZÀ-Ý][\w\-]+)*\s+en\s+[A-ZÀ-Ý])"   # 'Volksgezondheid, Welzijn en Sport'
          r"(?!\s+[a-zà-ÿ][\w\-]+\s+en\s+[a-zà-ÿ][\w\-]+(?:\s|$|[,.;:)]))")      # 'wetenschap, technologie en innovatie'
_EINDE_FO = (rf"(?=\s*(?::|;|\.\s|\.$|$|{_KOMMA})|\s+(?:te\s+)?(?:her)?benoem\w*|\s+(?:eervol\s+)?(?:te\s+)?ontsla\w*|"
             r"\s+wordt\b|\s+worden\b|\s+(?:zijn|is)\s+(?:her)?benoemd\b|"
             r"\s+voor\s+(?:de|een|het)\s+(?:periode|duur|termijn|zittingsperiode|tijdvak)|"
             r"\s+tussentijds\b|\s+(?:met|onder)\s+dankzegging|\s+(?:als\s+)?bedoeld\s+in\b|"
             r"\s+met ingang|\s+met terugwerkende|\s+per\s+\d|\s+te rekenen|\s+ingaande|\s+vanaf\s+\d|"
             r"\s+tot\s+(?:en met\s+)?\d|\s+onder\s+(?:dankzegging|toekenning)|\s+eervol|\s+op\s+eigen|"
             r"\s+(?:en|alsmede)\s+(?:aan|tot|wordt|worden|de\s+heer|mevrouw)\b|\s+(?:de\s+heer|mevrouw|mw\.|dhr\.)\s)")
FUNCTIE_ORG = re.compile(r"\b(?i:tot|als)\s+(?:het\s+|de\s+)?(?P<fo>.{3,220}?)" + _EINDE_FO, re.S)
_VAN = re.compile(r"\s+(?:van|bij|in|voor\s+(?=(?:de|het)\s+[A-ZÀ-Ý]))\s*(?:de\s+|het\s+)?")


def tussenzin(tekst: str) -> str:
    """'als lid, tevens voorzitter, van de …' → 'als lid tevens voorzitter van de …' (zelfde lengte niet nodig:
    wie posities gebruikt, gebruikt deze tekst)."""
    return re.sub(r",\s*(tevens\s+[\w\-/]+(?:\s+[\w\-/]+){0,3}?)\s*,\s*(?=(?:van|in|bij)\b)", r" \1 ", tekst)


def functie_org(tekst: str) -> tuple[str, str, int, int] | None:
    """'… tot voorzitter en lid van de raad van toezicht van de Nederlandse Publieke Omroep' →
    ('voorzitter en lid van de raad van toezicht', 'Nederlandse Publieke Omroep', begin, einde van de frase)."""
    tekst = tussenzin(tekst)
    for m in FUNCTIE_ORG.finditer(tekst):
        fo = m.group("fo").strip(" ,")
        for v in _VAN.finditer(fo):
            links, rechts = fo[:v.start()].strip(), fo[v.end():].strip(" ,.;:")
            if not FUNCTIEWOORD.search(links) or len(links.split()) > 9 or not rechts:
                continue
            functie, org = links, rechts
            for _ in range(2):   # 'raad van toezicht van de NPO', 'Afdeling rechtspraak van de RSJ'
                lm = LICHAAM.match(org)
                if not lm:
                    break
                lichaam = lm.group("lichaam")
                lidw = "het" if re.match(r"(?i)(?:dagelijks |algemeen )?bestuur|college|audit committee", lichaam) else "de"
                functie = f"{functie} van {lidw} {lichaam}"
                org = re.sub(r"^(?:de|het)\s+", "", lm.group("rest").strip(), flags=re.I)
            org = re.sub(r"\s*,\s*(?:tevens|als|in de|voor|met|die|welke|zoals|bedoeld).*$", "", org, flags=re.I)
            org = re.sub(r"\s+\((?:hierna|verder)[^)]*\)?", "", org).strip(" ,.;:")
            org = re.sub(r"^(?:de|het)\s+", "", org)
            functie = re.sub(r"^(?:respectievelijk|resp\.)\s+", "", functie, flags=re.I)
            functie = re.sub(r"^(?:her)?benoeming\s+(?:als|tot)\s+", "", functie, flags=re.I)
            functie = re.sub(r"\bleden\b", "lid", re.sub(r"\bexterne leden\b", "extern lid",
                                                            re.sub(r"\bonafhankelijke externe\b", "onafhankelijk extern", functie)))
            if len(org) < 3 or len(org.split()) > 16 or personen_in(org) or not re.search(r"[A-Za-zÀ-ÿ]{3}", org):
                continue
            return functie, org, m.start(), m.end()
    return None


GENERIEK = re.compile(r"^(?:staats|advies|begeleidings|toetsings)?(?:commissie|college|raad)$|^adviesorgaan$|"
                      r"^raad van (?:toezicht|bestuur|advies)$|^(?:dagelijks |algemeen )?bestuur$|^stichting$", re.I)
_LICHAAM_GEN = re.compile(r"^(?:raad van (?:toezicht|bestuur|advies)|(?:dagelijks |algemeen )?bestuur)$", re.I)
_TITEL_STOP = (r"(?=\s*(?:$|[,;()])|\s+en\s+(?:de\s+|het\s+)?(?:vergoeding|toekenning|vaststelling|bezoldiging|benoeming|"
               r"herbenoeming|ontslag|eervol|wijziging|instelling)\b|\s+(?:tot|houdende|ter|per|met ingang|alsmede)\b)")


def org_uit_titel(org: str, titel: str) -> tuple[str | None, str] | None:
    """'lid van de staatscommissie' of 'voorzitter van de Raad van Toezicht' zonder naam: de naam staat
    alleen in de titel ('… de staatscommissie overheidsingrijpen bij kindermishandeling en
    ontwikkelingsbedreiging en vergoeding …', '… de Raad van Toezicht van het Mondriaan Fonds') →
    (lichaam of None, naam). Alleen als de titel één niet-generieke naam geeft."""
    g = (org or "").strip()
    if not GENERIEK.match(g) or not titel:
        return None
    if _LICHAAM_GEN.match(g):
        m = re.search(rf"(?i)\b{re.escape(g)}\s+(?:van|bij)\s+(?:de\s+|het\s+)?(?P<naam>[^,;()]{{3,150}}?){_TITEL_STOP}", titel)
        if m:   # de eerste vermelding beslist; is die niet eenduidig, dan niets
            naam = m.group("naam").strip()
            return (g.lower(), naam) if not GENERIEK.match(naam) and re.search(r"[A-Za-zÀ-ÿ]{3}", naam) else None
        m = re.search(rf"(?i:\b{re.escape(g)})\s+(?P<naam>[A-Z][A-Za-z]{{1,7}})\b", titel)   # 'Raad van Advies ANVS'
        return (g.lower(), m.group("naam")) if m and m.group("naam").isupper() else None
    kern = re.escape(re.sub(r"(?i)^(?:staats|advies|begeleidings|toetsings)", "", g))
    citeer = re.search(r"\(([^()]*)\)\s*\.?\s*$", titel)
    for t in ([citeer.group(1)] if citeer else []) + [titel]:
        m = re.search(rf"(?i)\b(?P<naam>[\wÀ-ÿ\-]*{kern}\b[^,;()]{{0,150}}?){_TITEL_STOP}", t)
        if m:   # de eerste vermelding beslist ('de Adviescommissie tot benoeming van leden van de …': niets)
            naam = m.group("naam").strip(" .")
            return (None, naam) if not GENERIEK.match(naam) and len(naam.split()) <= 16 else None
    return None


_BIJZIN = re.compile(r"\b(?:de\s+)?(?:datum|dag)\s+(?:waarop|met ingang waarvan)\s+[^,.;:]*?\b(?:benoemd|beëdigd|ontslagen)"
                     r"(?:\s+en\s+daartoe\s+is\s+beëdigd)?", re.I)


def soort_van(tekst: str) -> str | None:
    """benoeming / herbenoeming / ontslag / None. Een alinea met beide: wat eerst staat. Een bijzin
    ('met ingang van de datum waarop hij door Ons tot Minister wordt benoemd') telt niet."""
    tekst = _BIJZIN.sub(" ", tekst)
    b, o = BENOEM.search(tekst), ONTSLAG.search(tekst)
    if not b and not o:
        return None
    if o and (not b or o.start() < b.start()):
        return "ontslag"
    return "herbenoeming" if HERBENOEM.search(tekst) else "benoeming"


def periode(tekst: str, publicatiedatum: str | None) -> dict:
    """Begin, einde en termijn zoals de tekst ze noemt (nooit verzonnen)."""
    t = re.sub(r"\s+", " ", tekst)
    uit = {"van": None, "tot": None, "tot_inclusief": None, "termijn": None}
    m = re.search(rf"\b(?:van|vanaf|periode|tijdvak)\s+({DATUM})\s+(?:tot\s+(en\s+met\s+)?|t/m\s+|tot en met\s+)({DATUM})",
                  t, re.I)
    if m:
        uit["van"], uit["tot"] = iso(m.group(1)), iso(m.group(3))
        uit["tot_inclusief"] = bool(m.group(2)) or " t/m " in m.group(0)
    if not uit["van"]:
        m = re.search(rf"\b(?:met ingang van|per|te rekenen (?:vanaf|van)|ingaande|vanaf|gaat in op|met terugwerkende "
                      rf"kracht tot(?: en met)?|werkt terug tot(?: en met)?|met ingang)\s+({DATUM})", t, re.I)
        if m:
            uit["van"] = iso(m.group(1))
    if not uit["van"] and publicatiedatum and re.search(
            r"met ingang van de (?:eerste\s+)?dag na (?:de datum van uitgifte|de dagtekening|de datum van "
            r"dagtekening|de publicatie|plaatsing)", t, re.I):
        d = datetime.date.fromisoformat(publicatiedatum) + datetime.timedelta(days=1)
        uit["van"], uit["van_afgeleid"] = d.isoformat(), "dag na publicatie"
    if not uit["tot"]:
        m = re.search(rf"\b(?:eindigt (?:op|met ingang van|per)|tot\s+(en\s+met\s+)?|t/m\s+)({DATUM})", t, re.I)
        if m and (not uit["van"] or iso(m.group(2)) != uit["van"]):
            uit["tot"], uit["tot_inclusief"] = iso(m.group(2)), bool(m.group(1)) or "t/m" in m.group(0)
    m = re.search(r"\b(?:voor|gedurende)\s+(?:een|de)\s+(?:(?:aaneengesloten|nieuwe|tweede)\s+)?"
                  r"(?:periode|duur|termijn|tijdvak|zittingsperiode|zittingstermijn)\s+van\s+(\w+)\s+(jaar|jaren|maanden|maand)",
                  t, re.I)
    if m:
        half = {"anderhalf": 18, "tweeënhalf": 30, "drieënhalf": 42}.get(m.group(1).lower())
        n = GETALLEN.get(m.group(1).lower()) or (int(m.group(1)) if m.group(1).isdigit() else None)
        if half and m.group(2).lower().startswith("ja"):
            uit["termijn"] = f"{half} maanden"
        elif n:
            uit["termijn"] = f"{n} {'jaar' if m.group(2).lower().startswith('ja') else 'maanden'}"
    return uit


def _plus(datum: str, termijn: str) -> str | None:
    n, eenheid = termijn.split()
    d = datetime.date.fromisoformat(datum)
    maanden = int(n) * (12 if eenheid == "jaar" else 1)
    j, mnd = divmod(d.month - 1 + maanden, 12)
    try:
        return d.replace(year=d.year + j, month=mnd + 1).isoformat()
    except ValueError:
        return (d.replace(year=d.year + j, month=mnd + 1, day=28)).isoformat()


# ── XML lezen ───────────────────────────────────────────────────────────────
WERKTEKST = {"regeling-tekst", "circulaire-tekst", "vrije-tekst"}
NIET_IN = {"nota-toelichting", "toelichting", "noot", "wijzig-artikel", "wijziging", "bijlage", "considerans",
           "aanhef", "regeling-sluiting", "circulaire-sluiting", "meta", "metadata"}


def _tekst(el) -> str:
    return schoon("".join(el.itertext()))


def alineas(root) -> list[str]:
    """De werkende tekst: elke <al> (buiten een opsomming) en elk <li> als één alinea, in volgorde,
    zonder toelichting, voetnoten, wijzigingsartikelen, aanhef en slot."""
    uit: list[str] = []

    def loop(el, binnen: bool):
        tag = el.tag
        if tag in NIET_IN:
            return
        binnen = binnen or tag in WERKTEKST
        if binnen and tag == "li":
            nr = el.find("li.nr")
            tekst = _tekst(el)
            if nr is not None and nr.text and tekst.startswith(schoon(nr.text)):
                tekst = tekst[len(schoon(nr.text)):].strip()
            uit.append(tekst)
            return
        if binnen and tag == "al":
            uit.append(_tekst(el))
            return
        for k in el:
            loop(k, binnen)

    loop(root, False)
    return [a for a in uit if a]


def lees_xml(inhoud: bytes, meta: dict) -> dict:
    """Eén publicatie → {meta, besluit, benoemer, alineas (zonder privé), benoemingen, overgeslagen}."""
    root = ET.fromstring(inhoud)
    intitule = root.find(".//intitule")
    titel = _tekst(intitule) if intitule is not None else ""
    if not titel:
        kop = next((_tekst(k) for k in root.iter("kop") if re.match(r"^(?:Besluit|Uittreksel|Benoeming|Regeling|KB)",
                                                                       _tekst(k))), "")
        titel = kop or meta.get("titel") or ""
    kb = root.find(".//koning") is not None or root.find(".//wij") is not None or bool(
        re.search(r"hebben goedgevonden en verstaan", _tekst(root), re.I))
    voordracht = next((_tekst(c) for c in root.iter("considerans.al")
                       if re.search(r"voordracht van", _tekst(c), re.I)), "")
    ondertekenaars = [schoon(_tekst(f)).rstrip(",") for f in root.iter("functie")
                      if re.search(r"minister|staatssecretaris|secretaris-generaal|directeur|bestuur|college|raad|"
                                   r"voorzitter|griffier|procureur", _tekst(f), re.I)]
    dag = root.find(".//dagtekening/datum")
    besluitdatum = (dag.get("isodatum") if dag is not None and dag.get("isodatum") else None) or iso(
        (re.search(rf"\b(?:Besluit|Regeling|Beschikking)\s+(?:van\s+(?:de|het)\s+[^,]*?\s+)?van\s+({DATUM})", titel)
         or [None, None])[1])
    if kb:
        m = re.search(r"voordracht van (?:Onze|de)\s+((?:Minister|Staatssecretaris)[^;]*?)"
                      r"(?=,(?!\s+[A-ZÀ-Ý][\w\-]+(?:,\s+[A-ZÀ-Ý][\w\-]+)*\s+en\s+[A-ZÀ-Ý])|\s+van\.?\s*\d|"
                      r"\s+van\s+\w+\s+\d|;|$)", voordracht)
        benoemer = "koninklijk besluit" + (f" op voordracht van de {m.group(1).strip()}" if m else "")
    else:
        benoemer = "; ".join(dict.fromkeys(re.sub(r"^(?:De|de)\s+", "", o) for o in ondertekenaars)) or \
            (meta.get("creator") or "onbekend")
    al = [z for z in (zonder_prive(a) for a in alineas(root) if not contact(a)) if z.strip(" ,;.:")]
    pub = {**meta, "titel": schoon(titel), "kb": kb, "benoemer": benoemer, "besluitdatum": besluitdatum,
           "alineas": al}
    if kieswet(pub):
        pub["benoemingen"], pub["overgeslagen"] = [], ["kieswetpublicatie (Kamerleden: tk.py, ep.py)"]
        return pub
    pub["benoemingen"], pub["overgeslagen"] = extraheer(pub)
    return pub


def kieswet(pub: dict) -> bool:
    """Benoemingen van Kamerleden en Europarlementariërs door een centraal stembureau: die staan
    al in het model via de registers van de Tweede Kamer en het Europees Parlement."""
    return bool(re.search(r"stembureau", pub.get("creator") or "", re.I) or pub.get("rubriek") == "kieswetpublicatie"
                or re.search(r"benoemd tot lid van (?:de Tweede Kamer|de Eerste Kamer|het Europees [Pp]arlement)|"
                             r"[Bb]enoeming(?:en)? (?:leden )?(?:Tweede|Eerste) ?Kamer", pub.get("titel") or ""))


def extraheer(pub: dict) -> tuple[list[dict], list[str]]:
    """De benoemingen uit de alinea's van één publicatie (zie de moduledoc)."""
    al = pub["alineas"]
    uit, mis = [], []
    gebruikt: set[int] = set()
    # publicatiebrede datums: 'De benoeming gaat in op …', 'Dit besluit treedt in werking met ingang van …'
    algemeen: dict = {}
    for a in al:
        if re.search(r"\b(?:de|deze)\s+(?:her)?benoeming(?:en)?\s+(?:gaat|gaan)\s+in|treedt in werking|werkt terug", a, re.I):
            for k, v in periode(a, pub.get("datum")).items():
                if v and not algemeen.get(k):
                    algemeen[k] = v
    for i in range(len(al)):
        a = al[i]
        if i in gebruikt or SLOT.match(a):
            continue
        soort = soort_van(a)
        if not soort:
            continue
        idx = [i]
        a = tussenzin(a)
        fo = functie_org(a)
        # 'te benoemen, voor de duur van 6 jaar,' + 'tot plaatsvervangend lid van het College …:'
        if not fo and i + 1 < len(al) and re.match(r"^(?:tot|als)\b", al[i + 1], re.I) and functie_org(al[i + 1]):
            a = f"{a} {al[i + 1]}"
            idx.append(i + 1)
            gebruikt.add(i + 1)
            fo = functie_org(a)
        uit_titel = False
        bewind = re.search(r"\btot\s+(Minister|Staatssecretaris)\s*:\s*$", a)
        if not fo and bewind:   # 'Met ingang van heden te benoemen tot Minister:' + per item het ministerie
            fo = (bewind.group(1), "", -1, -1)
        if not fo and (personen_in(a) or NAAM_WORDT.match(a) or a.rstrip().endswith(":")):
            fo = functie_org(pub["titel"])   # 'Met ingang van … wordt X benoemd.': de functie uit de titel
            uit_titel = bool(fo)
        if not fo:
            if personen_in(a):
                mis.append(f"geen functie/organisatie: {a[:160]}")
            continue
        functie, org, f_begin, f_eind = fo
        if uit_titel:
            f_begin = f_eind = -1
        ot = org_uit_titel(org, pub["titel"])
        if ot:   # de naam van het college staat alleen in de titel: de titel gaat mee in het citaat
            lichaam, org = ot
            if lichaam:
                lidw = "het" if re.match(r"(?:dagelijks |algemeen )?bestuur", lichaam) else "de"
                functie = f"{functie} van {lidw} {lichaam}"
            org_titel = True
        else:
            org_titel = False
        # personen: in de alinea (buiten de functie-organisatiefrase), dan de opsomming erna, dan ervoor
        items: list[tuple[str, int | None]] = [(p[2], None) for p in personen_in(a)
                                                if not (f_begin <= p[0] < f_eind)]
        if not items and NAAM_WORDT.match(a):
            items = [(NAAM_WORDT.match(a).group(0).strip(), None)]
        if not items:
            j = idx[-1] + 1
            while j < len(al) and len(items) < 80:
                namen = persoon_item(al[j])
                if not namen and ORGDEEL.search(al[j]) and len(al[j].split()) <= 8 and not soort_van(al[j]) \
                        and j + 1 < len(al) and persoon_item(al[j + 1]):
                    gebruikt.add(j)   # kopje tussen de namen
                    j += 1
                    continue
                if not namen:
                    break
                items += [(n, j) for n in namen]
                gebruikt.add(j)
                j += 1
        if not items:   # uittreksel: 'met ingang van …,' / 'Naam,' / 'te benoemen als lid van …'
            for j in range(i - 1, max(-1, i - 4), -1):
                if j in gebruikt or soort_van(al[j]):
                    break
                namen = persoon_item(al[j])
                if namen:
                    items += [(n, j) for n in namen]
                    gebruikt.add(j)
                    break
        if not items:
            mis.append(f"geen persoon: {a[:160]}")
            continue
        # datums: de alinea, de alinea's ervoor die alleen een datum zijn (uittreksel), dan publicatiebreed
        p = periode(a, pub.get("datum"))
        if not p["van"] and pub.get("besluitdatum") and re.search(
                r"\b(?:met ingang van|vanaf|per)\s+(?:heden|(?:de\s+)?(?:datum\s+van\s+)?dagtekening)\b", a, re.I):
            p["van"], p["van_afgeleid"] = pub["besluitdatum"], "besluitdatum ('heden'/'dagtekening')"
        if not p["van"]:
            for j in range(i - 1, max(-1, i - 4), -1):
                if re.match(rf"^\s*(?:met (?:ingang|terugwerkende kracht) (?:van|per|tot)|per|te rekenen vanaf)\s+{DATUM}\s*,?\s*$",
                            al[j], re.I):
                    p.update({k: v for k, v in periode(al[j], pub.get("datum")).items() if v})
                    idx.insert(0, j)
                    break
        for k in ("van", "tot", "termijn", "tot_inclusief", "van_afgeleid"):
            if not p.get(k) and algemeen.get(k):
                p[k] = algemeen[k]
        lichaam = re.search(r"\s+van de (?:raad|college|afdeling|bestuur|directie|kamer|sectie|commissie|audit).*$", functie)
        kern = functie[:lichaam.start()] if lichaam else functie
        resp = re.split(r"\s*(?:,|\ben\b)\s*", kern) if re.search(r"respectievelijk|resp\.", a, re.I) else None
        for n, (naam, j) in enumerate(items):
            f, o = functie, org
            if bewind and not org:
                mm = re.search(r"leiding van het (Ministerie van [^;,.]+?)(?:\s+en\s+(?:hem|haar)\b|[;,.]|$)",
                               al[j] if j is not None else "")
                if not mm:
                    continue
                o = mm.group(1)
            if resp and len(resp) == len(items):
                f = resp[n] + (lichaam.group(0) if lichaam else "")
            bron = al[j] if j is not None else a
            tevens = re.search(r"tevens\s+(voorzitter|vicevoorzitter|plaatsvervangend voorzitter|secretaris)", bron, re.I)
            if tevens and j is not None:
                f = f"{f} en {tevens.group(1).lower()}"
            # de eigen periode in een opsommingsitem ('voor de periode van … tot …: de heer …')
            q = dict(p)
            if j is not None and _ITEM_PERIODE.match(re.sub(r"^\s*(?:[a-z]\.|\d+[.)°]|[–\-•·])\s*", "", al[j])):
                q.update({k: v for k, v in periode(al[j], pub.get("datum")).items() if v})
            delen = [al[k] for k in sorted(set(idx + ([j] if j is not None else [])))]
            if re.fullmatch(r"(?i)(?:minister|staatssecretaris)", f.split(" van ")[0]) and o and not o.startswith("Ministerie"):
                o = f"Ministerie van {o}"   # 'tot Staatssecretaris van Financiën'
            uit.append({"persoon": naam, "functie": schoon(f), "organisatie": schoon(o), "soort": soort,
                        "van": q.get("van"), "tot": q.get("tot"), "tot_inclusief": q.get("tot_inclusief"),
                        "termijn": q.get("termijn"), "van_afgeleid": q.get("van_afgeleid"),
                        "functie_uit_titel": uit_titel,
                        "alineas": sorted(set(idx + ([j] if j is not None else []))),
                        "org_uit_titel": org_titel,
                        "tekst": schoon(" ".join(delen) if not (uit_titel or org_titel)
                                        else f"{pub['titel']} — {' '.join(delen)}")})
    return uit, mis


# ── ophalen ─────────────────────────────────────────────────────────────────
def uitgaven() -> list[Path]:
    return sorted(MAP.glob("staatscourant_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"staatscourant_{uitgave}.json"


def _get(url: str, timeout: int = 120) -> bytes:
    for poging in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404 or poging == 3:
                raise
            time.sleep(30 * (poging + 1) if e.code in (429, 503) else 5)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if poging == 3:
                raise
            time.sleep(10)
    raise FormaatFout(f"niet op te halen: {url}")


def zoek(van: str, meld=print) -> dict[str, dict]:
    """De publicaties van beide zoekvragen sinds `van`: id → metadata (titel, rubriek, ministerie,
    publicatiedatum, xml-url, vindplaats)."""
    uit: dict[str, dict] = {}
    for vraag in ZOEKVRAGEN:
        q, start, totaal = vraag.format(van=van), 1, None
        while totaal is None or start <= totaal:
            x = _get(f"{SRU}?" + urllib.parse.urlencode({"query": q, "maximumRecords": 1000, "startRecord": start}))
            root = ET.fromstring(x)
            if root.find(".//{http://docs.oasis-open.org/ns/search-ws/diagnostic}message") is not None:
                raise FormaatFout(f"SRU-diagnose bij zoekvraag {q!r}")
            totaal = int(root.findtext("sru:numberOfRecords", namespaces=NS) or 0)
            recs = root.findall(".//sru:record", NS)
            for r in recs:
                def g(p):
                    e = r.find(p, NS)
                    return schoon(e.text) if e is not None and e.text else None
                pid = g(".//dcterms:identifier")
                if not pid or not pid.startswith("stcrt-"):
                    continue
                uit.setdefault(pid, {"id": pid, "titel_meta": g(".//dcterms:title"), "rubriek": g(".//dcterms:type"),
                                     "creator": g(".//dcterms:creator"), "datum": g(".//dcterms:date"),
                                     "onderwerp": g(".//dcterms:subject"), "xml": g(".//gzd:url"),
                                     "vindplaats": g(".//gzd:preferredUrl") or f"{URL}/{pid}.html",
                                     "zoekvraag": ZOEKVRAGEN.index(vraag) + 1})
            meld(f"  zoekvraag {ZOEKVRAGEN.index(vraag) + 1}: {min(start + len(recs) - 1, totaal)}/{totaal}")
            if not recs:
                break
            start += len(recs)
            time.sleep(PAUZE)
    return uit


def prive(meta: dict) -> bool:
    return bool(PRIVE.search(meta.get("titel_meta") or "")) or (meta.get("rubriek") or "") in PRIVE_TYPES


def bekend() -> set[str]:
    """Publicaties die al in een uitgave staan; een mislukte ophaling (fout) wordt opnieuw geprobeerd."""
    ids = set()
    for p in uitgaven():
        ids |= {k for k, v in json.loads(p.read_text(encoding="utf-8"))["publicaties"].items() if "fout" not in v}
    return ids


def _sleutel(pid: str, b: dict) -> str:
    n = ontleed_naam(b["persoon"])
    h = hashlib.sha1("|".join(sleutel(x) for x in (pid, n["voorletters"] or n["roepnaam"] or "", n["achternaam"] or "",
                                                     b["functie"], b["organisatie"], b["soort"])).encode()).hexdigest()[:12]
    return f"{b['soort']}:{pid}:{h}"


def _datum_nl(iso_d: str | None) -> str:
    if not iso_d:
        return "?"
    d = datetime.date.fromisoformat(iso_d)
    return f"{d.day} {list(MAANDEN)[d.month - 1]} {d.year}"


_OO: dict = {}


def oo_index() -> dict:
    """Naam (sleutel, ook zonder 'Stichting', '&' als 'en') en afkorting → (oo_id, naam) uit de nieuwste
    bewaarde uitgave van het register van overheidsorganisaties; alleen wat één organisatie aanwijst.
    Delen meer organisaties een naam, dan telt eerst alleen wat nog bestaat en daarna alleen wat geen
    organisatieonderdeel is ('Politieacademie' is een zbo en een onderdeel met dezelfde naam)."""
    if _OO:
        return _OO
    import oo
    if not oo.uitgaven():
        _OO["_uitgave"] = None
        return _OO
    uitgave = oo.uitgaven()[-1].stem.split("_", 1)[1]
    per: dict[str, set] = {}
    for o in oo.lees_uitgave(uitgave)["organisaties"].values():
        for n in {o["naam"], re.sub(r"^Stichting\s+", "", o["naam"])} | ({o["afkorting"]} if o.get("afkorting") else set()):
            for k in namen_van(n.replace("&", " en ")):
                per.setdefault(k, set()).add((o["oo_id"], o["naam"], (o.get("types") or [""])[0], bool(o.get("eind"))))
    for k, v in per.items():
        if len(k) < 3:
            continue
        for filt in (lambda x: True, lambda x: not x[3], lambda x: not x[3] and x[2] != "Organisatieonderdeel"):
            w = {x for x in v if filt(x)}
            if len(w) == 1:
                _OO[k] = next(iter(w))[:2]
                break
            if not w:
                break
    _OO["_uitgave"] = uitgave
    return _OO


def oo_koppeling(org: str) -> tuple[str, str] | None:
    """De organisatie uit de besluittekst → (oo_id, naam in het register), op exacte naam; anders None."""
    idx = oo_index()
    for kand in org_varianten(org):
        k = sleutel(kand.replace("&", " en "))
        if k in idx:
            return idx[k]
    return None


def org_varianten(org: str) -> list[str]:
    """De naam zoals de tekst hem geeft, zonder rechtsvorm ('N.V.', 'B.V.'), zonder 'Stichting', en bij
    'Naam (AFK)' ook de naam en de afkorting apart (alleen als het een afkorting is)."""
    uit = [org]
    kaal = re.sub(r"\s*,?\s+(?:N\.?\s?V|B\.?\s?V)\.?$", "", org).strip()
    uit.append(kaal)
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", kaal)
    if m:
        uit.append(m.group(1))
        if re.fullmatch(r"[A-Z][A-Za-z&\-]{1,9}", m.group(2).strip()):
            uit.append(m.group(2).strip())
    uit += [re.sub(r"^(?:Stichting|stichting)\s+", "", u) for u in list(uit)]
    uit += [re.sub(r"^Ministerie van\s+", "", u) for u in list(uit) if u.startswith("Ministerie van ")]   # register: 'Financiën'
    return [u for u in dict.fromkeys(x.strip() for x in uit) if len(u) >= 2]


def maak_records(pub: dict) -> dict[str, dict]:
    uit = {}
    jaar, nr = re.match(r"stcrt-(\d{4})-(.+)$", pub["id"]).groups()
    for b in pub["benoemingen"]:
        s = _sleutel(pub["id"], b)
        n = ontleed_naam(b["persoon"])
        tot = b.get("tot") or (_plus(b["van"], b["termijn"]) if b.get("van") and b.get("termijn") else None)
        regel = (f"Staatscourant {jaar}, {nr} ({_datum_nl(pub.get('datum'))}; {pub['benoemer']}): {b['tekst']}")
        uit[s] = {"sleutel": s, "soort": b["soort"], "publicatie": pub["id"], "publicatiedatum": pub.get("datum"),
                  "besluitdatum": pub.get("besluitdatum"), "kb": pub["kb"], "benoemer": pub["benoemer"],
                  "ministerie": pub.get("creator"), "rubriek": pub.get("rubriek"), "vindplaats": pub["vindplaats"],
                  "persoon": b["persoon"], "voorletters": n["voorletters"], "roepnaam": n["roepnaam"],
                  "voornamen": n["voornamen"], "achternaam": schoon(f"{n['tussenvoegsel'] or ''} {n['achternaam'] or ''}"),
                  "weergave": n["weergave"], "functie": b["functie"], "organisatie": b["organisatie"],
                  "van": b.get("van"), "van_afgeleid": b.get("van_afgeleid"), "tot": tot,
                  "tot_uit_termijn": bool(tot and not b.get("tot")), "termijn": b.get("termijn"),
                  "functie_uit_titel": b.get("functie_uit_titel", False), "regel": regel}
        k = oo_koppeling(b["organisatie"]) if b["organisatie"] else None
        if k:
            uit[s].update(oo_id=k[0], oo_naam=k[1], oo_uitgave=oo_index()["_uitgave"])
    return uit


def haal(van: str | None = None, cache: Path | None = None, max_n: int | None = None, meld=print) -> Path:
    """Nieuwe publicaties sinds `van` (eerste keer BEGIN, daarna de laatste uitgave min OVERLAP_DAGEN)
    ophalen, lezen en als nieuwe uitgave bewaren. `cache`: map met eerder opgehaalde XML-bestanden
    (<id>.xml); ontbreekt een bestand, dan wordt het opgehaald (en daar bewaard). Hervat na een
    onderbreking via data/registers/staatscourant/_bezig.json (alleen de gelezen, opgeschoonde tekst)."""
    MAP.mkdir(parents=True, exist_ok=True)
    vandaag = datetime.date.today().isoformat()
    if van is None:
        van = BEGIN if not uitgaven() else (datetime.date.fromisoformat(uitgaven()[-1].stem.split("_")[1])
                                             - datetime.timedelta(days=OVERLAP_DAGEN)).isoformat()
    al_bekend = bekend()
    lijst = zoek(van, meld)
    nieuw = {k: m for k, m in sorted(lijst.items()) if k not in al_bekend}
    privé = {k for k, m in nieuw.items() if prive(m)}
    meld(f"{len(lijst)} publicaties sinds {van}; {len(nieuw)} nieuw, waarvan {len(privé)} privé (overgeslagen)")
    bezig_pad = MAP / "_bezig.json"
    bezig = json.loads(bezig_pad.read_text(encoding="utf-8")) if bezig_pad.exists() else {}
    if bezig.get("datum") != vandaag:
        bezig = {"datum": vandaag, "publicaties": {}}
    te_lezen = [k for k in nieuw if k not in privé and k not in bezig["publicaties"]]
    if max_n is not None:
        te_lezen = te_lezen[:max_n]
    for i, pid in enumerate(te_lezen, 1):
        m = nieuw[pid]
        bestand = Path(cache) / f"{pid}.xml" if cache else None
        if bestand is not None and bestand.exists():
            inhoud = bestand.read_bytes()
        else:
            time.sleep(PAUZE)
            try:
                inhoud = _get(m["xml"])
            except urllib.error.HTTPError as e:
                bezig["publicaties"][pid] = {**m, "fout": e.code}
                continue
            if bestand is not None:
                bestand.parent.mkdir(parents=True, exist_ok=True)
                bestand.write_bytes(inhoud)
        try:
            bezig["publicaties"][pid] = lees_xml(inhoud, m)
        except ET.ParseError as e:
            bezig["publicaties"][pid] = {**m, "fout": f"xml: {e}"}
        if i % 100 == 0 or i == len(te_lezen):
            bezig_pad.write_text(json.dumps(bezig, ensure_ascii=False), encoding="utf-8")
            meld(f"  gelezen: {i}/{len(te_lezen)}")
    publicaties = {k: v for k, v in bezig["publicaties"].items() if k in nieuw}
    if not publicaties:
        meld("geen nieuwe publicaties")
        return uitgaven()[-1] if uitgaven() else None
    records: dict[str, dict] = {}
    for pid, pub in sorted(publicaties.items()):
        if "fout" not in pub:
            records.update(maak_records(pub))
    pad = pad_van(vandaag)
    if pad.exists():
        raise FormaatFout(f"uitgave {vandaag} bestaat al; een uitgave wordt nooit overschreven")
    pad.write_text(json.dumps({"bron": BRON, "uitgave": vandaag, "opgehaald": vandaag, "van": van,
                               "zoekvragen": [q.format(van=van) for q in ZOEKVRAGEN], "licentie": LICENTIE,
                               "volledig": max_n is None, "prive_overgeslagen": len(privé),
                               "publicaties": publicaties, "records": records},
                              ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    (MAP / f"staatscourant_{vandaag}.sha256").write_text(sha256_bestand(pad) + "\n")
    if max_n is None:
        bezig_pad.unlink(missing_ok=True)
    return pad


# ── lezen (ook voor de registercheck) ──────────────────────────────────────
def lees(pad: Path) -> dict:
    data = json.loads(pad.read_text(encoding="utf-8"))
    if data.get("bron") != BRON or not isinstance(data.get("records"), dict):
        raise FormaatFout(f"{pad.name} is geen Staatscourant-uitgave")
    return {**data, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "titel": TITEL.format(uitgave=data["uitgave"])}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"staatscourant_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


# Organisaties die de Staatscourant anders noemt dan het model of het register van
# overheidsorganisaties: schrijfwijze (sleutel) → naam in het model. Met de hand nagelopen.
SCHRIJFWIJZEN = {
    "stichting etherreclame": "Ster",
    "stichting etherreclame ster": "Ster",
    "nederlandse omroep stichting": "NOS",
    "nederlandse publieke omroep": "NPO",
    "stichting nederlandse publieke omroep": "NPO",
    "nederlandse publieke omroep npo": "NPO",
}
RELATIETYPES = {"ambt", "bestuurder", "adviseur", "lidmaatschap"}


def org_namen(rec: dict) -> list[str]:
    """De organisatie uit het record en de vastgelegde schrijfwijze ervan."""
    uit = [rec["organisatie"]]
    for v in org_varianten(rec["organisatie"] or ""):
        if sleutel(v) in SCHRIJFWIJZEN and SCHRIJFWIJZEN[sleutel(v)] not in uit:
            uit.append(SCHRIJFWIJZEN[sleutel(v)])
    return uit


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """Een benoeming, herbenoeming of ontslag (dat de functie bevestigt) is persoon → organisatie
    (ambt/bestuurder/adviseur/lidmaatschap). De persoon: de achternaam uit het record staat in de naam, en de voornaam
    begint met de eerste voorletter (of is de roepnaam). De organisatie: haar oo-id is die uit het
    record (oo_id, vastgelegd door de import), of haar naam staat in de organisatie uit het record
    (ook de vastgelegde schrijfwijze, SCHRIJFWIJZEN)."""
    if rec["soort"] not in ("benoeming", "herbenoeming", "ontslag") or relatie_type not in RELATIETYPES:
        return f"een Staatscourant-feit is een (her)benoeming persoon → organisatie, niet '{relatie_type}' ({rec['soort']})"
    personen = [e for e in eindpunten if e["type"] == "persoon"]
    if len(personen) != 1:
        return "precies één eindpunt moet een persoon zijn"
    p = personen[0]
    achter = sleutel(rec.get("achternaam") or "")
    naam = sleutel(re.sub(r"\([^)]*\)", " ", p["name"]))
    if not achter or f" {achter} " not in f" {naam} ":
        # dubbele achternaam ('Vletter-van Dort'): één deel volstaat als het het eerste is
        delen = [d for d in re.split(r"[\s\-]+", achter) if len(d) > 2]
        if not delen or f" {delen[0]} " not in f" {naam} ":
            return f"de achternaam '{rec.get('achternaam')}' staat niet in '{p['name']}'"
    eerste = naam.split()[0] if naam.split() else ""
    roep = sleutel(rec.get("roepnaam") or rec.get("voornamen") or "")
    letters = re.sub(r"[^a-z]", "", (rec.get("voorletters") or "").lower())
    if roep and eerste == roep.split()[0]:
        pass
    elif letters and eerste[:1] != letters[:1] and not re.fullmatch(r"[a-z]\.?", eerste):
        return f"de voornaam van '{p['name']}' past niet bij '{rec['persoon']}'"
    org = [e for e in eindpunten if e is not p][0]
    if rec.get("oo_id") and ("oo", rec["oo_id"]) in org["ids"]:
        return None
    if any(noemt(n, org["name"]) or sleutel(n) in namen_van(org["name"]) for n in org_namen(rec)):
        return None
    return f"'{org['name']}' is niet de organisatie '{rec['organisatie']}' uit {sleutel_r}"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Staatscourant-benoemingen ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--van", help="YYYY-MM-DD (standaard: BEGIN of de laatste uitgave min de overlap)")
    ap.add_argument("--cache", help="map met al opgehaalde XML-bestanden (<id>.xml)")
    ap.add_argument("--max", type=int, default=None, help="hooguit N publicaties (proef)")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal(a.van, Path(a.cache) if a.cache else None, a.max))
    else:
        tel = Counter()
        for p in uitgaven():
            d = lees(p)
            tel[f"{d['uitgave']} publicaties"] = len(d["publicaties"])
            for r in d["records"].values():
                tel[f"{d['uitgave']} {r['soort']}"] += 1
        print(json.dumps(tel, ensure_ascii=False, indent=1))
