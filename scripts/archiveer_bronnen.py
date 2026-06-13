#!/usr/bin/env python3
"""Archiveer URL-bronnen in de Wayback Machine (BRON-ARCHIEF-achterstand).

Voor elke bron met een url-vindplaats maar zonder archive_url-rij:
1. vraag de availability-API of er al een snapshot bestaat; zo ja, registreer die;
2. met --save: vraag anders een verse snapshot aan via Save Page Now
   (traag en rate-gelimiteerd; het script pauzeert tussen aanvragen).

Gebruik:
    python3 scripts/archiveer_bronnen.py            # bestaande snapshots registreren
    python3 scripts/archiveer_bronnen.py --save     # ook verse snapshots aanvragen
    python3 scripts/archiveer_bronnen.py --limit 5  # maximaal n bronnen behandelen
    python3 scripts/archiveer_bronnen.py --dry-run  # niets schrijven

Schrijft archive_url-rijen in source_locations. Dit is bron-metadata, geen inhoud:
net als scripts/register_source.py valt dit buiten de dogfood-regel (M0.6).
"""
import argparse
import datetime
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
# De availability-API (archive.org/wayback/available) geeft in de praktijk vaak
# ten onrechte géén snapshot terug; de CDX-API is de betrouwbare route.
CDX_API = ("https://web.archive.org/cdx/search/cdx?url={url}"
           "&output=json&limit=-1&fl=timestamp,original&filter=statuscode:200")
SAVE_URL = "https://web.archive.org/save/{url}"
USER_AGENT = "propaganda-model-archiveer-bronnen (onderzoeksproject; stdlib urllib)"
SAVE_PAUZE_S = 8  # Save Page Now is rate-gelimiteerd; wees terughoudend


def _get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=timeout)


def zoek_snapshot(url):
    """Nieuwste 200-snapshot via de CDX-API; None als die er niet is."""
    api = CDX_API.format(url=urllib.parse.quote(url, safe=""))
    with _get(api, timeout=30) as resp:
        tekst = resp.read().decode("utf-8").strip()
    rijen = json.loads(tekst) if tekst else []
    if len(rijen) >= 2:  # rij 0 is de kopregel
        ts, origineel = rijen[-1][0], rijen[-1][1]
        return f"https://web.archive.org/web/{ts}/{origineel}"
    return None


def vraag_snapshot_aan(url):
    """Verse snapshot via Save Page Now; geeft de snapshot-URL of None."""
    with _get(SAVE_URL.format(url=url), timeout=120) as resp:
        eind = resp.geturl()
    if "/web/" in eind:
        return eind.replace("http://", "https://", 1)
    return None


def bronnen_zonder_archief(conn):
    """Per bron zonder archive_url-rij de eerste url-vindplaats."""
    return conn.execute("""
        SELECT s.id AS source_id, s.title, l.location AS url
        FROM sources s
        JOIN source_locations l ON l.source_id = s.id AND l.location_type = 'url'
        WHERE NOT EXISTS (SELECT 1 FROM source_locations a
                          WHERE a.source_id = s.id AND a.location_type = 'archive_url')
        GROUP BY s.id
        ORDER BY s.id
    """).fetchall()


def registreer(conn, source_id, snapshot, dry_run):
    if dry_run:
        return
    conn.execute("""
        INSERT INTO source_locations (source_id, location_type, location, accessed_at, notes)
        VALUES (?, 'archive_url', ?, ?, 'Wayback-snapshot geregistreerd door scripts/archiveer_bronnen.py')
    """, (source_id, snapshot, datetime.date.today().isoformat()))
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--save", action="store_true",
                        help="vraag een verse snapshot aan als er nog geen bestaat")
    parser.add_argument("--limit", type=int, default=None,
                        help="maximaal n bronnen behandelen")
    parser.add_argument("--dry-run", action="store_true", help="niets schrijven")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    werk = bronnen_zonder_archief(conn)
    if args.limit:
        werk = werk[:args.limit]
    print(f"{len(werk)} bron(nen) zonder archive_url{' (dry-run)' if args.dry_run else ''}")

    gevonden, aangevraagd, open_blijft = 0, 0, []
    for rij in werk:
        kop = f"bron #{rij['source_id']}: {rij['title'][:60]}"
        try:
            snapshot = zoek_snapshot(rij["url"])
        except Exception:  # noqa: BLE001 — de CDX-API time-out geregeld; één herkansing
            try:
                snapshot = zoek_snapshot(rij["url"])
            except Exception as exc:  # noqa: BLE001 — daarna rapporteren, niet stoppen
                print(f"  ? {kop} — CDX-API faalde ({type(exc).__name__})")
                open_blijft.append(rij)
                continue
        if snapshot:
            registreer(conn, rij["source_id"], snapshot, args.dry_run)
            gevonden += 1
            print(f"  ✓ {kop} — bestaande snapshot")
            continue
        if not args.save:
            open_blijft.append(rij)
            print(f"  · {kop} — geen snapshot (gebruik --save om er een aan te vragen)")
            continue
        try:
            snapshot = vraag_snapshot_aan(rij["url"])
        except Exception as exc:  # noqa: BLE001
            snapshot = None
            print(f"  ? {kop} — Save Page Now faalde ({type(exc).__name__})")
        if snapshot:
            registreer(conn, rij["source_id"], snapshot, args.dry_run)
            aangevraagd += 1
            print(f"  ✓ {kop} — verse snapshot aangevraagd")
        else:
            open_blijft.append(rij)
        time.sleep(SAVE_PAUZE_S)

    conn.close()
    print(f"\nKlaar: {gevonden} bestaande snapshot(s) geregistreerd, "
          f"{aangevraagd} vers aangevraagd, {len(open_blijft)} open.")
    if open_blijft and not args.save:
        print("Open gevallen opnieuw proberen met: python3 scripts/archiveer_bronnen.py --save")
    return 0


if __name__ == "__main__":
    sys.exit(main())
