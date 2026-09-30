#!/usr/bin/env python3
"""Bucket 4: schoon de partij↔politicus-banden van 9 politici op.

Per persoon stonden twee edges:
  * een LEGE, omgekeerde #92 partijlijn-edge (persoon→partij, 0 argumenten) — junk;
  * een #163 partijbinding-edge (partij→persoon) die het gesourcete lidmaatschap
    draagt, maar met het VERKEERDE mechanisme: partijbinding is voor een
    "mediafunctionaris zonder mandaat" (doelrol directie), terwijl dit politici
    (ex-ministers/Kamerleden) zijn. Juiste mechanisme = partijlijn (#92).

Resultaat: één schone, gesourcete `partij → politicus`-partijlijn-edge per persoon.
  1. Verwijder de 9 lege omgekeerde #92-edges (+ hun redundante instantiatie).
  2. Verpunt de 9 #163-edges van partijbinding (163) → partijlijn (92); richting
     partij→persoon klopt al, het argument blijft hangen.

Structurele correctie -> migratie met backup. Namens de eigenaar -> edit_log 'maxime'.
"""
import sqlite3, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "propaganda_model.db"
CHANGED_BY = "maxime"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
PARTIJLIJN = 92
PARTIJBINDING = 163

# (lege omgekeerde #92-edge om te verwijderen, #163-edge om te verpunten) per persoon
PAREN = [(336, 940), (343, 951), (347, 949), (349, 942), (352, 947),
         (354, 943), (486, 950), (490, 946), (493, 941)]

def log(c, table, rid, action, old, new, reason):
    c.execute(
        "INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason, created_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (table, rid, action, CHANGED_BY, old, new, reason, NOW),
    )

def main():
    backup = DB.parent / f"propaganda_model_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")

    for del_id, rep_id in PAREN:
        d = c.execute("SELECT source_id,target_id,mechanism_id FROM relations WHERE id=? AND status='goedgekeurd'", (del_id,)).fetchone()
        r = c.execute("SELECT source_id,target_id,mechanism_id FROM relations WHERE id=? AND status='goedgekeurd'", (rep_id,)).fetchone()
        assert d and r, f"relatie ontbreekt: {del_id}/{rep_id}"
        assert d["mechanism_id"] == PARTIJLIJN, f"rel {del_id} is geen partijlijn-edge"
        assert r["mechanism_id"] == PARTIJBINDING, f"rel {rep_id} is geen partijbinding-edge"
        nargs = c.execute("SELECT COUNT(*) FROM arguments WHERE relation_id=?", (del_id,)).fetchone()[0]
        assert nargs == 0, f"rel {del_id} draagt {nargs} argument(en) — niet zomaar verwijderen"

        pnaam = c.execute("SELECT name FROM entities WHERE id=?", (d["source_id"],)).fetchone()["name"]
        parnaam = c.execute("SELECT name FROM entities WHERE id=?", (d["target_id"],)).fetchone()["name"]

        # 1) verpunt #163 -> #92 (relatie + eventuele instantiatie)
        c.execute("UPDATE relations SET mechanism_id=? WHERE id=?", (PARTIJLIJN, rep_id))
        log(c, "relations", rep_id, "updated", f"mechanism_id={PARTIJBINDING} (partijbinding)",
            f"mechanism_id={PARTIJLIJN} (partijlijn)",
            f"mechanisme gecorrigeerd: {parnaam}→{pnaam} is partij→politicus (partijlijn), niet partijbinding")
        moved = c.execute("UPDATE instantiations SET mechanism_id=? WHERE relation_id=? AND mechanism_id=?",
                          (PARTIJLIJN, rep_id, PARTIJBINDING)).rowcount
        if moved:
            log(c, "instantiations", rep_id, "updated", f"mechanism_id={PARTIJBINDING}", f"mechanism_id={PARTIJLIJN}",
                "instantiatie-mechanisme meegewijzigd met de relatie")

        # 2) verwijder de lege omgekeerde #92-edge (+ redundante instantiatie)
        for ins in c.execute("SELECT id FROM instantiations WHERE relation_id=?", (del_id,)).fetchall():
            c.execute("DELETE FROM instantiations WHERE id=?", (ins["id"],))
            log(c, "instantiations", ins["id"], "deleted", f"relation_id={del_id}", None,
                f"redundante instantiatie van lege omgekeerde partijlijn-edge {del_id}")
        c.execute("DELETE FROM relations WHERE id=?", (del_id,))
        log(c, "relations", del_id, "deleted", f"{pnaam}->{parnaam} (partijlijn, omgekeerd, leeg)", None,
            f"lege omgekeerde partijlijn-edge; band blijft via {rep_id} ({parnaam}->{pnaam})")
        print(f"  {pnaam} ↔ {parnaam}: rel {del_id} verwijderd, rel {rep_id} → partijlijn")

    c.commit()
    c.close()
    print("Klaar.")

if __name__ == "__main__":
    main()
