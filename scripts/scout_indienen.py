#!/usr/bin/env python3
"""Scout-orkestratie (generiek) — bronnen, entiteiten, relaties én argumenten indienen.

Generalisatie van scout_personen.py: waar dat script alleen persoon→org-affiliaties
aankan, draait dit script een volledig manifest (elk entiteitstype, elke relatie,
losse argumenten op bestaande doelen). Het bevat GEEN inhoud; de inhoud staat in een
JSON-manifest (bv. data/scout/sterkste-routes-r1.json) dat uit geverifieerd
webonderzoek is opgebouwd. De flow per vondst is die van een menselijke scout:

    bron (+ url-locator) → entiteit → relatie → argument (+ citaat)

Alles landt als `voorgesteld` onder het `assistent`-bijdrager-account en telt in
niets tot een mens het merget. De DB wordt nooit rechtstreeks beschreven — alleen
alleen-lezen voor dedup (entiteit op naam, relatie op (source,target,type)).

Manifest-schema:
    {
      "bronnen":    [{"key", "titel", "type", "author", "publisher", "datum",
                      "url", "onderwerp", "betrouwbaarheid"}],
      "entiteiten": [{"key", "naam", "type", "rol_id", "beschrijving",
                      "active_from", "active_until"}],
      "relaties":   [{"source", "target",          # int = bestaand DB-id, str = manifest-key
                      "relation_type", "mechanisme_id", "beschrijving",
                      "active_from", "active_until",
                      "argumenten": [{"claim", "stance", "bron",  # bron = manifest-key
                                      "quote", "property", "property_value"}]}],
      "argumenten": [{"doel": {"relation_id"|"entity_id"|"mechanism_id"|
                               "role_id"|"emergent_effect_id": <id>},
                      "claim", "stance", "bron", "quote", "reasoning",
                      "property", "property_value"}]
    }

Modelleerdiscipline (CLAUDE.md): certainty/influence NIET zetten (0,05-vloer);
mechanisme-loos = kandidaat; elke supporting/contradicting root ≥1 echte citatie;
een 409 (duplicaat) wordt gelogd en overgeslagen, nooit met negeer_duplicaten
overreden.

Gebruik:
    python3 scripts/scout_indienen.py data/scout/sterkste-routes-r1.json            # droogloop
    python3 scripts/scout_indienen.py data/scout/sterkste-routes-r1.json --indienen # echt

Opties: --api (default http://localhost:5000), --token (default data/tokens/assistent.token).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / "assistent.token"
DEFAULT_API = "http://localhost:5000"

DOEL_VELDEN = ("relation_id", "entity_id", "role_id", "mechanism_id", "emergent_effect_id")


class Api:
    """Dunne REST-client (stdlib) met Bearer-auth en 429-retry."""

    def __init__(self, basis: str, token: str | None):
        self.basis = basis.rstrip("/")
        self.token = token

    def _call(self, method: str, pad: str, body: dict | None = None):
        for poging in range(5):
            status, res = self._eenmalig(method, pad, body)
            geraakt = status == 429 or "rate limit" in str(res.get("error", "")).lower()
            if geraakt and poging < 4:
                print("    ⏳ rate limit — 62s wachten…")
                time.sleep(62)
                continue
            return status, res
        return status, res

    def _eenmalig(self, method: str, pad: str, body: dict | None):
        url = f"{self.basis}{pad}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode() or "{}")
            except Exception:
                return e.code, {"error": str(e)}
        except urllib.error.URLError as e:
            sys.exit(f"Kan de API niet bereiken op {self.basis} ({e}). Draai: python3 server.py")

    def post(self, pad, body):
        return self._call("POST", pad, body)


def lees_db(query: str):
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return list(conn.execute(query))
    finally:
        conn.close()


class Indiener:
    def __init__(self, api: Api | None, droog: bool):
        self.api = api
        self.droog = droog
        self.entiteiten = {n: i for n, i in lees_db("SELECT name, id FROM entities")}
        self.namen = {i: n for n, i in self.entiteiten.items()}
        self.relaties = {tuple(r) for r in lees_db(
            "SELECT source_id, target_id, relation_type FROM relations")}
        self.bron_keys: dict[str, int | None] = {}
        self.ent_keys: dict[str, int | None] = {}
        self.aangemaakt: list[tuple[str, str, int | None]] = []
        self.stats = {"bronnen": 0, "entiteiten_nieuw": 0, "entiteiten_bestaand": 0,
                      "relaties_nieuw": 0, "relaties_bestaand": 0,
                      "argumenten": 0, "duplicaat_409": 0, "mislukt": 0}
        self._droog_teller = 0

    # -- helpers ---------------------------------------------------------------
    def _post(self, pad, body, wat):
        if self.droog:
            self._droog_teller -= 1
            print(f"    [droog] POST {pad}  {json.dumps(body, ensure_ascii=False)[:140]}")
            return {"id": self._droog_teller}
        status, res = self.api.post(pad, body)
        if status == 409:
            kand = res.get("duplicaat_kandidaten") or res.get("bestaande_reactie") or ""
            print(f"    ≈ duplicaat (409) bij {wat}: {str(kand)[:120]} — overgeslagen")
            self.stats["duplicaat_409"] += 1
            return None
        if status not in (200, 201):
            print(f"    ✗ {wat} faalde ({status}): {res.get('error', res)}")
            self.stats["mislukt"] += 1
            return None
        return res

    def _ent_id(self, ref, kant: str) -> int | None:
        """int = bestaand DB-id, str = manifest-key."""
        if isinstance(ref, int):
            if ref not in self.namen:
                print(f"    ✗ onbekend DB-id {ref} ({kant})")
                self.stats["mislukt"] += 1
                return None
            return ref
        if ref in self.ent_keys:
            return self.ent_keys[ref]
        print(f"    ✗ onbekende entiteit-key '{ref}' ({kant})")
        self.stats["mislukt"] += 1
        return None

    def _naam(self, eid) -> str:
        if eid in self.namen:
            return self.namen[eid]
        for k, v in self.ent_keys.items():
            if v == eid:
                return k
        return str(eid)

    # -- stappen ---------------------------------------------------------------
    def bronnen(self, items: list):
        for b in items:
            body = {"title": b["titel"], "source_type": b.get("type", "website")}
            for k_src, k_body in (("author", "author"), ("publisher", "publisher"),
                                  ("datum", "date_published")):
                if b.get(k_src):
                    body[k_body] = b[k_src]
            if b.get("url"):
                body["location"] = {"type": "url", "value": b["url"]}
            if b.get("onderwerp"):
                body["onderwerp_voorgesteld"] = b["onderwerp"]
            if b.get("betrouwbaarheid"):
                body["reliability_voorgesteld"] = b["betrouwbaarheid"]
            print(f"▸ bron: {b['titel'][:80]}")
            res = self._post("/api/sources", body, "bron")
            sid = res.get("id") if res else None
            self.bron_keys[b["key"]] = sid
            if res:
                self.stats["bronnen"] += 1
                self.aangemaakt.append(("bron", b["titel"][:60], sid))

    def entiteiten_aanmaken(self, items: list):
        for e in items:
            naam = e["naam"]
            if naam in self.entiteiten:
                print(f"▸ node bestaat: {naam} (#{self.entiteiten[naam]})")
                self.ent_keys[e["key"]] = self.entiteiten[naam]
                self.stats["entiteiten_bestaand"] += 1
                continue
            body = {"name": naam, "type": e["type"]}
            if e.get("rol_id"):
                body["primary_role_id"] = e["rol_id"]
            if e.get("beschrijving"):
                body["description"] = e["beschrijving"]
            for veld in ("active_from", "active_until"):
                if e.get(veld):
                    body[veld] = e[veld]
            print(f"▸ node aanmaken: {naam} ({e['type']}, rol {e.get('rol_id')})")
            res = self._post("/api/entities", body, "entiteit")
            nid = res.get("id") if res else None
            self.ent_keys[e["key"]] = nid
            if res:
                self.stats["entiteiten_nieuw"] += 1
                self.aangemaakt.append(("entiteit", naam, nid))
                self.entiteiten[naam] = nid
                if nid:
                    self.namen[nid] = naam

    def _argument(self, doel: dict, a: dict, context: str):
        body = {"claim": a["claim"], "stance": a.get("stance", "supporting"), **doel}
        if a.get("reasoning"):
            body["reasoning"] = a["reasoning"]
        if a.get("property"):
            body["property"] = a["property"]
        if a.get("property_value") is not None:
            body["property_value"] = str(a["property_value"])
        if a.get("bron"):
            sid = self.bron_keys.get(a["bron"])
            if sid is None and not self.droog:
                print(f"    ✗ argument overgeslagen — bron-key '{a['bron']}' niet aangemaakt")
                self.stats["mislukt"] += 1
                return
            cit = {"source_id": sid}
            if a.get("quote"):
                cit["quote"] = a["quote"]
            body["citations"] = [cit]
        print(f"    + argument ({body['stance']}{', ' + a['property'] if a.get('property') else ''}) op {context}")
        res = self._post("/api/arguments", body, "argument")
        if res:
            self.stats["argumenten"] += 1
            self.aangemaakt.append(("argument", a["claim"][:60], res.get("id")))

    def relaties_aanmaken(self, items: list):
        for r in items:
            sid = self._ent_id(r["source"], "source")
            tid = self._ent_id(r["target"], "target")
            if sid is None or tid is None:
                continue
            rt = r["relation_type"]
            sleutel = (sid, tid, rt)
            if sleutel in self.relaties:
                print(f"▸ relatie bestaat al: {self._naam(sid)} -{rt}-> {self._naam(tid)} — overgeslagen")
                self.stats["relaties_bestaand"] += 1
                continue
            body = {"source_id": sid, "target_id": tid, "relation_type": rt}
            if r.get("mechanisme_id"):
                body["mechanism_id"] = r["mechanisme_id"]
            if r.get("beschrijving"):
                body["description"] = r["beschrijving"]
            for veld in ("active_from", "active_until"):
                if r.get(veld):
                    body[veld] = r[veld]
            print(f"▸ relatie: {self._naam(sid)} -{rt}-> {self._naam(tid)}"
                  f"{' [mech ' + str(r['mechanisme_id']) + ']' if r.get('mechanisme_id') else ' [kandidaat]'}")
            res = self._post("/api/relations", body, "relatie")
            if res is None:
                continue
            rel_id = res.get("id")
            self.stats["relaties_nieuw"] += 1
            self.aangemaakt.append(("relatie", f"{self._naam(sid)} -{rt}-> {self._naam(tid)}", rel_id))
            self.relaties.add(sleutel)
            for a in r.get("argumenten", []):
                self._argument({"relation_id": rel_id}, a, "nieuwe relatie")

    def losse_argumenten(self, items: list):
        for a in items:
            doel = {k: v for k, v in a.get("doel", {}).items() if k in DOEL_VELDEN}
            if len(doel) != 1:
                print(f"    ✗ argument zonder geldig doel: {a.get('claim', '')[:60]}")
                self.stats["mislukt"] += 1
                continue
            self._argument(doel, a, f"bestaand doel {doel}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--indienen", action="store_true", help="echt schrijven (default: droogloop)")
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", type=Path, default=DEFAULT_TOKEN)
    args = ap.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    droog = not args.indienen

    api = None
    if not droog:
        if not args.token.exists():
            sys.exit(f"Token ontbreekt: {args.token}")
        api = Api(args.api, args.token.read_text().strip())

    print(f"{'DROOGLOOP' if droog else 'INDIENEN'} — {args.manifest.name}: "
          f"{len(data.get('bronnen', []))} bronnen, {len(data.get('entiteiten', []))} entiteiten, "
          f"{len(data.get('relaties', []))} relaties, {len(data.get('argumenten', []))} losse argumenten")
    ind = Indiener(api, droog)
    ind.bronnen(data.get("bronnen", []))
    ind.entiteiten_aanmaken(data.get("entiteiten", []))
    ind.relaties_aanmaken(data.get("relaties", []))
    ind.losse_argumenten(data.get("argumenten", []))

    print("\n── samenvatting ──")
    for k, v in ind.stats.items():
        print(f"  {k}: {v}")
    if not droog and ind.aangemaakt:
        print("\n── aangemaakt (voor het missielog) ──")
        for soort, naam, oid in ind.aangemaakt:
            print(f"  {soort} #{oid}: {naam}")
    if droog:
        print("\n(droogloop — er is niets geschreven. Voeg --indienen toe om echt in te dienen.)")


if __name__ == "__main__":
    main()
