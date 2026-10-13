"""validation.py — gezondheids- en consistentiechecks voor het model (verbeterplan M0.1).

Gedeeld door scripts/validate_model.py (CLI) en server.py (/api/health): één module,
dus de cijfers in de viz zijn per constructie identiek aan de validatoruitvoer (M0.5).
Alleen stdlib.

Elke check levert één of meer "bevindingen":
    {code, titel, ernst, aantal, voorbeelden, toelichting}
met ernst ∈ {'fout', 'waarschuwing', 'info'}. 'fout' is de strenge laag: zodra de
achterstand is weggewerkt houdt `--strict` (exit-code ≠ 0) het model op nul fouten.
"""
from __future__ import annotations

import datetime
import re
import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
MAX_VOORBEELDEN = 8

# DDL-verschillen (CHECK-teksten, commentaar) die bewust bestaan en dus geen drift zijn.
# Kolom-/FK-/indexpariteit blijft ook voor deze tabellen de strenge eis.
BEKENDE_DDL_VERSCHILLEN = {
    "entities": "schema.sql staat LEGACY-types toe voor seed-replay; live is opgeschoond "
                "(migrate_clean_entity_types.py). Ook de status-CHECK leeft alleen in "
                "schema.sql; live kolom kwam via ALTER TABLE (migrate_moderatie_wachtrij.py). "
                "bestuurslaag kwam via ALTER TABLE (migrate_add_besluitvorming.py)",
    "mechanisms": "aard-CHECK leeft alleen in schema.sql; live kolom kwam via ALTER TABLE "
                  "(zie CLAUDE.md)",
    "relations": "status-CHECK (moderatiewachtrij) leeft alleen in schema.sql; live kolom "
                 "kwam via ALTER TABLE (migrate_moderatie_wachtrij.py); functie kwam via ALTER "
                 "TABLE (migrate_add_besluitvorming.py)",
    "sources": "CHECK op reliability_voorgesteld/onderwerp_voorgesteld leeft alleen in "
               "schema.sql; live kolommen kwamen via ALTER TABLE "
               "(migrate_classificatie_voorstel.py)",
    "arguments": "property-CHECK kreeg 'politieke_positie' + 'machtsvalentie' via tabel-"
                 "rebuild (migrate_politieke_positie_property.py, migrate_machtsvalentie_"
                 "property.py); de enum-waarden zijn gelijk, "
                 "alleen het CHECK-commentaar verschilt van schema.sql",
}


def _bevinding(code, titel, ernst, items, toelichting="", aantal=None):
    items = list(items)
    return {
        "code": code,
        "titel": titel,
        "ernst": ernst,
        "aantal": len(items) if aantal is None else aantal,
        "voorbeelden": items[:MAX_VOORBEELDEN],
        "toelichting": toelichting,
    }


# ── Koppelingsplicht (Z6) ────────────────────────────────────

def check_koppelingsplicht(conn):
    # Vervangen elementen (M2.6) zijn bewust uit de keten; de plicht geldt het levende model.
    rel_zonder_mech = [
        f"relatie #{r['id']}: {r['src']} —{r['relation_type']}→ {r['tgt']}"
        for r in conn.execute("""
            SELECT r.id, r.relation_type, e1.name AS src, e2.name AS tgt
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            WHERE r.mechanism_id IS NULL AND NOT r.vervangen
              AND r.status = 'goedgekeurd' ORDER BY r.id
        """)]

    rel_zonder_inst = [
        f"relatie #{r['id']}: {r['src']} —{r['relation_type']}→ {r['tgt']} (mechanisme: {r['mech']})"
        for r in conn.execute("""
            SELECT r.id, r.relation_type, e1.name AS src, e2.name AS tgt, m.name AS mech
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            JOIN mechanisms m ON r.mechanism_id = m.id
            WHERE NOT EXISTS (SELECT 1 FROM instantiations i
                              WHERE i.relation_id = r.id AND i.mechanism_id = r.mechanism_id)
              AND NOT r.vervangen AND NOT m.vervangen AND r.status = 'goedgekeurd'
            ORDER BY r.id
        """)]

    # Een entiteit "zonder rol" is pas een fout als ze ook geen *afleidbare* rol heeft:
    # met de afgeleide primaire rol (scoring.py) volstaat een goedgekeurde bron-relatie
    # met mechanisme. Voorgestelde entiteiten tellen nog niet mee (telt-in-niets).
    ent_zonder_rol = [
        f"entiteit #{e['id']}: {e['name']} ({e['type']})"
        for e in conn.execute("""
            SELECT e.id, e.name, e.type FROM entities e
            WHERE e.primary_role_id IS NULL AND NOT e.vervangen
              AND e.status = 'goedgekeurd'
              AND NOT EXISTS (SELECT 1 FROM entity_roles er WHERE er.entity_id = e.id)
              AND NOT EXISTS (SELECT 1 FROM relations r WHERE r.source_id = e.id
                              AND r.status = 'goedgekeurd' AND NOT r.vervangen
                              AND r.mechanism_id IS NOT NULL)
            ORDER BY e.id
        """)]

    # Uitbreiding C (2026-10-07): mechanism_filters bevat alle filter-tags INCLUSIEF de
    # primaire. Ontbreekt die rij, dan verdringt de eerste extra categorie (overlap) de
    # primaire filter uit de lijst van de viz (viz_data.py valt alleen terug op de primaire
    # als er géén rijen zijn). cross_filter is geen tag (zie DOCUMENTATIE.md).
    mech_zonder_primair = [
        f"mechanisme #{m['id']}: {m['name']} (filter {m['filter']})"
        for m in conn.execute("""
            SELECT m.id, m.name, m.filter FROM mechanisms m
            WHERE NOT m.vervangen AND m.filter NOT IN ('cross_filter', 'systeemactor')
              AND NOT EXISTS (SELECT 1 FROM mechanism_filters mf
                              WHERE mf.mechanism_id = m.id AND mf.filter = m.filter)
            ORDER BY m.id
        """)]

    ent_zonder_inst = [
        f"entiteit #{e['id']}: {e['name']} ({e['type']})"
        for e in conn.execute("""
            SELECT e.id, e.name, e.type FROM entities e
            WHERE NOT EXISTS (SELECT 1 FROM instantiations i WHERE i.entity_id = e.id)
              AND NOT e.vervangen AND e.status = 'goedgekeurd'
            ORDER BY e.id
        """)]

    return [
        _bevinding("KOPPEL-REL-MECH", "Goedgekeurde relaties zonder mechanisme", "fout",
                   rel_zonder_mech,
                   "Een *goedgekeurde* praktijk-edge hoort aan een theoretisch mechanisme "
                   "te hangen. Een mechanisme-loze 'voorgesteld'-relatie is géén fout maar "
                   "een toegestane kandidaat (incubeert tot een RfC haar adopteert) — "
                   "zie GET /api/kandidaten."),
        _bevinding("KOPPEL-REL-INST", "Relaties mét mechanisme maar zonder instantiations-rij",
                   "fout", rel_zonder_inst,
                   "Zonder instantiatie telt de relatie stilletjes niet mee in de theoriescore (laag C)."),
        _bevinding("KOPPEL-ENT-ROL", "Entiteiten zonder rol", "fout", ent_zonder_rol,
                   "Geen primary_role_id, geen entity_roles-rij én geen afleidbare rol "
                   "(goedgekeurde bron-relatie met mechanisme)."),
        _bevinding("KOPPEL-ENT-INST", "Entiteiten zonder rol-instantiatie", "waarschuwing",
                   ent_zonder_inst,
                   "Wel of geen rol, maar geen instantiations-rij: onzichtbaar voor de rolscore."),
        _bevinding("KOPPEL-MECH-FILTER", "Mechanismen zonder hun primaire filter in "
                   "mechanism_filters", "fout", mech_zonder_primair,
                   "mechanism_filters hoort alle filter-tags te bevatten, inclusief de primaire; "
                   "anders verdringt een extra (overlappende) categorie de primaire filter."),
    ]


# ── Zichtbaarheid & volledigheid (wat staat wel in de DB, niet in de viz?) ──

def check_zichtbaarheid(conn):
    """De viz tekent alleen 'goedgekeurd'; voorgesteld werk is onzichtbaar tot een
    mens het goedkeurt (M2.2). Deze check maakt 'onzichtbaar/onaf' expliciet, zodat
    ingediend werk niet ogenschijnlijk 'verdwijnt' — één plek voor "wat mist er nog"."""
    voorgestelde_ent = [
        f"entiteit #{e['id']}: {e['name']} ({e['type']})"
        for e in conn.execute("""
            SELECT id, name, type FROM entities
            WHERE status = 'voorgesteld' AND NOT vervangen ORDER BY id""")]

    voorgestelde_rel = [
        f"relatie #{r['id']}: {r['src']} → {r['tgt']}"
        for r in conn.execute("""
            SELECT r.id, e1.name AS src, e2.name AS tgt FROM relations r
            JOIN entities e1 ON e1.id = r.source_id
            JOIN entities e2 ON e2.id = r.target_id
            WHERE r.status = 'voorgesteld' AND NOT r.vervangen ORDER BY r.id""")]

    # Goedgekeurde edge waarvan minstens één knoop nog niet goedgekeurd is: de viz
    # heeft dan geen knoop om de edge aan te hangen en tekent haar niet (dangling).
    dangling = [
        f"relatie #{r['id']}: {r['src']} ({r['ss']}) → {r['tgt']} ({r['ts']})"
        for r in conn.execute("""
            SELECT r.id, e1.name AS src, e2.name AS tgt,
                   e1.status AS ss, e2.status AS ts FROM relations r
            JOIN entities e1 ON e1.id = r.source_id
            JOIN entities e2 ON e2.id = r.target_id
            WHERE r.status = 'goedgekeurd' AND NOT r.vervangen
              AND (e1.status != 'goedgekeurd' OR e2.status != 'goedgekeurd')
            ORDER BY r.id""")]

    # Zichtbaar, maar de score drijft nog op de prior-vloer: alle root-argumenten
    # van een goedgekeurde relatie staan nog op 'voorgesteld' (tellen-in-niets).
    prior_only = [
        f"relatie #{r['id']}: {r['src']} → {r['tgt']}"
        for r in conn.execute("""
            SELECT r.id, e1.name AS src, e2.name AS tgt FROM relations r
            JOIN entities e1 ON e1.id = r.source_id
            JOIN entities e2 ON e2.id = r.target_id
            WHERE r.status = 'goedgekeurd' AND NOT r.vervangen
              AND EXISTS (SELECT 1 FROM arguments a WHERE a.relation_id = r.id
                          AND a.parent_argument_id IS NULL)
              AND NOT EXISTS (SELECT 1 FROM arguments a WHERE a.relation_id = r.id
                              AND a.parent_argument_id IS NULL AND a.status != 'voorgesteld')
            ORDER BY r.id""")]

    return [
        _bevinding("ZICHTBAAR-ENT", "Voorgestelde entiteiten (onzichtbaar in de viz)", "info",
                   voorgestelde_ent,
                   "In review: de viz tekent alleen 'goedgekeurd'. Keur goed via "
                   "PATCH /api/entities/<id>/status of /overleg — dan verschijnen ze."),
        _bevinding("ZICHTBAAR-REL", "Voorgestelde relaties (onzichtbaar in de viz)", "info",
                   voorgestelde_rel,
                   "Idem: koppelingen in review verschijnen pas na goedkeuring."),
        _bevinding("ZICHTBAAR-DANGEL", "Goedgekeurde relaties met een niet-goedgekeurd eindpunt",
                   "waarschuwing", dangling,
                   "De edge is goedgekeurd maar minstens één knoop staat nog in review; "
                   "de viz kan de edge dan niet tekenen. Keur ook het eindpunt goed."),
        _bevinding("ZICHTBAAR-PRIOR", "Goedgekeurde relaties met alleen voorgestelde argumenten",
                   "info", prior_only,
                   "Zichtbaar, maar de score drijft op de prior-vloer tot de argumenten "
                   "gemerged zijn (telt-in-niets tot merge, M2.2)."),
    ]


