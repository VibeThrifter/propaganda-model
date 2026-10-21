#!/usr/bin/env python3
"""End-to-end-test eigen metingen (eigenaarsbesluit 2026-10-16: een eigen meting telt als bewijs,
"zolang je aan journalistieke codes houdt") op een verse, tijdelijke database.

Dekt de hele keten en elke weigering van de journalistieke codes:
  1. opzet: poorten (login, vorm, maker), onvolledig vastleggen geweigerd, vastleggen (hash), daarna
     ligt de opzet vast;
  2. waarnemingen: alleen de maker, binnen de selectie (periode, media, groep, codes);
  3. afronden geweigerd zolang a–d open zijn (c: citaat niet op de url; d: te weinig controles);
  4. metingcheck (a) met een nep-ophaalfunctie: citaat_gevonden, alleen dat account mag het zetten,
     een gewijzigd citaat wordt opnieuw gezocht;
  5. blinde controle: niemand controleert een eigen waarneming, de controleur ziet de eerste
     codering pas na zijn eigen, codering ligt daarna vast; de agent meting_controle.py vult punt d
     aan (nep-model); overeenstemming en Cohen's kappa;
  6. afronden: dataset en samenvatting bevroren, publiek leesbaar, robots.txt en sitemap;
  7. als_bewijs: geweigerd zonder wederhoor (e), met een oordeel in de claim (f), met een regel die
     niet in de samenvatting staat; daarna bron (dataset, cluster meting:<id>, vindplaats) +
     argument + citatie (verbatim), dedup, een bijdrager landt 'voorgesteld';
  8. het gewicht: alleen een maintainer classificeert de bron, 'academisch' past niet bij een dataset;
  9. metingcheck (b): A1 'klopt', na geknoei aan de dataset 'klopt-niet' (herzien), en terug;
     bronchecker en bronzoeker slaan meting-argumenten over;
 10. een melding (rectificatie) over de meting gaat naar de maker, niet naar een agent; kill-switch.

Gebruik: python3 scripts/test_metingen.py   (exit-code 0 = alles groen)
"""
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import auth  # noqa: E402
import metingen  # noqa: E402
import server  # noqa: E402

PERIODE = {"van": "2026-01-01", "tot": "2026-06-30"}
VRAGEN = [{"sleutel": "standpunt", "vraag": "Welk standpunt neemt de geciteerde in over meer "
                                              "defensie-uitgaven?",
           "opties": ["tegen", "voor", "neutraal"]},
          {"sleutel": "financiering_vermeld", "vraag": "Vermeldt het artikel de financiering "
                                                       "van de organisatie?",
           "opties": ["ja", "nee"]}]


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


def fixture_db(pad):
    conn = sqlite3.connect(pad)
    conn.executescript((ROOT / "schema.sql").read_text())
    for eid, naam, soort in ((1, "NOS", "omroep"), (2, "RTL Nieuws", "mediaorganisatie"),
                             (3, "Clingendael", "denktank"), (4, "HCSS", "denktank"),
                             (5, "Rob de Wijk", "persoon"), (6, "Testkrant", "mediaorganisatie")):
        conn.execute("INSERT INTO entities (id, name, type) VALUES (?, ?, ?)", (eid, naam, soort))
    mech = conn.execute("SELECT id FROM mechanisms WHERE name = 'denktank_als_bron'").fetchone()[0]
    conn.execute("""INSERT INTO relations (id, source_id, target_id, relation_type, mechanism_id,
                    certainty, influence, active_from) VALUES (1, 3, 1, 'bron_van', ?, 0.6, 0.3,
                    '2020')""", (mech,))
    tokens = {}
    for naam, kind, rol in (("eigenaar", "mens", "maintainer"), ("collega", "mens", "bijdrager"),
                            ("bij2", "mens", "bijdrager"), ("rev", "mens", "reviewer"),
                            ("metingcheck", "agent", "bijdrager"),
                            ("metingcontrole", "agent", "bijdrager")):
        tokens[naam] = auth.new_token()
        conn.execute("INSERT INTO users (username, kind, role, token_hash, provenance) "
                     "VALUES (?, ?, ?, ?, ?)",
                     (naam, kind, rol, auth.hash_token(tokens[naam]),
                      "test" if kind == "agent" else None))
    conn.commit()
    conn.close()
    return tokens, mech


def verstuur_voor(client, token):
    kop = {"Authorization": f"Bearer {token}"}

    def verstuur(method, pad, body=None):
        if body is None:
            r = client.open(pad, method=method, headers=kop)
        else:
            r = client.open(pad, method=method, headers=kop, json=body)
        return r.status_code, (r.get_json(silent=True) or {})
    return verstuur


