# Mission-log: hoofdredacteuren grote kranten — ideologie & clubjes (assistent) — 2026-07-10

**Account:** `assistent` (bijdrager, rate-exempt). Alles landt `voorgesteld` — een mens beslist.
**Opdracht eigenaar:** "Zoek de ideologie uit en alle banden en clubjes van de hoofdredacteuren
van alle grote kranten" + "gebruik meerdere subagents".
**Methode:** 8 parallelle onderzoeks-subagents (één per krant: Telegraaf, Volkskrant, AD, NRC,
Trouw, FD, Parool + een naloop voor Telegraaf-duo-collega Esther Wemmers). Subagents deden alleen
webonderzoek; élk in te dienen citaat is daarna in de hoofdsessie **zelf verbatim hergeverifieerd**
via WebFetch vóór indienen. Ideologie-signalen strikt volgens `missies/ideoloog_brief.md`
(as-eigen framing, één bron ≤ één signaal per as, bestuurszetel ≠ establishment-signaal,
tweezijdige oogstplicht, onbepaald > geleende score).

## Wie zijn de hoofdredacteuren (peildatum 10-7-2026)?

| Krant | Hoofdredactie | In model |
|---|---|---|
| De Telegraaf | duo **Kamran Ullah** (398) + **Esther Wemmers** (470), sinds 1-6-2023 | bestonden al |
| de Volkskrant | **Pieter Klok** (464), sinds 1-9-2019 | bestond al |
| AD | **Rennie Rijpma** (469), sinds 1-7-2021 | bestond al |
| NRC | **Patricia Veldhuis** (465), sinds feb 2024 (ná René Moerland, vertrokken 31-10-2023) | bestond al |
| Trouw | duo **Wendelmoet Boersema** (466) + **Karel Smouter** (467), sinds 1-6-2024 (ná Cees van der Laan) | bestonden al |
| FD | **Perry Feenstra** (399), sinds 1-9-2020 (ná Jan Bonjer) | bestond al |
| Het Parool | duo **Jildou van der Bijl** (441) + **Michiel Couzy** (442), sinds mei 2025 (ná Kamilla Leupen) | bestonden al |

## Ingediend — 23 bronnen (1608–1629, 1631), 3 entiteiten, 19 relaties, 34 argumenten

### Nieuwe entiteiten
- **Kamilla Leupen (1051)** — ex-hoofdredacteur Parool (2021–2025), per mei 2025 algemeen
  directeur nieuwsmedia DPG (Volkskrant/Trouw/Parool/NU.nl): draaideur hoofdredactie→uitgeversdirectie.
- **Haya van Someren Stichting (1052)** — VVD-opleidingsinstituut (Ullah-band).
- **De Amsterdamsche Kring (1053)** — Amsterdamse sociëteit, rol elite_forum (Ullah-band).

### Clubjes & governance (relaties + supporting-arg met verbatim citaat)
- **NGH-lidmaatschap** (mech 179, bron 1612 = ledenlijst, per naam geverifieerd): Klok (rel 1868),
  Rijpma (1869), Veldhuis (1870), Smouter (1871), Couzy (1872), Wemmers (1873). NB: Ullah zat er al
  als bestuurder/secretaris (rel 895), Feenstra als penningmeester (rel 896). **Opvallend:**
  Boersema (Trouw) en Van der Bijl (Parool) staan als zittend hoofdredacteur *niet* op de ledenlijst.
- **Raad voor de Journalistiek**: Rijpma bestuurslid Stichting RvdJ namens NGH (rel 1874, kandidaat,
  bron 1613); Boersema lid van de Raad zelf, categorie journalisten (rel 1875, kandidaat, bron 1614).
- **Stichting PersVeilig** (opgericht 1-7-2025; bron 1631 = NVJ): bestuurszetels Wemmers (rel 1886)
  én Philippe Remarque/DPG (rel 1887), mech 179 — dit bestuur verbindt Mediahuis, DPG en NPO op
  persoonsniveau. Vervolgkandidaten (niet ingediend, personen ontbreken): Joost Oranje (NPO),
  Frans Pasma (NVJ), voorzitter Marcel Gelauff (ex-NOS).

