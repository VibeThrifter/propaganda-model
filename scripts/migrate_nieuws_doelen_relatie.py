#!/usr/bin/env python3
"""Schema/structuur-migratie: de nieuws-wachtrij `nieuws_doelen` krijgt de soort
'relatie' en de kolom `relation_id` (nieuws-aggregator Story 14.13, "dun bewijs").

Waarom: de nieuws-app toont bij elk nieuwsbericht welke verbanden uit dit model erachter
zitten. Veel daarvan rusten op één bron, of op een bron die de claim niet draagt. Zo'n
verband zet de nieuws-backend (account `nieuws-agent`) nu als onderzoeksdoel in de
wachtrij, sleutel 'relatie:<id>'. De missie-agent `nieuws-bewijs`
(missies/nieuws_bewijs_brief.md) zoekt er bewijs vóór én tegen. Procesmetadata, géén
inhoud: de tabel telt nog steeds in niets mee.

SQLite kan een CHECK niet ALTER-en, dus de tabel wordt één keer herbouwd (zelfde patroon
als migrate_objection_type_vrijtekst.py): de nieuwe definitie is exact die van
schema.sql, de rijen gaan mee (ids en AUTOINCREMENT-teller blijven), de index wordt
opnieuw aangelegd. Idempotent: staat 'relatie' al in de CHECK en bestaat de kolom, dan
gebeurt er niets. Backup-then-migrate per conventie.

Gebruik: python3 scripts/migrate_nieuws_doelen_relatie.py
"""
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migrate_add_nieuws_doelen import INDEX_DDL, NIEUWS_DOELEN_DDL, backup  # noqa: E402

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# De kolommen van vóór deze migratie, in hun opgeslagen volgorde
OUDE_KOLOMMEN = ("id", "sleutel", "naam", "soort", "rol_categorie", "rol_hint", "context",
                 "prioriteit", "entity_id", "status", "vervolg", "verslag", "resultaat",
                 "aangevraagd_door", "geclaimd_door", "geclaimd_op", "pogingen",
                 "aangemaakt", "bijgewerkt")
SOORT_CHECK = re.compile(r"CHECK\s*\(\s*soort\s+IN\s*\(([^)]*)\)\s*\)", re.IGNORECASE)


def nodig(conn) -> bool:
    """Heeft de bestaande tabel de soort 'relatie' en de kolom relation_id nog niet?"""
    rij = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' "
                       "AND name = 'nieuws_doelen'").fetchone()
    if rij is None:
        return False
    kolommen = {r[1] for r in conn.execute("PRAGMA table_info(nieuws_doelen)")}
    check = SOORT_CHECK.search(rij[0] or "")
    return "relation_id" not in kolommen or not check or "'relatie'" not in check.group(1)


def migreer(db: Path) -> list:
    """Herbouw de tabel als dat nodig is; geeft de lijst van wijzigingen terug."""
    conn = sqlite3.connect(db)
    conn.isolation_level = None      # alleen de expliciete BEGIN/COMMIT hieronder
    try:
        if not nodig(conn):
            print("nieuws_doelen kent de soort 'relatie' al (of bestaat niet) — overslaan.")
            return []
        kolommen = [r[1] for r in conn.execute("PRAGMA table_info(nieuws_doelen)")]
        mee = [k for k in OUDE_KOLOMMEN if k in kolommen]
        if "relation_id" in kolommen:
            mee.append("relation_id")
        voor = conn.execute("SELECT COUNT(*) FROM nieuws_doelen").fetchone()[0]
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("BEGIN")
        try:
            conn.execute("ALTER TABLE nieuws_doelen RENAME TO nieuws_doelen_oud")
            conn.execute(NIEUWS_DOELEN_DDL)
            lijst = ", ".join(mee)
            conn.execute(f"INSERT INTO nieuws_doelen ({lijst}) "  # noqa: S608 - vaste namen
                         f"SELECT {lijst} FROM nieuws_doelen_oud")
            conn.execute("DROP TABLE nieuws_doelen_oud")
            conn.execute(INDEX_DDL)
            na = conn.execute("SELECT COUNT(*) FROM nieuws_doelen").fetchone()[0]
            if na != voor:
                raise RuntimeError(f"rijen {voor} -> {na}")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        conn.execute("PRAGMA foreign_keys = ON")
        fouten = conn.execute("PRAGMA foreign_key_check(nieuws_doelen)").fetchall()
        if fouten:
            raise RuntimeError(f"foreign_key_check: {fouten}")
        return [f"tabel nieuws_doelen herbouwd ({voor} rijen): soort 'relatie' + relation_id"]
    finally:
        conn.close()


def main():
    if not DB.exists():
        sys.exit(f"DB niet gevonden: {DB}")
    conn = sqlite3.connect(DB)
    te_doen = nodig(conn)
    conn.close()
    if not te_doen:
        print("Niets te doen — migratie was al toegepast (of de wachtrij bestaat nog niet: "
              "draai dan scripts/migrate_add_nieuws_doelen.py).")
        return
    print(f"Backup: {backup(DB).name}")
    try:
        gedaan = migreer(DB)
    except Exception as exc:
        sys.exit(f"Migratie mislukt, teruggedraaid: {exc}")
    print("Gedaan:", ", ".join(gedaan))
    print("Klaar.")


if __name__ == "__main__":
    main()
