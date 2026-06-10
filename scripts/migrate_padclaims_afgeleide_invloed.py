#!/usr/bin/env python3
"""
Migratie: eindclaims (padclaims) voor afgeleide (indirecte) pijlen.

Modelreview-punt van de gebruiker: dat A→B en B→C elk onderbouwd zijn, bewijst
nog niet dat A indirecte invloed heeft op C — per-schakel-steun is nodig maar
niet voldoende voor de compositie. Een afgeleide stippelpijl A ⇢ C verschijnt
daarom voortaan alléén als de samengestelde claim zelf in de discussieboom
onderbouwd is.

Opslag zonder schemawijziging, via bestaande kolommen van `arguments`:
  role_id        = bronrol van de pijl
  property       = 'indirecte_invloed_op'
  property_value = naam van de doelrol
`scoring.py` sluit deze argumenten uit van de rolscore (het zijn claims over
het pad, niet over de rol); de viz indexeert ze als `pathClaims` en toetst er
elke kandidaat-pijl aan, in theorie- én praktijklaag (praktijk via de rollen
van de entiteiten).

Alleen composities mét vindplaats worden geclaimd; regelnummers verwijzen naar
sources/AI/propagandsmodel2.md. Al het andere (journalist ⇢ *, lobbyist ⇢
publiek, omroepkoepel ⇢ *, lange doorgeefkettingen) krijgt bewust géén claim
en verdwijnt uit de viz.

Extra: entity_role Tweede Kamer -> politicus, zodat de al onderbouwde
praktijkroute Shell ⇢ Tweede Kamer (via VNO-NCW) aan de theorieclaim
belanghebbende ⇢ politicus gekoppeld blijft.

Backup-then-migrate; idempotent op (role_id, property, property_value).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-padclaims-2026-06"
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

    roles = {n: i for i, n in cur.execute("SELECT id, name FROM roles")}
    bw_row = cur.execute("SELECT id FROM sources WHERE title=?", (BW_TITLE,)).fetchone()
    if not bw_row:
        raise SystemExit("FOUT: BW Boek 2-bron ontbreekt (draai eerst "
                         "migrate_kernschakels_onderbouwing.py)")
    BW = bw_row[0]

    def add_claim(src, tgt, claim, reasoning, weight, citations):
        if src not in roles or tgt not in roles:
            raise SystemExit(f"rol ontbreekt: {src} of {tgt}")
        if cur.execute(
            "SELECT 1 FROM arguments WHERE role_id=? AND property='indirecte_invloed_op' "
            "AND property_value=?", (roles[src], tgt)).fetchone():
            print(f"  claim bestaat al: {src} ⇢ {tgt}")
            return
        cur.execute(
            """INSERT INTO arguments (role_id, property, property_value, stance,
               claim, reasoning, weight, status, contributed_by)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (roles[src], "indirecte_invloed_op", tgt, "supporting",
             claim, reasoning, weight, "ongecontroleerd", CONTRIB))
        aid = cur.lastrowid
        for sid, quote, ctx in citations:
            cur.execute("INSERT INTO citations (argument_id, source_id, quote, context) "
                        "VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ padclaim {src} ⇢ {tgt}")

    # ── Eigendomsketen: de eigenaar door de getrapte structuur heen ──

    add_claim("mediaeigenaar", "hoofdredacteur",
        "De eigenaar heeft — klein maar reëel — indirecte invloed op wie "
        "hoofdredacteur wordt: de benoeming loopt via de directie die hij "
        "(via de keten) zelf kiest.",
        "De compositie zelf is gedocumenteerd, niet alleen de losse schakels: "
        "Bergman noemt de invloed van de eigenaar op de benoeming van "
        "hoofdredacteuren 'onmiskenbaar'. De demping in het pad weerspiegelt "
        "dat het om kaderstelling gaat, niet om dagelijkse aansturing.",
        0.65,
        [(3, "de invloed van de eigenaar op de bedrijfscultuur en de benoeming "
             "van hoofdredacteuren is onmiskenbaar",
          "typering via sources/AI/propagandsmodel2.md (regel 25); geen "
          "letterlijk citaat")])

    add_claim("mediaeigenaar", "directie",
        "De eigenaar bepaalt langs de formele keten (STAK → RvC → benoeming) "
        "wie de mediaorganisatie bestuurt — ook waar hij de directie niet "
        "rechtstreeks aanwijst.",
        "De getrapte structuur is juist ontworpen om deze zeggenschap te "
        "verankeren; de afgeleide route maakt het 'hoe' van de al-directe "
        "eigenaarsmacht zichtbaar.",
        0.65,
        [(3, "DPG Media is grotendeels eigendom van de Belgische familie Van "
             "Thillo, met Christian Van Thillo als de centrale figuur",
          "typering via sources/AI/propagandsmodel2.md (regel 23, 25)"),
         (BW, "de benoemingsketen aandeelhouder → raad van commissarissen → "
              "bestuur is wettelijk gecodificeerd",
          "parafrase van het structuurregime, Boek 2 BW")])

    add_claim("mediaeigenaar", "raad_van_commissarissen",
        "Via de STAK-constructie stelt de eigenaarsfamilie feitelijk het "
        "toezichtsorgaan samen: de stemrechten zijn daarvoor bij het "
        "administratiekantoor verankerd.",
        "Certificering bestaat juist om zeggenschap (waaronder het "
        "commissarisbenoemingsrecht) los van het economische belang te "
        "behouden — de compositie is het ontwerpdoel van de constructie.",
        0.60,
        [(BW, "het stemrecht op gecertificeerde aandelen berust bij het "
              "administratiekantoor als aandeelhouder",
          "parafrase, Boek 2 BW"),
         (3, "via hun gecertificeerde holdings",
          "typering via sources/AI/propagandsmodel2.md (regel 22)")])

    add_claim("mediaeigenaar", "overnamevehikel",
        "De eigenaarsfamilie controleert de holding/het overnamevehikel via "
        "haar gecertificeerde belang (Van Thillo via Epifin).",
        "Gedocumenteerde eigendomsstructuur: de familieholding is het "
        "instrument waarmee het mediabezit wordt gehouden en uitgebreid.",
        0.60,
        [(3, "Familie Van Thillo (via Epifin)",
          "typering via sources/AI/propagandsmodel2.md (regel 22, 39)")])

    add_claim("mediaeigenaar", "mediaorganisatie",
        "De eigenaar heeft via de holdingstructuur indirecte invloed op de "
        "mediaorganisatie: strategie, budgetten en acquisities worden op "
        "eigenaarsniveau bepaald.",
        "Bergman documenteert precies deze compositie — niet de losse "
        "schakels maar de eigenaarsmacht over de organisatie als geheel.",
        0.60,
        [(3, "zij bepalen de algemene strategie, keuren budgetten goed en "
             "beslissen over acquisities",
          "typering via sources/AI/propagandsmodel2.md (regel 25)")])

    add_claim("mediaeigenaar", "publiek",
        "Eigendom werkt — sterk gedempt — door tot in het nieuwsbeeld dat het "
        "publiek bereikt: de eigenaar bepaalt de institutionele context "
        "waarbinnen nieuws wordt geproduceerd.",
        "Dit is de kernstelling van het eerste filter zelf; de kleine "
        "padsterkte in de viz weerspiegelt dat het om context gaat, niet om "
        "redactionele regie.",
        0.50,
        [(2, "the size, ownership, and profit orientation of the mass media",
          "het eerste filter, Manufacturing Consent; typering"),
         (3, "het nieuws dat het publiek bereikt wordt grotendeels geproduceerd "
             "en geframed vanuit het perspectief van de gevestigde machten",
          "typering via sources/AI/propagandsmodel2.md (regel 17, 99)")])

    add_claim("aandeelhouder", "directie",
        "Aandeelhouders bepalen getrapt wie bestuurt: zij benoemen de "
        "commissarissen, die op hun beurt het bestuur benoemen.",
        "De compositie is geen interpretatie maar gecodificeerd "
        "vennootschapsrecht (structuurregime).",
        0.70,
        [(BW, "de algemene vergadering benoemt de commissarissen; bij de "
              "structuurvennootschap benoemt de raad van commissarissen de "
              "bestuurders",
          "parafrase van art. 2:142/2:158/2:162 BW")])

    add_claim("administratiekantoor", "directie",
        "De STAK heeft via haar greep op de Raad van Commissarissen getrapte "
        "invloed op de samenstelling van de directie.",
        "Zelfde wettelijke keten als bij de aandeelhouder, maar dan via de "
        "verankerde stemzeggenschap van het administratiekantoor.",
        0.65,
        [(BW, "de benoemingsketen aandeelhouder → raad van commissarissen → "
              "bestuur is wettelijk gecodificeerd",
          "parafrase van het structuurregime, Boek 2 BW")])

    # ── Lobby-driehoek (Luyendijk) ──

    add_claim("belanghebbende", "politicus",
        "De belanghebbende heeft via de lobbyist indirecte invloed op de "
        "politicus: tot en met kant-en-klare Kamervragen wordt het belang "
        "aangeleverd, terwijl de opdrachtgever buiten beeld blijft.",
        "Luyendijks kernbevinding betreft precies deze compositie — de "
        "driehoek, niet alleen de losse contacten.",
        0.65,
        [(4, "parlementsleden leunen zelfs zwaar op door lobbyisten "
             "aangeleverde informatie voor het stellen van Kamervragen",
          "typering via sources/AI/propagandsmodel2.md (regel 72)")])

    add_claim("belanghebbende", "journalist",
        "De belanghebbende bereikt via de lobbyist ook de journalist: het "
        "verhaal wordt geplant onder de mantel van vertrouwelijkheid ('je "
        "hebt het niet van mij, maar...').",
        "De boektitel beschrijft dit tweede kanaal van dezelfde driehoek; de "
        "afzender (de opdrachtgever) blijft voor de lezer onzichtbaar.",
        0.60,
        [(4, "politici, voorlichters, lobbyisten en journalisten in Den Haag "
             "functioneren als één stam",
          "typering via sources/AI/propagandsmodel2.md (regel 71)")])

    add_claim("belanghebbende", "publiek",
        "Belangen werken — gedempt — door tot in wat het publiek te zien "
        "krijgt: het nieuws wordt grotendeels geproduceerd en geframed vanuit "
        "het perspectief van de gevestigde machten.",
        "De keten belang → media → publiek is de centrale stelling van het "
        "propagandamodel als geheel; vandaar een gematigd gewicht en een "
        "kleine padsterkte.",
        0.50,
        [(3, "het nieuws dat het publiek bereikt wordt grotendeels geproduceerd "
             "en geframed vanuit het perspectief van de gevestigde machten",
          "typering via sources/AI/propagandsmodel2.md (regel 99)")])

    # ── Filterroutes naar het publiek ──

    add_claim("adverteerder", "publiek",
        "Adverteerders sturen indirect wat het publiek te zien krijgt: media "
        "bouwen een 'supportive selling environment' en mijden content die "
        "het consumentisme fundamenteel ter discussie stelt.",
        "H&C's tweede filter is zelf een compositieclaim (adverteerder → "
        "redactionele omgeving → publiek); Bergman kwantificeert het "
        "Nederlandse kanaal.",
        0.60,
        [(2, "a supportive selling environment",
          "tweede filter, Manufacturing Consent"),
         (3, "structurele voorkeur voor content die het consumentistische "
             "wereldbeeld bevestigt",
          "typering via sources/AI/propagandsmodel2.md (regel 58, 63)")])

    add_claim("persbureau", "publiek",
        "De centrale rol van het ANP leidt tot een uniform en beperkt "
        "nieuwsbeeld bij het publiek: de keuzes van één bureau worden door "
        "vrijwel het hele medialandschap overgenomen.",
        "De homogenisering van wat het publiek bereikt is het gedocumenteerde "
        "eindresultaat van pakketjournalistiek — de compositie zelf.",
        0.65,
        [(3, "doordat deze keuzes door een groot deel van het medialandschap "
             "worden overgenomen, ontstaat een uniform en beperkt nieuwsbeeld",
          "typering via sources/AI/propagandsmodel2.md (regel 69)")])

    add_claim("gezagsinstituut", "publiek",
        "Officiële bronnen bepalen indirect het beeld dat het publiek krijgt: "
        "bij Irak 2003 domineerde de versie van regeringswoordvoerders en "
        "inlichtingendiensten de berichtgeving.",
        "De casus documenteert de hele keten (bron → media → publiek), niet "
        "alleen de bronafhankelijkheid van redacties.",
        0.60,
        [(3, "de afhankelijkheid van officiële bronnen zorgde ervoor dat hun "
             "versie van het verhaal domineerde",
          "typering via sources/AI/propagandsmodel2.md (regel 155)")])

    add_claim("denktank", "publiek",
        "Door elites gefinancierde denktanks framen via de media het beeld "
        "dat het publiek krijgt; bij defensie- en geopolitieke onderwerpen "
        "domineren hun experts de duiding.",
        "De compositie (denktank → media → publiek) is gedocumenteerd als "
        "onderdeel van het derde filter; afwijkende experts zijn 'nagenoeg "
        "onzichtbaar'.",
        0.55,
        [(3, "afwijkende, kritische experts zijn nagenoeg onzichtbaar in de "
             "mainstream media",
          "typering via sources/AI/propagandsmodel2.md (regel 99, 130)")])

    # Bewust GEEN claim voorlichter ⇢ publiek: de claim-consistente route
    # (voorlichter → media → publiek) heeft geen onderbouwde schakelketen, en
    # de enige route die wél door de poort komt (via draaideur → politicus →
    # omroepbestel) vertelt een ander verhaal dan de claim. Een eindclaim
    # zonder route die hem waarmaakt hoort niet in de viz.

    # ── Omroepbestel ──

    add_claim("politicus", "ledenomroep",
        "De politiek heeft getrapte invloed op de ledenomroepen: zij benoemt "
        "de NPO-top en de NPO verdeelt budget en zendtijd over de omroepen — "
        "een wettelijk gecodificeerde sturingsketen.",
        "Net als bij het vennootschapsrecht is de compositie hier het ontwerp "
        "van de wet zelf (benoeming + bestelsturing), geen optelsom van "
        "toevallige schakels.",
        0.60,
        [(10, "benoeming van de NPO-organen via de minister en verdeling van "
              "budget en zendtijd door de NPO",
          "parafrase van de benoemings- en sturingsbepalingen, Mediawet 2008 "
          "hoofdstuk 2")])

    # ── Praktijkkoppeling: Tweede Kamer als instantie van de rol politicus ──
    tk = cur.execute("SELECT id FROM entities WHERE name='Tweede Kamer'").fetchone()
    if tk and "politicus" in roles:
        cur.execute(
            "INSERT OR IGNORE INTO entity_roles (entity_id, role_id) VALUES (?,?)",
            (tk[0], roles["politicus"]))
        print("+ entity_role Tweede Kamer -> politicus"
              if cur.rowcount else "  entity_role Tweede Kamer -> politicus bestond al")

    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM arguments WHERE property='indirecte_invloed_op'").fetchone()[0]
    t = cur.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    con.close()
    print(f"Klaar: {n} padclaims, {t} argumenten totaal.")


if __name__ == "__main__":
    main()
