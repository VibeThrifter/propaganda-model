"""
Modelreview — `omroepsignatuur` en `omroepverzuiling` ontwarren (twee niveaus, geen merge).

De twee leken te overlappen ("zuil kleurt inhoud"), maar het zijn twee NIVEAUS van dezelfde
verzuilde identiteit (zoals nu ook in DOCUMENTATIE.md, Filter 1/5, beschreven):

  - omroepsignatuur  (ledenomroep -> redactie):  INTERN  — de zuil stuurt de eigen redactie
  - omroepverzuiling (ledenomroep -> publiek):   SYSTEEM — pluriformiteit TUSSEN omroepen

Edges/filters blijven (beide ideologie); alleen de beschrijvingen worden scherp onderscheiden
met wederzijdse kruisverwijzing, zodat de overlap weg is. Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

UPDATES = [
    {
        "name": "omroepsignatuur",
        "description": (
            "INTERN niveau. De statutaire godsdienstige, maatschappelijke of geestelijke stroming van "
            "een ledenomroep (christelijk, sociaaldemocratisch, rechts-populistisch, ...) stuurt de "
            "eigen redactie: onderwerp- en gastenkeuze, toon en bronselectie worden vooraf gekleurd "
            "door de zuil-identiteit."
        ),
        "effect": (
            "Binnen één omroep is de selectie niet neutraal maar zuil-gebonden. Dit is de redactionele "
            "doorwerking van de zuil; de doorwerking naar publiek/bestel is `omroepverzuiling`."
        ),
    },
    {
        "name": "omroepverzuiling",
        "description": (
            "SYSTEEM-/BESTELNIVEAU. Het verzuilde bestel levert zijn pluriformiteit niet bínnen maar "
            "TUSSEN omroepen: het publiek kiest tussen vooraf gekleurde zuilen in plaats van binnen één "
            "neutrale redactie. De interne kleuring per omroep is `omroepsignatuur`."
        ),
        "effect": (
            "Schijn-pluralisme: veel 'stromingen', maar de keuze is gesegmenteerd langs zuilen en blijft "
            "binnen de grenzen van het bestel; fundamentele systeemkritiek valt buiten het toegestane "
            "spectrum."
        ),
    },
]


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bp = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, bp)
    print(f"Backup gemaakt: {bp.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    for u in UPDATES:
        cur = conn.execute(
            "UPDATE mechanisms SET description=?, effect=? WHERE name=?",
            (u["description"], u["effect"], u["name"]),
        )
        print(f"  {'ontward' if cur.rowcount else 'NIET gevonden'}: {u['name']}")

    conn.commit()
    print("\n== verificatie ==")
    for nm in ("omroepsignatuur", "omroepverzuiling"):
        row = conn.execute(
            """SELECT COALESCE(sr.name,'—'), COALESCE(tr.name,'—'), m.filter, substr(m.description,1,55)
               FROM mechanisms m LEFT JOIN roles sr ON sr.id=m.source_role_id LEFT JOIN roles tr ON tr.id=m.target_role_id
               WHERE m.name=?""", (nm,)
        ).fetchone()
        print(f"  {nm}: {row[0]} → {row[1]} ({row[2]}) — {row[3]}…")
    conn.close()


if __name__ == "__main__":
    main()
