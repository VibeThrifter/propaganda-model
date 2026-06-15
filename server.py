"""Propaganda Model — webserver met discussieboom-API.

Start: python3 server.py
Open:  http://localhost:5000
"""
import datetime
import difflib
import functools
import json
import os
import re
import sqlite3
import time
from pathlib import Path
from flask import Flask, g, jsonify, request, send_file, session

import auth  # wachtwoord-/token-hashing (M0.6)
import scoring  # scoringsketen: afgeleide praktijk- en theoriescores
import validation  # gezondheids-/consistentiechecks, gedeeld met scripts/validate_model.py
import voorstellen  # RfC's & granulariteitsbeheer (M2.3/M2.6), gedeeld met de tests

DB_PATH = Path(__file__).parent / "data" / "propaganda_model.db"
WEB_PATH = Path(__file__).parent / "web"
SECRET_KEY_PATH = Path(__file__).parent / "data" / "secret_key"
BRIDGING_PATH = Path(__file__).parent / "data" / "bridging.json"
RELEASES_PATH = Path(__file__).parent / "releases"

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

# ── Rate limits (M2.4): schrijfacties per account per minuut ──
# In-memory (één serverproces); een herstart leegt de emmers — acceptabel,
# de poort beschermt tegen score-manipulatie door volume, niet tegen DoS.
RATE_LIMITS = {"bijdrager": 30, "reviewer": 60, "maintainer": 120}
RATE_WINDOW = 60.0
_rate_emmers = {}


def _rate_limit_ok(user) -> bool:
    nu = time.monotonic()
    emmer = _rate_emmers.setdefault(user["id"], [])
    emmer[:] = [t for t in emmer if nu - t < RATE_WINDOW]
    if len(emmer) >= RATE_LIMITS.get(user["role"], 30):
        return False
    emmer.append(nu)
    return True


def _filterrollen(conn, user_id) -> dict:
    return {r["filter"]: r["rol"] for r in conn.execute(
        "SELECT filter, rol FROM user_filter_rollen WHERE user_id = ?", (user_id,))}


def heeft_rol(conn, user, min_rol, filters=None) -> bool:
    """Effectieve rol (M2.1): de globale rol, of een filterrol die de drempel haalt.

    ``filters`` is een iterable filternamen (bv. de filters van het doel van een
    argument); een reviewer-voor-'sourcing' mag binnen sourcing statusbesluiten nemen.
    """
    if ROLE_ORDER.get(user["role"], 0) >= ROLE_ORDER[min_rol]:
        return True
    if filters:
        per = _filterrollen(conn, user["id"])
        return any(ROLE_ORDER.get(per.get(f), 0) >= ROLE_ORDER[min_rol]
                   for f in filters if f)
    return False


def _filters_van_argument(conn, arg_id) -> list:
    """De filter(s) waaronder het doel van een argument valt (via de root)."""
    rij = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    while rij and rij["parent_argument_id"] is not None:
        rij = conn.execute("SELECT * FROM arguments WHERE id = ?",
                           (rij["parent_argument_id"],)).fetchone()
    if rij is None:
        return []
    fs = set()
    if rij["mechanism_id"]:
        r = conn.execute("SELECT filter FROM mechanisms WHERE id = ?",
                         (rij["mechanism_id"],)).fetchone()
        if r:
            fs.add(r["filter"])
    if rij["role_id"]:
        r = conn.execute("SELECT category FROM roles WHERE id = ?",
                         (rij["role_id"],)).fetchone()
        if r:
            fs.add(r["category"])
    if rij["emergent_effect_id"]:
        r = conn.execute("SELECT category FROM emergent_effects WHERE id = ?",
                         (rij["emergent_effect_id"],)).fetchone()
        if r:
            fs.add(r["category"])
    if rij["relation_id"]:
        r = conn.execute("""SELECT m.filter FROM relations rel
                            JOIN mechanisms m ON m.id = rel.mechanism_id
                            WHERE rel.id = ?""", (rij["relation_id"],)).fetchone()
        if r:
            fs.add(r["filter"])
    if rij["entity_id"]:
        r = conn.execute("""SELECT ro.category FROM entities e
                            JOIN roles ro ON ro.id = e.primary_role_id
                            WHERE e.id = ?""", (rij["entity_id"],)).fetchone()
        if r:
            fs.add(r["category"])
    return [f for f in fs if f]


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
            # M2.4: rate limit per account op schrijfacties
            if (request.method in ("POST", "PATCH", "DELETE")
                    and not _rate_limit_ok(g.user)):
                return jsonify({"error": "Rate limit bereikt: maximaal "
                                         f"{RATE_LIMITS.get(g.user['role'], 30)} "
                                         "schrijfacties per minuut"}), 429
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/login")
def login_page():
    return send_file(WEB_PATH / "login.html")


@app.route("/account")
def account_page():
    return send_file(WEB_PATH / "account.html")


@app.route("/overleg")
def overleg_page():
    """Overlegpagina (Wikipedia-stijl 'Overleg'): alle discussiedraden én open
    voorstellen/RfC's op een eigen volledige pagina, los van de netwerkviz."""
    return send_file(WEB_PATH / "overleg.html")


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

    # Ratings (M2.5) per argument: tellingen + de eigen stem van de ingelogde
    # gebruiker, zodat de viz de duim-toggle kan tonen (un-voten = nogmaals op je
    # eigen stem klikken). Lezen is open, dus de gebruiker kan ontbreken.
    user = _zoek_user(conn)
    mij = user["username"] if user else None
    for a in args_map.values():
        a["ratings"] = {"mens": {"nuttig": 0, "niet_nuttig": 0},
                        "agent": {"nuttig": 0, "niet_nuttig": 0}}
        a["mijn_oordeel"] = None
    if args_map:
        qs = ",".join("?" * len(args_map))
        for r in conn.execute(f"""
            SELECT ar.argument_id, ar.rater, ar.oordeel, u.kind
            FROM argument_ratings ar JOIN users u ON u.username = ar.rater
            WHERE ar.argument_id IN ({qs})
        """, list(args_map.keys())).fetchall():
            a = args_map[r["argument_id"]]
            a["ratings"][r["kind"]][r["oordeel"]] += 1
            if mij and r["rater"] == mij:
                a["mijn_oordeel"] = r["oordeel"]

    conn.close()
    return jsonify(list(args_map.values()))


@app.route("/api/discussion_index")
def discussion_index():
    """Index van alle discussiethreads voor de full-page discussie-UI: elk doel
    (relatie/entiteit/rol/mechanisme/emergent veld) met minstens één root-argument,
    gegroepeerd per soort, met tellingen (totaal + nog 'voorgesteld'). Lezen is
    open. Replies dragen geen doel (M1.1), dus dit telt root-claims per doel."""
    conn = get_db()

    def groepeer(sql):
        return [dict(r) for r in conn.execute(sql).fetchall()]

    relaties = groepeer("""
        SELECT r.id,
               e1.name || ' → ' || e2.name || ' (' || r.relation_type || ')' AS label,
               COALESCE(m.filter, '') AS filter,
               COUNT(*) AS n,
               SUM(CASE WHEN a.status = 'voorgesteld' THEN 1 ELSE 0 END) AS n_open
        FROM arguments a
        JOIN relations r ON a.relation_id = r.id
        JOIN entities e1 ON r.source_id = e1.id
        JOIN entities e2 ON r.target_id = e2.id
        LEFT JOIN mechanisms m ON r.mechanism_id = m.id
        GROUP BY r.id ORDER BY label
    """)

    mechanismen = groepeer("""
        SELECT t.id, t.name AS label, COALESCE(t.filter, '') AS filter, COUNT(*) AS n,
               SUM(CASE WHEN a.status = 'voorgesteld' THEN 1 ELSE 0 END) AS n_open
        FROM arguments a JOIN mechanisms t ON a.mechanism_id = t.id
        GROUP BY t.id ORDER BY label
    """)

    def simpel(tabel, kol):
        return groepeer(f"""
            SELECT t.id, t.name AS label, COUNT(*) AS n,
                   SUM(CASE WHEN a.status = 'voorgesteld' THEN 1 ELSE 0 END) AS n_open
            FROM arguments a JOIN {tabel} t ON a.{kol} = t.id
            GROUP BY t.id ORDER BY n DESC, label
        """)

    emergente_velden = groepeer("""
        SELECT t.id, COALESCE(t.label, t.name) AS label, COUNT(*) AS n,
               SUM(CASE WHEN a.status = 'voorgesteld' THEN 1 ELSE 0 END) AS n_open
        FROM arguments a JOIN emergent_effects t ON a.emergent_effect_id = t.id
        GROUP BY t.id ORDER BY n DESC, label
    """)

    uit = {
        "relaties": relaties,
        "entiteiten": simpel("entities", "entity_id"),
        "rollen": simpel("roles", "role_id"),
        "mechanismen": mechanismen,
        "emergente_velden": emergente_velden,
    }
    conn.close()
    return jsonify(uit)


