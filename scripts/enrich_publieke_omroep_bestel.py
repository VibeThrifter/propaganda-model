"""
Verrijking: het publieke-omroepbestel als gelaagde structuur (koepel -> omroepen -> redacties).

Aanleiding: het praktijkmodel kende alleen de NOS als losse 'omroep' ("belangrijkste
nieuwsbron"), terwijl de NOS feitelijk een TAAKOMROEP is binnen het NPO-bestel. De hele
laag erboven (de NPO als sturingsorganisatie, de minister van OCW, de Ster) en ernaast
(de ledenomroepen met hun verzuilde identiteit) ontbrak. Bovendien stond Tijs van den Brink
verkeerd: zijn draaideur wees naar de NOS, terwijl hij ~25 jaar EO-presentator was en in
november 2025 CDA-Kamerlid werd.

Het bestel kent drie lagen plus een politiek-bestuurlijke top:
  TOP   minister van OCW (erkenning, budget, benoeming NPO-bestuur), CvdM (toezicht), Ster (reclame).
  KOEPEL NPO (Stichting Nederlandse Publieke Omroep): verdeelt budget/zendtijd, stuurt zonder
         zelf programma's te maken. Raad van Bestuur (Leeflang, ex-Deloitte) + Raad van
         Toezicht (Joustra). De top is een baantjescarrousel voor (oud-)politici (bron: Spit);
         Shula Rijxman ging van NPO-voorzitter naar D66-wethouder.
  OMROEP taakomroepen (NOS nieuws/sport, NTR informatie/cultuur) zonder leden, en ledenomroepen
         (EO, BNNVARA, KRO-NCRV, AVROTROS, VPRO, MAX, WNL, PowNed) met een levensbeschouwelijke/
         politieke identiteit -- de verzuiling als ingebouwde ideologiefilter.
  REDACTIE per omroep een (hoofd)redactie die de dagelijkse redactionele keuzes maakt.

Onderzoeksframe: pro-elite-bias is een EMERGENTE eigenschap van deze structuur, geen complot.
De verzuilde identiteit, de politieke benoemingen en de draaideuren zijn structurele krachten.

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

UNSOURCED_CERTAINTY = 0.05  # conventie: onbronde relaties krijgen certainty 0.05

# --- THEORIE: nieuwe rollen ----------------------------------------------

NEW_ROLES = [
    {
        "name": "omroepkoepel",
        "category": "eigendom",
        "description": (
            "Sturingsorganisatie boven de omroepen (de NPO). Verdeelt budget en zendtijd, "
            "coordineert de zenders en bepaalt de net-profilering, maar maakt zelf geen "
            "programma's. Oefent zo structurele zeggenschap over de omroepen uit."
        ),
    },
    {
        "name": "ledenomroep",
        "category": "eigendom",
        "description": (
            "Ledengebonden omroep die op grond van zijn ledental zendtijd claimt en een "
            "levensbeschouwelijke, religieuze of politieke stroming vertegenwoordigt. Die "
            "verzuilde identiteit is een ingebouwde ideologiefilter in het bestel."
        ),
    },
]

# --- THEORIE: nieuwe mechanismen -----------------------------------------

NEW_MECHANISMS = [
    {
        "name": "bestelsturing",
        "filter": "eigendom",
        "mechanism_type": "structureel",
        "description": (
            "De omroepkoepel (NPO) verdeelt budget en zendtijd, coordineert de zenders en stuurt "
            "de net-profilering, zonder zelf programma's te maken."
        ),
        "effect": (
            "Omroepen zijn voor geld, plek en bereik afhankelijk van de koepel; de koepel kan "
            "de programmering sturen via de geldkraan en zendtijdverdeling in plaats van directe "
            "inhoudelijke bemoeienis."
        ),
        "source_role": "omroepkoepel",
        "target_role": "mediaorganisatie",
    },
    {
        "name": "politieke_benoeming_omroeptop",
        "filter": "eigendom",
        "mechanism_type": "procedureel",
        "description": (
            "De minister van OCW benoemt de NPO-Raad van Bestuur op 'zwaarwegend advies' van een "
            "Raad van Toezicht die zichzelf via een eigen benoemingscommissie aanvult. De RvT's van "
            "NPO en omroepen zitten vol (oud-)politici."
        ),
        "effect": (
            "De top van de publieke omroep wordt langs partij- en netwerklijnen bezet; onafhankelijk "
            "toezicht verzwakt doordat de gecontroleerden de controleurs (mede) selecteren (cooptatie)."
        ),
        "source_role": "politicus",
        "target_role": "omroepkoepel",
    },
    {
        "name": "omroepverzuiling",
        "filter": "ideologie",
        "mechanism_type": "structureel",
        "description": (
            "Een ledenomroep is statutair gebonden aan een levensbeschouwelijke of politieke "
            "stroming (christelijk, socialistisch, rechts-populistisch, ...). Die identiteit "
            "bepaalt onderwerpkeuze, gasten en toon."
        ),
        "effect": (
            "Nieuwsselectie en agenda worden vooraf gekleurd door de zuil; het pluralisme zit "
            "tussen omroepen, niet binnen een redactie, en blijft binnen de grenzen van het bestel."
        ),
        "source_role": "ledenomroep",
        "target_role": "partij",
    },
    {
        "name": "staatsreclame_exploitatie",
        "filter": "advertentie",
        "mechanism_type": "economisch",
        "description": (
            "De Ster verkoopt reclame rond publieke programma's; de opbrengst gaat naar het "
            "ministerie van OCW en komt als budget terug bij de publieke omroep."
        ),
        "effect": (
            "Ook de 'publieke' omroep is deels afhankelijk van advertentie-inkomsten en daarmee "
            "van kijk- en luistercijfers; markt- en bereikslogica disciplineert de programmering."
        ),
        "source_role": "belanghebbende",
        "target_role": "omroepkoepel",
    },
]

# --- INSTANCES: nieuwe entiteiten ----------------------------------------
# velden: name, type, role, description, active_from (optioneel)

NEW_ENTITIES = [
    # -- politiek-bestuurlijke top --
    {
        "name": "NPO",
        "type": "stichting",
        "role": "omroepkoepel",
        "active_from": "2014",
        "description": (
            "Stichting Nederlandse Publieke Omroep: koepel- en sturingsorganisatie boven de "
            "omroepen. Verdeelt budget en zendtijd, beheert de zenders (NPO 1/2/3, radio) en de "
            "net-profilering, maar maakt zelf geen programma's."
        ),
    },
    {
        "name": "Ministerie van OCW",
        "type": "overheidsinstelling",
        "role": "gezagsinstituut",
        "description": (
            "Ministerie van Onderwijs, Cultuur en Wetenschap. Verleent erkenningen aan omroepen, "
            "stelt het mediabudget vast en benoemt de NPO-Raad van Bestuur (tot 2017 met ministeriele "
            "goedkeuring, nu op zwaarwegend advies van de Raad van Toezicht). Het politieke "
            "controlepunt boven het bestel."
        ),
    },
    {
        "name": "Ster",
        "type": "stichting",
        "role": "belanghebbende",
        "active_from": "1967",
        "description": (
            "Stichting Etherreclame: verkoopt de reclame rond publieke programma's. De opbrengst "
            "gaat naar OCW en komt als budget terug bij de publieke omroep -- de advertentiehaak op "
            "een publiek stelsel."
        ),
    },
    # -- NPO-top: personen --
    {
        "name": "Frederieke Leeflang",
        "type": "toezichthouder_persoon",
        "role": "toezichthouder",
        "description": (
            "Voorzitter NPO-Raad van Bestuur (sinds 2022, inmiddels opgestapt). Kwam over van "
            "consultancyfirma Deloitte; de overlap met RvT-voorzitter Joustra werd bekritiseerd "
            "als gesloten benoemingskring (bedrijfsleven -> publieke top)."
        ),
    },
    {
        "name": "Tjibbe Joustra",
        "type": "toezichthouder_persoon",
        "role": "toezichthouder",
        "description": (
            "Voorzitter NPO-Raad van Toezicht, met een lange staat van dienst in de ambtelijke en "
            "bestuurlijke top (o.a. NCTb). Boegbeeld van de 'Haagse' bezetting van het toezicht op "
            "de publieke omroep."
        ),
    },
    {
        "name": "Shula Rijxman",
        "type": "persoon",
        "role": "politicus",
        "description": (
            "Voorzitter NPO-Raad van Bestuur (2016-2021), daarna D66-wethouder in Amsterdam "
            "(2022-2023). Schoolvoorbeeld van de draaideur media-bestuur <-> politiek; lag onder vuur "
            "door een niet-gemelde relatie met de hoogste OCW-ambtenaar en een vakantie met "
            "staatssecretaris Dekker."
        ),
    },
    # -- omroepen: taakomroep --
    {
        "name": "NTR",
        "type": "omroep",
        "role": "mediaorganisatie",
        "active_from": "2010",
        "description": (
            "Taakomroep zonder leden, met een wettelijke taak voor informatie, educatie en cultuur "
            "(jeugd, geschiedenis, wetenschap, onderzoeksjournalistiek). Opvolger van Teleac, NOT en RVU."
        ),
    },
    # -- omroepen: ledenomroepen --
    {
        "name": "EO",
        "type": "omroep",
        "role": "ledenomroep",
        "active_from": "1967",
        "description": (
            "Evangelische Omroep: ledenomroep met een christelijk-evangelische identiteit. Bekend "
            "van talkshows (o.a. Knevel & Van den Brink, Adieu God?). De thuisbasis van Tijs van den "
            "Brink voor zijn overstap naar de politiek."
        ),
    },
    {
        "name": "BNNVARA",
        "type": "omroep",
        "role": "ledenomroep",
        "active_from": "2014",
        "description": (
            "Ledenomroep ontstaan uit de fusie van BNN en VARA (2014). De VARA-wortels zijn "
            "socialistisch/links; de omroep wordt met die maatschappelijke stroming geassocieerd."
        ),
    },
    {
        "name": "KRO-NCRV",
        "type": "omroep",
        "role": "ledenomroep",
        "active_from": "2014",
        "description": (
            "Ledenomroep uit de fusie van de katholieke KRO en de protestants-christelijke NCRV "
            "(2014). Christelijk-maatschappelijke signatuur, historisch verbonden met de CDA-zuil."
        ),
    },
    {
        "name": "AVROTROS",
        "type": "omroep",
        "role": "ledenomroep",
        "active_from": "2014",
        "description": (
            "Ledenomroep uit de fusie van AVRO en TROS (2014). Breed/algemeen profiel zonder scherpe "
            "levensbeschouwelijke binding, maar wel ledengebonden."
        ),
    },
    {
        "name": "VPRO",
        "type": "omroep",
        "role": "ledenomroep",
        "active_from": "1926",
        "description": (
            "Ledenomroep met een progressief-intellectueel profiel; oorspronkelijk vrijzinnig-"
            "protestants, later cultureel-progressief."
        ),
    },
    {
        "name": "Omroep MAX",
        "type": "omroep",
        "role": "ledenomroep",
        "active_from": "2005",
        "description": (
            "Ledenomroep gericht op de oudere generatie (50-plussers). De doelgroep-identiteit "
            "bepaalt onderwerpkeuze en agenda."
        ),
    },
    {
        "name": "WNL",
        "type": "omroep",
        "role": "ledenomroep",
        "active_from": "2009",
        "description": (
            "Wakker Nederland: ledenomroep met een rechtse signatuur, ontstaan in de kring rond "
            "De Telegraaf. Voorbeeld van een uitgesproken ideologische zuil binnen het bestel."
        ),
    },
    {
        "name": "PowNed",
        "type": "omroep",
        "role": "ledenomroep",
        "active_from": "2009",
        "description": (
            "Ledenomroep voortgekomen uit weblog GeenStijl, met een rechts-populistische, "
            "anti-establishment signatuur."
        ),
    },
    # -- redactielaag (representatief) --
    {
        "name": "NOS-hoofdredactie",
        "type": "mediaorganisatie",
        "role": "redactie",
        "description": (
            "De hoofdredactie van de NOS: maakt de dagelijkse redactionele keuzes over nieuws en "
            "duiding, binnen het kader (budget, taakopdracht, bestelsturing) dat de lagen erboven "
            "stellen. Hier wordt de feitelijke selectie gemaakt."
        ),
    },
    {
        "name": "EO-redactie",
        "type": "mediaorganisatie",
        "role": "redactie",
        "description": (
            "De redactie van de EO: maakt binnen de christelijk-evangelische identiteit van de "
            "omroep de dagelijkse programma- en onderwerpkeuzes."
        ),
    },
    # -- RvT-politici (representatieve instances van de baantjescarrousel; bron: Spit) --
    {
        "name": "Kathleen Ferrier",
        "type": "politicus",
        "role": "politicus",
        "description": "CDA-politica (oud-Kamerlid) en toezichthouder bij (KRO-)NCRV.",
    },
    {
        "name": "Arjan el Fassed",
        "type": "politicus",
        "role": "politicus",
        "description": "Oud-GroenLinks-Kamerlid en toezichthouder bij BNNVARA.",
    },
    {
        "name": "Rob van Gijzel",
        "type": "politicus",
        "role": "politicus",
        "description": "Oud-PvdA-politicus (o.a. burgemeester Eindhoven) en toezichthouder bij de NOS.",
    },
    {
        "name": "Frits Huffnagel",
        "type": "politicus",
        "role": "politicus",
        "description": "VVD-politicus en toezichthouder bij AVROTROS.",
    },
    # -- partijen die nog ontbraken (voor schone draaideur-/verzuiling-bedrading) --
    {
        "name": "D66",
        "type": "partij",
        "role": "partij",
        "description": "Sociaal-liberale partij; relevant via o.a. de draaideur van Shula Rijxman.",
    },
    {
        "name": "GroenLinks",
        "type": "partij",
        "role": "partij",
        "description": "Groen-linkse partij; relevant via toezicht-draaideuren in het omroepbestel.",
    },
]

# --- INSTANCES: nieuwe relaties ------------------------------------------
# tuples: (src_name, tgt_name, relation_type, mechanism_name|None, description, influence, bidirectional)

NEW_RELATIONS = [
    # koepel stuurt de omroepen (bestelsturing)
    ("NPO", "NOS", "beinvloeding", "bestelsturing",
     "NPO verdeelt budget en zendtijd voor de nieuws-/sporttaak van de NOS.", 0.6, 0),
    ("NPO", "NTR", "beinvloeding", "bestelsturing",
     "NPO stuurt budget, zendtijd en profilering van de NTR.", 0.5, 0),
    ("NPO", "EO", "beinvloeding", "bestelsturing",
     "NPO stuurt budget, zendtijd en profilering van de EO.", 0.5, 0),
    ("NPO", "BNNVARA", "beinvloeding", "bestelsturing",
     "NPO stuurt budget, zendtijd en profilering van BNNVARA.", 0.5, 0),
    ("NPO", "KRO-NCRV", "beinvloeding", "bestelsturing",
     "NPO stuurt budget, zendtijd en profilering van KRO-NCRV.", 0.5, 0),
    ("NPO", "AVROTROS", "beinvloeding", "bestelsturing",
     "NPO stuurt budget, zendtijd en profilering van AVROTROS.", 0.5, 0),
    ("NPO", "VPRO", "beinvloeding", "bestelsturing",
     "NPO stuurt budget, zendtijd en profilering van de VPRO.", 0.5, 0),
    ("NPO", "Omroep MAX", "beinvloeding", "bestelsturing",
     "NPO stuurt budget, zendtijd en profilering van Omroep MAX.", 0.5, 0),
    ("NPO", "WNL", "beinvloeding", "bestelsturing",
     "NPO stuurt budget, zendtijd en profilering van WNL.", 0.5, 0),
    ("NPO", "PowNed", "beinvloeding", "bestelsturing",
     "NPO stuurt budget, zendtijd en profilering van PowNed.", 0.5, 0),

    # politiek-bestuurlijke top
    ("Ministerie van OCW", "NPO", "regulering", "politieke_benoeming_omroeptop",
     "OCW verleent erkenningen, stelt het budget vast en benoemt de NPO-Raad van Bestuur.", 0.7, 0),
    ("CvdM (Commissariaat voor de Media)", "NPO", "regulering", None,
     "Het Commissariaat handhaaft de Mediawet en houdt toezicht op de publieke omroep.", 0.35, 0),
    ("Ster", "Ministerie van OCW", "financiering", "staatsreclame_exploitatie",
     "Ster-reclameopbrengst loopt via OCW terug als budget naar de publieke omroep.", 0.4, 0),

    # NPO-top: personen
    ("Frederieke Leeflang", "NPO", "bestuurder", "draaideurconstructie",
     "Voorzitter NPO-Raad van Bestuur, afkomstig van Deloitte (bedrijfsleven -> publieke top).", 0.6, 0),
    ("Tjibbe Joustra", "NPO", "bestuurder", "politieke_benoeming_omroeptop",
     "Voorzitter NPO-Raad van Toezicht; boegbeeld van de Haagse bezetting van het toezicht.", 0.55, 0),
    ("Tjibbe Joustra", "Frederieke Leeflang", "cooptatie", "politieke_benoeming_omroeptop",
     "RvT-voorzitter en RvB-voorzitter in een gesloten, elkaar versterkende benoemingskring.", 0.5, 1),
    ("Shula Rijxman", "NPO", "draaideur", "draaideur_politiek_media",
     "NPO-bestuursvoorzitter (2016-2021) die daarna D66-wethouder werd: draaideur media-bestuur <-> politiek.", 0.55, 0),
    ("Shula Rijxman", "Ministerie van OCW", "cooptatie", "draaideur_politiek_media",
     "Niet-gemelde verstrengeling met de OCW-top (relatie met hoogste ambtenaar, vakantie met staatssecretaris Dekker).", 0.45, 0),
    ("Shula Rijxman", "D66", "lidmaatschap", None,
     "Werd na haar NPO-voorzitterschap D66-wethouder in Amsterdam.", 0.2, 0),

    # RvT-politici: de baantjescarrousel (bron: Spit)
    ("Kathleen Ferrier", "KRO-NCRV", "draaideur", "draaideur_politiek_media",
     "CDA-politica als toezichthouder bij (KRO-)NCRV: politiek -> mediatoezicht.", 0.4, 0),
    ("Kathleen Ferrier", "CDA", "lidmaatschap", None, "CDA-lid (oud-Kamerlid).", 0.2, 0),
    ("Arjan el Fassed", "BNNVARA", "draaideur", "draaideur_politiek_media",
     "Oud-GroenLinks-Kamerlid als toezichthouder bij BNNVARA: politiek -> mediatoezicht.", 0.4, 0),
    ("Arjan el Fassed", "GroenLinks", "lidmaatschap", None, "Oud-GroenLinks-Kamerlid.", 0.2, 0),
    ("Rob van Gijzel", "NOS", "draaideur", "draaideur_politiek_media",
     "Oud-PvdA-politicus als toezichthouder bij de NOS: politiek -> mediatoezicht.", 0.45, 0),
    ("Rob van Gijzel", "PvdA", "lidmaatschap", None, "PvdA-politicus (oud-burgemeester Eindhoven).", 0.2, 0),
    ("Frits Huffnagel", "AVROTROS", "draaideur", "draaideur_politiek_media",
     "VVD-politicus als toezichthouder bij AVROTROS: politiek -> mediatoezicht.", 0.4, 0),
    ("Frits Huffnagel", "VVD", "lidmaatschap", None, "VVD-politicus.", 0.2, 0),

    # verzuiling: omroep-identiteit <-> maatschappelijke/politieke stroming
    ("BNNVARA", "PvdA", "alliantie", "omroepverzuiling",
     "Socialistische/linkse VARA-wortels; geassocieerd met de sociaaldemocratische stroming.", 0.45, 0),
    ("KRO-NCRV", "CDA", "alliantie", "omroepverzuiling",
     "Katholiek-christelijke wortels; historisch verbonden met de CDA-zuil.", 0.4, 0),
    ("WNL", "De Telegraaf", "alliantie", "omroepverzuiling",
     "Rechtse signatuur, ontstaan in de kring rond De Telegraaf.", 0.5, 0),

    # redactielaag: waar de dagelijkse keuzes vallen
    ("NOS-hoofdredactie", "NOS", "personeel", "hoofdredacteur_als_filter",
     "De hoofdredactie maakt binnen de NOS de dagelijkse nieuwsselectie en duiding.", 0.6, 0),
    ("EO-redactie", "EO", "personeel", "hoofdredacteur_als_filter",
     "De EO-redactie maakt binnen de christelijk-evangelische identiteit de programma-keuzes.", 0.5, 0),

    # Tijs van den Brink: de draaideur compleet maken (bestemming CDA)
    ("Tijs van den Brink", "CDA", "lidmaatschap", None,
     "Werd op 12 november 2025 CDA-Kamerlid na ~25 jaar EO-journalistiek/presentatie.", 0.3, 0),
]


# --- helpers --------------------------------------------------------------

def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, dest)
    print(f"Backup gemaakt: {dest.name}")


def role_id(conn, name):
    row = conn.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
    if not row:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
    return row[0]


def mechanism_id(conn, name):
    if name is None:
        return None
    row = conn.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
    if not row:
        raise SystemExit(f"FOUT: mechanisme '{name}' niet gevonden.")
    return row[0]


def entity_id(conn, name):
    row = conn.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()
    return row[0] if row else None


def upsert_role(conn, r):
    if conn.execute("SELECT 1 FROM roles WHERE name=?", (r["name"],)).fetchone():
        conn.execute("UPDATE roles SET category=?, description=? WHERE name=?",
                     (r["category"], r["description"], r["name"]))
        print(f"Rol bijgewerkt: {r['name']}")
    else:
        conn.execute("INSERT INTO roles (name, category, description) VALUES (?,?,?)",
                     (r["name"], r["category"], r["description"]))
        print(f"Rol toegevoegd: {r['name']} ({r['category']})")


def upsert_mechanism(conn, m):
    sid, tid = role_id(conn, m["source_role"]), role_id(conn, m["target_role"])
    if conn.execute("SELECT 1 FROM mechanisms WHERE name=?", (m["name"],)).fetchone():
        conn.execute(
            """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
               source_role_id=?, target_role_id=? WHERE name=?""",
            (m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid, m["name"]))
        print(f"Mechanisme bijgewerkt: {m['name']}")
    else:
        conn.execute(
            """INSERT INTO mechanisms
               (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
               VALUES (?,?,?,?,?,?,?)""",
            (m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid))
        print(f"Mechanisme toegevoegd: {m['name']} ({m['source_role']} -> {m['target_role']})")


def get_or_create_entity(conn, e):
    eid = entity_id(conn, e["name"])
    rid = role_id(conn, e["role"])
    active_from = e.get("active_from")
    if eid:
        conn.execute(
            "UPDATE entities SET type=?, primary_role_id=?, description=?, active_from=COALESCE(?, active_from) WHERE id=?",
            (e["type"], rid, e["description"], active_from, eid))
        print(f"Entiteit bijgewerkt: {e['name']}")
    else:
        conn.execute(
            "INSERT INTO entities (name, type, primary_role_id, description, active_from, active) VALUES (?,?,?,?,?,1)",
            (e["name"], e["type"], rid, e["description"], active_from))
        eid = entity_id(conn, e["name"])
        print(f"Entiteit aangemaakt: {e['name']} ({e['type']}, rol {e['role']})")
    conn.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id, notes) VALUES (?,?,?)",
                 (eid, rid, "primaire functie"))
    return eid


def ensure_relation(conn, src_name, tgt_name, rtype, mech_name, desc, influence, bidir):
    src, tgt = entity_id(conn, src_name), entity_id(conn, tgt_name)
    if src is None or tgt is None:
        raise SystemExit(f"FOUT: relatie {src_name} -> {tgt_name} mist een entiteit.")
    if conn.execute("SELECT 1 FROM relations WHERE source_id=? AND target_id=?",
                    (src, tgt)).fetchone():
        return False
    conn.execute(
        """INSERT INTO relations
           (source_id, target_id, relation_type, mechanism_id, description, certainty, influence, bidirectional, active)
           VALUES (?,?,?,?,?,?,?,?,1)""",
        (src, tgt, rtype, mechanism_id(conn, mech_name), desc, UNSOURCED_CERTAINTY, influence, bidir))
    return True


# --- gerichte correcties --------------------------------------------------

def fix_nos_description(conn):
    new_desc = (
        "Taakomroep voor nieuws en sport binnen het NPO-bestel (geen ledenomroep), met een "
        "wettelijke taak voor onafhankelijke nieuwsvoorziening. Belangrijkste nieuwsbron van "
        "Nederland. De PVV wil de publieke omroep afschaffen."
    )
    conn.execute("UPDATE entities SET description=? WHERE name='NOS'", (new_desc,))
    print("NOS bijgewerkt: omschreven als taakomroep binnen het NPO-bestel.")


def fix_tijs(conn):
    tijs = entity_id(conn, "Tijs van den Brink")
    nos = entity_id(conn, "NOS")
    eo = entity_id(conn, "EO")
    if tijs is None or eo is None:
        raise SystemExit("FOUT: Tijs van den Brink of EO ontbreekt.")

    # 1. draaideur omhangen van NOS naar EO (idempotent)
    row = conn.execute(
        "SELECT id, target_id FROM relations WHERE source_id=? AND relation_type='draaideur'",
        (tijs,)).fetchone()
    if row and row[1] == nos:
        conn.execute(
            """UPDATE relations SET target_id=?, mechanism_id=?, description=? WHERE id=?""",
            (eo, mechanism_id(conn, "draaideur_journalistiek_politiek"),
             "~25 jaar EO-journalist/presentator (talkshows), stapte in november 2025 over naar de "
             "Tweede Kamer voor het CDA: draaideur journalistiek -> politiek.", row[0]))
        print("Tijs van den Brink: draaideur omgehangen van NOS naar EO.")
    elif row and row[1] == eo:
        print("Tijs van den Brink: draaideur wijst al naar EO (overgeslagen).")
    else:
        ensure_relation(conn, "Tijs van den Brink", "EO", "draaideur",
                        "draaideur_journalistiek_politiek",
                        "~25 jaar EO-journalist/presentator, stapte in 2025 over naar het CDA.", 0.55, 0)
        print("Tijs van den Brink: draaideur naar EO aangemaakt.")

    # 2. journalist-rol toevoegen (hij was journalist voordat hij politicus werd)
    jr = role_id(conn, "journalist")
    conn.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id, notes) VALUES (?,?,?)",
                 (tijs, jr, "herkomst: EO-journalist/presentator"))
    # type/omschrijving aanscherpen (hij is sinds nov 2025 daadwerkelijk politicus)
    conn.execute(
        "UPDATE entities SET description=? WHERE id=?",
        ("EO-journalist en presentator (~25 jaar talkshows op de EO), sinds 12 november 2025 "
         "CDA-Tweede Kamerlid. Draaideur journalistiek -> politiek.", tijs))
    print("Tijs van den Brink: journalist-rol + omschrijving bijgewerkt.")


# --- main -----------------------------------------------------------------

def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("\n[1] theorie: rollen")
    for r in NEW_ROLES:
        upsert_role(conn, r)

    print("\n[2] theorie: mechanismen")
    for m in NEW_MECHANISMS:
        upsert_mechanism(conn, m)

    print("\n[3] instances: entiteiten (top, omroepen, redacties, personen, partijen)")
    for e in NEW_ENTITIES:
        get_or_create_entity(conn, e)

    print("\n[4] instances: relaties")
    added = 0
    for rel in NEW_RELATIONS:
        if ensure_relation(conn, *rel):
            added += 1
    print(f"  nieuwe relaties toegevoegd: {added} (van {len(NEW_RELATIONS)})")

    print("\n[5] correcties: NOS + Tijs van den Brink")
    fix_nos_description(conn)
    fix_tijs(conn)

    conn.commit()
    bad = conn.execute("PRAGMA foreign_key_check").fetchall()
    if bad:
        raise SystemExit(f"FOUT: foreign_key_check faalt: {bad}")

    ent = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    rel = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
    rollen = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    mech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    omroepen = conn.execute("SELECT COUNT(*) FROM entities WHERE type='omroep'").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Entiteiten: {ent} | relaties: {rel} | rollen: {rollen} | "
          f"mechanismen: {mech} | omroepen: {omroepen}")


if __name__ == "__main__":
    main()
