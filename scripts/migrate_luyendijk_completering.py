#!/usr/bin/env python3
"""
Migratie: Luyendijk-completering — citaatautorisatie, primeurconcurrentie,
draaideur journalistiek→voorlichting, PR-inhuur + 'toeschouwersdemocratie' (hyperedge).

Vervolg op migrate_luyendijk_stam_routes.py. Maakt de uit "Je hebt het niet van
mij, maar..." (bron id 4; duiding sources/AI/propagandsmodel2.md) infereerbare
mechanismen af, conform de aard-regels in CLAUDE.md:

  - geen `indirect`-aard: de indirecte invloed van de belanghebbende (via lobbyist
    op politicus/journalist) blijft een PAD over directe edges; de viz toont die
    sinds deze review als afgeleide stippelpijl bij node-selectie.
  - citaatautorisatie            direct   voorlichter → journalist
  - draaideur_journalistiek_voorlichting  direct  journalist → voorlichter
  - pr_inhuur                    direct   belanghebbende → voorlichter
  - primeurconcurrentie          veld_eigenschap  (geen echte bron) → journalist
  - toeschouwersdemocratie       emergent hyperedge over {politicus, voorlichter,
                                 journalist, mediaorganisatie, publiek}

Conform repo-conventie: eerst backup (data/propaganda_model_backup_<ts>.db), dan
muteren. Idempotent op naam (mechanisms/emergent_effects uniek per naam).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-luyendijk-completering-2026-06"
LUYENDIJK_TITLE = "Je hebt het niet van mij, maar..."


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

    def mech_id(name):
        r = cur.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
        return r[0] if r else None

    # ---- THEORIELAAG: vier nieuwe mechanismen ------------------------------
    def add_mechanism(name, prim_filter, mtype, desc, effect, src_role, tgt_role,
                      aard, filters, themes):
        if mech_id(name):
            print(f"mechanisme bestaat al: {name}")
            return mech_id(name)
        cur.execute(
            """INSERT INTO mechanisms
               (name, filter, mechanism_type, description, effect,
                source_role_id, target_role_id, aard)
               VALUES (?,?,?,?,?,?,?,?)""",
            (name, prim_filter, mtype, desc, effect,
             role_id(src_role) if src_role else None,
             role_id(tgt_role) if tgt_role else None, aard),
        )
        mid = cur.lastrowid
        for f in filters:
            cur.execute("INSERT OR IGNORE INTO mechanism_filters VALUES (?,?)", (mid, f))
        for t in themes:
            cur.execute("INSERT OR IGNORE INTO mechanism_themes VALUES (?,?)", (mid, t))
        print(f"+ mechanisme {name} (filter={prim_filter}, aard={aard})")
        return mid

    m_autorisatie = add_mechanism(
        "citaatautorisatie", "sourcing", "procedureel",
        "De Haagse gewoonte dat citaten en passages vóór publicatie ter inzage en "
        "correctie aan de bron (of diens voorlichter) worden voorgelegd. Anders dan "
        "het voorlichter-informatiefilter — dat bepaalt wat naar buiten gaat — geeft "
        "autorisatie de bron redactiemacht over de tekst van de journalist zelf: "
        "scherpe formuleringen worden afgezwakt als prijs voor het behoud van de "
        "bronrelatie.",
        "De bron schrijft mee aan zijn eigen berichtgeving; kritische randen "
        "verdwijnen vóór publicatie en het publiek ziet een door de bron "
        "geautoriseerde versie zonder dat te weten.",
        "voorlichter", "journalist", "direct",
        [], [],
    )

    m_draaideur = add_mechanism(
        "draaideur_journalistiek_voorlichting", "sourcing", "structureel",
        "De meest gelopen draaideur van het Binnenhof: journalisten stappen over "
        "naar woordvoerderschap en PR (betere beloning, zelfde biotoop). Het "
        "vooruitzicht op die overstap werpt zijn schaduw vooruit: wie morgen "
        "voorlichter wil worden, valt vandaag de toekomstige werkgever niet hard "
        "aan. Versterkt bovendien de stam: de voorlichter kent het journalistieke "
        "handwerk en zijn oud-collega's van binnenuit.",
        "Anticiperende zelfcensuur via de arbeidsmarkt; de scheidslijn tussen "
        "journalistiek en belangencommunicatie vervaagt in beide richtingen.",
        "journalist", "voorlichter", "direct",
        [], ["draaideur"],
    )

    m_pr = add_mechanism(
        "pr_inhuur", "sourcing", "economisch",
        "Een belanghebbende (bedrijf, sector, ngo) huurt eigen voorlichters of "
        "PR-bureaus in. Spiegel van de lobbyroute: lobby is het belang richting "
        "politiek, PR is hetzelfde belang richting media — zelfde opdrachtgever, "
        "twee kanalen. Ontsluit de keten belanghebbende → voorlichter → "
        "persbureau/journalist (kant-en-klare 'informatiesubsidie').",
        "Belangen bereiken de berichtgeving verpakt als nieuws; gekrompen "
        "redacties nemen het materiaal van betaalde afzenders over.",
        "belanghebbende", "voorlichter", "direct",
        [], ["geldstromen"],
    )

    m_primeur = add_mechanism(
        "primeurconcurrentie", "sourcing", "psychologisch",
        "De wedloop om primeurs als eigenschap van het journalistencorps zelf: "
        "wie niet meebuigt in de ruilhandel met bronnen en voorlichters, ziet de "
        "primeur naar de concurrent gaan. Geen aanwijsbare externe afzender — de "
        "onderlinge concurrentie disciplineert; het is het voedingsmechanisme "
        "achter de zelfcensuur-halo.",
        "Volgzaamheid wordt beloond met exclusieve toegang en scoops; kritische "
        "distantie wordt een concurrentienadeel.",
        None, "journalist", "veld_eigenschap",
        [], [],
    )

    # ---- EMERGENTIELAAG: toeschouwersdemocratie als hyperedge --------------
    LEDEN = ["politicus", "voorlichter", "journalist", "mediaorganisatie", "publiek"]
    desc = (
        "Luyendijks toneelmetafoor: wat het publiek van de politiek te zien "
        "krijgt is de voorstelling (frontstage) — debat, Kamervraag, persmoment — "
        "terwijl de werkelijke afweging backstage plaatsvindt, in wandelgangen, "
        "achtergrondgesprekken en lobbycontact. Geen van de actoren regisseert "
        "dit; het is de gezamenlijke uitkomst van politiek dat zich op de camera "
        "richt, voorlichting die het beeld bewaakt en journalistiek die de "
        "opvoering verslaat."
    )
    effect = (
        "Het publiek kijkt naar politiek als toeschouwer van een opvoering: "
        "parlementaire controle wordt zelf mediaproduct (de Kamervraag om de "
        "krant te halen) en het debat blijft hangen in incidenten in plaats van "
        "structuren."
    )
    cur.execute(
        "INSERT OR IGNORE INTO emergent_effects (name, label, category, description, effect) "
        "VALUES (?,?,?,?,?)",
        ("toeschouwersdemocratie", "Toeschouwersdemocratie", "systeemactor", desc, effect),
    )
    eff_id = cur.execute(
        "SELECT id FROM emergent_effects WHERE name='toeschouwersdemocratie'").fetchone()[0]
    cur.execute(
        "UPDATE emergent_effects SET label=?, category=?, description=?, effect=? WHERE id=?",
        ("Toeschouwersdemocratie", "systeemactor", desc, effect, eff_id),
    )
    cur.execute("DELETE FROM emergent_effect_members WHERE emergent_effect_id=?", (eff_id,))
    for rn in LEDEN:
        cur.execute(
            "INSERT OR IGNORE INTO emergent_effect_members (emergent_effect_id, role_id) VALUES (?,?)",
            (eff_id, role_id(rn)),
        )
    print(f"+ emergent effect toeschouwersdemocratie ({len(LEDEN)} leden: {', '.join(LEDEN)})")

    # ---- DISCUSSIEBOOM: onderbouwing op mechanismeniveau -------------------
    src = cur.execute("SELECT id FROM sources WHERE title LIKE ?",
                      (LUYENDIJK_TITLE + "%",)).fetchone()
    src_id = src[0] if src else None
    if src_id is None:
        print("WAARSCHUWING: Luyendijk-bron niet gevonden; argumenten zonder citatie.")

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
            if sid:
                cur.execute(
                    "INSERT INTO citations (argument_id, source_id, quote, context) "
                    "VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument ({stance}) bij mechanisme {mechanism_id}")

    add_arg(m_primeur, "supporting",
        "Journalisten zijn voor primeurs en achtergrondinformatie afhankelijk van "
        "de goodwill van bronnen die ze morgen weer nodig hebben; de onderlinge "
        "concurrentie om die toegang disciplineert het hele corps.",
        "Luyendijks veldwerk beschrijft de primeur-ruileconomie van het Binnenhof "
        "als cultuur van het corps, niet als druk van één afzender — vandaar "
        "veld_eigenschap (halo) in plaats van een gerichte edge.",
        0.60,
        [(src_id,
          "Journalisten zijn voor hun primeurs en achtergrondinformatie "
          "afhankelijk van de goodwill van politici en hun woordvoerders",
          "typering van Luyendijks bevinding via sources/AI/propagandsmodel2.md "
          "(regel 71); geen letterlijk boekcitaat")],
    )

    add_arg(m_autorisatie, "supporting",
        "In de gesloten Haagse omgang met bronnen hoort het vooraf afstemmen en "
        "autoriseren van citaten tot de ongeschreven regels van de stam.",
        "De autorisatiepraktijk is de procedurele vorm van de terughoudendheid "
        "die Luyendijk beschrijft: de bron in verlegenheid brengen is een "
        "professionele doodzonde, dus krijgt de bron de tekst vooraf.",
        0.50,
        [(src_id,
          "Ze delen een fysieke ruimte, een jargon, ongeschreven regels en, "
          "bovenal, een diepe onderlinge afhankelijkheid",
          "typering van Luyendijks bevinding via sources/AI/propagandsmodel2.md "
          "(regel 71); geen letterlijk boekcitaat")],
    )

    add_arg(m_draaideur, "supporting",
        "De grenzen tussen journalistiek, politiek en belangenbehartiging "
        "vervagen door de draaideur; de overstap van journalist naar woordvoerder/"
        "adviseur is daarvan de meest voorkomende beweging.",
        "Het bronmateriaal beschrijft de draaideur expliciet, inclusief "
        "journalisten die woordvoerder of adviseur worden; de arbeidsmarktschaduw "
        "(anticiperende zelfcensuur) volgt daaruit als infereerbaar effect.",
        0.55,
        [(src_id,
          "Journalisten maken de overstap naar de politiek als woordvoerder of "
          "adviseur",
          "typering via sources/AI/propagandsmodel2.md (regel 74, "
          "'revolving door'); geen letterlijk boekcitaat")],
    )

    add_arg(m_pr, "supporting",
        "Dezelfde belanghebbende bedient twee kanalen: lobbyisten richting "
        "politiek en ingehuurde voorlichting/PR richting media; beide leveren "
        "kant-en-klaar materiaal dat gekrompen redacties overnemen.",
        "Spiegelt de bestaande keten belangenbehartiging → lobbyist; de "
        "PR-subsidie aan mediaorganisaties is al gemodelleerd, de opdrachtgever "
        "erachter (belanghebbende → voorlichter) nog niet.",
        0.55,
        [(src_id,
          "politici, voorlichters, lobbyisten en journalisten in Den Haag "
          "functioneren als één stam",
          "typering via sources/AI/propagandsmodel2.md (regel 71); geen "
          "letterlijk boekcitaat")],
    )

    con.commit()

    # ---- SAMENVATTING ------------------------------------------------------
    for label, q in (
        ("mechanisms", "SELECT COUNT(*) FROM mechanisms"),
        ("emergent_effects", "SELECT COUNT(*) FROM emergent_effects"),
        ("emergent_members", "SELECT COUNT(*) FROM emergent_effect_members"),
        ("arguments", "SELECT COUNT(*) FROM arguments"),
        ("citations", "SELECT COUNT(*) FROM citations"),
    ):
        print(f"{label:16s}: {cur.execute(q).fetchone()[0]}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
