# Missielog — lobby ↔ journalistiek

**Datum:** 2026-08-04
**Account:** `assistent` (indienen) — goedkeuring/merge door de eigenaar via `maxime` ("voeg alles toe als admin")
**Aanleiding:** vraag van de eigenaar: *"Wat voor verbanden kan je nog meer vinden met lobby en journalistiek?"*

## Diagnose vooraf

De lobby-laag van het model heeft een scheve vorm: de **omweg via denktank/expert** is instantie-rijk
maar argument-arm, en de **directe lobby→journalist-lijn** is in beide opzichten leeg.

| Mechanisme | instanties | mechanisme-argumenten (vóór deze ronde) |
|---|---:|---:|
| `expert_legitimatie` #87 | 158 | 5 |
| `denktank_financiering_bias` #52 | 117 | 0 |
| `expert_framing` #8 | 115 | 2 |
| `lobbyist_naar_journalist` #51 | 3 | 1 |
| `belangenbehartiging` #83 | 4 | 1 |
| `draaideur_journalistiek_voorlichting` #151 | 1 | 1 |
| `gecoordineerde_voorlichting` #84 | 1 | 0 |
| `voorlichter_informatiefilter` #48 | 1 | 2 |

Dat #151 één instantie heeft is het opvallendst: de eigen omschrijving noemt het *"de meest gelopen
draaideur van het Binnenhof"* — een claim die het model nergens waarmaakt. Het model telt in totaal
**6 voorlichter-entiteiten**.

## Ingediend en goedgekeurd

### Bronnen (alle geclassificeerd + locator)
| ID | Bron | Klasse |
|---|---|---|
| 2289 | Poole e.a., "Content analysis of Dutch newspaper coverage of three tobacco control policies, 2017-2019", BMJ Open 13(2):e057912, 10-02-2023, DOI 10.1136/bmjopen-2021-057912 | academisch |
| 2290 | Philip Morris International, "Philip Morris benoemt Ole Heil tot Director External Affairs Nederland", 09-05-2023 (eigen persbericht, PDF) | primair |
| 2291 | TabakNee, "Oud-woordvoerder VWS Ole Heil nu toplobbyist van Philip Morris", 22-05-2023 | grijs |
| 2292 | Nieuwspoort, "Over de sociëteit" (eigen website) | institutioneel |
| 2293 | Boom & Smouter, "De oesters van Nieuwspoort", De Groene Amsterdammer, 08-12-2010 | kwaliteitsjournalistiek |

### Entiteiten
- **1227 Ole Heil** (persoon, rol `voorlichter`)
- **1228 Philip Morris International** (bedrijf, rol `belanghebbende`)
- **1229 Bedrocan** (bedrijf, rol `belanghebbende`)

### Relaties — gedateerde persoon→org-affiliaties, instanties van `draaideurconstructie` #18
- **2235** Heil → Ministerie van VWS (586), `woordvoerder_van`, 2012-01-01 – 2019-12-31
- **2236** Heil → Bedrocan, `personeel`, 2019-01-01 – 2023-03-01
- **2237** Heil → Philip Morris International, `draaideur`, vanaf 2023-03-01

De org↔org-brug (VWS ↔ PMI) verschijnt hierdoor vanzelf; er is bewust géén org→org draaideur-relatie
opgeslagen (litmus: de persoon wisselt van werkgever → brug, geen directe edge).

### Argumenten (3760–3765, alle gemerged)
- **3760** op mechanisme **#51 `lobbyist_naar_journalist`** — Poole e.a. 2023. De eerste *gemeten*,
  peer-reviewed Nederlandse onderbouwing van dit mechanisme: de tabaksindustrie en haar bondgenoten
  kwamen voor in 38 van 134 artikelen (28%) in de tien best gelezen landelijke dagbladen
  (nov 2017 – nov 2019), en *"Negative coverage was predominantly accounted for by industry presence."*
- **3761–3763** op de drie Heil-relaties — verbatim uit het PMI-persbericht; de precisering
  "woordvoerder van Schippers en Bruins" is in de claim expliciet aan TabakNee toegeschreven in
  plaats van als modelfeit gesteld (bron is grijs).
