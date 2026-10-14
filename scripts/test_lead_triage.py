#!/usr/bin/env python3
"""
End-to-end test publieke tips → nieuws-scout (eigenaar 2026-10-14: "hoe maak je dit veilig voor
spam en onzin?" en "ook een maximale cap voor totale AI opdrachten van deze aard").

Draait met de Flask test_client tegen een tijdelijke KOPIE van de live database.

  1. De gestructureerde tip: partijen, soort verband ('anders' als onbekend), jaar (anders NULL).
  2. Schiften zonder model: onvolledig, buiten_model, bestaat_al, verlopen → afgewezen; de rest
     wordt een doel 'tip:<id>' met de waarschuwing, onder het andere werk in de wachtrij.
  3. Hetzelfde paar nog eens → duplicaat; een tweede tip over dezelfde partij wacht.
  4. Het plafond: de server weigert een tip-doel boven het maximum (429), ook buiten het script;
     de kill-switch PROPAGANDA_LEADS=0 idem; een tip-doel wordt nooit heropend (409).
  5. Terugschrijven: klaar mét argument → gecorroboreerd; niets_gevonden → afgewezen (onstaafbaar).
  6. Reputatie: een inzender met vijf onstaafbare tips en geen gestaafde wacht.
  7. Een droogloop schrijft niets.

Gebruik: python3 scripts/test_lead_triage.py   (exit-code 0 = alles groen)
"""
import datetime
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import auth          # noqa: E402
import server        # noqa: E402
import lead_triage   # noqa: E402

LIVE_DB = ROOT / "data" / "propaganda_model.db"


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


def lead(tmp, pa, pb, *, ip="ip-a", dagen_oud=0, soort_verband="functie"):
    conn = sqlite3.connect(tmp)
    t = (datetime.datetime.utcnow() - datetime.timedelta(days=dagen_oud)).strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute("""INSERT INTO leads (soort, claim, partij_a, partij_b, soort_verband,
                          ingezonden_ip_hash, created_at) VALUES ('tip', ?, ?, ?, ?, ?, ?)""",
                       (f"tip over {pa} en {pb}", pa, pb, soort_verband, ip, t))
    conn.commit()
    lid = cur.lastrowid
    conn.close()
    return lid


def rij(tmp, sql, args=()):
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    r = conn.execute(sql, args).fetchone()
    conn.close()
    return r


