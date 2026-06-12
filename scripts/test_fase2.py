#!/usr/bin/env python3
"""
End-to-end-test fase 2 (verbeterplan M2.1–M2.6) op een verse fixture-DB.

Dekt de klaar-wanneer-criteria:
  M2.1  elke mutatie herleidbaar; zelf-verificatie technisch onmogelijk; filterrollen
  M2.2  een voorstel telt pas mee na merge; score-diff-preview vooraf
  M2.3  een nieuw theorie-element ontstaat alleen via een RfC (2 menselijke reviewers;
        agent-oordeel telt nooit)
  M2.4  duplicaat gesignaleerd bij indienen; recent-changes-feed + watchlist; rate limit
  M2.5  ratings (nooit eigen werk; agent = advies)
  M2.6  één samenvoeging en één splitsing end-to-end via het voorstelpad, met lege
        hertriage-restlijst, werkende oude id's (lineage) en herberekende scores
        zonder dubbeltelling

Gebruik: python3 scripts/test_fase2.py   (exit-code 0 = alles groen)
"""
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import auth  # noqa: E402
import server  # noqa: E402
import validation  # noqa: E402


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


def fixture_db(pad):
    conn = sqlite3.connect(pad)
    conn.executescript((ROOT / "schema.sql").read_text())
    conn.execute("INSERT INTO entities (id, name, type) VALUES (1, 'F2-Holding', 'bedrijf')")
    conn.execute("INSERT INTO entities (id, name, type) "
                 "VALUES (2, 'F2-Krant', 'mediaorganisatie')")
    # R1 hangt aan mechanisme 1 (eigendomsconcentratie, filter eigendom),
    # R2 aan mechanisme 2 (transnationale_elite_verwevenheid).
    conn.execute("""INSERT INTO relations (id, source_id, target_id, relation_type,
                    mechanism_id, certainty, influence) VALUES (1, 1, 2, 'eigendom', 1, 0.8, 0.5)""")
    conn.execute("""INSERT INTO relations (id, source_id, target_id, relation_type,
                    mechanism_id, certainty, influence) VALUES (2, 2, 1, 'bron_van', 2, 0.6, 0.3)""")
    conn.execute("INSERT INTO instantiations (id, mechanism_id, relation_id, exemplarity) "
                 "VALUES (1, 1, 1, 0.9)")
    conn.execute("""INSERT INTO sources (id, title, source_type, reliability, cluster_key)
                    VALUES (1, 'F2-Bron', 'rapport', 'institutioneel', 'f2')""")
    # Literatuurargument op mechanisme 1 (voor de merge-herbevestiging)
    conn.execute("""INSERT INTO arguments (id, mechanism_id, stance, claim, weight, status,
                    contributed_by) VALUES (901, 1, 'supporting', 'M1-literatuur', 0.8,
                    'ongecontroleerd', 'baas')""")
    conn.execute("INSERT INTO citations (argument_id, source_id) VALUES (901, 1)")

    tokens = {}
    for naam, kind, rol, prov in (("baas", "mens", "maintainer", None),
                                  ("r1", "mens", "reviewer", None),
                                  ("r2", "mens", "reviewer", None),
                                  ("bij", "mens", "bijdrager", None),
                                  ("bot", "agent", "bijdrager", "claude-fable-5 (test)")):
        tokens[naam] = auth.new_token()
        conn.execute("INSERT INTO users (username, kind, role, token_hash, provenance)"
                     " VALUES (?, ?, ?, ?, ?)",
                     (naam, kind, rol, auth.hash_token(tokens[naam]), prov))
    # M2.1: filterrol — bij is reviewer voor alleen 'eigendom'
    conn.execute("""INSERT INTO user_filter_rollen (user_id, filter, rol)
                    SELECT id, 'eigendom', 'reviewer' FROM users WHERE username = 'bij'""")
    conn.commit()
    conn.close()
    return tokens


