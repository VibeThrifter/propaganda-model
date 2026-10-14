#!/usr/bin/env python3
"""Partijnetwerk — wie is aan welke partij verbonden, en welke posities bekleden die mensen.

Beschrijvende overlay over het praktijkmodel (hetzelfde netwerk; geen eigen tabel, niets
opgeslagen). Per partij: de personen met een partijband (lid, bestuurder, adviseur,
medewerker, woordvoerder, draaideur) en hun posities — een ambt in het openbaar bestuur
(Kabinet, Kamers, Europees Parlement, provincie, gemeente), een benoemde functie in de staat
(ambtelijke top, adviesraden, planbureaus, kennisinstituten, toezicht, inspecties, uitvoering,
rechtspraak, veiligheid) of een functie bij de media of daarbuiten (bedrijf, bank, adviesbureau,
lobby, vakbond, denktank, ngo, onderwijs, elite-netwerk). Plus de benoemde topfuncties zelf:
wie ze bekleedt en of die persoon aan een partij verbonden is (sleutelposities).
Daarnaast: welke organisaties mensen uit meerdere partijen delen.

Tijd (looptijd.py, 2026-10-13): een band loopt nooit buiten het bestaan van partij of
organisatie, dus een ongedateerd PvdA-lidmaatschap eindigt op 1 juli 2026. 'Lopend' wordt
op de dag bepaald, niet op het jaar.

Fusies: een partij die opging in een andere (aspect 'opgegaan_in') blijft haar eigen banden
houden. Met fusies=True (standaard) telt de opvolger ze mee als zijn stamboom: PRO toont ook
de mensen van PvdA en GroenLinks, elk met de partij en de periode van hun band. 'Nu' telt
alleen wat vandaag loopt. Een band met een opgeheven partij loopt niet meer, en een lid gaat
alleen over als een bron dat voor die persoon zegt.

Mandaat (2026-10-13, "gekozen met ongekozen kunnen scheiden"): elke positie draagt ook hoe
ze vervuld wordt — rechtstreeks door kiezers gekozen, afgeleid van een gekozen orgaan (dat
kiest of benoemt, of wiens vertrouwen nodig is), benoemd, of buiten het openbaar bestuur.
Een feit over de positie volgens de wet, geen oordeel over wie er invloed heeft. Waar de
klasse het niet vastlegt (provincie, gemeente, waterschap) beslist de ambtstitel; zegt die
niets, dan 'onbepaald' — nooit gokken.

Leest alléén goedgekeurde, niet-vervangen relaties tussen goedgekeurde entiteiten. Telt in
NIETS mee (scoring/influence/viz_data lezen dit niet) en beweert niets over invloed of
afstemming: het zegt wie welke positie bekleedt volgens de gesourcete verbanden. Dat is de
beschrijvende kant van de kartelpartij-these (Katz & Mair 1995) — of het patroon die these
draagt, blijft een vraag voor de discussieboom, niet voor deze telling.

Gebruikt door GET /api/partijen (overzicht), GET /api/partijen/<id> (één partij), de
pagina /partijen en de partij-sectie in het viz-detailpaneel.
"""
from __future__ import annotations

import datetime
import json
import re

import looptijd

# Band persoon ↔ partij (beide richtingen; het register schrijft partij → persoon).
PARTIJBAND_TYPES = ("lidmaatschap", "bestuurder", "adviseur", "personeel",
                    "dienstverband", "woordvoerder_van", "draaideur")
# Een positie: dezelfde affiliatietypen plus 'ambt', tussen een partijpersoon en een
# organisatie die zelf geen partij is.
POSITIE_TYPES = PARTIJBAND_TYPES + ("ambt",)

BAND_LABELS = {
    "lidmaatschap": "lid", "bestuurder": "bestuurder", "adviseur": "adviseur",
    "personeel": "medewerker", "dienstverband": "in dienst",
    "woordvoerder_van": "woordvoerder", "draaideur": "draaideur",
}
# Positie zonder `functie`: het relatietype als kort label, of — voor de klassen waar
# de titel vastligt — de gangbare titel.
POSITIE_LABELS = dict(BAND_LABELS, lidmaatschap="lid", personeel="werkzaam bij", ambt="ambt")
KLASSE_TITELS = {"kabinet": "bewindspersoon", "tweede_kamer": "Kamerlid",
                 "eerste_kamer": "Kamerlid", "europarlement": "Europarlementariër"}

