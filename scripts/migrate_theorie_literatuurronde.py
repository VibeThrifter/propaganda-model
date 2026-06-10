#!/usr/bin/env python3
"""
Migratie: theorieronde uit systematisch literatuuronderzoek (juni 2026),
na hertoets op rolparen en NL-toepasbaarheid.

Drie nieuwe theorie-elementen:
  - indexering            politicus -> redactie (direct, sourcing+ideologie)
                          Bennett 1990. VS-empirie; geen meerpartijen-toets
                          gevonden -> gewicht 0.5 en stelselvertaling
                          expliciet in de reasoning.
  - intermedia_agendering mediaorganisatie -> mediaorganisatie (direct,
                          sourcing). Vliegenthart & Walgrave 2008 (Vlaamse
                          data; structureel vergelijkbaar landschap, deels
                          dezelfde eigenaren). Eerste media->media-rand in
                          het model; let op: in de theorie-viz is dit een
                          self-loop op rolniveau.
  - nieuwswaardenroutine  halo op redactie (veld_eigenschap, sourcing+
                          ideologie). Galtung & Ruge 1965; Harcup & O'Neill
                          2016. Geen zender: overgedragen via opleiding en
                          socialisatie.

Eerste/extra onderbouwing voor bestaande mechanismen:
  - pakketjournalistiek      <- Boumans, Trilling, Vliegenthart &
                                Boomgaarden (IJoC 12, 2018): NL, kwantitatief;
                                NU.nl 75% bureaukopij, print 12-16%.
                                LET OP: het 75%-cijfer wordt in samenvattingen
                                vaak aan Welbers e.a. 2018 ("Gatekeeper among
                                Gatekeepers") toegeschreven; geverifieerd in de
                                open-access-pdf: het staat in Boumans e.a.
  - advertentiedruk          <- Baker 1994 (eerste argument advertentiefilter)
  - institutioneel_gezag     <- Hall e.a. 1978, primary definers
  - platform_journalistiekfinanciering <- Nechushtai 2018
  - voorlichter_informatiefilter <- Gans 1979 (hertoets: pijl gecorrigeerd;
                                de bron leidt, dus niet bij
                                journalist_bronrelatie geplaatst)
  - columnist_als_hegemon    <- Jacobs & Townsley 2011 (hertoets: Katz &
                                Lazarsfeld GESCHRAPT — hun opinion leaders
                                zijn interpersoonlijke figuren in de rol
                                publiek, geen columnisten)

Padclaim-versterking: Entman 2003 (cascademodel benoemt de compositie
regering -> elites -> media -> publiek) als extra citatie bij de bestaande
padclaims gezagsinstituut ⇢ publiek (arg 415) en politicus ⇢ publiek
(arg 422), met kanttekening VS-presidentieel stelsel.

Backup-then-migrate; idempotent; tweemaal draaien verandert niets.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-theorie-literatuurronde-2026-06"
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

    # ---- BRONNEN -------------------------------------------------------------
    def add_source(title, stype, author, publisher, date, url=None,
                   summary=None, language="en"):
        row = cur.execute("SELECT id FROM sources WHERE title=?",
                          (title,)).fetchone()
        if row:
            print(f"bron bestaat al: {title[:55]}")
            return row[0]
        cur.execute(
            """INSERT INTO sources (title, author, source_type, publisher,
               date_published, language, summary, reliability)
               VALUES (?,?,?,?,?,?,?,'academisch')""",
            (title, author, stype, publisher, date, language, summary))
        sid = cur.lastrowid
        if url:
            cur.execute(
                """INSERT INTO source_locations (source_id, location_type,
                   location, accessed_at) VALUES (?,?,?,?)""",
                (sid, "url", url, ACCESSED))
        print(f"+ bron {sid}: {title[:55]}")
        return sid

    S_GR = add_source(
        "The Structure of Foreign News",
        "academisch_artikel", "Galtung, J. & Ruge, M.H.",
        "Journal of Peace Research", "1965-01-01",
        summary="Grondleggend artikel over nieuwswaarden: twaalf factoren "
                "die bepalen of een gebeurtenis nieuws wordt (o.a. "
                "elitenaties, elitepersonen, negativiteit, "
                "personifieerbaarheid), getoetst op Noorse "
                "buitenlandverslaggeving.")
    S_HO = add_source(
        "What is News? News values revisited (again)",
        "academisch_artikel", "Harcup, T. & O'Neill, D.",
        "Journalism Studies (Taylor & Francis)", "2016-01-01",
        url="https://www.tandfonline.com/doi/full/10.1080/1461670X.2016."
            "1150193",
        summary="Tweede empirische herijking van Galtung & Ruge's "
                "nieuwswaarden (na Harcup & O'Neill 2001) op Britse "
                "dagbladen; bevestigt nieuwswaarden als werkzame "
                "selectiegrammatica, geactualiseerd voor o.a. exclusiviteit "
                "en deelbaarheid.")
    S_BENNETT = add_source(
        "Toward a Theory of Press-State Relations in the United States",
        "academisch_artikel", "Bennett, W.L.",
        "Journal of Communication", "1990-01-01",
        url="https://onlinelibrary.wiley.com/doi/abs/10.1111/"
            "j.1460-2466.1990.tb02265.x",
        summary="Indexing-hypothese: de bandbreedte van standpunten in het "
                "nieuws wordt geïndexeerd aan de bandbreedte van het debat "
                "binnen de politieke mainstream; getoetst op vier jaar "
                "NYT-dekking van de Nicaragua-politiek.")
    S_VW = add_source(
        "The Contingency of Intermedia Agenda Setting: A Longitudinal "
        "Study in Belgium",
        "academisch_artikel", "Vliegenthart, R. & Walgrave, S.",
        "Journalism & Mass Communication Quarterly", "2008-01-01",
        url="https://journals.sagepub.com/doi/10.1177/107769900808500409",
        summary="Longitudinale studie (negen media, acht jaar, België): "
                "media zetten elkaars agenda, vooral op korte termijn; "
                "kranten beïnvloeden televisie sterker dan omgekeerd.")
    S_BOUMANS18 = add_source(
        "The Agency Makes the (Online) News World Go Round: The Impact of "
        "News Agency Content on Print and Online News",
        "academisch_artikel",
        "Boumans, J., Trilling, D., Vliegenthart, R. & Boomgaarden, H.",
        "International Journal of Communication", "2018-01-01",
        url="https://ijoc.org/index.php/ijoc/article/view/7109",
        summary="Kwantitatieve NL-studie (een jaar ANP-kopij, n=119.452, "
                "tegen 247.161 print- en online-artikelen): NU.nl is voor "
                "75% op bureaukopij gebaseerd, printtitels 12-16%; veel "
                "online nieuws is vrijwel onbewerkte bureaukopij.")
    S_BAKER = add_source(
        "Advertising and a Democratic Press",
        "boek", "Baker, C.E.", "Princeton University Press", "1994-01-01",
        url="https://press.princeton.edu/books/hardcover/9780691633930/"
            "advertising-and-a-democratic-press",
        summary="Rechtseconomische analyse van het advertentiemodel: "
                "adverteerders belonen het vermijden van aanstoot en "
                "straffen kritiek, en vervangen zo deels lezers en "
                "redacties als feitelijke opdrachtgevers van de inhoud.")
    S_HALL = add_source(
        "Policing the Crisis: Mugging, the State, and Law and Order",
        "boek",
        "Hall, S., Critcher, C., Jefferson, T., Clarke, J. & Roberts, B.",
        "Macmillan", "1978-01-01",
        summary="Cultural-studies-klassieker; introduceert 'primary "
                "definers': machtige instituties (politie, rechters, "
                "ministers) leveren de eerste definitie van een kwestie, "
                "waarna media die reproduceren en het verdere debat erdoor "
                "wordt gekaderd.")
    S_NECH = add_source(
        "Could digital platforms capture the media through infrastructure?",
        "academisch_artikel", "Nechushtai, E.", "Journalism", "2018-01-01",
        url="https://journals.sagepub.com/doi/abs/10.1177/1464884917725163",
        summary="Introduceert 'infrastructural capture': redacties kunnen "
                "niet duurzaam opereren zonder de digitale infrastructuur "
                "(distributie, analytics, formats, financiering) van de "
                "platformbedrijven die ze zouden moeten controleren.")
    S_GANS = add_source(
        "Deciding What's News: A Study of CBS Evening News, NBC Nightly "
        "News, Newsweek, and Time",
        "boek", "Gans, H.J.", "Pantheon Books", "1979-01-01",
        summary="Etnografische newsroom-studie; beschrijft de "
                "bron-journalistrelatie als een tango waarin vaker de bron "
                "leidt: goed georganiseerde, gezaghebbende bronnen "
                "verschaffen zich structureel toegang tot het nieuws.")
    S_JT = add_source(
        "The Space of Opinion: Media Intellectuals and the Public Sphere",
        "boek", "Jacobs, R.N. & Townsley, E.",
        "Oxford University Press", "2011-01-01",
        url="https://archive.org/details/spaceofopinionme0000jaco",
        summary="Empirische studie van de opinie-ruimte (op-ed's, "
                "talkshows): professionele opiniemakers vormen een eigen "
                "veld tussen journalistiek, politiek, academie en "
                "denktanks, met eigen gezagsclaims richting publiek. "
                "Amerikaanse context.")
    S_ENTMAN = add_source(
        "Cascading Activation: Contesting the White House's Frame After "
        "9/11",
        "academisch_artikel", "Entman, R.M.",
        "Political Communication", "2003-01-01",
        url="https://www.tandfonline.com/doi/abs/10.1080/"
            "10584600390244176",
        summary="Cascademodel: interpretatieve frames stromen van de "
                "regering via niet-gouvernementele elites naar redacties, "
                "nieuwsteksten en publiek; feedback omhoog is zwakker en "
                "loopt vooral via de media. Amerikaans-presidentiële "
                "context.")

    # ---- NIEUWE MECHANISMEN ----------------------------------------------------
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

    M_INDEX = add_mechanism(
        "indexering", "sourcing", "procedureel", "direct",
        "politicus", "redactie",
        "De bandbreedte van het nieuws volgt de bandbreedte van het "
        "meningsverschil binnen de politieke elite: de redactie kalibreert "
        "welke standpunten als 'serieus' dekking en weerwoord krijgen aan "
        "wat in kabinet en Kamer daadwerkelijk wordt betwist (Bennetts "
        "indexing-hypothese). Valt de parlementaire oppositie op een thema "
        "stil — kamerbrede consensus — dan verdwijnt kritiek uit beeld, "
        "ook als die feitelijk onderbouwd is. Inputzijde van "
        "spectrum_bewaking; omgekeerde pijl van media_agendering (samen "
        "vormen ze de medialogica-lus).",
        "Het gedekte opiniespectrum krimpt en rekt mee met het "
        "parlementaire spectrum; buitenparlementaire kritiek blijft "
        "structureel onderbelicht zolang geen elite-actor haar overneemt.",
        extra_filters=("ideologie",))
    M_INTER = add_mechanism(
        "intermedia_agendering", "sourcing", "procedureel", "direct",
        "mediaorganisatie", "mediaorganisatie",
        "Titels en omroepen zetten elkaars agenda: wat de ene redactie "
        "groot brengt, wordt voor de andere een te volgen onderwerp — "
        "kranten sturen doorgaans televisie, vooral op korte termijn. "
        "Tweede uniformeringskanaal naast het persbureau "
        "(pakketjournalistiek): redacties convergeren ook zónder gedeelde "
        "kopij, omdat elkaars keuzes als bewijs van nieuwswaardigheid "
        "gelden.",
        "Convergentie van agenda's over titels heen; versterkt "
        "schijnpluriformiteit en mediahype: één agendakeuze plant zich "
        "door het hele landschap voort zonder centrale verspreider.")
    M_NWR = add_mechanism(
        "nieuwswaardenroutine", "sourcing", "procedureel",
        "veld_eigenschap", None, "redactie",
        "Geïnternaliseerde selectiegrammatica van de redactie: "
        "gebeurtenissen halen het nieuws naarmate ze scoren op "
        "nieuwswaarden als elitepersonen, elitenaties, conflict, "
        "negativiteit, onverwachtsheid en personifieerbaarheid (Galtung & "
        "Ruge; herijkt door Harcup & O'Neill). Geen aanwijsbare zender: de "
        "routine wordt overgedragen via opleiding en socialisatie en "
        "blijft werken zonder live input — daarom een veldeigenschap van "
        "de redactie, geen rand.",
        "Structurele scheefheid in wat überhaupt nieuws wordt: aandacht "
        "voor incident boven structuur en voor elite boven periferie — de "
        "selectiegrammatica waar medialogica en mediahype op draaien.",
        extra_filters=("ideologie",))

    def mech_id(name):
        row = cur.execute("SELECT id FROM mechanisms WHERE name=?",
                          (name,)).fetchone()
        if not row:
            raise SystemExit(f"FOUT: mechanisme ontbreekt: {name}")
        return row[0]

    # ---- ARGUMENTEN ------------------------------------------------------------
    def add_arg(mechanism_id, stance, claim, reasoning, weight, citations):
        row = cur.execute(
            "SELECT id FROM arguments WHERE mechanism_id=? AND claim=?",
            (mechanism_id, claim)).fetchone()
        if row:
            print(f"argument bestaat al (mechanism_id={mechanism_id})")
            return row[0]
        cur.execute(
            """INSERT INTO arguments (mechanism_id, stance, claim,
               reasoning, weight, status, contributed_by)
               VALUES (?,?,?,?,?,?,?)""",
            (mechanism_id, stance, claim, reasoning, weight,
             "ongecontroleerd", CONTRIB))
        aid = cur.lastrowid
        for sid, quote, ctx in citations:
            cur.execute(
                "INSERT INTO citations (argument_id, source_id, quote, "
                "context) VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument (w={weight}) bij mechanisme {mechanism_id}, "
              f"{len(citations)} citatie(s)")
        return aid

    add_arg(M_INDEX, "supporting",
        "De redactionele bandbreedte van standpunten volgt de bandbreedte "
        "van het debat binnen de politieke mainstream: kritiek krijgt pas "
        "volwaardige dekking wanneer een gevestigde politieke actor haar "
        "draagt.",
        "Bennett toetste dit op vier jaar New York Times-dekking van de "
        "Nicaragua-politiek. De empirie is Amerikaans (tweepartijen-, "
        "presidentieel stelsel) en een toets in een meerpartijenstelsel is "
        "niet gevonden; daarom blijft het gewicht beperkt. De logica "
        "vertaalt wel naar het Nederlandse coalitiestelsel: een bredere "
        "Kamer geeft een breder spectrum, maar bij kamerbrede consensus "
        "(Irak 2003, NAVO/EU-premissen, het migratiedebat vóór Fortuyn) "
        "voorspelt indexering juist de smalle dekking die voor die "
        "perioden ook beschreven is.",
        0.5,
        [(S_BENNETT,
          "Mass media news professionals tend to 'index' the range of "
          "voices and viewpoints in both news and editorials according to "
          "the range of views expressed in mainstream government debate "
          "about a given topic.",
          "kernformulering van de indexing-hypothese (Journal of "
          "Communication 40(2), 1990), zoals weergegeven in abstract en "
          "overzichtsliteratuur; tegen samenvattingen geverifieerd, niet "
          "tegen de volledige artikeltekst")])

    add_arg(M_INTER, "supporting",
        "Media zetten elkaars agenda: aandacht van de ene titel voorspelt "
        "aandacht van de andere, met kranten als dominante zender richting "
        "televisie, vooral op korte termijn.",
        "Longitudinale toets op negen media over acht jaar. Kanttekening: "
        "Belgische (Vlaamse) data — maar het Vlaamse landschap is "
        "structureel vergelijkbaar en deelt inmiddels grotendeels de "
        "eigenaren met het Nederlandse (DPG Media, Mediahuis). Het "
        "mechanisme veronderstelt geen afstemming: elkaars keuzes gelden "
        "als bewijs van nieuwswaardigheid.",
        0.55,
        [(S_VW,
          "Intermedia agenda setting is vooral een kortetermijnproces; "
          "kranten beïnvloeden de televisieagenda sterker dan omgekeerd, "
          "en het effect verschilt per onderwerpstype en valt grotendeels "
          "weg in verkiezingstijd.",
          "typering van de hoofdbevindingen (JMCQ 85(4), 2008, pp. "
          "860-877); geen letterlijk citaat")])

    add_arg(M_NWR, "supporting",
        "Nieuwsselectie verloopt langs een stabiele, aangeleerde set "
        "nieuwswaarden die gebeurtenissen met elites, conflict en incident "
        "structureel bevoordeelt boven structurele, trage of perifere "
        "ontwikkelingen.",
        "Galtung & Ruge formuleerden en toetsten de factoren op "
        "buitenlandverslaggeving (Europees onderzoek, geen "
        "stelselafhankelijkheid); Harcup & O'Neill hebben de taxonomie "
        "tweemaal empirisch herijkt op dagbladcorpora en bevestigen haar "
        "werking. Nieuwswaarden zijn standaardstof in de Nederlandse "
        "journalistiekopleiding — de overdrachtsroute van de routine.",
        0.6,
        [(S_GR,
          "Hoe meer een gebeurtenis elitenaties en elitepersonen betreft, "
          "hoe negatiever, onverwachtser en persoonlijker zij is, des te "
          "groter de kans dat zij nieuws wordt; factoren versterken "
          "elkaar (additiviteit) en wie op geen enkele factor scoort, "
          "haalt het nieuws niet (exclusie).",
          "typering van het factorenmodel (Journal of Peace Research "
          "2(1), 1965); geen letterlijk citaat"),
         (S_HO,
          "De herijkte taxonomie bevestigt dat een beperkte set "
          "nieuwswaarden (o.a. de machtselite, conflict, verrassing, "
          "slecht nieuws) de selectie in de onderzochte dagbladen "
          "verklaart.",
          "typering van de replicatiebevindingen (Journalism Studies, "
          "2016); geen letterlijk citaat")])

    add_arg(mech_id("pakketjournalistiek"), "supporting",
        "Nederlandse nieuwssites zijn voor het overgrote deel van hun "
        "berichten op ANP-kopij gebaseerd; een groot deel daarvan is "
        "vrijwel onbewerkt.",
        "Kwantitatieve computationele studie over een volledig jaar "
        "(119.452 ANP-berichten tegen 247.161 artikelen van Volkskrant, "
        "Telegraaf, Metro en NU.nl, print en online). Het hardste "
        "Nederlandse cijfer voor de persbureau-afhankelijkheid; let op de "
        "spreiding: online (NU.nl 75%) versus print (12-16%).",
        0.7,
        [(S_BOUMANS18,
          "Results suggest that particularly online news is highly "
          "dependent on agency content, with the agency being responsible "
          "for up to 75% of the online news articles. Furthermore, a "
          "large part of the online news consists of verbatim agency "
          "copy, involving little or no editing.",
          "letterlijk citaat (abstract), geverifieerd in de "
          "open-access-pdf (IJoC 12, 2018, pp. 1768-1789), geraadpleegd "
          f"{ACCESSED}"),
         (S_BOUMANS18,
          "The ratio indicates that 75% of the news articles that appear "
          "on the website are based on agency copy. (...) To compare, "
          "the ratio of the print titles is 16% for de Volkskrant, 12% "
          "for De Telegraaf, and 48% for Metro.",
          "letterlijk citaat (resultatensectie over NU.nl), geverifieerd "
          f"in de open-access-pdf, geraadpleegd {ACCESSED}")])

    add_arg(mech_id("advertentiedruk"), "supporting",
        "Adverteerders belonen media voor het vermijden van aanstoot bij "
        "potentiële klanten en straffen kritiek op hun producten of "
        "politieke agenda — een structurele, deels onzichtbare "
        "censuurprikkel.",
        "Bakers rechtseconomische analyse van het advertentiemodel: hoe "
        "afhankelijker een titel van advertenties, hoe sterker de inhoud "
        "naar de belangen van adverteerders buigt; adverteerders vervangen "
        "zo deels lezers en redactie als feitelijke opdrachtgever. "
        "Economisch generiek argument, niet stelselgebonden; een "
        "Nederlands praktijkanker (zoals de adverteerdersboycot van "
        "GeenStijl, 2017) vergt een eigen ronde.",
        0.6,
        [(S_BAKER,
          "Adverteerders belonen zowel gedrukte als audiovisuele media "
          "voor het vermijden van aanstoot bij potentiële klanten en "
          "straffen media voor kritiek op hun producten of politieke "
          "agenda — met directe en indirecte censuur tot gevolg.",
          "typering van de kernthese (Princeton UP, 1994); geen "
          "letterlijk citaat")])

    add_arg(mech_id("institutioneel_gezag"), "supporting",
        "Machtige instituties fungeren als 'primary definers': zij leveren "
        "de eerste definitie van een kwestie, die media reproduceren en "
        "die het verdere debat kadert.",
        "Hall e.a. laten zien dat de journalistieke voorkeur voor "
        "gezaghebbende bronnen (politie, rechters, ministers) deze "
        "instituties structureel het eerste en daarmee kaderstellende "
        "woord geeft; de journalist speelt een 'cruciale maar secundaire' "
        "rol. Britse context, maar het mechanisme berust op de "
        "objectiviteitsroutine zelf en is in de praktijklaag van dit model "
        "al Nederlands geïnstantieerd (RIVM/OMT, NCTV).",
        0.55,
        [(S_HALL,
          "De media reproduceren de definities van de machtigen: de "
          "structurele voorkeur voor institutionele zegspersonen maakt "
          "hen tot primary definers, wier eerste interpretatie het kader "
          "vormt waarbinnen alle verdere discussie plaatsvindt.",
          "typering van het primary definers-concept (Policing the "
          "Crisis, 1978); geen letterlijk citaat")])

    add_arg(mech_id("platform_journalistiekfinanciering"), "supporting",
        "Redacties raken infrastructureel gevangen: ze kunnen niet "
        "duurzaam opereren zonder de distributie, analytics, formats en "
        "fondsen van de platformbedrijven die ze journalistiek zouden "
        "moeten controleren.",
        "Nechushtai noemt dit 'infrastructural capture' — een vorm van "
        "capture die niet via eigendom of advertenties loopt maar via "
        "afhankelijkheid van de werkomgeving zelf. Voor Nederland is de "
        "geldstroom aantoonbaar: het Digital News Initiative van Google "
        "financierde meerdere Nederlandse redacties en platforms "
        "(praktijkanker voor een latere ronde).",
        0.55,
        [(S_NECH,
          "Infrastructural capture: circumstances in which a scrutinizing "
          "body is incapable of operating sustainably without the "
          "physical or digital resources and services provided by the "
          "businesses it oversees and is therefore dependent on them.",
          "definitie uit het artikel (Journalism 19(8), 2018); "
          "geverifieerd tegen abstract en secundaire weergaven, niet "
          "tegen de volledige tekst")])

    add_arg(mech_id("voorlichter_informatiefilter"), "supporting",
        "In de bron-journalistrelatie leidt vaker de bron: goed "
        "georganiseerde voorlichting bepaalt wat de journalist te zien "
        "krijgt en verschaft zich zo structureel toegang tot het nieuws.",
        "Gans' newsroom-etnografie beschrijft de relatie als een tango "
        "waarin de bron meestal leidt. Hertoets rolpaar: dit argument "
        "hoort bij de pijl voorlichter -> journalist (de bron stuurt), "
        "niet bij journalist_bronrelatie (journalist -> voorlichter, het "
        "koesteren van toegang) — die anticipatiekant blijft apart "
        "onderbouwd worden.",
        0.55,
        [(S_GANS,
          "Gans beschrijft de relatie tussen bronnen en journalisten als "
          "een tango — 'it takes two to tango' — waarbij vaker de bron "
          "leidt: bronnen die zich organiseren en gezag meebrengen, "
          "verschaffen zich structureel toegang tot het nieuws.",
          "typering van de bronnenanalyse in Deciding What's News "
          "(1979); geen letterlijk citaat")])

    add_arg(mech_id("columnist_als_hegemon"), "supporting",
        "Professionele opiniemakers vormen een eigen ruimte tussen "
        "journalistiek, politiek, academie en denktanks, met eigen "
        "gezagsclaims waarmee zij het publieke debat kaderen.",
        "Jacobs & Townsley analyseren de opinie-ruimte (op-ed's, "
        "talkshows) empirisch. Kanttekening: Amerikaanse context; de "
        "Nederlandse columnistencultuur is er een eigen variant van en "
        "verdient een eigen praktijkanker. Hertoets: Katz & Lazarsfelds "
        "two-step flow is hier bewust níét gebruikt — hun 'opinion "
        "leaders' zijn interpersoonlijke figuren binnen het publiek, geen "
        "professionele columnisten.",
        0.45,
        [(S_JT,
          "De opinie-ruimte is sterk uitgebreid en gedifferentieerd, op "
          "het snijvlak van journalistiek, politiek, academie en "
          "denktanks; opiniemakers hanteren er eigen gezagsclaims en "
          "aanspreekvormen richting publiek.",
          "typering van de kernbevindingen (Oxford UP, 2011); geen "
          "letterlijk citaat; Amerikaanse context")])

    # ---- ENTMAN-CITATIES BIJ BESTAANDE PADCLAIMS -------------------------------
    ENTMAN_QUOTE = (
        "Interpretatieve frames stromen in een cascade van de regering "
        "via niet-gouvernementele elites naar redacties, nieuwsteksten en "
        "publiek; feedback omhoog is zwakker en loopt vooral via de "
        "media.")
    ENTMAN_CTX = (
        "typering van het cascademodel (Political Communication 20(4), "
        "2003); Amerikaans-presidentiële context — in het Nederlandse "
        "coalitiestelsel is de cascadetop meervoudig (kabinet + "
        "coalitiefracties); aanvullend op het RMO-anker, geen vervanging")
    for arg_id, label in ((415, "gezagsinstituut ⇢ publiek"),
                          (422, "politicus ⇢ publiek")):
        row = cur.execute(
            "SELECT a.id FROM arguments a WHERE a.id=? AND "
            "a.property='indirecte_invloed_op'", (arg_id,)).fetchone()
        if not row:
            raise SystemExit(f"FOUT: padclaim-argument {arg_id} niet "
                             "gevonden — ids verifiëren")
        if cur.execute("SELECT 1 FROM citations WHERE argument_id=? AND "
                       "source_id=?", (arg_id, S_ENTMAN)).fetchone():
            print(f"Entman-citatie bestaat al bij padclaim {label}")
            continue
        cur.execute("INSERT INTO citations (argument_id, source_id, "
                    "quote, context) VALUES (?,?,?,?)",
                    (arg_id, S_ENTMAN, ENTMAN_QUOTE, ENTMAN_CTX))
        print(f"+ Entman-citatie bij padclaim {label}")

    con.commit()

    # ---- SAMENVATTING ----------------------------------------------------------
    print("---")
    for label in ("mechanisms", "arguments", "citations", "sources",
                  "source_locations"):
        n = cur.execute(f"SELECT COUNT(*) FROM {label}").fetchone()[0]
        print(f"{label:17s}: {n}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
