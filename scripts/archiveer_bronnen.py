#!/usr/bin/env python3
"""Archiveer URL-bronnen in de Wayback Machine (BRON-ARCHIEF-achterstand).

Voor elke bron met een url-vindplaats maar zonder archive_url-rij:
1. vraag via de CDX-API of er al een snapshot bestaat; zo ja, registreer die;
2. met --save: vraag anders een verse snapshot aan via Save Page Now
   (traag en rate-gelimiteerd; het script pauzeert tussen aanvragen).

Gebruik (zie ook scripts/run_archivering.md voor de gebatchte cadans):
    python3 scripts/archiveer_bronnen.py --tel          # alleen het percentage tonen (geen netwerk)
    python3 scripts/archiveer_bronnen.py                # bestaande CDX-snapshots registreren
    python3 scripts/archiveer_bronnen.py --save         # ook verse snapshots aanvragen
    python3 scripts/archiveer_bronnen.py --save --limit 10   # één gebatchte dag-run
    python3 scripts/archiveer_bronnen.py --dry-run      # niets schrijven (preview)

Twee-fasen-werkwijze (bewust ontkoppeld tegen de SPN-rate-limit):
  * eerst een goedkope pass ZONDER --save: die registreert alleen reeds bestaande
    snapshots via de CDX-API en verspilt geen Save-Page-Now-quota;
  * daarna gebatchte --save-runs (--limit N over meerdere dagen) voor de rest.
`bronnen_zonder_archief` is idempotent: bronnen die al een archive_url hebben worden
overgeslagen, dus een herdraai archiveert nooit dubbel.

Robuustheid: CDX wordt gepaced (CDX_PAUZE_S) en vangt 429/time-outs met exponentiële
backoff (CDX_BACKOFF_S) — een load-bearing schema-run mag de rate-limit niet uithongeren.
Elke run logt een regel naar data/archiveer_log.jsonl (source-ids + tellingen per batch).

Schrijft archive_url-rijen in source_locations. Dit is bron-metadata, geen inhoud:
net als scripts/register_source.py valt dit buiten de dogfood-regel (M0.6) — het is
een OS-/schema-taak, geen agent-bijdragepad.
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
LOG_PATH = Path(__file__).parent.parent / "data" / "archiveer_log.jsonl"
# De availability-API (archive.org/wayback/available) geeft in de praktijk vaak
# ten onrechte géén snapshot terug; de CDX-API is de betrouwbare route.
CDX_API = ("https://web.archive.org/cdx/search/cdx?url={url}"
           "&output=json&limit=-1&fl=timestamp,original&filter=statuscode:200")
# Vangnet-endpoint: de availability-API zit los van de CDX-rate-limit, dus als CDX
# 429't kunnen we hier alsnog een bestaande snapshot vinden. Minder volledig (geeft
# soms ten onrechte 'geen'), daarom alléén als fallback en nooit als grond voor een save.
AVAIL_API = "https://archive.org/wayback/available?url={url}"
SAVE_URL = "https://web.archive.org/save/{url}"
USER_AGENT = "propaganda-model-archiveer-bronnen (onderzoeksproject; stdlib urllib)"
SAVE_PAUZE_S = 8       # Save Page Now is rate-gelimiteerd; wees terughoudend
CDX_PAUZE_S = 2.0      # kleine pauze tussen CDX-calls om de 429-drempel te ontwijken
CDX_BACKOFF_S = 20     # basiswachttijd na een 429; verdubbelt per poging (20+40 = 60s)
CDX_MAX_POGINGEN = 3   # pogingen per bron; daarna latcht de run op de availability-fallback


def _get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=timeout)


class Ratelimiet(Exception):
    """CDX bleef 429 geven na alle pogingen — een tijdelijke, herstelbare toestand."""


def zoek_snapshot(url):
    """Nieuwste 200-snapshot via de CDX-API; None als die er niet is.

    Pace + backoff: op een 429 (Too Many Requests) wachten we (Retry-After of
    exponentiële backoff) en proberen opnieuw; op een time-out één korte herkansing.
    Blijft het na CDX_MAX_POGINGEN falen, dan raise Ratelimiet zodat de aanroeper
    de bron als 'open' laat i.p.v. 'geen snapshot'.
    """
    api = CDX_API.format(url=urllib.parse.quote(url, safe=""))
    wacht = CDX_BACKOFF_S
    laatste = None
    for _ in range(CDX_MAX_POGINGEN):
        try:
            with _get(api, timeout=30) as resp:
                tekst = resp.read().decode("utf-8").strip()
            rijen = json.loads(tekst) if tekst else []
            if len(rijen) >= 2:  # rij 0 is de kopregel
                ts, origineel = rijen[-1][0], rijen[-1][1]
                return f"https://web.archive.org/web/{ts}/{origineel}"
            return None
        except urllib.error.HTTPError as exc:
            laatste = exc
            if exc.code == 429:
                retry_after = (exc.headers.get("Retry-After") or "").strip()
                pauze = int(retry_after) if retry_after.isdigit() else wacht
                time.sleep(pauze)
                wacht *= 2
                continue
            raise
        except Exception as exc:  # noqa: BLE001 — time-out e.d.: korte herkansing
            laatste = exc
            time.sleep(2)
    raise Ratelimiet(str(laatste))


def zoek_snapshot_availability(url):
    """Vangnet-lookup via de availability-API; None als die er geen geeft.

    Losse endpoint dat níet meevalt onder de CDX-429. Minder volledig dan CDX
    (kan een bestaande snapshot missen), dus enkel als fallback wanneer CDX
    rate-gelimiteerd is; een 'None' hiervan is niet gezaghebbend.
    """
    api = AVAIL_API.format(url=urllib.parse.quote(url, safe=""))
    with _get(api, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8") or "{}")
    snap = (data.get("archived_snapshots") or {}).get("closest") or {}
    if snap.get("available") and snap.get("url"):
        return snap["url"].replace("http://", "https://", 1)
    return None


def archiveer_stand(conn):
    """(#url-bronnen met een archive_url, #url-bronnen totaal)."""
    totaal = conn.execute(
        "SELECT COUNT(DISTINCT source_id) FROM source_locations "
        "WHERE location_type = 'url'"
    ).fetchone()[0]
    gearchiveerd = conn.execute(
        "SELECT COUNT(DISTINCT u.source_id) FROM source_locations u "
        "WHERE u.location_type = 'url' AND EXISTS ("
        "  SELECT 1 FROM source_locations a "
        "  WHERE a.source_id = u.source_id AND a.location_type = 'archive_url')"
    ).fetchone()[0]
    return gearchiveerd, totaal


def toon_stand(conn, prefix=""):
    g, t = archiveer_stand(conn)
    pct = round(100 * g / t, 1) if t else 0.0
    print(f"{prefix}{g}/{t} url-bronnen gearchiveerd ({pct}%)")
    return pct


def log_batch(record):
    """Append één JSON-regel per run naar data/archiveer_log.jsonl (best-effort)."""
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:  # noqa: BLE001 — loggen mag de run nooit breken
        print(f"  (waarschuwing: kon batch-log niet schrijven: {exc})")


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
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--save", action="store_true",
                        help="vraag een verse snapshot aan als er nog geen bestaat")
    parser.add_argument("--limit", type=int, default=None,
                        help="maximaal n bronnen behandelen (gebatchte dag-run)")
    parser.add_argument("--dry-run", action="store_true", help="niets schrijven (preview)")
    parser.add_argument("--tel", action="store_true",
                        help="alleen het gearchiveerd-percentage tonen (geen netwerk, geen schrijf)")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Goedkope telstand: alleen DB, geen netwerk — handig als kerngetal (C3/C4).
    if args.tel:
        werk = bronnen_zonder_archief(conn)
        toon_stand(conn)
        print(f"{len(werk)} bron(nen) zonder archive_url.")
        conn.close()
        return 0

    pct_voor = toon_stand(conn, prefix="Voor:  ")

    werk = bronnen_zonder_archief(conn)
    if args.limit:
        werk = werk[:args.limit]
    print(f"{len(werk)} bron(nen) zonder archive_url in deze run"
          f"{' (dry-run)' if args.dry_run else ''}")

    gevonden, aangevraagd, open_geen, open_fout, behandeld = 0, 0, [], [], []
    cdx_uit = False  # latch: zodra CDX aanhoudend 429't, rest van de run via fallback
    try:
        for rij in werk:
            behandeld.append(rij["source_id"])
            kop = f"bron #{rij['source_id']}: {rij['title'][:60]}"
            snapshot = None
            gezaghebbend_nee = False  # heeft CDX écht 'geen snapshot' bevestigd?

            if not cdx_uit:
                try:
                    snapshot = zoek_snapshot(rij["url"])
                    gezaghebbend_nee = snapshot is None
                except Ratelimiet:
                    # CDX ligt aanhoudend eruit: latch aan; niet elke bron opnieuw
                    # de volle backoff betalen — de rest van deze run leunt op de
                    # availability-fallback (een volgende run pakt de volledige CDX weer).
                    cdx_uit = True
                    print("  (CDX aanhoudend rate-gelimiteerd (429) — rest van deze "
                          "run via availability-fallback; herdraai later voor volledige CDX)")
                except Exception as exc:  # noqa: BLE001 — rapporteren, niet stoppen
                    print(f"  ? {kop} — CDX-API faalde ({type(exc).__name__})")
                    open_fout.append(rij)
                    time.sleep(CDX_PAUZE_S)
                    continue

            if snapshot is None and cdx_uit:
                # Vangnet: availability-API (losse endpoint, niet 429). Een 'None'
                # hiervan is NIET gezaghebbend (availability mist er soms een), dus
                # het triggert geen save — dat blijft voor een volgende CDX-run.
                try:
                    snapshot = zoek_snapshot_availability(rij["url"])
                except Exception:  # noqa: BLE001
                    snapshot = None

            if snapshot:
                registreer(conn, rij["source_id"], snapshot, args.dry_run)
                gevonden += 1
                extra = " (availability-fallback)" if cdx_uit else ""
                print(f"  ✓ {kop} — bestaande snapshot{extra}")
                time.sleep(CDX_PAUZE_S)
                continue

            if not args.save:
                open_geen.append(rij)
                print(f"  · {kop} — geen snapshot (gebruik --save om er een aan te vragen)")
                time.sleep(CDX_PAUZE_S)
                continue

            if not gezaghebbend_nee:
                # Onzeker (CDX uit én availability gaf niets): niet blind saven — anders
                # dupliceren we een snapshot die CDX straks wél zou vinden.
                open_fout.append(rij)
                print(f"  ? {kop} — onzeker (CDX uit, geen fallback-snapshot); geen save, volgende run")
                time.sleep(CDX_PAUZE_S)
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
                open_fout.append(rij)
            time.sleep(SAVE_PAUZE_S)
    except KeyboardInterrupt:
        print("\n(onderbroken — reeds geregistreerde snapshots blijven behouden)")

    pct_na = toon_stand(conn, prefix="Na:    ")
    print(f"Klaar: {gevonden} bestaande snapshot(s) geregistreerd, "
          f"{aangevraagd} vers aangevraagd, "
          f"{len(open_geen)} zonder snapshot, {len(open_fout)} door fout/rate-limit open.")
    if not args.dry_run:
        log_batch({
            "datum": datetime.datetime.now().isoformat(timespec="seconds"),
            "modus": "save" if args.save else "cdx",
            "limit": args.limit,
            "behandeld": len(behandeld),
            "gevonden": gevonden,
            "aangevraagd": aangevraagd,
            "open_geen_snapshot": len(open_geen),
            "open_fout": len(open_fout),
            "pct_voor": pct_voor,
            "pct_na": pct_na,
            "source_ids": behandeld,
        })
    if open_geen and not args.save:
        print("Bronnen zonder bestaande snapshot: gebatcht aanvragen met "
              "python3 scripts/archiveer_bronnen.py --save --limit N (zie scripts/run_archivering.md)")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
