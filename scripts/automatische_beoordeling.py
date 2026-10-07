#!/usr/bin/env python3
"""Automatische beoordeling — de ene ronde (elk uur) waarin agents alles beslissen wat in het
propagandamodel binnenkomt of al staat (eigenaarsbesluit 2026-10-06: "ik ga niks handmatig
beoordelen"; "niks door mensen, alles door agents"; opgeschoond 2026-10-07: "gestroomlijnd,
duidelijk, en er mogen geen gaten vallen").

Elk stuk werk eindigt in een eindtoestand, met de reden in edit_log; een mens kan alles
terugdraaien (heropenen, intrekken), maar niemand hoeft iets te doen. Per ronde, in deze
volgorde (eerst repareren en controleren, dan beslissen, dan opruimen):

1. **Bronzoeker** (scripts/bronzoeker.py): een bron waar die ontbreekt of niet volstaat — een
   vervangend voorstel voor een voorgesteld argument met 'twijfel'/'klopt-niet', een steunend
   argument voor een verband zonder argument, een revisie van gemerged werk.
2. **A1 — bronchecker** (scripts/bronchecker.py): elk nieuw voorstel (ook wat stap 1 net
   indiende) en ``--max-controle`` gemergede argumenten die nooit gecontroleerd zijn, wat het
   nieuws toont eerst: haalt de bron op, zoekt het citaat letterlijk terug, en een model zegt
   of de bron de bewering draagt.
3. **Smaadtoets** (scripts/smaadtoets.py, Opus): claims over personen — feitelijk, gedragen
   door de bron, over de publieke rol? Dan smaad_hold eraf en de gewone poorten; zo niet,
   dan teruggekoppeld (stap 11 en 12). Eigen afwijzingen die een nieuw 'klopt'/'feitelijk'
   kregen, gaan terug naar 'voorgesteld' (heropenen).
4. **A2 — aanklager** (Opus, ``--a2-rondes-per-dag``, binnen de actieve uren) voor wat A1 én
   zo nodig de smaadtoets doorstond en een tegenstander nodig heeft (geen structuurfeit,
   ondergraving of bronrevisie).
5. **A7 — mergen** (``POST /api/arguments/<id>/auto_merge``, merge-service): de server checkt
   het predikaat zelf.
6. **Verificatie** (``POST /api/beoordeling/verificatie/<id>``): gemerged werk krijgt zijn
   status van het onafhankelijke A1-oordeel ('geverifieerd' / 'bronvermelding_nodig').
7. **Mechanismen** (scripts/mechanisme_toewijzer.py): een kandidaat-verband krijgt een
   mechanisme, of wordt afgewezen als het buiten het model valt.
8. **RfC's** (scripts/rfc_beoordeling.py): twee agents reviewen, de beoordeling beslist.
9. **Bronklassen** (scripts/bronklasse.py): twee onafhankelijke oordelen over de
   betrouwbaarheid en het onderwerp van een bron; bij verschil de voorzichtigste.
10. **Goedkeuren**: relaties en entiteiten met gecontroleerd bewijs gaan de graaf in.
11. **Opruimen** (status-PATCH door merge-service, altijd met reden): wat de bron niet draagt
    en niet te repareren is (na de poging van de bronzoeker), wat de smaadtoets terugkoppelde,
    en wat na ``--wachttijd-dagen`` (14) nog niet door de poort komt.
12. **Feitelijke versies**: wat de smaadtoets terugkoppelde, komt in zijn feitelijke vorm
    opnieuw binnen (en gaat weer langs alle controles).
13. **Archiveren** (scripts/archiveer_bronnen.py): ``--max-archief`` nieuwe bronnen naar de
    Wayback Machine, zodat de bronchecker ze ook later nog kan lezen.

Eén ronde tegelijk (lock). Logboek: data/automatische_beoordeling_log.jsonl.

Gebruik:
    python3 scripts/automatische_beoordeling.py --droog          # wat zou er gebeuren
    python3 scripts/automatische_beoordeling.py --once --json    # één ronde, echt
    python3 scripts/automatische_beoordeling.py --open-a2        # wachtrij van de aanklager
"""
from __future__ import annotations

