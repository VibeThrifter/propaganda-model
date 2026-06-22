# Verbinder-agent — missie-ronde 1

- **Datum:** 2026-06-20
- **Account:** `verbinder-agent` (bijdrager, agent)
- **Brief:** `missies/verbinder_brief.md` @ git `0cb647383b6270ac2ebccf3bd2417ed8506ea639`
- **Doel:** het netwerk laten groeien — nieuwe knopen + verbanden voorstellen die het
  model mist (instantielaag), niet bestaande claims beargumenteren.

## Onderwerpkeuze (anti-overfit)

`python3 scripts/onderzoeksagenda.py` → `data/onderzoeksagenda.json` (gegenereerd
2026-06-20). Vijf hoog-geprioriteerde theorie-elementen dragen het label **"geen
praktijk-instanties"** — precies wat de verbinder hoort te vullen:

- `#121 ledeneis` (eigendom) — prio 0.331
- `#123 erkenningverlening` (eigendom) — prio 0.331
- `#124 omroepsignatuur` (ideologie) — prio 0.331
- `#63 sociologische_homogeniteit` (ideologie) — prio 0.278
- `#86 institutioneel_gezag` (sourcing) — prio 0.277

De eerste drie beschrijven alle drie het **Nederlandse publieke omroepbestel**
(ledendrempel, erkenning door OCW, statutaire signatuur) en zijn met openbare registers
(CvdM, Rijksoverheid) en nieuwsbronnen controleerbaar. Gekozen onderwerp: **toetreding
en erkenning van nieuwe (aspirant-)omroepen in het publieke bestel.**

DB pas ná het zoeken gelezen voor de koppeling. Bestaande omroepknopen aanwezig
(BNNVARA, KRO-NCRV, AVROTROS, EO, VPRO, MAX, PowNed, WNL, NPO, NOS, CvdM, OCW), maar de
twee **nieuwste toetreders ontbraken** als knoop, en mechanismen #121/#123/#124 hadden
**nul** relaties.

## Neutrale missievraag

"Welke publieke omroep(verenigingen) hebben recent erkenning bij CvdM/OCW gezocht of
verloren, welke ledeneisen en statutaire identiteit (signatuur) speelden daarbij, en wie
beslist over toelating?" — geen modelclaim ingebakken.

## Queries (letterlijk)

Web (WebSearch / WebFetch), alle op 2026-06-20:

1. WebSearch: `Ongehoord Nederland erkenning Commissariaat voor de Media ledental aspirant-omroep`
2. WebSearch: `Omroep ZWART erkenning publieke bestel ledental aspirant 2021 2022`
3. WebFetch: `https://www.rijksoverheid.nl/onderwerpen/media-en-publieke-omroep/nieuws/2021/07/08/twee-nieuwe-aspiranten-krijgen-voorlopige-erkenning` → **HTTP 404** (pagina verplaatst/gearchiveerd; niet gebruikt — niet geciteerd)
4. WebFetch: `https://www.cvdm.nl/nieuws/commissariaat-maakt-uitkomst-ledentelling-bekend/` → **socket gesloten** (niet bereikbaar; niet gebruikt — niet geciteerd)
5. WebFetch: `https://www.villamedia.nl/artikel/elf-aspirantomroepen-haalden-eindstreep-inclusief-nieuwkomers-ongehoord-nederland-en-omroep-zwart` → ledentelling, drempels 50.000/100.000, €5,72 contributie, "twee nieuwkomers"
6. WebFetch: `https://nl.wikipedia.org/wiki/Nederlands_publiek_omroepbestel` → ledeneisen, rol minister OCW, toetreding 2022 (achtergrond, niet geciteerd als bewijsbron)
7. WebSearch: `Ongehoord Nederland erkenning intrekken NPO journalistieke code boetes 2022 2023 staatssecretaris Uslu`
8. WebSearch: `Omroep ZWART signatuur diversiteit inclusie statuten missie Akwasi oprichting`
9. WebFetch: `https://www.rijksoverheid.nl/actueel/nieuws/2023/11/27/ongehoord-nederland-behoudt-voorlopige-erkenning` → Uslu behoudt erkenning, juridische grond, 27-11-2023
10. WebFetch: `https://nos.nl/artikel/2499470-ongehoord-nederland-mag-voorlopig-blijven-besluit-uslu` → "te weinig juridische basis", politiek afstand tot inhoud
11. WebFetch: `https://www.villamedia.nl/artikel/ongehoord-nederland-krijgt-derde-sanctie-van-npo-boete-van-bijna-132.000-euro` → derde sanctie ~€132.000, NPO-verzoek tot intrekken, Karskens voorzitter
12. WebSearch: `Ongehoord Nederland oprichters Arnold Karskens omroep oprichting 2020 conservatief rechts` → oprichters/oriëntatie ON (achtergrond entiteit-beschrijving)

## Oogst (alles via REST API, alles `voorgesteld`)

**Bronnen** (`POST /api/sources`, met url-locator + voorgestelde classificatie — adviserend):

