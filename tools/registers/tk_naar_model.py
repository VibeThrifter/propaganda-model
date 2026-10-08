#!/usr/bin/env python3
"""Tweede Kamer (open data) → het model (Uitbreiding C, eigenaarsbesluit 2026-10-07).

Trap 3c (tk.py leest de uitgave): de zittende Kamerleden met hun ambt en fractie, en als belangen
en werving hun lopende nevenfuncties, hun loopbaan (draaideur), reizen die derden betaalden en
geschenken. Alles via de REST-API onder `register-import`; elk feit krijgt als citaat de
letterlijke recordregel uit de bewaarde uitgave, zodat scripts/registercheck.py het controleert.

Koppelen, nooit op naam alleen:
  - Kamerleden: eerst de externe id (tk_persoon), dan koppelingen.json ('tk_personen'), dan de
    volledige naam (ook zonder toevoeging als '(D66)', of met één deel van een dubbele
    achternaam) bij precies één bestaande persoon met een passende rol. Anders een nieuwe persoon;
    is de naam al van iemand anders, dan met '(Tweede Kamerlid)' erachter.
  - Organisaties alleen onder hun naam in het model (de registercheck zoekt die naam in de regel):
      werkgever en betaler (een naamveld): de exacte naam, of een bestaande naam als begin
        ('Rabobank Nederland' → Rabobank); anders nieuw als de rechtsvorm in de naam staat
        (Stichting, Vereniging, Coöperatie, B.V., N.V., Universiteit, Hogeschool);
      nevenfunctie (functie + organisatie in één zin): eerst functiewoorden ('Lid Raad van
        Toezicht', 'Penningmeester van het'), de rest moet de organisatie zijn. Zo wordt
        'Voorzitter Vrienden van het Rijksmuseum' niet het Rijksmuseum;
      geschenk: alleen een bestaande organisatie die als gever genoemd is ('ontvangen … van',
        'op uitnodiging van').
    Partijen, partij-eigen stichtingen en fracties, de Kamer zelf en de overheid als betaler van
    een reis tellen niet; politieke ambten in de loopbaan ook niet (dat is geen draaideur).
Wat niet te plaatsen is, staat met reden in data/registers/tk/overgeslagen_<uitgave>.json; elke
koppeling staat ter controle in data/registers/tk/koppelingen_<uitgave>.json.

Gebruik:
    python3 tools/registers/tk_naar_model.py                 # droogloop
    python3 tools/registers/tk_naar_model.py --indienen
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import naar_model  # noqa: E402
import oo  # noqa: E402
import tk  # noqa: E402
from common import PARTIJEN, ROOT, namen_van, partij_naam, schoon, sleutel  # noqa: E402
from naar_model import PASSENDE_ROLLEN, TOKEN, Rest  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
KOPPELINGEN = HIER / "koppelingen.json"
CLUSTER = "register:tk"
TWEEDE_KAMER_OO = "19432"
MECHNAMEN = ("kamerzetel", "partijlijn", "draaideurconstructie", "nevenfunctie_verstrengeling",
             "geschenk_en_gastvrijheid")
ROLNAMEN = ("politicus", "maatschappelijke_organisatie", "belanghebbende", "kennisinstituut")
LOKAAL = {"gemeente", "provincie", "waterschap"}
OVERHEID_TYPES = {"overheidsinstelling", "rechterlijke_macht", "toezichthouder"}

# Rechtsvorm in de naam → (type, rol). Alleen dan komt een onbekende organisatie erbij.
RECHTSVORMEN = [
    (re.compile(r"(?:^|\s)(?:B\.?V\.?|N\.?V\.?|SE)$|(?:^|\s)U\.?A\.?$|^Co[öo]peratie(ve)?\b", re.I),
     "bedrijf", "belanghebbende"),
    (re.compile(r"\b(?:Rijks)?[Uu]niversiteit\b|\bHogeschool\b"), "onderwijsinstelling", "kennisinstituut"),
    (re.compile(r"^(?:Koninklijke\s+)?Vereniging\b", re.I), "ngo", "maatschappelijke_organisatie"),
    (re.compile(r"^Stichting\b|\sStichting$", re.I), "stichting", "maatschappelijke_organisatie"),
]
UITSLUITEN = re.compile(r"fractie|ondersteuning|Tweede Kamer|Eerste Kamer|Staten[- ]Generaal|"
                        r"eigen (rekening|kosten)|privé|\bprive\b|\bzelf\b|partijbureau", re.I)
# Partij-eigen (jongerenclubs, bestuurdersverenigingen …): elke partijnaam of -afkorting als heel woord
PARTIJ_WOORDEN = set(PARTIJEN) | {"cdja", "jovd", "jonge democraten", "dwars", "pink",
                                  "jonge socialisten", "perspectief", "sgpj", "groen links"}

# Functiewoorden vooraan een nevenfunctie ('Lid Raad van Toezicht …'), per soort verband.
AMBT_W = {"raadslid", "gemeenteraadslid", "statenlid"}
EIGENDOM_W = {"eigenaar", "medeeigenaar", "dga", "aandeelhouder"}
PERSONEEL_W = {"terugkeerregeling", "docent", "gastdocent", "hoogleraar", "medewerker"}
ADVIES_W = {"advies", "adviseur", "adviesraad", "adviescommissie", "advisory"}
BESTUUR_W = {"voorzitter", "vicevoorzitter", "bestuurslid", "bestuurder", "bestuur", "stichtingsbestuur",
             "penningmeester", "secretaris", "toezicht", "commissaris", "commissarissen",
             "toezichthouder", "directeur", "directie", "curatorium", "curator", "trustee", "chair",
             "chairman", "chairwoman", "president", "oprichter", "medeoprichter", "board"}
LID_W = {"lid", "leden", "erelid", "member", "comite", "aanbeveling", "ambassadeur", "beschermheer",
         "beschermvrouwe", "coach", "mentor", "vrijwilliger"}
BIJWOORDEN = {"raad", "dagelijks", "algemeen", "onafhankelijk", "plaatsvervangend", "plv", "waarnemend",
              "vice", "mede", "co", "extern", "externe", "intern", "interne", "onbezoldigd", "bezoldigd",
              "honorair", "bijzonder", "of", "the", "van", "de", "het", "der", "den", "des", "bij", "en",
              "namens", "voor", "a", "an", "in"}
FUNCTIEWOORDEN = AMBT_W | EIGENDOM_W | PERSONEEL_W | ADVIES_W | BESTUUR_W | LID_W
POLITIEK_AMBT = re.compile(
    r"\b(wethouder|burgemeester|gedeputeerde|(gemeente)?raadslid|statenlid|minister|staatssecretaris|"
    r"kamerlid|senator|europarlementari|lijsttrekker|fractievoorzitter|dijkgraaf|heemraad|"
    r"lid (van (de|het) )?(tweede kamer|eerste kamer|gemeenteraad|provinciale staten|europees parlement|"
    r"algemeen bestuur)|commissaris van de koning)", re.I)
BESTUUR_FUNCTIE = re.compile(r"\b(voorzitter|bestuurder|bestuurslid|(dagelijks |hoofd)?bestuur|directeur|ceo|cfo|"
                             r"coo|cto|commissaris|toezichthouder|penningmeester|(?<!ambtelijk )secretaris|"
                             r"raad van (bestuur|toezicht|commissarissen))\b", re.I)
ADVIES_FUNCTIE = re.compile(r"\b(klankbord\w*|raad van advies|adviesraad|advisory board|adviescommissie)\b", re.I)
EIGENDOM_FUNCTIE = re.compile(r"eigenaar|aandeelhouder|\bdga\b", re.I)
LEIDING = re.compile(r"\b(eigenaar|oprichter|partner|management ?team)\b", re.I)  # mét bestuur/advies
GEVER = re.compile(r"^(?:ontvangen|gekregen)\b.*?\bvan\s+|\buitnodiging\s+van\s+|\baangeboden\s+door\s+|"
                   r"\bgeschonken\s+door\s+|\bnamens\s+", re.I)
GEVER_STOP = {"een", "twee", "drie", "vier", "het", "de", "ter", "tijdens", "als", "na", "n.a.v.", "bij", "voor",
              "met", "op", "in", "aan", "om", "uit", "namens", "ivm", "i.v.m.", "en", "die", "dat", "waarde"}
# Woorden die naast een naam van één woord mogen staan ('Rabobank Nederland', 'Coöperatieve Rabobank')
KWALIFICATIES = {"nederland", "nl", "netherlands", "the", "group", "groep", "holding", "holdings", "bank", "b", "v",
                 "n", "u", "a", "bv", "nv", "ua", "cooperatieve", "cooperatie", "international", "internationaal",
                 "europe", "benelux", "advocatenkantoor", "advocaten", "nederlandse", "de", "het"}
GENERIEK = {"vereniging van eigenaren", "vve", "stichting", "vereniging", "cooperatie"}
TE_PLAATS = re.compile(r",?\s+(?:gevestigd\s+)?te\s+[A-Z][\w'\- ]*$")


def rechtsvorm(naam: str) -> tuple[str, str] | None:
    for patroon, typ, rol in RECHTSVORMEN:
        if patroon.search(naam):
            if typ == "onderwijsinstelling" and not re.match(
                    r"^(?:[A-Z][\w-]*\s+)?(?:Rijks)?(?:[Uu]niversiteit|Hogeschool)\b", naam):
                return None  # 'Bestuurskunde Radboud Universiteit': een onderdeel, niet de instelling
            return typ, rol
    return None


def zonder_haakjes(tekst: str) -> str:
    return schoon(re.sub(r"\([^)]*\)?", " ", tekst or ""))


def _eind(tekst: str) -> str:
    """Leestekens aan het eind weg, behalve de punt van 'B.V.' of 'K.O.E.'."""
    tekst = tekst.strip(" ,;:")
    if tekst.endswith(".") and not re.search(r"(?:\b[A-Za-z]\.)+$", tekst):
        tekst = tekst[:-1].rstrip(" ,;:")
    return tekst


def _zonder_lidwoord(s: str) -> str:
    return re.sub(r"^(de|het|the)\s+", "", s)


def _functie_tekst(functie: str) -> str:
    """'Bedrijfsjurist' → 'bedrijfsjurist'; afkortingen ('CEO') blijven staan."""
    return functie if len(functie) > 1 and functie[1].isupper() else functie[:1].lower() + functie[1:]


def _datum(waarde: str | None) -> str | None:
    """'2010-10' / '2018' / '2010-03-01' → zo; anders None."""
    return waarde if waarde and re.match(r"^\d{4}(-\d{2})?(-\d{2})?$", waarde) else None


class Plan:
    def __init__(self, data: dict, conn: sqlite3.Connection, koppelingen: dict | None = None):
        self.d, self.conn, self.uitgave = data, conn, data["uitgave"]
        self.mech = self._ids("mechanisms", MECHNAMEN)
        self.rol = self._ids("roles", ROLNAMEN)
        rij = conn.execute("SELECT entity_id FROM externe_ids WHERE stelsel = 'oo' AND waarde = ?",
                           (TWEEDE_KAMER_OO,)).fetchone()
        if not rij:
            raise SystemExit("De Tweede Kamer heeft nog geen externe id oo:19432 — eerst naar_model.py (oo)")
        self.tweede_kamer = rij[0]
        self.partij_id = {n: i for i, n in conn.execute(
            "SELECT id, name FROM entities WHERE type = 'partij' AND status = 'goedgekeurd' AND NOT vervangen")}
        # organisaties onder hun naam in het model. Een sleutel van twee organisaties telt niet; een
        # naam gaat voor een afkorting tussen haakjes ('SBS6' tegenover 'Nieuws van de Dag (SBS6)').
        self.org: dict[int, tuple[str, str, str | None]] = {}
        sterk: dict[str, set[int]] = {}
        zwak: dict[str, set[int]] = {}
        for i, n, t, laag in conn.execute(
                "SELECT id, name, type, bestuurslaag FROM entities WHERE type <> 'persoon' "
                "AND NOT vervangen AND status <> 'afgewezen'"):
            self.org[i] = (n, t, laag)
            namen = namen_van(n)
            hoofd = {sleutel(n), sleutel(zonder_haakjes(n))}
            for k in namen:
                (sterk if k in hoofd else zwak).setdefault(k, set()).add(i)
        self.org_index = {k: next(iter(v)) for k, v in zwak.items() if len(v) == 1 and k not in sterk}
        self.org_index.update({k: next(iter(v)) for k, v in sterk.items() if len(v) == 1})
        # Overheidsorganisaties die wel in het register van overheidsorganisaties staan maar nog niet in
        # het model (zoals vijf provincies waarvan het register geen ambtsdrager noemt): onder dezelfde
        # naam en met dezelfde rol als naar_model.py ze zou geven, met hun externe id. Ze komen er
        # alleen bij als een Kamerfeit ze nodig heeft (negatieve sleutel tot ze bestaan).
        self.oo_orgs: dict[int, dict] = {}
        self._register_orgs(conn, sterk)
        self.op_eerste_woord: dict[str, list[tuple[list[str], int]]] = {}
        for k, eid in self.org_index.items():
            if len(k) >= 3:
                self.op_eerste_woord.setdefault(k.split()[0], []).append((k.split(), eid))
        # plaatsnamen ('Rabobank Horst-Venray'); korte woorden uit 'Alphen aan den Rijn' tellen niet
        self.plaatsen = {w for n, t, laag in self.org.values() if laag in ("gemeente", "provincie")
                         for w in sleutel(re.sub(r"^(Gemeente|Provincie)\s+", "", zonder_haakjes(n))).split()
                         if len(w) >= 4}
        self.kwalificaties = KWALIFICATIES | self.plaatsen
        self.schrijfwijzen = {sleutel(k): v for k, v in tk.schrijfwijzen().items()}
        self.partij_woorden = PARTIJ_WOORDEN | {k for n, t, _ in self.org.values() if t == "partij"
                                                for k in namen_van(n)}
        self.pm_personen: dict[str, list[tuple[int, str, str | None]]] = {}
        for i, n, rol in conn.execute("""
                SELECT e.id, e.name, r.name FROM entities e LEFT JOIN roles r ON r.id = e.primary_role_id
                WHERE e.type = 'persoon' AND NOT e.vervangen AND e.status <> 'afgewezen'"""):
            for k in {sleutel(n), sleutel(zonder_haakjes(n))}:
                self.pm_personen.setdefault(k, []).append((i, n, rol))
        self.ext_tk = {w: e for e, w in conn.execute(
            "SELECT entity_id, waarde FROM externe_ids WHERE stelsel = 'tk_persoon'")}
        self.handmatig = {k: v for k, v in (koppelingen or {}).get("tk_personen", {}).items()
                          if not k.startswith("_")}
        self.alle_namen = {sleutel(n) for (n,) in conn.execute("SELECT name FROM entities")}
        self.personen: dict[str, dict] = {}
        self.nieuwe_orgs: dict[str, dict] = {}
        self.relaties: list[dict] = []
        self.paren: set[tuple] = set()
        self.koppelingen: list[dict] = []
        self.overgeslagen: list[dict] = []
        self.tel = Counter()

    def _register_orgs(self, conn, sterk):
        if not oo.uitgaven():
            return
        oo_data = oo.lees_uitgave(oo.uitgaven()[-1].stem.split("_", 1)[1])
        np = naar_model.Plan(oo_data, conn)
        bekend = {w for (w,) in conn.execute("SELECT waarde FROM externe_ids WHERE stelsel = 'oo'")}
        rollen = {n: i for n, i in conn.execute("SELECT name, id FROM roles WHERE NOT vervangen")}
        for o in oo_data["organisaties"].values():
            if o["oo_id"] in bekend or np._gekozen(o) != "top":
                continue
            naam = np._naam_org(o)
            if sleutel(naam) in sterk or sleutel(naam) in self.org_index or np._rol_org(o, "top") not in rollen:
                continue
            eid = -(len(self.oo_orgs) + 1)
            typ = "rechterlijke_macht" if o["types"][0] == "Rechtspraak" else "overheidsinstelling"
            self.oo_orgs[eid] = {"naam": naam, "type": typ, "rol_id": rollen[np._rol_org(o, "top")],
                                 "bestuurslaag": o["bestuurslaag"] or "rijk", "oo_type": o["types"][0],
                                 "oo_id": o["oo_id"], "tooi": o["tooi"], "start": o["start"],
                                 "beschrijving": o["beschrijving"] or f"{o['types'][0]} (register van overheidsorganisaties)"}
            self.org[eid] = (naam, typ, o["bestuurslaag"] or "rijk")
            self.org_index.setdefault(sleutel(naam), eid)

    def _ids(self, tabel, namen):
        ids = {n: i for n, i in self.conn.execute(
            f"SELECT name, id FROM {tabel} WHERE NOT vervangen AND name IN ({','.join('?' * len(namen))})",  # noqa: S608
            namen)}
        if set(namen) - set(ids):
            raise SystemExit(f"Theorie ontbreekt nog ({tabel}): {sorted(set(namen) - set(ids))}")
        return ids

    # ── organisaties ───────────────────────────────────────────────────────
    def _partij_eigen(self, naam: str) -> bool:
        t = f" {sleutel(naam)} "
        return any(f" {k} " in t for k in self.partij_woorden if len(k) >= 2)

    def _bestaand(self, naam: str, ruim: bool) -> tuple[int, str] | None:
        """Exacte naam (of een vastgelegde schrijfwijze); ruim ook: een bestaande naam van twee of
        meer woorden waarmee de tekst begint ('Ministerie van X, DG Y'), of een bestaande naam met
        alleen kwalificaties eromheen ('Rabobank Nederland', 'Coöperatieve Rabobank', 'ABN AMRO Bank
        N.V.'). De langste naam wint."""
        naam = self.schrijfwijzen.get(sleutel(naam), naam)
        s = _zonder_lidwoord(sleutel(naam))
        for k in (s, sleutel(naam), f"de {s}", f"het {s}"):
            if k in self.org_index:
                return self.org_index[k], "exact"
        if not ruim:
            return None
        woorden, beste = s.split(), None
        for i, w in enumerate(woorden):
            for kw, eid in self.op_eerste_woord.get(w, []):
                if woorden[i:i + len(kw)] != kw:
                    continue
                rest = woorden[:i] + woorden[i + len(kw):]
                if (i == 0 and len(kw) >= 2) or all(r in self.kwalificaties for r in rest):
                    if beste is None or len(kw) > len(beste[0]):
                        beste = (kw, eid, "begin" if i == 0 and rest else "rond")
        return (beste[1], beste[2]) if beste else None

    def _toegestaan(self, eid: int, context: str) -> str | None:
        """None = mag; anders de reden waarom niet."""
        naam, typ, laag = self.org[eid]
        if typ == "partij" or self._partij_eigen(naam):
            return "partij"
        if eid == self.tweede_kamer:
            return "de Kamer zelf"
        if context == "reis" and (laag or typ in OVERHEID_TYPES):
            return "overheid betaalt"
        return None

    def _schoon_naam(self, naam: str) -> str:
        """'Stichting Ons Medisch Centrum te Oss.' → 'Stichting Ons Medisch Centrum'; ook ', Rotterdam'
        en ' in Rotterdam' als dat een bekende plaats is."""
        naam = _eind(zonder_haakjes(naam))
        naam = _eind(TE_PLAATS.sub("", naam))
        m = re.search(r"(?:,|\s+in)\s+([A-Z][\w'\-]*(?:\s+[A-Z][\w'\-]*)?)$", naam)
        if m and all(w in self.plaatsen for w in sleutel(m.group(1)).split()):
            naam = _eind(naam[:m.start()])
        return naam

    def _naamveld(self, naam: str, context: str, rec: dict, nieuw_mag: bool = True) -> tuple | None:
        """Werkgever of betaler → ('bestaand', id) | ('nieuw', sleutel) | None (gelogd)."""
        naam = self._schoon_naam(naam)
        if not naam or UITSLUITEN.search(naam):
            return self._mis(context, rec, "uitgesloten of leeg")
        for kand in [naam] + ([naam.split(",")[0].strip()] if "," in naam else []):
            gevonden = self._bestaand(kand, ruim=True)
            if gevonden:
                reden = self._toegestaan(gevonden[0], context)
                if reden:
                    return self._mis(context, rec, reden)
                return self._gekoppeld(rec, gevonden[0], gevonden[1], kand)
        if not nieuw_mag:
            return self._mis(context, rec, "onbekend; geen leidende functie")
        return self._nieuw(naam, context, rec)

    def _nieuw(self, naam: str, context: str, rec: dict) -> tuple | None:
        naam = self.schrijfwijzen.get(sleutel(naam), naam)
        vorm = rechtsvorm(naam)
        if not vorm or len(naam.split()) < 2:
            return self._mis(context, rec, "onbekend en geen rechtsvorm")
        if self._partij_eigen(naam):
            return self._mis(context, rec, "partij")
        k = re.sub(r"\s+(b v|n v|bv|nv|u a|ua)$", "", _zonder_lidwoord(sleutel(naam)))
        if k in GENERIEK:
            return self._mis(context, rec, "geen eigen naam")
        naam = re.sub(r"^(De|Het|The)\s+(?=(Stichting|Vereniging|Co[öo]peratie|Koninklijke)\b)", "", naam)
        naam = naam[:1].upper() + naam[1:]
        bron = {"nevenfunctie": "register van nevenactiviteiten", "loopbaan": "loopbaanoverzicht",
                "reis": "reizenregister", "lobby": "lobbyistenregister"}.get(context, "register")
        bestaand = self.nieuwe_orgs.get(k)
        if bestaand is None or sum(c.isupper() for c in naam) > sum(c.isupper() for c in bestaand["naam"]):
            self.nieuwe_orgs[k] = {"naam": naam, "type": vorm[0], "rol": vorm[1],
                                   "beschrijving": f"Genoemd in het {bron} van de Tweede Kamer."}
        self.koppelingen.append({"soort": context, "tekst": rec["regel"], "nieuw": naam, "type": vorm[0]})
        return ("nieuw", k)

    def _gekoppeld(self, rec, eid, hoe, gevonden_in):
        self.koppelingen.append({"soort": rec["soort"], "tekst": rec["regel"], "model": self.org[eid][0],
                                 "id": eid, "hoe": hoe if eid > 0 else f"{hoe}, register (nieuw)",
                                 "uit": gevonden_in})
        return ("bestaand", eid) if eid > 0 else ("oo", eid)

    def _mis(self, context, rec, reden):
        self.overgeslagen.append({"soort": context, "reden": reden, "tekst": rec["regel"]})
        self.tel[f"overgeslagen {context}: {reden}"] += 1
        return None

    # ── Kamerleden ─────────────────────────────────────────────────────────
    def _bestaande_persoon(self, pid: str, p: dict) -> int | None:
        if pid in self.ext_tk:
            return self.ext_tk[pid]
        if pid in self.handmatig:
            return self.handmatig[pid]
        namen = {sleutel(p["naam"])}
        if "-" in p["achternaam"]:  # dubbele achternaam: ook met het eerste of het laatste deel
            for deel in p["achternaam"].split("-"):
                namen.add(sleutel(f"{p['roepnaam']} {p['tussenvoegsel']} {deel}"))
        treffers = {i for k in namen for i, _, rol in self.pm_personen.get(k, []) if rol in PASSENDE_ROLLEN}
        return next(iter(treffers)) if len(treffers) == 1 else None

    def kamerleden(self):
        for pid, p in self.d["personen"].items():
            bestaand = self._bestaande_persoon(pid, p)
            naam = p["naam"]
            if not bestaand and sleutel(naam) in self.alle_namen:
                naam = f"{naam} (Tweede Kamerlid)"
            self.personen[pid] = {"tk_id": pid, "naam": naam, "bestaand": bestaand,
                                  "beschrijving": f"Lid van de Tweede Kamer voor {p['fractie']} "
                                                  f"(open data Tweede Kamer)."}
            if bestaand:
                n = self.conn.execute("SELECT name FROM entities WHERE id = ?", (bestaand,)).fetchone()[0]
                self.koppelingen.append({"soort": "kamerlid", "tekst": p["naam"], "model": n, "id": bestaand})
            rec = self.d["records"][f"persoon:{pid}"]
            functie = "Kamerlid"
            if p.get("zetel_functie") and p["zetel_functie"].lower() != "lid":
                functie += f", {p['zetel_functie'].lower()}"
            self._rel(("persoon", pid), ("bestaand", self.tweede_kamer), "ambt", "kamerzetel", rec,
                      functie=functie, start=p.get("van"),
                      claim=f"Volgens de open data van de Tweede Kamer (uitgave {self.uitgave}) is "
                            f"{p['naam']} lid van de Tweede Kamer voor {p['fractie']}"
                            f"{' (sinds ' + p['van'] + ')' if p.get('van') else ''}.")
            pnaam = partij_naam(p.get("fractie_afkorting") or "") or partij_naam(p.get("fractie") or "")
            if pnaam and pnaam in self.partij_id:
                self._rel(("bestaand", self.partij_id[pnaam]), ("persoon", pid), "lidmaatschap",
                          "partijlijn", rec,
                          claim=f"Volgens de open data van de Tweede Kamer (uitgave {self.uitgave}) zit "
                                f"{p['naam']} in de Tweede Kamerfractie van {p['fractie']}.")
            else:
                self._mis("fractie", rec, f"geen partij in het model voor '{p['fractie']}'")

    # ── belangen en werving ────────────────────────────────────────────────
    def nevenfuncties(self):
        for rec in self.d["records"].values():
            if rec["soort"] != "nevenfunctie" or rec.get("tot") or rec.get("actief") is False:
                continue
            woorden = zonder_haakjes(rec["omschrijving"]).split()
            vooraan = []  # functiewoorden vooraan, in sleutelvorm
            for w in woorden:
                s = sleutel(w)
                if s in FUNCTIEWOORDEN or s in BIJWOORDEN or s.replace(" ", "") in FUNCTIEWOORDEN \
                        or not s or s.isdigit():
                    vooraan.append(s.replace(" ", "") if s.replace(" ", "") in FUNCTIEWOORDEN else s)
                else:
                    break
            # de organisatie: de langste rest die in het model staat ('Lid Raad voor Cultuur'), anders
            # wat na alle functiewoorden overblijft, als nieuwe organisatie met rechtsvorm
            org, functie = None, set()
            for i in range(1, len(vooraan) + 1):
                rest = self._schoon_naam(" ".join(woorden[i:]))
                if not set(vooraan[:i]) & FUNCTIEWOORDEN or not rest:
                    continue
                gevonden = self._bestaand(rest, ruim=i == len(vooraan))
                if gevonden:
                    org, functie = gevonden, set(vooraan[:i])
                    break
            rest = self._schoon_naam(" ".join(woorden[len(vooraan):]))
            if org is None and (not set(vooraan) & FUNCTIEWOORDEN or not rest):
                self._mis("nevenfunctie", rec, "geen functie + organisatie")
                continue
            if UITSLUITEN.search(rest if org is None else self.org[org[0]][0]) or UITSLUITEN.search(rec["omschrijving"]):
                self._mis("nevenfunctie", rec, "uitgesloten")
                continue
            if org is not None:
                reden = self._toegestaan(org[0], "nevenfunctie")
                if reden:
                    self._mis("nevenfunctie", rec, reden)
                    continue
                ref = self._gekoppeld(rec, org[0], org[1], self.org[org[0]][0])
            else:
                functie = set(vooraan)
                ref = self._nieuw(rest, "nevenfunctie", rec)
                if not ref:
                    continue
            mech = "nevenfunctie_verstrengeling"
            if functie & AMBT_W:
                if ref[0] == "nieuw" or self.org[ref[1]][2] not in LOKAAL:
                    self._mis("nevenfunctie", rec, "raadslid/statenlid zonder gemeente of provincie")
                    continue
                rtype, mech = "ambt", "kamerzetel"
            elif functie & EIGENDOM_W:
                rtype = "eigendom"
            elif functie & PERSONEEL_W:
                rtype = "personeel"
            elif functie & ADVIES_W:
                rtype = "adviseur"
            elif functie & BESTUUR_W:
                rtype = "bestuurder"
            else:
                rtype = "lidmaatschap"
            naam = self.d["personen"][rec["persoon_id"]]["naam"]
            self._rel(("persoon", rec["persoon_id"]), ref, rtype, mech, rec,
                      functie=rec["omschrijving"][:200], start=_datum(rec.get("van")),
                      claim=f"Volgens het register van nevenactiviteiten van de Tweede Kamer (uitgave "
                            f"{self.uitgave}) heeft {naam} als nevenfunctie: {rec['omschrijving'].rstrip('.')}.")

    def loopbaan(self):
        """Bestaande organisaties bij elke functie; een nieuwe organisatie alleen als iemand er een
        leidende of adviserende functie had (directeur, bestuur, eigenaar, raad van advies …): een
        bijbaan neemt geen netwerk mee. Een latere andere functie bij die organisatie telt dan ook."""
        records = [r for r in self.d["records"].values() if r["soort"] == "loopbaan"]
        leidend = {(r["persoon_id"], sleutel(self._schoon_naam(r["werkgever"])))
                   for r in records if r.get("werkgever") and self._leidend(r.get("functie") or "")}
        for rec in records:
            if not rec.get("werkgever"):
                self._mis("loopbaan", rec, "geen werkgever")
                continue
            if POLITIEK_AMBT.search(rec.get("functie") or ""):
                self._mis("loopbaan", rec, "politiek ambt")
                continue
            nieuw_mag = (rec["persoon_id"], sleutel(self._schoon_naam(rec["werkgever"]))) in leidend
            ref = self._naamveld(rec["werkgever"], "loopbaan", rec, nieuw_mag=nieuw_mag)
            if not ref:
                continue
            f = rec["functie"] or ""
            overheid = ref[0] != "nieuw" and (self.org[ref[1]][2] or self.org[ref[1]][1] in OVERHEID_TYPES)
            if EIGENDOM_FUNCTIE.search(f):
                rtype = "eigendom"
            elif ADVIES_FUNCTIE.search(f):
                rtype = "adviseur"
            elif BESTUUR_FUNCTIE.search(f) and not overheid:
                rtype = "bestuurder"
            elif re.match(r"^(panel)?lid\b", f, re.I):
                rtype = "lidmaatschap"
            else:
                rtype = "personeel"
            naam = self.d["personen"][rec["persoon_id"]]["naam"]
            wat = (f"{_functie_tekst(rec['functie'])} bij {rec['werkgever']}" if rec["functie"]
                   else f"werkzaam bij {rec['werkgever']}")
            self._rel(("persoon", rec["persoon_id"]), ref, rtype, "draaideurconstructie", rec,
                      functie=(rec["functie"] or "")[:200], start=_datum(rec.get("van")),
                      eind=_datum(rec.get("tot")),
                      claim=f"Volgens de Tweede Kamer (uitgave {self.uitgave}) was {naam} {wat} "
                            f"({rec.get('van') or '?'} – {rec.get('tot') or 'heden'}).")

    @staticmethod
    def _leidend(functie: str) -> bool:
        return bool(BESTUUR_FUNCTIE.search(functie) or ADVIES_FUNCTIE.search(functie)
                    or EIGENDOM_FUNCTIE.search(functie) or LEIDING.search(functie))

    def reizen(self):
        for rec in self.d["records"].values():
            if rec["soort"] != "reis" or (rec.get("van") or "") < tk.GESCHENK_SINDS:
                continue
            betaler = re.sub(r"(?i)^.*?\b(betaald|vergoed) door\s+", "", rec["betaald_door"] or "")
            ref = self._naamveld(betaler, "reis", rec)
            if not ref:
                continue
            naam = self.d["personen"][rec["persoon_id"]]["naam"]
            self._rel(ref, ("persoon", rec["persoon_id"]), "geschenk", "geschenk_en_gastvrijheid", rec,
                      functie=f"Betaalde reis naar {rec['bestemming']}"[:200], start=rec.get("van"),
                      claim=f"Volgens het reizenregister van de Tweede Kamer (uitgave {self.uitgave}) "
                            f"reisde {naam} op {rec.get('van')} naar {rec['bestemming']}; betaald door: "
                            f"{rec['betaald_door']}.")

    def geschenken(self):
        for rec in self.d["records"].values():
            if rec["soort"] != "geschenk":
                continue
            tekst = re.sub(r"[‘'\"“”][^’'\"“”]{2,}[’'\"“”]", " ", rec["omschrijving"])  # titels weg
            gevonden = None
            for m in GEVER.finditer(tekst):
                frase = self._gever(tekst[m.end():])
                if not frase or UITSLUITEN.search(frase):
                    continue
                gevonden = self._bestaand(frase, ruim=True)
                if gevonden:
                    break
            if not gevonden:
                self._mis("geschenk", rec, "geen bekende gever")
                continue
            reden = self._toegestaan(gevonden[0], "geschenk")
            if reden:
                self._mis("geschenk", rec, reden)
                continue
            ref = self._gekoppeld(rec, gevonden[0], "gever", rec["omschrijving"][:80])
            naam = self.d["personen"][rec["persoon_id"]]["naam"]
            self._rel(ref, ("persoon", rec["persoon_id"]), "geschenk", "geschenk_en_gastvrijheid", rec,
                      functie="Geschenk", start=rec.get("datum"),
                      claim=f"Volgens het geschenkenregister van de Tweede Kamer (uitgave {self.uitgave}) "
                            f"meldde {naam} op {rec.get('datum')}: {rec['omschrijving']}")

    @staticmethod
    def _gever(tekst: str) -> str:
        """'de KNVB 2 kaarten voor …' → 'KNVB'; 'de Stichting De Gulden Regel een logo' → 'Stichting
        De Gulden Regel': de woorden tot een klein (niet-hoofdletter) stopwoord, getal of leesteken."""
        uit, woorden = [], tekst.split()
        for i, w in enumerate(woorden):
            if i == 0 and w in ("de", "het", "the"):
                continue
            volgend = woorden[i + 1] if i + 1 < len(woorden) else ""
            if uit and w in ("de", "van", "der", "den", "ter", "te") and volgend[:1].isupper():
                uit.append(w)  # tussenvoegsel in een naam ('Eva de Munnik'): geen einde van de gever
                continue
            if w in GEVER_STOP or re.match(r"^[\d€]", w):
                break
            if w[-1:] in ",;:" or (w.endswith(".") and not re.search(r"(?:\b[A-Za-z]\.)+$", w)):
                uit.append(w.rstrip(",;:."))
                break
            uit.append(w)
        return " ".join(uit)

    def _rel(self, bron, doel, rtype, mech, rec, claim, functie=None, start=None, eind=None):
        if (bron, doel, rtype) in self.paren:  # zelfde verband uit een ander record: één is genoeg
            self.tel["zelfde verband, ander record"] += 1
            return
        self.paren.add((bron, doel, rtype))
        self.relaties.append({"bron": bron, "doel": doel, "type": rtype, "mechanisme": mech,
                              "functie": functie, "start": start, "eind": eind, "sleutel": rec["sleutel"],
                              "regel": rec["regel"], "claim": claim})
        self.tel[f"{rtype}/{mech}"] += 1

    def maak(self):
        self.kamerleden()
        self.nevenfuncties()
        self.loopbaan()
        self.reizen()
        self.geschenken()
        return self


class Indiener:
    """Ook voor andere Kamerregisters (lobby_naar_model.py): `bron` = de registermodule."""

    def __init__(self, plan: Plan, rest, log=print, bron=tk, cluster: str = CLUSTER):
        self.p, self.rest, self.log, self.reg, self.cluster = plan, rest, log, bron, cluster
        self.ent: dict[tuple, int] = {}
        self.bestaande_relaties = {tuple(r) for r in plan.conn.execute(
            "SELECT source_id, target_id, relation_type FROM relations WHERE NOT vervangen AND status <> 'afgewezen'")}
        self.tel = Counter()

    def bron(self) -> int:
        status, res = self.rest("POST", "/api/sources", {
            "title": self.reg.TITEL.format(uitgave=self.p.uitgave), "source_type": "dataset",
            "publisher": self.reg.UITGEVER, "date_published": self.p.uitgave, "cluster_key": self.cluster,
            "location": {"type": "url", "value": self.reg.URL},
            "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
        if status not in (200, 201):
            raise SystemExit(f"bron registreren faalde: {status} {res}")
        return res["id"]

    def entiteiten(self):
        for pid, p in self.p.personen.items():
            ids = [{"stelsel": "tk_persoon", "waarde": pid}]
            if p["bestaand"]:
                status, res = self.rest("POST", f"/api/entities/{p['bestaand']}/register", {"externe_ids": ids})
                self.tel["persoon gekoppeld" if status == 200 else f"persoon koppelen {status}"] += 1
                if status != 200:
                    self.log(f"  ✗ koppelen {p['naam']} → #{p['bestaand']}: {status} {res.get('error')}")
                    continue
                self.ent[("persoon", pid)] = p["bestaand"]
                continue
            status, res = self.rest("POST", "/api/entities", {
                "name": p["naam"], "type": "persoon", "primary_role_id": self.p.rol["politicus"],
                "description": p["beschrijving"], "externe_ids": ids})
            if status == 201:
                self.ent[("persoon", pid)] = res["id"]
                self.tel["persoon nieuw"] += 1
            elif status == 409 and res.get("entity_id"):
                self.ent[("persoon", pid)] = res["entity_id"]
                self.tel["persoon bestond (externe id)"] += 1
            else:
                self.tel[f"persoon fout {status}"] += 1
                self.log(f"  ✗ {p['naam']}: {status} {res.get('error')}")
        for k, o in self.p.nieuwe_orgs.items():
            body = {"name": o["naam"], "type": o["type"], "primary_role_id": self.p.rol[o["rol"]],
                    "description": o["beschrijving"]}
            for veld in ("bestuurslaag", "externe_ids"):
                if o.get(veld):
                    body[veld] = o[veld]
            status, res = self.rest("POST", "/api/entities", body)
            if status == 201:
                self.ent[("nieuw", k)] = res["id"]
                self.tel["org nieuw"] += 1
            else:  # bv. de naam bestaat al als afgewezen of vervangen knoop: daar niet aan koppelen
                self.tel[f"org fout {status}"] += 1
                self.log(f"  ✗ {o['naam']}: {status} {res.get('error')}")
        nodig = {ref for r in self.p.relaties for ref in (r["bron"], r["doel"]) if ref[0] == "oo"}
        for ref in sorted(nodig):
            o = self.p.oo_orgs[ref[1]]
            body = {"name": o["naam"], "type": o["type"], "primary_role_id": o["rol_id"],
                    "description": o["beschrijving"], "bestuurslaag": o["bestuurslaag"],
                    "metadata": {"oo_type": o["oo_type"]},
                    "externe_ids": [{"stelsel": "oo", "waarde": o["oo_id"]}]
                    + ([{"stelsel": "tooi", "waarde": o["tooi"]}] if o["tooi"] else [])}
            if o["start"]:
                body["active_from"] = o["start"]
            status, res = self.rest("POST", "/api/entities", body)
            if status in (201, 409) and (res.get("id") or res.get("entity_id")):
                self.ent[ref] = res.get("id") or res.get("entity_id")
                self.tel["registerorganisatie nieuw" if status == 201 else "registerorganisatie bestond"] += 1
            else:
                self.tel[f"registerorganisatie fout {status}"] += 1
                self.log(f"  ✗ {o['naam']}: {status} {res.get('error')}")

    def _id(self, ref):
        return ref[1] if ref[0] == "bestaand" else self.ent.get(ref)

    def relaties(self, bron_id: int):
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
            for veld, waarde in (("functie", r["functie"]), ("active_from", r["start"]),
                                 ("active_until", r["eind"])):
                if waarde:
                    body[veld] = waarde
            status, res = self.rest("POST", "/api/relations", body)
            if status != 201:
                self.tel[f"relatie fout {status}"] += 1
                self.log(f"  ✗ relatie {r['type']} {s}→{t}: {status} {res.get('error')}")
                continue
            self.bestaande_relaties.add((s, t, r["type"]))
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": res["id"], "claim": r["claim"], "stance": "supporting",
                "citations": [{"source_id": bron_id, "quote": r["regel"], "methode": "officieel_register_scrape",
                               "section": r["sleutel"], "page": f"{self.reg.BRON}/{self.p.uitgave}",
                               "context": self.reg.URL}]})
            self.tel["relatie nieuw" if status == 201 else f"argument fout {status}"] += 1
            if status != 201:
                self.log(f"  ✗ argument {r['type']} {s}→{t}: {status} {res.get('error')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave", help="YYYY-MM-DD; standaard de nieuwste bewaarde uitgave")
    ap.add_argument("--indienen", action="store_true", help="echt indienen (standaard: droogloop)")
    a = ap.parse_args()
    data = tk.lees(tk.pad_van(a.uitgave) if a.uitgave else tk.uitgaven()[-1])
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(KOPPELINGEN.read_text(encoding="utf-8")) if KOPPELINGEN.exists() else {}
    plan = Plan(data, conn, koppelingen).maak()
    print(json.dumps({"uitgave": plan.uitgave, "kamerleden": len(plan.personen),
                      "kamerleden_bestaand": sum(1 for p in plan.personen.values() if p["bestaand"]),
                      "nieuwe_organisaties": len(plan.nieuwe_orgs), "relaties": len(plan.relaties),
                      "telling": dict(sorted(plan.tel.items()))}, ensure_ascii=False, indent=1))
    for naam, inhoud in (("overgeslagen", plan.overgeslagen), ("koppelingen", plan.koppelingen)):
        (tk.MAP / f"{naam}_{plan.uitgave}.json").write_text(
            json.dumps(inhoud, ensure_ascii=False, indent=1), encoding="utf-8")
    if not a.indienen:
        print(f"\n(droogloop — niets ingediend; zie {tk.MAP}/koppelingen_{plan.uitgave}.json)")
        return
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()))
    bron_id = ind.bron()
    ind.entiteiten()
    ind.relaties(bron_id)
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