# Filter-enum voor classificatie-aspect 'filter' (unie van de roles- en
# mechanisms-CHECK in schema.sql); property_value moet hier een van zijn.
FILTERS = {"eigendom", "advertentie", "sourcing", "flak", "ideologie",
           "cross_filter", "systeemactor", "tegenmacht", "overig"}


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
    # Classificatiedebat (telt als aspect, niet in de zekerheids-balans):
    #   'filter'    — bij welke propagandafilter hoort dit mechanisme/deze rol?
    #   'mechanism' — bij welk mechanisme hoort deze relatie? (waarde = mechanisme-ID)
    if prop == "filter":
        if not (mechanism_id or role_id):
            return jsonify({"error": "property 'filter' hoort bij een mechanisme of rol "
                                     "(mechanism_id of role_id)"}), 400
        if prop_value not in FILTERS:
            return jsonify({"error": "Ongeldige filter. Kies uit: "
                                     + ", ".join(sorted(FILTERS))}), 400
    if prop == "mechanism":
        if not relation_id:
            return jsonify({"error": "property 'mechanism' hoort bij een relatie "
                                     "(relation_id) — welk mechanisme hoort erbij?"}), 400
        if not (str(prop_value or "").isdigit()):
            return jsonify({"error": "property_value voor 'mechanism' moet een "
                                     "mechanisme-ID zijn (rename-vast)"}), 400
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
    # Een geflagde ondergraving (drogreden/foute logica) is geen kaal label: ze moet
    # de aangevochten redeneerstap benoemen, anders is het zelf een loze aanklacht.
    if objection_type and not reasoning:
        return jsonify({"error": "Een ondergraving met een objection_type vereist een "
                                 "onderbouwing: benoem in 'reasoning' de aangevochten "
                                 "redeneerstap"}), 400
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

    # Voorstel-workflow (M2.2): elk argument landt als 'voorgesteld' en telt in niets
    # mee tot een reviewer merget. De citatiepoort (M0.3) wordt op het merge-moment
    # toegepast (→ 'bronvermelding_nodig' of 'ongecontroleerd').
    status = "voorgesteld"

    conn = get_db()
    if parent_id is not None and not conn.execute(
            "SELECT 1 FROM arguments WHERE id = ?", (parent_id,)).fetchone():
        conn.close()
        return jsonify({"error": f"Parent-argument {parent_id} bestaat niet"}), 400
    for c in citaties:
        if not conn.execute("SELECT 1 FROM sources WHERE id = ?", (c["source_id"],)).fetchone():
            conn.close()
            return jsonify({"error": f"Bron {c['source_id']} bestaat niet"}), 400

    # Classificatie-aspect 'mechanism': de voorgestelde mechanisme-ID moet bestaan.
    if prop == "mechanism" and not conn.execute(
            "SELECT 1 FROM mechanisms WHERE id = ?", (int(prop_value),)).fetchone():
        conn.close()
        return jsonify({"error": f"Mechanisme {prop_value} bestaat niet"}), 400

    # Duplicaatdetectie (M2.4): vergelijk de claim met bestaande root-argumenten op
    # hetzelfde doel (stdlib-tekstgelijkenis; bewust geen externe embeddings).
    if parent_id is None and not data.get("negeer_duplicaten"):
        doel_map = {"relation_id": relation_id, "entity_id": entity_id, "role_id": role_id,
                    "mechanism_id": mechanism_id, "emergent_effect_id": emergent_effect_id}
        doelkolom = next(k for k, v in doel_map.items() if v)
        kandidaten = []
        for rij in conn.execute(
                f"SELECT id, claim, status FROM arguments WHERE {doelkolom} = ? "
                "AND parent_argument_id IS NULL", (doel_map[doelkolom],)):
            gelijkenis = difflib.SequenceMatcher(
                None, claim.lower(), (rij["claim"] or "").lower()).ratio()
            if gelijkenis >= 0.85:
                kandidaten.append({"id": rij["id"], "claim": rij["claim"],
                                   "status": rij["status"], "gelijkenis": round(gelijkenis, 2)})
        if kandidaten:
            conn.close()
            return jsonify({"error": "Mogelijke duplicaat-claim op dit doel; dien opnieuw "
                                     "in met negeer_duplicaten=true als dit echt een "
                                     "nieuwe claim is",
                            "duplicaat_kandidaten": kandidaten}), 409

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
@require_user()
def update_argument_status(arg_id):
    """Verificatie-status bijwerken (review-stap: reviewer of hoger, globaal of
    per filter — M2.1). Regels:
      - niemand verifieert eigen werk (M2.1): auteur → 'geverifieerd' wordt geweigerd;
      - een 'voorgesteld' argument verlaat die status alleen via merge (M2.2) of
        als 'verworpen' (afwijzing).
    """
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
    if not heeft_rol(conn, g.user, "reviewer", _filters_van_argument(conn, arg_id)):
        conn.close()
        return jsonify({"error": "Statusbesluiten vereisen reviewer of hoger "
                                 "(globaal of voor het filter van dit doel)"}), 403
    if old["status"] == "voorgesteld" and new_status != "verworpen":
        conn.close()
        return jsonify({"error": "Een voorstel telt pas mee na merge: gebruik "
                                 f"POST /api/arguments/{arg_id}/merge (of wijs af "
                                 "met status 'verworpen')"}), 400
    if new_status == "geverifieerd" and old["contributed_by"] == g.user["username"]:
        conn.close()
        return jsonify({"error": "Niemand verifieert eigen werk (M2.1): laat een "
                                 "andere reviewer dit argument beoordelen"}), 403

    # Verificatie gebeurt per constructie door een ander dan de auteur (zie boven);
    # de heraudit wist daarmee een eventuele oude zelf-merge-vlag.
    if new_status == "geverifieerd":
        conn.execute("UPDATE arguments SET status = ?, self_merged = 0 WHERE id = ?",
                     (new_status, arg_id))
    else:
        conn.execute("UPDATE arguments SET status = ? WHERE id = ?", (new_status, arg_id))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('arguments', ?, ?, ?, ?, ?, ?)
    """, (arg_id, "verified" if new_status == "geverifieerd" else "disputed",
          g.user["username"],
          json.dumps({"status": old["status"]}),
          json.dumps({"status": new_status}), None))

    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "status": new_status})


@app.route("/api/arguments/<int:arg_id>/merge", methods=["POST"])
@require_user()
def merge_argument(arg_id):
    """Voorstel mergen (M2.2): 'voorgesteld' → 'ongecontroleerd', of
    'bronvermelding_nodig' als de citatiepoort (M0.3) dat eist. Reviewer of hoger;
    zelf-merge is toegestaan (n=1) maar zet de self_merged-vlag (§6.1).
    """
    conn = get_db()
    arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if arg["status"] != "voorgesteld":
        conn.close()
        return jsonify({"error": f"Alleen 'voorgesteld' is mergebaar "
                                 f"(huidige status: {arg['status']})"}), 400
    if not heeft_rol(conn, g.user, "reviewer", _filters_van_argument(conn, arg_id)):
        conn.close()
        return jsonify({"error": "Mergen vereist reviewer of hoger "
                                 "(globaal of voor het filter van dit doel)"}), 403

    n_citaties = conn.execute("SELECT COUNT(*) FROM citations WHERE argument_id = ?",
                              (arg_id,)).fetchone()[0]
    if (arg["parent_argument_id"] is None
            and arg["stance"] in ("supporting", "contradicting") and not n_citaties):
        nieuwe_status = "bronvermelding_nodig"
    else:
        nieuwe_status = "ongecontroleerd"
    self_merged = arg["contributed_by"] == g.user["username"]

    conn.execute("UPDATE arguments SET status = ?, merged_by = ?, self_merged = ? WHERE id = ?",
                 (nieuwe_status, g.user["username"], self_merged, arg_id))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('arguments', ?, 'merged', ?, ?, ?, ?)
    """, (arg_id, g.user["username"],
          json.dumps({"status": "voorgesteld"}),
          json.dumps({"status": nieuwe_status}),
          "zelf-merge (n=1)" if self_merged else None))
    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "status": nieuwe_status,
                    "merged_by": g.user["username"], "self_merged": self_merged})


