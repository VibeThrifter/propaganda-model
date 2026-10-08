"""Lobbyistenregister van de Tweede Kamer — uitgave ophalen en lezen (Uitbreiding C, 2026-10-07).

Wie een vaste toegangspas tot de Tweede Kamer heeft, staat met naam, werkgever en de belangen die
hij behartigt in een pdf (tweedekamer.nl/contact_en_bezoek/lobbyisten). De pdf is de uitgave:
data/registers/lobby/lobby_<datum>.pdf (+ .sha256), datum = "Laatst bijgewerkt". De tabel wordt
deterministisch gelezen uit de woordposities (PyMuPDF): een nieuwe rij begint bij een naam in de
eerste kolom; een cel die doorloopt, hoort bij de rij erboven. De recordregel is het citaat.

Geen schrijfacties op het model (dat doet lobby_naar_model.py via de REST-API).
"""
from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, UA, schoon, sha256_bestand, sleutel  # noqa: E402

BRON = "lobby"
PAGINA = "https://www.tweedekamer.nl/contact_en_bezoek/lobbyisten"
URL = PAGINA
MAP = DATA / BRON
TITEL = "Tweede Kamer der Staten-Generaal, lobbyistenregister (vaste toegangspassen), bijgewerkt {uitgave}"
UITGEVER = "Tweede Kamer der Staten-Generaal"
KOLOMMEN = ("Naam", "Werkzaam bij / voor", "Behartigt belangen voor")


class FormaatFout(Exception):
    """De pdf heeft niet de verwachte tabel."""


