"""Maak het onderscheid draaideur ↔ partijbinding consistent in de theorielaag.

Aanleiding (modelreview juni 2026): de tekst van `draaideur_politiek_media` (96)
zegt zelf dat de BESTUURLIJKE landing (RvT/RvB) via `draaideur_politiek_institutie`
(95) en `politieke_benoeming_omroeptop` (99) loopt, maar in de praktijklaag hingen
veertien bestuurlijke landingen tóch op 96. Bovendien benoemden de beschrijvingen
van de draaideur-familie en `partijbinding` (163) hun onderlinge verschil nergens
(loopbaanbeweging vs. staande band), en vermengde 96 de partijband zelfs in de
draaideur ("of partijgebonden figuur").

Wijzigingen (alleen herclassificatie en theorieteksten; geen nieuwe elementen):
1. Veertien bestuurlijke landingen (politicus → omroep-RvT/RvB) van 96 → 95,
   inclusief hun instantiations. 95 dekt dit per eigen tekst al ("bestuurder/
   toezichthouder van een (semi-)publiek instituut").
2. Relatie 378 (Rijxman —cooptatie→ OCW: persoonlijke verstrengeling, geen
   loopbaanbeweging) van 96 → 99 (verwevenheid omroeptop ↔ OCW).
3. Tekst 95: publieke omroep expliciet als voorbeeld benoemd.
4. Tekst 96: "of partijgebonden figuur" eruit; contrastpassage draaideur ↔
   partijbinding erin.
5. Tekst 163: contrastpassage met de draaideur-familie (kanaal, richting,
   onafhankelijkheid).
6. Mechanisme 18 (draaideurconstructie): filter `ideologie` → `cross_filter`
   (de effect-tekst zei dat al); extra filters aangevuld met `eigendom`.
7. Thema's voor 163: `omroepbestel` + `benoemingsketen`.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "propaganda_model.db"

BESTUURLIJKE_LANDINGEN = [377, 380, 382, 384, 386, 441, 443, 445, 447, 449, 451, 455, 457, 459]
VERSTRENGELING_OCW = 378

TEKST_95 = (
    "Een bewindspersoon wordt bestuurder/toezichthouder van een (semi-)publiek "
    "instituut of ZBO — of omgekeerd komt een institutiebestuurder uit de "
    "gereguleerde sector. Hieronder valt ook de bestuurlijke laag van het "
    "omroepbestel: raden van toezicht en besturen van NPO, NOS en ledenomroepen. "
    "Benoemingen lopen langs partijlijnen."
)

TEKST_96 = (
    "Een (oud-)politicus belandt in de redactioneel-inhoudelijke laag: als "
    "hoofdredacteur, vaste commentator, duider of presentator — of omgekeerd. Dit "
    "is de inhoud-landing van de draaideur, te onderscheiden van de bestuurlijke "
    "landing (RvT/RvB), die via draaideur_politiek_institutie en "
    "politieke_benoeming_omroeptop loopt. De draaideur is een loopbaanbeweging: "
    "het kanaal is wat de persoon meeneemt (netwerk, insiderkennis, anticipatie "
    "op een terugkeer) en werkt partij-overstijgend. Een eventuele partijkaart is "
    "een aparte, staande kracht — zie partijbinding."
)

TOEVOEGING_163 = (
    " Te onderscheiden van de draaideur-mechanismen: een draaideur is een "
    "loopbaanbeweging (persoon → organisatie; meegenomen netwerk en insiderkennis; "
    "partij-overstijgend), partijbinding een staande band (partij → persoon; "
    "ideologische lijn en partijkaart als selectiesignaal; partij-specifiek). Ze "
    "bestaan onafhankelijk van elkaar — een partijloze topambtenaar kan draaien, "
    "een journalist kan partijlid zijn zonder ooit gedraaid te hebben — en "
    "versterken elkaar waar ze samenvallen."
)

CHANGED_BY = "maxime"


def log(conn, record_id, old, new, reason):
    conn.execute(
        """INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
           VALUES ('mechanisms', ?, 'updated', ?, ?, ?, ?)""",
        (record_id, CHANGED_BY, old, new, reason))


def main():
    backup = DB.with_name(f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")

    # 1. Bestuurlijke landingen: 96 -> 95 (relaties + instantiations)
    ph = ",".join("?" * len(BESTUURLIJKE_LANDINGEN))
    conn.execute(f"UPDATE relations SET mechanism_id = 95 WHERE id IN ({ph}) AND mechanism_id = 96",
                 BESTUURLIJKE_LANDINGEN)
    conn.execute(f"UPDATE instantiations SET mechanism_id = 95 WHERE relation_id IN ({ph}) AND mechanism_id = 96",
                 BESTUURLIJKE_LANDINGEN)
    for rid in BESTUURLIJKE_LANDINGEN:
        conn.execute(
            """INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
               VALUES ('relations', ?, 'updated', ?, '{"mechanism_id": 96}', '{"mechanism_id": 95}',
                       'Bestuurlijke landing (RvT/RvB) hoort per tekst van mechanisme 96 bij draaideur_politiek_institutie')""",
            (rid, CHANGED_BY))

    # 2. Rijxman-verstrengeling met OCW: 96 -> 99
    conn.execute("UPDATE relations SET mechanism_id = 99 WHERE id = ? AND mechanism_id = 96",
                 (VERSTRENGELING_OCW,))
    conn.execute("UPDATE instantiations SET mechanism_id = 99 WHERE relation_id = ? AND mechanism_id = 96",
                 (VERSTRENGELING_OCW,))
    conn.execute(
        """INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
           VALUES ('relations', ?, 'updated', ?, '{"mechanism_id": 96}', '{"mechanism_id": 99}',
                   'Persoonlijke verstrengeling omroeptop-OCW is geen loopbaanbeweging; hoort bij de benoemingsketen-verwevenheid')""",
        (VERSTRENGELING_OCW, CHANGED_BY))

    # 3-5. Teksten
    oud95 = conn.execute("SELECT description FROM mechanisms WHERE id = 95").fetchone()[0]
    conn.execute("UPDATE mechanisms SET description = ? WHERE id = 95", (TEKST_95,))
    log(conn, 95, oud95, TEKST_95, "Publieke omroep expliciet benoemd als (semi-)publiek instituut")

    oud96 = conn.execute("SELECT description FROM mechanisms WHERE id = 96").fetchone()[0]
    conn.execute("UPDATE mechanisms SET description = ? WHERE id = 96", (TEKST_96,))
    log(conn, 96, oud96, TEKST_96,
        "Partijband uit de draaideurtekst gehaald; contrast met partijbinding geexpliciteerd")

    oud163 = conn.execute("SELECT description FROM mechanisms WHERE id = 163").fetchone()[0]
    if "loopbaanbeweging" not in oud163:
        conn.execute("UPDATE mechanisms SET description = description || ? WHERE id = 163",
                     (TOEVOEGING_163,))
        log(conn, 163, oud163, oud163 + TOEVOEGING_163,
            "Contrast met de draaideur-familie geexpliciteerd")

    # 6. draaideurconstructie: primair filter cross_filter (effect-tekst zei dit al)
    conn.execute("UPDATE mechanisms SET filter = 'cross_filter' WHERE id = 18")
    conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) VALUES (18, 'eigendom')")
    log(conn, 18, '{"filter": "ideologie"}', '{"filter": "cross_filter"}',
        "Effect-tekst benoemt het mechanisme al als cross_filter; extra filter eigendom aangevuld")

    # 7. Thema's voor partijbinding
    conn.execute("INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) VALUES (163, 'omroepbestel')")
    conn.execute("INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) VALUES (163, 'benoemingsketen')")

    conn.commit()

    n95 = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id = 95").fetchone()[0]
    n96 = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id = 96").fetchone()[0]
    print(f"Relaties op 95 (draaideur_politiek_institutie): {n95}")
    print(f"Relaties op 96 (draaideur_politiek_media): {n96}")
    conn.close()
    print("Klaar.")


if __name__ == "__main__":
    main()