### Loopbaan/draaideur (mech 18 tenzij anders; gedateerd)
- Rijpma → ANP personeel tot 2012 (rel 1876, bron 1617).
- Ullah → WNL 2010–2013 (rel 1877), → VVD-bestuur A'dam-West 2006–2010 + Kamerkandidaat #59
  (rel 1878, **mech 96 draaideur_politiek_media**), → Haya van Someren Stichting trainer 2011–2020
  (rel 1879, mech 96), → De Amsterdamsche Kring bestuur 2018–2020 (rel 1880, mech 136).
  Bron: cv-kader Universiteit Leiden-interview 2021 (1618) + eigen campagnetekst 2010 (1621).
- Smouter → De Correspondent 2013–2017 (rel 1881), → NRC 2021–2024 (rel 1882; bron 1624).
- Leupen → Het Parool 1999–2025 (rel 1883), → DPG Media directeur per mei 2025 (rel 1884; bron 1629).

### Ideologie-signalen (property `politieke_positie`, allen met verbatim geverifieerde citatie)
| Wie | Signaal | Arg | Bron |
|---|---|---|---|
| Klok | economisch:links ("Studeren is een recht…") | 2802 | Babel 1-2025 (1608) |
| Klok | establishment:establishment (RIVM-gatekeeping, "oerdilemma") | 2803 | HP/De Tijd 5-2025 (1609) |
| Klok | establishment:establishment ("waarom zou je tegen het RIVM ingaan?") | 2804 | Wapenveld 4-2024 (1610) |
| Klok | establishment:**anti**-establishment (zelfcorrectie: "niet op instituten…varen") | 2805 | De Vrieze 12-2023 (1611) |
| Rijpma | cultureel:progressief (genderrepresentatie-sturing) | 2806 | Nouveau 12-2021 (1615) |
| Rijpma | cultureel:progressief (meer vrouwen als redactiedoel) | 2807 | AD via WK 6-2021 (1616) |
| Ullah | cultureel:conservatief (diversiteit = meningen, niet identiteit) | 2808 | Villamedia 4-2021 (1619) |
| Ullah | cultureel:conservatief (havermelk-monocultuur/Bluesky) | 2809 | Babel 3-2026 (1620) |
| Ullah | economisch:rechts ("kleinere overheid", **gedateerd 2010**, campagne) | 2810 | Rep. Allochtonië (1621) |
| Veldhuis | establishment:establishment ("heilige taak…democratie te beschermen") | 2811 | ANS 5-2024 (1622) |
| Smouter | cultureel:progressief (afwijzing christelijk-nationalisme) | 2812 | Cvandaag 11-2024 (1623) |
| Van der Bijl | cultureel:progressief (Charter Diversiteit, LINDA 2019) | 2813 | Bladendokter (1626) |
| Feenstra | economisch:rechts (zwak; bedrijfsleven-sympathie) | 2814 | Villamedia 2-2024 (1627) |
| Feenstra | economisch:links (tegensignaal; "te veel consolidatie") | 2815 | Villamedia 9-2020 (1628) |
| Trouw (org) | cultureel:progressief (rectificatie migratie-column, hoofdredactionele brief 9-5-2026) | 2816 | Netkwesties (1625) |

**Poolbalans ronde:** cultureel 5×progressief / 2×conservatief; economisch 2×links / 2×rechts;
establishment 3×establishment / 1×anti. Tweezijdig gezocht bij iedereen (zoekslagen op beide polen);
de asymmetrie weerspiegelt wat citeerbaar bestaat, niet de zoekrichting.

## Onbepaald gelaten (eerlijke uitkomst, geen geleende scores)
- **Wemmers:** alle drie assen — laag-profiel, alleen merk-/vakuitspraken gevonden.
- **Boersema:** alle drie assen — het De Groene-boekcitaat (Gronings goud) is machtskritisch *werk*,
  geen houding-uiting; niet gecodeerd.
- **Couzy:** alle drie assen — Zakenprins-citaten bleken bij verificatie van co-auteur Van Dun;
  zijn "witte enclave"-tweet is niet fetchbaar én dubbelzinnig (gedeelde kop).
- **Veldhuis:** economisch + cultureel; **Rijpma:** economisch + establishment; **Klok:** cultureel;
  **Ullah:** establishment (recent); **Feenstra:** cultureel; **Van der Bijl:** economisch + establishment;
  **Smouter:** economisch + establishment.

