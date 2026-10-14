"""Wikidata (query.wikidata.org) — volledige namen bij voorletters (plan fase 3f, 2026-10-13).

Het register van overheidsorganisaties noemt burgemeesters en wethouders vrijwel alleen met
voorletters ("B.C.M. Vostermans") of alleen een achternaam ("Dhr. Fortuin"). Wikidata kent veel
van hen met hun volledige naam en een vast id (QID) via de functie die ze bekleden: P39 met een
ambt dat een subklasse is van 'Nederlands burgemeester' (Q13423499) of 'wethouder' (Q20748682)
en een gemeente als rechtsgebied (P1001), met de CBS-gemeentecode (P382). Deze module haalt die
lijst op als een bewaarde uitgave (data/registers/wikidata/wikidata_<datum>.json + .sha256),
net als de andere registers, en zoekt bij een registerrecord de ene Wikidata-persoon die past.

Koppelen (nooit op naam alleen, plan fase 3: "Wikidata alleen voor naam en id"):
  - dezelfde gemeente (CBS-code uit de TOOI-code van de gemeente, 'gm1894' → '1894'),
  - dezelfde functie (burgemeester, ook waarnemend, of wethouder),
  - dezelfde achternaam (met tussenvoegsel; een dubbele naam mag met het eerste deel
    overeenkomen, in het register of in Wikidata: 'van Beukering' ~ 'van Beukering-Huijbregts'),
  - de voorletters passen: de voornamen in Wikidata (P735) geven precies die voorletters, of de
    eerste letter van de naam (de roepnaam) is een van de voorletters ('A.J.' ~ 'Judith');
    met alleen een achternaam in het register moet het ambt volgens Wikidata nog lopen;
  - het ambt loopt volgens Wikidata nog, of eindigde niet vóór het begin dat het register noemt
    (een open einde in Wikidata zegt niet dat iemand nog zit; het register zegt dat);
  - precies één kandidaat, en in het register precies één record met die gemeente, functie en
    achternaam. Anders geen naam.
Wikidata levert alleen de naam en het id; het ambt zelf blijft een feit uit het register.

Geen schrijfacties op het model.

Gebruik:
    python3 tools/registers/wikidata.py haal
    python3 tools/registers/wikidata.py lees
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "wikidata"
URL = "https://query.wikidata.org/sparql"
MAP = DATA / BRON
TITEL = "Wikidata, burgemeesters en wethouders van Nederlandse gemeenten (SPARQL), uitgave {uitgave}"
UITGEVER = "Wikimedia Foundation (Wikidata)"
UA = "propagandamodel-registers/1.0 (onderzoek; https://www.wikidata.org/wiki/Wikidata:Data_access)"
SOORTEN = {"Q13423499": "burgemeester", "Q20748682": "wethouder"}
SINDS = "2014-01-01"   # oudere ambten (die al eindigden) doen voor de huidige registers niet ter zake

# Twee vragen: eerst de ambten (snel), dan per blok van personen hun naam en voornamen
QUERY_AMBTEN = """
SELECT ?p ?cls ?cbs ?start ?eind WHERE {
  VALUES ?cls { %s }
  ?pos wdt:P279 ?cls ; wdt:P1001 ?gem .
  ?gem wdt:P382 ?cbs .
  ?st ps:P39 ?pos . ?p p:P39 ?st .
  OPTIONAL { ?st pq:P580 ?start }
  OPTIONAL { ?st pq:P582 ?eind }
  FILTER(!BOUND(?eind) || ?eind >= "%sT00:00:00Z"^^xsd:dateTime)
}""" % (" ".join(f"wd:{q}" for q in SOORTEN), SINDS)
QUERY_NAMEN = """
SELECT ?p ?naam ?ord ?voornaam WHERE {
  VALUES ?p { %s }
  ?p wdt:P31 wd:Q5 .
  ?p rdfs:label ?naam . FILTER(LANG(?naam) = "nl")
  OPTIONAL { ?p p:P735 ?vs . ?vs ps:P735 ?vn . OPTIONAL { ?vs pq:P1545 ?ord }
             ?vn rdfs:label ?voornaam . FILTER(LANG(?voornaam) IN ("nl", "mul")) }
}"""
BLOK = 300


class FormaatFout(Exception):
    """De uitgave mist velden die deze lezer verwacht."""


def _sparql(query: str) -> list[dict]:
    body = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "User-Agent": UA, "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=120) as r:
        ruw = json.loads(r.read().decode("utf-8"))
    return [{k: v["value"] for k, v in b.items()} for b in ruw["results"]["bindings"]]


def haal() -> Path:
    ambten = _sparql(QUERY_AMBTEN)
    qids = sorted({_qid(a["p"]) for a in ambten})
    namen = []
    for i in range(0, len(qids), BLOK):
        namen += _sparql(QUERY_NAMEN % " ".join(f"wd:{q}" for q in qids[i:i + BLOK]))
    data = {"bron": BRON, "opgehaald": date.today().isoformat(),
            "query_ambten": QUERY_AMBTEN, "query_namen": QUERY_NAMEN,
            "ambten": sorted(ambten, key=lambda r: (r["p"], r["cls"], r["cbs"], r.get("start", ""))),
            "namen": sorted(namen, key=lambda r: (r["p"], r.get("ord", ""), r.get("voornaam", "")))}
    MAP.mkdir(parents=True, exist_ok=True)
    pad = MAP / f"wikidata_{data['opgehaald']}.json"
    pad.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (MAP / f"wikidata_{data['opgehaald']}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("wikidata_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"wikidata_{uitgave}.json"


def _qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def _voorletters_uit(voornamen: list[tuple[str | None, str]]) -> str | None:
    """[('1', 'Bob'), ('2', 'Cornelis')] → 'BC'; meer dan één voornaam zonder volgorde (P1545):
    None (dan is de volgorde van de voorletters niet te zeggen)."""
    delen = sorted({(o or "", n.strip()) for o, n in voornamen if n and n.strip()})
    if not delen:
        return None
    if len(delen) > 1 and any(not o for o, _ in delen):
        return None
    try:
        delen.sort(key=lambda d: int(d[0] or 0))
    except ValueError:
        return None
    return "".join(n[:1].upper() for _, n in delen)


def lees(pad: Path) -> dict:
    """→ {bron, uitgave, sha256, personen{qid: {qid, naam, voorletters}}, ambten[{qid, soort, cbs,
    start, eind}]}. Alleen mensen (P31 Q5) met een Nederlandse naam."""
    ruw = json.loads(pad.read_text(encoding="utf-8"))
    for veld in ("ambten", "namen"):
        if veld not in ruw:
            raise FormaatFout(f"veld '{veld}' ontbreekt in {pad.name}")
    voornamen: dict[str, list] = {}
    personen = {}
    for r in ruw["namen"]:
        qid = _qid(r["p"])
        personen.setdefault(qid, {"qid": qid, "naam": schoon(r["naam"]), "voorletters": None})
        if r.get("voornaam"):
            voornamen.setdefault(qid, []).append((r.get("ord"), r["voornaam"]))
    for qid, p in personen.items():
        p["voorletters"] = _voorletters_uit(voornamen.get(qid, []))
    ambten = [{"qid": _qid(a["p"]), "soort": SOORTEN.get(_qid(a["cls"])), "cbs": a["cbs"].lstrip("0"),
               "start": (a.get("start") or "")[:10] or None, "eind": (a.get("eind") or "")[:10] or None}
              for a in ruw["ambten"] if _qid(a["p"]) in personen]
    return {"bron": BRON, "uitgave": ruw["opgehaald"], "sha256": sha256_bestand(pad), "bestand": str(pad),
            "url": URL, "titel": TITEL.format(uitgave=ruw["opgehaald"]), "personen": personen,
            "ambten": ambten}


def nieuwste() -> dict | None:
    return lees(uitgaven()[-1]) if uitgaven() else None


# ── Koppelen ───────────────────────────────────────────────────────────────
def cbs_van(tooi: str | None) -> str | None:
    """TOOI-code van een gemeente ('gm1894' of 'oorg…'): alleen een gm-code geeft een CBS-code."""
    m = re.match(r"^gm0*(\d+)$", tooi or "")
    return m.group(1) if m else None


def soort_van(functie: str) -> str | None:
    f = functie.lower()
    if f.startswith("burgemeester"):
        return "burgemeester"
    if f.startswith("wethouder"):
        return "wethouder"
    return None


def _achternaam_past(label: str, naam: dict) -> bool:
    """Eindigt de Wikidata-naam op de achternaam uit het register (met tussenvoegsel)? Een dubbele
    naam ('Keijzer - Broers') mag met het geheel of met het eerste deel overeenkomen."""
    lab = sleutel(label)
    achter = sleutel(f"{naam.get('tussenvoegsel') or ''} {naam.get('achternaam') or ''}")
    if not achter:
        return False
    vormen = {achter}
    if "-" in (naam.get("achternaam") or ""):
        eerste = (naam["achternaam"].split("-")[0]).strip()
        vormen.add(sleutel(f"{naam.get('tussenvoegsel') or ''} {eerste}"))
    return any((lab.endswith(" " + v) and len(lab) > len(v)) or f" {v} " in f" {lab_dubbel} "
               for v in vormen for lab_dubbel in [_eerste_deel(label)])


def _eerste_deel(label: str) -> str:
    """'Marijke van Beukering-Huijbregts' → 'marijke van beukering' (de naam tot het koppelteken
    van een dubbele achternaam); zonder koppelteken een lege string."""
    return sleutel(label.split("-")[0]) if "-" in label else ""


def _voorletters_passen(persoon: dict, label: str, naam: dict) -> bool:
    reg = (naam.get("voorletters") or "").replace(".", "").upper()
    reg = re.sub(r"[^A-ZÀ-Ý]", "", reg)
    if not reg:
        return True  # alleen een achternaam in het register: de andere eisen moeten het doen
    if persoon.get("voorletters") and persoon["voorletters"] == reg:
        return True
    eerste = sleutel(label)[:1].upper()
    return bool(eerste) and eerste in reg


def index(wd: dict) -> dict[tuple[str, str], list[dict]]:
    """(cbs, soort) → [{qid, naam, voorletters, start, eind}]."""
    uit: dict[tuple[str, str], list[dict]] = {}
    for a in wd["ambten"]:
        if not a["soort"]:
            continue
        p = wd["personen"][a["qid"]]
        uit.setdefault((a["cbs"], a["soort"]), []).append({**p, "start": a["start"], "eind": a["eind"]})
    return uit


def kandidaten(idx: dict, cbs: str, soort: str, naam: dict, sinds: str | None, uitgave: str) -> list[dict]:
    """De Wikidata-personen die bij dit registerrecord passen (zie de koppelregels bovenaan);
    één persoon per QID."""
    grens = sinds or uitgave
    uit = {}
    for k in idx.get((cbs, soort), []):
        if not _achternaam_past(k["naam"], naam) or not _voorletters_passen(k, k["naam"], naam):
            continue
        if k["eind"] and k["eind"] < grens:
            continue
        if naam.get("alleen_achternaam") and k["eind"]:
            continue  # alleen een achternaam: het ambt moet volgens Wikidata nog lopen
        uit[k["qid"]] = k
    return list(uit.values())


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Wikidata-uitgave ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--uitgave")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal())
    else:
        d = lees(pad_van(a.uitgave) if a.uitgave else uitgaven()[-1])
        print(json.dumps({"uitgave": d["uitgave"], "personen": len(d["personen"]),
                          "ambten": len(d["ambten"])}, ensure_ascii=False))
