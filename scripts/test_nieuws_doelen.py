#!/usr/bin/env python3
"""
End-to-end-test van de nieuws-wachtrij `nieuws_doelen` (Epic 12 "Wie is dit?", story 12.1):
de migratie (idempotent, DDL == schema.sql), de REST-endpoints (upsert/409/opnieuw,
lijst + filters, claim_volgende atomair + verlopen claim, claim, PATCH-validatie), de
poorten per account (nieuws-agent / nieuws-scout / maintainer / overige) en de
rate-limit-vrijstelling van de wachtrij-endpoints.

Bouwt een verse database in een tijdelijke map (schema.sql). De live database wordt
NOOIT aangeraakt.

Gebruik: python3 scripts/test_nieuws_doelen.py
Exit-code 0 = alles groen.
"""
import datetime
import importlib.util
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def laad_script(naam):
    spec = importlib.util.spec_from_file_location(naam, ROOT / "scripts" / f"{naam}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


def test_migratie(tmp):
    print("1. Migratie scripts/migrate_add_nieuws_doelen.py")
    import validation
    migr = laad_script("migrate_add_nieuws_doelen")
    db = Path(tmp) / "oud.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE)")
    conn.commit()
    conn.close()
    eerste = migr.migreer(db)
    eis(eerste == ["tabel nieuws_doelen", "index idx_nieuws_doelen_status"],
        f"eerste run legt tabel + index aan ({eerste})")
    eis(migr.migreer(db) == [], "tweede run is een no-op (idempotent)")
    backup = migr.backup(db)
    backup2 = migr.backup(db)
    eis(backup.exists() and backup2.exists() and backup != backup2
        and backup.name.startswith("propaganda_model_backup_"),
        "backup-then-migrate: backup-bestand, nooit overschreven binnen dezelfde seconde")
    live = sqlite3.connect(db)
    ddl_live = live.execute("SELECT sql FROM sqlite_master WHERE name = 'nieuws_doelen'"
                            ).fetchone()[0]
    live.close()
    vers = sqlite3.connect(":memory:")
    vers.executescript((ROOT / "schema.sql").read_text())
    ddl_schema = vers.execute("SELECT sql FROM sqlite_master WHERE name = 'nieuws_doelen'"
                              ).fetchone()[0]
    vers.close()
    eis(validation._normaliseer_ddl(ddl_live) == validation._normaliseer_ddl(ddl_schema),
        "migratie-DDL == schema.sql-DDL (schema-pariteit)")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        test_migratie(tmp)

        db = Path(tmp) / "vers.db"
        print("2. Verse build (schema.sql)")
        init = laad_script("init_db")
        init.DB_PATH = db
        init.init_db()

        import auth
        import server
        server.DB_PATH = db
        server._rate_emmers.clear()

        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        tokens = {}
        for naam, rol in (("nieuws-agent", "bijdrager"), ("nieuws-scout", "bijdrager"),
                          ("nieuws-autokeur", "reviewer"), ("t-ander", "bijdrager"),
                          ("t-admin", "maintainer")):
            tokens[naam] = auth.new_token()
            conn.execute("INSERT INTO users (username, kind, role, provenance, token_hash)"
                         " VALUES (?, 'agent', ?, 'test', ?)",
                         (naam, rol, auth.hash_token(tokens[naam])))
        ent = conn.execute("INSERT INTO entities (name, type, status) VALUES "
                           "('Test Gemeente', 'overheidsinstelling', 'goedgekeurd')").lastrowid
        conn.commit()
        conn.close()

        client = server.app.test_client()
        kop = {n: {"Authorization": f"Bearer {t}"} for n, t in tokens.items()}

        def doel_body(sleutel, prio=50.0, **extra):
            b = {"sleutel": sleutel, "naam": sleutel.split(":")[1].replace("-", " ").title(),
                 "soort": "persoon", "rol_categorie": "politicus",
                 "rol_hint": "wethouder Dijkerhoven",
                 "context": {"events": [{"titel": "Raadsdebat", "url": "https://x.test/e"}],
                             "artikelen": [], "organisaties": ["NordVind"],
                             "rolzinnen": ["Wethouder zegt ..."]},
                 "prioriteit": prio}
            b.update(extra)
            return b

        print("3. Upsert — poorten per account")
        r = client.post("/api/nieuws/doelen", json=doel_body("person:anouk-verbeek"))
        eis(r.status_code == 401, f"zonder token → 401 ({r.status_code})")
        for naam in ("t-ander", "nieuws-scout", "nieuws-autokeur"):
            r = client.post("/api/nieuws/doelen", json=doel_body("person:anouk-verbeek"),
                            headers=kop[naam])
            eis(r.status_code == 403, f"{naam} mag geen doelen in de rij zetten ({r.status_code})")
        r = client.post("/api/nieuws/doelen", json=doel_body("person:anouk-verbeek", 95.0),
                        headers=kop["nieuws-agent"])
        j = r.get_json()
        eis(r.status_code == 201 and j["doel"]["status"] == "open"
            and j["doel"]["aangevraagd_door"] == "nieuws-agent" and j["doel"]["pogingen"] == 0
            and isinstance(j["doel"]["context"], dict) and j["doel"]["resultaat"] is None,
            f"nieuws-agent: nieuw doel → 201 {{doel}} (open, context als object)")
        anouk = j["doel"]["id"]
        r = client.post("/api/nieuws/doelen", json=doel_body("org:nordvind", 60.0,
                                                             soort="organisatie",
                                                             rol_categorie="organisatie"),
                        headers=kop["t-admin"])
        eis(r.status_code == 201, f"maintainer mag ook in de rij zetten ({r.status_code})")
        nordvind = r.get_json()["doel"]["id"]

        print("4. Upsert — validatie")
        gevallen = [
            ({"naam": "X", "soort": "persoon"}, "sleutel ontbreekt"),
            ({"sleutel": "person:x", "soort": "persoon"}, "naam ontbreekt"),
            ({"sleutel": "person:x", "naam": "X", "soort": "bedrijf"}, "ongeldige soort"),
            ({"sleutel": "person:x", "naam": "X"}, "nieuw doel zonder soort"),
            ({"sleutel": "person:henk", "naam": "Henk (61)", "soort": "persoon",
              "rol_categorie": "prive"}, "privépersoon wordt geweigerd"),
            ({"sleutel": "person:x", "naam": "X", "soort": "persoon", "context": ["a"]},
             "context geen object"),
            ({"sleutel": "person:x", "naam": "X", "soort": "persoon", "prioriteit": "hoog"},
             "prioriteit geen getal"),
            ({"sleutel": "person:x", "naam": "X", "soort": "persoon", "entity_id": 999999},
             "entity_id bestaat niet"),
        ]
        for body, label in gevallen:
            r = client.post("/api/nieuws/doelen", json=body, headers=kop["nieuws-agent"])
            eis(r.status_code == 400, f"{label} → 400 ({r.status_code}: {r.get_json().get('error')})")

        print("5. Upsert — bestaand doel (open/bezig) wordt bijgewerkt")
        conn = sqlite3.connect(db)
        n_log_voor = conn.execute("SELECT COUNT(*) FROM edit_log WHERE table_name = "
                                  "'nieuws_doelen'").fetchone()[0]
        conn.close()
        r = client.post("/api/nieuws/doelen",
                        json=doel_body("person:anouk-verbeek", 40.0, rol_hint="wethouder NordVind",
                                       context={"events": [], "artikelen": [],
                                                "organisaties": ["Gemeente X"],
                                                "rolzinnen": []}, entity_id=ent),
                        headers=kop["nieuws-agent"])
        j = r.get_json()
        eis(r.status_code == 200 and j.get("bijgewerkt") is True and j["doel"]["id"] == anouk,
            f"bestaand open doel → 200 {{doel, bijgewerkt: true}} ({r.status_code})")
        eis(j["doel"]["prioriteit"] == 95.0, "prioriteit = max (lagere nieuwe waarde verlaagt niet)")
        eis(j["doel"]["rol_hint"] == "wethouder NordVind"
            and j["doel"]["context"]["organisaties"] == ["Gemeente X"]
            and j["doel"]["entity_id"] == ent, "rol/context/entity_id bijgewerkt")
        r = client.post("/api/nieuws/doelen", json=doel_body("person:anouk-verbeek", 99.5),
                        headers=kop["nieuws-agent"])
        eis(r.get_json()["doel"]["prioriteit"] == 99.5, "hogere prioriteit wint")
        conn = sqlite3.connect(db)
        n_log_na = conn.execute("SELECT COUNT(*) FROM edit_log WHERE table_name = "
                                "'nieuws_doelen'").fetchone()[0]
        conn.close()
        eis(n_log_na == n_log_voor, "gewone verversing logt niet in edit_log (geen ruis)")

        print("6. Rate limit: wachtrij-endpoints vrij, inhoud houdt de flood-rem")
        server._rate_emmers.clear()
        codes = set()
        for i in range(40):
            r = client.post("/api/nieuws/doelen",
                            json=doel_body(f"person:massa-{i:02d}", float(i % 7)),
                            headers=kop["nieuws-agent"])
            codes.add(r.status_code)
        eis(codes == {201}, f"40 upserts achter elkaar door nieuws-agent → geen 429 ({codes})")
        codes = []
        for _ in range(31):
            codes.append(client.post("/api/entities", json={},
                                     headers=kop["nieuws-agent"]).status_code)
        eis(codes[-1] == 429 and 429 not in codes[:30],
            f"inhouds-endpoint: de 31e schrijfactie → 429 (flood-rem blijft) ({codes[-3:]})")
        server._rate_emmers.clear()

        print("7. Lijst + enkel doel (elk ingelogd account)")
        r = client.get("/api/nieuws/doelen")
        eis(r.status_code == 401, f"lezen zonder login → 401 ({r.status_code})")
        r = client.get("/api/nieuws/doelen?limit=500", headers=kop["t-ander"])
        lijst = r.get_json()["doelen"]
        prios = [d["prioriteit"] for d in lijst]
        eis(r.status_code == 200 and len(lijst) == 42 and prios == sorted(prios, reverse=True),
            f"alle 42 doelen, prioriteit aflopend (eerste: {lijst[0]['sleutel']})")
        r = client.get("/api/nieuws/doelen?limit=5", headers=kop["t-ander"])
        eis(len(r.get_json()["doelen"]) == 5, "limit werkt")
        r = client.get("/api/nieuws/doelen?sleutel=org:nordvind,person:anouk-verbeek",
                       headers=kop["nieuws-scout"])
        eis({d["id"] for d in r.get_json()["doelen"]} == {anouk, nordvind},
            "sleutel-filter (ook komma-lijst)")
        r = client.get("/api/nieuws/doelen?status=open,raar", headers=kop["nieuws-scout"])
        eis(r.status_code == 400, f"onbekende status in filter → 400 ({r.status_code})")
        r = client.get("/api/nieuws/doelen?bijgewerkt_na=gisteren", headers=kop["nieuws-scout"])
        eis(r.status_code == 400, "ongeldige bijgewerkt_na → 400")
        r = client.get(f"/api/nieuws/doelen/{anouk}", headers=kop["nieuws-autokeur"])
        eis(r.status_code == 200 and r.get_json()["doel"]["sleutel"] == "person:anouk-verbeek",
            "GET /api/nieuws/doelen/<id> → {doel}")
        r = client.get("/api/nieuws/doelen/999999", headers=kop["nieuws-scout"])
        eis(r.status_code == 404, "onbekend doel → 404")

        print("8. claim_volgende — poort, volgorde, verlopen claim")
        r = client.post("/api/nieuws/doelen/claim_volgende", headers=kop["nieuws-agent"])
        eis(r.status_code == 403, f"nieuws-agent mag niet claimen ({r.status_code})")
        r = client.post("/api/nieuws/doelen/claim_volgende?limit=2", headers=kop["nieuws-scout"])
        geclaimd = r.get_json()["doelen"]
        eis(r.status_code == 200 and [d["id"] for d in geclaimd] == [anouk, nordvind],
            f"hoogste prioriteit eerst ({[d['sleutel'] for d in geclaimd]})")
        eis(all(d["status"] == "bezig" and d["geclaimd_door"] == "nieuws-scout"
                and d["pogingen"] == 1 and d["geclaimd_op"] for d in geclaimd),
            "geclaimd: status bezig, geclaimd_door/op gezet, pogingen 1")
        r = client.post("/api/nieuws/doelen/claim_volgende?limit=1", headers=kop["nieuws-scout"])
        volgende = r.get_json()["doelen"]
        eis(len(volgende) == 1 and volgende[0]["id"] not in (anouk, nordvind),
            "een tweede claim geeft een ánder (open) doel")
        # Verlopen claim: anouk 4 uur geleden geclaimd → weer claimbaar; nordvind 1 uur → niet.
        conn = sqlite3.connect(db)
        oud = (datetime.datetime.now() - datetime.timedelta(hours=4)).isoformat(timespec="seconds")
        recent = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat(timespec="seconds")
        conn.execute("UPDATE nieuws_doelen SET geclaimd_op = ? WHERE id = ?", (oud, anouk))
        conn.execute("UPDATE nieuws_doelen SET geclaimd_op = ? WHERE id = ?", (recent, nordvind))
        conn.commit()
        conn.close()
        r = client.post("/api/nieuws/doelen/claim_volgende?limit=1", headers=kop["nieuws-scout"])
        d = r.get_json()["doelen"][0]
        eis(d["id"] == anouk and d["pogingen"] == 2,
            "een 'bezig'-doel met een claim > 3 uur telt weer als open (pogingen 2)")

        print("9. claim_volgende — atomair onder gelijktijdigheid")
        conn = sqlite3.connect(db)
        conn.execute("UPDATE nieuws_doelen SET status = 'klaar' WHERE status = 'open'")
        for i in range(6):
            conn.execute("""INSERT INTO nieuws_doelen (sleutel, naam, soort, prioriteit, status,
                            aangemaakt, bijgewerkt) VALUES (?, ?, 'persoon', 10, 'open', ?, ?)""",
                         (f"person:race-{i}", f"Race {i}", "2026-09-30T10:00:00",
                          "2026-09-30T10:00:00"))
        conn.commit()
        conn.close()
        resultaten, fouten = [], []

        def claimer():
            try:
                c = server.app.test_client()
                for _ in range(3):
                    rr = c.post("/api/nieuws/doelen/claim_volgende?limit=1",
                                headers=kop["nieuws-scout"])
                    if rr.status_code != 200:
                        fouten.append(rr.status_code)
                        continue
                    resultaten.extend(x["id"] for x in rr.get_json()["doelen"])
            except Exception as e:  # noqa: BLE001 — test-scaffolding
                fouten.append(repr(e))

        draden = [threading.Thread(target=claimer) for _ in range(6)]
        for t in draden:
            t.start()
        for t in draden:
            t.join()
        eis(not fouten, f"geen fouten tijdens gelijktijdig claimen ({fouten[:3]})")
        eis(len(resultaten) == 6 and len(set(resultaten)) == 6,
            f"6 open doelen, 18 gelijktijdige claims → elk doel precies één keer ({len(resultaten)})")

        print("10. Enkel claimen")
        conn = sqlite3.connect(db)
        conn.execute("""INSERT INTO nieuws_doelen (sleutel, naam, soort, prioriteit, status,
                        aangemaakt, bijgewerkt) VALUES ('person:los', 'Los', 'persoon', 1,
                        'open', '2026-09-30T10:00:00', '2026-09-30T10:00:00')""")
        los = conn.execute("SELECT id FROM nieuws_doelen WHERE sleutel = 'person:los'").fetchone()[0]
        conn.commit()
        conn.close()
        r = client.post(f"/api/nieuws/doelen/{los}/claim", headers=kop["t-ander"])
        eis(r.status_code == 403, f"ander account mag niet claimen ({r.status_code})")
        r = client.post(f"/api/nieuws/doelen/{los}/claim", headers=kop["nieuws-scout"])
        eis(r.status_code == 200 and r.get_json()["doel"]["status"] == "bezig",
            "open → bezig (200)")
        r = client.post(f"/api/nieuws/doelen/{los}/claim", headers=kop["nieuws-scout"])
        eis(r.status_code == 409, f"al bezig → 409 ({r.status_code})")
        r = client.post("/api/nieuws/doelen/999999/claim", headers=kop["nieuws-scout"])
        eis(r.status_code == 404, "onbekend doel → 404")

        print("11. PATCH — poort + validatie")
        r = client.patch(f"/api/nieuws/doelen/{anouk}", json={"status": "klaar"},
                         headers=kop["nieuws-agent"])
        eis(r.status_code == 403, f"nieuws-agent mag niet patchen ({r.status_code})")
        slecht = [
            ({"status": "gedaan"}, "onbekende status"),
            ({"vervolg": "twitter"}, "onbekend vervolg"),
            ({"resultaat": [1, 2]}, "resultaat geen object"),
            ({"resultaat": {"entity_ids": ["a"]}}, "resultaat-lijst met tekst"),
            ({"resultaat": {"ids": [1]}}, "resultaat met onbekende sleutel"),
            ({"entity_id": 999999}, "entity_id bestaat niet"),
            ({"onzin": 1}, "onbekend veld"),
            ({}, "leeg"),
        ]
        for body, label in slecht:
            r = client.patch(f"/api/nieuws/doelen/{anouk}", json=body, headers=kop["nieuws-scout"])
            eis(r.status_code == 400, f"{label} → 400 ({r.status_code})")
        voor = client.get(f"/api/nieuws/doelen/{anouk}", headers=kop["nieuws-scout"]
                          ).get_json()["doel"]["bijgewerkt"]
        r = client.patch(f"/api/nieuws/doelen/{anouk}",
                         json={"status": "klaar", "verslag": "Wethouder; partijlidmaatschap "
                               "vastgelegd.", "resultaat": {"entity_ids": [3, 3, 1],
                                                           "relation_ids": [7]},
                               "vervolg": "linkedin", "entity_id": ent},
                         headers=kop["nieuws-scout"])
        d = r.get_json().get("doel", {})
        eis(r.status_code == 200 and d["status"] == "klaar" and d["vervolg"] == "linkedin"
            and d["entity_id"] == ent
            and d["resultaat"] == {"entity_ids": [1, 3], "relation_ids": [7],
                                   "source_ids": [], "argument_ids": []},
            f"geldige PATCH → 200; resultaat genormaliseerd naar de 4 lijsten ({d.get('resultaat')})")
        eis(d["bijgewerkt"] >= voor, "bijgewerkt is bijgewerkt")
        r = client.patch(f"/api/nieuws/doelen/{anouk}", json={"vervolg": None},
                         headers=kop["t-admin"])
        eis(r.status_code == 200 and r.get_json()["doel"]["vervolg"] is None,
            "maintainer mag patchen; vervolg terug naar null")
        r = client.patch("/api/nieuws/doelen/999999", json={"status": "klaar"},
                         headers=kop["nieuws-scout"])
        eis(r.status_code == 404, "PATCH onbekend doel → 404")

        print("12. Afgerond doel: 409, tenzij opnieuw")
        r = client.post("/api/nieuws/doelen", json=doel_body("person:anouk-verbeek"),
                        headers=kop["nieuws-agent"])
        j = r.get_json()
        eis(r.status_code == 409 and j["doel"]["status"] == "klaar" and "error" in j,
            f"afgerond → 409 {{error, doel}} ({r.status_code})")
        r = client.post("/api/nieuws/doelen", json=doel_body("person:anouk-verbeek", opnieuw=True),
                        headers=kop["nieuws-agent"])
        d = r.get_json()["doel"]
        eis(r.status_code == 200 and d["status"] == "open" and d["geclaimd_door"] is None
            and r.get_json().get("heropend") is True,
            f"opnieuw: true → heropend (open, claim vrij) ({r.status_code})")
        eis(d["resultaat"] is not None, "eerdere resultaat-ids blijven zichtbaar na heropenen")

        print("13. Audit (edit_log) van statuswissels")
        conn = sqlite3.connect(db)
        acties = [tuple(x) for x in conn.execute(
            "SELECT action, changed_by FROM edit_log WHERE table_name = 'nieuws_doelen' "
            "AND record_id = ? ORDER BY id", (anouk,))]
        conn.close()
        eis(acties[0] == ("created", "nieuws-agent")
            and ("updated", "nieuws-scout") in acties and ("updated", "t-admin") in acties
            and acties[-1] == ("updated", "nieuws-agent"),
            f"created + claims/PATCH/heropenen gelogd onder het juiste account ({len(acties)} rijen)")

        print("\nALLE NIEUWS-DOELEN-TESTS GESLAAGD")


if __name__ == "__main__":
    main()
