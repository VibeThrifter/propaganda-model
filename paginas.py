"""Programmatic-SEO — één server-gerenderde pagina per model-element (B4).

Per entiteit / persoon / mechanisme / relatie bouwt dit module een render-context
uit dezelfde afgeleide data die de viz gebruikt (`viz_data.export_data`), en rendert
die server-side met Jinja2 (komt met Flask — geen nieuwe dependency). De HTML is
zichtbaar zónder JavaScript, met unieke <title>/<meta>/<canonical>/OG/H1 en een
crawlbare interne-links-graaf: de eigenlijke SEO-motor.

Puur stdlib + de bestaande repo-root modules + Jinja2 (via Flask). De renderkost
wordt gedempt met een mtime-cache op dezelfde drie inputs als `_graph_cache_key` in
server.py (DB, bridging.json, nieuwste release).

Aangeroepen door de SSR-routes in server.py; server.py schrijft hier niet in de DB.
"""
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

import viz_data

ROOT = Path(__file__).parent
DB_PATH = ROOT / "data" / "propaganda_model.db"
BRIDGING_PATH = ROOT / "data" / "bridging.json"
RELEASES_DIR = ROOT / "releases"
WEB_DIR = ROOT / "web"

MERK = "Wie bezit de Nederlandse media"

# ── Leesbare namen (W2.3) — Python-poort van web/shared_vocab.js ──────────────
# TWEELINGBRON: deze twee maps spiegelen NAAM_WEERGAVE / FILTER_LABELS in
# web/shared_vocab.js (:31 / :18). Houd ze in sync — de sleutels blijven in de DB
# snake_case; dit is puur een weergavelaag (zoals weergaveNaam() in de JS).
NAAM_WEERGAVE = {
    # Rollen
    "mediaeigenaar": "Media-eigenaar",
    "raad_van_commissarissen": "Raad van commissarissen (RvC)",
    "columnist_opiniemaker": "Columnist / opiniemaker",
    "elite_forum": "Elite-forum",
    "vakbond_media": "Vakbond (media)",
    # Mechanismen — spelling (trema's, koppeltekens, afkortingen)
    "commerciele_afhankelijkheid": "Commerciële afhankelijkheid",
    "continuiteitsborging": "Continuïteitsborging",
    "gecoordineerde_voorlichting": "Gecoördineerde voorlichting",
    "inlichtingen_cooptatie": "Inlichtingen-coöptatie",
    "pr_inhuur": "PR-inhuur",
    "pr_subsidie": "PR-subsidie",
    "woo_obstructie": "Woo-obstructie",
    "stak_stemzeggenschap": "STAK-stemzeggenschap",
    "cross_media_eigendom": "Cross-media-eigendom",
    "media_agendering": "Media-agendering",
    "intermedia_agendering": "Intermedia-agendering",
    "journalist_bronrelatie": "Journalist-bronrelatie",
    # Mechanismen — elite-netwerkfamilie
    "belang_elite_netwerk": "Belanghebbende in elite-netwerk",
    "mediaeigenaar_elite_netwerk": "Media-eigenaar in elite-netwerk",
    "politicus_elite_netwerk": "Politicus in elite-netwerk",
    "elite_media_netwerk": "Elite-medianetwerk",
    "elite_kennisnetwerk": "Elite-kennisnetwerk",
    # Mechanismen — richting
    "draaideur_journalistiek_politiek": "Draaideur journalistiek ↔ politiek",
    "draaideur_journalistiek_voorlichting": "Draaideur journalistiek ↔ voorlichting",
    "draaideur_politiek_bedrijfsleven": "Draaideur politiek ↔ bedrijfsleven",
    "draaideur_politiek_institutie": "Draaideur politiek ↔ institutie",
    "draaideur_politiek_lobby": "Draaideur politiek ↔ lobby",
    "draaideur_politiek_media": "Draaideur politiek ↔ media",
    "denktank_naar_persbureau": "Denktank → persbureau",
    "denktank_naar_politiek": "Denktank → politiek",
    "lobbyist_naar_journalist": "Lobbyist → journalist",
    "lobbyist_naar_politicus": "Lobbyist → politicus",
    # Mechanismen — variant tussen haakjes
    "academische_socialisatie_hoofdredacteur": "Academische socialisatie (hoofdredacteur)",
    "academische_socialisatie_politiek": "Academische socialisatie (politiek)",
    "academische_orthodoxie_denktank": "Academische orthodoxie (denktank)",
    "academische_orthodoxie_instituut": "Academische orthodoxie (instituut)",
    # Entiteitstypen
    "pr_bureau": "PR-bureau",
    "ngo": "NGO",
    "elite_netwerk": "Elite-netwerk",
}

