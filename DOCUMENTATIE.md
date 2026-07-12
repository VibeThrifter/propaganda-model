# Propagandamodel Nederlandse Politiek & Media

## Doel

Dit project modelleert de structurele mechanismen waarmee nieuws in Nederland wordt gefilterd en gevormd voordat het het publiek bereikt. Het is gebaseerd op het propagandamodel van Herman & Chomsky (*Manufacturing Consent*, 1988), toegepast op de Nederlandse context met behulp van het werk van Tabe Bergman, Joris Luyendijk, Kees van der Pijl en anderen.

Het model is geen complottheorie. Het beschrijft hoe structurele krachten — eigendom, economische druk, bronafhankelijkheid, disciplinering en ideologie — leiden tot een systematische pro-elite bias als *emergente eigenschap* van het systeem, zonder dat er sprake hoeft te zijn van centrale sturing.

Dat sluit *bewezen* doelgerichte coördinatie niet uit. Binnen een emergent systeem kunnen wel degelijk concrete, gecoördineerde ingrepen zitten — staatscontentmoderatie via trusted-flagger-status, het werven van journalisten door inlichtingendiensten — en die horen er als zodanig in, mits **gedocumenteerd**. De scheidslijn is daarom niet *emergent vs. complot* maar **bewezen vs. speculatief**: emergente bias én aantoonbare sturing horen erin; ongefundeerde aannames van centrale sturing niet. Concreet vertaalt zich dat in de `certainty`-score (een speculatief verband zakt, een gedocumenteerd verband stijgt) — niet in het weglaten van een filter.

---

## Architectuur: twee lagen

Het systeem onderscheidt twee lagen:

### Laag 1: Theoretisch model (abstract, zonder namen)

Beschrijft de structuur: welke **rollen** bestaan er in het medialandschap en via welke **mechanismen** oefenen ze invloed uit?

- **Rollen** — abstracte functies die actoren kunnen vervullen (bijv. `mediaeigenaar`, `adverteerder`, `hoofdredacteur`)
- **Mechanismen** — processen waarmee de ene rol de andere beïnvloedt (bijv. `pakketjournalistiek`, `etikettering`, `zelfcensuur`)

