"""Seed het theoretische propagandamodel voor NL context.

Gebaseerd op Manufacturing Consent, aangevuld met:
- Culturele hegemonie
- Systeemtheorie / emergence
- Techplatform-filtering als modern fenomeen
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

ROLES = [
    # (name, category, description, examples)

    # Filter 1: Eigendom
    ("mediaeigenaar", "eigendom",
     "Partij die eigendom heeft over mediaorganisaties en daarmee redactionele lijn kan beinvloeden",
     "DPG Media (Van Thillo), Mediahuis (Leysen), holdings, families met mediaportfolio"),
    ("mediaorganisatie_rol", "eigendom",
     "Producent van nieuws/content, onderhevig aan eigendomsstructuur",
     "Kranten, omroepen, nieuwssites"),
    ("aandeelhouder", "eigendom",
     "Financieel belang in mediabedrijf zonder direct eigendom",
     "Investeerders, pensioenfondsen"),
    ("institutioneel_belegger", "eigendom",
     "Passieve, systemische eigenaar via vermogensbeheer. Bezit aandelen namens anderen en oefent stemrecht uit, met inherent belang bij stabiel kapitalistisch systeem",
     "BlackRock, Vanguard — de facto eigenaren van vrijwel alle beursgenoteerde bedrijven"),

    # Filter 2: Advertentie
    ("adverteerder", "advertentie",
     "Partij die via advertentie-inkomsten invloed heeft op media-inhoud",
     "Grote retailers (Albert Heijn, Lidl), FMCG (P&G, Unilever), loterijen, gokbedrijven"),
    ("mediaverkoper", "advertentie",
     "Mediapartij die afhankelijk is van advertentie-inkomsten",
     "Commerciele omroepen, gratis nieuwsplatforms (NU.nl), nieuwssites"),

    # Filter 3: Sourcing
    ("officiele_bron", "sourcing",
     "Institutionele bron die door media als betrouwbaar wordt behandeld en daardoor framing bepaalt",
     "Overheid, politie, RIVM, Belastingdienst, grote bedrijven met PR-afdeling"),
    ("persbureau", "sourcing",
     "Centraal nieuwsleverancier dat de hele nieuwsstroom voedt en daardoor homogeniseert. Distinct van individuele bronnen door wholesale-karakter",
     "ANP — levert dagelijks honderden berichten aan vrijwel alle NL media"),
    ("expert_bron", "sourcing",
     "Expert/denktank die door media geciteerd wordt en daardoor het debat kadert",
     "Universiteiten, CPB, Clingendael, HCSS, planbureaus"),
    ("pr_machine", "sourcing",
     "Professionele communicatie-afdeling die het narratief voedt",
     "Voorlichters, PR-bureaus, spin doctors, McKinsey"),

    # Filter 4: Flak
    ("flak_producent", "flak",
     "Partij die druk uitoefent op media/journalisten die afwijken van gewenst narratief",
     "Lobbygroepen, politici die media aanvallen (PVV), juridische dreiging (SLAPPs)"),
    ("flak_doelwit", "flak",
     "Journalist of medium dat gecorrigeerd/gedisciplineerd wordt",
     "Kritische journalisten (Peter R. de Vries), alternatieve media, afwijkende experts"),

    # Filter 5: Ideologie
    ("ideoloog", "ideologie",
     "Partij die het dominante ideologische kader verspreidt en normaliseert",
     "Denktanks, opiniemakers, politieke leiders"),
    ("gatekeeper", "ideologie",
     "Partij die bepaalt welke standpunten binnen het Overton window vallen",
     "Hoofdredacteuren, talkshow-presentatoren, factcheckers"),
    ("elite_forum", "ideologie",
     "Besloten coordinatieplatform waar transnationale elite consensus smeedt en wereldbeelden synchroniseert, buiten democratisch proces om",
     "Bilderberg Groep, Trilaterale Commissie, World Economic Forum (Davos), European Round Table of Industrialists"),

    # Overig
    ("burger", "overig",
     "Eindconsument van mediaproducten, doelwit van propaganda",
     "Kiezers, publieke opinie"),
    ("klokkenluider", "overig",
     "Partij die informatie lekt of het systeem blootlegt",
     "Whistleblowers, onderzoeksjournalisten"),
    ("techplatform", "overig",
     "Digitaal platform dat als nieuwe poortwachter fungeert met algoritmische filtering. Verdienmodel gebaseerd op engagement, niet journalistieke waarden",
     "Google, Meta (Facebook/Instagram), TikTok — primaire nieuwsbron voor jongeren"),
    ("toezichthouder", "overig",
     "Instantie die media-onafhankelijkheid en mededinging bewaakt, maar vaak tandeloos of te laat",
     "ACM, Commissariaat voor de Media, WRR, Raad voor de Journalistiek"),
]

MECHANISMS = [
    # (name, filter, description, effect, source_role, target_role)

    # Filter 1: Eigendom
    ("eigendomsconcentratie", "eigendom",
     "Kleine groep eigenaren bezit het merendeel van de media. In NL: duopolie DPG/Mediahuis met >90% online markt",
     "Beperkte diversiteit in redactionele lijnen, gedeelde belangen van transnationale elite",
     "mediaeigenaar", "mediaorganisatie_rol"),
    ("winstmaximalisatie", "eigendom",
     "Eigenaar stuurt op winst boven journalistieke kwaliteit",
     "Bezuinigingen op onderzoeksjournalistiek, clickbait, minder diepgang, gekrompen redacties",
     "mediaeigenaar", "mediaorganisatie_rol"),

    # Filter 2: Advertentie
    ("advertentiedruk", "advertentie",
     "Adverteerders trekken budget terug bij onwelgevallige berichtgeving",
     "Zelfcensuur, vermijden van kritiek op grote adverteerders",
     "adverteerder", "mediaverkoper"),
    ("commerciele_afhankelijkheid", "advertentie",
     "Medium is financieel afhankelijk van advertentie-inkomsten",
     "Redactionele keuzes worden beinvloed door commerciele belangen",
     "adverteerder", "mediaverkoper"),
    ("supportive_selling_environment", "advertentie",
     "Media creeren een redactionele omgeving die bevorderlijk is voor de commerciele boodschap: optimistisch, apolitiek, lifestyle- en consumptiegericht",
     "Structurele voorkeur voor content die het consumentistische wereldbeeld bevestigt. Systeemkritiek past niet in dit model",
     "adverteerder", "mediaorganisatie_rol"),

    # Filter 3: Sourcing
    ("bron_afhankelijkheid", "sourcing",
     "Media zijn afhankelijk van officiele bronnen voor snelle berichtgeving. In Den Haag functioneren politici, voorlichters en journalisten als 'een stam' (Luyendijk)",
     "Overheidsperspectief wordt standaard overgenomen, kritische vragen achterwege, symbiotische cultuur",
     "officiele_bron", "mediaorganisatie_rol"),
    ("pakketjournalistiek", "sourcing",
     "Media nemen op grote schaal kant-en-klare berichten van het centrale persbureau (ANP) over wegens tijds- en kostendruk op gekrompen redacties",
     "Homogenisering van de nieuwsstroom: keuzes van een persbureau bepalen het nieuwsbeeld van het hele land",
     "persbureau", "mediaorganisatie_rol"),
    ("expert_framing", "sourcing",
     "Selectie van experts die het gewenste narratief bevestigen. NAVO-gezinde denktanks (HCSS, Clingendael) worden als 'neutraal' opgevoerd",
     "Schijn van objectiviteit terwijl het debat wordt begrensd. Denktanks produceren 'argumenten op bestelling' voor sponsors",
     "expert_bron", "mediaorganisatie_rol"),
    ("pr_subsidie", "sourcing",
     "PR-materiaal wordt als nieuws overgenomen wegens tijds/kostendruk",
     "Corporate/overheidsnarratief wordt onkritisch verspreid",
     "pr_machine", "mediaorganisatie_rol"),

    # Filter 4: Flak
    ("juridische_dreiging", "flak",
     "Dreigen met rechtszaken (SLAPPs) tegen kritische journalisten. Doel is zelden winnen maar financieel en psychologisch uitputten",
     "Chilling effect: journalisten vermijden risicovolle onderwerpen",
     "flak_producent", "flak_doelwit"),
    ("publieke_aanval", "flak",
     "Georganiseerde campagne om journalist/medium in diskrediet te brengen. In NL o.a. PVV die publieke omroep wil afschaffen",
     "Reputatieschade, zelfcensuur, ontslag. Ondermijnt vertrouwen in media",
     "flak_producent", "flak_doelwit"),
    ("deplatforming", "flak",
     "Uitsluiten van stemmen uit mainstream media. Afwijkende experts worden niet meer uitgenodigd (bv. Van Rossem na Irak-kritiek)",
     "Kritische stemmen bereiken minder publiek, worden van duider tot 'querulant'",
     "gatekeeper", "flak_doelwit"),
    ("etikettering", "flak",
     "Diskwalificeren van kritiek door de boodschapper te labelen i.p.v. inhoudelijk te weerleggen: 'wappie', 'complotdenker', 'Poetin-versteher'",
     "Legitieme vragen over proportionaliteit en grondrechten worden besmet door associatie met extremen (reductio ad absurdum)",
     "gatekeeper", "flak_doelwit"),
    ("zelfcensuur", "flak",
     "Intern conformisme en groepsdenken op sociologisch homogene redacties. Journalisten leren ongeschreven regels en passen zich aan uit angst voor professionele en sociale repercussies",
     "Controversiele onderwerpen worden vermeden. Neurowetenschappelijk: afwijkende mening wordt verwerkt als 'foutsignaal'. 61% NL journalisten ervaart intimidatie",
     "mediaorganisatie_rol", "flak_doelwit"),
    ("geweld_intimidatie", "flak",
     "Fysiek en online geweld tegen journalisten: bedreigingen, doxing, en in het extreme geval moord (Peter R. de Vries, 2021)",
     "Directe bedreiging van journalistieke veiligheid. Chilling effect op hele beroepsgroep",
     "flak_producent", "flak_doelwit"),

    # Filter 5: Ideologie
    ("overton_bewaking", "ideologie",
     "Bepalen welke standpunten 'redelijk' zijn en welke 'extreem'. Debat wordt toegestaan binnen strikt gedefinieerde grenzen, fundamentele premissen blijven buiten schot",
     "Systeemkritiek wordt gemarginaliseerd als complotdenken of populisme. Levendig debat over details maskeert smalle consensus",
     "gatekeeper", "burger"),
    ("false_balance", "ideologie",
     "Schijn van debat terwijl fundamentele aannames niet ter discussie staan. Bv. onevenwichtige talkshowtafels waar criticus alleen staat tegenover consensusfront",
     "Illusie van pluralisme binnen smal ideologisch spectrum. Criticus lijkt onredelijk door isolatie",
     "mediaorganisatie_rol", "burger"),
    ("draaideurconstructie", "ideologie",
     "Personeel wisselt tussen media, politiek en bedrijfsleven. Journalisten worden woordvoerder, politici worden columnist",
     "Gedeelde belangen en wereldbeeld, old boys network, verlies van kritische distantie",
     "ideoloog", "gatekeeper"),
    ("ideologische_synchronisatie", "ideologie",
     "Elite-fora (Bilderberg, WEF, Davos) synchroniseren het wereldbeeld van de transnationale elite: media-eigenaren, CEO's, politici en academici komen besloten samen onder Chatham House Rule",
     "Consensus rond vrijemarktkapitalisme wordt gesmeed buiten democratisch proces. Gedeeld referentiekader van besluitvormers",
     "elite_forum", "ideoloog"),
    ("hegemonische_naturalisatie", "ideologie",
     "Culturele hegemonie: het wereldbeeld van de heersende klasse wordt via media, onderwijs en civil society gepresenteerd als 'gezond verstand' en 'de natuurlijke orde'. De ideologie is het effectiefst wanneer ze onzichtbaar is",
     "Pro-markt, pro-elite, pro-Atlantische premissen worden niet als politieke keuze gezien maar als onvermijdelijke realiteit. Alternatieven zijn 'onrealistisch'",
     "ideoloog", "burger"),

    # Overig / Nieuw: Techplatforms
    ("algoritmische_filtering", "overig",
     "Techplatforms (Google, Meta, TikTok) selecteren nieuws op basis van engagement-maximalisatie. Algoritmes geven voorkeur aan emotionele content (woede, verontwaardiging)",
     "Fragmentatie en polarisatie. Traditionele media passen content aan platform-logica aan. Jongeren worden gesocialiseerd in algoritmisch i.p.v. journalistiek ecosysteem",
     "techplatform", "mediaorganisatie_rol"),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Insert roles
    for name, category, description, examples in ROLES:
        cur.execute(
            "INSERT OR IGNORE INTO roles (name, category, description, examples) VALUES (?, ?, ?, ?)",
            (name, category, description, examples)
        )

    conn.commit()

    # Build role name->id lookup
    cur.execute("SELECT id, name FROM roles")
    role_map = {name: rid for rid, name in cur.fetchall()}

    # Insert mechanisms
    for name, filt, desc, effect, src_role, tgt_role in MECHANISMS:
        cur.execute(
            """INSERT OR IGNORE INTO mechanisms
               (name, filter, description, effect, source_role_id, target_role_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, filt, desc, effect, role_map[src_role], role_map[tgt_role])
        )

    conn.commit()
    conn.close()
    print(f"Theoretisch model geladen: {len(ROLES)} rollen, {len(MECHANISMS)} mechanismen")


if __name__ == "__main__":
    seed()