import argparse
import datetime
import difflib
import fcntl
import json
import os
import re
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
import bronklasse  # noqa: E402
import bronzoeker  # noqa: E402
import mechanisme_toewijzer  # noqa: E402
import rfc_beoordeling  # noqa: E402
import smaadtoets  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
API = "http://127.0.0.1:5000"
MERGE_TOKEN = ROOT / "data" / "tokens" / "merge-service.token"
LOG_PATH = ROOT / "data" / "automatische_beoordeling_log.jsonl"
AUTO_MERGE_LOG = ROOT / "data" / "auto_merge_log.json"
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


def startmoment(*tijden: str | None) -> str | None:
    """Het laatste van de gegeven momenten (ISO-tekst, of None): een heropend argument krijgt
    een nieuwe wachttijd vanaf het heropenen."""
    gezet = [str(t) for t in tijden if t]
    return max(gezet) if gezet else None


def leeftijd_dagen(tijd: str | None, nu: datetime.datetime) -> float:
    if not tijd:
        return 0.0
    try:
        t = datetime.datetime.fromisoformat(str(tijd).replace("Z", "").split(".")[0])
    except ValueError:
        return 0.0
    return (nu - t).total_seconds() / 86400


def _zelfde(claim: str, ander: str) -> bool:
    """Spiegelt server._zelfde_bewering (difflib; de dedup-module laten we hier weg)."""
    return difflib.SequenceMatcher(None, claim or "", ander or "").ratio() >= 0.85


def a2_wachtrij(conn) -> list[dict]:
    """Voorgestelde argumenten die de bronchecker op 'klopt' zette en die nog op een
    tegenspraak-certificaat wachten: invloedsclaims, duiding, aspecten, theorie-argumenten en
    steunende reacties (agents doen alles, 2026-10-06). Niet: ondergravingen, neutrale
    structuurfeiten en bronrevisies (die hebben geen A2 nodig), en persoonsclaims zolang de
    smaadtoets ze niet 'feitelijk' bevond."""
    rijen = conn.execute("""
        SELECT a.*,
               (SELECT verdict FROM immuun_oordelen o WHERE o.argument_id = a.id
                  AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1,
               (SELECT created_at FROM immuun_oordelen o WHERE o.argument_id = a.id
                  AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1_op
        FROM arguments a
        WHERE a.status = 'voorgesteld' AND NOT a.vervangen AND COALESCE(a.smaad_hold, 0) = 0
          AND NOT EXISTS (SELECT 1 FROM immuun_oordelen o WHERE o.argument_id = a.id
                          AND o.fase = 'tegenspraak')
        ORDER BY a.id DESC""").fetchall()
    uit = []
    for a in rijen:
        if a["a1"] != "klopt":
            continue
        if (a["parent_argument_id"] is not None and a["stance"] == "contradicting"
                and (a["reasoning"] or "").strip()):
            continue  # ondergraving: eigen route
        personen, rtype = smaadtoets.personen_van(conn, a)
        if (a["parent_argument_id"] is None and a["stance"] == "supporting"
                and rtype in STRUCTUURTYPES
                and (a["property"] or "existence") in ("existence", "influence")):
            continue  # neutraal structuurfeit
        if a["reviseert_id"]:
            oud = conn.execute("SELECT claim, status, vervangen FROM arguments WHERE id = ?",
                               (a["reviseert_id"],)).fetchone()
            if (oud and not oud["vervangen"] and oud["status"] not in ("voorgesteld", "verworpen")
                    and _zelfde(a["claim"], oud["claim"])):
                continue  # bronrevisie
        if personen:
            toets = conn.execute("""SELECT verdict FROM smaad_toetsen WHERE argument_id = ?
                                    AND COALESCE(door, '') <> COALESCE(?, '')
                                    ORDER BY created_at DESC, id DESC LIMIT 1""",
                                 (a["id"], a["contributed_by"])).fetchone()
            if not toets or toets["verdict"] != "feitelijk":
                continue  # eerst de smaadtoets
        uit.append({k: a[k] for k in ("id", "claim", "relation_id", "entity_id",
                                       "contributed_by", "created_at", "a1", "a1_op")})
    return uit


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
    """Eén aanklager-ronde (Opus) als er argumenten op tegenspraak wachten."""
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
    meld(f"A2: aanklager-ronde voor {len(wachtrij)} argument(en)…")
    t0 = time.monotonic()
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       timeout=args.a2_timeout + 300)
    return {"gestart": True, "exit": r.returncode, "duur_s": round(time.monotonic() - t0),
            "wachtend": len(wachtrij)}


