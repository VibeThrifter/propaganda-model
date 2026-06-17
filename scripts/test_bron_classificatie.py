#!/usr/bin/env python3
"""End-to-end-test: bron-classificatie (reviewer-gated) + relevantie-as (NL-onderwerp).

Dekt:
  - classificeren (reliability/onderwerp) is reviewer-werk; bijdrager → 403;
  - de poort weigert een onhoudbare/oncontroleerbare klasse: brontype dat niet bij de
    reliability past, of een hoge klasse zonder vindplaats (validation.klasse_consistentie);
  - de relevantie-as: een NL-bron weegt zwaarder dan een buitenlandse van dezelfde rigueur,
    maar overrulet nooit een rigueur-gat;
  - de validator vlagt een inconsistente classificatie (BRON-KLASSE).

Gebruik: python3 scripts/test_bron_classificatie.py   (exit-code 0 = alles groen)
"""
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import auth        # noqa: E402
import scoring     # noqa: E402
import server      # noqa: E402
import validation  # noqa: E402


def eis(c, m):
    if not c:
        sys.exit(f"FAAL: {m}")
    print(f"  ok — {m}")


def fixture(pad):
    conn = sqlite3.connect(pad)
    conn.executescript((ROOT / "schema.sql").read_text())
    # Bron 1: academisch_artikel mét vindplaats (mag academisch worden).
    conn.execute("INSERT INTO sources (id, title, source_type) VALUES (1, 'NL-studie', 'academisch_artikel')")
    conn.execute("INSERT INTO source_locations (source_id, location_type, location) VALUES (1, 'doi', '10.x/abc')")
    # Bron 2: boek zónder vindplaats (academisch moet geweigerd worden tot er een locator is).
    conn.execute("INSERT INTO sources (id, title, source_type) VALUES (2, 'Boek', 'boek')")
    # Bron 3: website (mag nooit academisch worden — typemismatch).
    conn.execute("INSERT INTO sources (id, title, source_type) VALUES (3, 'Blog', 'website')")
    toks = {}
    for naam, rol in (("bij", "bijdrager"), ("rev", "reviewer")):
        toks[naam] = auth.new_token()
        conn.execute("INSERT INTO users (username, kind, role, token_hash) VALUES (?,?,?,?)",
                     (naam, "mens", rol, auth.hash_token(toks[naam])))
    conn.commit(); conn.close()
    return toks


def main():
    # ── Unit: relevantie-as in source_factor ──
    print("1. relevantie-as (source_factor)")
    inst_nl = scoring.source_factor([("institutioneel", "nl_systeem")])
    inst_buit = scoring.source_factor([("institutioneel", "buitenlands")])
    inst_neutraal = scoring.source_factor([("institutioneel", "onbepaald")])
    eis(inst_nl > inst_neutraal > inst_buit,
        f"NL > neutraal > buitenlands bij gelijke rigueur ({inst_nl:.3f} > {inst_neutraal:.3f} > {inst_buit:.3f})")
    acad_buit = scoring.source_factor([("academisch", "buitenlands")])
    grijs_nl = scoring.source_factor([("grijs", "nl_systeem")])
    eis(acad_buit > grijs_nl,
        f"rigueur-gat blijft: buitenlands academisch > NL grijs ({acad_buit:.3f} > {grijs_nl:.3f})")

    # ── Endpoint: classificatie-poort ──
    tmp = Path(tempfile.mkdtemp()) / "cls.db"
    toks = fixture(tmp)
    server.DB_PATH = tmp
    server._rate_emmers.clear()
    c = server.app.test_client()
    kop = {n: {"Authorization": f"Bearer {t}"} for n, t in toks.items()}

    print("2. classificeren is reviewer-werk")
    r = c.patch("/api/sources/1/classificatie", headers=kop["bij"],
                json={"reliability": "academisch", "onderwerp": "nl_systeem"})
    eis(r.status_code == 403, f"bijdrager mag niet classificeren ({r.status_code})")

    print("3. poort weigert onhoudbare/oncontroleerbare klassen")
    r = c.patch("/api/sources/3/classificatie", headers=kop["rev"],
                json={"reliability": "academisch"})
    eis(r.status_code == 400, f"website → academisch geweigerd (typemismatch) ({r.status_code})")
    r = c.patch("/api/sources/2/classificatie", headers=kop["rev"],
                json={"reliability": "academisch"})
    eis(r.status_code == 400, f"boek zonder vindplaats → academisch geweigerd ({r.status_code})")

    print("4. geldige classificatie wordt geaccepteerd")
    r = c.patch("/api/sources/1/classificatie", headers=kop["rev"],
                json={"reliability": "academisch", "onderwerp": "nl_systeem"})
    j = r.get_json()
    eis(r.status_code == 200 and j["reliability"] == "academisch" and j["onderwerp"] == "nl_systeem",
        "academisch_artikel mét vindplaats → academisch + nl_systeem")
    # Vindplaats toevoegen aan het boek → dan mag academisch wél.
    c.post("/api/sources/2/locations", headers=kop["rev"], json={"type": "isbn", "value": "978-x"})
    r = c.patch("/api/sources/2/classificatie", headers=kop["rev"], json={"reliability": "academisch"})
    eis(r.status_code == 200, "boek mét vindplaats → academisch toegestaan")

    print("5. validator vlagt een inconsistente classificatie (BRON-KLASSE)")
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    # Forceer een inconsistente klasse direct (de poort zou dit weigeren) en valideer.
    conn.execute("UPDATE sources SET reliability='institutioneel' WHERE id=3")  # website
    conn.commit()
    bevs = {b["code"]: b for b in validation.check_bronnen(conn)}
    conn.close()
    eis("BRON-KLASSE" in bevs and bevs["BRON-KLASSE"]["aantal"] >= 1,
        f"BRON-KLASSE vlagt de website-als-institutioneel ({bevs['BRON-KLASSE']['aantal']})")

    print("\nBron-classificatie + relevantie-as: alles groen.")


if __name__ == "__main__":
    main()
