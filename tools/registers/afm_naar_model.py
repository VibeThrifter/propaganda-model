#!/usr/bin/env python3
"""AFM-meldingenregisters → het model: eigendoms- en bestuursnetwerken (2026-10-20).

afm.py bewaart de uitgave (substantiële deelnemingen, bestuurders en commissarissen 5:48 Wft,
transacties leidinggevenden MAR 19). Dit script kiest wat telt en plant, zonder AI:

  1. Eigendom (register sd). Per paar houder → uitgevende instelling de meldingen op datum. Een
     reeks loopt van de melding waarmee de houder boven de laagste drempel kwam (3%, vóór
     2013-07-01 5%) tot de melding waarmee hij eronder zakte. Het verband volgt de laatste reeks:
     `active_from` = de datum van de eerste melding van die reeks (de datum waarop de
     meldingsplicht ontstond), `active_until` = de datum van de melding onder de drempel. Is de
     eerste melding een overgangsmelding (2006-11-01: start van het register; 2013-07-01: drempel
     naar 3%), dan noemt het register geen begin en blijft het leeg. Alleen een reëel belang telt
     (aandelen, geen opties/swaps/CFD's): een reeks waarin het reële belang nooit de drempel haalt
     (handelsposities van banken) is geen eigendom.
     Relatietype `eigendom` (bron = houder). Mechanisme: `strategische_zeggenschap` als de houder
     reëel stemrecht heeft van ≥ 20%, of ≥ 5% bij een houder met hooguit 5 meldingsplichtige
     belangen (een blokhouder); anders `systemisch_eigenaarschap` (de gespreide institutionele
     belegger, ook een actieve vermogensbeheerder met 10% in meerdere fondsen). Zeggenschap is
     stemrecht: een reëel kapitaalbelang zonder reëel stemrecht (certificaten zonder stemrecht,
     aandelen als zekerheid met een calloptie voor een ander: Intel → ASML 2012–2018, ING → Van
     Lanschot Kempen 2025) krijgt geen verband, alleen een regel in het rapport.
  2. Bestuur (registers mar en bc). Een melding bevestigt dat de persoon op die datum bestuurder of
     commissaris was; het begin noemt geen van beide registers (geen nep-begin: leeg, daarna
     'register_zonder_datum'). Nieuw verband `bestuurder` (richtingloos) alleen met een functie uit
     MAR 19 die bestuur of toezicht bij de instelling zelf is (afm.is_bestuursfunctie), een
     melding in de laatste 12 maanden (anders zou een open einde een vertrokken bestuurder als
     zittend tonen) en een instelling in het model. Mechanisme `commissarisbenoeming` (toezicht, of
     een niet nader genoemde zetel in een one-tier board: benoemd door de AvA) of
     `directiebenoeming` (uitvoerend: CEO, CFO, raad van bestuur, management/executive board).
     Een 5:48-melding (zonder functie) is alleen een extra argument op een bestaand verband.
     Familieleden en andere nauw gelieerden staan niet eens in de uitgave.
  3. Ruis. Passieve indexbeleggers (BlackRock, Vanguard, Norges, …) houden overal 3–5%. De score
     is belang × zeldzaamheid, zeldzaamheid = log2(aantal instellingen ÷ aantal instellingen waarin
     de houder een reëel belang meldde): zo staat een blokhouder in één onderneming bovenaan en
     een indexbelegger onderaan. Nieuwe verbanden alleen bij een instelling die al in het model
     staat; een nieuwe houder alleen als rechtspersoon met een strategisch belang (nooit een
     natuurlijk persoon: die koppelt alleen aan een persoon die al in het model staat); een
     indexbelegger die nog niet in het model staat komt er niet bij (alleen in het rapport).
  4. Bestaande verbanden (houder → instelling eigendom/zeggenschap/investering, of persoon —
     instelling bestuurder) krijgen de meldingen als extra argument: het begin van de reeks, de
     laatste en het einde; hooguit MAX_PER_VERBAND per run, nooit een sectie die er al staat.

Koppelen, nooit op naam alleen: externe id (kvk/lei, zodra die stelsels bestaan), de met de hand
nagelopen afm_koppelingen.json, of de naam uit het model als hele woorden met alleen een
rechtsvorm eromheen ('Koninklijke KPN N.V.' → KPN; geen 'Holding': Heineken Holding N.V. is niet
Heineken N.V.). Personen: achternaam + passende voorletters bij precies één persoon in het model
die de instelling al kent (verband of beschrijving), of afm_koppelingen.json. Staat er wel een
naamgenoot met passende voorletters in het model maar zonder band met de instelling, dan niets
(handmatig koppelen, nooit een dubbele knoop); anders een nieuwe knoop '<voorletters> <naam>'
(met '(<functie> <instelling>)' erachter als die naam al bestaat). Twee AFM-namen die naar
dezelfde houderknoop wijzen (APG-groep, APG Asset Management) worden één verband.

Rapport: data/registers/afm/analyse.md + analyse.json. Zelfcontrole: elk gepland argument gaat door
afm.controleer met de eindpunten zoals de registercheck ze ziet; de droogloop telt de missers.

Gebruik:
    python3 tools/registers/afm_naar_model.py                    # droogloop + rapport
    python3 tools/registers/afm_naar_model.py --haal --indienen  # (vergt 'afm' in registercheck.BRONNEN)
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
import afm  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ROOT, klem_relaties, ontleed_naam, schoon, sleutel  # noqa: E402
from naar_model import TOKEN, Rest  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:afm"
MECHS = ("strategische_zeggenschap", "systemisch_eigenaarschap", "certificaatconstructie", "commissarisbenoeming",
         "directiebenoeming")
ROLLEN = ("aandeelhouder", "belanghebbende", "administratiekantoor", "raad_van_commissarissen", "directie")
STRATEGISCH_ALTIJD = 20.0   # % reëel stemrecht: blokhouder, ook bij een brede houder (Delta Lloyd 30% Van Lanschot)
STRATEGISCH_SMAL = 5.0      # % reëel stemrecht bij een houder met hooguit SMAL belangen (Cevian, EXOR)
SMAL = 5                    # een houder met meer belangen is een gespreide belegger (Artisan: 9, Capital: 13+)
NIEUWE_HOUDER = 10.0        # % reëel: pas dan een nieuwe houderknoop
BESTUUR_RECENT = 365        # dagen: een nieuw bestuursverband alleen bij een recente melding
MAX_PER_VERBAND = 3
# een persoon met al zo'n band met de instelling (Thomas Leysen — dsm-firmenich #73 'personeel',
# "voorzitter") krijgt geen tweede, 'bestuurder'-verband naast dat feit: handmatig
ANDERE_BANDEN = ("personeel", "dienstverband", "adviseur", "lidmaatschap", "draaideur", "ambt")
TOP = 60
# Typen die een uitgevende instelling of houder kunnen zijn
ORG_TYPES = {"bedrijf", "mediaorganisatie", "platform", "vermogensbeheerder", "stichting", "ngo",
             "persbureau", "overheidsinstelling", "elite_netwerk", "omroep"}
INSTELLING_TYPES = {"bedrijf", "mediaorganisatie", "platform", "vermogensbeheerder", "persbureau"}
MEDIA_TYPES = {"mediaorganisatie", "platform", "omroep", "persbureau"}
# Woorden die naast een naam uit het model mogen staan: rechtsvormen en 'Koninklijke', geen
# 'Holding' of 'Nederland' (dat is vaak een andere vennootschap)
KWAL = {"the", "group", "groep", "bank", "b", "v", "n", "u", "a", "bv", "nv", "ua", "cooperatieve", "cooperatie",
        "koninklijke", "royal", "plc", "ltd", "limited", "inc", "incorporated", "corp", "corporation", "co", "company",
        "se", "sa", "s", "ag", "asa", "ab", "oyj", "spa", "p", "llc", "lp", "l", "gmbh", "kgaa", "de", "het"}
RECHTSVORM_HOUDER = [
    (re.compile(r"^Stichting\b|\bStichting$|^Stg\.?\s|\bFoundation\b|\bStiftung\b", re.I), "stichting"),
    (re.compile(r"^(Koninklijke\s+)?Vereniging\b", re.I), "ngo"),
    (re.compile(r"^Staat der Nederlanden$|\bState of\b|\bRepublic\b|\bKingdom\b|\bMinist", re.I), "overheidsinstelling"),
    (re.compile(r"\b(Asset Management|Investment Management|Investors|Capital Management|Advisors|Gestion|"
                r"Fund Management|Fondsen|Pension|Pensioen)\b", re.I), "vermogensbeheerder"),
    (re.compile(r"(?:^|\s)(N\.?V\.?|B\.?V\.?|SE|S\.?A\.?|AG|GmbH|plc|PLC|Ltd\.?|Limited|Inc\.?|LLC|L\.?P\.?|"
                r"Corp\.?|Corporation|Co\.?|ASA|AB|KGaA|S\.p\.A\.?|U\.?A\.?)$|^Co[öo]peratie", re.I), "bedrijf"),
]
# Houdersoorten die geen gewone aandeelhouder zijn
STAK = re.compile(r"administratie\s*kantoor|\bstak\b|trust ?office", re.I)
BESCHERMING = re.compile(r"^(stichting|stg\.?)\b.*\b(preferente|preference|continu[iï]teit|bescherming|prioriteit)", re.I)
NATUURLIJK = re.compile(r"^(?:[A-Z][a-z]?\.(?:\s?-?[A-Z][a-z]?\.)*|[A-Z]-[A-Z]\.|[A-Z])\s+\S")


def _jaar_dagen(a: str, b: str) -> int:
    return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days


def afm_persoonsnaam(rec: dict) -> str:
    """'W.H' + 'van' + 'Houwelingen' → 'W.H. van Houwelingen'; 'Wortmann - Kool' → 'Wortmann-Kool'."""
    letters = [t for t in re.split(r"[.\s]+", rec.get("voorletters") or "") if t]
    achter = re.sub(r"\s*-\s*", "-", rec.get("achternaam") or "")
    return schoon(f"{'.'.join(letters)}{'.' if letters else ''} {rec.get('tussenvoegsel') or ''} {achter}")


def natuurlijk_persoon(naam: str) -> bool:
    """'J.H.H. de Mol', 'V. Bolloré', 'W.H. Gates III' — voorletters vooraan, geen rechtsvorm
    (ook niet vooraan: 'N.V. Sunderland')."""
    if re.match(r"^(N\.?V\.?|B\.?V\.?|S\.?A\.?)\s", naam or ""):
        return False
    return bool(NATUURLIJK.match(naam or "")) and not any(p.search(naam) for p, _t in RECHTSVORM_HOUDER)


def houder_type(naam: str) -> str | None:
    for patroon, typ in RECHTSVORM_HOUDER:
        if patroon.search(naam or ""):
            return typ
    return None


def drempel_op(datum: str) -> float:
    return afm.DREMPEL if datum >= "2013-07-01" else 5.0


def belang(rec: dict) -> dict:
    """Totalen en reëel belang (aandelen) van één melding, in procenten."""
    k, s = rec["kapitaal"], rec["stemrecht"]
    p = afm.procent
    kap_r = (p(k["reeel_rechtstreeks"]) or 0) + (p(k["reeel_middellijk"]) or 0)
    stem_r = (p(s["reeel_rechtstreeks"]) or 0) + (p(s["reeel_middellijk"]) or 0)
    return {"kap": p(k["totaal"]) or 0.0, "stem": p(s["totaal"]) or 0.0, "kap_reeel": round(kap_r, 2),
            "stem_reeel": round(stem_r, 2), "reeel": round(max(kap_r, stem_r), 2),
            "totaal": max(p(k["totaal"]) or 0.0, p(s["totaal"]) or 0.0)}


def reeksen(recs: list[dict]) -> list[dict]:
    """Meldingen (op datum) → reeksen boven de drempel: {start, eind, recs, max_reeel, laatste}."""
    uit, cur = [], None
    for r in recs:
        b = belang(r)
        boven = b["totaal"] >= drempel_op(r["datum"])
        if boven:
            if cur is None:
                cur = {"start": r, "eind": None, "recs": []}
            cur["recs"].append(r)
        else:
            if cur is None:   # een daling zonder eerdere melding (van vóór het register)
                uit.append({"start": None, "eind": r, "recs": [r]})
            else:
                cur["eind"] = r
                cur["recs"].append(r)
                uit.append(cur)
                cur = None
    if cur:
        uit.append(cur)
    for x in uit:
        x["max_reeel"] = max(belang(r)["reeel"] for r in x["recs"])
        x["laatste"] = x["recs"][-1]
    return uit


class Plan(tkm.Plan):
    def __init__(self, data: dict, conn: sqlite3.Connection, koppelingen: dict | None = None):
        super().__init__({"uitgave": data["uitgave"], "personen": {}, "records": {}}, conn, koppelingen)
        self.data, self.records = data, data["records"]
        self.mech.update(self._ids("mechanisms", MECHS))
        self.rol.update(self._ids("roles", ROLLEN))
        self.kwalificaties = KWAL
        self.k = afm.koppelingen()
        self.k_soorten = afm.koppelingen().get("houdersoorten", {})
        self.ext = {(s, w): e for e, s, w in conn.execute(
            "SELECT entity_id, stelsel, waarde FROM externe_ids WHERE stelsel IN ('kvk', 'lei')")}
        self.eigendom: dict[tuple[int, int], int] = {}
        self.bestuur: dict[tuple[int, int], int] = {}
        self.andere_band: dict[tuple[int, int], tuple[int, str]] = {}
        self.buren: dict[int, set[int]] = defaultdict(set)
        for rid, s, t, typ, van in conn.execute("""
                SELECT id, source_id, target_id, relation_type, active_from FROM relations
                WHERE NOT vervangen AND status <> 'afgewezen'"""):
            if typ in afm.EIGENDOMSTYPES:
                self.eigendom.setdefault((s, t), rid)
            if typ == "bestuurder":
                self.bestuur.setdefault((min(s, t), max(s, t)), rid)
            elif typ in ANDERE_BANDEN:
                self.andere_band.setdefault((min(s, t), max(s, t)), (rid, typ))
            self.buren[s].add(t)
            self.buren[t].add(s)
        self.rel_van = {rid: (van, tot) for rid, van, tot in conn.execute(
            "SELECT id, active_from, active_until FROM relations")}
        self.geciteerd: dict[int, set[str]] = defaultdict(set)
        for rid, sec in conn.execute("""
                SELECT a.relation_id, c.section FROM citations c JOIN arguments a ON a.id = c.argument_id
                WHERE c.page LIKE 'afm/%' AND a.relation_id IS NOT NULL"""):
            self.geciteerd[rid].add(sec)
        self.personen_model: dict[str, list[dict]] = defaultdict(list)
        for i, naam, beschr in conn.execute("""
                SELECT id, name, COALESCE(description, '') FROM entities
                WHERE type = 'persoon' AND NOT vervangen AND status <> 'afgewezen'"""):
            n = ontleed_naam(tkm.zonder_haakjes(naam).split(",")[0])
            c = {"id": i, "naam": naam, "beschrijving": beschr,
                 "letters": re.sub(r"[^a-z]", "", (n["voorletters"] or "").lower()),
                 "voornaam": sleutel(n["roepnaam"] or n["voornamen"] or "")}
            achter = n["achternaam"] or ""
            for k in {sleutel(achter), sleutel(achter.split("-")[0])} - {""}:
                self.personen_model[k].append(c)
        self.alle_namen = {sleutel(n) for (n,) in conn.execute("SELECT name FROM entities")}
        self.org_cache: dict[tuple[str, str], tuple] = {}
        self.koppeling_log: list[dict] = []
        self.analyse: list[dict] = []
        self.bestuur_analyse: list[dict] = []
        self.argumenten: list[dict] = []     # {verband: rid | ('nieuw', key), rec, claim}
        self.nieuwe_verbanden: dict[tuple, dict] = {}
        self.nieuwe_houders: dict[str, dict] = {}
        self.nieuwe_personen: dict[str, dict] = {}
        self.datumverschil: list[dict] = []
        # planregels van bestaande verbanden die de uitgave bevestigt (voor de looptijdstap van de
        # registers: registers_sync.geplande_relaties leest plan.relaties = nieuw + bestaand)
        self.relaties_bestaand: list[dict] = []

    # ── koppelen ───────────────────────────────────────────────────────────
    def koppel_org(self, naam: str, soort: str, ids=()) -> tuple[int | None, str]:
        """AFM-naam → (entiteit-id, hoe) of (None, '')."""
        ck = (soort, sleutel(naam))
        if ck in self.org_cache:
            return self.org_cache[ck]
        uit = (None, "")
        for i in ids:
            if i[1] and i in self.ext:
                uit = (self.ext[i], f"externe id {i[0]}")
                break
        else:
            hand = self.k.get(soort, {}).get(sleutel(naam))
            if hand:
                uit = (hand, "afm_koppelingen.json") if hand in self.org else (None, "")
            else:
                g = self._naam(naam)
                if g and g[0] > 0 and self.org[g[0]][1] in ORG_TYPES:
                    uit = g
        self.org_cache[ck] = uit
        if uit[0]:
            self.koppeling_log.append({"soort": soort, "afm": naam, "model": self.org[uit[0]][0], "id": uit[0],
                                       "hoe": uit[1]})
        return uit

    def _naam(self, naam: str) -> tuple[int, str] | None:
        """De naam uit het model als hele woorden, met eromheen alleen rechtsvormwoorden (KWAL):
        'Koninklijke KPN N.V.' → KPN, 'BlackRock, Inc.' → BlackRock; niet 'Heineken Holding N.V.'
        (Holding is een andere vennootschap) en niet 'ING Research' (geen rechtsvorm)."""
        s = tkm._zonder_lidwoord(sleutel(naam))
        for k in (s, sleutel(naam)):
            if k in self.org_index:
                return self.org_index[k], "naam (exact)"
        woorden, beste = s.split(), None
        for i, w in enumerate(woorden):
            for kw, eid in self.op_eerste_woord.get(w, []):
                if woorden[i:i + len(kw)] != kw:
                    continue
                rest = woorden[:i] + woorden[i + len(kw):]
                if all(r in KWAL for r in rest) and (beste is None or len(kw) > len(beste[0])):
                    beste = (kw, eid)
        return (beste[1], "naam + rechtsvorm") if beste else None

    def persoon(self, rec: dict, org_id: int) -> tuple[int | None, str]:
        pk = afm.persoonsleutel(rec)
        hand = self.k.get("personen", {}).get(sleutel(pk))
        if hand:
            return hand, "afm_koppelingen.json"
        letters = pk.split("|")[1]
        if not letters:
            return None, ""
        kand = {c["id"]: c for c in self.personen_model.get(sleutel(rec.get("achternaam") or ""), [])}.values()
        passend = [c for c in kand if (c["letters"] and (c["letters"].startswith(letters) or letters.startswith(c["letters"])))
                   or (not c["letters"] and c["voornaam"][:1] == letters[:1])]
        bekend = [c for c in passend if org_id in self.buren.get(c["id"], set())
                  or tkm.namen_van(self.org[org_id][0])[0] in sleutel(c["beschrijving"])]
        if len(bekend) == 1:
            return bekend[0]["id"], "voorletters + achternaam, de instelling al verbonden of genoemd"
        return None, ("kandidaat zonder verband met de instelling" if passend else "")

    # ── eigendom ───────────────────────────────────────────────────────────
    def eigendommen(self):
        sd = sorted((r for r in self.records.values() if r["register"] == "sd"),
                    key=lambda r: (r["datum"], int(r["meldingid"]) if r["meldingid"].isdigit() else 0))
        self.tel["sd: meldingen"] = len(sd)
        inst_alle = {sleutel(r["uitgevende_instelling"]) for r in sd}
        per_paar: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for r in sd:
            per_paar[(sleutel(r["meldingsplichtige"]), sleutel(r["uitgevende_instelling"]))].append(r)
        # breedte: in hoeveel instellingen meldde de houder ooit een reëel belang boven de drempel
        breedte: Counter = Counter()
        paren = {}
        for (h, i), recs in per_paar.items():
            rk = reeksen(recs)
            paren[(h, i)] = rk
            if any(x["max_reeel"] >= drempel_op(x["recs"][0]["datum"]) for x in rk):
                breedte[h] += 1
        n_inst = len(inst_alle)
        self.tel["sd: instellingen"] = n_inst
        self.tel["sd: houders"] = len({h for h, _ in per_paar})
        self.tel["sd: paren houder-instelling"] = len(per_paar)
        for (h, i), rk in paren.items():
            laatste_reeks = rk[-1]
            recs = per_paar[(h, i)]
            rec0 = recs[-1]
            max_r = laatste_reeks["max_reeel"]
            if max_r < afm.DREMPEL:
                self.tel["paar: alleen potentieel (opties, swaps, CFD's)"] += 1
                continue
            br = max(breedte[h], 1)
            zeldzaam = math.log2(n_inst / br)
            start = laatste_reeks["start"]
            eind = laatste_reeks["eind"]
            begin = start["datum"] if start else None
            overgang = afm.OVERGANGSDAGEN.get(begin) if begin else "melding van vóór het register"
            houdernaam = rec0["meldingsplichtige"]
            inst_id, inst_hoe = self.koppel_org(rec0["uitgevende_instelling"], "ondernemingen", [("kvk", rec0.get("kvk") or "")])
            persoon = natuurlijk_persoon(houdernaam)
            if persoon:
                houder_id, houder_hoe = (self.persoon({**afm.mar_naam(houdernaam), "persoon": houdernaam}, inst_id)
                                         if inst_id else (None, ""))
            else:
                houder_id, houder_hoe = self.koppel_org(houdernaam, "houders")
            kap_r = max(belang(r)["kap_reeel"] for r in laatste_reeks["recs"])
            stem_r = max(belang(r)["stem_reeel"] for r in laatste_reeks["recs"])
            strategisch = stem_r >= STRATEGISCH_ALTIJD or (br <= SMAL and stem_r >= STRATEGISCH_SMAL)
            soort = self.k_soorten.get(sleutel(houdernaam)) or (
                "administratiekantoor" if STAK.search(houdernaam) else
                "beschermingsstichting" if BESCHERMING.search(houdernaam) else
                "overheid" if houder_type(houdernaam) == "overheidsinstelling" else None)
            mech = ("certificaatconstructie" if soort == "administratiekantoor" else
                    "strategische_zeggenschap" if strategisch else "systemisch_eigenaarschap")
            a = {"houder": houdernaam, "houder_id": houder_id, "houder_model": self.org[houder_id][0] if houder_id and houder_id in self.org else (
                    self._persoonsnaam(houder_id) if houder_id else None), "houder_hoe": houder_hoe,
                 "natuurlijk_persoon": persoon,
                 "instelling": rec0["uitgevende_instelling"], "instelling_id": inst_id,
                 "instelling_model": self.org[inst_id][0] if inst_id else None,
                 "instelling_type": self.org[inst_id][1] if inst_id else None,
                 "max_reeel": max_r, "laatste_totaal": belang(laatste_reeks["laatste"])["totaal"],
                 "breedte": br, "zeldzaamheid": round(zeldzaam, 2), "score": round(max_r * zeldzaam, 2),
                 "mechanisme": mech, "soort": soort, "kap_reeel": kap_r, "stem_reeel": stem_r,
                 "begin": None if overgang else begin, "begin_melding": begin, "overgang": overgang,
                 "einde": eind["datum"] if eind else None, "reeksen": len(rk),
                 "eerdere_reeksen": [(x["start"]["datum"] if x["start"] else None, x["eind"]["datum"] if x["eind"] else None)
                                     for x in rk[:-1]],
                 "meldingen": len(recs), "laatste_melding": recs[-1]["datum"],
                 "citaat": (start or laatste_reeks["laatste"])["regel"], "status": None}
            self.analyse.append(a)
            self._kies_eigendom(a, laatste_reeks, rec0)
        self.analyse.sort(key=lambda a: (-a["score"], -a["max_reeel"]))

    def _persoonsnaam(self, eid):
        r = self.conn.execute("SELECT name FROM entities WHERE id = ?", (eid,)).fetchone()
        return r[0] if r else None

    def _kies_eigendom(self, a: dict, reeks: dict, rec0: dict):
        if not a["instelling_id"]:
            a["status"] = "instelling niet in het model"
            self.tel["paar: instelling niet in het model"] += 1
            return
        if a["instelling_type"] not in INSTELLING_TYPES:
            a["status"] = f"instelling is {a['instelling_type']}"
            self.tel["paar: instelling geen onderneming"] += 1
            return
        if a["soort"] == "beschermingsstichting":
            a["status"] = "beschermingsstichting (theoriegat: geen mechanisme)"
            self.tel["paar: beschermingsstichting (theoriegat)"] += 1
            return
        bron = ("bestaand", a["houder_id"]) if a["houder_id"] else None
        if bron is None and a["soort"] == "overheid":
            a["status"] = "staatsdeelneming, staat niet als knoop in het model (handmatig)"
            self.tel["paar: staatsdeelneming zonder knoop"] += 1
            return
        if bron and a["houder_id"] == a["instelling_id"]:
            a["status"] = "eigen aandelen"
            self.tel["paar: eigen aandelen (inkoop)"] += 1
            return
        if a["soort"] != "administratiekantoor" and a["stem_reeel"] < afm.DREMPEL:
            a["status"] = "kapitaal zonder reëel stemrecht (certificaten, zekerheid of optie): rapport"
            self.tel["paar: kapitaal zonder reëel stemrecht"] += 1
            return
        if bron is None:
            if a["natuurlijk_persoon"]:
                a["status"] = "natuurlijk persoon niet in het model (nooit nieuw)"
                self.tel["paar: natuurlijk persoon, niet in het model"] += 1
                return
            typ = "stichting" if a["soort"] == "administratiekantoor" else houder_type(a["houder"])
            if (a["mechanisme"] == "systemisch_eigenaarschap" or a["max_reeel"] < NIEUWE_HOUDER or not typ
                    or typ == "overheidsinstelling"):
                a["status"] = ("houder niet in het model (systemisch: alleen rapport)"
                               if a["mechanisme"] == "systemisch_eigenaarschap" else
                               "houder niet in het model (onder de drempel of zonder rechtsvorm)")
                self.tel["paar: houder niet in het model, niet nieuw"] += 1
                return
            k = sleutel(a["houder"])
            if k in self.alle_namen:
                a["status"] = "naam bestaat al als andere knoop (handmatig nalopen)"
                self.tel["paar: nieuwe houder botst met bestaande naam"] += 1
                return
            self.nieuwe_houders.setdefault(k, {"naam": schoon(a["houder"]), "type": typ,
                                               "rol": "administratiekantoor" if a["soort"] == "administratiekantoor"
                                               else "aandeelhouder",
                                               "beschrijving": "Meldingsplichtige in het AFM-register substantiële deelnemingen."})
            bron = ("nieuw", k)
        doel = ("bestaand", a["instelling_id"])
        rid = self.eigendom.get((bron[1], doel[1])) if bron[0] == "bestaand" else None
        if rid is None and bron[0] == "bestaand" and (doel[1], bron[1]) in self.eigendom:
            a["status"] = "omgekeerd verband bestaat (handmatig nalopen)"
            self.tel["paar: omgekeerd verband bestaat"] += 1
            return
        recs = [reeks["start"]] if reeks["start"] else []
        recs += [r for r in (reeks["laatste"], reeks["eind"]) if r and r not in recs]
        if rid:
            a["status"] = "versterkt"
            self.tel["paar: bestaand verband, extra argumenten"] += 1
            van, tot = self.rel_van.get(rid, (None, None))
            if a["begin"] and van and van[:4] != a["begin"][:4]:
                self.datumverschil.append({"verband": rid, "houder": a["houder_model"], "instelling": a["instelling_model"],
                                           "model_begin": van, "afm_begin": a["begin"], "citaat": reeks["start"]["regel"]})
            nieuw = [r for r in recs if r["sleutel"] not in self.geciteerd.get(rid, set())][:MAX_PER_VERBAND]
            for r in nieuw:
                self.argumenten.append({"verband": rid, "rec": r, "type": "eigendom", "bron": bron, "doel": doel,
                                        "claim": self._claim_sd(r, a)})
            typ = self.conn.execute("SELECT relation_type FROM relations WHERE id = ?", (rid,)).fetchone()[0]
            self.relaties_bestaand.append({"bron": bron, "doel": doel, "type": typ, "sleutel": recs[0]["sleutel"],
                                           "start": a["begin"], "eind": a["einde"], "zonder_begin": a["overgang"]})
            self.tel["argumenten: extra op bestaand eigendom"] += len(nieuw)
            return
        a["status"] = "nieuw"
        self.tel[f"paar: nieuw verband ({a['mechanisme']})"] += 1
        key = (bron, doel, "eigendom")
        v = {"bron": bron, "doel": doel, "type": "eigendom", "mechanisme": a["mechanisme"],
             "functie": None, "start": a["begin"], "eind": a["einde"],
             "sleutel": recs[0]["sleutel"], "regel": recs[0]["regel"],
             "zonder_begin": a["overgang"], "score": a["score"]}
        oud = self.nieuwe_verbanden.get(key)
        if oud:
            # twee AFM-namen voor dezelfde knoop (APG-groep en APG Asset Management): één verband van
            # het vroegste begin (leeg als één van beide geen begin noemt) tot het laatste einde
            self.tel["paar: tweede AFM-naam voor hetzelfde verband"] += 1
            eerst = min((oud, v), key=lambda x: (x["start"] is not None, x["start"] or ""))
            hoogst = max((oud, v), key=lambda x: x["score"])
            v = {**hoogst, "start": eerst["start"], "zonder_begin": eerst["zonder_begin"],
                 "sleutel": eerst["sleutel"], "regel": eerst["regel"],
                 "eind": None if oud["eind"] is None or v["eind"] is None else max(oud["eind"], v["eind"])}
        self.nieuwe_verbanden[key] = v
        for r in recs[:MAX_PER_VERBAND]:
            self.argumenten.append({"verband": key, "rec": r, "type": "eigendom", "bron": bron, "doel": doel,
                                    "claim": self._claim_sd(r, a)})
        self.tel["argumenten: op nieuw eigendom"] += len(recs[:MAX_PER_VERBAND])

    @staticmethod
    def _claim_sd(r: dict, a: dict) -> str:
        houder = a["houder_model"] or schoon(a["houder"])
        return (f"Volgens het AFM-register substantiële deelnemingen had {houder} op {r['datum']} een "
                f"kapitaalbelang van {r['kapitaal']['totaal']} en {r['stemrecht']['totaal']} van de stemrechten in "
                f"{a['instelling_model']} (melding {r['meldingid']}).")

    # ── bestuur ────────────────────────────────────────────────────────────
    def besturen(self):
        groepen: dict[tuple[str, int], list[dict]] = defaultdict(list)
        for r in self.records.values():
            if r["register"] not in ("bc", "mar"):
                continue
            self.tel[f"{r['register']}: meldingen"] += 1
            if not r.get("achternaam") or not re.sub(r"[^a-z]", "", sleutel(r.get("voorletters") or "")):
                self.tel[f"{r['register']}: geen voorletters"] += 1
                continue
            if r["register"] == "mar":
                r = {**r, "_soort": afm.is_bestuursfunctie(r["functie"], r["uitgevende_instelling"])}
                if not r["_soort"]:
                    self.tel["mar: geen bestuur of toezicht (overgeslagen)"] += 1
                    continue
            inst_id, _hoe = self.koppel_org(r["uitgevende_instelling"], "ondernemingen", [("lei", r.get("lei") or "")])
            if not inst_id or self.org[inst_id][1] not in INSTELLING_TYPES:
                self.tel[f"{r['register']}: instelling niet in het model"] += 1
                continue
            groepen[(afm.persoonsleutel(r), inst_id)].append(r)
        # concentratie: dezelfde persoonsleutel bij meer instellingen in het model
        conc: dict[str, set[int]] = defaultdict(set)
        for (pk, inst), recs in groepen.items():
            conc[pk].add(inst)
        uitgave = self.uitgave
        for (pk, inst), recs in groepen.items():
            recs.sort(key=lambda r: r["datum"])
            mar = [r for r in recs if r["register"] == "mar"]
            laatste = recs[-1]
            pid, hoe = self.persoon(laatste, inst)
            soort = (mar[-1]["_soort"] if mar else None)
            uitvoerend = bool(mar) and soort == "bestuurder" and re.search(
                r"\b(ceo|cfo|coo|chief|executive (board|director)|management board|raad van bestuur|bestuurder|"
                r"statutair|managing director)\b", mar[-1]["functie"], re.I) and not re.search(r"non[- ]?exec", mar[-1]["functie"], re.I)
            mech = "directiebenoeming" if uitvoerend else "commissarisbenoeming"
            recent = _jaar_dagen(laatste["datum"], uitgave) <= BESTUUR_RECENT
            b = {"persoon": laatste["persoon"], "persoonsleutel": pk, "persoon_id": pid, "koppeling": hoe,
                 "instelling": self.org[inst][0], "instelling_id": inst, "functie": mar[-1]["functie"] if mar else None,
                 "mechanisme": mech, "meldingen": len(recs), "eerste": recs[0]["datum"], "laatste": laatste["datum"],
                 "recent": recent, "instellingen_in_model": len(conc[pk]), "media": self.org[inst][1] in MEDIA_TYPES,
                 "citaat": (mar[-1] if mar else laatste)["regel"], "status": None}
            self.bestuur_analyse.append(b)
            rid = self.bestuur.get((min(pid, inst), max(pid, inst))) if pid else None
            kies = sorted({r["sleutel"]: r for r in [recs[0], (mar[-1] if mar else None), laatste] if r}.values(),
                          key=lambda r: r["datum"])
            if rid:
                b["status"] = "versterkt"
                self.tel["bestuur: bestaand verband, extra argumenten"] += 1
                nieuw = [r for r in kies if r["sleutel"] not in self.geciteerd.get(rid, set())][:MAX_PER_VERBAND]
                for r in nieuw:
                    self.argumenten.append({"verband": rid, "rec": r, "type": "bestuurder",
                                            "bron": ("bestaand", pid), "doel": ("bestaand", inst),
                                            "claim": self._claim_bestuur(r, self._persoonsnaam(pid), self.org[inst][0])})
                self.tel["argumenten: extra op bestaand bestuur"] += len(nieuw)
                self.relaties_bestaand.append({"bron": ("bestaand", pid), "doel": ("bestaand", inst), "type": "bestuurder",
                                               "sleutel": kies[0]["sleutel"], "start": None, "eind": None,
                                               "zonder_begin": "het register noemt geen begin van de functie"})
                continue
            ander = self.andere_band.get((min(pid, inst), max(pid, inst))) if pid else None
            if ander:
                b["status"] = f"al een band van een ander type (#{ander[0]} {ander[1]}): handmatig"
                self.tel["bestuur: al een band van een ander type (handmatig)"] += 1
                continue
            if not mar:
                b["status"] = "alleen 5:48 (geen functie): rapport"
                self.tel["bestuur: alleen 5:48, geen functie"] += 1
                continue
            if not recent:
                b["status"] = "laatste melding ouder dan 12 maanden: rapport"
                self.tel["bestuur: niet recent (einde onbekend)"] += 1
                continue
            if not pid and hoe:
                b["status"] = "naamgenoot in het model zonder verband met de instelling: handmatig koppelen"
                self.tel["bestuur: naamgenoot in het model (handmatig)"] += 1
                continue
            if pid:
                bron = ("bestaand", pid)
                naam = self._persoonsnaam(pid)
            else:
                naam = afm_persoonsnaam(laatste)
                if sleutel(naam) in self.alle_namen:
                    naam = f"{naam} ({mar[-1]['functie'][:60]} {self.org[inst][0]})"
                self.nieuwe_personen.setdefault(pk, {"naam": naam, "rol": "directie" if uitvoerend else "raad_van_commissarissen",
                                                     "beschrijving": f"Bestuurder of commissaris van {self.org[inst][0]} volgens de AFM-registers."})
                bron = ("persoon", pk)
                naam = self.nieuwe_personen[pk]["naam"]
            b["status"] = "nieuw" + ("" if pid else " (nieuwe persoon)")
            self.tel[f"bestuur: nieuw verband ({mech})" + ("" if pid else ", nieuwe persoon")] += 1
            key = (bron, ("bestaand", inst), "bestuurder")
            self.nieuwe_verbanden[key] = {"bron": bron, "doel": ("bestaand", inst), "type": "bestuurder",
                                          "mechanisme": mech, "functie": mar[-1]["functie"][:200], "start": None,
                                          "eind": None, "sleutel": mar[-1]["sleutel"], "regel": mar[-1]["regel"],
                                          "zonder_begin": "het register noemt geen begin van de functie",
                                          "score": 0}
            gekozen = [x for x in kies if x["register"] == "mar" or x is laatste][:MAX_PER_VERBAND]
            for r in gekozen:
                self.argumenten.append({"verband": key, "rec": r, "type": "bestuurder", "bron": bron,
                                        "doel": ("bestaand", inst), "claim": self._claim_bestuur(r, naam, self.org[inst][0])})
            self.tel["argumenten: op nieuw bestuur"] += len(gekozen)
        self.bestuur_analyse.sort(key=lambda b: (-b["instellingen_in_model"], not b["media"], b["status"] or "", b["instelling"]))

    @staticmethod
    def _claim_bestuur(r: dict, persoon: str, instelling: str) -> str:
        if r["register"] == "mar":
            return (f"Volgens het AFM-register transacties leidinggevenden (MAR art. 19) was {persoon} op {r['datum']} "
                    f"{r['functie']} bij {instelling} (melding {r['meldingid']}).")
        return (f"Volgens het AFM-register bestuurders en commissarissen (art. 5:48 Wft) deed {persoon} op {r['datum']} "
                f"als bestuurder of commissaris van {instelling} een melding (melding {r['meldingid']}).")

    # ── klemmen, zelfcontrole ──────────────────────────────────────────────
    def _bestaan_van(self, ref) -> tuple:
        soort, w = ref
        if soort == "bestaand":
            return self.ent_bestaan.get(w, (None, None))
        return None, None

    def klem(self):
        lijst = list(self.nieuwe_verbanden.values())
        klem_relaties(lijst, self._bestaan_van, self.tel)
        self.relaties = lijst + self.relaties_bestaand
        return self

    def eindpunt(self, ref) -> dict:
        """Het eindpunt zoals de registercheck het na indienen ziet (id, naam, type, externe ids)."""
        soort, w = ref
        if soort == "bestaand":
            rij = self.conn.execute("SELECT id, name, type FROM entities WHERE id = ?", (w,)).fetchone()
            ids = {(s, v) for s, v in self.conn.execute(
                "SELECT stelsel, waarde FROM externe_ids WHERE entity_id = ?", (w,))}
            return {"id": rij[0], "name": rij[1], "type": rij[2], "ids": ids}
        if soort == "nieuw":
            o = self.nieuwe_houders[w]
            return {"id": -1, "name": o["naam"], "type": o["type"], "ids": set()}
        p = self.nieuwe_personen[w]
        return {"id": -2, "name": p["naam"], "type": "persoon", "ids": set()}

    def zelfcontrole(self) -> list[dict]:
        missers = []
        for x in self.argumenten:
            rec = afm.record(self.uitgave, x["rec"]["sleutel"])
            if rec is None or schoon(rec["regel"]) != schoon(x["rec"]["regel"]):
                missers.append({"sleutel": x["rec"]["sleutel"], "reden": "record of regel wijkt af"})
                continue
            eind = [self.eindpunt(x["bron"]), self.eindpunt(x["doel"])]
            reden = afm.controleer(self.data, rec["sleutel"], rec, x["type"], eind)
            if reden:
                missers.append({"sleutel": rec["sleutel"], "reden": reden, "eindpunten": [e["name"] for e in eind]})
        self.tel["zelfcontrole: argumenten"] = len(self.argumenten)
        self.tel["zelfcontrole: missers"] = len(missers)
        return missers

    def maak(self):
        self.eigendommen()
        self.besturen()
        return self.klem()

    # ── rapport ────────────────────────────────────────────────────────────
    def rapport(self) -> str:
        t = self.tel
        r = ["# AFM-registers: eigendoms- en bestuursnetwerk", "",
             f"Uitgave {self.uitgave}. Substantiële deelnemingen: {t['sd: meldingen']} meldingen, "
             f"{t['sd: instellingen']} instellingen, {t['sd: houders']} houders, {t['sd: paren houder-instelling']} paren.", "",
             "Score = hoogste reële belang (%) in de laatste reeks × zeldzaamheid; zeldzaamheid = "
             "log2(instellingen ÷ instellingen waarin de houder een reëel belang meldde). Een indexbelegger "
             "die overal 3–5% houdt, scoort zo laag; een blokhouder in één onderneming hoog.", "",
             "## Eigendom bij instellingen in het model", "",
             "| # | houder | instelling | reëel max | breedte | score | mechanisme | begin | einde | status |",
             "|---|---|---|---|---|---|---|---|---|---|"]
        rijen = [a for a in self.analyse if a["instelling_id"]]
        for i, a in enumerate(rijen[:TOP], 1):
            r.append(f"| {i} | {a['houder']}{' → ' + a['houder_model'] if a['houder_model'] else ''} | {a['instelling_model']} | "
                     f"{a['max_reeel']}% | {a['breedte']} | {a['score']} | {a['mechanisme']} | "
                     f"{a['begin'] or ('— (' + a['overgang'] + ')' if a['overgang'] else '—')} | {a['einde'] or ''} | {a['status']} |")
        r += ["", "## Hoogste scores bij instellingen die (nog) niet in het model staan", "",
              "| # | houder | instelling | reëel max | breedte | score |", "|---|---|---|---|---|---|"]
        for i, a in enumerate([a for a in self.analyse if not a["instelling_id"] and not a["natuurlijk_persoon"]][:30], 1):
            r.append(f"| {i} | {a['houder']} | {a['instelling']} | {a['max_reeel']}% | {a['breedte']} | {a['score']} |")
        breed = Counter()
        for a in self.analyse:
            breed[a["houder"]] = max(breed[a["houder"]], a["breedte"])
        r += ["", "## Breedste houders (ruis: systemisch, laag in de score)", ""]
        r += [f"- {h}: reëel belang in {n} instellingen" for h, n in breed.most_common(15)]
        r += ["", "## Bestuur bij instellingen in het model", "",
              "| persoon | instelling | functie | laatste melding | in model bij # instellingen | koppeling | status |",
              "|---|---|---|---|---|---|---|"]
        for b in self.bestuur_analyse[:TOP]:
            r.append(f"| {b['persoon']} | {b['instelling']} | {b['functie'] or '(5:48)'} | {b['laatste']} | "
                     f"{b['instellingen_in_model']} | {b['koppeling'] or '—'} | {b['status']} |")
        if self.datumverschil:
            r += ["", "## Begin in het model wijkt af van de eerste AFM-melding", ""]
            r += [f"- #{d['verband']} {d['houder']} → {d['instelling']}: model {d['model_begin']}, AFM {d['afm_begin']}"
                  for d in self.datumverschil]
        return "\n".join(r) + "\n"


class Indiener:
    """Onder `register-import`: bron per uitgave, nieuwe houders en personen, nieuwe verbanden,
    dan elk argument met de recordregel als citaat."""

    def __init__(self, plan: Plan, rest, log=print):
        self.p, self.rest, self.log = plan, rest, log
        self.ent: dict[tuple, int] = {}
        self.verbanden: dict[tuple, int] = {}
        self.bron_id: int | None = None
        self.tel = Counter()

    def bron(self) -> int:
        if self.bron_id is None:
            status, res = self.rest("POST", "/api/sources", {
                "title": afm.TITEL.format(uitgave=self.p.uitgave), "source_type": "dataset",
                "publisher": afm.UITGEVER, "date_published": self.p.uitgave, "cluster_key": CLUSTER,
                "location": {"type": "url", "value": afm.URL},
                "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
            if status not in (200, 201):
                raise SystemExit(f"bron registreren faalde: {status} {res}")
            self.bron_id = res["id"]
        return self.bron_id

    def entiteiten(self):
        for k, o in self.p.nieuwe_houders.items():
            status, res = self.rest("POST", "/api/entities", {
                "name": o["naam"], "type": o["type"], "primary_role_id": self.p.rol[o["rol"]],
                "description": o["beschrijving"]})
            if status == 201:
                self.ent[("nieuw", k)] = res["id"]
                self.tel["houder nieuw"] += 1
            else:
                self.tel[f"houder fout {status}"] += 1
                self.log(f"  ✗ {o['naam']}: {status} {res.get('error')}")
        for pk, p in self.p.nieuwe_personen.items():
            rol = self.p.rol[p["rol"]]
            status, res = self.rest("POST", "/api/entities", {
                "name": p["naam"], "type": "persoon", "primary_role_id": rol, "description": p["beschrijving"]})
            if status == 201:
                self.ent[("persoon", pk)] = res["id"]
                self.tel["persoon nieuw"] += 1
            else:
                self.tel[f"persoon fout {status}"] += 1
                self.log(f"  ✗ {p['naam']}: {status} {res.get('error')}")

    def _id(self, ref):
        return ref[1] if ref[0] == "bestaand" else self.ent.get(ref)

    def indienen(self):
        self.entiteiten()
        for key, v in self.p.nieuwe_verbanden.items():
            s, t = self._id(v["bron"]), self._id(v["doel"])
            if not s or not t:
                self.tel["verband zonder eindpunt"] += 1
                continue
            body = {"source_id": s, "target_id": t, "relation_type": v["type"],
                    "mechanism_id": self.p.mech[v["mechanisme"]]}
            for veld, waarde in (("functie", v["functie"]), ("active_from", v["start"]), ("active_until", v["eind"])):
                if waarde:
                    body[veld] = waarde
            status, res = self.rest("POST", "/api/relations", body)
            if status != 201:
                self.tel[f"verband fout {status}"] += 1
                self.log(f"  ✗ verband {v['type']} {s}→{t}: {status} {res.get('error')}")
                continue
            self.verbanden[key] = res["id"]
            self.tel["verband nieuw"] += 1
        for x in self.p.argumenten:
            rid = x["verband"] if isinstance(x["verband"], int) else self.verbanden.get(x["verband"])
            if not rid:
                continue
            rec = x["rec"]
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": rid, "claim": x["claim"], "stance": "supporting",
                "citations": [{"source_id": self.bron(), "quote": rec["regel"], "methode": "officieel_register_scrape",
                               "section": rec["sleutel"], "page": f"{afm.BRON}/{self.p.uitgave}", "context": rec["url"]}]})
            self.tel["argument" if status == 201 else f"argument fout {status}"] += 1
            if status != 201:
                self.log(f"  ✗ argument {rec['sleutel']} op #{rid}: {status} {res.get('error')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave", help="YYYY-MM-DD; standaard de nieuwste bewaarde uitgave")
    ap.add_argument("--haal", action="store_true", help="eerst een nieuwe uitgave ophalen")
    ap.add_argument("--indienen", action="store_true", help="echt indienen (standaard: droogloop)")
    a = ap.parse_args()
    if a.haal:
        print(afm.haal())
    if not afm.uitgaven():
        raise SystemExit("nog geen AFM-uitgave; eerst: python3 tools/registers/afm.py haal")
    data = afm.lees_uitgave(a.uitgave or afm.uitgaven()[-1].stem.split("_", 1)[1])
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(data, conn, koppelingen).maak()
    missers = plan.zelfcontrole()
    (afm.MAP / "analyse.md").write_text(plan.rapport(), encoding="utf-8")
    (afm.MAP / "analyse.json").write_text(json.dumps({
        "eigendom": plan.analyse, "bestuur": plan.bestuur_analyse, "datumverschil": plan.datumverschil,
        "koppelingen": plan.koppeling_log, "nieuwe_houders": plan.nieuwe_houders,
        "nieuwe_personen": plan.nieuwe_personen, "zelfcontrole_missers": missers},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"uitgave": plan.uitgave, "nieuwe verbanden": len(plan.nieuwe_verbanden),
                      "nieuwe houders": len(plan.nieuwe_houders), "nieuwe personen": len(plan.nieuwe_personen),
                      "argumenten": len(plan.argumenten), "telling": dict(sorted(plan.tel.items()))},
                     ensure_ascii=False, indent=1))
    print(f"rapport: {afm.MAP / 'analyse.md'}")
    if missers:
        print(f"ZELFCONTROLE: {len(missers)} argumenten zouden de registercheck niet halen (zie analyse.json)")
    if not a.indienen:
        print("\n(droogloop — niets ingediend)")
        return
    if missers:
        raise SystemExit("niet indienen: de zelfcontrole vond missers")
    # zonder 'afm' in registercheck.BRONNEN zegt de registercheck 'onbekende registerbron' →
    # klopt-niet, en de opruimstap verwerpt alles: dan niet indienen
    regcheck = (ROOT / "scripts" / "registercheck.py").read_text(encoding="utf-8")
    if not re.search(r'"afm"\s*:\s*afm\b', regcheck):
        raise SystemExit("niet indienen: 'afm' staat nog niet in scripts/registercheck.py BRONNEN")
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()))
    ind.indienen()
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
