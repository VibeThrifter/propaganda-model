#!/usr/bin/env python3
"""LittleSis → het model: nieuwe verbanden en extra bronnen (onderzoek 2026-10-20).

littlesis.py bewaart een uitgave (relaties met minstens één Nederlandse, gekoppelde of elite-
forum-kant, plus de bronlinks per relatie). Dit script kiest wat het model iets brengt, zonder AI:

  1. koppelen: een LittleSis-entiteit hoort alleen bij een knoop als littlesis_koppelingen.json
     dat zegt (met de hand nagelopen, met het bewijs erbij; README § Regels: nooit op naam alleen).
     Familie en sociale relaties komen niet in de uitgave.
  2. per relatie waarvan beide kanten gekoppeld zijn:
     - bestaat er al een passend verband tussen die knopen (beide richtingen, ook via een
       model-dubbel zoals Shell #75/#835) → een EXTRA BRON op dat verband (één argument met
       LittleSis' zin als letterlijk citaat), tenzij die relatie al geciteerd is;
     - anders een NIEUW VERBAND, maar alleen als een bestaand mechanisme past (MECHANISMEN
       hieronder: elite-fora, draaideur, financiering, eigendom). Past niets, dan telt het als
       'geen theorie' in het rapport en wordt het niet gepland (geen kandidaat-verbanden);
  3. relaties met één gekoppelde kant en een Nederlandse of elite-forum-kant aan de andere kant:
     alleen in het rapport (tips: een nieuwe knoop vergt eerst een besluit en een primaire bron).
Opleiding, transacties, Amerikaanse lobby (LDA), 'professioneel' en 'generiek' gaan alleen het
rapport in (ruis voor dit model).

Score (rapport, top-50): categoriegewicht × bron (1 met een bronlink, 0,35 zonder) × actualiteit
× zeldzaamheid (1/log2(2 + aantal LittleSis-relaties van de organisatie), naar Adamic-Adar zoals
de viz) × 1,5 als er een elite-forum in zit × 1,5 als een kant Nederlands is (LittleSis noemt
Nederland of een .nl-website) × 1,3 als het een nieuw verband is; een extra bron
× 2/(1 + bronlijnen die het verband al heeft), × 0,4 op een registerfeit (dun bewijs eerst).

Citaat en methode. LittleSis is geen officieel register maar een secundaire, door onderzoekers
bijgehouden verzameling: `officieel_register_scrape` past niet (dat geeft het structuurpad zonder
A2/smaadtoets en de registercheck, bedoeld voor eerste-hands overheidsregisters). Wat wel past:
per relatie een bron "LittleSis: <zin>" (source_type `website`, vindplaats de relatiepagina
littlesis.org/relationships/<id>, `cluster_key` `littlesis`, betrouwbaarheid voorgesteld `grijs`),
citaat = LittleSis' zin, die letterlijk op die pagina staat → methode `verbatim_quote`; de
bronlinks van LittleSis gaan mee in `context`, zodat de bronzoeker de primaire bron kan toevoegen.
Zo loopt elk argument langs de gewone uurronde (bronchecker A1, smaadtoets bij personen,
stemtoets, aanklager) en telt alles van LittleSis als één bewijslijn per verband.

Gebruik:
    python3 tools/registers/littlesis_naar_model.py                  # droogloop + rapport
    python3 tools/registers/littlesis_naar_model.py --top 50
    python3 tools/registers/littlesis_naar_model.py --haal [--indienen] [--token data/tokens/assistent.token]
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
import littlesis  # noqa: E402
from common import ROOT  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
TOKEN = ROOT / "data" / "tokens" / "assistent.token"   # geen register: het gewone bijdragepad
CLUSTER = "littlesis"
TOP = 50

# Categorie → gewicht in de score; None = alleen rapport (ruis voor dit model)
CAT_GEWICHT = {1: 2.0, 3: 2.5, 5: 2.0, 10: 2.5, 11: 1.0, 2: None, 6: None, 7: None, 9: None, 12: None}
ELITE_TYPES = {"elite_netwerk"}
POLITIEK_ROLLEN = {"politicus", "bewindspersoon", "lokale_bestuurder", "topambtenaar"}
MEDIA_ROLLEN = {"journalist", "hoofdredacteur", "columnist_opiniemaker", "onderzoeksjournalist", "publieke_stem"}
KENNIS_ROLLEN = {"gezagsexpert", "denktank"}
DRAAIDEUR_DOELEN = {"bedrijf", "vermogensbeheerder", "lobbygroep", "denktank", "stichting", "ngo",
                    "mediaorganisatie", "omroep", "pr_bureau", "persbureau", "platform"}
AFFILIATIE = {"bestuurder", "personeel", "adviseur", "lidmaatschap", "dienstverband", "draaideur", "woordvoerder_van"}
BESTUUR = re.compile(r"\b(director|board|chair|chairman|chairwoman|president|trustee|commissaris|supervisory|"
                     r"steering|governor|non.executive|vice.chair)\b", re.I)
ADVIES = re.compile(r"\b(advis[eo]r\w*|advisory|counsel)\b", re.I)


def datum(w: str | None) -> str | None:
    """LittleSis '2014-00-00' → '2014', '2007-03-00' → '2007-03'."""
    if not w:
        return None
    m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", w)
    if not m or m.group(1) == "0000":
        return None
    j, mnd, d = m.groups()
    if not mnd or mnd == "00":
        return j
    return f"{j}-{mnd}" if not d or d == "00" else f"{j}-{mnd}-{d}"


def kandidaat_ids(ent: dict, rels: dict) -> list[int]:
    """Welke relaties een bronlink nodig hebben (littlesis.haal leest alleen die pagina's): beide
    kanten gekoppeld, of één gekoppeld en de andere Nederlands of een elite-forum (positie,
    lidmaatschap, eigendom); de rest is ruis of te ver weg."""
    k = littlesis.koppelingen()
    paar, een = [], []
    for rid, r in rels.items():
        cat = r["category_id"]
        if CAT_GEWICHT.get(cat) is None:
            continue
        e1, e2 = r["entity1_id"], r["entity2_id"]
        if e1 in k and e2 in k:
            if k[e1]["model"] != k[e2]["model"]:
                paar.append(rid)
        elif (e1 in k or e2 in k) and cat in (1, 3, 10):
            ander = e2 if e1 in k else e1
            if ander in littlesis.HUBS or set((ent.get(ander) or {}).get("nl") or []) & {"tekst", "website.nl"}:
                een.append(rid)
    return sorted(paar) + sorted(een)


class Plan:
    def __init__(self, data: dict, conn: sqlite3.Connection):
        self.data, self.conn = data, conn
        self.uitgave = data["uitgave"]
        self.k = littlesis.koppelingen()
        d = json.loads(littlesis.KOPPELINGEN.read_text(encoding="utf-8"))
        self.dubbel = {int(a): int(b) for a, b in d.get("model_dubbel", {}).items() if not a.startswith("_")}
        self.ent = {i: (n, t, r) for i, n, t, r in conn.execute("""
            SELECT e.id, e.name, e.type, ro.name FROM entities e LEFT JOIN roles ro ON ro.id = e.primary_role_id
            WHERE NOT e.vervangen AND e.status <> 'afgewezen'""")}
        self.mech = {n: i for n, i in conn.execute("SELECT name, id FROM mechanisms WHERE NOT vervangen")}
        self.politiek = {s for (s,) in conn.execute("""
            SELECT DISTINCT r.source_id FROM relations r JOIN mechanisms m ON m.id = r.mechanism_id
            WHERE NOT r.vervangen AND r.status <> 'afgewezen' AND (r.relation_type = 'ambt'
               OR m.name IN ('kamerzetel', 'partijlijn', 'lokaal_bestuursmandaat', 'ministeriele_verantwoordelijkheid'))""")}
        self.paren: dict[tuple[int, int], list[tuple]] = defaultdict(list)
        for rid, s, t, typ, st, mn in conn.execute("""
                SELECT r.id, r.source_id, r.target_id, r.relation_type, r.status, m.name FROM relations r
                LEFT JOIN mechanisms m ON m.id = r.mechanism_id WHERE NOT r.vervangen AND r.status <> 'afgewezen'"""):
            s, t = self.dubbel.get(s, s), self.dubbel.get(t, t)
            self.paren[(min(s, t), max(s, t))].append((rid, typ, st, mn, s, t))
        self.geciteerd = {(r, sec) for r, sec in conn.execute("""
            SELECT a.relation_id, c.section FROM citations c JOIN arguments a ON a.id = c.argument_id
            WHERE c.page LIKE 'littlesis/%' AND a.relation_id IS NOT NULL""")}
        # hoeveel onafhankelijke bronlijnen (clusters) een verband al heeft: een extra bron is het
        # meest waard waar het bewijs dun is; registerfeiten tellen als bron
        self.bronlijnen = Counter()
        self.register = set()
        for rid, cl, meth in conn.execute("""
                SELECT a.relation_id, COALESCE(s.cluster_key, 'bron:' || s.id), c.methode FROM arguments a
                JOIN citations c ON c.argument_id = a.id JOIN sources s ON s.id = c.source_id
                WHERE a.relation_id IS NOT NULL AND NOT a.vervangen AND a.status NOT IN ('verworpen')
                GROUP BY a.relation_id, 2, c.methode"""):
            self.bronlijnen[rid] += 1
            if meth == "officieel_register_scrape":
                self.register.add(rid)
        self.graad = Counter()
        for r in data["records"].values():
            self.graad[r["entity1_id"]] += 1
            self.graad[r["entity2_id"]] += 1
        self.extra_bron: list[dict] = []
        self.nieuw: list[dict] = []
        self.geen_theorie: Counter = Counter()
        self.geen_theorie_vb: dict[str, list[str]] = defaultdict(list)
        self.tips: list[dict] = []
        self.ruis: Counter = Counter()
        self.tel: Counter = Counter()

    # ── hulp ───────────────────────────────────────────────────────────────
    def model(self, ls_id: int) -> int | None:
        m = self.k.get(ls_id)
        return self.dubbel.get(m["model"], m["model"]) if m else None

    def _persoon_soort(self, eid: int) -> str:
        rol = self.ent[eid][2]
        if rol in POLITIEK_ROLLEN or eid in self.politiek:
            return "politiek"
        if rol == "mediaeigenaar":
            return "mediaeigenaar"
        if rol in MEDIA_ROLLEN:
            return "media"
        if rol in KENNIS_ROLLEN:
            return "kennis"
        return "belang"

    @staticmethod
    def _functie_type(rec: dict) -> str:
        titel = f"{rec.get('description1') or ''} {rec.get('description2') or ''}"
        attr = rec.get("category_attributes") or {}
        if re.search(r"\bmanager\b", titel, re.I) and not re.search(
                r"\b(director|chair\w*|commissaris|trustee|supervisory)\b", titel, re.I):
            return "personeel"   # 'HR manager for the board' is geen bestuursfunctie
        if attr.get("is_board") or BESTUUR.search(titel):
            return "bestuurder"
        if ADVIES.search(titel):
            return "adviseur"
        return "personeel"

    def _orienteer(self, rec: dict, a: int, b: int) -> tuple[int, int]:
        """(bron, doel): persoon → organisatie, gever → ontvanger, eigenaar → bezit, moeder → dochter."""
        cat = rec["category_id"]
        if cat in (1, 2, 3):
            if self.ent[b][1] == "persoon" and self.ent[a][1] != "persoon":
                return b, a
            return a, b
        if cat == 11:   # hiërarchie: entity1 is in LittleSis de dochter
            return b, a
        return a, b      # donatie, eigendom: entity1 geeft/bezit

    def mechanisme(self, rec: dict, bron: int, doel: int) -> tuple[str, str] | tuple[None, str]:
        """→ (mechanisme, relatietype) of (None, reden voor het rapport)."""
        cat = rec["category_id"]
        bt, dt = self.ent[bron][1], self.ent[doel][1]
        if cat in (1, 3):
            if dt in ELITE_TYPES:
                rtype = "bestuurder" if cat == 1 and self._functie_type(rec) == "bestuurder" else "lidmaatschap"
                if bt != "persoon":
                    return "belang_elite_netwerk", "lidmaatschap"
                soort = self._persoon_soort(bron)
                return {"politiek": "politicus_elite_netwerk", "mediaeigenaar": "mediaeigenaar_elite_netwerk",
                        "media": "elite_media_netwerk", "kennis": "elite_kennisnetwerk"}.get(
                    soort, "belang_elite_netwerk"), rtype
            if bt == "persoon" and cat == 1 and dt in DRAAIDEUR_DOELEN and self._persoon_soort(bron) == "politiek":
                return "draaideurconstructie", self._functie_type(rec)
            if bt != "persoon" and cat == 3 and dt == "denktank":
                # bedrijfslidmaatschap van een denktank is contributie (denktank_financiering noemt die)
                return "denktank_financiering", "lidmaatschap"
            if bt == "persoon" and dt == "partij":
                return None, "partijfunctie (hoort uit de TK/OO-registers te komen)"
            if bt == "persoon" and dt in ("overheidsinstelling", "toezichthouder"):
                return None, "ambt of functie bij de overheid (hoort uit de registers te komen)"
            if bt == "persoon" and dt in ("bedrijf", "vermogensbeheerder"):
                return None, "functie van een niet-politicus bij een bedrijf (bestuurlijke verstrengeling tussen bedrijven)"
            if bt == "persoon":
                return None, f"{'functie' if cat == 1 else 'lidmaatschap'} bij {dt} zonder passend mechanisme"
            return None, f"organisatie lid van {dt}"
        if cat == 5:
            mech = {"denktank": "denktank_financiering", "ngo": "ngo_financiering_bias",
                    "stichting": "ngo_financiering_bias", "partij": "partijfinanciering",
                    "mediaorganisatie": "externe_mediafinanciering", "omroep": "externe_mediafinanciering"}.get(dt)
            if not mech:
                return None, f"donatie aan {dt}"
            return mech, ("donor" if mech == "partijfinanciering" else "financiering")
        if cat == 10:
            if bt == "vermogensbeheerder":
                return "systemisch_eigenaarschap", "eigendom"
            if dt in ("mediaorganisatie", "omroep", "persbureau"):
                return "eigendomsconcentratie", "eigendom"
            return None, f"eigendom {bt} → {dt}"
        if cat == 11:
            return None, "moeder-dochter (hiërarchie) zonder mediaketen"
        return None, littlesis.CATEGORIE[cat]

    def score(self, rec: dict, a: int, b: int, nieuw: bool) -> float:
        g = CAT_GEWICHT.get(rec["category_id"]) or 0.5
        bron = 1.0 if rec.get("bronlinks") else 0.35
        eind = datum(rec.get("end_date"))
        actueel = 1.0 if (rec.get("is_current") or not eind or int(eind[:4]) >= 2015) else 0.6
        org = [x for x in (rec["entity1_id"], rec["entity2_id"])
               if (self.data["entiteiten"].get(x) or {}).get("primary_ext") == "Org"]
        zeld = min((1 / math.log2(2 + self.graad[x]) for x in org), default=1.0) * 3
        elite = 1.5 if {self.ent[a][1], self.ent[b][1]} & ELITE_TYPES else 1.0
        nl = 1.5 if any(set((self.data["entiteiten"].get(x) or {}).get("nl") or []) & {"tekst", "website.nl"}
                        for x in (rec["entity1_id"], rec["entity2_id"])) else 1.0
        return round(g * bron * actueel * zeld * elite * nl * (1.3 if nieuw else 1.0), 3)

    # ── plannen ────────────────────────────────────────────────────────────
    def maak(self):
        for rec in self.data["records"].values():
            self.tel["records"] += 1
            cat = rec["category_id"]
            a, b = self.model(rec["entity1_id"]), self.model(rec["entity2_id"])
            if a and b and (a not in self.ent or b not in self.ent):
                self.tel["gekoppelde knoop niet (meer) in het model"] += 1
                continue
            if not a and not b:
                self.tel["geen kant gekoppeld"] += 1
                continue
            if not (a and b):
                self._tip(rec, a or b)
                continue
            if a == b:
                self.tel["beide kanten dezelfde knoop (dochter/moeder)"] += 1
                continue
            self.tel["beide kanten gekoppeld"] += 1
            if CAT_GEWICHT.get(cat) is None:
                self.ruis[littlesis.CATEGORIE[cat]] += 1
                continue
            bestaand = [x for x in self.paren.get((min(a, b), max(a, b)), [])
                        if x[1] in littlesis.PASSEND.get(cat, set()) | (AFFILIATIE if cat in (1, 3) else set())]
            if bestaand:
                rel = sorted(bestaand, key=lambda x: (x[2] != "goedgekeurd", x[0]))[0]
                if (rel[0], rec["sleutel"]) in self.geciteerd:
                    self.tel["extra bron: al geciteerd"] += 1
                    continue
                n = self.bronlijnen[rel[0]]
                dun = 0.4 if rel[0] in self.register else min(2.0, 2 / (1 + n))
                self.extra_bron.append({"rec": rec, "relation_id": rel[0], "type": rel[1], "status": rel[2],
                                        "mechanisme": rel[3], "bron": rel[4], "doel": rel[5], "bronlijnen": n,
                                        "register": rel[0] in self.register,
                                        "score": round(self.score(rec, a, b, False) * dun, 3)})
                self.tel["extra bron"] += 1
                continue
            andere = self.paren.get((min(a, b), max(a, b)), [])
            bron, doel = self._orienteer(rec, a, b)
            mech, rtype = self.mechanisme(rec, bron, doel)
            if mech is None:
                self.geen_theorie[rtype] += 1
                if len(self.geen_theorie_vb[rtype]) < 4:
                    self.geen_theorie_vb[rtype].append(f"{rec['regel']} (#{rec['id']})")
                continue
            if mech not in self.mech:
                self.geen_theorie[f"mechanisme {mech} bestaat niet"] += 1
                continue
            if any(x[1] == rtype and x[4] == bron and x[5] == doel for x in andere):
                self.tel["nieuw: zelfde type bestaat al"] += 1
                continue
            self.nieuw.append({"rec": rec, "bron": bron, "doel": doel, "type": rtype, "mechanisme": mech,
                               "start": datum(rec.get("start_date")), "eind": datum(rec.get("end_date")),
                               "functie": (rec.get("description1") or "")[:200] or None,
                               "ander_verband": [f"#{x[0]} {x[1]}" for x in andere],
                               "score": self.score(rec, bron, doel, True)})
            self.tel[f"nieuw: {rtype}/{mech}"] += 1
        # één nieuw verband per (bron, doel, type): het hoogst scorende record draagt het
        beste: dict[tuple, dict] = {}
        for n in sorted(self.nieuw, key=lambda n: -n["score"]):
            beste.setdefault((n["bron"], n["doel"], n["type"]), n)
        self.tel["nieuw: dubbel record (zelfde verband)"] = len(self.nieuw) - len(beste)
        self.nieuw = list(beste.values())
        # één extra bron per verband per run: het hoogst scorende record (de rest is dezelfde bronlijn)
        per_rel: dict[int, dict] = {}
        for x in sorted(self.extra_bron, key=lambda x: -x["score"]):
            per_rel.setdefault(x["relation_id"], x)
        self.tel["extra bron: tweede record voor hetzelfde verband"] = len(self.extra_bron) - len(per_rel)
        self.tel["extra bron"] = len(per_rel)
        self.extra_bron = list(per_rel.values())
        self.tel["nieuw zonder begin (datumzoeker)"] = sum(1 for n in self.nieuw if not n["start"])
        self.tel["met bronlink (nieuw + extra bron)"] = sum(1 for x in self.nieuw + self.extra_bron if x["rec"].get("bronlinks"))
        return self

    def _tip(self, rec: dict, gekoppeld: int):
        cat = rec["category_id"]
        if cat not in (1, 3, 10):
            self.ruis[f"één kant: {littlesis.CATEGORIE[cat]}"] += 1
            return
        ander_ls = rec["entity2_id"] if self.model(rec["entity1_id"]) else rec["entity1_id"]
        ander = self.data["entiteiten"].get(ander_ls) or {}
        hub = ander_ls in littlesis.HUBS
        nl = set(ander.get("nl") or []) & {"tekst", "website.nl"}
        if not (hub or nl):
            self.tel["één kant gekoppeld, andere niet NL/elite"] += 1
            return
        self.tel["tip: andere kant niet in het model"] += 1
        g = CAT_GEWICHT[cat] * (1.0 if rec.get("bronlinks") else 0.35) * (1.5 if hub else 1.0)
        self.tips.append({"score": round(g, 3), "model": self.ent[gekoppeld][0], "model_id": gekoppeld,
                          "littlesis": ander.get("name"), "littlesis_id": ander_ls, "soort": ander.get("primary_ext"),
                          "blurb": (ander.get("blurb") or "")[:100], "regel": rec["regel"], "link": rec["link"],
                          "bronlinks": rec.get("bronlinks")})

    # ── rapport ────────────────────────────────────────────────────────────
    def _rij(self, x: dict, soort: str) -> dict:
        rec = x["rec"]
        return {"score": x["score"], "soort": soort,
                "verband": (f"#{x['relation_id']} {x['type']}" + (f"/{x['mechanisme']}" if x.get("mechanisme") else "")
                            + f", {x['bronlijnen']} bronlijn(en){', register' if x['register'] else ''}"
                            if soort == "extra bron" else f"{x['type']}/{x['mechanisme']}"),
                "bron": self.ent[x["bron"]][0], "doel": self.ent[x["doel"]][0],
                "periode": f"{datum(rec.get('start_date')) or '?'} – {datum(rec.get('end_date')) or ('nu' if rec.get('is_current') else '?')}",
                "citaat": rec["regel"], "littlesis": rec["link"],
                "bronlinks": [b["url"] for b in rec.get("bronlinks") or []]}

    def rapport(self, top: int) -> dict:
        alles = sorted([self._rij(x, "nieuw") for x in self.nieuw] + [self._rij(x, "extra bron") for x in self.extra_bron],
                       key=lambda r: -r["score"])
        tips = sorted(self.tips, key=lambda t: -t["score"])
        return {"uitgave": self.uitgave, "telling": {k: v for k, v in sorted(self.tel.items()) if v},
                "nieuw": len(self.nieuw), "extra_bron": len(self.extra_bron),
                "geen_theorie": dict(self.geen_theorie.most_common()),
                "geen_theorie_voorbeelden": self.geen_theorie_vb,
                "ruis": dict(self.ruis.most_common()), "top": alles[:top],
                "tips_nieuwe_knoop": len(tips), "tips_top": tips[:30]}

    def markdown(self, rap: dict) -> str:
        r = ["# LittleSis → model: droogloop", "",
             f"Uitgave {rap['uitgave']} · nieuwe verbanden {rap['nieuw']} · extra bronnen {rap['extra_bron']} · "
             f"tips (nieuwe knoop nodig) {rap['tips_nieuwe_knoop']}", "",
             "Score = categorie × bronlink (1 / 0,35) × actualiteit × zeldzaamheid × elite-forum 1,5 × NL-kant 1,5 × nieuw 1,3; extra bron × 2/(1 + bronlijnen), registerfeit × 0,4.", "",
             "| # | score | soort | bron | doel | verband | periode | citaat (LittleSis) | bronlink |", "|---|---|---|---|---|---|---|---|---|"]
        for i, t in enumerate(rap["top"], 1):
            link = (t["bronlinks"] or ["—"])[0]
            r.append(f"| {i} | {t['score']} | {t['soort']} | {t['bron']} | {t['doel']} | {t['verband']} | {t['periode']} | "
                     f"{t['citaat']} ([LS]({t['littlesis']})) | {link} |")
        r += ["", "## Geen passend mechanisme (niet gepland)", ""]
        r += [f"- {k}: {v}" + (" — bv. " + "; ".join(rap["geen_theorie_voorbeelden"].get(k, [])[:2]) if rap["geen_theorie_voorbeelden"].get(k) else "")
              for k, v in rap["geen_theorie"].items()]
        r += ["", "## Ruis (alleen geteld)", ""] + [f"- {k}: {v}" for k, v in rap["ruis"].items()]
        r += ["", "## Tips: de andere kant staat nog niet in het model", "",
              "| score | in model | LittleSis | wat | citaat |", "|---|---|---|---|---|"]
        r += [f"| {t['score']} | {t['model']} | {t['littlesis']} | {t['blurb']} | {t['regel']} |" for t in rap["tips_top"]]
        return "\n".join(r) + "\n"


class Indiener:
    """Langs het gewone bijdragepad (account `assistent`): per LittleSis-relatie een bron met de
    relatiepagina als vindplaats, dan (bij een nieuw verband) de relatie, dan het argument."""

    def __init__(self, plan: Plan, rest, log=print):
        self.p, self.rest, self.log = plan, rest, log
        self.tel = Counter()

    def _bron(self, rec: dict) -> int | None:
        status, res = self.rest("POST", "/api/sources", {
            "title": f"LittleSis: {rec['regel']}"[:300], "source_type": "website", "publisher": littlesis.UITGEVER,
            "date_published": (rec.get("updated_at") or "")[:10] or None, "language": "en", "cluster_key": CLUSTER,
            "location": {"type": "url", "value": rec["link"]},
            "reliability_voorgesteld": "grijs", "onderwerp_voorgesteld": "onbepaald"})
        if status not in (200, 201):
            self.tel[f"bron fout {status}"] += 1
            self.log(f"  ✗ bron {rec['sleutel']}: {status} {res.get('error')}")
            return None
        return res["id"]

    def _argument(self, rid: int, rec: dict, bron_id: int, bron: int, doel: int):
        namen = f"{self.p.ent[bron][0]} en {self.p.ent[doel][0]}"
        label = {"positie": "functie", "donatie": "gift"}.get(rec["categorie"], rec["categorie"])
        claim = (f"Volgens LittleSis ({label} tussen {namen}, relatie {rec['id']}): "
                 f"\"{rec['regel']}\" (periode {datum(rec.get('start_date')) or 'onbekend'} – "
                 f"{datum(rec.get('end_date')) or ('lopend' if rec.get('is_current') else 'onbekend')}).")
        context = "LittleSis-relatie " + rec["link"] + "; bronlinks van LittleSis: " + (
            ", ".join(b["url"] for b in rec.get("bronlinks") or []) or "geen")
        status, res = self.rest("POST", "/api/arguments", {
            "relation_id": rid, "claim": claim, "stance": "supporting",
            "citations": [{"source_id": bron_id, "quote": rec["regel"], "methode": "verbatim_quote",
                           "section": rec["sleutel"], "page": f"{littlesis.BRON}/{self.p.uitgave}",
                           "context": context[:1000]}]})
        self.tel["argument" if status == 201 else f"argument fout {status}"] += 1
        if status != 201:
            self.log(f"  ✗ argument {rec['sleutel']} op #{rid}: {status} {res.get('error')}")

    def indienen(self):
        for x in self.p.extra_bron:
            b = self._bron(x["rec"])
            if b:
                self._argument(x["relation_id"], x["rec"], b, x["bron"], x["doel"])
        for x in self.p.nieuw:
            b = self._bron(x["rec"])
            if not b:
                continue
            body = {"source_id": x["bron"], "target_id": x["doel"], "relation_type": x["type"],
                    "mechanism_id": self.p.mech[x["mechanisme"]], "functie": x["functie"]}
            if x["start"]:
                body["active_from"] = x["start"]
            if x["eind"]:
                body["active_until"] = x["eind"]
            status, res = self.rest("POST", "/api/relations", body)
            if status != 201:
                self.tel[f"relatie fout {status}"] += 1
                self.log(f"  ✗ relatie {x['rec']['sleutel']}: {status} {res.get('error')}")
                continue
            self.tel["relatie nieuw"] += 1
            self._argument(res["id"], x["rec"], b, x["bron"], x["doel"])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave")
    ap.add_argument("--top", type=int, default=TOP)
    ap.add_argument("--indienen", action="store_true")
    ap.add_argument("--token", type=Path, default=TOKEN)
    ap.add_argument("--haal", action="store_true", help="eerst een nieuwe uitgave ophalen (dumps + bronlinks, ± 1 uur)")
    a = ap.parse_args()
    if a.haal and not a.uitgave:
        littlesis.haal()
    pad = littlesis.pad_van(a.uitgave) if a.uitgave else (littlesis.uitgaven() or [None])[-1]
    if not pad or not pad.exists():
        raise SystemExit("nog geen LittleSis-uitgave; eerst: python3 tools/registers/littlesis.py haal")
    data = littlesis.lees(pad)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    plan = Plan(data, conn).maak()
    rap = plan.rapport(a.top)
    littlesis.MAP.mkdir(parents=True, exist_ok=True)
    (littlesis.MAP / f"rapport_{plan.uitgave}.json").write_text(json.dumps(rap, ensure_ascii=False, indent=1), encoding="utf-8")
    (littlesis.MAP / f"rapport_{plan.uitgave}.md").write_text(plan.markdown(rap), encoding="utf-8")
    print(json.dumps({k: rap[k] for k in ("uitgave", "nieuw", "extra_bron", "tips_nieuwe_knoop", "telling",
                                           "geen_theorie", "ruis")}, ensure_ascii=False, indent=1))
    print(f"\nTop {a.top}:")
    for i, t in enumerate(rap["top"], 1):
        print(f"{i:>3}. {t['score']:>5} {t['soort']:<10} {t['bron']} — {t['doel']} [{t['verband']}, {t['periode']}]\n"
              f"       “{t['citaat']}” {t['littlesis']}" + (f"\n       bron: {t['bronlinks'][0]}" if t["bronlinks"] else ""))
    if not a.indienen:
        print(f"\n(droogloop — niets ingediend; rapport in {littlesis.MAP}/rapport_{plan.uitgave}.md)")
        return
    from naar_model import Rest
    ind = Indiener(plan, Rest(a.token.read_text().strip()))
    ind.indienen()
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
