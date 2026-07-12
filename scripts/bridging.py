#!/usr/bin/env python3
"""
Bridging-aggregatie van ratings (verbeterplan M2.5, Community-Notes-model).

Matrixfactorisatie (1 polariteitsdimensie, stdlib-SGD) over de MENSELIJKE oordelen:

    rating(u, i) ≈ μ + b_u + b_i + p_u · q_i

De polariteitsas (p·q) absorbeert gezindheid; het intercept b_i is de nuttigheid
onafhankelijk van gezindheid — alleen dát wordt het argumentgewicht. Een
meerderheid van gelijkgestemden kan zo niets doordrukken.

Twee bronnen vormen de 0/1-matrix (review-verdict v2 — de kale 👎 bestaat niet meer):
  +1  'Argument klopt' = een nuttig-endorsement (argument_ratings.oordeel = 'nuttig');
   0  een gehandhaafde ONDERGRAVING (een contradicting reply waarvan de resolutielus
      NIET op 'opgelost' staat) is het beredeneerde oordeel "dit argument klopt niet"
      — de bezwaarmaker beoordeelt daarmee het aangevochten argument (de
      parent) als niet-nuttig. Zo houdt bridging het contrast dat het nodig heeft,
      maar is de 'downvote' onderbouwd i.p.v. goedkoop.

Let op: dezelfde ondergraving dempt ook de σ van haar parent via de boom (DF-QuAD).
Bridging weegt echter gezindheids-onafhankelijk over álle oordelen van een beoordelaar,
terwijl σ de lokale boomkracht van dít bezwaar gebruikt — andere grootheden, geen
exacte dubbeltelling. De interactie is mild en sowieso slapend tot de pool de drempel
haalt (zie §6.6 / de drempels hieronder).

Poort (§6.6): bridging vergt een populatie. Onder de drempels schrijft dit script
een rapport ZONDER gewichten — scoring.py valt dan terug op het zelfgekozen
``weight`` en de noodregels blijven gelden. Agent-ratings doen nooit mee
(één gecorreleerde familie, §6.4); hun verdiende, gecapte gewicht komt uit
scripts/kalibratie_agents.py en is advies.

Uitvoer: data/bridging.json — {"actief": bool, "weights": {argument_id: 0..1}}.
``/api/scores``, ``/api/graph_data`` en de statische export lezen dit automatisch (M2.5).
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

# Identificeerbaarheidsvloer (géén scoredrempel): met te weinig beoordelaars/oordelen
# is de gezindheidsas (p·q) wiskundig niet te schatten, dus draait de fit niet en geldt
# het neutrale gewicht. Klein "kan dit überhaupt"-minimum, niet de oude 5/25-klif.
FIT_MIN_RATERS = 3
FIT_MIN_RATINGS = 6
# Krimp naar het neutrale gewicht 1,0: een argument met n oordelen krijgt vertrouwen
# α = n/(n+SHRINK_K); bij n = SHRINK_K telt bridging voor de helft mee. Glad i.p.v. een
# klif — er is geen arbitraire grens meer waar de scores bij groei doorheen schieten.
SHRINK_K = 5
EPOCHS = 400
LR = 0.05
REG = 0.1
SEED = "bridging-m2.5"


def fit(ratings):
    """SGD op μ + b_u + b_i + p_u·q_i; rating ∈ {0, 1} (ondergraving/endorsement)."""
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
    # +1 = 'Argument klopt' (nuttig-endorsement); een legacy niet_nuttig telt als 0.
    endorsements = [(u, i, 1.0 if o == "nuttig" else 0.0) for u, i, o in conn.execute("""
        SELECT ar.rater, ar.argument_id, ar.oordeel
        FROM argument_ratings ar
        JOIN users u ON u.username = ar.rater AND u.kind = 'mens'""")]
    # 0 = een gehandhaafde (niet-'opgelost') ONDERGRAVING: de bezwaarmaker (u) oordeelt
    # dat de logica van het aangevochten argument (parent i) niet deugt. Alleen tellende
    # bezwaren (gemerged, niet vervangen) en alleen mensen.
    bezwaren = [(u, i, 0.0) for u, i in conn.execute("""
        SELECT a.contributed_by, a.parent_argument_id
        FROM arguments a
        JOIN users u ON u.username = a.contributed_by AND u.kind = 'mens'
        WHERE a.parent_argument_id IS NOT NULL
          AND a.stance = 'contradicting'
          AND a.bezwaar_resolutie IS NOT NULL
          AND a.bezwaar_resolutie != 'opgelost'
          AND a.status NOT IN ('voorgesteld', 'verworpen')
          AND NOT a.vervangen""")]
    ratings = endorsements + bezwaren
    conn.close()

    raters = {u for u, _, _ in ratings}
    per_item = {}
    for _, i, _ in ratings:
        per_item[i] = per_item.get(i, 0) + 1

    rapport = {"actief": False, "n_raters": len(raters), "n_ratings": len(ratings),
               "vloer": {"min_raters": FIT_MIN_RATERS, "min_ratings": FIT_MIN_RATINGS},
               "k": SHRINK_K}
    if len(raters) < FIT_MIN_RATERS or len(ratings) < FIT_MIN_RATINGS:
        rapport["reden"] = (f"pool nog te klein om gezindheid te schatten "
                            f"({len(raters)} beoordelaars, {len(ratings)} oordelen): "
                            f"neutraal gewicht 1,0 geldt. Geen klif — bridging schuift "
                            f"vloeiend in zodra er meer oordelen zijn.")
        OUT_PATH.write_text(json.dumps(rapport, indent=1))
        print(f"Bridging slaapt — {rapport['reden']}")
        print(f"Geschreven: {OUT_PATH}")
        return

    mu, b_i = fit(ratings)
    weights, vertrouwen = {}, {}
    for item, b in b_i.items():
        n = per_item.get(item, 0)
        alpha = n / (n + SHRINK_K)            # vertrouwen 0…1, glad met de hoeveelheid bewijs
        # Krimp naar het neutrale gewicht 1,0: alleen een gezindheids-onafhankelijk
        # 'slechter dan gemiddeld' (b < 0) trekt het gewicht omlaag, en dan nog
        # proportioneel aan het vertrouwen. Boven-gemiddeld blijft op 1,0 (geen inflatie).
        weights[item] = round(max(0.0, min(1.0, 1.0 + alpha * b)), 4)
        vertrouwen[item] = round(alpha, 3)
    rapport.update({"actief": True, "mu": round(mu, 4),
                    "weights": weights, "vertrouwen": vertrouwen})
    OUT_PATH.write_text(json.dumps(rapport, indent=1))
    print(f"Bridging actief: {len(weights)} argumentgewichten (krimp naar 1,0, k={SHRINK_K}) "
          f"uit {len(ratings)} oordelen van {len(raters)} beoordelaars.")
    print(f"Geschreven: {OUT_PATH} (gelezen door /api/scores, /api/graph_data en de statische export)")


if __name__ == "__main__":
    main()
