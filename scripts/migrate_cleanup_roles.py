#!/usr/bin/env python3
"""
Migratie: verwijder functie-rollen en dubbelingen uit het theoretisch model.

Functie-rollen (wat een entiteit DOET, niet wat het IS) worden verwijderd:
- gatekeeper, flak_producent, flak_doelwit, ideoloog, online_intimidator,
  slapp_actor, officiele_bron, expert_bron, mediaverkoper, pr_machine

Dubbelingen worden samengevoegd:
- burger + publiek → publiek
- alternatief_medium + onafhankelijk_medium → alternatief_medium
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'propaganda_model.db')


def get_role_ids(cur):
    cur.execute("SELECT id, name FROM roles")
    return {name: rid for rid, name in cur.fetchall()}


def reassign_entity_primary_roles(cur, roles):
    """Wijs entiteiten met functie-rollen toe aan echte rollen."""
    print("\n1. Entity primary roles herwijzen...")

    reassignments = {
        # expert_bron → denktank, academisch_criticus, journalist, etc.
        'expert_bron': {
            'CPB (Centraal Planbureau)': 'denktank',
            'Clingendael Instituut': 'denktank',
            'HCSS (The Hague Centre for Strategic Studies)': 'denktank',
            'Nationale DenkTank': 'denktank',
            'Willem Schinkel': 'academisch_criticus',
            'Maarten van Rossem': 'columnist_opiniemaker',
            'Rob de Wijk': 'denktank',
            'Ron Fresen': 'journalist',
            'UvA Journalistiek': None,
        },
        # ideoloog → denktank, academisch_criticus, etc.
        'ideoloog': {
            'CDA': None,          # partij, geen passende rol
            'NSC (Nieuw Sociaal Contract)': None,
            'PvdA': None,
            'VVD': None,
            'Koningshuis': None,
            'NAVO': 'elite_forum',
            'Teldersstichting': 'denktank',
            'Wiardi Beckman Stichting': 'denktank',
        },
        # officiele_bron → NULL (overheidsinstelling heeft geen passende rol)
        'officiele_bron': {
            'Belastingdienst': None,
            'Ministerie van Buitenlandse Zaken': None,
            'Ministerie van Defensie': None,
            'OMT (Outbreak Management Team)': None,
            'Politie': None,
            'RIVM': None,
            'Tweede Kamer': None,
        },
        # flak_doelwit → vakbond_media, onderzoeksjournalist, etc.
        'flak_doelwit': {
            'Free Press Unlimited': 'vakbond_media',
            'NVJ (Nederlandse Vereniging van Journalisten)': 'vakbond_media',
            'Peter R. de Vries': 'onderzoeksjournalist',
            'SP': None,
        },
        # flak_producent
        'flak_producent': {
            'PVV': None,  # partij
        },
        # mediaverkoper → mediaorganisatie
        'mediaverkoper': {
            'Metro': 'mediaorganisatie',
            'NU.nl': 'mediaorganisatie',
        },
        # pr_machine → elite_forum of NULL
        'pr_machine': {
            'European Publishers Council': 'elite_forum',
            'McKinsey': None,
        },
    }

    for old_role, entity_map in reassignments.items():
        old_role_id = roles.get(old_role)
        if not old_role_id:
            continue
        for entity_name, new_role_name in entity_map.items():
            new_role_id = roles.get(new_role_name) if new_role_name else None
            cur.execute(
                "UPDATE entities SET primary_role_id = ? WHERE name = ? AND primary_role_id = ?",
                (new_role_id, entity_name, old_role_id)
            )
            if cur.rowcount:
                print(f"   {entity_name}: {old_role} → {new_role_name or 'NULL'}")

    # Vang overgebleven entiteiten op (niet in de mapping)
    function_roles = [
        'gatekeeper', 'flak_producent', 'flak_doelwit', 'ideoloog',
        'online_intimidator', 'slapp_actor', 'officiele_bron', 'expert_bron',
        'mediaverkoper', 'pr_machine'
    ]
    for role_name in function_roles:
        role_id = roles.get(role_name)
        if role_id:
            cur.execute(
                "SELECT name FROM entities WHERE primary_role_id = ?", (role_id,)
            )
            remaining = cur.fetchall()
            for (name,) in remaining:
                cur.execute(
                    "UPDATE entities SET primary_role_id = NULL WHERE name = ?", (name,)
                )
                print(f"   {name}: {role_name} → NULL (niet in mapping)")


def reassign_mechanism_roles(cur, roles):
    """Wijs mechanismen toe aan echte rollen i.p.v. functie-rollen."""
    print("\n2. Mechanism source/target herwijzen...")

    # (new_source_role, new_target_role) — None = NULL
    updates = {
        # gatekeeper → hoofdredacteur/columnist_opiniemaker
        'deplatforming': ('hoofdredacteur', 'journalist'),
        'etikettering': ('columnist_opiniemaker', 'journalist'),
        'morele_chantage': ('columnist_opiniemaker', 'journalist'),
        'onevenwichtig_debat': ('hoofdredacteur', 'journalist'),
        'overton_bewaking': ('hoofdredacteur', 'publiek'),
        'spectrum_bewaking': ('hoofdredacteur', 'publiek'),

        # ideoloog → denktank/elite_forum
        'draaideurconstructie': ('politicus', 'columnist_opiniemaker'),
        'hegemonische_naturalisatie': ('denktank', 'publiek'),
        'ideologische_synchronisatie': ('elite_forum', 'mediaeigenaar'),
        'denktank_legitimatie': ('denktank', 'columnist_opiniemaker'),

        # flak_producent → NULL of specifieke rol
        'chilling_effect_geweld': (None, 'mediaorganisatie'),
        'geweld_intimidatie': (None, 'journalist'),
        'juridische_dreiging': (None, 'journalist'),
        'publieke_aanval': ('politicus', 'journalist'),

        # flak_doelwit → journalist
        'zelfcensuur': ('mediaorganisatie', 'journalist'),
        'woo_obstructie': (None, 'journalist'),

        # officiele_bron → NULL of specifiek
        'bron_afhankelijkheid': (None, 'mediaorganisatie'),
        'haagse_stam': ('politicus', 'journalist'),
        'lobby_informatievoorziening': ('lobbyist', 'politicus'),
        'parlementaire_doorbraak': ('parlementair_controleur', None),

        # expert_bron → denktank
        'expert_framing': ('denktank', 'mediaorganisatie'),

        # mediaverkoper → mediaorganisatie
        'advertentiedruk': ('adverteerder', 'mediaorganisatie'),
        'commerciele_afhankelijkheid': ('adverteerder', 'mediaorganisatie'),
        'platform_advertentie_concentratie': ('techplatform', 'mediaorganisatie'),

        # pr_machine → NULL
        'pr_naar_journalist': (None, 'journalist'),
        'pr_subsidie': (None, 'mediaorganisatie'),

        # online_intimidator / slapp_actor → NULL
        'online_intimidatie_journalist': (None, 'journalist'),
        'slapp_tegen_journalist': (None, 'journalist'),
    }

    for mech_name, (src, tgt) in updates.items():
        src_id = roles.get(src) if src else None
        tgt_id = roles.get(tgt) if tgt else None
        cur.execute(
            "UPDATE mechanisms SET source_role_id = ?, target_role_id = ? WHERE name = ?",
            (src_id, tgt_id, mech_name)
        )
        if cur.rowcount:
            print(f"   {mech_name}: {src or 'NULL'} → {tgt or 'NULL'}")
        else:
            # Mechanisme bestaat niet in DB, skip
            pass


def cleanup_entity_roles(cur, roles):
    """Verwijder entity_roles entries voor functie-rollen."""
    print("\n3. Entity_roles opschonen...")

    function_roles = [
        'gatekeeper', 'flak_producent', 'flak_doelwit', 'ideoloog',
        'online_intimidator', 'slapp_actor', 'officiele_bron', 'expert_bron',
        'mediaverkoper', 'pr_machine'
    ]

    for role_name in function_roles:
        role_id = roles.get(role_name)
        if role_id:
            cur.execute("DELETE FROM entity_roles WHERE role_id = ?", (role_id,))
            if cur.rowcount:
                print(f"   {cur.rowcount} entity_roles verwijderd voor '{role_name}'")


def merge_duplicates(cur, roles):
    """Voeg dubbele rollen samen."""
    print("\n4. Dubbelingen samenvoegen...")

    merges = [
        ('burger', 'publiek'),
        ('onafhankelijk_medium', 'alternatief_medium'),
    ]

    for old_name, keep_name in merges:
        old_id = roles.get(old_name)
        keep_id = roles.get(keep_name)
        if not old_id or not keep_id:
            continue

        cur.execute("UPDATE entities SET primary_role_id = ? WHERE primary_role_id = ?",
                    (keep_id, old_id))
        # Voorkom duplicate key violations bij entity_roles
        cur.execute("""
            DELETE FROM entity_roles
            WHERE role_id = ?
            AND entity_id IN (SELECT entity_id FROM entity_roles WHERE role_id = ?)
        """, (old_id, keep_id))
        cur.execute("UPDATE entity_roles SET role_id = ? WHERE role_id = ?",
                    (keep_id, old_id))
        cur.execute("UPDATE mechanisms SET source_role_id = ? WHERE source_role_id = ?",
                    (keep_id, old_id))
        cur.execute("UPDATE mechanisms SET target_role_id = ? WHERE target_role_id = ?",
                    (keep_id, old_id))
        print(f"   '{old_name}' → '{keep_name}' samengevoegd")


def delete_roles(cur, roles):
    """Verwijder functie-rollen en samengevoegde dubbelingen."""
    print("\n5. Rollen verwijderen...")

    to_delete = [
        'gatekeeper', 'flak_producent', 'flak_doelwit', 'ideoloog',
        'online_intimidator', 'slapp_actor', 'officiele_bron', 'expert_bron',
        'mediaverkoper', 'pr_machine',
        'burger', 'onafhankelijk_medium',
    ]

    for role_name in to_delete:
        role_id = roles.get(role_name)
        if not role_id:
            continue

        # Check referenties
        cur.execute("SELECT COUNT(*) FROM entities WHERE primary_role_id = ?", (role_id,))
        e_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM entity_roles WHERE role_id = ?", (role_id,))
        er_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM mechanisms WHERE source_role_id = ? OR target_role_id = ?",
                    (role_id, role_id))
        m_count = cur.fetchone()[0]

        if e_count == 0 and er_count == 0 and m_count == 0:
            cur.execute("DELETE FROM roles WHERE id = ?", (role_id,))
            print(f"   '{role_name}' verwijderd")
        else:
            print(f"   ⚠ '{role_name}' heeft nog referenties: "
                  f"{e_count} entities, {er_count} entity_roles, {m_count} mechanisms")


def main():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")

    print("=== Migratie: functie-rollen opschonen ===")

    try:
        cur = db.cursor()
        roles = get_role_ids(cur)

        reassign_entity_primary_roles(cur, roles)
        reassign_mechanism_roles(cur, roles)
        cleanup_entity_roles(cur, roles)
        merge_duplicates(cur, roles)
        delete_roles(cur, roles)

        db.commit()

        # Samenvatting
        cur.execute("SELECT COUNT(*) FROM roles")
        n_roles = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM mechanisms")
        n_mechs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM entities WHERE primary_role_id IS NULL")
        n_null = cur.fetchone()[0]

        print(f"\n=== Voltooid ===")
        print(f"   Rollen: {n_roles}")
        print(f"   Mechanismen: {n_mechs}")
        print(f"   Entiteiten zonder primaire rol: {n_null}")

    except Exception as e:
        db.rollback()
        print(f"\nMigratie mislukt: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
