#!/usr/bin/env python3
"""
Voorspellingsregister-CLI (verbeterplan M3.4): overzicht + kalibratierapport.

Het register zelf wordt via de API gevuld en gescoord (POST /api/predictions,
PATCH /api/predictions/<id>/uitkomst — dogfood-regel); dit script leest alleen.

Kalibratie: per kansklasse (bins van 0,2) vergelijken we de gemiddelde
voorspelde kans met de gerealiseerde frequentie; de Brier-score per
voorspelling is (kans − uitkomst)². 'onbeslisbaar' telt niet mee in de
kalibratie maar blijft zichtbaar in het overzicht.

Uitvoer: leesbaar rapport + data/voorspellingen_kalibratie.json.
Gebruik: python3 scripts/voorspellingen.py
"""
import datetime
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
OUT_PATH = ROOT / "data" / "voorspellingen_kalibratie.json"

BIN_BREEDTE = 0.2


def kalibratie(rows):
    """Kalibratie-bins + gemiddelde Brier over de gescoorde voorspellingen."""
    gescoord = [r for r in rows if r["status"] in ("uitgekomen", "niet_uitgekomen")]
    bins = {}
    for r in gescoord:
        b = min(int(r["kans"] / BIN_BREEDTE), int(1 / BIN_BREEDTE) - 1)
        bins.setdefault(b, []).append(r)
    rapport_bins = []
    for b in sorted(bins):
        groep = bins[b]
        rapport_bins.append({
            "kansklasse": f"{b * BIN_BREEDTE:.1f}–{(b + 1) * BIN_BREEDTE:.1f}",
            "n": len(groep),
            "kans_gemiddeld": round(sum(r["kans"] for r in groep) / len(groep), 3),
            "frequentie_uitgekomen": round(
                sum(1 for r in groep if r["status"] == "uitgekomen") / len(groep), 3),
        })
    brier = (round(sum(r["brier"] for r in gescoord) / len(gescoord), 4)
             if gescoord else None)
    return rapport_bins, brier, len(gescoord)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' "
                        "AND name = 'predictions'").fetchone():
        raise SystemExit("FOUT: geen predictions-tabel — draai eerst "
                         "scripts/migrate_fase3_voorspellingen.py")
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM predictions ORDER BY deadline, id")]
    conn.close()

    vandaag = datetime.date.today().isoformat()
    print(f"== Voorspellingsregister (M3.4) — {len(rows)} voorspelling(en) ==\n")
    for r in rows:
        verlopen = " ⚠ deadline verstreken" if (r["status"] == "open"
                                                and r["deadline"] < vandaag) else ""
        zelf = " [zelf gescoord]" if r["self_scored"] else ""
        brier = f"  Brier {r['brier']:.4f}" if r["brier"] is not None else ""
        print(f"#{r['id']:>3} [{r['status']:<15}] kans {r['kans']:.2f}  "
              f"deadline {r['deadline']}{verlopen}{brier}{zelf}")
        print(f"     {r['claim']}")

    bins, brier_gem, n_gescoord = kalibratie(rows)
    print(f"\n== Kalibratie ==")
    if not n_gescoord:
        print("Nog geen gescoorde voorspellingen — het rapport vult zich zodra "
              "uitkomsten beoordeeld zijn (PATCH /api/predictions/<id>/uitkomst).")
    else:
        print(f"Gescoord: {n_gescoord} · gemiddelde Brier: {brier_gem} "
              "(0 = perfect, 0,25 = muntje opgooien op 50%)")
        for b in bins:
            print(f"  kans {b['kansklasse']}: n={b['n']}, voorspeld "
                  f"{b['kans_gemiddeld']:.2f} vs gerealiseerd "
                  f"{b['frequentie_uitgekomen']:.2f}")

    rapport = {
        "gegenereerd": datetime.datetime.now().isoformat(timespec="seconds"),
        "n_totaal": len(rows),
        "n_open": sum(1 for r in rows if r["status"] == "open"),
        "n_gescoord": n_gescoord,
        "n_onbeslisbaar": sum(1 for r in rows if r["status"] == "onbeslisbaar"),
        "brier_gemiddeld": brier_gem,
        "kalibratie_bins": bins,
        "voorspellingen": [{k: r[k] for k in ("id", "claim", "kans", "deadline",
                                              "status", "brier", "self_scored")}
                           for r in rows],
    }
    OUT_PATH.write_text(json.dumps(rapport, ensure_ascii=False, indent=2))
    print(f"\nRapport: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
