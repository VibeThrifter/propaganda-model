#!/usr/bin/env python3
"""Vervolgstappen die wachten op een theorie-element (eigenaar 2026-10-15: "zorg dat het in de
toekomst smooth verloopt").

Wie een RfC indient, legt vaak werk klaar dat pas kan als die RfC is aangenomen: een
registerimport die op het nieuwe mechanisme wacht, verbanden met een nieuwe rol, of een
tweede RfC die de nieuwe rol als eindpunt nodig heeft. Zo'n stap staat als JSON-bestand in
data/vervolg/ en de automatische beoordeling voert hem uit zodra kan (stap 8c, na de RfC's).
Niemand hoeft erop te wachten of eraan te denken.

    {
      "beschrijving": "Provincie → gemeente uit de CBS-indeling (342 verbanden)",
      "wacht_op": [{"mechanisme": "interbestuurlijk_toezicht"}],     # en/of {"rol": "<naam>"}
      "commando": ["tools/registers/cbs_naar_model.py", "--indienen"]
    }

Regels:
- Klaar om te draaien als elk element in `wacht_op` bestaat (niet vervangen).
- Bestaat een element niet en ligt er geen open RfC die het voorstelt, dan vervalt de stap
  (naar data/vervolg/vervallen/): niets gaat het nog maken.
- Het commando is een Python-script binnen de repo (scripts/, tools/ of data/scout/), met
  dezelfde Python als deze ronde, vanuit de repo-map, zonder shell, hooguit 30 minuten.
- Exit 0 → klaar (naar data/vervolg/klaar/), exit 3 → het script wacht zelf nog op iets
  (blijft staan, volgende ronde opnieuw), iets anders → fout (naar data/vervolg/fout/).
  De uitvoer en het moment staan in het verplaatste bestand.

Gebruik:
    python3 scripts/vervolg.py            # toon wat er klaarstaat en wacht
    python3 scripts/vervolg.py --draai    # voer uit wat kan (dit doet de ronde ook)
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "data" / "vervolg"
DB_PATH = ROOT / "data" / "propaganda_model.db"
TOEGESTAAN = ("scripts", "tools", "data/scout")
WACHT = 3            # exit-code: het script wacht zelf nog op een voorwaarde
TIMEOUT_S = 1800
SOORTEN = {"mechanisme": "mechanisms", "rol": "roles"}


def _db(db_path=None):
    return sqlite3.connect(f"file:{db_path or DB_PATH}?mode=ro", uri=True)


def status_element(conn, soort: str, naam: str) -> str:
    """'bestaat', 'voorgesteld' (een open RfC stelt het voor) of 'weg'."""
    tabel = SOORTEN[soort]
    if conn.execute(f"SELECT 1 FROM {tabel} WHERE name = ? AND NOT vervangen",  # noqa: S608
                    (naam,)).fetchone():
        return "bestaat"
    for (payload,) in conn.execute("SELECT payload FROM voorstellen WHERE status = 'open' "
                                   "AND soort = 'nieuw_theorie_element'"):
        try:
            p = json.loads(payload or "{}")
        except ValueError:
            continue
        if p.get("element_type") == soort and p.get("naam") == naam:
            return "voorgesteld"
    return "weg"


def commando_pad(commando) -> Path | None:
    """Het script, als het een .py-bestand binnen een toegestane map van de repo is."""
    if not isinstance(commando, list) or not commando or not all(isinstance(a, str) for a in commando):
        return None
    pad = (ROOT / commando[0]).resolve()
    if pad.suffix != ".py" or not pad.is_file():
        return None
    if not any(pad.is_relative_to((ROOT / t).resolve()) for t in TOEGESTAAN):
        return None
    return pad


def stappen(map_=None) -> list[Path]:
    return sorted((map_ or MAP).glob("*.json"))


def beoordeel(stap: dict, conn) -> tuple[str, str]:
    """→ ('klaar_om_te_draaien' | 'wacht' | 'vervallen' | 'ongeldig', toelichting)."""
    if commando_pad(stap.get("commando")) is None:
        return "ongeldig", f"commando moet een .py-script binnen {', '.join(TOEGESTAAN)} zijn"
    wachtend = []
    for eis in stap.get("wacht_op") or []:
        if not isinstance(eis, dict) or len(eis) != 1 or next(iter(eis)) not in SOORTEN:
            return "ongeldig", f"wacht_op: onbekende eis {eis!r} (gebruik mechanisme of rol)"
        soort, naam = next(iter(eis.items()))
        st = status_element(conn, soort, naam)
        if st == "weg":
            return "vervallen", f"{soort} '{naam}' bestaat niet en geen open RfC stelt het voor"
        if st == "voorgesteld":
            wachtend.append(f"{soort} '{naam}' (open RfC)")
    if wachtend:
        return "wacht", "wacht op " + ", ".join(wachtend)
    return "klaar_om_te_draaien", ""


def _verplaats(pad: Path, stap: dict, uitkomst: str, extra: dict) -> Path:
    doelmap = pad.parent / uitkomst
    doelmap.mkdir(parents=True, exist_ok=True)
    stap = dict(stap, uitkomst=uitkomst, moment=datetime.datetime.now().isoformat(timespec="seconds"),
                **extra)
    doel = doelmap / pad.name
    doel.write_text(json.dumps(stap, ensure_ascii=False, indent=1), encoding="utf-8")
    pad.unlink()
    return doel


def draai(*, droog=False, meld=print, map_=None, db_path=None, timeout=TIMEOUT_S) -> dict:
    """Eén ronde over data/vervolg/*.json. → telling per uitkomst."""
    tel = {"klaar": 0, "wacht": 0, "fout": 0, "vervallen": 0}
    lijst = stappen(map_)
    if not lijst:
        return tel
    for pad in lijst:
        try:
            stap = json.loads(pad.read_text(encoding="utf-8"))
        except ValueError as e:
            if not droog:
                pad.rename(pad.with_suffix(".json.ongeldig"))
            meld(f"  ✗ vervolg {pad.name}: geen geldige JSON ({e})")
            tel["fout"] += 1
            continue
        naam = f"{pad.name} ({stap.get('beschrijving', '')[:80]})"
        with contextlib.closing(_db(db_path)) as conn:
            oordeel, toelichting = beoordeel(stap, conn)
        if oordeel == "wacht":
            tel["wacht"] += 1
            continue
        if oordeel in ("vervallen", "ongeldig"):
            meld(f"  ✗ vervolg {naam}: {toelichting}")
            if not droog:
                _verplaats(pad, stap, "vervallen" if oordeel == "vervallen" else "fout",
                           {"toelichting": toelichting})
            tel["vervallen" if oordeel == "vervallen" else "fout"] += 1
            continue
        if droog:
            meld(f"  · vervolg {naam}: zou nu draaien")
            tel["klaar"] += 1
            continue
        cmd = [sys.executable, str(commando_pad(stap["commando"])), *stap["commando"][1:]]
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
            code, uitvoer = r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            code, uitvoer = -1, f"time-out na {timeout} s"
        staart = "\n".join(uitvoer.strip().splitlines()[-40:])
        if code == WACHT:
            tel["wacht"] += 1
            meld(f"  · vervolg {naam}: wacht nog ({staart.splitlines()[-1] if staart else ''})")
            continue
        uitkomst = "klaar" if code == 0 else "fout"
        _verplaats(pad, stap, uitkomst, {"exit": code, "uitvoer": staart})
        tel[uitkomst] += 1
        meld(f"  {'✓' if code == 0 else '✗'} vervolg {naam}: {uitkomst} (exit {code})")
    meld(f"Vervolg: {tel['klaar']} uitgevoerd, {tel['wacht']} wachten, {tel['fout']} fout, "
         f"{tel['vervallen']} vervallen")
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--draai", action="store_true", help="voer uit wat kan")
    a = ap.parse_args()
    if not a.draai:
        with contextlib.closing(_db()) as conn:
            for pad in stappen():
                stap = json.loads(pad.read_text(encoding="utf-8"))
                oordeel, toelichting = beoordeel(stap, conn)
                print(f"{pad.name}: {oordeel} {toelichting} — {stap.get('beschrijving', '')}")
        return
    draai()


if __name__ == "__main__":
    main()
