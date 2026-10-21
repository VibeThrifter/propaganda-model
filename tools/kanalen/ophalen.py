#!/usr/bin/env python3
"""Kanalen ophalen: nieuwe posts, artikelen en video's van gevolgde accounts (eigenaar
2026-10-19: "scraping en agent die om de x tijd bepaalde social media accounts of blogs of
youtubers kan minen naar verbanden").

Pure stdlib voor wat zonder login leesbaar is:
  * blog / substack / site  → RSS of Atom (zelf gevonden via <link rel="alternate">), en
    bij een korte samenvatting de pagina zelf;
  * youtube                → de kanaalfeed (videos.xml), met het transcript via yt-dlp als
    dat in tools/kanalen/.venv staat (anders alleen de beschrijving);
  * telegram               → de publieke kanaalpagina t.me/s/<naam>.
X, Instagram en TikTok gaan via `sociaal.py` (Playwright/yt-dlp in de venv, achter `rem.py`).

Elk item is een dict {extern_id, url, titel, gepubliceerd, tekst, tekstsoort}; `tekst`
houdt links als "tekst (url)", want de bronnen die een kanaal noemt zijn wat we toetsen.
Ophalen schrijft niets; scripts/kanalen.py bewaart.
"""
from __future__ import annotations

import datetime
import email.utils
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

HIER = Path(__file__).resolve().parent
VENV_BIN = HIER / ".venv" / "bin"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0 Safari/537.36")
MAX_TEKST = 120_000           # tekens per item (een uur video ≈ 60k)
KORTE_SAMENVATTING = 1500     # korter → de pagina zelf ophalen
# deel-, like- en profielknoppen zijn geen bron die het kanaal noemt
DEELKNOP = re.compile(r"intent/|share|whatsapp|wa\.me/|mailto:|"
                      r"/auteur/|/author/|/tag/|/tags/|/categor|#|/login|/signup", re.I)
PLATFORMS = ("blog", "youtube", "podcast", "telegram", "x", "instagram", "tiktok")
SOCIAAL = ("x", "instagram", "tiktok")


class OphaalFout(Exception):
    pass


def haal(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "nl,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ruw = r.read(8_000_000)
            charset = r.headers.get_content_charset() or "utf-8"
    except Exception as e:  # noqa: BLE001 — elke netwerkfout is een ophaalfout
        raise OphaalFout(f"{url}: {e}") from e
    return ruw.decode(charset, errors="replace")


# ---------------------------------------------------------------- html → tekst

class _Tekst(HTMLParser):
    """HTML naar platte tekst; een link wordt "tekst (url)", blokken worden regels."""
    BLOK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "blockquote",
            "section", "article", "figcaption"}
    WEG = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "aside"}

    def __init__(self, basis: str = ""):
        super().__init__(convert_charrefs=True)
        self.basis = basis
        self.delen: list[str] = []
        self.weg = 0
        self.href: list[str | None] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.WEG:
            self.weg += 1
        if tag in self.BLOK:
            self.delen.append("\n")
        if tag == "a":
            href = dict(attrs).get("href")
            if href and href.startswith(("http", "/")) and not DEELKNOP.search(href):
                href = urllib.parse.urljoin(self.basis, href)
            else:
                href = None
            self.href.append(href)

    def handle_endtag(self, tag):
        if tag in self.WEG and self.weg:
            self.weg -= 1
        if tag == "a" and self.href:
            href = self.href.pop()
            if href and not self.weg:
                self.delen.append(f" ({href})")
        if tag in self.BLOK:
            self.delen.append("\n")

    def handle_data(self, data):
        if not self.weg:
            self.delen.append(data)


def html_naar_tekst(stuk: str, basis: str = "") -> str:
    p = _Tekst(basis)
    p.feed(stuk or "")
    tekst = "".join(p.delen)
    tekst = re.sub(r"[ \t ]+", " ", tekst)
    tekst = re.sub(r"\s*\n\s*", "\n", tekst)
    return re.sub(r"\n{3,}", "\n\n", tekst).strip()


