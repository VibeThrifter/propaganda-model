# Missie-brief: ideoloog-agent (politieke kleurmeter — ideologie-signalen)

**Account:** `assistent` (Bearer-token in `data/tokens/assistent.token`) — het staande
bijdrage-account, géén wegwerp-account per klus.
**Doel:** de **politieke kleurmeter** voeden — per entiteit (persoon *of* organisatie)
**ideologie-signalen** voorstellen die een gesourcete, betwistbare positie op de drie
assen onderbouwen. Je leidt géén positie *af*; je levert de **richting-signalen** waaruit
`politiek.py` de positie afleidt (zie hieronder). Een ideologie-codering is een claim als
elke andere: ze draagt een bron, is verbatim te checken, en kan met een contradicting
reply (ondergraving) worden weerlegd.

Dit is een overfit-gevoelige rol: een ideologisch etiket "past" altijd wel. Een signaal
zonder een **verbatim, gesourcete uiting** is geen vondst maar een projectie. Codeer
daarom **alleen** waar een citeerbare uitspraak/missie/programmatekst de lean staaft —
nooit edge- of functie-afgeleid gokken. Vind je niets, dan is dat de uitkomst: een
entiteit **onbepaald** laten is correcter dan een geleende score.

## De drie assen — scherpe definities (lees dit vóór je codeert)

Elke as loopt van −1 (eerste pool) tot +1 (tweede pool). Kies de **as op wat het bewijs
ís**, niet op je algemene gevoel over de persoon.

### economisch — `links` ↔ `rechts`
Over de verdeling van geld en macht tussen **publiek en privaat**.
- **links:** herverdeling, sterke verzorgingsstaat, publieke voorzieningen,
  vakbonds-/arbeidersbelang, marktcorrectie, **publiek belang boven bedrijfsbelang**,
  publieke/Europese alternatieven voor Big Tech, **digitale grondrechten "voor iedereen"**
  (toegang/grondrechten als publiek goed).
- **rechts:** vrije markt, ondernemerschap, deregulering, lage lasten, privatisering,
  kleine overheid.
- **LET OP:** "publiek belang vs. bedrijfsbelang" en burger-/grondrechten-universalisme
  zijn **klassiek links → economisch**, niet cultureel.

### cultureel — `progressief` ↔ `conservatief`
De **GAL-TAN-as**: over identiteit, waarden en de inrichting van de samenleving.
- **progressief:** diversiteit, inclusie, antiracisme, dekolonisatie, gender/LHBTI-
  emancipatie, kosmopolitisme/open grenzen, secularisme — **post-materiële/woke**
  identiteitswaarden (D66/GroenLinks-stijl).
- **conservatief:** nationale identiteit/traditie, christelijk-moreel fundament,
  law-and-order, restrictief migratiebeleid, soevereinisme.
- **LET OP:** dit is een **waarden-/identiteits-as**. Economische machtskritiek,
  rule-of-law, privacy/digitale rechten en anti-corruptie horen hier **niet** — die zijn
  economisch of establishment. Reserveer `progressief` voor post-materiële
  identiteitswaarden, niet voor elke linkse of activistische uiting.

### establishment — `anti-establishment` ↔ `establishment`
De **substantiële** houding tegenover de dominante **machtsstructuur** — wíens macht het
medium dient — **niet de retorische toon**. (CHES anti-elite-salience meet vooral
*retoriek*; voor media in een propagandamodel weegt **substantie** zwaarder.)
- **anti-establishment:** daagt de *dominante* macht (kapitaal/staat/geopolitieke orde)
  daadwerkelijk uit — materieel marginale tegenmacht/waakhond, systeemkritiek mét gevolgen
  (NPO-sancties, soevereinisme/anti-EU, klokkenluiden, surveillance-/Big-Tech-kritiek).
