#!/usr/bin/env python3
"""Rem voor X/Instagram/TikTok — dezelfde opzet als tools/linkedin/snelheidsrem.py, maar per
platform en per profielbezoek (eigenaar 2026-10-19: ook X/Instagram/TikTok volgen, alleen met
een trage rem zoals LinkedIn).

Regels per platform:
  * max KANALEN_MAX_PER_DAG profielbezoeken per lokale kalenderdag (standaard 6, hard plafond 6);
  * alleen 08:00–22:00;
  * stroomonderbreker: een loginmuur, captcha of blokkade stopt dat platform 24 uur, bij
    herhaling verdubbelend tot 7 dagen; na een geslaagde dag terug naar 0;
  * kill-switch: env KANALEN_SOCIAAL=0, of `rem.py uit`.
Env-overrides mogen alleen strenger. Toestand: data/kanalen/_rem.json (fcntl-lock).

CLI:
    python3 tools/kanalen/rem.py status
    python3 tools/kanalen/rem.py uit|aan
    python3 tools/kanalen/rem.py reset-blokkade <platform>
"""
from __future__ import annotations

import contextlib
import datetime
import fcntl
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAND = ROOT / "data" / "kanalen" / "_rem.json"
MAX_PER_DAG = 6
ACTIEF_VAN, ACTIEF_TOT = 8, 22
BLOKKADE_UUR = 24
BLOKKADE_MAX_UUR = 24 * 7
EXIT_REM, EXIT_BLOKKADE = 75, 76


def _max_per_dag() -> int:
    try:
        return max(0, min(MAX_PER_DAG, int(os.environ.get("KANALEN_MAX_PER_DAG", MAX_PER_DAG))))
    except ValueError:
        return MAX_PER_DAG


@contextlib.contextmanager
def _stand():
    STAND.parent.mkdir(parents=True, exist_ok=True)
    with open(STAND, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            data = json.loads(f.read() or "{}")
        except json.JSONDecodeError:
            data = {}
        yield data
        f.seek(0)
        f.truncate()
        f.write(json.dumps(data, indent=1))


def _platform(data: dict, p: str) -> dict:
    return data.setdefault("platforms", {}).setdefault(
        p, {"bezoeken": [], "geblokkeerd_tot": None, "niveau": 0, "reden": None})


def mag(platform: str, nu: datetime.datetime | None = None) -> tuple[bool, str]:
    """(mag, reden). Registreert het bezoek als het mag."""
    nu = nu or datetime.datetime.now()
    if os.environ.get("KANALEN_SOCIAAL", "1") == "0":
        return False, "kill-switch KANALEN_SOCIAAL=0"
    with _stand() as data:
        if data.get("uit"):
            return False, "uitgezet (rem.py uit)"
        if not (ACTIEF_VAN <= nu.hour < ACTIEF_TOT):
            return False, f"buiten {ACTIEF_VAN:02d}:00–{ACTIEF_TOT:02d}:00"
        st = _platform(data, platform)
        if st["geblokkeerd_tot"] and nu.isoformat() < st["geblokkeerd_tot"]:
            return False, f"geblokkeerd tot {st['geblokkeerd_tot'][:16]} ({st['reden']})"
        if st["geblokkeerd_tot"]:          # blokkade verlopen: eerste geslaagde dag telt
            st["geblokkeerd_tot"] = None
            st["herstel_sinds"] = nu.isoformat()
        if st.get("herstel_sinds") and (nu - datetime.datetime.fromisoformat(
                st["herstel_sinds"])).total_seconds() >= 86400:
            st["niveau"], st["herstel_sinds"] = 0, None
        vandaag = nu.date().isoformat()
        st["bezoeken"] = [b for b in st["bezoeken"] if b.startswith(vandaag)]
        if len(st["bezoeken"]) >= _max_per_dag():
            return False, f"dagmaximum {_max_per_dag()} bereikt"
        st["bezoeken"].append(nu.isoformat(timespec="seconds"))
        return True, "ok"


def blokkade(platform: str, reden: str, nu: datetime.datetime | None = None) -> str:
    nu = nu or datetime.datetime.now()
    with _stand() as data:
        st = _platform(data, platform)
        uren = min(BLOKKADE_MAX_UUR, BLOKKADE_UUR * (2 ** st["niveau"]))
        st["niveau"] += 1
        st["geblokkeerd_tot"] = (nu + datetime.timedelta(hours=uren)).isoformat(timespec="seconds")
        st["reden"] = reden
        st.pop("herstel_sinds", None)
        return st["geblokkeerd_tot"]


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd in ("uit", "aan"):
        with _stand() as data:
            data["uit"] = cmd == "uit"
        print(f"sociale kanalen: {cmd}")
    elif cmd == "reset-blokkade" and len(sys.argv) > 2:
        with _stand() as data:
            st = _platform(data, sys.argv[2])
            st.update(geblokkeerd_tot=None, niveau=0, reden=None)
        print(f"blokkade {sys.argv[2]} gewist")
    else:
        with _stand() as data:
            print(json.dumps({"uit": bool(data.get("uit")), "max_per_dag": _max_per_dag(),
                              "platforms": data.get("platforms", {})}, indent=1))


if __name__ == "__main__":
    main()
