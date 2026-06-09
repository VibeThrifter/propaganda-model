"""
Modelreview — `indirect` opheffen: een edge tussen twee nodes is `direct`.

Conceptueel punt (van de gebruiker): "indirect" is geen eigenschap van een EDGE maar van
een PAD. Een enkele getekende pijl A→B verbindt A en B rechtstreeks — dat ís een directe
verbinding. De `indirect`-aard tekende een gerichte dyade (pijlpunt, twee nodes) als
gestippeld "gemedieerd", maar dat was een visuele gloss op wat structureel gewoon een
directe edge is. Elke `indirect`-pijl in het model is zo'n 2-node-dyade.

Dus: alle `aard='indirect'` → `aard='direct'`. Ze worden gewone doorgetrokken pijlen,
altijd zichtbaar (niet meer onder de toggle).

Waar het "kleine, gemedieerde" effect dan leeft: in de KETEN zelf (de echte pijlen door de
tussennodes, bv. mediaeigenaar → STAK → RvC → directie) en in de demping van `influence.py`
(elke hop ×<1, dus een pad van 3 hops ≈ 0,4³ ≈ 0,06 — klein). De "indirectheid" emergeert
daar uit de padlengte, niet uit een edge-type.

Wat NIET verandert (geen 2-node-dyade, dus jouw regel raakt ze niet):
  • veld_instantiatie  — gestippelde waaier zónder pijlpunt; steekproef uit een regelmaat,
                         eindpunten verwisselbaar. Houdt zijn viz.
  • veld_eigenschap    — halo om één node (eigenschap ván de node).
  • emergent_effects   — gouden groepsveld (hyperedge, eigen tabellen).

`influence.py` verandert niet: een `indirect`-edge telde daar al als gewone gerichte edge,
dus de invloedscijfers blijven gelijk. Idempotent (tweede run: 0 rijen); backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


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

    rows = conn.execute("""
        SELECT m.name, (SELECT name FROM roles WHERE id = m.source_role_id),
               (SELECT name FROM roles WHERE id = m.target_role_id), m.filter
        FROM mechanisms m WHERE m.aard = 'indirect' ORDER BY m.name""").fetchall()

    if not rows:
        print("Geen mechanismen met aard='indirect' — niets te doen (al direct).")
    else:
        print("Stippelpijlen (indirect, gerichte 2-node-dyades) → direct:")
        for name, s, t, f in rows:
            print(f"  {name:42} {s} → {t}   [{f}]")
        conn.execute("UPDATE mechanisms SET aard = 'direct' WHERE aard = 'indirect'")
        conn.commit()

    print("\n== verificatie: mechanismen per aard ==")
    for aard, n in conn.execute(
            "SELECT aard, COUNT(*) FROM mechanisms GROUP BY aard ORDER BY aard"):
        print(f"  {aard:18} {n} mechanisme(n)")

    rest = conn.execute("SELECT COUNT(*) FROM mechanisms WHERE aard='indirect'").fetchone()[0]
    print(f"\nResterend indirect: {rest} (verwacht 0).")

    print("\n== de échte stippellijnen blijven (veld_instantiatie, ongewijzigd) ==")
    for name, s, t, f in conn.execute("""
        SELECT m.name, (SELECT name FROM roles WHERE id = m.source_role_id),
               (SELECT name FROM roles WHERE id = m.target_role_id), m.filter
        FROM mechanisms m WHERE m.aard = 'veld_instantiatie' ORDER BY m.name"""):
        print(f"  {name:42} {s} ··· {t}   [{f}]")

    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
