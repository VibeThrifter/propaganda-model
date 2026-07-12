"""voorstellen.py — theory-RfC's en granulariteitsbeheer (verbeterplan M2.3/M2.6).

Een nieuw theorie-element, splitsing, samenvoeging of hernoeming ontstaat alleen nog
via een voorstel (tabel ``voorstellen``). Deze module bevat de drie bouwstenen die
``server.py`` en de tests delen:

  valideer_payload()    sjablooncontrole bij indienen (RfC-velden, hertriage-plan)
  benodigde_akkoorden() reviewdrempel: theorielaag = 2 menselijke reviewers
                        (indiener telt niet mee; agent-oordelen zijn advies en
                        tellen nooit — alle LLM's zijn één familie, §6.4);
                        praktijklaag = 1 (zelf-akkoord toegestaan, gevlagd)
  voer_uit()            uitvoering ná acceptatie, binnen de transactie van de
                        aanroeper; raise ValueError = voorstel blijft open

Kernregels M2.6 (zie VERBETERPLAN § M2.6):
  1. Niets wissen — het oude element krijgt ``vervangen = TRUE`` plus
     lineage-rijen naar zijn opvolger(s); oude id's blijven herleidbaar.
  2. Bewijs verhuist nooit automatisch — bij samenvoegen verhuist alleen wat
     expliciet is herbevestigd (de rest blijft bij het vervangen element en telt
     nergens meer in mee); bij splitsen moet de hertriage-restlijst LEEG zijn:
     elk argument, elke relatie, instantiatie en padclaim is aan één of meer
     opvolgers toegewezen (één-op-veel = dupliceren, nooit automatisch).

Alleen stdlib.
"""
from __future__ import annotations
import json

SOORTEN = ("nieuw_theorie_element", "splitsen", "samenvoegen", "hernoemen",
           "herformuleren")

TABEL = {
    "rol": "roles",
    "mechanisme": "mechanisms",
    "entiteit": "entities",
    "relatie": "relations",
    "emergent_effect": "emergent_effects",
}
THEORIE_TYPES = ("rol", "mechanisme", "emergent_effect")
# Bewerkbare tekstvelden per element_type (voor 'herformuleren'). De naam loopt
# via 'hernoemen'; hier gaat het om de omschrijvende velden.
TEKSTVELDEN = {
    "rol": ("description", "examples"),
    "mechanisme": ("description", "effect"),
    "entiteit": ("description",),
    "relatie": ("description",),
    "emergent_effect": ("description", "effect", "label"),
}
# element_type → argumentkolom (voor hertriage van de discussieboom)
ARG_KOLOM = {
    "rol": "role_id", "mechanisme": "mechanism_id",
    "entiteit": "entity_id", "emergent_effect": "emergent_effect_id",
}
# Toegestane granulariteitsoperaties (relaties splits/merge je niet; een relatie
# corrigeer je via haar eigen discussieboom of een nieuwe relatie).
GRANULARITEIT_TYPES = ("rol", "mechanisme", "entiteit")

MECHANISME_FILTERS = ("eigendom", "advertentie", "sourcing", "flak", "ideologie",
                      "cross_filter", "tegenmacht", "overig")
ROL_CATEGORIEEN = ("eigendom", "advertentie", "sourcing", "flak", "ideologie",
                   "systeemactor", "tegenmacht", "overig")
VELD_CATEGORIEEN = ("eigendom", "advertentie", "sourcing", "flak", "ideologie",
                    "systeemactor", "overig")
AARD_KEUZES = ("direct", "veld_eigenschap")  # de twee levende waarden (zie CLAUDE.md)


def _tekst(payload, veld):
    return (payload.get(veld) or "").strip() if isinstance(payload.get(veld), str) else ""


def _naam_bestaat(conn, element_type, naam):
    return conn.execute(f"SELECT 1 FROM {TABEL[element_type]} WHERE name = ?",
                        (naam,)).fetchone() is not None


def _element(conn, element_type, element_id):
    return conn.execute(
        f"SELECT * FROM {TABEL[element_type]} WHERE id = ?", (element_id,)).fetchone()


# ── Gestructureerde instantiaties (bottom-up koppeling) ──────
# Een RfC-payload draagt verplicht ≥ 1 instantiatie. Een instantiatie als losse string
# is louter beschrijvend; als object (dict) is ze een *praktijkrelatie* die bij
# acceptatie aan het nieuwe mechanisme wordt gekoppeld — óf een nieuwe 'voorgesteld'-
# relatie, óf adoptie van een bestaande kandidaat ({'bestaande_relatie_id': N}). Zo
# krijgt een incuberend praktijkpatroon eindelijk zijn theorie-huis, in één besluit.

def _clamp01(v):
    if v in (None, ""):
        return None
    try:
        return min(1.0, max(0.0, float(v)))
    except (ValueError, TypeError):
        return None


def _instantiatie_specs(payload) -> list:
    """De gestructureerde (dict) instantiaties; tekst-instantiaties (str) materialiseren niets."""
    return [d for d in (payload.get("instantiaties") or []) if isinstance(d, dict)]