def stap_mergen(token, args, meld) -> dict:
    """A7 over alle voorgestelde argumenten: roots eerst, dan reacties. Schrijft de stand per
    argument (bucket + redenen) naar data/auto_merge_log.json, dat het toezicht op /beheer en
    de wachtrij op /overleg tonen (vroeger schreef scripts/auto_merge_service.py dat)."""
    conn = db()
    try:
        ids = [r["id"] for r in conn.execute("""
            SELECT id FROM arguments WHERE status = 'voorgesteld' AND NOT vervangen
            ORDER BY (parent_argument_id IS NOT NULL), id""")]
    finally:
        conn.close()
    tel = {"gemerged": 0, "buckets": {}}
    stand = {}
    nu = datetime.datetime.now().isoformat(timespec="seconds")
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
            bucket = "auto-gemerged"
        else:
            bucket = antwoord.get("bucket") or f"http-{status}"
            tel["buckets"][bucket] = tel["buckets"].get(bucket, 0) + 1
        stand[f"arg:{arg_id}"] = {"bucket": bucket, "redenen": antwoord.get("redenen") or [],
                                  "ts": nu}
    if not args.droog and not tel.get("uit"):
        tijdelijk = AUTO_MERGE_LOG.with_suffix(".tmp")
        tijdelijk.write_text(json.dumps(stand, ensure_ascii=False, indent=1), encoding="utf-8")
        tijdelijk.replace(AUTO_MERGE_LOG)
    meld(f"A7: {tel['gemerged']} argument(en) gemerged")
    return tel


def stap_bronzoeken(args, meld) -> dict:
    """Een bron waar die ontbreekt of niet volstaat: een vervangend voorstel, een steunend
    argument voor een verband zonder argument, of een revisie van gemerged werk."""
    if args.zonder_bronzoeker or args.max_zoek <= 0:
        return {"gestart": False, "reden": "uitgezet"}
    if not args.droog and not bronzoeker.DEFAULT_TOKEN.exists():
        return {"gestart": False, "reden": "geen token voor het account 'bronzoeker'"}
    return bronzoeker.draai(max_n=args.max_zoek, droog=args.droog, meld=meld)


def stap_heropenen(token, args, meld) -> dict:
    """Eigen afwijzingen terug naar 'voorgesteld' als een onafhankelijk oordeel de bron daarna
    toch bevestigt (de server checkt het predikaat zelf, ook de volgorde in de tijd)."""
    conn = db()
    try:
        ids = [r["id"] for r in conn.execute("""
            SELECT a.id FROM arguments a WHERE a.status = 'verworpen' AND NOT a.vervangen
              AND (SELECT verdict FROM immuun_oordelen o WHERE o.argument_id = a.id
                     AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC
                     LIMIT 1) = 'klopt'
              AND (SELECT l.reason FROM edit_log l WHERE l.table_name = 'arguments'
                     AND l.record_id = a.id AND l.action = 'disputed'
                     AND l.new_value LIKE '%verworpen%' ORDER BY l.id DESC LIMIT 1)
                  LIKE 'automatische beoordeling%'""")]
    finally:
        conn.close()
    tel = {"heropend": 0}
    for arg_id in ids:
        if args.droog:
            tel["heropend"] += 1
            continue
        status, antwoord = req("POST", f"/api/beoordeling/heropenen/{arg_id}", token)
        if status == 503:
            meld("Heropenen gestopt: automatische beoordeling staat uit")
            break
        if status == 200 and antwoord.get("heropend"):
            tel["heropend"] += 1
    meld(f"Heropend: {tel['heropend']} eigen afwijzing(en) met een bevestigde bron")
    return tel


