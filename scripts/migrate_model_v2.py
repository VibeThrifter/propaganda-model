"""
Migratie v2: Uitbreiding theoretisch model met ontbrekende entiteitstypen,
relatietypen, rolcategorieën en mechanisme-classificaties.

Wat wordt er gewijzigd:
- entities.type: van 11 naar 28 typen (voorlichter, lobbyist, columnist, etc.)
- relations.relation_type: van 15 naar 27 typen (bestuurder, bron_van, flak, etc.)
- roles.category: 'systeemactor' toegevoegd
- mechanisms.filter: 'cross_filter' toegevoegd
- mechanisms: nieuw veld 'mechanism_type' (structureel, procedureel, psychologisch, etc.)
"""
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{ts}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup gemaakt: {backup}")
    return backup


def migrate(conn: sqlite3.Connection):
    cur = conn.cursor()

    # --- 1. Herstructureer entities met uitgebreide type CHECK ---
    print("Migratie entities.type ...")
    cur.execute("ALTER TABLE entities RENAME TO entities_old;")
    cur.execute("""
        CREATE TABLE entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN (
                -- Personen
                'politicus',
                'journalist',
                'voorlichter',
                'lobbyist',
                'columnist',
                'academicus',
                'mediaeigenaar',
                'toezichthouder_persoon',
                'advocaat',
                'klokkenluider',
                'persoon',

                -- Organisaties
                'partij',
                'mediaorganisatie',
                'persbureau',
                'bedrijf',
                'adverteerder',
                'lobbygroep',
                'denktank',
                'overheidsinstelling',
                'toezichthouder',
                'ngo',
                'vakbond',
                'omroep',
                'elite_netwerk',
                'vermogensbeheerder',
                'pr_bureau',
                'platform',
                'rechterlijke_macht',
                'onderwijsinstelling',
                'burgerinitiatief'
            )),
            primary_role_id INTEGER REFERENCES roles(id),
            description TEXT,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active_from TEXT,
            active_until TEXT,
            active BOOLEAN DEFAULT TRUE
        );
    """)
    cur.execute("""
        INSERT INTO entities (id, name, type, primary_role_id, description,
                              metadata, created_at, updated_at,
                              active_from, active_until, active)
        SELECT id, name, type, primary_role_id, description,
               metadata, created_at, updated_at,
               active_from, active_until, active
        FROM entities_old;
    """)
    count = cur.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    print(f"  {count} entities gemigreerd")
    cur.execute("DROP TABLE entities_old;")

    # --- 2. Herstructureer relations met uitgebreide relation_type CHECK ---
    print("Migratie relations.relation_type ...")
    cur.execute("ALTER TABLE relations RENAME TO relations_old;")
    cur.execute("""
        CREATE TABLE relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES entities(id),
            target_id INTEGER NOT NULL REFERENCES entities(id),
            relation_type TEXT NOT NULL CHECK(relation_type IN (
                -- Eigendom & financiën
                'eigendom',
                'financiering',
                'adverteerder',
                'donor',
                'investering',

                -- Organisatorisch
                'lidmaatschap',
                'personeel',
                'bestuurder',
                'adviseur',
                'woordvoerder_van',
                'draaideur',

                -- Informatiestromen
                'bron_van',
                'mediaplatform',
                'framing',
                'citeert',

                -- Macht & druk
                'lobbyt',
                'censuur',
                'flak',
                'intimidatie',
                'regulering',
                'zelfcensuur',

                -- Politiek & ideologisch
                'alliantie',
                'oppositie',
                'beinvloeding',
                'cooptatie',
                'etikettering',

                -- Algoritmisch
                'algoritmische_filtering'
            )),
            mechanism_id INTEGER REFERENCES mechanisms(id),
            description TEXT,
            certainty REAL CHECK(certainty BETWEEN 0.0 AND 1.0),
            influence REAL CHECK(influence BETWEEN 0.0 AND 1.0),
            bidirectional BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active_from TEXT,
            active_until TEXT,
            active BOOLEAN DEFAULT TRUE
        );
    """)
    cur.execute("""
        INSERT INTO relations (id, source_id, target_id, relation_type,
                               mechanism_id, description, certainty, influence,
                               bidirectional, created_at,
                               active_from, active_until, active)
        SELECT id, source_id, target_id, relation_type,
               mechanism_id, description, certainty, influence,
               bidirectional, created_at,
               active_from, active_until, active
        FROM relations_old;
    """)
    count = cur.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    print(f"  {count} relations gemigreerd")
    cur.execute("DROP TABLE relations_old;")

    # --- 3. Herstructureer roles met uitgebreide category CHECK ---
    print("Migratie roles.category ...")
    cur.execute("ALTER TABLE roles RENAME TO roles_old;")
    cur.execute("""
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL CHECK(category IN (
                'eigendom',
                'advertentie',
                'sourcing',
                'flak',
                'ideologie',
                'systeemactor',
                'overig'
            )),
            description TEXT NOT NULL,
            examples TEXT
        );
    """)
    cur.execute("""
        INSERT INTO roles (id, name, category, description, examples)
        SELECT id, name, category, description, examples
        FROM roles_old;
    """)
    count = cur.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    print(f"  {count} roles gemigreerd")
    cur.execute("DROP TABLE roles_old;")

    # --- 4. Herstructureer mechanisms: uitgebreide filter + nieuw veld mechanism_type ---
    print("Migratie mechanisms (+ mechanism_type) ...")
    cur.execute("ALTER TABLE mechanisms RENAME TO mechanisms_old;")
    cur.execute("""
        CREATE TABLE mechanisms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            filter TEXT NOT NULL CHECK(filter IN (
                'eigendom',
                'advertentie',
                'sourcing',
                'flak',
                'ideologie',
                'cross_filter',
                'overig'
            )),
            mechanism_type TEXT CHECK(mechanism_type IN (
                'structureel',
                'procedureel',
                'psychologisch',
                'economisch',
                'juridisch',
                'technologisch',
                'discursief'
            )),
            description TEXT NOT NULL,
            effect TEXT NOT NULL,
            source_role_id INTEGER REFERENCES roles(id),
            target_role_id INTEGER REFERENCES roles(id)
        );
    """)
    cur.execute("""
        INSERT INTO mechanisms (id, name, filter, description, effect,
                                source_role_id, target_role_id)
        SELECT id, name, filter, description, effect,
               source_role_id, target_role_id
        FROM mechanisms_old;
    """)
    count = cur.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    print(f"  {count} mechanisms gemigreerd")
    cur.execute("DROP TABLE mechanisms_old;")

    # --- 5. Classificeer bestaande mechanismen met mechanism_type ---
    print("Classificatie bestaande mechanismen ...")
    classifications = {
        'structureel': [
            'eigendomsconcentratie', 'duopolie_vorming', 'transnationale_verwevenheid',
            'marktconcentratie', 'bronafhankelijkheid', 'informatie_asymmetrie',
            'emergente_bias', 'systemische_homeostase',
        ],
        'procedureel': [
            'pakketjournalistiek', 'anp_homogenisering', 'draaideurpersoneel',
            'denktank_framing', 'selectieve_bronkeuze', 'uitsluiting_afwijkende_expert',
            'onevenwichtig_debatformat', 'spectrum_management',
        ],
        'psychologisch': [
            'conformisme_redactiecultuur', 'groepsdenken', 'zelfcensuur',
            'culturele_hegemonie', 'sociologische_homogeniteit',
            'professionele_socialisatie',
        ],
        'economisch': [
            'advertentiedruk', 'winstmaximalisatie', 'efficiëntiedruk',
            'budgetcontrole', 'supportive_selling_environment',
            'commerciële_druk',
        ],
        'juridisch': [
            'slapp_rechtszaken', 'juridische_intimidatie', 'woo_obstructie',
        ],
        'technologisch': [
            'algoritmische_filtering', 'platformafhankelijkheid',
            'aandachtseconomie', 'online_intimidatie',
        ],
        'discursief': [
            'etikettering', 'morele_chantage', 'framing_complottheorie',
            'neoliberaal_frame', 'stakeholder_capitalism_narratief',
            'ideologisch_gezond_verstand', 'spectrum_toegestane_opinie',
            'naturalisering_elitebelangen', 'politieke_aanval_media',
        ],
    }
    for mtype, names in classifications.items():
        placeholders = ','.join('?' for _ in names)
        cur.execute(
            f"UPDATE mechanisms SET mechanism_type = ? WHERE name IN ({placeholders})",
            [mtype] + names
        )
    # Fallback: alles wat nog NULL is
    updated = cur.execute(
        "SELECT COUNT(*) FROM mechanisms WHERE mechanism_type IS NOT NULL"
    ).fetchone()[0]
    remaining = cur.execute(
        "SELECT COUNT(*) FROM mechanisms WHERE mechanism_type IS NULL"
    ).fetchone()[0]
    print(f"  {updated} geclassificeerd, {remaining} nog zonder type")

    # --- 6. Indexen opnieuw aanmaken ---
    print("Indexen aanmaken ...")
    for stmt in [
        "CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);",
        "CREATE INDEX IF NOT EXISTS idx_entities_role ON entities(primary_role_id);",
        "CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);",
        "CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);",
        "CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);",
        "CREATE INDEX IF NOT EXISTS idx_relations_mechanism ON relations(mechanism_id);",
        "CREATE INDEX IF NOT EXISTS idx_mechanisms_filter ON mechanisms(filter);",
        "CREATE INDEX IF NOT EXISTS idx_mechanisms_type ON mechanisms(mechanism_type);",
    ]:
        cur.execute(stmt)

    conn.commit()
    print("Migratie voltooid!")


