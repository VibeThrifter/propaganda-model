#!/usr/bin/env python3
"""Integratiecontrole — blijft alles op elkaar aansluiten? (eigenaar 2026-10-14: "hoe zorgen we
ervoor dat dat goed verloopt, alle integratie").

Meerdere sessies en agents passen tegelijk code en data aan. Dit script draait elke nacht
(launchd-job `integratiecontrole`, agent_schedule.py) en controleert drie dingen:

  1. **De testsuites** (`scripts/test_*.py`, `tools/linkedin/test_*.py`). Elke suite bouwt een eigen,
     tijdelijke database; de live database wordt nooit aangeraakt.
  2. **De modelvalidatie** (`validate_model.py --strict`): geen fout boven de baseline, en het
     golden snapshot van de scores.
  3. **Een rooktest tegen de live server.** Alleen lezen. De pagina's en API's antwoorden (/, /partijen,
     /methode, /api/health, /api/partijen, /api/graph_data, /metingen, /api/metingen). Het laatst goedgekeurde verband staat
     in graph_data, en de laatst goedgekeurde partijband staat in /api/partijen/<partij>. Zo blijkt
     dat afgeleide overzichten echt live uit dezelfde database komen.

Het resultaat gaat naar data/integratiecontrole.json (de laatste run; /api/toezicht en /beheer
tonen het) en wordt toegevoegd aan data/integratiecontrole_log.jsonl. Een onderdeel dat de vorige
keer groen was en nu rood is, is een **regressie**. Een onderdeel dat al rood was, blijft gemeld
maar is geen nieuw alarm. Exit-code 1 bij een regressie.

Gebruik: python3 scripts/integratiecontrole.py [--api http://127.0.0.1:5000] [--zonder-tests]
"""
from __future__ import annotations

import argparse
import datetime
import json
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
UIT_PAD = ROOT / "data" / "integratiecontrole.json"
LOG_PAD = ROOT / "data" / "integratiecontrole_log.jsonl"
SUITE_TIMEOUT_S = 1200
PAGINAS = ["/", "/partijen", "/methode", "/api/health", "/api/partijen", "/api/graph_data",
           "/metingen", "/api/metingen"]   # eigen metingen (2026-10-16); test_metingen.py draait mee
PARTIJBANDEN = ("lidmaatschap", "bestuurder", "adviseur", "personeel", "dienstverband",
                "woordvoerder_van", "draaideur")


def suites() -> list[Path]:
    return sorted((ROOT / "scripts").glob("test_*.py")) + sorted((ROOT / "tools" / "linkedin").glob("test_*.py"))


def draai(naam: str, cmd: list[str], timeout: int) -> dict:
    t0 = time.monotonic()
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        ok, uitvoer = r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        ok, uitvoer = False, f"time-out na {timeout} s\n{(e.stdout or '')[-500:] if isinstance(e.stdout, str) else ''}"
    staart = "\n".join(uitvoer.strip().splitlines()[-6:])
    return {"naam": naam, "ok": ok, "duur_s": round(time.monotonic() - t0, 1), "staart": staart[-1200:]}


def haal(api: str, pad: str):
    with urllib.request.urlopen(api + pad, timeout=120) as r:
        return r.status, r.read()


