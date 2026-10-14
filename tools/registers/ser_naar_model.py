#!/usr/bin/env python3
"""SER-samenstelling → het model (polder, 2026-10-13).

ser.py leest "Wie zitten er in de SER?": welke werkgevers- en werknemersorganisaties zetels in de
Sociaal-Economische Raad hebben. Elke organisatie krijgt een verband `lidmaatschap` met de SER,
mechanisme `polderoverleg`, met het aantal zetels als functie, en de rol `sociale_partner` naast
wat ze al was (alleen aanvullen). Alles via de REST-API onder `register-import`, met de
recordregel als citaat; scripts/registercheck.py controleert (ser.controleer).

Koppelen, nooit op naam alleen: de organisatie staat onder haar naam in het model (exact, of
haar afkorting als 'FNV' in 'FNV (Federatie Nederlandse Vakbeweging)'); een organisatie die er
nog niet is, komt er alleen bij als ze met de hand getypeerd is in koppelingen.json
('ser_organisaties', zoals de VCP). De SER zelf via zijn externe id oo:28455002.

Geen personen (de pagina noemt geen datum per persoon) en geen begin van een zetel (de pagina
noemt er geen): registers_looptijd.py legt 'register_zonder_datum' vast.

Gebruik:
    python3 tools/registers/ser.py haal
    python3 tools/registers/ser_naar_model.py                 # droogloop
    python3 tools/registers/ser_naar_model.py --indienen
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import ser  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ROOT, sleutel  # noqa: E402
from naar_model import TOKEN, Rest  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:ser"
GROEP = {"Werkgeversorganisaties": "werkgeversorganisatie", "Werknemersorganisaties": "werknemersorganisatie"}


class Plan(tkm.Plan):
    def __init__(self, data: dict, conn: sqlite3.Connection, koppelingen: dict | None = None):
        super().__init__({"uitgave": data["uitgave"], "personen": {}, "records": {}}, conn, koppelingen)
        self.ser = data
        self.ser_typen = {sleutel(k): v for k, v in (koppelingen or {}).get("ser_organisaties", {}).items()
                          if not k.startswith("_")}
        self.mech.update(self._ids("mechanisms", ("polderoverleg",)))
        self.rol.update(self._ids("roles", ("sociale_partner",)))
        rij = conn.execute("SELECT entity_id FROM externe_ids WHERE stelsel = 'oo' AND waarde = ?",
                           (ser.SER_OO,)).fetchone()
        if not rij:
            raise SystemExit("De SER heeft nog geen externe id oo:28455002 — eerst naar_model.py (oo)")
        self.ser_id = rij[0]
        self.sociale_partners: set[int] = set()   # bestaande organisaties die de rol erbij krijgen

    def maak(self):
        doel = ("bestaand", self.ser_id)
        for rec in self.ser["records"].values():
            ref = None
            gevonden = self._bestaand(rec["org"], ruim=False)
            if gevonden and gevonden[0] > 0:
                reden = self._toegestaan(gevonden[0], "ser")
                if reden:
                    self._mis("ser", rec, reden)
                    continue
                ref = self._gekoppeld(rec, gevonden[0], gevonden[1], rec["org"])
                self.sociale_partners.add(gevonden[0])
            else:
                t = self.ser_typen.get(sleutel(rec["org"]))
                if not t:
                    self._mis("ser", rec, "niet in het model en niet getypeerd in koppelingen.json")
                    continue
                if self._bestaand(t["naam"], ruim=False):
                    eid = self._bestaand(t["naam"], ruim=False)[0]
                    ref = ("bestaand", eid)
                    self.sociale_partners.add(eid)
                else:
                    k = sleutel(t["naam"])
                    self.nieuwe_orgs[k] = {"naam": t["naam"], "type": t["type"], "rol": t["rol"],
                                           "beschrijving": f"{GROEP[rec['groep']].capitalize()} met zetels in de "
                                                           f"Sociaal-Economische Raad (ser.nl)."}
                    self.rol.update(self._ids("roles", (t["rol"],)))
                    self.koppelingen.append({"soort": "ser", "tekst": rec["regel"], "nieuw": t["naam"]})
                    ref = ("nieuw", k)
            n = rec["zetels"]
            self._rel(ref, doel, "lidmaatschap", "polderoverleg", rec,
                      functie=f"{GROEP[rec['groep']].capitalize()}, {n} zetel{'s' if n != 1 else ''}",
                      claim=f"Volgens de SER (ser.nl, uitgave {self.uitgave}) heeft {rec['org']} als "
                            f"{GROEP[rec['groep']]} {n} zetel{'s' if n != 1 else ''} in de Sociaal-Economische Raad.")
        return self.klem()


class Indiener(tkm.Indiener):
    def __init__(self, plan: Plan, rest, log=print):
        super().__init__(plan, rest, log, bron=ser, cluster=CLUSTER)

    def bron(self) -> int:
        """De bewaarde uitgave als vindplaats ('file'), niet de url: het model kent die pagina al
        als gewone bron (cluster 'sociaal_economische_raad'), en een bron met dezelfde url wordt
        hergebruikt of later samengevoegd — dan zou het citaat geen registercitaat meer zijn. De url
        staat in elke citatie (context)."""
        status, res = self.rest("POST", "/api/sources", {
            "title": ser.TITEL.format(uitgave=self.p.uitgave), "source_type": "dataset",
            "publisher": ser.UITGEVER, "date_published": self.p.uitgave, "cluster_key": self.cluster,
            "location": {"type": "file", "value": f"data/registers/ser/ser_{self.p.uitgave}.html"},
            "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
        if status not in (200, 201):
            raise SystemExit(f"bron registreren faalde: {status} {res}")
        return res["id"]

    def entiteiten(self):
        super().entiteiten()
        # de rol die de SER-zetel geeft, naast wat de organisatie al was (de server vult alleen aan)
        for eid in sorted(self.p.sociale_partners):
            status, res = self.rest("POST", f"/api/entities/{eid}/register", {"rollen": ["sociale_partner"]})
            self.tel["rol sociale_partner" if status == 200 else f"rol fout {status}"] += 1
            if status != 200:
                self.log(f"  ✗ rol sociale_partner #{eid}: {status} {res.get('error')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave")
    ap.add_argument("--indienen", action="store_true")
    a = ap.parse_args()
    data = ser.lees(ser.pad_van(a.uitgave) if a.uitgave else ser.uitgaven()[-1])
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(data, conn, koppelingen).maak()
    print(json.dumps({"uitgave": plan.uitgave, "nieuwe_organisaties": [o["naam"] for o in plan.nieuwe_orgs.values()],
                      "koppelingen": [f"{k['model']} ⟵ {k['uit']}" for k in plan.koppelingen if "model" in k],
                      "rol sociale_partner erbij": sorted(plan.org[i][0] for i in plan.sociale_partners),
                      "relaties": [f"{r['functie']}: {r['regel']}" for r in plan.relaties],
                      "telling": dict(sorted(plan.tel.items()))}, ensure_ascii=False, indent=1))
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