@app.route("/api/arguments/<int:arg_id>/score_diff")
def argument_score_diff(arg_id):
    """Score-diff-preview (M2.2): wat verschuift er als dit argument die status krijgt?

    Default-doelstatus: de merge-uitkomst (citatiepoort); ``?status=`` overschrijft
    (bv. 'verworpen' om de impact van afwijzen te zien). Rekent op een tijdelijke
    in-memory kopie — de live database blijft onaangeraakt. Lezen is open.
    """
    conn = get_db()
    arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    n_citaties = conn.execute("SELECT COUNT(*) FROM citations WHERE argument_id = ?",
                              (arg_id,)).fetchone()[0]

    doelstatus = request.args.get("status")
    if doelstatus is None:
        if (arg["parent_argument_id"] is None
                and arg["stance"] in ("supporting", "contradicting") and not n_citaties):
            doelstatus = "bronvermelding_nodig"
        else:
            doelstatus = "ongecontroleerd"
    geldige = ("voorgesteld", "ongecontroleerd", "bronvermelding_nodig", "betwist",
               "geverifieerd", "verouderd", "verworpen")
    if doelstatus not in geldige:
        conn.close()
        return jsonify({"error": f"Status moet een van {geldige} zijn"}), 400

    mem = sqlite3.connect(":memory:")
    mem.row_factory = sqlite3.Row
    conn.backup(mem)
    conn.close()

    voor = scoring.compute_all_scores(mem)
    mem.execute("UPDATE arguments SET status = ? WHERE id = ?", (doelstatus, arg_id))
    na = scoring.compute_all_scores(mem)

    def _naam(categorie, ident):
        sql = {
            "relatie": """SELECT e1.name || ' → ' || e2.name FROM relations r
                          JOIN entities e1 ON r.source_id = e1.id
                          JOIN entities e2 ON r.target_id = e2.id WHERE r.id = ?""",
            "entiteit": "SELECT name FROM entities WHERE id = ?",
            "rol": "SELECT name FROM roles WHERE id = ?",
            "mechanisme": "SELECT name FROM mechanisms WHERE id = ?",
            "emergent_veld": "SELECT label FROM emergent_effects WHERE id = ?",
        }[categorie]
        rij = mem.execute(sql, (ident,)).fetchone()
        return rij[0] if rij else None

    lagen = (("relatie", "relations_detail", "score"),
             ("entiteit", "entities_detail", "score"),
             ("rol", "roles", "geloofwaardigheid"),
             ("mechanisme", "mechanisms", "geloofwaardigheid"),
             ("emergent_veld", "emergent_effects", "geloofwaardigheid"))
    diff = []
    for categorie, sleutel, veld in lagen:
        for ident, det in (na.get(sleutel) or {}).items():
            v0 = (voor.get(sleutel) or {}).get(ident, {}).get(veld, 0.0)
            v1 = det.get(veld, 0.0)
            if abs(v1 - v0) >= 0.0005:
                diff.append({"categorie": categorie, "id": ident, "naam": _naam(categorie, ident),
                             "voor": round(v0, 4), "na": round(v1, 4),
                             "delta": round(v1 - v0, 4)})
    mem.close()
    diff.sort(key=lambda d: -abs(d["delta"]))
    return jsonify({"argument_id": arg_id, "doelstatus": doelstatus, "diff": diff})


@app.route("/api/sources")
def get_sources():
    """Lijst van alle bronnen (voor citaat-selectie)."""
    conn = get_db()
    rows = conn.execute("SELECT id, title, author, source_type, reliability FROM sources ORDER BY author").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


SOURCE_TYPES = {"boek", "academisch_artikel", "rapport", "nieuwsartikel",
                "transcript", "interview", "dataset", "wetgeving",
                "persbericht", "website", "overig"}
LOCATION_TYPES = {"url", "file", "doi", "isbn", "arxiv", "handle", "archive_url"}


@app.route("/api/sources", methods=["POST"])
@require_user()
def create_source():
    """Nieuwe bron registreren vanuit de UI (voor inline citaat-selectie).

    De cluster_key (M1.2) wordt afgeleid uit auteur/uitgever — dezelfde regel als
    register_source.py — tenzij expliciet meegegeven. De bron is bibliografische
    referentie (geen claim), dus hij landt meteen; het argument dat hem gebruikt
    blijft 'voorgesteld' tot een reviewer merget. Een bestaande titel wordt
    hergebruikt i.p.v. gedupliceerd (clusterhygiëne)."""
    data = request.json or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Titel is verplicht"}), 400
    source_type = (data.get("source_type") or "").strip()
    if source_type not in SOURCE_TYPES:
        return jsonify({"error": "Ongeldig brontype. Kies uit: "
                                 + ", ".join(sorted(SOURCE_TYPES))}), 400
    author = (data.get("author") or "").strip() or None
    publisher = (data.get("publisher") or "").strip() or None
    date_published = (data.get("date_published") or "").strip() or None
    cluster_key = (data.get("cluster_key") or "").strip() or None
    if cluster_key is None:
        import sys as _sys
        scripts_dir = str(Path(__file__).parent / "scripts")
        if scripts_dir not in _sys.path:
            _sys.path.insert(0, scripts_dir)
        from migrate_scoring_v2 import cluster_key_voor
        cluster_key = cluster_key_voor(author, publisher)

    loc = data.get("location") or {}
    loc_type = (loc.get("type") or "").strip() or None
    loc_value = (loc.get("value") or "").strip() or None
    if loc_type and loc_type not in LOCATION_TYPES:
        return jsonify({"error": "Ongeldig locatietype. Kies uit: "
                                 + ", ".join(sorted(LOCATION_TYPES))}), 400

    conn = get_db()
    bestaand = conn.execute("SELECT id, title, author, source_type, reliability "
                            "FROM sources WHERE title = ?", (title,)).fetchone()
    if bestaand:
        conn.close()
        return jsonify({**dict(bestaand), "hergebruikt": True}), 200
    try:
        cur = conn.execute(
            """INSERT INTO sources (title, author, source_type, publisher, date_published, cluster_key)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, author, source_type, publisher, date_published, cluster_key))
        sid = cur.lastrowid
        if loc_type and loc_value:
            conn.execute(
                "INSERT INTO source_locations (source_id, location_type, location) VALUES (?, ?, ?)",
                (sid, loc_type, loc_value))
        conn.execute(
            """INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
               VALUES ('sources', ?, 'created', ?, ?, ?)""",
            (sid, g.user["username"],
             json.dumps({"title": title, "source_type": source_type, "cluster_key": cluster_key}),
             "Nieuwe bron geregistreerd via de UI (citaat-selectie)"))
        conn.commit()
        row = conn.execute("SELECT id, title, author, source_type, reliability "
                           "FROM sources WHERE id = ?", (sid,)).fetchone()
        conn.close()
        return jsonify(dict(row)), 201
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400


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
                VALUES ('arguments', ?, 'updated', ?, ?, ?, ?)
            """, (argument_id, g.user["username"],
                  json.dumps({"status": "bronvermelding_nodig"}),
                  json.dumps({"status": nieuwe_status}),
                  f"Automatisch (citatiepoort): citatie #{cid} toegevoegd"))

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
    # Moderatiewachtrij: admin → meteen 'goedgekeurd'; ieder ander → 'voorgesteld'
    # (onzichtbaar in viz/scores tot een reviewer goedkeurt).
    status = "goedgekeurd" if heeft_rol(conn, g.user, "maintainer") else "voorgesteld"
    try:
        cur = conn.execute("""
            INSERT INTO entities (name, type, primary_role_id, description, active_from, active_until, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, etype, primary_role_id, description, active_from, active_until, status))
        eid = cur.lastrowid

        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('entities', ?, 'created', ?, ?, ?)
        """, (eid, contributed_by, json.dumps({"name": name, "type": etype, "status": status}),
              "Nieuwe entiteit toegevoegd (admin: direct zichtbaar)" if status == "goedgekeurd"
              else "Nieuwe entiteit voorgesteld (wacht op goedkeuring)"))

        conn.commit()
        row = conn.execute("""
            SELECT e.id, e.name, e.type, e.description, e.status,
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

    status = "goedgekeurd" if heeft_rol(conn, g.user, "maintainer") else "voorgesteld"
    try:
        cur = conn.execute("""
            INSERT INTO relations
                (source_id, target_id, relation_type, mechanism_id, description,
                 certainty, influence, bidirectional, active_from, active_until, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, target_id, rtype, mechanism_id, description,
              certainty, influence, bidirectional, active_from, active_until, status))
        rid = cur.lastrowid

        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('relations', ?, 'created', ?, ?, ?)
        """, (rid, contributed_by,
              json.dumps({"source_id": source_id, "target_id": target_id,
                          "relation_type": rtype, "status": status}),
              "Nieuwe relatie toegevoegd (admin: direct zichtbaar)" if status == "goedgekeurd"
              else "Nieuwe relatie voorgesteld (wacht op goedkeuring)"))

        conn.commit()
        row = conn.execute("""
            SELECT r.id, r.source_id, r.target_id, r.relation_type, r.status,
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


def _creator_van(conn, tabel, rid):
    """De gebruiker die dit record aanmaakte (uit edit_log), voor de eigen-werk-poort."""
    row = conn.execute(
        "SELECT changed_by FROM edit_log WHERE table_name = ? AND record_id = ? "
        "AND action = 'created' ORDER BY id LIMIT 1", (tabel, rid)).fetchone()
    return row["changed_by"] if row else None