# ── Bewijs & status (Z2) ─────────────────────────────────────

def check_bewijs(conn):
    # Alleen roots: replies zijn beleidsconform bronloos (een ondergraving vergt
    # reasoning, geen citatie — M1.1/M1.8) en dragen geen eigen bewijsplicht.
    zonder_citatie = [
        f"argument #{a['id']} ({a['stance']}): {a['claim'][:70]}"
        for a in conn.execute("""
            SELECT a.id, a.stance, a.claim FROM arguments a
            WHERE a.stance IN ('supporting', 'contradicting')
              AND a.parent_argument_id IS NULL
              AND a.status != 'voorgesteld'
              AND NOT a.vervangen
              AND NOT EXISTS (SELECT 1 FROM citations c WHERE c.argument_id = a.id)
            ORDER BY a.id
        """)]

    per_status = {r["status"]: r["n"] for r in conn.execute(
        "SELECT status, COUNT(*) AS n FROM arguments GROUP BY status")}
    achterstand = [f"{status}: {n}" for status, n in sorted(per_status.items())
                   if status != "geverifieerd"]

    totaal = sum(per_status.values())
    onbeoordeeld = totaal - per_status.get("geverifieerd", 0)
    return [
        _bevinding("BEWIJS-CITATIE", "Voor/tegen-rootargumenten zonder citatie", "fout",
                   zonder_citatie,
                   "Een supporting/contradicting-rootargument zonder bron drijft op de "
                   "ondergrens-bronfactor; de citatiepoort (M0.3) voorkomt nieuwe gevallen. "
                   "Replies tellen niet mee: een ondergraving is bewust bronloos toegestaan."),
        _bevinding("BEWIJS-STATUS", "Statusachterstand (niet-geverifieerde argumenten)", "info",
                   achterstand,
                   f"{onbeoordeeld} van {totaal} argumenten zijn niet 'geverifieerd'.",
                   aantal=onbeoordeeld),
    ]


# ── Invloed-as: schuldig tot bewezen (symmetrisch met de certainty-vloer) ──

INVLOED_VLOER = 0.05  # gelijk aan scripts/migrate_unsourced_influence.py


def check_invloed(conn):
    """Relaties met een invloed-prior bóven de vloer maar zonder invloed-bewijs.

    De invloed-as is "schuldig tot bewezen", net als de zekerheid-as: een
    `influence` boven INVLOED_VLOER is alleen eerlijk als minstens één
    niet-verworpen, niet-voorgesteld root-argument met property='influence' de
    relatie onderbouwt (M1.7). Een hand-gezette invloed zonder zulk bewijs is
    een initiële willekeurige score — precies wat het project niet wil.
    """
    rijen = [
        f"relatie #{r['id']}: {r['src']} → {r['tgt']} (influence={r['influence']})"
        for r in conn.execute(f"""
            SELECT r.id, r.influence, e1.name AS src, e2.name AS tgt
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            WHERE NOT r.vervangen AND r.influence > {INVLOED_VLOER}
              AND NOT EXISTS (
                  SELECT 1 FROM arguments a
                  WHERE a.relation_id = r.id AND a.property = 'influence'
                    AND a.parent_argument_id IS NULL
                    AND a.status NOT IN ('verworpen', 'voorgesteld'))
            ORDER BY r.id
        """)]
    return [
        _bevinding("INVLOED-PRIOR", "Relaties met invloed-prior zonder bewijs", "fout",
                   rijen,
                   f"Een influence > {INVLOED_VLOER} hoort onderbouwd te zijn met een "
                   "property='influence'-argument (M1.7); anders is het een willekeurige "
                   "prior. Floor met scripts/migrate_unsourced_influence.py of voeg bewijs toe."),
    ]


# ── Stance-balans (Z1) ───────────────────────────────────────

_BALANS_TABEL = {"relation_id": "relations", "entity_id": "entities",
                 "mechanism_id": "mechanisms", "role_id": "roles",
                 "emergent_effect_id": "emergent_effects"}


def _alleen_steun(conn, kolom, naam_sql):
    """Doelen (relatie/entiteit/mechanisme/rol/emergent veld) met wél steun maar nul tegenspraak.

    Padclaims (property='indirecte_invloed_op') tellen niet mee: dat zijn
    compositieclaims, geen onderbouwing van het doel zelf (conform scoring.py).
    Voorgestelde argumenten (M2.2) en vervangen doelen (M2.6) tellen evenmin.
    """
    rows = conn.execute(f"""
        SELECT a.{kolom} AS doel_id, {naam_sql} AS naam,
               SUM(a.stance = 'supporting') AS steun,
               SUM(a.stance = 'contradicting') AS tegen
        FROM arguments a
        WHERE a.{kolom} IS NOT NULL
          AND (a.property IS NULL OR a.property != 'indirecte_invloed_op')
          AND a.status != 'voorgesteld'
          AND NOT (SELECT vervangen FROM {_BALANS_TABEL[kolom]} WHERE id = a.{kolom})
        GROUP BY a.{kolom}
        HAVING steun > 0 AND tegen = 0
        ORDER BY steun DESC
    """).fetchall()
    return [f"#{r['doel_id']} {r['naam']} ({r['steun']}× steun, 0× tegen)" for r in rows]


def check_balans(conn):
    toelichting = ("Onweersproken is niet hetzelfde als waar: zonder overwogen tegenspraak "
                   "meet de steunratio verzamelijver (verbeterplan Z1; plafond volgt in M1.4).")
    return [
        _bevinding("BALANS-REL", "Relaties met alleen steun-argumenten", "waarschuwing",
                   _alleen_steun(conn, "relation_id",
                                 "(SELECT e1.name || ' → ' || e2.name FROM relations r "
                                 " JOIN entities e1 ON r.source_id = e1.id"
                                 " JOIN entities e2 ON r.target_id = e2.id WHERE r.id = a.relation_id)"),
                   toelichting),
        _bevinding("BALANS-ENT", "Entiteiten met alleen steun-argumenten", "waarschuwing",
                   _alleen_steun(conn, "entity_id",
                                 "(SELECT name FROM entities WHERE id = a.entity_id)"),
                   toelichting),
        _bevinding("BALANS-MECH", "Mechanismen met alleen steun-argumenten", "waarschuwing",
                   _alleen_steun(conn, "mechanism_id",
                                 "(SELECT name FROM mechanisms WHERE id = a.mechanism_id)"),
                   toelichting),
        _bevinding("BALANS-ROL", "Rollen met alleen steun-argumenten", "waarschuwing",
                   _alleen_steun(conn, "role_id",
                                 "(SELECT name FROM roles WHERE id = a.role_id)"),
                   toelichting),
        _bevinding("BALANS-VELD", "Emergente velden met alleen steun-argumenten", "waarschuwing",
                   _alleen_steun(conn, "emergent_effect_id",
                                 "(SELECT name FROM emergent_effects WHERE id = a.emergent_effect_id)"),
                   toelichting),
    ]


# ── Padclaims (afgeleide pijlen) ─────────────────────────────

def check_padclaims(conn):
    """Elke padclaim moet ≥ 1 keten van directe mechanisme-edges tussen bron- en doelrol
    hebben (eerste versie zonder drempels; later dezelfde gates als de viz).

    Sinds M2.6 verwijst property_value met het ROL-ID (hernoem-vast); routes door
    of naar vervangen elementen zijn een fout — hertriage hoort ze te verleggen."""
    edges = {}
    for m in conn.execute("""
        SELECT source_role_id AS s, target_role_id AS t FROM mechanisms
        WHERE aard = 'direct' AND source_role_id IS NOT NULL AND target_role_id IS NOT NULL
          AND NOT vervangen
    """):
        edges.setdefault(m["s"], set()).add(m["t"])

    rollen = {r["id"]: r for r in conn.execute("SELECT id, name, vervangen FROM roles")}

    def bereikbaar(van, naar):
        gezien, rand = {van}, [van]
        while rand:
            volgende = []
            for n in rand:
                for buur in edges.get(n, ()):  # directe edges, ongeacht drempels
                    if buur == naar:
                        return True
                    if buur not in gezien:
                        gezien.add(buur)
                        volgende.append(buur)
            rand = volgende
        return False

    problemen, vervangen_route = [], []
    for a in conn.execute("""
        SELECT a.id, a.property_value, a.role_id, r.name AS bronrol, r.vervangen AS bron_vervangen
        FROM arguments a JOIN roles r ON a.role_id = r.id
        WHERE a.property = 'indirecte_invloed_op' ORDER BY a.id
    """):
        doel = (a["property_value"] or "").strip()
        doel_id = int(doel) if doel.isdigit() else None
        if doel_id is None or doel_id not in rollen:
            problemen.append(f"padclaim #{a['id']}: doelrol-id '{doel}' bestaat niet "
                             f"(bronrol {a['bronrol']})")
            continue
        doelrol = rollen[doel_id]
        if a["bron_vervangen"] or doelrol["vervangen"]:
            vervangen_route.append(
                f"padclaim #{a['id']}: {a['bronrol']} → {doelrol['name']} "
                f"({'bronrol' if a['bron_vervangen'] else 'doelrol'} is vervangen)")
        elif not bereikbaar(a["role_id"], doel_id):
            problemen.append(f"padclaim #{a['id']}: geen keten van directe edges "
                             f"{a['bronrol']} → {doelrol['name']}")

    return [
        _bevinding("PADCLAIM-ROUTE", "Padclaims zonder doorlatende route", "fout", problemen,
                   "Een compositieclaim zonder keten van directe edges kan nooit als "
                   "afgeleide pijl getoond worden (doelverwijzing op rol-id, M2.6)."),
        _bevinding("PADCLAIM-VERVANGEN", "Padclaims door vervangen rollen", "fout",
                   vervangen_route,
                   "Bij splitsen/samenvoegen hoort de hertriage padclaims naar de "
                   "opvolger(s) te verleggen (M2.6); deze bleven hangen."),
    ]


