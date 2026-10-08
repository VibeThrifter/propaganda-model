#!/usr/bin/env python3
"""Theorie-uitbreiding indienen vanuit een manifest (Uitbreiding C, eigenaarsbesluit 2026-10-07).

De basistheorie van een nieuwe categorie-groep gaat erin zoals de basis van het
propagandamodel erin ging: in de opbouwfase via de maintainer-route (POST /api/roles,
POST /api/mechanisms, POST /api/mechanisms/<id>/filters), gelogd als "opbouwfase, langs
RfC heen — betwistbaar". Elk nieuw element krijgt meteen een steunend argument mét
letterlijk citaat uit een online bron, ingediend onder het bijdrager-account `assistent`
(scout_indienen.Indiener); de automatische beoordeling controleert dat argument zoals
elk ander. Latere theorie gaat weer via RfC's.

Volgorde: rollen → mechanismen (rolnamen worden id's) → overlap op bestaande mechanismen
→ bronnen → argumenten. Bestaat een rol of mechanisme al (op naam), dan slaat het script
hem over; overlap is idempotent (INSERT OR IGNORE).

Manifest (JSON):
    {
      "bronnen":     [scout_indienen-bronschema: key, titel, type, publisher, url, …],
      "rollen":      [{"naam", "categorie", "definitie", "voorbeelden",
                       "argument": {"claim", "bron", "quote"}}],
      "mechanismen": [{"naam", "filter", "extra_filters": [], "mechanisme_type", "aard",
                       "definitie", "effect", "bron_rol", "doel_rol",
                       "argument": {"claim", "bron", "quote"}}],
      "overlap":     [{"mechanisme", "categorieen": [...], "motivatie"}]
    }

Gebruik:
    python3 scripts/theorie_indienen.py missies/bestuur_theorie.json             # droogloop
    python3 scripts/theorie_indienen.py missies/bestuur_theorie.json --uitvoeren
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scout_indienen import Api, Indiener  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
MAINTAINER_TOKEN = ROOT / "data" / "tokens" / "maxime.token"
BIJDRAGER_TOKEN = ROOT / "data" / "tokens" / "assistent.token"
DEFAULT_API = "http://127.0.0.1:5000"


def lees(query, args=()):
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return list(conn.execute(query, args))
    finally:
        conn.close()


class Theorie:
    def __init__(self, manifest: dict, api_m: Api | None, droog: bool):
        self.m = manifest
        self.api = api_m
        self.droog = droog
        self.rollen = {n: i for n, i in lees("SELECT name, id FROM roles WHERE NOT vervangen")}
        self.mechs = {n: i for n, i in lees("SELECT name, id FROM mechanisms WHERE NOT vervangen")}
        self.nieuw_rol: dict[str, int] = {}
        self.nieuw_mech: dict[str, int] = {}
        self._teller = 0
        self.fouten = 0

    def _post(self, pad, body, wat):
        if self.droog:
            self._teller -= 1
            print(f"    [droog] POST {pad}  {json.dumps(body, ensure_ascii=False)[:150]}")
            return {"id": self._teller}
        status, res = self.api.post(pad, body)
        if status not in (200, 201):
            print(f"    ✗ {wat} faalde ({status}): {res.get('error', res)} {res.get('fouten', '')}")
            self.fouten += 1
            return None
        return res

    def rollen_aanmaken(self):
        for r in self.m.get("rollen", []):
            if r["naam"] in self.rollen:
                print(f"▸ rol bestaat al: {r['naam']} (#{self.rollen[r['naam']]})")
                continue
            body = {"naam": r["naam"], "categorie": r["categorie"], "definitie": r["definitie"],
                    "voorbeelden": r.get("voorbeelden")}
            print(f"▸ rol: {r['naam']} ({r['categorie']})")
            res = self._post("/api/roles", body, f"rol {r['naam']}")
            if res:
                self.rollen[r["naam"]] = res["id"]
                self.nieuw_rol[r["naam"]] = res["id"]

    def _rol_id(self, naam):
        rid = self.rollen.get(naam)
        if rid is None:
            print(f"    ✗ onbekende rol '{naam}'")
            self.fouten += 1
        return rid

    def mechanismen_aanmaken(self):
        for mch in self.m.get("mechanismen", []):
            if mch["naam"] in self.mechs:
                print(f"▸ mechanisme bestaat al: {mch['naam']} (#{self.mechs[mch['naam']]})")
                continue
            src, tgt = self._rol_id(mch["bron_rol"]), self._rol_id(mch["doel_rol"])
            if src is None or tgt is None:
                continue
            body = {"naam": mch["naam"], "filter": mch["filter"],
                    "mechanisme_type": mch.get("mechanisme_type"),
                    "definitie": mch["definitie"], "effect": mch["effect"],
                    "aard": mch.get("aard", "direct"),
                    "source_role_id": src, "target_role_id": tgt,
                    "extra_filters": mch.get("extra_filters", [])}
            print(f"▸ mechanisme: {mch['naam']} ({mch['filter']}"
                  f"{' + ' + ', '.join(mch['extra_filters']) if mch.get('extra_filters') else ''}) "
                  f"{mch['bron_rol']} → {mch['doel_rol']}")
            res = self._post("/api/mechanisms", body, f"mechanisme {mch['naam']}")
            if res:
                self.mechs[mch["naam"]] = res["id"]
                self.nieuw_mech[mch["naam"]] = res["id"]

    def overlap(self):
        for o in self.m.get("overlap", []):
            mid = self.mechs.get(o["mechanisme"])
            if mid is None:
                print(f"    ✗ overlap: onbekend mechanisme '{o['mechanisme']}'")
                self.fouten += 1
                continue
            print(f"▸ overlap: {o['mechanisme']} + {', '.join(o['categorieen'])}")
            self._post(f"/api/mechanisms/{mid}/filters",
                       {"toevoegen": o["categorieen"], "motivatie": o["motivatie"]},
                       f"overlap {o['mechanisme']}")

    def argumenten_manifest(self) -> dict:
        """scout_indienen-manifest: bronnen + losse argumenten op de nieuwe elementen."""
        args = []
        for r in self.m.get("rollen", []):
            if r.get("argument") and r["naam"] in self.rollen:
                args.append({**r["argument"], "stance": "supporting", "methode": "verbatim_quote",
                             "doel": {"role_id": self.rollen[r["naam"]]}})
        for mch in self.m.get("mechanismen", []):
            if mch.get("argument") and mch["naam"] in self.mechs:
                args.append({**mch["argument"], "stance": "supporting", "methode": "verbatim_quote",
                             "doel": {"mechanism_id": self.mechs[mch["naam"]]}})
        return {"bronnen": self.m.get("bronnen", []), "argumenten": args}


def heeft_argument(doel_kolom, doel_id):
    return bool(lees(f"SELECT 1 FROM arguments WHERE {doel_kolom} = ? AND parent_argument_id "
                     "IS NULL AND stance = 'supporting' AND status != 'verworpen' LIMIT 1",
                     (doel_id,)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--uitvoeren", action="store_true", help="echt schrijven (default: droogloop)")
    ap.add_argument("--api", default=DEFAULT_API)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    droog = not args.uitvoeren
    api_m = api_b = None
    if not droog:
        for tok in (MAINTAINER_TOKEN, BIJDRAGER_TOKEN):
            if not tok.exists():
                sys.exit(f"Token ontbreekt: {tok}")
        api_m = Api(args.api, MAINTAINER_TOKEN.read_text().strip())
        api_b = Api(args.api, BIJDRAGER_TOKEN.read_text().strip())

    print(f"{'DROOGLOOP' if droog else 'UITVOEREN'} — {args.manifest.name}: "
          f"{len(manifest.get('rollen', []))} rollen, {len(manifest.get('mechanismen', []))} "
          f"mechanismen, {len(manifest.get('overlap', []))} overlap, "
          f"{len(manifest.get('bronnen', []))} bronnen")
    t = Theorie(manifest, api_m, droog)
    t.rollen_aanmaken()
    t.mechanismen_aanmaken()
    t.overlap()

    am = t.argumenten_manifest()
    # Een element dat al een steunend argument heeft (eerdere run), krijgt er geen tweede.
    am["argumenten"] = [a for a in am["argumenten"]
                        if droog or not heeft_argument(*next(iter(a["doel"].items())))]
    print(f"\n── bronnen + {len(am['argumenten'])} theorie-argumenten (account assistent) ──")
    ind = Indiener(api_b, droog)
    ind.bronnen(am["bronnen"])
    ind.losse_argumenten(am["argumenten"])

    print("\n── samenvatting ──")
    print(f"  nieuwe rollen: {len(t.nieuw_rol)}  nieuwe mechanismen: {len(t.nieuw_mech)}  "
          f"fouten: {t.fouten}")
    for k, v in ind.stats.items():
        if v:
            print(f"  {k}: {v}")
    if droog:
        print("\n(droogloop — er is niets geschreven. Voeg --uitvoeren toe.)")
    return 1 if (t.fouten or ind.stats["mislukt"]) else 0


if __name__ == "__main__":
    sys.exit(main())