# (sleutel, label, groep) — de volgorde is ook de rangorde voor de 'hoofdpositie' van
# een persoon (de eerste klasse waarin hij een positie heeft). Domeinen in drie blokken
# (eigenaar 2026-10-14: "de tweede kamer apart kunnen zien van ongekozen … we willen juist
# dingen zichtbaar maken die niet zo transparant zijn, zoals ongekozen macht en netwerken,
# rechterlijke macht, topambtenaren … 'per domein' gedetailleerder en daar al de scheiding van
# gekozen en ongekozen"): de ongekozen staat (gedetailleerd), netwerken buiten de overheid, en
# het gekozen deel (volksvertegenwoordiging en politiek bestuur).
KLASSEN = [
    # Ongekozen: de benoemde staat
    ("burgemeester", "Burgemeesters", "kroon"),
    ("cdk_dijkgraaf", "Commissarissen van de Koning & dijkgraven", "kroon"),
    ("ambtelijke_top", "Ambtelijke top (SG, DG)", "ambtenarij"),
    ("ministerie", "Ministeries (overige functies)", "ambtenarij"),
    ("rechtspraak", "Rechtspraak & Openbaar Ministerie", "rechtsstaat"),
    ("hoge_colleges", "Raad van State, Rekenkamer & ombudsman", "rechtsstaat"),
    ("toezicht", "Toezichthouders", "toezicht"),
    ("inspectie", "Inspecties", "toezicht"),
    ("advies", "Adviesraden & SER", "kennis"),
    ("planbureau", "Planbureaus", "kennis"),
    ("kennis", "Kennisinstituten", "kennis"),
    ("uitvoering", "Uitvoeringsorganisaties & zbo's", "uitvoering"),
    ("decentraal_overig", "Gemeente, provincie, waterschap (overig)", "uitvoering"),
    ("overheid", "Overige overheid", "uitvoering"),
    ("veiligheid", "Veiligheid, inlichtingen & defensie", "veiligheid"),
    ("internationaal", "EU & internationale organisaties", "internationaal"),
    # Netwerken buiten de overheid
    ("publieke_omroep", "Publieke omroep", "media"),
    ("pers_media", "Pers, programma's & commerciële media", "media"),
    ("platform", "Techplatforms", "media"),
    ("mediabestel", "Mediatoezicht, -fondsen & -verenigingen", "media"),
    ("bedrijfsleven", "Bedrijfsleven", "markt"),
    ("financieel", "Banken, pensioen & beleggen", "markt"),
    ("consultancy", "Consultancy, accountancy & advocatuur", "markt"),
    ("belangen", "Werkgevers, lobby & pr", "belangen"),
    ("vakbond", "Vakbonden", "belangen"),
    ("denktank", "Denktanks", "samenleving"),
    ("maatschappelijk", "Ngo's & stichtingen", "samenleving"),
    ("onderwijs", "Universiteiten, umc's & onderwijs", "samenleving"),
    ("elite_netwerk", "Elite-netwerken & clubs", "samenleving"),
    # Gekozen: volksvertegenwoordiging en politiek bestuur
    ("tweede_kamer", "Tweede Kamer", "volk"),
    ("eerste_kamer", "Eerste Kamer", "volk"),
    ("kamercommissie", "Kamercommissies", "volk"),
    ("europarlement", "Europees Parlement", "volk"),
    ("staten", "Provinciale Staten", "volk"),
    ("gemeenteraad", "Gemeenteraad", "volk"),
    ("waterschap_ab", "Waterschap (algemeen bestuur)", "volk"),
    ("assemblee", "Parlementaire assemblees", "volk"),
    ("kabinet", "Kabinet", "bestuur"),
    ("gedeputeerde", "Gedeputeerden & heemraden", "bestuur"),
    ("wethouder", "Wethouders", "bestuur"),
    ("politieke_staf", "Politieke medewerkers", "bestuur"),
]
# Domeinen (groepen) met hun blok, in weergavevolgorde.
GROEPEN_LIJST = [
    ("kroon", "Kroonbenoemde bestuurders", "staat"),
    ("ambtenarij", "Ambtelijke top & ministeries", "staat"),
    ("rechtsstaat", "Rechterlijke macht & hoge colleges", "staat"),
    ("toezicht", "Toezicht & inspecties", "staat"),
    ("kennis", "Advies, planbureaus & kennis", "staat"),
    ("uitvoering", "Uitvoering & overige overheid", "staat"),
    ("veiligheid", "Veiligheid & defensie", "staat"),
    ("internationaal", "EU & internationaal", "staat"),
    ("media", "Media", "buiten"),
    ("markt", "Bedrijfsleven & financiële sector", "buiten"),
    ("belangen", "Lobby, werkgevers & vakbonden", "buiten"),
    ("samenleving", "Maatschappij & wetenschap", "buiten"),
    ("volk", "Volksvertegenwoordiging", "gekozen"),
    ("bestuur", "Politiek bestuur", "gekozen"),
]
GROEPEN = {k: lab for k, lab, _ in GROEPEN_LIJST}
GROEP_BLOK = {k: b for k, _, b in GROEPEN_LIJST}
DOMEINBLOKKEN = [
    ("staat", "Ongekozen: de benoemde staat",
     "Benoemde functies in het openbaar bestuur: wie er zit, volgt niet uit verkiezingen."),
    ("buiten", "Netwerken buiten de overheid",
     "Media, bedrijfsleven, lobby, ngo's, denktanks, onderwijs en elite-netwerken."),
    ("gekozen", "Gekozen: volksvertegenwoordiging & politiek bestuur",
     "Zetels uit verkiezingen en het bestuur dat daaruit voortkomt; dit deel is al openbaar."),
]
# Concrete combinaties (in plaats van 'meer dan één domein'): wie zowel … als … heeft.
KRUISINGEN = [
    ("gekozen_staat", "Gekozen én ongekozen staat", ("gekozen", "staat"),
     "Personen met een gekozen of politieke functie én een benoemde functie in de staat (nu of eerder, binnen de partijband)."),
    ("gekozen_buiten", "Gekozen én netwerken", ("gekozen", "buiten"),
     "Personen met een gekozen of politieke functie én een positie bij media, bedrijfsleven, lobby of maatschappij."),
    ("staat_buiten", "Ongekozen staat én netwerken", ("staat", "buiten"),
     "Personen met een benoemde functie in de staat én een positie bij media, bedrijfsleven, lobby of maatschappij."),
]
RANG = {k: i for i, (k, _, _) in enumerate(KLASSEN)}
RANG_GROEP = {k: g for k, _, g in KLASSEN}
# Klassen met veel namen die de pagina compact toont (aantal + namenrooster, geen kaartjes).
BULK_KLASSEN = ("burgemeester", "wethouder")
# Wat er in een klasse valt (feitelijk, ter uitleg op de pagina).
KLASSE_UITLEG = {
    "burgemeester": "Burgemeesters worden bij koninklijk besluit benoemd (een waarnemend burgemeester door de commissaris van de Koning).",
    "cdk_dijkgraaf": "Commissarissen van de Koning en dijkgraven: bij koninklijk besluit benoemd.",
    "ambtelijke_top": "Secretarissen-generaal en directeuren-generaal: de ambtelijke leiding van de ministeries.",
    "ministerie": "Overige functies bij een ministerie of directoraat-generaal.",
    "rechtspraak": "Hoge Raad, gerechtshoven, rechtbanken, bestuursrechters en het Openbaar Ministerie.",
    "hoge_colleges": "De Hoge Colleges van Staat naast het parlement: Raad van State, Algemene Rekenkamer en Nationale ombudsman.",
    "toezicht": "ACM, AFM, DNB, NZa, Autoriteit Persoonsgegevens, Kansspelautoriteit, Onderzoeksraad voor Veiligheid en andere toezichthouders.",
    "inspectie": "Rijksinspecties onder een inspecteur-generaal: IGJ, Arbeidsinspectie, NVWA, ILT, Inspectie van het Onderwijs …",
    "advies": "Adviescolleges van regering en parlement (WRR, Gezondheidsraad, Onderwijsraad, Raad voor Cultuur, Kiesraad …), de SER en adviesteams zoals het OMT.",
    "planbureau": "Centraal Planbureau, Sociaal en Cultureel Planbureau en Planbureau voor de Leefomgeving.",
    "kennis": "RIVM, CBS, KNMI, CBG, Lareb, TNO, NWO, KNAW, NFI, WODC en vergelijkbare kennisinstituten.",
    "uitvoering": "Agentschappen en zelfstandige bestuursorganen die beleid uitvoeren: Belastingdienst, UWV, SVB, DUO, IND, COA, RVO, Rijkswaterstaat, fondsen …",
    "decentraal_overig": "Ambtelijke en overige functies bij een gemeente, provincie of waterschap, of een functie die het model niet vastlegt.",
    "veiligheid": "AIVD, MIVD, NCTV, politie, Marechaussee en de militaire top.",
    "internationaal": "Europese Commissie, ECB, EIB, EMA, NAVO, VN-organisaties en buitenlandse overheden.",
    "publieke_omroep": "NPO, NOS, de omroepverenigingen en de regionale en lokale publieke omroepen.",
    "pers_media": "Kranten, bladen, persbureaus, online media, programma's, commerciële omroepen en mediaconcerns.",
    "mediabestel": "Commissariaat voor de Media, Raad voor de Journalistiek, journalistieke fondsen, Nieuwspoort, het Genootschap van Hoofdredacteuren …",
    "consultancy": "Adviesbureaus, accountantskantoren en advocatenkantoren.",
    "kamercommissie": "Vaste en tijdelijke commissies en enquêtecommissies van de Tweede en Eerste Kamer; de leden zijn Kamerleden.",
    "assemblee": "Delegaties uit het parlement naar internationale parlementaire assemblees (NAVO, OVSE, Raad van Europa …).",
    "gedeputeerde": "Gedeputeerden (benoemd door Provinciale Staten) en heemraden (door het algemeen bestuur van een waterschap).",
    "politieke_staf": "Fractie- en delegatiemedewerkers en politiek assistenten van bewindspersonen.",
}

OVERHEID_TYPES = ("overheidsinstelling", "toezichthouder", "rechterlijke_macht")
PARLEMENTEN = ("Tweede Kamer", "Eerste Kamer", "Europees Parlement")
# Commissies van de Kamers ('Vaste commissie voor Financiën (Tweede Kamer)', enquêtecommissies).
KAMERCOMMISSIE = re.compile(r"\((tweede|eerste) kamer\)|^(vaste|tijdelijke|algemene) commissie|"
                            r"enquêtecommissie|^commissie voor de (rijksuitgaven|verzoekschriften|inlichtingen)",
                            re.IGNORECASE)


def _re(*woorden):
    return re.compile("|".join(woorden), re.IGNORECASE)


