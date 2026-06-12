"""Propaganda Model — webserver met discussieboom-API.

Start: python3 server.py
Open:  http://localhost:5000
"""
import functools
import json
import os
import sqlite3
from pathlib import Path
from flask import Flask, g, jsonify, request, send_file, session

import auth  # wachtwoord-/token-hashing (M0.6)
import scoring  # scoringsketen: afgeleide praktijk- en theoriescores
import validation  # gezondheids-/consistentiechecks, gedeeld met scripts/validate_model.py

DB_PATH = Path(__file__).parent / "data" / "propaganda_model.db"
WEB_PATH = Path(__file__).parent / "web"
SECRET_KEY_PATH = Path(__file__).parent / "data" / "secret_key"

app = Flask(__name__, static_folder=str(WEB_PATH), static_url_path="/static")


def _secret_key():
    """Sessiesleutel op schijf (gitignored), zodat sessies een herstart overleven."""
    if not SECRET_KEY_PATH.exists():
        SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SECRET_KEY_PATH.write_bytes(os.urandom(32))
        SECRET_KEY_PATH.chmod(0o600)
    return SECRET_KEY_PATH.read_bytes()


app.secret_key = _secret_key()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Identiteit & poorten (M0.6) ──────────────────────────────
# Lezen blijft open. Schrijven vereist een account (mens of agent); de
# attributie volgt áltijd de ingelogde gebruiker, nooit een payload-veld.
# Theorielaag-wijzigingen en DELETEs vereisen maintainer.

ROLE_ORDER = {"bijdrager": 1, "reviewer": 2, "maintainer": 3}


def _zoek_user(conn):
    """Bearer-token gaat vóór de sessie (agents en Claude Code sturen Bearer).

    Een meegestuurd maar onbekend token valt bewust níét terug op de sessie.
    """
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return conn.execute(
            "SELECT * FROM users WHERE token_hash = ? AND active",
            (auth.hash_token(header[len("Bearer "):]),)).fetchone()
    uid = session.get("user_id")
    if uid is not None:
        return conn.execute(
            "SELECT * FROM users WHERE id = ? AND active", (uid,)).fetchone()
    return None


def require_user(min_rol="bijdrager"):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            conn = get_db()
            rij = _zoek_user(conn)
            conn.close()
            if rij is None:
                return jsonify({"error": "Inloggen vereist: sessie (/login) of "
                                         "Authorization: Bearer <token>"}), 401
            if ROLE_ORDER.get(rij["role"], 0) < ROLE_ORDER[min_rol]:
                return jsonify({"error": f"Rol '{min_rol}' of hoger vereist "
                                         f"(jouw rol: {rij['role']})"}), 403
            g.user = dict(rij)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/login")
def login_page():
    return send_file(WEB_PATH / "login.html")


@app.route("/account")
def account_page():
    return send_file(WEB_PATH / "account.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    username = (data.get("username") or "").strip()
    wachtwoord = data.get("password") or ""
    conn = get_db()
    rij = conn.execute("SELECT * FROM users WHERE username = ? AND active",
                       (username,)).fetchone()
    if (rij is None or rij["kind"] != "mens"
            or not auth.verify_password(wachtwoord, rij["password_hash"])):
        conn.close()
        return jsonify({"error": "Onbekende gebruiker of onjuist wachtwoord"}), 401
    conn.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
                 (rij["id"],))
    conn.commit()
    conn.close()
    session["user_id"] = rij["id"]
    return jsonify({"username": rij["username"], "role": rij["role"], "kind": rij["kind"]})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user_id", None)
    return jsonify({"ok": True})


@app.route("/api/me")
def api_me():
    conn = get_db()
    rij = _zoek_user(conn)
    conn.close()
    if rij is None:
        return jsonify({"error": "Niet ingelogd"}), 401
    return jsonify({"username": rij["username"], "role": rij["role"], "kind": rij["kind"],
                    "provenance": rij["provenance"], "created_at": rij["created_at"],
                    "last_login_at": rij["last_login_at"],
                    "heeft_token": rij["token_hash"] is not None})


