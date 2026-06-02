"""
Verrijk de database met ontbrekende entiteiten en relaties uit de AI-bronnen.

Voegt toe:
- Entiteiten die in sources/AI/propagandsmodel2.md worden genoemd maar ontbreken
- Relaties voor wees-entiteiten (geen connecties) en onderverbonden entiteiten
- Diepere verbindingen gebaseerd op het bronmateriaal
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"
SOURCE_TITLE = "De Onzichtbare Architecten: Een Analyse van het Propagandamodel in het Nederlandse Medialandschap"


# =============================================================================
# NIEUWE ENTITEITEN (genoemd in bron maar ontbreken)
# =============================================================================
NEW_ENTITIES = [
    # (name, type, primary_role_name, description, metadata_json)

    # Overheidsinstanties als officiële bronnen
    ("RIVM", "overheidsinstelling", "officiele_bron",
     "Rijksinstituut voor Volksgezondheid en Milieu. Sleutelrol tijdens coronacrisis als officiële informatiebron. Framing van pandemiebeleid.",
     None),
    ("CPB (Centraal Planbureau)", "overheidsinstelling", "expert_bron",
     "Centraal Planbureau. Levert economische analyses die het debat kaderen. Doorrekeningen verkiezingsprogramma's bepalen politiek discourse.",
     None),
    ("Politie", "overheidsinstelling", "officiele_bron",
     "Routineuze bron voor criminaliteitsnieuws. Persvoorlichting bepaalt framing van veiligheidsvraagstukken.",
     None),
    ("Ministerie van Defensie", "overheidsinstelling", "officiele_bron",
     "Officiële bron voor defensie- en veiligheidsnieuws. Financiert denktanks als HCSS en Clingendael.",
     None),
    ("Ministerie van Buitenlandse Zaken", "overheidsinstelling", "officiele_bron",
     "Officiële bron voor buitenlandbeleid. Financiert Clingendael Instituut.",
     None),

    # Media die in de bron worden genoemd
    ("Brandpunt", "mediaorganisatie", "mediaorganisatie",
     "KRO-NCRV TV-programma.",
     None),
    ("RTL Nieuws", "mediaorganisatie", "mediaorganisatie",
     "Nieuwsredactie van RTL Nederland. Onderdeel RTL Nederland.",
     None),
    ("De Morgen", "mediaorganisatie", "mediaorganisatie",
     "Belgische krant, eigendom DPG Media. Van Thillo beïnvloedde redactionele cultuur na overname.",
     '{"land": "BE"}'),
    ("Gezond Verstand", "mediaorganisatie", "mediaorganisatie",
     "Alternatief tijdschrift dat zich afzet tegen mainstream consensus. Voorbeeld van reactie op hegemonische naturalisatie.",
     '{"type": "alternatief"}'),

    # Nog ontbrekende actoren
    ("Mediahuis Partners", "bedrijf", "aandeelhouder",
     "Holding gecontroleerd door familie Thomas Leysen. Belangrijkste aandeelhouder Mediahuis.",
     None),
    ("NSC (Nieuw Sociaal Contract)", "partij", "ideoloog",
     "Politieke partij opgericht door Pieter Omtzigt na vertrek uit CDA.",
     None),
    ("Adidas", "bedrijf", "aandeelhouder",
     "Sportmerk. Belang van Groupe Bruxelles Lambert illustreert breedte corporate netwerk Van Thillo.",
     None),
]


# =============================================================================
# NIEUWE RELATIES
# =============================================================================
NEW_RELATIONS = [
    # (source, target, type, mechanism, desc, certainty, influence, bidir)

    # =========================================================================
    # ONTBREKENDE ADVERTEERDER-RELATIES (orphans verbinden)
    # =========================================================================
    ("Bol.com", "DPG Media", "adverteerder", "advertentiedruk",
     "Grootste webwinkel NL, top-adverteerder in Nederlandse media",
     0.80, 0.35, False),
    ("Bol.com", "Mediahuis", "adverteerder", "advertentiedruk",
     "Top-adverteerder NL, adverteert ook in Mediahuis-titels",
     0.75, 0.30, False),
    ("A.S. Watson (Kruidvat)", "DPG Media", "adverteerder", "advertentiedruk",
     "Retailconcern (Kruidvat, Trekpleister), top-adverteerder NL",
     0.80, 0.35, False),
    ("A.S. Watson (Kruidvat)", "Mediahuis", "adverteerder", "advertentiedruk",
     "Retailconcern, adverteert breed in NL media",
     0.75, 0.30, False),
    ("Postcode Loterij", "DPG Media", "adverteerder", "advertentiedruk",
     "Grote loterij, top-adverteerder in NL media",
     0.75, 0.35, False),
    ("Postcode Loterij", "Mediahuis", "adverteerder", "advertentiedruk",
     "Grote loterij, adverteert ook in Mediahuis-titels",
     0.70, 0.30, False),
    ("Unibet", "Mediahuis", "adverteerder", "advertentiedruk",
     "Online gokbedrijf, adverteert ook in Mediahuis-titels",
     0.65, 0.25, False),

    # Supportive selling environment (structureel, niet individueel)
    ("Albert Heijn", "NOS", "adverteerder", "supportive_selling_environment",
     "NOS programma-sponsoring door retailers creëert afhankelijkheid",
     0.65, 0.25, False),
    ("Unilever", "RTL Nederland", "adverteerder", "advertentiedruk",
     "FMCG-multinational, grote adverteerder bij commerciële omroep",
     0.80, 0.45, False),
    ("Procter & Gamble", "RTL Nederland", "adverteerder", "advertentiedruk",
     "FMCG-multinational, grote adverteerder bij commerciële omroep",
     0.80, 0.45, False),
    ("Shell", "Mediahuis", "adverteerder", "advertentiedruk",
     "Fossiele industrie adverteert breed in NL media",
     0.55, 0.40, False),

    # =========================================================================
    # TOEZICHTHOUDERS VERBINDEN (orphans)
    # =========================================================================
    ("CvdM (Commissariaat voor de Media)", "DPG Media", "beinvloeding", None,
     "CvdM houdt toezicht op mediaconcentratie en signaleert risico's voor pluriformiteit",
     0.85, 0.35, False),
    ("CvdM (Commissariaat voor de Media)", "Mediahuis", "beinvloeding", None,
     "CvdM houdt toezicht op mediaconcentratie",
     0.85, 0.35, False),
    ("CvdM (Commissariaat voor de Media)", "NOS", "beinvloeding", None,
     "CvdM houdt toezicht op publieke omroep",
     0.90, 0.40, False),
    ("WRR (Wetenschappelijke Raad voor het Regeringsbeleid)", "NOS", "beinvloeding", None,
     "WRR-rapport 'Aandacht voor media' (2024) signaleert dat democratische functies onder druk staan",
     0.80, 0.30, False),
    ("WRR (Wetenschappelijke Raad voor het Regeringsbeleid)", "DPG Media", "beinvloeding", None,
     "WRR pleit voor herziening mediabeleid. Erkent structurele problemen die kern vormen van propagandamodel",
     0.80, 0.25, False),
    ("Raad voor de Journalistiek", "NOS", "beinvloeding", None,
     "Zelfregulering journalistiek. Kan geen bindende sancties opleggen, beperkte morele autoriteit",
     0.85, 0.20, False),
    ("Raad voor de Journalistiek", "DPG Media", "beinvloeding", None,
     "Raad oordeelt over klachten tegen DPG-titels maar kan geen sancties opleggen",
     0.85, 0.15, False),
    ("ACM (Autoriteit Consument & Markt)", "Mediahuis", "beinvloeding", None,
     "ACM houdt toezicht op mededinging in mediamarkt",
     0.85, 0.40, False),

    # =========================================================================
    # POLITIEKE PARTIJEN VERBINDEN
    # =========================================================================
    ("SP", "Renske Leijten", "lidmaatschap", None,
     "Leijten is SP-Kamerlid",
     0.95, 0.50, False),
    ("CDA", "Pieter Omtzigt", "lidmaatschap", None,
     "Omtzigt was CDA-Kamerlid. Later vertrokken naar NSC",
     0.95, 0.60, False),
    ("PVV", "De Telegraaf", "alliantie", None,
     "PVV en Telegraaf delen regelmatig framing op immigratie en veiligheid",
     0.65, 0.45, False),
    ("PVV", "de Volkskrant", "censuur", "publieke_aanval",
     "PVV valt regelmatig 'linkse' media aan, ondermijnt vertrouwen",
     0.80, 0.50, False),
    ("VVD", "DPG Media", "beinvloeding", "bron_afhankelijkheid",
     "VVD als langdurige regeringspartij is routineuze officiële bron voor media",
     0.75, 0.50, False),
    ("VVD", "NOS", "beinvloeding", "bron_afhankelijkheid",
     "VVD als dominante regeringspartij bepaalt Haags nieuwsaanbod",
     0.80, 0.55, False),

    # NSC afsplitsing
    ("NSC (Nieuw Sociaal Contract)", "Pieter Omtzigt", "lidmaatschap", None,
     "Omtzigt richtte NSC op na vertrek uit CDA",
     0.95, 0.70, False),

    # =========================================================================
    # ACADEMICI / CRITICI VERBINDEN (orphans)
    # =========================================================================
    ("Willem Schinkel", "NOS", "oppositie", None,
     "Schinkel levert brede maatschappijkritiek waarin de rol van media wordt meegenomen",
     0.70, 0.25, False),
    ("NVJ (Nederlandse Vereniging van Journalisten)", "DPG Media", "beinvloeding", None,
     "NVJ pleit voor persvrijheid en bescherming journalisten bij grote mediabedrijven",
     0.80, 0.25, False),
    ("NVJ (Nederlandse Vereniging van Journalisten)", "NOS", "alliantie", None,
     "NVJ behartigt belangen van NOS-journalisten",
     0.85, 0.20, False),
    ("Free Press Unlimited", "NOS", "alliantie", None,
     "Free Press Unlimited pleit voor persvrijheid en onafhankelijke journalistiek",
     0.80, 0.20, False),

    # =========================================================================
    # SOURCING-RELATIES (officiële bronnen → media)
    # =========================================================================
    ("RIVM", "NOS", "beinvloeding", "bron_afhankelijkheid",
     "RIVM was primaire officiële bron tijdens coronacrisis. Frame werd vrijwel onkritisch overgenomen",
     0.85, 0.80, False),
    ("RIVM", "RTL Nederland", "beinvloeding", "bron_afhankelijkheid",
     "RTL nam RIVM-persconferenties en communicatie over als primaire bron",
     0.85, 0.75, False),
    ("RIVM", "DPG Media", "beinvloeding", "bron_afhankelijkheid",
     "DPG-titels namen RIVM-communicatie over als gezaghebbende bron",
     0.80, 0.70, False),
    ("CPB (Centraal Planbureau)", "NOS", "beinvloeding", "expert_framing",
     "CPB-doorrekeningen kaderen economisch debat. Worden als neutrale feiten gepresenteerd",
     0.85, 0.65, False),
    ("CPB (Centraal Planbureau)", "de Volkskrant", "beinvloeding", "expert_framing",
     "CPB-analyses bepalen economische framing in kwaliteitskranten",
     0.80, 0.60, False),
    ("CPB (Centraal Planbureau)", "De Telegraaf", "beinvloeding", "expert_framing",
     "CPB-cijfers worden overgenomen, economisch frame bepaalt debat",
     0.80, 0.55, False),
    ("Politie", "NOS", "beinvloeding", "bron_afhankelijkheid",
     "Politie is routineuze bron voor criminaliteitsnieuws. Persvoorlichting bepaalt framing",
     0.90, 0.65, False),
    ("Politie", "De Telegraaf", "beinvloeding", "bron_afhankelijkheid",
     "Telegraaf leunt sterk op politiebronnen voor misdaadnieuws",
     0.85, 0.70, False),
    ("Politie", "RTL Nederland", "beinvloeding", "bron_afhankelijkheid",
     "RTL Nieuws neemt politiepersberichten routinematig over",
     0.85, 0.65, False),

    # Ministeries → denktanks (financiering)
    ("Ministerie van Defensie", "HCSS (The Hague Centre for Strategic Studies)", "financiering", None,
     "Min. van Defensie financiert HCSS-projecten over strategische vraagstukken",
     0.80, 0.55, False),
    ("Ministerie van Defensie", "Clingendael Instituut", "financiering", None,
     "Min. van Defensie financiert Clingendael voor veiligheidsonderzoek",
     0.80, 0.50, False),
    ("Ministerie van Buitenlandse Zaken", "Clingendael Instituut", "financiering", None,
     "Min. van BuZa is hoofdfinancier van Clingendael Instituut",
     0.85, 0.60, False),

    # =========================================================================
    # EIGENDOMSKETENS AANVULLEN
    # =========================================================================
    ("Mediahuis Partners", "Mediahuis", "eigendom", "eigendomsconcentratie",
     "Mediahuis Partners (gecontroleerd door familie Leysen) is belangrijkste aandeelhouder Mediahuis",
     0.90, 0.70, False),
    ("Thomas Leysen", "Mediahuis Partners", "eigendom", None,
     "Leysen controleert Mediahuis Partners, het belangrijkste aandeelhoudersblok",
     0.90, 0.65, False),
    ("DPG Media", "De Morgen", "eigendom", "eigendomsconcentratie",
     "DPG Media bezit De Morgen (Belgische krant). Van Thillo beïnvloedde redactiecultuur na overname",
     0.95, 0.85, False),
    ("DPG Media", "RTL Nieuws", "eigendom", "eigendomsconcentratie",
     "RTL Nieuws is onderdeel van RTL Nederland, eigendom DPG Media",
     0.95, 0.85, False),
    ("Talpa Network", "ANP", "eigendom", None,
     "Talpa was voormalig eigenaar ANP (vóór Chris Oomen). John de Mol had indirect controle over NL persbureau",
     0.90, 0.30, False),

    # GBL connecties
    ("Groupe Bruxelles Lambert", "Adidas", "eigendom", None,
     "GBL heeft belang in Adidas. Illustreert breedte corporate netwerk waar Van Thillo deel van uitmaakt",
     0.85, 0.15, False),

    # =========================================================================
    # DENKTANKS BETER VERBINDEN
    # =========================================================================
    ("Clingendael Instituut", "de Volkskrant", "beinvloeding", "expert_framing",
     "Clingendael levert experts voor duiding buitenland/veiligheid aan kwaliteitskranten",
     0.75, 0.50, False),
    ("Clingendael Instituut", "De Telegraaf", "beinvloeding", "expert_framing",
     "Clingendael-experts worden geciteerd in Telegraaf voor geopolitieke duiding",
     0.70, 0.45, False),
    ("HCSS (The Hague Centre for Strategic Studies)", "de Volkskrant", "beinvloeding", "expert_framing",
     "HCSS levert NAVO-gezinde experts aan kwaliteitskranten",
     0.70, 0.50, False),
    ("HCSS (The Hague Centre for Strategic Studies)", "De Telegraaf", "beinvloeding", "expert_framing",
     "HCSS-directeur Rob de Wijk is veelgevraagd commentator, ook bij Telegraaf",
     0.70, 0.45, False),
    ("Nationale DenkTank", "NOS", "beinvloeding", "expert_framing",
     "Nationale DenkTank levert beleidsanalyses die in media worden opgepikt",
     0.65, 0.35, False),
    ("Nationale DenkTank", "de Volkskrant", "beinvloeding", "expert_framing",
     "NDT-rapporten worden opgepikt door kwaliteitskranten",
     0.60, 0.30, False),
    ("Teldersstichting", "de Volkskrant", "beinvloeding", "expert_framing",
     "Teldersstichting (VVD) levert liberale analyses die het debat kaderen",
     0.65, 0.30, False),
    ("Wiardi Beckman Stichting", "de Volkskrant", "beinvloeding", "expert_framing",
     "WBS (PvdA) levert sociaaldemocratische analyses aan het debat",
     0.65, 0.30, False),

    # =========================================================================
    # FLAK / INTIMIDATIE BREDER
    # =========================================================================
    ("PVV", "RTL Nederland", "censuur", "publieke_aanval",
     "PVV valt commerciële media ook aan, ondermijnt vertrouwen in journalistiek",
     0.75, 0.45, False),
    ("PVV", "ANP", "censuur", "publieke_aanval",
     "PVV-aanvallen op media raken ook ANP als bron van 'mainstream' nieuws",
     0.60, 0.30, False),

    # =========================================================================
    # TECHPLATFORM-RELATIES AANVULLEN
    # =========================================================================
    ("Google", "ANP", "beinvloeding", "algoritmische_filtering",
     "Google News selecteert en rankt ANP-berichten via algoritme",
     0.75, 0.50, False),
    ("Meta (Facebook/Instagram)", "RTL Nederland", "beinvloeding", "algoritmische_filtering",
     "RTL content op social media onderhevig aan algoritmische selectie",
     0.75, 0.60, False),
    ("TikTok", "Mediahuis", "beinvloeding", "algoritmische_filtering",
     "Jongeren bereiken Mediahuis-content steeds meer via TikTok",
     0.60, 0.50, False),
    ("TikTok", "RTL Nederland", "beinvloeding", "algoritmische_filtering",
     "RTL content bereikt jongeren via TikTok-algoritme",
     0.65, 0.55, False),

    # =========================================================================
    # IDEOLOGISCHE SYNCHRONISATIE
    # =========================================================================
    ("World Economic Forum", "Mediahuis", "beinvloeding", "hegemonische_naturalisatie",
     "WEF-narratief van stakeholder capitalism wordt ook in Mediahuis-titels onkritisch overgenomen",
     0.55, 0.45, False),
    ("World Economic Forum", "Thomas Leysen", "lidmaatschap", "ideologische_synchronisatie",
     "Leysen is actief in WEF/Davos-netwerk als onderdeel van transnationale elite",
     0.80, 0.50, False),
    ("Bilderberg Groep", "Christian Van Thillo", "beinvloeding", "ideologische_synchronisatie",
     "Van Thillo opereert in het Bilderberg-netwerk via zijn GBL-positie en mediarol",
     0.65, 0.55, False),
    ("European Round Table of Industrialists", "DPG Media", "beinvloeding", "ideologische_synchronisatie",
     "ERT-leden (waaronder Leysen) delen pro-bedrijfs wereldbeeld dat doorsijpelt naar media",
     0.60, 0.40, False),
    ("Trilaterale Commissie", "Mediahuis", "beinvloeding", "ideologische_synchronisatie",
     "Leysen als lid Trilaterale Commissie verbindt Mediahuis met transnationale elite-consensus",
     0.65, 0.40, False),

    # Institutionele beleggers breder
    ("BlackRock", "Unilever", "eigendom", None,
     "BlackRock is grote aandeelhouder in Unilever, een top-adverteerder van NL media",
     0.85, 0.20, False),
    ("BlackRock", "Philips", "eigendom", None,
     "BlackRock is aandeelhouder in Philips",
     0.85, 0.20, False),
    ("Vanguard", "ING", "eigendom", None,
     "Vanguard is grote aandeelhouder in ING",
     0.80, 0.15, False),
    ("Vanguard", "Unilever", "eigendom", None,
     "Vanguard is grote aandeelhouder in Unilever",
     0.80, 0.15, False),

    # Peter R. de Vries chilling effect
    ("Peter R. de Vries", "De Telegraaf", "beinvloeding", "geweld_intimidatie",
     "Moord op De Vries (2021) had chilling effect op hele NL journalistiek inclusief Telegraaf",
     0.90, 0.55, False),
    ("Peter R. de Vries", "RTL Nederland", "beinvloeding", "geweld_intimidatie",
     "De Vries werkte voor RTL. Zijn moord toont extreme consequentie van misdaadjournalistiek",
     0.95, 0.65, False),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Haal source_id op
    cur.execute("SELECT id FROM sources WHERE title = ?", (SOURCE_TITLE,))
    row = cur.fetchone()
    source_id = row[0] if row else None

    # Bouw lookups
    cur.execute("SELECT id, name FROM roles")
    role_map = {name: rid for rid, name in cur.fetchall()}

    cur.execute("SELECT id, name FROM mechanisms")
    mech_map = {name: mid for mid, name in cur.fetchall()}

    # 1. Insert nieuwe entiteiten
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
                cur.execute(
                    "INSERT OR IGNORE INTO entity_roles (entity_id, role_id) VALUES (?, ?)",
                    (eid, role_id)
                )
            if source_id:
                cur.execute(
                    "INSERT OR IGNORE INTO source_mentions (source_id, entity_id) VALUES (?, ?)",
                    (source_id, eid)
                )
    conn.commit()

    # 2. Bouw entity lookup
    cur.execute("SELECT id, name FROM entities")
    entity_map = {name: eid for eid, name in cur.fetchall()}

    # 3. Insert relaties
    relation_count = 0
    skipped = 0
    for (src_name, tgt_name, rel_type, mech_name, desc,
         certainty, influence, bidir) in NEW_RELATIONS:
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

        # Check of relatie al bestaat
        cur.execute(
            """SELECT id FROM relations
               WHERE source_id=? AND target_id=? AND relation_type=?""",
            (src_id, tgt_id, rel_type)
        )
        if cur.fetchone():
            continue  # al aanwezig

        cur.execute(
            """INSERT INTO relations
               (source_id, target_id, relation_type, mechanism_id,
                description, certainty, influence, bidirectional)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (src_id, tgt_id, rel_type, mech_id, desc,
             certainty, influence, bidir)
        )
        relation_count += 1
        rel_id = cur.lastrowid

        # Argument + citatie
        if source_id:
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
                (arg_id, source_id, "Geïnfereerd uit AI-bronanalyse")
            )

    conn.commit()

    # 4. Statistieken
    cur.execute("SELECT COUNT(*) FROM entities")
    total_entities = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM relations")
    total_relations = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(*) FROM entities e
        WHERE e.id NOT IN (SELECT source_id FROM relations)
        AND e.id NOT IN (SELECT target_id FROM relations)
    """)
    orphans = cur.fetchone()[0]

    conn.close()

    print(f"\n{'='*60}")
    print(f"Database verrijkt")
    print(f"{'='*60}")
    print(f"Nieuwe entiteiten:      {entity_count}")
    print(f"Nieuwe relaties:        {relation_count}")
    print(f"Overgeslagen:           {skipped}")
    print(f"{'='*60}")
    print(f"Totaal entiteiten:      {total_entities}")
    print(f"Totaal relaties:        {total_relations}")
    print(f"Wees-entiteiten:        {orphans}")
    print(f"{'='*60}")


if __name__ == "__main__":
    seed()
