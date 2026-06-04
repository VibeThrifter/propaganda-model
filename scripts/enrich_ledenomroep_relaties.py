"""
Verrijking: de `ledenomroep` als volwaardige knoop in het theoretische model.

Aanleiding: in het theoriemodel was `ledenomroep` de bron van precies EEN mechanisme
(`omroepverzuiling -> publiek`) en had het GEEN enkele inkomende verbinding. De structurele
krachten die het Nederlandse omroepbestel uniek maken -- de ledeneis, de NPO-budgetregie en
de ministeriele erkenning -- ontbraken als theorie. Bovendien stuurde de NPO in het
praktijkmodel `bestelsturing` naar de ledenomroepen, terwijl die theorie (`bestelsturing:
omroepkoepel -> mediaorganisatie`) de ledenomroep formeel buiten de sturing liet (een
theorie/instantie-mismatch).

De toevoegingen zijn afgeleid uit LITERATUUR over hoe het bestel echt werkt, niet uit de
instance-data:
  - Mediawet 2008: ledeneis (100.000 leden voor een erkende, 50.000 voor een aspirant-omroep),
    de eis een 'godsdienstige, maatschappelijke of geestelijke stroming' te vertegenwoordigen,
    en het garantiebudget (art. 2.149/2.150: ~50% ledenomroep, 70% taakomroep).
  - Rijksoverheid (Mediawet-uitleg): "De minister van OCW beslist of een omroep een erkenning
    krijgt."
  - WRR, *Aandacht voor media* (2024): pluriformiteit wordt afgemeten aan ledentallen; goed
    bestuur en kwaliteit raken daaraan ondergeschikt; de NPO als centrale sturingsorganisatie.

Onderzoeksframe: pro-elite-/establishment-bias is een EMERGENTE eigenschap van deze structuur.
De ledeneis, de centrale budgetregie en de politieke erkenningspoort zijn structurele filters,
geen complot.

Vier nieuwe/aangescherpte mechanismen geven `ledenomroep` voortaan vijf verbindingen:
  IN   ledeneis           publiek        -> ledenomroep   (eigendom, structureel)
  IN   intekensturing     omroepkoepel   -> ledenomroep   (eigendom, economisch)
  IN   erkenningverlening gezagsinstituut-> ledenomroep   (eigendom, juridisch)
  OUT  omroepverzuiling   ledenomroep    -> publiek       (ideologie; omschrijving aangescherpt)
  OUT  omroepsignatuur    ledenomroep    -> redactie      (ideologie, structureel)

Dit is tevens de eerste LITERATUUR-onderbouwing in het model: argumenten die direct op een
mechanisme (mechanism_id) hangen, met geverifieerde citaten uit Mediawet/Rijksoverheid/WRR.

Volgt de backup-then-migrate-conventie. Idempotent: opnieuw draaien is veilig.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# --- THEORIE: nieuwe / aangescherpte mechanismen -------------------------

NEW_MECHANISMS = [
    {
        "name": "ledeneis",
        "filter": "eigendom",
        "mechanism_type": "structureel",
        "description": (
            "Een omroepvereniging krijgt en behoudt haar erkenning alleen met genoeg betalende "
            "leden: de Mediawet eist minimaal 100.000 leden voor een erkende omroep en 50.000 voor "
            "een aspirant-omroep. Het ledental geldt als bewijs van 'maatschappelijke binding' en "
            "bepaalt mede de zendtijd en het budgetaandeel."
        ),
        "effect": (
            "De omroep richt programmering, marketing en ledenwerving op het binden van (vooral de "
            "bestaande) leden; goed bestuur en kwaliteit raken ondergeschikt aan ledentallen (WRR "
            "2024). Het publiek-als-ledenmarkt wordt zo een structurele filter op wat er gemaakt wordt, "
            "en jongere/diffuse geluiden die geen massalidmaatschap binden vallen weg."
        ),
        "source_role": "publiek",
        "target_role": "ledenomroep",
    },
    {
        "name": "intekensturing",
        "filter": "eigendom",
        "mechanism_type": "economisch",
        "description": (
            "De NPO kent elke omroep een vast garantiebudget toe (~50% voor ledenomroepen, 70% voor "
            "taakomroepen; art. 2.149/2.150 Mediawet) en verdeelt het resterende programmageld "
            "competitief via 'intekening': omroepen pitchen programmavoorstellen die de NPO goedkeurt, "
            "weigert of op een zender plaatst. De stuurruimte van de koepel is wettelijk verruimd van "
            "30% naar 50% van het budget van de erkende omroepen."
        ),
        "effect": (
            "Ledenomroepen schikken hun aanbod naar het genre-, doelgroep- en plaatsingsbeleid van de "
            "koepel om geld en zendtijd te krijgen; de regie verschuift van de verzuilde omroep naar de "
            "centrale sturingsorganisatie ('geen thuisnet': de NPO bepaalt per programma de zender)."
        ),
        "source_role": "omroepkoepel",
        "target_role": "ledenomroep",
    },
    {
        "name": "erkenningverlening",
        "filter": "eigendom",
        "mechanism_type": "juridisch",
        "description": (
            "De minister van OCW beslist per concessieperiode -- op advies van de NPO, de Raad voor "
            "Cultuur en het Commissariaat voor de Media -- of een omroep een erkenning krijgt: de "
            "toegang tot het bestel, het publieke geld en een landelijk podium. De minister kan die "
            "erkenning ook onthouden of intrekken."
        ),
        "effect": (
            "Een politiek-bestuurlijke poort bepaalt welke 'stromingen' een landelijk podium krijgen. "
            "Nieuwe of onwelgevallige geluiden staan of vallen bij de erkenning (bv. de aanvaring rond "
            "Ongehoord Nederland), wat een disciplinerend signaal afgeeft aan het hele bestel."
        ),
        "source_role": "gezagsinstituut",
        "target_role": "ledenomroep",
    },
    {
        "name": "omroepsignatuur",
        "filter": "ideologie",
        "mechanism_type": "structureel",
        "description": (
            "De statutaire godsdienstige, maatschappelijke of geestelijke stroming van een ledenomroep "
            "(christelijk, sociaaldemocratisch, rechts-populistisch, ...) stuurt intern de onderwerp- "
            "en gastenkeuze, toon en bronselectie van de eigen redactie."
        ),
        "effect": (
            "Nieuwsselectie en framing zijn binnen een omroep vooraf gekleurd door de zuil; afwijken van "
            "de eigen signatuur is intern onwaarschijnlijk. Dit is de productie-zijde van de verzuiling "
            "(intern), waarvan `omroepverzuiling` het publiekgerichte resultaat is."
        ),
        "source_role": "ledenomroep",
        "target_role": "redactie",
    },
]

# omroepverzuiling bestaat al (ledenomroep -> publiek); we scherpen alleen de omschrijving aan
# zodat het ondubbelzinnig de EXTERNE pluriformiteit (tussen omroepen, naar het publiek) vat en
# niet overlapt met de nieuwe interne `omroepsignatuur`.
UPDATE_OMROEPVERZUILING = {
    "name": "omroepverzuiling",
    "description": (
        "Het bestel is 'extern pluriform': elke ledenomroep representeert statutair een eigen "
        "godsdienstige, maatschappelijke of geestelijke stroming en brengt vanuit dat perspectief "
        "programma's, gecoordineerd door de NPO voor heel Nederland."
    ),
    "effect": (
        "Het pluralisme zit TUSSEN omroepen, niet BINNEN een redactie, en blijft binnen de grenzen "
        "van het bestel: het publiek krijgt een verzameling vooraf gekleurde, elkaar begrenzende "
        "perspectieven aangeboden. De 'stroming'-eis is vaag gedefinieerd en stamt uit de "
        "20e-eeuwse verzuiling (WRR 2024)."
    ),
}

# --- INSTANTIE-CONSISTENTIE ----------------------------------------------
# De NPO->ledenomroep-relaties dragen nu `bestelsturing` (theorie-target: mediaorganisatie),
# maar hun doelen zijn ledenomroepen. Herbedraad ze naar `intekensturing`. NOS/NTR
# (taakomroepen, rol mediaorganisatie) blijven `bestelsturing`.

# --- LITERATUUR: bronnen --------------------------------------------------

MEDIAWET_SOURCE = {
    "title": "Mediawet 2008",
    "author": "Staten-Generaal",
    "source_type": "wetgeving",
    "publisher": "Overheid.nl",
    "date_published": "2008-12-29",
    "reliability": "primair",
    "summary": (
        "De wet die het Nederlandse mediabestel regelt: erkenning en ledeneisen van omroepen "
        "(o.a. 100.000/50.000 leden, de 'stroming'-eis), het garantiebudget (art. 2.149/2.150) en "
        "de sturende rol van de NPO."
    ),
    "url": "https://wetten.overheid.nl/BWBR0025028/",
}

RIJKSOVERHEID_SOURCE = {
    "title": "Aan welke eisen moet een omroepvereniging voldoen?",
    "author": "Rijksoverheid",
    "source_type": "website",
    "publisher": "Rijksoverheid.nl",
    "date_published": "2024-01-01",
    "reliability": "institutioneel",
    "summary": (
        "Publieksuitleg van de Mediawet-eisen voor omroepverenigingen: ledental, de 'stroming'-eis "
        "en het besluit van de minister van OCW over erkenning."
    ),
    "url": (
        "https://www.rijksoverheid.nl/onderwerpen/media-en-publieke-omroep/vraag-en-antwoord/"
        "aan-welke-eisen-moet-een-omroepvereniging-voldoen"
    ),
}

# --- LITERATUUR: argumenten (de eerste mechanism_id-argumenten in het model) ---
# tuples per argument: (mechanisme, stance, claim, reasoning, weight, status, [citaties])
# citatie: (bron-key, quote, section)   bron-key in {'mediawet','rijksoverheid','wrr'}

LIT_ARGUMENTS = [
    ("ledeneis", "supporting",
     "De Mediawet bindt de erkenning van een omroep rechtstreeks aan het ledental.",
     "Een erkende omroep moet minimaal 100.000 betalende leden hebben, een aspirant-omroep 50.000. "
     "Het ledental functioneert daarmee als toegangsdrempel en als verdeelsleutel voor zendtijd en budget.",
     0.9, "geverifieerd",
     [("rijksoverheid", "minimaal 100.000 betalende leden hebben", "Erkende omroep"),
      ("rijksoverheid", "minimaal 50.000 betalende leden hebben", "Aspirant-omroep")]),
    ("ledeneis", "contextual",
     "De WRR signaleert dat goed bestuur en kwaliteit ondergeschikt raken aan ledentallen.",
     "Pluriformiteit wordt afgemeten aan het halen van de ledendrempel; omroepen ervaren stress door de "
     "marketing die nodig is om die drempel te halen, terwijl vooral jongeren steeds minder lid worden.",
     0.7, "geverifieerd",
     [("wrr", "pluriformiteit wordt beoordeeld op het behalen van het ledental, terwijl goed bestuur en "
       "kwaliteit ondergeschikt zijn aan ledentallen", "Publieke omroep")]),

    ("intekensturing", "supporting",
     "Het budget is deels een vast garantiebudget en deels competitief verdeeld programmageld.",
     "Art. 2.149/2.150 Mediawet legt een garantiebudget vast (~50% voor ledenomroepen, 70% voor "
     "taakomroepen); de rest verdeelt de NPO via intekening op programmavoorstellen, waarbij de "
     "stuurruimte is verruimd van 30% naar 50%.",
     0.85, "geverifieerd",
     [("mediawet", "garantiebudget", "art. 2.149/2.150")]),

    ("erkenningverlening", "supporting",
     "De minister van OCW beslist of een omroep een erkenning krijgt.",
     "De erkenning verschaft toegang tot het bestel, publiek geld en een landelijk podium; het besluit ligt "
     "bij de bewindspersoon (op advies van NPO, Raad voor Cultuur en Commissariaat voor de Media).",
     0.9, "geverifieerd",
     [("rijksoverheid", "De minister van Onderwijs, Cultuur en Wetenschap beslist of een omroep een "
       "erkenning krijgt.", "Erkenning")]),

    ("omroepverzuiling", "supporting",
     "De Mediawet eist dat een omroep een godsdienstige, maatschappelijke of geestelijke stroming vertegenwoordigt.",
     "Die eis institutionaliseert de externe pluriformiteit: diversiteit tussen omroepen in plaats van binnen "
     "een redactie. Het begrip 'stroming' is vaag en stamt uit de verzuiling.",
     0.85, "geverifieerd",
     [("rijksoverheid", "een godsdienstige, maatschappelijke of geestelijke stroming vertegenwoordigen",
       "Stroming")]),

    ("omroepsignatuur", "supporting",
     "De wettelijke 'stroming'-eis bindt niet alleen het profiel maar ook de programma-inhoud van de omroep.",
     "Omroepverenigingen moeten een godsdienstige, maatschappelijke of geestelijke stroming vertegenwoordigen "
     "en maken hun programma's vanuit dat perspectief; de signatuur stuurt zo intern de onderwerp-, gasten- en "
     "bronselectie van de eigen redactie.",
     0.7, "geverifieerd",
     [("rijksoverheid", "een godsdienstige, maatschappelijke of geestelijke stroming vertegenwoordigen",
       "Stroming")]),
]


# --- helpers --------------------------------------------------------------

def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, dest)
    print(f"Backup gemaakt: {dest.name}")


def role_id(conn, name):
    row = conn.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
    if not row:
        raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
    return row[0]


def mechanism_id(conn, name):
    row = conn.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
    if not row:
        raise SystemExit(f"FOUT: mechanisme '{name}' niet gevonden.")
    return row[0]


def upsert_mechanism(conn, m):
    sid, tid = role_id(conn, m["source_role"]), role_id(conn, m["target_role"])
    if conn.execute("SELECT 1 FROM mechanisms WHERE name=?", (m["name"],)).fetchone():
        conn.execute(
            """UPDATE mechanisms SET filter=?, mechanism_type=?, description=?, effect=?,
               source_role_id=?, target_role_id=? WHERE name=?""",
            (m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid, m["name"]))
        print(f"Mechanisme bijgewerkt: {m['name']}")
    else:
        conn.execute(
            """INSERT INTO mechanisms
               (name, filter, mechanism_type, description, effect, source_role_id, target_role_id)
               VALUES (?,?,?,?,?,?,?)""",
            (m["name"], m["filter"], m["mechanism_type"], m["description"], m["effect"], sid, tid))
        print(f"Mechanisme toegevoegd: {m['name']} ({m['source_role']} -> {m['target_role']})")


def reroute_bestelsturing(conn):
    """NPO->ledenomroep-relaties van bestelsturing naar intekensturing (relatie + instantiation)."""
    bid = mechanism_id(conn, "bestelsturing")
    iid = mechanism_id(conn, "intekensturing")
    led = role_id(conn, "ledenomroep")
    rels = conn.execute(
        """SELECT r.id FROM relations r
           JOIN entities src ON r.source_id=src.id
           JOIN entities tgt ON r.target_id=tgt.id
           WHERE src.name='NPO' AND r.mechanism_id=? AND tgt.primary_role_id=?""",
        (bid, led)).fetchall()
    n = 0
    for (rid,) in rels:
        conn.execute("UPDATE relations SET mechanism_id=? WHERE id=?", (iid, rid))
        conn.execute("UPDATE instantiations SET mechanism_id=? WHERE relation_id=? AND mechanism_id=?",
                     (iid, rid, bid))
        n += 1
    print(f"Herbedraad: {n} NPO->ledenomroep-relaties van bestelsturing naar intekensturing "
          f"(NOS/NTR blijven bestelsturing).")


def upsert_source(conn, s):
    row = conn.execute("SELECT id FROM sources WHERE title=?", (s["title"],)).fetchone()
    if row:
        sid = row[0]
        conn.execute("UPDATE sources SET reliability=?, summary=? WHERE id=?",
                     (s["reliability"], s["summary"], sid))
        print(f"Bron bijgewerkt: {s['title']}")
    else:
        conn.execute(
            """INSERT INTO sources (title, author, source_type, publisher, date_published, language, summary, reliability)
               VALUES (?,?,?,?,?, 'nl', ?, ?)""",
            (s["title"], s["author"], s["source_type"], s["publisher"], s["date_published"],
             s["summary"], s["reliability"]))
        sid = conn.execute("SELECT id FROM sources WHERE title=?", (s["title"],)).fetchone()[0]
        print(f"Bron toegevoegd: {s['title']} ({s['reliability']})")
    if s.get("url"):
        if not conn.execute("SELECT 1 FROM source_locations WHERE source_id=? AND location=?",
                            (sid, s["url"])).fetchone():
            conn.execute(
                "INSERT INTO source_locations (source_id, location_type, location) VALUES (?, 'url', ?)",
                (sid, s["url"]))
    return sid


def fix_wrr_reliability(conn):
    conn.execute("UPDATE sources SET reliability='institutioneel' "
                 "WHERE author LIKE '%Regeringsbeleid%' AND reliability='onbeoordeeld'")
    print("WRR-bron op 'institutioneel' gezet.")


def add_lit_argument(conn, src_ids, mech, stance, claim, reasoning, weight, status, citations):
    mid = mechanism_id(conn, mech)
    # idempotent op (mechanism_id, claim)
    if conn.execute("SELECT 1 FROM arguments WHERE mechanism_id=? AND claim=?", (mid, claim)).fetchone():
        return False
    conn.execute(
        """INSERT INTO arguments (mechanism_id, stance, claim, reasoning, weight, status, contributed_by)
           VALUES (?,?,?,?,?,?, 'literatuuronderzoek')""",
        (mid, stance, claim, reasoning, weight, status))
    aid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for src_key, quote, section in citations:
        conn.execute(
            "INSERT INTO citations (argument_id, source_id, quote, section) VALUES (?,?,?,?)",
            (aid, src_ids[src_key], quote, section))
    return True


# --- main -----------------------------------------------------------------

def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("\n[1] theorie: nieuwe mechanismen voor ledenomroep")
    for m in NEW_MECHANISMS:
        upsert_mechanism(conn, m)

    print("\n[2] theorie: omroepverzuiling-omschrijving aanscherpen (externe pluriformiteit)")
    conn.execute("UPDATE mechanisms SET description=?, effect=? WHERE name=?",
                 (UPDATE_OMROEPVERZUILING["description"], UPDATE_OMROEPVERZUILING["effect"],
                  UPDATE_OMROEPVERZUILING["name"]))
    print("omroepverzuiling bijgewerkt.")

    print("\n[3] instantie-consistentie: bestelsturing -> intekensturing voor ledenomroepen")
    reroute_bestelsturing(conn)

    print("\n[4] literatuur: bronnen registreren")
    src_ids = {
        "mediawet": upsert_source(conn, MEDIAWET_SOURCE),
        "rijksoverheid": upsert_source(conn, RIJKSOVERHEID_SOURCE),
    }
    fix_wrr_reliability(conn)
    wrr = conn.execute("SELECT id FROM sources WHERE author LIKE '%Regeringsbeleid%'").fetchone()
    src_ids["wrr"] = wrr[0] if wrr else None

    print("\n[5] literatuur: argumenten op de mechanismen (eerste mechanism_id-argumenten)")
    added = 0
    for mech, stance, claim, reasoning, weight, status, citations in LIT_ARGUMENTS:
        if src_ids.get("wrr") is None:
            citations = [c for c in citations if c[0] != "wrr"]
        if add_lit_argument(conn, src_ids, mech, stance, claim, reasoning, weight, status, citations):
            added += 1
    print(f"  literatuurargumenten toegevoegd: {added} (van {len(LIT_ARGUMENTS)})")

    conn.commit()
    bad = conn.execute("PRAGMA foreign_key_check").fetchall()
    if bad:
        raise SystemExit(f"FOUT: foreign_key_check faalt: {bad}")

    # samenvatting: ledenomroep-edges
    print("\n=== ledenomroep-verbindingen na verrijking ===")
    for r in conn.execute(
        """SELECT m.name, sr.name src, tr.name tgt, m.filter
           FROM mechanisms m LEFT JOIN roles sr ON m.source_role_id=sr.id
           LEFT JOIN roles tr ON m.target_role_id=tr.id
           WHERE sr.name='ledenomroep' OR tr.name='ledenomroep'
           ORDER BY (tr.name='ledenomroep') DESC, m.name"""):
        arrow = "IN " if r[2] == "ledenomroep" else "OUT"
        print(f"  {arrow}  [{r[3]}] {r[0]}: {r[1]} -> {r[2]}")

    rollen = conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    mech = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    litargs = conn.execute("SELECT COUNT(*) FROM arguments WHERE mechanism_id IS NOT NULL OR role_id IS NOT NULL").fetchone()[0]
    cits = conn.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Rollen: {rollen} | mechanismen: {mech} | literatuurargumenten: {litargs} | citaties: {cits}")


if __name__ == "__main__":
    main()
