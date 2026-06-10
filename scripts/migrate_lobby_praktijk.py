#!/usr/bin/env python3
"""
Migratie: lobby-praktijklaag — de gedocumenteerde casussen die de lobbyroute
in het theoriemodel haar werkelijke gewicht geven.

De theorie-mechanismen belangenbehartiging / lobbyist_naar_politicus /
lobbyist_naar_journalist hadden geen enkele praktijk-instantie, waardoor hun
sterkte (= gewogen praktijk-invloed, zie scoring.theory_scores) op nul bleef en
de afgeleide invloed van de belanghebbende in de viz via andere routes liep.

Toegevoegd op basis van publiek gedocumenteerde gevallen:
  - VNO-NCW (nieuwe entiteit, lobbygroep/lobbyist) — Malietoren, SER-zetels.
  - Shell → VNO-NCW en Unilever → VNO-NCW (belangenbehartiging): de
    dividendbelasting-memo's (vrijgegeven 24-4-2018) tonen de opdrachtgevers.
  - VNO-NCW → Tweede Kamer (lobbyist_naar_politicus): zelfde casus + de
    geïnstitutionaliseerde toegang (SER, polderoverleg).
  - KLM → Tweede Kamer (lobbyist_naar_politicus): staatssteunlobby 2020
    (EUR 3,4 mld), tweede onafhankelijke instantie.
  - VNO-NCW → ANP (lobbyist_naar_journalist): persberichten/standpunten landen
    via de persbureauroutine in de berichtgeving — kanaal zeker, gerichte
    sturing niet aangetoond, dus lage zekerheid/invloed.

De scores coderen de onzekerheid; de dividendcasus krijgt ook een
contradicting argument (de afschaffing sneuvelde in oktober 2018 — lobbymacht
is sterk maar niet onbegrensd). Backup-then-migrate; idempotent.
"""
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-lobby-praktijk-2026-06"


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
        if not r:
            raise SystemExit(f"mechanisme ontbreekt: {name}")
        return r[0]

    def entity_id(name):
        r = cur.execute("SELECT id FROM entities WHERE name=?", (name,)).fetchone()
        return r[0] if r else None

    # ---- ENTITEIT: VNO-NCW -------------------------------------------------
    if not entity_id("VNO-NCW"):
        cur.execute(
            """INSERT INTO entities (name, type, primary_role_id, description, metadata)
               VALUES (?,?,?,?,?)""",
            ("VNO-NCW", "lobbygroep", role_id("lobbyist"),
             "Grootste Nederlandse ondernemingsorganisatie en de meest "
             "geïnstitutionaliseerde lobby van het land: zetels in de SER, vast "
             "polderoverleg met kabinet en sociale partners, kantoor in de "
             "Malietoren op loopafstand van het Binnenhof.",
             json.dumps({"bron": CONTRIB})))
        print("+ entiteit VNO-NCW (lobbygroep/lobbyist)")
    else:
        print("entiteit bestaat al: VNO-NCW")
    vno = entity_id("VNO-NCW")
    cur.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id) VALUES (?,?)",
                (vno, role_id("lobbyist")))
    if not cur.execute("SELECT 1 FROM instantiations WHERE role_id=? AND entity_id=?",
                       (role_id("lobbyist"), vno)).fetchone():
        cur.execute("INSERT INTO instantiations (role_id, entity_id, exemplarity, notes) "
                    "VALUES (?,?,?,?)", (role_id("lobbyist"), vno, 0.9, CONTRIB))

    # Bestaande bedrijven zijn in deze relaties belanghebbende (naast hun primaire rol).
    for naam in ("Shell", "Unilever", "KLM"):
        eid = entity_id(naam)
        if eid:
            cur.execute("INSERT OR IGNORE INTO entity_roles (entity_id, role_id) VALUES (?,?)",
                        (eid, role_id("belanghebbende")))

    # ---- RELATIES ------------------------------------------------------------
    def find_relation(src, tgt, mech=None):
        q = "SELECT id FROM relations WHERE source_id=? AND target_id=?"
        p = [entity_id(src), entity_id(tgt)]
        if mech:
            q += " AND mechanism_id=?"
            p.append(mech_id(mech))
        r = cur.execute(q, p).fetchone()
        return r[0] if r else None

    def add_relation(src, tgt, rel_type, mech, desc, certainty, influence,
                     active_from=None, exemplarity=0.8):
        rid = find_relation(src, tgt, mech)
        if rid:
            print(f"relatie bestaat al: {src} -> {tgt}")
            return rid
        cur.execute(
            """INSERT INTO relations
               (source_id, target_id, relation_type, mechanism_id, description,
                certainty, influence, active_from)
               VALUES (?,?,?,?,?,?,?,?)""",
            (entity_id(src), entity_id(tgt), rel_type, mech_id(mech), desc,
             certainty, influence, active_from))
        rid = cur.lastrowid
        cur.execute("INSERT INTO instantiations (mechanism_id, relation_id, exemplarity, notes) "
                    "VALUES (?,?,?,?)", (mech_id(mech), rid, exemplarity, CONTRIB))
        print(f"+ relatie {src} -> {tgt} ({rel_type}/{mech}) cert={certainty} infl={influence}")
        return rid

    r_shell = add_relation("Shell", "VNO-NCW", "lidmaatschap", "belangenbehartiging",
        "Lid en agendabepalend zwaargewicht. De in april 2018 vrijgegeven "
        "dividendbelasting-memo's tonen dat Shell (met Unilever) via én naast "
        "VNO-NCW het kabinet bewerkte voor afschaffing van de dividendbelasting "
        "(EUR 1,4 mld).", 0.92, 0.55, exemplarity=0.9)

    r_uni = add_relation("Unilever", "VNO-NCW", "lidmaatschap", "belangenbehartiging",
        "Lid en agendabepalend zwaargewicht; zelfde dividendbelasting-casus. "
        "Unilever koppelde de hoofdkantoorkeuze expliciet aan het Nederlandse "
        "vestigingsklimaat.", 0.90, 0.55, exemplarity=0.9)

    r_vno_tk = add_relation("VNO-NCW", "Tweede Kamer", "lobbyt", "lobbyist_naar_politicus",
        "Geïnstitutionaliseerde toegang: SER-zetels, polderoverleg, position "
        "papers en kant-en-klare inbreng voor Kamerdebatten. De "
        "dividendbelasting-memo's (vrijgegeven 24-4-2018) documenteren de "
        "directe route van werkgeverslobby naar regeerakkoord.",
        0.88, 0.60, exemplarity=0.9)

    r_klm = add_relation("KLM", "Tweede Kamer", "lobbyt", "lobbyist_naar_politicus",
        "Staatssteunlobby 2020: KLM verkreeg een steunpakket van EUR 3,4 mld "
        "(leningen en garanties), na intensieve lobby richting kabinet en Kamer "
        "onder verwijzing naar netwerkfunctie en werkgelegenheid.",
        0.85, 0.55, active_from="2020-06-26", exemplarity=0.7)

    r_vno_anp = add_relation("VNO-NCW", "ANP", "bron_van", "lobbyist_naar_journalist",
        "Persberichten, standpunten en woordvoering van VNO-NCW landen via de "
        "persbureauroutine breed in de berichtgeving. Het kanaal is zeker; "
        "gerichte sturing van individuele journalisten is niet aangetoond — "
        "vandaar lage zekerheid en bescheiden invloed.",
        0.50, 0.40, exemplarity=0.6)

    # ---- BRONNEN -------------------------------------------------------------
    def add_source(title, author, stype, publisher, date, reliability, url=None):
        r = cur.execute("SELECT id FROM sources WHERE title=?", (title,)).fetchone()
        if r:
            return r[0]
        cur.execute(
            """INSERT INTO sources (title, author, source_type, publisher,
               date_published, reliability, processed)
               VALUES (?,?,?,?,?,?,1)""",
            (title, author, stype, publisher, date, reliability))
        sid = cur.lastrowid
        if url:
            cur.execute("INSERT INTO source_locations (source_id, location_type, location) "
                        "VALUES (?,?,?)", (sid, "url", url))
        return sid

    s_memo = add_source(
        "Memo's dividendbelasting openbaar gemaakt",
        "Ministerie van Algemene Zaken / Ministerie van Financiën",
        "rapport", "Rijksoverheid", "2018-04-24", "institutioneel")
    s_ti = add_source(
        "Lifting the Lid on Lobbying: Enhancing Trust in Public Decision-making "
        "in the Netherlands",
        "Transparency International Nederland", "rapport",
        "Transparency International NL", "2015-01-01", "institutioneel")
    s_klm = add_source(
        "Staat steunt KLM met leningen en garanties van 3,4 miljard euro",
        "Ministerie van Financiën", "persbericht", "Rijksoverheid",
        "2020-06-26", "institutioneel")

    # ---- ARGUMENTEN + CITATIES -----------------------------------------------
    def add_arg(relation_id, stance, claim, reasoning, weight, citations):
        if cur.execute("SELECT 1 FROM arguments WHERE relation_id=? AND claim=?",
                       (relation_id, claim)).fetchone():
            print("argument bestaat al")
            return
        cur.execute(
            """INSERT INTO arguments (relation_id, stance, claim, reasoning,
               weight, status, contributed_by)
               VALUES (?,?,?,?,?,?,?)""",
            (relation_id, stance, claim, reasoning, weight, "ongecontroleerd", CONTRIB))
        aid = cur.lastrowid
        for sid, quote, ctx in citations:
            cur.execute("INSERT INTO citations (argument_id, source_id, quote, context) "
                        "VALUES (?,?,?,?)", (aid, sid, quote, ctx))
        print(f"+ argument ({stance}) bij relatie {relation_id}")

    add_arg(r_vno_tk, "supporting",
        "De in april 2018 vrijgegeven memo's tonen dat de voorgenomen afschaffing "
        "van de dividendbelasting (EUR 1,4 mld) mede op aandringen van VNO-NCW, "
        "Shell en Unilever in het regeerakkoord kwam, tegen ambtelijke adviezen in.",
        "Best gedocumenteerde Nederlandse lobbycasus: de papieren route van "
        "werkgeverslobby naar kabinetsbeleid is door het kabinet zelf openbaar "
        "gemaakt na Kamerdruk.",
        0.75,
        [(s_memo,
          "memo's over de afschaffing van de dividendbelasting openbaar gemaakt",
          "vrijgegeven na aanhoudende Kamervragen; parafrase van de strekking")],
    )
    add_arg(r_vno_tk, "contradicting",
        "De afschaffing van de dividendbelasting werd in oktober 2018 alsnog "
        "teruggedraaid na publieke en politieke druk en het afketsen van de "
        "Unilever-hoofdkantoorverhuizing.",
        "Begrenst de influence-score: de lobby bepaalt de agenda maar wint niet "
        "altijd het eindspel; tegenmacht (publiek debat, Kamer) corrigeerde hier.",
        0.50,
        [(s_memo, "afschaffing dividendbelasting", "afloop oktober 2018; context")],
    )
    add_arg(r_shell, "supporting",
        "Shell leverde via en naast VNO-NCW directe input voor het fiscale "
        "vestigingsklimaat-dossier; de memo's noemen de multinationals als "
        "gesprekspartners van het kabinet.",
        "Bevestigt de opdrachtgeversrelatie belanghebbende → lobbyist.",
        0.65,
        [(s_memo, "gesprekken met multinationals over het vestigingsklimaat",
          "parafrase van de strekking van de vrijgegeven memo's")],
    )
    add_arg(r_klm, "supporting",
        "KLM verkreeg in juni 2020 een steunpakket van EUR 3,4 mld na intensieve "
        "lobby richting kabinet en Kamer.",
        "Tweede onafhankelijke instantie van het kanaal lobbyist → politicus, "
        "in een ander dossier (luchtvaart i.p.v. fiscaliteit).",
        0.70,
        [(s_klm, "leningen en garanties van 3,4 miljard euro voor KLM", "")],
    )
    add_arg(r_vno_anp, "contradicting",
        "Nederland kent geen verplicht lobbyregister; de omvang van de "
        "persbeïnvloeding door belangenorganisaties is daardoor niet "
        "systematisch gedocumenteerd.",
        "Verklaart de lage zekerheid van deze relatie: het kanaal is plausibel "
        "en past in de churnalism-bevindingen, maar gerichte sturing is niet "
        "aangetoond.",
        0.45,
        [(s_ti, "The Netherlands lacks mandatory lobbying transparency",
          "TI-NL-rapport over het ontbreken van lobbytransparantie; parafrase")],
    )

    con.commit()

    # ---- SAMENVATTING ----------------------------------------------------------
    for label, q in (
        ("entities", "SELECT COUNT(*) FROM entities"),
        ("relations", "SELECT COUNT(*) FROM relations"),
        ("arguments", "SELECT COUNT(*) FROM arguments"),
        ("citations", "SELECT COUNT(*) FROM citations"),
        ("sources", "SELECT COUNT(*) FROM sources"),
    ):
        print(f"{label:10s}: {cur.execute(q).fetchone()[0]}")
    con.close()
    print("klaar.")


if __name__ == "__main__":
    main()
