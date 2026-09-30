#!/usr/bin/env python3
"""Nieuws-autokeur-service (Epic 12 "Wie is dit?", eigenaarsbesluit 2026-09-30) — de
deterministische loop die het werk van de `nieuws-scout` aanbiedt aan de
autokeur-poort. Spiegel van `scripts/auto_merge_service.py`.

Deze service *beslist niets zelf*: ze haalt de nieuws-doelen met status `klaar` op,
verzamelt de entiteit- en relatie-id's uit hun `resultaat`, en biedt ze één voor één
aan `POST /api/nieuws/autokeur/<tabel>/<id>` aan — **entiteiten eerst, dan relaties**
(een relatie mag pas als beide eindpunten goedgekeurd zijn). Het endpoint checkt het
predikaat `nieuws_autokeur_toegestaan` ZELF (defense-in-depth), past de kill-switch
(PROPAGANDA_NIEUWS_AUTOKEUR=0 → 503) en het dagplafond (→ 429) toe en keurt goed via
dezelfde moderatie-kern als een mens (eigen-werk-, orphan- en bronplicht-poort,
instantiaties, edit_log onder `nieuws-autokeur`). Argumenten worden nooit gemerged.

IDENTITEIT — het reviewer-tier machine-account `nieuws-autokeur`
(data/tokens/nieuws-autokeur.token). Bewust géén maintainer.

Modi:
    python3 scripts/nieuws_autokeur_service.py              # DROOGLOOP (default): toon
                                                            #   wat er zou gebeuren, via de
                                                            #   alleen-lezen predikaat-check
    python3 scripts/nieuws_autokeur_service.py --once       # één echte ronde
    python3 scripts/nieuws_autokeur_service.py --once --json
    python3 scripts/nieuws_autokeur_service.py --loop --interval 1800

`--json` print (en alleen dat, op stdout):
    {"goedgekeurd": {"entities": [ids], "relations": [ids]},
     "geparkeerd": [{"tabel", "id", "redenen"}], "doelen": [ids]}
(in de droogloop = wat er ZOU worden goedgekeurd). Meldingen gaan dan naar stderr.

Exit-codes: 0 = ok (ook als het dagplafond halverwege bereikt werd), 2 = server/token
onbereikbaar of onverwachte HTTP-fout, 3 = kill-switch actief.

Audit: élke beslissing van een echte ronde komt als JSON-regel in
data/nieuws_autokeur_log.jsonl (gitignored; ook via GET /api/nieuws/autokeur/log en
`scripts/admin.py autokeur-log`). Terugdraaien: `scripts/admin.py intrekken <tabel> <id> -m …`
(maintainer).
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
DEFAULT_TOKEN = ROOT / "data" / "tokens" / "nieuws-autokeur.token"
DEFAULT_BASE = "http://127.0.0.1:5000"
LOG_PATH = ROOT / "data" / "nieuws_autokeur_log.jsonl"
DEFAULT_PAUZE_S = 1.0          # tussen goedkeur-POSTs (menselijk tempo, ruim onder elke limiet)
DEFAULT_INTERVAL_S = 1800
EXIT_OK, EXIT_FOUT, EXIT_KILL = 0, 2, 3


class ServiceFout(Exception):
    """Server onbereikbaar / onverwacht antwoord — faal-veilig stoppen."""


def _req(method, path, token, base, body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode()
            return r.status, (json.loads(txt) if txt else {})
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try:
            payload = json.loads(txt)
        except json.JSONDecodeError:
            payload = {"error": txt}
        return e.code, payload
    except (urllib.error.URLError, OSError) as e:
        reden = getattr(e, "reason", e)
        raise ServiceFout(f"kan de propagandamodel-server niet bereiken op {base} ({reden}). "
                          "Start hem met `python3 server.py` (of de launchd-server-job) en "
                          "probeer opnieuw — er is niets goedgekeurd.")


def _schrijf_log(regel):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(regel, ensure_ascii=False) + "\n")


def verzamel(token, base):
    """→ (doel_ids, {tabel: {id: [doel_ids]}}) uit de 'klaar'-doelen."""
    st, d = _req("GET", "/api/nieuws/doelen?status=klaar&limit=500", token, base)
    if st != 200:
        raise ServiceFout(f"GET /api/nieuws/doelen gaf HTTP {st}: {d.get('error', d)}")
    items = {"entities": {}, "relations": {}}
    doel_ids = []
    for doel in d.get("doelen", []):
        res = doel.get("resultaat") or {}
        if not isinstance(res, dict):
            continue
        heeft = False
        for tabel, sleutel in (("entities", "entity_ids"), ("relations", "relation_ids")):
            for i in res.get(sleutel) or []:
                if isinstance(i, int):
                    items[tabel].setdefault(i, []).append(doel["id"])
                    heeft = True
        if heeft:
            doel_ids.append(doel["id"])
    return doel_ids, items


def draai_ronde(token, base, droog, pauze=DEFAULT_PAUZE_S, meld=print):
    """Eén ronde. → (uitkomst-dict in contractvorm, gestopt: None|'plafond'|'kill-switch')."""
    doel_ids, items = verzamel(token, base)
    uit = {"goedgekeurd": {"entities": [], "relations": []}, "geparkeerd": [],
           "doelen": doel_ids}
    gestopt = None
    meld(f"Nieuws-autokeur · {'DROOGLOOP' if droog else 'RONDE'} · {len(doel_ids)} klaar-doel(en), "
         f"{len(items['entities'])} entiteit(en), {len(items['relations'])} relatie(s)")
    for tabel in ("entities", "relations"):          # entiteiten EERST (eindpunten)
        for rid in sorted(items[tabel]):
            st, chk = _req("GET", f"/api/nieuws/autokeur/{tabel}/{rid}", token, base)
            if st == 404:
                meld(f"  · {tabel} #{rid}: bestaat niet (meer) — overgeslagen")
                continue
            if st != 200:
                raise ServiceFout(f"predikaat-check {tabel} #{rid} gaf HTTP {st}: "
                                  f"{chk.get('error', chk)}")
            if chk.get("status") != "voorgesteld":
                continue                              # al beoordeeld (goedgekeurd/afgewezen)
            if droog:
                if chk.get("toegestaan"):
                    uit["goedgekeurd"][tabel].append(rid)
                    meld(f"  [droog] {tabel} #{rid}: ZOU goedgekeurd worden")
                else:
                    uit["geparkeerd"].append({"tabel": tabel, "id": rid,
                                              "redenen": chk.get("redenen", [])})
                    meld(f"  [droog] {tabel} #{rid}: geparkeerd — "
                         f"{'; '.join(chk.get('redenen', []))}")
                continue
            code, p = _req("POST", f"/api/nieuws/autokeur/{tabel}/{rid}", token, base, body={})
            ts = _dt.datetime.now().isoformat(timespec="seconds")
            if code == 200 and p.get("goedgekeurd"):
                uit["goedgekeurd"][tabel].append(rid)
                _schrijf_log({"ts": ts, "tabel": tabel, "id": rid, "uitkomst": "goedgekeurd",
                              "doelen": items[tabel][rid]})
                meld(f"  ✓ {tabel} #{rid}: automatisch goedgekeurd")
            elif code == 409:
                redenen = p.get("redenen") or [p.get("error", "niet toegestaan")]
                uit["geparkeerd"].append({"tabel": tabel, "id": rid, "redenen": redenen})
                _schrijf_log({"ts": ts, "tabel": tabel, "id": rid, "uitkomst": "geparkeerd",
                              "redenen": redenen, "doelen": items[tabel][rid]})
                meld(f"  · {tabel} #{rid}: geparkeerd — {'; '.join(redenen)}")
            elif code == 429:
                gestopt = "plafond"
                _schrijf_log({"ts": ts, "uitkomst": "plafond", "error": p.get("error")})
                meld(f"⏹ Dagplafond bereikt — rest blijft voor de mens ({p.get('error')})")
                return uit, gestopt
            elif code == 503:
                gestopt = "kill-switch"
                meld("⛔ Kill-switch actief (PROPAGANDA_NIEUWS_AUTOKEUR=0) — service stopt.")
                return uit, gestopt
            else:
                raise ServiceFout(f"onverwachte HTTP {code} op {tabel} #{rid}: "
                                  f"{p.get('error', p)}")
            time.sleep(pauze)
    return uit, gestopt


def main(argv=None):
    ap = argparse.ArgumentParser(description="Nieuws-autokeur-service (Epic 12).")
    ap.add_argument("--token", default=str(DEFAULT_TOKEN),
                    help=f"pad naar het nieuws-autokeur-token (default {DEFAULT_TOKEN})")
    ap.add_argument("--base-url", default=DEFAULT_BASE,
                    help=f"server-URL (default {DEFAULT_BASE})")
    ap.add_argument("--once", action="store_true", help="één ECHTE ronde (keurt goed)")
    ap.add_argument("--loop", action="store_true", help="blijf echte rondes draaien")
    ap.add_argument("--dry-run", action="store_true",
                    help="droogloop afdwingen (default zonder --once/--loop)")
    ap.add_argument("--json", action="store_true",
                    help="print alleen het resultaat als JSON (contractvorm) op stdout")
    ap.add_argument("--pauze", type=float, default=DEFAULT_PAUZE_S,
                    help=f"seconden tussen goedkeur-calls (default {DEFAULT_PAUZE_S})")
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_S,
                    help=f"seconden tussen rondes in --loop (default {DEFAULT_INTERVAL_S})")
    args = ap.parse_args(argv)
    droog = args.dry_run or not (args.once or args.loop)
    leeg = {"goedgekeurd": {"entities": [], "relations": []}, "geparkeerd": [], "doelen": []}

    def meld(tekst):
        print(tekst, file=sys.stderr if args.json else sys.stdout, flush=True)

    def klaar(uit, code):
        if args.json:
            print(json.dumps(uit, ensure_ascii=False))
        return code

    token_pad = Path(args.token)
    if not token_pad.exists():
        meld(f"✗ Token niet gevonden: {token_pad}. Maak het aan met: python3 "
             "scripts/create_user.py nieuws-autokeur --kind agent --rol reviewer "
             "--provenance \"…\" --new-token --save")
        return klaar(leeg, EXIT_FOUT)
    token = token_pad.read_text().strip()

    while True:
        try:
            uit, gestopt = draai_ronde(token, args.base_url, droog, args.pauze, meld)
        except ServiceFout as e:
            meld(f"✗ {e}")
            return klaar(leeg, EXIT_FOUT)
        g = uit["goedgekeurd"]
        meld(f"── {'zou goedkeuren' if droog else 'goedgekeurd'}: {len(g['entities'])} "
             f"entiteit(en), {len(g['relations'])} relatie(s) · geparkeerd: "
             f"{len(uit['geparkeerd'])}")
        if droog:
            meld("(droogloop — er is niets goedgekeurd; gebruik --once voor een echte ronde)")
        if not args.loop or droog or gestopt == "kill-switch":
            return klaar(uit, EXIT_KILL if gestopt == "kill-switch" else EXIT_OK)
        meld(f"… {args.interval}s tot de volgende ronde (Ctrl-C om te stoppen)")
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOnderbroken.", file=sys.stderr)
        sys.exit(130)
