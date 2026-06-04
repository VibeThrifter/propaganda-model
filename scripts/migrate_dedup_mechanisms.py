"""
Modelreview — ontdubbeling van het theoretische model (mechanismen), ronde A+B.

Achtergrond. Het mechanismenregister was organisch gegroeid via opeenvolgende
enrich-scripts (v1 / v2 / comprehensive), waardoor dezelfde theoretische 'relatie'
(source_role -> target_role) soms meermaals onder verschillende namen was ingevoerd.
Deze migratie voegt die duplicaten samen (A) en ontwart/scherpt sterk overlappende
mechanismen (B). Het toetst NIET tegen de praktijkdata maar tegen de literatuur
(Herman & Chomsky over de vijf filters, Gandy's 'information subsidy', Gramsci,
Chomsky's 'spectrum of allowable opinion'). Bewust verdedigde onderscheidingen uit
DOCUMENTATIE.md (actief/passief aandeelhouderschap, de persbureau-routines, de
borging-familie, denktank-instituut vs. individuele expert) blijven ongemoeid.

Belangrijk: alle samen-te-voegen ('loser') mechanismen hebben 0 verwijzingen
(relations/instantiations/arguments) — de 'survivor' draagt telkens alle data.
De merge relinkt toch defensief eerst (idempotent, veilig bij latere data) en
verwijdert daarna de loser. Geen schemawijziging; alle enum-/rolwaarden bestaan al.
Volgt de backup-then-migrate-conventie.

A. ECHTE DUPLICATEN (samenvoegen):
   A1 lobby_informatievoorziening      -> lobbyist_naar_politicus
   A2 slapp_tegen_journalist           -> juridische_dreiging
   A3 elite_forum_ideologie            -> ideologische_synchronisatie
   A4 pr_naar_journalist               -> pr_subsidie
   A5 parlementaire_doorbraak          -> parlementaire_controle
   A6 online_intimidatie_journalist + chilling_effect_geweld -> geweld_intimidatie
      (de geweld/intimidatie-drieling: één mechanisme dat fysiek én online geweld en
       het brede chilling effect dekt; de '61%'-cijfers stonden 3x dubbel.)

B. STERKE OVERLAP (samenvoegen of aanscherpen):
   B1 denktank_naar_media + denktank_legitimatie -> expert_framing
   B2 overton_bewaking                 -> spectrum_bewaking
   B3 redactioneel_conformisme         -> zelfcensuur
   B4 morele_chantage                  -> etikettering
   B5 politieke_flak                   -> publieke_aanval
   B7 commerciele_content_druk         -> supportive_selling_environment
   B8 platform_nieuwsselectie          -> algoritmische_filtering
   B6 advertentiedruk / commerciele_afhankelijkheid : NIET samenvoegen, wel
      aanscherpen (4 = structurele afhankelijkheid; 3 = actieve disciplinering).
   B9 bron_afhankelijkheid : aanscherpen tot generiek-structureel; de stam-cultuur
      blijft `haagse_stam`, de bron-rol blijft `politicus_als_bron` (niet samengevoegd).
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "propaganda_model.db"

# --- A + B: merges (loser -> survivor) ---------------------------------------
MERGES = [
    ("lobby_informatievoorziening", "lobbyist_naar_politicus"),   # A1
    ("slapp_tegen_journalist", "juridische_dreiging"),            # A2
    ("elite_forum_ideologie", "ideologische_synchronisatie"),     # A3
    ("pr_naar_journalist", "pr_subsidie"),                        # A4
    ("parlementaire_doorbraak", "parlementaire_controle"),        # A5
    ("online_intimidatie_journalist", "geweld_intimidatie"),      # A6
    ("chilling_effect_geweld", "geweld_intimidatie"),             # A6
    ("denktank_naar_media", "expert_framing"),                    # B1
    ("denktank_legitimatie", "expert_framing"),                   # B1
    ("overton_bewaking", "spectrum_bewaking"),                    # B2
    ("redactioneel_conformisme", "zelfcensuur"),                  # B3
    ("morele_chantage", "etikettering"),                          # B4
    ("politieke_flak", "publieke_aanval"),                        # B5
    ("commerciele_content_druk", "supportive_selling_environment"),  # B7
    ("platform_nieuwsselectie", "algoritmische_filtering"),       # B8
]

# --- Survivor-aanscherpingen + B6/B9 (alleen opgegeven velden) ---------------
ENRICH = [
    # A1 ---------------------------------------------------------------------
    {
        "name": "lobbyist_naar_politicus",
        "description": (
            "Lobbyisten leveren kant-en-klare informatie, conceptamendementen en zelfs complete "
            "Kamervragen aan parlementsleden; politici — en via hen journalisten — zijn afhankelijk "
            "van deze informatieketen."
        ),
        "effect": (
            "Bedrijfs- en sectorbelangen worden via het lobbycircuit in parlementaire vragen en de "
            "media-agenda ingebracht zonder dat de oorsprong zichtbaar is; niet-gekozen "
            "belangenbehartigers sturen mee in de besluitvorming."
        ),
    },
    # A2 ---------------------------------------------------------------------
    {
        "name": "juridische_dreiging",
        "description": (
            "Een belanghebbende — doorgaans een vermogend bedrijf of individu — dreigt met of start "
            "kostbare, strategische rechtszaken (SLAPPs) tegen kritische journalisten. Het doel is "
            "zelden de zaak winnen maar de journalist financieel en psychologisch uitputten."
        ),
        "effect": (
            "Chilling effect: niet alleen het individuele slachtoffer maar de hele redactie wordt "
            "risicomijdender en vermijdt onderwerpen rond kapitaalkrachtige partijen."
        ),
    },
    # A3 ---------------------------------------------------------------------
    {
        "name": "ideologische_synchronisatie",
        "description": (
            "Elite-fora (Bilderberg, WEF/Davos, European Round Table of Industrialists) "
            "synchroniseren het wereldbeeld van de transnationale elite: media-eigenaren, CEO's, "
            "politici en academici komen besloten samen, doorgaans onder de Chatham House Rule."
        ),
        "effect": (
            "Consensus rond vrijemarktkapitalisme wordt gesmeed buiten het democratisch proces; het "
            "gedeelde referentiekader van de besluitvormers sijpelt door naar media, politiek en beleid."
        ),
    },
    # A4 ---------------------------------------------------------------------
    {
        "name": "pr_subsidie",
        "description": (
            "PR- en persvoorlichting (persberichten, kant-en-klare interviews, beeldmateriaal, "
            "mediatrainingen) wordt wegens tijds- en kostendruk grotendeels ongecontroleerd als "
            "nieuws overgenomen — Gandy's 'information subsidy'."
        ),
        "effect": (
            "Het corporate- en overheidsnarratief wordt onkritisch verspreid; bedrijfsbelangen "
            "verschijnen verpakt als nieuwswaardige verhalen."
        ),
    },
    # A5 ---------------------------------------------------------------------
    {
        "name": "parlementaire_controle",
        "description": (
            "Parlementaire controle en parlementair onderzoek kunnen filters doorbreken en "
            "misstanden blootleggen die media hebben gemist of genegeerd — mits een coalitie van "
            "journalisten, politici, burgers en advocaten lang genoeg volhoudt (Commissie Ongekend "
            "Onrecht, Toeslagenaffaire)."
        ),
        "effect": (
            "Narratieve verschuiving mogelijk (van 'fraude' naar 'onrecht'), maar het systeem is niet "
            "monolithisch: het bezit een sterke homeostase die zulke doorbraken uitzonderlijk maakt."
        ),
    },
    # A6 ---------------------------------------------------------------------
    {
        "name": "geweld_intimidatie",
        "description": (
            "Fysiek én online geweld tegen journalisten: bedreigingen, doxing en gecoördineerde "
            "online haatcampagnes — disproportioneel gericht op vrouwen en minderheden — en in het "
            "extreme geval moord (Peter R. de Vries, 2021)."
        ),
        "effect": (
            "Directe bedreiging van de journalistieke veiligheid én een breed chilling effect: 61% van "
            "de Nederlandse journalisten ervaart intimidatie, misdaad- en kritische verslaggeving "
            "worden risicovoller en hele redacties — niet alleen de individuele slachtoffers — worden "
            "risicomijdender."
        ),
    },
    # B1 ---------------------------------------------------------------------
    {
        "name": "expert_framing",
        "description": (
            "Door elites/sponsors gefinancierde denktanks leveren schijnbaar objectieve experts en "
            "analyses die media als 'neutraal' opvoeren (NAVO-gezinde instituten als HCSS en "
            "Clingendael als 'onafhankelijke' commentatoren). Ze produceren effectief 'argumenten op "
            "bestelling'. (De financieringsband zelf is `denktank_financiering_bias`; de individuele "
            "deskundige is `expert_legitimatie`.)"
        ),
        "effect": (
            "Schijn van wetenschappelijke objectiviteit terwijl het debat wordt begrensd; beleid dat "
            "de belangen van de financiers dient, krijgt het aureool van neutrale expertise."
        ),
    },
    # B2 ---------------------------------------------------------------------
    {
        "name": "spectrum_bewaking",
        "description": (
            "Chomsky's 'spectrum van toegestane opinie' (en het verwante Overton-venster): levendig "
            "debat over details wordt aangemoedigd, maar fundamentele premissen blijven buiten schot "
            "— discussie over wápens voor Oekraïne, niet over de premisse van militaire steun zelf."
        ),
        "effect": (
            "Illusie van een vrije, open pers terwijl de door de elite gedefinieerde consensus "
            "overeind blijft; wie buiten het spectrum treedt, wordt gemarginaliseerd als complotdenker "
            "of populist."
        ),
    },
    # B3 ---------------------------------------------------------------------
    {
        "name": "zelfcensuur",
        "description": (
            "Intern conformisme en groepsdruk op sociologisch homogene redacties: journalisten leren "
            "de ongeschreven regels en passen zich aan — aan collega's, chefs en de redactiecultuur — "
            "uit angst voor professionele en sociale repercussies."
        ),
        "effect": (
            "Controversiële onderwerpen en invalshoeken worden vermeden zonder externe instructie. "
            "Neurowetenschappelijk wordt een afwijkende mening verwerkt als 'foutsignaal'."
        ),
    },
    # B4 ---------------------------------------------------------------------
    {
        "name": "etikettering",
        "description": (
            "Diskwalificeren van kritiek door de boodschapper te labelen i.p.v. inhoudelijk te "
            "weerleggen: van 'wappie' en 'complotdenker' tot 'Poetin-versteher' en "
            "'Kremlin-propagandist'. De criticus wordt zo in het kamp van het irrationele of van de "
            "vijand geplaatst."
        ),
        "effect": (
            "Legitieme vragen over proportionaliteit, grondrechten en context worden besmet door "
            "associatie met extremen (reductio ad absurdum) en uit het debat geplaatst; de "
            "bronselectie versmalt tot consensus-bevestigende stemmen."
        ),
    },
    # B5 ---------------------------------------------------------------------
    {
        "name": "publieke_aanval",
        "description": (
            "Politici brengen een journalist, medium of de publieke omroep publiekelijk in diskrediet "
            "of dreigen met beleidsmaatregelen (bv. de PVV die de publieke omroep wil afschaffen)."
        ),
        "effect": (
            "Reputatieschade, zelfcensuur en een vijandig werkklimaat; ondermijning van het publieke "
            "vertrouwen in de media. Redacties worden voorzichtiger om politieke aanvallen te vermijden."
        ),
    },
    # B7 ---------------------------------------------------------------------
    {
        "name": "supportive_selling_environment",
        "description": (
            "Media creëren een redactionele omgeving die bevorderlijk is voor de commerciële "
            "boodschap — optimistisch, apolitiek, lifestyle- en consumptiegericht — omdat adverteerders "
            "een gunstig klimaat als voorwaarde stellen. In de hedendaagse vorm vervaagt dit via native "
            "advertising, branded content en gesponsorde rubrieken de grens tussen journalistiek en reclame."
        ),
        "effect": (
            "Structurele voorkeur voor content die het consumentistische wereldbeeld bevestigt; "
            "systeemkritiek past niet in dit model en de scheiding redactie/commercie erodeert."
        ),
    },
    # B8 ---------------------------------------------------------------------
    {
        "name": "algoritmische_filtering",
        "description": (
            "Techplatforms (Google, Meta, TikTok) selecteren welk nieuws zichtbaar wordt op basis van "
            "engagement-maximalisatie in plaats van journalistieke waarden; emotionele content (woede, "
            "verontwaardiging) krijgt voorrang."
        ),
        "effect": (
            "Emotionele, polariserende content wordt bevoordeeld; nuance en context verdwijnen. (De "
            "aanpassing van redacties aan deze logica loopt via `platform_verdienmodel_druk`, de "
            "socialisatie van het publiek via `algoritmische_socialisatie`.)"
        ),
    },
    # B6 — aanscherpen, NIET samenvoegen -------------------------------------
    {
        "name": "commerciele_afhankelijkheid",
        "mechanism_type": "structureel",
        "description": (
            "Het medium is voor zijn voortbestaan structureel afhankelijk van advertentie-inkomsten; "
            "adverteerders leveren zo de feitelijke 'licentie om te opereren' (H&C's tweede filter). "
            "Deze afhankelijkheid werkt ook zónder expliciete druk."
        ),
        "effect": (
            "Een permanente, structurele voorkeur voor een commercie-vriendelijke redactionele "
            "omgeving; de afhankelijkheid is de basisvoorwaarde waarop de actieve druk "
            "(`advertentiedruk`) kan inwerken."
        ),
    },
    {
        "name": "advertentiedruk",
        "description": (
            "De actieve, disciplinerende variant bovenop de structurele `commerciele_afhankelijkheid`: "
            "adverteerders trekken budget terug of dreigen daarmee bij onwelgevallige berichtgeving "
            "(de 'stok')."
        ),
        "effect": "Zelfcensuur en het vermijden van kritiek op grote adverteerders.",
    },
    # B9 — aanscherpen, NIET samenvoegen -------------------------------------
    {
        "name": "bron_afhankelijkheid",
        "description": (
            "Media zijn voor snelle, goedkope berichtgeving afhankelijk van een beperkt aantal "
            "routineuze, officiële bronnen (overheid, instituties, woordvoerders). Wie zo'n bron "
            "levert, levert ook het frame."
        ),
        "effect": (
            "Het overheids- en instellingsperspectief wordt standaard het vertrekpunt; kritische "
            "vragen blijven achterwege om de toegang niet te verspelen. (De NL-specifieke stamcultuur "
            "hiervan is `haagse_stam`; de politicus als concrete bron is `politicus_als_bron`.)"
        ),
    },
]


def backup_db():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"propaganda_model_backup_{timestamp}.db"
    shutil.copy(DB_PATH, backup_path)
    print(f"Backup gemaakt: {backup_path.name}")


def mech_id(conn, name):
    row = conn.execute("SELECT id FROM mechanisms WHERE name = ?", (name,)).fetchone()
    return row[0] if row else None


def merge_mechanism(conn, loser_name, survivor_name):
    """Hang alle verwijzingen van mechanisme `loser_name` om naar `survivor_name`
    en verwijder de loser. Idempotent: als de loser al weg is, gebeurt er niets."""
    lid = mech_id(conn, loser_name)
    if lid is None:
        print(f"  '{loser_name}' bestaat niet meer — merge al uitgevoerd, overgeslagen.")
        return
    sid = mech_id(conn, survivor_name)
    if sid is None:
        raise SystemExit(f"FOUT: survivor-mechanisme '{survivor_name}' niet gevonden.")

    n_rel = conn.execute("SELECT COUNT(*) FROM relations WHERE mechanism_id=?", (lid,)).fetchone()[0]
    n_ins = conn.execute("SELECT COUNT(*) FROM instantiations WHERE mechanism_id=?", (lid,)).fetchone()[0]
    n_arg = conn.execute("SELECT COUNT(*) FROM arguments WHERE mechanism_id=?", (lid,)).fetchone()[0]

    # relations + literatuur-argumenten: simpel omhangen
    conn.execute("UPDATE relations SET mechanism_id=? WHERE mechanism_id=?", (sid, lid))
    conn.execute("UPDATE arguments SET mechanism_id=? WHERE mechanism_id=?", (sid, lid))
    # instantiations: unieke index (mechanism_id, relation_id) -> botsingen eerst wegnemen
    conn.execute(
        """DELETE FROM instantiations
           WHERE mechanism_id=? AND relation_id IN
                 (SELECT relation_id FROM instantiations WHERE mechanism_id=?)""",
        (lid, sid),
    )
    conn.execute("UPDATE instantiations SET mechanism_id=? WHERE mechanism_id=?", (sid, lid))
    # de loser zelf
    conn.execute("DELETE FROM mechanisms WHERE id=?", (lid,))
    print(f"  '{loser_name}' (id {lid}) -> '{survivor_name}' (id {sid}); "
          f"omgehangen: {n_rel} rel, {n_ins} inst, {n_arg} arg.")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"FOUT: database niet gevonden op {DB_PATH}")

    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    n_before = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]

    print("\n-- A+B: mechanismen samenvoegen --")
    for loser, survivor in MERGES:
        merge_mechanism(conn, loser, survivor)

    print("\n-- A+B: survivors aanscherpen (+ B6/B9) --")
    for e in ENRICH:
        sets, vals = [], []
        for field in ("mechanism_type", "description", "effect"):
            if field in e:
                sets.append(f"{field}=?"); vals.append(e[field])
        vals.append(e["name"])
        cur = conn.execute(f"UPDATE mechanisms SET {', '.join(sets)} WHERE name=?", vals)
        print(f"  {'aangescherpt' if cur.rowcount else 'NIET gevonden'}: {e['name']}")

    conn.commit()

    # verificatie
    print("\n== verificatie ==")
    losers = [m[0] for m in MERGES]
    still = conn.execute(
        f"SELECT name FROM mechanisms WHERE name IN ({','.join('?' * len(losers))})", losers
    ).fetchall()
    print(f"  losers nog aanwezig (verwacht 0): {[r[0] for r in still]}")

    orphan = conn.execute(
        "SELECT COUNT(*) FROM relations WHERE mechanism_id IS NOT NULL "
        "AND mechanism_id NOT IN (SELECT id FROM mechanisms)"
    ).fetchone()[0]
    print(f"  verweesde relations.mechanism_id (verwacht 0): {orphan}")
    orphan_i = conn.execute(
        "SELECT COUNT(*) FROM instantiations WHERE mechanism_id IS NOT NULL "
        "AND mechanism_id NOT IN (SELECT id FROM mechanisms)"
    ).fetchone()[0]
    print(f"  verweesde instantiations.mechanism_id (verwacht 0): {orphan_i}")

    n_after = conn.execute("SELECT COUNT(*) FROM mechanisms").fetchone()[0]
    conn.close()
    print(f"\nKlaar. Mechanismen: {n_before} -> {n_after} (−{n_before - n_after}).")


if __name__ == "__main__":
    main()
