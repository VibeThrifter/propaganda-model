"""
Modelreview — hegemonie-reproductie via het kennisinstituut breder bedraden.

Het kennisinstituut bleek maar twee uitgaande ideologische edges te hebben (journalist,
gezagsexpert), terwijl de 'diplomademocratie' (Bovens & Wille) laat zien dat de hoogopgeleide
elite ALLE instituties bevolkt en er een gedeeld wereldbeeld deelt — opleiding als 'nieuwe
verzuiling'. Dit is Gramsci's hegemonie-REPRODUCTIE: de universiteit vormt de hele
professioneel-bestuurlijke klasse.

Vier upstream-VORMINGSedges toegevoegd, telkens als ideologische pendant die een bestaande
OUTPUT-edge voedt (dus geen redundantie):
  - academische_socialisatie_politiek (kennisinstituut -> politicus)        voedt politicus_als_ideoloog
  - academische_orthodoxie_denktank   (kennisinstituut -> denktank)         pendant van denktank_financiering_bias
  - academische_orthodoxie_instituut  (kennisinstituut -> gezagsinstituut)  voedt institutioneel_gezag
  - academische_vorming_opinie        (kennisinstituut -> columnist_opiniemaker) voedt columnist_als_hegemon

Bewust NIET: hoofdredacteur (al via journalist), voorlichter; belanghebbende als optie open.
Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

NEW = [
    {
        "name": "academische_socialisatie_politiek",
        "filter": "ideologie",
        "mechanism_type": "structureel",
        "source_role": "kennisinstituut",
        "target_role": "politicus",
        "description": (
            "De politieke klasse is overwegend academisch gevormd: parlement, kabinet en adviesraden "
            "worden gedomineerd door hoogopgeleiden (Bovens & Wille, 'diplomademocratie'). Politici "
            "delen daardoor de premissen en het wereldbeeld van de academische hegemonie."
        ),
        "effect": (
            "Beleid en debat vertrekken vanuit het hoogopgeleide referentiekader (internationalisering, "
            "milieu, migratie) dat afwijkt van de praktisch geschoolden; voedt `politicus_als_ideoloog` "
            "en vergroot de kloof tussen burger en politiek."
        ),
    },
    {
        "name": "academische_orthodoxie_denktank",
        "filter": "ideologie",
        "mechanism_type": "structureel",
        "source_role": "kennisinstituut",
        "target_role": "denktank",
        "description": (
            "Denktank-onderzoekers zijn academisch gevormd (PhD's, oud-academici); hun analyses blijven "
            "binnen de heersende academische paradigma's. Dit is de IDEOLOGISCHE achtergrond, te "
            "onderscheiden van de FINANCIËLE sturing (`denktank_financiering_bias`)."
        ),
        "effect": (
            "De 'schijnbaar objectieve' denktank-output deelt de premissen van de academische "
            "consensus; heterodoxe paradigma's komen er nauwelijks in. Versterkt het aureool van "
            "neutraliteit van `expert_framing`/`denktank_levert_expert`."
        ),
    },
    {
        "name": "academische_orthodoxie_instituut",
        "filter": "ideologie",
        "mechanism_type": "structureel",
        "source_role": "kennisinstituut",
        "target_role": "gezagsinstituut",
        "description": (
            "De 'primaire definieerders' (CPB, DNB, ministeries, planbureaus) worden bemenst door "
            "academisch gevormde economen en deskundigen die de heersende paradigma's hanteren (bv. "
            "neoklassieke economie). Hun 'neutrale' modellen en doorrekeningen dragen die orthodoxie."
        ),
        "effect": (
            "De aannames achter een CPB-doorrekening of DNB-prognose gelden als objectief feit terwijl "
            "ze een academisch paradigma weerspiegelen; alternatieve probleemdefinities moeten 'tegen de "
            "cijfers in' bewijzen. Voedt `institutioneel_gezag`."
        ),
    },
    {
        "name": "academische_vorming_opinie",
        "filter": "ideologie",
        "mechanism_type": "discursief",
        "source_role": "kennisinstituut",
        "target_role": "columnist_opiniemaker",
        "description": (
            "Columnisten en opiniemakers — de 'organische intellectuelen' — zijn academisch gevormd en "
            "reproduceren het dominante denkkader als vanzelfsprekend."
        ),
        "effect": (
            "Het hoogopgeleide, progressief-neoliberale frame wordt als 'gezond verstand' herhaald; "
            "voedt `columnist_als_hegemon` en helpt de grenzen van het redelijke debat bewaken."
        ),
    },
]


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bp = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, bp)
    print(f"Backup gemaakt: {bp.name}")


def role_id(conn, name):
    r = conn.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
    if not r:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
    return r[0]


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("\n-- nieuwe kennisinstituut-edges --")
    for m in NEW:
        sid, tid = role_id(conn, m["source_role"]), role_id(conn, m["target_role"])
        if conn.execute("SELECT 1 FROM mechanisms WHERE name=?", (m["name"],)).fetchone():
            conn.execute(
                "UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?, source_role_id=?, target_role_id=? WHERE name=?",
                (m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid, m["name"]),
            )
            print(f"  bijgewerkt (bestond al): {m['name']}")
        else:
            conn.execute(
                "INSERT INTO mechanisms (name, filter, mechanism_type, description, effect, source_role_id, target_role_id) VALUES (?,?,?,?,?,?,?)",
                (m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid),
            )
            print(f"  toegevoegd: {m['name']} ({m['filter']}) {m['source_role']} → {m['target_role']}")

    conn.commit()
    print("\n== verificatie: uitgaande edges van kennisinstituut ==")
    rows = conn.execute(
        """SELECT m.name, tr.name FROM mechanisms m
           JOIN roles sr ON sr.id=m.source_role_id JOIN roles tr ON tr.id=m.target_role_id
           WHERE sr.name='kennisinstituut' ORDER BY m.name"""
    ).fetchall()
    for r in rows:
        print(f"  kennisinstituut → {r[1]}  ({r[0]})")
    n = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen: {n}.")


if __name__ == "__main__":
    main()
