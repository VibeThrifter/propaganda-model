"""
Modelreview — publiek-kortsluitingen ompunten + hoofdredacteur-bedrading (pre-selectie).

Principe (zoals bij verwijderde `overheidsadvertenties`): een actor die niet zélf het medium is,
bereikt het publiek VIA het medium, niet rechtstreeks. Drie zulke kortsluitingen worden omgepunt /
gepoort, en de hoofdredacteur krijgt de twee ontbrekende bovenstroomse edges (Chomsky's
anticipatoire pre-selectie + academische socialisatie).

A. publiek-kortsluitingen (3):
   1. `verifieerbaarheidsroutine` (persbureau→publiek)  -> OMPUNTEN naar persbureau→mediaorganisatie
   2. `politicus_als_ideoloog`    (politicus→publiek)    -> OMPUNTEN naar politicus→journalist
   3. `columnist_als_hegemon`     (columnist→publiek)    -> BLIJFT; ontbrekende POORT toegevoegd:
      `podiumverlening` (hoofdredacteur→columnist_opiniemaker)
B. hoofdredacteur (+2):
   4. `academische_socialisatie_hoofdredacteur` (kennisinstituut→hoofdredacteur)
   5. `preselectie_hoofdredacteur`              (mediaorganisatie→hoofdredacteur)

Geen instance-data hangt aan de om-te-punten mechanismen (vooraf gecontroleerd: 0 relations/
instantiations/arguments). Idempotent; backup-then-migrate.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# --- A. ompunten (UPDATE op naam; target_role wijzigt + scherpere tekst) ---
REPOINT = [
    {
        "name": "verifieerbaarheidsroutine",
        "target_role": "mediaorganisatie",
        "filter": "sourcing",
        "description": (
            "Een persbureau moet altijd eerste én nooit fout zijn. Die dubbele eis bevoordeelt nieuws "
            "dat snel en goedkoop te verifiëren is — een officiële verklaring, een koersbeweging, een "
            "afgesloten snelweg — boven trage, betwistbare onderzoeksjournalistiek. Structurele "
            "problemen worden vaak pas 'bureaunieuws' als een officiële instantie er een rapport over "
            "uitbrengt of er rellen uitbreken. Deze productielogica bepaalt welke kant-en-klare kopij "
            "de titels binnenkrijgen (sluit aan op `persbureau_brongebondenheid`)."
        ),
        "effect": (
            "De selectiebias van de wire service zit al in de kopij die redacties via "
            "`pakketjournalistiek` overnemen; het persbureau raakt het publiek dus niet direct maar "
            "vormt het nieuwsaanbod van de titels stroomopwaarts."
        ),
    },
    {
        "name": "politicus_als_ideoloog",
        "target_role": "journalist",
        "filter": "ideologie",
        "description": (
            "Politici presenteren beleidsopties als de enige realistische keuze ('er is geen "
            "alternatief'); dat TINA-frame wordt door de verslaggever overgenomen als de gezaghebbende "
            "politieke realiteit. Ideologische pendant van `politicus_als_bron` (sourcing): daar gaat "
            "het om de bron-afhankelijkheid, hier om het wereldbeeld dat met de bron mee de "
            "berichtgeving in komt."
        ),
        "effect": (
            "De grenzen van het beleidsdebat worden door de politieke bron vooraf gezet en via de "
            "media gereproduceerd; de politicus bereikt het publiek niet rechtstreeks maar door de "
            "berichtgeving heen."
        ),
    },
]

# --- A.3 + B. nieuwe edges (INSERT-else-UPDATE) ---
NEW = [
    {
        "name": "podiumverlening",
        "filter": "eigendom",
        "mechanism_type": "procedureel",
        "source_role": "hoofdredacteur",
        "target_role": "columnist_opiniemaker",
        "description": (
            "De hoofdredacteur/opinieredactie verleent en cureert het column- en opiniepodium: wie een "
            "vaste column of gastbijdrage krijgt, met welke frequentie en plaatsing, is een "
            "redactionele selectiebeslissing. Spiegelbeeld van `toegangsdisciplinering` "
            "(redactie→gezagsexpert): toegang tot het podium is een schaarse hulpbron."
        ),
        "effect": (
            "De opiniepagina lijkt open maar is voorgeselecteerd; columnisten die het toegestane "
            "spectrum respecteren behouden hun podium. Dit is de ontbrekende poort vóór "
            "`columnist_als_hegemon`: de verbatim auteursstem bereikt het publiek pas nadat de "
            "redacteur het podium heeft verleend."
        ),
    },
    {
        "name": "academische_socialisatie_hoofdredacteur",
        "filter": "ideologie",
        "mechanism_type": "structureel",
        "source_role": "kennisinstituut",
        "target_role": "hoofdredacteur",
        "description": (
            "Ook de hoofdredacteur — de plek waar het redactionele eindoordeel valt — is academisch "
            "(WO) gevormd en deelt de premissen van de hoogopgeleide hegemonie (Bovens & Wille, "
            "'diplomademocratie'; Gramsci). Aanvulling op de socialisatie op journalist-niveau "
            "(`journalist_socialisatie`): de top van de hiërarchie draagt hetzelfde kader."
        ),
        "effect": (
            "Het redactionele eindoordeel vertrekt vanuit het hoogopgeleide referentiekader; samen met "
            "`journalist_socialisatie` en `sociologische_homogeniteit` maakt dit het dominante "
            "denkkader tot vanzelfsprekende achtergrond. Hoort bij de `academische_*`-familie van "
            "hegemonie-reproductie."
        ),
    },
    {
        "name": "preselectie_hoofdredacteur",
        "filter": "ideologie",
        "mechanism_type": "structureel",
        "source_role": "mediaorganisatie",
        "target_role": "hoofdredacteur",
        "description": (
            "Chomsky's anticipatoire pre-selectie: men bereikt en behoudt de hoofdredacteursstoel "
            "alleen na een lange loopbaan van bewezen, 'veilig' en eigenaar-aligned oordeel. Wie "
            "fundamenteel afwijkt wordt niet benoemd of houdt het niet vol. De loyaliteit aan het "
            "commerciële en reputatiebelang van de eigenaar is daardoor geïnternaliseerd, niet "
            "bevolen. Te onderscheiden van `benoemingspolitiek` (eigendom: de formele benoemingsmacht) "
            "— dit is de ideologische zeef die de benoeming toepast plus de doorlopende zelf-aligning."
        ),
        "effect": (
            "De hoofdredacteur dient het eigenaarsbelang uit zichzelf; dit is de bron van "
            "`hoofdredacteur_als_filter` (de neerwaartse vertaling naar de journalist). De eigenaar "
            "hoeft niet in te grijpen — de selectie heeft het werk al gedaan. Bron blijft op org-niveau "
            "(`mediaorganisatie`) zodat de eigenaar de redactie niet direct raakt."
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

    print("\n-- A. ompunten van publiek-kortsluitingen --")
    for r in REPOINT:
        tid = role_id(conn, r["target_role"])
        cur = conn.execute(
            "UPDATE mechanisms SET target_role_id=?, filter=?, description=?, effect=? WHERE name=?",
            (tid, r["filter"], r["description"], r["effect"], r["name"]),
        )
        print(f"  {'omgepunt' if cur.rowcount else 'NIET gevonden'}: {r['name']} → {r['target_role']}")

    print("\n-- A.3 + B. nieuwe edges --")
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

    print("\n== verificatie: gewijzigde/nieuwe edges ==")
    for nm in [r["name"] for r in REPOINT] + [m["name"] for m in NEW]:
        row = conn.execute(
            """SELECT COALESCE(sr.name,'—'), COALESCE(tr.name,'—'), m.filter
               FROM mechanisms m LEFT JOIN roles sr ON sr.id=m.source_role_id
               LEFT JOIN roles tr ON tr.id=m.target_role_id WHERE m.name=?""", (nm,)
        ).fetchone()
        print(f"  {nm:<42} {row[0]} → {row[1]} ({row[2]})")

    print("\n== verificatie: wie raakt 'publiek' nog direct? ==")
    rows = conn.execute(
        """SELECT sr.name, m.name FROM mechanisms m
           JOIN roles sr ON sr.id=m.source_role_id JOIN roles tr ON tr.id=m.target_role_id
           WHERE tr.name='publiek' ORDER BY sr.name, m.name"""
    ).fetchall()
    for r in rows:
        print(f"  {r[0]:<22} [{r[1]}]")

    n = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen: {n} (verwacht 106).")


if __name__ == "__main__":
    main()
