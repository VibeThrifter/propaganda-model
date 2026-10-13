#!/usr/bin/env python3
"""Registers-sync (Uitbreiding C, eigenaarsbesluit 2026-10-07): de registers elke week bijwerken.

Deterministisch, zonder LLM en zonder mens:
  1. per register een nieuwe uitgave ophalen (oo, tk, ep, lobby; tools/registers/<bron>.py haal);
  2. wat nieuw is indienen (<bron>_naar_model, onder `register-import`; idempotent: bestaande
     verbanden en knopen blijven, nieuwe ambten, Kamerleden, nevenfuncties … komen erbij en gaan
     langs de uurronde: registercheck → A7 → goedkeuren);
  3. wat afliep afsluiten: een lopend registerverband (ambt, zetel, fractie, nevenfunctie,
     zeggenschap, toegangspas) dat het plan van de nieuwste uitgave niet meer oplevert, krijgt een
     einddatum (de einddatum in het record als die er is, anders de datum van de uitgave) via
     POST /api/relations/<id>/looptijd onder `registercheck`, met de reden in edit_log.
     Stroomonderbreker: zou meer dan 10% (en meer dan 5) van de lopende verbanden van één register
     aflopen, dan sluit de sync voor dat register niets af en meldt het (een kapotte of halve
     download mag het model niet leeghalen).
Gebeurtenissen (geschenken, reizen) en de loopbaan lopen niet af; die blijven zoals ze zijn.
  4. looptijd (2026-10-09): scripts/registers_looptijd.py zet het begin en eind dat elk record
     noemt op verbanden die nog geen datum hebben, en legt vast waar het register geen begin noemt.

Gepland via agent_schedule.py (wekelijks); los:
    python3 scripts/registers_sync.py [--droog] [--alleen oo,tk,ep,lobby] [--zonder-ophalen]
"""
from __future__ import annotations

import argparse
import datetime
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "registers"))
sys.path.insert(0, str(ROOT / "scripts"))
import ep  # noqa: E402
import ep_naar_model  # noqa: E402
import lobby  # noqa: E402
import lobby_naar_model  # noqa: E402
import naar_model  # noqa: E402
import oo  # noqa: E402
import tk  # noqa: E402
import tk_naar_model  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
IMPORT_TOKEN = ROOT / "data" / "tokens" / "register-import.token"
CHECK_TOKEN = ROOT / "data" / "tokens" / "registercheck.token"
API = "http://127.0.0.1:5000"
BRONNEN = ("oo", "tk", "ep", "lobby")
# Welke records een lopende toestand zijn (de rest is een gebeurtenis of geschiedenis)
LOPEND = {"oo": ("org:", "fn:"), "tk": ("persoon:", "nevenfunctie:"), "ep": ("persoon:",), "lobby": ("lobbyist:",)}
MAX_AANDEEL = 0.10
MIN_ONDERBREKER = 5


def db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ── 1. ophalen ─────────────────────────────────────────────────────────────
def ophalen(bron: str, meld) -> None:
    module = {"oo": oo, "tk": tk, "ep": ep, "lobby": lobby}[bron]
    vandaag = datetime.date.today().isoformat()
    if any(vandaag in p.name for p in module.uitgaven()):
        meld(f"{bron}: de uitgave van vandaag is er al")
        return
    meld(f"{bron}: nieuwe uitgave {module.haal().name}")


def nieuwste(bron: str) -> tuple[str, dict]:
    if bron == "oo":
        uitgave = oo.uitgaven()[-1].stem.split("_", 1)[1]
        return uitgave, oo.lees_uitgave(uitgave)
    module = {"tk": tk, "ep": ep, "lobby": lobby}[bron]
    data = module.lees(module.uitgaven()[-1])
    return data["uitgave"], data


