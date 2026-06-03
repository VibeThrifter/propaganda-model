"""Vul de instantiations-tabel uit de impliciete klasse<->instantie-koppelingen.

De koppeling klasse->instantie zit impliciet in:
  - entities.primary_role_id  -> rol  <- entiteit (hoofdrol)
  - entity_roles              -> rol  <- entiteit (extra rollen)
  - relations.mechanism_id    -> mechanisme <- relatie

Idempotent: INSERT OR IGNORE tegen de partiele unieke indexen. Kan opnieuw worden
gedraaid nadat er entiteiten/relaties bij zijn gekomen (vult alleen de ontbrekende).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def populate(conn):
    """Vul ontbrekende instantiations; retourneert (n_hoofdrol, n_extra_rol, n_mechanisme)."""
    cur = conn.cursor()
    n1 = cur.execute("""
        INSERT OR IGNORE INTO instantiations (role_id, entity_id, exemplarity)
        SELECT primary_role_id, id, 1.0 FROM entities WHERE primary_role_id IS NOT NULL
    """).rowcount
    n2 = cur.execute("""
        INSERT OR IGNORE INTO instantiations (role_id, entity_id, exemplarity)
        SELECT role_id, entity_id, 1.0 FROM entity_roles
    """).rowcount
    n3 = cur.execute("""
        INSERT OR IGNORE INTO instantiations (mechanism_id, relation_id, exemplarity)
        SELECT mechanism_id, id, 1.0 FROM relations WHERE mechanism_id IS NOT NULL
    """).rowcount
    return n1, n2, n3


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    n1, n2, n3 = populate(conn)
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM instantiations").fetchone()[0]
    conn.close()
    print(f"Instantiations geseed: hoofdrol={n1}, extra rollen={n2}, mechanisme={n3} "
          f"(totaal nu {total}).")


if __name__ == "__main__":
    main()
