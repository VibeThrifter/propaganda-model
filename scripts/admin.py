#!/usr/bin/env python3
"""Admin-client voor het propagandamodel — een dunne REST-wrapper waarmee een
*maintainer* (mens, desnoods via Claude Code) de review-wachtrij beheert: het lezen
van de reviewer-gated adviesbestanden en het keuren / afwijzen / editten / mergen van
argumenten en voorstellen.

GEEN directe DB-toegang: alles loopt via de bestaande REST API met een Bearer-token,
zodat attributie, `edit_log` én de poorten (reviewer+/maintainer, niemand-keurt-eigen-werk)
vanzelf kloppen. Er is hier geen *nieuwe* API — de endpoints bestonden al; dit is enkel
een ergonomische client eromheen.

IDENTITEIT — standaard het maintainer-account `maxime` (data/tokens/maxime.token). Dit is
BEWUST een mens-account: admin-acties zijn het besluit van de eigenaar; Claude voert ze uit
op *expliciete* aanwijzing. "Ik stel voor, jij beslist" blijft gelden — keur nooit ongevraagd
je eigen `assistent`-inzending goed. Inhoud *voorstellen* blijft via het `assistent`-
bijdrageraccount (POST /api/arguments|sources|... ) en loopt NIET via deze client.

Voorbeelden:
    python3 scripts/admin.py queue                 # wat staat er ter review?
    python3 scripts/admin.py advies                # reviewbeoordelaar-advies (reviewer+)
    python3 scripts/admin.py bronnen               # documentalist bron-suggesties (reviewer+)
    python3 scripts/admin.py afgewezen             # afgewezen/ingetrokken backlog
    python3 scripts/admin.py merge 481             # voorgesteld argument mergen
    python3 scripts/admin.py afwijzen 481 -m "..." # afwijzen (motivatie verplicht)
    python3 scripts/admin.py herkeuren 481 -m "..."# gemerged argument terug ter herkeuring
    python3 scripts/admin.py edit-arg 481 --claim "..." --reasoning "..."
    python3 scripts/admin.py voorstel 15           # één RfC tonen
    python3 scripts/admin.py voorstel-akkoord 15   # RfC goedkeuren (telt; maintainer = quorum)
    python3 scripts/admin.py voorstel-afwijzen 15 -m "..."
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEFAULT_TOKEN = ROOT / "data" / "tokens" / "maxime.token"
DEFAULT_BASE = "http://localhost:5000"


def _token(path):
    p = Path(path)
    if not p.exists():
        sys.exit(f"Token niet gevonden: {p}\n"
                 "Maak/roteer er een via scripts/create_user.py, of geef --token <pad>.")
    return p.read_text().strip()


def _req(method, path, token, base, body=None):
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


def _ok(status, payload, msg=None):
    if 200 <= status < 300:
        print(f"✓ {msg}" if msg else json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    fout = payload.get("fouten") or payload.get("error") or payload
    print(f"✗ HTTP {status}: {fout}", file=sys.stderr)
    return 1


def _argregel(a):
    claim = (a.get("claim") or "").replace("\n", " ")
    return f"  #{a['id']:>4}  {a.get('stance', '?'):<13} {claim[:84]}"


def cmd_queue(args, token, base):
    st, q = _req("GET", "/api/review_queue", token, base)
    if st != 200:
        return _ok(st, q)
    arg, herk = q.get("argumenten", []), q.get("herkeuring", [])
    voor, ent, rel = q.get("voorstellen", []), q.get("entiteiten", []), q.get("relaties", [])
    print(f"Argumenten (voorgesteld): {len(arg)}")
    for a in arg:
        print(_argregel(a))
    print(f"\nHerkeuring (betwist): {len(herk)}")
    for a in herk:
        print(_argregel(a))
    print(f"\nVoorstellen / RfC's (open): {len(voor)}")
    for v in voor:
        akk = len(set((v.get("telling") or {}).get("akkoorden") or []))
        print(f"  #{v['id']:>4}  {v['soort']:<22} {akk}/{v.get('benodigde_akkoorden', '?')} akkoord  {v['titel'][:62]}")
    print(f"\nPraktijk — entiteiten: {len(ent)}, relaties: {len(rel)}")
    for e in ent:
        print(f"  ent #{e['id']:>4}  {e.get('name', '')}")
    for r in rel:
        print(f"  rel #{r['id']:>4}  {r.get('source_name', '')} → {r.get('target_name', '')}")
    return 0


def cmd_advies(args, token, base):
    return _ok(*_req("GET", "/api/review_advies", token, base))


def cmd_bronnen(args, token, base):
    return _ok(*_req("GET", "/api/bron_suggesties", token, base))


def cmd_afgewezen(args, token, base):
    st, af = _req("GET", "/api/afgewezen", token, base)
    if st != 200:
        return _ok(st, af)
    for sectie in ("voorstellen", "argumenten", "entiteiten", "relaties"):
        items = af.get(sectie, [])
        print(f"{sectie}: {len(items)}")
        for it in items:
            label = it.get("titel") or it.get("claim") or it.get("name") or \
                f"{it.get('source_name', '')} → {it.get('target_name', '')}"
            print(f"  #{it['id']:>4}  {str(label)[:84]}")
    return 0


def cmd_merge(args, token, base):
    st, p = _req("POST", f"/api/arguments/{args.id}/merge", token, base, body={})
    return _ok(st, p, f"argument #{args.id} gemerged (status: {p.get('status', '?')})")


def cmd_afwijzen(args, token, base):
    body = {"status": "verworpen", "motivatie": args.motivatie}
    st, p = _req("PATCH", f"/api/arguments/{args.id}/status", token, base, body=body)
    return _ok(st, p, f"argument #{args.id} afgewezen")


def cmd_herkeuren(args, token, base):
    body = {"status": "betwist", "motivatie": args.motivatie}
    st, p = _req("PATCH", f"/api/arguments/{args.id}/status", token, base, body=body)
    return _ok(st, p, f"argument #{args.id} terug ter herkeuring")


def cmd_edit_arg(args, token, base):
    body = {k: v for k, v in (("claim", args.claim), ("reasoning", args.reasoning)) if v is not None}
    if not body:
        sys.exit("Geef minstens --claim of --reasoning.")
    st, p = _req("PATCH", f"/api/arguments/{args.id}", token, base, body=body)
    return _ok(st, p, f"argument #{args.id} bijgewerkt")


def cmd_voorstel(args, token, base):
    return _ok(*_req("GET", f"/api/voorstellen/{args.id}", token, base))


def cmd_voorstel_akkoord(args, token, base):
    body = {"oordeel": "akkoord"}
    if args.motivatie:
        body["motivatie"] = args.motivatie
    st, p = _req("POST", f"/api/voorstellen/{args.id}/reviews", token, base, body=body)
    return _ok(st, p, f"voorstel #{args.id}: akkoord geregistreerd (status: {p.get('status', '?')})")


def cmd_voorstel_afwijzen(args, token, base):
    body = {"oordeel": "afwijzen", "motivatie": args.motivatie}
    st, p = _req("POST", f"/api/voorstellen/{args.id}/reviews", token, base, body=body)
    return _ok(st, p, f"voorstel #{args.id} afgewezen")


def main():
    ap = argparse.ArgumentParser(description="Admin-client (maintainer) voor de review-wachtrij.")
    ap.add_argument("--token", default=str(DEFAULT_TOKEN), help=f"pad naar Bearer-token (default {DEFAULT_TOKEN})")
    ap.add_argument("--base", default=DEFAULT_BASE, help=f"server-URL (default {DEFAULT_BASE})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("queue", help="review-wachtrij tonen").set_defaults(fn=cmd_queue)
    sub.add_parser("advies", help="reviewbeoordelaar-advies (reviewer+)").set_defaults(fn=cmd_advies)
    sub.add_parser("bronnen", help="documentalist bron-suggesties (reviewer+)").set_defaults(fn=cmd_bronnen)
    sub.add_parser("afgewezen", help="afgewezen/ingetrokken backlog").set_defaults(fn=cmd_afgewezen)

    p = sub.add_parser("merge", help="voorgesteld argument mergen"); p.add_argument("id", type=int); p.set_defaults(fn=cmd_merge)
    p = sub.add_parser("afwijzen", help="argument afwijzen"); p.add_argument("id", type=int)
    p.add_argument("-m", "--motivatie", required=True); p.set_defaults(fn=cmd_afwijzen)
    p = sub.add_parser("herkeuren", help="gemerged argument terug ter herkeuring"); p.add_argument("id", type=int)
    p.add_argument("-m", "--motivatie", required=True); p.set_defaults(fn=cmd_herkeuren)
    p = sub.add_parser("edit-arg", help="voorgesteld argument bijwerken"); p.add_argument("id", type=int)
    p.add_argument("--claim"); p.add_argument("--reasoning"); p.set_defaults(fn=cmd_edit_arg)

    p = sub.add_parser("voorstel", help="één RfC tonen"); p.add_argument("id", type=int); p.set_defaults(fn=cmd_voorstel)
    p = sub.add_parser("voorstel-akkoord", help="RfC goedkeuren (telt)"); p.add_argument("id", type=int)
    p.add_argument("-m", "--motivatie"); p.set_defaults(fn=cmd_voorstel_akkoord)
    p = sub.add_parser("voorstel-afwijzen", help="RfC afwijzen"); p.add_argument("id", type=int)
    p.add_argument("-m", "--motivatie", required=True); p.set_defaults(fn=cmd_voorstel_afwijzen)

    args = ap.parse_args()
    sys.exit(args.fn(args, _token(args.token), args.base))


if __name__ == "__main__":
    main()
