#!/usr/bin/env python3
"""X, Instagram en TikTok lezen onder een eigen, opgeslagen sessie, achter `rem.py`.

Draait onder tools/kanalen/.venv (Playwright + yt-dlp). Wordt aangeroepen door ophalen.py;
schrijft de items als JSON naar stdout. Zichtbaar venster (headful) onder de eigen sessie,
willekeurige pauzes, geen proxy's: hetzelfde beleid als tools/linkedin/.

    tools/kanalen/.venv/bin/python tools/kanalen/sociaal.py login x|instagram|tiktok
    tools/kanalen/.venv/bin/python tools/kanalen/sociaal.py haal x https://x.com/<naam> --max 5

Exit 75 = de rem weigert nu (niet herproberen), 76 = loginmuur/blokkade (de rem stopt het
platform 24 uur; is de sessie verlopen, dan logt de eigenaar opnieuw in met `login`).
Het automatisch lezen van deze platforms valt buiten hun voorwaarden en kan een account
blokkeren: gebruik een eigen account dat je daarvoor kunt missen.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import ophalen  # noqa: E402
import rem  # noqa: E402

SESSIES = HIER / "sessies"
START = {"x": "https://x.com/login", "instagram": "https://www.instagram.com/accounts/login/",
         "tiktok": "https://www.tiktok.com/login"}
MUUR = re.compile(r"/login|/i/flow/|/accounts/login|challenge|checkpoint|captcha", re.I)


def pauze(a=2.0, b=5.0):
    time.sleep(random.uniform(a, b))


def context(p, platform: str, headless: bool = False):
    SESSIES.mkdir(exist_ok=True)
    return p.chromium.launch_persistent_context(
        str(SESSIES / platform), headless=headless, locale="nl-NL",
        viewport={"width": 1280, "height": 900})


def login(platform: str):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = context(p, platform)
        page = ctx.new_page()
        page.goto(START[platform])
        input(f"Log in op {platform} in het venster en druk hier op Enter… ")
        ctx.close()
    print(f"sessie {platform} bewaard in {SESSIES / platform}")


class Muur(Exception):
    pass


def _check_muur(page):
    if MUUR.search(page.url):
        raise Muur(f"loginmuur ({page.url})")


def x(page, url: str, n: int) -> list[dict]:
    page.goto(url, wait_until="domcontentloaded")
    pauze()
    _check_muur(page)
    try:
        page.wait_for_selector("article", timeout=20000)
    except Exception as e:  # noqa: BLE001
        _check_muur(page)
        raise Muur(f"geen posts zichtbaar ({e.__class__.__name__})") from e
    gezien, uit = set(), []
    for _ in range(4):
        for art in page.query_selector_all("article"):
            link = art.query_selector("a[href*='/status/'] time")
            if not link:
                continue
            a = link.evaluate_handle("t => t.closest('a')")
            href = a.get_attribute("href")
            if not href or href in gezien:
                continue
            gezien.add(href)
            tekst_el = art.query_selector("[data-testid='tweetText']")
            tekst = tekst_el.inner_text() if tekst_el else ""
            for l in (tekst_el.query_selector_all("a[href]") if tekst_el else []):
                tekst += f"\n({l.inner_text().strip()} → {l.get_attribute('href')})"
            kaart = art.query_selector("[data-testid='card.wrapper'] a[href]")
            if kaart:
                tekst += f"\n(link: {kaart.get_attribute('href')})"
            if not tekst.strip():
                continue
            uit.append({"extern_id": href.rsplit("/", 1)[-1], "url": "https://x.com" + href,
                        "titel": tekst.split("\n", 1)[0][:120],
                        "gepubliceerd": link.get_attribute("datetime"),
                        "tekst": tekst, "tekstsoort": "tekst"})
        if len(uit) >= n:
            break
        page.mouse.wheel(0, 2500)
        pauze(1.5, 3.5)
    return uit[:n]


def instagram(page, url: str, n: int) -> list[dict]:
    page.goto(url, wait_until="domcontentloaded")
    pauze()
    _check_muur(page)
    page.wait_for_timeout(3000)
    links = []
    for a in page.query_selector_all("a[href*='/p/'], a[href*='/reel/']"):
        h = a.get_attribute("href")
        if h and h not in links:
            links.append(h)
    uit = []
    for h in links[:n]:
        post = "https://www.instagram.com" + h if h.startswith("/") else h
        page.goto(post, wait_until="domcontentloaded")
        pauze()
        _check_muur(page)
        meta = page.query_selector("meta[property='og:description']")
        tekst = meta.get_attribute("content") if meta else ""
        tijd = page.query_selector("time[datetime]")
        if "/reel/" in h:
            t = ophalen.transcript(post)
            if t:
                tekst += f"\n\n--- transcript ---\n{t}"
        uit.append({"extern_id": h.strip("/").split("/")[-1], "url": post,
                    "titel": (tekst or "").split("\n", 1)[0][:120],
                    "gepubliceerd": tijd.get_attribute("datetime") if tijd else None,
                    "tekst": tekst or "", "tekstsoort": "transcript" if "transcript" in tekst
                    else "beschrijving"})
    return uit


def tiktok(page, url: str, n: int) -> list[dict]:
    page.goto(url, wait_until="domcontentloaded")
    pauze()
    _check_muur(page)
    page.wait_for_timeout(4000)
    links = []
    for a in page.query_selector_all("a[href*='/video/']"):
        h = a.get_attribute("href")
        if h and h not in links:
            links.append(h)
    uit = []
    bin_ = ophalen.ytdlp()
    for h in links[:n]:
        beschrijving, datum = "", None
        if bin_:
            r = subprocess.run([str(bin_), "-J", "--no-warnings", "--skip-download", h],
                               capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                info = json.loads(r.stdout or "{}")
                beschrijving = info.get("description") or info.get("title") or ""
                if info.get("upload_date"):
                    d = info["upload_date"]
                    datum = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        tekst = beschrijving
        t = ophalen.transcript(h, talen="nl.*,en.*,.*")
        if t:
            tekst += f"\n\n--- transcript ---\n{t}"
        pauze()
        uit.append({"extern_id": h.rstrip("/").split("/")[-1], "url": h,
                    "titel": beschrijving.split("\n", 1)[0][:120], "gepubliceerd": datum,
                    "tekst": tekst, "tekstsoort": "transcript" if t else "beschrijving"})
    return uit


LEZERS = {"x": x, "instagram": instagram, "tiktok": tiktok}


def haal(platform: str, url: str, n: int):
    ok, reden = rem.mag(platform)
    if not ok:
        print(f"⏳ KANALEN-REM {platform}: {reden}")
        sys.exit(rem.EXIT_REM)
    if not (SESSIES / platform).exists():
        print(f"⚠ {platform}-SESSIE ONTBREEKT — de eigenaar draait: "
              f"tools/kanalen/.venv/bin/python tools/kanalen/sociaal.py login {platform}")
        sys.exit(rem.EXIT_BLOKKADE)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = context(p, platform)
        try:
            items = LEZERS[platform](ctx.new_page(), url, n)
        except Muur as e:
            tot = rem.blokkade(platform, str(e))
            print(f"⛔ KANALEN-BLOKKADE {platform}: {e} — gestopt tot {tot[:16]}; is de sessie "
                  f"verlopen, log dan opnieuw in met sociaal.py login {platform}")
            sys.exit(rem.EXIT_BLOKKADE)
        finally:
            ctx.close()
    print(json.dumps(items, ensure_ascii=False))


def render(url: str):
    """Een gewone website die haar tekst met JavaScript opbouwt (bv. NieuwRechts, een Angular-app):
    headless openen, wachten tot de tekst staat, de HTML naar stdout. Geen sessie, geen rem."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page(locale="nl-NL")
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)
        print(page.content())
        b.close()


def main():
    if sys.argv[1:2] == ["render"]:
        return render(sys.argv[2])
    ap = argparse.ArgumentParser()
    ap.add_argument("actie", choices=["login", "haal"])
    ap.add_argument("platform", choices=sorted(LEZERS))
    ap.add_argument("url", nargs="?")
    ap.add_argument("--max", type=int, default=5)
    a = ap.parse_args()
    if a.actie == "login":
        login(a.platform)
    else:
        haal(a.platform, a.url, min(a.max, 10))


if __name__ == "__main__":
    main()