## Bewust NIET ingediend
- Klok "één lijn trekken"-radiocitaat (maart 2020) via Containment Nu: activistische tweedehands
  bron, origineel niet gefetcht. Klok-vluchtelingenverdrag-citaat via De Dagelijkse Standaard:
  partijdige tweedehands bron, video zonder transcript.
- Ullah establishment-signaal 2010 ("Stem…liberaal geluid"): zelfde bron als het econ-signaal,
  grensgeval structureel/houding — dubbeltel-regel + zetelregel → weg.
- Ullah law-and-order-citaat ("gijzelen door angst"): audiobron, afleveringspagina-tekst niet
  woord-voor-woord tegen de audio te checken.
- Feenstra's RTL Z-doelgroepcitaat 2015 ("groep die ook graag wordt bereikt door adverteerders",
  Villamedia 14-8-2015) — géén ideologie-signaal, maar **kandidaat voor de welstandsmeter/**
  **koopkrachtselectie #176**; RTL Z bestaat niet als entiteit → genoteerd als vervolgwerk.
- Paywall-materiaal (FD-interviews Ullah, Villamedia-interviews Rijpma/Wemmers, Parool-stukken duo,
  Tubantia-interview Veldhuis, ND-interview Smouter, BNR-podcast Boersema): niet verbatim
  controleerbaar → niet gebruikt.
- Ullah NJR/Zwerfjongeren/Fonds 21-functies: buiten model-focus (opinievorming).
- Wemmers' vermeende "advocaat bij Mediahuis"-wissel (Google-snippet): op geen primaire pagina
  verifieerbaar, drie recente bronnen bevestigen dat ze gewoon hoofdredacteur is → als
  naamgenoot/zoekmachine-artefact beoordeeld.

## LinkedIn-afweging (standaard-reflex, expliciet)
Overwogen en **bewust overgeslagen**: de benoemings- en vakbladbronnen (Villamedia, NOS, Adformatie,
Leiden-cv) dekken de loopbanen al gedateerd en beter gesourcet dan zelf-gerapporteerde
LinkedIn-data (klasse grijs). Gericht vervolg dat wél zin heeft: een scrape van **Esther Wemmers**
(dunste publieke cv: functiejaren 1997–2017 en opleiding onbekend; beslecht ook de
advocaat-anomalie) en evt. **Jildou van der Bijl** (headline loopt achter). Sessie leefde op 3-7.

## Meldingen voor de eigenaar/admin
- **Duplicaat-relaties** in het model: Parool-duo heeft dubbele personeel-edges (973/1005 en
  974/1006) — opruimwerk voor admin, niet aan mij.
- Entiteit **Leupen** kreeg rol-suggestie `hoofdredacteur` (29) hoewel ze nu DPG-directeur is;
  er is geen passender rol (geen mediadirecteur-rol) — reviewer mag heroverwegen.
- `validate_model.py --strict` na de ronde: **EXIT 0**, golden snapshot groen (alles `voorgesteld`,
  telt nergens in mee tot merge).

## Naloop (zelfde dag): gerichte LinkedIn-scrape Esther Wemmers
Op vraag van de eigenaar ("waarom de scraper niet gebruikt?") de afweging herzien voor het ene
profiel waar hij wél meerwaarde had: Wemmers (dunste publieke cv). Scrape gelukt (sessie leefde):
11 ervaringen, 0 opleidingen. Oogst: gedateerde functietrap dec 1997 → heden, volledig binnen
Telegraaf/Mediahuis; **géén advocatuur-vermelding** → de "beëdigd als advocaat bij Mediahuis"-
snippet-anomalie is een naamgenoot/artefact. De mapper (`linkedin_naar_model.py`) bewust NIET
met `--indienen` gedraaid: die zou 11 aparte personeel-edges naar dezelfde org maken (incl.
groepeer-artefacten "Fulltime"/"TMG"/"Dagblad De Telegraaf"), terwijl het rondepatroon
(vgl. Remarque→Volkskrant 1996–2019) één gedateerde relatie per org is en de org-band al bestaat
(rel 1008). In plaats daarvan: bron 1721 (profiel, grijs voorgesteld) + supporting-arg **2912** op
rel 1008 met de volledige functietrap. **Admin-suggestie:** rel 1008 `active_from` 2023-06-01 →
1997-12 (de personeel-band is ouder dan het hoofdredacteurschap; beschrijving vermeldt de trap).
