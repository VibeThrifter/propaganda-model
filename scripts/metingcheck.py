#!/usr/bin/env python3
"""Metingcheck — de deterministische controle van eigen metingen (eigenaarsbesluit 2026-10-16: een
eigen meting telt als bewijs, "zolang je aan journalistieke codes houdt").

Geen taalmodel. Twee taken, onder het eigen account `metingcheck` (bijdrager, nooit de auteur):

  (a) Citaten op de url. Per waarneming van een vastgelegde meting wordt het artikel opgehaald
      (de url, dan de eigen archiefkopie, dan de Wayback Machine: dezelfde ophaalfunctie als de
      bronchecker) en het citaat letterlijk teruggezocht (genormaliseerd: hoofdletters,
      witruimte en typografische tekens tellen niet). Letterlijk gevonden → citaat_gevonden = 1;
      niet gevonden, alleen bijna letterlijk, of de pagina niet te lezen → 0, met de reden, en na
      24 uur een nieuwe poging. Dat kan alleen dit account
      (POST /api/metingen/<id>/waarnemingen/<wid>/citaatcontrole). Punt c van de journalistieke
      codes telt een waarneming pas als gecontroleerd met citaat_gevonden = 1.

  (b) De A1 voor argumenten op een meting. Een argument waarvan elke citatie uit een meting-bron
      komt (cluster_key 'meting:<id>', METING_ARG_SQL) krijgt zijn herverificatie-oordeel
      (POST /api/arguments/<id>/herverificatie): 'klopt' als de meting afgerond is, de data-hash
      klopt, het citaat letterlijk een regel uit de samenvatting is en alle journalistieke codes
      a–h in orde zijn (punt f met de claim van het argument); anders 'klopt-niet' met de reden.
      Verandert het oordeel later (de dataset blijkt gewijzigd), dan wordt het eigen oordeel
      herzien. De bronchecker en de bronzoeker slaan zulke argumenten over, net als registerfeiten.

Draait als stap 2c van scripts/automatische_beoordeling.py, met een klein plafond (citaten per
ronde) en een kill-switch PROPAGANDA_METINGEN=0. Los, bijvoorbeeld direct na het invoeren:
    python3 scripts/metingcheck.py --meting 3            # citaten en argumenten van meting #3
    python3 scripts/metingcheck.py --droog               # toon wat er te doen is, schrijf niets
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _pad in (ROOT, ROOT / "scripts"):
    if str(_pad) not in sys.path:
        sys.path.append(str(_pad))
import metingen  # noqa: E402  (repo-root, pure stdlib)

DB_PATH = ROOT / "data" / "propaganda_model.db"
TOKEN = ROOT / "data" / "tokens" / "metingcheck.token"
API = "http://127.0.0.1:5000"
ACCOUNT = "metingcheck"
PREFIX = "[metingcheck]"
HERPROBEER_UUR = 24          # een niet-gevonden citaat: na zoveel uur opnieuw zoeken
MAX_CITATEN = 20             # pagina's per ronde (stap 2c); elke pagina kost seconden
MAX_ARGUMENTEN = 100

# Een argument waarvan ELKE citatie een regel uit een eigen meting is (alias a = arguments).
# Gedeeld met scripts/bronchecker.py en scripts/bronzoeker.py: die slaan zulke argumenten over,
# zodat hun oordeel (een webpagina ophalen) dit niet overschrijft.
METING_ARG_SQL = """(
    EXISTS (SELECT 1 FROM citations mc WHERE mc.argument_id = a.id)
    AND NOT EXISTS (
        SELECT 1 FROM citations mc JOIN sources ms ON ms.id = mc.source_id
        WHERE mc.argument_id = a.id
          AND NOT (COALESCE(ms.cluster_key, '') LIKE 'meting:%'
                   AND TRIM(COALESCE(mc.quote, '')) <> '')))"""


def uitgeschakeld() -> bool:
    return os.environ.get("PROPAGANDA_METINGEN", "1") == "0"


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def heeft_tabel(conn, naam: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                        (naam,)).fetchone() is not None


def http_verstuurder(api: str, token: str):
    def verstuur(method, pad, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(api + pad, data=data, method=method,
                                     headers={"Authorization": f"Bearer {token}",
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                tekst = r.read().decode()
                return r.status, (json.loads(tekst) if tekst else {})
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode() or "{}")
            except json.JSONDecodeError:
                return e.code, {}
    return verstuur


# ------------------------------------------------------------------ (a) citaten op de url
def citaat_kandidaten(conn, meting_id: int | None = None,
                      nu: datetime.datetime | None = None) -> list[sqlite3.Row]:
    """Waarnemingen van vastgelegde metingen waarvan het citaat nog niet op de url is gezocht,
    of niet gevonden werd en de laatste poging meer dan HERPROBEER_UUR geleden was."""
    nu = nu or datetime.datetime.utcnow()
    grens = (nu - datetime.timedelta(hours=HERPROBEER_UUR)).strftime("%Y-%m-%d %H:%M:%S")
    filt, params = "", [grens]
    if meting_id:
        filt, params = " AND m.id = ?", [grens, meting_id]
    return conn.execute(f"""
        SELECT w.* FROM meting_waarnemingen w JOIN metingen m ON m.id = w.meting_id
        WHERE m.status = 'vastgelegd'
          AND (w.citaat_gevonden IS NULL
               OR (w.citaat_gevonden = 0 AND COALESCE(w.citaat_gecontroleerd_at, '') < ?)){filt}
        ORDER BY w.citaat_gevonden IS NOT NULL, w.id""", params).fetchall()  # noqa: S608


def _haal_standaard(bron: dict, citaat: str | None):
    import bronchecker  # hier: bronchecker leest METING_ARG_SQL uit dit script
    return bronchecker.haal_bron(bron, citaat)


def zoek_op_pagina(w, haal=None) -> tuple[bool, str]:
    """(gevonden, toelichting): staat het citaat letterlijk op de url of de archiefkopie?
    ``haal(bron, citaat) -> (tekst, toelichting, gebruikte_url)``, zoals bronchecker.haal_bron."""
    import bronchecker
    citaat = (w["citaat"] or "").strip()
    if len(bronchecker.normaliseer(citaat)) < 12:
        return False, "citaat te kort om terug te zoeken (minder dan 12 tekens)"
    tekst, toelichting, gebruikt = (haal or _haal_standaard)(
        {"url": w["url"], "archive_url": w["archief_url"]}, citaat)
    if not tekst:
        return False, f"pagina niet te lezen ({toelichting})"
    gevonden, letterlijk, _ = bronchecker.zoek_citaat(citaat, tekst)
    if gevonden and letterlijk:
        return True, f"letterlijk teruggevonden op {gebruikt}"
    if gevonden:
        return False, (f"alleen bijna letterlijk teruggevonden op {gebruikt}: neem het citaat "
                       "letterlijk over")
    return False, f"niet teruggevonden op de url of de archiefkopie ({toelichting})"


def stap_citaten(conn, *, verstuur, haal=None, max_n=MAX_CITATEN, droog=False, meld=print,
                 meting_id=None) -> dict:
    rijen = citaat_kandidaten(conn, meting_id)
    tel = {"te_doen": len(rijen), "gevonden": 0, "niet_gevonden": 0, "fout": 0}
    if droog:
        for w in rijen[:max_n]:
            meld(f"  · meting #{w['meting_id']}, waarneming #{w['id']}: citaat zoeken op {w['url']}")
        return tel
    for w in rijen[:max(0, max_n)]:
        gevonden, toelichting = zoek_op_pagina(w, haal)
        status, antwoord = verstuur(
            "POST", f"/api/metingen/{w['meting_id']}/waarnemingen/{w['id']}/citaatcontrole",
            {"gevonden": gevonden, "toelichting": toelichting})
        if status != 200:
            tel["fout"] += 1
            meld(f"  ✗ waarneming #{w['id']}: {status} {antwoord.get('error')}")
            continue
        tel["gevonden" if gevonden else "niet_gevonden"] += 1
        if not gevonden:
            meld(f"  · waarneming #{w['id']} (meting #{w['meting_id']}): {toelichting}")
    return tel


# ------------------------------------------------------------------ (b) A1 voor argumenten
def argument_kandidaten(conn) -> list[sqlite3.Row]:
    return conn.execute(f"""
        SELECT a.* FROM arguments a
        WHERE NOT a.vervangen AND a.status <> 'verworpen' AND {METING_ARG_SQL}
        ORDER BY a.id""").fetchall()  # noqa: S608 - vaste SQL


def metingen_van(conn, arg_id: int) -> set[int]:
    return {metingen.meting_id_uit_cluster(r[0]) for r in conn.execute(
        """SELECT s.cluster_key FROM citations c JOIN sources s ON s.id = c.source_id
           WHERE c.argument_id = ?""", (arg_id,))} - {None}


def beoordeel_argument(conn, arg) -> tuple[str, str, str | None, int | None]:
    """→ (verdict, detail, verbatim_span, bron_id)."""
    citaties = conn.execute("""
        SELECT c.quote, c.source_id, s.cluster_key FROM citations c
        JOIN sources s ON s.id = c.source_id WHERE c.argument_id = ? ORDER BY c.id""",
                            (arg["id"],)).fetchall()
    if not citaties:
        return "klopt-niet", f"{PREFIX} het argument heeft geen citaties", None, None
    gezien = []
    for c in citaties:
        mid = metingen.meting_id_uit_cluster(c["cluster_key"])
        if mid is None:
            return ("klopt-niet", f"{PREFIX} bron #{c['source_id']} is geen eigen meting",
                    None, c["source_id"])
        m = metingen.laad(conn, mid)
        if m is None:
            return ("klopt-niet", f"{PREFIX} meting #{mid} bestaat niet (meer)", None,
                    c["source_id"])
        if m["status"] != "afgerond":
            return ("klopt-niet", f"{PREFIX} meting #{mid} is niet afgerond (status "
                                  f"'{m['status']}')", None, c["source_id"])
        if not m.get("data_hash") or metingen.data_hash(m) != m["data_hash"]:
            return ("klopt-niet", f"{PREFIX} de dataset van meting #{mid} is gewijzigd na het "
                                  "afronden (de data-hash klopt niet)", None, c["source_id"])
        if (c["quote"] or "").strip() not in metingen.regels_van(m):
            return ("klopt-niet", f"{PREFIX} het citaat is geen letterlijke regel uit de "
                                  f"samenvatting van meting #{mid}", None, c["source_id"])
        open_ = metingen.open_punten(metingen.code_check(m, claim=arg["claim"]))
        if open_:
            return ("klopt-niet", f"{PREFIX} meting #{mid} voldoet niet aan de journalistieke "
                                  "codes: " + "; ".join(open_)[:700], None, c["source_id"])
        gezien.append(f"#{mid} (data-hash {m['data_hash'][:12]}…)")
    c0 = citaties[0]
    return ("klopt", f"{PREFIX} meting {', '.join(gezien)} is afgerond en ongewijzigd; het citaat "
                     "is letterlijk een regel uit de samenvatting en de journalistieke codes a–h "
                     "zijn in orde", (c0["quote"] or "").strip(), c0["source_id"])


def eigen_oordeel(conn, arg_id: int):
    return conn.execute("""SELECT verdict, detail FROM immuun_oordelen WHERE argument_id = ?
                           AND fase = 'herverificatie' AND door = ?""",
                        (arg_id, ACCOUNT)).fetchone()


def stap_argumenten(conn, *, verstuur, max_n=MAX_ARGUMENTEN, droog=False, meld=print,
                    meting_id=None) -> dict:
    tel = {"klopt": 0, "klopt-niet": 0, "ongewijzigd": 0, "fout": 0}
    for a in argument_kandidaten(conn):
        if meting_id and meting_id not in metingen_van(conn, a["id"]):
            continue
        if sum(tel.values()) >= max_n:
            break
        verdict, detail, span, bron_id = beoordeel_argument(conn, a)
        oud = eigen_oordeel(conn, a["id"])
        if oud is not None and oud["verdict"] == verdict:
            tel["ongewijzigd"] += 1
            continue
        if droog:
            tel[verdict] += 1
            meld(f"  · argument #{a['id']}: {verdict} — {detail}")
            continue
        body = {"verdict": verdict, "detail": detail, "verbatim_span": span, "bron_id": bron_id}
        if oud is not None:
            body["herzien"] = True
        status, antwoord = verstuur("POST", f"/api/arguments/{a['id']}/herverificatie", body)
        if status in (200, 201):
            tel[verdict] += 1
            if verdict != "klopt":
                meld(f"  · argument #{a['id']}: {detail}")
        else:
            tel["fout"] += 1
            meld(f"  ✗ argument #{a['id']}: {status} {antwoord.get('error')}")
    return tel


# ------------------------------------------------------------------ ronde
def draai(*, droog: bool = False, max_citaten: int = MAX_CITATEN,
          max_argumenten: int = MAX_ARGUMENTEN, meting_id: int | None = None,
          alleen_citaten: bool = False, verstuur=None, haal=None, meld=print) -> dict:
    """Eén ronde: eerst (a) de citaten, dan (b) de argumenten. ``verstuur(method, pad, body)``
    en ``haal(bron, citaat)`` zijn in te pluggen (tests)."""
    if uitgeschakeld():
        meld("Metingcheck: uitgeschakeld (PROPAGANDA_METINGEN=0)")
        return {"uit": True}
    if verstuur is None and not droog:
        if not TOKEN.exists():
            meld(f"Metingcheck: geen token ({TOKEN}); maak het account met scripts/create_user.py")
            return {"gestart": False, "reden": "geen token voor het account 'metingcheck'"}
        verstuur = http_verstuurder(API, TOKEN.read_text().strip())
    conn = db()
    try:
        if not heeft_tabel(conn, "metingen"):
            return {"gestart": False,
                    "reden": "de tabel metingen ontbreekt (scripts/migrate_add_metingen.py)"}
        citaten = stap_citaten(conn, verstuur=verstuur, haal=haal, max_n=max_citaten,
                               droog=droog, meld=meld, meting_id=meting_id)
        argumenten = ({} if alleen_citaten else
                      stap_argumenten(conn, verstuur=verstuur, max_n=max_argumenten, droog=droog,
                                      meld=meld, meting_id=meting_id))
    finally:
        conn.close()
    if citaten.get("te_doen") or any(argumenten.get(k) for k in ("klopt", "klopt-niet", "fout")):
        meld(f"Metingcheck: citaten {citaten.get('gevonden', 0)} gevonden, "
             f"{citaten.get('niet_gevonden', 0)} niet (van {citaten.get('te_doen', 0)} te doen); "
             f"argumenten {argumenten.get('klopt', 0)} klopt, {argumenten.get('klopt-niet', 0)} "
             f"klopt niet{' (droog)' if droog else ''}")
    return {"gestart": True, "citaten": citaten, "argumenten": argumenten}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--droog", action="store_true", help="toon wat er te doen is, schrijf niets")
    ap.add_argument("--meting", type=int, default=None, help="alleen deze meting")
    ap.add_argument("--max-citaten", type=int, default=MAX_CITATEN,
                    help="hooguit zoveel pagina's ophalen")
    ap.add_argument("--alleen-citaten", action="store_true", help="geen argumenten beoordelen")
    ap.add_argument("--api", default=API)
    a = ap.parse_args()
    verstuur = None
    if not a.droog and TOKEN.exists():
        verstuur = http_verstuurder(a.api, TOKEN.read_text().strip())
    uit = draai(droog=a.droog, max_citaten=a.max_citaten, meting_id=a.meting,
                alleen_citaten=a.alleen_citaten, verstuur=verstuur)
    print(json.dumps(uit, ensure_ascii=False))


if __name__ == "__main__":
    main()
