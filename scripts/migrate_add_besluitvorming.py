#!/usr/bin/env python3
"""Migratie: besluitvorming als categorieën in hetzelfde netwerk (eigenaarsbesluit 2026-10-07).

Structuur/schema, geen inhoud (VOORSTEL_besluitvorming-als-categorieen.md, DOCUMENTATIE.md
§ "Uitbreiding C"):

1. Vijf categorie-waarden (formele_macht, belangen, kennis_advies, polder, werving) in de
   CHECK-enums van mechanisms.filter, mechanism_filters.filter, roles.category,
   emergent_effects.category en user_filter_rollen.filter.
2. Vier relatietypes (ambt, zeggenschap, controle, geschenk) in relations.relation_type.
3. Kolommen relations.functie en entities.bestuurslaag.
4. Tabel externe_ids (+ index).
5. Herstel: elk mechanisme heeft zijn primaire filter ook als rij in mechanism_filters. Een
   deel miste die rij; zonder herstel zou de eerste extra categorie die een mechanisme krijgt
   de primaire filter uit de lijst van de viz (viz_data.py) verdringen.

Werkwijze (SQLite-herbouw): het LIVE CREATE-statement wordt alleen in de CHECK-lijst
uitgebreid (zo blijven bewuste live-verschillen met schema.sql staan, zie
validation.BEKENDE_DDL_VERSCHILLEN), dan <tabel>_nieuw maken, rijen kopiëren, oude tabel
droppen, de nieuwe hernoemen, indexen terugzetten en sqlite_sequence bewaren. Nooit eerst de
oude tabel hernoemen: SQLite herschrijft dan de foreign keys van andere tabellen naar de
oude naam.

Vooraf: stop de server en de agents (de database draait in WAL-modus):
    launchctl unload ~/Library/LaunchAgents/nl.propaganda.server.plist (en de agent-plists)
De backup gaat via de backup-API (neemt de WAL mee). Idempotent: een tweede run doet niets.

Gebruik: python3 scripts/migrate_add_besluitvorming.py [--droog] [--forceer]
  --droog    toont wat er zou veranderen, schrijft niets
  --forceer  slaat de controle over of de server nog draait
"""
import argparse
import re
import sqlite3
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"

CATEGORIEEN = ("formele_macht", "belangen", "kennis_advies", "polder", "werving")
RELATIETYPES = ("ambt", "zeggenschap", "controle", "geschenk")
BESTUURSLAGEN = ("eu", "rijk", "provincie", "gemeente", "waterschap", "caribisch", "regio")
STELSELS = ("tooi", "oo", "tk_persoon", "wikidata", "ep_mep")

# (tabel, kolom, nieuwe enum-waarden)
HERBOUW = (
    ("roles", "category", CATEGORIEEN),
    ("mechanisms", "filter", CATEGORIEEN),
    ("mechanism_filters", "filter", CATEGORIEEN),
    ("emergent_effects", "category", CATEGORIEEN),
    ("user_filter_rollen", "filter", CATEGORIEEN),
    ("relations", "relation_type", RELATIETYPES),
)

EXTERNE_IDS_DDL = """CREATE TABLE externe_ids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    stelsel TEXT NOT NULL CHECK(stelsel IN (
        'tooi',          -- identifier.overheid.nl (TOOI), bv. 'oorg10212'
        'oo',            -- systeemId in het register van overheidsorganisaties
        'tk_persoon',    -- Persoon.Id in de open data van de Tweede Kamer
        'wikidata',      -- QID, bv. 'Q12345'
        'ep_mep'         -- MEP-id in de open data van het Europees Parlement
    )),
    waarde TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (stelsel, waarde)
)"""
EXTERNE_IDS_INDEX = "CREATE INDEX idx_externe_ids_entity ON externe_ids(entity_id)"


def _sluit_haakje(sql, start):
    """Index van het ')' dat het '(' op `start` sluit; slaat strings en --commentaar over."""
    diepte, i = 0, start
    while i < len(sql):
        c = sql[i]
        if c == "'":
            i = sql.index("'", i + 1)
        elif sql.startswith("--", i):
            eind = sql.find("\n", i)
            i = len(sql) if eind < 0 else eind
            continue
        elif c == "(":
            diepte += 1
        elif c == ")":
            diepte -= 1
            if diepte == 0:
                return i
        i += 1
    raise ValueError("geen sluitend haakje gevonden")


