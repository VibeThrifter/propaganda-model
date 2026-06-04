"""
Modelreview — `overheidsadvertenties` (laag 1) + concrete financieringsinstanties (laag 2).

Deel 1 (theorie): mechanisme `overheidsadvertenties` (belanghebbende -> mediaorganisatie,
filter advertentie). De Rijksoverheid is via Dienst Publiek en Communicatie/VoRa een van de
grootste enkele adverteerders (~€21-25 mln/jaar); voor titels die op dat budget leunen
ontstaat zachte hefboom. In NL bescheiden vergeleken met landen waar staatsreclame een zwaar
disciplineringsmiddel is.

Deel 2 (instanties): twee gedocumenteerde geldstromen-naar-media als echte `relations`,
elk met mechanisme-instantiation + onderbouwend argument + citaat, zodat ze meetellen in de
scoringsketen:
  - EIB -> DPG Media  [publieke_groeifinanciering]  (~€220 mln, 2022 + 2024; EIB + FTM)
  - Google -> DPG Media [platform_journalistiekfinanciering] (News Showcase-licentiedeal via OPR)

Idempotent (alles guarded op bestaan); backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
TODAY = date.today().isoformat()
BY = "modelreview"

# --- Deel 1: nieuw mechanisme -------------------------------------------------
NEW_MECH = {
    "name": "overheidsadvertenties",
    "filter": "advertentie",
    "mechanism_type": "economisch",
    "source_role": "belanghebbende",
    "target_role": "mediaorganisatie",
    "description": (
        "De overheid zet als adverteerder haar campagnebudget in: de Rijksoverheid is via de Dienst "
        "Publiek en Communicatie/Voorlichtingsraad (VoRa) een van de grootste enkele adverteerders "
        "(~€21-25 mln/jaar). Dezelfde 'adverteerder-hoed' als bij een commerciële belanghebbende, maar "
        "met de overheid als principaal."
    ),
    "effect": (
        "Voor titels die sterk op overheidscampagnes leunen ontstaat zachte hefboom en goodwill: een "
        "prikkel om de overheid-als-adverteerder niet te antagoneren. In NL bescheiden vergeleken met "
        "landen waar staatsreclame een hard disciplineringsmiddel is, maar structureel aanwezig."
    ),
}

# --- Deel 2: bronnen ----------------------------------------------------------
SOURCES = [
    {
        "key": "eib_dpg",
        "title": "EIB and DPG Media Group: EUR 100m for the further digitalisation of media platforms",
        "author": "Europese Investeringsbank",
        "source_type": "persbericht",
        "reliability": "institutioneel",
        "summary": "EIB-persbericht over de leningsovereenkomst met DPG Media voor digitalisering (2022; vervolgtranche 2024).",
        "url": "https://www.eib.org/en/press/all/2022-021-eib-and-dpg-media-group-eur-100m-for-the-further-digitalisation-of-media-platforms-in-belgium-and-the-netherlands",
    },
    {
        "key": "ftm_dpg",
        "title": "In de strijd tegen Big Tech misbruikt uitgever DPG Europese miljoenen, zeggen privacy-experts",
        "author": "Follow the Money",
        "source_type": "nieuwsartikel",
        "reliability": "kwaliteitsjournalistiek",
        "summary": "FTM-onderzoek naar de EIB-leningen aan DPG en de datagedreven Trusted Web-advertentie-infrastructuur.",
        "url": "https://www.ftm.nl/artikelen/dpg-media-en-europese-subsidies",
    },
    {
        "key": "google_opr",
        "title": "Google sluit licentieovereenkomst met elf grote nieuwsorganisaties in Nederland",
        "author": "Google",
        "source_type": "persbericht",
        "reliability": "grijs",
        "summary": "Google-aankondiging van de News Showcase-licentiedeal met elf NL-uitgevers/omroepen via Stichting OPR (o.a. DPG, Mediahuis, RTL, NPO).",
        "url": "https://blog.google/intl/nl-nl/google-nieuws/initiatieven/google-sluit-overeenkomst-met-grote-nieuwsorganisaties-nederland-enp/",
    },
]

# --- Deel 2: relaties + bewijs ------------------------------------------------
RELATIONS = [
    {
        "source": "EIB (Europese Investeringsbank)",
        "target": "DPG Media",
        "relation_type": "financiering",
        "mechanism": "publieke_groeifinanciering",
        "description": (
            "De EIB verstrekte DPG Media in twee tranches ~€220 mln (€100 mln 2022 + €120 mln dec 2024) "
            "voor digitalisering en het 'Trusted Web'-advertentieplatform, gekoppeld aan EU-beleid."
        ),
        "certainty": 0.97,
        "influence": 0.5,
        "exemplarity": 1.0,
        "arg_claim": "De EIB financierde DPG Media met ~€220 mln aan groeileningen voor o.a. Trusted Web.",
        "arg_reasoning": (
            "Twee EIB-tranches (2022: €100 mln; dec 2024: €120 mln), gekoppeld aan EU-digitaliserings"
            "beleid; FTM/Bits of Freedom bekritiseren de datagedreven tracking-infrastructuur die ermee "
            "wordt opgebouwd. Prototypisch voorbeeld van publieke/supranationale groeifinanciering."
        ),
        "citations": [
            {"src": "eib_dpg", "quote": "EUR 100m for the further digitalisation of media platforms in Belgium and the Netherlands", "section": "EIB-persbericht 2022-021"},
            {"src": "ftm_dpg", "quote": "DPG ontving van de EIB in twee tranches honderden miljoenen; privacy-experts spreken van profilering zonder informed consent.", "section": "FTM-onderzoek"},
        ],
    },
    {
        "source": "Google",
        "target": "DPG Media",
        "relation_type": "financiering",
        "mechanism": "platform_journalistiekfinanciering",
        "description": (
            "Google betaalt DPG Media via de News Showcase-licentiedeal (gesloten met elf NL-uitgevers/"
            "omroepen via Stichting OPR) — Big Tech dat de pers deels terugfinanciert die het eigen "
            "advertentiemodel ondermijnde."
        ),
        "certainty": 0.9,
        "influence": 0.35,
        "exemplarity": 0.9,
        "arg_claim": "Google betaalt DPG (via News Showcase/OPR-licentiedeal) voor nieuwsgebruik.",
        "arg_reasoning": (
            "Google sloot een News Showcase-licentieovereenkomst met elf grote NL-nieuwsorganisaties via "
            "Stichting OPR, waaronder DPG Media. Voorbeeld van platform-journalistiekfinanciering "
            "(co-optatie/afhankelijkheid)."
        ),
        "citations": [
            {"src": "google_opr", "quote": "Google sluit licentieovereenkomst met elf grote nieuwsorganisaties in Nederland", "section": "Google-aankondiging News Showcase"},
        ],
    },
]


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bp = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, bp)
    print(f"Backup gemaakt: {bp.name}")


def role_id(conn, name):
    r = conn.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
    if not r:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
    return r[0]


def mech_id(conn, name):
    r = conn.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
    if not r:
        raise SystemExit(f"FOUT: mechanisme '{name}' niet gevonden.")
    return r[0]


def entity_id(conn, name):
    r = conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()
    return r[0] if r else None


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # --- Deel 1: mechanisme overheidsadvertenties ---
    print("\n-- Deel 1: mechanisme overheidsadvertenties --")
    sid, tid = role_id(conn, NEW_MECH["source_role"]), role_id(conn, NEW_MECH["target_role"])
    if conn.execute("SELECT 1 FROM mechanisms WHERE name=?", (NEW_MECH["name"],)).fetchone():
        conn.execute(
            "UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?, source_role_id=?, target_role_id=? WHERE name=?",
            (NEW_MECH["filter"], NEW_MECH["mechanism_type"], NEW_MECH["description"], NEW_MECH["effect"], sid, tid, NEW_MECH["name"]),
        )
        print(f"  bijgewerkt (bestond al): {NEW_MECH['name']}")
    else:
        conn.execute(
            "INSERT INTO mechanisms (name, filter, mechanism_type, description, effect, source_role_id, target_role_id) VALUES (?,?,?,?,?,?,?)",
            (NEW_MECH["name"], NEW_MECH["filter"], NEW_MECH["mechanism_type"], NEW_MECH["description"], NEW_MECH["effect"], sid, tid),
        )
        print(f"  toegevoegd: {NEW_MECH['name']} (advertentie) belanghebbende → mediaorganisatie")

    # --- Deel 2a: EIB-entiteit ---
    print("\n-- Deel 2: entiteit EIB --")
    eib = entity_id(conn, "EIB (Europese Investeringsbank)")
    if eib is None:
        conn.execute(
            "INSERT INTO entities (name, type, primary_role_id, description) VALUES (?,?,?,?)",
            ("EIB (Europese Investeringsbank)", "overheidsinstelling", role_id(conn, "belanghebbende"),
             "Supranationale publieke bank van de EU; verstrekt groeileningen gekoppeld aan EU-beleid, o.a. aan media-uitgevers."),
        )
        eib = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        print(f"  toegevoegd: EIB (id {eib})")
    else:
        print(f"  bestaat al: EIB (id {eib})")

    # --- Deel 2b: bronnen + locaties ---
    print("\n-- Deel 2: bronnen --")
    src_ids = {}
    for s in SOURCES:
        row = conn.execute("SELECT id FROM sources WHERE title=?", (s["title"],)).fetchone()
        if row:
            src_ids[s["key"]] = row[0]
            print(f"  bestaat al: {s['title'][:50]}…")
            continue
        conn.execute(
            "INSERT INTO sources (title, author, source_type, publisher, date_published, summary, reliability, processed) VALUES (?,?,?,?,?,?,?,1)",
            (s["title"], s["author"], s["source_type"], s["author"], None, s["summary"], s["reliability"]),
        )
        sid_ = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        src_ids[s["key"]] = sid_
        conn.execute(
            "INSERT INTO source_locations (source_id, location_type, location, accessed_at) VALUES (?,?,?,?)",
            (sid_, "url", s["url"], TODAY),
        )
        print(f"  toegevoegd bron+locatie: {s['title'][:50]}…")

    # --- Deel 2c: relaties + instantiation + argument + citaties ---
    print("\n-- Deel 2: relaties + bewijs --")
    for r in RELATIONS:
        s_id, t_id = entity_id(conn, r["source"]), entity_id(conn, r["target"])
        if s_id is None or t_id is None:
            raise SystemExit(f"FOUT: entiteit ontbreekt: {r['source']} / {r['target']}")
        m_id = mech_id(conn, r["mechanism"])
        existing = conn.execute(
            "SELECT id FROM relations WHERE source_id=? AND target_id=? AND mechanism_id=?",
            (s_id, t_id, m_id),
        ).fetchone()
        if existing:
            print(f"  bestaat al: {r['source']} → {r['target']} [{r['mechanism']}] (id {existing[0]})")
            continue
        conn.execute(
            "INSERT INTO relations (source_id, target_id, relation_type, mechanism_id, description, certainty, influence) VALUES (?,?,?,?,?,?,?)",
            (s_id, t_id, r["relation_type"], m_id, r["description"], r["certainty"], r["influence"]),
        )
        rel_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT OR IGNORE INTO instantiations (mechanism_id, relation_id, exemplarity, notes) VALUES (?,?,?,?)",
                     (m_id, rel_id, r["exemplarity"], "modelreview: financieringsinstantie"))
        conn.execute(
            "INSERT INTO arguments (relation_id, parent_argument_id, property, stance, claim, reasoning, weight, status, contributed_by) VALUES (?,?,?,?,?,?,?,?,?)",
            (rel_id, None, "existence", "supporting", r["arg_claim"], r["arg_reasoning"], 0.8, "geverifieerd", BY),
        )
        arg_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for c in r["citations"]:
            conn.execute(
                "INSERT INTO citations (argument_id, source_id, quote, section) VALUES (?,?,?,?)",
                (arg_id, src_ids[c["src"]], c["quote"], c["section"]),
            )
        conn.execute(
            "INSERT INTO edit_log (table_name, record_id, action, changed_by, reason) VALUES ('relations', ?, 'created', ?, 'modelreview financieringsinstantie')",
            (rel_id, BY),
        )
        print(f"  toegevoegd: {r['source']} → {r['target']} [{r['mechanism']}] (rel {rel_id}, arg {arg_id}, {len(r['citations'])} citaat/citaten)")

    conn.commit()

    # --- verificatie ---
    print("\n== verificatie ==")
    print(f"  mechanismen totaal: {conn.execute('SELECT COUNT(*) FROM mechanisms').fetchone()[0]}")
    has_oa = bool(conn.execute("SELECT 1 FROM mechanisms WHERE name='overheidsadvertenties'").fetchone())
    print(f"  overheidsadvertenties aanwezig: {has_oa}")
    for r in RELATIONS:
        row = conn.execute(
            """SELECT e1.name, e2.name, m.name, rel.certainty, rel.influence,
                      (SELECT COUNT(*) FROM arguments a WHERE a.relation_id=rel.id),
                      (SELECT COUNT(*) FROM citations c JOIN arguments a ON a.id=c.argument_id WHERE a.relation_id=rel.id)
               FROM relations rel JOIN entities e1 ON e1.id=rel.source_id JOIN entities e2 ON e2.id=rel.target_id
               JOIN mechanisms m ON m.id=rel.mechanism_id
               WHERE rel.source_id=(SELECT id FROM entities WHERE name=?) AND rel.mechanism_id=(SELECT id FROM mechanisms WHERE name=?)""",
            (r["source"], r["mechanism"]),
        ).fetchone()
        if row:
            print(f"  {row[0]} → {row[1]} [{row[2]}] cert={row[3]} infl={row[4]} args={row[5]} cit={row[6]}")
    conn.close()


if __name__ == "__main__":
    main()
