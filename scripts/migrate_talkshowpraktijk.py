#!/usr/bin/env python3
"""
Migratie: praktijklaag bij de talkshowlogica-ronde (juni 2026).

Vervolg op migrate_talkshowlogica_kijkcijfers.py, op verzoek: de
getuigenissen uit het DNW-interview (bron 67) worden wél als concrete
relaties opgenomen, met certainty-scores die de bronbasis eerlijk
weerspiegelen (één opiniebron, deels eigen partij): 0.35-0.6 in plaats
van weglaten. De twee onafhankelijke scores van het model dragen de
nuance: certainty = "bestaat deze relatie?", influence = effect op
berichtgeving.

Nieuwe entiteiten:
- Op1 (talkshowprogramma NPO 1, sinds 2020) — mediaorganisatie
- Vandaag Inside (talkshowprogramma SBS6/Talpa, sinds 2022) — mediaorganisatie
- Talitha Muusse (opiniemaker, oud-presentator Op1) — persoon
- Nationaal Media Onderzoek (NMO, kijkcijfermeting, sinds 2022) — stichting

Nieuwe relaties (alle onderbouwd met praktijk-argument + citaten uit
bron 67; status ongecontroleerd):
1. NMO -beinvloeding-> Op1 [kijkcijferdisciplinering] c=0.60 i=0.40
   NB: NMO is het meetKANAAL; de eigenlijke afzender in de theorielaag
   is het publiek (zapgedrag). Eerstehands (Muusse ontving en gebruikte
   de cijfers zelf) en consistent met de branchestandaard -> hoogste
   certainty van deze ronde.
2. NPO -censuur-> Talitha Muusse [spectrum_bewaking] c=0.35 i=0.15
   Eigen getuigenis van de geweerde partij, anonieme bron binnen de
   omroep, niet onafhankelijk verifieerbaar -> lage certainty.
3. de Volkskrant -beinvloeding-> RTL Nederland [intermedia_agendering]
   c=0.40 i=0.25 — programmering RTL Tonight georiënteerd op "het debat
   in de Volkskrant" (getuigenis Vlam over de toenmalige programmaleiding).
4. Vandaag Inside -beinvloeding-> Tweede Kamer [media_agendering]
   c=0.45 i=0.30 — Den Haag volgt wat de best bekeken talkshow zegt.

Backup-then-migrate; idempotent; tweemaal draaien verandert niets.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-talkshowlogica-2026-06"

S_DNW_TITLE = ("De Nieuwe Wereld: Talitha Muusse en Victor Vlam over de "
               "talkshowwereld")
BASE = ("Letterlijk citaat uit het ASR-transcript "
        "(sources/2026-06-10_vlam-muusse_talkshowwereld.txt); niet "
        "onafhankelijk tegen de uitzending geverifieerd; transcript "
        "zonder sprekerlabels — sprekertoeschrijving o.b.v. context. ")


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

    S_DNW = cur.execute("SELECT id FROM sources WHERE title=?",
                        (S_DNW_TITLE,)).fetchone()
    if not S_DNW:
        raise SystemExit("FOUT: draai eerst "
                         "migrate_talkshowlogica_kijkcijfers.py (bron 67)")
    S_DNW = S_DNW[0]

    def mech(name):
        return cur.execute("SELECT id FROM mechanisms WHERE name=?",
                           (name,)).fetchone()[0]

    def ent(name):
        return cur.execute("SELECT id FROM entities WHERE name=?",
                           (name,)).fetchone()[0]

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

    def add_relation(src, tgt, rtype, mech_id, desc, certainty, influence):
        row = cur.execute(
            "SELECT id FROM relations WHERE source_id=? AND target_id=? "
            "AND relation_type=?", (src, tgt, rtype)).fetchone()
        if row:
            print(f"relatie bestaat al: {src} -{rtype}-> {tgt}")
            return row[0]
        cur.execute(
            """INSERT INTO relations (source_id, target_id, relation_type,
               mechanism_id, description, certainty, influence)
               VALUES (?,?,?,?,?,?,?)""",
            (src, tgt, rtype, mech_id, desc, certainty, influence))
        rid = cur.lastrowid
        print(f"+ relatie {rid}: {src} -{rtype}-> {tgt} "
              f"(c={certainty}, i={influence})")
        return rid

    def add_arg(rel_id, claim, reasoning, weight, citations):
        row = cur.execute(
            "SELECT id FROM arguments WHERE relation_id=? AND claim=?",
            (rel_id, claim)).fetchone()
        if row:
            print(f"argument bestaat al (relation_id={rel_id})")
            return row[0]
        cur.execute(
            """INSERT INTO arguments (relation_id, stance, claim,
               reasoning, weight, status, contributed_by)
               VALUES (?,?,?,?,?,?,?)""",
            (rel_id, "supporting", claim, reasoning, weight,
             "ongecontroleerd", CONTRIB))
        aid = cur.lastrowid
        for quote, ctx in citations:
            cur.execute(
                "INSERT INTO citations (argument_id, source_id, quote, "
                "context) VALUES (?,?,?,?)", (aid, S_DNW, quote, ctx))
        print(f"+ argument (w={weight}) bij relatie {rel_id}, "
              f"{len(citations)} citatie(s)")
        return aid

    # ---- entiteiten -----------------------------------------------------------
    E_OP1 = add_entity(
        "Op1", "mediaorganisatie", "mediaorganisatie",
        "Dagelijkse late-night talkshow op NPO 1 (sinds 2020), gemaakt "
        "door wisselende ledenomroepen met duo-presentatie. Eigen "
        "redactie en eindredactie; in het model relevant als casus voor "
        "kijkcijferdisciplinering (minutenanalyses) en als context van "
        "de getuigenis van oud-presentator Talitha Muusse.",
        active_from="2020")
    E_VI = add_entity(
        "Vandaag Inside", "mediaorganisatie", "mediaorganisatie",
        "Dagelijkse talkshow op SBS6 (Talpa; sinds 2022, voortzetting "
        "van Veronica Inside), doorgaans de best bekeken talkshow van "
        "Nederland (rond de 1 miljoen kijkers). Personality-driven "
        "(vaste tafel rond Johan Derksen, Wilfred Genee, René van der "
        "Gijp); centrum-rechtse/populistische signatuur volgens "
        "media-analisten.",
        active_from="2022")
    E_MUUSSE = add_entity(
        "Talitha Muusse", "persoon", "columnist_opiniemaker",
        "Opiniemaker en presentator (De Nieuwe Wereld); presenteerde in "
        "2021 kort de NPO-talkshow Op1 en vertrok na een conflict, naar "
        "eigen zeggen gevolgd door een feitelijke boycot bij grote "
        "NPO-talkshows. Eerstehands bron over de werkwijze van "
        "talkshowredacties.",
        active_from="2020")
    E_NMO = add_entity(
        "Nationaal Media Onderzoek (NMO)", "stichting", "kennisinstituut",
        "Gezamenlijk bereiksonderzoek van de Nederlandse mediabranche "
        "(opvolger van o.a. SKO, sinds 2022); meet met een panel van "
        "1.850 huishoudens (ca. 3.900 personen, 6+) per minuut het "
        "tv-kijkgedrag. De cijfers zijn de feitelijke valuta van de "
        "advertentiemarkt en het dagelijkse sturingsinstrument van "
        "redacties.",
        active_from="2022")

    # ---- relaties + argumenten -------------------------------------------------
    R1 = add_relation(
        E_NMO, E_OP1, "beinvloeding", mech("kijkcijferdisciplinering"),
        "De dag- en minutencijfers van het kijkonderzoek stuurden bij "
        "Op1 de evaluatie van gasten ('wegzepper') en de beslissing wie "
        "wordt teruggevraagd (getuigenis oud-presentator). NB: het NMO "
        "is het meetkanaal — de eigenlijke afzender in de theorielaag is "
        "het publiek (zapgedrag), gemonetariseerd door adverteerders.",
        0.60, 0.40)
    add_arg(R1,
        "Op1 ontving dagcijfers en minutenanalyses (per spreker, per "
        "minuut) en evalueerde daarop welke gasten 'wegzeppers' waren en "
        "wie werd teruggevraagd.",
        "Eerstehands: Muusse ontving en gebruikte deze cijfers zelf als "
        "presentator; de praktijk is bovendien branchestandaard (Vlam: "
        "'alle keuzes worden op basis van deze grafiekjes gemaakt'). "
        "Eén bron, maar onomstreden werkwijzebeschrijving — vandaar "
        "certainty 0.6 en geen hoger.",
        0.5,
        [("Ja, dan de minutenanalyse die krijg je ook, maar die kwam dan "
          "meestal wat later en dan kon je echt precies zien eh daar "
          "gaan wij het ook over hebben, maar afhankelijk van per "
          "spreker, per minuut wie er aan het woord is. En soms zie je "
          "dus echt gewoon van wie is een wegzepper?",
          BASE + "Spreker: Muusse, over haar tijd bij Op1."),
         ("En alle keuzes worden ook op basis van deze grafiekjes "
          "gemaakt.",
          BASE + "Spreker: Vlam, over de minutenanalyse als "
          "sturingsinstrument.")])

    R2 = add_relation(
        ent("NPO"), E_MUUSSE, "censuur", mech("spectrum_bewaking"),
        "Volgens Muusse werd een gepland talkshowgesprek over haar "
        "NPO-kritiek last-minute geschrapt na druk vanuit de NPO (aldus "
        "de presentator van dat programma), en bestaat bij meerdere "
        "grote NPO-talkshows een informele policy om haar niet meer uit "
        "te nodigen. Eigen getuigenis van de geweerde partij, anonieme "
        "bron, niet onafhankelijk verifieerbaar — vandaar de lage "
        "certainty.",
        0.35, 0.15)
    add_arg(R2,
        "Een gepland NPO-talkshowitem over kritiek op de NPO werd "
        "last-minute geschrapt na druk vanuit de NPO, en redacties van "
        "grote NPO-talkshows hanteren een informele niet-uitnodigen-"
        "policy jegens Muusse.",
        "Laag gewicht: de getuige is zelf de geweerde partij, de "
        "omroepbron is anoniem en de claim is niet onafhankelijk te "
        "verifiëren. Tegelijk is dit het type backstage-gebeurtenis dat "
        "zelden anders dan via getuigenissen zichtbaar wordt; opgenomen "
        "mét die kanttekening.",
        0.3,
        [("omdat er toch echt wat druk was vanuit de NPO van dat gesprek "
          "gaan we echt niet faciliteren. Dat gaan we echt niet doen. "
          "Dus je schrapt het maar. En het stond al geprogrammeerd.",
          BASE + "Spreker: Muusse, die een presentator citeert "
          "(tweedehands binnen de getuigenis)."),
         ("dat er echt toch een soort policy was binnen een aantal eh "
          "grote NPO talkshows van doordat ik zo kritiek had gehad ook "
          "op het instituut zelf. Ja, genomen dat ze echt zeiden van die "
          "komt er echt gewoon nooit meer in.",
          BASE + "Zinsfragment. Spreker: Muusse.")])

    R3 = add_relation(
        ent("de Volkskrant"), ent("RTL Nederland"), "beinvloeding",
        mech("intermedia_agendering"),
        "De programmering van RTL Tonight werd volgens Vlam georiënteerd "
        "op 'het debat in de Volkskrant' via de toenmalige programma-"
        "leiding (Peter van der Vorst): de krant zet zo indirect de "
        "agenda van een concurrerend medium. Illustreert de onevenredige "
        "invloed van een kleine titel die juist door de mediatop wordt "
        "gelezen. Eén duidingsbron — lage certainty.",
        0.40, 0.25)
    add_arg(R3,
        "RTL Tonight werd geprogrammeerd op het referentiekader van de "
        "Volkskrant ('het debat in de grachtengordel'), wat volgens Vlam "
        "mede verklaart waarom het programma zijn brede RTL-publiek niet "
        "bereikte.",
        "Duiding van een media-analist, niet een gedocumenteerd besluit; "
        "het feitelijke substraat (samenstelling duiderspanel, woonplaats "
        "en profiel van de programmaleiding) is wel controleerbaar. "
        "Vandaar gewicht 0.35.",
        0.35,
        [("De volksrand is oneig invloedrijk doordat heel veel "
          "invloedrijke mensen ook weer die krant eh lezen.",
          BASE + "Spreker: Vlam. ASR-fouten: 'volksrand' = Volkskrant; "
          "'oneig' = onwijs."),
         ("Nou, de programmabaas destijds van RTL was Peter van der "
          "Vorst. Die woont in Amsterdam. Die heeft daar een groot "
          "grachpand. die is vooral bezig met het debat in de volksrand.",
          BASE + "Spreker: Vlam. ASR-fouten: 'grachpand' = grachtenpand; "
          "'volksrand' = Volkskrant.")])

    R4 = add_relation(
        E_VI, ent("Tweede Kamer"), "beinvloeding", mech("media_agendering"),
        "Politieke medewerkers en politici volgen wat aan de best "
        "bekeken talkshowtafel wordt gezegd als graadmeter van 'wat "
        "Nederland vindt'; wat Johan Derksen vindt kan een Haagse "
        "discussie van richting doen veranderen (getuigenis Vlam/Muusse).",
        0.45, 0.30)
    add_arg(R4,
        "Den Haag monitort Vandaag Inside: medewerkers scannen elke "
        "ochtend de talkshows van de vorige avond en de uitspraken van "
        "Derksen werken door in de politieke discussie.",
        "Twee samenvallende getuigenissen (Muusse vanuit haar contact "
        "met politici, Vlam als analist), consistent met het algemene "
        "media-agenderingsonderzoek; maar geen gedocumenteerde casus van "
        "een concreet doorwerkingsmoment — vandaar 0.4.",
        0.4,
        [("Kijk, ik weet dat politici wel eh hè medewerkers kijken "
          "gewoon iedere ochtend wat stond er in de klanten? Wat is er "
          "gisteravond bij de talkshows gezegd?",
          BASE + "Spreker: Muusse. ASR-fout: 'klanten' = kranten."),
         ("Ik denk één van de interessante dingen die ik altijd vind is "
          "als eh dat dat mensen in Den Haag echt kijken naar wat Johan "
          "Derks de avond daarvoor heeft eh gezegd.",
          BASE + "Spreker: Vlam. ASR-fout: 'Johan Derks' = Johan "
          "Derksen.")])

    con.commit()
    for t in ("mechanisms", "entities", "relations", "arguments",
              "citations", "sources", "source_locations"):
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: {n}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
