"""Migratie: floor invloed-prior naar 0.05 voor relaties zonder invloed-bewijs.

Achtergrond (eigenaarsbesluit juni 2026):
De zekerheid-as is "schuldig tot bewezen" — onbronnde relaties staan op
certainty 0.05 (migrate_unsourced_certainty.py) en de afgeleide score wordt
uit de discussieboom gehaald; de prior dient alleen als lage fallback. De
invloed-as miste die discipline: elke relatie droeg een met de hand gezette
`influence` (spreiding 0,15–0,9) zonder enig bewijs (0 argumenten met
property='influence' in het hele corpus). Dat zijn precies de "initiële
willekeurige scores" die het project niet wil.

Deze migratie maakt de invloed-as symmetrisch met de zekerheid-as:
relaties zónder invloed-bewijs krijgen influence = 0.05 (de "magnitude
onbekend"-vloer). De machinerie in scoring.py (`derived_influence`, M1.7)
tilt de invloed daarna alleen omhoog via `property='influence'`-argumenten —
net zoals citaties de zekerheid optillen. De vloer is bewust 0.05 en niet 0,
zodat de invloedsgraaf (influence.py) de *topologie* blijft meten (positie)
terwijl de *magnitude* eerlijk minimaal blijft tot ze onderbouwd is.

"Invloed-bewijs" = minstens één niet-verworpen, niet-voorgesteld
root-argument met property='influence' op de relatie. Relaties met zulk
bewijs blijven ongemoeid (hun prior is geen willekeur meer maar een
verschuifbare basis). Oude influence-waarden worden in het edit_log bewaard
(naast de DB-backup), zodat ze herbruikbaar zijn als zoek-hypothese.

Conform repo-conventie: maakt eerst een backup van de DB. Dit is structuur,
geen inhoud (het reset een niet-onderbouwde prior, net als de
certainty-migratie) en valt daarmee buiten de dogfood-regel (M0.6).
"""
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

UNSOURCED_INFLUENCE = 0.05  # conventie: niet-onderbouwde invloed krijgt deze vloer


def migrate():
    # --- Backup ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # --- Relaties mét invloed-bewijs (verschuifbare prior) blijven ongemoeid ---
    evidenced = {row[0] for row in cur.execute(
        """SELECT DISTINCT relation_id FROM arguments
           WHERE relation_id IS NOT NULL
             AND property = 'influence'
             AND parent_argument_id IS NULL
             AND status NOT IN ('verworpen', 'voorgesteld')"""
    ).fetchall()}
    print(f"Relaties met invloed-bewijs (ongemoeid): {sorted(evidenced) or '∅'}")

    # --- Oude waarden bewaren (herbruikbaar als hypothese; naast de DB-backup) ---
    if evidenced:
        ph = ",".join("?" * len(evidenced))
        rows = cur.execute(
            f"""SELECT id, influence FROM relations
                WHERE NOT vervangen AND influence > ? AND id NOT IN ({ph})""",
            [UNSOURCED_INFLUENCE, *sorted(evidenced)],
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT id, influence FROM relations WHERE NOT vervangen AND influence > ?",
            [UNSOURCED_INFLUENCE],
        ).fetchall()
    oude_waarden = {rid: inf for rid, inf in rows}

    # --- Floor niet-onderbouwde invloed naar de vloer ---
    for rid in oude_waarden:
        cur.execute("UPDATE relations SET influence = ? WHERE id = ?",
                    (UNSOURCED_INFLUENCE, rid))
    print(f"influence → {UNSOURCED_INFLUENCE} voor {len(oude_waarden)} "
          f"relaties zonder invloed-bewijs.")

    # --- Audit log (summary + per-relatie oude waarde, herbruikbaar) ---
    summary = {
        "naar_influence": UNSOURCED_INFLUENCE,
        "aangepaste_relaties": len(oude_waarden),
        "relaties_met_bewijs_ongemoeid": sorted(evidenced),
        "oude_invloed_per_relatie": {str(k): v for k, v in oude_waarden.items()},
    }
    cur.execute(
        """INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
           VALUES ('relations', 0, 'updated', 'migratie', ?, ?)""",
        (json.dumps(summary, ensure_ascii=False),
         f"Invloed-as schuldig-tot-bewezen: {len(oude_waarden)} niet-onderbouwde "
         f"invloed-priors gefloord naar {UNSOURCED_INFLUENCE} (symmetrisch met de "
         f"certainty-vloer); oude waarden bewaard voor hergebruik als hypothese."),
    )

    conn.commit()
    conn.close()
    print("Klaar.")


if __name__ == "__main__":
    migrate()
