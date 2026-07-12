"""Graafdata voor de visualisatie — één databouw, twee afnemers (W5.1).

`export_data(conn)` bouwt de volledige JSON-structuur die de viz nodig heeft
(entiteiten, relaties, theorielaag, discussiebomen, afgeleide scores, kleurmeter,
inkomstensamenstelling). Gedeeld door:
  - server.py  → GET /api/graph_data (live; de pagina op / haalt dit bij het laden)
  - scripts/generate_viz.py → statische export (bakt dezelfde data in web/index.html)

Puur stdlib + de bestaande repo-root modules (scoring, politiek), zoals scoring.py.
"""
import json
import re
import sqlite3
from pathlib import Path

import scoring   # scoringsketen: afgeleide praktijk- en theoriescores
import politiek  # politieke kleurmeter
import tegenmacht  # machtsvalentie: tegenmacht als gerichte edge-valentie
import doelgroep  # welstandsmeter: getargette marketing-/welstandsklasse per outlet
import bereik as bereik_mod  # bereikmeter: publieksbereik (kijkers/lezers) per jaar

ROOT = Path(__file__).parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
BRIDGING_PATH = ROOT / "data" / "bridging.json"
RELEASES_DIR = ROOT / "releases"


def laatste_release():
    """Nieuwste release-snapshot (M3.1) voor de releasetag in de topbar, of None."""
    nieuwste, beste = None, ()
    for pad in RELEASES_DIR.glob("model-v*.json"):
        m = re.fullmatch(r"model-v(\d+)\.(\d+)\.(\d+)\.json", pad.name)
        if m and tuple(map(int, m.groups())) > beste:
            beste, nieuwste = tuple(map(int, m.groups())), pad
    if nieuwste is None:
        return None
    try:
        snap = json.loads(nieuwste.read_text())
        return {"versie": snap.get("versie"), "gegenereerd": snap.get("gegenereerd"),
                "titel": snap.get("titel")}
    except (OSError, json.JSONDecodeError):
        return None


