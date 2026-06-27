# Documentalist — PAX × media, ronde 2 (perslijst → edges sourcen + ontbrekende kanalen)

**Datum:** 2026-06-22
**Aanleiding:** eigenaar wees op PAX' perslijst (`paxvoorvrede.nl/nieuws/pax-in-de-media/`) — ~350-400 vermeldingen, 2024-2026, bij vrijwel alle grote NL-titels. Vraag: noemenswaardige relaties of één patroon? Antwoord: **één structureel feit (PAX als routinematig vertrouwde bron — Sourcing-filter), niet 350 edges.** Eenheid = `PAX→titel` (één edge per medium), niet per optreden.
**Account:** `assistent` (eigen agent-token). Alles ingediend als `voorgesteld` — mens beslist.

## Doel van de ronde
1. Bestaande PAX→media-edges sourcen met geverifieerde *onderliggende* artikelen (niet de perslijst zelf).
2. Ontbrekende grote kanalen toevoegen — m.n. **ANP** (de persbureau-multiplier) en **Trouw** (meest genoemde titel, ontbrak).

## Crawl-beperking (eerlijk genoteerd)
- **Wél leesbaar** (body geverifieerd): persportaal.anp.nl, nos.nl, nd.nl.
- **Niet crawlbaar** (betaalmuur/blokkade): trouw.nl, nrc.nl, volkskrant.nl → bij die titels is de vindplaats (URL-locator) ingediend maar de directe PAX-quote in de body **niet** door de agent gelezen; gemarkeerd `twijfel` voor de reviewer. Geen verzonnen quotes.

## Queries (WebSearch)
1. `Trouw PAX vredesorganisatie geciteerd conflict wapenhandel 2024 2025`
2. `de Volkskrant PAX onderzoek Israël nederzettingen handel 2025`
3. `NRC PAX conflictanalist F-35 Israël geciteerd 2024`
4. site-filters trouw.nl / nrc.nl / volkskrant.nl → **400: domeinen niet toegankelijk voor crawler** (vandaar de twijfel-markeringen).

## Verificatie (WebFetch, body gelezen)
- **ANP** (persportaal, 25 nov 2025): Thomas van Gool (PAX) bij naam geciteerd — "Het is onvoorstelbaar dat Nederlandse spaar- en pensioengelden…". ANP-bericht = persbureau. ✓
- **Nederlands Dagblad** (1283115, 29 aug 2025): Van Gool "Israël-Palestina-expert van vredesorganisatie PAX" geciteerd. Zelfde kop/datum als het Volkskrant-stuk → identiek ANP-tweelingbericht (bewijs dat PAX de bron is). ✓
- **NOS Nieuwsuur** (2545611, 23 nov 2024): "een medewerker van vredesorganisatie PAX…"; opent met Van Gool als 'PAX-activist'. ✓
- **NOS** (2544164, 11 nov 2024): PAX-directeur Rolien Sasse geciteerd over de OS-bezuinigingen; ~70% staatsfinanciering genoemd. ✓
- **PAX-perslijst**: bevestigd als wegwijzer; echte onderliggende artikel-URL's voor Trouw/NRC/Volkskrant eruit gehaald.

## Ingediend (voorgesteld, account assistent)
**Bronnen (#144-#151):** ANP-bericht, Volkskrant 29-aug, Nederlands Dagblad 29-aug, Trouw Rode Lijn, NRC F-35 ×2, NOS Nieuwsuur, NOS kaalslag. Elk met url-locator + voorgestelde classificatie (kwaliteitsjournalistiek / nl_systeem).

**Nieuwe edges:**
- **#531 PAX → ANP** (`denktank_naar_persbureau`) — de multiplier: PAX-kopij via de bovenkant van de nieuwsketen. + arg **#621** met verbatim ANP-quote (geverifieerd).
- **#532 PAX → Trouw** (`expert_legitimatie`) — ontbrekende grote titel. + arg **#622**, citatie = Trouw-URL (locator); body niet gelezen → transparant gemarkeerd, reviewer bevestigt.

**Bestaande edges gesourcet:**
- **#470 PAX → de Volkskrant**: nieuw on-target arg **#620** (VK-URL + ND-tweelingbericht mét PAX-quote). Vervangt het afgewezen, off-target #536 (dat banken.nl op de VK-edge voerde).
- **#475 PAX → NRC** (arg #542): twee NRC F-35-artikelen als citatie (locator; body niet leesbaar).
- **#476 PAX → NOS** (arg #543): Rolien Sasse-quote (geverifieerd). Arg #584 (NOS Nieuwsuur): Van Gool/PAX-quote (geverifieerd).

## Advies-bestand
`data/bron_suggesties.json` herschreven naar deze stand: arg:622 (Trouw — bevestig vóór merge), arg:542 (NRC — locator, twijfel), arg:536 (vervangen door #620, verwijderbaar). De vervulde NOS-items (543/584, geverifieerde quotes) hebben geen suggestie meer nodig.

## Modelleer-notie
Elke vermelding op de perslijst is **bewijs onder een edge**, geen aparte edge — anders 350 orphan-relaties. De ~aantallen per titel kunnen later de **invloed-as** voeden (routine vs. incidenteel) via `property='influence'`-argumenten, niet als zelf-gerapporteerd gewicht. De perslijst zelf = PAX' eigen aggregatie: wegwijzer, nooit de citatie.

## Niets gemerged
Alle items staan `voorgesteld`. Mergen/verifiëren/classificeren blijft mensenwerk.
