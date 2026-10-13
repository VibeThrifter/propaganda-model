#!/usr/bin/env python3
"""Partijnetwerk — wie is aan welke partij verbonden, en welke posities bekleden die mensen.

Beschrijvende overlay over het praktijkmodel (hetzelfde netwerk; geen eigen tabel, niets
opgeslagen). Per partij: de personen met een partijband (lid, bestuurder, adviseur,
medewerker, woordvoerder, draaideur) en hun posities — een ambt in het openbaar bestuur
(Kabinet, Kamers, Europees Parlement, provincie, gemeente, topambt) of een functie bij een
organisatie daarbuiten (bedrijf, media, lobby, denktank, ngo, onderwijs, elite-netwerk).
Daarnaast: welke organisaties mensen uit meerdere partijen delen.

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


def _afgelopen(r, peiljaar):
    """Zelfde regel als de viz (isAfgelopen): inactief, of het eindjaar ligt vóór dit jaar."""
    if r.get("active") in (0, False):
        return True
    u = _jaar(r.get("active_until"))
    return u is not None and u < peiljaar


def _overlapt(a, b):
    """Overlappen twee looptijden (op jaarbasis)? Een open grens overlapt altijd —
    de meeste partijbanden zijn ongedateerd en tellen dus gewoon mee."""
    af, au = _jaar(a.get("active_from")), _jaar(a.get("active_until"))
    bf, bu = _jaar(b.get("active_from")), _jaar(b.get("active_until"))
    return (au is None or bf is None or bf <= au) and (bu is None or af is None or bu >= af)


def _looptijd(r):
    f, u = _jaar(r.get("active_from")), _jaar(r.get("active_until"))
    if f and u:
        return f"{f}–{u}"
    if f:
        return f"sinds {f}"
    if u:
        return f"tot {u}"
    return ""


def _laad(conn):
    """Alle goedgekeurde entiteiten + relaties (het model is klein: enkele duizenden rijen)."""
    def rijen(sql):
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    ents = {e["id"]: e for e in rijen(
        "SELECT id, name, type, bestuurslaag, description FROM entities "
        "WHERE status = 'goedgekeurd' AND NOT vervangen")}
    rels = [r for r in rijen(
        "SELECT r.id, r.source_id, r.target_id, r.relation_type, r.functie, "
        "       r.active_from, r.active_until, r.active, m.name AS mechanism_name "
        "FROM relations r LEFT JOIN mechanisms m ON m.id = r.mechanism_id "
        "WHERE r.status = 'goedgekeurd' AND NOT r.vervangen")
        if r["source_id"] in ents and r["target_id"] in ents]
    return ents, rels


def _ander(r, eid):
    return r["target_id"] if r["source_id"] == eid else r["source_id"]


def _bouw(conn, peiljaar=None):
    """Kern: per partij de personen met hun banden en posities.

    Geeft (ents, partijen, rels) met partijen = {partij_id: {persoon_id: {...}}}; per
    persoon 'banden' (met de partij) en 'posities' (elk met klasse, afgelopen en of hij
    in de tijd met een band overlapt — een positie van vóór of ná het lidmaatschap
    telt niet mee voor die partij, maar blijft zichtbaar)."""
    peiljaar = peiljaar or datetime.date.today().year
    ents, rels = _laad(conn)
    is_partij = lambda i: ents[i]["type"] == "partij"      # noqa: E731
    is_persoon = lambda i: ents[i]["type"] == "persoon"    # noqa: E731

    partijen = {i: {} for i, e in ents.items() if e["type"] == "partij"}
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
        slot = partijen[p].setdefault(pers, {"banden": [], "posities": []})
        slot["banden"].append(r)

    leden = {pers for pp in partijen.values() for pers in pp}
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
                "afgelopen": _afgelopen(r, peiljaar),
            })

    for pp in partijen.values():
        for pers, slot in pp.items():
            slot["band_afgelopen"] = all(_afgelopen(b, peiljaar) for b in slot["banden"])
            actieve_banden = [b for b in slot["banden"] if not _afgelopen(b, peiljaar)]
            for pos in posities.get(pers, []):
                binnen = any(_overlapt(b, pos["rel"]) for b in slot["banden"])
                slot["posities"].append(dict(
                    pos, binnen_band=binnen,
                    # 'nu': de band met de partij én de positie lopen allebei nog.
                    nu=bool(binnen and actieve_banden and not pos["afgelopen"]),
                ))
    return ents, partijen, rels, peiljaar


def _klassen_lijst():
    return [{"key": k, "label": lab, "groep": g, "groep_label": GROEPEN[g]}
            for k, lab, g in KLASSEN]


def _hoofdklasse(posities):
    tellend = [p for p in posities if p["binnen_band"]]
    for pool in ([p for p in tellend if p["nu"]], tellend):
        if pool:
            return min(pool, key=lambda p: RANG[p["klasse"]])["klasse"]
    return None


def compute_overzicht(conn, peiljaar=None) -> dict:
    """Alle partijen: tellingen per positieklasse (personen, 'alle' en 'nu') + de
    organisaties waar mensen uit twee of meer partijen een positie hebben."""
    ents, partijen, _, peiljaar = _bouw(conn, peiljaar)
    uit = []
    gedeeld = {}   # org_id -> {partij_id: {"alle": set, "nu": set}}
    for pid, pp in partijen.items():
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
        uit.append({"id": pid, "naam": ents[pid]["name"],
                    "n_personen": [len(pp), n_nu], "telling": telling})
    uit.sort(key=lambda p: (-p["n_personen"][0], p["naam"].lower()))

    orgs = []
    for oid, per_partij in gedeeld.items():
        if len(per_partij) < 2:
            continue
        o = ents[oid]
        orgs.append({
            "id": oid, "naam": o["name"], "type": o["type"], "laag": o.get("bestuurslaag"),
            "overheid": o["type"] in OVERHEID_TYPES,
            "partijen": {str(pid): {"alle": len(v["alle"]), "nu": len(v["nu"])}
                         for pid, v in per_partij.items()},
        })
    orgs.sort(key=lambda o: (-len(o["partijen"]),
                             -sum(v["alle"] for v in o["partijen"].values()),
                             o["naam"].lower()))
    return {"peiljaar": peiljaar, "klassen": _klassen_lijst(), "partijen": uit,
            "gedeelde_organisaties": orgs}


def _rel_uit(r, eid, ents, peiljaar):
    """Eén relatie vanuit het perspectief van entiteit eid (voor 'overige banden')."""
    ander = ents[_ander(r, eid)]
    return {
        "relation_id": r["id"], "type": r["relation_type"],
        "richting": "uit" if r["source_id"] == eid else "in",
        "ander": {"id": ander["id"], "naam": ander["name"], "type": ander["type"]},
        "mechanisme": r.get("mechanism_name"), "functie": r.get("functie"),
        "looptijd": _looptijd(r), "afgelopen": _afgelopen(r, peiljaar),
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


def compute_partij(conn, partij_id: int, peiljaar=None):
    """Eén partij in detail: per persoon de band(en), posities en overige relaties, plus
    de banden van de partij zelf met organisaties. None als het geen (goedgekeurde) partij is."""
    ents, partijen, rels, peiljaar = _bouw(conn, peiljaar)
    if partij_id not in partijen:
        return None
    pp = partijen[partij_id]

    # Overige relaties per persoon: alles wat geen band met een partij en geen positie is.
    overig = {}
    for r in rels:
        for pers in (r["source_id"], r["target_id"]):
            if pers not in pp:
                continue
            ander = ents[_ander(r, pers)]
            if r["relation_type"] in POSITIE_TYPES and ander["type"] != "persoon":
                continue   # band met een partij of positie: staat al elders
            overig.setdefault(pers, []).append(_rel_uit(r, pers, ents, peiljaar))

    andere_partijen = {}
    for pid, leden in partijen.items():
        if pid == partij_id:
            continue
        for pers, slot in leden.items():
            if pers in pp:
                andere_partijen.setdefault(pers, []).append({
                    "id": pid, "naam": ents[pid]["name"], "afgelopen": slot["band_afgelopen"]})

    personen = []
    telling = {}
    for pers, slot in pp.items():
        # Tellen op alle posities (zelfde getallen als het overzicht); tonen ontdubbeld.
        alle_k = {p["klasse"] for p in slot["posities"] if p["binnen_band"]}
        nu_k = {p["klasse"] for p in slot["posities"] if p["nu"]}
        posities = sorted(_ontdubbel(slot["posities"]), key=lambda p: (
            not p["binnen_band"], p["afgelopen"], RANG[p["klasse"]], p["org"]["name"].lower()))
        for k in alle_k:
            telling.setdefault(k, [0, 0])[0] += 1
        for k in nu_k:
            telling[k][1] += 1
        personen.append({
            "id": pers, "naam": ents[pers]["name"],
            "band": [{"relation_id": b["id"], "type": b["relation_type"],
                      "label": BAND_LABELS[b["relation_type"]], "looptijd": _looptijd(b),
                      "afgelopen": _afgelopen(b, peiljaar)} for b in slot["banden"]],
            "band_afgelopen": slot["band_afgelopen"],
            "hoofdklasse": _hoofdklasse(slot["posities"]),
            "posities": [{
                "relation_id": p["rel"]["id"], "klasse": p["klasse"],
                "label": _label(p),
                "type": p["rel"]["relation_type"],
                "org": {"id": p["org"]["id"], "naam": p["org"]["name"],
                        "type": p["org"]["type"], "laag": p["org"].get("bestuurslaag")},
                "looptijd": _looptijd(p["rel"]), "afgelopen": p["afgelopen"],
                "binnen_band": p["binnen_band"], "nu": p["nu"],
            } for p in posities],
            "overig": sorted(overig.get(pers, []), key=lambda o: (o["afgelopen"], o["type"])),
            "andere_partijen": andere_partijen.get(pers, []),
        })
    personen.sort(key=lambda p: (
        p["band_afgelopen"],
        RANG.get(p["hoofdklasse"], len(RANG)),
        p["naam"].lower()))

    organisaties = []
    for r in rels:
        if partij_id not in (r["source_id"], r["target_id"]):
            continue
        ander = ents[_ander(r, partij_id)]
        if ander["id"] in pp and r["relation_type"] in PARTIJBAND_TYPES:
            continue   # persoonsband: staat onder 'personen'
        organisaties.append(_rel_uit(r, partij_id, ents, peiljaar))
    organisaties.sort(key=lambda o: (o["afgelopen"], o["type"], o["ander"]["naam"].lower()))

    e = ents[partij_id]
    return {
        "peiljaar": peiljaar, "klassen": _klassen_lijst(),
        "partij": {"id": partij_id, "naam": e["name"], "beschrijving": e.get("description")},
        "n_personen": [len(pp), sum(1 for s in pp.values() if not s["band_afgelopen"])],
        "telling": telling, "personen": personen, "organisaties": organisaties,
    }
