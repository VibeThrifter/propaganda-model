"""Relevantie-as op bronnen: voegt `sources.onderwerp` toe.

Naast `reliability` (rigueur — hoe degelijk is de bron) krijgt een bron een tweede,
onafhankelijke as: hoe specifiek gaat ze over het ONDERWERP van dit model, het
Nederlandse mediasysteem? Dat stuurt de relevantiefactor in scoring.py:

  nl_systeem   over het Nederlandse mediasysteem            → ×1,15 (gecapt op 1,0)
  algemeen     landneutraal raamwerk/theorie (Man. Consent) → ×1,00
  buitenlands  over een buitenlands mediasysteem (VS, …)    → ×0,85
  onbepaald    nog niet bepaald (default)                   → ×1,00

Alle bestaande bronnen krijgen 'onbepaald' (factor 1,0 = geen score-effect; de golden
snapshot verschuift dus niet). Classificeren is reviewer-werk via de API; deze migratie
zet alleen de structuur neer. Structuurmigratie, geen inhoud.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"


def main():
    if not DB.exists():
        raise SystemExit(f"DB niet gevonden: {DB}")
    backup = DB.parent / f"propaganda_model_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

    conn = sqlite3.connect(DB)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(sources)")}
    if "onderwerp" in cols:
        print("Kolom onderwerp bestaat al — niets te doen.")
        conn.close()
        return
    # SQLite ALTER ... ADD COLUMN met CHECK + NOT NULL DEFAULT is toegestaan.
    conn.execute("""ALTER TABLE sources ADD COLUMN onderwerp TEXT NOT NULL DEFAULT 'onbepaald'
                    CHECK(onderwerp IN ('nl_systeem','algemeen','buitenlands','onbepaald'))""")
    n = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    conn.commit()
    print(f"Kolom onderwerp toegevoegd; {n} bron(nen) op 'onbepaald' (factor 1,0, geen "
          "score-effect tot een reviewer classificeert).")
    conn.close()


if __name__ == "__main__":
    main()
