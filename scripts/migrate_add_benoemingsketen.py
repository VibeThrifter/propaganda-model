"""
Modelreview (eigendom + tegenmacht) — de benoemingsketen expliciet maken.

Tot nu toe waren de Raad van Commissarissen en de directie samengevouwen in de
rol `mediaorganisatie`: `benoemingspolitiek` liep van mediaorganisatie -> hoofdredacteur.
Dat verhult de feitelijke keten waarlangs kapitaal de hoofdredactie bereikt:

    aandeelhouder/AvA       --commissarisbenoeming-->  Raad van Commissarissen
    administratiekantoor    --stak_stemzeggenschap-->  Raad van Commissarissen   (familiecontrole-route)
    Raad van Commissarissen --directiebenoeming-->     directie (CEO/uitgever)
    directie                --benoemingspolitiek-->    hoofdredacteur

De stak_stemzeggenschap-schakel koppelt de bestaande eigenaarsketen (mediaeigenaar -> STAK)
aan de board-keten, zodat de elite/eigenaar-band doorstroomt tot het toegestane frame i.p.v.
in een los eiland te blijven hangen.

En de tegenmacht die Gemini terecht als kernpunt noemt — het instemmingsrecht van
de redactieraad — was nergens een eigen edge; het stond alleen verstopt in de tekst
van een eigendom-mechanisme. Nu als expliciete tegenmacht:

    redactie (redactieraad) --redactieraad_instemming-->  directie   (rem op de benoeming)

Twee nieuwe rollen (eigendom): raad_van_commissarissen, directie.
Drie nieuwe mechanismen + één repoint (benoemingspolitiek: bron mediaorganisatie -> directie).
Alle vier de keten-schakels krijgen het thema 'benoemingsketen' zodat de eigendom<->tegenmacht-
draad in de viz als dwarsverband zichtbaar is.

Géén bevelstructuur: de RvC handelt formeel onafhankelijk, de directie benoemt binnen het
door eigendom ingebedde kader, en de bias blijft emergent. De redactie-instemming varieert
per redactiestatuut (zwaarwegend advies t/m hard instemmingsrecht) — dat hoort in de
certainty/beschrijving, niet als universeel veto.

Idempotent; backup-then-migrate. Rollen via naam opgelost.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# Nieuwe rollen: naam -> (category, description, examples)
ROLES = {
    "raad_van_commissarissen": (
        "eigendom",
        "De Raad van Commissarissen (RvC): het interne toezichtorgaan dat de directie "
        "benoemt, controleert en ontslaat. Wordt zelf benoemd door de aandeelhouders-"
        "vergadering / controlerende familie en handelt — formeel onafhankelijk — in de "
        "geest van de eigenaar. Schakel tussen kapitaal en dagelijks bestuur.",
        "RvC van DPG Media; RvC van Mediahuis; raden van commissarissen van uitgeverijen",
    ),
    "directie": (
        "eigendom",
        "De directie (CEO/uitgever): het dagelijks bestuur van de mediaorganisatie. Gaat "
        "over financiën, strategie, overnames en winstdoelstelling, en benoemt de "
        "hoofdredacteur — binnen het door de eigenaar via de RvC en de eigendomsketen "
        "(STAK/holding) bepaalde kader.",
        "Christian Van Thillo (DPG); CEO/uitgever van Mediahuis Nederland",
    ),
}

# Nieuwe mechanismen: naam -> (bron, doel, filter, type, aard, description, effect, [thema's])
MECHANISMS = {
    "commissarisbenoeming": (
        "aandeelhouder", "raad_van_commissarissen", "eigendom", "procedureel", "direct",
        "De aandeelhoudersvergadering benoemt de Raad van Commissarissen. Bij gespreid kapitaal "
        "loopt dit via de AvA; bij STAK-/prioriteitsconstructies ligt het benoemingsrecht bij de "
        "verankerde zeggenschap (zie stak_stemzeggenschap), niet bij de certificaathouders. "
        "Daarmee zet de eigenaar het toezichtorgaan naar zijn hand zónder dagelijkse bemoeienis.",
        "De RvC houdt toezicht 'in de geest van' de aandeelhouder; de eigenaar stuurt de top "
        "indirect, via wie er aan het toezicht zit.",
        ["benoemingsketen"],
    ),
    # Connector die de gecertificeerde familiecontrole aan de board-keten koppelt: zonder deze
    # edge is de RvC->directie->hoofdredacteur-keten een eiland en draagt de elite/eigenaar-band
    # niet door naar het toegestane frame. De STAK houdt de stemmen, dus benoemt feitelijk de RvC.
    "stak_stemzeggenschap": (
        "administratiekantoor", "raad_van_commissarissen", "eigendom", "structureel", "direct",
        "Het administratiekantoor (STAK) houdt de stemgerechtigde (prioriteits)aandelen en oefent "
        "zo het aandeelhoudersbenoemingsrecht over de Raad van Commissarissen uit. Zo verlengt de "
        "gecertificeerde familiecontrole zich van het kapitaal naar het toezicht — losgekoppeld van "
        "het economische belang dat via certificaten naar de certificaathouders gaat. Dit is de "
        "schakel waarlangs de eigenaarsvoorkeur (en daarmee de via mediaeigenaar_elite_netwerk "
        "ingebedde elite-frames) de RvC -> directie -> hoofdredacteur-keten in stroomt.",
        "De controlerende familie bepaalt — via de STAK — wie er toezicht houdt, en dus indirect "
        "wie er directie en hoofdredacteur wordt; het toegestane frame voor het publiek draagt een "
        "kleine, blijvende eigenaarssignatuur.",
        ["benoemingsketen"],
    ),
    "directiebenoeming": (
        "raad_van_commissarissen", "directie", "eigendom", "procedureel", "direct",
        "De Raad van Commissarissen benoemt, controleert en ontslaat de directie. Formeel een "
        "onafhankelijke afweging; feitelijk binnen de strategische kaders en winstverwachting "
        "die de eigenaar via de RvC heeft ingebed.",
        "De directie die de krant leidt is geselecteerd op passendheid bij het eigenaarsbelang; "
        "de eigenaarsvoorkeur stroomt zo door naar het dagelijks bestuur.",
        ["benoemingsketen"],
    ),
    "redactieraad_instemming": (
        "redactie", "directie", "tegenmacht", "procedureel", "direct",
        "Via het redactiestatuut heeft de redactieraad (de gekozen vertegenwoordiging van de "
        "redactie) een formele stem bij de benoeming van de hoofdredacteur: van zwaarwegend "
        "adviesrecht tot — bij veel titels — instemmingsrecht. In de praktijk werkt dat als "
        "veto: tegen een kandidaat zonder redactioneel draagvlak gaat de benoeming vrijwel "
        "nooit door. Het begrenst de benoemingsmacht van de directie (rem op benoemingspolitiek). "
        "De sterkte varieert per statuut — daarom geen universeel hard veto.",
        "De directie kan geen hoofdredacteur doordrukken zonder redactioneel draagvlak: interne "
        "tegenmacht naast de externe borgingsstichting (redactiestatuut_borging).",
        ["benoemingsketen"],
    ),
}


ALLOWED_THEMES = (
    "draaideur", "elite_netwerk", "geldstromen", "platform",
    "systemisch", "omroepbestel", "kennis_expertise", "benoemingsketen",
)


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def ensure_theme_allowed(conn, theme="benoemingsketen"):
    """De CHECK-enum op mechanism_themes.theme uitbreiden. SQLite kan een CHECK niet
    in-place wijzigen, dus de tabel wordt herbouwd (data behouden). Idempotent: doet
    niets als het thema al is toegestaan."""
    ddl = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='mechanism_themes'"
    ).fetchone()[0]
    if theme in ddl:
        print(f"  CHECK-enum bevat '{theme}' al — geen herbouw nodig.")
        return
    allowed = ", ".join(f"'{t}'" for t in ALLOWED_THEMES)
    conn.executescript(f"""
        CREATE TABLE mechanism_themes_new (
            mechanism_id INTEGER NOT NULL REFERENCES mechanisms(id) ON DELETE CASCADE,
            theme TEXT NOT NULL CHECK(theme IN ({allowed})),
            PRIMARY KEY (mechanism_id, theme)
        );
        INSERT INTO mechanism_themes_new SELECT * FROM mechanism_themes;
        DROP TABLE mechanism_themes;
        ALTER TABLE mechanism_themes_new RENAME TO mechanism_themes;
        CREATE INDEX idx_mechthemes_theme ON mechanism_themes(theme);
    """)
    print(f"  mechanism_themes herbouwd; CHECK-enum uitgebreid met '{theme}'.")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # 0) Thema-vocabulaire uitbreiden (anders dropt de CHECK 'benoemingsketen' stilzwijgend).
    print("Thema-enum:")
    ensure_theme_allowed(conn, "benoemingsketen")

    # 1) Rollen (idempotent: insert-or-ignore, dan tekst in sync brengen).
    for name, (cat, desc, examples) in ROLES.items():
        conn.execute(
            "INSERT OR IGNORE INTO roles (name, category, description, examples) VALUES (?,?,?,?)",
            (name, cat, desc, examples),
        )
        conn.execute(
            "UPDATE roles SET category=?, description=?, examples=? WHERE name=?",
            (cat, desc, examples, name),
        )
        print(f"  rol: {name} [{cat}]")

    role_id = {name: rid for rid, name in conn.execute("SELECT id, name FROM roles")}

    # 2) Nieuwe mechanismen.
    for name, (bron, doel, flt, mtype, aard, desc, effect, themes) in MECHANISMS.items():
        sid, tid = role_id.get(bron), role_id.get(doel)
        if sid is None or tid is None:
            print(f"  WAARSCHUWING: rol ontbreekt voor '{name}' ({bron}->{doel}) — overgeslagen.")
            continue
        conn.execute(
            "INSERT OR IGNORE INTO mechanisms (name, filter, mechanism_type, description, effect, "
            "source_role_id, target_role_id, aard) VALUES (?,?,?,?,?,?,?,?)",
            (name, flt, mtype, desc, effect, sid, tid, aard),
        )
        mid = conn.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()[0]
        conn.execute(
            "UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?, "
            "source_role_id=?, target_role_id=?, aard=? WHERE id=?",
            (flt, mtype, desc, effect, sid, tid, aard, mid),
        )
        conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) VALUES (?,?)", (mid, flt))
        for th in themes:
            conn.execute("INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) VALUES (?,?)", (mid, th))
        print(f"  mechanisme: {name}: {bron} -> {doel} [{flt}, {aard}, thema's: {', '.join(themes)}]")

    # 3) Repoint benoemingspolitiek: bron mediaorganisatie -> directie; tekst + thema bijwerken.
    directie_id = role_id.get("directie")
    bp = conn.execute("SELECT id FROM mechanisms WHERE name='benoemingspolitiek'").fetchone()
    if bp and directie_id is not None:
        bp_id = bp[0]
        new_desc = (
            "De directie/uitgever benoemt de hoofdredacteur — binnen het kader dat de eigenaar "
            "via de eigendomsketen (familie -> STAK -> holding) en via de Raad van Commissarissen "
            "(commissarisbenoeming -> directiebenoeming) heeft bepaald. De eigenaar raakt de "
            "redactie dus niet direct; de benoeming gebeurt op directieniveau, met zwaarwegend "
            "advies of instemming van de redactieraad (zie redactieraad_instemming / het "
            "redactiestatuut)."
        )
        conn.execute(
            "UPDATE mechanisms SET source_role_id=?, description=? WHERE id=?",
            (directie_id, new_desc, bp_id),
        )
        conn.execute("INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) VALUES (?,?)",
                     (bp_id, "benoemingsketen"))
        print("  repoint: benoemingspolitiek bron -> directie (+thema benoemingsketen)")
    else:
        print("  WAARSCHUWING: benoemingspolitiek of rol 'directie' niet gevonden — repoint overgeslagen.")

    conn.commit()

    # Verificatie: de keten + de tegenmacht-rem.
    print("\n== verificatie: benoemingsketen ==")
    rows = conn.execute("""
        SELECT m.name, (SELECT name FROM roles WHERE id=m.source_role_id),
               (SELECT name FROM roles WHERE id=m.target_role_id), m.filter, m.aard
        FROM mechanisms m
        WHERE m.id IN (SELECT mechanism_id FROM mechanism_themes WHERE theme='benoemingsketen')
        ORDER BY m.filter, m.name""").fetchall()
    for name, s, t, f, a in rows:
        print(f"  {name:26} {s} -> {t}   [{f}, {a}]")
    conn.close()
    print("\nKlaar.")


if __name__ == "__main__":
    main()
