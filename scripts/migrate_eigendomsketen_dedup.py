"""
Modelreview #7 (uitvoering) — eigendomsketens dedupliceren.

Diagnose (vorige sessie): de eigendomskant was dubbel bedraad. Overal liep een pad
ZOWEL via het gemodelleerde vehikel/STAK/sub-holding ALS via een directe shortcut van
baas/holding naar titel. Eigendom is in werkelijkheid een getrapte keten (DAG), geen
mesh: de baas raakt de titel nooit direct — zijn invloed ís de keten. De parallelle
directe edges zijn daarom redundant (en telden bovendien dubbel). De vehikels/STAK
zelf zijn NIET redundant: die zíjn de keten.

Het theorie-principe (keten-mediatie, STAK als controle-versterker) staat al in
DOCUMENTATIE.md (migrate_controle_vs_systemisch). Dit script ruimt nu de instantie-laag op.

Geen schemawijziging. Idempotent: identificeert relaties op (bron, doel, type) en slaat
over wat al weg/aanwezig is. Volgt de backup-then-migrate-conventie.

1. GAT DICHTEN — `NRC Media -> NRC` ontbrak (NRC hing direct onder Mediahuis). Eerst de
   proximate schakel toevoegen, zodat het verwijderen van de shortcut NRC niet losweekt.

2. SHORTCUTS VERWIJDEREN — directe eigendom-edges die een gemodelleerd vehikel/sub-holding
   overslaan, plus het rename-artefact De Persgroep -> DPG:
     DPG -> Volkskrant/AD/Trouw      (loopt via PCM Uitgevers)
     DPG -> NU.nl                    (loopt via Sanoma Nederland)
     Van Thillo -> DPG               (loopt via STAK Epifin -> Epifin)
     Leysen -> Mediahuis             (loopt via Mediahuis Partners)
     Van Puijenbroek -> Mediahuis    (loopt via VP Exploitatie)
     Baert -> Mediahuis              (loopt via Concentra)
     Mediahuis -> De Telegraaf       (loopt via TMG)
     Mediahuis -> NRC                (loopt via NRC Media, na stap 1)
     De Persgroep -> DPG             (artefact: oude naam van DPG Media)
   Alle eraan hangende argumenten zijn auto-gegenereerd, ongecontroleerd en zonder
   citaties; ze worden mee opgeruimd. Andere relatie-types (bv. de winstmaximalisatie-
   `beinvloeding` DPG -> Volkskrant) blijven staan: dat is een andere claim dan eigendom.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# 1. proximate schakel die het gat dicht (bron, doel, type, mechanisme, certainty, influence, claim)
ADD_RELATIONS = [
    ("NRC Media", "NRC", "eigendom", "eigendomsconcentratie", 0.05, 0.9,
     "NRC Media (uitgever) bezit en geeft NRC uit — de proximate eigendomsschakel onder Mediahuis."),
]

# 2. redundante directe shortcuts (bron, doel, type) — er bestaat een gemodelleerd tussenpad
DELETE_RELATIONS = [
    ("DPG Media", "de Volkskrant", "eigendom"),
    ("DPG Media", "AD (Algemeen Dagblad)", "eigendom"),
    ("DPG Media", "Trouw", "eigendom"),
    ("DPG Media", "NU.nl", "eigendom"),
    ("Christian Van Thillo", "DPG Media", "eigendom"),
    ("Thomas Leysen", "Mediahuis", "eigendom"),
    ("Familie Van Puijenbroek", "Mediahuis", "eigendom"),
    ("Familie Baert", "Mediahuis", "eigendom"),
    ("Mediahuis", "De Telegraaf", "eigendom"),
    ("Mediahuis", "NRC", "eigendom"),
    ("De Persgroep", "DPG Media", "eigendom"),
]


def backup_db():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{timestamp}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def entity_id(conn, name):
    row = conn.execute("SELECT id FROM entities WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise SystemExit(f"FOUT: entiteit '{name}' niet gevonden.")
    return row[0]


def find_relation(conn, src, dst, rtype):
    return conn.execute(
        "SELECT id FROM relations WHERE source_id=? AND target_id=? AND relation_type=?",
        (entity_id(conn, src), entity_id(conn, dst), rtype),
    ).fetchone()


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # 1. proximate schakel(s) toevoegen
    print("\n-- 1. ontbrekende proximate schakel toevoegen --")
    for src, dst, rtype, mech, cert, infl, claim in ADD_RELATIONS:
        if find_relation(conn, src, dst, rtype):
            print(f"  bestaat al: {src} -> {dst} ({rtype}) — overgeslagen.")
            continue
        mid = conn.execute("SELECT id FROM mechanisms WHERE name=?", (mech,)).fetchone()
        mid = mid[0] if mid else None
        cur = conn.execute(
            """INSERT INTO relations (source_id, target_id, relation_type, mechanism_id, description, certainty, influence)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entity_id(conn, src), entity_id(conn, dst), rtype, mid, claim, cert, infl),
        )
        rid = cur.lastrowid
        conn.execute(
            """INSERT INTO arguments (relation_id, property, stance, claim, status, contributed_by, weight)
               VALUES (?, 'existence', 'supporting', ?, 'ongecontroleerd', 'migrate_eigendomsketen_dedup', 0.6)""",
            (rid, claim),
        )
        print(f"  toegevoegd: {src} -> {dst} ({rtype}, infl {infl}) [+ existence-argument]")

    # 2. redundante shortcuts verwijderen (incl. afhankelijke argumenten/citaties/instantiaties)
    print("\n-- 2. redundante directe shortcuts verwijderen --")
    removed = 0
    for src, dst, rtype in DELETE_RELATIONS:
        row = find_relation(conn, src, dst, rtype)
        if row is None:
            print(f"  al weg / niet gevonden: {src} -> {dst} ({rtype})")
            continue
        rid = row[0]
        # afhankelijke rijen eerst (geen ON DELETE CASCADE in schema)
        conn.execute(
            "DELETE FROM citations WHERE argument_id IN (SELECT id FROM arguments WHERE relation_id=?)", (rid,)
        )
        nargs = conn.execute("SELECT COUNT(*) FROM arguments WHERE relation_id=?", (rid,)).fetchone()[0]
        conn.execute("DELETE FROM arguments WHERE relation_id=?", (rid,))
        conn.execute("DELETE FROM instantiations WHERE relation_id=?", (rid,))
        conn.execute("DELETE FROM relations WHERE id=?", (rid,))
        removed += 1
        print(f"  verwijderd: {src} -> {dst} ({rtype})  [+{nargs} arg(en)]")

    conn.commit()

    # verificatie
    print("\n== verificatie ==")
    fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    print(f"  FK-integriteit: {'OK' if not fk else fk}")
    for src, dst, rtype in DELETE_RELATIONS:
        if find_relation(conn, src, dst, rtype):
            print(f"  LET OP nog aanwezig: {src} -> {dst} ({rtype})")
    nrc = find_relation(conn, "NRC Media", "NRC", "eigendom")
    print(f"  NRC Media -> NRC aanwezig: {'ja' if nrc else 'NEE'}")
    nrel = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Shortcuts verwijderd: {removed}. Relaties totaal: {nrel}.")


if __name__ == "__main__":
    main()
