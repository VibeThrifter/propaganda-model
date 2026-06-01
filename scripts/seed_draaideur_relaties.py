#!/usr/bin/env python3
"""
Voegt draaideur-relaties toe aan het model.

Drie categorieën:
1. Journalist → politiek/woordvoering/PR
2. Politicus → bedrijfsleven/lobby
3. Politicus → media (columnist/commentator)

Bronnen:
- Luyendijk, "Je hebt het niet van mij, maar..." (2010) — Haagse stam
- Follow the Money — draaideur-onderzoeken
- Transparency International NL — "kwart oud-politici wordt lobbyist" (2016)
- Diverse nieuwsbronnen
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'propaganda_model.db')


def get_or_create_entity(cur, name, entity_type, description=None):
    cur.execute("SELECT id FROM entities WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO entities (name, type, description) VALUES (?, ?, ?)",
        (name, entity_type, description)
    )
    print(f"  + entiteit: {name} ({entity_type})")
    return cur.lastrowid


def add_relation(cur, source_id, target_id, rel_type, mechanism_id,
                 description, certainty, influence):
    # Check of relatie al bestaat
    cur.execute(
        "SELECT id FROM relations WHERE source_id = ? AND target_id = ? AND relation_type = ?",
        (source_id, target_id, rel_type)
    )
    if cur.fetchone():
        return
    cur.execute(
        """INSERT INTO relations
           (source_id, target_id, relation_type, mechanism_id, description, certainty, influence)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (source_id, target_id, rel_type, mechanism_id, description, certainty, influence)
    )


