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
    return uit
