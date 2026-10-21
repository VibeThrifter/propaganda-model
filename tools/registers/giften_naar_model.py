#!/usr/bin/env python3
"""Giften aan politieke partijen (Wfpp-overzichten van BZK) → het model (eigenaar 2026-10-20: "maak
een register van giften aan Nederlandse politieke partijen en mine er verbanden uit").

giften.py leest de overzichten; dit script kiest wat telt en plant, zonder AI:
  - gever → partij: `donor`, mechanisme `partijfinanciering`, met het totaal per jaar in `functie`
    en de vroegste giftdatum als begin. Elk record (één gever bij één partij in één overzicht) is
    een argument met de recordregel als citaat; een bestaand donor- of financieringsverband krijgt
    de records als extra bron. Hooguit MAX_PER_VERBAND argumenten per verband per run (de
    nieuwste eerst). Een neveninstelling (jongerenclub, wetenschappelijk bureau,
    campagnestichting) telt als de partij zelf (Wfpp art. 1); het record noemt haar.
  - organisaties: een die al in het model staat (naam, schrijfwijze, afkorting; zoals de
    Kamerregisters) bij elk bedrag; een nieuwe alleen als de rechtsvorm in de naam staat (README
    § Regels) én het totaal minstens DREMPEL_NIEUW is of de gever ook lobbyt, in de agenda's van
    bewindspersonen staat of een Kamerlid er een nevenfunctie heeft. Niet: partijen en hun eigen
    stichtingen, bestuurdersverenigingen en fracties (afdrachten), overheden, en persoonlijke
    vennootschappen (de naam bevat voorletters of de achternaam van de UBO: privé).
  - natuurlijke personen nooit als nieuwe knoop of verband. Een persoon die al als publieke persoon
    in het model staat koppelt alleen (a) met de hand (koppelingen.json 'giften_personen',
    "<gever>|<partijlabel>" → id) of (b) als de achternaam en eerste voorletter in de hele uitgave
    uniek zijn, er precies één kandidaat in het model is én die al een donor- of
    financieringsverband met dezelfde partij heeft: dan alleen een extra bron op dat verband. Een
    kandidaat die zelf politicus van die partij is, is een afdracht (ruis, niet gekoppeld).
Wat niet geplaatst wordt, telt het rapport; van privépersonen nooit de naam.

Interessant versus ruis (score per paar gever–partij, zie `score`):
  B = 1 + log10(totaal / € 1.000)                (bedrag; € 10.000 → 2, € 100.000 → 3)
  × H = 1 + 0,5 per extra jaar waarin de gever gaf (herhaling)
  × P = 1 + 0,75 per extra partij die de gever steunt (spreiding: toegang kopen)
  × L = 2 als de gever een vaste toegangspas tot de Tweede Kamer heeft of al 'lobbyt'
  × A = 1 + dagen/10 (max 3) als de gever in de agenda's van bewindspersonen staat
  × N = 1,5 als een politicus een nevenfunctie of loopbaan bij de gever heeft; 2 als dat een
        politicus van de ontvangende partij is
  × M = 1,3 als de gever al in het model staat
  × V = 0,3 bij een nalatenschap of legaat (geen invloed op een levende relatie)
Het rapport (data/registers/giften/rapport_<datum>.json + rapport.md) geeft per partij en jaar de
aantallen, de top en de tips (UBO's die een publieke persoon in het model lijken; organisaties
boven de drempel zonder rechtsvorm in de naam).

Gebruik:
    python3 tools/registers/giften_naar_model.py                 # droogloop + rapport
    python3 tools/registers/giften_naar_model.py --haal          # eerst nieuwe overzichten ophalen
    python3 tools/registers/giften_naar_model.py --indienen      # (pas na de regels in registercheck.py)
"""
from __future__ import annotations

import argparse
import datetime
import difflib
import json
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import giften  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import namen_van, noemt, ontleed_naam, sleutel  # noqa: E402
from naar_model import TOKEN, Rest  # noqa: E402

DB_PATH = tkm.ROOT / "data" / "propaganda_model.db"
AGENDA_ANALYSE = tkm.ROOT / "data" / "registers" / "agenda" / "analyse.json"
CLUSTER = "register:giften"
MECH = "partijfinanciering"
DONOR_TYPES = ("donor", "financiering")
DREMPEL_NIEUW = 10000.0      # € per gever over alle jaren: de meldplicht-drempel van art. 25a Wfpp
MAX_PER_VERBAND = 8
TOP = 30
OVERHEID = re.compile(r"^(gemeente|provincie|waterschap|ministerie|staat der nederlanden)\b", re.I)
NALATENSCHAP = re.compile(r"\b(nalatenschap|legaat|erven|erfgenamen|executele)\b", re.I)
RECHTSVORM_WOORDEN = re.compile(r"\b(stichting|stg|vereniging|b\s?v|n\s?v|bv|nv|cooperatie\w*|u\s?a|ua|st|the|de|het)\b")


gever_sleutel = giften.kern_sleutel


def _kern(naam: str) -> str:
    """De naam zonder rechtsvorm, voor het zoeken in lobbyregister, agenda's en nevenfuncties; een
    enkel woord pas vanaf acht letters ('Jethro' is ook een voornaam)."""
    k = " ".join(RECHTSVORM_WOORDEN.sub(" ", sleutel(naam)).split())
    return k if (len(k.split()) >= 2 or len(k) >= 8) else ""


def _naamdelen(naam: str) -> tuple[str, str, str]:
    """→ (achternaam met tussenvoegsel, eerste voornaam of '', voorletters) als sleutels."""
    n = ontleed_naam(tkm.zonder_haakjes(naam).split(",")[0])
    achter = sleutel(f"{n['tussenvoegsel'] or ''} {n['achternaam'] or ''}")
    voornaam = sleutel((n["roepnaam"] or n["voornamen"] or "").split()[0]) if (n["roepnaam"] or n["voornamen"]) else ""
    letters = re.sub(r"[^a-z]", "", sleutel(n["voorletters"] or ""))
    if not letters and voornaam:
        letters = voornaam[:1]
    return achter, voornaam, letters


def _past(gever: tuple[str, str, str], model: tuple[str, str, str]) -> bool:
    """Dezelfde achternaam; twee voornamen gelijk, anders twee reeksen voorletters gelijk
    (een losse voorletter past op de eerste), anders de eerste letter."""
    if not gever[0] or gever[0] != model[0] or not gever[2] or not model[2]:
        return False
    if gever[1] and model[1]:
        return gever[1] == model[1]
    if len(gever[2]) > 1 and len(model[2]) > 1:
        return gever[2] == model[2]
    return gever[2][:1] == model[2][:1]


def _binnen(datum: str | None, van: str | None, tot: str | None) -> bool:
    """Valt een datum (JJJJ[-MM[-DD]]) binnen een looptijd, vergeleken op gemeenschappelijke precisie?"""
    if not datum:
        return False
    for grens, groter in ((van, True), (tot, False)):
        if grens:
            n = min(len(datum), len(grens))
            if (datum[:n] < grens[:n]) if groter else (datum[:n] > grens[:n]):
                return False
    return True


def _jaarbedragen(r: dict) -> dict[str, float]:
    if r["per_jaar"]:
        return {j: b for j, b in r["per_jaar"].items() if b}
    return {r["jaar"]: r["totaal"] or 0} if r["jaar"] else {}


