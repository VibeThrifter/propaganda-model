#!/usr/bin/env python3
"""
Eigen, robuuste LinkedIn-extractie — vervangt de verouderde selectors van de
`linkedin_scraper`-bibliotheek (v3.1.2 zoekt naar `h1`/`#experience`; die bestaan niet
meer — LinkedIn gebruikt nu `h2` + geobfusceerde hash-klassen, dus de lib levert
"Unknown" + 0 ervaringen).

Aanpak die wél werkt en niet leunt op broze CSS-klassen: LinkedIn heeft aparte
**detailpagina's** die de volledige, gestructureerde lijst renderen, óók voor
niet-connecties:
    /in/<slug>/details/experience/
    /in/<slug>/details/education/
`page.inner_text("body")` geeft daar schone, gededupliceerde tekst. Elke entry volgt
strak de volgorde:
    ervaring:   <functie> / <organisatie [· dienstverband]> / <datumregel> / <locatie?> / <beschrijving?>
    opleiding:  <instelling> / <graad> / <jaren>
De **datumregel** ("mei 2026 - heden · 3 mnd", "2015 - 2015", "sep. 1988 - 1993") is een
betrouwbaar anker: de twee regels ervóór zijn altijd de kop + de organisatie/graad. Dat
maakt de parser robuust tegen wisselend aantal beschrijvingsregels.

Levert het genormaliseerde profielschema van `normalize.py` (zodat de mapper ongewijzigd
werkt). Async — verwacht een reeds ingelogde Playwright `page`.
"""
from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlencode, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalize  # noqa: E402
from snelheidsrem import pauze  # noqa: E402  (willekeurige pauzes — Epic 12)

# Een datumregel begint met (maand?) jaartal, dan streepje, dan (heden|(maand?) jaar).
_DATUMREGEL = re.compile(
    r'^\s*([A-Za-z.]+\s)?\d{4}\s*[-–]\s*(heden|present|now|([A-Za-z.]+\s)?\d{4})', re.I)

# Waar de inhoudelijke sectie ophoudt en de LinkedIn-ruis (aanbevolen profielen etc.) begint.
_STOP = ("Meer profielen", "Mensen die u misschien kent", "Meer activiteit",
         "People also viewed", "People you may know", "Interesses", "Interests",
         "Vaardigheden", "Skills", "Aanbevelingen", "Recommendations", "Talen", "Languages")

# Een regel die ALLEEN een tijdsduur is ("7 jr 9 mnd", "2 jr", "6 mnd") — LinkedIn zet
# die onder een bedrijf-kopregel wanneer iemand meerdere rollen bij één werkgever had
# (gegroepeerde ervaring). Het onderscheidt een groep-kop van een gewone entry.
_DUUR_ONLY = re.compile(
    r'^\s*\d+\s*(jr|jaar|yrs?|years?|mnd|maanden?|mos?|months?)'
    r'(\s+\d+\s*(mnd|maanden?|mos?|months?))?\s*$', re.I)


def _slug(url: str) -> str:
    m = re.search(r"/in/([^/?#]+)", url)
    return m.group(1) if m else url.rstrip("/").split("/")[-1]


def _sectieregels(txt: str, koppen: tuple[str, ...]) -> list[str]:
    """Niet-lege regels tussen de sectiekop (bv. 'Ervaring') en de eerste ruis-marker."""
    regels = [r.strip() for r in txt.splitlines() if r.strip()]
    start = next((i + 1 for i, r in enumerate(regels) if r in koppen), None)
    if start is None:
        return []
    eind = len(regels)
    for i in range(start, len(regels)):
        if any(regels[i].startswith(m) for m in _STOP):
            eind = i
            break
    return regels[start:eind]


def _datums(regel: str) -> tuple[str | None, str | None]:
    kern = regel.split("·")[0].strip()                 # duur ("· 3 mnd") eraf
    delen = re.split(r'\s*[-–]\s*', kern, maxsplit=1)
    van = normalize.normaliseer_datum(delen[0]) if delen else None
    tot = normalize.normaliseer_datum(delen[1]) if len(delen) > 1 else None
    return van, tot


def _is_groepkop(regels: list[str], i: int) -> bool:
    """regels[i] is een bedrijf/instelling-kop van een GROEP als de volgende regel een
    kale tijdsduur is (en de kop zelf geen datum/duur)."""
    return (i + 1 < len(regels) and _DUUR_ONLY.match(regels[i + 1])
            and not _DATUMREGEL.match(regels[i]) and not _DUUR_ONLY.match(regels[i]))


