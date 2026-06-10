"""
Modelreview — `transnationale_frame_export` is geen dyadisch kanaal maar een veld-eigenschap.

Bevinding: het mechanisme stond als `direct` (elite_forum → mediaorganisatie), maar er is
geen handeling van forum naar redactie — het frame reist via personen en bronnen, en díé
kanalen bestaan al als eigen mechanismen (`ideologische_synchronisatie` voor de fora-gangers,
de bron-routines voor institutionele bronnen). Een aparte forum→org-pijl telt dat dubbel.
Erger: `influence.py` weegt edges op `influence` en negeert `certainty`, dus de 14
cert=0,05-instanties gaven de fora op vol gewicht (0,4–0,8) uitgaande centraliteit naar zes
mediaorganisaties elk. "Twijfel in de certainty-score" dempt de invloedsgraaf dus niet.

Per de aard-beslisvolgorde is dit regel 1: een eigenschap ván de mediaorganisatie (zij
opereert binnen het elite-referentiekader) met diffuse herkomst — een `veld_eigenschap`-halo,
zoals eerder `sociologische_homogeniteit` (migrate_sociologische_homogeniteit_halo.py).

Acties:
  1. `transnationale_frame_export` → `elite_referentiekader`; aard `direct` → `veld_eigenschap`
     (target = mediaorganisatie, source = elite_forum als diffuse herkomst); description/effect
     generiek — geen namen van fora meer in de theorielaag (vervolg op
     migrate_genericize_elite_frames.py). De instance-relaties blijven gekoppeld: het
     praktijkmodel tekent ze als gewone edges, maar ze tellen niet meer mee als uitgaande
     invloed (FIELD_PROPERTY wordt in build_adjacency overgeslagen).
  2. De relatie Gezond Verstand → NOS [oppositie] hoort hier niet (een oppositieblad dat zich
     afzet tegen de NOS-consensus "exporteert" geen elite-frame): mechanism_id → NULL.
  3. Zelfde naamopruiming in `ideologische_synchronisatie`: description noemde Bilderberg,
     WEF/Davos en ERT — generiek gemaakt; de concrete fora staan als "Frame: ..."-notities
     in het praktijkmodel.

Idempotent (matcht oude of nieuwe naam; skipt al-losgekoppelde relatie); backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

OLD_NAME = "transnationale_frame_export"
NEW_NAME = "elite_referentiekader"
SOURCE_ROLE = "elite_forum"
TARGET_ROLE = "mediaorganisatie"
AARD = "veld_eigenschap"
DESCRIPTION = (
    "Mediaorganisaties opereren binnen het referentiekader dat in transnationale elite-fora "
    "als consensus geldt: het pro-markt/pro-Atlantische wereldbeeld is het impliciete "
    "uitgangspunt van de verslaggeving, zonder dat één forum dat oplegt. Eigenschap ván de "
    "mediaorganisatie (halo) met diffuse herkomst; er is geen handeling van forum naar "
    "redactie — het frame reist via personen en bronnen (ideologische_synchronisatie, de "
    "bron-routines). Twijfel over de concrete instanties zit in hun certainty-score."
)
EFFECT = (
    "Frames die in besloten elite-fora als consensus gelden, verschijnen in de verslaggeving "
    "als neutrale, vanzelfsprekende uitgangspunten in plaats van als betwistbare politieke "
    "keuzes."
)

SYNC_NAME = "ideologische_synchronisatie"
SYNC_DESCRIPTION = (
    "Elite-fora synchroniseren het wereldbeeld van de transnationale elite: media-eigenaren, "
    "CEO's, politici en academici komen besloten samen (doorgaans onder de Chatham House "
    "Rule) en kalibreren daar hun referentiekader. Welke fora dat concreet zijn, is "
    "praktijkmodel (entiteiten met een \"Frame: ...\"-notitie)."
)

DETACH_SOURCE = "Gezond Verstand"
DETACH_TARGET = "NOS"
DETACH_TYPE = "oppositie"


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

    # 1. herclassificeren naar halo + genereik maken
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

    # 2. Gezond Verstand → NOS loskoppelen (geen elite-frame, maar oppositie ertegen)
    drow = conn.execute("""
        SELECT r.id FROM relations r
        JOIN entities e1 ON e1.id = r.source_id
        JOIN entities e2 ON e2.id = r.target_id
        WHERE r.mechanism_id = ? AND e1.name = ? AND e2.name = ? AND r.relation_type = ?""",
        (mid, DETACH_SOURCE, DETACH_TARGET, DETACH_TYPE)).fetchone()
    if drow:
        conn.execute("UPDATE relations SET mechanism_id=NULL WHERE id=?", (drow[0],))
        print(f"Losgekoppeld: {DETACH_SOURCE} → {DETACH_TARGET} [{DETACH_TYPE}] "
              f"(relatie {drow[0]}, mechanism_id → NULL).")
    else:
        print(f"{DETACH_SOURCE} → {DETACH_TARGET} al losgekoppeld (of niet gevonden).")

    # 3. ideologische_synchronisatie: namen uit de theorie-description
    srow = conn.execute(
        "SELECT id, description FROM mechanisms WHERE name=?", (SYNC_NAME,)).fetchone()
    if srow is None:
        print(f"WAARSCHUWING: '{SYNC_NAME}' niet gevonden — overgeslagen.")
    elif srow[1] == SYNC_DESCRIPTION:
        print(f"{SYNC_NAME}: description al generiek, overslaan.")
    else:
        conn.execute(
            "UPDATE mechanisms SET description=? WHERE id=?", (SYNC_DESCRIPTION, srow[0]))
        print(f"{SYNC_NAME}: description generiek gemaakt (geen forum-namen meer).")

    conn.commit()

    name, aard, s, t = conn.execute("""
        SELECT name, aard, (SELECT name FROM roles WHERE id=source_role_id),
               (SELECT name FROM roles WHERE id=target_role_id)
        FROM mechanisms WHERE id=?""", (mid,)).fetchone()
    print(f"\n→ {name} [{aard}]   {s} → {t}")
    nrel2 = conn.execute(
        "SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (mid,)).fetchone()[0]
    print(f"  instance-relaties nog gekoppeld: {nrel2} (verwacht {nrel - 1}).")

    print("\n== mechanismen per aard (controle) ==")
    for aard, n in conn.execute(
            "SELECT aard, COUNT(*) FROM mechanisms GROUP BY aard ORDER BY aard"):
        print(f"  {aard:18} {n}")
    conn.close()
    print("\nKlaar. Vergeet niet: python3 scripts/generate_viz.py")


if __name__ == "__main__":
    main()
