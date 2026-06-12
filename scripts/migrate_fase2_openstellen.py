#!/usr/bin/env python3
"""
Migratie: structuur voor fase 2 — openstellen (verbeterplan M2.1–M2.6, juni 2026).

Eén structuurmigratie (inhoud blijft onaangeraakt — dogfood-regel):

M2.1  Attributie wordt een FK: `arguments.contributed_by` en `edit_log.changed_by`
      verwijzen voortaan naar users(username). Historische vrije-tekstwaarden
      (modelreview-sessietags, migratie-tags) krijgen elk een INACTIEF
      legacy-account (kind 'agent', provenance bewaart de oorspronkelijke tag);
      NULL-attributie in arguments mapt op het account 'legacy'.
      Plus: koppeltabel `user_filter_rollen` (reviewer/maintainer per filter).
M2.2  `arguments` herbouwd met status 'voorgesteld' in de CHECK en nieuwe kolom
      `merged_by`; `edit_log` herbouwd met action 'merged' en de changed_by-FK.
M2.3  Tabellen `voorstellen` + `voorstel_reviews` (theory-RfC's; ook M2.6).
M2.4  Tabel `watchlists` (recent-changes-feed leest edit_log rechtstreeks).
M2.5  Tabel `argument_ratings`.
M2.6  Kolom `vervangen` op roles/mechanisms/entities/relations/emergent_effects;
      tabel `lineage`; én de voorwaarde-migratie: padclaims
      (property='indirecte_invloed_op') verwijzen voortaan met het ROL-ID in
      property_value in plaats van de rolnaam (naam brak stil bij hernoemen).

Alle DDL wordt uit schema.sql gelezen (single source of truth); de validator-
schemacheck hoort daarna 0 verschillen te melden. Conventie: backup-then-migrate.
"""
import json
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
SCHEMA_PATH = ROOT / "schema.sql"

ARGUMENT_KOLOMMEN = [
    "id", "relation_id", "entity_id", "role_id", "mechanism_id", "emergent_effect_id",
    "parent_argument_id", "property", "property_value", "stance", "claim",
    "title", "reasoning", "weight", "status", "self_merged", "objection_type",
    "contributed_by", "created_at",
]
ARGUMENT_INDEXEN = [
    "CREATE INDEX idx_arguments_relation ON arguments(relation_id)",
    "CREATE INDEX idx_arguments_entity ON arguments(entity_id)",
    "CREATE INDEX idx_arguments_role ON arguments(role_id)",
    "CREATE INDEX idx_arguments_mechanism ON arguments(mechanism_id)",
    "CREATE INDEX idx_arguments_emergent ON arguments(emergent_effect_id)",
    "CREATE INDEX idx_arguments_parent ON arguments(parent_argument_id)",
    "CREATE INDEX idx_arguments_stance ON arguments(stance)",
    "CREATE INDEX idx_arguments_status ON arguments(status)",
]

EDITLOG_KOLOMMEN = [
    "id", "table_name", "record_id", "action", "changed_by",
    "old_value", "new_value", "reason", "created_at",
]
EDITLOG_INDEXEN = [
    "CREATE INDEX idx_edit_log_table ON edit_log(table_name, record_id)",
    "CREATE INDEX idx_edit_log_changed_by ON edit_log(changed_by)",
]

NIEUWE_TABELLEN = [
    ("user_filter_rollen", []),
    ("voorstellen", ["CREATE INDEX idx_voorstellen_status ON voorstellen(status)"]),
    ("voorstel_reviews",
     ["CREATE INDEX idx_voorstel_reviews_voorstel ON voorstel_reviews(voorstel_id)"]),
    ("argument_ratings",
     ["CREATE INDEX idx_ratings_argument ON argument_ratings(argument_id)"]),
    ("watchlists", []),
    ("lineage", ["CREATE INDEX idx_lineage_oud ON lineage(element_type, oud_id)",
                 "CREATE INDEX idx_lineage_nieuw ON lineage(element_type, nieuw_id)"]),
]

