#!/usr/bin/env python3
"""
Migratie: 'lobbymakelaardij' als emergent veld (hyperedge).

Het kerngebaar uit Luyendijks "Je hebt het niet van mij, maar..." is geen dyade
en geen los pad, maar een georkestreerde driehoek: de lobbyist koppelt journalist
en politicus aan elkaar NAMENS een belanghebbende die zelf buiten beeld blijft.
De losse edges bestaan al (belangenbehartiging, lobbyist_naar_politicus,
lobbyist_naar_journalist, media_agendering) en de afgeleide stippelpijlen tonen
de gedempte padinvloed — maar de gelijktijdige regie over béíde kanten is een
eigenschap van de groep en hoort dus in de emergentielaag (goud veld), naast
haagse_stam (waar de belanghebbende juist géén lid van is).

Conform repo-conventie: backup-then-migrate; idempotent op naam.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

LEDEN = ["belanghebbende", "lobbyist", "politicus", "journalist"]
DESC = (
    "De lobbyist als makelaar: hij koppelt journalist en politicus aan elkaar "
    "namens een belanghebbende die zelf buiten beeld blijft — het verhaal wordt "
    "bij de journalist geplant ('je hebt het niet van mij, maar...'), de "
    "Kamervraag bij de politicus aangeleverd. Publicatie en politieke reactie "
    "bevestigen elkaar vervolgens, terwijl ze dezelfde afzender hebben. De "
    "gelijktijdige regie over beide kanten is een eigenschap van de driehoek, "
    "niet van een losse edge of een los pad."
)
EFFECT = (
    "Het belang verschijnt tegelijk als onafhankelijk nieuws én als politiek "
    "feit; journalist noch politicus (noch het publiek) ziet de gezamenlijke "
    "regie. Zo heeft de belanghebbende indirecte maar georkestreerde invloed op "
    "beide — sterker dan de gedempte som van de losse paden suggereert."
)


def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = DB.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB, dst)
    print(f"backup -> {dst.name}")


def main():
    if not DB.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB}")
    backup()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    def role_id(name):
        r = cur.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
        if not r:
            raise SystemExit(f"rol ontbreekt: {name}")
        return r[0]

    cur.execute(
        "INSERT OR IGNORE INTO emergent_effects (name, label, category, description, effect) "
        "VALUES (?,?,?,?,?)",
        ("lobbymakelaardij", "Lobby-makelaardij", "sourcing", DESC, EFFECT),
    )
    eff_id = cur.execute(
        "SELECT id FROM emergent_effects WHERE name='lobbymakelaardij'").fetchone()[0]
    cur.execute(
        "UPDATE emergent_effects SET label=?, category=?, description=?, effect=? WHERE id=?",
        ("Lobby-makelaardij", "sourcing", DESC, EFFECT, eff_id),
    )
    cur.execute("DELETE FROM emergent_effect_members WHERE emergent_effect_id=?", (eff_id,))
    for rn in LEDEN:
        cur.execute(
            "INSERT OR IGNORE INTO emergent_effect_members (emergent_effect_id, role_id) VALUES (?,?)",
            (eff_id, role_id(rn)),
        )
    con.commit()
    print(f"+ emergent effect lobbymakelaardij ({len(LEDEN)} leden: {', '.join(LEDEN)})")

    n_eff = cur.execute("SELECT COUNT(*) FROM emergent_effects").fetchone()[0]
    n_mem = cur.execute("SELECT COUNT(*) FROM emergent_effect_members").fetchone()[0]
    con.close()
    print(f"Klaar: {n_eff} emergente effecten, {n_mem} lidmaatschappen.")


if __name__ == "__main__":
    main()
