#!/usr/bin/env python3
"""
Bridging-aggregatie van ratings (verbeterplan M2.5, Community-Notes-model).

Matrixfactorisatie (1 polariteitsdimensie, stdlib-SGD) over de MENSELIJKE ratings:

    rating(u, i) ≈ μ + b_u + b_i + p_u · q_i

De polariteitsas (p·q) absorbeert gezindheid; het intercept b_i is de nuttigheid
onafhankelijk van gezindheid — alleen dát wordt het argumentgewicht. Een
meerderheid van gelijkgestemden kan zo niets doordrukken.

Poort (§6.6): bridging vergt een populatie. Onder de drempels schrijft dit script
een rapport ZONDER gewichten — scoring.py valt dan terug op het zelfgekozen
``weight`` en de noodregels blijven gelden. Agent-ratings doen nooit mee
(één gecorreleerde familie, §6.4); hun verdiende, gecapte gewicht komt uit
scripts/kalibratie_agents.py en is advies.

Uitvoer: data/bridging.json — {"actief": bool, "weights": {argument_id: 0..1}}.
``/api/scores`` en generate_viz.py lezen dit bestand automatisch (M2.5).
Gebruik: python3 scripts/bridging.py
"""
import json
import random
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
OUT_PATH = ROOT / "data" / "bridging.json"

MIN_RATERS = 5      # minimaal aantal menselijke beoordelaars …
MIN_RATINGS = 25    # … en totaal ratings vóór bridging betekenis heeft
MIN_PER_ITEM = 2    # argumenten met minder ratings krijgen geen bridged gewicht
EPOCHS = 400
LR = 0.05
REG = 0.1
SEED = "bridging-m2.5"


def fit(ratings):
    """SGD op μ + b_u + b_i + p_u·q_i; rating ∈ {0, 1} (niet_nuttig/nuttig)."""
    users = sorted({u for u, _, _ in ratings})
    items = sorted({i for _, i, _ in ratings})
    rng = random.Random(SEED)
    b_u = {u: 0.0 for u in users}
    b_i = {i: 0.0 for i in items}
    p = {u: rng.gauss(0, 0.1) for u in users}
    q = {i: rng.gauss(0, 0.1) for i in items}
    mu = sum(r for _, _, r in ratings) / len(ratings)
    data = list(ratings)
    for _ in range(EPOCHS):
        rng.shuffle(data)
        for u, i, r in data:
            fout = (mu + b_u[u] + b_i[i] + p[u] * q[i]) - r
            b_u[u] -= LR * (fout + REG * b_u[u])
            b_i[i] -= LR * (fout + REG * b_i[i])
            p_oud = p[u]
            p[u] -= LR * (fout * q[i] + REG * p[u])
            q[i] -= LR * (fout * p_oud + REG * q[i])
    return mu, b_i


def main():
    if not DB_PATH.exists():
        sys.exit(f"FOUT: {DB_PATH} bestaat niet")
    conn = sqlite3.connect(DB_PATH)
    ratings = [(u, i, 1.0 if o == "nuttig" else 0.0) for u, i, o in conn.execute("""
        SELECT ar.rater, ar.argument_id, ar.oordeel
        FROM argument_ratings ar
        JOIN users u ON u.username = ar.rater AND u.kind = 'mens'""")]
    conn.close()

    raters = {u for u, _, _ in ratings}
    per_item = {}
    for _, i, _ in ratings:
        per_item[i] = per_item.get(i, 0) + 1

    rapport = {"actief": False, "n_raters": len(raters), "n_ratings": len(ratings),
               "drempels": {"min_raters": MIN_RATERS, "min_ratings": MIN_RATINGS,
                            "min_per_item": MIN_PER_ITEM}}
    if len(raters) < MIN_RATERS or len(ratings) < MIN_RATINGS:
        rapport["reden"] = (f"pool te klein ({len(raters)} beoordelaars, "
                            f"{len(ratings)} ratings): noodregels blijven gelden (§6.6)")
        OUT_PATH.write_text(json.dumps(rapport, indent=1))
        print(f"Bridging niet actief — {rapport['reden']}")
        print(f"Geschreven: {OUT_PATH}")
        return

    mu, b_i = fit(ratings)
    weights = {}
    for item, b in b_i.items():
        if per_item.get(item, 0) < MIN_PER_ITEM:
            continue
        weights[item] = round(min(1.0, max(0.0, mu + b)), 4)
    rapport.update({"actief": True, "mu": round(mu, 4), "weights": weights})
    OUT_PATH.write_text(json.dumps(rapport, indent=1))
    print(f"Bridging actief: {len(weights)} argumentgewichten uit {len(ratings)} ratings "
          f"van {len(raters)} beoordelaars.")
    print(f"Geschreven: {OUT_PATH} (gelezen door /api/scores en generate_viz.py)")


if __name__ == "__main__":
    main()
