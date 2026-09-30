#!/usr/bin/env python3
"""Onbewaakte missie-runner (C1) — draai één missie-ronde als headless Claude-sessie.

De agent-missies *zijn* Claude Code-sessies (zie missies/README.md); "schedulen"
betekent dus: per ronde één non-interactieve `claude -p "<prompt>"`-invocatie
plannen. Deze wrapper (stdlib-only, geen nieuwe dependency) is wat een systemd-timer
of cron-entry aanroept:

  * laadt het Bearer-token uit data/tokens/<account>.token (behalve tokenloze,
    alleen-lezen missies zoals de reviewbeoordelaar/voorspelling-resolutie);
  * bouwt de missie-prompt (verwijzing naar de brief + het account + de vaste
    voorregel: eerst GET /api/agent/reeds_gereageerd en die id's overslaan);
  * roept één `claude -p`-sessie aan en tee't stdout/stderr naar
    missies/logs/<datum>_<label>_<ronde>.md;
  * vangt exit-code + duur + oogst-telling (edit_log-delta van het account) en
    schrijft een run-record (log-footer + data/agent_runs.jsonl, C4-toezicht);
  * detecteert een dode LinkedIn-sessie en relayt het login-commando i.p.v. te
    herproberen; detecteert ook de LinkedIn-snelheidsrem (exit 75,
    "LINKEDIN-SNELHEIDSREM") en de stroomonderbreker ("LINKEDIN-BLOKKADE") en zet die
    als `linkedin_rem`/`linkedin_blokkade` in het run-record (Epic 12);
  * één ronde per label tegelijk: een fcntl-lock `data/locks/<label>.lock` (bezet →
    melding + exit 0, geen claude);
  * `--alleen-bij-open-doelen` (nieuws-scout): start alleen als de wachtrij
    `nieuws_doelen` open werk heeft (open, of 'bezig' met een claim > 3 uur) — anders
    exit 0 zonder claude en zonder logbestand; `--max-rondes-per-dag N` en
    `--actieve-uren 8-22` begrenzen het verbruik (Epic 12: max 4 rondes/dag, 08–22 uur).

Alles blijft binnen het agent-contract: de sessie draagt bij onder haar eigen token,
alles landt `voorgesteld`, geen statuswijzigingen. De wrapper zelf schrijft niets in
het model — alleen een logbestand + een run-record.

Gebruik:
  python3 scripts/agent_runner.py --agent monitor-agent --brief missies/monitor_brief.md
  python3 scripts/agent_runner.py --agent monitor-agent --brief missies/monitor_brief.md --dry-run
  python3 scripts/agent_runner.py --agent assistent --label ideoloog --brief missies/ideoloog_brief.md
  python3 scripts/agent_runner.py --label reviewbeoordelaar --geen-token \\
      --brief missies/reviewbeoordelaar_brief.md
  python3 scripts/agent_runner.py --agent nieuws-scout --label nieuws-scout \\
      --brief missies/nieuws_scout_brief.md --alleen-bij-open-doelen --dry-run
"""
import argparse
import datetime
import fcntl
import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOKENS_DIR = ROOT / "data" / "tokens"
LOGS_DIR = ROOT / "missies" / "logs"
DB_PATH = ROOT / "data" / "propaganda_model.db"
RUNS_JSONL = ROOT / "data" / "agent_runs.jsonl"
LOCKS_DIR = ROOT / "data" / "locks"

LINKEDIN_SESSIE_DOOD = "LINKEDIN-SESSIE VERLOPEN"
LINKEDIN_LOGIN_CMD = "python3 tools/linkedin/scrape_profile.py login"
LINKEDIN_REM = "LINKEDIN-SNELHEIDSREM"        # tools/linkedin/snelheidsrem.py (exit 75)
LINKEDIN_BLOKKADE = "LINKEDIN-BLOKKADE"       # stroomonderbreker gesprongen (exit 76)
NIEUWS_CLAIM_VERLOOP_UUR = 3                  # spiegelt server.py (claim_volgende)


def brief_hash(brief: Path) -> str:
    """Blob-hash van het briefbestand (de 'briefversie' uit missies/README.md)."""
    try:
        out = subprocess.run(["git", "hash-object", str(brief)], cwd=ROOT,
                             capture_output=True, text=True, timeout=10)
        if out.returncode == 0:
            return out.stdout.strip()[:12]
    except (OSError, subprocess.SubprocessError):
        pass
    return "onbekend"