def _dag(d: str) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(d[:10]) if len(d) >= 10 else None
    except ValueError:
        return None


def unieke_giften(recs: list[dict]) -> list[tuple[str, float]]:
    """De gedateerde giften van één gever aan één partij, elk één keer: dezelfde gift staat in
    meer overzichten, soms met een andere datum (ontvangst of boeking: 'Godefridus van Hees Fonds'
    € 29.000 op 18 én 29 april 2024). Een gift uit een ander overzicht met hetzelfde bedrag en
    hooguit 31 dagen verschil is dezelfde; binnen één overzicht zijn twee regels twee giften."""
    gezien: list[tuple[str, float, str]] = []
    gebruikt: set[tuple[int, str]] = set()   # (index in gezien, uitgave) al gekoppeld
    for r in sorted(recs, key=lambda r: r.get("_uitgave", "")):
        u = r.get("_uitgave", "")
        for b, d in r["bedragen"]:
            if not (d and b):
                continue
            b = round(b, 2)
            dag = _dag(d)
            treffer = None
            for i, (d2, b2, u2) in enumerate(gezien):
                if u2 == u or b2 != b or (i, u) in gebruikt:
                    continue
                dag2 = _dag(d2)
                if d2 == d or (dag and dag2 and abs((dag - dag2).days) <= 31):
                    treffer = i
                    break
            if treffer is None:
                gezien.append((d, b, u))
            else:
                gebruikt.add((treffer, u))
    return [(d, b) for d, b, _ in gezien]


def jaartotalen(recs: list[dict]) -> dict[str, float]:
    """Per jaar wat één gever één partij gaf, over overzichten die elkaar overlappen (jaaroverzicht,
    substantiële giften, vóór en ná een verkiezing): de som van de gedateerde giften (dezelfde datum
    en hetzelfde bedrag in twee overzichten is één gift), of, als dat meer is, het jaartotaal dat één
    overzicht zelf geeft (daar zitten ook de kleine, ongedateerde giften in)."""
    jaren: dict[str, float] = defaultdict(float)
    for d, b in unieke_giften(recs):
        jaren[d[:4]] += b
    per_uitgave: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in recs:
        for j, b in _jaarbedragen(r).items():
            per_uitgave[r.get("_uitgave", "")][j] += b
    for jb in per_uitgave.values():
        for j, b in jb.items():
            jaren[j] = max(jaren[j], b)
    return {j: round(b, 2) for j, b in sorted(jaren.items()) if b}


