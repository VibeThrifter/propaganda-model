#!/usr/bin/env python3
"""macOS-scheduling voor de onbewaakte missie-agents (C1) via launchd.

De agent-missies *zijn* Claude Code-sessies (`claude -p`, via
`scripts/agent_runner.py`). launchd is de enige planner (de oude systemd-timers en
crontab zijn weg, zie git-geschiedenis vóór 2026-10-13). Deze
generator schrijft één LaunchAgent-plist per agent naar `~/Library/LaunchAgents/`,
plus een KeepAlive-plist voor de Flask-server (de agents POSTen ernaar, dus die moet
draaien).

De **canonieke agent-lijst + het schema** wonen in `agent_schedule.py` (gedeeld met
server.py, dat het agents-paneel + de schema-editor op /beheer toont). Overrides op
de cadans leven in `data/agent_schedules.json` — de UI schrijft die en roept dit
script aan (`--geen-server --laden`) om ze toe te passen. Een agent op `freq: "uit"`
wordt niet geladen en z'n bestaande plist wordt ge-bootout.

Stdlib-only (projectregel): `plistlib` + `launchctl`.

Waarom `--skip-permissions` in de agent-plists? Een onbewaakte `claude -p`-sessie
blokkeert anders op tool-permissieprompts (WebFetch/Bash/Write). Op een vertrouwde
eigen machine is `--dangerously-skip-permissions` de juiste keuze; de blast radius
blijft begrensd door de missie-brief én de API-poorten (alles landt `voorgesteld`,
het agent-token kan niet mergen).

Gebruik:
  python3 deploy/launchd/genereer_launchd.py --lijst        # toon wat er komt (droog)
  python3 deploy/launchd/genereer_launchd.py                # schrijf plists (nog niet laden)
  python3 deploy/launchd/genereer_launchd.py --laden        # schrijf + launchctl bootstrap
  python3 deploy/launchd/genereer_launchd.py --verwijderen  # bootout + plists weg
  python3 deploy/launchd/genereer_launchd.py --geen-server  # sla de server-KeepAlive over
"""
import argparse
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
import agent_schedule as sched  # noqa: E402

PY = sys.executable or "/usr/bin/python3"
RUNNER = str(ROOT / "scripts" / "agent_runner.py")
LABEL_PREFIX = "nl.propaganda."
LAUNCHAGENTS = Path.home() / "Library" / "LaunchAgents"
LOGDIR = ROOT / "data" / "launchd"            # gitignored (data/)
CLAUDE = shutil.which("claude") or "/usr/local/bin/claude"
# caffeinate houdt de Mac wakker zolang een ronde loopt (`-i` = geen idle-sleep). Zonder
# dit valt een ~10-min claude-sessie stil als de laptop in slaap gaat → "Connection closed
# mid-response" → exit 1. Lost idle-sleep op; een dichtgeklapt deksel blijft VPS-terrein.
CAFFEINATE = shutil.which("caffeinate") or "/usr/bin/caffeinate"
PATH_ENV = "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"


def _plist_gemeen(label, argv, interval):
    p = {
        "Label": label,
        "ProgramArguments": argv,
        "WorkingDirectory": str(ROOT),
        "EnvironmentVariables": {"PATH": PATH_ENV},
        "RunAtLoad": False,
        "StandardOutPath": str(LOGDIR / f"{label.split('.')[-1]}.out.log"),
        "StandardErrorPath": str(LOGDIR / f"{label.split('.')[-1]}.err.log"),
        "ProcessType": "Background",
    }
    if interval is not None:
        p["StartInterval"] = interval   # elke N seconden (elke X min/uur/dag)
    return p


def bouw_plist(agent):
    """Geef (label, plist) of None als de agent op 'uit' staat."""
    interval = sched.interval_seconden(agent["schema"])
    if interval is None:
        return None
    label = LABEL_PREFIX + "agent-" + agent["naam"]
    soort, spec, timeout = agent["soort"], agent["spec"], agent["timeout"]
    if soort in ("runner", "leesagent"):
        # caffeinate -i <cmd>: houd de Mac wakker zolang de ronde loopt (agent_runner
        # bewaakt zelf de max-duur via --timeout). Model+effort vastgezet (Opus + high).
        argv = [CAFFEINATE, "-i",
                PY, RUNNER, *spec, "--timeout", str(timeout),
                "--claude-bin", CLAUDE, "--skip-permissions",
                "--model", sched.AGENT_MODEL, "--effort", sched.AGENT_EFFORT]
    else:  # kaal script (geen claude, geen skip-permissions)
        argv = [PY, str(ROOT / spec[0]), *spec[1:]]
    return label, _plist_gemeen(label, argv, interval)


