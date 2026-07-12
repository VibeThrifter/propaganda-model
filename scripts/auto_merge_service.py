#!/usr/bin/env python3
"""Auto-merge-service (story C2) — de achtergrond-loop die de `voorgesteld`-wachtrij
langsloopt en elk kandidaat-argument aanbiedt aan de A7-immuunpoort.

C2 = de dráaiende service; **A7 (server-side) levert het predikaat**. Deze loop
*beslist niets zelf*: hij itereert de wachtrij, doet één HTTP-call per kandidaat naar
`POST /api/arguments/<id>/auto_merge`, en registreert de uitkomst. Het endpoint checkt
het A7-predikaat (citatiepoort ∧ A1-herverificatie ∧ A2-tegenspraak ∧ A6-dedup ∧
jury-confidence ∧ niet-hoog-inzet ∧ praktijk-laag) **zelf** (defense-in-depth), zodat een
bug in deze loop nooit ongated kan mergen.

Contract met de F3-backend-lane:
    POST /api/arguments/<id>/auto_merge   (Bearer merge-service-token, reviewer-tier)
      → 200 {"merged": true,  "bucket": "auto-gemerged"}
      → 409 {"merged": false, "bucket": "geparkeerd-twijfel"|"geblokkeerd-hoog-inzet"|
                                        "mensenwerk", "redenen": [...]}
      → 503                                (kill-switch PROPAGANDA_AUTO_MERGE=0)

IDENTITEIT — het **reviewer-tier** systeemaccount `merge-service`
(data/tokens/merge-service.token). Bewust géén maintainer: die zou z'n eigen posts
auto-mergen en mogen verwijderen. `merge_argument` poort op reviewer, precies wat A7
sanctioneert, begrensd door het predikaat + de kill-switch + eigenaars-veto.

Faal-veilig & idempotent: elke merge is één server-transactie; gemergede argumenten
verdwijnen uit de wachtrij, dus een herstart/herdraai merget nooit dubbel. De queue
wordt elke cyclus vers opgehaald. Een dag-plafond op verificatie-spend voorkomt dat de
A1/A2-tokenkosten het budget leegtrekken (denial-of-wallet-verweer): boven het plafond
stopt de service en laat de rest voor de mens.

Audit-artefacten (beide gitignored, backend serveert data/auto_merge_log.json via
GET /api/auto_merge_log):
    data/auto_merge_log.json    {"arg:<id>": {"bucket","redenen","ts"}}   (uitzonderings-/
                                 steekproefwachtrij + audit; mirror van review_advies.json)
    data/auto_merge_state.json  {"datum","dag_teller","laatst_verwerkte_id"}  (restart-survival)

Voorbeelden:
    python3 scripts/auto_merge_service.py --dry-run          # toon wat het ZOU doen
    python3 scripts/auto_merge_service.py --once             # één ronde, echt mergen
    python3 scripts/auto_merge_service.py --plafond 50       # dag-plafond 50 verificaties
    python3 scripts/auto_merge_service.py --interval 300     # loop, 5 min tussen cycli

Draai GEEN live pass zonder eigenaars-sign-off: dat muteert het model autonoom.
"""
import argparse
import datetime as _dt
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEFAULT_TOKEN = ROOT / "data" / "tokens" / "merge-service.token"
DEFAULT_BASE = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "auto_merge_log.json"
STATE_PATH = ROOT / "data" / "auto_merge_state.json"

# Dag-plafond op verificatie-spend (elke auto_merge-call kan A1/A2-tokens kosten).
DEFAULT_PLAFOND = 100
# Sleep tussen individuele calls: merge-service = reviewer 60/min; ~1,1 s houdt de loop
# ruim onder de limiet ook als de vrijstelling (RATE_LIMIT_VRIJGESTELD) niet geldt.
CALL_THROTTLE_S = 1.1
# Sleep tussen loop-cycli (loop-modus, overschrijfbaar met --interval).
DEFAULT_INTERVAL_S = 300

# Terminale bucket: een hoog-inzet-blokkade (negatieve persoons-claim) merget A7 NOOIT
# automatisch, ongeacht de bron — dus nooit opnieuw een verificatie-token aan besteden.
TERMINALE_BUCKETS = {"geblokkeerd-hoog-inzet"}
# Aspect-/structuur-properties tellen niet in de zekerheidsbalans en vallen dus buiten A7
# (spiegelt server.py ASPECT_PROPERTIES). Alleen NULL + 'influence' zijn evidentieel.
EVIDENTIELE_PROPERTIES = {None, "", "influence"}


# --------------------------------------------------------------------------- HTTP
def _token(path):
    p = Path(path)
    if not p.exists():
        sys.exit(f"Token niet gevonden: {p}\n"
                 "Maak er een via: python3 scripts/create_user.py merge-service "
                 "--kind agent --rol reviewer --provenance \"C2 auto-merge-service\" "
                 "--new-token --save")
    return p.read_text().strip()