@app.route("/api/tokens", methods=["POST"])
@require_user()
def api_tokens():
    """Genereer/roteer het eigen API-token. De plaintext wordt één keer getoond;
    opgeslagen wordt alleen de sha256-hash."""
    token = auth.new_token()
    conn = get_db()
    conn.execute("UPDATE users SET token_hash = ? WHERE id = ?",
                 (auth.hash_token(token), g.user["id"]))
    conn.commit()
    conn.close()
    return jsonify({"token": token,
                    "let_op": "Bewaar dit token nu — het wordt niet opgeslagen en "
                              "vervangt een eventueel ouder token."}), 201


# ── Pagina's ─────────────────────────────────────────────────

@app.route("/")
def index():
    return send_file(WEB_PATH / "index.html")


# ── Argumenten API ───────────────────────────────────────────

@app.route("/api/arguments")
def get_arguments():
    """Haal argumenten op voor een relatie, entiteit, rol, mechanisme of emergent veld.

    Replies dragen geen eigen doel (M1.1) — de recursieve CTE haalt daarom de hele
    subboom op onder de root-argumenten van het gevraagde doel.
    """
    targets = {
        "relation_id": request.args.get("relation_id", type=int),
        "entity_id": request.args.get("entity_id", type=int),
        "role_id": request.args.get("role_id", type=int),
        "mechanism_id": request.args.get("mechanism_id", type=int),
        "emergent_effect_id": request.args.get("emergent_effect_id", type=int),
    }
    column = next((k for k, v in targets.items() if v), None)
    if not column:
        return jsonify([])

    conn = get_db()
    rows = conn.execute(f"""
        WITH RECURSIVE boom(id) AS (
            SELECT id FROM arguments WHERE {column} = ?
            UNION
            SELECT a.id FROM arguments a JOIN boom b ON a.parent_argument_id = b.id
        )
        SELECT a.*, c.id as citation_id, c.quote, c.page, c.section, c.context as cite_context,
               s.title as source_title, s.author as source_author, s.reliability
        FROM arguments a
        JOIN boom ON a.id = boom.id
        LEFT JOIN citations c ON c.argument_id = a.id
        LEFT JOIN sources s ON c.source_id = s.id
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
                "role_id": row["role_id"],
                "mechanism_id": row["mechanism_id"],
                "emergent_effect_id": row["emergent_effect_id"],
                "parent_argument_id": row["parent_argument_id"],
                "property": row["property"],
                "property_value": row["property_value"],
                "stance": row["stance"],
                "claim": row["claim"],
                "reasoning": row["reasoning"],
                "weight": row["weight"],
                "status": row["status"],
                "self_merged": row["self_merged"],
                "objection_type": row["objection_type"],
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
@require_user()
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
    emergent_effect_id = data.get("emergent_effect_id")  # literatuur-argument over een emergent veld (theorie)
    doelen = (relation_id, entity_id, role_id, mechanism_id, emergent_effect_id)

    parent_id = data.get("parent_argument_id")
    # Doelregel (M1.1): een root draagt ≥ 1 doel; een reply draagt GÉÉN eigen doel —
    # zijn stance is relatief aan de parent en zijn kracht stroomt via de boom.
    if parent_id is None and not any(doelen):
        return jsonify({"error": "relation_id, entity_id, role_id, mechanism_id "
                                 "of emergent_effect_id is verplicht"}), 400
    if parent_id is not None and any(doelen):
        return jsonify({"error": "Een reactie draagt geen eigen doel: haar stance is "
                                 "relatief aan de parent (boomsemantiek, M1.1)"}), 400

    prop = data.get("property")
    prop_value = data.get("property_value")
    if prop == "compositie" and not emergent_effect_id:
        return jsonify({"error": "property 'compositie' hoort bij een emergent veld "
                                 "(emergent_effect_id)"}), 400
    if prop and parent_id is not None:
        return jsonify({"error": "Een reactie draagt geen property: aspect-argumenten "
                                 "richten zich als root-argument op het doel zelf"}), 400

    # M1.8: machineleesbare ondergraving-classificatie, alleen op een
    # contradicting-reply ("de redenering van de parent deugt niet").
    objection_type = data.get("objection_type") or None
    if objection_type and (parent_id is None or stance != "contradicting"):
        return jsonify({"error": "objection_type hoort bij een contradicting-reactie "
                                 "(ondergraving van de parent)"}), 400

    reasoning = (data.get("reasoning") or "").strip() or None
    weight = data.get("weight")
    contributed_by = g.user["username"]  # attributie volgt de ingelogde gebruiker

    if weight is not None:
        try:
            weight = float(weight)
            if not 0 <= weight <= 1:
                weight = None
        except (ValueError, TypeError):
            weight = None

    # Citaties mogen direct meekomen (één call voor agents); elke citatie vereist source_id.
    citaties = data.get("citations") or []
    if not isinstance(citaties, list):
        return jsonify({"error": "citations moet een lijst zijn"}), 400
    for c in citaties:
        if not isinstance(c, dict) or not c.get("source_id"):
            return jsonify({"error": "Elke citatie vereist een source_id"}), 400

    # Citatiepoort (M0.3): een voor/tegen-ROOT-argument zonder citatie telt pas
    # volwaardig mee na bronvermelding; 'contextual' mag bronloos, en een reply ook —
    # een ondergraving wijst een logisch gat aan en vergt geen tegenbron (M1.8).
    if parent_id is None and stance in ("supporting", "contradicting") and not citaties:
        status = "bronvermelding_nodig"
    else:
        status = "ongecontroleerd"

    conn = get_db()
    if parent_id is not None and not conn.execute(
            "SELECT 1 FROM arguments WHERE id = ?", (parent_id,)).fetchone():
        conn.close()
        return jsonify({"error": f"Parent-argument {parent_id} bestaat niet"}), 400
    for c in citaties:
        if not conn.execute("SELECT 1 FROM sources WHERE id = ?", (c["source_id"],)).fetchone():
            conn.close()
            return jsonify({"error": f"Bron {c['source_id']} bestaat niet"}), 400

    try:
        cur = conn.execute("""
            INSERT INTO arguments
                (relation_id, entity_id, role_id, mechanism_id, emergent_effect_id,
                 parent_argument_id, property, property_value,
                 stance, claim, reasoning, weight, status, objection_type, contributed_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (relation_id, entity_id, role_id, mechanism_id, emergent_effect_id,
              parent_id, prop, prop_value,
              stance, claim, reasoning, weight, status, objection_type, contributed_by))
        arg_id = cur.lastrowid

        for c in citaties:
            conn.execute("""
                INSERT INTO citations (argument_id, source_id, quote, page, section, context)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (arg_id, c["source_id"], c.get("quote"), c.get("page"),
                  c.get("section"), c.get("context")))

        # Log in edit_log
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('arguments', ?, 'created', ?, ?, ?)
        """, (arg_id, contributed_by,
              json.dumps({"claim": claim, "stance": stance, "status": status,
                          "citaties": len(citaties)}),
              f"Nieuw argument: {stance}"))

        conn.commit()
        result = dict(conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone())
        conn.close()
        return jsonify(result), 201

    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400


@app.route("/api/arguments/<int:arg_id>/status", methods=["PATCH"])
@require_user("reviewer")
def update_argument_status(arg_id):
    """Verificatie-status van een argument bijwerken (review-stap: reviewer of hoger)."""
    data = request.json
    new_status = data.get("status")
    valid = ("ongecontroleerd", "bronvermelding_nodig", "betwist", "geverifieerd",
             "verouderd", "verworpen")
    if new_status not in valid:
        return jsonify({"error": f"Status moet een van {valid} zijn"}), 400

    conn = get_db()
    old = conn.execute("SELECT status, contributed_by FROM arguments WHERE id = ?",
                       (arg_id,)).fetchone()
    if not old:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404

    # Zelf-merge (n=1): eigen argument verifiëren mag, maar draagt een vlag
    # zodat het later herauditeerbaar is. Verificatie door een ánder wist de vlag.
    self_merged = (new_status == "geverifieerd"
                   and old["contributed_by"] == g.user["username"])
    if new_status == "geverifieerd":
        conn.execute("UPDATE arguments SET status = ?, self_merged = ? WHERE id = ?",
                     (new_status, self_merged, arg_id))
    else:
        conn.execute("UPDATE arguments SET status = ? WHERE id = ?", (new_status, arg_id))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('arguments', ?, ?, ?, ?, ?, ?)
    """, (arg_id, "verified" if new_status == "geverifieerd" else "disputed",
          g.user["username"],
          json.dumps({"status": old["status"]}),
          json.dumps({"status": new_status}),
          "zelf-merge (n=1)" if self_merged else None))

    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "status": new_status, "self_merged": self_merged})


@app.route("/api/sources")
def get_sources():
    """Lijst van alle bronnen (voor citaat-selectie)."""
    conn = get_db()
    rows = conn.execute("SELECT id, title, author, source_type, reliability FROM sources ORDER BY author").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/citations", methods=["POST"])
@require_user()
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
    arg = conn.execute("SELECT id, status FROM arguments WHERE id = ?", (argument_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if not conn.execute("SELECT 1 FROM sources WHERE id = ?", (source_id,)).fetchone():
        conn.close()
        return jsonify({"error": f"Bron {source_id} bestaat niet"}), 400

    try:
        cur = conn.execute("""
            INSERT INTO citations (argument_id, source_id, quote, page, section, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (argument_id, source_id, data.get("quote"), data.get("page"),
              data.get("section"), data.get("context")))
        cid = cur.lastrowid

        # Citatiepoort (M0.3): de eerste citatie heft 'bronvermelding_nodig' op.
        # Alleen die overgang — verificatie blijft een menselijke review-stap.
        nieuwe_status = None
        if arg["status"] == "bronvermelding_nodig":
            nieuwe_status = "ongecontroleerd"
            conn.execute("UPDATE arguments SET status = ? WHERE id = ?",
                         (nieuwe_status, argument_id))
            conn.execute("""
                INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
                VALUES ('arguments', ?, 'updated', 'citatiepoort', ?, ?, ?)
            """, (argument_id,
                  json.dumps({"status": "bronvermelding_nodig"}),
                  json.dumps({"status": nieuwe_status}),
                  f"Automatisch: citatie #{cid} toegevoegd"))

        conn.commit()
        conn.close()
        return jsonify({"id": cid, "argument_status": nieuwe_status or arg["status"]}), 201
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400


# ── Entiteiten & relaties API ────────────────────────────────

@app.route("/api/entities", methods=["POST"])
@require_user()
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
    contributed_by = g.user["username"]

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
@require_user()
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
    contributed_by = g.user["username"]

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
@require_user("maintainer")
def delete_relation(rid):
    """Relatie definitief verwijderen (incl. bijbehorende argumenten/citaties)."""
    changed_by = g.user["username"]

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
@require_user("maintainer")
def delete_entity(eid):
    """Entiteit definitief verwijderen.

    Verwijdert mee: alle relaties die de entiteit raken (incl. hun argumenten),
    argumenten direct op de entiteit, rol-koppelingen en bronvermeldingen.
    """
    changed_by = g.user["username"]

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
@require_user("maintainer")
def create_role():
    """Nieuwe rol (theoretische node) toevoegen (theorielaag: maintainer)."""
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
    contributed_by = g.user["username"]

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
@require_user("maintainer")
def delete_role(rid):
    """Rol verwijderen. Koppelingen worden losgemaakt (op NULL), niet de
    entiteiten of mechanismen zelf — die blijven bestaan.
    """
    changed_by = g.user["username"]

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
@require_user("maintainer")
def create_mechanism():
    """Nieuw mechanisme toevoegen (theorielaag: maintainer)."""
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
    contributed_by = g.user["username"]

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
@require_user("maintainer")
def delete_mechanism(mid):
    """Mechanisme verwijderen. Praktijk-relaties die ernaar verwijzen blijven
    bestaan; alleen hun koppeling (mechanism_id) wordt losgemaakt.
    """
    changed_by = g.user["username"]

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
@require_user()
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
    contributed_by = g.user["username"]

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
@require_user("maintainer")
def delete_instantiation(iid):
    """Een instantie-koppeling losmaken (de entiteit/relatie zelf blijft bestaan)."""
    changed_by = g.user["username"]

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

@app.route("/api/health")
def get_health():
    """Gezondheidsdashboard (M0.5): zelfde checkfuncties als de validator-CLI,
    dus de cijfers hier zijn per constructie identiek aan scripts/validate_model.py.
    (Zonder linkrot-check; die blijft CLI-only achter --network.)"""
    conn = get_db()
    rapport = validation.run_all(conn)
    conn.close()
    return jsonify(rapport)


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
