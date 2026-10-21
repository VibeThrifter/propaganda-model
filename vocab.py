"""De woordenschat van het model voor de Python-kant: filterlabels, leesbare namen,
relatielabels. Stdlib-only.

Eén Python-bron, gelezen door paginas.py (de server-gerenderde pagina's) en server.py
(de filter-enum). De browser leest dezelfde woorden uit web/shared_vocab.js (en
RELATION_LABELS uit web/template.html zolang die daar nog staat). Die JS-bestanden blijven
zoals ze zijn; `verschillen()` vergelijkt ze met dit bestand en
validation.check_woordenschat meldt elk verschil, zodat de kopieën niet uiteenlopen.

Sleutels blijven snake_case (DB, API, scores); dit is alleen de weergave.
"""
import re
from pathlib import Path

WEB = Path(__file__).parent / "web"

# De vijf filters (1 Eigendom … 5 Ideologie), de rest-categorieën en de vijf
# besluitvormingscategorieën (Uitbreiding C, 2026-10-07: zelfde netwerk, eigen chipgroep).
FILTER_LABELS = {
    "eigendom": "1. Eigendom",
    "advertentie": "2. Advertentie",
    "sourcing": "3. Sourcing",
    "flak": "4. Flak",
    "ideologie": "5. Ideologie",
    "systeemactor": "Systeemactor",
    "tegenmacht": "Tegenmacht",
    "cross_filter": "Cross-filter",
    "overig": "Overig",
    "formele_macht": "Formele macht",
    "belangen": "Belangen",
    "kennis_advies": "Kennis & advies",
    "polder": "Polder",
    "werving": "Werving",
}
FILTERS = frozenset(FILTER_LABELS)

# Leesbare namen (W2.3): alleen waar "underscores → spaties + hoofdletter" spelling of
# betekenis breekt (trema's, koppeltekens, afkortingen, richting).
NAAM_WEERGAVE = {
    # Rollen
    "mediaeigenaar": "Media-eigenaar",
    "raad_van_commissarissen": "Raad van commissarissen (RvC)",
    "columnist_opiniemaker": "Columnist / opiniemaker",
    "elite_forum": "Elite-forum",
    "vakbond_media": "Vakbond (media)",
    "eu_instelling": "EU-instelling",
    # Uitbreiding C — mechanismen met trema's/koppeltekens
    "ministeriele_verantwoordelijkheid": "Ministeriële verantwoordelijkheid",
    "hierarchische_aansturing": "Hiërarchische aansturing",
    "akkoord_preemptie": "Akkoord-preëmptie",
    # Mechanismen — spelling (trema's, koppeltekens, afkortingen)
    "commerciele_afhankelijkheid": "Commerciële afhankelijkheid",
    "continuiteitsborging": "Continuïteitsborging",
    "gecoordineerde_voorlichting": "Gecoördineerde voorlichting",
    "inlichtingen_cooptatie": "Inlichtingen-coöptatie",
    "pr_inhuur": "PR-inhuur",
    "pr_subsidie": "PR-subsidie",
    "woo_obstructie": "Woo-obstructie",
    "stak_stemzeggenschap": "STAK-stemzeggenschap",
    "cross_media_eigendom": "Cross-media-eigendom",
    "media_agendering": "Media-agendering",
    "intermedia_agendering": "Intermedia-agendering",
    "journalist_bronrelatie": "Journalist-bronrelatie",
    # Mechanismen — elite-netwerkfamilie
    "belang_elite_netwerk": "Belanghebbende in elite-netwerk",
    "mediaeigenaar_elite_netwerk": "Media-eigenaar in elite-netwerk",
    "politicus_elite_netwerk": "Politicus in elite-netwerk",
    "elite_media_netwerk": "Elite-medianetwerk",
    "elite_kennisnetwerk": "Elite-kennisnetwerk",
    # Mechanismen — richting (draaideur is wederzijds, levering is gericht)
    "draaideur_journalistiek_politiek": "Draaideur journalistiek ↔ politiek",
    "draaideur_journalistiek_voorlichting": "Draaideur journalistiek ↔ voorlichting",
    "draaideur_politiek_bedrijfsleven": "Draaideur politiek ↔ bedrijfsleven",
    "draaideur_politiek_institutie": "Draaideur politiek ↔ institutie",
    "draaideur_politiek_lobby": "Draaideur politiek ↔ lobby",
    "draaideur_politiek_media": "Draaideur politiek ↔ media",
    "denktank_naar_persbureau": "Denktank → persbureau",
    "denktank_naar_politiek": "Denktank → politiek",
    "lobbyist_naar_journalist": "Lobbyist → journalist",
    "lobbyist_naar_politicus": "Lobbyist → politicus",
    # Mechanismen — variant tussen haakjes leest beter dan een woordreeks
    "academische_socialisatie_hoofdredacteur": "Academische socialisatie (hoofdredacteur)",
    "academische_socialisatie_politiek": "Academische socialisatie (politiek)",
    "academische_orthodoxie_denktank": "Academische orthodoxie (denktank)",
    "academische_orthodoxie_instituut": "Academische orthodoxie (instituut)",
    # Entiteitstypen
    "pr_bureau": "PR-bureau",
    "ngo": "NGO",
    "elite_netwerk": "Elite-netwerk",
}