class Plan(tkm.Plan):
    def __init__(self, data: dict[str, dict], conn: sqlite3.Connection, koppelingen: dict | None = None):
        self.data = data   # uitgave → giften.lees(...)
        nieuwste = max(d["versie"] for d in data.values())
        super().__init__({"uitgave": nieuwste, "personen": {}, "records": {}}, conn, koppelingen)
        self.mech.update(self._ids("mechanisms", (MECH,)))
        k = koppelingen or {}
        self.hand_orgs = {sleutel(n): v for n, v in k.get("giften_organisaties", {}).items() if not n.startswith("_")}
        self.hand_personen = {n: v for n, v in k.get("giften_personen", {}).items() if not n.startswith("_")}
        self.schrijfwijzen.update({sleutel(a): b for a, b in giften.schrijfwijzen().items()})
        # bestaande donor-/financieringsverbanden per (bron, doel) en wat ze al uit dit register citeren
        self.donor: dict[tuple[int, int], int] = {}
        for rid, s, t in conn.execute(f"""
                SELECT id, source_id, target_id FROM relations
                WHERE relation_type IN ({','.join('?' * len(DONOR_TYPES))}) AND NOT vervangen
                  AND status <> 'afgewezen'""", DONOR_TYPES):
            self.donor.setdefault((s, t), rid)
        self.geciteerd: dict[int, set[str]] = defaultdict(set)
        for rid, sec in conn.execute("""
                SELECT a.relation_id, c.section FROM citations c JOIN arguments a ON a.id = c.argument_id
                WHERE c.page LIKE 'giften/%' AND a.relation_id IS NOT NULL"""):
            self.geciteerd[rid].add(sec)
        # elke relatie tussen een persoon en een partij die geen gift is: die persoon is politicus daar
        self.politicus: dict[int, set[int]] = defaultdict(set)
        for s, t, st, tt in conn.execute("""
                SELECT r.source_id, r.target_id, s.type, t.type FROM relations r
                JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
                WHERE NOT r.vervangen AND r.status <> 'afgewezen' AND r.relation_type NOT IN ('donor', 'financiering')
                  AND ((s.type = 'persoon' AND t.type = 'partij') OR (s.type = 'partij' AND t.type = 'persoon'))"""):
            persoon, partij = (s, t) if st == "persoon" else (t, s)
            self.politicus[persoon].add(partij)
        self._personen_index()
        # looptijd van bestaande donorverbanden en de beweringen erop (wie gaf via welk bedrijf?)
        self.rel_looptijd: dict[int, tuple] = {}
        self.rel_claims: dict[int, str] = defaultdict(str)
        rids = sorted(set(self.donor.values()))
        if rids:
            for rid, van, tot in conn.execute(f"SELECT id, active_from, active_until FROM relations WHERE id IN ({','.join('?' * len(rids))})", rids):  # noqa: S608
                self.rel_looptijd[rid] = (van, tot)
            for rid, claim in conn.execute(f"SELECT relation_id, claim FROM arguments WHERE relation_id IN ({','.join('?' * len(rids))}) AND status <> 'verworpen'", rids):  # noqa: S608
                self.rel_claims[rid] += f" {claim}"
        self.dubbel: list[dict] = []
        self.andere_naam: list[dict] = []
        self.buiten_looptijd: list[dict] = []
        self.pv_sleutels: set[str] = set()
        # 'voornaam achternaam' van publieke personen in het model: een holding of stichting die zo
        # heet ('Stichting Ivo Opstelten Foundation') is niet privé
        self.publieke_namen = {f"{d[1]} {d[0]}" for lijst in self.p_index.values() for _, _, d in lijst if d[1]}
        self.gift_paren: dict[tuple, list[dict]] = defaultdict(list)     # (gever_ref, partij_id) → records
        self.gever_naam: dict[tuple, str] = {}
        self.kandidaat_orgs: dict[str, list[dict]] = defaultdict(list)   # gever_sleutel → records (nieuw)
        self.argumenten: list[dict] = []
        self.extra_bron: list[dict] = []
        self.analyse: list[dict] = []
        self.ubo_tips: list[dict] = []
        self.privé = Counter()
        self.privé_bedrag = Counter()

    # ── personen ───────────────────────────────────────────────────────────
    def _personen_index(self):
        self.p_index: dict[str, list[tuple[int, str, tuple]]] = defaultdict(list)
        for i, naam in self.conn.execute("""SELECT id, name FROM entities
                WHERE type = 'persoon' AND NOT vervangen AND status <> 'afgewezen'"""):
            delen = _naamdelen(naam)
            if delen[0] and delen[2]:
                self.p_index[delen[0]].append((i, naam, delen))

    def kandidaten_persoon(self, naam: str) -> list[tuple[int, str, tuple]]:
        delen = _naamdelen(naam)
        return [c for c in self.p_index.get(delen[0], []) if _past(delen, c[2])]

    @staticmethod
    def _naam_sleutel(gever: str) -> tuple[str, str]:
        delen = _naamdelen(gever)
        return delen[0], delen[2][:1]

    def _persoon(self, rec: dict, pid: int, uniek: Counter) -> tuple | None:
        hand = self.hand_personen.get(f"{rec['gever']}|{rec['partij_label']}")
        if hand:
            return ("bestaand", int(hand))
        achter, letter = self._naam_sleutel(rec["gever"])
        kand = self.kandidaten_persoon(rec["gever"])
        bedrag = rec["totaal"] or 0
        if len(kand) == 1 and pid in self.politicus.get(kand[0][0], set()):
            self.privé["afdracht van een politicus van de partij (niet gekoppeld)"] += 1
            self.privé_bedrag["afdracht van een politicus van de partij (niet gekoppeld)"] += bedrag
            return None
        if len(kand) == 1 and uniek[(rec["_uitgave"], achter, letter)] == 1 and (kand[0][0], pid) in self.donor:
            self.koppelingen.append({"soort": "persoon", "tekst": f"{rec['gever']} → {rec['partij_label']}",
                                     "model": kand[0][1], "id": kand[0][0],
                                     "hoe": "unieke achternaam + voorletter, bestaand donorverband met dezelfde partij"})
            return ("bestaand", kand[0][0])
        reden = ("nalatenschap of legaat (privé)" if NALATENSCHAP.search(f"{rec['gever']} {rec['toelichting']}")
                 else "natuurlijk persoon, niet als publieke persoon in het model" if not kand
                 else "naamgenoot in het model, geen bestaand donorverband: niet gekoppeld")
        self.privé[reden] += 1
        self.privé_bedrag[reden] += bedrag
        return None

    # ── organisaties ───────────────────────────────────────────────────────
    def _org(self, rec: dict) -> tuple | None:
        naam = rec["gever"]
        if tkm.UITSLUITEN.search(naam) or self._partij_eigen(naam) or \
                (rec["neveninstelling"] and sleutel(naam) == sleutel(rec["neveninstelling"])):
            return self._mis("gift", rec, "partij-eigen gever (afdeling, fractie, bestuurdersvereniging, eigen stichting)")
        if OVERHEID.search(naam):
            return self._mis("gift", rec, "overheid (fractieondersteuning)")
        for kand in [naam] + ([naam.split(",")[0].strip()] if "," in naam else []):
            gevonden = self._bestaand(kand, ruim=True)
            if gevonden:
                n, typ, laag = self.org[gevonden[0]]
                if typ in tkm.OVERHEID_TYPES or laag:
                    return self._mis("gift", rec, "overheid (fractieondersteuning)")
                reden = self._toegestaan(gevonden[0], "gift")
                if reden:
                    return self._mis("gift", rec, f"partij-eigen gever ({reden})")
                return self._gekoppeld(rec, gevonden[0], gevonden[1], kand)
        if rec["gever_soort"] == "persoonlijke_vennootschap" and not self._publiek_genoemd(naam):
            self.pv_sleutels.add(gever_sleutel(naam))
            self.privé["persoonlijke vennootschap (voorletters of UBO-naam in de naam)"] += 1
            self.privé_bedrag["persoonlijke vennootschap (voorletters of UBO-naam in de naam)"] += rec["totaal"] or 0
            return None
        return ("kandidaat", gever_sleutel(naam))

    def _partij_eigen(self, naam: str) -> bool:
        """Zoals tkm.Plan, maar een plaatsnaam ('Ommen', 'Oss' uit een lokale partij) maakt een
        gever niet partij-eigen ('Beheermaatschappij Ommen B.V.')."""
        if not hasattr(self, "_gemeentenamen"):
            self._gemeentenamen = {sleutel(re.sub(r"^(Gemeente|Provincie)\s+", "", tkm.zonder_haakjes(n)))
                                   for n, t, laag in self.org.values() if laag in ("gemeente", "provincie")}
        t = f" {sleutel(naam)} "
        return any(f" {k} " in t for k in self.partij_woorden if len(k) >= 2 and k not in self._gemeentenamen)

    def _publiek_genoemd(self, naam: str) -> bool:
        t = f" {sleutel(naam)} "
        return any(f" {n} " in t for n in self.publieke_namen if len(n.split()) >= 2)

    def _privé_cluster(self, recs: list[dict]) -> bool:
        """Een nieuwe gever is privé als één van zijn schrijfwijzen dat in enig overzicht was, of naar
        een natuurlijk persoon heet (giften._persoonlijk met de namen uit alle overzichten), tenzij
        de naam een publieke persoon uit het model noemt."""
        for r in recs:
            if self._publiek_genoemd(r["gever"]) or sleutel(r["gever"]) in self.hand_orgs:
                return False
        return any(gever_sleutel(r["gever"]) in self.pv_sleutels
                   or giften._persoonlijk(r["gever"], self.voornamen, self.achternamen) for r in recs)

    def _mis(self, context, rec, reden):
        # zoals tkm.Plan._mis, maar zonder de recordregel van een natuurlijk persoon
        self.overgeslagen.append({"soort": context, "reden": reden,
                                  "tekst": rec["regel"] if rec["gever_soort"] == "organisatie" else None})
        self.tel[f"overgeslagen: {reden}"] += 1
        return None

    def _nieuwe_naam(self, recs: list[dict]) -> str | None:
        """De schrijfwijze met rechtsvorm (of met de hand getypeerd) die in de meeste records als
        gever staat; None als er geen is."""
        spellingen = list(dict.fromkeys(r["gever"] for r in recs))
        # 'Stg. X' / 'St. X' als 'Stichting X' (dezelfde gever volgens giften.zelfde_gever)
        spellingen += [re.sub(r"^St(?:g)?\.?\s+", "Stichting ", n) for n in spellingen if re.match(r"^Stg?\.\s|^Stg\s", n)]
        beste = None
        for naam in spellingen:
            hand = self.hand_orgs.get(sleutel(naam))
            if not (hand or tkm.rechtsvorm(naam)) or len(naam.split()) < 2:
                continue
            k = re.sub(r"\s+(b v|n v|bv|nv|u a|ua)$", "", tkm._zonder_lidwoord(sleutel(naam)))
            if k in tkm.GENERIEK or sleutel(naam) in self.alle_namen:
                continue
            dekking = sum(1 for r in recs if giften.zelfde_gever(r["gever"], naam))
            overgetikt = bool(re.search(r"\bl(?=[bcdfghjklmnpqrstvwxz])", naam))   # 'lnvestment'
            sleutel_b = (dekking, not overgetikt, naam.startswith("Stichting "), sum(c.isupper() for c in naam), len(naam))
            if beste is None or sleutel_b > beste[0]:
                beste = (sleutel_b, (hand or {}).get("naam") or naam)
        return beste[1] if beste else None

    # ── signalen ───────────────────────────────────────────────────────────
    def signalen(self):
        """Lobby (toegangspas, 'lobbyt'), agenda's van bewindspersonen en nevenfuncties van
        politici, voor bestaande en nieuwe gevers."""
        self.lobby_ids = {s for (s,) in self.conn.execute(
            "SELECT DISTINCT source_id FROM relations WHERE relation_type = 'lobbyt' AND NOT vervangen "
            "AND status <> 'afgewezen'")}
        self.agenda_dagen: Counter = Counter()
        if AGENDA_ANALYSE.exists():
            for a in json.loads(AGENDA_ANALYSE.read_text(encoding="utf-8")):
                self.agenda_dagen[a["org_id"]] += a["dagen"]
        self.neven: dict[int, set[int]] = defaultdict(set)     # org → personen met nevenfunctie/loopbaan
        for s, t in self.conn.execute("""
                SELECT r.source_id, r.target_id FROM relations r JOIN mechanisms m ON m.id = r.mechanism_id
                JOIN entities s ON s.id = r.source_id
                WHERE m.name IN ('nevenfunctie_verstrengeling', 'draaideurconstructie') AND s.type = 'persoon'
                  AND NOT r.vervangen AND r.status <> 'afgewezen'"""):
            self.neven[t].add(s)
        # tekstbronnen voor gevers die nog niet in het model staan
        self.lobby_teksten: list[str] = []
        try:
            import lobby
            if lobby.uitgaven():
                self.lobby_teksten = [f"{r.get('werkzaam') or ''} · {r.get('belangen') or ''}" for r in lobby.lees(lobby.uitgaven()[-1])["records"].values()]
        except Exception as e:  # noqa: BLE001 - een ontbrekend of kapot register mag het rapport niet tegenhouden
            self.tel[f"signaal lobbyregister niet gelezen ({type(e).__name__})"] += 1
        self.agenda_teksten: list[tuple[str, str]] = []
        try:
            import agenda
            for p in agenda.uitgaven():
                for r in agenda.lees(p)["records"].values():
                    if r.get("type") in ("Gesprek", "Ontvangst", "Werkbezoek"):
                        self.agenda_teksten.append((f" {sleutel(r['tekst'])} ", r["datum"]))
        except Exception as e:  # noqa: BLE001
            self.tel[f"signaal agenda's niet gelezen ({type(e).__name__})"] += 1
        self.agenda_woord: dict[str, set[int]] = defaultdict(set)
        for i, (t, _) in enumerate(self.agenda_teksten):
            for w in set(t.split()):
                self.agenda_woord[w].add(i)
        self.tk_neven: list[tuple[str, str]] = []   # (omschrijving, fractie)
        try:
            import tk
            if tk.uitgaven():
                d = tk.lees(tk.uitgaven()[-1])
                for r in d["records"].values():
                    if r["soort"] == "nevenfunctie" and not r.get("tot"):
                        self.tk_neven.append((r["omschrijving"], d["personen"].get(r["persoon_id"], {}).get("fractie") or ""))
                    elif r["soort"] == "loopbaan" and r.get("werkgever"):
                        self.tk_neven.append((r["werkgever"], d["personen"].get(r["persoon_id"], {}).get("fractie") or ""))
        except Exception as e:  # noqa: BLE001
            self.tel[f"signaal Kamerregisters niet gelezen ({type(e).__name__})"] += 1

    def _agenda_dagen_tekst(self, naam: str) -> int:
        k = _kern(naam)
        if not k:
            return 0
        woorden = k.split()
        kand = set.intersection(*(self.agenda_woord.get(w, set()) for w in woorden)) if woorden else set()
        return len({self.agenda_teksten[i][1] for i in kand if f" {k} " in self.agenda_teksten[i][0]})

    def _signaal(self, ref: tuple, naam: str, partij_ids: set[int]) -> dict:
        s = {"lobby": False, "agenda_dagen": 0, "nevenfunctie": 0, "nevenfunctie_partij": False}
        if ref[0] in ("bestaand", "oo") and ref[1] > 0:
            eid = ref[1]
            s["lobby"] = eid in self.lobby_ids
            s["agenda_dagen"] = self.agenda_dagen.get(eid, 0)
            s["nevenfunctie"] = len(self.neven.get(eid, ()))
            s["nevenfunctie_partij"] = any(self.politicus.get(p, set()) & partij_ids for p in self.neven.get(eid, ()))
        k = _kern(naam)
        if k:
            if not s["lobby"]:
                s["lobby"] = any(noemt(t, k) for t in self.lobby_teksten)
            s["agenda_dagen"] = max(s["agenda_dagen"], self._agenda_dagen_tekst(naam))
            treffers = [fr for om, fr in self.tk_neven if noemt(om, k)]
            if treffers:
                s["nevenfunctie"] = max(s["nevenfunctie"], len(treffers))
                partijnamen = {self.org[p][0] for p in partij_ids if p in self.org}
                s["nevenfunctie_partij"] = s["nevenfunctie_partij"] or any(
                    tkm.partij_naam(fr) in partijnamen for fr in treffers if fr)
        return s

    @staticmethod
    def score(totaal: float, jaren: int, partijen: int, sig: dict, in_model: bool, nalatenschap: bool) -> float:
        b = 1 + math.log10(max(totaal, 1000.0) / 1000.0)
        h = 1 + 0.5 * max(jaren - 1, 0)
        p = 1 + 0.75 * max(partijen - 1, 0)
        lob = 2.0 if sig["lobby"] else 1.0
        ag = 1 + min(sig["agenda_dagen"], 20) / 10
        nv = 2.0 if sig["nevenfunctie_partij"] else (1.5 if sig["nevenfunctie"] else 1.0)
        m = 1.3 if in_model else 1.0
        v = 0.3 if nalatenschap else 1.0
        return round(b * h * p * lob * ag * nv * m * v, 2)

    # ── plannen ────────────────────────────────────────────────────────────
    def maak(self):
        records = [{**r, "_uitgave": u} for u, d in self.data.items() for r in d["records"].values()]
        # voor- en achternamen uit de overzichten en (voornamen) van de personen in het model
        self.voornamen, self.achternamen = giften.namenlijsten(
            r["gever"] for r in records if r["gever_soort"] == "persoon")
        self.voornamen |= {d[1] for lijst in self.p_index.values() for _, _, d in lijst
                           if d[1] and re.fullmatch(r"[a-zà-ÿ'-]{3,}", d[1])}
        uniek = Counter()
        for u in self.data:
            namen = {_naamdelen(r["gever"]) for r in self.data[u]["records"].values() if r["gever_soort"] == "persoon"}
            for achter, _voornaam, letters in {(a, v, l) for a, v, l in namen}:
                uniek[(u, achter, letters[:1])] += 1
        for rec in records:
            self.tel["records"] += 1
            self.tel[f"records: {rec['gever_soort']}"] += 1
            pid = self.partij_id.get(rec["partij"]) if rec["partij"] else None
            if not pid:
                self.tel["overgeslagen: partij niet in het model"] += 1
                self.tel[f"partij niet in het model: {rec['partij_label']}"] += 1
                continue
            if rec["gever_soort"] == "persoon":
                ref = self._persoon(rec, pid, uniek)
            else:
                ref = self._org(rec)
            if not ref:
                continue
            if ref[0] == "kandidaat":
                self.kandidaat_orgs[ref[1]].append({**rec, "_partij_id": pid})
                continue
            self.gift_paren[(ref, pid)].append(rec)
            self.gever_naam[ref] = self.org[ref[1]][0] if ref[1] in self.org else self._persoonsnaam(ref[1])
        self._ubo_index()
        self._kandidaten()
        self._scoor()
        self._kies()
        self._ubo()
        self._zelfcontrole()
        return self.klem()

    def _persoonsnaam(self, eid: int) -> str:
        rij = self.conn.execute("SELECT name FROM entities WHERE id = ?", (eid,)).fetchone()
        return rij[0] if rij else f"#{eid}"

    def _kandidaten(self):
        """Nieuwe organisaties: overgetikte schrijfwijzen samen ('Lamda Furtherdance' bij 'Lambda
        Furtherance': zelfde begin, ≥ 8 tekens, gelijkenis ≥ 0,9), dan de naam kiezen; drempel en
        signalen beslissen in _kies."""
        vertegenwoordigers: list[str] = []
        for k in sorted(self.kandidaat_orgs, key=lambda x: (-len(self.kandidaat_orgs[x]), x)):
            doel = next((v for v in vertegenwoordigers if len(k) >= 8 and len(v) >= 8 and k[:2] == v[:2]
                         and difflib.SequenceMatcher(None, k, v).ratio() >= 0.9), None)
            if doel:
                self.kandidaat_orgs[doel].extend(self.kandidaat_orgs.pop(k))
                self.tel["nieuwe gever: overgetikte schrijfwijze samengevoegd"] += 1
            else:
                vertegenwoordigers.append(k)
        for k in list(self.kandidaat_orgs):
            recs = self.kandidaat_orgs[k]
            if self._privé_cluster(recs):
                reden = "persoonlijke vennootschap (voorletters of UBO-naam in de naam)"
                self.privé[reden] += len(recs)
                self.privé_bedrag[reden] += sum(r["totaal"] or 0 for r in recs)
                self.tel["nieuwe gever: privé (heet naar een natuurlijk persoon)"] += 1
                del self.kandidaat_orgs[k]
        for k, recs in self.kandidaat_orgs.items():
            naam = self._nieuwe_naam(recs)
            ref = ("nieuw", k)
            if naam:
                hand = self.hand_orgs.get(sleutel(naam))
                vorm = (hand["type"], hand["rol"]) if hand else tkm.rechtsvorm(naam)
                self.nieuwe_orgs[k] = {"naam": naam, "type": vorm[0], "rol": vorm[1], "_gepland": False,
                                       "beschrijving": "Gever aan een politieke partij volgens de Wfpp-overzichten "
                                                       "van giften (ministerie van BZK)."}
            else:
                ref = ("zonder_rechtsvorm", k)
                self.gever_naam[ref] = Counter(r["gever"] for r in recs).most_common(1)[0][0]
            for r in recs:
                self.gift_paren[(ref, r["_partij_id"])].append(r)
            if naam:
                self.gever_naam[ref] = naam

    def _scoor(self):
        per_gever_jaren: dict[tuple, set[str]] = defaultdict(set)
        per_gever_partijen: dict[tuple, set[int]] = defaultdict(set)
        bedrag_paar: dict[tuple, dict[str, float]] = {}
        self.gift_index: dict[tuple, set[tuple]] = defaultdict(set)   # (partij, datum, bedrag) → gevers
        for (ref, pid), recs in self.gift_paren.items():
            jaren = jaartotalen(recs)
            bedrag_paar[(ref, pid)] = jaren
            for r in recs:
                for b, d in r["bedragen"]:
                    if d and b:
                        self.gift_index[(pid, d, round(b, 2))].add(ref)
            per_gever_jaren[ref] |= {j for j, b in jaren.items() if b}
            per_gever_partijen[ref].add(pid)
        for (ref, pid), recs in self.gift_paren.items():
            naam = self.gever_naam.get(ref, "?")
            jaren = bedrag_paar[(ref, pid)]
            totaal = round(sum(jaren.values()), 2)
            sig = self._signaal(ref, naam, per_gever_partijen[ref])
            nalaten = all(NALATENSCHAP.search(f"{r['gever']} {r['toelichting']}") for r in recs)
            in_model = ref[0] in ("bestaand", "oo")
            soort = "persoon" if in_model and ref[1] not in self.org else recs[0]["gever_soort"]
            beste = max(recs, key=lambda r: ((r["totaal"] or 0), r["_uitgave"]))
            datums = [d for r in recs for _, d in r["bedragen"] if d]
            self.analyse.append({
                "gever": naam, "gever_ref": list(ref), "gever_soort": soort,
                "partij": self.org[pid][0], "partij_id": pid, "totaal": totaal,
                "per_jaar": dict(sorted(jaren.items())), "jaren_gever": len(per_gever_jaren[ref]),
                "partijen_gever": sorted(self.org[p][0] for p in per_gever_partijen[ref]),
                "signalen": sig, "in_model": in_model, "nalatenschap": nalaten,
                "score": self.score(totaal, len(per_gever_jaren[ref]), len(per_gever_partijen[ref]), sig, in_model, nalaten),
                "van": min(datums) if datums else min((r["jaar"] for r in recs if r["jaar"]), default=None),
                "tot": max(datums) if datums else max((r["jaar"] for r in recs if r["jaar"]), default=None),
                "records": len(recs),
                "neveninstellingen": sorted({r["neveninstelling"] for r in recs if r["neveninstelling"]}),
                "status": None, "citaat": beste["regel"], "sleutel": beste["sleutel"], "uitgave": beste["_uitgave"]})
        self.analyse.sort(key=lambda a: (-a["score"], -a["totaal"]))

    def _kies(self):
        for a in self.analyse:
            ref, pid = tuple(a["gever_ref"]), a["partij_id"]
            recs = sorted(self.gift_paren[(ref, pid)], key=lambda r: (r["laatste"] or r["jaar"] or "", r["_uitgave"]), reverse=True)
            if ref[0] == "zonder_rechtsvorm":
                a["status"] = "rapport: nieuw, maar geen rechtsvorm in de naam (koppelingen.json 'giften_organisaties')"
                self.tel["paar: geen rechtsvorm (rapport)"] += 1
                continue
            sig = a["signalen"]
            if ref[0] == "nieuw":
                totaal_gever = sum(x["totaal"] for x in self.analyse if tuple(x["gever_ref"]) == ref)
                if totaal_gever < DREMPEL_NIEUW and not (sig["lobby"] or sig["agenda_dagen"] or sig["nevenfunctie"]):
                    a["status"] = "rapport: nieuw, onder de drempel"
                    self.tel["paar: nieuw onder de drempel (rapport)"] += 1
                    continue
                naam = self.nieuwe_orgs[ref[1]]["naam"]
                recs = [r for r in recs if giften.zelfde_gever(r["gever"], naam)
                        or sleutel(self.schrijfwijzen.get(sleutel(r["gever"]), "")) == sleutel(naam)]
                if not recs:
                    a["status"] = "rapport: geen record noemt de gekozen naam"
                    continue
            s_id = ref[1] if ref[0] == "bestaand" else None
            rid = self.donor.get((s_id, pid)) if s_id else None
            if ref[0] == "nieuw":
                gedateerd = {(pid, d, round(b, 2)) for r in recs for b, d in r["bedragen"] if d and b}
                anderen = {o for g in gedateerd for o in self.gift_index.get(g, ()) if o != ref and o[0] == "bestaand"}
                if gedateerd and all(any(o in anderen for o in self.gift_index[g]) for g in gedateerd):
                    namen = sorted(self.gever_naam.get(o, "?") for o in anderen)
                    a["status"] = f"rapport: dezelfde gift(en) staan in een ander overzicht op naam van {', '.join(namen)}"
                    self.andere_naam.append({"gever": a["gever"], "partij": a["partij"], "totaal": a["totaal"],
                                             "ook_als": namen, "giften": sorted(g[1:] for g in gedateerd)})
                    self.tel["paar: zelfde gift onder een andere naam (rapport)"] += 1
                    continue
            if rid is None and (ref[0] == "nieuw" or s_id in self.org):
                dubbel = self._dubbel(a, recs, pid)
                if dubbel:
                    a["status"] = f"rapport: zelfde gift staat mogelijk al als {dubbel['persoon']} → {a['partij']} (#{dubbel['relation_id']})"
                    self.dubbel.append(dubbel)
                    self.tel["paar: mogelijk dubbel met een persoon → partij (rapport)"] += 1
                    continue
            if ref[0] == "nieuw":
                self.nieuwe_orgs[ref[1]]["_gepland"] = True
            if ref[0] == "bestaand" and ref[1] not in self.org and rid is None and \
                    not any(self.hand_personen.get(f"{r['gever']}|{r['partij_label']}") for r in recs):
                a["status"] = "rapport: persoon zonder bestaand donorverband"
                continue
            if rid:
                van, tot = self.rel_looptijd.get(rid, (None, None))
                binnen = [r for r in recs if any(_binnen(d, van, tot) for d in self._datums(r))]
                for r in recs:
                    if r not in binnen:
                        self.buiten_looptijd.append({"relation_id": rid, "gever": a["gever"], "partij": a["partij"],
                                                     "looptijd": [van, tot], "giftdata": self._datums(r),
                                                     "uitgave": r["_uitgave"], "sleutel": r["sleutel"]})
                        self.tel["extra bron: gift buiten de looptijd van het verband (rapport)"] += 1
                recs = binnen
            nieuw_rec = [r for r in recs if r["sleutel"] not in self.geciteerd.get(rid, set())][:MAX_PER_VERBAND] if rid else recs[:MAX_PER_VERBAND]
            if rid:
                a["status"] = "versterkt" if nieuw_rec else (
                    "bestaand verband (al geciteerd)" if recs else "bestaand verband (geen gift binnen de looptijd)")
                a["relation_id"] = rid
                self.tel["paar: bestaand verband, extra bron"] += 1
                for r in nieuw_rec:
                    self.extra_bron.append(self._arg(ref, pid, r, rid))
                continue
            a["status"] = "nieuw"
            self.tel["paar: nieuw verband"] += 1
            functie = "Giften volgens de Wfpp-overzichten: " + "; ".join(
                f"{j} {giften.euro(b)}" for j, b in sorted(a["per_jaar"].items()) if b)
            voor = len(self.relaties)
            self._rel(ref, ("bestaand", pid), "donor", MECH, nieuw_rec[0], self._claim(nieuw_rec[0]),
                      functie=functie[:200], start=a["van"], eind=a["tot"])
            if len(self.relaties) > voor:
                self.relaties[-1].update(score=a["score"], argumenten=[self._arg(ref, pid, r, None) for r in nieuw_rec])

    @staticmethod
    def _datums(r: dict) -> list[str]:
        """De giftdata van een record; zonder data de jaren met een bedrag, anders het jaar."""
        return sorted({d for _, d in r["bedragen"] if d}) or sorted(j for j, b in r["per_jaar"].items() if b) \
            or ([r["jaar"]] if r["jaar"] else [])

    def _dubbel(self, a: dict, recs: list[dict], pid: int) -> dict | None:
        """Staat dezelfde gift al in het model als persoon → partij? Ja als een publieke persoon met
        een donorverband naar deze partij de UBO van de gever lijkt (in welk overzicht ook), of als
        een bewering op dat verband de gever noemt ('via Movet Beheer bv'). Alleen tegenhouden en
        melden: nooit koppelen op naam."""
        k = gever_sleutel(a["gever"])
        kern = _kern(a["gever"])
        for (bron, doel), rid in self.donor.items():
            if doel != pid or bron in self.org:
                continue
            via_ubo = bron in self.ubo_personen.get(k, set())
            via_claim = bool(kern) and any(noemt(self.rel_claims.get(rid, ""), n) for n in
                                           {a["gever"], kern} | {r["gever"] for r in recs})
            if via_ubo or via_claim:
                return {"gever": a["gever"], "partij": a["partij"], "totaal": a["totaal"], "per_jaar": a["per_jaar"],
                        "persoon": self._persoonsnaam(bron), "persoon_id": bron, "relation_id": rid,
                        "hoe": "UBO lijkt de persoon" if via_ubo else "een bewering op het verband noemt de gever",
                        "citaat": a["citaat"]}
        return None

    def _claim(self, r: dict) -> str:
        d = self.data[r["_uitgave"]]
        nev = f" (neveninstelling {r['neveninstelling']})" if r["neveninstelling"] else ""
        wanneer = f", ontvangen {r['eerste']}" + (f" tot {r['laatste']}" if r["laatste"] != r["eerste"] else "") \
            if r["eerste"] else ""
        return (f"Volgens het {d['overzicht'][:1].lower() + d['overzicht'][1:]} (ministerie van BZK, versie "
                f"{d['versie']}) ontving {r['partij_label']}{nev} van {r['gever']} in totaal {giften.euro(r['totaal'])}"
                f"{wanneer}.")

    def _arg(self, ref, pid, r, rid) -> dict:
        return {"bron": ref, "doel": ("bestaand", pid), "relation_id": rid, "sleutel": r["sleutel"],
                "regel": r["regel"], "claim": self._claim(r), "uitgave": r["_uitgave"], "type": "donor",
                "mechanisme": MECH, "rec": r}

    def _ubo_index(self):
        """gever_sleutel → model-personen die de UBO lijken (precies één kandidaat, _past)."""
        self.ubo_personen: dict[str, set[int]] = defaultdict(set)
        self._ubo_treffers: list[tuple] = []
        for u, d in self.data.items():
            for s, namen in d.get("_ubo", {}).items():
                r = d["records"][s]
                for ubo in namen:
                    kand = self.kandidaten_persoon(ubo)
                    if len(kand) == 1:
                        self.ubo_personen[gever_sleutel(r["gever"])].add(kand[0][0])
                        self._ubo_treffers.append((u, r, kand, _naamdelen(ubo)))

    def _ubo(self):
        """Tips: een UBO van een gevende organisatie die een publieke persoon in het model lijkt
        (achternaam en voornaam of voorletters, precies één kandidaat; partij-eigen gevers niet).
        Alleen de modelnaam gaat het rapport in; de UBO-naam uit het overzicht niet."""
        gezien = set()
        for u, r, kand, ubo_delen in self._ubo_treffers:
            if (r["gever"], r["partij_label"], kand[0][0]) in gezien or tkm.UITSLUITEN.search(r["gever"]) \
                    or self._partij_eigen(r["gever"]):
                continue
            if (r["totaal"] or 0) < DREMPEL_NIEUW and not (ubo_delen[1] and kand[0][2][1]):
                continue   # een kleine gift en alleen een voorletter: te zwak voor een tip
            gezien.add((r["gever"], r["partij_label"], kand[0][0]))
            self.ubo_tips.append({"organisatie": r["gever"], "partij": r["partij_label"],
                                  "totaal": r["totaal"], "uitgave": u, "lijkt": kand[0][1], "id": kand[0][0],
                                  "bestaand_donorverband_persoon": self.donor.get(
                                      (kand[0][0], self.partij_id.get(r["partij"] or "", -1)))})

    def _zelfcontrole(self):
        """Wat de registercheck zou afkeuren, wordt niet gepland (giften.controleer)."""
        def ok(arg, bron_naam, bron_type):
            data = self.data[arg["uitgave"]]
            eind = [{"name": bron_naam, "type": bron_type, "ids": set()},
                    {"name": self.org[arg["doel"][1]][0], "type": "partij", "ids": set()}]
            reden = giften.controleer(data, arg["sleutel"], arg["rec"], "donor", eind)
            if reden:
                self.tel[f"zelfcontrole: {reden.split(':')[0][:60]}"] += 1
            return not reden

        def naam_type(ref):
            if ref[0] == "nieuw":
                return self.nieuwe_orgs[ref[1]]["naam"], self.nieuwe_orgs[ref[1]]["type"]
            if ref[1] in self.org:
                return self.org[ref[1]][0], self.org[ref[1]][1]
            return self._persoonsnaam(ref[1]), "persoon"
        self.extra_bron = [a for a in self.extra_bron if ok(a, *naam_type(a["bron"]))]
        for r in self.relaties:
            r["argumenten"] = [a for a in r["argumenten"] if ok(a, *naam_type(a["bron"]))]
        self.relaties = [r for r in self.relaties if r["argumenten"]]
        nodig = {r["bron"][1] for r in self.relaties if r["bron"][0] == "nieuw"}
        self.nieuwe_orgs = {k: v for k, v in self.nieuwe_orgs.items() if k in nodig}


