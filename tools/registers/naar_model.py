#!/usr/bin/env python3
"""Register van overheidsorganisaties → het model (Uitbreiding C, eigenaarsbesluit 2026-10-07).

Trap 3 van de registerpijplijn: leest een bewaarde uitgave (oo.py), bepaalt welke
organisaties, ambtsdragers en verbanden in het model horen, en dient ze in via de REST-API
onder het bijdrager-account `register-import` (dogfood-regel: nooit rechtstreeks in de DB).
Elk verband krijgt één steunend argument met als citaat de letterlijke recordregel
(methode `officieel_register_scrape`); scripts/registercheck.py controleert die regel
deterministisch tegen dezelfde uitgave en geeft het onafhankelijke A1-oordeel.

Diepte (eigenaarsbesluit "Rijk + alle bestuurders"):
  - organisaties: ministeries (+ directoraten-generaal, planbureaus, AIVD, NCTV, OM, RVD,
    Belastingdienst), agentschappen, zbo's (geen categorieën als "Keuringsinstanties …"),
    adviescolleges (+ WRR), inspecties, Hoge Colleges van Staat, rechtspraak, politie, SER,
    provincies, gemeenten, waterschappen;
  - ambtsdragers: bewindspersonen, SG's, DG's en de leiding van deze organisaties,
    commissarissen van de Koning, burgemeesters, wethouders, dijkgraven, Eerste Kamerleden.
    Sinds 2026-10-13 ook: gedeputeerden (lid van Gedeputeerde Staten), gemeente- en
    provinciesecretarissen, de secretaris-directeur van een waterschap en het hele bestuur dat
    het register bij een zbo, adviescollege of gerecht noemt (vicevoorzitter, bestuursleden,
    (niet-)rechterlijke bestuursleden, de Raad voor de rechtspraak). Staatsraden wachten op een
    mechanisme (STAATSRAAD_MECH); gewone leden van een college zijn geen leiding.
    Raadsleden niet. Kamerleden van de Tweede Kamer komen uit de Tweede Kamer-API (tk.py).
  - partijen: een landelijke partij uit de partijtabel; een lokale of provinciale partij wordt
    een eigen partijknoop met de bestuurslaag van haar gemeente of provincie (oo.lokale_partij).

Koppelen (nooit op naam alleen):
  - organisaties: eerst externe_ids (oo/tooi), dan koppelingen.json (ingecheckt, met de hand
    nagelopen), anders nieuw;
  - organisaties die al bestonden krijgen ook de rol die de registersoort geeft (een ministerie
    → departement), naast wat ze al waren;
  - personen: een volledige naam die exact gelijk is aan een bestaande persoon met een
    passende rol, of met al een verband met dezelfde organisatie, wordt gekoppeld; anders een
    nieuwe knoop. Een titel achter de naam ("MPM", "MSc") telt niet mee. Een naam met alleen
    voorletters krijgt altijd een toevoeging ("B.C.M. Vostermans (burgemeester Peel en Maas)").
    Een burgemeester of wethouder met alleen een achternaam ("Dhr. Fortuin") komt erbij als
    Wikidata precies één persoon kent met die achternaam in die functie in die gemeente, met een
    ambt dat volgens Wikidata loopt (wikidata.kandidaten): dan met die volledige naam en de QID
    als externe id. Anders blijft hij weg (2026-10-13).

Gebruik:
    python3 tools/registers/naar_model.py                    # droogloop: plan + aantallen
    python3 tools/registers/naar_model.py --plan-json pad    # plan wegschrijven
    python3 tools/registers/naar_model.py --indienen [--alleen organisaties|personen]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import oo  # noqa: E402
import wikidata  # noqa: E402
from common import (ROOT, afkorting_botst, geen_afkorting, klem_relaties, looptijd,  # noqa: E402
                    ontleed_naam, partij_naam, sleutel)

DB_PATH = ROOT / "data" / "propaganda_model.db"
TOKEN = ROOT / "data" / "tokens" / "register-import.token"
API = "http://127.0.0.1:5000"
KOPPELINGEN = HIER / "koppelingen.json"
CLUSTER = "register:oo"

# ── Selectie ────────────────────────────────────────────────────────────────
TOP_TYPES = {"Ministerie", "Agentschap", "Zelfstandig bestuursorgaan", "Adviescollege",
             "Inspectie", "Hoog College van Staat", "Rechtspraak", "Politie", "Provincie",
             "Gemeente", "Waterschap"}
EXTRA_ORGS = {  # oo_id → reden (onderdelen of afwijkende soorten die er wél in horen)
    "28351125": "WRR (externe commissie, wettelijk adviescollege)",
    "28455002": "SER (openbaar lichaam voor beroep en bedrijf)",
    "213": "Rijksvoorlichtingsdienst", "9633": "AIVD", "98010": "NCTV",
    "68888": "Directoraat-generaal Belastingdienst", "13333": "Openbaar Ministerie",
    "28963276": "Centraal Planbureau", "112992": "Planbureau voor de Leefomgeving",
    "66140": "Sociaal en Cultureel Planbureau",
}
NIET = {"704": "Kanselarij der Nederlandse Orden", "28630377": "College van afgevaardigden",
        "28044796": "Parket bij de Hoge Raad"}
DG_NAAM = re.compile(r"^(Directoraat-generaal|Directeur-Generaal)\b", re.I)
ZBO_CATEGORIE = re.compile(
    r"^(Keurings|Aangemelde|Aangewezen|Certificerende|Erkenninghouders|Gecertificeerde|"
    r"Inrichtingen|Instellingen|Onderzoeksgerechtigden|Reclasseringsorganisaties|Representatief|"
    r"Metacluster|Bevoegde autoriteiten|Uitvoerders|Waarborginstellingen|VTS-operators|"
    r"Klassenbureaus|Regionale Loodsencorporaties|Medisch-ethische|Havenbeheerders|"
    r"Rijkshavenmeesters|Notarissen|Gerechtsdeurwaarders|Bedrijfstakpensioenfondsen|Grondkamers|"
    r"Registratiecommissies|Nederlands Meetinstituut ex)|\bex (art|Regeling|Besluit)", re.I)
TOEZICHTHOUDERS = {"Autoriteit Consument en Markt", "Stichting Autoriteit Financiële Markten",
                   "De Nederlandsche Bank", "Autoriteit Persoonsgegevens", "Nederlandse Zorgautoriteit",
                   "Kansspelautoriteit", "Commissariaat voor de Media", "Kiesraad"}

# ── Theorie-id's (op naam, uit de DB) ───────────────────────────────────────
ROLNAMEN = ("departement", "uitvoeringsorganisatie", "adviesorgaan", "controleorgaan",
            "parlementair_controleur", "bestuursrechter", "decentrale_overheid", "toezichthouder",
            "elite_forum", "bewindspersoon", "topambtenaar", "lokale_bestuurder", "politicus",
            "partij")
MECHNAMEN = ("hierarchische_aansturing", "verzelfstandigd_bestuur", "institutioneel_advies",
             "ministeriele_verantwoordelijkheid", "ambtelijke_leiding", "lokaal_bestuursmandaat",
             "kamerzetel", "partijlijn")
# Het bestuur dat het register bij een zbo, adviescollege, gerecht of externe commissie noemt,
# naast de leiding uit de voorkeursvolgorde (2026-10-13): ambtelijke leiding, net als de voorzitter
BESTUUR_FUNCTIES = {"vicevoorzitter", "ondervoorzitter", "vicepresident", "vicepresident/algemeen secretaris", "bestuurslid", "lid raad van bestuur",
                    "bestuurder bedrijfsvoering", "bestuurder primair proces", "rechterlijk bestuurslid",
                    "niet-rechterlijk bestuurslid", "voorzitter raad voor de rechtspraak",
                    "rechterlijk lid raad voor de rechtspraak", "niet-rechterlijk lid raad voor de rechtspraak",
                    "permanent lid", "secretaris-directeur", "directeur/algemeen secretaris",
                    "algemeen secretaris/directeur"}
BESTUUR_TYPES = {"Zelfstandig bestuursorgaan", "Adviescollege", "Rechtspraak", "Externe commissie",
                 "Openbaar lichaam voor beroep en bedrijf"}
# Een gewoon lid van een college (adviesraad, commissie) is geen leiding: overgeslagen en geteld
COLLEGE_LEDEN = {"lid", "raadslid", "junior-lid", "commissielid", "collegelid"}
# Staatsraden (Raad van State): geen bestaand mechanisme past op het ambt van een staatsraad (de
# ambtsmechanismen gaan over leiding, een dagelijks bestuur of een Kamerzetel). Zodra de theorie
# er een heeft (RfC), komt de naam hier en gaan ze mee; tot dan overgeslagen en geteld.
STAATSRAAD_MECH: str | None = None
STAATSRAAD_ROL = "bestuursrechter"
# Korte functie in de naam van een knoop met voorletters ("A.B. Jansen (gedeputeerde Fryslân)")
KORT = {"Lid van Gedeputeerde Staten": "gedeputeerde"}

PASSENDE_ROLLEN = {"politicus", "bewindspersoon", "topambtenaar", "lokale_bestuurder",
                   "toezichthouder", "gezagsexpert", "parlementair_controleur", "directie",
                   "raad_van_commissarissen", "belanghebbende", "lobbyist", "voorlichter"}



def kleine(titel: str) -> str:
    """'Minister van Financiën' → 'minister van Financiën' (alleen de eerste letter)."""
    return titel[:1].lower() + titel[1:] if titel else titel


def bij(orgnaam: str) -> str:
    """'Ministerie van Financiën' → 'het Ministerie van Financiën'; anders ongewijzigd."""
    return f"het {orgnaam}" if orgnaam.startswith("Ministerie ") else orgnaam


def fnorm(functie: str) -> str:
    """Functienaam vergelijkbaar maken: 'Inspecteur - Generaal*' → 'inspecteur-generaal'."""
    s = functie.lower().replace("*", "").strip()
    s = re.sub(r"\s*-\s*", "-", s)
    return " ".join(s.split())


def _afkorting_uit(metadata) -> str | None:
    try:
        return (json.loads(metadata) or {}).get("afkorting") if metadata else None
    except (TypeError, ValueError, AttributeError):
        return None


class Plan:
    """Wat er in het model hoort, los van wat er al staat (dat bepaalt de indiener)."""

    def __init__(self, data: dict, conn: sqlite3.Connection):
        self.d = data
        self.uitgave = data["uitgave"]
        self.conn = conn
        self.rol = {n: i for n, i in conn.execute(
            f"SELECT name, id FROM roles WHERE NOT vervangen AND name IN "
            f"({','.join('?' * len(ROLNAMEN))})", ROLNAMEN)}
        self.mech = {n: i for n, i in conn.execute(
            f"SELECT name, id FROM mechanisms WHERE NOT vervangen AND name IN "
            f"({','.join('?' * len(MECHNAMEN))})", MECHNAMEN)}
        ontbreekt = set(MECHNAMEN) - set(self.mech) | (set(ROLNAMEN) - set(self.rol))
        if ontbreekt:
            raise SystemExit(f"Theorie ontbreekt nog in het model: {sorted(ontbreekt)} — "
                             "dien eerst missies/bestuur_theorie.json in (scripts/theorie_indienen.py).")
        koppel = json.loads(KOPPELINGEN.read_text())
        self.koppel = dict(koppel["organisaties"])
        self.koppel_personen = {n: i for n, i in koppel.get("personen", {}).items()
                                if not n.startswith("_")}
        self.partij_id = {n: i for i, n in conn.execute(
            "SELECT id, name FROM entities WHERE type = 'partij' AND status = 'goedgekeurd' "
            "AND NOT vervangen")}
        self.pm_personen = {}
        for i, n, rol, beschr in conn.execute("""
                SELECT e.id, e.name, r.name, e.description FROM entities e
                LEFT JOIN roles r ON r.id = e.primary_role_id
                WHERE e.type = 'persoon' AND NOT e.vervangen AND e.status <> 'afgewezen'"""):
            self.pm_personen.setdefault(sleutel(n), []).append((i, n, rol, beschr or ""))
        self.alle_namen = {sleutel(n) for (n,) in conn.execute(
            "SELECT name FROM entities WHERE NOT vervangen")}
        # Een volledige naam koppelt ook als die persoon al een levend verband met dezelfde
        # organisatie heeft (2026-10-09: "Laura van Geest" bij de AFM werd anders een tweede knoop)
        self.org_ext = {w: i for w, i in conn.execute(
            "SELECT waarde, entity_id FROM externe_ids WHERE stelsel = 'oo'")}
        self.banden: set[tuple[int, int]] = set()
        for a, b in conn.execute("""SELECT source_id, target_id FROM relations
                                    WHERE NOT vervangen AND status <> 'afgewezen'"""):
            self.banden.update(((a, b), (b, a)))
        self.orgs: dict[str, dict] = {}      # oo_id → organisatie-plan
        self.personen_plan: dict[str, dict] = {}  # persoon-sleutel → persoon-plan
        self.relaties: list[dict] = []
        self.overgeslagen: Counter = Counter()
        self.overgeslagen_functies: Counter = Counter()   # functies die (nog) niet meegaan
        self.bestaan: Counter = Counter()                  # wat het bestaan van een eindpunt begrenst
        self.ent_bestaan = {i: (af, au) for i, af, au in conn.execute(
            "SELECT id, active_from, active_until FROM entities WHERE type <> 'persoon' AND NOT vervangen")}
        self.lokale_partijen: dict[str, dict] = {}         # naam → partijplan (2026-10-13)
        # Wikidata (optioneel): volledige naam bij alleen een achternaam (2026-10-13)
        self.wd = wikidata.nieuwste()
        self.wd_index = wikidata.index(self.wd) if self.wd else {}
        self.wd_ext = {w: e for e, w in conn.execute(
            "SELECT entity_id, waarde FROM externe_ids WHERE stelsel = 'wikidata'")}
        # partijknopen op hun naamsleutel: het register schrijft dezelfde partij soms anders
        # ("Doe mee! Molenlanden" / "Doe Mee! Molenlanden")
        self.partij_op_naam = {sleutel(n): i for i, n in conn.execute(
            "SELECT id, name FROM entities WHERE type = 'partij' AND NOT vervangen AND status <> 'afgewezen'")}
        # Afkortingen (2026-10-14): de levende knopen met hun eigen afkorting, voor de botsingsregel
        self.levend = [(i, n, _afkorting_uit(m)) for i, n, m in conn.execute(
            "SELECT id, name, metadata FROM entities WHERE NOT vervangen AND status <> 'afgewezen'")]
        self.afkorting_tel: Counter = Counter()

    # ── organisaties ────────────────────────────────────────────────────────
    def _gekozen(self, o: dict) -> str | None:
        """→ soort ('top', 'dg', 'extra') of None."""
        if o["eind"] or o["oo_id"] in NIET or not o["types"]:
            return None
        if o["oo_id"] in EXTRA_ORGS:
            return "extra"
        if o["ouder_oo"] is None and o["types"][0] in TOP_TYPES:
            if "aruba" in o["naam"].lower():
                return None
            if o["types"][0] == "Zelfstandig bestuursorgaan" and ZBO_CATEGORIE.search(o["naam"]):
                return None
            return "top"
        if (o["types"][0] == "Organisatieonderdeel" and DG_NAAM.match(o["naam"])
                and self.d["organisaties"].get(o["top_oo"], {}).get("types", [""])[0] == "Ministerie"):
            return "dg"
        return None

    def _naam_org(self, o: dict) -> str:
        t = o["types"][0]
        if t == "Ministerie":
            return f"Ministerie van {o['naam']}"
        if t == "Waterschap" and not re.match(r"(?i)^(waterschap|hoogheemraadschap|wetterskip)", o["naam"]):
            return f"Waterschap {o['naam']}"
        if t == "Organisatieonderdeel":
            return re.sub(r"(?i)^Directeur-Generaal\b", "Directoraat-generaal", o["naam"])
        return o["naam"]

    def _rol_org(self, o: dict, soort: str) -> str:
        t, oid = o["types"][0], o["oo_id"]
        if o["naam"] in TOEZICHTHOUDERS:
            return "toezichthouder"
        if oid in ("28963276", "112992", "66140", "28351125"):
            return "adviesorgaan"          # planbureaus en de WRR
        if oid == "28455002":
            return "elite_forum"           # de SER, zoals het model hem al kent
        if soort == "dg" or t == "Ministerie" or oid == "213":
            return "departement"
        if oid in ("68888", "9633", "98010", "13333"):
            return "uitvoeringsorganisatie"  # Belastingdienst, AIVD, NCTV, OM
        per_naam = {"Tweede Kamer der Staten-Generaal": "parlementair_controleur",
                    "Eerste Kamer der Staten-Generaal": "parlementair_controleur",
                    "Raad van State": "adviesorgaan"}
        if o["naam"] in per_naam:
            return per_naam[o["naam"]]
        return {
            "Agentschap": "uitvoeringsorganisatie", "Zelfstandig bestuursorgaan": "uitvoeringsorganisatie",
            "Politie": "uitvoeringsorganisatie", "Adviescollege": "adviesorgaan",
            "Inspectie": "controleorgaan", "Hoog College van Staat": "controleorgaan",
            "Rechtspraak": "bestuursrechter", "Provincie": "decentrale_overheid",
            "Gemeente": "decentrale_overheid", "Waterschap": "decentrale_overheid",
        }.get(t, "uitvoeringsorganisatie")

    def organisaties(self):
        for o in self.d["organisaties"].values():
            soort = self._gekozen(o)
            if not soort:
                continue
            self.orgs[o["oo_id"]] = {
                "oo_id": o["oo_id"], "tooi": o["tooi"], "naam": self._naam_org(o),
                "type": "rechterlijke_macht" if o["types"][0] == "Rechtspraak" else "overheidsinstelling",
                "rol": self._rol_org(o, soort), "bestuurslaag": o["bestuurslaag"] or "rijk",
                "oo_type": o["types"][0], "soort": soort, "regel": o["regel"],
                "sleutel": o["sleutel"], "url": o["url"], "start": o["start"],
                "beschrijving": o["beschrijving"], "bestaand": self.koppel.get(o["oo_id"]),
                "record": o,
            }
        # verbanden tussen organisaties
        for p in self.orgs.values():
            o = p["record"]
            t = o["types"][0]
            if p["soort"] in ("dg", "extra") and o["ouder_oo"]:
                minis = self.orgs.get(o["top_oo"])
                if minis and minis["oo_type"] == "Ministerie" and p["rol"] != "adviesorgaan":
                    self._rel(minis, p, "zeggenschap", "hierarchische_aansturing", o,
                              "valt", f"als onderdeel onder het {minis['naam']}")
                    continue
                if minis and p["rol"] == "adviesorgaan":
                    self._rel(p, minis, "adviseur", "institutioneel_advies", o,
                              "is", f"een planbureau binnen het {minis['naam']}")
                    continue
            minis = self.orgs.get(o["ministerie_oo"] or "")
            if not minis:
                continue
            if t in ("Agentschap", "Inspectie", "Politie"):
                self._rel(minis, p, "zeggenschap", "hierarchische_aansturing", o,
                          "heeft", f"als relatie met ministerie het {minis['naam']}")
            elif t == "Zelfstandig bestuursorgaan":
                self._rel(minis, p, "zeggenschap", "verzelfstandigd_bestuur", o,
                          "is", f"een zelfstandig bestuursorgaan met als relatie met ministerie het {minis['naam']}")
            elif t in ("Adviescollege", "Externe commissie"):
                self._rel(p, minis, "adviseur", "institutioneel_advies", o,
                          "is", f"een adviescollege met als relatie met ministerie het {minis['naam']}")

    # ── personen ────────────────────────────────────────────────────────────
    def _functie_rol(self, org: dict, f: dict, nested_in: dict) -> tuple[str, str, str] | None:
        """→ (rol, mechanisme, functietitel) als deze functie erin hoort, anders None."""
        fn = fnorm(f["functie"])
        t = org["oo_type"]
        if t == "Ministerie" and nested_in is org:
            if fn.startswith("minister") or fn.startswith("staatssecretaris"):
                return ("bewindspersoon", "ministeriele_verantwoordelijkheid", f["functie"])
            if fn == "secretaris-generaal":
                return ("topambtenaar", "ambtelijke_leiding", f["functie"])
            return None
        if t in ("Gemeente",):
            if fn in ("burgemeester", "burgemeester waarnemend", "wethouder"):
                titel = "Burgemeester (waarnemend)" if fn == "burgemeester waarnemend" else f["functie"]
                return ("lokale_bestuurder", "lokaal_bestuursmandaat", titel)
            if fn == "gemeentesecretaris":  # de ambtelijke top van de gemeente (2026-10-13)
                return ("topambtenaar", "ambtelijke_leiding", f["functie"])
            return None
        if t == "Provincie":
            if fn == "commissaris van de koning":
                return ("lokale_bestuurder", "lokaal_bestuursmandaat", "Commissaris van de Koning")
            # 2026-10-13: Gedeputeerde Staten (het dagelijks bestuur) en de provinciesecretaris
            if fn == "lid" and f.get("org_naam") == "Gedeputeerde Staten":
                return ("lokale_bestuurder", "lokaal_bestuursmandaat", "Lid van Gedeputeerde Staten")
            if fn in ("provinciesecretaris", "algemeen directeur/provinciesecretaris"):
                return ("topambtenaar", "ambtelijke_leiding", f["functie"])
            return None
        if t == "Waterschap":
            if fn in ("dijkgraaf", "watergraaf"):
                return ("lokale_bestuurder", "lokaal_bestuursmandaat", f["functie"])
            if fn == "secretaris-directeur":  # de ambtelijke top van het waterschap (2026-10-13)
                return ("topambtenaar", "ambtelijke_leiding", f["functie"])
            return None
        if org["naam"] == "Eerste Kamer der Staten-Generaal":
            if fn.startswith("kamerlid"):
                return ("politicus", "kamerzetel", f["functie"])
            return None
        if org["naam"] == "Raad van State":
            if fn == "vice-president":
                return ("topambtenaar", "ambtelijke_leiding", "Vice-president")
            if fn.startswith("staatsraad"):
                if STAATSRAAD_MECH and STAATSRAAD_MECH in self.mech:
                    return (STAATSRAAD_ROL, STAATSRAAD_MECH, f"{f['functie']}, {f['org_naam']}")
                self.overgeslagen_functies[f"{fn} ({f.get('org_naam')}): wacht op een mechanisme"] += 1
            return None
        if org["naam"] == "Algemene Rekenkamer":
            return ("topambtenaar", "ambtelijke_leiding", f["functie"]) if fn == "president" else None
        if org["naam"] == "Nationale ombudsman":
            return ("topambtenaar", "ambtelijke_leiding", f["functie"]) if fn == "nationale ombudsman" else None
        if nested_in is not org:
            return None  # leiding van subonderdelen niet
        hoofd = {
            "Agentschap": ("directeur-generaal", "algemeen directeur", "directeur"),
            "Zelfstandig bestuursorgaan": ("voorzitter", "bestuursvoorzitter", "president",
                                           "directeur-bestuurder", "algemeen directeur", "directeur"),
            "Adviescollege": ("voorzitter",), "Externe commissie": ("voorzitter",),
            "Inspectie": ("inspecteur-generaal", "hoofdinspecteur"),
            "Rechtspraak": ("president", "president en voorzitter"),
            "Politie": ("korpschef",),
            "Organisatieonderdeel": ("directeur-generaal", "nationaal coördinator terrorismebestrijding en veiligheid",
                                     "directeur"),
            "Openbaar lichaam voor beroep en bedrijf": ("voorzitter",),
        }.get(t, ())
        if fn in hoofd or (t in BESTUUR_TYPES and fn in BESTUUR_FUNCTIES):
            return ("topambtenaar", "ambtelijke_leiding", f["functie"].replace("*", "").strip())
        if t in BESTUUR_TYPES and fn in COLLEGE_LEDEN:
            self.overgeslagen_functies[f"{fn} van een {t.lower()} (geen leiding)"] += 1
        return None

    def personen(self):
        funcs_per_org: dict[str, list[dict]] = {}
        for f in self.d["functies"].values():
            if f["eind"]:
                continue
            funcs_per_org.setdefault(f["oo_id"], []).append(f)
        for oo_id, org in self.orgs.items():
            # functies op de organisatie zelf, plus (voor provincies, Raad van State en de
            # Eerste Kamer) op haar onderdelen
            bronnen = [(org, funcs_per_org.get(oo_id, []))]
            if org["oo_type"] in ("Provincie", "Hoog College van Staat"):
                for sub in self.d["organisaties"].values():
                    if sub["top_oo"] == oo_id and sub["oo_id"] != oo_id and not sub["eind"]:
                        bronnen.append(({"oo_id": sub["oo_id"]}, funcs_per_org.get(sub["oo_id"], [])))
            gekozen: dict[str, list] = {}
            for nested, funcs in bronnen:
                for f in funcs:
                    hit = self._functie_rol(org, f, org if nested is org else nested)
                    if hit:
                        gekozen.setdefault(fnorm(f["functie"]), []).append((f, hit))
            # bij leiding: alleen de eerste functie in de voorkeursvolgorde, hooguit 2 personen
            if org["oo_type"] not in ("Ministerie", "Gemeente", "Provincie", "Waterschap") \
                    and org["naam"] != "Eerste Kamer der Staten-Generaal":
                # het bestuur dat het register noemt gaat mee (2026-10-13), naast de leiding
                bestuur = {k: v for k, v in gekozen.items()
                           if k in BESTUUR_FUNCTIES or k.startswith("staatsraad")}
                for voorkeur in ("vice-president", "president", "nationale ombudsman",
                                 "inspecteur-generaal", "directeur-generaal", "korpschef",
                                 "nationaal coördinator terrorismebestrijding en veiligheid",
                                 "voorzitter", "bestuursvoorzitter", "president en voorzitter",
                                 "directeur-bestuurder", "algemeen directeur", "hoofdinspecteur",
                                 "directeur"):
                    if voorkeur in gekozen:
                        gekozen = {voorkeur: gekozen[voorkeur][:2]}
                        break
                else:
                    gekozen = {}
                for k, v in bestuur.items():
                    gekozen.setdefault(k, v)
            for lijst in gekozen.values():
                for f, (rol, mech, titel) in lijst:
                    self._persoon(org, f, rol, mech, titel)

    def _naamsleutel(self, naam: dict) -> tuple[str, str]:
        achter = sleutel(f"{naam['tussenvoegsel'] or ''} {naam['achternaam'] or ''}")
        letter = ((naam["voorletters"] or naam["roepnaam"] or naam["voornamen"] or "")[:1]).lower()
        return achter, letter

    def _register_dubbel(self, naam: dict) -> bool:
        """Zijn er in deze registeruitgave verschillende mensen met dezelfde achternaam en
        eerste voorletter (bv. J.M. en J.G. de Vries)? Dezelfde persoon in meer functies
        ("S.M. (Saskia) Kluit" en "S.M. Kluit MSc") telt één keer: we tellen voorletters."""
        if not hasattr(self, "_reg_namen"):
            self._reg_namen = {}
            for f in self.d["functies"].values():
                n = ontleed_naam(f["naam_register"])
                vl = (n["voorletters"] or "").replace(".", "").lower() or \
                     (n["roepnaam"] or n["voornamen"] or "")[:1].lower()
                self._reg_namen.setdefault(self._naamsleutel(n), set()).add(vl)
        return len(self._reg_namen.get(self._naamsleutel(naam), set())) > 1

    def _zelfde_persoon(self, naam: dict, context: list[str]) -> int | None:
        """Een naam met alleen voorletters koppelt alleen aan een bestaande persoon als:
        (1) dezelfde achternaam + eerste voorletter in de hele registeruitgave maar één keer
        voorkomt, (2) er in het model precies één persoon is met die achternaam, die eerste
        letter en een passende rol, en (3) de beschrijving van die persoon de plaats of de
        functie noemt (bv. "burgemeester van Arnhem", "Eerste Kamerlid"). Nooit op naam alleen."""
        achter, letter = self._naamsleutel(naam)
        if not achter or not letter or self._register_dubbel(naam):
            return None
        treffers = []
        for lijst in self.pm_personen.values():
            for i, n, prol, beschr in lijst:
                woorden = sleutel(n).split()
                if (sleutel(n).endswith(" " + achter) and woorden and woorden[0][:1] == letter
                        and prol in PASSENDE_ROLLEN):
                    treffers.append((i, beschr.lower()))
        if len(treffers) != 1:
            return None
        i, beschr = treffers[0]
        if any(c and c.lower() in beschr for c in context):
            self.overgeslagen["voorletters gekoppeld aan bestaande persoon"] += 1
            return i
        return None

    def _persoon(self, org, f, rol, mech, titel):
        naam = ontleed_naam(f["naam_register"])
        qid = None
        if naam["alleen_achternaam"] and naam["achternaam"]:
            naam, qid = self._naam_uit_wikidata(org, f, naam)
        if naam["alleen_achternaam"] or not naam["achternaam"]:
            self.overgeslagen["alleen achternaam"] += 1
            return
        plaats = re.sub(r"^(Gemeente|Provincie) ", "", org["naam"]).replace(
            " der Staten-Generaal", "")
        functie_kort = KORT.get(titel) or titel.split(",")[0].strip().lower()
        if naam["volledig"]:
            weergave = naam["weergave"]
            sleutel_p = f"vol:{sleutel(weergave)}"
        else:
            weergave = f"{naam['weergave']} ({functie_kort} {plaats})"
            sleutel_p = f"init:{sleutel(weergave)}"
        p = self.personen_plan.get(sleutel_p)
        if p is None:
            bestaand = self.koppel_personen.get(f["naam_register"]) or self.wd_ext.get(qid or "")
            if bestaand:
                pass
            elif qid:
                # naam uit Wikidata: alleen koppelen aan wie al bij deze plaats of organisatie hoort
                org_eid = self.org_ext.get(org["oo_id"]) or org.get("bestaand")
                for i, n, prol, beschr in self.pm_personen.get(sleutel(weergave), []):
                    if plaats.lower() in beschr.lower() or (org_eid and (i, org_eid) in self.banden):
                        bestaand = i
                        break
                else:
                    if sleutel(weergave) in self.alle_namen:
                        weergave = f"{weergave} ({functie_kort} {plaats})"
            elif naam["volledig"]:
                org_eid = self.org_ext.get(org["oo_id"]) or org.get("bestaand")
                for i, n, prol, beschr in self.pm_personen.get(sleutel(weergave), []):
                    if (prol in PASSENDE_ROLLEN or plaats.lower() in beschr.lower()
                            or (org_eid and (i, org_eid) in self.banden)):
                        bestaand = i
                        break
                else:
                    if sleutel(weergave) in self.alle_namen:
                        weergave = f"{weergave} ({functie_kort} {plaats})"
            else:
                context = [plaats, org["naam"]] + (["eerste kamer"] if "Eerste Kamer" in org["naam"] else [])
                bestaand = self._zelfde_persoon(naam, context)
                if bestaand is None and sleutel(weergave) in self.alle_namen:
                    self.overgeslagen["toevoeging bestaat al"] += 1
            p = {"sleutel": sleutel_p, "naam": weergave, "rol": rol, "bestaand": bestaand, "qid": qid,
                 "register_naam": f["naam_register"], "oo_medewerker": f["sleutel"].split(":")[-1],
                 "beschrijving": f"{titel} bij {org['naam']} (register van overheidsorganisaties"
                                 + (f"; volledige naam uit Wikidata {qid})" if qid else ")")}
            self.personen_plan[sleutel_p] = p
        # de bewering noemt de naam zoals het register hem geeft (de volledige naam komt uit Wikidata)
        wie = ontleed_naam(f["naam_register"])["weergave"] if qid else naam["weergave"]
        medewerker = f["sleutel"].split(":")[-1]
        if medewerker not in p.setdefault("oo_medewerkers", []):
            p["oo_medewerkers"].append(medewerker)
        self.relaties.append({
            "bron": ("persoon", sleutel_p), "doel": ("org", org["oo_id"]), "type": "ambt",
            "mechanisme": mech, "functie": titel, "start": f["start"], "sleutel": f["sleutel"],
            "regel": f["regel"], "url": org["url"],
            "claim": (f"Volgens het register van overheidsorganisaties (uitgave {self.uitgave}) is "
                      f"{wie} {kleine(titel)} bij {bij(org['naam'])}"
                      f"{' (sinds ' + f['start'] + ')' if f['start'] else ''}."),
        })
        partij = f.get("partij") or self._fractie(f)
        if partij:
            pid = self.partij_id.get(partij_naam(partij) or "")
            lokaal = None if pid or partij_naam(partij) or self._fractie(f) else self._lokale_partij(f)
            if pid or lokaal:
                self.relaties.append({
                    "bron": ("bestaand", pid) if pid else lokaal, "doel": ("persoon", sleutel_p),
                    "type": "lidmaatschap",
                    # Een Eerste Kamerfractie begint met de zetel; bij een burgemeester of
                    # wethouder noemt het register geen begin van het partijlidmaatschap
                    "mechanisme": "partijlijn", "functie": None,
                    "start": f["start"] if "Fracties EK" in f["org_pad"] else None,
                    "sleutel": f["sleutel"],
                    "regel": f["regel"], "url": org["url"],
                    "claim": (f"Volgens het register van overheidsorganisaties (uitgave {self.uitgave}) "
                              + (f"is {wie} lid van de Eerste Kamerfractie van {partij}."
                                 if "Fracties EK" in f["org_pad"] else
                                 f"is {wie}, {kleine(titel)} bij {bij(org['naam'])}, "
                                 f"lid van {partij}.")),
                })
            elif partij_naam(partij):
                self.overgeslagen["landelijke partij niet in het model"] += 1
            elif self._fractie(f):
                self.overgeslagen["Eerste Kamerfractie zonder landelijke partij"] += 1

    def _naam_uit_wikidata(self, org: dict, f: dict, naam: dict) -> tuple[dict, str | None]:
        """Alleen een achternaam in het register: de volledige naam uit Wikidata als daar precies
        één persoon past (zelfde gemeente, functie en achternaam, ambt loopt) en de achternaam in
        deze gemeente en functie maar één keer in het register staat. → (naam, qid)."""
        rec_org = self.d["organisaties"].get(org["oo_id"]) or {}
        cbs, soort = wikidata.cbs_van(rec_org.get("tooi")), wikidata.soort_van(f["functie"])
        if not (self.wd and cbs and soort):
            return naam, None
        achter = sleutel(f"{naam['tussenvoegsel'] or ''} {naam['achternaam'] or ''}")
        zelfde = [g for g in self.d["functies"].values()
                  if g["oo_id"] == org["oo_id"] and not g["eind"] and wikidata.soort_van(g["functie"]) == soort
                  and sleutel(" ".join(filter(None, (ontleed_naam(g["naam_register"])["tussenvoegsel"],
                                                     ontleed_naam(g["naam_register"])["achternaam"])))) == achter]
        kand = wikidata.kandidaten(self.wd_index, cbs, soort, naam, f["start"], self.uitgave)
        if len(zelfde) != 1 or len(kand) != 1:
            return naam, None
        volledig = ontleed_naam(kand[0]["naam"])
        # de registercheck (oo.controleer) eist de achternaam uit het register in de naam: een
        # Wikidata-naam zonder het tweede deel ('Fleur Gräper' voor 'Gräper-van Koolwijk') niet
        if not volledig["volledig"] or sleutel(naam["achternaam"]) not in sleutel(kand[0]["naam"]):
            self.overgeslagen["alleen achternaam: Wikidata-naam mist een deel van de achternaam"] += 1
            return naam, None
        self.overgeslagen["alleen achternaam: volledige naam uit Wikidata"] += 1
        return volledig, kand[0]["qid"]

    def _lokale_partij(self, f: dict) -> tuple | None:
        """Een lokale of provinciale partij (oo.lokale_partij): een bestaande partijknoop onder
        precies die naam, anders een nieuwe. Wat geen partij is, wordt geteld."""
        naam, laag, reden = oo.lokale_partij(self.d, f)
        if not naam:
            self.overgeslagen[f"partij: {reden}"] += 1
            return None
        k = sleutel(naam)
        if k in self.partij_op_naam:
            return ("bestaand", self.partij_op_naam[k])
        if k in self.alle_namen:
            self.overgeslagen["partij: naam is al van een andere knoop"] += 1
            return None
        if k not in self.lokale_partijen:
            org = self.d["organisaties"][self.d["organisaties"][f["oo_id"]]["top_oo"]]
            self.lokale_partijen[k] = {
                "naam": naam, "bestuurslaag": laag, "partij": f["partij"], "org": org["naam"],
                "beschrijving": (f"Partij in de {'gemeente' if laag == 'gemeente' else 'provincie'} "
                                 f"{oo._plaats(org)} (register van overheidsorganisaties).")}
        return ("partij", k)

    @staticmethod
    def _fractie(f: dict) -> str | None:
        """Fractienaam uit het pad van een Eerste Kamerlid ('… > Fracties EK > <fractie>')."""
        delen = f["org_pad"].split(" > ")
        if len(delen) >= 3 and delen[-2].startswith("Fracties"):
            return delen[-1]
        return None

    def _rel(self, bron: dict, doel: dict, rtype: str, mech: str, record: dict, ww: str, rest: str):
        self.relaties.append({
            "bron": ("org", bron["oo_id"]), "doel": ("org", doel["oo_id"]), "type": rtype,
            # Looptijd (eigenaarsbesluit 2026-10-09): het begin en eind dat het record noemt
            "mechanisme": mech, "functie": None, "start": record.get("start"),
            "eind": record.get("eind"), "sleutel": record["sleutel"],
            "regel": record["regel"], "url": record["url"],
            "claim": (f"Volgens het register van overheidsorganisaties (uitgave {self.uitgave}) "
                      f"{ww} {self.orgs[record['oo_id']]['naam']} {rest}."),
        })

    def _bestaan_van(self, ref) -> tuple:
        """(van, tot) van een eindpunt: een organisatie begrenst met het begin en einde uit haar
        OO-record én wat het model al zegt (het strengste van beide; registers_looptijd zet het
        OO-begin op de knoop); een bestaande partij met haar eigen looptijd; een persoon of een
        nieuwe lokale partij zonder datum begrenst niet."""
        soort, w = ref
        if soort == "org":
            o = self.orgs.get(w) or {}
            rec = o.get("record") or {}
            db = self.ent_bestaan.get(self.org_ext.get(w) or o.get("bestaand"), (None, None))
            return looptijd._laatste(rec.get("start"), db[0]), looptijd._vroegste(rec.get("eind"), db[1])
        if soort == "bestaand":
            return self.ent_bestaan.get(w, (None, None))
        return None, None

    def maak(self):
        self.organisaties()
        self.personen()
        klem_relaties(self.relaties, self._bestaan_van, self.bestaan)
        # organisaties zonder enig verband kunnen niet worden goedgekeurd: weglaten
        gebruikt = {r["bron"][1] for r in self.relaties if r["bron"][0] == "org"} | \
                   {r["doel"][1] for r in self.relaties if r["doel"][0] == "org"}
        for oo_id in [k for k in self.orgs if k not in gebruikt and not self.orgs[k]["bestaand"]]:
            self.overgeslagen["organisatie zonder verband"] += 1
            del self.orgs[oo_id]
        self.afkortingen()
        return self

    def afkortingen(self):
        """De afkorting uit het register als metadata.afkorting (eigenaarsbesluit 2026-10-14):
        alleen een echte afkorting die nog niet in de naam van de knoop staat, die de knoop nog
        niet heeft en die met geen andere levende knoop botst (common.afkorting_botst). Twee
        organisaties in deze uitgave met dezelfde afkorting (SBB) krijgen haar geen van beide.
        Zet o['afkorting'] (meesturen) of o['afkorting_overgeslagen'] (reden) en telt."""
        eigen = {i: (n, a) for i, n, a in self.levend}
        kandidaten = {}
        for oo_id, o in self.orgs.items():
            afk = (o["record"].get("afkorting") or "").strip()
            if not afk:
                continue
            eid = self.org_ext.get(oo_id) or o["bestaand"]
            naam = eigen.get(eid, (o["naam"], None))[0]
            if o["oo_type"] == "Gemeente":
                reden = "gemeente (de 'afkorting' is de naam)"
            elif o["oo_type"] == "Provincie":
                reden = "provinciecode (NH, ZH …), geen naam in het nieuws"
            elif eid and eigen.get(eid, (None, None))[1]:
                reden = "heeft al een afkorting"
            else:
                reden = geen_afkorting(afk, naam)
            if reden:
                o["afkorting_overgeslagen"] = reden
                self.afkorting_tel[f"overgeslagen: {reden}"] += 1
                continue
            kandidaten[oo_id] = (afk, eid, naam)
        per_sleutel = Counter(sleutel(a) for a, _, _ in kandidaten.values())
        for oo_id, (afk, eid, naam) in kandidaten.items():
            o = self.orgs[oo_id]
            if per_sleutel[sleutel(afk)] > 1:
                reden = "gedeeld met een andere organisatie in het register"
            elif afkorting_botst(afk, eid, self.levend):
                reden = "botst met een andere knoop"
                o["afkorting_botsing"] = afkorting_botst(afk, eid, self.levend)
            else:
                reden = None
            if reden:
                o["afkorting_overgeslagen"] = reden
                self.afkorting_tel[f"overgeslagen: {reden}"] += 1
                continue
            o["afkorting"] = afk
            self.afkorting_tel["meesturen (bestaande knoop)" if eid else "meesturen (nieuwe knoop)"] += 1

    def samenvatting(self) -> dict:
        return {
            "uitgave": self.uitgave,
            "organisaties": len(self.orgs),
            "organisaties_bestaand": sum(1 for o in self.orgs.values() if o["bestaand"]),
            "per_laag": Counter(o["bestuurslaag"] for o in self.orgs.values()),
            "per_rol_org": Counter(o["rol"] for o in self.orgs.values()),
            "personen": len(self.personen_plan),
            "personen_bestaand": sum(1 for p in self.personen_plan.values() if p["bestaand"]),
            "personen_voorletters": sum(1 for p in self.personen_plan.values() if p["sleutel"].startswith("init:")),
            "per_rol_persoon": Counter(p["rol"] for p in self.personen_plan.values()),
            "relaties": Counter(f"{r['type']}/{r['mechanisme']}" for r in self.relaties),
            "per_functie": Counter(r["functie"] for r in self.relaties if r["type"] == "ambt"),
            "lokale_partijen": len(self.lokale_partijen),
            "overgeslagen": self.overgeslagen,
            "overgeslagen_functies": self.overgeslagen_functies,
            "bestaan": self.bestaan,
            "afkortingen": self.afkorting_tel,
        }


# ── Indienen via REST ───────────────────────────────────────────────────────
class Rest:
    def __init__(self, token: str, api: str = API):
        self.token, self.api = token, api.rstrip("/")

    def __call__(self, methode, pad, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.api + pad, data=data, method=methode)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.token}")
        for poging in range(5):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return r.status, json.loads(r.read().decode() or "{}")
            except urllib.error.HTTPError as e:
                inhoud = json.loads(e.read().decode() or "{}") if e.code != 500 else {"error": "500"}
                if e.code == 429 and poging < 4:
                    time.sleep(30)
                    continue
                return e.code, inhoud
        return 429, {"error": "rate limit"}


class Indiener:
    def __init__(self, plan: Plan, rest: Rest | None, alleen: str | None, log):
        self.p, self.rest, self.alleen, self.log = plan, rest, alleen, log
        self.conn = plan.conn
        self.ext = {(s, w): e for e, s, w in self.conn.execute(
            "SELECT entity_id, stelsel, waarde FROM externe_ids")}
        self.relaties_bestaand = {tuple(r) for r in self.conn.execute(
            "SELECT source_id, target_id, relation_type FROM relations WHERE NOT vervangen "
            "AND status <> 'afgewezen'")}
        self.ent: dict[tuple, int] = {}
        self.tel = Counter()

    def bron(self) -> int | None:
        body = {"title": oo.TITEL.format(uitgave=self.p.uitgave), "source_type": "dataset",
                "publisher": oo.UITGEVER, "date_published": self.p.uitgave, "cluster_key": CLUSTER,
                "location": {"type": "url", "value": oo.URL},
                "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"}
        status, res = self.rest("POST", "/api/sources", body)
        if status not in (200, 201):
            raise SystemExit(f"bron registreren faalde: {status} {res}")
        return res["id"]

    def organisaties(self):
        for o in self.p.orgs.values():
            ids = [{"stelsel": "oo", "waarde": o["oo_id"]}] + (
                [{"stelsel": "tooi", "waarde": o["tooi"]}] if o["tooi"] else [])
            eid = self.ext.get(("oo", o["oo_id"])) or o["bestaand"]
            if eid:
                body = {
                    "externe_ids": ids, "bestuurslaag": o["bestuurslaag"],
                    "metadata": {"oo_type": o["oo_type"]},
                    # de rol die de registersoort geeft (een ministerie → departement), naast
                    # wat de organisatie al was; de server vult alleen aan
                    "rollen": [o["rol"]]}
                if o.get("afkorting"):
                    body["afkorting"] = o["afkorting"]
                status, res = self.rest("POST", f"/api/entities/{eid}/register", body)
                self.tel["org gekoppeld" if status == 200 else f"org koppelen {status}"] += 1
                self._tel_afkorting(o, status, res)
                if status == 409:
                    self.log(f"  ! externe id al bezet: {o['naam']}: {res}")
            else:
                body = {"name": o["naam"], "type": o["type"], "primary_role_id": self.p.rol[o["rol"]],
                        "description": (o["beschrijving"] or f"{o['oo_type']} (register van overheidsorganisaties)"),
                        "bestuurslaag": o["bestuurslaag"], "metadata": {"oo_type": o["oo_type"]},
                        "externe_ids": ids}
                if o["start"]:
                    body["active_from"] = o["start"]
                if o.get("afkorting"):
                    body["metadata"]["afkorting"] = o["afkorting"]
                status, res = self.rest("POST", "/api/entities", body)
                if status == 201:
                    eid = res["id"]
                    self.tel["org nieuw"] += 1
                    self._tel_afkorting(o, status, res)
                elif status == 409:
                    eid = res.get("entity_id")
                    self.tel["org bestond (externe id)"] += 1
                else:
                    self.tel[f"org fout {status}"] += 1
                    self.log(f"  ✗ {o['naam']}: {status} {res.get('error')}")
                    continue
            self.ent[("org", o["oo_id"])] = eid

    def _tel_afkorting(self, o: dict, status: int, res: dict):
        if not o.get("afkorting") or status not in (200, 201):
            return
        reden = (res.get("overgeslagen") or res.get("afkorting_overgeslagen") or {})
        reden = reden.get("afkorting") if isinstance(reden, dict) else reden
        if reden:
            self.tel["afkorting overgeslagen (server)"] += 1
            self.log(f"  · afkorting {o['afkorting']} niet bij {o['naam']}: {reden}")
        elif status == 201 or "afkorting" in (res.get("gewijzigd") or {}).get("metadata", {}):
            self.tel["afkorting gezet"] += 1

    def personen(self):
        for p in self.p.personen_plan.values():
            # alle registernummers van deze persoon (één per functie): de registercheck
            # herleidt elk ambt via het nummer van díe functie
            ids = [{"stelsel": "oo", "waarde": f"m:{m}"} for m in p["oo_medewerkers"]]
            if p.get("qid"):
                ids.append({"stelsel": "wikidata", "waarde": p["qid"]})
            eid = next((self.ext[("oo", f"m:{m}")] for m in p["oo_medewerkers"]
                        if ("oo", f"m:{m}") in self.ext), None) or p["bestaand"]
            if eid:
                status, _ = self.rest("POST", f"/api/entities/{eid}/register", {"externe_ids": ids})
                self.tel["persoon gekoppeld" if status == 200 else f"persoon koppelen {status}"] += 1
            else:
                status, res = self.rest("POST", "/api/entities", {
                    "name": p["naam"], "type": "persoon", "primary_role_id": self.p.rol[p["rol"]],
                    "description": p["beschrijving"], "externe_ids": ids})
                if status == 201:
                    eid = res["id"]
                    self.tel["persoon nieuw"] += 1
                elif status == 409:
                    eid = res.get("entity_id")
                    self.tel["persoon bestond (externe id)"] += 1
                else:
                    self.tel[f"persoon fout {status}"] += 1
                    self.log(f"  ✗ {p['naam']}: {status} {res.get('error')}")
                    continue
            self.ent[("persoon", p["sleutel"])] = eid
        self.partijen()

    def partijen(self):
        """Lokale en provinciale partijen (2026-10-13): een nieuwe partijknoop per naam."""
        for k, lp in self.p.lokale_partijen.items():
            if ("partij", k) in self.ent:
                continue
            status, res = self.rest("POST", "/api/entities", {
                "name": lp["naam"], "type": "partij", "primary_role_id": self.p.rol["partij"],
                "description": lp["beschrijving"], "bestuurslaag": lp["bestuurslaag"]})
            if status == 201:
                self.ent[("partij", k)] = res["id"]
                self.tel["partij nieuw"] += 1
            else:
                self.tel[f"partij fout {status}"] += 1
                self.log(f"  ✗ {lp['naam']}: {status} {res.get('error')}")

    def _id(self, ref):
        soort, waarde = ref
        return waarde if soort == "bestaand" else self.ent.get((soort, waarde))

    def relaties(self, bron_id: int):
        for r in self.p.relaties:
            if self.alleen == "organisaties" and "persoon" in (r["bron"][0], r["doel"][0]):
                continue
            if self.alleen == "personen" and r["bron"][0] == "org" and r["doel"][0] == "org":
                continue
            s, t = self._id(r["bron"]), self._id(r["doel"])
            if not s or not t:
                self.tel["relatie zonder eindpunt"] += 1
                continue
            if (s, t, r["type"]) in self.relaties_bestaand:
                self.tel["relatie bestond"] += 1
                continue
            body = {"source_id": s, "target_id": t, "relation_type": r["type"],
                    "mechanism_id": self.p.mech[r["mechanisme"]]}
            if r["functie"]:
                body["functie"] = r["functie"]
            if r["start"]:
                body["active_from"] = r["start"]
            if r.get("eind"):
                body["active_until"] = r["eind"]
            status, res = self.rest("POST", "/api/relations", body)
            if status != 201:
                self.tel[f"relatie fout {status}"] += 1
                self.log(f"  ✗ relatie {r['type']} {s}→{t}: {status} {res.get('error')}")
                continue
            self.relaties_bestaand.add((s, t, r["type"]))
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": res["id"], "claim": r["claim"], "stance": "supporting",
                "citations": [{"source_id": bron_id, "quote": r["regel"],
                               "methode": "officieel_register_scrape", "section": r["sleutel"],
                               "page": f"{oo.BRON}/{self.p.uitgave}", "context": r["url"]}]})
            self.tel["relatie nieuw" if status == 201 else f"argument fout {status}"] += 1
            if status != 201:
                self.log(f"  ✗ argument {r['type']} {s}→{t}: {status} {res.get('error')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave", help="YYYY-MM-DD; standaard de nieuwste bewaarde uitgave")
    ap.add_argument("--indienen", action="store_true", help="echt indienen (standaard: droogloop)")
    ap.add_argument("--alleen", choices=["organisaties", "personen"])
    ap.add_argument("--plan-json", type=Path)
    a = ap.parse_args()
    pad = oo.pad_van(a.uitgave) if a.uitgave else oo.uitgaven()[-1]
    data = oo.lees(pad)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    plan = Plan(data, conn).maak()
    s = plan.samenvatting()
    print(json.dumps(s, ensure_ascii=False, indent=1, default=dict))
    if a.plan_json:
        a.plan_json.write_text(json.dumps({
            "samenvatting": s,
            "organisaties": [{k: v for k, v in o.items() if k != "record"} for o in plan.orgs.values()],
            "personen": list(plan.personen_plan.values()), "relaties": plan.relaties},
            ensure_ascii=False, indent=1, default=dict))
    if not a.indienen:
        print("\n(droogloop — niets ingediend. --indienen schrijft via de REST-API.)")
        return
    if not TOKEN.exists():
        sys.exit(f"Token ontbreekt: {TOKEN}")
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()), a.alleen, print)
    bron_id = ind.bron()
    if a.alleen != "personen":
        ind.organisaties()
    else:
        ind.organisaties()  # id's nodig voor de ambten; koppelen is idempotent
    if a.alleen != "organisaties":
        ind.personen()
    ind.relaties(bron_id)
    print(json.dumps(ind.tel, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
