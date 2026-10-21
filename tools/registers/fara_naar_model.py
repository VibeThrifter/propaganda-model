#!/usr/bin/env python3
"""FARA (Foreign Agents Registration Act) → het model, alleen opdrachtgevers uit het Koninkrijk
(eigenaar 2026-10-20, onderzoek OpenSecrets als bron en methodiek).

fara.py leest de uitgave (bulkdata van het Amerikaanse ministerie van Justitie, gefilterd op
Nederland, de Nederlandse Antillen, Aruba, Curaçao, Sint Maarten en Bonaire). Dit script kiest wat
het model iets zegt en plant, zonder AI:

  - een opdrachtgever die al in het model staat (met de hand nagelopen: fara.PRINCIPALEN) en een
    belanghebbende is (bedrijf, brancheclub, ngo, stichting) ↔ de Amerikaanse agent:
    `adviseur` (richtingloos), mechanisme `belangenbehartiging` (belanghebbende → ingehuurde
    lobbyist/pr), met de registratie- en einddatum van de opdrachtgever als looptijd;
  - de agent: een bestaande knoop via de externe id 'fara' of fara.REGISTRANTEN (Hill and Knowlton
    Strategies → Hill+Knowlton), anders nieuw als de rechtsvorm in de naam staat (Inc., LLC, LLP,
    P.C., Ltd., Corporation, Company), type pr_bureau of bedrijf, rol `lobbyist`, externe id
    'fara' = het registratienummer. Een agent die een persoon is ('Jansen, Leendert') nooit.
  - bestaat het verband al (zelfde paar), dan alleen een extra argument met de recordregel.
Wat NIET gepland wordt en waarom (het rapport telt het):
  - een overheid als opdrachtgever (ministeries, ambassade, NFIA, DNB, gemeenten, TU Delft):
    THEORIE ONTBREEKT — er is geen mechanisme voor een Nederlandse overheid die in het buitenland
    een agent inhuurt (publieke diplomatie, investeringswerving, nation branding);
  - de beïnvloeding van de Amerikaanse overheid zelf: THEORIE ONTBREEKT (geen rol voor een
    buitenlandse overheid als doel, geen mechanisme 'lobby bij een buitenlandse overheid');
  - opdrachtgevers die niet (of alleen als voorganger) in het model staan: tiplijst;
  - registraties die vóór MIN_EIND (1985) eindigden: alleen het rapport (vooral reclame, films en
    voorlichting uit 1942–1984, geen lobby in de zin van het mechanisme).
Koppel nooit op naam alleen: een gelijke naam zonder vermelding in fara.PRINCIPALEN/REGISTRANTEN
is een tip, geen koppeling.

Score (rapport, top-30): actualiteit × log2(2 + jaren) × (2 als de agent al in het model staat:
een brug naar het Nederlandse netwerk) × (1 + 0,25 per andere Nederlandse opdrachtgever van
dezelfde agent) × (1 + log2(1 + documenten)/4).

Gebruik:
    python3 tools/registers/fara_naar_model.py              # droogloop + rapport
    python3 tools/registers/fara_naar_model.py --haal       # eerst een nieuwe uitgave
    python3 tools/registers/fara_naar_model.py --indienen   # NIET zonder het stelsel 'fara' in
                                                            # server.EXTERNE_STELSELS en 'fara' in
                                                            # registercheck.BRONNEN
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import fara  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ontleed_naam, sleutel  # noqa: E402
from naar_model import TOKEN, Rest  # noqa: E402

DB_PATH = tkm.ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:fara"
STELSEL = "fara"
TOP = 30
MIN_EIND = 1985   # registraties die vóór dit jaar eindigden: alleen het rapport (vooral reclame en voorlichting)
STAAT_TYPES = {"overheidsinstelling", "toezichthouder", "rechterlijke_macht"}
US_RECHTSVORM = re.compile(r"(?:,|\s)\s*(?:Inc|Incorporated|LLC|L\.L\.C|LLP|L\.L\.P|P\.C|PLLC|P\.L\.L\.C|Ltd|Limited|"
                           r"Corporation|Corp|Company|Co)\.?\s*(?:\(.*\))?$", re.I)
PR_WOORDEN = re.compile(r"public relations|public affairs|communicat|\bpr\b|advertis|marketing|media|"
                        r"strateg|knowlton|edelman|ogilvy|burson|ketchum|shandwick|ruder finn|golin|"
                        r"precis|films?\b", re.I)
AFFILIATIE = {"bestuurder", "adviseur", "lidmaatschap", "personeel", "dienstverband", "financiering",
              "lobbyt", "woordvoerder_van"}


def _jaar(d: str | None) -> int | None:
    return int(d[:4]) if d and d[:4].isdigit() else None


class Plan(tkm.Plan):
    def __init__(self, data: dict, conn: sqlite3.Connection, koppelingen: dict | None = None):
        super().__init__({"uitgave": data["uitgave"], "personen": {}, "records": {}}, conn, koppelingen)
        self.f = data
        self.mech.update(self._ids("mechanisms", ("belangenbehartiging",)))
        self.rol.update(self._ids("roles", ("lobbyist",)))
        self.ext_fara = {w: e for e, w in conn.execute(
            "SELECT entity_id, waarde FROM externe_ids WHERE stelsel = ?", (STELSEL,))}
        self.bestaande_paren: dict[tuple[int, int], list[tuple[int, str, str]]] = defaultdict(list)
        for rid, s, t, typ, st in conn.execute(
                "SELECT id, source_id, target_id, relation_type, status FROM relations "
                "WHERE NOT vervangen AND status <> 'afgewezen'"):
            self.bestaande_paren[(min(s, t), max(s, t))].append((rid, typ, st))
        self.al_geciteerd = {(r, sec) for r, sec in conn.execute("""
            SELECT a.relation_id, c.section FROM citations c JOIN arguments a ON a.id = c.argument_id
            WHERE c.page LIKE 'fara/%' AND a.relation_id IS NOT NULL""")}
        self.persoon_namen: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for i, n in conn.execute("SELECT id, name FROM entities WHERE type = 'persoon' AND NOT vervangen "
                                 "AND status <> 'afgewezen'"):
            self.persoon_namen[sleutel(tkm.zonder_haakjes(n))].append((i, n))
        self.agenten: dict[str, dict] = {}       # regnr → plan voor de agent
        self.kandidaten: list[dict] = []         # elke gekoppelde opdrachtgever, ook niet gepland
        self.extra_bron: list[dict] = []
        self.tips: list[dict] = []

    # ── opdrachtgever en agent ─────────────────────────────────────────────
    def _principaal(self, rec: dict) -> int | None:
        k = fara.PRINCIPALEN.get(sleutel(rec["principaal"]))
        if not k:
            gok = self._bestaand(tkm.zonder_haakjes(rec["principaal"]), ruim=False)
            if gok:
                self.tips.append({"soort": "opdrachtgever met gelijke naam (niet gekoppeld)",
                                  "fara": rec["principaal"], "model": self.org[gok[0]][0], "id": gok[0],
                                  "sleutel": rec["sleutel"]})
            self._mis("opdrachtgever", rec, "niet in fara.PRINCIPALEN (niet in het model of niet nagelopen)")
            return None
        eid, naam, _reden = k
        if eid not in self.org or self.org[eid][0] != naam:
            self._mis("opdrachtgever", rec, f"knoop #{eid} '{naam}' bestaat niet (meer) onder die naam")
            return None
        return eid

    def soort_principaal(self, eid: int) -> str:
        naam, typ, laag = self.org[eid]
        return "staat" if typ in STAAT_TYPES or laag else "belang"

    def _agent(self, rec: dict) -> tuple | None:
        nr = rec["regnr"]
        if nr in self.agenten:
            return self.agenten[nr]["ref"]
        r = self.f["records"].get(f"registrant:{nr}") or {"naam": rec["registrant"], "van": None, "tot": None}
        naam = r["naam"] or rec["registrant"]
        ref, hoe = None, None
        if nr in fara.REGISTRANTEN:
            eid, mnaam, _ = fara.REGISTRANTEN[nr]
            if eid in self.org and self.org[eid][0] == mnaam:
                ref, hoe = ("bestaand", eid), "fara.REGISTRANTEN"
        elif nr in self.ext_fara:
            ref, hoe = ("bestaand", self.ext_fara[nr]), "externe id fara"
        if ref is None:
            if not US_RECHTSVORM.search(naam):
                self._mis("agent", rec, "agent is een persoon of heeft geen rechtsvorm in de naam")
                self.agenten[nr] = {"ref": None}
                return None
            if sleutel(naam) in self.alle_namen or self._bestaand(naam, ruim=False):
                self.tips.append({"soort": "agent met gelijke naam in het model (niet gekoppeld)", "fara": naam,
                                  "regnr": nr})
                self._mis("agent", rec, "een knoop met dezelfde naam bestaat al: met de hand nalopen")
                self.agenten[nr] = {"ref": None}
                return None
            k = f"fara:{nr}"
            self.nieuwe_orgs[k] = {
                "naam": naam, "type": "pr_bureau" if PR_WOORDEN.search(naam) else "bedrijf", "rol": "lobbyist",
                "externe_ids": [{"stelsel": STELSEL, "waarde": nr}], "active_from": r.get("van"),
                "beschrijving": f"Agent van buitenlandse opdrachtgevers in de VS, geregistreerd onder de Foreign Agents "
                                f"Registration Act (registratie {nr})."}
            ref, hoe = ("nieuw", k), "nieuw (rechtsvorm)"
        else:
            self.koppelingen.append({"soort": "agent", "tekst": naam, "id": ref[1], "model": self.org[ref[1]][0],
                                     "hoe": hoe})
        self.agenten[nr] = {"ref": ref, "naam": naam, "hoe": hoe}
        return ref

    # ── plannen ────────────────────────────────────────────────────────────
    def maak(self):
        recs = [r for r in self.f["records"].values() if r["soort"] == "principaal"]
        nl_per_agent: dict[str, set[int]] = defaultdict(set)
        gekoppeld = []
        for rec in recs:
            pid = self._principaal(rec)
            if pid:
                gekoppeld.append((rec, pid))
                nl_per_agent[rec["regnr"]].add(pid)
        for rec, pid in gekoppeld:
            agent = self._agent(rec)
            soort = self.soort_principaal(pid)
            sc = self._score(rec, agent, len(nl_per_agent[rec["regnr"]]))
            kand = {**sc, "sleutel": rec["sleutel"], "opdrachtgever": self.org[pid][0], "fara_naam": rec["principaal"],
                    "agent": self.agenten.get(rec["regnr"], {}).get("naam") or rec["registrant"],
                    "agent_in_model": bool(agent and agent[0] == "bestaand"), "regnr": rec["regnr"],
                    "van": rec["van"], "tot": rec["tot"], "soort": soort, "status": None, "citaat": rec["regel"]}
            self.kandidaten.append(kand)
            if soort == "staat":
                kand["status"] = "theorie ontbreekt (overheid als opdrachtgever)"
                self._mis("opdrachtgever", rec, "theorie ontbreekt: overheid als opdrachtgever van een buitenlandse agent")
                continue
            if not agent:
                kand["status"] = "agent niet te koppelen (persoon of geen rechtsvorm)"
                continue
            if rec["tot"] and not rec["datumfout"] and (_jaar(rec["tot"]) or 0) < MIN_EIND:
                kand["status"] = f"historisch (geëindigd vóór {MIN_EIND}): alleen rapport"
                self._mis("opdrachtgever", rec, f"historisch: geëindigd vóór {MIN_EIND}")
                continue
            eind = rec["tot"]
            if rec["datumfout"]:
                eind = None
                self.tel["einddatum vóór begin (FARA-fout): einde weggelaten"] += 1
            claim = (f"Volgens het FARA-register van het Amerikaanse ministerie van Justitie (uitgave {self.uitgave}) "
                     f"stond {kand['agent']} (registratie {rec['regnr']}) geregistreerd als agent van "
                     f"{rec['principaal']} ({self.org[pid][0]}), {fara._periode(rec['van'], rec['tot'])}.")
            n = len(self.relaties)
            self._rel(("bestaand", pid), agent, "adviseur", "belangenbehartiging", rec, claim,
                      functie=f"FARA-agent voor {rec['principaal']} (registratie {rec['regnr']})"[:200],
                      start=rec["van"], eind=eind)
            kand["status"] = "gepland" if len(self.relaties) > n else "zelfde verband, ander record"
            if len(self.relaties) > n:
                self.relaties[-1]["score"] = sc["score"]
        self._extra_bron()
        self._zelfcontrole()
        self._personen()
        return self.klem()

    def _score(self, rec: dict, agent: tuple | None, n_nl: int) -> dict:
        # een einddatum vóór het begin (FARA-fout) telt als een registratie van hooguit een jaar
        eind = _jaar(rec["tot"]) if not rec["datumfout"] else _jaar(rec["van"])
        ref = eind or int(self.uitgave[:4])
        actueel = 1.0 if not rec["tot"] else (0.9 if ref >= 2016 else 0.6 if ref >= 2000 else 0.35 if ref >= 1980 else 0.15)
        jaren = max(0, ref - (_jaar(rec["van"]) or ref))
        brug = 2.0 if agent and agent[0] == "bestaand" else 1.0
        hub = 1 + 0.25 * max(0, n_nl - 1)
        docs = 1 + math.log2(1 + rec["documenten"]) / 4
        return {"score": round(actueel * math.log2(2 + jaren) * brug * hub * docs, 3), "jaren": jaren,
                "documenten": rec["documenten"], "nl_opdrachtgevers_bij_agent": n_nl}

    def _extra_bron(self):
        blijven = []
        for r in self.relaties:
            s = r["bron"][1]
            t = r["doel"][1] if r["doel"][0] == "bestaand" else None
            bestaand = [x for x in self.bestaande_paren.get((min(s, t), max(s, t)), []) if x[1] in AFFILIATIE] if t else []
            if not bestaand:
                blijven.append(r)
                continue
            rel_id, typ, status = sorted(bestaand, key=lambda x: (x[1] != r["type"], x[0]))[0]
            self.tel[f"{r['type']}/{r['mechanisme']}"] -= 1
            if (rel_id, r["sleutel"]) in self.al_geciteerd:
                self.tel["bestaand verband, dit record al geciteerd"] += 1
                continue
            self.extra_bron.append({**r, "relation_id": rel_id, "bestaand_type": typ, "bestaand_status": status})
            self.tel["bestaand verband: extra bron"] += 1
        self.relaties = blijven

    def _zelfcontrole(self):
        """Wat de registercheck zou afkeuren, wordt niet gepland (dezelfde fara.controleer)."""
        def ok(r):
            rec = self.f["records"][r["sleutel"]]
            agent_naam = (self.nieuwe_orgs[r["doel"][1]]["naam"] if r["doel"][0] == "nieuw" else self.org[r["doel"][1]][0])
            eind = [{"id": r["bron"][1], "name": self.org[r["bron"][1]][0], "ids": set()},
                    {"id": None, "name": agent_naam, "ids": {(STELSEL, rec["regnr"])}}]
            reden = fara.controleer(self.f, r["sleutel"], rec, r["type"], eind)
            if reden:
                self._mis("opdrachtgever", rec, f"registercheck zou afkeuren: {reden}")
                if "relation_id" not in r:
                    self.tel[f"{r['type']}/{r['mechanisme']}"] -= 1
            return not reden
        self.relaties = [r for r in self.relaties if ok(r)]
        self.extra_bron = [r for r in self.extra_bron if ok(r)]
        nodig = {r["doel"][1] for r in self.relaties if r["doel"][0] == "nieuw"}
        self.nieuwe_orgs = {k: v for k, v in self.nieuwe_orgs.items() if k in nodig}

    def _personen(self):
        """Short forms bij een registratie met een Nederlandse opdrachtgever: alleen een tip als de volledige
        naam precies die van een persoon in het model is (nooit een koppeling: geen tweede kenmerk)."""
        for r in self.f["records"].values():
            if r["soort"] != "shortform":
                continue
            n = ontleed_naam(r["naam"])
            if not n["volledig"]:
                continue
            for i, naam in self.persoon_namen.get(sleutel(r["naam"]), []):
                self.tips.append({"soort": "persoon met dezelfde volledige naam (short form; niet gekoppeld)",
                                  "fara": r["naam"], "model": naam, "id": i, "regnr": r["regnr"], "sleutel": r["sleutel"]})


class Indiener(tkm.Indiener):
    def entiteiten(self):
        for nr, a in self.p.agenten.items():
            ref = a.get("ref")
            if ref and ref[0] == "bestaand" and a.get("hoe") == "fara.REGISTRANTEN":
                status, res = self.rest("POST", f"/api/entities/{ref[1]}/register",
                                        {"externe_ids": [{"stelsel": STELSEL, "waarde": nr}]})
                self.tel["agent gekoppeld" if status == 200 else f"agent koppelen {status}"] += 1
        self.p.personen = {}
        super().entiteiten()

    def extra_bronnen(self, bron_id: int):
        for r in self.p.extra_bron:
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": r["relation_id"], "claim": r["claim"], "stance": "supporting",
                "citations": [{"source_id": bron_id, "quote": r["regel"], "methode": "officieel_register_scrape",
                               "section": r["sleutel"], "page": f"{fara.BRON}/{self.p.uitgave}",
                               "context": fara.URL}]})
            self.tel["extra bron" if status == 201 else f"extra bron fout {status}"] += 1


# ── rapport ─────────────────────────────────────────────────────────────────
def rapport(plan: Plan) -> dict:
    recs = [r for r in plan.f["records"].values() if r["soort"] == "principaal"]
    per_land = Counter(r["land"] for r in recs)
    per_decennium = Counter(f"{(_jaar(r['van']) or 0) // 10 * 10}s" for r in recs)
    lopend = [r for r in recs if not r["tot"]]
    sinds2000 = [r for r in recs if (_jaar(r["tot"]) or 9999) >= 2000]
    niet = Counter(r["principaal"] for r in recs if not fara.PRINCIPALEN.get(sleutel(r["principaal"])))
    kand = sorted(plan.kandidaten, key=lambda k: -k["score"])
    agent_hubs = Counter()
    for k in plan.kandidaten:
        agent_hubs[(k["agent"], k["regnr"])] += 1
    return {
        "uitgave": plan.uitgave, "bulk": plan.f["bulk"],
        "dekking": {
            "opdrachtgevers_koninkrijk": len(recs), "verschillende_namen": len({sleutel(r["principaal"]) for r in recs}),
            "registraties": len({r["regnr"] for r in recs}), "lopend": len(lopend),
            "lopend_lijst": [r["regel"] for r in lopend], "beeindigd_2000_of_later": len(sinds2000),
            "per_land": dict(per_land.most_common()), "per_decennium_begin": dict(sorted(per_decennium.items())),
            "documenten_bij_nl_opdrachtgevers": sum(r["documenten"] for r in recs),
            "short_forms_bij_deze_registraties": sum(1 for r in plan.f["records"].values() if r["soort"] == "shortform"),
            "records_gekoppeld_aan_model": len(plan.kandidaten),
            "knopen_gekoppeld": sorted({k["opdrachtgever"] for k in plan.kandidaten}),
        },
        "top": [{k2: k[k2] for k2 in ("score", "opdrachtgever", "fara_naam", "agent", "agent_in_model", "regnr", "van",
                                       "tot", "soort", "status", "jaren", "documenten", "citaat")} for k in kand[:TOP]],
        "agenten_met_meer_nl_opdrachtgevers": [{"agent": a, "regnr": nr, "records": n}
                                              for (a, nr), n in agent_hubs.most_common() if n > 1],
        "niet_in_model_meest_geregistreerd": niet.most_common(40),
        "tips": plan.tips,
    }


def rapport_md(rap: dict, samenvatting: dict) -> str:
    d = rap["dekking"]
    r = [f"# FARA × het model — droogloop {rap['uitgave']}", "",
         f"Opdrachtgevers uit het Koninkrijk: {d['opdrachtgevers_koninkrijk']} records ({d['verschillende_namen']} namen, "
         f"{d['registraties']} registraties); lopend: {d['lopend']}; beëindigd in 2000 of later: {d['beeindigd_2000_of_later']}.",
         f"Per land: {d['per_land']}", f"Per decennium (begin): {d['per_decennium_begin']}",
         f"Gekoppeld aan het model (met de hand nagelopen): {d['records_gekoppeld_aan_model']} records → "
         f"{', '.join(d['knopen_gekoppeld'])}", "",
         f"Gepland: {samenvatting['nieuwe_verbanden']} nieuwe verbanden, {samenvatting['nieuwe_agenten']} nieuwe agenten, "
         f"{samenvatting['bestaande_verbanden_extra_bron']} extra bronnen op bestaande verbanden.", "",
         "Score = actualiteit × log2(2 + jaren) × 2 (agent al in het model) × (1 + 0,25 per andere NL-opdrachtgever "
         "van de agent) × (1 + log2(1 + documenten)/4).", "",
         "| # | score | opdrachtgever (model) | agent | periode | status |", "|---|---|---|---|---|---|"]
    for i, k in enumerate(rap["top"], 1):
        r.append(f"| {i} | {k['score']} | {k['opdrachtgever']} ({k['fara_naam']}) | {k['agent']} (reg. {k['regnr']})"
                 f"{' ★' if k['agent_in_model'] else ''} | {k['van']} – {k['tot'] or 'lopend'} | {k['status']} |")
    r += ["", "★ = agent staat al in het model.", "", "## Lopend", ""] + [f"- {x}" for x in d["lopend_lijst"]]
    r += ["", "## Niet in het model (meest geregistreerd)", ""] + [f"- {n}× {p}" for p, n in rap["niet_in_model_meest_geregistreerd"][:25]]
    r += ["", "## Tips (niet gekoppeld; met de hand nalopen)", ""] + [f"- {t['soort']}: {t['fara']} ~ {t.get('model', '')}"
                                                                    f"{' #' + str(t['id']) if t.get('id') else ''}" for t in rap["tips"][:40]]
    return "\n".join(r) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave")
    ap.add_argument("--haal", action="store_true")
    ap.add_argument("--indienen", action="store_true")
    a = ap.parse_args()
    if a.haal and not a.uitgave:
        fara.haal()
    data = fara.lees(fara.pad_van(a.uitgave) if a.uitgave else fara.uitgaven()[-1])
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(data, conn, koppelingen).maak()
    samenvatting = {
        "uitgave": plan.uitgave, "nieuwe_agenten": len(plan.nieuwe_orgs),
        "nieuwe_verbanden": len(plan.relaties), "bestaande_verbanden_extra_bron": len(plan.extra_bron),
        "telling": {k: v for k, v in sorted(plan.tel.items()) if v}}
    rap = rapport(plan)
    print(json.dumps(samenvatting, ensure_ascii=False, indent=1))
    fara.MAP.mkdir(parents=True, exist_ok=True)
    (fara.MAP / f"rapport_{plan.uitgave}.json").write_text(json.dumps(
        {"samenvatting": samenvatting, **rap,
         "relaties": [{k: v for k, v in r.items() if k != "claim"} for r in plan.relaties],
         "nieuwe_agenten": sorted(o["naam"] for o in plan.nieuwe_orgs.values()),
         "extra_bron": [{"relation_id": r["relation_id"], "type": r["bestaand_type"], "citaat": r["regel"]}
                        for r in plan.extra_bron]}, ensure_ascii=False, indent=1), encoding="utf-8")
    (fara.MAP / f"rapport_{plan.uitgave}.md").write_text(rapport_md(rap, samenvatting), encoding="utf-8")
    for naam, inhoud in (("overgeslagen", plan.overgeslagen), ("koppelingen", plan.koppelingen)):
        (fara.MAP / f"{naam}_{plan.uitgave}.json").write_text(json.dumps(inhoud, ensure_ascii=False, indent=1),
                                                              encoding="utf-8")
    print(f"rapport: {fara.MAP / f'rapport_{plan.uitgave}.md'}")
    if not a.indienen:
        print("\n(droogloop — niets ingediend)")
        return
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()), bron=fara, cluster=CLUSTER)
    bron_id = ind.bron()
    ind.entiteiten()
    ind.relaties(bron_id)
    ind.extra_bronnen(bron_id)
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
