#!/usr/bin/env python3
"""
Test kanalen-monitor (eigenaar 2026-10-19: accounts, blogs en youtubers minen naar verbanden,
toetsen, en het netwerk van elke genoemde partij uitzoeken).

Zonder netwerk en zonder de live database: een tijdelijke kanalen-db, een klein nep-model
(entities, relations, nieuws_doelen) en een nep-verstuurder die POST /api/nieuws/doelen nadoet.

  1. Ophalen: RSS, YouTube-Atom, Telegram-pagina, rollende WebVTT → tekst met tijdmarkeringen.
  2. Inlezen: een citaat dat niet letterlijk in het item staat wordt geweigerd; privé →
     buiten_scope; niet toetsbaar → niet_toetsbaar; alleen bronnen die in het item staan.
  3. Triage: een verband dat al goedgekeurd is → bevestigd zonder doel; een nieuw verband →
     doel 'kanaal:<id>' met de waarschuwing; hetzelfde paar → duplicaat; netwerkdoelen voor de
     partijen, nooit voor een privépersoon, en niet opnieuw binnen een half jaar.
  4. Terugschrijven: ingediend → voorgesteld → bevestigd zodra het verband goedgekeurd is;
     KANAAL-UITKOMST: weerlegd → weerlegd; niets_gevonden → onbewezen.
  5. Kill-switch KANALEN=0 zet geen doelen klaar; de droogloop schrijft niets.
  6. Rapport: tellingen per kanaal, een duplicaat telt met de uitkomst van zijn eerste.

Gebruik: python3 scripts/test_kanalen.py   (exit-code 0 = alles groen)
"""
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import kanalen  # noqa: E402
import ophalen  # noqa: E402  (via kanalen op het pad)

FOUTEN = []


def check(naam, ok, extra=""):
    print(("  ✓ " if ok else "  ✗ ") + naam + (f"  [{extra}]" if extra and not ok else ""))
    if not ok:
        FOUTEN.append(naam)


RSS = """<?xml version="1.0"?><rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel><title>Blog</title><item><title>Wie zit waar</title><link>https://blog.example/a</link>
<guid>a1</guid><pubDate>Mon, 19 Oct 2026 08:00:00 +0200</pubDate>
<content:encoded><![CDATA[<p>Jan Jansen zit sinds 2021 in het bestuur van Stichting Voorbeeld,
zie <a href="https://register.example/x">het register</a>.</p>
<p><a href="https://bsky.app/intent/compose?text=x">deel</a></p>]]></content:encoded></item></channel></rss>"""

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"
 xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/">
<entry><id>yt:video:abc</id><yt:videoId>abc</yt:videoId><title>Video</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=abc"/><published>2026-10-18T10:00:00+00:00</published>
<media:group><media:description>Beschrijving van de video</media:description></media:group></entry></feed>"""

TELEGRAM = """<div class="tgme_widget_message_wrap"><div class="tgme_widget_message" data-post="kanaal/7">
<div class="tgme_widget_message_text js-message_text" dir="auto">Piet Pieters werkt voor<br/>Bedrijf Y
<a href="https://nieuws.example/p">bron</a></div><time datetime="2026-10-17T12:00:00+00:00"></time></div></div>"""

VTT = """WEBVTT

00:00:01.000 --> 00:00:03.000
hallo allemaal

00:00:03.000 --> 00:00:03.010
hallo allemaal

00:00:03.010 --> 00:00:06.000
hallo allemaal
Jan Jansen zit in het bestuur