def breid_enum_uit(sql, kolom, waarden):
    """→ (nieuwe sql, toegevoegde waarden). Breidt de IN-lijst van CHECK(<kolom> IN (...)) uit."""
    m = re.search(rf"CHECK\s*\(\s*{re.escape(kolom)}\s+IN\s*\(", sql)
    if not m:
        raise ValueError(f"CHECK({kolom} IN (...)) niet gevonden")
    open_idx = m.end() - 1
    sluit_idx = _sluit_haakje(sql, open_idx)
    lijst = sql[open_idx:sluit_idx]
    bestaand = set(re.findall(r"'([^']*)'", re.sub(r"--[^\n]*", "", lijst)))
    nieuw = [w for w in waarden if w not in bestaand]
    if not nieuw:
        return sql, []
    toevoeging = ", " + ", ".join(f"'{w}'" for w in nieuw)
    # Staat er commentaar op de laatste regel vóór het sluithaakje, dan op een nieuwe regel.
    laatste_regel = lijst.rsplit("\n", 1)[-1]
    if "--" in laatste_regel:
        toevoeging = "\n        " + toevoeging
    return sql[:sluit_idx] + toevoeging + sql[sluit_idx:], nieuw


def live_sql(conn, tabel):
    rij = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                       (tabel,)).fetchone()
    if not rij:
        raise SystemExit(f"FOUT: tabel {tabel} bestaat niet")
    return rij[0]


def herbouw(conn, tabel, nieuw_sql):
    """Herbouw `tabel` met `nieuw_sql` (dezelfde kolommen); indexen en sqlite_sequence blijven."""
    kolommen = [r[1] for r in conn.execute(f'PRAGMA table_info("{tabel}")')]
    indexen = [r[0] for r in conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL",
        (tabel,))]
    seq = conn.execute("SELECT seq FROM sqlite_sequence WHERE name=?", (tabel,)).fetchone() \
        if conn.execute("SELECT 1 FROM sqlite_master WHERE name='sqlite_sequence'").fetchone() \
        else None
    n_voor = conn.execute(f'SELECT COUNT(*) FROM "{tabel}"').fetchone()[0]

    tijdelijk = f"{tabel}_nieuw"
    tmp_sql, n = re.subn(rf'CREATE TABLE (IF NOT EXISTS )?"?{re.escape(tabel)}"?',
                         f"CREATE TABLE {tijdelijk}", nieuw_sql, count=1)
    if n != 1:
        raise SystemExit(f"FOUT: CREATE TABLE {tabel} niet herkend")
    kol = ", ".join(f'"{k}"' for k in kolommen)
    conn.execute(f"DROP TABLE IF EXISTS {tijdelijk}")
    conn.execute(tmp_sql)
    conn.execute(f'INSERT INTO {tijdelijk} ({kol}) SELECT {kol} FROM "{tabel}"')
    conn.execute(f'DROP TABLE "{tabel}"')
    conn.execute(f'ALTER TABLE {tijdelijk} RENAME TO "{tabel}"')
    for idx in indexen:
        conn.execute(idx)
    if seq is not None:
        conn.execute("UPDATE sqlite_sequence SET seq = MAX(seq, ?) WHERE name = ?", (seq[0], tabel))
        if not conn.execute("SELECT 1 FROM sqlite_sequence WHERE name=?", (tabel,)).fetchone():
            conn.execute("INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)", (tabel, seq[0]))
    n_na = conn.execute(f'SELECT COUNT(*) FROM "{tabel}"').fetchone()[0]
    if n_na != n_voor:
        raise SystemExit(f"FOUT: {tabel}: {n_voor} rijen voor, {n_na} na — afgebroken")
    return n_voor


def server_draait():
    try:
        urllib.request.urlopen("http://127.0.0.1:5000/api/health", timeout=3)
        return True
    except Exception:
        return False


