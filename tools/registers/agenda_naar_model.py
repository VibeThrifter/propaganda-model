#!/usr/bin/env python3
"""Openbare agenda's van bewindspersonen → het model (eigenaar 2026-10-19: "hoe kunnen we deze
database gebruiken om interessante connecties te minen zonder te bedelven in onbelangrijke
afspraken?" … "als er een relatie uitkomt zet dit ook goed bij bronnen, en als het een relatie
versterkt kan dit ook als bron erbij").

agenda.py leest de afspraken; dit script kiest wat telt en dient het in, zonder AI:
  1. trechter: alleen gesprekken, ontvangsten en werkbezoeken, van één ministerie, met een
     organisatie die al in het model staat en die niet zelf overheid, partij, rechter,
     toezichthouder of medium is (een interview is geen lobby). De organisatie moet onder haar
     eigen naam in de tekst staan (common.noemt), zodat de registercheck hetzelfde vindt.
  2. sterkte is opvallendheid, geen aantal: lift = n(org, ministerie) / verwacht als de
     organisatie al haar afspraken gelijk over de ministeries had verdeeld. VNG die iedereen
     spreekt scoort laag; een bedrijf dat steeds bij hetzelfde ministerie zit hoog. Score =
     aantal dagen × log2(lift). Het rapport (data/registers/agenda/analyse.md + .json) rangschikt
     daarop, met de bewindspersoon die de organisatie het vaakst sprak.
  3. indienen (onder `register-import`, citaat = de recordregel, methode
     `officieel_register_scrape`, page `agenda/<uitgave>`, section = recordsleutel):
     - een bestaand `lobbyt`-verband organisatie → ministerie krijgt elke nog niet geciteerde
       afspraak als extra argument (de bron versterkt het verband);
     - anders een nieuw verband `lobbyt` → ministerie (mechanisme `departementale_lobby`, voor de
       koepels van mede-overheden `interbestuurlijk_overleg`) zodra er afspraken op minstens
       MIN_DAGEN verschillende dagen zijn; elke afspraak een argument.
     Hooguit MAX_PER_VERBAND nieuwe argumenten per verband per run (de nieuwste eerst).
De registercheck (stap 2b van de uurronde, agenda.controleer) toetst daarna elk argument.
  4. tips (--tips, los van het indienen): de afspraken zonder bekende organisatie laat een klein
     taalmodel de tegenpartij benoemen (gecachet in tips_cache.json); alleen namen die letterlijk
     in de afspraak staan, met dezelfde score, naar tips.md. Daar komt niets uit het model in.

Gebruik:
    python3 tools/registers/agenda_naar_model.py                    # droogloop + rapport
    python3 tools/registers/agenda_naar_model.py --tips             # + tiplijst onbekende tegenpartijen
    python3 tools/registers/agenda_naar_model.py --haal --indienen  # wekelijks (agent_schedule)
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import agenda  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ROOT, namen_van, sleutel  # noqa: E402
from naar_model import TOKEN, Rest  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:agenda"
CONTACT = {"Gesprek", "Ontvangst", "Werkbezoek"}
UITGESLOTEN_TYPES = {"overheidsinstelling", "partij", "rechterlijke_macht", "toezichthouder",
                     "mediaorganisatie", "omroep", "persbureau"}
KOEPELS = {"vng", "vereniging van nederlandse gemeenten", "ipo", "interprovinciaal overleg",
           "unie van waterschappen"}
MIN_DAGEN = 2
MAX_PER_VERBAND = 5
TOP = 50


class Plan(tkm.Plan):
    def __init__(self, records: dict[str, dict], conn: sqlite3.Connection, koppelingen: dict | None = None):
        super().__init__({"uitgave": max(r["_uitgave"] for r in records.values()), "personen": {},
                          "records": {}}, conn, koppelingen)
        self.records = records
        self.mech.update(self._ids("mechanisms", ("departementale_lobby", "interbestuurlijk_overleg")))
        self.ministerie = {w: e for e, w in conn.execute(
            "SELECT entity_id, waarde FROM externe_ids WHERE stelsel = 'oo'")}
        # organisaties die als lobbypartij kunnen tellen, onder hun eigen naam (geen metadata-afkorting:
        # de registercheck leest alleen de naam); een sleutel van twee organisaties telt niet
        per_sleutel: dict[str, set[int]] = defaultdict(set)
        for eid, (naam, typ, laag) in self.org.items():
            if eid < 0 or typ in UITGESLOTEN_TYPES or laag or self._toegestaan(eid, "agenda"):
                continue
            for k in namen_van(naam):
                if len(k) >= 3:
                    per_sleutel[k].add(eid)
        self.zoek: dict[str, list[tuple[list[str], int]]] = defaultdict(list)
        for k, ids in per_sleutel.items():
            if len(ids) == 1:
                self.zoek[k.split()[0]].append((k.split(), next(iter(ids))))
        bestaand = conn.execute("""
            SELECT r.id, r.source_id, r.target_id FROM relations r
            WHERE r.relation_type = 'lobbyt' AND NOT r.vervangen AND r.status <> 'afgewezen'""").fetchall()
        self.lobbyt = {(s, t): rid for rid, s, t in bestaand}
        self.geciteerd: dict[int, set[str]] = defaultdict(set)
        for rid, sec in conn.execute("""
                SELECT a.relation_id, c.section FROM citations c JOIN arguments a ON a.id = c.argument_id
                WHERE c.page LIKE 'agenda/%' AND a.relation_id IS NOT NULL"""):
            self.geciteerd[rid].add(sec)
        self.paren: dict[tuple[int, int], list[dict]] = defaultdict(list)
        self.argumenten: list[dict] = []

    def _organisaties(self, tekst: str) -> set[int]:
        """Organisaties die als hele woorden in de tekst staan; bij overlap wint de langste."""
        woorden = sleutel(tekst).split()
        treffers = []
        for i, w in enumerate(woorden):
            for kw, eid in self.zoek.get(w, ()):
                if woorden[i:i + len(kw)] == kw:
                    treffers.append((i, i + len(kw), eid))
        uit = set()
        for a, b, eid in treffers:
            if not any(a2 <= a and b <= b2 and (b2 - a2) > (b - a) for a2, b2, _ in treffers):
                uit.add(eid)
        return uit

    def maak(self):
        for rec in self.records.values():
            self.tel["afspraken"] += 1
            if rec["type"] not in CONTACT:
                self.tel["overgeslagen: geen gesprek/ontvangst/werkbezoek"] += 1
                continue
            oo_ids = {agenda.MINISTERIES.get(m) for m in rec["ministeries"]}
            if len(oo_ids) != 1 or None in oo_ids:
                self.tel["overgeslagen: ministerie onbekend of meer dan één"] += 1
                continue
            min_id = self.ministerie.get(next(iter(oo_ids)))
            if not min_id:
                self.tel["overgeslagen: ministerie niet in het model"] += 1
                continue
            orgs = self._organisaties(rec["tekst"])
            if not orgs:
                self.tel["contact zonder bekende organisatie"] += 1
                continue
            self.tel["contact met bekende organisatie"] += 1
            for eid in orgs:
                self.paren[(eid, min_id)].append(rec)
        self._scoor()
        self._kies()
        return self

    def _scoor(self):
        n_org, n_min = Counter(), Counter()
        for (o, m), recs in self.paren.items():
            n_org[o] += len(recs)
            n_min[m] += len(recs)
        totaal = sum(n_org.values()) or 1
        self.analyse = []
        for (o, m), recs in self.paren.items():
            dagen = len({r["datum"] for r in recs})
            lift = len(recs) * totaal / (n_org[o] * n_min[m])
            wie = Counter(r["bewindspersoon"] for r in recs).most_common(1)[0]
            self.analyse.append({
                "org_id": o, "organisatie": self.org[o][0], "type": self.org[o][1],
                "ministerie_id": m, "ministerie": self.org[m][0], "afspraken": len(recs), "dagen": dagen,
                "organisatie_totaal": n_org[o], "ministeries_gesproken": sum(1 for (o2, _m) in self.paren if o2 == o),
                "lift": round(lift, 2), "score": round(dagen * math.log2(max(lift, 1.0)), 2),
                "vooral_met": f"{wie[0]} ({wie[1]}×)",
                "van": min(r["datum"] for r in recs), "tot": max(r["datum"] for r in recs),
                "status": None, "voorbeeld": max(recs, key=lambda r: r["datum"])["tekst"][:240]})
        self.analyse.sort(key=lambda a: (-a["score"], -a["dagen"]))

    def _kies(self):
        for a in self.analyse:
            o, m = a["org_id"], a["ministerie_id"]
            rid = self.lobbyt.get((o, m))
            if rid is None and a["dagen"] < MIN_DAGEN:
                a["status"] = "te weinig (rapport)"
                self.tel["paar: te weinig afspraken"] += 1
                continue
            a["status"] = "versterkt" if rid else "nieuw"
            self.tel[f"paar: {a['status']}"] += 1
            recs = sorted(self.paren[(o, m)], key=lambda r: r["datum"], reverse=True)
            nieuw = [r for r in recs if r["sleutel"] not in self.geciteerd.get(rid, set())][:MAX_PER_VERBAND]
            mech = "interbestuurlijk_overleg" if set(namen_van(self.org[o][0])) & KOEPELS else "departementale_lobby"
            for r in nieuw:
                self.argumenten.append({"org": o, "ministerie": m, "relatie": rid, "mechanisme": mech,
                                        "van": a["van"], "rec": r})
            self.tel["argumenten gepland"] += len(nieuw)

    def rapport(self) -> str:
        regels = ["# Agenda's van bewindspersonen: opvallende lobbycontacten", "",
                  f"Afspraken: {self.tel['afspraken']} · met een bekende organisatie: "
                  f"{self.tel['contact met bekende organisatie']} · paren: {len(self.analyse)} "
                  f"(nieuw {self.tel['paar: nieuw']}, versterkt {self.tel['paar: versterkt']}, "
                  f"te weinig {self.tel['paar: te weinig afspraken']})", "",
                  "Score = dagen × log2(lift); lift = afspraken met dit ministerie ÷ verwacht bij een "
                  "gelijke verdeling.", "",
                  "| # | organisatie | ministerie | dagen | lift | score | vooral met | periode | status |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for i, a in enumerate(self.analyse[:TOP], 1):
            regels.append(f"| {i} | {a['organisatie']} ({a['type']}) | {a['ministerie']} | {a['dagen']} | "
                          f"{a['lift']} | {a['score']} | {a['vooral_met']} | {a['van']} – {a['tot']} | {a['status']} |")
        breed = sorted({a["org_id"]: a for a in self.analyse}.values(), key=lambda a: -a["ministeries_gesproken"])[:15]
        regels += ["", "## Spreekt (bijna) iedereen — lage lift, weinig zeggend", ""]
        regels += [f"- {a['organisatie']}: {a['organisatie_totaal']} afspraken bij {a['ministeries_gesproken']} ministeries"
                   for a in breed]
        return "\n".join(regels) + "\n"


class Indiener:
    def __init__(self, plan: Plan, rest, log=print):
        self.p, self.rest, self.log = plan, rest, log
        self.bronnen: dict[str, int] = {}
        self.relaties: dict[tuple[int, int], int] = dict(plan.lobbyt)
        self.tel = Counter()

    def bron(self, uitgave: str) -> int:
        if uitgave not in self.bronnen:
            data = agenda.lees_uitgave(uitgave)
            status, res = self.rest("POST", "/api/sources", {
                "title": data["titel"], "source_type": "dataset", "publisher": agenda.UITGEVER,
                "date_published": uitgave, "cluster_key": CLUSTER,
                "location": {"type": "url", "value": agenda.URL},
                "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
            if status not in (200, 201):
                raise SystemExit(f"bron registreren faalde: {status} {res}")
            self.bronnen[uitgave] = res["id"]
        return self.bronnen[uitgave]

    def indienen(self):
        for a in self.p.argumenten:
            rec, paar = a["rec"], (a["org"], a["ministerie"])
            rid = self.relaties.get(paar)
            if rid is None:
                status, res = self.rest("POST", "/api/relations", {
                    "source_id": a["org"], "target_id": a["ministerie"], "relation_type": "lobbyt",
                    "mechanism_id": self.p.mech[a["mechanisme"]], "active_from": a["van"]})
                if status != 201:
                    self.tel[f"relatie fout {status}"] += 1
                    self.log(f"  ✗ relatie {paar}: {status} {res.get('error')}")
                    continue
                rid = self.relaties[paar] = res["id"]
                self.tel["relatie nieuw"] += 1
            org = self.p.org[a["org"]][0]
            claim = (f"Volgens de openbare agenda had {rec['functie']} {rec['bewindspersoon']} "
                     f"({self.p.org[a['ministerie']][0]}) op {rec['datum']} een afspraak met {org}: {rec['tekst']}")
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": rid, "claim": claim, "stance": "supporting",
                "citations": [{"source_id": self.bron(rec["_uitgave"]), "quote": rec["regel"],
                               "methode": "officieel_register_scrape", "section": rec["sleutel"],
                               "page": f"{agenda.BRON}/{rec['_uitgave']}", "context": rec["url"]}]})
            self.tel["argument" if status == 201 else f"argument fout {status}"] += 1
            if status != 201:
                self.log(f"  ✗ argument {rec['sleutel']} op #{rid}: {status} {res.get('error')}")


TIPS_PROMPT = """Hieronder staan regels uit openbare agenda's van Nederlandse bewindspersonen, elk met een id.
Geef per regel de NIET-overheidsorganisaties waarmee de bewindspersoon spreekt of die hij bezoekt:
bedrijven, brancheclubs, vakbonden, ngo's, stichtingen, kennisinstellingen, adviesbureaus.
Geen ministeries, gemeenten, provincies, buitenlandse overheden, Kamer, partijen of media.
Geen personen. Gebruik de naam zoals hij in de regel staat (met afkorting als die er staat).
Antwoord ALLEEN met JSON: {"<id>": [{"naam": "...", "soort": "bedrijf|brancheclub|vakbond|ngo|kennis|advies|anders"}], ...}
Lege lijst als er geen is.

