"""
Grondige uitbreiding van het theoretisch model.

Voegt ontbrekende rollen toe en bouwt een veel rijker web van mechanismen
op basis van het rapport. Herclassificeert 'overig' waar mogelijk.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # ──────────────────────────────────────────────────────────
    # STAP 1: Herclassificeer bestaande rollen uit 'overig'
    # ──────────────────────────────────────────────────────────
    reclassify = {
        'techplatform':            'systeemactor',
        'burger':                  'systeemactor',
    }
    for name, cat in reclassify.items():
        cur.execute("UPDATE roles SET category = ? WHERE name = ?", (cat, name))
        print(f"  Herclassificeerd: {name} → {cat}")

    # ──────────────────────────────────────────────────────────
    # STAP 2: Nieuwe rollen toevoegen
    # ──────────────────────────────────────────────────────────
    new_roles = [
        # Sourcing
        ('journalist', 'sourcing',
         'Individuele nieuwsproducent die opereert binnen alle filters. '
         'Afhankelijk van bronnen, onderhevig aan flak, gesocialiseerd in ideologie.',
         'Parlementair verslaggevers, buitenlandcorrespondenten, redacteuren'),
        ('voorlichter', 'sourcing',
         'Woordvoerder of communicatieadviseur die de informatievoorziening namens '
         'overheid of bedrijf beheert, filtert en stuurt.',
         'Rijksvoorlichtingsdienst, ministeriële woordvoerders, corporate comms'),
        ('denktank', 'sourcing',
         'Onderzoeksinstituut dat schijnbaar objectieve analyses en beleidsvoorstellen '
         'levert, vaak gefinancierd door elite-belangen.',
         'HCSS, Clingendael, Nationale DenkTank, wetenschappelijke bureaus partijen'),

        # Eigendom
        ('hoofdredacteur', 'eigendom',
         'Eindverantwoordelijke voor de redactionele lijn. Scharnierpunt tussen '
         'eigendomsbelangen en de dagelijkse journalistieke praktijk. Benoemd door eigenaar.',
         'Hoofdredacteuren landelijke kranten, directeuren nieuwsredacties'),

        # Flak
        ('online_intimidator', 'flak',
         'Actor die via gecoördineerde online haat, doxing en bedreigingen '
         'journalisten onder druk zet.',
         'Trollenlegers, gecoördineerde haatcampagnes, anonieme accounts'),
        ('slapp_actor', 'flak',
         'Partij die strategische rechtszaken inzet om kritische journalistiek '
         'financieel uit te putten en af te schrikken.',
         'Bedrijven met grote juridische afdelingen, vermogende personen'),

        # Ideologie
        ('columnist_opiniemaker', 'ideologie',
         'Publieke duider die via regelmatige columns en media-optredens het spectrum '
         'van toegestane mening mede definieert en de hegemonie reproduceert.',
         'Vaste columnisten bij kranten, talkshowgasten, TV-commentatoren'),

        # Systeemactor
        ('politicus', 'systeemactor',
         'Gekozen volksvertegenwoordiger of bestuurder die zowel bron als onderwerp '
         'van berichtgeving is, en flak kan produceren of ondergaan.',
         'Kamerleden, ministers, partijleiders, wethouders'),
        ('redactie', 'systeemactor',
         'Het collectief van journalisten binnen een mediaorganisatie. Sociologisch '
         'vaak homogeen, onderhevig aan groepsdenken en conformisme.',
         'Redacties van landelijke kranten, nieuwsredacties omroepen'),
        ('publiek', 'systeemactor',
         'Het nieuwsconsumerende publiek dat via kijkcijfers, clicks en abonnementen '
         'economische feedback geeft en door framing wordt beïnvloed.',
         'Lezers, kijkers, online nieuwsconsumenten, social media gebruikers'),
    ]

    role_ids = {}
    # First load existing role ids
    for row in cur.execute("SELECT id, name FROM roles").fetchall():
        role_ids[row[0]] = row[1]
        role_ids[row[1]] = row[0]

    for name, category, description, examples in new_roles:
        if name in role_ids:
            print(f"  Rol bestaat al: {name}")
            continue
        cur.execute(
            "INSERT INTO roles (name, category, description, examples) VALUES (?, ?, ?, ?)",
            (name, category, description, examples)
        )
        rid = cur.lastrowid
        role_ids[name] = rid
        role_ids[rid] = name
        print(f"  + Rol: {name} ({category}) → id={rid}")

    # Refresh role_ids
    for row in cur.execute("SELECT id, name FROM roles").fetchall():
        role_ids[row[0]] = row[1]
        role_ids[row[1]] = row[0]

    def role_id(name):
        return role_ids.get(name)

    # ──────────────────────────────────────────────────────────
    # STAP 3: Herclassificeer mechanismen uit 'overig'
    # ──────────────────────────────────────────────────────────
    mech_reclassify = {
        'algoritmische_filtering':            'cross_filter',
        'platform_advertentie_concentratie':   'cross_filter',
        'algoritmische_socialisatie':          'cross_filter',
    }
    for name, filt in mech_reclassify.items():
        cur.execute("UPDATE mechanisms SET filter = ? WHERE name = ?", (filt, name))
        print(f"  Mechanisme herclassificeerd: {name} → {filt}")

    # ──────────────────────────────────────────────────────────
    # STAP 4: Nieuwe mechanismen toevoegen
    # ──────────────────────────────────────────────────────────
    new_mechanisms = [
        # === EIGENDOM ===
        ('benoemingspolitiek', 'eigendom', 'procedureel',
         'Eigenaar benoemt hoofdredacteur en bepaalt daarmee indirect de redactionele koers.',
         'Redactionele lijn weerspiegelt voorkeuren eigenaar zonder expliciete instructies.',
         'mediaeigenaar', 'hoofdredacteur'),
        ('redactioneel_budgetcontrole', 'eigendom', 'economisch',
         'Eigenaar bepaalt het redactiebudget; bezuinigingen raken onderzoeksjournalistiek het hardst.',
         'Minder middelen voor diepgravend, kritisch werk; meer afhankelijkheid van goedkope bronnen.',
         'mediaeigenaar', 'redactie'),
        ('hoofdredacteur_als_filter', 'eigendom', 'procedureel',
         'Hoofdredacteur vertaalt eigendomsbelangen naar dagelijkse redactionele keuzes.',
         'Selectie van onderwerpen en invalshoeken weerspiegelt impliciete eigenaarswensen.',
         'hoofdredacteur', 'journalist'),

        # === ADVERTENTIE ===
        ('commerciele_content_druk', 'advertentie', 'economisch',
         'Adverteerders eisen een gunstig redactioneel klimaat als voorwaarde voor advertentie-inkoop.',
         'Native advertising, branded content en gesponsorde rubrieken vervagen de grens journalistiek/reclame.',
         'adverteerder', 'hoofdredacteur'),

        # === SOURCING ===
        ('voorlichter_informatiefilter', 'sourcing', 'procedureel',
         'Voorlichter filtert en selecteert welke informatie journalisten bereiken via persberichten en briefings.',
         'Journalisten krijgen een voorgeselecteerd, gekleurd beeld van overheidsbeslissingen.',
         'voorlichter', 'journalist'),
        ('politicus_als_bron', 'sourcing', 'structureel',
         'Politici zijn primaire bronnen voor parlementaire verslaggeving; journalisten zijn afhankelijk van hun goodwill.',
         'Berichtgeving volgt de politieke agenda; kritische vragen worden vermeden om toegang te behouden.',
         'politicus', 'journalist'),
        ('lobbyist_naar_politicus', 'sourcing', 'procedureel',
         'Lobbyisten leveren kant-en-klare informatie, amendementen en Kamervragen aan politici.',
         'Parlementaire besluitvorming wordt mede gestuurd door niet-gekozen belangenbehartigers.',
         'lobbyist', 'politicus'),
        ('lobbyist_naar_journalist', 'sourcing', 'procedureel',
         'Lobbyisten benaderen journalisten direct met achtergrondinformatie, exclusieve data en experts.',
         'Journalisten nemen frames van lobbyisten over zonder de belangen erachter te expliciteren.',
         'lobbyist', 'journalist'),
        ('denktank_financiering_bias', 'sourcing', 'economisch',
         'Denktanks worden gefinancierd door overheid en bedrijfsleven; hun onderzoeksagenda weerspiegelt die belangen.',
         'Schijnbaar onafhankelijke analyses dienen de belangen van financiers.',
         'adverteerder', 'denktank'),
        ('denktank_naar_media', 'sourcing', 'discursief',
         'Denktank-experts worden opgevoerd als onafhankelijke commentatoren in nieuwsmedia.',
         'Beleidsstandpunten van financiers krijgen het aureool van wetenschappelijke objectiviteit.',
         'denktank', 'journalist'),
        ('denktank_naar_politiek', 'sourcing', 'discursief',
         'Denktanks leveren beleidsrapporten en aanbevelingen direct aan politici en ministeries.',
         'Politieke besluitvorming wordt gestuurd door analyses die corporate belangen dienen.',
         'denktank', 'politicus'),
        ('persbureau_naar_redactie', 'sourcing', 'procedureel',
         'Persbureau levert kant-en-klare berichten die door gekrompen redacties worden overgenomen.',
         'Keuzes van één persbureau (ANP) bepalen het landelijke nieuwsbeeld.',
         'persbureau', 'redactie'),
        ('journalist_bronrelatie', 'sourcing', 'psychologisch',
         'Journalist bouwt persoonlijke relatie op met bron en wordt daardoor terughoudend met kritiek.',
         'Zelfcensuur om de bronrelatie te beschermen; kritische vragen worden niet gesteld.',
         'journalist', 'voorlichter'),
        ('pr_naar_journalist', 'sourcing', 'procedureel',
         'PR-professionals leveren persberichten, interviews en mediatrainingen om het beeld te sturen.',
         'Bedrijfsbelangen worden verpakt als nieuwswaardige verhalen.',
         'pr_machine', 'journalist'),

        # === FLAK ===
        ('politieke_flak', 'flak', 'discursief',
         'Politici produceren flak door media publiekelijk aan te vallen of te dreigen met beleidsmaatregelen.',
         'Redacties worden voorzichtiger; zelfcensuur om politieke aanvallen te vermijden.',
         'politicus', 'redactie'),
        ('slapp_tegen_journalist', 'flak', 'juridisch',
         'Strategische rechtszaken (SLAPPs) door machtige partijen om individuele journalisten uit te putten.',
         'Afschrikwekkend effect op de hele redactie; onderwerpen worden vermeden.',
         'slapp_actor', 'journalist'),
        ('online_intimidatie_journalist', 'flak', 'technologisch',
         'Gecoördineerde online haat, doxing en bedreigingen gericht op individuele journalisten.',
         '61% van journalisten heeft intimidatie ervaren; disproportioneel gericht op vrouwen en minderheden.',
         'online_intimidator', 'journalist'),
        ('elite_forum_flak', 'flak', 'discursief',
         'Elite-netwerken produceren indirect flak door de grenzen van het acceptabele debat af te bakenen.',
         'Kritiek op de elite zelf wordt geframed als illegitiem of als complottheorie.',
         'elite_forum', 'journalist'),

        # === FLAK (intern) ===
        ('redactioneel_conformisme', 'flak', 'psychologisch',
         'Redactie oefent groepsdruk uit: afwijkende invalshoeken worden ontmoedigd door collega\'s en chefs.',
         'Journalisten internaliseren de redactiecultuur en passen zelfcensuur toe.',
         'redactie', 'journalist'),
        ('sociologische_homogeniteit', 'flak', 'structureel',
         'Redacties zijn sociologisch homogeen (HBO/WO, middenklasse, Randstad), wat blinde vlekken creëert.',
         'Leefwereld van grote delen van de samenleving blijft structureel onderbelicht.',
         'redactie', 'publiek'),

        # === IDEOLOGIE ===
        ('columnist_als_hegemon', 'ideologie', 'discursief',
         'Columnisten en opiniemakers reproduceren het dominante denkkader als vanzelfsprekend in hun stukken.',
         'Pro-markt, pro-Atlantisch frame wordt dagelijks herhaald en genormaliseerd.',
         'columnist_opiniemaker', 'publiek'),
        ('elite_forum_ideologie', 'ideologie', 'structureel',
         'Elite-netwerken (Bilderberg, WEF, ERT) synchroniseren het wereldbeeld van de transnationale klasse.',
         'Gedeelde ideologische consensus die doorsijpelt naar media, politiek en beleid.',
         'elite_forum', 'mediaeigenaar'),
        ('politicus_als_ideoloog', 'ideologie', 'discursief',
         'Politici presenteren neoliberale beleidsopties als de enige realistische keuzes.',
         'TINA-frame (There Is No Alternative) beperkt het politieke debat.',
         'politicus', 'publiek'),
        ('journalist_socialisatie', 'ideologie', 'psychologisch',
         'Journalisten worden via opleiding en carrière gesocialiseerd in het dominante denkkader.',
         'Journalist ervaart het dominante frame als professioneel gezond verstand, niet als ideologie.',
         'redactie', 'journalist'),

        # === CROSS-FILTER ===
        ('platform_nieuwsselectie', 'cross_filter', 'technologisch',
         'Platformalgoritmes bepalen welk nieuws gebruikers zien op basis van engagement, niet journalistieke waarden.',
         'Emotionele, polariserende content wordt bevoordeeld; nuance en context verdwijnen.',
         'techplatform', 'publiek'),
        ('platform_verdienmodel_druk', 'cross_filter', 'economisch',
         'Media moeten hun content aanpassen aan platformlogica om hun publiek te bereiken.',
         'Clickbait, korte formats en sensatie worden beloond; diepgang wordt gestraft.',
         'techplatform', 'redactie'),
        ('draaideur_journalistiek_politiek', 'cross_filter', 'structureel',
         'Journalisten stappen over naar politiek/PR en vice versa, waardoor netwerken verstrengelen.',
         'Gedeeld referentiekader ondermijnt kritische distantie tussen journalistiek en macht.',
         'journalist', 'politicus'),
        ('draaideur_politiek_journalistiek', 'cross_filter', 'structureel',
         'Ex-politici worden columnist of commentator; ex-journalisten worden voorlichter of adviseur.',
         'Dezelfde personen circuleren tussen rollen, wat de grenzen tussen macht en controle vervaagt.',
         'politicus', 'columnist_opiniemaker'),
        ('mediaeigenaar_elite_netwerk', 'cross_filter', 'structureel',
         'Media-eigenaren ontmoeten politici en CEO\'s in besloten elite-fora (Bilderberg, WEF).',
         'Gedeelde belangen en wereldbeelden worden gesynchroniseerd buiten het publieke oog.',
         'mediaeigenaar', 'elite_forum'),
        ('economische_feedback_loop', 'cross_filter', 'economisch',
         'Dalend vertrouwen → minder abonnees → meer bezuinigingen → slechtere journalistiek → nog minder vertrouwen.',
         'Zelfversterkende negatieve spiraal die alle filters versterkt.',
         'publiek', 'mediaorganisatie'),
    ]

    existing_mechs = set(
        row[0] for row in cur.execute("SELECT name FROM mechanisms").fetchall()
    )

    added = 0
    for name, filt, mtype, desc, effect, src_role, tgt_role in new_mechanisms:
        if name in existing_mechs:
            print(f"  Mechanisme bestaat al: {name}")
            continue
        src_id = role_id(src_role)
        tgt_id = role_id(tgt_role)
        if not src_id or not tgt_id:
            print(f"  WAARSCHUWING: Rol niet gevonden voor {name}: {src_role}={src_id}, {tgt_role}={tgt_id}")
            continue
        cur.execute(
            "INSERT INTO mechanisms (name, filter, mechanism_type, description, effect, "
            "source_role_id, target_role_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, filt, mtype, desc, effect, src_id, tgt_id)
        )
        added += 1
        print(f"  + Mechanisme: {name} ({filt}/{mtype}): {src_role} → {tgt_role}")

    conn.commit()

    # ──────────────────────────────────────────────────────────
    # VERIFICATIE
    # ──────────────────────────────────────────────────────────
    print(f"\n=== Resultaat ===")
    for table in ['roles', 'mechanisms']:
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} records")

    print("\nRollen per categorie:")
    for row in cur.execute(
        "SELECT category, COUNT(*) FROM roles GROUP BY category ORDER BY category"
    ).fetchall():
        print(f"  {row[0]}: {row[1]}")

    print("\nMechanismen per filter:")
    for row in cur.execute(
        "SELECT filter, COUNT(*) FROM mechanisms GROUP BY filter ORDER BY filter"
    ).fetchall():
        print(f"  {row[0]}: {row[1]}")

    print("\nMechanismen per type:")
    for row in cur.execute(
        "SELECT mechanism_type, COUNT(*) FROM mechanisms GROUP BY mechanism_type ORDER BY mechanism_type"
    ).fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Controleer connectiviteit
    print("\nRollen zonder mechanismen:")
    orphans = cur.execute("""
        SELECT r.name, r.category FROM roles r
        WHERE r.id NOT IN (
            SELECT source_role_id FROM mechanisms WHERE source_role_id IS NOT NULL
            UNION
            SELECT target_role_id FROM mechanisms WHERE target_role_id IS NOT NULL
        )
    """).fetchall()
    for name, cat in orphans:
        print(f"  WAARSCHUWING: {name} ({cat}) heeft geen mechanismen!")

    conn.close()
    print(f"\n{added} mechanismen toegevoegd.")


if __name__ == "__main__":
    run()
