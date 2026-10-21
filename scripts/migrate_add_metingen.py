#!/usr/bin/env python3
"""Schema-migratie: eigen metingen (eigenaarsbesluit 2026-10-16: een eigen meting telt als bewijs,
"het moet een tool zijn waarmee je zelf dat kan bepalen", "zolang je aan journalistieke codes
houdt").

Waarom: een meting is een vooraf vastgelegde telling (welke organisatie of deskundige komt in
welk medium aan het woord, over welk onderwerp, met welk standpunt, wordt de financiering
vermeld). Ze wordt een bron (een dataset) waarop een gewoon argument kan steunen. Vier tabellen:

  metingen             de opzet (JSON), status opzet → vastgelegd → afgerond, de hashes en de
                       bevroren samenvatting
  meting_waarnemingen  per citaat: groep, wie, medium, url, datum, letterlijk citaat, codes, en of
                       metingcheck het citaat op de url terugvond
  meting_controles     de blinde tweede codering door een ander account (UNIQUE per account)
  meting_wederhoor     hoor en wederhoor per partij

De definities zijn exact die van schema.sql (SCHEMA-pariteit). Puur additief en idempotent:
bestaat een tabel of index al, dan blijft hij staan. Backup-then-migrate per conventie: eerst een
kopie naar data/propaganda_model_backup_<timestamp>.db (SQLite-backup-API, ook de WAL-inhoud).

Gebruik: python3 scripts/migrate_add_metingen.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from migrate_add_nieuws_doelen import backup  # noqa: E402

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

TABELLEN = {
    "metingen": """CREATE TABLE metingen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titel TEXT NOT NULL,
    vraag TEXT NOT NULL,                  -- de onderzoeksvraag
    opzet TEXT NOT NULL,                  -- JSON {selectie, groepen, vragen, uitkomst, stopregel}
    status TEXT NOT NULL DEFAULT 'opzet' CHECK(status IN ('opzet', 'vastgelegd', 'afgerond')),
    voorspelling_id INTEGER REFERENCES predictions(id),
    contributed_by TEXT NOT NULL REFERENCES users(username),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vastgelegd_at TIMESTAMP,              -- opzet bevroren (UTC, zoals created_at)
    afgerond_at TIMESTAMP,                -- dataset bevroren
    opzet_hash TEXT,                      -- sha256 van de opzet bij het vastleggen
    data_hash TEXT,                       -- sha256 van de dataset bij het afronden
    samenvatting TEXT                     -- JSON, bevroren bij het afronden (vaste tekstregels)
)""",
    "meting_waarnemingen": """CREATE TABLE meting_waarnemingen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meting_id INTEGER NOT NULL REFERENCES metingen(id),
    groep TEXT NOT NULL,                  -- naam van een groep uit de opzet
    wie TEXT NOT NULL,                    -- naam en functie zoals in het artikel
    entity_id INTEGER REFERENCES entities(id),         -- de geciteerde, als knoop in het model
    medium_entity_id INTEGER REFERENCES entities(id),  -- het medium (uit de selectie)
    url TEXT NOT NULL,
    archief_url TEXT,
    datum TEXT NOT NULL,                  -- publicatiedatum van het artikel (JJJJ-MM-DD)
    citaat TEXT NOT NULL,                 -- letterlijk uit het artikel
    codes TEXT NOT NULL DEFAULT '{}',     -- JSON {sleutel: optie}
    notitie TEXT,
    contributed_by TEXT NOT NULL REFERENCES users(username),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    citaat_gevonden INTEGER CHECK(citaat_gevonden IS NULL OR citaat_gevonden IN (0, 1)),
    citaat_gecontroleerd_at TIMESTAMP     -- wanneer metingcheck het citaat op de url zocht
)""",
    "meting_controles": """CREATE TABLE meting_controles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    waarneming_id INTEGER NOT NULL REFERENCES meting_waarnemingen(id),
    codes TEXT NOT NULL,                  -- JSON {sleutel: optie}: de blinde tweede codering
    door TEXT NOT NULL REFERENCES users(username),  -- nooit de invoerder
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(waarneming_id, door)
)""",
    "meting_wederhoor": """CREATE TABLE meting_wederhoor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meting_id INTEGER NOT NULL REFERENCES metingen(id),
    partij TEXT NOT NULL,                 -- naam van de partij (organisatie of medium)
    entity_id INTEGER REFERENCES entities(id),
    soort TEXT NOT NULL CHECK(soort IN ('reactie', 'verzoek_zonder_reactie',
                                        'gepubliceerd_standpunt')),
    tekst TEXT,                           -- de reactie, het verzoek of het standpunt
    bron_url TEXT,                        -- vindplaats (verplicht bij een gepubliceerd standpunt)
    datum TEXT,                           -- JJJJ-MM-DD (verplicht bij een verzoek zonder reactie)
    door TEXT NOT NULL REFERENCES users(username),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""",
}
INDEXEN = {
    "idx_metingen_status": "CREATE INDEX idx_metingen_status ON metingen(status)",
    "idx_meting_waarnemingen_meting":
        "CREATE INDEX idx_meting_waarnemingen_meting ON meting_waarnemingen(meting_id)",
    "idx_meting_controles_waarneming":
        "CREATE INDEX idx_meting_controles_waarneming ON meting_controles(waarneming_id)",
    "idx_meting_wederhoor_meting":
        "CREATE INDEX idx_meting_wederhoor_meting ON meting_wederhoor(meting_id)",
}


def _bestaat(conn, soort, naam) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = ? AND name = ?",
                        (soort, naam)).fetchone() is not None


def nodig(conn) -> list[str]:
    """Wat er nog ontbreekt (tabel- en indexnamen)."""
    return ([t for t in TABELLEN if not _bestaat(conn, "table", t)]
            + [i for i in INDEXEN if not _bestaat(conn, "index", i)])


def migreer(db: Path) -> list[str]:
    """Leg aan wat ontbreekt. → de namen die zijn aangelegd."""
    conn = sqlite3.connect(db)
    try:
        aangelegd = []
        for naam, ddl in TABELLEN.items():
            if not _bestaat(conn, "table", naam):
                conn.execute(ddl)
                aangelegd.append(naam)
        for naam, ddl in INDEXEN.items():
            if not _bestaat(conn, "index", naam):
                conn.execute(ddl)
                aangelegd.append(naam)
        conn.commit()
        return aangelegd
    finally:
        conn.close()


def main():
    if not DB.exists():
        sys.exit(f"Database niet gevonden: {DB}")
    conn = sqlite3.connect(DB)
    try:
        ontbreekt = nodig(conn)
    finally:
        conn.close()
    if not ontbreekt:
        print("Eigen metingen: alle tabellen en indexen bestaan al — niets te doen.")
        return
    print(f"Backup: {backup(DB)}")
    aangelegd = migreer(DB)
    print(f"Aangelegd: {', '.join(aangelegd)}")


if __name__ == "__main__":
    main()