# Relatietypes (relations.relation_type), zoals de viz ze toont.
RELATIE_LABELS = {
    # Eigendom & financiën
    "eigendom": "Eigendom",
    "financiering": "Financiering",
    "adverteerder": "Adverteerder",
    "donor": "Donor",
    "investering": "Investering",
    # Organisatorisch
    "lidmaatschap": "Lidmaatschap",
    "personeel": "Personeel",
    "dienstverband": "Dienstverband",
    "bestuurder": "Bestuurder",
    "adviseur": "Adviseur",
    "woordvoerder_van": "Woordvoerder",
    "draaideur": "Draaideur",
    # Bestuur (Uitbreiding C, 2026-10-07)
    "ambt": "Ambt",
    "zeggenschap": "Zeggenschap",
    "controle": "Controle",
    "geschenk": "Geschenk",
    # Informatiestromen
    "bron_van": "Bron van",
    "mediaplatform": "Mediaplatform",
    "framing": "Framing",
    "citeert": "Citeert",
    # Macht & druk
    "lobbyt": "Lobbyt",
    "censuur": "Censuur",
    "flak": "Flak",
    "intimidatie": "Intimidatie",
    "regulering": "Regulering",
    "zelfcensuur": "Zelfcensuur",
    # Politiek & ideologisch
    "alliantie": "Alliantie",
    "oppositie": "Oppositie",
    "beinvloeding": "Beïnvloeding",
    "cooptatie": "Coöptatie",
    "etikettering": "Etikettering",
    # Algoritmisch
    "algoritmische_filtering": "Algoritmische filtering",
}


# Richting (eigenaarsbesluit 2026-10-15: "alleen directioneel als a ook echt invloed heeft op b en
# niet echt andersom, zoals a financiert b of a is eigenaar van b"). Een band waarbij iemand bij
# een organisatie hoort — werkt voor, is lid van, zit in het bestuur, adviseert, spreekt namens,
# bekleedt er een ambt, stapte over — heeft geen invloedsrichting: de persoon kan de organisatie
# beïnvloeden én de organisatie de persoon (en via hem verder). Zo'n band is richtingloos: de viz
# tekent hem zonder enkele pijl, de invloedsgraaf (influence.py) telt hem in beide richtingen. De
# opgeslagen volgorde van bron en doel zegt bij deze typen niets. Een gericht type kan per verband
# toch richtingloos zijn (relations.bidirectional = 1, gezet door de richtingtoets).
# Spiegel in web/shared_vocab.js (RICHTINGLOZE_TYPES); verschillen() bewaakt dat.
RICHTINGLOZE_TYPES = frozenset({
    "lidmaatschap", "personeel", "dienstverband", "bestuurder", "adviseur", "woordvoerder_van",
    "draaideur", "ambt", "alliantie",
})

# Wat bron → doel betekent bij elk gericht type: de bron oefent de invloed uit. De richtingtoets
# (scripts/richtingtoets.py) en de missiebriefs gebruiken deze zinnen.
RICHTING_PER_TYPE = {
    "eigendom": "bron is eigenaar of aandeelhouder van doel",
    "financiering": "bron betaalt, subsidieert of sponsort doel",
    "adverteerder": "bron adverteert bij doel (betaalt het medium)",
    "donor": "bron doneert aan doel",
    "investering": "bron investeert in doel",
    "zeggenschap": "bron heeft zeggenschap over doel (hogere organisatie → lagere)",
    "controle": "bron controleert doel (rekenkamer, rechter, volksvertegenwoordiging → bestuur)",
    "geschenk": "bron geeft het geschenk of de reis, doel ontvangt het",
    "bron_van": "bron levert informatie of expertise aan doel (het medium of de journalist)",
    "mediaplatform": "bron biedt het platform of het programma waarop doel publiceert of verschijnt",
    "framing": "bron bepaalt het frame dat doel overneemt",
    "citeert": "bron citeert doel",
    "lobbyt": "bron lobbyt bij doel",
    "censuur": "bron onderdrukt informatie van of bij doel",
    "flak": "bron valt doel aan of disciplineert doel",
    "intimidatie": "bron bedreigt of dreigt juridisch tegen doel",
    "regulering": "bron houdt toezicht op of reguleert doel",
    "zelfcensuur": "bron (de druk) brengt doel tot zelfcensuur",
    "oppositie": "bron treedt op tegen doel",
    "beinvloeding": "bron beïnvloedt doel (expert in een programma, instituut dat een medium voedt)",
    "cooptatie": "bron lijft doel of zijn kritiek in",
    "etikettering": "bron plakt doel een etiket op",
    "algoritmische_filtering": "bron (het platform) bepaalt wat van doel zichtbaar is",
}