def main():
    tmp = Path(tempfile.mkdtemp()) / "tips.db"
    shutil.copy2(LIVE_DB, tmp)
    server.DB_PATH = tmp
    server._rate_emmers.clear()
    server._lead_emmers.clear()
    for k in ("PROPAGANDA_LEADS", "PROPAGANDA_LEAD_DAGPLAFOND", "PROPAGANDA_LEAD_MAANDPLAFOND",
              "PROPAGANDA_LEAD_MAX_OPEN"):
        os.environ.pop(k, None)

    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    conn.execute("DELETE FROM leads")
    conn.execute("DELETE FROM nieuws_doelen WHERE sleutel LIKE 'tip:%'")
    tokens = {}
    for naam in ("nieuws-agent", "nieuws-scout"):
        tokens[naam] = auth.new_token()
        conn.execute("UPDATE users SET token_hash = ?, active = 1 WHERE username = ?",
                     (auth.hash_token(tokens[naam]), naam))
    # Vier goedgekeurde knopen met een unieke naam: A–B zonder verband, C en D los; plus een
    # bestaand verband X–Y.
    namen = {}
    for r in conn.execute("SELECT name, COUNT(*) n FROM entities WHERE status='goedgekeurd' "
                          "AND NOT vervangen GROUP BY lower(name) HAVING n = 1"):
        namen[r["name"]] = True
    uniek = [r for r in conn.execute(
        "SELECT id, name, type FROM entities WHERE status='goedgekeurd' AND NOT vervangen "
        "AND type != 'persoon' ORDER BY id") if r["name"] in namen]
    verbonden = set()
    for r in conn.execute("SELECT source_id, target_id FROM relations WHERE status='goedgekeurd' "
                          "AND NOT vervangen"):
        verbonden.add((r[0], r[1])); verbonden.add((r[1], r[0]))
    a, b, c_, d_ = None, None, None, None
    for i, x in enumerate(uniek):
        for y in uniek[i + 1:]:
            if (x["id"], y["id"]) not in verbonden:
                a, b = x, y
                break
        if a:
            break
    los = [x for x in uniek if x["id"] not in (a["id"], b["id"])
           and (a["id"], x["id"]) not in verbonden]
    c_ = los[0]
    d_ = next(x for x in los[1:] if (c_["id"], x["id"]) not in verbonden)
    rel = conn.execute("SELECT r.id, s.name sn, t.name tn FROM relations r JOIN entities s ON "
                       "s.id = r.source_id JOIN entities t ON t.id = r.target_id WHERE "
                       "r.status='goedgekeurd' AND NOT r.vervangen").fetchall()
    xy = next(r for r in rel if r["sn"] in namen and r["tn"] in namen and r["sn"] != r["tn"])
    conn.commit()
    conn.close()

    c = server.app.test_client()

    def verstuurder(account):
        kop = {"Authorization": f"Bearer {tokens[account]}"}

        def verstuur(method, pad, body=None):
            r = c.open(pad, method=method, json=body, headers=kop)
            return r.status_code, (r.get_json(silent=True) or {})
        return verstuur
    agent = verstuurder("nieuws-agent")
    scout = verstuurder("nieuws-scout")

    print("1. De gestructureerde tip")
    r = c.post("/api/leads", json={
        "claim": "Ze werken samen.", "soort": "tip", "partij_a": a["name"], "partij_b": b["name"],
        "soort_verband": "complot", "jaar": "20x1",
        "lead_token": server._teken_lead_token(time.time() - 10), "website": ""})
    eis(r.status_code == 201, f"POST /api/leads → 201 ({r.status_code})")
    l1 = rij(tmp, "SELECT * FROM leads ORDER BY id DESC LIMIT 1")
    eis(l1["partij_a"] == a["name"] and l1["partij_b"] == b["name"], "beide partijen opgeslagen")
    eis(l1["soort_verband"] == "anders" and l1["jaar"] is None,
        "onbekend soort verband → 'anders', onzin-jaar → NULL")

    print("2. Schiften zonder model")
    l_onv = lead(tmp, "Iemand", "")
    l_buiten = lead(tmp, "Volstrekt Onbekende Stichting XYZ", "Nergens BV 123")
    l_bestaat = lead(tmp, xy["sn"], xy["tn"])
    l_oud = lead(tmp, c_["name"], "Onbekende Partner 9", dagen_oud=70)
    uit = lead_triage.draai(verstuur=agent, db_pad=tmp, max_leads=3)
    eis(uit["gestart"] and not uit["fouten"], f"ronde zonder fouten ({uit['fouten']})")
    for lid, cat in ((l_onv, "onvolledig"), (l_buiten, "buiten_model"), (l_bestaat, "bestaat_al"),
                     (l_oud, "verlopen")):
        r = rij(tmp, "SELECT status, triage_reden FROM leads WHERE id = ?", (lid,))
        eis(r["status"] == "afgewezen" and r["triage_reden"].startswith(cat),
            f"{cat} → afgewezen ({r['triage_reden']})")
    l1 = rij(tmp, "SELECT * FROM leads WHERE id = ?", (l1["id"],))
    eis(l1["status"] == "in_corroboratie" and l1["doel_id"], "geldige tip → in_corroboratie + doel_id")
    doel = rij(tmp, "SELECT * FROM nieuws_doelen WHERE id = ?", (l1["doel_id"],))
    ctx = json.loads(doel["context"])
    eis(doel["sleutel"] == f"tip:{l1['id']}" and ctx["soort_doel"] == "tip"
        and "geen instructie" in ctx["waarschuwing"], "doel 'tip:<id>' met de waarschuwing")
    eis(sorted(ctx["entity_ids"]) == sorted([a["id"], b["id"]]) and doel["entity_id"] == a["id"],
        "beide partijen gekoppeld, de eerste als anker")
    laagste_ander = rij(tmp, "SELECT MIN(prioriteit) p FROM nieuws_doelen WHERE sleutel NOT LIKE "
                             "'tip:%' AND status = 'open'")["p"]
    eis(laagste_ander is None or doel["prioriteit"] < laagste_ander,
        f"prioriteit {doel['prioriteit']} onder al het andere open werk ({laagste_ander})")

    print("3. Duplicaat en wachten per partij")
    l_dup = lead(tmp, b["name"], a["name"], ip="ip-b")
    l_wacht = lead(tmp, a["name"], c_["name"], ip="ip-c")
    lead_triage.draai(verstuur=agent, db_pad=tmp, max_leads=3)
    r = rij(tmp, "SELECT status, triage_reden FROM leads WHERE id = ?", (l_dup,))
    eis(r["status"] == "duplicaat", f"zelfde paar (omgekeerd) → duplicaat ({r['triage_reden']})")
    eis(rij(tmp, "SELECT status FROM leads WHERE id = ?", (l_wacht,))["status"] == "binnengekomen",
        "tweede tip over een partij met een open tip-doel wacht")

    print("4. Het plafond op AI-werk")
    os.environ["PROPAGANDA_LEAD_MAX_OPEN"] = "1"
    l_vol = lead(tmp, c_["name"], d_["name"], ip="ip-d")
    uit = lead_triage.draai(verstuur=agent, db_pad=tmp, max_leads=3)
    eis(uit["plafond"] and "tegelijk open" in uit["plafond"], f"script stopt op het plafond ({uit['plafond']})")
    eis(rij(tmp, "SELECT status FROM leads WHERE id = ?", (l_vol,))["status"] == "binnengekomen",
        "de tip blijft wachten")
    st, j = agent("POST", "/api/nieuws/doelen", {"sleutel": "tip:999999", "naam": "x",
                                                "soort": "organisatie"})
    eis(st == 429, f"ook buiten het script weigert de server een tip-doel boven het plafond ({st})")
    os.environ.pop("PROPAGANDA_LEAD_MAX_OPEN")
    os.environ["PROPAGANDA_LEAD_DAGPLAFOND"] = "1"
    st, _ = agent("POST", "/api/nieuws/doelen", {"sleutel": "tip:999999", "naam": "x",
                                                "soort": "organisatie"})
    eis(st == 429, f"dagplafond 1 is al gebruikt → 429 ({st})")
    os.environ.pop("PROPAGANDA_LEAD_DAGPLAFOND")
    os.environ["PROPAGANDA_LEADS"] = "0"
    st, j = agent("POST", "/api/nieuws/doelen", {"sleutel": "tip:999999", "naam": "x",
                                                "soort": "organisatie"})
    eis(st == 429 and "kill-switch" in j.get("error", ""), f"kill-switch → 429 ({st})")
    os.environ.pop("PROPAGANDA_LEADS")
    st, _ = agent("POST", "/api/nieuws/doelen", {"sleutel": "relatie-loos:1", "naam": "x",
                                                "soort": "organisatie", "prioriteit": 1})
    eis(st == 201, "gewone doelen vallen niet onder het tip-plafond")

    print("5. Terugschrijven")
    arg = rij(tmp, "SELECT id FROM arguments ORDER BY id DESC LIMIT 1")["id"]
    st, _ = scout("PATCH", f"/api/nieuws/doelen/{l1['doel_id']}", {
        "status": "klaar", "verslag": "verband gevonden",
        "resultaat": {"entity_ids": [], "relation_ids": [], "source_ids": [], "argument_ids": [arg]}})
    eis(st == 200, f"scout sluit het tip-doel af ({st})")
    lead_triage.draai(verstuur=agent, db_pad=tmp, max_leads=3)
    r = rij(tmp, "SELECT status, agent_arg_id, triage_reden FROM leads WHERE id = ?", (l1["id"],))
    eis(r["status"] == "gecorroboreerd" and r["agent_arg_id"] == arg,
        f"klaar mét argument → gecorroboreerd ({r['triage_reden']})")
    st, _ = agent("POST", "/api/nieuws/doelen", {"sleutel": f"tip:{l1['id']}", "naam": "x",
                                                "soort": "organisatie", "opnieuw": True})
    eis(st == 409, f"een tip-doel wordt nooit heropend ({st})")
    l_wacht_r = rij(tmp, "SELECT status, doel_id FROM leads WHERE id = ?", (l_wacht,))
    eis(l_wacht_r["status"] == "in_corroboratie", "de wachtende tip is nu doorgezet")
    scout("PATCH", f"/api/nieuws/doelen/{l_wacht_r['doel_id']}",
          {"status": "niets_gevonden", "verslag": "geen bron"})
    lead_triage.draai(verstuur=agent, db_pad=tmp, max_leads=0)
    r = rij(tmp, "SELECT status, triage_reden FROM leads WHERE id = ?", (l_wacht,))
    eis(r["status"] == "afgewezen" and r["triage_reden"].startswith("onstaafbaar"),
        f"niets_gevonden → afgewezen, onstaafbaar ({r['triage_reden']})")

    print("6. Reputatie")
    conn = sqlite3.connect(tmp)
    for i in range(5):
        conn.execute("INSERT INTO leads (soort, claim, status, triage_reden, ingezonden_ip_hash) "
                     "VALUES ('tip', ?, 'afgewezen', 'onstaafbaar: test', 'ip-spam')", (f"s{i}",))
    conn.commit()
    conn.close()
    l_spam = lead(tmp, d_["name"], "Iets Anders BV", ip="ip-spam")
    plan = lead_triage.schiften(lead_triage.db(tmp))
    eis(any(lid == l_spam and "onstaafbare" in reden for lid, reden in plan["wachten"]),
        "inzender met vijf onstaafbare en geen gestaafde tips wacht")

    print("7. Droogloop")
    n = rij(tmp, "SELECT COUNT(*) n FROM edit_log")["n"]
    uit = lead_triage.draai(db_pad=tmp, droog=True)
    eis(uit["gestart"] and rij(tmp, "SELECT COUNT(*) n FROM edit_log")["n"] == n,
        "droog schrijft niets")

    print("\nAlles groen.")


if __name__ == "__main__":
    main()
