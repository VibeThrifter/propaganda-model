#!/usr/bin/env python3
"""Bereikmeter — leesbaar rapport + data/bereik.json.

Leidt per media-entiteit het gesourcete publieksbereik per jaar af (kijkcijfers/oplage/
maandbereik/invullers — zie bereik.py). Met --preview tellen ook nog-`voorgesteld`
signalen mee (voorlopig, vóór menselijke review).

  python3 scripts/bereik_meter.py [--preview] [--json]
"""
import sys, json, sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import bereik  # noqa: E402

DB = ROOT / "data" / "propaganda_model.db"
OUT = ROOT / "data" / "bereik.json"


def _fmt(n):
    return f"{n:,}".replace(",", ".")


def main():
    preview = "--preview" in sys.argv
    conn = sqlite3.connect(DB)
    res = bereik.compute_bereik(conn, include_voorgesteld=preview)
    conn.close()

    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        vlag = "  (PREVIEW — incl. voorgesteld, nog niet gereviewd)" if preview else ""
        print(f"\n=== BEREIKMETER — publieksbereik per media-entiteit{vlag} ===")
        # Gesorteerd op nieuwste bereik (groot → klein) leest als een machtsranglijst.
        ents = sorted(res["entiteiten"],
                      key=lambda o: -(o["nieuwste"]["aantal"] if o["nieuwste"] else 0))
        print(f"-- ENTITEITEN ({len(ents)}) [nieuwste punt · jaarreeks] --")
        for o in ents:
            nw = o["nieuwste"]
            kop = f"{_fmt(nw['aantal'])} {bereik.MATEN[nw['maat']]} ({nw['jaar']})" if nw else "?"
            print(f"\n  {o['naam']:35} {kop}")
            for jaar in sorted(o["reeks"]):
                print(f"      {jaar}: {_fmt(o['reeks'][jaar]):>12}")
            for s in o["signalen"]:
                print(f"      · {s['maat']}:{s['aantal']}:{s['jaar']} [{s['status']}]  "
                      f"{(s['claim'] or '')[:60]}")

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2))
    if "--json" not in sys.argv:
        print(f"\nGeschreven: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
