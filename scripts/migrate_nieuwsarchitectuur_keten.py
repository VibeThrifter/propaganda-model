#!/usr/bin/env python3
"""
Migratie: verbanden uit het document 'De Architectuur van het Nederlandse
Nieuws — Een Systeemanalyse (v4.0)' (aangeleverde AI-analyse, juni 2026).

Het document overlapt grotendeels met bestaande modelstructuur (eigendom,
elite-fora, voorlichting, draaideuren, algoritmes). Twee echte gaten worden
hier gedicht, plus vijf mechanismen krijgen hun allereerste onderbouwing:

  1. De internationale persbureau-laag ontbrak volledig: Reuters, AP en AFP
     als entiteiten, met bron_van-relaties naar NOS en ANP. Kernbron:
     'Het Persbureau in Perspectief' (Vermaas & Janssen, Stimuleringsfonds
     voor de Pers, nov. 2009): NL-bureaus zijn voor 80-90% aangewezen op
     internationale bureaus voor buitenlandnieuws; ANP werkt samen met AFP
     (exclusief foto/video, vgl. Villamedia 5-1-2018) en dpa.
  2. De veiligheidsstaat als bron ontbrak: NCTV als gezagsinstituut, met
     bron_van naar NOS (periodiek DTN; berichtgeving steunt primair op de
     NCTV zelf; onderliggende inlichtingen journalistiek niet onafhankelijk
     verifieerbaar — structureel gegeven, geen verwijt).

Eerste argumenten (theorie-laag) voor:
  - etikettering (13)            <- Hallin 1986, sphere of deviance
  - spectrum_bewaking (35)       <- Chomsky 1998, letterlijk citaat p. 43
  - verifieerbaarheidsroutine(107)<- SVDJ-rapport: spanningsveld snelheid/
                                     controle; verificatie uitbesteed
                                     (Diekerhof 2008; Mediamonitor 2007)
  - denktank_levert_expert (118) <- Herman & Chomsky 1988 (bron 2 bestond);
                                     NL-instantiatie al gemodelleerd
                                     (financiering Defensie/BZ/NAVO ->
                                     Clingendael/HCSS)
  - institutioneel_gezag (86)    <- DTN-spoor: NOS-bericht 11-6-2024 steunt
                                     primair op NCTV

Bewust NIET toegevoegd (en waarom):
  - Geen nieuwe mechanismen/rollen/hyperedges: alle fenomenen in het document
    mappen op bestaande structuur (waarneembare output != nieuwe structuur).
  - Bellingcat/NED: relevant maar beladen; vergt eigen onderzoeksronde met
    primaire financieringsdocumentatie. Niet en passant.
  - Astroturfing-mechanisme: document noemt geen gedocumenteerde NL-casus.
  - BlackRock/Vanguard -> adverteerders-edge: diffuse claim zonder bron;
    entiteiten bestaan al, eigendomslogica zit in bestaande mechanismen.
  - Nieuwsmijders: effect aan publiekszijde, geen filter; hooguit later een
    argument bij publieksfragmentatie (154).
  - Nieuwspoort/journalistieke prijzen: speculatief; de sociale arena zit al
    in de haagse_stam-hyperedge en gecoordineerde_voorlichting.
  - Stringer/fixer-laag en het ziekenhuisvoorbeeld: het 'belspel'-scenario is
    expliciet fictief ('Laten we een voorbeeld nemen') — illustratie, geen
    bewijs. UPI (in 2009-rapport genoemd) is feitelijk marginaal.

Backup-then-migrate; idempotent (SELECT-first op titel/naam/claim);
tweemaal draaien verandert niets.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-nieuwsarchitectuur-2026-06"
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

    # ---- BRONNEN -------------------------------------------------------------
    def add_source(title, stype, author, publisher, date, reliability,
                   url=None, summary=None):
        row = cur.execute("SELECT id FROM sources WHERE title=?",
                          (title,)).fetchone()
        if row:
            print(f"bron bestaat al: {title[:50]}")
            return row[0]
        cur.execute(
            """INSERT INTO sources (title, author, source_type, publisher,
               date_published, language, summary, reliability)
               VALUES (?,?,?,?,?,?,?,?)""",
            (title, author, stype, publisher, date,
             "en" if publisher in ("Oxford University Press", "Odonian Press")
             else "nl", summary, reliability))
        sid = cur.lastrowid
        if url:
            cur.execute(
                """INSERT INTO source_locations (source_id, location_type,
                   location, accessed_at) VALUES (?,?,?,?)""",
                (sid, "url", url, ACCESSED))
        print(f"+ bron {sid}: {title[:50]}")
        return sid

    S_RAPPORT = add_source(
        "Het Persbureau in Perspectief. Rol, functies en kernwaarden van "
        "Nederlandse persbureaus",
        "rapport", "Vermaas, K. & Janssen, F.",
        "Stimuleringsfonds voor de Pers", "2009-11-01", "institutioneel",
        url="https://www.svdj.nl/wp-content/uploads/2015/12/"
            "061109-S29-Het-Persbureau-in-Perspectief.pdf",
        summary="Onderzoek in opdracht van het Stimuleringsfonds voor de "
                "Pers (november 2009) naar rol, functies en kernwaarden van "
                "Nederlandse persbureaus; documenteert de afhankelijkheid "
                "van internationale bureaus (80-90% van het buitenland-"
                "nieuws), de ANP-samenwerking met AFP en dpa, en het "
                "spanningsveld snelheid/controle.")
    S_HALLIN = add_source(
        "The 'Uncensored War': The Media and Vietnam",
        "boek", "Hallin, D.C.", "Oxford University Press", "1986-01-01",
        "academisch",
        url="https://books.google.com/books/about/The_Uncensored_War.html"
            "?id=kmpYUSYLD8MC",
        summary="Standaardwerk over de Vietnam-verslaggeving; introduceert "
                "de drie sferen (consensus, legitieme controverse, "
                "deviantie) die bepalen welke stemmen journalistiek "
                "neutraal, kritisch of diskwalificerend worden behandeld.")
    S_CHOMSKY = add_source(
        "The Common Good",
        "boek", "Chomsky, N.", "Odonian Press", "1998-01-01", "primair",
        url="https://chomsky.info/commongood01/",
        summary="Interviewbundel (met David Barsamian); bevat op p. 43 de "
                "kernformulering van het 'spectrum van toegestane opinie'.")
    S_VILLA_AFP = add_source(
        "ANP levert internationale video's van AFP",
        "nieuwsartikel", None, "Villamedia", "2018-01-05",
        "kwaliteitsjournalistiek",
        url="https://www.villamedia.nl/artikel/"
            "anp-begint-met-internationale-videos",
        summary="Vakbladbericht: ANP levert vanaf januari 2018 exclusief "
                "voor de Nederlandse markt AFP-video's en had al een "
                "exclusief contract voor AFP-foto's.")
    S_NOS_DTN = add_source(
        "NCTV: terreurdreiging licht toegenomen, op een na hoogste niveau "
        "blijft in stand",
        "nieuwsartikel", None, "NOS", "2024-06-11",
        "kwaliteitsjournalistiek",
        url="https://nos.nl/artikel/2524087",
        summary="NOS-bericht over het halfjaarlijkse Dreigingsbeeld "
                "Terrorisme Nederland; steunt primair op de NCTV zelf "
                "(coördinator Aalbersberg en het DTN-rapport).")
    S_NCTV = add_source(
        "Dreigingsbeeld Terrorisme Nederland (onderwerpspagina NCTV)",
        "website", None, "NCTV", None, "institutioneel",
        url="https://www.nctv.nl/onderwerpen/d/dtn",
        summary="Institutionele pagina over het DTN; recente edities "
                "verschijnen halfjaarlijks (juni/december).")

    # bestaande bron: Manufacturing Consent (id-onafhankelijk opzoeken)
    row = cur.execute("SELECT id FROM sources WHERE title LIKE "
                      "'Manufacturing Consent%'").fetchone()
    if not row:
        raise SystemExit("FOUT: bron 'Manufacturing Consent' ontbreekt")
    S_HC = row[0]

    # ---- ENTITEITEN ----------------------------------------------------------
    def add_entity(name, etype, role, description, active_from=None):
        row = cur.execute("SELECT id FROM entities WHERE name=?",
                          (name,)).fetchone()
        if row:
            print(f"entiteit bestaat al: {name}")
            return row[0]
        cur.execute(
            """INSERT INTO entities (name, type, primary_role_id,
               description, active_from) VALUES (?,?,?,?,?)""",
            (name, etype, roles[role], description, active_from))
        eid = cur.lastrowid
        cur.execute("INSERT INTO entity_roles (entity_id, role_id) "
                    "VALUES (?,?)", (eid, roles[role]))
        print(f"+ entiteit {eid}: {name}")
        return eid

    E_REUTERS = add_entity(
        "Reuters", "persbureau", "persbureau",
        "Brits internationaal persbureau (opgericht 1851). Met AP en AFP "
        "een van de drie bureaus die wereldwijd uitgebreid reportagewerk "
        "doen; samen vormen ze de ruggengraat van het buitenlandnieuws in "
        "Nederlandse media.", active_from="1851")
    E_AP = add_entity(
        "AP (Associated Press)", "persbureau", "persbureau",
        "Amerikaans internationaal persbureau (coöperatie van Amerikaanse "
        "media). Met Reuters en AFP een van de drie bureaus die wereldwijd "
        "uitgebreid reportagewerk doen.")
    E_AFP = add_entity(
        "AFP (Agence France-Presse)", "persbureau", "persbureau",
        "Frans internationaal persbureau (opgericht 1944, erfgenaam van "
        "Havas). In Nederland exclusief vertegenwoordigd door het ANP "
        "(foto- en videocontracten).", active_from="1944")
    E_NCTV = add_entity(
        "NCTV (Nationaal Coördinator Terrorismebestrijding en Veiligheid)",
        "overheidsinstelling", "gezagsinstituut",
        "Coördineert terrorismebestrijding en crisisbeheersing onder het "
        "ministerie van J&V. Publiceert periodiek het Dreigingsbeeld "
        "Terrorisme Nederland (DTN), de officiële inschatting die het "
        "Nederlandse veiligheidsdiscours mede bepaalt; de onderliggende "
        "inlichtingen zijn journalistiek niet onafhankelijk verifieerbaar.",
        active_from="2012")

    def entity_id(name):
        row = cur.execute("SELECT id FROM entities WHERE name=?",
                          (name,)).fetchone()
        if not row:
            raise SystemExit(f"FOUT: entiteit ontbreekt: {name}")
        return row[0]

    E_NOS = entity_id("NOS")
    E_ANP = entity_id("ANP")

    def mech_id(name):
        row = cur.execute("SELECT id FROM mechanisms WHERE name=?",
                          (name,)).fetchone()
        if not row:
            raise SystemExit(f"FOUT: mechanisme ontbreekt: {name}")
        return row[0]

    # ---- RELATIES ------------------------------------------------------------
    def add_relation(src, tgt, rtype, mech, desc, certainty, influence):
        row = cur.execute(
            "SELECT id FROM relations WHERE source_id=? AND target_id=? "
            "AND relation_type=?", (src, tgt, rtype)).fetchone()
        if row:
            print(f"relatie bestaat al: {src}->{tgt} [{rtype}]")
            return row[0]
        cur.execute(
            """INSERT INTO relations (source_id, target_id, relation_type,
               mechanism_id, description, certainty, influence)
               VALUES (?,?,?,?,?,?,?)""",
            (src, tgt, rtype, mech, desc, certainty, influence))
        rid = cur.lastrowid
        print(f"+ relatie {rid}: {src}->{tgt} [{rtype}] c={certainty} "
              f"i={influence}")
        return rid

    R_REU_NOS = add_relation(
        E_REUTERS, E_NOS, "bron_van", mech_id("pakketjournalistiek"),
        "NOS leunt voor buitenlandnieuws op kopij en beeld van de grote "
        "internationale persbureaus; Reuters is daarvan met AP de kern.",
        0.85, 0.55)
    R_AP_NOS = add_relation(
        E_AP, E_NOS, "bron_van", mech_id("pakketjournalistiek"),
        "NOS leunt voor buitenlandnieuws op kopij en beeld van de grote "
        "internationale persbureaus, waaronder AP.",
        0.85, 0.5)
    R_AFP_ANP = add_relation(
        E_AFP, E_ANP, "bron_van", None,
        "ANP vertegenwoordigt AFP exclusief op de Nederlandse markt "
        "(foto, sinds 2018 ook video) en verwerkt AFP-kopij in zijn "
        "buitenlandpakket. Persbureau->persbureau: geen rolmechanisme; "
        "de doorvertaling naar titels loopt via pakketjournalistiek.",
        0.9, 0.55)
    R_REU_ANP = add_relation(
        E_REUTERS, E_ANP, "bron_van", None,
        "Nederlandse persbureaus zijn voor 80-90% van het buitenlandnieuws "
        "aangewezen op de internationale bureaus, waarop zij geabonneerd "
        "zijn (SVDJ-rapport 2009).",
        0.8, 0.5)
    R_NCTV_NOS = add_relation(
        E_NCTV, E_NOS, "bron_van", mech_id("bron_afhankelijkheid"),
        "Het periodieke DTN en NCTV-duiding worden als officiële "
        "inschatting overgenomen; de onderliggende inlichtingen zijn "
        "journalistiek niet onafhankelijk verifieerbaar (structureel "
        "gegeven door geheimhouding, geen redactioneel verwijt).",
        0.9, 0.4)

    # ---- ARGUMENTEN ----------------------------------------------------------
    def add_arg(target_col, target_id, stance, claim, reasoning, weight,
                citations):
        assert target_col in ("relation_id", "mechanism_id")
        row = cur.execute(
            f"SELECT id FROM arguments WHERE {target_col}=? AND claim=?",
            (target_id, claim)).fetchone()
        if row:
            print(f"argument bestaat al ({target_col}={target_id})")
            return row[0]
        cur.execute(
            f"""INSERT INTO arguments ({target_col}, stance, claim,
                reasoning, weight, status, contributed_by)
                VALUES (?,?,?,?,?,?,?)""",
            (target_id, stance, claim, reasoning, weight,
             "ongecontroleerd", CONTRIB))
        aid = cur.lastrowid
        for sid, quote, ctx in citations:
            cur.execute(
                "INSERT INTO citations (argument_id, source_id, quote, "
                "context) VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument ({stance}, w={weight}) bij {target_col}="
              f"{target_id}, {len(citations)} citatie(s)")
        return aid

    # -- theorie: eerste onderbouwing van vijf mechanismen ---------------------
    add_arg("mechanism_id", mech_id("etikettering"), "supporting",
        "Kritiek buiten het legitieme debat wordt geneutraliseerd door de "
        "boodschapper te etiketteren ('activist', 'omstreden', "
        "'Poetin-versteher') in plaats van het argument te weerleggen; "
        "Hallins deviantiesfeer beschrijft dit als vast journalistiek "
        "sorteermechanisme.",
        "Hallin laat aan de Vietnam-verslaggeving zien dat het politieke "
        "discours in drie sferen uiteenvalt; binnen de deviantiesfeer geldt "
        "de neutraliteitsnorm niet meer en mogen stemmen genegeerd of "
        "gediskwalificeerd worden. Dat vergt geen redactionele opzet: het "
        "etiket is de routinematige markering van de grens van het "
        "toelaatbare, en de grens verschuift mee met de elite-consensus.",
        0.55,
        [(S_HALLIN,
          "Hallin verdeelt het politieke discours in drie concentrische "
          "sferen — consensus, legitieme controverse en deviantie; in de "
          "deviantiesfeer hoeven journalisten standpunten niet meer "
          "neutraal te behandelen, maar mogen ze die negeren of "
          "diskwalificeren.",
          "typering van het kernschema uit The 'Uncensored War' (1986); "
          "geen letterlijk citaat")])

    add_arg("mechanism_id", mech_id("spectrum_bewaking"), "supporting",
        "Een levendig debat binnen begrensde premissen versterkt juist die "
        "premissen: het ideologische werk zit in de grenzen van het debat, "
        "niet in de uitkomst ervan.",
        "Chomsky's eigen kernformulering van het concept waarop dit "
        "mechanisme is gebaseerd. Het mechanisme vergt geen censuur: zolang "
        "de premissen (van bijvoorbeeld militaire steun of marktordening) "
        "buiten de vraagstelling blijven, bevestigt elk debat erbinnen ze.",
        0.6,
        [(S_CHOMSKY,
          "The smart way to keep people passive and obedient is to "
          "strictly limit the spectrum of acceptable opinion, but allow "
          "very lively debate within that spectrum — even encourage the "
          "more critical and dissident views. That gives people the sense "
          "that there's free thinking going on, while all the time the "
          "presuppositions of the system are being reinforced by the "
          "limits put on the range of the debate.",
          "letterlijk citaat (p. 43), geverifieerd via chomsky.info "
          f"(officieel excerpt), geraadpleegd {ACCESSED}")])

    add_arg("mechanism_id", mech_id("verifieerbaarheidsroutine"),
        "supporting",
        "De dubbele eis 'eerste én nooit fout' verschuift verificatie naar "
        "wat snel en goedkoop controleerbaar is, terwijl afnemers hun "
        "controle de facto uitbesteden aan het persbureau.",
        "Het SVDJ-rapport documenteert beide helften: het permanente "
        "spanningsveld tussen snelheid en controle bij het bureau zelf, én "
        "de uitbestede verificatie bij de afnemers (onderzoek School voor "
        "Journalistiek/Diekerhof 2008; Mediamonitor 2007 over onbewerkt "
        "doorgegeven persbureauberichten). Officiële verklaringen winnen "
        "dan structureel van traag, betwistbaar onderzoek.",
        0.6,
        [(S_RAPPORT,
          "Als een persbureau zijn werk goed doet, hoeft geen enkele krant "
          "of mediapartij meer de berichten te controleren.",
          "letterlijk citaat van een geïnterviewde expert (p. 9)"),
         (S_RAPPORT,
          "de persbureaus moeten constant de afweging maken tussen snel "
          "zijn (want anders hebben anderen het nieuws al opgepikt en "
          "wordt de waarde van het persbureau minder) en alle feiten in "
          "een bericht helemaal controleren",
          "letterlijk citaat (p. 9; herhaald p. 39)"),
         (S_RAPPORT,
          "dagbladjournalisten [controleren] informatie lang niet altijd "
          "zelf op juistheid. Ze gaan ervan uit dat persbureaus, "
          "deskundigen en voorlichters die ze kennen, voor de juistheid "
          "van de berichtgeving zullen instaan",
          "vrijwel letterlijk (p. 21); samenvatting in het rapport van "
          "onderzoek Kenniskring Crossmedia Content o.l.v. Els Diekerhof "
          "(School voor Journalistiek Utrecht, 2008)")])

    add_arg("mechanism_id", mech_id("denktank_levert_expert"), "supporting",
        "Denktanks leveren de vaste duiders van het veiligheids- en "
        "buitenlandnieuws: hun deskundigen verschijnen als onafhankelijke "
        "experts, terwijl hun instituten mede door belanghebbenden "
        "(ministeries, NAVO) gefinancierd worden.",
        "Kern van het sourcing-filter bij Herman & Chomsky: belanghebbenden "
        "financieren de instituten die het aanbod aan 'gezaghebbende' "
        "expertise vormen. De Nederlandse instantiatie staat al in het "
        "praktijkmodel (financieringsrelaties Defensie/BZ/NAVO -> "
        "Clingendael en HCSS; expert_framing-relaties van beide naar alle "
        "grote titels). Emergent, geen verborgen agenda: financiering "
        "stuurt onderzoeksagenda en expertselectie, niet per se de "
        "individuele uitspraak.",
        0.55,
        [(S_HC,
          "Machtige belanghebbenden financieren denktanks en kopen zo de "
          "expertise in die het publieke debat van gezaghebbende duiding "
          "voorziet.",
          "parafrase van het sourcing-filter (derde filter) uit "
          "Manufacturing Consent (1988); geen letterlijk citaat")])

    add_arg("mechanism_id", mech_id("institutioneel_gezag"), "supporting",
        "Officiële dreigings- en risico-inschattingen worden als feit "
        "overgenomen, ook waar de onderliggende informatie journalistiek "
        "niet onafhankelijk te verifiëren is.",
        "Structureel gegeven, geen redactioneel verwijt: geheimhouding van "
        "inlichtingen maakt onafhankelijke verificatie onmogelijk, dus "
        "berust overname noodzakelijk op institutioneel gezag. Het "
        "DTN-spoor illustreert dit: het NOS-bericht steunt volledig op de "
        "NCTV-coördinator en het rapport zelf. Eén casus is een spoor, "
        "geen media-inhoudsanalyse; het gewicht blijft daarom beperkt.",
        0.5,
        [(S_NOS_DTN,
          "De terroristische dreiging in Nederland is de afgelopen "
          "maanden licht toegenomen; het dreigingsniveau blijft op 4 "
          "(substantieel) — aldus NCTV-coördinator Aalbersberg in zijn "
          "halfjaarbericht.",
          "typering van de opening van het NOS-bericht (11 juni 2024); "
          "het bericht steunt primair op de NCTV zelf"),
         (S_NCTV,
          "Het DTN verschijnt periodiek (recente edities juni en "
          "december) als officiële inschatting van de terroristische "
          "dreiging in Nederland.",
          f"typering van de NCTV-onderwerpspagina, geraadpleegd "
          f"{ACCESSED}")])

    # -- praktijk: één argument per nieuwe relatie ------------------------------
    add_arg("relation_id", R_REU_NOS, "supporting",
        "Reuters behoort tot de drie bureaus die wereldwijd reportagewerk "
        "doen en waarop Nederlandse media voor buitenlandnieuws leunen.",
        "Gedocumenteerd in het SVDJ-rapport; de NOS noemt internationale "
        "persbureaus zelf als eerstemeldingsbron in haar journalistieke "
        "verantwoording.",
        0.5,
        [(S_RAPPORT,
          "AP en Reuters zijn samen met AFP de enige die uitgebreid "
          "internationaal reportagewerk doen. (...) de meesten gebruiken "
          "de grote persbureaus voor buitenlands nieuws, net als "
          "Nederlandse persbureaus.",
          "letterlijk citaat uit de bijlage (p. 45)")])
    add_arg("relation_id", R_AP_NOS, "supporting",
        "AP behoort tot de drie bureaus die wereldwijd reportagewerk doen "
        "en waarop Nederlandse media voor buitenlandnieuws leunen.",
        "Zie het SVDJ-rapport; zelfde grondslag als de Reuters-relatie.",
        0.5,
        [(S_RAPPORT,
          "AP en Reuters zijn samen met AFP de enige die uitgebreid "
          "internationaal reportagewerk doen. (...) de meesten gebruiken "
          "de grote persbureaus voor buitenlands nieuws, net als "
          "Nederlandse persbureaus.",
          "letterlijk citaat uit de bijlage (p. 45)")])
    add_arg("relation_id", R_AFP_ANP, "supporting",
        "ANP heeft een gedocumenteerde, deels exclusieve samenwerking met "
        "AFP voor de Nederlandse markt.",
        "De samenwerking staat in het SVDJ-rapport (2009) en is in 2018 "
        "uitgebreid met exclusieve videolevering (Villamedia).",
        0.65,
        [(S_RAPPORT,
          "Het ANP heeft bijvoorbeeld een samenwerking met het Franse AFP "
          "en Duitse dpa.",
          "letterlijk citaat (p. 10)"),
         (S_VILLA_AFP,
          "Het ANP levert vanaf maandag, exclusief voor de Nederlandse "
          "markt, video's van het Franse persbureau AFP. Het ANP had al "
          "een exclusief contract voor AFP-foto's.",
          "letterlijk citaat (Villamedia, 5 januari 2018)")])
    add_arg("relation_id", R_REU_ANP, "supporting",
        "Nederlandse persbureaus zijn voor het overgrote deel van hun "
        "buitenlandnieuws aangewezen op de internationale bureaus, "
        "waaronder Reuters.",
        "Het cijfer stamt uit Servaes & Tonnaer (1992), aangehaald en "
        "actueel geacht in het SVDJ-rapport (2009); sindsdien is het "
        "correspondentennet verder gekrompen. Certainty blijft 0.8 omdat "
        "de meting gedateerd is.",
        0.55,
        [(S_RAPPORT,
          "Volgens Servaes en Tonnaer (1992) zijn de Nederlandse bureaus "
          "voor 80 tot 90 procent aangewezen op internationale bureaus "
          "als het gaat om buitenlands nieuws.",
          "letterlijk citaat (p. 10)"),
         (S_RAPPORT,
          "Alle bureaus hebben een abonnement op de internationale "
          "bureaus en gebruiken de nieuwsberichten van internationale "
          "bureaus voor buitenlandse berichtgeving.",
          "letterlijk citaat (p. 10)")])
    add_arg("relation_id", R_NCTV_NOS, "supporting",
        "NOS bericht periodiek over het DTN op gezag van de NCTV; "
        "onafhankelijke verificatie van de onderliggende inlichtingen is "
        "niet mogelijk.",
        "Het NOS-bericht van 11 juni 2024 steunt primair op de "
        "NCTV-coördinator en het rapport; vergelijkbare berichten "
        "verschijnen bij elke DTN-editie. Dat is de normale werking van "
        "bron_afhankelijkheid bij gesloten bronnen, geen incident.",
        0.6,
        [(S_NOS_DTN,
          "De terroristische dreiging in Nederland is de afgelopen "
          "maanden licht toegenomen; het dreigingsniveau blijft op 4 "
          "(substantieel) — aldus NCTV-coördinator Aalbersberg in zijn "
          "halfjaarbericht.",
          "typering van de opening van het NOS-bericht (11 juni 2024)")])

    con.commit()

    # ---- SAMENVATTING --------------------------------------------------------
    print("---")
    for label in ("entities", "relations", "arguments", "citations",
                  "sources", "source_locations"):
        n = cur.execute(f"SELECT COUNT(*) FROM {label}").fetchone()[0]
        print(f"{label:17s}: {n}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
