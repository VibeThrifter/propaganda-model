"""
Modelreview — correctheid van het theoretische model (mechanismen), ronde C.

Na de ontdubbeling (ronde A+B, migrate_dedup_mechanisms.py) corrigeert deze ronde de
mechanismen die WRINGEN met de literatuur — vooral verkeerde filter-indeling t.o.v.
Herman & Chomsky's definitie van *flak* (een negatieve reactie op een mediastatement,
bedoeld om te disciplineren) en het media-studie-begrip *false balance* (bothsidesism:
een randstandpunt juist gelijk gewicht geven). Geen schemawijziging; alle filter-/rol-/
typewaarden bestaan al. Idempotent; volgt de backup-then-migrate-conventie.

C1  false_balance -> hernoemd 'schijndebat' (ideologie); `onevenwichtig_debat` erin
    samengevoegd. Beide beschreven dezelfde geënsceneerde-debat-dynamiek (één criticus
    tegenover een consensusfront) — dat is een gemanipuleerde *on*balans, niet 'false
    balance' (bothsidesism). Het ensceneren is discursief/ideologie, geen flak.
C2  woo_obstructie : flak -> sourcing, source-rol `gezagsinstituut`. WOO-traineren is
    een toegangsbarrière tot informatie (filter 3), geen reactie op een statement.
C3  alternatieve_uitdaging -> samengevoegd in `onafhankelijk_medium_tegenwicht`
    (tegenmacht). Alternatieve media die de mainstream uitdagen zijn tegenmacht, geen
    flak. Rol `alternatief_medium` verhuist mee van categorie `flak` -> `tegenmacht`.
C4  elite_forum_flak : VERWIJDERD (0 refs). 'Elite-fora bakenen het debat af' is geen
    flak maar ideologie, en is daar al gedekt door `spectrum_bewaking`,
    `ideologische_synchronisatie` en `etikettering`.
C5  sociologische_homogeniteit : flak -> ideologie. Homogene redactie -> blinde vlekken
    is een groepsdenk-/compositiekenmerk, geen disciplineringsreactie.
C6  hegemonische_naturalisatie : source-rol `denktank` -> `mediaorganisatie`. Gramsci's
    culturele hegemonie werkt systeembreed (media/onderwijs/civil society), niet
    specifiek vanuit denktanks; de description zei dat al.
C7  omroepverzuiling : target-rol `partij` -> `publiek`. De verzuiling kleurt de inhoud
    richting het publiek, niet de partij.
C8  draaideurconstructie : BEWUST ongemoeid. De koepel is load-bearing (19 relaties) en
    er is geen schone single-edge-verbetering; de familie levert al de details.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def backup_db():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{timestamp}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def role_id(conn, name):
    row = conn.execute("SELECT id FROM roles WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
    return row[0]


def mech_id(conn, name):
    row = conn.execute("SELECT id FROM mechanisms WHERE name = ?", (name,)).fetchone()
    return row[0] if row else None


def merge_mechanism(conn, loser_name, survivor_name):
    lid = mech_id(conn, loser_name)
    if lid is None:
        print(f"  '{loser_name}' bestaat niet meer — merge al gedaan, overgeslagen.")
        return
    sid = mech_id(conn, survivor_name)
    if sid is None:
        raise SystemExit(f"FOUT: survivor '{survivor_name}' niet gevonden.")
    n_rel = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (lid,)).fetchone()[0]
    n_ins = conn.execute("SELECT COUNT(*) FROM instantiations WHERE mechanism_id=?", (lid,)).fetchone()[0]
    n_arg = conn.execute("SELECT COUNT(*) FROM arguments WHERE mechanism_id=?", (lid,)).fetchone()[0]
    conn.execute("UPDATE relations SET mechanism_id=? WHERE mechanism_id=?", (sid, lid))
    conn.execute("UPDATE arguments SET mechanism_id=? WHERE mechanism_id=?", (sid, lid))
    conn.execute(
        """DELETE FROM instantiations WHERE mechanism_id=? AND relation_id IN
           (SELECT relation_id FROM instantiations WHERE mechanism_id=?)""",
        (lid, sid),
    )
    conn.execute("UPDATE instantiations SET mechanism_id=? WHERE mechanism_id=?", (sid, lid))
    conn.execute("DELETE FROM mechanisms WHERE id=?", (lid,))
    print(f"  '{loser_name}' (id {lid}) -> '{survivor_name}' (id {sid}); "
          f"omgehangen: {n_rel} rel, {n_ins} inst, {n_arg} arg.")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    n_before = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]

    # --- C1: false_balance -> schijndebat (hernoemen + herdefiniëren), dan merge 30 ---
    print("\n-- C1: false_balance -> schijndebat (+ onevenwichtig_debat) --")
    if mech_id(conn, "false_balance") is not None:
        conn.execute(
            """UPDATE mechanisms SET name='schijndebat', filter='ideologie',
                   mechanism_type='discursief', source_role_id=?, target_role_id=?,
                   description=?, effect=? WHERE name='false_balance'""",
            (
                role_id(conn, "mediaorganisatie"), role_id(conn, "publiek"),
                ("Een debat wordt zó geënsceneerd dat één criticus alleen staat tegenover een "
                 "overmacht aan consensus-stemmen (de klassieke talkshowtafel). Niet te verwarren "
                 "met het media-studie-begrip 'false balance' (bothsidesism, een randstandpunt juist "
                 "gelijk gewicht geven): dit is omgekeerd een gemanipuleerde ONbalans die de schijn "
                 "van open debat wekt."),
                ("Illusie van pluralisme binnen een smal ideologisch spectrum: de criticus oogt "
                 "onredelijk en geïsoleerd, terwijl de fundamentele aannames niet ter discussie staan."),
            ),
        )
        print("  hernoemd + geherdefinieerd: false_balance -> schijndebat")
    else:
        print("  'false_balance' al weg (schijndebat bestaat?) — hernoemen overgeslagen.")
    merge_mechanism(conn, "onevenwichtig_debat", "schijndebat")

    # --- C3: alternatieve_uitdaging -> onafhankelijk_medium_tegenwicht (eerst survivor verrijken) ---
    print("\n-- C3: alternatieve_uitdaging -> onafhankelijk_medium_tegenwicht --")
    conn.execute(
        """UPDATE mechanisms SET description=?, effect=? WHERE name='onafhankelijk_medium_tegenwicht'""",
        (
            ("Onafhankelijke media met een alternatief eigendoms-/verdienmodel bieden tegenwicht aan "
             "de commerciële filters en dagen de mainstream-consensus uit; ze appelleren aan een "
             "groeiend wantrouwen bij een publiek dat voelt dat het mediabeeld niet strookt met de "
             "eigen ervaring."),
            ("Diepgravende analyses en perspectieven die in de mainstream ontbreken — maar een deel "
             "van het alternatieve veld verspreidt feitelijk onjuiste content, waardoor legitieme "
             "kritiek besmet kan raken door associatie met extremen."),
        ),
    )
    merge_mechanism(conn, "alternatieve_uitdaging", "onafhankelijk_medium_tegenwicht")

    # rol alternatief_medium: flak -> tegenmacht
    cur = conn.execute("UPDATE roles SET category='tegenmacht' WHERE name='alternatief_medium'")
    print(f"  rol alternatief_medium -> categorie tegenmacht ({'ok' if cur.rowcount else 'niet gevonden'})")

    # --- C4: elite_forum_flak verwijderen (guard 0 relaties) ---
    print("\n-- C4: elite_forum_flak verwijderen --")
    eid = mech_id(conn, "elite_forum_flak")
    if eid is None:
        print("  al weg — overgeslagen.")
    else:
        n = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (eid,)).fetchone()[0]
        if n:
            print(f"  NIET verwijderd: {n} relaties hangen er nog aan.")
        else:
            conn.execute("DELETE FROM instantiations WHERE mechanism_id=?", (eid,))
            conn.execute("DELETE FROM arguments WHERE mechanism_id=?", (eid,))
            conn.execute("DELETE FROM mechanisms WHERE id=?", (eid,))
            print("  verwijderd (0 relaties): elite_forum_flak")

    # --- C2/C5/C6/C7: filter-/rol-correcties ---
    print("\n-- C2/C5/C6/C7: filter- en rol-correcties --")
    corrections = [
        ("C2 woo_obstructie -> sourcing + source gezagsinstituut",
         "UPDATE mechanisms SET filter='sourcing', source_role_id=? WHERE name='woo_obstructie'",
         (role_id(conn, "gezagsinstituut"),)),
        ("C5 sociologische_homogeniteit -> ideologie",
         "UPDATE mechanisms SET filter='ideologie' WHERE name='sociologische_homogeniteit'",
         ()),
        ("C6 hegemonische_naturalisatie -> source mediaorganisatie",
         "UPDATE mechanisms SET source_role_id=? WHERE name='hegemonische_naturalisatie'",
         (role_id(conn, "mediaorganisatie"),)),
        ("C7 omroepverzuiling -> target publiek",
         "UPDATE mechanisms SET target_role_id=? WHERE name='omroepverzuiling'",
         (role_id(conn, "publiek"),)),
    ]
    for label, sql, params in corrections:
        cur = conn.execute(sql, params)
        print(f"  {'ok' if cur.rowcount else 'NIET gevonden'}: {label}")

    conn.commit()

    # --- verificatie ---
    print("\n== verificatie ==")
    gone = conn.execute(
        "SELECT name FROM mechanisms WHERE name IN ('false_balance','onevenwichtig_debat','alternatieve_uitdaging','elite_forum_flak')"
    ).fetchall()
    print(f"  weg/hernoemd (verwacht leeg): {[r[0] for r in gone]}")
    for name in ("schijndebat", "woo_obstructie", "sociologische_homogeniteit",
                 "hegemonische_naturalisatie", "omroepverzuiling"):
        row = conn.execute(
            """SELECT m.filter, COALESCE(sr.name,'—'), COALESCE(tr.name,'—')
               FROM mechanisms m LEFT JOIN roles sr ON sr.id=m.source_role_id
               LEFT JOIN roles tr ON tr.id=m.target_role_id WHERE m.name=?""", (name,)
        ).fetchone()
        print(f"  {name}: filter={row[0]}, {row[1]} -> {row[2]}")
    altcat = conn.execute("SELECT category FROM roles WHERE name='alternatief_medium'").fetchone()[0]
    print(f"  rol alternatief_medium categorie: {altcat}")
    for tbl in ("relations", "instantiations"):
        orphan = conn.execute(
            f"SELECT COUNT(*) FROM {tbl} WHERE mechanism_id IS NOT NULL "
            f"AND mechanism_id NOT IN (SELECT id FROM mechanisms)"
        ).fetchone()[0]
        print(f"  verweesde {tbl}.mechanism_id (verwacht 0): {orphan}")

    n_after = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen: {n_before} -> {n_after} (−{n_before - n_after}).")


if __name__ == "__main__":
    main()