# Naam → klasse, voor elk organisatietype; de eerste treffer wint. Zo valt het CvdM bij de
# media, een universiteit met overheidstype bij onderwijs en het Lareb (een stichting) bij
# de kennisinstituten.
NAAM_KLASSE = [
    ("onderwijs", _re(r"universiteit", r"university", r"hogeschool", r"\btu delft\b",
                      r"\bumc\b", r"erasmus mc", r"radboudumc", r"amsterdam umc")),
    ("mediabestel", _re(r"commissariaat voor de media", r"\bcvdm\b", r"raad voor de journalistiek",
                        r"stimuleringsfonds voor de journalistiek", r"\bsvdj\b", r"media ombudsman",
                        r"fonds bijzondere journalistieke", r"nationaal media onderzoek", r"nieuwspoort",
                        r"genootschap van hoofdredacteuren", r"\bnvj\b", r"vereniging van journalisten",
                        r"persvrijheidsfonds", r"radio-omroep controle", r"beeld en geluid", r"\bde tegel\b",
                        r"european press prize", r"weekbladpers", r"democratie en media", r"villamedia")),
    ("publieke_omroep", _re(r"\bnpo\b", r"\bnos\b", r"regionale publieke omroep", r"\brpo\b",
                            r"lokale publieke omroep", r"^ster$", r"eo-redactie")),
    ("pers_media", _re(r"volkskrant", r"parool", r"\bnu\.nl\b", r"\brtl\b", r"telegraaf",
                       r"christelijke pers", r"investico", r"bellingcat", r"investigative desk",
                       r"bureau spotlight", r"vers beton")),
    ("assemblee", _re(r"parlementaire assemblee", r"parliamentary assembly", r"interparlementair")),
    ("internationaal", _re(r"europese commissie", r"europese centrale bank", r"\becb\b",
                           r"europese investeringsbank", r"\beib\b", r"\bnavo\b", r"\bnato\b",
                           r"\bwho\b", r"wereldgezondheidsorganisatie", r"verenigde naties", r"\bvn-",
                           r"\bimf\b", r"\boeso\b", r"\boecd\b", r"raad van europa", r"medicines agency",
                           r"\bus department\b", r"home office",
                           r"foreign, commonwealth", r"^ministry of", r"\busaid\b", r"\bnsa\b",
                           r"generalitat", r"taipei", r"unesco", r"stratcom")),
]
# Naam → klasse binnen de overheid, ná de directoraten-generaal (zodat 'DG Politie en
# Veiligheidsregio's' ambtelijke top blijft en niet bij de politie belandt).
STAAT_NAAM_KLASSE = [
    ("planbureau", _re(r"centraal planbureau", r"^cpb\b", r"sociaal en cultureel planbureau", r"^scp\b",
                       r"planbureau voor de leefomgeving")),
    ("veiligheid", _re(r"\baivd\b", r"\bmivd\b", r"\bnctv\b", r"\bnctb\b",
                       r"coördinator terrorismebestrijding", r"\bpolitie\b", r"politieacademie",
                       r"marechaussee", r"defensiestaf", r"commandant der strijdkrachten", r"\bncsc\b",
                       r"cyber security centrum", r"veiligheidsberaad", r"land information manoeuvre")),
    ("rechtspraak", _re(r"openbaar ministerie", r"raad voor de rechtspraak", r"parket bij de hoge raad",
                        r"procureurs-generaal", r"hoge raad", r"gerechtshof", r"rechtbank",
                        r"centrale raad van beroep", r"college van beroep")),
    ("kennis", _re(r"\brivm\b", r"\bknmi\b", r"meteorologisch instituut", r"centraal bureau voor de statistiek",
                   r"^cbs\b", r"beoordeling van geneesmiddelen", r"\blareb\b", r"\btno\b", r"^nwo\b",
                   r"\bknaw\b", r"forensisch instituut", r"\bwodc\b", r"zorgonderzoek nederland", r"\bzonmw\b",
                   r"\bnivel\b", r"trimbos", r"deltares", r"jeugdinstituut", r"lucht- en ruimtevaartcentrum",
                   r"maritime research institute")),
    ("toezicht", _re(r"autoriteit consument", r"^acm\b", r"autoriteit financiële markten", r"^afm\b",
                     r"nederlandsche bank", r"zorgautoriteit", r"autoriteit persoonsgegevens",
                     r"kansspelautoriteit", r"onderzoeksraad voor veiligheid", r"huis voor klokkenluiders",
                     r"autoriteit online terroristisch", r"dopingautoriteit")),
    ("advies", _re(r"kiesraad", r"wetenschappelijke raad voor het regeringsbeleid", r"^wrr\b",
                   r"sociaal-economische raad", r"^ser\b", r"outbreak management team", r"^omt\b",
                   r"klimaatberaad", r"gezondheidsraad")),
    ("hoge_colleges", _re(r"raad van state", r"algemene rekenkamer", r"nationale ombudsman")),
    ("uitvoering", _re(r"belastingdienst", r"dienst toeslagen")),
]
KENNIS_NAAM = dict(STAAT_NAAM_KLASSE)["kennis"]
# Registersoort (organisaties.overheid.nl, `metadata.oo_type`) → klasse.
OO_KLASSE = {
    "Adviescollege": "advies", "Externe commissie": "advies",
    "Openbaar lichaam voor beroep en bedrijf": "advies", "Inspectie": "inspectie",
    "Rechtspraak": "rechtspraak", "Hoog College van Staat": "hoge_colleges", "Politie": "veiligheid",
    "Agentschap": "uitvoering", "Zelfstandig bestuursorgaan": "uitvoering",
}
AMBTELIJKE_TOP = _re(r"secretaris-generaal", r"directeur-generaal", r"thesaurier-generaal")
POLITIEKE_STAF = _re(r"politiek assistent", r"fractiemedewerker", r"fractieassistent",
                     r"\bdelegatie\b", r"beleidsmedewerker (cda|vvd|pvv|d66|sp|pvda|groenlinks|gl|cu|sgp)\b",
                     r"parlementair (beleids)?medewerker")
# Buiten de overheid: naam → klasse alleen voor bedrijven (banken, adviesbureaus, mediaconcerns).
BEDRIJF_NAAM_KLASSE = [
    ("pers_media", _re(r"media", r"persgroep", r"\btmg\b", r"sanoma", r"wegener", r"talpa", r"hearst",
                       r"pcm uitgevers", r"\bvnu\b", r"roularta", r"mecom", r"netflix", r"videoland",
                       r"uitgeverij", r"groupm")),
    ("financieel", _re(r"\bbank\b", r"abn amro", r"^ing\b", r"rabobank", r"triodos", r"van lanschot",
                       r"\bbunq\b", r"^apg\b", r"pensioen", r"\bnn group\b", r"aegon", r"achmea", r"blackrock",
                       r"vanguard", r"northern trust", r"degroof", r"\bkbc\b", r"adyen", r"mollie",
                       r"capital", r"investments?\b", r"vermogensbeheer")),
    ("consultancy", _re(r"mckinsey", r"boston consulting", r"deloitte", r"ernst & young", r"\bkpmg\b",
                        r"\bpwc\b", r"berenschot", r"allen & overy", r"de brauw", r"accenture", r"\bbain\b",
                        r"capgemini", r"twynstra", r"houthoff", r"nautadutilh", r"stibbe", r"loyens",
                        r"clare locke", r"root legal", r"\btax\b", r"belastingadvis", r"interim")),
]
SECTOR_KLASSE = {
    "bedrijf": "bedrijfsleven", "vermogensbeheerder": "financieel",
    "mediaorganisatie": "pers_media", "persbureau": "pers_media", "platform": "platform",
    "lobbygroep": "belangen", "pr_bureau": "belangen", "vakbond": "vakbond",
    "denktank": "denktank",
    "ngo": "maatschappelijk", "stichting": "maatschappelijk", "burgerinitiatief": "maatschappelijk",
    "onderwijsinstelling": "onderwijs",
    "elite_netwerk": "elite_netwerk",
}
COMMERCIELE_OMROEP = _re(r"\brtl\b", r"\bsbs", r"talpa")


# (sleutel, label, kort, blok, uitleg) — volgorde = weergave en rang voor de hoofdgroep.
MANDATEN = [
    ("kiezers", "Rechtstreeks gekozen", "gekozen", "gekozen",
     "Gekozen door kiezers: Tweede Kamer, Europees Parlement, Provinciale Staten, gemeenteraad "
     "en het algemeen bestuur van een waterschap."),
    ("afgeleid", "Afgeleid van een gekozen orgaan", "afgeleid", "gekozen",
     "Niet door kiezers gekozen, maar door een gekozen orgaan gekozen of benoemd, of afhankelijk "
     "van zijn vertrouwen: de Eerste Kamer (gekozen door de Statenleden en de kiescolleges), het "
     "kabinet (benoemd bij koninklijk besluit, afhankelijk van het vertrouwen van het parlement), "
     "wethouders (benoemd door de raad), gedeputeerden (door de Staten), heemraden (door het "
     "algemeen bestuur) en delegaties uit het parlement naar internationale assemblees."),
    ("benoemd", "Benoemd", "benoemd", "ongekozen",
     "Benoemd, niet gekozen: burgemeesters, commissarissen van de Koning en dijkgraven (bij "
     "koninklijk besluit; een waarnemend burgemeester door de commissaris van de Koning), "
     "topambtenaren, rechters, toezichthouders, adviescolleges en wie bij de overheid in dienst "
     "of adviseur is."),
    ("buiten", "Buiten het openbaar bestuur", "", "ongekozen",
     "Een functie bij een bedrijf, medium, lobby- of belangenorganisatie, denktank, ngo, "
     "onderwijsinstelling of elite-netwerk."),
    ("onbepaald", "Bestuursfunctie niet vastgelegd", "?", None,
     "Een positie bij een provincie, gemeente of waterschap waarvan het model de functie niet "
     "vastlegt, zoals 'bestuurder' zonder titel (burgemeester of wethouder?). Telt in geen van "
     "beide blokken."),
]
MANDAAT_BLOK = {k: b for k, _, _, b, _ in MANDATEN}
BLOKKEN = [("gekozen", "Gekozen, rechtstreeks of afgeleid"), ("ongekozen", "Niet gekozen")]
MANDAAT_RANG = {k: i for i, (k, *_rest) in enumerate(MANDATEN)}
# Klassen met één vast mandaat; provincie, gemeente en waterschap hangen af van de functie.
KLASSE_MANDAAT = {
    "tweede_kamer": "kiezers", "europarlement": "kiezers", "staten": "kiezers",
    "gemeenteraad": "kiezers", "waterschap_ab": "kiezers",
    "eerste_kamer": "afgeleid", "kabinet": "afgeleid", "wethouder": "afgeleid",
    "gedeputeerde": "afgeleid", "assemblee": "afgeleid", "kamercommissie": "afgeleid",
    "burgemeester": "benoemd", "cdk_dijkgraaf": "benoemd", "politieke_staf": "benoemd",
}
# Ambtstitel → mandaat; de eerste treffer wint, dus 'duo-raadslid' (afgeleid) vóór 'raadslid'.
FUNCTIE_MANDAAT = [
    ("benoemd", ("commissaris van de koning", "gouverneur", "dijkgraaf", "watergraaf", "geborgd",
                 "griffier", "gemeentesecretaris", "provinciesecretaris", "secretaris-directeur",
                 "ambtenaar")),
    ("afgeleid", ("gedeputeerde", "heemraad", "dagelijks bestuur", "wethouder", "burgerlid",
                  "commissielid", "steunfractie", "fractieassistent", "duo-raadslid", "duoraadslid")),
    ("kiezers", ("statenlid", "provinciale staten", "raadslid", "gemeenteraad", "algemeen bestuur",
                 "lid van de raad", "lid van de staten")),
]
# Rijlabels voor een gemengde klasse binnen één mandaat (anders het klasselabel).
MANDAAT_RIJ_LABELS = {
    "afgeleid|decentraal_overig": "Gemeente (burger- of commissielid)",
    "benoemd|decentraal_overig": "Gemeente, provincie, waterschap (ambtelijk)",
    "onbepaald|decentraal_overig": "Gemeente, provincie, waterschap (functie onbekend)",
}
LOKAAL_GEKOZEN = {"provincie": "staten", "gemeente": "gemeenteraad", "waterschap": "waterschap_ab"}
KROON_FUNCTIE = _re(r"commissaris van de koning", r"gouverneur", r"dijkgraaf", r"watergraaf")


