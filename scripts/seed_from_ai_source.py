"""
Extract entiteiten en relaties uit sources/AI/propagandsmodel2.md
en laad ze in de propaganda_model database met zekerheids- en invloedsscores.

Bron: "De Onzichtbare Architecten: Een Analyse van het Propagandamodel
       in het Nederlandse Medialandschap"
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
SOURCE_PATH = "sources/AI/propagandsmodel2.md"
SOURCE_TITLE = "De Onzichtbare Architecten: Een Analyse van het Propagandamodel in het Nederlandse Medialandschap"


# =============================================================================
# ENTITEITEN
# =============================================================================
# (name, type, primary_role (name), description, metadata_json)

ENTITIES = [
    # --- MEDIACONGLOMERATEN (eigendom) ---
    ("DPG Media", "mediaorganisatie", "mediaeigenaar",
     "Grootste mediabedrijf van Nederland (Belgisch). Bezit AD, Volkskrant, Trouw, Het Parool, NU.nl, RTL Nederland. >90% marktaandeel online commercieel nieuws samen met Mediahuis.",
     '{"land": "BE/NL", "voorheen": "De Persgroep", "marktaandeel_online": ">90% (samen met Mediahuis)"}'),

    ("Mediahuis", "mediaorganisatie", "mediaeigenaar",
     "Belgisch mediaconglomeraat. Bezit De Telegraaf, NRC, diverse regionale kranten. Tweede pijler van het Nederlandse mediaduopolie.",
     '{"land": "BE/NL", "oorsprong": "fusie Vlaamse mediabedrijven"}'),

    # --- INDIVIDUELE MEDIA ---
    ("AD (Algemeen Dagblad)", "mediaorganisatie", "mediaorganisatie",
     "Landelijke krant, eigendom van DPG Media.", None),
    ("de Volkskrant", "mediaorganisatie", "mediaorganisatie",
     "Landelijke kwaliteitskrant, eigendom van DPG Media. Historisch als links beschouwd.", None),
    ("Trouw", "mediaorganisatie", "mediaorganisatie",
     "Landelijke kwaliteitskrant, eigendom van DPG Media.", None),
    ("Het Parool", "mediaorganisatie", "mediaorganisatie",
     "Amsterdamse krant, eigendom van DPG Media.", None),
    ("NU.nl", "platform", "mediaverkoper",
     "Grootste gratis nieuwsplatform van Nederland, eigendom van DPG Media. Sterk afhankelijk van advertentie-inkomsten.",
     '{"type": "online", "gratis": true}'),
    ("RTL Nederland", "mediaorganisatie", "mediaorganisatie",
     "Commerciële omroep, overgenomen door DPG Media. ACM stelde strenge voorwaarden aan overname.",
     '{"acm_voorwaarden": "onafhankelijke stichtingen, vetorecht hoofdredacteur, handvest"}'),
    ("De Telegraaf", "mediaorganisatie", "mediaorganisatie",
     "Grootste krant van Nederland, eigendom van Mediahuis.", None),
    ("NRC", "mediaorganisatie", "mediaorganisatie",
     "Landelijke kwaliteitskrant, eigendom van Mediahuis.", None),
    ("NOS", "mediaorganisatie", "mediaorganisatie",
     "Publieke omroep, belangrijkste nieuwsbron Nederland. PVV wil deze afschaffen.",
     '{"type": "publiek", "financiering": "overheid"}'),
    ("ANP", "mediaorganisatie", "persbureau",
     "Algemeen Nederlands Persbureau. Zenuwcentrum van Nederlandse nieuwsstroom. Levert dagelijks honderden berichten aan vrijwel alle media. Leidt tot homogenisering ('pakketjournalistiek').",
     '{"eigenaar": "Chris Oomen (sinds 2021)", "voorheen": "Talpa/John de Mol"}'),
    ("De Correspondent", "mediaorganisatie", "mediaorganisatie",
     "Onafhankelijk platform voor diepgravende journalistiek, buiten de grote conglomeraten.",
     '{"type": "onafhankelijk", "model": "ledenfinanciering"}'),

    # --- EIGENAREN / PERSONEN ---
    ("Christian Van Thillo", "persoon", "mediaeigenaar",
     "Executive Chairman DPG Media. Centrale figuur achter het grootste Nederlandse mediaconglomeraat. Bestuurder bij Groupe Bruxelles Lambert. Lid European Publishers Council.",
     '{"vermogen": "~1.8 miljard EUR", "nationaliteit": "BE", "gbl_bestuurder_sinds": 2023}'),
    ("Thomas Leysen", "persoon", "mediaeigenaar",
     "Voorzitter Mediahuis. Lid stuurgroep Bilderberg, Trilaterale Commissie, European Round Table of Industrialists. Voorzitter dsm-firmenich, voormalig voorzitter KBC Groep en Umicore.",
     '{"nationaliteit": "BE", "bilderberg": "stuurgroep"}'),
    ("Familie Baert", "persoon", "mediaeigenaar",
     "Aandeelhouder Mediahuis via Concentra. Belgische industriële familie.", None),
    ("Familie Van Puijenbroek", "persoon", "mediaeigenaar",
     "Aandeelhouder Mediahuis via VP Exploitatie. Nederlandse industriële familie.", None),
    ("Chris Oomen", "persoon", "mediaeigenaar",
     "Maatschappelijk investeerder, eigenaar ANP sinds 2021. Stelt persbureau niet voor winst te hebben gekocht.", None),
    ("John de Mol", "persoon", "mediaeigenaar",
     "Mediamagnaat, voormalig eigenaar ANP via Talpa Network.",
     '{"bedrijf": "Talpa Network"}'),

    # --- ELITE NETWERKEN / LOBBYGROEPEN ---
    ("Bilderberg Groep", "lobbygroep", "elite_forum",
     "Zeer invloedrijke, besloten jaarlijkse conferentie. Onder Chatham House Rule. Samenkomst van economische, politieke en intellectuele elite. Platform voor netwerkvorming en ideologische synchronisatie.",
     '{"frequentie": "jaarlijks", "regel": "Chatham House Rule"}'),
    ("Trilaterale Commissie", "lobbygroep", "elite_forum",
     "Invloedrijk internationaal netwerk van de transnationale kapitaalklasse.",
     '{"leden": "Thomas Leysen"}'),
    ("European Round Table of Industrialists", "lobbygroep", "elite_forum",
     "Lobbyplatform van Europese industriële top-CEO's.",
     '{"leden": "Thomas Leysen"}'),
    ("World Economic Forum", "lobbygroep", "elite_forum",
     "Internationaal platform in Davos. Propageert 'stakeholder capitalism' en 'Great Reset'. Doel: consensus rond vrijemarktkapitalisme versterken. Kritiek hierop wordt vaak als complottheorie geframed.",
     '{"locatie": "Davos", "initiatieven": ["Great Reset", "Fourth Industrial Revolution", "Stakeholder Capitalism"]}'),
    ("European Publishers Council", "lobbygroep", "pr_machine",
     "Europese uitgeverslobby. Christian Van Thillo is voorzitter.", None),

    # --- BEDRIJVEN / HOLDINGS ---
    ("Groupe Bruxelles Lambert", "bedrijf", "aandeelhouder",
     "Machtige Belgische holding met belangen in multinationals (Adidas, Imerys). Christian Van Thillo is bestuurder sinds 2023.",
     '{"belangen": ["Adidas", "Imerys"]}'),
    ("Epifin", "bedrijf", "aandeelhouder",
     "Investeringsvehikel van familie Van Thillo, controleert DPG Media.", None),
    ("VP Exploitatie", "bedrijf", "aandeelhouder",
     "Investeringsvehikel van familie Van Puijenbroek in Mediahuis.", None),
    ("Concentra", "bedrijf", "aandeelhouder",
     "Holding van familie Baert, aandeelhouder Mediahuis.", None),
    ("BlackRock", "bedrijf", "institutioneel_belegger",
     "Grootste vermogensbeheerder ter wereld. ~119 miljard EUR belegd in NL. Beheert pensioengeld miljoenen Nederlanders. De facto eigenaar via stemrecht.",
     '{"belegd_nl": "~119 miljard EUR"}'),
    ("Vanguard", "bedrijf", "institutioneel_belegger",
     "Grote vermogensbeheerder, samen met BlackRock dominant in aandeelhouderschap wereldwijd.", None),
    ("Talpa Network", "bedrijf", "mediaeigenaar",
     "Mediabedrijf van John de Mol. Voormalig eigenaar ANP.", None),

    # --- GROTE ADVERTEERDERS ---
    ("Albert Heijn", "bedrijf", "adverteerder",
     "Grootste supermarktketen NL, top-adverteerder.", None),
    ("Lidl", "bedrijf", "adverteerder",
     "Grote supermarktketen, top-adverteerder NL.", None),
    ("Bol.com", "bedrijf", "adverteerder",
     "Grootste webwinkel NL, top-adverteerder.", None),
    ("Procter & Gamble", "bedrijf", "adverteerder",
     "Multinational FMCG, top-adverteerder NL.", None),
    ("Unilever", "bedrijf", "adverteerder",
     "Multinational FMCG, top-adverteerder NL. Nauwe banden met NL economie.",
     '{"hoofdkantoor": "NL/UK"}'),
    ("A.S. Watson (Kruidvat)", "bedrijf", "adverteerder",
     "Retailconcern (Kruidvat, Trekpleister), top-adverteerder NL.", None),
    ("Nederlandse Loterij", "bedrijf", "adverteerder",
     "Staatsloterij en meer, grote adverteerder.", None),
    ("Postcode Loterij", "bedrijf", "adverteerder",
     "Grote loterij en adverteerder NL.", None),

    # --- TECHPLATFORMS ---
    ("Google", "platform", "techplatform",
     "Dominante zoekmachine en advertentieplatform. Nieuwe poortwachter met algoritmische filtermechanismen. Verdienmodel gebaseerd op engagement, niet journalistieke waarden.", None),
    ("Meta (Facebook/Instagram)", "platform", "techplatform",
     "Dominant socialmediaplatform. Algoritmische selectie bevordert emotionele content. Faciliteert haatcampagnes tegen journalisten.",
     '{"platforms": ["Facebook", "Instagram"]}'),
    ("TikTok", "platform", "techplatform",
     "Snel groeiend platform, primaire nieuwsbron voor jongeren. Algoritmisch gestuurd.", None),

    # --- DENKTANKS ---
    ("Clingendael Instituut", "denktank", "expert_bron",
     "Denktank internationale betrekkingen en veiligheid. Gefinancierd door ministeries (BuZa, Defensie). Levert experts aan media, adviseert overheid.",
     '{"financiering": ["Min. Buitenlandse Zaken", "Min. Defensie"]}'),
    ("HCSS (The Hague Centre for Strategic Studies)", "denktank", "expert_bron",
     "Denktank strategische/veiligheidsvraagstukken. Gefinancierd door overheid, NAVO, bedrijfsleven. Directeur Rob de Wijk is veelgevraagd mediacommentator.",
     '{"financiering": ["overheid", "NAVO", "bedrijfsleven"]}'),
    ("Nationale DenkTank", "denktank", "expert_bron",
     "Denktank die jonge academici inzet. Gefinancierd door commerciële sponsors (o.a. McKinsey), overheid, universiteiten.",
     '{"financiering": ["McKinsey", "overheid", "universiteiten"]}'),
    ("Teldersstichting", "denktank", "ideoloog",
     "Wetenschappelijk bureau VVD. Direct verbonden met liberale partijlijn.",
     '{"partij": "VVD"}'),
    ("Wiardi Beckman Stichting", "denktank", "ideoloog",
     "Wetenschappelijk bureau PvdA. Direct verbonden met sociaaldemocratische partijlijn.",
     '{"partij": "PvdA"}'),

    # --- OVERHEIDSINSTANTIES ---
    ("ACM (Autoriteit Consument & Markt)", "overheidsinstelling", "toezichthouder",
     "Mededingingstoezichthouder. Stelde strenge voorwaarden bij DPG/RTL-overname. Impliciete erkenning van gevaar eigendomsconcentratie.",
     '{"relevante_besluiten": ["DPG/RTL overname voorwaarden"]}'),
    ("WRR (Wetenschappelijke Raad voor het Regeringsbeleid)", "overheidsinstelling", "toezichthouder",
     "Adviesorgaan regering. Rapport 'Aandacht voor media' (2024): democratische functies media onder druk. Pleit voor herziening mediabeleid.",
     '{"rapport": "Aandacht voor media (2024)"}'),
    ("CvdM (Commissariaat voor de Media)", "overheidsinstelling", "toezichthouder",
     "Mediatoezichthouder. Signaleert dalend nieuwsgebruik, afnemend vertrouwen (vooral jongeren), economische kwetsbaarheid journalistiek.",
     '{"rapporten": "Digital News Reports"}'),
    ("Raad voor de Journalistiek", "overheidsinstelling", "toezichthouder",
     "Zelfregulering journalistiek. Kan geen bindende sancties opleggen. Morele autoriteit beperkt effectief.", None),
    ("Belastingdienst", "overheidsinstelling", "officiele_bron",
     "Uitvoeringsinstantie.", None),

    # --- POLITIEKE PARTIJEN ---
    ("VVD", "partij", "ideoloog",
     "Liberale partij, onderdeel van de neoliberale consensus. Wetenschappelijk bureau: Teldersstichting.", None),
    ("CDA", "partij", "ideoloog",
     "Christendemocratische partij. Steunde Irak-oorlog als regeringspartij.", None),
    ("PVV", "partij", "flak_producent",
     "Rechts-populistische partij. Wil publieke omroep afschaffen. Valt media actief aan.",
     '{"mediakritiek": "wil NOS/publieke omroep afschaffen"}'),
    ("PvdA", "partij", "ideoloog",
     "Sociaaldemocratische partij. Wetenschappelijk bureau: Wiardi Beckman Stichting.", None),
    ("SP", "partij", "flak_doelwit",
     "Socialistische partij.", None),

    # --- POLITICI ---
    ("Pieter Omtzigt", "persoon", "klokkenluider",
     "Voormalig CDA-Kamerlid. Criticus van het systeem.",
     '{"partij": "CDA (later NSC)"}'),
    ("Renske Leijten", "persoon", "klokkenluider",
     "SP-Kamerlid.", None),

    # --- JOURNALISTEN / EXPERTS ---
    ("Peter R. de Vries", "persoon", "flak_doelwit",
     "Misdaadjournalist, vermoord in 2021. Meest extreme voorbeeld van geweld tegen journalisten in NL.", None),
    ("Maarten van Rossem", "persoon", "expert_bron",
     "Amerikadeskundige en historicus. Kritisch over Irak-oorlog. Werd jarenlang niet meer uitgenodigd als commentator na afwijkende mening over WMD-claims.",
     '{"voorbeeld_van": "uitsluiting afwijkende expert"}'),
    ("Rob de Wijk", "persoon", "expert_bron",
     "Directeur HCSS, veelgevraagd mediacommentator over veiligheid en defensie. Bevestigt doorgaans NAVO-gezind narratief.", None),
    ("Ron Fresen", "persoon", "expert_bron",
     "Voormalig NOS-politiek verslaggever. Richtte na carrière een denktank op. Voorbeeld van draaideur media-politiek.", None),

    # --- ACADEMICI ---
    ("Willem Schinkel", "persoon", "expert_bron",
     "Socioloog met brede maatschappijkritiek waarin de rol van media wordt meegenomen.", None),

    # --- NGO'S ---
    ("Free Press Unlimited", "ngo", "flak_doelwit",
     "Pleit voor persvrijheid en bescherming journalisten. Focus meer op symptomen dan structurele oorzaken.", None),
    ("NVJ (Nederlandse Vereniging van Journalisten)", "ngo", "flak_doelwit",
     "Vakbond/beroepsvereniging journalisten. Pleit voor persvrijheid.", None),
    ("BOinK", "ngo", "burger",
     "Belangenorganisatie ouders kinderopvang.", None),

    # --- ONTBREKENDE KLEINE ENTITEITEN ---
    ("Koningshuis", "overheidsinstelling", "ideoloog",
     "Nederlands koningshuis. Aanwezig bij Bilderbergconferenties. Onderdeel van de transnationale elite.",
     None),
    ("Unibet", "bedrijf", "adverteerder",
     "Online gokbedrijf, grote adverteerder in NL media.", None),
    ("KBC Groep", "bedrijf", "aandeelhouder",
     "Belgische bank-verzekeringsgroep. Thomas Leysen was voorzitter.",
     '{"leysen": "voormalig voorzitter"}'),
    ("Umicore", "bedrijf", "aandeelhouder",
     "Belgisch materialentechnologiebedrijf. Thomas Leysen was voorzitter.",
     '{"leysen": "voormalig voorzitter"}'),

    # --- BEDRIJVEN MET ELITEVERBINDINGEN ---
    ("Shell", "bedrijf", "adverteerder",
     "Olie-multinational. CEO's aanwezig bij Bilderberg/Davos. Vertegenwoordigt fossiele belangen in NL economie.", None),
    ("ING", "bedrijf", "aandeelhouder",
     "Grote bank/financiële instelling. Top aanwezig bij Bilderberg/Davos.", None),
    ("ASML", "bedrijf", "aandeelhouder",
     "Chipmachinefabrikant, strategisch bedrijf. Top aanwezig bij Bilderberg/Davos.", None),
    ("Philips", "bedrijf", "aandeelhouder",
     "Technologieconcern. Top aanwezig bij Bilderberg/Davos.", None),
    ("dsm-firmenich", "bedrijf", "aandeelhouder",
     "Chemie/voedingsconcern. Thomas Leysen is voorzitter.", None),
    ("McKinsey", "bedrijf", "pr_machine",
     "Consultancyfirma. Sponsor Nationale DenkTank. Levert beleidsadviezen die belangen opdrachtgevers dienen.", None),

    # --- NAVO ---
    ("NAVO", "lobbygroep", "ideoloog",
     "Noord-Atlantische Verdragsorganisatie. Hoeksteen van pro-Atlantisch buitenlandbeleid. Onbetwist in dominant ideologisch frame. Financiert denktanks als HCSS.", None),
]


# =============================================================================
# RELATIES
# =============================================================================
# (source_name, target_name, relation_type, mechanism_name, description,
#  certainty, influence, evidence, bidirectional)
#
# certainty = hoe zeker is het dat deze relatie bestaat (0.0 - 1.0):
#   0.9-1.0 = Gedocumenteerd feit
#   0.7-0.89 = Sterk bewijs
#   0.5-0.69 = Waarschijnlijk
#   0.3-0.49 = Mogelijk
#   < 0.3 = Speculatief
#
# influence = hoe sterk beïnvloedt deze relatie de berichtgeving (0.0 - 1.0):
#   0.9-1.0 = Bepalend (bepaalt redactionele lijn, dagelijkse nieuwsstroom)
#   0.7-0.89 = Sterk (structureel effect op content, framing, of agenda)
#   0.5-0.69 = Matig (merkbaar effect, maar niet dominant)
#   0.3-0.49 = Beperkt (indirect, één van vele factoren)
#   < 0.3 = Marginaal (theoretisch aanwezig, nauwelijks meetbaar)

RELATIONS = [
    # =========================================================================
    # FILTER 1: EIGENDOM
    # =========================================================================

    # --- DPG Media eigendomsstructuur ---
    ("Epifin", "DPG Media", "eigendom", "eigendomsconcentratie",
     "Familie Van Thillo controleert DPG Media via Epifin",
     0.95, 0.70, "Gedocumenteerd in bedrijfsregistratie en jaarverslagen", False),
    ("Christian Van Thillo", "DPG Media", "eigendom", "eigendomsconcentratie",
     "Executive Chairman en via familie de facto eigenaar van DPG Media",
     0.95, 0.85, "Publiek bekend, bedrijfsdocumenten", False),
    ("Christian Van Thillo", "Epifin", "eigendom", None,
     "Van Thillo controleert DPG Media via investeringsvehikel Epifin",
     0.90, 0.30, "Bedrijfsregistratie", False),

    # DPG bezit media
    ("DPG Media", "AD (Algemeen Dagblad)", "eigendom", "eigendomsconcentratie",
     "DPG Media bezit het AD",
     0.95, 0.90, "Publiek bekend", False),
    ("DPG Media", "de Volkskrant", "eigendom", "eigendomsconcentratie",
     "DPG Media bezit de Volkskrant (via PCM overname)",
     0.95, 0.90, "Publiek bekend", False),
    ("DPG Media", "Trouw", "eigendom", "eigendomsconcentratie",
     "DPG Media bezit Trouw",
     0.95, 0.90, "Publiek bekend", False),
    ("DPG Media", "Het Parool", "eigendom", "eigendomsconcentratie",
     "DPG Media bezit Het Parool",
     0.95, 0.85, "Publiek bekend", False),
    ("DPG Media", "NU.nl", "eigendom", "eigendomsconcentratie",
     "DPG Media bezit NU.nl (via Sanoma overname)",
     0.95, 0.90, "Publiek bekend", False),
    ("DPG Media", "RTL Nederland", "eigendom", "eigendomsconcentratie",
     "DPG Media nam RTL Nederland over, onder strenge ACM-voorwaarden",
     0.95, 0.80, "ACM-besluit en mediaberichtgeving", False),

    # --- Mediahuis eigendomsstructuur ---
    ("Thomas Leysen", "Mediahuis", "eigendom", "eigendomsconcentratie",
     "Voorzitter Mediahuis, controleert via Mediahuis Partners",
     0.95, 0.85, "Publiek bekend, bedrijfsdocumenten", False),
    ("Familie Baert", "Mediahuis", "eigendom", "eigendomsconcentratie",
     "Aandeelhouder Mediahuis via Concentra",
     0.90, 0.50, "Bedrijfsdocumenten", False),
    ("Concentra", "Mediahuis", "eigendom", None,
     "Concentra (fam. Baert) is aandeelhouder Mediahuis",
     0.90, 0.30, "Bedrijfsdocumenten", False),
    ("Familie Van Puijenbroek", "Mediahuis", "eigendom", "eigendomsconcentratie",
     "Aandeelhouder Mediahuis via VP Exploitatie",
     0.90, 0.50, "Bedrijfsdocumenten", False),
    ("VP Exploitatie", "Mediahuis", "eigendom", None,
     "VP Exploitatie (fam. Van Puijenbroek) is aandeelhouder Mediahuis",
     0.90, 0.30, "Bedrijfsdocumenten", False),

    # Mediahuis bezit media
    ("Mediahuis", "De Telegraaf", "eigendom", "eigendomsconcentratie",
     "Mediahuis bezit De Telegraaf (via TMG overname)",
     0.95, 0.90, "Publiek bekend", False),
    ("Mediahuis", "NRC", "eigendom", "eigendomsconcentratie",
     "Mediahuis bezit NRC",
     0.95, 0.90, "Publiek bekend", False),

    # ANP eigendom
    ("Chris Oomen", "ANP", "eigendom", None,
     "Eigenaar ANP sinds 2021, als 'maatschappelijk investeerder'",
     0.95, 0.50, "Publiek bekend", False),
    ("John de Mol", "Talpa Network", "eigendom", None,
     "John de Mol is eigenaar Talpa Network",
     0.95, 0.20, "Publiek bekend", False),

    # Winstmaximalisatie effecten
    ("DPG Media", "de Volkskrant", "beinvloeding", "winstmaximalisatie",
     "Van Thillo staat bekend om vooroordelen tegen linkse redacties, wat dynamiek bij overname Volkskrant beïnvloedde",
     0.70, 0.60, "Bronvermelding in rapport, journalistieke bronnen", False),
    ("DPG Media", "RTL Nederland", "beinvloeding", "winstmaximalisatie",
     "ACM moest vergaande voorwaarden stellen om redactionele onafhankelijkheid te beschermen tegen eigenaarsbelangen",
     0.85, 0.70, "ACM-besluit met onafhankelijke stichtingen en vetorecht", False),

    # =========================================================================
    # FILTER 2: ADVERTENTIE
    # =========================================================================

    # Grote adverteerders → DPG
    ("Albert Heijn", "DPG Media", "adverteerder", "advertentiedruk",
     "Top-adverteerder NL, significante advertentie-uitgaven bij grote media",
     0.80, 0.40, "Nielsen advertentiedata, top-adverteerderslijsten", False),
    ("Lidl", "DPG Media", "adverteerder", "advertentiedruk",
     "Top-adverteerder NL",
     0.80, 0.35, "Nielsen data", False),
    ("Procter & Gamble", "DPG Media", "adverteerder", "advertentiedruk",
     "FMCG-multinational, top-adverteerder",
     0.80, 0.40, "Nielsen data", False),
    ("Unilever", "DPG Media", "adverteerder", "advertentiedruk",
     "FMCG-multinational, top-adverteerder NL",
     0.80, 0.40, "Nielsen data", False),

    # NU.nl specifiek afhankelijk
    ("Albert Heijn", "NU.nl", "adverteerder", "commerciele_afhankelijkheid",
     "NU.nl als gratis platform extra afhankelijk van adverteerders",
     0.75, 0.70, "Businessmodel NU.nl is advertentie-gedreven", False),

    # Adverteerders → Mediahuis
    ("Procter & Gamble", "Mediahuis", "adverteerder", "advertentiedruk",
     "Top-adverteerder bij Nederlandse media",
     0.75, 0.35, "Nielsen data", False),
    ("Unilever", "Mediahuis", "adverteerder", "advertentiedruk",
     "Top-adverteerder bij Nederlandse media",
     0.75, 0.35, "Nielsen data", False),
    ("Nederlandse Loterij", "DPG Media", "adverteerder", "advertentiedruk",
     "Loterijen/gokbedrijven zijn grote adverteerders in NL media",
     0.75, 0.35, "Nielsen data, top-adverteerders", False),
    ("Shell", "DPG Media", "adverteerder", "advertentiedruk",
     "Fossiele industrie als adverteerder beïnvloedt redactioneel klimaat",
     0.60, 0.45, "Indirect bewijs: grote advertentiebudgetten fossiele sector", False),

    # =========================================================================
    # FILTER 3: SOURCING
    # =========================================================================

    # ANP als centrale bron (pakketjournalistiek) — HOGE invloed
    ("ANP", "de Volkskrant", "beinvloeding", "pakketjournalistiek",
     "Volkskrant neemt op grote schaal ANP-berichten over ('pakketjournalistiek')",
     0.85, 0.80, "Onderzoek CvdM", False),
    ("ANP", "De Telegraaf", "beinvloeding", "pakketjournalistiek",
     "Telegraaf maakt grote gebruik van ANP-berichten",
     0.85, 0.80, "CvdM onderzoek", False),
    ("ANP", "NOS", "beinvloeding", "pakketjournalistiek",
     "NOS maakt gebruik van ANP als primaire bron",
     0.85, 0.70, "Publiek bekend", False),
    ("ANP", "RTL Nederland", "beinvloeding", "pakketjournalistiek",
     "RTL maakt gebruik van ANP-berichten",
     0.85, 0.75, "Publiek bekend", False),
    ("ANP", "AD (Algemeen Dagblad)", "beinvloeding", "pakketjournalistiek",
     "AD neemt ANP-berichten over",
     0.85, 0.85, "CvdM onderzoek", False),
    ("ANP", "NU.nl", "beinvloeding", "pakketjournalistiek",
     "NU.nl maakt intensief gebruik van ANP",
     0.85, 0.90, "Publiek bekend", False),

    # Denktanks als bronnen (expert framing)
    ("Clingendael Instituut", "NOS", "beinvloeding", "expert_framing",
     "Clingendael levert experts aan media, met name voor buitenland/veiligheid",
     0.80, 0.55, "Rapport: Clingendael experts frequent in media", False),
    ("HCSS (The Hague Centre for Strategic Studies)", "NOS", "beinvloeding", "expert_framing",
     "HCSS-directeur Rob de Wijk is veelgevraagd mediacommentator. Bevestigt NAVO-gezind narratief.",
     0.80, 0.60, "Publiek waarneembaar in media-optredens", False),
    ("Rob de Wijk", "HCSS (The Hague Centre for Strategic Studies)", "personeel", None,
     "Rob de Wijk is directeur HCSS",
     0.95, 0.20, "Publiek bekend", False),
    ("HCSS (The Hague Centre for Strategic Studies)", "RTL Nederland", "beinvloeding", "expert_framing",
     "HCSS levert experts aan RTL voor duiding",
     0.70, 0.50, "Media-optredens", False),

    # Denktank financiering
    ("NAVO", "HCSS (The Hague Centre for Strategic Studies)", "financiering", None,
     "NAVO financiert HCSS projecten",
     0.75, 0.60, "Rapport: financiering door int. organisaties (NAVO)", False),
    ("McKinsey", "Nationale DenkTank", "financiering", None,
     "McKinsey is commerciële sponsor van de Nationale DenkTank",
     0.85, 0.55, "Publiek bekend, sponsorlijsten", False),

    # Haagse stam / draaideur
    ("Ron Fresen", "NOS", "personeel", "draaideurconstructie",
     "Voormalig NOS politiek verslaggever, richtte na carrière denktank op. Voorbeeld draaideur media-politiek.",
     0.90, 0.40, "Publiek bekend", False),

    # Partij-denktank verbindingen
    ("VVD", "Teldersstichting", "alliantie", None,
     "Teldersstichting is wetenschappelijk bureau van VVD",
     0.95, 0.50, "Officieel wetenschappelijk bureau", False),
    ("PvdA", "Wiardi Beckman Stichting", "alliantie", None,
     "Wiardi Beckman Stichting is wetenschappelijk bureau van PvdA",
     0.95, 0.45, "Officieel wetenschappelijk bureau", False),

    # =========================================================================
    # FILTER 4: FLAK
    # =========================================================================

    # PVV aanval op publieke omroep
    ("PVV", "NOS", "censuur", "publieke_aanval",
     "PVV wil publieke omroep afschaffen. Directe bedreiging journalistieke infrastructuur.",
     0.90, 0.65, "Partijprogramma PVV, publieke uitspraken", False),

    # Uitsluiting Maarten van Rossem
    ("NOS", "Maarten van Rossem", "censuur", "deplatforming",
     "Van Rossem werd jarenlang niet meer uitgenodigd als commentator na kritische Irak-analyse.",
     0.75, 0.80, "Eigen verklaring Van Rossem", False),

    # Peter R. de Vries - geweld
    ("Peter R. de Vries", "NOS", "beinvloeding", None,
     "Moord op De Vries (2021) is meest extreme voorbeeld van geweld tegen journalisten in NL. Chilling effect op hele beroepsgroep.",
     0.95, 0.70, "Gedocumenteerd feit", False),

    # Zelfcensuur mechanisme (structureel)
    ("DPG Media", "de Volkskrant", "beinvloeding", "zelfcensuur",
     "Sociologische homogeniteit en conformisme op redacties leiden tot zelfcensuur.",
     0.70, 0.75, "Onderzoek: 61% journalisten heeft te maken gehad met intimidatie", False),

    # Juridische dreiging (SLAPPs)
    ("Groupe Bruxelles Lambert", "Free Press Unlimited", "oppositie", "juridische_dreiging",
     "Machtige bedrijven gebruiken SLAPPs om journalisten te intimideren.",
     0.50, 0.55, "Rapport over toename SLAPPs in NL, indirect bewijs voor specifieke actor", False),

    # =========================================================================
    # FILTER 5: IDEOLOGIE
    # =========================================================================

    # Elite-netwerken → ideologische synchronisatie
    ("Bilderberg Groep", "Thomas Leysen", "lidmaatschap", "ideologische_synchronisatie",
     "Leysen is lid van de stuurgroep van de Bilderberg Groep. Kernpositie in elite-netwerk.",
     0.95, 0.70, "Publiek bekende deelnemerslijsten", False),
    ("Trilaterale Commissie", "Thomas Leysen", "lidmaatschap", "ideologische_synchronisatie",
     "Leysen is lid van de Trilaterale Commissie",
     0.90, 0.55, "Publiek bekend", False),
    ("European Round Table of Industrialists", "Thomas Leysen", "lidmaatschap", "ideologische_synchronisatie",
     "Leysen is lid van de ERT",
     0.90, 0.55, "Publiek bekend", False),
    ("Groupe Bruxelles Lambert", "Christian Van Thillo", "personeel", "draaideurconstructie",
     "Van Thillo is bestuurder bij GBL sinds 2023. Plaatst hem in hart Europees corporate netwerk.",
     0.95, 0.60, "Publiek bekend, GBL jaarverslag", False),

    # Ideologische synchronisatie via elite-fora
    ("Bilderberg Groep", "DPG Media", "beinvloeding", "ideologische_synchronisatie",
     "Media-eigenaren delen via Bilderberg wereldbeeld met politieke en economische elite.",
     0.75, 0.65, "Deelnemerslijsten Bilderberg, netwerkanalyse", False),
    ("World Economic Forum", "DPG Media", "beinvloeding", "hegemonische_naturalisatie",
     "WEF propageert 'stakeholder capitalism'. Media nemen dit frame onkritisch over.",
     0.60, 0.55, "Analyse in rapport: mediaframing van WEF-kritiek als complottheorie", False),
    ("World Economic Forum", "NOS", "beinvloeding", "hegemonische_naturalisatie",
     "WEF-narratief wordt als vanzelfsprekend gepresenteerd. Kritiek wordt als complottheorie geframed.",
     0.55, 0.50, "Inhoudsanalyse vijf Nederlandse kranten", False),

    # Bilderberg → brede invloed
    ("Bilderberg Groep", "Shell", "lidmaatschap", None,
     "Shell-top is regelmatig aanwezig bij Bilderbergconferenties",
     0.85, 0.35, "Deelnemerslijsten Bilderberg", False),
    ("Bilderberg Groep", "ING", "lidmaatschap", None,
     "ING-top aanwezig bij Bilderbergconferenties",
     0.80, 0.30, "Deelnemerslijsten", False),
    ("Bilderberg Groep", "ASML", "lidmaatschap", None,
     "ASML-top aanwezig bij Bilderbergconferenties",
     0.75, 0.25, "Deelnemerslijsten", False),

    # Pro-Atlantisch narratief
    ("NAVO", "NOS", "beinvloeding", "hegemonische_naturalisatie",
     "NAVO-lidmaatschap als onbetwiste hoeksteen in mediaberichtgeving. Afwijkende analyse leidt tot labeling als 'Poetin-versteher'.",
     0.75, 0.80, "Analyse berichtgeving Oekraïne in rapport", False),
    ("NAVO", "Clingendael Instituut", "financiering", None,
     "NAVO-gezinde denktanks worden als 'neutrale' experts opgevoerd",
     0.70, 0.55, "Financieringsstructuur en media-optredens", False),

    # Etikettering - corona
    ("NOS", "Maarten van Rossem", "censuur", "etikettering",
     "Critici werden gelabeld als 'wappie', 'complotdenker'. Legitieme vragen gediskwalificeerd.",
     0.70, 0.75, "Analyse coronaberichtgeving in rapport", False),

    # Techplatforms als nieuwe filters (algoritmische filtering) — HOGE invloed
    ("Google", "DPG Media", "beinvloeding", "algoritmische_filtering",
     "Media worden afhankelijker van techplatforms, moeten content aanpassen aan algoritme-logica",
     0.80, 0.75, "WRR en CvdM rapporten over platformdominantie", False),
    ("Meta (Facebook/Instagram)", "DPG Media", "beinvloeding", "algoritmische_filtering",
     "Social media als distributienetwerk. Algoritmes geven voorkeur aan emotionele content.",
     0.80, 0.75, "WRR rapport, Digital News Reports", False),
    ("TikTok", "NOS", "beinvloeding", "algoritmische_filtering",
     "Jongeren gebruiken TikTok als primaire nieuwsbron i.p.v. traditionele media.",
     0.70, 0.65, "CvdM Digital News Reports", False),

    # Institutionele beleggers → systeem
    ("BlackRock", "Shell", "eigendom", None,
     "BlackRock is grootste aandeelhouder in vrijwel alle grote beursgenoteerde bedrijven.",
     0.90, 0.25, "Publieke aandeelhoudersregistraties", False),
    ("BlackRock", "ING", "eigendom", None,
     "BlackRock grote aandeelhouder in Nederlandse financiële instellingen",
     0.85, 0.25, "Aandeelhoudersregistraties", False),
    ("Vanguard", "Shell", "eigendom", None,
     "Vanguard samen met BlackRock dominant in wereldwijd aandeelhouderschap",
     0.85, 0.20, "Aandeelhoudersregistraties", False),

    # Thomas Leysen corporate netwerk
    ("Thomas Leysen", "dsm-firmenich", "personeel", "draaideurconstructie",
     "Leysen is voorzitter van dsm-firmenich",
     0.95, 0.45, "Publiek bekend", False),

    # =========================================================================
    # AANVULLENDE RELATIES
    # =========================================================================

    # Eigendomsketens compleet
    ("Familie Baert", "Concentra", "eigendom", None,
     "Familie Baert controleert Concentra, aandeelhouder Mediahuis",
     0.90, 0.30, "Bedrijfsdocumenten", False),
    ("Familie Van Puijenbroek", "VP Exploitatie", "eigendom", None,
     "Familie Van Puijenbroek controleert VP Exploitatie, aandeelhouder Mediahuis",
     0.90, 0.30, "Bedrijfsdocumenten", False),

    # Van Thillo → EPC (voorzitter)
    ("Christian Van Thillo", "European Publishers Council", "personeel", "draaideurconstructie",
     "Van Thillo is voorzitter van de European Publishers Council — Europese uitgeverslobby",
     0.95, 0.50, "Publiek bekend", False),

    # ACM toezicht
    ("ACM (Autoriteit Consument & Markt)", "DPG Media", "beinvloeding", None,
     "ACM stelde uitzonderlijk strenge voorwaarden bij DPG/RTL-overname.",
     0.95, 0.60, "ACM-besluit, publiek bekend", False),

    # ANP → overige media
    ("ANP", "NRC", "beinvloeding", "pakketjournalistiek",
     "NRC maakt gebruik van ANP-berichten",
     0.85, 0.70, "CvdM onderzoek", False),
    ("ANP", "Trouw", "beinvloeding", "pakketjournalistiek",
     "Trouw maakt gebruik van ANP-berichten",
     0.85, 0.75, "CvdM onderzoek", False),
    ("ANP", "Het Parool", "beinvloeding", "pakketjournalistiek",
     "Het Parool maakt gebruik van ANP-berichten",
     0.80, 0.75, "Inferentie: geldt voor alle NL dagbladen", False),

    # Techplatforms → alle media
    ("Google", "Mediahuis", "beinvloeding", "algoritmische_filtering",
     "Mediahuis-titels afhankelijk van Google voor bereik en advertentie-inkomsten",
     0.80, 0.70, "WRR en CvdM rapporten", False),
    ("Google", "NOS", "beinvloeding", "algoritmische_filtering",
     "NOS content wordt gefilterd door Google-algoritmes",
     0.75, 0.55, "WRR rapport", False),
    ("Meta (Facebook/Instagram)", "Mediahuis", "beinvloeding", "algoritmische_filtering",
     "Mediahuis-titels afhankelijk van Meta voor distributie",
     0.80, 0.70, "WRR rapport", False),
    ("Meta (Facebook/Instagram)", "NOS", "beinvloeding", "algoritmische_filtering",
     "NOS content op Facebook/Instagram onderhevig aan algoritmische selectie",
     0.75, 0.55, "WRR rapport", False),
    ("TikTok", "DPG Media", "beinvloeding", "algoritmische_filtering",
     "Jongeren bereiken DPG-media steeds meer via TikTok",
     0.65, 0.55, "CvdM Digital News Reports", False),

    # Koningshuis bij Bilderberg
    ("Bilderberg Groep", "Koningshuis", "lidmaatschap", "ideologische_synchronisatie",
     "Nederlands koningshuis is regelmatig aanwezig bij Bilderbergconferenties",
     0.90, 0.45, "Deelnemerslijsten Bilderberg", False),

    # Leysen corporate netwerk compleet
    ("Thomas Leysen", "KBC Groep", "personeel", "draaideurconstructie",
     "Leysen was voorzitter van KBC Groep",
     0.95, 0.40, "Publiek bekend", False),
    ("Thomas Leysen", "Umicore", "personeel", "draaideurconstructie",
     "Leysen was voorzitter van Umicore",
     0.95, 0.35, "Publiek bekend", False),

    # Gokadverteerder
    ("Unibet", "DPG Media", "adverteerder", "advertentiedruk",
     "Online gokbedrijf, grote adverteerder in NL media",
     0.70, 0.30, "Nielsen data, top-adverteerderslijsten", False),

    # Adverteerders → Mediahuis specifiek
    ("Albert Heijn", "Mediahuis", "adverteerder", "advertentiedruk",
     "Top-adverteerder, adverteert ook in Mediahuis-titels",
     0.80, 0.40, "Nielsen data", False),
    ("Lidl", "Mediahuis", "adverteerder", "advertentiedruk",
     "Top-adverteerder, adverteert ook in Mediahuis-titels",
     0.80, 0.35, "Nielsen data", False),
    ("Nederlandse Loterij", "Mediahuis", "adverteerder", "advertentiedruk",
     "Loterij adverteert breed in NL media",
     0.70, 0.30, "Nielsen data", False),

    # Irak-oorlog: specifieke media-analyse
    ("CDA", "de Volkskrant", "beinvloeding", "bron_afhankelijkheid",
     "Volkskrant vertoonde WMD-bias: 3x vaker claims als feit dan twijfel",
     0.80, 0.80, "Kwantitatieve inhoudsanalyse", False),
    ("CDA", "De Telegraaf", "beinvloeding", "bron_afhankelijkheid",
     "Telegraaf volgde pro-Atlantische consensus in Irak-berichtgeving",
     0.80, 0.80, "Inhoudsanalyse", False),
    ("CDA", "NRC", "beinvloeding", "bron_afhankelijkheid",
     "NRC volgde pro-Atlantische consensus, WMD-claims dominant",
     0.80, 0.75, "Inhoudsanalyse", False),

    # Bilderberg → Philips
    ("Bilderberg Groep", "Philips", "lidmaatschap", "ideologische_synchronisatie",
     "Philips-top regelmatig aanwezig bij Bilderbergconferenties",
     0.80, 0.25, "Deelnemerslijsten", False),

    # Irak-oorlog framing
    ("CDA", "NOS", "beinvloeding", "pr_subsidie",
     "CDA-regering steunde Irak-oorlog. Media volgden pro-Atlantische consensus.",
     0.80, 0.80, "Kwantitatieve inhoudsanalyse", False),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # 1. Registreer de bron
    cur.execute(
        """INSERT OR IGNORE INTO sources (title, author, source_type, summary)
           VALUES (?, ?, ?, ?)""",
        (SOURCE_TITLE, "AI-analyse (Claude)", "rapport",
         "Analyse van het propagandamodel in het Nederlandse medialandschap, gebaseerd op het propagandamodel, culturele hegemonie en systeemtheorie.")
    )
    conn.commit()
    cur.execute("SELECT id FROM sources WHERE title = ?", (SOURCE_TITLE,))
    source_id = cur.fetchone()[0]

    # Registreer locatie van het bronbestand
    cur.execute(
        """INSERT OR IGNORE INTO source_locations (source_id, location_type, location, notes)
           VALUES (?, 'file', ?, 'Lokaal bronbestand in project')""",
        (source_id, SOURCE_PATH)
    )
    conn.commit()

    # 2. Bouw role name → id lookup
    cur.execute("SELECT id, name FROM roles")
    role_map = {name: rid for rid, name in cur.fetchall()}

    # 3. Bouw mechanism name → id lookup
    cur.execute("SELECT id, name FROM mechanisms")
    mech_map = {name: mid for mid, name in cur.fetchall()}

    # 4. Insert entiteiten
    entity_count = 0
    for name, etype, role_name, desc, metadata in ENTITIES:
        role_id = role_map.get(role_name)
        cur.execute(
            """INSERT OR IGNORE INTO entities
               (name, type, primary_role_id, description, metadata)
               VALUES (?, ?, ?, ?, ?)""",
            (name, etype, role_id, desc, metadata)
        )
        if cur.rowcount > 0:
            entity_count += 1
            eid = cur.lastrowid
            if role_id:
                cur.execute(
                    "INSERT OR IGNORE INTO entity_roles (entity_id, role_id) VALUES (?, ?)",
                    (eid, role_id)
                )
            cur.execute(
                "INSERT OR IGNORE INTO source_mentions (source_id, entity_id) VALUES (?, ?)",
                (source_id, eid)
            )
    conn.commit()

    # 5. Bouw entity name → id lookup
    cur.execute("SELECT id, name FROM entities")
    entity_map = {name: eid for eid, name in cur.fetchall()}

    # 6. Insert relaties
    relation_count = 0
    for (src_name, tgt_name, rel_type, mech_name, desc,
         certainty, influence, evidence, bidir) in RELATIONS:
        src_id = entity_map.get(src_name)
        tgt_id = entity_map.get(tgt_name)
        mech_id = mech_map.get(mech_name) if mech_name else None

        if not src_id:
            print(f"  WARN: bron-entiteit '{src_name}' niet gevonden, skip")
            continue
        if not tgt_id:
            print(f"  WARN: doel-entiteit '{tgt_name}' niet gevonden, skip")
            continue

        cur.execute(
            """INSERT OR IGNORE INTO relations
               (source_id, target_id, relation_type, mechanism_id,
                description, certainty, influence, bidirectional)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (src_id, tgt_id, rel_type, mech_id, desc,
             certainty, influence, bidir)
        )
        if cur.rowcount > 0:
            relation_count += 1
            rel_id = cur.lastrowid
            # Maak een argument aan met citatie naar de bron
            cur.execute(
                """INSERT INTO arguments
                   (relation_id, stance, claim, weight)
                   VALUES (?, 'supporting', ?, ?)""",
                (rel_id, desc, certainty)
            )
            arg_id = cur.lastrowid
            cur.execute(
                """INSERT INTO citations
                   (argument_id, source_id, context)
                   VALUES (?, ?, ?)""",
                (arg_id, source_id, evidence)
            )

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"Bron: {SOURCE_TITLE}")
    print(f"{'='*60}")
    print(f"Entiteiten toegevoegd:  {entity_count}")
    print(f"Relaties toegevoegd:    {relation_count}")
    print(f"Bron-ID:                {source_id}")
    print(f"{'='*60}")
    print(f"\nZekerheid (certainty):")
    print(f"  0.9-1.0 (gedocumenteerd):  {sum(1 for r in RELATIONS if r[5] >= 0.9)}")
    print(f"  0.7-0.89 (sterk bewijs):   {sum(1 for r in RELATIONS if 0.7 <= r[5] < 0.9)}")
    print(f"  0.5-0.69 (waarschijnlijk): {sum(1 for r in RELATIONS if 0.5 <= r[5] < 0.7)}")
    print(f"  <0.5 (onzeker):            {sum(1 for r in RELATIONS if r[5] < 0.5)}")
    print(f"\nInvloed (influence):")
    print(f"  0.7-1.0 (sterk/bepalend): {sum(1 for r in RELATIONS if r[6] >= 0.7)}")
    print(f"  0.5-0.69 (matig):         {sum(1 for r in RELATIONS if 0.5 <= r[6] < 0.7)}")
    print(f"  0.3-0.49 (beperkt):       {sum(1 for r in RELATIONS if 0.3 <= r[6] < 0.5)}")
    print(f"  <0.3 (marginaal):         {sum(1 for r in RELATIONS if r[6] < 0.3)}")


if __name__ == "__main__":
    seed()