Elk mechanisme draagt **een of meer** van de vijf filters van het propagandamodel (een mechanisme kan meerdere filters tegelijk aandrijven — de draaideur van een politicus naar het bedrijfsleven is bijvoorbeeld winstbelang = Eigendom, naar een hoofdredacteur is Ideologie), plus de uitbreiding `tegenmacht` (krachten die het systeem begrenzen). Daarnaast kennen mechanismen optioneel een of meer **thema's** (dwarsverbanden) — zie [Thema's: dwarsverbanden](#themas-dwarsverbanden).

### Laag 2: Instantiemodel (concreet, met namen)

De echte entiteiten en relaties in Nederland:

- **Entiteiten** — concrete actoren met naam en toenaam (bijv. DPG Media, Thomas Leysen, Bilderberg Groep)
- **Relaties** — concrete verbanden tussen entiteiten (bijv. DPG Media bezit de Volkskrant)

Elke entiteit is gekoppeld aan een of meer rollen uit het theoretisch model. Elke relatie is optioneel gekoppeld aan een mechanisme.

#### Afgeleide primaire rol (emergent, niet toegekend)

In de geest van het model — bias is een *emergente* eigenschap — wordt de **primaire rol/filter van een entiteit afgeleid, niet toegekend**. Per filter telt `scoring.py` de som van *afgeleide zekerheid × afgeleide invloed* over de relaties **waarvan de entiteit de bron is** (het filter dat ze zélf uitoefent; bij een bidirectionele relatie tellen beide kanten). Het filter met de grootste som is de primaire rol (`compute_all_scores` → `entity_primary_filter`/`entity_filter_scores`). Zo classificeert het bewijs een actor, niet de invoerder: PAX komt bijvoorbeeld als `sourcing` (geco-opteerde bron) bovendrijven zodra haar media-relaties de tegenmacht-relatie overstemmen.

De kolom `entities.primary_role_id` is daarmee nog slechts **fallback/override**: ze geldt alleen voor entiteiten zonder (goedgekeurde) bron-relatie, en `influence.py` gebruikt haar nog om doelgroepen (`publiek`, `politicus`) te vinden. De viz en `/api/scores` kleuren/categoriseren op de afgeleide rol (`filter_category`, met `filter_category_bron` = `afgeleid`/`toegekend`/`geen`). Anders dan in de invloedsgraaf telt tegenmacht hier op *magnitude* mee (positief): classificatie meet welke functie een actor het sterkst vervult, niet de netto-duw op het systeem.

---

## De vijf filters + uitbreidingen

Elk mechanisme draagt **één of meer** filters (multi-filter, in `mechanism_filters`; het primaire filter staat in `mechanisms.filter` en bepaalt de kleur); elke rol hoort bij één categorie. Naast de vijf klassieke filters van Herman & Chomsky kent het model twee uitbreidingen die het hedendaagse Nederlandse landschap vangen: **tegenmacht** (krachten die het filtersysteem begrenzen of doorbreken) en **systeemactoren** (structurele spelers die in alle filters tegelijk opereren). De oude noodcategorie `cross_filter` is vervangen: wat "meerdere filters tegelijk" was, draagt nu gewoon die meerdere filters, en de herkenbare families (draaideur, elite-netwerk, geldstromen, …) zijn ondergebracht in een aparte **thema-as** (zie hieronder).

### Filter 1: Eigendom
De eigendomsstructuur bepaalt de institutionele context van nieuwsproductie. In Nederland bestaat een duopolie: DPG Media en Mediahuis bezitten samen >90% van de online commerciële nieuwsmarkt. De eigenaren (families Van Thillo, Leysen, Baert, Van Puijenbroek) behoren tot de transnationale kapitaalklasse.

Cruciaal voor de Nederlandse context: eigendom is hier **familie- en stichtingsgecontroleerd via een getrapte keten**, niet beursgenoteerd met verspreide/institutionele aandeelhouders. Het Angelsaksische beeld uit het oorspronkelijke propagandamodel (beursfondsen, BlackRock op het aandeelhoudersregister van de krant) is hier het *historische/buitenlandse randgeval*: TMG was beursgenoteerd tot Mediahuis het in 2017 van de beurs haalde, en RTL Group/Sanoma noteren bóven een buitenlandse holding. Verspreid beursaandeelhouderschap van een Nederlandse titel is daarom geen apart mechanisme in dit model.

Het eigendom wordt zelden direct uitgeoefend maar via een getrapte keten: de uiteindelijke eigenaar/UBO (`mediaeigenaar`, bv. familie Van Thillo) controleert een **Stichting Administratiekantoor (STAK)** (`administratiekantoor`), die via `familiezeggenschap` de zeggenschap concentreert en via `certificaatconstructie` de aandelen van het `overnamevehikel` (holding: Epifin, Mediahuis Partners, VP Exploitatie) certificeert — zeggenschap wordt zo gescheiden van economisch belang en de uiteindelijke eigenaren blijven buiten beeld. De holding bezit vervolgens de mediaorganisatie (`holdingconstructie`). De STAK is daarbij een controle-**versterker**, geen demper: eigenaarsinvloed is niet "distaal = zwak" — een klein (soms verwaterd) economisch belang wordt hoog in de keten omgezet in volledige, overdrachtsbestendige zeggenschap. Invloed loopt principieel *via* de keten (geen directe shortcut van baas naar titel) en dempt per schakel, behalve waar een controlevehikel haar juist concentreert. Daartegenover staat als tegenkracht de **borgingsstichting**: een onafhankelijkheidsstichting met een prioriteitsaandeel of vetorecht die de redactionele koers beschermt (bv. Stichting Democratie en Media, 14,27% + prioriteitsaandeel in DPG; zie *Tegenmacht*, `onafhankelijkheidsborging`).

Dit is de **commerciële controleketen** — één van twee governance-structuren binnen dit filter. Daarnaast staat het **publieke omroepbestel**: niet elke mediaorganisatie heeft een eigenaar/UBO. De zeggenschap over een `ledenomroep` loopt niet via een STAK maar via drie structurele krachten die uit de Mediawet en de WRR-analyse (*Aandacht voor media*, 2024) volgen — afgeleid uit de **literatuur over hoe het bestel werkt**, niet uit de instance-data:

- **Ledeneis** (`ledeneis`, `publiek → ledenomroep`): een omroepvereniging krijgt en behoudt haar erkenning alleen met genoeg betalende leden — 100.000 voor een erkende, 50.000 voor een aspirant-omroep. Het ledental geldt als bewijs van "maatschappelijke binding" en bepaalt mede zendtijd en budgetaandeel; de WRR signaleert dat goed bestuur en kwaliteit dááraan ondergeschikt raken. Het publiek-als-ledenmarkt is zo zelf een filter op het aanbod.
- **Koepelregie** (`intekensturing`, `omroepkoepel → ledenomroep`): de `omroepkoepel` (NPO) kent een vast garantiebudget toe (~50% voor ledenomroepen, 70% voor taakomroepen; art. 2.149/2.150 Mediawet) en verdeelt het resterende programmageld competitief via *intekening* — omroepen pitchen voorstellen die de NPO goedkeurt en op een zender plaatst. De stuurruimte is wettelijk verruimd van 30% naar 50%; de regie verschuift van de verzuilde omroep naar de centrale sturingsorganisatie ("geen thuisnet"). De generieke `bestelsturing` blijft de koepel→**taakomroep**-sturing (NOS/NTR, rol `mediaorganisatie`).
- **Politieke erkenningspoort** (`erkenningverlening`, `gezagsinstituut → ledenomroep`): de minister van OCW beslist per concessieperiode (op advies van NPO, Raad voor Cultuur en CvdM) of een omroep een erkenning krijgt — toegang tot het bestel, publiek geld en een landelijk podium — en kan die onthouden. Naast de benoeming van de NPO-top (`politieke_benoeming_omroeptop`) bepaalt dit welke "stromingen" een landelijk podium krijgen.

De verzuilde identiteit werkt vervolgens op twee niveaus door: intern stuurt ze de eigen redactie (`omroepsignatuur`, zie *Filter 5*), extern levert ze het bestel zijn pluriformiteit (`omroepverzuiling`). Zo ging `ledenomroep` van één losse uitgaande pijl naar een volwaardige knoop (drie inkomende + twee uitgaande mechanismen). De commerciële pers en online-titels hebben géén omroepkoepel — zij lopen via de keten hierboven.

Achter béíde structuren ligt een derde, diffuse laag: het systemische aandeelhouderschap. De `aandeelhouder` is één klasse met twee polen, onderscheiden door het *mechanisme* — niet door een aparte rol (een institutionele belegger ís immers een aandeelhouder). De **passieve** pool (BlackRock, Vanguard, pensioenfondsen) is geen pijl naar één media-eigenaar maar een systemische achtergrond achter de hele kapitaalcluster: via gespreid vermogensbeheer mede-eigenaar van zowel de media-holdings als de corporates die elders adverteren en lobbyen (de `belanghebbende`n). Dat gemeenschappelijke klassebelang bij een stabiel systeem is `systemisch_eigenaarschap` (diffuus, lage influence). De **actieve** pool is de blokhouder/controlerende familie (GBL/Frère, KBC) die via bestuurszetels en stemrecht gericht één onderneming stuurt: `strategische_zeggenschap` (specifiek, hoge influence).

**Rollen:** `mediaeigenaar`, `mediaorganisatie`, `aandeelhouder` (passief-systemisch én actief-strategisch), `overnamevehikel`, `administratiekantoor`, `hoofdredacteur`, `omroepkoepel`, `ledenomroep`
**Mechanismen:** `familiezeggenschap`, `certificaatconstructie`, `holdingconstructie`, `winstmaximalisatie`, `acquisitiestrategie`, `cross_media_eigendom`, `strategische_zeggenschap`, `systemisch_eigenaarschap`, `benoemingspolitiek`, `hoofdredacteur_als_filter`, `podiumverlening`, `redactioneel_budgetcontrole`, `bestelsturing`, `politieke_benoeming_omroeptop`, `ledeneis`, `intekensturing`, `erkenningverlening`, `staatsreclame_exploitatie`

> De eigendomskant kent geen directe `mediaeigenaar → mediaorganisatie`-pijl: de eigenaarsinvloed loopt strikt via de controleketen `mediaeigenaar → administratiekantoor → overnamevehikel → mediaorganisatie`. De eigenaar heeft daarmee **één uitgaande eigendomspijl — naar de STAK** — die alle eigenaar-niveau-mechanismen draagt (`familiezeggenschap`, `acquisitiestrategie`, `cross_media_eigendom`, en de structurele `eigendomsconcentratie`). De STAK certificeert vervolgens de holding (`certificaatconstructie`: vier effecten — stemmacht-concentratie, cash/controle-ontkoppeling, overnamebestendigheid, UBO-afscherming), en de holding bezit de titel en legt het rendementsregime op (`holdingconstructie`, `winstmaximalisatie`). De redactionele hefbomen liggen ná de keten, op org-niveau: de `mediaorganisatie` benoemt de hoofdredacteur (`benoemingspolitiek`) en stelt het redactiebudget vast (`redactioneel_budgetcontrole`, binnen het door de holding opgelegde rendementsregime). De eigenaar raakt de redactionele laag dus **nooit direct** — zijn invloed is volledig gemedieerd via de keten; alleen zijn persoonlijke elite-netwerk (`mediaeigenaar_elite_netwerk`, Eigendom + Ideologie; thema Elite-netwerk) loopt rechtstreeks. De `borgingsstichting` zet zich als tegenmacht precies op het benoemingspunt (`onafhankelijkheidsborging` → hoofdredacteur). De macro-concentratie zelf is een emergent systeemkenmerk — net als bij de halo's en hyperedges codeert de aard-laag dat, niet een thema.

### Filter 2: Advertentie
Media zijn financieel afhankelijk van adverteerders, wat een structurele voorkeur creëert voor content die het consumentistische wereldbeeld bevestigt. De `adverteerder` is geen losse actor maar de **advertentie-hoed van een `belanghebbende`**: dezelfde corporate of sector die elders lobbyt of procedeert, zet hier het advertentiebudget in als drukmiddel (`adverteren_als_belang`). Zie *Systeemactoren* voor de principaal-superklasse die door alle filters heen werkt.

**Rollen:** `adverteerder` (instrument-rol van `belanghebbende`)
**Mechanismen:** `adverteren_als_belang`, `advertentiedruk`, `commerciele_afhankelijkheid`, `supportive_selling_environment`, `stakeholder_capitalism_frame`, `kijkcijferdisciplinering`

> `kijkcijferdisciplinering` is de enige uitgaande pijl van het `publiek` in het model: het per minuut gemeten zapgedrag (NMO-panel) disciplineert de redactie — gasten worden als 'wegzepper' geëvalueerd, onderwerpen op zapgedrag geselecteerd. Het publiek stuurt dus mee, maar alleen langs de dimensie die gemeten en gemonetariseerd wordt (aandacht, niet kwaliteit). Platformonafhankelijk: YouTube-views/view-duration zijn hetzelfde mechanisme.

### Filter 3: Sourcing
Economische druk dwingt redacties tot afhankelijkheid van een beperkt aantal routineuze bronnen: het ANP, de overheid, en door de elite gefinancierde denktanks. Toegang (*access*) is hierbij zelf een schaarse hulpbron: wie aan tafel mag krijgt een podium, wie fundamenteel afwijkt verliest die toegang geruisloos (`toegangsdisciplinering`).

Het **persbureau** (ANP) is binnen dit filter de *industriële versterker*: objectief in HÓE het schrijft (zonder oordeel), maar door tijd, geld, klantvraag en routines structureel selectief in WÁT het schrijft — en het propagandamodel gaat juist over dat WÁT. Drie routines drijven die selectie: leunen op de agenda's van officiële instanties — rechtbank, Kamer, politie, persconferenties (`persbureau_brongebondenheid`); de gebundelde vraag van betalende klant-redacties die de "waan van de dag" opschaalt ten koste van structureel ondervraagde thema's (`klantvraag_persbureau`); en de snelheids-/verifieerbaarheidseis die het officieel-controleerbare bevoordeelt boven trage onderzoeksjournalistiek (`verifieerbaarheidsroutine`). Via `pakketjournalistiek` wordt die selectie vervolgens landelijk uniform doorgegeven. De landschapsbrede uitkomst — veel merknamen, één nieuwsstroom, terwijl het publiek meerstemmigheid ervaart — is gemodelleerd als emergent effect `schijnpluriformiteit` (Boumans, UvA 2016: ca. tweederde van het online nieuws in 2014 ANP-gebaseerd, veelal vrijwel integraal overgenomen). De structurele scheefgroei tussen de zendende en de checkende kant (±150.000 communicatieprofessionals tegenover ±15.000 journalisten; UvA/CBS) is het emergente effect `voorlichtingsovermacht`.

Achter de bronnen zitten **principalen** die de sourcing-stroom voeden via instrumenten — dezelfde logica, twee gedaanten. Corporate: een `belanghebbende` (bedrijf/sector/branche) zet zijn belang om in mediabeeld via lobbyisten, brancheorganisaties en denktanks (`belangenbehartiging`); de soorten lobby verschillen (corporate-sectoraal, branche/koepel, ideologisch/NGO) en goed georganiseerde belangen zijn structureel oververtegenwoordigd. Politiek: de voorlichter heeft altijd een principaal — een **politieke `partij`** (die via `gecoordineerde_voorlichting` één afgestemde boodschap langs de partijlijn levert en via `partijlijn` haar politici aanstuurt) **óf een instituut/ministerie** (`gezagsinstituut`, Rijksvoorlichtingsdienst, departementale woordvoerders, via `institutionele_voorlichting`). De voorlichter en de politicus zijn bewust *aparte* rollen — de toegangs-poortwachter versus de bron — en het smeermiddel is *access*: de off-the-record Nieuwspoort-code "je hebt het niet van mij, maar..." (Luyendijk), die zelfcensuur wekt omdat niemand hem durft te breken.

Naast deze principalen gelden officiële instituties zelf als gezaghebbende routinebron: een `gezagsinstituut` (CPB, DNB, CBS, RIVM, WRR, ministerie, OM) is een **primaire definieerder** (Hall) wiens cijfers en rapporten als neutraal feit gelden en de agenda zetten (`institutioneel_gezag`); de `gezagsexpert` (de "onafhankelijke" hoogleraar/econoom/deskundige) legitimeert de consensus (`expert_legitimatie`).

Een grensgeval tussen Sourcing en Flak is `inlichtingen_cooptatie`: een inlichtingendienst (AIVD/MIVD) werft journalisten als bron of agent. Gedocumenteerd door NRC/de Volkskrant (2024) — van 32 benaderde redacteuren/correspondenten meldde ~de helft een verzoek; een intern AIVD-document noemde 8 journalisten onder 21 "bronnen en agenten". Het compromitteert de onafhankelijkheid van de bronvergaarder (Sourcing) en ondermijnt de geloofwaardigheid van het vak (Flak). Dit is geen emergent veld-effect maar een *bewezen, doelgerichte* ingreep — en hoort daarom expliciet in het model. (Op instantieniveau is bewust nog géén specifieke dienst→journalist-relatie opgenomen: *dát* een dienst journalisten werft is bewezen, *welke* dienst wie benaderde niet — het praktijkmodel wacht op een gedocumenteerd, specifiek geval. Zo kan het theoretische model wél een verband met geheime diensten dragen terwijl de praktijklaag leeg blijft tot het bewijs er is.)

**Rollen:** `persbureau`, `journalist`, `voorlichter`, `lobbyist`, `denktank`, `belanghebbende`, `gezagsinstituut`, `gezagsexpert`
**Mechanismen:** `bron_afhankelijkheid`, `pakketjournalistiek`, `persbureau_brongebondenheid`, `klantvraag_persbureau`, `verifieerbaarheidsroutine`, `expert_framing`, `pr_subsidie`, `toegangsdisciplinering`, `belangenbehartiging`, `gecoordineerde_voorlichting`, `institutionele_voorlichting`, `partijlijn`, `institutioneel_gezag`, `expert_legitimatie`, `journalist_bronrelatie`, `politicus_als_bron`, `voorlichter_informatiefilter`, `lobbyist_naar_journalist`, `lobbyist_naar_politicus`, `denktank_financiering_bias`, `denktank_levert_expert`, `denktank_naar_politiek`, `denktank_naar_persbureau`, `woo_obstructie`, `draaideur_politiek_institutie`, `inlichtingen_cooptatie`, `mediageniekheidsselectie`

### Filter 4: Flak
Disciplineringsmechanismen die journalisten ontmoedigen om van de geaccepteerde lijn af te wijken: juridische dreiging, publieke aanvallen, etikettering, en interne zelfcensuur. De hedendaagse *cancelling* — een gast die iets onwelgevalligs zegt en niet meer wordt uitgenodigd — valt hier onder via `deplatforming`. Het uiterste van het flak-spectrum is fysiek én online `geweld_intimidatie` tegen journalisten; de bron daarvan is bewust diffuus gelaten (geen vaste principaal), passend bij het emergente — niet samenzweerderige — karakter van dát mechanisme. Externe flak en interne redactiecultuur versterken elkaar bovendien in een vicieuze cirkel — empirisch gedocumenteerd door PersVeilig/I&O (2021: 8 op de 10 journalisten ervaart agressie of bedreiging, 16% past de berichtgeving aan, ±15% publiceert soms niet) — gemodelleerd als emergent effect `verkillingsspiraal`: het collectieve chilling effect dat de individuele zelfcensuur-halo overstijgt.

Niet álle flak is echter diffuus: een hedendaagse, *wél* doelgerichte en gedocumenteerde variant is `statelijke_inhoudsmoderatie` — een overheid (bv. het ministerie van BZK met trusted-flagger-status bij vijf platforms) of de Europese Commissie (Code of Practice, EU Internet Forum 'borderline content'-handboek dat o.a. anti-elite en meme-content benoemt) zet techplatforms onder druk om legale maar ongewenste uitingen te modereren of demoten. Anders dan `deplatforming` (één mediagast) werkt dit digitaal en publieksbreed, op platformniveau, en raakt het ook Ideologie (spectrumbewaking). Het is het schoolvoorbeeld van bewezen sturing binnen een verder emergent systeem.

**Rollen:** _(geen — flak is een functie, geen identiteit; de mechanismen werken op bestaande rollen)_
**Mechanismen:** `juridische_dreiging`, `publieke_aanval`, `deplatforming`, `etikettering`, `zelfcensuur`, `geweld_intimidatie`, `statelijke_inhoudsmoderatie`, `statelijke_bronnenjacht`

### Filter 5: Ideologie
Het overkoepelende filter: een denkkader dat als "gezond verstand" wordt gepresenteerd (Gramsci's culturele hegemonie). In de Nederlandse context is die hegemonie een specifieke combinatie — **cultureel links-progressief** (een *politics of recognition*: diversiteit, identiteit) én **economisch neoliberaal**, pro-Atlantisch: wat Nancy Fraser "progressief neoliberalisme" noemt. Elite-fora synchroniseren dit wereldbeeld, en **universiteiten en journalistiekopleidingen** (`kennisinstituut`) reproduceren het als neutrale, wetenschappelijke vanzelfsprekendheid: ze socialiseren de journalisten (`academische_socialisatie`) én leveren de `gezagsexpert`s (`academische_autoriteit`). Doordat journalist én "onafhankelijke" bron uit dezelfde instituten komen, ontstaat **ideologische homofilie** — empirisch zichtbaar in de sterk afwijkende stemvoorkeur van NL-journalisten (D66/GroenLinks fors oververtegenwoordigd t.o.v. de bevolking; parlementair journalisten: D66 27% vs. 9% landelijk, 'Haagse waakhonden') — gemodelleerd als het gelijknamige emergente effect `ideologische_homofilie`. De hegemonie-*reproductie* reikt verder dan de media: het `kennisinstituut` vormt de hele hoogopgeleide elite die álle instituties bevolkt (Bovens & Wille, *diplomademocratie*) — politici (`academische_socialisatie_politiek`), denktanks (`academische_orthodoxie_denktank`), de "primaire definieerders" als CPB/DNB (`academische_orthodoxie_instituut`) en opiniemakers (`academische_vorming_opinie`). Afwijking verschijnt niet als ander standpunt maar als gebrek aan kennis of als "activisme". (De *academisch criticus die het filtersysteem blootlegt* is bewust geen aparte rol: in NL een marginaal, niet-bepalend verschijnsel — de relevante academische kracht is juist hegemonie-*dragend*.)

**Rollen:** `elite_forum`, `columnist_opiniemaker`, `kennisinstituut`
**Mechanismen:** `schijndebat`, `ideologische_synchronisatie`, `elite_referentiekader`, `spectrum_bewaking`, `journalist_socialisatie`, `academische_socialisatie`, `academische_socialisatie_hoofdredacteur`, `preselectie_hoofdredacteur`, `politicus_als_ideoloog`, `columnist_als_hegemon`, `omroepverzuiling`, `omroepsignatuur`, `sociologische_homogeniteit`, `academische_autoriteit`, `academische_socialisatie_politiek`, `academische_orthodoxie_denktank`, `academische_orthodoxie_instituut`, `academische_vorming_opinie`, `publieksfragmentatie`, `conflictregie`

<a id="themas-dwarsverbanden"></a>
### Thema's: dwarsverbanden
Sommige mechanismen vormen herkenbare *families* die dwars door de vijf filters heen lopen — ze laten zich niet onder één filter vangen omdat ze er meerdere tegelijk aandrijven. Vroeger zat dit in de noodcategorie `cross_filter`; nu draagt elk mechanisme gewoon **al** zijn filters (multi-filter), en de families zitten op een aparte, los selecteerbare **thema-as** (`mechanism_themes`, many-to-many — een mechanisme mag in meerdere thema's zitten). Een thema is dus géén filter en géén subgroep: het is een analytische dwarsdoorsnede.

De **draaideur** illustreert het principe: personeel circuleert tussen politiek, bedrijfsleven, media/journalistiek en lobby/PR, en raakt per spaak een ánder filter — politicus → bedrijfsleven is winstbelang (**Eigendom**), → hoofdredactie is **Ideologie**, → lobby/PR is **Sourcing**, → toezicht is **Flak** (regulatory capture). Het thema "Draaideur" houdt die spaken bij elkaar, terwijl de filter-tags het inhoudelijke kanaal benoemen.

De zeven thema's:

- **Draaideur** — circulatie van personeel/macht (politicus → bedrijfsleven/lobby/toezicht/hoofdredactie, journalist ↔ politiek).
- **Elite-netwerk** — synchronisatie van wereldbeeld in elite-fora (Bilderberg/WEF/ERT); combinatie van lobby (Sourcing) en Ideologie. Zeldzaam publiek spoor: de VN-herstelterm "build back better" (Sendai-raamwerk, 2015) werd na WEF- en OESO-publicaties van begin juni 2020 binnen maanden de herstelslogan van meerdere westerse regeringsleiders — gedocumenteerde vocabulaire-convergentie via gedeelde circuits, geen bewijs van regie (zie de argumenten bij `ideologische_synchronisatie`).
- **Geldstromen** — agenda-gebonden geld dat buiten eigendom én advertentie om naar partij of titel stroomt (partij-/mediafinanciering, groeileningen, platformfinanciering), plus de neutrale tegenpool `projectfinanciering_journalistiek`.
- **Platform/digitaal** — techplatforms en algoritmes (filtering, socialisatie, verdienmodeldruk, advertentieconcentratie).
- **Publiek omroepbestel** — de bestel-specifieke krachten (ledeneis, intekensturing, erkenningverlening, omroepsignatuur/-verzuiling, Ster); spant Eigendom + Ideologie + Advertentie.
- **Kennis & expertise** — het expert-/autoriteitscomplex (academische vorming/orthodoxie, denktanks, expert-framing/-legitimatie); spant Sourcing + Ideologie.
- **Benoemingsketen** — de keten waarlangs kapitaal de hoofdredactie bereikt (commissaris- en directiebenoeming, STAK-stemzeggenschap, benoemingspolitiek, voorselectie en de hoofdredacteur als doorgeefluik), met het redactieraad-instemmingsrecht als tegenmacht op precies dat punt; spant Eigendom + Ideologie + Tegenmacht.

> Een thema *Systemisch* bestond eerder, maar was dubbelop: een staande systeemtoestand is al een
> `veld_eigenschap` (halo) en een groepseigenschap een `emergent_effects`-hyperedge — de aard-laag
> codeert systemisch-zijn, een thema-as ernaast voegt niets toe (zie `migrate_thema_opschoning.py`).

### Uitbreiding B: Tegenmacht — een gerichte valentie, geen universele categorie
Het model is niet deterministisch: het modelleert óók de krachten die het filtersysteem begrenzen of doorbreken. Maar "tegenmacht" is **geen eigenschap van een actor** en zelfs niet van een losse edge zonder meer: het is een **tweeplaatsig predicaat**, `tegenmacht(X, doel)`. In een veld van meerdere machtsblokken dient het tegenwerken van het ene blok vaak het andere; dezelfde actor kan dus tegenmacht zijn op de ene as en promacht op de andere. Een universeel "tegenmacht"-stempel (op een knoop, of als kleur van een entiteit) is daarom een categoriefout — de valentie hangt altijd aan een **edge relatief aan een benoemd doel** (zie [Deel B: machtsvalentie](#machtsvalentie--tegenmacht-als-edge-valentie)).

Het model onderscheidt twee soorten "tegen" die niet op één hoop mogen:

1. **Verantwoording** — tegenwicht tegen een *filter-machtsconcentratie* (de borgingsstichting tegen eigendomsconcentratie, de toezichthouder tegen holdingconcentratie, de vakbond/NVJ tegen flak). Dit zijn de institutionele accountability-mechanismen hieronder. Ze delen één doel — de verantwoording van geconcentreerde mediamacht — en ontlenen daaraan hun samenhang. Ze zijn dubbel: parlementaire controle *checkt* macht én *legitimeert* de institutionele orde (consensusvloer-versterking).
2. **Contra-hegemonie** — een kracht die de grens van de **consensussfeer** verschuift: die een onderwerp van de sfeer van consensus naar die van legitieme controverse duwt. Dit is *niet* hetzelfde als verantwoording, en het is *niet* aan een actor te binden: een insurgente beweging kan contra-hegemoniaal zijn op de establishment-as en tegelijk reactionair/elite-gesteund op de economische as. Contra-hegemonie wordt daarom geclassificeerd als **edge-valentie per as**, niet als filter of actor-kleur.

**Hallins drie sferen als referentiekader.** De multipolariteit die het emergente veld `consensuscalibratie` codeert (de mate van consensus tussen meerdere machtsblokken als regelknop op de filters) valt samen met Hallins drie sferen (*The Uncensored War*, 1986): de **sfeer van consensus** (alle blokken eens → filters strak, fabricage van instemming totaal — dit ís de regelknop van `consensuscalibratie`), de **sfeer van legitieme controverse** (concurrerende elite-facties, vooral op de culturele as → begrensde pluriformiteit, `schijnpluriformiteit`) en de **sfeer van deviantie** (uitdagingen aan de vloer zelf + de structureel uitgesloten onderkant → marginalisering, flak-terrein). Het model gaat dus **niet** uit van één monolithische elite: de emergente pro-elite bias is het sterkst op de *overlap* van de blokken (de vloer) en zwak/pluralistisch op de *betwiste* as. Tegenmacht in de contra-hegemonische zin = een kracht die die grens verschuift.

De mechanismen hieronder houden `filter='tegenmacht'` — die filter-waarde markeert nu expliciet **soort 1 (verantwoording)**. Factie-insurgentie (bv. een partij die de institutionele legitimiteit betwist) krijgt géén `tegenmacht`-filter: ze wordt gemodelleerd als wat ze is (flak-/ideologie-edges tussen blokken), plus — waar ze de vloer zelf betwist — een `machtsvalentie`-annotatie op de betreffende as.

**Rollen:** `onderzoeksjournalist`, `klokkenluider`, `parlementair_controleur`, `toezichthouder`, `vakbond_media`, `burgerinitiatief`, `borgingsstichting`, `alternatief_medium`
**Mechanismen:** `onderzoeksjournalist_doorbraak`, `klokkenluider_doorbraak`, `onafhankelijk_medium_tegenwicht`, `parlementaire_controle`, `toezichthouder_interventie`, `toezicht_tandeloosheid`, `vakbond_bescherming`, `burgerinitiatief_druk`, `onafhankelijkheidsborging`, `redactiestatuut_borging`, `continuiteitsborging`, `afgedwongen_borging`, `projectfinanciering_journalistiek`

#### Machtsvalentie — tegenmacht als edge-valentie
De contra-hegemonische valentie leeft — net als de politieke kleurmeter — in **gesourcete, betwistbare** `arguments` met `property='machtsvalentie'` op een **relatie of mechanisme** (een edge), en is een **aspect**: het telt in niets mee (`ASPECT_PROPERTIES` sluit het uit van de zekerheidsbalans) en voedt geen score — een classificatie-/overlay-laag, zoals de kleurmeter. Twee vormen van `property_value`:

- `filter:<eigendom|advertentie|sourcing|flak|ideologie>` — **verantwoording**: deze edge checkt die filter-machtsconcentratie.
- `as:<economisch|cultureel|establishment>:<opent|sluit>` — **contra-hegemonie**: `opent` duwt het onderwerp van consensus → legitieme controverse (contra-hegemoniaal), `sluit` verstrakt de consensus (pro-hegemoniaal). Eén edge draagt max. één annotatie per as.

`tegenmacht.py` leidt hieruit per actor (de bron-entiteit van de relatie) een valentie-per-as af — `Σ(gewicht·teken)/(Σgewicht+K)`, zelfde weging als de kleurmeter — plus welke filter-concentraties ze verantwoordt; bereikbaar via `GET /api/machtsvalentie` (`?preview=1` telt nog-`voorgesteld` annotaties voorlopig mee). Zo toont de viz *"FvD: opent op establishment, neutraal/sluit op economisch"* in plaats van één misleidende `tegenmacht`-kleur. Een platform is tegelijk consensusvloer-versterkend (eigendom/advertentie) én betwiste-as-versterkend (engagement blaast factie-insurgentie op) — alleen per-as-valentie kan dat zonder tegenspraak naast elkaar zetten.

De `borgingsstichting` (onafhankelijkheidsstichting met prioriteitsaandeel/vetorecht, bv. Stichting Democratie en Media bij DPG) is de tegenpool van het STAK-controlevehikel uit Filter 1: ze biedt een structurele rem op eigenaarsinvloed, maar geen ijzeren garantie (een minderheidsbelang naast de winstgedreven meerderheid). Ze grijpt aan op beide eigenaarshefbomen op de inhoud: de benoeming van de hoofdredacteur (`onafhankelijkheidsborging`, tegenpool van `benoemingspolitiek`) én — via het redactiestatuut — de onafhankelijkheid van de hele redactie (`redactiestatuut_borging`, tegenpool van `redactioneel_budgetcontrole`), én de continuïteit van de titel zelf (`continuiteitsborging`, veto op verkoop/opheffing). Naast die zeggenschapsrol is ze ook **financier**: uit haar beleggingsrendement (niet uit het dividendloze DPG-belang) betaalt ze onderzoeksjournalistiek die het rendementsregime anders wegbezuinigt (`projectfinanciering_journalistiek`, tegenpool van `redactioneel_budgetcontrole`; ook dedicated persfondsen als SVDJ/FBJP/Journalismfund vervullen deze rol). De `toezichthouder` (ACM/CvdM) reguleert intussen niet de eigenaar-als-persoon maar de **concentratie/overname** op het holdingniveau (`toezichthouder_interventie`/`toezicht_tandeloosheid` → `overnamevehikel`); een ACM-interventie kan zo'n borgingsstichting zelfs afdwingen als overnamevoorwaarde (`afgedwongen_borging`, DPG-RTL-voorwaarden).

### Systeemactoren
Structurele spelers die in meerdere filters tegelijk opereren en daarom een eigen rolcategorie vormen (zij vervullen geen eigen filter maar voeden er meerdere).

De belangrijkste hiervan is de `belanghebbende`: georganiseerd privaat/elite-belang (bedrijf, sector, branche, overheidsorgaan, ideologische beweging) dat als **principaal-superklasse** door álle vijf filters projecteert — één actor, meerdere hoeden. De vijf filters zijn *kanalen* van invloed; achter meerdere kanalen staat dezelfde principaal. Het model tekent telkens de *eerste schakel* (de principaal raakt de media nooit direct, hij zet een instrument in); de vervolgschakel naar de redactie is een apart mechanisme binnen dat filter:

- **Eigendom (F1):** als eigenaar/holding zelf (`mediaeigenaar`), met de `aandeelhouder` als systemische achtergrond (`systemisch_eigenaarschap`) of actieve blokhouder (`strategische_zeggenschap`) achter de hele kapitaalcluster.
- **Advertentie (F2):** als `adverteerder`, het advertentiebudget als drukmiddel (`adverteren_als_belang`).
- **Sourcing (F3):** via ingehuurde `lobbyist`/brancheorganisatie (`belangenbehartiging`) en via gefinancierde `denktank`s (`denktank_financiering_bias`).
- **Flak (F4):** via juridische dreiging/SLAPP tegen kritische journalisten (`juridische_dreiging`).
- **Ideologie (F5):** via deelname aan elite-fora die het wereldbeeld synchroniseren (`belang_elite_netwerk`, naast `mediaeigenaar_elite_netwerk` en `politicus_elite_netwerk`).
- **Politiek (thema Geldstromen, filter Eigendom/winstbelang + Sourcing):** via rechtstreekse partijfinanciering — giften/donaties aan een politieke partij zónder lobbyist ertussen (`partijfinanciering`), naast de instrument-route via de `lobbyist`.
- **Media (thema Geldstromen, filter Eigendom + Ideologie):** via rechtstreekse mediafinanciering — giften/project- of programmasubsidies aan een titel, buiten eigendom en advertentie om (`externe_mediafinanciering`). De neutrale tegenpool (persfondsen die onderzoek mogelijk maken) staat onder *Tegenmacht* (`projectfinanciering_journalistiek`). Twee zware varianten van dezelfde geldstroom-naar-media: **publieke/supranationale groeileningen** van een instelling als de EIB (`publieke_groeifinanciering`, raakt F1-consolidatie + F2-data + F5-alignment) en **Big Tech die de pers terugfinanciert** die het zelf ondermijnde (`platform_journalistiekfinanciering`, co-optatie).

De superklasse wordt bewust *niet* opgesplitst in subtypes (bedrijf vs. lobby vs. beweging): dat onderscheid zit al in de *instrument-hoed* (adverteerder/lobbyist/denktank) en zou dupliceren. Wél kent een belanghebbende een onafhankelijke **aard**-as die zichtbaar maakt wélk soort belang het is, af te lezen aan het filterprofiel: *commercieel* (bedrijf — F1-eigendom + F2-advertentie, zit zélf in de kapitaalcluster), *sectoraal* (branche/koepel — vooral F3-lobby) of *ideologisch* (waardengedreven beweging — vooral F5/F3). De doorslaggevende scheidslijn is niet de rechtsvorm maar de **machtsalignering**: de `belanghebbende` is per definitie elite-/kapitaal-aligned. Diffuse, niet-elite tegenkrachten met dezelfde vorm (een vakbond, een burgerbeweging) horen daarom *niet* hier maar onder *Tegenmacht* (`vakbond_media`, `burgerinitiatief`) — anders verdwijnt precies het pro-elite-onderscheid dat de hele theorie draagt.

Zo vangt de `belanghebbende` de elite-/kapitaalkant die voorheen versplinterd over de losse filters lag. De politieke tegenhanger is de `partij` als coördinerende principaal (zie Filter 3, `gecoordineerde_voorlichting`): dezelfde sourcing-logica, een andere principaal.

**Rollen:** `politicus`, `publiek`, `redactie`, `techplatform`, `belanghebbende`, `partij`

---

## Databaseschema

### Overzicht tabellen

```
THEORETISCH MODEL          INSTANTIEMODEL              BEWIJS
┌──────────┐               ┌──────────┐                ┌──────────┐
│  roles   │◄─────────────►│ entities │                │ sources  │
└────┬─────┘  instantiations├──────────┤                ├──────────┤
     │        (+exemplariteit│entity_   │                │source_   │
┌────┴─────┐               │roles     │                │locations │
│mechanisms│◄─────────────►┤          │                └────┬─────┘
└────┬─────┘  instantiations└────┬─────┘                     │
     │        (+exemplariteit)    │                           │
     │  ▲ literatuur-      ┌─────┴─────┐               ┌────┴─────┐
     │  │ argumenten       │ relations │──────────────►│arguments │
     └──┴──────────────────┴───────────┘               ├──────────┤
        arguments.role_id/   certainty                 │citations │
        mechanism_id         influence                 └──────────┘

De afgeleide scores stromen omhoog: discussieboom → praktijkscore per relatie/entiteit
→ aggregatie (via instantiations) + literatuuronderbouwing → theoriescore per rol/mechanisme.
Zie "Scores: van discussieboom naar theorie".
```

### Theoretisch model

| Tabel | Beschrijving | Velden |
|---|---|---|
| `roles` | Abstracte rollen in het medialandschap | name, category (`eigendom`/`advertentie`/`sourcing`/`flak`/`ideologie`/`systeemactor`/`tegenmacht`/`overig`), description, examples, active_from/active_until (temporeel) |
| `mechanisms` | Processen waarmee rollen invloed uitoefenen | name, filter (primair filter; vijf filters + `tegenmacht`/`overig`), mechanism_type (`structureel`/`procedureel`/`psychologisch`/`economisch`/`juridisch`/`technologisch`/`discursief`), **aard** (`direct`/`veld_eigenschap` live; `indirect`/`veld_instantiatie` deprecated — zie [Aard: direct & systemisch](#aard-direct--systemisch)), description, effect, source_role_id, target_role_id, active_from/active_until (temporeel) |
| `mechanism_filters` | Multi-filter: alle filter-tags per mechanisme (≥1, incl. primair) | mechanism_id, filter |
| `mechanism_themes` | Thema-as: dwarsverbanden per mechanisme (0+) | mechanism_id, theme (`draaideur`/`elite_netwerk`/`geldstromen`/`platform`/`omroepbestel`/`kennis_expertise`/`benoemingsketen`; `systemisch` deprecated/leeg — aard-laag codeert dat) |
| `emergent_effects` | Emergent effect als **hyperedge**: systeemeigenschap uit het samenspel van een gróép rollen (geen bron→doel-pijl). Eersteklas theorie-element: eigen discussieboom (`arguments.emergent_effect_id`), eigen tijdvenster en eigen score (lit-only) | name, label, category, description, effect, active_from/active_until (temporeel) |
| `emergent_effect_members` | Koppeltabel: welke rollen dragen samen een emergent effect | emergent_effect_id, role_id |
| `emergent_effect_subeffects` | Tweede-orde-structuur: deel-effecten van een emergent effect. Gebruikt voor het apex-veld `fabricage_van_instemming` ⊃ de elf overige velden; de ledenset van het apex-veld blijft pars pro toto | parent_effect_id, child_effect_id |

> **Tijdsdimensie.** Ook de theorielaag is historisch contingent: mechanismen ontstaan (kijkcijferdisciplinering vereist een kijkmeterpanel — 1987; algoritmische_filtering een algoritmische feed — 2006) en kunnen verdwijnen. `roles`, `mechanisms` en `emergent_effects` dragen daarom dezelfde optionele `active_from`/`active_until` als de praktijklaag; NULL = onbegrensd voor zover bekend. Alleen invullen bij evident technologie- of bestelgebonden elementen — zie `scripts/migrate_tijdsdimensie_theorielaag.py` voor de zes gedateerde mechanismen plus rationale. De **tijdbalk** in de visualisatie werkt in beide modellen: op het gekozen jaar verdwijnen mechanismen, rollen en emergente velden (en in het praktijkmodel relaties/entiteiten) die toen niet actief waren; de stand "Alle jaren" toont alles. De looptijd is per mechanisme en rol bespreekbaar in het detailpaneel (via de discussieboom, net als bij relaties). `scoring.py` en `influence.py` blijven tijdloos: bewijs telt ongeacht datum even zwaar; tijdsweging van argumenten (ouder bewijs telt lichter) is een bewust uitgestelde, aparte modelkeuze.

### Instantiemodel

| Tabel | Beschrijving | Velden |
|---|---|---|
| `entities` | Concrete actoren (personen, organisaties, partijen) | name, type, primary_role_id, description, metadata (JSON), active_from/active_until/active (temporeel) |
| `entity_roles` | Koppeltabel: entiteit kan meerdere rollen vervullen | entity_id, role_id, notes |
| `relations` | Concrete relaties tussen entiteiten | source_id, target_id, relation_type, mechanism_id, description, certainty, influence, bidirectional, active_from/active_until/active (temporeel) |
| `instantiations` | Expliciete klasse↔instantie-koppeling: rol↔entiteit of mechanisme↔relatie, met **exemplariteit** (hoe prototypisch is dit voorbeeld). Basis voor de bottom-up aggregatie. | role_id/mechanism_id (de klasse), entity_id/relation_id (de instantie), exemplarity (0–1), notes |
| `source_mentions` | Welke entiteiten worden in welke bronnen genoemd | source_id, entity_id, context |

### Bronnen (academisch)

| Tabel | Beschrijving | Velden |
|---|---|---|
| `sources` | Academische bronnen (boeken, artikelen, rapporten) | title, author, source_type, publisher, date_published, language, summary, reliability (rigueur: `primair`/`academisch`/`institutioneel`/…), onderwerp (relevantie-as: `nl_systeem`/`algemeen`/`buitenlands`/`onbepaald`), processed |
| `source_locations` | Meerdere toegangspunten per bron | source_id, location_type (url/file/doi/isbn/arxiv/handle/archive_url), location, accessed_at, notes |

### Argumenten & citaties (discussieboom)

| Tabel | Beschrijving | Velden |
|---|---|---|
| `arguments` | Discussieboom: argumenten op een praktijk-target (relatie/entiteit) óf een theorie-target (rol/mechanisme/emergent veld = literatuuronderbouwing), met nesting | relation_id / entity_id / role_id / mechanism_id / emergent_effect_id (minstens één), parent_argument_id (NULL=root), property/property_value (optioneel), stance, claim, reasoning, weight, status (via de API landt alles als `voorgesteld` (M2.2); verder `ongecontroleerd`/`bronvermelding_nodig`/`betwist`/`geverifieerd`/`verouderd`/`verworpen`), self_merged (vlag: inbrenger mergede eigen voorstel), merged_by, contributed_by (FK naar users, M2.1) |
| `citations` | Bronvermeldingen per argument | argument_id, source_id, quote, page, section, context |
| `edit_log` | Auditlog van wijzigingen (aanmaak, status, merge) | table_name, record_id, action (`created`/`updated`/`deleted`/`verified`/`disputed`/`merged`), changed_by (FK naar users), old_value, new_value, reason |
| `users` | Identiteit voor het bijdragepad (M0.6): mensen én agents | username, kind (`mens`/`agent`), role (`bijdrager`/`reviewer`/`maintainer`), password_hash (alleen mensen), token_hash (sha256; token zelf wordt nooit opgeslagen), provenance (verplicht voor agents: model+versie), active, last_login_at |
| `user_filter_rollen` | M2.1: reviewer/maintainer per filter, bovenop de globale rol | user_id, filter, rol |
| `voorstellen` + `voorstel_reviews` | M2.3/M2.6: theory-RfC's en splitsen/samenvoegen/hernoemen; theorielaag vergt 2 menselijke akkoorden | soort, titel, payload (JSON-sjabloon), status (`open`/`geaccepteerd`/`afgewezen`/`ingetrokken`), ingediend_door, resultaat; reviews: reviewer, oordeel, motivatie |
| `argument_ratings` | M2.5: oordelen óver argumenten (nooit over waarheid); agent-ratings = advies | argument_id, rater, oordeel (`nuttig`/`niet_nuttig`), reden (gestructureerd), motivatie; UNIQUE per (argument, rater) |
| `watchlists` | M2.4: volglijsten op de recent-changes-feed | user_id, table_name, record_id |
| `lineage` | M2.6: opvolging bij splitsen/samenvoegen/hernoemen — niets wissen | soort, element_type, oud_id, nieuw_id, voorstel_id, reden |
| `predictions` | M3.4: voorspellingsregister — toetsbare verwachtingen, vastgelegd vóór de uitkomst | claim, afleiding, meetcriterium, kans (0–1 exclusief), deadline (toekomst), theorie-anker (mechanism_id/role_id/emergent_effect_id, ≥1), status (`open`/`uitgekomen`/`niet_uitgekomen`/`onbeslisbaar`), uitkomst, brier, self_scored, contributed_by, beoordeeld_door |

Argumenten vormen een boomstructuur:
- **Root-argumenten** (`parent_argument_id = NULL`) hangen direct aan een relatie of entiteit
- **Reacties** (`parent_argument_id = <id>`) reageren op een ander argument
- Elk argument kan gericht zijn op een **relatie** (`relation_id`) of een **entiteit** (`entity_id`), minstens één is verplicht

### Identiteit & poorten (M0.6)

Lezen is open; **elke schrijfactie vereist een account** (`users`, beheer via
`scripts/create_user.py`; inloggen op `/login`, token genereren/roteren op `/account`).
Mensen loggen in met een wachtwoord (sessie); agents en Claude Code sturen
`Authorization: Bearer <token>` mee — **elk onder een eigen agent-account**
(`bijdrager`, eigen token in `data/tokens/`), nooit met het account of token van
een mens: anders zou de attributie liegen én zou de AI de poorten omzeilen.
Mergen/verifiëren (reviewer+), verwijderen (maintainer) en tellende reviewer-akkoorden
blijven mensenwerk; wat de AI indient blijft `voorgesteld` tot een mens het beoordeelt
(de AI stelt voor, de mens beslist). De attributie (`contributed_by`,
`changed_by`) volgt altijd de ingelogde gebruiker; payload-velden worden genegeerd.
Rollen: `bijdrager` (inhoud toevoegen) < `reviewer` (ook statussen beoordelen) <
`maintainer` (ook DELETEs). Sinds M2.1 bestaan daarnaast **filterrollen**
(`user_filter_rollen`, beheer via `create_user.py --filter-rol sourcing=reviewer`):
de effectieve rol binnen een filter is max(globale rol, filterrol). **Dogfood-regel:**
inhoud gaat sinds juni 2026 uitsluitend via dit bijdragepad; migratiescripts zijn
alleen nog voor schema en structuur.

### Openstellen (fase 2, M2.1–M2.6)

**Voorstel-workflow (M2.2).** Elk argument landt via de API als `voorgesteld` en
telt in *niets* mee (statusfactor 0; ook niet in de tegenspraak-balans) tot een
reviewer het merget: `POST /api/arguments/<id>/merge` → `ongecontroleerd`, of
`bronvermelding_nodig` als de citatiepoort (M0.3) dat eist — de poort verhuist dus
naar het merge-moment. `merged_by` wordt vastgelegd; zelf-merge mag (n=1) maar zet
de `self_merged`-vlag. **Uitzondering (juli 2026): een admin hoeft geen review** —
een argument van een **maintainer** merget bij `POST` meteen (zelfde citatiepoort,
`merged_by` = de maintainer, `self_merged` gevlagd, extra `merged`-regel in de
`edit_log`); hetzelfde geldt voor een maintainer-**revisie** binnen de agent-scope
(eigen werk, agent-werk of auteurloos seed-werk — andermans menswerk blijft een
gewoon voorstel). Afwijzen = status `verworpen` (blijft herleidbaar). De
**score-diff-preview** (`GET /api/arguments/<id>/score_diff`, op een tijdelijke
kopie) toont vooraf wat acceptatie verschuift; de **review-wachtrij**
(`/api/review_queue`, paneel in de viz) bundelt voorgestelde argumenten en open
voorstellen.

**Zelf-verificatie is technisch onmogelijk (M2.1).** Niemand zet eigen werk op
`geverifieerd` — de API weigert (403); verificatie door een ander wist een oude
zelf-merge-vlag (heraudit).

**Theory-RfC's (M2.3).** Een nieuw theorie-element ontstaat alleen nog via
`POST /api/voorstellen` (soort `nieuw_theorie_element`); de directe
roles/mechanisms-POSTs zijn dicht. Sjabloon verplicht: definitie, aard-keuze +
freeze-test (mechanismen), afgrenzing, falsificatiecriterium, ≥ 1 instantiatie,
≥ 1 bron. Acceptatie op de theorielaag vergt **twee akkoorden van menselijke
reviewers** (de indiener telt niet mee; agent-oordelen zijn zichtbaar advies en
tellen nooit — alle LLM's gelden als één gecorreleerde familie); de praktijklaag
vergt één akkoord (zelf-akkoord gevlagd). Eén gemotiveerde menselijke afwijzing
sluit het voorstel (`afgewezen`); de indiener kan herzien en opnieuw indienen via
`POST /api/voorstellen/<id>/herzien` — een nieuw, voorgevuld open voorstel met
`payload.vorige_voorstel_id` naar het origineel (de ontvangen reviewfeedback blijft
herleidbaar). Een afgewezen praktijkelement gaat dezelfde weg via
`POST /api/{entities,relations}/<id>/heraanmelden` (auteur bewerkt → terug op
`voorgesteld`).

**Bottom-up: kandidaat-relaties & RfC-koppeling.** Niet elk praktijkpatroon heeft
meteen een theorie-huis. Een relatie zónder mechanisme is daarom geen verboden orphan
maar een **kandidaat**: ze landt `voorgesteld` (telt in niets) en incubeert tot er
genoeg vergelijkbare instanties zijn om er een mechanisme van te destilleren.
`GET /api/kandidaten` groepeert de kandidaten op rol-paar (A→B), zodat je afleest
wanneer een mechanisme rijp is; de orphan-poort zit op het *goedkeur*-moment (een
kandidaat kan niet `goedgekeurd` worden zolang ze mechanisme-loos is — `_modereer`),
niet op creatie. Een mechanisme-RfC kan in zijn `instantiaties` een **gestructureerde**
instantiatie meegeven — `{"bestaande_relatie_id": N}` **adopteert** een incuberende
kandidaat, `{"source_id","target_id","relation_type",…}` **creëert** een verse — die
bij acceptatie aan het nieuwe mechanisme worden gekoppeld (verse instanties landen
`voorgesteld`). Eén besluit koppelt zo de *indiening* van theorie + praktijk, zonder de
*poorten* te koppelen: de gekoppelde relatie behoudt haar eigen bronplicht.

**Argument-revisie-lus (verbeter-pad voor de discussieboom).** Argumenten zijn niet
meer onveranderlijk. Een nog-`voorgesteld` argument schaaft de auteur in-place bij
(`PATCH /api/arguments/<id>` — het telt nog nergens in mee). Een al *gemerged*
argument bevries je en verbeter je via een **revisie**: `POST
/api/arguments/<id>/revisie` maakt een nieuw `voorgesteld` argument; mergt een
reviewer dat, dan **vervangt** het het oude (oud → `verouderd` + `vervangen = 1`,
overgeslagen door `scoring.py`/`influence.py`/viz, herleidbaar via de self-pointer
`reviseert_id`). Iedereen mag een revisie voorstellen, ook van andermans argument —
*ik stel voor, jij beslist*. Een reviewer kan een gemerged argument na een slechte
rating of een drogreden-ondergraving **terug ter herkeuring** zetten (`status
'betwist'` + verplichte motivatie); het verschijnt dan in `review_queue.herkeuring`.
Afwijzen van een argument vergt nu net als bij RfC's/praktijk een motivatie, zodat de
auteur weet wat te verbeteren. De pagina **`/werkbank`** toont elke gebruiker het
eigen ingediende werk per status met de ontvangen feedback en knoppen om te bewerken,
reviseren of opnieuw in te dienen.

> *Waarom geen `lineage`-tabel voor argumenten?* `lineage.voorstel_id` is `NOT NULL`
> en argument-merges lopen bewust niet via `voorstellen` (de lichte mergeweg, M2.2).
> Argumenten dragen hun opvolging daarom zelf (`reviseert_id` + `vervangen`),
> symmetrisch met de `vervangen`-vlag op de theorie-/praktijktabellen.

**Anti-misbruik (M2.4).** Rate limit per account (30/60/120 schrijfacties per
minuut voor bijdrager/reviewer/maintainer); duplicaatdetectie bij indienen
(stdlib-tekstgelijkenis tegen bestaande claims op hetzelfde doel; 409 met
kandidaten, override via `negeer_duplicaten`); recent-changes-feed
(`/api/recent_changes`, open) + persoonlijke watchlist (`/api/watchlist`).

**Ratings & bridging (M2.5, review-verdict v2).** Het verdict op een argument is
**"Argument klopt"** (een lichte endorsement, `nuttig`-rating — telt niet als bewijs)
of **"Argument klopt niet"** (een onderbouwde ondergraving met verplichte reden +
resolutielus; zie "Resolutielus op een ondergraving" onder *Scores*). De kale 👎 als
losse score-laag bestaat niet meer. Bridging (matrixfactorisatie,
`scripts/bridging.py` → `data/bridging.json`) leidt hieruit een gezindheids-
onafhankelijk argumentgewicht af: **+1** = endorsement, **−1** = een gehandhaafde
ondergraving. Je beoordeelt onderbouwing, relevantie en eerlijkheid — nooit waarheid,
en nooit eigen werk; agent-oordelen zijn advies (gewicht via
`scripts/kalibratie_agents.py`, gecapt; agent×agent telt nooit). Het gewicht **krimpt**
naar het neutrale 1,0 met vertrouwen α = n/(n+k) — geen drempel-klif, alleen een
identificeerbaarheidsvloer (≥3 beoordelaars, ≥6 oordelen) — dus het schuift vloeiend in
naarmate de pool groeit.

**Splitsen & samenvoegen (M2.6).** Granulariteit is score-relevant; de knip loopt
daarom via voorstellen (soorten `splitsen`/`samenvoegen`/`hernoemen`). Twee
kernregels: (1) **niets wissen** — het oude element krijgt `vervangen = TRUE` plus
`lineage`-rijen naar de opvolger(s); scoring, influence en viz slaan vervangen
elementen over en `GET /api/lineage/<type>/<id>` beantwoordt oude id's met de
opvolging; (2) **bewijs verhuist nooit automatisch** — bij samenvoegen verhuist
alleen wat in `herbevestigd` staat (de rest blijft achter en telt nergens meer in
mee), bij splitsen moet de hertriage-restlijst (argumenten, relaties,
instantiaties, padclaims) leeg zijn vóór uitvoering; één-op-veel = dupliceren.
`scripts/analyse_granulariteit.py` vlagt kandidaten (bron-overlap, tekstgelijkenis,
disjuncte bewijsgroepen) maar beslist niets.

### Levend & falsifieerbaar (fase 3, M3.1–M3.5)

**Modelreleases (M3.1).** `python3 scripts/release_model.py <X.Y.Z> --titel "…"`
schrijft een onveranderlijk scores-snapshot (`releases/model-vX.Y.Z.json`) en een
changelog mét score-diff t.o.v. de vorige release (`releases/model-vX.Y.Z.md`:
"geloofwaardigheid mechanisme X: 0,62 → 0,71"). `releases/` is ingecheckt; het
script commit/tagt niet zelf (wel via `--tag`). De viz-topbar en `/api/health`
tonen de nieuwste releasetag.

**Onderzoeksagenda (M3.2).** `python3 scripts/onderzoeksagenda.py` rangschikt alle
theorie-elementen op **belang × bewijsarmoede** (brontekort, volumetekort,
tegenspraaktekort en — voor velden — compositietekort), met per element de
concrete `ontbreekt`-lijst: dáár levert één nieuwe goede bron de grootste
verschuiving op. Uitvoer in `data/onderzoeksagenda.json` → `/api/health` →
Modelgezondheid-paneel; de scout-brief (M1.9) kiest zijn missie-onderwerp uit de
top van deze lijst.

**Adversarial rondes (M3.3).** Hetzelfde rapport levert de red-team-doelwitten:
de top-20 invloedrijkste edges (afgeleide invloed × zekerheid, met stance-balans).
De rondes draaien onder `redteam-agent` met `missies/redteam_brief.md` (sterkste
eerlijke tegenbewijs, anti-stroman-regels, afwezigheidsrapporten); bevindingen
volgen het gewone voorstelpad.

**Voorspellingsregister (M3.4).** De stap van "consistent verhaal" naar "getoetst
model": `POST /api/predictions` legt een toetsbare verwachting vast vóór de
uitkomst bekend is (claim + afleiding uit het model + meetcriterium + kans +
deadline in de toekomst + ≥ 1 theorie-anker). Na de deadline scoort een reviewer
de uitkomst (`PATCH /api/predictions/<id>/uitkomst`): Brier = (kans − uitkomst)²;
`onbeslisbaar` telt niet mee in de kalibratie; gescoord = onveranderlijk; zelf
scoren mag (n=1) maar draagt de `self_scored`-vlag. `scripts/voorspellingen.py`
geeft het overzicht + kalibratierapport; de validator vlagt verlopen open
voorspellingen (VOORSPELLING-DEADLINE) en de heraudit-lijst (VOORSPELLING-ZELF).

**Jaarlijkse audit (M3.5).** Checklist in `missies/audit_checklist.md`
(aard/tiers, bronclassificaties, halo-criteria & constanten, proces/provenance);
eerstvolgende audit: juni 2027, afgesloten met een modelrelease.

---

## Scores op relaties

Elke relatie heeft twee onafhankelijke scores:

### Certainty (zekerheid): "Bestaat deze relatie?"

| Score | Betekenis | Voorbeeld |
|---|---|---|
| 0.9 - 1.0 | Gedocumenteerd feit | DPG Media bezit de Volkskrant |
| 0.7 - 0.89 | Sterk bewijs | ANP-pakketjournalistiek bij dagbladen |
| 0.5 - 0.69 | Waarschijnlijk | WEF-invloed op NOS-framing |
| 0.3 - 0.49 | Mogelijk | Specifieke SLAPP-dreiging door GBL |
| < 0.3 | Speculatief | — |

### Influence (invloed): "Hoe sterk werkt het door in de berichtgeving?"

| Score | Betekenis | Voorbeeld |
|---|---|---|
| 0.9 - 1.0 | Bepalend | DPG→Volkskrant eigendom (bepaalt budget, hoofdredacteur) |
| 0.7 - 0.89 | Sterk | ANP→NU.nl pakketjournalistiek (bulk van het nieuws) |
| 0.5 - 0.69 | Matig | Clingendael→NOS expert framing |
| 0.3 - 0.49 | Beperkt | Eén adverteerder van velen |
| < 0.3 | Marginaal | BlackRock→Shell (passief bezit) |

Een relatie kan zeker bestaan maar weinig impact hebben (Vanguard→Shell: feit, maar passief). Of onzeker zijn maar potentieel groot effect hebben (zelfcensuur op redacties: moeilijk te bewijzen, maar systemisch).

Beide assen zijn **schuldig tot bewezen**: de handmatige kolom blijft als **prior** bestaan, maar de score die het model gebruikt wordt afgeleid uit de bewijslast (zie hieronder). Een prior zonder onderbouwing wordt naar een lage vloer (0,05) gezet en dient alleen als fallback — voor `certainty` via `migrate_unsourced_certainty.py`, voor `influence` via `migrate_unsourced_influence.py`. `influence` wordt vervolgens net als `certainty` uit bewijs opgetild: `property='influence'`-argumenten (M1.7) verschuiven hem, anders blijft hij op de vloer. Zo is er geen enkele *initiële willekeurige score*: de validator (`INVLOED-PRIOR`, een fout) bewaakt dat een invloed boven de vloer altijd onderbouwd is. De vloer is bewust 0,05 en niet 0, zodat de invloedsgraaf (`influence.py`) de *topologie* (positie) blijft meten terwijl de *magnitude* eerlijk minimaal blijft tot ze is bewezen.

### Aard: direct & systemisch

Niet elke relatie is een onmiddellijk dyadisch kanaal tussen twee actoren; sommige zijn een *emergente
eigenschap van het systeem* zonder gericht bron→doel-kanaal. De kolom `mechanisms.aard` legt dat onderscheid
vast (relaties erven het van hun mechanisme); het stuurt zowel de visualisatie als de invloed-wiskunde
(`influence.py`).

**Leidend principe: een edge tussen twee nodes is `direct`.** "Indirectheid" is een eigenschap van een
*pad* (≥2 edges via tussen-nodes), niet van één edge. Een gemedieerde invloed teken je dus als de *keten*
van directe edges (de demping volgt vanzelf uit `influence.py`, zie onder); de twijfel of een verband wel
een hard kanaal is, zit in de `certainty`-score — niet in een stippellijn. Daarom zijn er nog maar twee
levende aarden, met de visuele grammatica **pijlpunt = gericht, doorgetrokken = onmiddellijk**:

| aard | betekenis | toets | render | voorbeeld |
|---|---|---|---|---|
| `direct` | lokaal feit; de oorzaak ís de twee eindpunten — óók als de invloed gemedieerd of onzeker is (mediatie → de keten; twijfel → de `certainty`-score) | verander de bron/het doel → de claim wordt onwaar | doorgetrokken pijl **mét** punt, filterkleur | DPG → Het Parool (eigendom); Bilderberg → mediabestuurder (`ideologische_synchronisatie`, cert ≈ 0,05) |
| `veld_eigenschap` | een staande *toestand* ván de getroffen node (die de node *ondergaat*); oorzaken bestaan wél, maar zijn diffuus/overgedetermineerd — er is geen toerekenbare levende zender, en de toestand blijft werken zonder levende input | wie is de zénder (niet: de oorzaak)? niemand specifieks — én: bevries alle andere nodes; werkt het effect morgen nog door? (zelfcensuur: ja; eigenaarsinvloed via de hoofdredacteur: nee, die heeft de levende keten nodig) | **halo** om de node (geen edge); bron-rol mag `NULL` zijn of de diffuse herkomst aanduiden | `zelfcensuur`, `sociologische_homogeniteit` (homogene redactie → blinde vlekken), `geweld_intimidatie`, `elite_referentiekader` (media opereren binnen het elite-frame; herkomst diffuus — er is geen handeling van forum naar redactie) |

> Let op: dat een mechanisme een systemisch *kenmerk* beschrijft zegt niets over zijn `aard`.
> `eigendomsconcentratie` is een macro-systeemkenmerk, maar elke afzonderlijke edge (DPG → Het Parool)
> is een lokaal eigendomsfeit — dus `direct`. Het emergente zit daar in de *optelsom* (de concentratie),
> niet in de losse edge.

**Afgeschaft.** Twee oudere aarden zijn leeg en hun viz-rendering is verwijderd:
- `indirect` (gericht-maar-gemedieerd; was een gestippelde pijl mét punt) — vervangen door het principe
  hierboven. De gemedieerde eigenaarsgreep (`mediaeigenaar → STAK → RvC → directie → hoofdredacteur`) is nu
  gewoon díé keten van directe edges; elke schakel vermenigvuldigt een influence < 1, dus het netto-effect
  aan het eind blijft klein — geen bevel, wel een eigenaarssignatuur.
- `veld_instantiatie` (diffuse waaier; was gestippeld zónder punt) — elke waaier bleek óf een echte gerichte
  dyade (→ `direct` gemaakt: `ideologische_synchronisatie`, `schijndebat`, `omroepverzuiling`), óf redundant
  (→ verwijderd: `stakeholder_capitalism_frame`), óf bij nader inzien een node-eigenschap
  (`transnationale_frame_export` werd eerst `direct`, maar er is geen handeling van forum naar redactie en
  de cert=0,05-edges bliezen de forum-centraliteit op — herclassificeerd tot halo `elite_referentiekader`).

Beide blijven geldig in de `CHECK` (voor migratie-replay) maar tekenen, indien gezet, gewoon als directe edge.

**Effect op de wiskunde** (`influence.py`, parameter `field_mode`): een `veld_eigenschap` telt **niet** mee
als uitgaande invloed (het is een node-eigenschap, geen kanaal) — en hoort ook niet als inkomende edge
gemodelleerd te worden: de oorzaken van de toestand (flak, eigendomsdruk, carrièreprikkels) hebben al hun
eigen directe edges in de graaf, en hun invloed-scores worden geschat op een effect dat juist vía de
internalisering loopt. De halo daarnaast als kanaal tellen zou dezelfde causale kracht dubbel tellen;
de halo is de *neerslag en versterker* van edges die er al zijn, geen extra kanaal; bij `exclude` (de schone dyadische graaf)
valt ze helemaal weg. De `collapse`-correctie voor veld-instantiatie-waaiers (één gedempte bijdrage per bron,
gewicht gedeeld door de fan-out `k`) bestaat nog in de code maar staat inactief — er zijn geen waaiers meer;
ze voorkwam dat fan-out-edges de centraliteit van elite-knooppunten kunstmatig inflateerden. `aard` is
orthogonaal aan het filter, dus de kleur (het filter) blijft.

**In de viz**: het paneel *Systemische effecten* heeft aparte toggles per laag — **emergente velden**
(goud) en **halo's** (ring om de getroffen node; schakelt ook de node-grootte naar de veld-variant) gelden
alleen in het **theoriemodel** (in het praktijkmodel is WEF → NOS gewoon een concrete relatie en tekent
álles als normale edge); **afgeleide pijlen** en **directe pijlen** werken in beide modellen. Default staat
alleen *directe pijlen* aan (schone graaf).

Naast deze edge-aarden kent het theoriemodel het **emergente effect als hyperedge**: een systeem-
eigenschap die uit het samenspel van een hele *groep* rollen voortkomt en niet in één bron→doel-relatie
te vangen is (eigen tabellen `emergent_effects` + `emergent_effect_members`; bv. *fabricage van instemming*,
*zelfversterkende homeostase*). Ook **terugkoppellussen tussen meerdere rollen** horen hier (medialogica,
verkillingsspiraal, economische feedback-loop): een lus is geen toestand van één node en geen gerichte
dyade — elke schakel is tegelijk oorzaak en gevolg. Het verschijnt als een transparant **goud veld** rond
de leden, met label, hoverbaar/klikbaar (het detailpaneel toont het samenspel).

Velden zijn **eersteklas theorie-elementen**, met dezelfde drie attributen als rollen en mechanismen:
een eigen **discussieboom** (argumenten met `emergent_effect_id` + citaties — elk veld draagt zijn
canonieke literatuur als argument, zie de tabel hieronder), een eigen **tijdvenster**
(`active_from`/`active_until`, gefilterd door de tijdbalk) en een eigen **score** (`scoring.py`:
lit-only — een veld heeft geen praktijk-instanties; de praktijk leeft in zijn mechanismen en rollen,
dus geloofwaardigheid = literatuurpoot en 'sterkte' is niet van toepassing). Het detailpaneel toont
score, samenspel, deel-effecten en de literatuuronderbouwing met invoerformulier.

Eén veld is structureel anders: `fabricage_van_instemming` is het **apex-veld** — de conclusie van het
hele model, niet "nóg een groepseigenschap". De elf overige velden zijn er formeel als **deel-effecten**
aan gekoppeld (`emergent_effect_subeffects`): de kaasstolp-lussen, de uniformerings- en homogeniteits-
velden en de versterkings- en disciplineringslussen komen erin samen. Zo zit de Haagse kaasstolp — en
daarmee politicus, voorlichter en lobbyist — wél in het apex-effect (via hún velden), zonder
alles-omvattende ledenset (een hyperedge die alles bevat ís het model zelf en verklaart niets) en
zonder dubbeltelling. De *ledenset* van het apex-veld blijft pars pro toto: één dragende rol per
filter (mediaeigenaar, adverteerder, persbureau, belanghebbende, elite_forum) plus mediaorganisatie
en publiek.

De twaalf emergente effecten, met de literatuur die de compositie benoemt:

| effect | kern | literatuur |
|---|---|---|
| `fabricage_van_instemming` | pro-elite bias uit het samenspel van de vijf filters; 'manufacturing consent' = instemming van de geregeerden fabriceren (niet 'consensus' of 'toestemming'); ledenset pars pro toto — één dragende rol per filter + medium + publiek | Herman & Chomsky (naar Lippmann 1922) |
| `zelfversterkende_homeostase` | afwijkingen worden gedempt, status quo reproduceert zichzelf | Bergman; systeemtheorie-duiding |
| `haagse_stam` | politici, voorlichters, lobbyisten en journalisten als één stam | Luyendijk |
| `toeschouwersdemocratie` | het publiek ziet de frontstage-opvoering, de afweging is backstage | Luyendijk |
| `lobbymakelaardij` | de lobbyist regisseert journalist én politicus namens een onzichtbare opdrachtgever | Luyendijk |
| `schijnpluriformiteit` | veel merknamen, één ANP-nieuwsstroom; pluriformiteit als façade | Boumans (2016): ±66% online nieuws ANP-gebaseerd |
| `ideologische_homofilie` | journalist, expert en politicus uit dezelfde academische kring; bevestiging oogt als verificatie | Bovens & Wille (2011); Vis (2001, 'Haagse waakhonden'); Hermans (2016, WJS) |
| `mediahype` | zelfversterkende nieuwsgolf, pack journalism; positieve feedback | Vasterman (2004) |
| `medialogica` | wurggreep politiek↔media; incidenten verdringen inhoud (gevangenendilemma) | RMO (2003) |
| `verkillingsspiraal` | extern flak ↔ intern conformisme; collectief chilling effect | PersVeilig/I&O (2021) |
| `voorlichtingsovermacht` | ±150.000 communicatieprofessionals vs. ±15.000 journalisten | UvA/CBS (via Villamedia 2018) |
| `economische_feedback_loop` | dalend vertrouwen → minder abonnees → bezuinigingen → slechtere journalistiek → nog minder vertrouwen | systeemtheorie-duiding (nieuwsmijding verhoogt de financiële druk) |

### Afgeleide (indirecte) pijlen & padclaims

Indirecte invloed wordt **niet opgeslagen** maar bij selectie van een node ter plekke afgeleid: de
sterkste ≥2-hops-route (max-product over de zichtbare graaf) tekent als violette stippelpijl met
"via …"-label. Drie poorten bepalen of zo'n pijl mag bestaan — alle drie verplicht:

1. **Schakelscore** — de drempel-sliders gelden ook hier, net als voor gewone edges: de
   zekerheid/geloofwaardigheid-slider toetst élke schakel afzonderlijk, de invloed/sterkte-slider
   de gedempte padsterkte (max-product) van de hele pijl, met een vaste ondergrens van 5%
   padsterkte tegen ruis.
2. **Schakelargumenten** — elke schakel heeft eigen argumenten in de discussieboom; een score zonder
   discussieboom telt niet als onderbouwing.
3. **Eindclaim (padclaim)** — de *compositie* zelf is onderbouwd. Dat A→B en B→C elk kloppen, bewijst
   nog niet A ⇢ C: invloed is niet automatisch transitief (wat A bij B verandert hoeft niet het kanaal
   te zijn waarlangs B C beïnvloedt). Een padclaim is een gewoon argument in `arguments` met
   `role_id` = bronrol, `property = 'indirecte_invloed_op'`, `property_value` = **ID van de doelrol**
   (sinds M2.6; voorheen de rolnaam, die brak stil bij hernoemen/splitsen/samenvoegen),
   plus citaties — dezelfde bewijsstandaard als een directe pijl. `scoring.py` sluit padclaims uit van
   de rolscore (ze gaan over het pad, niet over de rol); de viz toetst er elke kandidaat-pijl aan, in
   het praktijkmodel via de rollen van de twee entiteiten. Vuistregel: claim alleen een paar als de
   literatuur de compositie zelf benoemt (bv. Bergman over eigenaarsinvloed op hoofdredacteurs-
   benoemingen; Luyendijk over de lobby-driehoek), en alleen als er ook een route bestaat die het
   verhaal van de claim volgt — een claim wiens enige doorlatende route iets ánders vertelt, hoort er
   niet in.

---

## Scores: van discussieboom naar theorie

Een theoretisch element (rol/mechanisme) is een **klasse**; de concrete entiteiten/relaties zijn
**instanties** ervan (gekoppeld via `instantiations`). De geloofwaardigheid en sterkte van de klasse
zijn *emergent*: ze bouwen op uit de bewijslast eronder. De berekening (in `scoring.py`, gedeeld door
`generate_viz.py` en het `/api/scores`-endpoint) kent drie lagen.

**Laag A — basiskracht τ per argument:** `weight × statusfactor × bronfactor`, met `weight`
**geneutraliseerd**. Het zelf-gerapporteerde argumentgewicht is geen objectieve maat (de invoerder
zet zijn eigen gewicht — Z2), dus de opgeslagen `weight`-kolom telt niet meer mee: in de praktijk is
`weight = 1,0` (neutraal) en rust τ alleen op de verifieerbare factoren `statusfactor × bronfactor`.
Een **bridged rating** (M2.5, review-verdict v2) vult het gewicht alsnog objectief in zodra de
beoordelaarspool het toelaat: **+1** = een 'Argument klopt'-endorsement, **−1** = een gehandhaafde
(niet-'opgelost') ondergraving — de beredeneerde vervanger van de oude 👎. `scripts/bridging.py`
krimpt het oordeel naar het neutrale 1,0 met vertrouwen α = n/(n+k) (k=5): **geen drempel-klif meer**,
alleen een kleine identificeerbaarheidsvloer (≥3 beoordelaars, ≥6 oordelen) waaronder de gezindheidsas
niet te schatten is — bridging schuift dus vloeiend in naarmate de pool groeit. De statusfactor
schaalt op verificatiestatus (geverifieerd 1,0 → betwist 0,25 → verworpen 0,0); de **bronfactor =
rigueur × relevantie**: het reliabilitygewicht van de betrouwbaarste citatie × een relevantiefactor
uit `sources.onderwerp` (`nl_systeem` ×1,15 · `algemeen`/`onbepaald` ×1,0 · `buitenlands` ×0,85,
gecapt op 1,0) — zo weegt een bron over het Nederlandse mediasysteem zwaarder dan een buitenlandse van
gelijke rigueur, zónder ooit een rigueur-gat te overrulen. Classificeren (reliability + onderwerp) is
**reviewer-werk** (`PATCH /api/sources/<id>/classificatie`), bewaakt door `validation.klasse_consistentie`
(de klasse past bij het brontype; een hoge klasse vereist een vindplaats) en geaudit door de
`BRON-KLASSE`-check. Reliabilitygewichten: `academisch 1,0 · primair 0,95 · institutioneel 0,85 ·
kwaliteitsjournalistiek 0,70 · regulier 0,50 · opinie 0,35 · grijs 0,20 · eigen_synthese 0,0 ·
onbeoordeeld 0,15`. Projectmateriaal (`sources/AI/`, klasse `eigen_synthese`) weegt 0: vindplaats,
nooit bewijs. Zo is geen enkele score-input meer zelf-gerapporteerd: zekerheid en invloed komen uit
bewijs (priors gefloord op 0,05), en de argumentkracht uit status + bron + bridged oordeel.

**Boomsemantiek (M1.1) — eindkracht σ per argument (DF-QuAD).** Replies dragen géén eigen doel
(DB-CHECK + API): hun stance is relatief aan de *parent*. Kracht stroomt van blad naar wortel: de
steunende en aanvallende kinderen worden elk geaggregeerd met de probabilistische som
`1 − ∏(1 − σᵢ)`, waarna het verschil de basiskracht moduleert — aanvallers trekken σ richting 0
(`σ = τ·(1−(a−s))`), steuners richting 1 (`σ = τ + (1−τ)·(s−a)`), in balans blijft τ. Een blad houdt
σ = τ, dus een platte boom reproduceert exact de oude formule. **Doorgerekend voorbeeld** (ook de
golden-snapshot-test, `scripts/test_scoring.py`):

```
A1 voor   (geverifieerd · academische bron)            τ = 1,0·1,0       = 1,00
 └─ B1 ondergraving (geverifieerd · geen bron)         τ = 1,0·0,3       = 0,30
     └─ C1 versterkt B1 (ongecontroleerd · geen bron)  τ = 0,5·0,3       = 0,15
σ_B1 = 0,30 + (1−0,30)·0,15 = 0,405         (B1 versterkt door C1)
σ_A1 = 1,00 · (1 − 0,405)   = 0,595         (A1 gedempt door B1)
```
(weight telt niet mee — neutraal 1,0; alleen statusfactor × bronfactor)

Alleen **root**-argumenten tellen voor het doel zelf; een ondergraving dempt dus alleen het argument
dat ze aanvalt (een drogredelijk argument vóór een ware claim trekt de claim niet omlaag — het houdt
alleen op haar te stutten). Tegenbewijs voor het doel zelf is een **weerlegging**: een contradicting
*root*-argument mét bron.

**Resolutielus op een ondergraving (review-verdict v2).** "Argument klopt niet" is geen kale downvote:
elke ondergraving vereist een `reasoning` (benoem wat er niet klopt) en draagt een stand
`bezwaar_resolutie` ∈ {`open`, `herzien`, `blijft`, `opgelost`}. Open/herzien/blijft dempen de σ van
de parent; alleen **`opgelost`** heft de demping op. De lus: de auteur van het aangevochten argument
verbetert en zet `herzien`; de bezwaarmaker herbeoordeelt (`opgelost` of `blijft staan`); een reviewer
mag een bezwaar pas **overrulen** naar `opgelost` ná `herzien` (zodat een afwezige bezwaarmaker het
argument niet eeuwig bevriest). Het effect is omkeerbaar: lost de auteur het op, dan veert de σ terug
naar haar onaangevochten basiskracht. De 👍/👎-duim als losse score-laag bestaat niet meer — "Argument
klopt" is een lichte endorsement (voedt hooguit bridging), "Argument klopt niet" is deze ondergraving.
Een ondergraving mag een `objection_type` dragen — sinds juli 2026 een **vrij tekstveld** (de
CHECK-enum verviel via `migrate_objection_type_vrijtekst.py`: elke sluitende categorielijst bleek te
kort en een volledige eindeloos; de oude drogreden-taxonomie blijft het aanbevolen vocabulaire).

**Admin-veto (juli 2026).** Een ondergraving van een **maintainer** (admin) weegt niet mee als gewone
demping maar als **veto**: de parent telt voor **0** (σ = 0, "de punten volledig ongedaan") zolang het
bezwaar actief is. Het veto vervalt op twee manieren: (1) de resolutielus eindigt op **`opgelost`**
(zoals elke ondergraving), of (2) iemand **weerlegt het veto met review** — een tegen-reactie
(contradicting reply, met verplichte `reasoning`) op de admin-ondergraving die een reviewer merget
schort het veto op, waarna de gewone DF-QuAD-demping weer geldt (het veto blijft dan een normale,
zelf ook dempbare ondergraving). Een voorgestelde tegen-reactie verandert niets — de opheffing loopt
per definitie via review. `scoring.py` exporteert de vlaggen `admin_veto` (op het veto) en `geveto`
(op de genulde parent) in `argument_scores`; de UI toont ⛔-badges. End-to-end:
`scripts/test_admin_veto.py`.

**Laag B — afgeleide praktijkscore per relatie/entiteit:** `steun / (steun + tegen + k)` over de
σ's van de root-argumenten, met **clusteraggregatie (M1.2)**: elke bron heeft een `cluster_key`
(zelfde auteur/uitgever/onderliggende data = zelfde cluster); binnen een (stance, cluster)-paar telt
alleen de sterkste σ, en argumenten zonder echte citatie delen per doel één pseudocluster — tien
citaten uit hetzelfde boek zijn geen tien bewijzen, en tien bronloze beweringen ook niet. In het
voorbeeld: een tweede voor-argument (σ 1,0) uit hetzelfde broncluster als A1 telt als de sterkste
van het cluster (max, geen som → steun 1,0); een weerlegging D1 (τ 0,895, institutionele bron) staat
daar tegenover: `score = 1,0 / (1,0 + 0,895 + 1) = 0,3454`. Zonder argumenten valt de score terug op
de handmatige `certainty` (prior, gefloord op 0,05 zonder bron); een entiteit zonder eigen argumenten
erft het gemiddelde van haar relaties.

**Uitzondering — personen dragen geen zekerheidsscore (juli 2026).** Het bestaan van een persoon is
binair: een persoon bestaat of bestaat niet, en daar valt niets aan te scoren — een
"geloofwaardigheid 34%" op een persoonsknoop leest als bestaanstwijfel en het
`onweersproken`-plafond zou er zinloze tegenspraak afdwingen (niemand weerlegt het bestaan van een
hoofdredacteur). `scoring.py` berekent de waarde intern nog wél (ze voedt als
rol-instantie-zekerheid laag C: *functie-invulling*, geen bestaan) maar laat `persoon`-entiteiten
weg uit de geëxporteerde `entities`/`entities_detail`; `viz_data.py` zet de velden expliciet op
`None`, zodat de viz geen scorebalk, interval of onweersproken-badge tekent. De echte onzekerheden
rond een persoon leven waar ze thuishoren: in de **relaties** (elk met eigen certainty) en de
**aspect-overlays** (kleurmeter/welstandsmeter). Een niet-relevante of verzonnen persoon is een
**moderatie**-kwestie, geen score-kwestie: de discussieboom op de knoop blijft bestaan (weerleg
gerust de *typering*), een reviewer wijst een voorgestelde nep-persoon af en een maintainer kan elke
persoonsentiteit verwijderen (`DELETE /api/entities/<id>`); de bronpoort op relaties vangt fictieve
personen bovendien al bij binnenkomst.

**Laag C — theoriescore per rol/mechanisme**, uit twee onafhankelijke bewijslijnen:
- **Praktijk (bottom-up):** geloofwaardigheid-gewogen aggregatie over de gekoppelde instanties, met
  volume-verzadiging `gem_cert × n/(n+k)` — veel goed-onderbouwde voorbeelden tillen de klasse op.
  De **sterkte** is de geloofwaardigheid-gewogen gemiddelde invloed van die instanties.
- **Literatuur (top-down):** argumenten/citaties die *direct* op de rol/het mechanisme hangen
  (`arguments.role_id`/`mechanism_id`), met dezelfde cluster- en boomsemantiek.

De twee lijnen worden gecombineerd met een **noisy-OR**: `geloofwaardigheid = 1 − (1−literatuur)(1−praktijk)`.
**Emergente velden (M1.5)** hebben hun eigen twee lijnen: literatuur op het effect zelf ⊕ de
**compositieclaim** (`property='compositie'`) — bewijs dat het *samenspel* bestaat, niet alleen de
leden (analoog aan padclaims). Zonder compositieclaim is de veldscore gemaximeerd op **0,50**.

**Dwarsmaatregelen over alle lagen:**
- **Onzekerheidsband (M1.3):** elke geloofwaardigheid krijgt een 95%-interval — laag B analytisch
  (Beta-posterior op de steun/tegen-massa's, Jeffreys-smoothing, demping k als tegenmassa), laag C
  via bootstrap over de instanties gecombineerd met het Beta-interval van de literatuurlijn. Een
  lijn zónder bewijs telt als 0 zonder onzekerheid: de score meet *onderbouwing*, niet waarheid.
  Toon nooit een puntscore zonder interval en dekking erbij.
- **Tegenspraak-plafond (M1.4):** zonder *overwogen tegenspraak* — minstens één niet-verworpen
  contradicting-argument mét echte citatie op het doel — is de geloofwaardigheid gemaximeerd op
  **0,70** en draagt het element het label **onweersproken**. Het plafond geldt óók voor priors.
- **SPOF-vlag (M1.2):** drijft alle steun op één broncluster, dan vlagt de score "1 broncluster".
- **Invloed-as bewijsbaar & schuldig tot bewezen (M1.7):** aspect-argumenten met
  `property='influence'` verschuiven de afgeleide invloed van een relatie (of de sterkte van een
  mechanisme/halo): de handmatige kolom blijft de prior en de bewijsbalans trekt hem naar zich toe
  met gewicht `massa/(massa+k)`. Een niet-onderbouwde invloed-prior staat op de vloer 0,05
  (`migrate_unsourced_influence.py`), symmetrisch met de certainty-vloer; de validator-check
  `INVLOED-PRIOR` (fout) bewaakt dat een invloed boven de vloer altijd bewijs heeft — geen
  initiële willekeurige scores. Aspect-argumenten (influence, padclaims, compositie) tellen nooit
  mee in de zekerheids-balans: twee assen, één bewijsstandaard.

In het theoriemodel codeert de node-grootte/lijndikte de **sterkte**; het detailpaneel toont beide
scores met interval, opsplitsing literatuur ⊕ praktijk en de vlaggen. Alle constanten staan boven in
`scoring.py`; `scripts/analyse_gevoeligheid.py` (M1.6) rapporteert leave-one-cluster-out en een
parameter-sweep (resultaat zichtbaar in het Modelgezondheid-paneel), en
`scripts/test_scoring.py` legt de einduitkomsten vast als golden snapshot (draait mee in
`scripts/validate_model.py --strict`).

**Emergente velden** doorlopen dezelfde laag C, maar alleen langs de literatuurlijn
(`arguments.emergent_effect_id`): een veld heeft geen instanties — zijn praktijk leeft in de
gekoppelde mechanismen en rollen — dus de geloofwaardigheid is de literatuurpoot en 'sterkte' is
niet van toepassing. Het detailpaneel van een veld toont die score met dezelfde maatstaf.

---

## Argumentstructuur per relatie

Elke relatie kan meerdere argumenten hebben die voor, tegen of nuancerend zijn. Elk argument kan onderbouwd worden met meerdere citaties uit verschillende bronnen.

```
Relatie: DPG Media → RTL Nederland [winstmaximalisatie]
  certainty: 0.85  |  influence: 0.70
  │
  ├── [+] SUPPORTING: "ACM moest voorwaarden stellen..."
  │     ├── Citatie → AI-analyse rapport (lokaal bestand)
  │     │
  │     └── [−] CONTRADICTING: "ACM-voorwaarden beperken winstmaximalisatie"
  │           ├── Citatie → ACM besluit (2023)
  │           │
  │           └── [+] SUPPORTING: "Voorwaarden zijn niet afdwingbaar na fusie"
  │                 └── Citatie → FTM onderzoek (2024)
  │
  └── [~] CONTEXTUAL: "Redactiestatuten bieden geen ijzerharde garanties"
        ├── Citatie → Bergman (2014), Hoofdstuk 1
        └── Citatie → Herman & Chomsky (1988), pp. 3-14

Entiteit: DPG Media
  │
  ├── [+] SUPPORTING: "DPG heeft een dominante marktpositie in online nieuws"
  │     └── Citatie → ACM marktanalyse (2023)
  │
  └── [−] CONTRADICTING: "Marktaandeel alleen zegt niets over redactionele invloed"
        └── Citatie → NVJ rapport (2022)
```

### Stances

| Stance | Symbool | Betekenis |
|---|---|---|
| `supporting` | + | Bewijs dat de relatie bevestigt |
| `contradicting` | - | Bewijs dat de relatie tegenspreekt |
| `contextual` | ~ | Nuancering, noch voor noch tegen |

**Voorstel-poort (M2.2) + citatiepoort (M0.3).** Elk argument landt via
`POST /api/arguments` als `voorgesteld` en telt nergens in mee tot een reviewer het
merget — behalve van een **maintainer** (admin): dat merget meteen (juli 2026, zie
"Voorstel-workflow"). Op het merge-moment geldt de citatiepoort: een `supporting`- of
`contradicting`-**root**-argument zonder citaties wordt `bronvermelding_nodig`
(statusfactor 0,40), mét citaties `ongecontroleerd`. De eerste citatie
(`POST /api/citations`, of direct in het `citations`-veld van `POST /api/arguments`)
heft `bronvermelding_nodig` automatisch op naar `ongecontroleerd` — uitsluitend die
overgang; `geverifieerd` blijft een menselijke review-stap, en sinds M2.1 per
definitie door een ánder dan de auteur. Alleen `contextual` mag bronloos.

**Reply-regels (M1.1/M1.8).** Een reply (`parent_argument_id` gevuld) draagt **geen
eigen doel en geen property** (DB-CHECK; de API weigert anders): zijn stance is
relatief aan de parent. De UI kent op een argument precies **twee reacties** (juli
2026): **"Argument klopt niet"** (de ondergraving — bronloos, reden verplicht) en
**"Bewijs/tegenbewijs gevonden"** (een reply mét bron, vóór of tegen). Een
`supporting`-reply versterkt het parent-argument; een `contradicting`-reply is een
**ondergraving** ("dit argument klopt niet") — die mag bronloos (het aanwijzen van
het gat volstaat, de citatiepoort geldt niet) en kan een `objection_type` dragen:
sinds juli 2026 een **vrij tekstveld** (de indiener benoemt de categorie zelf; de
oude drogreden-taxonomie — `cirkelredenering`, `stroman`, `non_sequitur`,
`correlatie_als_causatie`, `vals_dilemma`, `ad_hominem`, `autoriteit_buiten_domein`,
`anekdote_als_regel`, `cherry_picking`, `equivocatie`, `citaat_dekking`, `overig` —
blijft het aanbevolen vocabulaire), met in `reasoning` wat er precies niet klopt.
Een **weerlegging** (tegenbewijs voor het doel zelf) is géén reply maar een
contradicting root-argument mét bron.

---

## Entiteittypes

> **Soort entiteit (`type`) vs. functie in model (rol).** Dit zijn twee verschillende
> assen die niet door elkaar mogen lopen:
> - **`type` = de structurele VORM** — *wat is het?* Voor organisaties varieert die echt
>   (bedrijf, partij, stichting, omroep…); voor mensen bestaat er maar **één** soort:
>   `persoon`. Een "politicus" of "journalist" is geen ander *soort mens* maar een *functie*.
> - **Rol (`primary_role_id` / `entity_roles`) = de FUNCTIE in het model** — *wat doet het
>   binnen de vijf filters?* (bv. `mediaeigenaar`, `adverteerder`, `gezagsexpert`, `politicus`).
>
> Concreet: Shell is `type=bedrijf` met rol `adverteerder`; John de Mol is `type=persoon`
> met rol `mediaeigenaar`. Functie/positie hoort dus altijd in de rol, nooit in `type`.

De volledige toegestane lijst staat in de `CHECK`-constraint van `entities` in `schema.sql`.

**Personen:** `persoon` — één structurele soort; de functie (politicus, journalist, lobbyist, columnist, klokkenluider, mediaeigenaar…) staat in de rol.

**Organisaties (structurele vormen):**

| Type | Beschrijving | Voorbeelden |
|---|---|---|
| `mediaorganisatie` | Nieuwsproducent of -distributeur (pers/online) | DPG Media, de Volkskrant, De Telegraaf, NRC |
| `omroep` | Publieke of commerciële omroep | NOS, RTL Nederland |
| `persbureau` | Persbureau / nieuwsgroothandel | ANP |
| `bedrijf` | Commercieel bedrijf (ook in de rol van adverteerder, holding, belegger) | Shell, Albert Heijn, Unilever, BlackRock |
| `stichting` | Stichting, administratiekantoor (STAK), borgingsstichting | Stichting Democratie en Media |
| `vermogensbeheerder` | Institutionele belegger | BlackRock, Vanguard |
| `elite_netwerk` | Besloten elite-/coördinatieforum | Bilderberg Groep, World Economic Forum |
| `denktank` | Onderzoeks-/beleidsinstituut | Clingendael, HCSS |
| `overheidsinstelling` | Overheidsorgaan | Belastingdienst, WRR |
| `toezichthouder` | Toezichthoudend orgaan | ACM, Commissariaat voor de Media |
| `partij` | Politieke partij | VVD, CDA, PVV |
| `platform` | Digitaal platform | Google, Meta, TikTok |
| `pr_bureau` | Communicatie-/PR-bureau | — |
| `ngo`, `vakbond`, `onderwijsinstelling`, `burgerinitiatief`, `rechterlijke_macht`, `lobbygroep` | Maatschappelijke en tegenmacht-actoren | NVJ, vakbonden, universiteiten |

> **Legacy.** Rol-achtige type-waarden (`politicus`, `journalist`, `voorlichter`, `lobbyist`,
> `columnist`, `academicus`, `mediaeigenaar`, `toezichthouder_persoon`, `advocaat`,
> `klokkenluider`, `adverteerder`) blijven in de `CHECK` toegestaan zodat seed-/enrich-scripts
> hun ruwe extractie kunnen invoeren, maar worden in de live DB samengevouwen tot hun
> structurele vorm door `scripts/migrate_clean_entity_types.py`. Gebruik voor nieuwe data
> alleen de structurele types hierboven.

## Relatietypes

De volledige lijst staat in de `CHECK`-constraint van `relations` in `schema.sql`, gegroepeerd:

| Groep | Types |
|---|---|
| **Eigendom & financiën** | `eigendom`, `financiering`, `adverteerder`, `donor`, `investering` |
| **Organisatorisch** | `lidmaatschap`, `personeel`, `bestuurder`, `adviseur`, `woordvoerder_van`, `draaideur` |
| **Informatiestromen** | `bron_van`, `mediaplatform`, `framing`, `citeert` |
| **Macht & druk** | `lobbyt`, `censuur`, `flak`, `intimidatie`, `regulering`, `zelfcensuur` |
| **Politiek & ideologisch** | `alliantie`, `oppositie`, `beinvloeding`, `cooptatie`, `etikettering` |
| **Algoritmisch** | `algoritmische_filtering` |

Meest gebruikt: `beinvloeding` (151), `eigendom` (51), `adverteerder` (40), `lidmaatschap` (24), `personeel` (16), `draaideur` (14).

---

## Projectstructuur

```
propaganda-model/
├── schema.sql                          # Databaseschema (alle tabellen)
├── DOCUMENTATIE.md                     # Dit bestand
├── server.py                           # Flask: discussieboom-API + visualisatie op /
├── .gitignore                          # Negeert data/*.db, __pycache__, etc.
│
├── data/
│   └── propaganda_model.db             # SQLite database (niet in git)
│
├── releases/                           # M3.1: modelreleases (wél in git): per versie
│   ├── model-vX.Y.Z.json               #   onveranderlijk scores-snapshot
│   └── model-vX.Y.Z.md                 #   changelog met score-diff t.o.v. de vorige
│
├── missies/                            # Agent-missies: briefs + logs (M1.8/M1.9/M3.3)
│   ├── monitor_brief.md / scout_brief.md / redteam_brief.md
│   ├── audit_checklist.md              # M3.5: jaarlijkse audit (volgende: juni 2027)
│   └── logs/                           # rondelogs (queries, oogst, stance-balans)
│
├── web/
│   ├── template.html                   # BRON van de D3-visualisatie; / serveert dit direct,
│   │                                   #   data komt live via GET /api/graph_data (W5.1)
│   └── index.html                      # OPTIONELE statische export (generate_viz.py; veroudert,
│                                       #   bereikbaar als /static/index.html — niet bewerken)
│
├── scripts/
│   ├── init_db.py                      # Database aanmaken vanuit schema.sql
│   ├── seed_theoretical_model.py       # Basis: rollen + mechanismen (laag 1)
│   ├── seed_from_ai_source.py          # Basis: entiteiten + relaties (laag 2)
│   ├── seed_instantiations.py          # Vult instantiations uit de impliciete koppelingen (laag 1↔2)
│   ├── seed_draaideur_relaties.py      # Extra draaideur-relaties
│   ├── enrich_*.py                     # Verrijken van een bestaande DB (theorie + instanties)
│   ├── migrate_*.py                    # Schema-/datamigraties (backup-then-migrate)
│   ├── set_temporal_data.py            # Vult active_from/active_until op entiteiten/relaties
│   ├── generate_viz.py                 # Optionele statische export (web/index.html) uit de DB
│   └── register_source.py              # Registreer een academische bron via CLI
│
└── sources/                            # Bronmateriaal (teksten, transcripts)
    ├── README.md                       # Uitleg over bronmateriaal en naamgeving
    ├── AI/                             # AI-gegenereerde analyses
    │   └── propagandsmodel2.md         # Hoofdbron: "De Onzichtbare Architecten"
    ├── transcripts/                    # Uitgeschreven audio/video
    ├── articles/                       # Nieuwsartikelen, columns
    └── interviews/                     # Interview-transcripts
```

> De `seed_*`-scripts leggen de basis; de huidige DB-inhoud is daarna uitgebreid via de `enrich_*`- en `migrate_*`-scripts. Een volledige reconstructie draait dus seed → enrich → migrate (de migratiescripts maken telkens een backup `data/propaganda_model_backup_<timestamp>.db`).

---

## Gebruik

### Database opzetten

```bash
# Database aanmaken (verwijder eerst bestaande als je wilt herbeginnen)
rm -f data/propaganda_model.db
python3 scripts/init_db.py

# Theoretisch model laden (rollen + mechanismen)
python3 scripts/seed_theoretical_model.py

# Entiteiten en relaties laden uit bronanalyse
python3 scripts/seed_from_ai_source.py

# Klasse↔instantie-koppelingen vullen uit de impliciete koppelingen (voor de scoringsketen)
python3 scripts/seed_instantiations.py
```

> Bestaande database (met data) upgraden naar de scoringslaag: `python3 scripts/migrate_add_scoring_layer.py`
> (maakt eerst een backup, voegt `instantiations` toe en geeft `arguments` theorie-doelen).

### Bronnen registreren

```bash
python3 scripts/register_source.py \
    "Manufacturing Consent" \
    boek \
    "Herman, E.S. & Chomsky, N." \
    "Pantheon Books" \
    "1988-01-01"
```

### Queries

```sql
-- Alle relaties van een entiteit met scores
SELECT e1.name, r.relation_type, e2.name, r.certainty, r.influence
FROM relations r
JOIN entities e1 ON r.source_id = e1.id
JOIN entities e2 ON r.target_id = e2.id
WHERE e1.name = 'DPG Media'
ORDER BY r.influence DESC;

-- Alle argumenten bij een relatie, met citaties
SELECT a.stance, a.claim, a.weight, s.author, s.title, c.quote, c.page
FROM arguments a
LEFT JOIN citations c ON c.argument_id = a.id
LEFT JOIN sources s ON c.source_id = s.id
WHERE a.relation_id = 5
ORDER BY a.stance;

-- Meest verbonden entiteiten
SELECT e.name, e.type, COUNT(DISTINCT r.id) as relaties
FROM entities e
LEFT JOIN relations r ON e.id = r.source_id OR e.id = r.target_id
GROUP BY e.id
ORDER BY relaties DESC
LIMIT 10;

-- Relaties per filter/mechanisme
SELECT m.filter, m.name, COUNT(r.id) as aantal
FROM relations r
JOIN mechanisms m ON r.mechanism_id = m.id
GROUP BY m.filter, m.name
ORDER BY m.filter, aantal DESC;

-- Onzekere relaties met hoge invloed (onderzoeksprioriteit)
SELECT e1.name, r.relation_type, e2.name, r.certainty, r.influence
FROM relations r
JOIN entities e1 ON r.source_id = e1.id
JOIN entities e2 ON r.target_id = e2.id
WHERE r.certainty < 0.75 AND r.influence >= 0.55
ORDER BY r.influence DESC;

-- Alle bronnen met hun locaties
SELECT s.title, s.author, sl.location_type, sl.location
FROM sources s
LEFT JOIN source_locations sl ON sl.source_id = s.id
ORDER BY s.author;
```

---

## Huidige inhoud

| Onderdeel | Aantal |
|---|---|
| Rollen (theoretisch) | 35 |
| Mechanismen (theoretisch) | 126 |
| Emergente effecten (hyperedges) | 12 |
| Entiteiten (concreet) | 167 |
| Relaties (concreet) | 398 |
| Argumenten | 443 |
| Citaties | 212 |
| Bronnen | 67 |
| Bronlocaties | 57 |

> Let op: de meeste argumenten zijn automatisch gegenereerde `supporting`-onderbouwingen met status `ongecontroleerd` en nog grotendeels zonder citatie. Het aanvullen van citaties en het controleren van argumentstatus is openstaand werk.

### Top 10 meest verbonden entiteiten

| Entiteit | Type | Relaties |
|---|---|---|
| DPG Media | mediaorganisatie | 47 |
| NOS | omroep | 45 |
| Mediahuis | mediaorganisatie | 34 |
| RTL Nederland | omroep | 33 |
| de Volkskrant | mediaorganisatie | 28 |
| De Telegraaf | mediaorganisatie | 25 |
| AD (Algemeen Dagblad) | mediaorganisatie | 17 |
| ANP | persbureau | 16 |
| Bilderberg Groep | elite_netwerk | 15 |
| World Economic Forum | elite_netwerk | 15 |

---

## Hoe het model uitbreiden

### Nieuwe bron toevoegen

1. Plaats het bestand in `sources/` (juiste submap)
2. Registreer de bron: `python3 scripts/register_source.py "Titel" type "Auteur"`
3. Voeg locaties toe (URL, DOI, ISBN) via SQL of een script
4. Analyseer de tekst en voeg entiteiten, relaties en argumenten toe

### Argument toevoegen aan een relatie

Inhoud gaat sinds M0.6 uitsluitend via het bijdragepad (REST-API met een ingelogde
gebruiker of Bearer-token), nooit via directe SQL:

```bash
TOKEN=$(cat data/tokens/claude-code.token)   # eigen agent-account, nooit maxime.token
# Root-argument mét citatie in één call (citatiepoort tevreden)
curl -s -X POST localhost:5000/api/arguments \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"relation_id": 42, "stance": "contradicting",
       "claim": "De Volkskrant publiceerde kritisch Shell-dossier",
       "reasoning": "Als zelfcensuur dominant was, was dit dossier niet gepubliceerd.",
       "citations": [{"source_id": 3, "quote": "Het onderzoeksteam werkte zes maanden aan het dossier", "page": "pp. 12-15"}]}'
```

### Reactie op een bestaand argument (discussieboom)

Een reply draagt géén eigen doel en geen property (M1.1); een contradicting-reply is
een ondergraving ("argument klopt niet") en mag bronloos, met optioneel
`objection_type` — sinds juli 2026 een **vrij tekstveld** (de taxonomie-waarden
blijven het aanbevolen vocabulaire voor agents). Zet je een `objection_type`, dan is
`reasoning` **verplicht** (benoem wat er precies niet klopt): een kaal
categorie-label is zelf een loze aanklacht en wordt geweigerd (400).

```bash
curl -s -X POST localhost:5000/api/arguments \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"parent_argument_id": 15, "stance": "contradicting",
       "claim": "Eén casus draagt geen algemene regel",
       "reasoning": "Aangevochten stap: uit het ene Shell-dossier wordt een structurele conclusie getrokken.",
       "objection_type": "anekdote_als_regel"}'
```

### Argument over een entiteit of over de invloed-as

```bash
# Bewering over een entiteit
curl -s -X POST localhost:5000/api/arguments \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"entity_id": 1, "stance": "supporting",
       "claim": "DPG bezit >60% van de online commerciële nieuwsmarkt",
       "citations": [{"source_id": 12}]}'

# Invloed-as (M1.7): bewijs dat de invloed van relatie 42 sterk is
curl -s -X POST localhost:5000/api/arguments \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"relation_id": 42, "property": "influence", "stance": "supporting",
       "claim": "Adverteerderdruk leidde aantoonbaar tot het intrekken van de rubriek",
       "citations": [{"source_id": 5}]}'
```

### Certainty herberekenen

De `certainty` op een relatie kan periodiek worden herberekend als gewogen balans van alle supporting vs contradicting argumenten:

```sql
-- Voorbeeld: gemiddelde weight per stance voor een relatie
SELECT
    relation_id,
    AVG(CASE WHEN stance = 'supporting' THEN weight END) as avg_support,
    AVG(CASE WHEN stance = 'contradicting' THEN weight END) as avg_contra,
    COUNT(CASE WHEN stance = 'supporting' THEN 1 END) as n_support,
    COUNT(CASE WHEN stance = 'contradicting' THEN 1 END) as n_contra
FROM arguments
GROUP BY relation_id
HAVING n_contra > 0;
```

---

## Theoretische basis

| Werk | Auteur | Bijdrage |
|---|---|---|
| *Manufacturing Consent* (1988) | Herman & Chomsky | De vijf filters van het propagandamodel |
| *De Nederlandse Nieuwsfabriek* (2014) | Tabe Bergman | Toepassing op het Nederlandse medialandschap |
| *Je hebt het niet van mij, maar...* (2010) | Joris Luyendijk | Etnografie van de Haagse "stam" (Filter 3) |
| *The Making of an Atlantic Ruling Class* (1984) | Kees van der Pijl | Transnational Capitalist Class theorie |
| *Quaderni del Carcere* (1935) | Antonio Gramsci | Culturele hegemonie (Filter 5) |
| *Aandacht voor media* (2024) | WRR | Institutionele erkenning van de crisis |
| *Medialogica* (2003) | RMO | Wurggreep politiek↔media (emergent effect `medialogica`) |
| *Mediahype* (2004) | Peter Vasterman | Zelfversterkende nieuwsgolven (emergent effect `mediahype`) |
| *Diplomademocratie* (2011) | Bovens & Wille | Dominantie van hoogopgeleiden in alle instituties (emergent effect `ideologische_homofilie`) |
| *Haagse waakhonden* (2001) | J.C.P.M. Vis (RUG) | Stemvoorkeur parlementair journalisten: D66/GL fors oververtegenwoordigd (emergent effect `ideologische_homofilie`, halo `sociologische_homogeniteit`) |
| *Journalists in the Netherlands* (2016) | Liesbeth Hermans (Worlds of Journalism Study) | Samenstelling en rolopvatting van het journalistencorps (halo `sociologische_homogeniteit`) |
| *Outsourcing the news?* (2016) | Jelle Boumans | Kwantificering ANP-afhankelijkheid (emergent effect `schijnpluriformiteit`) |
| *Agressie en bedreiging richting journalisten* (2021) | PersVeilig / I&O Research | Collectief chilling effect (emergent effect `verkillingsspiraal`) |
| *Digital News Report Nederland* (2024/2025) | Commissariaat voor de Media | Fragmentatie en nieuwsmijding (halo `publieksfragmentatie`) |