def _valideer_instantiatie_specs(conn, element_type, payload, fouten):
    specs = _instantiatie_specs(payload)
    if not specs:
        return
    if element_type != "mechanisme":
        fouten.append("een gestructureerde instantiatie (relatie) kan alleen bij een "
                      f"mechanisme-RfC; gebruik beschrijvende tekst voor een {element_type}-RfC")
        return
    for i, spec in enumerate(specs, 1):
        pre = f"instantiatie #{i}: "
        if spec.get("type", "relatie") != "relatie":
            fouten.append(f"{pre}alleen type 'relatie' wordt ondersteund")
            continue
        if spec.get("bestaande_relatie_id"):
            rij = conn.execute("SELECT mechanism_id FROM relations WHERE id = ?",
                               (spec["bestaande_relatie_id"],)).fetchone()
            if rij is None:
                fouten.append(f"{pre}relatie #{spec['bestaande_relatie_id']} bestaat niet")
            elif rij["mechanism_id"] is not None:
                fouten.append(f"{pre}relatie #{spec['bestaande_relatie_id']} hangt al aan een "
                              "mechanisme — alleen een kandidaat (mechanisme-loos) is adopteerbaar")
            continue
        bron, doel = spec.get("source_id"), spec.get("target_id")
        if not bron or not doel:
            fouten.append(f"{pre}source_id en target_id (of bestaande_relatie_id) zijn verplicht")
        elif bron == doel:
            fouten.append(f"{pre}bron en doel mogen niet dezelfde entiteit zijn")
        else:
            for label, eid in (("bron", bron), ("doel", doel)):
                if not conn.execute("SELECT 1 FROM entities WHERE id = ?", (eid,)).fetchone():
                    fouten.append(f"{pre}{label}-entiteit #{eid} bestaat niet")
        if not _tekst(spec, "relation_type"):
            fouten.append(f"{pre}relation_type is verplicht")


# ── Sjablooncontrole bij indienen ────────────────────────────

def _valideer_elementvelden(conn, element_type, velden, fouten, prefix=""):
    """Minimale definitie van een NIEUW element (gebruikt door alle soorten)."""
    naam = _tekst(velden, "naam")
    if not naam:
        fouten.append(f"{prefix}naam is verplicht")
    elif element_type in TABEL and _naam_bestaat(conn, element_type, naam):
        fouten.append(f"{prefix}er bestaat al een {element_type} met de naam '{naam}'")
    if not _tekst(velden, "definitie"):
        fouten.append(f"{prefix}definitie is verplicht")
    if element_type == "mechanisme":
        if velden.get("filter") not in MECHANISME_FILTERS:
            fouten.append(f"{prefix}filter moet een van {MECHANISME_FILTERS} zijn")
        if not _tekst(velden, "effect"):
            fouten.append(f"{prefix}effect is verplicht")
        aard = velden.get("aard")
        if aard not in AARD_KEUZES:
            fouten.append(f"{prefix}aard moet 'direct' of 'veld_eigenschap' zijn "
                          "(beslisgids: CLAUDE.md)")
        # Rol-eindpunten: een 'direct' edge vergt bron- én doelrol, anders tekent ze
        # niet (de val waarin RfC #41 belandde). Een veld_eigenschap vergt minstens de
        # doelrol (de knoop waarvan het een eigenschap is); de bron mag diffuus/NULL zijn.
        for sleutel, verplicht in (("source_role_id", aard == "direct"),
                                   ("target_role_id", aard in ("direct", "veld_eigenschap"))):
            rid = velden.get(sleutel)
            if rid in (None, "", 0, "0"):
                if verplicht:
                    fouten.append(f"{prefix}{sleutel} is verplicht voor aard '{aard}' "
                                  "— een edge zonder rol-eindpunt tekent niet")
                continue
            try:
                rid = int(rid)
            except (ValueError, TypeError):
                fouten.append(f"{prefix}{sleutel} moet een rol-id (geheel getal) zijn")
                continue
            rol = conn.execute("SELECT vervangen FROM roles WHERE id = ?", (rid,)).fetchone()
            if rol is None:
                fouten.append(f"{prefix}{sleutel}: rol {rid} bestaat niet")
            elif rol["vervangen"]:
                fouten.append(f"{prefix}{sleutel}: rol {rid} is vervangen; kies de opvolger")
    elif element_type == "rol":
        if velden.get("categorie") not in ROL_CATEGORIEEN:
            fouten.append(f"{prefix}categorie moet een van {ROL_CATEGORIEEN} zijn")
    elif element_type == "emergent_effect":
        if not _tekst(velden, "label"):
            fouten.append(f"{prefix}label is verplicht")
        if not _tekst(velden, "effect"):
            fouten.append(f"{prefix}effect is verplicht")
        leden = velden.get("leden") or []
        if len(leden) < 2:
            fouten.append(f"{prefix}een emergent veld vergt ≥ 2 leden (rol-id's)")
        # Optioneel: koppel het nieuwe veld bij acceptatie als deel-effect onder een
        # bestaand (apex-)veld. Zonder dit veld blijft het een standalone veld.
        deel_van = velden.get("deel_van")
        if deel_van is not None:
            rij = conn.execute("SELECT vervangen FROM emergent_effects WHERE id = ?",
                               (deel_van,)).fetchone()
            if rij is None:
                fouten.append(f"{prefix}deel_van #{deel_van} bestaat niet "
                              "(onbekend apex-veld om als deel-effect onder te hangen)")
            elif rij["vervangen"]:
                fouten.append(f"{prefix}deel_van #{deel_van} is vervangen; "
                              "koppel aan de opvolger")
    elif element_type == "entiteit":
        if not _tekst(velden, "type"):
            fouten.append(f"{prefix}type is verplicht")


