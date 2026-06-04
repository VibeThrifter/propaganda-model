"""
Modelreview — twee structurele financieringskanalen NAAR de media toevoegen.

Vervolg op `migrate_add_mediafinanciering.py`. Onderzoek (EIB-leningen aan DPG; Big
Tech-journalistiekfondsen) laat zien dat de geldstroom-naar-media nóg twee zware,
systeembeïnvloedende kanalen kent die het model miste. Beide raken meerdere filters
tegelijk -> cross_filter. Laag 1 blijft generiek (archetypes als illustratie, in lijn
met de bestaande mechanisme-descripties); concrete bedragen/instanties horen in de
instantielaag mét bron. Idempotent; backup-then-migrate.

A. `publieke_groeifinanciering` (belanghebbende -> mediaorganisatie):
   Een publieke/supranationale instelling (m.n. EIB/EU) verstrekt grootschalige
   GROEILENINGEN aan een dominante uitgever, gekoppeld aan eigen beleidsprogramma's.
   Archetype: EIB -> DPG, ~€220 mln in twee tranches (2022 + 2024) voor o.a. het
   'Trusted Web'-advertentieplatform; eenzelfde patroon bij Bonnier (€100 mln).
   Effect cuts across F1 (consolidatie), F2 (data-/tracking-afhankelijkheid) en
   F5 (alignment met de instituties waarover men moet berichten).

B. `platform_journalistiekfinanciering` (techplatform -> mediaorganisatie):
   Big Tech financiert de pers deels terug die het eigen advertentiemodel ondermijnde —
   via fondsen (Google News Initiative, Meta Journalism Project, Digital News Initiative)
   en (deels afgedwongen) vergoedingen (bargaining codes). Effect: afhankelijkheid +
   co-optatie; versterkt `platform_advertentie_concentratie`/`platform_verdienmodel_druk`.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

MECHS = [
    {
        "name": "publieke_groeifinanciering",
        "filter": "cross_filter",
        "mechanism_type": "economisch",
        "source_role": "belanghebbende",
        "target_role": "mediaorganisatie",
        "description": (
            "Een publieke of supranationale instelling (m.n. de Europese Investeringsbank/EU) "
            "verstrekt grootschalige groeileningen aan een dominante media-uitgever, gekoppeld aan "
            "haar eigen beleidsprogramma's (EFSI/Investeringsplan voor Europa, Digital Europe). Geen "
            "gift maar krediet, bedoeld om de uitgever met Big Tech te laten concurreren via een "
            "eigen advertentie-/data-ecosysteem. Archetype: de EIB leende DPG Media in twee tranches "
            "~€220 mln (2022 + 2024), o.a. voor het 'Trusted Web'-advertentieplatform; eenzelfde "
            "patroon bij Bonnier (€100 mln). Zulke bedragen zijn alleen voor de allergrootste "
            "bereikbaar."
        ),
        "effect": (
            "Drievoudig structureel effect, zonder dat de geldschieter voorschrijft wát er geschreven "
            "wordt: (F1) de overheid/EU subsidieert de facto de consolidatie — kleine, lokale of "
            "onafhankelijke media kunnen niet aankloppen voor honderden miljoenen, zodat alternatieve "
            "stemmen verder marginaliseren; (F2) de aflossingsdruk duwt de uitgever dieper in "
            "datagedreven tracking-advertising (FTM/Bits of Freedom: profilering zonder 'informed "
            "consent'); (F5) zakelijke en ideologische verwevenheid — de grootste uitgever is voor "
            "zijn technologische toekomst afhankelijk van de instituties waarover hij geacht wordt "
            "kritisch te berichten."
        ),
    },
    {
        "name": "platform_journalistiekfinanciering",
        "filter": "cross_filter",
        "mechanism_type": "economisch",
        "source_role": "techplatform",
        "target_role": "mediaorganisatie",
        "description": (
            "Big Tech financiert de journalistiek deels terug die het eigen advertentiemodel "
            "ondermijnde: via fondsen (Google News Initiative ~$300 mln; Meta Journalism Project "
            "~$600 mln sinds 2018; de Europese Digital News Initiative €150 mln) en via (deels "
            "afgedwongen) vergoedingen voor nieuwsgebruik (Australische News Media Bargaining Code, "
            "Canadese Online News Act). Ook Nederlandse innovaties zijn zo gefinancierd."
        ),
        "effect": (
            "Afhankelijkheid en co-optatie: uitgevers worden milder over de platforms, richten "
            "innovatie en productkeuzes naar platformprioriteiten, en de pers raakt structureel "
            "afhankelijk van de partij die haar verdienmodel uitholde. Versterkt "
            "`platform_advertentie_concentratie` en `platform_verdienmodel_druk`."
        ),
    },
]


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


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    for m in MECHS:
        sid, tid = role_id(conn, m["source_role"]), role_id(conn, m["target_role"])
        exists = conn.execute("SELECT 1 FROM mechanisms WHERE name = ?", (m["name"],)).fetchone()
        if exists:
            conn.execute(
                """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
                   source_role_id=?, target_role_id=? WHERE name=?""",
                (m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid, m["name"]),
            )
            print(f"  bijgewerkt (bestond al): {m['name']}")
        else:
            conn.execute(
                """INSERT INTO mechanisms
                   (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid),
            )
            print(f"  toegevoegd: {m['name']} ({m['filter']}) {m['source_role']} → {m['target_role']}")

    conn.commit()
    print("\n== verificatie ==")
    for m in MECHS:
        row = conn.execute(
            """SELECT m.filter, sr.name, tr.name FROM mechanisms m
               JOIN roles sr ON sr.id=m.source_role_id JOIN roles tr ON tr.id=m.target_role_id
               WHERE m.name=?""", (m["name"],)
        ).fetchone()
        print(f"  {m['name']}: filter={row[0]}, {row[1]} → {row[2]}")
    n = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen: {n}.")


if __name__ == "__main__":
    main()
