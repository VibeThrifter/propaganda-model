"""
Modelreview — `overheidsadvertenties` schrappen (redundante directe principaal->media-pijl).

`overheidsadvertenties` (belanghebbende -> mediaorganisatie, advertentie) doorbrak het
model-principe dat de principaal de media NOOIT direct raakt: advertentie-invloed loopt altijd
via de adverteerder-hoed (`belanghebbende -> adverteerder` [`adverteren_als_belang`] ->
`mediaorganisatie` [`advertentiedruk`/`commerciele_afhankelijkheid`]). De overheid is gewoon een
`belanghebbende` (aard: overheidsorgaan) die die hoed draagt; de directe pijl is dus redundant
met de bestaande route via de adverteerder-node.

Fix: mechanisme verwijderen (guard: 0 verwijzingen) en de staat-als-adverteerder-nuance opnemen
in `adverteren_als_belang`. Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

REMOVE = "overheidsadvertenties"

ENRICH = {
    "name": "adverteren_als_belang",
    "description": (
        "De eerste schakel van het advertentie-instrument: een belanghebbende zet advertentiebudget "
        "in en verschijnt richting de redactie in de 'adverteerder-hoed'. Dezelfde principaal die "
        "elders lobbyt of procedeert, drukt hier via de advertentie-euro. De belanghebbende kan "
        "commercieel zijn (retail, FMCG, loterijen — de grootste hefboom) maar óók een overheidsorgaan: "
        "de Rijksoverheid is via Dienst Publiek en Communicatie/VoRa een van de grootste enkele "
        "adverteerders (~€21-25 mln/jaar). Niet elke belanghebbende drukt even hard; grote, "
        "geconcentreerde adverteerders hebben de meeste hefboom."
    ),
    "effect": (
        "Maakt expliciet dat de adverteerder geen losse actor is maar een verschijningsvorm van een "
        "belanghebbende (commercieel óf overheid). De vervolgschakel naar de media is het bestaande "
        "`advertentiedruk` / `commerciele_afhankelijkheid` — de principaal raakt de redactie dus nooit "
        "direct."
    ),
}


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bp = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, bp)
    print(f"Backup gemaakt: {bp.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("\n-- verwijderen overheidsadvertenties --")
    row = conn.execute("SELECT id FROM mechanisms WHERE name=?", (REMOVE,)).fetchone()
    if row is None:
        print("  bestaat niet (al weg) — overgeslagen.")
    else:
        mid = row[0]
        n = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (mid,)).fetchone()[0]
        if n:
            print(f"  NIET verwijderd: {n} relaties hangen er nog aan — laat staan.")
        else:
            conn.execute("DELETE FROM instantiations WHERE mechanism_id=?", (mid,))
            conn.execute("DELETE FROM arguments WHERE mechanism_id=?", (mid,))
            conn.execute("DELETE FROM mechanisms WHERE id=?", (mid,))
            print(f"  verwijderd (0 relaties): {REMOVE}")

    print("\n-- aanscherpen adverteren_als_belang (staat-als-adverteerder-nuance) --")
    cur = conn.execute(
        "UPDATE mechanisms SET description=?, effect=? WHERE name=?",
        (ENRICH["description"], ENRICH["effect"], ENRICH["name"]),
    )
    print(f"  {'aangescherpt' if cur.rowcount else 'NIET gevonden'}: {ENRICH['name']}")

    conn.commit()
    print("\n== verificatie ==")
    gone = conn.execute("SELECT COUNT(*) FROM mechanisms WHERE name=?", (REMOVE,)).fetchone()[0]
    print(f"  overheidsadvertenties aanwezig (verwacht 0): {gone}")
    print("  directe belanghebbende→mediaorganisatie-mechanismen (verwacht alleen financierings-cross_filter):")
    rows = conn.execute(
        """SELECT m.name, m.filter FROM mechanisms m
           JOIN roles sr ON sr.id=m.source_role_id JOIN roles tr ON tr.id=m.target_role_id
           WHERE sr.name='belanghebbende' AND tr.name='mediaorganisatie' ORDER BY m.name"""
    ).fetchall()
    for r in rows:
        print(f"    {r[0]} ({r[1]})")
    n = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen: {n}.")


if __name__ == "__main__":
    main()