def klasse(rel_type: str, functie: str | None, org: dict) -> str:
    """Positieklasse van één band persoon → organisatie. Leunt op relatietype, de
    ambtstitel (`functie`, zoals het register hem geeft) en de organisatie (naam/laag/
    type, en bij de rijksoverheid de registersoort `oo_type`). Zonder titel geldt: een
    ambt of bestuurder bij een ministerie is een bewindspersoon, een lid van een Kamer een
    Kamerlid (oudere seed-relaties). Daarna: een bekende naam (NAAM_KLASSE), en binnen de
    overheid de ambtelijke top, weer een bekende naam (STAAT_NAAM_KLASSE) en de registersoort."""
    f = (functie or "").strip().lower()
    naam = org.get("name") or ""
    laag = org.get("bestuurslaag")
    otype = org.get("type")
    if otype in OVERHEID_TYPES:
        if f.startswith(("minister", "staatssecretaris")) or (
                not f and rel_type in ("ambt", "bestuurder") and naam.startswith("Ministerie")):
            return "kabinet"
        if rel_type in ("ambt", "lidmaatschap"):
            if naam == "Tweede Kamer":
                return "tweede_kamer"
            if naam == "Eerste Kamer":
                return "eerste_kamer"
            if naam == "Europees Parlement" or f.startswith("europarlementari"):
                return "europarlement"
        if KAMERCOMMISSIE.search(naam) and rel_type in ("ambt", "lidmaatschap"):
            return "kamercommissie"
        if naam in PARLEMENTEN or POLITIEKE_STAF.search(f):
            return "politieke_staf"
        if laag in LOKAAL_GEKOZEN:
            if laag == "gemeente" and f.startswith("burgemeester"):
                return "burgemeester"
            if laag == "gemeente" and f.startswith("wethouder"):
                return "wethouder"
            if KROON_FUNCTIE.search(f):
                return "cdk_dijkgraaf"
            m = _lokaal_mandaat(rel_type, f)
            if m == "kiezers":
                return LOKAAL_GEKOZEN[laag]
            if m == "afgeleid" and laag != "gemeente":
                return "gedeputeerde"
            return "decentraal_overig"
    for k, patroon in NAAM_KLASSE:
        if patroon.search(naam):
            return k
    if otype in OVERHEID_TYPES:
        return _staat_klasse(f, naam, laag, otype, org)
    if KENNIS_NAAM.search(naam):
        return "kennis"   # een kennisinstituut als stichting (Lareb, Nivel, Trimbos, Deltares)
    if otype == "omroep":
        return "pers_media" if COMMERCIELE_OMROEP.search(naam) else "publieke_omroep"
    if otype == "bedrijf":
        for k, patroon in BEDRIJF_NAAM_KLASSE:
            if patroon.search(naam):
                return k
    return SECTOR_KLASSE.get(otype, "maatschappelijk")


def _oo_type(org):
    meta = org.get("metadata")
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except ValueError:
            return None
    return (meta or {}).get("oo_type") if isinstance(meta, dict) else None


def _staat_klasse(f, naam, laag, otype, org):
    """Klasse binnen de (rijks)overheid: de ambtelijke top van een ministerie of
    directoraat-generaal, dan een bekende naam, dan de registersoort."""
    oo = _oo_type(org)
    dg_org = naam.lower().startswith(("directoraat-generaal", "directoraat generaal"))
    if "commandant der strijdkrachten" in f or "chef defensiestaf" in f:
        return "veiligheid"
    if oo == "Ministerie" or naam.startswith("Ministerie") or dg_org:
        return "ambtelijke_top" if (AMBTELIJKE_TOP.search(f) or (dg_org and f)) else "ministerie"
    for k, patroon in STAAT_NAAM_KLASSE:
        if patroon.search(naam):
            return k
    if oo in OO_KLASSE:
        return OO_KLASSE[oo]
    if otype == "toezichthouder":
        return "toezicht"
    if otype == "rechterlijke_macht":
        return "rechtspraak"
    if laag == "eu":
        return "internationaal"
    return "overheid"


def _lokaal_mandaat(rel_type: str, f: str) -> str:
    """Mandaat van een positie bij een provincie, gemeente of waterschap uit de ambtstitel. Zonder
    titel: een kaal lid zit in de raad, de Staten of het algemeen bestuur (zoals een kaal lid van
    een Kamer een Kamerlid is), wie in dienst of adviseur is, is benoemd, en een kale bestuurder
    of draaideur blijft onbepaald."""
    for m, woorden in FUNCTIE_MANDAAT:
        if any(w in f for w in woorden):
            return m
    if rel_type == "lidmaatschap" and not f:
        return "kiezers"
    if rel_type in ("personeel", "dienstverband", "adviseur", "woordvoerder_van"):
        return "benoemd"
    return "onbepaald"


def mandaat(klasse_key: str, rel_type: str, functie: str | None, org: dict | None = None) -> str:
    """Hoe een positie vervuld wordt (zie MANDATEN). De klasse beslist waar ze één mandaat
    heeft; de overige functies bij gemeente, provincie en waterschap volgen de ambtstitel
    (_lokaal_mandaat). De benoemde staat is benoemd; netwerken buiten de overheid vallen buiten
    het openbaar bestuur, behalve een overheidsorganisatie daar (het CvdM)."""
    if klasse_key in KLASSE_MANDAAT:
        return KLASSE_MANDAAT[klasse_key]
    if klasse_key == "decentraal_overig":
        return _lokaal_mandaat(rel_type, (functie or "").strip().lower())
    blok = GROEP_BLOK[RANG_GROEP[klasse_key]]
    if blok == "staat":
        return "benoemd"
    return "benoemd" if org and org.get("type") in OVERHEID_TYPES else "buiten"


LEIDING = _re(r"voorzitter", r"president", r"directeur", r"bestuurder", r"-generaal", r"\bhoofd",
              r"\bchef\b", r"commissaris", r"toezicht", r"\bceo\b", r"\bcfo\b", r"partner", r"oprichter",
              r"korpschef", r"ombudsman", r"procureur", r"coördinator", r"hoofdredact", r"commandant",
              r"rector", r"decaan", r"raad van")


def _leiding(rel_type, functie):
    """Leidt of bestuurt deze positie (bestuurder, ambt, of een leidinggevende titel)? Alleen
    voor de volgorde: leiding eerst."""
    return rel_type in ("bestuurder", "ambt") or bool(LEIDING.search(functie or ""))


