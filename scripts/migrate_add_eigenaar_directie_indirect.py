"""
Modelreview — `mediaeigenaar ⇢ directie` als samenvattende INDIRECTE pijl.

Probleem: in het theoriemodel staat de eigenaar nergens naast de directie. Het beste pad
loopt `mediaeigenaar → administratiekantoor (STAK) → raad_van_commissarissen → directie`
(3 hops, 2 tussenknopen), en de demping per hop (~0,4³ ≈ 0,06) onderschat wat in
werkelijkheid geldt: de eigenaar kíést de directie — alleen gemedieerd (hij benoemt de RvC
en zit er vaak zelf in; bij de feitelijke Belgische, eenlaagse eigenaren valt de RvC-laag
zelfs weg). De keten toont het *hoe*; het *netto* ("eigenaar kiest directie") was onzichtbaar.

Oplossing: precies de `indirect`-aard (zie migrate_add_indirect_aard.py). Eén samenvattende
schakel `mediaeigenaar → directie`, `aard='indirect'` — een gestippelde pijl MÉT punt in de
eigendom-kleur, in de achtergrondlaag áchter de gouden velden, onder de toggle "Indirecte &
systemische effecten". De gedetailleerde keten (STAK → RvC → directie) blijft staan voor het
hoe; deze pijl toont het netto-effect.

Effect op `influence.py`: de graaf neemt het BESTE pad (max-product), dus de 1-hop indirecte
schakel (~0,4) wint van de uitgedoofde 3-hop keten (~0,06). Geen dubbeltelling (max-pad per
doel, geen som); het corrigeert de eerdere onderschatting van de eigenaarsgreep.

Idempotent; backup-then-migrate. Rollen via naam opgelost.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

MECH_NAME = "eigenaar_directiekeuze"
SOURCE_ROLE = "mediaeigenaar"
TARGET_ROLE = "directie"
FILTER = "eigendom"
MTYPE = "procedureel"
AARD = "indirect"
THEME = "benoemingsketen"
DESCRIPTION = (
    "De feitelijke, gemedieerde keuze van de directie door de eigenaar. Juridisch loopt de "
    "benoeming via de keten (eigenaar → STAK → Raad van Commissarissen → directie), maar de "
    "eigenaar benoemt de RvC en zit er vaak zelf in; bij de feitelijke (Belgische, vaak "
    "eenlaagse) eigenaren valt die tussenlaag weg en benoemt de algemene vergadering het "
    "bestuur rechtstreeks. Deze schakel vat dat netto-effect samen: de eigenaar kiest de "
    "directie — gemedieerd, niet rechtstreeks. Het *hoe* staat in de keten "
    "(stak_stemzeggenschap → directiebenoeming); dit is het *wat*."
)
EFFECT = (
    "Het dagelijks bestuur dat de krant leidt is door de eigenaar geselecteerd op passendheid "
    "bij het eigenaarsbelang; de eigenaarsvoorkeur bereikt zo — gedempt maar blijvend — de "
    "directie en daarmee de benoeming van de hoofdredacteur."
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

    conn.execute(
        "INSERT OR IGNORE INTO mechanisms (name, filter, mechanism_type, description, effect, "
        "source_role_id, target_role_id, aard) VALUES (?,?,?,?,?,?,?,?)",
        (MECH_NAME, FILTER, MTYPE, DESCRIPTION, EFFECT, sid, tid, AARD),
    )
    mid = conn.execute("SELECT id FROM mechanisms WHERE name=?", (MECH_NAME,)).fetchone()[0]
    conn.execute(
        "UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?, "
        "source_role_id=?, target_role_id=?, aard=? WHERE id=?",
        (FILTER, MTYPE, DESCRIPTION, EFFECT, sid, tid, AARD, mid),
    )
    conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) VALUES (?,?)", (mid, FILTER))
    conn.execute("INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) VALUES (?,?)", (mid, THEME))
    print(f"  mechanisme: {MECH_NAME}: {SOURCE_ROLE} ⇢ {TARGET_ROLE} [{FILTER}, {AARD}, thema: {THEME}]")

    conn.commit()

    print("\n== verificatie: indirecte schakels ==")
    for name, s, t, f in conn.execute("""
        SELECT m.name, (SELECT name FROM roles WHERE id=m.source_role_id),
               (SELECT name FROM roles WHERE id=m.target_role_id), m.filter
        FROM mechanisms m WHERE m.aard='indirect' ORDER BY m.name"""):
        print(f"  {name:40} {s} ⇢ {t}   [{f}]")
    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
