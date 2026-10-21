#!/usr/bin/env python3
"""Nevenfunctieregister van de Rechtspraak (via Open Rechtspraak) → het model (eigenaar 2026-10-19).

rechtspraak.py leest de uitgave: per rechter of raadsheer (ook plaatsvervangers) de huidige
functies in de rechtspraak, de nevenbetrekkingen (functie, instantie, soort, betaald) en de
beroepsgegevens buiten de rechterlijke macht. Dit script kiest daaruit wat ertoe doet en plant:

  - een lopende nevenbetrekking bij een organisatie die al in het model staat → rechter ↔
    organisatie (bestuurder / adviseur / lidmaatschap / personeel / eigendom; een raadslid of
    statenlid: ambt/kamerzetel bij de gemeente of provincie), mechanisme
    `nevenfunctie_verstrengeling`;
  - een lopende nevenbetrekking bij een organisatie die nog niet in het model staat, alleen als de
    rechtsvorm in de naam staat (README § Regels), de functie leidend of adviserend is en de
    nevenbetrekking boven de interessedrempel scoort (DREMPEL_NIEUW), of als de organisatie met de
    hand getypeerd is in koppelingen.json ('rechtspraak_organisaties');
  - een functie buiten de rechterlijke macht (loopbaan) → `draaideurconstructie`, onder dezelfde
    regels als de loopbaan van Kamerleden: een bestaande organisatie, of nieuw met rechtsvorm bij
    een leidende functie;
  - bestaat het verband al (zelfde paar, een affiliatietype), dan krijgt het alleen een extra
    argument met de recordregel als citaat.
Organisaties binnen de rechtspraak (gerechten, Raad voor de rechtspraak, SSR, NVvR), partijen,
publicaties, onderwijs en cursussen worden geen verband. Rechters koppelen nooit op naam alleen:
externe id 'rechtspraak' (het id in het register), of voorletters + achternaam die in de hele
uitgave uniek zijn, bij precies één persoon met een passende rol die het gerecht noemt; anders een
nieuwe knoop. Alleen wie nu in het register staat; geen plaats, adres of contactgegevens.

Interessant versus ruis (zie `score`): organisatiesoort × functiesoort × bezoldiging ×
zeldzaamheid (1/log2(1 + aantal rechters bij dezelfde instantie), naar Adamic-Adar zoals de viz)
× 1,5 als de organisatie al in het model staat. Het rapport (data/registers/rechtspraak/
rapport_<uitgave>.json) geeft de top, de lift per organisatiesoort bij plaatsvervangers
tegenover beroepsrechters en wat het filter weglaat.

Gebruik:
    python3 tools/registers/rechtspraak_naar_model.py                 # droogloop + rapport
    python3 tools/registers/rechtspraak_naar_model.py --top 50
    python3 tools/registers/rechtspraak_naar_model.py --haal [--indienen]
    (--indienen vergt eerst het stelsel 'rechtspraak' in server.EXTERNE_STELSELS)
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
import rechtspraak  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ACHTER, TITELS, ontleed_naam, schoon, sleutel  # noqa: E402
from naar_model import PASSENDE_ROLLEN, TOKEN, Rest  # noqa: E402

DB_PATH = tkm.ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:rechtspraak"
STELSEL = "rechtspraak"
DREMPEL_BESTAAND = 2.0    # minimumscore voor een verband met een organisatie in het model
DREMPEL_NIEUW = 6.0       # minimumscore voor een nieuwe organisatie
NIEUW_SOORTEN = {"bedrijf", "financieel", "advocatuur", "belangen_lobby", "politiek_denktank", "media"}
# Een eigen vennootschap (pensioen-bv, praktijk, beheer-bv) is privé, geen netwerk
PRIVE_BV = re.compile(r"\b(beheer|holding|praktijk\w*|pensioen ?bv|management|houdster\w*|familie\w*|"
                      r"pensioenvennootschap|eigen vennootschap)\b", re.I)
AFFILIATIE = {"bestuurder", "adviseur", "lidmaatschap", "personeel", "eigendom", "dienstverband",
              "draaideur", "ambt"}

# ── organisatiesoort (soort instantie + naam) → gewicht ─────────────────────
# Volgorde telt: de eerste soort waarvan een woord(deel) voorkomt, wint.
ORG_SOORTEN = [
    ("rechtspraak", 0.1, r"\b(rechtbank|gerechtshof|hoge raad|raad voor de rechtspraak|studiecentrum rechtspleging|"
                         r"ssr|rechterlijke macht|rechtspraak|nvvr|nederlandse vereniging voor rechtspraak|"
                         r"centrale raad van beroep|college van beroep voor het bedrijfsleven|"
                         r"rechtersvereniging|vereniging voor rechtspraak)\b"),
    ("tucht_geschil", 1.5, r"(tucht|discipline|geschil|arbitr|bindend advies|klachten|mediat|kifid|scheidsgerecht|"
                           r"commissie van beroep|bezwa(a)?r|beroepscommissie|ombuds)"),
    ("advocatuur", 3.0, r"(advoca|\blaw\b|\blegal\b|notari|\bcounsel)"),
    ("financieel", 3.0, r"(\bbank|verzeker|pensioen|belegg|vermogen|financ|accountan|\bfonds\b|insurance|capital|"
                        r"investment|trust\b)"),
    ("politiek_denktank", 3.0, r"(politieke partij|\bpartij\b|denktank|think ?tank|wetenschappelijk bureau|"
                               r"wiardi beckman|teldersstichting|\bvvd\b|\bcda\b|\bd66\b|\bpvda\b|groenlinks|"
                               r"\bsgp\b|christenunie|\bpvv\b|\bbbb\b|\bja21\b)"),
    ("belangen_lobby", 2.5, r"(branche|werkgevers|\bvno|\bmkb|belangen|lobby|ondernemersorganisatie|"
                            r"brancheorganisatie|koepel)"),
    ("bedrijf", 2.5, r"(\bb v\b|\bn v\b|\bbv\b|\bnv\b|bedrijf|onderneming|vennootschap|holding|makelaar|"
                     r"consultan|adviesbureau|\bgroup\b|\bgroep\b|vastgoed|projectontwikkel|\bltd\b|\bgmbh\b)"),
    ("overheid", 2.0, r"(ministerie|gemeente|provincie|waterschap|\brijks|overheid|politie|belastingdienst|"
                      r"\buwv\b|\bsvb\b|\bind\b|inspectie|penitentiair|\bdji\b|justitiele|staat der nederlanden|"
                      r"raad van state|zelfstandig bestuursorgaan|\bzbo\b|autoriteit|toezichthouder|"
                      r"openbaar ministerie|\bom\b|\bcbr\b|\bcak\b|\bduo\b)"),
    ("advies", 1.5, r"(adviescollege|adviesorgaan|adviesraad|raad voor|\bcommissie\b|college|kenniscentrum|"
                    r"planbureau|wrr)"),
    ("beroep_vakbond", 1.5, r"(vakbond|beroepsvereniging|beroepsorganisatie|orde van|\bknb\b|\bnova\b)"),
    ("media", 1.0, r"(uitgever|uitgeverij|tijdschrift|omroep|krant|dagblad|\bmedia|podcast|\bsdu\b|wolters|"
                   r"kluwer|boom juridisch)"),
    ("zorg", 0.7, r"(ziekenhuis|\bzorg|gezondheid|\bggz|hulpverlen|jeugdzorg|ouderenzorg|verpleeg)"),
    ("onderwijs", 0.5, r"(universiteit|university|hogeschool|hoge school|academie|academy|opleiding|instituut|"
                       r"school|\bpao\b|wetenschap|onderzoek|faculteit|studiecentrum|college of)"),
    ("eigen_praktijk", 1.0, r"(eenmanszaak|zelfstandig|eigen praktijk|\bzzp)"),
    ("maatschappelijk", 0.3, r"(stichting|vereniging|kerk|parochie|sport|voetbal|hockey|tennis|golf|museum|theater|"
                             r"muziek|koor|orkest|cultuur|festival|\bvve\b|oudercommissie|club|society|genootschap|"
                             r"vrienden van|fonds voor|loge|serviceclub|rotary|lions)"),
]
MODEL_TYPE_GEWICHT = {"bedrijf": 2.5, "vermogensbeheerder": 3.0, "lobbygroep": 3.0, "denktank": 3.0,
                      "elite_netwerk": 3.0, "mediaorganisatie": 2.5, "omroep": 2.5, "persbureau": 2.5,
                      "platform": 2.0, "pr_bureau": 3.0, "overheidsinstelling": 2.0, "toezichthouder": 2.0,
                      "partij": 3.0, "ngo": 1.0, "stichting": 1.0, "vakbond": 1.5,
                      "onderwijsinstelling": 0.5, "rechterlijke_macht": 0.1}

# ── functiesoort → (gewicht, relatietype); None = geen verband ───────────────
FUNCTIE_SOORTEN = [
    ("publicatie_onderwijs", 0.2, None,
     r"^(gast)?docent|\bdocent|doceren|docentschap|auteur|redact|cursus|spreker|examinator|praktijkbegeleider|"
     r"\bcoach|intervisie|presentator|commentator|annotator|preadvis|videobespreking|opleider|trainer|"
     r"gastcollege|columnist|schrijver|podcast|scheidsrechter|wijkco"),
    ("eigendom", 3.0, "eigendom", r"\b(eigenaar|aandeelhouder|dga|firmant|vennoot|medeeigenaar|mede eigenaar)\b"),
    ("toezicht", 3.0, "bestuurder",
     r"(commissaris|raad van commissarissen|raad van toezicht|toezichthouder|\brvc\b|\brvt\b|supervisory|"
     r"non executive)"),
    ("advocaat", 3.0, "personeel", r"\b(advocaat|advocate|advocaat partner|partner|of counsel|notaris)\b"),
    ("advies", 2.0, "adviseur",
     r"(adviseur|raad van advies|adviescommissie|advisory|adviesraad|klankbord|consultant)"),
    ("quasi_rechtspraak", 1.5, "lidmaatschap",
     r"(arbiter|bindend advis|mediator|tuchtcollege|geschillencommissie|klachtencommissie|bezwa(a)?rcommissie|"
     r"beroepscommissie|commissie van beroep|plaatsvervangend lid|plv lid|plv\b|staatsraad|kroonlid|"
     r"rechter plaatsvervanger|raadsheer plaatsvervanger|lid jurist|onafhankelijk voorzitter)"),
    ("bestuur", 2.0, "bestuurder",
     r"\b(voorzitter|vicevoorzitter|vice voorzitter|bestuurslid|bestuurder|penningmeester|penningsmeester|"
     r"secretaris|directeur|president|trustee|chair|bestuur|dagelijks bestuur)\b"),
    ("dienstverband", 1.0, "personeel",
     r"\b(hoogleraar|universitair|medewerker|jurist|werkzaam|onderzoeker|fellow|in dienst|ambtenaar)\b"),
    ("lid", 1.0, "lidmaatschap", r"\b(lid|leden|member|erelid|lidmaatschap)\b"),
]
RAADSLID = re.compile(r"\b(gemeenteraadslid|raadslid|statenlid|lid (van )?(de )?(gemeenteraad|provinciale staten))\b", re.I)


def org_soort(tekst: str, model_type: str | None = None) -> tuple[str, float]:
    s = f" {sleutel(tekst)} "
    for naam, gewicht, patroon in ORG_SOORTEN:
        if re.search(patroon, s):
            soort = (naam, gewicht)
            break
    else:
        soort = ("onbekend", 0.5)
    if model_type in MODEL_TYPE_GEWICHT and soort[0] != "rechtspraak":
        return (f"{soort[0]}|model:{model_type}", max(soort[1], MODEL_TYPE_GEWICHT[model_type]))
    return soort


def functie_soort(functie: str) -> tuple[str, float, str | None]:
    s = f" {sleutel(functie)} "
    for naam, gewicht, rtype, patroon in FUNCTIE_SOORTEN:
        if re.search(patroon, s):
            return naam, gewicht, rtype
    return "onbekend", 0.5, None


def _achter(n: dict) -> str:
    """Tussenvoegsel + achternaam, zonder titels erachter ('Yu bc.' → 'yu')."""
    w = sleutel(f"{n['tussenvoegsel'] or ''} {n['achternaam'] or ''}").split()
    while len(w) > 1 and (w[-1] in TITELS or w[-1] in ACHTER):
        w.pop()
    return " ".join(w)


def plaatsvervanger(rec: dict) -> bool:
    fs = [f for f, _, _ in rec.get("functies") or []]
    return bool(fs) and all("plaatsvervang" in sleutel(f) for f in fs)


class Plan(tkm.Plan):
    def __init__(self, data: dict, conn: sqlite3.Connection, koppelingen: dict | None = None):
        super().__init__({"uitgave": data["uitgave"], "personen": {}, "records": {}}, conn, koppelingen)
        self.rs = data
        self.mech.update(self._ids("mechanisms", ("nevenfunctie_verstrengeling", "draaideurconstructie",
                                                  "kamerzetel")))
        self.rol.update({n: i for n, i in conn.execute(
            "SELECT name, id FROM roles WHERE NOT vervangen AND name IN ('bestuursrechter', 'topambtenaar')")})
        self.hand = {sleutel(k): v for k, v in (koppelingen or {}).get("rechtspraak_organisaties", {}).items()
                     if not k.startswith("_")}
        self.ext_rs = {w: e for e, w in conn.execute(
            "SELECT entity_id, waarde FROM externe_ids WHERE stelsel = ?", (STELSEL,))}
        # bestaande verbanden per ongeordend paar (voor 'extra bron')
        self.bestaande_paren: dict[tuple[int, int], list[tuple[int, str, str]]] = defaultdict(list)
        for rid, s, t, typ, st in conn.execute(
                "SELECT id, source_id, target_id, relation_type, status FROM relations "
                "WHERE NOT vervangen AND status <> 'afgewezen'"):
            self.bestaande_paren[(min(s, t), max(s, t))].append((rid, typ, st))
        self.al_geciteerd = {(r, sec) for r, sec in conn.execute("""
            SELECT a.relation_id, c.section FROM citations c JOIN arguments a ON a.id = c.argument_id
            WHERE c.page LIKE 'rechtspraak/%' AND a.relation_id IS NOT NULL""")}
        recs = data["records"].values()
        # hoeveel rechters bij dezelfde instantie: de noemer van de zeldzaamheid
        self.df = Counter()
        for k, ids in self._per_instantie(recs).items():
            self.df[k] = len(ids)
        # voorletters + achternaam: alleen uniek in de hele uitgave koppelt
        self.naam_telling = Counter(self._kort(r) for r in recs if r["soort"] == "persoon")
        self.personen_rs: dict[str, dict] = {}
        self.extra_bron: list[dict] = []
        self.kandidaten: list[dict] = []   # alles wat gescoord is (ook niet gepland), voor het rapport

    @staticmethod
    def _per_instantie(recs):
        uit = defaultdict(set)
        for r in recs:
            if r["soort"] in ("nevenfunctie", "loopbaan") and r.get("instantie"):
                uit[sleutel(tkm.zonder_haakjes(r["instantie"]) or r["instantie"])].add(r["persoon_id"])
        return uit

    @staticmethod
    def _kort(rec: dict) -> str:
        return sleutel(ontleed_naam(rec["naam"])["weergave"])

    # ── score ──────────────────────────────────────────────────────────────
    def score(self, rec: dict, org_ref: tuple | None) -> dict:
        model_type = self.org[org_ref[1]][1] if org_ref and org_ref[0] in ("bestaand", "oo") else None
        osoort, ow = org_soort(f"{rec.get('soort_instantie') or ''} {rec['instantie']}", model_type)
        fsoort, fw, rtype = functie_soort(rec.get("functie") or "")
        if rec["soort"] == "loopbaan":
            fw *= 0.8
            if rec.get("tot") and rec["tot"][:4].isdigit() and int(rec["tot"][:4]) < int(self.uitgave[:4]) - 10:
                fw *= 0.5
        betaald = {"betaald": 1.5, "onbetaald": 1.0}.get(rec.get("betaald"), 1.2)
        df = max(1, self.df[sleutel(tkm.zonder_haakjes(rec["instantie"]) or rec["instantie"])])
        zeldzaam = 1 / math.log2(1 + df)
        in_model = 1.5 if org_ref and org_ref[0] in ("bestaand", "oo") else 1.0
        return {"score": round(ow * fw * betaald * zeldzaam * in_model, 3), "org_soort": osoort,
                "functie_soort": fsoort, "rtype": rtype, "df": df}

    # ── rechters ───────────────────────────────────────────────────────────
    def _bestaande_rechter(self, rec: dict) -> int | None:
        if rec["persoon_id"] in self.ext_rs:
            return self.ext_rs[rec["persoon_id"]]
        kort = self._kort(rec)
        if self.naam_telling[kort] != 1:
            return None
        n = ontleed_naam(rec["naam"])
        letters = re.sub(r"[^a-z]", "", (n["voorletters"] or "").lower())
        achter = _achter(n)
        gerechten = {sleutel(o) for _, o, _ in rec["functies"]}
        treffers = set()
        for i, naam, rol, c in self._kandidaat_personen():
            if c["achter"] != achter or not letters:
                continue
            # voorletters passen ('M.' ~ 'M.V.'), of de voornaam begint met de eerste voorletter
            if c["letters"]:
                if not (c["letters"].startswith(letters) or letters.startswith(c["letters"])):
                    continue
            elif not c["voornaam"].startswith(letters[:1]):
                continue
            beschr = self.conn.execute("SELECT name || ' ' || COALESCE(description, '') FROM entities "
                                       "WHERE id = ?", (i,)).fetchone()[0]
            doelen = {sleutel(t) for (t,) in self.conn.execute(
                "SELECT e.name FROM relations r JOIN entities e ON e.id = r.target_id "
                "WHERE r.source_id = ? AND NOT r.vervangen", (i,))}
            if any(g and (g in sleutel(beschr) or g in doelen) for g in gerechten):
                treffers.add(i)
        return next(iter(treffers)) if len(treffers) == 1 else None

    def _kandidaat_personen(self):
        if not hasattr(self, "_kp"):
            self._kp = []
            for i, naam, rol in self.conn.execute("""
                    SELECT e.id, e.name, r.name FROM entities e LEFT JOIN roles r ON r.id = e.primary_role_id
                    WHERE e.type = 'persoon' AND NOT e.vervangen AND e.status <> 'afgewezen'"""):
                if rol not in PASSENDE_ROLLEN | {"bestuursrechter"}:
                    continue
                c = ontleed_naam(tkm.zonder_haakjes(naam).split(",")[0])
                self._kp.append((i, naam, rol, {
                    "achter": _achter(c),
                    "letters": re.sub(r"[^a-z]", "", (c["voorletters"] or "").lower()),
                    "voornaam": sleutel(c["roepnaam"] or c["voornamen"] or "")}))
        return self._kp

    def _rechter(self, rec: dict) -> tuple:
        pid = rec["persoon_id"]
        if pid not in self.personen_rs:
            bestaand = self._bestaande_rechter(rec)
            naam = ontleed_naam(rec["naam"])["weergave"]
            f, o = (rec["functies"][0][0], rec["functies"][0][1]) if rec["functies"] else ("rechter", "")
            if not bestaand and sleutel(naam) in self.alle_namen:
                naam = f"{naam} ({f.lower()} {o})".strip()
            bestuursrecht = any(re.search(r"centrale raad van beroep|college van beroep voor het bedrijfsleven|"
                                          r"bestuursrecht", sleutel(f"{a} {b}")) for a, b, _ in rec["functies"])
            self.personen_rs[pid] = {
                "rs_id": pid, "naam": naam, "bestaand": bestaand,
                "rol": "bestuursrechter" if bestuursrecht else None,
                "beschrijving": ("; ".join(f"{a.lower()} bij {b}" for a, b, _ in rec["functies"])
                                 or "Rechterlijk ambtenaar") + " (nevenfunctieregister van de Rechtspraak)."}
            if bestaand:
                self.koppelingen.append({"soort": "rechter", "tekst": rec["naam"], "id": bestaand,
                                         "model": self.conn.execute("SELECT name FROM entities WHERE id = ?",
                                                                    (bestaand,)).fetchone()[0]})
        return ("persoon", pid)

    # ── organisaties ───────────────────────────────────────────────────────
    def _organisatie(self, rec: dict, fsoort: str, sc: dict) -> tuple | None:
        """→ ('bestaand'|'oo', id) | ('nieuw', sleutel) | None (gelogd)."""
        context = rec["soort"]
        naam = self._schoon_naam(rec["instantie"] or "")
        if not naam:
            return self._mis(context, rec, "geen instantie")
        if UITGESLOTEN.search(sleutel(naam)):
            return self._mis(context, rec, "rechtspraak zelf of partij-eigen")
        kandidaten = [naam] + ([naam.split(",")[0].strip()] if "," in naam else [])
        if (rec.get("soort_instantie") and len(rec["soort_instantie"].split()) > 1
                and sleutel(tkm.zonder_haakjes(naam)) in sleutel(rec["soort_instantie"])):
            kandidaten.append(self._schoon_naam(rec["soort_instantie"]))  # 'Raad voor …' in het soortveld
        for kand in kandidaten:
            gevonden = self._bestaand(kand, ruim=True)
            if gevonden:
                if self.org[gevonden[0]][1] == "rechterlijke_macht":
                    return self._mis(context, rec, "rechtspraak zelf")
                reden = self._toegestaan(gevonden[0], context)
                if reden:
                    return self._mis(context, rec, reden)
                return self._gekoppeld(rec, gevonden[0], gevonden[1], kand)
        t = self.hand.get(sleutel(naam))
        if t:
            k = sleutel(t["naam"])
            self.nieuwe_orgs.setdefault(k, {"naam": t["naam"], "type": t["type"], "rol": t["rol"],
                                            "beschrijving": "Genoemd in het nevenfunctieregister van de Rechtspraak."})
            self.rol.update(self._ids("roles", (t["rol"],)))
            return ("nieuw", k)
        if sc["org_soort"].split("|")[0] not in NIEUW_SOORTEN:
            return self._mis(context, rec, f"niet in het model ({sc['org_soort']})")
        n = ontleed_naam(rec["naam"])
        if PRIVE_BV.search(f"{naam} {rec.get('functie') or ''} {rec.get('soort_instantie') or ''}") or (n["achternaam"] and sleutel(n["achternaam"]) in sleutel(naam).split()):
            return self._mis(context, rec, "eigen vennootschap (privé)")
        if fsoort not in ("eigendom", "toezicht", "advocaat", "bestuur", "advies"):
            return self._mis(context, rec, "niet in het model; geen leidende of adviserende functie")
        if sc["score"] < DREMPEL_NIEUW:
            return self._mis(context, rec, "niet in het model; onder de drempel voor een nieuwe organisatie")
        return self._nieuw_rs(naam, rec)

    def _nieuw_rs(self, naam: str, rec: dict) -> tuple | None:
        vorm = tkm.rechtsvorm(naam)
        if not vorm or len(naam.split()) < 2:
            return self._mis(rec["soort"], rec, "niet in het model en geen rechtsvorm in de naam")
        if self._partij_eigen(naam):
            return self._mis(rec["soort"], rec, "partij")
        k = re.sub(r"\s+(b v|n v|bv|nv|u a|ua)$", "", tkm._zonder_lidwoord(sleutel(naam)))
        if k in tkm.GENERIEK:
            return self._mis(rec["soort"], rec, "geen eigen naam")
        naam = naam[:1].upper() + naam[1:]
        self.nieuwe_orgs.setdefault(k, {"naam": naam, "type": vorm[0], "rol": vorm[1],
                                        "beschrijving": "Genoemd in het nevenfunctieregister van de Rechtspraak."})
        self.koppelingen.append({"soort": rec["soort"], "tekst": rec["regel"], "nieuw": naam, "type": vorm[0]})
        return ("nieuw", k)

    # ── plannen ────────────────────────────────────────────────────────────
    def maak(self):
        for rec in self.rs["records"].values():
            if rec["soort"] == "nevenfunctie" and not (rec.get("huidig") and not rec.get("tot")):
                continue
            if rec["soort"] not in ("nevenfunctie", "loopbaan"):
                continue
            sc0 = self.score(rec, None)
            fsoort, rtype = sc0["functie_soort"], sc0["rtype"]
            self.kandidaten.append({**sc0, "sleutel": rec["sleutel"], "regel": rec["regel"],
                                    "plv": plaatsvervanger(rec), "gepland": False})
            kand = self.kandidaten[-1]
            if rec["soort"] == "nevenfunctie" and rtype is None:
                self._mis("nevenfunctie", rec, f"ruis: {fsoort}")
                continue
            if rec["soort"] == "loopbaan" and tkm.POLITIEK_AMBT.search(rec.get("functie") or ""):
                self._mis("loopbaan", rec, "politiek ambt")
                continue
            if rec["soort"] == "loopbaan":
                rtype = rtype or "personeel"
                if fsoort == "publicatie_onderwijs":
                    rtype = "personeel"
            # loopbaan: een nieuwe organisatie alleen bij een leidende functie (README § Regels)
            ref = self._organisatie(rec, fsoort if rec["soort"] == "nevenfunctie"
                                    else ("bestuur" if self._leidend(rec.get("functie") or "") else "niet leidend"), sc0)
            if not ref:
                continue
            sc = self.score(rec, ref)
            kand.update(sc)
            mech = "nevenfunctie_verstrengeling" if rec["soort"] == "nevenfunctie" else "draaideurconstructie"
            if RAADSLID.search(rec.get("functie") or ""):
                if ref[0] == "nieuw" or self.org[ref[1]][2] not in tkm.LOKAAL:
                    self._mis(rec["soort"], rec, "raadslid/statenlid zonder gemeente of provincie")
                    continue
                rtype, mech = "ambt", "kamerzetel"
            if ref[0] != "nieuw" and sc["score"] < DREMPEL_BESTAAND:
                self._mis(rec["soort"], rec, "onder de interessedrempel")
                continue
            persoon = self._rechter(rec)
            kand["gepland"] = True
            naam = self.personen_rs[rec["persoon_id"]]["naam"]
            wat = (f"als nevenbetrekking {rec['functie']} bij {rec['instantie']}" if rec["soort"] == "nevenfunctie"
                   else f"buiten de rechterlijke macht {tkm._functie_tekst(rec['functie'])} bij {rec['instantie']}")
            claim = (f"Volgens het nevenfunctieregister van de Rechtspraak (uitgave {self.uitgave}) heeft "
                     f"{rec['naam']} ({'; '.join(dict.fromkeys(f'{a}, {b}' for a, b, _ in rec['functies']))}) {wat}"
                     f" ({rechtspraak._periode(rec.get('van'), rec.get('tot'))}"
                     + (f", {rec['betaald']}" if rec.get("betaald") else "") + ").")
            n_voor = len(self.relaties)
            self._rel(persoon, ref, rtype, mech, rec, claim, functie=(rec["functie"] or "")[:200],
                      start=rec.get("van"), eind=rec.get("tot"))
            if len(self.relaties) > n_voor:
                self.relaties[-1].update(score=sc["score"], org_soort=sc["org_soort"],
                                         functie_soort=sc["functie_soort"], betaald=rec.get("betaald"),
                                         plv=kand["plv"])
        self._extra_bron()
        self._zelfcontrole()
        return self.klem()

    def _zelfcontrole(self):
        """Wat de registercheck zou afkeuren (de instantie staat onder een andere schrijfwijze of
        afkorting in het model), wordt niet gepland: dezelfde controle als scripts/registercheck.py."""
        def ok(r):
            rec = self.rs["records"][r["sleutel"]]
            pid = r["bron"][1]
            eind = [{"name": self.personen_rs[pid]["naam"], "ids": {(STELSEL, pid)}},
                    {"name": _org_naam(self, r["doel"]), "ids": set()}]
            reden = rechtspraak.controleer(self.rs, r["sleutel"], rec, r["type"], eind)
            if reden:
                self._mis(rec["soort"], rec, "registercheck zou afkeuren")
                if "relation_id" not in r:
                    self.tel[f"{r['type']}/{r['mechanisme']}"] -= 1
            return not reden
        self.relaties = [r for r in self.relaties if ok(r)]
        self.extra_bron = [r for r in self.extra_bron if ok(r)]
        nodig = {r["bron"][1] for r in self.relaties + self.extra_bron}
        self.personen_rs = {k: v for k, v in self.personen_rs.items() if k in nodig}
        nodig_org = {r["doel"][1] for r in self.relaties if r["doel"][0] == "nieuw"}
        self.nieuwe_orgs = {k: v for k, v in self.nieuwe_orgs.items() if k in nodig_org}

    def _extra_bron(self):
        """Een gepland verband dat al bestaat (zelfde paar, affiliatietype) wordt geen nieuw verband
        maar krijgt een extra argument met de recordregel als citaat."""
        blijven = []
        for r in self.relaties:
            p = self.personen_rs.get(r["bron"][1]) if r["bron"][0] == "persoon" else None
            s = p["bestaand"] if p else None
            t = r["doel"][1] if r["doel"][0] == "bestaand" else None
            bestaand = [x for x in self.bestaande_paren.get((min(s, t), max(s, t)), [])
                        if x[1] in AFFILIATIE] if s and t else []
            if not bestaand:
                blijven.append(r)
                continue
            rel_id, typ, status = sorted(bestaand, key=lambda x: (x[1] != r["type"], x[0]))[0]
            self.tel[f"{r['type']}/{r['mechanisme']}"] -= 1
            if (rel_id, r["sleutel"]) in self.al_geciteerd:
                self.tel["bestaand verband, dit record al geciteerd"] += 1
                continue
            self.extra_bron.append({**r, "relation_id": rel_id, "bestaand_type": typ, "bestaand_status": status})
            self.tel["bestaand verband: extra bron" + ("" if typ == r["type"] else f" (type {typ})")] += 1
        self.relaties = blijven


UITGESLOTEN = re.compile(r"^(rechtbank|gerechtshof|hoge raad der nederlanden|raad voor de rechtspraak|"
                         r"studiecentrum rechtspleging|ssr|nvvr|nederlandse vereniging voor rechtspraak|"
                         r"centrale raad van beroep|college van beroep voor het bedrijfsleven)\b")


class Indiener(tkm.Indiener):
    """Zoals de Kamerregisters, met rechters (externe id 'rechtspraak') in plaats van Kamerleden
    en een extra argument op een verband dat al bestaat."""

    def entiteiten(self):
        for pid, p in self.p.personen_rs.items():
            ids = [{"stelsel": STELSEL, "waarde": pid}]
            if p["bestaand"]:
                status, res = self.rest("POST", f"/api/entities/{p['bestaand']}/register", {"externe_ids": ids})
                self.tel["rechter gekoppeld" if status == 200 else f"rechter koppelen {status}"] += 1
                if status == 200:
                    self.ent[("persoon", pid)] = p["bestaand"]
                continue
            body = {"name": p["naam"], "type": "persoon", "description": p["beschrijving"], "externe_ids": ids}
            if p["rol"] and p["rol"] in self.p.rol:
                body["primary_role_id"] = self.p.rol[p["rol"]]
            status, res = self.rest("POST", "/api/entities", body)
            if status in (201, 409) and (res.get("id") or res.get("entity_id")):
                self.ent[("persoon", pid)] = res.get("id") or res.get("entity_id")
                self.tel["rechter nieuw" if status == 201 else "rechter bestond (externe id)"] += 1
            else:
                self.tel[f"rechter fout {status}"] += 1
                self.log(f"  ✗ {p['naam']}: {status} {res.get('error')}")
        self.p.personen = {}
        super().entiteiten()

    def extra_bronnen(self, bron_id: int):
        for r in self.p.extra_bron:
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": r["relation_id"], "claim": r["claim"], "stance": "supporting",
                "citations": [{"source_id": bron_id, "quote": r["regel"], "methode": "officieel_register_scrape",
                               "section": r["sleutel"], "page": f"{self.reg.BRON}/{self.p.uitgave}",
                               "context": self.reg.URL}]})
            self.tel["extra bron" if status == 201 else f"extra bron fout {status}"] += 1


# ── rapport ─────────────────────────────────────────────────────────────────
def rapport(plan: Plan, data: dict, top: int) -> dict:
    recs = list(data["records"].values())
    rechters = [r for r in recs if r["soort"] == "persoon"]
    neven = [r for r in recs if r["soort"] == "nevenfunctie"]
    lopend = [r for r in neven if r.get("huidig") and not r.get("tot")]
    kand = plan.kandidaten
    # lift per organisatiesoort: plaatsvervangers tegenover alle rechters (lopende nevenbetrekkingen)
    k_neven = [k for k in kand if k["sleutel"].startswith("nevenfunctie:")]
    n_alle, n_plv = len(k_neven), sum(1 for k in k_neven if k["plv"])
    per_soort = Counter(k["org_soort"].split("|")[0] for k in k_neven)
    per_soort_plv = Counter(k["org_soort"].split("|")[0] for k in k_neven if k["plv"])
    lift = {s: {"aantal": n, "plaatsvervangers": per_soort_plv[s],
                "lift_plaatsvervanger": round((per_soort_plv[s] / n_plv) / (n / n_alle), 2) if n_plv and n else None}
            for s, n in per_soort.most_common()}
    betaald = Counter((k["org_soort"].split("|")[0], plan.rs["records"][k["sleutel"]].get("betaald")) for k in k_neven)
    for s in lift:
        b = betaald[(s, "betaald")]
        lift[s]["aandeel_betaald"] = round(b / lift[s]["aantal"], 2)
    routine = Counter()
    for k in k_neven:
        routine[plan.rs["records"][k["sleutel"]]["instantie"]] += 1
    gelijktijdig_advocaat = sorted({plan.rs["records"][k["sleutel"]]["naam"] for k in k_neven
                                    if k["functie_soort"] == "advocaat" or k["org_soort"].startswith("advocatuur")})
    draaideur_adv = [k for k in kand if k["sleutel"].startswith("loopbaan:") and k["org_soort"].startswith("advocatuur")]
    gepland = sorted(plan.relaties, key=lambda r: -r.get("score", 0))
    onbekend_interessant = sorted([k for k in kand if not k["gepland"] and k["score"] >= DREMPEL_NIEUW],
                                  key=lambda k: -k["score"])
    return {
        "uitgave": plan.uitgave, "volledig": data.get("volledig"),
        "rechters_in_register": len(rechters),
        "rechters_plaatsvervanger": sum(1 for r in rechters if plaatsvervanger(r)),
        "nevenbetrekkingen": len(neven), "nevenbetrekkingen_lopend": len(lopend),
        "loopbaan_buiten_rechtspraak": sum(1 for r in recs if r["soort"] == "loopbaan"),
        "lift_per_organisatiesoort": lift,
        "meest_routinematige_instanties": routine.most_common(15),
        "rechters_met_lopende_advocatuur_nevenbetrekking": len(gelijktijdig_advocaat),
        "loopbaan_in_advocatuur": len(draaideur_adv),
        "rechters_met_loopbaan_in_advocatuur": len({plan.rs["records"][k["sleutel"]]["persoon_id"] for k in draaideur_adv}),
        "top": [{"score": r.get("score"), "type": r["type"], "mechanisme": r["mechanisme"],
                 "org_soort": r.get("org_soort"), "rechter": plan.personen_rs[r["bron"][1]]["naam"],
                 "organisatie": _org_naam(plan, r["doel"]), "nieuw": r["doel"][0] == "nieuw",
                 "sleutel": r["sleutel"], "citaat": r["regel"]} for r in gepland[:top]],
        "interessant_niet_gepland": [{"score": k["score"], "org_soort": k["org_soort"], "citaat": k["regel"],
                                      "reden": _reden(plan, k["sleutel"])} for k in onbekend_interessant[:30]],
    }


def _org_naam(plan: Plan, ref: tuple) -> str:
    if ref[0] == "nieuw":
        return plan.nieuwe_orgs[ref[1]]["naam"]
    return plan.org[ref[1]][0]


def _reden(plan: Plan, sleutel_r: str) -> str | None:
    regel = plan.rs["records"][sleutel_r]["regel"]
    return next((o["reden"] for o in plan.overgeslagen if o["tekst"] == regel), None)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave")
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--indienen", action="store_true")
    ap.add_argument("--haal", action="store_true", help="eerst een nieuwe uitgave ophalen (± 90 minuten)")
    a = ap.parse_args()
    if a.haal and not a.uitgave:
        rechtspraak.haal()
    data = rechtspraak.lees(rechtspraak.pad_van(a.uitgave) if a.uitgave else rechtspraak.uitgaven()[-1])
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(data, conn, koppelingen).maak()
    rap = rapport(plan, data, a.top)
    samenvatting = {
        "uitgave": plan.uitgave, "volledig": data.get("volledig"),
        "rechters_nieuw": sum(1 for p in plan.personen_rs.values() if not p["bestaand"]),
        "rechters_bestaand": sum(1 for p in plan.personen_rs.values() if p["bestaand"]),
        "nieuwe_organisaties": len(plan.nieuwe_orgs),
        "nieuwe_verbanden": len(plan.relaties),
        "bestaande_verbanden_extra_bron": len(plan.extra_bron),
        "telling": {k: v for k, v in sorted(plan.tel.items()) if v}}
    print(json.dumps(samenvatting, ensure_ascii=False, indent=1))
    rechtspraak.MAP.mkdir(parents=True, exist_ok=True)
    (rechtspraak.MAP / f"rapport_{plan.uitgave}.json").write_text(
        json.dumps({"samenvatting": samenvatting, **rap,
                    "nieuwe_organisatienamen": sorted(o["naam"] for o in plan.nieuwe_orgs.values()),
                    "extra_bron": [{"relation_id": r["relation_id"], "type": r["bestaand_type"],
                                    "citaat": r["regel"]} for r in plan.extra_bron]},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    for naam, inhoud in (("overgeslagen", plan.overgeslagen), ("koppelingen", plan.koppelingen)):
        (rechtspraak.MAP / f"{naam}_{plan.uitgave}.json").write_text(
            json.dumps(inhoud, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nTop {a.top} (score = organisatiesoort × functiesoort × bezoldiging × zeldzaamheid × in model):")
    for i, t in enumerate(rap["top"], 1):
        print(f"{i:>3}. {t['score']:>5}  {t['rechter']} — {t['organisatie']}{' (nieuw)' if t['nieuw'] else ''}"
              f"  [{t['type']}/{t['mechanisme']}, {t['org_soort']}]\n       “{t['citaat']}”")
    if not a.indienen:
        print(f"\n(droogloop — niets ingediend; rapport in {rechtspraak.MAP}/rapport_{plan.uitgave}.json)")
        return
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()), bron=rechtspraak, cluster=CLUSTER)
    bron_id = ind.bron()
    ind.entiteiten()
    ind.relaties(bron_id)
    ind.extra_bronnen(bron_id)
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
