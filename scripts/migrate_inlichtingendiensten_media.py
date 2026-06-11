#!/usr/bin/env python3
"""
Migratie: inlichtingendiensten en de media (juni 2026).

Aanleiding: de claim "de helft van de journalisten is door geheime diensten
benaderd". Geverifieerd: het cijfer komt uit NRC-onderzoek van 15 oktober
2022 — de helft van 32 NRC-redacteuren/-correspondenten die werken op
terreinen waar de diensten belangstelling voor hebben, dus een kleine,
niet-representatieve groep; géén uitspraak over journalisten in het
algemeen. De bestaande onderbouwing van inlichtingen_cooptatie (arg 350,
bron 15) dateerde dat onderzoek verkeerd (als "NRC/Volkskrant, 2024") —
de URL was al het NOS-stuk over het NRC-onderzoek van 2022.

Wat deze migratie doet:

1. REPARATIE bron 15 + argument 350 + citatie:
   - bron 15: titel/auteur/datum naar het werkelijke NOS-artikel
     (15-10-2022, over het NRC-onderzoek);
   - argument 350: claim herdateerd (2022) en steekproef-kanttekening
     expliciet in de reasoning;
   - citatie 353: elliptische parafrase vervangen door letterlijke,
     geverifieerde zinnen.

2. VERSTERKING inlichtingen_cooptatie (mech 133) met twee argumenten:
   - CTIVD-toezichtsrapporten 77 en 78 (28-06-2024): officiële
     bevestiging dat MIVD en AIVD in 2019-2023 journalisten als agent
     inzetten; geen aanwijzing voor dwang; wettelijk toegestaan
     (art. 41 Wiv 2017); op onderdelen onvoldoende aandacht voor de
     bijzondere positie van de journalist. Gewicht 0.8 (toezichtsorgaan).
   - Casus Bas van Hout (BVD 1997-2002; geheim CTIVD-rapport 2014:
     'levensbedreigende situatie' mede door de dienst; ±865.000 euro
     schadevergoeding). Gewicht 0.6 (één casus).

3. NIEUW MECHANISME statelijke_bronnenjacht (flak + extra sourcing,
   juridisch, direct, gezagsinstituut -> journalist): inzet van
   bijzondere bevoegdheden tegen journalisten om bronnen/lekken te
   achterhalen; chilling effect op bronbescherming. Onderbouwd met
   EHRM Telegraaf Media Nederland t. Nederland (22-11-2012, nr.
   39315/06): schending art. 8 en 10 EVRM; citaten letterlijk
   geverifieerd in het persbericht van de griffie (ECHR 430 (2012)).
   NB: ander mechanisme dan inlichtingen_cooptatie — daar wordt de
   journalist instrument van de dienst, hier doelwit.

4. PRAKTIJKLAAG: nieuwe entiteit AIVD (gezagsinstituut) met twee
   relaties: AIVD -flak-> De Telegraaf (taps/observatie 2006, EHRM
   2012; certainty 0.95 — rechterlijk vastgesteld) en AIVD -cooptatie->
   NRC (benadering van redacteuren/correspondenten; certainty 0.85 —
   eigen verslag van de redactie). MIVD bewust niet als entiteit
   opgenomen: geen geverifieerde relatie met een specifieke,
   benoemde media-entiteit.

Bewust NIET opgenomen: de veralgemenisering "de helft van alle
journalisten"; Udo Ulfkotte (methodologisch onbetrouwbaar); Church
Committee/VS-historie (mechanisme heeft al sterkere NL-onderbouwing).

Backup-then-migrate; idempotent; tweemaal draaien verandert niets.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-inlichtingendiensten-2026-06"
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

    # ---- 1. REPARATIE bron 15 / argument 350 / citatie 353 -------------------
    OLD_TITLE_15 = "AIVD en MIVD rekruteerden journalisten als agent"
    row = cur.execute("SELECT title FROM sources WHERE id=15").fetchone()
    if row and row[0] == OLD_TITLE_15:
        cur.execute(
            "UPDATE sources SET title=?, author=?, date_published=?, "
            "summary=? WHERE id=15",
            ("Inlichtingendiensten AIVD en MIVD ronselen journalisten",
             "NOS, naar onderzoek van NRC",
             "2022-10-15",
             "NOS-bericht over het NRC-onderzoek van 15 oktober 2022: NRC "
             "sprak 32 eigen redacteuren en correspondenten op terreinen "
             "waar de diensten belangstelling voor hebben; de helft zegt "
             "ooit benaderd te zijn door AIVD of MIVD. Aanleiding was een "
             "in 2016 naar PubLeaks gelekt intern AIVD-document met 21 "
             "bronnen en agenten, onder wie acht journalisten."))
        print("~ bron 15 gecorrigeerd: NOS 15-10-2022 (was 'NRC/Volkskrant "
              "2024')")
    else:
        print("bron 15 al gecorrigeerd")

    OLD_CLAIM_350 = ("NRC/Volkskrant (2024): van 32 benaderde redacteuren/"
                     "correspondenten meldde ~de helft een verzoek; intern "
                     "AIVD-document noemde 8 journalisten onder 21 'bronnen "
                     "en agenten'.")
    row = cur.execute("SELECT claim FROM arguments WHERE id=350").fetchone()
    if row and row[0] == OLD_CLAIM_350:
        cur.execute(
            "UPDATE arguments SET claim=?, reasoning=? WHERE id=350",
            ("NRC (2022): van 32 NRC-redacteuren en -correspondenten op "
             "terreinen waar de inlichtingendiensten belangstelling voor "
             "hebben, zegt de helft ooit benaderd te zijn door AIVD of "
             "MIVD; een gelekt intern AIVD-document noemde onder 21 "
             "'bronnen en agenten' acht journalisten.",
             "Sterke onderbouwing dat benadering een staande praktijk is. "
             "Reikwijdte-kanttekening: het gaat om een kleine, "
             "niet-representatieve groep journalisten die juist op voor "
             "de diensten interessante terreinen werkt (Rusland, "
             "Midden-Oosten); het cijfer rechtvaardigt dus niet de "
             "bredere claim 'de helft van de journalisten is benaderd'."))
        print("~ argument 350 gecorrigeerd: herdateerd naar 2022 + "
              "steekproef-kanttekening")
    else:
        print("argument 350 al gecorrigeerd")

    OLD_QUOTE_353 = "ronselen journalisten ... 32 ... ongeveer de helft"
    row = cur.execute(
        "SELECT quote FROM citations WHERE id=353 AND argument_id=350 "
        "AND source_id=15").fetchone()
    if row and row[0] == OLD_QUOTE_353:
        cur.execute(
            "UPDATE citations SET quote=?, context=? WHERE id=353",
            ("De krant sprak met 32 redacteuren en correspondenten die "
             "zich bezighouden met onderwerpen over of werken in gebieden "
             "waar de inlichtingendiensten aandacht voor hebben. De helft "
             "van de journalisten zegt benaderd te zijn door een van de "
             "twee diensten. (...) In dat document staan de namen van 21 "
             "\"bronnen en agenten\", onder wie acht journalisten.",
             "Letterlijk geverifieerd in het NOS-artikel van 15-10-2022, "
             "geraadpleegd 2026-06-11; verving een elliptische parafrase."))
        print("~ citatie 353: parafrase vervangen door letterlijke citaten")
    else:
        print("citatie 353 al gecorrigeerd")

    # ---- 2. BRONNEN -----------------------------------------------------------
    def add_source(title, stype, author, publisher, date, reliability,
                   url=None, summary=None, language="nl"):
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
        if url:
            cur.execute(
                """INSERT INTO source_locations (source_id, location_type,
                   location, accessed_at) VALUES (?,?,?,?)""",
                (sid, "url", url, ACCESSED))
        print(f"+ bron {sid}: {title[:55]}")
        return sid

    S_CTIVD = add_source(
        "Toezichtsrapporten 77 en 78 over de inzet van journalisten als "
        "agent door de MIVD en de AIVD",
        "rapport", "CTIVD",
        "Commissie van Toezicht op de Inlichtingen- en Veiligheidsdiensten",
        "2024-06-28", "institutioneel",
        url="https://www.ctivd.nl/actueel/nieuws/2024/06/28/index",
        summary="Officieel toezichtsonderzoek naar alle operaties waarin "
                "MIVD en AIVD tussen 1-1-2019 en 1-1-2023 journalisten als "
                "agent inzetten. Conclusies: wettelijk toegestaan, geen "
                "aanwijzing voor dwang, zorgvuldigheidsinspanningen "
                "aanwezig, maar op onderdelen onvoldoende aandacht voor de "
                "bijzondere positie van de journalist; aanbevelingen door "
                "beide ministers overgenomen.")
    S_VANHOUT = add_source(
        "'Fouten AIVD brachten misdaadjournalist én bron Bas van Hout in "
        "levensgevaar'",
        "nieuwsartikel", "NOS, naar onderzoek van de Volkskrant", "NOS",
        "2019-06-08", "kwaliteitsjournalistiek",
        url="https://nos.nl/l/2288117",
        summary="Misdaadjournalist Bas van Hout (Panorama, De Telegraaf, "
                "Nieuwe Revu) sprak 1997-2002 met de BVD. De CTIVD "
                "concludeerde in een geheim rapport (2014) dat hij mede "
                "door het handelen van de dienst sinds 2001 in een "
                "'levensbedreigende situatie' zit; de staat betaalde circa "
                "865.000 euro schadevergoeding plus immateriële "
                "schadevergoeding.")
    S_EHRM = add_source(
        "Telegraaf Media Nederland Landelijke Media B.V. and Others v. "
        "the Netherlands (nr. 39315/06) — persbericht ECHR 430 (2012)",
        "rapport", "Europees Hof voor de Rechten van de Mens (griffie)",
        "Raad van Europa", "2012-11-22", "primair",
        url="https://hudoc.echr.coe.int/app/conversion/pdf/?library=ECHR"
            "&id=003-4167297-4926068&filename=Chamber+Judgment+Telegraaf+"
            "Media+Nederland+Landelijke+Media+B.V.+and+Others+v.+the+"
            "Netherlands+22.11.2012.pdf",
        summary="Kamerarrest: unaniem schending van art. 8 en 10 EVRM "
                "wegens de inzet van bijzondere bevoegdheden door de AIVD "
                "tegen Telegraaf-journalisten De Haas en Mos om hun "
                "journalistieke bron te achterhalen (taps en observatie, "
                "2006); de wet bood geen passende waarborgen "
                "(onafhankelijke toetsing vooraf ontbrak).",
        language="en")

    # ---- 3. NIEUW MECHANISME ---------------------------------------------------
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

    M_BRONNENJACHT = add_mechanism(
        "statelijke_bronnenjacht", "flak", "juridisch", "direct",
        "gezagsinstituut", "journalist",
        "Een staatsdienst (inlichtingendienst, politie of OM) zet "
        "bijzondere bevoegdheden — taps, observatie, vorderingen, "
        "doorzoekingen — in tegen journalisten om hun bronnen of een lek "
        "te achterhalen. Het doel is doorgaans niet de berichtgeving zelf "
        "maar de geheimhouding van de staat; het effect raakt de "
        "berichtgeving wél: bronnen drogen op zodra vertrouwelijkheid "
        "niet gegarandeerd kan worden (chilling effect). Door het EHRM "
        "getoetst in Telegraaf t. Nederland (2012): zonder onafhankelijke "
        "toetsing vooraf schendt zulke inzet art. 8 en 10 EVRM. Spiegel "
        "van inlichtingen_cooptatie: daar wordt de journalist instrument "
        "van de dienst, hier doelwit.",
        "Verzwakking van bronbescherming en daarmee van "
        "onderzoeksjournalistiek naar de staat: potentiële klokkenluiders "
        "en bronnen wegen het identificatierisico mee, waardoor minder "
        "vertrouwelijke informatie de redactie bereikt.",
        extra_filters=("sourcing",))

    # ---- 4. THEORIE-ARGUMENTEN -------------------------------------------------
    M_COOPTATIE = cur.execute(
        "SELECT id FROM mechanisms WHERE name='inlichtingen_cooptatie'"
    ).fetchone()[0]

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

    CTX_CTIVD = ("Nieuwsbericht CTIVD bij toezichtsrapporten 77 (MIVD) en "
                 "78 (AIVD), 28-06-2024; letterlijk geverifieerd op "
                 "ctivd.nl, geraadpleegd 2026-06-11.")
    add_arg("mechanism_id", M_COOPTATIE, "supporting",
        "CTIVD-toezichtsrapporten 77 en 78 (2024) bevestigen dat MIVD en "
        "AIVD in 2019-2023 journalisten als agent hebben ingezet: "
        "wettelijk toegestaan, zonder aanwijzing voor dwang, maar met op "
        "onderdelen onvoldoende aandacht voor de bijzondere positie van "
        "de journalist.",
        "Institutionele bevestiging door het officiële toezichtsorgaan "
        "zelf — het sterkst denkbare brontype voor het bestaan van de "
        "praktijk. De nuance telt mee: de CTIVD vond geen dwang en zag "
        "zorgvuldigheidsinspanningen; het mechanisme werkt dus via "
        "vrijwillige, soms betaalde vervlechting, niet via pressie. Dat "
        "de inzet wettelijk is toegestaan (art. 41 Wiv 2017) maakt haar "
        "structureel: staand beleid, geen incident.",
        0.8,
        [(S_CTIVD,
          "De CTIVD heeft alle operaties onderzocht waarbij de MIVD en de "
          "AIVD een journalist heeft ingezet als agent in de periode van "
          "1 januari 2019 tot 1 januari 2023.",
          CTX_CTIVD),
         (S_CTIVD,
          "De CTIVD heeft geen aanleiding om te veronderstellen dat de "
          "journalisten onder druk zijn gezet om te werken als agenten.",
          CTX_CTIVD),
         (S_CTIVD,
          "Wel is op onderdelen nog onvoldoende aandacht voor de "
          "bijzondere positie die een journalist inneemt in de "
          "maatschappij en de extra (veiligheids)risico's die de rol van "
          "agent en samenwerking met de diensten met zich mee kunnen "
          "brengen.",
          CTX_CTIVD)])

    add_arg("mechanism_id", M_COOPTATIE, "supporting",
        "Casus Bas van Hout: misdaadjournalist deelde 1997-2002 "
        "informatie met de BVD; de CTIVD concludeerde in een geheim "
        "rapport (2014) dat hij mede door het handelen van de dienst in "
        "een 'levensbedreigende situatie' kwam; de staat betaalde circa "
        "865.000 euro schadevergoeding.",
        "Gedocumenteerde individuele casus die de vervlechting concreet "
        "maakt, inclusief de reële risico's voor de journalist. Het "
        "CTIVD-oordeel en de schadevergoeding zijn institutionele "
        "bevestiging achteraf. Eén casus, dus beperkt gewicht voor de "
        "algemene werking van het mechanisme.",
        0.6,
        [(S_VANHOUT,
          "Van Hout, die werkte voor onder andere Panorama, De Telegraaf "
          "en Nieuwe Revu, sprak tussen 1997 en 2002 met de Binnenlandse "
          "Veiligheidsdienst, de BVD.",
          "Letterlijk geverifieerd in het NOS-artikel van 08-06-2019 "
          "(naar Volkskrant-onderzoek), geraadpleegd 2026-06-11."),
         (S_VANHOUT,
          "in 2014 in een geheim rapport tot de conclusie dat Van Hout "
          "mede door het handelen van de geheime dienst al sinds 2001 in "
          "een 'levensbedreigende situatie' zit",
          "Zinsfragment; het onderwerp (de toezichthouder CTIVD) staat "
          "eerder in de zin. Geverifieerd 2026-06-11."),
         (S_VANHOUT,
          "De rijksoverheid heeft Van Hout volgens de krant 865.000 euro "
          "betaald, daarbovenop komt nog een immateriële schadevergoeding.",
          "Letterlijk geverifieerd, geraadpleegd 2026-06-11.")])

    CTX_EHRM = ("Persbericht van de griffie, ECHR 430 (2012), 22-11-2012; "
                "letterlijk geverifieerd in de pdf via HUDOC, geraadpleegd "
                "2026-06-11.")
    add_arg("mechanism_id", M_BRONNENJACHT, "supporting",
        "EHRM, Telegraaf Media Nederland t. Nederland (2012): de inzet "
        "van bijzondere bevoegdheden door de AIVD tegen twee "
        "Telegraaf-journalisten om hun bron te achterhalen schond art. 8 "
        "en 10 EVRM; de Nederlandse wet bood daarvoor geen passende "
        "waarborgen.",
        "Rechterlijk vastgesteld op het hoogste Europese niveau — "
        "maximale zekerheid dat de praktijk heeft bestaan. Het Hof "
        "benoemt expliciet het chilling effect op bronbescherming: "
        "precies het kanaal waarlangs dit mechanisme de berichtgeving "
        "raakt. De zaak toont tegelijk werkende tegenmacht: het arrest "
        "droeg bij aan onafhankelijke toetsing vooraf (onder de Wiv 2017 "
        "belegd bij de TIB), wat de praktijk inperkt maar niet uitsluit.",
        0.75,
        [(S_EHRM,
          "unanimously, that there had been a violation of Articles 8 "
          "(right to respect for private and family life) and 10 (freedom "
          "of expression and information) of the European Convention on "
          "Human Rights, as regards the use by the secret services of "
          "special powers against two journalists, Mr De Haas and Mr Mos",
          CTX_EHRM),
         (S_EHRM,
          "The Court found that the relevant law in the Netherlands had "
          "not provided appropriate safeguards in respect of the powers "
          "of surveillance used against the applicants, Mr De Haas and "
          "Mr Mos, who are both journalists, with a view to discovering "
          "their journalistic sources.",
          CTX_EHRM),
         (S_EHRM,
          "the potentially chilling effect an order of source disclosure "
          "could have on the exercise of that freedom",
          CTX_EHRM)])

    # ---- 5. PRAKTIJKLAAG -------------------------------------------------------
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

    E_AIVD = add_entity(
        "AIVD (Algemene Inlichtingen- en Veiligheidsdienst)",
        "overheidsinstelling", "gezagsinstituut",
        "Binnenlandse inlichtingen- en veiligheidsdienst, opvolger van de "
        "BVD (2002). Raakt het mediaveld langs twee gedocumenteerde "
        "wegen: benadering en werving van journalisten als agent "
        "(wettelijk toegestaan; CTIVD-toezichtsrapporten 77/78, 2024) en "
        "inzet van bijzondere bevoegdheden tegen journalisten om bronnen "
        "te achterhalen (EHRM Telegraaf t. Nederland, 2012: schending "
        "art. 8 en 10 EVRM).",
        active_from="2002")

    E_TELEGRAAF = cur.execute(
        "SELECT id FROM entities WHERE name='De Telegraaf'").fetchone()[0]
    E_NRC = cur.execute(
        "SELECT id FROM entities WHERE name='NRC'").fetchone()[0]

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

    R_AIVD_TEL = add_relation(
        E_AIVD, E_TELEGRAAF, "flak", M_BRONNENJACHT,
        "In 2006 zette de AIVD taps en observatie in tegen "
        "Telegraaf-journalisten De Haas en Mos om te achterhalen wie hun "
        "gelekte AIVD-documenten had verstrekt. Het EHRM oordeelde in "
        "2012 dat dit art. 8 en 10 EVRM schond: de wet bood geen "
        "passende waarborgen (geen onafhankelijke toetsing vooraf).",
        0.95, 0.3)
    R_AIVD_NRC = add_relation(
        E_AIVD, E_NRC, "cooptatie", M_COOPTATIE,
        "Volgens NRC-onderzoek (2022) is ongeveer de helft van 32 "
        "NRC-redacteuren en -correspondenten op voor de diensten "
        "interessante terreinen weleens benaderd door AIVD of MIVD, soms "
        "met aanbod van betaling. Benadering is niet hetzelfde als "
        "werving; over daadwerkelijke werving bij NRC is niets "
        "vastgesteld.",
        0.85, 0.25)

    add_arg("relation_id", R_AIVD_TEL, "supporting",
        "Het EHRM stelde de inzet van bijzondere bevoegdheden tegen De "
        "Haas en Mos vast en oordeelde unaniem dat die art. 8 en 10 EVRM "
        "schond.",
        "Rechterlijk vastgestelde feiten op het hoogste Europese niveau; "
        "de certainty van deze relatie is daarom vrijwel maximaal. De "
        "influence blijft beperkt: het ging om bronnenjacht na "
        "publicatie, niet om aangetoonde sturing van de inhoud.",
        0.8,
        [(S_EHRM,
          "unanimously, that there had been a violation of Articles 8 "
          "(right to respect for private and family life) and 10 (freedom "
          "of expression and information) of the European Convention on "
          "Human Rights, as regards the use by the secret services of "
          "special powers against two journalists, Mr De Haas and Mr Mos",
          CTX_EHRM)])
    add_arg("relation_id", R_AIVD_NRC, "supporting",
        "De helft van 32 NRC-redacteuren en -correspondenten op voor de "
        "diensten interessante terreinen meldt benadering door AIVD of "
        "MIVD.",
        "Eigen verslag van de redactie over haar journalisten, door NRC "
        "zelf gepubliceerd. Kleine, niet-representatieve groep op juist "
        "die terreinen waar benadering te verwachten valt; het cijfer "
        "draagt de relatie AIVD->NRC, niet een uitspraak over de "
        "journalistiek als geheel.",
        0.7,
        [(15,
          "De krant sprak met 32 redacteuren en correspondenten die zich "
          "bezighouden met onderwerpen over of werken in gebieden waar de "
          "inlichtingendiensten aandacht voor hebben. De helft van de "
          "journalisten zegt benaderd te zijn door een van de twee "
          "diensten.",
          "Letterlijk geverifieerd in het NOS-artikel van 15-10-2022, "
          "geraadpleegd 2026-06-11.")])

    con.commit()

    # ---- eindstand -------------------------------------------------------------
    for t in ("mechanisms", "entities", "relations", "arguments",
              "citations", "sources", "source_locations"):
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