# ── 2. indienen ────────────────────────────────────────────────────────────
def plan_voor(bron: str, data: dict, conn):
    koppelingen = json.loads(tk_naar_model.KOPPELINGEN.read_text(encoding="utf-8"))
    if bron == "oo":
        return naar_model.Plan(data, conn).maak()
    if bron == "tk":
        return tk_naar_model.Plan(data, conn, koppelingen).maak()
    if bron == "ep":
        return ep_naar_model.Plan(data, conn).maak()
    return lobby_naar_model.Plan(data, conn, koppelingen).maak()


def indienen(bron: str, plan, rest, meld) -> dict:
    if bron == "oo":
        ind = naar_model.Indiener(plan, rest, None, meld)
        bron_id = ind.bron()
        ind.organisaties()
        ind.personen()
    elif bron == "lobby":
        ind = tk_naar_model.Indiener(plan, rest, meld, bron=lobby, cluster=lobby_naar_model.CLUSTER)
        bron_id = ind.bron()
        ind.entiteiten()
    else:
        ind = (tk_naar_model if bron == "tk" else ep_naar_model).Indiener(plan, rest, meld)
        bron_id = ind.bron()
        ind.entiteiten()
    ind.relaties(bron_id)
    return dict(ind.tel)


# ── 3. afsluiten ───────────────────────────────────────────────────────────
def geplande_verbanden(bron: str, plan, conn) -> set[tuple[int, int, str]]:
    """(bron_id, doel_id, type) van alles wat het plan van de nieuwste uitgave oplevert, voor
    zover de eindpunten al bestaan (na stap 2 is dat alles)."""
    return set(geplande_relaties(bron, plan, conn))


def geplande_relaties(bron: str, plan, conn) -> dict[tuple[int, int, str], dict]:
    """Als geplande_verbanden, met per verband de planregel (recordsleutel, start, eind):
    dezelfde koppeling als de import (externe id's, koppelingen), nooit op naam alleen."""
    ext = {(r["stelsel"], r["waarde"]): r["entity_id"] for r in conn.execute("SELECT * FROM externe_ids")}

    def eindpunt(ref):
        soort, w = ref
        if soort == "bestaand":
            return w
        if bron == "oo":
            if soort == "org":
                return ext.get(("oo", w)) or (plan.orgs.get(w) or {}).get("bestaand")
            if soort == "persoon":
                p = plan.personen_plan.get(w) or {}
                return next((ext[("oo", f"m:{m}")] for m in p.get("oo_medewerkers", [])
                             if ("oo", f"m:{m}") in ext), None) or p.get("bestaand")
        if soort == "persoon":
            return (plan.personen.get(w) or {}).get("bestaand")
        return None
    uit: dict[tuple[int, int, str], dict] = {}
    for r in plan.relaties:
        s, t = eindpunt(r["bron"]), eindpunt(r["doel"])
        if s and t:
            uit.setdefault((s, t, r["type"]), r)
    return uit


def lopende_verbanden(bron: str, conn) -> dict[int, dict]:
    rijen = conn.execute("""
        SELECT r.id, r.source_id, r.target_id, r.relation_type, c.page, c.section
        FROM relations r JOIN arguments a ON a.relation_id = r.id
        JOIN citations c ON c.argument_id = a.id JOIN sources s ON s.id = c.source_id
        WHERE c.methode = 'officieel_register_scrape' AND s.cluster_key = ?
          AND r.active_until IS NULL AND NOT r.vervangen AND r.status <> 'afgewezen'
          AND a.status <> 'verworpen'""", (f"register:{bron}",)).fetchall()
    uit: dict[int, dict] = {}
    for r in rijen:
        if not (r["section"] or "").startswith(LOPEND[bron]):
            continue
        v = uit.setdefault(r["id"], {"sleutel": (r["source_id"], r["target_id"], r["relation_type"]),
                                     "records": set()})
        v["records"].add((r["page"], r["section"]))
    return uit


