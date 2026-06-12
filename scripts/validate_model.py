#!/usr/bin/env python3
"""Validator-CLI (verbeterplan M0.1): gezondheid- en consistentiechecks op de live DB.

Gebruik:
    python3 scripts/validate_model.py            # leesbaar rapport
    python3 scripts/validate_model.py --json     # machine-leesbaar (agents/dashboard)
    python3 scripts/validate_model.py --strict   # exit-code 1 zodra er fouten zijn
    python3 scripts/validate_model.py --network  # ook linkrot-check (HEAD-requests)

De checks zelf leven in validation.py (repo-root) en worden gedeeld met /api/health,
zodat dashboard en CLI per constructie dezelfde cijfers tonen.
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import validation  # noqa: E402  (repo-root module, gedeeld met server.py)

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

GLYPH = {"fout": "✗", "waarschuwing": "⚠", "info": "·"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DB_PATH), help="pad naar de SQLite-database")
    parser.add_argument("--json", action="store_true", help="JSON-uitvoer")
    parser.add_argument("--strict", action="store_true",
                        help="exit-code 1 als er bevindingen met ernst 'fout' zijn")
    parser.add_argument("--network", action="store_true",
                        help="ook linkrot controleren (HEAD-requests, traag)")
    args = parser.parse_args()

    db = Path(args.db)
    if not db.exists():
        print(f"Database niet gevonden: {db}", file=sys.stderr)
        sys.exit(2)

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rapport = validation.run_all(conn, network=args.network)
    conn.close()

    if args.json:
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
    else:
        k = rapport["kerngetallen"]
        print(f"Modelvalidatie — {rapport['gegenereerd']}  (db: {db.name})")
        print(f"  {k['entiteiten']} entiteiten · {k['relaties']} relaties · "
              f"{k['argumenten']} argumenten · {k['bronnen']} bronnen · {k['citaties']} citaties")
        stance = k["stance"]
        print(f"  stance: {stance.get('supporting', 0)} steun / "
              f"{stance.get('contradicting', 0)} tegen / {stance.get('contextual', 0)} context"
              f" · replies: {k['replies']}")
        print()
        for b in rapport["bevindingen"]:
            kop = f"{GLYPH[b['ernst']]} {b['code']:<16} {b['titel']}: {b['aantal']}"
            print(kop)
            for v in b["voorbeelden"]:
                print(f"      {v}")
            if b["aantal"] > len(b["voorbeelden"]):
                print(f"      … en {b['aantal'] - len(b['voorbeelden'])} meer")
            if b["toelichting"] and b["aantal"]:
                print(f"      ({b['toelichting']})")
        t = rapport["totalen"]
        print()
        print(f"Totaal: {t['fout']} fouten · {t['waarschuwing']} waarschuwingen · {t['info']} info")

    if args.strict and rapport["totalen"]["fout"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
