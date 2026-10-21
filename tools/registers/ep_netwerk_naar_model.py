#!/usr/bin/env python3
"""Het netwerk rond de Nederlandse Europarlementariërs → het model (onderzoek 2026-10-20).

ep_netwerk.py leest de uitgave (EP open data, de verklaringen en vergaderingen van leden en het
EU-transparantieregister; geen Parltrack: parltrack.org weert ClaudeBot in robots.txt). Dit script
kiest wat een structureel verband is en plant het, naast wat ep_naar_model.py al doet (zetel,
fractie en nationale partij). Een lid koppelt alleen via zijn externe id `ep_mep` (die
ep_naar_model.py heeft gezet), nooit op naam; een lid zonder die id slaat het over.

Structureel (wordt een verband):
  - commissiezetels die nu lopen → `ambt`/`kamerzetel` van het lid bij '<commissie> (Europees
    Parlement)', een knoop zoals '<commissie> (Tweede Kamer)' (overheidsinstelling, rol
    parlementair_controleur, bestuurslaag eu). Geen delegaties.
  - de opgave van particuliere belangen (nieuwste versie): rubriek B, C (lopend) en D (deelneming)
    → `nevenfunctie_verstrengeling`; rubriek A (de drie jaar vóór het mandaat) →
    `draaideurconstructie`, onder dezelfde regels als de Kamerregisters: een organisatie die al in het
    model staat, of nieuw met rechtsvorm in de naam bij een leidende of adviserende functie; geen
    politieke ambten, partijen (ook Europese), het parlement zelf of een eigen vennootschap.
  - een verklaring van deelname aan een evenement dat een derde betaalde → `geschenk`/
    `geschenk_en_gastvrijheid` van die derde naar het lid, alleen als de derde al in het model staat
    en geen overheid is (zoals de reizen van Kamerleden).
  - vergaderingen met een organisatie die al in het model staat (geen overheid, partij, rechter,
    toezichthouder of medium) op minstens MIN_DAGEN verschillende dagen → `lobbyt` organisatie → lid,
    mechanisme `lobbyist_naar_politicus` (een denktank: `denktank_naar_politiek`); elke vergadering
    een argument (hooguit MAX_PER_VERBAND per verband per run, de nieuwste eerst).
  - bestaat het verband al (zelfde paar; een affiliatie of `lobbyt`), dan alleen een extra argument.
Alleen een tip (rapport, geen verband): één vergadering, vergaderingen met organisaties die niet in
het model staan (met land en categorie uit het transparantieregister), rapporteurschappen (geen
dossierknoop in de theorie), steun van derden (rubriek E). Stemmen en amendementen worden niet
opgehaald (eerst theorie).

Opvallendheid (score), niet volume:
  vergadering: dagen × log2(lift) × (1 + rapporteursgewicht); lift = vergaderingen van deze
    organisatie met dit lid ÷ verwacht als zij haar vergaderingen gelijk over alle Nederlandse
    leden had verdeeld (agenda_naar_model.py). Wie iedereen spreekt, scoort laag. Het
    rapporteursgewicht per vergadering is het hoogste van de hoedanigheid in de vergadering zelf en
    het (schaduw)rapporteurschap voor dezelfde procedure uit de verklaringen over
    belangenconflicten (open data): rapport 1,0, advies 0,75, commissievoorzitter 0,5.
  belang: organisatiesoort × functiesoort × bezoldiging × 1,5 als de organisatie in het model staat
    (rechtspraak_naar_model.org_soort); loopbaan × 0,8.
  deelname: organisatiesoort × 2 (een derde betaalde reis of verblijf).
Het rapport (data/registers/ep_netwerk/rapport_<uitgave>.json en .md) geeft de nieuwe verbanden,
de extra bronnen op bestaande verbanden, de top-30 en de tips.

Gebruik:
    python3 tools/registers/ep_netwerk_naar_model.py                 # droogloop + rapport
    python3 tools/registers/ep_netwerk_naar_model.py --haal          # ± 10 minuten (Crawl-delay 2 s)
    python3 tools/registers/ep_netwerk_naar_model.py --indienen      (vergt eerst 'ep_netwerk' in
                                                                       scripts/registercheck.BRONNEN)
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
import ep_netwerk as en  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ROOT, noemt, schoon, sleutel  # noqa: E402
from naar_model import TOKEN, Rest  # noqa: E402
from rechtspraak_naar_model import PRIVE_BV, org_soort  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:ep_netwerk"
EP_WIKIDATA = "Q8889"
MIN_DAGEN = 2
MAX_PER_VERBAND = 5
TOP = 30
UITGESLOTEN_TYPES = {"overheidsinstelling", "partij", "rechterlijke_macht", "toezichthouder",
                     "mediaorganisatie", "omroep", "persbureau"}
AFFILIATIE = {"bestuurder", "adviseur", "lidmaatschap", "personeel", "eigendom", "dienstverband",
              "draaideur", "ambt", "lobbyt", "geschenk"}
CAP_GEWICHT = {"rapporteur": 1.0, "schaduwrapporteur": 1.0, "rapporteur voor advies": 0.75,
               "shadow rapporteur for opinion": 0.75, "commissievoorzitter": 0.5}
# Europese partijen, fracties en hun staf, het parlement zelf en informele groepen: geen organisatie
# voor een nevenfunctie of loopbaan (zoals partijen en de Kamer zelf bij de Kamerregisters)
EP_INTERN = re.compile(
    r"\b(europe(es|an) parlement|european parliament|parlement europeen|\bapa\b|accredited parliamentary|"
    r"medewerker in het europees|group staff|fractiemedewerker|\bepp\b|\balde\b|renew europe|\bs ?& ?d\b|"
    r"greens ?/ ?efa|\becr\b|patriots for europe|europe of sovereign|volt europa|european people s party|"
    r"alliance of liberals|unofficial grouping|informal grouping|intergroup|friendship group|caucus|"
    r"kiescollege|congres van de lokale|comite van de regio|committee of the regions)\b", re.I)
WOORD_EIGENDOM = re.compile(r"\b(eigenaar|mede ?eigenaar|aandeelhouder|shareholder|owner|co ?owner|dga|vennoot|firmant)\b", re.I)
WOORD_ADVIES = re.compile(r"\b(raad van advies|adviesraad|advisory|adviescommissie|adviseur|klankbord)\w*", re.I)
WOORD_BESTUUR = re.compile(
    r"\b(voorzitter|vicevoorzitter|bestuurslid|bestuurder|bestuur|board|supervisory|raad van toezicht|rvt|rvc|"
    r"raad van commissarissen|commissaris|toezichthouder|chair\w*|president|director|directeur\w*|treasurer|"
    r"penningm\w*|secretaris|trustee)\b", re.I)
WOORD_LID = re.compile(r"\b(lid|member|ambassadeur|ambassador|comite van aanbeveling|commitee van aanbeveling)\b", re.I)
VERBINDERS = re.compile(r"\s+(?:-|–|at|bij|aan|van|of|for|in)\s+(?:de |het |the )?|,\s*|:\s*", re.I)
DATUM_IN_TEKST = re.compile(
    r"\(([^)]*\d{4}[^)]*)\)|\b(?:tot|until|to)\s+[\d./]*\d{4}\b|\b(?:vanaf|since|from)\s+[\d./]*\d{4}\b", re.I)


MAANDEN = {k: i for i, ks in enumerate((("jan",), ("feb",), ("maa", "mar"), ("apr",), ("mei", "may"), ("jun",),
                                        ("jul",), ("aug",), ("sep",), ("okt", "oct"), ("nov",), ("dec",)), 1)
           for k in ks}


def _jaar_maand(tekst: str) -> tuple[str | None, str | None]:
    """'(vanaf 06/2022 tot 08/2024)' → ('2022-06', '2024-08'); '(until June 2024)' → (None, '2024');
    'Tot 1.3.2021' → (None, '2021-03-01'); '(2021-07/2024)' → ('2021', '2024-07')."""
    def dat(w: str) -> str | None:
        w = w.strip()
        m = re.search(r"(?:(\d{1,2})\s+)?([a-z]{3,9})\s+(\d{4})", w)
        if m and m.group(2)[:3] in MAANDEN:
            mnd = f"{m.group(3)}-{MAANDEN[m.group(2)[:3]]:02d}"
            return f"{mnd}-{int(m.group(1)):02d}" if m.group(1) else mnd
        m = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", w)
        if m:
            return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
        m = re.search(r"(\d{1,2})[./](\d{4})", w)
        if m:
            return f"{m.group(2)}-{int(m.group(1)):02d}"
        m = re.search(r"(\d{4})", w)
        return m.group(1) if m else None
    t = tekst.lower()
    van = tot = None
    mnd = r"(?:\d{1,2}\s+)?[a-z]{3,9}\s+\d{4}"
    m = re.search(r"(?:tot|until|to|-|–)\s*(" + mnd + r"|[\d./]*\d{4})", t)
    if m:
        tot = dat(m.group(1))
    m = re.search(r"(?:vanaf|since|from|\()\s*(" + mnd + r"|[\d./]*\d{4})\s*(?:-|–|tot|to)", t)
    if m:
        van = dat(m.group(1))
    if not van:
        m = re.search(r"(?:vanaf|since|from)\s*(" + mnd + r"|[\d./]*\d{4})", t)
        van = dat(m.group(1)) if m else None
    if van and tot and tot < van:
        tot = None
    return van, tot


def functie_rtype(tekst: str, rubriek: str) -> tuple[str, str, float]:
    """→ (relatietype, functiesoort, gewicht)."""
    if rubriek == "D" or WOORD_EIGENDOM.search(tekst):
        return "eigendom", "eigendom", 3.0
    if re.search(r"\b(raad van toezicht|supervisory|rvt|rvc|raad van commissarissen|commissaris|toezichthouder)\b",
                 tekst, re.I):
        return "bestuurder", "toezicht", 3.0
    if WOORD_ADVIES.search(tekst):
        return "adviseur", "advies", 2.0
    if WOORD_BESTUUR.search(tekst):
        return "bestuurder", "bestuur", 2.0
    if rubriek == "A" or re.search(r"\b(manager|officer|adviser|advisor|consultant|medewerker|hoogleraar|"
                                   r"persvoorlichter|campagneleider|strateeg|beleidsmedewerker|freelancer|"
                                   r"in dienst|employee)\b", tekst, re.I):
        return "personeel", "dienstverband", 1.0
    if WOORD_LID.search(tekst):
        return "lidmaatschap", "lid", 1.0
    return "lidmaatschap", "onbekend", 0.5


class Plan(tkm.Plan):
    def __init__(self, data: dict, conn: sqlite3.Connection, koppelingen: dict | None = None):
        super().__init__({"uitgave": data["uitgave"], "personen": {}, "records": {}}, conn, koppelingen)
        self.pt = data
        self.mech.update(self._ids("mechanisms", ("lobbyist_naar_politicus", "denktank_naar_politiek")))
        self.org_rol = {i: r for i, r in conn.execute(
            "SELECT e.id, r.name FROM entities e LEFT JOIN roles r ON r.id = e.primary_role_id")}
        self.ext_ep = {w: e for e, w in conn.execute("SELECT entity_id, waarde FROM externe_ids WHERE stelsel = 'ep_mep'")}
        rij = conn.execute("SELECT entity_id FROM externe_ids WHERE stelsel = 'wikidata' AND waarde = ?",
                           (EP_WIKIDATA,)).fetchone()
        self.parlement = rij[0] if rij else None
        self.naam_ent = {i: n for i, n in conn.execute("SELECT id, name FROM entities")}
        self.paren_bestaand: dict[tuple[int, int], list[tuple[int, str, str, int]]] = defaultdict(list)
        for rid, s, t, typ, st in conn.execute(
                "SELECT id, source_id, target_id, relation_type, status FROM relations "
                "WHERE NOT vervangen AND status <> 'afgewezen'"):
            self.paren_bestaand[(min(s, t), max(s, t))].append((rid, typ, st, s))
        self.al_geciteerd = {(r, sec) for r, sec in conn.execute("""
            SELECT a.relation_id, c.section FROM citations c JOIN arguments a ON a.id = c.argument_id
            WHERE c.page LIKE 'ep_netwerk/%' AND a.relation_id IS NOT NULL""")}
        self.extra: list[dict] = []          # extra argumenten (op een bestaand of een gepland verband)
        self.kandidaten: list[dict] = []     # alles wat gescoord is, ook niet gepland
        self.tips: dict[str, list] = defaultdict(list)
        self.lid_ontbreekt: set[str] = set()

    # ── hulp ───────────────────────────────────────────────────────────────
    def _lid(self, rec: dict) -> tuple | None:
        eid = self.ext_ep.get(rec["persoon_id"])
        if not eid:
            self.lid_ontbreekt.add(rec["persoon_id"])
            return self._mis(rec["soort"], rec, "lid niet in het model met externe id ep_mep (eerst ep_naar_model.py)")
        return ("bestaand", eid)

    def _naam(self, ref: tuple) -> str:
        return self.nieuwe_orgs[ref[1]]["naam"] if ref[0] == "nieuw" else (
            self.naam_ent.get(ref[1]) or self.org.get(ref[1], ("?",))[0])

    def _uitgesloten_org(self, eid: int, context: str) -> str | None:
        naam, typ, laag = self.org[eid]
        if eid == self.parlement or EP_INTERN.search(sleutel(naam)):
            return "het parlement, een Europese partij of fractie"
        reden = self._toegestaan(eid, context)
        if reden:
            return reden
        if context in ("vergadering", "deelname") and (typ in UITGESLOTEN_TYPES or laag):
            return f"geen lobbypartij ({typ})"
        if context in ("vergadering", "deelname") and "journalist" in (self.org_rol.get(eid) or ""):
            return "geen lobbypartij (journalistiek)"
        return None

    def _alleen_afkorting(self, eid: int, teksten: list[str]) -> bool:
        """Gevonden op alleen de afkorting ('EBU' → European Broadcasting Union, terwijl de European
        Barge Union bedoeld is): de naam zonder haakjes staat in geen van de teksten, en ook geen
        uitgeschreven vorm tussen haakjes ('FNV (Federatie Nederlandse Vakbeweging)')."""
        naam = self.org[eid][0]
        vormen = [tkm.zonder_haakjes(naam)] + [
            v.strip() for v in re.findall(r"\(([^)]*)\)", naam) if " " in v.strip() and len(sleutel(v)) > 6]
        return not any(noemt(t, v) for t in teksten if t for v in vormen if v)

    def _zoek_org(self, kandidaten: list[str], context: str, rec: dict) -> tuple | None:
        """De eerste kandidaat die (ruim) in het model staat; None als geen enkele."""
        for k in kandidaten:
            k = self._schoon_naam(k)
            if len(sleutel(k)) < 3:
                continue
            gevonden = self._bestaand(k, ruim=True)
            if gevonden and self._alleen_afkorting(gevonden[0], kandidaten):
                self._mis(context, rec, f"alleen de afkorting van '{self.org[gevonden[0]][0]}' (niet bevestigd)")
                return ("uitgesloten", None)
            if gevonden:
                reden = self._uitgesloten_org(gevonden[0], context)
                if reden:
                    self._mis(context, rec, reden)
                    return ("uitgesloten", None)
                return self._gekoppeld(rec, gevonden[0], gevonden[1], k)
        return None

    def _score_org(self, ref: tuple | None, tekst: str) -> tuple[str, float]:
        model_type = self.org[ref[1]][1] if ref and ref[0] in ("bestaand", "oo") else None
        return org_soort(tekst, model_type)

    def _plan(self, bron, doel, rtype, mech, rec, claim, *, functie=None, start=None, eind=None,
              score=0.0, soort="", extra_recs=()):
        """Nieuw verband, of een extra argument als het paar al een passend verband heeft."""
        s, t = (x[1] if x[0] == "bestaand" else None for x in (bron, doel))
        bestaand = [x for x in self.paren_bestaand.get((min(s, t), max(s, t)), []) if x[1] in AFFILIATIE] \
            if s and t else []
        if rtype == "lobbyt":
            bestaand = [x for x in bestaand if x[1] == "lobbyt" and x[3] == s]
        if bestaand:
            rel_id, typ, st, _ = sorted(bestaand, key=lambda x: (x[1] != rtype, x[0]))[0]
            for r in (rec, *extra_recs):
                if (rel_id, r["sleutel"]) in self.al_geciteerd:
                    self.tel["bestaand verband, record al geciteerd"] += 1
                    continue
                self.extra.append({"relation_id": rel_id, "bestaand_type": typ, "bestaand_status": st,
                                   "bron": bron, "doel": doel, "type": rtype, "sleutel": r["sleutel"],
                                   "regel": r["regel"], "claim": self._claim(r), "soort": soort, "score": score})
                self.tel["bestaand verband: extra bron"] += 1
            return
        n = len(self.relaties)
        self._rel(bron, doel, rtype, mech, rec, claim, functie=functie, start=start, eind=eind)
        if len(self.relaties) > n:
            self.relaties[-1].update(score=round(score, 2), soort=soort)
            for r in extra_recs:
                self.extra.append({"relation_id": None, "bron": bron, "doel": doel, "type": rtype,
                                   "sleutel": r["sleutel"], "regel": r["regel"], "claim": self._claim(r),
                                   "soort": soort, "score": score})
                self.tel["extra argument op nieuw verband"] += 1

    def _claim(self, rec: dict) -> str:
        u = self.uitgave
        if rec["soort"] == "vergadering":
            return (f"Volgens de door het Europees Parlement gepubliceerde vergaderingen van leden (uitgave {u}) "
                    f"sprak {rec['naam']} op {rec['datum']} als {rec['hoedanigheid']}"
                    + (f" (procedure {rec['procedure']})" if rec.get("procedure") else "")
                    + f" met {rec['aanwezig']} over '{rec['titel']}'.")
        if rec["soort"] == "commissie":
            return (f"Volgens de open data van het Europees Parlement (uitgave {u}) is {rec['naam']} "
                    f"{rec['rol'].lower()} van de "
                    f"{rec['commissie']} van het Europees Parlement" + (f" (sinds {rec['van']})." if rec.get("van") else "."))
        if rec["soort"] == "belang":
            wat = {"A": "in de drie jaar vóór het mandaat", "B": "als bezoldigde nevenactiviteit",
                   "C": "als lopende nevenfunctie", "D": "als deelneming", "E": "als steun van derden"}[rec["rubriek"]]
            return (f"Volgens de opgave van particuliere belangen van {rec['naam']} bij het Europees Parlement "
                    f"({rec['opgave']}) vermeldt het lid {wat}: {rec['tekst']}.")
        if rec["soort"] == "deelname":
            return (f"Volgens een verklaring van {rec['naam']} bij het Europees Parlement ({rec['titel']}) betaalde "
                    f"{rec['derde']} reis-, verblijf- of verblijfskosten voor een evenement"
                    + (f" ({rec['data']}" + (f", {rec['plaats']}" if rec.get("plaats") else "") + ")" if rec.get("data") else "")
                    + ".")
        return rec["regel"]

    # ── commissies ─────────────────────────────────────────────────────────
    def commissies(self):
        for rec in self.pt["records"].values():
            if rec["soort"] != "commissie":
                continue
            lid = self._lid(rec)
            if not lid:
                continue
            naam_c = en.commissie_naam(rec["commissie"])
            if (naam_c, "overheidsinstelling") in self.op_naam_type:
                ref = ("bestaand", self.op_naam_type[(naam_c, "overheidsinstelling")])
            elif sleutel(naam_c) in self.alle_namen:
                self._mis("commissie", rec, f"de naam '{naam_c}' is al van een andere knoop")
                continue
            else:
                k = f"epcommissie:{sleutel(naam_c)}"
                if k not in self.nieuwe_orgs:
                    self.nieuwe_orgs[k] = {
                        "naam": naam_c, "type": "overheidsinstelling", "rol": "parlementair_controleur",
                        "bestuurslaag": "eu",
                        "beschrijving": f"Commissie van het Europees Parlement"
                                        f"{' (' + rec['afkorting'] + ')' if rec.get('afkorting') else ''} (open data Europees Parlement)."}
                    self.tel["nieuwe EP-commissie"] += 1
                ref = ("nieuw", k)
            score = {"Voorzitter": 2.0, "Vicevoorzitter": 1.5, "Lid": 1.0}.get(rec["rol"], 0.5)
            self._plan(lid, ref, "ambt", "kamerzetel", rec, self._claim(rec),
                       functie=f"{rec['rol']}{' (' + rec['afkorting'] + ')' if rec.get('afkorting') else ''}",
                       start=rec.get("van"), score=score, soort="commissie")

    # ── opgave van particuliere belangen ───────────────────────────────────
    def belangen(self):
        per_lid = defaultdict(list)
        for rec in self.pt["records"].values():
            if rec["soort"] == "belang":
                per_lid[rec["persoon_id"]].append(rec)
        for uid, recs in per_lid.items():
            lopend = {sleutel(DATUM_IN_TEKST.sub(" ", r["tekst"])) for r in recs if r["rubriek"] in "BCD"}
            for rec in sorted(recs, key=lambda r: (r["rubriek"], r["nr"])):
                rub = rec["rubriek"]
                if rub == "E":
                    self.tips["steun_van_derden"].append({"lid": rec["naam"], "citaat": rec["regel"]})
                    self._mis("belang", rec, "steun van derden: geen mechanisme (tip)")
                    continue
                if rub == "A" and sleutel(DATUM_IN_TEKST.sub(" ", rec["tekst"])) in lopend:
                    self.tel["belang A ook lopend (B/C/D): één keer"] += 1
                    continue
                lid = self._lid(rec)
                if not lid:
                    continue
                self._belang(rec, lid)

    def _belang(self, rec: dict, lid: tuple):
        rub, tekst = rec["rubriek"], rec["tekst"]
        kaal = schoon(re.sub(r"\s+e\.\s?o\.?(?=\s|$)", " ", DATUM_IN_TEKST.sub(" ", tekst)))
        context = "loopbaan" if rub == "A" else "nevenfunctie"
        if EP_INTERN.search(sleutel(kaal)):
            return self._mis(context, rec, "het parlement, een Europese partij, fractie of informele groep")
        if tkm.POLITIEK_AMBT.search(kaal) or re.search(
                r"\b(wethouder|gedeputeerde|provinciale staten|gemeenteraad|waterschap|hoogheemraadschap)\b",
                kaal, re.I):
            return self._mis(context, rec, "politiek ambt")
        rtype, fsoort, fw = functie_rtype(kaal, rub)
        delen = [d for d in VERBINDERS.split(kaal) if d and len(sleutel(d)) >= 3]
        kandidaten = [kaal] + delen
        # functiewoorden vooraan weg ('Lid Raad van Toezicht Stichting X' → 'Stichting X')
        for k in list(kandidaten):
            m = re.match(r"^(?:(?:lid|member|voorzitter|chair|bestuurslid|board|of|van|the|de|het|raad van "
                         r"(?:toezicht|advies|commissarissen)|rvc|rvt|supervisory|advisory|director general|"
                         r"director|directeur(?:-bestuurder)?|treasurer|penningmeester|algemeen|dagelijks|"
                         r"senior|co-?president|vice[- ]?president|mede-eigenaar|eigenaar)\s+)+(.*)$", k, re.I)
            if m and m.group(1):
                kandidaten.append(m.group(1))
        ref = self._zoek_org(kandidaten, context, rec)
        if ref and ref[0] == "uitgesloten":
            return None
        if not ref:
            leidend = fsoort in ("eigendom", "toezicht", "advies", "bestuur")
            self._tr_tip(rec, kaal, context)
            if not leidend:
                return self._mis(context, rec, "niet in het model; geen leidende of adviserende functie")
            n = rec["naam"].split()[-1]
            vorm_kand = [k for k in kandidaten if tkm.rechtsvorm(self._schoon_naam(k))]
            if not vorm_kand:
                return self._mis(context, rec, "niet in het model en geen rechtsvorm in de naam")
            org = self._schoon_naam(min(vorm_kand, key=len))
            if PRIVE_BV.search(org) or sleutel(n) in sleutel(org).split():
                return self._mis(context, rec, "eigen vennootschap (privé)")
            if re.search(r"\bB\.?\s?V\.?$", org) and any(
                    r["soort"] == "belang" and r["persoon_id"] == rec["persoon_id"] and r["rubriek"] == "D"
                    and noemt(r["tekst"], org) for r in self.pt["records"].values()):
                return self._mis(context, rec, "eigen vennootschap (privé; ook als eigendom opgegeven)")
            kern = re.sub(r"\b(stichting|vereniging|cooperatie|foundation|b v|n v|bv|nv|u a|ua)\b", " ",
                          sleutel(org)).replace(" ", "")
            if len(kern) < 3:
                return self._mis(context, rec, "geen herkenbare eigen naam")
            ref = self._nieuw(org, context, rec)
            if not ref:
                return None
            self.nieuwe_orgs[ref[1]]["beschrijving"] = "Genoemd in een opgave van particuliere belangen bij het Europees Parlement."
        osoort, ow = self._score_org(ref, kaal)
        betaald = 1.5 if re.search(r"\d\s*(eur|€)", rec.get("waarde") or "", re.I) else 1.0
        in_model = 1.5 if ref[0] in ("bestaand", "oo") else 1.0
        score = ow * fw * betaald * in_model * (0.8 if rub == "A" else 1.0)
        van, tot = _jaar_maand(tekst)
        mech = "draaideurconstructie" if rub == "A" else "nevenfunctie_verstrengeling"
        self.kandidaten.append({"sleutel": rec["sleutel"], "score": round(score, 2), "soort": context,
                                "org_soort": osoort, "functie_soort": fsoort})
        self._plan(lid, ref, rtype, mech, rec, self._claim(rec), functie=kaal[:200], start=van,
                   eind=tot, score=score, soort=context)

    def _tr_tip(self, rec: dict, tekst: str, context: str):
        """Een organisatie die niet in het model staat maar wel in het transparantieregister (bv. een
        public-affairsbureau in de loopbaan): geen verband, wel een tip."""
        for o in self.pt["tr"].values():
            namen = [o["naam"]] + ([o["afkorting"]] if o.get("afkorting") and len(o["afkorting"]) >= 4 else [])
            if any(len(sleutel(n)) >= 5 and noemt(tekst, n) for n in namen):
                self.tips["belang_bij_lobbyorganisatie"].append({
                    "lid": rec["naam"], "soort": context, "organisatie": o["naam"], "tr_id": o["id"],
                    "categorie": o.get("categorie"), "land": o.get("land"), "citaat": rec["regel"]})
                return

    # ── deelname aan evenementen van derden ────────────────────────────────
    def deelnames(self):
        for rec in self.pt["records"].values():
            if rec["soort"] != "deelname":
                continue
            lid = self._lid(rec)
            if not lid:
                continue
            kand = [rec["derde"]] + [d for d in re.split(r",|\s+en\s+|\s+and\s+|\(|\)", rec["derde"]) if d.strip()]
            ref = self._zoek_org(kand, "deelname", rec)
            if not ref or ref[0] == "uitgesloten":
                if not ref:
                    self._mis("deelname", rec, "betaler niet in het model (tip)")
                    self.tips["deelname_onbekende_betaler"].append({"lid": rec["naam"], "citaat": rec["regel"]})
                continue
            osoort, ow = self._score_org(ref, rec["derde"])
            score = ow * 2.0
            self.kandidaten.append({"sleutel": rec["sleutel"], "score": round(score, 2), "soort": "deelname",
                                    "org_soort": osoort})
            self._plan(ref, lid, "geschenk", "geschenk_en_gastvrijheid", rec, self._claim(rec),
                       functie=f"Betaalde deelname aan een evenement{' (' + rec['plaats'] + ')' if rec.get('plaats') else ''}"[:200],
                       start=rec.get("van"), score=score, soort="deelname")

    # ── vergaderingen ──────────────────────────────────────────────────────
    def _cap(self, rec: dict) -> float:
        """Rapporteursgewicht van één vergadering: de hoedanigheid in de vergadering zelf, of het
        (schaduw)rapporteurschap voor dezelfde procedure uit de open data, wat het hoogst is."""
        w = CAP_GEWICHT.get(rec["hoedanigheid"], 0.0)
        k = en.procedure_sleutel(rec.get("procedure"))
        dci = self.dci.get(rec["persoon_id"], {}).get(k, 0.0) if k else 0.0
        if dci > w:
            self.tel["vergadering: rapporteursgewicht uit de open data"] += 1
        return max(w, dci)

    def vergaderingen(self):
        self.dci: dict[str, dict[str, float]] = defaultdict(dict)
        for r in self.pt["records"].values():
            if r["soort"] == "rapporteur" and r.get("procedure_sleutel"):
                d = self.dci[r["persoon_id"]]
                d[r["procedure_sleutel"]] = max(d.get(r["procedure_sleutel"], 0.0), r["gewicht"])
        paren: dict[tuple, list[dict]] = defaultdict(list)
        onbekend: dict[str, list[dict]] = defaultdict(list)
        self.n_vergaderingen = 0
        for rec in self.pt["records"].values():
            if rec["soort"] != "vergadering":
                continue
            self.n_vergaderingen += 1
            if rec["persoon_id"] not in self.ext_ep:
                self.lid_ontbreekt.add(rec["persoon_id"])
                continue
            kand = [rec["aanwezig"]] + list(rec.get("tr_namen") or [])
            gevonden = None
            for k in kand:
                k = self._schoon_naam(k)
                if len(sleutel(k)) >= 3:
                    gevonden = self._bestaand(k, ruim=True)
                    if gevonden:
                        break
            if gevonden and self._alleen_afkorting(gevonden[0], kand):
                self.tel["vergadering: alleen de afkorting (niet bevestigd)"] += 1
                self.tips["alleen_afkorting"].append({"model": self.org[gevonden[0]][0], "aanwezig": rec["aanwezig"],
                                                      "tr": rec.get("tr_namen"), "citaat": rec["regel"]})
                continue
            if not gevonden:
                tid = (rec.get("tr_ids") or [None])[0]
                onbekend[tid or f"naam:{sleutel(rec['aanwezig'])}"].append(rec)
                continue
            if self._uitgesloten_org(gevonden[0], "vergadering"):
                self.tel[f"vergadering: {self._uitgesloten_org(gevonden[0], 'vergadering')}"] += 1
                continue
            paren[(gevonden[0], rec["persoon_id"])].append(rec)
        # lift over alle vergaderingen met een bekende organisatie (zoals de agenda's)
        n_org, n_lid = Counter(), Counter()
        for (o, u), recs in paren.items():
            n_org[o] += len(recs)
            n_lid[u] += len(recs)
        totaal = sum(n_org.values()) or 1
        self.analyse = []
        for (o, u), recs in paren.items():
            dagen = len({r["datum"] for r in recs})
            lift = len(recs) * totaal / (n_org[o] * n_lid[u])
            cap = sum(self._cap(r) for r in recs) / len(recs)
            score = dagen * math.log2(max(lift, 1.0)) * (1 + cap)
            procs = Counter(r["procedure"] for r in recs if r.get("procedure"))
            a = {"org_id": o, "organisatie": self.org[o][0], "type": self.org[o][1], "lid_id": u,
                 "lid": recs[0]["naam"], "vergaderingen": len(recs), "dagen": dagen, "lift": round(lift, 2),
                 "rapporteur_aandeel": round(cap, 2), "score": round(score, 2),
                 "leden_gesproken": sum(1 for (o2, _u) in paren if o2 == o), "organisatie_totaal": n_org[o],
                 "procedures": [p for p, _ in procs.most_common(3)], "van": min(r["datum"] for r in recs),
                 "tot": max(r["datum"] for r in recs), "status": None}
            self.analyse.append(a)
            lid = ("bestaand", self.ext_ep[u])
            if dagen < MIN_DAGEN:
                a["status"] = "tip (één dag)"
                self.tel["vergadering: paar op één dag (tip)"] += 1
                continue
            ref = self._gekoppeld(recs[0], o, "vergadering", recs[0]["aanwezig"])
            nieuwste = sorted(recs, key=lambda r: r["datum"], reverse=True)
            ongeciteerd = nieuwste[:MAX_PER_VERBAND]
            n_extra = len(self.extra)
            mech = "denktank_naar_politiek" if self.org[o][1] == "denktank" else "lobbyist_naar_politicus"
            self._plan(ref, lid, "lobbyt", mech, ongeciteerd[0],
                       self._claim(ongeciteerd[0]), functie="Vergaderingen (Europees Parlement)",
                       start=a["van"], score=score, soort="vergadering", extra_recs=ongeciteerd[1:])
            a["status"] = "extra bron" if any(e.get("relation_id") for e in self.extra[n_extra:]) else "nieuw"
        self.analyse.sort(key=lambda a: (-a["score"], -a["dagen"]))
        # tips: organisaties die niet in het model staan, met land en categorie uit het register
        tr = self.pt["tr"]
        self.onbekend = []
        for k, recs in onbekend.items():
            o = tr.get(k) or {}
            dagen = len({r["datum"] for r in recs})
            leden = {r["persoon_id"] for r in recs}
            cap = sum(self._cap(r) for r in recs) / len(recs)
            self.onbekend.append({"organisatie": o.get("naam") or recs[0]["aanwezig"], "tr_id": k if o else None,
                                  "land": o.get("land"), "categorie": o.get("categorie"),
                                  "ep_passen": o.get("ep_passen"), "kosten_eur": o.get("kosten_eur"),
                                  "vergaderingen": len(recs), "dagen": dagen, "leden": len(leden),
                                  "rapporteur_aandeel": round(cap, 2),
                                  # zonder lift (geen noemer voor wie niet in het model staat): dagen per lid
                                  "score": round(dagen / max(1, len(leden)) * (1 + cap) * math.log2(1 + dagen), 2)})
        self.onbekend.sort(key=lambda x: -x["score"])

    def rapporteurs(self):
        """Geen verband (er is geen dossierknoop in de theorie): telling per lid en, als tip, de
        verklaringen waarin een lid zelf een belangenconflict meldt."""
        self.rapporteurschap = Counter()
        for rec in self.pt["records"].values():
            if rec["soort"] == "rapporteur":
                self.rapporteurschap[(rec["naam"], rec["hoedanigheid"])] += 1
                if rec.get("conflict"):
                    self.tips["belangenconflict_gemeld"].append({"lid": rec["naam"], "procedure": rec.get("procedure"),
                                                                 "citaat": rec["regel"]})

    # ── zelfcontrole: wat de registercheck zou afkeuren, niet plannen ──────
    def _zelfcontrole(self):
        def eindpunten(r):
            uit = []
            for ref in (r["bron"], r["doel"]):
                if ref[0] == "bestaand":
                    eid = ref[1]
                    ids = {(s, w) for s, w in self.conn.execute(
                        "SELECT stelsel, waarde FROM externe_ids WHERE entity_id = ?", (eid,))}
                    uit.append({"id": eid, "name": self._naam(ref), "type": None, "ids": ids})
                else:
                    uit.append({"id": None, "name": self._naam(ref), "type": None, "ids": set()})
            return uit

        def ok(r):
            rec = self.pt["records"][r["sleutel"]]
            reden = en.controleer(self.pt, r["sleutel"], rec, r["type"], eindpunten(r))
            if reden:
                self._mis(rec["soort"], rec, f"registercheck zou afkeuren: {reden}")
                if "mechanisme" in r:
                    self.tel[f"{r['type']}/{r['mechanisme']}"] -= 1
            return not reden
        self.relaties = [r for r in self.relaties if ok(r)]
        geplande = {(r["bron"], r["doel"], r["type"]) for r in self.relaties}
        self.extra = [e for e in self.extra if ok(e) and (e.get("relation_id") or (e["bron"], e["doel"], e["type"]) in geplande)]
        nodig = {ref[1] for r in self.relaties for ref in (r["bron"], r["doel"]) if ref[0] == "nieuw"}
        self.nieuwe_orgs = {k: v for k, v in self.nieuwe_orgs.items() if k in nodig}

    def maak(self):
        self.commissies()
        self.belangen()
        self.deelnames()
        self.vergaderingen()
        self.rapporteurs()
        self._zelfcontrole()
        return self.klem()


class Indiener(tkm.Indiener):
    """Zoals de Kamerregisters; drie bronnen (open data, verklaringen, vergaderingen) in één
    cluster register:ep_netwerk, en extra argumenten op bestaande of net aangemaakte verbanden."""

    def __init__(self, plan: Plan, rest, log=print):
        super().__init__(plan, rest, log, bron=en, cluster=CLUSTER)
        self.bron_ids: dict[str, int] = {}
        self.nieuw_rel: dict[tuple, int] = {}

    def bronnen(self):
        for soort, (titel, uitgever, url) in en.BRONNEN.items():
            status, res = self.rest("POST", "/api/sources", {
                "title": titel.format(uitgave=self.p.uitgave), "source_type": "dataset", "publisher": uitgever,
                "date_published": self.p.uitgave, "cluster_key": CLUSTER, "location": {"type": "url", "value": url},
                "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
            if status not in (200, 201):
                raise SystemExit(f"bron registreren faalde: {status} {res}")
            self.bron_ids[soort] = res["id"]

    def _citaat(self, sleutel_r: str, regel: str) -> dict:
        soort = en.SOORT_BRON[sleutel_r.split(":", 1)[0]]
        return {"source_id": self.bron_ids[soort], "quote": regel, "methode": "officieel_register_scrape",
                "section": sleutel_r, "page": f"{en.BRON}/{self.p.uitgave}",
                "context": en.BRONNEN[soort][2]}

    def relaties(self, _bron_id: int | None = None):
        for r in self.p.relaties:
            s, t = self._id(r["bron"]), self._id(r["doel"])
            if not s or not t:
                self.tel["relatie zonder eindpunt"] += 1
                continue
            if (s, t, r["type"]) in self.bestaande_relaties:
                self.tel["relatie bestond"] += 1
                continue
            body = {"source_id": s, "target_id": t, "relation_type": r["type"],
                    "mechanism_id": self.p.mech[r["mechanisme"]]}
            for veld, waarde in (("functie", r["functie"]), ("active_from", r["start"]), ("active_until", r["eind"])):
                if waarde:
                    body[veld] = waarde
            status, res = self.rest("POST", "/api/relations", body)
            if status != 201:
                self.tel[f"relatie fout {status}"] += 1
                self.log(f"  ✗ relatie {r['type']} {s}→{t}: {status} {res.get('error')}")
                continue
            self.bestaande_relaties.add((s, t, r["type"]))
            self.nieuw_rel[(r["bron"], r["doel"], r["type"])] = res["id"]
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": res["id"], "claim": r["claim"], "stance": "supporting",
                "citations": [self._citaat(r["sleutel"], r["regel"])]})
            self.tel["relatie nieuw" if status == 201 else f"argument fout {status}"] += 1

    def extra_bronnen(self):
        for e in self.p.extra:
            rid = e.get("relation_id") or self.nieuw_rel.get((e["bron"], e["doel"], e["type"]))
            if not rid:
                self.tel["extra argument zonder verband"] += 1
                continue
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": rid, "claim": e["claim"], "stance": "supporting",
                "citations": [self._citaat(e["sleutel"], e["regel"])]})
            self.tel["extra argument" if status == 201 else f"extra argument fout {status}"] += 1


# ── rapport ─────────────────────────────────────────────────────────────────
def _regel_top(plan: Plan, r: dict) -> dict:
    return {"score": r.get("score"), "soort": r.get("soort"), "type": r["type"], "mechanisme": r.get("mechanisme"),
            "bron": plan._naam(r["bron"]), "doel": plan._naam(r["doel"]),
            "nieuw_doel": r["doel"][0] == "nieuw" or r["bron"][0] == "nieuw",
            "start": r.get("start"), "eind": r.get("eind"), "sleutel": r["sleutel"], "citaat": r["regel"]}


def rapport(plan: Plan, top: int) -> dict:
    recs = plan.pt["records"].values()
    zonder_commissie = [r for r in plan.relaties if r.get("soort") != "commissie"]
    gepland = sorted(zonder_commissie, key=lambda r: -(r.get("score") or 0))
    extra_bestaand = [e for e in plan.extra if e.get("relation_id")]
    breed = sorted({a["org_id"]: a for a in plan.analyse}.values(), key=lambda a: -a["leden_gesproken"])[:15]
    return {
        "uitgave": plan.uitgave,
        "robots": {h: {"groep": r.get("groep"), "crawl_delay": r.get("crawl_delay"), "sha256": r.get("sha256")}
                   for h, r in (plan.pt.get("robots") or {}).items()},
        "tr_export": plan.pt.get("tr_export"),
        "records": dict(Counter(r["soort"] for r in recs)),
        "leden_zonder_ep_mep": sorted(plan.lid_ontbreekt),
        "vergaderingen": plan.n_vergaderingen,
        "vergaderingen_met_bekende_organisatie": sum(a["vergaderingen"] for a in plan.analyse),
        "paren_organisatie_lid": len(plan.analyse),
        "nieuwe_verbanden": dict(Counter(r.get("soort") for r in plan.relaties)),
        "extra_argumenten_op_nieuwe_verbanden": sum(1 for e in plan.extra if not e.get("relation_id")),
        "extra_bronnen_op_bestaande_verbanden": [
            {"relation_id": e["relation_id"], "type": e["bestaand_type"], "status": e["bestaand_status"],
             "bron": plan._naam(e["bron"]), "doel": plan._naam(e["doel"]), "citaat": e["regel"]} for e in extra_bestaand],
        "nieuwe_organisaties": sorted(f"{o['naam']} ({o['type']})" for o in plan.nieuwe_orgs.values()),
        "top": [_regel_top(plan, r) for r in gepland[:top]],
        "lobby_per_paar": plan.analyse[:50],
        "spreekt_iedereen": [{"organisatie": a["organisatie"], "leden": a["leden_gesproken"],
                              "vergaderingen": a["organisatie_totaal"]} for a in breed],
        "tips_organisaties_niet_in_model": plan.onbekend[:60],
        "tips_nederlandse_organisaties_niet_in_model": [o for o in plan.onbekend if o.get("land") == en.TR_LAND][:40],
        "tips_steun_van_derden": plan.tips["steun_van_derden"],
        "tips_deelname_onbekende_betaler": plan.tips["deelname_onbekende_betaler"],
        "tips_belang_bij_lobbyorganisatie": plan.tips["belang_bij_lobbyorganisatie"],
        "tips_alleen_afkorting": plan.tips["alleen_afkorting"][:30],
        "tips_belangenconflict_gemeld": plan.tips["belangenconflict_gemeld"],
        "rapporteurschappen": [{"lid": k[0], "hoedanigheid": k[1], "aantal": n}
                               for k, n in plan.rapporteurschap.most_common()],
        "overgeslagen_redenen": dict(Counter(f"{o['soort']}: {o['reden']}" for o in plan.overgeslagen).most_common()),
    }


def rapport_md(rap: dict) -> str:
    r = ["# EP-netwerk: verbanden van Nederlandse Europarlementariërs", "",
         f"Uitgave {rap['uitgave']} · EP open data, verklaringen en vergaderingen van leden · "
         f"transparantieregister {rap['tr_export']}", "",
         f"Vergaderingen: {rap['vergaderingen']} · met een organisatie in het model: "
         f"{rap['vergaderingen_met_bekende_organisatie']} · paren organisatie–lid: {rap['paren_organisatie_lid']}", "",
         f"Nieuwe verbanden: {rap['nieuwe_verbanden']} · extra bronnen op bestaande verbanden: "
         f"{len(rap['extra_bronnen_op_bestaande_verbanden'])} · extra argumenten op nieuwe verbanden: "
         f"{rap['extra_argumenten_op_nieuwe_verbanden']}", "",
         "## Top (zonder commissiezetels)", "",
         "| # | score | soort | van | naar | type | citaat |", "|---|---|---|---|---|---|---|"]
    for i, t in enumerate(rap["top"], 1):
        r.append(f"| {i} | {t['score']} | {t['soort']} | {t['bron']} | {t['doel']}{' (nieuw)' if t['nieuw_doel'] else ''} | "
                 f"{t['type']}/{t['mechanisme']} | {t['citaat'][:160]} |")
    r += ["", "## Lobby per paar (score = dagen × log2(lift) × (1 + aandeel als rapporteur))", "",
          "| organisatie | lid | dagen | lift | rapp. | score | status |", "|---|---|---|---|---|---|---|"]
    for a in rap["lobby_per_paar"][:30]:
        r.append(f"| {a['organisatie']} | {a['lid']} | {a['dagen']} | {a['lift']} | {a['rapporteur_aandeel']} | "
                 f"{a['score']} | {a['status']} |")
    r += ["", "## Spreekt (bijna) iedereen — lage lift", ""]
    r += [f"- {a['organisatie']}: {a['vergaderingen']} vergaderingen met {a['leden']} leden" for a in rap["spreekt_iedereen"]]
    r += ["", "## Tips: Nederlandse organisaties (transparantieregister) die niet in het model staan", "",
          "| organisatie | categorie | dagen | leden | rapp. | EP-passen | kosten | score |", "|---|---|---|---|---|---|---|---|"]
    for o in rap["tips_nederlandse_organisaties_niet_in_model"][:30]:
        r.append(f"| {o['organisatie']} | {o['categorie']} | {o['dagen']} | {o['leden']} | {o['rapporteur_aandeel']} | "
                 f"{o['ep_passen']} | {o['kosten_eur']} | {o['score']} |")
    return "\n".join(r) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave")
    ap.add_argument("--top", type=int, default=TOP)
    ap.add_argument("--haal", action="store_true", help="eerst een nieuwe uitgave ophalen (± 10 minuten)")
    ap.add_argument("--indienen", action="store_true")
    a = ap.parse_args()
    if a.haal and not a.uitgave:
        en.haal()
    uitgave = a.uitgave or en.uitgaven()[-1].stem.rsplit("_", 1)[1]
    data = en.lees_uitgave(uitgave)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(data, conn, koppelingen).maak()
    rap = rapport(plan, a.top)
    samenvatting = {"uitgave": plan.uitgave, "nieuwe_organisaties": len(plan.nieuwe_orgs),
                    "nieuwe_verbanden": len(plan.relaties), "per_soort": rap["nieuwe_verbanden"],
                    "extra_bronnen_bestaand": len(rap["extra_bronnen_op_bestaande_verbanden"]),
                    "extra_argumenten_nieuw": rap["extra_argumenten_op_nieuwe_verbanden"],
                    "telling": {k: v for k, v in sorted(plan.tel.items()) if v}}
    print(json.dumps(samenvatting, ensure_ascii=False, indent=1))
    (en.MAP / f"rapport_{plan.uitgave}.json").write_text(
        json.dumps({"samenvatting": samenvatting, **rap}, ensure_ascii=False, indent=1), encoding="utf-8")
    (en.MAP / f"rapport_{plan.uitgave}.md").write_text(rapport_md(rap), encoding="utf-8")
    for naam, inhoud in (("overgeslagen", plan.overgeslagen), ("koppelingen", plan.koppelingen)):
        (en.MAP / f"{naam}_{plan.uitgave}.json").write_text(
            json.dumps(inhoud, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nTop {a.top} (zonder commissiezetels):")
    for i, t in enumerate(rap["top"], 1):
        print(f"{i:>3}. {t['score']:>6}  {t['bron']} → {t['doel']}{' (nieuw)' if t['nieuw_doel'] else ''}"
              f"  [{t['type']}/{t['mechanisme']}]\n        “{t['citaat'][:220]}”")
    if not a.indienen:
        print(f"\n(droogloop — niets ingediend; rapport in {en.MAP}/rapport_{plan.uitgave}.md)")
        return
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()))
    ind.bronnen()
    ind.entiteiten()
    ind.relaties()
    ind.extra_bronnen()
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
