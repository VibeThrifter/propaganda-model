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
                "(migrate_clean_entity_types.py)",
    "mechanisms": "aard-CHECK leeft alleen in schema.sql; live kolom kwam via ALTER TABLE "
                  "(zie CLAUDE.md)",
    # 'sources' is sinds migrate_scoring_v2.py herbouwd uit schema.sql: geen drift meer.
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
    rel_zonder_mech = [
        f"relatie #{r['id']}: {r['src']} —{r['relation_type']}→ {r['tgt']}"
        for r in conn.execute("""
            SELECT r.id, r.relation_type, e1.name AS src, e2.name AS tgt
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            WHERE r.mechanism_id IS NULL ORDER BY r.id
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
            ORDER BY r.id
        """)]

    ent_zonder_rol = [
        f"entiteit #{e['id']}: {e['name']} ({e['type']})"
        for e in conn.execute("""
            SELECT e.id, e.name, e.type FROM entities e
            WHERE e.primary_role_id IS NULL
              AND NOT EXISTS (SELECT 1 FROM entity_roles er WHERE er.entity_id = e.id)
            ORDER BY e.id
        """)]

    ent_zonder_inst = [
        f"entiteit #{e['id']}: {e['name']} ({e['type']})"
        for e in conn.execute("""
            SELECT e.id, e.name, e.type FROM entities e
            WHERE NOT EXISTS (SELECT 1 FROM instantiations i WHERE i.entity_id = e.id)
            ORDER BY e.id
        """)]

    return [
        _bevinding("KOPPEL-REL-MECH", "Relaties zonder mechanisme", "fout", rel_zonder_mech,
                   "Elke praktijk-edge hoort aan een theoretisch mechanisme te hangen."),
        _bevinding("KOPPEL-REL-INST", "Relaties mét mechanisme maar zonder instantiations-rij",
                   "fout", rel_zonder_inst,
                   "Zonder instantiatie telt de relatie stilletjes niet mee in de theoriescore (laag C)."),
        _bevinding("KOPPEL-ENT-ROL", "Entiteiten zonder rol", "fout", ent_zonder_rol,
                   "Geen primary_role_id en geen entity_roles-rij."),
        _bevinding("KOPPEL-ENT-INST", "Entiteiten zonder rol-instantiatie", "waarschuwing",
                   ent_zonder_inst,
                   "Wel of geen rol, maar geen instantiations-rij: onzichtbaar voor de rolscore."),
    ]


# ── Bewijs & status (Z2) ─────────────────────────────────────

def check_bewijs(conn):
    zonder_citatie = [
        f"argument #{a['id']} ({a['stance']}): {a['claim'][:70]}"
        for a in conn.execute("""
            SELECT a.id, a.stance, a.claim FROM arguments a
            WHERE a.stance IN ('supporting', 'contradicting')
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
        _bevinding("BEWIJS-CITATIE", "Voor/tegen-argumenten zonder citatie", "fout",
                   zonder_citatie,
                   "Een supporting/contradicting-argument zonder bron drijft op de "
                   "ondergrens-bronfactor; de citatiepoort (M0.3) voorkomt nieuwe gevallen."),
        _bevinding("BEWIJS-STATUS", "Statusachterstand (niet-geverifieerde argumenten)", "info",
                   achterstand,
                   f"{onbeoordeeld} van {totaal} argumenten zijn niet 'geverifieerd'.",
                   aantal=onbeoordeeld),
    ]


# ── Stance-balans (Z1) ───────────────────────────────────────

def _alleen_steun(conn, kolom, naam_sql):
    """Doelen (relatie/entiteit/mechanisme/rol/emergent veld) met wél steun maar nul tegenspraak.

    Padclaims (property='indirecte_invloed_op') tellen niet mee: dat zijn
    compositieclaims, geen onderbouwing van het doel zelf (conform scoring.py).
    """
    rows = conn.execute(f"""
        SELECT a.{kolom} AS doel_id, {naam_sql} AS naam,
               SUM(a.stance = 'supporting') AS steun,
               SUM(a.stance = 'contradicting') AS tegen
        FROM arguments a
        WHERE a.{kolom} IS NOT NULL
          AND (a.property IS NULL OR a.property != 'indirecte_invloed_op')
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
    hebben (eerste versie zonder drempels; later dezelfde gates als de viz)."""
    edges = {}
    for m in conn.execute("""
        SELECT source_role_id AS s, target_role_id AS t FROM mechanisms
        WHERE aard = 'direct' AND source_role_id IS NOT NULL AND target_role_id IS NOT NULL
    """):
        edges.setdefault(m["s"], set()).add(m["t"])

    rol_id = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM roles")}

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

    problemen = []
    for a in conn.execute("""
        SELECT a.id, a.property_value, r.name AS bronrol
        FROM arguments a JOIN roles r ON a.role_id = r.id
        WHERE a.property = 'indirecte_invloed_op' ORDER BY a.id
    """):
        doel = (a["property_value"] or "").strip()
        if doel not in rol_id:
            problemen.append(f"padclaim #{a['id']}: doelrol '{doel}' bestaat niet (bronrol {a['bronrol']})")
        elif not bereikbaar(rol_id[a["bronrol"]], rol_id[doel]):
            problemen.append(f"padclaim #{a['id']}: geen keten van directe edges {a['bronrol']} → {doel}")

    return [_bevinding("PADCLAIM-ROUTE", "Padclaims zonder doorlatende route", "fout", problemen,
                       "Een compositieclaim zonder keten van directe edges kan nooit als "
                       "afgeleide pijl getoond worden; doelrollen matchen op naam (kwetsbaar "
                       "bij hernoemen — zie M2.6).")]


# ── Bronnen (locaties, archief, linkrot) ─────────────────────

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

    bevindingen = [
        _bevinding("BRON-LOCATIE", "Bronnen zonder vindplaats (source_locations)",
                   "waarschuwing", zonder_locatie,
                   "Zonder locatie is een bron niet door derden te controleren."),
        _bevinding("BRON-ARCHIEF", "URL-bronnen zonder archive_url", "waarschuwing",
                   zonder_archief,
                   "Webpagina's verdwijnen; een Wayback-snapshot houdt het bewijs controleerbaar."),
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
              AND NOT EXISTS (SELECT 1 FROM citations c WHERE c.argument_id = a.id)"""),
        "relaties_zonder_argumenten": een("""
            SELECT COUNT(*) FROM relations r
            WHERE NOT EXISTS (SELECT 1 FROM arguments a WHERE a.relation_id = r.id)"""),
        "relaties_zonder_mechanisme": een(
            "SELECT COUNT(*) FROM relations WHERE mechanism_id IS NULL"),
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
        "citatie_concentratie_top3": top3,
        "citatie_concentratie_aandeel": (
            round(sum(t["citaties"] for t in top3) / citaties_totaal, 3) if citaties_totaal else None),
    }


# ── Alles in één run ─────────────────────────────────────────

def run_all(conn, schema_path=SCHEMA_PATH, network=False):
    bevindingen = []
    bevindingen += check_koppelingsplicht(conn)
    bevindingen += check_bewijs(conn)
    bevindingen += check_balans(conn)
    bevindingen += check_padclaims(conn)
    bevindingen += check_bronnen(conn, network=network)
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