# Spiegelt FILTER_LABELS in web/shared_vocab.js (:18).
FILTER_LABELS = {
    "eigendom": "1. Eigendom", "advertentie": "2. Advertentie",
    "sourcing": "3. Sourcing", "flak": "4. Flak", "ideologie": "5. Ideologie",
    "systeemactor": "Systeemactor", "tegenmacht": "Tegenmacht",
    "cross_filter": "Cross-filter", "overig": "Overig",
    # Uitbreiding C (besluitvorming, 2026-10-07)
    "formele_macht": "Formele macht", "belangen": "Belangen",
    "kennis_advies": "Kennis & advies", "polder": "Polder", "werving": "Werving",
}


def weergave_naam(naam):
    """Python-poort van weergaveNaam() (web/shared_vocab.js:78)."""
    if naam is None or naam == "":
        return ""
    s = str(naam)
    if s in NAAM_WEERGAVE:
        return NAAM_WEERGAVE[s]
    vlak = s.replace("_", " ").strip()
    return vlak[:1].upper() + vlak[1:] if vlak else ""


def filter_label(cat):
    return FILTER_LABELS.get(cat, weergave_naam(cat))


# ── Slug-schema (id-geprefixt: canoniek is de int, tekst is decoratief) ───────

def slugify(tekst):
    """lowercase / diakriet-strip / [^a-z0-9] → '-' / samenvouwen."""
    if not tekst:
        return ""
    genorm = unicodedata.normalize("NFKD", str(tekst))
    ascii_ = genorm.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", ascii_)).strip("-")


def maak_slug(elem_id, naam):
    """Canonieke, botsings- en rename-vaste slug: '<id>-<slug>' (of '<id>')."""
    s = slugify(naam)
    return f"{elem_id}-{s}" if s else str(elem_id)


def slug_id(slug):
    """Canonieke int uit een slug (leidende cijfers), of None."""
    m = re.match(r"^(\d+)", str(slug or ""))
    return int(m.group(1)) if m else None


# ── mtime-cache op de volledige afgeleide data (zelfde inputs als _graph_cache_key) ──
_cache = {}


def _cache_key():
    def _stat(p):
        try:
            st = p.stat()
            return (st.st_mtime_ns, st.st_size)
        except OSError:
            return (0, 0)
    nieuwste_release = max((_stat(p) for p in RELEASES_DIR.glob("model-v*.json")),
                           default=(0, 0))
    return (_stat(DB_PATH), _stat(BRIDGING_PATH), nieuwste_release)


