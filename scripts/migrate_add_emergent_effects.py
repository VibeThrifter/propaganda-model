"""
Modelreview — emergente effecten als *hyperedge* (groep), niet als dyadische relatie.

Aanleiding: emergentie ontstaat uit de wisselwerking tussen MEERDERE rollen/edges samen
en is per definitie niet in een 1-op-1 relatie te vangen. De bestaande `aard`-niveaus
(`veld_instantiatie`/`veld_eigenschap`) hangen nog altijd aan één bron→doel-paar; dat
leest als een direct effect. Een *emergent effect* hoort daarom bij een GROEP rollen:

  emergent_effects          — het emergente effect zelf (abstract, theorie-laag): een
                              systeemeigenschap die uit het samenspel van leden voortkomt.
  emergent_effect_members   — hyperedge: welke rollen dragen samen dit effect (N leden).

In de viz (theoriemodel, onder de veld-effecten-toggle) wordt dit een transparant VELD
dat de ledengroep omsluit, met een label — geen pijl, geen bron. Het effect = het geheel.

Idempotent; backup-then-migrate. Leden worden via rolNAAM opgelost (robuust tegen id-drift).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# Tabellen (ook in schema.sql voor verse builds).
DDL = """
CREATE TABLE IF NOT EXISTS emergent_effects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,            -- machine-naam, bv. 'fabricage_van_consensus'
    label TEXT NOT NULL,                  -- weergavenaam, bv. 'Fabricage van consensus'
    category TEXT NOT NULL DEFAULT 'systeemactor' CHECK(category IN (
        'eigendom','advertentie','sourcing','flak','ideologie','systeemactor','overig'
    )),
    description TEXT NOT NULL,            -- wat is het emergente effect (uit welk samenspel)
    effect TEXT NOT NULL                 -- gevolg voor de berichtgeving
);
CREATE TABLE IF NOT EXISTS emergent_effect_members (
    emergent_effect_id INTEGER NOT NULL REFERENCES emergent_effects(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    PRIMARY KEY (emergent_effect_id, role_id)
);
"""

# Seed: machine-naam -> (label, category, description, effect, [lid-rolnamen]).
# De ledensets spannen bewust meerdere filters: de emergentie zit in het samenspel.
EFFECTS = {
    "fabricage_van_consensus": (
        "Fabricage van consensus",
        "systeemactor",
        "De systematische pro-elite bias die ontstaat uit het samenspel van de vijf filters "
        "(eigendom, advertentie, sourcing, ideologie) — géén centrale sturing, maar een "
        "emergente uitkomst van de gezamenlijke werking. Het effect is niet aan één edge "
        "toe te schrijven; het is een eigenschap van de hele configuratie.",
        "Wat het publiek bereikt is binnen een smal, elite-vriendelijk kader voorgevormd, "
        "zonder dat enige actor dat afzonderlijk hoeft te beogen.",
        ["mediaeigenaar", "adverteerder", "persbureau", "elite_forum", "mediaorganisatie", "publiek"],
    ),
    "zelfversterkende_homeostase": (
        "Zelfversterkende homeostase",
        "systeemactor",
        "Het systeem houdt zijn eigen evenwicht in stand via terugkoppeling: socialisatie van "
        "journalisten, redactieroutines, elite-referentiekaders en publieksverwachting "
        "corrigeren afwijkingen vanzelf. De stabiliteit is een emergente lus-eigenschap van de "
        "groep, niet van een losse relatie.",
        "Afwijkingen van de consensus worden gedempt en de status quo reproduceert zichzelf "
        "over de tijd, zonder expliciete coördinatie.",
        ["mediaorganisatie", "redactie", "journalist", "elite_forum", "publiek"],
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
    conn.executescript(DDL)
    print("Tabellen gegarandeerd: emergent_effects, emergent_effect_members")

    role_id = {name: rid for rid, name in conn.execute("SELECT id, name FROM roles")}

    for name, (label, cat, desc, effect, members) in EFFECTS.items():
        cur = conn.execute(
            "INSERT OR IGNORE INTO emergent_effects (name, label, category, description, effect) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, label, cat, desc, effect),
        )
        eff_id = conn.execute("SELECT id FROM emergent_effects WHERE name = ?", (name,)).fetchone()[0]
        # Beschrijving/effect bijwerken (idempotent her-run pakt tekstwijzigingen mee).
        conn.execute(
            "UPDATE emergent_effects SET label=?, category=?, description=?, effect=? WHERE id=?",
            (label, cat, desc, effect, eff_id),
        )
        # Leden (her)zetten: eerst leeg, dan vullen — zo blijft de ledenset in sync met dit script.
        conn.execute("DELETE FROM emergent_effect_members WHERE emergent_effect_id=?", (eff_id,))
        kept = []
        for rn in members:
            rid = role_id.get(rn)
            if rid is None:
                print(f"  WAARSCHUWING: rol '{rn}' niet gevonden — overgeslagen voor '{name}'.")
                continue
            conn.execute(
                "INSERT OR IGNORE INTO emergent_effect_members (emergent_effect_id, role_id) VALUES (?, ?)",
                (eff_id, rid),
            )
            kept.append(rn)
        print(f"  {label}: {len(kept)} leden ({', '.join(kept)})")

    conn.commit()
    n_eff = conn.execute("SELECT COUNT(*) FROM emergent_effects").fetchone()[0]
    n_mem = conn.execute("SELECT COUNT(*) FROM emergent_effect_members").fetchone()[0]
    conn.close()
    print(f"\nKlaar: {n_eff} emergente effecten, {n_mem} lidmaatschappen.")


if __name__ == "__main__":
    main()
