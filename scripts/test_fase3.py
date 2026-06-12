#!/usr/bin/env python3
"""
End-to-end-test fase 3 (verbeterplan M3.1–M3.4) op een verse fixture-DB.

Dekt de bouwbare klaar-wanneer-criteria:
  M3.1  twee releases met een leesbare score-diff (snapshot + changelog);
        releases zijn onveranderlijk
  M3.2  de onderzoeksagenda rangschikt belang × bewijsarmoede en levert
        red-team-doelwitten (M3.3)
  M3.4  voorspellingen: vastleggen vóór de uitkomst (deadline in de toekomst,
        theorie-anker verplicht), scoren door een reviewer (Brier), zelf
        scoren gevlagd, gescoord = onveranderlijk; validator-checks

De inhoudelijke criteria (echte adversarial ronde, gescoorde echte
voorspelling, audit 2027) zijn bijdrage-/eigenaarswerk en blijven open in §9.

Gebruik: python3 scripts/test_fase3.py   (exit-code 0 = alles groen)
"""
import importlib.util
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import auth  # noqa: E402
import scoring  # noqa: E402
import server  # noqa: E402
import validation  # noqa: E402


def laad_script(naam):
    spec = importlib.util.spec_from_file_location(naam, ROOT / "scripts" / f"{naam}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


def fixture_db(pad):
    conn = sqlite3.connect(pad)
    conn.executescript((ROOT / "schema.sql").read_text())
    conn.execute("INSERT INTO entities (id, name, type) VALUES (1, 'F3-Holding', 'bedrijf')")
    conn.execute("INSERT INTO entities (id, name, type) "
                 "VALUES (2, 'F3-Krant', 'mediaorganisatie')")
    conn.execute("""INSERT INTO relations (id, source_id, target_id, relation_type,
                    mechanism_id, certainty, influence) VALUES (1, 1, 2, 'eigendom', 1, 0.8, 0.7)""")
    conn.execute("INSERT INTO instantiations (id, mechanism_id, relation_id, exemplarity) "
                 "VALUES (1, 1, 1, 0.9)")
    conn.execute("""INSERT INTO sources (id, title, source_type, reliability, cluster_key)
                    VALUES (1, 'F3-Bron', 'rapport', 'institutioneel', 'f3')""")
    tokens = {}
    for naam, kind, rol in (("baas", "mens", "maintainer"), ("r1", "mens", "reviewer"),
                            ("bij", "mens", "bijdrager")):
        tokens[naam] = auth.new_token()
        conn.execute("INSERT INTO users (username, kind, role, token_hash) VALUES (?, ?, ?, ?)",
                     (naam, kind, rol, auth.hash_token(tokens[naam])))
    conn.commit()
    conn.close()
    return tokens


def main():
    tmpdir = Path(tempfile.mkdtemp())
    tmp = tmpdir / "fase3.db"
    tokens = fixture_db(tmp)
    server.DB_PATH = tmp
    server._rate_emmers.clear()
    c = server.app.test_client()
    kop = {n: {"Authorization": f"Bearer {t}"} for n, t in tokens.items()}

    print("1. M3.4 — voorspellingsregister: poorten en vastlegging vooraf")
    geldig = {"claim": "F3-Krant brengt in 2027 meetbaar minder follow-up bij "
                       "berichtgeving die F3-Holding raakt.",
              "afleiding": "Volgt uit eigendomsconcentratie (mechanisme 1).",
              "meetcriterium": "Telling vervolgstukken in een steekproefmaand.",
              "kans": 0.7, "deadline": "2099-01-01", "mechanism_id": 1}
    r = c.post("/api/predictions", json=geldig)
    eis(r.status_code == 401, f"anoniem vastleggen kan niet ({r.status_code})")
    r = c.post("/api/predictions", headers=kop["bij"], json={"claim": "x"})
    eis(r.status_code == 400 and len(r.get_json()["fouten"]) >= 4,
        "onvolledige voorspelling geweigerd met foutenlijst")
    r = c.post("/api/predictions", headers=kop["bij"],
               json={**geldig, "deadline": "2020-01-01"})
    eis(r.status_code == 400, "deadline in het verleden geweigerd (vooraf vastleggen!)")
    r = c.post("/api/predictions", headers=kop["bij"],
               json={**geldig, "mechanism_id": 999})
    eis(r.status_code == 400, "onbestaand theorie-anker geweigerd")
    r = c.post("/api/predictions", headers=kop["bij"], json=geldig)
    p = r.get_json()
    eis(r.status_code == 201 and p["status"] == "open" and p["contributed_by"] == "bij",
        "geldige voorspelling landt open, met attributie")
    pid = p["id"]
    open_lijst = c.get("/api/predictions?status=open").get_json()
    eis(any(x["id"] == pid for x in open_lijst), "register is open leesbaar (filter werkt)")

    print("2. M3.4 — scoren: reviewer, Brier, onveranderlijk, zelf-scoren gevlagd")
    r = c.patch(f"/api/predictions/{pid}/uitkomst", headers=kop["bij"],
                json={"status": "niet_uitgekomen", "uitkomst": "x"})
    eis(r.status_code == 403, "bijdrager mag niet scoren (reviewer-poort)")
    r = c.patch(f"/api/predictions/{pid}/uitkomst", headers=kop["r1"],
                json={"status": "kapot", "uitkomst": "x"})
    eis(r.status_code == 400, "ongeldige eindstatus geweigerd")
    r = c.patch(f"/api/predictions/{pid}/uitkomst", headers=kop["r1"],
                json={"status": "niet_uitgekomen",
                      "uitkomst": "Geen meetbaar verschil gevonden (testbron)."})
    j = r.get_json()
    eis(r.status_code == 200 and abs(j["brier"] - 0.49) < 1e-9 and not j["self_scored"],
        "reviewer scoort; Brier = kans² bij niet_uitgekomen; geen zelf-vlag")
    r = c.patch(f"/api/predictions/{pid}/uitkomst", headers=kop["baas"],
                json={"status": "uitgekomen", "uitkomst": "x"})
    eis(r.status_code == 409, "gescoorde voorspelling is onveranderlijk (409)")
    r = c.post("/api/predictions", headers=kop["r1"],
               json={**geldig, "kans": 0.6, "role_id": 1, "mechanism_id": None,
                     "claim": "Tweede testvoorspelling (rol-anker)."})
    pid2 = r.get_json()["id"]
    r = c.patch(f"/api/predictions/{pid2}/uitkomst", headers=kop["r1"],
                json={"status": "uitgekomen", "uitkomst": "x (zelf gescoord, test)"})
    j = r.get_json()
    eis(j["self_scored"] is True and abs(j["brier"] - 0.16) < 1e-9,
        "zelf scoren mag maar wordt gevlagd; Brier = (kans−1)² bij uitgekomen")

    print("3. M3.4 — validator-checks en kerngetallen")
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    conn.execute("""INSERT INTO predictions (claim, afleiding, meetcriterium, kans,
                    deadline, mechanism_id, contributed_by)
                    VALUES ('verlopen testvoorspelling', 'x', 'x', 0.5,
                            '2020-01-01', 1, 'bij')""")  # validatortest: kan via de
    conn.commit()                                        # API niet meer ontstaan
    bevindingen = {b["code"]: b for b in validation.check_fase3(conn)}
    eis(bevindingen["VOORSPELLING-DEADLINE"]["aantal"] == 1,
        "validator vlagt open voorspelling voorbij de deadline")
    eis(bevindingen["VOORSPELLING-ZELF"]["aantal"] == 1,
        "validator toont de heraudit-lijst van zelf gescoorde uitkomsten")
    k = validation.kerngetallen(conn)
    eis(k["voorspellingen_open"] == 1 and k["voorspellingen_gescoord"] == 2
        and abs(k["voorspellingen_brier_gem"] - 0.325) < 1e-9,
        "kerngetallen tellen het register mee (gem. Brier)")

    print("4. M3.2 — onderzoeksagenda + red-team-doelwitten (M3.3)")
    agenda_mod = laad_script("onderzoeksagenda")
    scores = scoring.compute_all_scores(conn)
    agenda = agenda_mod.bouw_agenda(conn, scores)
    eis(agenda and all(agenda[i]["prioriteit"] >= agenda[i + 1]["prioriteit"]
                       for i in range(len(agenda) - 1)),
        "agenda is gevuld en gesorteerd op prioriteit (belang × bewijsarmoede)")
    eis(all("ontbreekt" in a for a in agenda),
        "elk agendapunt benoemt de concrete bewijsgaten")
    redteam = agenda_mod.bouw_redteam(conn, scores)
    eis(redteam and redteam[0]["relatie_id"] == 1 and "n_tegen" in redteam[0],
        "red-team-doelwitten: invloedrijkste edge bovenaan, met stance-balans")
    conn.close()

    print("5. M3.1 — twee releases met leesbare score-diff")
    release_mod = laad_script("release_model")
    rdir = tmpdir / "releases"
    release_mod.DB_PATH = tmp  # naam-lookups in maak_snapshot volgen de fixture
    snap1, _ = release_mod.release("0.1.0", "eerste testrelease",
                                   db_path=tmp, releases_dir=rdir)
    eis((rdir / "model-v0.1.0.json").exists() and (rdir / "model-v0.1.0.md").exists(),
        "release 1: snapshot + changelog geschreven")
    eis(snap1["scores"]["relaties"]["1"]["geloofwaardigheid"] > 0,
        "snapshot bevat de gescoorde relaties")
    try:
        release_mod.release("0.1.0", "dubbel", db_path=tmp, releases_dir=rdir)
        sys.exit("FAAL: release 0.1.0 mocht niet twee keer")
    except SystemExit as e:
        eis("onveranderlijk" in str(e), "releases zijn onveranderlijk")
    # Verschuif een score via het bijdragepad (argument + citatie + merge), dan release 2
    r = c.post("/api/arguments", headers=kop["bij"], json={
        "relation_id": 1, "stance": "supporting",
        "claim": "Eigendomsrelatie blijkt uit het F3-jaarverslag.",
        "citations": [{"source_id": 1, "quote": "p. 3"}]})
    arg_id = r.get_json()["id"]
    r = c.post(f"/api/arguments/{arg_id}/merge", headers=kop["r1"])
    eis(r.status_code == 200, "score-verschuiving aangebracht via het bijdragepad")
    snap2, diff = release_mod.release("0.2.0", "tweede testrelease",
                                      db_path=tmp, releases_dir=rdir)
    verschoven = diff["relaties"]["verschoven"]
    eis(any(v["id"] == 1 for v in verschoven),
        "score-diff toont de verschuiving van relatie 1")
    md = (rdir / "model-v0.2.0.md").read_text()
    eis("→" in md and "v0.1.0" in md, "changelog is leesbaar en verwijst naar de vorige release")
    eis(release_mod.vorige_release(rdir, "0.2.0")["versie"] == "0.1.0",
        "vorige-release-resolutie volgt semver")

    print("Fase 3: alles groen.")


if __name__ == "__main__":
    main()
