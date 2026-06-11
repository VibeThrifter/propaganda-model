# Memeonderzoek: framework & pijplijn (ontwerp)

> **Status: ontwerp, 11 juni 2026 — er is hiervan níéts gebouwd.** Dit document beschrijft een
> tweede onderzoeksprogramma naast `VERBETERPLAN_DISCUSSIESYSTEEM.md`. Dat plan maakt de
> *structuur* van het model robuust (de buizen); dit framework ontwerpt het volgen van *inhoud*
> die door die structuur stroomt (het water): memes, frames en memecomplexen. Bouwen gebeurt pas
> op expliciete opdracht, per stap uit de checklist in §10. Schemawijzigingen volgen dan het
> vaste patroon: backup-dan-migreren, `schema.sql` mee-updaten, `DOCUMENTATIE.md` blijft de
> specificatie van wat live staat.

## 0. Kernidee en leeswijzer

Het bestaande model beschrijft **wie wie kan beïnvloeden**: een statisch netwerk van rollen,
mechanismen, entiteiten en relaties. Dit framework voegt de dynamische tegenhanger toe: **wat er
daadwerkelijk doorheen reist**. Een meme — een herkenbare zinsnede, een frame, een
beleidsvoorstel-met-belang — verschijnt ergens, wordt gekopieerd, gemuteerd, geselecteerd en
dooft uit of bereikt een evenwicht. De vijf filters van Herman & Chomsky zijn in die termen een
*selectieomgeving*: ze bepalen welke memes doorgang vinden en welke sterven.

De winst is tweeledig:

1. **Zichtbaarheid**: verspreiding als olievlek over de bestaande graaf — waar dook het meme het
   eerst op, langs welke schakels reisde het, waar versnelde het (zelfversterking), waar stokte
   het (poortwachters, demping), waar ligt het evenwicht.
2. **Falsifieerbaarheid**: de scherpste toets die dit model kan krijgen. Het propagandamodel
   voorspelt *differentiële verspreiding*: elite-dienende memes reizen door hetzelfde netwerk
   sneller en breder dan elite-kritische. Met gedateerde, bebronde waarnemingen is dat meetbaar —
   en dus ook weerlegbaar.

Omdat "alle memes van Nederland ooit" niet kan, is het ontwerp **dossier-gedreven**: een klein
aantal expliciet geselecteerde memes wordt diep en volgens protocol gevolgd (case studies), en
memecomplexen worden niet continu maar via **sentinelmemes en periodieke steekproeven** gemeten.
§1 definieert de eenheden, §3 lost het selectieprobleem op, §5 geeft de pijplijn van intake tot
rapport, §6 behandelt de complexen, §10 de fasering met afvinkbare stappen.

## 1. Wat volgen we? Drie granulariteiten

| niveau | eenheid | voorbeeld | detectie | welke claims zijn geldig |
|---|---|---|---|---|
| **frase-meme** | herkenbare zinsnede + mutaties | "vestigingsklimaat", "graaiflatie", "linkse hobby's" | tekstmatching (stdlib) + handwerk | waarnemingen, adoptiecurves, transmissiehypothesen t/m de hoogste bewijsklassen |
| **frame-meme** | duiding/claim, niet aan één formulering gebonden | "de overheid moet als een bedrijf worden gerund" | codeboek + mens/agent-codering, dubbelcodering | adoptie en prevalentie per entiteit; transmissie alleen bij expliciet bewijs |
| **memecomplex** | samenhangende bundel frames + frasen rond een kern (ideologie, belang) | "BV Nederland / marktwerking" | niet direct: sentinelmemes + periodieke panelmeting | prevalentietrends, dominantie en homogeniteit per outlet, koppeling aan het Ideologie-filter |

**Vuistregel: hoe grover de eenheid, hoe zwakker de causale claims die het bewijs kan dragen.**
Een frase-meme laat letterlijke overname zien (soms zelfs met gedeelde tikfouten — een
vingerafdruk); een frame vergt interpretatie; een complex is alleen als trend te meten. Het
datamodel dwingt dit af via bewijsklassen op transmissies (§5/P4, appendix C): op complexniveau
bestaan geen transmissieclaims, alleen prevalentie.