class Indiener(tkm.Indiener):
    """Nieuwe organisaties zoals de Kamerregisters; per verband meer argumenten, een bron per
    uitgave (elk overzicht is een eigen document)."""

    def __init__(self, plan: Plan, rest, log=print):
        super().__init__(plan, rest, log, bron=giften, cluster=CLUSTER)
        self.bronnen: dict[str, int] = {}

    def bron_van(self, uitgave: str) -> int:
        if uitgave not in self.bronnen:
            d = self.p.data[uitgave]
            status, res = self.rest("POST", "/api/sources", {
                "title": d["titel"], "source_type": "dataset", "publisher": giften.UITGEVER,
                "date_published": d["versie"], "cluster_key": self.cluster,
                "location": {"type": "url", "value": d["url"]},
                "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
            if status not in (200, 201):
                raise SystemExit(f"bron registreren faalde: {status} {res}")
            self.bronnen[uitgave] = res["id"]
        return self.bronnen[uitgave]

    def _argument(self, rid: int, a: dict):
        status, res = self.rest("POST", "/api/arguments", {
            "relation_id": rid, "claim": a["claim"], "stance": "supporting",
            "citations": [{"source_id": self.bron_van(a["uitgave"]), "quote": a["regel"],
                           "methode": "officieel_register_scrape", "section": a["sleutel"],
                           "page": f"{giften.BRON}/{a['uitgave']}", "context": self.p.data[a["uitgave"]]["pagina"]}]})
        self.tel["argument" if status == 201 else f"argument fout {status}"] += 1
        if status != 201:
            self.log(f"  ✗ argument {a['sleutel']} op #{rid}: {status} {res.get('error')}")

    def relaties(self, bron_id: int | None = None):
        for r in self.p.relaties:
            s, t = self._id(r["bron"]), self._id(r["doel"])
            if not s or not t:
                self.tel["relatie zonder eindpunt"] += 1
                continue
            body = {"source_id": s, "target_id": t, "relation_type": r["type"],
                    "mechanism_id": self.p.mech[r["mechanisme"]]}
            for veld, waarde in (("functie", r["functie"]), ("active_from", r["start"]), ("active_until", r["eind"])):
                if waarde:
                    body[veld] = waarde
            status, res = self.rest("POST", "/api/relations", body)
            if status != 201:
                self.tel[f"relatie fout {status}"] += 1
                self.log(f"  ✗ relatie donor {s}→{t}: {status} {res.get('error')}")
                continue
            self.tel["relatie nieuw"] += 1
            for a in r["argumenten"]:
                self._argument(res["id"], a)
        for a in self.p.extra_bron:
            self._argument(a["relation_id"], a)


# ── rapport ─────────────────────────────────────────────────────────────────
def per_partij_jaar(plan: Plan) -> dict:
    """Per partij en jaar: het aantal gevers en het bedrag, organisaties en personen apart; een
    gift die in meer overzichten staat telt één keer (jaartotalen per gever en partij)."""
    groepen: dict[tuple, list[dict]] = defaultdict(list)
    soort: dict[tuple, str] = {}
    for u, d in plan.data.items():
        for r in d["records"].values():
            k = (r["partij"] or r["partij_label"], gever_sleutel(r["gever"]))
            groepen[k].append({**r, "_uitgave": u})
            soort[k] = "personen" if r["gever_soort"] == "persoon" else "organisaties"
    uit: dict = defaultdict(lambda: defaultdict(lambda: {"organisaties": 0, "personen": 0,
                                                          "bedrag_organisaties": 0.0, "bedrag_personen": 0.0}))
    for k, recs in groepen.items():
        for j, b in jaartotalen(recs).items():
            cel = uit[k[0]][j]
            cel[soort[k]] += 1
            cel["bedrag_" + soort[k]] = round(cel["bedrag_" + soort[k]] + b, 2)
    return {p: dict(sorted(v.items())) for p, v in sorted(uit.items())}


def rapport(plan: Plan) -> dict:
    gekozen = [a for a in plan.analyse if a["status"] and not a["status"].startswith("rapport")]
    uitgaven = [{"uitgave": u, "overzicht": d["overzicht"], "versie": d["versie"], "records": len(d["records"]),
                 "organisaties": sum(1 for r in d["records"].values() if r["gever_soort"] == "organisatie"),
                 "persoonlijke_vennootschappen": sum(1 for r in d["records"].values()
                                                     if r["gever_soort"] == "persoonlijke_vennootschap"),
                 "personen": sum(1 for r in d["records"].values() if r["gever_soort"] == "persoon"),
                 "sha256": d["sha256"], "url": d["url"]} for u, d in sorted(plan.data.items())]

    def rij(a):
        return {k: a[k] for k in ("score", "gever", "gever_soort", "partij", "totaal", "per_jaar", "partijen_gever",
                                  "jaren_gever", "signalen", "neveninstellingen", "status", "van", "citaat")}
    return {
        "uitgave": plan.uitgave, "uitgaven": uitgaven,
        "nieuwe_verbanden": len(plan.relaties),
        "argumenten_op_nieuwe_verbanden": sum(len(r["argumenten"]) for r in plan.relaties),
        "extra_bronnen_op_bestaande_verbanden": len(plan.extra_bron),
        "bestaande_verbanden_versterkt": len({a["relation_id"] for a in plan.extra_bron}),
        "nieuwe_organisaties": sorted(o["naam"] for o in plan.nieuwe_orgs.values()),
        "niet_gekoppeld_privé": {k: {"records": v, "bedrag": round(plan.privé_bedrag[k], 2)} for k, v in plan.privé.items()},
        "telling": {k: v for k, v in sorted(plan.tel.items()) if v},
        "per_partij_jaar": per_partij_jaar(plan),
        "top": [rij(a) for a in gekozen[:TOP]],
        "rapport_niet_gepland": [rij(a) for a in plan.analyse
                                 if a["status"] and a["status"].startswith("rapport") and a["gever_soort"] != "persoon"][:TOP],
        "ubo_tips": plan.ubo_tips,
        "mogelijk_dubbel_met_persoon": plan.dubbel,
        "zelfde_gift_andere_naam": plan.andere_naam,
        "buiten_looptijd": plan.buiten_looptijd,
        "extra_bron": [{"relation_id": a["relation_id"], "gever": plan.gever_naam.get(a["bron"]),
                        "partij": plan.org[a["doel"][1]][0], "citaat": a["regel"]} for a in plan.extra_bron],
    }


def rapport_md(rap: dict) -> str:
    r = ["# Giften aan politieke partijen: opvallende gevers", "",
         f"Nieuwe verbanden: {rap['nieuwe_verbanden']} (argumenten {rap['argumenten_op_nieuwe_verbanden']}) · "
         f"extra bronnen op bestaande verbanden: {rap['extra_bronnen_op_bestaande_verbanden']} "
         f"({rap['bestaande_verbanden_versterkt']} verbanden) · nieuwe organisaties: {len(rap['nieuwe_organisaties'])}", "",
         "Score = bedrag × herhaling × spreiding over partijen × lobby × agenda × nevenfuncties × in model "
         "(× 0,3 bij een nalatenschap); zie giften_naar_model.py.", "",
         "| # | score | gever | partij | totaal | jaren | ook aan | signalen | status |", "|---|---|---|---|---|---|---|---|---|"]
    for i, a in enumerate(rap["top"], 1):
        s = a["signalen"]
        sig = ", ".join(x for x in (("lobby" if s["lobby"] else ""), (f"agenda {s['agenda_dagen']}d" if s["agenda_dagen"] else ""),
                                    (f"nevenfunctie {s['nevenfunctie']}" + (" (eigen partij)" if s["nevenfunctie_partij"] else "")
                                     if s["nevenfunctie"] else "")) if x)
        ook = ", ".join(p for p in a["partijen_gever"] if p != a["partij"])
        r.append(f"| {i} | {a['score']} | {a['gever']} | {a['partij']} | {giften.euro(a['totaal'])} | "
                 f"{', '.join(a['per_jaar'])} | {ook} | {sig} | {a['status']} |")
    r += ["", "## Per partij en jaar (gevers; een gift in meer overzichten één keer)", "",
          "| partij | jaar | organisaties | bedrag | personen | bedrag |", "|---|---|---|---|---|---|"]
    for p, jaren in rap["per_partij_jaar"].items():
        for j, c in jaren.items():
            r.append(f"| {p} | {j} | {c['organisaties']} | {giften.euro(c['bedrag_organisaties'])} | {c['personen']} | "
                     f"{giften.euro(c['bedrag_personen'])} |")
    r += ["", "## Niet geplaatst (privacy en ruis)", ""]
    r += [f"- {k}: {v['records']} records, {giften.euro(v['bedrag'])}" for k, v in rap["niet_gekoppeld_privé"].items()]
    if rap["mogelijk_dubbel_met_persoon"]:
        r += ["", "## Niet gepland: dezelfde gift staat mogelijk al als persoon → partij", "",
              "Het register noemt de organisatie als gever; het model heeft de persoon. Kies met de hand: "
              "organisatie → partij plus een band persoon — organisatie, of het bestaande verband laten.", ""]
        r += [f"- {d['gever']} → {d['partij']} ({giften.euro(d['totaal'])}): {d['persoon']} → {d['partij']} "
              f"#{d['relation_id']} ({d['hoe']})" for d in rap["mogelijk_dubbel_met_persoon"]]
    if rap["zelfde_gift_andere_naam"]:
        r += ["", "## Niet gepland: dezelfde gift onder een andere naam in een ander overzicht", ""]
        r += [f"- {d['gever']} → {d['partij']} ({giften.euro(d['totaal'])}) staat ook als {', '.join(d['ook_als'])}"
              for d in rap["zelfde_gift_andere_naam"]]
    if rap["buiten_looptijd"]:
        r += ["", "## Giften buiten de looptijd van een bestaand verband (looptijd met de hand verruimen?)", ""]
        r += [f"- #{b['relation_id']} {b['gever']} → {b['partij']} (looptijd {b['looptijd'][0]}–{b['looptijd'][1] or ''}): "
              f"gift {', '.join(b['giftdata'])} ({b['uitgave']})" for b in rap["buiten_looptijd"]]
    if rap["ubo_tips"]:
        r += ["", "## Tips: UBO lijkt een publieke persoon in het model (niet gepland, met de hand nagaan)", ""]
        r += [f"- {t['organisatie']} → {t['partij']} ({giften.euro(t['totaal'])}, {t['uitgave']}): UBO lijkt "
              f"{t['lijkt']} (#{t['id']})" + (f"; die persoon heeft al donorverband #{t['bestaand_donorverband_persoon']}"
                                                if t["bestaand_donorverband_persoon"] else "") for t in rap["ubo_tips"]]
    return "\n".join(r) + "\n"


def lees_alle(alle_versies: bool = False) -> dict[str, dict]:
    keuze = [giften.uitgave_van(p) for p in giften.uitgaven()] if alle_versies else list(giften.nieuwste_per_reeks().values())
    return {u: giften.lees_uitgave(u) for u in sorted(keuze)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--haal", action="store_true", help="eerst nieuwe overzichten ophalen")
    ap.add_argument("--indienen", action="store_true")
    ap.add_argument("--top", type=int, default=TOP)
    a = ap.parse_args()
    if a.haal:
        for p in giften.haal():
            print(f"nieuw: {p.name}")
    data = lees_alle()
    if not data:
        raise SystemExit("nog geen uitgave; eerst: python3 tools/registers/giften.py haal")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(data, conn, koppelingen)
    plan.signalen()
    plan.maak()
    rap = rapport(plan)
    datum = datetime.date.today().isoformat()
    (giften.MAP / f"rapport_{datum}.json").write_text(json.dumps(rap, ensure_ascii=False, indent=1), encoding="utf-8")
    (giften.MAP / "rapport.md").write_text(rapport_md(rap), encoding="utf-8")
    print(json.dumps({k: rap[k] for k in ("nieuwe_verbanden", "argumenten_op_nieuwe_verbanden",
                                          "extra_bronnen_op_bestaande_verbanden", "bestaande_verbanden_versterkt")}
                     | {"nieuwe_organisaties": len(rap["nieuwe_organisaties"]), "niet_gekoppeld": rap["niet_gekoppeld_privé"],
                        "telling": rap["telling"]}, ensure_ascii=False, indent=1))
    print(f"\nTop {a.top} (score = bedrag × herhaling × partijen × lobby × agenda × nevenfuncties × in model):")
    for i, t in enumerate(rap["top"][:a.top], 1):
        print(f"{i:>3}. {t['score']:>6}  {t['gever']} → {t['partij']}  {giften.euro(t['totaal'])}  [{t['status']}]\n"
              f"       “{t['citaat']}”")
    if not a.indienen:
        print(f"\n(droogloop — niets ingediend; rapport in {giften.MAP}/rapport_{datum}.json en rapport.md)")
        return
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()))
    ind.entiteiten()
    ind.relaties()
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
