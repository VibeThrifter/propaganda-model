#!/usr/bin/env python3
"""Migratie: doel en grondslag van elk mechanisme (eigenaarsbesluit 2026-10-15, Uitbreiding D).

Het model gaat over machtsuitoefening op beslissing en opinie (DOCUMENTATIE.md § "Uitbreiding D").
Elk mechanisme krijgt daarom twee kenmerken naast zijn categorieën:

- doel (`mechanism_doelen`, één of meer): waar de macht op werkt.
  - beslissing: wat overheid, politiek of rechter besluit;
  - agenda: wat op de besluitvormingsagenda komt en welke opties meetellen;
  - opinie: wat het publiek te zien krijgt en denkt.
- grondslag (`mechanisms.grondslag`): officieel of niet_officieel.
  - officieel: de invloed loopt via een formeel toegekende bevoegdheid of een formeel
    toegekend recht van de bron over het doel (wet, ambt, mandaat, statuut, eigendom,
    benoemingsrecht, werkgeversgezag, rechterlijke uitspraak);
  - niet_officieel: de invloed loopt daarbuiten om, via geld, toegang, netwerken,
    circulerend personeel, informatie, expertise, druk of gedeelde ideeën.

Wat deze migratie doet (idempotent; een tweede run doet niets):
1. Tabel `mechanism_doelen` + index, kolom `mechanisms.grondslag` (ALTER TABLE, met CHECK).
2. Elk levend mechanisme zonder doel of grondslag krijgt ze, volgens de regels en uitzonderingen
   hieronder (`indeling`). Elke indeling komt in edit_log onder `assistent`, betwistbaar
   via een RfC 'herformuleren' (velden `doelen`/`grondslag`).
3. Herstel: een mechanisme uit een aangenomen RfC kreeg zijn `mechanism_type`, extra
   categorieën en thema's niet mee (voorstellen._maak_element las de sleutel
   'mechanisme_type', de RfC's sturen 'mechanism_type', en sloeg extra_filters/themes over).
   Die worden alsnog uit de payload gezet.
4. Open mechanisme-RfC's zonder doel/grondslag krijgen ze in hun payload (zelfde regels),
   zodat ze na aanname niet zonder kenmerken in het model komen.

Geen tabel-herbouw: de server mag blijven draaien (WAL). Backup via de backup-API.

Gebruik: python3 scripts/migrate_add_doel_grondslag.py [--droog] [--toon]
  --droog  toont het plan, schrijft niets
  --toon   print de indeling van elk mechanisme (met --droog: ter controle)
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import voorstellen  # noqa: E402

DB_PATH = ROOT / "data" / "propaganda_model.db"
ACCOUNT = "assistent"
REDEN = ("Uitbreiding D (eigenaarsbesluit 2026-10-15): doel en grondslag ingedeeld volgens "
         "scripts/migrate_add_doel_grondslag.py; betwistbaar via een RfC 'herformuleren' "
         "(velden doelen/grondslag)")

DOELEN_DDL = """CREATE TABLE mechanism_doelen (
    mechanism_id INTEGER NOT NULL REFERENCES mechanisms(id) ON DELETE CASCADE,
    doel TEXT NOT NULL CHECK(doel IN ('beslissing', 'agenda', 'opinie')),
    PRIMARY KEY (mechanism_id, doel)
)"""
DOELEN_INDEX = "CREATE INDEX idx_mechdoelen_doel ON mechanism_doelen(doel)"
GRONDSLAG_DDL = ("ALTER TABLE mechanisms ADD COLUMN grondslag TEXT "
                 "CHECK(grondslag IN ('officieel', 'niet_officieel'))")

# ── De indeling ──────────────────────────────────────────────────────────────
# Doel volgt uit de categorieën en de doelrol; de uitzonderingen staan bij naam.
OPINIE_CATEGORIEEN = {"eigendom", "advertentie", "sourcing", "flak", "ideologie"}
BESLISSING_CATEGORIEEN = {"formele_macht", "belangen", "kennis_advies", "polder", "werving"}
# Een mechanisme dat een beslisser raakt, werkt (ook) op beslissingen.
BESLISSERS = {"politicus", "partij", "bewindspersoon", "topambtenaar", "departement",
              "uitvoeringsorganisatie", "decentrale_overheid", "lokale_bestuurder",
              "eu_instelling", "parlementair_controleur", "bestuursrechter"}

# Precies deze doelen, ongeacht categorie of doelrol.
DOEL_PRECIES = {
    # media zetten de politieke agenda (krantenkop → Kamervraag), ze besluiten niet
    "media_agendering": {"agenda"},
    # homogeniteit van rechters werkt op uitspraken
    "sociologische_homogeniteit_rechtspraak": {"beslissing"},
    # de journalist dwingt openbaarheid af en publiceert: controle op het bestuur én berichtgeving
    "woo_verzoek": {"beslissing", "opinie"},
}
# Komt er bij: de agenda (wat op tafel komt en welke opties meetellen).
DOEL_ERBIJ = {
    "lobbytoegang": {"agenda"},
    "departementale_lobby": {"agenda"},
    "lobbyist_naar_politicus": {"agenda"},    # kant-en-klare Kamervragen en amendementen
    "belangenbehartiging": {"agenda"},
    "denktank_naar_politiek": {"agenda"},
    "institutioneel_advies": {"agenda"},      # ongevraagd advies zet onderwerpen op de agenda
    "polderoverleg": {"agenda"},
    "akkoord_preemptie": {"agenda"},          # de uitkomst ligt vast vóór het parlement spreekt
    "begrotingsorthodoxie": {"agenda"},       # welke opties als 'onbetaalbaar' afvallen
    "kapitaalvluchtdreiging": {"agenda"},     # het 'vestigingsklimaat' begrenst wat besproken wordt
    "politicus_elite_netwerk": {"beslissing"},  # het forum bindt de politicus, niet alleen het frame
}

# Grondslag: niet_officieel tenzij hier genoemd (of primaire categorie formele_macht).
OFFICIEEL = {
    # eigendom, zeggenschap en de benoemingsketen van media
    "eigendomsconcentratie", "winstmaximalisatie", "cross_media_eigendom", "acquisitiestrategie",
    "holdingconstructie", "systemisch_eigenaarschap", "strategische_zeggenschap",
    "familiezeggenschap", "certificaatconstructie", "publieke_kapitaalketen",
    "commissarisbenoeming", "directiebenoeming", "stak_stemzeggenschap", "eigenaar_directiekeuze",
    "benoemingspolitiek", "redactioneel_budgetcontrole", "hoofdredacteur_als_filter",
    "podiumverlening", "deplatforming", "dienstverband",
    # het publieke omroepbestel (Mediawet)
    "bestelsturing", "politieke_benoeming_omroeptop", "staatsreclame_exploitatie", "ledeneis",
    "intekensturing", "erkenningverlening",
    # formele bevoegdheden van de staat, de rechter en de werkgever tegenover een uiting
    "statelijke_bronnenjacht", "strafvervolging_uiting", "beroepssanctie_uiting",
    "civiele_inperking_uiting", "werkgeverssanctie_uiting", "bestuurlijke_publicatieboete",
    "woo_obstructie", "accreditatiepoort",
    # voorlichters handelen in opdracht van hun werkgever
    "gecoordineerde_voorlichting", "institutionele_voorlichting", "woordvoerdersregie",
    # wettelijk advies, wettelijke zetels, benoemingsrecht
    "institutioneel_advies", "polderoverleg", "kroonbenoeming",
    # toezicht, controle, rechtspraak, statutaire borging en openbaarheidsrecht
    "toezicht_tandeloosheid", "toezichthouder_interventie", "parlementaire_controle",
    "onafhankelijkheidsborging", "redactiestatuut_borging", "continuiteitsborging",
    "afgedwongen_borging", "redactieraad_instemming", "ledenraad_zeggenschap",
    "integriteitstoezicht_expert", "onafhankelijke_controle", "beleid_via_rechter", "woo_verzoek",
}


def indeling(naam, filters, doelrol, primair):
    """→ (doelen, grondslag) voor één mechanisme. `filters`: alle categorieën (incl. primair),
    `doelrol`: naam van de doelrol of None, `primair`: mechanisms.filter."""
    if naam in DOEL_PRECIES:
        doelen = set(DOEL_PRECIES[naam])
    else:
        doelen = set()
        if set(filters) & OPINIE_CATEGORIEEN:
            doelen.add("opinie")
        if set(filters) & BESLISSING_CATEGORIEEN or doelrol in BESLISSERS:
            doelen.add("beslissing")
        if not doelen:  # alleen tegenmacht/overig: de media of het publiek als doel
            doelen.add("opinie")
        doelen |= DOEL_ERBIJ.get(naam, set())
    grondslag = "officieel" if (primair == "formele_macht" or naam in OFFICIEEL) else "niet_officieel"
    return sorted(doelen, key=voorstellen.MECHANISME_DOELEN.index), grondslag


def kolom_bestaat(conn, tabel, kolom):
    return any(r[1] == kolom for r in conn.execute(f"PRAGMA table_info({tabel})"))


def tabel_bestaat(conn, naam):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (naam,)).fetchone() is not None


def te_doen(conn, heeft_tabel, heeft_kolom):
    rollen = {i: n for i, n in conn.execute("SELECT id, name FROM roles")}
    filters = {}
    for mid, f in conn.execute("SELECT mechanism_id, filter FROM mechanism_filters"):
        filters.setdefault(mid, set()).add(f)
    met_doel = ({m for (m,) in conn.execute("SELECT DISTINCT mechanism_id FROM mechanism_doelen")}
                if heeft_tabel else set())
    plan = []
    for mid, naam, primair, doelrol_id, grondslag in conn.execute(
            f"SELECT id, name, filter, target_role_id, "
            f"{'grondslag' if heeft_kolom else 'NULL'} FROM mechanisms "
            f"WHERE NOT vervangen ORDER BY id"):
        doelen, gs = indeling(naam, filters.get(mid, set()) | {primair},
                              rollen.get(doelrol_id), primair)
        plan.append({"id": mid, "naam": naam,
                     "doelen": None if mid in met_doel else doelen,
                     "grondslag": None if grondslag else gs})
    return [p for p in plan if p["doelen"] or p["grondslag"]], plan


def rfc_herstel(conn):
    """Aangenomen mechanisme-RfC's waarvan type, extra categorieën of thema's niet zijn gezet."""
    uit = []
    for vid, payload, resultaat in conn.execute(
            "SELECT id, payload, resultaat FROM voorstellen WHERE status = 'geaccepteerd' "
            "AND soort = 'nieuw_theorie_element'"):
        p, r = json.loads(payload or "{}"), json.loads(resultaat or "{}")
        if p.get("element_type") != "mechanisme" or not r.get("id"):
            continue
        rij = conn.execute("SELECT mechanism_type, vervangen FROM mechanisms WHERE id = ?",
                           (r["id"],)).fetchone()
        if rij is None or rij[1]:
            continue
        mtype = p.get("mechanisme_type") or p.get("mechanism_type")
        zet_type = mtype if (not rij[0] and mtype) else None
        heeft = {f for (f,) in conn.execute(
            "SELECT filter FROM mechanism_filters WHERE mechanism_id = ?", (r["id"],))}
        extra = [f for f in (p.get("extra_filters") or [])
                 if f in voorstellen.MECHANISME_FILTERS and f != "cross_filter" and f not in heeft]
        themas_heeft = {t for (t,) in conn.execute(
            "SELECT theme FROM mechanism_themes WHERE mechanism_id = ?", (r["id"],))}
        themas = [t for t in (p.get("themes") or p.get("themas") or []) if t not in themas_heeft]
        if zet_type or extra or themas:
            uit.append({"voorstel": vid, "id": r["id"], "type": zet_type, "extra_filters": extra,
                        "themes": themas})
    return uit


def open_rfcs(conn):
    """Open mechanisme-RfC's zonder doelen/grondslag → de aangevulde payload."""
    rollen = {i: n for i, n in conn.execute("SELECT id, name FROM roles")}
    uit = []
    for vid, payload in conn.execute(
            "SELECT id, payload FROM voorstellen WHERE status = 'open' "
            "AND soort = 'nieuw_theorie_element'"):
        p = json.loads(payload or "{}")
        if p.get("element_type") != "mechanisme" or (p.get("doelen") and p.get("grondslag")):
            continue
        filters = {p.get("filter")} | set(p.get("extra_filters") or [])
        doelen, gs = indeling(p.get("naam", ""), filters, rollen.get(p.get("target_role_id")),
                              p.get("filter"))
        p.setdefault("doelen", doelen)
        p.setdefault("grondslag", gs)
        uit.append({"voorstel": vid, "naam": p.get("naam"), "doelen": p["doelen"],
                    "grondslag": p["grondslag"], "payload": p})
    return uit


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--droog", action="store_true")
    ap.add_argument("--toon", action="store_true")
    args = ap.parse_args()
    if not DB_PATH.exists():
        sys.exit(f"FOUT: {DB_PATH} bestaat niet")

    conn = sqlite3.connect(DB_PATH, isolation_level=None, timeout=60)
    heeft_tabel = tabel_bestaat(conn, "mechanism_doelen")
    heeft_kolom = kolom_bestaat(conn, "mechanisms", "grondslag")
    plan, alles = te_doen(conn, heeft_tabel, heeft_kolom)
    herstel = rfc_herstel(conn)
    rfcs = open_rfcs(conn)

    print("Plan:")
    if not heeft_tabel:
        print("  tabel mechanism_doelen + idx_mechdoelen_doel")
    if not heeft_kolom:
        print("  kolom mechanisms.grondslag")
    tel = {}
    for p in alles:
        d, g = indeling_van(p, conn, heeft_tabel, heeft_kolom)
        for x in d:
            tel[x] = tel.get(x, 0) + 1
        tel[g] = tel.get(g, 0) + 1
    print(f"  {len(plan)} mechanismen krijgen doel en/of grondslag "
          f"(over alle {len(alles)}: {', '.join(f'{k} {v}' for k, v in sorted(tel.items()))})")
    for h in herstel:
        print(f"  herstel #{h['id']} (RfC {h['voorstel']}): type {h['type']}, "
              f"extra {h['extra_filters']}, thema's {h['themes']}")
    for r in rfcs:
        print(f"  open RfC {r['voorstel']} ({r['naam']}): doelen {r['doelen']}, grondslag {r['grondslag']}")
    if args.toon:
        for p in alles:
            d, g = indeling_van(p, conn, heeft_tabel, heeft_kolom)
            print(f"    #{p['id']:<4} {p['naam']:<42} {','.join(d):<28} {g}")
    if not (plan or herstel or rfcs or not heeft_tabel or not heeft_kolom):
        print("Niets te doen — alles staat er al.")
        return
    if args.droog:
        print("(droogloop: niets geschreven)")
        return

    conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
    backup = DB_PATH.with_name(f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
    doel = sqlite3.connect(backup)
    conn.backup(doel)
    doel.close()
    print(f"Backup: {backup.name}")

    conn.execute("BEGIN IMMEDIATE")
    try:
        if not heeft_tabel:
            conn.execute(DOELEN_DDL)
            conn.execute(DOELEN_INDEX)
        if not heeft_kolom:
            conn.execute(GRONDSLAG_DDL)
        for p in plan:
            nieuw = {}
            if p["doelen"]:
                for d in p["doelen"]:
                    conn.execute("INSERT OR IGNORE INTO mechanism_doelen (mechanism_id, doel) "
                                 "VALUES (?, ?)", (p["id"], d))
                nieuw["doelen"] = p["doelen"]
            if p["grondslag"]:
                conn.execute("UPDATE mechanisms SET grondslag = ? WHERE id = ?",
                             (p["grondslag"], p["id"]))
                nieuw["grondslag"] = p["grondslag"]
            conn.execute("INSERT INTO edit_log (table_name, record_id, action, changed_by, "
                         "new_value, reason) VALUES ('mechanisms', ?, 'updated', ?, ?, ?)",
                         (p["id"], ACCOUNT, json.dumps(nieuw, ensure_ascii=False), REDEN))
        for h in herstel:
            if h["type"]:
                conn.execute("UPDATE mechanisms SET mechanism_type = ? WHERE id = ?",
                             (h["type"], h["id"]))
            for f in h["extra_filters"]:
                conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) "
                             "VALUES (?, ?)", (h["id"], f))
            for t in h["themes"]:
                conn.execute("INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) "
                             "VALUES (?, ?)", (h["id"], t))
            conn.execute("INSERT INTO edit_log (table_name, record_id, action, changed_by, "
                         "new_value, reason) VALUES ('mechanisms', ?, 'updated', ?, ?, ?)",
                         (h["id"], ACCOUNT, json.dumps(
                             {k: h[k] for k in ("type", "extra_filters", "themes")}, ensure_ascii=False),
                          f"Herstel: aangenomen RfC {h['voorstel']} droeg dit in zijn payload, "
                          "voorstellen._maak_element zette het niet (sleutel mechanism_type, "
                          "extra_filters/themes overgeslagen)"))
        for r in rfcs:
            conn.execute("UPDATE voorstellen SET payload = ? WHERE id = ?",
                         (json.dumps(r["payload"], ensure_ascii=False), r["voorstel"]))
            conn.execute("INSERT INTO edit_log (table_name, record_id, action, changed_by, "
                         "new_value, reason) VALUES ('voorstellen', ?, 'updated', ?, ?, ?)",
                         (r["voorstel"], ACCOUNT,
                          json.dumps({"doelen": r["doelen"], "grondslag": r["grondslag"]}),
                          "Uitbreiding D: een open mechanisme-RfC krijgt doel en grondslag "
                          "volgens de indeling van scripts/migrate_add_doel_grondslag.py"))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise

    zonder = conn.execute("""SELECT count(*) FROM mechanisms m WHERE NOT m.vervangen AND (
        m.grondslag IS NULL OR NOT EXISTS (SELECT 1 FROM mechanism_doelen d WHERE d.mechanism_id = m.id))
    """).fetchone()[0]
    print(f"Klaar. Levende mechanismen zonder doel of grondslag: {zonder}")
    conn.close()


def indeling_van(p, conn, heeft_tabel, heeft_kolom):
    """De indeling zoals ze na de migratie staat (bestaand of gepland), voor de telling."""
    if p["doelen"]:
        doelen = p["doelen"]
    else:
        doelen = [d for (d,) in conn.execute(
            "SELECT doel FROM mechanism_doelen WHERE mechanism_id = ?", (p["id"],))]
    if p["grondslag"]:
        gs = p["grondslag"]
    else:
        gs = conn.execute("SELECT grondslag FROM mechanisms WHERE id = ?", (p["id"],)).fetchone()[0]
    return doelen, gs


if __name__ == "__main__":
    main()
