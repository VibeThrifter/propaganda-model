#!/usr/bin/env python3
"""Automatische beoordeling — één beoordelingsronde zonder mens (eigenaarsbesluit
2026-10-06: "ik ga niks handmatig beoordelen").

Wat agents voorstellen ('voorgesteld') wordt hier beslist, via de bestaande poorten:

1. **A1 — bronchecker** (scripts/bronchecker.py): elke voorgestelde evidentiële root en
   elke ondergraving wordt onafhankelijk tegen de echte bron gecontroleerd.
2. **A2 — aanklager**: staan er invloedsclaims klaar die de bronchecker op 'klopt' zette
   maar die nog geen tegenspraak hadden, dan één ronde van de aanklager-agent (Opus) —
   hooguit ``--a2-rondes-per-dag`` per dag en alleen binnen de actieve uren. Neutrale
   structuurfeiten hebben geen A2 nodig.
3. **A7 — mergen** via ``POST /api/arguments/<id>/auto_merge`` (merge-service): de server
   checkt het predikaat zelf (A1 ∧ A2 ∧ dedup ∧ citatiepoort ∧ smaad-firewall, met de twee
   routes van 2026-10-06 voor structuurfeiten en ondergravingen).
4. **Relaties en entiteiten** met gecontroleerd bewijs gaan de graaf in via
   ``POST /api/beoordeling/autokeur/<tabel>/<id>`` (entiteiten eerst).
5. **Opruimen** (status-PATCH door merge-service, altijd met reden, terug te draaien met
   heropenen/intrekken):
   - wat de bronchecker 'klopt-niet' gaf: de bron draagt de bewering niet, of het bezwaar
     houdt geen stand → verworpen;
   - wat na de wachttijd (``--wachttijd-dagen``, standaard 14) nog niet door de poort komt
     → verworpen (argumenten) of afgewezen (relaties, entiteiten). Een argument dat alleen
     nog op een A2-ronde wacht, krijgt die wachttijd vanaf zijn A1-oordeel.
   Nooit opgeruimd: kandidaat-relaties zonder mechanisme (incubatie, bewust) en RfC's.

Eén ronde tegelijk (lock). Logboek: data/automatische_beoordeling_log.jsonl.

Gebruik:
    python3 scripts/automatische_beoordeling.py --droog          # wat zou er gebeuren
    python3 scripts/automatische_beoordeling.py --once --json    # één ronde, echt
    python3 scripts/automatische_beoordeling.py --open-a2        # wachtrij van de aanklager
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import bronchecker  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
API = "http://127.0.0.1:5000"
MERGE_TOKEN = ROOT / "data" / "tokens" / "merge-service.token"
LOG_PATH = ROOT / "data" / "automatische_beoordeling_log.jsonl"
LOCK_PATH = ROOT / "data" / "locks" / "automatische-beoordeling.lock"
RUNS_JSONL = ROOT / "data" / "agent_runs.jsonl"
CLAUDE = shutil.which("claude") or "/usr/local/bin/claude"
CAFFEINATE = shutil.which("caffeinate")
# Spiegelt server.BEOORDELING_STRUCTUURTYPES (neutrale structuurfeiten: geen A2 nodig)
STRUCTUURTYPES = ("personeel", "dienstverband", "bestuurder", "adviseur", "woordvoerder_van",
                  "lidmaatschap", "eigendom", "draaideur")
REDEN = "automatische beoordeling"


# ------------------------------------------------------------------ helpers
def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def req(method, pad, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + pad, data=data, method=method,
                               headers={"Authorization": f"Bearer {token}",
                                        "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            tekst = resp.read().decode()
            return resp.status, (json.loads(tekst) if tekst else {})
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except json.JSONDecodeError:
            return e.code, {}


def leeftijd_dagen(tijd: str | None, nu: datetime.datetime) -> float:
    if not tijd:
        return 0.0
    try:
        t = datetime.datetime.fromisoformat(str(tijd).replace("Z", "").split(".")[0])
    except ValueError:
        return 0.0
    return (nu - t).total_seconds() / 86400


def a2_wachtrij(conn) -> list[dict]:
    """Voorgestelde invloedsclaims die de bronchecker op 'klopt' zette en die nog geen
    tegenspraak-certificaat hebben (en geen persoon raken: die merget A7 nooit)."""
    rijen = conn.execute(f"""
        SELECT a.id, a.claim, a.relation_id, a.entity_id, a.contributed_by, a.created_at,
               (SELECT verdict FROM immuun_oordelen o WHERE o.argument_id = a.id
                  AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1,
               (SELECT created_at FROM immuun_oordelen o WHERE o.argument_id = a.id
                  AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1_op
        FROM arguments a
        WHERE a.status = 'voorgesteld' AND NOT a.vervangen AND a.parent_argument_id IS NULL
          AND a.stance IN ('supporting', 'contradicting')
          AND COALESCE(a.property, 'existence') IN ('existence', 'influence')
          AND (a.relation_id IS NOT NULL OR a.entity_id IS NOT NULL)
          AND NOT EXISTS (SELECT 1 FROM immuun_oordelen o WHERE o.argument_id = a.id
                          AND o.fase = 'tegenspraak')
          AND NOT (a.stance = 'supporting' AND a.relation_id IN (
                SELECT id FROM relations WHERE relation_type IN
                ({",".join("?" * len(STRUCTUURTYPES))})))
          AND NOT EXISTS (SELECT 1 FROM relations r JOIN entities e
                          ON e.id IN (r.source_id, r.target_id)
                          WHERE r.id = a.relation_id AND e.type = 'persoon')
          AND NOT EXISTS (SELECT 1 FROM entities e WHERE e.id = a.entity_id
                          AND e.type = 'persoon')
        ORDER BY a.id DESC""", STRUCTUURTYPES).fetchall()  # noqa: S608 - placeholders
    return [dict(r) for r in rijen if r["a1"] == "klopt"]


def rondes_vandaag(label: str) -> int:
    vandaag = datetime.date.today().isoformat()
    try:
        regels = RUNS_JSONL.read_text(encoding="utf-8").splitlines()[-2000:]
    except OSError:
        return 0
    n = 0
    for regel in regels:
        try:
            r = json.loads(regel)
        except ValueError:
            continue
        if r.get("label") == label and r.get("datum") == vandaag:
            n += 1
    return n


# ------------------------------------------------------------------ stappen
def stap_a2(wachtrij, args, meld) -> dict:
    """Eén aanklager-ronde (Opus) als er invloedsclaims op tegenspraak wachten."""
    if not wachtrij:
        return {"gestart": False, "reden": "niets wacht op tegenspraak"}
    if args.zonder_a2:
        return {"gestart": False, "reden": "uitgezet (--zonder-a2)", "wachtend": len(wachtrij)}
    uur = datetime.datetime.now().hour
    van, tot = args.actieve_uren
    if not (van <= uur < tot):
        return {"gestart": False, "reden": "buiten de actieve uren", "wachtend": len(wachtrij)}
    if rondes_vandaag("aanklager-agent") >= args.a2_rondes_per_dag:
        return {"gestart": False, "reden": "dagbudget aanklager bereikt",
                "wachtend": len(wachtrij)}
    if args.droog:
        return {"gestart": False, "reden": "droog", "wachtend": len(wachtrij)}
    cmd = [sys.executable, str(ROOT / "scripts" / "agent_runner.py"),
           "--agent", "aanklager-agent", "--label", "aanklager-agent",
           "--brief", "missies/aanklager_brief.md", "--skip-permissions",
           "--claude-bin", CLAUDE, "--timeout", str(args.a2_timeout),
           "--model", "opus", "--effort", "high"]
    if CAFFEINATE:
        cmd = [CAFFEINATE, "-i", *cmd]
    meld(f"A2: aanklager-ronde voor {len(wachtrij)} invloedsclaim(s)…")
    t0 = time.monotonic()
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       timeout=args.a2_timeout + 300)
    return {"gestart": True, "exit": r.returncode, "duur_s": round(time.monotonic() - t0),
            "wachtend": len(wachtrij)}


def stap_mergen(token, args, meld) -> dict:
    """A7 over alle voorgestelde argumenten: roots eerst, dan reacties."""
    conn = db()
    try:
        ids = [r["id"] for r in conn.execute("""
            SELECT id FROM arguments WHERE status = 'voorgesteld' AND NOT vervangen
            ORDER BY (parent_argument_id IS NOT NULL), id""")]
    finally:
        conn.close()
    tel = {"gemerged": 0, "buckets": {}}
    for arg_id in ids:
        if args.droog:
            continue
        status, antwoord = req("POST", f"/api/arguments/{arg_id}/auto_merge", token)
        if status == 503:
            meld("A7: auto-merge staat uit (PROPAGANDA_AUTO_MERGE=0)")
            tel["uit"] = True
            break
        if status == 200 and antwoord.get("merged"):
            tel["gemerged"] += 1
        else:
            bucket = antwoord.get("bucket") or f"http-{status}"
            tel["buckets"][bucket] = tel["buckets"].get(bucket, 0) + 1
    meld(f"A7: {tel['gemerged']} argument(en) gemerged")
    return tel


def stap_goedkeuren(token, args, meld) -> dict:
    """Relaties en entiteiten met gecontroleerd bewijs: entiteiten eerst, dan relaties."""
    tel = {"entities": 0, "relations": 0}
    for tabel in ("entities", "relations"):
        conn = db()
        try:
            ids = [r["id"] for r in conn.execute(f"""
                SELECT id FROM {tabel} WHERE status = 'voorgesteld' AND NOT vervangen
                ORDER BY id""")]  # noqa: S608 - vaste tabelnaam
        finally:
            conn.close()
        for rid in ids:
            methode = "GET" if args.droog else "POST"
            status, antwoord = req(methode, f"/api/beoordeling/autokeur/{tabel}/{rid}", token)
            if status in (429, 503):
                meld(f"Goedkeuren gestopt: {antwoord.get('error')}")
                return tel
            if (args.droog and antwoord.get("toegestaan")) or antwoord.get("goedgekeurd"):
                tel[tabel] += 1
    meld(f"Goedgekeurd: {tel['entities']} entiteit(en), {tel['relations']} relatie(s)")
    return tel


def stap_opruimen(token, args, meld) -> dict:
    """Verwerp wat aantoonbaar niet klopt of na de wachttijd niet door de poort komt."""
    nu = datetime.datetime.now()
    tel = {"verworpen": 0, "afgewezen": 0, "wacht_op_a2": 0}
    conn = db()
    try:
        args_rijen = [dict(r) for r in conn.execute("""
            SELECT a.id, a.created_at, a.parent_argument_id, a.contributed_by,
                   (SELECT verdict FROM immuun_oordelen o WHERE o.argument_id = a.id
                      AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1,
                   (SELECT detail FROM immuun_oordelen o WHERE o.argument_id = a.id
                      AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1_detail,
                   (SELECT created_at FROM immuun_oordelen o WHERE o.argument_id = a.id
                      AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1_op
            FROM arguments a WHERE a.status = 'voorgesteld' AND NOT a.vervangen""")]
        wacht_a2 = {r["id"]: r for r in a2_wachtrij(conn)}
        # Nog niet door de bronchecker bekeken (boven --max-bron): eerst controleren
        ongecontroleerd = {r["id"] for r in bronchecker.kandidaten(conn)}
        # Doelen waarvan het bewijs nog in behandeling is: niet afwijzen
        bezig = ongecontroleerd | set(wacht_a2)
        doelen_bezig = {("relations", r["relation_id"]) for r in conn.execute(
            f"SELECT relation_id FROM arguments WHERE id IN ({','.join('?' * len(bezig))})",
            list(bezig)) if r["relation_id"]} if bezig else set()
    finally:
        conn.close()
    for a in args_rijen:
        motivatie = None
        if a["id"] in ongecontroleerd:
            continue
        detail = (a["a1_detail"] or "").replace("[bronchecker] ", "").strip()
        if a["a1"] == "klopt-niet":
            motivatie = (f"{REDEN}: het bezwaar houdt geen stand — {detail}"
                         if a["parent_argument_id"] else
                         f"{REDEN}: de bron draagt de bewering niet — {detail}")
        elif a["id"] in wacht_a2:
            if leeftijd_dagen(a["a1_op"], nu) >= args.wachttijd_dagen:
                motivatie = (f"{REDEN}: kreeg binnen {args.wachttijd_dagen} dagen geen "
                             "tegenspraak-certificaat — opgeschoond")
            else:
                tel["wacht_op_a2"] += 1
        elif leeftijd_dagen(a["created_at"], nu) >= args.wachttijd_dagen:
            waarom = {"twijfel": f"de bron bevestigt het niet volledig ({detail})",
                      "klopt": "het komt (nog) niet door de immuunpoort"}.get(
                a["a1"], "het valt buiten wat automatisch te controleren is")
            motivatie = (f"{REDEN}: na {args.wachttijd_dagen} dagen niet te bevestigen — "
                         f"{waarom}; opgeschoond")
        if not motivatie:
            continue
        if not args.droog:
            status, antwoord = req("PATCH", f"/api/arguments/{a['id']}/status", token,
                                   {"status": "verworpen", "motivatie": motivatie[:900]})
            if status != 200:
                meld(f"  ✗ #{a['id']} verwerpen: {antwoord.get('error')}")
                continue
        tel["verworpen"] += 1
    # Relaties en entiteiten die na de wachttijd nog niet goedkeurbaar zijn (geen kandidaten)
    for tabel in ("relations", "entities"):
        conn = db()
        try:
            rijen = [dict(r) for r in conn.execute(f"""
                SELECT t.id, (SELECT MIN(created_at) FROM edit_log l WHERE l.table_name = ?
                                AND l.record_id = t.id AND l.action = 'created') AS aangemaakt
                FROM {tabel} t WHERE t.status = 'voorgesteld' AND NOT t.vervangen
                {"AND t.mechanism_id IS NOT NULL" if tabel == "relations" else ""}""",
                (tabel,))]  # noqa: S608 - vaste tabelnaam
        finally:
            conn.close()
        for rij in rijen:
            if leeftijd_dagen(rij["aangemaakt"], nu) < args.wachttijd_dagen:
                continue
            if (tabel, rij["id"]) in doelen_bezig:
                continue
            if tabel == "entities":
                conn = db()
                try:
                    hangt = conn.execute("""SELECT 1 FROM relations WHERE (source_id = ? OR
                        target_id = ?) AND status = 'voorgesteld' AND NOT vervangen LIMIT 1""",
                                         (rij["id"], rij["id"])).fetchone()
                finally:
                    conn.close()
                if hangt:
                    continue  # haar relatie is nog in behandeling (of een kandidaat)
            _s, check = req("GET", f"/api/beoordeling/autokeur/{tabel}/{rij['id']}", token)
            if check.get("toegestaan"):
                continue
            redenen = "; ".join(check.get("redenen") or [])[:500]
            motivatie = (f"{REDEN}: na {args.wachttijd_dagen} dagen niet goedkeurbaar "
                         f"({redenen}); opgeschoond")
            if not args.droog:
                status, antwoord = req("PATCH", f"/api/{tabel}/{rij['id']}/status", token,
                                       {"status": "afgewezen", "motivatie": motivatie})
                if status != 200:
                    meld(f"  ✗ {tabel} #{rij['id']} afwijzen: {antwoord.get('error')}")
                    continue
            tel["afgewezen"] += 1
    meld(f"Opgeruimd: {tel['verworpen']} argument(en) verworpen, {tel['afgewezen']} "
         f"relatie(s)/entiteit(en) afgewezen; {tel['wacht_op_a2']} wachten op de aanklager")
    return tel


# ------------------------------------------------------------------ ronde
def ronde(args, meld=print) -> dict:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock = open(LOCK_PATH, "a+")
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        meld("Er loopt al een beoordelingsronde — overgeslagen.")
        return {"overgeslagen": True}
    token = MERGE_TOKEN.read_text().strip() if MERGE_TOKEN.exists() else None
    if not token:
        raise SystemExit(f"Token niet gevonden: {MERGE_TOKEN}")
    t0 = time.monotonic()
    uitkomst = {"start": datetime.datetime.now().isoformat(timespec="seconds"),
                "droog": bool(args.droog)}
    uitkomst["a1"] = bronchecker.draai(max_n=args.max_bron, droog=args.droog,
                                       parallel=args.parallel, meld=meld)
    # Twijfelgevallen van bronchecker v1 nog één keer met v2 (eigen oordeel herzien)
    uitkomst["a1_herzien"] = bronchecker.draai(max_n=args.max_bron, droog=args.droog,
                                               parallel=args.parallel, herzien=True, meld=meld)
    conn = db()
    try:
        wachtrij = a2_wachtrij(conn)
    finally:
        conn.close()
    uitkomst["a2"] = stap_a2(wachtrij, args, meld)
    if uitkomst["a2"].get("gestart"):
        # Wat de aanklager aanviel of indiende, kan nu zelf een A1 nodig hebben
        uitkomst["a1_na_a2"] = bronchecker.draai(max_n=args.max_bron, droog=args.droog,
                                                 parallel=args.parallel, meld=meld)
    uitkomst["a7"] = stap_mergen(token, args, meld)
    uitkomst["goedgekeurd"] = stap_goedkeuren(token, args, meld)
    if not args.zonder_opruimen:
        uitkomst["opgeruimd"] = stap_opruimen(token, args, meld)
    uitkomst["gemerged"] = uitkomst["a7"]["gemerged"]
    uitkomst["duur_s"] = round(time.monotonic() - t0)
    if not args.droog:
        with open(LOG_PATH, "a", encoding="utf-8") as log:
            log.write(json.dumps(uitkomst, ensure_ascii=False) + "\n")
    return uitkomst


def parse_uren(spec):
    van, _, tot = spec.partition("-")
    return int(van), int(tot)


def main():
    ap = argparse.ArgumentParser(description="Automatische beoordeling (eigenaarsbesluit 2026-10-06)")
    ap.add_argument("--once", action="store_true", help="één ronde (standaard)")
    ap.add_argument("--droog", action="store_true", help="niets schrijven")
    ap.add_argument("--json", action="store_true", help="eindig met één JSON-regel")
    ap.add_argument("--open-a2", action="store_true",
                    help="print de argumenten die op een tegenspraak-certificaat wachten")
    ap.add_argument("--max-bron", type=int, default=80, help="hooguit zoveel A1-checks per ronde")
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--zonder-a2", action="store_true", help="geen aanklager-ronde starten")
    ap.add_argument("--a2-rondes-per-dag", type=int, default=2)
    ap.add_argument("--a2-timeout", type=int, default=2700)
    ap.add_argument("--actieve-uren", type=parse_uren, default=(8, 22))
    ap.add_argument("--wachttijd-dagen", type=int, default=14)
    ap.add_argument("--zonder-opruimen", action="store_true")
    args = ap.parse_args()
    if args.open_a2:
        conn = db()
        try:
            print(json.dumps(a2_wachtrij(conn), ensure_ascii=False, indent=1))
        finally:
            conn.close()
        return
    uitkomst = ronde(args)
    if args.json:
        print(json.dumps(uitkomst, ensure_ascii=False))
    else:
        print(json.dumps(uitkomst, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
