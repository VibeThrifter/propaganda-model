#!/usr/bin/env python3
"""Partijnetwerk — wie is aan welke partij verbonden, en welke posities bekleden die mensen.

Beschrijvende overlay over het praktijkmodel (hetzelfde netwerk; geen eigen tabel, niets
opgeslagen). Per partij: de personen met een partijband (lid, bestuurder, adviseur,
medewerker, woordvoerder, draaideur) en hun posities — een ambt in het openbaar bestuur
(Kabinet, Kamers, Europees Parlement, provincie, gemeente, topambt) of een functie bij een
organisatie daarbuiten (bedrijf, media, lobby, denktank, ngo, onderwijs, elite-netwerk).
Daarnaast: welke organisaties mensen uit meerdere partijen delen.

Tijd (looptijd.py, 2026-10-13): een band loopt nooit buiten het bestaan van partij of
organisatie, dus een ongedateerd PvdA-lidmaatschap eindigt op 1 juli 2026. 'Lopend' wordt
op de dag bepaald, niet op het jaar.

Fusies: een partij die opging in een andere (aspect 'opgegaan_in') blijft haar eigen banden
houden. Met fusies=True (standaard) telt de opvolger ze mee als zijn stamboom: PRO toont ook
de mensen van PvdA en GroenLinks, elk met de partij en de periode van hun band. 'Nu' telt
alleen wat vandaag loopt. Een band met een opgeheven partij loopt niet meer, en een lid gaat
alleen over als een bron dat voor die persoon zegt.

Leest alléén goedgekeurde, niet-vervangen relaties tussen goedgekeurde entiteiten. Telt in
NIETS mee (scoring/influence/viz_data lezen dit niet) en beweert niets over invloed of
afstemming: het zegt wie welke positie bekleedt volgens de gesourcete verbanden. Dat is de
beschrijvende kant van de kartelpartij-these (Katz & Mair 1995) — of het patroon die these
draagt, blijft een vraag voor de discussieboom, niet voor deze telling.

Gebruikt door GET /api/partijen (overzicht), GET /api/partijen/<id> (één partij), de
pagina /partijen en de partij-sectie in het viz-detailpaneel.
"""
from __future__ import annotations

import datetime

import looptijd

# Band persoon ↔ partij (beide richtingen; het register schrijft partij → persoon).
PARTIJBAND_TYPES = ("lidmaatschap", "bestuurder", "adviseur", "personeel",
                    "dienstverband", "woordvoerder_van", "draaideur")
# Een positie: dezelfde affiliatietypen plus 'ambt', tussen een partijpersoon en een
# organisatie die zelf geen partij is.
POSITIE_TYPES = PARTIJBAND_TYPES + ("ambt",)

BAND_LABELS = {
    "lidmaatschap": "lid", "bestuurder": "bestuurder", "adviseur": "adviseur",
    "personeel": "medewerker", "dienstverband": "in dienst",
    "woordvoerder_van": "woordvoerder", "draaideur": "draaideur",
}
# Positie zonder `functie`: het relatietype als kort label, of — voor de klassen waar
# de titel vastligt — de gangbare titel.
POSITIE_LABELS = dict(BAND_LABELS, lidmaatschap="lid", personeel="werkzaam bij", ambt="ambt")
KLASSE_TITELS = {"kabinet": "bewindspersoon", "tweede_kamer": "Kamerlid",
                 "eerste_kamer": "Kamerlid", "europarlement": "Europarlementariër"}

