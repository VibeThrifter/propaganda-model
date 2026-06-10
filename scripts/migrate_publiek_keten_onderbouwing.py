#!/usr/bin/env python3
"""
Migratie: onderbouwing van de keten naar het publiek + bron-reliability ingevuld.

Aanleiding (modelreview): de viz toont afgeleide (indirecte) pijlen alleen nog als
élke schakel van het pad onderbouwd is (theorie: geloofwaardigheid >= 0.10 per
mechanisme). De route belanghebbende -> mediaorganisatie -> publiek strandde op
twee schakels die wél echte literatuur hebben maar nog geen argument in de
discussieboom:

  - schijndebat (mediaorganisatie -> publiek): kernmechanisme uit Manufacturing
    Consent (debat binnen de grenzen van de elite-consensus); Bergman past het
    toe op Nederland. Bron id 2 + 3 stonden al geregistreerd, ongebruikt.
  - publieke_groeifinanciering (belanghebbende -> mediaorganisatie): concreet
    gedocumenteerd kanaal (EIB-groeileningen aan DPG, EUR 220 mln; FTM-kritiek).
    Bron id 13 + 14 stonden al geregistreerd op de relaties, niet op de theorie.

Daarnaast: drie boeken stonden op reliability 'onbeoordeeld' (de default =
"nog niet beoordeeld"), waardoor al hun citaties kunstmatig licht wogen.
Ingevuld, alleen waar nog 'onbeoordeeld':
  - id 2 Manufacturing Consent  -> academisch
  - id 3 De Nederlandse Nieuwsfabriek (Bergman) -> academisch
  - id 4 Je hebt het niet van mij, maar... (Luyendijk) -> kwaliteitsjournalistiek

Backup-then-migrate; idempotent op (mechanisme, claim) en reliability alleen
gewijzigd vanaf 'onbeoordeeld'.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-publiek-keten-2026-06"


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

    # ---- Bron-reliability invullen (alleen vanaf 'onbeoordeeld') ------------
    for sid, rel in ((2, "academisch"), (3, "academisch"), (4, "kwaliteitsjournalistiek")):
        n = cur.execute(
            "UPDATE sources SET reliability=? WHERE id=? AND reliability='onbeoordeeld'",
            (rel, sid)).rowcount
        titel = cur.execute("SELECT title FROM sources WHERE id=?", (sid,)).fetchone()
        print(("~ reliability " if n else "  reliability ongewijzigd ")
              + f"bron {sid} ({titel[0][:40]}…) -> {rel}" if titel else f"bron {sid} ontbreekt")

    def mech_id(name):
        r = cur.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
        if not r:
            raise SystemExit(f"mechanisme ontbreekt: {name}")
        return r[0]

    def add_arg(mech_name, stance, claim, reasoning, weight, citations):
        mid = mech_id(mech_name)
        if cur.execute("SELECT 1 FROM arguments WHERE mechanism_id=? AND claim=?",
                       (mid, claim)).fetchone():
            print(f"argument bestaat al bij {mech_name}")
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

    add_arg("schijndebat", "supporting",
        "Media moedigen levendig debat aan zolang het binnen de vooronderstellingen "
        "van de elite-consensus blijft; wat daarbuiten valt wordt niet weerlegd "
        "maar genegeerd — het debat zelf toont de schijn van pluriformiteit.",
        "Kernmechanisme van het propagandamodel (Herman & Chomsky); Bergman laat "
        "zien dat het Nederlandse debat dezelfde insluitings-/uitsluitingslogica "
        "volgt. Zonder deze schakel is de keten van belang naar publiek in het "
        "theoriemodel niet onderbouwd.",
        0.70,
        [(2, "spirited debate within the system of presuppositions that "
             "constitute an elite consensus",
          "typering van de kernstelling uit Manufacturing Consent; geen "
          "letterlijk citaat"),
         (3, "het Nederlandse publieke debat beweegt binnen dezelfde "
             "consensusgrenzen",
          "typering van Bergmans Nederlandse toepassing; geen letterlijk citaat")],
    )

    add_arg("publieke_groeifinanciering", "supporting",
        "Publieke instellingen financieren mediaorganisaties met groeileningen "
        "(EIB aan DPG: EUR 100 mln in 2022 + EUR 120 mln in 2025); daarmee bestaat "
        "een gedocumenteerde geldstroom van belanghebbende naar mediaorganisatie.",
        "Het kanaal zelf is institutioneel bevestigd (EIB-persbericht); FTM "
        "documenteert de kritische vragen over afhankelijkheid en besteding "
        "('Trusted Web'). Invloed op berichtgeving blijft onbewezen — dat zit in "
        "de sterkte-score, niet in deze bestaansclaim.",
        0.60,
        [(13, "DPG Media signs new loan agreement with EIB",
          "EUR 120 mln-tranche 2025; institutionele bevestiging van het kanaal"),
         (14, "In de strijd tegen Big Tech misbruikt uitgever DPG Europese "
              "miljoenen",
          "kritische duiding van de geldstroom door FTM")],
    )

    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    c = cur.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
    con.close()
    print(f"Klaar: {n} argumenten, {c} citaties.")


if __name__ == "__main__":
    main()
