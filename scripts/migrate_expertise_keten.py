"""
Modelreview — expertise-keten sluiten + ideologische homofilie expliciteren.

De expertise-/autoriteitsbedrading miste twee schakels (bevestigd bij een check tegen de
literatuur, niet de praktijkdata):

1. `denktank_levert_expert` (denktank -> gezagsexpert): de ontbrekende MIDDENschakel die de
   keten `belanghebbende -> denktank -> gezagsexpert -> journalist` sluit. De denktank fielt en
   credentialiseert zijn eigen verbonden deskundige; die verschijnt via `expert_legitimatie`
   bij de journalist. Naast de institutionele route (`expert_framing`: de denktank zélf als
   geciteerde bron) en de financieringsband (`denktank_financiering_bias`).

2. `academische_autoriteit` (kennisinstituut -> gezagsexpert): de universiteit produceert en
   credentialiseert de 'gezagsexpert' (verleent het gezag). Cruciaal: dezelfde instituten
   socialiseren óók de journalisten (`academische_socialisatie`) -> gedeelde opleidings- en
   wereldbeeldachtergrond -> ideologische HOMOFILIE tussen journalist en 'onafhankelijke' bron.
   Empirisch: NL-journalisten stemmen sterk afwijkend (D66 ~27% vs 9% bevolking, GroenLinks
   ~14% vs 7,3%; De Groene 'Ons soort mensen' / Worlds of Journalism Study).

De bestaande `kennisinstituut -> journalist` (`academische_socialisatie`) is NIET overbodig: ander
doel (journalist socialiseren vs. expert kweken). Juist het delen van die bron maakt de homofilie;
dat wordt in de beschrijving van `academische_socialisatie` geëxpliciteerd.

Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NEW = [
    {
        "name": "denktank_levert_expert",
        "filter": "sourcing",
        "mechanism_type": "procedureel",
        "source_role": "denktank",
        "target_role": "gezagsexpert",
        "description": (
            "Een denktank fielt en credentialiseert zijn eigen, aan het instituut verbonden "
            "deskundigen, die vervolgens als 'onafhankelijke' gezagsexpert worden opgevoerd. Dit is de "
            "ontbrekende middenschakel die de keten belanghebbende → denktank → gezagsexpert → "
            "journalist sluit, naast de institutionele route (`expert_framing`: de denktank zélf als "
            "geciteerde bron) en de financieringsband (`denktank_financiering_bias`)."
        ),
        "effect": (
            "De belangengebonden agenda van de denktank bereikt de journalist via een persoon die als "
            "neutrale wetenschapper oogt; de institutionele inbedding blijft buiten beeld. De laatste "
            "schakel naar de journalist is `expert_legitimatie`."
        ),
    },
    {
        "name": "academische_autoriteit",
        "filter": "ideologie",
        "mechanism_type": "structureel",
        "source_role": "kennisinstituut",
        "target_role": "gezagsexpert",
        "description": (
            "Universiteiten en kennisinstituten produceren en credentialiseren de 'gezagsexperts' "
            "(hoogleraren, economen, deskundigen) die later als neutrale autoriteit worden opgevoerd — "
            "ze verlenen het 'gezag'. Cruciaal: dezelfde instituten socialiseren óók de journalisten "
            "(`academische_socialisatie`), waardoor journalist en expert een gedeelde opleidings- en "
            "wereldbeeldachtergrond delen."
        ),
        "effect": (
            "Ideologische homofilie tussen journalist en bron: de 'onafhankelijke' expert deelt "
            "doorgaans de premissen van de journalist die hem uitnodigt, wat de consensus bevestigt in "
            "plaats van toetst. Empirisch zichtbaar in de sterk afwijkende stemvoorkeur van NL-"
            "journalisten (D66/GroenLinks fors oververtegenwoordigd). De grenzen van het redelijke "
            "debat liggen al vast vóór de uitzending."
        ),
    },
]

ENRICH = [
    {
        "name": "academische_socialisatie",
        "description": (
            "Universiteiten en journalistiekopleidingen socialiseren toekomstige journalisten en "
            "bestuurders in de dominante hegemonie — cultureel progressief én economisch neoliberaal "
            "('progressief neoliberalisme', Fraser) — die als neutrale, wetenschappelijke "
            "vanzelfsprekendheid geldt. Dezelfde instituten leveren via `academische_autoriteit` ook "
            "de 'gezagsexperts' die journalisten later opvoeren: journalist én bron delen zo dezelfde "
            "achtergrond (ideologische homofilie)."
        ),
        "effect": (
            "De grenzen van het 'redelijke' debat worden al vóór de redactievloer gezet; afwijking van "
            "de consensus verschijnt niet als ander standpunt maar als gebrek aan kennis of als "
            "'activisme'. De bias is emergent, niet gecoördineerd. Empirisch correleert dit met de "
            "sterk afwijkende stemvoorkeur van NL-journalisten t.o.v. de bevolking."
        ),
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


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("\n-- nieuwe mechanismen --")
    for m in NEW:
        sid, tid = role_id(conn, m["source_role"]), role_id(conn, m["target_role"])
        if conn.execute("SELECT 1 FROM mechanisms WHERE name=?", (m["name"],)).fetchone():
            conn.execute(
                "UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?, source_role_id=?, target_role_id=? WHERE name=?",
                (m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid, m["name"]),
            )
            print(f"  bijgewerkt (bestond al): {m['name']}")
        else:
            conn.execute(
                "INSERT INTO mechanisms (name, filter, mechanism_type, description, effect, source_role_id, target_role_id) VALUES (?,?,?,?,?,?,?)",
                (m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid),
            )
            print(f"  toegevoegd: {m['name']} ({m['filter']}) {m['source_role']} → {m['target_role']}")

    print("\n-- aanscherpingen --")
    for e in ENRICH:
        cur = conn.execute(
            "UPDATE mechanisms SET description=?, effect=? WHERE name=?",
            (e["description"], e["effect"], e["name"]),
        )
        print(f"  {'aangescherpt' if cur.rowcount else 'NIET gevonden'}: {e['name']}")

    conn.commit()

    print("\n== verificatie: expertise-keten ==")
    for nm in ("denktank_financiering_bias", "denktank_levert_expert", "expert_legitimatie",
               "expert_framing", "academische_autoriteit", "academische_socialisatie"):
        row = conn.execute(
            """SELECT COALESCE(sr.name,'—'), COALESCE(tr.name,'—'), m.filter FROM mechanisms m
               LEFT JOIN roles sr ON sr.id=m.source_role_id LEFT JOIN roles tr ON tr.id=m.target_role_id
               WHERE m.name=?""", (nm,)
        ).fetchone()
        print(f"  {nm}: {row[0]} → {row[1]} ({row[2]})")
    n = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen: {n}.")


if __name__ == "__main__":
    main()