def rooktest(api: str) -> list[dict]:
    uit = []
    for pad in PAGINAS:
        t0 = time.monotonic()
        try:
            status, _ = haal(api, pad)
            uit.append({"naam": f"live {pad}", "ok": status == 200, "duur_s": round(time.monotonic() - t0, 1),
                        "staart": f"HTTP {status}"})
        except Exception as e:  # noqa: BLE001 — elke fout is een rode rooktest
            uit.append({"naam": f"live {pad}", "ok": False, "duur_s": round(time.monotonic() - t0, 1),
                        "staart": f"{type(e).__name__}: {e}"[:300]})
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=60)
    try:
        laatste = conn.execute("""SELECT id FROM relations WHERE status = 'goedgekeurd' AND NOT vervangen
                                  ORDER BY id DESC LIMIT 1""").fetchone()
        band = conn.execute(f"""
            SELECT r.id, CASE WHEN s.type = 'partij' THEN s.id ELSE t.id END,
                   CASE WHEN s.type = 'partij' THEN t.id ELSE s.id END
            FROM relations r JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
            WHERE r.status = 'goedgekeurd' AND NOT r.vervangen
              AND s.status = 'goedgekeurd' AND t.status = 'goedgekeurd'
              AND r.relation_type IN ({','.join('?' * len(PARTIJBANDEN))})
              AND ((s.type = 'partij' AND t.type = 'persoon') OR (s.type = 'persoon' AND t.type = 'partij'))
            ORDER BY r.id DESC LIMIT 1""", PARTIJBANDEN).fetchone()
    finally:
        conn.close()
    try:
        g = json.loads(haal(api, "/api/graph_data")[1])
        ids = {r["id"] for r in g.get("relations", [])}
        ok = laatste is None or laatste[0] in ids
        uit.append({"naam": "live: laatst goedgekeurd verband in graph_data", "ok": ok, "duur_s": 0,
                    "staart": f"relatie #{laatste[0] if laatste else '-'} {'aanwezig' if ok else 'ONTBREEKT'}"})
    except Exception as e:  # noqa: BLE001
        uit.append({"naam": "live: laatst goedgekeurd verband in graph_data", "ok": False, "duur_s": 0,
                    "staart": f"{type(e).__name__}: {e}"[:300]})
    if band:
        rid, partij, pers = band
        try:
            d = json.loads(haal(api, f"/api/partijen/{partij}")[1])
            ok = any(b.get("relation_id") == rid for p in d.get("personen", []) if p.get("id") == pers
                     for b in p.get("band", []))
            uit.append({"naam": "live: laatste partijband in /api/partijen", "ok": ok, "duur_s": 0,
                        "staart": f"relatie #{rid} bij partij #{partij} {'aanwezig' if ok else 'ONTBREEKT'}"})
        except Exception as e:  # noqa: BLE001
            uit.append({"naam": "live: laatste partijband in /api/partijen", "ok": False, "duur_s": 0,
                        "staart": f"{type(e).__name__}: {e}"[:300]})
    return uit


def vorige() -> dict:
    try:
        return {o["naam"]: o["ok"] for o in json.loads(UIT_PAD.read_text(encoding="utf-8"))["onderdelen"]}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api", default="http://127.0.0.1:5000")
    ap.add_argument("--zonder-tests", action="store_true", help="alleen validatie en rooktest")
    a = ap.parse_args()
    t0 = time.monotonic()
    onderdelen = []
    if not a.zonder_tests:
        for pad in suites():
            onderdelen.append(draai(pad.stem, [sys.executable, str(pad)], SUITE_TIMEOUT_S))
    onderdelen.append(draai("validate_model --strict",
                            [sys.executable, str(ROOT / "scripts" / "validate_model.py"), "--strict"], 900))
    onderdelen += rooktest(a.api)
    oud = vorige()
    for o in onderdelen:
        o["regressie"] = (not o["ok"]) and oud.get(o["naam"]) is True
    regressies = [o["naam"] for o in onderdelen if o["regressie"]]
    rood = [o["naam"] for o in onderdelen if not o["ok"]]
    uit = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
           "ok": not rood, "regressies": regressies, "rood": rood,
           "n": len(onderdelen), "n_groen": len(onderdelen) - len(rood),
           "duur_s": round(time.monotonic() - t0), "onderdelen": onderdelen}
    UIT_PAD.parent.mkdir(parents=True, exist_ok=True)
    tmp = UIT_PAD.with_suffix(".tmp")
    tmp.write_text(json.dumps(uit, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(UIT_PAD)
    with open(LOG_PAD, "a", encoding="utf-8") as f:
        f.write(json.dumps({k: uit[k] for k in ("ts", "ok", "regressies", "rood", "n", "n_groen", "duur_s")},
                           ensure_ascii=False) + "\n")
    print(f"Integratiecontrole: {uit['n_groen']}/{uit['n']} groen"
          + (f"; rood: {', '.join(rood)}" if rood else "")
          + (f"; REGRESSIE: {', '.join(regressies)}" if regressies else ""))
    sys.exit(1 if regressies else 0)


if __name__ == "__main__":
    main()
