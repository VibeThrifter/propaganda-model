#!/usr/bin/env python3
"""
Genormaliseerde profiel-laag — het contract tussen de scraper en het model.

Waarom een tussenlaag? De scrape-kant (`scrape_profile.py`, Playwright + de
`linkedin_scraper`-bibliotheek) is fragiel en tegen LinkedIn's voorwaarden; ze
verandert per bibliotheekversie en kan zomaar breken. De model-kant
(`linkedin_naar_model.py`, dient voorstellen in via de REST-API) is de waardevolle,
testbare helft. Door beide te laten praten via één **genormaliseerd profiel-JSON**
staat de mapper los van welke scraper je gebruikt: breekt `linkedin_scraper`, dan
schrijf je met wat dan ook hetzelfde JSON en de mapper werkt ongewijzigd door.

Deze module is **pure stdlib** (geen Playwright, geen Pydantic) zodat de mapper en de
tests draaien zonder browser. `scrape_profile.py` importeert hem óók, om een
gescrapet Person/Company-object (of een dict) om te zetten naar dit schema.

Genormaliseerd profielschema (persoon):
    {
      "type": "persoon",
      "bron": {"linkedin_url": "...", "gescraped_op": "YYYY-MM-DD"},
      "persoon": {"naam": "...", "kop": "...", "locatie": "...", "over": "..."},
      "ervaringen":     [{"organisatie","functie","van","tot","duur","locatie",
                          "beschrijving","linkedin_url"}],
      "opleidingen":    [{"instelling","graad","van","tot","beschrijving"}],
      "lidmaatschappen":[{"organisatie","rol","herkomst"}]
    }

Alle datums zijn strings ("2015", "2015-07") of null (lopend/onbekend); de
`entities`/`relations`-tabellen bewaren `active_from`/`active_until` óók als TEXT, dus
gedeeltelijke datums mogen.
"""
from __future__ import annotations

import datetime
import re

# --- Verlopen-sessie: gedeelde, agent-bewuste instructie ------------------------
# De LinkedIn-login is een HANDMATIGE, headful stap (evt. 2FA/CAPTCHA) die alleen de
# eigenaar (een mens) kan doen — een agent kan dit principieel niet zelf. Beide trappen
# (scraper + mapper) tonen daarom deze exacte tekst wanneer de sessie verlopen blijkt,
# zodat een agent 'm herkent en de opdracht dóórgeeft aan de eigenaar i.p.v. te blijven
# proberen of stil niets te doen.
SESSIE_LOGIN_COMMANDO = "python3 tools/linkedin/scrape_profile.py login"


def sessie_verlopen_bericht(reden: str = "") -> str:
    """De canonieke 'sessie verlopen'-melding. `reden` = één regel context erboven."""
    regels = ["⚠ LINKEDIN-SESSIE VERLOPEN — actie voor de eigenaar (mens), niet voor een agent."]
    if reden:
        regels.append(reden)
    regels.append("Een agent kan hier niet zelf inloggen (handmatige LinkedIn-login, evt. "
                  "2FA/CAPTCHA). Geef de eigenaar deze opdracht en probeer daarna opnieuw:")
    regels.append(f"    {SESSIE_LOGIN_COMMANDO}")
    return "\n".join(regels)


# --- Functie → relatietype (uit BRUG_AFFILIATIE, zie CLAUDE.md) -----------------
# Een gedateerde persoon→organisatie-affiliatie is een instantie van
# `draaideurconstructie`. Het relatietype nuanceert de aard van de band; het
# CHECK-enum in schema.sql accepteert precies deze waarden.
# Stammen (open eind) alleen voor lange, distinctieve woorden: 'bestuur' vangt óók
# 'bestuurslid'/'bestuurder'. Korte acroniemen (ceo/cfo/coo/cto) blijven woord-gebonden,
# anders matcht 'coo' binnen 'coordinator'.
_BESTUUR_STAM = re.compile(r"\b(bestuur|commissar|toezichthoud|oprichter|directeur)", re.I)
_BESTUUR_TOK = re.compile(
    r"\b(voorzitter|board|chair|ceo|cfo|coo|cto|president|managing director|partner"
    r"|founder|owner|eigenaar|raad van (?:toezicht|bestuur|commissarissen))\b", re.I)