# (sleutel, label, groep) — de volgorde is ook de rangorde voor de 'hoofdpositie' van
# een persoon (de eerste klasse waarin hij een positie heeft).
KLASSEN = [
    ("kabinet", "Kabinet", "bestuur"),
    ("tweede_kamer", "Tweede Kamer", "bestuur"),
    ("eerste_kamer", "Eerste Kamer", "bestuur"),
    ("europarlement", "Europees Parlement", "bestuur"),
    ("provincie", "Provincie", "bestuur"),
    ("burgemeester", "Burgemeester", "bestuur"),
    ("wethouder", "Wethouder", "bestuur"),
    ("gemeente", "Gemeente (overig)", "bestuur"),
    ("waterschap", "Waterschap", "bestuur"),
    ("topambt", "Topambt, rechtspraak & toezicht", "overheid"),
    ("overheid", "Overige overheid", "overheid"),
    ("bedrijfsleven", "Bedrijfsleven", "buiten"),
    ("media", "Media & omroep", "buiten"),
    ("belangen", "Lobby, vakbond & pr", "buiten"),
    ("denktank", "Denktanks", "buiten"),
    ("maatschappelijk", "Ngo's & stichtingen", "buiten"),
    ("onderwijs", "Onderwijs & wetenschap", "buiten"),
    ("elite_netwerk", "Elite-netwerken", "buiten"),
]
GROEPEN = {"bestuur": "Politiek & bestuur", "overheid": "Overheid",
           "buiten": "Buiten de overheid"}
RANG = {k: i for i, (k, _, _) in enumerate(KLASSEN)}

OVERHEID_TYPES = ("overheidsinstelling", "toezichthouder", "rechterlijke_macht")
SECTOR_KLASSE = {
    "bedrijf": "bedrijfsleven", "vermogensbeheerder": "bedrijfsleven",
    "mediaorganisatie": "media", "omroep": "media", "persbureau": "media", "platform": "media",
    "lobbygroep": "belangen", "vakbond": "belangen", "pr_bureau": "belangen",
    "denktank": "denktank",
    "ngo": "maatschappelijk", "stichting": "maatschappelijk", "burgerinitiatief": "maatschappelijk",
    "onderwijsinstelling": "onderwijs",
    "elite_netwerk": "elite_netwerk",
}


def klasse(rel_type: str, functie: str | None, org: dict) -> str:
    """Positieklasse van één band persoon → organisatie. Leunt op relatietype, de
    ambtstitel (`functie`, zoals het register hem geeft) en de organisatie (naam/laag/
    type). Zonder titel geldt: een ambt of bestuurder bij een ministerie is een
    bewindspersoon, een lid van een Kamer een Kamerlid (oudere seed-relaties)."""
    f = (functie or "").strip().lower()
    naam = org.get("name") or ""
    laag = org.get("bestuurslaag")
    otype = org.get("type")
    if otype in OVERHEID_TYPES:
        if f.startswith(("minister", "staatssecretaris")) or (
                not f and rel_type in ("ambt", "bestuurder") and naam.startswith("Ministerie")):
            return "kabinet"
        if rel_type in ("ambt", "lidmaatschap"):
            if naam == "Tweede Kamer":
                return "tweede_kamer"
            if naam == "Eerste Kamer":
                return "eerste_kamer"
            if naam == "Europees Parlement" or f.startswith("europarlementari"):
                return "europarlement"
        if laag == "provincie":
            return "provincie"
        if laag == "gemeente":
            if f.startswith("burgemeester"):
                return "burgemeester"
            if f.startswith("wethouder"):
                return "wethouder"
            return "gemeente"
        if laag == "waterschap":
            return "waterschap"
        if rel_type == "ambt" or otype != "overheidsinstelling":
            return "topambt"
        return "overheid"
    return SECTOR_KLASSE.get(otype, "maatschappelijk")


def _jaar(v):
    try:
        return int(str(v)[:4]) if v else None
    except ValueError:
        return None


def _peil(peiljaar):
    """Peildatum: vandaag (op de dag), of een opgegeven jaar (op jaarbasis)."""
    return str(peiljaar) if peiljaar else datetime.date.today().isoformat()