def _index(conn):
    """Bouw (mtime-gecachet) de volledige afgeleide data één keer en indexeer op id.

    Hergebruikt viz_data.export_data — dezelfde bouw als /api/graph_data — zodat de
    per-element pagina exact de afgeleide scores/vlaggen/meters van de viz krijgt,
    zonder de hele scoringsketen per request te herrekenen."""
    sleutel = _cache_key()
    entry = _cache.get("entry")
    if entry is None or entry[0] != sleutel:
        data = viz_data.export_data(conn)
        idx = {
            "entities": {e["id"]: e for e in data["entities"]},
            "relations": {r["id"]: r for r in data["relations"]},
            "mechanisms": {m["id"]: m for m in data["mechanisms"]},
            "roles": {r["id"]: r for r in data["roles"]},
            "kleurmeter": data.get("kleurmeter", {}),
            "doelgroep": data.get("doelgroep", {}),
            "bereik": data.get("bereik", {}),
            "inkomsten": data.get("inkomsten", {}),
        }
        # Relaties per entiteit (bron + doel)
        rel_uit, rel_in = {}, {}
        for r in data["relations"]:
            if r.get("status") != "goedgekeurd":
                continue
            rel_uit.setdefault(r["source_id"], []).append(r)
            rel_in.setdefault(r["target_id"], []).append(r)
        # Instantie-relaties per mechanisme
        rel_per_mech = {}
        for r in data["relations"]:
            if r.get("status") == "goedgekeurd" and r.get("mechanism_id"):
                rel_per_mech.setdefault(r["mechanism_id"], []).append(r)
        # Citaties per argument + argumenten per doel
        cit_per_arg = {}
        for c in data["citations"]:
            cit_per_arg.setdefault(c["argument_id"], []).append(c)
        args_op = {"relation_id": {}, "entity_id": {}, "mechanism_id": {}}
        for a in data["arguments"]:
            if a.get("status") in ("verworpen", "verouderd", "voorgesteld"):
                continue
            # Smaad-firewall (D2.3): een negatieve persoonsclaim onder smaad_hold rendert
            # nooit publiek tot de eigenaar 'm vrijgeeft. viz_data.export_data houdt zulke
            # args al helemaal uit deze lijst; deze guard maakt de uitsluiting expliciet en
            # blijft veilig mocht de export ze ooit meesturen.
            if a.get("smaad_hold"):
                continue
            if a.get("parent_argument_id"):  # alleen roots dragen bronnen op het doel
                continue
            for veld in args_op:
                if a.get(veld):
                    args_op[veld].setdefault(a[veld], []).append(a)
        idx.update({"rel_uit": rel_uit, "rel_in": rel_in,
                    "rel_per_mech": rel_per_mech,
                    "cit_per_arg": cit_per_arg, "args_op": args_op})
        entry = (sleutel, idx)
        _cache["entry"] = entry
    return entry[1]


# ── Helpers voor de render-context ────────────────────────────────────────────

def _pad_entiteit(e):
    soort = "persoon" if e.get("type") == "persoon" else "entiteit"
    return f"/{soort}/{maak_slug(e['id'], e['name'])}"


def _rel_link(idx, entiteit_id):
    e = idx["entities"].get(entiteit_id)
    if not e:
        return None
    return {"id": entiteit_id, "naam": e["name"], "pad": _pad_entiteit(e),
            "type": weergave_naam(e.get("type"))}


def _relatie_rij(idx, r, kant):
    """kant='uit' → toon het doel; kant='in' → toon de bron."""
    ander_id = r["target_id"] if kant == "uit" else r["source_id"]
    link = _rel_link(idx, ander_id)
    mech = idx["mechanisms"].get(r.get("mechanism_id"))
    return {
        "id": r["id"],
        "pad": f"/relatie/{r['id']}",
        "richting": "→" if kant == "uit" else "←",
        "ander": link,
        "relatie_type": weergave_naam(r.get("relation_type")),
        "mechanisme": ({"id": mech["id"], "naam": weergave_naam(mech["name"]),
                        "pad": f"/mechanisme/{maak_slug(mech['id'], mech['name'])}"}
                       if mech else None),
        "beschrijving": r.get("description") or "",
        "zekerheid": r.get("derived_certainty"),
        "invloed": r.get("derived_influence"),
    }


def _citaties_voor(idx, args):
    """Platte, ontdubbelde bronnenlijst uit een set argumenten (roots)."""
    uit, gezien = [], set()
    for a in args:
        for c in idx["cit_per_arg"].get(a["id"], []):
            sleutel = (c.get("source_title"), c.get("quote"), c.get("url"))
            if sleutel in gezien:
                continue
            gezien.add(sleutel)
            uit.append({
                "titel": c.get("source_title") or "(bron)",
                "auteur": c.get("source_author") or "",
                "quote": c.get("quote") or "",
                "url": c.get("url"),
                "archief": c.get("archive_url"),
            })
    return uit


