#!/usr/bin/env python3
"""
Migratie: Luyendijk-stamroutes — twee ontbrekende schakels + de Haagse stam als hyperedge.

Aanleiding: de indirecte effecten uit "Je hebt het niet van mij, maar..." (Luyendijk,
bron id 4; duiding in sources/AI/propagandsmodel2.md) zijn paden over directe edges.
De Kamervragen-witwasroute (belanghebbende → lobbyist → politicus → journalist) is al
compleet, maar twee schakels ontbreken waardoor andere Luyendijk-routes niet
traceerbaar zijn in de invloedsgraaf:

  1. media_agendering   (mediaorganisatie → politicus) — "krantenkop wordt Kamervraag";
     ontsluit de tweede lobbyroute belanghebbende → lobbyist → journalist → ... → politicus.
  2. woordvoerdersregie (politicus → voorlichter) — de politicus stuurt zijn woordvoerder;
     ontsluit politicus → voorlichter → journalist (toegang als ruilmiddel).

Daarnaast krijgt Luyendijks kernthese een eigen plek in de emergentielaag:

  3. haagse_stam (hyperedge over politicus, voorlichter, lobbyist, journalist) — de
     groepseigenschap "één stam" incl. het tweede-orde-effect dat de lobby zelf
     structureel ongecoverd blijft.

Conform repo-conventie: eerst backup (data/propaganda_model_backup_<ts>.db), dan
muteren. Idempotent op naam (mechanisms/emergent_effects uniek per naam).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-luyendijk-stam-2026-06"
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

    # ---- THEORIELAAG: twee nieuwe mechanismen ------------------------------
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
             role_id(src_role), role_id(tgt_role), aard),
        )
        mid = cur.lastrowid
        for f in filters:
            cur.execute("INSERT OR IGNORE INTO mechanism_filters VALUES (?,?)", (mid, f))
        for t in themes:
            cur.execute("INSERT OR IGNORE INTO mechanism_themes VALUES (?,?)", (mid, t))
        print(f"+ mechanisme {name} (filter={prim_filter}, aard={aard})")
        return mid

    m_agenda = add_mechanism(
        "media_agendering", "sourcing", "procedureel",
        "Berichtgeving zet de politieke agenda: een krantenkop of nieuwsitem wordt "
        "Kamervraag, spoeddebat of beleidsreactie. Politici en hun staf monitoren "
        "de media doorlopend en richten hun handelen op de medialogica. Daarmee "
        "bestaat een tweede lobbyroute: wie een verhaal bij een journalist plant "
        "('je hebt het niet van mij, maar...'), beweegt daarmee indirect de "
        "politiek.",
        "De invloedsketen belanghebbende → lobbyist → journalist → politicus wordt "
        "traceerbaar; de politiek volgt deels een media-agenda die zelf al door de "
        "stam is voorgevormd, waardoor frames tussen media en politiek circuleren "
        "zonder externe toets.",
        "mediaorganisatie", "politicus", "direct",
        [], [],
    )

    m_regie = add_mechanism(
        "woordvoerdersregie", "sourcing", "procedureel",
        "De politicus stuurt zijn woordvoerder: wie toegang krijgt, welke primeur "
        "naar wie gaat, embargo's en achtergrondgesprekken, en wie wordt "
        "uitgesloten van de informatiestroom. De voorlichter voert deze "
        "toegangsdisciplinering uit, op afstand van de politicus zelf — die houdt "
        "schone handen. Raakt naast Sourcing ook Flak (disciplinering via "
        "uitsluitingsdreiging).",
        "Toegang wordt ruilmiddel; de dreiging van uitsluiting uit de "
        "informatiestroom loopt via de voorlichter en voedt terughoudendheid en "
        "zelfcensuur bij journalisten die hun bronnen morgen weer nodig hebben.",
        "politicus", "voorlichter", "direct",
        ["flak"], [],
    )

    # ---- EMERGENTIELAAG: de Haagse stam als hyperedge ----------------------
    STAM_LEDEN = ["politicus", "voorlichter", "lobbyist", "journalist"]
    stam_desc = (
        "Luyendijks etnografische kernbevinding: politici, voorlichters, "
        "lobbyisten en journalisten op het Binnenhof functioneren als één stam — "
        "gedeelde fysieke ruimte, gedeeld jargon, ongeschreven regels en een "
        "diepe wederzijdse afhankelijkheid. Geen van de dyadische relaties vangt "
        "dit; het is een eigenschap van de groep als geheel."
    )
    stam_effect = (
        "Parlementaire verslaggeving volgt de agenda en frames van de zittende "
        "macht, en de stam beschermt zichzelf: de lobby wordt zelf vrijwel nooit "
        "gecoverd, zodat de lobbyist voor het publiek structureel onzichtbaar "
        "blijft. Resultaat is een van de meest gesloten politieke culturen van "
        "het Westen."
    )
    cur.execute(
        "INSERT OR IGNORE INTO emergent_effects (name, label, category, description, effect) "
        "VALUES (?,?,?,?,?)",
        ("haagse_stam", "De Haagse stam", "sourcing", stam_desc, stam_effect),
    )
    eff_id = cur.execute("SELECT id FROM emergent_effects WHERE name='haagse_stam'").fetchone()[0]
    # Tekst en ledenset in sync houden met dit script (idempotente her-run).
    cur.execute(
        "UPDATE emergent_effects SET label=?, category=?, description=?, effect=? WHERE id=?",
        ("De Haagse stam", "sourcing", stam_desc, stam_effect, eff_id),
    )
    cur.execute("DELETE FROM emergent_effect_members WHERE emergent_effect_id=?", (eff_id,))
    for rn in STAM_LEDEN:
        cur.execute(
            "INSERT OR IGNORE INTO emergent_effect_members (emergent_effect_id, role_id) VALUES (?,?)",
            (eff_id, role_id(rn)),
        )
    print(f"+ emergent effect haagse_stam ({len(STAM_LEDEN)} leden: {', '.join(STAM_LEDEN)})")

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

    add_arg(m_agenda, "supporting",
        "Kamerleden leunen zwaar op door lobbyisten aangeleverde informatie voor "
        "het stellen van Kamervragen; berichtgeving en geplante verhalen vertalen "
        "zich zo direct in politiek handelen.",
        "Luyendijks veldwerk toont de route belang → verhaal in de media → "
        "politieke reactie; zonder de edge mediaorganisatie → politicus is die "
        "cascade niet in de invloedsgraaf te traceren.",
        0.60,
        [(src_id,
          "parlementsleden leunen zelfs zwaar op door lobbyisten aangeleverde "
          "informatie voor het stellen van Kamervragen",
          "typering van Luyendijks bevinding via sources/AI/propagandsmodel2.md "
          "(regel 72); geen letterlijk boekcitaat")],
    )

    add_arg(m_regie, "supporting",
        "Fundamentele kritiek of publicatie die een bron in verlegenheid brengt "
        "kan leiden tot uitsluiting uit de informatiestroom; die toegangsmacht "
        "wordt namens de politicus door diens voorlichter uitgeoefend.",
        "Journalisten zijn voor primeurs en achtergrond afhankelijk van de "
        "goodwill van politici en hun woordvoerders; de voorlichter is het "
        "uitvoerende kanaal van die disciplinering.",
        0.60,
        [(src_id,
          "Journalisten zijn voor hun primeurs en achtergrondinformatie "
          "afhankelijk van de goodwill van politici en hun woordvoerders",
          "typering van Luyendijks bevinding via sources/AI/propagandsmodel2.md "
          "(regel 71); geen letterlijk boekcitaat")],
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
