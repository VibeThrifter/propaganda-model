"""Nevenfunctieregister van de Rechtspraak, via Open Rechtspraak — uitgave ophalen en lezen
(eigenaar 2026-10-19).

Rechters, raadsheren en hun plaatsvervangers melden hun nevenbetrekkingen in het
nevenfunctieregister van de Rechtspraak (rechtspraak.nl/registers/nevenfunctieregister). Dat
register is alleen per persoon te raadplegen. Open Rechtspraak (openrechtspraak.nl, Open State
Foundation) haalt het dagelijks over en maakt het doorzoekbaar:
  - /api/v1/person (JSON, 100 per pagina): naam, het id in het register (`rechtspraak_id`), de
    beroepsgegevens binnen en buiten de rechterlijke macht, met begin en einde;
  - /person/<id> (html): daarnaast de huidige en vroegere nevenbetrekkingen (functie, instantie,
    soort instantie, betaald of onbetaald, begin en einde). Die staan niet in de API.
  - /sitemap.xml: per persoon wanneer Open Rechtspraak het register voor het laatst las.
Alleen wie nu in het register staat (geen oud-rechters). Plaats van een nevenfunctie,
adressen en contactgegevens worden nooit bewaard.

De uitgave is één json-bestand: data/registers/rechtspraak/rechtspraak_<ophaaldatum>.json
(+ .sha256). Een record is een rechter ('persoon:<rechtspraak_id>'), een nevenbetrekking
('nevenfunctie:<hash>') of een functie buiten de rechtspraak ('loopbaan:<hash>'); de hash hangt
alleen af van persoon, functie, instantie en begin, dus een dubbel getoonde nevenbetrekking is
één record. De recordregel is het citaat.

Geen schrijfacties op het model (dat doet rechtspraak_naar_model.py via de REST-API).

    python3 tools/registers/rechtspraak.py haal [--max N]
    python3 tools/registers/rechtspraak.py lees
"""
from __future__ import annotations

import datetime
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, UA, noemt, ontleed_naam, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "rechtspraak"
BASIS = "https://openrechtspraak.nl"
URL = "https://www.rechtspraak.nl/registers/nevenfunctieregister"
MAP = DATA / BRON
UITGEVER = "De Rechtspraak (nevenfunctieregister), ontsloten door Open Rechtspraak (Open State Foundation)"
TITEL = ("Nevenfunctieregister van de Rechtspraak, zoals ontsloten door Open Rechtspraak "
         "(openrechtspraak.nl, Open State Foundation), opgehaald {uitgave}")
PAUZE = 1.1   # seconden tussen verzoeken
PER_PAGINA = 100


class FormaatFout(Exception):
    """De uitgave of de pagina heeft niet het verwachte formaat."""


def _get(url: str, timeout: int = 60) -> str:
    for poging in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404 or poging == 3:
                raise
            time.sleep(30 * (poging + 1) if e.code in (429, 503) else 5)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if poging == 3:
                raise
            time.sleep(10)
    raise FormaatFout(f"niet op te halen: {url}")


def _datum(waarde: str | None) -> str | None:
    """'2013-05-01T00:00:00' of '01-05-2013' → '2013-05-01'."""
    w = (waarde or "").strip()
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", w)
    if m:
        return m.group(1)
    m = re.match(r"^(\d{2})-(\d{2})-(\d{4})$", w)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


# ── de detailpagina (alleen de nevenbetrekkingen) ───────────────────────────
_KAART = re.compile(r'<div class="col-lg-6 mb-3" id="([0-9a-f-]{36})">(.*?)</div>\s*</div>\s*</div>', re.S)


def _tekst(fragment: str) -> str:
    return schoon(html.unescape(re.sub(r"<[^>]+>", " ", fragment or "")))