# ── Bronnen (locaties, archief, linkrot) ─────────────────────

# Classificatie-integriteit (controleerbaarheid van de bron-classificatie): welke
# brontypes mogen een hoge betrouwbaarheidsklasse dragen, en welke klassen vereisen een
# vindplaats. Gedeeld door de validator (audit over de hele DB) én de classificatie-poort
# in server.py (PATCH /api/sources/<id>/classificatie), zodat de regel op één plek staat.
HOGE_KLASSEN = {"academisch", "primair", "institutioneel"}
TYPE_PER_KLASSE = {
    "academisch": {"academisch_artikel", "boek"},
    "primair": {"dataset", "wetgeving", "transcript", "interview", "persbericht", "overig"},
    "institutioneel": {"rapport", "dataset", "wetgeving", "boek", "website", "overig"},
}


def klasse_consistentie(source_type, reliability, heeft_locator) -> list:
    """Problemen met een bron-classificatie (leeg = consistent). De reliability-klasse
    stuurt de score, dus juist die moet bij het brontype passen én controleerbaar zijn."""
    problemen = []
    toegestaan = TYPE_PER_KLASSE.get(reliability)
    if toegestaan is not None and source_type not in toegestaan:
        problemen.append(f"reliability '{reliability}' past niet bij brontype "
                         f"'{source_type}' (verwacht een van: {', '.join(sorted(toegestaan))})")
    if reliability in HOGE_KLASSEN and not heeft_locator:
        problemen.append(f"klasse '{reliability}' vereist een vindplaats (locator) zodat "
                         "ze door derden te controleren is")
    return problemen


def methode_consistentie(methode, quote) -> list:
    """Problemen met de provenance-methode van een citatie (A5; leeg = consistent).

    Gedeeld tussen de create-poort (server.py) en de METHODE-CONSISTENTIE-validator.
    Een citatie die 'verbatim_quote' claimt moet een niet-lege quote dragen — anders
    is de sterkste tier (factor 1,0) een lege belofte. NULL/andere methoden zijn vrij.
    """
    problemen = []
    if methode == "verbatim_quote" and not (quote or "").strip():
        problemen.append("methode 'verbatim_quote' vereist een niet-lege quote "
                         "(de letterlijk overgenomen passage)")
    return problemen


def _archief_dekking(conn):
    """Wayback-dekking (C3): hoeveel URL-bronnen hebben een archive_url-locatie?

    Noemer = bronnen met een 'url'-locatie; teller = daarvan die óók een
    'archive_url'-locatie hebben. Gedeeld door de ARCHIEF-DEKKING-bevinding en het
    kerngetal, zodat de 3%→hoog-voortgang op één plek berekend wordt."""
    url_bronnen = conn.execute("""
        SELECT COUNT(DISTINCT s.id) FROM sources s
        JOIN source_locations l ON l.source_id = s.id AND l.location_type = 'url'
    """).fetchone()[0]
    gearchiveerd = conn.execute("""
        SELECT COUNT(DISTINCT s.id) FROM sources s
        JOIN source_locations l ON l.source_id = s.id AND l.location_type = 'url'
        WHERE EXISTS (SELECT 1 FROM source_locations a
                      WHERE a.source_id = s.id AND a.location_type = 'archive_url')
    """).fetchone()[0]
    pct = round(100 * gearchiveerd / url_bronnen, 1) if url_bronnen else None
    return {"url_bronnen": url_bronnen, "gearchiveerd": gearchiveerd, "percentage": pct}


def check_bronnen(conn, network=False):
    zonder_locatie = [
        f"bron #{s['id']}: {s['title']} ({s['source_type']})"
        for s in conn.execute("""
            SELECT s.id, s.title, s.source_type FROM sources s
            WHERE NOT EXISTS (SELECT 1 FROM source_locations l WHERE l.source_id = s.id)
            ORDER BY s.id
        """)]

    zonder_archief = [
        f"bron #{s['id']}: {s['title']}"
        for s in conn.execute("""
            SELECT DISTINCT s.id, s.title FROM sources s
            JOIN source_locations l ON l.source_id = s.id AND l.location_type = 'url'
            WHERE NOT EXISTS (SELECT 1 FROM source_locations a
                              WHERE a.source_id = s.id AND a.location_type = 'archive_url')
            ORDER BY s.id
        """)]

    inconsistent = []
    for s in conn.execute("""
            SELECT s.id, s.title, s.source_type, s.reliability,
                   EXISTS(SELECT 1 FROM source_locations l WHERE l.source_id = s.id) AS heeft_loc
            FROM sources s ORDER BY s.id"""):
        for prob in klasse_consistentie(s["source_type"], s["reliability"], s["heeft_loc"]):
            inconsistent.append(f"bron #{s['id']} ({s['title']}): {prob}")

    dekking = _archief_dekking(conn)
    bevindingen = [
        _bevinding("BRON-LOCATIE", "Bronnen zonder vindplaats (source_locations)",
                   "waarschuwing", zonder_locatie,
                   "Zonder locatie is een bron niet door derden te controleren."),
        _bevinding("BRON-ARCHIEF", "URL-bronnen zonder archive_url", "waarschuwing",
                   zonder_archief,
                   "Webpagina's verdwijnen; een Wayback-snapshot houdt het bewijs controleerbaar."),
        _bevinding("ARCHIEF-DEKKING", "Wayback-archiveringsgraad van URL-bronnen", "info",
                   [f"{dekking['gearchiveerd']} van {dekking['url_bronnen']} URL-bronnen "
                    f"gearchiveerd = {dekking['percentage']}%"] if dekking["url_bronnen"] else [],
                   "Aandeel URL-bronnen mét een archive_url-locatie (Wayback). C3 tilt dit "
                   "van ~3% richting hoog: A1-herverificatie en de 'linkrot-vrij'-claim "
                   "vereisen een onveranderlijke kopie. Draai scripts/archiveer_bronnen.py --save.",
                   aantal=dekking["url_bronnen"] - dekking["gearchiveerd"]),
        _bevinding("BRON-KLASSE", "Bron-classificaties die niet bij het brontype passen "
                   "of een vindplaats missen", "waarschuwing", inconsistent,
                   "De reliability-klasse stuurt de score; ze hoort bij het brontype te "
                   "passen en (voor hoge klassen) door een vindplaats controleerbaar te zijn."),
    ]

    if network:
        import urllib.error
        import urllib.request
        kapot = []
        urls = conn.execute("""
            SELECT l.location, s.title FROM source_locations l
            JOIN sources s ON l.source_id = s.id
            WHERE l.location_type IN ('url', 'archive_url')
            ORDER BY l.id
        """).fetchall()
        for row in urls:
            url = row["location"]
            try:
                req = urllib.request.Request(url, method="HEAD",
                                             headers={"User-Agent": "propaganda-model-validator"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status >= 400:
                        kapot.append(f"{resp.status} {url} ({row['title']})")
            except Exception as exc:  # noqa: BLE001 — elke netwerkfout is een bevinding
                kapot.append(f"{type(exc).__name__} {url} ({row['title']})")
        bevindingen.append(_bevinding(
            "BRON-LINKROT", "Onbereikbare bron-URLs", "waarschuwing", kapot,
            f"{len(urls)} URLs geprobeerd (HEAD). Sommige servers weigeren HEAD: "
            "controleer een bevinding handmatig vóór je de bron afschrijft."))

    return bevindingen


# ── Neutraliteit / smaad-productregel (J3) ───────────────────

# Negatief-geladen, potentieel-beschuldigende woorden (Nederlands). De lijst hoeft
# niet uitputtend te zijn: de check is adviserend en mag ruim vlaggen.
NEUTRALITEIT_NEGATIEF = {
    "corrupt", "corruptie", "corrupte", "fraude", "frauduleus", "fraudeert",
    "oplichting", "oplichter", "oplichten", "omkoping", "omgekocht", "omkopen",
    "chantage", "afpersing", "witwas", "witwassen", "witwaste",
    "crimineel", "criminele", "misdaad", "misdadig", "strafbaar",
    "liegt", "loog", "leugen", "leugens", "leugenaar", "gelogen",
    "bedrog", "bedriegt", "bedroog", "misleiding", "misleidt", "misleidde",
    "belangenverstrengeling", "machtsmisbruik", "misbruik", "wanbeleid",
    "verzweeg", "verzwijgt", "verzwegen", "doofpot", "samenzwering", "samenspanning",
    "schuldig", "medeplichtig", "laakbaar", "onethisch", "immoreel",
    "manipuleert", "manipulatie", "manipuleerde", "intimideert", "intimidatie",
    "dubieus", "dubieuze", "malversatie", "malversaties", "verduistering",
    "nepotisme", "vriendjespolitiek", "graaien", "graaier", "zelfverrijking",
}

# In-zin-attributiesignalen: is een bron/spreker in dezelfde zin genoemd, dan is
# het een geattribueerde (dus toegestane) claim, geen eigen-stem-beschuldiging.
NEUTRALITEIT_ATTRIBUTIE = (
    "volgens", "aldus", "volgens eigen", "naar eigen zeggen",
    "zei", "zegt", "zeggen", "stelt", "stelde", "beweert", "beweerde",
    "schreef", "schrijft", "verklaarde", "verklaart", "oordeelde", "oordeelt",
    "concludeert", "concludeerde", "rapporteert", "rapporteerde", "meldt", "meldde",
    "betoogt", "betoogde", "noemde", "noemt", "citeert", "citeerde",
    "volgens het", "volgens de", "according to",
)
# Aanhalingstekens/dubbele punt duiden op een citaat → geattribueerd genoeg.
_CITAAT_TEKENS = ('"', "'", "«", "»", "„", "“", "”", "‘", "’", "„", "″")

_ZIN_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _bevat_attributie(zin_lower: str) -> bool:
    if any(t in zin_lower for t in _CITAAT_TEKENS):
        return True
    for sig in NEUTRALITEIT_ATTRIBUTIE:
        # woordgrens zodat 'meldt' niet in 'gemeld...' fout matcht is niet nodig;
        # een ruime attributie-match onderdrukt juist (veilige kant: minder vlaggen).
        if sig in zin_lower:
            return True
    return False


def check_neutraliteit(conn):
    """NEUTRALITEIT-RENDER (J3): adviserende smaad-/neutraliteitscontrole.

    Heuristiek (bewust ruim, adviserend — nooit een geratchete 'fout', zodat
    `validate_model.py --strict` groen blijft): scant de eigen-stem-tekst van het
    model — `arguments.claim`, `arguments.reasoning`, `relations.description`,
    `entities.description` — plus, indien aanwezig, gegenereerde prose in
    `data/prose/*.txt` (B5, nog niet gebouwd). Per *zin* vlagt ze een passage die
    (1) de naam van een `type='persoon'`-entiteit noemt, én (2) een negatief-geladen
    woord (NEUTRALITEIT_NEGATIEF) bevat, én (3) géén in-zin bron-attributie draagt
    (NEUTRALITEIT_ATTRIBUTIE / aanhalingstekens). Zo'n passage is een kandidaat-
    *beschuldiging in de eigen stem van het model* over een genoemd natuurlijk
    persoon — precies wat smaad-/onrechtmatige-daad-risico geeft (plan §Juridisch).

    Bewust een paar false-positives boven een gemiste beschuldiging: het is een
    toezichtsignaal (waarschuwing), geen poort. Een correct geattribueerde zin
    ("volgens de NOS …", of een citaat) wordt niet gevlagd; een kale conclusie in
    de eigen stem wél. Personen worden op hun volledige opgeslagen naam gematcht
    (woordgrens), wat losse achternamen/gewone woorden buiten schot houdt.
    """
    personen = [r["name"] for r in conn.execute(
        "SELECT name FROM entities WHERE type = 'persoon' AND NOT vervangen")]
    if not personen:
        return [_bevinding("NEUTRALITEIT-RENDER",
                           "Ongeattribueerde negatieve persoons-claims in de eigen stem",
                           "waarschuwing", [], _NEUTRALITEIT_TOELICHTING)]

    # Eén alternatie-regex over alle persoonsnamen (langste eerst), met woordgrenzen.
    naam_regex = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(n) for n in sorted(personen, key=len, reverse=True))
        + r")(?!\w)")

    def scan(bron_label, tekst):
        treffers = []
        if not tekst:
            return treffers
        for zin in _ZIN_SPLIT.split(tekst):
            zin_l = zin.lower()
            if not any(w in zin_l for w in NEUTRALITEIT_NEGATIEF):
                continue
            m = naam_regex.search(zin)
            if not m:
                continue
            if _bevat_attributie(zin_l):
                continue
            snip = zin.strip()
            treffers.append(f"{bron_label} — '{m.group(1)}': {snip[:110]}")
        return treffers

    gevlagd = []
    for a in conn.execute("""
            SELECT id, claim, reasoning FROM arguments
            WHERE NOT vervangen AND status != 'verworpen'"""):
        gevlagd += scan(f"argument #{a['id']}", a["claim"])
        gevlagd += scan(f"argument #{a['id']} (reasoning)", a["reasoning"])
    for r in conn.execute(
            "SELECT id, description FROM relations WHERE NOT vervangen"):
        gevlagd += scan(f"relatie #{r['id']}", r["description"])
    for e in conn.execute(
            "SELECT id, name, description FROM entities WHERE NOT vervangen"):
        gevlagd += scan(f"entiteit #{e['id']} ({e['name']})", e["description"])

    # Optioneel: gegenereerde prose (B5). Bestaat nog niet; scan als het er komt.
    prose_dir = Path(__file__).parent / "data" / "prose"
    if prose_dir.is_dir():
        for pad in sorted(prose_dir.glob("*.txt")):
            try:
                gevlagd += scan(f"prose {pad.name}", pad.read_text(encoding="utf-8"))
            except OSError:
                pass

    return [_bevinding("NEUTRALITEIT-RENDER",
                       "Ongeattribueerde negatieve persoons-claims in de eigen stem",
                       "waarschuwing", gevlagd, _NEUTRALITEIT_TOELICHTING)]


