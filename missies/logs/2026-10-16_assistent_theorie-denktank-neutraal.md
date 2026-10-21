# Missielog: eigen stem van de denktank-mechanismen (#8, #52, #87, #118) en literatuur voor #52

- **Datum:** 2026-10-16
- **Account:** `assistent` (bijdrager). Alles ging via de REST-API op `localhost:5000` en staat op `voorgesteld` of `open`. Ik heb niets gemerged, geen status gewijzigd, niets verwijderd en niets in de DB geschreven. De DB heb ik alleen read-only gelezen.
- **Contract:** `missies/README.md` (laatste commit `efc2ad8`, 2026-10-13, met lokale wijzigingen in de werkboom) en CLAUDE.md § "Eigen stem, strikt". Er hoort geen eigen brief bij deze opdracht.
- **Opdracht:**
  1. Vier mechanismen neutraal herformuleren. Hun `description`/`effect` bevatten etiketten, oordelende aanhalingstekens en organisatienamen.
  2. #52 hernoemen zonder "bias".
  3. Literatuur voor #52, dat nul literatuurargumenten had: steunend én tegensprekend.
  4. Nagaan of de Quincy-brief beter op #8 past, met de omvang-confound als apart argument.

## 1. RfC's (alle `open`)

| RfC | Soort | Element | Wat |
|---|---|---|---|
| **#111** | herformuleren | mechanisme 52 `denktank_financiering_bias` | `description` + `effect` |
| **#112** | herformuleren | mechanisme 8 `expert_framing` | `description` + `effect` |
| **#113** | herformuleren | mechanisme 87 `expert_legitimatie` | `description` + `effect` |
| **#114** | herformuleren | mechanisme 118 `denktank_levert_expert` | `description` + `effect` |
| **#115** | hernoemen | mechanisme 52 → `denktank_financiering` | naam |

`doelen` en `grondslag` heb ik niet aangeraakt (alle vier: `opinie`, `niet_officieel`). Bron- en doelrol en aard blijven ook gelijk. Elke motivatie citeert de fragmenten die verdwijnen, omdat de RfC-reviewers de huidige tekst alleen ingekort zien.

### Voorgestelde teksten

**#52 (RfC #111)**
- *description:* "Een belanghebbende (een bedrijf, sector of branche, soms een overheid) financiert een denktank of onderzoeksinstituut, met subsidie, opdrachtonderzoek, giften, partnerschappen of contributie. Langs die geldstroom kan de financier invloed krijgen op welke onderwerpen het instituut onderzoekt, welke vragen het stelt en wat het publiceert."
- *effect:* "Wanneer het mechanisme werkt, sluiten de onderzoeksagenda en de publicaties van het instituut aan bij de belangen van de financier. Die analyses bereiken beleid en media als onderzoek van het instituut, ook wanneer de financiering daarbij niet wordt vermeld."
- *Eruit:* de aangenomen uitkomst ("hun onderzoeksagenda weerspiegelt die belangen"), "Schijnbaar onafhankelijke" en 'argumenten op bestelling'.

**#8 (RfC #112)**
- *description:* "Een denktank, gefinancierd door bedrijven, overheden of andere partijen met een belang bij het beleid waarover zij publiceert, levert een mediaorganisatie analyses, rapporten en commentatoren; de mediaorganisatie presenteert het instituut of zijn medewerkers als deskundige bron. Het mechanisme werkt wanneer daarbij niet wordt vermeld wie de denktank financiert. Het gaat hier om de denktank als instituut dat geciteerd wordt; de financieringsband tussen financier en denktank is mechanisme #52, de individuele deskundige is `expert_legitimatie` (#87)."
- *effect:* "Wanneer het mechanisme werkt, verschijnen de analyses van de denktank in de berichtgeving met het gezag van onderzoek, zonder dat het publiek weet wie het onderzoek financiert. De standpunten die in de berichtgeving als deskundig gelden, blijven dan beperkt tot die van de instituten die de mediaorganisatie benadert, en beleidsvoorstellen die aansluiten bij de belangen van de financiers krijgen de status van deskundig advies."
- *Eruit:* "NAVO-gezinde", HCSS en Clingendael, 'neutraal', 'onafhankelijke', 'argumenten op bestelling', "schijnbaar objectieve", "Schijn van … objectiviteit" en "aureool".

