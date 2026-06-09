"""
Modelreview — `hegemonische_naturalisatie` was verkeerd gericht: omdraaien naar elite→media.

Bevinding: het theorie-mechanisme stond als `veld_instantiatie` (gestippelde waaier)
`mediaorganisatie → publiek` — als systeemeigenschap vrijwel identiek aan
`systemische_homeostase` + `emergente_bias` (drie keer "het systeem houdt elite-consensus in
stand"), dus redundant. MAAR de 14 instance-relaties eronder gaan niet media→publiek; ze gaan
ELITE → MEDIA: WEF/NAVO → NOS, Volkskrant, NRC, Telegraaf, RTL, AD, DPG, Mediahuis (+ Gezond
Verstand → NOS), allemaal cert=0,05 (de bewust-speculatieve, systemische claim dat
transnationale fora de NL-media ideologisch beïnvloeden).

De bug was dus de RICHTING van de theorie-pijl, niet het bestaan van het effect. Fix:
  • hernoemen  hegemonische_naturalisatie → transnationale_frame_export
  • herrichten  elite_forum → mediaorganisatie  (zoals de 14 relaties feitelijk lopen)
  • aard        veld_instantiatie → direct  (gerichte instroom vanuit de fora; de gestippelde
                media→publiek-waaier verdwijnt)
De 14 relaties blijven gekoppeld (mechanism_id ongewijzigd). De systeem-eigenschap "wordt
vanzelfsprekend bij het publiek" blijft bij emergente_bias / systemische_homeostase.

Idempotent (matcht oude of nieuwe naam); backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

OLD_NAME = "hegemonische_naturalisatie"
NEW_NAME = "transnationale_frame_export"
SOURCE_ROLE = "elite_forum"
TARGET_ROLE = "mediaorganisatie"
AARD = "direct"
DESCRIPTION = (
    "Transnationale elite-fora (WEF/Davos, NAVO-gerelateerde netwerken) exporteren hun "
    "ideologische frame naar de nieuwsmedia: het pro-markt/pro-Atlantische referentiekader "
    "wordt het impliciete uitgangspunt van de verslaggeving. Gerichte maar diffuse, moeilijk "
    "hard te maken invloed (vandaar de lage certainty op de instanties): van het forum náár de "
    "media, niet andersom. Dat het frame vervolgens bij het publiek vanzelfsprekend wórdt is de "
    "systeemeigenschap (emergente_bias / systemische_homeostase); dit mechanisme is specifiek "
    "de gerichte instroom vanuit de fora."
)
EFFECT = (
    "Frames die in besloten elite-fora als consensus gelden (stakeholder capitalism, "
    "Atlantische veiligheidslogica) verschijnen in de media als neutrale, vanzelfsprekende "
    "uitgangspunten in plaats van als betwistbare politieke keuzes."
)


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

    role_id = {n: i for i, n in conn.execute("SELECT id, name FROM roles")}
    sid, tid = role_id.get(SOURCE_ROLE), role_id.get(TARGET_ROLE)
    if sid is None or tid is None:
        raise SystemExit(f"FOUT: rol ontbreekt ({SOURCE_ROLE}={sid}, {TARGET_ROLE}={tid}).")

    row = conn.execute(
        "SELECT id, name FROM mechanisms WHERE name IN (?, ?)", (OLD_NAME, NEW_NAME)).fetchone()
    if row is None:
        raise SystemExit(f"FOUT: mechanisme '{OLD_NAME}'/'{NEW_NAME}' niet gevonden.")
    mid, cur_name = row
    nrel = conn.execute(
        "SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (mid,)).fetchone()[0]
    print(f"Mechanisme gevonden: '{cur_name}' (id={mid}) met {nrel} instance-relatie(s).")

    conn.execute(
        "UPDATE mechanisms SET name=?, source_role_id=?, target_role_id=?, aard=?, "
        "description=?, effect=? WHERE id=?",
        (NEW_NAME, sid, tid, AARD, DESCRIPTION, EFFECT, mid))
    conn.commit()

    name, aard, s, t = conn.execute("""
        SELECT name, aard, (SELECT name FROM roles WHERE id=source_role_id),
               (SELECT name FROM roles WHERE id=target_role_id)
        FROM mechanisms WHERE id=?""", (mid,)).fetchone()
    print(f"\n→ {name} [{aard}]   {s} → {t}")
    nrel2 = conn.execute(
        "SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (mid,)).fetchone()[0]
    print(f"  instance-relaties nog gekoppeld: {nrel2} (verwacht {nrel}).")

    print("\n== resterende veld_instantiatie (gestippelde waaiers) ==")
    rest = conn.execute(
        "SELECT name FROM mechanisms WHERE aard='veld_instantiatie' ORDER BY name").fetchall()
    for (n,) in rest:
        print("  ", n)
    print(f"  totaal: {len(rest)}")
    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