def _parse_loopbaan(regels: list[str], org_eerst_ongegroepeerd: bool) -> list[tuple]:
    """→ lijst (org, titel, van, tot). Verwerkt twee LinkedIn-structuren:

    * **Gegroepeerd** — meerdere rollen bij één werkgever: een bedrijf-kopregel + kale
      totale-duurregel (+ optionele locatie), daarna per rol `[titel, datumregel]`.
    * **Ongegroepeerd** — één rol: `[titel, org, datumregel]` (ervaring) of
      `[org, titel, datumregel]` (opleiding; `org_eerst_ongegroepeerd=True`).
    De datumregel blijft het anker; de groep-kop lost de "bedrijf staat niet vlak vóór
    de datum"-structuur op (anders werd de locatie als functie gelezen)."""
    n = len(regels)
    uit = []
    i = 0
    while i < n:
        if _is_groepkop(regels, i):
            org = regels[i].split("·")[0].strip()
            j = i + 2                                   # sla kop + totale-duurregel over
            while j < n and not _is_groepkop(regels, j):
                if j + 1 < n and _DATUMREGEL.match(regels[j + 1]) and not _DATUMREGEL.match(regels[j]):
                    van, tot = _datums(regels[j + 1])
                    uit.append((org, regels[j], van, tot))   # (org=kop, titel=rol)
                    j += 2
                else:
                    j += 1                              # locatie/beschrijving/ruis: overslaan
            i = j
            continue
        if _DATUMREGEL.match(regels[i]) and i >= 2:
            van, tot = _datums(regels[i])
            if org_eerst_ongegroepeerd:                 # opleiding: [org, titel, datum]
                org, titel = regels[i - 2], regels[i - 1]
            else:                                       # ervaring: [titel, org, datum]
                titel, org = regels[i - 2], regels[i - 1].split("·")[0].strip()
            uit.append((org, titel, van, tot))
        i += 1
    return uit


def parse_ervaringen(txt: str) -> list[dict]:
    regels = _sectieregels(txt, ("Ervaring", "Experience"))
    return [{"organisatie": org, "functie": titel, "van": v, "tot": t,
             "duur": None, "locatie": None, "beschrijving": None, "linkedin_url": None}
            for org, titel, v, t in _parse_loopbaan(regels, org_eerst_ongegroepeerd=False)]


def parse_opleidingen(txt: str) -> list[dict]:
    regels = _sectieregels(txt, ("Opleiding", "Education"))
    return [{"instelling": org, "graad": titel, "van": v, "tot": t, "beschrijving": None}
            for org, titel, v, t in _parse_loopbaan(regels, org_eerst_ongegroepeerd=True)]


# ── Blokkadedetectie (Epic 12 — stroomonderbreker van de snelheidsrem) ──────────
# Na élke navigatie: staat LinkedIn op een beveiligingscontrole (checkpoint/challenge/
# captcha) of — midden in een ingelogde sessie — op de authwall, dan stopt de scrape
# METEEN (geen tweede request) en springt de stroomonderbreker (snelheidsrem.blokkeer).
# Dit is iets anders dan een dode sessie: die vangt scrape_profile.py vóóraf af op /feed/
# (is_logged_in) met de ongewijzigde "⚠ LINKEDIN-SESSIE VERLOPEN"-melding; daar telt een
# authwall/login dus NIET als blokkade (authwall_is_blokkade=False).

class LinkedInBlokkade(Exception):
    """LinkedIn toont een beveiligingscontrole/captcha/authwall — stop alles."""

    def __init__(self, reden: str):
        super().__init__(reden)
        self.reden = reden


_BLOKKADE_PADEN = ("/checkpoint", "/challenge", "captcha")
_AUTHWALL_PADEN = ("/authwall",)
_BLOKKADE_TEKST = re.compile(
    r"(security verification|quick security check|security check|beveiligingscontrole"
    r"|veiligheidscontrole|verify (?:that )?you(?:'|’)?re (?:a )?human"
    r"|bevestig dat je (?:een )?mens bent|restricted your account"
    r"|account (?:is )?(?:tijdelijk )?beperkt|unusual activity|ongebruikelijke activiteit"
    r"|captcha)", re.I)
# Alleen de kop van de pagina scannen: een controlepagina is kort; zo vermijden we
# vals alarm op een profieltekst die toevallig 'unusual activity' bevat.
_BLOKKADE_SCAN_TEKENS = 2000


