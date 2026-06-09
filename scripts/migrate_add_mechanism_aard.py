"""
Modelreview — `aard` op mechanismen: direct vs. veld-instantiatie vs. veld-eigenschap.

Veel relaties in de instantielaag zijn géén concreet invloedskanaal tussen twee actoren,
maar een *emergente* eigenschap van het hele systeem die als dyadische pijl is uitgewaaierd.
Drie niveaus, vastgelegd op het MECHANISME (relaties erven het):

  • direct (niveau 0)        — lokaal feit; de oorzaak ís de twee eindpunten.
                               (eigendom, draaideur, advertentiedruk, bronafhankelijkheid,
                                benoemingen, en de *specifieke* flak-daden met een echte dader.)
                               Dat `eigendomsconcentratie` als thema 'systemisch' draagt is hier
                               misleidend: de edge (DPG → Het Parool) is een lokaal eigendomsfeit;
                               alleen de concentratie-*lezing* (de optelsom) is emergent.

  • veld_instantiatie (1)    — de dyade is een willekeurige steekproef uit een veld-regelmaat;
                               de eindpunten zijn substitueerbaar en de oorzaak is de configuratie
                               van het hele veld, niet de bron. (WEF/NAVO → uitlaten; elites die
                               onderling synchroniseren.) De pijl is waar als steekproef, maar
                               optellen inflateert de centraliteit van de bron.

  • veld_eigenschap (2)      — er ís geen zinnige externe bron; de "bron" is verzonnen. Hoort een
                               eigenschap ván de getroffen node te zijn, geen A→B-pijl.
                               (zelfcensuur — de redactie censureert zichzelf; geweld/intimidatie
                               met bewust diffuse bron; en de zuivere systeemmechanismen.)

Effect in de invloed-wiskunde (`influence.py`): niveau 1 telt als één gedempte bijdrage per
bron (fan-out gedeeld door k) i.p.v. N losse duwen; niveau 2 telt niet mee als uitgaande
invloed (node-eigenschap). In de viz: niveau 1 = diffuse waaier (toggle), niveau 2 = halo.

Idempotent; backup-then-migrate. Default voor alle niet-genoemde mechanismen blijft 'direct'.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# Mechanisme-naam -> aard. Alles wat hier niet staat = 'direct' (de kolom-default).
VELD_INSTANTIATIE = [
    "hegemonische_naturalisatie",   # WEF/NAVO → uitlaten (substitueerbaar, geen centrale zender)
    "ideologische_synchronisatie",  # elites → willekeurige elite-nodes
    "schijndebat",                  # veld-eigenschap van het debat zelf
    "omroepverzuiling",             # structurele veld-regelmaat (twijfelgeval, bewust niveau 1)
    "stakeholder_capitalism_frame", # elite-frame → publiek; diffuse normalisatie, geen dyade
]
VELD_EIGENSCHAP = [
    "zelfcensuur",                  # geen externe zender; nu kunstmatig aan de eigenaar geknoopt
    "geweld_intimidatie",           # spec: bron bewust diffuus gelaten
    "emergente_bias",               # zuiver systeemmechanisme (0 edges)
    "systemische_homeostase",       # idem
    "economische_feedback_loop",    # idem
]


def backup_db():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{timestamp}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def column_exists(conn, table, column):
    return any(r[1] == column for r in conn.execute(f"PRAGMA table_info({table})"))


def set_aard(conn, names, aard):
    for name in names:
        cur = conn.execute("UPDATE mechanisms SET aard = ? WHERE name = ?", (aard, name))
        if cur.rowcount == 0:
            print(f"  WAARSCHUWING: mechanisme '{name}' niet gevonden — overgeslagen.")
        else:
            print(f"  {name} → {aard}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    if not column_exists(conn, "mechanisms", "aard"):
        conn.execute("ALTER TABLE mechanisms ADD COLUMN aard TEXT NOT NULL DEFAULT 'direct'")
        print("Kolom toegevoegd: mechanisms.aard (default 'direct')")
    else:
        print("Kolom mechanisms.aard bestond al — alleen herclassificeren.")

    # Reset naar default, dan de twee niet-directe niveaus zetten (idempotent).
    conn.execute("UPDATE mechanisms SET aard = 'direct'")
    print("\nVeld-instantiaties (niveau 1):")
    set_aard(conn, VELD_INSTANTIATIE, "veld_instantiatie")
    print("\nVeld-eigenschappen (niveau 2):")
    set_aard(conn, VELD_EIGENSCHAP, "veld_eigenschap")

    conn.commit()

    print("\n== verificatie: mechanismen per aard ==")
    for aard, n in conn.execute(
            "SELECT aard, COUNT(*) FROM mechanisms GROUP BY aard ORDER BY aard"):
        print(f"  {aard:18} {n} mechanisme(n)")

    print("\n== verificatie: relaties (edges) per aard ==")
    rows = conn.execute("""
        SELECT COALESCE(m.aard, 'direct') AS aard, COUNT(*) AS n
        FROM relations r LEFT JOIN mechanisms m ON m.id = r.mechanism_id
        GROUP BY aard ORDER BY n DESC""").fetchall()
    for aard, n in rows:
        print(f"  {aard:18} {n} edge(s)")
    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