def main():
    tmp = Path(tempfile.mkdtemp()) / "fase2.db"
    tokens = fixture_db(tmp)
    server.DB_PATH = tmp
    server._rate_emmers.clear()
    c = server.app.test_client()
    kop = {n: {"Authorization": f"Bearer {t}"} for n, t in tokens.items()}

    print("1. M2.2 — voorstel-workflow: landen, niet meetellen, score-diff, merge")
    r = c.post("/api/arguments", headers=kop["bij"], json={
        "relation_id": 1, "stance": "supporting", "claim": "R1 blijkt uit het jaarverslag."})
    a = r.get_json()
    eis(r.status_code == 201 and a["status"] == "voorgesteld",
        f"argument landt als 'voorgesteld' ({a.get('status')})")
    arg1 = a["id"]
    s = c.get("/api/scores").get_json()
    eis(s["relations_detail"]["1"]["bron"] == "prior",
        "voorgesteld argument telt niet mee (R1 blijft op de prior)")
    r = c.get(f"/api/arguments/{arg1}/score_diff")
    d = r.get_json()
    eis(r.status_code == 200 and d["doelstatus"] == "bronvermelding_nodig"
        and any(x["categorie"] == "relatie" and x["id"] == "1" or x["id"] == 1
                for x in d["diff"]),
        "score-diff-preview toont de merge-impact vooraf")
    r = c.patch(f"/api/arguments/{arg1}/status", headers=kop["r1"],
                json={"status": "geverifieerd"})
    eis(r.status_code == 400, f"voorgesteld → geverifieerd kan niet zonder merge ({r.status_code})")
    r = c.post(f"/api/arguments/{arg1}/merge", headers=kop["bot"])
    eis(r.status_code == 403, f"agent (bijdrager) mag niet mergen ({r.status_code})")
    r = c.post(f"/api/arguments/{arg1}/merge", headers=kop["bij"])
    j = r.get_json()
    eis(r.status_code == 200 and j["status"] == "bronvermelding_nodig",
        "M2.1: filterrol (bij = reviewer voor 'eigendom') mag deze merge; "
        "citatiepoort geldt op het merge-moment")
    eis(j["self_merged"] is True, "zelf-merge wordt gevlagd (auteur = merger)")
    s = c.get("/api/scores").get_json()
    eis(s["relations_detail"]["1"]["bron"] == "bewijs", "na merge telt het argument mee")

    print("2. M2.1 — zelf-verificatie technisch onmogelijk")
    r = c.post("/api/citations", headers=kop["bij"],
               json={"argument_id": arg1, "source_id": 1, "quote": "p. 12"})
    eis(r.status_code == 201 and r.get_json()["argument_status"] == "ongecontroleerd",
        "citatie promoveert bronvermelding_nodig → ongecontroleerd")
    r = c.patch(f"/api/arguments/{arg1}/status", headers=kop["bij"],
                json={"status": "geverifieerd"})
    eis(r.status_code == 403, f"auteur kan eigen werk niet verifiëren ({r.status_code})")
    r = c.patch(f"/api/arguments/{arg1}/status", headers=kop["r1"],
                json={"status": "geverifieerd"})
    eis(r.status_code == 200, "een ánder verifieert wel")

    print("3. M2.4 — duplicaatdetectie")
    r = c.post("/api/arguments", headers=kop["bij"], json={
        "relation_id": 1, "stance": "supporting", "claim": "R1 blijkt uit het jaarverslag!"})
    eis(r.status_code == 409 and r.get_json().get("duplicaat_kandidaten"),
        "vrijwel identieke claim wordt gesignaleerd (409 + kandidaten)")
    r = c.post("/api/arguments", headers=kop["bij"], json={
        "relation_id": 1, "stance": "supporting", "claim": "R1 blijkt uit het jaarverslag!",
        "negeer_duplicaten": True})
    eis(r.status_code == 201, "negeer_duplicaten dient alsnog in")
    arg_dup = r.get_json()["id"]

    print("4. M2.5 — ratings: nooit eigen werk; agent = advies")
    r = c.post(f"/api/arguments/{arg1}/ratings", headers=kop["bij"],
               json={"oordeel": "nuttig"})
    eis(r.status_code == 403, "eigen werk raten kan niet")
    r = c.post(f"/api/arguments/{arg1}/ratings", headers=kop["r1"],
               json={"oordeel": "nuttig", "reden": "sterke_onderbouwing"})
    eis(r.status_code == 201, "menselijke rating geaccepteerd")
    r = c.post(f"/api/arguments/{arg1}/ratings", headers=kop["bot"],
               json={"oordeel": "nuttig"})
    eis(r.status_code == 201 and r.get_json()["advies"] is True,
        "agent-rating is zichtbaar advies")
    t = c.get(f"/api/arguments/{arg1}/ratings").get_json()["telling"]
    eis(t["mens"]["nuttig"] == 1 and t["agent"]["nuttig"] == 1,
        "telling splitst mens en agent")

    print("5. M2.4 — watchlist + recent-changes-feed")
    r = c.post("/api/watchlist", headers=kop["r2"],
               json={"table_name": "relations", "record_id": 1})
    eis(r.status_code == 201, "relatie 1 op de watchlist")
    feed = c.get("/api/recent_changes?watchlist=1", headers=kop["r2"]).get_json()
    eis(any(f["table_name"] == "arguments" and f["record_id"] == arg1 for f in feed),
        "watchlist-feed vangt argumenten op het gevolgde doel")
    eis(c.get("/api/recent_changes").status_code == 200, "feed is open leesbaar")

    print("6. M2.3 — theory-RfC: sjabloon + twee menselijke reviewers")
    r = c.post("/api/roles", headers=kop["baas"], json={"name": "x"})
    eis(r.status_code == 403, "directe theorie-POST is dicht (alleen nog RfC)")
    r = c.post("/api/voorstellen", headers=kop["baas"], json={
        "soort": "nieuw_theorie_element", "titel": "Rol: testwaakhond",
        "payload": {"element_type": "rol", "naam": "testwaakhond"}})
    eis(r.status_code == 400 and len(r.get_json()["fouten"]) >= 3,
        "onvolledig RfC-sjabloon wordt geweigerd met foutenlijst")
    rfc = {"element_type": "rol", "naam": "testwaakhond", "categorie": "tegenmacht",
           "definitie": "Institutionele waakhond die mediamacht doorlicht.",
           "afgrenzing": "Anders dan toezichthouder: geen formele bevoegdheid.",
           "falsificatiecriterium": "Geen aantoonbare doorlichtingscasussen.",
           "instantiaties": ["F2-Krant als casus"], "bronnen": ["F2-Bron"]}
    r = c.post("/api/voorstellen", headers=kop["baas"], json={
        "soort": "nieuw_theorie_element", "titel": "Rol: testwaakhond", "payload": rfc})
    eis(r.status_code == 201 and r.get_json()["benodigde_akkoorden"] == 2,
        "volledig RfC ingediend; theorielaag vergt 2 akkoorden")
    vid = r.get_json()["id"]
    r = c.post(f"/api/voorstellen/{vid}/reviews", headers=kop["bot"],
               json={"oordeel": "akkoord"})
    eis(r.status_code == 200 and r.get_json()["besluit"] == "open",
        "agent-akkoord telt nooit mee (advies)")
    r = c.post(f"/api/voorstellen/{vid}/reviews", headers=kop["baas"],
               json={"oordeel": "akkoord"})
    eis(r.get_json()["besluit"] == "open", "indiener-akkoord telt niet op de theorielaag")
    r = c.post(f"/api/voorstellen/{vid}/reviews", headers=kop["r1"],
               json={"oordeel": "akkoord"})
    eis(r.get_json()["besluit"] == "open", "één menselijke reviewer is niet genoeg (1/2)")
    r = c.post(f"/api/voorstellen/{vid}/reviews", headers=kop["r2"],
               json={"oordeel": "akkoord"})
    j = r.get_json()
    eis(j["besluit"] == "geaccepteerd", "tweede akkoord accepteert en voert uit")
    rol_id = j["resultaat"]["id"]
    conn = sqlite3.connect(tmp)
    eis(conn.execute("SELECT name FROM roles WHERE id = ?", (rol_id,)).fetchone()[0]
        == "testwaakhond", "rol bestaat na acceptatie")
    conn.close()

    print("7. M2.6 — samenvoegen via het voorstelpad (herbevestiging, lineage)")
    samen = {"element_type": "mechanisme", "oud_ids": [1, 2],
             "doel": {"naam": "f2_fusiemechanisme", "definitie": "Samengevoegd testmechanisme.",
                      "filter": "eigendom", "effect": "Testeffect.", "aard": "direct"},
             "motivatie": "Vrijwel identieke bron- en argumentverzamelingen (test).",
             "herbevestigd": {"argumenten": [901], "relaties": [1],
                              "instantiaties": [1], "padclaims": []}}
    r = c.post("/api/voorstellen", headers=kop["baas"], json={
        "soort": "samenvoegen", "titel": "Fusie mechanisme 1+2", "payload": samen})
    eis(r.status_code == 201, f"samenvoegvoorstel ingediend ({r.status_code}: {r.get_json()})")
    vid = r.get_json()["id"]
    for wie in ("r1", "r2"):
        r = c.post(f"/api/voorstellen/{vid}/reviews", headers=kop[wie],
                   json={"oordeel": "akkoord"})
    j = r.get_json()
    eis(j["besluit"] == "geaccepteerd", f"samenvoeging geaccepteerd ({j.get('besluit')})")
    fusie_id = j["resultaat"]["nieuw_id"]
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    eis(all(conn.execute("SELECT vervangen FROM mechanisms WHERE id = ?", (m,)).fetchone()[0]
            for m in (1, 2)), "oude mechanismen staan op vervangen (niets gewist)")
    eis(conn.execute("SELECT mechanism_id FROM relations WHERE id = 1").fetchone()[0] == fusie_id,
        "herbevestigde relatie verhuist naar de opvolger")
    eis(conn.execute("SELECT mechanism_id FROM relations WHERE id = 2").fetchone()[0] == 2,
        "niet-herbevestigd bewijs blijft bij het vervangen element (geen bewijs-witwassen)")
    eis(conn.execute("SELECT COUNT(*) FROM lineage WHERE element_type = 'mechanisme' "
                     "AND nieuw_id = ?", (fusie_id,)).fetchone()[0] == 2,
        "lineage: twee opvolgingsrijen")
    conn.close()
    r = c.get("/api/lineage/mechanisme/1").get_json()
    eis(r["vervangen"] and r["opvolgers"][0]["id"] == fusie_id,
        "oud id #1 verwijst naar de opvolger (API)")
    s = c.get("/api/scores").get_json()
    eis(str(fusie_id) in {str(k) for k in s["mechanisms"]}
        and "1" not in {str(k) for k in s["mechanisms"]},
        "scores: opvolger telt, vervangen mechanisme niet (geen dubbeltelling)")

    print("8. M2.6 — splitsen: restlijst-poort, dan end-to-end")
    nieuwe = [{"naam": "f2_split_a", "definitie": "Deel A.", "filter": "eigendom",
               "effect": "Effect A.", "aard": "direct"},
              {"naam": "f2_split_b", "definitie": "Deel B.", "filter": "eigendom",
               "effect": "Effect B.", "aard": "direct"}]
    onvolledig = {"element_type": "mechanisme", "oud_id": fusie_id, "nieuwe": nieuwe,
                  "motivatie": "Vermengt eigendom en redactie (test).",
                  "toewijzing": {"argumenten": {}, "relaties": {}, "instantiaties": {},
                                 "padclaims": {}}}
    r = c.post("/api/voorstellen", headers=kop["baas"], json={
        "soort": "splitsen", "titel": "Split fusiemechanisme (onvolledig)",
        "payload": onvolledig})
    vid = r.get_json()["id"]
    c.post(f"/api/voorstellen/{vid}/reviews", headers=kop["r1"], json={"oordeel": "akkoord"})
    r = c.post(f"/api/voorstellen/{vid}/reviews", headers=kop["r2"], json={"oordeel": "akkoord"})
    eis(r.status_code == 409 and "restlijst" in r.get_json()["blokkade"],
        "onvolledige hertriage blokkeert de uitvoering (voorstel blijft open)")
    r = c.post(f"/api/voorstellen/{vid}/intrekken", headers=kop["baas"])
    eis(r.status_code == 200, "onvolledig voorstel ingetrokken")

    conn = sqlite3.connect(tmp)
    inst_id = conn.execute("SELECT id FROM instantiations WHERE mechanism_id = ?",
                           (fusie_id,)).fetchone()[0]
    conn.close()
    volledig = dict(onvolledig)
    volledig["toewijzing"] = {"argumenten": {"901": [0, 1]}, "relaties": {"1": [0]},
                              "instantiaties": {str(inst_id): [0]}, "padclaims": {}}
    r = c.post("/api/voorstellen", headers=kop["baas"], json={
        "soort": "splitsen", "titel": "Split fusiemechanisme", "payload": volledig})
    vid = r.get_json()["id"]
    c.post(f"/api/voorstellen/{vid}/reviews", headers=kop["r1"], json={"oordeel": "akkoord"})
    r = c.post(f"/api/voorstellen/{vid}/reviews", headers=kop["r2"], json={"oordeel": "akkoord"})
    j = r.get_json()
    eis(j["besluit"] == "geaccepteerd", f"volledige splitsing geaccepteerd ({j.get('besluit')})")
    a_id, b_id = j["resultaat"]["nieuw_ids"]
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    eis(conn.execute("SELECT vervangen FROM mechanisms WHERE id = ?",
                     (fusie_id,)).fetchone()[0] == 1, "gesplitst element staat op vervangen")
    eis(conn.execute("SELECT COUNT(*) FROM arguments WHERE mechanism_id = ?",
                     (b_id,)).fetchone()[0] == 1,
        "argument 901 is gedupliceerd naar opvolger B (één-op-veel = dupliceren)")
    eis(conn.execute("SELECT mechanism_id FROM relations WHERE id = 1").fetchone()[0] == a_id,
        "relatie 1 toegewezen aan opvolger A")
    rapport = validation.run_all(conn)
    fase2_fouten = [b for b in rapport["bevindingen"]
                    if b["code"] in ("LINEAGE-VOORSTEL", "VERVANGEN-LINEAGE",
                                     "PADCLAIM-VERVANGEN") and b["aantal"]]
    eis(not fase2_fouten, f"validator: lineage/vervangen-checks groen ({fase2_fouten})")
    conn.close()

    print("9. M2.4 — rate limit per account")
    oud = dict(server.RATE_LIMITS)
    server.RATE_LIMITS["bijdrager"] = 1
    r = c.post("/api/arguments", headers=kop["bij"], json={
        "relation_id": 2, "stance": "contextual", "claim": "Rate-limit-test."})
    eis(r.status_code == 429, f"boven de limiet → 429 ({r.status_code})")
    server.RATE_LIMITS.update(oud)
    server._rate_emmers.clear()

    print("Fase 2: alles groen.")


if __name__ == "__main__":
    main()