class _Tijd:
    """De looptijd van verbanden binnen het bestaan van hun eindpunten (looptijd.py)."""

    def __init__(self, ents, peil):
        self.ents, self.peil = ents, peil

    def eindpunten(self, r):
        return self.ents.get(r["source_id"]), self.ents.get(r["target_id"])

    def effectief(self, r):
        return looptijd.effectief(r, *self.eindpunten(r))

    def afgelopen(self, r):
        return looptijd.afgelopen(r, *self.eindpunten(r), peil=self.peil)

    def overlapt(self, a, b):
        av, at, _ = self.effectief(a)
        bv, bt, _ = self.effectief(b)
        return looptijd.overlapt(av, at, bv, bt)

    def label(self, r):
        """'1990–2026', 'sinds 2019', 'tot 2026': het eigen begin, het effectieve einde (een
        opgeheven partij of organisatie kapt een open band af)."""
        f = _jaar(r.get("active_from"))
        u = _jaar(self.effectief(r)[1])
        if f and u:
            return f"{f}–{u}"
        if f:
            return f"sinds {f}"
        if u:
            return f"tot {u}"
        return ""

    def einde_door(self, r):
        door = self.effectief(r)[2]
        if door is None:
            return None
        e = self.ents[door]
        return {"id": door, "naam": e["name"], "einde": e.get("active_until")}


def _laad(conn):
    """Alle goedgekeurde entiteiten + relaties (het model is klein: enkele duizenden rijen)."""
    def rijen(sql):
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    ents = {e["id"]: e for e in rijen(
        "SELECT id, name, type, bestuurslaag, description, active_from, active_until "
        "FROM entities WHERE status = 'goedgekeurd' AND NOT vervangen")}
    rels = [r for r in rijen(
        "SELECT r.id, r.source_id, r.target_id, r.relation_type, r.functie, "
        "       r.active_from, r.active_until, r.active, m.name AS mechanism_name "
        "FROM relations r LEFT JOIN mechanisms m ON m.id = r.mechanism_id "
        "WHERE r.status = 'goedgekeurd' AND NOT r.vervangen")
        if r["source_id"] in ents and r["target_id"] in ents]
    return ents, rels


def _ander(r, eid):
    return r["target_id"] if r["source_id"] == eid else r["source_id"]


def _stamboom(conn, ents):
    """Fusies tussen partijen: (hoofd, voorgangers, opvolgers) — zie looptijd.stamboom."""
    opv = {}
    for vg, lijst in looptijd.opvolgingen(conn).items():
        if ents.get(vg, {}).get("type") != "partij":
            continue
        lijst = [x for x in lijst if ents.get(x["opvolger"], {}).get("type") == "partij"]
        if lijst:
            opv[vg] = lijst
    hoofd, voorgangers = looptijd.stamboom(opv)
    return hoofd, voorgangers, {k: [x["opvolger"] for x in v] for k, v in opv.items()}


def _bouw(conn, peiljaar=None):
    """Kern: per partij (zonder samenvoegen) de banden per persoon, en per partijpersoon zijn
    posities. Samenvoegen langs fusies en de tijdtoets per groep doet _groep."""
    ents, rels = _laad(conn)
    tijd = _Tijd(ents, _peil(peiljaar))
    is_partij = lambda i: ents[i]["type"] == "partij"      # noqa: E731
    is_persoon = lambda i: ents[i]["type"] == "persoon"    # noqa: E731

    per_partij = {i: {} for i, e in ents.items() if e["type"] == "partij"}
    for r in rels:
        if r["relation_type"] not in PARTIJBAND_TYPES:
            continue
        s, t = r["source_id"], r["target_id"]
        if is_partij(s) and is_persoon(t):
            p, pers = s, t
        elif is_persoon(s) and is_partij(t):
            p, pers = t, s
        else:
            continue
        per_partij[p].setdefault(pers, []).append(dict(r, partij_id=p))

    leden = {pers for pp in per_partij.values() for pers in pp}
    posities = {}   # persoon_id -> [positie-dict]
    for r in rels:
        if r["relation_type"] not in POSITIE_TYPES:
            continue
        for pers in (r["source_id"], r["target_id"]):
            if pers not in leden:
                continue
            org = ents[_ander(r, pers)]
            if org["type"] in ("persoon", "partij"):
                continue
            posities.setdefault(pers, []).append({
                "rel": r, "org": org,
                "klasse": klasse(r["relation_type"], r.get("functie"), org),
                "afgelopen": tijd.afgelopen(r),
            })
    return ents, per_partij, posities, rels, tijd


