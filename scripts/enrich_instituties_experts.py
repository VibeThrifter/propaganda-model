"""
Verrijking theorielaag: gezaghebbende instituties, experts en herijking van de
ideologie-laag (sourcing-autoriteit + hegemonische reproductie).

Achtergrond — uit de modelreview kwamen drie dingen samen:

1. GEZAGHEBBENDE INSTITUTIES & EXPERTS ontbraken. Het model kende de academicus alleen als
   *criticus* en instituties alleen als `toezichthouder`/`denktank`. De dominante realiteit —
   het 'neutrale' gezaghebbende instituut en de gecrediteerde expert die de consensus
   *legitimeren* — is kern-sourcing: Herman & Chomsky's 'experts' én Stuart Halls 'primaire
   definieerders'. -> rollen `gezagsinstituut`, `gezagsexpert`; mechanismen
   `institutioneel_gezag`, `expert_legitimatie`. Plus: zeven fout/niet-gerolde instituties
   herrold naar `gezagsinstituut`.

2. VOORLICHTING (Luyendijk-verfijning). De voorlichter dient een partij/bewindspersoon ÓF
   een ministerie/instituut (RVD), en het smeermiddel is *access* — de off-the-record
   Nieuwspoort-code 'je hebt het niet van mij, maar...'. -> `gecoordineerde_voorlichting`
   aangescherpt.

3. IDEOLOGIE-HERIJKING. De `academisch_criticus` die filters blootlegt is in NL marginaal en
   niet de relevante actor (0 entiteiten, 0 relaties). Relevanter zijn universiteiten/
   kennisinstituten als dragers van de dominante hegemonie: cultureel links-progressief én
   economisch neoliberaal — Nancy Fraser's 'progressief neoliberalisme', langs Gramsciaanse
   'consent'. -> rol `academisch_criticus` + mechanismen `academische_blootlegging`/
   `academische_kritiek` verwijderd; rol `kennisinstituut` + mechanisme
   `academische_socialisatie` toegevoegd.

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


NEW_ROLES = [
    {
        "name": "gezagsinstituut",
        "category": "sourcing",
        "description": (
            "Officieel, gezaghebbend instituut dat door media als neutrale, geloofwaardige "
            "routinebron wordt behandeld — een 'primaire definieerder' (Hall) die de termen "
            "van het debat zet vóór de journalistiek begint. Cijfers, prognoses en rapporten "
            "gelden als feit, niet als standpunt."
        ),
        "examples": "CPB, DNB, CBS, RIVM, WRR, OMT, ministeries, Openbaar Ministerie/politie",
    },
    {
        "name": "gezagsexpert",
        "category": "sourcing",
        "description": (
            "Gecrediteerde deskundige (hoogleraar, econoom, viroloog, veiligheidsexpert) die "
            "als 'onafhankelijke' autoriteit wordt opgevoerd en daarmee de consensus "
            "naturaliseert. Vaak ingebed in universiteiten of kennisinstituten die de "
            "dominante hegemonie reproduceren."
        ),
        "examples": (
            "Bankeconomen, hoogleraren staatsrecht, defensie-/veiligheidsexperts, "
            "gezondheidsdeskundigen in talkshows"
        ),
    },
    {
        "name": "kennisinstituut",
        "category": "ideologie",
        "description": (
            "Universiteit, journalistiekopleiding of onderzoeksinstituut dat de dominante "
            "hegemonie reproduceert en als 'neutrale' wetenschap presenteert. In Nederland is "
            "die hegemonie een specifieke combinatie: cultureel links-progressief (politics of "
            "recognition: diversiteit, identiteit) én economisch neoliberaal — wat Nancy "
            "Fraser 'progressief neoliberalisme' noemt, langs Gramsciaanse 'consent'."
        ),
        "examples": "Universiteiten, journalistiekopleidingen (UvA), onderzoeksinstituten",
    },
]

NEW_MECHANISMS = [
    {
        "name": "institutioneel_gezag",
        "filter": "sourcing",
        "mechanism_type": "structureel",
        "description": (
            "Officiële instituties functioneren als primaire definieerders: hun rapporten, "
            "prognoses en statistieken worden als neutraal feit overgenomen en bepalen agenda "
            "en kader van een onderwerp. Journalisten behandelen ze als gratis, geloofwaardige, "
            "gezagvolle routinebron."
        ),
        "effect": (
            "Het institutionele kader wordt het vanzelfsprekende vertrekpunt; alternatieve "
            "probleemdefinities moeten 'tegen de feiten in' bewijzen. De aannames achter een "
            "CPB-doorrekening of een RIVM-advies blijven onbesproken."
        ),
        "source_role": "gezagsinstituut",
        "target_role": "journalist",
    },
    {
        "name": "expert_legitimatie",
        "filter": "sourcing",
        "mechanism_type": "discursief",
        "description": (
            "De gecrediteerde deskundige wordt als 'neutrale' autoriteit opgevoerd; zijn "
            "institutionele inbedding en aannames blijven buiten beeld. Vult `expert_framing` "
            "(denktank-selectie) aan op het niveau van de individuele expert."
        ),
        "effect": (
            "De consensus krijgt het aureool van wetenschappelijke objectiviteit; het debat "
            "versmalt tot wat 'de experts' al delen, terwijl afwijkende deskundigen als "
            "'querulant' of 'activist' wegvallen."
        ),
        "source_role": "gezagsexpert",
        "target_role": "journalist",
    },
    {
        "name": "academische_socialisatie",
        "filter": "ideologie",
        "mechanism_type": "discursief",
        "description": (
            "Universiteiten en journalistiekopleidingen socialiseren toekomstige journalisten "
            "en bestuurders in de dominante hegemonie — cultureel progressief én economisch "
            "neoliberaal ('progressief neoliberalisme', Fraser) — die als neutrale, "
            "wetenschappelijke vanzelfsprekendheid geldt."
        ),
        "effect": (
            "De grenzen van het 'redelijke' debat worden al vóór de redactievloer gezet; "
            "afwijking van de consensus verschijnt niet als ander standpunt maar als gebrek "
            "aan kennis of als 'activisme'. De bias is emergent, niet gecoördineerd."
        ),
        "source_role": "kennisinstituut",
        "target_role": "journalist",
    },
]

# Aanscherping bestaand mechanisme (Luyendijk): voorlichter dient partij ÓF instituut,
# smeermiddel is access (off-the-record Nieuwspoort-code 'je hebt het niet van mij').
UPDATE_MECHANISMS = {
    "gecoordineerde_voorlichting": {
        "filter": "sourcing",
        "description": (
            "Een principaal — een politieke partij/bewindspersoon ÓF een ministerie/instituut "
            "(Rijksvoorlichtingsdienst, departementale woordvoerders) — levert via de "
            "voorlichter één afgestemde, voorverpakte boodschap. De voorlichter is de "
            "poortwachter: hij beheert de toegang tot de minister/politicus en deelt die uit "
            "als beloning of straf (vgl. `toegangsdisciplinering`). Smeermiddel is de "
            "off-the-record-cultuur — de Nieuwspoort-code 'je hebt het niet van mij, maar...' "
            "(Luyendijk) — waarmee op de achtergrond wordt gelekt."
        ),
        "effect": (
            "Politicus/instituut en voorlichter zijn analytisch aparte rollen — de bron versus "
            "de toegangs-poortwachter — maar opereren als één bronmachine. In hun jacht op "
            "primeurs en toegang worden journalisten minder kritisch; de vage code wekt "
            "zelfcensuur omdat niemand hem wil breken (zie `haagse_stam`)."
        ),
    },
}

# Ideologie-herijking: de marginale 'criticus' eruit (0 entiteiten/relaties geverifieerd).
# Eerst de laatste verwijzing herrichten: toegangsdisciplinering disciplineert niet de
# 'filter-blootleggende academicus' maar de afwijkende talkshow-deskundige -> gezagsexpert.
REPOINT_TARGET = {"toegangsdisciplinering": "gezagsexpert"}
DELETE_MECHANISMS = ["academische_blootlegging", "academische_kritiek"]
DELETE_ROLES = ["academisch_criticus"]

# Zeven duidelijke gevallen -> gezagsinstituut (de vier discutabele blijven ongemoeid).
RE_ROLE = {
    "WRR (Wetenschappelijke Raad voor het Regeringsbeleid)": "gezagsinstituut",
    "CPB (Centraal Planbureau)": "gezagsinstituut",
    "RIVM": "gezagsinstituut",
    "OMT (Outbreak Management Team)": "gezagsinstituut",
    "Ministerie van Defensie": "gezagsinstituut",
    "Ministerie van Buitenlandse Zaken": "gezagsinstituut",
    "Politie": "gezagsinstituut",
}


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

    # 1. nieuwe rollen
    for r in NEW_ROLES:
        if conn.execute("SELECT 1 FROM roles WHERE name = ?", (r["name"],)).fetchone():
            print(f"Rol bestaat al: {r['name']} — overgeslagen.")
        else:
            conn.execute(
                "INSERT INTO roles (name, category, description, examples) VALUES (?, ?, ?, ?)",
                (r["name"], r["category"], r["description"], r["examples"]),
            )
            print(f"Rol toegevoegd: {r['name']} ({r['category']})")

    # 2. nieuwe mechanismen (idempotent: bestaat al -> bijwerken)
    for m in NEW_MECHANISMS:
        params = (
            m["filter"], m["mechanism_type"], m["description"], m["effect"],
            role_id(conn, m["source_role"]), role_id(conn, m["target_role"]),
        )
        if conn.execute("SELECT 1 FROM mechanisms WHERE name = ?", (m["name"],)).fetchone():
            conn.execute(
                """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
                   source_role_id=?, target_role_id=? WHERE name=?""",
                (*params, m["name"]),
            )
            print(f"Mechanisme bijgewerkt: {m['name']}")
        else:
            conn.execute(
                """INSERT INTO mechanisms
                   (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (m["name"], *params),
            )
            print(f"Mechanisme toegevoegd: {m['name']} ({m['source_role']} → {m['target_role']})")

    # 3. bestaand mechanisme aanscherpen
    for name, f in UPDATE_MECHANISMS.items():
        cur = conn.execute(
            "UPDATE mechanisms SET filter=?, description=?, effect=? WHERE name=?",
            (f["filter"], f["description"], f["effect"], name),
        )
        print(f"Aangescherpt: {name}" if cur.rowcount else f"Let op: '{name}' niet gevonden.")

    # 3b. laatste criticus-verwijzing herrichten (zodat de rol straks weg kan)
    for mech, new_target in REPOINT_TARGET.items():
        cur = conn.execute(
            "UPDATE mechanisms SET target_role_id=? WHERE name=?",
            (role_id(conn, new_target), mech),
        )
        print(f"Herricht: {mech} → {new_target}" if cur.rowcount else f"Let op: '{mech}' niet gevonden.")

    # 4. criticus-mechanismen verwijderen (guard: 0 relaties)
    for name in DELETE_MECHANISMS:
        row = conn.execute("SELECT id FROM mechanisms WHERE name = ?", (name,)).fetchone()
        if row is None:
            print(f"Verwijderen overgeslagen: mechanisme '{name}' bestaat niet.")
            continue
        n = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (row[0],)).fetchone()[0]
        if n:
            print(f"NIET verwijderd: '{name}' heeft nog {n} relaties.")
        else:
            conn.execute("DELETE FROM mechanisms WHERE id = ?", (row[0],))
            print(f"Verwijderd (0 relaties): {name}")

    # 5. criticus-rol verwijderen (guard: 0 entiteiten, geen mechanisme-referentie)
    for name in DELETE_ROLES:
        row = conn.execute("SELECT id FROM roles WHERE name = ?", (name,)).fetchone()
        if row is None:
            print(f"Verwijderen overgeslagen: rol '{name}' bestaat niet.")
            continue
        rid = row[0]
        in_ent = conn.execute("SELECT COUNT(*) FROM entities WHERE primary_role_id=?", (rid,)).fetchone()[0]
        in_er = conn.execute("SELECT COUNT(*) FROM entity_roles WHERE role_id=?", (rid,)).fetchone()[0]
        in_mech = conn.execute(
            "SELECT COUNT(*) FROM mechanisms WHERE source_role_id=? OR target_role_id=?", (rid, rid)
        ).fetchone()[0]
        if in_ent or in_er or in_mech:
            print(f"NIET verwijderd: rol '{name}' nog in gebruik "
                  f"(entiteiten={in_ent}, entity_roles={in_er}, mechanismen={in_mech}).")
        else:
            conn.execute("DELETE FROM roles WHERE id = ?", (rid,))
            print(f"Verwijderd (ongebruikt): rol {name}")

    # 6. instituties herrollen + entity_roles synchroniseren
    for ent_name, new_role in RE_ROLE.items():
        e = conn.execute("SELECT id, primary_role_id FROM entities WHERE name = ?", (ent_name,)).fetchone()
        if e is None:
            print(f"Let op: entiteit '{ent_name}' niet gevonden — overgeslagen.")
            continue
        eid, old_pr = e
        new_id = role_id(conn, new_role)
        if old_pr == new_id:
            print(f"Al correct gerold: {ent_name}")
            continue
        conn.execute("UPDATE entities SET primary_role_id = ? WHERE id = ?", (new_id, eid))
        if old_pr is not None:
            conn.execute("DELETE FROM entity_roles WHERE entity_id = ? AND role_id = ?", (eid, old_pr))
        if not conn.execute(
            "SELECT 1 FROM entity_roles WHERE entity_id = ? AND role_id = ?", (eid, new_id)
        ).fetchone():
            conn.execute(
                "INSERT INTO entity_roles (entity_id, role_id, notes) VALUES (?, ?, ?)",
                (eid, new_id, "herrold: primaire definieerder"),
            )
        old_name = conn.execute("SELECT name FROM roles WHERE id = ?", (old_pr,)).fetchone() if old_pr else None
        print(f"Herrold: {ent_name}  {old_name[0] if old_name else 'geen'} → {new_role}")

    conn.commit()
    nroles = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    nmech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Totaal rollen: {nroles}, mechanismen: {nmech}")


if __name__ == "__main__":
    main()