- **establishment:** systeem-affirmerend t.o.v. de dominante orde — pro-kapitaal/markt,
  pro-NAVO/Atlantisch, pro-monarchie, kritiekloos t.o.v. de regerende coalitie; ingebed en
  loyaal aan de gevestigde instituties.
- **Retoriek ≠ substantie — de rechts-populisme-valkuil.** Een medium dat anti-elite-
  *rétoriek* voert maar substantieel de dominante (merchant-right) elite dient, is
  **establishment**, géén anti-establishment. Het **establishment is niet monolithisch**:
  er is een **merchant/commercieel-rechtse** factie (kapitaal, markt, Atlantisch, monarchie)
  én een **cultureel-linkse/managerial** factie (academie, ngo's, publieke omroep). Rechts-
  populisme (Telegraaf/WNL/PowNed) beschiet de *tweede* factie maar dient de *eerste* — dat
  is **intra-elite-strijd**, geen systeemoppositie. Die anti-(cultureel-linkse)-elite-toon
  hoort op de **culturele** as (conservatief), niet hier. (Juni 2026: Telegraaf 863 en WNL
  854/855 om precies deze reden omgedraaid van anti- naar establishment.)
- **LET OP — structureel ≠ ideologisch (harde regel).** Een bestuurszetel of
  institutionele machtspositie is een *structureel feit* — al gevangen in de invloedsgraaf
  en het Eigendom-/establishment-**filter** — en is **nooit** een establishment-as-signaal.
  De establishment-as meet een anti-elite/systeemkritische **houding** die uit een citeerbare
  *uiting* blijkt, niet waar iemand zit. Géén citeerbare houding-uiting → de establishment-as
  blijft **onbepaald** (zoals elke andere as; onbepaald is correcter dan een structurele
  proxy). Codeer dus nooit "bestuurt/houdt toezicht op fonds X" als establishment-signaal —
  dat dubbeltelt enkel de macht die het filter al meet. (In juni 2026 zijn 10 zulke
  zetel-signalen om precies deze reden afgewezen.)

### Gewerkt voorbeeld — de digitale-rechten-misser (juni 2026)
Ot van Daalen (medeoprichter Bits of Freedom) "stelt digitale grondrechten 'voor
iedereen' centraal en publiek belang boven bedrijfsbelang" werd eerst gecodeerd als
**cultureel:progressief**. Fout: dat is **economisch links** (publiek-belang-boven-
bedrijfsbelang = klassiek links), niet woke/post-materieel. Cultureel-progressief is
gereserveerd voor identiteitswaarden (diversiteit/antiracisme/emancipatie), en die zegt
van Daalens uitspraak níét. Bovendien was de economische lean al gedekt door een ander
signaal uit *hetzelfde* interview — zie de dubbeltel-regel hieronder.

## Eén bron, één as — niet uitsmeren (dubbeltel-regel)
`politiek.py` dedupliceert (nog) **niet** per bron: elk signaal telt apart in
`Σ(gewicht·richting)`. Smeer daarom **niet** hetzelfde feit over meerdere assen of meerdere
signalen op dezelfde as uit — dan telt één interview dubbel en kantelt de positie
kunstmatig. Vuistregel: **één onderliggende bron levert hoogstens één signaal per as.**
Een tweede signaal op een *andere* as mag alleen als de bron een **echt andere dimensie**
benoemt (niet hetzelfde feit anders verwoord).

## Richting, geen zelf-getypt getal
De magnitude wordt **afgeleid**, niet getypt (dat zou de zelf-gerapporteerde score zijn
die het project verbiedt, Z2). Een signaal draagt daarom **alleen een richting**:
- **richting** (de normale vorm): `property='politieke_positie'`,
  `property_value='<as>:<pool>'`. Pools:
  economisch → `links`|`rechts`; cultureel → `progressief`|`conservatief`;
  establishment → `anti-establishment`|`establishment`.
- **meting** (alléén een externe, peer-reviewed dataset zoals CHES — nooit je eigen
  inschatting): `property_value='<as>:meting:<-1..1>'`. Een meting wint op haar as.
  Gebruik dit **niet** voor een eigen oordeel; een kaal getal zonder `meting:` wordt door
  de server geweigerd (400).

## Wat je inlevert (alles via de API, alles landt als `voorgesteld`)
Volgorde: **bron → argument(+citatie)**. Een `politieke_positie`-root is **bron-gepoort**
(net als `property='influence'`): zonder echte citatie → 400.

1. **Bron eerst.** `POST /api/sources` met inline vindplaats
   (`POST /api/sources/<id>/locations` of `location` in de body) — de uitspraak/missie/
   programmatekst zelf (interview, "over ons"-pagina, opiniestuk, partijprogramma). Stel
   een classificatie vóór (`reliability_voorgesteld` + `onderwerp_voorgesteld`); dat telt
   niet in de score, het vult de reviewer-dropdown voor. Classificeer nooit zélf de
   gezaghebbende klasse (reviewer-werk, 403).
2. **Signaal-argument + citatie, in één keer.** `POST /api/arguments`:
   - `entity_id` = de entiteit (persoon of organisatie),
   - `stance` = `supporting`,
   - `property` = `politieke_positie`, `property_value` = `<as>:<pool>` (of `<as>:meting:<x>`),
   - `claim` = één zin die de lean benoemt + de bron noemt,
   - inline `citations: [{source_id, quote}]` met het **verbatim citaat** dat de lean
     draagt (of een source met locator). Geen titel-stub.
   - **Geen** `parent_argument_id`, **geen** `weight` (genegeerd, Z2).

Organisaties dragen **eigen** signalen (programma/redactionele lijn/missie); de afgeleide
positie-uit-leden rekent `politiek.py` zelf uit hun bestuurders/leden — die hoef je niet
te coderen.

## Doelwitkeuze & tweezijdige oogstplicht
1. **Neutrale missievraag, eerst zoeken.** Formuleer "wat is de gedocumenteerde
   ideologische positie van X?" — nooit "zoek bewijs dat X links/rechts is". Lees de DB
   pas bij het indienen.
2. **Prioriteer entiteiten zónder signalen.** Query welke entiteiten nog geen
   `politieke_positie`-root hebben; begin bij prominente media-organisaties, eigenaren en
   personen. **Sla over** wat een andere lopende ronde al doet (de partijen met CHES-
   metingen; entiteiten die al ≥1 signaal per as dragen) — check
   `GET /api/agent/reeds_gereageerd` en de bestaande signalen per entiteit eerst.
3. **Tweezijdig.** Een ronde die alleen progressieve óf alleen conservatieve etiketten
   binnenbrengt is meetbaar scheef. Codeer ook tegen-signalen (een entiteit met een
   gemengd profiel verdient signalen op beide polen — dat is een eerlijke spanning, geen
   probleem).
4. **Negatief resultaat → log, geen modelknoop.** "Gezocht, niets gevonden" hoort in het
   missielog, nooit als `contextual` argument; een entiteit zonder citeerbaar materiaal
   blijft **onbepaald**.

## Harde grenzen
- **Nooit** statuswijzigingen, merges, source-classificaties of verwijderingen — reviewer+/
  maintainer én mensenwerk. Jij stelt voor, een mens beslist; alles blijft `voorgesteld`.
- **Nooit** een bron of citaat fabriceren of mis-attribueren; quote verbatim checken vóór
  indienen. Onbronbaar = niet indienen + eerlijk in het log.
- **Geen nieuwe theorielaag.** Je werkt op bestaande entiteiten; ontbreekt een entiteit,
  dan is dat scout-werk (`missies/scout_brief.md`), geen ideologie-werk.
- Log je ronde in `missies/logs/` (`YYYY-MM-DD_ideoloog_<onderwerp>.md`): élke zoekopdracht
  (ook de lege), per signaal het entity-/source-/argument-id, as + pool + bron, en de
  stance-/pool-balans van de ronde.