def _modereer(tabel, rid):
    """Moderatie van een 'voorgesteld' node/edge: reviewer+ keurt goed of af.
    Niemand keurt eigen werk goed (M2.1)."""
    data = request.json or {}
    nieuw = data.get("status")
    if nieuw not in ("goedgekeurd", "afgewezen"):
        return jsonify({"error": "status moet 'goedgekeurd' of 'afgewezen' zijn"}), 400
    conn = get_db()
    rij = conn.execute(f"SELECT status FROM {tabel} WHERE id = ?", (rid,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": "Niet gevonden"}), 404
    if not heeft_rol(conn, g.user, "reviewer"):
        conn.close()
        return jsonify({"error": "Modereren vereist reviewer of hoger"}), 403
    if rij["status"] != "voorgesteld":
        conn.close()
        return jsonify({"error": f"Alleen een 'voorgesteld' item kan gemodereerd worden "
                                 f"(huidige status: {rij['status']})"}), 400
    if _creator_van(conn, tabel, rid) == g.user["username"]:
        conn.close()
        return jsonify({"error": "Niemand keurt eigen werk goed (M2.1): laat een "
                                 "andere reviewer dit beoordelen"}), 403
    conn.execute(f"UPDATE {tabel} SET status = ? WHERE id = ?", (nieuw, rid))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES (?, ?, 'updated', ?, ?, ?, ?)
    """, (tabel, rid, g.user["username"], json.dumps({"status": "voorgesteld"}),
          json.dumps({"status": nieuw}), (data.get("motivatie") or "").strip() or None))
    conn.commit()
    conn.close()
    return jsonify({"id": rid, "status": nieuw})


@app.route("/api/entities/<int:eid>/status", methods=["PATCH"])
@require_user()
def moderate_entity(eid):
    return _modereer("entities", eid)


@app.route("/api/relations/<int:rid>/status", methods=["PATCH"])
@require_user()
def moderate_relation(rid):
    return _modereer("relations", rid)


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
@require_user()
def create_role():
    """M2.3: een nieuw theorie-element ontstaat normaal via een RfC. In de
    opbouwfase mag een globale maintainer een rol (node) direct toevoegen,
    langs de RfC heen — gevlagd en gelogd. Zo'n element heeft nog geen
    discussieboom, krijgt dus een lage credibility en kan via tegenargumenten
    en de zichtbaarheidsdrempel weer uit beeld raken."""
    conn = get_db()
    if not heeft_rol(conn, g.user, "maintainer"):
        conn.close()
        return jsonify({"error": "Theorie-elementen ontstaan via een RfC (M2.3): "
                                 "POST /api/voorstellen met soort 'nieuw_theorie_element' "
                                 "(twee menselijke reviewers). Een globale maintainer mag "
                                 "in de opbouwfase direct toevoegen."}), 403
    d = request.json or {}
    velden = {
        "naam": (d.get("naam") or d.get("name") or "").strip(),
        "categorie": d.get("categorie") or d.get("category"),
        "definitie": (d.get("definitie") or d.get("description") or "").strip(),
        "voorbeelden": d.get("voorbeelden") or d.get("examples"),
    }
    fouten = []
    if not velden["naam"]:
        fouten.append("naam is verplicht")
    elif voorstellen._naam_bestaat(conn, "rol", velden["naam"]):
        fouten.append(f"er bestaat al een rol met de naam '{velden['naam']}'")
    if velden["categorie"] not in voorstellen.ROL_CATEGORIEEN:
        fouten.append(f"categorie moet een van {voorstellen.ROL_CATEGORIEEN} zijn")
    if not velden["definitie"]:
        fouten.append("definitie/description is verplicht")
    if fouten:
        conn.close()
        return jsonify({"error": "Ongeldige rol", "fouten": fouten}), 400
    try:
        rid = voorstellen._maak_element(conn, "rol", velden)
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('roles', ?, 'created', ?, ?, ?)
        """, (rid, g.user["username"], json.dumps({"name": velden["naam"]}),
              "Direct toegevoegd door maintainer (opbouwfase, langs RfC heen) — betwistbaar"))
        conn.commit()
        conn.close()
        return jsonify({"id": rid, "name": velden["naam"], "direct_toegevoegd": True}), 201
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 400


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
@require_user()
def create_mechanism():
    """M2.3: een nieuw theorie-element ontstaat normaal via een RfC. In de
    opbouwfase mag een globale maintainer een mechanisme (edge) direct
    toevoegen, langs de RfC heen — gevlagd en gelogd. Zonder discussieboom
    blijft de credibility laag, dus het kan via de zichtbaarheidsdrempel en
    tegenargumenten weer uit beeld raken."""
    conn = get_db()
    if not heeft_rol(conn, g.user, "maintainer"):
        conn.close()
        return jsonify({"error": "Theorie-elementen ontstaan via een RfC (M2.3): "
                                 "POST /api/voorstellen met soort 'nieuw_theorie_element' "
                                 "(twee menselijke reviewers). Een globale maintainer mag "
                                 "in de opbouwfase direct toevoegen."}), 403
    d = request.json or {}
    velden = {
        "naam": (d.get("naam") or d.get("name") or "").strip(),
        "filter": d.get("filter"),
        "mechanisme_type": d.get("mechanisme_type") or d.get("mechanism_type"),
        "definitie": (d.get("definitie") or d.get("description") or "").strip(),
        "effect": (d.get("effect") or "").strip(),
        "aard": d.get("aard"),
        "source_role_id": d.get("source_role_id"),
        "target_role_id": d.get("target_role_id"),
    }
    fouten = []
    if not velden["naam"]:
        fouten.append("naam is verplicht")
    elif voorstellen._naam_bestaat(conn, "mechanisme", velden["naam"]):
        fouten.append(f"er bestaat al een mechanisme met de naam '{velden['naam']}'")
    if velden["filter"] not in voorstellen.MECHANISME_FILTERS:
        fouten.append(f"filter moet een van {voorstellen.MECHANISME_FILTERS} zijn")
    if not velden["definitie"]:
        fouten.append("definitie/description is verplicht")
    if not velden["effect"]:
        fouten.append("effect is verplicht")
    if velden["aard"] not in voorstellen.AARD_KEUZES:
        fouten.append(f"aard moet een van {voorstellen.AARD_KEUZES} zijn")
    if fouten:
        conn.close()
        return jsonify({"error": "Ongeldig mechanisme", "fouten": fouten}), 400
    try:
        mid = voorstellen._maak_element(conn, "mechanisme", velden)
        for f in d.get("extra_filters") or []:
            conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) "
                         "VALUES (?, ?)", (mid, f))
        for thema in d.get("themes") or d.get("themas") or []:
            conn.execute("INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) "
                         "VALUES (?, ?)", (mid, thema))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('mechanisms', ?, 'created', ?, ?, ?)
        """, (mid, g.user["username"], json.dumps({"name": velden["naam"]}),
              "Direct toegevoegd door maintainer (opbouwfase, langs RfC heen) — betwistbaar"))
        conn.commit()
        conn.close()
        return jsonify({"id": mid, "name": velden["naam"], "direct_toegevoegd": True}), 201
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 400


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


# ── Titel/beschrijving bewerken (Wikipedia/open-source-model) ─
# Iedereen kan een herformulering/hernoeming *voorstellen* via POST /api/voorstellen
# (soort 'herformuleren' / 'hernoemen'), die langs de gewone reviewweg loopt (theorie
# 2 mensen, praktijk 1, of maintainer-quorum). Een globale maintainer mag daarnaast
# direct bewerken — gevlagd en gelogd, betwistbaar via de score/discussieboom.

_NAAMBAAR = {"rol", "mechanisme", "entiteit", "emergent_effect"}  # relaties hebben geen naam


def _maintainer_patch(element_type):
    """Directe titel/tekst-bewerking door een globale maintainer (opbouwfase)."""
    conn = get_db()
    if not heeft_rol(conn, g.user, "maintainer"):
        conn.close()
        return jsonify({"error": "Direct bewerken vereist een globale maintainer. "
                                 "Stel anders een wijziging voor via POST /api/voorstellen "
                                 "(soort 'herformuleren' of 'hernoemen')."}), 403
    tabel = voorstellen.TABEL[element_type]
    eid = request.view_args[list(request.view_args)[0]]
    rij = conn.execute(f"SELECT * FROM {tabel} WHERE id = ?", (eid,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": f"{element_type} niet gevonden"}), 404
    d = request.json or {}
    toegestaan = list(voorstellen.TEKSTVELDEN[element_type])
    if element_type in _NAAMBAAR:
        toegestaan.append("name")
    diff = {}
    for kol in toegestaan:
        # accepteer NL-alias 'naam'/'definitie' naast de kolomnaam
        waarde = d.get(kol)
        if kol == "name" and waarde is None:
            waarde = d.get("naam")
        if kol == "description" and waarde is None:
            waarde = d.get("definitie")
        if waarde is None:
            continue
        nieuw = (waarde or "").strip()
        if kol in ("name",) and not nieuw:
            conn.close()
            return jsonify({"error": "naam mag niet leeg zijn"}), 400
        if nieuw != (rij[kol] or ""):
            diff[kol] = {"oud": rij[kol], "nieuw": nieuw}
    if not diff:
        conn.close()
        return jsonify({"error": f"geen gewijzigd veld (toegestaan: {toegestaan})"}), 400
    if "name" in diff and voorstellen._naam_bestaat(conn, element_type, diff["name"]["nieuw"]):
        conn.close()
        return jsonify({"error": f"er bestaat al een {element_type} met die naam"}), 400
    motivatie = (d.get("motivatie") or "").strip() or "direct bewerkt door maintainer"
    try:
        for kol, v in diff.items():
            conn.execute(f"UPDATE {tabel} SET {kol} = ? WHERE id = ?", (v["nieuw"], eid))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
            VALUES (?, ?, 'updated', ?, ?, ?, ?)
        """, (tabel, eid, g.user["username"],
              json.dumps({k: v["oud"] for k, v in diff.items()}, ensure_ascii=False),
              json.dumps({k: v["nieuw"] for k, v in diff.items()}, ensure_ascii=False),
              f"Direct bewerkt door maintainer (opbouwfase) — {motivatie}; betwistbaar"))
        conn.commit()
        conn.close()
        return jsonify({"id": eid, "element_type": element_type,
                        "gewijzigd": list(diff), "diff": diff, "direct_bewerkt": True})
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 400


