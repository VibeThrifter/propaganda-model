#!/usr/bin/env python3
"""
Modelrelease (verbeterplan M3.1): semver-snapshot + changelog + score-diff.

Een release = een gescoorde momentopname van het model. Het script schrijft
twee bestanden in releases/ (ingecheckt, anders dan data/):

  releases/model-v<X.Y.Z>.json   het scores-snapshot (alle theorie- en
                                 praktijkscores + kerngetallen + git-commit)
  releases/model-v<X.Y.Z>.md     de changelog: score-diff t.o.v. de vorige
                                 release ("geloofwaardigheid mechanisme X:
                                 0,62 → 0,71") + sjabloon voor de duiding

Het script commit en tagt NIET zelf — het print de voorgestelde commando's
(of draai met --tag om de annotated git-tag direct te zetten). De viz toont
de nieuwste releasetag (generate_viz.py leest releases/).

Gebruik:
    python3 scripts/release_model.py 0.1.0 --titel "Eerste gescoorde snapshot"
    python3 scripts/release_model.py 0.2.0 --titel "..." --tag
"""
import argparse
import datetime
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import scoring  # noqa: E402
import validation  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
RELEASES_DIR = ROOT / "releases"

DIFF_DREMPEL = 0.01  # |Δ geloofwaardigheid| vanaf hier in de changelog


def _git(*args):
    try:
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                           text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else None
    except OSError:
        return None


def parse_versie(s):
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", s)
    if not m:
        raise SystemExit(f"FOUT: '{s}' is geen semver (X.Y.Z)")
    return tuple(map(int, m.groups()))


def maak_snapshot(conn, versie, titel):
    """Het volledige gescoorde snapshot van het model, op één moment."""
    scores = scoring.compute_all_scores(
        conn, bridged_weights=scoring.bridged_weights_from_file(
            DB_PATH.parent / "bridging.json"))

    def naam_map(sql):
        return {r[0]: r[1] for r in conn.execute(sql)}

    mech_naam = naam_map("SELECT id, name FROM mechanisms WHERE NOT vervangen")
    rol_naam = naam_map("SELECT id, name FROM roles WHERE NOT vervangen")
    veld_naam = naam_map("SELECT id, label FROM emergent_effects WHERE NOT vervangen")
    ent_naam = naam_map("SELECT id, name FROM entities WHERE NOT vervangen")
    rel_naam = {r[0]: f"{r[1]} → {r[2]}" for r in conn.execute("""
        SELECT r.id, e1.name, e2.name FROM relations r
        JOIN entities e1 ON e1.id = r.source_id
        JOIN entities e2 ON e2.id = r.target_id WHERE NOT r.vervangen""")}

    return {
        "versie": versie,
        "titel": titel,
        "gegenereerd": datetime.datetime.now().isoformat(timespec="seconds"),
        "git_commit": _git("rev-parse", "--short", "HEAD"),
        "kerngetallen": validation.kerngetallen(conn),
        "scores": {
            "mechanismen": {str(i): {
                "naam": mech_naam.get(i, f"#{i}"),
                "geloofwaardigheid": s["geloofwaardigheid"],
                "lo": s["lo"], "hi": s["hi"], "sterkte": s["sterkte"],
            } for i, s in scores["mechanisms"].items()},
            "rollen": {str(i): {
                "naam": rol_naam.get(i, f"#{i}"),
                "geloofwaardigheid": s["geloofwaardigheid"],
                "lo": s["lo"], "hi": s["hi"], "sterkte": s["sterkte"],
            } for i, s in scores["roles"].items()},
            "velden": {str(i): {
                "naam": veld_naam.get(i, f"#{i}"),
                "geloofwaardigheid": s["geloofwaardigheid"],
                "lo": s["lo"], "hi": s["hi"],
            } for i, s in scores.get("emergent_effects", {}).items()},
            "relaties": {str(i): {
                "naam": rel_naam.get(i, f"#{i}"),
                "geloofwaardigheid": d["score"],
                "invloed": scores["relations_influence"].get(i, 0.0),
            } for i, d in scores["relations_detail"].items()},
            "entiteiten": {str(i): {
                "naam": ent_naam.get(i, f"#{i}"),
                "geloofwaardigheid": d["score"],
            } for i, d in scores["entities_detail"].items()},
        },
    }


def vorige_release(releases_dir, nieuwe_versie):
    """De nieuwste bestaande release ouder dan ``nieuwe_versie``, of None."""
    beste, pad = (), None
    for p in Path(releases_dir).glob("model-v*.json"):
        m = re.fullmatch(r"model-v(\d+)\.(\d+)\.(\d+)\.json", p.name)
        if m:
            v = tuple(map(int, m.groups()))
            if v < parse_versie(nieuwe_versie) and v > beste:
                beste, pad = v, p
    if pad is None:
        return None
    return json.loads(pad.read_text())


