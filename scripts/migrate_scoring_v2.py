#!/usr/bin/env python3
"""
Migratie: structuur voor scoring v2 (verbeterplan fase 1, juni 2026).

Eén structuurmigratie voor vier maatregelen (inhoud blijft onaangeraakt — dogfood-regel):

M1.1  `arguments` herbouwd met de nieuwe doelregel-CHECK: een root-argument draagt
      minstens één doel, een reply (parent_argument_id gevuld) draagt GÉÉN eigen doel.
      Migratie is gratis: er zijn 0 replies in de live DB.
M1.5  property-CHECK krijgt 'compositie' (compositieclaim voor emergente velden).
M1.8  nieuwe kolom `objection_type` (machineleesbare ondergraving-classificatie).
M1.2  `sources` herbouwd met kolom `cluster_key` + reliability-klasse 'eigen_synthese';
      initiële clustertoekenning op auteur/uitgever/onderliggende data (reviewlijst
      in BRONCLUSTER_REVIEW.md — de toekenning is een voorstel, geen vaststelling).

Beide DDL's worden uit schema.sql gelezen (single source of truth); de validator-
schemacheck hoort daarna 0 verschillen te melden — de bekende DDL-tekstafwijking
van `sources` (kolomvolgorde door oude ALTER TABLE) verdwijnt hiermee ook.
Conventie: backup-then-migrate.
"""
import re
import shutil
import sqlite3
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
SCHEMA_PATH = ROOT / "schema.sql"
REVIEW_PATH = ROOT / "BRONCLUSTER_REVIEW.md"

