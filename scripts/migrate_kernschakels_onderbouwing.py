#!/usr/bin/env python3
"""
Migratie: discussieboom-onderbouwing voor de kernschakels van de vijf filters.

Aanleiding (modelreview): de afgeleide (indirecte) stippelpijlen verschijnen
alleen als élke schakel van het pad onderbouwd is (theorie: geloofwaardigheid
>= 0.10 per mechanisme). Vrijwel alle paden die de ongegatede cascade eerder
toonde (eigenaar ⇢ hoofdredacteur, adverteerder ⇢ publiek, persbureau ⇢
publiek, politicus ⇢ ledenomroep, ...) strandden op kernmechanismen van het
propagandamodel zélf die nog géén argument in de discussieboom hadden —
terwijl de geregistreerde literatuur ze expliciet dekt. Deze migratie voegt
die onderbouwing toe; de drempel blijft staan. Schakels zonder echte
vindplaats (young_global_leaders, etikettering, deplatforming, ...) blijven
bewust onbelegd — die paden komen dus níet terug.

Vindplaatsen per schakel staan in de citatie-context; regelnummers verwijzen
naar sources/AI/propagandsmodel2.md (de extractie-input), conform de eerdere
lobby- en publiek-keten-onderbouwing. Nieuw geregistreerde bron: Burgerlijk
Wetboek Boek 2 (wetgeving, primair) voor de wettelijke benoemingsketen
AvA -> RvC -> bestuur en de certificerings-/STAK-constructie.

Backup-then-migrate; idempotent op (mechanisme, claim) en op de brontitel.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-kernschakels-2026-06"

BW_TITLE = "Burgerlijk Wetboek Boek 2 (Rechtspersonen)"


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

    # ---- Bron: Burgerlijk Wetboek Boek 2 (idempotent op titel) --------------
    row = cur.execute("SELECT id FROM sources WHERE title=?", (BW_TITLE,)).fetchone()
    if row:
        bw = row[0]
        print(f"bron bestaat al: {BW_TITLE} (id {bw})")
    else:
        cur.execute(
            """INSERT INTO sources (title, author, source_type, publisher,
               date_published, language, reliability)
               VALUES (?,?,?,?,?,?,?)""",
            (BW_TITLE, "Staten-Generaal", "wetgeving", "Rijksoverheid",
             "1976-07-26", "nl", "primair"))
        bw = cur.lastrowid
        cur.execute(
            "INSERT INTO source_locations (source_id, location_type, location, accessed_at) "
            "VALUES (?,?,?,date('now'))",
            (bw, "url", "https://wetten.overheid.nl/BWBR0003045"))
        print(f"+ bron {BW_TITLE} (id {bw})")

    def mech_id(name):
        r = cur.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
        if not r:
            raise SystemExit(f"mechanisme ontbreekt: {name}")
        return r[0]

    def add_arg(mech_name, stance, claim, reasoning, weight, citations):
        mid = mech_id(mech_name)
        if cur.execute("SELECT 1 FROM arguments WHERE mechanism_id=? AND claim=?",
                       (mid, claim)).fetchone():
            print(f"  argument bestaat al bij {mech_name}")
            return
        cur.execute(
            """INSERT INTO arguments (mechanism_id, stance, claim, reasoning,
               weight, status, contributed_by)
               VALUES (?,?,?,?,?,?,?)""",
            (mid, stance, claim, reasoning, weight, "ongecontroleerd", CONTRIB))
        aid = cur.lastrowid
        for sid, quote, ctx in citations:
            cur.execute("INSERT INTO citations (argument_id, source_id, quote, context) "
                        "VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument ({stance}) bij {mech_name}")

    # ════ Filter 1: Eigendom — de controle- en benoemingsketen ════

    add_arg("eigendomsconcentratie", "supporting",
        "Een handvol familieconglomeraten (DPG/Van Thillo via Epifin; Mediahuis/"
        "families Leysen, Baert en Van Puijenbroek) controleert via gecertificeerde "
        "holdings het overgrote deel van de Nederlandse nieuwsmedia.",
        "Extreme marktconcentratie is de kern van het eerste filter; de ACM "
        "bevestigde de marktposities bij de toetsing van de DPG/RTL-overname.",
        0.75,
        [(3, "de belangrijkste nieuwsmedia in handen van een kleine, "
             "transnationaal opererende elite",
          "typering via sources/AI/propagandsmodel2.md (regel 17, 22-24); "
          "geen letterlijk citaat"),
         (12, "DPG Media krijgt vergunning voor overname RTL Nederland",
          "het ACM-besluit documenteert de marktposities en concentratiegraad")])

    add_arg("certificaatconstructie", "supporting",
        "De familiecontrole over de mediaholdings loopt via certificering van "
        "aandelen: het administratiekantoor houdt de stemrechtdragende aandelen, "
        "certificaathouders houden alleen het economische belang.",
        "Standaard Nederlandse constructie (Boek 2 BW); de extractie-analyse "
        "benoemt 'gecertificeerde holdings' expliciet als het kanaal van "
        "familiecontrole over de nieuwsmarkt.",
        0.60,
        [(bw, "certificering van aandelen scheidt het stemrecht (bij het "
              "administratiekantoor) van het economische belang (bij de "
              "certificaathouder)",
          "parafrase van de wettelijke constructie, Boek 2 BW; geen letterlijk "
          "citaat"),
         (3, "via hun gecertificeerde holdings",
          "typering via sources/AI/propagandsmodel2.md (regel 22)")])

    add_arg("winstmaximalisatie", "supporting",
        "De holding legt het rendementsregime op: eigenaren bepalen de strategie, "
        "keuren budgetten goed en beslissen over acquisities — winstoriëntatie "
        "vormt de institutionele context van de nieuwsproductie.",
        "Herman & Chomsky's eerste filter; Bergmans Nederlandse toepassing laat "
        "zien dat het systeem is 'ontworpen rond winstmaximalisatie, efficiëntie "
        "en risicovermijding'.",
        0.70,
        [(2, "the size, ownership, and profit orientation of the mass media",
          "het eerste filter uit Manufacturing Consent; typering"),
         (3, "zij bepalen de algemene strategie, keuren budgetten goed en "
             "beslissen over acquisities",
          "typering via sources/AI/propagandsmodel2.md (regel 25, 171)")])

    add_arg("stak_stemzeggenschap", "supporting",
        "De STAK oefent als houder van de stemgerechtigde aandelen het "
        "aandeelhoudersbenoemingsrecht over de Raad van Commissarissen uit — "
        "familiecontrole verlengt zich zo van het kapitaal naar het toezicht.",
        "Rechtstreeks gevolg van certificering plus het wettelijke "
        "benoemingsrecht van de aandeelhoudersvergadering: de zeggenschap ligt "
        "bij het stichtingsbestuur, niet bij de certificaathouders.",
        0.60,
        [(bw, "het stemrecht op gecertificeerde aandelen berust bij het "
              "administratiekantoor als aandeelhouder",
          "parafrase, Boek 2 BW; geen letterlijk citaat")])

    add_arg("commissarisbenoeming", "supporting",
        "De algemene vergadering van aandeelhouders benoemt de commissarissen — "
        "het wettelijke kanaal waarlangs het kapitaal het toezichtsorgaan "
        "samenstelt.",
        "Wettelijk benoemingsrecht; bij STAK-constructies wordt dit recht "
        "uitgeoefend door de verankerde zeggenschap (zie stak_stemzeggenschap).",
        0.80,
        [(bw, "de commissarissen worden benoemd door de algemene vergadering",
          "parafrase van art. 2:142/2:158 BW")])

    add_arg("directiebenoeming", "supporting",
        "De Raad van Commissarissen benoemt en ontslaat het bestuur "
        "(structuurregime) — het formele scharnier tussen toezicht en "
        "dagelijkse leiding.",
        "Wettelijke bevoegdheid bij de structuurvennootschap; daarmee is de "
        "keten aandeelhouder -> RvC -> directie institutioneel gesloten.",
        0.80,
        [(bw, "bij de structuurvennootschap worden de bestuurders benoemd door "
              "de raad van commissarissen",
          "parafrase van art. 2:162 BW")])

    add_arg("eigenaar_directiekeuze", "supporting",
        "Ongeacht de juridische vorm bepaalt de eigenaar feitelijk wie de "
        "mediaorganisatie leidt: bij DPG is Christian Van Thillo als executive "
        "chairman zelf het scharnier tussen familie en directie.",
        "De eigenaarsmacht over de top is geen abstractie maar gedocumenteerde "
        "praktijk: de families bepalen strategie, budgetten en acquisities.",
        0.65,
        [(3, "DPG Media is grotendeels eigendom van de Belgische familie Van "
             "Thillo, met Christian Van Thillo als de centrale figuur",
          "typering via sources/AI/propagandsmodel2.md (regel 23, 25, 29)")])

    add_arg("benoemingspolitiek", "supporting",
        "De directie/uitgever benoemt en ontslaat de hoofdredacteur; dat de ACM "
        "bij de DPG/RTL-overname onafhankelijke stichtingen met vetorecht op "
        "precies die benoeming afdwong, bevestigt institutioneel dat deze macht "
        "bij directie en eigenaar ligt.",
        "Een toezichthouder bouwt geen vetorecht op een benoemingsmacht die "
        "niet bestaat — de remedie bewijst het kanaal.",
        0.75,
        [(12, "onafhankelijke stichtingen met een prioriteitsaandeel dat "
              "vetorecht geeft over de benoeming en het ontslag van de "
              "hoofdredacteur",
          "typering van de ACM-voorwaarden via sources/AI/propagandsmodel2.md "
          "(regel 48)"),
         (3, "de invloed van de eigenaar op de bedrijfscultuur en de benoeming "
             "van hoofdredacteuren is onmiskenbaar",
          "typering via sources/AI/propagandsmodel2.md (regel 25)")])

    add_arg("preselectie_hoofdredacteur", "supporting",
        "Hoofdredacteuren bereiken hun stoel via anticipatoire selectie: een "
        "lange loopbaan van bewezen 'veilig', eigenaar-aligned oordeel — "
        "geïnternaliseerd, niet bevolen.",
        "Chomsky's pre-selectiemechanisme: wie fundamenteel afwijkt wordt niet "
        "benoemd of houdt het niet vol; de loyaliteit voelt van binnenuit als "
        "professioneel 'gezond verstand'.",
        0.65,
        [(2, "the selection of right-thinking personnel and the internalization "
             "of priorities",
          "typering van H&C's pre-selectie; geen letterlijk citaat"),
         (3, "een hoofdredacteur doet dit niet omdat hij een bevel krijgt van "
             "zijn aandeelhouder, maar omdat hij het als 'onrealistisch' "
             "beschouwt",
          "typering via sources/AI/propagandsmodel2.md (regel 146)")])

    add_arg("redactioneel_budgetcontrole", "supporting",
        "Redactiestatuten leggen de beslissingsbevoegdheid over strategische "
        "zaken zoals het budget bij de directie, waardoor redactionele "
        "autonomie via de geldkraan kan worden uitgehold.",
        "De budgetmacht is het feitelijke stuurkanaal van organisatie naar "
        "redactie: geen inhoudelijk bevel nodig als de capaciteit bepaald wordt.",
        0.70,
        [(3, "vaak leggen ze de uiteindelijke beslissingsbevoegdheid over "
             "strategische zaken, zoals het budget, bij de directie",
          "typering via sources/AI/propagandsmodel2.md (regel 110)")])

    # ════ Filter 2: Advertentie ════

    add_arg("commerciele_afhankelijkheid", "supporting",
        "Structurele afhankelijkheid van advertentie-inkomsten beloont een "
        "'supportive selling environment': een redactionele omgeving die de "
        "commerciële boodschap niet tegenwerkt — ook zonder expliciete druk.",
        "H&C's tweede filter; voor Nederland gedocumenteerd met 232 miljoen "
        "advertentieomzet kranten (2023) en 580 miljoen reclameomzet bij DPG.",
        0.75,
        [(2, "a supportive selling environment",
          "kernbegrip van het tweede filter, Manufacturing Consent"),
         (3, "de advertentieomzet voor kranten bedroeg in 2023 nog 232 miljoen "
             "euro; DPG's reclameomzet 580 miljoen",
          "typering via sources/AI/propagandsmodel2.md (regel 50-63)")])

    add_arg("commerciele_afhankelijkheid", "contradicting",
        "De lezersmarkt vormt met 79% van de totale dagbladomzet de "
        "belangrijkste inkomstenbron, wat de afhankelijkheid van adverteerders "
        "voor de printtitels relativeert.",
        "Dezelfde bron levert de relativering: voor abonnementsgedreven titels "
        "is de adverteerder secundair; de afhankelijkheid concentreert zich bij "
        "gratis en online platforms.",
        0.40,
        [(3, "in het Nederlandse dagbladmodel vormt de lezersmarkt, met 79% van "
             "de totale omzet, de belangrijkste inkomstenbron",
          "typering via sources/AI/propagandsmodel2.md (regel 52)")])

    # ════ Filter 3: Sourcing ════

    add_arg("pakketjournalistiek", "supporting",
        "Nederlandse kranten nemen op grote schaal ANP-berichten over "
        "('pakketjournalistiek'); gekrompen redacties zijn afhankelijk van de "
        "kant-en-klare nieuwsstroom, met homogenisering van het nieuwsbeeld "
        "als gevolg.",
        "Empirisch vastgesteld door CvdM en Radboud Universiteit; het ANP is "
        "het zenuwcentrum van de Nederlandse nieuwsstroom.",
        0.75,
        [(3, "onderzoek van zowel het CvdM als de Radboud Universiteit heeft "
             "aangetoond dat Nederlandse kranten in toenemende mate en op grote "
             "schaal gebruikmaken van ANP-berichten",
          "typering via sources/AI/propagandsmodel2.md (regel 67-69)")])

    add_arg("bron_afhankelijkheid", "supporting",
        "Deadline- en kostendruk dwingen redacties tot een symbiotische relatie "
        "met routineuze officiële bronnen; wie de informatie levert, levert het "
        "frame — de Irak-berichtgeving van 2003 als schoolvoorbeeld.",
        "H&C's derde filter; in de Nederlandse Irak-casus domineerde de versie "
        "van regeringswoordvoerders en inlichtingendiensten het nieuwsbeeld.",
        0.70,
        [(2, "reliance on information provided by government, business, and "
             "'experts'",
          "het derde filter uit Manufacturing Consent; typering"),
         (3, "de afhankelijkheid van officiële bronnen zorgde ervoor dat hun "
             "versie van het verhaal domineerde",
          "typering via sources/AI/propagandsmodel2.md (regel 65, 155)")])

    add_arg("expert_framing", "supporting",
        "Denktanks leveren schijnbaar objectieve experts en 'evidence-based' "
        "analyses die media als neutraal opvoeren, terwijl hun financiering de "
        "richting stuurt — 'argumenten op bestelling'.",
        "HCSS en Clingendael domineren de bronselectie bij defensie- en "
        "geopolitieke onderwerpen; hun rapporten geven beleid een aureool van "
        "wetenschappelijke legitimiteit.",
        0.65,
        [(2, "experts",
          "de gecoöpteerde expertlaag uit het derde filter, Manufacturing "
          "Consent; typering"),
         (3, "ze produceren effectief 'argumenten op bestelling' voor hun "
             "corporate sponsors",
          "typering via sources/AI/propagandsmodel2.md (regel 75-76, 130)")])

    # ════ Omroepbestel: het politieke benoemings- en sturingskanaal ════

    add_arg("politieke_benoeming_omroeptop", "supporting",
        "De benoeming van de NPO-top loopt wettelijk via de minister van OCW "
        "(raad van toezicht bij koninklijk besluit, raad van bestuur op "
        "zwaarwegend advies) — een formeel politiek benoemingskanaal.",
        "Het kanaal is geen interpretatie maar wettekst: de Mediawet legt de "
        "benoemingsketen van de publieke omroeptop bij de politiek.",
        0.80,
        [(10, "de leden van de raad van toezicht worden benoemd bij koninklijk "
              "besluit",
          "parafrase van de benoemingsbepalingen, Mediawet 2008 hoofdstuk 2")])

    add_arg("politieke_benoeming_omroeptop", "contradicting",
        "De benoemingsprocedure kent waarborgen (zwaarwegend advies, wettelijk "
        "verankerde onafhankelijkheid van de publieke omroep) die directe "
        "politieke sturing dempen.",
        "Dezelfde wet die het kanaal schept, begrenst het ook; het bestaan van "
        "het kanaal zegt nog niets over de benuttingsgraad.",
        0.35,
        [(10, "de publieke mediadienst is onafhankelijk van commerciële en "
              "politieke invloeden",
          "parafrase van de onafhankelijkheidsbepaling, Mediawet 2008")])

    add_arg("bestelsturing", "supporting",
        "De NPO heeft wettelijke sturingsmacht over het bestel: zij coördineert "
        "de kanalen en verdeelt budget en zendtijd over de omroepen.",
        "De sturingsbevoegdheid is wettelijk verankerd; via budget- en "
        "plaatsingsbeslissingen vormt de koepel het aanbod zonder zelf "
        "programma's te maken.",
        0.75,
        [(10, "de NPO is belast met de coördinatie en ordening van het "
              "media-aanbod op de kanalen",
          "parafrase, Mediawet 2008 art. 2.2 e.v.")])

    # ════ Draaideuren (Haagse stam, Luyendijk) ════

    add_arg("draaideurconstructie", "supporting",
        "Voormalige politici en ambtenaren vinden hun weg naar de media als "
        "columnist of commentator en nemen netwerk en referentiekader mee.",
        "De draaideur is onderdeel van Luyendijks stam-analyse: gedeelde "
        "loopbanen produceren een gedeeld wereldbeeld aan de opinietafels.",
        0.60,
        [(4, "voormalige politici en ambtenaren vinden hun weg naar de media "
             "als columnist of commentator",
          "typering via sources/AI/propagandsmodel2.md (regel 74); geen "
          "letterlijk boekcitaat")])

    add_arg("draaideur_journalistiek_politiek", "supporting",
        "Journalisten stappen over naar de politiek als woordvoerder of "
        "adviseur; de verstrengeling van netwerken bemoeilijkt kritische "
        "distantie.",
        "Zelfde stam-logica, andere richting: de overstap is binnen de Haagse "
        "stam een normale carrièrestap, geen breuk.",
        0.60,
        [(4, "journalisten maken de overstap naar de politiek als woordvoerder "
             "of adviseur",
          "typering via sources/AI/propagandsmodel2.md (regel 74); geen "
          "letterlijk boekcitaat")])

    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    c = cur.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
    con.close()
    print(f"Klaar: {n} argumenten, {c} citaties.")


if __name__ == "__main__":
    main()