def kolom_bestaat(conn, tabel, kolom):
    return any(r[1] == kolom for r in conn.execute(f'PRAGMA table_info("{tabel}")'))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--droog", action="store_true")
    ap.add_argument("--forceer", action="store_true")
    args = ap.parse_args()

    if not DB_PATH.exists():
        sys.exit(f"FOUT: {DB_PATH} bestaat niet")
    if not args.droog and not args.forceer and server_draait():
        sys.exit("FOUT: de server draait nog (localhost:5000). Stop eerst de server en de agents:\n"
                 "  for p in server agent-automatische-beoordeling agent-nieuws-scout "
                 "agent-nieuws-bewijs; do launchctl unload "
                 "~/Library/LaunchAgents/nl.propaganda.$p.plist; done")

    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    plan = []
    for tabel, kolom, waarden in HERBOUW:
        nieuw_sql, nieuw = breid_enum_uit(live_sql(conn, tabel), kolom, waarden)
        if nieuw:
            plan.append((tabel, kolom, nieuw, nieuw_sql))
    kolommen_nodig = [(t, k) for t, k in (("relations", "functie"), ("entities", "bestuurslaag"))
                      if not kolom_bestaat(conn, t, k)]
    externe_nodig = not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='externe_ids'").fetchone()
    mf_toegestaan = set(re.findall(r"'([^']*)'", re.sub(
        r"--[^\n]*", "", live_sql(conn, "mechanism_filters"))))
    mf_toegestaan |= set(CATEGORIEEN)
    herstel = conn.execute(
        "SELECT m.id, m.name, m.filter FROM mechanisms m WHERE NOT EXISTS ("
        " SELECT 1 FROM mechanism_filters mf WHERE mf.mechanism_id = m.id AND mf.filter = m.filter)"
    ).fetchall()
    herstel = [r for r in herstel if r[2] in mf_toegestaan]

    print("Plan:")
    for tabel, kolom, nieuw, _ in plan:
        print(f"  herbouw {tabel}: {kolom} + {', '.join(nieuw)}")
    for t, k in kolommen_nodig:
        print(f"  kolom {t}.{k}")
    if externe_nodig:
        print("  tabel externe_ids + idx_externe_ids_entity")
    print(f"  mechanism_filters: {len(herstel)} mechanismen krijgen hun primaire filter als rij")
    if not (plan or kolommen_nodig or externe_nodig or herstel):
        print("Niets te doen — alles staat er al.")
        return
    if args.droog:
        print("(droogloop: niets geschreven)")
        return

    # Backup via de backup-API: neemt ook wat nog in de WAL staat mee.
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    doel = sqlite3.connect(backup)
    conn.backup(doel)
    doel.close()
    print(f"Backup: {backup.name}")

    fk_voor = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.execute("PRAGMA foreign_keys = OFF")  # vóór BEGIN, anders cascadeert DROP TABLE
    conn.execute("BEGIN IMMEDIATE")
    try:
        for tabel, kolom, nieuw, nieuw_sql in plan:
            n = herbouw(conn, tabel, nieuw_sql)
            print(f"  {tabel}: herbouwd ({n} rijen)")
        if ("relations", "functie") in kolommen_nodig:
            conn.execute("ALTER TABLE relations ADD COLUMN functie TEXT")
        if ("entities", "bestuurslaag") in kolommen_nodig:
            lagen = ", ".join(f"'{w}'" for w in BESTUURSLAGEN)
            conn.execute(f"ALTER TABLE entities ADD COLUMN bestuurslaag TEXT "
                         f"CHECK(bestuurslaag IN ({lagen}))")
        if externe_nodig:
            conn.execute(EXTERNE_IDS_DDL)
            conn.execute(EXTERNE_IDS_INDEX)
        for mid, _naam, filt in herstel:
            conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) "
                         "VALUES (?, ?)", (mid, filt))
        fk_na = conn.execute("PRAGMA foreign_key_check").fetchall()
        if len(fk_na) > len(fk_voor):
            raise SystemExit(f"FOUT: foreign_key_check meldt {len(fk_na)} problemen "
                             f"(was {len(fk_voor)}) — teruggedraaid")
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    # Nacontrole in een verse verbinding: integriteit en de CHECK's doen wat ze moeten.
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    print("integrity_check:", conn.execute("PRAGMA integrity_check").fetchone()[0])
    proeven = [
        ("INSERT INTO roles (name, category, description) VALUES "
         "('__proef_rol', 'formele_macht', 'proef')", True),
        ("INSERT INTO roles (name, category, description) VALUES "
         "('__proef_rol2', 'onzin', 'proef')", False),
        ("INSERT INTO relations (source_id, target_id, relation_type) "
         "SELECT source_id, target_id, 'ambt' FROM relations LIMIT 1", True),
        ("INSERT INTO relations (source_id, target_id, relation_type) "
         "SELECT source_id, target_id, 'zomaarwat' FROM relations LIMIT 1", False),
        ("UPDATE entities SET bestuurslaag = 'rijk' WHERE id = (SELECT MIN(id) FROM entities)", True),
        ("UPDATE entities SET bestuurslaag = 'maan' WHERE id = (SELECT MIN(id) FROM entities)", False),
        ("INSERT INTO externe_ids (entity_id, stelsel, waarde) "
         "VALUES ((SELECT MIN(id) FROM entities), 'tooi', '__proef')", True),
        ("INSERT INTO externe_ids (entity_id, stelsel, waarde) "
         "VALUES ((SELECT MIN(id) FROM entities), 'kvk', '__proef')", False),
    ]
    for sql, moet_lukken in proeven:
        conn.execute("BEGIN")
        try:
            conn.execute(sql)
            gelukt = True
        except sqlite3.IntegrityError:
            gelukt = False
        conn.execute("ROLLBACK")
        if gelukt != moet_lukken:
            sys.exit(f"FOUT: CHECK-proef faalt: {sql}")
    print("CHECK-proeven: OK")
    conn.close()
    print("Klaar. Start de server en de agents weer:\n"
          "  for p in server agent-automatische-beoordeling agent-nieuws-scout agent-nieuws-bewijs; "
          "do launchctl load ~/Library/LaunchAgents/nl.propaganda.$p.plist; done")


if __name__ == "__main__":
    main()
