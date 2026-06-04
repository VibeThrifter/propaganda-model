"""
Modelreview — twee ontbrekende financieringsrelaties naar de media toevoegen.

De geldstroom-NAAR-media was incompleet. Het model dekte eigendom (de keten) en
advertentie (`adverteerder`), maar niet de directe project-/giftfinanciering van media
door fondsen en stichtingen. Die bestaat echt (Open Society/PIJ, EMIF, Creative Europe,
SVDJ, FBJP, Journalismfund Europe, en SDM uit haar beleggingsrendement) en is — net als
alternatieve media — Janus-koppig: het hangt af van de MACHTSALIGNERING van de financier.

#1 FILTER — `externe_mediafinanciering` (belanghebbende -> mediaorganisatie, cross_filter):
   een elite-/agenda-gealigneerde financier (ideologisch fonds, filantroop, bedrijf,
   supranationaal programma) betaalt een titel rechtstreeks; de geldstroom stuurt
   onderwerpkeuze en kader. De eerste DIRECTE geldroute van de belanghebbende naar een
   medium (eerder alleen via adverteerder/lobbyist/denktank).

#2 TEGENMACHT — `projectfinanciering_journalistiek` (borgingsstichting -> onderzoeksjournalist):
   onafhankelijke persfondsen/stichtingen financieren onderzoeksjournalistiek die de
   commerciële filters anders wegbezuinigen; tegenwicht tegen `redactioneel_budgetcontrole`.
   SDM (uit beleggingsrendement, niet uit haar dividendloze DPG-belang) is het prototype;
   dedicated fondsen als SVDJ/FBJP/Journalismfund spelen dezelfde rol.

Laag 1 blijft generiek (geen namen/instanties); concrete giften horen in de instantielaag
met bronvermelding. Geen schemawijziging; idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

MECHS = [
    {
        "name": "externe_mediafinanciering",
        "filter": "cross_filter",
        "mechanism_type": "economisch",
        "source_role": "belanghebbende",
        "target_role": "mediaorganisatie",
        "description": (
            "Een belanghebbende (ideologisch fonds, filantroop, bedrijf, supranationaal programma) "
            "financiert een mediaorganisatie rechtstreeks via giften, project- of programmasubsidies "
            "— buiten eigendom en advertentie om. Anders dan de neutrale persfondsen (zie "
            "`projectfinanciering_journalistiek`, tegenmacht) is deze financier elite-/agenda-"
            "gealigneerd: de geldstroom stuurt onderwerpkeuze en kader (bv. thematische fondsen rond "
            "'desinformatie'/factchecking, programmasubsidies met een inhoudelijke agenda). NB: een "
            "concrete claim als 'fonds X betaalt titel Y' hoort als instantie mét bron, niet als "
            "generieke aanname."
        ),
        "effect": (
            "Financiële afhankelijkheid van een agenda-gebonden geldstroom: redacties richten zich "
            "(deels) naar de thema's en kaders die de financier beloont; herkomst en inhoudelijke "
            "voorwaarde blijven voor het publiek meestal onzichtbaar."
        ),
    },
    {
        "name": "projectfinanciering_journalistiek",
        "filter": "tegenmacht",
        "mechanism_type": "economisch",
        "source_role": "borgingsstichting",
        "target_role": "onderzoeksjournalist",
        "description": (
            "Onafhankelijke persfondsen en stichtingen financieren onderzoeksjournalistiek die de "
            "commerciële filters anders wegbezuinigen — projectgebonden, niet als exploitatiesteun. "
            "Prototype is SDM, dat grants betaalt uit haar beleggingsrendement (niet uit haar "
            "dividendloze DPG-belang); dedicated fondsen als het Stimuleringsfonds voor de "
            "Journalistiek (SVDJ), het Fonds Bijzondere Journalistieke Projecten en Journalismfund "
            "Europe spelen dezelfde rol."
        ),
        "effect": (
            "Tegenwicht tegen `redactioneel_budgetcontrole`: diepgravend, langlopend onderzoek wordt "
            "mogelijk dat binnen het rendementsregime van de eigenaar geen ruimte krijgt. Geen "
            "structurele garantie — het blijft projectgeld, afhankelijk van toekenning."
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
