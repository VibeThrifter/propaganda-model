#!/usr/bin/env python3
"""Migratie (structuur): voeg de waarde 'inkomensaandeel' toe aan de CHECK van
arguments.property.

Achtergrond: de inkomstensamenstelling van een outlet wordt model-getrouw afgeleid
uit haar inkomende financierings-edges, waarbij elke edge een GESOURCET aandeel draagt
als aspect-argument (property='inkomensaandeel', property_value='<pct>:<jaar>'). Dat is
een nieuwe property-waarde; de live-DB handhaaft de CHECK op arguments.property, dus de
enum moet verruimd worden.

SQLite kan een CHECK niet met ALTER wijzigen, en nieuwere builds weigeren een directe
write op sqlite_master (defensive mode). Daarom de canonieke 12-staps tabel-herbouw:

  foreign_keys=OFF, legacy_alter_table=ON (domme rename — laat FK-clausules met rust),
  nieuwe tabel met dezelfde kolomvolgorde + verruimde enum, rijen kopiëren (id's
  behouden), oude tabel droppen, nieuwe hernoemen, indexen hermaken, foreign_key_check.

De nieuwe CREATE wordt AFGELEID uit sqlite_master (alleen de tabelnaam + de enum-regel
aangepast), niet overgetypt, zodat alle kolommen/constraints exact matchen. Idempotent.
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
ANKER = "'compositie',"
NIEUW = "'compositie',\n        'inkomensaandeel',"


def main():
    if not DB.exists():
        sys.exit(f"DB niet gevonden: {DB}")

    conn = sqlite3.connect(DB)
    conn.isolation_level = None  # expliciete transactiebesturing
    create_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='arguments'"
    ).fetchone()[0]

    if "'inkomensaandeel'" in create_sql:
        print("✓ 'inkomensaandeel' zit al in de CHECK — niets te doen (idempotent).")
        conn.close()
        return
    if create_sql.count(ANKER) != 1:
        conn.close()
        sys.exit(f"FOUT: anker {ANKER!r} komt {create_sql.count(ANKER)}× voor (verwacht 1).")

    # Nieuwe CREATE: tabelnaam → arguments_new (alleen de declaratie, niet de self-FK
    # 'REFERENCES arguments(id)' — die wijst straks ná de rename correct naar zichzelf),
    # en de enum-regel verruimen.
    # Tabelnaam kan gequote zijn (CREATE TABLE "arguments") of kaal.
    if 'CREATE TABLE "arguments"' in create_sql:
        kop_oud, kop_nieuw = 'CREATE TABLE "arguments"', 'CREATE TABLE "arguments_new"'
    elif "CREATE TABLE arguments" in create_sql:
        kop_oud, kop_nieuw = "CREATE TABLE arguments", "CREATE TABLE arguments_new"
    else:
        conn.close()
        sys.exit("FOUT: onverwachte CREATE-vorm voor arguments.")
    nieuwe_create = create_sql.replace(kop_oud, kop_nieuw, 1).replace(ANKER, NIEUW)

    index_ddls = [r[0] for r in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='arguments' "
        "AND sql IS NOT NULL").fetchall()]
    n_voor = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB.parent / f"propaganda_model_backup_{stamp}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}  ({n_voor} argumenten)")

    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("PRAGMA legacy_alter_table=ON")
    conn.execute("BEGIN")
    try:
        conn.execute(nieuwe_create)
        conn.execute("INSERT INTO arguments_new SELECT * FROM arguments")
        conn.execute("DROP TABLE arguments")
        conn.execute("ALTER TABLE arguments_new RENAME TO arguments")
        for ddl in index_ddls:
            conn.execute(ddl)
        schendingen = conn.execute("PRAGMA foreign_key_check").fetchall()
        if schendingen:
            raise RuntimeError(f"foreign_key_check schendingen: {schendingen}")
        n_na = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
        if n_na != n_voor:
            raise RuntimeError(f"rijtelling wijkt af: {n_voor} → {n_na}")
        conn.execute("COMMIT")
    except Exception as e:
        conn.execute("ROLLBACK")
        conn.close()
        sys.exit(f"FOUT — teruggerold, DB ongewijzigd: {e}")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.close()

    # Verifieer in een verse connectie: integriteit + dat de nieuwe waarde insertbaar is
    # en de CHECK nog handhaaft.
    conn = sqlite3.connect(DB)
    conn.isolation_level = None
    ic = conn.execute("PRAGMA integrity_check").fetchone()[0]
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    print(f"integrity_check: {ic}")
    print(f"foreign_key_check: {'OK' if not fk else fk}")
    if ic != "ok" or fk:
        sys.exit("FOUT: integriteitscheck faalde — herstel uit de backup.")

    rid = conn.execute("SELECT id FROM relations LIMIT 1").fetchone()[0]
    conn.execute("BEGIN")
    conn.execute("INSERT INTO arguments (relation_id, property, property_value, stance, "
                 "claim, contributed_by, status) VALUES (?,?,?,?,?,?,?)",
                 (rid, "inkomensaandeel", "56:2024", "supporting", "dry", "assistent",
                  "voorgesteld"))
    conn.execute("ROLLBACK")
    print("✓ insert met property='inkomensaandeel' lukt.")
    try:
        conn.execute("BEGIN")
        conn.execute("INSERT INTO arguments (relation_id, property, stance, claim, "
                     "contributed_by, status) VALUES (?,?,?,?,?,?)",
                     (rid, "onzin_xyz", "supporting", "dry", "assistent", "voorgesteld"))
        conn.execute("ROLLBACK")
        conn.close()
        sys.exit("FOUT: CHECK handhaaft niet meer.")
    except sqlite3.IntegrityError:
        print("✓ CHECK handhaaft nog steeds (onzin-property geweigerd).")
    conn.close()
    print(f"Klaar — {n_voor} argumenten behouden.")


if __name__ == "__main__":
    main()