- **3764–3765** op mechanisme **#179 `beroepsnetwerk_lidmaatschap`** — de Nieuwspoort-sociëteit is
  geen zuiver journalistieke club (~2000 leden: journalisten, politici, voorlichters, persattachés en
  PR-functionarissen samen), en de kritiek daarop komt van Joris Luyendijk, die het Nieuwspoort-
  *bestuur zelf* aanstelde als jaarlijkse "rapporteur politiek-publicitair complex".

**Geen RfC nodig.** Mechanisme #179 noemt de Nieuwspoort-sociëteit al bij naam; de vondst scherpt de
bestaande omschrijving aan in plaats van een nieuw theorie-element te vragen.

## Poorten
`scripts/test_scoring.py` 23/23 groen · `scripts/validate_model.py --strict`: geen fouten boven de
baseline (136 fouten, alle binnen baseline).

Score-effect: mechanisme #51 van 1 → 2 bronclusters (geloofwaardigheid 0,51); #179 naar 0,57. Alle
nieuwe elementen staan `onweersproken: true` en lopen dus tegen het M1.4-plafond van 0,70 — werk voor
de aanklager-agent.

## Bewust NIET ingediend (negatieve resultaten)

- **Tien kranten als afzonderlijke instanties van #51.** De studie geeft **geen uitsplitsing per titel**
  van de industrie-aanwezigheid; het enige per-krant-cijfer betreft de *toon* (De Telegraaf 58%
  oppositioneel). Tien "tabakslobby → krant"-relaties afleiden uit een corpusbreed percentage zou een
  eigen gevolgtrekking zijn, niet die van de auteurs. Daarom alleen een mechanisme-argument.
- **Mozaïek van Belangen** (Braun & Fraussen, Universiteit Leiden i.o.v. BZK, 20-12-2024). Het rapport
  bestaat en beveelt een lobbyregister aan, maar de PDF-tekstextractie mislukte, dus ik kreeg geen
  verbatim conclusie uit het primaire document; de citaten die ik heb komen van Transparency
  International NL — vindplaats, geen bewijs. Bovendien gaat het over lobby↔overheid, niet
  lobby↔journalistiek. Niet ingediend.
- **Handboek public affairs** (Van Drimmelen). Zou het Eumedion-patroon herhalen — de lobby die haar
  eigen mediastrategie op schrift zet — maar er kwam geen enkel verbatim citaat uit het boek los,
  alleen uitgeversteksten. Niet ingediend.
- **Grote Haagse PA-bureaus** (Publyon/ex-Dröge & van Drimmelen, Wepublic, Meines Holla, Van Oort).
  Ontbreken volledig in het model — een echt gat — maar ik vond geen geverifieerde, specifieke
  band met een redactie. Zonder die band is het geen edge.
- **Farma → patiëntenorganisaties → media** (Transparantieregister Zorg). Het geldspoor is
  gedocumenteerd, maar geen enkele geverifieerde stap van *dat geld* naar *een media-optreden*.
  Valt af op de model-focusregel: geen invloedslijn naar opinievorming.
- **Vrienden van Nieuwspoort** (sponsoring door bedrijven). De pagina gaf 404; geen uitspraak gedaan.

## LinkedIn-reflex
Dit was loopbaanonderzoek, dus de scraper hoorde de eerste stap te zijn. `data/linkedin/session.json`
**bestaat niet**, dus die route lag plat; de loopbaan is opgebouwd uit het PMI-persbericht (primair).
Wil de eigenaar de scraper weer inzetten: `python3 tools/linkedin/scrape_profile.py login`.

## Reparatieronde (zelfde dag, op verzoek "fix het")

### 1. Dubbele VWS-entiteit — opgelost
Voorstel **60** (`samenvoegen`, ingediend en geaccepteerd via `maxime`): entiteit **820**
"Ministerie van Volksgezondheid, Welzijn en Sport" → **586** "Ministerie van VWS". Relatie 1514
(VWS → SCP) is herbevestigd en verhuisd; 820 staat op `vervangen = 1` met een `lineage`-regel.
Niets verwijderd.