def bouw_server_plist():
    label = LABEL_PREFIX + "server"
    plist = {
        "Label": label,
        "ProgramArguments": [PY, str(ROOT / "server.py")],
        "WorkingDirectory": str(ROOT),
        "EnvironmentVariables": {"PATH": PATH_ENV},
        "KeepAlive": True,
        "RunAtLoad": True,
        "StandardOutPath": str(LOGDIR / "server.out.log"),
        "StandardErrorPath": str(LOGDIR / "server.err.log"),
        "ProcessType": "Standard",
    }
    return label, plist


def actief_en_uit(met_server):
    """(items om te laden, labels die 'uit' staan). items = list van (label, plist)."""
    items, uit = [], []
    if met_server:
        items.append(bouw_server_plist())
    for a in sched.alle_effectief():
        res = bouw_plist(a)
        if res is None:
            uit.append(LABEL_PREFIX + "agent-" + a["naam"])
        else:
            items.append(res)
    return items, uit


def toon(items, uit):
    print(f"Repo:   {ROOT}")
    print(f"Python: {PY}")
    print(f"claude: {CLAUDE}")
    print(f"Doel:   {LAUNCHAGENTS}/")
    print(f"Logs:   {LOGDIR}/  (gitignored)\n")
    for label, plist in items:
        iv = plist.get("StartInterval")
        cadans = f"elke {iv}s" if iv else "KeepAlive (altijd aan)"
        argv = plist["ProgramArguments"]
        print(f"• {label}")
        print(f"    cadans: {cadans}")
        print(f"    cmd:    …/{Path(argv[1]).name} {' '.join(argv[2:])}")
    if uit:
        print("\nUIT (niet geladen; bestaande plist wordt verwijderd):")
        for label in uit:
            print(f"  · {label}")


def uid():
    return os.getuid()


def launchctl(*args):
    r = subprocess.run(["launchctl", *args], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def schrijf(items, uit):
    LAUNCHAGENTS.mkdir(parents=True, exist_ok=True)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    paden = []
    for label, plist in items:
        pad = LAUNCHAGENTS / f"{label}.plist"
        with open(pad, "wb") as f:
            plistlib.dump(plist, f)
        paden.append((label, pad))
        print(f"✓ geschreven: {pad}")
    # 'uit'-agents: plist weg zodat ze niet meer bestaan
    for label in uit:
        pad = LAUNCHAGENTS / f"{label}.plist"
        if pad.exists():
            pad.unlink()
            print(f"✗ verwijderd (uit): {pad}")
    return paden


def laden(paden, uit):
    dom = f"gui/{uid()}"
    for label in uit:  # eerst de uitgeschakelde eruit booten
        launchctl("bootout", f"{dom}/{label}")
    for label, pad in paden:
        launchctl("bootout", f"{dom}/{label}")          # idempotent
        rc, msg = launchctl("bootstrap", dom, str(pad))
        print(f"  launchctl bootstrap {label}: {'geladen' if rc == 0 else 'FOUT (' + msg + ')'}")
    print(f"\nControleer: launchctl list | grep {LABEL_PREFIX}")
    print(f"Handmatig testen: launchctl kickstart -k {dom}/{LABEL_PREFIX}agent-monitor")


def verwijderen():
    dom = f"gui/{uid()}"
    for pad in sorted(LAUNCHAGENTS.glob(f"{LABEL_PREFIX}*.plist")):
        launchctl("bootout", f"{dom}/{pad.stem}")
        pad.unlink()
        print(f"✗ verwijderd + uitgeladen: {pad.stem}")


def main():
    ap = argparse.ArgumentParser(description="launchd-scheduling voor de missie-agents (C1, macOS).")
    ap.add_argument("--lijst", action="store_true", help="Toon alleen wat er komt (droog).")
    ap.add_argument("--laden", action="store_true", help="Na schrijven ook launchctl bootstrap.")
    ap.add_argument("--verwijderen", action="store_true", help="bootout + plists verwijderen.")
    ap.add_argument("--geen-server", action="store_true", help="Sla de server-KeepAlive-plist over.")
    args = ap.parse_args()

    if args.verwijderen:
        verwijderen()
        return

    items, uit = actief_en_uit(met_server=not args.geen_server)

    if args.lijst:
        toon(items, uit)
        print("\n(Droog — niets geschreven. Laat --lijst weg om te schrijven.)")
        return

    toon(items, uit)
    print()
    paden = schrijf(items, uit)
    if args.laden:
        print()
        laden(paden, uit)
    else:
        print("\nGeschreven maar nog niet geladen. Laad met:")
        print(f"  python3 {Path(__file__).relative_to(ROOT)} --laden")


if __name__ == "__main__":
    main()