def volgende_ronde(datum: str, label: str) -> str:
    """ronde<N> op basis van bestaande logs voor dezelfde datum + label."""
    bestaand = list(LOGS_DIR.glob(f"{datum}_{label}_*.md"))
    return f"ronde{len(bestaand) + 1}"


def edit_log_telling(account: str) -> int:
    """Aantal edit_log-schrijfacties van een account (voor de oogst-delta). Wachtrij-
    administratie (nieuws_doelen: claims/PATCH) is geen oogst en telt niet mee."""
    if not DB_PATH.exists() or not account:
        return 0
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        n = conn.execute("SELECT COUNT(*) FROM edit_log WHERE changed_by = ? "
                         "AND table_name <> 'nieuws_doelen'", (account,)).fetchone()[0]
        conn.close()
        return int(n)
    except sqlite3.Error:
        return 0


def open_nieuws_doelen():
    """Aantal doelen in de nieuws-wachtrij met werk (open, of 'bezig' met een claim
    ouder dan NIEUWS_CLAIM_VERLOOP_UUR). Alleen-lezen. None = tabel/DB ontbreekt."""
    if not DB_PATH.exists():
        return None
    grens = (datetime.datetime.now() - datetime.timedelta(hours=NIEUWS_CLAIM_VERLOOP_UUR)
             ).isoformat(timespec="seconds")
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        try:
            return int(conn.execute(
                "SELECT COUNT(*) FROM nieuws_doelen WHERE status = 'open' OR "
                "(status = 'bezig' AND (geclaimd_op IS NULL OR geclaimd_op < ?))",
                (grens,)).fetchone()[0])
        finally:
            conn.close()
    except sqlite3.Error:
        return None


def rondes_vandaag(label: str, datum: str) -> int:
    """Aantal echte rondes (run-records) van dit label op deze datum."""
    if not RUNS_JSONL.exists():
        return 0
    n = 0
    try:
        for regel in RUNS_JSONL.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(regel)
            except json.JSONDecodeError:
                continue
            if r.get("label") == label and r.get("datum") == datum:
                n += 1
    except OSError:
        return 0
    return n


def parse_uren(spec: str):
    """'8-22' → (8, 22): van (incl.) tot (excl.). Ongeldig → argparse-fout."""
    m = re.fullmatch(r"\s*(\d{1,2})\s*-\s*(\d{1,2})\s*", spec or "")
    if not m or not (0 <= int(m.group(1)) < int(m.group(2)) <= 24):
        raise argparse.ArgumentTypeError("verwacht VAN-TOT in hele uren, bv. 8-22")
    return int(m.group(1)), int(m.group(2))


def neem_lock(label: str):
    """Niet-blokkerende fcntl-lock per label. → open bestand (vasthouden tot exit) of
    None als een andere ronde van dit label al loopt."""
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    f = open(LOCKS_DIR / f"{label}.lock", "a+")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    f.seek(0)
    f.truncate()
    f.write(f"{os.getpid()} {datetime.datetime.now().isoformat(timespec='seconds')}\n")
    f.flush()
    return f


def lock_bezet(label: str) -> bool:
    """Alleen voor de droogloop: is de lock nu bezet? (neemt en geeft direct vrij)"""
    pad = LOCKS_DIR / f"{label}.lock"
    if not pad.exists():
        return False
    with open(pad, "a+") as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return True
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    return False


