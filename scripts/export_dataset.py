#!/usr/bin/env python3
"""Data-feed (verbeterplan E1): de licentieerbare, geversioneerde tabel-export.

Één CSV per *verkochte* tabel in ``releases/dataset-v<X.Y.Z>/`` — het geversioneerde
zusje van het scores-snapshot (`scripts/release_model.py`). Puur stdlib (`csv` +
`sqlite3`), zelfde ROOT-patroon als `release_model.py`.

De VERKOOPBARE slice (neutraliteit + juridisch, zie DATA_DICTIONARY.md):
  - entities            structuurgraaf-knopen
  - relations           gerichte banden (relation_type, mechanism, certainty, influence)
  - sources             bronnenlijst (bibliografisch)
  - source_locations    vindplaatsen (url/doi/isbn/archive) per bron
  - income_composition  afgeleide geldstroom-'pie' (scoring.compute_income_composition)
  - bereik              gesourcet publieksbereik per jaar (bereik.compute_bereik)
  - doelgroep           getargette welstandsklasse per outlet (doelgroep.compute_doelgroepmeter)

UITGESLOTEN (mechanisch, nooit in de export): de politieke-positie-laag
(`politiek.py` / property='politieke_positie', art. 9-AVG) én `machtsvalentie`
(grensgeval — standaard uit de betaalde feed). De export raakt die modules niet aan.

Filter: alleen `status='goedgekeurd' AND NOT vervangen` (spiegelt viz_data.export_data);
`voorgesteld`/`afgewezen`/`vervangen` blijven eruit, net als de smaad_hold-firewall.

Gebruik:
    python3 scripts/export_dataset.py            # versie uit de nieuwste model-release
    python3 scripts/export_dataset.py 0.2.0      # expliciete semver
"""
import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import scoring    # noqa: E402  income composition
import bereik     # noqa: E402  publieksbereik
import doelgroep  # noqa: E402  welstandsmeter

DB_PATH = ROOT / "data" / "propaganda_model.db"
RELEASES_DIR = ROOT / "releases"

# De verkochte tabellen, in exportvolgorde. Elke bouwer geeft (kolommen, rijen).
SLICE_TABELLEN = ("entities", "relations", "sources", "source_locations",
                  "income_composition", "bereik", "doelgroep")


def laatste_versie() -> str:
    """Semver van de nieuwste model-release (releases/model-v*.json), of 0.1.0."""
    beste = None
    for p in RELEASES_DIR.glob("model-v*.json"):
        m = re.fullmatch(r"model-v(\d+)\.(\d+)\.(\d+)\.json", p.name)
        if m:
            v = tuple(map(int, m.groups()))
            if beste is None or v > beste:
                beste = v
    return ".".join(map(str, beste)) if beste else "0.1.0"


# ── Tabelbouwers (elk: conn -> (kolommen, rijen)) ────────────────────────────

def _entities(conn):
    # De vrije-tekst `description` wordt bewust NIET meegeleverd: dat is de model-
    # eigen redactionele prose (de neutraliteits-risicolaag) en kan — data-afhankelijk
    # — de uitgesloten analyse-lagen (kleurmeter/machtsvalentie) noemen. De verkochte
    # slice is de STRUCTUUR (types, rollen, scores, bronnen); de prose blijft op de
    # live site. Zie DATA_DICTIONARY.md.
    kol = ["id", "name", "type", "primary_role_id", "primary_role",
           "active_from", "active_until", "active", "bestuurslaag"]
    rijen = [[r["id"], r["name"], r["type"], r["primary_role_id"], r["role_name"],
              r["active_from"], r["active_until"], int(bool(r["active"])), r["bestuurslaag"]]
             for r in conn.execute("""
        SELECT e.id, e.name, e.type, e.primary_role_id,
               e.active_from, e.active_until, e.active, ro.name AS role_name, e.bestuurslaag
        FROM entities e
        LEFT JOIN roles ro ON ro.id = e.primary_role_id
        WHERE e.status = 'goedgekeurd' AND NOT e.vervangen
        ORDER BY e.id""")]
    return kol, rijen


def _relations(conn):
    """Alleen edges waarvan béide eindpunten in de verkochte entiteitenset zitten.

    Zonder de vrije-tekst `description` (zie _entities): de gestructureerde edge
    (type, mechanisme, filter, twee-assen-score) is het product."""
    kol = ["id", "source_id", "source_name", "target_id", "target_name",
           "relation_type", "mechanism_id", "mechanism_name", "filter",
           "certainty", "influence", "active_from", "active_until", "functie"]
    rijen = [[r["id"], r["source_id"], r["source_name"], r["target_id"],
              r["target_name"], r["relation_type"], r["mechanism_id"],
              r["mechanism_name"], r["mechanism_filter"], r["certainty"],
              r["influence"], r["active_from"], r["active_until"], r["functie"]]
             for r in conn.execute("""
        SELECT r.id, r.source_id, r.target_id, r.relation_type, r.mechanism_id,
               r.certainty, r.influence, r.active_from, r.active_until, r.functie,
               e1.name AS source_name, e2.name AS target_name,
               m.name AS mechanism_name, m.filter AS mechanism_filter
        FROM relations r
        JOIN entities e1 ON e1.id = r.source_id
        JOIN entities e2 ON e2.id = r.target_id
        LEFT JOIN mechanisms m ON m.id = r.mechanism_id
        WHERE r.status = 'goedgekeurd' AND NOT r.vervangen
          AND e1.status = 'goedgekeurd' AND NOT e1.vervangen
          AND e2.status = 'goedgekeurd' AND NOT e2.vervangen
        ORDER BY r.id""")]
    return kol, rijen