@app.route("/api/roles/<int:rid>", methods=["PATCH"])
@require_user()
def patch_role(rid):
    return _maintainer_patch("rol")


@app.route("/api/mechanisms/<int:mid>", methods=["PATCH"])
@require_user()
def patch_mechanism(mid):
    return _maintainer_patch("mechanisme")


@app.route("/api/entities/<int:eid>", methods=["PATCH"])
@require_user()
def patch_entity(eid):
    return _maintainer_patch("entiteit")


@app.route("/api/relations/<int:rid>", methods=["PATCH"])
@require_user()
def patch_relation(rid):
    return _maintainer_patch("relatie")


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


# ── Voorstellen: theory-RfC's & granulariteitsbeheer (M2.3/M2.6) ──

def _filters_van_voorstel(payload) -> list:
    """Filter(s)/categorie(ën) die een voorstel raakt, voor de filterrol-poort."""
    fs = set()
    bronnen = [payload, payload.get("doel") or {}] + list(payload.get("nieuwe") or [])
    for d in bronnen:
        for sleutel in ("filter", "categorie"):
            if isinstance(d, dict) and d.get(sleutel):
                fs.add(d[sleutel])
    return sorted(fs)


def _voorstel_dict(conn, rij) -> dict:
    payload = json.loads(rij["payload"])
    theorielaag = voorstellen.is_theorielaag(rij["soort"], payload)
    t = voorstellen.telling(conn, rij["id"], rij["ingediend_door"], theorielaag)
    return {
        "id": rij["id"], "soort": rij["soort"], "titel": rij["titel"],
        "payload": payload, "status": rij["status"],
        "ingediend_door": rij["ingediend_door"], "created_at": rij["created_at"],
        "besloten_at": rij["besloten_at"],
        "resultaat": json.loads(rij["resultaat"]) if rij["resultaat"] else None,
        "theorielaag": theorielaag,
        "benodigde_akkoorden": voorstellen.benodigde_akkoorden(rij["soort"], payload),
        "telling": t,
    }