| id | titel | classificatie-voorstel | cluster_key |
|----|-------|------------------------|-------------|
| 115 | Ongehoord Nederland behoudt voorlopige erkenning (Rijksoverheid, 2023-11-27) | institutioneel / nl_systeem | rijksoverheid-on-erkenning-2023 |
| 116 | Ongehoord Nederland mag voorlopig blijven, besluit Uslu (NOS, 2023-11-27) | regulier / nl_systeem | nos-on-erkenning-2023 |
| 117 | ON krijgt derde sanctie van NPO: boete bijna 132.000 euro (Villamedia, 2023-04) | regulier / nl_systeem | villamedia-on-sancties-2023 |
| 118 | Elf (aspirant)omroepen haalden eindstreep … (Villamedia, 2021-03-31) | regulier / nl_systeem | villamedia-ledentelling-2021 |

**Nieuwe entiteiten (knopen)** (`POST /api/entities`, type `omroep`, geen score-cijfers):

| id | naam | nieuwheid |
|----|------|-----------|
| 205 | Ongehoord Nederland | nieuwe knoop (bestond niet) |
| 206 | Omroep ZWART | nieuwe knoop (bestond niet) |

**Nieuwe verbanden (edges)** (`POST /api/relations`, certainty/influence leeg → vloer 0.05):

| id | edge | relation_type | mechanisme |
|----|------|---------------|------------|
| 496 | Ministerie van OCW (132) → Ongehoord Nederland (205) | regulering | #123 erkenningverlening |
| 497 | CvdM (50) → Ongehoord Nederland (205) | regulering | #121 ledeneis |
| 498 | CvdM (50) → Omroep ZWART (206) | regulering | #121 ledeneis |
| 499 | NPO (131) → Ongehoord Nederland (205) | oppositie | geen (zie negatief resultaat) |

**Argumenten** (`POST /api/arguments`, supporting root + inline citaat, hard-gate gehaald):

| arg-id | op rel | stance | bronnen |
|--------|--------|--------|---------|
| 585 | 496 | supporting | 115 + 116 (Uslu behoudt erkenning) |
| 586 | 497 | supporting | 118 (ledentelling, drempel 50.000) |
| 587 | 498 | supporting | 118 (ledentelling, drempel 50.000) |
| 588 | 499 | supporting | 117 (NPO-verzoek tot intrekken + €132k boete) |

## Stance-balans van de ronde

- 4 supporting / 0 contradicting / 0 contextual.
- Tweezijdigheid is geborgd in de **inhoud**, niet in de stance-tellers: edge 499
  (NPO → ON, oppositie) en argument 585 (OCW koos op 27-11-2023 om de erkenning van een
  rechts/dissident omroep **niet** in te trekken, met expliciet "politiek moet afstand
  houden tot de inhoud van het bestel") zijn **model-compliceren­de tegenmacht-vondsten**:
  een toezicht-/disciplineringsdynamiek bínnen het bestel én een staat die haar
  erkenningsmacht juist terughoudend inzet. Alle vier de argumenten zijn `supporting`
  omdat ze het *bestaan* van het verband staven (de stance volgt het bewijs over het
  doel, niet de sympathie); het compliceren zit in wat het bewijs over de richting van
  de macht zegt.

## Nieuwheid

- 2 volledig nieuwe knopen (geen hercitaties).
- 4 volledig nieuwe edges (geen van de mechanismen #121/#123 had eerder een relatie; #124
  bleef leeg — zie negatief resultaat).
- 4 nieuwe bronnen (geen hergebruik).

## Negatieve resultaten / niet kunnen staven

- **Mechanisme #124 omroepsignatuur (INTERN niveau) niet geïnstantieerd.** De
  definitie beschrijft een *zelf-eigenschap* van een omroep (de statutaire signatuur
  stuurt de eigen redactie). De relatie-grammatica eist source ≠ target, dus een
  "ZWART → ZWART"- of "ON → ON"-edge kan niet. Er is geen schone externe ankerknoop
  zoals bij omroepverzuiling (#100: BNNVARA→PvdA). Niet geforceerd aan een verkeerd
  mechanisme gehangen; laat dit hier na als modelleer-keuze (redactie-deelknoop of
  node-property/halo) — geen verbinder-werk.
- **Twee primaire/officiële bronnen onbereikbaar:** de Rijksoverheid-pagina uit 2021
  (404) en de CvdM-ledentellingpagina (socket gesloten). Niet geciteerd; de
  ledentelling is in plaats daarvan gestaafd via Villamedia (bron 118) met letterlijke
  drempel- en contributiecijfers. Een reviewer kan desgewenst de CvdM-/Rijksoverheid-
  primaire bron later toevoegen of via Wayback archiveren.
- **Exacte ledenaantallen van ON en ZWART** (boven de 50.000-drempel) niet met een
  controleerbaar getal gevonden in de bereikte bronnen — alleen "haalden de drempel".
  Daarom in claim/beschrijving géén precies ledental beweerd.
- **Mechanismen #63 (sociologische_homogeniteit) en #86 (institutioneel_gezag)** deze
  ronde niet aangepakt (buiten het gekozen omroepbestel-onderwerp); blijven open voor
  een volgende ronde.

## Verificatie achteraf

`python3 scripts/monitor_agents.py` toont onder `verbinder-agent`: 2 voorgestelde
entiteiten, 4 voorgestelde relaties, 4 bronnen, 4 argumenten — allemaal status
`voorgesteld`. Niets gemerged/geclassificeerd/verwijderd (mensenwerk).
