"""
Verrijk het theoretische model (rollen + mechanismen) op basis van de AI-bronanalyse.

Voegt toe:
- Nieuwe rollen die in het rapport worden beschreven maar ontbreken
- Nieuwe mechanismen (verbindingen tussen rollen)
- Ontbrekende verbindingen tussen bestaande rollen
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"


# =============================================================================
# NIEUWE ROLLEN
# =============================================================================
NEW_ROLES = [
    # (name, category, description, examples)

    # Sourcing
    ("lobbyist", "sourcing",
     "Professionele belangenbehartiger die politici en journalisten van informatie voorziet. "
     "Parlementsleden leunen op door lobbyisten aangeleverde info voor Kamervragen (Luyendijk)",
     "Branche-organisaties, corporate lobbyisten in Den Haag, public affairs bureaus"),

    # Flak
    ("alternatief_medium", "flak",
     "Medium buiten de mainstream dat de hegemonie uitdaagt. Reactie op ervaren tekortkomingen "
     "van gevestigde media. Variëert van kwaliteitsjournalistiek tot desinformatie",
     "De Correspondent (kwaliteit), Gezond Verstand (complottheorieën), Follow the Money, onafhankelijke podcasts"),

    # Ideologie
    ("academisch_criticus", "ideologie",
     "Academicus die de structurele filters blootlegt en het systeem analyseert. "
     "Wordt vaak gemarginaliseerd of genegeerd door mainstream media en gevestigde mediawetenschap",
     "Willem Schinkel"),

    ("parlementair_controleur", "overig",
     "Volksvertegenwoordiger die de macht controleert en structurele misstanden blootlegt. "
     "Kan de filters doorbreken maar vereist uitzonderlijke inspanning over lange periode",
     "Pieter Omtzigt, Renske Leijten (SP), parlementaire enquêtecommissies"),

    # Overig
    ("overnamevehikel", "eigendom",
     "Juridische constructie (holding, investeringsvehikel) waarmee families eigendom "
     "over mediaconglomeraten uitoefenen op afstand van de redactie",
     "Epifin (Van Thillo/DPG), Mediahuis Partners (Leysen), VP Exploitatie (Van Puijenbroek), Concentra (Baert)"),

    ("vakbond_media", "overig",
     "Beroepsvereniging of vakbond die opkomt voor journalistieke belangen en persvrijheid. "
     "Focus vaak meer op symptomen (geweld, intimidatie) dan op dieperliggende structuren",
     "NVJ, Free Press Unlimited, internationale persvrijheidsorganisaties"),
]


# =============================================================================
# NIEUWE MECHANISMEN
# =============================================================================
NEW_MECHANISMS = [
    # (name, filter, description, effect, source_role_name, target_role_name)

    # ---- EIGENDOM ----
    ("cross_media_eigendom", "eigendom",
     "Eén conglomeraat bezit kranten, online platforms én televisie. DPG bezit na RTL-overname "
     "print, online en TV. Vermindert pluriformiteit op eigenaarsniveau drastisch",
     "Controle over meerdere mediakanalen door dezelfde eigenaar. "
     "Minder concurrerende perspectieven, uniforme bedrijfscultuur over titels heen",
     "mediaeigenaar", "mediaorganisatie"),

    ("acquisitiestrategie", "eigendom",
     "Decennia van overnames en fusies concentreren eigendom: DPG nam PCM, VNU, Sanoma, RTL over; "
     "Mediahuis nam TMG en NRC Media over. Wordt gerechtvaardigd als 'noodzakelijk voor digitaal tijdperk'",
     "Drastische vermindering pluriformiteit. Controle informatievoorziening bij kleine groep",
     "mediaeigenaar", "mediaorganisatie"),

    ("holdingconstructie", "eigendom",
     "Eigendom wordt uitgeoefend via tussenvehikels (Epifin, Mediahuis Partners, VP Exploitatie) "
     "die afstand creëren tussen familie en redactie maar controle behouden",
     "Schijn van onafhankelijkheid terwijl eigendomsmacht intact blijft. Redactiestatuten bieden geen ijzerharde garanties",
     "overnamevehikel", "mediaorganisatie"),

    ("systemisch_eigenaarschap", "eigendom",
     "Institutionele beleggers (BlackRock, Vanguard) bezitten via stemrecht de facto alle "
     "beursgenoteerde bedrijven. Inherent belang bij stabiel kapitalistisch systeem",
     "Passieve maar systemische druk richting status quo. Het hele economische ecosysteem "
     "waarin media opereren wordt gedomineerd door financieel kapitaal",
     "institutioneel_belegger", "mediaeigenaar"),

    # ---- ADVERTENTIE ----
    ("stakeholder_capitalism_frame", "advertentie",
     "WEF propageert 'stakeholder capitalism' als ideologisch verdedigingsmechanisme. "
     "Media nemen dit frame onkritisch over in economie- en duurzaamheidskaternen",
     "Neutraliseert systeemkritiek door kapitalisme zelf als oplossing te presenteren. "
     "ESG-metrics dienen meer ter legitimatie dan controle. Greenwashing wordt genormaliseerd",
     "adverteerder", "mediaorganisatie"),

    # ---- SOURCING ----
    ("haagse_stam", "sourcing",
     "Politici, voorlichters, lobbyisten en journalisten in Den Haag functioneren als 'één stam' (Luyendijk). "
     "Gedeelde ruimte, jargon, ongeschreven regels en diepe onderlinge afhankelijkheid",
     "Cultuur van terughoudendheid en zelfcensuur. Fundamentele kritiek leidt tot uitsluiting. "
     "Parlementaire verslaggeving volgt agenda machthebbers. NL politieke cultuur een van meest gesloten in Westen",
     "officiele_bron", "mediaorganisatie"),

    ("lobby_informatievoorziening", "sourcing",
     "Lobbyisten leveren kant-en-klare informatie aan parlementsleden voor Kamervragen. "
     "Journalisten zijn afhankelijk van deze informatieketen",
     "Bedrijfsbelangen worden via lobbycircuit in parlementaire vragen en media-agenda ingebracht "
     "zonder dat de oorsprong zichtbaar is",
     "lobbyist", "officiele_bron"),

    ("denktank_legitimatie", "sourcing",
     "Denktanks presenteren door sponsors gefinancierd onderzoek als objectieve, wetenschappelijke analyse. "
     "Ze produceren effectief 'argumenten op bestelling' voor corporate sponsors",
     "Beleid dat belangen van financiers dient krijgt aureool van wetenschappelijke legitimiteit. "
     "NAVO-gezinde denktanks worden als 'neutrale' experts opgevoerd",
     "expert_bron", "ideoloog"),

    # ---- FLAK ----
    ("onevenwichtig_debat", "flak",
     "Talkshowdynamiek: enkele criticus aan tafel tegenover overmacht consensus-stemmen. "
     "Criticus staat letterlijk en figuurlijk alleen tegen verenigd front",
     "Criticus overkomt als onredelijk en geïsoleerd. Schijn van open debat "
     "terwijl de critische positie structureel wordt verzwakt",
     "gatekeeper", "flak_doelwit"),

    ("morele_chantage", "flak",
     "Critici worden in het kamp van de vijand geplaatst: 'Poetin-versteher', 'Kremlin-propagandist'. "
     "Geen inhoudelijke weerlegging maar morele diskwalificatie",
     "Fundamentele vragen over proportionaliteit en context worden onmogelijk. "
     "Bronselectie beperkt zich tot consensus-bevestigende experts",
     "gatekeeper", "flak_doelwit"),

    ("woo_obstructie", "flak",
     "Overheid handelt Woo-verzoeken (FOIA) traag en onwillig af. "
     "Tegelijkertijd krijgen opsporingsdiensten ruimere afluisterbevoegdheden",
     "Diepgravend onderzoek wordt gefrustreerd. Bescherming journalistieke bronnen onder druk. "
     "Asymmetrische informatietoegang: overheid weet meer over journalisten dan andersom",
     "officiele_bron", "flak_doelwit"),

    ("chilling_effect_geweld", "flak",
     "Fysiek geweld tegen journalisten (moord Peter R. de Vries, bedreigingen, doxing) "
     "creëert angstcultuur die hele beroepsgroep beïnvloedt. 61% NL journalisten ervaart intimidatie",
     "Misdaadjournalistiek en kritische verslaggeving worden risicovoller. "
     "Hele redacties worden risicomijdender, niet alleen individuele slachtoffers",
     "flak_producent", "mediaorganisatie"),

    ("alternatieve_uitdaging", "flak",
     "Alternatieve media dagen mainstream consensus uit. Appelleren aan groeiend wantrouwen "
     "bij publiek dat voelt dat 'gezond verstand' van media niet strookt met eigen ervaring",
     "Toont dat hegemonie niet totaal is. Maar inhoud vaak feitelijk onjuist, "
     "waardoor legitieme kritiek besmet raakt door associatie met extremen",
     "alternatief_medium", "mediaorganisatie"),

    # ---- IDEOLOGIE ----
    ("spectrum_bewaking", "ideologie",
     "Chomsky's 'spectrum van toegestane opinie': levendig debat over details wordt aangemoedigd, "
     "maar fundamentele premissen blijven buiten schot. Discussie over wápens voor Oekraïne, "
     "niet over de premisse van militaire steun zelf",
     "Illusie van vrije, open pers terwijl fundamentele, door elite gedefinieerde consensus overeind blijft. "
     "Wie buiten het spectrum treedt wordt gemarginaliseerd",
     "gatekeeper", "burger"),

    ("systemische_homeostase", "ideologie",
     "Het systeem heeft sterke neiging terug te keren naar evenwicht dat elite-belangen dient. "
     "Filters kunnen doorbroken worden maar vereisen uitzonderlijke inspanning "
     "van coalitie van actoren over zeer lange periode",
     "Default setting is volgen elite-consensus. Enorme hoeveelheid tegenbewijs en "
     "maatschappelijke druk nodig om narratief duurzaam te veranderen",
     "mediaorganisatie", "burger"),

    ("emergente_bias", "ideologie",
     "Pro-elite bias is geen georkestreerd plan maar emergent, zelforganiserend gevolg van systeem "
     "ontworpen rond winstmaximalisatie en risicovermijding. Duizenden dagelijkse beslissingen "
     "op basis van dezelfde prikkels produceren uniform nieuwsproduct",
     "Journalist kiest invalshoek niet op bevel eigenaar maar omdat hij weet dat chef het goed vindt, "
     "het online scoort en geen problemen oplevert. De 'black box' is geen controlekamer maar zelforganiserend systeem",
     "mediaorganisatie", "burger"),

    ("academische_blootlegging", "ideologie",
     "Kritische academici leggen structurele filters bloot. Hun werk wordt echter grotendeels genegeerd "
     "door gevestigde mediawetenschap en reguliere media. De hegemonie beschermt zichzelf",
     "Structurele kritiek bereikt zelden het publiek. Discussie blijft steken bij incidenten, "
     "zonder onderliggende systemische oorzaken te benoemen",
     "academisch_criticus", "mediaorganisatie"),

    ("parlementaire_doorbraak", "overig",
     "Parlementaire controle kan filters doorbreken. "
     "Vereist coalitie van journalisten, politici, burgers en advocaten over lange periode",
     "Narratieve verschuiving mogelijk: van 'fraude' naar 'onrecht'. Maar het systeem is niet monolithisch, "
     "het bezit slechts een sterke homeostase",
     "parlementair_controleur", "officiele_bron"),

    # ---- OVERIG ----
    ("platform_advertentie_concentratie", "overig",
     "Techplatforms absorberen het grootste deel van online advertentie-inkomsten. "
     "Traditionele media verliezen verdienmodel en worden afhankelijker van platforms",
     "Dubbele afhankelijkheid: media hebben platforms nodig voor bereik én advertentie-inkomsten. "
     "Platforms worden de nieuwe adverteerder-gatekeepers",
     "techplatform", "mediaverkoper"),

    ("algoritmische_socialisatie", "overig",
     "Jongeren worden gesocialiseerd in algoritmisch i.p.v. journalistiek ecosysteem. "
     "TikTok, Instagram, YouTube zijn primaire nieuwsbron, niet traditionele media",
     "Fundamenteel andere informatie-omgeving. Minder contact met nieuwsmerken. "
     "Engagement-logica vervangt journalistieke waarden bij nieuwe generatie",
     "techplatform", "burger"),

    ("toezicht_tandeloosheid", "overig",
     "Toezichthouders (ACM, CvdM, RvJ) signaleren problemen maar kunnen vaak niet effectief ingrijpen. "
     "RvJ kan geen sancties opleggen. Redactiestatuten bieden geen ijzerharde garanties",
     "Formele beschermingsmechanismen zijn onvoldoende robuust. "
     "ACM DPG/RTL-voorwaarden zijn uitzondering die de regel bevestigt",
     "toezichthouder", "mediaeigenaar"),

    ("klokkenluider_doorbraak", "overig",
     "Whistleblowers en onderzoeksjournalisten kunnen het systeem blootleggen, "
     "maar betalen hoge persoonlijke prijs (reputatie, veiligheid, carrière)",
     "Essentiële correctiefunctie op het systeem. Maar het systeem reageert met flak: "
     "juridische dreiging, deplatforming, etikettering",
     "klokkenluider", "mediaorganisatie"),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Insert rollen
    role_count = 0
    for name, category, description, examples in NEW_ROLES:
        cur.execute(
            "INSERT OR IGNORE INTO roles (name, category, description, examples) VALUES (?, ?, ?, ?)",
            (name, category, description, examples))
        if cur.rowcount > 0:
            role_count += 1
    conn.commit()

    # 2. Build role lookup
    cur.execute("SELECT id, name FROM roles")
    role_map = {name: rid for rid, name in cur.fetchall()}

    # 3. Insert mechanismen
    mech_count = 0
    for name, filt, desc, effect, src_role, tgt_role in NEW_MECHANISMS:
        src_id = role_map.get(src_role)
        tgt_id = role_map.get(tgt_role)
        if not src_id:
            print(f"  WARN: bronrol '{src_role}' niet gevonden")
            continue
        if not tgt_id:
            print(f"  WARN: doelrol '{tgt_role}' niet gevonden")
            continue

        cur.execute(
            """INSERT OR IGNORE INTO mechanisms
               (name, filter, description, effect, source_role_id, target_role_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, filt, desc, effect, src_id, tgt_id))
        if cur.rowcount > 0:
            mech_count += 1
    conn.commit()

    # Stats
    cur.execute("SELECT COUNT(*) FROM roles")
    total_roles = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM mechanisms")
    total_mechs = cur.fetchone()[0]

    conn.close()

    print(f"\n{'='*60}")
    print(f"Theoretisch model verrijkt")
    print(f"{'='*60}")
    print(f"Nieuwe rollen:          {role_count}")
    print(f"Nieuwe mechanismen:     {mech_count}")
    print(f"{'='*60}")
    print(f"TOTALEN:")
    print(f"  Rollen:               {total_roles}")
    print(f"  Mechanismen:          {total_mechs}")
    print(f"{'='*60}")


if __name__ == "__main__":
    seed()
