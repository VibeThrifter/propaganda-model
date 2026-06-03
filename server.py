"""Propaganda Model — webserver met discussieboom-API.

Start: python3 server.py
Open:  http://localhost:5000
"""
import json
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request, send_file

import scoring  # scoringsketen: afgeleide praktijk- en theoriescores

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
    """Haal argumenten op voor een relatie, entiteit, rol of mechanisme."""
    targets = {
        "relation_id": request.args.get("relation_id", type=int),
        "entity_id": request.args.get("entity_id", type=int),
        "role_id": request.args.get("role_id", type=int),
        "mechanism_id": request.args.get("mechanism_id", type=int),
    }
    column = next((k for k, v in targets.items() if v), None)
    if not column:
        return jsonify([])

    conn = get_db()
    rows = conn.execute(f"""
        SELECT a.*, c.id as citation_id, c.quote, c.page, c.section, c.context as cite_context,
               s.title as source_title, s.author as source_author, s.reliability
        FROM arguments a
        LEFT JOIN citations c ON c.argument_id = a.id
        LEFT JOIN sources s ON c.source_id = s.id
        WHERE a.{column} = ?
        ORDER BY a.parent_argument_id NULLS FIRST, a.id
    """, (targets[column],)).fetchall()

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
    role_id = data.get("role_id")              # literatuur-argument over een rol (theorie)
    mechanism_id = data.get("mechanism_id")    # literatuur-argument over een mechanisme (theorie)
    if not (relation_id or entity_id or role_id or mechanism_id):
        return jsonify({"error": "relation_id, entity_id, role_id of mechanism_id is verplicht"}), 400

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
                (relation_id, entity_id, role_id, mechanism_id, parent_argument_id, property, property_value,
                 stance, claim, reasoning, weight, contributed_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (relation_id, entity_id, role_id, mechanism_id, parent_id, prop, prop_value,
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


# ── Entiteiten & relaties API ────────────────────────────────

@app.route("/api/entities", methods=["POST"])
def create_entity():
    """Nieuwe entiteit (node) toevoegen."""
    data = request.json
    if not data:
        return jsonify({"error": "Geen data"}), 400

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Naam is verplicht"}), 400

    etype = (data.get("type") or "").strip()
    if not etype:
        return jsonify({"error": "Type is verplicht"}), 400

    primary_role_id = data.get("primary_role_id") or None
    description = (data.get("description") or "").strip() or None
    active_from = (data.get("active_from") or "").strip() or None
    active_until = (data.get("active_until") or "").strip() or None
    contributed_by = (data.get("contributed_by") or "").strip() or "anoniem"

    conn = get_db()
    try:
        cur = conn.execute("""
            INSERT INTO entities (name, type, primary_role_id, description, active_from, active_until)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, etype, primary_role_id, description, active_from, active_until))
        eid = cur.lastrowid

        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('entities', ?, 'created', ?, ?, ?)
        """, (eid, contributed_by, json.dumps({"name": name, "type": etype}),
              "Nieuwe entiteit toegevoegd"))

        conn.commit()
        row = conn.execute("""
            SELECT e.id, e.name, e.type, e.description,
                   e.active_from, e.active_until, e.active,
                   r.name as role_name, r.category as filter_category
            FROM entities e
            LEFT JOIN roles r ON e.primary_role_id = r.id
            WHERE e.id = ?
        """, (eid,)).fetchone()
        conn.close()
        return jsonify(dict(row)), 201

    except sqlite3.IntegrityError as e:
        conn.close()
        msg = str(e)
        if "UNIQUE" in msg:
            return jsonify({"error": f"Er bestaat al een entiteit met de naam '{name}'"}), 400
        if "CHECK" in msg:
            return jsonify({"error": f"Ongeldig entiteittype: '{etype}'"}), 400
        return jsonify({"error": msg}), 400


@app.route("/api/relations", methods=["POST"])
def create_relation():
    """Nieuwe relatie (edge) tussen twee entiteiten toevoegen."""
    data = request.json
    if not data:
        return jsonify({"error": "Geen data"}), 400

    source_id = data.get("source_id")
    target_id = data.get("target_id")
    if not source_id or not target_id:
        return jsonify({"error": "Bron en doel zijn verplicht"}), 400
    if source_id == target_id:
        return jsonify({"error": "Bron en doel mogen niet dezelfde entiteit zijn"}), 400

    rtype = (data.get("relation_type") or "").strip()
    if not rtype:
        return jsonify({"error": "Relatietype is verplicht"}), 400

    mechanism_id = data.get("mechanism_id") or None
    description = (data.get("description") or "").strip() or None
    bidirectional = 1 if data.get("bidirectional") else 0
    active_from = (data.get("active_from") or "").strip() or None
    active_until = (data.get("active_until") or "").strip() or None
    contributed_by = (data.get("contributed_by") or "").strip() or "anoniem"

    def clamp01(v):
        if v in (None, ""):
            return None
        try:
            return min(1.0, max(0.0, float(v)))
        except (ValueError, TypeError):
            return None

    certainty = clamp01(data.get("certainty"))
    influence = clamp01(data.get("influence"))

    conn = get_db()
    for label, eid in (("Bron", source_id), ("Doel", target_id)):
        if not conn.execute("SELECT 1 FROM entities WHERE id = ?", (eid,)).fetchone():
            conn.close()
            return jsonify({"error": f"{label}-entiteit bestaat niet"}), 400

    try:
        cur = conn.execute("""
            INSERT INTO relations
                (source_id, target_id, relation_type, mechanism_id, description,
                 certainty, influence, bidirectional, active_from, active_until)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, target_id, rtype, mechanism_id, description,
              certainty, influence, bidirectional, active_from, active_until))
        rid = cur.lastrowid

        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('relations', ?, 'created', ?, ?, ?)
        """, (rid, contributed_by,
              json.dumps({"source_id": source_id, "target_id": target_id, "relation_type": rtype}),
              "Nieuwe relatie toegevoegd"))

        conn.commit()
        row = conn.execute("""
            SELECT r.id, r.source_id, r.target_id, r.relation_type,
                   r.certainty, r.influence, r.bidirectional, r.description,
                   r.active_from, r.active_until, r.active,
                   e1.name as source_name, e2.name as target_name,
                   m.name as mechanism_name, m.filter as mechanism_filter
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            LEFT JOIN mechanisms m ON r.mechanism_id = m.id
            WHERE r.id = ?
        """, (rid,)).fetchone()
        conn.close()
        return jsonify(dict(row)), 201

    except sqlite3.IntegrityError as e:
        conn.close()
        msg = str(e)
        if "CHECK" in msg:
            return jsonify({"error": f"Ongeldig relatietype of waarde: '{rtype}'"}), 400
        return jsonify({"error": msg}), 400


def _collect_argument_tree(conn, root_ids):
    """Verzamel alle argument-ids in de subbomen onder root_ids (incl. de roots).

    Vangt ook reacties op die alleen via parent_argument_id aan de boom hangen
    zonder zelf een relation_id/entity_id te dragen.
    """
    todo = list(root_ids)
    collected = set()
    while todo:
        aid = todo.pop()
        if aid in collected:
            continue
        collected.add(aid)
        rows = conn.execute(
            "SELECT id FROM arguments WHERE parent_argument_id = ?", (aid,)
        ).fetchall()
        todo.extend(row[0] for row in rows)
    return collected


def _delete_arguments(conn, arg_ids):
    """Verwijder argumenten en hun citaties; kinderen (hoger id) vóór ouders."""
    arg_ids = list(arg_ids)
    if not arg_ids:
        return
    placeholders = ",".join("?" * len(arg_ids))
    conn.execute(f"DELETE FROM citations WHERE argument_id IN ({placeholders})", arg_ids)
    # Een reactie heeft altijd een hoger id dan zijn parent (later aangemaakt),
    # dus aflopend verwijderen respecteert de foreign key naar parent_argument_id.
    for aid in sorted(arg_ids, reverse=True):
        conn.execute("DELETE FROM arguments WHERE id = ?", (aid,))


def _delete_relation_cascade(conn, rid):
    """Verwijder een relatie inclusief haar discussieboom en instantie-koppelingen."""
    direct = [row[0] for row in conn.execute(
        "SELECT id FROM arguments WHERE relation_id = ?", (rid,)).fetchall()]
    _delete_arguments(conn, _collect_argument_tree(conn, direct))
    conn.execute("DELETE FROM instantiations WHERE relation_id = ?", (rid,))
    conn.execute("DELETE FROM relations WHERE id = ?", (rid,))


@app.route("/api/relations/<int:rid>", methods=["DELETE"])
def delete_relation(rid):
    """Relatie definitief verwijderen (incl. bijbehorende argumenten/citaties)."""
    data = request.get_json(silent=True) or {}
    changed_by = (data.get("changed_by") or "").strip() or "admin"

    conn = get_db()
    row = conn.execute("""
        SELECT r.id, r.relation_type, e1.name AS source_name, e2.name AS target_name
        FROM relations r
        JOIN entities e1 ON r.source_id = e1.id
        JOIN entities e2 ON r.target_id = e2.id
        WHERE r.id = ?
    """, (rid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Relatie niet gevonden"}), 404

    try:
        _delete_relation_cascade(conn, rid)
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, reason)
            VALUES ('relations', ?, 'deleted', ?, ?, ?)
        """, (rid, changed_by,
              json.dumps({"source_name": row["source_name"], "target_name": row["target_name"],
                          "relation_type": row["relation_type"]}),
              "Relatie verwijderd (admin)"))
        conn.commit()
        conn.close()
        return jsonify({"id": rid, "deleted": True})
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 400


@app.route("/api/entities/<int:eid>", methods=["DELETE"])
def delete_entity(eid):
    """Entiteit definitief verwijderen.

    Verwijdert mee: alle relaties die de entiteit raken (incl. hun argumenten),
    argumenten direct op de entiteit, rol-koppelingen en bronvermeldingen.
    """
    data = request.get_json(silent=True) or {}
    changed_by = (data.get("changed_by") or "").strip() or "admin"

    conn = get_db()
    ent = conn.execute("SELECT id, name, type FROM entities WHERE id = ?", (eid,)).fetchone()
    if not ent:
        conn.close()
        return jsonify({"error": "Entiteit niet gevonden"}), 404

    try:
        rel_ids = [row[0] for row in conn.execute(
            "SELECT id FROM relations WHERE source_id = ? OR target_id = ?",
            (eid, eid)).fetchall()]
        for rid in rel_ids:
            _delete_relation_cascade(conn, rid)

        direct = [row[0] for row in conn.execute(
            "SELECT id FROM arguments WHERE entity_id = ?", (eid,)).fetchall()]
        _delete_arguments(conn, _collect_argument_tree(conn, direct))

        conn.execute("DELETE FROM entity_roles WHERE entity_id = ?", (eid,))
        conn.execute("DELETE FROM source_mentions WHERE entity_id = ?", (eid,))
        conn.execute("DELETE FROM instantiations WHERE entity_id = ?", (eid,))
        conn.execute("DELETE FROM entities WHERE id = ?", (eid,))

        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, reason)
            VALUES ('entities', ?, 'deleted', ?, ?, ?)
        """, (eid, changed_by, json.dumps({"name": ent["name"], "type": ent["type"]}),
              f"Entiteit verwijderd (admin); {len(rel_ids)} relatie(s) mee verwijderd"))
        conn.commit()
        conn.close()
        return jsonify({"id": eid, "deleted": True, "relations_deleted": len(rel_ids)})
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 400


# ── Theoretisch model: rollen & mechanismen ──────────────────

@app.route("/api/roles", methods=["POST"])
def create_role():
    """Nieuwe rol (theoretische node) toevoegen."""
    data = request.json or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Naam is verplicht"}), 400
    category = (data.get("category") or "").strip()
    if not category:
        return jsonify({"error": "Categorie is verplicht"}), 400
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "Beschrijving is verplicht"}), 400
    examples = (data.get("examples") or "").strip() or None
    contributed_by = (data.get("contributed_by") or "").strip() or "anoniem"

    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO roles (name, category, description, examples) VALUES (?, ?, ?, ?)",
            (name, category, description, examples))
        rid = cur.lastrowid
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('roles', ?, 'created', ?, ?, ?)
        """, (rid, contributed_by, json.dumps({"name": name, "category": category}),
              "Nieuwe rol toegevoegd"))
        conn.commit()
        row = dict(conn.execute(
            "SELECT id, name, category, description, examples FROM roles WHERE id = ?",
            (rid,)).fetchone())
        conn.close()
        return jsonify(row), 201
    except sqlite3.IntegrityError as e:
        conn.close()
        msg = str(e)
        if "UNIQUE" in msg:
            return jsonify({"error": f"Er bestaat al een rol met de naam '{name}'"}), 400
        if "CHECK" in msg:
            return jsonify({"error": f"Ongeldige categorie: '{category}'"}), 400
        return jsonify({"error": msg}), 400


@app.route("/api/roles/<int:rid>", methods=["DELETE"])
def delete_role(rid):
    """Rol verwijderen. Koppelingen worden losgemaakt (op NULL), niet de
    entiteiten of mechanismen zelf — die blijven bestaan.
    """
    data = request.get_json(silent=True) or {}
    changed_by = (data.get("changed_by") or "").strip() or "admin"

    conn = get_db()
    row = conn.execute("SELECT id, name FROM roles WHERE id = ?", (rid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Rol niet gevonden"}), 404

    try:
        ent_unlinked = conn.execute(
            "SELECT COUNT(*) FROM entities WHERE primary_role_id = ?", (rid,)).fetchone()[0]
        conn.execute("UPDATE entities SET primary_role_id = NULL WHERE primary_role_id = ?", (rid,))
        conn.execute("DELETE FROM entity_roles WHERE role_id = ?", (rid,))
        conn.execute("UPDATE mechanisms SET source_role_id = NULL WHERE source_role_id = ?", (rid,))
        conn.execute("UPDATE mechanisms SET target_role_id = NULL WHERE target_role_id = ?", (rid,))
        conn.execute("DELETE FROM instantiations WHERE role_id = ?", (rid,))
        # Literatuur-argumenten die direct op deze rol hingen (incl. discussieboom)
        direct = [r[0] for r in conn.execute(
            "SELECT id FROM arguments WHERE role_id = ?", (rid,)).fetchall()]
        _delete_arguments(conn, _collect_argument_tree(conn, direct))
        conn.execute("DELETE FROM roles WHERE id = ?", (rid,))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, reason)
            VALUES ('roles', ?, 'deleted', ?, ?, ?)
        """, (rid, changed_by, json.dumps({"name": row["name"]}),
              f"Rol verwijderd (admin); {ent_unlinked} entiteit(en) losgekoppeld"))
        conn.commit()
        conn.close()
        return jsonify({"id": rid, "deleted": True})
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 400


