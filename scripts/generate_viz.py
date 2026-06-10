"""Genereer een interactieve webvisualisatie van het propagandamodel.

Leest de SQLite database en produceert een standalone HTML-bestand
met een D3.js force-directed graph.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import scoring  # noqa: E402  (repo-root module met de scoringsketen)

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
OUT_PATH = Path(__file__).parent.parent / "web" / "index.html"
TEMPLATE_PATH = Path(__file__).parent.parent / "web" / "template.html"


def export_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Entities with role info + temporal data
    cur.execute("""
        SELECT e.id, e.name, e.type, e.description,
               e.active_from, e.active_until, e.active,
               r.name as role_name, r.category as filter_category
        FROM entities e
        LEFT JOIN roles r ON e.primary_role_id = r.id
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
               r.description, r.mechanism_id,
               r.active_from, r.active_until, r.active,
               e1.name as source_name, e2.name as target_name,
               m.name as mechanism_name, m.filter as mechanism_filter,
               COALESCE(m.aard, 'direct') as aard
        FROM relations r
        JOIN entities e1 ON r.source_id = e1.id
        JOIN entities e2 ON r.target_id = e2.id
        LEFT JOIN mechanisms m ON r.mechanism_id = m.id
    """)
    relations = [dict(row) for row in cur.fetchall()]

    # Roles
    cur.execute("SELECT id, name, category, description FROM roles")
    roles = [dict(row) for row in cur.fetchall()]

    # Mechanisms (incl. `aard`: direct / veld_instantiatie / veld_eigenschap)
    cur.execute("SELECT id, name, filter, mechanism_type, aard, description, effect, source_role_id, target_role_id FROM mechanisms")
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
        cur.execute("SELECT id, name, label, category, description, effect FROM emergent_effects")
        emergent_effects = [dict(row) for row in cur.fetchall()]
        members = {}
        for eid, rid in cur.execute(
            "SELECT emergent_effect_id, role_id FROM emergent_effect_members"
        ):
            members.setdefault(eid, []).append(rid)
        for e in emergent_effects:
            e['member_role_ids'] = members.get(e['id'], [])

    # Arguments: volledige discussiebomen
    cur.execute("""
        SELECT a.id, a.relation_id, a.entity_id, a.role_id, a.mechanism_id, a.parent_argument_id,
               a.property, a.property_value,
               a.stance, a.claim, a.reasoning, a.weight, a.status
        FROM arguments a
        ORDER BY a.parent_argument_id NULLS FIRST, a.id
    """)
    arguments = [dict(row) for row in cur.fetchall()]

    # Citations per argument
    cur.execute("""
        SELECT c.id, c.argument_id, c.quote, c.page, c.section, c.context,
               s.title as source_title, s.author as source_author
        FROM citations c
        JOIN sources s ON c.source_id = s.id
    """)
    citations = [dict(row) for row in cur.fetchall()]

    # Instantiations: expliciete klasse<->instantie-koppeling + exemplariteit
    cur.execute("SELECT id, role_id, mechanism_id, entity_id, relation_id, exemplarity FROM instantiations")
    instantiations = [dict(r) for r in cur.fetchall()]

    # Volledige scoringsketen (gedeeld met /api/scores), zolang de connectie nog open is
    scores = scoring.compute_all_scores(conn)

    # Argument counts per relation (voor edge labels)
    arg_counts = {}
    for a in arguments:
        rid = a.get('relation_id')
        if rid:
            if rid not in arg_counts:
                arg_counts[rid] = {'arg_count': 0, 'stances': []}
            arg_counts[rid]['arg_count'] += 1
            arg_counts[rid]['stances'].append(a['stance'])

    conn.close()

    # Compute degree for node sizing
    degree = {}
    for r in relations:
        degree[r['source_id']] = degree.get(r['source_id'], 0) + 1
        degree[r['target_id']] = degree.get(r['target_id'], 0) + 1

    for e in entities:
        e['degree'] = degree.get(e['id'], 0)
        ac = arg_counts.get(e['id'])

    for r in relations:
        ac = arg_counts.get(r['id'])
        r['argument_count'] = ac['arg_count'] if ac else 0
        # Relatie erft de twee-assen-tags van haar mechanisme (primair filter blijft mechanism_filter)
        mid = r.get('mechanism_id')
        r['mechanism_filters'] = mech_filters.get(mid, [r['mechanism_filter']] if r.get('mechanism_filter') else [])
        r['mechanism_themes'] = sorted(mech_themes.get(mid, []))

    # ── Afgeleide scores injecteren (uit scoring.compute_all_scores) ──
    for r in relations:
        r['derived_certainty'] = scores['relations'].get(r['id'], r.get('certainty') or 0.0)
    for e in entities:
        e['derived_certainty'] = scores['entities'].get(e['id'], 0.0)
    for role in roles:
        role.update(scores['roles'].get(role['id'], {}))
    for m in mechanisms:
        m.update(scores['mechanisms'].get(m['id'], {}))

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
    }


def generate():
    data = export_data()
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    html = template.replace('"%%DATA%%"', json.dumps(data, ensure_ascii=False, indent=2))
    OUT_PATH.write_text(html, encoding='utf-8')
    print(f"Visualisatie gegenereerd: {OUT_PATH}")
    print(f"  {len(data['entities'])} entiteiten, {len(data['relations'])} relaties")
    print(f"  Open in browser: file://{OUT_PATH.resolve()}")


if __name__ == "__main__":
    generate()
