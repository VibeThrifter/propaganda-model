"""
Modelreview — drie veld_instantiatie-waaiers die eigenlijk gerichte 2-node-dyades zijn → direct.

Toets (model-definitie): veld_instantiatie = dyad als steekproef uit een regelmaat,
eindpunten VERWISSELBAAR. direct = lokaal feit, de oorzaak ZIJN de twee eindpunten.

Deze drie zijn specifieke, gerichte A→B-relaties, geen diffuus veld:
  • ideologische_synchronisatie  (elite_forum → mediaeigenaar): eigenaren komen besloten
    samen in de fora en absorberen het wereldbeeld; concrete tegenhanger van het al-directe
    mediaeigenaar_elite_netwerk (eigenaar → forum). Twee kanten van één concrete relatie.
  • schijndebat                  (mediaorganisatie → publiek): een concrete redactionele
    ensceneringstechniek (de talkshowtafel) — iets wat de organisatie DOET, geen veldregelmaat.
  • omroepverzuiling             (ledenomroep → publiek): de ledenomroep bedient zijn eigen
    zuilpubliek — een directe bestel-relatie.

Blijven WEL veld (diffuus, eindpunten verwisselbaar, géén bruut kanaal):
  • hegemonische_naturalisatie   (mediaorg ··· publiek): Gramsci's hegemonie via media ÉN
    onderwijs ÉN civil society — meervoudige bron, emergente 'gezond verstand'-werking.
  • stakeholder_capitalism_frame (elite_forum ··· publiek): expliciet "géén direct kanaal";
    diffuus de publieke vanzelfsprekendheid.

Effect op influence.py: veld_instantiatie had aparte demping (één bijdrage per bron,
fan-out/k); als direct tellen ze als gewone gerichte edge. Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

FIELD_TO_DIRECT = [
    "ideologische_synchronisatie",
    "schijndebat",
    "omroepverzuiling",
]


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    rn = {i: n for i, n in conn.execute("SELECT id, name FROM roles")}

    print("veld_instantiatie → direct (gerichte 2-node-dyades):")
    for name in FIELD_TO_DIRECT:
        row = conn.execute(
            "SELECT source_role_id, target_role_id, aard FROM mechanisms WHERE name=?",
            (name,)).fetchone()
        if row is None:
            print(f"  WAARSCHUWING: '{name}' niet gevonden — overgeslagen.")
            continue
        s, t, aard = row
        conn.execute("UPDATE mechanisms SET aard='direct' WHERE name=?", (name,))
        print(f"  {name:30} {rn.get(s)} → {rn.get(t)}   [{aard} → direct]")
    conn.commit()

    print("\n== verificatie: mechanismen per aard ==")
    for aard, n in conn.execute(
            "SELECT aard, COUNT(*) FROM mechanisms GROUP BY aard ORDER BY aard"):
        print(f"  {aard:18} {n} mechanisme(n)")

    print("\n== resterende veld_instantiatie (blijven gestippeld) ==")
    for name, s, t in conn.execute("""
        SELECT name, source_role_id, target_role_id
        FROM mechanisms WHERE aard='veld_instantiatie' ORDER BY name"""):
        print(f"  {name:30} {rn.get(s)} ··· {rn.get(t)}")
    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