def valideer_payload(conn, soort, payload) -> list:
    """Sjablooncontrole; retourneert een lijst fouten (leeg = indienbaar)."""
    fouten = []
    if soort not in SOORTEN:
        return [f"soort moet een van {SOORTEN} zijn"]
    if not isinstance(payload, dict):
        return ["payload moet een object zijn"]
    et = payload.get("element_type")

    if soort == "nieuw_theorie_element":
        if et not in THEORIE_TYPES:
            return [f"element_type moet een van {THEORIE_TYPES} zijn"]
        _valideer_elementvelden(conn, et, payload, fouten)
        # Het RfC-sjabloon (M2.3): afgrenzing, freeze-test, falsificatie, dekking
        for veld, eis in (
                ("afgrenzing", "afgrenzing van bestaande elementen is verplicht"),
                ("falsificatiecriterium", "een falsificatiecriterium is verplicht "
                                          "(wat zou dit element weerleggen?)")):
            if not _tekst(payload, veld):
                fouten.append(eis)
        if et == "mechanisme" and not _tekst(payload, "freeze_test"):
            fouten.append("de freeze-test bij de aard-keuze is verplicht (blijft de "
                          "toestand werken zonder levende afzender?)")
        if not payload.get("instantiaties"):
            fouten.append("≥ 1 beoogde instantiatie is verplicht (welke praktijk-"
                          "relatie/-entiteit valt eronder?)")
        _valideer_instantiatie_specs(conn, et, payload, fouten)
        if not payload.get("bronnen"):
            fouten.append("≥ 1 onafhankelijke bron is verplicht")

    elif soort == "hernoemen":
        if et not in TABEL or et == "relatie":
            return ["element_type moet rol, mechanisme, entiteit of emergent_effect zijn"]
        rij = _element(conn, et, payload.get("element_id") or 0)
        if rij is None:
            fouten.append("element_id bestaat niet")
        elif rij["vervangen"]:
            fouten.append("element is al vervangen; hernoem de opvolger")
        nieuwe = _tekst(payload, "nieuwe_naam")
        if not nieuwe:
            fouten.append("nieuwe_naam is verplicht")
        elif _naam_bestaat(conn, et, nieuwe):
            fouten.append(f"er bestaat al een {et} met de naam '{nieuwe}'")
        if not _tekst(payload, "motivatie"):
            fouten.append("motivatie is verplicht (verschuift de betekenis wezenlijk, "
                          "dan is het de facto vervangen → kies splitsen/samenvoegen)")

    elif soort == "herformuleren":
        if et not in TABEL:
            return [f"element_type moet een van {tuple(TABEL)} zijn"]
        rij = _element(conn, et, payload.get("element_id") or 0)
        if rij is None:
            fouten.append("element_id bestaat niet")
        elif rij["vervangen"]:
            fouten.append("element is al vervangen; herformuleer de opvolger")
        velden = payload.get("velden") or {}
        toegestaan = TEKSTVELDEN[et]
        onbekend = [k for k in velden if k not in toegestaan]
        if onbekend:
            fouten.append(f"onbekende velden voor {et}: {onbekend} "
                          f"(toegestaan: {toegestaan}; de naam loopt via hernoemen)")
        gewijzigd = [k for k, v in velden.items()
                     if k in toegestaan and (v or "").strip()
                     and (rij is None or (v or "").strip() != (rij[k] or ""))]
        if not gewijzigd:
            fouten.append(f"geef ≥ 1 gewijzigd tekstveld op ({', '.join(toegestaan)})")
        if not _tekst(payload, "motivatie"):
            fouten.append("motivatie is verplicht (verschuift de betekenis wezenlijk, "
                          "dan is het de facto vervangen → kies splitsen/samenvoegen)")

    elif soort == "samenvoegen":
        if et not in GRANULARITEIT_TYPES:
            return [f"element_type moet een van {GRANULARITEIT_TYPES} zijn"]
        oud_ids = payload.get("oud_ids") or []
        doel = payload.get("doel") or {}
        bestaand = doel.get("bestaand_id")
        if len(oud_ids) < (1 if bestaand else 2):
            fouten.append("samenvoegen vergt ≥ 2 elementen (of ≥ 1 plus een bestaand doel)")
        for oid in oud_ids:
            rij = _element(conn, et, oid)
            if rij is None:
                fouten.append(f"oud element #{oid} bestaat niet")
            elif rij["vervangen"]:
                fouten.append(f"oud element #{oid} is al vervangen")
        if bestaand:
            if bestaand in oud_ids:
                fouten.append("het bestaande doel kan niet zelf vervangen worden")
            rij = _element(conn, et, bestaand)
            if rij is None or rij["vervangen"]:
                fouten.append(f"doel-element #{bestaand} bestaat niet of is vervangen")
        else:
            _valideer_elementvelden(conn, et, doel, fouten, prefix="doel: ")
        if not _tekst(payload, "motivatie"):
            fouten.append("motivatie is verplicht (waarom zijn dit niet twee krachten?)")
        if "herbevestigd" not in payload:
            fouten.append("een herbevestigingsplan is verplicht (herbevestigd: "
                          "{argumenten, relaties, instantiaties, padclaims} — bewijs "
                          "verhuist nooit automatisch; een lege lijst is een expliciete keuze)")

    elif soort == "splitsen":
        if et not in GRANULARITEIT_TYPES:
            return [f"element_type moet een van {GRANULARITEIT_TYPES} zijn"]
        rij = _element(conn, et, payload.get("oud_id") or 0)
        if rij is None:
            fouten.append("oud_id bestaat niet")
        elif rij["vervangen"]:
            fouten.append("element is al vervangen")
        nieuwe = payload.get("nieuwe") or []
        if len(nieuwe) < 2:
            fouten.append("splitsen vergt ≥ 2 opvolger-definities")
        namen = set()
        for i, d in enumerate(nieuwe):
            _valideer_elementvelden(conn, et, d or {}, fouten, prefix=f"opvolger {i}: ")
            naam = _tekst(d or {}, "naam")
            if naam in namen:
                fouten.append(f"opvolger {i}: naam '{naam}' dubbel in het voorstel")
            namen.add(naam)
        if not _tekst(payload, "motivatie"):
            fouten.append("motivatie is verplicht (welke twee dingen vermengt dit element?)")
        if "toewijzing" not in payload:
            fouten.append("een hertriage-plan is verplicht (toewijzing: {argumenten, "
                          "relaties, instantiaties, padclaims} — de restlijst moet leeg "
                          "zijn vóór uitvoering)")

    return fouten