_NEUTRALITEIT_TOELICHTING = (
    "Adviserende smaad-/neutraliteitscontrole (J3): een zin die een genoemd "
    "natuurlijk persoon aan negatief-geladen taal koppelt zonder bron-attributie "
    "in dezelfde zin. Het model spreekt in zijn eigen stem alleen gesourcete feiten "
    "en geattribueerde meningen — nooit een eigen beschuldiging. Ruim bedoeld "
    "(mogelijk false-positives); herformuleer met bron/attributie of controleer.")


# ── Eigen stem (stemtoets, eigenaarsbesluit 2026-10-08) ───────
# "'ondermijnt zo het vertrouwen in de journalistiek' … deze taal moeten we niet overnemen, dit
# is duidelijk een politiek spelletje … waak hier streng voor." De eigen stem van het model zegt
# wat er gebeurde (wie deed of zei wat, wanneer); een oordeel over gevolgen of motieven, een
# etiket of de retoriek van één kant staat er alleen als citaat, met naam toegeschreven. Het
# oordeel per tekst geeft de stemtoets (scripts/stemtoets.py, een taalmodel); dit lexicon is
# de deterministische ondergrens: STRENG zijn uitdrukkingen die buiten een citaat of
# toeschrijving altijd een oordeel of etiket zijn (de geratchete fout NEUTRALITEIT-EIGEN-STEM),
# RUIM wijst de stemtoets aan waar ze eerst moet kijken (ook woorden die soms feitelijk zijn).
EIGEN_STEM_STRENG = (
    (r"ondermijn\w*\s+(?:zo\s+|daarmee\s+|daardoor\s+|zij\s+|hij\s+)?(?:het\s+|de\s+)?"
     r"(?:publieke\s+)?vertrouwen", "ondermijnt het vertrouwen"),
    (r"\bvertrouwen\s+(?:in|van)\s+[^.:;]{0,60}?\bte\s+ondermijnen", "vertrouwen … te ondermijnen"),
    (r"\bbedreiging\s+(?:voor|van)\s+(?:de\s+|het\s+)?(?:onafhankelijke\s+|vrije\s+)?"
     r"(?:journalisti\w*|democratie|persvrijheid|rechtsstaat|pers|media|nieuwsvoorziening)",
     "bedreiging voor de journalistiek/democratie"),
    (r"\bdirecte\s+bedreiging", "directe bedreiging"),
    (r"\b(?:rechts|links)[- ]?populist\w*|\bpopulistisch\w*|\bpopulisten\b", "populistisch"),
    (r"\bneoliberale\s+(?:consensus|hegemonie)", "neoliberale consensus"),
    (r"\blinkse\s+(?:kerk|media|pers|elite)|\brechtse\s+(?:media|pers)", "linkse/rechtse media"),
    (r"\bmainstream[- ]?media\b|\bmainstreammedia\b", "mainstream media"),
)
EIGEN_STEM_RUIM = EIGEN_STEM_STRENG + (
    (r"\bondermijn\w*", "ondermijnt"),
    (r"\bbedreig\w*", "bedreigt"),
    (r"\bextreem[- ]?(?:rechts|links)\w*|\bradicaal[- ]?(?:rechts|links)\w*"
     r"|\buiterst[- ](?:rechts|links)\w*", "extreem/radicaal rechts of links"),
    (r"\bnepnieuws\b|\bpropaganda\b|\bcomplot\w*|\bwappie\w*|\bhetze\b", "nepnieuws/propaganda"),
    (r"\bnarratie\w*", "narratief"),
    (r"\w+-gezind\w*", "-gezind"),
    (r"\bschadelijk\w*|\bgevaarlijk\w*", "schadelijk/gevaarlijk"),
    (r"\bpolaris\w*", "polariseert"),
    (r"\bdesinformatie\w*|\bmanipul\w*|\bmisleid\w*", "desinformatie/misleiding"),
    (r"\bintimid\w*", "intimideert"),
    (r"\bkernpositie|\bzeer\s+invloedrijk\w*|\bmachtig\w*|\bberucht\w*|\bomstreden"
     r"|\bkritiekloos\w*", "versterker"),
    (r"\belite\b|\bconsensus\b|\bhegemon\w*|\bideologisch\w*|\bestablishment\b",
     "analysewoord als etiket"),
    (r"\bactivist\w*|\bradica\w*|\bextreem\w*|\blinkse\b|\brechtse\b", "etiket"),
)
_EIGEN_STEM_STRENG_RE = [(re.compile(p, re.IGNORECASE), label) for p, label in EIGEN_STEM_STRENG]
_EIGEN_STEM_RUIM_RE = [(re.compile(p, re.IGNORECASE), label) for p, label in EIGEN_STEM_RUIM]
# Citaten (dubbele, enkele en typografische aanhalingstekens): wat erbinnen staat, is van een ander
_CITAAT_SPAN = re.compile(r"\"[^\"]{1,400}\"|“[^”]{1,400}”|„[^“”]{1,400}[“”]|«[^»]{1,400}»"
                          r"|‘[^’]{1,400}’|(?<!\w)'[^']{1,400}'(?!\w)")
