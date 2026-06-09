"""
Modelreview — directe elite-netwerk-routes: hoe een elite-forum (WEF) frames de
infrastructuur in krijgt VOORDAT media iets overnemen. Onderbouwd met gedocumenteerde
programma's/communities (socialisatie & legitimatie — geen bevelstructuur; de bias blijft
emergent). Drie nieuwe theorie-mechanismen vanuit `elite_forum`:

  • young_global_leaders   elite_forum -> politicus
      WEF Young Global Leaders: nominatie + vetting, vorming in een gedeeld referentiekader.
      Gedocumenteerd o.a. Mark Rutte, Karien van Gennip (YGL 2008), Ruben Brekelmans (2025).

  • elite_kennisnetwerk     elite_forum -> denktank
      WEF Global Future Councils (37 councils, ~1/3 academia/denktanks): frames worden er als
      'neutrale' inzichten geproduceerd en verspreid -> expert-/wetenschapslegitimatie.

  • elite_media_netwerk     elite_forum -> columnist_opiniemaker
      WEF Media Leaders-community (hoofdredacteuren, senior columnisten, anchors; Chatham House
      Rule) + Davos-mediapartners (FT, NYT, Reuters, Bloomberg).

De eindbestemming richting media is GEEN directe elite_forum -> mediaorganisatie-pijl: het frame
loopt via deze tussenactoren (en via de eigenaar) en landt als emergente 'common sense' bij het
publiek (zie hegemonische_naturalisatie). Het her-classificeren van `stakeholder_capitalism_frame`
gebeurt apart.

Idempotent; backup-then-migrate. Rollen via naam opgelost.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# naam -> (bron-rol, doel-rol, filter, type, aard, description, effect, [thema's])
MECHANISMS = {
    "young_global_leaders": (
        "elite_forum", "politicus", "ideologie", "psychologisch", "direct",
        "Het elite-forum socialiseert politici via leiderschapsprogramma's zoals het WEF Young "
        "Global Leaders-programma (nominatie + vetting door derden, geen zelf-aanmelding; vorming "
        "in een gedeeld referentiekader). Gedocumenteerde (oud-)deelnemers: o.a. Mark Rutte, "
        "Karien van Gennip (YGL 2008), Ruben Brekelmans (2025), Mabel Wisse Smit, Marietje Schaake.",
        "Politici nemen het elite-referentiekader mee in beleid en publieke uitingen — niet als "
        "opdracht maar als geïnternaliseerde vanzelfsprekendheid (selectie + socialisatie van "
        "reeds machtigen; lidmaatschap is geen sturing).",
        ["elite_netwerk"],
    ),
    "elite_kennisnetwerk": (
        "elite_forum", "denktank", "ideologie", "discursief", "direct",
        "Het elite-forum bindt denktanks en academici in zijn kennisnetwerk (bv. WEF Global Future "
        "Councils: 37 thematische councils, ~1/3 uit academia en denktanks). Daar worden frames als "
        "'neutrale', interdisciplinaire inzichten geproduceerd en verspreid.",
        "Het elite-frame krijgt expert- en wetenschapslegitimatie en stroomt vandaar via "
        "expert_framing / expert_legitimatie / denktank_naar_politiek naar media en politiek.",
        ["elite_netwerk", "kennis_expertise"],
    ),
    "elite_media_netwerk": (
        "elite_forum", "columnist_opiniemaker", "ideologie", "psychologisch", "direct",
        "Het elite-forum netwerkt opiniemakers in zijn media-community (bv. WEF Media Leaders: "
        "hoofdredacteuren, senior columnisten, chief correspondents en anchors met volledige "
        "toegang onder Chatham House Rule) en via Davos-mediapartners (FT, NYT, Reuters, Bloomberg).",
        "Vooraanstaande columnisten/opiniemakers dragen het elite-referentiekader uit naar het "
        "publiek (zie columnist_als_hegemon) — gepresenteerd als 'verstandig midden', niet als belang.",
        ["elite_netwerk"],
    ),
}


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    role_id = {name: rid for rid, name in conn.execute("SELECT id, name FROM roles")}

    for name, (bron, doel, flt, mtype, aard, desc, effect, themes) in MECHANISMS.items():
        sid, tid = role_id.get(bron), role_id.get(doel)
        if sid is None or tid is None:
            print(f"  WAARSCHUWING: rol ontbreekt voor '{name}' ({bron}->{doel}) — overgeslagen.")
            continue
        conn.execute(
            "INSERT OR IGNORE INTO mechanisms (name, filter, mechanism_type, description, effect, "
            "source_role_id, target_role_id, aard) VALUES (?,?,?,?,?,?,?,?)",
            (name, flt, mtype, desc, effect, sid, tid, aard),
        )
        mid = conn.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()[0]
        # Tekst/koppelingen in sync houden bij her-run.
        conn.execute(
            "UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?, "
            "source_role_id=?, target_role_id=?, aard=? WHERE id=?",
            (flt, mtype, desc, effect, sid, tid, aard, mid),
        )
        conn.execute("INSERT OR IGNORE INTO mechanism_filters (mechanism_id, filter) VALUES (?,?)", (mid, flt))
        for th in themes:
            conn.execute("INSERT OR IGNORE INTO mechanism_themes (mechanism_id, theme) VALUES (?,?)", (mid, th))
        print(f"  {name}: {bron} -> {doel} [{flt}, {aard}, thema's: {', '.join(themes)}]")

    conn.commit()
    conn.close()
    print("Klaar.")


if __name__ == "__main__":
    main()