def _groep(partij_ids, per_partij, posities, tijd):
    """De personen van een groep partijen (een partij plus haar voorgangers) met hun banden en
    posities. Een positie telt voor de groep als ze in de tijd met een band overlapt: een
    positie van vóór of ná de band blijft zichtbaar maar telt niet. 'Nu' betekent dat een band
    met de groep én de positie vandaag lopen."""
    slots = {}
    for p in partij_ids:
        for pers, banden in per_partij.get(p, {}).items():
            slots.setdefault(pers, {"banden": [], "posities": []})["banden"] += banden
    for pers, slot in slots.items():
        slot["band_afgelopen"] = all(tijd.afgelopen(b) for b in slot["banden"])
        actieve_banden = [b for b in slot["banden"] if not tijd.afgelopen(b)]
        for pos in posities.get(pers, []):
            binnen = any(tijd.overlapt(b, pos["rel"]) for b in slot["banden"])
            slot["posities"].append(dict(
                pos, binnen_band=binnen,
                nu=bool(binnen and actieve_banden and not pos["afgelopen"]),
            ))
    return slots


def _klassen_lijst():
    return [{"key": k, "label": lab, "groep": g, "groep_label": GROEPEN[g]}
            for k, lab, g in KLASSEN]


def _hoofdklasse(posities):
    tellend = [p for p in posities if p["binnen_band"]]
    for pool in ([p for p in tellend if p["nu"]], tellend):
        if pool:
            return min(pool, key=lambda p: RANG[p["klasse"]])["klasse"]
    return None


def _bestaan_label(e):
    f, u = _jaar(e.get("active_from")), _jaar(e.get("active_until"))
    if f and u:
        return f"{f}–{u}"
    if f:
        return f"sinds {f}"
    return f"tot {u}" if u else ""


def _partij_kort(ents, pid):
    e = ents[pid]
    return {"id": pid, "naam": e["name"], "looptijd": _bestaan_label(e)}


def _groep_ids(pid, voorgangers, fusies):
    return {pid} | (set(voorgangers.get(pid, ())) if fusies else set())


def compute_overzicht(conn, peiljaar=None, fusies=True) -> dict:
    """Alle partijen: tellingen per positieklasse (personen, 'alle' en 'nu') + de
    organisaties waar mensen uit twee of meer partijen een positie hebben. Met fusies=True is
    een opgeheven partij een deel van de kolom van haar opvolger (stamboom)."""
    ents, per_partij, posities, _, tijd = _bouw(conn, peiljaar)
    hoofd, voorgangers, opvolgers = _stamboom(conn, ents)
    kolommen = [p for p in per_partij if not (fusies and p in hoofd)]
    uit = []
    gedeeld = {}   # org_id -> {kolom_id: {"alle": set, "nu": set}}
    for pid in kolommen:
        groep = _groep_ids(pid, voorgangers, fusies)
        pp = _groep(groep, per_partij, posities, tijd)
        if not pp:
            continue
        telling = {}
        n_nu = 0
        for pers, slot in pp.items():
            if not slot["band_afgelopen"]:
                n_nu += 1
            alle_k, nu_k = set(), set()
            for pos in slot["posities"]:
                if not pos["binnen_band"]:
                    continue
                alle_k.add(pos["klasse"])
                if pos["nu"]:
                    nu_k.add(pos["klasse"])
                g = gedeeld.setdefault(pos["org"]["id"], {}).setdefault(
                    pid, {"alle": set(), "nu": set()})
                g["alle"].add(pers)
                if pos["nu"]:
                    g["nu"].add(pers)
            for k in alle_k:
                telling.setdefault(k, [0, 0])[0] += 1
            for k in nu_k:
                telling[k][1] += 1
        kol = {"id": pid, "naam": ents[pid]["name"], "looptijd": _bestaan_label(ents[pid]),
               "n_personen": [len(pp), n_nu], "telling": telling}
        if fusies and voorgangers.get(pid):
            kol["voorgangers"] = sorted((_partij_kort(ents, v) for v in voorgangers[pid]),
                                        key=lambda v: (v["looptijd"], v["naam"]))
        if opvolgers.get(pid):
            kol["opgegaan_in"] = [_partij_kort(ents, o) for o in opvolgers[pid]]
        uit.append(kol)
    uit.sort(key=lambda p: (-p["n_personen"][0], p["naam"].lower()))

    orgs = []
    for oid, per_kolom in gedeeld.items():
        if len(per_kolom) < 2:
            continue
        o = ents[oid]
        orgs.append({
            "id": oid, "naam": o["name"], "type": o["type"], "laag": o.get("bestuurslaag"),
            "overheid": o["type"] in OVERHEID_TYPES,
            "partijen": {str(pid): {"alle": len(v["alle"]), "nu": len(v["nu"])}
                         for pid, v in per_kolom.items()},
        })
    orgs.sort(key=lambda o: (-len(o["partijen"]),
                             -sum(v["alle"] for v in o["partijen"].values()),
                             o["naam"].lower()))
    return {"peiljaar": int(_peil(peiljaar)[:4]), "peildatum": _peil(peiljaar),
            "fusies": bool(fusies), "klassen": _klassen_lijst(), "partijen": uit,
            "gedeelde_organisaties": orgs}