def blokkade_reden(url: str, titel: str = "", tekst: str = "",
                   authwall_is_blokkade: bool = True) -> str | None:
    """Pure functie: reden-tekst als deze pagina een blokkade is, anders None."""
    pad = unquote(urlparse(url or "").path or "").lower()
    volledig = (url or "").lower()
    for p in _BLOKKADE_PADEN:
        if p in pad or (p == "captcha" and "captcha" in volledig):
            return f"LinkedIn-beveiligingscontrole ({p.strip('/')}) op {url}"
    if authwall_is_blokkade and any(p in pad for p in _AUTHWALL_PADEN):
        return f"LinkedIn-authwall midden in een ingelogde sessie op {url}"
    kop = f"{titel or ''}\n{(tekst or '')[:_BLOKKADE_SCAN_TEKENS]}"
    m = _BLOKKADE_TEKST.search(kop)
    if m:
        return f"LinkedIn toont een beveiligingscontrole ('{m.group(0)}') op {url}"
    return None


async def controleer_blokkade(page, authwall_is_blokkade: bool = True) -> None:
    """Na een navigatie: werp LinkedInBlokkade als de pagina een blokkade is."""
    try:
        titel = await page.title()
    except Exception:  # noqa: BLE001 — een half geladen pagina mag de check niet breken
        titel = ""
    try:
        tekst = await page.inner_text("body")
    except Exception:  # noqa: BLE001
        tekst = ""
    reden = blokkade_reden(page.url, titel, tekst, authwall_is_blokkade)
    if reden:
        raise LinkedInBlokkade(reden)


# ── People-search (subcommando `zoek`, Epic 12) ─────────────────────────────
# Leest de gerenderde TEKST van de zoekresultaten + de profiel-links (a[href*='/in/']),
# niet de geobfusceerde CSS-klassen — zelfde robuustheidsprincipe als de detailpagina's.
# Per kaart: naam (uit de link), kop (headline) en locatie = de eerste twee
# niet-ruisregels onder de naam in de paginatekst.

_ZOEK_RUIS = re.compile(
    r"^(?:[•·]\s*)?(?:1e|2e|3e\+?|1st|2nd|3rd\+?)(?:\s|$)"
    r"|graads|degree connection"
    r"|^(?:connectie maken|connect|volgen|follow|bericht|message|in afwachting|pending"
    r"|verbinden|meer|more)$"
    r"|^bekijk (?:het )?profiel van|^view .+ profile$|profiel bekijken"
    r"|^status is|^(?:huidig|current|vorige|past|samenvatting|summary)\s*:"
    r"|gemeenschappelijke connectie|mutual connection|^anderen genaamd|^people also"
    r"|^•$|^·$", re.I)
_ZOEK_ANONIEM = {"linkedin member", "linkedin-lid", "linkedin lid", "lid van linkedin"}


def _profiel_slug(href: str) -> str | None:
    m = re.search(r"linkedin\.com/in/([^/?#]+)", href or "")
    if not m:
        m = re.match(r"^/in/([^/?#]+)", href or "")
    return unquote(m.group(1)) if m else None


def _naam_uit_linktekst(tekst: str) -> str | None:
    for regel in (tekst or "").splitlines():
        regel = regel.strip()
        if not regel:
            continue
        m = re.match(r"^(?:bekijk (?:het )?profiel van|view)\s+(.+?)(?:(?:'|’)s? profile)?$",
                     regel, re.I)
        if m and not _ZOEK_RUIS.search(m.group(1)):
            regel = m.group(1).strip()
        regel = re.split(r"\s+[•·]\s+", regel)[0].strip()
        if not regel or _ZOEK_RUIS.search(regel):
            continue
        return regel
    return None


def _kop_en_locatie(regels: list[str], naam: str,
                    n: int = 0) -> tuple[str | None, str | None]:
    """Kop + locatie onder de n-de (0-based) kaart met deze naam — naamgenoten krijgen
    zo elk hun eigen kaart i.p.v. allemaal de eerste."""
    laag = naam.lower()
    treffers = [i for i, r in enumerate(regels)
                if r.lower() == laag or r.lower().startswith(laag + " ")]
    for i in treffers[n:n + 1]:
        gevonden = []
        for r2 in regels[i + 1:i + 12]:
            if r2 == naam or laag in r2.lower() or _ZOEK_RUIS.search(r2):
                continue
            gevonden.append(r2)
            if len(gevonden) == 2:
                break
        kop = gevonden[0] if gevonden else None
        locatie = gevonden[1] if len(gevonden) > 1 else None
        return kop, locatie
    return None, None