def main():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    cur = db.cursor()

    # Mechanism IDs
    DRAAIDEUR_J_P = 70   # draaideur_journalistiek_politiek
    DRAAIDEUR_P_J = 71   # draaideur_politiek_journalistiek
    DRAAIDEUR = 18       # draaideurconstructie (generiek)

    print("=== Draaideur-relaties toevoegen ===\n")

    # === Nieuwe entiteiten ===
    print("Entiteiten aanmaken...")

    hans_hillen = get_or_create_entity(cur, "Hans Hillen", "politicus",
        "NOS Journaal politiek correspondent (1977-1982), daarna woordvoerder minister Ruding, "
        "CDA-Kamerlid, CDA-senator, minister van Defensie (2010-2012)")

    jack_de_vries = get_or_create_entity(cur, "Jack de Vries", "lobbyist",
        "CDA-spindoctor, woordvoerder CDA-fractie, campagneleider, "
        "staatssecretaris Defensie (2007-2010), daarna directeur Hill+Knowlton/lobbyist JSF")

    wouter_bos = get_or_create_entity(cur, "Wouter Bos", "politicus",
        "PvdA-leider, vicepremier en minister van Financiën (2007-2010), "
        "daarna partner bij KPMG")

    balkenende = get_or_create_entity(cur, "Jan Peter Balkenende", "politicus",
        "Minister-president (2002-2010), daarna partner bij Ernst & Young")

    eurlings = get_or_create_entity(cur, "Camiel Eurlings", "politicus",
        "CDA-minister van Verkeer en Waterstaat (2007-2010), "
        "daarna directeur KLM (2011)")

    neelie_kroes = get_or_create_entity(cur, "Neelie Kroes", "politicus",
        "VVD-staatssecretaris, minister, Eurocommissaris Mededinging/Digitale Agenda, "
        "daarna lobbyist voor Uber")

    frank_heemskerk = get_or_create_entity(cur, "Frank Heemskerk", "politicus",
        "PvdA-staatssecretaris Economische Zaken (2007-2010), "
        "daarna directeur Royal HaskoningDHV")

    bart_de_liefde = get_or_create_entity(cur, "Bart de Liefde", "politicus",
        "VVD-Kamerlid, woordvoerder Mededinging, "
        "daarna public policy manager bij Uber")

    raymond_knops = get_or_create_entity(cur, "Raymond Knops", "politicus",
        "CDA-Kamerlid, defensiewoordvoerder, staatssecretaris BZK, "
        "daarna lobbyist defensie-industrie")

    tijs_vd_brink = get_or_create_entity(cur, "Tijs van den Brink", "politicus",
        "EO-journalist en presentator (25+ jaar), "
        "daarna CDA-Kamerlid (2025)")

    paul_sneijder = get_or_create_entity(cur, "Paul Sneijder", "voorlichter",
        "NOS-correspondent bij internationale toppen (NAVO, EU), "
        "daarna PvdA-kandidaat EP en persofficier PvdA-delegatie EP")

    afke_schaart = get_or_create_entity(cur, "Afke Schaart", "lobbyist",
        "Directeur public affairs KPN, daarna VVD-Kamerlid ICT/telecom (2010-2012), "
        "daarna senior directeur EU bij Microsoft")

    eeke_vd_veen = get_or_create_entity(cur, "Eeke van der Veen", "politicus",
        "Voorzitter RvB zorgverzekeraar Agis, daarna PvdA-Kamerlid zorg (2006-2012), "
        "daarna voorzitter Zorgbelang Nederland")

    hill_knowlton = get_or_create_entity(cur, "Hill+Knowlton", "pr_bureau",
        "Internationaal PR- en lobbybureau, Nederlandse tak actief in defensie- en JSF-lobby")

    kpmg = get_or_create_entity(cur, "KPMG", "bedrijf",
        "Big Four accountants- en adviesbureau")

    ernst_young = get_or_create_entity(cur, "Ernst & Young", "bedrijf",
        "Big Four accountants- en adviesbureau")

    klm = get_or_create_entity(cur, "KLM", "bedrijf",
        "Nationale luchtvaartmaatschappij")

    uber = get_or_create_entity(cur, "Uber", "bedrijf",
        "Techbedrijf, taxiplatform")

    royal_haskoning = get_or_create_entity(cur, "Royal HaskoningDHV", "bedrijf",
        "Internationaal ingenieurs- en adviesbureau")

    microsoft = get_or_create_entity(cur, "Microsoft", "bedrijf",
        "Techbedrijf, actief in EU-lobby")

    # Bestaande entiteiten ophalen
    def get_id(name):
        cur.execute("SELECT id FROM entities WHERE name = ?", (name,))
        row = cur.fetchone()
        return row[0] if row else None

    nos = get_id("NOS")
    cda = get_id("CDA")
    vvd = get_id("VVD")
    pvda = get_id("PvdA")
    ron_fresen = get_id("Ron Fresen")
    min_defensie = get_id("Ministerie van Defensie")

    print("\nDraaideur-relaties toevoegen...")

    # ============================================================
    # 1. JOURNALIST → POLITIEK / WOORDVOERING / PR
    # ============================================================
    print("\n--- Journalist → Politiek/PR ---")

    # Hans Hillen: NOS journalist → woordvoerder minister Ruding → CDA-politicus → minister Defensie
    add_relation(cur, hans_hillen, nos, 'draaideur', DRAAIDEUR_J_P,
        "Politiek correspondent NOS Journaal (1977-1982), stapte over naar "
        "woordvoering minister Ruding en later CDA-politiek",
        0.95, 0.65)

    add_relation(cur, hans_hillen, cda, 'personeel', None,
        "CDA-Kamerlid, senator, en minister van Defensie (2010-2012)",
        1.0, 0.50)

    # Tijs van den Brink: EO-journalist → CDA-Kamerlid
    add_relation(cur, tijs_vd_brink, nos, 'draaideur', DRAAIDEUR_J_P,
        "25+ jaar EO-journalist/presentator (publieke omroep), "
        "stapte in 2025 over naar CDA als Kamerlid",
        0.95, 0.55)

    # Paul Sneijder: NOS-correspondent → PvdA-persofficier
    add_relation(cur, paul_sneijder, nos, 'draaideur', DRAAIDEUR_J_P,
        "NOS-correspondent bij NAVO/EU-toppen, werd PvdA-kandidaat EP "
        "en persofficier PvdA-delegatie Europees Parlement",
        0.95, 0.50)

    # Ron Fresen: NOS-verslaggever → denktank
    if ron_fresen:
        add_relation(cur, ron_fresen, nos, 'draaideur', DRAAIDEUR_J_P,
            "Voormalig NOS politiek verslaggever, richtte na carrière "
            "een denktank op voor het politieke debat",
            0.90, 0.45)

    # ============================================================
    # 2. POLITICUS → BEDRIJFSLEVEN / LOBBY
    # ============================================================
    print("\n--- Politicus → Bedrijfsleven/Lobby ---")

    # Jack de Vries: staatssecretaris Defensie → Hill+Knowlton (JSF-lobby)
    add_relation(cur, jack_de_vries, hill_knowlton, 'draaideur', DRAAIDEUR,
        "Staatssecretaris Defensie (2007-2010), verdedigde JSF-aankoop, "
        "werd in 2011 directeur Hill+Knowlton dat JSF-belangen behartigde",
        1.0, 0.80)

    if min_defensie:
        add_relation(cur, jack_de_vries, min_defensie, 'personeel', None,
            "Staatssecretaris van Defensie (2007-2010)", 1.0, 0.70)

    # Wouter Bos: minister van Financiën → KPMG
    add_relation(cur, wouter_bos, kpmg, 'draaideur', DRAAIDEUR,
        "Vicepremier en minister van Financiën (2007-2010), "
        "werd partner bij KPMG per 1 oktober 2010 (advies publieke sector)",
        1.0, 0.70)

    add_relation(cur, wouter_bos, pvda, 'personeel', None,
        "PvdA-leider, vicepremier en minister van Financiën (2007-2010)",
        1.0, 0.60)

    # Balkenende: premier → Ernst & Young
    add_relation(cur, balkenende, ernst_young, 'draaideur', DRAAIDEUR,
        "Minister-president (2002-2010), werd partner bij Ernst & Young per april 2011",
        1.0, 0.75)

    add_relation(cur, balkenende, cda, 'personeel', None,
        "CDA-leider en minister-president (2002-2010)", 1.0, 0.60)

    # Camiel Eurlings: minister Verkeer → KLM
    add_relation(cur, eurlings, klm, 'draaideur', DRAAIDEUR,
        "CDA-minister van Verkeer en Waterstaat (2007-2010), had als minister "
        "subsidies aan KLM verleend, werd in 2011 directeur KLM",
        1.0, 0.80)

    add_relation(cur, eurlings, cda, 'personeel', None,
        "CDA-minister van Verkeer en Waterstaat (2007-2010)", 1.0, 0.55)

    # Neelie Kroes: Eurocommissaris → Uber
    add_relation(cur, neelie_kroes, uber, 'draaideur', DRAAIDEUR,
        "Eurocommissaris Mededinging en Digitale Agenda, regelde na aftreden "
        "ontmoeting Uber-CEO met premier Rutte ondanks lobbyverbod",
        0.95, 0.75)

    add_relation(cur, neelie_kroes, vvd, 'personeel', None,
        "VVD-staatssecretaris, minister, Eurocommissaris", 1.0, 0.55)

    # Frank Heemskerk: staatssecretaris EZ → Royal HaskoningDHV
    add_relation(cur, frank_heemskerk, royal_haskoning, 'draaideur', DRAAIDEUR,
        "PvdA-staatssecretaris Economische Zaken (2007-2010), "
        "Royal HaskoningDHV profiteerde van beleid dat Heemskerk als staatssecretaris voerde",
        0.90, 0.65)

    # Bart de Liefde: VVD-Kamerlid Mededinging → Uber
    add_relation(cur, bart_de_liefde, uber, 'draaideur', DRAAIDEUR,
        "VVD-Kamerlid, woordvoerder Mededinging, steunde Uber als Kamerlid op 19 juni 2014, "
        "werd binnen drie weken na vertrek public policy manager bij Uber",
        1.0, 0.75)

    add_relation(cur, bart_de_liefde, vvd, 'personeel', None,
        "VVD-Kamerlid, woordvoerder Mededinging", 1.0, 0.50)

    # Raymond Knops: defensiewoordvoerder → lobbyist defensie-industrie
    add_relation(cur, raymond_knops, min_defensie, 'draaideur', DRAAIDEUR,
        "CDA-Kamerlid en defensiewoordvoerder, staatssecretaris BZK, "
        "brak termijn af om lobbyist te worden in de defensie-industrie",
        0.95, 0.70)

    add_relation(cur, raymond_knops, cda, 'personeel', None,
        "CDA-Kamerlid, defensiewoordvoerder, staatssecretaris BZK", 1.0, 0.55)

    # Afke Schaart: KPN → VVD-Kamerlid ICT → Microsoft
    add_relation(cur, afke_schaart, microsoft, 'draaideur', DRAAIDEUR,
        "Directeur public affairs KPN, werd VVD-Kamerlid woordvoerder ICT/telecom (2010-2012), "
        "werd senior directeur EU International Relations bij Microsoft",
        1.0, 0.75)

    add_relation(cur, afke_schaart, vvd, 'personeel', None,
        "VVD-Kamerlid, woordvoerder ICT en telecommunicatie (2010-2012)", 1.0, 0.50)

    # Eeke van der Veen: zorgverzekeraar → PvdA-Kamerlid zorg → zorglobby
    add_relation(cur, eeke_vd_veen, pvda, 'draaideur', DRAAIDEUR,
        "Voorzitter RvB zorgverzekeraar Agis, werd PvdA-Kamerlid woordvoerder zorg (2006-2012), "
        "werd daarna voorzitter Zorgbelang Nederland",
        1.0, 0.70)

    # ============================================================
    # 3. POLITICUS → MEDIA
    # ============================================================
    # (Dit wordt al deels gedekt door draaideur_politiek_journalistiek mechanisme)

    db.commit()

    # Samenvatting
    cur.execute("SELECT COUNT(*) FROM relations WHERE relation_type = 'draaideur'")
    n_draaideur = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM entities")
    n_entities = cur.fetchone()[0]

    print(f"\n=== Voltooid ===")
    print(f"  Totaal draaideur-relaties: {n_draaideur}")
    print(f"  Totaal entiteiten: {n_entities}")

    db.close()


if __name__ == '__main__':
    main()