def _rel_uit(r, eid, ents, tijd):
    """Eén relatie vanuit het perspectief van entiteit eid (voor 'overige banden')."""
    ander = ents[_ander(r, eid)]
    return {
        "relation_id": r["id"], "type": r["relation_type"],
        "richting": "uit" if r["source_id"] == eid else "in",
        "ander": {"id": ander["id"], "naam": ander["name"], "type": ander["type"]},
        "mechanisme": r.get("mechanism_name"), "functie": r.get("functie"),
        "looptijd": tijd.label(r), "afgelopen": tijd.afgelopen(r),
    }


def _ontdubbel(posities):
    """Oudere seed-relaties ('bestuurder' van een ministerie, 'lid' van de Tweede Kamer)
    staan vaak naast het registerambt bij dezelfde organisatie ('Minister van …',
    'Kamerlid'). Heeft een organisatie in dezelfde klasse een positie mét ambtstitel, dan
    valt de kale variant weg uit de weergave (de tellingen zijn per persoon en klasse en
    veranderen daardoor niet)."""
    met_titel = {(p["org"]["id"], p["klasse"]) for p in posities if p["rel"].get("functie")}
    return [p for p in posities
            if p["rel"].get("functie") or (p["org"]["id"], p["klasse"]) not in met_titel]


def _label(pos):
    r = pos["rel"]
    if r.get("functie"):
        return r["functie"]
    if r["relation_type"] in ("ambt", "lidmaatschap", "bestuurder") and pos["klasse"] in KLASSE_TITELS:
        return KLASSE_TITELS[pos["klasse"]]
    return POSITIE_LABELS[r["relation_type"]]


