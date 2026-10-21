#!/usr/bin/env python3
"""Staatscourant-benoemingen → het model (eigen idee hoofdsessie 2026-10-20).

staatscourant.py bewaart de benoemingsbesluiten (koninklijke en ministeriële besluiten) met per
benoeming, herbenoeming of ontslag een record: persoon, functie, organisatie, begin, einde, wie
benoemde, en als citaat de letterlijke besluittekst (zonder woonplaats). Dit script kiest daaruit
wat ertoe doet en plant, zonder AI:

  - een (her)benoeming van een persoon die al in het model staat bij een organisatie die al in het
    model staat (of in het register van overheidsorganisaties) → persoon → organisatie. Mechanisme
    zoals de bestaande verbanden van die soort: `ambtelijke_leiding` (ambt bij een zbo, toezichthouder
    of college, of een leidende functie), `commissarisbenoeming` (raad van toezicht van een stichting,
    zoals bij de NPO), anders `kroonbenoeming` (gewoon lid van een adviescollege). Relatietype: `ambt` bij een overheidsorganisatie (zbo, adviescollege,
    toezichthouder), `bestuurder` bij een raad van toezicht of bestuur van een stichting of bedrijf
    (NPO, NTR, NLFI), `adviseur` bij een raad van advies, anders `lidmaatschap`;
  - een nieuwe persoon alleen bij een zware categorie (media, toezichthouder, Hoog College,
    staatsdeelneming, staatscommissie, adviescollege), een leidende functie of zetel, boven de
    interessedrempel (DREMPEL_NIEUW);
  - bestaat het verband al (zelfde paar, type ambt/bestuurder/adviseur/lidmaatschap), dan krijgt het
    alleen een extra argument met de recordregel als citaat (ook een ontslagbesluit bevestigt de
    functie); bij bewindspersonen alleen dat (hun ambt komt uit het register van
    overheidsorganisaties);
  - alleen besluiten van de Kroon of een bewindspersoon (of namens hem); een benoeming door een
    raad van bestuur, een college van procureurs-generaal of de griffier valt niet onder
    `kroonbenoeming` en wordt alleen gemeld.
Routine (tucht-, klacht-, bezwaar-, examen- en geschillencommissies, toetsingscommissies
euthanasie, grondkamers, commissies van toezicht, auditcommissies, secretarissen) wordt geteld maar
niet gepland. Kamerleden (centraal stembureau) staan niet in de uitgave: die komen uit tk.py/ep.py.

Koppelen (README § Regels): een persoon via de volledige naam (roepnaam uit het besluit +
achternaam) bij precies één persoon met een passende rol, of via voorletters + achternaam bij
precies één passende kandidaat die de organisatie of de functie al noemt (beschrijving of een
verband); anders een nieuwe knoop (met voorletters: '<voorletters> <naam> (<functie> <organisatie>)').
Een organisatie via haar oo-id (het record legt het vast als de naam exact in het register van
overheidsorganisaties staat), de vastgelegde schrijfwijze (staatscourant.SCHRIJFWIJZEN) of haar exacte
naam in het model (ook zonder 'Stichting').

Interessant versus ruis (`score`): categorie × functie × soort (herbenoeming 0,6) × politieke
achtergrond in het model (×2: partijlid, (oud-)Kamerlid, bewindspersoon, lokaal bestuurder, een
draaideur_politiek-verband) × in het model (×1,5) × concentratie (dezelfde persoon in meer colleges)
× lopend. Het rapport (data/registers/staatscourant/rapport_<uitgave>.json en analyse.md) geeft de
aantallen, de top, de draaideur-kandidaten (politiek → toezicht/advies/media), de concentratie en
wat interessant is maar niet te plaatsen.

Gebruik:
    python3 tools/registers/staatscourant_naar_model.py                 # droogloop + rapport
    python3 tools/registers/staatscourant_naar_model.py --top 50
    python3 tools/registers/staatscourant_naar_model.py --haal [--indienen]
    (--indienen vergt eerst 'staatscourant' in scripts/registercheck.py BRONNEN)
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import staatscourant as sc  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import noemt, ontleed_naam, schoon, sleutel  # noqa: E402
from naar_model import PASSENDE_ROLLEN, TOKEN, Rest  # noqa: E402

DB_PATH = tkm.ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:staatscourant"
MECH = "kroonbenoeming"
# Precedent in het model (de 68 bestaande verbanden die de Staatscourant bevestigt): een ambt bij een
# zbo, toezichthouder of college draagt `ambtelijke_leiding`, een zetel in de raad van toezicht van een
# stichting (NPO) `commissarisbenoeming`. Een nieuw verband volgt dat, anders telt ontdubbelen
# (stap 8b) het als een ander feit naast een later registerverband. Alleen een gewoon lid van een
# adviescollege of commissie krijgt `kroonbenoeming` (de Kroon of de minister benoemt 'leden van
# adviescolleges').
LEIDING_MECH, TOEZICHT_MECH = "ambtelijke_leiding", "commissarisbenoeming"
BESTUURSCOLLEGE = {"toezichthouder", "zbo", "hoog_college", "media", "staatsdeelneming"}
PERSOONSROLLEN = PASSENDE_ROLLEN | {"bestuursrechter", "hoofdredacteur", "columnist_opiniemaker", "journalist",
                                    "mediaeigenaar", "gezagsexpert"}
AFFILIATIE = sc.RELATIETYPES
DREMPEL_NIEUW = 4.0
MAX_ARG = 5
ZWAAR = {"media", "toezichthouder", "hoog_college", "staatsdeelneming", "staatscommissie", "adviescollege"}
VANDAAG = datetime.date.today().isoformat()
# Registersoorten die het register van overheidsorganisaties wel kent maar naar_model.py niet als
# knoop opneemt (geen 'top'): alleen als een zwaar of politiek verband ze nodig heeft, met hun oo-id.
EXTRA_OO = {"Externe commissie": ("overheidsinstelling", "adviesorgaan"),
            "Adviescollege": ("overheidsinstelling", "adviesorgaan"),
            "Zelfstandig bestuursorgaan": ("overheidsinstelling", "uitvoeringsorganisatie"),
            "Overheidsstichting of -vereniging": ("stichting", "uitvoeringsorganisatie"),
            "Organisatie met overheidsbemoeienis": ("stichting", "uitvoeringsorganisatie")}

# ── categorie van de organisatie → gewicht ──────────────────────────────────
# Volgorde telt: de eerste die past, wint (op de naam uit het besluit en die in het model).
CATEGORIEEN = [
    ("ruis", 0.3, r"tucht|klacht|bezwa(?:a)?r|examen|geschil|toetsingscommissie euthanasie|grondkamer|"
                  r"beroepscollege|tolken|vertalers|zuivelnotering|peer review|begeleidingscommissie|monitoringcomit|"
                  r"deskundigencommissie|panel|commissie van toezicht|commissie van beroep|klachtadvies|"
                  r"stembureau|audit committee|auditcommissie|voorselectiecommissie|benoemingsadviescommissie|"
                  r"benoemingenadviescommissie|commissie gewetensbezwaren|integriteitskamer|"
                  r"(?:commissie|college) (?:voor|tot|ter) (?:de )?(?:benoeming|werving|selectie)|\bbac\b"),
    ("media", 3.0, r"publieke omroep|\bnpo\b|\bntr\b|omroep|commissariaat voor de media|journalistiek|mediafonds|"
                   r"beeld en geluid|\bnos\b|letterenfonds|filmfonds"),
    ("hoog_college", 3.0, r"raad van state|algemene rekenkamer|nationale ombudsman"),
    ("toezichthouder", 3.0, r"\bautoriteit\b|nederlandsche bank|\bdnb\b|\bafm\b|\bacm\b|zorgautoriteit|kansspelautoriteit|"
                            r"commissariaat|kiesraad|college voor de rechten van de mens|dopingautoriteit|"
                            r"college ter beoordeling van geneesmiddelen|college sanering"),
    ("staatsdeelneming", 3.0, r"beheer financi[eë]le instellingen|\bnlfi\b|invest-nl|pallas|staatsdeelneming|"
                              r"\bfmo\b|\bbng\b|gasunie|tennet|schiphol|holland casino|volksbank"),
    ("staatscommissie", 2.5, r"staatscommissie"),
    ("adviescollege", 2.0, r"^raad voor\b|^adviesraad|gezondheidsraad|onderwijsraad|wetenschappelijke raad|klimaatraad|"
                           r"^adviescollege|sociaal-economische raad|\bwrr\b|sportraad|cultuur|wetenschap|"
                           r"raad voor het openbaar bestuur|politieonderwijsraad|commissie van advies|nationaal groeifonds"),
]
OO_CATEGORIE = {"Adviescollege": ("adviescollege", 2.0), "Hoog College van Staat": ("hoog_college", 3.0),
                "Zelfstandig bestuursorgaan": ("zbo", 1.5), "Externe commissie": ("commissie", 1.0)}
MODEL_CATEGORIE = {"toezichthouder": ("toezichthouder", 3.0), "omroep": ("media", 3.0),
                   "mediaorganisatie": ("media", 3.0), "persbureau": ("media", 3.0),
                   "bedrijf": ("staatsdeelneming", 2.5), "denktank": ("adviescollege", 2.0)}


def functie_gewicht(functie: str) -> tuple[str, float]:
    f = sleutel(functie)
    if re.search(r"\b(?:minister|staatssecretaris)\b", f):
        return "bewindspersoon", 1.0
    if re.search(r"\b(?:secretaris|griffier|penningmeester)\b", f) and not re.search(r"directeur|voorzitter|\blid\b", f):
        return "secretaris", 0.3
    if re.search(r"plaatsvervang|buitengewoon|\bextern|reserve|toegevoegd|\bplv\b", f):
        return "plaatsvervangend", 0.6
    if re.search(r"vicevoorzitter|vice voorzitter|ondervoorzitter|vicepresident", f):
        return "vicevoorzitter", 1.3
    if re.search(r"\bvoorzitter\b|\bpresident\b", f):
        return "voorzitter", 1.5
    if re.search(r"directeur|bestuurder|raad van bestuur|bestuurslid|collegelid|gouverneur|commissaris", f):
        return "bestuur", 1.4
    if re.search(r"raad van toezicht|raad van commissarissen|toezicht", f):
        return "toezicht", 1.3
    return "lid", 1.0


class Plan(tkm.Plan):
    def __init__(self, records: dict[str, dict], conn: sqlite3.Connection, koppelingen: dict | None = None):
        super().__init__({"uitgave": max(r["_uitgave"] for r in records.values()), "personen": {}, "records": {}},
                         conn, koppelingen)
        self.records = records
        self.mech.update(self._ids("mechanisms", (MECH, LEIDING_MECH, TOEZICHT_MECH)))
        self.rol.update({n: i for n, i in conn.execute(
            "SELECT name, id FROM roles WHERE NOT vervangen AND name IN ('topambtenaar', 'gezagsexpert', 'toezichthouder')")})
        self.ext_oo = {w: e for e, w in conn.execute("SELECT entity_id, waarde FROM externe_ids WHERE stelsel = 'oo'")
                       if e in self.org}   # niet vervangen of afgewezen
        self.oo_neg = {o["oo_id"]: eid for eid, o in self.oo_orgs.items()}
        self.oo_types, self.oo_alle = {}, {}
        idx = sc.oo_index()
        if idx.get("_uitgave"):
            import oo
            self.oo_alle = oo.lees_uitgave(idx["_uitgave"])["organisaties"]
            self.oo_types = {o["oo_id"]: o["types"] for o in self.oo_alle.values()}
        self.oo_extra: set[int] = set()
        self.rollen_alle = {n: i for n, i in conn.execute("SELECT name, id FROM roles WHERE NOT vervangen")}
        self.hand_personen = {k: v for k, v in (koppelingen or {}).get("staatscourant_personen", {}).items()
                              if not k.startswith("_")}
        # personen in het model per achternaam (voor voorletters + achternaam)
        self.op_achternaam: dict[str, list[dict]] = defaultdict(list)
        for i, naam, rol, beschr in conn.execute("""
                SELECT e.id, e.name, r.name, COALESCE(e.description, '') FROM entities e
                LEFT JOIN roles r ON r.id = e.primary_role_id
                WHERE e.type = 'persoon' AND NOT e.vervangen AND e.status <> 'afgewezen'"""):
            n = ontleed_naam(tkm.zonder_haakjes(naam).split(",")[0])
            achter = sleutel(f"{n['tussenvoegsel'] or ''} {n['achternaam'] or ''}")
            c = {"id": i, "naam": naam, "rol": rol, "beschrijving": beschr,
                 "letters": re.sub(r"[^a-z]", "", (n["voorletters"] or "").lower()),
                 "voornaam": sleutel(n["roepnaam"] or n["voornamen"] or "")}
            for k in self._achternamen(f"{n['tussenvoegsel'] or ''} {n['achternaam'] or ''}"):
                self.op_achternaam[k].append(c)
        # bestaande verbanden per ongeordend paar (voor 'extra bron'), en wat al geciteerd is
        self.bestaande_paren: dict[tuple[int, int], list[tuple[int, str]]] = defaultdict(list)
        self.doelen: dict[int, set[str]] = defaultdict(set)
        for rid, s, t, typ, tnaam, snaam in conn.execute("""
                SELECT r.id, r.source_id, r.target_id, r.relation_type, et.name, es.name FROM relations r
                JOIN entities et ON et.id = r.target_id JOIN entities es ON es.id = r.source_id
                WHERE NOT r.vervangen AND r.status <> 'afgewezen'"""):
            self.bestaande_paren[(min(s, t), max(s, t))].append((rid, typ))
            self.doelen[s].add(tnaam)
            self.doelen[t].add(snaam)
        self.al_geciteerd = {(r, sec) for r, sec in conn.execute("""
            SELECT a.relation_id, c.section FROM citations c JOIN arguments a ON a.id = c.argument_id
            WHERE c.page LIKE 'staatscourant/%' AND a.relation_id IS NOT NULL""")}
        self.personen_sc: dict[str, dict] = {}
        self.groepen: dict[tuple, dict] = {}
        self.extra_bron: list[dict] = []
        self.kandidaten: list[dict] = []
        self._pol: dict[int, list[dict]] = {}
        self.concentratie = self._concentratie()

    # ── personen ───────────────────────────────────────────────────────────
    @staticmethod
    def persoonsleutel(rec: dict) -> str:
        letters = re.sub(r"[^a-z]", "", (rec.get("voorletters") or "").lower())
        return f"{sleutel(rec['achternaam'])}|{letters or sleutel(rec.get('roepnaam') or rec.get('voornamen') or '')}"

    def _concentratie(self) -> dict[str, set[str]]:
        uit: dict[str, set[str]] = defaultdict(set)
        for r in self.records.values():
            if r["soort"] in ("benoeming", "herbenoeming") and r["organisatie"]:
                uit[self.persoonsleutel(r)].add(r.get("oo_naam") or sc.SCHRIJFWIJZEN.get(sleutel(r["organisatie"]))
                                                or r["organisatie"])
        return uit

    @staticmethod
    def _achternamen(achternaam: str) -> set[str]:
        """De achternaam, en bij een dubbele naam ook het eerste deel ('Engwirda-Kromwijk' → 'engwirda')."""
        uit = {sleutel(achternaam)}
        if "-" in achternaam:
            uit.add(sleutel(achternaam.split("-")[0]))
        return {u for u in uit if u}

    def _kandidaten(self, rec: dict) -> list[dict]:
        """Personen in het model (elke rol) met dezelfde achternaam en een passende eerste voorletter."""
        kand = list({c["id"]: c for k in self._achternamen(rec["achternaam"] or "")
                     for c in self.op_achternaam.get(k, [])}.values())
        voornaam = sleutel(rec.get("roepnaam") or rec.get("voornamen") or "")
        letters = re.sub(r"[^a-z]", "", (rec.get("voorletters") or "").lower()) or voornaam[:1]
        if not letters:
            return []
        return [c for c in kand if (voornaam and c["voornaam"] == voornaam)   # 'C.M. (Mirjam) van Praag'
                or (c["letters"] and (c["letters"].startswith(letters) or letters.startswith(c["letters"])))
                or (not c["letters"] and c["voornaam"][:1] == letters[:1])]

    def _bestaande_persoon(self, rec: dict, org_ref: tuple | None) -> tuple[int | None, str]:
        pk = self.persoonsleutel(rec)
        if pk in self.hand_personen:
            return self.hand_personen[pk], "koppelingen.json"
        passend = self._kandidaten(rec)
        voornaam = sleutel(rec.get("roepnaam") or rec.get("voornamen") or "")
        if voornaam:
            exact = [c for c in passend if c["voornaam"] == voornaam and c["rol"] in PERSOONSROLLEN]
            if len(exact) == 1:
                return exact[0]["id"], "volledige naam + passende rol"
        if len(passend) != 1:
            return None, ""
        c = passend[0]
        org_namen = [rec["organisatie"]] + ([rec["oo_naam"]] if rec.get("oo_naam") else []) + \
                    ([self.org[org_ref[1]][0]] if org_ref else [])
        tekst = " ".join([c["beschrijving"]] + sorted(self.doelen.get(c["id"], ())))
        if any(n and (noemt(tekst, n) or sleutel(n) in {sleutel(d) for d in self.doelen.get(c["id"], ())})
               for n in org_namen):
            return c["id"], "voorletters + achternaam, de organisatie al genoemd"
        return None, ""

    def politiek(self, eid: int | None) -> list[dict]:
        """Politieke achtergrond zoals het model haar al kent (verbanden, geen beschrijvingen)."""
        if not eid:
            return []
        if eid in self._pol:
            return self._pol[eid]
        uit = []
        for rid, partij, van, tot, mech in self.conn.execute("""
                SELECT r.id, s.name, r.active_from, r.active_until, m.name FROM relations r
                JOIN entities s ON s.id = r.source_id LEFT JOIN mechanisms m ON m.id = r.mechanism_id
                WHERE r.target_id = ? AND s.type = 'partij' AND r.relation_type = 'lidmaatschap'
                  AND NOT r.vervangen AND r.status <> 'afgewezen'""", (eid,)):
            uit.append({"wat": f"lid {partij}", "relatie": rid, "van": van, "tot": tot})
        for rid, doel, functie, van, tot, mech in self.conn.execute("""
                SELECT r.id, t.name, r.functie, r.active_from, r.active_until, m.name FROM relations r
                JOIN entities t ON t.id = r.target_id LEFT JOIN mechanisms m ON m.id = r.mechanism_id
                WHERE r.source_id = ? AND NOT r.vervangen AND r.status <> 'afgewezen'
                  AND (m.name IN ('kamerzetel', 'ministeriele_verantwoordelijkheid', 'lokaal_bestuursmandaat')
                       OR m.name LIKE 'draaideur_politiek%')""", (eid,)):
            if mech == "kamerzetel" and "(Tweede Kamer)" in doel:
                continue   # commissiezetel: het Kamerlidmaatschap zelf telt al
            wat = {"kamerzetel": f"zetel {doel}", "ministeriele_verantwoordelijkheid": functie or f"bewindspersoon {doel}",
                   "lokaal_bestuursmandaat": f"{functie or 'bestuurder'} {doel}"}.get(mech, f"{mech}: {doel}")
            uit.append({"wat": wat, "relatie": rid, "van": van, "tot": tot})
        rol = self.conn.execute("SELECT r.name FROM entities e JOIN roles r ON r.id = e.primary_role_id WHERE e.id = ?",
                                (eid,)).fetchone()
        if not uit and rol and rol[0] in ("politicus", "bewindspersoon", "lokale_bestuurder"):
            uit.append({"wat": f"rol {rol[0]}", "relatie": None, "van": None, "tot": None})
        self._pol[eid] = uit
        return uit

    # ── organisaties ───────────────────────────────────────────────────────
    def _org(self, rec: dict) -> tuple | None:
        if rec.get("oo_id"):
            if rec["oo_id"] in self.ext_oo:
                return ("bestaand", self.ext_oo[rec["oo_id"]])
            if rec["oo_id"] in self.oo_neg:
                return ("oo", self.oo_neg[rec["oo_id"]])
        org = rec["organisatie"]
        if not org:
            return None
        kandidaten = []
        for v in sc.org_varianten(org):
            if sleutel(v) in sc.SCHRIJFWIJZEN:
                kandidaten.append(sc.SCHRIJFWIJZEN[sleutel(v)])
            kandidaten.append(v)
        for k in dict.fromkeys(kandidaten):
            g = self._bestaand(k, ruim=False)
            if g and not self._toegestaan(g[0], "staatscourant"):
                return ("bestaand", g[0]) if g[0] > 0 else ("oo", g[0])
        return self._oo_extra(rec.get("oo_id"))

    def _oo_extra(self, oo_id: str | None) -> tuple | None:
        """Een organisatie uit het register die naar_model.py niet opneemt (externe commissie,
        overheidsstichting …): dezelfde vorm als tk_naar_model's registerorganisaties, met oo-id."""
        o = self.oo_alle.get(oo_id) if oo_id else None
        if not o or o.get("eind") or not o.get("types") or o["types"][0] not in EXTRA_OO:
            return None
        if oo_id in self.oo_neg:
            return ("oo", self.oo_neg[oo_id])
        g = self._bestaand(o["naam"], ruim=False)
        if g:
            return ("bestaand", g[0]) if g[0] > 0 else ("oo", g[0])
        typ, rol = EXTRA_OO[o["types"][0]]
        if rol not in self.rollen_alle:
            return None
        eid = -(len(self.oo_orgs) + 1)
        self.oo_orgs[eid] = {"naam": o["naam"], "type": typ, "rol_id": self.rollen_alle[rol],
                             "bestuurslaag": o.get("bestuurslaag") or "rijk", "oo_type": o["types"][0],
                             "oo_id": oo_id, "tooi": o.get("tooi"), "start": o.get("start"),
                             "beschrijving": o.get("beschrijving") or f"{o['types'][0]} (register van overheidsorganisaties)"}
        self.org[eid] = (o["naam"], typ, o.get("bestuurslaag") or "rijk")
        self.oo_neg[oo_id] = eid
        self.oo_extra.add(eid)
        return ("oo", eid)

    def categorie(self, rec: dict, org_ref: tuple | None) -> tuple[str, float]:
        if functie_gewicht(rec["functie"])[0] == "bewindspersoon":
            return "bewindspersoon", 1.0
        namen = " | ".join(n for n in (rec["organisatie"], rec.get("oo_naam"),
                                       self.org[org_ref[1]][0] if org_ref else None) if n)
        s = sleutel(namen)
        for naam, gewicht, patroon in CATEGORIEEN:
            if any(re.search(patroon, sleutel(deel)) for deel in namen.split(" | ")) or re.search(patroon, s):
                return naam, gewicht
        for t in self.oo_types.get(rec.get("oo_id"), []):
            if t in OO_CATEGORIE:
                return OO_CATEGORIE[t]
        if org_ref and self.org[org_ref[1]][1] in MODEL_CATEGORIE:
            return MODEL_CATEGORIE[self.org[org_ref[1]][1]]
        return "overig", 1.0

    def _rtype(self, rec: dict, org_ref: tuple) -> str:
        f = sleutel(rec["functie"])
        if "raad van advies" in f or re.search(r"\badviseur\b", f):
            return "adviseur"
        typ = "overheidsinstelling" if org_ref[0] == "oo" else self.org[org_ref[1]][1]
        if typ in ("overheidsinstelling", "toezichthouder", "rechterlijke_macht"):
            return "ambt"
        if re.search(r"voorzitter|raad van toezicht|raad van bestuur|bestuur|directeur|commissaris|toezicht|president", f):
            return "bestuurder"
        return "lidmaatschap"

    # ── score ──────────────────────────────────────────────────────────────
    def score(self, rec: dict, org_ref: tuple | None, eid: int | None) -> dict:
        cat, cw = self.categorie(rec, org_ref)
        fsoort, fw = functie_gewicht(rec["functie"])
        sw = {"benoeming": 1.0, "herbenoeming": 0.6, "ontslag": 0.3}[rec["soort"]]
        pol = self.politiek(eid)
        pw = 2.0 if pol else 1.0
        mw = 1.5 if eid else 1.0
        n = len(self.concentratie.get(self.persoonsleutel(rec), ()))
        kw = min(2.5, 1 + 0.5 * max(0, n - 1))
        lw = 0.7 if rec.get("tot") and rec["tot"] < VANDAAG else 1.0
        return {"score": round(cw * fw * sw * pw * mw * kw * lw, 3), "categorie": cat, "functiesoort": fsoort,
                "politiek": [p["wat"] for p in pol], "colleges": n}

    # ── plannen ────────────────────────────────────────────────────────────
    @staticmethod
    def _door_kroon_of_minister(rec: dict) -> bool:
        return rec["kb"] or bool(re.search(r"\b(?:minister|staatssecretaris|secretaris-generaal|directeur-generaal)\b",
                                           rec["benoemer"] or "", re.I))

    def _persoon_ref(self, rec: dict, eid: int | None, sc_: dict, org_ref: tuple) -> tuple:
        pk = self.persoonsleutel(rec)
        if pk not in self.personen_sc:
            if eid:
                naam = self.conn.execute("SELECT name FROM entities WHERE id = ?", (eid,)).fetchone()[0]
            elif rec.get("roepnaam") or rec.get("voornamen"):
                naam = schoon(f"{rec.get('roepnaam') or rec.get('voornamen')} {rec['achternaam']}")
            else:
                naam = schoon(f"{rec['voorletters'] or ''} {rec['achternaam']}")
                naam = f"{naam} ({rec['functie'].split(' en ')[0]} {self.org[org_ref[1]][0]})"
            if not eid and sleutel(naam) in self.alle_namen:
                naam = f"{naam} ({rec['functie'].split(' en ')[0]} {self.org[org_ref[1]][0]})"
            rol = ("toezichthouder" if re.search(r"toezicht|commissaris", sleutel(rec["functie"]))
                   else "gezagsexpert" if sc_["categorie"] in ("adviescollege", "staatscommissie")
                   else "topambtenaar")
            self.personen_sc[pk] = {"sleutel": pk, "naam": naam, "bestaand": eid, "rol": rol,
                                    "beschrijving": f"{rec['functie'][:1].upper()}{rec['functie'][1:]} van "
                                                    f"{self.org[org_ref[1]][0]} (Staatscourant {rec['publicatie'][6:]})."}
        return ("persoon", pk)

    def maak(self):
        for rec in sorted(self.records.values(), key=lambda r: (r.get("publicatiedatum") or "", r["sleutel"])):
            self.tel[f"record: {rec['soort']}"] += 1
            org_ref = self._org(rec)
            eid, hoe = self._bestaande_persoon(rec, org_ref)
            sc_ = self.score(rec, org_ref, eid)
            kand = {**sc_, "sleutel": rec["sleutel"], "regel": rec["regel"], "persoon": rec["persoon"],
                    "persoon_id": eid, "koppeling": hoe, "functie": rec["functie"], "organisatie": rec["organisatie"],
                    "org_id": org_ref[1] if org_ref and org_ref[0] == "bestaand" else None,
                    "soort": rec["soort"], "van": rec.get("van"), "tot": rec.get("tot"), "status": None,
                    "_uitgave": rec["_uitgave"]}
            self.kandidaten.append(kand)
            self.tel[f"categorie: {sc_['categorie']}"] += 1
            if eid:
                self.tel["persoon in het model"] += 1

            def mis(reden):
                kand["status"] = reden
                self.tel[f"niet gepland: {reden}"] += 1
            if not rec["organisatie"]:
                mis("geen organisatie")
                continue
            if sc_["categorie"] == "ruis":
                mis("routinecommissie (ruis)")
                continue
            if not self._door_kroon_of_minister(rec):
                mis("benoemer is geen Kroon of bewindspersoon")
                continue
            if not org_ref:
                mis("organisatie niet in het model of het register")
                continue
            if sc_["functiesoort"] == "secretaris":
                mis("secretaris of griffier (ambtelijke ondersteuning)")
                continue
            if org_ref[1] in self.oo_extra and sc_["categorie"] not in ZWAAR and not sc_["politiek"]:
                mis("registerorganisatie buiten de kern (externe commissie e.d.), niet zwaar of politiek")
                continue
            rtype = self._rtype(rec, org_ref)
            bestaand = []
            if eid and org_ref[0] == "bestaand":
                bestaand = [x for x in self.bestaande_paren.get((min(eid, org_ref[1]), max(eid, org_ref[1])), [])
                            if x[1] in AFFILIATIE]
            if bestaand:
                rid, typ = sorted(bestaand, key=lambda x: (x[1] != rtype, x[0]))[0]
                if (rid, rec["sleutel"]) in self.al_geciteerd:
                    mis("verband bestaat, record al geciteerd")
                    continue
                self.extra_bron.append({"relation_id": rid, "bestaand_type": typ, "rec": rec, "score": sc_["score"],
                                        "persoon_id": eid, "org_id": org_ref[1], "claim": self._claim(rec)})
                kand["status"] = "extra bron"
                self.tel["extra bron"] += 1
                continue
            if sc_["categorie"] == "bewindspersoon":
                mis("bewindspersoon zonder bestaand ambt (komt uit het register van overheidsorganisaties)")
                continue
            if rec["soort"] == "ontslag":
                mis("ontslag zonder bestaand verband")
                continue
            if not eid and (sc_["categorie"] not in ZWAAR or sc_["score"] < DREMPEL_NIEUW
                            or sc_["functiesoort"] == "plaatsvervangend"):
                mis("nieuwe persoon onder de drempel")
                continue
            if not eid and self._kandidaten(rec):
                mis("mogelijke naamgenoot in het model (niet te bevestigen; koppelingen.json)")
                continue
            persoon = self._persoon_ref(rec, eid, sc_, org_ref)
            g = self.groepen.setdefault((persoon, org_ref, rtype), {
                "bron": persoon, "doel": org_ref, "type": rtype, "mechanisme": MECH, "records": [], "score": 0.0,
                "categorie": sc_["categorie"], "politiek": sc_["politiek"]})
            g["records"].append(rec)
            g["score"] = max(g["score"], sc_["score"])
            kand["status"] = "nieuw verband"
        # ontslag dat bij een gepland nieuw verband hoort: het einde, en een argument
        for rec in self.records.values():
            if rec["soort"] != "ontslag":
                continue
            for (persoon, org_ref, _t), g in self.groepen.items():
                if persoon[1] == self.persoonsleutel(rec) and self._org(rec) == org_ref and rec not in g["records"]:
                    g["records"].append(rec)
        self._relaties()
        self._zelfcontrole()
        return self.klem()

    def _relaties(self):
        self.relaties = []
        for g in self.groepen.values():
            recs = sorted(g["records"], key=lambda r: (r.get("van") or r.get("publicatiedatum") or ""))
            benoemd = [r for r in recs if r["soort"] == "benoeming" and r.get("van")]
            start = benoemd[0]["van"] if benoemd else None   # een herbenoeming zegt niet wanneer het begon
            ontslag = [r for r in recs if r["soort"] == "ontslag" and r.get("van") and (not start or r["van"] >= start)]
            tots = [r["tot"] for r in recs if r["soort"] != "ontslag" and r.get("tot")]
            eind = ontslag[-1]["van"] if ontslag else (max(tots) if tots else None)
            if start and eind and eind < start:
                eind = None
            laatste = [r for r in recs if r["soort"] != "ontslag"][-1]
            g["mechanisme"] = self._mechanisme(g, recs)
            self.relaties.append({
                "bron": g["bron"], "doel": g["doel"], "type": g["type"], "mechanisme": g["mechanisme"],
                "functie": laatste["functie"][:200], "start": start, "eind": eind,
                "eind_uit_termijn": bool(eind and not ontslag and all(r.get("tot_uit_termijn") for r in recs if r.get("tot") == eind)),
                "records": recs[-MAX_ARG:], "sleutel": laatste["sleutel"], "regel": laatste["regel"],
                "claim": self._claim(laatste), "score": g["score"], "categorie": g["categorie"],
                "politiek": g["politiek"]})
            self.tel[f"{g['type']}/{g['mechanisme']}"] += 1

    def _mechanisme(self, g: dict, recs: list[dict]) -> str:
        functies = {functie_gewicht(r["functie"])[0] for r in recs}
        if g["type"] == "bestuurder" and any(re.search(r"toezicht|commissaris", sleutel(r["functie"])) for r in recs):
            return TOEZICHT_MECH
        if g["type"] == "ambt" and (functies & {"voorzitter", "vicevoorzitter", "bestuur"}
                                    or g["categorie"] in BESTUURSCOLLEGE):
            return LEIDING_MECH
        return MECH

    def _zelfcontrole(self):
        """Wat de registercheck (staatscourant.controleer) zou afkeuren, wordt niet gepland."""
        def ok(rec, persoonsnaam, orgnaam, ids, rtype):
            eind = [{"name": persoonsnaam, "type": "persoon", "ids": set()}, {"name": orgnaam, "type": "org", "ids": ids}]
            return sc.controleer({}, rec["sleutel"], rec, rtype, eind)
        blijven = []
        for r in self.relaties:
            naam = self.personen_sc[r["bron"][1]]["naam"]
            ids = {("oo", self.oo_orgs[r["doel"][1]]["oo_id"])} if r["doel"][0] == "oo" else \
                {("oo", w) for w, e in self.ext_oo.items() if e == r["doel"][1]}
            goed = []
            for rec in r["records"]:
                reden = ok(rec, naam, self.org[r["doel"][1]][0], ids, r["type"])
                if reden:
                    self.tel["registercheck zou afkeuren"] += 1
                    self.overgeslagen.append({"soort": rec["soort"], "reden": f"registercheck: {reden}", "tekst": rec["regel"]})
                else:
                    goed.append(rec)
            if goed:
                r["records"] = goed
                blijven.append(r)
            else:
                self.tel[f"{r['type']}/{r['mechanisme']}"] -= 1
        self.relaties = blijven
        extra = []
        for x in self.extra_bron:
            naam = self.conn.execute("SELECT name FROM entities WHERE id = ?", (x["persoon_id"],)).fetchone()[0]
            ids = {("oo", w) for w, e in self.ext_oo.items() if e == x["org_id"]}
            reden = ok(x["rec"], naam, self.org[x["org_id"]][0], ids, x["bestaand_type"])
            if reden:
                self.tel["registercheck zou afkeuren"] += 1
                self.tel["extra bron"] -= 1
                self.overgeslagen.append({"soort": "extra bron", "reden": f"registercheck: {reden}", "tekst": x["rec"]["regel"]})
            else:
                extra.append(x)
        # hooguit MAX_ARG nieuwe argumenten per bestaand verband (de nieuwste eerst)
        per: dict[int, list] = defaultdict(list)
        for x in sorted(extra, key=lambda x: x["rec"].get("publicatiedatum") or "", reverse=True):
            per[x["relation_id"]].append(x)
        self.extra_bron = [x for lijst in per.values() for x in lijst[:MAX_ARG]]
        nodig = {r["bron"][1] for r in self.relaties}
        self.personen_sc = {k: v for k, v in self.personen_sc.items() if k in nodig}

    @staticmethod
    def _claim(rec: dict) -> str:
        jaar, nr = re.match(r"stcrt-(\d{4})-(.+)$", rec["publicatie"]).groups()
        werkw = {"benoeming": "benoemd tot", "herbenoeming": "herbenoemd tot", "ontslag": "ontslagen als"}[rec["soort"]]
        periode = ""
        if rec.get("van") and rec["soort"] != "ontslag":
            periode = f" met ingang van {rec['van']}"
            if rec.get("tot"):
                periode += f" tot {rec['tot']}" + (f" ({rec['termijn']})" if rec.get("tot_uit_termijn") else "")
        elif rec.get("van"):
            periode = f" per {rec['van']}"
        door = "bij koninklijk besluit" if rec["kb"] else f"door {rec['benoemer']}"
        return (f"Volgens de Staatscourant ({jaar}, nr. {nr}, gepubliceerd {rec.get('publicatiedatum')}) is "
                f"{rec['persoon']} {door} {werkw} {rec['functie']} van {rec['organisatie']}{periode}.")


