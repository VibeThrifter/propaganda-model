"""
Modelreview — `sociologische_homogeniteit` is geen gerichte relatie maar een eigenschap.

Stond als `direct` (redactie → publiek), maar het is geen gericht kanaal: redacties ZÍJN
sociologisch homogeen (HBO/WO, middenklasse, Randstad) → blinde vlekken. Dat is een
eigenschap VÁN de redactie, dus een `veld_eigenschap`-halo.

Een veld_eigenschap-halo tekent op de DOEL-node (die de eigenschap "ondergaat"), en kent geen
echte externe bron — precies zoals `geweld_intimidatie` (bron NULL → journalist). Dus:
  bron NULL → doel=redactie, aard=veld_eigenschap.
Zo verschijnt de halo om de redactie i.p.v. een pijl naar het publiek. 0 instances, dus geen
relaties te verplaatsen. Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
MECH = "sociologische_homogeniteit"
TARGET_ROLE = "redactie"


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    redactie = conn.execute("SELECT id FROM roles WHERE name=?", (TARGET_ROLE,)).fetchone()
    if redactie is None:
        raise SystemExit(f"FOUT: rol '{TARGET_ROLE}' niet gevonden.")
    rid = redactie[0]

    row = conn.execute("SELECT id FROM mechanisms WHERE name=?", (MECH,)).fetchone()
    if row is None:
        raise SystemExit(f"FOUT: mechanisme '{MECH}' niet gevonden.")
    mid = row[0]
    nrel = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (mid,)).fetchone()[0]
    if nrel:
        print(f"LET OP: {MECH} heeft {nrel} instance-relatie(s) — die blijven gekoppeld.")

    conn.execute(
        "UPDATE mechanisms SET aard='veld_eigenschap', source_role_id=NULL, target_role_id=? "
        "WHERE id=?", (rid, mid))
    conn.commit()

    name, aard, s, t = conn.execute("""
        SELECT name, aard, source_role_id,
               (SELECT name FROM roles WHERE id=target_role_id) FROM mechanisms WHERE id=?""",
        (mid,)).fetchone()
    print(f"\n→ {name} [{aard}]   bron={s if s is not None else 'NULL'} → doel={t}")

    print("\n== veld_eigenschap-halo's nu ==")
    rn = {i: n for i, n in conn.execute("SELECT id, name FROM roles")}
    for n, sr, tr in conn.execute(
            "SELECT name, source_role_id, target_role_id FROM mechanisms "
            "WHERE aard='veld_eigenschap' ORDER BY name"):
        print(f"  {n:28} {rn.get(sr) if sr is not None else 'NULL'} → {rn.get(tr)}")
    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