def _score_vlaggen(d):
    """Python-poort van scoreVlaggen() (template.html:4569) — leesbare vlaggen."""
    if not d:
        return []
    v = []
    if d.get("onweersproken"):
        v.append({"label": "onweersproken" + (" · plafond" if d.get("capped") else ""),
                  "titel": "geen overwogen tegenspraak (≥1 niet-verworpen tegenargument "
                           "mét bron): geloofwaardigheid gemaximeerd op 70% (M1.4)",
                  "kleur": "#f0a030"})
    if d.get("spof"):
        v.append({"label": "1 broncluster",
                  "titel": "alle steun drijft op één broncluster — geen onafhankelijke "
                           "bewijslijnen (M1.2)", "kleur": "#e74c3c"})
    if d.get("zonder_compositieclaim"):
        v.append({"label": "geen compositieclaim",
                  "titel": "geen bewijs dat het sámenspel bestaat (alleen de leden): "
                           "plafond 50% (M1.5)", "kleur": "#e74c3c"})
    if d.get("bron") == "prior":
        v.append({"label": "prior",
                  "titel": "nog geen argumenten: de score is de handmatige inschatting "
                           "(prior)", "kleur": "#7f8c9a"})
    return v


def _pct(x):
    return None if x is None else round(float(x) * 100)


def _kleurmeter_tekst(km):
    """Leesbare, geattribueerde samenvatting van de afgeleide politieke positie."""
    if not km or not km.get("genoeg"):
        return None
    pos = km.get("positie") or {}
    assen = [
        ("economisch", "economisch links", "economisch rechts"),
        ("cultureel", "cultureel progressief", "cultureel conservatief"),
        ("establishment", "anti-establishment", "pro-establishment"),
    ]
    delen = []
    for sleutel, links, rechts in assen:
        v = pos.get(sleutel)
        if v is None:
            continue
        if abs(v) < 0.08:
            delen.append(f"{sleutel}: neutraal")
        else:
            delen.append(f"{(links if v < 0 else rechts)} ({v:+.2f})")
    return "; ".join(delen) if delen else None


def _eerste_zin(tekst):
    if not tekst:
        return ""
    m = re.match(r"(.+?[.!?])(\s|$)", tekst.strip())
    return (m.group(1) if m else tekst).strip()


# ── B5: gecachete AI-prose — fingerprint (staleness) + cache-lookup ────────────