@app.route("/api/voorstellen", methods=["POST"])
@require_user()
def create_voorstel():
    """Voorstel indienen (M2.3/M2.6): nieuw theorie-element (RfC-sjabloon),
    splitsen, samenvoegen of hernoemen. Validatie tegen het sjabloon gebeurt
    bij indienen; uitvoering pas na voldoende reviews."""
    data = request.json or {}
    soort = data.get("soort")
    titel = (data.get("titel") or "").strip()
    payload = data.get("payload") or {}
    if not titel:
        return jsonify({"error": "Titel is verplicht"}), 400

    conn = get_db()
    fouten = voorstellen.valideer_payload(conn, soort, payload)
    if fouten:
        conn.close()
        return jsonify({"error": "Voorstel voldoet niet aan het sjabloon",
                        "fouten": fouten}), 400
    cur = conn.execute("""
        INSERT INTO voorstellen (soort, titel, payload, ingediend_door)
        VALUES (?, ?, ?, ?)
    """, (soort, titel, json.dumps(payload, ensure_ascii=False), g.user["username"]))
    vid = cur.lastrowid
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('voorstellen', ?, 'created', ?, ?, ?)
    """, (vid, g.user["username"], json.dumps({"soort": soort, "titel": titel}),
          "Voorstel ingediend"))
    conn.commit()
    rij = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (vid,)).fetchone()
    uit = _voorstel_dict(conn, rij)
    conn.close()
    return jsonify(uit), 201


@app.route("/api/voorstellen")
def list_voorstellen():
    """Openstaande (of alle, ?status=alle) voorstellen met reviewstand."""
    status = request.args.get("status", "open")
    conn = get_db()
    if status == "alle":
        rows = conn.execute("SELECT * FROM voorstellen ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM voorstellen WHERE status = ? ORDER BY id DESC",
                            (status,)).fetchall()
    uit = [_voorstel_dict(conn, r) for r in rows]
    conn.close()
    return jsonify(uit)


@app.route("/api/voorstellen/<int:vid>")
def get_voorstel(vid):
    """Voorsteldetail, incl. de hertriage-checklist bij splitsen/samenvoegen
    (per aanhangend argument/relatie/instantiatie/padclaim: toegewezen of niet)."""
    conn = get_db()
    rij = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (vid,)).fetchone()
    if not rij:
        conn.close()
        return jsonify({"error": "Voorstel niet gevonden"}), 404
    uit = _voorstel_dict(conn, rij)
    uit["reviews"] = [dict(r) for r in conn.execute(
        """SELECT vr.reviewer, vr.oordeel, vr.motivatie, vr.created_at, u.kind
           FROM voorstel_reviews vr JOIN users u ON u.username = vr.reviewer
           WHERE vr.voorstel_id = ? ORDER BY vr.id""", (vid,))]

    payload = uit["payload"]
    et = payload.get("element_type")
    if rij["status"] == "open" and et in voorstellen.GRANULARITEIT_TYPES:
        if rij["soort"] == "splitsen" and payload.get("oud_id"):
            aan = voorstellen.aanhangsels(conn, et, payload["oud_id"])
            toe = payload.get("toewijzing") or {}
            uit["hertriage"] = {
                naam: [{"id": i, "toegewezen": bool((toe.get(naam) or {}).get(str(i))
                                                    or (toe.get(naam) or {}).get(i))}
                       for i in items]
                for naam, items in aan.items()}
            uit["restlijst_leeg"] = all(
                x["toegewezen"] for lijst in uit["hertriage"].values() for x in lijst)
        elif rij["soort"] == "samenvoegen" and payload.get("oud_ids"):
            aan = voorstellen.aanhangsels_meervoudig(conn, et, payload["oud_ids"])
            her = payload.get("herbevestigd") or {}
            uit["hertriage"] = {
                naam: [{"id": i, "herbevestigd": i in (her.get(naam) or [])}
                       for i in items]
                for naam, items in aan.items()}
    conn.close()
    return jsonify(uit)


@app.route("/api/voorstellen/<int:vid>/reviews", methods=["POST"])
@require_user()
def review_voorstel(vid):
    """Review op een voorstel. Menselijke reviewers (reviewer of hoger, globaal of
    per filter) tellen; agent-oordelen worden vastgelegd als zichtbaar advies maar
    tellen nooit (§6.4). Besluit:
      - ≥ 1 geldige menselijke afwijzing → 'afgewezen' (indiener kan herzien);
      - geldige akkoorden ≥ drempel (theorielaag 2, praktijk 1) → 'geaccepteerd'
        en het voorstel wordt direct uitgevoerd; faalt de uitvoering (bv.
        hertriage-restlijst niet leeg) dan blijft het voorstel open (409).
    Opbouwfase: één akkoord van een globale maintainer telt als het volledige
    quorum (ook van de indiener zelf); een afwijzing blokkeert dan nog steeds.
    """
    data = request.json or {}
    oordeel = data.get("oordeel")
    if oordeel not in ("akkoord", "afwijzen"):
        return jsonify({"error": "oordeel moet 'akkoord' of 'afwijzen' zijn"}), 400
    motivatie = (data.get("motivatie") or "").strip() or None
    if oordeel == "afwijzen" and not motivatie:
        return jsonify({"error": "Een afwijzing vergt een motivatie"}), 400

    conn = get_db()
    rij = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (vid,)).fetchone()
    if not rij:
        conn.close()
        return jsonify({"error": "Voorstel niet gevonden"}), 404
    if rij["status"] != "open":
        conn.close()
        return jsonify({"error": f"Voorstel is al {rij['status']}"}), 400
    payload = json.loads(rij["payload"])
    if g.user["kind"] == "mens" and not heeft_rol(conn, g.user, "reviewer",
                                                  _filters_van_voorstel(payload)):
        conn.close()
        return jsonify({"error": "Reviewen vereist reviewer of hoger "
                                 "(globaal of voor het filter van dit voorstel)"}), 403

    conn.execute("""
        INSERT INTO voorstel_reviews (voorstel_id, reviewer, oordeel, motivatie)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (voorstel_id, reviewer)
        DO UPDATE SET oordeel = excluded.oordeel, motivatie = excluded.motivatie,
                      created_at = CURRENT_TIMESTAMP
    """, (vid, g.user["username"], oordeel, motivatie))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('voorstellen', ?, 'updated', ?, ?, ?)
    """, (vid, g.user["username"], json.dumps({"oordeel": oordeel}), motivatie))
    conn.commit()  # de review zelf staat vast, ook als de uitvoering hieronder faalt

    theorielaag = voorstellen.is_theorielaag(rij["soort"], payload)
    t = voorstellen.telling(conn, vid, rij["ingediend_door"], theorielaag)
    benodigd = voorstellen.benodigde_akkoorden(rij["soort"], payload)
    besluit = "open"

    # Maintainer-quorum (opbouwfase): één akkoord van een globale maintainer telt
    # als het volledige quorum (theorielaag 2, praktijk 1) — ook van de indiener
    # zelf, langs de indiener-uitsluiting heen. Een openstaande afwijzing blokkeert
    # nog steeds (zoals 2 akkoorden dat ook niet van een afwijzing winnen). Gevlagd
    # en gelogd; via tegen-RfC/discussieboom en de zichtbaarheidsdrempel betwistbaar.
    maintainer_quorum = conn.execute("""
        SELECT 1 FROM voorstel_reviews vr JOIN users u ON u.username = vr.reviewer
        WHERE vr.voorstel_id = ? AND vr.oordeel = 'akkoord'
          AND u.kind = 'mens' AND u.role = 'maintainer' LIMIT 1""", (vid,)).fetchone() is not None
    indiener_keurde_goed = oordeel == "akkoord" and g.user["username"] == rij["ingediend_door"]

    if t["afwijzingen"]:
        conn.execute("UPDATE voorstellen SET status = 'afgewezen', "
                     "besloten_at = CURRENT_TIMESTAMP WHERE id = ?", (vid,))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('voorstellen', ?, 'updated', ?, ?, ?)
        """, (vid, g.user["username"], json.dumps({"status": "afgewezen"}),
              f"Afgewezen door: {', '.join(t['afwijzingen'])}"))
        conn.commit()
        besluit = "afgewezen"
    elif len(set(t["akkoorden"])) >= benodigd or maintainer_quorum:
        try:
            resultaat = voorstellen.voer_uit(conn, rij["soort"], payload, vid)
            via_maintainer = maintainer_quorum and len(set(t["akkoorden"])) < benodigd
            resultaat["self_merged"] = t["zelf_akkoord"] or indiener_keurde_goed
            resultaat["maintainer_quorum"] = via_maintainer
            if via_maintainer:
                reden = (f"maintainer-akkoord telt als volledig quorum ({benodigd}) "
                         f"— {g.user['username']}; betwistbaar via tegen-RfC")
            elif t["zelf_akkoord"]:
                reden = "zelf-akkoord (n=1)"
            else:
                reden = f"Akkoord van: {', '.join(set(t['akkoorden']))}"
            conn.execute("""UPDATE voorstellen SET status = 'geaccepteerd', resultaat = ?,
                            besloten_at = CURRENT_TIMESTAMP WHERE id = ?""",
                         (json.dumps(resultaat, ensure_ascii=False), vid))
            conn.execute("""
                INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
                VALUES ('voorstellen', ?, 'merged', ?, ?, ?)
            """, (vid, g.user["username"], json.dumps(resultaat), reden))
            conn.commit()
            besluit = "geaccepteerd"
        except (ValueError, sqlite3.IntegrityError) as e:
            conn.rollback()
            conn.close()
            return jsonify({"voorstel_id": vid, "besluit": "open",
                            "blokkade": str(e),
                            "telling": t, "benodigde_akkoorden": benodigd}), 409
    rij = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (vid,)).fetchone()
    uit = _voorstel_dict(conn, rij)
    uit["besluit"] = besluit
    conn.close()
    return jsonify(uit)


@app.route("/api/voorstellen/<int:vid>/intrekken", methods=["POST"])
@require_user()
def intrek_voorstel(vid):
    """Eigen voorstel intrekken (of door een maintainer)."""
    conn = get_db()
    rij = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (vid,)).fetchone()
    if not rij:
        conn.close()
        return jsonify({"error": "Voorstel niet gevonden"}), 404
    if rij["status"] != "open":
        conn.close()
        return jsonify({"error": f"Voorstel is al {rij['status']}"}), 400
    if (rij["ingediend_door"] != g.user["username"]
            and ROLE_ORDER.get(g.user["role"], 0) < ROLE_ORDER["maintainer"]):
        conn.close()
        return jsonify({"error": "Alleen de indiener of een maintainer trekt een "
                                 "voorstel in"}), 403
    conn.execute("UPDATE voorstellen SET status = 'ingetrokken', "
                 "besloten_at = CURRENT_TIMESTAMP WHERE id = ?", (vid,))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value)
        VALUES ('voorstellen', ?, 'updated', ?, ?)
    """, (vid, g.user["username"], json.dumps({"status": "ingetrokken"})))
    conn.commit()
    conn.close()
    return jsonify({"id": vid, "status": "ingetrokken"})


@app.route("/api/review_queue")
def review_queue():
    """Review-wachtrij (M2.2): voorgestelde argumenten + open voorstellen."""
    conn = get_db()
    argumenten = []
    for a in conn.execute("""
        SELECT a.id, a.stance, a.claim, a.property, a.parent_argument_id,
               a.contributed_by, a.created_at,
               a.relation_id, a.entity_id, a.role_id, a.mechanism_id, a.emergent_effect_id,
               (SELECT COUNT(*) FROM citations c WHERE c.argument_id = a.id) AS n_citaties
        FROM arguments a WHERE a.status = 'voorgesteld' ORDER BY a.id"""):
        a = dict(a)
        if a["parent_argument_id"]:
            doel = f"reactie op argument #{a['parent_argument_id']}"
        elif a["relation_id"]:
            r = conn.execute("""SELECT e1.name || ' → ' || e2.name AS n FROM relations r
                                JOIN entities e1 ON r.source_id = e1.id
                                JOIN entities e2 ON r.target_id = e2.id
                                WHERE r.id = ?""", (a["relation_id"],)).fetchone()
            doel = f"relatie: {r['n']}" if r else f"relatie #{a['relation_id']}"
        elif a["entity_id"]:
            r = conn.execute("SELECT name FROM entities WHERE id = ?",
                             (a["entity_id"],)).fetchone()
            doel = f"entiteit: {r['name']}" if r else f"entiteit #{a['entity_id']}"
        elif a["role_id"]:
            r = conn.execute("SELECT name FROM roles WHERE id = ?", (a["role_id"],)).fetchone()
            doel = f"rol: {r['name']}" if r else f"rol #{a['role_id']}"
        elif a["mechanism_id"]:
            r = conn.execute("SELECT name FROM mechanisms WHERE id = ?",
                             (a["mechanism_id"],)).fetchone()
            doel = f"mechanisme: {r['name']}" if r else f"mechanisme #{a['mechanism_id']}"
        else:
            r = conn.execute("SELECT label FROM emergent_effects WHERE id = ?",
                             (a["emergent_effect_id"],)).fetchone()
            doel = f"veld: {r['label']}" if r else f"veld #{a['emergent_effect_id']}"
        a["doel"] = doel
        argumenten.append(a)

    open_voorstellen = [_voorstel_dict(conn, r) for r in conn.execute(
        "SELECT * FROM voorstellen WHERE status = 'open' ORDER BY id")]
    conn.close()
    return jsonify({"argumenten": argumenten, "voorstellen": open_voorstellen})


# ── Ratings (M2.5) ───────────────────────────────────────────