def _req(method, path, token, base, body=None):
    """Eén HTTP-call; geeft (status, payload). Patroon van scripts/admin.py:_req."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            txt = r.read().decode()
            return r.status, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try:
            payload = json.loads(txt)
        except json.JSONDecodeError:
            payload = {"error": txt}
        return e.code, payload
    except urllib.error.URLError as e:
        sys.exit(f"Kan de server niet bereiken op {base} ({e.reason}). Draait `python3 server.py`?")


# ------------------------------------------------------------------- state & log
def _laad_json(path, default):
    if not path.exists():
        return dict(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(default)


def _schrijf_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # atomair: een crash midden in het schrijven laat de oude log heel


def _vandaag():
    return _dt.date.today().isoformat()


def _laad_state():
    st = _laad_json(STATE_PATH, {"datum": _vandaag(), "dag_teller": 0,
                                 "laatst_verwerkte_id": None})
    if st.get("datum") != _vandaag():  # dagwissel → verificatie-teller reset
        st = {"datum": _vandaag(), "dag_teller": 0,
              "laatst_verwerkte_id": st.get("laatst_verwerkte_id")}
    return st


# --------------------------------------------------------------------- kandidaten
def _is_kandidaat(a):
    """Goedkope scope-filter (strikt vóór de dure A1/A2): alleen supporting/contradicting
    evidentiële **roots** op de praktijk-laag. Alles daarbuiten (replies/ondergravingen,
    contextual, aspect-roots, theorie- en instance-laag) weigert het endpoint tóch met
    bucket 'mensenwerk' — dit dubbele filter bespaart de call."""
    if a.get("parent_argument_id") is not None:
        return False
    if a.get("stance") not in ("supporting", "contradicting"):
        return False
    if a.get("property") not in EVIDENTIELE_PROPERTIES:
        return False
    # doel moet praktijk-laag zijn (relatie/entiteit), geen theorie (rol/mechanisme/veld)
    theorie = a.get("role_id") or a.get("mechanism_id") or a.get("emergent_effect_id")
    praktijk = a.get("relation_id") or a.get("entity_id")
    return bool(praktijk) and not theorie


def _al_geevalueerd_vandaag(log, arg_id):
    """Idempotentie/spend-zuinig: een item dat vandaag al een verdict kreeg (dus geparkeerd
    bleef — een gemerged item is uit de queue verdwenen) slaan we over. Zo doet een herdraai
    binnen de dag 0 nieuwe calls; een volgende dag wordt het opnieuw geëvalueerd (A1/A2-
    verdicts kunnen intussen zijn bijgewerkt). Een terminale hoog-inzet-blokkade blijft
    voorgoed overgeslagen."""
    entry = log.get(f"arg:{arg_id}")
    if not entry:
        return False
    if entry.get("bucket") in TERMINALE_BUCKETS:
        return True
    ts = entry.get("ts", "")
    return ts[:10] == _vandaag()


# ------------------------------------------------------------------------ ronde
def _print(msg):
    print(msg, flush=True)


def draai_ronde(token, base, plafond, dry_run, throttle=CALL_THROTTLE_S):
    """Eén wachtrij-doorloop. Geeft een tel-dict terug + of de kill-switch aanstond."""
    st, q = _req("GET", "/api/review_queue", token, base)
    if st != 200:
        _print(f"✗ review_queue gaf HTTP {st}: {q.get('error', q)}")
        return {"fout": True}, False

    alle = q.get("argumenten", [])
    kandidaten = [a for a in alle if _is_kandidaat(a)]
    _print(f"Wachtrij: {len(alle)} voorgesteld · {len(kandidaten)} in A7-scope "
           f"(supporting/contradicting evidentiële praktijk-roots)")

    log = _laad_json(LOG_PATH, {})
    state = _laad_state()
    tel = {"gemerged": 0, "geparkeerd": 0, "geblokkeerd": 0, "mensenwerk": 0,
           "overgeslagen": 0, "plafond_bereikt": False}
    kill_switch = False

    for a in kandidaten:
        arg_id = a["id"]

        if _al_geevalueerd_vandaag(log, arg_id):
            tel["overgeslagen"] += 1
            continue

        if state["dag_teller"] >= plafond:
            tel["plafond_bereikt"] = True
            _print(f"⏹ Dag-plafond ({plafond} verificaties) bereikt — rest blijft "
                   f"voor de menselijke wachtrij.")
            break

        claim = (a.get("claim") or "").replace("\n", " ")[:70]

        if dry_run:
            _print(f"  [dry-run] #{arg_id:>4} {a['stance']:<13} → ZOU aanbieden aan "
                   f"auto_merge :: {claim}")
            tel["overgeslagen"] += 1
            continue

        code, payload = _req("POST", f"/api/arguments/{arg_id}/auto_merge",
                             token, base, body={})

        if code == 503:  # kill-switch PROPAGANDA_AUTO_MERGE=0
            _print("⛔ Kill-switch actief (PROPAGANDA_AUTO_MERGE=0) — service stopt.")
            kill_switch = True
            break
        if code == 404:  # endpoint (nog) niet aanwezig — F3-backend-lane niet gemerged
            _print("✗ Endpoint /auto_merge ontbreekt (HTTP 404). De F3-backend-lane die "
                   "het A7-endpoint levert is nog niet gemerged. Service stopt.")
            tel["fout"] = True
            break

        bucket = payload.get("bucket")
        redenen = payload.get("redenen") or []

        if code == 200 and payload.get("merged"):
            bucket = bucket or "auto-gemerged"
            tel["gemerged"] += 1
            _print(f"  ✓ #{arg_id:>4} auto-gemerged :: {claim}")
        elif code == 409:
            if bucket == "geblokkeerd-hoog-inzet":
                tel["geblokkeerd"] += 1
            elif bucket == "mensenwerk":
                tel["mensenwerk"] += 1
            else:
                bucket = bucket or "geparkeerd-twijfel"
                tel["geparkeerd"] += 1
            _print(f"  · #{arg_id:>4} {bucket} :: {'; '.join(redenen) or claim}")
        else:
            bucket = bucket or f"fout-http-{code}"
            redenen = redenen or [payload.get("error", f"onverwachte HTTP {code}")]
            tel["geparkeerd"] += 1
            _print(f"  ? #{arg_id:>4} onverwacht HTTP {code}: {redenen}")

        # Elke uitkomst direct wegschrijven (fail-safe: een crash laat eerdere staat staan).
        log[f"arg:{arg_id}"] = {"bucket": bucket, "redenen": redenen,
                                "ts": _dt.datetime.now().isoformat(timespec="seconds")}
        _schrijf_json(LOG_PATH, log)

        # Verificatie-spend + restart-survival bijwerken (elke aangeboden call telt).
        state["dag_teller"] += 1
        state["laatst_verwerkte_id"] = arg_id
        _schrijf_json(STATE_PATH, state)

        time.sleep(throttle)  # onder 60/min blijven; niet zelf floodt

    return tel, kill_switch


def _samenvatting(tel):
    if tel.get("fout"):
        return
    _print("\n── Samenvatting ────────────────────────────")
    _print(f"  auto-gemerged        : {tel.get('gemerged', 0)}")
    _print(f"  geparkeerd-twijfel   : {tel.get('geparkeerd', 0)}")
    _print(f"  geblokkeerd-hoog-inzet: {tel.get('geblokkeerd', 0)}")
    _print(f"  mensenwerk (buiten A7): {tel.get('mensenwerk', 0)}")
    _print(f"  overgeslagen/reeds    : {tel.get('overgeslagen', 0)}")
    if tel.get("plafond_bereikt"):
        _print("  ⏹ dag-plafond bereikt — rest naar menselijke wachtrij")
    _print("────────────────────────────────────────────")


def main():
    ap = argparse.ArgumentParser(
        description="Auto-merge-service (C2): draait het A7-predikaat over de wachtrij.")
    ap.add_argument("--token", default=str(DEFAULT_TOKEN),
                    help=f"pad naar merge-service Bearer-token (default {DEFAULT_TOKEN})")
    ap.add_argument("--base-url", default=DEFAULT_BASE,
                    help=f"server-URL (default {DEFAULT_BASE})")
    ap.add_argument("--once", action="store_true", help="één ronde i.p.v. blijven loopen")
    ap.add_argument("--dry-run", action="store_true",
                    help="haal de queue op en toon wat het ZOU doen; doe GEEN enkele POST")
    ap.add_argument("--plafond", type=int, default=DEFAULT_PLAFOND,
                    help=f"dag-plafond op verificatie-spend (default {DEFAULT_PLAFOND})")
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_S,
                    help=f"seconden tussen loop-cycli (default {DEFAULT_INTERVAL_S})")
    args = ap.parse_args()

    token = _token(args.token)
    modus = "DRY-RUN" if args.dry_run else ("EENMALIG" if args.once else "LOOP")
    _print(f"Auto-merge-service · {modus} · base={args.base_url} · dag-plafond={args.plafond}")
    if not args.dry_run:
        st = _laad_state()
        _print(f"Verificatie-spend vandaag ({st['datum']}): {st['dag_teller']}/{args.plafond}")

    if args.once or args.dry_run:
        tel, _ = draai_ronde(token, args.base_url, args.plafond, args.dry_run)
        _samenvatting(tel)
        return 1 if tel.get("fout") else 0

    # Loop-modus: blijf cyclen tot de kill-switch of een fout.
    while True:
        tel, kill_switch = draai_ronde(token, args.base_url, args.plafond, dry_run=False)
        _samenvatting(tel)
        if kill_switch or tel.get("fout"):
            _print("Service stopt.")
            return 1 if tel.get("fout") else 0
        if tel.get("plafond_bereikt"):
            # Slaap tot na middernacht i.p.v. het plafond in een strakke lus te herbevestigen.
            _print(f"Plafond bereikt; wacht {args.interval}s (dag-teller reset na middernacht).")
        _print(f"… {args.interval}s tot de volgende cyclus (Ctrl-C om te stoppen).\n")
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        _print("\nOnderbroken.")
        sys.exit(130)