def main():
    tmpdir = Path(tempfile.mkdtemp(prefix="test-metingen-"))
    tmp = tmpdir / "metingen.db"
    tokens, mech = fixture_db(tmp)
    server.DB_PATH = tmp
    server._rate_emmers.clear()
    os.environ.pop("PROPAGANDA_METINGEN", None)
    os.environ.pop("PROPAGANDA_BASIS_URL", None)
    c = server.app.test_client()
    kop = {n: {"Authorization": f"Bearer {t}"} for n, t in tokens.items()}

    def db():
        conn = sqlite3.connect(tmp)
        conn.row_factory = sqlite3.Row
        return conn

    print("1. Opzet: poorten, vorm, vastleggen")
    r = c.post("/api/metingen", json={"titel": "x", "vraag": "y", "opzet": {}})
    eis(r.status_code == 401, f"anoniem een meting maken kan niet ({r.status_code})")
    slecht = {"selectie": {"media": [1, 999], "periode": {"van": "2026-13-01", "tot": None}},
              "groepen": [{"naam": "Clingendael", "entity_ids": [3]}, {"naam": "clingendael"}],
              "vragen": [{"sleutel": "Standpunt!", "vraag": "?", "opties": ["voor"]}],
              "extra": 1}
    r = c.post("/api/metingen", headers=kop["eigenaar"],
               json={"titel": "Experts over defensie", "vraag": "Wie?", "opzet": slecht})
    fouten = r.get_json().get("fouten") or []
    eis(r.status_code == 400 and len(fouten) >= 6,
        f"een misvormde opzet geeft een nette 400 met de fouten ({len(fouten)} fouten)")
    eis(any("#999" in f for f in fouten) and any("periode.van" in f for f in fouten)
        and any("twee keer" in f for f in fouten) and any("twee opties" in f for f in fouten),
        "onbekend medium, ongeldige datum, dubbele groep en één optie worden genoemd")
    concept = {"selectie": {"media": [1, 2], "periode": PERIODE, "zoektermen": "defensie"},
               "groepen": [{"naam": "Clingendael", "entity_ids": [3]},
                           {"naam": "HCSS", "entity_ids": [4]}],
               "vragen": VRAGEN}
    r = c.post("/api/metingen", headers=kop["eigenaar"],
               json={"titel": "Denktanks over defensie-uitgaven", "opzet": concept,
                     "vraag": "Welke denktanks komen bij NOS en RTL aan het woord over "
                              "defensie-uitgaven, met welk standpunt?"})
    j = r.get_json()
    eis(r.status_code == 201 and j["url"] == f"/meting/{j['id']}" and j["status"] == "opzet",
        "een onvolledige maar welgevormde opzet landt als 'opzet' met {id, url}")
    mid = j["id"]
    eis(c.get(f"/api/metingen/{mid}").status_code == 401,
        "een niet-afgeronde meting is niet openbaar (401)")
    eis(not c.get("/api/metingen").get_json()["metingen"],
        "de openbare lijst toont geen niet-afgeronde meting")
    eis(any(x["id"] == mid for x in c.get("/api/metingen", headers=kop["collega"])
            .get_json()["metingen"]), "ingelogd staat ze wel in de lijst")
    r = c.post(f"/api/metingen/{mid}/vastleggen", headers=kop["eigenaar"])
    open_ = r.get_json().get("open") or []
    eis(r.status_code == 400 and any("stopregel" in f for f in open_)
        and any("uitkomstmaat" in f for f in open_)
        and any("selectieregel" in f for f in open_),
        "vastleggen weigert een onvolledige opzet (selectieregel, uitkomstmaat, stopregel)")
    r = c.patch(f"/api/metingen/{mid}", headers=kop["collega"], json={"titel": "kaping"})
    eis(r.status_code == 403, "een ander dan de maker (of een maintainer) wijzigt de opzet niet")
    opzet = dict(concept, uitkomst="Aandeel 'tegen' per denktank en per medium",
                 stopregel="Alle artikelen in de periode; geen stop vóór 30 juni 2026")
    opzet["selectie"] = dict(concept["selectie"],
                             regel="Alle artikelen op nos.nl en rtl.nl met 'defensie' in de periode, "
                                   "via de zoekfunctie van beide sites, op volgorde van datum")
    r = c.patch(f"/api/metingen/{mid}", headers=kop["eigenaar"], json={"opzet": opzet})
    eis(r.status_code == 200 and r.get_json()["opzet"]["stopregel"], "de maker vult de opzet aan")
    r = c.post(f"/api/metingen/{mid}/waarnemingen", headers=kop["eigenaar"], json={})
    eis(r.status_code == 409, "geen waarnemingen vóór het vastleggen (methode vooraf)")
    r = c.post(f"/api/metingen/{mid}/vastleggen", headers=kop["eigenaar"])
    j = r.get_json()
    eis(r.status_code == 200 and j["status"] == "vastgelegd"
        and j["opzet_hash"] == metingen.opzet_hash(opzet),
        "vastgelegd met de sha256 van de opzet")
    eis(c.patch(f"/api/metingen/{mid}", headers=kop["eigenaar"],
                json={"titel": "andere titel"}).status_code == 409,
        "na het vastleggen ligt de opzet vast (409)")
    a = next(p for p in j["code_check"] if p["sleutel"] == "a")
    eis(a["ok"] is True, f"punt a (methode vooraf) is in orde: {a['uitleg'][:60]}…")
    r = c.delete(f"/api/metingen/{mid}", headers=kop["eigenaar"])
    eis(r.status_code == 409, "een vastgelegde meting kan niet weg")

    print("2. Waarnemingen: alleen de maker, binnen de selectie")
    basis = {"groep": "Clingendael", "wie": "Rob de Wijk, oprichter HCSS", "medium_entity_id": 1,
             "url": "https://nos.nl/artikel/1", "datum": "2026-02-01",
             "citaat": "We moeten de defensie-uitgaven niet verder verhogen dan nodig is.",
             "codes": {"standpunt": "tegen", "financiering_vermeld": "nee"}}
    r = c.post(f"/api/metingen/{mid}/waarnemingen", headers=kop["collega"], json=basis)
    eis(r.status_code == 403, "een ander dan de maker voert geen waarnemingen in")
    for fout_veld, waarde, woord in (("datum", "2025-12-31", "periode"),
                                     ("medium_entity_id", 6, "selectie"),
                                     ("groep", "TNO", "groep"),
                                     ("url", "nos.nl/artikel", "url"),
                                     ("codes", {"standpunt": "misschien"}, "optie")):
        r = c.post(f"/api/metingen/{mid}/waarnemingen", headers=kop["eigenaar"],
                   json=dict(basis, **{fout_veld: waarde}))
        eis(r.status_code == 400 and any(woord in f for f in r.get_json()["fouten"]),
            f"geweigerd: {fout_veld} = {waarde!r}")
    # Zes waarnemingen; de pagina's (nep-ophaalfunctie) staan hieronder
    invoer = [
        ("Clingendael", "Dick Zandee, onderzoeker Clingendael", 1, "https://nos.nl/a/1",
         "2026-02-02", "De verhoging van de defensie-uitgaven gaat te snel voor de krijgsmacht.",
         {"standpunt": "tegen", "financiering_vermeld": "nee"}, 3),
        ("Clingendael", "Monika Sie, directeur Clingendael", 2, "https://rtl.nl/a/2",
         "2026-03-03", "Europa moet meer investeren in zijn eigen verdediging, dat staat vast.",
         {"standpunt": "voor", "financiering_vermeld": "ja"}, None),
        ("Clingendael", "een buurtbewoner", 1, "https://nos.nl/a/3", "2026-03-10",
         "Ik zie niet waarom we zoveel geld aan tanks moeten uitgeven in deze tijd.",
         {"standpunt": "tegen"}, None),
        ("Clingendael", "Bob Deen, onderzoeker Clingendael", 1, "https://nos.nl/a/4",
         "2026-04-01", "Meer geld alleen lost de tekorten bij de landmacht niet op.",
         {"standpunt": "tegen", "financiering_vermeld": "nee"}, None),
        ("HCSS", "Rob de Wijk (HCSS)", 2, "https://rtl.nl/a/5", "2026-04-15",
         "Twee procent is het absolute minimum voor de NAVO-norm, eigenlijk is meer nodig.",
         {"standpunt": "voor", "financiering_vermeld": "nee"}, 5),
        ("HCSS", "Tim Sweijs, onderzoeksdirecteur HCSS", 1, "https://nos.nl/a/6", "2026-05-20",
         "Het is verstandig om de uitgaven geleidelijk en voorspelbaar te laten stijgen.",
         {"standpunt": "voor", "financiering_vermeld": "ja"}, None),
    ]
    wids = []
    for groep, wie, medium, url, datum, citaat, codes, ent in invoer:
        r = c.post(f"/api/metingen/{mid}/waarnemingen", headers=kop["eigenaar"],
                   json={"groep": groep, "wie": wie, "medium_entity_id": medium, "url": url,
                         "datum": datum, "citaat": citaat, "codes": codes, "entity_id": ent})
        eis(r.status_code == 201, f"waarneming ingevoerd ({wie[:28]}…)")
        wids.append(r.get_json()["id"])
    paginas = {url: f"<html><body><p>Inleiding van het artikel over defensie en de NAVO. {'x ' * 400}"
                    f"</p><p>{citaat}</p></body></html>" for _, _, _, url, _, citaat, _, _ in invoer}
    paginas["https://nos.nl/a/3"] = "<html><body>" + "Een ander artikel zonder het citaat. " * 40

    def nep_haal(bron, citaat):
        for url in (bron.get("url"), bron.get("archive_url")):
            if url in paginas:
                return paginas[url], "nep-pagina", url
        return None, "HTTP 404", None

    r = c.post(f"/api/metingen/{mid}/afronden", headers=kop["eigenaar"])
    open_ = r.get_json().get("open") or []
    eis(r.status_code == 400 and any(f.startswith("c.") for f in open_)
        and any(f.startswith("d.") for f in open_),
        "afronden weigert zolang c (citaten niet op de url) en d (geen controles) open zijn")
    eis(any("nog niet op de url gecontroleerd" in f for f in open_)
        and any("geen code voor 'financiering_vermeld'" in f for f in open_),
        "c noemt de ongecontroleerde citaten en de ontbrekende code")

    print("3. metingcheck (a): het citaat op de url, met een nep-ophaalfunctie")
    import metingcheck
    metingcheck.DB_PATH = tmp
    r = c.post(f"/api/metingen/{mid}/waarnemingen/{wids[0]}/citaatcontrole",
               headers=kop["eigenaar"], json={"gevonden": True})
    eis(r.status_code == 403, "alleen het account metingcheck zet citaat_gevonden")
    check = verstuur_voor(c, tokens["metingcheck"])
    uit = metingcheck.draai(verstuur=check, haal=nep_haal, meld=lambda *_: None)
    eis(uit["citaten"]["gevonden"] == 5 and uit["citaten"]["niet_gevonden"] == 1,
        f"vijf citaten letterlijk teruggevonden, één niet ({uit['citaten']})")
    conn = db()
    stand = {r["id"]: r["citaat_gevonden"] for r in conn.execute(
        "SELECT id, citaat_gevonden FROM meting_waarnemingen")}
    conn.close()
    eis(stand[wids[2]] == 0 and all(stand[w] == 1 for w in wids if w != wids[2]),
        "citaat_gevonden = 1 voor de vijf, 0 voor het artikel zonder het citaat")
    eis(metingcheck.draai(verstuur=check, haal=nep_haal, meld=lambda *_: None)
        ["citaten"]["te_doen"] == 0, "een niet-gevonden citaat komt pas na 24 uur terug")
    # De maker corrigeert waarneming 3: een publieke rol, het juiste artikel en de ontbrekende
    # codes (vóór de controle mag dat nog)
    paginas["https://nos.nl/a/3"] = paginas["https://nos.nl/a/1"].replace(
        invoer[0][5], "Wij zien geen reden om de uitgaven nu al zo sterk te verhogen, zei ze.")
    r = c.patch(f"/api/metingen/{mid}/waarnemingen/{wids[2]}", headers=kop["eigenaar"],
                json={"wie": "Margriet Drent, onderzoeker Clingendael",
                      "citaat": "Wij zien geen reden om de uitgaven nu al zo sterk te verhogen, zei ze.",
                      "codes": {"standpunt": "tegen", "financiering_vermeld": "nee"}})
    j = r.get_json()
    eis(r.status_code == 200 and j["citaat_gevonden"] is None,
        "een gewijzigd citaat moet opnieuw op de url teruggevonden worden")
    eis(c.patch(f"/api/metingen/{mid}/waarnemingen/{wids[2]}", headers=kop["collega"],
                json={"notitie": "x"}).status_code == 403, "alleen je eigen waarnemingen")
    uit = metingcheck.draai(verstuur=check, haal=nep_haal, meld=lambda *_: None)
    eis(uit["citaten"]["gevonden"] == 1, "na de correctie is het citaat gevonden")

    print("4. Blinde controle: niemand controleert zijn eigen waarneming")
    r = c.post(f"/api/metingen/{mid}/waarnemingen/{wids[0]}/controle", headers=kop["eigenaar"],
               json={"codes": {"standpunt": "tegen", "financiering_vermeld": "nee"}})
    eis(r.status_code == 403, "de invoerder controleert zijn eigen waarneming niet (403)")
    d = c.get(f"/api/metingen/{mid}", headers=kop["collega"]).get_json()
    eis(all(w["codes"] is None and w["codes_verborgen"] for w in d["waarnemingen"])
        and d["samenvatting"] is None,
        "de controleur ziet geen eerste codering en geen samenvatting (blind)")
    rij = c.get(f"/api/metingen/{mid}/controle", headers=kop["collega"]).get_json()
    eis(len(rij["te_controleren"]) == 6 and all("codes" not in w for w in rij["te_controleren"])
        and rij["nodig"] == 5, "de wachtrij geeft url en citaat zonder codes; nodig: 5 (min. 5)")
    eerste = rij["te_controleren"][0]["id"]
    r = c.post(f"/api/metingen/{mid}/waarnemingen/{eerste}/controle", headers=kop["collega"],
               json={"codes": {"standpunt": "tegen"}})
    eis(r.status_code == 400, "een controle codeert alle vragen")
    # De collega codeert vier waarnemingen; bij twee kiest hij voor 'standpunt' anders
    eerste_codes = {w: cd for w, (_, _, _, _, _, _, cd, _) in zip(wids, invoer)}
    eerste_codes[wids[2]] = {"standpunt": "tegen", "financiering_vermeld": "nee"}
    gecontroleerd = rij["te_controleren"][:4]
    for i, w in enumerate(gecontroleerd):
        codes = dict(eerste_codes[w["id"]])
        if i < 2:
            codes["standpunt"] = "neutraal"
        r = c.post(f"/api/metingen/{mid}/waarnemingen/{w['id']}/controle",
                   headers=kop["collega"], json={"codes": codes})
        eis(r.status_code == 201 and r.get_json()["eerste"] == eerste_codes[w["id"]],
            f"blinde controle #{w['id']} ingediend; daarna ziet de controleur de eerste codering")
    r = c.post(f"/api/metingen/{mid}/waarnemingen/{gecontroleerd[0]['id']}/controle",
               headers=kop["collega"], json={"codes": eerste_codes[gecontroleerd[0]["id"]]})
    eis(r.status_code == 409, "één controle per account per waarneming (409)")
    d = c.get(f"/api/metingen/{mid}", headers=kop["collega"]).get_json()
    zichtbaar = {w["id"] for w in d["waarnemingen"] if not w["codes_verborgen"]}
    eis(zichtbaar == {w["id"] for w in gecontroleerd},
        "na zijn eigen codering ziet de controleur alleen die eerste coderingen")
    r = c.patch(f"/api/metingen/{mid}/waarnemingen/{gecontroleerd[0]['id']}",
                headers=kop["eigenaar"], json={"codes": {"standpunt": "neutraal",
                                                         "financiering_vermeld": "nee"}})
    eis(r.status_code == 409, "na een controle ligt de eerste codering vast (409)")
    r = c.delete(f"/api/metingen/{mid}/waarnemingen/{gecontroleerd[0]['id']}",
                 headers=kop["eigenaar"])
    eis(r.status_code == 400, "een gecontroleerde waarneming verwijderen vergt een reden")
    d = c.get(f"/api/metingen/{mid}", headers=kop["eigenaar"]).get_json()
    pd = next(p for p in d["code_check"] if p["sleutel"] == "d")
    eis(pd["ok"] is False and d["gecontroleerd"] == 4 and "nog 1" in pd["open"][0],
        f"punt d: 4 van de 5 nodige controles ({pd['open'][0]})")
    o = d["overeenstemming"]["standpunt"]
    eis(o["n"] == 4 and o["gelijk"] == 2 and o["pct"] == 50.0 and o["waarschuwing"]
        and len(o["afwijkingen"]) == 2 and o["kappa"] is not None,
        f"overeenstemming 'standpunt' 50% (κ {o['kappa']}), onder 80%: waarschuwing met afwijkingen")
    eis(d["overeenstemming"]["financiering_vermeld"]["pct"] == 100.0,
        "overeenstemming 'financiering_vermeld' 100%")
    eis(pd["waarschuwingen"] and "afwijkingen #" in pd["waarschuwingen"][0],
        "de maker ziet de afwijkingen in de waarschuwing van punt d")
    dc = c.get(f"/api/metingen/{mid}", headers=kop["collega"]).get_json()
    pdc = next(p for p in dc["code_check"] if p["sleutel"] == "d")
    eis(all("afwijkingen #" not in w for w in pdc["waarschuwingen"]),
        "de controleur ziet de afwijkingen niet (blind tot hij zelf codeert)")
    eis(metingen.kappa([("a", "a"), ("b", "b")]) == 1.0
        and metingen.kappa([("a", "b"), ("b", "a")]) == -1.0
        and metingen.kappa([("a", "a"), ("a", "a")]) is None,
        "Cohen's kappa: 1 bij volledige, −1 bij tegengestelde overeenstemming, n.v.t. bij één klasse")

    # De agent vult punt d aan (nep-model en nep-pagina's; geen netwerk, geen tokens)
    import meting_controle
    gevraagd = []

    def nep_model(prompt, schema):
        gevraagd.append((prompt, schema))
        return {"codes": {"standpunt": "voor", "financiering_vermeld": "ja"}, "toelichting": "nep"}

    agent = verstuur_voor(c, tokens["metingcontrole"])
    uit = meting_controle.draai(mid, indienen=False, verstuur=agent, haal=nep_haal,
                                model=nep_model, meld=lambda *_: None)
    eis(uit["gecodeerd"] == 1 and uit["ingediend"] == 0,
        "de agent codeert standaard als droogloop (niets ingediend)")
    prompt, schema = gevraagd[0]
    eis(set(schema["properties"]["codes"]["properties"]) == {"standpunt", "financiering_vermeld"}
        and "Citaat:" in prompt and "Kies uit:" in prompt,
        "het model krijgt het artikel, het citaat en de vragen met opties (blind: geen codering)")
    uit = meting_controle.draai(mid, indienen=True, verstuur=agent, haal=nep_haal,
                                model=nep_model, meld=lambda *_: None)
    eis(uit["ingediend"] == 1, "met --indienen dient de agent zijn blinde codering in")

    print("5. Afronden: dataset en samenvatting bevroren, publiek")
    r = c.post(f"/api/metingen/{mid}/afronden", headers=kop["collega"])
    eis(r.status_code == 403, "alleen de maker (of een maintainer) rondt af")
    r = c.post(f"/api/metingen/{mid}/afronden", headers=kop["eigenaar"])
    j = r.get_json()
    eis(r.status_code == 200 and j["status"] == "afgerond" and j["data_hash"]
        and j["afgerond_at"], f"afgerond met een data-hash ({r.status_code}: {j.get('error')})")
    conn = db()
    m = metingen.laad(conn, mid)
    conn.close()
    eis(metingen.data_hash(m) == j["data_hash"], "de data-hash is de sha256 van de dataset")
    regels = j["regels"]
    verwacht = "Clingendael (n=4) · standpunt: tegen 3 (75%), voor 1 (25%), neutraal 0 (0%)"
    eis(verwacht in regels, f"vaste samenvattingsregel: {verwacht}")
    eis("Clingendael (n=4) · media: NOS 3, RTL Nieuws 1" in regels
        and any(x.startswith("Alle groepen (n=6) · standpunt:") for x in regels),
        "per groep het aantal per medium, plus alle groepen samen")
    for pad, body in ((f"/api/metingen/{mid}/waarnemingen", dict(basis)),
                      (f"/api/metingen/{mid}/waarnemingen/{wids[5]}/controle",
                       {"codes": eerste_codes[wids[5]]})):
        r = c.post(pad, headers=kop["collega"] if "controle" in pad else kop["eigenaar"],
                   json=body)
        eis(r.status_code == 409, f"na het afronden ligt alles vast ({pad.split('/')[-1]}: 409)")
    d = c.get(f"/api/metingen/{mid}").get_json()
    eis(d["status"] == "afgerond" and all(w["codes"] is not None for w in d["waarnemingen"]),
        "een afgeronde meting is openbaar, met alle coderingen")
    eis(any(x["id"] == mid for x in c.get("/api/metingen").get_json()["metingen"]),
        "de openbare lijst toont de afgeronde meting")
    eis(c.get(f"/meting/{mid}").status_code == 200, "de pagina /meting/<id> is publiek")
    r = c.post("/api/metingen", headers=kop["eigenaar"], json={"titel": "Concept", "vraag": "?"})
    concept_id = r.get_json()["id"]
    r = c.get(f"/meting/{concept_id}")
    eis(r.status_code == 302 and "/login" in r.headers["Location"],
        "een niet-afgeronde meting zit achter login (302 naar /login)")
    robots = c.get("/robots.txt").get_data(as_text=True)
    eis("Disallow: /meting" in robots and f"Allow: /meting/{mid}$" in robots
        and f"Allow: /meting/{concept_id}$" not in robots,
        "robots.txt: /meting op Disallow, behalve de afgeronde meting")
    eis(f"/meting/{mid}</loc>" in c.get("/sitemap.xml").get_data(as_text=True),
        "de afgeronde meting staat in sitemap.xml")
    eis(c.delete(f"/api/metingen/{concept_id}", headers=kop["eigenaar"]).status_code == 200,
        "een opzet kan wel weg (maker)")

    print("6. Als bewijs: de journalistieke codes e–h, regel en claim")
    regel = verwacht
    claim = ("In eigen meting #%d (NOS en RTL Nieuws, januari tot en met juni 2026) waren 3 van "
             "de 4 citaten van Clingendael-onderzoekers tegen hogere defensie-uitgaven." % mid)
    bewijs = {"relation_id": 1, "stance": "supporting", "property": None, "claim": claim,
              "regel": regel}
    r = c.post(f"/api/metingen/{mid}/als_bewijs", headers=kop["eigenaar"], json=bewijs)
    j = r.get_json()
    eis(r.status_code == 400 and any(f.startswith("e.") for f in j["open"])
        and not any(f.startswith(("a.", "b.", "c.", "d.", "f.", "g.", "h.")) for f in j["open"]),
        "zonder hoor en wederhoor weigert als_bewijs (punt e)")
    r = c.post(f"/api/metingen/{mid}/wederhoor", headers=kop["eigenaar"],
               json={"partij": "NOS", "entity_id": 1, "soort": "verzoek_zonder_reactie"})
    eis(r.status_code == 400, "een verzoek zonder reactie draagt een datum")
    r = c.post(f"/api/metingen/{mid}/wederhoor", headers=kop["collega"],
               json={"partij": "NOS", "soort": "verzoek_zonder_reactie", "datum": "2026-07-01"})
    eis(r.status_code == 403, "wederhoor legt de maker vast")
    for body in ({"entity_id": 1, "soort": "verzoek_zonder_reactie", "datum": "2026-07-01",
                  "tekst": "Vraag per mail aan de redactie, geen antwoord ontvangen."},
                 {"entity_id": 2, "soort": "reactie", "datum": "2026-07-03",
                  "tekst": "RTL Nieuws: wij nodigen experts uit op deskundigheid."},
                 {"entity_id": 3, "soort": "gepubliceerd_standpunt",
                  "bron_url": "https://www.clingendael.org/nl/over-ons"}):
        r = c.post(f"/api/metingen/{mid}/wederhoor", headers=kop["eigenaar"], json=body)
        eis(r.status_code == 201, f"wederhoor vastgelegd ({body['soort']})")
    r = c.post(f"/api/metingen/{mid}/als_bewijs", headers=kop["eigenaar"], json=bewijs)
    eis(r.status_code == 400 and any("HCSS" in f for f in r.get_json()["open"]),
        "nog geen wederhoor voor HCSS: nog steeds geweigerd")
    r = c.post(f"/api/metingen/{mid}/wederhoor", headers=kop["eigenaar"],
               json={"partij": "HCSS", "soort": "gepubliceerd_standpunt",
                     "bron_url": "https://hcss.nl/over-hcss/"})
    eis(r.status_code == 201, "wederhoor voor HCSS (op naam, zonder knoop)")
    r = c.post(f"/api/metingen/{mid}/als_bewijs", headers=kop["eigenaar"],
               json=dict(bewijs, claim=claim + " Dat ondermijnt het vertrouwen in de NOS."))
    eis(r.status_code == 400 and any(f.startswith("f.") for f in r.get_json()["open"]),
        "een oordeel in de claim ('ondermijnt het vertrouwen') faalt op punt f")
    r = c.post(f"/api/metingen/{mid}/als_bewijs", headers=kop["eigenaar"],
               json=dict(bewijs, claim="De NOS citeerde Clingendael eenzijdig."))
    eis(r.status_code == 400 and any("eenzijdig" in f for f in r.get_json()["open"]),
        "'eenzijdig' is een oordeel, geen telling (punt f)")
    eis(metingen.claim_treffers('Volgens de NVJ is de keuze "eenzijdig".') == [],
        "een toegeschreven of geciteerd oordeel mag (zoals in de eigen stem)")
    r = c.post(f"/api/metingen/{mid}/als_bewijs", headers=kop["eigenaar"],
               json=dict(bewijs, regel="Clingendael (n=4) · standpunt: tegen 4 (100%)"))
    eis(r.status_code == 400 and r.get_json().get("regels"),
        "een regel die niet letterlijk in de samenvatting staat, wordt geweigerd")
    r = c.post(f"/api/metingen/{mid}/als_bewijs", headers=kop["eigenaar"],
               json=dict(bewijs, relation_id=None, entity_id=3, stance="neutraal"))
    eis(r.status_code == 400, "stance moet supporting of contradicting zijn")
    r = c.post(f"/api/metingen/{mid}/als_bewijs", headers=kop["eigenaar"], json=bewijs)
    j = r.get_json()
    eis(r.status_code == 201 and j["source_id"] and j["argument_id"]
        and j["argument_status"] == "ongecontroleerd",
        f"als bewijs: bron + argument; een maintainer merget meteen ({j.get('argument_status')})")
    sid, aid = j["source_id"], j["argument_id"]
    conn = db()
    bron = dict(conn.execute("SELECT * FROM sources WHERE id = ?", (sid,)).fetchone())
    loc = conn.execute("SELECT location FROM source_locations WHERE source_id = ? AND "
                       "location_type = 'url'", (sid,)).fetchone()[0]
    cit = dict(conn.execute("SELECT * FROM citations WHERE argument_id = ?", (aid,)).fetchone())
    arg = dict(conn.execute("SELECT * FROM arguments WHERE id = ?", (aid,)).fetchone())
    conn.close()
    eis(bron["source_type"] == "dataset" and bron["cluster_key"] == f"meting:{mid}"
        and bron["title"] == f"Eigen meting #{mid}: Denktanks over defensie-uitgaven"
        and bron["publisher"] == "Propagandamodel (eigen meting)"
        and bron["author"] == "eigenaar" and bron["reliability"] == "onbeoordeeld",
        "bron: dataset, cluster meting:<id>, titel, uitgever, auteur; gewicht nog onbeoordeeld")
    eis(bron["date_published"] == str(m["afgerond_at"])[:10],
        f"bron: publicatiedatum = de dag van afronden ({bron['date_published']})")
    eis(loc == f"http://localhost:5000/meting/{mid}", f"vindplaats: de metingpagina ({loc})")
    eis(cit["quote"] == regel and cit["methode"] == "verbatim_quote" and cit["source_id"] == sid,
        "één citatie: quote = de regel, methode verbatim_quote")
    eis(arg["relation_id"] == 1 and arg["claim"] == claim and arg["self_merged"] == 1,
        "het argument hangt aan het verband, met de claim (maintainer: self-merge)")
    r = c.post(f"/api/metingen/{mid}/als_bewijs", headers=kop["eigenaar"], json=bewijs)
    eis(r.status_code == 409 and r.get_json()["source_id"] == sid,
        "dezelfde claim nog eens: duplicaat (409), de bron wordt hergebruikt")
    r = c.post(f"/api/metingen/{mid}/als_bewijs", headers=kop["bij2"],
               json={"doel": {"entity_id": 3}, "stance": "supporting", "claim":
                     "In eigen meting #%d kwam Clingendael 4 keer aan het woord bij NOS en RTL "
                     "Nieuws." % mid, "regel": "Clingendael (n=4) · media: NOS 3, RTL Nieuws 1"})
    j2 = r.get_json()
    eis(r.status_code == 201 and j2["source_id"] == sid and j2["argument_status"] == "voorgesteld",
        "een bijdrager gebruikt dezelfde bron; zijn argument landt 'voorgesteld'")
    d = c.get(f"/api/metingen/{mid}").get_json()
    eis({a["id"] for a in d["argumenten"]} == {aid},
        "publiek toont de meting alleen gemerged werk dat erop steunt")

    print("7. Het gewicht bepaalt de eigenaar")
    r = c.patch(f"/api/sources/{sid}/classificatie", headers=kop["rev"],
                json={"reliability": "primair", "onderwerp": "nl_systeem"})
    eis(r.status_code == 403, "een reviewer classificeert een eigen meting niet (403)")
    r = c.patch(f"/api/sources/{sid}/classificatie", headers=kop["eigenaar"],
                json={"reliability": "academisch", "onderwerp": "nl_systeem"})
    eis(r.status_code == 400, "'academisch' past niet bij een dataset (klasse_consistentie)")
    r = c.patch(f"/api/sources/{sid}/classificatie", headers=kop["eigenaar"],
                json={"reliability": "primair", "onderwerp": "nl_systeem",
                      "motivatie": "eigen meting, vooraf vastgelegd en blind gecontroleerd"})
    eis(r.status_code == 200 and r.get_json()["reliability"] == "primair",
        "de eigenaar kiest 'primair' (dataset met vindplaats mag)")
    d = c.get(f"/api/metingen/{mid}").get_json()
    kl = {k["klasse"]: k for k in d["bronklassen"]}
    eis(d["bron"]["gewicht"] == 0.95 and kl["primair"]["gewicht"] == 0.95
        and kl["primair"]["toegestaan"] and not kl["academisch"]["toegestaan"],
        "de pagina krijgt de gewichten uit scoring.RELIABILITY_WEIGHT per klasse")

    print("8. metingcheck (b): de A1 voor argumenten op een meting")
    import bronchecker
    import bronzoeker
    conn = sqlite3.connect(f"file:{tmp}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    eis(aid not in {r["id"] for r in bronchecker.kandidaten(conn)}
        and aid not in {r["id"] for r in bronchecker.controle_kandidaten(conn)}
        and j2["argument_id"] not in {r["id"] for r in bronchecker.kandidaten(conn)},
        "de bronchecker slaat meting-argumenten over (METING_ARG_SQL)")
    eis(not [x for x in bronzoeker.kandidaten(conn) if x["id"] in (aid, j2["argument_id"])],
        "de bronzoeker slaat meting-argumenten over")
    conn.close()
    uit = metingcheck.draai(verstuur=check, haal=nep_haal, meld=lambda *_: None)
    eis(uit["argumenten"]["klopt"] == 2, f"beide argumenten: A1 'klopt' ({uit['argumenten']})")
    conn = db()
    oordelen = {r["argument_id"]: r for r in conn.execute(
        "SELECT * FROM immuun_oordelen WHERE door = 'metingcheck'")}
    conn.close()
    eis(oordelen[aid]["verdict"] == "klopt" and oordelen[aid]["verbatim_span"] == regel,
        "het oordeel staat als herverificatie van metingcheck, met de regel als verbatim span")
    eis(metingcheck.draai(verstuur=check, haal=nep_haal, meld=lambda *_: None)
        ["argumenten"]["ongewijzigd"] == 2, "een tweede ronde verandert niets")
    conn = db()
    oud_citaat = conn.execute("SELECT citaat FROM meting_waarnemingen WHERE id = ?",
                              (wids[0],)).fetchone()[0]
    conn.execute("UPDATE meting_waarnemingen SET citaat = 'geknoeid' WHERE id = ?", (wids[0],))
    conn.commit()
    conn.close()
    uit = metingcheck.draai(verstuur=check, haal=nep_haal, meld=lambda *_: None)
    conn = db()
    o = conn.execute("SELECT verdict, detail FROM immuun_oordelen WHERE door = 'metingcheck' AND "
                     "argument_id = ?", (aid,)).fetchone()
    eis(uit["argumenten"]["klopt-niet"] == 2 and o["verdict"] == "klopt-niet"
        and "data-hash" in o["detail"],
        "na geknoei aan de dataset herziet metingcheck zijn oordeel: 'klopt-niet' (data-hash)")
    import validation
    eis(validation.check_metingen(conn)[0]["aantal"] == 1,
        "de validator meldt METING-INTEGRITEIT (fout) bij het geknoei")
    conn.execute("UPDATE meting_waarnemingen SET citaat = ? WHERE id = ?", (oud_citaat, wids[0]))
    conn.commit()
    conn.close()
    uit = metingcheck.draai(verstuur=check, haal=nep_haal, meld=lambda *_: None)
    eis(uit["argumenten"]["klopt"] == 2, "hersteld: weer 'klopt'")

    print("9. Melding over de meting, kill-switch")
    import lead_triage
    conn = sqlite3.connect(tmp)
    conn.execute("INSERT INTO leads (soort, claim, betreft) VALUES ('rectificatie', ?, ?)",
                 ("Het citaat van Dick Zandee staat niet in dat artikel.", f"meting:{mid}"))
    conn.execute("INSERT INTO leads (soort, claim, betreft) VALUES ('rectificatie', ?, ?)",
                 ("Klopt niet.", "meting:99999"))
    conn.commit()
    conn.close()
    plan = lead_triage.schiften(lead_triage.db(tmp))
    eis(any("eigen meting" in reden for _, reden in plan["wachten"])
        and not any(d.get("sleutel", "").startswith("rectificatie:") for d in plan["doorzetten"])
        and any("bestaat niet" in b["triage_reden"] for _, b in plan["afwijzen"]),
        "een melding over de meting wacht op de maker (geen agent); een onbekende meting valt af")
    d = c.get(f"/api/metingen/{mid}", headers=kop["eigenaar"]).get_json()
    eis(d["meldingen"] and d["meldingen"][0]["claim"].startswith("Het citaat"),
        "de maker ziet de melding op de metingpagina")
    eis(c.get(f"/api/metingen/{mid}").get_json()["meldingen"] is None,
        "publiek ziet geen meldingen")
    eis(metingen.RECTIFICATIE_LINK in (ROOT / "web" / "meting.html").read_text(encoding="utf-8")
        and next(p for p in d["code_check"] if p["sleutel"] == "h")["ok"],
        "punt h: de metingpagina linkt naar /tip?betreft=meting:<id>")
    os.environ["PROPAGANDA_METINGEN"] = "0"
    eis(metingcheck.draai(verstuur=check, haal=nep_haal, meld=lambda *_: None) == {"uit": True},
        "kill-switch PROPAGANDA_METINGEN=0 zet metingcheck uit")
    os.environ.pop("PROPAGANDA_METINGEN", None)
    r = c.get("/api/metingen/claimtoets?claim=" + "De NOS citeerde 4 keer Clingendael.")
    eis(r.get_json() == {"ok": True, "treffers": []}, "claimtoets (live punt f) op een telling")

    print("\nEigen metingen: alles groen.")


if __name__ == "__main__":
    main()