def richtingloos(relatietype, bidirectional=False):
    """True als een verband geen invloedsrichting heeft (het type, of het verband zelf)."""
    return relatietype in RICHTINGLOZE_TYPES or bool(bidirectional)


def weergave_naam(naam):
    """snake_case → leesbare naam (spiegel van weergaveNaam() in shared_vocab.js)."""
    if naam is None or naam == "":
        return ""
    s = str(naam)
    if s in NAAM_WEERGAVE:
        return NAAM_WEERGAVE[s]
    vlak = s.replace("_", " ").strip()
    return vlak[:1].upper() + vlak[1:] if vlak else ""


def filter_label(cat):
    return FILTER_LABELS.get(cat, weergave_naam(cat))


def relatie_label(relatietype):
    return RELATIE_LABELS.get(relatietype, weergave_naam(relatietype))


# ── Vergelijking met de JS-kopieën ───────────────────────────────────────────

# (bestanden in web/ waar de JS-constante kan staan — de eerste die haar heeft telt,
#  JS-constante, Python-dict)
JS_KOPIEEN = (
    (("shared_vocab.js",), "FILTER_LABELS", FILTER_LABELS),
    (("shared_vocab.js",), "NAAM_WEERGAVE", NAAM_WEERGAVE),
    (("shared_vocab.js", "template.html"), "RELATION_LABELS", RELATIE_LABELS),
)


def js_object(tekst, naam):
    """{sleutel: 'waarde'} uit `const NAAM = { … };` (commentaar genegeerd), of None."""
    m = re.search(r"const\s+%s\s*=\s*\{(.*?)\n\};" % re.escape(naam), tekst, re.S)
    if m is None:
        return None
    return dict(re.findall(r"(\w+)\s*:\s*'([^']*)'", re.sub(r"//[^\n]*", "", m.group(1))))


def verschillen(web=WEB):
    """Lijst van leesbare verschillen tussen dit bestand en de JS-kopieën; leeg = gelijk."""
    uit = []
    for bestanden, naam, py in JS_KOPIEEN:
        js, bestand = None, " of ".join(bestanden)
        for kandidaat in bestanden:
            try:
                js = js_object((Path(web) / kandidaat).read_text(encoding="utf-8"), naam)
            except OSError:
                js = None
            if js is not None:
                bestand = kandidaat
                break
        if js is None:
            uit.append(f"{bestand}: {naam} niet gevonden")
            continue
        for k in sorted(set(js) | set(py)):
            if js.get(k) != py.get(k):
                uit.append(f"{bestand} {naam}.{k}: JS {js.get(k)!r} ≠ vocab.py {py.get(k)!r}")
    try:
        tekst = (Path(web) / "shared_vocab.js").read_text(encoding="utf-8")
    except OSError:
        tekst = ""
    m = re.search(r"const\s+RICHTINGLOZE_TYPES\s*=\s*new Set\(\[(.*?)\]\)", tekst, re.S)
    js_set = set(re.findall(r"'(\w+)'", m.group(1))) if m else None
    if js_set is None:
        uit.append("shared_vocab.js: RICHTINGLOZE_TYPES niet gevonden")
    elif js_set != set(RICHTINGLOZE_TYPES):
        uit.append(f"shared_vocab.js RICHTINGLOZE_TYPES: JS {sorted(js_set)} ≠ vocab.py "
                   f"{sorted(RICHTINGLOZE_TYPES)}")
    return uit


# Publieke tip (2026-10-14, web/tip.html → leads.soort_verband): het soort verband dat de inzender
# kiest. Bewust grof: de nieuws-scout kiest zelf relatietype en mechanisme uit de precedenten; dit
# label is alleen een hint (scripts/lead_triage.py zet het in de context van het doel).
LEAD_SOORTEN_VERBAND = {
    "functie": "werkt of werkte bij, heeft of had een functie bij",
    "bestuur": "zit of zat in het bestuur of de raad van toezicht van",
    "eigendom": "is (mede-)eigenaar van",
    "financiering": "financiert, sponsort of adverteert bij",
    "lidmaatschap": "is of was lid van",
    "advies": "adviseert of levert experts of onderzoek aan",
    "druk": "oefent druk uit op, klaagt aan of dreigt met juridische stappen tegen",
    "anders": "een ander verband (zie de toelichting)",
}
