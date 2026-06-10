#!/usr/bin/env python3
"""
Migratie: de WHO-klimaatcasus van 17 mei 2026 als onderbouwing voor de
sourcing-keten (vervolg op migrate_elite_forum_onderbouwing.py, zelfde aanpak:
publiek waarneembaar spoor → argumenten bij bestaande mechanismen).

De casus (alle feiten online geverifieerd op 10 juni 2026):
  - WHO/Europa's Pan-European Commission on Climate and Health (gelanceerd
    11 juni 2025, voorzitter Katrín Jakobsdóttir) publiceerde haar Call to
    Action op 17 mei 2026.
  - Het ANP/NOS-bericht "Experts: klimaatverandering is 'catastrofale
    bedreiging voor volksgezondheid'" (nos.nl/artikel/2614735) verscheen
    DEZELFDE dag (17 mei 2026, 20:17), zonder byline, met de kernframes uit
    het commissiemateriaal.
  - Alle geciteerde stemmen komen uit dezelfde institutionele keten:
    commissielid Ernst Kuipers (oud-minister VWS 2022-2024; nu o.a. RvT-
    voorzitter TU Delft, vice-president NTU Singapore) en RVS-voorzitter
    Jet Bussemaker (oud-minister OCW 2012-2017, oud-staatssecretaris VWS;
    RVS-voorzitter sinds 1 juni 2019), die instemmend reageert. De enige
    relativering is de slotzin.

Wat dit toevoegt (theorie eerst, praktijk bescheiden):
  theorie  - eerste argument bij institutionele_voorlichting (91): voorverpakte
             institutionele communicatie bepaalt de framing (Sumner et al. 2014
             + persmoment-spoor van 17 mei 2026);
           - eerste argument bij draaideur_politiek_institutie (95): Kuipers en
             Bussemaker als publiek gedocumenteerde gevallen;
           - eerste argument bij expert_legitimatie (87), contextual: de expert
             legitimeert mede zijn eigen eerdere beleidsframe ("pandemische
             paraatheid" → "crisisparaatheid"); inbedding wordt deels wél
             vermeld, dus begrensd gewicht;
           - contextual argument bij schijndebat (17): eenstemmige sourcing in
             één bericht als publiek spoor — géén claim over NOS-brede
             verslaggeving.
  praktijk - entiteiten WHO, RVS, Ernst Kuipers, Jet Bussemaker; relaties
             Kuipers→WHO en Bussemaker→RVS (draaideur, gedocumenteerd feit,
             certainty 0.9) en WHO→NOS / RVS→NOS (bron_van via
             bron_afhankelijkheid, certainty 0.7), elk met eigen argument.
             De ANP-schakel hoeft niet apart: ANP→NOS (pakketjournalistiek)
             bestaat al, dus de keten WHO→NOS naast ANP→NOS volgt het
             RIVM/OMT-precedent.

Bewust NIET toegevoegd:
  - geen nieuw mechanisme of hyperedge: "synchrone publicatie op het
    persmoment" is waarneembare output van institutionele_voorlichting +
    persbureau_brongebondenheid + pakketjournalistiek, geen nieuwe structuur;
  - geen claim van redactionele opzet of WHO-regie: alarmtaal is een
    gedocumenteerde communicatiestrategie van instituten, de doorstroom is
    verklaarbaar uit kosten- en embargoroutines (emergent, geen complot);
  - geen argument over "monocausale reductie": de gezondheidskoppelingen in
    het bericht zijn aan studies geattribueerd; die kritiek is inhoudelijk
    zwak en hoort niet in het model;
  - geen entiteiten Katrín Jakobsdóttir of The Lancet (geen rol in de
    NL-keten); het Lancet-rapport is niet als bron geregistreerd (403 bij
    verificatie; de WHO-commissiepagina volstaat als primaire bron);
  - schijndebat/expert_legitimatie blijven contextual met beperkt gewicht:
    één artikel is een spoor, geen media-inhoudsanalyse.

Backup-then-migrate; idempotent op sources.title, entities.name,
(source,target,mechanism) voor relaties en (target, claim) voor argumenten.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-klimaatcasus-sourcing-2026-06"
ACCESSED = "2026-06-10"


def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = DB.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB, dst)
    print(f"backup -> {dst.name}")


def main():
    if not DB.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB}")
    backup()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    roles = {n: i for i, n in cur.execute("SELECT id, name FROM roles")}

    # ---- BRONNEN (SELECT-first: sources heeft geen unique constraint) --------
    def add_source(title, stype, author, publisher, date, reliability, url=None):
        row = cur.execute("SELECT id FROM sources WHERE title=?", (title,)).fetchone()
        if row:
            sid = row[0]
        else:
            cur.execute(
                """INSERT INTO sources
                   (title, author, source_type, publisher, date_published, reliability)
                   VALUES (?,?,?,?,?,?)""",
                (title, author, stype, publisher, date, reliability))
            sid = cur.lastrowid
            print(f"+ bron [{sid}] {title[:60]}")
        if url and not cur.execute(
            "SELECT 1 FROM source_locations WHERE source_id=? AND location=?",
            (sid, url)).fetchone():
            cur.execute(
                "INSERT INTO source_locations (source_id, location_type, location, accessed_at) "
                "VALUES (?,?,?,?)", (sid, "url", url, ACCESSED))
        return sid

    SRC_NOS = add_source(
        "Experts: klimaatverandering is 'catastrofale bedreiging voor volksgezondheid'",
        "nieuwsartikel", "ANP / NOS Nieuws", "NOS", "2026-05-17",
        "kwaliteitsjournalistiek",
        "https://nos.nl/artikel/2614735-experts-klimaatverandering-is-catastrofale-bedreiging-voor-volksgezondheid")
    SRC_WHO = add_source(
        "Pan-European Commission on Climate and Health (commissiepagina)",
        "website", "WHO Regional Office for Europe", "WHO/Europe", None,
        "institutioneel",
        "https://www.who.int/europe/groups/pan-european-commission-on-climate-and-health")
    SRC_DELTA = add_source(
        "Kuipers in WHO report: climate threatens public health",
        "nieuwsartikel", "Delta", "Delta (TU Delft)", None, "regulier",
        "https://delta.tudelft.nl/en/article/kuipers-in-who-report-climate-threatens-public-health")
    SRC_RVS_ADVIES = add_source(
        "Te heet onder onze voeten — gezond samenleven kan alleen op een gezonde planeet",
        "rapport", "Raad voor Volksgezondheid & Samenleving", "RVS", "2025-07-21",
        "institutioneel",
        "https://www.raadrvs.nl/adviezen/t/te-heet-onder-onze-voeten")
    SRC_RVS_PROFIEL = add_source(
        "Prof. dr. M. (Jet) Bussemaker (RVS-profielpagina)",
        "website", "Raad voor Volksgezondheid & Samenleving", "RVS", None,
        "institutioneel",
        "https://www.raadrvs.nl/personen/raad/prof.-dr.-m.-jet-bussemaker")
    SRC_SUMNER = add_source(
        "The association between exaggeration in health related science news "
        "and academic press releases: retrospective observational study",
        "academisch_artikel", "Sumner, P. et al.", "BMJ", "2014-12-10",
        "academisch", "https://www.bmj.com/content/349/bmj.g7015")

    # ---- ENTITEITEN ----------------------------------------------------------
    def add_entity(name, etype, role, description, active_from=None):
        row = cur.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()
        if row:
            return row[0]
        cur.execute(
            """INSERT INTO entities (name, type, primary_role_id, description, active_from)
               VALUES (?,?,?,?,?)""",
            (name, etype, roles[role], description, active_from))
        eid = cur.lastrowid
        cur.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id) VALUES (?,?)",
                    (eid, roles[role]))
        print(f"+ entiteit [{eid}] {name}")
        return eid

    E_WHO = add_entity(
        "WHO (Wereldgezondheidsorganisatie)", "overheidsinstelling", "gezagsinstituut",
        "VN-organisatie voor volksgezondheid (1948). Stelt internationale "
        "gezondheidsnormen en noodstatussen vast; rapporten en persmomenten "
        "(o.a. de Pan-European Commission on Climate and Health, 2025-2026) "
        "sturen nieuwsagenda's wereldwijd.", "1948")
    E_RVS = add_entity(
        "RVS (Raad voor Volksgezondheid en Samenleving)", "overheidsinstelling",
        "gezagsinstituut",
        "Onafhankelijk adviesorgaan van regering en parlement voor "
        "volksgezondheid en samenleving. Adviezen (o.a. 'Te heet onder onze "
        "voeten', juli 2025) zetten gezondheids- en klimaatthema's op de "
        "publieke agenda.")
    E_KUIPERS = add_entity(
        "Ernst Kuipers", "persoon", "politicus",
        "Oud-minister van VWS (2022-2024, kabinet-Rutte IV); daarvoor "
        "bestuursvoorzitter Erasmus MC. Na het ministerschap o.a. "
        "vice-president research NTU Singapore, voorzitter raad van toezicht "
        "TU Delft (september 2025) en lid van de WHO Pan-European Commission "
        "on Climate and Health.")
    E_BUSSEMAKER = add_entity(
        "Jet Bussemaker", "persoon", "politicus",
        "Oud-minister van OCW (2012-2017) en oud-staatssecretaris van VWS "
        "(2007-2010, PvdA). Sinds 1 juni 2019 voorzitter van de RVS; "
        "hoogleraar aan het LUMC / Universiteit Leiden.")

    ENT = {n: i for i, n in cur.execute("SELECT id, name FROM entities")}
    E_NOS = ENT["NOS"]

    def mech_id(name):
        r = cur.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
        if not r:
            raise SystemExit(f"mechanisme ontbreekt: {name}")
        return r[0]

    M_VOORLICHTING = mech_id("institutionele_voorlichting")
    M_DRAAIDEUR = mech_id("draaideur_politiek_institutie")
    M_EXPERT = mech_id("expert_legitimatie")
    M_SCHIJNDEBAT = mech_id("schijndebat")
    M_BRON = mech_id("bron_afhankelijkheid")

    # ---- RELATIES (praktijk) -------------------------------------------------
    def add_relation(src, tgt, rtype, mech, desc, certainty, influence,
                     active_from=None):
        row = cur.execute(
            "SELECT id FROM relations WHERE source_id=? AND target_id=? AND mechanism_id=?",
            (src, tgt, mech)).fetchone()
        if row:
            print(f"relatie bestaat al (id {row[0]})")
            return row[0]
        cur.execute(
            """INSERT INTO relations (source_id, target_id, relation_type,
               mechanism_id, description, certainty, influence, active_from)
               VALUES (?,?,?,?,?,?,?,?)""",
            (src, tgt, rtype, mech, desc, certainty, influence, active_from))
        rid = cur.lastrowid
        print(f"+ relatie [{rid}] {desc[:70]}")
        return rid

    R_KUIPERS_WHO = add_relation(
        E_KUIPERS, E_WHO, "draaideur", M_DRAAIDEUR,
        "Oud-minister van VWS (2022-2024) is lid van de Pan-European "
        "Commission on Climate and Health van WHO/Europa (gelanceerd 11 juni "
        "2025).", 0.9, 0.35, "2025")
    R_BUSSEMAKER_RVS = add_relation(
        E_BUSSEMAKER, E_RVS, "draaideur", M_DRAAIDEUR,
        "Oud-minister van OCW (2012-2017) en oud-staatssecretaris van VWS is "
        "sinds 1 juni 2019 voorzitter van de RVS.", 0.9, 0.7, "2019")
    R_WHO_NOS = add_relation(
        E_WHO, E_NOS, "bron_van", M_BRON,
        "NOS bericht op gezag van WHO-organen; het ANP/NOS-bericht van 17 mei "
        "2026 verscheen op de dag van de Call to Action van de "
        "klimaatcommissie en volgt het commissiemateriaal (via het ANP; de "
        "schakel ANP→NOS bestaat al als pakketjournalistiek).", 0.7, 0.5)
    R_RVS_NOS = add_relation(
        E_RVS, E_NOS, "bron_van", M_BRON,
        "Het adviesorgaan levert de instemmende binnenlandse duiding bij "
        "(inter)nationale gezondheidsrapporten; reactie van de RVS-voorzitter "
        "in het bericht van 17 mei 2026.", 0.7, 0.35)

    # ---- ARGUMENTEN ----------------------------------------------------------
    def add_arg(target_col, target_id, stance, claim, reasoning, weight, citations):
        if cur.execute(f"SELECT 1 FROM arguments WHERE {target_col}=? AND claim=?",
                       (target_id, claim)).fetchone():
            print("argument bestaat al (claim ongewijzigd)")
            return
        cur.execute(
            f"""INSERT INTO arguments ({target_col}, stance, claim, reasoning,
                weight, status, contributed_by)
                VALUES (?,?,?,?,?,?,?)""",
            (target_id, stance, claim, reasoning, weight, "ongecontroleerd", CONTRIB))
        aid = cur.lastrowid
        for sid, quote, ctx in citations:
            cur.execute("INSERT INTO citations (argument_id, source_id, quote, context) "
                        "VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument ({stance}) bij {target_col}={target_id}")

    # Letterlijk geverifieerd via nos.nl (WebFetch, 10 juni 2026): kop, datum,
    # ANP-vermelding, sprekers en openingszinnen. Overige passages zijn
    # overgenomen uit een integrale kopie van het bericht.
    NOS_OPENING = ("Klimaatverandering moet in Europa worden behandeld als "
                   "internationale noodsituatie voor de volksgezondheid. Dat "
                   "stelt een speciale commissie die is opgezet door de "
                   "Wereldgezondheidsorganisatie (WHO).")

    # -- theorie ---------------------------------------------------------------
    add_arg("mechanism_id", M_VOORLICHTING, "supporting",
        "Gezagsinstituten verpakken hun boodschap voor: persmomenten, "
        "gelanceerde rapporten en kant-en-klare citaten bepalen de framing "
        "van het nieuws voordat journalistieke toetsing plaatsvindt.",
        "Sumner et al. (BMJ 2014) toonden dat overdrijving in "
        "gezondheidsnieuws meestal al in het institutionele persbericht zit "
        "en dat nieuwsberichten het persbericht volgen. De klimaatcasus van "
        "mei 2026 toont dezelfde routine als publiek spoor: de WHO-commissie "
        "publiceerde haar Call to Action op 17 mei 2026 en het ANP/NOS-bericht "
        "verscheen diezelfde dag (20:17) met de kernframes ('catastrofale "
        "bedreiging', 'noodsituatie') uit het commissiemateriaal. Dit "
        "documenteert voorverpakking en gelijktijdige doorstroom; het zegt "
        "niets over de juistheid van de inhoud en impliceert geen regie bij "
        "de redactie.", 0.55,
        [(SRC_SUMNER,
          "40% van de persberichten bevatte overdreven gezondheidsadvies, 33% "
          "overdreven causale claims en 36% overdreven extrapolatie van dier "
          "naar mens, vergeleken met het onderliggende artikel; het nieuws "
          "volgde doorgaans het persbericht.",
          "typering van de kernresultaten (BMJ 2014;349:g7015); geen "
          "letterlijk citaat"),
         (SRC_WHO,
          "Commissie gelanceerd op 11 juni 2025 onder voorzitterschap van "
          "Katrín Jakobsdóttir; Call to Action gepubliceerd op 17 mei 2026.",
          "typering van de WHO/Europe-commissiepagina (geraadpleegd 10 juni "
          "2026); geen letterlijk citaat"),
         (SRC_NOS, NOS_OPENING,
          "letterlijke openingszinnen van het ANP/NOS-bericht van 17 mei "
          "2026, 20:17 — dezelfde dag als de Call to Action")])

    add_arg("mechanism_id", M_DRAAIDEUR, "supporting",
        "Oud-bewindspersonen stromen door naar bestuurs- en adviesfuncties "
        "bij (inter)nationale gezagsinstituten, waardoor politieke en "
        "institutionele perspectieven personeel verweven raken.",
        "Twee publiek gedocumenteerde Nederlandse gevallen uit de "
        "klimaatcasus: Ernst Kuipers (minister VWS 2022-2024 → lid WHO "
        "Pan-European Commission on Climate and Health, RvT-voorzitter TU "
        "Delft, vice-president NTU Singapore) en Jet Bussemaker (minister OCW "
        "2012-2017, staatssecretaris VWS → RVS-voorzitter sinds 2019). De "
        "benoemingen zijn openbaar en regulier; het mechanisme beschrijft "
        "structurele verweving van perspectieven, geen verborgen agenda. "
        "Effect in de casus: het internationale rapport krijgt een vertrouwd "
        "Nederlands gezicht, en het adviesorgaan dat instemmend reageert "
        "wordt eveneens door een oud-bewindspersoon geleid.", 0.6,
        [(SRC_DELTA,
          "Kuipers is sinds september 2025 voorzitter van de raad van "
          "toezicht van de TU Delft, vice-president research aan NTU "
          "Singapore en lid van de Pan-European Commission on Climate and "
          "Health.",
          "typering van het Delta-artikel (TU Delft); geen letterlijk citaat"),
         (SRC_RVS_PROFIEL,
          "Jet Bussemaker is sinds 1 juni 2019 voorzitter van de RVS; eerder "
          "minister van OCW (2012-2017) en staatssecretaris van VWS "
          "(2007-2010); hoogleraar aan het LUMC.",
          "typering van de RVS-profielpagina; geen letterlijk citaat")])

    add_arg("mechanism_id", M_EXPERT, "contextual",
        "In de klimaatcasus van mei 2026 wordt het commissielid als "
        "deskundige duider opgevoerd; zijn oud-ministerschap wordt genoemd, "
        "maar niet dat hij het beleidsframe dat hij als minister zelf "
        "vormgaf ('pandemische paraatheid') als commissielid doortrekt "
        "('crisisparaatheid') — de expert legitimeert zo mede zijn eigen "
        "eerdere beleid.",
        "Begrenzend: het bericht vermeldt de institutionele inbedding wél "
        "(oud-minister van Volksgezondheid), dus van verhulling is geen "
        "sprake; de casus illustreert het subtielere punt dat continuïteit "
        "tussen eigen beleid en het te duiden rapport onbenoemd blijft. Eén "
        "artikel, geen inhoudsanalyse — daarom contextual met beperkt "
        "gewicht.", 0.4,
        [(SRC_NOS,
          "Kuipers, die na de coronacrisis minister werd in het "
          "kabinet-Rutte IV, vergelijkt de te nemen stappen met de "
          "'pandemische paraatheid' waar hij destijds geld voor vrijmaakte. "
          "'Dat kun je nu misschien beter vertalen als crisisparaatheid.'",
          "passage uit het ANP/NOS-bericht van 17 mei 2026; kop, datum, "
          "sprekers en openingszinnen geverifieerd via nos.nl, passage "
          "overgenomen uit een integrale kopie van het bericht")])

    add_arg("mechanism_id", M_SCHIJNDEBAT, "contextual",
        "Het klimaat-gezondheidsbericht van 17 mei 2026 is een publiek "
        "waarneembaar spoor van eenstemmige sourcing: alle geciteerde "
        "stemmen (commissie, commissielid, instemmend adviesorgaan) komen "
        "uit dezelfde institutionele keten; een onafhankelijke tegenstem of "
        "toetsende buitenstaander ontbreekt.",
        "Het bureauredactiebericht (ANP-vermelding, geen byline) bevat als "
        "enige relativering de slotzin dat landen en de WHO de oproepen "
        "naast zich neer kunnen leggen. De uniformiteit is verklaarbaar uit "
        "kosten- en persmomentroutines (voorverpakte citaten, zelfde-dag-"
        "publicatie) en vereist geen redactionele opzet. Begrenzend: één "
        "artikel; over de bredere NOS-klimaatverslaggeving zegt deze casus "
        "niets — daarom contextual met beperkt gewicht.", 0.4,
        [(SRC_NOS,
          "De urgentie die uit dit rapport spreekt, sluit naadloos aan bij "
          "onze eigen bevindingen.",
          "reactie van RVS-voorzitter Bussemaker in het bericht van 17 mei "
          "2026; spreker geverifieerd via nos.nl, passage overgenomen uit "
          "een integrale kopie van het bericht"),
         (SRC_NOS,
          "Landen en de WHO kunnen de oproepen van de commissie naast zich "
          "neerleggen.",
          "slotzin van het bericht — de enige relativering; passage "
          "overgenomen uit een integrale kopie van het bericht")])

    # -- praktijk --------------------------------------------------------------
    add_arg("relation_id", R_KUIPERS_WHO, "supporting",
        "Ernst Kuipers is lid van de Pan-European Commission on Climate and "
        "Health van WHO/Europa (gelanceerd 11 juni 2025).",
        "Publiek gedocumenteerd: zowel het commissieoverzicht van WHO/Europe "
        "als onafhankelijke berichtgeving (Delta TU Delft; ANP/NOS noemt hem "
        "als commissielid) bevestigen het lidmaatschap.", 0.6,
        [(SRC_DELTA,
          "Kuipers is lid van de Pan-European Commission on Climate and "
          "Health; de aanbevelingen verschenen in The Lancet.",
          "typering van het Delta-artikel; geen letterlijk citaat"),
         (SRC_WHO,
          "Pan-European Commission on Climate and Health, gelanceerd 11 juni "
          "2025, voorzitter Katrín Jakobsdóttir.",
          "typering van de WHO/Europe-commissiepagina; geen letterlijk "
          "citaat")])

    add_arg("relation_id", R_BUSSEMAKER_RVS, "supporting",
        "Jet Bussemaker is sinds 1 juni 2019 voorzitter van de RVS, na een "
        "loopbaan als minister van OCW en staatssecretaris van VWS.",
        "Publiek gedocumenteerd op de profielpagina van het adviesorgaan "
        "zelf.", 0.6,
        [(SRC_RVS_PROFIEL,
          "Voorzitter RVS sinds 1 juni 2019; eerder minister van OCW "
          "(2012-2017) en staatssecretaris van VWS (2007-2010).",
          "typering van de RVS-profielpagina; geen letterlijk citaat")])

    add_arg("relation_id", R_WHO_NOS, "supporting",
        "NOS bericht op gezag van WHO-organen: het bericht van 17 mei 2026 "
        "verscheen op de dag van de Call to Action en volgt het "
        "commissiemateriaal.",
        "De zelfde-dag-publicatie met de kernframes uit het "
        "commissiemateriaal documenteert de sourcing-route; de feitelijke "
        "aanlevering liep via het ANP (de schakel ANP→NOS bestaat al als "
        "pakketjournalistiek-relatie).", 0.5,
        [(SRC_NOS, NOS_OPENING,
          "letterlijke openingszinnen; ANP-vermelding en publicatiedatum "
          "17 mei 2026, 20:17 geverifieerd via nos.nl"),
         (SRC_WHO,
          "Call to Action gepubliceerd op 17 mei 2026.",
          "typering van de WHO/Europe-commissiepagina; geen letterlijk "
          "citaat")])

    add_arg("relation_id", R_RVS_NOS, "supporting",
        "De RVS levert de instemmende binnenlandse duiding bij het "
        "WHO-klimaatrapport; het adviesorgaan agendeerde hetzelfde thema al "
        "in juli 2025 met 'Te heet onder onze voeten'.",
        "In het bericht van 17 mei 2026 reageert de RVS-voorzitter "
        "instemmend ('sluit naadloos aan bij onze eigen bevindingen'); het "
        "eigen advies van juli 2025 documenteert dat het adviesorgaan het "
        "thema zelfstandig op de agenda had gezet.", 0.5,
        [(SRC_NOS,
          "De urgentie die uit dit rapport spreekt, sluit naadloos aan bij "
          "onze eigen bevindingen.",
          "reactie van RVS-voorzitter Bussemaker; passage overgenomen uit "
          "een integrale kopie van het bericht"),
         (SRC_RVS_ADVIES,
          "Planetaire ongezondheid bedreigt rechtstreeks de menselijke "
          "gezondheid; gezond samenleven kan alleen op een gezonde planeet.",
          "typering van de kernboodschap van het RVS-advies (21 juli 2025); "
          "geen letterlijk citaat")])

    con.commit()

    # ---- SAMENVATTING --------------------------------------------------------
    print("---")
    for label, q in (
        ("entities", "SELECT COUNT(*) FROM entities"),
        ("relations", "SELECT COUNT(*) FROM relations"),
        ("arguments", "SELECT COUNT(*) FROM arguments"),
        ("citations", "SELECT COUNT(*) FROM citations"),
        ("sources", "SELECT COUNT(*) FROM sources"),
        ("source_locations", "SELECT COUNT(*) FROM source_locations"),
    ):
        print(f"{label:17s}: {cur.execute(q).fetchone()[0]}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