def compute_partij(conn, partij_id: int, peiljaar=None, fusies=True):
    """Eén partij in detail: per persoon de band(en), posities en overige relaties, plus
    de banden van de partij zelf met organisaties. Met fusies=True horen de partijen die erin
    opgingen erbij (elke band noemt zijn partij). None als het geen (goedgekeurde) partij is."""
    ents, per_partij, posities, rels, tijd = _bouw(conn, peiljaar)
    if partij_id not in per_partij:
        return None
    hoofd, voorgangers, opvolgers = _stamboom(conn, ents)
    groep = _groep_ids(partij_id, voorgangers, fusies)
    pp = _groep(groep, per_partij, posities, tijd)

    # Overige relaties per persoon: alles wat geen band met een partij en geen positie is.
    overig = {}
    for r in rels:
        for pers in (r["source_id"], r["target_id"]):
            if pers not in pp:
                continue
            ander = ents[_ander(r, pers)]
            if r["relation_type"] in POSITIE_TYPES and ander["type"] != "persoon":
                continue   # band met een partij of positie: staat al elders
            overig.setdefault(pers, []).append(_rel_uit(r, pers, ents, tijd))

    andere_partijen = {}
    for pid, leden in per_partij.items():
        if pid in groep:
            continue
        for pers, banden in leden.items():
            if pers in pp:
                andere_partijen.setdefault(pers, []).append({
                    "id": pid, "naam": ents[pid]["name"],
                    "afgelopen": all(tijd.afgelopen(b) for b in banden)})

    personen = []
    telling = {}
    for pers, slot in pp.items():
        # Tellen op alle posities (zelfde getallen als het overzicht); tonen ontdubbeld.
        alle_k = {p["klasse"] for p in slot["posities"] if p["binnen_band"]}
        nu_k = {p["klasse"] for p in slot["posities"] if p["nu"]}
        posities_p = sorted(_ontdubbel(slot["posities"]), key=lambda p: (
            not p["binnen_band"], p["afgelopen"], RANG[p["klasse"]], p["org"]["name"].lower()))
        for k in alle_k:
            telling.setdefault(k, [0, 0])[0] += 1
        for k in nu_k:
            telling[k][1] += 1
        banden = sorted(slot["banden"], key=lambda b: (tijd.afgelopen(b), -(_jaar(b.get("active_from")) or 0)))
        personen.append({
            "id": pers, "naam": ents[pers]["name"],
            "band": [{"relation_id": b["id"], "type": b["relation_type"],
                      "label": BAND_LABELS[b["relation_type"]], "looptijd": tijd.label(b),
                      "afgelopen": tijd.afgelopen(b), "einde_door": tijd.einde_door(b),
                      "partij": {"id": b["partij_id"], "naam": ents[b["partij_id"]]["name"]}}
                     for b in banden],
            "band_afgelopen": slot["band_afgelopen"],
            "hoofdklasse": _hoofdklasse(slot["posities"]),
            "posities": [{
                "relation_id": p["rel"]["id"], "klasse": p["klasse"],
                "label": _label(p),
                "type": p["rel"]["relation_type"],
                "org": {"id": p["org"]["id"], "naam": p["org"]["name"],
                        "type": p["org"]["type"], "laag": p["org"].get("bestuurslaag")},
                "looptijd": tijd.label(p["rel"]), "afgelopen": p["afgelopen"],
                "binnen_band": p["binnen_band"], "nu": p["nu"],
            } for p in posities_p],
            "overig": sorted(overig.get(pers, []), key=lambda o: (o["afgelopen"], o["type"])),
            "andere_partijen": andere_partijen.get(pers, []),
        })
    personen.sort(key=lambda p: (
        p["band_afgelopen"],
        RANG.get(p["hoofdklasse"], len(RANG)),
        p["naam"].lower()))

    organisaties = []
    for r in rels:
        via = next((p for p in groep if p in (r["source_id"], r["target_id"])), None)
        if via is None:
            continue
        ander = ents[_ander(r, via)]
        if ander["id"] in groep:
            continue   # band tussen partijen van dezelfde stamboom
        if ander["id"] in pp and r["relation_type"] in PARTIJBAND_TYPES:
            continue   # persoonsband: staat onder 'personen'
        o = _rel_uit(r, via, ents, tijd)
        if via != partij_id:
            o["via"] = {"id": via, "naam": ents[via]["name"]}
        organisaties.append(o)
    organisaties.sort(key=lambda o: (o["afgelopen"], o["type"], o["ander"]["naam"].lower()))

    e = ents[partij_id]
    uit = {
        "peiljaar": int(_peil(peiljaar)[:4]), "peildatum": _peil(peiljaar), "fusies": bool(fusies),
        "klassen": _klassen_lijst(),
        "partij": {"id": partij_id, "naam": e["name"], "beschrijving": e.get("description"),
                   "looptijd": _bestaan_label(e)},
        "n_personen": [len(pp), sum(1 for s in pp.values() if not s["band_afgelopen"])],
        "telling": telling, "personen": personen, "organisaties": organisaties,
    }
    if fusies and voorgangers.get(partij_id):
        uit["partij"]["voorgangers"] = sorted(
            (_partij_kort(ents, v) for v in voorgangers[partij_id]),
            key=lambda v: (v["looptijd"], v["naam"]))
    if opvolgers.get(partij_id):
        uit["partij"]["opgegaan_in"] = [_partij_kort(ents, o) for o in opvolgers[partij_id]]
    return uit
