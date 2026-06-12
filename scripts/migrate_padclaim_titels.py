#!/usr/bin/env python3
"""
Migratie: titels voor padclaims (afgeleide/indirecte pijlen).

De labels op de afgeleide pijlen toonden een afgekapte claimzin; dat leest
rommelig. Elke padclaim (arguments.property = 'indirecte_invloed_op') krijgt
een korte redactionele titel in een nieuwe kolom `arguments.title`, die de viz
als pijl-label toont. De kolom is generiek (ook andere argumenten zouden een
titel kunnen krijgen), maar wordt hier alleen voor de 18 padclaims gevuld.

Conform repo-conventie: eerst backup (data/propaganda_model_backup_<ts>.db),
dan muteren. Idempotent: de ALTER wordt overgeslagen als de kolom al bestaat,
de UPDATEs overschrijven hooguit dezelfde waarden. schema.sql is in dezelfde
commit bijgewerkt voor verse builds.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# argument-id -> korte titel (bron -> doel ter referentie in de comment)
TITELS = {
    402: "Hoofdredacteur via de benoemingsketen",     # mediaeigenaar -> hoofdredacteur
    403: "Bestuur via STAK en RvC",                   # mediaeigenaar -> directie
    404: "Toezicht via STAK-stemrechten",             # mediaeigenaar -> raad_van_commissarissen
    405: "Controle over de holding",                  # mediaeigenaar -> overnamevehikel
    406: "Sturing via de holdingstructuur",           # mediaeigenaar -> mediaorganisatie
    407: "Eigendom kleurt het nieuwsbeeld",           # mediaeigenaar -> publiek
    408: "Getrapte bestuursbenoeming",                # aandeelhouder -> directie
    409: "Directie via greep op de RvC",              # administratiekantoor -> directie
    410: "Gelobbyde Kamervragen",                     # belanghebbende -> politicus
    411: "Geplante verhalen via de lobbyist",         # belanghebbende -> journalist
    412: "Belangen framen het nieuws",                # belanghebbende -> publiek
    413: "Advertentievriendelijk nieuwsbeeld",        # adverteerder -> publiek
    414: "Uniform nieuwsbeeld via het ANP",           # persbureau -> publiek
    415: "De officiële versie domineert",             # gezagsinstituut -> publiek
    416: "Expertframes via de media",                 # denktank -> publiek
    418: "Sturing via NPO-benoemingen",               # politicus -> ledenomroep
    422: "Politieke regie in het nieuws",             # politicus -> publiek
    423: "Doorgegeven voorlichting",                  # voorlichter -> publiek
}


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cols = [r[1] for r in cur.execute("PRAGMA table_info(arguments)")]
    if "title" not in cols:
        cur.execute("ALTER TABLE arguments ADD COLUMN title TEXT")
        print("Kolom arguments.title toegevoegd")
    else:
        print("Kolom arguments.title bestond al")

    for aid, titel in TITELS.items():
        row = cur.execute(
            "SELECT property FROM arguments WHERE id = ?", (aid,)
        ).fetchone()
        if not row or row[0] != "indirecte_invloed_op":
            print(f"  OVERGESLAGEN: argument {aid} is geen padclaim ({row})")
            continue
        cur.execute("UPDATE arguments SET title = ? WHERE id = ?", (titel, aid))
        print(f"  {aid}: {titel}")

    leeg = cur.execute(
        "SELECT COUNT(*) FROM arguments WHERE property = 'indirecte_invloed_op' AND title IS NULL"
    ).fetchone()[0]
    if leeg:
        print(f"LET OP: {leeg} padclaim(s) nog zonder titel")

    conn.commit()
    conn.close()
    print("Klaar.")


if __name__ == "__main__":
    main()