def lees_pagina(pagina: str) -> dict:
    """De nevenbetrekkingen van één persoonspagina: {'huidig': [...], 'historisch': [...]}.
    Per kaart: functie (h5), begin/einde, instantie (primaire badge), soort instantie
    (secundaire badge), betaald ('Betaald'/'Onbetaald'). De plaats wordt niet bewaard."""
    uit = {"huidig": [], "historisch": []}
    kop = re.search(r"<h2[^>]*>\s*Nevenbetrekkingen\s*</h2>", pagina)
    if not kop:
        raise FormaatFout("geen kop 'Nevenbetrekkingen' op de persoonspagina")
    rest = pagina[kop.end():]
    hist = re.search(r"<h2[^>]*>\s*Historische nevenbetrekkingen\s*</h2>", rest)
    einde = re.search(r'<div class="col-lg-4">', rest)
    delen = {"huidig": rest[:hist.start()] if hist else rest[:einde.start() if einde else None],
             "historisch": rest[hist.end():einde.start() if einde else None] if hist else ""}
    for soort, deel in delen.items():
        for kid, kaart in _KAART.findall(deel + "</div></div></div>"):
            functie = _tekst((re.search(r"<h5>(.*?)</h5>", kaart, re.S) or [None, ""])[1])
            badges = re.findall(r'<span class="badge rounded-pill ([^"]*)"[^>]*>(.*?)</span>', kaart, re.S)
            instantie = next((_tekst(t) for k, t in badges if "bg-primary" in k), "")
            soort_inst = next((_tekst(t) for k, t in badges if "bg-secondary" in k), "")
            betaald = next((_tekst(t) for k, t in badges if "bg-warning" in k or "bg-success" in k), "")
            start = re.search(r'class="start-date">([^<]*)<', kaart)
            eind = re.search(r'class="end-date">([^<]*)<', kaart)
            uit[soort].append({"id": kid, "functie": functie, "instantie": instantie,
                               "soort_instantie": soort_inst, "betaald": betaald,
                               "van": _datum(start.group(1)) if start else None,
                               "tot": _datum(eind.group(1)) if eind else None})
    return uit