def haal() -> Path:
    req = urllib.request.Request(PAGINA, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    m = re.search(r'href="([^"]*Lobbyistenregister[^"]*\.pdf)"', html)
    if not m:
        raise FormaatFout("geen pdf-link op de lobbyistenpagina")
    url = m.group(1) if m.group(1).startswith("http") else "https://www.tweedekamer.nl" + m.group(1)
    MAP.mkdir(parents=True, exist_ok=True)
    tijdelijk = MAP / "nieuw.pdf"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tijdelijk.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    uitgave = _bijgewerkt(tijdelijk)
    pad = MAP / f"lobby_{uitgave}.pdf"
    tijdelijk.replace(pad)
    (MAP / f"lobby_{uitgave}.sha256").write_text(sha256_bestand(pad) + "\n")
    return pad


def _woorden(pad: Path) -> list[tuple[int, float, float, str]]:
    import fitz  # PyMuPDF; alleen hier nodig
    uit = []
    with fitz.open(pad) as doc:
        for pno, page in enumerate(doc):
            for x0, y0, _x1, _y1, w, *_ in page.get_text("words"):
                uit.append((pno, round(y0), x0, w))
    return uit


def _bijgewerkt(pad: Path) -> str:
    tekst = " ".join(w for *_, w in _woorden(pad))
    m = re.search(r"Laatst bijgewerkt:\s*(\d{2})-(\d{2})-(\d{4})", tekst)
    if not m:
        raise FormaatFout("geen 'Laatst bijgewerkt'-datum in de pdf")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"


def uitgaven() -> list[Path]:
    return sorted(MAP.glob("lobby_????-??-??.pdf"))


def pad_van(uitgave: str) -> Path:
    return MAP / f"lobby_{uitgave}.pdf"


def _rijen(pad: Path) -> list[dict]:
    woorden = _woorden(pad)
    kop = [(pno, y, x, w) for pno, y, x, w in woorden if w in ("Naam", "Werkzaam", "Behartigt")]
    if len({w for *_, w in kop}) < 3:
        raise FormaatFout("kolomkoppen niet gevonden")
    grens1 = min(x for *_, x, w in kop if w == "Werkzaam") - 4
    grens2 = min(x for *_, x, w in kop if w == "Behartigt") - 4
    regels: dict[tuple[int, int], list[tuple[float, str]]] = {}
    for pno, y, x, w in woorden:
        regels.setdefault((pno, y), []).append((x, w))
    rijen, huidig = [], None
    for (pno, y) in sorted(regels):
        cellen = ["", "", ""]
        for x, w in sorted(regels[(pno, y)]):
            k = 0 if x < grens1 else (1 if x < grens2 else 2)
            cellen[k] = f"{cellen[k]} {w}".strip()
        if cellen[0] in ("Naam",) or cellen[0].startswith("Laatst bijgewerkt"):
            continue
        if cellen[0]:
            huidig = {"naam": cellen[0], "werkzaam": cellen[1], "belangen": cellen[2]}
            rijen.append(huidig)
        elif huidig:
            for k, veld in ((1, "werkzaam"), (2, "belangen")):
                if cellen[k]:
                    huidig[veld] = f"{huidig[veld]} {cellen[k]}".strip()
    return rijen


def lees(pad: Path) -> dict:
    uitgave = _bijgewerkt(pad)
    records = {}
    for r in _rijen(pad):
        r = {k: schoon(v) for k, v in r.items()}
        s = f"lobbyist:{sleutel(r['naam']).replace(' ', '-')}"
        rec = {**r, "sleutel": s, "soort": "lobbyist",
               "regel": f"Tweede Kamer · lobbyistenregister (vaste toegangspas): {r['naam']} · werkzaam bij / voor: "
                        f"{r['werkzaam']} · behartigt belangen voor: {r['belangen']}"}
        if s in records:
            raise FormaatFout(f"dubbele naam in het register: {r['naam']}")
        records[s] = rec
    if not records:
        raise FormaatFout("geen rijen gelezen")
    return {"bron": BRON, "uitgave": uitgave, "sha256": sha256_bestand(pad), "bestand": str(pad), "url": URL,
            "titel": TITEL.format(uitgave=uitgave), "records": records}


_CACHE: dict[str, dict] = {}


def lees_uitgave(uitgave: str) -> dict | None:
    if uitgave in _CACHE:
        return _CACHE[uitgave]
    pad = pad_van(uitgave)
    if not pad.exists():
        return None
    vast = MAP / f"lobby_{uitgave}.sha256"
    if vast.exists() and vast.read_text().strip() != sha256_bestand(pad):
        raise FormaatFout(f"sha256 van uitgave {uitgave} klopt niet meer met het vastgelegde")
    _CACHE[uitgave] = lees(pad)
    return _CACHE[uitgave]


def record(uitgave: str, sleutel_r: str) -> dict | None:
    data = lees_uitgave(uitgave)
    return None if data is None else data["records"].get(sleutel_r)


def controleer(data: dict, sleutel_r: str, rec: dict, relatie_type: str,
               eindpunten: list[dict]) -> str | None:
    """De ene kant is de Tweede Kamer (oo:19432), de andere staat in de recordregel."""
    from tk import schrijfwijzen
    from common import noemt
    kamer = [e for e in eindpunten if ("oo", "19432") in e["ids"]]
    if relatie_type != "lobbyt" or not kamer:
        return "een lobbyfeit is 'lobbyt' met de Tweede Kamer als doel"
    ander = [e for e in eindpunten if e is not kamer[0]][0]
    namen = [ander["name"]] + [v for v, m in schrijfwijzen().items() if sleutel(m) == sleutel(ander["name"])]
    if not any(noemt(rec["regel"], n) for n in namen):
        return f"'{ander['name']}' staat niet in het record {sleutel_r}"
    return None


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser(description="Lobbyistenregister ophalen/lezen")
    ap.add_argument("actie", choices=["haal", "lees"])
    a = ap.parse_args()
    if a.actie == "haal":
        print(haal())
    else:
        d = lees(uitgaven()[-1])
        for r in d["records"].values():
            print(f"{r['naam']:<22} | {r['werkzaam'][:34]:<34} | {r['belangen'][:80]}")
        print(json.dumps({"uitgave": d["uitgave"], "lobbyisten": len(d["records"])}))
