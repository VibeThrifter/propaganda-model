# Reviewbeoordelaar — ronde 3: webverificatie van verdachte citaten

**Datum:** 2026-06-21
**Agent:** reviewbeoordelaar (geen account, alleen-lezen; web alleen lézend)
**Scope:** gerichte citaat-/bronverificatie van 10 kandidaten — supporting-roots met
een lege quote of alleen een locator, plus #544 (citaat dekt de claim niet).
**Niet in scope:** de wereld onderzoeken of nieuw bewijs zoeken. Ik toets alléén of
de geciteerde bron bestaat en de claim *zoals geciteerd* dekt.

De 42 bestaande adviezen uit ronde 2 zijn behouden; alleen de gecheckte items zijn
verrijkt met een `bron_check`-veld. Drie verdicts zijn na de webcheck verzwaard
(#549 toelichting, #564 en #566 van verdict gewijzigd).

---

## Per item: wat gecheckt, query/URL, uitkomst

### #544 — supporting · rel.477 (PAX→FD) — quote dekt overname-claim niet
- **Bron 85** "Don't Bank on the Bomb (PAX/ICAN-rapportenreeks)", loc: `https://paxvoorvrede.nl/wat-wij-doen/programmas/dont-bank-on-the-bomb/`
- WebFetch van die URL.
- **Uitkomst:** URL resolvet. De quote ("…gezamenlijk project van PAX en ICAN…jaarlijks
  onderzoek naar investeringen in kernwapenproducenten") staat er **letterlijk**. MAAR de
  pagina noemt het FD of Nederlandse financiële media **niet** — de overname-claim ("FD
  neemt snel en ongecontroleerd over") wordt door deze bron **niet** gedekt.
- **Verdict ongewijzigd:** verbeteren (citaat-dekking). Webcheck bevestigt de eerdere grond.

### #546 — supporting · rel.479 (NWO→Radboud) — NWA-quote leeg
- **Bron 89** "Nationale Wetenschapsagenda (NWA) — thematische programmering", loc:
  `https://www.nwo.nl/en/researchprogrammes/dutch-research-agenda-nwa/thematic-programming` (lege quote)
- **Bron 88** Rathenau (26%-quote — generieke recycling)
- WebFetch van beide URL's.
- **Uitkomst:** Beide URL's resolveren en zijn echte bronnen. De NWA-pagina spreekt van
  "collaboration with societal partners (including governments…)" maar bevestigt *niet*
  expliciet dat overheid/partners de thema's mede *bepalen* en zo de agenda sturen — de
  specifieke sturingsclaim mist een dragende quote. De Rathenau-26%-quote is letterlijk
  correct (zie #545).
- **Verdict ongewijzigd:** verbeteren (specifieke claim niet met dragende quote gedekt).

### #547 — supporting · rel.480 (Radboud→NOS) — sterke claim, lege quote
- **Bron 90** "Academische vrijheid in Nederland: een begripsanalyse en richtsnoer" (KNAW, 2021),
  loc: `https://pure.knaw.nl/portal/nl/publications/academische-vrijheid-in-nederland-een-begripsanalyse-en-richtsnoe` (lege quote)
- WebFetch van die URL.
- **Uitkomst:** Echte KNAW-publicatie uit 2021 (57 p., advies). MAAR gaat over academische
  vrijheid in het algemeen — dekt de specifieke expertrol/sourcing-claim (consensus
  gereproduceerd als neutraal nieuwsframe) niet rechtstreeks. Poort haalt het via de
  locator, dragende quote ontbreekt.
- **Verdict ongewijzigd:** verbeteren.

### #548 — supporting · rel.481 (Tweede Kamer→Radboud, flak) — quotes leeg + buitenlandse casussen
- **Bron 91** FNV "Kabinet bezuinigt 1 miljard…": URL resolvet, bevestigt **letterlijk**
  "Het kabinet bezuinigt 1 miljard op hoger onderwijs en wetenschap." (NL-casus, klopt)
- **Bron 92** Inside Higher Ed (CEU/Hongarije 2018): echt artikel, klopt — buitenlands
- **Bron 93** The Conversation (Bolsonaro/Brazilië 2019): echt artikel, klopt — buitenlands
- **Bron 94** NBC News (DeSantis SB 266, 2023): URL gaf 403 bij WebFetch; via WebSearch
  ("DeSantis signs SB 266 defunding diversity DEI programs Florida colleges NBC News 2023")
  bevestigd dat het artikel **bestaat** met exact deze inhoud — geen verzonnen bron, alleen
  bot-blokkade. Buitenlands.
- **Uitkomst:** Alle vier bronnen zijn echt en kloppen feitelijk. Bevinding ongewijzigd:
  alle quotes leeg, en drie van de vier casussen zijn buitenlands en staan ver van
  flak-op-Radboud; alleen de Schoof-bezuiniging is NL-relevant.
- **Verdict ongewijzigd:** verbeteren (trim naar NL-casus of voeg dragende quotes toe).

### #549 — supporting · rel.482 (zelfcensuur BuZa→PAX) — stance-fout + bron-mismatch
- **Bron 83** titel "PAX Jaarverslag — financiering en herkomst inkomsten", maar loc:
  `https://nl.wikipedia.org/wiki/PAX_(vredesorganisatie)` (lege quote)
- WebFetch van die Wikipedia-URL.
- **Uitkomst:** De URL is **geen jaarverslag** maar de Wikipedia-pagina, en die bevat de
  >80%-staatssubsidie-/BuZa-/Power-of-Voices-claim **niet** — alleen omzet (€17,3 mln 2023)
  en donaties (€0,84 mln 2023). De brontitel suggereert een jaarverslag dat de >80%-claim
  zou dekken; de feitelijke vindplaats doet dat niet. Verkeerd toegeschreven locator.
- **Verdict ongewijzigd (verbeteren), grond verzwaard:** behalve de al gevlagde stance-fout
  (F-35-tegenbewijs begraven in de supporting-root) dekt de enige citatie de kernclaim
  (>80% afhankelijkheid) óók niet — de titel belooft een jaarverslag, de URL is Wikipedia
  zonder dat cijfer.

### #562 — supporting · rel.485 (draaideur Van Nieuwenhuizen→Energie-Nederland)
- **Bron 95** NOS `https://nos.nl/l/2502916`: WebFetch — resolvet, bevestigt dat zij zich
  als minister met de energiesector bemoeide vóór ze lobbyist werd.
- **Bron 96** FTM `https://www.ftm.nl/artikelen/cora-van-nieuwenhuizen-negeert-lobbyverbod`:
  WebFetch gaf 403 (paywall/bot-blokkade). Via WebSearch ("Cora van Nieuwenhuizen
  lobbyverbod Energie-Nederland Follow the Money Jetten") bevestigd dat het FTM-artikel
  **bestaat** en exact dit dekt — incl. voorzitterschap Energie-Nederland en lobbyverbod.
- **Uitkomst:** Beide bronnen echt en dekken de claim. (Detail: de overstap was 2021, de
  bemoeienis-affaire kwam in 2023 uit — de claim zegt "in 2021…direct over"; dat klopt.)
- **Verdict ongewijzigd:** merge-klaar (bevestigd).

### #563 — supporting · rel.487 (draaideur Hillen→NIDV)
- **Bron 99** Materieelgezien `https://magazines.defensie.nl/materieelgezien/2017/08/06mg201708hillennidv`
- WebFetch.
- **Uitkomst:** Echt artikel. Bevestigt: Hillen nam per **1 oktober 2017** het
  NIDV-voorzitterschap over van Karla Peijs. Dekt de claim.
- **Verdict ongewijzigd:** merge-klaar (bevestigd).

### #564 — supporting · rel.488 (draaideur Eijsink→NIDV) — DATUMFOUT
- **Bron 98** NIDV `https://www.nidv.eu/nieuws/angelien-eijsink-benoemd-tot-voorzitter-nidv/`
- WebFetch + WebSearch ("Angelien Eijsink voorzitter NIDV benoemd jaar 2021 Hans Hillen opvolger").
- **Uitkomst:** De NIDV-pagina bestaat en bevestigt de benoeming, MAAR per **1 oktober 2021**
  (aankondiging 22 maart 2021), als **opvolger van Hans Hillen** — niet "in 2017". 2017 was
  juist het jaar dat Hillen aantrad (#563). De claim noemt 2017; de eigen cited source
  weerspreekt dat. Web (FD, parlement.com, NIDV) bevestigt unaniem 2021.
- **Verdict GEWIJZIGD:** merge-klaar → **verbeteren**. Feitelijke datumfout: zet "2017" om
  naar "2021" (opvolger van Hillen). Bron is echt en correct; de claim is onjuist.

### #565 — supporting · rel.489 (draaideur Knops→NIDV)
- **Bron 97** NIDV `https://www.nidv.eu/nieuws/raymond-knops-nieuwe-voorzitter-nidv/`
- WebFetch.
- **Uitkomst:** Echt persbericht. Bevestigt **letterlijk**: "Raymond Knops treedt per
  1 april 2023 aan als voorzitter van de Stichting Nederlandse Industrie voor Defensie
  en Veiligheid." Dekt de claim (2023) volledig.
- **Verdict ongewijzigd:** merge-klaar (bevestigd).

### #566 — supporting · rel.492 (draaideur Ollongren→YES) — locator dekt claim niet
- **Bron 100** "Kajsa Ollongren - Wikipedia", loc: `https://en.wikipedia.org/wiki/Kajsa_Ollongren` (lege quote)
- WebFetch van die URL + WebSearch ("Kajsa Ollongren Yalta European Strategy YES board Pinchuk 2024").
- **Uitkomst:** De Wikipedia-pagina bestaat maar noemt **YES / Yalta European Strategy
  nergens** — de enige citatie dekt de claim dus niet. (Observatie, géén afwijsgrond: de
  wereld-claim zelf klopt wél — officiële YES-bron
  `https://yes-ukraine.org/en/news/kaysa-ollongren-uviyshla-do-skladu-pravlinnya-yaltinskoyi-yevropeyskoyi-strategiyi-yes`
  bevestigt dat Ollongren in 2024 tot het YES-bestuur toetrad. Tip voor de bijdrager/scout:
  vervang de Wikipedia-locator door deze YES-bron.)
- **Verdict GEWIJZIGD:** context → **verbeteren**. De citatie (Wikipedia) dekt de
  YES-toetreding niet; voeg de officiële YES-bron toe. (De relevantie-kanttekening uit
  ronde 2 — YES is een internationaal forum, geen NL-branchelobby — blijft staan.)

---

## Conclusie

| Item | Bron(nen) | Uitkomst | Verdict |
|------|-----------|----------|---------|
| #544 | PAX-pagina | bevestigd (quote letterlijk; FD-overname niet gedekt) | verbeteren (ongewijzigd) |
| #546 | NWA + Rathenau | bevestigd echt; sturingsclaim niet door quote gedekt | verbeteren (ongewijzigd) |
| #547 | KNAW | bevestigd echt; dekt expertrol-claim niet direct | verbeteren (ongewijzigd) |
| #548 | FNV/IHE/Conversation/NBC | alle 4 echt + feitelijk juist; quotes leeg, 3 buitenlands | verbeteren (ongewijzigd) |
| #549 | "PAX Jaarverslag" = Wikipedia | bron-mismatch: Wikipedia dekt >80%-claim niet | verbeteren (grond verzwaard) |
| #562 | NOS + FTM | beide echt, dekken claim | merge-klaar (ongewijzigd) |
| #563 | Materieelgezien | echt, dekt claim (Hillen 2017) | merge-klaar (ongewijzigd) |
| #564 | NIDV | **datumfout**: benoeming 2021, niet 2017 | **verbeteren (gewijzigd)** |
| #565 | NIDV | echt, dekt claim letterlijk (Knops 2023) | merge-klaar (ongewijzigd) |
| #566 | Wikipedia Ollongren | locator dekt YES-claim niet (claim zelf klopt; YES-bron bestaat) | **verbeteren (gewijzigd)** |

**Samengevat:** 10 kandidaten gecheckt. **0 gehallucineerde/verzonnen bronnen** — alle
geciteerde bronnen bestaan echt en resolveren (twee 403's bleken bot-blokkades, via
WebSearch bevestigd). **Wel twee citatie-/feitproblemen die het web onthulde:**

1. **#564** — de claim dateert de Eijsink-benoeming op 2017, maar de eigen cited NIDV-bron
   (en FD/parlement.com) zegt 2021. Een verifieerbare datumfout: van merge-klaar naar
   verbeteren.
2. **#566** — de Wikipedia-locator dekt de YES-claim niet (Wikipedia noemt YES niet); van
   context naar verbeteren. De wereld-claim klopt wél en een officiële YES-bron bestaat —
   gemeld als tip, niet als afwijsgrond.

Plus een verzwaarde grond bij **#549** (de "PAX Jaarverslag"-titel is feitelijk een
Wikipedia-URL zonder het >80%-cijfer). De zes draaideur-feiten (Van Nieuwenhuizen, Hillen,
Knops) en de NL-bezuinigingsbron (#548) zijn solide bevestigd. **Geen enkele check
rechtvaardigt een afwijzing** — bij twijfel verbeteren, conform de brief.
