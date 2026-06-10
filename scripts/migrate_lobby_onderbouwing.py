#!/usr/bin/env python3
"""
Migratie: discussieboom-onderbouwing voor de lobbyroute.

De drie lobby-edges (belangenbehartiging, lobbyist_naar_politicus,
lobbyist_naar_journalist) hadden nog geen argumenten, waardoor hun theorie-
sterkte op de bodemwaarde bleef en de afgeleide invloed van de belanghebbende
in de viz via andere (wél onderbouwde) routes liep. Luyendijks kernbevindingen
horen juist hier: Kamerleden leunen op door lobbyisten aangeleverde informatie
(→ lobbyist_naar_politicus) en lobbyisten planten verhalen bij journalisten
('je hebt het niet van mij, maar...' → lobbyist_naar_journalist), in opdracht
van betalende belanghebbenden (→ belangenbehartiging).

Backup-then-migrate; idempotent op (mechanisme, claim).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-lobby-onderbouwing-2026-06"
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

    def mech_id(name):
        r = cur.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
        if not r:
            raise SystemExit(f"mechanisme ontbreekt: {name}")
        return r[0]

    src = cur.execute("SELECT id FROM sources WHERE title LIKE ?",
                      (LUYENDIJK_TITLE + "%",)).fetchone()
    src_id = src[0] if src else None
    if src_id is None:
        print("WAARSCHUWING: Luyendijk-bron niet gevonden; argumenten zonder citatie.")

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
            if sid:
                cur.execute(
                    "INSERT INTO citations (argument_id, source_id, quote, context) "
                    "VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument ({stance}) bij {mech_name}")

    add_arg("lobbyist_naar_politicus", "supporting",
        "Kamerleden leunen zwaar op door lobbyisten aangeleverde informatie, tot "
        "en met kant-en-klare Kamervragen.",
        "Luyendijks etnografische kernbevinding over het kanaal lobbyist → "
        "politicus; maakt de Nederlandse politieke cultuur volgens hem een van "
        "de meest gesloten van het Westen.",
        0.65,
        [(src_id,
          "parlementsleden leunen zelfs zwaar op door lobbyisten aangeleverde "
          "informatie voor het stellen van Kamervragen",
          "typering van Luyendijks bevinding via sources/AI/propagandsmodel2.md "
          "(regel 72); geen letterlijk boekcitaat")],
    )

    add_arg("lobbyist_naar_journalist", "supporting",
        "Lobbyisten planten verhalen bij journalisten onder de mantel van "
        "vertrouwelijkheid ('je hebt het niet van mij, maar...'), als tweede "
        "kanaal naast hun directe politieke toegang.",
        "De boektitel zelf beschrijft dit kanaal: de lobbyist is volwaardig lid "
        "van de Haagse stam en gebruikt de journalist om het belang als nieuws "
        "te laten verschijnen.",
        0.60,
        [(src_id,
          "politici, voorlichters, lobbyisten en journalisten in Den Haag "
          "functioneren als één stam",
          "typering via sources/AI/propagandsmodel2.md (regel 71); geen "
          "letterlijk boekcitaat")],
    )

    add_arg("belangenbehartiging", "supporting",
        "De lobbyist opereert in opdracht van betalende belanghebbenden; zijn "
        "toegang tot politici en journalisten is het product dat hij verkoopt.",
        "Definieert de driehoek: de invloed die via de lobbyist bij politicus "
        "en journalist aankomt, is herleidbaar tot de opdrachtgever — de "
        "belanghebbende zelf blijft daarbij buiten beeld.",
        0.60,
        [(src_id,
          "politici, voorlichters, lobbyisten en journalisten in Den Haag "
          "functioneren als één stam",
          "typering via sources/AI/propagandsmodel2.md (regel 71); geen "
          "letterlijk boekcitaat")],
    )

    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM arguments").fetchone()[0]
    c = cur.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
    con.close()
    print(f"Klaar: {n} argumenten, {c} citaties.")


if __name__ == "__main__":
    main()
