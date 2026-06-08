"""
Modelreview — zwevende edges een bron geven + twee filter-correcties.

Sweep-bevindingen over de overige verbanden:

A. Drie mechanismen misten een `source_role` (zweefden onder ∅ in de graaf), terwijl ze wél
   instance-relaties dragen. De instance-bronrollen + de mechanisme-betekenis wijzen de bron aan:
     - `bron_afhankelijkheid`  (→mediaorganisatie, sourcing)  -> bron = gezagsinstituut
       (17/24 instances zijn gezagsinstituut; "overheid, instituties, woordvoerders")
     - `pr_subsidie`           (→mediaorganisatie, sourcing)  -> bron = voorlichter
       (Gandy's 'information subsidy' = de PR-/voorlichtingsapparatuur)
     - `geweld_intimidatie`    (→journalist, flak)            -> bron BLIJFT NULL (bewust diffuus)
       Een vaste principaal-pijl zou georkestreerd elite-geweld impliceren; dat botst met het
       emergente — niet samenzweerderige — kernframe. Beschrijving krijgt die notitie.

B. Twee filter-misclassificaties (filter-op-relatie: door welk filter wérkt het mechanisme?):
     - `draaideur_politiek_institutie` (politicus→gezagsinstituut): flak -> SOURCING
       (politieke capture corrumpeert een primaire definieerder als bron; het gaat niet over
       media-eigendom maar over de sourcing-stroom — vandaar bij Filter 3, niet Filter 1)
     - `staatsreclame_exploitatie`     (belanghebbende→omroepkoepel): advertentie -> EIGENDOM
       (Ster→OCW→omroep-budgetlus is een staats-financieringshefboom op een media-orgaan, geen
       adverteerderdruk; hoort bij Filter 1/omroepbestel)

Geen mechanismen toegevoegd/verwijderd; telling blijft 106. Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

GEWELD_DESC = (
    "Fysiek én online geweld tegen journalisten: bedreigingen, doxing en gecoördineerde online "
    "haatcampagnes — disproportioneel gericht op vrouwen en minderheden — en in het extreme geval "
    "moord (Peter R. de Vries, 2021). De bron is bewust diffuus gelaten (geen vaste principaal): "
    "geweld en intimidatie komen van uiteenlopende, niet-georkestreerde actoren (criminaliteit, "
    "extremisten, anonieme online-massa), passend bij het emergente — niet samenzweerderige — "
    "karakter van het model."
)


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

    print("\n-- A. bron-toewijzing zwevende edges --")
    for mech, role in [("bron_afhankelijkheid", "gezagsinstituut"), ("pr_subsidie", "voorlichter")]:
        cur = conn.execute(
            "UPDATE mechanisms SET source_role_id=? WHERE name=?", (role_id(conn, role), mech)
        )
        print(f"  {'bron gezet' if cur.rowcount else 'NIET gevonden'}: {mech} ← {role}")

    cur = conn.execute("UPDATE mechanisms SET description=? WHERE name=?", (GEWELD_DESC, "geweld_intimidatie"))
    print(f"  {'beschrijving (bron bewust NULL)' if cur.rowcount else 'NIET gevonden'}: geweld_intimidatie")

    print("\n-- B. filter-correcties --")
    for mech, new_filter in [("draaideur_politiek_institutie", "sourcing"),
                             ("staatsreclame_exploitatie", "eigendom")]:
        cur = conn.execute("UPDATE mechanisms SET filter=? WHERE name=?", (new_filter, mech))
        print(f"  {'filter→'+new_filter if cur.rowcount else 'NIET gevonden'}: {mech}")

    conn.commit()

    print("\n== verificatie ==")
    for nm in ["bron_afhankelijkheid", "pr_subsidie", "geweld_intimidatie",
               "draaideur_politiek_institutie", "staatsreclame_exploitatie"]:
        r = conn.execute(
            """SELECT COALESCE(sr.name,'∅'), COALESCE(tr.name,'∅'), m.filter
               FROM mechanisms m LEFT JOIN roles sr ON sr.id=m.source_role_id
               LEFT JOIN roles tr ON tr.id=m.target_role_id WHERE m.name=?""", (nm,)
        ).fetchone()
        print(f"  {nm:<32} {r[0]} → {r[1]} ({r[2]})")

    rest = conn.execute(
        "SELECT name FROM mechanisms WHERE source_role_id IS NULL OR target_role_id IS NULL ORDER BY name"
    ).fetchall()
    print(f"\n  resterende edges zonder source/target ({len(rest)}): {[x[0] for x in rest]}")
    n = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen: {n} (verwacht 106).")


if __name__ == "__main__":
    main()
