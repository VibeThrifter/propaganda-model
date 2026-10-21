#!/usr/bin/env python3
"""Naamcontrole van persoonsknopen (2026-10-15): spelfouten opsporen vóór ze looptijden blokkeren.

Aanleiding: 'Bouke Geersing' (zo hoort 'Bauke') vond de datumzoeker in geen enkele bron, omdat
elke bron de juiste spelling schrijft. Deze controle wijst zulke knopen aan.

Deterministisch, zonder LLM, alleen lezend (geen schrijfactie op het model, geen voorstellen):
  1. Referentienamen uit bewaarde registeruitgaven: Wikidata (burgemeesters/wethouders), de Tweede
     Kamer (zetels) en het Europees Parlement (leden).
  2. Per goedgekeurde persoon (type 'persoon', niet vervangen of afgewezen):
     - **id**: de knoop hangt via een externe id (wikidata, tk_persoon, ep_mep) aan een
       registerpersoon, met dezelfde achternaam maar een andere voornaam → hoog vertrouwen;
     - **register**: dezelfde achternaam (met tussenvoegsel) en een voornaam op editafstand 1
       van de voornaam van een registerpersoon, terwijl de voornaam zelf nergens in het register
       met die achternaam voorkomt → midden;
     - **model**: dezelfde achternaam en voornaam op editafstand 1 van een andere persoonsknoop
       in het model (mogelijk dubbel of spelfout; geen bron die zegt wie goed is) → laag.
  3. Rapport: entiteit-id, naam, voorstel, reden, bron-record, vertrouwen. Alleen een voorstel, de
     hernoeming loopt via de gewone route (hernoemen-voorstel).

    python3 scripts/naamcontrole.py [--db PAD] [--uit PAD] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "registers"))
import common  # noqa: E402

DB = ROOT / "data" / "propaganda_model.db"
UIT = ROOT / "data" / "naamcontrole_rapport.json"
DATA = ROOT / "data" / "registers"
MIN_VOORNAAM = 4          # kortere voornamen geven te veel schijnparen (Jan/Jon, Ali/Ala)
TUSSEN = {"van", "de", "den", "der", "het", "te", "ten", "ter", "in", "op", "la", "le", "du",
          "von", "bin", "el", "al", "t", "'t", "d'"}


def editafstand(a: str, b: str) -> int:
    """Levenshtein (klein, stdlib)."""
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 2:
        return 3
    vorig = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        huidig = [i]
        for j, cb in enumerate(b, 1):
            huidig.append(min(vorig[j] + 1, huidig[j - 1] + 1, vorig[j - 1] + (ca != cb)))
        vorig = huidig
    return vorig[-1]


def splits(naam: str) -> tuple[str, str] | None:
    """'Bouke Geersing' → ('bouke', 'geersing'); 'Mark van der Berg' → ('mark', 'van der berg').
    Alleen namen met een echte voornaam (geen voorletters, geen aanhef); een toevoeging tussen
    haakjes ('(burgemeester X)') valt weg."""
    basis = re.sub(r"\([^)]*\)", " ", naam or "")
    n = common.ontleed_naam(basis)
    if n.get("voorletters") or not n.get("voornamen"):
        return None
    voor = common.sleutel(str(n["voornamen"]).split()[0])
    achter = common.sleutel(f"{n.get('tussenvoegsel') or ''} {n.get('achternaam') or ''}")
    if not voor or not achter or len(voor) < MIN_VOORNAAM:
        return None
    return voor, achter


def achternaam_van(tekst: str) -> str:
    return common.sleutel(tekst)


# ------------------------------------------------------------------ referentie
def _nieuwste(map_: Path, patroon: str) -> Path | None:
    g = sorted(map_.glob(patroon))
    return g[-1] if g else None


def lees_referentie(data: Path = DATA) -> dict:
    """→ {'achternaam': {achternaamsleutel: {voornaamsleutel: record}}, 'id': {(stelsel, id): record}}.
    record = {naam, bron} met bron als 'stelsel uitgave id'."""
    per_achter: dict[str, dict[str, dict]] = {}
    per_id: dict[tuple[str, str], dict] = {}

    def voeg(voornamen: list[str], achter: str, volledig: str, stelsel: str, uitgave: str, rid: str):
        achter_k = common.sleutel(achter)
        if not achter_k:
            return
        rec = {"naam": volledig, "bron": f"{stelsel} {uitgave} {rid}"}
        for v in voornamen:
            vk = common.sleutel(v)
            if vk:
                per_achter.setdefault(achter_k, {}).setdefault(vk, rec)
        per_id[(stelsel, str(rid))] = {**rec, "voornamen": [common.sleutel(v) for v in voornamen if v],
                                       "achternaam": achter_k}

    # Wikidata: label is de volledige naam; de eerste voornaam komt uit het label
    p = _nieuwste(data / "wikidata", "wikidata_????-??-??.json")
    if p:
        d = json.loads(p.read_text(encoding="utf-8"))
        uitgave = d.get("opgehaald", p.stem)
        for r in d.get("namen", []):
            label = (r.get("naam") or "").strip()
            qid = r["p"].rsplit("/", 1)[-1]
            n = common.ontleed_naam(label)
            if n.get("achternaam") and n.get("voornamen"):
                voeg([str(n["voornamen"]).split()[0]], f"{n.get('tussenvoegsel') or ''} {n['achternaam']}", label,
                     "wikidata", uitgave, qid)
    # Tweede Kamer: Persoon met Roepnaam, Voornamen, Tussenvoegsel, Achternaam
    p = _nieuwste(data / "tk", "tk_????-??-??.json")
    if p:
        d = json.loads(p.read_text(encoding="utf-8"))
        uitgave = d.get("opgehaald", p.stem)
        gezien = set()
        for z in d.get("zetels", []):
            pers = z.get("Persoon") or {}
            pid = pers.get("Id")
            if not pid or pid in gezien:
                continue
            gezien.add(pid)
            voor = [v for v in [pers.get("Roepnaam")] + (pers.get("Voornamen") or "").split() if v]
            # alleen roepnaam + eerste voornaam tellen als schrijfwijze van de voornaam
            voor = voor[:2]
            volledig = " ".join(x for x in [pers.get("Roepnaam") or (pers.get("Voornamen") or "").split(" ")[0],
                                            pers.get("Tussenvoegsel"), pers.get("Achternaam")] if x)
            voeg(voor, f"{pers.get('Tussenvoegsel') or ''} {pers.get('Achternaam') or ''}", volledig,
                 "tk_persoon", uitgave, pid)
    # Europees Parlement
    p = _nieuwste(data / "ep", "ep_????-??-??.json")
    if p:
        d = json.loads(p.read_text(encoding="utf-8"))
        uitgave = d.get("opgehaald", p.stem)
        for m in d.get("leden", []):
            voeg([m.get("voornaam") or ""], m.get("achternaam") or "",
                 f"{m.get('voornaam') or ''} {m.get('achternaam') or ''}".strip(), "ep_mep", uitgave,
                 str(m.get("id")))
    return {"achternaam": per_achter, "id": per_id}


# ------------------------------------------------------------------ controle
def controleer(conn, ref: dict) -> list[dict]:
    conn.row_factory = sqlite3.Row
    pers = [dict(r) for r in conn.execute(
        "SELECT id, name FROM entities WHERE type = 'persoon' AND status = 'goedgekeurd' "
        "AND NOT vervangen")]
    ids: dict[int, list[tuple[str, str]]] = {}
    for r in conn.execute("SELECT entity_id, stelsel, waarde FROM externe_ids "
                          "WHERE stelsel IN ('wikidata', 'tk_persoon', 'ep_mep')"):
        ids.setdefault(r["entity_id"], []).append((r["stelsel"], r["waarde"]))
    # Model: achternaam → {voornaam: [entiteit]}
    model: dict[str, dict[str, list[dict]]] = {}
    gesplitst = {}
    for e in pers:
        s = splits(e["name"])
        if s:
            gesplitst[e["id"]] = s
            model.setdefault(s[1], {}).setdefault(s[0], []).append(e)

    gevonden: dict[int, dict] = {}

    def meld(e, voorstel, reden, bron, vertrouwen):
        rang = {"hoog": 3, "midden": 2, "laag": 1}
        oud = gevonden.get(e["id"])
        if oud and rang[oud["vertrouwen"]] >= rang[vertrouwen]:
            return
        gevonden[e["id"]] = {"entiteit_id": e["id"], "naam": e["name"], "voorstel": voorstel,
                             "reden": reden, "bron": bron, "vertrouwen": vertrouwen}

    for e in pers:
        s = gesplitst.get(e["id"])
        # 1. id: dezelfde persoon in een register, dezelfde achternaam, andere voornaam
        for sleutel_id in ids.get(e["id"], []):
            r = ref["id"].get(sleutel_id)
            if not r:
                continue
            nm = splits(e["name"])
            if not nm:
                continue
            voor, achter = nm
            if achter == r["achternaam"] and voor not in r["voornamen"] and r["voornamen"]:
                dichtst = min(r["voornamen"], key=lambda v: editafstand(voor, v))
                if editafstand(voor, dichtst) <= 2:
                    meld(e, r["naam"], f"zelfde {sleutel_id[0]}-id, voornaam '{voor}' wijkt af van "
                         f"'{dichtst}'", r["bron"], "hoog")
        if not s:
            continue
        voor, achter = s
        # 2. register: voornaam op editafstand 1, zelf nergens in het register met die achternaam
        bekend = ref["achternaam"].get(achter, {})
        if bekend and voor not in bekend:
            kand = sorted((v for v in bekend if len(v) >= MIN_VOORNAAM and editafstand(voor, v) == 1))
            if len(kand) == 1:
                rec = bekend[kand[0]]
                meld(e, rec["naam"], f"voornaam '{voor}' staat niet in het register bij '{achter}'; "
                     f"'{kand[0]}' wel (editafstand 1)", rec["bron"], "midden")
        # 3. model: ander model-persoon met dezelfde achternaam en voornaam op editafstand 1
        for v2, ents in model.get(achter, {}).items():
            if v2 != voor and len(v2) >= MIN_VOORNAAM and editafstand(voor, v2) == 1:
                for e2 in ents:
                    if e2["id"] != e["id"] and e["id"] < e2["id"]:
                        meld(e, e2["name"], f"model: '{voor}' en '{v2}' met achternaam '{achter}' "
                             f"liggen één letter uit elkaar (mogelijk dubbel of spelfout)",
                             f"entiteit #{e2['id']}", "laag")
        # 4. achternaam: zelfde voornaam, achternaam op editafstand 1 van een registerachternaam
        #    (alleen als de eigen achternaam nergens in het register staat)
        if achter not in ref["achternaam"] and len(achter) >= 6:
            for a2, voornamen in ref["achternaam"].items():
                if voor in voornamen and abs(len(a2) - len(achter)) <= 1 and editafstand(achter, a2) == 1:
                    rec = voornamen[voor]
                    meld(e, rec["naam"], f"achternaam '{achter}' staat niet in het register; '{a2}' met "
                         f"voornaam '{voor}' wel (editafstand 1)", rec["bron"], "midden")
                    break
    rang = {"hoog": 0, "midden": 1, "laag": 2}
    return sorted(gevonden.values(), key=lambda r: (rang[r["vertrouwen"]], r["entiteit_id"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--uit", default=str(UIT))
    ap.add_argument("--json", action="store_true", help="rapport op stdout als JSON")
    a = ap.parse_args()
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    try:
        rapport = controleer(conn, lees_referentie())
    finally:
        conn.close()
    Path(a.uit).write_text(json.dumps({"verdacht": rapport, "aantal": len(rapport)},
                                      ensure_ascii=False, indent=1), encoding="utf-8")
    if a.json:
        print(json.dumps(rapport, ensure_ascii=False, indent=1))
    else:
        print(f"Naamcontrole: {len(rapport)} verdachte namen → {a.uit}")
        for r in rapport:
            print(f"  [{r['vertrouwen']}] #{r['entiteit_id']} {r['naam']} → {r['voorstel']}: {r['reden']} ({r['bron']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
