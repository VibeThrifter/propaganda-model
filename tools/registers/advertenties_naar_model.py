#!/usr/bin/env python3
"""Meta Ad Library Report Nederland → het model (verkenning 2026-10-20; DROOGLOOP standaard).

advertenties.py leest de uitgaven: per Facebook/Instagram-pagina en per disclaimer ("betaald
door") het cumulatieve bedrag aan advertenties over maatschappelijke kwesties, verkiezingen of
politiek. Het verband zit in het verschil tussen de twee: wie betaalt voor de advertenties van
een ander. Dit script kiest daaruit wat telt, zonder AI.

  1. trechter, per rij van de nieuwste uitgave:
     - geen disclaimer ("These ads ran without a disclaimer"), pagina-id 0 (Instagram-gebruikers)
       en een disclaimer die geen organisatie is (een persoon, ook een kandidaat die zelf betaalt):
       weg. Privépersonen komen nooit in het model of het rapport;
     - de pagina betaalt zelf (dezelfde naam op rechtsvorm en 'Nederland/NL' na): eigen
       advertenties, alleen geteld;
     - de partij betaalt voor haar eigen kandidaten, afdelingen of jongeren: partij-eigen, ruis;
     - wat overblijft is een derde betaler: het verband dat ertoe doet.
  2. plannen (bestaande theorie, README § Regels):
     - de pagina IS een partij in het model (exacte naam of de partijtabel uit common) en een
       organisatie die geen partij of overheid is betaalt ervoor, voor minstens DREMPEL_EUR:
       `donor` betaler → partij, mechanisme `partijfinanciering` (een gift in natura: de partij
       krijgt bereik dat een ander betaalt). De betaler koppelt op haar exacte naam in het model
       of komt nieuw met rechtsvorm in de naam (tk_naar_model.rechtsvorm); nooit op een deel van
       de naam;
     - bestaat het verband al (donor/financiering betaler → partij, of `adverteerder` betaler →
       Meta), dan krijgt het alleen een extra argument met de recordregel als citaat.
     Alles verder (een bedrijf of lobbyclub die een eigen campagnepagina betaalt, een ministerie
     dat campagne voert) staat in het rapport: daarvoor ontbreekt een eindpunt of mechanisme.
  3. rapport (data/registers/advertenties/rapport_<uitgave>.md + .json): elke derde betaler,
     gescoord als (log10(1 + €) − 2) × soort × model × netwerk × piek × kwestie:
       soort   partijpagina met externe betaler 3 · campagnepagina van een ander 2 · overheid
               betaalt 1,5 · partij-eigen 0,3;
       model   ×1,5 als de betaler al in het model staat, ×1,25 als de pagina dat doet;
       netwerk 1 + ¼·log2(aantal pagina's van anderen die deze betaler financiert): één stichting
               achter meerdere 'eigen' pagina's (frontnetwerk) stijgt;
       piek    (vanaf € 1.000) √min(4, max(1, aandeel van het bedrag in de verkiezingskwartalen ÷ verwacht): de reeks
               kwartaaluitgaven (advertenties.py haal --reeks) geeft per paar wat in elk
               kwartaal is uitgegeven, en het aandeel daarvan in de verkiezingskwartalen; PS 2023, TK 2023 en EP 2024 zijn de verkiezingskwartalen;
       kwestie ×1,3 als de paginanaam een campagne tegen of voor een maatregel noemt
               ('Stop extra bierbelasting').

Gebruik:
    python3 tools/registers/advertenties.py haal [--reeks]
    python3 tools/registers/advertenties_naar_model.py                 # droogloop + rapport
    python3 tools/registers/advertenties_naar_model.py --indienen      # pas na de regels in
                        # registercheck.BRONNEN (zie het verslag); weigert anders
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
import advertenties as adv  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ROOT, partij_naam, sleutel  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
CLUSTER = f"register:{adv.BRON}"
META_NAAM = "Meta (Facebook/Instagram)"
DREMPEL_EUR = 1000          # minimum voor een nieuw donorverband
TOP = 30
VERKIEZINGEN = {"2023-03-15": "PS/WS 2023", "2023-11-22": "TK 2023", "2024-06-06": "EP 2024"}
STOPWOORDEN = {"stichting", "st", "vereniging", "nederland", "nederlandse", "nl", "holland", "bv", "b", "v", "nv",
               "n", "the", "de", "het", "van", "voor", "en", "foundation", "international", "netherlands", "org",
               "inc", "ltd", "com", "www", "afdeling", "tot", "behoud", "in"}
ORG_WOORD = re.compile(
    r"\b(stichting|st|vereniging|foundation|fonds|fund|bv|nv|ltd|inc|gmbh|llc|sa|ministerie|gemeente|provincie|"
    r"waterschap|rijksoverheid|overheid|partij|party|beweging|bond|vakbond|fnv|cnv|media|groep|group|nederland|"
    r"netherlands|holland|international|europe|european|council|unie|union|coalitie|collectief|platform|"
    r"alliantie|netwerk|instituut|institute|universiteit|university|hogeschool|omroep|bank|verzekeraar|"
    r"cooperatie|federatie|raad|campagne|actie|comite|committee|nl|com|eu|org|kerk|politie|ggd|unicef|"
    r"brouwers|boeren|ondernemers|werkgevers|club|centrum|center|centre|agency|bureau|studio|lab|hub|"
    r"solutions|services|consultancy|company|partners|holding|energie|cooperatie|coalition)\b")
KWESTIE = re.compile(r"\b(stop|nee|tegen|ja|belasting|wet|petitie|red|behoud|geen|referendum|verbod|"
                     r"accijns|heffing|tol|kerncentrale|windmolen|stikstof|asiel|azc)\b")


def _tokens(naam: str) -> set[str]:
    return {w for w in sleutel(naam).split() if w not in STOPWOORDEN and len(w) > 1}


def zelfde(pagina: str, disclaimer: str) -> bool:
    """Betaalt de pagina zelf? 'Vattenfall' ~ 'Vattenfall Nederland', 'Natuurmonumenten' ~
    'Vereniging tot Behoud van Natuurmonumenten in Nederland', 'JA21' ~ 'JA21.nl'."""
    a, b = _tokens(pagina), _tokens(disclaimer)
    if sleutel(pagina) == sleutel(disclaimer):
        return True
    if not a or not b:
        return False
    if a <= b or b <= a or {sleutel(pagina), sleutel(disclaimer)} in HANDMATIG_ZELFDE:
        return True
    # zelfde eerste eigen woord ('Amref Health Africa NL' ~ 'Amref Flying Doctors NL', 'FNV Vakbond' ~
    # 'FNV Supermarkt'): een hernoemde of onderverdeelde organisatie, geen derde betaler
    ea = [w for w in sleutel(pagina).split() if w not in STOPWOORDEN]
    eb = [w for w in sleutel(disclaimer).split() if w not in STOPWOORDEN]
    if ea and eb and ea[0] == eb[0] and len(ea[0]) >= 3 and not OVERHEID_NAAM.match(ea[0]):
        return True
    # samengeschreven: 'BoerBurgerBeweging' ~ 'Boer Burger Beweging', 'JA21.nl' ~ 'JA21'
    return "".join(sorted(a)) == "".join(sorted(b)) or sleutel(pagina).replace(" ", "") in \
        sleutel(disclaimer).replace(" ", "") or sleutel(disclaimer).replace(" ", "") in sleutel(pagina).replace(" ", "")


HANDMATIG_ZELFDE = [{"meta", "facebook inc"}, {"meta", "facebook"}]
TUSSEN_W = {"van", "de", "der", "den", "het", "ten", "ter", "te", "in", "'t", "op", "el", "al", "la", "le", "du", "da",
            "di", "von", "bin", "ben"}
OVERHEID_NAAM = re.compile(r"^(ministerie|gemeente|provincie|waterschap|rijksoverheid|rijksdienst|stadsdeel|ggd|"
                           r"politie|veiligheidsregio|taskforce|riec|omgevingsdienst|dienst)\b")
MEDIA_TYPES = {"mediaorganisatie", "omroep", "persbureau", "uitgeverij"}
MEDIA_NAAM = re.compile(r"\b(media|mediagroep|omroep|uitgeverij|publishing|dagblad|kro ncrv|bnnvara|avrotros|ntr|npo|"
                        r"eo|vpro|max|powned|wnl|ongehoord nederland|rtl|talpa|mediahuis|dpg)\b")
GROEP_TYPES = ("eigendom", "zeggenschap", "bestuurder", "controle", "lidmaatschap")


def persoonsnaam(naam: str) -> bool:
    """Ziet het eruit als de naam van een mens ('Rolin Den Heijer', 'Jan de Vries')? Twee tot vijf
    woorden, elk met een hoofdletter of een tussenvoegsel, zonder cijfers, organisatie- of
    kwestiewoorden. Zo'n naam komt nooit in het model of het rapport, tenzij hij er al staat."""
    if re.search(r"\(\s*\d+\s*\)", naam):   # 'Naam (324006487628747)': Meta zet zo een pagina-id achter een persoon
        return True
    naam = re.sub(r"\s*\([^)]*\)\s*", " ", naam).strip()
    if " - " in naam or " | " in naam:   # 'Shohreh Feshtali - BVNL': kandidaat met partij erachter
        return persoonsnaam(re.split(r" [-|] ", naam)[0])
    woorden = naam.replace("-", " - ").split()
    if not 2 <= len(woorden) <= 5 or any(c.isdigit() for c in naam):
        return False
    if ORG_WOORD.search(sleutel(naam)) or KWESTIE.search(sleutel(naam)):
        return False
    hoofd = [w for w in woorden if re.match(r"^[A-ZÀ-Ý][a-zà-ÿ'’.]+$", w)]
    initiaal = [w for w in woorden if re.match(r"^(?:[A-ZÀ-Ý]\.)+$", w)]
    return len(hoofd) + len(initiaal) >= 2 and len(hoofd) >= 1 and \
        all(w in hoofd or w in initiaal or w.lower() in TUSSEN_W or w == "-" for w in woorden)