_ADVIES = re.compile(r"\b(advies|adviseur|advisor|adviser|consultant|councillor)", re.I)
_WOORDVOERDER = re.compile(
    r"\b(woordvoerd|persvoorlicht|spokesperson|spokesman|press officer"
    r"|communicatieadviseur|public affairs|persvoorlichting)", re.I)
# 'vrijwillig'/'volunteer' als stam (vrijwilliger); 'lid'/'member' met sluit-\b.
_VRIJWILLIG = re.compile(r"\b(?:vrijwillig|volunteer)|\b(?:lid|member)\b", re.I)


def relatietype_voor_functie(functie: str | None) -> str:
    """Kies het BRUG_AFFILIATIE-relatietype dat het best bij de functietitel past.

    Volgorde is specifiek → generiek; default = 'personeel' (werkgever-werknemer).
    """
    f = (functie or "").strip()
    if not f:
        return "personeel"
    if _WOORDVOERDER.search(f):
        return "woordvoerder_van"
    if _BESTUUR_STAM.search(f) or _BESTUUR_TOK.search(f):
        return "bestuurder"
    if _ADVIES.search(f):
        return "adviseur"
    if _VRIJWILLIG.search(f):
        return "lidmaatschap"
    return "personeel"


# --- Datum-normalisatie ---------------------------------------------------------
_MAANDEN = {
    # NL
    "jan": 1, "januari": 1, "feb": 2, "februari": 2, "mrt": 3, "maart": 3,
    "apr": 4, "april": 4, "mei": 5, "jun": 6, "juni": 6, "jul": 7, "juli": 7,
    "aug": 8, "augustus": 8, "sep": 9, "sept": 9, "september": 9, "okt": 10,
    "oktober": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
    # EN
    "january": 1, "february": 2, "march": 3, "june": 6, "july": 7,
    "august": 8, "october": 10, "december ": 12,
}
_LOPEND = re.compile(r"^(present|heden|current|now|nu|tot heden)$", re.I)


def normaliseer_datum(waarde: str | None) -> str | None:
    """"Jul 2015" / "juli 2015" / "2015" / "Present" → "2015-07" / "2015" / None.

    Geeft None terug voor lopend/leeg/onparsbaar — dat betekent in het model
    "onbegrensd voor zover bekend" (active_until NULL).
    """
    s = (waarde or "").strip()
    if not s or _LOPEND.match(s):
        return None
    # Zuiver jaartal
    m = re.fullmatch(r"(\d{4})", s)
    if m:
        return m.group(1)
    # "maand jaar" in willekeurige volgorde
    jaar = re.search(r"(\d{4})", s)
    maand = None
    for token in re.split(r"[\s.,/-]+", s.lower()):
        if token in _MAANDEN:
            maand = _MAANDEN[token]
            break
    if jaar and maand:
        return f"{jaar.group(1)}-{maand:02d}"
    if jaar:
        return jaar.group(1)
    return None


def _attr(obj, naam, default=None):
    """Leest een veld duck-typed: werkt op een Pydantic-object én op een dict.

    Zo overleeft de omzetting kleine versieverschillen in `linkedin_scraper`
    (een ontbrekend veld wordt gewoon None) zonder de mapper te breken.
    """
    if isinstance(obj, dict):
        return obj.get(naam, default)
    return getattr(obj, naam, default)


def _schoon(waarde) -> str | None:
    if waarde is None:
        return None
    s = str(waarde).strip()
    return s or None


