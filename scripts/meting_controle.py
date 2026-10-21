#!/usr/bin/env python3
"""Blinde controle van een eigen meting door een agent (eigenaarsbesluit 2026-10-16).

Punt d van de journalistieke codes eist dat minstens 20% van de waarnemingen (minimaal 5, of
alle bij minder dan 5) blind opnieuw gecodeerd is door een ander account dan de invoerder. Een
eigenaar die alleen werkt, kan dat door deze agent laten doen: account `metingcontrole`
(bijdrager), Claude Sonnet via de `claude`-CLI, zoals de bronchecker.

Blind: de agent haalt zijn steekproef uit GET /api/metingen/<id>/controle. Dat geeft per
waarneming de url, de datum, het medium, wie er geciteerd wordt, het citaat en de vragen met hun
opties, maar NIET de eerste codering; de volgorde is per account willekeurig, dus de agent neemt
gewoon de eerste uit de lijst. Hij leest het artikel (de url, dan de archiefkopie, dan de
Wayback Machine) en beantwoordt elke vraag met één van de opties. Met ``--indienen`` gaat dat
naar POST /api/metingen/<id>/waarnemingen/<wid>/controle; daarna toont de meting de
overeenstemming per vraag (percentage en Cohen's kappa).

Standaard een droogloop: de codes worden getoond, niet ingediend (het model wordt wel gevraagd).
Draait niet in de uurronde; de eigenaar start het zelf:
    python3 scripts/meting_controle.py --meting 3              # droogloop
    python3 scripts/meting_controle.py --meting 3 --indienen   # echt
    python3 scripts/meting_controle.py --meting 3 --aantal 10 --indienen
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _pad in (ROOT, ROOT / "scripts"):
    if str(_pad) not in sys.path:
        sys.path.append(str(_pad))
import bronchecker  # noqa: E402  (ophalen, citaat terugzoeken, model aanroepen)
import metingcheck  # noqa: E402  (HTTP-verstuurder)

ACCOUNT = "metingcontrole"
TOKEN = ROOT / "data" / "tokens" / f"{ACCOUNT}.token"
API = "http://127.0.0.1:5000"
MODEL = "sonnet"
FRAGMENT_TEKENS = 2500      # tekst rond het citaat die het model ziet (elke kant)

SYSTEEM = (
    "Je codeert een citaat uit een Nederlands nieuwsartikel voor een inhoudsanalyse. Je ziet het "
    "artikel (of een fragment rond het citaat), wie er geciteerd wordt, het citaat, en een paar "
    "vragen met hun antwoordopties. Beantwoord elke vraag met precies één van de gegeven opties, "
    "uitsluitend op grond van wat er in het artikel staat. Voeg geen kennis van buiten het artikel "
    "toe en geef geen eigen oordeel over de inhoud. Antwoord alleen met het gevraagde JSON.")


def schema_voor(vragen: list[dict]) -> dict:
    return {
        "type": "object",
        "properties": {
            "codes": {"type": "object",
                      "properties": {v["sleutel"]: {"type": "string", "enum": list(v["opties"])}
                                     for v in vragen},
                      "required": [v["sleutel"] for v in vragen],
                      "additionalProperties": False},
            "toelichting": {"type": "string"},
        },
        "required": ["codes", "toelichting"],
        "additionalProperties": False,
    }


def fragment_van(w: dict, haal=None) -> tuple[str | None, str]:
    """(tekst rond het citaat, toelichting). None als het artikel niet te lezen is."""
    tekst, toelichting, gebruikt = (haal or bronchecker.haal_bron)(
        {"url": w["url"], "archive_url": w.get("archief_url")}, w["citaat"])
    if not tekst:
        return None, toelichting
    gevonden, _, pos = bronchecker.zoek_citaat(w["citaat"], tekst)
    t = bronchecker.normaliseer(tekst)
    if gevonden and pos is not None:
        begin = max(0, pos - FRAGMENT_TEKENS)
        return t[begin:pos + len(w["citaat"]) + FRAGMENT_TEKENS], f"fragment uit {gebruikt}"
    return t[:2 * FRAGMENT_TEKENS], f"begin van {gebruikt} (citaat niet letterlijk gevonden)"


def prompt_voor(w: dict, vragen: list[dict], fragment: str) -> str:
    regels = [f"Artikel: {w['url']}",
              f"Medium: {w.get('medium') or 'onbekend'} · datum: {w.get('datum') or 'onbekend'}",
              "", "Tekst uit het artikel:", "<<<", fragment, ">>>", "",
              f"Geciteerd: {w.get('wie')} (groep: {w.get('groep')})",
              f"Citaat: \"{w['citaat']}\"", "", "Vragen:"]
    for i, v in enumerate(vragen, 1):
        regels.append(f"{i}. {v['sleutel']}: {v['vraag']} Kies uit: "
                      + ", ".join(f"'{o}'" for o in v["opties"]))
    regels.append("")
    regels.append("Geef per vraag (sleutel) de optie die het artikel draagt, en in 'toelichting' "
                  "kort waarop je dat baseert.")
    return "\n".join(regels)


def codeer(w: dict, vragen: list[dict], *, haal=None, model=None) -> tuple[dict | None, str]:
    """(codes, toelichting) voor één waarneming, of (None, reden)."""
    fragment, toelichting = fragment_van(w, haal)
    if fragment is None:
        return None, f"artikel niet te lezen ({toelichting})"
    antwoord = (model or (lambda p, s: bronchecker.vraag_model(p, s, systeem=SYSTEEM,
                                                               model=MODEL)))(
        prompt_voor(w, vragen, fragment), schema_voor(vragen))
    if not isinstance(antwoord, dict) or not isinstance(antwoord.get("codes"), dict):
        return None, "het model gaf geen bruikbaar antwoord"
    codes = {}
    for v in vragen:
        o = antwoord["codes"].get(v["sleutel"])
        if o not in v["opties"]:
            return None, f"het model gaf geen geldige optie voor '{v['sleutel']}'"
        codes[v["sleutel"]] = o
    return codes, str(antwoord.get("toelichting") or "")[:300]


def draai(meting_id: int, *, aantal: int | None = None, indienen: bool = False, verstuur=None,
          haal=None, model=None, meld=print) -> dict:
    """De steekproef blind coderen; met ``indienen`` ook als controle insturen."""
    if verstuur is None:
        if not TOKEN.exists():
            meld(f"Geen token voor het account '{ACCOUNT}' ({TOKEN}). Maak het met:\n"
                 f"  python3 scripts/create_user.py {ACCOUNT} --kind agent --provenance "
                 "\"metingcontrole: Claude Sonnet\" --new-token --save")
            return {"gestart": False, "reden": "geen token"}
        verstuur = metingcheck.http_verstuurder(API, TOKEN.read_text().strip())
    status, rij = verstuur("GET", f"/api/metingen/{meting_id}/controle", None)
    if status != 200:
        meld(f"Meting #{meting_id}: {status} {rij.get('error')}")
        return {"gestart": False, "reden": rij.get("error") or f"HTTP {status}"}
    if rij.get("reden"):
        meld(f"Meting #{meting_id}: {rij['reden']}")
        return {"gestart": False, "reden": rij["reden"]}
    vragen = rij["vragen"]
    nog = max(0, rij["nodig"] - rij["gecontroleerd"])
    doel = aantal if aantal is not None else nog
    steekproef = rij["te_controleren"][:max(0, doel)]
    meld(f"Meting #{meting_id}: {rij['gecontroleerd']} van {rij['nodig']} nodige controles gedaan; "
         f"deze ronde {len(steekproef)} blind ({'indienen' if indienen else 'droogloop'})")
    tel = {"gestart": True, "gecodeerd": 0, "ingediend": 0, "overgeslagen": 0, "fout": 0,
           "uitkomsten": []}
    for w in steekproef:
        codes, toelichting = codeer(w, vragen, haal=haal, model=model)
        if codes is None:
            tel["overgeslagen"] += 1
            meld(f"  · waarneming #{w['id']}: overgeslagen — {toelichting}")
            continue
        tel["gecodeerd"] += 1
        uitkomst = {"waarneming_id": w["id"], "codes": codes, "toelichting": toelichting}
        if indienen:
            s, j = verstuur("POST", f"/api/metingen/{meting_id}/waarnemingen/{w['id']}/controle",
                            {"codes": codes})
            if s == 201:
                tel["ingediend"] += 1
                uitkomst["gelijk"] = j.get("gelijk")
            else:
                tel["fout"] += 1
                uitkomst["fout"] = f"{s} {j.get('error')}"
        tel["uitkomsten"].append(uitkomst)
        meld(f"  · waarneming #{w['id']}: {json.dumps(codes, ensure_ascii=False)}"
             + (f" — {uitkomst['fout']}" if uitkomst.get("fout") else ""))
    return tel


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--meting", type=int, required=True, help="het id van de meting")
    ap.add_argument("--aantal", type=int, default=None,
                    help="zoveel waarnemingen (standaard: wat punt d nog nodig heeft)")
    ap.add_argument("--indienen", action="store_true", help="de codes echt als controle insturen")
    ap.add_argument("--api", default=API)
    a = ap.parse_args()
    verstuur = None
    if TOKEN.exists():
        verstuur = metingcheck.http_verstuurder(a.api, TOKEN.read_text().strip())
    uit = draai(a.meting, aantal=a.aantal, indienen=a.indienen, verstuur=verstuur)
    print(json.dumps({k: v for k, v in uit.items() if k != "uitkomsten"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