# Een zinsdeel dat een oordeel aan iemand toeschrijft ("volgens de NVJ …", "X noemde …")
_TOESCHRIJVING = re.compile(
    r"\b(?:volgens|aldus|naar eigen zeggen|zei|zegt|zeggen|stelt|stelde|stellen|beweert|"
    r"beweerde|schreef|schrijft|verklaarde|verklaart|oordeelde|oordeelt|concludeert|"
    r"concludeerde|noemde|noemt|noemen|betoogt|betoogde|waarschuwde|waarschuwt|vindt|vond|"
    r"bekritiseerde|bekritiseert|aangemerkt|aanmerkt|merkte|bestempel\w*|beschuldig\w*|"
    r"framet|framede|framen|geframed|etiketteer\w*|omschrijft|omschreef|omschreven|typeer\w*|"
    r"kwalificeer\w*|identificeert|profileert|geprofileerd|positioneert|zelfverklaard\w*|"
    r"according to)\b", re.IGNORECASE)
_ZINSDEEL_SPLIT = re.compile(r"(?<=[.!?:;])\s+|\s+[—–]\s+")


def eigen_stem_treffers(tekst, streng=True):
    """Welke oordelen of etiketten staan er in de EIGEN STEM van deze tekst: buiten citaten en
    in een zinsdeel dat ze niet aan iemand toeschrijft? → lijst van labels (leeg = niets).
    ``streng=False`` gebruikt het ruime lexicon (alleen om de stemtoets te laten voorgaan)."""
    patronen = _EIGEN_STEM_STRENG_RE if streng else _EIGEN_STEM_RUIM_RE
    gevonden = []
    for deel in _ZINSDEEL_SPLIT.split(tekst or ""):
        kaal = _CITAAT_SPAN.sub(" ", deel)
        if _TOESCHRIJVING.search(kaal):
            continue
        for regex, label in patronen:
            if regex.search(kaal) and label not in gevonden:
                gevonden.append(label)
    return gevonden


def check_eigen_stem(conn):
    """NEUTRALITEIT-EIGEN-STEM (fout, geratchet; eigenaarsbesluit 2026-10-08): teksten van het
    levende model — gemergede argument-claims in de praktijklaag en de beschrijvingen van
    goedgekeurde relaties en entiteiten — met een oordeel of etiket uit het STRENGE lexicon in
    de eigen stem (niet in een citaat, niet toegeschreven). De stemtoets herschrijft de
    bestaande; de ratchet (validatie_baseline.json) houdt nieuwe buiten."""
    gevlagd = []
    for a in conn.execute("""
            SELECT id, claim FROM arguments
            WHERE NOT vervangen AND (relation_id IS NOT NULL OR entity_id IS NOT NULL)
              AND status IN ('ongecontroleerd', 'geverifieerd', 'betwist', 'bronvermelding_nodig')"""):
        treffers = eigen_stem_treffers(a["claim"])
        if treffers:
            gevlagd.append(f"argument #{a['id']} ({', '.join(treffers)}): {(a['claim'] or '')[:110]}")
    for tabel, label in (("relations", "relatie"), ("entities", "entiteit")):
        for r in conn.execute(f"""SELECT id, description FROM {tabel}
                                  WHERE NOT vervangen AND status = 'goedgekeurd'
                                    AND description IS NOT NULL"""):  # noqa: S608 - vaste tabel
            treffers = eigen_stem_treffers(r["description"])
            if treffers:
                gevlagd.append(f"{label} #{r['id']} ({', '.join(treffers)}): "
                               f"{(r['description'] or '')[:110]}")
    return [_bevinding(
        "NEUTRALITEIT-EIGEN-STEM", "Oordelen of etiketten in de eigen stem van het model",
        "fout", gevlagd,
        "De eigen stem zegt wat er gebeurde (wie deed of zei wat, wanneer); een oordeel over "
        "gevolgen of motieven ('ondermijnt het vertrouwen'), een etiket ('rechts-populistisch', "
        "'neoliberale consensus') of de retoriek van één kant alleen als citaat, met naam "
        "toegeschreven (eigenaarsbesluit 2026-10-08). De stemtoets (scripts/stemtoets.py) "
        "herschrijft wat er staat; deze geratchete fout houdt nieuwe buiten.")]


def check_looptijd(conn):
    """RELATIE-ZONDER-JAAR (fout, geratchet; eigenaarsbesluit 2026-10-09: "vul bij alles de
    goede jaartallen in … het model kijkt per tijdsvak wat de relaties zijn"): goedgekeurde
    verbanden zonder begin (active_from) waarvoor niemand aantoonbaar zocht. Een verband mag
    alleen zonder begin blijven als de datumzoeker niets vond ('niets_gevonden') of het register
    zelf geen begin noemt ('register_zonder_datum'); beide staan in looptijd_onderzoek. De
    datumzoeker werkt de rest af; de ratchet houdt nieuwe buiten (en de goedkeurpoort
    looptijd_reden in server.py laat ze niet meer toe)."""
    try:
        conn.execute("SELECT 1 FROM looptijd_onderzoek LIMIT 1")
        uitgezocht = ("AND NOT EXISTS (SELECT 1 FROM looptijd_onderzoek o WHERE o.relation_id = r.id "
                      "AND o.status IN ('niets_gevonden', 'register_zonder_datum'))")
    except sqlite3.OperationalError:
        uitgezocht = ""
    rijen = conn.execute(f"""
        SELECT r.id, s.name AS bron, r.relation_type, t.name AS doel FROM relations r
        JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
        WHERE r.status = 'goedgekeurd' AND NOT r.vervangen
          AND TRIM(COALESCE(r.active_from, '')) = '' {uitgezocht}
        ORDER BY r.id""").fetchall()  # noqa: S608 - vaste SQL
    return [_bevinding(
        "RELATIE-ZONDER-JAAR", "Goedgekeurde verbanden zonder begin (en zonder vastgelegde zoektocht)",
        "fout", [f"relatie #{r['id']}: {r['bron']} — {r['relation_type']} — {r['doel']}" for r in rijen],
        "Elk verband draagt zijn looptijd: begin (active_from) en, als het voorbij is, einde "
        "(active_until), zo precies als de bron geeft. De datumzoeker (scripts/datumzoeker.py) "
        "zoekt wat ontbreekt; registerfeiten krijgen hun datum uit het record "
        "(scripts/registers_looptijd.py). Zonder jaartal blijft alleen wat aantoonbaar is "
        "uitgezocht (looptijd_onderzoek).")]


