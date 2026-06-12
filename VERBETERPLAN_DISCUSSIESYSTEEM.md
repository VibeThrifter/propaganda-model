# Verbeterplan: discussieboom & scoringsketen

**Status: in uitvoering — Fase 0 is gebouwd en geverifieerd op 12 juni 2026 (zie §9;
alleen het M0.4-slotcriterium wacht op de 6 theorie-kandidaten uit `BACKFILL_REVIEW.md`).
Fase 1 en verder: nog niet gestart.**
Geschreven juni 2026 na een audit van schema, `scoring.py`, `server.py` en de live database. Doel: het discussiesysteem dat nodes,
edges en systeemeffecten onderbouwt robuuster en wetenschappelijker maken, en het klaarmaken
voor open bijdragen door gebruikers én agents. De domeinspec blijft `DOCUMENTATIE.md`; dit
document is de routekaart erbovenop.

---

## 1. Oordeel in het kort

**Het skelet is goed; de spieren ontbreken.** De architectuur is bovengemiddeld doordacht:
twee onafhankelijke score-assen (certainty/influence), drie expliciete lagen (theorie →
praktijk → bewijs), een bronhiërarchie naar Wikipedia-model, verificatiestatussen, en — echt
zeldzaam — de padclaim-eis dat *samengestelde* invloed zijn eigen bewijs nodig heeft omdat
invloed niet transitief is. Dat ontwerp hoeft niet vervangen te worden.

Wat het systeem nu níét doet: discrimineren. Vrijwel elke kracht-onderscheidende factor staat
op zijn default, er is geen georganiseerde tegenspraak, de boomstructuur wordt niet gebruikt
(en zou verkeerd geteld worden als hij wél gebruikt werd), de twaalf meest verstrekkende
claims (de hyperedges) vallen volledig buiten de bewijsketen, en er zit geen enkele poort
tussen "iemand POST iets naar de API" en "het telt mee in de score". De huidige scores meten
daardoor vooral *vlijt van de invuller*, niet *overlevingskracht van de claim*.

### Gezondheidsfoto (live DB, juni 2026)

| Meting | Stand | Betekenis |
|---|---|---|
| Stance-verdeling argumenten | 414 supporting / 7 contradicting / 6 contextual | 97% steun: monocultuur |
| Verificatiestatus | 419 van 427 `ongecontroleerd` | statusfactor discrimineert niet |
| Argumenten zonder citatie | 306 van 427 (72%) | bronfactor zit meestal op de ondergrens 0,30 |
| Relaties zonder argumenten | 60 van 394 (15%) | vallen terug op handmatige prior |
| Relaties zonder `mechanism_id` | 114 van 394 (29%) | theoriekoppeling is vrijwillig |
| Relaties mét mechanisme, zonder `instantiations`-rij | 10 | onzichtbaar voor de theoriescore (laag C) |
| Entiteiten zonder instantiatie / zonder primary_role | 23 / 13 van 163 | idem |
| Replies (`parent_argument_id` gevuld) | 0 van 427 | de "boom" is in de praktijk plat |
| Citatie-concentratie | top-3 bronnen = 49 van 168 citaties (29%) | Bergman, Luyendijk, Herman & Chomsky — alle drie pleitbezorgers van het model |
| Hyperedges met een bewijslijn | 0 van 12 | `arguments` kan geen emergent effect targeten |
| Live DDL vs `schema.sql` | gedrift | zie Z9 |

---

## 2. Diagnose: tien zwaktes

### Z1 — Monocultuur van steun
`steun / (steun + tegen + k)` (laag B) is alleen informatief als tegenspraak een eerlijke kans
heeft gehad. Met 7 contradicting-argumenten op 427 meet de ratio geen overlevingskracht maar
verzamelijver. Wetenschappelijk gezien is dit bevestiging-door-opsomming; een claim die nooit
is aangevallen hoort niet hetzelfde te scoren als een claim die aanvallen heeft overleefd.

### Z2 — Alles staat op defaults, behalve het zelfgekozen gewicht
72% van de argumenten heeft geen citatie (bronfactor 0,30), 98% is ongecontroleerd
(statusfactor 0,50). De enige factor die wél varieert is `weight` — en die wordt door de
*inbrenger zelf* gezet, zonder rubric of tweede beoordelaar. Netto: de score is grotendeels
zelfgerapporteerde kracht maal een constante. De zorgvuldig ontworpen factoren bestaan, maar
doen geen werk.