def afgelopen(bron: str, uitgave: str, data: dict, plan, conn) -> tuple[list[dict], int]:
    gepland = geplande_verbanden(bron, plan, conn)
    lopend = lopende_verbanden(bron, conn)
    eind = []
    for rid, v in lopend.items():
        if v["sleutel"] in gepland or all(p.endswith("/" + uitgave) for p, _ in v["records"]):
            continue
        page, sectie = sorted(v["records"])[-1]
        rec = (data.get("records") or {}).get(sectie) or {}
        tot = rec.get("tot") if rec.get("tot") and len(str(rec["tot"])) >= 4 else uitgave
        eind.append({"id": rid, "active_until": tot,
                     "reden": f"{bron}: record {sectie} (uitgave {page.split('/', 1)[-1]}) levert in uitgave "
                              f"{uitgave} geen verband meer op" + (f"; einde volgens het record: {tot}" if tot != uitgave else "")})
    return eind, len(lopend)


def draai(*, droog: bool = False, alleen=BRONNEN, ophalen_aan: bool = True, meld=print, rest=None,
          check_rest=None) -> dict:
    uitkomst = {}
    if rest is None and not droog:
        rest = naar_model.Rest(IMPORT_TOKEN.read_text().strip(), API)
    if check_rest is None and not droog:
        check_rest = naar_model.Rest(CHECK_TOKEN.read_text().strip(), API)
    for bron in alleen:
        u = uitkomst[bron] = {}
        try:
            if ophalen_aan and not droog:
                ophalen(bron, meld)
            uitgave, data = nieuwste(bron)
        except Exception as e:  # noqa: BLE001 — een register dat stuk is, houdt de rest niet tegen
            u["fout"] = f"ophalen/lezen: {e}"
            meld(f"{bron}: {u['fout']}")
            continue
        u["uitgave"] = uitgave
        conn = db()
        try:
            plan = plan_voor(bron, data, conn)
            u["gepland"] = len(plan.relaties)
            if not droog:
                u["ingediend"] = indienen(bron, plan, rest, meld)
        finally:
            conn.close()
        conn = db()  # opnieuw: wat net is aangemaakt, bestaat nu
        try:
            plan = plan_voor(bron, data, conn)
            eind, n_lopend = afgelopen(bron, uitgave, data, plan, conn)
        finally:
            conn.close()
        u["lopend"], u["afgelopen"] = n_lopend, len(eind)
        if len(eind) > max(MIN_ONDERBREKER, MAX_AANDEEL * n_lopend):
            u["onderbreker"] = (f"{len(eind)} van {n_lopend} lopende verbanden zouden aflopen; "
                                f"niets afgesloten (controleer de uitgave {uitgave})")
            meld(f"{bron}: {u['onderbreker']}")
            continue
        for e in eind:
            if droog:
                meld(f"  (droog) #{e['id']} → {e['active_until']}: {e['reden']}")
                continue
            status, res = check_rest("POST", f"/api/relations/{e['id']}/looptijd",
                                     {"active_until": e["active_until"], "reden": e["reden"]})
            if status != 200:
                u.setdefault("fouten", []).append(f"#{e['id']}: {status} {res.get('error')}")
        meld(f"{bron}: uitgave {uitgave}, {u.get('gepland')} gepland, {n_lopend} lopend, {len(eind)} afgelopen")
        # 4. Looptijd: wat nieuw kwam (of nog geen datum had) krijgt het begin en eind uit zijn
        #    record; noemt het register geen begin, dan wordt dat vastgelegd (2026-10-09)
        import registers_looptijd  # noqa: PLC0415 — dat script importeert deze module
        u["looptijd"] = registers_looptijd.draai(droog=droog, alleen=[bron], meld=meld,
                                                 rest=check_rest,
                                                 data_per_bron={bron: (uitgave, data)})[bron]
    return uitkomst


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--droog", action="store_true", help="niets ophalen, indienen of afsluiten; laten zien wat")
    ap.add_argument("--alleen", default=",".join(BRONNEN))
    ap.add_argument("--zonder-ophalen", action="store_true", help="de nieuwste bewaarde uitgaven gebruiken")
    a = ap.parse_args()
    uit = draai(droog=a.droog, alleen=[b for b in a.alleen.split(",") if b in BRONNEN],
                ophalen_aan=not a.zonder_ophalen)
    print(json.dumps(uit, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