def gerenderd(url: str) -> str:
    """De HTML na JavaScript (Playwright in de venv, sociaal.py render)."""
    py = VENV_BIN / "python"
    if not py.exists():
        raise OphaalFout("tools/kanalen/.venv ontbreekt (nodig voor --js)")
    r = subprocess.run([str(py), str(HIER / "sociaal.py"), "render", url],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise OphaalFout(f"renderen mislukt: {(r.stderr.strip().splitlines() or ['?'])[-1]}")
    return r.stdout


def pagina_tekst(url: str, js: bool = False) -> str:
    """De leestekst van een artikelpagina: <article>, anders <main>, anders <body>. Met `js`
    eerst renderen (sites die hun tekst met JavaScript opbouwen)."""
    doc = gerenderd(url) if js else haal(url)
    for tag in ("article", "main", "body"):
        m = re.search(rf"<{tag}\b[^>]*>(.*)</{tag}>", doc, re.S | re.I)
        if m:
            return html_naar_tekst(m.group(1), url)
    return html_naar_tekst(doc, url)


# ---------------------------------------------------------------- datums

def iso(datum: str | None) -> str | None:
    if not datum:
        return None
    datum = datum.strip()
    try:
        return email.utils.parsedate_to_datetime(datum).isoformat(timespec="seconds")
    except (TypeError, ValueError):
        pass
    try:
        return datetime.datetime.fromisoformat(datum.replace("Z", "+00:00")
                                               ).isoformat(timespec="seconds")
    except ValueError:
        return datum[:25]


# ---------------------------------------------------------------- RSS / Atom

NS = {"atom": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/",
      "yt": "http://www.youtube.com/xml/schemas/2015",
      "content": "http://purl.org/rss/1.0/modules/content/"}


def is_feed(doc: str) -> bool:
    kop = doc.lstrip()[:500].lower()
    return kop.startswith("<?xml") or "<rss" in kop or "<feed" in kop


def feed_items(doc: str, basis: str = "") -> list[dict]:
    try:
        wortel = ET.fromstring(doc.encode("utf-8", errors="replace"))
    except ET.ParseError as e:
        raise OphaalFout(f"geen geldige feed: {e}") from e
    uit = []
    if wortel.tag.endswith("rss") or wortel.find("channel") is not None:
        for it in wortel.iter("item"):
            link = (it.findtext("link") or "").strip()
            inhoud = it.findtext("content:encoded", namespaces=NS) or it.findtext("description") or ""
            enc = it.find("enclosure")
            uit.append({"extern_id": (it.findtext("guid") or link).strip(), "url": link,
                        "titel": html.unescape((it.findtext("title") or "").strip()),
                        "gepubliceerd": iso(it.findtext("pubDate")),
                        "tekst": html_naar_tekst(inhoud, link or basis), "tekstsoort": "tekst",
                        "audio": enc.get("url") if enc is not None
                        and (enc.get("type") or "").startswith("audio") else None})
        return uit
    for e in wortel.findall("atom:entry", NS):
        link = ""
        for l in e.findall("atom:link", NS):
            if l.get("rel", "alternate") == "alternate":
                link = l.get("href", "")
                break
        inhoud = (e.findtext("atom:content", namespaces=NS)
                  or e.findtext("atom:summary", namespaces=NS)
                  or e.findtext("media:group/media:description", namespaces=NS) or "")
        vid = e.findtext("yt:videoId", namespaces=NS)
        uit.append({"extern_id": vid or (e.findtext("atom:id", namespaces=NS) or link).strip(),
                    "url": link, "titel": html.unescape((e.findtext("atom:title", namespaces=NS) or "").strip()),
                    "gepubliceerd": iso(e.findtext("atom:published", namespaces=NS)
                                        or e.findtext("atom:updated", namespaces=NS)),
                    "tekst": inhoud.strip() if vid else html_naar_tekst(inhoud, link or basis),
                    "tekstsoort": "beschrijving" if vid else "tekst"})
    return uit


def vind_feed(url: str) -> str:
    """De feed-url bij een blog/site: de url zelf, een <link rel=alternate>, of /feed. Weigert de
    homepage (403, bv. cidi.nl), dan nog de vaste paden proberen: de feed is vaak wel open."""
    try:
        doc = haal(url)
    except OphaalFout:
        doc = ""
    if doc and is_feed(doc):
        return url
    for m in re.finditer(r"<link\b[^>]*>", doc, re.I):
        tag = m.group(0)
        if re.search(r"application/(rss|atom)\+xml", tag, re.I):
            href = re.search(r'href=["\']([^"\']+)', tag, re.I)
            if href:
                return urllib.parse.urljoin(url, html.unescape(href.group(1)))
    for pad in ("/feed", "/feed/", "/rss", "/feed.xml", "/atom.xml", "/index.xml"):
        kandidaat = urllib.parse.urljoin(url.rstrip("/") + "/", pad.lstrip("/"))
        try:
            if is_feed(haal(kandidaat)):
                return kandidaat
        except OphaalFout:
            continue
    raise OphaalFout(f"geen RSS/Atom-feed gevonden op {url}")


def blog(kanaal: dict, max_items: int) -> list[dict]:
    feed = kanaal.get("feed_url") or vind_feed(kanaal["url"])
    kanaal["feed_url"] = feed
    items = feed_items(haal(feed), kanaal["url"])[:max_items]
    for it in items:
        if (kanaal.get("js") or len(it["tekst"]) < KORTE_SAMENVATTING) and it["url"]:
            try:
                it["tekst"] = pagina_tekst(it["url"], js=bool(kanaal.get("js")))
            except OphaalFout:
                pass
    return items


# ---------------------------------------------------------------- YouTube

def youtube_feed(url: str) -> str:
    if "feeds/videos.xml" in url:
        return url
    m = re.search(r"/channel/(UC[\w-]{22})", url)
    if not m:
        m = re.search(r'"(?:channelId|externalId)":"(UC[\w-]{22})"', haal(url))
    if not m:
        raise OphaalFout(f"geen YouTube-kanaal-id gevonden op {url}")
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}"


