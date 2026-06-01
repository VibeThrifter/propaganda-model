"""
Grondige tweede verrijking: alle ontbrekende entiteiten en relaties uit de AI-bron.

Voegt toe:
- Historische overnames (PCM, TMG, Sanoma, VNU, NRC Media)
- Alle ontbrekende cross-verbindingen tussen bestaande entiteiten
- Brede adverteerder-media relaties per individuele titel
- Brede sourcing/beinvloedingsrelaties
- Alle genoemde casestudie-verbindingen (Irak, Corona, Oekraïne)
- Elke relatie krijgt certainty, influence, argument + citatie
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
SOURCE_TITLE = "De Onzichtbare Architecten: Een Analyse van het Propagandamodel in het Nederlandse Medialandschap"


# =============================================================================
# NIEUWE ENTITEITEN
# =============================================================================
NEW_ENTITIES = [
    # Historische bedrijven (overnames die eigendomsconcentratie verklaren)
    ("PCM Uitgevers", "bedrijf", "mediaeigenaar",
     "Voormalig uitgever van de Volkskrant, Trouw, NRC en AD. Overgenomen door DPG Media (toen De Persgroep). NRC later doorverkocht aan Mediahuis.",
     '{"status": "overgenomen door DPG Media"}'),
    ("Sanoma Nederland", "bedrijf", "mediaeigenaar",
     "Voormalig eigenaar van NU.nl. Overgenomen door DPG Media.",
     '{"status": "overgenomen door DPG Media"}'),
    ("VNU Media", "bedrijf", "mediaeigenaar",
     "Voormalig mediabedrijf, overgenomen door DPG Media in reeks acquisities.",
     '{"status": "overgenomen door DPG Media"}'),
    ("TMG (Telegraaf Media Groep)", "bedrijf", "mediaeigenaar",
     "Voormalig eigenaar van De Telegraaf. Overgenomen door Mediahuis.",
     '{"status": "overgenomen door Mediahuis"}'),
    ("NRC Media", "bedrijf", "mediaeigenaar",
     "Voormalig eigenaar van NRC. Overgenomen door Mediahuis na eerdere doorverkoop door DPG.",
     '{"status": "overgenomen door Mediahuis"}'),
    ("Metro", "mediaorganisatie", "mediaverkoper",
     "Gratis krant, eigendom Mediahuis. Genoemd in eigendomstabel als Mediahuis-titel.",
     None),

    # Overig
    ("Imerys", "bedrijf", "aandeelhouder",
     "Frans mineralenbedrijf. Belang van Groupe Bruxelles Lambert. Illustreert breedte Van Thillo's corporate netwerk.",
     None),
    ("UvA Journalistiek", "denktank", "expert_bron",
     "Duale master Journalistiek en Media aan de UvA. Stimuleert kritische reflectie op rol journalistiek en ethische dimensies.",
     None),
    ("OMT (Outbreak Management Team)", "overheidsinstelling", "officiele_bron",
     "Adviesorgaan tijdens coronacrisis. OMT-leden domineerden talkshows als consensus-stemmen tegenover critici.",
     None),
    ("Tweede Kamer", "overheidsinstelling", "officiele_bron",
     "Parlement. Volksvertegenwoordiging en medewetgever.",
     None),
    ("De Persgroep", "bedrijf", "mediaeigenaar",
     "Voormalige naam van DPG Media. Belgisch mediabedrijf dat via decennia van overnames uitgroeide tot dominant conglomeraat.",
     '{"status": "hernoemd naar DPG Media"}'),
]


# =============================================================================
# NIEUWE RELATIES — per filter/hoofdstuk
# =============================================================================
NEW_RELATIONS = [
    # =======================================================================
    # EIGENDOM: Historische overnames die concentratie verklaren
    # =======================================================================
    ("DPG Media", "PCM Uitgevers", "eigendom", "eigendomsconcentratie",
     "DPG (toen De Persgroep) nam PCM Uitgevers over: Volkskrant, Trouw, AD kwamen in bezit",
     0.95, 0.85, "Gedocumenteerd in bedrijfshistorie en rapport [15, 19]"),
    ("DPG Media", "VNU Media", "eigendom", "eigendomsconcentratie",
     "DPG nam VNU Media over in reeks acquisities die leidde tot dominante positie",
     0.90, 0.60, "Rapport [15, 19]"),
    ("DPG Media", "Sanoma Nederland", "eigendom", "eigendomsconcentratie",
     "DPG nam Sanoma Nederland over, waarmee NU.nl in bezit kwam",
     0.95, 0.80, "Rapport [15, 19]"),
    ("Mediahuis", "TMG (Telegraaf Media Groep)", "eigendom", "eigendomsconcentratie",
     "Mediahuis verwierf TMG, waarmee De Telegraaf — grootste krant van NL — in bezit kwam",
     0.95, 0.90, "Rapport [17, 18]"),
    ("Mediahuis", "NRC Media", "eigendom", "eigendomsconcentratie",
     "Mediahuis verwierf NRC Media na eerdere doorverkoop door DPG",
     0.95, 0.85, "Rapport [17, 18]"),
    ("Mediahuis", "Metro", "eigendom", "eigendomsconcentratie",
     "Metro is gratis krant in bezit van Mediahuis",
     0.90, 0.50, "Tabel 1 in rapport"),
    ("De Persgroep", "DPG Media", "eigendom", None,
     "De Persgroep is de voormalige naam van DPG Media — zelfde bedrijf, hernoemd",
     0.95, 0.10, "Publiek bekend"),
    ("PCM Uitgevers", "de Volkskrant", "eigendom", None,
     "PCM bezat de Volkskrant vóór overname door DPG",
     0.95, 0.85, "Historisch gedocumenteerd"),
    ("PCM Uitgevers", "Trouw", "eigendom", None,
     "PCM bezat Trouw vóór overname door DPG",
     0.95, 0.85, "Historisch gedocumenteerd"),
    ("PCM Uitgevers", "AD (Algemeen Dagblad)", "eigendom", None,
     "PCM bezat het AD vóór overname door DPG",
     0.95, 0.85, "Historisch gedocumenteerd"),
    ("Sanoma Nederland", "NU.nl", "eigendom", None,
     "Sanoma bezat NU.nl vóór overname door DPG",
     0.95, 0.85, "Historisch gedocumenteerd"),
    ("TMG (Telegraaf Media Groep)", "De Telegraaf", "eigendom", None,
     "TMG bezat De Telegraaf vóór overname door Mediahuis",
     0.95, 0.90, "Historisch gedocumenteerd"),

    # GBL belangen compleet
    ("Groupe Bruxelles Lambert", "Imerys", "eigendom", None,
     "GBL heeft belang in Imerys. Onderdeel van breed corporate netwerk Van Thillo",
     0.85, 0.15, "Rapport [31, 32, 33]"),

    # Duopolie relatie
    ("DPG Media", "Mediahuis", "alliantie", "eigendomsconcentratie",
     "DPG en Mediahuis vormen samen een duopolie met >90% online marktaandeel. Beperkte onderlinge concurrentie",
     0.90, 0.70, "Rapport [13]: marktaandeel >90% samen"),

    # =======================================================================
    # ADVERTENTIE: Alle adverteerders → individuele titels
    # =======================================================================
    # Adverteerders → RTL Nederland (commerciële omroep, extra afhankelijk)
    ("Albert Heijn", "RTL Nederland", "adverteerder", "advertentiedruk",
     "Albert Heijn is top-adverteerder bij commerciële omroep RTL",
     0.80, 0.50, "Nielsen data, rapport [46, 47]"),
    ("Lidl", "RTL Nederland", "adverteerder", "advertentiedruk",
     "Lidl is top-adverteerder bij commerciële omroep",
     0.80, 0.45, "Nielsen data"),
    ("Bol.com", "RTL Nederland", "adverteerder", "advertentiedruk",
     "Bol.com adverteert bij RTL als grote webwinkel",
     0.75, 0.35, "Nielsen data"),
    ("A.S. Watson (Kruidvat)", "RTL Nederland", "adverteerder", "advertentiedruk",
     "A.S. Watson is top-adverteerder bij commerciële omroepen",
     0.75, 0.35, "Nielsen data"),
    ("Nederlandse Loterij", "RTL Nederland", "adverteerder", "advertentiedruk",
     "Loterijen zijn grote adverteerders bij commerciële TV",
     0.75, 0.40, "Nielsen data"),
    ("Postcode Loterij", "RTL Nederland", "adverteerder", "advertentiedruk",
     "Postcode Loterij is grote adverteerder bij commerciële TV",
     0.75, 0.40, "Nielsen data"),
    ("Unibet", "RTL Nederland", "adverteerder", "advertentiedruk",
     "Online gokbedrijven adverteren zwaar bij commerciële omroepen",
     0.70, 0.35, "Nielsen data"),

    # Adverteerders → individuele kranten
    ("Albert Heijn", "de Volkskrant", "adverteerder", "advertentiedruk",
     "Albert Heijn adverteert in landelijke kranten",
     0.75, 0.30, "Nielsen data, structureel"),
    ("Albert Heijn", "De Telegraaf", "adverteerder", "advertentiedruk",
     "Albert Heijn adverteert in De Telegraaf als grootste krant",
     0.80, 0.35, "Nielsen data"),
    ("Albert Heijn", "AD (Algemeen Dagblad)", "adverteerder", "advertentiedruk",
     "Albert Heijn adverteert in AD",
     0.75, 0.30, "Nielsen data"),
    ("Lidl", "De Telegraaf", "adverteerder", "advertentiedruk",
     "Lidl adverteert in De Telegraaf",
     0.75, 0.30, "Nielsen data"),
    ("Unilever", "de Volkskrant", "adverteerder", "supportive_selling_environment",
     "FMCG-adverteerders creëren behoefte aan consumptievriendelijke omgeving",
     0.70, 0.35, "Rapport: 'supportive selling environment' [3]"),
    ("Unilever", "NOS", "adverteerder", "supportive_selling_environment",
     "FMCG-multinationals adverteren bij publieke omroep, creëren afhankelijkheid",
     0.65, 0.25, "Structureel"),
    ("Procter & Gamble", "De Telegraaf", "adverteerder", "advertentiedruk",
     "P&G is top-adverteerder in NL media",
     0.75, 0.30, "Nielsen data"),
    ("Shell", "NOS", "adverteerder", "supportive_selling_environment",
     "Fossiele industrie adverteert breed, beïnvloedt redactioneel klimaat rond energietransitie",
     0.55, 0.35, "Indirect bewijs: advertentiebudgetten fossiele sector"),
    ("Shell", "RTL Nederland", "adverteerder", "advertentiedruk",
     "Shell adverteert bij commerciële omroep",
     0.60, 0.40, "Nielsen data"),

    # =======================================================================
    # SOURCING: Brede bron-afhankelijkheid
    # =======================================================================
    # ANP → ontbrekende media
    ("ANP", "De Correspondent", "beinvloeding", "pakketjournalistiek",
     "Zelfs onafhankelijke media gebruiken ANP als basismateriaal",
     0.65, 0.40, "Structureel: ANP levert aan vrijwel alle NL media [53-57]"),
    ("ANP", "Metro", "beinvloeding", "pakketjournalistiek",
     "Gratis krant Metro leunt zwaar op ANP-berichten vanwege kostendruk",
     0.85, 0.90, "CvdM onderzoek [61]"),

    # RIVM → alle grote media (coronacrisis)
    ("RIVM", "de Volkskrant", "beinvloeding", "bron_afhankelijkheid",
     "RIVM was primaire bron tijdens coronacrisis. Volkskrant nam RIVM-communicatie over",
     0.80, 0.70, "Analyse coronaberichtgeving in rapport"),
    ("RIVM", "De Telegraaf", "beinvloeding", "bron_afhankelijkheid",
     "RIVM-communicatie werd door Telegraaf overgenomen als gezaghebbend",
     0.80, 0.65, "Analyse coronaberichtgeving"),
    ("RIVM", "AD (Algemeen Dagblad)", "beinvloeding", "bron_afhankelijkheid",
     "AD nam RIVM-persberichten en data routinematig over",
     0.75, 0.65, "Structureel"),

    # OMT als bron
    ("OMT (Outbreak Management Team)", "NOS", "beinvloeding", "bron_afhankelijkheid",
     "OMT-leden domineerden als officiële experts in talkshows en NOS-berichtgeving",
     0.85, 0.80, "Rapport: OMT-leden als consensus-stemmen"),
    ("OMT (Outbreak Management Team)", "RTL Nederland", "beinvloeding", "bron_afhankelijkheid",
     "OMT-leden werden standaard opgevoerd als experts bij RTL",
     0.80, 0.75, "Rapport: talkshowdynamiek"),
    ("OMT (Outbreak Management Team)", "RIVM", "alliantie", None,
     "OMT adviseerde vanuit RIVM tijdens coronacrisis",
     0.95, 0.60, "Publiek bekend"),

    # CPB → meer media
    ("CPB (Centraal Planbureau)", "NRC", "beinvloeding", "expert_framing",
     "CPB-doorrekeningen kaderen economisch debat in NRC",
     0.80, 0.55, "Structureel: CPB als gezaghebbende bron"),
    ("CPB (Centraal Planbureau)", "RTL Nederland", "beinvloeding", "expert_framing",
     "CPB-cijfers worden door RTL Nieuws overgenomen",
     0.75, 0.50, "Structureel"),
    ("CPB (Centraal Planbureau)", "AD (Algemeen Dagblad)", "beinvloeding", "expert_framing",
     "CPB-analyses bepalen economische framing in AD",
     0.75, 0.50, "Structureel"),

    # Politie → meer media
    ("Politie", "AD (Algemeen Dagblad)", "beinvloeding", "bron_afhankelijkheid",
     "AD leunt op politiepersberichten voor misdaadnieuws",
     0.85, 0.60, "Structureel"),
    ("Politie", "de Volkskrant", "beinvloeding", "bron_afhankelijkheid",
     "Volkskrant neemt politie-persberichten over als routinebron",
     0.80, 0.50, "Structureel"),
    ("Politie", "NRC", "beinvloeding", "bron_afhankelijkheid",
     "NRC gebruikt politie als routinebron",
     0.75, 0.45, "Structureel"),

    # Ministeries → media (als officiële bronnen)
    ("Ministerie van Defensie", "NOS", "beinvloeding", "bron_afhankelijkheid",
     "Defensie levert officiële informatie over militaire zaken die NOS overneemt",
     0.80, 0.60, "Rapport: officiële bronnen domineren"),
    ("Ministerie van Defensie", "De Telegraaf", "beinvloeding", "bron_afhankelijkheid",
     "Telegraaf neemt defensie-persberichten over",
     0.75, 0.50, "Structureel"),
    ("Ministerie van Buitenlandse Zaken", "NOS", "beinvloeding", "bron_afhankelijkheid",
     "BuZa levert officiële buitenlandse politiek-informatie aan NOS",
     0.80, 0.55, "Rapport: Haagse stam [62]"),

    # Denktanks → meer media
    ("Clingendael Instituut", "RTL Nederland", "beinvloeding", "expert_framing",
     "Clingendael levert experts aan RTL voor geopolitieke duiding",
     0.70, 0.45, "Media-optredens"),
    ("Clingendael Instituut", "NRC", "beinvloeding", "expert_framing",
     "Clingendael-experts worden geciteerd in NRC",
     0.70, 0.45, "Media-optredens"),
    ("Clingendael Instituut", "AD (Algemeen Dagblad)", "beinvloeding", "expert_framing",
     "Clingendael levert experts aan AD",
     0.65, 0.40, "Media-optredens"),
    ("HCSS (The Hague Centre for Strategic Studies)", "NRC", "beinvloeding", "expert_framing",
     "HCSS levert NAVO-gezinde experts aan NRC",
     0.70, 0.45, "Media-optredens, rapport"),
    ("HCSS (The Hague Centre for Strategic Studies)", "AD (Algemeen Dagblad)", "beinvloeding", "expert_framing",
     "HCSS levert veiligheidsexperts aan AD",
     0.65, 0.40, "Media-optredens"),
    ("Nationale DenkTank", "RTL Nederland", "beinvloeding", "expert_framing",
     "NDT-rapporten worden opgepikt door RTL",
     0.55, 0.30, "Structureel"),
    ("Nationale DenkTank", "De Telegraaf", "beinvloeding", "expert_framing",
     "NDT-rapporten worden opgepikt door Telegraaf",
     0.55, 0.25, "Structureel"),

    # =======================================================================
    # FLAK: Brede disciplinering
    # =======================================================================
    # DPG Media zelfcensuur → alle titels
    ("DPG Media", "Trouw", "beinvloeding", "zelfcensuur",
     "Sociologische homogeniteit en conformisme op DPG-redacties leiden tot zelfcensuur",
     0.65, 0.60, "Rapport: 61% journalisten ervaart intimidatie [76]"),
    ("DPG Media", "AD (Algemeen Dagblad)", "beinvloeding", "zelfcensuur",
     "Zelfcensuur en conformisme op AD-redactie als onderdeel van DPG-concern",
     0.65, 0.60, "Rapport: groepsdenken op homogene redacties"),
    ("DPG Media", "Het Parool", "beinvloeding", "zelfcensuur",
     "Zelfcensuur en conformisme op Parool-redactie",
     0.60, 0.55, "Rapport: groepsdenken"),
    ("DPG Media", "NU.nl", "beinvloeding", "zelfcensuur",
     "NU.nl als DPG-platform onderhevig aan concernbrede cultuur",
     0.65, 0.60, "Rapport: concernstructuur beïnvloedt cultuur"),

    # Mediahuis zelfcensuur → titels
    ("Mediahuis", "De Telegraaf", "beinvloeding", "zelfcensuur",
     "Conformisme en groepsdenken op Telegraaf-redactie binnen Mediahuis-concern",
     0.65, 0.60, "Rapport: redactiecultuur, ongeschreven regels"),
    ("Mediahuis", "NRC", "beinvloeding", "zelfcensuur",
     "Zelfcensuur en conformisme op NRC-redactie als onderdeel Mediahuis",
     0.60, 0.55, "Rapport: sociologische homogeniteit redacties"),

    # PVV flak → meer media
    ("PVV", "AD (Algemeen Dagblad)", "censuur", "publieke_aanval",
     "PVV valt breed media aan, ondermijnt vertrouwen",
     0.70, 0.40, "Rapport [64]: politieke druk op media"),
    ("PVV", "NRC", "censuur", "publieke_aanval",
     "PVV aanvallen treffen ook kwaliteitskranten",
     0.70, 0.40, "Rapport"),

    # Tweede Kamer lidmaatschappen
    ("Pieter Omtzigt", "Tweede Kamer", "lidmaatschap", None,
     "Omtzigt was Kamerlid",
     0.95, 0.70, "Publiek bekend"),
    ("Renske Leijten", "Tweede Kamer", "lidmaatschap", None,
     "Leijten was Kamerlid",
     0.95, 0.65, "Publiek bekend"),

    # De Correspondent breder verbinden
    ("De Correspondent", "de Volkskrant", "oppositie", None,
     "De Correspondent positioneert zich als alternatief voor dagelijkse nieuwshectiek van mainstream kranten",
     0.70, 0.30, "Rapport: focus op diepgravende analyses [98, 119]"),
    ("De Correspondent", "NOS", "oppositie", None,
     "De Correspondent biedt alternatief frame t.o.v. NOS-berichtgeving",
     0.65, 0.25, "Structureel"),

    # Peter R. de Vries breder
    ("Peter R. de Vries", "de Volkskrant", "beinvloeding", "geweld_intimidatie",
     "Moord op De Vries (2021) had chilling effect op alle NL journalistiek",
     0.90, 0.50, "Rapport [64, 77]"),
    ("Peter R. de Vries", "AD (Algemeen Dagblad)", "beinvloeding", "geweld_intimidatie",
     "Moord op De Vries had chilling effect op misdaadjournalistiek",
     0.85, 0.45, "Rapport"),

    # =======================================================================
    # IDEOLOGIE: Elite-synchronisatie breed
    # =======================================================================
    # Bilderberg → meer bedrijven/entiteiten
    ("Bilderberg Groep", "Mediahuis", "beinvloeding", "ideologische_synchronisatie",
     "Via Leysen (stuurgroeplid) is Mediahuis direct verbonden met Bilderberg-netwerk",
     0.85, 0.65, "Rapport [28, 29]: Leysen lid stuurgroep"),
    ("Bilderberg Groep", "NOS", "beinvloeding", "ideologische_synchronisatie",
     "Bilderberg synchroniseert wereldbeeld elite dat doorsijpelt naar NOS via bronafhankelijkheid",
     0.60, 0.45, "Rapport: elite-consensus beïnvloedt mediaframe"),

    # WEF → meer media
    ("World Economic Forum", "de Volkskrant", "beinvloeding", "hegemonische_naturalisatie",
     "WEF-frame 'stakeholder capitalism' wordt in Volkskrant-katernen onkritisch overgenomen",
     0.55, 0.45, "Rapport [48-52]: mediaframing WEF"),
    ("World Economic Forum", "De Telegraaf", "beinvloeding", "hegemonische_naturalisatie",
     "WEF-narratief wordt als vanzelfsprekend gepresenteerd in Telegraaf economie-sectie",
     0.50, 0.40, "Rapport: inhoudsanalyse vijf kranten [104]"),
    ("World Economic Forum", "NRC", "beinvloeding", "hegemonische_naturalisatie",
     "NRC neemt WEF-frame deels over, kritiek wordt als complottheorie geframed",
     0.55, 0.45, "Rapport [104-110]"),
    ("World Economic Forum", "RTL Nederland", "beinvloeding", "hegemonische_naturalisatie",
     "RTL presenteert WEF/Davos als neutraal platform",
     0.50, 0.40, "Rapport"),

    # WEF/Bilderberg cross-connections
    ("World Economic Forum", "Bilderberg Groep", "alliantie", "ideologische_synchronisatie",
     "WEF en Bilderberg zijn beide elite-fora die TCC-consensus smeden",
     0.80, 0.55, "Rapport [34]: versterken consensus rond vrijemarktkapitalisme"),
    ("World Economic Forum", "Shell", "lidmaatschap", "ideologische_synchronisatie",
     "Shell-top is aanwezig bij WEF Davos",
     0.80, 0.30, "Deelnemerslijsten"),
    ("World Economic Forum", "ING", "lidmaatschap", "ideologische_synchronisatie",
     "ING-top is aanwezig bij WEF Davos",
     0.75, 0.25, "Deelnemerslijsten"),
    ("World Economic Forum", "Philips", "lidmaatschap", "ideologische_synchronisatie",
     "Philips-top is aanwezig bij WEF Davos",
     0.75, 0.25, "Deelnemerslijsten"),
    ("World Economic Forum", "ASML", "lidmaatschap", "ideologische_synchronisatie",
     "ASML-top is aanwezig bij WEF Davos",
     0.70, 0.20, "Deelnemerslijsten"),
    ("World Economic Forum", "Koningshuis", "lidmaatschap", "ideologische_synchronisatie",
     "Koningshuis is aanwezig bij WEF Davos",
     0.80, 0.35, "Deelnemerslijsten [35-38]"),

    # NAVO → alle grote media (Oekraïne-berichtgeving)
    ("NAVO", "De Telegraaf", "beinvloeding", "hegemonische_naturalisatie",
     "Pro-NAVO/Atlantisch frame dominant in Telegraaf Oekraïne-berichtgeving",
     0.75, 0.75, "Rapport: spectrum toegestane opinie Oekraïne"),
    ("NAVO", "de Volkskrant", "beinvloeding", "hegemonische_naturalisatie",
     "Volkskrant volgt NAVO-consensus in Oekraïne-berichtgeving. Critici worden gelabeld",
     0.75, 0.70, "Rapport: etikettering 'Poetin-versteher'"),
    ("NAVO", "NRC", "beinvloeding", "hegemonische_naturalisatie",
     "NRC volgt pro-Atlantische lijn in Oekraïne-berichtgeving",
     0.75, 0.70, "Rapport"),
    ("NAVO", "RTL Nederland", "beinvloeding", "hegemonische_naturalisatie",
     "RTL Nieuws volgt NAVO-consensus",
     0.70, 0.65, "Rapport"),
    ("NAVO", "AD (Algemeen Dagblad)", "beinvloeding", "hegemonische_naturalisatie",
     "AD volgt pro-Atlantische consensus",
     0.70, 0.60, "Rapport"),

    # NAVO → denktanks (beinvloeding, niet alleen financiering)
    ("NAVO", "HCSS (The Hague Centre for Strategic Studies)", "beinvloeding", "expert_framing",
     "NAVO-financiering stuurt HCSS-output richting NAVO-gezind narratief",
     0.75, 0.65, "Rapport: 'argumenten op bestelling' voor sponsors [71]"),
    ("NAVO", "Clingendael Instituut", "beinvloeding", "expert_framing",
     "NAVO-financiering beïnvloedt Clingendael-output",
     0.70, 0.55, "Rapport [71]"),

    # Irak-oorlog casestudie
    ("CDA", "AD (Algemeen Dagblad)", "beinvloeding", "bron_afhankelijkheid",
     "AD volgde CDA-regering in pro-Atlantische consensus Irak-oorlog",
     0.75, 0.65, "Inhoudsanalyse Bergman [95]"),
    ("CDA", "NAVO", "alliantie", None,
     "CDA-regering steunde NAVO-positie in Irak-oorlog ondanks ontbreken VN-mandaat",
     0.85, 0.70, "Rapport [95, 96]"),
    ("VVD", "NAVO", "alliantie", None,
     "VVD is traditioneel voorstander van pro-Atlantisch buitenlandbeleid",
     0.85, 0.60, "Structureel"),

    # BlackRock/Vanguard → meer bedrijven
    ("BlackRock", "ASML", "eigendom", None,
     "BlackRock is grote aandeelhouder in ASML",
     0.85, 0.20, "Aandeelhoudersregistraties [39]"),
    ("Vanguard", "ASML", "eigendom", None,
     "Vanguard is grote aandeelhouder in ASML",
     0.80, 0.15, "Aandeelhoudersregistraties"),
    ("Vanguard", "Philips", "eigendom", None,
     "Vanguard is grote aandeelhouder in Philips",
     0.80, 0.15, "Aandeelhoudersregistraties"),
    ("BlackRock", "Procter & Gamble", "eigendom", None,
     "BlackRock is grote aandeelhouder in P&G — een top-adverteerder in NL",
     0.85, 0.20, "Aandeelhoudersregistraties"),
    ("BlackRock", "Albert Heijn", "eigendom", None,
     "BlackRock belegt in Ahold Delhaize (moeder AH) — top-adverteerder NL media",
     0.80, 0.20, "Aandeelhoudersregistraties"),

    # Ron Fresen draaideur
    ("Ron Fresen", "VVD", "beinvloeding", "draaideurconstructie",
     "Fresen bewoog zich als NOS-duider in dezelfde Haagse netwerken als VVD-politici. Voorbeeld draaideur",
     0.65, 0.35, "Rapport [67]: revolving door"),
    ("Ron Fresen", "CDA", "beinvloeding", "draaideurconstructie",
     "Fresen was onderdeel van Haagse stam waar CDA-politici ook in opereren",
     0.60, 0.30, "Rapport: Haagse stam [62]"),

    # UvA als kritische plek
    ("UvA Journalistiek", "NOS", "beinvloeding", None,
     "UvA leidt journalisten op met kritische reflectie, levert personeel aan NOS",
     0.70, 0.25, "Rapport [114, 115]"),
    ("UvA Journalistiek", "de Volkskrant", "beinvloeding", None,
     "UvA-opgeleide journalisten komen bij Volkskrant terecht",
     0.65, 0.20, "Structureel"),

    # Gezond Verstand als reactie op hegemonische naturalisatie
    ("Gezond Verstand", "NOS", "oppositie", "hegemonische_naturalisatie",
     "Gezond Verstand zet zich af tegen NOS-consensus. Toont dat hegemonie niet totaal is, maar reactie vaak feitelijk onjuist",
     0.70, 0.25, "Rapport [93, 94]"),
    ("Gezond Verstand", "de Volkskrant", "oppositie", None,
     "Alternatief medium dat zich afzet tegen mainstream consensus van kwaliteitskranten",
     0.65, 0.20, "Rapport"),

    # Techplatforms → individuele titels
    ("Google", "de Volkskrant", "beinvloeding", "algoritmische_filtering",
     "Volkskrant afhankelijk van Google voor online bereik",
     0.80, 0.65, "WRR/CvdM rapporten"),
    ("Google", "De Telegraaf", "beinvloeding", "algoritmische_filtering",
     "Telegraaf afhankelijk van Google voor online bereik en advertentie-inkomsten",
     0.80, 0.70, "WRR/CvdM rapporten"),
    ("Google", "NRC", "beinvloeding", "algoritmische_filtering",
     "NRC afhankelijk van Google voor digitale distributie",
     0.75, 0.60, "WRR/CvdM rapporten"),
    ("Google", "RTL Nederland", "beinvloeding", "algoritmische_filtering",
     "RTL content afhankelijk van Google-algoritmes",
     0.80, 0.65, "WRR/CvdM rapporten"),
    ("Meta (Facebook/Instagram)", "de Volkskrant", "beinvloeding", "algoritmische_filtering",
     "Volkskrant distribueert via Facebook/Instagram, onderhevig aan algoritmes",
     0.75, 0.60, "WRR rapport"),
    ("Meta (Facebook/Instagram)", "De Telegraaf", "beinvloeding", "algoritmische_filtering",
     "Telegraaf afhankelijk van Meta voor distributie",
     0.80, 0.65, "WRR rapport"),
    ("Meta (Facebook/Instagram)", "AD (Algemeen Dagblad)", "beinvloeding", "algoritmische_filtering",
     "AD afhankelijk van social media voor bereik",
     0.75, 0.60, "WRR rapport"),
    ("Meta (Facebook/Instagram)", "NU.nl", "beinvloeding", "algoritmische_filtering",
     "NU.nl als gratis platform extra afhankelijk van social media distributie",
     0.80, 0.70, "WRR rapport"),
    ("TikTok", "de Volkskrant", "beinvloeding", "algoritmische_filtering",
     "Jongeren bereiken Volkskrant steeds meer via TikTok",
     0.60, 0.45, "CvdM Digital News Reports"),
    ("TikTok", "De Telegraaf", "beinvloeding", "algoritmische_filtering",
     "Jongeren bereiken Telegraaf content via TikTok",
     0.60, 0.45, "CvdM Digital News Reports"),
    ("TikTok", "AD (Algemeen Dagblad)", "beinvloeding", "algoritmische_filtering",
     "Jongeren bereiken AD content via TikTok",
     0.55, 0.40, "CvdM Digital News Reports"),
    ("TikTok", "NU.nl", "beinvloeding", "algoritmische_filtering",
     "Jongeren bereiken NU.nl steeds meer via TikTok",
     0.65, 0.55, "CvdM Digital News Reports"),

    # NVJ en Free Press Unlimited breder
    ("NVJ (Nederlandse Vereniging van Journalisten)", "Mediahuis", "beinvloeding", None,
     "NVJ behartigt belangen journalisten bij Mediahuis-titels",
     0.80, 0.20, "Structureel"),
    ("NVJ (Nederlandse Vereniging van Journalisten)", "RTL Nederland", "beinvloeding", None,
     "NVJ behartigt belangen journalisten bij RTL",
     0.80, 0.20, "Structureel"),
    ("Free Press Unlimited", "DPG Media", "beinvloeding", None,
     "Free Press Unlimited pleit voor persvrijheid bij grote mediabedrijven",
     0.75, 0.15, "Structureel [120, 121]"),
    ("Free Press Unlimited", "Mediahuis", "beinvloeding", None,
     "Free Press Unlimited pleit voor persvrijheid bij Mediahuis",
     0.75, 0.15, "Structureel"),

    # Koningshuis → breder
    ("Koningshuis", "NOS", "beinvloeding", "bron_afhankelijkheid",
     "Koningshuis is officiële bron voor NOS. RVD (Rijksvoorlichtingsdienst) bepaalt framing",
     0.85, 0.45, "Structureel"),
    ("Koningshuis", "World Economic Forum", "lidmaatschap", "ideologische_synchronisatie",
     "Koningshuis is aanwezig bij WEF Davos en Bilderberg",
     0.80, 0.35, "Deelnemerslijsten [35-38]"),

    # Maarten van Rossem breder
    ("Maarten van Rossem", "de Volkskrant", "beinvloeding", None,
     "Van Rossem is columnist/commentator. Voorbeeld van expert die na afwijkende mening werd geweerd",
     0.70, 0.35, "Rapport: deplatforming na Irak-kritiek"),
    ("Maarten van Rossem", "RTL Nederland", "beinvloeding", None,
     "Van Rossem treedt op als commentator bij RTL",
     0.65, 0.30, "Publiek waarneembaar"),

    # Chris Oomen breder
    ("Chris Oomen", "NOS", "beinvloeding", None,
     "Oomen als eigenaar ANP beïnvloedt indirect alle NOS-berichtgeving via persbureau",
     0.70, 0.35, "Rapport [54, 59, 60]"),

    # John de Mol → breder
    ("John de Mol", "RTL Nederland", "beinvloeding", None,
     "De Mol was via Talpa verbonden met NL medialandschap. Voormalig eigenaar ANP",
     0.70, 0.30, "Rapport [58]"),

    # ACM → toezicht breder
    ("ACM (Autoriteit Consument & Markt)", "RTL Nederland", "beinvloeding", None,
     "ACM stelde strenge voorwaarden aan DPG-overname RTL: stichtingen met vetorecht",
     0.95, 0.60, "ACM-besluit [16]"),
    ("ACM (Autoriteit Consument & Markt)", "NU.nl", "beinvloeding", None,
     "ACM richtte onafhankelijke stichting op voor NU.nl na DPG/RTL-overname",
     0.95, 0.55, "ACM-besluit [16]"),

    # ASML/ING/Philips → DPG/Mediahuis (indirect via elite-netwerken)
    ("ASML", "Bilderberg Groep", "lidmaatschap", None,
     "ASML-top aanwezig bij Bilderberg — dezelfde fora als media-eigenaren",
     0.75, 0.20, "Deelnemerslijsten"),
    ("ING", "Bilderberg Groep", "lidmaatschap", None,
     "ING-top aanwezig bij Bilderberg",
     0.80, 0.25, "Deelnemerslijsten"),
    ("Shell", "Bilderberg Groep", "lidmaatschap", None,
     "Shell-top aanwezig bij Bilderberg",
     0.85, 0.30, "Deelnemerslijsten"),
    ("Philips", "Bilderberg Groep", "lidmaatschap", None,
     "Philips-top aanwezig bij Bilderberg",
     0.80, 0.25, "Deelnemerslijsten"),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Haal source_id op
    cur.execute("SELECT id FROM sources WHERE title = ?", (SOURCE_TITLE,))
    row = cur.fetchone()
    source_id = row[0] if row else None

    # Lookups
    cur.execute("SELECT id, name FROM roles")
    role_map = {name: rid for rid, name in cur.fetchall()}

    cur.execute("SELECT id, name FROM mechanisms")
    mech_map = {name: mid for mid, name in cur.fetchall()}

    # 1. Insert entiteiten
    entity_count = 0
    for name, etype, role_name, desc, metadata in NEW_ENTITIES:
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
                cur.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id) VALUES (?, ?)", (eid, role_id))
            if source_id:
                cur.execute("INSERT OR IGNORE INTO source_mentions (source_id, entity_id) VALUES (?, ?)", (source_id, eid))
    conn.commit()

    # 2. Entity lookup
    cur.execute("SELECT id, name FROM entities")
    entity_map = {name: eid for eid, name in cur.fetchall()}

    # 3. Insert relaties
    relation_count = 0
    skipped = 0
    for (src_name, tgt_name, rel_type, mech_name, desc,
         certainty, influence, evidence) in NEW_RELATIONS:
        src_id = entity_map.get(src_name)
        tgt_id = entity_map.get(tgt_name)
        mech_id = mech_map.get(mech_name) if mech_name else None

        if not src_id:
            print(f"  WARN: bron '{src_name}' niet gevonden, skip")
            skipped += 1
            continue
        if not tgt_id:
            print(f"  WARN: doel '{tgt_name}' niet gevonden, skip")
            skipped += 1
            continue

        # Check duplicaat
        cur.execute(
            "SELECT id FROM relations WHERE source_id=? AND target_id=? AND relation_type=?",
            (src_id, tgt_id, rel_type))
        if cur.fetchone():
            continue

        cur.execute(
            """INSERT INTO relations
               (source_id, target_id, relation_type, mechanism_id,
                description, certainty, influence, bidirectional)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
            (src_id, tgt_id, rel_type, mech_id, desc, certainty, influence))
        relation_count += 1
        rel_id = cur.lastrowid

        # Argument + citatie
        if source_id:
            cur.execute(
                """INSERT INTO arguments (relation_id, stance, claim, reasoning, weight)
                   VALUES (?, 'supporting', ?, ?, ?)""",
                (rel_id, desc, f"Bewijs: {evidence}", certainty))
            arg_id = cur.lastrowid
            cur.execute(
                """INSERT INTO citations (argument_id, source_id, context)
                   VALUES (?, ?, ?)""",
                (arg_id, source_id, evidence))

    conn.commit()

    # Stats
    cur.execute("SELECT COUNT(*) FROM entities")
    total_e = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM relations")
    total_r = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM arguments")
    total_a = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM citations")
    total_c = cur.fetchone()[0]
    cur.execute("""SELECT COUNT(*) FROM entities e
        WHERE e.id NOT IN (SELECT source_id FROM relations)
        AND e.id NOT IN (SELECT target_id FROM relations)""")
    orphans = cur.fetchone()[0]

    conn.close()

    print(f"\n{'='*60}")
    print(f"Grondige verrijking voltooid")
    print(f"{'='*60}")
    print(f"Nieuwe entiteiten:      {entity_count}")
    print(f"Nieuwe relaties:        {relation_count}")
    print(f"Overgeslagen:           {skipped}")
    print(f"{'='*60}")
    print(f"TOTALEN:")
    print(f"  Entiteiten:           {total_e}")
    print(f"  Relaties:             {total_r}")
    print(f"  Argumenten:           {total_a}")
    print(f"  Citaties:             {total_c}")
    print(f"  Wees-entiteiten:      {orphans}")
    print(f"{'='*60}")


if __name__ == "__main__":
    seed()
