"""
Verrijking theorie- + instantielaag: `belanghebbende` als principaal-superklasse
over alle vijf filters.

Achtergrond — modelreview. De kapitaal-/belang-kant van het model was "shattered":
dezelfde actorklasse (georganiseerd privaat/elite-belang) stond verspreid over drie
rolcategorieën en was deels fout of onvolledig bedraad. De vijf filters zijn *kanalen*;
achter meerdere kanalen staat dezelfde principaal. Het model kende dat principaal-patroon
al voor sourcing (zie enrich_belanghebbenden_borging_draaideur.py): "de principaal raakt de
media NOOIT direct, hij zet een instrument in; het mechanisme tekent de eerste schakel
(belanghebbende -> lobbyist)". Dit script maakt die eerste schakel SYMMETRISCH voor
advertentie (F2), flak (F4) en ideologie (F5), repareert de fout-bedrade edges, en
populeert de superklasse.

Geen schemawijziging (alle enum-waarden bestonden al). Idempotent: opnieuw draaien is veilig.
Volgt de backup-then-migrate-conventie.

1. SUPERKLASSE VULLEN — `belanghebbende` had 1 instantie (Ster) terwijl de echte
   verschijningen als adverteerder/bedrijf leefden. 13 corporates krijgen de rol
   `belanghebbende` erbij (entity_roles + instantiations); hun instrument-rol blijft primair.

2. EERSTE-SCHAKELS symmetrisch maken (de principaal -> zijn instrument, per filter):
   - F2 advertentie:   NEW adverteren_als_belang   belanghebbende -> adverteerder
   - F5 ideologie:      NEW belang_elite_netwerk     belanghebbende -> elite_forum
   (De verzuiling van ledenomroepen zit al in het bestaande mechanisme `omroepverzuiling`
    (ledenomroep -> partij, 3 relaties); daar voegen we niets aan toe. Een eerdere versie
    van dit script maakte een duplicaat `verzuilde_identiteit` — dat wordt nu opgeruimd.)

3. CORRECTIES van fout-/ondergespecificeerde bedrading:
   - denktank_financiering_bias: bron adverteerder       -> belanghebbende
   - juridische_dreiging:        lege bron               -> belanghebbende
   - slapp_tegen_journalist:     lege bron               -> belanghebbende
   - systemisch_eigenaarschap:   target mediaeigenaar    -> belanghebbende
        (matcht de data: BlackRock/Vanguard -> Shell/ING/Unilever/...; de systemische
         eigenaarslaag zit achter de HELE kapitaalcluster, niet als pijl naar de eigenaar)
   - aandeelhouder_druk:         target mediaeigenaar    -> mediaorganisatie
   - rol-descripties `aandeelhouder` / `institutioneel_belegger` ontdubbeld
     (directe actieve deelneming versus passieve systemische achtergrond).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


# --- 1. Superklasse vullen: corporates -> rol belanghebbende -----------------
# (entiteitsnaam, exemplariteit). Exemplariteit ~ hoe prototypisch/georganiseerd
# het belang is: sterk lobbyende sectoren hoog, pure retail-adverteerders lager.
BELANGHEBBENDE_ENTITIES = [
    ("Shell", 0.90), ("ING", 0.90), ("ASML", 0.90), ("Philips", 0.90),
    ("Unilever", 0.75), ("Procter & Gamble", 0.75),
    ("Albert Heijn", 0.45), ("Lidl", 0.45), ("A.S. Watson (Kruidvat)", 0.45), ("Bol.com", 0.45),
    ("Nederlandse Loterij", 0.50), ("Postcode Loterij", 0.50), ("Unibet", 0.50),
]
ENTITY_ROLE_NOTE = (
    "Instrument-rol (bv. adverteerder) blijft primair; belanghebbende = de principaal-"
    "superklasse die via meerdere filters projecteert (modelreview)."
)

# --- 2. Nieuwe mechanismen: de ontbrekende eerste-schakels -------------------
NEW_MECHANISMS = [
    {
        "name": "adverteren_als_belang",
        "filter": "advertentie",
        "mechanism_type": "economisch",
        "description": (
            "De eerste schakel van het advertentie-instrument: een belanghebbende "
            "(bedrijf/sector/branche) zet advertentiebudget in en verschijnt richting de "
            "redactie in de 'adverteerder-hoed'. Dezelfde principaal die elders lobbyt of "
            "procedeert, drukt hier via de advertentie-euro. Niet elke belanghebbende doet dit "
            "even hard; grote, geconcentreerde adverteerders (retail, FMCG, loterijen) hebben "
            "de meeste hefboom."
        ),
        "effect": (
            "Maakt expliciet dat de adverteerder geen losse actor is maar een "
            "verschijningsvorm van een belanghebbende. De vervolgschakel naar de media is het "
            "bestaande 'advertentiedruk' / 'commerciele_afhankelijkheid'."
        ),
        "source_role": "belanghebbende",
        "target_role": "adverteerder",
    },
    {
        "name": "belang_elite_netwerk",
        "filter": "cross_filter",
        "mechanism_type": "structureel",
        "description": (
            "Bestuurders van belanghebbenden (CEO's, sectorfederaties) nemen deel aan besloten "
            "elite-fora (Bilderberg, WEF/Davos, European Round Table of Industrialists) en "
            "helpen daar het wereldbeeld van de transnationale kapitaalklasse synchroniseren. "
            "Spiegelt 'mediaeigenaar_elite_netwerk': dezelfde fora binden eigenaar én "
            "belanghebbende."
        ),
        "effect": (
            "Ideologische premissen (vrijemarkt, pro-Atlantisch, 'stakeholder capitalism') "
            "worden buiten het democratisch proces afgestemd en sijpelen via een gedeeld "
            "referentiekader door in media en beleid. Eerste schakel van het ideologie-instrument."
        ),
        "source_role": "belanghebbende",
        "target_role": "elite_forum",
    },
]

# --- Opruimen: duplicaat uit een eerdere scriptversie (alleen als 0 relaties) -
# `verzuilde_identiteit` overlapte volledig met het bestaande `omroepverzuiling`.
DELETE_MECHANISMS = ["verzuilde_identiteit"]

# --- 3a. Correcties op bestaande mechanismen ---------------------------------
# Per mechanisme alleen de te wijzigen velden (source_role/target_role/description/effect).
CORRECT_MECHANISMS = [
    {
        "name": "denktank_financiering_bias",
        "source_role": "belanghebbende",
        "description": (
            "Een belanghebbende (bedrijfsleven, sector, branche, soms de overheid) financiert "
            "denktanks en onderzoeksinstituten; hun onderzoeksagenda weerspiegelt die belangen."
        ),
        "effect": "Schijnbaar onafhankelijke analyses dienen de belangen van financiers ('argumenten op bestelling').",
    },
    {
        "name": "juridische_dreiging",
        "source_role": "belanghebbende",
        "description": (
            "Een belanghebbende — doorgaans een vermogend bedrijf of individu — dreigt met of "
            "start kostbare rechtszaken (SLAPPs) tegen kritische journalisten. Het doel is zelden "
            "de zaak winnen maar de journalist financieel en psychologisch uitputten."
        ),
        "effect": "Chilling effect: journalisten vermijden risicovolle onderwerpen rond kapitaalkrachtige partijen.",
    },
    {
        # bron stond leeg sinds de oude flak_producent-rol verdween
        "name": "slapp_tegen_journalist",
        "source_role": "belanghebbende",
    },
    {
        "name": "systemisch_eigenaarschap",
        "target_role": "belanghebbende",
        "description": (
            "Institutionele beleggers (BlackRock, Vanguard, grote pensioenfondsen) bezitten via "
            "gespreid vermogensbeheer aandelen in vrijwel álle grote beursgenoteerde bedrijven "
            "tegelijk — zowel de holdings achter de media als de corporates die adverteren en "
            "lobbyen. Zo ontstaat een systemische achtergrond achter de hele bezittende klasse, "
            "geen gerichte greep op één media-eigenaar."
        ),
        "effect": (
            "Een gemeenschappelijk klassebelang bij een stabiel, winstgevend kapitalistisch "
            "systeem wordt de stille premisse achter de kapitaalcluster. Diffuus en passief op "
            "de losse relatie (lage influence), maar structureel alomtegenwoordig."
        ),
    },
    {
        "name": "aandeelhouder_druk",
        "target_role": "mediaorganisatie",
        "description": (
            "Een aandeelhouder met een directe (vaak strategische of minderheids-)deelneming eist "
            "rendement en dividendgroei en oefent via stemrecht en governance druk uit op de "
            "mediaorganisatie zelf. Onderscheidt zich van de passieve, systemische institutionele "
            "belegger doordat het belang specifiek en actief is."
        ),
        "effect": "Kostenbesparing op redacties; focus op klikbare content boven kwaliteitsjournalistiek.",
    },
]

# --- 3b. Ontdubbelen van de twee eigenaars-rollen ----------------------------
UPDATE_ROLES = [
    {
        "name": "aandeelhouder",
        "description": (
            "Directe (vaak strategische of minderheids-)deelneming in een mediabedrijf of "
            "-holding, mét stemrecht en governance-invloed — actief en specifiek, in "
            "tegenstelling tot de passieve systemische belegger."
        ),
        "examples": "Strategische investeerders, participatiemaatschappijen, een familie met minderheidsbelang",
    },
    {
        "name": "institutioneel_belegger",
        "description": (
            "Passieve, systemische (mede)eigenaar via gespreid vermogensbeheer: bezit aandelen "
            "namens anderen in vrijwel álle grote beursgenoteerde bedrijven tegelijk en vormt zo "
            "de stille achtergrond achter de hele kapitaalcluster — media-holdings én "
            "adverteerder-corporates. Inherent belang bij een stabiel kapitalistisch systeem."
        ),
        "examples": "BlackRock, Vanguard, grote pensioenfondsen — de facto mede-eigenaren van vrijwel alle beursgenoteerde bedrijven",
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


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    bid = role_id(conn, "belanghebbende")

    # 1. superklasse vullen: rol + instantiatie per corporate (idempotent)
    print("\n-- 1. belanghebbende-superklasse vullen --")
    for name, exemplarity in BELANGHEBBENDE_ENTITIES:
        row = conn.execute("SELECT id FROM entities WHERE name = ?", (name,)).fetchone()
        if row is None:
            print(f"  Let op: entiteit '{name}' niet gevonden — overgeslagen.")
            continue
        eid = row[0]
        conn.execute(
            "INSERT OR IGNORE INTO entity_roles (entity_id, role_id, notes) VALUES (?, ?, ?)",
            (eid, bid, ENTITY_ROLE_NOTE),
        )
        exists = conn.execute(
            "SELECT 1 FROM instantiations WHERE role_id = ? AND entity_id = ?", (bid, eid)
        ).fetchone()
        if exists:
            print(f"  {name}: rol/instantiatie bestaat al — overgeslagen.")
        else:
            conn.execute(
                "INSERT INTO instantiations (role_id, entity_id, exemplarity, notes) VALUES (?, ?, ?, ?)",
                (bid, eid, exemplarity, "Corporate als principaal-belanghebbende (modelreview)."),
            )
            print(f"  {name}: belanghebbende toegevoegd (exemplariteit {exemplarity}).")

    # 2. nieuwe mechanismen (idempotent: bestaat al -> volledig bijwerken)
    print("\n-- 2. nieuwe eerste-schakels --")
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

    # 2b. duplicaat opruimen (guard: alleen verwijderen als 0 relaties eraan hangen)
    print("\n-- 2b. duplicaat opruimen --")
    for name in DELETE_MECHANISMS:
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
            print(f"  verwijderd (duplicaat, 0 relaties): {name}")

    # 3a. correcties op bestaande mechanismen (alleen de opgegeven velden)
    print("\n-- 3a. mechanisme-correcties --")
    for c in CORRECT_MECHANISMS:
        sets, vals = [], []
        if "source_role" in c:
            sets.append("source_role_id = ?"); vals.append(role_id(conn, c["source_role"]))
        if "target_role" in c:
            sets.append("target_role_id = ?"); vals.append(role_id(conn, c["target_role"]))
        if "description" in c:
            sets.append("description = ?"); vals.append(c["description"])
        if "effect" in c:
            sets.append("effect = ?"); vals.append(c["effect"])
        vals.append(c["name"])
        cur = conn.execute(f"UPDATE mechanisms SET {', '.join(sets)} WHERE name = ?", vals)
        if cur.rowcount:
            print(f"  gecorrigeerd: {c['name']} ({', '.join(s.split(' =')[0] for s in sets)})")
        else:
            print(f"  Let op: mechanisme '{c['name']}' niet gevonden — niets aangepast.")

    # 3b. rol-descripties ontdubbelen
    print("\n-- 3b. rol-descripties ontdubbelen --")
    for r in UPDATE_ROLES:
        cur = conn.execute(
            "UPDATE roles SET description = ?, examples = ? WHERE name = ?",
            (r["description"], r["examples"], r["name"]),
        )
        print(f"  {'bijgewerkt' if cur.rowcount else 'NIET gevonden'}: rol {r['name']}")

    conn.commit()
    nmech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    nbelang = conn.execute(
        "SELECT COUNT(*) FROM instantiations WHERE role_id = ?", (bid,)
    ).fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen totaal: {nmech}. Belanghebbende-instantiaties: {nbelang}.")


if __name__ == "__main__":
    main()
