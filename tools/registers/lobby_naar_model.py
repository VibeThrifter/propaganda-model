#!/usr/bin/env python3
"""Lobbyistenregister van de Tweede Kamer → het model (Uitbreiding C, eigenaarsbesluit 2026-10-07).

Trap 3e (lobby.py leest de pdf): elke organisatie waarvoor iemand een vaste toegangspas tot de
Tweede Kamer heeft, krijgt `lobbyt` → Tweede Kamer met het mechanisme `lobbytoegang`; de
opdrachtgevers die het register noemt ("behartigt belangen voor") ook, met "via <bureau>" als
functie, maar alleen als ze al in het model staan (exacte naam; een opsomming als "Dak- en
thuisloze jongeren" is geen organisatie). Lobbyisten zelf worden geen knoop: het gaat om de
toegang van de organisatie. Organisaties koppelen zoals in tk_naar_model.py (bestaande naam, of
nieuw met rechtsvorm; partijen, fracties en de Kamer zelf nooit). Alles via de REST-API onder
`register-import`, met de recordregel als citaat; scripts/registercheck.py controleert.

Gebruik:
    python3 tools/registers/lobby_naar_model.py                 # droogloop
    python3 tools/registers/lobby_naar_model.py --indienen
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import lobby  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ROOT, sleutel  # noqa: E402
from naar_model import TOKEN, Rest  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:lobby"


class Plan(tkm.Plan):
    def __init__(self, data: dict, conn: sqlite3.Connection, koppelingen: dict | None = None):
        super().__init__({"uitgave": data["uitgave"], "personen": {}, "records": {}}, conn, koppelingen)
        self.lobby = data
        self.lobby_typen = {sleutel(k): v for k, v in (koppelingen or {}).get("lobby_organisaties", {}).items()
                            if not k.startswith("_")}
        self.mech.update(self._ids("mechanisms", ("lobbytoegang",)))
        self.rol.update(self._ids("roles", ("lobbyist",)))

    def _bekend_type(self, rec: dict) -> tuple | None:
        """Een werkgever zonder rechtsvorm in de naam, met de hand getypeerd in koppelingen.json
        ('lobby_organisaties'), komt erbij als hij nog niet in het model staat."""
        t = self.lobby_typen.get(sleutel(rec["werkzaam"]))
        if not t or self._bestaand(rec["werkzaam"], ruim=True) or self._bestaand(t["naam"], ruim=False):
            return None
        k = sleutel(t["naam"])
        self.nieuwe_orgs[k] = {"naam": t["naam"], "type": t["type"], "rol": t["rol"],
                               "bestuurslaag": t.get("bestuurslaag"),
                               "externe_ids": [{"stelsel": "oo", "waarde": t["oo"]}] if t.get("oo") else None,
                               "beschrijving": "Heeft een vaste toegangspas tot de Tweede Kamer (lobbyistenregister)."}
        self.rol.update(self._ids("roles", (t["rol"],)))
        self.koppelingen.append({"soort": "lobby", "tekst": rec["regel"], "nieuw": t["naam"], "type": t["type"]})
        return ("nieuw", k)

    def maak(self):
        kamer = ("bestaand", self.tweede_kamer)
        for rec in self.lobby["records"].values():
            claim = (f"Volgens het lobbyistenregister van de Tweede Kamer (bijgewerkt {self.uitgave}) heeft "
                     f"{rec['naam']}, werkzaam bij {rec['werkzaam']}, een vaste toegangspas tot de Tweede Kamer "
                     f"en behartigt belangen voor: {rec['belangen']}.")
            eigen = self._bekend_type(rec) or self._naamveld(rec["werkzaam"], "lobby", rec)
            if eigen:
                if eigen[0] == "nieuw" and sleutel(rec["belangen"]) not in ("idem", sleutel(rec["werkzaam"])):
                    self.nieuwe_orgs[eigen[1]]["rol"] = "lobbyist"  # een bureau dat voor anderen lobbyt
                self._rel(eigen, kamer, "lobbyt", "lobbytoegang", rec, claim,
                          functie=f"Vaste toegangspas ({rec['naam']})")
            if sleutel(rec["belangen"]) in ("idem", sleutel(rec["werkzaam"])):
                continue
            for item in re.split(r"[,;/]", tkm.zonder_haakjes(rec["belangen"])):
                item = tkm._eind(item.strip())
                if not item or sleutel(item) == sleutel(rec["werkzaam"]):
                    continue
                gevonden = self._bestaand(item, ruim=False)
                if not gevonden or self._toegestaan(gevonden[0], "lobby") or (eigen and eigen[1] == gevonden[0]):
                    continue
                ref = self._gekoppeld(rec, gevonden[0], "opdrachtgever", item)
                self._rel(ref, kamer, "lobbyt", "lobbytoegang", rec, claim,
                          functie=f"Via {rec['werkzaam']} (vaste toegangspas)")
        return self


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave")
    ap.add_argument("--indienen", action="store_true")
    a = ap.parse_args()
    data = lobby.lees(lobby.pad_van(a.uitgave) if a.uitgave else lobby.uitgaven()[-1])
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(data, conn, koppelingen).maak()
    print(json.dumps({"uitgave": plan.uitgave, "nieuwe_organisaties": [o["naam"] for o in plan.nieuwe_orgs.values()],
                      "koppelingen": [f"{k['model']} ⟵ {k['uit']}" for k in plan.koppelingen if "model" in k],
                      "relaties": len(plan.relaties), "telling": dict(sorted(plan.tel.items()))},
                     ensure_ascii=False, indent=1))
    if not a.indienen:
        print("\n(droogloop — niets ingediend)")
        return
    ind = tkm.Indiener(plan, Rest(TOKEN.read_text().strip()), bron=lobby, cluster=CLUSTER)
    bron_id = ind.bron()
    ind.entiteiten()
    ind.relaties(bron_id)
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
