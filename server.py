"""Propaganda Model — webserver met discussieboom-API.

Start: python3 server.py
Open:  http://localhost:5000
"""
import json
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request, send_file

DB_PATH = Path(__file__).parent / "data" / "propaganda_model.db"
WEB_PATH = Path(__file__).parent / "web"

app = Flask(__name__, static_folder=str(WEB_PATH), static_url_path="/static")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Pagina's ─────────────────────────────────────────────────

@app.route("/")
def index():
    return send_file(WEB_PATH / "index.html")


# ── Argumenten API ───────────────────────────────────────────

@app.route("/api/arguments")
def get_arguments():
    """Haal argumenten op voor een relatie of entiteit."""
    relation_id = request.args.get("relation_id", type=int)
    entity_id = request.args.get("entity_id", type=int)

    conn = get_db()
    if relation_id:
        rows = conn.execute("""
            SELECT a.*, c.id as citation_id, c.quote, c.page, c.section, c.context as cite_context,
                   s.title as source_title, s.author as source_author, s.reliability
            FROM arguments a
            LEFT JOIN citations c ON c.argument_id = a.id
            LEFT JOIN sources s ON c.source_id = s.id
            WHERE a.relation_id = ?
            ORDER BY a.parent_argument_id NULLS FIRST, a.id
        """, (relation_id,)).fetchall()
    elif entity_id:
        rows = conn.execute("""
            SELECT a.*, c.id as citation_id, c.quote, c.page, c.section, c.context as cite_context,
                   s.title as source_title, s.author as source_author, s.reliability
            FROM arguments a
            LEFT JOIN citations c ON c.argument_id = a.id
            LEFT JOIN sources s ON c.source_id = s.id
            WHERE a.entity_id = ?
            ORDER BY a.parent_argument_id NULLS FIRST, a.id
        """, (entity_id,)).fetchall()
    else:
        conn.close()
        return jsonify([])

    # Groepeer citaties per argument
    args_map = {}
    for row in rows:
        row = dict(row)
        aid = row["id"]
        if aid not in args_map:
            args_map[aid] = {
                "id": row["id"],
                "relation_id": row["relation_id"],
                "entity_id": row["entity_id"],
                "parent_argument_id": row["parent_argument_id"],
                "property": row["property"],
                "property_value": row["property_value"],
                "stance": row["stance"],
                "claim": row["claim"],
                "reasoning": row["reasoning"],
                "weight": row["weight"],
                "status": row["status"],
                "contributed_by": row["contributed_by"],
                "created_at": row["created_at"],
                "citations": [],
            }
        if row.get("citation_id"):
            args_map[aid]["citations"].append({
                "id": row["citation_id"],
                "quote": row["quote"],
                "page": row["page"],
                "section": row["section"],
                "context": row["cite_context"],
                "source_title": row["source_title"],
                "source_author": row["source_author"],
                "reliability": row["reliability"],
            })

    conn.close()
    return jsonify(list(args_map.values()))


@app.route("/api/arguments", methods=["POST"])
def create_argument():
    """Nieuw argument toevoegen (root of reactie)."""
    data = request.json
    if not data:
        return jsonify({"error": "Geen data"}), 400

    # Validatie
    claim = (data.get("claim") or "").strip()
    if not claim:
        return jsonify({"error": "Claim is verplicht"}), 400

    stance = data.get("stance")
    if stance not in ("supporting", "contradicting", "contextual"):
        return jsonify({"error": "Ongeldige stance"}), 400

    relation_id = data.get("relation_id")
    entity_id = data.get("entity_id")
    if not relation_id and not entity_id:
        return jsonify({"error": "relation_id of entity_id is verplicht"}), 400

    parent_id = data.get("parent_argument_id")
    prop = data.get("property")
    prop_value = data.get("property_value")
    reasoning = (data.get("reasoning") or "").strip() or None
    weight = data.get("weight")
    contributed_by = (data.get("contributed_by") or "").strip() or "anoniem"

    if weight is not None:
        try:
            weight = float(weight)
            if not 0 <= weight <= 1:
                weight = None
        except (ValueError, TypeError):
            weight = None

    conn = get_db()
    try:
        cur = conn.execute("""
            INSERT INTO arguments
                (relation_id, entity_id, parent_argument_id, property, property_value,
                 stance, claim, reasoning, weight, contributed_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (relation_id, entity_id, parent_id, prop, prop_value,
              stance, claim, reasoning, weight, contributed_by))
        arg_id = cur.lastrowid

        # Log in edit_log
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('arguments', ?, 'created', ?, ?, ?)
        """, (arg_id, contributed_by, json.dumps({"claim": claim, "stance": stance}),
              f"Nieuw argument: {stance}"))

        conn.commit()
        result = dict(conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone())
        conn.close()
        return jsonify(result), 201

    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400


@app.route("/api/arguments/<int:arg_id>/status", methods=["PATCH"])
def update_argument_status(arg_id):
    """Verificatie-status van een argument bijwerken."""
    data = request.json
    new_status = data.get("status")
    valid = ("ongecontroleerd", "bronvermelding_nodig", "betwist", "geverifieerd", "verouderd")
    if new_status not in valid:
        return jsonify({"error": f"Status moet een van {valid} zijn"}), 400

    conn = get_db()
    old = conn.execute("SELECT status FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not old:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404

    conn.execute("UPDATE arguments SET status = ? WHERE id = ?", (new_status, arg_id))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value)
        VALUES ('arguments', ?, ?, ?, ?, ?)
    """, (arg_id, "verified" if new_status == "geverifieerd" else "disputed",
          data.get("changed_by", "anoniem"),
          json.dumps({"status": old["status"]}),
          json.dumps({"status": new_status})))

    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "status": new_status})


@app.route("/api/sources")
def get_sources():
    """Lijst van alle bronnen (voor citaat-selectie)."""
    conn = get_db()
    rows = conn.execute("SELECT id, title, author, source_type, reliability FROM sources ORDER BY author").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/citations", methods=["POST"])
def create_citation():
    """Citatie toevoegen aan een argument."""
    data = request.json
    if not data:
        return jsonify({"error": "Geen data"}), 400

    argument_id = data.get("argument_id")
    source_id = data.get("source_id")
    if not argument_id or not source_id:
        return jsonify({"error": "argument_id en source_id zijn verplicht"}), 400

    conn = get_db()
    try:
        cur = conn.execute("""
            INSERT INTO citations (argument_id, source_id, quote, page, section, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (argument_id, source_id, data.get("quote"), data.get("page"),
              data.get("section"), data.get("context")))
        conn.commit()
        cid = cur.lastrowid
        conn.close()
        return jsonify({"id": cid}), 201
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    print(f"Database: {DB_PATH}")
    print(f"Open: http://localhost:5000")
    app.run(debug=True, port=5000)