def _vul_mandaat(posities, tijd):
    """Mandaat per positie van één persoon. Een positie zonder titel die onbepaald blijft,
    neemt het mandaat over van haar posities mét titel bij dezelfde organisatie in dezelfde
    periode, als dat er één is: de seed-'bestuurder' van Gemeente Amsterdam naast het
    registerambt 'Burgemeester' is dezelfde functie."""
    for p in posities:
        p["mandaat"] = mandaat(p["klasse"], p["rel"]["relation_type"], p["rel"].get("functie"), p["org"])
    for p in posities:
        if p["mandaat"] != "onbepaald" or p["rel"].get("functie"):
            continue
        bekend = {q["mandaat"] for q in posities
                  if q["org"]["id"] == p["org"]["id"] and q["rel"].get("functie")
                  and q["mandaat"] not in ("onbepaald", "buiten")
                  and tijd.overlapt(p["rel"], q["rel"])}
        if len(bekend) == 1:
            p["mandaat"] = bekend.pop()


def _jaar(v):
    try:
        return int(str(v)[:4]) if v else None
    except ValueError:
        return None


def _peil(peiljaar):
    """Peildatum: vandaag (op de dag), of een opgegeven jaar (op jaarbasis)."""
    return str(peiljaar) if peiljaar else datetime.date.today().isoformat()


class _Tijd:
    """De looptijd van verbanden binnen het bestaan van hun eindpunten (looptijd.py)."""

    def __init__(self, ents, peil, gedateerd=False):
        self.ents, self.peil, self.gedateerd = ents, peil, gedateerd
        self.zonder_begin = {"banden": 0, "posities": 0}

    def eindpunten(self, r):
        return self.ents.get(r["source_id"]), self.ents.get(r["target_id"])

    def effectief(self, r):
        return looptijd.effectief(r, *self.eindpunten(r))

    def afgelopen(self, r):
        return looptijd.afgelopen(r, *self.eindpunten(r), peil=self.peil)

    def later(self, r, soort=None):
        """Valt het verband buiten de peildatum omdat het pas daarna begint? In een terugblik
        (gedateerd=True) ook als het model zijn begin niet kent: dan valt niet te zeggen dat het
        toen liep (het bestaan van de partij is geen begin). Die worden geteld per soort."""
        if self.gedateerd and not looptijd.geldig(r.get("active_from")):
            if soort:
                self.zonder_begin[soort] += 1
            return True
        return looptijd.voor(self.peil, self.effectief(r)[0])

    def overlapt(self, a, b):
        av, at, _ = self.effectief(a)
        bv, bt, _ = self.effectief(b)
        return looptijd.overlapt(av, at, bv, bt)

    def label(self, r):
        """'1990–2026', 'sinds 2019', 'tot 2026': het eigen begin, het effectieve einde (een
        opgeheven partij of organisatie kapt een open band af)."""
        f = _jaar(r.get("active_from"))
        u = _jaar(self.effectief(r)[1])
        if f and u:
            return f"{f}–{u}"
        if f:
            return f"sinds {f}"
        if u:
            return f"tot {u}"
        return ""

    def einde_door(self, r):
        door = self.effectief(r)[2]
        if door is None:
            return None
        e = self.ents[door]
        return {"id": door, "naam": e["name"], "einde": e.get("active_until")}


def _laad(conn):
    """Alle goedgekeurde entiteiten + relaties (het model is klein: enkele duizenden rijen)."""
    def rijen(sql):
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    ents = {e["id"]: e for e in rijen(
        "SELECT id, name, type, bestuurslaag, description, metadata, active_from, active_until "
        "FROM entities WHERE status = 'goedgekeurd' AND NOT vervangen")}
    rels = [r for r in rijen(
        "SELECT r.id, r.source_id, r.target_id, r.relation_type, r.functie, "
        "       r.active_from, r.active_until, r.active, m.name AS mechanism_name "
        "FROM relations r LEFT JOIN mechanisms m ON m.id = r.mechanism_id "
        "WHERE r.status = 'goedgekeurd' AND NOT r.vervangen")
        if r["source_id"] in ents and r["target_id"] in ents]
    return ents, rels


def _ander(r, eid):
    return r["target_id"] if r["source_id"] == eid else r["source_id"]


def _stamboom(conn, ents, peil=None):
    """Fusies tussen partijen: (hoofd, voorgangers, opvolgers) — zie looptijd.stamboom. Met een
    peildatum telt alleen een fusie die toen al had plaatsgevonden: in 2015 is de PvdA de PvdA."""
    opv = {}
    for vg, lijst in looptijd.opvolgingen(conn).items():
        if ents.get(vg, {}).get("type") != "partij":
            continue
        einde = ents[vg].get("active_until")
        if peil and not (einde and looptijd.voor(einde, peil)):
            continue
        lijst = [x for x in lijst if ents.get(x["opvolger"], {}).get("type") == "partij"]
        if lijst:
            opv[vg] = lijst
    hoofd, voorgangers = looptijd.stamboom(opv)
    return hoofd, voorgangers, {k: [x["opvolger"] for x in v] for k, v in opv.items()}


def _bouw(conn, peiljaar=None, gedateerd=False):
    """Kern: per partij (zonder samenvoegen) de banden per persoon, en per partijpersoon zijn
    posities. Samenvoegen langs fusies en de tijdtoets per groep doet _groep."""
    ents, rels = _laad(conn)
    tijd = _Tijd(ents, _peil(peiljaar), gedateerd=bool(gedateerd and peiljaar))
    is_partij = lambda i: ents[i]["type"] == "partij"      # noqa: E731
    is_persoon = lambda i: ents[i]["type"] == "persoon"    # noqa: E731

    per_partij = {i: {} for i, e in ents.items() if e["type"] == "partij"}
    for r in rels:
        if r["relation_type"] not in PARTIJBAND_TYPES:
            continue
        s, t = r["source_id"], r["target_id"]
        if is_partij(s) and is_persoon(t):
            p, pers = s, t
        elif is_persoon(s) and is_partij(t):
            p, pers = t, s
        else:
            continue
        if tijd.later(r, "banden"):
            continue   # begint pas na de peildatum (of onbekend, in een terugblik)
        per_partij[p].setdefault(pers, []).append(dict(r, partij_id=p))

    leden = {pers for pp in per_partij.values() for pers in pp}
    posities = {}   # persoon_id -> [positie-dict]
    for r in rels:
        if r["relation_type"] not in POSITIE_TYPES:
            continue
        for pers in (r["source_id"], r["target_id"]):
            if pers not in leden:
                continue
            org = ents[_ander(r, pers)]
            if org["type"] in ("persoon", "partij") or tijd.later(r, "posities"):
                continue
            posities.setdefault(pers, []).append({
                "rel": r, "org": org,
                "klasse": klasse(r["relation_type"], r.get("functie"), org),
                "afgelopen": tijd.afgelopen(r),
                "leiding": _leiding(r["relation_type"], r.get("functie")),
            })
    for ps in posities.values():
        _vul_mandaat(ps, tijd)
    return ents, per_partij, posities, rels, tijd


def _groep(partij_ids, per_partij, posities, tijd):
    """De personen van een groep partijen (een partij plus haar voorgangers) met hun banden en
    posities. Een positie telt voor de groep als ze in de tijd met een band overlapt: een
    positie van vóór of ná de band blijft zichtbaar maar telt niet. 'Nu' betekent dat een band
    met de groep én de positie vandaag lopen."""
    slots = {}
    for p in partij_ids:
        for pers, banden in per_partij.get(p, {}).items():
            slots.setdefault(pers, {"banden": [], "posities": []})["banden"] += banden
    for pers, slot in slots.items():
        slot["band_afgelopen"] = all(tijd.afgelopen(b) for b in slot["banden"])
        actieve_banden = [b for b in slot["banden"] if not tijd.afgelopen(b)]
        for pos in posities.get(pers, []):
            binnen = any(tijd.overlapt(b, pos["rel"]) for b in slot["banden"])
            slot["posities"].append(dict(
                pos, binnen_band=binnen,
                nu=bool(binnen and actieve_banden and not pos["afgelopen"]),
            ))
    return slots


def _klassen_lijst():
    return [{"key": k, "label": lab, "groep": g, "groep_label": GROEPEN[g],
             "bulk": k in BULK_KLASSEN, "uitleg": KLASSE_UITLEG.get(k)}
            for k, lab, g in KLASSEN]


def _mandaten_lijst():
    blok_label = dict(BLOKKEN)
    return [{"key": k, "label": lab, "kort": kort, "blok": b, "blok_label": blok_label.get(b),
             "uitleg": uitleg} for k, lab, kort, b, uitleg in MANDATEN]


