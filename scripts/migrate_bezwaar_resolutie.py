"""Resolutielus op ondergravingen (review-verdict v2).

Voegt `arguments.bezwaar_resolutie` toe: de stand van de resolutielus van een
ONDERGRAVING (contradicting reply). Een lezer die "logica klopt niet" kiest, levert
voortaan een onderbouwd bezwaar (verplichte reasoning, server-kant); de auteur kan
verbeteren ('herzien'), en de bezwaarmaker herbeoordeelt vervolgens ('opgelost' /
'blijft'). Scoring telt een 'opgelost' bezwaar niet meer als aanval.

  open      = vers bezwaar, auteur heeft nog niet gereageerd        → dempt
  herzien   = auteur zegt 'aangepast, herbeoordeel'                 → dempt
  blijft    = bezwaarmaker heeft herbeoordeeld en handhaaft         → dempt
  opgelost  = bezwaar weg (bezwaarmaker, of reviewer-overrule)      → dempt NIET
  NULL      = geen ondergraving (gewoon argument / +Voor / context)

Backfill: bestaande ondergravingen krijgen 'open' (dempt — identiek aan het huidige
gedrag, dus de golden snapshot verschuift niet). Structuurmigratie, geen inhoud.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def main():
    if not DB.exists():
        raise SystemExit(f"DB niet gevonden: {DB}")

    backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(arguments)")}
    if "bezwaar_resolutie" in cols:
        print("Kolom bezwaar_resolutie bestaat al — niets te doen.")
        conn.close()
        return

    conn.execute("ALTER TABLE arguments ADD COLUMN bezwaar_resolutie TEXT")
    n = conn.execute(
        "UPDATE arguments SET bezwaar_resolutie = 'open' "
        "WHERE parent_argument_id IS NOT NULL AND stance = 'contradicting'"
    ).rowcount
    conn.commit()
    print(f"Kolom toegevoegd; {n} bestaande ondergraving(en) op 'open' gezet (dempt, "
          "ongewijzigd gedrag).")
    conn.close()


if __name__ == "__main__":
    main()
