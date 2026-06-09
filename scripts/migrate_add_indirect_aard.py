"""
Modelreview — vierde `aard`: `indirect` (gericht maar GEMEDIEERD effect).

De `aard`-as kende drie niveaus (zie migrate_add_mechanism_aard.py): `direct`,
`veld_instantiatie`, `veld_eigenschap`. Daartussen ontbrak een categorie die telkens
terugkwam bij de eigendoms-/benoemingsketen: een effect dat wél gericht is (A beïnvloedt
echt B) maar niet face-to-face — het loopt *via tussen-nodes*. De eigenaar raakt de
hoofdredacteur niet rechtstreeks; zijn voorkeur stroomt gemedieerd door de keten. Dat is
geen brute dyadisch feit (direct) en geen diffuus veld (veld_*), maar `indirect`.

Visuele grammatica die hiermee sluit (pijlpunt = gericht; doorgetrokken = onmiddellijk,
gestippeld = gemedieerd/diffuus):

    doorgetrokken + pijlpunt   →  direct             (DPG → Het Parool)
    gestippeld   + pijlpunt    →  INDIRECT           (STAK ⇢ RvC; org ⇢ hoofdredacteur)
    gestippeld   + géén punt    →  veld_instantiatie  (WEF ··· uitlaten)
    halo (geen edge)           →  veld_eigenschap    (zelfcensuur)
    transparant veld om groep  →  emergent_effects   (samenspel; hyperedge)

In de viz horen de indirecte pijlen bij de **indirecte & systemische** laag: ze vallen
onder dezelfde toggle als de waaiers/halo's/groepsvelden en worden als achtergrondlaag
áchter de gouden emergente velden getekend (gestippeld mét punt, filterkleur).

In de invloed-wiskunde (`influence.py`) verandert er NIETS: een `indirect`-edge telt als
gewone gerichte edge — de demping zit al in de (lagere) influence-waarde. `aard` is
orthogonaal aan het filter; het filter (en dus de kleur) blijft staan.

Live-DB: de kolom `mechanisms.aard` is destijds via ALTER TABLE toegevoegd ZONDER CHECK
(de CHECK staat alleen in schema.sql, voor verse builds). Een simpele UPDATE volstaat dus;
geen tabel-rebuild nodig. Idempotent; backup-then-migrate.

Seed (gericht-maar-gemedieerd, onomstreden):
  • stak_stemzeggenschap              (STAK → RvC): familiecontrole via gecertificeerde stemmen
  • preselectie_hoofdredacteur        (mediaorganisatie → hoofdredacteur): ideologische voorselectie
                                       van de kandidatenpool — niet de benoeming zelf
  • academische_socialisatie_hoofdredacteur (kennisinstituut → hoofdredacteur): vormende socialisatie

Verdere kandidaten (bewust NIET automatisch gezet — opt-in als je 'm wilt uitbreiden):
  commissarisbenoeming (de beurs-route blijft direct als formeel benoemingsrecht; de
  familie-route stak_stemzeggenschap is juist de indirecte). Voeg toe aan INDIRECT als je
  de aandeelhouders-sturing ook als gemedieerd wilt tonen.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# Mechanisme-namen die `indirect` worden. Alles wat hier niet staat houdt zijn huidige aard.
INDIRECT = [
    "stak_stemzeggenschap",
    "preselectie_hoofdredacteur",
    "academische_socialisatie_hoofdredacteur",
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

    print("Mechanismen → aard 'indirect':")
    for name in INDIRECT:
        cur = conn.execute("UPDATE mechanisms SET aard = 'indirect' WHERE name = ?", (name,))
        if cur.rowcount == 0:
            print(f"  WAARSCHUWING: mechanisme '{name}' niet gevonden — overgeslagen.")
        else:
            print(f"  {name} → indirect")

    conn.commit()

    print("\n== verificatie: mechanismen per aard ==")
    for aard, n in conn.execute(
            "SELECT aard, COUNT(*) FROM mechanisms GROUP BY aard ORDER BY aard"):
        print(f"  {aard:18} {n} mechanisme(n)")

    print("\n== verificatie: de indirecte schakels ==")
    rows = conn.execute("""
        SELECT m.name, (SELECT name FROM roles WHERE id = m.source_role_id),
               (SELECT name FROM roles WHERE id = m.target_role_id), m.filter
        FROM mechanisms m WHERE m.aard = 'indirect' ORDER BY m.name""").fetchall()
    for name, s, t, f in rows:
        print(f"  {name:40} {s} ⇢ {t}   [{f}]")
    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
