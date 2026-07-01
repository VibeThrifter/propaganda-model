#!/usr/bin/env python3
"""
Migratie: toeslagenaffaire — generaliseren (incident → argument, geen eigen structuur).

Aanleiding (juni 2026, eigenaarsbesluit). De toeslagenaffaire zat in het model als
een tros van ~13 relaties rond één knoop (de Belastingdienst), elk gedragen door
precies één bronloos seed-argument. Dat is een *incident* dat zich voordeed als
*staande structuur* — wat de modelleerdiscipline afkeurt: een incident is bewijs
(een argument) voor een algemeen mechanisme, geen eigen org→org-relatie.

DE GENERALISATIE (de inhoud) loopt via de API onder `assistent`, niet via dit
script: drie gesourcete literatuur-argumenten op de algemene mechanismen —
  #889 pr_subsidie  (media namen het Belastingdienst-fraudeframe over; Medialogica)
  #890 onderzoeksjournalist_doorbraak (Kleinnijenhuis/Klein-tandem + Correspondent)
  #891 parlementaire_controle (Omtzigt & Leijten → POK → 'Ongekend onrecht')
Elk met een geverifieerd HUMAN/Medialogica-citaat. Ze landen 'voorgesteld' en
tellen pas mee na een menselijke merge.

DIT SCRIPT doet alleen de kleine structurele kant: de twee nog-open affaire-edges
time-boxen op het affaire-venster, zodat de hele cluster netjes in zijn tijd zit.
De meeste edges stonden al op 2013–2019/2021.

  rel 88  De Correspondent → Belastingdienst (doorbraak)  active_until: open → 2021
  rel 65  NOS → BOinK (schijndebat)                        active_until: open → 2021

WAAROM GEEN `vervangen` (afvoeren).  Een eerste versie zette de 9 redundante
org→Belastingdienst-edges (42/86/87/254/255 pr_subsidie, 49/50 parl. controle,
88/171 doorbraak) op `vervangen=1`. Dat brak de M2.6-kernregel "niets wissen, alles
herleidbaar": de validator-check VERVANGEN-LINEAGE (een *fout*) eist dat een
vervangen element een `lineage`-opvolgingsspoor heeft, gekoppeld aan een geaccepteerd
voorstel. Maar `lineage` koppelt relatie→relatie; er ís geen opvolger-*relatie* als
de inhoud naar een mechanisme-*argument* generaliseert. De vervangen-poging is
teruggedraaid. Eigenaarsbesluit: de 9 blijven leven als gedateerde incident-records
(getime-boxt, ~0 score-bijdrage want bronloos/gevloerd); de structurele les leeft op
de mechanismen (889/890/891). Wie ze tóch formeel wil afvoeren: via een
samenvoeg-voorstel met menselijk akkoord (de blessed route die wél lineage maakt).

Niets uit Bucket A wordt aangeraakt: politicus_als_bron (103/104/259/260/261) en
partijlidmaatschap (125/126/131/258) zijn algemene staande banden waar de affaire
slechts een gedateerd *argument* onder is — daar hoort het incident juist thuis.

Conform repo-conventie: eerst backup, dan muteren. Idempotent (slaat al-getime-boxte
rijen over). Volledig omkeerbaar: active_until terug op NULL herstelt de oude toestand.
Reeds toegepast op de live DB juni 2026; opnieuw draaien is een no-op.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-toeslag-generalisatie-2026-06"

# (relatie-id, active_until) — de nog-open affaire-edges hard time-boxen
TIMEBOX = [(88, "2021"), (65, "2021")]


def main():
    if not DB.exists():
        raise SystemExit(f"DB niet gevonden: {DB}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # edit_log.changed_by is een FK naar users(username); de attributietag bestaat als
    # inactief legacy-agent-account (precedent: migrate_tier_herindeling.py).
    conn.execute(
        "INSERT OR IGNORE INTO users (username, kind, role, provenance, active) "
        "VALUES (?, 'agent', 'bijdrager', ?, 0)",
        (CONTRIB, f"legacy-account (structuur-migratie): attributietag '{CONTRIB}' "
                  "voor de toeslagenaffaire-generalisatie"))

    geboxt = []
    for rid, until in TIMEBOX:
        rij = conn.execute(
            "SELECT id, active_until FROM relations WHERE id = ?", (rid,)).fetchone()
        if rij is None:
            print(f"  ! rel {rid} bestaat niet — overgeslagen")
            continue
        if (rij["active_until"] or "") == until:
            print(f"  = rel {rid} al getime-boxt op {until}")
            continue
        oud = rij["active_until"]
        conn.execute("UPDATE relations SET active_until = ? WHERE id = ?", (until, rid))
        conn.execute(
            """INSERT INTO edit_log (table_name, record_id, action, changed_by, old_value, new_value, reason)
               VALUES ('relations', ?, 'updated', ?, ?, ?, ?)""",
            (rid, CONTRIB,
             f'{{"active_until": {oud!r}}}', f'{{"active_until": "{until}"}}',
             "Toeslagenaffaire-generalisatie: open affaire-edge getime-boxt op het "
             "affaire-venster (incident hoort in zijn tijd; mechanisme blijft)."))
        geboxt.append((rid, oud, until))

    conn.commit()
    boxt_str = ", ".join(f"{r}: {o or 'open'}->{u}" for r, o, u in geboxt) or "—"
    print(f"Getime-boxt: {boxt_str}")

    print("\nAffaire-cluster (vervangen=0, gedateerd):")
    for rid in (42, 86, 87, 254, 255, 49, 50, 88, 171, 172, 90, 256, 65):
        r = conn.execute(
            """SELECT r.id, se.name AS bron, te.name AS doel, m.name AS mech,
                      r.active_from, r.active_until
               FROM relations r JOIN entities se ON r.source_id=se.id
               JOIN entities te ON r.target_id=te.id
               LEFT JOIN mechanisms m ON r.mechanism_id=m.id WHERE r.id=?""", (rid,)).fetchone()
        if r:
            print(f"  rel {r['id']}: {r['bron']} → {r['doel']} [{r['mech']}] "
                  f"({r['active_from'] or '?'}–{r['active_until'] or 'open'})")
    conn.close()
    print("\nKlaar. Regenereer de viz: python3 scripts/generate_viz.py")


if __name__ == "__main__":
    main()