def check_bestaan(conn):
    """Eigenaarsbesluit 2026-10-13 ("zorg goed dat alle tijdsintervallen worden gehandhaafd"): een
    verband loopt nooit buiten het bestaan van zijn eindpunten (looptijd.py).

    LOOPTIJD-BUITEN-BESTAAN (fout, geratchet): een goedgekeurd verband met een eigen datum buiten
    het bestaan van een organisatie, met een begin na het einde, of met een datum die geen datum
    is. Een open grens is geen fout, want de effectieve looptijd kapt die al af. Nieuwe gevallen
    houdt de goedkeurpoort tegen (server.bestaan_reden). Wat er nog staat is meestal een
    ontbrekende voorganger: een VARA-band op BNNVARA, een NTS-band op de NOS.
    OPVOLGING-ONGELDIG (fout): een gemergede fusie ('opgegaan_in') naar iets dat geen
    goedgekeurde organisatie is, een kring, of een opvolger die pas na de opheffing ontstond.
    OPVOLGING-ZONDER-EINDE (waarschuwing): een organisatie met een opvolger maar zonder einddatum
    begrenst haar banden nog niet.
    PERSOON-LOOPTIJD (waarschuwing): een persoon wiens active_from/active_until een functieperiode
    lijkt in plaats van zijn leven, omdat eigen verbanden erbuiten vallen. Daarom begrenzen
    personen (nog) niet."""
    import looptijd   # repo-root, stdlib (lazy zoals de rest van deze checks)

    ents = {r["id"]: dict(r) for r in conn.execute(
        "SELECT id, name, type, active_from, active_until FROM entities "
        "WHERE status = 'goedgekeurd' AND NOT vervangen")}
    opv = looptijd.opvolgingen(conn)
    opv_ids = {k: [x["opvolger"] for x in v] for k, v in opv.items()}
    namen = {i: e["name"] for i, e in ents.items()}
    buiten, persoon = [], {}
    for r in conn.execute("""SELECT id, source_id, target_id, relation_type, active_from, active_until
                             FROM relations WHERE status = 'goedgekeurd' AND NOT vervangen
                             ORDER BY id"""):
        b, d = ents.get(r["source_id"]), ents.get(r["target_id"])
        if b is None or d is None:
            continue
        rel = dict(r)
        redenen = looptijd.conflicten(rel, b, d, opv_ids, namen)
        if redenen:
            buiten.append(f"relatie #{r['id']}: {b['name']} — {r['relation_type']} — {d['name']}: "
                          + "; ".join(redenen))
        van, tot = rel["active_from"], rel["active_until"]
        for p in (b, d):
            p_van, p_tot = p["active_from"], p["active_until"]
            if p["type"] != "persoon" or not (p_van or p_tot):
                continue
            if (looptijd.voor(van or tot, p_van) or looptijd.voor(tot, p_van)
                    or looptijd.voor(p_tot, van or tot) or looptijd.voor(p_tot, tot)):
                persoon.setdefault(p["id"], []).append(r["id"])

    ongeldig, zonder_einde = [], []
    for vg, lijst in opv.items():
        e = ents.get(vg)
        for x in lijst:
            o = ents.get(x["opvolger"])
            naam = f"argument #{x['argument_id']}: {namen.get(vg, f'#{vg}')} → {namen.get(x['opvolger'], '#' + str(x['opvolger']))}"
            if e is None or o is None:
                ongeldig.append(f"{naam}: geen goedgekeurde entiteit")
            elif "persoon" in (e["type"], o["type"]):
                ongeldig.append(f"{naam}: een persoon gaat nergens in op")
            elif looptijd.kring({k: v for k, v in opv.items() if k != vg}, vg, x["opvolger"]):
                ongeldig.append(f"{naam}: kring")
            elif o["active_from"] and e["active_until"] and looptijd.voor(e["active_until"], o["active_from"]):
                ongeldig.append(f"{naam}: de opvolger ontstond ({o['active_from']}) na de opheffing "
                                f"({e['active_until']})")
        if e is not None and not e["active_until"]:
            zonder_einde.append(f"entiteit #{vg} {e['name']}: opgegaan in "
                                + ", ".join(namen.get(x["opvolger"], "?") for x in lijst)
                                + ", maar zonder einddatum")
    # Is het bestaan ingevuld? Organisaties met een goedgekeurd verband maar zonder oprichting
    # (de datumzoeker zoekt ze op; wat hij vergeefs zocht staat in data/datumzoeker_organisaties.json)
    try:
        import json as _json
        stand = _json.loads((Path(__file__).parent / "data" / "datumzoeker_organisaties.json")
                            .read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stand = {}
    zonder_bestaan = [
        f"entiteit #{r['id']} {r['name']} ({r['type']}, {r['n']} verbanden)"
        for r in conn.execute("""
            SELECT e.id, e.name, e.type, COUNT(*) AS n FROM entities e
            JOIN relations r ON (r.source_id = e.id OR r.target_id = e.id)
                             AND r.status = 'goedgekeurd' AND NOT r.vervangen
            WHERE e.status = 'goedgekeurd' AND NOT e.vervangen AND e.type <> 'persoon'
              AND TRIM(COALESCE(e.active_from, '')) = ''
            GROUP BY e.id ORDER BY n DESC, e.id""")
        if (stand.get(str(r["id"])) or {}).get("status") != "niets_gevonden"]
    return [
        _bevinding(
            "ORGANISATIE-ZONDER-BESTAAN", "Organisaties met verbanden maar zonder oprichtingsdatum",
            "waarschuwing", zonder_bestaan,
            "Zonder begin begrenst het bestaan van een organisatie haar verbanden niet. De "
            "datumzoeker zoekt het op (--max-web-org per ronde), het overheidsregister geeft het "
            "voor overheidsorganisaties (scripts/registers_looptijd.py); wat vergeefs gezocht is, "
            "telt niet mee."),
        _bevinding(
            "LOOPTIJD-BUITEN-BESTAAN", "Verbanden met een datum buiten het bestaan van een eindpunt",
            "fout", buiten,
            "Een verband loopt nooit buiten het bestaan van zijn eindpunten (looptijd.py). Koppel "
            "een band van vóór een fusie aan de voorganger (met 'opgegaan_in' naar de opvolger), "
            "een band van ná een opheffing aan de opvolger, of corrigeer de datum van het verband "
            "of van de organisatie."),
        _bevinding(
            "OPVOLGING-ONGELDIG", "Fusies ('opgegaan_in') die niet kunnen", "fout", ongeldig,
            "Een opvolger is een goedgekeurde organisatie die al bestond toen de voorganger ophield, "
            "zonder kring."),
        _bevinding(
            "OPVOLGING-ZONDER-EINDE", "Opgeheven organisaties zonder einddatum", "waarschuwing",
            zonder_einde,
            "Zonder active_until begrenst de opheffing haar banden nog niet: dien een "
            "active_until-argument in (stap 10c zet het)."),
        _bevinding(
            "PERSOON-LOOPTIJD", "Personen met een functieperiode als looptijd", "waarschuwing",
            [f"persoon #{pid} {namen.get(pid)} ({ents[pid]['active_from'] or '…'}–"
             f"{ents[pid]['active_until'] or ''}): eigen verbanden erbuiten "
             f"({', '.join('#' + str(x) for x in rids[:5])}{'…' if len(rids) > 5 else ''})"
             for pid, rids in sorted(persoon.items())],
            "De looptijd van een persoon is zijn leven, geen functie: die hoort op het verband. "
            "Zolang dit gemengd is, begrenzen personen hun verbanden niet en verbergt de tijdbalk "
            "ze buiten die periode."),
    ]


# ── Schema-pariteit (Z9) ─────────────────────────────────────

def _strip_sql_commentaar(sql):
    return re.sub(r"--[^\n]*", "", sql)


def _normaliseer_ddl(sql):
    sql = _strip_sql_commentaar(sql or "")
    sql = re.sub(r"\bIF NOT EXISTS\b", "", sql, flags=re.I)
    sql = sql.replace('"', "")
    sql = " ".join(sql.split()).lower()
    return re.sub(r"\s*([(),])\s*", r"\1", sql)  # komma-/haakjesspaties zijn geen drift


def _tabel_kolommen(conn, tabel):
    kolommen = {}
    for c in conn.execute(f"PRAGMA table_info({tabel})"):
        dflt = c["dflt_value"]
        kolommen[c["name"]] = (
            " ".join((c["type"] or "").upper().split()),
            c["notnull"],
            " ".join(str(dflt).split()) if dflt is not None else None,
            c["pk"],
        )
    return kolommen


def _tabel_fks(conn, tabel):
    return {(fk["from"], fk["table"], fk["to"] or "", (fk["on_delete"] or "NO ACTION").upper())
            for fk in conn.execute(f"PRAGMA foreign_key_list({tabel})")}


def check_schema_pariteit(conn, schema_path=SCHEMA_PATH):
    """Bouw een verse DB in-memory uit schema.sql en vergelijk de structuur met live.

    Streng (fout): tabellen, kolommen (naam/type/notnull/default/pk), foreign keys,
    indexnamen. Informatief: genormaliseerde DDL-tekst (vangt CHECK-verschillen;
    bekende intentionele verschillen staan in BEKENDE_DDL_VERSCHILLEN).
    """
    vers = sqlite3.connect(":memory:")
    vers.row_factory = sqlite3.Row
    vers.executescript(Path(schema_path).read_text())

    def tabellen(c):
        return {r["name"]: r["sql"] for r in c.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")}

    live_tab, vers_tab = tabellen(conn), tabellen(vers)
    tabel_diff = ([f"alleen live: {t}" for t in sorted(set(live_tab) - set(vers_tab))]
                  + [f"alleen schema.sql: {t}" for t in sorted(set(vers_tab) - set(live_tab))])

    kolom_diff, fk_diff, ddl_info = [], [], []
    for tabel in sorted(set(live_tab) & set(vers_tab)):
        lk, vk = _tabel_kolommen(conn, tabel), _tabel_kolommen(vers, tabel)
        for naam in sorted(set(lk) | set(vk)):
            if naam not in vk:
                kolom_diff.append(f"{tabel}.{naam}: alleen live")
            elif naam not in lk:
                kolom_diff.append(f"{tabel}.{naam}: alleen schema.sql")
            elif lk[naam] != vk[naam]:
                kolom_diff.append(f"{tabel}.{naam}: live {lk[naam]} vs schema.sql {vk[naam]}")

        lf, vf = _tabel_fks(conn, tabel), _tabel_fks(vers, tabel)
        for fk in sorted(lf - vf):
            fk_diff.append(f"{tabel}: FK {fk} alleen live")
        for fk in sorted(vf - lf):
            fk_diff.append(f"{tabel}: FK {fk} alleen schema.sql")

        if _normaliseer_ddl(live_tab[tabel]) != _normaliseer_ddl(vers_tab[tabel]):
            reden = BEKENDE_DDL_VERSCHILLEN.get(tabel, "onderzoeken")
            ddl_info.append(f"{tabel}: DDL-tekst wijkt af ({reden})")

    def indexen(c):
        return {r["name"] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'")}

    li, vi = indexen(conn), indexen(vers)
    index_diff = ([f"alleen live: {i}" for i in sorted(li - vi)]
                  + [f"alleen schema.sql: {i}" for i in sorted(vi - li)])

    vers.close()
    return [
        _bevinding("SCHEMA-TABELLEN", "Tabellen ongelijk tussen live DB en schema.sql",
                   "fout", tabel_diff),
        _bevinding("SCHEMA-KOLOMMEN", "Kolomverschillen (naam/type/notnull/default/pk)",
                   "fout", kolom_diff),
        _bevinding("SCHEMA-FK", "Foreign-key-verschillen", "fout", fk_diff),
        _bevinding("SCHEMA-INDEX", "Indexverschillen", "fout", index_diff),
        _bevinding("SCHEMA-DDL", "DDL-tekstverschillen (CHECKs, commentaar)", "info", ddl_info,
                   "Kolompariteit is leidend; dit vangt CHECK-drift die PRAGMA niet ziet."),
    ]


# ── Kerngetallen (gezondheidsfoto, verbeterplan §1) ──────────

def kerngetallen(conn):
    een = lambda sql: conn.execute(sql).fetchone()[0]  # noqa: E731
    tabellen = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}

    stance = {r["stance"]: r["n"] for r in conn.execute(
        "SELECT stance, COUNT(*) AS n FROM arguments GROUP BY stance")}
    status = {r["status"]: r["n"] for r in conn.execute(
        "SELECT status, COUNT(*) AS n FROM arguments GROUP BY status")}

    top3 = [{"titel": r["title"], "citaties": r["n"]} for r in conn.execute("""
        SELECT s.title, COUNT(*) AS n FROM citations c
        JOIN sources s ON c.source_id = s.id
        GROUP BY c.source_id ORDER BY n DESC LIMIT 3
    """)]
    citaties_totaal = een("SELECT COUNT(*) FROM citations")

    arg_kolommen = {c["name"] for c in conn.execute("PRAGMA table_info(arguments)")}
    hyperedges_met_bewijs = 0
    if "emergent_effect_id" in arg_kolommen:  # komt pas met M1.5
        hyperedges_met_bewijs = een(
            "SELECT COUNT(DISTINCT emergent_effect_id) FROM arguments WHERE emergent_effect_id IS NOT NULL")

    return {
        "entiteiten": een("SELECT COUNT(*) FROM entities"),
        "relaties": een("SELECT COUNT(*) FROM relations"),
        "argumenten": een("SELECT COUNT(*) FROM arguments"),
        "bronnen": een("SELECT COUNT(*) FROM sources"),
        "citaties": citaties_totaal,
        "replies": een("SELECT COUNT(*) FROM arguments WHERE parent_argument_id IS NOT NULL"),
        "stance": stance,
        "status": status,
        "voor_tegen_zonder_citatie": een("""
            SELECT COUNT(*) FROM arguments a
            WHERE a.stance IN ('supporting', 'contradicting')
              AND a.parent_argument_id IS NULL
              AND NOT a.vervangen
              AND NOT EXISTS (SELECT 1 FROM citations c WHERE c.argument_id = a.id)"""),
        "relaties_zonder_argumenten": een("""
            SELECT COUNT(*) FROM relations r
            WHERE NOT EXISTS (SELECT 1 FROM arguments a WHERE a.relation_id = r.id)"""),
        "relaties_zonder_mechanisme": een(
            "SELECT COUNT(*) FROM relations WHERE mechanism_id IS NULL"),
        # Bottom-up: kandidaten (voorgesteld, incuberen — toegestaan) vs. de echte
        # overtreding (een goedgekeurde orphan).
        "kandidaat_relaties": een(
            "SELECT COUNT(*) FROM relations WHERE mechanism_id IS NULL "
            "AND status = 'voorgesteld' AND NOT vervangen"),
        "goedgekeurde_orphans": een(
            "SELECT COUNT(*) FROM relations WHERE mechanism_id IS NULL "
            "AND status = 'goedgekeurd' AND NOT vervangen"),
        "relaties_met_mech_zonder_instantiatie": een("""
            SELECT COUNT(*) FROM relations r
            WHERE r.mechanism_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM instantiations i
                              WHERE i.relation_id = r.id AND i.mechanism_id = r.mechanism_id)"""),
        "entiteiten_zonder_rol": een("""
            SELECT COUNT(*) FROM entities e
            WHERE e.primary_role_id IS NULL
              AND NOT EXISTS (SELECT 1 FROM entity_roles er WHERE er.entity_id = e.id)"""),
        "entiteiten_zonder_instantiatie": een("""
            SELECT COUNT(*) FROM entities e
            WHERE NOT EXISTS (SELECT 1 FROM instantiations i WHERE i.entity_id = e.id)"""),
        "hyperedges": een("SELECT COUNT(*) FROM emergent_effects"),
        "hyperedges_met_bewijslijn": hyperedges_met_bewijs,
        "hyperedges_met_compositieclaim": (een("""
            SELECT COUNT(DISTINCT emergent_effect_id) FROM arguments
            WHERE emergent_effect_id IS NOT NULL AND property = 'compositie'""")
            if "emergent_effect_id" in arg_kolommen else 0),
        "bronclusters": een(
            "SELECT COUNT(DISTINCT COALESCE(cluster_key, 'bron' || id)) FROM sources"),
        # Wayback-dekking (C3): 3% → hoog zichtbaar in de gezondheidsfoto.
        "archief_dekking": _archief_dekking(conn),
        "citatie_concentratie_top3": top3,
        "citatie_concentratie_aandeel": (
            round(sum(t["citaties"] for t in top3) / citaties_totaal, 3) if citaties_totaal else None),
        # Fase 2 (M2.2–M2.6): review-wachtrij, ratings en opvolging
        "voorgestelde_argumenten": status.get("voorgesteld", 0),
        "open_voorstellen": (een("SELECT COUNT(*) FROM voorstellen WHERE status = 'open'")
                             if "voorstellen" in tabellen else 0),
        "ratings": een("SELECT COUNT(*) FROM argument_ratings") if "argument_ratings" in tabellen else 0,
        "vervangen_elementen": (sum(
            een(f"SELECT COUNT(*) FROM {t} WHERE vervangen")
            for t in ("roles", "mechanisms", "entities", "relations", "emergent_effects"))
            if "lineage" in tabellen else 0),
        # Fase 3 (M3.4): voorspellingsregister
        "voorspellingen_open": (een(
            "SELECT COUNT(*) FROM predictions WHERE status = 'open'")
            if "predictions" in tabellen else 0),
        "voorspellingen_gescoord": (een(
            "SELECT COUNT(*) FROM predictions WHERE status != 'open'")
            if "predictions" in tabellen else 0),
        "voorspellingen_brier_gem": (een(
            "SELECT ROUND(AVG(brier), 4) FROM predictions WHERE brier IS NOT NULL")
            if "predictions" in tabellen else None),
    }


# ── Scoring v2 (fase 1): clusters & compositieclaims ─────────

def check_scoring_v2(conn):
    """M1.2/M1.5-dekking: clustertoekenning en compositieclaims."""
    zonder_cluster = [
        f"bron #{s['id']}: {s['title'][:70]}"
        for s in conn.execute("""
            SELECT id, title FROM sources WHERE cluster_key IS NULL ORDER BY id""")]

    zonder_compositie = [
        f"veld #{e['id']}: {e['label']}"
        for e in conn.execute("""
            SELECT id, label FROM emergent_effects e
            WHERE NOT EXISTS (SELECT 1 FROM arguments a
                              WHERE a.emergent_effect_id = e.id AND a.property = 'compositie')
            ORDER BY id""")]

    return [
        _bevinding("CLUSTER-BRON", "Bronnen zonder cluster_key", "waarschuwing",
                   zonder_cluster,
                   "Zonder cluster telt de bron als eigen cluster; dat is veilig maar "
                   "verbergt verwantschap met andere bronnen (M1.2)."),
        _bevinding("EFF-COMPOSITIE", "Hyperedges zonder compositieclaim", "waarschuwing",
                   zonder_compositie,
                   "Zonder bewijs dat het sámenspel bestaat is de veldscore gemaximeerd "
                   "op 0,50 (M1.5; analoog aan padclaims)."),
    ]


# ── Fase 2 (M2.1–M2.6): voorstellen, lineage & vervangen ─────

def check_fase2(conn):
    """Integriteit van het voorstel-/lineage-systeem en de vervangen-status."""
    tabellen = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    if "lineage" not in tabellen:
        return []  # pre-fase-2-database (bv. oude backup)

    lineage_zonder_voorstel = [
        f"lineage #{r['id']}: {r['soort']} {r['element_type']} "
        f"#{r['oud_id']} → #{r['nieuw_id']} (voorstel: {r['vstatus'] or 'ontbreekt'})"
        for r in conn.execute("""
            SELECT l.id, l.soort, l.element_type, l.oud_id, l.nieuw_id, v.status AS vstatus
            FROM lineage l LEFT JOIN voorstellen v ON v.id = l.voorstel_id
            WHERE v.id IS NULL OR v.status != 'geaccepteerd'
            ORDER BY l.id""")]

    vervangen_zonder_lineage = []
    for element_type, tabel, label in (
            ("rol", "roles", "t.name"), ("mechanisme", "mechanisms", "t.name"),
            ("entiteit", "entities", "t.name"),
            ("relatie", "relations", "t.relation_type"),
            ("emergent_effect", "emergent_effects", "t.name")):
        vervangen_zonder_lineage += [
            f"{element_type} #{r['id']}: {r['label']}"
            for r in conn.execute(f"""
                SELECT t.id, {label} AS label FROM {tabel} t
                WHERE t.vervangen AND NOT EXISTS (
                    SELECT 1 FROM lineage l
                    WHERE l.element_type = ? AND l.oud_id = t.id)
                ORDER BY t.id""", (element_type,))]

    rel_naar_vervangen_mech = [
        f"relatie #{r['id']} → vervangen mechanisme '{r['mech']}'"
        for r in conn.execute("""
            SELECT r.id, m.name AS mech FROM relations r
            JOIN mechanisms m ON m.id = r.mechanism_id
            WHERE m.vervangen AND NOT r.vervangen ORDER BY r.id""")]

    open_voorstellen = [
        f"voorstel #{r['id']} ({r['soort']}): {r['titel'][:60]} — "
        f"ingediend door {r['ingediend_door']}"
        for r in conn.execute(
            "SELECT id, soort, titel, ingediend_door FROM voorstellen "
            "WHERE status = 'open' ORDER BY id")]
    voorgestelde_args = conn.execute(
        "SELECT COUNT(*) FROM arguments WHERE status = 'voorgesteld'").fetchone()[0]

    return [
        _bevinding("LINEAGE-VOORSTEL", "Lineage-rijen zonder geaccepteerd voorstel", "fout",
                   lineage_zonder_voorstel,
                   "Elke opvolgingsrij hoort bij een geaccepteerd voorstel (M2.6); "
                   "een losse rij wijst op een omzeilde poort."),
        _bevinding("VERVANGEN-LINEAGE", "Vervangen elementen zonder lineage", "fout",
                   vervangen_zonder_lineage,
                   "Vervangen zonder opvolgingsspoor maakt het oude id onherleidbaar "
                   "(M2.6-kernregel: niets wissen, alles herleidbaar)."),
        _bevinding("VERVANGEN-REL-MECH", "Relaties gekoppeld aan een vervangen mechanisme",
                   "info", rel_naar_vervangen_mech,
                   "Niet-herbevestigd bewijs blijft bewust bij het vervangen element "
                   "achter en telt nergens in mee; herbevestig of koppel om."),
        _bevinding("REVIEW-WACHTRIJ", "Openstaande voorstellen", "info", open_voorstellen,
                   f"Plus {voorgestelde_args} argument(en) met status 'voorgesteld' — "
                   "zie /api/review_queue."),
    ]


# ── Fase 3 (M3.4): voorspellingsregister ─────────────────────

def check_fase3(conn):
    """Hygiëne van het voorspellingsregister: scoren wat scoorbaar is, en de
    heraudit-lijst van zelf gescoorde uitkomsten zichtbaar houden (§6.1)."""
    tabellen = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    if "predictions" not in tabellen:
        return []  # pre-fase-3-database (bv. oude backup)

    verlopen = [
        f"voorspelling #{r['id']} (deadline {r['deadline']}): {r['claim'][:70]}"
        for r in conn.execute("""
            SELECT id, deadline, claim FROM predictions
            WHERE status = 'open' AND deadline < date('now') ORDER BY deadline""")]
    zelf_gescoord = [
        f"voorspelling #{r['id']} ({r['status']}): {r['claim'][:70]}"
        for r in conn.execute("""
            SELECT id, status, claim FROM predictions
            WHERE self_scored ORDER BY id""")]

    return [
        _bevinding("VOORSPELLING-DEADLINE", "Open voorspellingen voorbij hun deadline",
                   "waarschuwing", verlopen,
                   "De uitkomst is beoordeelbaar; scoor haar via "
                   "PATCH /api/predictions/<id>/uitkomst (M3.4) — een register dat "
                   "niet gescoord wordt, toetst niets."),
        _bevinding("VOORSPELLING-ZELF", "Zelf gescoorde voorspellingen (heraudit-lijst)",
                   "info", zelf_gescoord,
                   "Indiener = beoordelaar (n=1-realiteit, §6.1); herauditeren zodra "
                   "er onafhankelijke reviewers zijn."),
    ]


# ── Alles in één run ─────────────────────────────────────────

def check_machtsvalentie(conn):
    """MACHTSVALENTIE: elk 'machtsvalentie'-aspect-argument codeert een geldige
    edge-valentie ('filter:<filter>' of 'as:<as>:<opent|sluit>') én hangt aan een edge
    (relatie of mechanisme). De API poortert dit al bij creatie; deze check is een
    backstop voor direct-DB-rijen (migraties/handmatig)."""
    import tegenmacht
    rows = conn.execute("""
        SELECT id, property_value, relation_id, mechanism_id
        FROM arguments WHERE property = 'machtsvalentie'
    """).fetchall()
    fout = []
    for a in rows:
        if tegenmacht.parse_machtsvalentie(a["property_value"]) is None:
            fout.append(f"arg #{a['id']}: ongeldige property_value {a['property_value']!r}")
        elif not (a["relation_id"] or a["mechanism_id"]):
            fout.append(f"arg #{a['id']}: hangt niet aan een edge (relatie/mechanisme)")
    out = []
    if fout:
        out.append(_bevinding(
            "MACHTSVALENTIE",
            "Machtsvalentie-annotaties met ongeldige vorm of zonder edge", "fout", fout,
            "Een 'machtsvalentie'-aspect codeert 'filter:<filter>' (verantwoording) of "
            "'as:<as>:<opent|sluit>' (contra-hegemonie) op een relatie/mechanisme."))
    return out


def check_methode(conn):
    """METHODE-CONSISTENTIE (A5, fout): citaties die 'verbatim_quote' claimen zonder
    een niet-lege quote. De methode stuurt de bronfactor (scoring.source_factor), dus
    een lege verbatim-claim is precies de tier-ontduiking die A5 moet afvangen. Deelt de
    regel met de create-poort (methode_consistentie). Alle bestaande citaties hebben
    methode=NULL → deze check start op 0 fouten (baseline blijft ongewijzigd)."""
    fout = []
    for c in conn.execute(
            "SELECT id, argument_id, methode, quote FROM citations "
            "WHERE methode IS NOT NULL ORDER BY id"):
        for prob in methode_consistentie(c["methode"], c["quote"]):
            fout.append(f"citatie #{c['id']} (arg #{c['argument_id']}): {prob}")
    return [
        _bevinding("METHODE-CONSISTENTIE",
                   "Citaties met een provenance-methode die niet bij de quote past",
                   "fout", fout,
                   "Een 'verbatim_quote'-citatie hoort een letterlijke quote te dragen; "
                   "anders weegt de sterkste methode-tier (factor 1,0) op lucht. De "
                   "create-poort weigert zulke citaties bij invoer (A5)."),
    ]


def _immuun_tabel_bestaat(conn) -> bool:
    return conn.execute("SELECT name FROM sqlite_master WHERE type='table' "
                        "AND name='immuun_oordelen'").fetchone() is not None


def check_immuunsysteem(conn):
    """IMMUUN-DEKKING (A1, info) + TEGENSPRAAK-DEKKING (A2, info).

    Meet de achterstand van het immuunsysteem: evidentiële roots (supporting/
    contradicting) die nog geen onafhankelijke bron-herverificatie (A1) resp. geen
    enkele gedecorreleerde tegenspraak (A2) hebben gehad. Beide zijn INFO — het
    immuunsysteem bouwt zich op; het is een meetbare achterstand, geen fout."""
    if not _immuun_tabel_bestaat(conn):
        return []
    zonder_herverificatie = [
        f"argument #{a['id']} ({a['stance']}): {(a['claim'] or '')[:70]}"
        for a in conn.execute("""
            SELECT a.id, a.stance, a.claim FROM arguments a
            WHERE a.stance IN ('supporting', 'contradicting')
              AND a.parent_argument_id IS NULL
              AND NOT a.vervangen
              AND NOT EXISTS (SELECT 1 FROM immuun_oordelen o
                              WHERE o.argument_id = a.id AND o.fase = 'herverificatie')
            ORDER BY a.id
        """)]
    zonder_tegenspraak = [
        f"argument #{a['id']} ({a['stance']}): {(a['claim'] or '')[:70]}"
        for a in conn.execute("""
            SELECT a.id, a.stance, a.claim FROM arguments a
            WHERE a.stance IN ('supporting', 'contradicting')
              AND a.parent_argument_id IS NULL
              AND a.status NOT IN ('voorgesteld', 'verworpen')
              AND NOT a.vervangen
              AND NOT EXISTS (SELECT 1 FROM immuun_oordelen o
                              WHERE o.argument_id = a.id AND o.fase = 'tegenspraak')
            ORDER BY a.id
        """)]
    return [
        _bevinding("IMMUUN-DEKKING",
                   "Evidentiële roots zonder onafhankelijke bron-herverificatie (A1)",
                   "info", zonder_herverificatie,
                   "Een supporting/contradicting-root hoort door een andere agent tegen "
                   "de echte bron te worden her-geverifieerd (verbatim + citaat-dekking). "
                   "Dit meet de achterstand; het verdict telt nergens in de score."),
        _bevinding("TEGENSPRAAK-DEKKING",
                   "Gemergede evidentiële roots zonder enige tegenspraak (A2)",
                   "info", zonder_tegenspraak,
                   "Elke gemergede claim hoort langs een gedecorreleerde aanklager te gaan "
                   "die een tegenbron zoekt of de inferentie aanvalt. Dit meet de "
                   "achterstand; het certificaat telt nergens in de score."),
    ]


# ── Publieke-intake-anomalie (D2.4, Laag 4) ──────────────────

# Drempels voor de burst-vlag. Bewust modest; een piek is een signaal voor de eigenaar
# (C4), geen model-inconsistentie — daarom ernst 'waarschuwing', nooit 'fout' (de
# ratchet-baseline blijft ongemoeid).
LEAD_BURST_VENSTER_UREN = 24
LEAD_BURST_DREMPEL_BETREFT = 10   # leads over één 'betreft' binnen het venster
LEAD_BURST_DREMPEL_IP = 10        # leads uit één IP-hash binnen het venster
LEAD_BURST_DREMPEL_DUP = 15       # duplicaat-cluster over één 'betreft' (near-dup narratief)


def check_lead_anomalie(conn):
    """LEAD-ANOMALIE (D2.4, waarschuwing): vlag een verdachte piek in de publieke intake —
    veel leads over één entiteit/'betreft', uit één IP-hash, of één near-dup-narratief
    (duplicaat-cluster) binnen een venster. Voedt C4 (eigenaar-toezicht) + /api/health.
    Nooit 'fout' (een burst is geen model-inconsistentie); de tabel hoeft niet te bestaan."""
    tabellen = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if "leads" not in tabellen:
        return []
    grens = f"-{LEAD_BURST_VENSTER_UREN} hours"
    treffers = []
    for r in conn.execute("""
            SELECT betreft, COUNT(*) AS n FROM leads
            WHERE betreft IS NOT NULL AND betreft <> ''
              AND created_at >= datetime('now', ?)
            GROUP BY betreft HAVING n >= ? ORDER BY n DESC""",
            (grens, LEAD_BURST_DREMPEL_BETREFT)):
        treffers.append(f"betreft '{r['betreft'][:60]}': {r['n']} leads "
                        f"in {LEAD_BURST_VENSTER_UREN}u")
    for r in conn.execute("""
            SELECT ingezonden_ip_hash AS h, COUNT(*) AS n FROM leads
            WHERE ingezonden_ip_hash IS NOT NULL
              AND created_at >= datetime('now', ?)
            GROUP BY ingezonden_ip_hash HAVING n >= ? ORDER BY n DESC""",
            (grens, LEAD_BURST_DREMPEL_IP)):
        treffers.append(f"IP-hash {r['h'][:12]}…: {r['n']} leads "
                        f"in {LEAD_BURST_VENSTER_UREN}u")
    for r in conn.execute("""
            SELECT betreft, COUNT(*) AS n FROM leads
            WHERE status = 'duplicaat' AND betreft IS NOT NULL AND betreft <> ''
              AND created_at >= datetime('now', ?)
            GROUP BY betreft HAVING n >= ? ORDER BY n DESC""",
            (grens, LEAD_BURST_DREMPEL_DUP)):
        treffers.append(f"near-dup-narratief over '{r['betreft'][:50]}': "
                        f"{r['n']} duplicaten")
    return [_bevinding(
        "LEAD-ANOMALIE",
        "Verdachte piek in de publieke intake (entiteit/IP/narratief)",
        "waarschuwing", treffers,
        "Een burst leads over één betreft, uit één IP-hash of als near-dup-cluster kan een "
        "gecoördineerde aanval zijn. Signaal voor de eigenaar (C4); geen model-fout — "
        "leads tellen nergens in de score mee. Herhaal-misbruikers zijn retroactief te "
        "blocklisten (Laag 0).")]


def run_all(conn, schema_path=SCHEMA_PATH, network=False):
    bevindingen = []
    bevindingen += check_koppelingsplicht(conn)
    bevindingen += check_zichtbaarheid(conn)
    bevindingen += check_bewijs(conn)
    bevindingen += check_invloed(conn)
    bevindingen += check_balans(conn)
    bevindingen += check_padclaims(conn)
    bevindingen += check_machtsvalentie(conn)
    bevindingen += check_methode(conn)
    bevindingen += check_immuunsysteem(conn)
    bevindingen += check_neutraliteit(conn)
    bevindingen += check_eigen_stem(conn)
    bevindingen += check_looptijd(conn)
    bevindingen += check_bestaan(conn)
    bevindingen += check_bronnen(conn, network=network)
    bevindingen += check_scoring_v2(conn)
    bevindingen += check_fase2(conn)
    bevindingen += check_fase3(conn)
    bevindingen += check_lead_anomalie(conn)
    bevindingen += check_schema_pariteit(conn, schema_path)

    totalen = {"fout": 0, "waarschuwing": 0, "info": 0}
    for b in bevindingen:
        if b["aantal"]:
            totalen[b["ernst"]] += b["aantal"]

    return {
        "gegenereerd": datetime.datetime.now().isoformat(timespec="seconds"),
        "kerngetallen": kerngetallen(conn),
        "bevindingen": bevindingen,
        "totalen": totalen,
    }
