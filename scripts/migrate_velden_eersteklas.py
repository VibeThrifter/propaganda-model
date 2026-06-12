"""
Emergente velden worden eersteklas theorie-elementen (modelreview juni 2026).

Velden (hyperedges) waren het enige elementtype zonder eigen discussieboom: argumenten
konden alleen op relaties, entiteiten, rollen en mechanismen hangen, waardoor de
onderbouwing van een veld in de beschrijvingstekst en op aangrenzende mechanismen
leefde. Tijd hadden velden al (active_from/until + tijdbalk); bronnen en score niet.

Drie stappen:

1. ARGUMENTS-REBUILD. `arguments` krijgt een vijfde doelkolom `emergent_effect_id`
   (+ uitgebreide CHECK + index). SQLite kan een CHECK niet wijzigen, dus herbouw
   volgens het recept van migrate_schema_pariteit: nieuwe tabel, data overzetten,
   hernoemen, indexen terugzetten, foreign_key_check.

2. TWEEDE-ORDE-STRUCTUUR. Nieuwe koppeltabel `emergent_effect_subeffects`; het
   apex-veld `fabricage_van_instemming` krijgt de elf overige velden als formele
   deel-effecten. Zo zit de Haagse kaasstolp (haagse_stam, medialogica, …) — en
   daarmee politicus, voorlichter en lobbyist — wél in het apex-effect, zonder
   alles-omvattende ledenset of dubbeltelling. De ledenset blijft pars pro toto.

3. EIGEN DISCUSSIEBOOM PER VELD. Elk van de twaalf velden krijgt een
   literatuur-argument mét citaties uit zijn canonieke bron(nen) — dezelfde
   literatuur die de doc-tabel per veld noemt. De veldscore (scoring.py) bouwt
   hierop: literatuurpoot, geen praktijklaag (velden hebben geen instanties).

Idempotent; backup-then-migrate. Daarna: python3 scripts/generate_viz.py
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

CONTRIB = "modelreview-velden-eersteklas-2026-06"
APEX = "fabricage_van_instemming"

# Nieuwe arguments-DDL: identiek aan de live tabel + emergent_effect_id (kolom,
# CHECK-uitbreiding). Ook in schema.sql voor verse builds.
ARGUMENTS_DDL = """
CREATE TABLE arguments_nieuw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relation_id INTEGER REFERENCES relations(id),
    entity_id INTEGER REFERENCES entities(id),
    role_id INTEGER REFERENCES roles(id),
    mechanism_id INTEGER REFERENCES mechanisms(id),
    emergent_effect_id INTEGER REFERENCES emergent_effects(id),
    parent_argument_id INTEGER REFERENCES arguments(id),
    property TEXT CHECK(property IN (
        'existence',
        'active_from',
        'active_until',
        'certainty',
        'influence',
        'relation_type',
        'description',
        'type',
        'role',
        'indirecte_invloed_op'
    )),
    property_value TEXT,
    stance TEXT NOT NULL CHECK(stance IN (
        'supporting',
        'contradicting',
        'contextual'
    )),
    claim TEXT NOT NULL,
    title TEXT,
    reasoning TEXT,
    weight REAL CHECK(weight BETWEEN 0.0 AND 1.0),
    status TEXT NOT NULL DEFAULT 'ongecontroleerd' CHECK(status IN (
        'ongecontroleerd',
        'bronvermelding_nodig',
        'betwist',
        'geverifieerd',
        'verouderd',
        'verworpen'
    )),
    self_merged BOOLEAN NOT NULL DEFAULT FALSE,
    contributed_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (relation_id IS NOT NULL OR entity_id IS NOT NULL
        OR role_id IS NOT NULL OR mechanism_id IS NOT NULL
        OR emergent_effect_id IS NOT NULL)
)
"""

OUDE_KOLOMMEN = ("id, relation_id, entity_id, role_id, mechanism_id, "
                 "parent_argument_id, property, property_value, stance, claim, "
                 "title, reasoning, weight, status, self_merged, contributed_by, "
                 "created_at")

ARGUMENT_INDEXEN = [
    "CREATE INDEX idx_arguments_relation ON arguments(relation_id)",
    "CREATE INDEX idx_arguments_entity ON arguments(entity_id)",
    "CREATE INDEX idx_arguments_role ON arguments(role_id)",
    "CREATE INDEX idx_arguments_mechanism ON arguments(mechanism_id)",
    "CREATE INDEX idx_arguments_emergent ON arguments(emergent_effect_id)",
    "CREATE INDEX idx_arguments_parent ON arguments(parent_argument_id)",
    "CREATE INDEX idx_arguments_stance ON arguments(stance)",
    "CREATE INDEX idx_arguments_status ON arguments(status)",
]

SUBEFFECTS_DDL = """
CREATE TABLE IF NOT EXISTS emergent_effect_subeffects (
    parent_effect_id INTEGER NOT NULL REFERENCES emergent_effects(id) ON DELETE CASCADE,
    child_effect_id  INTEGER NOT NULL REFERENCES emergent_effects(id) ON DELETE CASCADE,
    PRIMARY KEY (parent_effect_id, child_effect_id),
    CHECK (parent_effect_id != child_effect_id)
)
"""

APEX_DESC_SUFFIX = (
    " De elf overige emergente velden zijn er formeel als deel-effecten aan "
    "gekoppeld (emergent_effect_subeffects): de kaasstolp-lussen (haagse_stam, "
    "toeschouwersdemocratie, medialogica, lobbymakelaardij), de uniformerings- en "
    "homogeniteitsvelden (schijnpluriformiteit, ideologische_homofilie, "
    "voorlichtingsovermacht) en de versterkings- en disciplineringslussen "
    "(zelfversterkende_homeostase, mediahype, verkillingsspiraal, economische "
    "feedback-loop) — politicus, voorlichter en lobbyist doen dus volop mee, via "
    "hún velden."
)

# Canonieke bronnen per veld, geresolved op exacte titel.
BRON_TITELS = {
    "hc": "Manufacturing Consent: The Political Economy of the Mass Media",
    "bergman": "De Nederlandse Nieuwsfabriek: Onthulling van het propagandamodel",
    "luyendijk": "Je hebt het niet van mij, maar...: Achter de schermen van de "
                 "Haagse politiek",
    "boumans": "Outsourcing the news? An empirical assessment of the role of "
               "sources and news agencies in the contemporary news landscape",
    "bw": "Diplomademocratie. Over de spanning tussen meritocratie en democratie",
    "vasterman": "Mediahype",
    "rmo": "Medialogica. Over het krachtenveld tussen burgers, media en politiek",
    "persveilig": "Agressie en bedreiging richting journalisten",
    "oremus": "Verhouding communicatieprofessionals-journalisten. Wat zeggen de "
              "cijfers?",
    "dnr": "Digital News Report Nederland 2025",
    "vis": "Haagse waakhonden. Politieke voorkeur, zelfbeeld van en "
           "informatiegaring van parlementair journalisten",
    "hermans": "Journalists in the Netherlands. Country report "
               "(Worlds of Journalism Study)",
}


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def rebuild_arguments(conn):
    kolommen = {r[1] for r in conn.execute("PRAGMA table_info(arguments)")}
    if "emergent_effect_id" in kolommen:
        print("= arguments heeft emergent_effect_id al, rebuild overslaan")
        return
    voor = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("BEGIN")
    conn.execute(ARGUMENTS_DDL)
    conn.execute(f"INSERT INTO arguments_nieuw ({OUDE_KOLOMMEN}) "
                 f"SELECT {OUDE_KOLOMMEN} FROM arguments")
    conn.execute("DROP TABLE arguments")
    conn.execute("ALTER TABLE arguments_nieuw RENAME TO arguments")
    for index_sql in ARGUMENT_INDEXEN:
        conn.execute(index_sql)
    na = conn.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    if na != voor:
        conn.execute("ROLLBACK")
        sys.exit(f"Rijverlies ({voor} -> {na}): teruggedraaid.")
    fk_problemen = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_problemen:
        conn.execute("ROLLBACK")
        sys.exit(f"foreign_key_check faalde: {fk_problemen[:5]} — teruggedraaid.")
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    print(f"~ arguments herbouwd met emergent_effect_id ({na} rijen)")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")

    # ---- 1: arguments-rebuild ------------------------------------------------
    rebuild_arguments(con)
    cur = con.cursor()

    def veld_id(name):
        row = cur.execute("SELECT id FROM emergent_effects WHERE name=?", (name,)).fetchone()
        if row is None:
            raise SystemExit(f"FOUT: emergent effect '{name}' niet gevonden.")
        return row[0]

    def source_id(key):
        row = cur.execute("SELECT id FROM sources WHERE title=?", (BRON_TITELS[key],)).fetchone()
        if row is None:
            raise SystemExit(f"FOUT: bron '{key}' niet gevonden ({BRON_TITELS[key][:50]}…).")
        return row[0]

    # ---- 2: tweede-orde-structuur (apex + deel-effecten) ----------------------
    cur.execute(SUBEFFECTS_DDL)
    apex_id = veld_id(APEX)
    n_nieuw = 0
    for (cid,) in cur.execute("SELECT id FROM emergent_effects WHERE id != ?", (apex_id,)).fetchall():
        n_nieuw += cur.execute(
            "INSERT OR IGNORE INTO emergent_effect_subeffects (parent_effect_id, child_effect_id) "
            "VALUES (?,?)", (apex_id, cid)).rowcount
    print(f"+ deel-effecten gekoppeld aan {APEX}: {n_nieuw} nieuw")

    desc = cur.execute("SELECT description FROM emergent_effects WHERE id=?", (apex_id,)).fetchone()[0]
    if APEX_DESC_SUFFIX.strip() not in desc:
        cur.execute("UPDATE emergent_effects SET description=? WHERE id=?",
                    (desc + APEX_DESC_SUFFIX, apex_id))
        print("~ apex-beschrijving uitgebreid met deel-effecten")

    # ---- 3: eigen discussieboom per veld --------------------------------------
    def add_veld_arg(veld_name, claim, reasoning, weight, citations):
        eid = veld_id(veld_name)
        if cur.execute("SELECT 1 FROM arguments WHERE emergent_effect_id=? AND claim=?",
                       (eid, claim)).fetchone():
            print(f"= argument bestaat al bij veld {veld_name}")
            return
        cur.execute(
            """INSERT INTO arguments (emergent_effect_id, stance, claim, reasoning,
               weight, status, contributed_by)
               VALUES (?,'supporting',?,?,?,'ongecontroleerd',?)""",
            (eid, claim, reasoning, weight, CONTRIB))
        aid = cur.lastrowid
        for skey, quote, page, ctx in citations:
            cur.execute(
                "INSERT INTO citations (argument_id, source_id, quote, page, context) "
                "VALUES (?,?,?,?,?)", (aid, source_id(skey), quote, page, ctx))
        print(f"+ argument bij veld {veld_name} ({len(citations)} citatie(s))")

    add_veld_arg(
        "fabricage_van_instemming",
        "De vijf filters produceren samen een nieuwsbeeld dat de instemming van "
        "het publiek met de bestaande orde organiseert — als emergente uitkomst, "
        "zonder centrale regie.",
        "Kernthese van het propagandamodel; de filters zijn elk afzonderlijk "
        "onderbouwd, dit argument draagt de compositie op systeemniveau.",
        0.70,
        [("hc",
          "Typering: nieuws passeert opeenvolgende filters (eigendom, advertenties, "
          "bronnen, flak, ideologie); wat overblijft is het residu dat de premissen "
          "van de gevestigde macht reproduceert.",
          None, "kernthese Manufacturing Consent (1988); typering, geen letterlijk citaat")])

    add_veld_arg(
        "zelfversterkende_homeostase",
        "Het Nederlandse mediasysteem corrigeert afwijkingen van de consensus "
        "vanzelf: socialisatie, redactieroutines en publieksverwachting brengen "
        "het narratief terug naar het evenwicht dat elite-belangen dient.",
        "Bergman past het propagandamodel op Nederland toe en laat de "
        "terugkeer-naar-evenwicht-dynamiek zien zonder censor of regie.",
        0.60,
        [("bergman",
          "Typering: ook zonder censor keert de Nederlandse journalistiek na "
          "incidentele uitschieters terug naar de gevestigde consensus — de "
          "correctie zit in de structuur, niet in een ingreep.",
          None, "Bergman (2014); typering, geen letterlijk citaat")])

    add_veld_arg(
        "haagse_stam",
        "Politici, voorlichters, lobbyisten en journalisten op het Binnenhof "
        "functioneren als één stam met gedeelde codes en wederzijdse "
        "afhankelijkheid — en de stam beschermt zichzelf.",
        "Luyendijks etnografische kernbevinding; de lobby wordt zelf vrijwel "
        "nooit gecoverd, waardoor de stam voor het publiek onzichtbaar blijft.",
        0.70,
        [("luyendijk",
          "Typering: het Binnenhof is een dorp met ongeschreven regels; wie de "
          "regels breekt verliest zijn toegang — en de lobby blijft buiten beeld.",
          None, "Je hebt het niet van mij, maar... (2010); typering, geen letterlijk citaat")])

    add_veld_arg(
        "toeschouwersdemocratie",
        "Het publiek ziet van de politiek vooral de frontstage-opvoering; de "
        "werkelijke afweging gebeurt backstage, in wandelgangen en "
        "achtergrondgesprekken.",
        "Luyendijks toneelmetafoor: politiek richt zich op de camera, "
        "voorlichting bewaakt het beeld, journalistiek verslaat de opvoering.",
        0.65,
        [("luyendijk",
          "Typering: debat en Kamervraag zijn de voorstelling; de besluiten "
          "vallen backstage, waar camera's en publiek niet komen.",
          None, "Je hebt het niet van mij, maar... (2010); typering, geen letterlijk citaat")])

    add_veld_arg(
        "lobbymakelaardij",
        "De lobbyist regisseert journalist én politicus tegelijk namens een "
        "opdrachtgever die buiten beeld blijft: het verhaal wordt geplant, de "
        "Kamervraag aangeleverd, en publicatie en politieke reactie bevestigen "
        "elkaar.",
        "De gelijktijdige regie over beide kanten is een eigenschap van de "
        "driehoek; geen van beide losse paden vangt haar.",
        0.65,
        [("luyendijk",
          "Typering: 'je hebt het niet van mij, maar...' — hetzelfde belang "
          "verschijnt tegelijk als onafhankelijk nieuws en als politiek feit, "
          "zonder zichtbare afzender.",
          None, "Je hebt het niet van mij, maar... (2010); typering, geen letterlijk citaat")])

    add_veld_arg(
        "schijnpluriformiteit",
        "Circa twee derde van het online nieuws op grote Nederlandse sites was "
        "in 2014 gebaseerd op ANP-kopij, veelal vrijwel integraal overgenomen — "
        "veel titels, één nieuwsstroom.",
        "Boumans kwantificeert de ANP-afhankelijkheid die de ervaren "
        "pluriformiteit tot façade maakt.",
        0.75,
        [("boumans",
          "Typering van de kernbevinding: ±66% van het online nieuws op "
          "volkskrant.nl, nu.nl en telegraaf.nl in 2014 was ANP-gebaseerd, "
          "grotendeels integraal overgenomen.",
          None, "Outsourcing the news? (2016); typering, geen letterlijk citaat")])

    add_veld_arg(
        "ideologische_homofilie",
        "Journalist, expert, politicus en denktanker komen uit dezelfde "
        "academische vormingsinstituten en wijken als groep ideologisch af van "
        "de bevolking; onderlinge bevestiging oogt als onafhankelijke "
        "verificatie.",
        "Drie bewijslijnen: de diplomademocratie-these (Bovens & Wille), de "
        "stemvoorkeur van parlementair journalisten (Vis) en de samenstelling "
        "van het corps (WJS/Hermans).",
        0.65,
        [("bw",
          "Typering: Nederland ontwikkelt zich tot een diplomademocratie — "
          "academici domineren politiek, bestuur en de instituties daaromheen.",
          None, "kernthese Bovens & Wille (2011); typering, geen letterlijk citaat"),
         ("vis",
          "Typering: parlementair journalisten wijken in politieke voorkeur "
          "sterk af van het electoraat — D66 27% tegenover 9% landelijk, "
          "GroenLinks 14% tegenover 7,3% (TK1998).",
          "pp. 114-136",
          "cijfers zoals aangehaald in de veldbeschrijving; typering, geen letterlijk citaat"),
         ("hermans",
          "Typering: de Nederlandse journalist is overwegend hoogopgeleid, met "
          "gemiddeld bijna 19 jaar ervaring — het corps is demografisch en qua "
          "vorming opvallend eenvormig.",
          None, "WJS-landenrapport NL (golf 2012-2016); typering van de samenstellingsbevindingen")])

    add_veld_arg(
        "mediahype",
        "Na een sleutelgebeurtenis jagen media elkaars aandacht aan tot een "
        "zelfversterkende nieuwsgolf die losraakt van de onderliggende "
        "werkelijkheid (pack journalism).",
        "Vastermans kernmechanisme: positieve feedback — iets is nieuws ómdat "
        "andere media het groot brengen.",
        0.70,
        [("vasterman",
          "Typering van de kernthese: een mediahype is een mediabrede, zichzelf "
          "versterkende nieuwsgolf die groeit zonder nieuwe feiten, aangejaagd "
          "doordat media elkaars aandacht als bewijs van nieuwswaarde nemen.",
          None, "Vasterman (2004); typering, geen letterlijk citaat")])

    add_veld_arg(
        "medialogica",
        "Politiek en media houden elkaar in een wurggreep: het parlement "
        "reageert op wat gisteren in de media stond, media verslaan een "
        "politiek die zich op de camera richt — een gevangenendilemma.",
        "Institutionele bevestiging (RMO 2003) van de lus; niemand kan eruit "
        "zolang de anderen meedoen.",
        0.70,
        [("rmo",
          "Politiek en media zitten gevangen in een patroon van medialogica; "
          "personen, conflicten en incidenten verdringen inhoud en "
          "langetermijnbeleid.",
          None, "kernbevinding RMO Medialogica (2003); typering, geen letterlijk rapportcitaat")])

    add_veld_arg(
        "verkillingsspiraal",
        "Externe agressie en interne risicomijdendheid versterken elkaar: 8 op "
        "de 10 journalisten ervaart agressie of bedreiging, 16% past de "
        "berichtgeving aan en circa 15% publiceert soms niet.",
        "Het collectieve chilling effect overstijgt de individuele "
        "zelfcensuur-halo: hele onderwerpen verdwijnen uit de berichtgeving.",
        0.75,
        [("persveilig",
          "8 op de 10 respondenten heeft ervaring met geweld of bedreiging in "
          "de journalistiek; 16% past de berichtgeving aan, ongeveer 15% "
          "publiceert soms niet.",
          None, "kernbevindingen PersVeilig/I&O (2021); typering, geen letterlijk rapportcitaat")])

    add_veld_arg(
        "voorlichtingsovermacht",
        "Tegenover circa 150.000 communicatieprofessionals staan circa 15.000 "
        "journalisten; de checkende kant kan het aanbod van de zendende kant "
        "structureel niet bijhouden.",
        "De Villamedia-analyse bundelt de UvA- en CBS-tellingen; de effectieve "
        "overmacht ligt lager (interne communicatie meegeteld) maar blijft een "
        "veelvoud.",
        0.70,
        [("oremus",
          "Typering: de tellingen komen uit op ±150.000 communicatieprofessionals "
          "(CBS 2017: 149.000) tegenover ±15.000 journalisten — ruwweg tien "
          "zenders op één checker.",
          None, "Villamedia-analyse (2018) van UvA/CBS-cijfers; typering, geen letterlijk citaat")])

    add_veld_arg(
        "economische_feedback_loop",
        "Dalende nieuwsinteresse en nieuwsmijding verkleinen de betalende "
        "basis, waarna bezuinigingen de journalistiek verzwakken en het "
        "vertrouwen verder daalt — een zichzelf versterkende spiraal.",
        "De lus zelf is systeemtheorie-duiding; de instroomkant (nieuwsmijding, "
        "dalende interesse) is empirisch gedocumenteerd in het Digital News "
        "Report NL.",
        0.55,
        [("dnr",
          "Typering: de nieuwsinteresse onder 18-34-jarigen halveerde in vier "
          "jaar (61% naar 33%); wie nieuws mijdt, betaalt er ook niet voor — de "
          "financiële basis onder de journalistiek versmalt structureel.",
          None, "CvdM Digital News Report NL 2025; typering — de lus zelf is systeemtheorie-duiding")])

    con.commit()

    # ---- samenvatting --------------------------------------------------------
    for label, q in (
        ("arguments", "SELECT COUNT(*) FROM arguments"),
        ("veld-argumenten", "SELECT COUNT(*) FROM arguments WHERE emergent_effect_id IS NOT NULL"),
        ("citations", "SELECT COUNT(*) FROM citations"),
        ("deel-effecten", "SELECT COUNT(*) FROM emergent_effect_subeffects"),
    ):
        print(f"{label:16s}: {cur.execute(q).fetchone()[0]}")
    con.close()
    print("klaar. Vergeet niet: python3 scripts/generate_viz.py")


if __name__ == "__main__":
    main()
