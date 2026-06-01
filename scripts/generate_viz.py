"""Genereer een interactieve webvisualisatie van het propagandamodel.

Leest de SQLite database en produceert een standalone HTML-bestand
met een D3.js force-directed graph.
"""
import json
import sqlite3
from pathlib import Path

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

    # Relations with entity names, mechanism + temporal data
    cur.execute("""
        SELECT r.id, r.source_id, r.target_id, r.relation_type,
               r.certainty, r.influence, r.bidirectional,
               r.description,
               r.active_from, r.active_until, r.active,
               e1.name as source_name, e2.name as target_name,
               m.name as mechanism_name, m.filter as mechanism_filter
        FROM relations r
        JOIN entities e1 ON r.source_id = e1.id
        JOIN entities e2 ON r.target_id = e2.id
        LEFT JOIN mechanisms m ON r.mechanism_id = m.id
    """)
    relations = [dict(row) for row in cur.fetchall()]

    # Roles
    cur.execute("SELECT id, name, category, description FROM roles")
    roles = [dict(row) for row in cur.fetchall()]

    # Mechanisms
    cur.execute("SELECT id, name, filter, mechanism_type, description, effect, source_role_id, target_role_id FROM mechanisms")
    mechanisms = [dict(row) for row in cur.fetchall()]

    # Arguments: volledige discussiebomen
    cur.execute("""
        SELECT a.id, a.relation_id, a.entity_id, a.parent_argument_id,
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

    return {
        'entities': entities,
        'relations': relations,
        'roles': roles,
        'mechanisms': mechanisms,
        'arguments': arguments,
        'citations': citations,
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
