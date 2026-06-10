#!/usr/bin/env python3
"""
Migratie: onderbouwing van het elite_forum-cluster met de publiek
gedocumenteerde 'Build Back Better'-casus (2020).

Aanleiding: alle acht elite_forum-mechanismen hadden nul argumenten in de
discussieboom — besloten fora zijn per definitie moeilijk verifieerbaar. De
BBB-casus is de zeldzame publiek waarneembare output van frame-circulatie en
is per stap te documenteren:

  VN/Sendai-raamwerk (2015, prioriteit 4: "Build Back Better" als vakterm in
  rampenherstel) → OESO-policy brief (5 juni 2020) en WEF Great Reset-
  lancering (3 juni 2020, met 'build back better' letterlijk in de
  aankondiging) → centrale herstelslogan van meerdere westerse
  regeringsleiders (Biden — die zijn plan ernaar noemde —, Johnson, Trudeau;
  BBC-reconstructie 24 juni 2021).

Toegevoegd:
  1. Zes bronnen (Sendai/UNDRR, OESO, WEF-essay Schwab, Rijksoverheid-
     mediatekst 9 april 2020, BBC, El-Erian/Per Jacobsson-lezing 2010).
  2. Eén supporting argument bij `ideologische_synchronisatie` (het
     BBB-traject als publiek spoor van vocabulaire-convergentie via gedeelde
     rapporten, toppen en fora — uitdrukkelijk: circulatie en adoptie, geen
     bewijs van centrale regie).
  3. Eén contextual argument bij hetzelfde mechanisme dat 'het nieuwe
     normaal' (Rutte, 9 april 2020) afbakent: die term stamt uit het
     financieel-economische discours na 2008 (El-Erian/PIMCO) en was in
     omloop vóór de Great Reset-lancering — een forum-route is daarvoor niet
     aantoonbaar en wordt niet geclaimd.
  4. Frame-notitie WEF-entiteit uitgebreid met 'Build Back Better'
     (letterlijk in de lanceringsaankondiging van de Great Reset).

Bewust NIET toegevoegd:
  - Geen nieuw mechanisme of hyperedge: "alle leiders gebruiken hetzelfde
    woord" is de waarneembare output van de al gemodelleerde synchronisatie,
    geen apart systeemeffect.
  - Geen argument bij de halo `elite_referentiekader`: de casus documenteert
    politieke adoptie van vocabulaire, niet de nieuwsverslaggeving zelf;
    daarvoor zou een media-inhoudsanalyse als bron nodig zijn.
  - Geen OESO/VN/IMF-entiteiten: zonder gedocumenteerde koppeling aan de
    Nederlandse nieuwsketen zouden die zweven (scope: Nederlandse media).
  - Geen padclaim elite_forum ⇢ publiek: de literatuur benoemt die
    compositie niet (vuistregel).
  - Geen claim dat Rutte 'build back better' gebruikte: dat circuleert wel
    (o.a. openDemocracy) maar is niet onafhankelijk geverifieerd.

Backup-then-migrate; idempotent op sources.title, op (mechanism_id, claim)
voor argumenten en op een LIKE-guard voor de frame-notitie.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-elite-forum-onderbouwing-2026-06"
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

    # ---- BRONNEN ------------------------------------------------------------
    def add_source(title, stype, author, publisher, date, reliability, url=None):
        row = cur.execute("SELECT id FROM sources WHERE title=?", (title,)).fetchone()
        if row:
            sid = row[0]
            print(f"bron bestaat al, id={sid}: {title[:60]}")
        else:
            cur.execute(
                """INSERT INTO sources
                   (title, author, source_type, publisher, date_published, reliability)
                   VALUES (?,?,?,?,?,?)""",
                (title, author, stype, publisher, date, reliability),
            )
            sid = cur.lastrowid
            print(f"+ bron id={sid}: {title[:60]}")
        if url and not cur.execute(
            "SELECT 1 FROM source_locations WHERE source_id=? AND location=?",
            (sid, url),
        ).fetchone():
            cur.execute(
                "INSERT INTO source_locations (source_id, location_type, location, accessed_at) "
                "VALUES (?,?,?,?)", (sid, "url", url, ACCESSED),
            )
        return sid

    src_sendai = add_source(
        "Sendai Framework for Disaster Risk Reduction 2015-2030",
        "rapport", "Verenigde Naties (UNDRR)", "United Nations",
        "2015-03-18", "institutioneel",
        "https://www.undrr.org/publication/sendai-framework-disaster-risk-reduction-2015-2030",
    )
    src_oeso = add_source(
        "Building back better: A sustainable, resilient recovery after COVID-19",
        "rapport", "OECD", "OECD Policy Responses to Coronavirus (COVID-19)",
        "2020-06-05", "institutioneel",
        "https://www.oecd.org/en/publications/2020/06/building-back-better-a-sustainable-resilient-recovery-after-covid-19_b386e72d.html",
    )
    src_wef = add_source(
        "Now is the time for a 'great reset'",
        "website", "Schwab, K.", "World Economic Forum",
        "2020-06-03", "primair",
        "https://www.weforum.org/stories/2020/06/now-is-the-time-for-a-great-reset/",
    )
    src_rijk = add_source(
        "Letterlijke tekst persconferentie na ministerraad 9 april 2020",
        "transcript", "Rutte, M. & De Jonge, H.", "Rijksoverheid",
        "2020-04-09", "primair",
        "https://www.rijksoverheid.nl/documenten/mediateksten/2020/04/09/"
        "letterlijke-tekst-persconferentie-na-ministerraad-9-april-2020",
    )
    src_bbc = add_source(
        "What is the Great Reset - and how did it get hijacked by conspiracy theories?",
        "nieuwsartikel", "BBC News", "BBC",
        "2021-06-24", "kwaliteitsjournalistiek",
        "https://www.bbc.com/news/blogs-trending-57532368",
    )
    src_elerian = add_source(
        "Navigating the New Normal in Industrial Countries",
        "overig", "El-Erian, M.A.", "Per Jacobsson Foundation",
        "2010-10-10", "institutioneel",
        "https://www.perjacobsson.org/lectures/101010.pdf",
    )

    # ---- ARGUMENTEN ----------------------------------------------------------
    def mech_id(name):
        r = cur.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
        if not r:
            raise SystemExit(f"mechanisme ontbreekt: {name}")
        return r[0]

    def add_arg(mechanism_id, stance, claim, reasoning, weight, citations):
        if cur.execute("SELECT 1 FROM arguments WHERE mechanism_id=? AND claim=?",
                       (mechanism_id, claim)).fetchone():
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
            cur.execute("INSERT INTO citations (argument_id, source_id, quote, context) "
                        "VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument ({stance}) bij mechanisme {mechanism_id}")

    m_sync = mech_id("ideologische_synchronisatie")

    add_arg(m_sync, "supporting",
        "Frame-synchronisatie in transnationale beleidscircuits is in 2020 "
        "publiek waarneembaar geweest: de VN-herstelterm 'build back better' "
        "(Sendai-raamwerk 2015, prioriteit 4) werd na de WEF Great "
        "Reset-lancering (3 juni 2020) en de OESO-policy brief (5 juni 2020) "
        "binnen maanden de centrale herstelslogan van meerdere westerse "
        "regeringsleiders (Biden, Johnson, Trudeau).",
        "Het traject is per stap gedocumenteerd: vakterm in VN-rampenherstel "
        "(2015) → herstelvocabulaire in WEF/OESO-publicaties (begin juni "
        "2020) → regeringsslogans (Biden noemde zijn herstelplan ernaar). "
        "Dit documenteert convergentie van vocabulaire via gedeelde "
        "rapporten, toppen en fora — circulatie en adoptie, géén bewijs van "
        "centrale regie; de BBC-reconstructie beschrijft juist hoe het "
        "ontbreken van concrete besluitvorming achter de slogan ruimte gaf "
        "aan complotinterpretaties. Het is daarmee een zeldzaam publiek "
        "spoor van het synchronisatieproces dat dit mechanisme beschrijft, "
        "consistent met de emergente lezing van het model; over wat besloten "
        "bijeenkomsten zelf uitwisselen zegt de casus niets.",
        0.5,
        [(src_sendai,
          "Priority 4: Enhancing disaster preparedness for effective "
          "response and to “Build Back Better” in recovery, "
          "rehabilitation and reconstruction.",
          "letterlijke prioriteitstitel (Engels) uit het Sendai-raamwerk, "
          "aangenomen door de VN op 18 maart 2015"),
         (src_wef,
          "Het Great Reset-initiatief werd op 3 juni 2020 gelanceerd "
          "(essay van Schwab plus aankondiging met de prins van Wales); de "
          "begeleidende aankondiging omschreef het doel als zorgen dat "
          "bedrijven en gemeenschappen 'build back better'.",
          "typering van de lancering; 'build back better' staat letterlijk "
          "in de aankondigingstweet van Clarence House (3 juni 2020), niet "
          "in het essay zelf"),
         (src_oeso,
          "Economic recovery packages should be designed to 'build back "
          "better' — meer doen dan economieën snel weer op de been helpen.",
          "vrijwel letterlijke kernzin uit de samenvatting van de "
          "OESO-policy brief (5 juni 2020), tweede zinsdeel vertaald"),
         (src_bbc,
          "Regeringsleiders onder wie Biden (VS), Johnson (VK) en Trudeau "
          "(Canada) namen 'build back better' als herstelslogan over; het "
          "ontbreken van concrete invulling achter de Great Reset bood "
          "vruchtbare grond voor complottheorieën.",
          "typering van de BBC-reconstructie (24 juni 2021); geen "
          "letterlijk citaat")],
    )

    add_arg(m_sync, "contextual",
        "Het Nederlandse 'het nieuwe normaal' (Rutte, persconferenties "
        "april 2020) is internationaal circulerend crisisvocabulaire met "
        "een andere route dan 'build back better': de term stamt uit het "
        "financieel-economische discours na de kredietcrisis van 2008 en "
        "was al breed in omloop vóór de lancering van de Great Reset.",
        "Rutte gebruikte 'het nieuwe normaal' op 9 april 2020 — twee "
        "maanden vóór de WEF- en OESO-publicaties van juni; een route via "
        "elite-fora is voor deze term dus niet aantoonbaar en wordt hier "
        "niet geclaimd. Dit argument bakent af wat de casus wél laat zien "
        "(gedeeld transnationaal beleids- en mediavocabulaire) en wat níét "
        "(forum-specifieke sturing), zodat de twee termen — met "
        "verschillende oorsprong en tijdlijn — niet op één hoop belanden.",
        0.4,
        [(src_rijk,
          "in het nieuwe normaal (...) in die anderhalvemetersamenleving",
          "letterlijk (ingekort) citaat van Rutte uit de mediatekst van de "
          "persconferentie na de ministerraad van 9 april 2020"),
         (src_elerian,
          "'The new normal' werd na de kredietcrisis van 2008 door PIMCO "
          "(El-Erian) gemunt voor een economie die niet terugkeert naar "
          "het oude groeipad.",
          "typering van de Per Jacobsson-lezing (10 oktober 2010); geen "
          "letterlijk citaat")],
    )

    # ---- FRAME-NOTITIE WEF -----------------------------------------------------
    OLD = "Frame: stakeholder capitalism / ESG / Great Reset."
    NEW = "Frame: stakeholder capitalism / ESG / Great Reset / Build Back Better."
    n = cur.execute(
        "UPDATE entities SET description = REPLACE(description, ?, ?) "
        "WHERE name='World Economic Forum' AND description LIKE '%' || ? || '%' "
        "AND description NOT LIKE '%Build Back Better%'",
        (OLD, NEW, OLD)).rowcount
    print(f"frame-notitie WEF bijgewerkt: {n} rij(en)")

    con.commit()

    # ---- SAMENVATTING ----------------------------------------------------------
    print("---")
    for label, q in (
        ("sources", "SELECT COUNT(*) FROM sources"),
        ("locations", "SELECT COUNT(*) FROM source_locations"),
        ("arguments", "SELECT COUNT(*) FROM arguments"),
        ("citations", "SELECT COUNT(*) FROM citations"),
    ):
        print(f"{label:12s}: {cur.execute(q).fetchone()[0]}")
    for stance, claim in cur.execute(
        "SELECT a.stance, substr(a.claim,1,70) FROM arguments a "
        "JOIN mechanisms m ON m.id=a.mechanism_id "
        "WHERE m.name='ideologische_synchronisatie' ORDER BY a.id"):
        print(f"  ideologische_synchronisatie [{stance}]: {claim}…")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
