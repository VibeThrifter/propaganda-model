"""
Verrijking: twee-assen-categorisatie van mechanismen — multi-filter + thema's.

Aanleiding: het model gebruikte een enkele `filter`-waarde per mechanisme, met een
noodcategorie `cross_filter` voor alles wat "niet in een filter past". Dat verdoezelde
twee dingen:
  1. Veel mechanismen horen bij MEERDERE Chomsky-filters tegelijk (de draaideur van een
     politicus naar het bedrijfsleven is winstbelang = Eigendom; naar een hoofdredacteur
     is Ideologie; naar de toezichthouder is Flak). `cross_filter` was de noodoplossing.
  2. Er lopen THEMA'S dwars door de filters heen (draaideur, elite-netwerk, geldstromen,
     platform, systemisch, publiek omroepbestel, kennis & expertise) — herkenbare families
     die je los wilt kunnen selecteren, ongeacht onder welk filter ze vallen.

Daarom:
  - `mechanisms.filter` blijft bestaan als PRIMAIR filter (lead-kleur + relatie-overerving).
    De 19 `cross_filter`-mechanismen krijgen hun echte primaire Chomsky-filter. `cross_filter`
    als waarde wordt niet meer gebruikt (winstbelang valt onder Eigendom — H&C filter 1 is
    'ownership AND profit orientation').
  - NIEUW `mechanism_filters` (koppeltabel): alle filter-tags per mechanisme (>=1, incl. primair).
  - NIEUW `mechanism_themes` (koppeltabel): de dwarsliggende thema's per mechanisme (0+).

Onderzoeksframe: pro-elite-bias is een EMERGENTE eigenschap. De thema's zijn analytische
dwarsdoorsnedes, geen complot-clusters.

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig (de koppel-
tabellen worden volledig herschreven uit de definities hieronder).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

CHOMSKY_FILTERS = ("eigendom", "advertentie", "sourcing", "flak", "ideologie", "tegenmacht", "overig")
THEMES = ("draaideur", "elite_netwerk", "geldstromen", "platform", "systemisch",
          "omroepbestel", "kennis_expertise")

# ── Multi-filter: mechanisme -> [filters]; EERSTE = primair (bepaalt kleur). ──
# Dit dekt alle 19 voormalige cross_filter-mechanismen + stakeholder_capitalism_frame
# (krijgt Ideologie erbij). Mechanismen die hier NIET staan houden hun ene filter.
MULTI_FILTER = {
    # Draaideur
    "draaideur_politiek_bedrijfsleven":   ["eigendom"],            # winstbelang = F1
    "draaideur_politiek_media":           ["ideologie"],
    "draaideur_journalistiek_politiek":   ["sourcing", "ideologie"],
    "draaideurconstructie":               ["ideologie", "sourcing"],
    "draaideur_politiek_lobby":           ["sourcing"],
    "draaideur_politiek_institutie":      ["flak"],                # regulatory capture
    # Elite-netwerk
    "mediaeigenaar_elite_netwerk":        ["eigendom", "ideologie"],
    "belang_elite_netwerk":               ["sourcing", "ideologie"],
    "politicus_elite_netwerk":            ["ideologie", "sourcing"],
    "stakeholder_capitalism_frame":       ["ideologie"],  # gecorrigeerd: ideologisch frame, geen advertentie
    # Geldstromen — zuiver economische kanalen; het (ideologische) motief van de
    # geldstroom is geen filter, maar het belang van de actor.
    "partijfinanciering":                 ["eigendom"],
    "externe_mediafinanciering":          ["eigendom"],
    "publieke_groeifinanciering":         ["eigendom", "advertentie"],
    "platform_journalistiekfinanciering": ["advertentie"],
    # Platform/digitaal — attentie-/engagement-economie; polarisatie is een effect,
    # geen ideologisch kanaal.
    "platform_advertentie_concentratie":  ["advertentie"],
    "platform_verdienmodel_druk":         ["advertentie"],
    "algoritmische_filtering":            ["advertentie"],
    "algoritmische_socialisatie":         ["ideologie"],
    # Systemisch
    "eigendomsconcentratie":              ["eigendom"],
    "economische_feedback_loop":          ["eigendom", "advertentie"],
}

# ── Thema's: thema -> [mechanisme-namen]. Many-to-many (een mechanisme mag in meerdere). ──
THEME_MEMBERS = {
    "draaideur": [
        "draaideurconstructie", "draaideur_journalistiek_politiek",
        "draaideur_politiek_bedrijfsleven", "draaideur_politiek_lobby",
        "draaideur_politiek_institutie", "draaideur_politiek_media",
    ],
    "elite_netwerk": [
        "mediaeigenaar_elite_netwerk", "belang_elite_netwerk", "politicus_elite_netwerk",
        "ideologische_synchronisatie", "stakeholder_capitalism_frame",
    ],
    "geldstromen": [
        "partijfinanciering", "externe_mediafinanciering", "publieke_groeifinanciering",
        "platform_journalistiekfinanciering", "denktank_financiering_bias",
        "projectfinanciering_journalistiek",
    ],
    "platform": [
        "platform_advertentie_concentratie", "platform_verdienmodel_druk",
        "algoritmische_filtering", "algoritmische_socialisatie",
        "platform_journalistiekfinanciering",
    ],
    "systemisch": [
        "eigendomsconcentratie", "economische_feedback_loop",
        "emergente_bias", "systemische_homeostase", "hegemonische_naturalisatie",
    ],
    "omroepbestel": [
        "bestelsturing", "intekensturing", "ledeneis", "erkenningverlening",
        "politieke_benoeming_omroeptop", "omroepsignatuur", "omroepverzuiling",
        "staatsreclame_exploitatie",
    ],
    "kennis_expertise": [
        "academische_autoriteit", "academische_socialisatie",
        "academische_socialisatie_politiek", "academische_vorming_opinie",
        "academische_orthodoxie_denktank", "academische_orthodoxie_instituut",
        "denktank_levert_expert", "denktank_naar_persbureau", "denktank_naar_politiek",
        "denktank_financiering_bias", "expert_framing", "expert_legitimatie",
        "institutioneel_gezag",
    ],
}


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, dest)
    print(f"Backup gemaakt: {dest.name}")


def ensure_tables(conn):
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS mechanism_filters (
            mechanism_id INTEGER NOT NULL REFERENCES mechanisms(id) ON DELETE CASCADE,
            filter TEXT NOT NULL CHECK(filter IN {CHOMSKY_FILTERS}),
            PRIMARY KEY (mechanism_id, filter)
        )""")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS mechanism_themes (
            mechanism_id INTEGER NOT NULL REFERENCES mechanisms(id) ON DELETE CASCADE,
            theme TEXT NOT NULL CHECK(theme IN {THEMES}),
            PRIMARY KEY (mechanism_id, theme)
        )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mechfilters_filter ON mechanism_filters(filter)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mechthemes_theme ON mechanism_themes(theme)")
    print("Koppeltabellen mechanism_filters / mechanism_themes klaar.")