def maak_diff(oud, nieuw):
    """Score-verschuivingen, nieuwe en vervallen elementen per categorie."""
    diff = {}
    for cat in ("mechanismen", "rollen", "velden", "relaties", "entiteiten"):
        o, n = oud["scores"].get(cat, {}), nieuw["scores"].get(cat, {})
        verschoven = []
        for i in sorted(set(o) & set(n), key=int):
            d = round(n[i]["geloofwaardigheid"] - o[i]["geloofwaardigheid"], 4)
            if abs(d) >= DIFF_DREMPEL:
                verschoven.append({"id": int(i), "naam": n[i]["naam"],
                                   "oud": o[i]["geloofwaardigheid"],
                                   "nieuw": n[i]["geloofwaardigheid"], "delta": d})
        verschoven.sort(key=lambda v: -abs(v["delta"]))
        diff[cat] = {
            "verschoven": verschoven,
            "nieuw": [{"id": int(i), "naam": n[i]["naam"]}
                      for i in sorted(set(n) - set(o), key=int)],
            "vervallen": [{"id": int(i), "naam": o[i]["naam"]}
                          for i in sorted(set(o) - set(n), key=int)],
        }
    return diff


ENKELVOUD = {"mechanismen": "mechanisme", "rollen": "rol", "velden": "veld",
             "relaties": "relatie", "entiteiten": "entiteit"}


def schrijf_changelog(pad, snapshot, vorige, diff):
    k = snapshot["kerngetallen"]
    regels = [
        f"# Modelrelease v{snapshot['versie']} — {snapshot['titel']}",
        "",
        f"Datum: {snapshot['gegenereerd']} · git: {snapshot['git_commit'] or 'n.v.t.'} · "
        + (f"vorige release: v{vorige['versie']}" if vorige else "eerste release"),
        "",
        "## Samenvatting",
        "",
        "_(Duiding door de releaser: wat veranderde er inhoudelijk en waarom — welke",
        "bronnen, welke tegenspraak, welke structuurwijzigingen.)_",
        "",
        "## Kerngetallen",
        "",
    ]
    if vorige:
        vk = vorige["kerngetallen"]
        regels += [f"| | v{vorige['versie']} | v{snapshot['versie']} |", "|---|---|---|"]
        for veld in ("entiteiten", "relaties", "argumenten", "bronnen", "citaties"):
            regels.append(f"| {veld} | {vk.get(veld, '—')} | {k.get(veld, '—')} |")
    else:
        regels.append(" · ".join(f"{k.get(v)} {v}" for v in
                                 ("entiteiten", "relaties", "argumenten", "bronnen")))
    regels += ["", f"## Score-verschuivingen (|Δ| ≥ {DIFF_DREMPEL})", ""]
    if not vorige:
        regels.append("Eerste release: geen vorige snapshot om tegen te diffen.")
    else:
        iets = False
        for cat, d in diff.items():
            for v in d["verschoven"]:
                iets = True
                regels.append(f"- {ENKELVOUD[cat]} **{v['naam']}**: "
                              f"{v['oud']:.2f} → {v['nieuw']:.2f} ({v['delta']:+.2f})")
        if not iets:
            regels.append("Geen verschuivingen boven de drempel.")
        regels += ["", "## Nieuw / vervallen", ""]
        iets = False
        for cat, d in diff.items():
            for v in d["nieuw"]:
                iets = True
                regels.append(f"- nieuw: {ENKELVOUD[cat]} **{v['naam']}** (#{v['id']})")
            for v in d["vervallen"]:
                iets = True
                regels.append(f"- vervallen/vervangen: {ENKELVOUD[cat]} "
                              f"**{v['naam']}** (#{v['id']})")
        if not iets:
            regels.append("Geen elementen bijgekomen of vervallen.")
    pad.write_text("\n".join(regels) + "\n", encoding="utf-8")


def release(versie, titel, db_path=DB_PATH, releases_dir=RELEASES_DIR, tag=False):
    parse_versie(versie)  # valideert
    releases_dir = Path(releases_dir)
    releases_dir.mkdir(exist_ok=True)
    json_pad = releases_dir / f"model-v{versie}.json"
    md_pad = releases_dir / f"model-v{versie}.md"
    if json_pad.exists():
        raise SystemExit(f"FOUT: {json_pad.name} bestaat al — releases zijn "
                         "onveranderlijk; kies een nieuwe versie")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    snapshot = maak_snapshot(conn, versie, titel)
    conn.close()

    vorige = vorige_release(releases_dir, versie)
    diff = maak_diff(vorige, snapshot) if vorige else {}
    json_pad.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))
    schrijf_changelog(md_pad, snapshot, vorige, diff)

    print(f"Release v{versie}: {json_pad.name} + {md_pad.name}")
    if vorige:
        n = sum(len(d["verschoven"]) for d in diff.values())
        print(f"Diff t.o.v. v{vorige['versie']}: {n} verschuiving(en) ≥ {DIFF_DREMPEL}")
    if tag:
        vuil = _git("status", "--porcelain")
        if vuil:
            print("LET OP: werkboom is niet schoon; de tag wijst naar de laatste commit, "
                  "niet naar deze snapshot-bestanden.")
        _git("tag", "-a", f"model-v{versie}", "-m", f"Modelrelease v{versie}: {titel}")
        print(f"Git-tag gezet: model-v{versie}")
    else:
        print("Volgende stap (zelf uitvoeren):\n"
              f"  git add releases/ && git commit -m 'Modelrelease v{versie}'\n"
              f"  git tag -a model-v{versie} -m 'Modelrelease v{versie}: {titel}'")
    return snapshot, diff


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("versie", help="semver, bv. 0.1.0")
    parser.add_argument("--titel", default="modelrelease",
                        help="korte typering voor changelog en tag")
    parser.add_argument("--tag", action="store_true",
                        help="zet direct een annotated git-tag model-v<versie>")
    args = parser.parse_args()
    release(args.versie, args.titel, tag=args.tag)


if __name__ == "__main__":
    main()