def bouw_prompt(account, brief, label, ronde, datum, bhash, geen_token) -> str:
    lognaam = f"missies/logs/{datum}_{label}_{ronde}.md"
    regels = [
        f"Je draait een onbewaakte, geplande missie-ronde ({ronde}) van de agent "
        f"\"{label}\".",
        f"Lees en volg de missie-brief in deze repo: {brief} "
        f"(briefversie/blob-hash {bhash}).",
    ]
    if geen_token:
        regels += [
            "Dit is een ALLEEN-LEZEN missie: je hebt geen token en dient niets in het "
            "model in. Je enige uitvoer is het adviesbestand dat de brief noemt "
            "(een gewoon JSON-bestand, geen API-schrijfactie) plus je ronde-log. "
            "GET-endpoints zijn open en vergen geen token.",
        ]
    else:
        regels += [
            f"Authenticeer elke schrijfactie met het Bearer-token uit "
            f"data/tokens/{account}.token (GET-endpoints zijn open). Alles wat je "
            "indient landt 'voorgesteld' en telt in niets tot een mens het merget; "
            "je zet NOOIT statussen, merget niets, classificeert geen bronnen en "
            "verwijdert niets — dat is reviewer+/maintainer én mensenwerk.",
            "VOORREGEL (verplicht, vóór je iets indient): haal GET "
            "/api/agent/reeds_gereageerd op met je token en sla elk argument-id "
            "daaruit over — reageer nooit twee keer op hetzelfde argument (de server "
            "weigert een tweede agent-reply op dezelfde parent met 409).",
        ]
    regels += [
        f"Log deze ronde in {lognaam} met: de brief-blob-hash ({bhash}), élke "
        "zoekopdracht letterlijk (web of database), per vondst het aangemaakte "
        "source-/entity-/relation-/argument-id, de negatieve resultaten (alléén in "
        "het log, nooit als contextual modelbijdrage), en de stance-balans van de "
        "ronde (n steun / n tegen / n context).",
        "Exit-condities: (a) lege oogst — niets relevants te doen → rond af en log "
        "dat, dien geen vulling in; (b) rate-limit 429 → stop de ronde en log het, "
        "herprobeer niet in een lus; (c) een dode LinkedIn-sessie "
        f"(\"⚠ {LINKEDIN_SESSIE_DOOD}\") → stop, relay letterlijk het login-commando "
        f"`{LINKEDIN_LOGIN_CMD}` aan de eigenaar en herprobeer niet.",
    ]
    return "\n\n".join(regels)


def stream_naar_log(proc, logfile) -> str:
    """Tee de gecombineerde stdout/stderr naar console én logbestand; geef terug."""
    stukken = []
    for regel in iter(proc.stdout.readline, ""):
        sys.stdout.write(regel)
        sys.stdout.flush()
        logfile.write(regel)
        stukken.append(regel)
    proc.stdout.close()
    return "".join(stukken)