ARGUMENT_KOLOMMEN = [
    "id", "relation_id", "entity_id", "role_id", "mechanism_id", "emergent_effect_id",
    "parent_argument_id", "property", "property_value", "stance", "claim",
    "title", "reasoning", "weight", "status", "self_merged", "contributed_by", "created_at",
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

SOURCE_KOLOMMEN = [
    "id", "title", "author", "source_type", "publisher", "date_published",
    "language", "summary", "processed", "reliability", "created_at",
]
SOURCE_INDEXEN = [
    "CREATE INDEX idx_sources_type ON sources(source_type)",
    "CREATE INDEX idx_sources_reliability ON sources(reliability)",
]

# ── Clustertoekenning (M1.2): zelfde auteur / uitgever / onderliggende data ──
# Sleutel: genormaliseerde auteursnaam (of uitgever als auteur leeg is).
# OVERRIDES vangt varianten en bekende verwantschappen; alles wat hierbuiten valt
# clustert op de eigen genormaliseerde naam (en is dus zijn eigen cluster).
OVERRIDES = {
    # zelfde organisatie, andere schrijfwijze
    "acm": "acm",
    "autoriteit consument & markt": "acm",
    "eib": "eib",
    "europese investeringsbank": "eib",
    "follow the money": "follow_the_money",
    # de Rijksoverheid-familie: zelfde afzender (regering), zelfde belang
    "rijksoverheid": "rijksoverheid",
    "ministerie van algemene zaken / ministerie van financien": "rijksoverheid",
    "ministerie van financien": "rijksoverheid",
    "rutte, m. & de jonge, h.": "rijksoverheid",
    # wetgever apart van de regering
    "staten-generaal": "staten_generaal",
    # zelfde auteurschap/advocacy-lijn: Herman & Chomsky en Chomsky solo
    "herman, e.s. & chomsky, n.": "chomsky",
    "chomsky, n.": "chomsky",
    # NOS-berichten clusteren op het onderliggende onderzoek waar dat benoemd is
    "nos, naar onderzoek van nrc": "nrc",
    "nos, naar onderzoek van de volkskrant": "volkskrant",
    "anp / nos nieuws": "nos",
    "nos": "nos",
    # Boumans is (mede)auteur van beide sourcing-studies: zelfde onderliggende lijn
    "boumans, j.": "boumans",
    "boumans, j., trilling, d., vliegenthart, r. & boomgaarden, h.": "boumans",
    # RVS-rapport en -profielpagina
    "raad voor volksgezondheid & samenleving": "rvs",
}


def _normaliseer(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def _slug(s):
    s = _normaliseer(s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or None


def cluster_key_voor(author, publisher):
    """Afleidregel voor de initiële clustertoekenning (en register_source.py)."""
    basis = _normaliseer(author) or _normaliseer(publisher)
    if not basis:
        return None
    if basis in OVERRIDES:
        return OVERRIDES[basis]
    # personen: cluster op de eerste auteursachternaam ("Vasterman, P." -> vasterman)
    if "," in basis and not basis.startswith(("ministerie", "raad ", "commissie")):
        eerste = basis.split("&")[0].split(",")[0]
        return _slug(eerste)
    return _slug(basis)


def lees_ddl(tabel):
    sql = SCHEMA_PATH.read_text()
    m = re.search(rf"CREATE TABLE {tabel} \(.*?\n\);", sql, re.S)
    if not m:
        sys.exit(f"FOUT: kan CREATE TABLE {tabel} niet vinden in schema.sql")
    return m.group(0)


def herbouw(conn, tabel, kolommen, indexen, extra_kolommen=""):
    ddl = lees_ddl(tabel)
    conn.execute(f"ALTER TABLE {tabel} RENAME TO {tabel}_oud")
    conn.execute(ddl)
    kols = ", ".join(kolommen)
    conn.execute(f"INSERT INTO {tabel} ({kols}) SELECT {kols} FROM {tabel}_oud")
    conn.execute(f"DROP TABLE {tabel}_oud")
    for idx in indexen:
        conn.execute(idx)


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

    # Voorcontrole M1.1: replies met een eigen doel zouden de nieuwe CHECK breken.
    kapot = conn.execute("""
        SELECT COUNT(*) FROM arguments
        WHERE parent_argument_id IS NOT NULL
          AND (relation_id IS NOT NULL OR entity_id IS NOT NULL OR role_id IS NOT NULL
               OR mechanism_id IS NOT NULL OR emergent_effect_id IS NOT NULL)
    """).fetchone()[0]
    if kapot:
        sys.exit(f"FOUT: {kapot} reply(s) dragen een eigen doel; eerst opschonen "
                 "(de nieuwe doelregel-CHECK zou ze weigeren)")

    n_arg = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    n_src = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]

    print("1. arguments herbouwen (doelregel-CHECK, property 'compositie', objection_type)")
    herbouw(conn, "arguments", ARGUMENT_KOLOMMEN, ARGUMENT_INDEXEN)

    print("2. sources herbouwen (cluster_key, reliability 'eigen_synthese')")
    herbouw(conn, "sources", SOURCE_KOLOMMEN, SOURCE_INDEXEN)

    print("3. initiële clustertoekenning")
    rijen = conn.execute(
        "SELECT id, title, author, publisher FROM sources ORDER BY id").fetchall()
    clusters = {}
    for r in rijen:
        key = cluster_key_voor(r["author"], r["publisher"])
        conn.execute("UPDATE sources SET cluster_key = ? WHERE id = ?", (key, r["id"]))
        clusters.setdefault(key, []).append(r)

    # Nacontrole: geen rij verloren, FKs heel, CHECKs geldig
    assert conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0] == n_arg
    assert conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == n_src
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk:
        sys.exit(f"FOUT: foreign_key_check meldt {len(fk)} problemen — niet gecommit")
    conn.commit()

    print("4. reviewlijst schrijven")
    meervoudig = {k: v for k, v in sorted(clusters.items()) if len(v) > 1}
    regels = [
        "# Bronclusters — reviewlijst (M1.2)",
        "",
        f"Gegenereerd door `scripts/migrate_scoring_v2.py` op {datetime.now():%Y-%m-%d}.",
        "De initiële toekenning is een **voorstel** op auteur/uitgever; de eigenaar",
        "reviewt en past `sources.cluster_key` aan waar de regel de plank misslaat.",
        "Regel in `scoring.py`: binnen een cluster telt alleen het sterkste argument,",
        "combineren gebeurt over clusters; argumenten zonder citatie delen per doel",
        "één pseudocluster (geen onafhankelijke bewijslijnen).",
        "",
        f"## Clusters met meerdere bronnen ({len(meervoudig)})",
        "",
    ]
    for key, bronnen in meervoudig.items():
        regels.append(f"### `{key}` ({len(bronnen)} bronnen)")
        for r in bronnen:
            regels.append(f"- bron #{r['id']}: {r['author'] or r['publisher']} — {r['title'][:90]}")
        regels.append("")
    solo = sum(1 for v in clusters.values() if len(v) == 1)
    regels += [f"## Solo-clusters: {solo} bronnen zijn hun eigen cluster", "",
               "Controlepunt: staan hier bronnen die eigenlijk dezelfde auteur/uitgever/",
               "dataset delen met een andere? Zet dan hun `cluster_key` gelijk.", ""]
    REVIEW_PATH.write_text("\n".join(regels))

    print(f"\nKlaar: {n_arg} argumenten en {n_src} bronnen gemigreerd; "
          f"{len(meervoudig)} meervoudige clusters (zie BRONCLUSTER_REVIEW.md)")
    conn.close()


if __name__ == "__main__":
    main()