# ── Reviewdrempels (M2.2/M2.3) ───────────────────────────────

def is_theorielaag(soort, payload) -> bool:
    return soort == "nieuw_theorie_element" or (
        isinstance(payload, dict) and payload.get("element_type") in THEORIE_TYPES)


def benodigde_akkoorden(soort, payload) -> int:
    """Theorielaag = beschermd niveau (twee menselijke reviewers); praktijk = één."""
    return 2 if is_theorielaag(soort, payload) else 1


def telling(conn, voorstel_id, indiener, theorielaag) -> dict:
    """Telt de geldige akkoorden/afwijzingen.

    Menselijke reviewers tellen; agent-oordelen zijn zichtbaar advies maar tellen
    nooit (§6.4). Op de theorielaag telt de indiener niet mee als reviewer; op de
    praktijklaag wél (n=1-realiteit), maar een zelf-akkoord wordt gevlagd.
    """
    rows = conn.execute("""
        SELECT vr.oordeel, vr.reviewer, u.kind FROM voorstel_reviews vr
        JOIN users u ON u.username = vr.reviewer
        WHERE vr.voorstel_id = ?""", (voorstel_id,)).fetchall()
    akkoorden, afwijzingen, advies = [], [], []
    for r in rows:
        if r["kind"] != "mens":
            advies.append({"reviewer": r["reviewer"], "oordeel": r["oordeel"]})
            continue
        if theorielaag and r["reviewer"] == indiener:
            advies.append({"reviewer": r["reviewer"], "oordeel": r["oordeel"]})
            continue
        (akkoorden if r["oordeel"] == "akkoord" else afwijzingen).append(r["reviewer"])
    return {"akkoorden": akkoorden, "afwijzingen": afwijzingen, "advies": advies,
            "zelf_akkoord": indiener in akkoorden}


# ── Hertriage-administratie (M2.6) ───────────────────────────

def aanhangsels(conn, element_type, oud_id) -> dict:
    """Alles wat aan een element hangt en bij splitsen toegewezen moet worden."""
    kol = ARG_KOLOM[element_type]
    argumenten = [r[0] for r in conn.execute(
        f"""SELECT id FROM arguments WHERE {kol} = ? AND parent_argument_id IS NULL
            AND (property IS NULL OR property != 'indirecte_invloed_op')""", (oud_id,))]
    padclaims = []
    if element_type == "rol":
        padclaims = [r[0] for r in conn.execute(
            """SELECT id FROM arguments WHERE property = 'indirecte_invloed_op'
               AND (role_id = ? OR property_value = ?)""", (oud_id, str(oud_id)))]
    if element_type == "mechanisme":
        relaties = [r[0] for r in conn.execute(
            "SELECT id FROM relations WHERE mechanism_id = ?", (oud_id,))]
        instantiaties = [r[0] for r in conn.execute(
            "SELECT id FROM instantiations WHERE mechanism_id = ?", (oud_id,))]
    elif element_type == "rol":
        relaties = []
        instantiaties = [r[0] for r in conn.execute(
            "SELECT id FROM instantiations WHERE role_id = ?", (oud_id,))]
    else:  # entiteit
        relaties = [r[0] for r in conn.execute(
            "SELECT id FROM relations WHERE source_id = ? OR target_id = ?",
            (oud_id, oud_id))]
        instantiaties = [r[0] for r in conn.execute(
            "SELECT id FROM instantiations WHERE entity_id = ?", (oud_id,))]
    return {"argumenten": argumenten, "relaties": relaties,
            "instantiaties": instantiaties, "padclaims": padclaims}


