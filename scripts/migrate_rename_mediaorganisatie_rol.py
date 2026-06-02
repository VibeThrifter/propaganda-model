"""
Migratie: rol `mediaorganisatie_rol` hernoemen naar `mediaorganisatie`.

Achtergrond: `mediaorganisatie_rol` was de enige rol met een `_rol`-achtervoegsel.
Dat suffix diende ooit om de ROL te onderscheiden van het gelijknamige entity-TYPE
`mediaorganisatie`, maar alle andere rollen die met een type samenvallen (journalist,
persbureau, voorlichter, ...) hebben dat suffix niet — dus het was inconsistent.

Veiligheid: alle verwijzingen (entities.primary_role_id, mechanisms.source/target_role_id,
entity_roles.role_id) lopen via de role-ID, niet via de naam. Een naamswijziging laat die
dus intact. De enige risico's zijn (a) een UNIQUE-botsing met een bestaande rol
'mediaorganisatie' (gecheckt) en (b) string-verwijzingen in de seed-/migratiescripts
(buiten dit script meegswapt; dit script behoudt de oude naam bewust als historische bron).

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
OLD = "mediaorganisatie" + "_rol"  # bewust samengesteld zodat een string-swap dit script niet raakt
NEW = "mediaorganisatie"


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, dest)
    print(f"Backup gemaakt: {dest.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    old_row = conn.execute("SELECT id FROM roles WHERE name=?", (OLD,)).fetchone()
    if not old_row:
        if conn.execute("SELECT 1 FROM roles WHERE name=?", (NEW,)).fetchone():
            print(f"Al hernoemd: rol '{NEW}' bestaat, '{OLD}' niet meer — overgeslagen.")
        else:
            print(f"Let op: noch '{OLD}' noch '{NEW}' gevonden — niets gedaan.")
        conn.close()
        return

    role_id = old_row[0]
    if conn.execute("SELECT 1 FROM roles WHERE name=?", (NEW,)).fetchone():
        raise SystemExit(f"FOUT: er bestaat al een rol '{NEW}' — naamsbotsing, gestopt.")

    # tel verwijzingen vooraf (moeten daarna identiek zijn — ze lopen via id)
    before = {
        "entities": conn.execute("SELECT COUNT(*) FROM entities WHERE primary_role_id=?", (role_id,)).fetchone()[0],
        "mechanisms": conn.execute(
            "SELECT COUNT(*) FROM mechanisms WHERE source_role_id=? OR target_role_id=?", (role_id, role_id)
        ).fetchone()[0],
        "entity_roles": conn.execute("SELECT COUNT(*) FROM entity_roles WHERE role_id=?", (role_id,)).fetchone()[0],
    }

    backup_db()
    conn.execute("UPDATE roles SET name=? WHERE id=?", (NEW, role_id))
    conn.commit()

    after = {
        "entities": conn.execute("SELECT COUNT(*) FROM entities WHERE primary_role_id=?", (role_id,)).fetchone()[0],
        "mechanisms": conn.execute(
            "SELECT COUNT(*) FROM mechanisms WHERE source_role_id=? OR target_role_id=?", (role_id, role_id)
        ).fetchone()[0],
        "entity_roles": conn.execute("SELECT COUNT(*) FROM entity_roles WHERE role_id=?", (role_id,)).fetchone()[0],
    }

    bad = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()

    if before != after:
        raise SystemExit(f"FOUT: verwijzingen veranderden! voor={before} na={after}")
    if bad:
        raise SystemExit(f"FOUT: foreign_key_check faalt: {bad}")

    print(f"Hernoemd: '{OLD}' -> '{NEW}' (rol-id {role_id}).")
    print(f"Verwijzingen intact (via id): {after}")


if __name__ == "__main__":
    main()