@app.route("/api/arguments/<int:arg_id>/ratings", methods=["GET"])
def get_ratings(arg_id):
    conn = get_db()
    rows = [dict(r) for r in conn.execute("""
        SELECT ar.rater, ar.oordeel, ar.reden, ar.motivatie, ar.created_at, u.kind
        FROM argument_ratings ar JOIN users u ON u.username = ar.rater
        WHERE ar.argument_id = ? ORDER BY ar.id""", (arg_id,))]
    conn.close()
    telling = {"mens": {"nuttig": 0, "niet_nuttig": 0},
               "agent": {"nuttig": 0, "niet_nuttig": 0}}
    for r in rows:
        telling[r["kind"]][r["oordeel"]] += 1
    return jsonify({"argument_id": arg_id, "ratings": rows, "telling": telling})


@app.route("/api/arguments/<int:arg_id>/ratings", methods=["POST"])
@require_user()
def create_rating(arg_id):
    """Rating afgeven (M2.5): nuttig/niet_nuttig + gestructureerde reden.

    Je beoordeelt onderbouwing/relevantie/eerlijkheid, nooit waarheid; eigen werk
    raten kan niet. Agent-ratings zijn zichtbaar advies (kalibratie: M2.5)."""
    data = request.json or {}
    oordeel = data.get("oordeel")
    if oordeel not in ("nuttig", "niet_nuttig"):
        return jsonify({"error": "oordeel moet 'nuttig' of 'niet_nuttig' zijn"}), 400
    reden = data.get("reden") or None

    conn = get_db()
    arg = conn.execute("SELECT contributed_by FROM arguments WHERE id = ?",
                       (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if arg["contributed_by"] == g.user["username"]:
        conn.close()
        return jsonify({"error": "Eigen werk raten kan niet (M2.5)"}), 403
    try:
        conn.execute("""
            INSERT INTO argument_ratings (argument_id, rater, oordeel, reden, motivatie)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (argument_id, rater)
            DO UPDATE SET oordeel = excluded.oordeel, reden = excluded.reden,
                          motivatie = excluded.motivatie, created_at = CURRENT_TIMESTAMP
        """, (arg_id, g.user["username"], oordeel, reden,
              (data.get("motivatie") or "").strip() or None))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value)
            VALUES ('argument_ratings', ?, 'created', ?, ?)
        """, (arg_id, g.user["username"], json.dumps({"oordeel": oordeel, "reden": reden})))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400
    conn.close()
    return jsonify({"argument_id": arg_id, "rater": g.user["username"],
                    "oordeel": oordeel, "kind": g.user["kind"],
                    "advies": g.user["kind"] == "agent"}), 201


@app.route("/api/arguments/<int:arg_id>/ratings", methods=["DELETE"])
@require_user()
def delete_rating(arg_id):
    """Eigen rating intrekken (un-vote): verwijdert uitsluitend de stem van de
    ingelogde gebruiker op dit argument. Idempotent — geen stem = niets te doen."""
    conn = get_db()
    cur = conn.execute(
        "DELETE FROM argument_ratings WHERE argument_id = ? AND rater = ?",
        (arg_id, g.user["username"]))
    verwijderd = cur.rowcount > 0
    if verwijderd:
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by)
            VALUES ('argument_ratings', ?, 'deleted', ?)
        """, (arg_id, g.user["username"]))
        conn.commit()
    conn.close()
    return jsonify({"argument_id": arg_id, "rater": g.user["username"],
                    "verwijderd": verwijderd})


# ── Recent changes & watchlists (M2.4) ───────────────────────

@app.route("/api/recent_changes")
def recent_changes():
    """Recent-changes-feed op edit_log. ?watchlist=1 filtert op de eigen volglijst
    (vereist login); een gevolgde relatie/entiteit/rol/… vangt ook de argumenten
    die erop ingediend worden."""
    limit = min(request.args.get("limit", 50, type=int), 200)
    conn = get_db()

    watch_filter = None
    if request.args.get("watchlist") == "1":
        user = _zoek_user(conn)
        if user is None:
            conn.close()
            return jsonify({"error": "Inloggen vereist voor de watchlist-weergave"}), 401
        direct = {(r["table_name"], r["record_id"]) for r in conn.execute(
            "SELECT table_name, record_id FROM watchlists WHERE user_id = ?",
            (user["id"],))}
        arg_ids = {rid for (tn, rid) in direct if tn == "arguments"}
        kolommen = {"relations": "relation_id", "entities": "entity_id", "roles": "role_id",
                    "mechanisms": "mechanism_id", "emergent_effects": "emergent_effect_id"}
        for tn, kolom in kolommen.items():
            ids = [rid for (t, rid) in direct if t == tn]
            if ids:
                qs = ",".join("?" * len(ids))
                arg_ids |= {r[0] for r in conn.execute(
                    f"SELECT id FROM arguments WHERE {kolom} IN ({qs})", ids)}
        watch_filter = (direct, arg_ids)

    uit = []
    for r in conn.execute("SELECT * FROM edit_log ORDER BY id DESC LIMIT ?",
                          (limit * 10 if watch_filter else limit,)):
        if watch_filter:
            direct, arg_ids = watch_filter
            if ((r["table_name"], r["record_id"]) not in direct
                    and not (r["table_name"] == "arguments" and r["record_id"] in arg_ids)):
                continue
        uit.append(dict(r))
        if len(uit) >= limit:
            break
    conn.close()
    return jsonify(uit)


@app.route("/api/watchlist", methods=["GET", "POST", "DELETE"])
@require_user()
def watchlist():
    conn = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in conn.execute(
            "SELECT table_name, record_id, created_at FROM watchlists WHERE user_id = ? "
            "ORDER BY created_at DESC", (g.user["id"],))]
        conn.close()
        return jsonify(rows)

    data = request.json or {}
    table_name, record_id = data.get("table_name"), data.get("record_id")
    geldige = ("relations", "entities", "roles", "mechanisms", "emergent_effects", "arguments")
    if table_name not in geldige or not isinstance(record_id, int):
        conn.close()
        return jsonify({"error": f"table_name moet een van {geldige} zijn, "
                                 "record_id een integer"}), 400
    if request.method == "POST":
        if not conn.execute(f"SELECT 1 FROM {table_name} WHERE id = ?",
                            (record_id,)).fetchone():
            conn.close()
            return jsonify({"error": f"{table_name} #{record_id} bestaat niet"}), 404
        conn.execute("INSERT OR IGNORE INTO watchlists (user_id, table_name, record_id) "
                     "VALUES (?, ?, ?)", (g.user["id"], table_name, record_id))
        conn.commit()
        conn.close()
        return jsonify({"watching": True, "table_name": table_name,
                        "record_id": record_id}), 201
    conn.execute("DELETE FROM watchlists WHERE user_id = ? AND table_name = ? "
                 "AND record_id = ?", (g.user["id"], table_name, record_id))
    conn.commit()
    conn.close()
    return jsonify({"watching": False, "table_name": table_name, "record_id": record_id})


# ── Lineage (M2.6): oude id's blijven herleidbaar ────────────

@app.route("/api/lineage/<element_type>/<int:element_id>")
def get_lineage(element_type, element_id):
    """Opvolging van een element: is het vervangen, en door wie? Oude id's
    beantwoorden met een verwijzing naar de opvolger(s)."""
    if element_type not in voorstellen.TABEL:
        return jsonify({"error": f"element_type moet een van "
                                 f"{tuple(voorstellen.TABEL)} zijn"}), 400
    conn = get_db()
    tabel = voorstellen.TABEL[element_type]
    rij = conn.execute(f"SELECT id, name, vervangen FROM {tabel} WHERE id = ?",
                       (element_id,)).fetchone()
    if not rij:
        conn.close()
        return jsonify({"error": f"{element_type} #{element_id} bestaat niet"}), 404
    opvolgers = [dict(r) for r in conn.execute(f"""
        SELECT l.soort, l.nieuw_id AS id, t.name AS naam, l.voorstel_id, l.reden
        FROM lineage l JOIN {tabel} t ON t.id = l.nieuw_id
        WHERE l.element_type = ? AND l.oud_id = ? AND l.nieuw_id != l.oud_id
        ORDER BY l.id""", (element_type, element_id))]
    herkomst = [dict(r) for r in conn.execute(f"""
        SELECT l.soort, l.oud_id AS id, t.name AS naam, l.voorstel_id, l.reden
        FROM lineage l JOIN {tabel} t ON t.id = l.oud_id
        WHERE l.element_type = ? AND l.nieuw_id = ? AND l.nieuw_id != l.oud_id
        ORDER BY l.id""", (element_type, element_id))]
    conn.close()
    return jsonify({"element_type": element_type, "id": element_id, "naam": rij["name"],
                    "vervangen": bool(rij["vervangen"]),
                    "opvolgers": opvolgers, "herkomst": herkomst})