VERVANGEN_TABELLEN = ["roles", "mechanisms", "entities", "relations", "emergent_effects"]


def lees_ddl(tabel):
    sql = SCHEMA_PATH.read_text()
    m = re.search(rf"CREATE TABLE {tabel} \(.*?\n\);", sql, re.S)
    if not m:
        sys.exit(f"FOUT: kan CREATE TABLE {tabel} niet vinden in schema.sql")
    return m.group(0)


def herbouw(conn, tabel, kolommen, indexen):
    ddl = lees_ddl(tabel)
    conn.execute(f"ALTER TABLE {tabel} RENAME TO {tabel}_oud")
    conn.execute(ddl)
    kols = ", ".join(kolommen)
    conn.execute(f"INSERT INTO {tabel} ({kols}) SELECT {kols} FROM {tabel}_oud")
    conn.execute(f"DROP TABLE {tabel}_oud")
    for idx in indexen:
        conn.execute(idx)


def slug(tag):
    """Gebruikersnaam-slug voor een historische attributietag.

    Een parenthetische staart ("backfill-M0.4 (agent; review eigenaar)") is
    beschrijving, geen identiteit — die valt weg; de volledige tag blijft
    bewaard in de provenance van het legacy-account.
    """
    basis = tag.split(" (")[0]
    s = re.sub(r"[^a-z0-9]+", "-", basis.lower()).strip("-")
    return s or "legacy"


def maak_legacy_accounts(conn):
    """M2.1: elk historisch attributielabel wordt een inactief legacy-account."""
    bestaand = {r[0] for r in conn.execute("SELECT username FROM users")}
    tags = {r[0] for r in conn.execute(
        "SELECT DISTINCT contributed_by FROM arguments WHERE contributed_by IS NOT NULL")}
    tags |= {r[0] for r in conn.execute(
        "SELECT DISTINCT changed_by FROM edit_log WHERE changed_by IS NOT NULL")}

    mapping = {}
    for tag in sorted(tags):
        if tag in bestaand:
            mapping[tag] = tag
            continue
        naam = basis = slug(tag)
        volgnummer = 2
        while naam in bestaand:
            naam = f"{basis}-{volgnummer}"
            volgnummer += 1
        bestaand.add(naam)
        conn.execute(
            "INSERT INTO users (username, kind, role, provenance, active)"
            " VALUES (?, 'agent', 'bijdrager', ?, 0)",
            (naam, f"legacy-account (M2.1): historische attributietag {tag!r} "
                   "van vóór de gebruikersregistratie"))
        mapping[tag] = naam

    if "legacy" not in bestaand:
        conn.execute(
            "INSERT INTO users (username, kind, role, provenance, active)"
            " VALUES ('legacy', 'agent', 'bijdrager', ?, 0)",
            ("legacy-account (M2.1): ongeattribueerde corpus-import van vóór M0.6",))

    for tag, naam in mapping.items():
        if tag != naam:
            conn.execute("UPDATE arguments SET contributed_by = ? WHERE contributed_by = ?",
                         (naam, tag))
            conn.execute("UPDATE edit_log SET changed_by = ? WHERE changed_by = ?",
                         (naam, tag))
    n_null = conn.execute(
        "SELECT COUNT(*) FROM arguments WHERE contributed_by IS NULL").fetchone()[0]
    conn.execute("UPDATE arguments SET contributed_by = 'legacy' WHERE contributed_by IS NULL")
    return mapping, n_null


def migreer_padclaims_naar_id(conn):
    """M2.6-voorwaarde: padclaim-doelen op rol-ID in plaats van rolnaam."""
    rol_id = {r[1]: r[0] for r in conn.execute("SELECT id, name FROM roles")}
    rijen = conn.execute("""
        SELECT id, property_value FROM arguments
        WHERE property = 'indirecte_invloed_op'""").fetchall()
    onbekend = []
    for aid, waarde in rijen:
        waarde = (waarde or "").strip()
        if waarde.isdigit() and int(waarde) in {v for v in rol_id.values()}:
            continue  # al gemigreerd
        if waarde not in rol_id:
            onbekend.append(f"padclaim #{aid}: doelrol '{waarde}'")
            continue
        conn.execute("UPDATE arguments SET property_value = ? WHERE id = ?",
                     (str(rol_id[waarde]), aid))
    if onbekend:
        sys.exit("FOUT: padclaims met onbekende doelrol — eerst herstellen:\n  "
                 + "\n  ".join(onbekend))
    return len(rijen)