def verify(conn: sqlite3.Connection):
    """Verificatie na migratie."""
    cur = conn.cursor()
    print("\n=== Verificatie ===")
    for table in ['entities', 'relations', 'roles', 'mechanisms']:
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} records")

    print("\nEntity types beschikbaar:")
    # Haal de CHECK constraint op uit het schema
    schema = cur.execute(
        "SELECT sql FROM sqlite_master WHERE name='entities'"
    ).fetchone()[0]
    import re
    types = re.findall(r"'(\w+)'", schema.split("CHECK")[1].split(")")[0])
    for t in types:
        count = cur.execute(
            "SELECT COUNT(*) FROM entities WHERE type=?", (t,)
        ).fetchone()[0]
        marker = f" ({count})" if count > 0 else ""
        print(f"    {t}{marker}")

    print("\nRelation types beschikbaar:")
    schema = cur.execute(
        "SELECT sql FROM sqlite_master WHERE name='relations'"
    ).fetchone()[0]
    types = re.findall(r"'(\w+)'", schema.split("CHECK")[1].split(")")[0])
    for t in types:
        count = cur.execute(
            "SELECT COUNT(*) FROM relations WHERE relation_type=?", (t,)
        ).fetchone()[0]
        marker = f" ({count})" if count > 0 else ""
        print(f"    {t}{marker}")

    print("\nMechanism types:")
    rows = cur.execute(
        "SELECT mechanism_type, COUNT(*) FROM mechanisms GROUP BY mechanism_type ORDER BY mechanism_type"
    ).fetchall()
    for mtype, count in rows:
        print(f"    {mtype or 'NULL'}: {count}")


if __name__ == "__main__":
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF;")
    try:
        migrate(conn)
        verify(conn)
    except Exception as e:
        print(f"\nFOUT: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
