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
    Raadsleden niet. Kamerleden van de Tweede Kamer komen uit de Tweede Kamer-API (tk.py).

Koppelen (nooit op naam alleen):
  - organisaties: eerst externe_ids (oo/tooi), dan koppelingen.json (ingecheckt, met de hand
    nagelopen), anders nieuw;
  - organisaties die al bestonden krijgen ook de rol die de registersoort geeft (een ministerie
    → departement), naast wat ze al waren;
  - personen: een volledige naam die exact gelijk is aan een bestaande persoon met een
    passende rol, of met al een verband met dezelfde organisatie, wordt gekoppeld; anders een
    nieuwe knoop. Een titel achter de naam ("MPM", "MSc") telt niet mee. Een naam met alleen
    voorletters krijgt altijd een toevoeging ("B.C.M. Vostermans (burgemeester Peel en Maas)").

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
from common import ROOT, ontleed_naam, partij_naam, sleutel  # noqa: E402

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
            "elite_forum", "bewindspersoon", "topambtenaar", "lokale_bestuurder", "politicus")
MECHNAMEN = ("hierarchische_aansturing", "verzelfstandigd_bestuur", "institutioneel_advies",
             "ministeriele_verantwoordelijkheid", "ambtelijke_leiding", "lokaal_bestuursmandaat",
             "kamerzetel", "partijlijn")
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
            return None
        if t == "Provincie":
            if fn == "commissaris van de koning":
                return ("lokale_bestuurder", "lokaal_bestuursmandaat", "Commissaris van de Koning")
            return None
        if t == "Waterschap":
            if fn in ("dijkgraaf", "watergraaf"):
                return ("lokale_bestuurder", "lokaal_bestuursmandaat", f["functie"])
            return None
        if org["naam"] == "Eerste Kamer der Staten-Generaal":
            if fn.startswith("kamerlid"):
                return ("politicus", "kamerzetel", f["functie"])
            return None
        if org["naam"] == "Raad van State":
            if fn == "vice-president":
                return ("topambtenaar", "ambtelijke_leiding", "Vice-president")
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
        if fn in hoofd:
            return ("topambtenaar", "ambtelijke_leiding", f["functie"].replace("*", "").strip())
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
                for voorkeur in ("vice-president", "president", "nationale ombudsman",
                                 "inspecteur-generaal", "directeur-generaal", "korpschef",
                                 "nationaal coördinator terrorismebestrijding en veiligheid",
                                 "voorzitter", "bestuursvoorzitter", "president en voorzitter",
                                 "directeur-bestuurder", "algemeen directeur", "hoofdinspecteur",
                                 "directeur"):
                    if voorkeur in gekozen:
                        gekozen = {voorkeur: gekozen[voorkeur][:2]}
                        break
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
        if naam["alleen_achternaam"] or not naam["achternaam"]:
            self.overgeslagen["alleen achternaam"] += 1
            return
        plaats = re.sub(r"^(Gemeente|Provincie) ", "", org["naam"]).replace(
            " der Staten-Generaal", "")
        functie_kort = titel.split(",")[0].strip().lower()
        if naam["volledig"]:
            weergave = naam["weergave"]
            sleutel_p = f"vol:{sleutel(weergave)}"
        else:
            weergave = f"{naam['weergave']} ({functie_kort} {plaats})"
            sleutel_p = f"init:{sleutel(weergave)}"
        p = self.personen_plan.get(sleutel_p)
        if p is None:
            bestaand = self.koppel_personen.get(f["naam_register"])
            if bestaand:
                pass
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
            p = {"sleutel": sleutel_p, "naam": weergave, "rol": rol, "bestaand": bestaand,
                 "register_naam": f["naam_register"], "oo_medewerker": f["sleutel"].split(":")[-1],
                 "beschrijving": f"{titel} bij {org['naam']} (register van overheidsorganisaties)"}
            self.personen_plan[sleutel_p] = p
        medewerker = f["sleutel"].split(":")[-1]
        if medewerker not in p.setdefault("oo_medewerkers", []):
            p["oo_medewerkers"].append(medewerker)
        self.relaties.append({
            "bron": ("persoon", sleutel_p), "doel": ("org", org["oo_id"]), "type": "ambt",
            "mechanisme": mech, "functie": titel, "start": f["start"], "sleutel": f["sleutel"],
            "regel": f["regel"], "url": org["url"],
            "claim": (f"Volgens het register van overheidsorganisaties (uitgave {self.uitgave}) is "
                      f"{naam['weergave']} {kleine(titel)} bij {bij(org['naam'])}"
                      f"{' (sinds ' + f['start'] + ')' if f['start'] else ''}."),
        })
        partij = f.get("partij") or self._fractie(f)
        if partij:
            pid = self.partij_id.get(partij_naam(partij) or "")
            if pid:
                self.relaties.append({
                    "bron": ("bestaand", pid), "doel": ("persoon", sleutel_p), "type": "lidmaatschap",
                    # Een Eerste Kamerfractie begint met de zetel; bij een burgemeester of
                    # wethouder noemt het register geen begin van het partijlidmaatschap
                    "mechanisme": "partijlijn", "functie": None,
                    "start": f["start"] if "Fracties EK" in f["org_pad"] else None,
                    "sleutel": f["sleutel"],
                    "regel": f["regel"], "url": org["url"],
                    "claim": (f"Volgens het register van overheidsorganisaties (uitgave {self.uitgave}) "
                              + (f"is {naam['weergave']} lid van de Eerste Kamerfractie van {partij}."
                                 if "Fracties EK" in f["org_pad"] else
                                 f"is {naam['weergave']}, {kleine(titel)} bij {bij(org['naam'])}, "
                                 f"lid van {partij}.")),
                })
            else:
                self.overgeslagen["partij niet landelijk of onbekend"] += 1

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

    def maak(self):
        self.organisaties()
        self.personen()
        # organisaties zonder enig verband kunnen niet worden goedgekeurd: weglaten
        gebruikt = {r["bron"][1] for r in self.relaties if r["bron"][0] == "org"} | \
                   {r["doel"][1] for r in self.relaties if r["doel"][0] == "org"}
        for oo_id in [k for k in self.orgs if k not in gebruikt and not self.orgs[k]["bestaand"]]:
            self.overgeslagen["organisatie zonder verband"] += 1
            del self.orgs[oo_id]
        return self

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
            "overgeslagen": self.overgeslagen,
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
                status, res = self.rest("POST", f"/api/entities/{eid}/register", {
                    "externe_ids": ids, "bestuurslaag": o["bestuurslaag"],
                    "metadata": {"oo_type": o["oo_type"]},
                    # de rol die de registersoort geeft (een ministerie → departement), naast
                    # wat de organisatie al was; de server vult alleen aan
                    "rollen": [o["rol"]]})
                self.tel["org gekoppeld" if status == 200 else f"org koppelen {status}"] += 1
                if status == 409:
                    self.log(f"  ! externe id al bezet: {o['naam']}: {res}")
            else:
                body = {"name": o["naam"], "type": o["type"], "primary_role_id": self.p.rol[o["rol"]],
                        "description": (o["beschrijving"] or f"{o['oo_type']} (register van overheidsorganisaties)"),
                        "bestuurslaag": o["bestuurslaag"], "metadata": {"oo_type": o["oo_type"]},
                        "externe_ids": ids}
                if o["start"]:
                    body["active_from"] = o["start"]
                status, res = self.rest("POST", "/api/entities", body)
                if status == 201:
                    eid = res["id"]
                    self.tel["org nieuw"] += 1
                elif status == 409:
                    eid = res.get("entity_id")
                    self.tel["org bestond (externe id)"] += 1
                else:
                    self.tel[f"org fout {status}"] += 1
                    self.log(f"  ✗ {o['naam']}: {status} {res.get('error')}")
                    continue
            self.ent[("org", o["oo_id"])] = eid

    def personen(self):
        for p in self.p.personen_plan.values():
            # alle registernummers van deze persoon (één per functie): de registercheck
            # herleidt elk ambt via het nummer van díe functie
            ids = [{"stelsel": "oo", "waarde": f"m:{m}"} for m in p["oo_medewerkers"]]
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