Terminologie-eerlijkheid: "memetics" als discipline is omstreden; dit framework leunt
methodisch op gevestigde velden — *intermedia agenda-setting* (hoe media onderwerpen van elkaar
overnemen), framing-analyse (Entman), informatiediffusie op netwerken, en frasetracking à la
MemeTracker (Leskovec et al. 2009, die letterlijke zinsneden en hun mutaties door de
Amerikaanse nieuwscyclus volgden). "Meme" is hier dus een werkwoord-arm containerbegrip, geen
theorieclaim.

## 2. Verhouding tot het bestaande model

**Mechanismen zijn de dragers.** De theorielaag beschrijft al hóé memes reizen:

| mechanisme/filter | meme-operator |
|---|---|
| pakketjournalistiek (ANP-copy) | replicatie met hoge kopieertrouw |
| sourcing (toegang tot officiële bronnen) | toegangsselectie: wie mag memes inbrengen |
| flak | negatieve selectie: georganiseerde tegendruk op specifieke memes |
| advertentie/eigendom | selectieomgeving: welke memes zijn commercieel/structureel veilig |
| ideologie-halo's (frame-export, sociologische homogeniteit) | staand memecomplex: de achtergrondselectie |
| tegenmacht-mechanismen | demping en tegenmemes |

Concreet betekent dit: een transmissie kan optioneel een `mechanism_id` dragen ("deze overname
liep via ANP-copy", "dit frame kwam binnen via de lobbyroute"). Aggregatie daarvan beantwoordt
per dossier de vraag *welk filter deed het werk* — structurele attributie in plaats van
daderdenken.

**De invloedgraaf is de plausibiliteitstoets.** `influence.py` levert voor elke
transmissiehypothese de structurele vraag: bestaat er überhaupt een edge of pad van zender naar
ontvanger, en hoe sterk? Temporele volgorde + structureel pad = zwak maar toelaatbaar bewijs
(klasse 4, appendix C); temporele volgorde zónder pad is óf toeval, óf gemeenschappelijke bron,
óf — interessantst — een ontbrekende edge.

**De meme-laag is omgekeerd een detector voor het structuurmodel.** Drie terugkoppellussen:

1. Herhaalde transmissies tussen twee entiteiten zonder relatie in de instantielaag → kandidaat
   **ontbrekende edge**, automatisch op de onderzoeksagenda (M3.2).
2. Een complex dat aantoonbaar persistent, outlet-overstijgend en richting-consistent is →
   instantiërend bewijs voor een **Ideologie-halo** (koppeling via de gewone bewijslaag).
3. Waargenomen zelfversterking — acceleratie zodra rollagen elkaar gaan echoën (media citeren
   politici die media citeren) → kandidaat-instantiatie van een **emergent effect** (hyperedge).

Zo wordt "hoe komen we dynamisch tot een beter model" letterlijk: de stroomdata genereert
hypothesen voor de structuur, de structuur toetst de stroomclaims.

**De bewijslaag wordt hergebruikt, niet gedupliceerd.** Elke waarneming is een citaat (bron
verplicht — de citatiepoort M0.3 geldt onverkort); elke transmissieclaim krijgt een eigen
discussieboompje met steun en tegenspraak; meme-dossiers volgen de voorstelroutes (M2.2/M2.3);
en als een dossier achteraf twee dingen blijkt te vermengen ("dit zijn eigenlijk twee frames"),
gelden de splits/samenvoeg-regels van M2.6 ook hier.

## 3. Het selectieprobleem: dossiers, geen volledigheid

Alles volgen kan niet en hoeft niet — maar *wat* je kiest bepaalt wat je kunt concluderen.
Selectie is daarom zelf een gereguleerde stap:

- **Intakecriteria** (alle vijf vereist):
  1. *relevantie* — het dossier toetst ten minste één filterhypothese uit de theorielaag;
  2. *traceerbaarheid* — onderscheidende signatuur, afgebakend tijdvenster, beschikbaar corpus;
  3. *gewicht* — maatschappelijke of beleidsmatige inzet (anders is de uitkomst oninteressant);
  4. *contrastwaarde* — is er een vergelijkbaar meme met tegengestelde belangenrichting te
     paren (§8)?
  5. *capaciteit* — er is plek binnen het plafond van actieve dossiers (start: **max 3**).
- **Contrastparen**: op termijn verplicht. Voor elk elite-dienend dossier een vergelijkbaar
  elite-kritisch dossier — zelfde domein, vergelijkbare periode en nieuwswaardigheid waar
  mogelijk. Wie alleen memes volgt die het model bevestigen, meet zijn eigen gelijk; dit is de
  anti-homofilie-regel uit het verbeterplan (§6) toegepast op caseselectie.
- **Selectieregister**: óók afgewezen kandidaten worden gelogd, met reden. Cherry-picking moet
  achteraf controleerbaar zijn.
- **Intake = voorstel in de discussieboom**: een dossier wordt ingediend met volledige
  preregistratie (appendix B) en gereviewd zoals een theorievoorstel (M2.3-route; zolang er
  geen tweede reviewer is geldt de koudstartregel uit het verbeterplan).
- **Dossierstatussen**: `voorgesteld → actief → afgerond | gestaakt`. Staken mag, maar met
  reden — een dossier dat onuitvoerbaar bleek is data over het protocol zelf.

## 4. Datamodel (ontwerp — niet gebouwd)

Vijf nieuwe tabellen, maximaal leunend op wat er al is (`entities`, `sources`, `citations`,
`arguments`, `mechanisms`, `users` zodra M0.6 bestaat):

- **`memes`** — id, `naam`, `type` (`frase` | `frame` | `complex`), `definitie`, `signatuur`
  (frase: kernvormen en bekende varianten; frame: verwijzing naar codeboekversie), `status`
  (§3), preregistratievelden (verwachte oorsprongsrol, verwachte route over roltypen, verwachte
  dragende filters, verwacht contrastresultaat, falsificatiecriterium), `contrast_meme_id`
  (nullable), tijdvenster, datums.
- **`meme_members`** — `complex_id` → `meme_id`, met `is_sentinel` (§6). Een complex is zelf een
  rij in `memes` met `type='complex'`.
- **`meme_observations`** — `meme_id`, `entity_id` (de uiter), **`citation_id` verplicht**,
  `datum_uiting` (≠ datum van registratie), `kanaal` (krant/tv/Kamer/persbericht/online),
  `variant_tekst` (frase) of `codering` (frame: welke codeboek-indicatoren raak waren),
  `coder` (user, mens of agent), `status` (`ongecontroleerd` → `bevestigd`/`verworpen`;
  reviewer ≠ coder, conform de geen-zelfverificatie-regel van M2.1).
- **`meme_transmissions`** — `meme_id`, `van_entity_id`, `naar_entity_id`, `bewijsklasse` (1–5,
  appendix C), `mechanism_id` (nullable: de drager), `certainty`, datumvenster, en een
  root-argument in de discussieboom. **Alleen geclaimde transmissies worden opgeslagen**;
  kandidaten (temporeel + structureel afgeleid) worden berekend en gesuggereerd, nooit
  automatisch vastgelegd — hetzelfde principe als de afgeleide pijlen in de viz, die ook nooit
  worden opgeslagen.
- **`meme_search_log`** — `meme_id`, corpus, zoekvraag, periode, uitvoerder, datum,
  `aantal_treffers`. **Nul treffers is betekenisvolle data**: zonder vastgelegde stilte is
  "outlet X negeerde dit meme" niet te onderscheiden van "niemand heeft gekeken" — en valt de
  poortwachterstoets (§7) weg.

Ontwerpprincipes: variantclusters en mutatieketens worden bij analyse afgeleid (normalisatie +
similariteit + tijdsordening), niet opgeslagen. Entiteitsgranulariteit: outletniveau is de
standaard; persoonsniveau wanneer de uiting persoonsgebonden is (politicus, columnist) — bestaat
de entiteit nog niet, dan eerst via de gewone voorstelroute. Geen nieuwe dependencies: matching
en statistiek blijven stdlib.

## 5. De pijplijn: zeven stappen per dossier

**P1 — Intake & preregistratie.** Dossiervoorstel met appendix B volledig ingevuld, *vóór* er
ook maar één zoekopdracht draait: verwachte oorsprong (roltype), verwachte route (in welke
volgorde adopteren roltypen het meme — belanghebbende → intermediair → politiek → media →
publiek, of juist anders), verwachte dragende filters, verwacht verschil met het contrastmeme,
en een falsificatiecriterium ("als X, dan klopt onze verwachting niet"). Poort: review als
theorievoorstel. *Wie:* mens beslist, agents mogen kandidaten aandragen.

**P2 — Corpusafbakening & zoekprotocol.** Welke bronnen, welk tijdvenster, welke zoektermen
(inclusief spellings- en mutatievarianten) — vastgelegd vóór uitvoering, elke uitgevoerde
zoekopdracht in de zoeklog. Realistische corpora: Delpher, krantenarchieven en -sites, NOS/NU,
officielebekendmakingen.nl (Handelingen en Kamerstukken — goud voor politieke memes),
persberichtenarchieven, Wayback Machine. Social media is grotendeels een blinde vlek
(API-toegang is realistisch gezien weg): per dossier expliciet noteren, niet wegmoffelen.

**P3 — Oogst & registratie.** Agents draaien het zoekprotocol en dienen kandidaat-waarnemingen
in mét citaat (landingsstatus `ongecontroleerd`). Frase: matching op genormaliseerde vormen
(kleine letters, interpunctie weg, n-gram-overlap, difflib-ratio) plus handwerk voor de randen.
Frame: codeboek (appendix A); eerst dubbelcodering op een steekproef (mens × agent of mens ×
mens), poort: **Cohen's kappa ≥ 0,7** vóór er solo gecodeerd mag worden; twijfelgevallen worden
contextuele argumenten in de boom, zodat de codeboekgrens zelf bediscussieerbaar is.

**P4 — Transmissiehypothesen.** Elke claim "B nam het van A over" krijgt een bewijsklasse
(appendix C): (1) expliciete attributie; (2) gedeelde unieke mutatie of fout — de
vingerafdruk; (3) letterlijke overname zonder attributie; (4) temporeel + structureel
plausibel pad; (5) louter temporeel. Klassen 4–5 mogen als hypothese bestaan maar krijgen lage
certainty en mogen schakelstatistiek nooit domineren. Standaardcheck bij 3–5: de
gemeenschappelijke-bron-confound (kopieerden beiden gewoon het ANP?) als verplicht
tegenargument in het boompje.

**P5 — Dynamiek-analyse.** Per dossier, stdlib-scripts: adoptiecurve (cumulatief aantal
entiteiten in de tijd), groeifase (exponentieel / lineair / plateau / afname via
venster-groeivoeten), adoptieratio per venster, halfwaardetijd na de piek, persistentie. En de
modelspecifieke maat: **rollaag-volgorde** — in welke volgorde bereiken roltypen het meme? Dat
is de geregistreerde routeverwachting uit P1 rechtstreeks toetsbaar gemaakt.

**P6 — Structurele attributie & terugkoppeling.** Transmissies aggregeren op `mechanism_id`:
welk filter droeg dit meme? Ontbrekende-edge-kandidaten naar de onderzoeksagenda;
complex-bevindingen naar halo-instantiaties; acceleratie-met-echo naar hyperedge-kandidaten
(§2).

**P7 — Rapport & falsificatie.** Case-rapport tegen de preregistratie: wat klopte, wat niet,
wat bleef onbeslist. Contrastpaar-vergelijking zodra het paar compleet is. Uitkomsten —
bevestigend én weersprekend — naar het voorspellingsregister (M3.4). **Een dossier dat de
modelvoorspelling weerspreekt is een topresultaat** en gaat met voorrang het rapport in; dat is
de Popper-afspraak uit het verbeterplan, hier herhaald omdat de verleiding bij stroomdata het
grootst is.

## 6. Memecomplexen: hoe dan?

Het eerlijke antwoord: een complex volg je niet rechtstreeks — het is te diffuus om te matchen
en te groot om te coderen. De oplossing is drielagig:

1. **Sentinelmemes** (indicatorsoorten, zoals een ecoloog een ecosysteem meet): per complex 3–7
   leden, gekozen op onderscheidendheid, spreiding over dragers (politiek, media, lobby) en
   verschillende levensfasen (één opkomend, één gevestigd, één omstreden). Die worden continu
   gevolgd via de gewone pijplijn (P2–P5).
2. **Periodieke panelmeting**: per kwartaal een *samengestelde week* (constructed week sampling,
   de standaardmethode uit de inhoudsanalyse: zeven dagen getrokken uit verschillende weken,
   zodat weekdag-effecten uitmiddelen) over een vast outlet-panel, gecodeerd tegen het
   complex-codeboek. Dat geeft een prevalentietijdreeks per outlet die onafhankelijk is van de
   sentinelkeuze — de correctie op je eigen selectie.
3. **Complex-dashboard**: aggregatie van de ledencurves + de panelreeks; dominantie per outlet;
   en vooral **divergentie tussen outlets**: homogeen hoge prevalentie over redactioneel
   verschillende outlets is een aanwijzing voor een staande selectieomgeving (Ideologie-halo),
   heterogeniteit is een tegenwijzing.

Complex-claims gaan dus over prevalentie, samenhang en homogeniteit — nooit over transmissie.
Een complex dat duurzaam, outlet-overstijgend en richting-consistent blijkt, levert
instantiërend bewijs voor het Ideologie-filter; zakt de prevalentie aantoonbaar na
tegenmacht-events (onderzoeksjournalistiek, WOB-onthullingen), dan is dát genoteerde demping.

## 7. Meetlatten & statistiek (alles stdlib-haalbaar)

| maat | wat het meet | let op |
|---|---|---|
| adoptiecurve & groeifase | verspreidingsverloop, zelfversterking vs verzadiging | first-seen ≠ ontstaan (linkscensuur) |
| adoptieratio per venster | nieuwe adopters per actieve adopter — besmettelijkheid | géén epidemiologische R claimen |
| halfwaardetijd & persistentie | uitdoving vs evenwicht | rechtscensuur bij lopende memes |
| rollaag-volgorde | wie eerst: belanghebbende, politiek, media, publiek? | dé modelvoorspelling per dossier |
| vroegheidsindex | gemiddelde adoptiepositie van een entiteit over dossiers heen | pas zinvol bij meerdere dossiers |
| doorgeefgraad | uitgraad in geclaimde transmissies, gewogen naar certainty | klasse 4–5 nooit dominant |
| brugpositie | betweenness op de transmissiegraaf (BFS) | idem |
| **poortwachterssterfte** | fractie memes die de inputbuurt van entiteit X bereikt maar bij X nooit verschijnt | alleen geldig met gevulde zoeklog — anders is afwezigheid meetfout |
| contrastpaar-toets | tekentoets/permutatietoets over paren elite-dienend vs elite-kritisch | accumuleert traag; elk paar is óók een zelfstandige case |
| onzekerheid | bootstrap over waarnemingen | consistent met M1.3 |

De poortwachterssterfte verdient nadruk: het maakt de gatekeeper-rol — die nu alleen
theoretisch bestaat — voor het eerst empirisch meetbaar, en hij is precies de reden dat de
zoeklog geen bureaucratie is maar meetinstrument.

## 8. Wetenschappelijke waarborgen & grenzen

- **Preregistratie** (P1) tegen achteraf-verhalen; **selectieregister** (§3) tegen
  cherry-picking; **contrastparen** tegen overfitten op het eigen gelijk.
- **Causaliteit**: homofilie en besmetting zijn in observationele netwerkdata formeel niet te
  scheiden (Shalizi & Thomas 2011); gelijktijdig opduiken bewijst geen overdracht. Daarom: de
  waarneming is hard, de transmissie is altijd hypothese met bewijsklasse, en de
  gemeenschappelijke-bron-check is verplicht.
- **Censuur en corpusbias**: oorsprong kan vóór het corpus liggen (rapporteer first-seen mét
  corpusgrens, claim nooit "ontstaan bij"); lopende memes zijn rechtsgecensureerd; het corpus
  overdekt online en onderdekt print, omroep en social — per dossier expliciet.
- **Frame-codering is interpretatief**: kappa-poort, geversioneerde codeboeken met besluitlog,
  twijfels als contextuele argumenten in de boom.
- **Complotkader-waakzaamheid**: "waar komt het vandaan" glijdt makkelijk naar "wie zit
  erachter". De onderzoeksvraag is structureel — *welk filter selecteerde en versterkte dit* —
  en oorsprong is vaak diffuus en overgedetermineerd. Rapporten formuleren in
  selectie/structuur-termen; dit is dezelfde framing-regel die voor het hele model geldt
  (emergent, geen complot).
- **Capaciteit**: het dossierplafond is hard. Liever drie dossiers afgerond met lege
  hertriage-lijsten dan tien half — een half dossier heeft negatieve waarde, want het oogt als
  bewijs maar draagt niets.

## 9. Agents in de pijplijn

Alle agentwerk loopt als Claude Code background agents op het Max-abonnement, via dezelfde REST
API en met dezelfde accountplichten als menselijke gebruikers (verbeterplan §6, M0.6/M2.1) —
geen aparte integratie. Rollen, gemapt op de pijplijn:

| agent | stap | taak | mag niet |
|---|---|---|---|
| oogst-agent | P2/P3 | zoekprotocol draaien, kandidaat-waarnemingen + citaat indienen, zoeklog vullen | eigen waarnemingen bevestigen |
| codeer-agent | P3 | tweede codeur voor kappa; steekproef-hercodering | codeboek eigenhandig wijzigen |
| transmissie-agent | P4 | kandidaten afleiden (temporeel × structureel), bewijsklasse schatten | claims boven klasse 4 zelf vastleggen |
| analyse-agent | P5 | curves en maten herberekenen, afwijkingen van de preregistratie signaleren | conclusies in rapporten schrijven |
| waakhond (M1.8) | overal | drogreden- en logicacontrole, ook op meme-claims | — |

Menspoorten: dossier-acceptatie (P1), codeboek-vaststelling, bevestiging van transmissieclaims
klasse 1–3, en het eindrapport (P7). De koudstart-kanttekening uit het verbeterplan geldt
onverkort: alle LLM-agents vormen één gecorreleerd cluster en tellen nooit als onafhankelijke
bevestiging van elkaar.

## 10. Fasering & uitvoeringschecklist

Zelfde conventie als verbeterplan §9: een vinkje pas wanneer het onderdeel **werkend en
geverifieerd** is. Volgorde-afhankelijkheid: MT0 kan grotendeels als papierwerk starten, maar
de migratie (MT1) wil de validator (M0.1) en de citatiepoort (M0.3) uit het verbeterplan als
fundament. Dit programma dringt niet voor op Fase 0/1 van het verbeterplan.

### MT0 — fundament (afspraken & ontwerp, geen code)

- [ ] Dossiersjabloon + preregistratievelden vastgesteld (appendix B als startpunt)
- [ ] Bewijsladder + certainty-banden vastgesteld (appendix C als startpunt)
- [ ] Selectieregister + intakecriteria operationeel (mag als markdown beginnen, DB later)
- [ ] Datamodelontwerp (§4) gereviewd tegen het live schema (kolomnamen, FK's, statussen)
- [ ] **Klaar wanneer:** een eerste dossiervoorstel formeel kan worden ingediend en beoordeeld

### MT1 — pilot: één frase-meme end-to-end (handmatig)

- [ ] Eén dossier geaccepteerd (kandidaten: §11), preregistratie vastgelegd vóór de oogst
- [ ] Migratie `migrate_add_memes.py` (backup-dan-migreren; `schema.sql` mee; validator-checks
      uitgebreid: waarneming zonder citaat = fout, transmissie zonder bewijsklasse = fout)
- [ ] Zoekprotocol uitgevoerd (handmatig/agent-geassisteerd), waarnemingen + citaten + zoeklog
- [ ] Transmissieclaims met bewijsklassen en eigen discussieboompjes
- [ ] `scripts/analyse_meme.py` (stdlib): adoptiecurve, groeifase, rollaag-volgorde, schakels
- [ ] Case-rapport tegen de preregistratie, uitkomst in het voorspellingsregister (M3.4)
- [ ] **Klaar wanneer:** het dossier `afgerond` is, elke waarneming een citaat heeft, elke
      transmissie een bewijsklasse + boompje, en het rapport expliciet benoemt wat de
      preregistratie wél en níét goed voorspelde

### MT2 — opschalen & contrast

- [ ] Oogst-agent draait als background agent met eigen account (vereist M0.6)
- [ ] Tweede dossier = contrastpaar van het eerste (elite-kritisch tegenover elite-dienend)
- [ ] Transmissie-suggestiescript: afgeleide kandidaten tonen, nooit automatisch opslaan
- [ ] Zoeklog-dekking afdwingbaar → poortwachterssterfte voor het eerst geldig meetbaar
- [ ] **Klaar wanneer:** de eerste contrastpaar-vergelijking in het voorspellingsregister staat

### MT3 — complexen, differentiële toets & viz

- [ ] Eerste complex-dossier: codeboek + sentinelkeuze + kwartaalpanel (constructed week)
- [ ] Complex-dashboard: ledencurves, panelreeks, outlet-divergentie
- [ ] Differentiële toets over ≥ 3 contrastparen (teken-/permutatietoets, stdlib)
- [ ] Viz: tijdslider + olievlek-animatie + transmissie-overlay in de bestaande D3-graaf
      (via `web/template.html` en de generator — `web/index.html` nooit met de hand)
- [ ] Terugkoppellussen actief: ontbrekende-edge-kandidaten en halo-instantiaties stromen
      automatisch naar de onderzoeksagenda (M3.2)
- [ ] **Klaar wanneer:** één complex minstens een jaar panelmeting heeft én minstens één
      structurele ontdekking (nieuwe edge, halo-instantiatie of hyperedge-kandidaat) aantoonbaar
      uit memedata is voortgekomen

## 11. Pilotkandidaten (kandidaten — geen besluit)

1. **"vestigingsklimaat"** (frase, venster ± 2017–2019, dividendbelasting-episode).
   Gedocumenteerd elitebelang (VNO-NCW-lobby, later via WOB-stukken boven), scherp tijdvenster,
   onderscheidende term, rijk corpus (Handelingen, kranten, persberichten), bekende
   tegenbeweging. Sterkste eerste kandidaat: alles aan de casus is al publiek gedocumenteerd,
   dus de pilot toetst het *protocol*, niet de archiefkunst.
2. **"graaiflatie"** (frase, 2023–…). Elite-kritisch (FNV-omgeving), onderscheidend, recent en
   doorzoekbaar corpus. Natuurlijke contrastkandidaat voor (1), al verschilt de periode —
   matchingbeperking expliciet in het paar-rapport noteren.
3. **Complex "BV Nederland / marktwerking"** — sentinelkandidaten: "vestigingsklimaat",
   "lastenverlichting", "banenmotor", "BV Nederland"; panel van 4–6 landelijke outlets. Pas ná
   MT1/MT2: een complex als eerste dossier is een recept voor verzanden.

De verwachte routes en filters worden hier bewust níét ingevuld: dat hoort in de preregistratie
(P1), ná acceptatie en vóór de oogst — anders is dit document zelf al een achteraf-verhaal.

## Appendix A — codeboeksjabloon (frame-meme)

Per frame-meme één geversioneerd codeboek: **kernclaim** (één zin); **insluitcriteria** (welke
uitingen tellen, ook zonder de letterlijke woorden); **uitsluitcriteria** (wat er lijkt op maar
niet telt — citaten-van-critici, ironie, berichtgeving óver het frame); **randgevallen** met
uitspraak en motivering (groeit tijdens het coderen, wijzigingen via de discussieboom);
**voorbeelden** (≥ 3 positief, ≥ 3 negatief, uit het echte corpus); **versie + datum +
besluitlog**. Hercodering van de steekproef bij elke versie-bump.

## Appendix B — dossiersjabloon (preregistratie)

Naam + type; definitie/signatuur (frase: kernvormen + varianten; frame: codeboekversie);
tijdvenster + corpora + zoektermen; score op de vijf intakecriteria; **hypothesen**: verwachte
oorsprongsrol, verwachte rollaag-route, verwachte dragende filters/mechanismen, verwacht
verschil met het contrastmeme; **falsificatiecriterium** ("onze verwachting is weerlegd als…");
capaciteitscheck (plafond); reviewbesluit + datum. Het ingevulde sjabloon is onderdeel van het
dossier en wordt na acceptatie niet meer gewijzigd — wel aangevuld met een afwijkingenlog.

## Appendix C — bewijsladder transmissies → certainty-banden

| klasse | bewijs | certainty-band |
|---|---|---|
| 1 | expliciete attributie ("aldus ANP", bronvermelding, letterlijk citaat met verwijzing) | 0,85–0,95 |
| 2 | gedeelde unieke mutatie of fout (vingerafdruk: dezelfde verhaspeling, dezelfde foute datum) | 0,70–0,85 |
| 3 | letterlijke overname zonder attributie (identieke formulering, geen verwijzing) | 0,50–0,70 |
| 4 | temporele volgorde + structureel plausibel pad in de invloedgraaf | 0,20–0,40 |
| 5 | louter temporele volgorde | 0,05–0,15 |

Regels: klasse 4–5 nooit dominant in schakelstatistiek (doorgeefgraad, brugpositie); bij klasse
3–5 is de gemeenschappelijke-bron-check (ANP, persbericht, gedeeld evenement) een verplicht
tegenargument in het discussieboompje; opwaardering van klasse kan alleen met nieuw bewijs, niet
met meer waarnemingen van hetzelfde type.