@app.route("/api/mechanisms", methods=["POST"])
def create_mechanism():
    """Nieuw mechanisme (theoretisch verband tussen twee rollen) toevoegen."""
    data = request.json or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Naam is verplicht"}), 400
    filt = (data.get("filter") or "").strip()
    if not filt:
        return jsonify({"error": "Filter is verplicht"}), 400
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"error": "Beschrijving is verplicht"}), 400
    effect = (data.get("effect") or "").strip()
    if not effect:
        return jsonify({"error": "Effect is verplicht"}), 400
    mechanism_type = (data.get("mechanism_type") or "").strip() or None
    source_role_id = data.get("source_role_id") or None
    target_role_id = data.get("target_role_id") or None
    contributed_by = (data.get("contributed_by") or "").strip() or "anoniem"

    conn = get_db()
    for label, role_id in (("Bron-rol", source_role_id), ("Doel-rol", target_role_id)):
        if role_id and not conn.execute("SELECT 1 FROM roles WHERE id = ?", (role_id,)).fetchone():
            conn.close()
            return jsonify({"error": f"{label} bestaat niet"}), 400

    try:
        cur = conn.execute("""
            INSERT INTO mechanisms
                (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, filt, mechanism_type, description, effect, source_role_id, target_role_id))
        mid = cur.lastrowid
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('mechanisms', ?, 'created', ?, ?, ?)
        """, (mid, contributed_by, json.dumps({"name": name, "filter": filt}),
              "Nieuw mechanisme toegevoegd"))
        conn.commit()
        row = dict(conn.execute("""
            SELECT id, name, filter, mechanism_type, description, effect,
                   source_role_id, target_role_id
            FROM mechanisms WHERE id = ?
        """, (mid,)).fetchone())
        conn.close()
        return jsonify(row), 201
    except sqlite3.IntegrityError as e:
        conn.close()
        msg = str(e)
        if "UNIQUE" in msg:
            return jsonify({"error": f"Er bestaat al een mechanisme met de naam '{name}'"}), 400
        if "CHECK" in msg:
            return jsonify({"error": "Ongeldige filter of mechanisme-type"}), 400
        return jsonify({"error": msg}), 400


