#!/usr/bin/env python3
"""Live-dashboard voor draaiende agent-missies (monitor/scout/red team).

Toont wat de agent-accounts tot nu toe hebben ingediend en hun laatste
schrijfacties. Leest alleen; verandert niets. Draai zo vaak je wilt:

    python3 scripts/monitor_agents.py
    watch -n 10 python3 scripts/monitor_agents.py   # ververst elke 10s

Let op: `arguments.contributed_by` en `edit_log.changed_by` bevatten de
gebruikersnaam (string), niet een id — vandaar de directe filter op naam.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
AGENTS = ("monitor-agent", "scout-agent", "redteam-agent", "verbinder-agent")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    qs = ",".join("?" * len(AGENTS))

    print("=== Argumenten per agent-account (status) ===")
    rows = conn.execute(
        f"""SELECT contributed_by AS who, status, COUNT(*) n
            FROM arguments
            WHERE contributed_by IN ({qs})
            GROUP BY contributed_by, status ORDER BY contributed_by, status""",
        AGENTS,
    ).fetchall()
    if rows:
        for r in rows:
            print(f'  {r["who"]:<15} {r["status"]:<18} {r["n"]}')
    else:
        print("  (nog niets ingediend)")

    print("\n=== Bronregistraties door agents (uit edit_log) ===")
    rows = conn.execute(
        f"""SELECT changed_by AS who, COUNT(*) n
            FROM edit_log
            WHERE table_name='sources' AND action='created'
              AND changed_by IN ({qs})
            GROUP BY changed_by ORDER BY changed_by""",
        AGENTS,
    ).fetchall()
    print("\n".join(f'  {r["who"]:<15} {r["n"]} bron(nen)' for r in rows)
          or "  (nog geen bronnen)")

    print("\n=== Voorgestelde knopen & verbanden per agent (uit edit_log) ===")
    # entities/relations dragen geen contributed_by-kolom; attributie loopt via
    # edit_log.changed_by (action='created'). Status komt uit de rij zelf.
    rows = conn.execute(
        f"""SELECT l.changed_by AS who, 'entiteit' AS soort, e.status, COUNT(*) n
              FROM edit_log l JOIN entities e ON e.id = l.record_id
             WHERE l.table_name='entities' AND l.action='created'
               AND l.changed_by IN ({qs})
             GROUP BY l.changed_by, e.status
            UNION ALL
            SELECT l.changed_by, 'relatie', r.status, COUNT(*)
              FROM edit_log l JOIN relations r ON r.id = l.record_id
             WHERE l.table_name='relations' AND l.action='created'
               AND l.changed_by IN ({qs})
             GROUP BY l.changed_by, r.status
            ORDER BY who, soort, status""",
        AGENTS + AGENTS,
    ).fetchall()
    if rows:
        for r in rows:
            print(f'  {r["who"]:<15} {r["soort"]:<9} {r["status"]:<12} {r["n"]}')
    else:
        print("  (nog geen knopen/verbanden)")

    print("\n=== Laatste 15 schrijfacties (edit_log) ===")
    rows = conn.execute(
        f"""SELECT created_at, changed_by AS who, action, table_name, record_id
            FROM edit_log
            WHERE changed_by IN ({qs})
            ORDER BY id DESC LIMIT 15""",
        AGENTS,
    ).fetchall()
    if rows:
        for r in rows:
            print(f'  {r["created_at"]}  {r["who"]:<15} '
                  f'{r["action"]:<8} {r["table_name"]}#{r["record_id"]}')
    else:
        print("  (nog geen schrijfacties)")
    conn.close()


if __name__ == "__main__":
    main()
