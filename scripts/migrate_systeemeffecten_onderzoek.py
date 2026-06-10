#!/usr/bin/env python3
"""
Migratie: zes nieuwe emergente effecten (hyperedges) + één halo, uit het
systeemeffecten-onderzoek van juni 2026 (DB-scan + webonderzoek).

Toets per kandidaat (CLAUDE.md/DOCUMENTATIE.md § Aard): eigenschap van een
*groep* rollen zonder één afzender, waarbij het samenspel zelf — niet de
optelsom van losse edges — het verschijnsel is, en de literatuur de
compositie benoemt.

  - schijnpluriformiteit    hyperedge  veel titels, één ANP-nieuwsstroom
                            (Boumans 2016: ~66% van online nieuws ANP-gebaseerd)
  - ideologische_homofilie  hyperedge  diplomademocratie in de nieuwsketen
                            (Bovens & Wille; stemvoorkeur parlementair journalisten)
  - mediahype               hyperedge  zelfversterkende nieuwsgolf (Vasterman 2004)
  - medialogica             hyperedge  wurggreep politiek<->media (RMO 2003)
  - verkillingsspiraal      hyperedge  flak <-> conformisme, collectief chilling
                            effect (PersVeilig/I&O 2021)
  - voorlichtingsovermacht  hyperedge  ~150.000 communicatieprofessionals vs
                            ~15.000 journalisten (UvA/CBS via Villamedia 2018)
  - publieksfragmentatie    veld_eigenschap (halo) op publiek; diffuse herkomst
                            techplatform (CvdM Digital News Report 2024/2025)

Afgewezen na onderzoek: structureel nieuwsgat (compositie niet benoemd in
literatuur), nieuwswoestijnen (SVDJ: in NL geen woestijnen, wel onvolledig
lokaal landschap), platformisering-als-hyperedge (één afzender; optelsom
blijft in de techplatform-edges, conform de eigendomsconcentratie-regel).

Conform repo-conventie: eerst backup (data/propaganda_model_backup_<ts>.db),
dan muteren. Idempotent op naam (sources op titel, mechanisms/emergent_effects
op naam, arguments op (mechanism_id, claim)).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-systeemeffecten-webonderzoek-2026-06"


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

    def role_id(name):
        r = cur.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
        if not r:
            raise SystemExit(f"rol ontbreekt: {name}")
        return r[0]

    # ---- BRONNEN ------------------------------------------------------------
    def add_source(title, stype, author, publisher, date, reliability, url=None):
        cur.execute(
            """INSERT OR IGNORE INTO sources
               (title, author, source_type, publisher, date_published, reliability)
               VALUES (?,?,?,?,?,?)""",
            (title, author, stype, publisher, date, reliability),
        )
        sid = cur.execute("SELECT id FROM sources WHERE title=?", (title,)).fetchone()[0]
        if url:
            cur.execute(
                "INSERT OR IGNORE INTO source_locations (source_id, location_type, location) "
                "VALUES (?,?,?)", (sid, "url", url),
            )
        print(f"bron id={sid}: {title}")
        return sid

    src_boumans = add_source(
        "Outsourcing the news? An empirical assessment of the role of sources "
        "and news agencies in the contemporary news landscape",
        "academisch_artikel", "Boumans, J.", "Universiteit van Amsterdam",
        "2016-01-01", "academisch")
    src_bovens = add_source(
        "Diplomademocratie. Over de spanning tussen meritocratie en democratie",
        "boek", "Bovens, M. & Wille, A.", "Bert Bakker",
        "2011-01-01", "academisch")
    src_vasterman = add_source(
        "Mediahype",
        "boek", "Vasterman, P.", "Aksant",
        "2004-01-01", "academisch")
    src_rmo = add_source(
        "Medialogica. Over het krachtenveld tussen burgers, media en politiek",
        "rapport", "Raad voor Maatschappelijke Ontwikkeling", "RMO",
        "2003-01-01", "institutioneel",
        url="https://www.raadrvs.nl/site/binaries/site-content/collections/"
            "documents/2003/01/01/medialogica/Medialogica.pdf")
    src_persveilig = add_source(
        "Agressie en bedreiging richting journalisten",
        "rapport", "I&O Research / PersVeilig", "I&O Research",
        "2021-01-01", "institutioneel",
        url="https://nvj.nl/actueel/onderzoek-persveilig-8-10-respondenten-"
            "heeft-ervaring-geweld-of-bedreiging-journalistiek")
    src_villamedia = add_source(
        "Verhouding communicatieprofessionals-journalisten. Wat zeggen de cijfers?",
        "nieuwsartikel", "Oremus, F.", "Villamedia",
        "2018-10-04", "kwaliteitsjournalistiek",
        url="https://www.villamedia.nl/artikel/verhouding-communicatie"
            "professionals-journalisten.-wat-zeggen-de-cijfers/275159784-1ed8c474")
    src_dnr = add_source(
        "Digital News Report Nederland 2025",
        "rapport", "Commissariaat voor de Media", "CvdM",
        "2025-01-01", "institutioneel",
        url="https://www.cvdm.nl/nieuws/digital-news-report-nederland-2025-"
            "daling-van-nieuwsgebruik-zet-journalistiek-onder-druk/")

    # ---- EMERGENTIELAAG: zes hyperedges -------------------------------------
    def add_emergent(name, label, category, desc, effect, leden):
        cur.execute(
            "INSERT OR IGNORE INTO emergent_effects (name, label, category, description, effect) "
            "VALUES (?,?,?,?,?)", (name, label, category, desc, effect))
        eid = cur.execute(
            "SELECT id FROM emergent_effects WHERE name=?", (name,)).fetchone()[0]
        cur.execute(
            "UPDATE emergent_effects SET label=?, category=?, description=?, effect=? WHERE id=?",
            (label, category, desc, effect, eid))
        cur.execute("DELETE FROM emergent_effect_members WHERE emergent_effect_id=?", (eid,))
        for rn in leden:
            cur.execute(
                "INSERT OR IGNORE INTO emergent_effect_members (emergent_effect_id, role_id) "
                "VALUES (?,?)", (eid, role_id(rn)))
        print(f"+ emergent effect {name} ({len(leden)} leden: {', '.join(leden)})")
        return eid

    add_emergent(
        "schijnpluriformiteit", "Schijnpluriformiteit", "sourcing",
        "Eén centraal persbureau bevoorraadt vrijwel alle titels — Boumans (UvA, "
        "2016): circa twee derde van het online nieuws op sites als volkskrant.nl, "
        "nu.nl en telegraaf.nl was in 2014 gebaseerd op ANP-kopij, veelal vrijwel "
        "integraal overgenomen; de Nieuwsmonitor mat eerder al een stijging van 24% "
        "naar 28% ANP-gebaseerde krantenartikelen (2006-2008). Tegelijk zetten "
        "eigendomsconcentratie en hetzelfde rendementsregime de redacties op "
        "dezelfde efficiëntieprikkels. Geen van de losse pakketjournalistiek-edges "
        "produceert dit; de eenvormigheid is een eigenschap van de configuratie als "
        "geheel: veel merknamen, één nieuwsstroom.",
        "Het publiek ziet ogenschijnlijk concurrerende titels met eigen identiteit, "
        "maar krijgt grotendeels hetzelfde, door één bureau geselecteerde nieuws — "
        "pluriformiteit als façade, terwijl de feitelijke diversiteit aan "
        "perspectieven krimpt.",
        ["persbureau", "mediaorganisatie", "mediaeigenaar", "adverteerder", "publiek"])

    add_emergent(
        "ideologische_homofilie", "Ideologische homofilie", "ideologie",
        "Bovens & Willes diplomademocratie toegepast op de nieuwsketen: journalist, "
        "'onafhankelijke' expert, politicus, denktanker en topambtenaar komen uit "
        "dezelfde academische vormingsinstituten en leven in dezelfde kring. "
        "Empirisch zichtbaar in de stemvoorkeur van parlementair journalisten "
        "(D66 27% tegenover 9% landelijk, GroenLinks 14% tegenover 7,3%; "
        "'Haagse waakhonden', RUG) en in de Worlds of Journalism-surveys. Geen "
        "afzender stuurt dit; de homofilie is een eigenschap van de groep — "
        "wederzijdse bevestiging tussen gelijkgevormden.",
        "Bevestiging tussen journalist en bron oogt als onafhankelijke verificatie; "
        "afwijking van de hoogopgeleide consensus verschijnt niet als ander "
        "standpunt maar als gebrek aan kennis of 'activisme'. Structurele blinde "
        "vlekken voor de leefwereld van praktisch opgeleiden.",
        ["kennisinstituut", "journalist", "gezagsexpert", "denktank",
         "gezagsinstituut", "politicus", "columnist_opiniemaker"])

    add_emergent(
        "mediahype", "Mediahype", "systeemactor",
        "Vastermans zelfversterkende nieuwsgolf: één sleutelgebeurtenis als "
        "startpunt, daarna jagen media elkaars nieuws aan (pack journalism) — iets "
        "wordt belangrijk nieuws ómdat andere media het groot brengen. Politici "
        "reageren op de golf en voeden hem met nieuwe feiten en Kamervragen; "
        "columnisten versterken het frame. Geen actor regisseert de golf; de "
        "dynamiek is de lus zelf — het spiegelbeeld van de zelfversterkende "
        "homeostase: positieve in plaats van negatieve feedback.",
        "Eén frame klikt vast en duwt nuance en tegeninformatie maandenlang weg "
        "(de 'brutale fraude'-hype na de Bulgarenfraude die de Toeslagenaffaire "
        "mede mogelijk maakte); beleidsreacties op de hype bestendigen het frame "
        "nog voordat het is getoetst.",
        ["journalist", "columnist_opiniemaker", "mediaorganisatie", "politicus", "publiek"])

    add_emergent(
        "medialogica", "Medialogica", "systeemactor",
        "Het RMO-rapport Medialogica (2003): politiek en media houden elkaar in "
        "een wurggreep — het parlement laat zich sturen door wat gisteren in de "
        "media stond, media verslaan een politiek die zich op de camera richt. "
        "Het RMO noemt het een gevangenendilemma: niemand kan eruit zolang de "
        "anderen meedoen. Verwant aan maar onderscheiden van de "
        "toeschouwersdemocratie: dáár gaat het om wat het publiek te zien krijgt "
        "(de opvoering), hier om hoe de politiek haar eigen gedrag naar "
        "medialogica vormt.",
        "Personen en conflicten verdringen inhoud, beelden en emoties verdringen "
        "argumenten, incidenten verdringen langetermijnbeleid; hypes en "
        "kuddegedrag zijn uitwassen van dezelfde lus.",
        ["politicus", "voorlichter", "journalist", "mediaorganisatie", "publiek"])

    add_emergent(
        "verkillingsspiraal", "Verkillingsspiraal", "flak",
        "Externe flak en interne redactiecultuur versterken elkaar in een vicieuze "
        "cirkel: agressie, juridische dreiging en publieke aanvallen maken "
        "redacties risicomijdender, dat versterkt het conformisme, en het corps "
        "als geheel verlegt zijn grenzen. PersVeilig/I&O (2021): 8 op de 10 "
        "journalisten ervaart agressie of bedreiging (6 op de 10 in 2017), 16% "
        "past de berichtgeving aan, ~15% publiceert soms niet, 93% ziet een reëel "
        "gevaar voor de persvrijheid. De verkilling is een eigenschap van het "
        "samenspel — geen enkele afzender bereikt dit alleen.",
        "Het chilling effect overstijgt de individuele zelfcensuur-halo: hele "
        "onderwerpen en toonsoorten verdwijnen collectief uit de berichtgeving en "
        "het spectrum van het toelaatbare debat versmalt, zonder dat één partij "
        "daartoe besluit.",
        ["belanghebbende", "politicus", "publiek", "mediaorganisatie",
         "redactie", "journalist"])

    add_emergent(
        "voorlichtingsovermacht", "Voorlichtingsovermacht", "sourcing",
        "De structurele asymmetrie tussen de zendende en de controlerende kant "
        "van de informatieketen: circa 150.000 voorlichters en "
        "communicatiemedewerkers (UvA 'Gevaarlijk spel' 2010; CBS telde er "
        "149.000 in 2017) tegenover circa 15.000 journalisten — gegroeid vanaf "
        "55.000 in 2004 (UvA 'Schuivende grenzen'). Kanttekening die bij de "
        "verhouding hoort: de tellingen onderscheiden interne en externe "
        "communicatie niet, dus de effectieve overmacht richting journalistiek "
        "ligt lager — maar blijft een veelvoud. Geen enkele voorlichter-edge "
        "vangt dit; de overmacht is een eigenschap van de veldverhouding.",
        "Voorverpakte informatie wordt de standaardgrondstof van het nieuws: de "
        "checkende kant kan het aanbod van de zendende kant structureel niet "
        "bijhouden, waardoor persberichten en gecoördineerde voorlichting "
        "grotendeels ongefilterd doorstromen.",
        ["belanghebbende", "gezagsinstituut", "voorlichter", "journalist", "persbureau"])

    # ---- THEORIELAAG: publieksfragmentatie als halo op publiek --------------
    def mech_id(name):
        r = cur.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
        return r[0] if r else None

    m_frag = mech_id("publieksfragmentatie")
    if m_frag:
        print("mechanisme bestaat al: publieksfragmentatie")
    else:
        cur.execute(
            """INSERT INTO mechanisms
               (name, filter, mechanism_type, description, effect,
                source_role_id, target_role_id, aard)
               VALUES (?,?,?,?,?,?,?,?)""",
            ("publieksfragmentatie", "ideologie", "technologisch",
             "Het publiek versplintert als nieuwspubliek: nieuwsinteresse onder "
             "18-34-jarigen daalde van 61% (2021) naar 33% (2025), bij jonge "
             "vrouwen van 58% naar 22%; voor 60% van de jongeren zijn "
             "techplatforms de belangrijkste toegang tot nieuws en bepalen "
             "engagement-algoritmes wat zij zien (CvdM Digital News Report). "
             "Geen gerichte afzender: het is een toestand die het publiek "
             "ondergaat — de diffuse uitkomst van platformlogica, nieuwsmijding "
             "en het wegvallen van gedeelde nieuwsmerken.",
             "Het gedeelde nieuwsbeeld erodeert: deelpublieken leven in "
             "gescheiden, algoritmisch samengestelde informatie-omgevingen, "
             "journalistieke media bereiken vooral oudere kerngroepen, en "
             "fragmentatie en polarisatie versterken elkaar.",
             role_id("techplatform"), role_id("publiek"), "veld_eigenschap"),
        )
        m_frag = cur.lastrowid
        cur.execute("INSERT OR IGNORE INTO mechanism_filters VALUES (?,?)",
                    (m_frag, "advertentie"))
        for t in ("platform", "systemisch"):
            cur.execute("INSERT OR IGNORE INTO mechanism_themes VALUES (?,?)",
                        (m_frag, t))
        print("+ mechanisme publieksfragmentatie (filter=ideologie, aard=veld_eigenschap)")

    # ---- DISCUSSIEBOOM: onderbouwing op mechanismeniveau ---------------------
    def add_arg(mechanism_id, stance, claim, reasoning, weight, citations):
        bestaat = cur.execute(
            "SELECT 1 FROM arguments WHERE mechanism_id=? AND claim=?",
            (mechanism_id, claim)).fetchone()
        if bestaat:
            print("argument bestaat al (claim ongewijzigd)")
            return
        cur.execute(
            """INSERT INTO arguments (mechanism_id, stance, claim, reasoning,
               weight, status, contributed_by)
               VALUES (?,?,?,?,?,?,?)""",
            (mechanism_id, stance, claim, reasoning, weight,
             "ongecontroleerd", CONTRIB))
        aid = cur.lastrowid
        for sid, quote, ctx in citations:
            cur.execute(
                "INSERT INTO citations (argument_id, source_id, quote, context) "
                "VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument ({stance}) bij mechanisme {mechanism_id}")

    add_arg(m_frag, "supporting",
        "De nieuwsinteresse onder 18-34-jarigen halveerde in vier jaar (61% in "
        "2021 naar 33% in 2025) en voor 60% van de jongeren zijn techplatforms "
        "de belangrijkste toegang tot online nieuws.",
        "Het CvdM signaleert dat platforms met hun algoritmes bepalen wat "
        "gebruikers zien en dat journalistieke media het publiek steeds slechter "
        "bereiken — de fragmentatie is een toestand van het publiek, geen "
        "gerichte handeling: vandaar veld_eigenschap (halo) op publiek.",
        0.70,
        [(src_dnr,
          "Slechts 33% van de jongeren (18-34) zegt geïnteresseerd te zijn in "
          "nieuws; in 2021 was dat nog 61%. Voor 60% van de jongeren zijn "
          "big-techplatforms de belangrijkste toegang tot online nieuws.",
          "typering van de kernbevindingen via het CvdM-nieuwsbericht over het "
          "Digital News Report Nederland 2025; geen letterlijk rapportcitaat")],
    )

    add_arg(mech_id("pakketjournalistiek"), "supporting",
        "Circa twee derde van het online nieuws op grote Nederlandse nieuwssites "
        "(volkskrant.nl, nu.nl, telegraaf.nl) was in 2014 gebaseerd op "
        "ANP-berichtgeving, met tekstoverlap die neerkomt op vrijwel integrale "
        "overname.",
        "Empirische kwantificering van de schaal van pakketjournalistiek "
        "(proefschrift Boumans, UvA 2016); Boumans noemt twee derde uit één bron "
        "onwenselijk wegens eenzijdige berichtgeving en beeldvorming.",
        0.70,
        [(src_boumans,
          "Around 66 percent of news published online in 2014 was based on "
          "reporting from the Algemeen Nederlands Persbureau; the texts "
          "overlapped to such an extent that there was essentially an integral "
          "takeover of the ANP article.",
          "typering van de bevinding zoals samengevat in de vakpers "
          "(Adformatie/Villamedia); geen letterlijk proefschriftcitaat")],
    )

    add_arg(mech_id("zelfcensuur"), "supporting",
        "16% van de journalisten past de berichtgeving aan uit angst voor "
        "bedreiging en circa 15% ziet soms helemaal van publicatie af; 8 op de "
        "10 ervaart agressie of bedreiging (was 6 op de 10 in 2017).",
        "PersVeilig/I&O-onderzoek (2021) kwantificeert de zelfcensuur-halo en "
        "laat de stijging sinds 2017 zien; 93% van de journalisten noemt "
        "agressie en bedreiging een reëel gevaar voor de persvrijheid.",
        0.70,
        [(src_persveilig,
          "8 op de 10 respondenten heeft ervaring met geweld of bedreiging in "
          "de journalistiek; 16% past de berichtgeving aan, ongeveer 15% "
          "publiceert soms niet.",
          "typering van de kernbevindingen via het NVJ-bericht over het "
          "PersVeilig/I&O-onderzoek; geen letterlijk rapportcitaat")],
    )

    # bronnen die alleen de hyperedge-beschrijvingen dragen, markeren als verwerkt
    for sid in (src_bovens, src_vasterman, src_rmo, src_villamedia):
        cur.execute("UPDATE sources SET processed=1 WHERE id=?", (sid,))

    con.commit()

    # ---- SAMENVATTING --------------------------------------------------------
    for label, q in (
        ("mechanisms", "SELECT COUNT(*) FROM mechanisms"),
        ("emergent_effects", "SELECT COUNT(*) FROM emergent_effects"),
        ("emergent_members", "SELECT COUNT(*) FROM emergent_effect_members"),
        ("sources", "SELECT COUNT(*) FROM sources"),
        ("arguments", "SELECT COUNT(*) FROM arguments"),
        ("citations", "SELECT COUNT(*) FROM citations"),
    ):
        print(f"{label:16s}: {cur.execute(q).fetchone()[0]}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