def stap_verifieren(token, args, meld) -> dict:
    """Gemergede argumenten krijgen hun status van het onafhankelijke A1-oordeel."""
    conn = db()
    try:
        rijen = conn.execute("""
            SELECT a.id, a.status,
                   (SELECT verdict FROM immuun_oordelen o WHERE o.argument_id = a.id
                      AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC
                      LIMIT 1) AS a1
            FROM arguments a
            WHERE a.status IN ('ongecontroleerd', 'bronvermelding_nodig') AND NOT a.vervangen
            ORDER BY a.id""").fetchall()
    finally:
        conn.close()
    ids = [r["id"] for r in rijen
           if r["a1"] == "klopt" or (r["a1"] == "klopt-niet" and r["status"] == "ongecontroleerd")]
    tel = {"geverifieerd": 0, "bron_nodig": 0, "blijft": 0}
    for arg_id in ids:
        status, antwoord = req("GET" if args.droog else "POST",
                               f"/api/beoordeling/verificatie/{arg_id}", token)
        if status in (429, 503):
            meld(f"Verifiëren gestopt: {antwoord.get('error')}")
            break
        nieuw = (antwoord.get("nieuwe_status") if args.droog
                 else antwoord.get("status") if antwoord.get("gewijzigd") else None)
        tel[{"geverifieerd": "geverifieerd",
             "bronvermelding_nodig": "bron_nodig"}.get(nieuw, "blijft")] += 1
    meld(f"Verificatie: {tel['geverifieerd']} geverifieerd, {tel['bron_nodig']} naar "
         f"'bronvermelding_nodig' (bron draagt het niet)")
    return tel


def stap_smaadtoets(args, meld) -> dict:
    """De smaad-firewall door een agent: persoonsclaims met een bevestigde bron toetsen."""
    if args.max_smaad <= 0:
        return {"gestart": False, "reden": "uitgezet"}
    if not args.droog and not smaadtoets.DEFAULT_TOKEN.exists():
        return {"gestart": False, "reden": "geen token voor het account 'smaadtoets'"}
    return smaadtoets.draai(max_n=args.max_smaad, droog=args.droog, meld=meld)


def stap_smaad_vrijgeven(token, args, meld) -> dict:
    """smaad_hold eraf waar de smaadtoets 'feitelijk' zei en de bron de claim draagt."""
    conn = db()
    try:
        ids = [r["id"] for r in conn.execute("""
            SELECT a.id FROM arguments a WHERE COALESCE(a.smaad_hold, 0) = 1
              AND NOT a.vervangen AND a.status <> 'verworpen'
              AND (SELECT verdict FROM smaad_toetsen t WHERE t.argument_id = a.id
                     AND COALESCE(t.door, '') <> COALESCE(a.contributed_by, '')
                     ORDER BY t.created_at DESC, t.id DESC LIMIT 1) = 'feitelijk'""")]
    finally:
        conn.close()
    tel = {"vrijgegeven": 0}
    for arg_id in ids:
        if args.droog:
            tel["vrijgegeven"] += 1
            continue
        status, antwoord = req("POST", f"/api/beoordeling/smaad_vrijgeven/{arg_id}", token)
        if status == 503:
            break
        if status == 200 and antwoord.get("vrijgegeven"):
            tel["vrijgegeven"] += 1
    meld(f"Smaadtoets: {tel['vrijgegeven']} argument(en) van smaad_hold af (feitelijk)")
    return tel


def stap_mechanismen(args, meld) -> dict:
    """Kandidaat-verbanden krijgen een mechanisme van de mechanisme-toewijzer."""
    if args.max_mechanismen <= 0:
        return {"gestart": False, "reden": "uitgezet"}
    return mechanisme_toewijzer.draai(max_n=args.max_mechanismen, droog=args.droog, meld=meld)


def stap_rfc(token, args, meld) -> dict:
    """Open RfC's: reviews van twee agents, dan het besluit (aannemen/afwijzen)."""
    if args.max_rfc <= 0:
        return {"gestart": False, "reden": "uitgezet"}
    reviews = rfc_beoordeling.draai(droog=args.droog, max_n=args.max_rfc, meld=meld)
    conn = db()
    try:
        ids = [r["id"] for r in conn.execute(
            "SELECT id FROM voorstellen WHERE status = 'open' ORDER BY id")]
    finally:
        conn.close()
    tel = {"reviews": reviews, "aangenomen": 0, "afgewezen": 0, "open": 0, "blokkade": 0}
    for vid in ids:
        if args.droog:
            tel["open"] += 1
            continue
        status, antwoord = req("POST", f"/api/beoordeling/rfc/{vid}", token)
        if status == 503:
            break
        besluit = antwoord.get("besluit")
        if status == 200 and besluit == "geaccepteerd":
            tel["aangenomen"] += 1
        elif status == 200 and besluit == "afgewezen":
            tel["afgewezen"] += 1
        elif antwoord.get("blokkade"):
            tel["blokkade"] += 1
            meld(f"  ✗ RfC #{vid} niet uitvoerbaar: {antwoord['blokkade'][:160]}")
        else:
            tel["open"] += 1
    meld(f"RfC's: {tel['aangenomen']} aangenomen, {tel['afgewezen']} afgewezen, "
         f"{tel['open']} wachten nog")
    return tel


