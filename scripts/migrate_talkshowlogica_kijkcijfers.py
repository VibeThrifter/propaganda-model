#!/usr/bin/env python3
"""
Migratie: talkshowlogica & kijkcijferdisciplinering (juni 2026).

Aanleiding: interview De Nieuwe Wereld — Talitha Muusse (oud-presentator
Op1) in gesprek met Victor Vlam (media-analist/kijkcijferduider) over de
talkshowwereld. Eerstehands getuigenissen over werkwijze (minutenanalyse,
gastselectie, voorgesprekken, exclusiviteitscontracten) plus duidingen.

Bronwaardering: primaire getuigenis voor de wérkwijze, maar (a) beide
sprekers zijn zelf partij (beiden NPO-kritisch; Muusse heeft een
persoonlijk conflict met Op1/NPO), (b) het is een opinieprogramma,
(c) ASR-transcript zonder sprekerlabels. Daarom gewichten 0.4-0.5;
de NPO-druk-anekdote 0.3 (anoniem, niet onafhankelijk verifieerbaar).
Algemene duidingen ("NPO is links") zijn NIET als feit opgenomen.
Het kijkcijferpanel-feit is extra gestaafd met de NMO-methodepagina's
(institutioneel; 1.850 huishoudens, ca. 3.900 personen 6+).

Wat deze migratie doet:

1. BRONNEN: het DNW-transcript (primair; bestand in sources/, afleverings-
   URL nog te bevestigen) en de NMO-methodepagina's (institutioneel).

2. DRIE NIEUWE MECHANISMEN (architectuurkeuze: theorie blijft abstract op
   rolniveau; formats als talkshow/krant worden GEEN rollen — een
   talkshowprogramma kan later als praktijk-entiteit worden opgenomen
   zodra er een geverifieerde, scoorbare relatie is):
   - kijkcijferdisciplinering (advertentie, economisch, direct,
     publiek -> redactie): per minuut gemeten zapgedrag disciplineert
     redactionele keuzes; platformonafhankelijk (YouTube-views idem).
     Eerste uitgaande pijl van het publiek in het model.
   - mediageniekheidsselectie (sourcing + extra advertentie, procedureel,
     direct, redactie -> gezagsexpert): tafelgasten geselecteerd op vorm/
     amusementswaarde i.p.v. expertise; vaste-duiderspool met
     exclusiviteitscontracten.
   - conflictregie (ideologie + extra advertentie, discursief, direct,
     redactie -> publiek): enscenering van conflict (gescheiden houden,
     aandikken in het voorgesprek, tafelopstelling). Complement van
     schijndebat: daar onbalans, hier gefabriceerd conflict.

3. ARGUMENTEN bij bestaande mechanismen (eerstehands bevestiging):
   zelfcensuur (14), sociologische_homogeniteit (63), etikettering (13),
   schijndebat (17), spectrum_bewaking (35; incl. de NPO-druk-anekdote
   als apart argument met gewicht 0.3 en expliciete kanttekening),
   media_agendering (148), intermedia_agendering (157).

Bewust NIET opgenomen: programma-entiteiten of personen zonder scoorbare
relatie; praktijkrelaties op basis van anonieme anekdotes; nieuwe rollen
(duider = columnist_opiniemaker, talkshowredactie = redactie, de
presentator-als-itemkiezer valt onder hoofdredacteur_als_filter).

Backup-then-migrate; idempotent; tweemaal draaien verandert niets.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-talkshowlogica-2026-06"
ACCESSED = "2026-06-11"


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

    # ---- 1. BRONNEN ----------------------------------------------------------
    def add_source(title, stype, author, publisher, date, reliability,
                   locations=(), summary=None, language="nl"):
        row = cur.execute("SELECT id FROM sources WHERE title=?",
                          (title,)).fetchone()
        if row:
            print(f"bron bestaat al: {title[:55]}")
            return row[0]
        cur.execute(
            """INSERT INTO sources (title, author, source_type, publisher,
               date_published, language, summary, reliability)
               VALUES (?,?,?,?,?,?,?,?)""",
            (title, author, stype, publisher, date, language, summary,
             reliability))
        sid = cur.lastrowid
        for loc_type, loc, notes in locations:
            cur.execute(
                """INSERT INTO source_locations (source_id, location_type,
                   location, accessed_at, notes) VALUES (?,?,?,?,?)""",
                (sid, loc_type, loc, ACCESSED, notes))
        print(f"+ bron {sid}: {title[:55]}")
        return sid

    S_DNW = add_source(
        "De Nieuwe Wereld: Talitha Muusse en Victor Vlam over de "
        "talkshowwereld",
        "transcript", "Talitha Muusse & Victor Vlam (De Nieuwe Wereld)",
        "De Nieuwe Wereld", "2026-06-10", "primair",
        locations=[
            ("file", "sources/2026-06-10_vlam-muusse_talkshowwereld.txt",
             "ASR-transcript zonder sprekerlabels; datering benaderd "
             "(opname tussen eind mei en 10 juni 2026, o.b.v. interne "
             "verwijzingen); afleverings-URL op het DNW-kanaal nog toe "
             "te voegen zodra gepubliceerd/gevonden.")],
        summary="Gesprek over de talkshowwereld: minutenanalyse en "
                "kijkcijferdiscipline, gastselectie op mediageniekheid, "
                "vaste duiders met exclusiviteitscontracten, conflictregie "
                "in voorgesprekken, signatuur van talkshows, cancelcultuur "
                "en zelfcensuur. Eerstehands getuigenissen (Muusse: Op1; "
                "Vlam: kijkcijferanalist en talkshowgast), maar beide "
                "sprekers zijn zelf partij en het is een opinieprogramma — "
                "gebruikt voor werkwijze-getuigenissen, niet voor de "
                "algemene duidingen.")
    S_NMO = add_source(
        "NMO Kijken — panel en meetmethode",
        "website", "Nationaal Media Onderzoek (NMO)",
        "Nationaal Media Onderzoek", None, "institutioneel",
        locations=[
            ("url", "https://www.nationaalmediaonderzoek.nl/"
             "nmo-kijken-panel", "Panelomvang en representativiteit."),
            ("url", "https://www.nationaalmediaonderzoek.nl/"
             "nmo-kijken-hoe-wordt-gemeten",
             "Meetmethode (audiomatching, aanmelden panelleden).")],
        summary="Officiële methodebeschrijving van het Nederlandse "
                "kijkonderzoek: panel van 1.850 huishoudens (ca. 3.900 "
                "personen, 6+), representatief samengesteld o.b.v. CBS-"
                "gegevens; kijkmeter registreert via audiomatching het "
                "kijkgedrag van afzonderlijke respondenten.")

    # ---- 2. NIEUWE MECHANISMEN -----------------------------------------------
    def add_mechanism(name, filter_, mtype, aard, src_role, tgt_role,
                      description, effect, extra_filters=()):
        row = cur.execute("SELECT id FROM mechanisms WHERE name=?",
                          (name,)).fetchone()
        if row:
            print(f"mechanisme bestaat al: {name}")
            return row[0]
        cur.execute(
            """INSERT INTO mechanisms (name, filter, mechanism_type,
               description, effect, source_role_id, target_role_id, aard)
               VALUES (?,?,?,?,?,?,?,?)""",
            (name, filter_, mtype, description, effect,
             roles[src_role] if src_role else None, roles[tgt_role], aard))
        mid = cur.lastrowid
        cur.execute("INSERT INTO mechanism_filters (mechanism_id, filter) "
                    "VALUES (?,?)", (mid, filter_))
        for f in extra_filters:
            cur.execute("INSERT INTO mechanism_filters (mechanism_id, "
                        "filter) VALUES (?,?)", (mid, f))
        print(f"+ mechanisme {mid}: {name} ({aard})")
        return mid

    M_KIJK = add_mechanism(
        "kijkcijferdisciplinering", "advertentie", "economisch", "direct",
        "publiek", "redactie",
        "Het per minuut gemeten kijkgedrag van het publiek disciplineert "
        "de redactie. Het NMO-panel (1.850 huishoudens, ca. 3.900 "
        "personen) levert dagcijfers en minutenanalyses per item en per "
        "spreker; redacties evalueren gasten als 'wegzepper' en beslissen "
        "op zapgedrag wie terugkomt en welke onderwerpen sneuvelen. Bij "
        "commerciële zenders is het kijkcijfer de advertentievaluta "
        "(reclameblok-plaatsing wordt erop geoptimaliseerd); bij de "
        "publieke omroep werkt dezelfde tucht via legitimatie en "
        "Ster-inkomsten. Platformonafhankelijk: view-duration-metrics op "
        "YouTube en podcastplatforms zijn hetzelfde mechanisme. NB: de "
        "enige uitgaande pijl van het publiek in het model — het publiek "
        "stuurt mee, maar alleen langs de dimensie die gemeten en "
        "gemonetariseerd wordt (aandacht, niet kwaliteit).",
        "Gastselectie, onderwerpkeuze en itemvolgorde worden "
        "geoptimaliseerd op zapgedrag in plaats van maatschappelijk "
        "belang; trage, complexe of buitenlandonderwerpen en onbekende "
        "stemmen verliezen structureel terrein.")
    M_GENIEK = add_mechanism(
        "mediageniekheidsselectie", "sourcing", "procedureel", "direct",
        "redactie", "gezagsexpert",
        "Tafelgasten worden geselecteerd op vorm- en amusementscriteria — "
        "smeuïg kunnen vertellen, conflictpotentieel ('een pepertje'), "
        "uiterlijk, bekendheid en een herkenbaar persona ('een karikatuur "
        "van jezelf') — niet primair op inhoudelijke expertise. Politici "
        "en academici gelden als 'saai', buitenland 'boeit niet'; "
        "journalisten en tv-persoonlijkheden domineren de tafels. "
        "Exclusiviteitscontracten binden vaste duiders aan programma's, "
        "waardoor een kleine pool (orde van 150 personen) het "
        "televisiedebat voert. Verwant aan expert_framing en "
        "toegangsdisciplinering, maar het selectiecriterium is hier "
        "amusementswaarde, niet inhoudelijke welgevalligheid; de "
        "drijvende kracht is kijkcijferdisciplinering.",
        "Het publieke debat op televisie wordt gevoerd door duiders in "
        "plaats van experts: wie het leuk kan vertellen wint van wie het "
        "weet. De vaste-duidersconstructie dempt bovendien onderlinge "
        "kritiek: wie volgende week weer aan tafel zit, valt collega's "
        "niet hard aan.",
        extra_filters=("advertentie",))
    M_CONFLICT = add_mechanism(
        "conflictregie", "ideologie", "discursief", "direct",
        "redactie", "publiek",
        "Redactionele enscenering van conflict: gasten met verwachte "
        "botsing worden vóór de uitzending gescheiden gehouden, "
        "standpunten worden in het voorgesprek aangedikt ('geladen'), en "
        "de tafelopstelling stuurt op confrontatie (tegenover elkaar = "
        "discussie, naast elkaar = aanvullen). Het publiek ziet "
        "geregisseerd vuurwerk als ware het spontaan maatschappelijk "
        "debat. Complement van schijndebat: daar een gemanipuleerde "
        "ónbalans die de schijn van open debat wekt, hier gefabriceerd "
        "conflict omwille van de spanning (en dus de kijkcijfers).",
        "Het getoonde 'maatschappelijk debat' is deels een "
        "productiekeuze: standpunten verschijnen scherper en "
        "onverzoenlijker op het scherm dan ze zonder regie aan dezelfde "
        "tafel zouden zijn, wat het publieksbeeld van polarisatie "
        "versterkt.",
        extra_filters=("advertentie",))

    # ---- vervolg in DEEL 2 (argumenten) --------------------------------------
    run_part2(cur, S_DNW, S_NMO, M_KIJK, M_GENIEK, M_CONFLICT)

    con.commit()
    for t in ("mechanisms", "entities", "relations", "arguments",
              "citations", "sources", "source_locations"):
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: {n}")
    con.close()
    print("klaar.")


def run_part2(cur, S_DNW, S_NMO, M_KIJK, M_GENIEK, M_CONFLICT):
    """Argumenten + citaties (deel 2 van de migratie)."""

    def add_arg(mech_id, stance, claim, reasoning, weight, citations):
        row = cur.execute(
            "SELECT id FROM arguments WHERE mechanism_id=? AND claim=?",
            (mech_id, claim)).fetchone()
        if row:
            print(f"argument bestaat al (mechanism_id={mech_id})")
            return row[0]
        cur.execute(
            """INSERT INTO arguments (mechanism_id, stance, claim,
               reasoning, weight, status, contributed_by)
               VALUES (?,?,?,?,?,?,?)""",
            (mech_id, stance, claim, reasoning, weight,
             "ongecontroleerd", CONTRIB))
        aid = cur.lastrowid
        for sid, quote, ctx in citations:
            cur.execute(
                "INSERT INTO citations (argument_id, source_id, quote, "
                "context) VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument ({stance}, w={weight}) bij mechanisme "
              f"{mech_id}, {len(citations)} citatie(s)")
        return aid

    def mech(name):
        return cur.execute("SELECT id FROM mechanisms WHERE name=?",
                           (name,)).fetchone()[0]

    BASE = ("Letterlijk citaat uit het ASR-transcript "
            "(sources/2026-06-10_vlam-muusse_talkshowwereld.txt); niet "
            "onafhankelijk tegen de uitzending geverifieerd; transcript "
            "zonder sprekerlabels — sprekertoeschrijving o.b.v. context. ")
    KANT = ("Kanttekening: opinieprogramma, beide sprekers zelf partij "
            "(NPO-kritisch; Muusse heeft een persoonlijk conflict met "
            "Op1/NPO); gewicht daarom gematigd.")

    # -- kijkcijferdisciplinering ----------------------------------------------
    add_arg(M_KIJK, "supporting",
        "Talkshowredacties evalueren gasten en items op minuten-"
        "kijkcijfers: 'wegzeppers' worden niet teruggevraagd, "
        "reclameblokken worden op het cijfer geoptimaliseerd, en 'alle "
        "keuzes' worden op de minutengrafiek gebaseerd (getuigenis "
        "Muusse/Vlam).",
        "Eerstehands werkwijze-getuigenis van een oud-presentator (Op1) "
        "en een kijkcijferanalist die zelf met deze data werkt; beide "
        "beschrijven onafhankelijk dezelfde praktijk. " + KANT,
        0.5,
        [(S_DNW,
          "Ja, dan de minutenanalyse die krijg je ook, maar die kwam dan "
          "meestal wat later en dan kon je echt precies zien eh daar gaan "
          "wij het ook over hebben, maar afhankelijk van per spreker, per "
          "minuut wie er aan het woord is. En soms zie je dus echt gewoon "
          "van wie is een wegzepper? En dat zo wordt dat dan ook wel "
          "geëvalueerd van nou die eh taxiog gast van gister, dat is "
          "eigenlijk een moment waarop ook een beetje op basis daarvan "
          "wordt bepaald ga je een taxogas nog terughalen of niet.",
          BASE + "Spreker: Muusse (over Op1). ASR-fouten: 'taxiog "
          "gast'/'taxogas' = talkshowgast."),
         (S_DNW,
          "En alle keuzes worden ook op basis van deze grafiekjes "
          "gemaakt.",
          BASE + "Spreker: Vlam, bij de getoonde minutenanalyse."),
         (S_DNW,
          "Eh als je weet dat het kijkcijfer van die aflevering lager "
          "gaat zijn, dan heeft het zin om het reclameblok zoveel "
          "mogelijk naar achteren te verplaatsen.",
          BASE + "Spreker: Vlam, over reclameblok-optimalisatie.")])
    add_arg(M_KIJK, "supporting",
        "Het meetinstrument bestaat en werkt zoals beschreven: het NMO-"
        "kijkonderzoek rapporteert op basis van een representatief panel "
        "van 1.850 huishoudens (ca. 3.900 personen, 6+) en registreert "
        "het kijkgedrag van afzonderlijke respondenten.",
        "Institutionele methodebeschrijving van het meetinstituut zelf; "
        "staaft het instrument en bevestigt Vlams panelcijfers. De "
        "disciplinerende wérking volgt niet uit deze bron maar uit de "
        "getuigenissen (eerste argument).",
        0.55,
        [(S_NMO,
          "Het vernieuwde kijkonderzoek rapporteert op basis van een "
          "panelgrootte van 1.850 huishoudens (ca. 3.900 personen, 6+).",
          "Letterlijk geverifieerd op nationaalmediaonderzoek.nl "
          "(NMO Kijken — Panel), geraadpleegd 2026-06-11."),
         (S_NMO,
          "Op basis van het kijkgedrag van het panel worden uitspraken "
          "gedaan over het kijkgedrag van de totale Nederlandse bevolking "
          "(6 jaar of ouder).",
          "Letterlijk geverifieerd op nationaalmediaonderzoek.nl "
          "(NMO Kijken — Panel), geraadpleegd 2026-06-11."),
         (S_NMO,
          "registreert op basis van audiomatching het kijkgedrag van "
          "afzonderlijke respondenten",
          "Zinsfragment (onderwerp: de kijkmeter) van de pagina 'NMO "
          "Kijken — Hoe wordt gemeten?'; letterlijk geverifieerd, "
          "geraadpleegd 2026-06-11.")])

    # -- mediageniekheidsselectie ----------------------------------------------
    add_arg(M_GENIEK, "supporting",
        "Talkshowgasten worden geselecteerd op vertelkwaliteit, "
        "conflictpotentieel, uiterlijk en persona; politici en academici "
        "gelden als 'saai' en vrouwen werden openlijk als 'risicovoller' "
        "besproken; exclusiviteitscontracten binden vaste duiders "
        "(getuigenis Muusse/Vlam).",
        "Eerstehands van twee kanten: Muusse vanuit de redactiekant "
        "(selectiecriteria zoals achter de schermen besproken), Vlam als "
        "frequente talkshowgast (persona/'karikatuur', pepertje-rol, "
        "contractpraktijk). " + KANT,
        0.45,
        [(S_DNW,
          "Je als je een talkshot überhaupt kijkt, zie je inderdaad "
          "precies wat jij zegt, dat er bijna geen politici en bijna geen "
          "eh professoren/hoogleraren/academici het zijn veel ehm eh "
          "journalisten en televisiepersoonlijkheden die talkshows "
          "domineren.",
          BASE + "Spreker: Vlam. ASR-fout: 'talkshot' = talkshow."),
         (S_DNW,
          "Je hebt ook mensen die een pepertje eh zijn eh nodig. Eh eh "
          "dus die af en toe gewoon eens even er lekker in eh vliegen en "
          "die ervoor kunnen zorgen dat er conflict ontstaat. Want dat "
          "gaat eh ook eh gewoon simpelweg eh scoren.",
          BASE + "Spreker: Vlam, over casting-ingrediënten."),
         (S_DNW,
          "zelfde met vrouwen werd echt openlijk al toch als iets "
          "risicovoller gezien. Ehm ja, werden dus dan minder gevraagd",
          BASE + "Zinsfragment. Spreker: Muusse, over haar redactietijd; "
          "direct erna ook 'Buitenland vinden mensen niet zo boeiend' "
          "als redactieregel."),
         (S_DNW,
          "dat exclusiviteit is ook iets wat de hele talkshow wereld "
          "doorgaat dat iedereen het liefst zijn experts aan zich wil "
          "binden",
          BASE + "Zinsfragment. Spreker: Vlam; noemt vervolgens dat "
          "Pauw & De Wit, Eva, RTL Tonight en Vandaag Inside allemaal "
          "vaste duiders contracteren."),
         (S_DNW,
          "Dus ik denk een goede talkshow gast die moet ook een soort "
          "van karikatuur van zichzelf laten maken.",
          BASE + "Spreker: Vlam; met voorbeelden (laptop als attribuut, "
          "speciale 'tv-hoed' van een natuurduider).")])

    # -- conflictregie -----------------------------------------------------------
    add_arg(M_CONFLICT, "supporting",
        "Redacties regisseren conflict: gasten met verwachte botsing "
        "worden vooraf gescheiden gehouden, standpunten worden in het "
        "voorgesprek aangedikt, en de tafelopstelling stuurt op "
        "confrontatie; Vlam noemt het zelf 'absoluut manipulatie' "
        "(getuigenis Muusse/Vlam).",
        "Eerstehands: Vlam beschrijft een casus waarin hij zelf "
        "gescheiden werd gehouden van zijn opponent; Muusse zag als "
        "presentator/redactielid het aandikken in voorgesprekken. "
        + KANT,
        0.4,
        [(S_DNW,
          "Als als mensen tegenover elkaar aan tafel zitten, heb je "
          "eerder een discussie. Als je ze naast elkaar zet, dan gaan ze "
          "elkaar aanvullen.",
          BASE + "Spreker: Vlam, over sturing via tafelopstelling."),
         (S_DNW,
          "Dus ze hadden haar en mij destijds eh gewoon gescheiden "
          "gehouden, wat ik denk dat een eh slimme zet eh was.",
          BASE + "Spreker: Vlam, over een eigen talkshowoptreden."),
         (S_DNW,
          "Ja, maar ik heb ook wel eens gezien en meegemaakt dat echt "
          "wel ook een beetje wordt aangedikt in het voor door de "
          "redactie bij de ene taxi gast.",
          BASE + "Spreker: Muusse. ASR-fouten: 'in het voor' = in het "
          "voorgesprek; 'taxi gast' = talkshowgast."),
         (S_DNW,
          "Eh het is wel ik denk dat het is absoluut manipulatie.",
          BASE + "Spreker: Vlam; strekking: 'het is absoluut "
          "manipulatie' (ASR-haperingen).")])

    # -- bestaande mechanismen ---------------------------------------------------
    add_arg(mech("zelfcensuur"), "supporting",
        "Getuigenis: redacteuren brengen een afwijkende insteek niet in "
        "als de hoofdredacteur het frame al heeft gezet, en hoogopgeleide "
        "professionals verzwijgen hun (rechtse) stemgedrag — zelfcensuur "
        "als het mechanisme waarlangs cancelcultuur werkt.",
        "Eerstehands beschrijving van het anticiperende conformisme dat "
        "dit mechanisme definieert, hier van binnenuit de redactie- en "
        "opiniemakerswereld. " + KANT,
        0.45,
        [(S_DNW,
          "Ja, zelfcensuur vind ik dat dat volgens mij ook het mechanisme "
          "waarbij eh die kcelcultuur werkt, hè. Dat mensen vooraf "
          "eigenlijk al bij zichzelf denken van: \"Oeh, als ik daar 100% "
          "eerlijk over ben, dan kan ik dus eh uiteindelijk eh mijn "
          "positie daar eh vergeten. Dat is een groot probleem.\"",
          BASE + "Spreker: Vlam. ASR-fout: 'kcelcultuur' = "
          "cancelcultuur."),
         (S_DNW,
          "Als jij nu daar werkt bij de Volkskant en je denkt er net een "
          "slag anders over of je hebt een partner thuis die dat ga jij "
          "niet inbrengen tijdens de vergadering van nou mijn vrouw die "
          "vindt trouwens wel is ook bang voor weet ik veel de komst van "
          "dat van asielzoekcentrum.",
          BASE + "Spreker: Muusse. ASR-fout: 'Volkskant' = Volkskrant."),
         (S_DNW,
          "Ik heb zoveel vrienden die gewoon inderdaad wat meer rechts "
          "van de VVD eh stemmen eh maar die eh gewoon hoogopstellend "
          "geleid en gewoon goede banen hebben. Die vertellen in bijna "
          "alle gevallen niet waar zij op stemmen en die zijn niet "
          "volledig open over een politieke meningen.",
          BASE + "Sprekertoeschrijving onzeker (Muusse of Vlam).")])

    add_arg(mech("sociologische_homogeniteit"), "supporting",
        "Getuigenis/illustratie: mediatop en redacties zijn hoogopgeleid, "
        "Randstedelijk en overwegend progressief; casus RTL Tonight — "
        "vast duiderspanel waarvan de meest rechtse duider een VVD'er is, "
        "geprogrammeerd door een Amsterdamse programmadirecteur, terwijl "
        "RTL een dwarsdoorsnede van Nederland bedient.",
        "Illustreert de blinde-vlek-dynamiek van de halo met een "
        "concrete, falsifieerbare casus (de samenstelling van het "
        "RTL Tonight-panel is controleerbaar). De algemene duiding "
        "('al onze instituties') is een opinie en weegt niet mee als "
        "feit. " + KANT,
        0.45,
        [(S_DNW,
          "al onze instituties worden gedomineerd door progressief "
          "linkse mensen. Dat geldt ook wel voor de journalistiek "
          "uiteraard. Dat zijn ook allemaal mensen hoog opgeleid in de "
          "Randstad. Dus dat correlleert allemaal heel sterk met dat ze "
          "progressief zijn.",
          BASE + "Zinsfragment. Spreker: Vlam (toeschrijving o.b.v. "
          "context)."),
         (S_DNW,
          "Maar RTL Tonight eh heeft een vast eh panel aan duiders "
          "waarbij Albert Vlinde de meest rechtse duider is. En hij is "
          "zoals bekend een VV'er. Daar is op zich niks mis mee. Prima "
          "zijn keuze. Maar dat betekent dat een derde van het "
          "Nederlands electoraat niet vertegenwoordigd wordt door de "
          "vaste duiders van RTL Tonight.",
          BASE + "Spreker: Vlam. ASR-fout: 'Albert Vlinde' = Albert "
          "Verlinde."),
         (S_DNW,
          "Want het is veel te veel het debat in de grachengordel van "
          "Amsterdam in plaats van het debat in de samenleving waar de "
          "RTO kijker wel op zitten wachten.",
          BASE + "Spreker: Vlam. ASR-fouten: 'grachengordel' = "
          "grachtengordel; 'RTO' = RTL.")])

    add_arg(mech("etikettering"), "supporting",
        "Getuigenis: de 'drietrapsraket' van diskwalificaties tegen "
        "rechts-conservatieve stemmen — eerst 'dom', dan 'verdienmodel/"
        "doelgroep bespelen', ten slotte 'racist/xenofoob' — zodat er "
        "altijd een reden is om iemand geen platform te geven.",
        "Beschrijft het mechanisme (labelen i.p.v. weerleggen) als "
        "gefaseerde escalatie; eerstehands ervaren door beide sprekers. "
        + KANT,
        0.45,
        [(S_DNW,
          "Dus je hebt een soort van drietraps eh raket eh dat op het "
          "moment dat jij eh constatief rechtse standpunten uit, dan "
          "zeggen mensen van: \"Oh, het zal wel iemand zijn die dom is, "
          "hè.",
          BASE + "Spreker: Vlam. ASR-fout: 'constatief' = conservatief."),
         (S_DNW,
          "En als ze er dan achter komen dat je misschien niet dom bent, "
          "dan zeggen ze van: \"Ah, maar je bent gewoon een doelgroep "
          "aan het bespelen.\" Is een verdienmodel en daarom moet je "
          "buiten de orde worden geplaatst.",
          BASE + "Spreker: Vlam."),
         (S_DNW,
          "Ja, en als ze dan geloven dat je het wel meent, dan is de "
          "laatste conclusie van: \"Oh, kijk, zie je wel, het is een "
          "racist of het is een xenofoob, het is of het sexist.\" En "
          "daarom moeten we die persoon geen platform eh geven. Dus er "
          "is altijd een reden om mensen geen platform te geven.",
          BASE + "Spreker: Vlam.")])

    add_arg(mech("schijndebat"), "supporting",
        "Getuigenis: een afwijkende (rechtse) gast staat aan de "
        "talkshowtafel alleen tegenover presentator én voltallig panel, "
        "terwijl mainstream-gasten nauwelijks kritisch bevraagd worden "
        "omdat hun standpunt als vanzelfsprekend geldt.",
        "Beide kanten van de geënsceneerde onbalans uit één mond: de "
        "overmacht tegen de dissident én de coulance voor de consensus. "
        + KANT,
        0.4,
        [(S_DNW,
          "Als je bij Pau in de wit zit, dan krijg je ook een hele stort "
          "eh vloed eh van negatieve kritieken over je heen. En dat is "
          "soms ook echt oneerlijk, want het is de presentator en het is "
          "het hele panel van de rest van de tafel wat ook over jou eh "
          "heen valt.",
          BASE + "Spreker: Vlam. ASR-fout: 'Pau in de wit' = "
          "Pauw & De Wit."),
         (S_DNW,
          "Dus wat je krijgt is dat eh zo iemand wordt dan niet kritisch "
          "bevraagd omdat de indruk ontstaat dat er niet zo heel veel te "
          "bevragen is.",
          BASE + "Spreker: Vlam, over gasten met als mainstream ervaren "
          "standpunten.")])

    add_arg(mech("spectrum_bewaking"), "supporting",
        "Getuigenis: hoofdredacteuren en columnisten gedragen zich als "
        "poortwachters van wíe aan het maatschappelijk debat mag "
        "meedoen; in talkshows wordt expliciet besloten debatten niet te "
        "voeren om rechts 'niet in de kaart te spelen', en sommige "
        "stemmen worden feitelijk (onuitgesproken) geboycot.",
        "Sluit naadloos aan op het spectrum-van-toegestane-opinie: niet "
        "de inhoud wordt bestreden, de deelname wordt gereguleerd. "
        + KANT,
        0.45,
        [(S_DNW,
          "ze zien zich als poortwachters inderdaad van wat tot het "
          "maatschappelijk debat eh behoort. Dat zie je heel sterk bij "
          "die eh kranten. En dat betekent dat het vaak niet zozeer het "
          "het engagen van mensen is op inhoud, maar op basis van wie er "
          "aan het debat mag meedoen of niet.",
          BASE + "Zinsfragment. Spreker: Vlam."),
         (S_DNW,
          "En dat wordt wel kunstmatig klein gehouden. Dus ik denk wel "
          "eens dat er in talkshows wordt gezegd van we gaan maar niet "
          "dat debat voeren, want dan spelen we conservatief rechts of "
          "radicaal rechts of populistisch rechts, hoe ze het ook noemen "
          "in",
          BASE + "Spreker: Vlam; zin breekt af in het transcript."),
         (S_DNW,
          "Het is nooit officieel eh uitgesproken dat ze geboorkcot "
          "wordt, maar ze wordt gewoon nergens uitgenodigd.",
          BASE + "Spreker: Vlam, over de feitelijke talkshowboycot van "
          "een rechtse opiniemaker. ASR-fout: 'geboorkcot' = geboycot.")])

    add_arg(mech("spectrum_bewaking"), "supporting",
        "Getuigenis (anoniem, niet onafhankelijk verifieerbaar): een "
        "gepland talkshowgesprek over kritiek op de NPO werd volgens de "
        "presentator last-minute geschrapt na druk vanuit de NPO, en bij "
        "meerdere grote NPO-talkshows zou een informele policy bestaan "
        "om de criticus niet meer uit te nodigen.",
        "Laag gewicht: de getuige is zelf de geweerde partij, de bron "
        "binnen de omroep is anoniem en de claim is niet onafhankelijk "
        "te verifiëren. Tegelijk is dit precies het type backstage-"
        "gebeurtenis dat zelden anders dan via getuigenissen zichtbaar "
        "wordt; opgenomen mét die kanttekening.",
        0.3,
        [(S_DNW,
          "omdat er toch echt wat druk was vanuit de NPO van dat gesprek "
          "gaan we echt niet faciliteren. Dat gaan we echt niet doen. "
          "Dus je schrapt het maar. En het stond al geprogrammeerd.",
          BASE + "Spreker: Muusse, die een presentator citeert "
          "(tweedehands binnen de getuigenis)."),
         (S_DNW,
          "dat er echt toch een soort policy was binnen een aantal eh "
          "grote NPO talkshows van doordat ik zo kritiek had gehad ook "
          "op het instituut zelf. Ja, genomen dat ze echt zeiden van die "
          "komt er echt gewoon nooit meer in.",
          BASE + "Zinsfragment. Spreker: Muusse, over wat zij van "
          "redacties hoorde.")])

    add_arg(mech("media_agendering"), "supporting",
        "Getuigenis: politieke medewerkers scannen elke ochtend kranten "
        "én de talkshows van de vorige avond als graadmeter van het "
        "debat; wat een dominante talkshowopiniemaker vindt, kan een "
        "discussie in Den Haag van richting doen veranderen.",
        "Bevestigt het mechanisme specifiek voor talkshows (naast "
        "kranten): de monitoringroutine in Den Haag en het "
        "doorwerkingseffect van één opiniemaker met miljoenenbereik. "
        + KANT,
        0.5,
        [(S_DNW,
          "Kijk, ik weet dat politici wel eh hè medewerkers kijken "
          "gewoon iedere ochtend wat stond er in de klanten? Wat is er "
          "gisteravond bij de talkshows gezegd?",
          BASE + "Spreker: Muusse. ASR-fout: 'klanten' = kranten."),
         (S_DNW,
          "Ik denk één van de interessante dingen die ik altijd vind is "
          "als eh dat dat mensen in Den Haag echt kijken naar wat Johan "
          "Derks de avond daarvoor heeft eh gezegd.",
          BASE + "Spreker: Vlam. ASR-fout: 'Johan Derks' = Johan "
          "Derksen."),
         (S_DNW,
          "Als hij iets vindt dan kan dat echt een discussie een andere "
          "kant op eh laten gaan.",
          BASE + "Spreker: Vlam, over dezelfde opiniemaker.")])

    add_arg(mech("intermedia_agendering"), "supporting",
        "Getuigenis: de Volkskrant is als relatief kleine, Randstedelijke "
        "krant onevenredig invloedrijk doordat juist de top van "
        "mediaorganisaties, politiek en ministeries haar leest en die "
        "opvattingen als poortwachters binnen hun eigen organisaties "
        "doorgeven.",
        "Specificeert het kanaal van intermedia-agendering: niet alleen "
        "redacties volgen elkaars kopij, ook de leiding van andere media "
        "neemt het referentiekader van één titel over (casus RTL "
        "Tonight: programmering gericht op 'het debat in de "
        "Volkskrant'). " + KANT,
        0.4,
        [(S_DNW,
          "De volksrand is oneig invloedrijk doordat heel veel "
          "invloedrijke mensen ook weer die krant eh lezen.",
          BASE + "Spreker: Vlam. ASR-fouten: 'volksrand' = Volkskrant; "
          "'oneig' = onwijs."),
         (S_DNW,
          "die hebben op hun werk ook weer die poortwachtersfunctie "
          "voor de geluiden binnen hun organisaties. Dus daar daarin "
          "krijgt dan zo'n relatief kleine nieskrant",
          BASE + "Zinsfragment. Spreker: Muusse, over de mediatop, "
          "politiek en ministeries als Volkskrant-lezers. ASR-fout: "
          "'nieskrant' = nichekrant.")])


if __name__ == "__main__":
    main()
