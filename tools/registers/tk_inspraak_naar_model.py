#!/usr/bin/env python3
"""Tweede Kamer, wie mag inspreken → het model (2026-10-20). Het parlementaire spiegelbeeld van
agenda_naar_model.py: niet wie een bewindspersoon spreekt, maar wie een Kamercommissie hoort.

tk_inspraak.py leest de records (position papers, genodigden bij rondetafelgesprekken,
hoorzittingen en briefings, de tegenpartij van een gesprek of petitie); dit script kiest wat telt
en dient het in, zonder AI:
  1. trechter: de voortouwcommissie controleert het bestuur (tk.controlerende_commissie); de
     organisatie staat al in het model en staat onder haar eigen naam in het deel van de regel waar
     de indiener, genodigde of tegenpartij staat (common.noemt, zoals de registercheck); geen
     privépersonen (ervaringsdeskundige, burger, ouder …, ook via de blokkop).
  2. instituut of persoon (eigenaarsbesluit 2026-10-19): een position paper of de leiding of een
     medewerker die namens de organisatie spreekt, is organisatie → commissie. Een hoogleraar,
     onderzoeker, advocaat of arts op eigen titel is de persoonsroute (`expert_naar_politiek` met
     namens_id): die telt in het rapport bij zijn organisatie, maar wordt hier niet gepland
     (personen niet op naam). Bij een denktank spreekt alleen de leiding namens het instituut
     (precedent RfC 118: de Clingendael-onderzoekers bij het rondetafelgesprek van 16 april 2026).
  3. mechanisme naar wat de organisatie is (MECHANISMEN hieronder):
       denktank                          → `adviseur`, `denktank_naar_politiek` (#54; precedent #1984)
       wettelijk adviescollege/planbureau → `adviseur`, `institutioneel_advies` (#217)
       belangenorganisatie, bedrijf, vakbond, ngo → `lobbyt`, `lobbyist_naar_politicus` (#50)
     Geen mechanisme (alleen rapport): overheid (ministerie, uitvoering, toezicht, gemeenten en
     hun koepels), media, kennisinstellingen (universiteit, kennisinstituut: hun deskundigen zijn
     de persoonsroute), partijen, elite-netwerken.
  4. sterkte is opvallendheid: lift = n(org, commissie) / verwacht als de organisatie gelijk over
     de commissies verdeeld was; score = keren × log2(lift) (keren = verschillende activiteiten of
     papers). Sterke signalen: de organisatie heeft een toegangspas (lobbyistenregister) of spreekt
     het ministerie van hetzelfde beleidsterrein (agenda's, data/registers/agenda/analyse.json).
  5. indienen (onder `register-import`, citaat = de recordregel, methode
     `officieel_register_scrape`, page `tk_inspraak/<uitgave>`, section = recordsleutel):
     - een bestaand verband organisatie → commissie (zelfde type) krijgt elke nog niet geciteerde
       inbreng als extra argument;
     - anders een nieuw verband vanaf MIN_KEREN keer inbreng namens de organisatie;
     - een optreden dat al op een ander verband van de organisatie staat (Clingendael → Tweede
       Kamer #1984 citeert het paper van 16 april 2026) wordt niet nog eens gebruikt: één optreden,
       één verband.
     Hooguit MAX_PER_VERBAND nieuwe argumenten per verband per run (de nieuwste eerst).
De registercheck (stap 2b, tk_inspraak.controleer) toetst daarna elk argument.

Gebruik:
    python3 tools/registers/tk_inspraak_naar_model.py                    # droogloop + rapport
    python3 tools/registers/tk_inspraak_naar_model.py --haal             # eerst een nieuwe uitgave
    python3 tools/registers/tk_inspraak_naar_model.py --indienen         # echt indienen (REST)
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
import agenda  # noqa: E402
import tk  # noqa: E402
import tk_inspraak as tki  # noqa: E402
import tk_naar_model as tkm  # noqa: E402
from common import ROOT, klem_relaties, namen_van, sleutel  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
CLUSTER = "register:tk_inspraak"
MIN_KEREN = 2          # een nieuw verband vanaf zoveel keer inbreng namens de organisatie
MAX_PER_VERBAND = 5    # nieuwe argumenten per verband per run
TOP = 30
NGO_ALS_LOBBY = True   # ngo's en ideële stichtingen als belangenbehartiger (#83 noemt "ideologisch/NGO")

OVERHEID_TYPES = {"overheidsinstelling", "rechterlijke_macht", "toezichthouder"}
MEDIA_TYPES = {"mediaorganisatie", "omroep", "persbureau"}
MEDIA_ROLLEN = {"mediaorganisatie", "redactie", "alternatief_medium", "onderzoeksjournalist", "mediaeigenaar",
                "journalist", "ledenomroep", "omroepkoepel", "persbureau", "journalistiek_beroepsnetwerk"}
KENNIS_ROLLEN = {"kennisinstituut", "gezagsinstituut", "gezagsexpert"}
BELANG_TYPES = {"lobbygroep", "pr_bureau", "bedrijf", "vakbond", "platform", "vermogensbeheerder"}
BELANG_ROLLEN = {"lobbyist", "belanghebbende", "sociale_partner", "adverteerder", "techplatform", "aandeelhouder",
                 "vakbond_media", "overnamevehikel"}
NGO_TYPES = {"ngo", "stichting"}
NGO_ROLLEN = {"maatschappelijke_organisatie", "borgingsstichting", None}
MECHANISMEN = ("denktank_naar_politiek", "institutioneel_advies", "lobbyist_naar_politicus")
# beleidsterrein van een commissie → ministerie (oo-id, zoals agenda.MINISTERIES), voor het agenda-signaal
COMMISSIE_MINISTERIE = {
    "buitenlandse handel en ontwikkelingssamenwerking": "2515", "europese zaken": "2515",
    "koninkrijksrelaties": "9632", "binnenlandse zaken": "9632", "digitale zaken": "9632",
    "economische zaken en klimaat": "10621", "landbouw natuur en voedselkwaliteit": "22387697",
}
THEMA_STOP = set("""rondetafelgesprek rondetafelgesprekken technische briefing gesprek gesprekken petitie position
paper papers hoorzitting wetsvoorstel wetsvoorstellen wijziging voorstel verband invoering nederland nederlandse
tweede kamer commissie aanbieding rondom tussen onderwerp situatie toekomst aanpak ontwikkelingen stand zaken
openbaar besloten initiatiefwetsvoorstel kabinet beleid regels rapport onderzoek""".split())


class Plan(tkm.Plan):
    def __init__(self, data: dict, conn: sqlite3.Connection, koppelingen: dict | None = None,
                 lobby_ids: set[int] | None = None, agenda_rijen: list[dict] | None = None):
        super().__init__({"uitgave": data["uitgave"], "personen": {}, "records": {}}, conn, koppelingen)
        self.data = data
        self.mech.update(self._ids("mechanisms", MECHANISMEN))
        self.rol.update(self._ids("roles", ("parlementair_controleur",)))
        self.rol_van = {i: r for i, r in conn.execute(
            "SELECT e.id, r.name FROM entities e LEFT JOIN roles r ON r.id = e.primary_role_id "
            "WHERE e.type <> 'persoon' AND NOT e.vervangen")}
        self.adviescolleges = {s for (s,) in conn.execute("""
            SELECT r.source_id FROM relations r JOIN mechanisms m ON m.id = r.mechanism_id
            WHERE m.name = 'institutioneel_advies' AND NOT r.vervangen AND r.status <> 'afgewezen'""")}
        # organisaties onder hun eigen naam (geen metadata-afkorting: de registercheck leest de naam);
        # een sleutel van twee organisaties telt niet. Niet: partijen, de Kamer en haar commissies.
        per_sleutel: dict[str, set[int]] = defaultdict(set)
        for eid, (naam, typ, _laag) in self.org.items():
            if eid < 0 or typ == "partij" or self._partij_eigen(naam) or eid == self.tweede_kamer \
                    or self.rol_van.get(eid) == "parlementair_controleur":
                continue
            for k in namen_van(naam):
                if len(k) >= 3:
                    per_sleutel[k].add(eid)
        self.zoek: dict[str, list[tuple[list[str], int]]] = defaultdict(list)
        for k, ids in per_sleutel.items():
            if len(ids) == 1:
                self.zoek[k.split()[0]].append((k.split(), next(iter(ids))))
        # vastgelegde schrijfwijzen uit de Kamerregisters (koppelingen.json 'tk_namen'; de registercheck
        # leest dezelfde lijst): 'Instituut Clingendael' → 'Clingendael Instituut'
        uniek = {k: next(iter(ids)) for k, ids in per_sleutel.items() if len(ids) == 1}
        for variant, model in tk.schrijfwijzen().items():
            eid = next((uniek[k] for k in namen_van(model) if k in uniek), None)
            k = sleutel(variant)
            if eid and len(k) >= 3 and k not in per_sleutel:
                self.zoek[k.split()[0]].append((k.split(), eid))
        # voor de tiplijst: een naam die alleen in woordvolgorde van een modelnaam verschilt
        self.woordenset: dict[frozenset, int] = {}
        for k, eid in uniek.items():
            if len(k.split()) >= 2:
                self.woordenset.setdefault(frozenset(k.split()), eid)
        self.schrijfwijze_tips: Counter = Counter()
        # een afkorting telt alleen in haar eigen schrijfwijze: 'RvS' (Raad van State) is niet
        # 'RVS (Raad voor Volksgezondheid en Samenleving)', 'Ing.' is niet ING
        self.exact: dict[tuple[str, int], str] = {}
        for eid, (naam, _t, _l) in self.org.items():
            m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", naam or "")
            for vorm in ([naam] + ([m.group(1), m.group(2)] if m else [])):
                vorm = (vorm or "").strip()
                if vorm and " " not in vorm and sum(c.isupper() for c in vorm) >= 2:
                    self.exact[(sleutel(vorm), eid)] = vorm
        # bestaande verbanden organisatie → commissie, en wat de import daar al citeerde
        self.bestaand = {(s, t, rt): rid for rid, s, t, rt in conn.execute("""
            SELECT id, source_id, target_id, relation_type FROM relations
            WHERE relation_type IN ('lobbyt', 'adviseur') AND NOT vervangen AND status <> 'afgewezen'""")}
        self.geciteerd: dict[int, set[str]] = defaultdict(set)
        # elk citaat op een levend verband van een organisatie: is dit optreden al ergens gebruikt?
        self.citaten: dict[int, list[tuple[int, str, str]]] = defaultdict(list)
        for rid, src, sec, page, quote in conn.execute("""
                SELECT r.id, r.source_id, c.section, c.page, c.quote FROM citations c
                JOIN arguments a ON a.id = c.argument_id JOIN relations r ON r.id = a.relation_id
                WHERE NOT r.vervangen AND r.status <> 'afgewezen' AND NOT a.vervangen"""):
            if (page or "").startswith(f"{tki.BRON}/"):
                self.geciteerd[rid].add(sec)
            self.citaten[src].append((rid, sec or "", sleutel(quote)))
        self.kamerverbanden: dict[int, list[str]] = defaultdict(list)
        for s, mnaam, rt in conn.execute("""
                SELECT r.source_id, m.name, r.relation_type FROM relations r JOIN mechanisms m ON m.id = r.mechanism_id
                WHERE r.target_id = ? AND NOT r.vervangen AND r.status <> 'afgewezen'""", (self.tweede_kamer,)):
            self.kamerverbanden[s].append(f"{rt}/{mnaam}")
        self.lobby_ids = lobby_ids or set()
        self.agenda: dict[int, list[dict]] = defaultdict(list)
        for a in agenda_rijen or []:
            self.agenda[a["org_id"]].append(a)
        self.ministerie_oo = {e: w for e, w in conn.execute("SELECT entity_id, waarde FROM externe_ids WHERE stelsel = 'oo'")}
        self.optredens: dict[tuple[int, str], list[dict]] = defaultdict(list)
        self.commissies: dict[str, dict] = {}
        self.tips: dict[str, Counter] = defaultdict(Counter)
        self.persoonlijk_per_org: Counter = Counter()
        self.analyse: list[dict] = []
        self.argumenten: list[dict] = []

    # ── herkennen ──────────────────────────────────────────────────────────
    def _organisaties(self, tekst: str) -> set[int]:
        """Organisaties die als hele woorden in de tekst staan; bij overlap wint de langste."""
        woorden = sleutel(tekst).split()
        treffers = []
        for i, w in enumerate(woorden):
            for kw, eid in self.zoek.get(w, ()):
                if woorden[i:i + len(kw)] == kw and self._schrijfwijze_klopt(tekst, kw, eid):
                    treffers.append((i, i + len(kw), eid))
        return {eid for a, b, eid in treffers
                if not any(a2 <= a and b <= b2 and (b2 - a2) > (b - a) for a2, b2, _ in treffers)}

    def _schrijfwijze_klopt(self, tekst: str, kw: list[str], eid: int) -> bool:
        """Een afkorting (één woord, twee of meer hoofdletters) moet zo in de tekst staan, of met alleen
        een beginhoofdletter ('Pax voor Vrede') als er geen punt achter staat ('Ing.')."""
        vorm = self.exact.get((" ".join(kw), eid)) if len(kw) == 1 else None
        if not vorm:
            return True
        for variant in {vorm, vorm[:1] + vorm[1:].lower()}:
            for m in re.finditer(rf"(?<![\w]){re.escape(variant)}(?![\w])", tekst):
                if variant == vorm or (len(vorm) >= 3 and tekst[m.end():m.end() + 1] != "."):
                    return True
        return False

    def mechanisme(self, eid: int) -> tuple[str | None, str | None, str]:
        """→ (relatietype, mechanisme, groep) of (None, None, reden)."""
        naam, typ, laag = self.org[eid]
        rol = self.rol_van.get(eid)
        if (eid in self.adviescolleges or rol == "adviesorgaan") and typ != "toezichthouder":
            return "adviseur", "institutioneel_advies", "adviescollege of planbureau"
        if typ == "denktank" or rol == "denktank":
            return "adviseur", "denktank_naar_politiek", "denktank"
        if laag or typ in OVERHEID_TYPES:
            return None, None, "overheid (verantwoording of mede-overheid, geen inspraak van buiten)"
        if typ in MEDIA_TYPES or rol in MEDIA_ROLLEN:
            return None, None, "medium"
        if typ == "onderwijsinstelling" or rol in KENNIS_ROLLEN:
            return None, None, "kennisinstelling (geen institutioneel mechanisme; deskundigen: expert_naar_politiek)"
        if rol == "consultant":
            return None, None, "consultancy (inhuur_consultancy loopt naar het departement)"
        if typ in BELANG_TYPES and rol is None:
            return None, None, f"{typ} zonder rol in het model (eerst typeren)"
        if typ in BELANG_TYPES or rol in BELANG_ROLLEN:
            return "lobbyt", "lobbyist_naar_politicus", "belangenorganisatie of bedrijf"
        if typ in NGO_TYPES and rol in NGO_ROLLEN and NGO_ALS_LOBBY:
            return "lobbyt", "lobbyist_naar_politicus", "ngo of ideële stichting"
        return None, None, f"geen passend mechanisme ({typ}/{rol or '-'})"

    @staticmethod
    def _orgachtig(tekst: str) -> bool:
        """Lijkt dit op een organisatie (voor de tiplijst; nooit een persoon)?"""
        if tki._PERSOON.match(tekst) or len(tekst) > 80:
            return False
        return bool(re.search(r"\b[A-Z][A-Za-z]*[A-Z]{1,}\w*\b", tekst) or re.search(
            r"(?i)\b(stichting|vereniging|instituut|centrum|raad|federatie|bond|platform|coalitie|netwerk|"
            r"nederland|groep|b\.?v\.?|n\.?v\.?|universiteit|hogeschool|fonds|bank|alliantie|branche|organisatie|"
            r"collectief|partners|associatie|koepel|unie|genootschap|academie|kamer van)\b", tekst))

    # ── plannen ────────────────────────────────────────────────────────────
    def maak(self):
        for rec in self.data["records"].values():
            self.tel["records"] += 1
            if rec["soort"] == "positionpaper" and rec.get("indiener_persoon"):
                self.tel["overgeslagen: position paper op eigen naam (persoon)"] += 1
                continue
            crec = {"commissie": rec["commissie"], "commissie_soort": rec.get("commissie_soort")}
            if not tk.controlerende_commissie(crec):
                self.tel["overgeslagen: geen controlerende commissie (delegatie, contactgroep …)"] += 1
                continue
            orgs = self._organisaties(rec["wie"])
            if not orgs:
                self.tel[f"{rec['soort']}: geen bekende organisatie"] += 1
                if rec["soort"] in ("positionpaper", "tegenpartij") and self._orgachtig(rec["wie"]):
                    gelijk = self.woordenset.get(frozenset(sleutel(rec["wie"]).split()))
                    if gelijk:
                        self.schrijfwijze_tips[(rec["wie"], self.org[gelijk][0])] += 1
                    else:
                        self.tips[rec["wie"]][tk.commissie_naam(rec)] += 1
                continue
            naam_c = tk.commissie_naam(rec)
            self.commissies.setdefault(naam_c, {k: rec.get(k) for k in (
                "commissie", "commissie_soort", "commissie_actief", "commissie_inactief")})
            for eid in orgs:
                pet, prive = tki.hoedanigheid(rec, [self.org[eid][0]])
                if prive:
                    self.tel["overgeslagen: privépersoon"] += 1
                    continue
                rtype, mech, groep = self.mechanisme(eid)
                planbaar = pet in ("leiding", "namens")
                reden = None
                if not planbaar:
                    reden = f"op eigen titel ({pet})"
                    self.persoonlijk_per_org[eid] += 1
                elif rec["soort"] == "genodigde" and len(orgs) > 1:
                    planbaar, reden = False, "meerdere organisaties in één regel"
                elif mech == "denktank_naar_politiek" and rec["soort"] == "genodigde" and pet != "leiding":
                    planbaar, reden = False, "denktank: medewerker op eigen titel (RfC 118)"
                self.optredens[(eid, naam_c)].append({"rec": rec, "pet": pet, "planbaar": planbaar, "reden": reden,
                                                      "keer": rec.get("activiteit") or rec.get("zaak")})
                self.tel[f"optreden: {rec['soort']} ({pet})"] += 1
        self._scoor()
        self._kies()
        return self

    @staticmethod
    def _thema(recs: list[dict], naam: str) -> list[str]:
        """Woorden of dossiers die in de onderwerpen van minstens twee verschillende activiteiten
        terugkomen (zonder de naam van de organisatie zelf, die in elk paper staat)."""
        eigen = {w for k in namen_van(naam) for w in k.split()} | set(sleutel(naam).split())
        per_keer: dict[str, set[str]] = defaultdict(set)
        for r in recs:
            tekst = re.sub(r"\bd\.\s?d\..*$", "", r["onderwerp"] or "")
            if r["soort"] == "positionpaper":
                tekst = tki._PP.sub(r"\g<rest>", tekst)
            woorden = {w for w in sleutel(tekst).split()
                       if len(w) >= 6 and w not in THEMA_STOP and w not in eigen and not w.isdigit()}
            woorden |= {f"dossier {d.split()[0]}" for d in r.get("dossiers") or []}
            per_keer[r.get("activiteit") or r.get("zaak")] |= woorden
        tel = Counter(w for ws in per_keer.values() for w in ws)
        return [f"{w} ({n}×)" for w, n in tel.most_common(3) if n >= 2]

    def _ministerie_van(self, commissie: str) -> str | None:
        kaal = sleutel(re.sub(r"\s*\(\d{4}-\d{4}\)\s*$", "", re.sub(r"(?i)^vaste commissie voor\s+", "", commissie)))
        if kaal in COMMISSIE_MINISTERIE:
            return COMMISSIE_MINISTERIE[kaal]
        for naam, oo_id in agenda.MINISTERIES.items():
            if sleutel(naam) == kaal or sleutel(naam).startswith(kaal + " "):
                return oo_id
        return None

    def _scoor(self):
        n_org, n_com = Counter(), Counter()
        keren = {p: {o["keer"] for o in lijst} for p, lijst in self.optredens.items()}
        for (o, c), k in keren.items():
            n_org[o] += len(k)
            n_com[c] += len(k)
        totaal = sum(n_org.values()) or 1
        for (o, c), lijst in self.optredens.items():
            k = len(keren[(o, c)])
            lift = k * totaal / (n_org[o] * n_com[c])
            rtype, mech, groep = self.mechanisme(o)
            plan = [x for x in lijst if x["planbaar"]]
            recs = [x["rec"] for x in lijst]
            oo_min = self._ministerie_van(self.commissies[c]["commissie"])
            agenda_hier = [a for a in self.agenda.get(o, []) if self.ministerie_oo.get(a["ministerie_id"]) == oo_min]
            signalen = []
            if o in self.lobby_ids:
                signalen.append("toegangspas (lobbyistenregister)")
            if agenda_hier:
                a = agenda_hier[0]
                signalen.append(f"agenda: {a['ministerie']} {a['dagen']} dagen (lift {a['lift']})")
            elif self.agenda.get(o):
                signalen.append(f"agenda: {sum(a['dagen'] for a in self.agenda[o])} dagen bij andere ministeries")
            if self.kamerverbanden.get(o):
                signalen.append("verband met de Kamer: " + ", ".join(sorted(set(self.kamerverbanden[o]))))
            voorbeeld = max(plan or lijst, key=lambda x: (x["rec"]["soort"] != "genodigde", x["rec"]["datum"] or ""))["rec"]
            self.analyse.append({
                "org_id": o, "organisatie": self.org[o][0], "type": self.org[o][1], "rol": self.rol_van.get(o),
                "commissie": c, "keren": k, "keren_namens": len({x["keer"] for x in plan}),
                "position_papers": sum(1 for x in lijst if x["rec"]["soort"] == "positionpaper"),
                "genodigde": sum(1 for x in lijst if x["rec"]["soort"] == "genodigde"),
                "tegenpartij": sum(1 for x in lijst if x["rec"]["soort"] == "tegenpartij"),
                "op_eigen_titel": sum(1 for x in lijst if x["pet"] in ("persoonlijk", "oud")),
                "organisatie_totaal": n_org[o], "commissies_gehoord": sum(1 for (o2, _c) in self.optredens if o2 == o),
                "lift": round(lift, 2), "score": round(k * math.log2(max(lift, 1.0)), 2),
                "relatietype": rtype, "mechanisme": mech, "groep": groep, "signalen": signalen,
                "sterk": bool(o in self.lobby_ids or any(x["dagen"] >= 2 and x["lift"] >= 1 for x in agenda_hier)),
                "thema": self._thema(recs, self.org[o][0]),
                "van": min((r["datum"] for r in recs if r["datum"]), default=None),
                "tot": max((r["datum"] for r in recs if r["datum"]), default=None),
                "status": None, "voorbeeld": voorbeeld["regel"], "voorbeeld_sleutel": voorbeeld["sleutel"]})
        self.analyse.sort(key=lambda a: (-a["score"], -a["keren"]))

    def _al_elders(self, eid: int, rec: dict, rid: int | None) -> int | None:
        """Staat dit optreden al op een ander verband van deze organisatie? (één optreden, één verband)"""
        tekst = rec["wie"] if rec["soort"] == "genodigde" else rec["onderwerp"]
        kern = sleutel(tekst)
        # alleen een tekst die meer zegt dan de naam (een persoon, functie of onderwerp erbij)
        vergelijk = len(kern) >= 25 and len(tki._zonder(tekst, [self.org[eid][0]])) >= 12
        for r2, sec, quote in self.citaten.get(eid, ()):
            if r2 == rid:
                continue
            if sec == rec["sleutel"] or (vergelijk and kern in quote):
                return r2
        return None

    def _commissie_ref(self, naam_c: str) -> tuple:
        if (naam_c, "overheidsinstelling") in self.op_naam_type:
            return ("bestaand", self.op_naam_type[(naam_c, "overheidsinstelling")])
        k = f"commissie:{sleutel(naam_c)}"
        if k not in self.nieuwe_orgs:
            c = self.commissies[naam_c]
            self.nieuwe_orgs[k] = {
                "naam": naam_c, "type": "overheidsinstelling", "rol": "parlementair_controleur", "bestuurslaag": "rijk",
                "active_from": c.get("commissie_actief"), "active_until": c.get("commissie_inactief"),
                "beschrijving": ("Commissie van de Tweede Kamer"
                                 + (f" (rubriek '{c['commissie_soort']}')" if c.get("commissie_soort") else "")
                                 + (f", actief {c['commissie_actief']}" if c.get("commissie_actief") else "")
                                 + (f" tot {c['commissie_inactief']}" if c.get("commissie_inactief") else "")
                                 + " (open data Tweede Kamer).")}
            self.tel["nieuwe commissie (opgeheven of nog niet in het model)"] += 1
        return ("nieuw", k)

    def _kies(self):
        self.relaties = []
        for a in self.analyse:
            o, c = a["org_id"], a["commissie"]
            if not a["mechanisme"]:
                a["status"] = f"geen mechanisme: {a['groep']}"
                self.tel["paar: geen mechanisme"] += 1
                continue
            if a["keren_namens"] == 0:
                a["status"] = "alleen op eigen titel of gedeeld (niet gepland)"
                self.tel["paar: alleen persoonsroute of gedeelde regel"] += 1
                continue
            cid = self.op_naam_type.get((c, "overheidsinstelling"))
            rid = self.bestaand.get((o, cid, a["relatietype"])) if cid else None
            if rid is None and a["keren_namens"] < MIN_KEREN:
                a["status"] = "te weinig (rapport)"
                self.tel["paar: te weinig"] += 1
                continue
            plan = sorted((x for x in self.optredens[(o, c)] if x["planbaar"]),
                          key=lambda x: (x["rec"]["datum"] or "", x["rec"]["sleutel"]), reverse=True)
            nieuw = []
            for x in plan:
                if x["rec"]["sleutel"] in self.geciteerd.get(rid, set()):
                    continue
                elders = self._al_elders(o, x["rec"], rid)
                if elders:
                    self.tel["optreden staat al op een ander verband (één optreden, één verband)"] += 1
                    a.setdefault("al_elders", []).append(f"{x['rec']['sleutel']} → #{elders}")
                    continue
                nieuw.append(x["rec"])
            if rid is None and len({r.get("activiteit") or r.get("zaak") for r in nieuw}) < MIN_KEREN:
                a["status"] = "te weinig na ontdubbelen (rapport)"
                self.tel["paar: te weinig na ontdubbelen"] += 1
                continue
            nieuw = nieuw[:MAX_PER_VERBAND]
            ref_c = self._commissie_ref(c)
            a["status"] = "versterkt" if rid else "nieuw"
            a["argumenten"] = len(nieuw)
            self.tel[f"paar: {a['status']}"] += 1
            if not rid:
                start = min(r["datum"] for r in nieuw if r["datum"])
                self.relaties.append({"bron": ("bestaand", o), "doel": ref_c, "type": a["relatietype"],
                                      "mechanisme": a["mechanisme"], "start": start, "eind": None,
                                      "analyse": a})
            for r in nieuw:
                self.argumenten.append({"org": o, "commissie": ref_c, "relatie": rid, "type": a["relatietype"],
                                        "mechanisme": a["mechanisme"], "rec": r})
            self.tel["argumenten gepland"] += len(nieuw)
            self.tel[f"argumenten gepland: {a['mechanisme']}"] += len(nieuw)
        klem_relaties(self.relaties, self._bestaan_van, self.tel)
        for r in self.relaties:
            r["analyse"]["start"] = r["start"]

    def _bestaan_van(self, ref) -> tuple:
        if ref[0] == "nieuw":
            o = self.nieuwe_orgs.get(ref[1]) or {}
            return o.get("active_from"), o.get("active_until")
        return super()._bestaan_van(ref)

    # ── rapport ────────────────────────────────────────────────────────────
    def rapport(self) -> str:
        t = self.tel
        nieuw = [a for a in self.analyse if a["status"] == "nieuw"]
        versterkt = [a for a in self.analyse if a["status"] == "versterkt"]
        kandidaten = [a for a in self.analyse if a["mechanisme"]]

        def rij(i, a, met_status=True):
            return (f"| {i} | {a['organisatie']} ({a['type']}) | {a['commissie'].replace(' (Tweede Kamer)', '')} | "
                    f"{a['keren']} ({a['keren_namens']} namens) | {a['position_papers']}/{a['genodigde']}/{a['tegenpartij']} | "
                    f"{a['lift']} | {a['score']} | {(a['mechanisme'] or '-')} | {'; '.join(a['signalen']) or '-'} | "
                    f"{', '.join(a['thema']) or '-'} | {a['van']} – {a['tot']}"
                    + (f" | {a['status']}" if met_status else "") + " |")
        kop = ("| # | organisatie | commissie | keren | pp/gen/teg | lift | score | mechanisme | signalen | "
               "terugkerend thema | periode |")
        regels = [
            "# Wie mag inspreken bij de Tweede Kamer: opvallende inbreng per commissie", "",
            f"Uitgave {self.uitgave} (open data Tweede Kamer, sinds {tki.SINDS}). Records: {t['records']} · "
            f"optredens van een bekende organisatie: {sum(len(v) for v in self.optredens.values())} · paren "
            f"organisatie × commissie: {len(self.analyse)} (nieuw {t['paar: nieuw']}, versterkt {t['paar: versterkt']}, "
            f"te weinig {t['paar: te weinig'] + t['paar: te weinig na ontdubbelen']}, geen mechanisme "
            f"{t['paar: geen mechanisme']}, alleen op eigen titel {t['paar: alleen persoonsroute of gedeelde regel']}) · "
            f"argumenten gepland: {t['argumenten gepland']}.", "",
            "Score = keren × log2(lift); lift = inbreng bij deze commissie ÷ verwacht bij een gelijke verdeling over "
            "de commissies. Keren = verschillende activiteiten of papers. pp/gen/teg = position papers / genodigde "
            "/ tegenpartij van een gesprek, petitie of briefing. Sterk signaal = ook een toegangspas "
            "(lobbyistenregister) of ook bij het ministerie van hetzelfde beleidsterrein (agenda's).", "",
            f"## Nieuwe verbanden (gepland: {len(nieuw)})", "", kop + " argumenten |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        regels += [rij(i, a, False)[:-1] + f"| {a.get('argumenten', 0)} |" for i, a in enumerate(nieuw, 1)]
        regels += ["", f"## Extra bronnen op bestaande verbanden ({len(versterkt)})", ""]
        if versterkt:
            regels += [kop + " argumenten |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
            regels += [rij(i, a, False)[:-1] + f"| {a.get('argumenten', 0)} |" for i, a in enumerate(versterkt, 1)]
        else:
            regels.append("Nog geen verband organisatie → commissie in het model; een volgende run vult de verbanden "
                          "uit deze run aan. Inbreng die al op een ander verband staat, wordt niet hergebruikt:")
            regels += [f"- {a['organisatie']} → {a['commissie']}: {', '.join(a['al_elders'])}"
                       for a in self.analyse if a.get("al_elders")]
        regels += ["", f"## Top-{TOP} (organisaties met een passend mechanisme)", "", kop + " status |",
                   "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        regels += [rij(i, a) for i, a in enumerate(kandidaten[:TOP], 1)]
        sterk = [a for a in kandidaten if a["sterk"]]
        regels += ["", f"## Sterke signalen: ook in het lobbyistenregister of bij het ministerie van hetzelfde "
                       f"beleidsterrein ({len(sterk)})", "", kop + " status |",
                   "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        regels += [rij(i, a) for i, a in enumerate(sterk[:TOP], 1)]
        terug = sorted((a for a in kandidaten if a["thema"] and a["keren"] >= 2),
                       key=lambda a: (-int(a["thema"][0].rsplit("(", 1)[1].rstrip("×)")), -a["score"]))
        regels += ["", "## Terugkerend bij hetzelfde dossier of thema", ""]
        regels += [f"- {a['organisatie']} → {a['commissie'].replace(' (Tweede Kamer)', '')}: {', '.join(a['thema'])}"
                   for a in terug[:25]]
        breed = sorted({a["org_id"]: a for a in self.analyse}.values(), key=lambda a: -a["commissies_gehoord"])[:15]
        regels += ["", "## Breed gehoord (bij veel commissies: lage lift, weinig zeggend)", ""]
        regels += [f"- {a['organisatie']}: {a['organisatie_totaal']} keer bij {a['commissies_gehoord']} commissies"
                   for a in breed]
        geen = Counter()
        per_reden: dict[str, Counter] = defaultdict(Counter)
        for a in self.analyse:
            if not a["mechanisme"]:
                geen[a["groep"]] += a["keren"]
                per_reden[a["groep"]][a["organisatie"]] += a["keren"]
        regels += ["", "## Gehoord, maar zonder passend mechanisme (niet gepland)", ""]
        for reden, n in geen.most_common():
            regels.append(f"- {reden}: {n} keer — " + ", ".join(f"{o} ({k})" for o, k in per_reden[reden].most_common(8)))
        regels += ["", "## Deskundigen op eigen titel per organisatie (persoonsroute, niet gepland)", ""]
        regels += [f"- {self.org[o][0]}: {n}" for o, n in self.persoonlijk_per_org.most_common(15)]
        regels += ["", "## Voorstel schrijfwijzen voor koppelingen.json ('tk_namen'): zelfde woorden als een "
                       "modelnaam, andere volgorde", "",
                   "Met de hand nalopen en toevoegen; import en registercheck lezen dezelfde lijst.", ""]
        regels += [f'- "{w}": "{m}" ({n}×)' for (w, m), n in self.schrijfwijze_tips.most_common(25)]
        tips = sorted(self.tips.items(), key=lambda kv: -sum(kv[1].values()))
        regels += ["", "## Tips: indieners en tegenpartijen die (onder deze naam) niet in het model staan", "",
                   "Alleen namen die op een organisatie lijken; niets hiervan is ingediend.", ""]
        regels += [f"- {w} ({sum(c.values())}×: " + ", ".join(k.replace(' (Tweede Kamer)', '') for k, _ in c.most_common(2)) + ")"
                   for w, c in tips[:TOP] if sum(c.values()) >= 2]
        return "\n".join(regels) + "\n"


class Indiener:
    def __init__(self, plan: Plan, rest, log=print):
        self.p, self.rest, self.log = plan, rest, log
        self.ent: dict[tuple, int] = {}
        self.relaties: dict[tuple, int] = {}
        self.tel = Counter()
        self.bron_id: int | None = None

    def bron(self) -> int:
        if self.bron_id is None:
            status, res = self.rest("POST", "/api/sources", {
                "title": tki.TITEL.format(uitgave=self.p.uitgave), "source_type": "dataset",
                "publisher": tki.UITGEVER, "date_published": self.p.uitgave, "cluster_key": CLUSTER,
                "location": {"type": "url", "value": tki.URL},
                "reliability_voorgesteld": "primair", "onderwerp_voorgesteld": "nl_systeem"})
            if status not in (200, 201):
                raise SystemExit(f"bron registreren faalde: {status} {res}")
            self.bron_id = res["id"]
        return self.bron_id

    def entiteiten(self):
        for k, o in self.p.nieuwe_orgs.items():
            body = {"name": o["naam"], "type": o["type"], "primary_role_id": self.p.rol[o["rol"]],
                    "description": o["beschrijving"]}
            for veld in ("bestuurslaag", "active_from", "active_until"):
                if o.get(veld):
                    body[veld] = o[veld]
            status, res = self.rest("POST", "/api/entities", body)
            if status == 201:
                self.ent[("nieuw", k)] = res["id"]
                self.tel["commissie nieuw"] += 1
            else:
                self.tel[f"commissie fout {status}"] += 1
                self.log(f"  ✗ {o['naam']}: {status} {res.get('error')}")

    def _id(self, ref):
        return ref[1] if ref[0] == "bestaand" else self.ent.get(ref)

    def indienen(self):
        self.entiteiten()
        for r in self.p.relaties:
            s, t = self._id(r["bron"]), self._id(r["doel"])
            if not s or not t:
                self.tel["relatie zonder eindpunt"] += 1
                continue
            body = {"source_id": s, "target_id": t, "relation_type": r["type"],
                    "mechanism_id": self.p.mech[r["mechanisme"]]}
            if r["start"]:
                body["active_from"] = r["start"]
            status, res = self.rest("POST", "/api/relations", body)
            if status != 201:
                self.tel[f"relatie fout {status}"] += 1
                self.log(f"  ✗ relatie {s}→{t}: {status} {res.get('error')}")
                continue
            self.relaties[(s, t, r["type"])] = res["id"]
            self.tel["relatie nieuw"] += 1
        for a in self.p.argumenten:
            rec = a["rec"]
            s, t = a["org"], self._id(a["commissie"])
            rid = a["relatie"] or self.relaties.get((s, t, a["type"]))
            if not rid:
                self.tel["argument zonder verband"] += 1
                continue
            org = self.p.org[s][0]
            if rec["soort"] == "positionpaper":
                claim = (f"Volgens de open data van de Tweede Kamer (uitgave {self.p.uitgave}) stuurde {org} de "
                         f"{rec['commissie']} op {rec['datum']} een position paper: {rec['onderwerp']}.")
            elif rec["soort"] == "genodigde":
                claim = (f"Volgens de open data van de Tweede Kamer (uitgave {self.p.uitgave}) sprak {org} op "
                         f"{rec['datum']} als genodigde bij het {rec['activiteit_soort'].lower()} "
                         f"'{rec['onderwerp']}' van de {rec['commissie']}: {rec['wie']}.")
            else:
                claim = (f"Volgens de open data van de Tweede Kamer (uitgave {self.p.uitgave}) sprak de "
                         f"{rec['commissie']} op {rec['datum']} met {org} ({rec['activiteit_soort'].lower()}): "
                         f"{rec['onderwerp']}.")
            status, res = self.rest("POST", "/api/arguments", {
                "relation_id": rid, "claim": claim, "stance": "supporting",
                "citations": [{"source_id": self.bron(), "quote": rec["regel"], "methode": "officieel_register_scrape",
                               "section": rec["sleutel"], "page": f"{tki.BRON}/{self.p.uitgave}",
                               "context": tki.URL}]})
            self.tel["argument" if status == 201 else f"argument fout {status}"] += 1
            if status != 201:
                self.log(f"  ✗ argument {rec['sleutel']} op #{rid}: {status} {res.get('error')}")


def lobby_organisaties(conn, koppelingen: dict) -> set[int]:
    """Organisaties met een vaste toegangspas: wat al in het model staat (lobbyt → Tweede Kamer,
    lobbytoegang) plus wat lobby_naar_model.py uit de nieuwste uitgave zou koppelen."""
    ids = {s for (s,) in conn.execute("""
        SELECT r.source_id FROM relations r JOIN mechanisms m ON m.id = r.mechanism_id
        WHERE m.name = 'lobbytoegang' AND NOT r.vervangen AND r.status <> 'afgewezen'""")}
    try:
        import lobby
        import lobby_naar_model
        if lobby.uitgaven():
            lp = lobby_naar_model.Plan(lobby.lees(lobby.uitgaven()[-1]), conn, koppelingen).maak()
            ids |= {r["bron"][1] for r in lp.relaties if r["bron"][0] == "bestaand"}
    except Exception as e:  # noqa: BLE001 - het signaal is een extra, geen voorwaarde
        print(f"(lobbyistenregister niet gelezen: {e})", file=sys.stderr)
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--uitgave", help="JJJJ-MM-DD; standaard de nieuwste bewaarde uitgave")
    ap.add_argument("--haal", action="store_true", help="eerst een nieuwe uitgave ophalen")
    ap.add_argument("--indienen", action="store_true", help="echt indienen (standaard: droogloop)")
    a = ap.parse_args()
    if a.haal:
        print(tki.haal())
    if not tki.uitgaven():
        raise SystemExit("nog geen uitgave; eerst: python3 tools/registers/tk_inspraak.py haal")
    data = tki.lees_uitgave(a.uitgave or tki.uitgaven()[-1].stem.split("_")[-1])
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    koppelingen = json.loads(tkm.KOPPELINGEN.read_text(encoding="utf-8")) if tkm.KOPPELINGEN.exists() else {}
    agenda_pad = agenda.MAP / "analyse.json"
    agenda_rijen = json.loads(agenda_pad.read_text(encoding="utf-8")) if agenda_pad.exists() else []
    plan = Plan(data, conn, koppelingen, lobby_organisaties(conn, koppelingen), agenda_rijen).maak()
    (tki.MAP / "analyse.md").write_text(plan.rapport(), encoding="utf-8")
    (tki.MAP / "analyse.json").write_text(json.dumps(plan.analyse, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"uitgave": plan.uitgave, "lezer": data["telling"],
                      "nieuwe_commissies": [o["naam"] for o in plan.nieuwe_orgs.values()],
                      "relaties_nieuw": len(plan.relaties), "telling": dict(sorted(plan.tel.items()))},
                     ensure_ascii=False, indent=1))
    print(f"rapport: {tki.MAP / 'analyse.md'}")
    if not a.indienen:
        print("\n(droogloop — niets ingediend)")
        return
    from naar_model import TOKEN, Rest
    ind = Indiener(plan, Rest(TOKEN.read_text().strip()))
    ind.indienen()
    print(json.dumps(dict(sorted(ind.tel.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