def vtt_naar_tekst(vtt: str) -> str:
    """WebVTT (ook de rollende auto-ondertitels van YouTube, waar elke regel twee keer langskomt)
    naar tekst met een tijdmarkering per ~30 s, zodat een citaat een tijdcode kan dragen."""
    uit, recent, laatste_mark = [], [], -999
    for blok in re.split(r"\n\s*\n", vtt):
        m = re.search(r"(\d+):(\d\d):(\d\d)[.,]\d+\s+-->", blok)
        if not m:
            continue
        tijd = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
        for regel in blok.split("\n")[1:]:
            if "-->" in regel:
                continue
            regel = html.unescape(re.sub(r"<[^>]+>", "", regel)).strip()
            if not regel or regel in recent:
                continue
            recent = (recent + [regel])[-4:]
            if tijd - laatste_mark >= 30:
                u, r = divmod(tijd, 3600)
                uit.append(f"\n[{u}:{r // 60:02d}:{r % 60:02d}] " if u else
                           f"\n[{r // 60:02d}:{r % 60:02d}] ")
                laatste_mark = tijd
            uit.append(regel + " ")
    return "".join(uit).strip()


def ytdlp() -> Path | None:
    p = VENV_BIN / "yt-dlp"
    return p if p.exists() else None


def transcript(video_url: str, talen: str = "nl-orig,nl,en-orig,en") -> str | None:
    """Ondertitels (handmatig, anders automatisch) via yt-dlp; None als dat niet kan. De
    originele taal (-orig) eerst: een vertaalde ondertitel geeft sneller een 429."""
    bin_ = ytdlp()
    if not bin_:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [str(bin_), "--skip-download", "--write-subs", "--write-auto-subs",
               "--sub-langs", talen, "--sub-format", "vtt", "--no-warnings", "--quiet",
               "--ignore-errors", "-o", f"{tmp}/%(id)s.%(ext)s", video_url]
        if shutil.which("node"):
            cmd[1:1] = ["--js-runtimes", "node"]   # YouTube vraagt een JS-runtime
        try:
            subprocess.run(cmd, capture_output=True, timeout=180, check=False)
        except subprocess.TimeoutExpired:
            return None
        voorkeur = [t.strip() for t in talen.split(",")]
        vtts = sorted(Path(tmp).glob("*.vtt"), key=lambda p: next(
            (i for i, t in enumerate(voorkeur) if p.name.endswith(f".{t}.vtt")), len(voorkeur)))
        if not vtts:
            return None
        return vtt_naar_tekst(vtts[0].read_text(errors="replace")) or None


def youtube(kanaal: dict, max_items: int, met_transcript: bool = True) -> list[dict]:
    feed = kanaal.get("feed_url") or youtube_feed(kanaal["url"])
    kanaal["feed_url"] = feed
    items = feed_items(haal(feed))[:max_items]
    for it in items:
        if met_transcript and it["url"]:
            t = transcript(it["url"])
            if t:
                it["tekst"] = f"{it['tekst']}\n\n--- transcript ---\n{t}"
                it["tekstsoort"] = "transcript"
    return items


# ---------------------------------------------------------------- Podcast

PODCAST_PER_RONDE = 1


def podcast_feed(url: str) -> str:
    """De RSS-feed van een podcast: de url zelf, of via de iTunes-lookup bij een Apple-link."""
    m = re.search(r"podcasts\.apple\.com/.*/id(\d+)|^(\d+)$", url)
    if m:
        data = json.loads(haal(f"https://itunes.apple.com/lookup?id={m.group(1) or m.group(2)}"))
        if data.get("results") and data["results"][0].get("feedUrl"):
            return data["results"][0]["feedUrl"]
        raise OphaalFout(f"geen podcastfeed bij {url}")
    return url


def spraak_naar_tekst(audio_url: str) -> str | None:
    """Lokaal transcriberen (transcribeer.py, faster-whisper in de venv); None als dat niet kan."""
    py = VENV_BIN / "python"
    if not py.exists():
        return None
    try:
        r = subprocess.run([str(py), str(HIER / "transcribeer.py"), audio_url],
                           capture_output=True, text=True, timeout=3 * 3600)
    except subprocess.TimeoutExpired:
        return None
    return r.stdout.strip() or None if r.returncode == 0 else None


