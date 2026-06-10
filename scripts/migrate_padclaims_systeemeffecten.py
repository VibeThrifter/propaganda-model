#!/usr/bin/env python3
"""
Migratie: padclaims uit het systeemeffecten-onderzoek (vervolg op
migrate_systeemeffecten_onderzoek.py).

Het webonderzoek leverde naast zes hyperedges ook twee composities op die de
literatuur zelf benoemt en waarvoor een route door de rolgraaf bestaat die het
verhaal van de claim volgt:

  politicus  ⇢ publiek   RMO 'Medialogica' (2003): het krachtenveld
                         burgers-media-politiek als gesloten lus; route
                         woordvoerdersregie → persbureau_brongebondenheid →
                         pakketjournalistiek → schijndebat.
  voorlichter ⇢ publiek  voorlichtingsovermacht (UvA/CBS via Villamedia 2018)
                         + 'grotendeels ongecontroleerd doorgegeven'
                         (sources/AI/propagandsmodel2.md r. 67-72, 99); zelfde
                         keten vanaf de voorlichter, plus de kortere route via
                         pr_subsidie.

Géén padclaims voor de andere nieuwe systeemeffecten, omdat de vorm niet past:
mediahype en verkillingsspiraal zijn lússen (cyclisch — geen A ⇢ C),
ideologische_homofilie is gelijkvormigheid tussen rollen (geen pad),
schijnpluriformiteit is een optelsom over álle titels (geen dyadische
compositie) en techplatform → publiek is al een directe edge
(algoritmische_socialisatie).

Omdat poort 2 (eigen discussieboom-argumenten per schakel) anders faalt,
krijgen twee tot nu toe onbeargumenteerde schakels hun onderbouwing:
persbureau_brongebondenheid (Boumans 2016) en pr_subsidie (Herman & Chomsky;
overmachtscijfers).

Backup-then-migrate; idempotent op (role_id, property, property_value) voor
claims en op (mechanism_id, claim) voor argumenten.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-padclaims-systeemeffecten-2026-06"


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

    def source_id(title_prefix):
        r = cur.execute("SELECT id FROM sources WHERE title LIKE ?",
                        (title_prefix + "%",)).fetchone()
        if not r:
            raise SystemExit(f"FOUT: bron ontbreekt: {title_prefix} "
                             "(draai eerst migrate_systeemeffecten_onderzoek.py)")
        return r[0]

    SRC_RMO = source_id("Medialogica. Over het krachtenveld")
    SRC_VILLA = source_id("Verhouding communicatieprofessionals-journalisten")
    SRC_BOUMANS = source_id("Outsourcing the news?")
    SRC_HC = source_id("Manufacturing Consent")

    # ---- PADCLAIMS -----------------------------------------------------------
    def add_claim(src, tgt, claim, reasoning, weight, citations):
        if cur.execute(
            "SELECT 1 FROM arguments WHERE role_id=? AND property='indirecte_invloed_op' "
            "AND property_value=?", (roles[src], tgt)).fetchone():
            print(f"claim bestaat al: {src} ⇢ {tgt}")
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

    add_claim(
        "politicus", "publiek",
        "De politiek heeft — gemedieerd en gedempt — invloed op het beeld dat "
        "het publiek krijgt: via woordvoerdersregie en de officiële agenda's "
        "stroomt de politieke frontstage door persbureau en titels naar de "
        "burger.",
        "Het RMO-rapport Medialogica beschrijft het krachtenveld "
        "burgers-media-politiek als gesloten lus (vgl. ook 'Het publiek volgt "
        "media die de politiek volgen', VU): de compositie zelf is benoemd, "
        "niet alleen de losse schakels. De doorlatende route volgt het verhaal "
        "van de claim: woordvoerdersregie → persbureau_brongebondenheid → "
        "pakketjournalistiek → schijndebat (mediaorganisatie → publiek).",
        0.60,
        [(SRC_RMO,
          "Politiek en media zitten gevangen in een patroon van medialogica; "
          "wat het publiek te zien krijgt benadrukt personen, conflicten en "
          "incidenten in plaats van inhoud en langetermijnbeleid.",
          "typering van de RMO-kernbevinding (2003) via persverslagen "
          "(Montesquieu Instituut); geen letterlijk rapportcitaat")],
    )

    add_claim(
        "voorlichter", "publiek",
        "Voorverpakte voorlichting bereikt — gemedieerd — het publiek: "
        "persberichten en gecoördineerde woordvoering worden door persbureau "
        "en gekrompen redacties grotendeels ongecontroleerd doorgegeven en "
        "vormen zo het nieuwsbeeld van de burger.",
        "De voorlichtingsovermacht (±150.000 communicatieprofessionals "
        "tegenover ±15.000 journalisten) maakt de doorstroom structureel; het "
        "bronmateriaal benoemt de uitkomst aan publiekszijde expliciet "
        "(sources/AI/propagandsmodel2.md r. 99: nieuws dat het publiek bereikt "
        "wordt grotendeels geproduceerd en geframed vanuit het perspectief van "
        "de gevestigde machten). Routes: persbureau_brongebondenheid → "
        "pakketjournalistiek → schijndebat, en korter via pr_subsidie → "
        "schijndebat.",
        0.55,
        [(SRC_VILLA,
          "Circa 150.000 voorlichters en communicatiemedewerkers (UvA "
          "'Gevaarlijk spel' 2010; CBS 2017: 149.000) tegenover circa 15.000 "
          "journalisten.",
          "typering van de telling in het Villamedia-overzichtsartikel "
          "(Oremus, 2018); kanttekening: intern/extern niet onderscheiden")],
    )

    # ---- HOP-ONDERBOUWING (poort 2) ------------------------------------------
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

    add_arg(mech_id("persbureau_brongebondenheid"), "supporting",
        "Het persbureau leunt voor continue, goedkope en 'gezaghebbende' "
        "productie zwaar op officiële agenda's en kant-en-klare persberichten "
        "van voorlichters, die het grotendeels ongecontroleerd doorgeeft.",
        "Boumans' proefschrift onderzoekt precies deze rol van bronnen en "
        "persbureaus in de hedendaagse nieuwsketen; de routinematige "
        "afhankelijkheid van officiële en voorverpakte input is de kern van "
        "zijn bevindingen.",
        0.60,
        [(SRC_BOUMANS,
          "Persbureaus leunen voor hun continue productie structureel op "
          "routineuze, officiële bronnen en voorverpakt PR-materiaal.",
          "typering van de proefschrift-bevindingen (UvA 2016); geen "
          "letterlijk citaat")],
    )

    add_arg(mech_id("pr_subsidie"), "supporting",
        "PR-materiaal functioneert als informatiesubsidie: het verlaagt de "
        "productiekosten van nieuws en wordt daardoor door redacties onder "
        "tijds- en kostendruk overgenomen.",
        "Kernconcept van Herman & Chomsky's sourcing-filter; de Nederlandse "
        "overmachtscijfers (±150.000 communicatieprofessionals tegenover "
        "±15.000 journalisten) maken de subsidiestroom hier structureel.",
        0.60,
        [(SRC_HC,
          "De massamedia worden uit economische noodzaak in een symbiotische "
          "relatie met machtige informatiebronnen getrokken.",
          "parafrase van het derde filter uit Manufacturing Consent (1988); "
          "geen paginaverwijzing"),
         (SRC_VILLA,
          "Circa 150.000 voorlichters en communicatiemedewerkers tegenover "
          "circa 15.000 journalisten.",
          "typering van de telling in het Villamedia-overzichtsartikel "
          "(Oremus, 2018)")],
    )

    con.commit()

    # ---- SAMENVATTING --------------------------------------------------------
    print("---")
    for r_name, tgt in cur.execute(
        "SELECT r.name, a.property_value FROM arguments a JOIN roles r ON r.id=a.role_id "
        "WHERE a.property='indirecte_invloed_op' ORDER BY a.id"):
        print(f"  padclaim: {r_name} ⇢ {tgt}")
    for label, q in (
        ("arguments", "SELECT COUNT(*) FROM arguments"),
        ("citations", "SELECT COUNT(*) FROM citations"),
    ):
        print(f"{label:12s}: {cur.execute(q).fetchone()[0]}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