def main():
    if not DB_PATH.exists():
        sys.exit(f"FOUT: {DB_PATH} bestaat niet")

    backup = DB_PATH.with_name(
        f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    # RENAME mag de FK-verwijzingen in kindtabellen niet meeschrijven naar
    # '<tabel>_oud' (we herbouwen de tabel direct onder de oorspronkelijke naam).
    conn.execute("PRAGMA legacy_alter_table = ON")

    n_arg = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    n_log = conn.execute("SELECT COUNT(*) FROM edit_log").fetchone()[0]

    print("1. M2.1 — legacy-accounts voor historische attributietags")
    mapping, n_null = maak_legacy_accounts(conn)
    nieuw = sum(1 for t, n in mapping.items() if t != n) + (1 if n_null else 0)
    print(f"   {len(mapping)} tags gemapt ({nieuw} hernoemd), "
          f"{n_null} ongeattribueerde argumenten → 'legacy'")

    print("2. arguments herbouwen (status 'voorgesteld', merged_by, contributed_by-FK)")
    herbouw(conn, "arguments", ARGUMENT_KOLOMMEN, ARGUMENT_INDEXEN)

    print("3. edit_log herbouwen (action 'merged', changed_by-FK)")
    herbouw(conn, "edit_log", EDITLOG_KOLOMMEN, EDITLOG_INDEXEN)

    print("4. M2.6 — kolom 'vervangen' op de elementtabellen")
    for tabel in VERVANGEN_TABELLEN:
        kolommen = {r["name"] for r in conn.execute(f"PRAGMA table_info({tabel})")}
        if "vervangen" not in kolommen:
            conn.execute(f"ALTER TABLE {tabel} ADD COLUMN "
                         "vervangen BOOLEAN NOT NULL DEFAULT FALSE")

    print("5. M2.6 — padclaims: rolnaam → rol-ID in property_value")
    n_pad = migreer_padclaims_naar_id(conn)
    print(f"   {n_pad} padclaims gecontroleerd/omgezet")

    print("6. nieuwe tabellen (voorstellen, reviews, ratings, watchlists, lineage, filterrollen)")
    for tabel, indexen in NIEUWE_TABELLEN:
        if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (tabel,)).fetchone():
            continue
        conn.execute(lees_ddl(tabel))
        for idx in indexen:
            conn.execute(idx)

    # Nacontrole: geen rij verloren, FKs heel
    assert conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0] == n_arg
    assert conn.execute("SELECT COUNT(*) FROM edit_log").fetchone()[0] == n_log
    assert conn.execute(
        "SELECT COUNT(*) FROM arguments WHERE contributed_by IS NULL").fetchone()[0] == 0
    conn.execute("PRAGMA foreign_keys = ON")
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        for r in fk[:10]:
            print(f"   FK-probleem: {tuple(r)}")
        sys.exit(f"FOUT: foreign_key_check meldt {len(fk)} problemen — niet gecommit")
    conn.commit()

    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('schema', 0, 'updated', 'maxime', ?, ?)
    """, (json.dumps({"migratie": "fase2_openstellen"}),
          "Structuurmigratie fase 2 (M2.1–M2.6): FK-attributie, voorstel-workflow, "
          "ratings, watchlists, lineage, padclaims op rol-ID"))
    conn.commit()

    print(f"\nKlaar: {n_arg} argumenten en {n_log} log-regels gemigreerd; "
          f"{n_pad} padclaims op rol-ID; vervangen-kolom op {len(VERVANGEN_TABELLEN)} tabellen.")
    conn.close()


if __name__ == "__main__":
    main()
