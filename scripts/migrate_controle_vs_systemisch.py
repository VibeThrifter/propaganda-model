"""
Modelreview-ronde 2 — rode draad: 'controle vs. systemische alignering' + opschoning.

Achtergrond. Na een reality-check (NL-medialandschap, niet onze data) bleek de
eigendoms-/kapitaalkant te leunen op de *passieve/systemische* variant die bij het
Angelsaksische beursmodel hoort, terwijl het echte Nederlandse machtskanaal de
*directe zeggenschap/controle* is (strategische blokhouder, STAK-concentratie,
bestuurlijke draaideur). Dit script trekt dat onderscheid consistent door, ruimt een
niet-NL mechanisme op, en ontdubbelt een rol — zónder nieuwe redundantie te creëren.

Geen schemawijziging (alle enum-/rolwaarden bestaan al). Idempotent: opnieuw draaien
is veilig. Volgt de backup-then-migrate-conventie.

1. VERWIJDEREN — `aandeelhouder_druk` (aandeelhouder -> mediaorganisatie, 0 relaties).
   Direct beursaandeelhouderschap van een NL-titel is geen Nederlandse norm; het kanaal
   bestaat alleen historisch/buitenlands (TMG tot 2017, RTL Group/Sanoma boven een
   buitenlandse holding) en hoort in de Filter 1-docs als randgeval, niet als mechanisme.

2. MERGEN — `institutioneel_belegger` -> `aandeelhouder`. Een institutionele belegger
   *is* een aandeelhouder (deelverzameling). Het onderscheid actief/passief is geen
   verschil in actorklasse maar in MECHANISME + exemplariteit. Alle verwijzingen worden
   omgehangen (BlackRock/Vanguard, entity_roles, instantiations, mechanismen), daarna
   verdwijnt de rol. `systemisch_eigenaarschap` krijgt zo automatisch `aandeelhouder` als bron.

3. NIEUW — `strategische_zeggenschap` (aandeelhouder -> belanghebbende): de ACTIEVE pool
   naast de passieve `systemisch_eigenaarschap`. Een blokhouder/controlerende familie
   (GBL/Frère, KBC) stuurt gericht één onderneming via bestuurszetels en stemrecht.
   Het onderscheid zit zo in het mechanisme, niet in twee rollen.

4. STAK = CONTROLE-VERSTERKER (geen demper). `certificaatconstructie` wordt aangescherpt:
   eigenaarsinvloed is niet 'distaal = zwak' — de STAK concentreert de macht juist hoog
   in de keten (klein economisch belang -> volledige, overdrachtsbestendige zeggenschap).

5. DRAAIDEUR — geen nieuw mechanisme (de bestuurlijke landing is al gedekt door
   `politieke_benoeming_omroeptop` en `draaideur_politiek_institutie`). Alleen de
   beschrijving van `draaideur_politiek_media` wordt aangescherpt tot de inhoud-landing
   (hoofdredacteur/duider/presentator), zodat de twee landings niet door elkaar lopen.

6. PERSBUREAU (Filter 3) — het persbureau is de industriële versterker van de
   sourcing-bias: objectief in HÓE, structureel selectief in WÁT. Roldefinitie
   aangescherpt; `persbureau_brongebondenheid` verdiept (officiële agenda's); twee
   nieuwe mechanismen: `klantvraag_persbureau` (mediaorganisatie -> persbureau) en
   `verifieerbaarheidsroutine` (persbureau -> publiek).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# --- 1. Verwijderen (alleen als 0 relaties eraan hangen) ---------------------
DELETE_MECHANISMS_IF_UNUSED = ["aandeelhouder_druk"]

# --- 2. Rol-merge ------------------------------------------------------------
MERGE_FROM = "institutioneel_belegger"
MERGE_TO = "aandeelhouder"

# --- 3 + 6. Nieuwe mechanismen ----------------------------------------------
NEW_MECHANISMS = [
    {
        "name": "strategische_zeggenschap",
        "filter": "eigendom",
        "mechanism_type": "structureel",
        "description": (
            "De actieve tegenpool van `systemisch_eigenaarschap`. Een aandeelhouder met een "
            "geconcentreerd, strategisch belang — blokhouder, controlerende familie, "
            "participatiemaatschappij (bv. GBL/Frère, KBC) — oefent gerichte zeggenschap uit "
            "over één onderneming (`belanghebbende`) via bestuurszetels, stemrecht en "
            "strategiebepaling. Anders dan de gespreide, passieve universal owner stuurt deze "
            "aandeelhouder één specifiek bedrijf. (De media-zijde-variant van geconcentreerde "
            "controle is de gecertificeerde familiecontrole van Filter 1: "
            "`familiezeggenschap`/`certificaatconstructie`.)"
        ),
        "effect": (
            "Gerichte invloed op koers, kapitaalallocatie en benoemingen van de gecontroleerde "
            "onderneming — hoge influence op de losse relatie, tegenover de diffuse "
            "alomtegenwoordigheid van `systemisch_eigenaarschap`. Zo zit het onderscheid "
            "actief/passief in het mechanisme, niet in een aparte rol."
        ),
        "source_role": "aandeelhouder",
        "target_role": "belanghebbende",
    },
    {
        "name": "klantvraag_persbureau",
        "filter": "sourcing",
        "mechanism_type": "economisch",
        "description": (
            "Het persbureau is een commercieel bedrijf dat levert wat zijn betalende klanten "
            "(de aangesloten titels en omroepen) vragen. Vragen redacties massaal om hetzelfde "
            "onderwerp (formatie, grote sport, incidenten), dan schaalt het bureau daar zijn "
            "inzet op op — ten koste van structureel ondervraagde thema's (klimaat, "
            "internationale cultuur, sluimerende misstanden). De markt-vraag van de klant stuurt "
            "zo de aanbod-selectie aan de bovenkant van de keten."
        ),
        "effect": (
            "De 'waan van de dag' wordt geïndustrialiseerd: de bovenkant van de nieuwsketen "
            "volgt de gebundelde klantvraag, waardoor onderbelichte onderwerpen ook "
            "stroomafwaarts (via `pakketjournalistiek`) onderbelicht blijven."
        ),
        "source_role": "mediaorganisatie",
        "target_role": "persbureau",
    },
    {
        "name": "verifieerbaarheidsroutine",
        "filter": "sourcing",
        "mechanism_type": "procedureel",
        "description": (
            "Een persbureau moet altijd eerste én nooit fout zijn. Die dubbele eis bevoordeelt "
            "nieuws dat snel en goedkoop te verifiëren is — een officiële verklaring, een "
            "koersbeweging, een afgesloten snelweg — boven trage, betwistbare "
            "onderzoeksjournalistiek. Structurele problemen worden vaak pas 'bureaunieuws' als "
            "een officiële instantie er een rapport over uitbrengt of er rellen uitbreken "
            "(sluit aan op `persbureau_brongebondenheid`)."
        ),
        "effect": (
            "Selectiebias richting het officieel-controleerbare en het gebeurtenis-nieuws: het "
            "ANP is objectief in HÓE het schrijft, maar door tijd, geld en routine onvermijdelijk "
            "selectief in WÁT het schrijft — en die WÁT-selectie is precies wat het "
            "propagandamodel betreft."
        ),
        "source_role": "persbureau",
        "target_role": "publiek",
    },
]

# --- 4 + 5 + 6. Aanscherpingen op bestaande mechanismen (alleen opgegeven velden) -
CORRECT_MECHANISMS = [
    {
        "name": "systemisch_eigenaarschap",
        "description": (
            "De passieve, systemische pool van het aandeelhouderschap. Institutionele beleggers "
            "(BlackRock, Vanguard, grote pensioenfondsen) bezitten via gespreid vermogensbeheer "
            "aandelen in vrijwel álle grote beursgenoteerde bedrijven tegelijk — zowel de "
            "holdings achter de media als de corporates die adverteren en lobbyen. Zo ontstaat "
            "een systemische achtergrond achter de hele bezittende klasse, geen gerichte greep "
            "op één onderneming. De actieve tegenpool is `strategische_zeggenschap`."
        ),
    },
    {
        "name": "certificaatconstructie",
        "description": (
            "De STAK certificeert de aandelen van het overnamevehikel/holding: economische "
            "rechten (certificaten) worden gescheiden van stemrecht, dat bij het stichtingsbestuur "
            "blijft. De constructie is een controle-VERSTERKER, geen demper: een klein (soms "
            "verwaterd) economisch belang wordt omgezet in volledige, overdrachtsbestendige "
            "zeggenschap."
        ),
        "effect": (
            "Zeggenschap is niet meer evenredig met economisch belang; een familie/UBO houdt de "
            "controle ook bij externe kapitaalinbreng of verwatering. De uiteindelijke eigenaren "
            "blijven buiten beeld (geen UBO-transparantie) en de keten wordt overnamebestendig. "
            "Eigenaarsinvloed is dus niet 'distaal = zwak': de STAK concentreert de macht juist "
            "hoog in de keten."
        ),
    },
    {
        "name": "draaideur_politiek_media",
        "description": (
            "Een (oud-)politicus of partijgebonden figuur belandt in de redactioneel-INHOUDELIJKE "
            "laag: als hoofdredacteur, vaste commentator, duider of presentator — of omgekeerd. "
            "Dit is de inhoud-landing van de draaideur, te onderscheiden van de BESTUURLIJKE "
            "landing (RvT/RvB), die via `politieke_benoeming_omroeptop` en "
            "`draaideur_politiek_institutie` loopt."
        ),
    },
    {
        "name": "persbureau_brongebondenheid",
        "description": (
            "Het persbureau moet continu, goedkoop en 'gezaghebbend' produceren en leunt daarom "
            "zwaar op de agenda's van officiële instanties — rechtbank, Tweede Kamer, politie, "
            "ministeries en persconferenties van grote bedrijven — plus kant-en-klare "
            "persberichten van voorlichters, die het grotendeels ongecontroleerd doorgeeft. Wat "
            "geen officiële bron of agenda heeft (sluimerende, structurele problemen) wordt pas "
            "nieuws als een instantie er een rapport over uitbrengt."
        ),
    },
]

# --- 2 + 6. Rol-descripties bijwerken ----------------------------------------
UPDATE_ROLES = [
    {
        "name": "aandeelhouder",
        "description": (
            "Verschaffer van aandelenkapitaal in een onderneming, holding of mediabedrijf. Omvat "
            "het hele spectrum van actief-strategische blokhouder (bestuurszetels, gerichte "
            "zeggenschap) tot passief-systemische universal owner (gespreid, diffuus, "
            "mede-eigenaar van vrijwel alles tegelijk). Het onderscheid actief/passief zit in het "
            "mechanisme — `strategische_zeggenschap` versus `systemisch_eigenaarschap` — en in de "
            "exemplariteit, niet in een aparte rol."
        ),
        "examples": (
            "BlackRock, Vanguard, pensioenfondsen (passief-systemisch); GBL/Frère, KBC, "
            "strategische participaties en controlerende families (actief-strategisch)"
        ),
    },
    {
        "name": "persbureau",
        "description": (
            "Centraal nieuwsleverancier dat de hele nieuwsstroom voedt en daardoor homogeniseert "
            "— distinct van individuele bronnen door zijn wholesale-karakter. Objectief in HÓE "
            "het schrijft (zonder oordeel), maar door tijd, geld, klantvraag en routines "
            "structureel selectief in WÁT het schrijft. Daarmee de industriële versterker van "
            "Filter 3: het zet selectiebias om in een landelijk uniform nieuwsbeeld."
        ),
        "examples": "ANP — levert dagelijks honderden berichten aan vrijwel alle NL media",
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
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden in roles-tabel.")
    return row[0]


def merge_role(conn, from_name, to_name):
    """Hang alle verwijzingen van rol `from_name` om naar `to_name` en verwijder de oude rol.
    Idempotent: als from_name al weg is, gebeurt er niets."""
    frow = conn.execute("SELECT id FROM roles WHERE name = ?", (from_name,)).fetchone()
    if frow is None:
        print(f"  '{from_name}' bestaat niet meer — merge al uitgevoerd, overgeslagen.")
        return
    fid = frow[0]
    tid = role_id(conn, to_name)

    # entities.primary_role_id
    conn.execute("UPDATE entities SET primary_role_id = ? WHERE primary_role_id = ?", (tid, fid))
    # entity_roles (PK entity_id,role_id) — OR IGNORE vangt botsing, daarna restanten weg
    conn.execute("UPDATE OR IGNORE entity_roles SET role_id = ? WHERE role_id = ?", (tid, fid))
    conn.execute("DELETE FROM entity_roles WHERE role_id = ?", (fid,))
    # instantiations (unieke index role_id,entity_id) — idem
    conn.execute("UPDATE OR IGNORE instantiations SET role_id = ? WHERE role_id = ?", (tid, fid))
    conn.execute("DELETE FROM instantiations WHERE role_id = ?", (fid,))
    # mechanismen die de rol als bron/doel hebben (o.a. systemisch_eigenaarschap als bron)
    conn.execute("UPDATE mechanisms SET source_role_id = ? WHERE source_role_id = ?", (tid, fid))
    conn.execute("UPDATE mechanisms SET target_role_id = ? WHERE target_role_id = ?", (tid, fid))
    # literatuur-argumenten over de rol
    conn.execute("UPDATE arguments SET role_id = ? WHERE role_id = ?", (tid, fid))
    # de rol zelf
    conn.execute("DELETE FROM roles WHERE id = ?", (fid,))
    print(f"  '{from_name}' (id {fid}) volledig omgehangen naar '{to_name}' (id {tid}) en verwijderd.")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    # 1. verwijderen (guard: 0 relaties)
    print("\n-- 1. niet-NL mechanisme verwijderen --")
    for name in DELETE_MECHANISMS_IF_UNUSED:
        row = conn.execute("SELECT id FROM mechanisms WHERE name = ?", (name,)).fetchone()
        if row is None:
            print(f"  '{name}' bestaat niet (al weg) — overgeslagen.")
            continue
        n = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id = ?", (row[0],)).fetchone()[0]
        if n:
            print(f"  NIET verwijderd: '{name}' heeft nog {n} relaties — laat staan.")
        else:
            conn.execute("DELETE FROM instantiations WHERE mechanism_id = ?", (row[0],))
            conn.execute("DELETE FROM mechanisms WHERE id = ?", (row[0],))
            print(f"  verwijderd (0 relaties): {name}")

    # 2. rol-merge
    print("\n-- 2. rol-merge institutioneel_belegger -> aandeelhouder --")
    merge_role(conn, MERGE_FROM, MERGE_TO)

    # 3 + 6. nieuwe mechanismen (idempotent: bestaat al -> volledig bijwerken)
    print("\n-- 3+6. nieuwe mechanismen --")
    for m in NEW_MECHANISMS:
        sid, tid = role_id(conn, m["source_role"]), role_id(conn, m["target_role"])
        exists = conn.execute("SELECT 1 FROM mechanisms WHERE name = ?", (m["name"],)).fetchone()
        if exists:
            conn.execute(
                """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
                   source_role_id=?, target_role_id=? WHERE name=?""",
                (m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid, m["name"]),
            )
            print(f"  bijgewerkt: {m['name']} ({m['source_role']} → {m['target_role']})")
        else:
            conn.execute(
                """INSERT INTO mechanisms
                   (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid),
            )
            print(f"  toegevoegd: {m['name']} ({m['filter']}) {m['source_role']} → {m['target_role']}")

    # 4 + 5 + 6. aanscherpingen op bestaande mechanismen
    print("\n-- 4+5+6. mechanisme-aanscherpingen --")
    for c in CORRECT_MECHANISMS:
        sets, vals = [], []
        for field in ("source_role", "target_role"):
            if field in c:
                col = "source_role_id" if field == "source_role" else "target_role_id"
                sets.append(f"{col} = ?"); vals.append(role_id(conn, c[field]))
        for field in ("description", "effect"):
            if field in c:
                sets.append(f"{field} = ?"); vals.append(c[field])
        vals.append(c["name"])
        cur = conn.execute(f"UPDATE mechanisms SET {', '.join(sets)} WHERE name = ?", vals)
        print(f"  {'aangescherpt' if cur.rowcount else 'NIET gevonden'}: {c['name']}")

    # 2 + 6. rol-descripties
    print("\n-- 2+6. rol-descripties --")
    for r in UPDATE_ROLES:
        cur = conn.execute(
            "UPDATE roles SET description = ?, examples = ? WHERE name = ?",
            (r["description"], r["examples"], r["name"]),
        )
        print(f"  {'bijgewerkt' if cur.rowcount else 'NIET gevonden'}: rol {r['name']}")

    conn.commit()

    # verificatie
    print("\n== verificatie ==")
    for q, label in [
        ("SELECT COUNT(*) FROM roles WHERE name='institutioneel_belegger'", "rol institutioneel_belegger (verwacht 0)"),
        ("SELECT COUNT(*) FROM mechanisms WHERE name='aandeelhouder_druk'", "mechanisme aandeelhouder_druk (verwacht 0)"),
        ("SELECT COUNT(*) FROM mechanisms WHERE name='strategische_zeggenschap'", "mechanisme strategische_zeggenschap (verwacht 1)"),
        ("SELECT COUNT(*) FROM mechanisms WHERE name IN ('klantvraag_persbureau','verifieerbaarheidsroutine')", "nieuwe persbureau-mechanismen (verwacht 2)"),
        ("SELECT COUNT(*) FROM entities WHERE primary_role_id=(SELECT id FROM roles WHERE name='aandeelhouder')", "entiteiten met primaire rol aandeelhouder"),
    ]:
        print(f"  {label}: {conn.execute(q).fetchone()[0]}")

    print("\n  systemisch_eigenaarschap bron/doel:")
    row = conn.execute(
        """SELECT sr.name, tr.name FROM mechanisms m
           LEFT JOIN roles sr ON sr.id=m.source_role_id
           LEFT JOIN roles tr ON tr.id=m.target_role_id WHERE m.name='systemisch_eigenaarschap'"""
    ).fetchone()
    print(f"    {row[0]} → {row[1]}")

    nmech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    nrol = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Rollen: {nrol}. Mechanismen: {nmech}.")


if __name__ == "__main__":
    main()