### 2. `draaideur_voorlichting_lobby` — bewust NIET aangemaakt
Er kwam geen tweede Nederlands geval van rijksvoorlichter → lobby boven water, en `draaideurconstructie`
#18 dekt de stap expliciet ("alle richtingen komen voor… lobbyist ↔ overheid/bedrijf"). Een eigen
mechanisme bouwen op n=1 is precies wat de kandidaat-discipline afraadt. Heil blijft op #18; het
blijft een RfC-kandidaat zodra er een tweede geval is.

**Wel gevonden op ditzelfde spoor, en toegevoegd:** de draaideur van het *mediatoezicht* naar de
gereguleerde partij. **Madeleine de Cock Buning** (1231), voorzitter van het Commissariaat voor de
Media, werd in januari 2020 lobbyist voor **Netflix** (1232) — een halfjaar na haar vertrek bij de
toezichthouder. Bron: Peter Teffer, Follow the Money, 19-04-2021 (bron 2296), die er ook bij vermeldt
dat de afkoelregels sinds 1 oktober 2020 geen sancties kennen. Relaties 2242/2243, argumenten
3770/3771. Voor een mediamodel is dit een relevantere richting dan de VWS-variant: het toezicht
bewaakt de spelregels van het bestel.

### 3. `draaideur_journalistiek_voorlichting` #151 — van 1 naar 3 instanties
- **Kees Berghuis** stond al in het model (539), maar zijn twee relaties hingen aan de generieke #18.
  Gecorrigeerd via het admin-pad: **1075** (→ VVD) naar **#151** — de overstap van chef politieke
  redactie RTL Nieuws naar hoofd voorlichting van de VVD-fractie — en **1074** (→ WNL) naar **#96**
  `draaideur_politiek_media`, de redactionele landing. Twee ontbrekende schakels toegevoegd
  (2244: VVD-persvoorlichter 2001–2006; 2245: RTL Nieuws 2006–2015) met argumenten 3772–3774.
  Bron: Trudy Brandenburg-van de Ven, Villamedia, 14-05-2025 (bron 2294).
- **Sebastiaan Meijer** (1230) toegevoegd met vier gedateerde affiliaties: AT5 2003–2009 (2238),
  NOS parlementair verslaggever 2009–2015 (2239), woordvoerder gemeente Amsterdam 2018–2024
  (**2240, #151**), hoofd communicatie politie Amsterdam vanaf 2024 (2241). Argumenten 3766–3769.
  Bron: Jasper Mulder, Adformatie, 03-07-2024 (bron 2295).

Poorten na de reparatie: `test_scoring.py` 23/23 groen, `--strict` geen fouten boven de baseline.
Instanties nu: #151 → 3, #96 → 11, #18 → 505.

**Provenance-noot:** waar de loopbaanchronologie uit een samenvatting van de pagina kwam in plaats van
een letterlijk overgenomen alinea, draagt de citatie `methode = llm_samenvatting_van_pagina`
(bronfactor 0,55) in plaats van `verbatim_quote`. De letterlijke passages (Adformatie over Meijers
AT5/NOS-jaren, Villamedia over de kritiek op de WNL-benoeming, FTM over Netflix) staan wél als
`verbatim_quote`.

## Resterend actiepunt

**Datums van goedgekeurde relaties zijn niet via de API te bewerken.** `_maintainer_patch` laat voor
een relatie alleen tekstvelden en `mechanism_id` toe, niet `active_from`/`active_until`. Daardoor
blijft relatie **1074** (Berghuis → WNL) ongedateerd en **1075** (Berghuis → VVD) zonder einddatum,
terwijl de bron 2015–2025 respectievelijk vanaf juni 2025 geeft. Inhoud hoort niet met een migratie
geschreven te worden, dus dit vraagt óf een kleine uitbreiding van `_maintainer_patch`, óf een
`herformuleren`-voorstel-pad voor relatiedatums.
