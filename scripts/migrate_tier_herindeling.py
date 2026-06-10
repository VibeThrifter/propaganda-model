#!/usr/bin/env python3
"""
Migratie: tier-herindeling systemische effecten — vier mechanismen die in de
verkeerde laag zaten, na een audit van alle aard-tiers (direct / halo / hyperedge).

Het toetsingskader (zie DOCUMENTATIE.md § "Aard: direct & systemisch"): een halo is
een staande *toestand* van één drager zonder toerekenbare levende zender; een
groepseigenschap zonder enkele drager hoort in de emergentielaag (hyperedge). De
audit vond vier rijen die daar niet aan voldoen — alle vier zonder relaties,
argumenten of instantiaties, dus schoon te herindelen:

  1. emergente_bias (halo mediaorganisatie → publiek) — systeembrede groeps-
     eigenschap, dubbelt de hyperedge `fabricage_van_consensus`. De unieke
     inhoud (duizenden beslissingen op dezelfde prikkels; "geen controlekamer
     maar zelforganiserend systeem") gaat op in de hyperedge; het mechanisme
     vervalt.
  2. systemische_homeostase (halo mediaorganisatie → publiek) — idem, dubbelt
     `zelfversterkende_homeostase`. De Toeslagenaffaire-nuance (doorbraken
     mogelijk maar uitzonderlijk en tijdelijk) gaat op in de hyperedge.
  3. economische_feedback_loop (halo publiek → mediaorganisatie) — een lus
     tussen meerdere nodes is geen toestand van één node. Wordt een eigen
     hyperedge over {publiek, mediaorganisatie, redactie}, naar het precedent
     van `medialogica` en `verkillingsspiraal` (wederzijdse-wurggreep-lussen).
  4. haagse_stam (direct politicus → journalist) — de groepsbeschrijving van de
     stam in een dyade geperst; de hyperedge `haagse_stam` (Luyendijk-migratie)
     draagt de these al, en de echte dyadische routes bestaan als eigen
     mechanismen (politicus_als_bron, woordvoerdersregie, citaatautorisatie, …).
     Het mechanisme-effect ("agenda machthebbers", "gesloten politieke cultuur")
     staat al integraal in de hyperedge; niets gaat verloren.

Conform repo-conventie: eerst backup (data/propaganda_model_backup_<ts>.db), dan
muteren. Idempotent op naam; weigert te verwijderen zodra er toch relaties,
argumenten of instantiaties aan een mechanisme blijken te hangen.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "propaganda_model.db"
CONTRIB = "modelreview-tier-herindeling-2026-06"

TE_VERWIJDEREN = [
    "emergente_bias",
    "systemische_homeostase",
    "economische_feedback_loop",
    "haagse_stam",
]

FABRICAGE_DESC = (
    "De systematische pro-elite bias die ontstaat uit het samenspel van de vijf "
    "filters (eigendom, advertentie, sourcing, flak, ideologie) — géén centrale "
    "sturing, maar een emergente uitkomst van de gezamenlijke werking: duizenden "
    "dagelijkse beslissingen op basis van dezelfde prikkels (winstmaximalisatie, "
    "risicovermijding) produceren een uniform nieuwsproduct. Het effect is niet "
    "aan één edge toe te schrijven; het is een eigenschap van de hele "
    "configuratie — geen controlekamer, maar een zelforganiserend systeem."
)
FABRICAGE_EFFECT = (
    "Wat het publiek bereikt is binnen een smal, elite-vriendelijk kader "
    "voorgevormd, zonder dat enige actor dat afzonderlijk hoeft te beogen: de "
    "journalist kiest zijn invalshoek niet op bevel van de eigenaar, maar omdat "
    "hij weet dat de chef het goed vindt, dat het online scoort en dat het geen "
    "problemen oplevert."
)
HOMEOSTASE_DESC = (
    "Het systeem houdt zijn eigen evenwicht in stand via terugkoppeling: "
    "socialisatie van journalisten, redactieroutines, elite-referentiekaders en "
    "publieksverwachting corrigeren afwijkingen vanzelf. De stabiliteit is een "
    "emergente lus-eigenschap van de groep, niet van een losse relatie. "
    "Doorbraken zijn mogelijk (Toeslagenaffaire), maar vergen een uitzonderlijke "
    "coalitie van actoren over een lange periode — daarna keert het systeem "
    "terug naar het evenwicht dat elite-belangen dient."
)
HOMEOSTASE_EFFECT = (
    "Afwijkingen van de consensus worden gedempt en de status quo reproduceert "
    "zichzelf over de tijd, zonder expliciete coördinatie. De default is het "
    "volgen van de elite-consensus; er is een enorme hoeveelheid tegenbewijs en "
    "maatschappelijke druk nodig om het narratief duurzaam te veranderen."
)
FEEDBACK_LOOP = {
    "name": "economische_feedback_loop",
    "label": "Economische feedback-loop",
    "category": "eigendom",
    "description": (
        "Dalend vertrouwen → minder abonnees → meer bezuinigingen → slechtere "
        "journalistiek → nog minder vertrouwen. De spiraal is een lus-eigenschap "
        "van de kringloop publiek–mediaorganisatie–redactie als geheel: geen van "
        "de schakels is de zender, elke schakel is tegelijk oorzaak en gevolg."
    ),
    "effect": (
        "Zelfversterkende negatieve spiraal die alle filters versterkt: elke "
        "ronde verkleint de redactionele capaciteit en vergroot de "
        "afhankelijkheid van de overige filters."
    ),
    # redactie hoort erbij: de bezuinigingen landen daar (vgl. redactioneel_
    # budgetcontrole) en "slechtere journalistiek" is haar product.
    "leden": ["publiek", "mediaorganisatie", "redactie"],
}


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

    # ---- 1+2: unieke inhoud van de dubbel-mechanismen in de hyperedges ------
    for naam, desc, effect in [
        ("fabricage_van_consensus", FABRICAGE_DESC, FABRICAGE_EFFECT),
        ("zelfversterkende_homeostase", HOMEOSTASE_DESC, HOMEOSTASE_EFFECT),
    ]:
        n = cur.execute(
            "UPDATE emergent_effects SET description=?, effect=? WHERE name=?",
            (desc, effect, naam),
        ).rowcount
        print(f"{'~' if n else '!'} hyperedge {naam} {'verrijkt' if n else 'NIET GEVONDEN'}")

    # ---- 3: economische_feedback_loop als hyperedge --------------------------
    fl = FEEDBACK_LOOP
    if not cur.execute(
        "SELECT 1 FROM emergent_effects WHERE name=?", (fl["name"],)
    ).fetchone():
        cur.execute(
            "INSERT INTO emergent_effects (name, label, category, description, effect)"
            " VALUES (?,?,?,?,?)",
            (fl["name"], fl["label"], fl["category"], fl["description"], fl["effect"]),
        )
        eff_id = cur.lastrowid
        for rolnaam in fl["leden"]:
            r = cur.execute("SELECT id FROM roles WHERE name=?", (rolnaam,)).fetchone()
            if not r:
                raise SystemExit(f"FOUT: rol ontbreekt: {rolnaam}")
            cur.execute(
                "INSERT INTO emergent_effect_members (emergent_effect_id, role_id)"
                " VALUES (?,?)",
                (eff_id, r[0]),
            )
        print(f"+ hyperedge {fl['name']} ({len(fl['leden'])} leden: {', '.join(fl['leden'])})")
    else:
        print(f"= hyperedge {fl['name']} bestond al")

    # ---- 4: de vier mechanismen verwijderen ----------------------------------
    for naam in TE_VERWIJDEREN:
        row = cur.execute("SELECT id FROM mechanisms WHERE name=?", (naam,)).fetchone()
        if not row:
            print(f"= mechanisme {naam} al weg")
            continue
        mid = row[0]
        in_gebruik = {
            tabel: cur.execute(
                f"SELECT COUNT(*) FROM {tabel} WHERE mechanism_id=?", (mid,)
            ).fetchone()[0]
            for tabel in ("relations", "arguments", "instantiations")
        }
        if any(in_gebruik.values()):
            raise SystemExit(f"FOUT: {naam} is in gebruik ({in_gebruik}); niet verwijderd")
        cur.execute("DELETE FROM mechanism_filters WHERE mechanism_id=?", (mid,))
        cur.execute("DELETE FROM mechanism_themes WHERE mechanism_id=?", (mid,))
        cur.execute("DELETE FROM mechanisms WHERE id=?", (mid,))
        cur.execute(
            "INSERT INTO edit_log (table_name, record_id, action, changed_by,"
            " old_value, reason) VALUES ('mechanisms', ?, 'deleted', ?, ?, ?)",
            (
                mid,
                CONTRIB,
                naam,
                "tier-audit: groepseigenschap/lus hoort in de emergentielaag, "
                "niet als halo of dyade; inhoud opgegaan in de hyperedge",
            ),
        )
        print(f"- mechanisme {naam} (id {mid}) verwijderd")

    con.commit()
    n_mech = cur.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    n_halo = cur.execute(
        "SELECT COUNT(*) FROM mechanisms WHERE aard='veld_eigenschap'"
    ).fetchone()[0]
    n_eff = cur.execute("SELECT COUNT(*) FROM emergent_effects").fetchone()[0]
    print(f"klaar: {n_mech} mechanismen ({n_halo} halo's), {n_eff} emergente effecten")
    con.close()


if __name__ == "__main__":
    main()
