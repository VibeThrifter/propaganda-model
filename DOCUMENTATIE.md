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

> De eigendomskant kent geen directe `mediaeigenaar → mediaorganisatie`-pijl: de eigenaarsinvloed loopt strikt via de controleketen `mediaeigenaar → administratiekantoor → overnamevehikel → mediaorganisatie`. De eigenaar heeft daarmee **één uitgaande eigendomspijl — naar de STAK** — die alle eigenaar-niveau-mechanismen draagt (`familiezeggenschap`, `acquisitiestrategie`, `cross_media_eigendom`, en de structurele `eigendomsconcentratie`). De STAK certificeert vervolgens de holding (`certificaatconstructie`: vier effecten — stemmacht-concentratie, cash/controle-ontkoppeling, overnamebestendigheid, UBO-afscherming), en de holding bezit de titel en legt het rendementsregime op (`holdingconstructie`, `winstmaximalisatie`). De redactionele hefbomen liggen ná de keten, op org-niveau: de `mediaorganisatie` benoemt de hoofdredacteur (`benoemingspolitiek`) en stelt het redactiebudget vast (`redactioneel_budgetcontrole`, binnen het door de holding opgelegde rendementsregime). De eigenaar raakt de redactionele laag dus **nooit direct** — zijn invloed is volledig gemedieerd via de keten; alleen zijn persoonlijke elite-netwerk (`mediaeigenaar_elite_netwerk`, Eigendom + Ideologie; thema Elite-netwerk) loopt rechtstreeks. De `borgingsstichting` zet zich als tegenmacht precies op het benoemingspunt (`onafhankelijkheidsborging` → hoofdredacteur). De macro-concentratie zelf is een emergent systeemkenmerk — zie het thema *Systemisch* onder [Thema's: dwarsverbanden](#themas-dwarsverbanden).

### Filter 2: Advertentie
Media zijn financieel afhankelijk van adverteerders, wat een structurele voorkeur creëert voor content die het consumentistische wereldbeeld bevestigt. De `adverteerder` is geen losse actor maar de **advertentie-hoed van een `belanghebbende`**: dezelfde corporate of sector die elders lobbyt of procedeert, zet hier het advertentiebudget in als drukmiddel (`adverteren_als_belang`). Zie *Systeemactoren* voor de principaal-superklasse die door alle filters heen werkt.

**Rollen:** `adverteerder` (instrument-rol van `belanghebbende`)
**Mechanismen:** `adverteren_als_belang`, `advertentiedruk`, `commerciele_afhankelijkheid`, `supportive_selling_environment`, `stakeholder_capitalism_frame`

### Filter 3: Sourcing
Economische druk dwingt redacties tot afhankelijkheid van een beperkt aantal routineuze bronnen: het ANP, de overheid, en door de elite gefinancierde denktanks. Toegang (*access*) is hierbij zelf een schaarse hulpbron: wie aan tafel mag krijgt een podium, wie fundamenteel afwijkt verliest die toegang geruisloos (`toegangsdisciplinering`).

Het **persbureau** (ANP) is binnen dit filter de *industriële versterker*: objectief in HÓE het schrijft (zonder oordeel), maar door tijd, geld, klantvraag en routines structureel selectief in WÁT het schrijft — en het propagandamodel gaat juist over dat WÁT. Drie routines drijven die selectie: leunen op de agenda's van officiële instanties — rechtbank, Kamer, politie, persconferenties (`persbureau_brongebondenheid`); de gebundelde vraag van betalende klant-redacties die de "waan van de dag" opschaalt ten koste van structureel ondervraagde thema's (`klantvraag_persbureau`); en de snelheids-/verifieerbaarheidseis die het officieel-controleerbare bevoordeelt boven trage onderzoeksjournalistiek (`verifieerbaarheidsroutine`). Via `pakketjournalistiek` wordt die selectie vervolgens landelijk uniform doorgegeven. De landschapsbrede uitkomst — veel merknamen, één nieuwsstroom, terwijl het publiek meerstemmigheid ervaart — is gemodelleerd als emergent effect `schijnpluriformiteit` (Boumans, UvA 2016: ca. tweederde van het online nieuws in 2014 ANP-gebaseerd, veelal vrijwel integraal overgenomen). De structurele scheefgroei tussen de zendende en de checkende kant (±150.000 communicatieprofessionals tegenover ±15.000 journalisten; UvA/CBS) is het emergente effect `voorlichtingsovermacht`.

Achter de bronnen zitten **principalen** die de sourcing-stroom voeden via instrumenten — dezelfde logica, twee gedaanten. Corporate: een `belanghebbende` (bedrijf/sector/branche) zet zijn belang om in mediabeeld via lobbyisten, brancheorganisaties en denktanks (`belangenbehartiging`); de soorten lobby verschillen (corporate-sectoraal, branche/koepel, ideologisch/NGO) en goed georganiseerde belangen zijn structureel oververtegenwoordigd. Politiek: de voorlichter heeft altijd een principaal — een **politieke `partij`** (die via `gecoordineerde_voorlichting` één afgestemde boodschap langs de partijlijn levert en via `partijlijn` haar politici aanstuurt) **óf een instituut/ministerie** (`gezagsinstituut`, Rijksvoorlichtingsdienst, departementale woordvoerders, via `institutionele_voorlichting`). De voorlichter en de politicus zijn bewust *aparte* rollen — de toegangs-poortwachter versus de bron — en het smeermiddel is *access*: de off-the-record Nieuwspoort-code "je hebt het niet van mij, maar..." (Luyendijk), die zelfcensuur wekt omdat niemand hem durft te breken.

Naast deze principalen gelden officiële instituties zelf als gezaghebbende routinebron: een `gezagsinstituut` (CPB, DNB, CBS, RIVM, WRR, ministerie, OM) is een **primaire definieerder** (Hall) wiens cijfers en rapporten als neutraal feit gelden en de agenda zetten (`institutioneel_gezag`); de `gezagsexpert` (de "onafhankelijke" hoogleraar/econoom/deskundige) legitimeert de consensus (`expert_legitimatie`).

Een grensgeval tussen Sourcing en Flak is `inlichtingen_cooptatie`: een inlichtingendienst (AIVD/MIVD) werft journalisten als bron of agent. Gedocumenteerd door NRC/de Volkskrant (2024) — van 32 benaderde redacteuren/correspondenten meldde ~de helft een verzoek; een intern AIVD-document noemde 8 journalisten onder 21 "bronnen en agenten". Het compromitteert de onafhankelijkheid van de bronvergaarder (Sourcing) en ondermijnt de geloofwaardigheid van het vak (Flak). Dit is geen emergent veld-effect maar een *bewezen, doelgerichte* ingreep — en hoort daarom expliciet in het model. (Op instantieniveau is bewust nog géén specifieke dienst→journalist-relatie opgenomen: *dát* een dienst journalisten werft is bewezen, *welke* dienst wie benaderde niet — het praktijkmodel wacht op een gedocumenteerd, specifiek geval. Zo kan het theoretische model wél een verband met geheime diensten dragen terwijl de praktijklaag leeg blijft tot het bewijs er is.)

**Rollen:** `persbureau`, `journalist`, `voorlichter`, `lobbyist`, `denktank`, `belanghebbende`, `gezagsinstituut`, `gezagsexpert`
**Mechanismen:** `bron_afhankelijkheid`, `pakketjournalistiek`, `persbureau_brongebondenheid`, `klantvraag_persbureau`, `verifieerbaarheidsroutine`, `expert_framing`, `pr_subsidie`, `toegangsdisciplinering`, `belangenbehartiging`, `gecoordineerde_voorlichting`, `institutionele_voorlichting`, `partijlijn`, `institutioneel_gezag`, `expert_legitimatie`, `journalist_bronrelatie`, `politicus_als_bron`, `voorlichter_informatiefilter`, `lobbyist_naar_journalist`, `lobbyist_naar_politicus`, `denktank_financiering_bias`, `denktank_levert_expert`, `denktank_naar_politiek`, `denktank_naar_persbureau`, `woo_obstructie`, `draaideur_politiek_institutie`, `inlichtingen_cooptatie`

### Filter 4: Flak
Disciplineringsmechanismen die journalisten ontmoedigen om van de geaccepteerde lijn af te wijken: juridische dreiging, publieke aanvallen, etikettering, en interne zelfcensuur. De hedendaagse *cancelling* — een gast die iets onwelgevalligs zegt en niet meer wordt uitgenodigd — valt hier onder via `deplatforming`. Het uiterste van het flak-spectrum is fysiek én online `geweld_intimidatie` tegen journalisten; de bron daarvan is bewust diffuus gelaten (geen vaste principaal), passend bij het emergente — niet samenzweerderige — karakter van dát mechanisme. Externe flak en interne redactiecultuur versterken elkaar bovendien in een vicieuze cirkel — empirisch gedocumenteerd door PersVeilig/I&O (2021: 8 op de 10 journalisten ervaart agressie of bedreiging, 16% past de berichtgeving aan, ±15% publiceert soms niet) — gemodelleerd als emergent effect `verkillingsspiraal`: het collectieve chilling effect dat de individuele zelfcensuur-halo overstijgt.

Niet álle flak is echter diffuus: een hedendaagse, *wél* doelgerichte en gedocumenteerde variant is `statelijke_inhoudsmoderatie` — een overheid (bv. het ministerie van BZK met trusted-flagger-status bij vijf platforms) of de Europese Commissie (Code of Practice, EU Internet Forum 'borderline content'-handboek dat o.a. anti-elite en meme-content benoemt) zet techplatforms onder druk om legale maar ongewenste uitingen te modereren of demoten. Anders dan `deplatforming` (één mediagast) werkt dit digitaal en publieksbreed, op platformniveau, en raakt het ook Ideologie (spectrumbewaking). Het is het schoolvoorbeeld van bewezen sturing binnen een verder emergent systeem.

**Rollen:** _(geen — flak is een functie, geen identiteit; de mechanismen werken op bestaande rollen)_
**Mechanismen:** `juridische_dreiging`, `publieke_aanval`, `deplatforming`, `etikettering`, `zelfcensuur`, `geweld_intimidatie`, `statelijke_inhoudsmoderatie`

### Filter 5: Ideologie
Het overkoepelende filter: een denkkader dat als "gezond verstand" wordt gepresenteerd (Gramsci's culturele hegemonie). In de Nederlandse context is die hegemonie een specifieke combinatie — **cultureel links-progressief** (een *politics of recognition*: diversiteit, identiteit) én **economisch neoliberaal**, pro-Atlantisch: wat Nancy Fraser "progressief neoliberalisme" noemt. Elite-fora synchroniseren dit wereldbeeld, en **universiteiten en journalistiekopleidingen** (`kennisinstituut`) reproduceren het als neutrale, wetenschappelijke vanzelfsprekendheid: ze socialiseren de journalisten (`academische_socialisatie`) én leveren de `gezagsexpert`s (`academische_autoriteit`). Doordat journalist én "onafhankelijke" bron uit dezelfde instituten komen, ontstaat **ideologische homofilie** — empirisch zichtbaar in de sterk afwijkende stemvoorkeur van NL-journalisten (D66/GroenLinks fors oververtegenwoordigd t.o.v. de bevolking; parlementair journalisten: D66 27% vs. 9% landelijk, 'Haagse waakhonden') — gemodelleerd als het gelijknamige emergente effect `ideologische_homofilie`. De hegemonie-*reproductie* reikt verder dan de media: het `kennisinstituut` vormt de hele hoogopgeleide elite die álle instituties bevolkt (Bovens & Wille, *diplomademocratie*) — politici (`academische_socialisatie_politiek`), denktanks (`academische_orthodoxie_denktank`), de "primaire definieerders" als CPB/DNB (`academische_orthodoxie_instituut`) en opiniemakers (`academische_vorming_opinie`). Afwijking verschijnt niet als ander standpunt maar als gebrek aan kennis of als "activisme". (De *academisch criticus die het filtersysteem blootlegt* is bewust geen aparte rol: in NL een marginaal, niet-bepalend verschijnsel — de relevante academische kracht is juist hegemonie-*dragend*.)

**Rollen:** `elite_forum`, `columnist_opiniemaker`, `kennisinstituut`
**Mechanismen:** `schijndebat`, `ideologische_synchronisatie`, `elite_referentiekader`, `spectrum_bewaking`, `journalist_socialisatie`, `academische_socialisatie`, `academische_socialisatie_hoofdredacteur`, `preselectie_hoofdredacteur`, `politicus_als_ideoloog`, `columnist_als_hegemon`, `omroepverzuiling`, `omroepsignatuur`, `sociologische_homogeniteit`, `academische_autoriteit`, `academische_socialisatie_politiek`, `academische_orthodoxie_denktank`, `academische_orthodoxie_instituut`, `academische_vorming_opinie`, `publieksfragmentatie`

<a id="themas-dwarsverbanden"></a>
### Thema's: dwarsverbanden
Sommige mechanismen vormen herkenbare *families* die dwars door de vijf filters heen lopen — ze laten zich niet onder één filter vangen omdat ze er meerdere tegelijk aandrijven. Vroeger zat dit in de noodcategorie `cross_filter`; nu draagt elk mechanisme gewoon **al** zijn filters (multi-filter), en de families zitten op een aparte, los selecteerbare **thema-as** (`mechanism_themes`, many-to-many — een mechanisme mag in meerdere thema's zitten). Een thema is dus géén filter en géén subgroep: het is een analytische dwarsdoorsnede.

De **draaideur** illustreert het principe: personeel circuleert tussen politiek, bedrijfsleven, media/journalistiek en lobby/PR, en raakt per spaak een ánder filter — politicus → bedrijfsleven is winstbelang (**Eigendom**), → hoofdredactie is **Ideologie**, → lobby/PR is **Sourcing**, → toezicht is **Flak** (regulatory capture). Het thema "Draaideur" houdt die spaken bij elkaar, terwijl de filter-tags het inhoudelijke kanaal benoemen.

De zeven thema's:

- **Draaideur** — circulatie van personeel/macht (politicus → bedrijfsleven/lobby/toezicht/hoofdredactie, journalist ↔ politiek).
- **Elite-netwerk** — synchronisatie van wereldbeeld in elite-fora (Bilderberg/WEF/ERT); combinatie van lobby (Sourcing) en Ideologie. Zeldzaam publiek spoor: de VN-herstelterm "build back better" (Sendai-raamwerk, 2015) werd na WEF- en OESO-publicaties van begin juni 2020 binnen maanden de herstelslogan van meerdere westerse regeringsleiders — gedocumenteerde vocabulaire-convergentie via gedeelde circuits, geen bewijs van regie (zie de argumenten bij `ideologische_synchronisatie`).
- **Geldstromen** — agenda-gebonden geld dat buiten eigendom én advertentie om naar partij of titel stroomt (partij-/mediafinanciering, groeileningen, platformfinanciering), plus de neutrale tegenpool `projectfinanciering_journalistiek`.
- **Platform/digitaal** — techplatforms en algoritmes (filtering, socialisatie, verdienmodeldruk, advertentieconcentratie).
- **Systemisch** — emergente, zelfversterkende systeemkenmerken (eigendomsconcentratie, economische terugkoppeling, emergente bias, homeostase).
- **Publiek omroepbestel** — de bestel-specifieke krachten (ledeneis, intekensturing, erkenningverlening, omroepsignatuur/-verzuiling, Ster); spant Eigendom + Ideologie + Advertentie.
- **Kennis & expertise** — het expert-/autoriteitscomplex (academische vorming/orthodoxie, denktanks, expert-framing/-legitimatie); spant Sourcing + Ideologie.

### Uitbreiding B: Tegenmacht
Het model is niet deterministisch: het modelleert óók de krachten die het filtersysteem begrenzen of doorbreken. Zulke doorbraken zijn mogelijk, maar vaak incidenteel en onder druk (zie ook `toezicht_tandeloosheid`).

**Rollen:** `onderzoeksjournalist`, `klokkenluider`, `parlementair_controleur`, `toezichthouder`, `vakbond_media`, `burgerinitiatief`, `borgingsstichting`, `alternatief_medium`
**Mechanismen:** `onderzoeksjournalist_doorbraak`, `klokkenluider_doorbraak`, `onafhankelijk_medium_tegenwicht`, `parlementaire_controle`, `toezichthouder_interventie`, `toezicht_tandeloosheid`, `vakbond_bescherming`, `burgerinitiatief_druk`, `onafhankelijkheidsborging`, `redactiestatuut_borging`, `continuiteitsborging`, `afgedwongen_borging`, `projectfinanciering_journalistiek`

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
| `roles` | Abstracte rollen in het medialandschap | name, category (`eigendom`/`advertentie`/`sourcing`/`flak`/`ideologie`/`systeemactor`/`tegenmacht`/`overig`), description, examples |
| `mechanisms` | Processen waarmee rollen invloed uitoefenen | name, filter (primair filter; vijf filters + `tegenmacht`/`overig`), mechanism_type (`structureel`/`procedureel`/`psychologisch`/`economisch`/`juridisch`/`technologisch`/`discursief`), **aard** (`direct`/`veld_eigenschap` live; `indirect`/`veld_instantiatie` deprecated — zie [Aard: direct & systemisch](#aard-direct--systemisch)), description, effect, source_role_id, target_role_id |
| `mechanism_filters` | Multi-filter: alle filter-tags per mechanisme (≥1, incl. primair) | mechanism_id, filter |
| `mechanism_themes` | Thema-as: dwarsverbanden per mechanisme (0+) | mechanism_id, theme (`draaideur`/`elite_netwerk`/`geldstromen`/`platform`/`systemisch`/`omroepbestel`/`kennis_expertise`/`benoemingsketen`) |
| `emergent_effects` | Emergent effect als **hyperedge**: systeemeigenschap uit het samenspel van een gróép rollen (geen bron→doel-pijl) | name, label, category, description, effect |
| `emergent_effect_members` | Koppeltabel: welke rollen dragen samen een emergent effect | emergent_effect_id, role_id |

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
| `sources` | Academische bronnen (boeken, artikelen, rapporten) | title, author, source_type, publisher, date_published, language, summary, reliability (`primair`/`academisch`/`institutioneel`/…), processed |
| `source_locations` | Meerdere toegangspunten per bron | source_id, location_type (url/file/doi/isbn/arxiv/handle/archive_url), location, accessed_at, notes |

### Argumenten & citaties (discussieboom)

| Tabel | Beschrijving | Velden |
|---|---|---|
| `arguments` | Discussieboom: argumenten op een praktijk-target (relatie/entiteit) óf een theorie-target (rol/mechanisme = literatuuronderbouwing), met nesting | relation_id / entity_id / role_id / mechanism_id (minstens één), parent_argument_id (NULL=root), property/property_value (optioneel), stance, claim, reasoning, weight, status (`ongecontroleerd` default), contributed_by |
| `citations` | Bronvermeldingen per argument | argument_id, source_id, quote, page, section, context |
| `edit_log` | Auditlog van wijzigingen (aanmaak, statuswijziging) | table_name, record_id, action (`created`/`updated`/`deleted`/`verified`/`disputed`), changed_by, old_value, new_value, reason |

Argumenten vormen een boomstructuur:
- **Root-argumenten** (`parent_argument_id = NULL`) hangen direct aan een relatie of entiteit
- **Reacties** (`parent_argument_id = <id>`) reageren op een ander argument
- Elk argument kan gericht zijn op een **relatie** (`relation_id`) of een **entiteit** (`entity_id`), minstens één is verplicht

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

De handmatige `certainty` blijft als **prior** bestaan, maar de score die het model gebruikt wordt afgeleid uit de bewijslast (zie hieronder). `influence` blijft handmatig.

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

> Let op: dat een mechanisme thema `systemisch` draagt zegt niets over zijn `aard`. `eigendomsconcentratie`
> is thematisch systemisch, maar elke afzonderlijke edge (DPG → Het Parool) is een lokaal eigendomsfeit —
> dus `direct`. Het emergente zit daar in de *optelsom* (de concentratie), niet in de losse edge.

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
te vangen is (eigen tabellen `emergent_effects` + `emergent_effect_members`; bv. *fabricage van consensus*,
*zelfversterkende homeostase*). Ook **terugkoppellussen tussen meerdere rollen** horen hier (medialogica,
verkillingsspiraal, economische feedback-loop): een lus is geen toestand van één node en geen gerichte
dyade — elke schakel is tegelijk oorzaak en gevolg. Het verschijnt als een transparant **goud veld** rond
de leden, met label, hoverbaar/klikbaar (het detailpaneel toont het samenspel).

De twaalf emergente effecten, met de literatuur die de compositie benoemt:

| effect | kern | literatuur |
|---|---|---|
| `fabricage_van_consensus` | pro-elite bias uit het samenspel van de vijf filters | Herman & Chomsky |
| `zelfversterkende_homeostase` | afwijkingen worden gedempt, status quo reproduceert zichzelf | Bergman; systeemtheorie-duiding |
| `haagse_stam` | politici, voorlichters, lobbyisten en journalisten als één stam | Luyendijk |
| `toeschouwersdemocratie` | het publiek ziet de frontstage-opvoering, de afweging is backstage | Luyendijk |
| `lobbymakelaardij` | de lobbyist regisseert journalist én politicus namens een onzichtbare opdrachtgever | Luyendijk |
| `schijnpluriformiteit` | veel merknamen, één ANP-nieuwsstroom; pluriformiteit als façade | Boumans (2016): ±66% online nieuws ANP-gebaseerd |
| `ideologische_homofilie` | journalist, expert en politicus uit dezelfde academische kring; bevestiging oogt als verificatie | Bovens & Wille (2011); 'Haagse waakhonden' |
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
   `role_id` = bronrol, `property = 'indirecte_invloed_op'`, `property_value` = naam van de doelrol,
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

**Laag A — bewijskracht per argument:** `weight × statusfactor × bronfactor`. De statusfactor schaalt
op verificatiestatus (geverifieerd 1,0 → betwist 0,25); de bronfactor op de betrouwbaarste citatie.
Brongewichten: `academisch 1,0 · primair 0,95 · institutioneel 0,85 · kwaliteitsjournalistiek 0,70 ·
regulier 0,50 · opinie 0,35 · grijs 0,20 · onbeoordeeld 0,15`.

**Laag B — afgeleide praktijkscore per relatie/entiteit:** `steun / (steun + tegen + k)`, waar steun en
tegen de optelsom van de bewijskracht van de supporting- resp. contradicting-argumenten zijn. Zonder
argumenten valt het terug op de handmatige `certainty` (prior). Een entiteit zonder eigen argumenten
erft het gemiddelde van haar relaties.

**Laag C — theoriescore per rol/mechanisme**, uit twee onafhankelijke bewijslijnen:
- **Praktijk (bottom-up):** geloofwaardigheid-gewogen aggregatie over de gekoppelde instanties, met
  volume-verzadiging `gem_cert × n/(n+k)` — veel goed-onderbouwde voorbeelden tillen de klasse op.
  De **sterkte** is de geloofwaardigheid-gewogen gemiddelde invloed van die instanties.
- **Literatuur (top-down):** argumenten/citaties die *direct* op de rol/het mechanisme hangen
  (`arguments.role_id`/`mechanism_id`). Zo onderbouwt bijvoorbeeld Luyendijk's *Je hebt het niet van
  mij* een mechanisme als bronafhankelijkheid; het gewicht volgt uit de `reliability` van die bron.

De twee lijnen worden gecombineerd met een **noisy-OR**: `geloofwaardigheid = 1 − (1−literatuur)(1−praktijk)`
— sterke literatuur óf veel geloofwaardige praktijkvoorbeelden maken de theorie geloofwaardiger, samen
nog meer. In het theoriemodel codeert de node-grootte/lijndikte de **sterkte**; het detailpaneel toont
beide scores met de opsplitsing literatuur ⊕ praktijk. Alle constanten staan boven in `scoring.py`.

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
├── web/
│   ├── template.html                   # BRON van de D3-visualisatie (handmatig bewerken)
│   └── index.html                      # GEGENEREERD door generate_viz.py (niet bewerken)
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
│   ├── generate_viz.py                 # Regenereert web/index.html uit de DB
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
| Mechanismen (theoretisch) | 119 |
| Emergente effecten (hyperedges) | 12 |
| Entiteiten (concreet) | 162 |
| Relaties (concreet) | 392 |
| Argumenten | 413 |
| Citaties | 144 |
| Bronnen | 51 |
| Bronlocaties | 43 |

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

```sql
-- 1. Root-argument op een relatie
INSERT INTO arguments (relation_id, stance, claim, reasoning, weight)
VALUES (42, 'contradicting',
        'De Volkskrant publiceerde kritisch Shell-dossier',
        'Als zelfcensuur dominant was, zou dit dossier niet gepubliceerd zijn.',
        0.40);

-- 2. Voeg citatie(s) toe
INSERT INTO citations (argument_id, source_id, quote, page, section)
VALUES (last_insert_rowid(), 3,
        'Het onderzoeksteam werkte zes maanden aan het dossier',
        'pp. 12-15',
        'Redactioneel verantwoording');
```

### Reactie op een bestaand argument (discussieboom)

```sql
-- Tegenargument op argument #15
INSERT INTO arguments (relation_id, parent_argument_id, stance, claim, reasoning, weight)
VALUES (42, 15, 'supporting',
        'Dit was een uitzondering die de regel bevestigt',
        'Het Shell-dossier was het enige kritische stuk in 5 jaar. Structurele zelfcensuur sluit incidentele doorbraken niet uit.',
        0.55);
```

### Argument over een entiteit

```sql
-- Bewering over een entiteit (bijv. "Is DPG Media een monopolist?")
INSERT INTO arguments (entity_id, stance, claim, reasoning, weight)
VALUES (1, 'supporting',
        'DPG bezit >60% van de online commerciële nieuwsmarkt',
        'Volgens ACM marktanalyse 2023 is DPG de dominante speler.',
        0.80);
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
| *Outsourcing the news?* (2016) | Jelle Boumans | Kwantificering ANP-afhankelijkheid (emergent effect `schijnpluriformiteit`) |
| *Agressie en bedreiging richting journalisten* (2021) | PersVeilig / I&O Research | Collectief chilling effect (emergent effect `verkillingsspiraal`) |
| *Digital News Report Nederland* (2024/2025) | Commissariaat voor de Media | Fragmentatie en nieuwsmijding (halo `publieksfragmentatie`) |