"""


def tips(plan: Plan, records: dict[str, dict], model: str = "haiku", batch: int = 80, log=print) -> list[dict]:
    """Afspraken zonder bekende organisatie: de tegenpartij laten benoemen (claude -p, gecachet per
    recordsleutel) en net zo rangschikken. Alleen een tiplijst; niets hiervan gaat het model in."""
    import subprocess
    cache_pad = agenda.MAP / "tips_cache.json"
    cache = json.loads(cache_pad.read_text(encoding="utf-8")) if cache_pad.exists() else {}
    # ook een bekende organisatie bij een ministerie dat (nog) niet in het model staat is geen tip
    kandidaten = [r for r in records.values() if r["type"] in CONTACT and not plan._organisaties(r["tekst"])
                  and len({agenda.MINISTERIES.get(m) for m in r["ministeries"]} - {None}) == 1]
    open_ = [r for r in kandidaten if r["sleutel"] not in cache]
    log(f"tips: {len(kandidaten)} afspraken zonder bekende organisatie, {len(open_)} nog te lezen")
    for i in range(0, len(open_), batch):
        deel = open_[i:i + batch]
        tekst = "\n".join(f"{r['sleutel'][9:]}\t{r['tekst'][:400]}" for r in deel)
        try:
            p = subprocess.run(["claude", "-p", TIPS_PROMPT + tekst, "--model", model],
                               capture_output=True, text=True, timeout=600, cwd=ROOT)
            uit = json.loads(p.stdout[p.stdout.find("{"):p.stdout.rfind("}") + 1])
        except (subprocess.TimeoutExpired, ValueError) as e:
            log(f"  ! batch {i // batch}: {e}")
            continue
        for r in deel:
            cache[r["sleutel"]] = uit.get(r["sleutel"][9:], [])
        cache_pad.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        log(f"  tips: {min(i + batch, len(open_))}/{len(open_)}")
    paren: dict[tuple[str, str], list[dict]] = defaultdict(list)
    naam_van: dict[str, Counter] = defaultdict(Counter)
    soort_van: dict[str, Counter] = defaultdict(Counter)
    for r in kandidaten:
        m = agenda.MINISTERIES.get(r["ministeries"][0])
        for o in cache.get(r["sleutel"], []):
            k = sleutel(o.get("naam"))
            if len(k) < 3 or not noemt_letterlijk(r["tekst"], o.get("naam")):
                continue   # verzonnen of verbasterd: alleen wat letterlijk in de afspraak staat
            naam_van[k][o["naam"]] += 1
            soort_van[k][o.get("soort") or "anders"] += 1
            paren[(k, m)].append(r)
    n_org, n_min = Counter(), Counter()
    for (k, m), recs in paren.items():
        n_org[k] += len(recs)
        n_min[m] += len(recs)
    totaal = sum(n_org.values()) or 1
    min_naam = {v: f"Ministerie van {n}" for n, v in agenda.MINISTERIES.items()}
    uit = []
    for (k, m), recs in paren.items():
        dagen = len({r["datum"] for r in recs})
        lift = len(recs) * totaal / (n_org[k] * n_min[m])
        uit.append({"organisatie": naam_van[k].most_common(1)[0][0], "soort": soort_van[k].most_common(1)[0][0],
                    "ministerie": min_naam[m], "afspraken": len(recs), "dagen": dagen,
                    "organisatie_totaal": n_org[k], "lift": round(lift, 2),
                    "score": round(dagen * math.log2(max(lift, 1.0)), 2),
                    "vooral_met": "{} ({}×)".format(*Counter(r["bewindspersoon"] for r in recs).most_common(1)[0]),
                    "van": min(r["datum"] for r in recs), "tot": max(r["datum"] for r in recs),
                    "voorbeeld": max(recs, key=lambda r: r["datum"])["tekst"][:240]})
    uit.sort(key=lambda a: (-a["score"], -a["dagen"]))
    return uit


def noemt_letterlijk(tekst: str, naam: str | None) -> bool:
    return bool(naam) and f" {sleutel(naam)} " in f" {sleutel(tekst)} "


def tips_rapport(rijen: list[dict]) -> str:
    regels = ["# Agenda's: opvallende tegenpartijen die nog niet in het model staan", "",
              "Tiplijst (een taalmodel benoemde de organisatie; alleen namen die letterlijk in de afspraak "
              "staan). Niets hiervan is ingediend.", "",
              "| # | organisatie | soort | ministerie | dagen | lift | score | vooral met | periode |",
              "|---|---|---|---|---|---|---|---|---|"]
    for i, a in enumerate([a for a in rijen if a["dagen"] >= MIN_DAGEN][:TOP], 1):
        regels.append(f"| {i} | {a['organisatie']} | {a['soort']} | {a['ministerie']} | {a['dagen']} | {a['lift']} | "
                      f"{a['score']} | {a['vooral_met']} | {a['van']} – {a['tot']} |")
    return "\n".join(regels) + "\n"


def alle_records() -> dict[str, dict]:
    uit = {}
    for p in agenda.uitgaven():
        d = agenda.lees(p)
        for s, r in d["records"].items():
            uit.setdefault(s, {**r, "_uitgave": d["uitgave"]})
    return uit


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--haal", action="store_true", help="eerst nieuwe weekpagina's ophalen")
    ap.add_argument("--indienen", action="store_true")
    ap.add_argument("--tips", action="store_true",
                    help="tegenpartijen die nog niet in het model staan laten benoemen (claude -p, gecachet) → tips.md")
    a = ap.parse_args()
    if a.haal:
        print(agenda.haal())
    records = alle_records()
    if not records:
        raise SystemExit("nog geen agenda-uitgave; eerst: python3 tools/registers/agenda.py haal")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(records, conn, koppelingen).maak()
    (agenda.MAP / "analyse.md").write_text(plan.rapport(), encoding="utf-8")
    (agenda.MAP / "analyse.json").write_text(json.dumps(plan.analyse, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(sorted(plan.tel.items())), ensure_ascii=False, indent=1))
    print(f"rapport: {agenda.MAP / 'analyse.md'}")
    if a.tips:
        rijen = tips(plan, records)
        (agenda.MAP / "tips.md").write_text(tips_rapport(rijen), encoding="utf-8")
        (agenda.MAP / "tips.json").write_text(json.dumps(rijen, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"tips: {agenda.MAP / 'tips.md'}")
    if not a.indienen:
        print("\n(droogloop — niets ingediend)")
        return
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()))
    ind.indienen()
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
