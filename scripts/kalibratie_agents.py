#!/usr/bin/env python3
"""
Agent-kalibratie (verbeterplan M2.5): kwamen agent-oordelen overeen met latere
menselijke uitkomsten?

Een agent-rating is advies; stemgewicht wordt VERDIEND via kalibratie en blijft
gecapt. Vergeleken wordt:
  - rating 'nuttig'      ↔ argument later door een mens 'geverifieerd'
  - rating 'niet_nuttig' ↔ argument later 'verworpen' of 'betwist'
  - voorstel-review      ↔ definitieve voorstelstatus (geaccepteerd/afgewezen)
Argumenten/voorstellen zonder menselijke uitkomst tellen niet mee (onbeslist).

Gewicht = kalibratie × n/(n+K), gecapt op CAP — een agent begint op 0 en kan
nooit boven CAP uitkomen. Agent×agent-overeenstemming telt nergens (§6.4).

Uitvoer: leesbaar rapport + data/kalibratie.json.
Gebruik: python3 scripts/kalibratie_agents.py
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
OUT_PATH = ROOT / "data" / "kalibratie.json"

CAP = 0.5   # maximaal verdiend gewicht (t.o.v. 1.0 voor een mens)
K = 10.0    # demping: pas na ~K beslisbare oordelen nadert het gewicht de kalibratie


def main():
    if not DB_PATH.exists():
        sys.exit(f"FOUT: {DB_PATH} bestaat niet")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    agents = {}
    # Ratings vs latere argumentstatus (status­besluiten zijn menselijk werk:
    # agents kunnen geen statussen zetten, dus de uitkomst is per constructie mens)
    for r in conn.execute("""
        SELECT ar.rater, ar.oordeel, a.status
        FROM argument_ratings ar
        JOIN users u ON u.username = ar.rater AND u.kind = 'agent'
        JOIN arguments a ON a.id = ar.argument_id"""):
        st = agents.setdefault(r["rater"], {"beslist": 0, "correct": 0, "onbeslist": 0})
        if r["status"] == "geverifieerd":
            st["beslist"] += 1
            st["correct"] += 1 if r["oordeel"] == "nuttig" else 0
        elif r["status"] in ("verworpen", "betwist"):
            st["beslist"] += 1
            st["correct"] += 1 if r["oordeel"] == "niet_nuttig" else 0
        else:
            st["onbeslist"] += 1

    # Voorstel-reviews (advies) vs definitieve voorstelstatus
    for r in conn.execute("""
        SELECT vr.reviewer, vr.oordeel, v.status
        FROM voorstel_reviews vr
        JOIN users u ON u.username = vr.reviewer AND u.kind = 'agent'
        JOIN voorstellen v ON v.id = vr.voorstel_id"""):
        st = agents.setdefault(r["reviewer"], {"beslist": 0, "correct": 0, "onbeslist": 0})
        if r["status"] == "geaccepteerd":
            st["beslist"] += 1
            st["correct"] += 1 if r["oordeel"] == "akkoord" else 0
        elif r["status"] == "afgewezen":
            st["beslist"] += 1
            st["correct"] += 1 if r["oordeel"] == "afwijzen" else 0
        else:
            st["onbeslist"] += 1
    conn.close()

    rapport = {"cap": CAP, "k": K, "agents": {}}
    print("== Agent-kalibratie (M2.5) ==")
    if not agents:
        print("  Nog geen agent-ratings of -reviews; alle agent-gewichten zijn 0.")
    for naam, st in sorted(agents.items()):
        kalibratie = st["correct"] / st["beslist"] if st["beslist"] else 0.0
        gewicht = min(CAP, kalibratie * st["beslist"] / (st["beslist"] + K))
        rapport["agents"][naam] = {**st, "kalibratie": round(kalibratie, 3),
                                   "gewicht": round(gewicht, 3)}
        print(f"  {naam:<20} beslist={st['beslist']} correct={st['correct']} "
              f"onbeslist={st['onbeslist']} → kalibratie {kalibratie:.2f}, "
              f"gewicht {gewicht:.3f} (cap {CAP})")

    OUT_PATH.write_text(json.dumps(rapport, ensure_ascii=False, indent=1))
    print(f"\nGeschreven: {OUT_PATH}")


if __name__ == "__main__":
    main()