def stap_bronklassen(token, args, meld) -> dict:
    """Bronklassen door agents: twee onafhankelijke oordelen, bij verschil de voorzichtigste."""
    if args.max_bronklasse <= 0:
        return {"gestart": False, "reden": "uitgezet"}
    return bronklasse.draai(token=token, max_n=args.max_bronklasse, droog=args.droog,
                            meld=meld)


ARCHIEF_KLAAR = re.compile(r"Klaar: (\d+) bestaande snapshot\(s\) geregistreerd, (\d+) vers "
                           r"aangevraagd, (\d+) zonder snapshot, (\d+) door fout")


def stap_archiveren(args, meld) -> dict:
    """Nieuwe bronnen naar de Wayback Machine (bestaande snapshot registreren, anders een verse
    aanvragen), hooguit ``--max-archief`` per ronde: de bronchecker leest een verdwenen pagina
    uit het archief."""
    if args.max_archief <= 0 or args.droog:
        return {"gestart": False, "reden": "uitgezet" if args.max_archief <= 0 else "droog"}
    cmd = [sys.executable, str(ROOT / "scripts" / "archiveer_bronnen.py"), "--save",
           "--limit", str(args.max_archief), "--nieuwste-eerst", "--overslaan-dagen", "7"]
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=args.archief_timeout)
    except subprocess.TimeoutExpired:
        meld("Archief: time-out (de volgende ronde gaat verder)")
        return {"gestart": True, "timeout": True}
    m = ARCHIEF_KLAAR.search(r.stdout or "")
    tel = ({"gevonden": int(m[1]), "aangevraagd": int(m[2]), "zonder": int(m[3]),
            "fout": int(m[4])} if m else {"exit": r.returncode})
    meld(f"Archief: {tel}")
    return tel


FEITELIJKE_VERSIE = "Feitelijke versie van #{id} na de smaadtoets"


def feitelijke_versie(orig: dict, citaties: list[dict], herformulering: str, reden: str) -> dict:
    """De body van een nieuw argument met de feitelijke formulering die de smaadtoets gaf:
    hetzelfde doel, dezelfde stance en dezelfde bronnen (de controles beginnen opnieuw)."""
    body = {"stance": orig["stance"], "claim": herformulering.strip(),
            "reasoning": f"{FEITELIJKE_VERSIE.format(id=orig['id'])}: {reden}"[:1500],
            "negeer_duplicaten": True,
            "citations": [{k: c[k] for k in ("source_id", "quote", "methode") if c.get(k)}
                          for c in citaties]}
    if orig.get("parent_argument_id"):
        body["parent_argument_id"] = orig["parent_argument_id"]
    else:
        for kolom in ("relation_id", "entity_id", "role_id", "mechanism_id",
                      "emergent_effect_id"):
            if orig.get(kolom):
                body[kolom] = orig[kolom]
        if orig.get("property"):
            body["property"] = orig["property"]
        if orig.get("property_value") is not None:
            body["property_value"] = orig["property_value"]
    return body


