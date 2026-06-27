"""Migratie: hang de twee standalone emergente velden alsnog onder de apex.

Achtergrond (juni 2026):
`gefinancierde_onafhankelijkheid` (voorstel 10) en `consensuscalibratie`
(voorstel 15) zijn via een RfC geaccepteerd en bedoeld als **deel-effect van
`fabricage_van_instemming`** (de apex) — beide payloads zeggen dat letterlijk
in hun afgrenzing/definitie. Maar de RfC-afhandeling (`voorstellen.py
_maak_element`) legde tot nu toe nooit een `emergent_effect_subeffects`-
koppeling: ze maakte alleen de veld-rij + leden. Daardoor bleven beide velden
*standalone* en verschenen ze niet in het apex-detailpaneel onder "Komt samen
uit deel-effecten".

`voorstellen.py` legt deze koppeling voortaan zelf (optioneel veld `deel_van`
in de RfC-payload). Deze migratie maakt de bestaande data daarmee consistent.

Geen score-effect: `scoring.py`/`influence.py` lezen geen deel-effect-koppeling
(alleen `generate_viz.py` doet dat, voor het detailpaneel). Het is dus
structuur/weergave, geen inhoud — en valt buiten de dogfood-regel (M0.6).

Conform repo-conventie: maakt eerst een backup van de DB. Idempotent
(INSERT OR IGNORE); herhaald draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

APEX = "fabricage_van_instemming"
KINDEREN = ["gefinancierde_onafhankelijkheid", "consensuscalibratie"]


def migrate():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    def veld_id(naam):
        rij = conn.execute("SELECT id FROM emergent_effects WHERE name = ?", (naam,)).fetchone()
        return rij["id"] if rij else None

    apex_id = veld_id(APEX)
    if apex_id is None:
        print(f"Apex '{APEX}' niet gevonden — niets te doen.")
        conn.close()
        return

    gekoppeld = 0
    for naam in KINDEREN:
        kind_id = veld_id(naam)
        if kind_id is None:
            print(f"  veld '{naam}' bestaat (nog) niet — overgeslagen.")
            continue
        al = conn.execute(
            "SELECT 1 FROM emergent_effect_subeffects "
            "WHERE parent_effect_id = ? AND child_effect_id = ?",
            (apex_id, kind_id)).fetchone()
        if al:
            print(f"  '{naam}' (#{kind_id}) hangt al onder de apex — overgeslagen.")
            continue
        conn.execute(
            "INSERT OR IGNORE INTO emergent_effect_subeffects "
            "(parent_effect_id, child_effect_id) VALUES (?, ?)",
            (apex_id, kind_id))
        print(f"  '{naam}' (#{kind_id}) → deel-effect van '{APEX}' (#{apex_id})")
        gekoppeld += 1

    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM emergent_effect_subeffects "
                     "WHERE parent_effect_id = ?", (apex_id,)).fetchone()[0]
    conn.close()
    print(f"{gekoppeld} nieuwe koppeling(en); apex draagt nu {n} deel-effecten.")
    print("Klaar.")


if __name__ == "__main__":
    migrate()