def _indeling():
    """De lijsten die de pagina nodig heeft om op klasse én op mandaat in te delen."""
    return {"klassen": _klassen_lijst(),
            "groepen": [{"key": k, "label": lab, "blok": b} for k, lab, b in GROEPEN_LIJST],
            "domeinblokken": [{"key": k, "label": lab, "uitleg": u} for k, lab, u in DOMEINBLOKKEN],
            "kruisingen": [{"key": k, "label": lab, "blokken": list(bl), "uitleg": u}
                           for k, lab, bl, u in KRUISINGEN],
            "mandaten": _mandaten_lijst(),
            "blokken": [{"key": k, "label": lab} for k, lab in BLOKKEN],
            "mandaat_rij_labels": MANDAAT_RIJ_LABELS}


def _leeg_tellingen():
    return {"telling": {}, "telling_groep": {}, "telling_dblok": {}, "telling_mandaat": {},
            "telling_mk": {}, "telling_blok": {}, "telling_kruis": {}}


def _tel(tellingen, slot):
    """Tel één persoon één keer per klasse, domein, mandaat, mandaat+klasse ('kiezers|gemeente')
    en blok, als [alle, nu]: alleen posities binnen de band, 'nu' als die vandaag loopt."""
    alle, nu = set(), set()
    for pos in slot["posities"]:
        if not pos["binnen_band"]:
            continue
        m = pos["mandaat"]
        g = RANG_GROEP[pos["klasse"]]
        s = {("telling", pos["klasse"]), ("telling_groep", g), ("telling_dblok", GROEP_BLOK[g]),
             ("telling_mandaat", m), ("telling_mk", f"{m}|{pos['klasse']}")}
        if MANDAAT_BLOK[m]:
            s.add(("telling_blok", MANDAAT_BLOK[m]))
        alle |= s
        if pos["nu"]:
            nu |= s
    # Concrete combinaties van blokken (gekozen én ongekozen staat, …): de verwevenheid.
    for verz in (alle, nu):
        blokken = {k for dim, k in verz if dim == "telling_dblok"}
        for sleutel, _, paar, _ in KRUISINGEN:
            if set(paar) <= blokken:
                verz.add(("telling_kruis", sleutel))
    for dim, k in alle:
        tellingen[dim].setdefault(k, [0, 0])[0] += 1
    for dim, k in nu:
        tellingen[dim][k][1] += 1


def _hoofdklasse(posities):
    tellend = [p for p in posities if p["binnen_band"]]
    for pool in ([p for p in tellend if p["nu"]], tellend):
        if pool:
            return min(pool, key=lambda p: RANG[p["klasse"]])["klasse"]
    return None


def _bestaan_label(e):
    f, u = _jaar(e.get("active_from")), _jaar(e.get("active_until"))
    if f and u:
        return f"{f}–{u}"
    if f:
        return f"sinds {f}"
    return f"tot {u}" if u else ""


def _partij_kort(ents, pid):
    e = ents[pid]
    return {"id": pid, "naam": e["name"], "looptijd": _bestaan_label(e)}


def _groep_ids(pid, voorgangers, fusies):
    return {pid} | (set(voorgangers.get(pid, ())) if fusies else set())


# ── Sleutelposities: de benoemde topfuncties zelf, met of zonder partijband ──────────────
# Een leidinggevende titel (zoals het register hem geeft) als ambt of bestuurder bij een
# organisatie in de benoemde staat of de media. Een plaatsvervanger of gewoon lid niet.
SLEUTEL_KLASSEN = ("cdk_dijkgraaf", "ambtelijke_top", "planbureau", "toezicht", "inspectie", "uitvoering",
                   "hoge_colleges", "advies", "kennis", "rechtspraak", "veiligheid", "internationaal",
                   "publieke_omroep", "pers_media", "mediabestel")
SLEUTEL_FUNCTIE = _re(r"-generaal", r"\bvoorzitter\b", r"\bpresident\b", r"vice-?president", r"\bdirecteur\b",
                      r"bestuursvoorzitter", r"directeur-bestuurder", r"korpschef", r"ombudsman",
                      r"nationaal coördinator", r"commandant", r"hoofdredacteur", r"\bceo\b",
                      r"commissaris van de koning", r"dijkgraaf", r"watergraaf")
NIET_SLEUTEL = _re(r"plaatsvervangend", r"\bplv\b", r"\blid\b", r"vice-?voorzitter", r"fractievoorzitter",
                   r"commissievoorzitter", r"adjunct")
# Instituties die in dit overzicht horen (2026-10-13: "ook andere instituties van belang
# meenemen, Lareb … wat nog meer?"). Alleen om de dekking te tonen: wat ontbreekt in het
# model, of staat erin zonder leidinggevende functie. De ministeries komen uit het register.
INSTITUTEN_VAN_BELANG = [
    ("Algemene Bestuursdienst", "ambtelijke_top", r"algemene bestuursdienst"),
    ("Centraal Planbureau", "planbureau", r"centraal planbureau"),
    ("Sociaal en Cultureel Planbureau", "planbureau", r"sociaal en cultureel planbureau"),
    ("Planbureau voor de Leefomgeving", "planbureau", r"planbureau voor de leefomgeving"),
    ("ACM", "toezicht", r"autoriteit consument"), ("AFM", "toezicht", r"autoriteit financiële markten"),
    ("De Nederlandsche Bank", "toezicht", r"nederlandsche bank"),
    ("Nederlandse Zorgautoriteit", "toezicht", r"zorgautoriteit"),
    ("Autoriteit Persoonsgegevens", "toezicht", r"autoriteit persoonsgegevens"),
    ("Kansspelautoriteit", "toezicht", r"kansspelautoriteit"),
    ("Onderzoeksraad voor Veiligheid", "toezicht", r"onderzoeksraad voor veiligheid"),
    ("Inspectie Gezondheidszorg en Jeugd", "inspectie", r"inspectie gezondheidszorg"),
    ("Nederlandse Arbeidsinspectie", "inspectie", r"arbeidsinspectie"),
    ("NVWA", "inspectie", r"voedsel- en warenautoriteit"),
    ("Inspectie Leefomgeving en Transport", "inspectie", r"inspectie leefomgeving"),
    ("Inspectie van het Onderwijs", "inspectie", r"inspectie van het onderwijs"),
    ("Belastingdienst", "uitvoering", r"^belastingdienst"), ("Dienst Toeslagen", "uitvoering", r"toeslagen"),
    ("UWV", "uitvoering", r"werknemersverzekeringen|\buwv\b"),
    ("Sociale Verzekeringsbank", "uitvoering", r"sociale verzekeringsbank"),
    ("DUO", "uitvoering", r"dienst uitvoering onderwijs"),
    ("IND", "uitvoering", r"naturalisatiedienst"), ("COA", "uitvoering", r"opvang asielzoekers"),
    ("RVO", "uitvoering", r"ondernemend nederland"), ("Rijkswaterstaat", "uitvoering", r"rijkswaterstaat"),
    ("Kadaster", "uitvoering", r"kadaster"), ("Zorginstituut Nederland", "uitvoering", r"zorginstituut"),
    ("Raad van State", "hoge_colleges", r"^raad van state"),
    ("Algemene Rekenkamer", "hoge_colleges", r"algemene rekenkamer"),
    ("Nationale ombudsman", "hoge_colleges", r"nationale ombudsman"),
    ("SER", "advies", r"sociaal-economische raad"), ("WRR", "advies", r"regeringsbeleid"),
    ("Gezondheidsraad", "advies", r"gezondheidsraad"), ("Onderwijsraad", "advies", r"onderwijsraad"),
    ("Raad voor Volksgezondheid en Samenleving", "advies", r"volksgezondheid en samenleving"),
    ("Raad voor de leefomgeving en infrastructuur", "advies", r"leefomgeving en infrastructuur"),
    ("Adviesraad Internationale Vraagstukken", "advies", r"internationale vraagstukken"),
    ("Raad voor het Openbaar Bestuur", "advies", r"raad voor het openbaar bestuur"),
    ("Raad voor Cultuur", "advies", r"raad voor cultuur"), ("Adviesraad Migratie", "advies", r"adviesraad migratie"),
    ("Kiesraad", "advies", r"kiesraad"), ("Wetenschappelijke Klimaatraad", "advies", r"klimaatraad"),
    ("College voor de Rechten van de Mens", "advies", r"rechten van de mens"),
    ("RIVM", "kennis", r"\brivm\b"), ("CBS", "kennis", r"centraal bureau voor de statistiek"),
    ("KNMI", "kennis", r"meteorologisch instituut|\bknmi\b"),
    ("College ter Beoordeling van Geneesmiddelen", "kennis", r"beoordeling van geneesmiddelen"),
    ("Bijwerkingencentrum Lareb", "kennis", r"\blareb\b"), ("TNO", "kennis", r"\btno\b"),
    ("NWO", "kennis", r"^nwo\b"), ("KNAW", "kennis", r"\bknaw\b"), ("ZonMw", "kennis", r"zorgonderzoek nederland|zonmw"),
    ("Nederlands Forensisch Instituut", "kennis", r"forensisch instituut"), ("WODC", "kennis", r"\bwodc\b"),
    ("Nivel", "kennis", r"\bnivel\b"), ("Trimbos-instituut", "kennis", r"trimbos"), ("Deltares", "kennis", r"deltares"),
    ("Hoge Raad", "rechtspraak", r"^hoge raad"), ("Raad voor de rechtspraak", "rechtspraak", r"raad voor de rechtspraak"),
    ("Openbaar Ministerie", "rechtspraak", r"openbaar ministerie"),
    ("Parket bij de Hoge Raad", "rechtspraak", r"parket bij de hoge raad"),
    ("AIVD", "veiligheid", r"\baivd\b"), ("MIVD", "veiligheid", r"\bmivd\b"), ("NCTV", "veiligheid", r"\bnctv\b"),
    ("Politie", "veiligheid", r"^politie$"), ("Koninklijke Marechaussee", "veiligheid", r"marechaussee"),
    ("Commandant der Strijdkrachten", "veiligheid", r"commandant der strijdkrachten|defensiestaf"),
    ("Nationaal Cyber Security Centrum", "veiligheid", r"cyber security centrum|\bncsc\b"),
    ("Europese Commissie", "internationaal", r"europese commissie"),
    ("Europees Geneesmiddelenbureau (EMA)", "internationaal", r"medicines agency|geneesmiddelenbureau"),
    ("NPO", "publieke_omroep", r"^npo$"), ("NOS", "publieke_omroep", r"^nos$"), ("ANP", "pers_media", r"^anp$"),
    ("Commissariaat voor de Media", "mediabestel", r"commissariaat voor de media"),
    ("Raad voor de Journalistiek", "mediabestel", r"raad voor de journalistiek"),
    ("Stimuleringsfonds voor de Journalistiek", "mediabestel", r"stimuleringsfonds voor de journalistiek"),
    ("NVJ", "mediabestel", r"\bnvj\b|vereniging van journalisten"),
    ("Beeld en Geluid", "mediabestel", r"beeld en geluid"),
]


