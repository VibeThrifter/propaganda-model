# Missielog — ESG-verkenning: wat is er te koppelen aan het model?

- **Datum:** 2026-08-03
- **Account:** `assistent` (bijdrager) — alles ingediend als `voorgesteld`
- **Aanleiding:** eigenaarsvraag *"Is er nog iets van ESG's te koppelen aan het model?"*
- **Opzet:** vier parallelle onderzoekssporen (repo+DB · NL-greenwashing/advertentie · institutionele
  beleggers/CSRD · ideologisch frame · flak+tegenmacht), daarna een **verplichte
  herverificatieronde** vóór indienen (eigenaarskeuze).

---

## 1. Hoofdoordeel: "ESG" valt af als thema, filter of ideologie-mechanisme

Het bewijs snijdt er **tégen**, en dat is de belangrijkste uitkomst van deze ronde:

- Investico + Follow the Money + De Groene vielen ESG frontaal aan (*Great Green Investment
  Investigation*): van €6 biljoen "duurzaam" belegd vermogen streeft *"slechts 4 procent"* daadwerkelijk
  een betere wereld na. ESG is in de NL-media een **onderzoeksobject**, geen ongemarkeerd consensusframe.
- De rechter oordeelde 15 van 19 KLM-duurzaamheidsclaims misleidend (ECLI:NL:RBAMS:2024:1512).
- *Greenhushing*: het frame trekt zich terug, niet uit.
- Degrowth zit **ín** het NL-debat (De Groene, VPRO Tegenlicht; Amsterdam adopteerde formeel het
  donutmodel) — marginaal in volume, niet buiten het zegbare.
- Larry Fink installeerde en de-installeerde de term binnen vijf jaar (2020 → 2023/25). Een frame dat
  één CEO kan aan- en uitzetten is een **elite-modecyclus**, geen structureel filter.

Bijkomend: een nieuw thema zou hoe dan ook een schema-migratie vergen (`mechanism_themes.theme` is een
gesloten CHECK-enum) én zakken voor de toelatingslat uit het `systemisch`-verwijderprecedent.

**Wat er wél te koppelen is, past zonder uitzondering in bestáánde mechanismen — geen enkele RfC nodig.
Dat is zelf een bevinding.** Het zwaartepunt ligt bovendien niet bij ESG-als-frame maar bij het
**agro/stikstof-dossier**.

## 2. Herverificatie — twee correcties op de deelonderzoeken

