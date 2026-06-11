#!/usr/bin/env python3
"""
Migratie: correctie van foute tijden in het praktijkmodel (juni 2026).

Audit van entities/relations.active_from/active_until vond een
systematische fout: bij ~25 relaties is het GEBOORTEJAAR van de
betrokken persoon als startdatum van de relatie ingevuld (Peter R. de
Vries "beinvloedt de NOS sinds 1956" — zijn geboortejaar; Omtzigt sinds
1974, Eurlings -> KLM sinds 1973, Wouter Bos -> KPMG sinds 1987, enz.).
Een relatie begint pas als de functie/het dienstverband begint.

Correcties hier: waar het juiste jaar publiek goed gedocumenteerd is
(Kamerlidmaatschap, ministerschap, indiensttreding) wordt dat gezet;
waar het beginjaar onbekend is wordt het geboortejaar vervangen door
NULL = "onbegrensd voor zover bekend" — eerlijker dan schijnprecisie.

Daarnaast: entity DPG Media stond op active_from=2019 (jaar van de
naamswijziging), waardoor zijn eigen overnames van PCM (2009) en VNU
Media (2007) voor zijn ontstaan vielen. DPG Media is de hernoemde
De Persgroep (1987); de entiteit krijgt 1987 als start.

Backup-then-migrate; idempotent: een relatie wordt alleen aangepast als
active_from nog op de bekende foute waarde staat. Al gecorrigeerde of
handmatig afwijkende waarden blijven staan.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# (relation_id, foute_from, nieuwe_from, nieuwe_until, rationale)
RELATIE_FIXES = [
    (3,   "1962", None,   None,   "geboortejaar Van Thillo; oprichtingsjaar Epifin onbekend"),
    (48,  "1956", "1978", "2021", "De Vries journalist vanaf 1978 (De Telegraaf); overleden 2021"),
    (53,  "1960", None,   None,   "geboortejaar Leysen; eerste Bilderberg-deelname onbekend"),
    (103, "1974", "2003", None,   "Omtzigt Kamerlid sinds 2003"),
    (125, "1979", None,   None,   "geboortejaar Leijten; jaar SP-lidmaatschap onbekend"),
    (156, "1960", "2013", None,   "oprichting Mediahuis (2013)"),
    (179, "1962", None,   None,   "geboortejaar Van Thillo; Bilderberg-betrokkenheid niet gedateerd"),
    (186, "1956", "1978", "2021", "De Vries journalist vanaf 1978; overleden 2021"),
    (257, "1974", "2003", None,   "Omtzigt Kamerlid sinds 2003"),
    (258, "1979", "2006", "2023", "Leijten Kamerlid 2006-2023"),
    (259, "1974", "2003", None,   "Omtzigt Kamerlid sinds 2003"),
    (260, "1974", "2003", None,   "Omtzigt Kamerlid sinds 2003"),
    (261, "1974", "2003", None,   "Omtzigt Kamerlid sinds 2003"),
    (265, "1956", "1978", "2021", "De Vries journalist vanaf 1978; overleden 2021"),
    (266, "1956", "1978", "2021", "De Vries journalist vanaf 1978; overleden 2021"),
    (325, "1943", None,   None,   "geboortejaar Van Rossem; begin commentaarrol niet scherp dateerbaar"),
    (337, "1976", None,   None,   "geboortejaar Van den Brink; begin EO-loopbaan niet scherp dateerbaar"),
    (340, "1968", "2010", None,   "Jack de Vries naar Hill+Knowlton na aftreden (2010)"),
    (341, "1968", "2007", "2010", "staatssecretaris van Defensie dec 2007 - mei 2010"),
    (342, "1987", "2010", "2013", "Bos partner bij KPMG 2010-2013"),
    (343, "1963", "1998", "2010", "Bos Kamerlid/partijleider/minister 1998-2010"),
    (346, "1973", "2011", "2014", "Eurlings bij KLM 2011-2014 (CEO 2013-2014)"),
    (352, "1976", "2010", "2016", "De Liefde Kamerlid VVD 2010-2016"),
    (353, "1971", "2005", None,   "Knops Kamerlid sinds 2005 na loopbaan als beroepsofficier"),
    (356, "1973", "2010", "2011", "Schaart Kamerlid VVD 2010-2011"),
    (357, "1948", "2006", "2012", "Van der Veen Kamerlid PvdA 2006-2012 na bestuursvoorzitterschap Agis"),
]

# (entity_naam, foute_from, nieuwe_from, rationale)
ENTITY_FIXES = [
    ("DPG Media", "2019", "1987",
     "rechtsvoorganger De Persgroep opgericht 1987, hernoemd tot DPG Media in 2019; "
     "anders vallen de overnames van PCM (2009) en VNU Media (2007) voor het ontstaan"),
]


def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = DB.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB, dst)
    print(f"backup -> {dst.name}")


def main():
    if not DB.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB}")
    backup()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    for rid, fout, van, tot, rationale in RELATIE_FIXES:
        row = cur.execute(
            "SELECT active_from, active_until FROM relations WHERE id=?", (rid,)).fetchone()
        if row is None:
            print(f"WAARSCHUWING: relatie {rid} niet gevonden")
            continue
        huidig_van, huidig_tot = row
        if huidig_van == fout:
            cur.execute("UPDATE relations SET active_from=?, active_until=? WHERE id=?",
                        (van, tot, rid))
            print(f"gecorrigeerd: relatie {rid} [{fout}] -> [{van or '?'} - {tot or 'heden'}] ({rationale})")
        elif (huidig_van, huidig_tot) == (van, tot):
            print(f"al gecorrigeerd: relatie {rid}")
        else:
            print(f"OVERGESLAGEN (handmatig afwijkend): relatie {rid} [{huidig_van}]")

    for name, fout, van, rationale in ENTITY_FIXES:
        row = cur.execute(
            "SELECT id, active_from FROM entities WHERE name=?", (name,)).fetchone()
        if row is None:
            print(f"WAARSCHUWING: entiteit niet gevonden: {name}")
            continue
        eid, huidig = row
        if huidig == fout:
            cur.execute("UPDATE entities SET active_from=? WHERE id=?", (van, eid))
            print(f"gecorrigeerd: entiteit {name} [{fout}] -> [{van}] ({rationale})")
        elif huidig == van:
            print(f"al gecorrigeerd: entiteit {name}")
        else:
            print(f"OVERGESLAGEN (handmatig afwijkend): entiteit {name} [{huidig}]")

    con.commit()
    con.close()
    print("\nklaar — draai scripts/generate_viz.py om de viz bij te werken")


if __name__ == "__main__":
    main()