def parse_zoekresultaten(tekst: str, links: list[dict], max_n: int = 5) -> list[dict]:
    """Pure functie (fixtures-testbaar): paginatekst + [{href, tekst}] → [{naam, kop,
    locatie, url}], in paginavolgorde, zonder dubbelen en zonder anonieme 'LinkedIn-lid'."""
    regels = [r.strip() for r in (tekst or "").splitlines() if r.strip()]
    volgorde, namen = [], {}
    for link in links or []:
        slug = _profiel_slug(link.get("href", ""))
        if not slug:
            continue
        if slug not in namen:
            volgorde.append(slug)
            namen[slug] = None
        if namen[slug] is None:
            namen[slug] = _naam_uit_linktekst(link.get("tekst", ""))
    uit, gezien_naam = [], {}
    for slug in volgorde:
        naam = namen[slug]
        if not naam or naam.lower() in _ZOEK_ANONIEM:
            continue
        n = gezien_naam.get(naam.lower(), 0)
        gezien_naam[naam.lower()] = n + 1
        kop, locatie = _kop_en_locatie(regels, naam, n)
        uit.append({"naam": naam, "kop": kop, "locatie": locatie,
                    "url": f"https://www.linkedin.com/in/{slug}/"})
        if len(uit) >= max_n:
            break
    return uit


async def zoek_personen(page, naam: str, context: str | None = None,
                        max_n: int = 5) -> list[dict]:
    """People-search in de ingelogde sessie → [{naam, kop, locatie, url}]."""
    kw = " ".join(x.strip() for x in (naam, context or "") if x and x.strip())
    url = ("https://www.linkedin.com/search/results/people/?"
           + urlencode({"keywords": kw, "origin": "GLOBAL_SEARCH_HEADER"}))
    await page.goto(url, wait_until="domcontentloaded")
    await controleer_blokkade(page)
    await asyncio.sleep(pauze(4.0))
    for _ in range(2):                            # lazy-loaded kaarten zichtbaar maken
        await page.mouse.wheel(0, 1500)
        await asyncio.sleep(pauze(1.2))
    await controleer_blokkade(page)
    tekst = await page.inner_text("body")
    links = await page.eval_on_selector_all(
        "a[href*='/in/']", "els => els.map(e => ({href: e.href, tekst: e.innerText || ''}))")
    return parse_zoekresultaten(tekst, links, max_n=max_n)


async def _laad_tekst(page, url: str, wachten: float = 4.0, max_rondes: int = 40) -> str:
    """Ga naar url en scroll tot de pagina niet meer groeit — LinkedIn-detailpagina's
    laden entries via *infinite scroll* (geen 'toon meer'-knop; die zit alleen op de
    hoofdpagina en linkt naar déze detailpagina). We scrollen dus tot de zichtbare tekst
    drie rondes lang niet meer aangroeit, met een harde bovengrens als vangrail.
    ('networkidle' haalt LinkedIn nooit — constante achtergrond-requests.)"""
    await page.goto(url, wait_until="domcontentloaded")
    await controleer_blokkade(page)
    await asyncio.sleep(pauze(wachten))           # willekeurig, geen vast ritme (Epic 12)
    vorige_len, stabiel = 0, 0
    for _ in range(max_rondes):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.mouse.wheel(0, 3000)
        await asyncio.sleep(pauze(0.8))
        huidige = len(await page.inner_text("body"))
        if huidige <= vorige_len:
            stabiel += 1
            if stabiel >= 3:        # 3 rondes geen groei = alles geladen
                break
        else:
            stabiel = 0
        vorige_len = huidige
    await asyncio.sleep(pauze(1.0))
    await controleer_blokkade(page)
    return await page.inner_text("body")


async def scrape_persoon(page, url: str, gescraped_op: str | None = None) -> dict:
    """Scrape een persoon via de detailpagina's → genormaliseerd profielschema."""
    slug = _slug(url)
    basis = f"https://www.linkedin.com/in/{slug}"

    # Naam betrouwbaar uit de paginatitel ("(3) Frederieke Leeflang | LinkedIn").
    await page.goto(basis + "/", wait_until="domcontentloaded")
    await controleer_blokkade(page)
    await asyncio.sleep(pauze(3.0))
    titel = await page.title()
    naam = re.sub(r'^\(\d+\)\s*', '', titel).split("|")[0].strip() or None

    exp_txt = await _laad_tekst(page, basis + "/details/experience/")
    await asyncio.sleep(pauze(4.0))               # menselijke pauze tussen paginaladingen
    edu_txt = await _laad_tekst(page, basis + "/details/education/")

    import datetime
    return {
        "type": "persoon",
        "bron": {"linkedin_url": basis + "/",
                 "gescraped_op": gescraped_op or datetime.date.today().isoformat()},
        "persoon": {"naam": naam, "kop": None, "locatie": None, "over": None},
        "ervaringen": parse_ervaringen(exp_txt),
        "opleidingen": parse_opleidingen(edu_txt),
        "lidmaatschappen": [],
    }
