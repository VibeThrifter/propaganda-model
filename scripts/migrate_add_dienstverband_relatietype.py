"""Voeg 'dienstverband' toe aan de relation_type-enum (CHECK) van de relations-tabel.

Aanleiding: RfC #41 ('dienstverband', Eigendom, mediaorganisatie -> journalist) is de
gerichte filter-edge onder de zelfcensuur — de materiele arbeids-/inkomensafhankelijkheid
van de journalist t.o.v. de organisatie die hem betaalt. Die relatie heeft een EIGEN
relatietype nodig: 'personeel' zit in BRUG_AFFILIATIE (persoon<->org-affiliatie-brug), dus
dat hergebruiken zou de brug-afleiding vervuilen (org<->org-bruggen via elke journalist).
'dienstverband' is een gerichte edge, GEEN affiliatie-brug -> bewust NIET in BRUG_AFFILIATIE.

Structuur/schema-migratie (geen inhoud): breidt alleen uit wat toekomstige inserts mogen.
Verandert geen bestaande rijen; laat data, FK's (arguments/instantiations) en indexes intact
door alleen de CHECK in het opgeslagen CREATE-statement te herschrijven (writable_schema).
"""
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NIEUW = "'dienstverband',         -- economische afhankelijkheid journalist<-org (Eigendom-filter)"
ANKER = "'personeel',"


def main():
    backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy(DB, backup)
    print(f"backup -> {backup.name}")

    conn = sqlite3.connect(DB)
    sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='relations'"
    ).fetchone()[0]

    if "'dienstverband'" in sql:
        print("relation_type 'dienstverband' bestaat al — niets te doen.")
        conn.close()
        return

    if ANKER not in sql:
        raise SystemExit("anker 'personeel' niet gevonden in CREATE-statement; migratie afgebroken.")

    nieuw_sql = sql.replace(ANKER, ANKER + "\n                " + NIEUW)
    # relations_new bouwen we van hetzelfde CREATE-statement, alleen hernoemd.
    nieuw_sql_tmp = nieuw_sql.replace("CREATE TABLE relations", "CREATE TABLE relations_new", 1)

    kolommen = [r[1] for r in conn.execute("PRAGMA table_info(relations)")]
    kol_csv = ", ".join(kolommen)

    conn.execute("PRAGMA foreign_keys=OFF")
    conn.executescript(
        f"""
        BEGIN;
        {nieuw_sql_tmp};
        INSERT INTO relations_new ({kol_csv}) SELECT {kol_csv} FROM relations;
        DROP TABLE relations;
        ALTER TABLE relations_new RENAME TO relations;
        CREATE INDEX idx_relations_source ON relations(source_id);
        CREATE INDEX idx_relations_target ON relations(target_id);
        CREATE INDEX idx_relations_type ON relations(relation_type);
        CREATE INDEX idx_relations_mechanism ON relations(mechanism_id);
        COMMIT;
        """
    )
    conn.execute("PRAGMA foreign_keys=ON")
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        raise SystemExit(f"FOUT: foreign_key_check niet leeg na rebuild: {fk[:5]}")
    conn.commit()
    conn.close()

    # Heropenen zodat de nieuwe schema-cache geldt; integriteit + CHECK verifieren.
    conn = sqlite3.connect(DB)
    ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
    print("integrity_check:", ok)
    conn.execute("PRAGMA foreign_keys=ON")
    # Test: een 'dienstverband'-insert moet nu slagen, een onzin-type moet nog falen.
    conn.execute("BEGIN")
    try:
        conn.execute(
            "INSERT INTO relations (source_id,target_id,relation_type,certainty,influence) "
            "SELECT source_id,target_id,'dienstverband',certainty,influence FROM relations LIMIT 1"
        )
        print("insert 'dienstverband': OK")
    finally:
        conn.execute("ROLLBACK")
    try:
        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO relations (source_id,target_id,relation_type,certainty,influence) "
            "SELECT source_id,target_id,'zomaarwat',certainty,influence FROM relations LIMIT 1"
        )
        conn.execute("ROLLBACK")
        raise SystemExit("FOUT: CHECK laat onzin-type toe — migratie verdacht.")
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        print("CHECK weigert onzin-type: OK")
    conn.close()
    print("klaar.")


if __name__ == "__main__":
    main()