class Indiener(tkm.Indiener):
    """Nieuwe personen (zonder externe id), registerorganisaties zoals tk_naar_model, nieuwe verbanden
    met één argument per record en extra argumenten op bestaande verbanden; één bron per uitgave."""

    def __init__(self, plan: Plan, rest, log=print):
        super().__init__(plan, rest, log, bron=sc, cluster=CLUSTER)
        self.bronnen: dict[str, int] = {}

    def bron_van(self, uitgave: str) -> int:
        if uitgave not in self.bronnen:
            data = sc.lees_uitgave(uitgave)
            status, res = self.rest("POST", "/api/sources", {
                "title": data["titel"], "source_type": "dataset", "publisher": sc.UITGEVER,
                "date_published": uitgave, "cluster_key": CLUSTER, "location": {"type": "url", "value": sc.URL},
                "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
            if status not in (200, 201):
                raise SystemExit(f"bron registreren faalde: {status} {res}")
            self.bronnen[uitgave] = res["id"]
        return self.bronnen[uitgave]

    def entiteiten(self):
        for pk, p in self.p.personen_sc.items():
            if p["bestaand"]:
                self.ent[("persoon", pk)] = p["bestaand"]
                continue
            body = {"name": p["naam"], "type": "persoon", "description": p["beschrijving"]}
            if p["rol"] in self.p.rol:
                body["primary_role_id"] = self.p.rol[p["rol"]]
            status, res = self.rest("POST", "/api/entities", body)
            if status == 201:
                self.ent[("persoon", pk)] = res["id"]
                self.tel["persoon nieuw"] += 1
            else:
                self.tel[f"persoon fout {status}"] += 1
                self.log(f"  ✗ {p['naam']}: {status} {res.get('error')}")
        self.p.personen, self.p.nieuwe_orgs = {}, {}
        super().entiteiten()   # registerorganisaties ('oo') die een verband nodig heeft

    def _argument(self, rid: int, rec: dict, claim: str) -> int:
        status, res = self.rest("POST", "/api/arguments", {
            "relation_id": rid, "claim": claim, "stance": "supporting",
            "citations": [{"source_id": self.bron_van(rec["_uitgave"]), "quote": rec["regel"],
                           "methode": "officieel_register_scrape", "section": rec["sleutel"],
                           "page": f"{sc.BRON}/{rec['_uitgave']}", "context": rec["vindplaats"]}]})
        if status != 201:
            self.log(f"  ✗ argument {rec['sleutel']} op #{rid}: {status} {res.get('error')}")
        return status

    def relaties(self, _bron_id=None):
        for r in self.p.relaties:
            s, t = self._id(r["bron"]), self._id(r["doel"])
            if not s or not t:
                self.tel["relatie zonder eindpunt"] += 1
                continue
            if (s, t, r["type"]) in self.bestaande_relaties:
                self.tel["relatie bestond"] += 1
                continue
            body = {"source_id": s, "target_id": t, "relation_type": r["type"], "mechanism_id": self.p.mech[r["mechanisme"]],
                    "functie": r["functie"]}
            for veld, waarde in (("active_from", r["start"]), ("active_until", r["eind"])):
                if waarde:
                    body[veld] = waarde
            status, res = self.rest("POST", "/api/relations", body)
            if status != 201:
                self.tel[f"relatie fout {status}"] += 1
                self.log(f"  ✗ relatie {r['type']} {s}→{t}: {status} {res.get('error')}")
                continue
            self.bestaande_relaties.add((s, t, r["type"]))
            self.tel["relatie nieuw"] += 1
            for rec in r["records"]:
                st = self._argument(res["id"], rec, Plan._claim(rec))
                self.tel["argument" if st == 201 else f"argument fout {st}"] += 1

    def extra_bronnen(self):
        for x in self.p.extra_bron:
            st = self._argument(x["relation_id"], x["rec"], x["claim"])
            self.tel["extra bron" if st == 201 else f"extra bron fout {st}"] += 1


# ── rapport ─────────────────────────────────────────────────────────────────
def _org_naam(plan: Plan, ref: tuple) -> str:
    return plan.org[ref[1]][0]


def rapport(plan: Plan, top: int) -> dict:
    recs = list(plan.records.values())
    kand = plan.kandidaten
    per_soort = Counter(r["soort"] for r in recs)
    per_cat = defaultdict(Counter)
    for k in kand:
        per_cat[k["categorie"]][k["soort"]] += 1
    benoemer = Counter("koninklijk besluit" if r["kb"] else
                       ("bewindspersoon (of namens)" if Plan._door_kroon_of_minister(r) else "ander orgaan") for r in recs)
    items = []
    for r in plan.relaties:
        p = plan.personen_sc[r["bron"][1]]
        items.append({"score": r["score"], "wat": "nieuw verband", "type": r["type"], "categorie": r["categorie"],
                      "persoon": p["naam"], "persoon_nieuw": not p["bestaand"], "organisatie": _org_naam(plan, r["doel"]),
                      "functie": r["functie"], "begin": r["start"], "eind": r["eind"], "politiek": r["politiek"],
                      "argumenten": len(r["records"]), "citaat": r["regel"], "vindplaats": r["records"][-1]["vindplaats"]})
    for x in plan.extra_bron:
        k = next(k for k in kand if k["sleutel"] == x["rec"]["sleutel"])
        naam = plan.conn.execute("SELECT name FROM entities WHERE id = ?", (x["persoon_id"],)).fetchone()[0]
        items.append({"score": x["score"], "wat": f"extra bron op #{x['relation_id']} ({x['bestaand_type']})",
                      "type": x["bestaand_type"], "categorie": k["categorie"], "persoon": naam, "persoon_nieuw": False,
                      "organisatie": plan.org[x["org_id"]][0], "functie": x["rec"]["functie"],
                      "begin": x["rec"].get("van"), "eind": x["rec"].get("tot"), "politiek": k["politiek"],
                      "argumenten": 1, "citaat": x["rec"]["regel"], "vindplaats": x["rec"]["vindplaats"]})
    items.sort(key=lambda i: -i["score"])
    draaideur = sorted([k for k in kand if k["politiek"] and k["categorie"] in ZWAAR | {"zbo", "commissie", "overig"}
                        and k["soort"] != "ontslag"], key=lambda k: -k["score"])
    conc = sorted(((pk, orgs) for pk, orgs in plan.concentratie.items() if len(orgs) >= 2), key=lambda x: -len(x[1]))
    naam_van = {}
    for k in kand:
        naam_van.setdefault(plan.persoonsleutel(plan.records[k["sleutel"]]), (k["persoon"], k["persoon_id"]))
    niet = sorted([k for k in kand if k["status"] not in ("nieuw verband", "extra bron") and k["score"] >= 3.0],
                  key=lambda k: -k["score"])
    return {
        "uitgave": plan.uitgave, "uitgaven": sorted({r["_uitgave"] for r in recs}),
        "publicaties": sum(len(sc.lees_uitgave(u)["publicaties"]) for u in sorted({r["_uitgave"] for r in recs})),
        "records_per_soort": dict(per_soort), "benoemer": dict(benoemer),
        "per_categorie": {c: dict(v) for c, v in sorted(per_cat.items(), key=lambda x: -sum(x[1].values()))},
        "personen_in_model": len({k["persoon_id"] for k in kand if k["persoon_id"]}),
        "top": items[:top],
        "draaideur_kandidaten": [{"score": k["score"], "persoon": k["persoon"], "persoon_id": k["persoon_id"],
                                  "politiek": k["politiek"], "functie": k["functie"], "organisatie": k["organisatie"],
                                  "categorie": k["categorie"], "van": k["van"], "status": k["status"],
                                  "citaat": k["regel"]} for k in draaideur[:40]],
        "concentratie": [{"persoon": naam_van.get(pk, (pk, None))[0], "persoon_id": naam_van.get(pk, (pk, None))[1],
                          "colleges": sorted(orgs)} for pk, orgs in conc[:40]],
        "interessant_niet_gepland": [{"score": k["score"], "reden": k["status"], "categorie": k["categorie"],
                                      "persoon": k["persoon"], "organisatie": k["organisatie"], "citaat": k["regel"]}
                                     for k in niet[:40]],
    }


def markdown(rap: dict, samenvatting: dict) -> str:
    r = ["# Staatscourant: benoemingen (droogloop)", "",
         f"Uitgave(n) {', '.join(rap['uitgaven'])} · {rap['publicaties']} publicaties · records: "
         + ", ".join(f"{k} {v}" for k, v in rap["records_per_soort"].items())
         + f" · benoemer: " + ", ".join(f"{k} {v}" for k, v in rap["benoemer"].items()), "",
         f"Gepland: {samenvatting['nieuwe_verbanden']} nieuwe verbanden ({samenvatting['nieuwe_personen']} nieuwe personen), "
         f"{samenvatting['extra_bronnen']} extra bronnen op bestaande verbanden.", "",
         "Score = categorie × functie × soort × politieke achtergrond (×2) × in model (×1,5) × concentratie × lopend.", "",
         "## Per categorie", "", "| categorie | benoeming | herbenoeming | ontslag |", "|---|---|---|---|"]
    for c, v in rap["per_categorie"].items():
        r.append(f"| {c} | {v.get('benoeming', 0)} | {v.get('herbenoeming', 0)} | {v.get('ontslag', 0)} |")
    r += ["", "## Top", "", "| # | score | wat | persoon | functie | organisatie | per | politiek (model) |",
          "|---|---|---|---|---|---|---|---|"]
    for i, t in enumerate(rap["top"], 1):
        r.append(f"| {i} | {t['score']} | {t['wat']} | {t['persoon']}{' (nieuw)' if t['persoon_nieuw'] else ''} | "
                 f"{t['functie']} | {t['organisatie']} | {t['begin'] or '?'} | {'; '.join(t['politiek']) or '–'} |")
    r += ["", "## Draaideur-kandidaten (politieke achtergrond in het model)", ""]
    r += [f"- {k['score']} · {k['persoon']} ({'; '.join(k['politiek'])}) → {k['functie']} {k['organisatie']}"
          f" [{k['categorie']}, {k['status']}]" for k in rap["draaideur_kandidaten"]]
    r += ["", "## Concentratie (dezelfde naam in meer colleges)", ""]
    r += [f"- {c['persoon']}{' (#' + str(c['persoon_id']) + ')' if c['persoon_id'] else ''}: {'; '.join(c['colleges'])}"
          for c in rap["concentratie"]]
    r += ["", "## Interessant maar niet gepland", ""]
    r += [f"- {k['score']} · {k['persoon']} → {k['organisatie']} ({k['reden']})" for k in rap["interessant_niet_gepland"]]
    return "\n".join(r) + "\n"


def alle_records() -> dict[str, dict]:
    uit = {}
    for p in sc.uitgaven():
        d = sc.lees_uitgave(p.stem.split("_", 1)[1])
        for s, r in d["records"].items():
            uit.setdefault(s, {**r, "_uitgave": d["uitgave"]})
    return uit


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--haal", action="store_true", help="eerst nieuwe publicaties ophalen")
    ap.add_argument("--indienen", action="store_true")
    a = ap.parse_args()
    if a.haal:
        print(sc.haal())
    records = alle_records()
    if not records:
        raise SystemExit("nog geen uitgave; eerst: python3 tools/registers/staatscourant.py haal")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(records, conn, koppelingen).maak()
    rap = rapport(plan, a.top)
    samenvatting = {
        "uitgave": plan.uitgave, "records": len(records),
        "nieuwe_verbanden": len(plan.relaties),
        "nieuwe_personen": sum(1 for p in plan.personen_sc.values() if not p["bestaand"]),
        "bestaande_personen_in_nieuwe_verbanden": sum(1 for p in plan.personen_sc.values() if p["bestaand"]),
        "registerorganisaties_nieuw": len({r["doel"] for r in plan.relaties if r["doel"][0] == "oo"}),
        "extra_bronnen": len(plan.extra_bron),
        "bestaande_verbanden_met_extra_bron": len({x["relation_id"] for x in plan.extra_bron}),
        "telling": {k: v for k, v in sorted(plan.tel.items()) if v}}
    print(json.dumps(samenvatting, ensure_ascii=False, indent=1))
    sc.MAP.mkdir(parents=True, exist_ok=True)
    (sc.MAP / f"rapport_{plan.uitgave}.json").write_text(json.dumps({"samenvatting": samenvatting, **rap},
                                                                     ensure_ascii=False, indent=1), encoding="utf-8")
    (sc.MAP / "analyse.md").write_text(markdown(rap, samenvatting), encoding="utf-8")
    (sc.MAP / f"overgeslagen_{plan.uitgave}.json").write_text(
        json.dumps(plan.overgeslagen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nTop {a.top}:")
    for i, t in enumerate(rap["top"], 1):
        print(f"{i:>3}. {t['score']:>6}  {t['persoon']}{' (nieuw)' if t['persoon_nieuw'] else ''} — {t['functie']}, "
              f"{t['organisatie']} [{t['wat']}, {t['categorie']}] per {t['begin'] or '?'}"
              + (f"  · politiek: {'; '.join(t['politiek'])}" if t["politiek"] else "")
              + f"\n        “{t['citaat'][:300]}”")
    if not a.indienen:
        print(f"\n(droogloop — niets ingediend; rapport in {sc.MAP}/rapport_{plan.uitgave}.json en analyse.md)")
        return
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()))
    ind.entiteiten()
    ind.relaties()
    ind.extra_bronnen()
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