Elke quote is tegen het primaire document gecontroleerd (`data.rechtspraak.nl` XML werkt waar
`uitspraken.rechtspraak.nl` en de persberichten 403 geven; PDF's lokaal uitgelezen).

| Gecorrigeerd | Wat er mis was |
|---|---|
| **Geen dwangsom in ECLI:NL:RBOVE:2025:4639** | Het deelonderzoek meldde "dwangsom tot €1 mln" bij deze uitspraak. Onjuist: de Overijsselse uitspraak (10-07-2025, niet 15-07) kent alleen €907 proceskosten. De dwangsom (€50k/dag, max €1 mln) hoort bij een **apart** civiel kort geding in Den Haag van 04-09-2025. Twee zaken, twee maanden uit elkaar. |
| **Eumedion "Annual Report 2025" bestaat niet** | De Abma-nevenfuncties werden geciteerd uit een niet-bestaand jaarverslag 2025, p. 37. De werkelijke primaire vindplaats is **Annual Report 2024, p. 55** (en p. 18 voor de organisatie-posities). Inhoud klopte, vindplaats niet. |

Overige quotes bleken wél exact: het `misbruik van bevoegdheden`-oordeel, het `vertragen`-oordeel, de
DPG-quote bij Villamedia, de BNR-verkooppagina, Eumedions `active media policy`, de Clintel-uitspraak
(8 uitlatingen beoordeeld, precies 1 onrechtmatig) en de Nijpels-functiedata bij parlement.com.

## 3. Ingediend (alles `voorgesteld` — 14 bronnen · 8 entiteiten · 14 relaties · 26 argumenten)

### Blok 1 — agro/Woo-keten (sterkste vondst)
Eén causale keten over drie filters, primair gedocumenteerd. Journalisten vroegen bedrijfsgegevens van
alle NL-veehouderijen op *"om te berekenen hoe effectief het stikstofbeleid is"*; boeren + **Farmers
Defence Force** procedeerden tegen openbaarmaking; de minister trok haar besluiten tijdens de zitting in;
de rechtbank: *"De minister heeft misbruik gemaakt van haar bevoegdheden"*, handelen dat *"niet anders kan
worden begrepen dan een actie om de openbaarmaking (…) te vertragen"*.

- Entiteiten **1219** LTO Nederland, **1220** Farmers Defence Force
- Relaties **2221/2222/2223** — Min. LNV → FTM / Omroep Gelderland / NRC, `censuur`, **mech 32
  `woo_obstructie`** (precedent: rel. 1132 VWS→Nieuwsuur gebruikt hetzelfde relatietype)
- Argumenten 3735–3737

### Blok 2 — Eumedion: sluit de openstaande reviewkritiek op mechanisme 171
De reviewbeoordelaar merkte in juni 2026 op dat `belanghebbende_als_adviseur` alleen de BlackRock/EC-casus
draagt en "niet het NL-mediasysteem" raakt. **Dat gat is nu gevuld**, volledig uit Eumedions eigen
primaire documenten:

- **Relatie 2226** Eumedion → AFM, `adviseur`, **mech 171** — de beleggerslobby zit in het AFM Capital
  Market Committee, de AFM Financial Reporting and Accounting Committee én het AFM Advisory Panel of
  Representative Organisations (Annual Report 2024, p. 18).
- **Relatie 2227** Eumedion → FD, `bron_van`, **mech 51 `lobbyist_naar_journalist`** — Eumedion legt zijn
  mediastrategie schriftelijk vast (*"it will pursue an active media policy (…) writing op-eds in
  newspapers"*, Beleidsplan 2026 §2.3) én telt de opbrengst: *"the media (…) a total of 108 times, that is
  nine times per month"* (AR 2024, p. 22).
- **Relatie 2228** Van Wijngaarden → DUFAS, **mech 94 `draaideur_politiek_lobby`** — VVD-Kamerlid wordt
  lobbydirecteur (01-11-2023) en ondertekent 15 maanden later mede het vijf-lobby-opiniestuk in het FD.
- Entiteiten **1221** Eumedion, **1222** Rients Abma, **1223** DUFAS, **1224** Jeroen van Wijngaarden

*Nuance t.o.v. het deelonderzoek:* de AFM-commissieposities zijn in het jaarverslag toegeschreven aan
**Eumedion als organisatie** (p. 18), niet aan Abma persoonlijk. Zo gemodelleerd — verdedigbaarder. Abma's
eigen stapeling (voorzitter NBA Stakeholders Forum, AFM-panels, DASB/RJ, redactie *Ondernemingsrecht*)
staat als apart entiteits-argument (p. 55).

### Blok 3 — Ed Nijpels afgemaakt
Entiteit 1199 en relatie 2181 stonden `voorgesteld` **zonder één argument** — dus onkeurbaar. De
ontbrekende helft was juist de interessante: hij zat vanaf **1 januari 2014** de RvT van AVROTROS voor
terwijl hij vanaf **oktober 2013** de borgingscommissie van het SER-energieakkoord en van **februari 2018
tot 1 november 2022** het Klimaatberaad voorzat. Toezicht op een landelijke publieke omroep en het
voorzitterschap van de nationale klimaatgovernance, jarenlang parallel.

- Entiteit **1225** Klimaatberaad; relaties **2230/2231/2232** (AVROTROS / SER / Klimaatberaad), alle
  **mech 95 `draaideur_politiek_institutie`** (dat mechanisme noemt expliciet "de bestuurlijke laag van
  het omroepbestel: raden van toezicht")

### Blok 4 — advertentie-filter
- **Mech 5 `supportive_selling_environment`** kreeg een NL-instantiatie uit de mond van de uitgever zelf:
  FD Mediagroep verkoopt sponsoring van BNR Duurzaam als *"een kans om thought leadership te claimen in
  een relevant, betrouwbaar en hoogwaardig journalistiek kader"*, met een maandelijkse FD-advertentie in
  het pakket — plus een eigen effectclaim (spontane sponsorherkenning 40%).
- **Mech 4 `commerciele_afhankelijkheid`**: DPG *"maakt geen eigen keuze in adverteerders (…) want dat zou
  een politieke stellingname zijn"* — een uitgever die redactionele selectie principieel weigert.
- **Contradicting op rel. 29** (Shell→DPG, `advertentiedruk`): in dit best gedocumenteerde NL-geval komt de
  druk juist van lézers en Duurzame 100-laureaten, niet van de adverteerder. Stance volgt het effect op de
  doelclaim, niet de sympathie.
- DPG/de Volkskrant zélf berispt door het College van Beroep RCC (2021/00061-CVB) voor een "CO2-neutrale"
  reis — de uitgever in de adverteerdersstoel.

### Blok 5 — betwiste zaken, neutraal met verplichte tegen-context
**Clintel → KRO-NCRV** (rel. **2233**, mech 10 `juridische_dreiging`). Bewust omgedraaid t.o.v. het
deelonderzoek: de gedocumenteerde, door de rechter vastgestelde richting is Clintel als **eiser** tegen een
publieke omroep — niet Pointer als flak-bron. De rechter achtte de labels "lobbyclub" en "klimaatontkenner"
juist **rechtmatig**; die als flak modelleren zou tendentieus zijn. In dezelfde inzending, conform de
twee-niveau-regel: alle vorderingen afgewezen + Clintel in de kosten (€1.692) **én** dat Clintel op één
punt gelijk kreeg (de olie-financieringsclaim vond onvoldoende steun; de uitlating was onrechtmatig) — dus
geen lichtvaardige gang naar de rechter. Het model velt geen oordeel over de klimaatstandpunten zelf.

**Stichting Agrifacts** (entiteit **1226**) bewust **bescheiden**: alleen een mechanisme-loze kandidaat.
Klagen bij de Raad voor de Journalistiek is een legitiem instrument, en de Raad verklaarde STAF
niet-ontvankelijk (*"De Raad behandelt de klacht niet inhoudelijk"*). Zonder volume- en uitkomstbewijs is
"STAF procedeert" geen flak-bewijs.

## 4. Bewust niet ingediend (negatieve resultaten — hier, niet als `contextual` modelbijdrage)

- **NRC XTR / Shell branded content** (AR-x1/AR-x2). Niet ingediend: AR-x1 is advocacy-gesourcet, AR-x2
  (FTM-woordtelling) is paywalled, en de tellingen spreken elkaar tegen (24 vs. 25 artikelen). De
  NRC XTR-verkooppagina zelf is niet opgehaald. **Openstaand.**
- **Den Haag fossiel reclameverbod** (ECLI:NL:RBDHA:2025:6874, ANVR/TUI verloren; *"Tegenover de algemene
  gezondheidsbelangen van de burgers staat immers slechts het commerciële belang van de adverteerders"*).
  Wél geverifieerd, tóch niet ingediend: het gaat over **buitenreclame in de openbare ruimte**, niet over
  advertentie-afhankelijkheid van nieuwsmedia. Ander object; forceren zou het filter oprekken.
- **Jeff Harvey** (VU/NIOO, haatmail + advocatenbrieven na kritiek op klimaatontkenners): alleen een
  secundaire bron (Advalvas), en het raakt wetenschapscommunicatie eerder dan NL-opinievorming.
- **ESG-financelaag** (Sustainalytics-oorsprong via PGGM/Triodos/MeesPierson, CSRD-assurance,
  VBDO-financiën, ESG-ratings): feitelijk interessant, maar géén invloedslijn naar opinievorming.
  Laagste prioriteit per de model-focusregel. Bijvangst: **ESG-ratingbureaus leveren geen woordvoerders
  aan NL-media** — de woordvoerders komen uit de lobbylaag (Eumedion/VBDO/DUFAS/VEB).
- **Trouw Duurzame 100 als gesponsorde lijst**: gezocht, **niets gevonden**. Sterker: Trouws eigen
  criterium sluit *"grootschalige, top-down projecten of puur beleidsgerichte platforms"* juist uit.
  Niet beweren.
- **Adverteerdersdruk rond de Shell/ING-klimaatzaken**: gezocht, niets gevonden.
- **Per-adverteerder bestedingscijfers** in NL-media: niet publiek (Nielsen geeft alleen totalen).
- **WUR-onderzoeker monddood over stikstof**: geen enkel geval gevonden; het bewijs reikt tot structurele
  afhankelijkheid + één geweigerd Wob-verzoek. Niet opwaarderen tot causale claim.
- **Hajer, Fraser, Mirowski**: reële werken, correct geattribueerd, maar in deze ronde kwam **geen enkele
  geverifieerde quote** los. Niet verbatim citeren tot iemand de teksten opent.
- **PFZW/PGGM-holdings**: transparantielijsten zitten achter JavaScript; niet geverifieerd. De
  eigendomsconclusie geldt dus hard voor ABP, aannemelijk voor de sector.

## 5. Actiepunten voor de eigenaar / reviewronde

1. **Rel. 2181 (Nijpels→TROS) hangt aan mechanisme 96** (`draaideur_politiek_media`, politicus→hoofdredacteur).
   Dat past niet op een RvT-voorzitterschap; **mech 95** dekt expliciet de omroep-RvT's. Mijn PATCH gaf
   403 (vereist globale maintainer). Graag corrigeren bij de review.
2. **Twee kandidaat-relaties zonder theorie-huis**, bewust zo gelaten:
   - **2224** FTM → Min. LNV: geen tegenmacht-mechanisme dekt "journalistiek dwingt een gezagsinstituut
     tot openbaarheid" (mech 74 richt zich op *mediaorganisatie*). Rolpaar onderzoeksjournalist →
     gezagsinstituut. **Serieuze RfC-kandidaat.**
   - **2225** LTO → Min. LNV en **2234** STAF → Trouw: incuberen.
3. **Mechanisme 25 `systemisch_eigenaarschap`** noemt "grote pensioenfondsen" in zijn omschrijving, maar
   geen van de 33 instantiaties ís een pensioenfonds — het zijn allemaal BlackRock/Vanguard. Kandidaat
   voor een `herformuleren`-RfC. Zie het nieuwe onderzoeksdocument.

## 6. Onderzoeksdocumenten (géén modelinhoud)

- `onderzoek/1_in-voordeel-van-welke-eliten/00e_gemeten-bias-bevindingen.md`: **B5 herschreven** (nu
  "doel-consensus mét instrumenten-strijd", met de steekproefbeperking april–mei 2019 en de eigen
  kwalificatie van de auteurs); **nieuwe rij B5′** (Dirikx & Gelders: gemeten *null*-verschil tussen
  ideologisch uiteenlopende NL-titels — de beste empirische haak voor het Ideologie-filter op dit
  dossier); **G20 opgewaardeerd 🟡→✅** met de Semantic Scholar Graph API-route genoteerd; **G26/G27**
  toegevoegd; **Tier D-entry voor ESG**, met de observatie dat dit het **derde** geval is waarin het
  propagandamodel voor NL uitsluiting overvoorspelt (na populisme en Big Tech).
- `onderzoek/3_mechanismes-van-beinvloeding/eigendom-naar-bias/04_pensioenkapitaal-geen-media-eigendom.md`:
  **nieuw** — geverifieerd negatief resultaat tegen ABP's eigen 47-pagina-beleggingsoverzicht (nul
  treffers op RTL/Bertelsmann/DPG/Mediahuis/Talpa; enige NL-exposure een VodafoneZiggo-obligatie van €14
  mln). DPG/Mediahuis/Talpa zijn familie-/privébezit — er ís geen beursvehikel om te kopen.

## 7. Poorten

- Golden snapshot `scripts/test_scoring.py`: **groen** (23 tests) — zoals verwacht: `voorgesteld` werk
  telt in niets.
- `scripts/validate_model.py --strict`: **geen fouten boven de baseline**.
- Niets gemerged, niets goedgekeurd, niets verwijderd. Ik stel voor, de eigenaar beslist.