@app.route("/api/mechanisms/<int:mid>", methods=["DELETE"])
def delete_mechanism(mid):
    """Mechanisme verwijderen. Praktijk-relaties die ernaar verwijzen blijven
    bestaan; alleen hun koppeling (mechanism_id) wordt losgemaakt.
    """
    data = request.get_json(silent=True) or {}
    changed_by = (data.get("changed_by") or "").strip() or "admin"

    conn = get_db()
    row = conn.execute("SELECT id, name FROM mechanisms WHERE id = ?", (mid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Mechanisme niet gevonden"}), 404

    try:
        rel_unlinked = conn.execute(
            "SELECT COUNT(*) FROM relations WHERE mechanism_id = ?", (mid,)).fetchone()[0]
        conn.execute("UPDATE relations SET mechanism_id = NULL WHERE mechanism_id = ?", (mid,))
        conn.execute("DELETE FROM instantiations WHERE mechanism_id = ?", (mid,))
        # Literatuur-argumenten die direct op dit mechanisme hingen (incl. discussieboom)
        direct = [r[0] for r in conn.execute(
            "SELECT id FROM arguments WHERE mechanism_id = ?", (mid,)).fetchall()]
        _delete_arguments(conn, _collect_argument_tree(conn, direct))
        conn.execute("DELETE FROM mechanisms WHERE id = ?", (mid,))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, reason)
            VALUES ('mechanisms', ?, 'deleted', ?, ?, ?)
        """, (mid, changed_by, json.dumps({"name": row["name"]}),
              f"Mechanisme verwijderd (admin); {rel_unlinked} relatie(s) losgekoppeld"))
        conn.commit()
        conn.close()
        return jsonify({"id": mid, "deleted": True, "relations_unlinked": rel_unlinked})
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 400


# ── Instantiaties (klasse <-> instantie + exemplariteit) ─────

@app.route("/api/instantiations", methods=["POST"])
def create_instantiation():
    """Koppel een praktijk-instantie aan een theoretische klasse.

    Geldige paren: rol<->entiteit of mechanisme<->relatie. Met een exemplariteit
    (0..1): hoe prototypisch is dit voorbeeld voor de klasse?
    """
    data = request.json or {}
    role_id = data.get("role_id") or None
    mechanism_id = data.get("mechanism_id") or None
    entity_id = data.get("entity_id") or None
    relation_id = data.get("relation_id") or None

    # precies één klasse en één instantie, met kloppend type-paar
    if bool(role_id) == bool(mechanism_id):
        return jsonify({"error": "Kies precies één klasse: een rol óf een mechanisme"}), 400
    if role_id and not entity_id:
        return jsonify({"error": "Een rol koppel je aan een entiteit"}), 400
    if mechanism_id and not relation_id:
        return jsonify({"error": "Een mechanisme koppel je aan een relatie"}), 400

    ex = data.get("exemplarity")
    try:
        ex = 1.0 if ex in (None, "") else min(1.0, max(0.0, float(ex)))
    except (ValueError, TypeError):
        ex = 1.0
    notes = (data.get("notes") or "").strip() or None
    contributed_by = (data.get("contributed_by") or "").strip() or "admin"

    conn = get_db()
    # Bestaanscontroles
    checks = ([("Rol", "roles", role_id)] if role_id else [("Mechanisme", "mechanisms", mechanism_id)])
    checks += ([("Entiteit", "entities", entity_id)] if entity_id else [("Relatie", "relations", relation_id)])
    for label, table, ident in checks:
        if not conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", (ident,)).fetchone():
            conn.close()
            return jsonify({"error": f"{label} bestaat niet"}), 400

    try:
        cur = conn.execute("""
            INSERT INTO instantiations (role_id, mechanism_id, entity_id, relation_id, exemplarity, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (role_id, mechanism_id, entity_id, relation_id, ex, notes))
        iid = cur.lastrowid
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('instantiations', ?, 'created', ?, ?, ?)
        """, (iid, contributed_by,
              json.dumps({"role_id": role_id, "mechanism_id": mechanism_id,
                          "entity_id": entity_id, "relation_id": relation_id, "exemplarity": ex}),
              "Instantie aan klasse gekoppeld"))
        conn.commit()
        row = dict(conn.execute(
            "SELECT id, role_id, mechanism_id, entity_id, relation_id, exemplarity, notes "
            "FROM instantiations WHERE id = ?", (iid,)).fetchone())
        conn.close()
        return jsonify(row), 201
    except sqlite3.IntegrityError as e:
        conn.close()
        msg = str(e)
        if "UNIQUE" in msg:
            return jsonify({"error": "Deze koppeling bestaat al"}), 400
        return jsonify({"error": msg}), 400


@app.route("/api/instantiations/<int:iid>", methods=["DELETE"])
def delete_instantiation(iid):
    """Een instantie-koppeling losmaken (de entiteit/relatie zelf blijft bestaan)."""
    data = request.get_json(silent=True) or {}
    changed_by = (data.get("changed_by") or "").strip() or "admin"

    conn = get_db()
    row = conn.execute("SELECT id FROM instantiations WHERE id = ?", (iid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Koppeling niet gevonden"}), 404
    conn.execute("DELETE FROM instantiations WHERE id = ?", (iid,))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, reason)
        VALUES ('instantiations', ?, 'deleted', ?, ?)
    """, (iid, changed_by, "Instantie-koppeling losgemaakt"))
    conn.commit()
    conn.close()
    return jsonify({"id": iid, "deleted": True})


# ── Afgeleide scores (live herberekening) ────────────────────

@app.route("/api/scores")
def get_scores():
    """Herbereken de volledige scoringsketen en geef alle afgeleide scores terug.

    De UI roept dit aan na een bewerking (argument, instantie) om panelen en de
    visuele codering te verversen zonder de hele pagina te regenereren.
    """
    conn = get_db()
    scores = scoring.compute_all_scores(conn)
    conn.close()
    return jsonify(scores)


if __name__ == "__main__":
    print(f"Database: {DB_PATH}")
    print(f"Open: http://localhost:5000")
    app.run(debug=True, port=5000)