def stap_feitelijke_versies(args, meld) -> dict:
    """Terugkoppelen tot het eind: wat de smaadtoets 'niet feitelijk' bevond en verworpen is,
    komt met de feitelijke formulering die de bron wél draagt opnieuw binnen (account
    'bronzoeker', dezelfde bronnen), en gaat weer langs bron-check, smaadtoets en aanklager."""
    if args.droog or not bronzoeker.DEFAULT_TOKEN.exists():
        return {"ingediend": 0, "reden": "droog of geen token"}
    token = bronzoeker.DEFAULT_TOKEN.read_text().strip()
    conn = db()
    try:
        rijen = conn.execute("""
            SELECT a.*, t.herformulering, t.reden AS smaad_reden FROM arguments a
            JOIN smaad_toetsen t ON t.id = (
                SELECT t2.id FROM smaad_toetsen t2 WHERE t2.argument_id = a.id
                  AND COALESCE(t2.door, '') <> COALESCE(a.contributed_by, '')
                ORDER BY t2.created_at DESC, t2.id DESC LIMIT 1)
            WHERE a.status = 'verworpen' AND NOT a.vervangen
              AND t.verdict = 'niet_feitelijk' AND TRIM(COALESCE(t.herformulering, '')) <> ''
            ORDER BY a.id""").fetchall()
        werk = []
        for r in rijen:
            merk = FEITELIJKE_VERSIE.format(id=r["id"]) + "%"
            if conn.execute("SELECT 1 FROM arguments WHERE reasoning LIKE ? LIMIT 1",
                            (merk,)).fetchone():
                continue  # al opnieuw ingediend
            citaties = [dict(c) for c in conn.execute(
                "SELECT source_id, quote, methode FROM citations WHERE argument_id = ?",
                (r["id"],))]
            if citaties:
                werk.append(feitelijke_versie(dict(r), citaties, r["herformulering"],
                                              r["smaad_reden"] or ""))
    finally:
        conn.close()
    tel = {"ingediend": 0, "fouten": 0}
    for body in werk:
        status, antwoord = req("POST", "/api/arguments", token, body)
        if status == 201:
            tel["ingediend"] += 1
        else:
            tel["fouten"] += 1
            meld(f"  ✗ feitelijke versie niet ingediend ({status}): {antwoord.get('error')}")
    meld(f"Smaadtoets: {tel['ingediend']} feitelijke versie(s) opnieuw ingediend")
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


def motivatie_voor(a: dict, *, wacht_a2, wacht_zoeker, pogingen, wachttijd, nu):
    """Het opruimbesluit voor één voorgesteld argument → (motivatie of None, waarop het nog
    wacht of None). Eerst repareren, dan beslissen: wat de bron niet (volledig) draagt, krijgt
    eerst een poging van de bronzoeker (als die het kan repareren) en wordt daarna meteen
    verworpen — met de vervanger erbij, of de reden waarom er geen is. Dode wachttijd is er
    alleen nog voor wat op de aanklager wacht (A2-budget)."""
    detail = (a["a1_detail"] or "").replace("[bronchecker] ", "").strip()
    if a["smaad"] == "niet_feitelijk":
        return (f"{REDEN}: teruggekoppeld door de smaadtoets — {a['smaad_reden']}"
                + (f" Feitelijk zou zijn: {a['smaad_herformulering']}"
                   if a["smaad_herformulering"] else "")), None
    if a["a1"] in ("klopt-niet", "twijfel"):
        if a["id"] in wacht_zoeker:
            return None, "bronzoeker"
        poging = pogingen.get(str(a["id"])) or {}
        if poging.get("uitkomst") == "gevonden" and poging.get("nieuw_id"):
            return (f"{REDEN}: vervangen door #{poging['nieuw_id']} — de bronzoeker vond een "
                    f"bron die het wel draagt (de bronchecker: {detail})"), None
        if a["parent_argument_id"] and a["a1"] == "klopt-niet":
            return f"{REDEN}: het bezwaar houdt geen stand — {detail}", None
        waarom = ("de bron draagt de bewering niet" if a["a1"] == "klopt-niet"
                  else "de bron bevestigt het niet volledig")
        zonder = ("; de bronzoeker vond geen betere bron" if poging.get("uitkomst") == "niets"
                  else "")
        return f"{REDEN}: {waarom} — {detail}{zonder}", None
    if a["id"] in wacht_a2:
        if leeftijd_dagen(startmoment(a["a1_op"], a["heropend_op"]), nu) >= wachttijd:
            return (f"{REDEN}: kreeg binnen {wachttijd} dagen geen tegenspraak-certificaat "
                    "— opgeschoond"), None
        return None, "aanklager"
    if leeftijd_dagen(startmoment(a["created_at"], a["heropend_op"]), nu) >= wachttijd:
        waarom = {"klopt": ("de aanklager viel het aan (tegenbewijs of een ondergraving)"
                            if a["a2"] == "aangevallen"
                            else "het komt (nog) niet door de immuunpoort")}.get(
            a["a1"], "het valt buiten wat automatisch te controleren is")
        return (f"{REDEN}: na {wachttijd} dagen niet te bevestigen — {waarom}; "
                "opgeschoond"), None
    return None, None