# ── Voorspellingsregister (M3.4) ─────────────────────────────
# Toetsbare verwachtingen worden vastgelegd vóór de uitkomst bekend is en na de
# deadline gescoord (Brier = (kans − uitkomst)²). Indienen = bijdrager; scoren =
# reviewer; zelf scoren mag (n=1) maar draagt de self_scored-vlag (§6.1).

PREDICTION_EINDSTATUSSEN = ("uitgekomen", "niet_uitgekomen", "onbeslisbaar")


def _prediction_dict(rij) -> dict:
    d = dict(rij)
    d["self_scored"] = bool(d["self_scored"])
    return d


@app.route("/api/predictions")
def list_predictions():
    """Het voorspellingsregister (open leesbaar); ?status=open filtert."""
    status = request.args.get("status")
    conn = get_db()
    sql, params = "SELECT * FROM predictions", ()
    if status:
        sql, params = sql + " WHERE status = ?", (status,)
    rows = [_prediction_dict(r) for r in conn.execute(sql + " ORDER BY deadline, id", params)]
    conn.close()
    return jsonify(rows)


@app.route("/api/predictions", methods=["POST"])
@require_user()
def create_prediction():
    """Nieuwe voorspelling: claim + afleiding + meetcriterium + kans + deadline,
    verankerd aan ≥ 1 theorie-element. De deadline moet in de toekomst liggen —
    het register bestaat juist om vóóraf vast te leggen (M3.4)."""
    data = request.json or {}
    fouten, velden = [], {}
    for veld in ("claim", "afleiding", "meetcriterium"):
        velden[veld] = (data.get(veld) or "").strip()
        if not velden[veld]:
            fouten.append(f"'{veld}' is verplicht")
    try:
        kans = float(data.get("kans"))
        if not 0 < kans < 1:
            raise ValueError
    except (TypeError, ValueError):
        kans = None
        fouten.append("'kans' moet een getal tussen 0 en 1 (exclusief) zijn — "
                      "0 of 1 is dogma, geen voorspelling")
    deadline = (data.get("deadline") or "").strip()
    try:
        if datetime.date.fromisoformat(deadline) <= datetime.date.today():
            fouten.append("'deadline' moet in de toekomst liggen — een claim over "
                          "een al bekende uitkomst hoort in de discussieboom")
    except ValueError:
        fouten.append("'deadline' moet een datum zijn (YYYY-MM-DD)")

    ankers = {k: data.get(k) for k in ("mechanism_id", "role_id", "emergent_effect_id")}
    if not any(ankers.values()):
        fouten.append("ten minste één theorie-anker is verplicht "
                      "(mechanism_id, role_id of emergent_effect_id)")
    conn = get_db()
    for veld, tabel in (("mechanism_id", "mechanisms"), ("role_id", "roles"),
                        ("emergent_effect_id", "emergent_effects")):
        if ankers[veld]:
            rij = conn.execute(f"SELECT vervangen FROM {tabel} WHERE id = ?",
                               (ankers[veld],)).fetchone()
            if rij is None:
                fouten.append(f"{veld} #{ankers[veld]} bestaat niet")
            elif rij["vervangen"]:
                fouten.append(f"{veld} #{ankers[veld]} is vervangen (M2.6) — "
                              "veranker aan de opvolger (zie /api/lineage)")
    if fouten:
        conn.close()
        return jsonify({"error": "Voorspelling onvolledig", "fouten": fouten}), 400

    cur = conn.execute("""
        INSERT INTO predictions (claim, afleiding, meetcriterium, kans, deadline,
                                 mechanism_id, role_id, emergent_effect_id, contributed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (velden["claim"], velden["afleiding"], velden["meetcriterium"], kans, deadline,
         ankers["mechanism_id"], ankers["role_id"], ankers["emergent_effect_id"],
         g.user["username"]))
    pid = cur.lastrowid
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('predictions', ?, 'created', ?, ?, ?)""",
        (pid, g.user["username"],
         json.dumps({"claim": velden["claim"], "kans": kans, "deadline": deadline}),
         "Voorspelling vastgelegd vóór de uitkomst (M3.4)"))
    conn.commit()
    rij = _prediction_dict(conn.execute(
        "SELECT * FROM predictions WHERE id = ?", (pid,)).fetchone())
    conn.close()
    return jsonify(rij), 201


@app.route("/api/predictions/<int:pid>/uitkomst", methods=["PATCH"])
@require_user("reviewer")
def score_prediction(pid):
    """Uitkomst + Brier-score vastleggen (reviewer+). Alleen vanuit 'open';
    een gescoorde voorspelling is onveranderlijk — dat ís het register."""
    data = request.json or {}
    status = data.get("status")
    uitkomst = (data.get("uitkomst") or "").strip()
    if status not in PREDICTION_EINDSTATUSSEN:
        return jsonify({"error": f"status moet een van {PREDICTION_EINDSTATUSSEN} zijn"}), 400
    if not uitkomst:
        return jsonify({"error": "'uitkomst' is verplicht: wat gebeurde er, "
                                 "met bronverwijzing"}), 400

    conn = get_db()
    rij = conn.execute("SELECT * FROM predictions WHERE id = ?", (pid,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": f"Voorspelling #{pid} bestaat niet"}), 404
    if rij["status"] != "open":
        conn.close()
        return jsonify({"error": f"Voorspelling #{pid} is al gescoord "
                                 f"({rij['status']}) en onveranderlijk"}), 409

    brier = None
    if status == "uitgekomen":
        brier = round((rij["kans"] - 1.0) ** 2, 4)
    elif status == "niet_uitgekomen":
        brier = round(rij["kans"] ** 2, 4)
    self_scored = rij["contributed_by"] == g.user["username"]
    conn.execute("""
        UPDATE predictions SET status = ?, uitkomst = ?, brier = ?, self_scored = ?,
               beoordeeld_door = ?, beoordeeld_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (status, uitkomst, brier, self_scored, g.user["username"], pid))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('predictions', ?, 'updated', ?, ?, ?, ?)""",
        (pid, g.user["username"], json.dumps({"status": "open"}),
         json.dumps({"status": status, "brier": brier, "self_scored": self_scored}),
         "Uitkomst gescoord (M3.4)" + (" — zelf gescoord, heraudit-lijst" if self_scored else "")))
    conn.commit()
    nieuw = _prediction_dict(conn.execute(
        "SELECT * FROM predictions WHERE id = ?", (pid,)).fetchone())
    conn.close()
    return jsonify(nieuw)


# ── Afgeleide scores (live herberekening) ────────────────────

def _laatste_release():
    """Nieuwste release-snapshot in releases/ (M3.1), of None."""
    nieuwste, beste = None, ()
    for pad in RELEASES_PATH.glob("model-v*.json"):
        m = re.fullmatch(r"model-v(\d+)\.(\d+)\.(\d+)\.json", pad.name)
        if m and tuple(map(int, m.groups())) > beste:
            beste = tuple(map(int, m.groups()))
            nieuwste = pad
    if nieuwste is None:
        return None
    try:
        snap = json.loads(nieuwste.read_text())
        return {"versie": snap.get("versie"), "gegenereerd": snap.get("gegenereerd"),
                "titel": snap.get("titel")}
    except (OSError, json.JSONDecodeError):
        return None


@app.route("/api/health")
def get_health():
    """Gezondheidsdashboard (M0.5): zelfde checkfuncties als de validator-CLI,
    dus de cijfers hier zijn per constructie identiek aan scripts/validate_model.py.
    (Zonder linkrot-check; die blijft CLI-only achter --network.)

    Als scripts/analyse_gevoeligheid.py (M1.6) of scripts/onderzoeksagenda.py
    (M3.2) een rapport heeft geschreven, komt dat mee onder 'gevoeligheid'
    resp. 'onderzoeksagenda'; de nieuwste release (M3.1) onder 'release'."""
    conn = get_db()
    rapport = validation.run_all(conn)
    conn.close()
    for sleutel, bestand in (("gevoeligheid", "gevoeligheid.json"),
                             ("onderzoeksagenda", "onderzoeksagenda.json")):
        pad = Path(__file__).parent / "data" / bestand
        if pad.exists():
            try:
                rapport[sleutel] = json.loads(pad.read_text())
            except (OSError, json.JSONDecodeError):
                pass
    release = _laatste_release()
    if release:
        rapport["release"] = release
    return jsonify(rapport)


@app.route("/api/scores")
def get_scores():
    """Herbereken de volledige scoringsketen en geef alle afgeleide scores terug.

    De UI roept dit aan na een bewerking (argument, instantie) om panelen en de
    visuele codering te verversen zonder de hele pagina te regenereren.
    """
    conn = get_db()
    scores = scoring.compute_all_scores(
        conn, bridged_weights=scoring.bridged_weights_from_file(BRIDGING_PATH))
    conn.close()
    return jsonify(scores)


if __name__ == "__main__":
    print(f"Database: {DB_PATH}")
    print(f"Open: http://localhost:5000")
    app.run(debug=True, port=5000)
