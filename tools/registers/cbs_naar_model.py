#!/usr/bin/env python3
"""Gemeentelijke indeling (CBS) → het model: welke provincie toezicht houdt op welke gemeente (2026-10-15).

cbs.py leest 'Gebieden in Nederland <jaar>': per gemeente de provincie waarin ze ligt. Gedeputeerde
Staten van die provincie houden toezicht op de gemeente (Gemeentewet; mechanisme
`interbestuurlijk_toezicht`, dat via een RfC in de theorie komt). Elke gemeente krijgt zo een
verband `controle` vanuit haar provincie. Alles via de REST-API onder `register-import`, met de
recordregel als citaat; scripts/registercheck.py controleert (cbs.controleer).

Koppelen, nooit op naam alleen: de gemeente via haar tooi-code (gm0225, uit het register van
overheidsorganisaties) of, waar het register er geen heeft, via de met de hand nagelopen oo-id in
koppelingen.json ('cbs_gemeenten'); de provincie via haar oo-id (cbs.PROVINCIES). Een provincie die het model
nog niet heeft (Utrecht en Noord-Brabant: het register noemt er geen CdK, zie README § Bekende
gaten) komt erbij onder dezelfde naam en rol als naar_model.py haar zou geven.

Zolang het mechanisme er niet is, plant dit niets en telt het wat wacht. Geen begin: de tabel
noemt er geen (registers_looptijd legt 'register_zonder_datum' vast).

Gebruik:
    python3 tools/registers/cbs.py haal
    python3 tools/registers/cbs_naar_model.py                 # droogloop
    python3 tools/registers/cbs_naar_model.py --indienen
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import cbs  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ROOT  # noqa: E402
from naar_model import TOKEN, Rest  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:cbs"
TOEZICHT_MECH = "interbestuurlijk_toezicht"


class Plan(tkm.Plan):
    def __init__(self, data: dict, conn: sqlite3.Connection, koppelingen: dict | None = None):
        super().__init__({"uitgave": data["uitgave"], "personen": {}, "records": {}}, conn, koppelingen)
        self.cbs = data
        rij = conn.execute("SELECT id FROM mechanisms WHERE name = ? AND NOT vervangen", (TOEZICHT_MECH,)).fetchone()
        self.toezicht = rij is not None
        if self.toezicht:
            self.mech[TOEZICHT_MECH] = rij[0]
        self.ext = {(s, w): e for e, s, w in conn.execute("""
            SELECT x.entity_id, x.stelsel, x.waarde FROM externe_ids x JOIN entities e ON e.id = x.entity_id
            WHERE NOT e.vervangen AND e.status <> 'afgewezen' AND x.stelsel IN ('oo', 'tooi')""")}
        self.oo_ref = {o["oo_id"]: eid for eid, o in self.oo_orgs.items()}
        self.gem_oo = cbs.gemeente_oo()

    def _provincie(self, rec: dict):
        oo_id = cbs.PROVINCIES[rec["provinciecode"]][1]
        if ("oo", oo_id) in self.ext:
            return ("bestaand", self.ext[("oo", oo_id)])
        if oo_id in self.oo_ref:
            return ("oo", self.oo_ref[oo_id])
        return None

    def maak(self):
        if not self.toezicht:
            self.tel[f"wacht op het mechanisme {TOEZICHT_MECH}"] = len(self.cbs["records"])
            return self
        for rec in self.cbs["records"].values():
            gem = self.ext.get(("tooi", rec["gemeentecode"].lower())) \
                or self.ext.get(("oo", self.gem_oo.get(rec["gemeentecode"], "")))
            if not gem:
                self._mis("cbs", rec, f"gemeente {rec['gemeentecode']} niet in het model (tooi of koppelingen.json)")
                continue
            prov = self._provincie(rec)
            if not prov:
                self._mis("cbs", rec, f"provincie {rec['provincie']} niet in het model en niet in het register")
                continue
            self._rel(prov, ("bestaand", gem), "controle", TOEZICHT_MECH, rec,
                      claim=f"Volgens het CBS (Gebieden in Nederland {self.cbs['jaar']}, tabel {self.cbs['tabel']}) "
                            f"ligt de gemeente {rec['gemeente']} in de provincie {rec['provincie']}.")
        return self.klem()


class Indiener(tkm.Indiener):
    def __init__(self, plan: Plan, rest, log=print):
        super().__init__(plan, rest, log, bron=cbs, cluster=CLUSTER)

    def bron(self) -> int:
        """De bewaarde uitgave als vindplaats ('file'); de url van de tabel staat in elke citatie."""
        status, res = self.rest("POST", "/api/sources", {
            "title": self.p.cbs["titel"], "source_type": "dataset", "publisher": cbs.UITGEVER,
            "date_published": self.p.uitgave, "cluster_key": self.cluster,
            "location": {"type": "file", "value": f"data/registers/cbs/cbs_{self.p.uitgave}.json"},
            "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
        if status not in (200, 201):
            raise SystemExit(f"bron registreren faalde: {status} {res}")
        return res["id"]

    def relaties(self, bron_id: int):
        # de citatie verwijst naar de tabel zelf, niet naar de catalogus
        self.reg = type("cbs_uitgave", (), {"BRON": cbs.BRON, "URL": self.p.cbs["url"]})
        super().relaties(bron_id)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave")
    ap.add_argument("--indienen", action="store_true")
    a = ap.parse_args()
    data = cbs.lees_uitgave(a.uitgave or cbs.uitgaven()[-1].stem.split("_", 1)[1])
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(data, conn, koppelingen).maak()
    nieuw = sorted({plan.oo_orgs[r[1]]["naam"] for x in plan.relaties for r in (x["bron"], x["doel"]) if r[0] == "oo"})
    print(json.dumps({"uitgave": plan.uitgave, "tabel": data["tabel"], "nieuwe_provincies": nieuw,
                      "relaties": len(plan.relaties), "voorbeeld": [r["regel"] for r in plan.relaties[:3]],
                      "overgeslagen": [f"{o.get('reden')}: {o.get('tekst', '')[:90]}" for o in plan.overgeslagen][:20],
                      "telling": dict(sorted(plan.tel.items()))}, ensure_ascii=False, indent=1))
    if not a.indienen:
        print("\n(droogloop — niets ingediend)")
        return
    if not plan.toezicht:
        raise SystemExit(f"Het mechanisme {TOEZICHT_MECH} staat nog niet in de theorie (RfC): niets ingediend")
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()))
    bron_id = ind.bron()
    ind.entiteiten()
    ind.relaties(bron_id)
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
