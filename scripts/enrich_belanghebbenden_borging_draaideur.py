"""
Verrijking theorielaag: belanghebbenden, sourcing-principalen, borgingsstichtingen
en het opschonen van de draaideur-typologie.

Achtergrond — drie samenhangende lacunes in de theorielaag (rollen + mechanismen),
ontstaan uit een modelreview. Alleen theorielaag; geen instance-data, geen schema-
wijziging (alle gebruikte enum-waarden bestonden al).

1. DRAAIDEUR was rommelig: drie deels overlappende mechanismen, waarvan de werkpaard
   (`draaideurconstructie`, 18 relaties) onterecht onder *ideologie* stond en een lege
   variant (`draaideur_politiek_journalistiek`, 0 relaties) redundant was.
   -> `draaideurconstructie` herplaatst naar `cross_filter` en aangescherpt met de vier
      domeinen en richtingen; de lege redundante variant verwijderd.

2. BELANGHEBBENDE ontbrak als concept. Bedrijven hingen alleen als adverteerder/eigenaar
   aan de media. De principaal met een materieel belang die invloedsmiddelen inzet
   (lobby, PR, advertentiedruk, denktank-financiering, draaideur-aanwervingen) had geen rol.
   -> rol `belanghebbende` (systeemactor) + sourcing-mechanisme `belangenbehartiging`
      (principaal -> lobbyist/lobbygroep -> politicus/journalist), met lobby-typologie.

3. VOORLICHTER/POLITICUS/PARTIJ waren los van elkaar gemodelleerd. Dat is functioneel
   correct (de bron versus de toegangs-poortwachter, Chomsky filter 3; Luyendijk), maar
   de *binding* — de partij als coördinerende principaal — ontbrak.
   -> sourcing-mechanisme `gecoordineerde_voorlichting`: de politieke tegenhanger van
      corporate belangenbehartiging (partij/politicus -> voorlichter -> journalist).

4. STICHTING-CONSTRUCTIE was afwezig terwijl ze dubbel-natuurlijk is:
   (a) de STAK (Stichting Administratiekantoor) als controle-/ondoorzichtigheidsvehikel
       boven de familieholding (bv. boven Epifin/DPG) -> aangescherpt in `holdingconstructie`;
   (b) de onafhankelijkheidsstichting met prioriteitsaandeel die de redactie beschermt
       (Stichting Democratie en Media bij DPG; ACM-stichtingen met vetorecht) -> nieuwe
       tegenmacht-rol `borgingsstichting` + mechanisme `onafhankelijkheidsborging`.

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


# --- Nieuwe rollen ----------------------------------------------------------
NEW_ROLES = [
    {
        "name": "belanghebbende",
        "category": "systeemactor",
        "description": (
            "Actor met een materieel belang in hoe een onderwerp wordt gedekt of "
            "gereguleerd (bedrijf, sector, branche, overheidsorgaan, ideologische "
            "beweging) die dat belang behartigt door invloedsmiddelen in te zetten: "
            "lobby, PR, advertentiedruk, denktank-financiering en draaideur-aanwervingen. "
            "Niet elke belanghebbende lobbyt even hard — de mate van georganiseerde "
            "belangenbehartiging verschilt sterk per sector."
        ),
        "examples": (
            "Shell/energie, defensie-industrie, big tech (Uber, Microsoft), "
            "zorgverzekeraars, banken (ING), brancheorganisaties (VNO-NCW)"
        ),
    },
    {
        "name": "borgingsstichting",
        "category": "tegenmacht",
        "description": (
            "Onafhankelijkheidsstichting die — vaak via een prioriteitsaandeel of "
            "statutair vetorecht — de redactionele onafhankelijkheid en continuïteit van "
            "titels beschermt, zónder winstoogmerk. Een rem op de eigenaar binnen de "
            "eigendomsstructuur; tegenpool van het STAK-controlevehikel."
        ),
        "examples": (
            "Stichting Democratie en Media (14,27% + prioriteitsaandeel DPG, beschermt "
            "Trouw/de Volkskrant), continuïteitsstichtingen, de bij de DPG/RTL-overname "
            "door ACM afgedwongen stichtingen met vetorecht over de hoofdredacteur"
        ),
    },
]

# --- Aangescherpte bestaande mechanismen ------------------------------------
UPDATE_MECHANISMS = {
    "draaideurconstructie": {
        "filter": "cross_filter",
        "description": (
            "Personeel circuleert tussen vier domeinen — politiek, bedrijfsleven, "
            "media/journalistiek en lobby/PR — en neemt netwerk en wereldbeeld mee. Alle "
            "richtingen komen voor: minister → corporate bestuur (Eurlings → KLM, Bos → "
            "KPMG), politiek ↔ omroep (Hillen, Van den Brink), journalist → woordvoering, "
            "en lobbyist ↔ overheid/bedrijf (Jack de Vries, Afke Schaart)."
        ),
        "effect": (
            "Gedeelde belangen en wereldbeeld, old-boys-netwerk, verlies van kritische "
            "distantie. Werkt over de filters heen: verbindt eigendom, sourcing én "
            "ideologie — vandaar cross_filter."
        ),
    },
    "holdingconstructie": {
        "filter": "eigendom",
        "description": (
            "Eigendom wordt uitgeoefend via gestapelde tussenvehikels (Epifin, Mediahuis "
            "Partners, VP Exploitatie) en vaak een Stichting Administratiekantoor (STAK) "
            "die de aandelen certificeert: stemrecht/zeggenschap wordt gescheiden van "
            "economisch belang en geconcentreerd bij de familie, terwijl de uiteindelijke "
            "eigenaren buiten beeld blijven. Zo ontstaat afstand tussen familie en redactie "
            "zónder controleverlies."
        ),
        "effect": (
            "Schijn van onafhankelijkheid terwijl eigendomsmacht en zeggenschap intact "
            "blijven; de uiteindelijke begunstigden zijn ondoorzichtig. Redactiestatuten "
            "bieden geen ijzerharde garanties (vgl. de tegenkracht 'onafhankelijkheidsborging')."
        ),
    },
}

# --- Te verwijderen redundante mechanismen (alleen als 0 relaties) ----------
DELETE_MECHANISMS = ["draaideur_politiek_journalistiek"]

# --- Nieuwe mechanismen -----------------------------------------------------
NEW_MECHANISMS = [
    {
        "name": "belangenbehartiging",
        "filter": "sourcing",
        "mechanism_type": "structureel",
        "description": (
            "Een belanghebbende zet zijn materiële belang om in mediabeeld via een keten van "
            "instrumenten: eigen public-affairs, ingehuurde lobbyisten/lobbygroepen, "
            "brancheorganisaties en denktanks. Die keten voedt zowel politici (kant-en-klare "
            "Kamervragen, amendementen) als journalisten (achtergrond, exclusieve data, "
            "'experts'). De soorten lobby verschillen: corporate-sectoraal (Shell, defensie, "
            "big tech), branche/koepel (VNO-NCW, sectorfederaties) en ideologisch/NGO."
        ),
        "effect": (
            "De oorsprong van een frame blijft onzichtbaar: belangengestuurde informatie "
            "verschijnt als neutraal nieuws of als 'onafhankelijke' politieke vraag. Goed "
            "georganiseerde belangen zijn structureel oververtegenwoordigd; diffuse belangen "
            "(consumenten, toekomstige generaties) ontbreken."
        ),
        # De principaal raakt de media NOOIT direct: hij zet een instrument in. Het
        # mechanisme tekent daarom de eerste schakel (belanghebbende -> lobbyist); de
        # vervolgschakels (lobbyist -> journalist/politicus) zijn aparte mechanismen.
        "source_role": "belanghebbende",
        "target_role": "lobbyist",
    },
    {
        "name": "gecoordineerde_voorlichting",
        "filter": "sourcing",
        "mechanism_type": "structureel",
        "description": (
            "Een politieke partij of bewindspersoon functioneert als coördinerende "
            "principaal: politicus, partij-apparaat en voorlichter/woordvoerder leveren één "
            "afgestemde, voorverpakte boodschap. De voorlichter is de poortwachter die bepaalt "
            "wie toegang krijgt tot de politicus (Luyendijk, 'Je hebt het niet van mij, "
            "maar...'). Dit is de politieke tegenhanger van corporate belangenbehartiging: "
            "dezelfde sourcing-logica, een andere principaal."
        ),
        "effect": (
            "Politicus en voorlichter zijn analytisch aparte rollen — de bron versus de "
            "toegangs-poortwachter — maar opereren langs de partijlijn als één bronmachine. "
            "De journalist ruilt kritische distantie in voor toegang; de verslaggeving volgt "
            "agenda en frame van de machthebber (zie ook 'haagse_stam')."
        ),
        # Zelfde logica als belangenbehartiging: de partij/politicus bereikt de journalist
        # via de voorlichter (poortwachter). Eerste schakel = politicus -> voorlichter;
        # voorlichter -> journalist is het bestaande 'voorlichter_informatiefilter'.
        "source_role": "politicus",
        "target_role": "voorlichter",
    },
    {
        "name": "onafhankelijkheidsborging",
        "filter": "tegenmacht",
        "mechanism_type": "juridisch",
        "description": (
            "Een onafhankelijkheidsstichting houdt een prioriteitsaandeel of statutair "
            "vetorecht en gebruikt dat om de benoeming van de hoofdredacteur en de "
            "redactionele koers te beschermen tegen de commerciële eigenaar. Gekoppeld aan "
            "het redactiestatuut. Voorbeelden: Stichting Democratie en Media bij DPG (Trouw, "
            "de Volkskrant); de door ACM bij de DPG/RTL-overname afgedwongen stichtingen met "
            "vetorecht."
        ),
        "effect": (
            "Structurele rem op eigenaarsinvloed, maar geen ijzeren garantie: het "
            "redactiestatuut is geen harde juridische muur en de stichting is een "
            "minderheidsbelang naast de winstgedreven meerderheid."
        ),
        "source_role": "borgingsstichting",
        "target_role": "hoofdredacteur",
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

    # 1. nieuwe rollen (idempotent)
    for r in NEW_ROLES:
        exists = conn.execute("SELECT 1 FROM roles WHERE name = ?", (r["name"],)).fetchone()
        if exists:
            print(f"Rol bestaat al: {r['name']} — overgeslagen.")
        else:
            conn.execute(
                "INSERT INTO roles (name, category, description, examples) VALUES (?, ?, ?, ?)",
                (r["name"], r["category"], r["description"], r["examples"]),
            )
            print(f"Rol toegevoegd: {r['name']} ({r['category']})")

    # 2. bestaande mechanismen aanscherpen / herplaatsen
    for name, fields in UPDATE_MECHANISMS.items():
        cur = conn.execute(
            "UPDATE mechanisms SET filter = ?, description = ?, effect = ? WHERE name = ?",
            (fields["filter"], fields["description"], fields["effect"], name),
        )
        if cur.rowcount:
            print(f"Aangescherpt: {name} -> filter={fields['filter']}")
        else:
            print(f"Let op: mechanisme '{name}' niet gevonden — niets aangepast.")

    # 3. redundante lege mechanismen verwijderen (guard: 0 relaties)
    for name in DELETE_MECHANISMS:
        row = conn.execute("SELECT id FROM mechanisms WHERE name = ?", (name,)).fetchone()
        if row is None:
            print(f"Verwijderen overgeslagen: '{name}' bestaat niet (al weg).")
            continue
        n = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id = ?", (row[0],)).fetchone()[0]
        if n:
            print(f"NIET verwijderd: '{name}' heeft nog {n} relaties — laat staan.")
        else:
            conn.execute("DELETE FROM mechanisms WHERE id = ?", (row[0],))
            print(f"Verwijderd (redundant, 0 relaties): {name}")

    # 4. nieuwe mechanismen (idempotent: bestaat al -> rol-paar/tekst bijwerken)
    for m in NEW_MECHANISMS:
        exists = conn.execute("SELECT 1 FROM mechanisms WHERE name = ?", (m["name"],)).fetchone()
        if exists:
            conn.execute(
                """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
                   source_role_id=?, target_role_id=? WHERE name=?""",
                (
                    m["filter"], m["mechanism_type"], m["description"], m["effect"],
                    role_id(conn, m["source_role"]), role_id(conn, m["target_role"]), m["name"],
                ),
            )
            print(f"Mechanisme bijgewerkt: {m['name']} ({m['source_role']} → {m['target_role']})")
        else:
            conn.execute(
                """INSERT INTO mechanisms
                   (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"],
                    role_id(conn, m["source_role"]), role_id(conn, m["target_role"]),
                ),
            )
            print(f"Mechanisme toegevoegd: {m['name']} ({m['filter']}) "
                  f"{m['source_role']} → {m['target_role']}")

    conn.commit()
    nroles = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    nmech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Totaal rollen: {nroles}, mechanismen: {nmech}")


if __name__ == "__main__":
    main()
