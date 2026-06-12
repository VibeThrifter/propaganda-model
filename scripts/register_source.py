"""Registreer een academische bron in de database, optioneel met locaties."""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

SOURCE_TYPES = [
    "boek", "academisch_artikel", "rapport", "nieuwsartikel",
    "transcript", "interview", "dataset", "wetgeving",
    "persbericht", "website", "overig"
]

LOCATION_TYPES = ["url", "file", "doi", "isbn", "arxiv", "handle", "archive_url"]


def register_source(title: str, source_type: str, author: str = None,
                    publisher: str = None, date: str = None,
                    locations: list = None, cluster: str = None):
    if source_type not in SOURCE_TYPES:
        print(f"Ongeldig type '{source_type}'. Kies uit: {', '.join(SOURCE_TYPES)}")
        return

    # Broncluster (M1.2): zelfde auteur/uitgever/onderliggende data = zelfde cluster.
    # Zonder expliciete --cluster wordt de afleidregel van de migratie gebruikt.
    if cluster is None:
        sys.path.insert(0, str(Path(__file__).parent))
        from migrate_scoring_v2 import cluster_key_voor
        cluster = cluster_key_voor(author, publisher)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cur.execute(
        """INSERT OR IGNORE INTO sources (title, author, source_type, publisher, date_published, cluster_key)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, author, source_type, publisher, date, cluster)
    )
    conn.commit()

    cur.execute("SELECT id FROM sources WHERE title = ?", (title,))
    source_id = cur.fetchone()[0]

    if locations:
        for loc_type, loc_value in locations:
            if loc_type not in LOCATION_TYPES:
                print(f"  WARN: ongeldig locatietype '{loc_type}', skip")
                continue
            cur.execute(
                "INSERT OR IGNORE INTO source_locations (source_id, location_type, location) VALUES (?, ?, ?)",
                (source_id, loc_type, loc_value)
            )
        conn.commit()

    conn.close()
    loc_count = len(locations) if locations else 0
    print(f"Bron geregistreerd: \"{title}\" (id={source_id}, {loc_count} locaties)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Gebruik: python register_source.py <titel> <type> [auteur] [uitgever] [datum] [cluster]")
        print(f"Types: {', '.join(SOURCE_TYPES)}")
        print(f"\nVoorbeeld:")
        print(f'  python register_source.py "Manufacturing Consent" boek "Herman & Chomsky" "Pantheon" "1988-01-01"')
        print("Cluster (M1.2) wordt zonder argument afgeleid uit auteur/uitgever; geef hem")
        print("expliciet mee als de bron dezelfde onderliggende data deelt met een andere bron.")
        sys.exit(1)

    sys.path.insert(0, str(Path(__file__).parent))
    register_source(
        title=sys.argv[1],
        source_type=sys.argv[2],
        author=sys.argv[3] if len(sys.argv) > 3 else None,
        publisher=sys.argv[4] if len(sys.argv) > 4 else None,
        date=sys.argv[5] if len(sys.argv) > 5 else None,
        cluster=sys.argv[6] if len(sys.argv) > 6 else None,
    )
