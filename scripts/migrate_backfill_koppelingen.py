#!/usr/bin/env python3
"""
Migratie: backfill koppelingsplicht (verbeterplan M0.4, juni 2026).

Dicht de Z6-achterstand die scripts/validate_model.py rapporteert:
  1. 108 van de 114 ongekoppelde relaties krijgen een bestaand mechanisme
     (mapping hieronder, per mechanisme gemotiveerd); de overige 6 staan als
     kandidaten voor nieuwe theorie-elementen in BACKFILL_REVIEW.md (M2.3-input);
  2. elke relatie mét mechanisme maar zonder instantiations-rij krijgt er één;
  3. 11 entiteiten zonder rol krijgen een primary_role_id (+ entity_roles-spiegel);
  4. elke entiteit mét primaire rol maar zonder instantiatie krijgt er één.

Backfill-instantiaties krijgen exemplariteit 0.8 (bewust onder de 1.0-norm:
nog niet handmatig gewogen) en een CONTRIB-tag in notes/edit_log zodat de
eigenaar ze kan reviewen (BACKFILL_REVIEW.md bevat de volledige werklijst).
Idempotent; conventie: backup-then-migrate.
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "data" / "propaganda_model.db"

TAG = "backfill-M0.4 (agent; review eigenaar)"
EXEMPLARITEIT = 0.8

# Relatie-ids per mechanisme, met de motivering die in edit_log landt.
KOPPELINGEN = {
    "eigendomsconcentratie": (
        [12, 14, 17, 159, 195, 196, 197, 198, 199],
        "aandeelhouderschap/eigendom van nieuwsmedia: de concentratie-as zelf (duopolie-"
        "aandeelhouders, ANP-eigendom, consolidatietrail PCM/Sanoma/TMG)"),
    "familiezeggenschap": (
        [18, 74, 75, 156],
        "persoon/familie controleert het eigendomsvehikel (Talpa, Concentra, "
        "VP Exploitatie, Mediahuis Partners)"),
    "systemisch_eigenaarschap": (
        [70, 71, 72, 160, 182, 183, 184, 185, 200, 289, 290, 291, 292, 293],
        "institutionele beleggers/holdings als stille aandeelhouder in (adverterende) concerns"),
    "denktank_financiering_bias": (
        [40, 41, 64, 152, 153, 154, 44, 45],
        "belanghebbende financiert/stuurt denktank of wetenschappelijk bureau"),
    "belang_elite_netwerk": (
        [60, 61, 62, 331, 332, 333, 334],
        "bedrijfstop in elite-fora (Bilderberg); 60-62 zijn omgekeerde duplicaten "
        "van 331-334 — zie reviewlijst"),
    "partijlijn": (
        [125, 126, 131, 379, 381, 383, 385, 387, 393,
         336, 343, 345, 347, 349, 352, 354, 356],
        "partijlidmaatschap/-functie van politicus: binding aan de partijlijn"),
    "parlementaire_controle": (
        [257, 258, 49, 50, 256],
        "Kamerleden/parlement als controleurs van de uitvoeringsmacht (Toeslagenaffaire)"),
    "politicus_als_bron": (
        [103, 104, 127, 262, 259, 260, 261],
        "politicus voedt media als bron / dwingt agendering af"),
    "vakbond_bescherming": (
        [138, 139, 137, 319, 320, 321, 322],
        "NVJ/Free Press Unlimited beschermen journalisten bij omroep en uitgevers"),
    "politieke_synchronisatie": (
        [287, 288],
        "partijen volgen de Atlantische consensus (richting instantie omgekeerd "
        "t.o.v. mechanisme — zie reviewlijst)"),
    "externe_mediafinanciering": (
        [408],
        "externe financier (OSF) financiert mediastichting"),
    "toezicht_tandeloosheid": (
        [117, 118, 119, 122, 123],
        "toezicht/zelfregulering zonder bindende sancties (CvdM signaleert, "
        "RvdJ kan niet sanctioneren)"),
    "toezichthouder_interventie": (
        [124, 330, 372],
        "actief toezicht: ACM-mededinging, NU.nl-borgingsstichting, Mediawet-handhaving"),
    "expert_framing": (
        [120, 121],
        "WRR-analyse stuurt het mediadebat: kennisinstituut als frame-leverancier"),
    "academische_socialisatie": (
        [303, 304],
        "journalistiekopleiding vormt en levert redactiepersoneel"),
    "expert_legitimatie": (
        [325, 326],
        "vaste expert/commentator verleent gezag aan berichtgeving"),
    "geweld_intimidatie": (
        [48],
        "moord op Peter R. de Vries als extreem geweld tegen journalisten"),
    "onderzoeksjournalist_doorbraak": (
        [88, 171, 172],
        "onderzoeksjournalistiek brak Toeslagenaffaire/Bulgarenfraude open"),
    "burgerinitiatief_druk": (
        [90],
        "BOinK agendeerde de toeslagenproblemen jaren vóór de doorbraak"),
    "onafhankelijk_medium_tegenwicht": (
        [263, 264, 305, 306],
        "alternatieve media positioneren zich expliciet tegen de mainstream-consensus"),
    "denktank_levert_expert": (
        [38],
        "HCSS-directeurschap maakt De Wijk tot mediabeschikbare gezagsexpert "
        "(richting instantie omgekeerd — zie reviewlijst)"),
    "draaideur_politiek_institutie": (
        [341],
        "politicus bekleedt ambt bij gezagsinstituut (Defensie)"),
    "pakketjournalistiek": (
        [425, 426],
        "internationale persbureaus zijn de groothandel achter het ANP-buitenlandnieuws"),
}

# Restgroep: géén bestaand mechanisme past — kandidatenlijst voor M2.3 (BACKFILL_REVIEW.md).
KANDIDATEN = [409, 225, 242, 411, 327, 328]

# Entiteit-id -> (rolnaam, motivering)
ROLLEN = {
    52: ("gezagsinstituut", "uitvoeringsmacht met informatiemonopolie (Toeslagenaffaire)"),
    71: ("gezagsinstituut", "staatsinstituut; aanwezig in elite-fora"),
    80: ("belanghebbende", "consultancy met beleidsbelangen; sponsor Nationale DenkTank"),
    103: ("kennisinstituut", "universiteit; onderzocht ANP-afhankelijkheid"),
    104: ("kennisinstituut", "journalistiekopleiding"),
    122: ("lobbyist", "PR-/lobbybureau, actief in de defensielobby"),
    123: ("belanghebbende", "Big Four-adviesbureau met overheidsopdrachten"),
    124: ("belanghebbende", "Big Four-adviesbureau met overheidsopdrachten"),
    126: ("belanghebbende", "platformbedrijf als lobby-actor (Uber-files-context)"),
    127: ("belanghebbende", "ingenieurs-/adviesbureau als lobby-actor"),
    128: ("belanghebbende", "techconcern als EU-lobby-actor (functie in dít model)"),
    # Hadden wel een entity_roles-rij maar geen primaire rol:
    107: ("parlementair_controleur", "de Kamer als controleur van de uitvoeringsmacht "
          "(consistent met relatie #256 → parlementaire_controle; oude rol 'politicus' "
          "blijft als extra entity_roles-rij staan)"),
    125: ("belanghebbende", "staatsgesteund bedrijf met mediabelang (KLM-steunpakket)"),
}


def main():
    if not DB_PATH.exists():
        sys.exit(f"Database niet gevonden: {DB_PATH}")
    backup = DB_PATH.with_name(
        f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")

    mech_id = {r[1]: r[0] for r in conn.execute("SELECT id, name FROM mechanisms")}
    rol_id = {r[1]: r[0] for r in conn.execute("SELECT id, name FROM roles")}

    # 1. Mechanisme-koppelingen
    gekoppeld = 0
    for mechanisme, (rel_ids, waarom) in KOPPELINGEN.items():
        mid = mech_id.get(mechanisme)
        if mid is None:
            sys.exit(f"Mechanisme '{mechanisme}' bestaat niet — mapping verouderd?")
        for rid in rel_ids:
            rij = conn.execute(
                "SELECT mechanism_id FROM relations WHERE id = ?", (rid,)).fetchone()
            if rij is None:
                print(f"  LET OP: relatie #{rid} bestaat niet (overgeslagen)")
                continue
            if rij[0] is not None:
                continue  # idempotent: al gekoppeld
            conn.execute("UPDATE relations SET mechanism_id = ? WHERE id = ?", (mid, rid))
            conn.execute("""
                INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
                VALUES ('relations', ?, 'updated', ?, ?, ?)
            """, (rid, TAG, f'{{"mechanism_id": {mid}}}',
                  f"M0.4-koppeling aan '{mechanisme}': {waarom}"))
            gekoppeld += 1
    print(f"1. {gekoppeld} relaties aan een mechanisme gekoppeld "
          f"({len(KANDIDATEN)} kandidaten blijven open, zie BACKFILL_REVIEW.md)")

    # 2. Ontbrekende mechanisme-instantiaties
    rijen = conn.execute("""
        SELECT r.id, r.mechanism_id FROM relations r
        WHERE r.mechanism_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM instantiations i
                          WHERE i.relation_id = r.id AND i.mechanism_id = r.mechanism_id)
    """).fetchall()
    for rid, mid in rijen:
        conn.execute("""
            INSERT OR IGNORE INTO instantiations (mechanism_id, relation_id, exemplarity, notes)
            VALUES (?, ?, ?, ?)
        """, (mid, rid, EXEMPLARITEIT, TAG))
    print(f"2. {len(rijen)} mechanisme-instantiaties aangevuld (exemplariteit {EXEMPLARITEIT})")

    # 3. Rollen voor rolloze entiteiten
    rollen_gezet = 0
    for eid, (rolnaam, waarom) in ROLLEN.items():
        rij = conn.execute(
            "SELECT primary_role_id FROM entities WHERE id = ?", (eid,)).fetchone()
        if rij is None:
            print(f"  LET OP: entiteit #{eid} bestaat niet (overgeslagen)")
            continue
        if rij[0] is not None:
            continue
        rid = rol_id.get(rolnaam)
        if rid is None:
            sys.exit(f"Rol '{rolnaam}' bestaat niet — mapping verouderd?")
        conn.execute("UPDATE entities SET primary_role_id = ? WHERE id = ?", (rid, eid))
        conn.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id, notes) "
                     "VALUES (?, ?, ?)", (eid, rid, TAG))
        conn.execute("""
            INSERT INTO edit_log (table_name, record_id, action, changed_by, new_value, reason)
            VALUES ('entities', ?, 'updated', ?, ?, ?)
        """, (eid, TAG, f'{{"primary_role_id": {rid}}}',
              f"M0.4-rol '{rolnaam}': {waarom}"))
        rollen_gezet += 1
    print(f"3. {rollen_gezet} entiteiten een primaire rol gegeven")

    # 4. Ontbrekende rol-instantiaties
    rijen = conn.execute("""
        SELECT e.id, e.primary_role_id FROM entities e
        WHERE e.primary_role_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM instantiations i WHERE i.entity_id = e.id)
    """).fetchall()
    for eid, rid in rijen:
        conn.execute("""
            INSERT OR IGNORE INTO instantiations (role_id, entity_id, exemplarity, notes)
            VALUES (?, ?, ?, ?)
        """, (rid, eid, EXEMPLARITEIT, TAG))
    print(f"4. {len(rijen)} rol-instantiaties aangevuld (exemplariteit {EXEMPLARITEIT})")

    conn.commit()
    conn.close()
    print("Klaar. Draai scripts/validate_model.py om de nieuwe stand te zien;"
          " de werklijst voor review staat in BACKFILL_REVIEW.md.")


if __name__ == "__main__":
    main()
