#!/usr/bin/env python3
"""Scout-orkestratie — ontbrekende persoon-nodes + persoon→org-affiliaties indienen.

Dit script bevat GEEN inhoud. De inhoud (namen, rollen, bronnen, verbatim quotes) staat in
een los JSON-manifest (bv. data/scout/ronde1.json) dat uit webonderzoek is opgebouwd; dit
script draait daar alleen de scout-flow op via de REST-API, exact zoals een menselijke scout:

    bron (+ url-locator) → entiteit → relatie → argument (+ citaat)

Alles landt als `voorgesteld` onder het `assistent`-bijdrager-account en telt in niets tot
een mens het merget. De DB wordt nooit rechtstreeks beschreven — alleen alleen-lezen voor
dedup (entiteit op naam, relatie op (source,target,type)), zodat een herstart idempotent is.

Modelleerdiscipline (CLAUDE.md):
  * persoon→org-affiliatie: relatietype personeel/bestuurder/adviseur/woordvoerder_van/
    lidmaatschap; certainty/influence NIET zetten (guilty-until-proven, 0,05-vloer valt vanzelf in).
  * mechanisme-loos = kandidaat (incubeert); mechanisme_id alleen bij een echte sector-overstap
    (draaideurconstructie) of een ander passend bestaand mechanisme.
  * elke supporting/contradicting root draagt ≥1 echte citaat (quote of bron-met-locator),
    anders weigert de API met 400 — dat is de bedoeling, nooit fabriceren.

Gebruik:
    python3 scripts/scout_personen.py data/scout/ronde1.json            # droogloop
    python3 scripts/scout_personen.py data/scout/ronde1.json --indienen # echt indienen

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

    def get(self, pad):
        return self._call("GET", pad)

    def post(self, pad, body):
        return self._call("POST", pad, body)


def laad_entiteiten() -> dict[str, int]:
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return {n: i for n, i in conn.execute("SELECT name, id FROM entities")}
    finally:
        conn.close()


def laad_relaties() -> set:
    if not DB_PATH.exists():
        return set()
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return {tuple(r) for r in conn.execute(
            "SELECT source_id, target_id, relation_type FROM relations")}
    finally:
        conn.close()


def laad_org_namen() -> dict[int, str]:
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return {i: n for i, n in conn.execute("SELECT id, name FROM entities")}
    finally:
        conn.close()


class Indiener:
    def __init__(self, api: Api | None, entiteiten: dict, relaties: set, orgs: dict, droog: bool):
        self.api = api
        self.entiteiten = dict(entiteiten)   # naam → id (groeit tijdens de run)
        self.relaties = set(relaties)
        self.orgs = orgs
        self.droog = droog
        self.stats = {"personen_nieuw": 0, "personen_hergebruikt": 0,
                      "relaties_nieuw": 0, "relaties_bestaand": 0,
                      "bronnen": 0, "argumenten": 0, "overgeslagen": 0}

    # -- lage-niveau helpers --------------------------------------------------
    def _post(self, pad, body, wat):
        if self.droog:
            print(f"    [droog] POST {pad}  {json.dumps(body, ensure_ascii=False)[:120]}")
            return {"id": None}
        status, res = self.api.post(pad, body)
        if status not in (200, 201):
            print(f"    ✗ {wat} faalde ({status}): {res.get('error', res)}")
            return None
        return res

    def entiteit_id(self, naam: str, rol_id: int | None, beschrijving: str,
                    active_from=None, active_until=None) -> int | None:
        if naam in self.entiteiten:
            print(f"  • node bestaat: {naam} (#{self.entiteiten[naam]})")
            self.stats["personen_hergebruikt"] += 1
            return self.entiteiten[naam]
        body = {"name": naam, "type": "persoon"}
        if rol_id:
            body["primary_role_id"] = rol_id
        if beschrijving:
            body["description"] = beschrijving
        if active_from:
            body["active_from"] = active_from
        if active_until:
            body["active_until"] = active_until
        print(f"  + node aanmaken: {naam} (rol {rol_id})")
        res = self._post("/api/entities", body, "entiteit")
        if res is None:
            return None
        self.stats["personen_nieuw"] += 1
        nid = res.get("id")
        if nid:
            self.entiteiten[naam] = nid
        return nid

    def bron_id(self, bron: dict) -> int | None:
        body = {"title": bron["titel"], "source_type": bron.get("type", "website")}
        for k_src, k_body in (("author", "author"), ("publisher", "publisher"),
                              ("datum", "date_published")):
            if bron.get(k_src):
                body[k_body] = bron[k_src]
        if bron.get("url"):
            body["location"] = {"type": "url", "value": bron["url"]}
        if bron.get("onderwerp"):
            body["onderwerp_voorgesteld"] = bron["onderwerp"]
        if bron.get("betrouwbaarheid"):
            body["reliability_voorgesteld"] = bron["betrouwbaarheid"]
        res = self._post("/api/sources", body, "bron")
        if res is None:
            return None
        self.stats["bronnen"] += 1
        return res.get("id")

    def relatie(self, persoon_id, aff: dict, persoon_naam: str):
        org_id = aff["org_id"]
        rt = aff["relatietype"]
        sleutel = (persoon_id, org_id, rt)
        if persoon_id and sleutel in self.relaties:
            print(f"    · relatie bestaat al: {persoon_naam} -{rt}-> {self.orgs.get(org_id, org_id)}")
            self.stats["relaties_bestaand"] += 1
            # toch het argument proberen? nee — bestaande relatie heeft eigen boom; overslaan
            return
        body = {"source_id": persoon_id, "target_id": org_id, "relation_type": rt}
        if aff.get("mechanisme_id"):
            body["mechanism_id"] = aff["mechanisme_id"]
        if aff.get("beschrijving"):
            body["description"] = aff["beschrijving"]
        if aff.get("active_from"):
            body["active_from"] = aff["active_from"]
        if aff.get("active_until"):
            body["active_until"] = aff["active_until"]
        print(f"    + relatie: {persoon_naam} -{rt}-> {self.orgs.get(org_id, org_id)}"
              f"{' [mech ' + str(aff['mechanisme_id']) + ']' if aff.get('mechanisme_id') else ' [kandidaat]'}")
        res = self._post("/api/relations", body, "relatie")
        if res is None:
            return
        self.stats["relaties_nieuw"] += 1
        rel_id = res.get("id")
        if persoon_id:
            self.relaties.add(sleutel)
        # bron + argument
        bron = aff["bron"]
        src_id = self.bron_id(bron)
        arg = {"claim": aff["claim"], "stance": aff.get("stance", "supporting"),
               "relation_id": rel_id}
        cit = {"source_id": src_id}
        if bron.get("quote"):
            cit["quote"] = bron["quote"]
        arg["citations"] = [cit]
        res = self._post("/api/arguments", arg, "argument")
        if res is not None:
            self.stats["argumenten"] += 1

    def verwerk(self, personen: list):
        for p in personen:
            print(f"\n▸ {p['naam']}")
            pid = self.entiteit_id(p["naam"], p.get("rol_id"), p.get("beschrijving", ""),
                                   p.get("active_from"), p.get("active_until"))
            if pid is None and not self.droog:
                print("  ✗ node mislukt — affiliaties overgeslagen")
                self.stats["overgeslagen"] += 1
                continue
            for aff in p.get("affiliaties", []):
                self.relatie(pid, aff, p["naam"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--indienen", action="store_true", help="echt schrijven (default: droogloop)")
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--token", type=Path, default=DEFAULT_TOKEN)
    args = ap.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    personen = data["personen"] if isinstance(data, dict) else data
    droog = not args.indienen

    api = None
    if not droog:
        if not args.token.exists():
            sys.exit(f"Token ontbreekt: {args.token}")
        api = Api(args.api, args.token.read_text().strip())

    print(f"{'DROOGLOOP' if droog else 'INDIENEN'} — {len(personen)} perso(o)n(en) uit {args.manifest.name}")
    ind = Indiener(api, laad_entiteiten(), laad_relaties(), laad_org_namen(), droog)
    ind.verwerk(personen)
    print("\n── samenvatting ──")
    for k, v in ind.stats.items():
        print(f"  {k}: {v}")
    if droog:
        print("\n(droogloop — er is niets geschreven. Voeg --indienen toe om echt in te dienen.)")


if __name__ == "__main__":
    main()
