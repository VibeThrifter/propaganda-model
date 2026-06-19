#!/usr/bin/env python3
"""Structurele metadata-correctie van twee bronrecords (geen content, geen scores).

Er is geen API om titel/brontype van een bron te bewerken (alleen reliability+onderwerp
via /classificatie, en locaties toevoegen). Zulke bibliografische correcties zijn dus
maintainer-/migratiewerk. Twee gevallen:

  #3  Titel was geconfabuleerd: "De Nederlandse Nieuwsfabriek: Onthulling van het
      propagandamodel" bestaat niet. Auteur (Bergman, T.) en jaar (2014) wijzen
      eenduidig op zijn echte werk -> titel + uitgever gecorrigeerd. De ISBN-vindplaats
      (9789086596720) wordt apart via de API toegevoegd (vindplaats = bijdragepad).

  #49 Brontype was 'boek' terwijl het een interviewbundel is (Chomsky & Barsamian).
      Type 'boek' liet de klasse 'primair' niet toe; type 'interview' wél. Zo blijft de
      bron terecht 'primair' (een interview is een primaire bron) i.p.v. afgewaardeerd
      naar 'opinie'. Reliability blijft ongewijzigd.

Volgt de backup-then-migrate-conventie. Idempotent: draait twee keer zonder schade.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "propaganda_model.db"

BRON3_TITEL = ("The Dutch Media Monopoly: A Political-Economic Analysis of the Crisis "
               "in Journalism in the Netherlands")
BRON3_UITGEVER = "VU University Press"


def main():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB.parent / f"propaganda_model_backup_{stamp}.db"
    shutil.copy2(DB, backup)
    print(f"Back-up: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")

    wijzigingen = []

    # #3 — titel/uitgever corrigeren (auteur + jaar kloppen al)
    oud = conn.execute("SELECT title, publisher FROM sources WHERE id = 3").fetchone()
    if oud and oud[0] != BRON3_TITEL:
        conn.execute("UPDATE sources SET title = ?, publisher = ? WHERE id = 3",
                     (BRON3_TITEL, BRON3_UITGEVER))
        conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by,
                        old_value, new_value, reason)
                        VALUES ('sources', 3, 'updated', 'claude-code', ?, ?, ?)""",
                     (f'{{"title": "{oud[0]}"}}',
                      f'{{"title": "{BRON3_TITEL}", "publisher": "{BRON3_UITGEVER}"}}',
                      "structurele correctie: geconfabuleerde titel -> echte Bergman-2014-bron"))
        wijzigingen.append(f"#3 titel -> {BRON3_TITEL[:50]}...")

    # #49 — brontype boek -> interview (interviewbundel; houdt 'primair' geldig)
    oud49 = conn.execute("SELECT source_type FROM sources WHERE id = 49").fetchone()
    if oud49 and oud49[0] != "interview":
        conn.execute("UPDATE sources SET source_type = 'interview' WHERE id = 49")
        conn.execute("""INSERT INTO edit_log (table_name, record_id, action, changed_by,
                        old_value, new_value, reason)
                        VALUES ('sources', 49, 'updated', 'claude-code', ?, ?, ?)""",
                     (f'{{"source_type": "{oud49[0]}"}}', '{"source_type": "interview"}',
                      "structurele correctie: interviewbundel als brontype 'interview' (klasse 'primair' wordt geldig)"))
        wijzigingen.append("#49 brontype boek -> interview")

    conn.commit()
    conn.close()

    if wijzigingen:
        print("Doorgevoerd:")
        for w in wijzigingen:
            print(f"  - {w}")
    else:
        print("Niets te doen (al gecorrigeerd).")


if __name__ == "__main__":
    main()