### Z3 — De boom telt niet (en zou verkeerd tellen)
`stance` is per definitie relatief aan de *parent* ("bevestigt/weerspreekt de
parent-bewering"), maar `compute_all_scores` aggregeert plat op target-id. Zodra iemand de
boom echt gebruikt ontstaat een tekenfout: een supporting-reactie op een
contradicting-argument telt — als hij een `relation_id` meekrijgt — als steun *voor de
relatie*, terwijl hij de tegenwerping versterkt; krijgt hij geen target mee, dan is hij
onzichtbaar voor de score. Dat het nog niet misgaat komt alleen doordat er nul replies zijn:
het kernidee van het systeem (discussie!) is nu niet score-dragend.

### Z4 — Onafhankelijkheid van bewijs is niet gemodelleerd
Optellen van bewijskracht (laag B) en de noisy-OR (laag C) veronderstellen *onafhankelijke*
bewijslijnen. Tien argumenten uit hetzelfde boek zijn echter geen tien bewijzen. De top-3
bronnen leveren 29% van alle citaties en zijn alle drie pleitbezorgers van het propagandamodel
— begrijpelijk voor de literatuurlaag, maar het systeem kan een claim die op één broncluster
drijft niet onderscheiden van een claim met vijf onafhankelijke lijnen. Er is ook geen
waarborg tegen circulariteit: de eigen extractie-analyses (`sources/AI/*.md`) staan nu terecht
níét als bron geregistreerd, maar niets houdt dat tegen.

### Z5 — Hyperedges en halo-sterkte vallen buiten de bewijsketen
`arguments` heeft geen `emergent_effect_id`; de twaalf hyperedges (fabricage van consensus,
homeostase, medialogica …) — juist de meest verstrekkende claims van het model — hebben dus
geen discussieboom, geen geloofwaardigheid en geen sterkte. Halo's kunnen als mechanisme wél
argumenten dragen, maar hun *sterkte* heeft geen gedefinieerde bewijslijn. Precies het deel
van het model dat het meest op "interpretatie" leunt, is het minst toetsbaar gemaakt.

### Z6 — Theoriekoppeling is een conventie, geen regel
De bedoeling is dat elke praktijk-node/edge aan een theorie-element hangt (en zo de
bottom-up-score voedt). In werkelijkheid: 114 relaties zonder mechanisme, 23 entiteiten zonder
instantiatie, en 10 relaties die wél een `mechanism_id` hebben maar geen `instantiations`-rij
— die laatste tellen stilletjes niet mee in laag C, wat de theoriescore vertekent zonder dat
iemand het ziet.

### Z7 — Schijnprecisie: puntscores zonder onzekerheid of gevoeligheid
Een geloofwaardigheid van 0,80 op basis van één instantie oogt identiek aan 0,80 op basis van
twintig. Er zijn geen intervallen, geen leave-one-out ("wat gebeurt er als deze ene bron
wegvalt?"), en de constanten (`K_AGG=5`, statusfactoren, brongewichten) zijn redelijk gekozen
maar onverdedigd en nooit op gevoeligheid getest.

### Z8 — Geen poort tussen bijdrage en score
`POST /api/arguments` schrijft direct in de live DB en het argument telt *onmiddellijk* mee
(status `ongecontroleerd` = factor 0,50 > 0). Geen authenticatie, geen review-stap, geen rate
limit, geen duplicaatdetectie; `contributed_by` is vrije tekst. Voor de geplande openstelling
is dit de showstopper: score-manipulatie is triviaal (100 ongecontroleerde steun-argumenten
zonder bron verschuiven elke score).

### Z9 — Schema-drift: de live DB en `schema.sql` zijn uit elkaar gegroeid
De live `arguments`-tabel is ooit herbouwd zónder CHECKs: stance, status en property
accepteren elke string, en de FK op `parent_argument_id` is weg. Omgekeerd kent
`schema.sql` de property-waarde `indirecte_invloed_op` niet (een verse build zou de 18
padclaims weigeren) en mist het de kolommen `active_from`/`active_until`/`active` op
entities/relations die `server.py` wél schrijft — een verse build breekt dus
`POST /api/entities`. Validatie leeft nu alleen in `server.py`, terwijl migratiescripts er
omheen schrijven. Symptoom van het ontbreken van elke vorm van CI.

### Z10 — Provenance van agent-bijdragen
Het corpus is grotendeels door agents gebouwd (de `modelreview-*`-tags; 305 argumenten hebben
zelfs geen `contributed_by`). Er is geen onderscheid mens/agent, geen modelversie, en geen
regel dat een agent-claim herleidbaar moet zijn naar een door mensen verifieerbare bron.
Risico zodra agents vrij mogen bijdragen: confabulatie wordt bewijs, en een agent kan in
principe zijn eigen argument op `geverifieerd` zetten.

---

## 3. Wat al goed is (behouden en uitbouwen)

- **Twee onafhankelijke assen** (certainty: "bestaat het?" / influence: "doet het ertoe?") —
  veel volwassener dan één waarheidsgetal.
- **Drie lagen met expliciete koppeltabel** (`instantiations` met exemplariteit): theorie
  wint geloofwaardigheid *uit* praktijkvoorbeelden, met volume-verzadiging tegen
  voorbeelden-stapelen.
- **Padclaims**: de eis dat een afgeleide pijl A ⇢ C zijn eigen bewijs heeft (invloed is niet
  transitief) is wetenschappelijk de sterkste ontwerpbeslissing in het systeem. Hetzelfde
  principe gaan we hergebruiken voor hyperedges (M1.5).
- **Bronhiërarchie + statusworkflow + `edit_log`**: de Wikipedia-bouwstenen staan er al; ze
  worden alleen nog niet afgedwongen of gebruikt.
- **Aspect-argumenten** (`property` = existence/certainty/influence/…): het schema kan nu al
  onderscheid maken tussen "bestaat de relatie" en "hoe sterk is de invloed" — vrijwel
  ongebruikt, maar precies wat nodig is om óók `influence` bewijsbaar te maken i.p.v.
  handmatig (zie M1.7).
- **Pure-stdlib scoring, gedeeld door viz en API**: één plek voor de rekenlogica maakt elke
  verbetering hieronder goedkoop.

---

## 4. Lessen van elders

### 4.1 Wikipedia
| Principe | Vertaling naar dit project |
|---|---|
| *Verifiability, not truth* | Citatieloosheid wordt een **poort**, geen korting: een voor/tegen-argument zonder citatie telt niet mee (nu: factor 0,30) of degradeert automatisch naar `bronvermelding_nodig`. |
| Reliable-sources-register (perennial sources) | De `reliability`-klassen bestaan al; voeg een beslislog per bron toe (wie classificeerde, waarom) en herbeoordeel periodiek. |
| Overlegpagina's | = onze discussieboom. Wikipedia's les: de discussie hoort *naast* de inhoud zichtbaar, met expliciete afsluiting ("consensus bereikt") — ons statusbesluit. |
| Recent changes & watchlists | `edit_log` bestaat al; er is alleen geen feed of patrouille-weergave op. |
| Protection levels | De theorielaag (rollen/mechanismen/hyperedges) krijgt een hogere wijzigingsdrempel dan de praktijklaag — zoals een beveiligde pagina. |
| *No original research*, aangepast | Claims moeten herleidbaar zijn naar bronnen **buiten het project**; eigen syntheses (`sources/AI/`) mogen vindplaats zijn, nooit bewijs. |

### 4.2 Open source
| Principe | Vertaling |
|---|---|
| Pull request → review → merge | Bijdragen landen als `voorgesteld` en tellen **niet** mee tot een reviewer ze merget. Het verschil tussen "in de database" en "in de score" is hetzelfde verschil als branch vs. main. |
| CI | Een validator-script dat bij elke wijziging draait: koppelingsplicht, schema-pariteit, citatieplicht, linkrot, padclaims zonder route. Plus een **golden-snapshot-test** op `scoring.py`: scores van een fixture-DB mogen alleen bewust veranderen. |
| CODEOWNERS | Maintainers per filter (eigendom, sourcing, …): wie mag in welk deel statusbesluiten nemen. |
| Issue/PR-templates | Argumentsjabloon met Toulmin-velden: claim, bewijs (citaties), rechtvaardiging (waarom ondersteunt dit bewijs de claim), bekende tegenwerpingen. |
| Releases + semver + changelog | Het model krijgt versies; een release = gescoorde snapshot + diff-rapport ("geloofwaardigheid mechanisme X: 0,62 → 0,71 door bron Y"). |

### 4.3 Wetenschap
- **Graduele argumentatiesemantiek** (bipolaire argumentatiegrafen, bv. DF-QuAD — Rago,
  Toni e.a. 2016): precies het wiskundige gereedschap voor Z3. Elk argument heeft een
  basiskracht (ons laag A); zijn eindkracht wordt gemoduleerd door de eindkracht van zijn
  aanvallende en steunende kinderen, recursief van blad naar wortel. Op een platte boom
  reduceert dit tot ongeveer de huidige formule — backwards compatible.
- **GRADE-denken** (evidence-beoordeling in de geneeskunde): niet alleen *brontype* weegt,
  maar de hele bewijsbundel krijgt expliciete op-/afwaardeerredenen: consistentie tussen
  onafhankelijke bronnen, directheid (gaat de bron over déze claim of iets aanpalends?),
  precisie, en selectie-/publicatiebias.
- **Onafhankelijkheid & replicatie**: bewijslijnen clusteren per auteur/uitgever/onderliggende
  data; binnen een cluster telt alleen de sterkste citatie, combineren gebeurt over clusters.
  `geverifieerd` vereist ≥ 2 onafhankelijke clusters — de replicatie-eis.
- **Interbeoordelaarsbetrouwbaarheid**: `weight` en `exemplarity` krijgen een rubric;
  een steekproef wordt dubbel gecodeerd en de overeenstemming (bv. Krippendorff's α) komt in
  het dashboard. Lage α = de rubric is onduidelijk, niet de wereld.
- **Falsificeerbaarheid**: elk mechanisme krijgt een veld *"wat zou dit weerleggen"*, en het
  project organiseert actief pogingen daartoe (adversarial rondes, §M3.3). Kroon op het werk:
  het model **voorspellend** maken — uit de theorie volgen toetsbare verwachtingen over
  berichtgeving (bv. "verhalen die grote adverteerders raken krijgen meetbaar minder
  follow-up") die tegen mediacorpora gescoord kunnen worden. Dat is de stap van beschrijvend
  naar toetsbaar.
- **Onzekerheid**: scores als interval (Beta-posterior of bootstrap over argumenten), niet
  als punt. Monte-Carlo door laag C geeft de theoriescores een band.
- **Value of Information**: de onderzoeksagenda automatisch genereren — sorteer
  theorie-elementen op (sterkte × bewijsarmoede): waar levert één nieuwe goede bron de
  grootste verschuiving op?

### 4.4 Community Notes (X/Birdwatch): bridging-aggregatie

**Het mechanisme.** Beoordelaars raten bijdragen als nuttig/niet nuttig. Een matrix-
factorisatie ontleedt die ratings in een *polariteitsas* (de algemene gezindheid van de
beoordelaar — daar vallen partijdige ratings in) en een *intercept* per bijdrage: nuttigheid
onafhankelijk van gezindheid. Alleen bijdragen met een hoge intercept tellen — bijdragen die
nuttig gevonden worden door mensen die het elders structureel met elkaar **oneens** zijn. Een
meerderheid van gelijkgestemden kan dus niets doordrukken. Voor een politiek geladen onderwerp
als dit, waar de beoordelaarspopulatie zichzelf selecteert (mensen die sympathiek staan
tegenover mediakritiek), is dat precies goed: simpel stemmen zou de bias inbakken die het
model zelf beschrijft.

**Integratie met de discussieboom: een laag erbóven, niet erin.** Bridging beoordeelt geen
waarheid en geen bewijs; het beoordeelt menselijke oordelen óver argumenten. De bewijsketen
(claim → citatie → bron) blijft de enige plek waar geloofwaardigheid vandaan komt; bridging
vervangt de plekken waar nu één persoon subjectief iets vaststelt. Drie integratiepunten:

1. **`weight` in laag A.** Nu zet de inbrenger zijn eigen argumentgewicht (Z2). In plaats
   daarvan een `argument_ratings`-tabel (beoordelaar × argument × nuttig/niet, plus
   gestructureerde redenen zoals "citaat dekt de claim niet"); het bridged nuttigheidscijfer
   wordt de weight-factor. Een steun-argument weegt pas zwaar als ook sceptici van het model
   toegeven dat dit citaat deze claim echt draagt; een tegenwerping van een scepticus krijgt
   gewicht zodra sympathisanten erkennen dat ze eerlijk is.
2. **Statusbesluiten als poort.** `geverifieerd` wordt geen klik van één beheerder maar een
   bridged drempel. Community Notes' *needs more ratings* is letterlijk ons
   `ongecontroleerd`; hun gestructureerde afwijsredenen mappen op onze statussen
   (`bronvermelding_nodig`, `betwist`).
3. **De "serieuze tegenwerping"-vraag van M1.4.** Of een tegenwerping een eerlijke aanval is
   of een stroman, is bij uitstek een bridging-vraag: ze telt als serieus wanneer juist
   vóórstanders van de claim haar als eerlijk beoordelen.

Er wordt dus nooit over stances "gestemd": je stemt niet over of een claim waar is, je
beoordeelt of een argument goed onderbouwd, relevant en eerlijk is. Bewijs en oordeel blijven
gescheiden assen, zoals certainty en influence dat zijn.

**De eerlijke beperking: bridging heeft een populatie nodig.** De polariteitsas vergt per
item meerdere ratings én rating-geschiedenis per beoordelaar; met een handvol gebruikers
degenereert het model en valt er niets te bridgen. Daarom fase 2+, met §6 als overbrugging:
tot die tijd doen expliciete regels hetzelfde werk in ruwe vorm (niemand verifieert zijn
eigen argument, theoriewijzigingen vergen twee reviewers, adversarial rondes organiseren het
tegengeluid dat bridging later automatisch beloont). Rekenkracht is geen beperking — de
factorisatie is op deze schaal triviaal; het schaarse goed is een divers beoordelaarsbestand.

### 4.5 Wikidata
Claims hebben er meerdere referenties, kwalificatoren én **ranks** (preferred / normal /
deprecated): een weerlegde claim wordt niet gewist maar gedegradeerd mét reden, zodat de
geschiedenis leerbaar blijft. Vertaling: status `verworpen` toevoegen en de huidige harde
DELETE-cascades (die complete discussiebomen vernietigen) vervangen door soft-archive.

### 4.6 Kialo / pol.is / Society Library
Vooral UI-lessen: één claim per kaartje (hebben we), korte stellingen, expliciete
impact-beoordeling per ouder-kindrelatie, en (pol.is) het *clusteren* van perspectieven in
plaats van ze weg te middelen. Geen van deze systemen heeft onze bronnenketen — dat is onze
kracht; de hunne is deliberatie-ergonomie.

---

## 5. Het plan — vier fasen

Elke maatregel noemt wat hij raakt en welke zwakte (Z#) hij dicht. Dit hoofdstuk is het
*wat en waarom*; de concrete uitvoeringsstappen mét afvinkbare voortgang staan per
maatregel in §9.

### Fase 0 — meten & dichten (dagen, geen scoring-wijziging)

- **M0.1 Validator** — `scripts/validate_model.py`: rapporteert koppelingsplicht (Z6),
  argumenten zonder citatie (Z2), statusachterstand, stance-balans per node (Z1),
  padclaims zonder doorlatende route, linkrot + ontbrekende `archive_url`. Eerst
  rapporterend; zodra de achterstand is weggewerkt afdwingend (exit-code, pre-commit/CI).
- **M0.2 Schema-pariteit herstellen** (Z9): `schema.sql` bijwerken (active-kolommen,
  `indirecte_invloed_op`, status `verworpen`), live DB her-CHECKen via de
  backup-then-migrate-conventie, en een pariteitscheck (`PRAGMA`-vergelijking live vs. vers
  gebouwd) opnemen in M0.1.
- **M0.3 Citatiepoort in de API** (Z2, Z8): een supporting/contradicting-argument zonder
  citatie krijgt automatisch `bronvermelding_nodig`; alleen `contextual` mag bronloos.
  (Dit is de goedkoopste grote verbetering: één if-statement.)
- **M0.4 Backfill-campagne** (Z6): de 114 ongekoppelde relaties → bestaand mechanisme of
  expliciet voorstel voor een nieuw theorie-element; de 10 ontbrekende instantiaties; de 23
  entiteiten. Agent-taak met menselijke review; daarna houdt M0.1 het op nul.
- **M0.5 Gezondheidsdashboard**: de tabel uit §1 als live endpoint (`/api/health`) en
  paneel in de viz. Wat zichtbaar is, wordt vanzelf onderhouden.
- **M0.6 Dogfood-regel + identiteit-licht: inlogportal & tokens** (→ §6.1; Z8, Z10): vanaf
  nu gaat álle inhoud — ook die van de eigenaar, ook agent-werk — via het bijdragepad
  (landt als `voorgesteld`, daarna review), niet meer via ad-hoc migratiescripts; migraties
  zijn voortaan alleen voor schema en structuur. Ontwerp:
  - **`users`-tabel** (mens/agent): username, rol (bijdrager < reviewer < maintainer),
    wachtwoord-hash (alleen mensen; scrypt), token-hash (sha256 — het token zelf wordt
    nooit opgeslagen en één keer getoond), en voor agents verplichte provenance
    (model + versie). Beheer via een CLI (`scripts/create_user.py`).
  - **Inlogportal** `/login` (+ `/logout`, accountpagina): mensen loggen in met een
    wachtwoord; op de accountpagina genereren/roteren ze hun API-token. De viz toont wie
    ingelogd is; de vrije "jouw naam"-tekstvelden vervallen.
  - **Tokens als brug naar Claude Code**: een sessie of background-agent stuurt
    `Authorization: Bearer <token>` mee. Met het token van de méns werkt Claude Code als
    die mens (de mens blijft de bijdrager, §6.1); agents gebruiken hun eigen agent-account.
  - **Poorten**: schrijf-endpoints vereisen een identiteit en de attributie volgt de
    ingelogde gebruiker (nooit een vrij tekstveld); theorielaag-wijzigingen en DELETEs
    vereisen maintainer; lezen blijft open. Zelf-merges zijn toegestaan (n=1) maar dragen
    een `self_merged`-vlag zodat ze later herauditeerbaar zijn.

### Fase 1 — scoring v2 (weken)

- **M1.1 Boomsemantiek** (Z3): graduele propagatie à la DF-QuAD. Regels: een reply draagt
  géén eigen target (CHECK + API-validatie; migratie is gratis want er zijn 0 replies);
  kracht stroomt van blad naar wortel; de relatie-score combineert alleen de netto
  rootkrachten. Ondergravingen (M1.8) hechten aan het argument dat ze aanvallen en dempen
  diens kracht; alleen weerleggingen tellen als tegenbewijs voor het doel zelf.
  Golden-snapshot-test ernaast (4.2).
- **M1.2 Bronclusters** (Z4): `cluster_key` op `sources` (auteur/uitgever/dataset); binnen
  cluster max, tussen clusters combineren; bronklasse `eigen_synthese` met bewijsgewicht 0
  voor projectmateriaal. Verplichte vlag in het detailpaneel: *"drijft op één broncluster"*.
- **M1.3 Onzekerheidsband** (Z7): intervallen per score (laag B: Beta op steun/tegen;
  laag C: bootstrap over instanties); de viz toont band of kleurverzadiging i.p.v. een punt.
- **M1.4 Tegenspraak-plafond** (Z1): zonder overwogen tegenspraak (≥ 1 serieus
  contradicting-argument, of een expliciete "beste tegenwerping"-notitie die reviewers als
  eerlijk beoordelen) is de geloofwaardigheid gemaximeerd (bv. 0,70) en draagt het element
  zichtbaar het label **onweersproken**. Let op stroman-risico: of een tegenwerping "serieus"
  is, is een review-oordeel (later: bridging, 4.4) — nooit een automatische telling.
- **M1.5 Hyperedges & halo's in de keten** (Z5): `arguments.emergent_effect_id` (+ API +
  index). Geloofwaardigheid uit twee lijnen zoals mechanismen: literatuur op het effect zelf,
  en — analoog aan padclaims — een verplichte **compositieclaim**: bewijs dat het *samenspel*
  bestaat, niet alleen dat de leden bestaan. Halo-sterkte krijgt dezelfde behandeling
  (aspect-argumenten op `property='influence'`).
- **M1.6 Gevoeligheidsanalyse** (Z7): leave-one-cluster-out-script: welke theorie-elementen
  verschuiven > X bij het wegvallen van één broncluster; parameter-sweep over de constanten
  in `scoring.py` met rapport welke conclusies parameter-robuust zijn en welke niet.
- **M1.7 Influence bewijsbaar maken**: `influence` blijft handmatig als prior, maar
  aspect-argumenten (`property='influence'`) kunnen hem voortaan verschuiven, met dezelfde
  keten als certainty. Twee assen, één bewijsstandaard.
- **M1.8 Monitor-agent: logica- en drogreden-controle** (→ §6.2): een agent-account dat elk
  argument toetst op de gevolgtrekking — volgt de claim uit het aangevoerde bewijs? De plek
  om te benoemen *waarom een argument niet klopt* bestaat al: een reply in de discussieboom
  op dát argument. Het plan voegt het onderscheid toe dat de scoring nodig heeft
  (argumentatietheorie: *ondergraving* vs. *weerlegging*):
  - **Ondergraving** ("de redenering deugt niet"): drogreden (cirkelredenering, stroman,
    non sequitur, correlatie-als-causatie, vals dilemma, ad hominem, autoriteit buiten haar
    domein, anekdote-als-regel, cherry-picking, equivocatie) of citaat-dekking (het citaat
    ondersteunt déze claim niet). Landt als reply op het argument, met machineleesbaar
    `objection_type` + de exact aangevochten redeneerstap. Eenmaal bevestigd dempt ze via
    de boomsemantiek (M1.1) alleen de kracht van dát argument — een drogredelijk argument
    vóór een ware claim trekt de claim niet omlaag, het houdt alleen op haar te stutten.
    Een ondergraving vergt geen tegenbron; het aanwijzen van het logische gat volstaat.
  - **Weerlegging** ("de claim is onwaar"): geen logica-kwestie maar tegenbewijs — een
    contradicting-argument mét bronnen, dezelfde standaard als elk ander argument.
  Constructieve variant: classificeer argumenten naar Walton-achtige redeneerschema's
  (expertise-argument, oorzaak→gevolg, voorbeeld, teken) en stel per schema de
  bijbehorende kritische vragen — dat levert benoemde, specifieke zwaktes op ("is deze
  expert autoriteit op dít domein?") én maakt zichtbaar welke toetsing een argument
  *overleefde*. Guardrails: LLM-drogredendetectie slaat te vaak aan (elke compacte claim
  oogt als stroman), dus bevindingen landen als `voorgesteld`, citeren verplicht de
  aangevochten stap en een mens bevestigt; nooit directe statuswijzigingen. Het
  `objection_type`-veld maakt het corpus doorzoekbaar ("meest voorkomende zwakte" op het
  dashboard, M0.5). Routinetaken blijven daarnaast: duplicaten, verouderde bronnen,
  consistentie beschrijving ↔ discussieboom.
- **M1.9 Scout-agents met blind-zoekprotocol** (→ §6.3): agents die wetenschap en internet
  afzoeken naar nieuwe verbanden en bronnen — onder het anti-overfit-protocol: neutrale
  missie-briefs zonder de modelclaim, tweezijdige oogstplicht (beide stances), gelogde
  queries, negatieve-resultatenregister. Alle vondsten landen als `voorgesteld`.

### Fase 2 — openstellen voor gebruikers en agents (maanden)

- **M2.1 Identiteit** (Z8, Z10): de `users`-tabel uit M0.6 uitgebouwd: reviewer/maintainer
  per filter en `contributed_by` wordt een FK; agent-accounts blijven verplicht gemarkeerd
  met model + versie. Regel: niemand verifieert zijn eigen argument — agents al helemaal
  niet.
- **M2.2 Voorstel-workflow** (Z8): status `voorgesteld` als landingsstatus; telt mee in
  niets tot eerste review. Review-UI toont de **score-diff** ("accepteren verschuift
  mechanisme X van 0,62 → 0,71") zodat de reviewer ziet wat er epistemisch op het spel staat.
- **M2.3 Theory-RfC** (Z6, zijnoot van de opdrachtgever): praktijkdata zonder passend
  theorie-element opent een voorstel met sjabloon: definitie, aard-keuze (+ freeze-test),
  afgrenzing van bestaande elementen, falsificatiecriterium, ≥ 1 instantiatie, ≥ 1
  onafhankelijke bron. Twee reviewers (theorielaag = beschermd niveau, 4.1). Zo blijft de
  regel "alles gelinkt aan theorie" hard én blijft de theorielaag uitbreidbaar.
- **M2.4 Anti-misbruik** (Z8): rate limits; duplicaatdetectie (embedding-gelijkenis tegen
  bestaande claims); recent-changes-feed + watchlists op `edit_log`; bridging-aggregatie
  van beoordelingen zodra er per item meerdere beoordelaars zijn.
- **M2.5 Agent-stem in bridging — verdiend, begrensd, nooit onderling** (→ §6.4; Z10):
  agents mogen raten, maar hun ratings zijn eerst alleen advies (zichtbaar naast de
  menselijke oordelen). Stemgewicht wordt verdiend via kalibratie — kwamen eerdere
  agent-oordelen overeen met latere menselijke uitkomsten? — blijft gecapt, en
  agent×agent-overeenstemming telt nooit als brug: alle LLM's gelden als één gecorreleerde
  familie tot het tegendeel blijkt.
- **M2.6 Splitsen & samenvoegen (granulariteitsbeheer)** (Z8): "deze node vermengt twee
  dingen" of "deze twee elementen zijn één kracht" is zelf een claim — hij landt als
  voorstel in de discussieboom met bronnen en tegenspraak, en volgt de gewone route
  (instantielaag M2.2, theorielaag M2.3 met twee reviewers). Die poort is nodig omdat
  granulariteit score-relevant is: samenvoegen poolt bewijs (de verzadigingsfactor
  n/(n+5) springt bij 2 × 5 argumenten van 0,50 naar 0,67), splitsen verdunt het —
  zonder regels wordt de knip zelf een instrument om scores te bewegen. Na acceptatie
  gelden twee kernregels. (1) **Niets wissen**: het oude element krijgt status
  `vervangen` plus een lineage-verwijzing naar zijn opvolger(s); oude ID's blijven
  herleidbaar en een samenvoeging is omkeerbaar (Wikidata's merge-redirects, Gene
  Ontology's *obsolete* met `replaced_by`). (2) **Bewijs verhuist nooit automatisch**:
  bij samenvoegen telt alleen bewijs dat expliciet voor de brédere claim is herbevestigd
  (anders is een merge bewijs-witwassen: een zwakke claim erft de score van een sterke),
  bij splitsen wordt elk argument, elke relatie en elke instantiatie handmatig aan één
  of meer opvolgers toegewezen (GO's `consider`: één-op-veel is nooit automatisch
  veilig). De bewijsstructuur is meteen de lakmoesproef voor kandidaten: disjuncte
  argumentclusters en terugkerende "geldt alleen voor…"-ondergravingen wijzen op
  splitsen, vrijwel identieke bron- en argumentverzamelingen op samenvoegen —
  `scripts/analyse_granulariteit.py` vlagt zulke kandidaten voor de onderzoeksagenda
  (M3.2), maar beslist niets. Hernoemen zonder betekenisverandering is de lichte
  variant (zelfde route, geen hertriage); verschuift de definitie wezenlijk, dan is het
  de facto vervangen. Precedent: de tier-audit van juni 2026 (duplicaat-halo's en een
  dyade geabsorbeerd door hun hyperedges) wás zo'n operatie, toen als
  maintainer-migratie — voortaan loopt dit via het voorstelpad.

### Fase 3 — een levend, falsifieerbaar model (doorlopend)

- **M3.1 Modelreleases**: semver + changelog + score-diff tussen releases; de viz kan een
  releasetag tonen ("model v2.3, 2026-09").
- **M3.2 Onderzoeksagenda**: automatisch gegenereerde ranglijst (invloed × bewijsarmoede):
  de waardevolste ontbrekende bron staat bovenaan. Dit is hoe het model *dynamisch* beter
  wordt: het systeem vertelt zelf waar het zwak is.
- **M3.3 Adversarial rondes**: periodiek krijgt een red team (mens of agent) de expliciete
  opdracht tegenbewijs te vinden voor de top-N invloedrijkste edges; idealiter als
  adversarial collaboration met een inhoudelijke criticus van het propagandamodel als
  mede-reviewer. Dit is het structurele antwoord op Z1 — tegenspraak moet georganiseerd
  worden, ze ontstaat niet vanzelf.
- **M3.4 Voorspellingsregister**: afleidbare voorspellingen vastleggen vóór de uitkomst
  bekend is, daarna scoren (kalibratie). De enige weg van "consistent verhaal" naar
  "getoetst model".
- **M3.5 Jaarlijkse audit** van aard/tiers en bronclassificaties (precedent: de tier-audit
  van juni 2026).

---

## 6. Koudstart: één mens + agents, zonder homofilie te kweken

De beginsituatie is eerlijk benoemd: er is precies één menselijke gebruiker (de eigenaar,
die via Claude Code werkt) en een groeiend aantal agents. Dat is geen reden om te wachten —
wel om drie valkuilen expliciet te ontwerpen vóórdat ze ontstaan: **zelfbevestiging** (de
eigenaar reviewt de eigenaar), **overfit** (agents die het bestaande model als zoekbril
gebruiken en alleen bevestiging terugbrengen) en **schijnpluriformiteit** (gecorreleerde
agents die samen een gemeenschap simuleren).

### 6.1 Dogfooding: de eigenaar is gebruiker nul

Alle inhoud gaat vanaf nu door het systeem zelf (M0.6): bijdragen landen als `voorgesteld`
onder een eigen gebruikersidentiteit. Ook als Claude Code het typewerk doet, is de mens de
bijdrager — praktisch: de sessie stuurt het persoonlijke API-token van de gebruiker mee
(M0.6), zodat de attributie vanzelf klopt. Autonome agent-missies draaien daarentegen onder
hun eigen agent-account (model + versie + missie-brief). Met n=1 mens is zelf-review onvermijdelijk; dat wordt niet verstopt
maar gemarkeerd (`self_merged`-vlag) en verzacht met drie gewoontes uit solo-onderhouden
open source: verplichte validator/CI vóór elke merge, een afkoelperiode tussen indienen en
zelf-mergen (je leest je eigen claim morgen kritischer dan vanavond), en de monitor-agent
(M1.8) als vaste pre-review. Alles wat zelf-gemerged is, staat automatisch op de
heraudit-lijst zodra er wél onafhankelijke reviewers zijn.

### 6.2 Agent-rollen: vier functies, één regel

| Agent | Doet | Mag niet |
|---|---|---|
| **Monitor** (M1.8) | drogreden-lint, citaat-dekking, consistentie, duplicaten | statussen zetten; alleen bevindingen indienen |
| **Scout** (M1.9) | wetenschap/internet afzoeken naar nieuwe verbanden en bronnen, voor béíde stances | rechtstreeks de score in; alles landt als `voorgesteld` |
| **Red team** (M3.3) | actief tegenbewijs zoeken voor de sterkste edges | — (tegenspraak ís zijn taak) |
| **Verificateur** (M2.5) | citaten narekenen, ratings afgeven | bruggen vormen met andere agents; eigen werk raten |

De ene regel die overal geldt: **een agent telt als gebruiker, maar verdient zijn gewicht.**
Provenance is verplicht (model, versie, missie-brief in `edit_log`), elke claim moet
herleidbaar zijn naar een door mensen controleerbare bron, en invloed op poorten komt pas na
bewezen kalibratie — gecapt.

**Runtime: Claude Code background agents, geen aparte integratie.** Alle agent-rollen draaien
als Claude Code (background) agents op het bestaande Max-abonnement — niet als losse
API-integratie met eigen modelsleutels in de server. Ze gebruiken exact dezelfde REST-API als
menselijke gebruikers en authenticeren met het token van hun agent-account (M0.6). Dat houdt
de server modelvrij (stdlib + Flask), maakt agent-gedrag auditeerbaar via dezelfde poorten
als mensen, en kost niets extra. Een missie is een gewone sessie met een brief (monitor-ronde,
scout-opdracht, red-team-ronde), handmatig of gepland gestart.

### 6.3 Anti-overfit: zoeken alsof het model er nog niet is

Een scout die eerst de database leest en dan gaat zoeken, vindt wat het model al gelooft —
de lantaarnpaal-fout als dienstverlening. Daarom het blind-zoekprotocol:

- **Neutrale missie-briefs**: de zoekvraag wordt geformuleerd zónder de modelclaim ("wat is
  bekend over eigenaarsinvloed op redactionele besluitvorming in NL?"), nooit als
  bevestigingsvraag ("zoek bewijs dat …"). Brief en alle zoekopdrachten worden gelogd en
  zijn zelf auditeerbaar — bevooroordeeld zoeken is dan achteraf aantoonbaar.
- **Tweezijdige oogstplicht**: elke missie levert kandidaat-bewijs voor beide stances, of
  een expliciet *afwezigheidsrapport* ("geen tegenbewijs gevonden; gezocht via X, Y, Z").
  Dat rapport is zelf een `contextual`-bijdrage en telt mee in de bewijsdekking.
- **Negatieve-resultatenregister**: zoektochten die niets opleverden worden vastgelegd; zo
  wordt herhaald cherry-picken zichtbaar en bouwt het corpus aantoonbare dekking op — de
  vertaling van het publicatiebias-probleem uit de wetenschap.
- **Buiten-de-bril-bemonstering**: periodiek wordt gezocht búíten de trefwoorden van het
  model (recente mediastudies-jaargangen, proefschriften, toezichtsrapporten) met als vraag
  "wat beschrijft dit veld dat ons model mist?". Nieuwe theorie-elementen horen ook van
  buiten naar binnen te komen, niet alleen uit verfijning van wat er al staat.
- **Meetbaar**: het dashboard (M0.5) toont per missie de stance-balans en de *nieuwheid*
  (nieuwe bronclusters vs. hercitaties van bestaande). Een scout die alleen bevestiging
  binnenbrengt, is meetbaar kapot.

### 6.4 Schijnpluriformiteit: alle agents zijn één familie

LLM-agents delen trainingsdata en gezindheid; tien agents zijn epistemisch geen tien
beoordelaars. Daarom gelden alle agents voor bridging én voor het onafhankelijkheids-
rekenwerk als **één gecorreleerd cluster** (vgl. bronclusters, M1.2) tot het tegendeel
blijkt. Persona-diversificatie (een agent gebrieft als methodoloog, één als sceptische
communicatiewetenschapper, één als sympathisant) is nuttig tégen blinde vlekken in het
*zoeken*, maar koopt geen onafhankelijkheid in het *oordelen*: agent×agent-overeenstemming
vormt nooit een brug en vervult nooit de twee-reviewer-eis van de theorielaag. De gewenste
agent-stem in de bridging-laag ("een agent die kan verifiëren of afkeuren op basis van goede
argumenten") werkt daarom zoals een nieuwe Community-Notes-beoordelaar: hij begint zonder
invloed, bouwt een kalibratiegeschiedenis op (kwamen zijn oordelen overeen met latere
menselijke uitkomsten?), krijgt dan begrensd gewicht — en verliest het meetbaar bij drift
(M2.5).

### 6.5 Mensen eerst: ontwerp voor de criticus

De waardevolste vroege gebruiker is degene die het propagandamodel *overdreven* vindt: een
journalist, een communicatiewetenschapper, een rechtse én een linkse mediacriticus. Werving
is dus geen marketing maar methode — pluriformiteit van de beoordelaarspool is een
wetenschappelijke randvoorwaarde (zonder haar valt er niets te bridgen). Wat meedoen
aantrekkelijk maakt:

- **Zichtbare epistemische impact**: de score-diff (M2.2) als beloning — "jouw bron
  verschoof dit mechanisme −0,06" is bevredigender dan een like, en beloont juist
  tegenspraak even goed als steun.
- **Tegenspraak als eerbewijs**: erkenning (Wikipedia's barnstar-les) voor de sterkste
  overlevende tegenwerping, de bron die een score omlaag bracht, de gevonden fout — nooit
  voor volume. "Beste tegenwerping van het kwartaal" weegt cultureel zwaarder dan elke
  hoeveelheidsbadge.
- **Twee-minuten-bijdragen**: de mens levert het oordeel (een bron, een tegenwerping, een
  twijfel), een agent doet het invoerwerk (registratie, citatie, koppeling, opmaak) en legt
  het ter bevestiging voor. Agents verlagen zo de drempel voor mensen in plaats van ze te
  vervangen.
- **De onderzoeksagenda als voordeur** (M3.2): nieuwkomers zien meteen waar het model
  zichzelf zwak verklaart — uitnodigender en eerlijker dan een dichtgetimmerd bolwerk.
- **Adversarial collaboration als uitnodiging** (M3.3): critici niet als doelwit maar als
  co-reviewer, met naam in de release notes.

### 6.6 Groeipad in drie standen

| Stand | Populatie | Poorten | Eerlijke labels |
|---|---|---|---|
| **Solo** (nu) | 1 mens + agents | rubric + validator + afkoelperiode + monitor-agent; zelf-merge gevlagd | scores dragen een "één beoordelaar"-label; Popper-plafond laag |
| **Klein** (≥ ~3 onafhankelijke mensen) | handvol mensen + agents | twee-reviewer-eis wordt echt; heraudit van alle `self_merged` | "beperkte pool"-label |
| **Gemeenschap** (tientallen, divers) | divers genoeg voor een polariteitsas | bridging vervangt de noodregels (M2.5 wordt actief) | labels vervallen waar bridging draagt |

Het systeem moet in elke stand *eerlijk over zichzelf* zijn: niet doen alsof er consensus is
waar één persoon en zijn gereedschap aan het werk zijn. Dat is precies het verschil tussen
dit project en de mediadynamiek die het beschrijft.

---

## 7. Wat bewust níét

- **Geen upvotes/likes of populariteitsgewichten** — meerderheid ≠ bewijs; alleen
  bridging-aggregatie of niets.
- **Geen LLM als zelfstandige bron of eindverificateur** — agents mogen aandragen,
  structureren, zoeken, raten (M2.5) en red-teamen; elk bewijs moet herleidbaar zijn naar
  een door mensen controleerbare bron, en geen statusbesluit rust ooit op agent-stemmen
  alleen.
- **Geen gesimuleerde gemeenschap** — agents tellen mee als gebruikers, maar alle LLM's
  vormen samen één gecorreleerd cluster (§6.4): agent×agent-overeenstemming telt nooit als
  brug, consensus of tweede reviewer. Pluriformiteit komt van mensen.
- **Geen harde deletes van weerlegde inhoud** — degraderen mét reden (Wikidata-rank-stijl);
  de geschiedenis van een verworpen claim is zelf bewijsmateriaal over het proces.
- **Geen blockchain/DAO** — `edit_log` + git + releases volstaan voor herleidbaarheid.
- **Geen schijnprecisie** — nooit een puntscore tonen zonder interval en bewijsdekking
  ("3 argumenten, 1 broncluster, onweersproken") ernaast.

---

## 8. Prioriteit

| # | Maatregel | Moeite | Effect | Dicht |
|---|---|---|---|---|
| 1 | M0.1+M0.2 validator & schema-pariteit | klein | reproduceerbaarheid, drift stopt | Z9, Z6 |
| 2 | M0.3 citatiepoort | zeer klein | bronfactor gaat eindelijk werk doen | Z2, Z8 |
| 3 | M0.6 dogfood-regel + identiteit-licht | klein | alles herleidbaar; einde content-migraties; basis voor §6 | Z8, Z10 |
| 4 | M3.3-voorproef: handmatige tegenspraakronde op de 20 invloedrijkste edges | klein | stance-balans wordt betekenisvol; kalibreert M1.4 | Z1 |
| 5 | M1.1 boomsemantiek | middel | discussie wordt score-dragend | Z3 |
| 6 | M1.2 bronclusters | middel | einde dubbeltelling; SPOF-vlaggen | Z4 |
| 7 | M1.8+M1.9 monitor- & scout-agents (blind-zoekprotocol) | middel | vaste foutdetectie; tweezijdige bronoogst | Z1, Z4, Z10 |
| 8 | M1.5 hyperedges in de keten | middel | de grootste claims worden toetsbaar | Z5 |
| 9 | M1.3+M1.6 onzekerheid & gevoeligheid | middel | eerlijke presentatie | Z7 |
| 10 | M2.x openstelling (incl. M2.5 agent-stem) | groot | gebruikers/agents kunnen veilig bijdragen | Z8, Z10 |
| 11 | M3.x releases, agenda, voorspellingen | doorlopend | dynamisch zelfverbeterend model | alles |

Concrete stappen en voortgang per maatregel: **§9**.

**Eén zin als samenvatting:** het systeem hoeft niet herontworpen te worden — het moet
*afgedwongen* (poorten, koppelingsplicht, CI), *gewogen* (onafhankelijkheid, boomsemantiek,
onzekerheid) en *weersproken* (georganiseerde tegenspraak, falsificatie) worden.

---

## 9. Uitvoeringschecklist

Per maatregel de concrete stappen, in uitvoeringsvolgorde (prioriteit: §8). Een vakje wordt
pas afgevinkt als de stap af **én geverifieerd** is; een maatregel is af wanneer al haar
stappen plus het **klaar wanneer**-criterium zijn afgevinkt. Vaste conventies bij elke stap
die de DB raakt: backup-then-migrate, `schema.sql` mee-updaten; en zodra M0.6 staat geldt de
dogfood-regel (inhoud via het bijdragepad, migraties alleen voor schema/structuur).

### Fase 0 — meten & dichten

- [x] **M0.1 Validator** — `scripts/validate_model.py` (stdlib)
  - [x] Skelet: elke check een functie die (code, ernst, aantal, voorbeelden) teruggeeft;
        uitvoer leesbaar én `--json` (voor agents/dashboard); `--strict` → exit-code ≠ 0
        *(checks leven in `validation.py` op de repo-root, gedeeld met `/api/health`)*
  - [x] Check koppelingsplicht: relaties zonder `mechanism_id`; relaties mét mechanisme
        zonder `instantiations`-rij; entiteiten zonder rol of instantiatie (Z6)
  - [x] Check bewijs: voor/tegen-argumenten zonder citatie; omvang statusachterstand (Z2)
  - [x] Check balans: alleen-steun-vlag per relatie/mechanisme/rol (Z1)
  - [x] Check padclaims: elke padclaim heeft ≥ 1 keten van directe edges tussen bron- en
        doelrol (eerste versie zonder drempels; later dezelfde gates als de viz)
  - [x] Check bronnen: bron zonder `source_locations`; url zonder `archive_url`;
        linkrot achter een `--network`-vlag (HEAD-requests)
  - [x] Check schema-pariteit: verse DB in-memory bouwen uit `schema.sql` en per tabel
        `PRAGMA table_info` + DDL diffen met de live DB (Z9)
  - [x] **Klaar wanneer:** draait foutloos op de live DB, rapporteert de bekende
        achterstanden, en staat gedocumenteerd in CLAUDE.md *(12 juni 2026)*

- [x] **M0.2 Schema-pariteit herstellen** (Z9)
  - [x] Driftlijst vaststellen met de M0.1-schemacheck *(7 kolommen, 1 FK, 1 index +
        `tegenmacht` ontbrak in beide CHECKs en `mechanism_type` moest nullable)*
  - [x] `schema.sql`: `active_from`/`active_until`/`active` op entities én relations;
        `indirecte_invloed_op` in de property-CHECK; status `verworpen` toevoegen (4.5)
  - [x] Migratie: live `arguments`-tabel herbouwen mét CHECKs en FK op
        `parent_argument_id` (de 18 padclaims moeten geldig blijven)
        *(`migrate_schema_pariteit.py`; DDL wordt uit schema.sql gelezen; +`self_merged`)*
  - [x] `scoring.py`: `STATUS_FACTOR['verworpen'] = 0.0`
  - [x] Verse-buildtest: `init_db` + seeds draaien schoon; alle POST-endpoints werken op
        de verse DB *(`scripts/test_fresh_build.py`)*
  - [x] **Klaar wanneer:** de M0.1-schemacheck meldt 0 verschillen *(12 juni 2026;
        resterende DDL-tekstverschillen zijn gedocumenteerd intentioneel, info-niveau)*

- [x] **M0.3 Citatiepoort** (Z2, Z8)
  - [x] `server.py`: voor/tegen-argument start als `bronvermelding_nodig`
        (contextual blijft `ongecontroleerd`)
  - [x] `POST /api/citations` promoveert het doelargument automatisch
        `bronvermelding_nodig` → `ongecontroleerd` (alleen die overgang)
  - [x] Optioneel: citaties direct meegeven in `POST /api/arguments` (één call voor agents)
  - [x] Viz: de regel tonen in het argumentformulier; DOCUMENTATIE.md § Stances bijwerken
  - [x] **Klaar wanneer:** handmatige test toont de automatische statusflow in beide
        richtingen *(12 juni 2026; geautomatiseerd herhaald in test_fresh_build +
        test_auth_smoke)*

- [x] **M0.4 Backfill koppelingsplicht** (Z6)
  - [x] Werklijst uit M0.1 (stand 12 juni: 114 relaties / 14 instantiaties /
        13 entiteiten zonder rol / 29 zonder instantiatie)
  - [x] Per relatie een bestaand mechanisme koppelen; de restgroep wordt de
        kandidatenlijst voor nieuwe mechanismen (input voor M2.3-RfC's)
        *(108 gekoppeld via `migrate_backfill_koppelingen.py`; 6 kandidaten +
        motiveringen + richting-mismatches in `BACKFILL_REVIEW.md`)*
  - [x] Instantiaties en entiteit-rollen aanvullen (migratie met CONTRIB-tag
        `backfill-M0.4`, exemplariteit 0,8; eigenaar reviewt via BACKFILL_REVIEW.md)
  - [ ] **Klaar wanneer:** M0.1 meldt 0 ontbrekende koppelingen — *6 relaties blijven
        bewust open (kandidaten voor nieuwe theorie-elementen, M2.3; twee daarvan zijn
        verwijder-adviezen). Dit vakje sluit pas na de eerste theorie-RfC's of review.*

- [x] **M0.5 Gezondheidsdashboard**
  - [x] `/api/health` hergebruikt de M0.1-checkfuncties (zelfde module, geen duplicatie)
  - [x] Inklapbaar paneel "Modelgezondheid" in de viz-zijbalk met kerngetallen,
        stance-balans, bewijsdekking en alle bevindingen
  - [x] **Klaar wanneer:** de cijfers in de viz zijn identiek aan de validatoruitvoer
        *(per constructie: zelfde `validation.py`; gelijkheid van de totalen is
        programmatisch geverifieerd, 12 juni 2026)*

- [x] **M0.6 Users, inlogportal & tokens** (ontwerp: §5/M0.6)
  - [x] `auth.py`: scrypt-wachtwoordhash + sha256-tokenhash (stdlib) *(met
        PBKDF2-SHA256-fallback, 600k iteraties: de macOS-systeem-Python is tegen
        LibreSSL gecompileerd en mist `hashlib.scrypt`; het opslagformaat draagt
        het schema, dus beide blijven verifieerbaar)*
  - [x] Migratie `users`-tabel (+ `schema.sql`; UNIQUE op token_hash levert de index)
  - [x] `scripts/create_user.py`: mens/agent aanmaken, `--new-token --save`
        (schrijft `data/tokens/<naam>.token`, chmod 600), `--set-password`, `--list`
  - [x] `server.py`: `_zoek_user` (Bearer gaat vóór sessie) + `require_user(min_rol)`;
        álle schrijf-endpoints beschermd; attributie uit `g.user`, nooit uit de payload;
        DELETEs en theorielaag = maintainer; status-PATCH = reviewer; zelf-merge zet
        de `self_merged`-vlag
  - [x] Portal: `/login`, `/api/logout`, accountpagina (`/account`) met
        token-generatie/rotatie; `/api/me`; `/api/tokens`
  - [x] Viz: auth-chip in de topbar; "jouw naam"-velden vervangen door "ingediend als …"
  - [x] `.gitignore`: `data/secret_key`, `data/tokens/`
  - [x] Smoke-test (Flask `test_client` op een kopie-DB): 401 anoniem, sessieflow,
        Bearer-flow, rolpoorten (403), attributie-spoofing genegeerd
        *(`scripts/test_auth_smoke.py`, plus zelf-merge en tokenrotatie)*
  - [x] Eigenaarsaccount (maintainer `maxime`) + token; eerste echte bijdrage via de
        API als ingelogde gebruiker *(argument #483 op relatie #426, met citatie,
        `contributed_by=maxime`; wachtwoord voor de browser-portal zet de eigenaar
        zelf: `python3 scripts/create_user.py maxime --set-password`)*
  - [x] Dogfood-regel vastleggen in CLAUDE.md (inhoud nooit meer via migratiescripts)
  - [x] **Klaar wanneer:** een bijdrage via Claude Code landt onder het eigenaarsaccount,
        zonder vrije naamvelden *(12 juni 2026)*

### Fase 1 — scoring v2

- [ ] **M1.1 Boomsemantiek** (Z3)
  - [ ] Semantiek vastleggen in DOCUMENTATIE.md: basiskracht τ per argument (laag A);
        eindkracht σ = τ gemoduleerd door de σ's van steunende en aanvallende kinderen
        (DF-QuAD-combinatie); 2–3 doorgerekende voorbeelden
  - [ ] Regels afdwingen: een reply draagt géén eigen target (API-validatie; CHECK samen
        met M1.5 herdefiniëren); stance is relatief aan de parent
  - [ ] `scoring.py`: recursieve propagatie; een platte boom reproduceert de huidige
        uitkomsten (regressie-eis)
  - [ ] Golden-snapshot: fixture-DB + `scripts/test_scoring.py` (stdlib `unittest`),
        draait mee in M0.1 `--strict`
  - [ ] Viz: reply-formulier stuurt geen target meer mee; per argument de gedempte
        σ tonen
  - [ ] **Klaar wanneer:** snapshottest groen én een demo-ondergraving dempt aantoonbaar
        in `/api/scores`

- [ ] **M1.2 Bronclusters** (Z4)
  - [ ] Migratie: `cluster_key` op `sources` + vulregels (zelfde auteur / uitgever /
        onderliggende data); reliability-klasse `eigen_synthese` met gewicht 0
  - [ ] Clustertoekenning voor de bestaande ~65 bronnen, handmatig gereviewd
  - [ ] `scoring.py`: binnen een cluster telt de sterkste citatie, combineren gebeurt
        over clusters; SPOF-vlag ("drijft op één cluster") in de output
  - [ ] Viz: SPOF-badge in het detailpaneel; DOCUMENTATIE.md bijwerken
  - [ ] **Klaar wanneer:** scores verschuiven aantoonbaar waar één boek nu meervoudig
        telt, en de badge verschijnt

- [ ] **M1.3 Onzekerheidsband** (Z7)
  - [ ] Methode vastleggen: Beta-interval op steun/tegen-massa's (laag B); bootstrap
        over instanties (laag C)
  - [ ] `scoring.py`: interval naast elke puntscore in `compute_all_scores`
  - [ ] Viz: band/kleurverzadiging + notatie "0,62 [0,45–0,76]" in de detailpanelen
  - [ ] **Klaar wanneer:** geen enkele score wordt nog zonder interval getoond

- [ ] **M1.4 Tegenspraak-plafond** (Z1)
  - [ ] Criterium vastleggen (wat telt als "overwogen tegenspraak") + startplafond 0,70
  - [ ] `scoring.py`: cap + `onweersproken`-vlag; label in de viz
  - [ ] Herijken op de M1.6-uitkomsten
  - [ ] **Klaar wanneer:** onweersproken elementen tonen label én cap in API en viz

- [ ] **M1.5 Hyperedges & halo's in de keten** (Z5)
  - [ ] Migratie: `arguments.emergent_effect_id` + index; CHECK-herdefinitie sámen met
        de M1.1-replyregel; `schema.sql`
  - [ ] API: GET/POST argumenten op een emergent effect
  - [ ] Compositieclaim-conventie vastleggen (analoog aan padclaims) + `scoring.py`:
        literatuurlijn + compositielijn per hyperedge
  - [ ] Halo-sterkte: eigen bewijslijn via `property='influence'`-argumenten
  - [ ] Viz: discussieboom + score + dekking in het hyperedge-detailpaneel
  - [ ] **Klaar wanneer:** alle 12 hyperedges kunnen argumenten dragen en tonen een
        score met dekking

- [ ] **M1.6 Gevoeligheidsanalyse** (Z7)
  - [ ] `scripts/analyse_gevoeligheid.py`: leave-one-cluster-out over alle
        theorie-elementen; parameter-sweep over de `scoring.py`-constanten
  - [ ] Rapport: top-10 kwetsbaarste elementen; advies voor het M1.4-plafond;
        resultaat zichtbaar in het dashboard
  - [ ] **Klaar wanneer:** het rapport draait herhaalbaar en de SPOF-lijst staat in
        het dashboard

- [ ] **M1.7 Influence bewijsbaar**
  - [ ] `scoring.py`: `property='influence'`-argumenten verschuiven de afgeleide
        invloed (handmatige kolom blijft de prior)
  - [ ] Viz + DOCUMENTATIE.md: beide assen tonen hun bewijs
  - [ ] **Klaar wanneer:** een influence-argument verschuift de sterkte aantoonbaar
        in `/api/scores`

- [ ] **M1.8 Monitor-agent** (→ §6.2)
  - [ ] Beslissen + doorvoeren: `objection_type` als kolom of property-conventie
        (migratie + `schema.sql`)
  - [ ] Missie-brief schrijven: drogreden-taxonomie, ondergraving vs weerlegging,
        verplichte stap-citatie, alles landt als `voorgesteld`
  - [ ] Agent-account aanmaken (M0.6-CLI) en ronde 1 over het bestaande corpus draaien
        (Claude Code background agent, §6.2-runtime)
  - [ ] Menselijke review van ronde 1: vals-positief-ratio meten, brief bijstellen
  - [ ] **Klaar wanneer:** een ronde levert reviewbare bevindingen, < 50% vals-positief,
        0 directe statuswijzigingen

- [ ] **M1.9 Scout-agents** (→ §6.3)
  - [ ] Blind-zoekprotocol als missie-brief (neutrale vraag, tweezijdige oogstplicht,
        afwezigheidsrapport)
  - [ ] Query- en brief-logging inrichten (auditbaar)
  - [ ] Eerste missie op een zwak onderbouwd mechanisme; nieuwheid + stance-balans
        meten in het dashboard
  - [ ] **Klaar wanneer:** de missie levert bronnen voor beide stances óf een gelogd
        afwezigheidsrapport

### Fase 2 — openstellen

- [ ] **M2.1 Identiteit volwaardig**
  - [ ] Migratie: `contributed_by`/`changed_by` → FK naar `users` (bestaande
        tekstwaarden mappen op accounts of een `legacy`-account)
  - [ ] Reviewer-/maintainer-rollen per filter (koppeltabel)
  - [ ] Regel afdwingen: niemand verifieert eigen werk (API-check auteur ≠ beoordelaar)
  - [ ] **Klaar wanneer:** elke mutatie is herleidbaar tot een account en
        zelf-verificatie is technisch onmogelijk

- [ ] **M2.2 Voorstel-workflow**
  - [ ] Status `voorgesteld` toevoegen (CHECK + `scoring.py`: telt als 0)
  - [ ] Merge-flow: reviewer accepteert (`voorgesteld` → `ongecontroleerd` of
        `bronvermelding_nodig`); `merged_by` vastleggen — zelf-merge is dan afleidbaar
        (auteur = merger) en wordt gevlagd (§6.1)
  - [ ] Score-diff-preview: herberekening op een tijdelijke kopie mét het voorstel;
        delta tonen in de review-UI
  - [ ] Review-wachtrij in de viz (openstaande voorstellen)
  - [ ] **Klaar wanneer:** een voorstel telt pas mee na merge en de reviewer ziet
        vooraf de score-impact

- [ ] **M2.3 Theory-RfC**
  - [ ] Sjabloon vastleggen: definitie, aard-keuze + freeze-test, afgrenzing van
        bestaande elementen, falsificatiecriterium, ≥ 1 instantiatie, ≥ 1
        onafhankelijke bron
  - [ ] Twee-reviewer-eis op de theorielaag afdwingen (rolpoort + merge-regel)
  - [ ] De M0.4-restlijst als eerste RfC's indienen
  - [ ] **Klaar wanneer:** een nieuw theorie-element kan alleen nog via een RfC ontstaan

- [ ] **M2.4 Anti-misbruik**
  - [ ] Rate-limits per account; recent-changes-feed + watchlist op `edit_log`
  - [ ] Duplicaatdetectie (stdlib-tekstsimilariteit per target; bewust geen externe
        embeddings — repo-conventie)
  - [ ] **Klaar wanneer:** een dubbele claim wordt bij indienen gesignaleerd en de
        feed toont alle mutaties

- [ ] **M2.5 Ratings & bridging**
  - [ ] Tabel `argument_ratings` (beoordelaar × argument × oordeel + gestructureerde
        redenen; UNIQUE per paar)
  - [ ] Ratings-UI per argument; agent-ratings zichtbaar als advies (§6.4)
  - [ ] Kalibratiescript: agent-oordelen vs latere menselijke uitkomsten → verdiend,
        gecapt gewicht; agent×agent telt nooit
  - [ ] Bridging-model (matrixfactorisatie, stdlib) activeren zodra de pool divers
        genoeg is (§6.6); tot die tijd gelden de noodregels
  - [ ] **Klaar wanneer:** weight in laag A komt uit bridged ratings zodra de pool het
        toelaat

- [ ] **M2.6 Splitsen & samenvoegen (granulariteitsbeheer)**
  - [ ] Voorwaarde-migratie: padclaims verwijzen nu naar rolnámen (`property_value`) —
        omzetten naar id-verwijzing, anders breken ze stil bij hernoemen, splitsen of
        samenvoegen
  - [ ] `lineage`-tabel (oud element → opvolger(s), richting, voorstel-id, datum) +
        status `vervangen` op rollen, mechanismen, entiteiten, relaties én hyperedges;
        `scoring.py`, `influence.py` en de viz slaan vervangen elementen over; de API
        beantwoordt oude ID's met een verwijzing naar de opvolger(s)
  - [ ] Voorstelsjabloon (RfC-conventie van M2.3): betrokken elementen, richting
        (splitsen / samenvoegen / hernoemen), nieuwe definitie(s) + aard-keuze,
        afgrenzing, en een hertriage-plan voor al het aanhangende bewijs
  - [ ] Merge-hertriage in de review-UI: checklist per aanhangend argument —
        herbevestigd voor de bredere claim → verhuist mee; niet herbevestigd → blijft
        bij het vervangen element en telt nergens meer in mee
  - [ ] Split-hertriage: restlijst (argumenten, relaties, instantiaties, padclaims)
        moet leeg zijn vóór afronding; relaties zo nodig dupliceren met eigen
        certainty/influence per opvolger
  - [ ] Validator-checks (uitbreiding M0.1): padclaim- of afgeleide-routes door
        `vervangen` elementen → fout; lineage-rij zonder geaccepteerd voorstel → fout
  - [ ] `scripts/analyse_granulariteit.py`: kandidaten vlaggen via argument-overlap,
        gedeelde citaties en stdlib-tekstgelijkenis → voedt de onderzoeksagenda (M3.2),
        beslist niets
  - [ ] **Klaar wanneer:** één samenvoeging en één splitsing zijn end-to-end via het
        voorstelpad uitgevoerd (op een kopie-DB of op een echte kandidaat) met lege
        hertriage-restlijst, werkende oude ID's en herberekende scores zonder
        dubbeltelling

### Fase 3 — levend & falsifieerbaar

- [ ] **M3.1 Modelreleases**
  - [ ] `scripts/release_model.py`: git-tag + scores-snapshot (JSON) +
        changelog-sjabloon + score-diff t.o.v. de vorige release
  - [ ] Releasetag tonen in de viz
  - [ ] **Klaar wanneer:** er bestaan twee releases en hun score-diff is leesbaar

- [ ] **M3.2 Onderzoeksagenda**
  - [ ] `scripts/onderzoeksagenda.py`: ranglijst sterkte × bewijsarmoede (dekking =
        bronclusters, argumenten, stance-balans)
  - [ ] In het dashboard + als voordeur voor nieuwkomers (§6.5)
  - [ ] **Klaar wanneer:** de lijst draait en stuurt aantoonbaar de eerstvolgende
        scout-missie (M1.9)

- [ ] **M3.3 Adversarial rondes** (voorproef = prioriteit 4 in §8)
  - [ ] Red-team-brief (doel: sterkste eerlijke tegenbewijs, geen stromannen)
  - [ ] Voorproefronde: top-20 invloedrijkste edges (ranking uit `influence.py`),
        handmatig of als agent-missie; bevindingen als contradicting/contextual args
  - [ ] Ritme afspreken + een externe criticus uitnodigen als co-reviewer (§6.5)
  - [ ] **Klaar wanneer:** de stance-balans van de top-20 is geen 98/2 meer en de
        ronde is herhaalbaar

- [ ] **M3.4 Voorspellingsregister**
  - [ ] Tabel `predictions` (claim, afleiding uit het model, deadline, uitkomst,
        score) + minimale UI/CLI
  - [ ] De eerste 3–5 voorspellingen afleiden en vastleggen vóórdat de uitkomst
        bekend is
  - [ ] **Klaar wanneer:** minstens één voorspelling is gescoord en er een
        kalibratierapport bestaat

- [ ] **M3.5 Jaarlijkse audit**
  - [ ] Auditchecklist vastleggen (aard/tiers, bronclassificaties, halo-criteria;
        precedent: juni 2026)
  - [ ] Eerstvolgende audit inplannen (juni 2027)
  - [ ] **Klaar wanneer:** audit 2027 is uitgevoerd en gedocumenteerd