def main():
    ap = argparse.ArgumentParser(description="Onbewaakte missie-runner (C1).")
    ap.add_argument("--agent", default="",
                    help="Account-naam (data/tokens/<naam>.token). Leeg bij --geen-token.")
    ap.add_argument("--brief", required=True, help="Pad naar de missie-brief.")
    ap.add_argument("--label", default="",
                    help="Naam in het logbestand (default = --agent). Gebruik dit als "
                         "meerdere overlays onder één account draaien, bv. --agent "
                         "assistent --label ideoloog.")
    ap.add_argument("--ronde", default="",
                    help="Ronde-tag in de logbestandsnaam (default: auto ronde<N>).")
    ap.add_argument("--geen-token", action="store_true",
                    help="Alleen-lezen missie zonder token (reviewbeoordelaar, "
                         "voorspelling-resolutie).")
    ap.add_argument("--claude-bin", default="claude",
                    help="Pad naar de claude-CLI (default: claude op PATH).")
    ap.add_argument("--model", default="",
                    help="Optioneel model doorgeven aan `claude -p` (bv. opus).")
    ap.add_argument("--effort", default="",
                    help="Optioneel reasoning-effort doorgeven aan `claude -p` (bv. high).")
    ap.add_argument("--skip-permissions", action="store_true",
                    help="Voeg --dangerously-skip-permissions toe aan de claude-sessie. "
                         "NODIG voor echt onbewaakte runs (launchd/cron): anders "
                         "blokkeren tool-permissieprompts (WebFetch/Bash/Write) de ronde. "
                         "Alleen op een vertrouwde eigen machine; de missie-brief + de "
                         "API-poorten (alles landt 'voorgesteld', het agent-token kan niet "
                         "mergen) begrenzen de blast radius.")
    ap.add_argument("--timeout", type=int, default=0,
                    help="Harde timeout in seconden (0 = geen; systemd doet dit meestal).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print het exacte claude-commando + tokenpad, draai niets.")
    ap.add_argument("--alleen-bij-open-doelen", action="store_true",
                    help="Epic 12 (nieuws-scout): alleen starten als de wachtrij "
                         "nieuws_doelen open werk heeft; anders exit 0 zonder claude en "
                         "zonder logbestand.")
    ap.add_argument("--max-rondes-per-dag", type=int, default=0,
                    help="Max. echte rondes per kalenderdag voor dit label (0 = onbegrensd); "
                         "daarboven exit 0 zonder claude.")
    ap.add_argument("--actieve-uren", type=parse_uren, default=None, metavar="VAN-TOT",
                    help="Alleen starten binnen deze lokale uren, bv. 8-22; daarbuiten exit 0.")
    args = ap.parse_args()

    brief = Path(args.brief)
    if not brief.is_absolute():
        brief = ROOT / brief
    if not brief.exists():
        sys.exit(f"Brief niet gevonden: {brief}")

    account = args.agent.strip()
    label = (args.label or account or brief.stem.replace("_brief", "")).strip()
    token_pad = TOKENS_DIR / f"{account}.token" if account else None

    if not args.geen_token:
        if not account:
            sys.exit("Geef --agent <account> (of gebruik --geen-token voor een "
                     "alleen-lezen missie).")
        if not token_pad.exists() and not args.dry_run:
            sys.exit(f"Token niet gevonden: {token_pad}\n"
                     "Maak het aan via scripts/create_user.py, of gebruik --geen-token.")

    datum = datetime.date.today().isoformat()
    ronde = args.ronde or volgende_ronde(datum, label)
    bhash = brief_hash(brief)
    prompt = bouw_prompt(account, brief.relative_to(ROOT), label, ronde, datum, bhash,
                         args.geen_token)

    cmd = [args.claude_bin, "-p", prompt]
    if args.skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    if args.model:
        cmd += ["--model", args.model]
    if args.effort:
        cmd += ["--effort", args.effort]

    logpad = LOGS_DIR / f"{datum}_{label}_{ronde}.md"

    # Poorten vóór de sessie (Epic 12): elk levert een reden om NIET te draaien.
    def overslaan_reden():
        if args.actieve_uren:
            van, tot = args.actieve_uren
            if not (van <= datetime.datetime.now().hour < tot):
                return f"buiten de actieve uren ({van:02d}:00–{tot:02d}:00)"
        if args.max_rondes_per_dag and rondes_vandaag(label, datum) >= args.max_rondes_per_dag:
            return (f"dagmaximum bereikt ({rondes_vandaag(label, datum)}/"
                    f"{args.max_rondes_per_dag} rondes vandaag)")
        if args.alleen_bij_open_doelen:
            n = open_nieuws_doelen()
            if not n:
                return ("geen open nieuws-doelen" if n == 0
                        else "wachtrij nieuws_doelen niet leesbaar (migratie gedraaid?)")
        return None

    if args.dry_run:
        print("== DROOGLOOP (er wordt niets gedraaid en niets gepost) ==")
        print(f"Account:    {account or '(geen — alleen-lezen)'}")
        print(f"Token:      {token_pad if token_pad else '(geen)'}"
              + ("" if not token_pad or token_pad.exists() else "  [ontbreekt!]"))
        print(f"Brief:      {brief.relative_to(ROOT)}  (blob {bhash})")
        print(f"Logbestand: {logpad.relative_to(ROOT)}")
        print(f"Timeout:    {args.timeout or '(geen)'} s")
        print(f"Lock:       data/locks/{label}.lock "
              f"({'BEZET — een ronde loopt al' if lock_bezet(label) else 'vrij'})")
        if args.alleen_bij_open_doelen:
            n = open_nieuws_doelen()
            print(f"Open doelen: {'onleesbaar' if n is None else n}")
        reden = overslaan_reden()
        print(f"Zou starten: {'NEE — ' + reden + ' (exit 0, geen claude)' if reden else 'ja'}")
        print("\nCommando:")
        print("  " + " ".join(shlex.quote(c) for c in cmd))
        return

    lock = neem_lock(label)
    if lock is None:
        print(f"[runner] Er loopt al een ronde van '{label}' (lock data/locks/{label}.lock "
              "bezet) — deze start wordt overgeslagen. Geen claude-sessie.")
        sys.exit(0)
    reden = overslaan_reden()
    if reden:
        print(f"[runner] {label}: {reden} — geen claude-sessie, geen logbestand.")
        sys.exit(0)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    voor = edit_log_telling(account)
    start = time.monotonic()
    linkedin_dood = False
    exit_code = None
    output = ""

    with open(logpad, "a", encoding="utf-8") as logfile:
        logfile.write(f"# Onbewaakte ronde — {label} · {ronde} · {datum}\n\n")
        logfile.write(f"- Brief: `{brief.relative_to(ROOT)}` (blob `{bhash}`)\n")
        logfile.write(f"- Account: `{account or '(geen — alleen-lezen)'}`\n")
        logfile.write(f"- Gestart: {datetime.datetime.now().isoformat(timespec='seconds')}\n\n")
        logfile.write("## Sessie-uitvoer\n\n```\n")
        logfile.flush()
        try:
            proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, bufsize=1)
        except FileNotFoundError:
            logfile.write(f"[runner] claude-CLI niet gevonden: {args.claude_bin}\n```\n")
            sys.exit(f"claude-CLI niet gevonden ({args.claude_bin}); geef --claude-bin.")
        try:
            output = stream_naar_log(proc, logfile)
            exit_code = proc.wait(timeout=args.timeout or None)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            exit_code = 124
            logfile.write(f"\n[runner] TIMEOUT na {args.timeout}s — sessie afgebroken.\n")
        logfile.write("\n```\n\n")

        duur = round(time.monotonic() - start, 1)
        na = edit_log_telling(account)
        oogst = max(0, na - voor)
        linkedin_dood = LINKEDIN_SESSIE_DOOD in output
        linkedin_rem = LINKEDIN_REM in output
        linkedin_blokkade = LINKEDIN_BLOKKADE in output

        logfile.write("## Runner-metadata\n\n")
        logfile.write(f"- Exit-code: {exit_code}\n")
        logfile.write(f"- Duur: {duur} s\n")
        logfile.write(f"- Oogst (edit_log-delta van `{account or '—'}`): {oogst}\n")
        if linkedin_dood:
            logfile.write(f"- ⚠ LinkedIn-sessie verlopen — RELAY aan de eigenaar: "
                          f"`{LINKEDIN_LOGIN_CMD}` (niet herproberen)\n")
        if linkedin_rem:
            logfile.write("- ⏳ LinkedIn-snelheidsrem weigerde (exit 75) — doelen met "
                          "vervolg=linkedin wachten op de volgende kans\n")
        if linkedin_blokkade:
            logfile.write("- ⛔ LinkedIn-blokkade: stroomonderbreker gesprongen — eigenaar: "
                          "account controleren, `python3 tools/linkedin/snelheidsrem.py "
                          "status`\n")
        logfile.write(f"- Beëindigd: "
                      f"{datetime.datetime.now().isoformat(timespec='seconds')}\n")

    run_record = {
        "datum": datum, "label": label, "account": account, "ronde": ronde,
        "brief": str(brief.relative_to(ROOT)), "brief_hash": bhash,
        "exit_code": exit_code, "duur_s": duur, "oogst": oogst,
        "linkedin_verlopen": linkedin_dood, "linkedin_rem": linkedin_rem,
        "linkedin_blokkade": linkedin_blokkade, "log": str(logpad.relative_to(ROOT)),
        "beeindigd": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    try:
        with open(RUNS_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(run_record, ensure_ascii=False) + "\n")
    except OSError:
        pass

    print(f"\n== ronde klaar: exit {exit_code}, {duur}s, oogst {oogst} "
          f"→ {logpad.relative_to(ROOT)} ==")
    if linkedin_blokkade:
        print("⛔ LINKEDIN-BLOKKADE in deze ronde — de stroomonderbreker staat; eigenaar: "
              "controleer het account (python3 tools/linkedin/snelheidsrem.py status).")
    if linkedin_dood:
        print(f"⚠ LINKEDIN-SESSIE VERLOPEN — geef dit commando aan de eigenaar en "
              f"herprobeer NIET:\n    {LINKEDIN_LOGIN_CMD}")
        sys.exit(0)  # geen retry-lus; de eigenaar logt opnieuw in
    sys.exit(0 if exit_code == 0 else 1)


if __name__ == "__main__":
    main()
