#!/usr/bin/env python3
"""Validator-CLI (verbeterplan M0.1): gezondheid- en consistentiechecks op de live DB.

Gebruik:
    python3 scripts/validate_model.py            # leesbaar rapport
    python3 scripts/validate_model.py --json     # machine-leesbaar (agents/dashboard)
    python3 scripts/validate_model.py --strict   # exit-code 1 bij fouten bóven de baseline
    python3 scripts/validate_model.py --network  # ook linkrot-check (HEAD-requests)
    python3 scripts/validate_model.py --update-baseline  # ratchet aanscherpen

De checks zelf leven in validation.py (repo-root) en worden gedeeld met /api/health,
zodat dashboard en CLI per constructie dezelfde cijfers tonen.

Ratchet (validatie_baseline.json, ingecheckt): de bekende achterstand per foutcode.
--strict faalt alleen als een telling daar bovenuit stijgt — zo vangt de CI-poort
nieuwe regressies terwijl de achterstand wordt weggewerkt. Daalt een telling, dan
mag de baseline alleen omlaag (aanscherpen via --update-baseline), nooit omhoog
zonder bewuste beslissing.
"""
import argparse
import datetime
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import validation  # noqa: E402  (repo-root module, gedeeld met server.py)

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
BASELINE_PATH = Path(__file__).parent.parent / "validatie_baseline.json"

GLYPH = {"fout": "✗", "waarschuwing": "⚠", "info": "·"}


def laad_baseline(pad=BASELINE_PATH):
    if not pad.exists():
        return {}
    with open(pad, encoding="utf-8") as f:
        return json.load(f).get("fouten", {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(DB_PATH), help="pad naar de SQLite-database")
    parser.add_argument("--json", action="store_true", help="JSON-uitvoer")
    parser.add_argument("--strict", action="store_true",
                        help="exit-code 1 bij 'fout'-bevindingen boven de baseline")
    parser.add_argument("--network", action="store_true",
                        help="ook linkrot controleren (HEAD-requests, traag)")
    parser.add_argument("--update-baseline", action="store_true",
                        help="schrijf de huidige fout-tellingen als nieuwe baseline "
                             "(alleen bewust gebruiken, bv. na het wegwerken van achterstand)")
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

    if args.update_baseline:
        fouten = {b["code"]: b["aantal"] for b in rapport["bevindingen"]
                  if b["ernst"] == "fout" and b["aantal"]}
        oud = laad_baseline()
        omhoog = {c: (oud[c], n) for c, n in fouten.items() if n > oud.get(c, 0) and c in oud}
        if omhoog:
            print("Weigering: baseline mag niet omhoog (ratchet). Eerst de nieuwe fouten "
                  "herstellen of bewust het bestand handmatig aanpassen:", file=sys.stderr)
            for code, (basis, aantal) in sorted(omhoog.items()):
                print(f"  {code}: {basis} → {aantal}", file=sys.stderr)
            sys.exit(1)
        BASELINE_PATH.write_text(json.dumps({
            "_toelichting": "Ratchet voor validate_model.py --strict: bekende achterstand "
                            "per foutcode. --strict faalt alleen boven deze aantallen. "
                            "Aanscherpen met --update-baseline; verhogen is een bewuste, "
                            "handmatige beslissing.",
            "vastgesteld": datetime.date.today().isoformat(),
            "fouten": dict(sorted(fouten.items())),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Baseline geschreven: {BASELINE_PATH.name} — "
              f"{sum(fouten.values())} bekende fouten in {len(fouten)} check(s)")
        return

    if args.strict:
        # Golden-snapshot-test op scoring.py (M1.1): scores mogen alleen bewust
        # veranderen. Draait op een fixture-DB, raakt de live DB niet.
        import subprocess
        toets = subprocess.run([sys.executable, str(Path(__file__).parent / "test_scoring.py")],
                               capture_output=True, text=True)
        if toets.returncode:
            print("\nGolden-snapshot-test scoring.py FAALT:", file=sys.stderr)
            print(toets.stderr or toets.stdout, file=sys.stderr)
            sys.exit(1)
        print("\nGolden-snapshot-test scoring.py: groen")

        baseline = laad_baseline()
        boven, onder = [], []
        for b in rapport["bevindingen"]:
            if b["ernst"] != "fout":
                continue
            basis = baseline.get(b["code"], 0)
            if b["aantal"] > basis:
                boven.append((b["code"], b["aantal"], basis))
            elif b["aantal"] < basis:
                onder.append((b["code"], b["aantal"], basis))
        for code, aantal, basis in onder:
            print(f"Achterstand gedaald: {code} {aantal} < baseline {basis} — "
                  f"aanscherpen met --update-baseline")
        if boven:
            print("\nStrict: fouten bóven de baseline (validatie_baseline.json):",
                  file=sys.stderr)
            for code, aantal, basis in boven:
                print(f"  {code}: {aantal} (baseline {basis}, +{aantal - basis})",
                      file=sys.stderr)
            sys.exit(1)
        print("Strict: geen fouten boven de baseline.")


if __name__ == "__main__":
    main()
