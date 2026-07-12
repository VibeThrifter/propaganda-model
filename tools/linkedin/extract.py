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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalize  # noqa: E402

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


async def _laad_tekst(page, url: str, wachten: float = 4.0, max_rondes: int = 40) -> str:
    """Ga naar url en scroll tot de pagina niet meer groeit — LinkedIn-detailpagina's
    laden entries via *infinite scroll* (geen 'toon meer'-knop; die zit alleen op de
    hoofdpagina en linkt naar déze detailpagina). We scrollen dus tot de zichtbare tekst
    drie rondes lang niet meer aangroeit, met een harde bovengrens als vangrail.
    ('networkidle' haalt LinkedIn nooit — constante achtergrond-requests.)"""
    await page.goto(url, wait_until="domcontentloaded")
    await asyncio.sleep(wachten)
    vorige_len, stabiel = 0, 0
    for _ in range(max_rondes):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.mouse.wheel(0, 3000)
        await asyncio.sleep(0.8)
        huidige = len(await page.inner_text("body"))
        if huidige <= vorige_len:
            stabiel += 1
            if stabiel >= 3:        # 3 rondes geen groei = alles geladen
                break
        else:
            stabiel = 0
        vorige_len = huidige
    await asyncio.sleep(1)
    return await page.inner_text("body")


async def scrape_persoon(page, url: str, gescraped_op: str | None = None) -> dict:
    """Scrape een persoon via de detailpagina's → genormaliseerd profielschema."""
    slug = _slug(url)
    basis = f"https://www.linkedin.com/in/{slug}"

    # Naam betrouwbaar uit de paginatitel ("(3) Frederieke Leeflang | LinkedIn").
    await page.goto(basis + "/", wait_until="domcontentloaded")
    await asyncio.sleep(3)
    titel = await page.title()
    naam = re.sub(r'^\(\d+\)\s*', '', titel).split("|")[0].strip() or None

    exp_txt = await _laad_tekst(page, basis + "/details/experience/")
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
