#!/usr/bin/env python3
"""Welstandsmeter — leesbaar rapport + data/doelgroep.json.

Leidt per nieuwsoutlet de getargette marketing-/welstandsklasse af (hoog A/AB1 ↔ laag C/D)
uit gesourcete 'doelgroepklasse'-signalen in de discussieboom (zie doelgroep.py). Met
--preview tellen ook nog-`voorgesteld` signalen mee (voorlopig, vóór menselijke review).

  python3 scripts/doelgroep_meter.py [--preview] [--json]
"""
import sys, json, sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import doelgroep  # noqa: E402

DB = ROOT / "data" / "propaganda_model.db"
OUT = ROOT / "data" / "doelgroep.json"


def _balk(x):
    """ASCII-positie op een -1..+1 schaal (laag ◄──► hoog); · = geen signaal."""
    if x is None:
        return "      ·      "
    n = 13
    i = round((x + 1) / 2 * (n - 1))
    return "".join("◆" if k == i else "─" for k in range(n))


def main():
    preview = "--preview" in sys.argv
    conn = sqlite3.connect(DB)
    res = doelgroep.compute_doelgroepmeter(conn, include_voorgesteld=preview)
    conn.close()

    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        vlag = "  (PREVIEW — incl. voorgesteld, nog niet gereviewd)" if preview else ""
        print(f"\n=== WELSTANDSMETER — getargette klasse per outlet{vlag} ===")
        print("schaal  laag D/C ◄──► hoog A/AB1  (welstand)\n")
        print(f"-- OUTLETS ({len(res['outlets'])}) [positie · vertrouwen α] --")
        for o in res["outlets"]:
            print(f"\n  {o['naam']:30} {o['klasse_label']}")
            print(f"    laag [{_balk(o['positie'])}] hoog   α={o['alpha']}  "
                  f"({o['n_signalen']} signaal/-en, {o['as_soort']})")
            for s in o["signalen"]:
                vv = f"meting {s['meting']:+.2f}" if s.get("soort") == "meting" else (s.get("klasse") or "?")
                print(f"      · {vv:16} [{s['status']}]  {s['claim'][:70]}")

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2))
    if "--json" not in sys.argv:
        print(f"\nGeschreven: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
