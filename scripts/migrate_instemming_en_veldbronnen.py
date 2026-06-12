"""
Velden-audit (modelreview juni 2026): bronnen dichten + fabricage-veld rechtzetten.

Aanleiding: audit van de 12 emergente velden en 7 halo's. Structureel klopte alles,
maar drie bevindingen vroegen om een fix:

1. NAAM. `fabricage_van_consensus` is een scheve vertaling van Herman & Chomsky's
   "manufacturing consent" (naar Lippmanns "manufacture of consent", 1922).
   "Consent" = *instemming* van de geregeerden met de bestaande orde — niet
   "consensus" (eensgezindheid tussen actoren) en niet "toestemming" (expliciete
   permissie). Hernoemd naar `fabricage_van_instemming`.

2. LEDEN. De beschrijving claimt sinds migrate_fix_fabricage_description het
   samenspel van de vijf filters, maar de ledenset droeg er vier (mediaeigenaar,
   adverteerder, persbureau, elite_forum) — geen flak-drager. `belanghebbende`
   toegevoegd (de georganiseerde flak-zender, naar het precedent van
   verkillingsspiraal). De ledenset is bewust pars pro toto — één dragende rol
   per filter plus medium en publiek — niet "alle rollen": een hyperedge die
   alles omvat is gelijk aan het model zelf en verklaart niets, en de andere
   elf velden zijn al deelmechanismen van hetzelfde macro-effect. Die curatie
   staat nu expliciet in de beschrijving.

3. BRONNEN. Drie velden en twee halo's misten registratie of citaties:
   - ideologische_homofilie: kerncijfers (D66 27% vs 9%, GL 14% vs 7,3% — TK1998)
     komen uit Vis (2001) 'Haagse waakhonden' (RUG): niet geregistreerd. Worlds of
     Journalism (Hermans 2016, landenrapport NL): niet geregistreerd. Bovens &
     Wille (2011): geregistreerd maar nergens geciteerd.
   - mediahype: Vasterman (2004) geregistreerd maar nergens geciteerd.
   - medialogica: RMO (2003) alleen geciteerd op een padclaim, niet op een
     dragend mechanisme.
   - halo's geweld_intimidatie en elite_referentiekader: nul argumenten.
   Omdat een emergent veld per ontwerp geen eigen discussieboom heeft, hangen de
   nieuwe argumenten op de dragende mechanismen: academische_socialisatie en
   sociologische_homogeniteit (→ ideologische_homofilie), intermedia_agendering
   (→ mediahype), media_agendering (→ medialogica), en de twee lege halo's zelf.

Idempotent; backup-then-migrate. Daarna: python3 scripts/generate_viz.py
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

CONTRIB = "modelreview-velden-bronnenaudit-2026-06"
ACCESSED = "2026-06-12"

OLD_NAME = "fabricage_van_consensus"
NEW_NAME = "fabricage_van_instemming"
NEW_LABEL = "Fabricage van instemming"
NEW_DESC = (
    "De systematische pro-elite bias die ontstaat uit het samenspel van de vijf "
    "filters (eigendom, advertentie, sourcing, flak, ideologie) — géén centrale "
    "sturing, maar een emergente uitkomst van de gezamenlijke werking: duizenden "
    "dagelijkse beslissingen op basis van dezelfde prikkels (winstmaximalisatie, "
    "risicovermijding) produceren een uniform nieuwsproduct dat de instemming van "
    "het publiek met de bestaande orde organiseert. 'Manufacturing consent' "
    "(Lippmann 1922; Herman & Chomsky 1988) is het fabriceren van *instemming* "
    "van de geregeerden — niet van 'consensus' (eensgezindheid tussen actoren) en "
    "niet van 'toestemming' (expliciete permissie). Het effect is niet aan één "
    "edge toe te schrijven; het is een eigenschap van de hele configuratie — geen "
    "controlekamer, maar een zelforganiserend systeem. De ledenset is pars pro "
    "toto: één dragende rol per filter (mediaeigenaar — eigendom; adverteerder — "
    "advertentie; persbureau — sourcing; belanghebbende — flak; elite_forum — "
    "ideologie) plus de mediaorganisatie als locus en het publiek als doelwit; "
    "het effect zelf omspant het hele model."
)

BRONNEN = [
    {
        "title": "Haagse waakhonden. Politieke voorkeur, zelfbeeld van en "
                 "informatiegaring van parlementair journalisten",
        "author": "Vis, J.C.P.M.",
        "source_type": "academisch_artikel",
        "publisher": "Amsterdam University Press (in: H. Wijfjes (red.), "
                     "Journalistieke cultuur in Nederland, pp. 114-136)",
        "date": "2001-01-01",
        "summary": "RUG-onderzoek onder parlementair journalisten: politieke "
                   "voorkeur (D66 en GroenLinks fors oververtegenwoordigd t.o.v. "
                   "de TK1998-uitslag), zelfbeeld en informatiegaring. Empirische "
                   "basis voor de stemvoorkeurcijfers in het emergente veld "
                   "ideologische_homofilie.",
        "locations": [("url", "https://research.rug.nl/nl/publications/"
                              "haagse-waakhonden-politieke-voorkeur-zelfbeeld-"
                              "van-en-informatieg")],
    },
    {
        "title": "Journalists in the Netherlands. Country report "
                 "(Worlds of Journalism Study)",
        "author": "Hermans, L.",
        "source_type": "rapport",
        "publisher": "Worlds of Journalism Study / LMU München",
        "date": "2016-01-01",
        "summary": "Nederlands landenrapport van de Worlds of Journalism Study "
                   "(golf 2012-2016): demografie, opleiding, rolopvatting en "
                   "ervaren autonomie van het Nederlandse journalistencorps.",
        "locations": [("url", "https://epub.ub.uni-muenchen.de/30118/"),
                      ("doi", "10.5282/ubm/epub.30118")],
    },
]


def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{ts}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")
    backup_db()
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    def role_id(name):
        row = cur.execute("SELECT id FROM roles WHERE name=?", (name,)).fetchone()
        if row is None:
            raise SystemExit(f"FOUT: rol '{name}' niet gevonden.")
        return row[0]

    def mech_id(name):
        row = cur.execute("SELECT id FROM mechanisms WHERE name=?", (name,)).fetchone()
        if row is None:
            raise SystemExit(f"FOUT: mechanisme '{name}' niet gevonden.")
        return row[0]

    def source_id(title):
        row = cur.execute("SELECT id FROM sources WHERE title=?", (title,)).fetchone()
        return row[0] if row else None

    # ---- 1+2: fabricage-veld hernoemen, beschrijving en ledenset rechtzetten --
    row = cur.execute(
        "SELECT id FROM emergent_effects WHERE name IN (?,?)",
        (OLD_NAME, NEW_NAME)).fetchone()
    if row is None:
        raise SystemExit(f"FOUT: emergent effect '{OLD_NAME}' niet gevonden.")
    eff_id = row[0]
    cur.execute(
        "UPDATE emergent_effects SET name=?, label=?, description=? WHERE id=?",
        (NEW_NAME, NEW_LABEL, NEW_DESC, eff_id))
    print(f"~ veld {eff_id}: {OLD_NAME} -> {NEW_NAME} (beschrijving bijgewerkt)")
    n = cur.execute(
        "INSERT OR IGNORE INTO emergent_effect_members (emergent_effect_id, role_id) "
        "VALUES (?,?)", (eff_id, role_id("belanghebbende"))).rowcount
    print(f"{'+' if n else '='} lid belanghebbende (flak-drager) "
          f"{'toegevoegd' if n else 'was al lid'}")

    # ---- 3a: ontbrekende bronnen registreren -------------------------------
    bron_ids = {}
    for b in BRONNEN:
        sid = source_id(b["title"])
        if sid:
            print(f"= bron bestaat al ({sid}): {b['title'][:55]}")
        else:
            cur.execute(
                """INSERT INTO sources (title, author, source_type, publisher,
                   date_published, language, summary, reliability)
                   VALUES (?,?,?,?,?,'nl',?,'academisch')""",
                (b["title"], b["author"], b["source_type"], b["publisher"],
                 b["date"], b["summary"]))
            sid = cur.lastrowid
            for loc_type, loc in b["locations"]:
                cur.execute(
                    """INSERT INTO source_locations (source_id, location_type,
                       location, accessed_at) VALUES (?,?,?,?)""",
                    (sid, loc_type, loc, ACCESSED))
            print(f"+ bron {sid}: {b['title'][:55]}")
        bron_ids[b["author"]] = sid

    vis_id = bron_ids["Vis, J.C.P.M."]
    woj_id = bron_ids["Hermans, L."]
    hc_id = source_id("Manufacturing Consent: The Political Economy of the Mass Media")
    bergman_id = source_id("De Nederlandse Nieuwsfabriek: Onthulling van het propagandamodel")
    bw_id = source_id("Diplomademocratie. Over de spanning tussen meritocratie en democratie")
    vasterman_id = source_id("Mediahype")
    rmo_id = source_id("Medialogica. Over het krachtenveld tussen burgers, media en politiek")
    persveilig_id = source_id("Agressie en bedreiging richting journalisten")
    for naam, sid in [("H&C", hc_id), ("Bergman", bergman_id), ("Bovens & Wille", bw_id),
                      ("Vasterman", vasterman_id), ("RMO", rmo_id),
                      ("PersVeilig", persveilig_id)]:
        if sid is None:
            raise SystemExit(f"FOUT: bestaande bron '{naam}' niet gevonden.")

    # ---- 3b: argumenten + citaties op de dragende mechanismen ---------------
    def add_arg(mechanism, stance, claim, reasoning, weight, citations):
        mid = mech_id(mechanism)
        if cur.execute("SELECT 1 FROM arguments WHERE mechanism_id=? AND claim=?",
                       (mid, claim)).fetchone():
            print(f"= argument bestaat al bij {mechanism}")
            return
        cur.execute(
            """INSERT INTO arguments (mechanism_id, stance, claim, reasoning,
               weight, status, contributed_by)
               VALUES (?,?,?,?,?,'ongecontroleerd',?)""",
            (mid, stance, claim, reasoning, weight, CONTRIB))
        aid = cur.lastrowid
        for sid, quote, page, ctx in citations:
            cur.execute(
                "INSERT INTO citations (argument_id, source_id, quote, page, context) "
                "VALUES (?,?,?,?,?)", (aid, sid, quote, page, ctx))
        print(f"+ argument ({stance}) bij {mechanism} ({len(citations)} citatie(s))")

    # ideologische_homofilie: literatuurpoot (Bovens & Wille, nu eindelijk geciteerd)
    add_arg(
        "academische_socialisatie", "supporting",
        "Politiek, bestuur, journalistiek en maatschappelijke instituties worden "
        "gedomineerd door hoogopgeleiden uit dezelfde academische vormingsinstituten "
        "— een diplomademocratie waarin journalist en bron dezelfde vorming delen.",
        "Bovens & Wille documenteren de oververtegenwoordiging van academici in "
        "alle Nederlandse instituties; doordat journalist én 'onafhankelijke' bron "
        "uit dezelfde instituten komen, draagt deze socialisatie het emergente "
        "veld ideologische_homofilie.",
        0.60,
        [(bw_id,
          "Typering van de kernthese: Nederland ontwikkelt zich tot een "
          "diplomademocratie — een democratie bestuurd door de burgers met de "
          "hoogste diploma's; academici domineren politiek, bestuur en de "
          "instituties daaromheen.",
          None,
          "kernthese Bovens & Wille (2011); typering, geen letterlijk citaat")])

    # ideologische_homofilie: empirische poot (stemvoorkeur + samenstelling),
    # tegelijk de magere sociologische_homogeniteit-halo versterkt
    add_arg(
        "sociologische_homogeniteit", "supporting",
        "Het journalistencorps is sociologisch smal: parlementair journalisten "
        "stemden bij TK1998 27% D66 (landelijk 9%) en 14% GroenLinks (landelijk "
        "7,3%), en het corps als geheel is homogeen hoogopgeleid.",
        "Stemvoorkeur- en samenstellingsdata onderbouwen de halo op de redactie "
        "(blinde vlekken door eenzijdige samenstelling) en leveren de empirie "
        "voor het emergente veld ideologische_homofilie.",
        0.65,
        [(vis_id,
          "Typering: parlementair journalisten wijken in politieke voorkeur sterk "
          "af van het electoraat — D66 27% tegenover 9% landelijk, GroenLinks 14% "
          "tegenover 7,3% (TK1998).",
          "pp. 114-136",
          "cijfers zoals aangehaald in het veld ideologische_homofilie; typering, "
          "geen letterlijk citaat"),
         (woj_id,
          "Typering: de Nederlandse journalist is overwegend hoogopgeleid, met "
          "gemiddeld bijna 19 jaar ervaring — het corps is demografisch en qua "
          "vorming opvallend eenvormig.",
          None,
          "WJS-landenrapport NL (golf 2012-2016); typering van de "
          "samenstellingsbevindingen")])

    # mediahype: Vasterman eindelijk geciteerd, op het dragende mechanisme
    add_arg(
        "intermedia_agendering", "supporting",
        "Nieuwsgolven versterken zichzelf: na een sleutelgebeurtenis verlagen "
        "media gezamenlijk de nieuwsdrempel en jagen ze elkaars aandacht aan "
        "(pack journalism), waardoor een hype groeit zonder nieuwe feiten.",
        "Vastermans mediahype is de positieve-feedbackvariant van "
        "intermedia-agendering; dit argument draagt tegelijk het emergente veld "
        "mediahype.",
        0.65,
        [(vasterman_id,
          "Typering van de kernthese: een mediahype is een mediabrede, zichzelf "
          "versterkende nieuwsgolf die ontstaat doordat media elkaars aandacht "
          "als bewijs van nieuwswaarde nemen — de golf groeit los van de "
          "onderliggende gebeurtenissen.",
          None,
          "Vasterman (2004); typering, geen letterlijk citaat")])

    # medialogica: RMO op het dragende mechanisme (stond alleen op een padclaim)
    add_arg(
        "media_agendering", "supporting",
        "Het parlement laat zich sturen door wat gisteren in de media stond: "
        "politiek gedrag richt zich naar de medialogica, waardoor incidenten "
        "inhoud verdringen — een wurggreep waar geen partij eenzijdig uit kan.",
        "Het RMO-rapport (2003) is de institutionele bevestiging van "
        "media->politiek-agendering en draagt het emergente veld medialogica.",
        0.70,
        [(rmo_id,
          "Politiek en media zitten gevangen in een patroon van medialogica; "
          "personen, conflicten en incidenten verdringen inhoud en "
          "langetermijnbeleid.",
          None,
          "kernbevinding RMO Medialogica (2003); typering, geen letterlijk "
          "rapportcitaat")])

    # halo geweld_intimidatie: was leeg, terwijl de doc de PersVeilig-cijfers noemt
    add_arg(
        "geweld_intimidatie", "supporting",
        "Agressie en bedreiging tegen journalisten zijn wijdverbreid en nemen "
        "toe: 8 op de 10 journalisten heeft ermee te maken (6 op de 10 in 2017) "
        "en 93% ziet er een reëel gevaar voor de persvrijheid in.",
        "Empirische basis voor de halo op de journalist: de dreiging is een "
        "staande toestand zonder toerekenbare afzender — precies de "
        "veld_eigenschap die dit mechanisme modelleert.",
        0.75,
        [(persveilig_id,
          "8 op de 10 respondenten heeft ervaring met geweld of bedreiging; 93% "
          "ziet agressie en bedreiging als een reëel gevaar voor de persvrijheid.",
          None,
          "kernbevindingen PersVeilig/I&O (2021); typering, geen letterlijk "
          "rapportcitaat")])

    # halo elite_referentiekader: was leeg; H&C + Bergman zijn de natuurlijke dragers
    add_arg(
        "elite_referentiekader", "supporting",
        "Media opereren binnen het referentiekader van gevestigde "
        "elite-instituties: hun agenda en premissen gelden als neutraal "
        "vertrekpunt, zonder dat daar een aanwijsbare handeling voor nodig is.",
        "Herman & Chomsky's ideologie-filter en Bergmans Nederlandse toepassing "
        "beschrijven deze staande toestand; de herkomst is diffuus — vandaar een "
        "veld_eigenschap-halo in plaats van een gerichte edge.",
        0.60,
        [(hc_id,
          "Typering: het nieuws beweegt zich binnen de premissen van de "
          "gevestigde machtscentra; wat daarbuiten valt verschijnt als onserieus "
          "of ongeloofwaardig.",
          None,
          "ideologische premissen / vijfde filter, Manufacturing Consent (1988); "
          "typering"),
         (bergman_id,
          "Typering: ook Nederlandse redacties opereren binnen een "
          "elite-consensus die als gezond verstand wordt ervaren.",
          None,
          "Bergman (2014), Nederlandse toepassing van het propagandamodel; "
          "typering")])

    con.commit()

    # ---- samenvatting --------------------------------------------------------
    for label, q in (
        ("sources", "SELECT COUNT(*) FROM sources"),
        ("arguments", "SELECT COUNT(*) FROM arguments"),
        ("citations", "SELECT COUNT(*) FROM citations"),
        ("leden fabricage", "SELECT COUNT(*) FROM emergent_effect_members "
                            f"WHERE emergent_effect_id={eff_id}"),
    ):
        print(f"{label:16s}: {cur.execute(q).fetchone()[0]}")
    con.close()
    print("klaar. Vergeet niet: python3 scripts/generate_viz.py")


if __name__ == "__main__":
    main()