def _maak_element(conn, element_type, velden) -> int:
    if element_type == "rol":
        cur = conn.execute(
            "INSERT INTO roles (name, category, description, examples) VALUES (?, ?, ?, ?)",
            (velden["naam"].strip(), velden["categorie"], velden["definitie"].strip(),
             (velden.get("voorbeelden") or "").strip() or None))
    elif element_type == "mechanisme":
        cur = conn.execute(
            """INSERT INTO mechanisms (name, filter, mechanism_type, description, effect,
                                       source_role_id, target_role_id, aard)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (velden["naam"].strip(), velden["filter"], velden.get("mechanisme_type"),
             velden["definitie"].strip(), velden["effect"].strip(),
             velden.get("source_role_id"), velden.get("target_role_id"), velden["aard"]))
    elif element_type == "entiteit":
        cur = conn.execute(
            "INSERT INTO entities (name, type, primary_role_id, description) VALUES (?, ?, ?, ?)",
            (velden["naam"].strip(), velden["type"], velden.get("primary_role_id"),
             velden["definitie"].strip()))
    elif element_type == "emergent_effect":
        cur = conn.execute(
            """INSERT INTO emergent_effects (name, label, category, description, effect)
               VALUES (?, ?, ?, ?, ?)""",
            (velden["naam"].strip(), velden["label"].strip(),
             velden.get("categorie") or "systeemactor",
             velden["definitie"].strip(), velden["effect"].strip()))
        eff_id = cur.lastrowid
        for rid in velden.get("leden") or []:
            conn.execute("INSERT INTO emergent_effect_members (emergent_effect_id, role_id)"
                         " VALUES (?, ?)", (eff_id, rid))
        # Deel-effect-koppeling onder een apex-veld (optioneel; gevalideerd bij indienen).
        if velden.get("deel_van"):
            conn.execute("INSERT OR IGNORE INTO emergent_effect_subeffects "
                         "(parent_effect_id, child_effect_id) VALUES (?, ?)",
                         (velden["deel_van"], eff_id))
    else:
        raise ValueError(f"onbekend element_type '{element_type}'")
    return cur.lastrowid


def _verhuis_instantiatie(conn, element_type, inst_id, nieuw_id):
    """Re-point de klasse-/instantiekant; bij een UNIQUE-botsing vervalt de oude rij."""
    kol = {"rol": "role_id", "mechanisme": "mechanism_id", "entiteit": "entity_id"}[element_type]
    rij = conn.execute("SELECT * FROM instantiations WHERE id = ?", (inst_id,)).fetchone()
    if rij is None:
        raise ValueError(f"instantiatie #{inst_id} bestaat niet")
    paar = {"rol": ("role_id", "entity_id"), "mechanisme": ("mechanism_id", "relation_id"),
            "entiteit": ("role_id", "entity_id")}[element_type]
    nieuwe_waarden = {paar[0]: rij[paar[0]], paar[1]: rij[paar[1]], kol: nieuw_id}
    botsing = conn.execute(
        f"SELECT id FROM instantiations WHERE {paar[0]} = ? AND {paar[1]} = ? AND id != ?",
        (nieuwe_waarden[paar[0]], nieuwe_waarden[paar[1]], inst_id)).fetchone()
    if botsing:
        conn.execute("DELETE FROM instantiations WHERE id = ?", (inst_id,))
    else:
        conn.execute(f"UPDATE instantiations SET {kol} = ? WHERE id = ?", (nieuw_id, inst_id))


def _dupliceer_argument(conn, arg_id, kol, nieuw_doel) -> int:
    rij = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    velden = {k: rij[k] for k in rij.keys() if k != "id"}
    velden[kol] = nieuw_doel
    kols = ", ".join(velden)
    cur = conn.execute(
        f"INSERT INTO arguments ({kols}) VALUES ({', '.join('?' * len(velden))})",
        list(velden.values()))
    for c in conn.execute("SELECT * FROM citations WHERE argument_id = ?", (arg_id,)).fetchall():
        conn.execute("""INSERT INTO citations (argument_id, source_id, quote, page, section, context)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                     (cur.lastrowid, c["source_id"], c["quote"], c["page"],
                      c["section"], c["context"]))
    return cur.lastrowid


def _dupliceer_relatie(conn, rel_id, overrides) -> int:
    rij = conn.execute("SELECT * FROM relations WHERE id = ?", (rel_id,)).fetchone()
    velden = {k: rij[k] for k in rij.keys() if k != "id"}
    velden.update(overrides)
    kols = ", ".join(velden)
    cur = conn.execute(
        f"INSERT INTO relations ({kols}) VALUES ({', '.join('?' * len(velden))})",
        list(velden.values()))
    return cur.lastrowid


# ── Uitvoering ná acceptatie ─────────────────────────────────