def podcast(kanaal: dict, max_items: int) -> list[dict]:
    feed = kanaal.get("feed_url") or podcast_feed(kanaal["url"])
    kanaal["feed_url"] = feed
    items = feed_items(haal(feed), kanaal["url"])[:max_items]
    # transcriberen kost op de cpu ~0,6× de speelduur: alleen afleveringen die nieuw zijn, en
    # hooguit PODCAST_PER_RONDE per ronde (de nieuwste eerst); de rest komt een volgende ronde
    bekend, nieuwste = kanaal.get("bekend") or set(), kanaal.get("nieuwste")
    uit = []
    for it in items:
        if len(uit) >= PODCAST_PER_RONDE:
            break
        if str(it.get("extern_id")) in bekend or (
                nieuwste and it.get("gepubliceerd") and it["gepubliceerd"] < nieuwste):
            continue
        t = spraak_naar_tekst(it["audio"]) if it.get("audio") else None
        if t:
            it["tekst"] = f"{it['tekst']}\n\n--- transcript (automatisch) ---\n{t}"
            it["tekstsoort"] = "transcript"
            uit.append(it)
    return uit


# ---------------------------------------------------------------- Telegram

def telegram_naam(url: str) -> str:
    m = re.search(r"(?:t\.me|telegram\.me)/(?:s/)?([\w]+)", url)
    return m.group(1) if m else url.lstrip("@")


def telegram_items(doc: str, naam: str) -> list[dict]:
    uit = []
    for blok in re.split(r'(?=<div class="tgme_widget_message_wrap)', doc)[1:]:
        post = re.search(r'data-post="([^"]+)"', blok)
        if not post:
            continue
        tekst_m = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
                            blok, re.S)
        tijd = re.search(r'<time[^>]*datetime="([^"]+)"', blok)
        tekst = html_naar_tekst((tekst_m.group(1) if tekst_m else "").replace("<br/>", "\n"),
                                "https://t.me/")
        if not tekst:
            continue
        uit.append({"extern_id": post.group(1), "url": f"https://t.me/{post.group(1)}",
                    "titel": tekst.split("\n", 1)[0][:120],
                    "gepubliceerd": iso(tijd.group(1)) if tijd else None,
                    "tekst": tekst, "tekstsoort": "tekst"})
    return uit


def telegram(kanaal: dict, max_items: int) -> list[dict]:
    naam = telegram_naam(kanaal["url"])
    items = telegram_items(haal(f"https://t.me/s/{naam}"), naam)
    return list(reversed(items))[:max_items]          # nieuwste eerst


# ---------------------------------------------------------------- sociaal (venv)

def sociaal(kanaal: dict, max_items: int) -> list[dict]:
    """X/Instagram/TikTok: sociaal.py onder de venv-python (Playwright/yt-dlp, achter de rem).
    Exit 75 = de rem weigert nu, 76 = blokkade/login nodig; beide → OphaalFout met de melding."""
    py = VENV_BIN / "python"
    if not py.exists():
        raise OphaalFout("tools/kanalen/.venv ontbreekt (zie tools/kanalen/README.md)")
    cmd = [str(py), str(HIER / "sociaal.py"), "haal", kanaal["platform"], kanaal["url"],
           "--max", str(max_items)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        melding = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or ["?"])[-1]
        raise OphaalFout(f"{kanaal['platform']} (exit {r.returncode}): {melding}")
    return json.loads(r.stdout or "[]")


def haal_kanaal(kanaal: dict, max_items: int = 5) -> list[dict]:
    p = kanaal["platform"]
    if p == "blog":
        items = blog(kanaal, max_items)
    elif p == "youtube":
        items = youtube(kanaal, max_items)
    elif p == "podcast":
        items = podcast(kanaal, max_items)
    elif p == "telegram":
        items = telegram(kanaal, max_items)
    elif p in SOCIAAL:
        items = sociaal(kanaal, max_items)
    else:
        raise OphaalFout(f"onbekend platform '{p}' (een van {PLATFORMS})")
    for it in items:
        it.pop("audio", None)
        it["tekst"] = (it.get("tekst") or "")[:MAX_TEKST]
        it["extern_id"] = str(it.get("extern_id") or it.get("url"))[:300]
    return [it for it in items if it["extern_id"]]


if __name__ == "__main__":
    # los proberen: python3 tools/kanalen/ophalen.py youtube https://www.youtube.com/@kanaal
    k = {"platform": sys.argv[1], "url": sys.argv[2]}
    for it in haal_kanaal(k, int(sys.argv[3]) if len(sys.argv) > 3 else 3):
        print(json.dumps({**it, "tekst": it["tekst"][:400]}, ensure_ascii=False, indent=1))
