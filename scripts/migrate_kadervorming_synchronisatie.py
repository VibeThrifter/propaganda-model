#!/usr/bin/env python3
"""
Migratie: elite_forum → politicus generiek en compleet.

Twee gebreken in het elite_forum-cluster (theorielaag hoort abstract te zijn,
"generiek in theorie, specifiek in praktijk" — vgl. migrate_genericize_elite_frames.py):

  1. `young_global_leaders` is de naam van één concreet WEF-programma, en de
     beschrijving somt concrete personen op (Rutte, Van Gennip, …) — dat is
     praktijklaag-/bewijsmateriaal. Het mechanisme zelf is generiek: elite-clubs
     hebben kadervormingsprogramma's voor aanstaande bestuurders (WEF YGL,
     Atlantik-Brücke Young Leaders, European Young Leaders, fellow-programma's
     van Trilaterale Commissie en Aspen). → hernoemd naar `politieke_kadervorming`;
     het YGL-programma en de gedocumenteerde deelnemers verhuizen naar een
     supporting argument in de discussieboom.

  2. Asymmetrie: gewone deelname-synchronisatie bestaat als terugpijl voor de
     mediaeigenaar (`ideologische_synchronisatie`), denktank en opiniemaker,
     maar niet voor de politicus — de enige forum→politicus-pijl was het
     trainingsprogramma. → nieuw mechanisme `politieke_synchronisatie`
     (elite_forum → politicus): doorlopende kalibratie van het referentiekader
     door deelname, los van kadervorming. Diffuse twijfel hoort in de
     certainty-score van instanties, niet in de aard — dus gewoon `direct`.

  3. `politicus_elite_netwerk` (politicus → forum, het lidmaatschapsfeit)
     verwees naar het YGL-programma; die verwijzing hoort bij de vormende
     terugpijlen en wordt vervangen door een verwijzing daarnaar.

Conform repo-conventie: eerst backup, dan muteren. Idempotent op naam.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-elite-forum-generiek-2026-06"

KADERVORMING_DESC = (
    "Het elite-forum selecteert en vormt aanstaande bestuurders via "
    "kadervormings-/talentprogramma's (nominatie en vetting door derden, geen "
    "zelfaanmelding; vorming in een gedeeld referentiekader vóór of vroeg in de "
    "loopbaan). Welke programma's en deelnemers dat concreet zijn, is "
    "praktijkmodel en discussieboom. Onderscheid met `politieke_synchronisatie`: "
    "kadervorming is de pijplijn vooraf, synchronisatie het doorlopende "
    "onderhoud bij zittende politici."
)
KADERVORMING_EFFECT = (
    "Politici nemen het elite-referentiekader mee in beleid en publieke "
    "uitingen — niet als opdracht maar als geïnternaliseerde vanzelfsprekendheid "
    "(selectie + socialisatie van aanstaande machtigen; deelname is geen sturing)."
)
KADERVORMING_ARG = (
    "Het WEF Young Global Leaders-programma is het best gedocumenteerde "
    "voorbeeld van politieke kadervorming door een elite-forum: nominatie en "
    "vetting door derden, geen zelfaanmelding, vorming in een gedeeld "
    "referentiekader. Gedocumenteerde Nederlandse (oud-)deelnemers: Mark Rutte, "
    "Karien van Gennip (YGL 2008), Ruben Brekelmans (2025), Mabel Wisse Smit "
    "en Marietje Schaake."
)
SYNCHRONISATIE = {
    "name": "politieke_synchronisatie",
    "filter": "ideologie",
    "mechanism_type": "psychologisch",
    "description": (
        "Elite-fora synchroniseren het wereldbeeld van zittende politici: "
        "deelname aan besloten bijeenkomsten (doorgaans onder de Chatham House "
        "Rule) kalibreert het referentiekader — los van kadervormings-"
        "programma's (`politieke_kadervorming`). Spiegelt "
        "`ideologische_synchronisatie` (mediaeigenaar): het lidmaatschapsfeit "
        "zelf is de omgekeerde pijl (`politicus_elite_netwerk`); of er "
        "werkelijk invloed terugloopt is de claim van déze pijl, en die twijfel "
        "zit in de certainty-score van de instanties. Welke fora dat concreet "
        "zijn, is praktijkmodel."
    ),
    "effect": (
        "Beleid en publieke uitingen bewegen binnen het elite-consensuskader "
        "zonder expliciete afspraak of opdracht."
    ),
}
POLITICUS_NETWERK_DESC = (
    "Politici nemen deel aan besloten elite-fora (Bilderberg, WEF/Davos, "
    "Trilaterale Commissie). Spiegelt `mediaeigenaar_elite_netwerk` en "
    "`belang_elite_netwerk`: dezelfde fora binden eigenaar, belanghebbende én "
    "politicus. Dit is het lidmaatschapsfeit (hoge certainty); de vormende "
    "werking terug loopt via `politieke_synchronisatie` en "
    "`politieke_kadervorming` (lage certainty)."
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
            raise SystemExit(f"FOUT: rol ontbreekt: {name}")
        return r[0]

    # ---- 1: young_global_leaders → politieke_kadervorming --------------------
    row = cur.execute(
        "SELECT id FROM mechanisms WHERE name='young_global_leaders'"
    ).fetchone()
    if row:
        mid = row[0]
        cur.execute(
            "UPDATE mechanisms SET name='politieke_kadervorming', description=?,"
            " effect=? WHERE id=?",
            (KADERVORMING_DESC, KADERVORMING_EFFECT, mid),
        )
        cur.execute(
            "INSERT INTO edit_log (table_name, record_id, action, changed_by,"
            " old_value, new_value, reason) VALUES ('mechanisms', ?, 'updated', ?,"
            " 'young_global_leaders', 'politieke_kadervorming',"
            " 'theorielaag generiek: programmanaam en deelnemers naar discussieboom')",
            (mid, CONTRIB),
        )
        print(f"~ mechanisme young_global_leaders → politieke_kadervorming (id {mid})")
    else:
        mid = cur.execute(
            "SELECT id FROM mechanisms WHERE name='politieke_kadervorming'"
        ).fetchone()
        mid = mid[0] if mid else None
        print("= young_global_leaders al hernoemd")

    # YGL-bewijs als supporting argument op het mechanisme (idempotent op claim)
    if mid and not cur.execute(
        "SELECT 1 FROM arguments WHERE mechanism_id=? AND claim LIKE"
        " 'Het WEF Young Global Leaders-programma%'", (mid,)
    ).fetchone():
        cur.execute(
            "INSERT INTO arguments (mechanism_id, stance, claim, status,"
            " contributed_by) VALUES (?, 'supporting', ?, 'ongecontroleerd', ?)",
            (mid, KADERVORMING_ARG, CONTRIB),
        )
        cur.execute(
            "INSERT INTO edit_log (table_name, record_id, action, changed_by,"
            " reason) VALUES ('arguments', ?, 'created', ?,"
            " 'YGL-deelnemers uit mechanismebeschrijving naar discussieboom')",
            (cur.lastrowid, CONTRIB),
        )
        print("+ argument: YGL-programma + deelnemers bij politieke_kadervorming")

    # ---- 2: politieke_synchronisatie (elite_forum → politicus) ---------------
    s = SYNCHRONISATIE
    if not cur.execute(
        "SELECT 1 FROM mechanisms WHERE name=?", (s["name"],)
    ).fetchone():
        cur.execute(
            "INSERT INTO mechanisms (name, filter, mechanism_type, description,"
            " effect, source_role_id, target_role_id, aard)"
            " VALUES (?,?,?,?,?,?,?,'direct')",
            (s["name"], s["filter"], s["mechanism_type"], s["description"],
             s["effect"], role_id("elite_forum"), role_id("politicus")),
        )
        new_id = cur.lastrowid
        cur.execute(
            "INSERT INTO mechanism_filters (mechanism_id, filter) VALUES (?, 'ideologie')",
            (new_id,),
        )
        cur.execute(
            "INSERT INTO mechanism_themes (mechanism_id, theme) VALUES (?, 'elite_netwerk')",
            (new_id,),
        )
        cur.execute(
            "INSERT INTO edit_log (table_name, record_id, action, changed_by,"
            " reason) VALUES ('mechanisms', ?, 'created', ?,"
            " 'terugpijl deelname-synchronisatie forum→politicus, spiegel van"
            " ideologische_synchronisatie')",
            (new_id, CONTRIB),
        )
        print(f"+ mechanisme politieke_synchronisatie (id {new_id})")
    else:
        print("= politieke_synchronisatie bestond al")

    # ---- 3: politicus_elite_netwerk zonder YGL-verwijzing --------------------
    n = cur.execute(
        "UPDATE mechanisms SET description=? WHERE name='politicus_elite_netwerk'",
        (POLITICUS_NETWERK_DESC,),
    ).rowcount
    print(f"{'~' if n else '!'} politicus_elite_netwerk beschrijving "
          f"{'bijgewerkt' if n else 'NIET GEVONDEN'}")

    con.commit()
    n_mech = cur.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    print(f"klaar: {n_mech} mechanismen")
    con.close()


if __name__ == "__main__":
    main()