def _materialiseer_instantiaties(conn, mechanism_id, payload, voorstel_id, ingediend_door):
    """Maak/adopteer de gestructureerde instantiaties als praktijkrelaties aan het
    zojuist gemaakte mechanisme. Nieuw → een 'voorgesteld'-relatie (telt in niets tot
    een reviewer haar apart goedkeurt — de poorten blijven ontkoppeld); adoptie → een
    bestaande kandidaat krijgt dit mechanisme (en wordt zo goedkeurbaar). Evidence komt
    er daarna via de eigen discussieboom. Raise ValueError = niet uitvoerbaar."""
    nieuw, geadopteerd = [], []
    for spec in _instantiatie_specs(payload):
        bestaand = spec.get("bestaande_relatie_id")
        if bestaand:
            rij = conn.execute("SELECT mechanism_id FROM relations WHERE id = ?",
                               (bestaand,)).fetchone()
            if rij is None:
                raise ValueError(f"kandidaat-relatie #{bestaand} bestaat niet meer")
            if rij["mechanism_id"] is not None:
                raise ValueError(f"relatie #{bestaand} hangt al aan een mechanisme")
            conn.execute("UPDATE relations SET mechanism_id = ? WHERE id = ?",
                         (mechanism_id, bestaand))
            conn.execute("""
                INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
                VALUES ('relations', ?, 'updated', ?, ?, ?)
            """, (bestaand, ingediend_door, json.dumps({"mechanism_id": mechanism_id}),
                  f"kandidaat geadopteerd door RfC-voorstel #{voorstel_id}"))
            # Klasse↔instantie-link: zonder deze rij telt de relatie niet mee in de
            # theoriescore van het mechanisme (laag C) en trekt ze KOPPEL-REL-INST.
            conn.execute("INSERT OR IGNORE INTO instantiations (mechanism_id, relation_id) "
                         "VALUES (?, ?)", (mechanism_id, bestaand))
            geadopteerd.append(bestaand)
            continue
        bron, doel = spec.get("source_id"), spec.get("target_id")
        for label, eid in (("bron", bron), ("doel", doel)):
            if not conn.execute("SELECT 1 FROM entities WHERE id = ?", (eid,)).fetchone():
                raise ValueError(f"{label}-entiteit #{eid} bestaat niet meer")
        rtype = (spec.get("relation_type") or "").strip()
        influence = _clamp01(spec.get("influence"))
        if influence is None:
            influence = 0.05   # guilty-until-proven-vloer, als POST /api/relations
        cur = conn.execute("""
            INSERT INTO relations
                (source_id, target_id, relation_type, mechanism_id, description,
                 certainty, influence, bidirectional, active_from, active_until, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'voorgesteld')
        """, (bron, doel, rtype, mechanism_id,
              (spec.get("description") or "").strip() or None,
              _clamp01(spec.get("certainty")), influence,
              1 if spec.get("bidirectional") else 0,
              (spec.get("active_from") or "").strip() or None,
              (spec.get("active_until") or "").strip() or None))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('relations', ?, 'created', ?, ?, ?)
        """, (cur.lastrowid, ingediend_door,
              json.dumps({"source_id": bron, "target_id": doel, "relation_type": rtype,
                          "mechanism_id": mechanism_id, "status": "voorgesteld"}),
              f"instantiatie gematerialiseerd uit RfC-voorstel #{voorstel_id} (wacht op merge)"))
        # Klasse↔instantie-link (zie adoptie-tak): laat de relatie meetellen in de
        # theoriescore van het mechanisme en houd KOPPEL-REL-INST schoon.
        conn.execute("INSERT OR IGNORE INTO instantiations (mechanism_id, relation_id) "
                     "VALUES (?, ?)", (mechanism_id, cur.lastrowid))
        nieuw.append(cur.lastrowid)
    return nieuw, geadopteerd


def voer_uit(conn, soort, payload, voorstel_id, ingediend_door=None) -> dict:
    """Voer een geaccepteerd voorstel uit (binnen de transactie van de aanroeper).

    Raise ValueError = niet uitvoerbaar (bv. hertriage-restlijst niet leeg);
    het voorstel blijft dan open en de aanroeper rolt terug.
    """
    if soort == "nieuw_theorie_element":
        et = payload["element_type"]
        nieuw_id = _maak_element(conn, et, payload)
        resultaat = {"element_type": et, "id": nieuw_id}
        if et == "mechanisme":
            nieuw, geadopteerd = _materialiseer_instantiaties(
                conn, nieuw_id, payload, voorstel_id, ingediend_door)
            if nieuw:
                resultaat["instantiaties_aangemaakt"] = nieuw
            if geadopteerd:
                resultaat["instantiaties_geadopteerd"] = geadopteerd
        return resultaat

    if soort == "hernoemen":
        et = payload["element_type"]
        rij = _element(conn, et, payload["element_id"])
        if rij is None:
            raise ValueError("element bestaat niet meer")
        naamkolom = "name"
        oude_naam = rij["name"]
        conn.execute(f"UPDATE {TABEL[et]} SET {naamkolom} = ? WHERE id = ?",
                     (payload["nieuwe_naam"].strip(), payload["element_id"]))
        if et == "emergent_effect" and payload.get("nieuw_label"):
            conn.execute("UPDATE emergent_effects SET label = ? WHERE id = ?",
                         (payload["nieuw_label"].strip(), payload["element_id"]))
        conn.execute("""INSERT INTO lineage (soort, element_type, oud_id, nieuw_id,
                                             voorstel_id, reden)
                        VALUES ('hernoemen', ?, ?, ?, ?, ?)""",
                     (et, payload["element_id"], payload["element_id"], voorstel_id,
                      f"oude naam: {oude_naam}"))
        return {"element_type": et, "id": payload["element_id"], "oude_naam": oude_naam}

    if soort == "herformuleren":
        et = payload["element_type"]
        rij = _element(conn, et, payload["element_id"])
        if rij is None:
            raise ValueError("element bestaat niet meer")
        velden = payload.get("velden") or {}
        toegestaan = TEKSTVELDEN[et]
        diff = {}
        for kol in toegestaan:
            if kol in velden and (velden[kol] or "").strip():
                nieuw = velden[kol].strip()
                if nieuw != (rij[kol] or ""):
                    diff[kol] = {"oud": rij[kol], "nieuw": nieuw}
                    conn.execute(f"UPDATE {TABEL[et]} SET {kol} = ? WHERE id = ?",
                                 (nieuw, payload["element_id"]))
        if not diff:
            raise ValueError("geen gewijzigd tekstveld")
        conn.execute("""INSERT INTO lineage (soort, element_type, oud_id, nieuw_id,
                                             voorstel_id, reden)
                        VALUES ('herformuleren', ?, ?, ?, ?, ?)""",
                     (et, payload["element_id"], payload["element_id"], voorstel_id,
                      payload.get("motivatie")))
        return {"element_type": et, "id": payload["element_id"],
                "gewijzigd": list(diff), "diff": diff}

    if soort == "samenvoegen":
        return _voer_samenvoegen_uit(conn, payload, voorstel_id)
    if soort == "splitsen":
        return _voer_splitsen_uit(conn, payload, voorstel_id)
    raise ValueError(f"onbekende soort '{soort}'")


def _voer_samenvoegen_uit(conn, payload, voorstel_id) -> dict:
    et = payload["element_type"]
    oud_ids = list(payload["oud_ids"])
    doel = payload.get("doel") or {}
    nieuw_id = doel.get("bestaand_id") or _maak_element(conn, et, doel)
    kol = ARG_KOLOM[et]
    her = payload.get("herbevestigd") or {}
    oud_set = set(oud_ids)

    verplaatst = {"argumenten": 0, "relaties": 0, "instantiaties": 0, "padclaims": 0}
    for aid in her.get("argumenten") or []:
        rij = conn.execute(f"SELECT {kol} AS doel FROM arguments WHERE id = ?",
                           (aid,)).fetchone()
        if rij is None or rij["doel"] not in oud_set:
            raise ValueError(f"herbevestigd argument #{aid} hangt niet aan een oud element")
        conn.execute(f"UPDATE arguments SET {kol} = ? WHERE id = ?", (nieuw_id, aid))
        verplaatst["argumenten"] += 1

    for rid in her.get("relaties") or []:
        rij = conn.execute("SELECT * FROM relations WHERE id = ?", (rid,)).fetchone()
        if rij is None:
            raise ValueError(f"herbevestigde relatie #{rid} bestaat niet")
        if et == "mechanisme":
            if rij["mechanism_id"] not in oud_set:
                raise ValueError(f"relatie #{rid} hangt niet aan een oud mechanisme")
            conn.execute("UPDATE relations SET mechanism_id = ? WHERE id = ?", (nieuw_id, rid))
        elif et == "entiteit":
            if rij["source_id"] not in oud_set and rij["target_id"] not in oud_set:
                raise ValueError(f"relatie #{rid} raakt geen oude entiteit")
            src = nieuw_id if rij["source_id"] in oud_set else rij["source_id"]
            tgt = nieuw_id if rij["target_id"] in oud_set else rij["target_id"]
            conn.execute("UPDATE relations SET source_id = ?, target_id = ? WHERE id = ?",
                         (src, tgt, rid))
        else:
            raise ValueError("relatie-herbevestiging geldt alleen voor mechanisme/entiteit")
        verplaatst["relaties"] += 1

    for iid in her.get("instantiaties") or []:
        _verhuis_instantiatie(conn, et, iid, nieuw_id)
        verplaatst["instantiaties"] += 1

    if et == "rol":
        oud_strs = {str(o) for o in oud_set}
        for aid in her.get("padclaims") or []:
            rij = conn.execute(
                "SELECT role_id, property_value FROM arguments WHERE id = ? "
                "AND property = 'indirecte_invloed_op'", (aid,)).fetchone()
            if rij is None or (rij["role_id"] not in oud_set
                               and (rij["property_value"] or "") not in oud_strs):
                raise ValueError(f"padclaim #{aid} hangt niet aan een oude rol")
            if rij["role_id"] in oud_set:
                conn.execute("UPDATE arguments SET role_id = ? WHERE id = ?", (nieuw_id, aid))
            if (rij["property_value"] or "") in oud_strs:
                conn.execute("UPDATE arguments SET property_value = ? WHERE id = ?",
                             (str(nieuw_id), aid))
            verplaatst["padclaims"] += 1

    for oud in oud_ids:
        conn.execute(f"UPDATE {TABEL[et]} SET vervangen = 1 WHERE id = ?", (oud,))
        conn.execute("""INSERT INTO lineage (soort, element_type, oud_id, nieuw_id,
                                             voorstel_id, reden)
                        VALUES ('samenvoegen', ?, ?, ?, ?, ?)""",
                     (et, oud, nieuw_id, voorstel_id, payload.get("motivatie")))
    achtergebleven = sum(len(v) for v in aanhangsels_meervoudig(conn, et, oud_ids).values())
    return {"element_type": et, "nieuw_id": nieuw_id, "vervangen": oud_ids,
            "verplaatst": verplaatst, "achtergebleven": achtergebleven}


def aanhangsels_meervoudig(conn, element_type, oud_ids) -> dict:
    totaal = {"argumenten": [], "relaties": [], "instantiaties": [], "padclaims": []}
    for oid in oud_ids:
        for k, v in aanhangsels(conn, element_type, oid).items():
            totaal[k].extend(v)
    return totaal


def _voer_splitsen_uit(conn, payload, voorstel_id) -> dict:
    et = payload["element_type"]
    oud_id = payload["oud_id"]
    nieuw_ids = [_maak_element(conn, et, d) for d in payload["nieuwe"]]
    kol = ARG_KOLOM[et]
    toe = payload.get("toewijzing") or {}

    def _norm(naam):
        ruw = toe.get(naam) or {}
        uit = {}
        for k, v in ruw.items():
            idxs = v if isinstance(v, list) else [v]
            for i in idxs:
                if not isinstance(i, int) or not 0 <= i < len(nieuw_ids):
                    raise ValueError(f"toewijzing.{naam}[{k}]: index {i} bestaat niet "
                                     f"(0–{len(nieuw_ids) - 1})")
            uit[int(k)] = idxs
        return uit

    arg_toe, rel_toe = _norm("argumenten"), _norm("relaties")
    inst_toe, pad_toe = _norm("instantiaties"), _norm("padclaims")

    # De lakmoesproef: de restlijst moet leeg zijn vóór afronding (M2.6-kernregel 2).
    aan = aanhangsels(conn, et, oud_id)
    rest = ([f"argument #{a}" for a in aan["argumenten"] if not arg_toe.get(a)]
            + [f"relatie #{r}" for r in aan["relaties"] if not rel_toe.get(r)]
            + [f"instantiatie #{i}" for i in aan["instantiaties"] if not inst_toe.get(i)]
            + [f"padclaim #{p}" for p in aan["padclaims"] if not pad_toe.get(p)])
    if rest:
        raise ValueError("hertriage-restlijst is niet leeg: " + "; ".join(rest))

    for aid, idxs in arg_toe.items():
        if aid not in aan["argumenten"]:
            raise ValueError(f"argument #{aid} hangt niet aan element #{oud_id}")
        conn.execute(f"UPDATE arguments SET {kol} = ? WHERE id = ?", (nieuw_ids[idxs[0]], aid))
        for i in idxs[1:]:
            _dupliceer_argument(conn, aid, kol, nieuw_ids[i])

    for rid, idxs in rel_toe.items():
        if rid not in aan["relaties"]:
            raise ValueError(f"relatie #{rid} hangt niet aan element #{oud_id}")
        rij = conn.execute("SELECT * FROM relations WHERE id = ?", (rid,)).fetchone()
        if et == "mechanisme":
            conn.execute("UPDATE relations SET mechanism_id = ? WHERE id = ?",
                         (nieuw_ids[idxs[0]], rid))
            for i in idxs[1:]:
                _dupliceer_relatie(conn, rid, {"mechanism_id": nieuw_ids[i]})
        else:  # entiteit: endpoints her-adresseren; dupliceren per extra opvolger
            def _ends(nid):
                return {"source_id": nid if rij["source_id"] == oud_id else rij["source_id"],
                        "target_id": nid if rij["target_id"] == oud_id else rij["target_id"]}
            e0 = _ends(nieuw_ids[idxs[0]])
            conn.execute("UPDATE relations SET source_id = ?, target_id = ? WHERE id = ?",
                         (e0["source_id"], e0["target_id"], rid))
            for i in idxs[1:]:
                _dupliceer_relatie(conn, rid, _ends(nieuw_ids[i]))

    for iid, idxs in inst_toe.items():
        if iid not in aan["instantiaties"]:
            raise ValueError(f"instantiatie #{iid} hangt niet aan element #{oud_id}")
        rij = conn.execute("SELECT * FROM instantiations WHERE id = ?", (iid,)).fetchone()
        _verhuis_instantiatie(conn, et, iid, nieuw_ids[idxs[0]])
        # extra opvolgers: nieuwe rij (zelfde instantiekant, andere klasse)
        klasse_kol = {"rol": "role_id", "mechanisme": "mechanism_id",
                      "entiteit": "entity_id"}[et]
        for i in idxs[1:]:
            velden = {k: rij[k] for k in rij.keys() if k != "id"}
            velden[klasse_kol] = nieuw_ids[i]
            conn.execute(
                f"INSERT OR IGNORE INTO instantiations ({', '.join(velden)}) "
                f"VALUES ({', '.join('?' * len(velden))})", list(velden.values()))

    for pid, idxs in pad_toe.items():
        if pid not in aan["padclaims"]:
            raise ValueError(f"padclaim #{pid} hangt niet aan rol #{oud_id}")
        if len(idxs) != 1:
            raise ValueError(f"padclaim #{pid}: een padclaim kent precies één opvolger")
        rij = conn.execute("SELECT role_id, property_value FROM arguments WHERE id = ?",
                           (pid,)).fetchone()
        if rij["role_id"] == oud_id:
            conn.execute("UPDATE arguments SET role_id = ? WHERE id = ?",
                         (nieuw_ids[idxs[0]], pid))
        if (rij["property_value"] or "") == str(oud_id):
            conn.execute("UPDATE arguments SET property_value = ? WHERE id = ?",
                         (str(nieuw_ids[idxs[0]]), pid))

    conn.execute(f"UPDATE {TABEL[et]} SET vervangen = 1 WHERE id = ?", (oud_id,))
    for nid in nieuw_ids:
        conn.execute("""INSERT INTO lineage (soort, element_type, oud_id, nieuw_id,
                                             voorstel_id, reden)
                        VALUES ('splitsen', ?, ?, ?, ?, ?)""",
                     (et, oud_id, nid, voorstel_id, payload.get("motivatie")))
    return {"element_type": et, "oud_id": oud_id, "nieuw_ids": nieuw_ids}