def export_data(conn):
    """Bouw de volledige viz-datastructuur uit een open DB-connectie.

    De aanroeper beheert de connectie (openen/sluiten); row_factory wordt hier
    op sqlite3.Row gezet omdat de bouw op naam indexeert."""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Entities with role info + temporal data.
    # Vervangen elementen (M2.6) blijven overal buiten beeld: de viz toont het
    # levende model; opvolging is opvraagbaar via /api/lineage.
    # 'voorgesteld' wordt méégegeven (getagd met status) zodat de viz het als
    # gestippelde 'in review'-ghost kan tonen achter een toggle; default blijft de
    # viz het goedgekeurde model tonen. Vervangen (M2.6) blijft altijd buiten beeld.
    cur.execute("""
        SELECT e.id, e.name, e.type, e.description, e.status,
               e.active_from, e.active_until, e.active,
               r.name as role_name, r.category as filter_category
        FROM entities e
        LEFT JOIN roles r ON e.primary_role_id = r.id
        WHERE NOT e.vervangen AND e.status IN ('goedgekeurd', 'voorgesteld')
    """)
    entities = [dict(row) for row in cur.fetchall()]

    # Alle rollen per entiteit (hoofdrol + entity_roles) — nodig om padclaims
    # (rol ⇢ rol) op praktijk-paren te kunnen toetsen.
    entity_role_ids = {}
    for eid, rid in cur.execute(
        "SELECT entity_id, role_id FROM entity_roles WHERE role_id IS NOT NULL"
    ):
        entity_role_ids.setdefault(eid, set()).add(rid)
    for eid, rid in cur.execute(
        "SELECT id, primary_role_id FROM entities WHERE primary_role_id IS NOT NULL"
    ):
        entity_role_ids.setdefault(eid, set()).add(rid)
    for e in entities:
        e['role_ids'] = sorted(entity_role_ids.get(e['id'], []))

    # Relations with entity names, mechanism + temporal data
    cur.execute("""
        SELECT r.id, r.source_id, r.target_id, r.relation_type,
               r.certainty, r.influence, r.bidirectional,
               r.description, r.mechanism_id, r.status,
               r.active_from, r.active_until, r.active,
               e1.name as source_name, e2.name as target_name,
               m.name as mechanism_name, m.filter as mechanism_filter,
               COALESCE(m.aard, 'direct') as aard
        FROM relations r
        JOIN entities e1 ON r.source_id = e1.id
        JOIN entities e2 ON r.target_id = e2.id
        LEFT JOIN mechanisms m ON r.mechanism_id = m.id
        WHERE NOT r.vervangen AND r.status IN ('goedgekeurd', 'voorgesteld')
    """)
    relations = [dict(row) for row in cur.fetchall()]

    # Een relatie mag geen eindpunt hebben dat zélf buiten beeld valt: de statusfilters op
    # entiteit en relatie lopen onafhankelijk, dus een 'voorgesteld'/'goedgekeurd' relatie
    # kan naar een 'afgewezen' entiteit wijzen. Zo'n bungelende edge laat d3.forceLink in de
    # viz crashen ("missing: <id>") → het praktijkmodel laadt dan niet meer. Houd alleen
    # edges met béide eindpunten in de geëmitteerde entiteitenset.
    levende_entiteit_ids = {e['id'] for e in entities}
    _voor = len(relations)
    relations = [r for r in relations
                 if r['source_id'] in levende_entiteit_ids
                 and r['target_id'] in levende_entiteit_ids]
    if len(relations) != _voor:
        print(f"  {_voor - len(relations)} relatie(s) met een eindpunt buiten beeld weggelaten "
              "(entiteit afgewezen/verborgen)")

    # Roles (+ temporele velden: ook de theorielaag is historisch contingent)
    cur.execute("SELECT id, name, category, description, active_from, active_until "
                "FROM roles WHERE NOT vervangen")
    roles = [dict(row) for row in cur.fetchall()]

    # Mechanisms (incl. `aard`: direct / veld_instantiatie / veld_eigenschap)
    cur.execute("SELECT id, name, filter, mechanism_type, aard, description, effect, "
                "source_role_id, target_role_id, active_from, active_until "
                "FROM mechanisms WHERE NOT vervangen")
    mechanisms = [dict(row) for row in cur.fetchall()]

    # Twee-assen-tags: alle filters (multi) + thema's (dwarsverbanden) per mechanisme.
    # Primair filter (kleur/lead) staat altijd vooraan in 'filters'.
    mech_filters, mech_themes = {}, {}
    for mid, flt in cur.execute("SELECT mechanism_id, filter FROM mechanism_filters"):
        mech_filters.setdefault(mid, []).append(flt)
    for mid, thm in cur.execute("SELECT mechanism_id, theme FROM mechanism_themes"):
        mech_themes.setdefault(mid, []).append(thm)
    for m in mechanisms:
        fs = mech_filters.get(m['id'], [m['filter']])
        # primair filter vooraan
        m['filters'] = [m['filter']] + [f for f in fs if f != m['filter']]
        m['themes'] = sorted(mech_themes.get(m['id'], []))

    # Emergente effecten (hyperedge): een systeemeigenschap over MEERDERE rollen.
    # Optioneel — oudere DB's zonder de tabel leveren simpelweg een lege lijst.
    emergent_effects = []
    have_emergent = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='emergent_effects'"
    ).fetchone()
    if have_emergent:
        cur.execute("SELECT id, name, label, category, description, effect, active_from, "
                    "active_until FROM emergent_effects WHERE NOT vervangen")
        emergent_effects = [dict(row) for row in cur.fetchall()]
        members = {}
        for eid, rid in cur.execute(
            "SELECT emergent_effect_id, role_id FROM emergent_effect_members"
        ):
            members.setdefault(eid, []).append(rid)
        for e in emergent_effects:
            e['member_role_ids'] = members.get(e['id'], [])
        # Tweede-orde-structuur: deel-effecten (apex-veld) + omgekeerde verwijzing
        sub, parent = {}, {}
        if cur.execute("SELECT name FROM sqlite_master WHERE type='table' "
                       "AND name='emergent_effect_subeffects'").fetchone():
            for pid, cid in cur.execute(
                    "SELECT parent_effect_id, child_effect_id FROM emergent_effect_subeffects"):
                sub.setdefault(pid, []).append(cid)
                parent.setdefault(cid, []).append(pid)
        for e in emergent_effects:
            e['sub_effect_ids'] = sub.get(e['id'], [])
            e['parent_effect_ids'] = parent.get(e['id'], [])

    # Arguments: volledige discussiebomen
    cur.execute("""
        SELECT a.id, a.relation_id, a.entity_id, a.role_id, a.mechanism_id,
               a.emergent_effect_id, a.parent_argument_id,
               a.property, a.property_value,
               a.stance, a.claim, a.title, a.reasoning, a.weight, a.status,
               a.objection_type
        FROM arguments a
        ORDER BY a.parent_argument_id NULLS FIRST, a.id
    """)
    arguments = [dict(row) for row in cur.fetchall()]

    # Citations per argument (incl. klikbare vindplaats/archief uit source_locations)
    cur.execute("""
        SELECT c.id, c.argument_id, c.quote, c.page, c.section, c.context,
               c.source_id, s.title as source_title, s.author as source_author
        FROM citations c
        JOIN sources s ON c.source_id = s.id
    """)
    citations = [dict(row) for row in cur.fetchall()]
    bron_locs = {}
    for sid, lt, lv in cur.execute("SELECT source_id, location_type, location FROM source_locations"):
        bron_locs.setdefault(sid, []).append((lt, lv))

    def _link(lt, lv):
        if lt in ("url", "archive_url"):
            return lv
        if lt == "doi":
            return f"https://doi.org/{lv}"
        if lt == "handle":
            return f"https://hdl.handle.net/{lv}"
        return None
    for c in citations:
        sl = bron_locs.get(c.get("source_id"), [])
        c["url"] = next((_link(t, v) for t, v in sl if _link(t, v)), None)
        c["archive_url"] = next((v for t, v in sl if t == "archive_url"), None)
        c["has_locator"] = bool(sl)

    # Instantiations: expliciete klasse<->instantie-koppeling + exemplariteit
    cur.execute("SELECT id, role_id, mechanism_id, entity_id, relation_id, exemplarity FROM instantiations")
    instantiations = [dict(r) for r in cur.fetchall()]

    # Ratings-aggregaat per argument (M2.5): mens en agent apart (agent = advies)
    ratings = {}
    if cur.execute("SELECT name FROM sqlite_master WHERE type='table' "
                   "AND name='argument_ratings'").fetchone():
        for aid, kind, oordeel, n in cur.execute("""
            SELECT ar.argument_id, u.kind, ar.oordeel, COUNT(*)
            FROM argument_ratings ar JOIN users u ON u.username = ar.rater
            GROUP BY ar.argument_id, u.kind, ar.oordeel"""):
            ratings.setdefault(aid, {"mens": {"nuttig": 0, "niet_nuttig": 0},
                                     "agent": {"nuttig": 0, "niet_nuttig": 0}})
            ratings[aid][kind][oordeel] = n
    for a in arguments:
        a['ratings'] = ratings.get(a['id'])

    # Volledige scoringsketen (gedeeld met /api/scores), zolang de connectie nog open is.
    # Bridged gewichten (M2.5) tellen mee zodra scripts/bridging.py ze geschreven heeft.
    scores = scoring.compute_all_scores(
        conn, bridged_weights=scoring.bridged_weights_from_file(BRIDGING_PATH))

    # Politieke kleurmeter (id-gekoppelde maps voor het detailpaneel). Preview = ook
    # `voorgesteld` signalen tellen voorlopig mee; nieuw werk staat immers nog voorgesteld.
    km = politiek.compute_kleurmeter(conn, include_voorgesteld=True)
    kleurmeter = {
        'preview': km['preview'],
        'personen': {p['id']: p for p in km['personen']},
        'organisaties': {o['id']: o for o in km['organisaties']},
    }

    # Machtsvalentie (tegenmacht als GERICHTE edge-valentie): per actor de contra-
    # hegemonische valentie per as + welke filter-concentraties ze verantwoordt, plus per
    # relatie/mechanisme een netto `teken` (+1 opent / −1 sluit / 0). Preview net als de
    # kleurmeter — nieuw werk staat voorgesteld. Voedt geen score; puur een overlay-laag.
    mv = tegenmacht.compute_machtsvalentie(conn, include_voorgesteld=True)
    machtsvalentie = {
        'preview': mv['preview'],
        'actoren': {a['id']: a for a in mv['actoren']},
        'relaties': mv['relaties'],       # relation_id → netto valentie (praktijkmodel)
        'mechanismen': mv['mechanismen'],  # mechanism_id → netto valentie (theoriemodel)
    }

    # Welstandsmeter (doelgroep.py): per outlet de getargette marketing-/welstandsklasse
    # (hoog A ↔ laag D) uit gesourcete 'doelgroepklasse'-signalen. Id-gekoppelde map voor de
    # viz (nodekleur + detailpaneel). Preview net als de kleurmeter — nieuw werk staat voorgesteld.
    dg = doelgroep.compute_doelgroepmeter(conn, include_voorgesteld=True)
    doelgroepmeter = {
        'preview': dg['preview'],
        'outlets': {o['id']: o for o in dg['outlets']},
    }

    # Inkomstensamenstelling per outlet (de 'pie' in het detailpaneel): afgeleid uit de
    # financier-edges met gesourcete aandelen. Preview = ook nog-`voorgesteld` aandelen,
    # zodat nieuw werk meteen zichtbaar is (zoals de kleurmeter).
    inkomsten = scoring.compute_income_composition(conn, include_voorgesteld=True)

    # Bereikmeter (bereik.py): gesourcet publieksbereik per entiteit per jaar. Id-gekoppelde
    # map voor het detailpaneel + een plat per-node veld `bereik_reeks` (jaar → grootste
    # publieksmaat) zodat de grootte-maat 'mediabereik' het zonder aparte lookup kan lezen
    # en meebeweegt met de tijdlijn-slider. Preview net als de andere meters.
    br = bereik_mod.compute_bereik(conn, include_voorgesteld=True)
    bereikmeter = {
        'preview': br['preview'],
        'entiteiten': {o['id']: o for o in br['entiteiten']},
    }

    # Argument counts per relation (voor edge labels)
    arg_counts = {}
    for a in arguments:
        rid = a.get('relation_id')
        if rid:
            if rid not in arg_counts:
                arg_counts[rid] = {'arg_count': 0, 'stances': []}
            arg_counts[rid]['arg_count'] += 1
            arg_counts[rid]['stances'].append(a['stance'])

    # Compute degree for node sizing — alleen op het goedgekeurde model; ghosts
    # (voorgesteld) tellen niet mee, anders zou node-grootte van review-werk afhangen.
    degree = {}
    for r in relations:
        if r.get('status') != 'goedgekeurd':
            continue
        degree[r['source_id']] = degree.get(r['source_id'], 0) + 1
        degree[r['target_id']] = degree.get(r['target_id'], 0) + 1

    for e in entities:
        e['degree'] = degree.get(e['id'], 0)
        b = bereikmeter['entiteiten'].get(e['id'])
        e['bereik_reeks'] = b['reeks'] if b else None

    for r in relations:
        ac = arg_counts.get(r['id'])
        r['argument_count'] = ac['arg_count'] if ac else 0
        # Relatie erft de twee-assen-tags van haar mechanisme (primair filter blijft mechanism_filter)
        mid = r.get('mechanism_id')
        r['mechanism_filters'] = mech_filters.get(mid, [r['mechanism_filter']] if r.get('mechanism_filter') else [])
        r['mechanism_themes'] = sorted(mech_themes.get(mid, []))

    # ── Afgeleide scores injecteren (uit scoring.compute_all_scores) ──
    # Naast het kale cijfer ook het scoring-v2-detail (interval, onweersproken-,
    # SPOF- en clustervlaggen) en de afgeleide invloed (M1.7).
    for r in relations:
        r['derived_certainty'] = scores['relations'].get(r['id'], r.get('certainty') or 0.0)
        r['score_detail'] = scores['relations_detail'].get(r['id'])
        r['derived_influence'] = scores['relations_influence'].get(r['id'], r.get('influence') or 0.0)
        r['influence_detail'] = scores['relations_influence_detail'].get(r['id'])
    for e in entities:
        if e['type'] == 'persoon':
            # Een persoon bestaat of bestaat niet: geen zekerheidsscore (scoring.py
            # exporteert personen niet). Expliciet None — de 0.0-default zou als
            # "score 0%" renderen en dat is precies de misvatting die we weren.
            e['derived_certainty'] = None
            e['score_detail'] = None
        else:
            e['derived_certainty'] = scores['entities'].get(e['id'], 0.0)
            e['score_detail'] = scores['entities_detail'].get(e['id'])
        # Afgeleide primaire rol = bron van waarheid voor kleur/categorie: het filter
        # met de grootste Σ(zekerheid×invloed) over de relaties van de entiteit. De
        # toegekende primary_role-categorie (uit de SQL hierboven) blijft als fallback
        # voor entiteiten die nog geen (goedgekeurde) relaties hebben.
        e['filter_scores'] = scores.get('entity_filter_scores', {}).get(e['id'], {})
        afgeleid = scores.get('entity_primary_filter', {}).get(e['id'])
        if afgeleid:
            e['toegekend_filter_category'] = e.get('filter_category')
            e['filter_category'] = afgeleid
            e['filter_category_bron'] = 'afgeleid'
        else:
            e['filter_category_bron'] = 'toegekend' if e.get('filter_category') else 'geen'
            e['filter_category'] = e.get('filter_category') or 'overig'
    for role in roles:
        role.update(scores['roles'].get(role['id'], {}))
    for m in mechanisms:
        m.update(scores['mechanisms'].get(m['id'], {}))
    for eff in emergent_effects:
        eff.update(scores.get('emergent_effects', {}).get(eff['id'], {}))
    # Per argument τ (basiskracht) en σ (eindkracht na replies, M1.1) + admin-veto-
    # vlaggen ('argument klopt niet' door een maintainer nult zijn parent volledig).
    for a in arguments:
        sc = scores.get('argument_scores', {}).get(a['id'])
        if sc:
            a['tau'] = sc['tau']
            a['sigma'] = sc['sigma']
            if sc.get('admin_veto'):
                a['admin_veto'] = True
            if sc.get('geveto'):
                a['geveto'] = True

    # ── Structurele invloed-centraliteit (topologie) ──
    # Twee varianten per node: de basisvelden (influence_*) komen uit de SCHONE dyadische graaf
    # (veld-effecten weg) — dat is de default-view. De *_veld-velden komen uit de variant MÉT
    # veld-effecten (fan-out gedempt); de viz-toggle "toon veld-effecten" schakelt ernaartoe.
    def _attach_influence(items, clean_map, field_map):
        keys = [('direct', 'influence_direct'), ('transitive', 'influence_transitive'),
                ('reach', 'influence_reach'), ('transitive_norm', 'influence_norm'),
                ('rank', 'influence_rank'), ('public', 'influence_public'),
                ('public_norm', 'influence_public_norm'), ('public_rank', 'influence_public_rank'),
                ('politiek', 'influence_politiek'), ('politiek_norm', 'influence_politiek_norm'),
                ('politiek_rank', 'influence_politiek_rank')]
        defaults = {'reach': 0, 'rank': None, 'public_rank': None, 'politiek_rank': None}
        for it in items:
            clean = clean_map.get(it['id'], {})
            field = field_map.get(it['id'], {})
            for src_key, dst_key in keys:
                d = defaults.get(src_key, 0.0)
                it[dst_key] = clean.get(src_key, d)
                it[dst_key + '_veld'] = field.get(src_key, d)

    _attach_influence(entities,
                      scores.get('entity_influence_clean', {}),
                      scores.get('entity_influence', {}))   # instantiemodel
    _attach_influence(roles,
                      scores.get('role_influence_clean', {}),
                      scores.get('role_influence', {}))      # theoretisch model

    return {
        'entities': entities,
        'relations': relations,
        'roles': roles,
        'mechanisms': mechanisms,
        'emergent_effects': emergent_effects,
        'arguments': arguments,
        'citations': citations,
        'instantiations': instantiations,
        'release': laatste_release(),   # M3.1: releasetag in de topbar (of null)
        'kleurmeter': kleurmeter,       # politieke kleurmeter per entiteit (detailpaneel)
        'machtsvalentie': machtsvalentie,  # tegenmacht als gerichte edge-valentie (overlay)
        'doelgroep': doelgroepmeter,    # welstandsmeter: getargette klasse per outlet (overlay)
        'inkomsten': inkomsten,         # inkomstensamenstelling per outlet (donut, detailpaneel)
        'bereik': bereikmeter,          # bereikmeter: publieksbereik per jaar (node-grootte + detailpaneel)
    }
