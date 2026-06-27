#!/usr/bin/env python3
"""Politieke kleurmeter — leesbaar rapport + data/kleurmeter.json.

Leidt per persoon en per organisatie een ideologische positie af uit gesourcete
'politieke_positie'-signalen in de discussieboom (zie politiek.py). Met --preview
tellen ook nog-`voorgesteld` signalen mee (voorlopig, vóór menselijke review).

  python3 scripts/politiek_kleurmeter.py [--preview] [--json]
"""
import sys, json, sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import politiek  # noqa: E402

DB = ROOT / "data" / "propaganda_model.db"
OUT = ROOT / "data" / "kleurmeter.json"


def _balk(econ, cult, est):
    """ASCII-positie op een -1..+1 schaal (· = geen signaal)."""
    def cel(x):
        if x is None:
            return "      ·      "
        n = 13
        i = round((x + 1) / 2 * (n - 1))
        return "".join("◆" if k == i else "─" for k in range(n))
    return (f"econ  [{cel(econ)}]\n    cult  [{cel(cult)}]\n    estab [{cel(est)}]")


def main():
    preview = "--preview" in sys.argv
    conn = sqlite3.connect(DB)
    res = politiek.compute_kleurmeter(conn, include_voorgesteld=preview)
    conn.close()

    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        vlag = "  (PREVIEW — incl. voorgesteld, nog niet gereviewd)" if preview else ""
        print(f"\n=== POLITIEKE KLEURMETER{vlag} ===")
        print("schaal −1 ◄──► +1 per as:  econ links/rechts · "
              "cult progressief/conservatief · estab anti-establishment/establishment\n")
        print(f"-- PERSONEN ({len(res['personen'])}) "
              "[as-positie · vertrouwen α] --")
        for p in res["personen"]:
            print(f"\n  {p['naam']:24} {p['kleur']}")
            pp = p['positie']
            print(f"    {_balk(pp['economisch'], pp['cultureel'], pp['establishment'])}"
                  f"   α={p['alpha']}  ({p['n_signalen']} signaal/-en)")
            for s in p["signalen"]:
                vv = f"meting {s['meting']:+.2f}" if s.get("soort") == "meting" else (s.get("pool") or "?")
                print(f"      · {s['as']:11} {vv:24}  [{s['status']}]  {s['claim'][:74]}")
        bepaald = [o for o in res["organisaties"] if o["genoeg"]]
        indicatief = [o for o in res["organisaties"] if not o["genoeg"]]
        print(f"\n-- ORGANISATIES — BEPAALD ({len(bepaald)}) "
              "[eigen signaal, of ≥2 bekende leden] --")
        for o in bepaald:
            tag = "EIGEN" if o["bron"] == "eigen" else "afgeleid"
            print(f"\n  {o['naam']:36} {o['kleur']}   [{tag}]")
            op = o["positie"]
            print(f"    {_balk(op['economisch'], op['cultureel'], op['establishment'])}")
            if o.get("eigen"):
                print(f"      eigen: {o['eigen']['n_signalen']} signaal/-en "
                      f"(α={o['eigen']['alpha']})")
            if o.get("afgeleid"):
                afl = o["afgeleid"]
                via = "tevens afgeleid uit" if o["bron"] == "eigen" else "afgeleid uit"
                print(f"      {via} {afl['n_leden']} leden → {afl['kleur']}:")
                for m in afl["leden"]:
                    lp = "" if m["lopend"] else " (beëindigd)"
                    print(f"        · {m['naam']:24} {m['band']:14}{lp}  → {m['kleur']}")
        print(f"\n-- ORGANISATIES — INDICATIEF ({len(indicatief)}) "
              "[1 bekend lid, geen eigen signaal; niet representatief] --")
        for o in indicatief:
            m = o["afgeleid"]["leden"][0] if o.get("afgeleid") else {"naam": "?", "band": "?"}
            print(f"  {o['naam']:42} {o['kleur']:34} ({m['naam']}, {m['band']})")

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2))
    if "--json" not in sys.argv:
        print(f"\nGeschreven: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
