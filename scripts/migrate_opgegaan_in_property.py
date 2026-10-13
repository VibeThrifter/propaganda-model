#!/usr/bin/env python3
"""Schema-migratie: property 'opgegaan_in' in de CHECK-enum van arguments.property.

Fusies en opheffingen (eigenaarsbesluit 2026-10-13, "PvdA en GroenLinks samenvoegen met PRO … en
kijken of en hoe je banden van het verleden samenvoegt met fusies"). Een opgeheven organisatie
draagt een gesourcet aspect-argument `property='opgegaan_in'` met als `property_value` het id van
de opvolger. Het telt nergens mee (scoring.ASPECT_PROPERTIES), de bron is verplicht, en de
stamboom wordt afgeleid in looptijd.py (opvolgingen/stamboom). De banden van de voorganger blijven
van de voorganger. Zie DOCUMENTATIE.md § "Looptijd en bestaan".

SQLite kan een CHECK niet wijzigen, dus de tabel arguments wordt één keer herbouwd. De rebuild
gebruikt de opgeslagen definitie (sqlite_master) en voegt alleen de nieuwe enumwaarde in na
'bereik'. Kolomvolgorde, typen, overige CHECKs en indexen blijven gelijk.

Werkwijze: eerst een backup, dan de lock van de automatische beoordeling (geen ronde halverwege),
dan één transactie. Idempotent.

Gebruik: python3 scripts/migrate_opgegaan_in_property.py [--db pad]
"""
import argparse
import fcntl
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "propaganda_model.db"
LOCK_PATH = ROOT / "data" / "locks" / "automatische-beoordeling.lock"
NIEUW = "opgegaan_in"
NA = "bereik"


def migreer(db: Path, backup: bool = True) -> str:
    conn = sqlite3.connect(db, timeout=60)
    conn.row_factory = sqlite3.Row
    create_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='arguments'").fetchone()["sql"]
    if f"'{NIEUW}'" in create_sql:
        conn.close()
        return f"property '{NIEUW}' staat al in de CHECK — niets te doen"
    if create_sql.count(f"'{NA}'") != 1:
        conn.close()
        sys.exit(f"Onverwacht aantal '{NA}'-voorkomens in de definitie; afgebroken.")
    if backup:
        doel = db.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        bron = sqlite3.connect(db, timeout=60)
        kopie = sqlite3.connect(doel)
        bron.backup(kopie)          # consistente kopie, ook in WAL-modus
        kopie.close()
        bron.close()
        print(f"Backup: {doel.name}")

    if 'CREATE TABLE "arguments"' in create_sql:
        nieuw_sql = create_sql.replace('CREATE TABLE "arguments"', 'CREATE TABLE "arguments_new"', 1)
    elif "CREATE TABLE arguments" in create_sql:
        nieuw_sql = create_sql.replace("CREATE TABLE arguments", "CREATE TABLE arguments_new", 1)
    else:
        conn.close()
        sys.exit("Kon 'CREATE TABLE arguments' niet vinden in de opgeslagen definitie.")
    nieuw_sql = nieuw_sql.replace(f"'{NA}'", f"'{NA}',\n        '{NIEUW}'", 1)
    index_sqls = [r["sql"] for r in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='arguments' "
        "AND sql IS NOT NULL")]
    n_voor = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.isolation_level = None
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(nieuw_sql)
        conn.execute("INSERT INTO arguments_new SELECT * FROM arguments")
        conn.execute("DROP TABLE arguments")
        conn.execute("ALTER TABLE arguments_new RENAME TO arguments")
        for isql in index_sqls:
            conn.execute(isql)
        conn.execute("COMMIT")
    except Exception as e:  # noqa: BLE001
        conn.execute("ROLLBACK")
        conn.close()
        sys.exit(f"Migratie mislukt, teruggedraaid: {e}")
    conn.execute("PRAGMA foreign_keys = ON")
    n_na = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    fk = conn.execute("PRAGMA foreign_key_check(arguments)").fetchall()
    ok = f"'{NIEUW}'" in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='arguments'").fetchone()["sql"]
    conn.close()
    if n_voor != n_na or fk or not ok:
        sys.exit(f"VERIFICATIE GEFAALD (rijen {n_voor} → {n_na}, fk {fk}, check {ok}) — "
                 "herstel via de backup.")
    return f"klaar: {n_na} argumenten, CHECK bevat '{NIEUW}'"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--db", type=Path, default=DB)
    args = p.parse_args()
    if not args.db.exists():
        sys.exit(f"DB niet gevonden: {args.db}")
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_PATH, "a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit("De automatische beoordeling draait nu; probeer het zo opnieuw.")
        print(migreer(args.db))


if __name__ == "__main__":
    main()