def mech_id(conn, name):
    row = conn.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
    if not row:
        raise SystemExit(f"FOUT: mechanisme '{name}' niet gevonden.")
    return row[0]


def role_id(conn, name):
    row = conn.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
    if not row:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
    return row[0]


# Mechanismen die inhoudelijk verkeerd geplaatst stonden (bron-rol). Het primaire filter
# wordt al via MULTI_FILTER gezet; hier alleen de bron-rol corrigeren.
ROLE_FIXES = {
    # 'WEF propageert stakeholder capitalism': de bron is een elite-forum, geen adverteerder.
    "stakeholder_capitalism_frame": {"source_role": "elite_forum"},
}


def fix_misplaced_roles(conn):
    for name, fix in ROLE_FIXES.items():
        if "source_role" in fix:
            conn.execute("UPDATE mechanisms SET source_role_id=? WHERE name=?",
                         (role_id(conn, fix["source_role"]), name))
        print(f"Bron-rol gecorrigeerd: {name} → {fix.get('source_role','?')}")


def reassign_primary_filters(conn):
    """Zet het primaire filter van de multi-filter-mechanismen (haalt cross_filter eruit)."""
    n = 0
    for name, filters in MULTI_FILTER.items():
        conn.execute("UPDATE mechanisms SET filter=? WHERE name=?", (filters[0], name))
        n += 1
    left = conn.execute("SELECT COUNT(*) FROM mechanisms WHERE filter='cross_filter'").fetchone()[0]
    print(f"Primair filter herzet voor {n} mechanismen; resterende cross_filter-rijen: {left}.")


def rebuild_filter_tags(conn):
    """Vul mechanism_filters volledig opnieuw: voor elk mechanisme alle filter-tags."""
    conn.execute("DELETE FROM mechanism_filters")
    rows = conn.execute("SELECT id, name, filter FROM mechanisms").fetchall()
    total = 0
    for mid, name, primary in rows:
        filters = MULTI_FILTER.get(name, [primary])
        for f in filters:
            conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) VALUES (?,?)",
                         (mid, f))
            total += 1
    multi = conn.execute("""
        SELECT COUNT(*) FROM (SELECT mechanism_id FROM mechanism_filters
                              GROUP BY mechanism_id HAVING COUNT(*) > 1)""").fetchone()[0]
    print(f"mechanism_filters gevuld: {total} tags over {len(rows)} mechanismen ({multi} multi-filter).")


def rebuild_theme_tags(conn):
    """Vul mechanism_themes volledig opnieuw uit THEME_MEMBERS."""
    conn.execute("DELETE FROM mechanism_themes")
    total = 0
    for theme, names in THEME_MEMBERS.items():
        for name in names:
            conn.execute("INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) VALUES (?,?)",
                         (mech_id(conn, name), theme))
            total += 1
    print(f"mechanism_themes gevuld: {total} tags over {len(THEME_MEMBERS)} thema's.")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: {DB_PATH} bestaat niet.")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        ensure_tables(conn)
        fix_misplaced_roles(conn)
        reassign_primary_filters(conn)
        rebuild_filter_tags(conn)
        rebuild_theme_tags(conn)
        bad = conn.execute("PRAGMA foreign_key_check").fetchall()
        if bad:
            raise SystemExit(f"FOUT: foreign_key_check faalt: {bad}")
        conn.commit()
        print("Klaar: twee-assen-categorisatie (multi-filter + thema's) toegepast.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