def stap_opruimen(token, args, meld) -> dict:
    """Verwerp wat aantoonbaar niet klopt of na de wachttijd niet door de poort komt."""
    nu = datetime.datetime.now()
    tel = {"verworpen": 0, "afgewezen": 0, "wacht_op_a2": 0, "wacht_op_bronzoeker": 0}
    zoeker_aan = not args.zonder_bronzoeker and args.max_zoek > 0
    pogingen = bronzoeker.laad_pogingen() if zoeker_aan else {}
    conn = db()
    try:
        args_rijen = [dict(r) for r in conn.execute("""
            SELECT a.id, a.created_at, a.parent_argument_id, a.contributed_by,
                   (SELECT verdict FROM immuun_oordelen o WHERE o.argument_id = a.id
                      AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1,
                   (SELECT detail FROM immuun_oordelen o WHERE o.argument_id = a.id
                      AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1_detail,
                   (SELECT created_at FROM immuun_oordelen o WHERE o.argument_id = a.id
                      AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC LIMIT 1) AS a1_op,
                   (SELECT verdict FROM smaad_toetsen t WHERE t.argument_id = a.id
                      AND COALESCE(t.door, '') <> COALESCE(a.contributed_by, '')
                      ORDER BY t.created_at DESC, t.id DESC LIMIT 1) AS smaad,
                   (SELECT reden FROM smaad_toetsen t WHERE t.argument_id = a.id
                      AND COALESCE(t.door, '') <> COALESCE(a.contributed_by, '')
                      ORDER BY t.created_at DESC, t.id DESC LIMIT 1) AS smaad_reden,
                   (SELECT herformulering FROM smaad_toetsen t WHERE t.argument_id = a.id
                      AND COALESCE(t.door, '') <> COALESCE(a.contributed_by, '')
                      ORDER BY t.created_at DESC, t.id DESC LIMIT 1) AS smaad_herformulering,
                   (SELECT verdict FROM immuun_oordelen o WHERE o.argument_id = a.id
                      AND o.fase = 'tegenspraak' ORDER BY o.id DESC LIMIT 1) AS a2,
                   (SELECT MAX(l.created_at) FROM edit_log l WHERE l.table_name = 'arguments'
                      AND l.record_id = a.id
                      AND l.reason LIKE 'automatische beoordeling: heropend%') AS heropend_op
            FROM arguments a WHERE a.status = 'voorgesteld' AND NOT a.vervangen""")]
        wacht_a2 = {r["id"]: r for r in a2_wachtrij(conn)}
        # Nog niet door de bronchecker bekeken (boven --max-bron): eerst controleren
        ongecontroleerd = {r["id"] for r in bronchecker.kandidaten(conn)}
        # Wat de bronzoeker nog moet proberen: eerst repareren, dan beslissen
        wacht_zoeker = bronzoeker.wacht_op_zoeker(conn, pogingen) if zoeker_aan else set()
        verband_wacht = ({r["relation_id"] for r in bronzoeker.verbanden_zonder_argument(conn)
                          if (pogingen.get(f"relatie:{r['relation_id']}") or {}).get(
                              "uitkomst") in (None, "fout")} if zoeker_aan else set())
        # Doelen waarvan het bewijs nog in behandeling is: niet afwijzen
        bezig = ongecontroleerd | set(wacht_a2) | wacht_zoeker
        doelen_bezig = {("relations", r["relation_id"]) for r in conn.execute(
            f"SELECT relation_id FROM arguments WHERE id IN ({','.join('?' * len(bezig))})",
            list(bezig)) if r["relation_id"]} if bezig else set()
        doelen_bezig |= {("relations", rid) for rid in verband_wacht}
    finally:
        conn.close()
    for a in args_rijen:
        if a["id"] in ongecontroleerd and a["smaad"] != "niet_feitelijk":
            continue
        motivatie, wacht = motivatie_voor(a, wacht_a2=wacht_a2, wacht_zoeker=wacht_zoeker,
                                          pogingen=pogingen, wachttijd=args.wachttijd_dagen,
                                          nu=nu)
        if wacht == "aanklager":
            tel["wacht_op_a2"] += 1
        elif wacht == "bronzoeker":
            tel["wacht_op_bronzoeker"] += 1
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
                SELECT t.id, COALESCE(
                    (SELECT MAX(created_at) FROM edit_log l WHERE l.table_name = ?
                       AND l.record_id = t.id
                       AND l.reason LIKE 'automatische beoordeling: mechanisme%'),
                    (SELECT MIN(created_at) FROM edit_log l WHERE l.table_name = ?
                       AND l.record_id = t.id AND l.action = 'created')) AS aangemaakt
                FROM {tabel} t WHERE t.status = 'voorgesteld' AND NOT t.vervangen
                {"AND t.mechanism_id IS NOT NULL" if tabel == "relations" else ""}""",
                (tabel, tabel))]  # noqa: S608 - vaste tabelnaam
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
         f"relatie(s)/entiteit(en) afgewezen; {tel['wacht_op_a2']} wachten op de aanklager, "
         f"{tel['wacht_op_bronzoeker']} op de bronzoeker")
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
    # 1. Repareren: een bron waar die ontbreekt of niet volstaat (wat de bronzoeker indient,
    #    controleert stap 2 nog in dezelfde ronde)
    uitkomst["bronzoeker"] = stap_bronzoeken(args, meld)
    # 2. A1: elk nieuw voorstel, en gemerged werk dat nooit gecontroleerd is (nieuws eerst)
    uitkomst["a1"] = bronchecker.draai(max_n=args.max_bron, droog=args.droog,
                                       parallel=args.parallel, meld=meld)
    uitkomst["a1_controle"] = bronchecker.draai(max_n=args.max_controle, droog=args.droog,
                                                parallel=args.parallel, modus="controle",
                                                meld=meld)
    # 3. Smaad-firewall door een agent, en eigen afwijzingen terug na een nieuw 'klopt'
    uitkomst["smaadtoets"] = stap_smaadtoets(args, meld)
    uitkomst["smaad_vrijgegeven"] = stap_smaad_vrijgeven(token, args, meld)
    uitkomst["heropend"] = stap_heropenen(token, args, meld)
    # 4. A2: de aanklager
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
    # 5–10. Beslissen
    uitkomst["a7"] = stap_mergen(token, args, meld)
    uitkomst["verificatie"] = stap_verifieren(token, args, meld)
    uitkomst["mechanismen"] = stap_mechanismen(args, meld)
    uitkomst["rfc"] = stap_rfc(token, args, meld)
    uitkomst["bronklassen"] = stap_bronklassen(token, args, meld)
    uitkomst["goedgekeurd"] = stap_goedkeuren(token, args, meld)
    # 11–12. Opruimen, en wat de smaadtoets terugkoppelde in zijn feitelijke vorm opnieuw
    if not args.zonder_opruimen:
        uitkomst["opgeruimd"] = stap_opruimen(token, args, meld)
    uitkomst["feitelijke_versies"] = stap_feitelijke_versies(args, meld)
    # 13. Nieuwe bronnen archiveren (zodat de bronchecker ze later nog kan lezen)
    uitkomst["archief"] = stap_archiveren(args, meld)
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
    ap.add_argument("--max-controle", type=int, default=60,
                    help="hooguit zoveel gemergede, nooit gecontroleerde argumenten per ronde")
    ap.add_argument("--max-zoek", type=int, default=8,
                    help="hooguit zoveel argumenten zonder (goede) bron per ronde (bronzoeker)")
    ap.add_argument("--zonder-bronzoeker", action="store_true", help="geen bronnen zoeken")
    ap.add_argument("--max-smaad", type=int, default=20,
                    help="hooguit zoveel smaadtoetsen per ronde (0 = uit)")
    ap.add_argument("--max-mechanismen", type=int, default=12,
                    help="hooguit zoveel kandidaat-verbanden per ronde (0 = uit)")
    ap.add_argument("--max-rfc", type=int, default=3,
                    help="hooguit zoveel open RfC's per ronde laten reviewen (0 = uit)")
    ap.add_argument("--max-bronklasse", type=int, default=160,
                    help="hooguit zoveel bronnen per ronde classificeren (0 = uit)")
    ap.add_argument("--max-archief", type=int, default=10,
                    help="hooguit zoveel bronnen per ronde archiveren (0 = uit)")
    ap.add_argument("--archief-timeout", type=int, default=900)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--zonder-a2", action="store_true", help="geen aanklager-ronde starten")
    ap.add_argument("--a2-rondes-per-dag", type=int, default=4)
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
