#!/usr/bin/env python3
"""Corrigeer relaties waarvan bron/doel omgekeerd staan t.o.v. de
source_role -> target_role-richting van hun eigen mechanisme.

Achtergrond: een gerichte mechanisme-edge is source_role -> target_role; een
instantie-relatie hoort dezelfde kant op te wijzen. 75 goedgekeurde relaties
stonden omgekeerd, wat influence.py een verkeerde-richting-pijl liet rekenen
(o.a. "Even tot hier -> BNNVARA" i.p.v. "BNNVARA -> Even tot hier").

Drie buckets (Bucket 4 = de 9 partijlijn-met-partijbinding-tweeling blijft
bewust staan, dat is een aparte modelleerbeslissing):

  1. VERWIJDER (3): omgekeerde duplicaten met een tweeling in dezelfde richting
     EN hetzelfde mechanisme (Bilderberg 60/61/62 <-> 331/332/333). Hun
     argumenten verhuizen naar de tweeling; hun redundante instantiaties gaan mee.
  2+3. FLIP (63): bron/doel wisselen zodat de edge de mechanisme-richting volgt.

Structurele correctie (richting/topologie), geen inhoud -> migratie met backup.
Handeling namens de eigenaar (maintainer) -> edit_log changed_by = 'maxime'.
"""
import sqlite3, shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "propaganda_model.db"
CHANGED_BY = "maxime"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def roles(c, eid):
    s = set()
    r = c.execute("SELECT primary_role_id FROM entities WHERE id=?", (eid,)).fetchone()
    if r and r[0]:
        s.add(r[0])
    for row in c.execute("SELECT role_id FROM entity_roles WHERE entity_id=?", (eid,)):
        s.add(row[0])
    return s

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

    rows = c.execute(
        """SELECT r.id, r.source_id sid, r.target_id tid, r.mechanism_id mid,
                  se.name b, te.name d, m.name mech, m.source_role_id sr, m.target_role_id tr
           FROM relations r JOIN entities se ON r.source_id=se.id JOIN entities te ON r.target_id=te.id
           JOIN mechanisms m ON r.mechanism_id=m.id
           WHERE m.source_role_id IS NOT NULL AND m.target_role_id IS NOT NULL
             AND m.source_role_id <> m.target_role_id AND r.status='goedgekeurd'"""
    ).fetchall()

    reversed_ = [
        r for r in rows
        if (r["tr"] in roles(c, r["sid"])) and (r["sr"] in roles(c, r["tid"]))
        and not ((r["sr"] in roles(c, r["sid"])) and (r["tr"] in roles(c, r["tid"])))
    ]

    def twin_same_mech(r):
        return c.execute(
            "SELECT id FROM relations WHERE source_id=? AND target_id=? AND mechanism_id=? AND status='goedgekeurd'",
            (r["tid"], r["sid"], r["mid"]),
        ).fetchone()

    def has_any_twin(r):
        return c.execute(
            "SELECT id FROM relations WHERE source_id=? AND target_id=? AND status='goedgekeurd'",
            (r["tid"], r["sid"]),
        ).fetchone()

    delete_set, skip_set, flip_set = [], [], []
    for r in reversed_:
        if twin_same_mech(r):
            delete_set.append(r)
        elif has_any_twin(r):
            skip_set.append(r)
        else:
            flip_set.append(r)

    print(f"Omgekeerd: {len(reversed_)}  |  verwijder={len(delete_set)}  flip={len(flip_set)}  bucket4-skip={len(skip_set)}")
    assert len(delete_set) == 3, f"verwacht 3 duplicaten, kreeg {len(delete_set)}"
    assert len(skip_set) == 9, f"verwacht 9 bucket-4, kreeg {len(skip_set)}"
    assert len(flip_set) == 63, f"verwacht 63 flips, kreeg {len(flip_set)}"

    # --- Bucket 1: verwijder duplicaten (argumenten -> tweeling, instantiaties weg) ---
    for r in delete_set:
        twin = twin_same_mech(r)["id"]
        for a in c.execute("SELECT id FROM arguments WHERE relation_id=?", (r["id"],)).fetchall():
            c.execute("UPDATE arguments SET relation_id=? WHERE id=?", (twin, a["id"]))
            log(c, "arguments", a["id"], "updated", f"relation_id={r['id']}", f"relation_id={twin}",
                f"argument verhuisd van duplicaat-relatie {r['id']} naar tweeling {twin}")
        for ins in c.execute("SELECT id FROM instantiations WHERE relation_id=?", (r["id"],)).fetchall():
            c.execute("DELETE FROM instantiations WHERE id=?", (ins["id"],))
            log(c, "instantiations", ins["id"], "deleted", f"relation_id={r['id']}", None,
                f"redundante instantiatie van duplicaat-relatie {r['id']} (tweeling {twin} dekt hem)")
        c.execute("DELETE FROM relations WHERE id=?", (r["id"],))
        log(c, "relations", r["id"], "deleted", f"{r['b']}->{r['d']} (mech {r['mid']})", None,
            f"omgekeerd duplicaat van tweeling {twin}; richtingcorrectie")
        print(f"  verwijderd rel {r['id']} {r['b']}->{r['d']}  (arg/instantiatie naar tweeling {twin})")

    # --- Bucket 2+3: flip bron/doel ---
    for r in flip_set:
        c.execute("UPDATE relations SET source_id=?, target_id=? WHERE id=?", (r["tid"], r["sid"], r["id"]))
        log(c, "relations", r["id"], "updated", f"{r['b']}->{r['d']}", f"{r['d']}->{r['b']}",
            f"richtingcorrectie: bron/doel gewisseld om mechanisme {r['mech']} (#{r['mid']}) te volgen")

    c.commit()
    print(f"  geflipt: {len(flip_set)} relaties")

    # skip-set tonen (Bucket 4)
    print("\nBucket 4 (bewust ongemoeid, beslissing nodig):")
    for r in skip_set:
        print(f"  rel {r['id']} {r['b']}->{r['d']} (#{r['mid']} {r['mech']})")
    c.close()
    print("\nKlaar.")

if __name__ == "__main__":
    main()
