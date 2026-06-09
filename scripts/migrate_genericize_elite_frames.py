"""
Modelreview — elite-frames genereik in de theorie, specifiek in de praktijk.

Probleem (theorielaag = abstract, géén namen): `stakeholder_capitalism_frame` was genoemd
naar één specifiek frame (WEF, Davos 2020), had 0 instances, en wees naar het verkeerde
kanaal (elite_forum → publiek — terwijl het publiek elite-frames via de media krijgt, niet
rechtstreeks van Davos). Het was dus een instance-concept dat in de theorielaag hing.

Actie:
  1. Verwijder `stakeholder_capitalism_frame` (0 relaties; mechanism_filters/themes mee).
     De generieke elite→media-instroom blijft staan: `ideologische_synchronisatie`
     (→ eigenaar) en `transnationale_frame_export` (→ org). Het publiek krijgt het frame via
     de bestaande media→publiek-effecten (emergente_bias, columnist_als_hegemon, ...).
  2. Zet de SPECIFIEKE frames in het PRAKTIJKMODEL: per elite_forum-entiteit een expliciete
     "Frame: ..."-notitie in de description (een frame is een eigenschap van de club, dus
     instance-niveau). WEF/NAVO noemden het al; nu uniform en aangevuld voor de rest.

Idempotent (skip als 'Frame:' al in de description staat); backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

REMOVE_MECH = "stakeholder_capitalism_frame"

CLUB_FRAMES = {
    "World Economic Forum": "stakeholder capitalism / ESG / Great Reset",
    "NAVO": "Atlantische veiligheidslogica (pro-Atlantisch defensieframe)",
    "Bilderberg Groep": "transatlantische politieke consensus",
    "European Round Table of Industrialists": "industriële concurrentiekracht en deregulering",
    "Trilaterale Commissie": "trilaterale geopolitieke coördinatie (VS–Europa–Azië) van de "
                             "transnationale kapitaalklasse",
    "European Publishers Council": "uitgevers- en mediabeleidsbelangen (auteursrecht, "
                                   "platformregulering)",
}


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # 1. verwijder het frame-specifieke, lege theorie-mechanisme
    row = conn.execute("SELECT id FROM mechanisms WHERE name=?", (REMOVE_MECH,)).fetchone()
    if row:
        mid = row[0]
        nrel = conn.execute(
            "SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (mid,)).fetchone()[0]
        if nrel:
            raise SystemExit(f"FOUT: {REMOVE_MECH} heeft {nrel} relatie(s) — niet verwijderd.")
        conn.execute("DELETE FROM mechanism_filters WHERE mechanism_id=?", (mid,))
        conn.execute("DELETE FROM mechanism_themes WHERE mechanism_id=?", (mid,))
        conn.execute("DELETE FROM mechanisms WHERE id=?", (mid,))
        print(f"Verwijderd: {REMOVE_MECH} (+ filters/themes).")
    else:
        print(f"{REMOVE_MECH} bestaat niet (al weg).")

    # 2. specifieke frames → praktijkmodel (entity-descriptions)
    print("\nSpecifieke frames → entity-descriptions (praktijkmodel):")
    for club, frame in CLUB_FRAMES.items():
        r = conn.execute("SELECT id, description FROM entities WHERE name=?", (club,)).fetchone()
        if r is None:
            print(f"  WAARSCHUWING: entiteit '{club}' niet gevonden — overgeslagen.")
            continue
        eid, desc = r
        desc = desc or ""
        if "Frame:" in desc:
            print(f"  {club}: al getagd, overslaan.")
            continue
        newdesc = (desc.rstrip() + " " if desc.strip() else "") + f"Frame: {frame}."
        conn.execute("UPDATE entities SET description=? WHERE id=?", (newdesc, eid))
        print(f"  {club} → Frame: {frame}")

    conn.commit()

    print("\n== mechanismen per aard (controle) ==")
    for aard, n in conn.execute(
            "SELECT aard, COUNT(*) FROM mechanisms GROUP BY aard ORDER BY aard"):
        print(f"  {aard:18} {n}")
    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