00:00:40.000 --> 00:00:42.000
van Stichting Voorbeeld
"""


def nep_model(pad: Path):
    c = sqlite3.connect(pad)
    c.executescript("""
    CREATE TABLE entities (id INTEGER PRIMARY KEY, name TEXT, type TEXT, metadata TEXT,
                           status TEXT, vervangen INTEGER DEFAULT 0);
    CREATE TABLE relations (id INTEGER PRIMARY KEY, source_id INTEGER, target_id INTEGER,
                            status TEXT, vervangen INTEGER DEFAULT 0);
    CREATE TABLE nieuws_doelen (id INTEGER PRIMARY KEY, sleutel TEXT UNIQUE, naam TEXT, soort TEXT,
                                status TEXT, verslag TEXT, resultaat TEXT);
    INSERT INTO entities VALUES (1, 'Jan Jansen', 'persoon', '{}', 'goedgekeurd', 0),
                                (2, 'Stichting Voorbeeld', 'stichting', '{}', 'goedgekeurd', 0),
                                (3, 'Bedrijf Y', 'bedrijf', '{}', 'goedgekeurd', 0),
                                (4, 'Kees Klaassen', 'persoon', '{}', 'goedgekeurd', 0);
    INSERT INTO relations VALUES (10, 1, 2, 'goedgekeurd', 0);
    """)
    c.commit()
    return c


class NepServer:
    """Doet POST /api/nieuws/doelen na in het nep-model."""
    def __init__(self, conn):
        self.conn, self.posts = conn, []

    def __call__(self, method, pad, body=None):
        self.posts.append(body)
        rij = self.conn.execute("SELECT * FROM nieuws_doelen WHERE sleutel = ?",
                                (body["sleutel"],)).fetchone()
        if rij and rij[4] not in ("open", "bezig") and not body.get("opnieuw"):
            return 409, {"error": "al afgerond", "doel": {"id": rij[0], "status": rij[4]}}
        if rij:
            self.conn.execute("UPDATE nieuws_doelen SET status = 'open' WHERE id = ?", (rij[0],))
            did = rij[0]
        else:
            did = self.conn.execute("INSERT INTO nieuws_doelen (sleutel, naam, soort, status) "
                                    "VALUES (?, ?, ?, 'open')",
                                    (body["sleutel"], body["naam"], body["soort"])).lastrowid
        self.conn.commit()
        return 201, {"doel": {"id": did, "status": "open"}}


def main():
    tmp = Path(tempfile.mkdtemp(prefix="kanalen_test_"))
    kanalen.MANIFESTEN = tmp / "manifesten"
    os.environ.pop("KANALEN", None)

    print("1. Ophalen (parsers)")
    rss = ophalen.feed_items(RSS)
    check("RSS: één item met link als bron", len(rss) == 1 and "(https://register.example/x)" in rss[0]["tekst"])
    check("RSS: deelknop weggefilterd", "bsky.app" not in rss[0]["tekst"])
    check("RSS: datum naar ISO", rss[0]["gepubliceerd"].startswith("2026-10-19T08:00:00"))
    yt = ophalen.feed_items(ATOM)
    check("YouTube-Atom: video-id en beschrijving", yt[0]["extern_id"] == "abc"
          and yt[0]["tekst"] == "Beschrijving van de video" and yt[0]["tekstsoort"] == "beschrijving")
    tg = ophalen.telegram_items(TELEGRAM, "kanaal")
    check("Telegram: post, regels en link", tg and tg[0]["extern_id"] == "kanaal/7"
          and "Bedrijf Y" in tg[0]["tekst"] and "(https://nieuws.example/p)" in tg[0]["tekst"])
    vtt = ophalen.vtt_naar_tekst(VTT)
    check("VTT: rollende regels ontdubbeld", vtt.count("hallo allemaal") == 1, vtt)
    check("VTT: tijdmarkeringen", "[00:01]" in vtt and "[00:40]" in vtt, vtt)

    print("2. Inlezen")
    conn = kanalen.kdb(tmp / "kanalen.db")
    kanalen.toevoegen(conn, "blog", "https://blog.example", naam="Blog A")
    kanalen.toevoegen(conn, "youtube", "https://youtube.com/@b", naam="Kanaal B")
    for kid, eid, tekst in ((1, "a1", rss[0]["tekst"] + "\nPiet Pieters werkt voor Bedrijf Y."),
                            (2, "v1", vtt + " Kees Klaassen is lid van Stichting Voorbeeld. "
                             "Jan Jansen zit in het bestuur van Stichting Voorbeeld, echt waar. "
                             "Mijn buurman Henk werkt bij Bedrijf Y. Piet Pieters werkt voor Bedrijf Y. "
                             "Kees Klaassen is corrupt en werkt samen met Bedrijf Y.")):
        conn.execute("INSERT INTO items (kanaal_id, extern_id, url, titel, tekst, opgehaald) "
                     "VALUES (?, ?, ?, 't', ?, ?)", (kid, eid, f"https://x/{eid}", tekst, kanalen.nu()))
    conn.commit()

    def cl(a, sa, b, sb, sv, citaat, **kw):
        return {"partij_a": a, "soort_a": sa, "partij_b": b, "soort_b": sb, "soort_verband": sv,
                "citaat": citaat, **kw}
    kanalen.MANIFESTEN.mkdir(parents=True)
    (kanalen.MANIFESTEN / "r1.json").write_text(json.dumps({"items": [
        {"item_id": 1, "claims": [
            cl("Jan Jansen", "persoon", "Stichting Voorbeeld", "organisatie", "bestuur",
               "Jan Jansen zit sinds 2021 in het bestuur van Stichting Voorbeeld", jaar="2021",
               bronnen=["https://register.example/x", "https://verzonnen.example/y"],
               rolcat_a="politicus"),
            cl("Piet Pieters", "persoon", "Bedrijf Y", "organisatie", "functie",
               "Piet Pieters werkt voor Bedrijf Y", rolcat_a="bestuurder"),
            cl("Piet Pieters", "persoon", "Partij Z", "organisatie", "lidmaatschap",
               "Piet Pieters is lid van Partij Z"),          # staat niet in de tekst
        ]},
        {"item_id": 2, "claims": [
            cl("Kees Klaassen", "persoon", "Stichting Voorbeeld", "organisatie", "lidmaatschap",
               "Kees Klaassen is lid van Stichting Voorbeeld", tijdcode="00:40"),
            cl("Stichting Voorbeeld", "organisatie", "Jan Jansen", "persoon", "bestuur",
               "Jan Jansen zit in het bestuur van Stichting Voorbeeld"),
            cl("Henk", "persoon", "Bedrijf Y", "organisatie", "functie",
               "Mijn buurman Henk werkt bij Bedrijf Y", rolcat_a="prive"),
            cl("Kees Klaassen", "persoon", "Bedrijf Y", "organisatie", "anders",
               "Kees Klaassen is corrupt en werkt samen met Bedrijf Y", toetsbaar=False),
            cl("Bedrijf Y", "organisatie", "Piet Pieters", "persoon", "functie",
               "Piet Pieters werkt voor Bedrijf Y"),
        ]},
    ]}))
    uit = kanalen.inlezen(conn, meld=lambda *_: None)
    check("7 claims aangenomen, 1 geweigerd (citaat niet in item)",
          uit["claims"] == 7 and len(uit["geweigerd"]) == 1, uit)
    check("manifest naar verwerkt/", (kanalen.MANIFESTEN / "verwerkt" / "r1.json").exists())
    bronnen = json.loads(conn.execute("SELECT bronnen FROM claims WHERE id = 1").fetchone()[0])
    check("alleen bronnen die in het item staan", bronnen == ["https://register.example/x"], bronnen)
    st = dict(conn.execute("SELECT partij_a, status FROM claims WHERE partij_a IN ('Henk')"
                           " OR toetsbaar = 0").fetchall())
    check("privé → buiten_scope", st.get("Henk") == "buiten_scope", st)
    check("niet toetsbaar → niet_toetsbaar", st.get("Kees Klaassen") == "niet_toetsbaar", st)
    check("items gelezen", conn.execute("SELECT COUNT(*) FROM items WHERE status = 'gelezen'"
                                        ).fetchone()[0] == 2)

    print("3. Triage")
    m = nep_model(tmp / "model.db")
    mro = sqlite3.connect(f"file:{tmp / 'model.db'}?mode=ro", uri=True)
    mro.row_factory = sqlite3.Row
    droog = kanalen.triage(conn, mconn=mro, droog=True, meld=lambda *_: None)
    check("droogloop schrijft niets", conn.execute(
        "SELECT COUNT(*) FROM claims WHERE status = 'binnengekomen'").fetchone()[0] == 5
        and droog["plan"]["claims"], droog)
    os.environ["KANALEN"] = "0"
    server = NepServer(m)
    kanalen.triage(conn, verstuur=server, mconn=mro, meld=lambda *_: None)
    check("KANALEN=0: geen doelen", not server.posts)
    os.environ.pop("KANALEN")
    kanalen.triage(conn, verstuur=server, mconn=mro, meld=lambda *_: None)
    st = {r["id"]: dict(r) for r in conn.execute("SELECT * FROM claims")}
    check("bestaand verband → bevestigd zonder doel",
          st[1]["status"] == "bevestigd" and st[1]["doel_id"] is None, st[1])
    check("ander kanaal, verband staat al in het model → ook bevestigd",
          st[4]["status"] == "bevestigd", st[4])
    check("omgekeerde volgorde zelfde paar → duplicaat van #2",
          st[7]["status"] == "duplicaat" and st[7]["zelfde_als"] == 2, st[7])
    check("nieuw verband → in_onderzoek met doel", st[2]["status"] == "in_onderzoek"
          and st[2]["doel_id"], st[2])
    kdoel = next(p for p in server.posts if p["sleutel"] == "kanaal:2")
    check("kanaaldoel: waarschuwing, citaat, soort en anker", kdoel["context"]["waarschuwing"]
          and kdoel["context"]["claim"]["citaat"] == "Piet Pieters werkt voor Bedrijf Y"
          and kdoel["entity_id"] == 3 and kdoel["soort"] == "organisatie"
          and kdoel["prioriteit"] == kanalen.PRIORITEIT_CLAIM, kdoel)
    net = {p["sleutel"] for p in server.posts if p["sleutel"].startswith("netwerk:")}
    check("netwerkdoelen voor de partijen, ook na de kill-switch",
          {"netwerk:e1", "netwerk:e2"} <= net, net)
    check("nooit een netwerkdoel voor een privépersoon", "netwerk:henk" not in net, net)
    voor = len(server.posts)
    kanalen.triage(conn, verstuur=server, mconn=mro, max_netwerk=10, meld=lambda *_: None)
    nieuw = {p["sleutel"] for p in server.posts[voor:]}
    check("geen tweede netwerkdoel voor dezelfde partij", not (nieuw & net), nieuw & net)

    print("4. Terugschrijven")
    d2 = st[2]["doel_id"]
    m.execute("INSERT INTO entities VALUES (5, 'Piet Pieters', 'persoon', '{}', 'voorgesteld', 0)")
    m.execute("INSERT INTO relations VALUES (11, 5, 3, 'voorgesteld', 0)")
    m.execute("UPDATE nieuws_doelen SET status = 'klaar', verslag = ?, resultaat = ? WHERE id = ?",
              ("KANAAL-UITKOMST: bevestigd; KANAAL-BRON: geen\nverslag",
               json.dumps({"relation_ids": [11], "argument_ids": [99]}), d2))
    m.commit()
    kanalen.triage(conn, verstuur=server, mconn=mro, meld=lambda *_: None)
    c2 = dict(conn.execute("SELECT * FROM claims WHERE id = 2").fetchone())
    check("ingediend → voorgesteld (wacht op de uurronde)", c2["status"] == "voorgesteld", c2)
    check("bronoordeel uit het verslag", c2["bron_oordeel"] == "geen", c2)
    m.execute("UPDATE relations SET status = 'goedgekeurd' WHERE id = 11")
    m.commit()
    kanalen.triage(conn, verstuur=server, mconn=mro, meld=lambda *_: None)
    check("goedgekeurd in het model → bevestigd",
          conn.execute("SELECT status FROM claims WHERE id = 2").fetchone()[0] == "bevestigd")
    d3 = conn.execute("SELECT doel_id FROM claims WHERE id = 3").fetchone()[0]
    check("claim 3 (Kees–Stichting) kreeg een doel", bool(d3))
    m.execute("UPDATE nieuws_doelen SET status = 'niets_gevonden', verslag = ? WHERE id = ?",
              ("KANAAL-UITKOMST: weerlegd; KANAAL-BRON: draagt_niet\nledenlijst 2024 noemt hem niet",
               d3))
    m.commit()
    kanalen.triage(conn, verstuur=server, mconn=mro, meld=lambda *_: None)
    c3 = dict(conn.execute("SELECT * FROM claims WHERE id = 3").fetchone())
    check("KANAAL-UITKOMST: weerlegd → weerlegd", c3["status"] == "weerlegd"
          and c3["bron_oordeel"] == "draagt_niet", c3)

    print("5. Rapport")
    r = {k["kanaal"]["naam"]: k for k in kanalen.rapport(conn)}
    check("Blog A: 2 bevestigd", r["Blog A"]["telling"]["bevestigd"] == 2, r["Blog A"]["telling"])
    check("Kanaal B: duplicaat telt met uitkomst van #2, weerlegd 1, niet toetsbaar 1",
          r["Kanaal B"]["telling"]["bevestigd"] == 2 and r["Kanaal B"]["telling"]["weerlegd"] == 1
          and r["Kanaal B"]["telling"]["niet_toetsbaar"] == 1, r["Kanaal B"]["telling"])
    tekst = kanalen.rapport_tekst(kanalen.rapport(conn))
    check("rapport als tekst", "| Blog A | blog |" in tekst and "**weerlegd**" in tekst, tekst[:400])

    print()
    if FOUTEN:
        print(f"✗ {len(FOUTEN)} fout(en): {FOUTEN}")
        sys.exit(1)
    print("✓ alles groen")


if __name__ == "__main__":
    main()