# ── ophalen ─────────────────────────────────────────────────────────────────
def uitgaven() -> list[Path]:
    return sorted(MAP.glob("rechtspraak_????-??-??.json"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"rechtspraak_{uitgave}.json"


def _lijst(meld=print) -> list[dict]:
    personen, offset, totaal = [], 0, None
    while totaal is None or offset < totaal:
        d = json.loads(_get(f"{BASIS}/api/v1/person?limit={PER_PAGINA}&offset={offset}"))
        totaal = d["count"]
        if not d["data"]:
            break
        personen.extend(d["data"])
        offset += PER_PAGINA
        if offset // PER_PAGINA % 10 == 0:
            meld(f"  lijst: {len(personen)}/{totaal}")
        time.sleep(PAUZE)
    if len(personen) < totaal:
        raise FormaatFout(f"lijst onvolledig: {len(personen)} van {totaal}")
    return personen


def _sitemap() -> dict[str, str]:
    xml = _get(f"{BASIS}/sitemap.xml", timeout=120)
    return {m.group(1): m.group(2)[:10] for m in re.finditer(
        r"<loc>[^<]*/person/([0-9a-f-]{36})</loc>\s*<lastmod>([^<]+)</lastmod>", xml)}


def haal(max_n: int | None = None, meld=print) -> Path:
    """Lijst + sitemap + per persoon met nevenbetrekkingen de detailpagina. Hervat na een
    onderbreking (data/registers/rechtspraak/_bezig.json bewaart de gelezen pagina's)."""
    MAP.mkdir(parents=True, exist_ok=True)
    bezig_pad = MAP / "_bezig.json"
    bezig = json.loads(bezig_pad.read_text(encoding="utf-8")) if bezig_pad.exists() else {}
    if bezig.get("datum") != datetime.date.today().isoformat():
        bezig = {"datum": datetime.date.today().isoformat(), "paginas": {}}
    personen = _lijst(meld)
    time.sleep(PAUZE)
    gelezen = _sitemap()
    nodig = [p for p in personen if p.get("has_no_side_jobs") is not True
             and p.get("did_not_self_report_side_jobs") is not True and p["id"] not in bezig["paginas"]]
    if max_n is not None:
        nodig = nodig[:max_n]
    meld(f"{len(personen)} personen, {len(nodig)} detailpagina's te lezen "
         f"({len(bezig['paginas'])} al gelezen)")
    for i, p in enumerate(nodig, 1):
        time.sleep(PAUZE)
        try:
            bezig["paginas"][p["id"]] = lees_pagina(_get(f"{BASIS}/person/{p['id']}"))
        except urllib.error.HTTPError as e:
            bezig["paginas"][p["id"]] = {"fout": e.code}
        if i % 50 == 0 or i == len(nodig):
            bezig_pad.write_text(json.dumps(bezig, ensure_ascii=False), encoding="utf-8")
            meld(f"  pagina's: {i}/{len(nodig)}")
    uitgave = bezig["datum"]
    for p in personen:
        p["nevenbetrekkingen"] = bezig["paginas"].get(p["id"])
        p["bijgewerkt"] = gelezen.get(p["id"])
    pad = pad_van(uitgave)
    pad.write_text(json.dumps({"bron": BRON, "uitgave": uitgave, "opgehaald": uitgave,
                               "volledig": max_n is None, "personen": personen},
                              ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    (MAP / f"rechtspraak_{uitgave}.sha256").write_text(sha256_bestand(pad) + "\n")
    if max_n is None:
        bezig_pad.unlink(missing_ok=True)
    return pad


# ── lezen ───────────────────────────────────────────────────────────────────
def _hash(*delen) -> str:
    return hashlib.sha1("|".join(sleutel(d or "") for d in delen).encode()).hexdigest()[:16]


def _periode(van: str | None, tot: str | None) -> str:
    if van and tot:
        return f"{van} tot {tot}"
    if van:
        return f"sinds {van}"
    return f"tot {tot}" if tot else "zonder datum"


def huidige_functies(p: dict) -> list[dict]:
    return [d for d in p.get("professional_details") or []
            if not d.get("end_date") and not d.get("outside_of_judiciary")]


def lees(pad: Path) -> dict:
    ruw = json.loads(pad.read_text(encoding="utf-8"))
    uitgave = ruw["uitgave"]
    records: dict[str, dict] = {}
    for p in ruw["personen"]:
        rid = p["rechtspraak_id"]
        naam = schoon(p["toon_naam"])
        functies = list(dict.fromkeys((schoon(d["function"]), schoon(d["organisation"]), _datum(d.get("start_date")))
                                      for d in huidige_functies(p)))  # Open Rechtspraak toont soms dubbel
        ambt = "; ".join(dict.fromkeys(f"{f}, {o}" for f, o, _ in functies)) or "geen huidige functie vermeld"
        n = ontleed_naam(naam)  # zonder titels achter de naam ('Marring RA' → 'Marring')
        basis = {"persoon_id": rid, "naam": naam, "initialen": p.get("initials"),
                 "achternaam": schoon(f"{n['tussenvoegsel'] or ''} {n['achternaam'] or ''}") or p.get("last_name"),
                 "functies": functies, "osf_id": p["id"]}
        records[f"persoon:{rid}"] = {
            **basis, "sleutel": f"persoon:{rid}", "soort": "persoon", "bijgewerkt": p.get("bijgewerkt"),
            "regel": f"Nevenfunctieregister Rechtspraak: {naam} · "
                     + "; ".join(f"{f}, {o} ({_periode(v, None)})" for f, o, v in functies)}
        for d in p.get("professional_details") or []:
            if not d.get("outside_of_judiciary"):
                continue
            f, o = schoon(d["function"]), schoon(d.get("organisation"))
            van, tot = _datum(d.get("start_date")), _datum(d.get("end_date"))
            s = f"loopbaan:{_hash(rid, f, o, van)}"
            records[s] = {**basis, "sleutel": s, "soort": "loopbaan", "functie": f, "instantie": o,
                          "van": van, "tot": tot,
                          "regel": f"Nevenfunctieregister Rechtspraak: {naam} ({ambt}) · beroepsgegeven buiten de "
                                   f"rechterlijke macht: {f} · instantie: {o} · {_periode(van, tot)}"}
        neven = p.get("nevenbetrekkingen") or {}
        for soort in ("huidig", "historisch"):
            for n in neven.get(soort, []):
                s = f"nevenfunctie:{_hash(rid, n['functie'], n['instantie'], n['van'])}"
                if s in records:
                    if n["soort_instantie"] and not records[s]["soort_instantie"]:
                        pass  # dubbel getoond; de eerste (vollediger) telt
                    continue
                betaald = {"betaald": "betaald", "onbetaald": "onbetaald"}.get(sleutel(n["betaald"]),
                                                                              "bezoldiging niet vermeld")
                records[s] = {**basis, "sleutel": s, "soort": "nevenfunctie", "huidig": soort == "huidig",
                              "functie": n["functie"], "instantie": n["instantie"],
                              "soort_instantie": n["soort_instantie"], "betaald": betaald,
                              "van": n["van"], "tot": n["tot"],
                              "regel": f"Nevenfunctieregister Rechtspraak: {naam} ({ambt}) · nevenbetrekking: "
                                       f"{n['functie']} · instantie: {n['instantie']}"
                                       + (f" ({n['soort_instantie']})" if n["soort_instantie"] else "")
                                       + f" · {betaald} · {_periode(n['van'], n['tot'])}"}
    if not records:
        raise FormaatFout("geen records gelezen")
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "volledig": ruw.get("volledig", True), "titel": TITEL.format(uitgave=uitgave), "records": records}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"rechtspraak_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


RELATIETYPES = {"bestuurder", "adviseur", "lidmaatschap", "personeel", "eigendom", "ambt"}


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """De ene kant is de rechter (externe id 'rechtspraak' = het id in het register, en de
    achternaam staat in de naam), de andere de instantie uit de recordregel."""
    if rec["soort"] not in ("nevenfunctie", "loopbaan") or relatie_type not in RELATIETYPES:
        return f"een rechtspraakfeit is een nevenbetrekking of loopbaan, niet '{relatie_type}'"
    rechter = [e for e in eindpunten if ("rechtspraak", rec["persoon_id"]) in e["ids"]]
    if not rechter:
        return f"geen eindpunt met externe id rechtspraak:{rec['persoon_id']}"
    if sleutel(rec.get("achternaam") or "") not in sleutel(rechter[0]["name"]):
        return f"de achternaam '{rec.get('achternaam')}' staat niet in '{rechter[0]['name']}'"
    ander = [e for e in eindpunten if e is not rechter[0]][0]
    from tk import schrijfwijzen
    namen = [ander["name"]] + [v for v, m in schrijfwijzen().items() if sleutel(m) == sleutel(ander["name"])]
    velden = (rec["instantie"], rec.get("functie") or "", rec.get("soort_instantie") or "")
    if not any(noemt(v, n) for v in velden for n in namen):
        return f"'{ander['name']}' staat niet in het record {sleutel_r}"
    return None


if __name__ == "__main__":
    import argparse
    from collections import Counter
    ap = argparse.ArgumentParser(description="Nevenfunctieregister Rechtspraak (Open Rechtspraak) ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    ap.add_argument("--max", type=int, default=None, help="hooguit N detailpagina's (proef)")
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal(a.max))
    else:
        d = lees(uitgaven()[-1])
        tel = Counter(r["soort"] for r in d["records"].values())
        tel["nevenfunctie lopend"] = sum(1 for r in d["records"].values() if r.get("huidig"))
        print(json.dumps({"uitgave": d["uitgave"], "volledig": d["volledig"], **tel}, ensure_ascii=False))