def prose_fingerprint(ctx):
    """Stabiele fingerprint van de prose-inputs voor een render-context.

    GEDEELD met scripts/genereer_prose.py: die batch-generator bouwt exact dezelfde
    render-context (via bouw_entiteit/bouw_mechanisme) en berekent deze hash, zodat
    een fingerprint-mismatch bij render betekent dat de onderliggende data sinds de
    generatie veranderde (stale prose → niet tonen). Zelfde geest als
    _graph_cache_key in server.py, maar per element: de hash dekt precies de velden
    die de samenvatting parafraseert — naam, de relaties (id/buur/mechanisme/scores)
    en de meterposities (kleur/welstand/bereik)."""
    def _rel(r):
        if not r:
            return None
        ander = r.get("ander") or {}
        mech = r.get("mechanisme") or {}
        return [r.get("id"), ander.get("id"), mech.get("id"),
                _pct(r.get("zekerheid")), _pct(r.get("invloed"))]

    def _sorteer(rijen):
        schoon = [x for x in (_rel(r) for r in (rijen or [])) if x]
        return sorted(schoon, key=lambda x: (x[0] is None, x[0]))

    kern = {
        "naam": ctx.get("h1"),
        "soort": ctx.get("soort"),
        "uit": _sorteer(ctx.get("relaties_uit")),
        "in": _sorteer(ctx.get("relaties_in")),
        "instanties": _sorteer(ctx.get("instanties")),
        "kleurmeter": ctx.get("kleurmeter"),
        "welstand": ctx.get("welstand"),
        "bereik": ctx.get("bereik"),
        "score_pct": ctx.get("score_pct"),
        "sterkte_pct": ctx.get("sterkte_pct"),
    }
    blob = json.dumps(kern, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _vul_prose(conn, ctx, element_type, element_id):
    """Vul ctx['prose'] met gecachete, verse AI-prose (of laat 'm None).

    Puur een DB-lookup — NOOIT een LLM-call in het request-pad. De prose telt in
    niets mee (afgeleide copy). Toont alleen wanneer de opgeslagen invoer_hash exact
    de live-fingerprint matcht (anders is de prose stale → weg, graceful). De tabel
    kan in een oude DB ontbreken → dan stil terugvallen op geen prose."""
    try:
        row = conn.execute(
            "SELECT prose, invoer_hash FROM afgeleide_prose "
            "WHERE element_type = ? AND element_id = ?",
            (element_type, int(element_id))).fetchone()
    except sqlite3.Error:
        return ctx
    if row and row[0] and row[1] == prose_fingerprint(ctx):
        ctx["prose"] = row[0]
    return ctx


# ── Per-element render-contexten ──────────────────────────────────────────────

def bouw_entiteit(idx, e):
    """Render-context voor een org- of persoon-entiteit (of None → 404)."""
    is_persoon = e.get("type") == "persoon"
    soort = "persoon" if is_persoon else "entiteit"
    naam = e["name"]
    type_label = weergave_naam(e.get("type"))
    filter_cat = e.get("filter_category")
    canonical = _pad_entiteit(e)

    rel_uit = [_relatie_rij(idx, r, "uit") for r in idx["rel_uit"].get(e["id"], [])]
    rel_in = [_relatie_rij(idx, r, "in") for r in idx["rel_in"].get(e["id"], [])]

    # Bronnen: argumenten op de entiteit zélf + op haar relaties.
    args = list(idx["args_op"]["entity_id"].get(e["id"], []))
    for r in idx["rel_uit"].get(e["id"], []) + idx["rel_in"].get(e["id"], []):
        args += idx["args_op"]["relation_id"].get(r["id"], [])
    citaties = _citaties_voor(idx, args)

    # Interne-links-graaf: buren + betrokken mechanismen.
    buren, gezien_e = [], set()
    mechs, gezien_m = [], set()
    for rij in rel_uit + rel_in:
        if rij["ander"] and rij["ander"]["id"] not in gezien_e:
            gezien_e.add(rij["ander"]["id"])
            buren.append(rij["ander"])
        if rij["mechanisme"] and rij["mechanisme"]["id"] not in gezien_m:
            gezien_m.add(rij["mechanisme"]["id"])
            mechs.append(rij["mechanisme"])

    # Meters (waar van toepassing) → leesbare context.
    km = idx["kleurmeter"]
    kleur_raw = (km.get("personen", {}).get(e["id"])
                 or km.get("organisaties", {}).get(e["id"]))
    kleurmeter = _kleurmeter_tekst(kleur_raw)
    dg = idx["doelgroep"].get("outlets", {}).get(e["id"])
    welstand = (dg.get("klasse_label") if dg and dg.get("n_signalen") else None)
    br = idx["bereik"].get("entiteiten", {}).get(e["id"])
    bereik = (br.get("reeks") if br and br.get("reeks") else None)
    inkomsten = idx["inkomsten"].get(e["id"])

    n_rel = len(rel_uit) + len(rel_in)
    intro = (f"{naam} is {'een persoon' if is_persoon else weergave_naam(e.get('type'))} "
             f"in dit open onderzoek naar de structuur van het Nederlandse medialandschap. "
             f"Dit dossier bundelt {n_rel} gedocumenteerde "
             f"{'relatie' if n_rel == 1 else 'relaties'} met andere actoren, "
             f"met de onderliggende bronnen.")
    beschrijving = e.get("description") or ""
    meta = _eerste_zin(beschrijving) or intro

    return {
        "soort": soort,
        "canonical": canonical,
        "viz_deeplink": f"/#sel=entity:{e['id']}",
        "titel": f"{naam} — {type_label} in de Nederlandse media | {MERK}",
        "meta_description": meta[:300],
        "h1": naam,
        "ondertitel": type_label + (f" · {filter_label(filter_cat)}" if filter_cat else ""),
        "prose": None,          # B5-hook: gecachete AI-prose vult dit later in paginas.py
        "intro": intro,
        "beschrijving": beschrijving,
        "is_persoon": is_persoon,
        "filter_label": filter_label(filter_cat) if filter_cat else None,
        "score": e.get("score_detail"),
        "score_pct": _pct(e.get("derived_certainty")),
        "score_vlaggen": _score_vlaggen(e.get("score_detail")),
        "relaties_uit": rel_uit,
        "relaties_in": rel_in,
        "citaties": citaties,
        "buren": buren,
        "mechanismen": mechs,
        "kleurmeter": kleurmeter,
        "welstand": welstand,
        "bereik": bereik,
        "inkomsten": inkomsten,
    }


def bouw_mechanisme(idx, m):
    naam = weergave_naam(m["name"])
    filter_cat = m.get("filter")
    canonical = f"/mechanisme/{maak_slug(m['id'], m['name'])}"

    bron_rol = idx["roles"].get(m.get("source_role_id"))
    doel_rol = idx["roles"].get(m.get("target_role_id"))

    instanties = [_relatie_rij(idx, r, "uit")
                  for r in idx["rel_per_mech"].get(m["id"], [])]
    citaties = _citaties_voor(idx, idx["args_op"]["mechanism_id"].get(m["id"], []))

    intro = (f"{naam} is een mechanisme in het filter “{filter_label(filter_cat)}” van het "
             f"propagandamodel toegepast op Nederland. Het beschrijft een structureel "
             f"proces — geen motief van individuen — met "
             f"{len(instanties)} gedocumenteerde "
             f"{'instantie' if len(instanties) == 1 else 'instanties'} in de praktijk.")
    beschrijving = m.get("description") or ""
    meta = _eerste_zin(beschrijving) or intro

    return {
        "soort": "mechanisme",
        "canonical": canonical,
        "viz_deeplink": f"/#sel=mechanism:{m['id']}",
        "titel": f"{naam} — mechanisme ({filter_label(filter_cat)}) in de Nederlandse media | {MERK}",
        "meta_description": meta[:300],
        "h1": naam,
        "ondertitel": f"Mechanisme · {filter_label(filter_cat)}",
        "prose": None,          # B5-hook
        "intro": intro,
        "beschrijving": beschrijving,
        "effect": m.get("effect") or "",
        "filter_label": filter_label(filter_cat),
        "bron_rol": ({"naam": weergave_naam(bron_rol["name"]),
                      "pad": None} if bron_rol else None),
        "doel_rol": ({"naam": weergave_naam(doel_rol["name"]),
                      "pad": None} if doel_rol else None),
        "score": m,  # theory_scores-velden zitten op het mechanisme-dict zelf
        "score_pct": _pct(m.get("geloofwaardigheid")),
        "sterkte_pct": _pct(m.get("sterkte")),
        "score_vlaggen": _score_vlaggen(m),
        "instanties": instanties,
        "citaties": citaties,
        "mechanismen": [],
        "buren": [],
    }


def bouw_relatie(idx, r):
    bron = idx["entities"].get(r["source_id"])
    doel = idx["entities"].get(r["target_id"])
    if not bron or not doel:
        return None
    mech = idx["mechanisms"].get(r.get("mechanism_id"))
    rel_type = weergave_naam(r.get("relation_type"))
    naam = f"{bron['name']} {rel_type or 'relatie'} {doel['name']}"
    canonical = f"/relatie/{r['id']}"

    citaties = _citaties_voor(idx, idx["args_op"]["relation_id"].get(r["id"], []))

    bron_link = _rel_link(idx, r["source_id"])
    doel_link = _rel_link(idx, r["target_id"])
    mech_link = ({"id": mech["id"], "naam": weergave_naam(mech["name"]),
                  "pad": f"/mechanisme/{maak_slug(mech['id'], mech['name'])}",
                  "filter_label": filter_label(mech.get("filter"))}
                 if mech else None)

    intro = (f"Gedocumenteerde relatie: {bron['name']} "
             f"{'→' } {doel['name']}"
             f"{' (' + rel_type + ')' if rel_type else ''}"
             f"{', een instantie van het mechanisme “' + weergave_naam(mech['name']) + '”' if mech else ''}. "
             f"Onderbouwd met bronnen en gewogen op zekerheid en invloed.")
    beschrijving = r.get("description") or ""
    meta = _eerste_zin(beschrijving) or intro

    return {
        "soort": "relatie",
        "canonical": canonical,
        "viz_deeplink": f"/#sel=relation:{r['id']}",
        "titel": f"{bron['name']} → {doel['name']} — relatie in de Nederlandse media | {MERK}",
        "meta_description": meta[:300],
        "h1": naam,
        "ondertitel": (rel_type or "Relatie")
                      + (f" · {filter_label(mech.get('filter'))}" if mech else ""),
        "prose": None,          # B5-hook
        "intro": intro,
        "beschrijving": beschrijving,
        "bron": bron_link,
        "doel": doel_link,
        "mechanisme": mech_link,
        "relatie_type": rel_type,
        "score": r.get("score_detail"),
        "score_pct": _pct(r.get("derived_certainty")),
        "invloed_pct": _pct(r.get("derived_influence")),
        "score_vlaggen": _score_vlaggen(r.get("score_detail")),
        "citaties": citaties,
        "buren": [b for b in (bron_link, doel_link) if b],
        "mechanismen": [mech_link] if mech_link else [],
    }


# ── Jinja-omgeving + publieke render-API ──────────────────────────────────────
_env = Environment(
    loader=FileSystemLoader(str(WEB_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)
_env.filters["pct"] = lambda x: "" if x is None else f"{round(float(x) * 100)}%"


def _render(ctx, base_url):
    ctx = dict(ctx)
    # B5-hook: zodra paginas.py een `prose`-string levert, wordt de eerste zin de
    # <meta description> (en toont de template de prose als intro-alinea). Zonder
    # prose blijft de feitelijke fallback-description staan.
    if ctx.get("prose"):
        eerste = _eerste_zin(ctx["prose"])
        if eerste:
            ctx["meta_description"] = eerste[:300]
    ctx["merk"] = MERK
    ctx["base_url"] = (base_url or "").rstrip("/")
    ctx["canonical_url"] = ctx["base_url"] + ctx["canonical"]
    return _env.get_template("pagina_element.html").render(**ctx)


def _status_ok_entiteit(e):
    # Publieke pagina: alleen goedgekeurde, niet-vervangen entiteiten (export_data
    # levert ook 'voorgesteld' ghosts en filtert vervangen al weg).
    return bool(e) and e.get("status") == "goedgekeurd"


class Redirect:
    """Sein voor de route: 301 naar het canonieke pad."""
    def __init__(self, pad):
        self.pad = pad


def render_entiteit(conn, slug, base_url, soort="entiteit"):
    """soort ∈ {'entiteit','persoon'} — bepaalt de canonieke type-route.
    Retourneert HTML-string, Redirect(pad) (301) of None (404)."""
    eid = slug_id(slug)
    if eid is None:
        return None
    idx = _index(conn)
    e = idx["entities"].get(eid)
    if not _status_ok_entiteit(e):
        return None
    # Type-correcte canonieke route afdwingen (persoon ↔ /persoon, org ↔ /entiteit).
    juiste_soort = "persoon" if e.get("type") == "persoon" else "entiteit"
    canon = _pad_entiteit(e)
    if soort != juiste_soort or f"/{soort}/{slug}" != canon:
        return Redirect(canon)
    ctx = _vul_prose(conn, bouw_entiteit(idx, e), "entiteit", e["id"])
    return _render(ctx, base_url)


def render_mechanisme(conn, slug, base_url):
    mid = slug_id(slug)
    if mid is None:
        return None
    idx = _index(conn)
    m = idx["mechanisms"].get(mid)
    if not m:
        return None
    canon = f"/mechanisme/{maak_slug(m['id'], m['name'])}"
    if f"/mechanisme/{slug}" != canon:
        return Redirect(canon)
    ctx = _vul_prose(conn, bouw_mechanisme(idx, m), "mechanisme", m["id"])
    return _render(ctx, base_url)


def render_relatie(conn, rid, base_url):
    idx = _index(conn)
    r = idx["relations"].get(rid)
    if not r or r.get("status") != "goedgekeurd":
        return None
    return _render(bouw_relatie(idx, r), base_url)


# ── sitemap.xml ───────────────────────────────────────────────────────────────

def sitemap_xml(conn, base_url):
    """Well-formed sitemap over alle publieke, goedgekeurde, niet-vervangen elementen
    (entiteiten/personen, mechanismen, relaties). <lastmod> = DB-mtime (het model is
    één levend bestand). mtime-gecachet net als de pagina's."""
    base = (base_url or "").rstrip("/")
    try:
        lastmod = _iso_date(DB_PATH.stat().st_mtime)
    except OSError:
        lastmod = _iso_date(0)
    idx = _index(conn)
    from xml.sax.saxutils import escape
    delen = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    def _url(pad):
        delen.append(f"<url><loc>{escape(base + pad)}</loc>"
                     f"<lastmod>{lastmod}</lastmod></url>")

    _url("/")
    _url("/methode")
    for e in idx["entities"].values():
        if e.get("status") == "goedgekeurd":
            _url(_pad_entiteit(e))
    for m in idx["mechanisms"].values():
        _url(f"/mechanisme/{maak_slug(m['id'], m['name'])}")
    for r in idx["relations"].values():
        if r.get("status") == "goedgekeurd":
            _url(f"/relatie/{r['id']}")
    delen.append("</urlset>")
    return "\n".join(delen)


def _iso_date(ts):
    import datetime
    return datetime.date.fromtimestamp(ts).isoformat() if ts else "1970-01-01"


def render_overzicht(conn, base_url):
    """Publiek blader-overzicht: alle goedgekeurde entiteiten (gegroepeerd op type)
    + mechanismen, elk gelinkt naar hun SSR-pagina. Geeft mensen (en crawlers) een
    ingang tot de longtail-pagina's die anders alleen via de sitemap/zoekmachine
    bereikbaar zijn. Hergebruikt de gedeelde huisstijl (topbal + voettekst)."""
    from xml.sax.saxutils import escape
    base = (base_url or "").rstrip("/")
    idx = _index(conn)
    per_type = {}
    for e in idx["entities"].values():
        if e.get("status") == "goedgekeurd":
            per_type.setdefault(e.get("type") or "overig", []).append(e)
    secties = []
    for t, lst in sorted(per_type.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lst.sort(key=lambda e: (e.get("name") or "").lower())
        links = "".join(
            f'<li><a href="{escape(_pad_entiteit(e))}">{escape(e.get("name") or "?")}</a></li>'
            for e in lst)
        secties.append(f'<section><h2>{escape(weergave_naam(t))} '
                       f'<span class="n">{len(lst)}</span></h2><ul class="cols">{links}</ul></section>')
    mechs = sorted(idx["mechanisms"].values(), key=lambda m: (m.get("name") or "").lower())
    mech_links = "".join(
        f'<li><a href="/mechanisme/{escape(maak_slug(m["id"], m["name"]))}">{escape(m.get("name") or "?")}</a></li>'
        for m in mechs)
    secties.append(f'<section><h2>Mechanismen <span class="n">{len(mechs)}</span></h2>'
                   f'<ul class="cols">{mech_links}</ul></section>')
    n_ent = sum(len(v) for v in per_type.values())
    body = "\n".join(secties)
    return f"""<!doctype html>
<html lang="nl"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Overzicht — alle entiteiten &amp; mechanismen | {escape(MERK)}</title>
<meta name="description" content="Bladeroverzicht van alle {n_ent} in kaart gebrachte entiteiten en {len(mechs)} mechanismen in het Nederlandse medialandschap.">
<link rel="canonical" href="{escape(base)}/overzicht">
<link rel="stylesheet" href="/static/huisstijl.css">
<style>
  main {{ max-width: 1040px; margin: 0 auto; padding: 1.25rem 1rem 4rem; }}
  .intro {{ color: var(--text-muted); max-width: 62ch; line-height: 1.5; }}
  section {{ margin-top: 1.6rem; }}
  section h2 {{ font-size: 1.02rem; margin: 0 0 .4rem; border-bottom: 1px solid var(--border); padding-bottom: .25rem; }}
  section h2 .n {{ color: var(--text-dim); font-weight: 400; font-size: .85rem; }}
  ul.cols {{ list-style: none; padding: 0; margin: 0; columns: 3; column-gap: 1.5rem; }}
  ul.cols li {{ break-inside: avoid; margin: .12rem 0; font-size: .9rem; }}
  ul.cols a {{ color: var(--accent); text-decoration: none; }}
  ul.cols a:hover {{ text-decoration: underline; }}
  @media (max-width: 780px) {{ ul.cols {{ columns: 2; }} }}
  @media (max-width: 480px) {{ ul.cols {{ columns: 1; }} }}
</style>
</head><body>
<header class="topbal"></header>
<main>
  <h1>Overzicht</h1>
  <p class="intro">Alle {n_ent} in kaart gebrachte entiteiten en {len(mechs)} mechanismen, elk met een eigen pagina.
  Of verken ze in samenhang in de <a href="/">interactieve graaf</a>.</p>
  {body}
</main>
<script src="/static/huisstijl.js"></script>
</body></html>"""