def _neg(datum):
    """Sorteersleutel 'nieuwste eerst' voor een datumtekst (JJJJ[-MM[-DD]]); leeg achteraan."""
    return tuple(-ord(c) for c in datum) if datum else (1,)


def _functie_rang(functie):
    """Secretarissen-generaal vóór directeuren-generaal vóór de rest."""
    f = functie.lower()
    return 0 if "secretaris-generaal" in f else 1 if "directeur-generaal" in f else 2


def _sleutelposities(ents, rels, per_partij, tijd):
    """Wie bekleedt volgens het model de benoemde topfuncties, en is die persoon aan een
    partij verbonden? Plus de dekking: welke instituties van belang ontbreken of geen
    leidinggevende functie in het model hebben. Telt nergens mee."""
    partijen_van = {}
    for pid, leden in per_partij.items():
        for pers, banden in leden.items():
            partijen_van.setdefault(pers, []).append({
                "id": pid, "naam": ents[pid]["name"],
                "afgelopen": all(tijd.afgelopen(b) for b in banden)})
    gezien = {}
    for r in rels:
        if r["relation_type"] not in ("ambt", "bestuurder"):
            continue
        f = (r.get("functie") or "").strip()
        if not SLEUTEL_FUNCTIE.search(f) or NIET_SLEUTEL.search(f):
            continue
        s, t = ents[r["source_id"]], ents[r["target_id"]]
        pers, org = (s, t) if s["type"] == "persoon" else (t, s)
        if pers["type"] != "persoon" or org["type"] in ("persoon", "partij"):
            continue
        k = klasse(r["relation_type"], f, org)
        if k not in SLEUTEL_KLASSEN or tijd.later(r):
            continue
        functie = gezien.setdefault((org["id"], f.lower()), {
            "klasse": k, "functie": f, "org": {"id": org["id"], "naam": org["name"]}, "houders": {}})
        afg = tijd.afgelopen(r)
        oud = functie["houders"].get(pers["id"])
        if oud and not oud["afgelopen"]:
            continue   # dezelfde persoon twee keer: de lopende band wint
        functie["houders"][pers["id"]] = {
            "relation_id": r["id"], "persoon": {"id": pers["id"], "naam": pers["name"]},
            "looptijd": tijd.label(r), "afgelopen": afg, "begin": r.get("active_from") or "",
            "partijen": sorted(partijen_van.get(pers["id"], []), key=lambda p: (p["afgelopen"], p["naam"])),
        }
    # Eén functie per organisatie en titel, met al haar houders: lopend eerst, nieuwste begin
    # eerst. Meer dan één lopende houder van een enkelvoudige functie betekent meestal dat een
    # einddatum ontbreekt; de pagina toont dat, het model kiest niet zelf.
    functies = []
    for x in gezien.values():
        houders = sorted(x["houders"].values(), key=lambda h: (h["afgelopen"], _neg(h["begin"]),
                                                                 h["persoon"]["naam"]))
        for h in houders:
            del h["begin"]
        x["houders"] = houders
        x["afgelopen"] = all(h["afgelopen"] for h in houders)
        functies.append(x)
    functies.sort(key=lambda x: (RANG[x["klasse"]], _functie_rang(x["functie"]),
                                 x["org"]["naam"].lower(), x["functie"].lower()))

    met_functie = {}
    for x in functies:
        o = met_functie.setdefault(x["org"]["id"], [False, False])
        o[0] = True
        o[1] = o[1] or not x["afgelopen"]
    namen = [(e["id"], e["name"]) for e in ents.values() if e["type"] not in ("persoon", "partij")]
    verwacht = [(lab, k, re.compile(pat, re.IGNORECASE)) for lab, k, pat in INSTITUTEN_VAN_BELANG]
    verwacht += [(e["name"], "ambtelijke_top", re.compile("^" + re.escape(e["name"]) + "$"))
                 for e in ents.values() if _oo_type(e) == "Ministerie"]
    instituten = []
    for lab, k, patroon in verwacht:
        ids = [i for i, naam in namen if patroon.search(naam)]
        instituten.append({
            "naam": lab, "klasse": k, "id": ids[0] if ids else None,
            "met_functie": [any(met_functie.get(i, [False, False])[j] for i in ids) for j in (0, 1)],
        })
    return {"functies": functies, "instituten": instituten}


def compute_overzicht(conn, peiljaar=None, fusies=True, gedateerd=False) -> dict:
    """Alle partijen: tellingen per positieklasse (personen, 'alle' en 'nu') + de
    organisaties waar mensen uit twee of meer partijen een positie hebben + de benoemde
    sleutelposities. Met fusies=True is een opgeheven partij een deel van de kolom van haar
    opvolger (stamboom)."""
    ents, per_partij, posities, rels, tijd = _bouw(conn, peiljaar, gedateerd)
    hoofd, voorgangers, opvolgers = _stamboom(conn, ents, tijd.peil)
    kolommen = [p for p in per_partij if not (fusies and p in hoofd)]
    uit = []
    gedeeld = {}   # org_id -> {kolom_id: {"alle": set, "nu": set}}
    org_klasse = {}   # org_id -> klasse van de eerste positie daar (voor het domein)
    for pid in kolommen:
        groep = _groep_ids(pid, voorgangers, fusies)
        pp = _groep(groep, per_partij, posities, tijd)
        if not pp:
            continue
        tellingen = _leeg_tellingen()
        n_nu = 0
        for pers, slot in pp.items():
            if not slot["band_afgelopen"]:
                n_nu += 1
            _tel(tellingen, slot)
            for pos in slot["posities"]:
                if not pos["binnen_band"]:
                    continue
                g = gedeeld.setdefault(pos["org"]["id"], {}).setdefault(
                    pid, {"alle": set(), "nu": set()})
                g["alle"].add(pers)
                if pos["nu"]:
                    g["nu"].add(pers)
                org_klasse.setdefault(pos["org"]["id"], pos["klasse"])
        kol = {"id": pid, "naam": ents[pid]["name"], "looptijd": _bestaan_label(ents[pid]),
               "n_personen": [len(pp), n_nu], **tellingen}
        if fusies and voorgangers.get(pid):
            kol["voorgangers"] = sorted((_partij_kort(ents, v) for v in voorgangers[pid]),
                                        key=lambda v: (v["looptijd"], v["naam"]))
        if opvolgers.get(pid):
            kol["opgegaan_in"] = [_partij_kort(ents, o) for o in opvolgers[pid]]
        uit.append(kol)
    uit.sort(key=lambda p: (-p["n_personen"][0], p["naam"].lower()))

    orgs = []
    for oid, per_kolom in gedeeld.items():
        if len(per_kolom) < 2:
            continue
        o = ents[oid]
        orgs.append({
            "id": oid, "naam": o["name"], "type": o["type"], "laag": o.get("bestuurslaag"),
            "overheid": o["type"] in OVERHEID_TYPES, "groep": RANG_GROEP[org_klasse[oid]],
            "blok": GROEP_BLOK[RANG_GROEP[org_klasse[oid]]],
            "partijen": {str(pid): {"alle": len(v["alle"]), "nu": len(v["nu"])}
                         for pid, v in per_kolom.items()},
        })
    orgs.sort(key=lambda o: (-len(o["partijen"]),
                             -sum(v["alle"] for v in o["partijen"].values()),
                             o["naam"].lower()))
    return {"peiljaar": int(_peil(peiljaar)[:4]), "peildatum": _peil(peiljaar),
            "fusies": bool(fusies), "gedateerd": tijd.gedateerd, "zonder_begin": tijd.zonder_begin,
            **_indeling(), "partijen": uit,
            "gedeelde_organisaties": orgs,
            "sleutelposities": _sleutelposities(ents, rels, per_partij, tijd)}


