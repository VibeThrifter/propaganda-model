#!/usr/bin/env python3
"""Europees Parlement (open data) → het model (Uitbreiding C, eigenaarsbesluit 2026-10-07).

Trap 3d (ep.py leest de uitgave): de zittende Nederlandse Europarlementariërs met hun zetel
(`ambt`/`kamerzetel` met het Europees Parlement) en hun nationale partij
(`lidmaatschap`/`partijlijn`). Via de REST-API onder `register-import`, met als citaat de
letterlijke recordregel, zodat scripts/registercheck.py het controleert.

Koppelen zoals bij de Kamer (tk_naar_model.py): eerst de externe id (`ep_mep`), dan de volledige
naam (ook zonder toevoeging tussen haakjes) bij precies één bestaande persoon met een passende rol;
anders een nieuwe persoon, met '(Europarlementariër)' erachter als de naam al van iemand anders is.
Het Europees Parlement zelf krijgt de externe id wikidata:Q8889 (de registercheck herkent het daaraan).

Gebruik:
    python3 tools/registers/ep_naar_model.py                 # droogloop
    python3 tools/registers/ep_naar_model.py --indienen
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import ep  # noqa: E402
from common import ROOT, sleutel  # noqa: E402
from naar_model import PASSENDE_ROLLEN, TOKEN, Rest  # noqa: E402
from tk_naar_model import zonder_haakjes  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:ep"


class Plan:
    def __init__(self, data: dict, conn: sqlite3.Connection):
        self.d, self.conn, self.uitgave = data, conn, data["uitgave"]
        self.mech = {n: i for n, i in conn.execute(
            "SELECT name, id FROM mechanisms WHERE NOT vervangen AND name IN ('kamerzetel', 'partijlijn')")}
        self.rol = {n: i for n, i in conn.execute("SELECT name, id FROM roles WHERE NOT vervangen AND name = 'politicus'")}
        if len(self.mech) < 2 or not self.rol:
            raise SystemExit("Theorie ontbreekt nog: kamerzetel, partijlijn of de rol politicus")
        rij = conn.execute("SELECT entity_id FROM externe_ids WHERE stelsel = 'wikidata' AND waarde = ?",
                           (ep.EP_WIKIDATA,)).fetchone() or conn.execute(
            "SELECT id FROM entities WHERE name = 'Europees Parlement' AND NOT vervangen").fetchone()
        if not rij:
            raise SystemExit("Het Europees Parlement staat nog niet in het model")
        self.parlement = rij[0]
        self.partij_id = {n: i for i, n in conn.execute(
            "SELECT id, name FROM entities WHERE type = 'partij' AND status = 'goedgekeurd' AND NOT vervangen")}
        self.pm_personen: dict[str, list[tuple[int, str | None]]] = {}
        for i, n, rol in conn.execute("""
                SELECT e.id, e.name, r.name FROM entities e LEFT JOIN roles r ON r.id = e.primary_role_id
                WHERE e.type = 'persoon' AND NOT e.vervangen AND e.status <> 'afgewezen'"""):
            for k in {sleutel(n), sleutel(zonder_haakjes(n))}:
                self.pm_personen.setdefault(k, []).append((i, rol))
        self.ext = {w: e for e, w in conn.execute("SELECT entity_id, waarde FROM externe_ids WHERE stelsel = 'ep_mep'")}
        self.alle_namen = {sleutel(n) for (n,) in conn.execute("SELECT name FROM entities")}
        self.personen: dict[str, dict] = {}
        self.relaties: list[dict] = []
        self.overgeslagen: list[dict] = []
        self.tel = Counter()

    def maak(self):
        for pid, p in self.d["personen"].items():
            treffers = {i for i, rol in self.pm_personen.get(sleutel(p["naam"]), []) if rol in PASSENDE_ROLLEN}
            bestaand = self.ext.get(pid) or (next(iter(treffers)) if len(treffers) == 1 else None)
            naam = p["naam"]
            if not bestaand and sleutel(naam) in self.alle_namen:
                naam = f"{naam} (Europarlementariër)"
            self.personen[pid] = {"naam": naam, "bestaand": bestaand,
                                  "beschrijving": f"Lid van het Europees Parlement voor {p['partij'] or 'Nederland'}"
                                                  f"{', fractie ' + p['fractie'] if p['fractie'] else ''} "
                                                  f"(open data Europees Parlement)."}
            rec = self.d["records"][f"persoon:{pid}"]
            self._rel(("persoon", pid), ("bestaand", self.parlement), "ambt", "kamerzetel", rec,
                      functie=f"Europarlementariër{' (' + p['fractie'] + ')' if p['fractie'] else ''}",
                      start=p["van"],
                      claim=f"Volgens de open data van het Europees Parlement (uitgave {self.uitgave}) is "
                            f"{p['naam']} lid van het Europees Parlement voor Nederland"
                            f"{' (fractie ' + p['fractie'] + ')' if p['fractie'] else ''}"
                            f"{', sinds ' + p['van'] if p['van'] else ''}.")
            partij = ep.partij_van(p)
            if partij and partij in self.partij_id:
                self._rel(("bestaand", self.partij_id[partij]), ("persoon", pid), "lidmaatschap", "partijlijn", rec,
                          claim=f"Volgens de open data van het Europees Parlement (uitgave {self.uitgave}) zit "
                                f"{p['naam']} er namens {p['partij']}.")
            else:
                self.overgeslagen.append({"naam": p["naam"], "reden": f"geen partij in het model voor '{p['partij']}'"})
        return self

    def _rel(self, bron, doel, rtype, mech, rec, claim, functie=None, start=None):
        self.relaties.append({"bron": bron, "doel": doel, "type": rtype, "mechanisme": mech, "functie": functie,
                              "start": start, "sleutel": rec["sleutel"], "regel": rec["regel"], "claim": claim})
        self.tel[f"{rtype}/{mech}"] += 1


class Indiener:
    def __init__(self, plan: Plan, rest, log=print):
        self.p, self.rest, self.log = plan, rest, log
        self.ent: dict[str, int] = {}
        self.bestaande_relaties = {tuple(r) for r in plan.conn.execute(
            "SELECT source_id, target_id, relation_type FROM relations WHERE NOT vervangen AND status <> 'afgewezen'")}
        self.tel = Counter()

    def bron(self) -> int:
        status, res = self.rest("POST", "/api/sources", {
            "title": ep.TITEL.format(uitgave=self.p.uitgave), "source_type": "dataset",
            "publisher": ep.UITGEVER, "date_published": self.p.uitgave, "cluster_key": CLUSTER,
            "location": {"type": "url", "value": ep.URL},
            "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
        if status not in (200, 201):
            raise SystemExit(f"bron registreren faalde: {status} {res}")
        return res["id"]

    def entiteiten(self):
        status, res = self.rest("POST", f"/api/entities/{self.p.parlement}/register", {
            "externe_ids": [{"stelsel": "wikidata", "waarde": ep.EP_WIKIDATA}], "bestuurslaag": "eu"})
        self.tel["parlement gekoppeld" if status == 200 else f"parlement koppelen {status}"] += 1
        for pid, p in self.p.personen.items():
            ids = [{"stelsel": "ep_mep", "waarde": pid}]
            if p["bestaand"]:
                status, res = self.rest("POST", f"/api/entities/{p['bestaand']}/register", {"externe_ids": ids})
                self.tel["persoon gekoppeld" if status == 200 else f"persoon koppelen {status}"] += 1
                if status == 200:
                    self.ent[pid] = p["bestaand"]
                else:
                    self.log(f"  ✗ koppelen {p['naam']}: {status} {res.get('error')}")
                continue
            status, res = self.rest("POST", "/api/entities", {
                "name": p["naam"], "type": "persoon", "primary_role_id": self.p.rol["politicus"],
                "description": p["beschrijving"], "externe_ids": ids})
            if status in (201, 409) and (res.get("id") or res.get("entity_id")):
                self.ent[pid] = res.get("id") or res.get("entity_id")
                self.tel["persoon nieuw" if status == 201 else "persoon bestond (externe id)"] += 1
            else:
                self.tel[f"persoon fout {status}"] += 1
                self.log(f"  ✗ {p['naam']}: {status} {res.get('error')}")

    def relaties(self, bron_id: int):
        for r in self.p.relaties:
            s, t = (self.ent.get(x[1]) if x[0] == "persoon" else x[1] for x in (r["bron"], r["doel"]))
            if not s or not t:
                self.tel["relatie zonder eindpunt"] += 1
                continue
            if (s, t, r["type"]) in self.bestaande_relaties:
                self.tel["relatie bestond"] += 1
                continue
            body = {"source_id": s, "target_id": t, "relation_type": r["type"], "mechanism_id": self.p.mech[r["mechanisme"]]}
            for veld, waarde in (("functie", r["functie"]), ("active_from", r["start"])):
                if waarde:
                    body[veld] = waarde
            status, res = self.rest("POST", "/api/relations", body)
            if status != 201:
                self.tel[f"relatie fout {status}"] += 1
                self.log(f"  ✗ relatie {r['type']} {s}→{t}: {status} {res.get('error')}")
                continue
            self.bestaande_relaties.add((s, t, r["type"]))
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": res["id"], "claim": r["claim"], "stance": "supporting",
                "citations": [{"source_id": bron_id, "quote": r["regel"], "methode": "officieel_register_scrape",
                               "section": r["sleutel"], "page": f"{ep.BRON}/{self.p.uitgave}", "context": ep.URL}]})
            self.tel["relatie nieuw" if status == 201 else f"argument fout {status}"] += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave")
    ap.add_argument("--indienen", action="store_true")
    a = ap.parse_args()
    data = ep.lees(ep.pad_van(a.uitgave) if a.uitgave else ep.uitgaven()[-1])
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    plan = Plan(data, conn).maak()
    print(json.dumps({"uitgave": plan.uitgave, "leden": len(plan.personen),
                      "gekoppeld": {p["naam"]: p["bestaand"] for p in plan.personen.values() if p["bestaand"]},
                      "relaties": dict(plan.tel), "overgeslagen": plan.overgeslagen}, ensure_ascii=False, indent=1))
    if not a.indienen:
        print("\n(droogloop — niets ingediend)")
        return
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()))
    bron_id = ind.bron()
    ind.entiteiten()
    ind.relaties(bron_id)
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
