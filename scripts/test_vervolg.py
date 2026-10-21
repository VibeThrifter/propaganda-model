#!/usr/bin/env python3
"""Test vervolg.py (2026-10-15): werk dat op een theorie-element wacht, draait zodra het er is.

Tijdelijke repo-map en database; de echte data/vervolg en de live database worden niet geraakt.
    python3 scripts/test_vervolg.py
"""
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vervolg  # noqa: E402

FOUTEN = []


def eis(conditie, melding):
    print(("  ok — " if conditie else "  FAAL: ") + melding)
    if not conditie:
        FOUTEN.append(melding)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "scripts").mkdir()
        (root / "data" / "vervolg").mkdir(parents=True)
        db = root / "data" / "model.db"
        c = sqlite3.connect(db)
        c.executescript("""
            CREATE TABLE mechanisms (id INTEGER PRIMARY KEY, name TEXT, vervangen BOOLEAN DEFAULT 0);
            CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT, vervangen BOOLEAN DEFAULT 0);
            CREATE TABLE voorstellen (id INTEGER PRIMARY KEY, soort TEXT, status TEXT, payload TEXT);
        """)
        c.execute("INSERT INTO voorstellen VALUES (1, 'nieuw_theorie_element', 'open', ?)",
                  (json.dumps({"element_type": "mechanisme", "naam": "nieuw_mech"}),))
        c.commit()
        for naam, code in (("ok.py", 0), ("wacht.py", 3), ("kapot.py", 1)):
            (root / "scripts" / naam).write_text(
                f"import sys\nprint('uitvoer van {naam}', sys.argv[1:])\nsys.exit({code})\n")
        buiten = root / "elders.py"
        buiten.write_text("print('mag niet')\n")
        vervolg.ROOT = root
        map_ = root / "data" / "vervolg"

        def stap(naam, wacht_op, commando):
            (map_ / naam).write_text(json.dumps({"beschrijving": naam, "wacht_op": wacht_op,
                                                 "commando": commando}))

        stap("1_wacht_op_rfc.json", [{"mechanisme": "nieuw_mech"}], ["scripts/ok.py"])
        stap("2_vervalt.json", [{"rol": "bestaat_nergens"}], ["scripts/ok.py"])
        stap("3_buiten_repo.json", [], ["elders.py"])
        stap("4_wacht_zelf.json", [], ["scripts/wacht.py"])
        stap("5_kapot.json", [], ["scripts/kapot.py"])
        tel = vervolg.draai(meld=lambda *_: None, map_=map_, db_path=db)
        eis((map_ / "1_wacht_op_rfc.json").exists(), "wacht op een element dat een open RfC voorstelt")
        eis((map_ / "vervallen" / "2_vervalt.json").exists(),
            "vervalt als niets het element nog maakt (geen open RfC)")
        eis((map_ / "fout" / "3_buiten_repo.json").exists(), "een script buiten scripts/tools/data/scout draait niet")
        eis((map_ / "4_wacht_zelf.json").exists(), "exit 3: het script wacht zelf nog, blijft staan")
        kapot = json.loads((map_ / "fout" / "5_kapot.json").read_text())
        eis(kapot["exit"] == 1 and "uitvoer van kapot.py" in kapot["uitvoer"], "exit ≠ 0/3 → fout, met de uitvoer")
        eis(tel == {"klaar": 0, "wacht": 2, "fout": 2, "vervallen": 1}, f"telling klopt ({tel})")

        c.execute("INSERT INTO mechanisms (name) VALUES ('nieuw_mech')")
        c.execute("UPDATE voorstellen SET status = 'geaccepteerd'")
        c.commit()
        stap("1_wacht_op_rfc.json", [{"mechanisme": "nieuw_mech"}], ["scripts/ok.py", "--indienen"])
        vervolg.draai(meld=lambda *_: None, map_=map_, db_path=db, droog=True)
        eis((map_ / "1_wacht_op_rfc.json").exists(), "droog: niets uitgevoerd of verplaatst")
        vervolg.draai(meld=lambda *_: None, map_=map_, db_path=db)
        klaar = json.loads((map_ / "klaar" / "1_wacht_op_rfc.json").read_text())
        eis(klaar["exit"] == 0 and "['--indienen']" in klaar["uitvoer"],
            "na aanname draait het script met zijn argumenten en gaat het naar klaar/")
        c.close()
    if FOUTEN:
        print(f"\n{len(FOUTEN)} fout(en)")
        sys.exit(1)
    print("\nVervolg: alles groen.")


if __name__ == "__main__":
    main()
