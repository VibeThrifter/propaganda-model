"""Propaganda Model — webserver met discussieboom-API.

Start: python3 server.py
Open:  http://localhost:5000
"""
import csv
import datetime
import difflib
import functools
import hashlib
import hmac
import html
import json
import os
import io
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote, urlparse
from flask import Flask, g, jsonify, redirect, request, send_file, session

import auth  # wachtwoord-/token-hashing (M0.6)
import scoring  # scoringsketen: afgeleide praktijk- en theoriescores
import politiek  # politieke kleurmeter: ideologische positie uit gesourcete signalen
import tegenmacht  # machtsvalentie: tegenmacht als gerichte edge-valentie (geen categorie)
import doelgroep  # welstandsmeter: getargette marketing-/welstandsklasse per outlet
import bereik  # bereikmeter: gesourcet publieksbereik (kijkers/lezers/invullers) per jaar
import validation  # gezondheids-/consistentiechecks, gedeeld met scripts/validate_model.py
import voorstellen  # RfC's & granulariteitsbeheer (M2.3/M2.6), gedeeld met de tests
import viz_data  # graafdata voor de viz (W5.1), gedeeld met scripts/generate_viz.py
import paginas  # programmatic-SEO: server-gerenderde pagina per element (B4)
import subprocess  # herlaad de launchd-agents na een schema-wijziging (C1, macOS)
import agent_schedule  # canonieke agent-lijst + schema (gedeeld met de launchd-generator)
try:
    import dedup  # A6: semantische (paraphrase-)dedup bovenop difflib; aparte stdlib-module
except ImportError:  # de module wordt parallel gebouwd — val terug op alleen difflib
    dedup = None

ROOT = Path(__file__).parent
# Optionele env-override voor deploy (B1). Defaults blijven exact de repo-root, dus
# lokaal draaien (python3 server.py) verandert niets. PROPAGANDA_DATA_DIR verplaatst
# de hele data/-map (DB + secret_key + tokens) naar een persistent volume; de drie
# losse paden zijn daarnaast individueel te overschrijven.
DATA_DIR = Path(os.environ.get("PROPAGANDA_DATA_DIR", str(ROOT / "data")))
DB_PATH = Path(os.environ.get("PROPAGANDA_DB_PATH", str(DATA_DIR / "propaganda_model.db")))
WEB_PATH = Path(os.environ.get("PROPAGANDA_WEB_PATH", str(ROOT / "web")))
SECRET_KEY_PATH = Path(os.environ.get("PROPAGANDA_SECRET_KEY_PATH", str(DATA_DIR / "secret_key")))
REVIEW_ADVIES_PATH = DATA_DIR / "review_advies.json"
BRON_SUGGESTIES_PATH = DATA_DIR / "bron_suggesties.json"
VOORSPELLING_VOORSTELLEN_PATH = DATA_DIR / "voorspelling_voorstellen.json"
AUTO_MERGE_LOG_PATH = DATA_DIR / "auto_merge_log.json"
AGENT_RUNS_PATH = DATA_DIR / "agent_runs.jsonl"
RELEASES_PATH = ROOT / "releases"
# E1 (data-feed): de map met API-keys voor de gemeterde feed-namespace. Spiegelt
# data/tokens/ — één JSON-bestand per key, alléén de sha256-hash opgeslagen.
API_KEYS_DIR = Path(os.environ.get("PROPAGANDA_API_KEYS_DIR", str(DATA_DIR / "api_keys")))

# E1: gedeelde bouwer van de VERKOCHTE data-slice (neutraliteits-afbakening op één
# plek). Dient zowel de CSV-export (scripts/export_dataset.py) als de feed-API hier.
sys.path.insert(0, str(ROOT / "scripts"))
import export_dataset  # noqa: E402

app = Flask(__name__, static_folder=str(WEB_PATH), static_url_path="/static")

# ── Advertentie-CSP (B6) — SCAFFOLD, standaard leeg/uit ──────────────────
# De site draait volledig self-contained (geen externe scripts/cookies). Een
# advertentienetwerk is de éérste externe afhankelijkheid en krijgt daarom een
# eigen, PAD-GESCOPEDE Content-Security-Policy: alléén de element-pagina's (de
# SEO-longtail) mogen ad-/consent-domeinen laden. De viz (/) en de redactie-
# routes (/overleg, /beheer, /werkbank) blijven strikt self — een GLOBALE CSP
# zou de viz breken (die leunt zwaar op inline scripts). Leeg = de scaffold-
# staat: infra klaar, niets extern toegestaan. De eigenaar vult hieronder de
# domeinen van het gekozen netwerk in om te activeren (OWNER-ACTION). AdSense
# vergt daarbij doorgaans óók "'unsafe-inline'" in AD_CSP_SCRIPT_DOMEINEN.
AD_CSP_PADEN = ("/entiteit/", "/persoon/", "/mechanisme/", "/relatie/")
AD_CSP_SCRIPT_DOMEINEN = ()   # bv. "https://pagead2.googlesyndication.com", "https://*.googlesyndication.com", "'unsafe-inline'"
AD_CSP_FRAME_DOMEINEN = ()    # bv. "https://googleads.g.doubleclick.net", "https://*.safeframe.googlesyndication.com"
AD_CSP_IMG_DOMEINEN = ()      # bv. "https://*.g.doubleclick.net", "https://*.googlesyndication.com"
AD_CSP_CONNECT_DOMEINEN = ()  # bv. "https://*.google.com", "https://*.googlesyndication.com"


@app.after_request
def _no_cache_html(resp):
    # HTML-pagina's (viz, /overleg, …) tonen live data; zonder dit blijft de
    # browser een oude kopie tonen en lijkt nieuwe data te ontbreken.
    if resp.mimetype == "text/html":
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    return resp


@app.after_request
def _csp_element_paginas(resp):
    # Content-Security-Policy UITSLUITEND op de B6-element-pagina's (zie de
    # AD_CSP_*-constanten hierboven). KRITISCH: nooit op / (viz — inline scripts)
    # of de redactie-routes; die krijgen géén CSP-wijziging. Standaard (lege
    # domein-tuples) is dit een strikte self-CSP die de element-pagina's precies
    # zo laat werken als nu (eigen /static-scripts + inline <style> + self-fonts),
    # met de ad-/consent-domeinen als uit-geconfigureerde uitbreidingspunten.
    pad = request.path or ""
    if resp.mimetype != "text/html" or not any(pad.startswith(p) for p in AD_CSP_PADEN):
        return resp
    script = " ".join(("'self'",) + tuple(AD_CSP_SCRIPT_DOMEINEN))
    img = " ".join(("'self'", "data:") + tuple(AD_CSP_IMG_DOMEINEN))
    frame = " ".join(("'self'",) + tuple(AD_CSP_FRAME_DOMEINEN))
    connect = " ".join(("'self'",) + tuple(AD_CSP_CONNECT_DOMEINEN))
    resp.headers["Content-Security-Policy"] = "; ".join([
        "default-src 'self'",
        f"script-src {script}",
        "style-src 'self' 'unsafe-inline'",  # de pagina heeft een inline <style>-blok
        f"img-src {img}",
        f"frame-src {frame}",
        f"connect-src {connect}",
        "base-uri 'self'",
        "form-action 'self'",
    ])
    return resp


def _secret_key():
    """Sessiesleutel op schijf (gitignored), zodat sessies een herstart overleven."""
    if not SECRET_KEY_PATH.exists():
        SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SECRET_KEY_PATH.write_bytes(os.urandom(32))
        SECRET_KEY_PATH.chmod(0o600)
    return SECRET_KEY_PATH.read_bytes()


app.secret_key = _secret_key()


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # B1: veilig onder meerdere gunicorn-workers. WAL laat lezen-tijdens-schrijven
    # toe (de auto-merge-service schrijft terwijl bezoekers lezen); busy_timeout
    # laat een gelijktijdige schrijver even wachten i.p.v. direct 'database is locked'.
    # WAL is een persistente DB-file-instelling (één keer zetten volstaat), maar het
    # herhalen is goedkoop en robuust bij een verse build.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
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
# Vrijgesteld van de rate limit: de maintainer-rol (admin — bewuste mensbesluiten), het
# vaste bijdrage-account 'assistent', en het reviewer-tier systeemaccount 'merge-service'
# (A7/C2: de auto-merge-service pace't zelf; de 60/min-limiet zou anders de doorvoer knellen).
# Overige bijdragers/agents houden hun trap-limiet als flood-rem tegen een doorgeslagen agent-lus.
# Epic 12 (2026-09-30): ook 'nieuws-autokeur' — hetzelfde soort reviewer-tier systeemaccount
# als merge-service; de service pace't zelf en het harde dagplafond (standaard 60) is de
# echte rem. De bijdrager-accounts 'nieuws-agent'/'nieuws-scout' blijven bewust NIET
# vrijgesteld (hun inhouds-schrijfacties houden de flood-rem); alleen hun wachtrij-
# endpoints zijn vrij (RATE_LIMIT_VRIJE_ENDPOINTS hieronder).
RATE_LIMIT_VRIJGESTELD = {"assistent", "merge-service", "nieuws-autokeur",
                          "register-import", "registercheck"}  # Uitbreiding C: registerpijplijn
# Endpoints die voor ELK account buiten de per-account-limiet vallen: de nieuws-wachtrij
# (nieuws_doelen) is procesmetadata, geen modelinhoud — de rate limit beschermt tegen
# score-manipulatie door volume en heeft hier geen functie, terwijl de nieuws-backend per
# cyclus ~12–30 doelen tegelijk aanbiedt. Wie hier mag schrijven, poorten de endpoints zelf
# (nieuws-agent/nieuws-scout/maintainer). Idem de voorrang uit het nieuws (2026-10-06).
RATE_LIMIT_VRIJE_ENDPOINTS = {"nieuws_doelen_upsert", "nieuws_doelen_claim_volgende",
                              "nieuws_doelen_claim", "nieuws_doelen_patch", "nieuws_voorrang"}


def _rate_limit_ok(user) -> bool:
    if user["role"] == "maintainer" or user.get("username") in RATE_LIMIT_VRIJGESTELD:
        return True
    nu = time.monotonic()
    emmer = _rate_emmers.setdefault(user["id"], [])
    emmer[:] = [t for t in emmer if nu - t < RATE_WINDOW]
    if len(emmer) >= RATE_LIMITS.get(user["role"], 30):
        return False
    emmer.append(nu)
    return True


# ── API-key-gating + lees-metering (E1, data-feed) ───────────
# Hergebruikt het write-side rate-limit-patroon (emmer per RATE_WINDOW), maar dan
# op een LEES-quotum en op een APARTE feed-namespace (/api/feed/*). De publieke
# /api/graph_data + de metriek-endpoints blijven open en ongemeterd — de portal-
# loader hangt eraan. Sleutel-opslag spiegelt data/tokens/: één JSON per key
# (`{"naam","tier","key_hash"}`), alléén de sha256-hash op schijf (auth.hash_token).
FEED_QUOTA = {"proef": 20, "feed": 240, "onbeperkt": None}  # leesverzoeken per RATE_WINDOW
_read_emmers = {}


def _api_keys_map() -> dict:
    """{key_hash: {"naam","tier"}} uit data/api_keys/*.json. Per-request gescand
    (weinig keys); een onbekende/ongeldige tier valt terug op 'feed'."""
    out = {}
    if not API_KEYS_DIR.exists():
        return out
    for p in API_KEYS_DIR.glob("*.json"):
        try:
            d = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        kh = d.get("key_hash")
        if kh:
            tier = d.get("tier") if d.get("tier") in FEED_QUOTA else "feed"
            out[kh] = {"naam": d.get("naam", p.stem), "tier": tier}
    return out


def _lees_api_key() -> str:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[len("Bearer "):].strip()
    return (request.args.get("key") or "").strip()


def _read_meter_ok(key_hash, tier) -> bool:
    limiet = FEED_QUOTA.get(tier)
    if limiet is None:                       # 'onbeperkt'-tier
        return True
    nu = time.monotonic()
    emmer = _read_emmers.setdefault(key_hash, [])
    emmer[:] = [t for t in emmer if nu - t < RATE_WINDOW]
    if len(emmer) >= limiet:
        return False
    emmer.append(nu)
    return True


def require_api_key(min_tier=None):
    """Poort voor de betaalde feed-namespace. Geen key → 401; onbekende key → 401;
    boven het lees-quotum van de tier → 429 (zelfde meldingsvorm als de write-side)."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = _lees_api_key()
            if not key:
                return jsonify({"error": "API-key vereist: Authorization: Bearer "
                                         "<key> of ?key=<key>"}), 401
            kh = auth.hash_token(key)
            rec = _api_keys_map().get(kh)
            if rec is None:
                return jsonify({"error": "Ongeldige API-key"}), 401
            if not _read_meter_ok(kh, rec["tier"]):
                return jsonify({"error": "Lees-quotum bereikt: maximaal "
                                         f"{FEED_QUOTA.get(rec['tier'])} feed-verzoeken "
                                         f"per {int(RATE_WINDOW)} s"}), 429
            g.api_key = rec
            return fn(*args, **kwargs)
        return wrapper
    return decorator


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
                    and request.endpoint not in RATE_LIMIT_VRIJE_ENDPOINTS
                    and not _rate_limit_ok(g.user)):
                return jsonify({"error": "Rate limit bereikt: maximaal "
                                         f"{RATE_LIMITS.get(g.user['role'], 30)} "
                                         "schrijfacties per minuut"}), 429
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_user_page(min_rol="bijdrager"):
    """Pagina-poort (B3): een niet-ingelogde bezoeker wordt naar /login?next=<pad>
    geredirect (HTTP 302) i.p.v. een JSON-401 te krijgen (die 401 is prima voor de
    API's maar lelijk voor een HTML-pagina). De echte datalaag-poorten zitten al op
    de API's; dit schermt alleen de redactie-*pagina's* af zodat ze niet als publieke,
    indexeerbare surface uitlekken."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            conn = get_db()
            rij = _zoek_user(conn)
            conn.close()
            if rij is None:
                pad = request.full_path.rstrip("?")
                return redirect(f"/login?next={quote(pad, safe='/')}", code=302)
            if ROLE_ORDER.get(rij["role"], 0) < ROLE_ORDER[min_rol]:
                # Ingelogd maar te lage rol: naar de leessurface, niet naar login.
                return redirect("/", code=302)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/login")
def login_page():
    return send_file(WEB_PATH / "login.html")


@app.route("/account")
def account_page():
    return send_file(WEB_PATH / "account.html")


@app.route("/methode")
def methode_page():
    """Publieke methodologie-/verantwoordingspagina (B2 + J1): de vijf filters, de
    scoring-/bewijsdiscipline, de redactionele verantwoording, de neutraliteits-
    verklaring, de disclaimer en de art. 43-UAVG-grondslag. Openbaar (geen gate) —
    dit is het juridische schild en moet vindbaar zijn vanaf de voordeur."""
    return send_file(WEB_PATH / "methode.html")


@app.route("/docs/openapi.yaml")
def openapi_spec():
    """OpenAPI-beschrijving van de PUBLIEKE + VERKOCHTE GET-vormen van de data-feed
    (E1). Bevat bewust NIET /api/kleurmeter of /api/machtsvalentie (uitgesloten laag)."""
    return send_file(ROOT / "docs" / "openapi.yaml", mimetype="application/yaml")


@app.route("/robots.txt")
def robots_txt():
    """Weert de redactie-/account-routes en de API uit de zoekindex, maar houdt de
    deelbare graafdata (GET /api/graph_data) expliciet toegankelijk (feed-verhaal E1)."""
    return send_file(ROOT / "robots.txt", mimetype="text/plain")


@app.route("/beheer")
@require_user_page("maintainer")
def beheer_page():
    """Accountbeheer voor maintainers: rollen, filterrollen en (de)activeren via het
    web — zodat een reviewer onboarden geen shell-toegang meer vergt. De pagina toont
    alleen iets als /api/me maintainer is; de echte poort zit op /api/users."""
    return send_file(WEB_PATH / "beheer.html")


@app.route("/beheer/acties")
@require_user_page("maintainer")
def acties_page():
    """Owner-acties-overzicht: de hand-offs uit de gefaseerde monetisatie-bouw
    (fase 1-6) die bewust aan de eigenaar zijn overgelaten — deploy, agents/timers
    aanzetten, auto-merge inschakelen, prose/archivering draaien, ads activeren,
    feed-key minten. Statisch checklist (afvinken lokaal bewaard) + een live
    systeemstatus-strip uit /api/toezicht. Maintainer-only, achter de B3-gate."""
    return send_file(WEB_PATH / "acties.html")


@app.route("/werkbank")
@require_user_page("bijdrager")
def werkbank_page():
    """Mijn werkbank: het eigen ingediende werk (argumenten, voorstellen, praktijk)
    met de ontvangen feedback en knoppen om te bewerken, reviseren of opnieuw in te
    dienen — de aparte indien-/verbeterplek (Fase E)."""
    return send_file(WEB_PATH / "werkbank.html")


@app.route("/overleg")
@require_user_page("bijdrager")
def overleg_page():
    """Overlegpagina (Wikipedia-stijl 'Overleg'): alle threads én open
    voorstellen/RfC's op een eigen volledige pagina, los van de netwerkviz."""
    return send_file(WEB_PATH / "overleg.html")


@app.route("/overleg/voorstel/<int:vid>")
@require_user_page("bijdrager")
def overleg_voorstel_page(vid):
    """Permalink-pagina van één RfC/voorstel — het 'dakloze' nieuwe theorie-element
    dat (nog) geen knoop in de graaf heeft en dus een eigen adresseerbare pagina
    verdient. Dezelfde overleg.html leidt het voorstel uit de pathname af."""
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


@app.route("/api/account/password", methods=["POST"])
@require_user()
def api_change_password():
    """Self-service wachtwoord wijzigen (alleen mensen). Vereist het huidige
    wachtwoord, tenzij er nog geen staat (eerste keer instellen)."""
    if g.user["kind"] != "mens":
        return jsonify({"error": "Wachtwoorden zijn alleen voor mensen; "
                                 "agents gebruiken een Bearer-token"}), 400
    data = request.json or {}
    huidig = data.get("huidig") or data.get("old_password") or ""
    nieuw = data.get("nieuw") or data.get("new_password") or ""
    if len(nieuw) < 8:
        return jsonify({"error": "Nieuw wachtwoord: minimaal 8 tekens"}), 400
    conn = get_db()
    rij = conn.execute("SELECT password_hash FROM users WHERE id = ?",
                       (g.user["id"],)).fetchone()
    if rij["password_hash"] and not auth.verify_password(huidig, rij["password_hash"]):
        conn.close()
        return jsonify({"error": "Huidig wachtwoord onjuist"}), 403
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                 (auth.hash_password(nieuw), g.user["id"]))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ── Accountbeheer (maintainer) ───────────────────────────────
# Rollen, filterrollen en (de)activeren via het web. De CLI (scripts/create_user.py)
# blijft bestaan; dit is dezelfde macht zonder shell-toegang. Poort overal: maintainer.

def _aantal_actieve_maintainers(conn, behalve_id=None):
    if behalve_id is None:
        return conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='maintainer' AND active").fetchone()[0]
    return conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='maintainer' AND active AND id != ?",
        (behalve_id,)).fetchone()[0]


@app.route("/api/users", methods=["GET"])
@require_user("maintainer")
def api_users_list():
    """Alle accounts met rol, filterrollen en status (geen hashes — alleen of er een
    wachtwoord/token ís). Maintainer-only: dit is gevoelige beheerinfo."""
    conn = get_db()
    filterrollen = {}
    for fr in conn.execute("SELECT user_id, filter, rol FROM user_filter_rollen"):
        filterrollen.setdefault(fr["user_id"], {})[fr["filter"]] = fr["rol"]
    users = []
    for u in conn.execute(
            "SELECT id, username, kind, role, active, provenance, created_at, "
            "last_login_at, token_hash IS NOT NULL AS heeft_token, "
            "password_hash IS NOT NULL AS heeft_wachtwoord FROM users "
            "ORDER BY active DESC, role DESC, username"):
        users.append({
            "id": u["id"], "username": u["username"], "kind": u["kind"],
            "role": u["role"], "active": bool(u["active"]),
            "provenance": u["provenance"], "created_at": u["created_at"],
            "last_login_at": u["last_login_at"],
            "heeft_token": bool(u["heeft_token"]),
            "heeft_wachtwoord": bool(u["heeft_wachtwoord"]),
            "is_zelf": u["id"] == g.user["id"],
            "filterrollen": filterrollen.get(u["id"], {})})
    conn.close()
    return jsonify({"users": users, "filters": sorted(FILTERS)})


@app.route("/api/users", methods=["POST"])
@require_user("maintainer")
def api_users_create():
    """Nieuw account aanmaken — mens (met initieel wachtwoord) of agent (met
    provenance; geeft één keer een Bearer-token terug). Onboarding zonder terminal."""
    data = request.json or {}
    naam = (data.get("username") or "").strip()
    kind = data.get("kind") or "mens"
    rol = data.get("role") or "bijdrager"
    if not naam:
        return jsonify({"error": "username verplicht"}), 400
    if kind not in ("mens", "agent"):
        return jsonify({"error": "kind moet 'mens' of 'agent' zijn"}), 400
    if rol not in ROLE_ORDER:
        return jsonify({"error": f"rol moet een van {tuple(ROLE_ORDER)} zijn"}), 400
    conn = get_db()
    if conn.execute("SELECT 1 FROM users WHERE username = ?", (naam,)).fetchone():
        conn.close()
        return jsonify({"error": "Gebruikersnaam bestaat al"}), 409
    token = None
    if kind == "agent":
        prov = (data.get("provenance") or "").strip()
        if not prov:
            conn.close()
            return jsonify({"error": "Een agent-account vereist provenance "
                                     "(model + versie)"}), 400
        token = auth.new_token()
        cur = conn.execute(
            "INSERT INTO users (username, kind, role, provenance, token_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            (naam, kind, rol, prov, auth.hash_token(token)))
    else:
        pw = data.get("wachtwoord") or data.get("password") or ""
        if len(pw) < 8:
            conn.close()
            return jsonify({"error": "Initieel wachtwoord: minimaal 8 tekens"}), 400
        cur = conn.execute(
            "INSERT INTO users (username, kind, role, password_hash) VALUES (?, ?, ?, ?)",
            (naam, kind, rol, auth.hash_password(pw)))
    uid = cur.lastrowid
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value)
                    VALUES ('users', ?, 'created', ?, ?)""",
                 (uid, g.user["username"],
                  json.dumps({"username": naam, "kind": kind, "role": rol})))
    conn.commit()
    conn.close()
    resp = {"id": uid, "username": naam, "kind": kind, "role": rol}
    if token:
        resp["token"] = token
        resp["let_op"] = ("Geef dit token één keer door — alleen de hash is bewaard.")
    return jsonify(resp), 201


@app.route("/api/users/<int:uid>", methods=["PATCH"])
@require_user("maintainer")
def api_users_update(uid):
    """Globale rol en/of actief-status zetten. Bewaakt: niemand wijzigt z'n eigen
    rol/status hier (lockout-risico — gebruik /account), en er moet altijd minstens
    één actieve maintainer overblijven."""
    data = request.json or {}
    conn = get_db()
    u = conn.execute("SELECT id, username, role, active FROM users WHERE id = ?",
                     (uid,)).fetchone()
    if not u:
        conn.close()
        return jsonify({"error": "Gebruiker niet gevonden"}), 404
    if uid == g.user["id"]:
        conn.close()
        return jsonify({"error": "Je eigen rol/status wijzig je hier niet "
                                 "(lockout-risico) — laat een andere maintainer dat doen"}), 400
    updates = {}
    if "role" in data and data["role"] is not None:
        if data["role"] not in ROLE_ORDER:
            conn.close()
            return jsonify({"error": f"rol moet een van {tuple(ROLE_ORDER)} zijn"}), 400
        updates["role"] = data["role"]
    if "active" in data and data["active"] is not None:
        updates["active"] = 1 if data["active"] else 0
    if not updates:
        conn.close()
        return jsonify({"error": "niets te wijzigen (geef role en/of active)"}), 400
    # Invariant: minstens één actieve maintainer moet overblijven.
    blijft_actieve_maintainer = (updates.get("role", u["role"]) == "maintainer"
                                 and updates.get("active", u["active"]))
    was_actieve_maintainer = u["role"] == "maintainer" and u["active"]
    if (was_actieve_maintainer and not blijft_actieve_maintainer
            and _aantal_actieve_maintainers(conn, behalve_id=uid) == 0):
        conn.close()
        return jsonify({"error": "Dit zou de laatste actieve maintainer verwijderen "
                                 "— promoveer eerst iemand anders"}), 400
    sets = ", ".join(f"{k} = ?" for k in updates)
    conn.execute(f"UPDATE users SET {sets} WHERE id = ?", (*updates.values(), uid))
    weergave = {k: (bool(v) if k == "active" else v) for k, v in updates.items()}
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value)
                    VALUES ('users', ?, 'updated', ?, ?, ?)""",
                 (uid, g.user["username"],
                  json.dumps({"role": u["role"], "active": bool(u["active"])}),
                  json.dumps(weergave)))
    conn.commit()
    conn.close()
    return jsonify({"id": uid, **weergave})


@app.route("/api/users/<int:uid>/filterrol", methods=["POST"])
@require_user("maintainer")
def api_users_filterrol(uid):
    """Filterrol (reviewer/maintainer voor één propagandafilter) zetten of intrekken
    (lege rol = intrekken). De effectieve rol binnen een filter = max(globaal, filterrol)."""
    data = request.json or {}
    filt = (data.get("filter") or "").strip()
    rol = (data.get("rol") or "").strip()
    if filt not in FILTERS:
        return jsonify({"error": f"filter moet een van {sorted(FILTERS)} zijn"}), 400
    conn = get_db()
    if not conn.execute("SELECT 1 FROM users WHERE id = ?", (uid,)).fetchone():
        conn.close()
        return jsonify({"error": "Gebruiker niet gevonden"}), 404
    if rol == "":
        conn.execute("DELETE FROM user_filter_rollen WHERE user_id = ? AND filter = ?",
                     (uid, filt))
        actie = {"filter": filt, "rol": None}
    elif rol not in ("reviewer", "maintainer"):
        conn.close()
        return jsonify({"error": "filterrol moet 'reviewer' of 'maintainer' zijn "
                                 "(of leeg laten = intrekken)"}), 400
    else:
        conn.execute("""INSERT INTO user_filter_rollen (user_id, filter, rol) VALUES (?, ?, ?)
                        ON CONFLICT (user_id, filter) DO UPDATE SET rol = excluded.rol""",
                     (uid, filt, rol))
        actie = {"filter": filt, "rol": rol}
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value)
                    VALUES ('users', ?, 'updated', ?, ?)""",
                 (uid, g.user["username"], json.dumps({"filterrol": actie})))
    conn.commit()
    conn.close()
    return jsonify({"id": uid, **actie})


# ── Pagina's ─────────────────────────────────────────────────

@app.route("/")
def index():
    # Dunne pagina (W5.1): web/template.html zelf, mét de "%%DATA%%"-sentinel er
    # nog in — de boot-loader in de pagina haalt de graafdata live via
    # GET /api/graph_data. De statische export (scripts/generate_viz.py →
    # web/index.html) hangt hier niet meer onder; die blijft bereikbaar als
    # /static/index.html. No-cache komt uit _no_cache_html.
    return send_file(WEB_PATH / "template.html")


# ── Graafdata voor de visualisatie (W5.1) ────────────────────
# De pagina op / is dun; de data komt live hiervandaan. Een mtime-cache voorkomt
# dat elke paginalaad de volledige scoringsketen (~0,75 s) opnieuw draait: de
# sleutel verandert zodra de DB of de nieuwste release verandert —
# precies de twee inputs van viz_data.export_data.
_graph_cache = {}


def _graph_cache_key():
    def _stat(p):
        try:
            st = p.stat()
            return (st.st_mtime_ns, st.st_size)
        except OSError:
            return (0, 0)
    nieuwste_release = max((_stat(p) for p in RELEASES_PATH.glob("model-v*.json")),
                           default=(0, 0))
    return (_stat(DB_PATH), nieuwste_release)


@app.route("/api/graph_data")
def graph_data():
    """Volledige viz-datastructuur (entiteiten, relaties, theorielaag, discussiebomen,
    afgeleide scores, kleurmeter, inkomsten) — identiek aan wat de statische export
    in web/index.html bakt (zelfde bouw: viz_data.export_data)."""
    sleutel = _graph_cache_key()
    entry = _graph_cache.get("entry")
    if entry is None or entry[0] != sleutel:
        conn = get_db()
        try:
            data = viz_data.export_data(conn)
        finally:
            conn.close()
        entry = (sleutel, json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        _graph_cache["entry"] = entry
    return app.response_class(entry[1], mimetype="application/json")


# ── Programmatic-SEO: server-gerenderde pagina per element (B4) ──────────────
# Publiek, geen auth-gate: dit is de crawlbare leessurface. Elk element krijgt een
# stabiele, id-geprefixte URL met unieke <title>/<meta>/<canonical>/OG/H1 + interne
# links. De renderkost wordt gedempt met dezelfde mtime-cache als /api/graph_data
# (paginas.py). Een niet-canonieke tekst-slug → 301; onbekend/vervangen/afgewezen → 404.

def _ssr_respond(res):
    if res is None:
        return ("Niet gevonden.", 404)
    if isinstance(res, paginas.Redirect):
        return redirect(res.pad, code=301)
    return res  # HTML-string → Flask levert text/html


@app.route("/entiteit/<slug>")
def entiteit_page(slug):
    conn = get_db()
    try:
        res = paginas.render_entiteit(conn, slug, request.url_root, soort="entiteit")
    finally:
        conn.close()
    return _ssr_respond(res)


@app.route("/persoon/<slug>")
def persoon_page(slug):
    conn = get_db()
    try:
        res = paginas.render_entiteit(conn, slug, request.url_root, soort="persoon")
    finally:
        conn.close()
    return _ssr_respond(res)


@app.route("/mechanisme/<slug>")
def mechanisme_page(slug):
    conn = get_db()
    try:
        res = paginas.render_mechanisme(conn, slug, request.url_root)
    finally:
        conn.close()
    return _ssr_respond(res)


@app.route("/relatie/<int:rid>")
def relatie_page(rid):
    conn = get_db()
    try:
        res = paginas.render_relatie(conn, rid, request.url_root)
    finally:
        conn.close()
    return _ssr_respond(res)


@app.route("/overzicht")
def overzicht_page():
    """Publiek blader-overzicht (index) van alle entiteiten + mechanismen, elk gelinkt
    naar hun SSR-pagina — de menselijke ingang tot de longtail-pagina's (die anders
    alleen via de sitemap/zoekmachine bereikbaar zijn). Gelinkt vanuit de voettekst."""
    conn = get_db()
    try:
        html = paginas.render_overzicht(conn, request.url_root)
    finally:
        conn.close()
    return html


@app.route("/sitemap.xml")
def sitemap_xml_route():
    conn = get_db()
    try:
        xml = paginas.sitemap_xml(conn, request.url_root)
    finally:
        conn.close()
    return app.response_class(xml, mimetype="application/xml")


# ── Argumenten API ───────────────────────────────────────────

def _locatie_link(location_type, location):
    """Klikbare URL voor een source_location, of None als niet web-koppelbaar."""
    if location_type in ("url", "archive_url"):
        return location
    if location_type == "doi":
        return f"https://doi.org/{location}"
    if location_type == "handle":
        return f"https://hdl.handle.net/{location}"
    return None  # isbn/file: geen directe weblink


def _citaties_per_argument(conn, arg_ids):
    """{arg_id: [citatie-dicts]} met bron, betrouwbaarheid en (waar aanwezig) een
    klikbare link + archieflink. Een citatie is **echt** als ze een quote draagt
    OF haar bron een vindplaats (locator) heeft — een kale titel-stub is dat niet.
    Gedeeld door /api/arguments, /api/review_queue en de viz-generator."""
    arg_ids = list(arg_ids)
    if not arg_ids:
        return {}
    qs = ",".join("?" * len(arg_ids))
    rows = conn.execute(f"""
        SELECT c.id, c.argument_id, c.quote, c.page, c.section, c.context,
               c.source_id, s.title AS source_title, s.author AS source_author,
               s.reliability, s.onderwerp, s.date_published
        FROM citations c JOIN sources s ON c.source_id = s.id
        WHERE c.argument_id IN ({qs}) ORDER BY c.id""", arg_ids).fetchall()
    bron_ids = {r["source_id"] for r in rows}
    locs = {}
    if bron_ids:
        lqs = ",".join("?" * len(bron_ids))
        for l in conn.execute(
                f"SELECT source_id, location_type, location FROM source_locations "
                f"WHERE source_id IN ({lqs})", list(bron_ids)):
            locs.setdefault(l["source_id"], []).append((l["location_type"], l["location"]))
    out = {}
    for r in rows:
        sl = locs.get(r["source_id"], [])
        link = next((_locatie_link(t, v) for t, v in sl if _locatie_link(t, v)), None)
        archive = next((v for t, v in sl if t == "archive_url"), None)
        has_locator = bool(sl)
        out.setdefault(r["argument_id"], []).append({
            "id": r["id"], "quote": r["quote"], "page": r["page"],
            "section": r["section"], "context": r["context"],
            "source_id": r["source_id"], "source_title": r["source_title"],
            "source_author": r["source_author"], "reliability": r["reliability"],
            "onderwerp": r["onderwerp"], "source_date": r["date_published"],
            "url": link, "archive_url": archive, "has_locator": has_locator,
            "echt": bool((r["quote"] or "").strip()) or has_locator,
        })
    return out


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
               s.title as source_title, s.author as source_author, s.reliability, s.onderwerp,
               u.kind as auteur_kind, u.role as auteur_rol
        FROM arguments a
        JOIN boom ON a.id = boom.id
        LEFT JOIN citations c ON c.argument_id = a.id
        LEFT JOIN sources s ON c.source_id = s.id
        LEFT JOIN users u ON u.username = a.contributed_by
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
                "bezwaar_resolutie": row["bezwaar_resolutie"],
                "contributed_by": row["contributed_by"],
                "auteur_is_agent": (row["auteur_kind"] == "agent"),
                "auteur_is_admin": (row["auteur_rol"] == "maintainer"),
                "created_at": row["created_at"],
                "vervangen": row["vervangen"],
                "reviseert_id": row["reviseert_id"],
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
                "onderwerp": row["onderwerp"],
            })

    # De 👍/👎-ratinglaag (M2.5) is bij de solo+agents-kanteling geschrapt (A3): bij n=1
    # was ze inert. De tabel argument_ratings blijft bevroren (audit) maar wordt niet meer
    # uitgelezen; de velden blijven leeg zodat de front-end netjes degradeert.
    for a in args_map.values():
        a["ratings"] = {"mens": {"nuttig": 0, "niet_nuttig": 0},
                        "agent": {"nuttig": 0, "niet_nuttig": 0}}
        a["mijn_oordeel"] = None

    # Verrijk citaties met vindplaats/link (vervangt de kale join hierboven), zodat
    # de discussieboom de bron klikbaar kan tonen.
    cites = _citaties_per_argument(conn, args_map.keys())
    for aid, a in args_map.items():
        a["citations"] = cites.get(aid, [])

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

    # Threads toont de discussie van het LEVENDE model: alléén goedgekeurde praktijk-
    # elementen (entiteiten/relaties). Een nog-voorgesteld element zit in de Voorstellen-
    # wachtrij en een afgewezen element in de Afgewezen-flow — die horen niet óók als losse
    # thread hier (dat was 'raar en dubbel'). Theorie-elementen (rollen/mechanismen/velden)
    # zijn altijd levend (ontstaan via RfC) en blijven dus ongefilterd.
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
        WHERE r.status = 'goedgekeurd'
        GROUP BY r.id ORDER BY label
    """)

    mechanismen = groepeer("""
        SELECT t.id, t.name AS label, COALESCE(t.filter, '') AS filter, COUNT(*) AS n,
               SUM(CASE WHEN a.status = 'voorgesteld' THEN 1 ELSE 0 END) AS n_open
        FROM arguments a JOIN mechanisms t ON a.mechanism_id = t.id
        GROUP BY t.id ORDER BY label
    """)

    def simpel(tabel, kol, alleen_goedgekeurd=False):
        waar = "WHERE t.status = 'goedgekeurd'" if alleen_goedgekeurd else ""
        return groepeer(f"""
            SELECT t.id, t.name AS label, COUNT(*) AS n,
                   SUM(CASE WHEN a.status = 'voorgesteld' THEN 1 ELSE 0 END) AS n_open
            FROM arguments a JOIN {tabel} t ON a.{kol} = t.id
            {waar}
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
        "entiteiten": simpel("entities", "entity_id", alleen_goedgekeurd=True),
        "rollen": simpel("roles", "role_id"),
        "mechanismen": mechanismen,
        "emergente_velden": emergente_velden,
    }

    # n_bezwaar (W3.1): lopende resolutielussen per thread — ondergravingen die op
    # afhandeling wachten ('open' wacht op de auteur, 'herzien' op herbeoordeling door
    # de bezwaarmaker; 'blijft'/'opgelost' zijn afgehandeld). Alleen mee-tellende
    # ondergravingen: gemerged (niet 'voorgesteld' — die staan in de reviewwachtrij),
    # niet verworpen, niet vervangen. Reacties dragen geen doel (M1.1), dus de
    # recursieve keten zoekt per ondergraving de thread-wortel.
    bezwaar_rows = conn.execute("""
        WITH RECURSIVE keten(id, wortel) AS (
            SELECT id, id FROM arguments WHERE parent_argument_id IS NULL
            UNION ALL
            SELECT a.id, k.wortel FROM arguments a JOIN keten k ON a.parent_argument_id = k.id
        )
        SELECT w.relation_id, w.entity_id, w.role_id, w.mechanism_id, w.emergent_effect_id,
               COUNT(*) AS n
        FROM arguments ond
        JOIN keten k ON k.id = ond.id
        JOIN arguments w ON w.id = k.wortel
        WHERE ond.parent_argument_id IS NOT NULL
          AND ond.stance = 'contradicting'
          AND ond.bezwaar_resolutie IN ('open', 'herzien')
          AND NOT ond.vervangen
          AND ond.status NOT IN ('voorgesteld', 'verworpen')
        GROUP BY 1, 2, 3, 4, 5
    """).fetchall()
    bezwaar = {}
    kolom_per_groep = {"relaties": "relation_id", "entiteiten": "entity_id",
                       "rollen": "role_id", "mechanismen": "mechanism_id",
                       "emergente_velden": "emergent_effect_id"}
    for r in bezwaar_rows:
        for groep, kol in kolom_per_groep.items():
            if r[kol] is not None:
                bezwaar[(groep, r[kol])] = bezwaar.get((groep, r[kol]), 0) + r["n"]
    for groep, items in uit.items():
        for it in items:
            it["n_bezwaar"] = bezwaar.get((groep, it["id"]), 0)

    conn.close()
    return jsonify(uit)


# Filter-enum voor classificatie-aspect 'filter' (unie van de roles- en
# mechanisms-CHECK in schema.sql); property_value moet hier een van zijn.
FILTERS = {"eigendom", "advertentie", "sourcing", "flak", "ideologie",
           "cross_filter", "systeemactor", "tegenmacht", "overig",
           # Uitbreiding C (besluitvorming, eigenaarsbesluit 2026-10-07): zelfde netwerk
           "formele_macht", "belangen", "kennis_advies", "polder", "werving"}

# Provenance-methode-tier (A5): de toegestane methode-waarden op een citatie.
METHODES = tuple(scoring.METHODE_FACTOR)


def _methode_fout(methode, quote):
    """Valideer een citatie-methode (A5). Geen reviewer-poort: methode is een MECHANISCH
    feit (verbatim gekopieerd of LLM-samengevat), geen oordeel zoals reliability — de
    A1-verbatim-herverificatie is de teeth. Retourneert een foutstring, of None als ok.
    NULL/afwezig is toegestaan (neutrale factor 1,0)."""
    if methode is None:
        return None
    if methode not in scoring.METHODE_FACTOR:
        return "Ongeldige methode. Kies uit: " + ", ".join(METHODES)
    prob = validation.methode_consistentie(methode, quote)
    return prob[0] if prob else None


# ── Smaad-firewall (D2.3, Laag 3) ────────────────────────────
# Negatief-feitelijk lexicon: woorden die een beschuldiging van een strafbaar/
# verwijtbaar FEIT dragen (geen geattribueerde mening). De heuristiek is bewust
# conservatief (liever te veel dan te weinig in de eigenaars-wachtrij) — een agent-
# classificatie in de corroboratie-brief (D2.2) is de tweede laag. Woordgrens-match
# op de kleine letters van de claim (+reasoning). Uitbreidbaar.
SMAAD_LEXICON = {
    "fraude", "fraudeur", "frauduleus", "corrupt", "corruptie", "omkoping", "omkoopt",
    "omgekocht", "liegt", "loog", "liegen", "leugen", "leugens", "leugenaar",
    "belangenverstrengeling", "veroordeeld", "veroordeling", "crimineel", "criminele",
    "misdaad", "misdrijf", "oplichting", "oplichter", "oplicht", "witwassen", "witwast",
    "witwaste", "verduistering", "verduistert", "verduisterde", "chantage", "chanteert",
    "smaad", "laster", "plagiaat", "misbruik", "aanranding", "verkrachting", "racist",
    "racisme", "nepotisme", "vriendjespolitiek", "malversatie", "malversaties",
    "machtsmisbruik", "intimidatie", "intimideert", "pedofiel", "dief", "steelt",
    "gestolen", "bedrog", "bedriegt", "valsheid", "meineed", "omkopen", "zwendel",
}
_SMAAD_PATROON = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in sorted(SMAAD_LEXICON)) + r")\b", re.I)


def _bevat_negatieve_lading(*teksten) -> bool:
    for t in teksten:
        if t and _SMAAD_PATROON.search(t):
            return True
    return False


def _raakt_persoon(conn, entity_id=None, relation_id=None, betreft=None) -> bool:
    """Raakt dit doel een genoemd natuurlijk persoon? entity_id → type='persoon';
    relation_id → bron- of doel-entiteit is 'persoon'; betreft (vrije tekst, leads) →
    matcht op de naam van een 'persoon'-entiteit."""
    if entity_id:
        r = conn.execute("SELECT type FROM entities WHERE id = ?", (entity_id,)).fetchone()
        if r and r["type"] == "persoon":
            return True
    if relation_id:
        n = conn.execute("""
            SELECT COUNT(*) FROM relations r
            JOIN entities e ON e.id IN (r.source_id, r.target_id)
            WHERE r.id = ? AND e.type = 'persoon'""", (relation_id,)).fetchone()[0]
        if n:
            return True
    if betreft:
        naald = betreft.strip().lower()
        if naald:
            for e in conn.execute("SELECT name FROM entities WHERE type = 'persoon'"):
                naam = (e["name"] or "").strip().lower()
                if naam and (naam in naald or naald in naam):
                    return True
    return False


def _negatieve_persoonsclaim(conn, *, entity_id=None, relation_id=None, betreft=None,
                             claim="", reasoning="") -> bool:
    """D2.3-heuristiek: het doel raakt een natuurlijk persoon ÉN de tekst draagt
    negatief-feitelijke lading. Organisaties (type ≠ 'persoon') vallen er bewust buiten."""
    return (_bevat_negatieve_lading(claim, reasoning)
            and _raakt_persoon(conn, entity_id=entity_id, relation_id=relation_id,
                               betreft=betreft))


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
    # Politiek positie-signaal (kleurmeter): hoort bij een ENTITEIT (persoon/org). Een
    # signaal codeert ALLEEN een RICHTING (pool) — GEEN zelf-getypt getal; de magnitude
    # wordt afgeleid (politiek.py: Σ(gewicht·richting)/(Σgewicht+K)). Uitzondering: een
    # externe meting (CHES) mag '<as>:meting:<-1..1>' dragen — dat getal komt uit een
    # dataset, niet uit een mens. Bron is verplicht (gated, zie onder).
    if prop == "politieke_positie":
        if not entity_id:
            return jsonify({"error": "property 'politieke_positie' hoort bij een entiteit "
                                     "(entity_id)"}), 400
        as_, _, rest = str(prop_value or "").partition(":")
        ok = False
        if as_ in politiek.ASSEN:
            if rest in politiek.POOL_TEKEN.get(as_, {}):
                ok = True                                       # richting-pool
            elif rest.startswith("meting:"):
                try:
                    mv = float(rest.split(":", 1)[1]); ok = -1.0 <= mv <= 1.0
                except ValueError:
                    ok = False
        if not ok:
            return jsonify({"error": "property_value voor 'politieke_positie' codeert een "
                                     "RICHTING, geen getal: '<as>:<pool>' met as ∈ {economisch, "
                                     "cultureel, establishment} en pool ∈ {links|rechts, "
                                     "progressief|conservatief, anti-establishment|establishment}. "
                                     "Een externe meting (CHES) mag '<as>:meting:<-1..1>'. "
                                     "De magnitude wordt afgeleid, niet zelf gezet."}), 400
    # Inkomensaandeel (pie): welk deel van de inkomsten van de TARGET-outlet loopt via
    # deze financier-edge? Hoort dus bij een RELATIE; property_value codeert '<pct>:<jaar>'
    # (pct 0-100, jaar optioneel). Telt niet in de zekerheidsbalans (ASPECT_PROPERTIES),
    # maar is WÉL gesourcet (gated, zie onder) — het getal komt uit een jaarrekening, niet
    # uit een mens. Voedt scoring.compute_income_composition (residu = 100 − Σ edges).
    if prop == "inkomensaandeel":
        if not relation_id:
            return jsonify({"error": "property 'inkomensaandeel' hoort bij een financier-"
                                     "relatie (relation_id) — welk deel van de inkomsten "
                                     "van de outlet loopt hierlangs?"}), 400
        if scoring.parse_inkomensaandeel(prop_value)[0] is None:
            return jsonify({"error": "property_value voor 'inkomensaandeel' is "
                                     "'<percentage 0-100>:<jaar>' (jaar optioneel), bijv. "
                                     "'56:2024'. De magnitude komt uit de bron, niet vrij "
                                     "gekozen."}), 400
    # Machtsvalentie (tegenmacht als gerichte edge-valentie): hoort bij een RELATIE of
    # MECHANISME (een edge). property_value: 'filter:<filter>' (verantwoording — tegen
    # welke concentratie) of 'as:<as>:<opent|sluit>' (contra-hegemonie — opent/sluit de
    # consensus op die as, Hallin). Aspect: telt niet in de zekerheidsbalans en vereist
    # geen bron (interpretatie/structuur, geen extern bewijs — zoals 'filter'/'mechanism').
    if prop == "machtsvalentie":
        if not (relation_id or mechanism_id):
            return jsonify({"error": "property 'machtsvalentie' hoort bij een relatie of "
                                     "mechanisme (relation_id of mechanism_id) — het is de "
                                     "valentie van een edge, geen actor-kleur"}), 400
        if tegenmacht.parse_machtsvalentie(prop_value) is None:
            return jsonify({"error": "property_value voor 'machtsvalentie' is "
                                     "'filter:<" + "|".join(tegenmacht.FILTER_DOELEN) + ">' "
                                     "(verantwoording) of 'as:<economisch|cultureel|"
                                     "establishment>:<opent|sluit>' (contra-hegemonie)"}), 400
    # Doelgroepklasse (welstandsmeter): welke marketing-/welstandsklasse targt een OUTLET.
    # Hoort bij een ENTITEIT (entity_id). Een signaal codeert een KLASSE (A/B1/B2/C/D) op de
    # as `welstand`, of een externe bereikmeting ('welstand:meting:<-1..1>'); de magnitude/
    # positie wordt AFGELEID (doelgroep.py), niet zelf gekozen. Bron verplicht (zie evidentieel).
    if prop == "doelgroepklasse":
        if not entity_id:
            return jsonify({"error": "property 'doelgroepklasse' hoort bij een entiteit "
                                     "(entity_id) — welke klasse targt deze outlet?"}), 400
        as_, _, rest = str(prop_value or "").partition(":")
        ok = False
        if as_ == doelgroep.AS:
            if rest in doelgroep.KLASSEN:
                ok = True
            elif rest.startswith("meting:"):
                try:
                    mv = float(rest.split(":", 1)[1]); ok = -1.0 <= mv <= 1.0
                except ValueError:
                    ok = False
        if not ok:
            return jsonify({"error": "property_value voor 'doelgroepklasse' is "
                                     "'welstand:<klasse>' met klasse ∈ {A, B1, B2, C, D} "
                                     "(hoog→laag), of 'welstand:meting:<-1..1>' (NOM/NMO-"
                                     "bereikindex). De magnitude wordt afgeleid, niet zelf gezet."}), 400
    # Publieksbereik-signaal (bereikmeter): hoort bij een ENTITEIT. Eén signaal = één
    # cijfer uit één bron: '<maat>:<aantal>:<jaar>' (bv. 'kijkers:650000:2024'). Het jaar
    # is verplicht — de tijdreeks voedt de tijdlijn-gekoppelde node-grootte in de viz.
    # Bron verplicht (zie evidentieel); telt in niets mee (ASPECT_PROPERTIES).
    if prop == "bereik":
        if not entity_id:
            return jsonify({"error": "property 'bereik' hoort bij een entiteit "
                                     "(entity_id) — welk publiek bereikt dit medium?"}), 400
        try:
            bereik._parse(prop_value)
        except (ValueError, AttributeError) as e:
            return jsonify({"error": "property_value voor 'bereik' is "
                                     "'<maat>:<aantal>:<jaar>' met maat ∈ {"
                                     + ", ".join(bereik.MATEN) + "}, aantal een positief "
                                     "geheel getal en jaar 4 cijfers (het jaar waarop het "
                                     f"cijfer slaat). Probleem: {e}"}), 400
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
    # Een ONDERGRAVING ('logica klopt niet' — een contradicting-reply) moet ALTIJD
    # zeggen waarom de logica/het argument niet deugt. Een kaal 'oneens' is precies de
    # goedkope downvote die we niet willen: de reden is wat de auteur kan verbeteren én
    # wat de bezwaarmaker straks zelf herbeoordeelt (resolutielus). Een objection_type
    # (drogreden-label) is daar bovenop optioneel.
    is_ondergraving = parent_id is not None and stance == "contradicting"
    if is_ondergraving and not reasoning:
        return jsonify({"error": "Een ondergraving (‘logica klopt niet’) vereist een "
                                 "onderbouwing: benoem in 'reasoning' wat er niet klopt "
                                 "aan de redenering of het argument"}), 400
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
        fout = _methode_fout(c.get("methode"), c.get("quote"))
        if fout:
            return jsonify({"error": fout}), 400

    # Voorstel-workflow (M2.2): elk argument landt als 'voorgesteld' en telt in niets
    # mee tot een reviewer merget. De citatiepoort (M0.3) wordt op het merge-moment
    # toegepast (→ 'bronvermelding_nodig' of 'ongecontroleerd').
    status = "voorgesteld"

    conn = get_db()
    if parent_id is not None and not conn.execute(
            "SELECT 1 FROM arguments WHERE id = ?", (parent_id,)).fetchone():
        conn.close()
        return jsonify({"error": f"Parent-argument {parent_id} bestaat niet"}), 400
    # Backstop tegen dubbel agent-werk: een agent reageert niet twee keer op hetzelfde
    # argument. (Mensen mogen dat wel — een echte discussie kan meerdere reacties dragen.)
    if parent_id is not None and g.user.get("kind") == "agent":
        al = conn.execute(
            "SELECT id FROM arguments WHERE parent_argument_id = ? AND contributed_by = ? "
            "ORDER BY id LIMIT 1", (parent_id, contributed_by)).fetchone()
        if al:
            conn.close()
            return jsonify({"error": f"Je reageerde al op argument #{parent_id} (jouw reactie "
                                     f"#{al['id']}); een agent reageert niet twee keer op "
                                     "hetzelfde argument.",
                            "bestaande_reactie": al["id"]}), 409
    for c in citaties:
        if not conn.execute("SELECT 1 FROM sources WHERE id = ?", (c["source_id"],)).fetchone():
            conn.close()
            return jsonify({"error": f"Bron {c['source_id']} bestaat niet"}), 400

    # Bronplicht (HARDE poort): een EVIDENTIEEL ondersteunend/weerleggend ROOT-argument
    # vereist bij creatie minstens één ECHTE bron — een citaat met quote, óf een bron met
    # vindplaats (source_locations). Een kale titel-stub telt niet. Vroeger was dit een zachte
    # poort bij merge (→ bronvermelding_nodig, score-straf); nu blokkeert de API onbronnde
    # claims zodat ze het model niet eens binnenkomen.
    #   Wél bron nodig: gewoon bewijs (geen property), invloed-bewijs (property='influence'),
    #   politiek positie-signaal (property='politieke_positie') én inkomensaandeel — een
    #   feitelijke magnitude uit een jaarrekening moet je staven.
    #   Vrijgesteld (interpretatie/structuur, geen extern bewijs): classificatie-aspecten
    #   (property='filter'/'mechanism'), compositie- en padclaims ('compositie'/'indirecte_invloed_op'),
    #   contextual-roots, en replies/ondergravingen ('logica klopt niet' — parent_id gezet).
    evidentieel = prop in (None, "influence", "politieke_positie", "inkomensaandeel",
                           "doelgroepklasse", "bereik")
    heeft_echte_bron = any(
        bool((c.get("quote") or "").strip()) or conn.execute(
            "SELECT 1 FROM source_locations WHERE source_id = ?", (c["source_id"],)).fetchone()
        for c in citaties)
    if (parent_id is None and stance in ("supporting", "contradicting") and evidentieel
            and not heeft_echte_bron):
        conn.close()
        return jsonify({"error": "Bron verplicht: een ondersteunend of weerleggend "
                                 "root-argument vereist minstens één echte bron — een citaat "
                                 "met quote, óf een bron met vindplaats (locator). Geef die mee "
                                 "in 'citations' (source_id + quote, of een bron met url/doi/…)."}), 400

    # Classificatie-aspect 'mechanism': de voorgestelde mechanisme-ID moet bestaan.
    if prop == "mechanism" and not conn.execute(
            "SELECT 1 FROM mechanisms WHERE id = ?", (int(prop_value),)).fetchone():
        conn.close()
        return jsonify({"error": f"Mechanisme {prop_value} bestaat niet"}), 400

    # Duplicaatdetectie (M2.4 + A6): vergelijk de claim met bestaande root-argumenten op
    # hetzelfde doel. Twee goedkope, stdlib-lagen (bewust geen externe embeddings in het
    # synchrone POST-pad):
    #   - difflib.SequenceMatcher, drempel 0,85 (gratis Laag-0-voorcheck, bestaand gedrag);
    #   - dedup.gelijkenis (A6, token-cosine/Jaccard over shingles), drempel 0,80 — vangt
    #     herformuleringen die difflib mist (synoniemarme paraphrase, herordening).
    # Een kandidaat wordt gevlagd als max(difflib, dedup) ≥ zijn drempel. De 409 geeft de
    # gelijkenis-score per bron terug; negeer_duplicaten=true blijft de bewuste override.
    DIFFLIB_DREMPEL = 0.85
    DEDUP_DREMPEL = 0.80
    if parent_id is None and not data.get("negeer_duplicaten"):
        doel_map = {"relation_id": relation_id, "entity_id": entity_id, "role_id": role_id,
                    "mechanism_id": mechanism_id, "emergent_effect_id": emergent_effect_id}
        doelkolom = next(k for k, v in doel_map.items() if v)
        kandidaten = []
        for rij in conn.execute(
                f"SELECT id, claim, status FROM arguments WHERE {doelkolom} = ? "
                "AND parent_argument_id IS NULL", (doel_map[doelkolom],)):
            ander = rij["claim"] or ""
            difflib_ratio = difflib.SequenceMatcher(
                None, claim.lower(), ander.lower()).ratio()
            dedup_ratio = dedup.gelijkenis(claim, ander) if dedup is not None else 0.0
            if difflib_ratio >= DIFFLIB_DREMPEL or dedup_ratio >= DEDUP_DREMPEL:
                kandidaten.append({"id": rij["id"], "claim": rij["claim"],
                                   "status": rij["status"],
                                   "gelijkenis": round(max(difflib_ratio, dedup_ratio), 2),
                                   "difflib": round(difflib_ratio, 2),
                                   "dedup": round(dedup_ratio, 2)})
        if kandidaten:
            conn.close()
            return jsonify({"error": "Mogelijke duplicaat-claim op dit doel; dien opnieuw "
                                     "in met negeer_duplicaten=true als dit echt een "
                                     "nieuwe claim is",
                            "duplicaat_kandidaten": kandidaten}), 409

    try:
        # Een ondergraving start de resolutielus in 'open' (dempt); andere argumenten
        # dragen geen resolutie-stand.
        bezwaar_resolutie = "open" if is_ondergraving else None
        cur = conn.execute("""
            INSERT INTO arguments
                (relation_id, entity_id, role_id, mechanism_id, emergent_effect_id,
                 parent_argument_id, property, property_value,
                 stance, claim, reasoning, weight, status, objection_type, contributed_by,
                 bezwaar_resolutie)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (relation_id, entity_id, role_id, mechanism_id, emergent_effect_id,
              parent_id, prop, prop_value,
              stance, claim, reasoning, weight, status, objection_type, contributed_by,
              bezwaar_resolutie))
        arg_id = cur.lastrowid

        for c in citaties:
            conn.execute("""
                INSERT INTO citations (argument_id, source_id, quote, page, section, context, methode)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (arg_id, c["source_id"], c.get("quote"), c.get("page"),
                  c.get("section"), c.get("context"), c.get("methode")))

        # Log in edit_log
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('arguments', ?, 'created', ?, ?, ?)
        """, (arg_id, contributed_by,
              json.dumps({"claim": claim, "stance": stance, "status": status,
                          "citaties": len(citaties)}),
              f"Nieuw argument: {stance}"))

        # Smaad-firewall (D2.3, Laag 3): een nieuw ROOT-argument met een negatieve
        # feitelijke claim over een genoemd natuurlijk persoon krijgt smaad_hold = 1.
        # Dat houdt het uit ELKE publieke render (viz_data.py + paginas.py) tot alleen
        # de eigenaar (maintainer, mens) het vrijgeeft — hoe schoon de bron ook is.
        # Alleen bij creatie (nieuw voorgesteld argument); bestaande args blijven 0.
        if parent_id is None and _negatieve_persoonsclaim(
                conn, entity_id=entity_id, relation_id=relation_id,
                claim=claim, reasoning=reasoning or ""):
            conn.execute("UPDATE arguments SET smaad_hold = 1 WHERE id = ?", (arg_id,))
            conn.execute("""
                INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
                VALUES ('arguments', ?, 'updated', ?, ?, ?)
            """, (arg_id, contributed_by, json.dumps({"smaad_hold": 1}),
                  "smaad-firewall (D2.3): negatieve feitelijke claim over een natuurlijk "
                  "persoon — geblokkeerd voor publieke render tot eigenaars-akkoord"))

        # Admin hoeft geen review (juli 2026): een argument van een maintainer merget
        # meteen — dezelfde citatiepoort als merge_argument (M0.3, zachte variant),
        # gemarkeerd als self-merge (n=1, herauditeerbaar via edit_log). Een admin-
        # ondergraving ('argument klopt niet') wordt zo direct actief en nult zijn
        # parent volledig (admin-veto, scoring.py) tot ze is opgelost of weerlegd.
        if g.user["role"] == "maintainer":
            status = ("bronvermelding_nodig"
                      if parent_id is None and stance in ("supporting", "contradicting")
                      and not heeft_echte_bron else "ongecontroleerd")
            conn.execute("UPDATE arguments SET status = ?, merged_by = ?, self_merged = 1 "
                         "WHERE id = ?", (status, contributed_by, arg_id))
            conn.execute("""
                INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
                VALUES ('arguments', ?, 'merged', ?, ?, ?, ?)
            """, (arg_id, contributed_by,
                  json.dumps({"status": "voorgesteld"}),
                  json.dumps({"status": status}),
                  "auto-merge: maintainer (admin hoeft geen review)"))

        conn.commit()
        result = dict(conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone())
        conn.close()
        return jsonify(result), 201

    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400


def _kopieer_citaties(conn, van_arg_id, naar_arg_id):
    """Citaties dupliceren naar een nieuw (revisie-)argument."""
    for c in conn.execute("SELECT * FROM citations WHERE argument_id = ?",
                          (van_arg_id,)).fetchall():
        conn.execute("""INSERT INTO citations
                        (argument_id, source_id, quote, page, section, context, methode)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (naar_arg_id, c["source_id"], c["quote"], c["page"],
                      c["section"], c["context"], c["methode"]))


def _zet_citaties(conn, arg_id, citaties):
    """Vervang de citaties van een argument door de opgegeven lijst (validatie:
    elke citatie heeft een bestaande source_id). Retourneert een foutstring of None."""
    for c in citaties:
        if not isinstance(c, dict) or not c.get("source_id"):
            return "Elke citatie vereist een source_id"
        if not conn.execute("SELECT 1 FROM sources WHERE id = ?", (c["source_id"],)).fetchone():
            return f"Bron {c['source_id']} bestaat niet"
        fout = _methode_fout(c.get("methode"), c.get("quote"))
        if fout:
            return fout
    conn.execute("DELETE FROM citations WHERE argument_id = ?", (arg_id,))
    for c in citaties:
        conn.execute("""INSERT INTO citations
                        (argument_id, source_id, quote, page, section, context, methode)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                     (arg_id, c["source_id"], c.get("quote"), c.get("page"),
                      c.get("section"), c.get("context"), c.get("methode")))
    return None


@app.route("/api/arguments/<int:arg_id>", methods=["PATCH"])
@require_user()
def edit_argument(arg_id):
    """Een nog-VOORGESTELD argument bijschaven (Fase C). Alleen de auteur, en alleen
    zolang het 'voorgesteld' is — dan telt het nog nergens in mee, dus in-place
    bewerken breekt geen provenance. Een al gemerged argument verbeter je via een
    revisie (POST .../revisie), die het oude vervangt en opnieuw door de poort moet.

    Bewerkbaar: claim, reasoning, stance, property_value, objection_type, citations.
    Het doel/de parent en het property-TYPE liggen vast (kies anders een nieuw argument).
    """
    data = request.json or {}
    conn = get_db()
    arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if arg["contributed_by"] != g.user["username"] and not (
            heeft_rol(conn, g.user, "maintainer") and _is_agent(conn, arg["contributed_by"])):
        conn.close()
        return jsonify({"error": "Alleen de auteur bewerkt een eigen voorstel "
                                 "(een maintainer mag wél agent-werk bijschaven; een mens "
                                 "herziet zijn eigen bijdrage zelf)"}), 403
    if arg["status"] != "voorgesteld":
        conn.close()
        return jsonify({"error": "Alleen een 'voorgesteld' argument is bewerkbaar; "
                                 "verbeter een gemerged argument via "
                                 f"POST /api/arguments/{arg_id}/revisie"}), 400

    velden, waarden = [], []
    if "claim" in data:
        claim = (data.get("claim") or "").strip()
        if not claim:
            conn.close()
            return jsonify({"error": "Claim mag niet leeg zijn"}), 400
        velden.append("claim = ?"); waarden.append(claim)
    if "reasoning" in data:
        velden.append("reasoning = ?"); waarden.append((data.get("reasoning") or "").strip() or None)
    if "stance" in data:
        if data["stance"] not in ("supporting", "contradicting", "contextual"):
            conn.close()
            return jsonify({"error": "Ongeldige stance"}), 400
        velden.append("stance = ?"); waarden.append(data["stance"])
    if "property_value" in data and arg["parent_argument_id"] is None:
        velden.append("property_value = ?"); waarden.append((data.get("property_value") or "").strip() or None)
    if "objection_type" in data and arg["parent_argument_id"] is not None:
        velden.append("objection_type = ?"); waarden.append(data.get("objection_type") or None)

    if velden:
        conn.execute(f"UPDATE arguments SET {', '.join(velden)} WHERE id = ?", waarden + [arg_id])
    if isinstance(data.get("citations"), list):
        fout = _zet_citaties(conn, arg_id, data["citations"])
        if fout:
            conn.rollback(); conn.close()
            return jsonify({"error": fout}), 400
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('arguments', ?, 'updated', ?, ?, ?)
    """, (arg_id, g.user["username"], json.dumps({"bewerkt": [v.split(" =")[0] for v in velden]}),
          "auteur bewerkt eigen voorstel"))
    conn.commit()
    result = dict(conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone())
    conn.close()
    return jsonify(result)


@app.route("/api/arguments/<int:arg_id>/revisie", methods=["POST"])
@require_user()
def revise_argument(arg_id):
    """Een verbeterde versie van een al gemerged argument indienen (Fase C). De revisie
    landt als een nieuw 'voorgesteld' argument met reviseert_id = het oude; mergt een
    reviewer haar, dan supersedet ze het oude (→ 'verouderd' + vervangen). Zo blijft de
    keten herleidbaar en beslist een mens ('ik stel voor, jij beslist'). Iedereen mag
    een revisie voorstellen, ook van andermans argument.

    Erft doel/parent/property-type/stance van het origineel; body kan claim, reasoning,
    stance, property_value en citations overschrijven (anders citaties gekopieerd).
    """
    data = request.json or {}
    conn = get_db()
    oud = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not oud:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if oud["status"] == "voorgesteld":
        conn.close()
        return jsonify({"error": "Dit argument is zelf nog een voorstel; bewerk het direct "
                                 f"(PATCH /api/arguments/{arg_id}) i.p.v. te reviseren"}), 400
    if oud["vervangen"]:
        conn.close()
        return jsonify({"error": "Dit argument is al vervangen; reviseer de opvolger"}), 400

    claim = (data.get("claim") or oud["claim"] or "").strip()
    if not claim:
        conn.close()
        return jsonify({"error": "Claim is verplicht"}), 400
    stance = data.get("stance") or oud["stance"]
    if stance not in ("supporting", "contradicting", "contextual"):
        conn.close()
        return jsonify({"error": "Ongeldige stance"}), 400
    reasoning = ((data.get("reasoning") if "reasoning" in data else oud["reasoning"]) or "").strip() or None
    prop_value = (data.get("property_value") if "property_value" in data
                  else oud["property_value"])

    cur = conn.execute("""
        INSERT INTO arguments
            (relation_id, entity_id, role_id, mechanism_id, emergent_effect_id,
             parent_argument_id, property, property_value, stance, claim, reasoning,
             objection_type, status, contributed_by, reviseert_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'voorgesteld', ?, ?)
    """, (oud["relation_id"], oud["entity_id"], oud["role_id"], oud["mechanism_id"],
          oud["emergent_effect_id"], oud["parent_argument_id"], oud["property"],
          prop_value, stance, claim, reasoning, oud["objection_type"],
          g.user["username"], arg_id))
    nieuw_id = cur.lastrowid

    if isinstance(data.get("citations"), list):
        fout = _zet_citaties(conn, nieuw_id, data["citations"])
        if fout:
            conn.rollback(); conn.close()
            return jsonify({"error": fout}), 400
    else:
        _kopieer_citaties(conn, arg_id, nieuw_id)

    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('arguments', ?, 'created', ?, ?, ?)
    """, (nieuw_id, g.user["username"], json.dumps({"reviseert": arg_id, "status": "voorgesteld"}),
          f"revisie van argument #{arg_id}"))

    # Admin hoeft geen review (juli 2026): een maintainer-revisie merget meteen en
    # supersedet het origineel — maar alleen binnen de agent-scope (eigen werk,
    # agent-werk of auteurloos seed-werk). Andermans MENSWERK vervang je niet
    # eigenmachtig: die revisie blijft een gewoon voorstel voor een tweede paar ogen.
    if g.user["role"] == "maintainer" and (
            oud["contributed_by"] is None
            or oud["contributed_by"] == g.user["username"]
            or _is_agent(conn, oud["contributed_by"])):
        n_echt = conn.execute("""
            SELECT COUNT(*) FROM citations c WHERE c.argument_id = ? AND (
                (c.quote IS NOT NULL AND TRIM(c.quote) <> '')
                OR EXISTS (SELECT 1 FROM source_locations sl WHERE sl.source_id = c.source_id))
            """, (nieuw_id,)).fetchone()[0]
        nieuwe_status = ("bronvermelding_nodig"
                         if oud["parent_argument_id"] is None
                         and stance in ("supporting", "contradicting") and not n_echt
                         else "ongecontroleerd")
        conn.execute("UPDATE arguments SET status = ?, merged_by = ?, self_merged = 1 "
                     "WHERE id = ?", (nieuwe_status, g.user["username"], nieuw_id))
        conn.execute("UPDATE arguments SET status = 'verouderd', vervangen = 1 WHERE id = ?",
                     (arg_id,))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
            VALUES ('arguments', ?, 'merged', ?, ?, ?, ?)
        """, (nieuw_id, g.user["username"],
              json.dumps({"status": "voorgesteld"}), json.dumps({"status": nieuwe_status}),
              "auto-merge: maintainer (admin hoeft geen review)"))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
            VALUES ('arguments', ?, 'updated', ?, ?, ?, ?)
        """, (arg_id, g.user["username"], json.dumps({"vervangen": False}),
              json.dumps({"vervangen": True, "status": "verouderd"}),
              f"vervangen door revisie #{nieuw_id} (auto-merge maintainer)"))

    conn.commit()
    result = dict(conn.execute("SELECT * FROM arguments WHERE id = ?", (nieuw_id,)).fetchone())
    conn.close()
    return jsonify(result), 201


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
    # Afwijzen én terug-naar-herkeuring (betwist) vergen een motivatie — zonder
    # feedback kan de auteur niet verbeteren (Fase B; symmetrisch met RfC-/praktijk-
    # afwijzingen). De motivatie landt in edit_log.reason en is zichtbaar in de werkbank.
    motivatie = (data.get("motivatie") or data.get("reason") or "").strip() or None
    if new_status in ("verworpen", "betwist") and not motivatie:
        woord = "afwijzing" if new_status == "verworpen" else "herkeuring"
        return jsonify({"error": f"Een {woord} vergt een motivatie "
                                 "(waarom — bv. fout, formulering of drogreden?)"}), 400

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
          json.dumps({"status": new_status}), motivatie))

    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "status": new_status})


@app.route("/api/arguments/<int:arg_id>/smaad_vrijgeven", methods=["POST"])
@require_user("maintainer")
def smaad_vrijgeven(arg_id):
    """Smaad-firewall opheffen (D2.3): alleen de eigenaar (maintainer, mens) heft de
    smaad_hold-vlag op een argument op → het argument mag weer publiek renderen. Een
    agent/reviewer kan dit niet (403 via de maintainer-poort). Menselijk eindoordeel op
    de hoogste-inzet-categorie; geaudit in edit_log."""
    conn = get_db()
    arg = conn.execute("SELECT id, smaad_hold FROM arguments WHERE id = ?",
                       (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if not arg["smaad_hold"]:
        conn.close()
        return jsonify({"id": arg_id, "smaad_hold": 0,
                        "opmerking": "Argument stond niet op smaad_hold"}), 200
    conn.execute("UPDATE arguments SET smaad_hold = 0 WHERE id = ?", (arg_id,))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('arguments', ?, 'updated', ?, ?, ?, ?)
    """, (arg_id, g.user["username"], json.dumps({"smaad_hold": 1}),
          json.dumps({"smaad_hold": 0}),
          "smaad-firewall vrijgegeven door eigenaar (maintainer)"))
    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "smaad_hold": 0}), 200


@app.route("/api/arguments/<int:arg_id>/bezwaar", methods=["PATCH"])
@require_user()
def update_bezwaar_resolutie(arg_id):
    """Resolutielus op een ONDERGRAVING (contradicting reply, het 'logica klopt niet'-
    verdict). Stappen:
      - 'herzien'  : de auteur van het aangevochten argument (de parent) — of een
                     reviewer — zegt 'ik heb het aangepast, herbeoordeel'.
      - 'opgelost' : het bezwaar is weg → de demping vervalt (scoring telt 'opgelost'
                     niet als aanval). Alleen de bezwaarmaker zelf; OF, NÁ 'herzien',
                     een reviewer (overrule), zodat een afwezige bezwaarmaker het
                     argument niet eeuwig bevriest.
      - 'blijft'   : de bezwaarmaker heeft herbeoordeeld en handhaaft; demping blijft.
    Open/herzien/blijft dempen; alleen 'opgelost' niet.
    """
    data = request.json or {}
    actie = data.get("actie") or data.get("resolutie")
    if actie not in ("herzien", "opgelost", "blijft"):
        return jsonify({"error": "actie moet 'herzien', 'opgelost' of 'blijft' zijn"}), 400

    conn = get_db()
    arg = conn.execute(
        "SELECT id, parent_argument_id, stance, status, contributed_by, bezwaar_resolutie "
        "FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if arg["parent_argument_id"] is None or arg["stance"] != "contradicting":
        conn.close()
        return jsonify({"error": "De resolutielus geldt alleen voor een ondergraving "
                                 "(een tegen-reactie op een ander argument)"}), 400
    if arg["status"] in ("voorgesteld", "verworpen"):
        conn.close()
        return jsonify({"error": "Dit bezwaar telt nog niet mee (status "
                                 f"'{arg['status']}'); de resolutielus start pas na merge"}), 400

    parent = conn.execute("SELECT contributed_by FROM arguments WHERE id = ?",
                          (arg["parent_argument_id"],)).fetchone()
    auteur = parent["contributed_by"] if parent else None   # auteur van het aangevochten argument
    bezwaarmaker = arg["contributed_by"]                    # wie het bezwaar plaatste
    huidig = arg["bezwaar_resolutie"] or "open"
    ik = g.user["username"]
    is_reviewer = heeft_rol(conn, g.user, "reviewer", _filters_van_argument(conn, arg_id))

    if actie == "herzien":
        if huidig == "opgelost":
            conn.close()
            return jsonify({"error": "Dit bezwaar is al opgelost"}), 400
        if ik != auteur and not is_reviewer:
            conn.close()
            return jsonify({"error": "Alleen de auteur van het aangevochten argument "
                                     "(of een reviewer) kan het op 'herzien' zetten"}), 403
    elif actie == "blijft":
        if ik != bezwaarmaker:
            conn.close()
            return jsonify({"error": "Alleen de bezwaarmaker kan het bezwaar handhaven "
                                     "('blijft staan')"}), 403
    elif actie == "opgelost":
        # Bezwaarmaker mag altijd sluiten; reviewer mag overrulen, maar pas ná 'herzien'
        # (afwezige bezwaarmaker → geen eeuwige bevriezing) en niet op eigen bezwaar.
        if ik == bezwaarmaker:
            pass
        elif is_reviewer and huidig == "herzien":
            pass
        elif is_reviewer:
            conn.close()
            return jsonify({"error": "Een reviewer kan een bezwaar pas overrulen nadat "
                                     "de auteur het op 'herzien' heeft gezet"}), 403
        else:
            conn.close()
            return jsonify({"error": "Alleen de bezwaarmaker sluit dit bezwaar; een "
                                     "reviewer kan overrulen ná 'herzien'"}), 403

    overrule = (actie == "opgelost" and ik != bezwaarmaker)
    conn.execute("UPDATE arguments SET bezwaar_resolutie = ? WHERE id = ?", (actie, arg_id))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('arguments', ?, 'updated', ?, ?, ?, ?)
    """, (arg_id, ik, json.dumps({"bezwaar_resolutie": huidig}),
          json.dumps({"bezwaar_resolutie": actie, "overrule": overrule}),
          (data.get("motivatie") or data.get("reason") or "").strip()
          or f"resolutielus: {huidig} → {actie}"))
    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "bezwaar_resolutie": actie, "overrule": overrule})


def _merge_core(conn, arg, merged_by, *, reason=None):
    """Gedeelde merge-kern (M2.2): de statusberekening (citatiepoort), de UPDATE +
    'merged'-edit_log-rij, en de revisie-supersede. Hergebruikt door merge_argument
    (menselijke reviewer) én auto_merge_argument (A7-immuunpoort). Commit blijft bij
    de caller. ``reason`` overschrijft de edit_log-reden (auto-merge zet er
    'auto-merge (immuunpoort)'); None → de bestaande zelf-merge-label-logica.
    Retourneert (nieuwe_status, self_merged, vervangt)."""
    arg_id = arg["id"]
    # Citatiepoort (M0.3), zachte variant: een supporting/contradicting ROOT zonder
    # ÉCHTE bron (citatie met quote óf vindplaats — een kale titel-stub telt niet)
    # landt op 'bronvermelding_nodig' (statusfactor 0,40 i.p.v. 0,50: score-straf,
    # geen block). Zo blijven ware-maar-nog-ongesourcete claims behouden — het
    # gewicht van het bewijs beslist, niet een harde poort.
    n_echt = conn.execute("""
        SELECT COUNT(*) FROM citations c WHERE c.argument_id = ? AND (
            (c.quote IS NOT NULL AND TRIM(c.quote) <> '')
            OR EXISTS (SELECT 1 FROM source_locations sl WHERE sl.source_id = c.source_id))
        """, (arg_id,)).fetchone()[0]
    if (arg["parent_argument_id"] is None
            and arg["stance"] in ("supporting", "contradicting") and not n_echt):
        nieuwe_status = "bronvermelding_nodig"
    else:
        nieuwe_status = "ongecontroleerd"
    self_merged = arg["contributed_by"] == merged_by
    edit_reason = reason if reason is not None else ("zelf-merge (n=1)" if self_merged else None)

    conn.execute("UPDATE arguments SET status = ?, merged_by = ?, self_merged = ? WHERE id = ?",
                 (nieuwe_status, merged_by, self_merged, arg_id))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('arguments', ?, 'merged', ?, ?, ?, ?)
    """, (arg_id, merged_by,
          json.dumps({"status": "voorgesteld"}),
          json.dumps({"status": nieuwe_status}),
          edit_reason))

    # Revisie (Fase C): mergt deze rij een ouder argument weg? Dan supersedet ze het —
    # het oude gaat op 'verouderd' + vervangen = 1 (scoring/influence/viz slaan het over),
    # de opvolging blijft herleidbaar via reviseert_id + edit_log.
    vervangt = arg["reviseert_id"]
    if vervangt is not None:
        conn.execute("UPDATE arguments SET status = 'verouderd', vervangen = 1 WHERE id = ?",
                     (vervangt,))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
            VALUES ('arguments', ?, 'updated', ?, ?, ?, ?)
        """, (vervangt, merged_by, json.dumps({"vervangen": False}),
              json.dumps({"vervangen": True, "status": "verouderd"}),
              f"vervangen door revisie #{arg_id}"))
    return nieuwe_status, self_merged, vervangt


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

    nieuwe_status, self_merged, vervangt = _merge_core(conn, arg, g.user["username"])
    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "status": nieuwe_status,
                    "merged_by": g.user["username"], "self_merged": self_merged,
                    "vervangt": vervangt})


# ── Immuunsysteem (A1/A2): her-verificatie + verplichte tegenspraak ──
# Procesmetadata in immuun_oordelen — GEEN boomnode, GEEN τ/σ, telt NERGENS in de score.
# Beide poorten weigeren zelf-oordeel (door == contributed_by): een reproductietest tegen
# de echte bron (A1) en een gedecorreleerde aanklager (A2) zijn precies de twee dingen die
# met agents wél schalen, maar alleen als een ánder account ze uitvoert.

HERVERIFICATIE_VERDICTS = ("klopt", "twijfel", "klopt-niet")
TEGENSPRAAK_VERDICTS = ("aangevallen", "overleefd", "onbeslist")


def _normaliseer_tekst(s: str) -> str:
    """Lowercase + witruimte-collapse, voor de goedkope verbatim-voorcheck (A1)."""
    return " ".join((s or "").lower().split())


def _schrijf_immuun_oordeel(conn, arg_id, fase, verdict, *, verbatim_span=None,
                            bron_id=None, detail=None):
    """Schrijf een immuun_oordeel-rij + edit_log-regel onder de ingelogde gebruiker.
    Retourneert de nieuwe rij-id. UNIQUE(argument_id, fase, door) wordt door de caller
    afgevangen (sqlite3.IntegrityError → 409)."""
    door = g.user["username"]
    model_familie = g.user.get("provenance")
    cur = conn.execute("""
        INSERT INTO immuun_oordelen
            (argument_id, fase, verdict, verbatim_span, bron_id, detail, door, model_familie)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (arg_id, fase, verdict, verbatim_span, bron_id, detail, door, model_familie))
    oid = cur.lastrowid
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('immuun_oordelen', ?, 'created', ?, ?, ?)
    """, (oid, door, json.dumps({"argument_id": arg_id, "fase": fase, "verdict": verdict}),
          f"immuun-oordeel ({fase}): {verdict}"))
    return oid


@app.route("/api/arguments/<int:arg_id>/herverificatie", methods=["POST"])
@require_user()
def herverificatie(arg_id):
    """A1 — onafhankelijke bron-herverificatie. Een ándere agent haalt de bron opnieuw op
    en checkt de quote verbatim + de citaat-dekking. Verdict klopt/twijfel/klopt-niet.
    403 bij zelf-verificatie. Telt nergens in de score — procesmetadata voor de auto-merge-
    poort (A7). Met ``"herzien": true`` herziet een account zijn EIGEN eerdere oordeel
    (nieuwe bron-poging, betere controle): de rij wordt bijgewerkt en gelogd, nooit een
    tweede stem (automatische beoordeling, 2026-10-06)."""
    data = request.json or {}
    verdict = data.get("verdict")
    if verdict not in HERVERIFICATIE_VERDICTS:
        return jsonify({"error": "verdict moet een van zijn: "
                                 + ", ".join(HERVERIFICATIE_VERDICTS)}), 400
    verbatim_span = (data.get("verbatim_span") or "").strip() or None
    bron_id = data.get("bron_id")
    detail = (data.get("detail") or "").strip() or None

    conn = get_db()
    arg = conn.execute("SELECT id, contributed_by FROM arguments WHERE id = ?",
                       (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if arg["contributed_by"] == g.user["username"]:
        conn.close()
        return jsonify({"error": "Zelf-verificatie is niet toegestaan: een andere agent moet "
                                 "de bron onafhankelijk her-verifiëren (A1)"}), 403

    # Goedkope mechanische voorcheck (A1): claim je verdict 'klopt' mét een verbatim_span,
    # dan moet die span (genormaliseerd) een citaat-quote van dit argument bevatten — zo niet,
    # forceer 'twijfel'. Dit is de gratis filter vóór de dure LLM-beoordeling.
    if verdict == "klopt" and verbatim_span:
        quotes = [q[0] for q in conn.execute(
            "SELECT quote FROM citations WHERE argument_id = ? AND quote IS NOT NULL AND TRIM(quote) <> ''",
            (arg_id,)).fetchall()]
        span_n = _normaliseer_tekst(verbatim_span)
        if quotes and not any(_normaliseer_tekst(q) in span_n or span_n in _normaliseer_tekst(q)
                              for q in quotes):
            verdict = "twijfel"
            detail = ("[auto] verbatim_span matcht geen enkele citaat-quote van dit argument; "
                      "verdict verlaagd naar 'twijfel'. " + (detail or "")).strip()

    if data.get("herzien") is True:
        oud = conn.execute("""SELECT id, verdict FROM immuun_oordelen WHERE argument_id = ?
                              AND fase = 'herverificatie' AND door = ?""",
                           (arg_id, g.user["username"])).fetchone()
        if oud is not None:
            conn.execute("""UPDATE immuun_oordelen SET verdict = ?, verbatim_span = ?,
                            bron_id = ?, detail = ?, created_at = CURRENT_TIMESTAMP
                            WHERE id = ?""", (verdict, verbatim_span, bron_id, detail, oud["id"]))
            conn.execute("""
                INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value,
                                      new_value, reason)
                VALUES ('immuun_oordelen', ?, 'updated', ?, ?, ?, ?)
            """, (oud["id"], g.user["username"], json.dumps({"verdict": oud["verdict"]}),
                  json.dumps({"argument_id": arg_id, "verdict": verdict}),
                  f"immuun-oordeel (herverificatie) herzien: {verdict}"))
            conn.commit()
            conn.close()
            return jsonify({"id": oud["id"], "argument_id": arg_id, "fase": "herverificatie",
                            "verdict": verdict, "detail": detail, "herzien": True}), 200
    try:
        oid = _schrijf_immuun_oordeel(conn, arg_id, "herverificatie", verdict,
                                      verbatim_span=verbatim_span, bron_id=bron_id, detail=detail)
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Je gaf al een herverificatie-oordeel op dit argument "
                                 "(stuur \"herzien\": true om het te herzien)"}), 409
    conn.close()
    return jsonify({"id": oid, "argument_id": arg_id, "fase": "herverificatie",
                    "verdict": verdict, "detail": detail}), 201


@app.route("/api/arguments/<int:arg_id>/tegenspraak", methods=["POST"])
@require_user()
def tegenspraak(arg_id):
    """A2 — verplichte tegenspraak. Een gedecorreleerde aanklager zoekt een tegenbron of valt
    de inferentie aan; vindt hij niets weerlegbaars, dan certificeert hij 'overleefd'. Zo blijft
    'ik zocht en vond niets' PROCESMETADATA (nooit een contextual-boomnode). Verdict
    aangevallen/overleefd/onbeslist. 403 bij zelf-certificering. Telt nergens in de score."""
    data = request.json or {}
    verdict = data.get("verdict")
    if verdict not in TEGENSPRAAK_VERDICTS:
        return jsonify({"error": "verdict moet een van zijn: "
                                 + ", ".join(TEGENSPRAAK_VERDICTS)}), 400
    detail = (data.get("detail") or "").strip() or None

    conn = get_db()
    arg = conn.execute("SELECT id, contributed_by FROM arguments WHERE id = ?",
                       (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if arg["contributed_by"] == g.user["username"]:
        conn.close()
        return jsonify({"error": "Zelf-certificering is niet toegestaan: een gedecorreleerde "
                                 "aanklager moet de claim aanvallen (A2)"}), 403

    try:
        oid = _schrijf_immuun_oordeel(conn, arg_id, "tegenspraak", verdict, detail=detail)
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Je gaf al een tegenspraak-certificaat op dit argument"}), 409
    conn.close()
    return jsonify({"id": oid, "argument_id": arg_id, "fase": "tegenspraak",
                    "verdict": verdict, "detail": detail}), 201


# ── Auto-merge-poort (A7): het immuunpoort-predikaat + endpoint ──
# Een root merget alleen automatisch als A1 ∧ A2 ∧ A6 ∧ citatiepoort ∧ jury-
# onafhankelijkheid allemaal waar zijn, én het geen theorie-/aspect-doel of een
# negatieve persoons-claim is. De C2-service (aparte lane) draait dit over de
# wachtrij; het endpoint checkt het predikaat ZELF (defense-in-depth) zodat een bug
# in de loop nooit ongated kan mergen. Bewuste, geaudite uitzondering op "mergen is
# mensenwerk" (§A7): niet mens-only maar reviewer-tier, begrensd door dit predikaat.
#
# Automatische beoordeling (eigenaarsbesluit 2026-10-06: de eigenaar beoordeelt niets
# meer met de hand) voegt twee smalle routes toe, elk met een onafhankelijke A1:
#   - een NEUTRAAL STRUCTUURFEIT (supporting root op een relatie van een structuurtype:
#     lidmaatschap, dienstverband, bestuurder, …) merget op A1 'klopt' alleen — ook als
#     de relatie een persoon raakt (dezelfde scope als de nieuws-autokeur van 2026-09-30);
#     tegenspraak zoeken (A2) heeft bij "X is wethouder van Y" geen zin;
#   - een ONDERGRAVING (contradicting reply mét reasoning) merget als een onafhankelijk
#     A1-oordeel op die reply 'klopt' zegt: het bezwaar houdt stand. Een bezwaar dempt
#     alleen zijn parent; het kan het model voorzichtiger maken, nooit stelliger.
#   - een BRONREVISIE (revisie die de bewering van een al gemerged argument houdt en
#     alleen de bron verbetert, bv. van de bronzoeker) merget op A1 'klopt' alleen: er komt
#     geen nieuwe bewering in het model, alleen een bron die de oude draagt. Raakt ze een
#     persoon, dan alleen zonder negatief-feitelijke lading (smaad-lexicon).
# Al het andere blijft zoals het was: invloedsclaims vergen A1 én A2, negatieve claims
# over personen nooit automatisch, aspect/duiding/theorie blijven buiten A7.
BEOORDELING_STRUCTUURTYPES = ("personeel", "dienstverband", "bestuurder", "adviseur",
                              "woordvoerder_van", "lidmaatschap", "eigendom", "draaideur",
                              # Uitbreiding C (2026-10-07): openbaar ambt, hiërarchie,
                              # controle en geregistreerde geschenken zijn structuurfeiten
                              "ambt", "zeggenschap", "controle", "geschenk")
AUTO_MERGE_EVIDENTIEEL = (None, "influence", "existence")

# Duplicaat-drempels (spiegelt create_argument, M0.3/A6).
AUTO_MERGE_DIFFLIB_DREMPEL = 0.85
AUTO_MERGE_DEDUP_DREMPEL = 0.80


def _open_ondergraving_in_boom(conn, root_id) -> bool:
    """Is er een niet-'opgelost' ondergraving (contradicting reply) in de boom onder
    ``root_id``? Alleen mee-tellende ondergravingen: gemerged (niet 'voorgesteld'/
    'verworpen'), niet vervangen, bezwaar_resolutie ≠ 'opgelost' (open/herzien/blijft
    dempen de σ nog)."""
    n = conn.execute("""
        WITH RECURSIVE keten(id) AS (
            SELECT id FROM arguments WHERE id = ?
            UNION ALL
            SELECT a.id FROM arguments a JOIN keten k ON a.parent_argument_id = k.id
        )
        SELECT COUNT(*) FROM arguments ond
        JOIN keten k ON k.id = ond.id
        WHERE ond.parent_argument_id IS NOT NULL
          AND ond.stance = 'contradicting'
          AND COALESCE(ond.bezwaar_resolutie, 'open') <> 'opgelost'
          AND NOT ond.vervangen
          AND ond.status NOT IN ('voorgesteld', 'verworpen')
    """, (root_id,)).fetchone()[0]
    return n > 0


def _semantisch_duplicaat(conn, arg) -> bool:
    """A6: bestaat er al een GEMERGEDE root met (bijna) dezelfde claim op hetzelfde
    praktijk-doel? max(difflib, dedup.gelijkenis) ≥ de drempel → duplicaat."""
    doelkol, doelid = None, None
    if arg["relation_id"]:
        doelkol, doelid = "relation_id", arg["relation_id"]
    elif arg["entity_id"]:
        doelkol, doelid = "entity_id", arg["entity_id"]
    if doelkol is None:
        return False
    claim = arg["claim"] or ""
    # Een revisie vervangt haar origineel: dat is geen duplicaat maar haar voorganger
    rijen = conn.execute(f"""
        SELECT claim FROM arguments
        WHERE id <> ? AND id <> COALESCE(?, -1) AND parent_argument_id IS NULL
          AND NOT vervangen AND status NOT IN ('voorgesteld', 'verworpen')
          AND {doelkol} = ?
    """, (arg["id"], arg["reviseert_id"], doelid)).fetchall()
    return any(_zelfde_bewering(claim, r["claim"] or "") for r in rijen)


def _zelfde_bewering(claim, ander) -> bool:
    """(Bijna) dezelfde bewering: max(difflib, dedup.gelijkenis) ≥ de A6-drempel."""
    difflib_ratio = difflib.SequenceMatcher(None, claim, ander).ratio()
    dedup_ratio = dedup.gelijkenis(claim, ander) if dedup is not None else 0.0
    return (difflib_ratio >= AUTO_MERGE_DIFFLIB_DREMPEL
            or dedup_ratio >= AUTO_MERGE_DEDUP_DREMPEL)


def _bronrevisie(conn, arg) -> bool:
    """Automatische beoordeling (2026-10-06, bronzoeker): is dit een revisie die de bewering
    van een al gemerged root-argument houdt (zelfde doel, stance, aspect en bijna dezelfde
    claim) en alleen de bron verbetert? Dan brengt ze geen nieuwe bewering in het model."""
    if not arg["reviseert_id"] or arg["parent_argument_id"] is not None:
        return False
    oud = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg["reviseert_id"],)).fetchone()
    if (oud is None or oud["vervangen"] or oud["parent_argument_id"] is not None
            or oud["status"] in ("voorgesteld", "verworpen")):
        return False
    if ((oud["relation_id"], oud["entity_id"], oud["stance"], oud["property"])
            != (arg["relation_id"], arg["entity_id"], arg["stance"], arg["property"])):
        return False
    return _zelfde_bewering(arg["claim"] or "", oud["claim"] or "")


def _wortel(conn, arg):
    """De root van de boom waarin dit argument staat (het argument zelf als het een root is):
    die draagt het doel (relatie, entiteit of theorie-element)."""
    rij, gezien = arg, set()
    while rij["parent_argument_id"] is not None and rij["id"] not in gezien:
        gezien.add(rij["id"])
        ouder = conn.execute("SELECT * FROM arguments WHERE id = ?",
                             (rij["parent_argument_id"],)).fetchone()
        if ouder is None:
            break
        rij = ouder
    return rij


def _ondergraving_toegestaan(conn, arg):
    """Automatische beoordeling (2026-10-06): een ondergraving — een 'voorgesteld'
    contradicting reply mét reasoning — merget als het nieuwste A1-oordeel op die reply
    'klopt' is (het bezwaar houdt stand), gegeven door een account dat noch de reply noch
    de parent schreef. Een bezwaar dempt alleen zijn parent (DF-QuAD); het maakt het model
    voorzichtiger, nooit stelliger. Overige replies (steun/duiding) blijven mensenwerk."""
    if arg["stance"] != "contradicting":
        return (False, ["reactie die geen ondergraving is — mensenwerk"], "mensenwerk")
    if not (arg["reasoning"] or "").strip():
        return (False, ["ondergraving zonder reasoning — mensenwerk"], "mensenwerk")
    if arg["smaad_hold"]:
        return (False, ["smaad_hold op deze reactie — mensenwerk"], "geblokkeerd-hoog-inzet")
    ouder = conn.execute("SELECT id, status, contributed_by, vervangen FROM arguments "
                         "WHERE id = ?", (arg["parent_argument_id"],)).fetchone()
    if ouder is None or ouder["status"] == "verworpen" or ouder["vervangen"]:
        return (False, ["de parent bestaat niet meer, is verworpen of vervangen"], "mensenwerk")
    a1 = conn.execute("""
        SELECT verdict, door FROM immuun_oordelen
        WHERE argument_id = ? AND fase = 'herverificatie'
        ORDER BY created_at DESC, id DESC LIMIT 1""", (arg["id"],)).fetchone()
    redenen = []
    if a1 is None:
        redenen.append("A1: geen onafhankelijk oordeel over dit bezwaar")
    else:
        if a1["verdict"] != "klopt":
            redenen.append(f"A1: nieuwste oordeel over het bezwaar is '{a1['verdict']}' "
                           "(niet 'klopt')")
        if a1["door"] in (arg["contributed_by"], ouder["contributed_by"]):
            redenen.append("A1: oordeel door de auteur van het bezwaar of van de parent")
    if redenen:
        return (False, redenen, "geparkeerd-twijfel")
    return (True, [], "auto-gemerged")


def auto_merge_toegestaan(conn, arg_id):
    """A7-immuunpoort: mag dit argument automatisch mergen?

    Retourneert (ok, redenen, bucket). ``ok`` is True (bucket 'auto-gemerged')
    ALLEEN als álle condities gelden; anders False met de gefaalde reden(en) en een
    bucket:
      - 'mensenwerk'            — buiten scope (geen voorstel, of zonder doel)
      - 'geblokkeerd-hoog-inzet'— smaad_hold, of een persoonsclaim die de smaadtoets
                                  niet doorstond ('niet_feitelijk')
      - 'geparkeerd-twijfel'    — in scope, maar één of meer signalen ontbreken
    """
    arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not arg:
        return (False, ["Argument niet gevonden"], "mensenwerk")

    # (1) Scope — een 'voorgesteld' argument. Een ondergraving (contradicting reply mét
    # reasoning) heeft haar eigen route (_ondergraving_toegestaan). Sinds "agents doen alles"
    # (eigenaarsbesluit 2026-10-06) beslist deze poort ook over duiding (contextual roots),
    # aspecten (classificatie, politieke positie, data, …), theorie-argumenten (rol,
    # mechanisme, emergent veld) en steunende reacties — met dezelfde eisen als een
    # invloedsclaim: echte bron, onafhankelijke A1 én A2, geen duplicaat.
    if arg["status"] != "voorgesteld":
        return (False, [f"status is '{arg['status']}', niet 'voorgesteld'"], "mensenwerk")
    if (arg["parent_argument_id"] is not None and arg["stance"] == "contradicting"
            and (arg["reasoning"] or "").strip()):
        return _ondergraving_toegestaan(conn, arg)
    if arg["smaad_hold"]:
        return (False, ["smaad_hold op dit argument — wacht op de smaadtoets"],
                "geblokkeerd-hoog-inzet")
    wortel = _wortel(conn, arg)
    if not any(wortel[k] for k in ("relation_id", "entity_id", "role_id", "mechanism_id",
                                   "emergent_effect_id")):
        return (False, ["geen doel (relatie, entiteit of theorie-element)"], "mensenwerk")

    # Neutraal structuurfeit (automatische beoordeling, 2026-10-06): een supporting root op
    # een relatie van een structuurtype merget op een onafhankelijke A1 alleen — ook als de
    # relatie een persoon raakt (geen negatieve claim; scope van de nieuws-autokeur).
    structuur = False
    if (arg["parent_argument_id"] is None and arg["stance"] == "supporting"
            and arg["relation_id"] and arg["property"] in AUTO_MERGE_EVIDENTIEEL):
        rtype = conn.execute("SELECT relation_type FROM relations WHERE id = ?",
                             (arg["relation_id"],)).fetchone()
        structuur = bool(rtype) and rtype["relation_type"] in BEOORDELING_STRUCTUURTYPES
        # Uitbreiding C: een letterlijke registerregel (bv. lobbytoegang, subsidie) is ook
        # een neutraal structuurfeit — geen duiding, alleen wat het register zegt.
        if bool(rtype) and not structuur:
            structuur = _alleen_registercitaties(conn, arg_id)
    # Bronrevisie (2026-10-06): dezelfde bewering als een al gemerged argument, betere bron.
    # Die bewering stond al in het model: alleen de onafhankelijke A1 (de nieuwe bron draagt
    # haar) telt.
    bronrevisie = _bronrevisie(conn, arg)

    # (7) Smaad-firewall (D2.3), sinds 2026-10-06 door agents: een claim die een natuurlijk
    # persoon raakt ("raken" = het doel van de boom is een 'persoon'-entiteit, of een relatie
    # met een persoon als bron of doel) en geen neutraal structuurfeit is, merget alleen na
    # een SMAADTOETS 'feitelijk' van een ander account dan de auteur: een feit, gedragen door
    # de bron (niet verder dan de bron, geen insinuatie), over de publieke rol. 'niet_feitelijk'
    # → geblokkeerd; de opruimstap koppelt het met de reden terug.
    raakt_persoon = _raakt_persoon(conn, entity_id=wortel["entity_id"],
                                   relation_id=wortel["relation_id"])
    smaad = None
    if raakt_persoon and not structuur:
        smaad = _smaadtoets(conn, arg_id, arg["contributed_by"])
        if smaad is not None and smaad["verdict"] == "niet_feitelijk":
            return (False, [f"smaadtoets: niet feitelijk — {smaad['reden']}"],
                    "geblokkeerd-hoog-inzet")

    redenen = []
    if raakt_persoon and not structuur and smaad is None:
        redenen.append("smaadtoets: nog geen oordeel (de claim raakt een natuurlijk persoon)")

    # (2) Citatiepoort — een echte citatie (quote óf vindplaats).
    n_echt = conn.execute("""
        SELECT COUNT(*) FROM citations c WHERE c.argument_id = ? AND (
            (c.quote IS NOT NULL AND TRIM(c.quote) <> '')
            OR EXISTS (SELECT 1 FROM source_locations sl WHERE sl.source_id = c.source_id))
        """, (arg_id,)).fetchone()[0]
    if not n_echt:
        redenen.append("citatiepoort: geen echte bron (quote óf vindplaats)")

    auteur = arg["contributed_by"]

    # (3) A1 — nieuwste her-verificatie-oordeel = 'klopt', door een ander account.
    a1 = conn.execute("""
        SELECT verdict, door, model_familie FROM immuun_oordelen
        WHERE argument_id = ? AND fase = 'herverificatie'
        ORDER BY created_at DESC, id DESC LIMIT 1""", (arg_id,)).fetchone()
    if a1 is None:
        redenen.append("A1: geen bron-herverificatie-oordeel")
    else:
        if a1["verdict"] != "klopt":
            redenen.append(f"A1: nieuwste herverificatie is '{a1['verdict']}' (niet 'klopt')")
        if a1["door"] == auteur:
            redenen.append("A1: her-verificatie door de auteur zelf (geen onafhankelijk oordeel)")

    # (4) A2 — nieuwste tegenspraak-certificaat = 'overleefd' én geen openstaande ondergraving.
    # Een neutraal structuurfeit en een bronrevisie hebben geen tegenspraak nodig (alleen de
    # onafhankelijke A1).
    a2 = conn.execute("""
        SELECT verdict, door, model_familie FROM immuun_oordelen
        WHERE argument_id = ? AND fase = 'tegenspraak'
        ORDER BY id DESC LIMIT 1""", (arg_id,)).fetchone()
    zonder_a2 = structuur or bronrevisie
    if zonder_a2:
        pass
    elif a2 is None:
        redenen.append("A2: geen tegenspraak-certificaat")
    else:
        if a2["verdict"] != "overleefd":
            redenen.append(f"A2: nieuwste tegenspraak is '{a2['verdict']}' (niet 'overleefd')")
        if a2["door"] == auteur:
            redenen.append("A2: tegenspraak door de auteur zelf (geen gedecorreleerde aanklager)")
    if _open_ondergraving_in_boom(conn, arg_id):
        redenen.append("A2: openstaande (niet-'opgelost') ondergraving in de boom")

    # (6) Jury-onafhankelijkheid — A1 en A2 door verschillende accounts (elk ≠ auteur).
    if not zonder_a2 and a1 is not None and a2 is not None and a1["door"] == a2["door"]:
        redenen.append("jury-onafhankelijkheid: A1 en A2 door hetzelfde account")

    # (5) A6 — geen semantisch duplicaat t.o.v. bestaande gemergede roots op dit doel.
    if _semantisch_duplicaat(conn, arg):
        redenen.append("A6: semantisch duplicaat van een bestaande gemergede root op dit doel")

    if redenen:
        return (False, redenen, "geparkeerd-twijfel")
    return (True, [], "auto-gemerged")


@app.route("/api/arguments/<int:arg_id>/auto_merge", methods=["POST"])
@require_user("reviewer")
def auto_merge_argument(arg_id):
    """A7 — auto-merge via de immuunpoort (bedoeld voor het reviewer-tier
    systeemaccount 'merge-service'). Checkt ``auto_merge_toegestaan`` ALTIJD zelf
    (defense-in-depth). Kill-switch: env PROPAGANDA_AUTO_MERGE=0 → 503. Predikaat ok
    → hergebruikt de merge-kern (merged_by = het aanroepende account, edit_log-reden
    'auto-merge (immuunpoort)') en geeft 200; niet ok → 409 + bucket + redenen."""
    if os.environ.get("PROPAGANDA_AUTO_MERGE", "1") == "0":
        return jsonify({"error": "auto-merge uitgeschakeld"}), 503
    conn = get_db()
    arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    ok, redenen, bucket = auto_merge_toegestaan(conn, arg_id)
    if not ok:
        conn.close()
        return jsonify({"merged": False, "bucket": bucket, "redenen": redenen}), 409
    _merge_core(conn, arg, g.user["username"], reason="auto-merge (immuunpoort)")
    conn.commit()
    conn.close()
    return jsonify({"merged": True, "bucket": "auto-gemerged"}), 200


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
    """Lijst van bronnen (voor citaat-selectie).

    Optioneel ``?q=`` filtert op titel/auteur en ``?limit=`` kapt de uitvoer af —
    samen vormen ze de typeahead-zoekopdracht, zodat het bron-kiesveld nooit
    duizenden opties hoeft te renderen. Zonder ``q`` blijft het de volledige lijst
    (de Bronnen-tab heeft die nog nodig)."""
    q = (request.args.get("q") or "").strip()
    try:
        limit = int(request.args.get("limit", 0))
    except ValueError:
        limit = 0
    sql = ["""SELECT s.id, s.title, s.author, s.source_type, s.reliability, s.onderwerp,
        s.date_published,
        s.reliability_voorgesteld, s.onderwerp_voorgesteld, s.classificatie_voorgesteld_door,
        EXISTS(SELECT 1 FROM source_locations l WHERE l.source_id = s.id) AS heeft_locator,
        (SELECT l.location FROM source_locations l WHERE l.source_id = s.id
            AND l.location_type = 'url' LIMIT 1) AS url,
        (SELECT l.location FROM source_locations l WHERE l.source_id = s.id
            AND l.location_type = 'archive_url' LIMIT 1) AS archive_url
        FROM sources s"""]
    params = []
    if q:
        sql.append("WHERE s.title LIKE ? OR s.author LIKE ?")
        params += [f"%{q}%", f"%{q}%"]
    sql.append("ORDER BY s.author")
    if limit > 0:
        sql.append("LIMIT ?")
        params.append(limit)
    conn = get_db()
    rows = conn.execute(" ".join(sql), params).fetchall()
    conn.close()
    uit = []
    for r in rows:
        d = dict(r)
        # Inconsistentie-vlag (zelfde regel als de validator en de classificatie-poort).
        d["problemen"] = validation.klasse_consistentie(d["source_type"], d["reliability"], d["heeft_locator"])
        uit.append(d)
    return jsonify(uit)


SOURCE_TYPES = {"boek", "academisch_artikel", "rapport", "nieuwsartikel",
                "transcript", "interview", "dataset", "wetgeving",
                "persbericht", "website", "overig"}
LOCATION_TYPES = {"url", "file", "doi", "isbn", "arxiv", "handle", "archive_url"}
RELIABILITY_KLASSEN = {"primair", "academisch", "institutioneel", "kwaliteitsjournalistiek",
                       "regulier", "opinie", "grijs", "eigen_synthese", "onbeoordeeld"}
ONDERWERPEN = {"nl_systeem", "algemeen", "buitenlands", "onbepaald"}


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

    # Voorgestelde classificatie (adviserend, telt niet in de score — een reviewer
    # bevestigt haar later via PATCH .../classificatie). Een bijdrager mag dit dus zetten.
    rel_voorstel = (data.get("reliability_voorgesteld") or "").strip() or None
    ond_voorstel = (data.get("onderwerp_voorgesteld") or "").strip() or None
    if rel_voorstel and rel_voorstel not in RELIABILITY_KLASSEN:
        return jsonify({"error": "Ongeldige reliability_voorgesteld. Kies uit: "
                                 + ", ".join(sorted(RELIABILITY_KLASSEN))}), 400
    if ond_voorstel and ond_voorstel not in ONDERWERPEN:
        return jsonify({"error": "Ongeldig onderwerp_voorgesteld. Kies uit: "
                                 + ", ".join(sorted(ONDERWERPEN))}), 400
    voorsteller = g.user["username"] if (rel_voorstel or ond_voorstel) else None

    conn = get_db()
    bestaand = conn.execute("SELECT id, title, author, source_type, reliability "
                            "FROM sources WHERE title = ?", (title,)).fetchone()
    if bestaand:
        conn.close()
        return jsonify({**dict(bestaand), "hergebruikt": True}), 200
    try:
        cur = conn.execute(
            """INSERT INTO sources (title, author, source_type, publisher, date_published,
               cluster_key, reliability_voorgesteld, onderwerp_voorgesteld,
               classificatie_voorgesteld_door)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, author, source_type, publisher, date_published, cluster_key,
             rel_voorstel, ond_voorstel, voorsteller))
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


@app.route("/api/sources/<int:sid>/locations", methods=["POST"])
@require_user()
def add_source_location(sid):
    """Vindplaats (url/doi/isbn/...) toevoegen aan een BESTAANDE bron.

    create_source neemt een locatie alleen bij aanmaak; dit endpoint laat een
    eerder geregistreerde bron alsnog verifieerbaar/klikbaar worden (en zo een
    titel-stub een echte vindplaats geven). Dubbele locaties worden hergebruikt."""
    data = request.json or {}
    loc_type = (data.get("type") or data.get("location_type") or "").strip()
    loc_value = (data.get("value") or data.get("location") or "").strip()
    if loc_type not in LOCATION_TYPES:
        return jsonify({"error": "Ongeldig locatietype. Kies uit: "
                                 + ", ".join(sorted(LOCATION_TYPES))}), 400
    if not loc_value:
        return jsonify({"error": "Locatiewaarde is verplicht"}), 400
    conn = get_db()
    if not conn.execute("SELECT 1 FROM sources WHERE id = ?", (sid,)).fetchone():
        conn.close()
        return jsonify({"error": "Bron bestaat niet"}), 404
    bestaat = conn.execute(
        "SELECT id FROM source_locations WHERE source_id=? AND location_type=? AND location=?",
        (sid, loc_type, loc_value)).fetchone()
    if bestaat:
        conn.close()
        return jsonify({"id": bestaat["id"], "source_id": sid, "hergebruikt": True}), 200
    cur = conn.execute(
        "INSERT INTO source_locations (source_id, location_type, location) VALUES (?, ?, ?)",
        (sid, loc_type, loc_value))
    lid = cur.lastrowid
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
                    VALUES ('source_locations', ?, 'created', ?, ?, ?)""",
                 (lid, g.user["username"],
                  json.dumps({"source_id": sid, "location_type": loc_type}),
                  "Vindplaats toegevoegd aan bestaande bron"))
    conn.commit()
    conn.close()
    return jsonify({"id": lid, "source_id": sid, "location_type": loc_type,
                    "location": loc_value}), 201


@app.route("/api/sources/<int:sid>/classificatie_voorstel", methods=["PATCH"])
@require_user()
def stel_classificatie_voor(sid):
    """Een classificatie VOORSTELLEN (bijdrager+, ook agents) — adviserend.

    Spiegelt de voorgesteld→merged-lus van argumenten: dit voorstel telt NIET in de
    score; het vult straks alleen de dropdowns van de reviewer voor. Pas wanneer een
    reviewer het bevestigt (PATCH .../classificatie) verhuist het naar de gezaghebbende
    reliability/onderwerp. Zo classificeert niemand zijn eigen werk de score in."""
    data = request.json or {}
    rel = (data.get("reliability_voorgesteld") or data.get("reliability") or "").strip() or None
    ond = (data.get("onderwerp_voorgesteld") or data.get("onderwerp") or "").strip() or None
    if not rel and not ond:
        return jsonify({"error": "Geef minstens reliability_voorgesteld of onderwerp_voorgesteld"}), 400
    if rel and rel not in RELIABILITY_KLASSEN:
        return jsonify({"error": "Ongeldige reliability. Kies uit: "
                                 + ", ".join(sorted(RELIABILITY_KLASSEN))}), 400
    if ond and ond not in ONDERWERPEN:
        return jsonify({"error": "Ongeldig onderwerp. Kies uit: "
                                 + ", ".join(sorted(ONDERWERPEN))}), 400
    conn = get_db()
    bron = conn.execute("SELECT id, reliability_voorgesteld, onderwerp_voorgesteld "
                        "FROM sources WHERE id = ?", (sid,)).fetchone()
    if not bron:
        conn.close()
        return jsonify({"error": "Bron bestaat niet"}), 404
    nieuwe_rel = rel if rel else bron["reliability_voorgesteld"]
    nieuw_ond = ond if ond else bron["onderwerp_voorgesteld"]
    conn.execute("UPDATE sources SET reliability_voorgesteld = ?, onderwerp_voorgesteld = ?, "
                 "classificatie_voorgesteld_door = ? WHERE id = ?",
                 (nieuwe_rel, nieuw_ond, g.user["username"], sid))
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by,
                    new_value, reason) VALUES ('sources', ?, 'updated', ?, ?, ?)""",
                 (sid, g.user["username"],
                  json.dumps({"reliability_voorgesteld": nieuwe_rel,
                              "onderwerp_voorgesteld": nieuw_ond}),
                  "classificatievoorstel: "
                  + ((data.get("motivatie") or "").strip() or "(geen motivatie)")))
    conn.commit()
    conn.close()
    return jsonify({"id": sid, "reliability_voorgesteld": nieuwe_rel,
                    "onderwerp_voorgesteld": nieuw_ond})


@app.route("/api/sources/<int:sid>/classificatie", methods=["PATCH"])
@require_user("reviewer")
def classificeer_source(sid):
    """Betrouwbaarheidsklasse (reliability) en/of onderwerp van een bron zetten.

    Classificatie stuurt de score (bronfactor × relevantiefactor), dus het is een
    reviewer-besluit — niet een vrije keuze bij het aanmaken. De poort bewaakt dat de
    klasse controleerbaar is (validation.klasse_consistentie): de reliability moet bij het
    brontype passen, en een hoge klasse vereist een vindplaats. Alles gaat naar edit_log
    en is herzienbaar (een latere reviewer kan de classificatie betwisten/wijzigen)."""
    data = request.json or {}
    conn = get_db()
    bron = conn.execute("SELECT id, source_type, reliability, onderwerp FROM sources "
                        "WHERE id = ?", (sid,)).fetchone()
    if not bron:
        conn.close()
        return jsonify({"error": "Bron bestaat niet"}), 404

    nieuwe_rel = data.get("reliability", bron["reliability"])
    nieuw_ond = data.get("onderwerp", bron["onderwerp"])
    if nieuwe_rel not in RELIABILITY_KLASSEN:
        conn.close()
        return jsonify({"error": "Ongeldige reliability. Kies uit: "
                                 + ", ".join(sorted(RELIABILITY_KLASSEN))}), 400
    if nieuw_ond not in ONDERWERPEN:
        conn.close()
        return jsonify({"error": "Ongeldig onderwerp. Kies uit: "
                                 + ", ".join(sorted(ONDERWERPEN))}), 400

    heeft_loc = bool(conn.execute("SELECT 1 FROM source_locations WHERE source_id = ?",
                                  (sid,)).fetchone())
    problemen = validation.klasse_consistentie(bron["source_type"], nieuwe_rel, heeft_loc)
    if problemen:
        conn.close()
        return jsonify({"error": "Classificatie niet controleerbaar/consistent: "
                                 + "; ".join(problemen)}), 400

    # Bevestiging consumeert een eventueel voorstel: het is nu beslist, ruim het op.
    conn.execute("UPDATE sources SET reliability = ?, onderwerp = ?, "
                 "reliability_voorgesteld = NULL, onderwerp_voorgesteld = NULL, "
                 "classificatie_voorgesteld_door = NULL WHERE id = ?",
                 (nieuwe_rel, nieuw_ond, sid))
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by,
                    old_value, new_value, reason) VALUES ('sources', ?, 'updated', ?, ?, ?, ?)""",
                 (sid, g.user["username"],
                  json.dumps({"reliability": bron["reliability"], "onderwerp": bron["onderwerp"]}),
                  json.dumps({"reliability": nieuwe_rel, "onderwerp": nieuw_ond}),
                  (data.get("motivatie") or "").strip() or "bron geclassificeerd"))
    conn.commit()
    conn.close()
    return jsonify({"id": sid, "reliability": nieuwe_rel, "onderwerp": nieuw_ond})


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

    fout = _methode_fout(data.get("methode"), data.get("quote"))
    if fout:
        return jsonify({"error": fout}), 400

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
            INSERT INTO citations (argument_id, source_id, quote, page, section, context, methode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (argument_id, source_id, data.get("quote"), data.get("page"),
              data.get("section"), data.get("context"), data.get("methode")))
        cid = cur.lastrowid

        # Citatiepoort (M0.3): een ÉCHTE citatie (quote óf vindplaats van de bron)
        # heft 'bronvermelding_nodig' op. Een kale titel-stub doet dat niet — anders
        # zou de poort met een lege verwijzing te omzeilen zijn.
        echt = bool((data.get("quote") or "").strip()) or conn.execute(
            "SELECT 1 FROM source_locations WHERE source_id = ?", (source_id,)).fetchone() is not None
        nieuwe_status = None
        if arg["status"] == "bronvermelding_nodig" and echt:
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


@app.route("/api/citations/<int:cid>", methods=["PATCH"])
@require_user()
def patch_citation(cid):
    """Quote/pagina/sectie/context van een bestaande citatie bijwerken.

    Laat een eerder zonder verbatim ingevoerde citatie alsnog een quote krijgen
    (zonder een duplicaat-citatie aan te maken). Heft, net als create_citation, een
    'bronvermelding_nodig'-status op zodra de citatie daarmee 'echt' wordt."""
    data = request.json or {}
    velden = {k: data[k] for k in ("quote", "page", "section", "context", "methode") if k in data}
    if not velden:
        return jsonify({"error": "Niets om te wijzigen (quote/page/section/context/methode)"}), 400
    conn = get_db()
    row = conn.execute("SELECT id, argument_id, source_id, quote, methode FROM citations WHERE id = ?",
                       (cid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Citatie niet gevonden"}), 404
    # A5: valideer de (effectieve) methode tegen de (effectieve) quote — de verbatim-regel
    # geldt ook als je alleen de quote leegmaakt of alleen de methode zet.
    eff_methode = velden.get("methode", row["methode"])
    eff_quote = velden.get("quote", row["quote"])
    fout = _methode_fout(eff_methode, eff_quote)
    if fout:
        conn.close()
        return jsonify({"error": fout}), 400
    sets = ", ".join(f"{k} = ?" for k in velden)
    conn.execute(f"UPDATE citations SET {sets} WHERE id = ?", (*velden.values(), cid))

    # Citatiepoort: een nu-echte citatie (quote óf vindplaats) heft bronvermelding_nodig op.
    arg = conn.execute("SELECT id, status FROM arguments WHERE id = ?",
                       (row["argument_id"],)).fetchone()
    echt = bool((velden.get("quote") or "").strip()) or conn.execute(
        "SELECT 1 FROM source_locations WHERE source_id = ?", (row["source_id"],)).fetchone() is not None
    nieuwe_status = None
    if arg and arg["status"] == "bronvermelding_nodig" and echt:
        nieuwe_status = "ongecontroleerd"
        conn.execute("UPDATE arguments SET status = ? WHERE id = ?", (nieuwe_status, arg["id"]))
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
                    VALUES ('citations', ?, 'updated', ?, ?, ?)""",
                 (cid, g.user["username"], json.dumps(list(velden.keys())),
                  "Citatie bijgewerkt (quote/vindplaats)"))
    conn.commit()
    conn.close()
    return jsonify({"id": cid, "argument_status": nieuwe_status}), 200


@app.route("/api/citations/<int:cid>", methods=["DELETE"])
@require_user()
def delete_citation(cid):
    """Hard delete van een citatie — maintainer-only (consistent met de overige
    hard-deletes van afgewezen/foutieve content). Schrijft een 'deleted'-regel in
    edit_log. Bedoeld voor o.a. een verkeerd aan een argument gehangen citatie."""
    conn = get_db()
    if not heeft_rol(conn, g.user, "maintainer"):
        conn.close()
        return jsonify({"error": "Verwijderen vereist maintainer"}), 403
    row = conn.execute("SELECT id, argument_id, source_id, quote FROM citations WHERE id = ?",
                       (cid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Citatie niet gevonden"}), 404
    conn.execute("DELETE FROM citations WHERE id = ?", (cid,))
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
                    VALUES ('citations', ?, 'deleted', ?, ?, ?)""",
                 (cid, g.user["username"],
                  json.dumps({"argument_id": row["argument_id"], "source_id": row["source_id"],
                              "quote": row["quote"]}, ensure_ascii=False),
                  "Citatie verwijderd (maintainer)"))
    conn.commit()
    conn.close()
    return jsonify({"id": cid, "deleted": True}), 200


# ── Entiteiten & relaties API ────────────────────────────────

# Uitbreiding C (besluitvorming, eigenaarsbesluit 2026-10-07). Spiegelt de CHECK's in schema.sql.
BESTUURSLAGEN = ("eu", "rijk", "provincie", "gemeente", "waterschap", "caribisch", "regio")
EXTERNE_STELSELS = ("tooi", "oo", "tk_persoon", "wikidata", "ep_mep")
# Wie registergegevens (laag, registersoort, externe id's) aan een BESTAANDE entiteit mag
# hangen: de registerpijplijn (tools/registers/) en maintainers. Geen inhoud: alleen
# identificatie en structuur uit een officieel register, gelogd en terug te draaien.
REGISTER_ACCOUNTS = {"register-import", "registercheck"}


def _externe_ids_uit(waarde):
    """→ ([(stelsel, waarde)], fout). Neemt een lijst {stelsel, waarde} aan."""
    if waarde in (None, []):
        return [], None
    if not isinstance(waarde, list):
        return [], "externe_ids moet een lijst {stelsel, waarde} zijn"
    uit = []
    for item in waarde:
        if not isinstance(item, dict):
            return [], "externe_ids moet een lijst {stelsel, waarde} zijn"
        stelsel = (item.get("stelsel") or "").strip()
        w = str(item.get("waarde") or "").strip()
        if stelsel not in EXTERNE_STELSELS:
            return [], f"stelsel moet een van {list(EXTERNE_STELSELS)} zijn"
        if not w:
            return [], "externe id zonder waarde"
        uit.append((stelsel, w))
    return uit, None


def _externe_ids_bezet(conn, ext, behalve=None):
    """Externe id's die al aan een (andere) entiteit hangen."""
    bezet = []
    for stelsel, w in ext:
        rij = conn.execute("SELECT entity_id FROM externe_ids WHERE stelsel = ? AND waarde = ?",
                           (stelsel, w)).fetchone()
        if rij and rij["entity_id"] != behalve:
            bezet.append({"stelsel": stelsel, "waarde": w, "entity_id": rij["entity_id"]})
    return bezet


@app.route("/api/externe_ids", methods=["GET"])
def api_externe_ids():
    """Opzoeken: ?stelsel=tooi[&waarde=oorg10212] of ?entity_id=123. Open, zoals alle GET's."""
    stelsel = (request.args.get("stelsel") or "").strip()
    waarde = (request.args.get("waarde") or "").strip()
    entity_id = request.args.get("entity_id", type=int)
    sql, args = "SELECT entity_id, stelsel, waarde FROM externe_ids WHERE 1=1", []
    if stelsel:
        sql += " AND stelsel = ?"; args.append(stelsel)
    if waarde:
        sql += " AND waarde = ?"; args.append(waarde)
    if entity_id:
        sql += " AND entity_id = ?"; args.append(entity_id)
    if not (stelsel or entity_id):
        return jsonify({"error": "geef stelsel of entity_id"}), 400
    conn = get_db()
    rijen = [dict(r) for r in conn.execute(sql + " ORDER BY entity_id", args)]
    conn.close()
    return jsonify(rijen)


@app.route("/api/entities/<int:eid>/register", methods=["POST"])
@require_user()
def api_entity_register(eid):
    """Registergegevens aan een BESTAANDE entiteit hangen (Uitbreiding C): externe id's,
    bestuurslaag en registersoort (metadata). Vult alleen wat leeg is — overschrijft nooit —
    zodat een registerkoppeling geen inhoud kan wijzigen. Alleen REGISTER_ACCOUNTS of een
    maintainer; elke wijziging staat in edit_log."""
    data = request.json or {}
    conn = get_db()
    if g.user["username"] not in REGISTER_ACCOUNTS and not heeft_rol(conn, g.user, "maintainer"):
        conn.close()
        return jsonify({"error": "alleen de registerpijplijn of een maintainer"}), 403
    rij = conn.execute("SELECT id, bestuurslaag, metadata FROM entities WHERE id = ?",
                       (eid,)).fetchone()
    if not rij:
        conn.close()
        return jsonify({"error": "entiteit niet gevonden"}), 404
    ext, fout = _externe_ids_uit(data.get("externe_ids"))
    laag = (data.get("bestuurslaag") or "").strip() or None
    meta_in = data.get("metadata") or {}
    if not fout and laag is not None and laag not in BESTUURSLAGEN:
        fout = f"bestuurslaag moet een van {list(BESTUURSLAGEN)} zijn"
    if not fout and not isinstance(meta_in, dict):
        fout = "metadata moet een object zijn"
    if fout:
        conn.close()
        return jsonify({"error": fout}), 400
    bezet = _externe_ids_bezet(conn, ext, behalve=eid)
    if bezet:
        conn.close()
        return jsonify({"error": "externe id hoort al bij een andere entiteit",
                        "bezet": bezet}), 409
    gewijzigd = {}
    for stelsel, w in ext:
        if conn.execute("INSERT OR IGNORE INTO externe_ids (entity_id, stelsel, waarde) "
                        "VALUES (?, ?, ?)", (eid, stelsel, w)).rowcount:
            gewijzigd.setdefault("externe_ids", []).append(f"{stelsel}:{w}")
    if laag and not rij["bestuurslaag"]:
        conn.execute("UPDATE entities SET bestuurslaag = ? WHERE id = ?", (laag, eid))
        gewijzigd["bestuurslaag"] = laag
    try:
        meta = json.loads(rij["metadata"]) if rij["metadata"] else {}
    except (TypeError, ValueError):
        meta = {}
    nieuw = {k: v for k, v in meta_in.items() if k not in meta}
    if nieuw:
        meta.update(nieuw)
        conn.execute("UPDATE entities SET metadata = ? WHERE id = ?",
                     (json.dumps(meta, ensure_ascii=False), eid))
        gewijzigd["metadata"] = nieuw
    if gewijzigd:
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('entities', ?, 'updated', ?, ?, ?)
        """, (eid, g.user["username"], json.dumps(gewijzigd, ensure_ascii=False),
              (data.get("reden") or "registerkoppeling (tools/registers)")[:300]))
    conn.commit()
    conn.close()
    return jsonify({"entity_id": eid, "gewijzigd": gewijzigd})


@app.route("/api/relations/<int:rid>/looptijd", methods=["POST"])
@require_user()
def api_relation_looptijd(rid):
    """Een registerfeit loopt af (Uitbreiding C, scripts/registers_sync.py): het register noemt
    het ambt, de nevenfunctie of de toegangspas niet meer. Zet alleen `active_until` (vult wat
    leeg is; een andere einddatum overschrijft het niet), alleen voor een verband dat een
    registercitatie draagt, alleen door het account `registercheck` of een maintainer, en altijd
    met de reden (welke uitgave, welk record) in edit_log. Terug te draaien door een maintainer."""
    data = request.json or {}
    conn = get_db()
    if g.user["username"] != "registercheck" and not heeft_rol(conn, g.user, "maintainer"):
        conn.close()
        return jsonify({"error": "alleen de registercheck of een maintainer"}), 403
    rel = conn.execute("SELECT id, active_until, vervangen FROM relations WHERE id = ?", (rid,)).fetchone()
    if not rel or rel["vervangen"]:
        conn.close()
        return jsonify({"error": "verband niet gevonden"}), 404
    uit_register = conn.execute("""
        SELECT 1 FROM arguments a JOIN citations c ON c.argument_id = a.id
        JOIN sources s ON s.id = c.source_id
        WHERE a.relation_id = ? AND c.methode = 'officieel_register_scrape'
          AND COALESCE(s.cluster_key, '') LIKE 'register:%' LIMIT 1""", (rid,)).fetchone()
    tot = (data.get("active_until") or "").strip()
    reden = (data.get("reden") or "").strip()
    fout = None
    if not uit_register:
        fout = "alleen voor een verband uit een register (registercitatie)"
    elif not re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", tot):
        fout = "active_until moet JJJJ, JJJJ-MM of JJJJ-MM-DD zijn"
    elif not reden:
        fout = "reden is verplicht (welke uitgave, welk record)"
    elif rel["active_until"]:
        fout = f"het verband heeft al een einddatum ({rel['active_until']})"
    if fout:
        conn.close()
        return jsonify({"error": fout}), 400
    conn.execute("UPDATE relations SET active_until = ? WHERE id = ?", (tot, rid))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('relations', ?, 'updated', ?, ?, ?, ?)
    """, (rid, g.user["username"], json.dumps({"active_until": None}), json.dumps({"active_until": tot}),
          f"registers-sync: {reden}"[:300]))
    conn.commit()
    conn.close()
    return jsonify({"id": rid, "active_until": tot})


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
    # Uitbreiding C (besluitvorming, 2026-10-07): bestuurslaag, registersoort (metadata) en
    # externe id's (tooi/oo/tk_persoon/wikidata/ep_mep) — zie _externe_ids_uit.
    bestuurslaag = (data.get("bestuurslaag") or "").strip() or None
    if bestuurslaag is not None and bestuurslaag not in BESTUURSLAGEN:
        return jsonify({"error": f"bestuurslaag moet een van {list(BESTUURSLAGEN)} zijn"}), 400
    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        return jsonify({"error": "metadata moet een object zijn"}), 400
    ext, fout = _externe_ids_uit(data.get("externe_ids"))
    if fout:
        return jsonify({"error": fout}), 400

    conn = get_db()
    bezet = _externe_ids_bezet(conn, ext)
    if bezet:
        conn.close()
        return jsonify({"error": "externe id hoort al bij een andere entiteit",
                        "entity_id": bezet[0]["entity_id"], "bezet": bezet}), 409
    # Moderatiewachtrij: admin → meteen 'goedgekeurd'; ieder ander → 'voorgesteld'
    # (onzichtbaar in viz/scores tot een reviewer goedkeurt).
    status = "goedgekeurd" if heeft_rol(conn, g.user, "maintainer") else "voorgesteld"
    try:
        cur = conn.execute("""
            INSERT INTO entities (name, type, primary_role_id, description, active_from, active_until,
                                  status, bestuurslaag, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, etype, primary_role_id, description, active_from, active_until, status,
              bestuurslaag, json.dumps(metadata, ensure_ascii=False) if metadata else None))
        eid = cur.lastrowid
        for stelsel, waarde in ext:
            conn.execute("INSERT INTO externe_ids (entity_id, stelsel, waarde) VALUES (?, ?, ?)",
                         (eid, stelsel, waarde))

        # Klasse↔instantie-link meteen materialiseren als er een rol-suggestie is (spiegelt
        # create_relation): zonder deze rij telt de entiteit na goedkeuring niet mee in de
        # rolscore (laag C) en trekt ze KOPPEL-ENT-INST. Idempotent (INSERT OR IGNORE op de
        # unieke index). De afgeleide primaire rol (viz-kleur) blijft los hiervan berekend.
        if primary_role_id is not None:
            conn.execute("INSERT OR IGNORE INTO instantiations (role_id, entity_id) "
                         "VALUES (?, ?)", (primary_role_id, eid))

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
    # Uitbreiding C: de ambtstitel zoals het register hem geeft (bij relation_type 'ambt').
    functie = (data.get("functie") or "").strip()[:200] or None
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
    # Guilty-until-proven: een relatie zonder opgegeven influence krijgt de
    # "magnitude-onbekend"-vloer (0.05), niet NULL. NULL gaf derived_influence 0 →
    # gewicht 0 in scoring én de tijdbewuste kleur. De vloer houdt de topologie meetbaar;
    # boven de vloer komen vereist een property='influence'-argument (INVLOED-PRIOR).
    if influence is None:
        influence = 0.05

    conn = get_db()
    for label, eid in (("Bron", source_id), ("Doel", target_id)):
        if not conn.execute("SELECT 1 FROM entities WHERE id = ?", (eid,)).fetchone():
            conn.close()
            return jsonify({"error": f"{label}-entiteit bestaat niet"}), 400

    # Een kandidaat-relatie (nog geen theorie-huis: mechanism_id leeg) landt ALTIJD als
    # 'voorgesteld' — ook van een maintainer. Ze incubeert (telt in niets) tot een RfC
    # haar een mechanisme geeft; pas dan kan ze naar 'goedgekeurd' (poort in _modereer).
    if mechanism_id is None:
        status = "voorgesteld"
    else:
        status = "goedgekeurd" if heeft_rol(conn, g.user, "maintainer") else "voorgesteld"
    try:
        cur = conn.execute("""
            INSERT INTO relations
                (source_id, target_id, relation_type, mechanism_id, description, functie,
                 certainty, influence, bidirectional, active_from, active_until, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, target_id, rtype, mechanism_id, description, functie,
              certainty, influence, bidirectional, active_from, active_until, status))
        rid = cur.lastrowid

        # Klasse↔instantie-link meteen materialiseren als er een mechanisme is (zelfde
        # regel als de RfC-adoptie in voorstellen.py en de maintainer-patch): zonder deze
        # rij telt de relatie na goedkeuring niet mee in de theoriescore van het mechanisme
        # (laag C) en trekt ze KOPPEL-REL-INST. Idempotent (INSERT OR IGNORE op de unieke
        # index). Een kandidaat (mechanism_id NULL) krijgt er geen — die incubeert.
        if mechanism_id is not None:
            conn.execute("INSERT OR IGNORE INTO instantiations (mechanism_id, relation_id) "
                         "VALUES (?, ?)", (mechanism_id, rid))

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


def _is_agent(conn, username):
    """Is dit een agent-account (bot)? Bepaalt of een maintainer andermans werk in-place
    mag bijschaven: alleen bot-werk — een mens herziet zijn eigen bijdrage zelf."""
    if not username:
        return False
    row = conn.execute("SELECT kind FROM users WHERE username = ?", (username,)).fetchone()
    return bool(row and row["kind"] == "agent")


def _maintainer_mag_direct(conn, tabel, rid):
    """Mag de ingelogde maintainer dit praktijk-element (entiteit/relatie) direct
    bewerken? Ja voor agent-werk, eigen werk en seed/onbekende elementen; NEE voor de
    bijdrage van een ándere mens (die herziet zijn eigen werk zelf — zelfde regel als
    bij argumenten en RfC's). Geeft None als het mag, anders een (response, 403)."""
    auteur = _creator_van(conn, tabel, rid)
    if auteur and auteur != g.user["username"] and not _is_agent(conn, auteur):
        return jsonify({"error": "Dit is het werk van een andere gebruiker — een maintainer "
                                 "bewerkt alleen agent-werk (en eigen/seed-elementen) direct. "
                                 "Laat de auteur het herzien, of stel een wijziging voor via "
                                 "POST /api/voorstellen (soort 'herformuleren' of 'hernoemen')."}), 403
    return None


def _modereer_kern(conn, tabel, rid, nieuw, gebruikersnaam, motivatie):
    """Gedeelde moderatie-kern (refactor Epic 12, gedrag ongewijzigd): keur een
    'voorgesteld' node/edge goed of af namens ``gebruikersnaam``. Hergebruikt door
    ``_modereer`` (menselijke reviewer, PATCH …/status) én de nieuws-autokeur
    (``POST /api/nieuws/autokeur/<tabel>/<id>``). Alle poorten zitten HIER, in dezelfde
    volgorde als voorheen: statuswaarde (400) → bestaan (404) → reviewer+ (403) →
    alleen 'voorgesteld' (400) → niemand keurt eigen werk goed (403, M2.1) → orphan-poort
    (400) → bronplicht voor relaties (400). Daarna: statuswissel + instantiatie-backstop
    + edit_log + (bij afwijzen) de cascade over de discussieboom.

    Retourneert (ok, fout, http_code, extra); ``extra`` is bij succes het JSON-antwoord
    ({id, status, argumenten_mee_afgewezen}). Commit blijft bij de caller (net als
    ``_merge_core``); bij een fout is er niets geschreven."""
    if tabel not in ("entities", "relations"):
        raise ValueError(f"onbekende moderatietabel: {tabel}")
    if nieuw not in ("goedgekeurd", "afgewezen"):
        return (False, "status moet 'goedgekeurd' of 'afgewezen' zijn", 400, None)
    rij = conn.execute(f"SELECT status FROM {tabel} WHERE id = ?", (rid,)).fetchone()
    if rij is None:
        return (False, "Niet gevonden", 404, None)
    gebruiker = conn.execute("SELECT * FROM users WHERE username = ? AND active",
                             (gebruikersnaam,)).fetchone()
    if gebruiker is None or not heeft_rol(conn, gebruiker, "reviewer"):
        return (False, "Modereren vereist reviewer of hoger", 403, None)
    if rij["status"] != "voorgesteld":
        return (False, f"Alleen een 'voorgesteld' item kan gemodereerd worden "
                       f"(huidige status: {rij['status']})", 400, None)
    if _creator_van(conn, tabel, rid) == gebruikersnaam:
        return (False, "Niemand keurt eigen werk goed (M2.1): laat een "
                       "andere reviewer dit beoordelen", 403, None)
    # Orphan-poort (bottom-up): een mechanisme-loze relatie is een kandidaat — een
    # praktijkpatroon dat nog geen theorie-huis heeft. Ze mag incuberen als 'voorgesteld'
    # (telt in niets) maar NIET de goedgekeurde graaf in: eerst een RfC die haar adopteert.
    if tabel == "relations" and nieuw == "goedgekeurd":
        if conn.execute("SELECT mechanism_id FROM relations WHERE id = ?",
                        (rid,)).fetchone()["mechanism_id"] is None:
            return (False, "Dit is een kandidaat-relatie zonder mechanisme "
                "(incuberende instantie). Ze kan niet worden goedgekeurd zolang er geen "
                "theorie-element bij hoort: dien een RfC in (soort 'nieuw_theorie_element') "
                "die deze relatie adopteert, of laat haar 'voorgesteld' incuberen.", 400, None)
    # Bronplicht voor relaties (praktijklaag): een edge mag de graaf alleen in als ze
    # door minstens één gesourcet root-argument (supporting/contradicting met echte
    # citatie) wordt gedragen — anders is het een lege bewering. Het argument zelf mag
    # nog 'voorgesteld' zijn (de score blijft op de vloer tot het gemerged is), maar het
    # bewijs moet er zijn. Seed-/maintainer-relaties zijn al 'goedgekeurd' en passeren hier niet.
    if tabel == "relations" and nieuw == "goedgekeurd":
        heeft_bron = conn.execute("""
            SELECT 1 FROM arguments a
            WHERE a.relation_id = ? AND a.parent_argument_id IS NULL AND NOT a.vervangen
              AND a.stance IN ('supporting', 'contradicting')
              AND (EXISTS (SELECT 1 FROM citations c
                           WHERE c.argument_id = a.id AND TRIM(COALESCE(c.quote, '')) <> '')
                   OR EXISTS (SELECT 1 FROM citations c
                              JOIN source_locations l ON l.source_id = c.source_id
                              WHERE c.argument_id = a.id))
            LIMIT 1""", (rid,)).fetchone()
        if not heeft_bron:
            return (False, "Deze relatie heeft nog geen gesourcet argument "
                "(een supporting/contradicting root met een echte citatie — quote of "
                "vindplaats). Een edge zonder bewijs is een lege bewering: wijs af, of "
                "laat de indiener eerst een onderbouwend argument met bron toevoegen.", 400, None)
    conn.execute(f"UPDATE {tabel} SET status = ? WHERE id = ?", (nieuw, rid))
    # Klasse↔instantie-link bij goedkeuring: het choke-point waar een element telt-mee-waardig
    # wordt. Backstop naast create_relation/RfC-adoptie — vangt ook elementen die vóór die
    # fixes 'voorgesteld' zijn aangemaakt zonder instantie-rij. Zonder deze rij telt het
    # goedgekeurde element niet mee in de theoriescore (laag C) en trekt het KOPPEL-REL-INST /
    # (als waarschuwing) KOPPEL-ENT-INST. Idempotent (INSERT OR IGNORE op de unieke index);
    # een kandidaat-relatie zonder mechanisme is hier al geweigerd (orphan-poort hierboven).
    if nieuw == "goedgekeurd":
        if tabel == "relations":
            mech = conn.execute("SELECT mechanism_id FROM relations WHERE id = ?",
                                (rid,)).fetchone()["mechanism_id"]
            if mech is not None:
                conn.execute("INSERT OR IGNORE INTO instantiations (mechanism_id, relation_id) "
                             "VALUES (?, ?)", (mech, rid))
        elif tabel == "entities":
            prol = conn.execute("SELECT primary_role_id FROM entities WHERE id = ?",
                                (rid,)).fetchone()["primary_role_id"]
            if prol is not None:
                conn.execute("INSERT OR IGNORE INTO instantiations (role_id, entity_id) "
                             "VALUES (?, ?)", (prol, rid))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES (?, ?, 'updated', ?, ?, ?, ?)
    """, (tabel, rid, gebruikersnaam, json.dumps({"status": "voorgesteld"}),
          json.dumps({"status": nieuw}), (motivatie or "").strip() or None))
    # Argumenten bouwen het element: wordt een entiteit/relatie afgewezen, dan vervalt ook de
    # onderbouwing. Reject de hele discussie(sub)boom mee — de root-argumenten die op dit
    # element wijzen plus al hun reacties — voor zover nog niet verworpen/vervangen. Zo blijven
    # er geen wees-argumenten 'voorgesteld' in de wachtrij hangen voor een afgewezen element,
    # en verschijnen ze (verworpen) in de Afgewezen-flow waar je ze kunt verbeteren & heropenen.
    # Geen score-effect: scoring.py telt alleen goedgekeurde elementen, en verworpen weegt 0.
    mee_afgewezen = 0
    if nieuw == "afgewezen":
        col = "entity_id" if tabel == "entities" else "relation_id"
        boom = conn.execute(f"""
            WITH RECURSIVE boom(id) AS (
              SELECT id FROM arguments WHERE {col} = ? AND parent_argument_id IS NULL
              UNION ALL
              SELECT a.id FROM arguments a JOIN boom b ON a.parent_argument_id = b.id
            )
            SELECT a.id, a.status FROM arguments a
            WHERE a.id IN (SELECT id FROM boom) AND a.status <> 'verworpen' AND NOT a.vervangen
        """, (rid,)).fetchall()
        for ar in boom:
            conn.execute("UPDATE arguments SET status = 'verworpen' WHERE id = ?", (ar["id"],))
            conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
                            VALUES ('arguments', ?, 'updated', ?, ?, ?, ?)""",
                         (ar["id"], gebruikersnaam, json.dumps({"status": ar["status"]}),
                          json.dumps({"status": "verworpen"}), f"mee-afgewezen met {tabel} #{rid}"))
        mee_afgewezen = len(boom)
    return (True, None, 200, {"id": rid, "status": nieuw, "argumenten_mee_afgewezen": mee_afgewezen})


def _modereer(tabel, rid):
    """Moderatie van een 'voorgesteld' node/edge: reviewer+ keurt goed of af.
    Niemand keurt eigen werk goed (M2.1). Dunne HTTP-schil om ``_modereer_kern``."""
    data = request.json or {}
    conn = get_db()
    ok, fout, code, extra = _modereer_kern(conn, tabel, rid, data.get("status"),
                                           g.user["username"], data.get("motivatie"))
    if not ok:
        conn.close()
        return jsonify({"error": fout}), code
    conn.commit()
    conn.close()
    return jsonify(extra)


@app.route("/api/entities/<int:eid>/status", methods=["PATCH"])
@require_user()
def moderate_entity(eid):
    return _modereer("entities", eid)


@app.route("/api/relations/<int:rid>/status", methods=["PATCH"])
@require_user()
def moderate_relation(rid):
    return _modereer("relations", rid)


def _heraanmeld(tabel, rid, bewerkbaar):
    """Een AFGEWEZEN praktijkelement bijwerken en opnieuw indienen (Fase D): de
    oorspronkelijke auteur óf een maintainer (zodat de admin agent-werk dat is
    afgewezen alsnog kan verbeteren), status 'afgewezen' → 'voorgesteld'. `bewerkbaar`
    = de kolommen die de body mag overschrijven vóór de heraanmelding."""
    data = request.json or {}
    conn = get_db()
    rij = conn.execute(f"SELECT status FROM {tabel} WHERE id = ?", (rid,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": "Niet gevonden"}), 404
    _auteur = _creator_van(conn, tabel, rid)
    if (_auteur != g.user["username"]
            and not (heeft_rol(conn, g.user, "maintainer") and _is_agent(conn, _auteur))):
        conn.close()
        return jsonify({"error": "Alleen de auteur dient zijn afgewezen item opnieuw in "
                                 "(een maintainer mag dit voor agent-werk doen; een mens "
                                 "meldt zijn eigen werk zelf opnieuw aan)"}), 403
    if rij["status"] != "afgewezen":
        conn.close()
        return jsonify({"error": f"Alleen een afgewezen item kun je opnieuw indienen "
                                 f"(huidige status: {rij['status']})"}), 400
    sets, vals, bewerkt = [], [], {}
    for k in bewerkbaar:
        if k in data and data[k] is not None:
            sets.append(f"{k} = ?"); vals.append(data[k]); bewerkt[k] = data[k]
    sets.append("status = ?"); vals.append("voorgesteld")
    try:
        conn.execute(f"UPDATE {tabel} SET {', '.join(sets)} WHERE id = ?", vals + [rid])
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400
    # Het edit_log registreert óók welke velden meegingen, niet alleen de statusflip —
    # zo blijft de herkomst eerlijk nu heraanmelden de inhoud mag corrigeren.
    nieuw = {"status": "voorgesteld", **bewerkt}
    reden = "opnieuw ingediend na herziening" + (f" (bewerkt: {', '.join(bewerkt)})" if bewerkt else " (ongewijzigd)")
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES (?, ?, 'updated', ?, ?, ?, ?)
    """, (tabel, rid, g.user["username"], json.dumps({"status": "afgewezen"}),
          json.dumps(nieuw, ensure_ascii=False), reden))
    conn.commit()
    conn.close()
    return jsonify({"id": rid, "status": "voorgesteld"})


@app.route("/api/entities/<int:eid>/heraanmelden", methods=["POST"])
@require_user()
def resubmit_entity(eid):
    return _heraanmeld("entities", eid, ("name", "type", "description", "primary_role_id"))


@app.route("/api/relations/<int:rid>/heraanmelden", methods=["POST"])
@require_user()
def resubmit_relation(rid):
    return _heraanmeld("relations", rid,
                       ("description", "relation_type", "certainty", "influence", "mechanism_id"))


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


# ── Eigen werk intrekken (auteur verwijdert een eigen concept) ────
# Een nog-VOORGESTELD argument/praktijkelement is een concept: het telt in niets
# mee en niemand heeft het beoordeeld. De indiener mag het zelf definitief
# verwijderen (audit blijft in edit_log). Een al gemerged/goedgekeurd element
# verwijdert de indiener niet — dat verbeter je via een revisie of voert een
# maintainer af. We slepen geen andermans werk mee: bouwde iemand anders erop
# voort (een relatie of argument), dan blokkeert het intrekken (→ maintainer).

def _eigen_intrekbaar_relatie(conn, rid, user):
    """True als elk argument op deze relatie van `user` is (anders sleept intrekken
    andermans werk mee)."""
    return all(a["contributed_by"] == user for a in conn.execute(
        "SELECT contributed_by FROM arguments WHERE relation_id = ?", (rid,)))


def _eigen_intrekbaar_entiteit(conn, eid, user):
    """True als alle relaties die deze entiteit raken én alle argumenten erop van
    `user` zijn — zodat zelf-intrekken alleen het eigen concept opruimt."""
    for r in conn.execute(
            "SELECT id FROM relations WHERE source_id = ? OR target_id = ?", (eid, eid)):
        if _creator_van(conn, "relations", r["id"]) != user:
            return False
        if not _eigen_intrekbaar_relatie(conn, r["id"], user):
            return False
    return all(a["contributed_by"] == user for a in conn.execute(
        "SELECT contributed_by FROM arguments WHERE entity_id = ?", (eid,)))


@app.route("/api/arguments/<int:arg_id>/intrekken", methods=["POST"])
@require_user()
def withdraw_argument(arg_id):
    """De auteur trekt een eigen, nog-VOORGESTELD argument in: een concept dat in niets
    meetelt en dat niemand nog beoordeeld heeft → definitief verwijderd (audit blijft).
    Een gemerged argument verbeter je via een revisie. Een maintainer mag elk argument
    (met thread en al) verwijderen."""
    conn = get_db()
    arg = conn.execute("SELECT id, contributed_by, status, claim FROM arguments WHERE id = ?",
                       (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    eigenaar = arg["contributed_by"] == g.user["username"]
    maintainer = heeft_rol(conn, g.user, "maintainer")
    if not eigenaar and not maintainer:
        conn.close()
        return jsonify({"error": "Alleen de auteur (of een maintainer) trekt dit in"}), 403
    if eigenaar and not maintainer and arg["status"] != "voorgesteld":
        conn.close()
        return jsonify({"error": "Alleen een nog-voorgesteld argument trek je zelf in; "
                                 "een gemerged argument verbeter je via een revisie "
                                 f"(POST /api/arguments/{arg_id}/revisie)."}), 400
    kinderen = conn.execute(
        "SELECT COUNT(*) FROM arguments WHERE parent_argument_id = ?", (arg_id,)).fetchone()[0]
    if kinderen and not maintainer:
        conn.close()
        return jsonify({"error": f"Er hangen {kinderen} reactie(s) onder dit argument; "
                                 "vraag een maintainer om het met thread en al te verwijderen."}), 409
    boom = _collect_argument_tree(conn, [arg_id])
    _delete_arguments(conn, boom)
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, reason)
        VALUES ('arguments', ?, 'deleted', ?, ?, ?)
    """, (arg_id, g.user["username"],
          json.dumps({"claim": arg["claim"], "status": arg["status"]}),
          "auteur trekt eigen voorgesteld argument in" if eigenaar
          else "argument verwijderd (maintainer)"))
    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "deleted": True, "verwijderd": len(boom)})


@app.route("/api/relations/<int:rid>/intrekken", methods=["POST"])
@require_user()
def withdraw_relation(rid):
    """De indiener trekt een eigen, nog-VOORGESTELD (onzichtbaar in de viz) relatie in.
    Definitief verwijderd; audit blijft. Een goedgekeurde relatie verwijdert een maintainer
    (DELETE /api/relations/<id>)."""
    conn = get_db()
    rel = conn.execute("SELECT id, status, relation_type FROM relations WHERE id = ?",
                       (rid,)).fetchone()
    if not rel:
        conn.close()
        return jsonify({"error": "Relatie niet gevonden"}), 404
    maintainer = heeft_rol(conn, g.user, "maintainer")
    eigenaar = _creator_van(conn, "relations", rid) == g.user["username"]
    if not eigenaar and not maintainer:
        conn.close()
        return jsonify({"error": "Alleen de indiener (of een maintainer) trekt dit in"}), 403
    if not maintainer and rel["status"] != "voorgesteld":
        conn.close()
        return jsonify({"error": "Alleen een nog-voorgestelde relatie trek je zelf in; "
                                 "een goedgekeurde relatie verwijdert een maintainer."}), 400
    if not maintainer and not _eigen_intrekbaar_relatie(conn, rid, g.user["username"]):
        conn.close()
        return jsonify({"error": "Iemand anders bouwde op deze relatie voort; "
                                 "vraag een maintainer om ze te verwijderen."}), 409
    _delete_relation_cascade(conn, rid)
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, reason)
        VALUES ('relations', ?, 'deleted', ?, ?, ?)
    """, (rid, g.user["username"], json.dumps({"relation_type": rel["relation_type"]}),
          "indiener trekt eigen voorgestelde relatie in" if eigenaar
          else "relatie verwijderd (maintainer)"))
    conn.commit()
    conn.close()
    return jsonify({"id": rid, "deleted": True})


@app.route("/api/entities/<int:eid>/intrekken", methods=["POST"])
@require_user()
def withdraw_entity(eid):
    """De indiener trekt een eigen, nog-VOORGESTELD praktijkelement in (incl. de eigen
    relaties/argumenten die eraan hangen). Definitief verwijderd; audit blijft. Een
    goedgekeurde entiteit verwijdert een maintainer (DELETE /api/entities/<id>)."""
    conn = get_db()
    ent = conn.execute("SELECT id, name, type, status FROM entities WHERE id = ?",
                       (eid,)).fetchone()
    if not ent:
        conn.close()
        return jsonify({"error": "Entiteit niet gevonden"}), 404
    maintainer = heeft_rol(conn, g.user, "maintainer")
    eigenaar = _creator_van(conn, "entities", eid) == g.user["username"]
    if not eigenaar and not maintainer:
        conn.close()
        return jsonify({"error": "Alleen de indiener (of een maintainer) trekt dit in"}), 403
    if not maintainer and ent["status"] != "voorgesteld":
        conn.close()
        return jsonify({"error": "Alleen een nog-voorgestelde entiteit trek je zelf in; "
                                 "een goedgekeurde entiteit verwijdert een maintainer."}), 400
    if not maintainer and not _eigen_intrekbaar_entiteit(conn, eid, g.user["username"]):
        conn.close()
        return jsonify({"error": "Anderen bouwden op deze entiteit voort (relatie/argument); "
                                 "vraag een maintainer om ze te verwijderen."}), 409
    rel_ids = [row[0] for row in conn.execute(
        "SELECT id FROM relations WHERE source_id = ? OR target_id = ?", (eid, eid)).fetchall()]
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
    """, (eid, g.user["username"], json.dumps({"name": ent["name"], "type": ent["type"]}),
          "indiener trekt eigen voorgestelde entiteit in" if eigenaar
          else "entiteit verwijderd (maintainer)"))
    conn.commit()
    conn.close()
    return jsonify({"id": eid, "deleted": True, "relations_deleted": len(rel_ids)})


# ── Theoretisch model: rollen & mechanismen ──────────────────

@app.route("/api/roles", methods=["GET"])
def list_roles():
    """Lichte rollenlijst (id, naam, categorie) — o.a. voor de rol-keuze bij het
    goedkeuren van een entiteit op /overleg. Lezen is open; vervangen rollen weg."""
    conn = get_db()
    rollen = [dict(r) for r in conn.execute(
        "SELECT id, name, category FROM roles WHERE NOT vervangen ORDER BY category, name")]
    conn.close()
    return jsonify(rollen)


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


@app.route("/api/mechanisms/<int:mid>/filters", methods=["POST"])
@require_user()
def api_mechanism_filters(mid):
    """Overlap (Uitbreiding C, 2026-10-07): extra categorieën aan een BESTAAND mechanisme
    hangen of weghalen (`mechanism_filters`). Zelfde status als het direct toevoegen van een
    theorie-element: alleen een globale maintainer, in de opbouwfase, gelogd en betwistbaar
    (een classificatiedebat loopt via aspect-argumenten met property='filter'). De primaire
    filter (`mechanisms.filter`) blijft altijd staan.
    Body: {"toevoegen": [...], "verwijderen": [...], "motivatie": "..."}."""
    conn = get_db()
    if not heeft_rol(conn, g.user, "maintainer"):
        conn.close()
        return jsonify({"error": "Categorieën van een mechanisme wijzigen vereist een globale "
                                 "maintainer; stel het anders voor via een argument met "
                                 "property 'filter'."}), 403
    d = request.json or {}
    toevoegen = [f for f in (d.get("toevoegen") or []) if isinstance(f, str)]
    verwijderen = [f for f in (d.get("verwijderen") or []) if isinstance(f, str)]
    motivatie = (d.get("motivatie") or "").strip()
    toegestaan = set(voorstellen.MECHANISME_FILTERS) - {"cross_filter"}
    fout = [f for f in toevoegen + verwijderen if f not in toegestaan]
    if fout or not (toevoegen or verwijderen) or not motivatie:
        conn.close()
        return jsonify({"error": "geef toevoegen/verwijderen uit "
                                 f"{sorted(toegestaan)} en een motivatie",
                        "ongeldig": fout}), 400
    mech = conn.execute("SELECT id, name, filter, vervangen FROM mechanisms WHERE id = ?",
                        (mid,)).fetchone()
    if not mech or mech["vervangen"]:
        conn.close()
        return jsonify({"error": "mechanisme niet gevonden of vervangen"}), 404
    if mech["filter"] in verwijderen:
        conn.close()
        return jsonify({"error": "de primaire filter kan niet weg (wijzig die via een RfC)"}), 400
    # De primaire filter hoort zelf ook als rij in mechanism_filters (KOPPEL-MECH-FILTER).
    if mech["filter"] in toegestaan:
        conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) "
                     "VALUES (?, ?)", (mid, mech["filter"]))
    toegevoegd = [f for f in toevoegen if conn.execute(
        "INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) VALUES (?, ?)",
        (mid, f)).rowcount]
    weg = [f for f in verwijderen if conn.execute(
        "DELETE FROM mechanism_filters WHERE mechanism_id = ? AND filter = ?",
        (mid, f)).rowcount]
    if toegevoegd or weg:
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('mechanisms', ?, 'updated', ?, ?, ?)
        """, (mid, g.user["username"],
              json.dumps({"filters_toegevoegd": toegevoegd, "filters_verwijderd": weg}),
              ("Categorieën gewijzigd door maintainer (opbouwfase, langs RfC heen) — "
               f"betwistbaar: {motivatie}")[:500]))
    conn.commit()
    filters = [r[0] for r in conn.execute(
        "SELECT filter FROM mechanism_filters WHERE mechanism_id = ? ORDER BY filter", (mid,))]
    conn.close()
    return jsonify({"id": mid, "name": mech["name"], "toegevoegd": toegevoegd,
                    "verwijderd": weg, "filters": filters})


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
    # Entiteit: een maintainer mag ook de rol-toekenning (her)zetten (opbouwfase) —
    # primary_role_id, met validatie dat de rol bestaat en niet vervangen is.
    # Accepteert 'primary_role_id' of alias 'role_id'; null/0/"" = rol losmaken.
    if element_type == "entiteit" and ("primary_role_id" in d or "role_id" in d):
        raw = d["primary_role_id"] if "primary_role_id" in d else d["role_id"]
        if raw in (None, "", 0, "0"):
            nieuw_rid = None
        else:
            try:
                nieuw_rid = int(raw)
            except (ValueError, TypeError):
                conn.close()
                return jsonify({"error": "primary_role_id moet een rol-id (geheel getal) of null zijn"}), 400
            rol = conn.execute("SELECT vervangen FROM roles WHERE id = ?", (nieuw_rid,)).fetchone()
            if rol is None:
                conn.close()
                return jsonify({"error": f"rol {nieuw_rid} bestaat niet"}), 400
            if rol["vervangen"]:
                conn.close()
                return jsonify({"error": f"rol {nieuw_rid} is vervangen; kies de opvolger"}), 400
        if nieuw_rid != rij["primary_role_id"]:
            diff["primary_role_id"] = {"oud": rij["primary_role_id"], "nieuw": nieuw_rid}
    # Relatie: een maintainer mag ook het theorie-huis (mechanism_id) (her)zetten —
    # nodig voor goedgekeurde relaties van vóór de orphan-poort. Losmaken (null) kan
    # alleen zolang de relatie niet goedgekeurd is: een goedgekeurde orphan is precies
    # wat de poort in _modereer verhindert, dus die maken we hier niet alsnog.
    if element_type == "relatie" and "mechanism_id" in d:
        raw = d["mechanism_id"]
        if raw in (None, "", 0, "0"):
            nieuw_mid = None
        else:
            try:
                nieuw_mid = int(raw)
            except (ValueError, TypeError):
                conn.close()
                return jsonify({"error": "mechanism_id moet een mechanisme-id (geheel getal) of null zijn"}), 400
            mech = conn.execute("SELECT vervangen FROM mechanisms WHERE id = ?", (nieuw_mid,)).fetchone()
            if mech is None:
                conn.close()
                return jsonify({"error": f"mechanisme {nieuw_mid} bestaat niet"}), 400
            if mech["vervangen"]:
                conn.close()
                return jsonify({"error": f"mechanisme {nieuw_mid} is vervangen; kies de opvolger"}), 400
        if nieuw_mid is None and rij["mechanism_id"] is not None and rij["status"] == "goedgekeurd":
            conn.close()
            return jsonify({"error": "Een goedgekeurde relatie kan haar mechanisme niet verliezen "
                                     "(orphan-poort): wijs een ander mechanisme toe, of zet de "
                                     "relatie eerst terug naar 'voorgesteld'."}), 400
        if nieuw_mid != rij["mechanism_id"]:
            diff["mechanism_id"] = {"oud": rij["mechanism_id"], "nieuw": nieuw_mid}
    # Mechanisme: een maintainer mag de rol-eindpunten (her)zetten. Zonder dit pad is
    # er géén manier om source_role_id/target_role_id te corrigeren — terwijl een
    # 'direct' edge zonder eindpunten niet tekent (precies de val waarin een RfC zonder
    # eindpunten belandt). NULL/0/"" = losmaken (alleen zinvol voor de diffuse bron van
    # een veld_eigenschap).
    if element_type == "mechanisme":
        for kol in ("source_role_id", "target_role_id"):
            if kol not in d:
                continue
            raw = d[kol]
            if raw in (None, "", 0, "0"):
                nieuw_rid = None
            else:
                try:
                    nieuw_rid = int(raw)
                except (ValueError, TypeError):
                    conn.close()
                    return jsonify({"error": f"{kol} moet een rol-id (geheel getal) of null zijn"}), 400
                rol = conn.execute("SELECT vervangen FROM roles WHERE id = ?", (nieuw_rid,)).fetchone()
                if rol is None:
                    conn.close()
                    return jsonify({"error": f"rol {nieuw_rid} bestaat niet"}), 400
                if rol["vervangen"]:
                    conn.close()
                    return jsonify({"error": f"rol {nieuw_rid} is vervangen; kies de opvolger"}), 400
            if nieuw_rid != rij[kol]:
                diff[kol] = {"oud": rij[kol], "nieuw": nieuw_rid}
    # Temporele velden (active_from/active_until) mag een maintainer (her)zetten op
    # elementen die ze dragen (entiteit/relatie/rol/mechanisme). Zonder dit pad is er
    # géén manier om een bestaande band te dateren — terwijl de timeline-/tijdbewuste
    # kleur dat juist nodig heeft. NULL/"" = datum wissen; vrije tekst (jaar of datum),
    # consistent met de bestaande seed-data.
    if element_type in ("entiteit", "relatie", "rol", "mechanisme"):
        for kol in ("active_from", "active_until"):
            if kol in d:
                raw = d.get(kol)
                nieuw = None if raw in (None, "", 0, "0") else str(raw).strip()
                if nieuw != (rij[kol] if rij[kol] not in ("",) else None):
                    diff[kol] = {"oud": rij[kol], "nieuw": nieuw}
    if not diff:
        conn.close()
        velden_hint = toegestaan + (["primary_role_id"] if element_type == "entiteit" else []) \
            + (["mechanism_id"] if element_type == "relatie" else []) \
            + (["source_role_id", "target_role_id"] if element_type == "mechanisme" else []) \
            + (["active_from", "active_until"] if element_type in ("entiteit", "relatie", "rol", "mechanisme") else [])
        return jsonify({"error": f"geen gewijzigd veld (toegestaan: {velden_hint})"}), 400
    if "name" in diff and voorstellen._naam_bestaat(conn, element_type, diff["name"]["nieuw"]):
        conn.close()
        return jsonify({"error": f"er bestaat al een {element_type} met die naam"}), 400
    motivatie = (d.get("motivatie") or "").strip() or "direct bewerkt door maintainer"
    try:
        for kol, v in diff.items():
            conn.execute(f"UPDATE {tabel} SET {kol} = ? WHERE id = ?", (v["nieuw"], eid))
        # Klasse↔instantie-link meebewegen (zelfde regel als RfC-adoptie in
        # voorstellen.py): zonder deze rij telt de relatie niet mee in de
        # theoriescore van het mechanisme en trekt ze KOPPEL-REL-INST.
        if "mechanism_id" in diff:
            if diff["mechanism_id"]["oud"]:
                conn.execute("DELETE FROM instantiations WHERE relation_id = ? AND mechanism_id = ?",
                             (eid, diff["mechanism_id"]["oud"]))
            if diff["mechanism_id"]["nieuw"]:
                conn.execute("INSERT OR IGNORE INTO instantiations (mechanism_id, relation_id) "
                             "VALUES (?, ?)", (diff["mechanism_id"]["nieuw"], eid))
        # Idem voor de rol↔entiteit-link als de primaire rol wijzigt: verplaats de
        # instantiatie mee (create_entity/goedkeuring materialiseren haar, dus een
        # rolcorrectie moet de oude rij opruimen en de nieuwe zetten).
        if "primary_role_id" in diff:
            if diff["primary_role_id"]["oud"]:
                conn.execute("DELETE FROM instantiations WHERE entity_id = ? AND role_id = ?",
                             (eid, diff["primary_role_id"]["oud"]))
            if diff["primary_role_id"]["nieuw"]:
                conn.execute("INSERT OR IGNORE INTO instantiations (role_id, entity_id) "
                             "VALUES (?, ?)", (diff["primary_role_id"]["nieuw"], eid))
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


def _auteur_entiteit_patch(conn, eid, ent):
    """Auteur-pad: de bijdrager (incl. agent) die deze entiteit aanmaakte mag haar
    voorstelvelden — incl. de rol-suggestie `primary_role_id` — bijschaven zolang ze
    'voorgesteld' is. Dan telt ze nog nergens in mee (viz/scores negeren 'voorgesteld'),
    dus in-place bewerken breekt geen provenance. Spiegelt de argument-bewerklus
    (PATCH /api/arguments/<id>); een goedgekeurde entiteit wijzigt alleen een maintainer.
    Bewerkbaar: name, type, description, primary_role_id (alias role_id), active_from/until."""
    d = request.json or {}
    diff = {}
    if "name" in d or "naam" in d:
        nieuw = (d.get("name") or d.get("naam") or "").strip()
        if not nieuw:
            conn.close(); return jsonify({"error": "naam mag niet leeg zijn"}), 400
        if nieuw != (ent["name"] or ""):
            if voorstellen._naam_bestaat(conn, "entiteit", nieuw):
                conn.close(); return jsonify({"error": "er bestaat al een entiteit met die naam"}), 400
            diff["name"] = nieuw
    if "type" in d:
        nieuw = (d.get("type") or "").strip()
        if nieuw and nieuw != (ent["type"] or ""):
            diff["type"] = nieuw
    if "description" in d or "definitie" in d:
        nieuw = (d.get("description") or d.get("definitie") or "").strip() or None
        if nieuw != ent["description"]:
            diff["description"] = nieuw
    if "primary_role_id" in d or "role_id" in d:
        raw = d["primary_role_id"] if "primary_role_id" in d else d["role_id"]
        if raw in (None, "", 0, "0"):
            nieuw_rid = None
        else:
            try:
                nieuw_rid = int(raw)
            except (ValueError, TypeError):
                conn.close()
                return jsonify({"error": "primary_role_id moet een rol-id (geheel getal) of null zijn"}), 400
            rol = conn.execute("SELECT vervangen FROM roles WHERE id = ?", (nieuw_rid,)).fetchone()
            if rol is None:
                conn.close(); return jsonify({"error": f"rol {nieuw_rid} bestaat niet"}), 400
            if rol["vervangen"]:
                conn.close(); return jsonify({"error": f"rol {nieuw_rid} is vervangen; kies de opvolger"}), 400
        if nieuw_rid != ent["primary_role_id"]:
            diff["primary_role_id"] = nieuw_rid
    for kol in ("active_from", "active_until"):
        if kol in d:
            raw = d.get(kol)
            nieuw = None if raw in (None, "", 0, "0") else str(raw).strip()
            if nieuw != (ent[kol] if ent[kol] not in ("",) else None):
                diff[kol] = nieuw
    if not diff:
        conn.close()
        return jsonify({"error": "geen gewijzigd veld (toegestaan: name, type, description, "
                                 "primary_role_id, active_from, active_until)"}), 400
    try:
        for kol, v in diff.items():
            conn.execute(f"UPDATE entities SET {kol} = ? WHERE id = ?", (v, eid))
        conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
                        VALUES ('entities', ?, 'updated', ?, ?, ?)""",
                     (eid, g.user["username"], json.dumps(diff, ensure_ascii=False),
                      "auteur bewerkt eigen voorstel"))
        conn.commit(); conn.close()
        return jsonify({"id": eid, "gewijzigd": list(diff), "auteur_bewerkt": True})
    except sqlite3.IntegrityError as e:
        conn.rollback(); conn.close()
        msg = str(e)
        if "UNIQUE" in msg:
            return jsonify({"error": "er bestaat al een entiteit met die naam"}), 400
        if "CHECK" in msg:
            return jsonify({"error": f"ongeldig entiteittype: '{diff.get('type')}'"}), 400
        return jsonify({"error": msg}), 400


@app.route("/api/entities/<int:eid>", methods=["PATCH"])
@require_user()
def patch_entity(eid):
    # Maintainer → volledige directe bewerking (opbouwfase). Anders: de auteur mag
    # z'n eigen, nog-VOORGESTELDE entiteit bijschaven — rol-suggestie incluis.
    conn = get_db()
    if heeft_rol(conn, g.user, "maintainer"):
        belet = _maintainer_mag_direct(conn, "entities", eid)
        conn.close()
        return belet or _maintainer_patch("entiteit")
    ent = conn.execute("SELECT * FROM entities WHERE id = ?", (eid,)).fetchone()
    if ent is None:
        conn.close()
        return jsonify({"error": "entiteit niet gevonden"}), 404
    if ent["status"] != "voorgesteld":
        conn.close()
        return jsonify({"error": "Direct bewerken vereist een globale maintainer. "
                                 "Stel anders een wijziging voor via POST /api/voorstellen "
                                 "(soort 'herformuleren' of 'hernoemen')."}), 403
    maker = conn.execute("SELECT changed_by FROM edit_log WHERE table_name='entities' "
                         "AND record_id=? AND action='created' ORDER BY id LIMIT 1", (eid,)).fetchone()
    if maker is None or maker["changed_by"] != g.user["username"]:
        conn.close()
        return jsonify({"error": "Alleen de auteur bewerkt een eigen voorstel "
                                 "(zolang het 'voorgesteld' is)"}), 403
    return _auteur_entiteit_patch(conn, eid, ent)


@app.route("/api/relations/<int:rid>", methods=["PATCH"])
@require_user()
def patch_relation(rid):
    # Zelfde agent-scope als entiteiten: een maintainer bewerkt geen relatie van een
    # ándere mens direct (die herziet zelf, of via een voorstel). Agent-/eigen/seed-werk wel.
    conn = get_db()
    belet = _maintainer_mag_direct(conn, "relations", rid) if heeft_rol(conn, g.user, "maintainer") else None
    conn.close()
    return belet or _maintainer_patch("relatie")


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

    # Idempotent (net als create_source / add_source_location): sinds create_relation en
    # het goedkeur-pad de klasse↔instantie-link zelf materialiseren, is een expliciete POST
    # van hetzelfde paar een normaal "bestaat al"-geval, geen fout. Geef de bestaande rij
    # terug i.p.v. 400 op de UNIQUE-index.
    if role_id:
        bestaand = conn.execute(
            "SELECT id, role_id, mechanism_id, entity_id, relation_id, exemplarity, notes "
            "FROM instantiations WHERE role_id = ? AND entity_id = ?",
            (role_id, entity_id)).fetchone()
    else:
        bestaand = conn.execute(
            "SELECT id, role_id, mechanism_id, entity_id, relation_id, exemplarity, notes "
            "FROM instantiations WHERE mechanism_id = ? AND relation_id = ?",
            (mechanism_id, relation_id)).fetchone()
    if bestaand:
        conn.close()
        return jsonify({**dict(bestaand), "hergebruikt": True}), 200

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
    reviews = [dict(r) for r in conn.execute(
        """SELECT vr.reviewer, vr.oordeel, vr.motivatie, vr.created_at, u.kind
           FROM voorstel_reviews vr JOIN users u ON u.username = vr.reviewer
           WHERE vr.voorstel_id = ? ORDER BY vr.id""", (rij["id"],))]
    return {
        "id": rij["id"], "soort": rij["soort"], "titel": rij["titel"],
        "payload": payload, "status": rij["status"],
        "ingediend_door": rij["ingediend_door"], "created_at": rij["created_at"],
        "besloten_at": rij["besloten_at"],
        "resultaat": json.loads(rij["resultaat"]) if rij["resultaat"] else None,
        "theorielaag": theorielaag,
        "benodigde_akkoorden": voorstellen.benodigde_akkoorden(rij["soort"], payload),
        "telling": t,
        "reviews": reviews,
    }


@app.route("/api/kandidaten")
def list_kandidaten():
    """Incubator (bottom-up): mechanisme-loze 'voorgesteld'-relaties — praktijk-
    patronen die nog geen theorie-huis hebben — gegroepeerd op rol-paar (A→B).
    Zo lees je af wanneer een rol-paar genoeg instanties heeft verzameld om er via
    een RfC een mechanisme van te maken (die de kandidaten dan adopteert). Telt in
    niets tot adoptie. Open (read)."""
    conn = get_db()
    rows = conn.execute("""
        SELECT r.id, r.relation_type, r.description, r.certainty, r.influence,
               e1.name AS bron, e2.name AS doel,
               e1.primary_role_id AS bron_rol_id, e2.primary_role_id AS doel_rol_id,
               s.name AS bron_rol, t.name AS doel_rol,
               (SELECT COUNT(*) FROM arguments a WHERE a.relation_id = r.id) AS n_argumenten
        FROM relations r
        JOIN entities e1 ON r.source_id = e1.id
        JOIN entities e2 ON r.target_id = e2.id
        LEFT JOIN roles s ON e1.primary_role_id = s.id
        LEFT JOIN roles t ON e2.primary_role_id = t.id
        WHERE r.mechanism_id IS NULL AND r.status = 'voorgesteld' AND NOT r.vervangen
        ORDER BY e1.primary_role_id, e2.primary_role_id, r.id
    """).fetchall()
    conn.close()
    groepen, ongekoppeld = {}, []
    for r in rows:
        rel = {"id": r["id"], "relation_type": r["relation_type"],
               "description": r["description"], "bron": r["bron"], "doel": r["doel"],
               "certainty": r["certainty"], "influence": r["influence"],
               "n_argumenten": r["n_argumenten"]}
        # Zonder afleidbaar rol-paar kun je nog geen mechanisme (rol→rol-edge) destilleren.
        if r["bron_rol_id"] is None or r["doel_rol_id"] is None:
            ongekoppeld.append(rel)
            continue
        groep = groepen.setdefault((r["bron_rol_id"], r["doel_rol_id"]), {
            "bron_rol": {"id": r["bron_rol_id"], "naam": r["bron_rol"]},
            "doel_rol": {"id": r["doel_rol_id"], "naam": r["doel_rol"]},
            "relaties": []})
        groep["relaties"].append(rel)
    kandidaten = sorted(
        ({**g_, "aantal": len(g_["relaties"])} for g_ in groepen.values()),
        key=lambda g_: g_["aantal"], reverse=True)
    return jsonify({"kandidaten": kandidaten, "ongekoppeld": ongekoppeld,
                    "totaal": len(rows)})


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


@app.route("/api/voorstellen/<int:vid>/herzien", methods=["POST"])
@require_user()
def herzien_voorstel(vid):
    """Een afgewezen/ingetrokken voorstel verbeteren en opnieuw indienen (Fase D).

    Maakt een NIEUW 'open' voorstel, voorgevuld uit de oude payload (de body mag
    `payload`/`titel` overschrijven), met `payload.vorige_voorstel_id` naar het
    origineel zodat de herkomst + de ontvangen reviewfeedback herleidbaar blijven.
    Alleen de oorspronkelijke indiener of een maintainer; het oude blijft bewaard.
    """
    conn = get_db()
    oud = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (vid,)).fetchone()
    if not oud:
        conn.close()
        return jsonify({"error": "Voorstel niet gevonden"}), 404
    if oud["status"] not in ("afgewezen", "ingetrokken"):
        conn.close()
        return jsonify({"error": "Alleen een afgewezen of ingetrokken voorstel kun je "
                                 f"herzien (huidige status: {oud['status']})"}), 400
    if (oud["ingediend_door"] != g.user["username"]
            and not (heeft_rol(conn, g.user, "maintainer") and _is_agent(conn, oud["ingediend_door"]))):
        conn.close()
        return jsonify({"error": "Alleen de indiener herziet een voorstel "
                                 "(een maintainer mag dit voor agent-werk doen; een mens "
                                 "herziet zijn eigen voorstel zelf)"}), 403

    data = request.json or {}
    payload = data.get("payload") or json.loads(oud["payload"])
    payload["vorige_voorstel_id"] = vid
    titel = (data.get("titel") or oud["titel"] or "").strip()
    soort = oud["soort"]
    fouten = voorstellen.valideer_payload(conn, soort, payload)
    if fouten:
        conn.close()
        return jsonify({"error": "Herziening voldoet niet aan het sjabloon",
                        "fouten": fouten}), 400
    cur = conn.execute("""
        INSERT INTO voorstellen (soort, titel, payload, ingediend_door)
        VALUES (?, ?, ?, ?)
    """, (soort, titel, json.dumps(payload, ensure_ascii=False), g.user["username"]))
    nid = cur.lastrowid
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('voorstellen', ?, 'created', ?, ?, ?)
    """, (nid, g.user["username"], json.dumps({"herziet": vid, "titel": titel}),
          f"herziening van voorstel #{vid}"))
    conn.commit()
    rij = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (nid,)).fetchone()
    uit = _voorstel_dict(conn, rij)
    conn.close()
    return jsonify(uit), 201


@app.route("/api/voorstellen")
@require_user("reviewer")
def list_voorstellen():
    """Openstaande (of alle, ?status=alle) voorstellen met reviewstand.

    Reviewer+ only (zie review_queue): de voorstellenlijst is moderatie-werkruimte."""
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
@require_user()
def get_voorstel(vid):
    """Voorsteldetail, incl. de hertriage-checklist bij splitsen/samenvoegen
    (per aanhangend argument/relatie/instantiatie/padclaim: toegewezen of niet).

    Zichtbaar voor reviewer+ (moderatie) óf de indiener zelf (die z'n eigen RfC vanuit
    de werkbank bekijkt/herziet). Een andere bijdrager mag andermans voorstel niet zien."""
    conn = get_db()
    rij = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (vid,)).fetchone()
    if not rij:
        conn.close()
        return jsonify({"error": "Voorstel niet gevonden"}), 404
    if (ROLE_ORDER.get(g.user["role"], 0) < ROLE_ORDER["reviewer"]
            and rij["ingediend_door"] != g.user["username"]):
        conn.close()
        return jsonify({"error": "Alleen de indiener of een reviewer+ mag dit voorstel zien"}), 403
    uit = _voorstel_dict(conn, rij)  # bevat al reviews (met motivatie)

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
            resultaat = voorstellen.voer_uit(conn, rij["soort"], payload, vid,
                                             ingediend_door=rij["ingediend_door"])
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


ARG_DOELKOLOMMEN = ("relation_id", "entity_id", "role_id", "mechanism_id",
                    "emergent_effect_id")


def _wortel_doel(conn, arg):
    """(param, id) van het doel waaraan de DRÁAD van dit argument hangt.

    Root-argumenten dragen hun doel zelf; reacties (geen eigen doel, M1.1) erven het
    van hun wortel. Zo kan de reviewkaart de omringende thread laden, ook voor replies.
    """
    rij = arg
    while rij["parent_argument_id"] is not None:
        rij = conn.execute(
            "SELECT id, parent_argument_id, relation_id, entity_id, role_id, "
            "mechanism_id, emergent_effect_id FROM arguments WHERE id = ?",
            (rij["parent_argument_id"],)).fetchone()
        if rij is None:
            return (None, None)
    for kol in ARG_DOELKOLOMMEN:
        if rij[kol] is not None:
            return (kol, rij[kol])
    return (None, None)


def _doel_leesbaar(conn, param, tid):
    """(type-label, naam) van het doel-element op (param, id). Werkt voor zowel een
    root-argument (z'n eigen doel) als een reactie (die het doel van haar thread-wortel
    erft via _wortel_doel) — zo weet je áltijd over welk element een argument gaat."""
    if not param or not tid:
        return (None, None)
    if param == "relation_id":
        r = conn.execute("""SELECT e1.name || ' → ' || e2.name AS n FROM relations r
                            JOIN entities e1 ON r.source_id = e1.id
                            JOIN entities e2 ON r.target_id = e2.id
                            WHERE r.id = ?""", (tid,)).fetchone()
        return ("relatie", r["n"] if r else f"#{tid}")
    if param == "entity_id":
        r = conn.execute("SELECT name FROM entities WHERE id = ?", (tid,)).fetchone()
        return ("entiteit", r["name"] if r else f"#{tid}")
    if param == "role_id":
        r = conn.execute("SELECT name FROM roles WHERE id = ?", (tid,)).fetchone()
        return ("rol", r["name"] if r else f"#{tid}")
    if param == "mechanism_id":
        r = conn.execute("SELECT name FROM mechanisms WHERE id = ?", (tid,)).fetchone()
        return ("mechanisme", r["name"] if r else f"#{tid}")
    if param == "emergent_effect_id":
        r = conn.execute("SELECT label FROM emergent_effects WHERE id = ?", (tid,)).fetchone()
        return ("veld", r["label"] if r else f"#{tid}")
    return (None, None)


def _verrijk_review_argumenten(conn, rows):
    """Maak van ruwe argumentrijen review-kaart-dicts: leesbaar doel, thread-anker
    (param/id) en citaties + poort-vlag. Gedeeld door de voorgesteld- en de
    herkeuring-lijst (betwist)."""
    argumenten = []
    for a in rows:
        a = dict(a)
        param, tid = _wortel_doel(conn, a)
        a["thread_param"], a["thread_id"] = param, tid
        # Doel-element altijd resolven via de thread-wortel — ook voor een reactie, die
        # zelf geen doel draagt (M1.1) maar wél over het element van haar wortel gaat.
        doel_type, doel_naam = _doel_leesbaar(conn, param, tid)
        a["doel_type"], a["doel_naam"] = doel_type, doel_naam
        if a["parent_argument_id"]:
            a["doel"] = f"reactie op argument #{a['parent_argument_id']}"
        elif doel_type:
            a["doel"] = f"{doel_type}: {doel_naam}"
        else:
            a["doel"] = "—"
        argumenten.append(a)

    # Citaties op de reviewkaart (quote + bron + link/archief) zodat reviewen iets
    # betekent, plus een legibele poort-vlag vóór de merge-klik.
    cites = _citaties_per_argument(conn, [a["id"] for a in argumenten])
    # Immuunsysteem (A1/A2): het nieuwste her-verificatie-verdict + tegenspraak-certificaat
    # per argument, zodat /overleg (en straks de auto-merge-poort A7) ze naast de kaart toont.
    immuun = _immuun_per_argument(conn, [a["id"] for a in argumenten])
    for a in argumenten:
        a["citations"] = cites.get(a["id"], [])
        a["n_echte_bronnen"] = sum(1 for c in a["citations"] if c["echt"])
        a["ongesourcet_root"] = (a["parent_argument_id"] is None
                                 and a["stance"] in ("supporting", "contradicting")
                                 and a["n_echte_bronnen"] == 0)
        oordeel = immuun.get(a["id"], {})
        a["herverificatie"] = oordeel.get("herverificatie")
        a["tegenspraak"] = oordeel.get("tegenspraak")
    return argumenten


def _immuun_per_argument(conn, arg_ids):
    """{arg_id: {'herverificatie': {...}|None, 'tegenspraak': {...}|None}} — per fase het
    NIEUWSTE immuun-oordeel (A1/A2). Leeg als de tabel (nog) niet bestaat (live DB vóór de
    migratie)."""
    if not arg_ids or not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='immuun_oordelen'").fetchone():
        return {}
    qs = ",".join("?" * len(arg_ids))
    resultaat = {}
    # Per (argument, fase) wint de hoogste id = het nieuwste oordeel.
    for row in conn.execute(f"""
            SELECT o.argument_id, o.fase, o.verdict, o.verbatim_span, o.bron_id,
                   o.detail, o.door, o.model_familie, o.created_at
            FROM immuun_oordelen o
            WHERE o.argument_id IN ({qs})
              AND o.id = (SELECT MAX(o2.id) FROM immuun_oordelen o2
                          WHERE o2.argument_id = o.argument_id AND o2.fase = o.fase)
            """, arg_ids):
        resultaat.setdefault(row["argument_id"], {})[row["fase"]] = {
            "verdict": row["verdict"], "verbatim_span": row["verbatim_span"],
            "bron_id": row["bron_id"], "detail": row["detail"], "door": row["door"],
            "model_familie": row["model_familie"], "created_at": row["created_at"]}
    return resultaat


@app.route("/api/review_queue")
@require_user("reviewer")
def review_queue():
    """Review-wachtrij (M2.2): voorgestelde argumenten + open voorstellen, plus de
    herkeuring-lijst (betwiste, al gemergede argumenten — Fase B).

    Reviewer+ only: de wachtrij is moderatie-werkruimte. Voorstellen tellen in niets tot
    een reviewer ze beoordeelt; niet-ingelogden en bijdragers hebben er niets te zoeken
    (hun eigen ingediende werk zien ze in de werkbank, niet hier)."""
    conn = get_db()
    SELECT_ARG = """
        SELECT a.id, a.stance, a.claim, a.reasoning, a.property, a.property_value,
               a.objection_type, a.bezwaar_resolutie, a.parent_argument_id,
               a.contributed_by, a.created_at, a.reviseert_id,
               a.relation_id, a.entity_id, a.role_id, a.mechanism_id, a.emergent_effect_id,
               (SELECT COUNT(*) FROM citations c WHERE c.argument_id = a.id) AS n_citaties
        FROM arguments a WHERE a.status = ? AND NOT a.vervangen ORDER BY a.id"""
    argumenten = _verrijk_review_argumenten(
        conn, conn.execute(SELECT_ARG, ("voorgesteld",)).fetchall())
    herkeuring = _verrijk_review_argumenten(
        conn, conn.execute(SELECT_ARG, ("betwist",)).fetchall())

    open_voorstellen = [_voorstel_dict(conn, r) for r in conn.execute(
        "SELECT * FROM voorstellen WHERE status = 'open' ORDER BY id")]

    # Praktijklaag-moderatie (M0.6/M2.1): entiteiten/relaties die een niet-maintainer
    # toevoegt landen als 'voorgesteld' en worden door de viz verborgen. Zonder ze hier
    # te tonen zou een reviewer ze nergens kunnen vinden. Goedkeuren/afwijzen loopt via
    # /api/entities|relations/<id>/status (zie _modereer).
    entiteiten = []
    for e in conn.execute("""SELECT e.id, e.name, e.type, e.description, e.created_at,
                                    e.primary_role_id, ro.name AS role_name
                             FROM entities e
                             LEFT JOIN roles ro ON ro.id = e.primary_role_id
                             WHERE e.status = 'voorgesteld' ORDER BY e.id"""):
        e = dict(e)
        e["ingediend_door"] = _creator_van(conn, "entities", e["id"])
        entiteiten.append(e)
    # Root-argumenten (mét citaties) ook aan entiteiten meegeven — symmetrisch met relaties
    # hieronder — zodat de reviewer de onderbouwing/positie-signalen op de entiteit-kaart
    # ziet (bv. de politieke_positie-signalen) i.p.v. alleen naam + beschrijving.
    ent_ids = [e["id"] for e in entiteiten]
    args_per_ent = {}
    if ent_ids:
        qs = ",".join("?" * len(ent_ids))
        arg_rows = conn.execute(f"""
            SELECT id, entity_id, stance, status, claim, property, property_value
            FROM arguments
            WHERE entity_id IN ({qs}) AND parent_argument_id IS NULL AND NOT vervangen
            ORDER BY id""", ent_ids).fetchall()
        cites = _citaties_per_argument(conn, [a["id"] for a in arg_rows])
        for a in arg_rows:
            d = dict(a); d["citations"] = cites.get(a["id"], [])
            args_per_ent.setdefault(a["entity_id"], []).append(d)
    for e in entiteiten:
        e["argumenten"] = args_per_ent.get(e["id"], [])
    rel_rows = conn.execute("""
        SELECT r.id, r.relation_type, r.description, r.certainty, r.influence, r.created_at,
               r.bidirectional, r.active_from, r.active_until,
               e1.name AS source_name, e2.name AS target_name,
               m.name AS mechanism_name, m.filter AS mechanism_filter, m.aard AS mechanism_aard
        FROM relations r
        JOIN entities e1 ON r.source_id = e1.id
        JOIN entities e2 ON r.target_id = e2.id
        LEFT JOIN mechanisms m ON r.mechanism_id = m.id
        WHERE r.status = 'voorgesteld' ORDER BY r.id""").fetchall()
    # De onderbouwende root-argumenten (mét citaties) meegeven, zodat de reviewer het
    # bewijs op de praktijk-kaart ziet i.p.v. alleen de kale priors (0%). Een edge zonder
    # gesourcet argument is een lege bewering — die status moet zichtbaar zijn vóór het
    # goedkeuren (en wordt door _modereer geblokkeerd).
    args_per_rel = {}
    rel_ids = [r["id"] for r in rel_rows]
    if rel_ids:
        qs = ",".join("?" * len(rel_ids))
        arg_rows = conn.execute(f"""
            SELECT id, relation_id, stance, status, claim, property
            FROM arguments
            WHERE relation_id IN ({qs}) AND parent_argument_id IS NULL AND NOT vervangen
            ORDER BY id""", rel_ids).fetchall()
        cites = _citaties_per_argument(conn, [a["id"] for a in arg_rows])
        for a in arg_rows:
            d = dict(a)
            d["citations"] = cites.get(a["id"], [])
            args_per_rel.setdefault(a["relation_id"], []).append(d)
    relaties = []
    for r in rel_rows:
        r = dict(r)
        r["ingediend_door"] = _creator_van(conn, "relations", r["id"])
        r["argumenten"] = args_per_rel.get(r["id"], [])
        relaties.append(r)

    conn.close()
    return jsonify({"argumenten": argumenten, "herkeuring": herkeuring,
                    "voorstellen": open_voorstellen,
                    "entiteiten": entiteiten, "relaties": relaties})


@app.route("/api/review_advies")
@require_user("reviewer")
def review_advies():
    """Adviesrapport van de reviewbeoordelaar-agent: read-only beslissteun die in de
    UI rechts van elk wachtrij-item verschijnt. Bewust BUITEN het model — een los
    JSON-bestand dat de agent schrijft (geen discussieboom-bijdrage, telt nergens
    mee, mirrors data/gevoeligheid.json). Reviewer+ only: intern werkmateriaal voor
    wie merget. Leeg als de agent nog geen ronde draaide (missies/reviewbeoordelaar_brief.md)."""
    if not REVIEW_ADVIES_PATH.exists():
        return jsonify({"gegenereerd": None, "ronde": None, "items": {}})
    try:
        return jsonify(json.loads(REVIEW_ADVIES_PATH.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({"error": f"Adviesbestand onleesbaar: {e}", "items": {}}), 500


@app.route("/api/bron_suggesties")
@require_user("reviewer")
def bron_suggesties():
    """Bron-suggesties van de documentalist-agent voor probleem-argumenten (afgewezen
    of bronloos ingediend): per arg:<id> een lijst voorgestelde bronnen, elk optioneel
    met een `check`-verdict van de reviewbeoordelaar (bestaat de bron, dekt hij de claim?).
    Read-only beslissteun BUITEN het model — een los JSON-bestand dat de agents schrijven
    (geen discussieboom-bijdrage, telt nergens mee, mirrors review_advies.json). Reviewer+
    only. Leeg tot de documentalist een ronde draaide (missies/documentalist_brief.md)."""
    if not BRON_SUGGESTIES_PATH.exists():
        return jsonify({"gegenereerd": None, "agent": None, "items": {}})
    try:
        return jsonify(json.loads(BRON_SUGGESTIES_PATH.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({"error": f"Bron-suggestiebestand onleesbaar: {e}", "items": {}}), 500


@app.route("/api/predictions/resolutie_voorstellen")
@require_user("reviewer")
def resolutie_voorstellen():
    """A4 — resolutievoorstellen van de voorspelling-resolutie-agent: per verlopen open
    voorspelling een voorgestelde uitkomst + status + bron. Read-only beslissteun BUITEN
    het model (adviserend, telt nergens mee, mirrors review_advies.json). De agent kan
    NIET scoren (geen reviewer-rol); de eigenaar bevestigt via PATCH …/uitkomst. Reviewer+
    only. Leeg tot de agent een ronde draaide (missies/voorspelling_resolutie_brief.md)."""
    if not VOORSPELLING_VOORSTELLEN_PATH.exists():
        return jsonify({"gegenereerd": None, "agent": None, "items": []})
    try:
        return jsonify(json.loads(VOORSPELLING_VOORSTELLEN_PATH.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({"error": f"Resolutie-voorstelbestand onleesbaar: {e}", "items": []}), 500


@app.route("/api/auto_merge_log")
@require_user("reviewer")
def auto_merge_log():
    """C4 — het auto-merge-verdictlogboek dat de C2-service schrijft: per arg:<id> de
    bucket ('auto-gemerged'/'geparkeerd-twijfel'/'geblokkeerd-hoog-inzet') + de gefaalde
    redenen + tijdstempel. Read-only toezicht-materiaal BUITEN het model (mirrors
    review_advies.json). Reviewer+ only. Leeg tot de service een ronde draaide."""
    if not AUTO_MERGE_LOG_PATH.exists():
        return jsonify({})
    try:
        return jsonify(json.loads(AUTO_MERGE_LOG_PATH.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({"error": f"Auto-merge-logboek onleesbaar: {e}"}), 500


# C4 — overzicht van de onbewaakte achtergrond-agents. launchd draait
# scripts/agent_runner.py; elke ronde schrijft een record in data/agent_runs.jsonl.
# Puur procesmeta (lezend) — telt nergens in de score mee. De cadans komt uit
# agent_schedule (dezelfde bron als de launchd-generator + de schema-editor).
def _agent_runs_overzicht(limiet_historie=5):
    """Lees data/agent_runs.jsonl → per-agent samenvatting (laatste run + korte
    historie + tellingen) voor het toezicht-paneel. Faalveilig: ontbreekt het bestand
    of is een regel stuk, dan sla je 'm over."""
    runs = []
    if AGENT_RUNS_PATH.exists():
        try:
            for regel in AGENT_RUNS_PATH.read_text(encoding="utf-8").splitlines():
                regel = regel.strip()
                if not regel:
                    continue
                try:
                    runs.append(json.loads(regel))
                except json.JSONDecodeError:
                    continue
        except OSError:
            runs = []
    overrides = agent_schedule.laad_overrides()
    cadans_van = lambda label: agent_schedule.cadans_tekst(
        agent_schedule.effectief_schema(label, overrides))
    per = {}
    for r in runs:  # bestandsvolgorde = chronologisch
        label = r.get("label") or r.get("account") or "onbekend"
        per.setdefault(label, []).append(r)
    per_agent = []
    vastgelopen = 0
    for label, lijst in per.items():
        laatste = lijst[-1]
        exit_code = laatste.get("exit_code")
        # Een LinkedIn-blokkade (stroomonderbreker, Epic 12) vraagt eigenaarsaandacht → niet ok.
        ok = ((exit_code == 0) and not laatste.get("linkedin_verlopen")
              and not laatste.get("linkedin_blokkade"))
        if not ok:
            vastgelopen += 1
        per_agent.append({
            "label": label, "cadans": cadans_van(label),
            "laatste": laatste.get("beeindigd"), "exit_code": exit_code,
            "duur_s": laatste.get("duur_s"), "oogst": laatste.get("oogst"),
            "linkedin_verlopen": bool(laatste.get("linkedin_verlopen")),
            "linkedin_blokkade": bool(laatste.get("linkedin_blokkade")),
            "linkedin_rem": bool(laatste.get("linkedin_rem")),
            "ok": ok, "n_runs": len(lijst),
            "historie": [
                {"beeindigd": x.get("beeindigd"), "exit_code": x.get("exit_code"),
                 "oogst": x.get("oogst"), "duur_s": x.get("duur_s"),
                 "ronde": x.get("ronde")}
                for x in lijst[-limiet_historie:][::-1]
            ],
        })
    for a in agent_schedule.AGENTS:  # geplande agents die nog nooit draaiden
        if a["label"] not in per:
            per_agent.append({"label": a["label"], "cadans": cadans_van(a["label"]),
                              "laatste": None, "exit_code": None, "duur_s": None,
                              "oogst": None, "linkedin_verlopen": False,
                              "linkedin_blokkade": False, "linkedin_rem": False, "ok": None,
                              "n_runs": 0, "historie": []})
    per_agent.sort(key=lambda a: (a["laatste"] or ""), reverse=True)
    return {"per_agent": per_agent, "vastgelopen": vastgelopen, "totaal_runs": len(runs)}


@app.route("/api/toezicht")
@require_user("reviewer")
def toezicht():
    """C4 — dun kalibratie-toezicht-aggregaat voor de eigenaar (reviewer+): bundelt de
    auto-merge-doorvoer (uit edit_log merged_by='merge-service' + auto_merge_log.json),
    een steekproef recente service-merges, de voorspellingen-kalibratie (open+verlopen +
    Brier), de validatie-kerngetallen en de archiefdekking. Aggregator, geen zware nieuwe
    logica — de UI-lane (C4) consumeert dit."""
    conn = get_db()

    # Auto-merge-doorvoer: gemerged (24u) uit edit_log; geparkeerd/geblokkeerd uit het logboek.
    gemerged_24u = conn.execute("""
        SELECT COUNT(*) FROM edit_log
        WHERE action = 'merged' AND changed_by = 'merge-service'
          AND created_at >= datetime('now', '-1 day')""").fetchone()[0]
    steekproef = [dict(r) for r in conn.execute("""
        SELECT record_id AS argument_id, created_at, reason FROM edit_log
        WHERE action = 'merged' AND changed_by = 'merge-service'
        ORDER BY id DESC LIMIT 20""")]

    logboek = {}
    if AUTO_MERGE_LOG_PATH.exists():
        try:
            logboek = json.loads(AUTO_MERGE_LOG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logboek = {}
    buckets = {"auto-gemerged": 0, "geparkeerd-twijfel": 0, "geblokkeerd-hoog-inzet": 0}
    for v in logboek.values():
        b = (v or {}).get("bucket")
        if b in buckets:
            buckets[b] += 1

    # Voorspellingen: open-verlopen (zelfde populatie als VOORSPELLING-DEADLINE) + Brier.
    open_verlopen = conn.execute("""
        SELECT COUNT(*) FROM predictions
        WHERE status = 'open' AND deadline < date('now')""").fetchone()[0]
    briers = [r["brier"] for r in conn.execute(
        "SELECT brier FROM predictions WHERE brier IS NOT NULL")]
    brier_gem = round(sum(briers) / len(briers), 4) if briers else None

    # Validatie-kerngetallen (gedeeld met de CLI/health).
    rapport = validation.run_all(conn)
    conn.close()
    totalen = rapport.get("totalen", {})
    archief = rapport.get("kerngetallen", {}).get("archief_dekking")

    return jsonify({
        "auto_merge": {
            "gemerged_24u": gemerged_24u,
            "geparkeerd": buckets["geparkeerd-twijfel"],
            "geblokkeerd": buckets["geblokkeerd-hoog-inzet"],
        },
        "steekproef": steekproef,
        "voorspellingen": {"open_verlopen": open_verlopen, "brier": brier_gem,
                           "n_gescoord": len(briers)},
        "validatie": {"fouten": totalen.get("fout", 0),
                      "waarschuwingen": totalen.get("waarschuwing", 0),
                      "info": totalen.get("info", 0)},
        "archief_dekking": archief,
        "agent_runs": _agent_runs_overzicht(),
    })


@app.route("/api/agents/schedules", methods=["GET"])
@require_user("maintainer")
def agents_schedules_get():
    """C1 — de bewerkbare schema's van de achtergrond-agents (maintainer). Per agent de
    meta + het effectieve schema + de default (zodat de /beheer-editor kan tonen/resetten).
    Puur infra; telt nergens in het model mee."""
    overrides = agent_schedule.laad_overrides()
    status = {a["label"]: a for a in _agent_runs_overzicht()["per_agent"]}
    uit = []
    for a in agent_schedule.AGENTS:
        schema = agent_schedule.effectief_schema(a["label"], overrides)
        st = status.get(a["label"], {})
        uit.append({
            "label": a["label"], "naam": a["naam"], "soort": a["soort"],
            "omschrijving": a.get("omschrijving"),
            "schema": schema, "cadans": agent_schedule.cadans_tekst(schema),
            "default": a.get("default"),
            # laatste-ronde-status (uit data/agent_runs.jsonl) — één rij per agent
            "laatste": st.get("laatste"), "ok": st.get("ok"),
            "exit_code": st.get("exit_code"), "oogst": st.get("oogst"),
            "duur_s": st.get("duur_s"), "n_runs": st.get("n_runs", 0),
            "linkedin_verlopen": st.get("linkedin_verlopen", False),
            "linkedin_blokkade": st.get("linkedin_blokkade", False),
        })
    return jsonify({"agents": uit, "eenheden": agent_schedule.EENHEDEN,
                    "min_minuut": agent_schedule.MIN_ELKE_MINUUT})


@app.route("/api/agents/schedules", methods=["PATCH"])
@require_user("maintainer")
def agents_schedules_patch():
    """Schrijf per-label schema-overrides (maintainer; agents zijn bijdrager → geen
    toegang). agent_schedule valideert/normaliseert. Slaat alleen op — het toepassen op
    launchd loopt via POST /api/agents/herlaad."""
    body = request.get_json(silent=True) or {}
    nieuw = body.get("schedules") if isinstance(body.get("schedules"), dict) else body
    if not isinstance(nieuw, dict):
        return jsonify({"error": "verwacht een object {label: schema}"}), 400
    schoon = agent_schedule.schrijf_overrides(nieuw)
    return jsonify({"ok": True, "overrides": schoon})


@app.route("/api/agents/herlaad", methods=["POST"])
@require_user("maintainer")
def agents_herlaad():
    """Pas de opgeslagen schema's toe op launchd: draai de generator
    (--geen-server --laden) via subprocess. macOS-only; faal-veilig — bij een fout keert
    de melding terug (geen 500) en het opgeslagen schema blijft staan (handmatig
    toepasbaar). --geen-server zodat de draaiende server-job zichzelf niet herstart."""
    script = str(ROOT / "deploy" / "launchd" / "genereer_launchd.py")
    try:
        r = subprocess.run([sys.executable, script, "--geen-server", "--laden"],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        return jsonify({"ok": r.returncode == 0, "returncode": r.returncode,
                        "uitvoer": (r.stdout + r.stderr)[-4000:]})
    except (OSError, subprocess.SubprocessError) as e:
        return jsonify({"ok": False, "uitvoer":
                        f"Kon de generator niet draaien: {e}\nDraai handmatig: "
                        "python3 deploy/launchd/genereer_launchd.py --geen-server --laden"})


@app.route("/api/afgewezen")
@require_user("reviewer")
def afgewezen_queue():
    """Afgewezen/ingetrokken inzendingen voor de admin: verworpen argumenten, afgewezen
    entiteiten/relaties en afgewezen+ingetrokken RfC's — elk met de afwijs-feedback. Buiten
    de gewone review_queue gehouden zodat afgewezen werk de wachtrij niet vervuilt, maar wél
    vindbaar/handelbaar blijft. Reviewer+ mag kijken; de acties (herzien/heropenen/
    heraanmelden/verwijderen) houden elk hun eigen poort (verwijderen = maintainer).

    De argumenten-lijst toont alléén *standalone* verworpen argumenten — afwijzingen op een
    nog levend element (goedgekeurd/voorgesteld). Een argument dat mee-afgewezen is met zíjn
    element hoort niet als los kaartje hier: dat bewerk/heropen je in de discussieboom ónder
    de afgewezen entiteit/relatie zelf (cohesief, niet los van elkaar)."""
    conn = get_db()
    # 'onder_afgewezen' = de hele (sub)boom van elk afgewezen element (root-argumenten die op
    # een afgewezen entiteit/relatie wijzen + al hun reacties). Die sluiten we hier uit; ze
    # leven onder de element-kaart.
    SELECT_ARG = """
        WITH RECURSIVE onder_afgewezen(id) AS (
          SELECT id FROM arguments WHERE parent_argument_id IS NULL AND (
               relation_id IN (SELECT id FROM relations WHERE status = 'afgewezen')
            OR entity_id   IN (SELECT id FROM entities  WHERE status = 'afgewezen'))
          UNION ALL
          SELECT a.id FROM arguments a JOIN onder_afgewezen o ON a.parent_argument_id = o.id
        )
        SELECT a.id, a.stance, a.claim, a.reasoning, a.property, a.property_value,
               a.objection_type, a.bezwaar_resolutie, a.parent_argument_id,
               a.contributed_by, a.created_at, a.reviseert_id,
               a.relation_id, a.entity_id, a.role_id, a.mechanism_id, a.emergent_effect_id,
               (SELECT COUNT(*) FROM citations c WHERE c.argument_id = a.id) AS n_citaties
        FROM arguments a
        WHERE a.status = 'verworpen' AND NOT a.vervangen
          AND a.id NOT IN (SELECT id FROM onder_afgewezen)
        ORDER BY a.id DESC"""
    argumenten = _verrijk_review_argumenten(conn, conn.execute(SELECT_ARG).fetchall())
    for a in argumenten:
        a["feedback"] = _laatste_feedback(conn, "arguments", a["id"])
        a["auteur_is_agent"] = _is_agent(conn, a["contributed_by"])

    voorstellen_lijst = []
    for r in conn.execute("SELECT * FROM voorstellen WHERE status IN ('afgewezen','ingetrokken') "
                          "ORDER BY id DESC"):
        v = _voorstel_dict(conn, r)
        v["feedback"] = _laatste_feedback(conn, "voorstellen", v["id"])
        v["auteur_is_agent"] = _is_agent(conn, v["ingediend_door"])
        voorstellen_lijst.append(v)

    entiteiten = []
    for e in conn.execute("""SELECT e.id, e.name, e.type, e.description, e.created_at,
                                    e.primary_role_id, ro.name AS role_name
                             FROM entities e LEFT JOIN roles ro ON ro.id = e.primary_role_id
                             WHERE e.status = 'afgewezen' ORDER BY e.id DESC"""):
        e = dict(e)
        e["ingediend_door"] = _creator_van(conn, "entities", e["id"])
        e["feedback"] = _laatste_feedback(conn, "entities", e["id"])
        e["auteur_is_agent"] = _is_agent(conn, e["ingediend_door"])
        e["n_argumenten"] = conn.execute(
            "SELECT COUNT(*) c FROM arguments WHERE entity_id = ? "
            "AND parent_argument_id IS NULL AND NOT vervangen", (e["id"],)).fetchone()["c"]
        entiteiten.append(e)

    relaties = []
    for r in conn.execute("""SELECT r.id, r.relation_type, r.description, r.certainty, r.influence,
                                    r.created_at, e1.name AS source_name, e2.name AS target_name,
                                    m.name AS mechanism_name, m.filter AS mechanism_filter
                             FROM relations r
                             JOIN entities e1 ON r.source_id = e1.id
                             JOIN entities e2 ON r.target_id = e2.id
                             LEFT JOIN mechanisms m ON r.mechanism_id = m.id
                             WHERE r.status = 'afgewezen' ORDER BY r.id DESC"""):
        r = dict(r)
        r["ingediend_door"] = _creator_van(conn, "relations", r["id"])
        r["feedback"] = _laatste_feedback(conn, "relations", r["id"])
        r["auteur_is_agent"] = _is_agent(conn, r["ingediend_door"])
        r["n_argumenten"] = conn.execute(
            "SELECT COUNT(*) c FROM arguments WHERE relation_id = ? "
            "AND parent_argument_id IS NULL AND NOT vervangen", (r["id"],)).fetchone()["c"]
        relaties.append(r)

    conn.close()
    return jsonify({"argumenten": argumenten, "voorstellen": voorstellen_lijst,
                    "entiteiten": entiteiten, "relaties": relaties})


@app.route("/api/voorstellen/<int:vid>", methods=["DELETE"])
@require_user("maintainer")
def delete_voorstel(vid):
    """Een afgewezen/ingetrokken RfC hard verwijderen (admin-keuze, geen audit-trail).
    Alleen op een afgewezen of ingetrokken voorstel — een open/geaccepteerd voorstel
    raak je hier niet aan. voorstel_reviews cascadet via FK (ON DELETE CASCADE)."""
    conn = get_db()
    row = conn.execute("SELECT id, titel, soort, status FROM voorstellen WHERE id = ?",
                       (vid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Voorstel niet gevonden"}), 404
    if row["status"] not in ("afgewezen", "ingetrokken"):
        conn.close()
        return jsonify({"error": "Alleen een afgewezen of ingetrokken voorstel kun je "
                                 f"verwijderen (huidige status: {row['status']})"}), 400
    try:
        conn.execute("DELETE FROM lineage WHERE voorstel_id = ?", (vid,))  # defensief; normaal leeg
        conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, reason)
                        VALUES ('voorstellen', ?, 'deleted', ?, ?, ?)""",
                     (vid, g.user["username"],
                      json.dumps({"titel": row["titel"], "soort": row["soort"], "status": row["status"]}),
                      "RfC hard verwijderd (admin)"))
        conn.execute("DELETE FROM voorstellen WHERE id = ?", (vid,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback(); conn.close()
        return jsonify({"error": str(e)}), 400
    conn.close()
    return jsonify({"id": vid, "deleted": True})


@app.route("/api/arguments/<int:arg_id>", methods=["DELETE"])
@require_user("maintainer")
def delete_argument(arg_id):
    """Een verworpen argument hard verwijderen (admin-keuze). Alleen op status
    'verworpen'; weigert als er nog niet-verworpen antwoorden onder hangen (anders sleep
    je levende discussie stilletjes mee). Citaties + de verworpen subboom gaan mee."""
    conn = get_db()
    arg = conn.execute("SELECT id, status, claim FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if arg["status"] != "verworpen":
        conn.close()
        return jsonify({"error": "Alleen een verworpen argument kun je hard verwijderen "
                                 f"(huidige status: {arg['status']}); wijs het eerst af."}), 400
    subtree = _collect_argument_tree(conn, [arg_id])
    overig = [i for i in subtree if i != arg_id]
    if overig:
        ph = ",".join("?" * len(overig))
        levend = [r["id"] for r in conn.execute(
            f"SELECT id FROM arguments WHERE id IN ({ph}) AND status <> 'verworpen'", overig)]
        if levend:
            conn.close()
            return jsonify({"error": "Dit argument heeft nog niet-verworpen antwoorden "
                                     f"(#{', #'.join(map(str, levend))}); wijs die eerst af."}), 409
    try:
        conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, reason)
                        VALUES ('arguments', ?, 'deleted', ?, ?, ?)""",
                     (arg_id, g.user["username"], json.dumps({"claim": (arg["claim"] or "")[:200]}),
                      "Verworpen argument hard verwijderd (admin)"))
        _delete_arguments(conn, subtree)
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback(); conn.close()
        return jsonify({"error": str(e)}), 400
    conn.close()
    return jsonify({"id": arg_id, "deleted": True, "verwijderd_aantal": len(subtree)})


@app.route("/api/arguments/<int:arg_id>/heropenen", methods=["POST"])
@require_user("maintainer")
def heropen_argument(arg_id):
    """Een verworpen argument terug in de wachtrij zetten (verworpen → voorgesteld), zodat
    de auteur het kan bijschaven of een reviewer het opnieuw beoordeelt. De body mág het
    argument meteen verbeteren (claim/reasoning/stance + property_value of objection_type +
    citations) — symmetrisch met heraanmelden bij entiteiten/relaties. Inhoud bewerken volgt
    dezelfde poort als PATCH /api/arguments: een maintainer schaaft agent- of eigen werk bij,
    maar herschrijft het argument van een ándere mens niet (dan alléén heropenen; de auteur
    herziet zelf)."""
    data = request.json or {}
    conn = get_db()
    arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if not arg:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if arg["status"] != "verworpen":
        conn.close()
        return jsonify({"error": "Alleen een verworpen argument kun je heropenen "
                                 f"(huidige status: {arg['status']})"}), 400

    # Optionele inhoudsbewerking bij heropenen — zelfde velden + auteurspoort als edit_argument.
    BEWERKVELDEN = ("claim", "reasoning", "stance", "property_value", "objection_type", "citations")
    velden, waarden, bewerkt = [], [], []
    if any(k in data for k in BEWERKVELDEN):
        if arg["contributed_by"] != g.user["username"] and not _is_agent(conn, arg["contributed_by"]):
            conn.close()
            return jsonify({"error": "Een maintainer schaaft agent-/eigen werk bij; het argument "
                                     "van een andere mens herschrijf je niet — heropen het zonder "
                                     "wijziging, dan herziet de auteur het zelf."}), 403
        if "claim" in data:
            claim = (data.get("claim") or "").strip()
            if not claim:
                conn.close()
                return jsonify({"error": "Claim mag niet leeg zijn"}), 400
            velden.append("claim = ?"); waarden.append(claim); bewerkt.append("claim")
        if "reasoning" in data:
            velden.append("reasoning = ?"); waarden.append((data.get("reasoning") or "").strip() or None); bewerkt.append("reasoning")
        if "stance" in data:
            if data["stance"] not in ("supporting", "contradicting", "contextual"):
                conn.close()
                return jsonify({"error": "Ongeldige stance"}), 400
            velden.append("stance = ?"); waarden.append(data["stance"]); bewerkt.append("stance")
        if "property_value" in data and arg["parent_argument_id"] is None:
            velden.append("property_value = ?"); waarden.append((data.get("property_value") or "").strip() or None); bewerkt.append("property_value")
        if "objection_type" in data and arg["parent_argument_id"] is not None:
            velden.append("objection_type = ?"); waarden.append(data.get("objection_type") or None); bewerkt.append("objection_type")

    velden.append("status = ?"); waarden.append("voorgesteld")
    conn.execute(f"UPDATE arguments SET {', '.join(velden)} WHERE id = ?", waarden + [arg_id])
    if isinstance(data.get("citations"), list):
        fout = _zet_citaties(conn, arg_id, data["citations"])
        if fout:
            conn.rollback(); conn.close()
            return jsonify({"error": fout}), 400
        bewerkt.append("citations")
    reden = "heropend door maintainer (verworpen → voorgesteld)" + (f"; bewerkt: {', '.join(bewerkt)}" if bewerkt else "")
    conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
                    VALUES ('arguments', ?, 'updated', ?, ?, ?, ?)""",
                 (arg_id, g.user["username"], json.dumps({"status": "verworpen"}),
                  json.dumps({"status": "voorgesteld", "bewerkt": bewerkt}, ensure_ascii=False), reden))
    conn.commit()
    conn.close()
    return jsonify({"id": arg_id, "status": "voorgesteld", "bewerkt": bewerkt})


def _laatste_feedback(conn, tabel, rid):
    """De meest recente edit_log-reden (motivatie) voor een record — de feedback die
    de auteur in de werkbank te zien krijgt na een afwijzing/herkeuring."""
    row = conn.execute(
        "SELECT reason, changed_by, created_at FROM edit_log "
        "WHERE table_name = ? AND record_id = ? AND reason IS NOT NULL AND TRIM(reason) <> '' "
        "ORDER BY id DESC LIMIT 1", (tabel, rid)).fetchone()
    return dict(row) if row else None


@app.route("/api/mijn/bijdragen")
@require_user()
def mijn_bijdragen():
    """Mijn werkbank (Fase E): het eigen ingediende werk met status + ontvangen
    feedback, zodat de auteur weet wat te verbeteren en opnieuw in te dienen."""
    conn = get_db()
    mij = g.user["username"]

    argumenten = []
    for a in conn.execute("""
        SELECT id, stance, claim, status, property, parent_argument_id, created_at,
               vervangen, reviseert_id,
               relation_id, entity_id, role_id, mechanism_id, emergent_effect_id
        FROM arguments WHERE contributed_by = ? ORDER BY id DESC""", (mij,)):
        a = dict(a)
        param, tid = _wortel_doel(conn, a)
        a["thread_param"], a["thread_id"] = param, tid
        # Leesbaar doel-element (naam i.p.v. enkel "type #id") — ook voor een reactie,
        # die het element van haar thread-wortel erft.
        a["doel_type"], a["doel_naam"] = _doel_leesbaar(conn, param, tid)
        # Feedback alleen tonen waar ze betekenis heeft (verworpen/betwist/verouderd).
        if a["status"] in ("verworpen", "betwist", "verouderd"):
            a["feedback"] = _laatste_feedback(conn, "arguments", a["id"])
        argumenten.append(a)

    voorstellen_lijst = []
    for v in conn.execute(
            "SELECT * FROM voorstellen WHERE ingediend_door = ? ORDER BY id DESC", (mij,)):
        d = _voorstel_dict(conn, v)
        d["reviews"] = [dict(r) for r in conn.execute(
            """SELECT vr.reviewer, vr.oordeel, vr.motivatie, vr.created_at, u.kind
               FROM voorstel_reviews vr JOIN users u ON u.username = vr.reviewer
               WHERE vr.voorstel_id = ? ORDER BY vr.id""", (v["id"],))]
        voorstellen_lijst.append(d)

    entiteiten, relaties = [], []
    for e in conn.execute("SELECT id, name, type, status FROM entities ORDER BY id DESC"):
        if _creator_van(conn, "entities", e["id"]) != mij:
            continue
        e = dict(e)
        if e["status"] == "afgewezen":
            e["feedback"] = _laatste_feedback(conn, "entities", e["id"])
        entiteiten.append(e)
    for r in conn.execute("""
        SELECT r.id, r.relation_type, r.status, e1.name AS source_name, e2.name AS target_name
        FROM relations r JOIN entities e1 ON r.source_id = e1.id
        JOIN entities e2 ON r.target_id = e2.id ORDER BY r.id DESC"""):
        if _creator_van(conn, "relations", r["id"]) != mij:
            continue
        r = dict(r)
        if r["status"] == "afgewezen":
            r["feedback"] = _laatste_feedback(conn, "relations", r["id"])
        relaties.append(r)

    conn.close()
    return jsonify({"argumenten": argumenten, "voorstellen": voorstellen_lijst,
                    "entiteiten": entiteiten, "relaties": relaties})


@app.route("/api/mijn/interacties")
@require_user()
def mijn_interacties():
    """Wat ánderen op MIJN werk deden: reacties op mijn argumenten + ontvangen ratings
    (👍/👎). Eigen replies/ratings tellen niet mee — dit gaat over wat het werk losmaakte."""
    conn = get_db()
    mij = g.user["username"]
    mijn = {r["id"]: r["claim"] for r in conn.execute(
        "SELECT id, claim FROM arguments WHERE contributed_by = ?", (mij,))}
    replies, ratings = [], []
    if mijn:
        ids = list(mijn)
        qs = ",".join("?" * len(ids))
        for r in conn.execute(f"""
            SELECT id, claim, stance, status, objection_type, parent_argument_id,
                   contributed_by, created_at
            FROM arguments
            WHERE parent_argument_id IN ({qs}) AND contributed_by <> ?
            ORDER BY id DESC LIMIT 100""", ids + [mij]):
            r = dict(r)
            r["op_claim"] = mijn.get(r["parent_argument_id"], "")
            r["thread_param"], r["thread_id"] = _wortel_doel(conn, r)
            replies.append(r)
        for r in conn.execute(f"""
            SELECT ar.argument_id, ar.oordeel, ar.reden, ar.motivatie, ar.created_at,
                   ar.rater, u.kind
            FROM argument_ratings ar JOIN users u ON u.username = ar.rater
            WHERE ar.argument_id IN ({qs}) AND ar.rater <> ?
            ORDER BY ar.id DESC LIMIT 100""", ids + [mij]):
            r = dict(r)
            r["op_claim"] = mijn.get(r["argument_id"], "")
            ratings.append(r)
    conn.close()
    return jsonify({"replies": replies, "ratings": ratings})


@app.route("/api/mijn/herbeoordelen")
@require_user("reviewer")
def mijn_herbeoordelen():
    """Reviewer-inbox: dingen die ÍK eerder afwees of terugstuurde en die de auteur
    verbeterd opnieuw indiende — nu opnieuw wachtend op een beslissing. Zo zie je het
    resultaat van je eigen review terugkomen zonder de hele wachtrij af te speuren."""
    conn = get_db()
    mij = g.user["username"]
    argumenten, voorstellen_lijst, entiteiten, relaties = [], [], [], []

    def mijn_afwijzing(tabel, rid, patroon):
        return conn.execute(
            f"SELECT reason, created_at FROM edit_log WHERE table_name = ? "
            f"AND record_id = ? AND changed_by = ? AND ({patroon}) "
            f"ORDER BY id DESC LIMIT 1", (tabel, rid, mij)).fetchone()

    # 1) Argument-revisies waarvan ik de voorganger betwistte/verwierp
    for a in conn.execute("""
        SELECT id, claim, stance, reviseert_id, created_at, contributed_by,
               relation_id, entity_id, role_id, mechanism_id, emergent_effect_id,
               parent_argument_id
        FROM arguments
        WHERE status = 'voorgesteld' AND reviseert_id IS NOT NULL
        ORDER BY id DESC"""):
        actie = mijn_afwijzing("arguments", a["reviseert_id"],
                               "new_value LIKE '%betwist%' OR new_value LIKE '%verworpen%'")
        if not actie:
            continue
        a = dict(a)
        a["thread_param"], a["thread_id"] = _wortel_doel(conn, a)
        a["mijn_review"] = dict(actie)
        argumenten.append(a)

    # 2) Open herziene voorstellen waarvan ik de voorganger afwees
    for v in conn.execute("SELECT * FROM voorstellen WHERE status = 'open' ORDER BY id DESC"):
        try:
            vorige = (json.loads(v["payload"]) or {}).get("vorige_voorstel_id")
        except (TypeError, ValueError):
            vorige = None
        if not vorige:
            continue
        oordeel = conn.execute(
            "SELECT motivatie, created_at FROM voorstel_reviews WHERE voorstel_id = ? "
            "AND reviewer = ? AND oordeel = 'afwijzen' ORDER BY id DESC LIMIT 1",
            (vorige, mij)).fetchone()
        if not oordeel:
            continue
        d = _voorstel_dict(conn, v)
        d["herziet"] = vorige
        d["mijn_review"] = {"reason": oordeel["motivatie"], "created_at": oordeel["created_at"]}
        voorstellen_lijst.append(d)

    # 3) Praktijkelementen die ik afwees en die opnieuw 'voorgesteld' staan (heraanmeld)
    for e in conn.execute("SELECT id, name, type FROM entities WHERE status = 'voorgesteld'"):
        actie = mijn_afwijzing("entities", e["id"], "new_value LIKE '%afgewezen%'")
        if actie:
            e = dict(e); e["mijn_review"] = dict(actie); entiteiten.append(e)
    for r in conn.execute("""
        SELECT r.id, r.relation_type, e1.name AS source_name, e2.name AS target_name
        FROM relations r JOIN entities e1 ON r.source_id = e1.id
        JOIN entities e2 ON r.target_id = e2.id WHERE r.status = 'voorgesteld'"""):
        actie = mijn_afwijzing("relations", r["id"], "new_value LIKE '%afgewezen%'")
        if actie:
            r = dict(r); r["mijn_review"] = dict(actie); relaties.append(r)

    conn.close()
    return jsonify({"argumenten": argumenten, "voorstellen": voorstellen_lijst,
                    "entiteiten": entiteiten, "relaties": relaties})


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

    # Verrijking voor de startkaart op /overleg (W3.1): argument-regels krijgen de
    # claim + het thread-anker (param/id, via de wortel — reacties dragen zelf geen
    # doel, M1.1) zodat de feed klikbaar naar de juiste thread kan linken. Een
    # inmiddels hard verwijderd argument levert niets op; de client slaat regels
    # zonder anker over. Backward compatible: bestaande velden blijven onaangetast.
    for rij in uit:
        if rij["table_name"] != "arguments":
            continue
        arg = conn.execute(
            "SELECT id, parent_argument_id, stance, claim, relation_id, entity_id, "
            "role_id, mechanism_id, emergent_effect_id FROM arguments WHERE id = ?",
            (rij["record_id"],)).fetchone()
        if arg is None:
            continue
        param, tid = _wortel_doel(conn, arg)
        doel_type, doel_naam = _doel_leesbaar(conn, param, tid)
        rij.update({"claim": arg["claim"], "stance": arg["stance"],
                    "thread_param": param, "thread_id": tid,
                    "doel_type": doel_type, "doel_naam": doel_naam})

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

    Als scripts/analyse_gevoeligheid.py (M1.6), scripts/onderzoeksagenda.py
    (M3.2) of scripts/voorspellingen.py (A4, Brier) een rapport heeft geschreven,
    komt dat mee onder 'gevoeligheid' resp. 'onderzoeksagenda' resp.
    'voorspellingen_kalibratie'; de nieuwste release (M3.1) onder 'release'."""
    conn = get_db()
    rapport = validation.run_all(conn)
    conn.close()
    for sleutel, bestand in (("gevoeligheid", "gevoeligheid.json"),
                             ("onderzoeksagenda", "onderzoeksagenda.json"),
                             ("voorspellingen_kalibratie", "voorspellingen_kalibratie.json")):
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
    scores = scoring.compute_all_scores(conn)
    conn.close()
    return jsonify(scores)


@app.route("/api/inkomsten")
def get_inkomsten():
    """Afgeleide inkomstensamenstelling per outlet (de 'pie'): een COMBINATIE VAN EDGES —
    de inkomende financier-relaties, elk met een gesourcet aandeel (property=
    'inkomensaandeel'), plus een afgeleid restpart 'eigen inkomsten (leden/markt)' =
    100 − Σ. Model-getrouw: het getal komt uit een jaarrekening-citaat, de samenstelling
    wordt afgeleid, niet zelf gezet. ?preview=1 telt nog-`voorgesteld` aandelen voorlopig
    mee (vóór menselijke review); standaard alleen gemergde."""
    preview = request.args.get("preview") in ("1", "true", "ja")
    conn = get_db()
    res = scoring.compute_income_composition(conn, include_voorgesteld=preview)
    conn.close()
    return jsonify(res)


@app.route("/api/kleurmeter")
def get_kleurmeter():
    """Afgeleide politieke kleurmeter (politiek.py): per persoon een 2-assige
    ideologische positie uit GESOURCETE 'politieke_positie'-signalen, per organisatie
    geaggregeerd uit haar bestuurders/leden. ?preview=1 telt nog-`voorgesteld` signalen
    voorlopig mee (vóór menselijke review); standaard alleen gemergde signalen."""
    preview = request.args.get("preview") in ("1", "true", "ja")
    conn = get_db()
    res = politiek.compute_kleurmeter(conn, include_voorgesteld=preview)
    conn.close()
    return jsonify(res)


@app.route("/api/machtsvalentie")
def get_machtsvalentie():
    """Afgeleide machtsvalentie (tegenmacht.py): tegenmacht als GERICHTE edge-valentie.
    Per actor de contra-hegemonische valentie per as (opent/sluit de consensus, Hallin)
    én welke filter-machtsconcentraties ze verantwoordt, uit 'machtsvalentie'-aspect-
    argumenten op edges. ?preview=1 telt nog-`voorgesteld` annotaties voorlopig mee."""
    preview = request.args.get("preview") in ("1", "true", "ja")
    conn = get_db()
    res = tegenmacht.compute_machtsvalentie(conn, include_voorgesteld=preview)
    conn.close()
    return jsonify(res)


@app.route("/api/doelgroep")
def get_doelgroep():
    """Afgeleide welstandsmeter (doelgroep.py): per nieuwsoutlet de getargette marketing-/
    welstandsklasse (hoog A/AB1 ↔ laag C/D) uit GESOURCETE 'doelgroepklasse'-signalen
    (mediakits, NOM/NMO-bereikdata). Operationele brug van koopkrachtselectie. ?preview=1
    telt nog-`voorgesteld` signalen voorlopig mee; standaard alleen gemergde signalen."""
    preview = request.args.get("preview") in ("1", "true", "ja")
    conn = get_db()
    res = doelgroep.compute_doelgroepmeter(conn, include_voorgesteld=preview)
    conn.close()
    return jsonify(res)


@app.route("/api/bereik")
def get_bereik():
    """Afgeleide bereikmeter (bereik.py): per media-entiteit het gesourcete publieksbereik
    per jaar (kijkcijfers/oplage/maandbereik/invullers) uit 'bereik'-signalen. Voedt de
    tijdlijn-gekoppelde node-grootte in de viz. ?preview=1 telt nog-`voorgesteld` signalen
    voorlopig mee; standaard alleen gemergde signalen."""
    preview = request.args.get("preview") in ("1", "true", "ja")
    conn = get_db()
    res = bereik.compute_bereik(conn, include_voorgesteld=preview)
    conn.close()
    return jsonify(res)


# ── Betaalde data-feed (E1): gemeterde namespace achter een API-key ──────────
# De VERKOCHTE slice (structuurgraaf + geldstroom/bereik/welstand) uit de gedeelde
# bouwer export_dataset.verzamel — mechanisch ZONDER de politieke-positie-laag en
# machtsvalentie (neutraliteit + art. 9-AVG). Alléén status='goedgekeurd'. Gated
# + gemeterd; de open /api/graph_data blijft ongemeterd voor de portal.

@app.route("/api/feed/graph")
@require_api_key()
def feed_graph():
    """De verkochte data-slice als JSON: {versie, tabellen:{tabel:{kolommen,rijen}}}.
    Zelfde bron als de CSV-export (scripts/export_dataset.py) — de politieke laag en
    machtsvalentie zitten er per constructie NIET in."""
    conn = get_db()
    try:
        data = export_dataset.verzamel(conn)
    finally:
        conn.close()
    return jsonify({"versie": export_dataset.laatste_versie(), "tabellen": data})


@app.route("/api/feed/export/<tabel>.csv")
@require_api_key()
def feed_export_csv(tabel):
    """Eén verkochte tabel als CSV-download (entities/relations/sources/
    source_locations/income_composition/bereik/doelgroep)."""
    conn = get_db()
    try:
        kolommen, rijen = export_dataset.tabel(conn, tabel)
    except KeyError:
        return jsonify({"error": f"onbekende tabel: {tabel}",
                        "beschikbaar": list(export_dataset.SLICE_TABELLEN)}), 404
    finally:
        conn.close()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(kolommen)
    w.writerows(rijen)
    return app.response_class(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{tabel}.csv"'})


# ── Agent-geheugen: waar heeft dit account al op gereageerd? ──
# Voorkomt dat een agent over de tijd twee keer op hetzelfde argument reageert. Geen
# eigen tabel nodig — de reacties staan al in de data: een reply is een argument met
# parent_argument_id + contributed_by. (De 👍/👎-ratinglaag is bij de solo+agents-
# kanteling geschrapt — A3 — dus reageren = uitsluitend nog via een reply.) Een agent
# haalt vóór een ronde zijn eigen lijst op en slaat die argumenten over.
@app.route("/api/agent/reeds_gereageerd")
@require_user()
def reeds_gereageerd():
    """De argument-id's waar het ingelogde account al op reageerde (via een reply),
    zodat een agent ze in een volgende ronde overslaat."""
    conn = get_db()
    ik = g.user["username"]
    via_reply = sorted({r["parent_argument_id"] for r in conn.execute(
        "SELECT DISTINCT parent_argument_id FROM arguments "
        "WHERE contributed_by = ? AND parent_argument_id IS NOT NULL", (ik,))})
    conn.close()
    return jsonify({"door": ik, "via_reply": via_reply,
                    "gereageerd_op": via_reply})


# ══ Publieke intake: leads-baan + Laag 0-poort (D2-kern / D2.0 / D2.1) ══════════
# Een publieke inzending is een TIP/LEAD, geen claim: ze landt in de aparte, lager-
# vertrouwde `leads`-baan (aparte tabel = structurele isolatie; telt in NIETS mee, geen
# scoring/influence/viz leest 'm, auto-merget nooit, rendert nooit publiek). Vóór de write
# draait een stapel GRATIS filters (Laag 0) — denial-of-wallet-verweer: nooit een agent-
# token besteden aan iets dat een goedkope regel had kunnen droppen. Pas een corroboratie-
# agent (aparte lane) leidt een lead onafhankelijk her af tot een echt 'voorgesteld'
# argument via de gewone POST /api/arguments (met de harde citatiepoort). Alles eenrichting.

# Harde lengtegrenzen per vrije-tekstveld.
LEAD_MAXLENGTHS = {"claim": 1000, "bron_url": 500, "quote": 2000, "betreft": 200}
# Challenge: het lead_token is een HMAC-getekende uitgifte-timestamp (render_ts).
LEAD_TOKEN_MAX_LEEFTIJD = 3600.0   # token 1 uur geldig
LEAD_MIN_INVULTIJD = 2.0           # < 2 s ná uitgifte = bot → stille drop
# Per-IP rate-limit: VEEL strenger dan de account-limieten (30/60/120 per minuut).
LEAD_RATE_LIMIET = 5               # inzendingen ...
LEAD_RATE_WINDOW = 3600.0          # ... per uur, per IP (in-memory emmer, als _rate_emmers)
_lead_emmers = {}
# Sock-puppet-collapse: difflib-drempel op claim+betreft (spiegelt create_argument, M0.3).
LEAD_DEDUP_DREMPEL = 0.85
# Spam-domein-blocklist (host uit bron_url). Uitbreidbaar (D2.4 retroactief blocklisten).
SPAM_DOMEINEN = {
    "bit.ly", "tinyurl.com", "t.me", "spam.example", "casino.example",
    "buy-now.example", "viagra.example", "cheap-pills.example",
}


def _client_ip():
    """Client-IP voor de per-IP-poort. Achter een reverse proxy (B1: Caddy/nginx) staat
    het echte IP in X-Forwarded-For (eerste hop = client); lokaal/tests valt het terug op
    request.remote_addr. (ProxyFix is de nette deploy-variant; deze helper houdt de code
    dependency-vrij.)"""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "onbekend"


def _lead_rate_ok(ip) -> bool:
    nu = time.monotonic()
    emmer = _lead_emmers.setdefault(ip, [])
    emmer[:] = [t for t in emmer if nu - t < LEAD_RATE_WINDOW]
    if len(emmer) >= LEAD_RATE_LIMIET:
        return False
    emmer.append(nu)
    return True


def _teken_lead_token(render_ts: float) -> str:
    ts = f"{render_ts:.3f}"
    sig = hmac.new(app.secret_key, ts.encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"


def _lead_token_geldig(token):
    """(ok, render_ts) — verifieer de HMAC-handtekening en de leeftijd van het lead_token."""
    if not token or not isinstance(token, str) or "." not in token:
        return (False, None)
    ts_str, _, sig = token.rpartition(".")
    verwacht = hmac.new(app.secret_key, ts_str.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, verwacht):
        return (False, None)
    try:
        ts = float(ts_str)
    except ValueError:
        return (False, None)
    if time.time() - ts > LEAD_TOKEN_MAX_LEEFTIJD:
        return (False, None)
    return (True, ts)


def _ip_hash(ip) -> str:
    """Gehasht IP (nooit ruw IP/PII opslaan) — sessiesleutel als pepper, stabiel per IP
    voor de burst-analyse (D2.4)."""
    return hashlib.sha256(app.secret_key + (ip or "").encode()).hexdigest()


def _strip_veld(waarde, maxlen):
    """HTML-escape (stdlib) + harde afkap. Ruwe lengte eerst begrensd, dan geëscaped."""
    s = waarde if isinstance(waarde, str) else ("" if waarde is None else str(waarde))
    return html.escape(s.strip()[:maxlen])


def _spam_domein(bron_url) -> bool:
    if not bron_url:
        return False
    host = (urlparse(bron_url if "//" in bron_url else "//" + bron_url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host in SPAM_DOMEINEN


@app.route("/api/lead_token")
def lead_token():
    """Geef een HMAC-getekende render_ts (challenge-baseline, D2.0). Geen auth. Een
    PoW-/Turnstile-haak kan hierbovenop (open beslissing); de getekende tijdstempel is de
    baseline die zowel de challenge als de tijd-heuristiek voedt."""
    return jsonify({"token": _teken_lead_token(time.time())})


@app.route("/tip")
def tip_page():
    """Publieke intake-widget (D2-kern). De UI-lane levert web/tip.html."""
    return send_file(WEB_PATH / "tip.html")


@app.route("/rectificatie")
def rectificatie_page():
    """Rectificatie-ingang (J2/D2.4) — dezelfde eenrichtings-wachtrij als /tip."""
    return send_file(WEB_PATH / "rectificatie.html")


def _lead_poort(data):
    """Laag 0 (D2.0): kosteloze filters, strikt vóór de write en vóór elke agent-token.
    Volgorde: challenge → honeypot → tijd-heuristiek → per-IP rate-limit → blocklist.
    Retourneert (True, render_ts) of (False, (respons, status)) — een stille 200-drop
    voor bot-signalen (honeypot/te snel), een 400/429 voor challenge/limiet/blocklist."""
    # (1) Challenge — geldig, niet-verlopen HMAC-token.
    ok, render_ts = _lead_token_geldig(data.get("lead_token"))
    if not ok:
        return (False, (jsonify({"error": "Ongeldig of verlopen formulier-token; herlaad "
                                          "de pagina (GET /api/lead_token)."}), 400))
    # (2) Honeypot — het onzichtbare veld 'website' is ingevuld → bot. Stille 200-drop
    #     (geen foutsignaal dat de bot leert te omzeilen).
    if (data.get("website") or "").strip():
        return (False, (jsonify({"ok": True}), 200))
    # (3) Tijd-heuristiek — te snel ingevuld ná uitgifte → bot. Stille drop.
    if time.time() - render_ts < LEAD_MIN_INVULTIJD:
        return (False, (jsonify({"ok": True}), 200))
    # (4) Per-IP rate-limit — veel strenger dan de account-limieten.
    if not _lead_rate_ok(_client_ip()):
        return (False, (jsonify({"error": "Te veel inzendingen; probeer het later "
                                          "opnieuw."}), 429))
    # (5) Spam-domein-blocklist op de bron-URL.
    if _spam_domein(data.get("bron_url") or data.get("url")):
        return (False, (jsonify({"error": "Bron-domein staat op de blocklist."}), 400))
    return (True, render_ts)


@app.route("/api/leads", methods=["POST"])
def create_lead():
    """Publieke intake (D2-kern + D2.0 + D2.1). BEWUST GEEN @require_user — _lead_poort is
    de eigen, loginloze gate. Een welgevormde inzending landt als één rij in de aparte
    leads-baan (status='binnengekomen'); ze telt in NIETS mee en rendert nooit publiek.
    Respons: 201 {lead_id} (ondoorzichtig) of een stille 200-drop / 400/429 uit Laag 0."""
    data = request.json or {}
    poort_ok, uit = _lead_poort(data)
    if not poort_ok:
        return uit
    render_ts = uit

    # (6) HTML-strip + harde lengtebegrenzing op alle vrije-tekstvelden (stored-XSS-verweer).
    claim = _strip_veld(data.get("claim") or data.get("melding"), LEAD_MAXLENGTHS["claim"])
    if not claim.strip():
        return jsonify({"error": "Een melding/claim is verplicht."}), 400
    soort = (data.get("soort") or "tip").strip().lower()
    if soort not in ("tip", "rectificatie"):
        soort = "tip"
    bron_url = _strip_veld(data.get("bron_url") or data.get("url"),
                           LEAD_MAXLENGTHS["bron_url"]) or None
    quote_v = _strip_veld(data.get("quote"), LEAD_MAXLENGTHS["quote"]) or None
    betreft = _strip_veld(data.get("betreft"), LEAD_MAXLENGTHS["betreft"]) or None

    conn = get_db()
    # (7) Sock-puppet-collapse (D2.1): near-dup van een bestaande lead → 'duplicaat', zodat
    #     1000 sock-puppets samenvallen tot één te-corroboreren claim (agreement onder
    #     indieners telt nergens; dezelfde regel als "agreement onder agents is nep-bewijs").
    nieuw_sleutel = (claim + " " + (betreft or "")).lower()
    status = "binnengekomen"
    for rij in conn.execute("SELECT claim, betreft FROM leads"):
        bestaand = ((rij["claim"] or "") + " " + (rij["betreft"] or "")).lower()
        if difflib.SequenceMatcher(None, nieuw_sleutel, bestaand).ratio() >= LEAD_DEDUP_DREMPEL:
            status = "duplicaat"
            break

    cur = conn.execute("""
        INSERT INTO leads (herkomst, soort, claim, bron_url, quote, betreft,
                           ingezonden_ip_hash, render_ts, status)
        VALUES ('publiek', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (soort, claim, bron_url, quote_v, betreft, _ip_hash(_client_ip()),
          f"{render_ts:.3f}", status))
    lead_id = cur.lastrowid
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('leads', ?, 'created', NULL, ?, ?)
    """, (lead_id, json.dumps({"soort": soort, "status": status}),
          "Publieke intake (D2): lead binnengekomen"))
    conn.commit()
    conn.close()
    # Ondoorzichtig lead_id: ontvangst-bevestiging zonder status-lek/thread/reply-kanaal.
    opaque = hashlib.sha256(str(lead_id).encode() + app.secret_key).hexdigest()[:16]
    return jsonify({"lead_id": opaque}), 201


def _mag_leads_lezen(conn):
    """De lead-wachtrij is voor de corroboratie-agent en de eigenaar: reviewer+ of een
    agent-account. Het publiek ziet de quarantaine nooit."""
    return heeft_rol(conn, g.user, "reviewer") or g.user.get("kind") == "agent"


@app.route("/api/leads")
@require_user()
def list_leads():
    """De agent-wachtrij (D2.1): leads voor de corroboratie-agent. Reviewer+ of agent-
    account. Standaard alleen 'binnengekomen'; ?status=<...> of ?status=alle voor de rest."""
    conn = get_db()
    if not _mag_leads_lezen(conn):
        conn.close()
        return jsonify({"error": "Alleen reviewer+ of een agent-account leest de "
                                 "lead-wachtrij"}), 403
    status = request.args.get("status", "binnengekomen")
    if status == "alle":
        rijen = conn.execute("SELECT * FROM leads ORDER BY id").fetchall()
    else:
        rijen = conn.execute("SELECT * FROM leads WHERE status = ? ORDER BY id",
                             (status,)).fetchall()
    leads = [dict(r) for r in rijen]
    conn.close()
    return jsonify({"leads": leads, "aantal": len(leads)})


LEAD_STATUSSEN = ("binnengekomen", "in_corroboratie", "gecorroboreerd", "afgewezen",
                  "duplicaat", "smaad_hold")


@app.route("/api/leads/<int:lead_id>", methods=["PATCH"])
@require_user()
def patch_lead(lead_id):
    """Lead-status bijwerken door de corroboratie-agent (D2.1/D2.2). Reviewer+ of agent-
    account (403 anders). Bedoelde levensloop: binnengekomen → in_corroboratie →
    gecorroboreerd/afgewezen (agent_arg_id wijst naar het afgeleide echte argument). De
    overgangen worden niet streng afgedwongen; niets wordt verwijderd (statusvlag +
    edit_log). Het publiek raakt dit endpoint nooit."""
    conn = get_db()
    if not _mag_leads_lezen(conn):
        conn.close()
        return jsonify({"error": "Alleen reviewer+ of een agent-account werkt de "
                                 "lead-wachtrij bij"}), 403
    lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        conn.close()
        return jsonify({"error": "Lead niet gevonden"}), 404
    data = request.json or {}
    velden, waarden = [], []
    nieuwe_status = data.get("status")
    if nieuwe_status is not None:
        if nieuwe_status not in LEAD_STATUSSEN:
            conn.close()
            return jsonify({"error": f"Status moet een van {LEAD_STATUSSEN} zijn"}), 400
        velden.append("status = ?")
        waarden.append(nieuwe_status)
    if "agent_arg_id" in data:
        aid = data.get("agent_arg_id")
        if aid is not None and not conn.execute(
                "SELECT 1 FROM arguments WHERE id = ?", (aid,)).fetchone():
            conn.close()
            return jsonify({"error": f"Argument {aid} bestaat niet"}), 400
        velden.append("agent_arg_id = ?")
        waarden.append(aid)
    if not velden:
        conn.close()
        return jsonify({"error": "Niets te wijzigen: geef 'status' en/of "
                                 "'agent_arg_id'"}), 400
    conn.execute(f"UPDATE leads SET {', '.join(velden)} WHERE id = ?",
                 waarden + [lead_id])
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('leads', ?, 'updated', ?, ?, ?, ?)
    """, (lead_id, g.user["username"],
          json.dumps({"status": lead["status"], "agent_arg_id": lead["agent_arg_id"]}),
          json.dumps({"status": nieuwe_status if nieuwe_status is not None else lead["status"],
                      "agent_arg_id": data.get("agent_arg_id", lead["agent_arg_id"])}),
          "lead-corroboratie: status/agent_arg_id bijgewerkt"))
    conn.commit()
    rij = dict(conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone())
    conn.close()
    return jsonify(rij)


# ══ Nieuws-pijplijn (Epic 12 "Wie is dit?", eigenaarsbesluit 2026-09-30) ══════════
# De nieuws-aggregator (zusterproject) maakt elke naam in het nieuws klikbaar en toont
# het netwerk uit dit model. Ontbreekt een naam of heeft hij < 3 goedgekeurde verbanden,
# dan zet de nieuws-backend (account 'nieuws-agent') een onderzoeksdoel in de wachtrij
# `nieuws_doelen`; de missie-agent 'nieuws-scout' (missies/nieuws_scout_brief.md) claimt
# en werkt die af via het GEWONE bijdragepad (alles 'voorgesteld'). Daarna mag een
# deterministische, gepoorte service (account 'nieuws-autokeur', reviewer-tier) veilige
# structuurfeiten goedkeuren — een BEWUSTE, geaudite uitzondering op "AI stelt voor, mens
# beslist" (expliciet eigenaarsbesluit 2026-09-30): alleen neutrale structuur-relatietypes
# mét mechanisme en bron-URL, argumenten worden NIET gemerged, eerlijk edit_log,
# kill-switch, dagplafond, intrekken door een maintainer.
#
# Bewijsdoelen (soort 'relatie', nieuws-aggregator Story 14.13): een verband dat lezers
# in het nieuws zien en dat dun onderbouwd is (één bron, een bron die de claim niet
# draagt, niets gecontroleerd), sleutel 'relatie:<id>'. Die doelen claimt alléén de
# missie-agent 'nieuws-bewijs' (missies/nieuws_bewijs_brief.md): bewijs vóór én tegen,
# alles 'voorgesteld' — invloeds-/sourcingclaims blijven mensenwerk, de autokeur raakt
# ze nooit. De nieuws-scout claimt alleen personen en organisaties.

NIEUWS_AGENT = "nieuws-agent"
NIEUWS_SCOUT = "nieuws-scout"
NIEUWS_BEWIJS = "nieuws-bewijs"
NIEUWS_AUTOKEUR = "nieuws-autokeur"
NIEUWS_DOEL_STATUSSEN = ("open", "bezig", "klaar", "niets_gevonden", "overgeslagen",
                         "twijfel", "fout")
NIEUWS_DOEL_ACTIEF = ("open", "bezig")           # de rest = afgerond
NIEUWS_DOEL_SOORTEN = ("persoon", "organisatie", "relatie")
NIEUWS_NAAM_SOORTEN = ("persoon", "organisatie")  # het werk van de nieuws-scout
NIEUWS_RELATIE_SLEUTEL = re.compile(r"relatie:(\d+)")
NIEUWS_DOEL_VERVOLG = ("linkedin",)              # plus null
NIEUWS_RESULTAAT_SLEUTELS = ("entity_ids", "relation_ids", "source_ids", "argument_ids")
NIEUWS_CLAIM_VERLOOP_UUR = 3                     # 'bezig' ouder dan dit telt weer als open
NIEUWS_CONTEXT_MAX_TEKENS = 50000
NIEUWS_PRIVE_CATEGORIEEN = ("prive", "privé", "privepersoon", "privépersoon")


def _nu_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _nieuws_iso(waarde):
    """Normaliseer een ISO-tijd uit een query-param naar lokale 'YYYY-MM-DDTHH:MM:SS'
    (de opslagvorm), zodat tekstvergelijking klopt. Accepteert 'Z'/offsets/microseconden
    en een kale datum. None bij onleesbaar."""
    s = (waarde or "").strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt.isoformat(timespec="seconds")


def _nieuws_doel_dict(rij):
    d = dict(rij)
    for k in ("context", "resultaat"):
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except (TypeError, ValueError):
                pass
    return d


def _nieuws_doel(conn, did):
    rij = conn.execute("SELECT * FROM nieuws_doelen WHERE id = ?", (did,)).fetchone()
    return _nieuws_doel_dict(rij) if rij else None


def _mag_nieuws(conn, account):
    """Dit specifieke machine-account, of een maintainer."""
    return g.user["username"] == account or heeft_rol(conn, g.user, "maintainer")


def _nieuws_werker(soort):
    """Het missie-account dat doelen van deze soort claimt en afwerkt."""
    return NIEUWS_BEWIJS if soort == "relatie" else NIEUWS_SCOUT


def _nieuws_soorten_param(waarde):
    """?soort=a,b → (lijst, fout). Leeg → de namen (persoon, organisatie)."""
    lijst = [x.strip() for x in (waarde or "").split(",") if x.strip()]
    onbekend = [x for x in lijst if x not in NIEUWS_DOEL_SOORTEN]
    if onbekend:
        return None, f"onbekende soort {onbekend}; kies uit {NIEUWS_DOEL_SOORTEN}"
    return lijst, None


def _nieuws_log(conn, did, actie, oud, nieuw, reden):
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('nieuws_doelen', ?, ?, ?, ?, ?, ?)
    """, (did, actie, g.user["username"],
          json.dumps(oud, ensure_ascii=False) if oud is not None else None,
          json.dumps(nieuw, ensure_ascii=False) if nieuw is not None else None, reden))


def _nieuws_tekst(data, veld, maxlen, verplicht=False):
    """(waarde, fout). Lege string → None; te lang of geen string → fout."""
    w = data.get(veld)
    if w is None or (isinstance(w, str) and not w.strip()):
        return (None, f"'{veld}' is verplicht" if verplicht else None)
    if not isinstance(w, str):
        return (None, f"'{veld}' moet tekst zijn")
    w = w.strip()
    if len(w) > maxlen:
        return (None, f"'{veld}' is te lang (max {maxlen} tekens)")
    return (w, None)


@app.route("/api/nieuws/doelen", methods=["POST"])
@require_user()
def nieuws_doelen_upsert():
    """Zet een onderzoeksdoel in de wachtrij (upsert op `sleutel`). Alleen 'nieuws-agent'
    of een maintainer. Nieuw → 201 {doel}. Bestaat en open/bezig → 200 {doel, bijgewerkt}
    (prioriteit = max, naam/rol/context/entity_id bijgewerkt). Afgerond → 409 {error, doel},
    tenzij "opnieuw": true → heropend ('open'), 200. Privépersonen (rol_categorie 'prive')
    worden nooit onderzocht → 400 (eigenaarsbesluit; defense-in-depth naast de triage van
    de nieuws-backend). Een bewijsdoel (soort 'relatie') heeft de sleutel 'relatie:<id>'
    van een bestaande, niet-vervangen relatie; `relation_id` volgt uit die sleutel."""
    data = request.get_json(silent=True) or {}
    conn = get_db()
    if not _mag_nieuws(conn, NIEUWS_AGENT):
        conn.close()
        return jsonify({"error": f"Alleen het account '{NIEUWS_AGENT}' of een maintainer "
                                 "zet doelen in de nieuws-wachtrij"}), 403
    fouten = []
    velden = {}
    for veld, maxlen, verplicht in (("sleutel", 200, True), ("naam", 300, True),
                                    ("rol_categorie", 40, False), ("rol_hint", 300, False)):
        velden[veld], fout = _nieuws_tekst(data, veld, maxlen, verplicht=verplicht)
        if fout:
            fouten.append(fout)
    sleutel, naam = velden["sleutel"], velden["naam"]
    rol_cat, rol_hint = velden["rol_categorie"], velden["rol_hint"]
    soort = data.get("soort")
    if soort is not None and soort not in NIEUWS_DOEL_SOORTEN:
        fouten.append(f"'soort' moet een van {NIEUWS_DOEL_SOORTEN} zijn")
    if rol_cat and rol_cat.lower() in NIEUWS_PRIVE_CATEGORIEEN:
        fouten.append("privépersonen worden nooit onderzocht (eigenaarsbesluit 2026-09-30)")
    context_json = None
    if data.get("context") is not None:
        if not isinstance(data["context"], dict):
            fouten.append("'context' moet een object zijn")
        else:
            context_json = json.dumps(data["context"], ensure_ascii=False)
            if len(context_json) > NIEUWS_CONTEXT_MAX_TEKENS:
                fouten.append(f"'context' is te groot (max {NIEUWS_CONTEXT_MAX_TEKENS} tekens)")
    prioriteit = None
    if data.get("prioriteit") is not None:
        p = data["prioriteit"]
        if isinstance(p, bool) or not isinstance(p, (int, float)):
            fouten.append("'prioriteit' moet een getal zijn")
        else:
            prioriteit = float(p)
    entity_id = data.get("entity_id")
    if entity_id is not None:
        if isinstance(entity_id, bool) or not isinstance(entity_id, int):
            fouten.append("'entity_id' moet een geheel getal of null zijn")
        elif not conn.execute("SELECT 1 FROM entities WHERE id = ?", (entity_id,)).fetchone():
            fouten.append(f"entiteit {entity_id} bestaat niet")
    relation_id = data.get("relation_id")
    if relation_id is not None and (isinstance(relation_id, bool)
                                    or not isinstance(relation_id, int)):
        fouten.append("'relation_id' moet een geheel getal of null zijn")
        relation_id = None
    relatie_sleutel = NIEUWS_RELATIE_SLEUTEL.fullmatch(sleutel or "")
    if relatie_sleutel or soort == "relatie" or relation_id is not None:
        # sleutel 'relatie:<id>', soort 'relatie' en relation_id horen bij elkaar
        if not relatie_sleutel:
            fouten.append("een bewijsdoel (soort 'relatie') heeft de sleutel "
                          "'relatie:<relation_id>'")
        elif soort not in (None, "relatie"):
            fouten.append("de sleutel 'relatie:<id>' hoort bij soort 'relatie'")
        else:
            rid = int(relatie_sleutel.group(1))
            if relation_id is not None and relation_id != rid:
                fouten.append(f"'relation_id' {relation_id} wijkt af van de sleutel")
            relation_id = rid
            rel = conn.execute("SELECT vervangen FROM relations WHERE id = ?",
                               (rid,)).fetchone()
            if rel is None:
                fouten.append(f"relatie {rid} bestaat niet")
            elif rel["vervangen"]:
                fouten.append(f"relatie {rid} is vervangen")
    if fouten:
        conn.close()
        return jsonify({"error": "; ".join(fouten)}), 400

    nu = _nu_iso()
    conn.isolation_level = None      # expliciete transactie: upsert atomair (UNIQUE-race)
    conn.execute("BEGIN IMMEDIATE")
    try:
        rij = conn.execute("SELECT * FROM nieuws_doelen WHERE sleutel = ?",
                           (sleutel,)).fetchone()
        if rij is None:
            if soort is None:
                conn.execute("ROLLBACK")
                conn.close()
                return jsonify({"error": "'soort' is verplicht bij een nieuw doel "
                                         f"(een van {NIEUWS_DOEL_SOORTEN})"}), 400
            cur = conn.execute("""
                INSERT INTO nieuws_doelen (sleutel, naam, soort, rol_categorie, rol_hint,
                    context, prioriteit, entity_id, relation_id, status, aangevraagd_door,
                    pogingen, aangemaakt, bijgewerkt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, 0, ?, ?)
            """, (sleutel, naam, soort, rol_cat, rol_hint, context_json,
                  prioriteit if prioriteit is not None else 0.0, entity_id, relation_id,
                  g.user["username"], nu, nu))
            did = cur.lastrowid
            _nieuws_log(conn, did, "created", None,
                        {"sleutel": sleutel, "naam": naam, "soort": soort, "status": "open"},
                        "nieuws-doel in de wachtrij gezet")
            conn.execute("COMMIT")
            doel = _nieuws_doel(conn, did)
            conn.close()
            return jsonify({"doel": doel}), 201

        heropen = False
        if rij["status"] not in NIEUWS_DOEL_ACTIEF:
            if data.get("opnieuw") is not True:
                conn.execute("ROLLBACK")
                doel = _nieuws_doel_dict(rij)
                conn.close()
                return jsonify({"error": f"Dit doel is al afgerond (status '{rij['status']}'); "
                                         "stuur \"opnieuw\": true om het te heropenen",
                                "doel": doel}), 409
            heropen = True
        sets = ["naam = ?", "bijgewerkt = ?"]
        vals = [naam, nu]
        if soort is not None:
            sets.append("soort = ?"); vals.append(soort)
        if rol_cat is not None:
            sets.append("rol_categorie = ?"); vals.append(rol_cat)
        if rol_hint is not None:
            sets.append("rol_hint = ?"); vals.append(rol_hint)
        if context_json is not None:
            sets.append("context = ?"); vals.append(context_json)
        if prioriteit is not None:
            sets.append("prioriteit = MAX(prioriteit, ?)"); vals.append(prioriteit)
        if "entity_id" in data and entity_id is not None:
            sets.append("entity_id = ?"); vals.append(entity_id)
        if relation_id is not None:
            sets.append("relation_id = ?"); vals.append(relation_id)
        if heropen:
            sets += ["status = 'open'", "geclaimd_door = NULL", "geclaimd_op = NULL"]
        conn.execute(f"UPDATE nieuws_doelen SET {', '.join(sets)} WHERE id = ?",
                     vals + [rij["id"]])
        # Een gewone verversing van een open/bezig doel (elke nieuws-cyclus) logt NIET in
        # edit_log (anders duizenden ruisregels per dag); `bijgewerkt` legt haar vast.
        # Heropenen is een statuswissel en logt wél.
        if heropen:
            _nieuws_log(conn, rij["id"], "updated", {"status": rij["status"]},
                        {"status": "open"}, "nieuws-doel heropend (opnieuw: true)")
        conn.execute("COMMIT")
    except sqlite3.Error:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        conn.close()
        raise
    doel = _nieuws_doel(conn, rij["id"])
    conn.close()
    antwoord = {"doel": doel, "bijgewerkt": True}
    if heropen:
        antwoord["heropend"] = True
    return jsonify(antwoord), 200


@app.route("/api/nieuws/doelen", methods=["GET"])
@require_user()
def nieuws_doelen_lijst():
    """De wachtrij (elk ingelogd account). ?status=a,b &soort=a,b &limit=50 (max 500)
    &bijgewerkt_na=ISO &sleutel=<s>[,<s>…]. Prioriteit aflopend."""
    waar, vals = [], []
    soorten, fout = _nieuws_soorten_param(request.args.get("soort"))
    if fout:
        return jsonify({"error": fout}), 400
    if soorten:
        waar.append(f"soort IN ({','.join('?' * len(soorten))})"); vals += soorten
    status = (request.args.get("status") or "").strip()
    if status:
        lijst = [s.strip() for s in status.split(",") if s.strip()]
        onbekend = [s for s in lijst if s not in NIEUWS_DOEL_STATUSSEN]
        if onbekend:
            return jsonify({"error": f"onbekende status {onbekend}; kies uit "
                                     f"{NIEUWS_DOEL_STATUSSEN}"}), 400
        waar.append(f"status IN ({','.join('?' * len(lijst))})"); vals += lijst
    sleutel = (request.args.get("sleutel") or "").strip()
    if sleutel:
        lijst = [s.strip() for s in sleutel.split(",") if s.strip()]
        waar.append(f"sleutel IN ({','.join('?' * len(lijst))})"); vals += lijst
    if request.args.get("bijgewerkt_na"):
        grens = _nieuws_iso(request.args.get("bijgewerkt_na"))
        if grens is None:
            return jsonify({"error": "'bijgewerkt_na' is geen geldige ISO-tijd"}), 400
        waar.append("bijgewerkt > ?"); vals.append(grens)
    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        return jsonify({"error": "'limit' moet een geheel getal zijn"}), 400
    limit = max(1, min(500, limit))
    conn = get_db()
    rijen = conn.execute(
        "SELECT * FROM nieuws_doelen"
        + (f" WHERE {' AND '.join(waar)}" if waar else "")
        + " ORDER BY prioriteit DESC, aangemaakt ASC, id ASC LIMIT ?", vals + [limit]).fetchall()
    conn.close()
    return jsonify({"doelen": [_nieuws_doel_dict(r) for r in rijen]})


@app.route("/api/nieuws/doelen/<int:did>", methods=["GET"])
@require_user()
def nieuws_doel_get(did):
    conn = get_db()
    doel = _nieuws_doel(conn, did)
    conn.close()
    if doel is None:
        return jsonify({"error": "Doel niet gevonden"}), 404
    return jsonify({"doel": doel})


@app.route("/api/nieuws/doelen/claim_volgende", methods=["POST"])
@require_user()
def nieuws_doelen_claim_volgende():
    """Claim ATOMAIR (één BEGIN IMMEDIATE-transactie) de hoogste open doelen:
    prioriteit aflopend, oudste eerst; een 'bezig'-doel waarvan de claim ouder is dan
    NIEUWS_CLAIM_VERLOOP_UUR telt weer als open (vastgelopen ronde). ?limit=3 (max 10).
    Met ?linkedin=1 (de agent zag dat de snelheidsrem LinkedIn nu toelaat) worden daarna
    ook afgeronde doelen met vervolg='linkedin' geclaimd: die krijgen alleen nog de
    LinkedIn-stap (vervolg blijft 'linkedin' tot de PATCH het op null zet).
    Zonder ?soort claimt dit namen (persoon, organisatie): alleen 'nieuws-scout' of een
    maintainer. ?soort=relatie claimt bewijsdoelen: alleen 'nieuws-bewijs' of een
    maintainer. Eén soort-familie per aanroep."""
    conn = get_db()
    soorten, fout = _nieuws_soorten_param(request.args.get("soort"))
    if fout:
        conn.close()
        return jsonify({"error": fout}), 400
    soorten = soorten or list(NIEUWS_NAAM_SOORTEN)
    werkers = {_nieuws_werker(x) for x in soorten}
    if len(werkers) != 1:
        conn.close()
        return jsonify({"error": "claim namen (persoon, organisatie) en relaties apart"}), 400
    werker = werkers.pop()
    if not _mag_nieuws(conn, werker):
        conn.close()
        return jsonify({"error": f"Alleen het account '{werker}' of een maintainer "
                                 f"claimt deze nieuws-doelen ({', '.join(soorten)})"}), 403
    try:
        limit = int(request.args.get("limit", 3))
    except ValueError:
        conn.close()
        return jsonify({"error": "'limit' moet een geheel getal zijn"}), 400
    limit = max(1, min(10, limit))
    met_linkedin = request.args.get("linkedin") in ("1", "true", "ja")
    nu = datetime.datetime.now()
    nu_iso = nu.isoformat(timespec="seconds")
    verlopen = (nu - datetime.timedelta(hours=NIEUWS_CLAIM_VERLOOP_UUR)).isoformat(
        timespec="seconds")
    conn.isolation_level = None
    conn.execute("BEGIN IMMEDIATE")
    try:
        rijen = conn.execute(f"""
            SELECT id, status FROM nieuws_doelen
            WHERE soort IN ({','.join('?' * len(soorten))})
              AND (status = 'open'
                   OR (status = 'bezig' AND (geclaimd_op IS NULL OR geclaimd_op < ?))
                   OR (? AND status = 'klaar' AND vervolg = 'linkedin'))
            ORDER BY (status = 'klaar'), prioriteit DESC, aangemaakt ASC, id ASC
            LIMIT ?""", (*soorten, verlopen, 1 if met_linkedin else 0, limit)).fetchall()
        for r in rijen:
            conn.execute("""UPDATE nieuws_doelen SET status = 'bezig', geclaimd_door = ?,
                            geclaimd_op = ?, pogingen = pogingen + 1, bijgewerkt = ?
                            WHERE id = ?""", (g.user["username"], nu_iso, nu_iso, r["id"]))
            _nieuws_log(conn, r["id"], "updated", {"status": r["status"]},
                        {"status": "bezig"},
                        "nieuws-doel geclaimd" + (" (verlopen claim overgenomen)"
                                                  if r["status"] == "bezig" else
                                                  " (LinkedIn-vervolg)"
                                                  if r["status"] == "klaar" else ""))
        conn.execute("COMMIT")
    except sqlite3.Error:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        conn.close()
        raise
    doelen = [_nieuws_doel(conn, r["id"]) for r in rijen]
    conn.close()
    return jsonify({"doelen": doelen})


@app.route("/api/nieuws/doelen/<int:did>/claim", methods=["POST"])
@require_user()
def nieuws_doelen_claim(did):
    """Claim één doel: 'open' → 'bezig', anders 409. Het account van de soort
    ('nieuws-scout' voor namen, 'nieuws-bewijs' voor relaties) of een maintainer."""
    conn = get_db()
    nu = _nu_iso()
    conn.isolation_level = None
    conn.execute("BEGIN IMMEDIATE")
    rij = conn.execute("SELECT * FROM nieuws_doelen WHERE id = ?", (did,)).fetchone()
    if rij is None:
        conn.execute("ROLLBACK")
        conn.close()
        return jsonify({"error": "Doel niet gevonden"}), 404
    werker = _nieuws_werker(rij["soort"])
    if not _mag_nieuws(conn, werker):
        conn.execute("ROLLBACK")
        conn.close()
        return jsonify({"error": f"Alleen het account '{werker}' of een maintainer "
                                 "claimt dit nieuws-doel"}), 403
    if rij["status"] != "open":
        conn.execute("ROLLBACK")
        doel = _nieuws_doel_dict(rij)
        conn.close()
        return jsonify({"error": f"Alleen een 'open' doel is te claimen (status "
                                 f"'{rij['status']}')", "doel": doel}), 409
    conn.execute("""UPDATE nieuws_doelen SET status = 'bezig', geclaimd_door = ?,
                    geclaimd_op = ?, pogingen = pogingen + 1, bijgewerkt = ? WHERE id = ?""",
                 (g.user["username"], nu, nu, did))
    _nieuws_log(conn, did, "updated", {"status": "open"}, {"status": "bezig"},
                "nieuws-doel geclaimd")
    conn.execute("COMMIT")
    doel = _nieuws_doel(conn, did)
    conn.close()
    return jsonify({"doel": doel})


@app.route("/api/nieuws/doelen/<int:did>", methods=["PATCH"])
@require_user()
def nieuws_doelen_patch(did):
    """Werk een doel bij: {status?, verslag?, resultaat?, entity_id?, vervolg?}.
    Het account van de soort ('nieuws-scout' / 'nieuws-bewijs') of een maintainer. `resultaat` = object met (een deel van) de vier
    id-lijsten {entity_ids, relation_ids, source_ids, argument_ids}; ontbrekende lijsten
    worden []. Zet je 'open' terug, dan vervalt de claim."""
    data = request.get_json(silent=True) or {}
    conn = get_db()
    rij = conn.execute("SELECT * FROM nieuws_doelen WHERE id = ?", (did,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": "Doel niet gevonden"}), 404
    werker = _nieuws_werker(rij["soort"])
    if not _mag_nieuws(conn, werker):
        conn.close()
        return jsonify({"error": f"Alleen het account '{werker}' of een maintainer "
                                 "werkt dit nieuws-doel bij"}), 403
    toegestaan = {"status", "verslag", "resultaat", "entity_id", "vervolg"}
    onbekend = sorted(set(data) - toegestaan)
    if onbekend:
        conn.close()
        return jsonify({"error": f"onbekende velden {onbekend}; toegestaan: "
                                 f"{sorted(toegestaan)}"}), 400
    if not data:
        conn.close()
        return jsonify({"error": "Niets te wijzigen"}), 400
    sets, vals, fouten = [], [], []
    if "status" in data:
        if data["status"] not in NIEUWS_DOEL_STATUSSEN:
            fouten.append(f"'status' moet een van {NIEUWS_DOEL_STATUSSEN} zijn")
        else:
            sets.append("status = ?"); vals.append(data["status"])
            if data["status"] == "open":
                sets += ["geclaimd_door = NULL", "geclaimd_op = NULL"]
    if "verslag" in data:
        verslag, f = _nieuws_tekst(data, "verslag", 4000)
        if f:
            fouten.append(f)
        else:
            sets.append("verslag = ?"); vals.append(verslag)
    if "vervolg" in data:
        if data["vervolg"] is not None and data["vervolg"] not in NIEUWS_DOEL_VERVOLG:
            fouten.append("'vervolg' moet null of 'linkedin' zijn")
        else:
            sets.append("vervolg = ?"); vals.append(data["vervolg"])
    if "entity_id" in data:
        eid = data["entity_id"]
        if eid is not None and (isinstance(eid, bool) or not isinstance(eid, int)):
            fouten.append("'entity_id' moet een geheel getal of null zijn")
        elif eid is not None and not conn.execute(
                "SELECT 1 FROM entities WHERE id = ?", (eid,)).fetchone():
            fouten.append(f"entiteit {eid} bestaat niet")
        else:
            sets.append("entity_id = ?"); vals.append(eid)
    if "resultaat" in data:
        res = data["resultaat"]
        if res is None:
            sets.append("resultaat = NULL")
        elif not isinstance(res, dict):
            fouten.append("'resultaat' moet een object zijn met "
                          f"{list(NIEUWS_RESULTAAT_SLEUTELS)}")
        else:
            vreemd = sorted(set(res) - set(NIEUWS_RESULTAAT_SLEUTELS))
            if vreemd:
                fouten.append(f"'resultaat' heeft onbekende sleutels {vreemd}")
            schoon = {}
            for k in NIEUWS_RESULTAAT_SLEUTELS:
                lijst = res.get(k, [])
                if not isinstance(lijst, list) or any(
                        isinstance(x, bool) or not isinstance(x, int) for x in lijst):
                    fouten.append(f"'resultaat.{k}' moet een lijst gehele getallen zijn")
                    continue
                schoon[k] = sorted(set(lijst))
            if not fouten:
                sets.append("resultaat = ?"); vals.append(json.dumps(schoon))
    if fouten:
        conn.close()
        return jsonify({"error": "; ".join(fouten)}), 400
    nu = _nu_iso()
    sets.append("bijgewerkt = ?"); vals.append(nu)
    conn.execute(f"UPDATE nieuws_doelen SET {', '.join(sets)} WHERE id = ?", vals + [did])
    oud = {k: rij[k] for k in ("status", "vervolg", "entity_id")}
    nieuw = {k: data[k] for k in ("status", "vervolg", "entity_id") if k in data}
    if "resultaat" in data:
        nieuw["resultaat"] = data["resultaat"]
    _nieuws_log(conn, did, "updated", oud, nieuw, "nieuws-doel bijgewerkt")
    conn.commit()
    doel = _nieuws_doel(conn, did)
    conn.close()
    return jsonify({"doel": doel})


# ── Nieuws-autokeur: automatisch goedkeuren (eigenaarsbesluit 2026-09-30) ──────────
# Deterministisch predikaat (spiegel van auto_merge_toegestaan) + endpoint dat het
# predikaat ZELF checkt (defense-in-depth) en goedkeurt via _modereer_kern, zodat élke
# bestaande moderatiepoort (eigen-werk, orphan, bronplicht, instantiaties, edit_log) ook
# hier geldt. Alleen ENTITEITEN en RELATIES; argumenten worden nooit gemerged — de score
# blijft op de 0,05-vloer tot een mens merget.

NIEUWS_AUTOKEUR_RELATIETYPES = ("personeel", "dienstverband", "bestuurder", "adviseur",
                                "woordvoerder_van", "lidmaatschap", "eigendom",
                                "ambt", "zeggenschap", "controle", "geschenk")
NIEUWS_AUTOKEUR_MOTIVATIE = "auto-keur nieuws-pijplijn (eigenaarsbesluit 2026-09-30)"
NIEUWS_AUTOKEUR_REDEN_PREFIX = "auto-keur nieuws-pijplijn"
NIEUWS_INTREK_REDEN_PREFIX = "intrekken auto-keur nieuws-pijplijn"
NIEUWS_AUTOKEUR_PLAFOND_DEFAULT = 60
NIEUWS_NAAM_DREMPEL = 0.9
NIEUWS_AUTOKEUR_LOG_PATH = DATA_DIR / "nieuws_autokeur_log.jsonl"


def _nieuws_autokeur_plafond():
    try:
        return max(0, int(os.environ.get("PROPAGANDA_NIEUWS_AUTOKEUR_PLAFOND",
                                         NIEUWS_AUTOKEUR_PLAFOND_DEFAULT)))
    except ValueError:
        return NIEUWS_AUTOKEUR_PLAFOND_DEFAULT


def _nieuws_autokeur_vandaag(conn):
    """Aantal automatische goedkeuringen vandaag (lokale kalenderdag), uit edit_log."""
    return conn.execute("""
        SELECT COUNT(*) FROM edit_log
        WHERE action = 'updated' AND table_name IN ('entities', 'relations')
          AND reason LIKE ? AND date(created_at, 'localtime') = date('now', 'localtime')
    """, (NIEUWS_AUTOKEUR_REDEN_PREFIX + "%",)).fetchone()[0]


def _nieuws_klaar_ids(conn):
    """{'entity_ids': set, 'relation_ids': set} uit het resultaat van alle 'klaar'-doelen
    van de nieuws-scout (namen). Bewijsdoelen (soort 'relatie') tellen nooit mee: wat
    'nieuws-bewijs' vindt, blijft mensenwerk."""
    uit = {"entity_ids": set(), "relation_ids": set()}
    for r in conn.execute("SELECT resultaat FROM nieuws_doelen WHERE status = 'klaar' "
                          "AND resultaat IS NOT NULL "
                          "AND soort IN ('persoon', 'organisatie')"):
        try:
            res = json.loads(r["resultaat"])
        except (TypeError, ValueError):
            continue
        if not isinstance(res, dict):
            continue
        for k in uit:
            uit[k].update(x for x in (res.get(k) or []) if isinstance(x, int))
    return uit


def _naam_sleutel(naam):
    """Hoofdletter-, diakriet- en leestekenongevoelige naamvorm."""
    s = unicodedata.normalize("NFKD", naam or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^\w]+", " ", s).split())


def _laatste_goedkeurder(conn, tabel, rid):
    """(changed_by, reason) van de nieuwste edit_log-rij die dit element op
    'goedgekeurd' zette, of (None, None)."""
    for r in conn.execute("""SELECT changed_by, new_value, reason FROM edit_log
                             WHERE table_name = ? AND record_id = ?
                               AND action IN ('updated', 'created')
                             ORDER BY id DESC""", (tabel, rid)):
        try:
            nv = json.loads(r["new_value"] or "{}")
        except (TypeError, ValueError):
            continue
        if isinstance(nv, dict) and nv.get("status") == "goedgekeurd":
            return r["changed_by"], r["reason"]
    return None, None


def _smaad_in_boom(conn, kolom, rid):
    """Draagt een argument in de discussieboom van dit element een smaad_hold?"""
    return conn.execute(f"""
        WITH RECURSIVE boom(id) AS (
            SELECT id FROM arguments WHERE {kolom} = ? AND parent_argument_id IS NULL
            UNION ALL
            SELECT a.id FROM arguments a JOIN boom b ON a.parent_argument_id = b.id
        )
        SELECT COUNT(*) FROM arguments WHERE id IN (SELECT id FROM boom)
          AND COALESCE(smaad_hold, 0) = 1""", (rid,)).fetchone()[0] > 0


def _nieuws_autokeur_basis(conn, tabel, rid, klaar_ids):
    """De INTRINSIEKE voorwaarden van één element (zonder de koppel-voorwaarden tussen
    entiteit en relatie). Lege lijst = in orde."""
    rij = conn.execute(f"SELECT * FROM {tabel} WHERE id = ?", (rid,)).fetchone()
    if rij is None:
        return ["niet gevonden"]
    redenen = []
    if rij["status"] != "voorgesteld":
        redenen.append(f"status is '{rij['status']}', niet 'voorgesteld'")
    if rij["vervangen"]:
        redenen.append("vervangen (M2.6)")
    maker = _creator_van(conn, tabel, rid)
    if maker != NIEUWS_SCOUT:
        redenen.append(f"aangemaakt door '{maker}', niet door '{NIEUWS_SCOUT}'")
    lijst = "entity_ids" if tabel == "entities" else "relation_ids"
    if rid not in klaar_ids[lijst]:
        redenen.append("staat niet in het resultaat van een nieuws-doel met status 'klaar'")
    if conn.execute("SELECT 1 FROM edit_log WHERE table_name = ? AND record_id = ? "
                    "AND reason LIKE ? LIMIT 1",
                    (tabel, rid, NIEUWS_INTREK_REDEN_PREFIX + "%")).fetchone():
        redenen.append("eerder door een maintainer ingetrokken — nooit opnieuw automatisch")
    kolom = "entity_id" if tabel == "entities" else "relation_id"
    if _smaad_in_boom(conn, kolom, rid):
        redenen.append("smaad_hold op een argument (smaad-firewall) — mensenwerk")

    if tabel == "relations":
        if rij["relation_type"] not in NIEUWS_AUTOKEUR_RELATIETYPES:
            redenen.append(f"relatietype '{rij['relation_type']}' valt buiten de neutrale "
                           f"structuurtypes {NIEUWS_AUTOKEUR_RELATIETYPES} — mensenwerk")
        if rij["mechanism_id"] is None:
            redenen.append("geen mechanisme (kandidaat) — niet goedkeurbaar")
        n_steun = conn.execute("""
            SELECT COUNT(*) FROM arguments a
            WHERE a.relation_id = ? AND a.parent_argument_id IS NULL AND NOT a.vervangen
              AND a.stance = 'supporting' AND a.property IS NULL
              AND a.status <> 'verworpen' AND a.contributed_by = ?
              AND EXISTS (SELECT 1 FROM citations c
                          JOIN source_locations sl ON sl.source_id = c.source_id
                          WHERE c.argument_id = a.id AND sl.location_type = 'url'
                            AND TRIM(COALESCE(sl.location, '')) <> '')
        """, (rid, NIEUWS_SCOUT)).fetchone()[0]
        if not n_steun:
            redenen.append(f"geen supporting root-argument van '{NIEUWS_SCOUT}' met een "
                           "citatie naar een bron met URL-vindplaats")
        n_tegen = conn.execute("""
            SELECT COUNT(*) FROM arguments WHERE relation_id = ? AND parent_argument_id IS NULL
              AND NOT vervangen AND stance = 'contradicting' AND status <> 'verworpen'
        """, (rid,)).fetchone()[0]
        if n_tegen:
            redenen.append("er ligt een tegenargument op deze relatie — mensenwerk")
    else:
        if not (rij["type"] or "").strip():
            redenen.append("geen entiteittype")
        if rij["primary_role_id"] is None:
            redenen.append("geen rol-suggestie (primary_role_id)")
        sleutel = _naam_sleutel(rij["name"])
        for ander in conn.execute("""SELECT id, name FROM entities
                                     WHERE status = 'goedgekeurd' AND NOT vervangen
                                       AND id <> ?""", (rid,)):
            if _naam_sleutel(ander["name"]) == sleutel:
                gelijk = 1.0
            elif dedup is not None:
                gelijk = dedup.gelijkenis(rij["name"], ander["name"])
            else:
                gelijk = difflib.SequenceMatcher(None, rij["name"].lower(),
                                                 ander["name"].lower()).ratio()
            if gelijk >= NIEUWS_NAAM_DREMPEL:
                redenen.append(f"lijkt op bestaande entiteit #{ander['id']} "
                               f"'{ander['name']}' (gelijkenis {gelijk:.2f}) — "
                               "mogelijk duplicaat, mensenwerk")
                break
    return redenen


def _eindpunt_ok(conn, eid, klaar_ids, *, behalve=None):
    """Is dit eindpunt goedgekeurd, of in dezelfde ronde automatisch goedkeurbaar?
    Geeft None als ok, anders een reden."""
    if behalve is not None and eid == behalve:
        return None
    e = conn.execute("SELECT status, vervangen FROM entities WHERE id = ?", (eid,)).fetchone()
    if e is None:
        return f"entiteit #{eid} bestaat niet"
    if e["status"] == "goedgekeurd" and not e["vervangen"]:
        return None
    if e["status"] == "voorgesteld":
        sub = _nieuws_autokeur_basis(conn, "entities", eid, klaar_ids)
        if not sub:
            return None
        return (f"entiteit #{eid} is niet goedgekeurd en niet automatisch goedkeurbaar "
                f"({'; '.join(sub)})")
    return f"entiteit #{eid} heeft status '{e['status']}'"


def nieuws_autokeur_toegestaan(conn, tabel, rid, strikt=False):
    """Mag de nieuws-autokeur dit element goedkeuren? → (ok, redenen).

    Gemeenschappelijk: status 'voorgesteld' en niet vervangen; aangemaakt door
    'nieuws-scout'; vermeld in het `resultaat` van een nieuws-doel met status 'klaar';
    nooit eerder door een maintainer ingetrokken; geen smaad_hold in de boom.
    Relaties: type ∈ NIEUWS_AUTOKEUR_RELATIETYPES, mechanism_id gezet, ≥1 supporting
    evidentiële root (niet vervangen/verworpen) van 'nieuws-scout' met een citatie naar
    een bron met URL-vindplaats, geen tegenargument, en beide eindpunten goedgekeurd of
    in dezelfde ronde goedkeurbaar (de service keurt entiteiten eerst).
    Entiteiten: type + rol-suggestie gezet, gekoppeld aan ≥1 relatie die (in dezelfde
    ronde) goedkeurbaar is, en geen bijna-duplicaat van een goedgekeurde entiteitnaam
    (gelijkenis ≥ 0,9 of hoofdletter-/diakriet-ongevoelig gelijk) → anders parkeren.
    ``strikt=True`` (het goedkeur-endpoint zelf): een relatie mag pas als beide eindpunten
    NU al goedgekeurd zijn — zo kan geen relatie vóór haar entiteit de graaf in (geen
    bungelende edge), ook niet bij een verkeerde aanroepvolgorde. De alleen-lezen check
    (GET, droogloop) gebruikt de ronde-brede lezing."""
    if tabel not in ("entities", "relations"):
        return (False, [f"onbekende tabel '{tabel}' (entities | relations)"])
    klaar = _nieuws_klaar_ids(conn)
    redenen = _nieuws_autokeur_basis(conn, tabel, rid, klaar)
    if redenen == ["niet gevonden"]:
        return (False, redenen)
    if tabel == "relations":
        rel = conn.execute("SELECT source_id, target_id FROM relations WHERE id = ?",
                           (rid,)).fetchone()
        for kant, eid in (("bron", rel["source_id"]), ("doel", rel["target_id"])):
            fout = _eindpunt_ok(conn, eid, klaar)
            if fout:
                redenen.append(f"{kant}-eindpunt: {fout}")
            elif strikt and conn.execute("SELECT status FROM entities WHERE id = ?",
                                         (eid,)).fetchone()["status"] != "goedgekeurd":
                redenen.append(f"{kant}-eindpunt #{eid} is nog niet goedgekeurd — volgorde: "
                               "de autokeur keurt eerst de entiteiten goed, dan de relaties")
    else:
        gekoppeld = False
        for r in conn.execute("""SELECT id, source_id, target_id FROM relations
                                 WHERE (source_id = ? OR target_id = ?)
                                   AND status = 'voorgesteld' AND NOT vervangen""",
                              (rid, rid)).fetchall():
            if _nieuws_autokeur_basis(conn, "relations", r["id"], klaar):
                continue
            ander = r["target_id"] if r["source_id"] == rid else r["source_id"]
            if _eindpunt_ok(conn, ander, klaar, behalve=rid) is None:
                gekoppeld = True
                break
        if not gekoppeld:
            redenen.append("niet gekoppeld aan een relatie die (in dezelfde ronde) "
                           "automatisch goedkeurbaar is")
    return (not redenen, redenen)


def _nieuws_autokeur_tabel(tabel):
    return tabel in ("entities", "relations")


@app.route("/api/nieuws/autokeur/<tabel>/<int:rid>", methods=["GET"])
@require_user("reviewer")
def nieuws_autokeur_check(tabel, rid):
    """Alleen-lezen predikaat-check (reviewer): {tabel, id, status, toegestaan, redenen}.
    Voor de droogloop van scripts/nieuws_autokeur_service.py; wijzigt niets en telt niet
    mee in het dagplafond."""
    if not _nieuws_autokeur_tabel(tabel):
        return jsonify({"error": "tabel moet 'entities' of 'relations' zijn"}), 400
    conn = get_db()
    rij = conn.execute(f"SELECT status FROM {tabel} WHERE id = ?", (rid,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": "Niet gevonden"}), 404
    ok, redenen = nieuws_autokeur_toegestaan(conn, tabel, rid)
    conn.close()
    return jsonify({"tabel": tabel, "id": rid, "status": rij["status"],
                    "toegestaan": ok, "redenen": redenen})


@app.route("/api/nieuws/autokeur/<tabel>/<int:rid>", methods=["POST"])
@require_user("reviewer")
def nieuws_autokeur(tabel, rid):
    """Automatisch goedkeuren via de nieuws-pijplijn (reviewer-tier; bedoeld voor het
    machine-account 'nieuws-autokeur'). Kill-switch PROPAGANDA_NIEUWS_AUTOKEUR=0 → 503;
    boven het dagplafond (PROPAGANDA_NIEUWS_AUTOKEUR_PLAFOND, standaard 60) → 429;
    predikaat niet ok → 409 {goedgekeurd: false, redenen}. Anders keurt _modereer_kern
    goed met motivatie 'auto-keur nieuws-pijplijn (eigenaarsbesluit 2026-09-30)' →
    200 {goedgekeurd: true}. Het predikaat wordt hier ALTIJD zelf gecheckt."""
    if os.environ.get("PROPAGANDA_NIEUWS_AUTOKEUR", "1") == "0":
        return jsonify({"goedgekeurd": False,
                        "error": "nieuws-autokeur uitgeschakeld (PROPAGANDA_NIEUWS_AUTOKEUR=0)"}), 503
    if not _nieuws_autokeur_tabel(tabel):
        return jsonify({"error": "tabel moet 'entities' of 'relations' zijn"}), 400
    conn = get_db()
    if conn.execute(f"SELECT 1 FROM {tabel} WHERE id = ?", (rid,)).fetchone() is None:
        conn.close()
        return jsonify({"error": "Niet gevonden"}), 404
    plafond = _nieuws_autokeur_plafond()
    vandaag = _nieuws_autokeur_vandaag(conn)
    if vandaag >= plafond:
        conn.close()
        return jsonify({"goedgekeurd": False, "plafond": plafond, "vandaag": vandaag,
                        "error": f"dagplafond bereikt ({vandaag}/{plafond} automatische "
                                 "goedkeuringen vandaag) — rest blijft voor de mens"}), 429
    ok, redenen = nieuws_autokeur_toegestaan(conn, tabel, rid, strikt=True)
    if not ok:
        conn.close()
        return jsonify({"goedgekeurd": False, "redenen": redenen}), 409
    ok, fout, code, _extra = _modereer_kern(conn, tabel, rid, "goedgekeurd",
                                            g.user["username"], NIEUWS_AUTOKEUR_MOTIVATIE)
    if not ok:
        conn.close()
        return jsonify({"goedgekeurd": False, "redenen": [fout], "kern_http": code}), 409
    conn.commit()
    conn.close()
    return jsonify({"goedgekeurd": True, "tabel": tabel, "id": rid}), 200


# ── Automatische beoordeling: relaties en entiteiten (eigenaarsbesluit 2026-10-06) ──
# De eigenaar beoordeelt niets meer met de hand. Een voorgestelde relatie gaat de graaf in
# zodra haar bewijs onafhankelijk is gecontroleerd: ≥1 GEMERGEDE supporting root met een
# echte citatie (gemerged door de A7-immuunpoort of een mens), geen gemerged tegenargument,
# een mechanisme, beide eindpunten goedgekeurd; raakt ze een persoon, dan alleen als
# neutraal structuurfeit (BEOORDELING_STRUCTUURTYPES). Een entiteit volgt haar relatie:
# type gezet, gekoppeld aan een (goedkeurbare) relatie, geen bijna-duplicaat. Zelfde
# moderatie-kern als een mens (eigen-werk-, orphan- en bronplicht-poort), reviewer-tier
# systeemaccount (merge-service), kill-switch PROPAGANDA_AUTOMATISCHE_BEOORDELING=0,
# dagplafond PROPAGANDA_BEOORDELING_PLAFOND (standaard 200), eerlijk edit_log.
BEOORDELING_MOTIVATIE = ("automatische beoordeling: bewijs onafhankelijk gecontroleerd "
                         "(eigenaarsbesluit 2026-10-06)")
BEOORDELING_REDEN_PREFIX = "automatische beoordeling"
BEOORDELING_PLAFOND_DEFAULT = 200
# Uitbreiding C (2026-10-07): registerfeiten (tools/registers/, gecontroleerd door de
# deterministische scripts/registercheck.py) hebben een eigen dagplafond, zodat een import van
# duizenden ambten het gewone plafond niet opsoupeert. Hun reden begint óók met
# BEOORDELING_REDEN_PREFIX, zodat intrekken/heropenen ze blijven herkennen.
REGISTER_REDEN_PREFIX = "automatische beoordeling (register)"
REGISTER_MOTIVATIE = ("automatische beoordeling (register): registerfeit deterministisch "
                      "gecontroleerd tegen de bewaarde registeruitgave (eigenaarsbesluit 2026-10-07)")
REGISTER_PLAFOND_DEFAULT = 5000
REGISTER_CLUSTER_PREFIX = "register:"   # sources.cluster_key van een registeruitgave


def _register_plafond():
    try:
        return max(0, int(os.environ.get("PROPAGANDA_REGISTER_PLAFOND",
                                         REGISTER_PLAFOND_DEFAULT)))
    except ValueError:
        return REGISTER_PLAFOND_DEFAULT


def _alleen_registercitaties(conn, arg_id):
    """True als het argument ≥1 citatie heeft en ALLE citaties letterlijke registerregels
    zijn (methode officieel_register_scrape, met quote, uit een registeruitgave)."""
    rij = conn.execute("""
        SELECT COUNT(*) AS n,
               SUM(CASE WHEN c.methode = 'officieel_register_scrape'
                         AND TRIM(COALESCE(c.quote, '')) <> ''
                         AND s.cluster_key LIKE ? THEN 1 ELSE 0 END) AS reg
        FROM citations c JOIN sources s ON s.id = c.source_id
        WHERE c.argument_id = ?""", (REGISTER_CLUSTER_PREFIX + "%", arg_id)).fetchone()
    return bool(rij["n"]) and rij["n"] == rij["reg"]


def _registerelement(conn, tabel, rid):
    """Is dit element een registerfeit (eigen plafond, eigen motivatie)? Een entiteit als
    ze een externe id heeft; een relatie als al haar levende steunende roots alleen
    registercitaties dragen."""
    if tabel == "entities":
        return conn.execute("SELECT 1 FROM externe_ids WHERE entity_id = ? LIMIT 1",
                            (rid,)).fetchone() is not None
    roots = [r["id"] for r in conn.execute("""
        SELECT id FROM arguments WHERE relation_id = ? AND parent_argument_id IS NULL
          AND stance = 'supporting' AND NOT vervangen AND status <> 'verworpen'""", (rid,))]
    return bool(roots) and all(_alleen_registercitaties(conn, a) for a in roots)


def _beoordeling_plafond():
    try:
        return max(0, int(os.environ.get("PROPAGANDA_BEOORDELING_PLAFOND",
                                         BEOORDELING_PLAFOND_DEFAULT)))
    except ValueError:
        return BEOORDELING_PLAFOND_DEFAULT


def _beoordeling_vandaag(conn, register=False):
    """Aantal automatische goedkeuringen van de beoordeling vandaag (lokale kalenderdag).
    ``register=True`` telt alleen registerfeiten (eigen plafond); anders alles behalve die."""
    if register:
        return conn.execute("""
            SELECT COUNT(*) FROM edit_log
            WHERE action = 'updated' AND table_name IN ('entities', 'relations')
              AND reason LIKE ? AND date(created_at, 'localtime') = date('now', 'localtime')
        """, (REGISTER_REDEN_PREFIX + "%",)).fetchone()[0]
    return conn.execute("""
        SELECT COUNT(*) FROM edit_log
        WHERE action = 'updated' AND table_name IN ('entities', 'relations')
          AND reason LIKE ? AND reason NOT LIKE ?
          AND date(created_at, 'localtime') = date('now', 'localtime')
    """, (BEOORDELING_REDEN_PREFIX + "%", REGISTER_REDEN_PREFIX + "%")).fetchone()[0]


def _beoordeling_basis(conn, tabel, rid):
    """Gedeelde voorwaarden: voorgesteld, niet vervangen, nooit ingetrokken, geen smaad."""
    rij = conn.execute(f"SELECT * FROM {tabel} WHERE id = ?", (rid,)).fetchone()
    if rij is None:
        return None, ["niet gevonden"]
    redenen = []
    if rij["status"] != "voorgesteld":
        redenen.append(f"status is '{rij['status']}', niet 'voorgesteld'")
    if rij["vervangen"]:
        redenen.append("vervangen (M2.6)")
    if conn.execute("SELECT 1 FROM edit_log WHERE table_name = ? AND record_id = ? "
                    "AND reason LIKE 'intrekken%' LIMIT 1", (tabel, rid)).fetchone():
        redenen.append("eerder door een maintainer ingetrokken — nooit opnieuw automatisch")
    kolom = "entity_id" if tabel == "entities" else "relation_id"
    if _smaad_in_boom(conn, kolom, rid):
        redenen.append("smaad_hold op een argument (smaad-firewall)")
    return rij, redenen


def _bewijs_relatie_redenen(conn, rid):
    """De eigen voorwaarden van een relatie (zonder de eindpunten). Lege lijst = in orde."""
    rij, redenen = _beoordeling_basis(conn, "relations", rid)
    if rij is None:
        return redenen
    if rij["mechanism_id"] is None:
        redenen.append("geen mechanisme (kandidaat) — niet goedkeurbaar")
    raakt_persoon = conn.execute(
        "SELECT COUNT(*) FROM entities WHERE id IN (?, ?) AND type = 'persoon'",
        (rij["source_id"], rij["target_id"])).fetchone()[0]
    if raakt_persoon and rij["relation_type"] not in BEOORDELING_STRUCTUURTYPES:
        # Smaad-firewall door agents (2026-10-06): alleen met bewijs dat de smaadtoets doorstond
        feitelijk = [a for a in conn.execute("""
            SELECT a.id, a.contributed_by FROM arguments a
            WHERE a.relation_id = ? AND a.parent_argument_id IS NULL AND NOT a.vervangen
              AND a.stance = 'supporting' AND a.status IN ('geverifieerd', 'ongecontroleerd')
              AND COALESCE(a.smaad_hold, 0) = 0""", (rid,))
            if (_smaadtoets(conn, a["id"], a["contributed_by"]) or {"verdict": None})["verdict"]
            == "feitelijk"]
        if not feitelijk:
            redenen.append("raakt een persoon: nog geen gemerged argument dat de smaadtoets "
                           "doorstond (feitelijk)")
    n_steun = conn.execute("""
        SELECT COUNT(*) FROM arguments a
        WHERE a.relation_id = ? AND a.parent_argument_id IS NULL AND NOT a.vervangen
          AND a.stance = 'supporting' AND COALESCE(a.property, 'existence') = 'existence'
          AND a.status IN ('geverifieerd', 'ongecontroleerd')
          AND EXISTS (SELECT 1 FROM citations c WHERE c.argument_id = a.id AND (
                TRIM(COALESCE(c.quote, '')) <> ''
                OR EXISTS (SELECT 1 FROM source_locations sl WHERE sl.source_id = c.source_id)))
    """, (rid,)).fetchone()[0]
    if not n_steun:
        redenen.append("nog geen gemerged supporting argument met een echte bron")
    n_tegen = conn.execute("""
        SELECT COUNT(*) FROM arguments WHERE relation_id = ? AND parent_argument_id IS NULL
          AND NOT vervangen AND stance = 'contradicting'
          AND status NOT IN ('voorgesteld', 'verworpen')
    """, (rid,)).fetchone()[0]
    if n_tegen:
        redenen.append("er ligt een gemerged tegenargument op deze relatie")
    return redenen


def _bewijs_entiteit_redenen(conn, eid):
    rij, redenen = _beoordeling_basis(conn, "entities", eid)
    if rij is None:
        return redenen
    if not (rij["type"] or "").strip():
        redenen.append("geen entiteittype")
    sleutel = _naam_sleutel(rij["name"])
    # Uitbreiding C: een entiteit met een externe id (registerpijplijn) is uniek door die id;
    # naamgelijkenis zegt dan niets ("J. de Vries (wethouder Utrecht)" ≠ "Jack de Vries").
    # Alleen een exact gelijke naamvorm parkeert haar nog (dan had de import moeten koppelen).
    met_id = conn.execute("SELECT 1 FROM externe_ids WHERE entity_id = ? LIMIT 1",
                          (eid,)).fetchone() is not None
    for ander in conn.execute("""SELECT id, name FROM entities
                                 WHERE status = 'goedgekeurd' AND NOT vervangen AND id <> ?""",
                              (eid,)):
        if met_id:
            if _naam_sleutel(ander["name"]) == sleutel:
                redenen.append(f"zelfde naam als bestaande entiteit #{ander['id']} "
                               f"'{ander['name']}' — koppelen in plaats van dupliceren")
                break
            continue
        if _naam_sleutel(ander["name"]) == sleutel:
            gelijk = 1.0
        elif dedup is not None:
            gelijk = dedup.gelijkenis(rij["name"], ander["name"])
        else:
            gelijk = difflib.SequenceMatcher(None, rij["name"].lower(),
                                             ander["name"].lower()).ratio()
        if gelijk >= NIEUWS_NAAM_DREMPEL:
            redenen.append(f"lijkt op bestaande entiteit #{ander['id']} '{ander['name']}' "
                           f"(gelijkenis {gelijk:.2f}) — mogelijk duplicaat")
            break
    gekoppeld = False
    for r in conn.execute("""SELECT id, status FROM relations
                             WHERE (source_id = ? OR target_id = ?) AND NOT vervangen
                               AND status IN ('voorgesteld', 'goedgekeurd')""", (eid, eid)):
        if r["status"] == "goedgekeurd" or not _bewijs_relatie_redenen(conn, r["id"]):
            gekoppeld = True
            break
    if not gekoppeld:
        redenen.append("niet gekoppeld aan een goedgekeurde of goedkeurbare relatie")
    return redenen


def bewijs_autokeur_toegestaan(conn, tabel, rid, strikt=False):
    """Mag de automatische beoordeling dit element goedkeuren? → (ok, redenen).
    ``strikt=True`` (het goedkeur-endpoint): een relatie pas als beide eindpunten NU al
    goedgekeurd zijn (de service keurt eerst entiteiten, dan relaties)."""
    if tabel not in ("entities", "relations"):
        return (False, [f"onbekende tabel '{tabel}' (entities | relations)"])
    if tabel == "entities":
        redenen = _bewijs_entiteit_redenen(conn, rid)
        return (not redenen, redenen)
    redenen = _bewijs_relatie_redenen(conn, rid)
    if redenen == ["niet gevonden"]:
        return (False, redenen)
    rel = conn.execute("SELECT source_id, target_id FROM relations WHERE id = ?",
                       (rid,)).fetchone()
    for kant, eid in (("bron", rel["source_id"]), ("doel", rel["target_id"])):
        e = conn.execute("SELECT status, vervangen FROM entities WHERE id = ?",
                         (eid,)).fetchone()
        if e is None:
            redenen.append(f"{kant}-eindpunt #{eid} bestaat niet")
        elif e["status"] == "goedgekeurd" and not e["vervangen"]:
            continue
        elif strikt:
            redenen.append(f"{kant}-eindpunt #{eid} is nog niet goedgekeurd")
        elif e["status"] != "voorgesteld" or _bewijs_entiteit_redenen(conn, eid):
            redenen.append(f"{kant}-eindpunt #{eid} is niet (automatisch) goedkeurbaar")
    return (not redenen, redenen)


@app.route("/api/beoordeling/autokeur/<tabel>/<int:rid>", methods=["GET"])
@require_user("reviewer")
def beoordeling_autokeur_check(tabel, rid):
    """Alleen-lezen predikaat-check (reviewer) voor de droogloop van
    scripts/automatische_beoordeling.py: {tabel, id, status, toegestaan, redenen}."""
    if tabel not in ("entities", "relations"):
        return jsonify({"error": "tabel moet 'entities' of 'relations' zijn"}), 400
    conn = get_db()
    rij = conn.execute(f"SELECT status FROM {tabel} WHERE id = ?", (rid,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": "Niet gevonden"}), 404
    ok, redenen = bewijs_autokeur_toegestaan(conn, tabel, rid)
    conn.close()
    return jsonify({"tabel": tabel, "id": rid, "status": rij["status"],
                    "toegestaan": ok, "redenen": redenen})


@app.route("/api/beoordeling/autokeur/<tabel>/<int:rid>", methods=["POST"])
@require_user("reviewer")
def beoordeling_autokeur(tabel, rid):
    """Goedkeuren door de automatische beoordeling (reviewer-tier; bedoeld voor het
    systeemaccount 'merge-service'). Kill-switch PROPAGANDA_AUTOMATISCHE_BEOORDELING=0 →
    503; boven het dagplafond → 429; predikaat niet ok → 409. Het predikaat wordt hier
    ALTIJD zelf gecheckt (strikt)."""
    if os.environ.get("PROPAGANDA_AUTOMATISCHE_BEOORDELING", "1") == "0":
        return jsonify({"goedgekeurd": False, "error": "automatische beoordeling uitgeschakeld "
                        "(PROPAGANDA_AUTOMATISCHE_BEOORDELING=0)"}), 503
    if tabel not in ("entities", "relations"):
        return jsonify({"error": "tabel moet 'entities' of 'relations' zijn"}), 400
    conn = get_db()
    if conn.execute(f"SELECT 1 FROM {tabel} WHERE id = ?", (rid,)).fetchone() is None:
        conn.close()
        return jsonify({"error": "Niet gevonden"}), 404
    register = _registerelement(conn, tabel, rid)
    soort = "register" if register else "gewoon"
    if register:
        plafond, vandaag = _register_plafond(), _beoordeling_vandaag(conn, register=True)
    else:
        plafond, vandaag = _beoordeling_plafond(), _beoordeling_vandaag(conn)
    if vandaag >= plafond:
        conn.close()
        return jsonify({"goedgekeurd": False, "plafond": plafond, "vandaag": vandaag,
                        "soort": soort,
                        "error": f"dagplafond ({soort}) bereikt ({vandaag}/{plafond})"}), 429
    ok, redenen = bewijs_autokeur_toegestaan(conn, tabel, rid, strikt=True)
    if not ok:
        conn.close()
        return jsonify({"goedgekeurd": False, "redenen": redenen}), 409
    ok, fout, code, _extra = _modereer_kern(
        conn, tabel, rid, "goedgekeurd", g.user["username"],
        REGISTER_MOTIVATIE if register else BEOORDELING_MOTIVATIE)
    if not ok:
        conn.close()
        return jsonify({"goedgekeurd": False, "redenen": [fout], "kern_http": code}), 409
    conn.commit()
    conn.close()
    return jsonify({"goedgekeurd": True, "tabel": tabel, "id": rid}), 200


# ── Automatische verificatie en heropenen (eigenaarsbesluit 2026-10-06: agents doen alles) ──
# Wat al gemerged is maar nooit gecontroleerd ('ongecontroleerd', of 'bronvermelding_nodig'
# met inmiddels een echte bron), krijgt zijn status van het onafhankelijke A1-oordeel
# (bronchecker of verificatie-agent, nooit de auteur): draagt de bron de bewering, dan
# 'geverifieerd' — wat een mens-reviewer deed (citaties gecontroleerd en bevestigd); draagt
# de bron haar aantoonbaar niet ('klopt-niet'), dan 'bronvermelding_nodig' en zoekt de
# bronzoeker een betere bron. Een statusbesluit van een mens wordt nooit overschreven: wat
# een maintainer terugzet, blijft staan. En een afwijzing van de automatische beoordeling
# zelf gaat terug naar 'voorgesteld' zodra de bron daarna alsnog onafhankelijk bevestigd is
# (de bronchecker herzag zich). Reviewer-tier systeemaccount (merge-service), kill-switch
# PROPAGANDA_AUTOMATISCHE_BEOORDELING=0, dagplafond PROPAGANDA_VERIFICATIE_PLAFOND
# (standaard 2000), eerlijk edit_log (reden 'automatische beoordeling: verificatie…' /
# '…: heropend…').
VERIFICATIE_REDEN_PREFIX = BEOORDELING_REDEN_PREFIX + ": verificatie"
HEROPEN_REDEN_PREFIX = BEOORDELING_REDEN_PREFIX + ": heropend"
VERIFICATIE_PLAFOND_DEFAULT = 2000


def _verificatie_plafond():
    try:
        return max(0, int(os.environ.get("PROPAGANDA_VERIFICATIE_PLAFOND",
                                         VERIFICATIE_PLAFOND_DEFAULT)))
    except ValueError:
        return VERIFICATIE_PLAFOND_DEFAULT


def _verificatie_vandaag(conn):
    """Statusbesluiten van de automatische verificatie vandaag (lokale kalenderdag)."""
    return conn.execute("""
        SELECT COUNT(*) FROM edit_log
        WHERE table_name = 'arguments' AND reason LIKE ?
          AND date(created_at, 'localtime') = date('now', 'localtime')
    """, (VERIFICATIE_REDEN_PREFIX + "%",)).fetchone()[0]


def _nieuwste_a1(conn, arg_id):
    return conn.execute("""
        SELECT verdict, door, detail, created_at FROM immuun_oordelen
        WHERE argument_id = ? AND fase = 'herverificatie'
        ORDER BY created_at DESC, id DESC LIMIT 1""", (arg_id,)).fetchone()


def _a1_detail(a1):
    return (a1["detail"] or "").replace("[bronchecker v2] ", "").strip()[:400]


def verificatie_besluit(conn, arg_id):
    """Welke status geeft de automatische verificatie dit gemergede argument?
    → (nieuwe_status | None, redenen waarom niet, motivatie)."""
    arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if arg is None:
        return None, ["niet gevonden"], None
    redenen = []
    if arg["status"] not in ("ongecontroleerd", "bronvermelding_nodig"):
        redenen.append(f"status is '{arg['status']}' (alleen nooit gecontroleerd werk)")
    if arg["vervangen"]:
        redenen.append("vervangen")
    if arg["smaad_hold"]:
        redenen.append("smaad_hold op dit argument (smaad-firewall)")
    # Sinds "agents doen alles" (2026-10-06) elk soort argument: evidentieel, duiding,
    # aspect, theorie of reactie — de A1 zegt of de bron het draagt
    mens = conn.execute("""
        SELECT l.changed_by FROM edit_log l JOIN users u ON u.username = l.changed_by
        WHERE l.table_name = 'arguments' AND l.record_id = ?
          AND l.action IN ('verified', 'disputed') AND u.kind = 'mens'
        ORDER BY l.id DESC LIMIT 1""", (arg_id,)).fetchone()
    if mens:
        redenen.append(f"een mens ({mens['changed_by']}) besliste al over de status — blijft staan")
    a1 = _nieuwste_a1(conn, arg_id)
    if a1 is None:
        redenen.append("A1: nog geen bron-herverificatie")
    elif a1["door"] == arg["contributed_by"]:
        redenen.append("A1: oordeel van de auteur zelf (niet onafhankelijk)")
    if redenen:
        return None, redenen, None
    if a1["verdict"] == "klopt":
        # Een ondergraving (bezwaar tegen de bron van haar parent) leunt op die bron: de A1
        # toetste het bezwaar daartegen, dus telt de citatiepoort ook de citaties van de parent
        bezwaar = arg["parent_argument_id"] is not None and arg["stance"] == "contradicting"
        n_echt = conn.execute("""
            SELECT COUNT(*) FROM citations c WHERE c.argument_id IN (?, ?) AND (
                (c.quote IS NOT NULL AND TRIM(c.quote) <> '')
                OR EXISTS (SELECT 1 FROM source_locations sl WHERE sl.source_id = c.source_id))
            """, (arg_id, arg["parent_argument_id"] if bezwaar else arg_id)).fetchone()[0]
        if not n_echt:
            return None, ["citatiepoort: geen echte bron (quote óf vindplaats)"], None
        return ("geverifieerd", [], f"{VERIFICATIE_REDEN_PREFIX}: de bron draagt de bewering "
                f"(onafhankelijk A1-oordeel van {a1['door']}: {_a1_detail(a1)})")
    if a1["verdict"] == "klopt-niet" and arg["status"] == "ongecontroleerd":
        return ("bronvermelding_nodig", [], f"{VERIFICATIE_REDEN_PREFIX}: de bron draagt de "
                f"bewering niet (A1-oordeel van {a1['door']}: {_a1_detail(a1)}); de bronzoeker "
                "zoekt een betere bron")
    return None, [f"A1: nieuwste oordeel is '{a1['verdict']}' — geen statuswijziging"], None


def heropen_besluit(conn, arg_id):
    """Mag de automatische beoordeling haar EIGEN afwijzing terugdraaien? Alleen als de
    laatste afwijzing van haar kwam en een onafhankelijk A1-oordeel ná die afwijzing zegt dat
    de bron de bewering draagt. → (ok, redenen waarom niet, motivatie)."""
    arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if arg is None:
        return False, ["niet gevonden"], None
    redenen = []
    if arg["status"] != "verworpen":
        redenen.append(f"status is '{arg['status']}', niet 'verworpen'")
    if arg["vervangen"]:
        redenen.append("vervangen")
    if arg["smaad_hold"]:
        redenen.append("smaad_hold op dit argument (smaad-firewall)")
    afwijzing = conn.execute("""
        SELECT reason, created_at FROM edit_log
        WHERE table_name = 'arguments' AND record_id = ? AND action = 'disputed'
          AND new_value LIKE '%verworpen%' ORDER BY id DESC LIMIT 1""", (arg_id,)).fetchone()
    if afwijzing is None or not (afwijzing["reason"] or "").startswith(BEOORDELING_REDEN_PREFIX):
        redenen.append("niet verworpen door de automatische beoordeling — blijft staan")
    a1 = _nieuwste_a1(conn, arg_id)
    toets = _smaadtoets(conn, arg_id, arg["contributed_by"])
    na = str(afwijzing["created_at"]) if afwijzing is not None else ""
    # Nieuw sinds de afwijzing: een bevestiging van de bron, of (bij een persoonsclaim die op
    # de oude smaad-firewall strandde) een smaadtoets 'feitelijk'
    toets_nieuw = (toets is not None and toets["verdict"] == "feitelijk"
                   and str(toets["created_at"]) > na)
    if a1 is None or a1["verdict"] != "klopt":
        redenen.append("A1: geen bevestiging dat de bron de bewering draagt")
    elif a1["door"] == arg["contributed_by"]:
        redenen.append("A1: oordeel van de auteur zelf (niet onafhankelijk)")
    elif afwijzing is not None and str(a1["created_at"]) <= na and not toets_nieuw:
        redenen.append("A1: geen nieuw oordeel sinds de afwijzing")
    if redenen:
        return False, redenen, None
    waarom = (f"na de afwijzing bevond {toets['door']} de claim feitelijk"
              if toets_nieuw and str(a1["created_at"]) <= na
              else f"na de afwijzing bevestigt {a1['door']} de bron ({_a1_detail(a1)})")
    return True, [], f"{HEROPEN_REDEN_PREFIX} (verworpen → voorgesteld): {waarom}"


@app.route("/api/beoordeling/verificatie/<int:arg_id>", methods=["GET"])
@require_user("reviewer")
def beoordeling_verificatie_check(arg_id):
    """Alleen-lezen (droogloop): {id, status, nieuwe_status, redenen, motivatie}."""
    conn = get_db()
    rij = conn.execute("SELECT status FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    nieuw, redenen, motivatie = verificatie_besluit(conn, arg_id)
    conn.close()
    return jsonify({"id": arg_id, "status": rij["status"], "nieuwe_status": nieuw,
                    "redenen": redenen, "motivatie": motivatie})


@app.route("/api/beoordeling/verificatie/<int:arg_id>", methods=["POST"])
@require_user("reviewer")
def beoordeling_verificatie(arg_id):
    """Automatische verificatie van een gemerged argument (merge-service). Het besluit
    wordt hier ALTIJD zelf genomen. Kill-switch → 503, dagplafond → 429, niets te
    besluiten → 409 + redenen."""
    if os.environ.get("PROPAGANDA_AUTOMATISCHE_BEOORDELING", "1") == "0":
        return jsonify({"gewijzigd": False, "error": "automatische beoordeling uitgeschakeld "
                        "(PROPAGANDA_AUTOMATISCHE_BEOORDELING=0)"}), 503
    conn = get_db()
    oud = conn.execute("SELECT status FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if oud is None:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    plafond, vandaag = _verificatie_plafond(), _verificatie_vandaag(conn)
    if vandaag >= plafond:
        conn.close()
        return jsonify({"gewijzigd": False, "plafond": plafond, "vandaag": vandaag,
                        "error": f"dagplafond bereikt ({vandaag}/{plafond})"}), 429
    nieuw, redenen, motivatie = verificatie_besluit(conn, arg_id)
    if nieuw is None:
        conn.close()
        return jsonify({"gewijzigd": False, "redenen": redenen}), 409
    if nieuw == "geverifieerd":
        conn.execute("UPDATE arguments SET status = ?, self_merged = 0 WHERE id = ?",
                     (nieuw, arg_id))
    else:
        conn.execute("UPDATE arguments SET status = ? WHERE id = ?", (nieuw, arg_id))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('arguments', ?, ?, ?, ?, ?, ?)
    """, (arg_id, "verified" if nieuw == "geverifieerd" else "disputed", g.user["username"],
          json.dumps({"status": oud["status"]}), json.dumps({"status": nieuw}), motivatie))
    conn.commit()
    conn.close()
    return jsonify({"gewijzigd": True, "id": arg_id, "status": nieuw}), 200


@app.route("/api/beoordeling/heropenen/<int:arg_id>", methods=["POST"])
@require_user("reviewer")
def beoordeling_heropenen(arg_id):
    """De automatische beoordeling draait een eigen afwijzing terug (verworpen →
    voorgesteld) als de bron daarna onafhankelijk bevestigd is; de immuunpoort (A7) beslist
    daarna opnieuw. Kill-switch → 503, niet toegestaan → 409 + redenen."""
    if os.environ.get("PROPAGANDA_AUTOMATISCHE_BEOORDELING", "1") == "0":
        return jsonify({"heropend": False, "error": "automatische beoordeling uitgeschakeld "
                        "(PROPAGANDA_AUTOMATISCHE_BEOORDELING=0)"}), 503
    conn = get_db()
    if conn.execute("SELECT 1 FROM arguments WHERE id = ?", (arg_id,)).fetchone() is None:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    ok, redenen, motivatie = heropen_besluit(conn, arg_id)
    if not ok:
        conn.close()
        return jsonify({"heropend": False, "redenen": redenen}), 409
    conn.execute("UPDATE arguments SET status = 'voorgesteld' WHERE id = ?", (arg_id,))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('arguments', ?, 'updated', ?, ?, ?, ?)
    """, (arg_id, g.user["username"], json.dumps({"status": "verworpen"}),
          json.dumps({"status": "voorgesteld"}), motivatie))
    conn.commit()
    conn.close()
    return jsonify({"heropend": True, "id": arg_id, "status": "voorgesteld"}), 200


# ── Voorrang uit het nieuws (2026-10-06) ──
# De nieuws-app meldt welke verbanden lezers onder "Wie zit erachter?" te zien krijgen. Die
# gaan voor bij de automatische controle (bronchecker) en de bronzoeker. Procesdata: telt
# nergens in de score en verandert niets aan het model.
NIEUWS_VOORRANG_MAX = 200


@app.route("/api/nieuws/voorrang", methods=["POST"])
@require_user()
def nieuws_voorrang():
    """{relation_ids: [...]} (max 200; alleen 'nieuws-agent' of een maintainer). Bestaande,
    niet-vervangen relaties krijgen voorrang (gevraagd_op = nu, aantal + 1); de rest wordt
    genegeerd. → {bijgewerkt}."""
    data = request.get_json(silent=True) or {}
    ids = data.get("relation_ids")
    if (not isinstance(ids, list) or len(ids) > NIEUWS_VOORRANG_MAX
            or any(isinstance(i, bool) or not isinstance(i, int) or i <= 0 for i in ids)):
        return jsonify({"error": f"'relation_ids' moet een lijst van hooguit "
                                 f"{NIEUWS_VOORRANG_MAX} positieve gehele getallen zijn"}), 400
    conn = get_db()
    if not _mag_nieuws(conn, NIEUWS_AGENT):
        conn.close()
        return jsonify({"error": f"Alleen het account '{NIEUWS_AGENT}' of een maintainer "
                                 "geeft voorrang uit het nieuws door"}), 403
    nu = _nu_iso()
    bijgewerkt = 0
    for rid in sorted(set(ids)):
        if not conn.execute("SELECT 1 FROM relations WHERE id = ? AND NOT vervangen",
                            (rid,)).fetchone():
            continue
        conn.execute("""
            INSERT INTO nieuws_voorrang (relation_id, gevraagd_op, aantal) VALUES (?, ?, 1)
            ON CONFLICT (relation_id) DO UPDATE SET gevraagd_op = excluded.gevraagd_op,
                                                    aantal = nieuws_voorrang.aantal + 1
        """, (rid, nu))
        bijgewerkt += 1
    conn.commit()
    conn.close()
    return jsonify({"bijgewerkt": bijgewerkt})


# ── Smaadtoets (eigenaarsbesluit 2026-10-06: "laat de smaad-firewall checken of het feitelijk
# is; als het niet feitelijk is koppel het terug, anders is het geen smaad") ──
# Een agent (account 'smaadtoets', nooit de auteur) toetst een claim die een natuurlijk persoon
# raakt: (1) een feit, geen mening of waardeoordeel als feit; (2) gedragen door de bron, niet
# verder dan de bron (geen overdrijving, insinuatie of conclusie die de bron niet trekt); (3)
# over de publieke rol, niet het privéleven. 'feitelijk' → de gewone poorten; 'niet_feitelijk'
# → teruggekoppeld (de opruimstap verwerpt met de reden en, waar mogelijk, een feitelijke
# formulering). Procesmetadata in `smaad_toetsen`; telt nergens in de score.
SMAADTOETS_VERDICTS = ("feitelijk", "niet_feitelijk")


def _smaadtoets(conn, arg_id, auteur):
    """Nieuwste smaadtoets van een ander account dan de auteur, of None."""
    try:
        return conn.execute("""
            SELECT verdict, reden, herformulering, door, created_at FROM smaad_toetsen
            WHERE argument_id = ? AND COALESCE(door, '') <> COALESCE(?, '')
            ORDER BY created_at DESC, id DESC LIMIT 1""", (arg_id, auteur)).fetchone()
    except sqlite3.OperationalError:  # database van vóór de smaadtoets
        return None


@app.route("/api/arguments/<int:arg_id>/smaadtoets", methods=["POST"])
@require_user()
def smaadtoets(arg_id):
    """Smaadtoets door een ander account dan de auteur: {verdict: feitelijk|niet_feitelijk,
    reden, herformulering?}. Eén oordeel per account; met "herzien": true werkt het account
    zijn eigen oordeel bij (nooit een tweede stem). 403 voor de auteur."""
    data = request.get_json(silent=True) or {}
    verdict = data.get("verdict")
    if verdict not in SMAADTOETS_VERDICTS:
        return jsonify({"error": "verdict moet 'feitelijk' of 'niet_feitelijk' zijn"}), 400
    reden = (data.get("reden") or "").strip()[:1500]
    if not reden:
        return jsonify({"error": "een smaadtoets vergt een reden"}), 400
    herformulering = (data.get("herformulering") or "").strip()[:1000] or None
    conn = get_db()
    arg = conn.execute("SELECT id, contributed_by FROM arguments WHERE id = ?",
                       (arg_id,)).fetchone()
    if arg is None:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    if arg["contributed_by"] == g.user["username"]:
        conn.close()
        return jsonify({"error": "De auteur toetst zijn eigen claim niet"}), 403
    oud = conn.execute("SELECT id, verdict FROM smaad_toetsen WHERE argument_id = ? AND door = ?",
                       (arg_id, g.user["username"])).fetchone()
    if oud is not None and data.get("herzien") is not True:
        conn.close()
        return jsonify({"error": "Je gaf al een smaadtoets op dit argument (stuur "
                                 "\"herzien\": true om hem bij te werken)"}), 409
    if oud is not None:
        conn.execute("""UPDATE smaad_toetsen SET verdict = ?, reden = ?, herformulering = ?,
                        created_at = CURRENT_TIMESTAMP WHERE id = ?""",
                     (verdict, reden, herformulering, oud["id"]))
        tid = oud["id"]
    else:
        tid = conn.execute("""INSERT INTO smaad_toetsen (argument_id, verdict, reden,
                              herformulering, door) VALUES (?, ?, ?, ?, ?)""",
                           (arg_id, verdict, reden, herformulering,
                            g.user["username"])).lastrowid
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
        VALUES ('smaad_toetsen', ?, ?, ?, ?, ?)
    """, (tid, "updated" if oud else "created", g.user["username"],
          json.dumps({"argument_id": arg_id, "verdict": verdict}), f"smaadtoets: {verdict}"))
    conn.commit()
    conn.close()
    return jsonify({"id": tid, "argument_id": arg_id, "verdict": verdict,
                    "herzien": oud is not None}), 200 if oud else 201


@app.route("/api/beoordeling/smaad_vrijgeven/<int:arg_id>", methods=["POST"])
@require_user("reviewer")
def beoordeling_smaad_vrijgeven(arg_id):
    """De automatische beoordeling heft een smaad_hold op (merge-service) als een ander
    account dan de auteur de claim 'feitelijk' bevond én het nieuwste onafhankelijke
    A1-oordeel zegt dat de bron haar draagt. Kill-switch → 503; niet toegestaan → 409."""
    if os.environ.get("PROPAGANDA_AUTOMATISCHE_BEOORDELING", "1") == "0":
        return jsonify({"vrijgegeven": False, "error": "automatische beoordeling "
                        "uitgeschakeld (PROPAGANDA_AUTOMATISCHE_BEOORDELING=0)"}), 503
    conn = get_db()
    arg = conn.execute("SELECT * FROM arguments WHERE id = ?", (arg_id,)).fetchone()
    if arg is None:
        conn.close()
        return jsonify({"error": "Argument niet gevonden"}), 404
    redenen = []
    if not arg["smaad_hold"]:
        redenen.append("staat niet op smaad_hold")
    toets = _smaadtoets(conn, arg_id, arg["contributed_by"])
    if toets is None or toets["verdict"] != "feitelijk":
        redenen.append("smaadtoets: niet (of nog niet) 'feitelijk'")
    a1 = _nieuwste_a1(conn, arg_id)
    if a1 is None or a1["verdict"] != "klopt" or a1["door"] == arg["contributed_by"]:
        redenen.append("A1: de bron draagt de bewering niet (of nog geen onafhankelijk oordeel)")
    if redenen:
        conn.close()
        return jsonify({"vrijgegeven": False, "redenen": redenen}), 409
    conn.execute("UPDATE arguments SET smaad_hold = 0 WHERE id = ?", (arg_id,))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('arguments', ?, 'updated', ?, ?, ?, ?)
    """, (arg_id, g.user["username"], json.dumps({"smaad_hold": 1}),
          json.dumps({"smaad_hold": 0}),
          f"{BEOORDELING_REDEN_PREFIX}: smaadtoets feitelijk ({toets['door']}: "
          f"{(toets['reden'] or '')[:300]}) en de bron draagt het — vrijgegeven"))
    conn.commit()
    conn.close()
    return jsonify({"vrijgegeven": True, "id": arg_id}), 200


# ── Mechanisme voor een kandidaat-verband (2026-10-06: agents doen alles) ──
# Een voorgestelde relatie zonder mechanisme ('kandidaat') wacht niet meer op een mens: de
# mechanisme-toewijzer (scripts/mechanisme_toewijzer.py) kiest een bestaand mechanisme dat het
# verband beschrijft, en de automatische beoordeling zet het hier (merge-service). Daarna gaat
# de relatie langs de gewone bewijspoort. Past er geen, dan blijft ze kandidaat.
@app.route("/api/beoordeling/mechanisme/<int:rid>", methods=["POST"])
@require_user("reviewer")
def beoordeling_mechanisme(rid):
    """{mechanism_id, motivatie}: zet het mechanisme van een kandidaat-relatie. Kill-switch →
    503; geen kandidaat of onbekend mechanisme → 409/400."""
    if os.environ.get("PROPAGANDA_AUTOMATISCHE_BEOORDELING", "1") == "0":
        return jsonify({"gezet": False, "error": "automatische beoordeling uitgeschakeld "
                        "(PROPAGANDA_AUTOMATISCHE_BEOORDELING=0)"}), 503
    data = request.get_json(silent=True) or {}
    mid = data.get("mechanism_id")
    motivatie = (data.get("motivatie") or "").strip()[:600]
    if isinstance(mid, bool) or not isinstance(mid, int) or not motivatie:
        return jsonify({"error": "mechanism_id (geheel getal) en motivatie zijn verplicht"}), 400
    conn = get_db()
    rel = conn.execute("SELECT * FROM relations WHERE id = ?", (rid,)).fetchone()
    mech = conn.execute("SELECT id, name, vervangen FROM mechanisms WHERE id = ?",
                        (mid,)).fetchone()
    if rel is None:
        conn.close()
        return jsonify({"error": "Relatie niet gevonden"}), 404
    if mech is None or mech["vervangen"]:
        conn.close()
        return jsonify({"error": f"Mechanisme {mid} bestaat niet (meer)"}), 400
    redenen = []
    if rel["status"] != "voorgesteld" or rel["vervangen"]:
        redenen.append(f"relatie is '{rel['status']}'{' en vervangen' if rel['vervangen'] else ''}")
    if rel["mechanism_id"] is not None:
        redenen.append("relatie heeft al een mechanisme (geen kandidaat)")
    if conn.execute("SELECT 1 FROM edit_log WHERE table_name = 'relations' AND record_id = ? "
                    "AND reason LIKE 'intrekken%' LIMIT 1", (rid,)).fetchone():
        redenen.append("eerder door een maintainer ingetrokken — nooit automatisch")
    if redenen:
        conn.close()
        return jsonify({"gezet": False, "redenen": redenen}), 409
    conn.execute("UPDATE relations SET mechanism_id = ? WHERE id = ?", (mid, rid))
    conn.execute("""
        INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
        VALUES ('relations', ?, 'updated', ?, ?, ?, ?)
    """, (rid, g.user["username"], json.dumps({"mechanism_id": None}),
          json.dumps({"mechanism_id": mid}),
          f"{BEOORDELING_REDEN_PREFIX}: mechanisme '{mech['name']}' gekozen door de "
          f"mechanisme-toewijzer — {motivatie}"))
    conn.commit()
    conn.close()
    return jsonify({"gezet": True, "id": rid, "mechanism_id": mid}), 200


# ── RfC's door agents (2026-10-06: agents doen alles) ──
# Een open voorstel (RfC) wacht niet meer op menselijke akkoorden: twee onafhankelijke agents
# (scripts/rfc_beoordeling.py, accounts 'rfc-toetser' en 'rfc-criticus') reviewen het via
# POST /api/voorstellen/<id>/reviews, en de automatische beoordeling beslist hier: twee
# akkoorden van verschillende agent-accounts (niet de indiener) en geen afwijzing →
# aangenomen en uitgevoerd; één agent-afwijzing → afgewezen met die motivatie (de indiener kan
# herzien). Een afwijzing door een mens wint altijd (die beslist het gewone review-endpoint).
def rfc_besluit(conn, vid):
    """→ ('geaccepteerd' | 'afgewezen' | None, toelichting, akkoorden)."""
    rij = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (vid,)).fetchone()
    if rij is None:
        return None, "niet gevonden", []
    if rij["status"] != "open":
        return None, f"voorstel is al {rij['status']}", []
    akkoord, afwijzing = [], []
    for r in conn.execute("""
            SELECT vr.reviewer, vr.oordeel, vr.motivatie FROM voorstel_reviews vr
            JOIN users u ON u.username = vr.reviewer
            WHERE vr.voorstel_id = ? AND u.kind = 'agent' AND vr.reviewer <> ?
            ORDER BY vr.id""", (vid, rij["ingediend_door"])):
        (akkoord if r["oordeel"] == "akkoord" else afwijzing).append(r)
    if afwijzing:
        return ("afgewezen", "; ".join(f"{r['reviewer']}: {(r['motivatie'] or '')[:400]}"
                                       for r in afwijzing), [])
    namen = sorted({r["reviewer"] for r in akkoord})
    if len(namen) >= 2:
        return "geaccepteerd", f"akkoord van {', '.join(namen)}", namen
    return None, "wacht op twee onafhankelijke agent-akkoorden", namen


@app.route("/api/beoordeling/rfc/<int:vid>", methods=["POST"])
@require_user("reviewer")
def beoordeling_rfc(vid):
    """Beslis een open RfC op de agent-reviews (merge-service). Kill-switch → 503; nog niets
    te beslissen → 409; uitvoering faalt (bv. hertriage niet leeg) → 409 en het blijft open."""
    if os.environ.get("PROPAGANDA_AUTOMATISCHE_BEOORDELING", "1") == "0":
        return jsonify({"besluit": None, "error": "automatische beoordeling uitgeschakeld "
                        "(PROPAGANDA_AUTOMATISCHE_BEOORDELING=0)"}), 503
    conn = get_db()
    rij = conn.execute("SELECT * FROM voorstellen WHERE id = ?", (vid,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": "Voorstel niet gevonden"}), 404
    besluit, toelichting, _namen = rfc_besluit(conn, vid)
    if besluit is None:
        conn.close()
        return jsonify({"besluit": None, "reden": toelichting}), 409
    if besluit == "afgewezen":
        conn.execute("UPDATE voorstellen SET status = 'afgewezen', besloten_at = "
                     "CURRENT_TIMESTAMP WHERE id = ?", (vid,))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('voorstellen', ?, 'updated', ?, ?, ?)
        """, (vid, g.user["username"], json.dumps({"status": "afgewezen"}),
              f"{BEOORDELING_REDEN_PREFIX}: RfC afgewezen — {toelichting}"[:2000]))
        conn.commit()
        conn.close()
        return jsonify({"besluit": "afgewezen", "id": vid, "reden": toelichting}), 200
    payload = json.loads(rij["payload"])
    try:
        resultaat = voorstellen.voer_uit(conn, rij["soort"], payload, vid,
                                         ingediend_door=rij["ingediend_door"])
        resultaat["automatisch"] = True
        conn.execute("""UPDATE voorstellen SET status = 'geaccepteerd', resultaat = ?,
                        besloten_at = CURRENT_TIMESTAMP WHERE id = ?""",
                     (json.dumps(resultaat, ensure_ascii=False), vid))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('voorstellen', ?, 'merged', ?, ?, ?)
        """, (vid, g.user["username"], json.dumps(resultaat, ensure_ascii=False),
              f"{BEOORDELING_REDEN_PREFIX}: RfC aangenomen op {toelichting}"))
        conn.commit()
    except (ValueError, sqlite3.IntegrityError) as e:
        conn.rollback()
        conn.close()
        return jsonify({"besluit": None, "blokkade": str(e)}), 409
    conn.close()
    return jsonify({"besluit": "geaccepteerd", "id": vid, "resultaat": resultaat}), 200


@app.route("/api/nieuws/autokeur/intrekken", methods=["POST"])
@require_user("maintainer")
def nieuws_autokeur_intrekken():
    """Draai een automatische goedkeuring terug (maintainer): {tabel, id, motivatie}.
    Alleen voor een element waarvan de NIEUWSTE goedkeuring automatisch was: van
    'nieuws-autokeur', of van de automatische beoordeling (reden 'automatische beoordeling…');
    status → 'voorgesteld' (terug in de menselijke wachtrij), edit_log onder de maintainer
    met de motivatie. Een ingetrokken element keurt de autokeur nooit opnieuw goed.
    Een entiteit neemt haar automatisch goedgekeurde relaties mee; hangt er een door een
    mens goedgekeurde relatie aan, dan weigert dit (409) — trek die eerst zelf in/af."""
    data = request.get_json(silent=True) or {}
    tabel, rid = data.get("tabel"), data.get("id")
    motivatie = data.get("motivatie")
    if not _nieuws_autokeur_tabel(tabel):
        return jsonify({"error": "tabel moet 'entities' of 'relations' zijn"}), 400
    if isinstance(rid, bool) or not isinstance(rid, int):
        return jsonify({"error": "id moet een geheel getal zijn"}), 400
    if not isinstance(motivatie, str) or not motivatie.strip():
        return jsonify({"error": "motivatie is verplicht"}), 400
    motivatie = motivatie.strip()
    conn = get_db()
    rij = conn.execute(f"SELECT status FROM {tabel} WHERE id = ?", (rid,)).fetchone()
    if rij is None:
        conn.close()
        return jsonify({"error": "Niet gevonden"}), 404
    if rij["status"] != "goedgekeurd":
        conn.close()
        return jsonify({"error": f"Alleen een goedgekeurd element is in te trekken "
                                 f"(status '{rij['status']}')"}), 409
    def automatisch(tab, ident):
        door, reden = _laatste_goedkeurder(conn, tab, ident)
        return door == NIEUWS_AUTOKEUR or (reden or "").startswith(BEOORDELING_REDEN_PREFIX), door

    ok, door = automatisch(tabel, rid)
    if not ok:
        conn.close()
        return jsonify({"error": f"De laatste goedkeuring was niet automatisch (maar van "
                                 f"'{door}') — gebruik de gewone moderatie"}), 409
    mee = []
    if tabel == "entities":
        menselijk = []
        for r in conn.execute("""SELECT id FROM relations WHERE (source_id = ? OR target_id = ?)
                                 AND status = 'goedgekeurd'""", (rid, rid)).fetchall():
            (mee if automatisch("relations", r["id"])[0] else menselijk).append(r["id"])
        if menselijk:
            conn.close()
            return jsonify({"error": "Aan deze entiteit hangen goedgekeurde relaties die niet "
                                     "door de autokeur zijn goedgekeurd; trek die eerst in of "
                                     "keur ze af", "relaties": menselijk}), 409
    reden = f"{NIEUWS_INTREK_REDEN_PREFIX}: {motivatie}"
    for t, i, r in [("relations", x, f"{reden} (mee met entities #{rid})") for x in mee] + [
            (tabel, rid, reden)]:
        conn.execute(f"UPDATE {t} SET status = 'voorgesteld' WHERE id = ?", (i,))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
            VALUES (?, ?, 'updated', ?, ?, ?, ?)
        """, (t, i, g.user["username"], json.dumps({"status": "goedgekeurd"}),
              json.dumps({"status": "voorgesteld"}), r))
    conn.commit()
    conn.close()
    return jsonify({"ingetrokken": True, "tabel": tabel, "id": rid,
                    "mee_ingetrokken": {"relations": mee}})


@app.route("/api/nieuws/autokeur/log")
@require_user("reviewer")
def nieuws_autokeur_log():
    """De laatste regels van data/nieuws_autokeur_log.jsonl (reviewer+), nieuwste eerst.
    ?limit=100 (max 1000). Plus de teller van vandaag en het plafond."""
    try:
        limit = max(1, min(1000, int(request.args.get("limit", 100))))
    except ValueError:
        return jsonify({"error": "'limit' moet een geheel getal zijn"}), 400
    regels = []
    if NIEUWS_AUTOKEUR_LOG_PATH.exists():
        try:
            for regel in NIEUWS_AUTOKEUR_LOG_PATH.read_text(encoding="utf-8").splitlines():
                regel = regel.strip()
                if regel:
                    try:
                        regels.append(json.loads(regel))
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            return jsonify({"error": f"Autokeur-log onleesbaar: {e}"}), 500
    conn = get_db()
    vandaag = _nieuws_autokeur_vandaag(conn)
    conn.close()
    return jsonify({"regels": regels[-limit:][::-1], "vandaag": vandaag,
                    "plafond": _nieuws_autokeur_plafond(),
                    "uitgeschakeld": os.environ.get("PROPAGANDA_NIEUWS_AUTOKEUR", "1") == "0"})


if __name__ == "__main__":
    print(f"Database: {DB_PATH}")
    print(f"Open: http://localhost:5000")
    app.run(debug=True, port=5000)