**#87 (RfC #113)**
- *description:* "Een journalist citeert of interviewt een deskundige (bijvoorbeeld een hoogleraar, econoom of onderzoeker) en presenteert hem als autoriteit op het onderwerp. Zijn institutionele inbedding (werkgever, financiers, nevenfuncties) en de aannames achter zijn analyse worden daarbij niet vermeld. Vult `expert_framing` (#8, de denktank als geciteerd instituut) aan op het niveau van de individuele deskundige."
- *effect:* "Wanneer het mechanisme werkt, krijgt wat de opgevoerde deskundigen gemeen hebben in de berichtgeving het gezag van wetenschappelijke kennis, en blijft het debat daartoe beperkt. Deskundigen met een afwijkende analyse komen minder vaak aan het woord, of worden niet als deskundige maar als partij in het debat opgevoerd."
- *Eruit:* 'neutrale', 'de experts', 'querulant', 'activist', "consensus" en "aureool".

**#118 (RfC #114)**
- *description:* "Een denktank brengt eigen, aan het instituut verbonden onderzoekers naar voren als deskundige: zij krijgen functietitels en publiceren onder de naam van het instituut, en treden vervolgens in de media op als gezagsexpert. Dit is de schakel tussen denktank en gezagsexpert in de keten belanghebbende → denktank → gezagsexpert → journalist, naast de institutionele route (`expert_framing`, #8: de denktank zelf als geciteerde bron) en de financieringsband (#52)."
- *effect:* "Wanneer het mechanisme werkt, bereikt de onderzoeksagenda van de denktank, en via de financieringsband (#52) mogelijk die van haar financiers, de journalist via een persoon die als individuele wetenschapper wordt gepresenteerd, zonder vermelding van de denktank of haar financiers. De laatste schakel naar de journalist is `expert_legitimatie` (#87)."
- *Eruit:* 'onafhankelijke', "als neutrale wetenschapper oogt", "belangengebonden agenda" en "fielt en credentialiseert".

**Verwijzing naar #52 via het id.** #8 en #118 noemen de oude naam nu letterlijk. Hun nieuwe tekst verwijst naar "#52", zodat de verwijzing klopt, of de hernoeming (#115) nu wordt aangenomen of niet. Dat volgt de bestaande conventie in #199–#201: "naam (#id)".

**Lexicontoets.** Alle nieuwe teksten (8 theorievelden en 16 argumentvelden) heb ik gecontroleerd met `validation.eigen_stem_treffers`, zowel streng als ruim. Uitkomst: 0 treffers.

### Hernoemen #52 (RfC #115): controle vooraf

- **Is de naam vrij?** `denktank_financiering` bestaat niet in `mechanisms`.
- **Waar staat de oude naam?** `grep -rn denktank_financiering` (zonder `data/`, `.git`, `pm-base`) vindt hem in geen enkel `.py`-, `.js`- of `.html`-bestand, ook niet in de seed-scripts: #52 kwam via een migratie die sindsdien is verwijderd. Hij staat alleen in:
  - `DOCUMENTATIE.md` r. 89 en 157;
  - `releases/model-v0.1.0.json` en `releases/dataset-v0.1.0/relations.csv` (onveranderlijke snapshot);
  - `docs/archief/BACKFILL_REVIEW.md`, missielogs en `onderzoek/…/03_navo-amerika-apparaat.md`;
  - de niet-ingecheckte kopie `pm-base/` (bewust buiten de grep gehouden; ook daar alleen documenten, de snapshot en `web/index.html`).