def _sources(conn):
    kol = ["id", "title", "author", "source_type", "publisher", "date_published",
           "language", "reliability", "onderwerp", "cluster_key"]
    rijen = [[r["id"], r["title"], r["author"], r["source_type"], r["publisher"],
              r["date_published"], r["language"], r["reliability"], r["onderwerp"],
              r["cluster_key"]]
             for r in conn.execute("""
        SELECT id, title, author, source_type, publisher, date_published,
               language, reliability, onderwerp, cluster_key
        FROM sources ORDER BY id""")]
    return kol, rijen


def _source_locations(conn):
    kol = ["id", "source_id", "location_type", "location", "accessed_at"]
    rijen = [[r["id"], r["source_id"], r["location_type"], r["location"],
              r["accessed_at"]]
             for r in conn.execute("""
        SELECT id, source_id, location_type, location, accessed_at
        FROM source_locations ORDER BY id""")]
    return kol, rijen


def _income_composition(conn):
    """Afgeleide geldstroom-'pie' (alleen gemergde aandelen; geen preview)."""
    kol = ["outlet_id", "outlet", "soort", "bron_id", "bron", "relation_type",
           "relation_id", "share_pct", "jaar", "som_institutioneel", "residu_pct"]
    rijen = []
    comp = scoring.compute_income_composition(conn, include_voorgesteld=False)
    for oid, d in sorted(comp.items()):
        for s in d["slices"]:
            rijen.append([oid, d["outlet"], "aandeel", s["bron_id"], s["bron"],
                          s["relation_type"], s["relation_id"], s["share"],
                          s["jaar"], d["som_institutioneel"], d["residu"]])
        for s in d["onbekend"]:
            rijen.append([oid, d["outlet"], "onbekend", s["bron_id"], s["bron"],
                          s["relation_type"], s["relation_id"], None, None,
                          d["som_institutioneel"], d["residu"]])
    return kol, rijen


def _bereik(conn):
    """Gesourcet publieksbereik per jaar, één rij per signaal (geen preview)."""
    kol = ["entity_id", "entity", "type", "maat", "aantal", "jaar", "arg_id", "status"]
    rijen = []
    res = bereik.compute_bereik(conn, include_voorgesteld=False)
    for o in res["entiteiten"]:
        for s in o["signalen"]:
            rijen.append([o["id"], o["naam"], o["type"], s["maat"], s["aantal"],
                          s["jaar"], s["arg_id"], s["status"]])
    return kol, rijen


def _doelgroep(conn):
    """Getargette welstandsklasse per outlet (bron-gewogen; geen preview)."""
    kol = ["outlet_id", "outlet", "type", "positie", "klasse_label", "as_soort",
           "vertrouwen", "n_signalen"]
    rijen = []
    res = doelgroep.compute_doelgroepmeter(conn, include_voorgesteld=False)
    for o in res["outlets"]:
        rijen.append([o["id"], o["naam"], o["type"], o["positie"],
                      o["klasse_label"], o["as_soort"], o["vertrouwen"],
                      o["n_signalen"]])
    return kol, rijen


_BOUWERS = {
    "entities": _entities,
    "relations": _relations,
    "sources": _sources,
    "source_locations": _source_locations,
    "income_composition": _income_composition,
    "bereik": _bereik,
    "doelgroep": _doelgroep,
}


def verzamel(conn):
    """De volledige verkochte slice als {tabel: {"kolommen":[...], "rijen":[[...]]}}.

    Gedeelde bron voor de CSV-export (deze CLI) én de feed-API (server.py); zo
    zit de neutraliteits-afbakening op precies één plek."""
    conn.row_factory = sqlite3.Row
    out = {}
    for tabel in SLICE_TABELLEN:
        kol, rijen = _BOUWERS[tabel](conn)
        out[tabel] = {"kolommen": kol, "rijen": rijen}
    return out


def tabel(conn, naam):
    """Eén verkochte tabel (kolommen, rijen) — voor /api/feed/export/<tabel>.csv."""
    if naam not in _BOUWERS:
        raise KeyError(naam)
    conn.row_factory = sqlite3.Row
    return _BOUWERS[naam](conn)


def export(versie=None, db_path=DB_PATH, releases_dir=RELEASES_DIR):
    versie = versie or laatste_versie()
    if not re.fullmatch(r"\d+\.\d+\.\d+", versie):
        raise SystemExit(f"FOUT: '{versie}' is geen semver (X.Y.Z)")
    uit = Path(releases_dir) / f"dataset-v{versie}"
    uit.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        data = verzamel(conn)
    finally:
        conn.close()

    for tabel_naam, d in data.items():
        pad = uit / f"{tabel_naam}.csv"
        with pad.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(d["kolommen"])
            w.writerows(d["rijen"])
        print(f"  {pad.relative_to(ROOT)}: {len(d['rijen'])} rijen")
    print(f"Dataset-export v{versie} → {uit.relative_to(ROOT)}/")
    return uit


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("versie", nargs="?", default=None,
                   help="semver (default: de nieuwste model-release, of 0.1.0)")
    export(p.parse_args().versie)


if __name__ == "__main__":
    main()
