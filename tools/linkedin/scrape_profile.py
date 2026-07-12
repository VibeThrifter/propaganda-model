#!/usr/bin/env python3
"""
Trap 1 — scrapen: een LinkedIn-URL → genormaliseerd profiel-JSON.

Dit is de fragiele, voorwaarden-gevoelige helft. Ze draait onder JOUW LinkedIn-sessie
(handmatig ingelogd, headful) en gebruikt de `linkedin_scraper`-bibliotheek. Ze schrijft
alleen een lokaal JSON-bestand — ze raakt de database of de API NIET aan. De model-kant
(`linkedin_naar_model.py`) leest dat JSON en dient pas dán voorstellen in.

Voorbereiding (eenmalig):
    python3 -m venv tools/linkedin/.venv && source tools/linkedin/.venv/bin/activate
    pip install -r tools/linkedin/requirements.txt
    playwright install chromium
    python3 tools/linkedin/scrape_profile.py login       # log handmatig in, sessie opgeslagen

Scrapen:
    python3 tools/linkedin/scrape_profile.py "https://www.linkedin.com/in/<slug>/"
    python3 tools/linkedin/scrape_profile.py --bedrijf "https://www.linkedin.com/company/<slug>/"

Uitvoer: data/linkedin/<slug>.json (gitignored — persoonsdata).

LET OP (staat ook in de README): geautomatiseerd scrapen schendt LinkedIn's
gebruiksvoorwaarden en kan je account kosten. Gebruik het gericht, met mate, en alleen
voor legitiem onderzoek. Deze tool is bewust headful + met een pauze tussen requests.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalize  # noqa: E402  (buurmodule)
import extract    # noqa: E402  (eigen, robuuste extractie via de detailpagina's)

ROOT = Path(__file__).resolve().parents[2]
UITVOER_DIR = ROOT / "data" / "linkedin"
SESSIE_BESTAND = Path(__file__).resolve().parent / "session.json"
LOGIN_TIMEOUT_S = 600  # 10 minuten om handmatig in te loggen (incl. 2FA/CAPTCHA)


def _eis_bibliotheek():
    """Importeer de scraper pas hier, met een leesbare fout als 'ie ontbreekt —
    zo draaien `normalize.py` en de mapper zonder Playwright te hoeven installeren."""
    try:
        from linkedin_scraper import BrowserManager, PersonScraper, CompanyScraper  # type: ignore
        try:
            from linkedin_scraper import wait_for_manual_login  # type: ignore
        except ImportError:
            wait_for_manual_login = None
        return BrowserManager, PersonScraper, CompanyScraper, wait_for_manual_login
    except ImportError as e:
        sys.exit(
            "linkedin_scraper is niet geïnstalleerd.\n"
            "  python3 -m venv tools/linkedin/.venv && source tools/linkedin/.venv/bin/activate\n"
            "  pip install -r tools/linkedin/requirements.txt\n"
            "  playwright install chromium\n"
            f"(onderliggende fout: {e})")


def _slug(url: str) -> str:
    m = re.search(r"/(?:in|company)/([^/?#]+)", url)
    basis = m.group(1) if m else re.sub(r"\W+", "-", url)[-40:]
    return re.sub(r"[^A-Za-z0-9_-]", "-", basis).strip("-") or "profiel"


async def _login():
    BrowserManager, _, _, _ = _eis_bibliotheek()
    # De timeout van wait_for_manual_login is in MILLISECONDEN (lib-default 300000 = 5 min).
    from linkedin_scraper import wait_for_manual_login, is_logged_in  # type: ignore
    minuten = LOGIN_TIMEOUT_S // 60
    async with BrowserManager(headless=False) as browser:
        page = browser.page
        await page.goto("https://www.linkedin.com/login")
        print(f"Log nu handmatig in op LinkedIn in het geopende venster.")
        print(f"Je hebt hiervoor {minuten} minuten (2FA/CAPTCHA mag). Zodra je binnen "
              f"bent, wordt de sessie automatisch opgeslagen — je hoeft niets te typen.")
        try:
            await wait_for_manual_login(page, timeout=LOGIN_TIMEOUT_S * 1000)
        except Exception as e:
            # Een lib-timeout/hapering mag niet fataal zijn: val terug op een Enter-bevestiging
            # zonder de event loop te blokkeren (anders bevriest de browser).
            print(f"(automatische detectie stopte: {e})")
            print("Ben je ingelogd? Druk dan hier op Enter.")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, input, "Enter om door te gaan… ")
        if not await is_logged_in(page):
            sys.exit("Nog niet ingelogd — sessie NIET opgeslagen. Draai het commando opnieuw "
                     "en voltooi de login (ook 2FA) binnen de tijd.")
        await browser.save_session(str(SESSIE_BESTAND))
    print(f"✓ Sessie opgeslagen in {SESSIE_BESTAND} (gitignored — bevat auth-cookies).")
    print("  Test met: python3 tools/linkedin/scrape_profile.py \"<een-LinkedIn-profiel-URL>\"")


async def _scrape(url: str, is_bedrijf: bool, uit: Path, sessie: Path, headless: bool):
    BrowserManager, PersonScraper, CompanyScraper, _ = _eis_bibliotheek()
    from linkedin_scraper import is_logged_in  # type: ignore
    if not sessie.exists():
        sys.exit(f"Geen sessie gevonden ({sessie}). Draai eerst: "
                 f"python3 {Path(__file__).name} login")
    async with BrowserManager(headless=headless) as browser:
        await browser.load_session(str(sessie))
        # Sessiecookies verlopen (LinkedIn: ~dagen–weken). Een verlopen cookie laadt
        # zonder fout, maar LinkedIn stuurt je dan naar de authwall — de detailpagina's
        # renderen dan de login i.p.v. het profiel, en de extractie levert stil een
        # leeg profiel (0 ervaringen). Vang dat hier af met een expliciete check, zodat
        # je een duidelijke fout krijgt i.p.v. misleidend-lege output.
        await browser.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        if not await is_logged_in(browser.page):
            sys.exit(normalize.sessie_verlopen_bericht(
                "LinkedIn toont de login/authwall i.p.v. het profiel — de opgeslagen "
                "sessie is verlopen of ongeldig."))
        if is_bedrijf:
            # Company draait nog op de bibliotheek (idem caveat: selectors kunnen verouderd zijn).
            obj = await CompanyScraper(browser.page).scrape(url)
            profiel = normalize.bedrijf_naar_profiel(obj, linkedin_url=url)
        else:
            # Persoon via de eigen detailpagina-extractie (robuuster dan de lib-selectors).
            profiel = await extract.scrape_persoon(browser.page, url)
    uit.parent.mkdir(parents=True, exist_ok=True)
    uit.write_text(json.dumps(profiel, ensure_ascii=False, indent=2), encoding="utf-8")
    naam = (profiel.get("persoon") or profiel.get("organisatie") or {}).get("naam")
    n_erv = len(profiel.get("ervaringen", []))
    n_opl = len(profiel.get("opleidingen", []))
    print(f"✓ {naam or url} → {uit}")
    if not is_bedrijf:
        print(f"  {n_erv} ervaring(en), {n_opl} opleiding(en), "
              f"{len(profiel.get('lidmaatschappen', []))} lidmaatschap(pen).")
    print(f"  Volgende stap: python3 tools/linkedin/linkedin_naar_model.py {uit}")


def main():
    p = argparse.ArgumentParser(description="Scrape een LinkedIn-profiel naar genormaliseerd JSON.",
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=__doc__)
    p.add_argument("url", nargs="?", help="LinkedIn-profiel-URL, of 'login' om een sessie te maken")
    p.add_argument("--bedrijf", action="store_true", help="scrape een company-pagina i.p.v. een persoon")
    p.add_argument("--out", type=Path, help="uitvoerbestand (default data/linkedin/<slug>.json)")
    p.add_argument("--sessie", type=Path, default=SESSIE_BESTAND, help="pad naar het sessiebestand")
    p.add_argument("--headless", action="store_true",
                   help="draai zonder zichtbaar venster (afgeraden: anti-botdetectie is strenger)")
    args = p.parse_args()

    if not args.url:
        p.print_help()
        return
    if args.url == "login":
        asyncio.run(_login())
        return

    uit = args.out or (UITVOER_DIR / f"{_slug(args.url)}.json")
    asyncio.run(_scrape(args.url, args.bedrijf, uit, args.sessie, args.headless))


if __name__ == "__main__":
    main()