def org_achtig(naam: str) -> bool:
    """Een organisatie (en geen privépersoon)? Rechtsvorm, organisatiewoord, een afkorting in
    hoofdletters ('BVNL', 'VLG') of een domeinnaam."""
    if tkm.rechtsvorm(naam) or ORG_WOORD.search(sleutel(naam)):
        return True
    return any(len(w) >= 2 and w.isupper() for w in re.findall(r"[\w&]+", naam)) or bool(re.search(r"\.\w{2,3}$", naam))


class Plan(tkm.Plan):
    def __init__(self, reeks: list[dict], conn: sqlite3.Connection, koppelingen: dict | None = None):
        data = reeks[-1]
        super().__init__({"uitgave": data["uitgave"], "personen": {}, "records": {}}, conn, koppelingen)
        self.data, self.reeks = data, reeks
        self.mech.update(self._ids("mechanisms", ("partijfinanciering", "adverteren_als_belang", "overheidscampagne")))
        self.meta = self.org_index.get(sleutel(META_NAAM))
        self.hand = {sleutel(k): v for k, v in (koppelingen or {}).get("advertenties_namen", {}).items()
                     if not k.startswith("_")}
        self.bestaand_rel: dict[tuple[int, int], list[tuple[int, str]]] = defaultdict(list)
        for rid, s, t, typ in conn.execute(
                "SELECT id, source_id, target_id, relation_type FROM relations WHERE NOT vervangen AND status <> 'afgewezen'"):
            self.bestaand_rel[(s, t)].append((rid, typ))
        self.al_geciteerd = {(r, sec) for r, sec in conn.execute(f"""
            SELECT a.relation_id, c.section FROM citations c JOIN arguments a ON a.id = c.argument_id
            WHERE c.page LIKE '{adv.BRON}/%' AND a.relation_id IS NOT NULL""")}  # noqa: S608
        self.extra_bron: list[dict] = []
        self.eigen_in_model: Counter = Counter()
        self.kandidaten: list[dict] = []
        self.kwartalen = self._kwartalen()

    # ── koppelen ────────────────────────────────────────────────────────────
    def _partij(self, naam: str) -> int | None:
        """Een partij in het model onder deze naam (exact, of via de partijtabel)."""
        gevonden = self._bestaand(naam, ruim=False)
        if gevonden and self.org[gevonden[0]][1] == "partij":
            return gevonden[0]
        p = partij_naam(naam)
        return self.partij_id.get(p) if p else None

    def _org(self, naam: str) -> int | None:
        """Exacte naam in het model (geen deel van de naam, geen persoon), of de met de hand
        nagelopen schrijfwijze in koppelingen.json ('advertenties_namen': disclaimer → modelnaam)."""
        naam = self.hand.get(sleutel(naam), naam)
        gevonden = self._bestaand(naam, ruim=False)
        return gevonden[0] if gevonden and gevonden[0] > 0 else None

    # ── tijdreeks ───────────────────────────────────────────────────────────
    def _kwartalen(self) -> dict[tuple[str, str], list[int]]:
        """Per (pagina-id, disclaimer) het bedrag per interval tussen opeenvolgende uitgaven."""
        per_uitgave = []
        for d in self.reeks:
            som: Counter = Counter()
            for r in d["records"].values():
                som[(r["pagina_id"], sleutel(r["disclaimer"]))] += r["eur"] or 0
            per_uitgave.append(som)
        self.intervallen = [(a["uitgave"], b["uitgave"]) for a, b in zip(self.reeks, self.reeks[1:])]
        self.verkiezing_iv = {i for i, (van, tot) in enumerate(self.intervallen)
                              for dag in VERKIEZINGEN if van < dag <= tot}
        uit = {}
        for k in per_uitgave[-1]:
            uit[k] = [max(0, b.get(k, 0) - a.get(k, 0)) for a, b in zip(per_uitgave, per_uitgave[1:])]
        return uit

    def _piek(self, k) -> tuple[float, str | None]:
        reeks = self.kwartalen.get(k) or []
        totaal = sum(reeks)
        if not totaal or not self.intervallen:
            return 1.0, None
        aandeel = sum(v for i, v in enumerate(reeks) if i in self.verkiezing_iv) / totaal
        verwacht = len(self.verkiezing_iv) / len(self.intervallen)
        top = max(range(len(reeks)), key=lambda i: reeks[i])
        return round(aandeel / verwacht, 2), f"{self.intervallen[top][0]}…{self.intervallen[top][1]}"

    # ── kiezen ──────────────────────────────────────────────────────────────
    def maak(self):
        paren: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for rec in self.data["records"].values():
            self.tel["rijen"] += 1
            if rec["disclaimer"] == adv.GEEN_DISCLAIMER:
                self.tel["weg: geen disclaimer"] += 1
                self.tel["€ zonder disclaimer"] += rec["eur"] or 0
                continue
            if rec["pagina_id"] == "0":
                self.tel["weg: Instagram-gebruiker zonder pagina"] += 1
                continue
            if zelfde(rec["pagina"], rec["disclaimer"]):
                self.tel["eigen advertenties (pagina betaalt zelf)"] += 1
                self.tel["€ eigen advertenties"] += rec["eur"] or 0
                self._eigen(rec)
                continue
            if persoonsnaam(rec["disclaimer"]) and not self._org(rec["disclaimer"]) \
                    and not self._partij(rec["disclaimer"]):
                self.tel["weg: betaler is (waarschijnlijk) een persoon"] += 1
                continue
            paren[(rec["pagina_id"], sleutel(rec["disclaimer"]))].append(rec)
        netwerk = Counter(d for (_p, d) in paren)
        for k, recs in paren.items():
            self._derde(k, recs, netwerk[k[1]])
        self.kandidaten.sort(key=lambda c: -c["score"])
        return self.klem()

    def _eigen(self, rec):
        """Eigen advertenties: alleen een extra bron op een bestaand 'adverteerder → Meta'."""
        eid = self._org(rec["disclaimer"]) or self._org(rec["pagina"])
        if eid and self.org[eid][1] != "partij":
            self.eigen_in_model[eid] += rec["eur"] or 0
        if eid and self.meta and (rec["eur"] or 0) >= DREMPEL_EUR:
            self._extra(eid, self.meta, ("adverteerder",), rec,
                        f"Volgens het Meta Ad Library Report (NL, cumulatief t/m {self.uitgave}) gaf "
                        f"{self.org[eid][0]} € {rec['eur_tekst']} uit aan {rec['advertenties']} advertenties over "
                        f"maatschappelijke kwesties, verkiezingen of politiek op Facebook/Instagram.")

    def _extra(self, s, t, typen, rec, claim) -> bool:
        for rid, typ in self.bestaand_rel.get((s, t), []):
            if typ in typen:
                if (rid, rec["sleutel"]) in self.al_geciteerd:
                    self.tel["extra bron: al geciteerd"] += 1
                else:
                    self.extra_bron.append({"relatie": rid, "type": typ, "bron": self.org[s][0], "doel": self.org[t][0],
                                            "sleutel": rec["sleutel"], "regel": rec["regel"], "claim": claim})
                    self.tel[f"extra bron op bestaand {typ}"] += 1
                return True
        return False

    def _derde(self, k, recs, n_paginas):
        rec = max(recs, key=lambda r: r["eur"] or 0)
        eur = sum(r["eur"] or 0 for r in recs)
        pagina, betaler = rec["pagina"], rec["disclaimer"]
        p_partij, b_partij = self._partij(pagina), self._partij(betaler)
        b_org, p_org = self._org(betaler), self._org(pagina)
        persoonspagina = persoonsnaam(pagina) and not (p_org or p_partij or self.pm_personen.get(sleutel(pagina)))
        verbonden = bool(b_org and p_org and (self.bestaand_rel.get((b_org, p_org)) or self.bestaand_rel.get((p_org, b_org))))
        partijnaam = sleutel(self.org[b_partij][0]) if b_partij else ""
        b_eigen = (bool(b_partij) or self._partij_eigen(betaler)) and (
            persoonspagina or self._partij_eigen(pagina) or bool(p_partij) or verbonden
            or bool(self.pm_personen.get(sleutel(pagina)))
            or bool(partijnaam and sleutel(pagina).replace(" ", "").startswith(partijnaam.split()[0])))
        b_overheid = bool(b_org and (self.org[b_org][2] or self.org[b_org][1] in tkm.OVERHEID_TYPES)) or \
            bool(OVERHEID_NAAM.match(sleutel(betaler)))
        p_overheid = bool(p_org and (self.org[p_org][2] or self.org[p_org][1] in tkm.OVERHEID_TYPES)) or \
            bool(OVERHEID_NAAM.match(sleutel(pagina)))
        groep = bool(b_org and p_org and any(typ in GROEP_TYPES for rid, typ in
                                             self.bestaand_rel.get((b_org, p_org), []) + self.bestaand_rel.get((p_org, b_org), [])))
        b_media = bool(b_org and self.org[b_org][1] in MEDIA_TYPES) or bool(MEDIA_NAAM.search(sleutel(betaler)))
        if b_eigen:
            soort, w = "partij betaalt voor kandidaat/afdeling (partij-eigen)", 0.3
        elif b_partij or self._partij_eigen(betaler):
            soort, w = "partij betaalt campagnepagina van een ander", 2.5
        elif b_media and not p_partij:
            soort, w = "mediabedrijf betaalt voor eigen titel", 0.3
        elif groep:
            soort, w = "moeder betaalt voor eigen onderdeel (bestaand verband)", 0.3
        elif b_overheid and p_overheid:
            soort, w = "overheid betaalt voor overheid", 0.3
        elif p_partij:
            soort, w = "externe betaler van een partijpagina", 3.0
        elif b_overheid:
            soort, w = "overheid betaalt campagnepagina", 1.5
        else:
            soort, w = "betaler van andermans (campagne)pagina", 2.0
        piek, top_iv = self._piek(k)
        kwestie = bool(KWESTIE.search(sleutel(pagina)))
        # geld: €100 → 0,1 · €1.000 → 1 · €10.000 → 2 · €100.000 → 3; kleine bedragen zinken weg
        geld = max(0.1, math.log10(1 + eur) - 2)
        score = (geld * w * (1.5 if b_org else 1) * (1.25 if (p_org or p_partij) else 1)
                 * (1 + 0.25 * math.log2(n_paginas)) * (math.sqrt(min(4.0, max(1.0, piek))) if eur >= 1000 else 1)
                 * (1.3 if kwestie else 1))
        c = {"betaler": betaler, "betaler_in_model": self.org[b_org][0] if b_org else None,
             "pagina": "(pagina van een persoon)" if persoonspagina else pagina,
             "pagina_in_model": self.org[p_org or p_partij][0] if (p_org or p_partij) else None,
             "eur": eur, "eur_tekst": " + ".join(r["eur_tekst"] for r in recs), "advertenties": sum(r["advertenties"] for r in recs),
             "paginas_van_betaler": n_paginas, "soort": soort, "piek": piek, "grootste_kwartaal": top_iv,
             "kwestie": kwestie, "score": round(score, 2), "status": "rapport", "sleutel": rec["sleutel"]}
        self.kandidaten.append(c)
        self.tel[f"derde betaler: {soort}"] += 1
        if w < 1:
            c["status"] = "ruis"
            return
        if not p_partij:
            if b_overheid:
                c["status"] = "ontbrekende theorie (overheidscampagne: geen doelknoop)"
            else:
                c["status"] = "ontbrekende theorie (betaalde campagne voor een ander)"
            self.tel[f"rapport: {c['status']}"] += 1
            return
        # een partijpagina met een externe betaler: donor/partijfinanciering
        claim = (f"Volgens het Meta Ad Library Report (NL, cumulatief t/m {self.uitgave}) betaalde {betaler} "
                 f"(disclaimer) voor {c['advertenties']} advertenties op de pagina '{pagina}' van "
                 f"{self.org[p_partij][0]}, samen € {c['eur_tekst']}.")
        if b_org and self._extra(b_org, p_partij, ("donor", "financiering"), rec, claim):
            c["status"] = "extra bron"
            return
        if b_overheid:
            c["status"] = "overgeslagen: overheid als betaler van een partijpagina"
            self.tel["overgeslagen: overheid betaalt partijpagina"] += 1
            return
        if eur < DREMPEL_EUR:
            c["status"] = f"te weinig (< € {DREMPEL_EUR})"
            self.tel["paar: te weinig"] += 1
            return
        if b_org:
            ref = ("bestaand", b_org)
        else:
            ref = self._nieuw(betaler, "advertentie", rec)
            if not ref:
                c["status"] = "overgeslagen: betaler niet in het model en geen rechtsvorm"
                return
            self.nieuwe_orgs[ref[1]]["beschrijving"] = (
                f"Betaalde (disclaimer) voor politieke advertenties op Facebook/Instagram volgens het Meta Ad "
                f"Library Report Nederland ({self.uitgave}).")
        self._rel(ref, ("bestaand", p_partij), "donor", "partijfinanciering", rec, claim,
                  functie=f"Betaalde advertenties op '{pagina}' (€ {c['eur_tekst']})")
        c["status"] = "nieuw verband"

    # ── rapport ─────────────────────────────────────────────────────────────
    def rapport(self) -> str:
        t = self.tel
        r = ["# Meta Ad Library Report NL: wie betaalt voor wiens advertenties", "",
             f"Uitgave {self.uitgave} (cumulatief), reeks {self.reeks[0]['uitgave']} – {self.uitgave} "
             f"({len(self.reeks)} uitgaven; verkiezingskwartalen: "
             f"{', '.join(f'{v} ({self.intervallen[i][1]})' for i in sorted(self.verkiezing_iv) for d, v in VERKIEZINGEN.items() if self.intervallen[i][0] < d <= self.intervallen[i][1])}).", "",
             f"Rijen {t['rijen']} · zonder disclaimer {t['weg: geen disclaimer']} (€ {t['€ zonder disclaimer']:,}) · "
             f"eigen advertenties {t['eigen advertenties (pagina betaalt zelf)']} (€ {t['€ eigen advertenties']:,}) · "
             f"betaler is een persoon (weggelaten) {t['weg: betaler is (waarschijnlijk) een persoon']} · "
             f"derde betalers {len(self.kandidaten)}.".replace(",", "."), "",
             "Score = (log10(1+€) − 2) × soort × model × netwerk × √piek × kwestie (zie de kop van het script). "
             "Bedragen '≤100' tellen als 0.", "",
             f"## Top {TOP}", "",
             "| # | betaler (disclaimer) | pagina | € | adv. | pagina's | soort | piek | grootste kwartaal | score | status |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
        for i, c in enumerate([c for c in self.kandidaten if c["status"] != "ruis"][:TOP], 1):
            b = c["betaler"] + (" ✓" if c["betaler_in_model"] else "")
            p = c["pagina"] + (" ✓" if c["pagina_in_model"] else "")
            r.append(f"| {i} | {b} | {p} | {c['eur_tekst']} | {c['advertenties']} | {c['paginas_van_betaler']} | "
                     f"{c['soort']} | {c['piek']} | {c['grootste_kwartaal'] or ''} | {c['score']} | {c['status']} |")
        r += ["", "✓ = staat al in het model (exacte naam).", "",
              "## Betalers achter meerdere pagina's van anderen (netwerk)", ""]
        per: dict[str, list[dict]] = defaultdict(list)
        for c in self.kandidaten:
            if c["status"] != "ruis":
                per[c["betaler"]].append(c)
        for b, cs in sorted(per.items(), key=lambda kv: (-len(kv[1]), -sum(c["eur"] for c in kv[1])))[:15]:
            if len(cs) < 2:
                break
            r.append(f"- {b}: {len(cs)} pagina's, € {sum(c['eur'] for c in cs):,} — ".replace(",", ".")
                     + "; ".join(c["pagina"] for c in sorted(cs, key=lambda c: -c["eur"])[:6]))
        r += ["", "## Externe betalers van partijpagina's", ""]
        for c in [c for c in self.kandidaten if c["soort"] == "externe betaler van een partijpagina"][:20]:
            r.append(f"- {c['betaler']} → {c['pagina']} ({c['pagina_in_model']}): € {c['eur_tekst']}, {c['status']}")
        r += ["", "## Overheid als betaler van campagnepagina's (overheidscampagne)", ""]
        for c in [c for c in self.kandidaten if c["soort"].startswith("overheid")][:15]:
            r.append(f"- {c['betaler']} → {c['pagina']}: € {c['eur_tekst']}")
        r += ["", "## Sterkste verkiezingspieken (piek ≥ 2, € ≥ 5.000)", ""]
        for c in sorted([c for c in self.kandidaten if c["piek"] >= 2 and c["eur"] >= 5000
                         and c["status"] != "ruis"], key=lambda c: -c["piek"])[:15]:
            r.append(f"- {c['betaler']} → {c['pagina']}: piek {c['piek']}, € {c['eur_tekst']}, grootste kwartaal {c['grootste_kwartaal']}")
        r += ["", "## Grootste eigen adverteerders die al in het model staan", "",
              "Eigen advertenties over kwesties/politiek (pagina = betaler). Alleen een bestaand 'adverteerder → "
              "Meta' krijgt een bron; voor de rest ontbreekt een mechanisme (zie het verslag).", ""]
        for eid, eur in self.eigen_in_model.most_common(20):
            heeft = any(typ == "adverteerder" for rid, typ in self.bestaand_rel.get((eid, self.meta), []))
            r.append(f"- {self.org[eid][0]} ({self.org[eid][1]}): € {eur:,}".replace(",", ".")
                     + (" — bestaand adverteerder → Meta" if heeft else ""))
        r += ["", "## Gepland (droogloop)", ""]
        for rel in self.relaties:
            bron = self.org[rel["bron"][1]][0] if rel["bron"][0] == "bestaand" else self.nieuwe_orgs[rel["bron"][1]]["naam"] + " (nieuw)"
            r.append(f"- nieuw: {bron} —donor/partijfinanciering→ {self.org[rel['doel'][1]][0]} · {rel['sleutel']}")
        for e in self.extra_bron:
            r.append(f"- extra bron op #{e['relatie']} ({e['type']}): {e['bron']} → {e['doel']} · {e['sleutel']}")
        return "\n".join(r) + "\n"


class Indiener(tkm.Indiener):
    def extra(self, bron_id: int):
        for e in self.p.extra_bron:
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": e["relatie"], "claim": e["claim"], "stance": "supporting",
                "citations": [{"source_id": bron_id, "quote": e["regel"], "methode": "officieel_register_scrape",
                               "section": e["sleutel"], "page": f"{adv.BRON}/{self.p.uitgave}", "context": adv.URL}]})
            self.tel["extra argument" if status == 201 else f"extra argument fout {status}"] += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--indienen", action="store_true")
    a = ap.parse_args()
    if not adv.uitgaven():
        raise SystemExit("nog geen uitgave; eerst: python3 tools/registers/advertenties.py haal [--reeks]")
    reeks = [adv.lees_uitgave(p.stem.split("_", 1)[1]) for p in adv.uitgaven()]
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    plan = Plan(reeks, conn, koppelingen).maak()
    (adv.MAP / f"rapport_{plan.uitgave}.md").write_text(plan.rapport(), encoding="utf-8")
    (adv.MAP / f"rapport_{plan.uitgave}.json").write_text(json.dumps(
        {"gemaakt": datetime.date.today().isoformat(), "telling": dict(plan.tel), "kandidaten": [
            c for c in plan.kandidaten if c["status"] != "ruis"]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"uitgave": plan.uitgave, "nieuwe_organisaties": [o["naam"] for o in plan.nieuwe_orgs.values()],
                      "nieuwe_verbanden": len(plan.relaties), "extra_bronnen": len(plan.extra_bron),
                      "telling": dict(sorted(plan.tel.items()))}, ensure_ascii=False, indent=1))
    print(f"rapport: {adv.MAP / f'rapport_{plan.uitgave}.md'}")
    if not a.indienen:
        print("\n(droogloop — niets ingediend)")
        return
    sys.path.insert(0, str(ROOT / "scripts"))
    import registercheck
    if adv.BRON not in registercheck.BRONNEN:
        raise SystemExit(f"registercheck kent '{adv.BRON}' nog niet (BRONNEN); zonder onafhankelijke A1 "
                         "wordt niets ingediend")
    from naar_model import TOKEN, Rest
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()), bron=adv, cluster=CLUSTER)
    bron_id = ind.bron()
    ind.entiteiten()
    ind.relaties(bron_id)
    ind.extra(bron_id)
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
