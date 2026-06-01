"""Initialiseer de SQLite database met het schema."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())
    conn.close()
    print(f"Database aangemaakt: {DB_PATH}")


if __name__ == "__main__":
    init_db()