def _rel_uit(r, eid, ents, tijd):
    """Eén relatie vanuit het perspectief van entiteit eid (voor 'overige banden')."""
    ander = ents[_ander(r, eid)]
    return {
        "relation_id": r["id"], "type": r["relation_type"],
        "richting": "uit" if r["source_id"] == eid else "in",
        "ander": {"id": ander["id"], "naam": ander["name"], "type": ander["type"]},
        "mechanisme": r.get("mechanism_name"), "functie": r.get("functie"),
        "looptijd": tijd.label(r), "afgelopen": tijd.afgelopen(r),
    }


def _ontdubbel(posities):
    """Oudere seed-relaties ('bestuurder' van een ministerie, 'lid' van de Tweede Kamer)
    staan vaak naast het registerambt bij dezelfde organisatie ('Minister van …',
    'Kamerlid'). Heeft een organisatie in dezelfde klasse en met hetzelfde mandaat een positie
    mét ambtstitel, dan valt de kale variant weg uit de weergave (de tellingen zijn per
    persoon en klasse of mandaat en veranderen daardoor niet)."""
    sleutel = lambda p: (p["org"]["id"], p["klasse"], p["mandaat"])   # noqa: E731
    met_titel = {sleutel(p) for p in posities if p["rel"].get("functie")}
    return [p for p in posities if p["rel"].get("functie") or sleutel(p) not in met_titel]


def _label(pos):
    r = pos["rel"]
    if r.get("functie"):
        return r["functie"]
    if r["relation_type"] in ("ambt", "lidmaatschap", "bestuurder") and pos["klasse"] in KLASSE_TITELS:
        return KLASSE_TITELS[pos["klasse"]]
    return POSITIE_LABELS[r["relation_type"]]


def compute_partij(conn, partij_id: int, peiljaar=None, fusies=True, gedateerd=False):
    """Eén partij in detail: per persoon de band(en), posities en overige relaties, plus
    de banden van de partij zelf met organisaties. Met fusies=True horen de partijen die erin
    opgingen erbij (elke band noemt zijn partij). None als het geen (goedgekeurde) partij is."""
    ents, per_partij, posities, rels, tijd = _bouw(conn, peiljaar, gedateerd)
    if partij_id not in per_partij:
        return None
    hoofd, voorgangers, opvolgers = _stamboom(conn, ents, tijd.peil)
    groep = _groep_ids(partij_id, voorgangers, fusies)
    pp = _groep(groep, per_partij, posities, tijd)

    # Overige relaties per persoon: alles wat geen band met een partij en geen positie is.
    overig = {}
    for r in rels:
        for pers in (r["source_id"], r["target_id"]):
            if pers not in pp:
                continue
            ander = ents[_ander(r, pers)]
            if r["relation_type"] in POSITIE_TYPES and ander["type"] != "persoon":
                continue   # band met een partij of positie: staat al elders
            overig.setdefault(pers, []).append(_rel_uit(r, pers, ents, tijd))

    andere_partijen = {}
    for pid, leden in per_partij.items():
        if pid in groep:
            continue
        for pers, banden in leden.items():
            if pers in pp:
                andere_partijen.setdefault(pers, []).append({
                    "id": pid, "naam": ents[pid]["name"],
                    "afgelopen": all(tijd.afgelopen(b) for b in banden)})

    personen = []
    tellingen = _leeg_tellingen()
    for pers, slot in pp.items():
        # Tellen op alle posities (zelfde getallen als het overzicht); tonen ontdubbeld.
        _tel(tellingen, slot)
        posities_p = sorted(_ontdubbel(slot["posities"]), key=lambda p: (
            not p["binnen_band"], p["afgelopen"], RANG[p["klasse"]], p["org"]["name"].lower()))
        banden = sorted(slot["banden"], key=lambda b: (tijd.afgelopen(b), -(_jaar(b.get("active_from")) or 0)))
        personen.append({
            "id": pers, "naam": ents[pers]["name"],
            "band": [{"relation_id": b["id"], "type": b["relation_type"],
                      "label": BAND_LABELS[b["relation_type"]], "looptijd": tijd.label(b),
                      "afgelopen": tijd.afgelopen(b), "einde_door": tijd.einde_door(b),
                      "partij": {"id": b["partij_id"], "naam": ents[b["partij_id"]]["name"]}}
                     for b in banden],
            "band_afgelopen": slot["band_afgelopen"],
            "hoofdklasse": _hoofdklasse(slot["posities"]),
            "posities": [{
                "relation_id": p["rel"]["id"], "klasse": p["klasse"], "mandaat": p["mandaat"],
                "leiding": p["leiding"],
                "label": _label(p),
                "type": p["rel"]["relation_type"],
                "org": {"id": p["org"]["id"], "naam": p["org"]["name"],
                        "type": p["org"]["type"], "laag": p["org"].get("bestuurslaag")},
                "looptijd": tijd.label(p["rel"]), "afgelopen": p["afgelopen"],
                "binnen_band": p["binnen_band"], "nu": p["nu"],
            } for p in posities_p],
            "overig": sorted(overig.get(pers, []), key=lambda o: (o["afgelopen"], o["type"])),
            "andere_partijen": andere_partijen.get(pers, []),
        })
    personen.sort(key=lambda p: (
        p["band_afgelopen"],
        RANG.get(p["hoofdklasse"], len(RANG)),
        p["naam"].lower()))

    organisaties = []
    for r in rels:
        via = next((p for p in groep if p in (r["source_id"], r["target_id"])), None)
        if via is None:
            continue
        ander = ents[_ander(r, via)]
        if ander["id"] in groep:
            continue   # band tussen partijen van dezelfde stamboom
        if ander["type"] == "persoon" and r["relation_type"] in PARTIJBAND_TYPES:
            continue   # persoonsband: staat onder 'personen' (of valt buiten de peildatum)
        o = _rel_uit(r, via, ents, tijd)
        if via != partij_id:
            o["via"] = {"id": via, "naam": ents[via]["name"]}
        organisaties.append(o)
    organisaties.sort(key=lambda o: (o["afgelopen"], o["type"], o["ander"]["naam"].lower()))

    e = ents[partij_id]
    uit = {
        "peiljaar": int(_peil(peiljaar)[:4]), "peildatum": _peil(peiljaar), "fusies": bool(fusies),
        "gedateerd": tijd.gedateerd, "zonder_begin": tijd.zonder_begin,
        **_indeling(),
        "partij": {"id": partij_id, "naam": e["name"], "beschrijving": e.get("description"),
                   "looptijd": _bestaan_label(e)},
        "n_personen": [len(pp), sum(1 for s in pp.values() if not s["band_afgelopen"])],
        **tellingen, "personen": personen, "organisaties": organisaties,
    }
    if fusies and voorgangers.get(partij_id):
        uit["partij"]["voorgangers"] = sorted(
            (_partij_kort(ents, v) for v in voorgangers[partij_id]),
            key=lambda v: (v["looptijd"], v["naam"]))
    if opvolgers.get(partij_id):
        uit["partij"]["opgegaan_in"] = [_partij_kort(ents, o) for o in opvolgers[partij_id]]
    return uit