- **Doel-/grondslagmigratie:** `scripts/migrate_add_doel_grondslag.py` noemt #52 niet bij naam. Een hernoeming verandert dus niets aan een nieuwe run.
- **Tekst in de DB met de oude naam:** de beschrijvingen van mechanisme #8, #118 en #126 en van relatie #469, plus argument #11167 (verworpen).
- **Omvang:** 117 goedgekeurde, 4 voorgestelde en 1 afgewezen relatie dragen mechanisme 52. Alle hebben `influence` = 0,05. Er is één `influence`-argument (#535 op rel. 469, zonder waarde).

## 2. Bronnen (geregistreerd via `POST /api/sources` + `/locations`)

De classificatie is een voorstel en adviserend. Stap 9 van de ronde beslist.

| Bron | Titel | Cluster | Voorstel | Vindplaatsen |
|---|---|---|---|---|
| **#3229** | Farrell, "Corporate funding and ideological polarization about climate change", PNAS 113(1), 2016 | `farrell` | academisch / buitenlands | url PMC4711825, doi 10.1073/pnas.1509433112, archive (Wayback 2026-08-16) |
| **#3230** | Lipton, Williams & Confessore, "Foreign Powers Buy Influence at Think Tanks", NYT 2014-09-06 | `lipton` | kwaliteitsjournalistiek / buitenlands | url nytimes.com (live 403 voor bots), archive Wayback 2014-09-08 |
| **#3231** | Egeland & Pelopidas, "No such thing as a free donation? …", International Relations 39(1), online 2022-12-22 | `egeland` | academisch / algemeen | url HAL-pdf, doi 10.1177/00471178221140000, archive Wayback `id_` (pdf) |
| **#3232** | Gonzalez Hernando & Williams, "Examining the Link Between Funding and Intellectual Interventions …", IJPCS 31(2), 2018 | `gonzalez_hernando` | academisch / algemeen | url White Rose-pdf, doi 10.1007/s10767-018-9281-2, archive Wayback `id_` |
| **#3233** | Freeman, "Defense Contractor Funded Think Tanks Dominate Ukraine Debate" (Quincy Brief No. 41), 2023-06-01 | `freeman` | grijs / buitenlands | url quincyinst.org, archive Wayback 2026-10-11 |
| **#3234** | Rich & Weaver, "Think Tanks in the U.S. Media", Harvard Int. J. Press/Politics 5(4), 2000 | `rich` | academisch / buitenlands | url SAGE (live 403), doi 10.1177/1081180X00005004006, archive Wayback 2024-12-09 |

**Verificatie.** Elk citaat heb ik teruggevonden met `bronchecker.haal_bron` + `bronchecker.zoek_citaat` (alleen ophalen en vergelijken, geen DB, geen model). De meeste citaten staan er letterlijk. De Wayback-weigeringen (HTTP 429) waren tijdelijk: met een pauze ertussen werden ook de NYT-citaten (via archive) en de E&P-citaten (via `id_`) letterlijk gevonden. Een pdf op Wayback zónder `id_` geeft alleen een html-omhulsel van 243 tekens. Daarom staan de pdf-archieflinks in de `id_`-vorm.

## 3. Argumenten (alle `voorgesteld`, citaties `verbatim_quote`)

### Mechanisme 52

- **#11245 (steun, bron #3229).** Farrell (PNAS, 2016): bedrijfsfinanciering beïnvloedt de thematische inhoud van de teksten van 164 organisaties, waaronder denktanks.
  - Citaten: "…corporate funding influences the actual thematic content of these polarization efforts…" en de netwerkzin met "e.g., think tanks".
  - In de redenering staat Farrells eigen selectie-check, zonder oordeel van mij.
- **#11246 (steun, bron #3230).** NYT (2014): sommige buitenlandse regeringen sloten met Washingtonse denktanks "contracts that define the scope and direction of research".
- **#11247 (steun, bron #3231).** Egeland & Pelopidas: "such 'stakeholder funding' has real effects on intellectual freedom". Het onderzoek omvatte 45 denktanks en interviews.
- **#11248 (tegen, bron #3231).** Egeland & Pelopidas: druk om conclusies te veranderen is "by all accounts a relatively rare phenomenon". Financiers bepalen vooral "who gets funded to write or say something in the first place". Dit is de selectie-nuance.
  - Stance: tegen #52 als band tussen één financier en één instituut.
  - De redenering wijst op het steunende argument uit dezelfde bron. Zo plukt dit argument de nuance niet los uit een studie die in hoofdzaak steunt.
- **#11249 (tegen, bron #3232).** Gonzalez Hernando & Williams (theoretisch kader): "it is unlikely for established organisations that face reputational risks to change their 'preferred arguments' too readily". Volgens hen is de argumentatie het minst gevoelig voor financiers.

### Mechanisme 8

- **#11250 (steun, bron #3233).** Quincy Brief nr. 41: NYT, WaPo en WSJ citeerden tussen 1 maart 2022 en 31 januari 2023 in artikelen over Amerikaanse militaire betrokkenheid bij Oekraïne in 85% van de gevallen een denktank met defensiefinanciering, "seven times as often" als denktanks zonder. De citaten zijn de bevinding en twee methodezinnen.
- **#11251 (steun, bron #3233).** Quincy Brief nr. 41: "none of the media mentions analyzed here included disclosures of defense industry funding". Dit is de kern van #8: presenteren zonder de financiers te noemen.
- **#11252 (tegen, bron #3234).** Rich & Weaver (2000): "Disparities in the budget resources of think tanks account for substantial variation in their media visibility". In de redenering staat de omvang-confound bij #11250: grote denktanks krijgen meer geld én meer citaten.

**Waarom Quincy op #8 en niet op #52.** De brief meet hoe media gefinancierde denktanks citeren en of ze de financiering vermelden. Dat is #8. Over financiering en standpunten (#52) zegt de brief zelf: "The findings here show a correlation between funding and publications by think tank scholars, but do not necessarily establish causality."

**Waarom de confound een root is en geen reply.** Een gemergede, open ondergraving onder #11250 houdt de automerge van #11250 tegen (`_open_ondergraving_in_boom`). Stap 11 wijst #11250 dan na 14 dagen af. De confound zou het argument dus wegdrukken in plaats van het te wegen. Als root op #8 telt de confound mee aan de tegenkant. Dat volgt de conventie van de confound-roots in eerdere rondes.

## Queries (letterlijk, met tijdstip; tijden met "ca." zijn op de minuut geschat)

**Database (read-only, sqlite3 `-readonly`), vóór 13:44 (geen exacte tijden vastgelegd) en ca. 14:11**
- `mechanisms` WHERE id IN (8,52,87,118): alle velden.
- `roles` 2/26/28/39/42.
- `mechanism_doelen`, `mechanism_filters` en `mechanism_themes` voor de vier.
- `voorstellen`: de laatste 25, plus herformuleren/hernoemen, met payloads #51/#62/#63 en de reviews.
- Mechanismen met naam LIKE 'denktank%' / '%financiering%'.
- Teksten (mechanisms/roles/arguments/relations/entities/emergent_effects) LIKE '%denktank_financiering_bias%'.
- Root-argumenten op de vier mechanismen, met hun citaties en bronnen.
- Bronnen LIKE think tank/Farrell/Quincy/Lipton/Transparify/Brulle, en vindplaatsen LIKE PMC4711825/foreign-powers/how-weapons-firms/responsiblestatecraft.
- Relaties met mechanism_id 52 per status en invloed, en influence-argumenten daarop.
- `cluster_key`-botsingen.
- `users` (assistent).
- Na het indienen: controle van #11245–#11252 en #3229–#3234.

**Code**
- `grep -rn denktank_financiering . --exclude-dir=data,.git,pm-base`
- `grep -n denktank scripts/*.py`

**Web**
- 13:44:49 curl https://pmc.ncbi.nlm.nih.gov/articles/PMC4711825/ (200).
- 13:45:19 curl nytimes.com …foreign-powers-buy-influence-at-think-tanks.html (403). Daarna Wayback-CDX en snapshot 20140908134130 (200).
- ca. 13:46 WebSearch (extended): `think tank funding donors select like-minded think tanks rather than change positions empirical study`
- ca. 13:46 WebFetch https://pac.org/impact/big-donors-compromise-think-tanks
- ca. 13:47 WebSearch: `"unlikely to provide initial or continued support to organizations or analysts whose views are antithetical"`
- ca. 13:47 WebSearch: `think tanks donors "which questions are asked" "who gets funded" nuclear funding study`
- ca. 13:47 WebSearch (extended): `does funding change think tank positions or do funders choose aligned think tanks causal evidence selection effect "think tanks" paper`
- 13:48:21 Springer 10.1007/s10767-018-9281-2 (bot-challenge). Daarna Crossref-API.
- ca. 13:48 WebSearch: `Gonzalez Hernando Williams 2018 "Examining the Link Between Funding and Intellectual Interventions" pdf`. Daarna de White Rose-pdf (200).
- ca. 13:49 WebSearch (extended): `foreign funding think tank research output text analysis study donor countries mentions favorable evidence`
- ca. 13:50 WebSearch (extended): `"think tanks" funders "ideological" "sorting" OR "self-selection" donors support organizations that already share their views research article`
- 13:50:52 HAL hal-04017574 (bot-challenge).
  - WebFetch SAGE full text (403).
  - Crossref- en Unpaywall-API voor 10.1177/00471178221140000.
  - Wayback-CDX; pdf-snapshot 20260112083344 (200).
- ca. 13:51 WebSearch: `Chaves Stephens Galaskiewicz 2004 "Does Government Funding Suppress Nonprofits' Political Activity" abstract`
- ca. 13:51 WebSearch (extended): `think tanks government funding independence empirical "no evidence" funding influences policy recommendations study Europe`
- 13:53:03 curl responsiblestatecraft.org/2023/06/01/how-weapons-firms-influence-the-ukraine-debate (200).
- 13:54:21 curl quincyinst.org/research/defense-contractor-funded-think-tanks-dominate-ukraine-debate/ (200).
- ca. 13:55 WebSearch: `Rich Weaver 2000 "Think Tanks in the U.S. Media" budget media visibility Harvard International Journal of Press/Politics abstract`
  - Crossref-zoekopdracht.
  - Wayback-CDX SAGE; snapshot 20241209172020 (200; SAGE live 403).
- ca. 14:00–14:05 Wayback-CDX voor archieflinks (PMC, Quincy, White Rose, Quincy-pdf). Daarna verificatie met `bronchecker.haal_bron` (enkele 429's, opnieuw geprobeerd).

## Negatieve resultaten en wat niet is ingediend

- **Geen empirische studie gevonden** die voor denktanks aantoont dat financiering alléén bestaande standpunten volgt (pure selectie), of dat financiering en output niet samenhangen. Gezocht via de zes WebSearch-zoekopdrachten hierboven, de bronnen die daaruit volgden, en Crossref.
  - Het dichtst bij komen #11248 (selectie als hoofdroute, maar dezelfde studie vindt ook censuur en zelfcensuur) en #11249 (theoretisch).
- **Chaves, Stephens & Galaskiewicz 2004** (ASR 69(2)): overheidsfinanciering onderdrukt de politieke activiteit van nonprofits niet ("positive or null"). Niet ingediend: het gaat over congregaties en nonprofits in Minneapolis–St. Paul, niet over denktanks of onderzoeksoutput. De bronchecker (v3, specificiteit) en de aanklager zouden het terecht als niet-passend aanmerken.
- **NYT-artikel, reactie van de denktanks:** "saying the money never compromised the integrity of their organizations' research. Where their scholars' views overlapped with those of donors, they said, was coincidence." Letterlijk teruggevonden, niet ingediend. Het is een zelfverklaring van de betrokken partijen, geen literatuur, en komt uit dezelfde bron als #11246. De literatuur-nuance (#11248, #11249) dekt de tegenkant.
- **Public Affairs Council 2017**, "Do Big Donors Compromise Think Tanks?": meningen van een lobbyvereniging, geen onderzoek. Niet ingediend.
- **Gonzalez Hernando & Williams verwijzen naar Albert 2003 en Behrens & Gray 2001:** "funding shifts do not significantly affect actual research practices". Niet opgehaald of geverifieerd. Het gaat over universiteiten. Mogelijke vervolgbron.
- **Quincy, eigen causaliteitsvoorbehoud (over #52):** niet apart ingediend, omdat Quincy alleen op #8 staat.

## Stance-balans van de ronde

- #52: 3 steun / 2 tegen / 0 context.
- #8: 2 steun / 1 tegen / 0 context.
- Totaal: 5 steun / 3 tegen / 0 context.

## Werkwijze-incident

Een andere sessie gebruikte dezelfde scratchpad-map en overschreef om 14:10:11 mijn `indienen.py` met een eigen Clingendael-script. Mijn aanroep `--stap args` startte daardoor dat script. Het stopte in droogloop meteen met een KeyError en postte niets. Mijn RfC- en bronstappen waren al klaar, en hun uitkomstbestanden zijn intact. De argumentstap heb ik opnieuw opgebouwd in een eigen submap en daarna ingediend.

## Vervolg (niet uitgevoerd)

- **Beslissen over RfC #111–#115.** Dat doet de uurronde (rfc-toetser + rfc-criticus, stap 8). De ronde neemt de oudste open voorstellen eerst, hooguit 3 per keer.
- **Na aanname van #115:**
  - `DOCUMENTATIE.md` r. 89 en 157 bijwerken (documentatie- en codewerk).
  - De beschrijvingen van mechanisme #126 en relatie #469 noemen de oude naam nog als tekst.
    - #126 bevat daarnaast 'schijnbaar objectieve' en "aureool van neutraliteit": kandidaat voor een eigen herformuleren-RfC.
    - #469 zegt in eigen stem "Financier stuurt de agenda": kandidaat voor de stemtoets/stap 10b of een maintainer-PATCH.
- **Seed-scripts** zetten bij een verse build de oude tekst van #8 terug: `scripts/seed_theoretical_model.py:123` ("NAVO-gezinde denktanks (HCSS, Clingendael) worden als 'neutraal' opgevoerd") en `scripts/seed_from_ai_source.py:514`. Codewerk.
- **Dezelfde soort taal elders:**
  - rol #28 `denktank` ("schijnbaar objectieve analyses … elite-belangen");
  - rol #42 `gezagsexpert` ("als 'onafhankelijke' autoriteit … de consensus naturaliseert");
  - mechanisme #180 `ngo_financiering_bias` (dezelfde naamkwestie);
  - de gemergede theorie-argumenten #396 ("schijnbaar objectieve", 'argumenten op bestelling') en #3441 ("vermomd als objectiviteit") op #8. De stemtoets slaat theorie-argumenten over, dus deze vergen een revisie.