def persoon_naar_profiel(person, linkedin_url: str | None = None,
                         gescraped_op: str | None = None) -> dict:
    """Zet een `linkedin_scraper` Person (of een gelijkvormige dict) om naar het
    genormaliseerde profielschema. Kent alle velden duck-typed toe, dus dit werkt
    ook als een veld in jouw scraper-versie anders heet of ontbreekt."""
    gescraped_op = gescraped_op or datetime.date.today().isoformat()
    url = linkedin_url or _attr(person, "linkedin_url")

    ervaringen = []
    for exp in _attr(person, "experiences", []) or []:
        org = _schoon(_attr(exp, "institution_name"))
        if not org:
            continue  # zonder organisatie geen edge
        ervaringen.append({
            "organisatie": org,
            "functie": _schoon(_attr(exp, "position_title")),
            "van": normaliseer_datum(_attr(exp, "from_date")),
            "tot": normaliseer_datum(_attr(exp, "to_date")),
            "duur": _schoon(_attr(exp, "duration")),
            "locatie": _schoon(_attr(exp, "location")),
            "beschrijving": _schoon(_attr(exp, "description")),
            "linkedin_url": _schoon(_attr(exp, "linkedin_url")),
        })

    opleidingen = []
    for edu in _attr(person, "educations", []) or []:
        inst = _schoon(_attr(edu, "institution_name"))
        if not inst:
            continue
        opleidingen.append({
            "instelling": inst,
            "graad": _schoon(_attr(edu, "degree")),
            "van": normaliseer_datum(_attr(edu, "from_date")),
            "tot": normaliseer_datum(_attr(edu, "to_date")),
            "beschrijving": _schoon(_attr(edu, "description")),
        })

    # Lidmaatschappen: alleen 'Organizations'/vrijwilligerswerk uit accomplishments.
    # Interesses (List[str]) zijn *volgen*, geen lidmaatschap → bewust weggelaten
    # (dat zou overfit zijn: een bedrijf volgen ≠ er lid van zijn).
    lidmaatschappen = []
    for acc in _attr(person, "accomplishments", []) or []:
        cat = (_schoon(_attr(acc, "category")) or "").lower()
        titel = _schoon(_attr(acc, "title"))
        if not titel:
            continue
        if any(k in cat for k in ("organi", "vrijwillig", "volunteer", "member", "lid")):
            lidmaatschappen.append({
                "organisatie": titel,
                "rol": None,
                "herkomst": f"accomplishment:{cat}",
            })

    return {
        "type": "persoon",
        "bron": {"linkedin_url": url, "gescraped_op": gescraped_op},
        "persoon": {
            "naam": _schoon(_attr(person, "name")),
            "kop": _schoon(_attr(person, "headline")),  # niet in elke versie aanwezig
            "locatie": _schoon(_attr(person, "location")),
            "over": _schoon(_attr(person, "about")),
        },
        "ervaringen": ervaringen,
        "opleidingen": opleidingen,
        "lidmaatschappen": lidmaatschappen,
    }


def bedrijf_naar_profiel(company, linkedin_url: str | None = None,
                         gescraped_op: str | None = None) -> dict:
    """Genormaliseerd bedrijfsprofiel — als context/verrijking voor een org-knoop.
    (De mapper gebruikt dit voorlopig alleen beschrijvend; org→org-conclusies slaan
    we nooit op — zie CLAUDE.md.)"""
    gescraped_op = gescraped_op or datetime.date.today().isoformat()
    return {
        "type": "bedrijf",
        "bron": {"linkedin_url": linkedin_url or _attr(company, "linkedin_url"),
                 "gescraped_op": gescraped_op},
        "organisatie": {
            "naam": _schoon(_attr(company, "name")),
            "industrie": _schoon(_attr(company, "industry")),
            "omvang": _schoon(_attr(company, "company_size")),
            "hoofdkantoor": _schoon(_attr(company, "headquarters")),
            "opgericht": _schoon(_attr(company, "founded")),
            "website": _schoon(_attr(company, "website")),
            "over": _schoon(_attr(company, "about_us") or _attr(company, "about")),
        },
    }
