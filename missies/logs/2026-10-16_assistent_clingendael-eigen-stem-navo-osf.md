# Missielog: Clingendael, eigen stem op de banden, NAVO → Clingendael (rel. 285), OSF en FOSI

- **Datum:** 2026-10-16, ca. 13:30–14:15 CEST. De indieningen staan in `edit_log` tussen 12:10 en 12:12 UTC.
- **Account:** `assistent` (bijdrager).
  - Alles is ingediend via de REST-API op `localhost:5000` en landt `voorgesteld`.
  - Ik heb niets gemerged, geen status gewijzigd en niets verwijderd. De DB is alleen read-only gelezen.
  - Er draaide tegelijk een andere sessie onder hetzelfde account: bronnen #3226–#3234, argumenten #11226–#11229 en #11245–#11252, RfC's #111–#115. Die raakt dezelfde argumenten niet.
- **Opdracht** (van de eigenaar, via de hoofdsessie; geen briefbestand):
  - **A.** Eigen stem op de levende argumenten van de goedgekeurde Clingendael-banden.
  - **B.** Rel. 285 NAVO → Clingendael.
  - **C.** Open Society Foundations (#161) en Foundation Open Society Institute (#838).
- **Regels:** CLAUDE.md (git `436d980`, lokaal gewijzigd), § "Eigen stem, strikt", § Looptijd, § Richting en de granulariteitslitmus. `missies/README.md` (git `efc2ad8`, lokaal gewijzigd).

## A. Eigen stem op de Clingendael-banden

**Werkwijze.**
- **Gelezen:** alle 55 gemergede, levende root-argumenten op de 44 goedgekeurde verbanden met Clingendael (#43) als bron of doel, plus de ene levende reactie (#10369).
- **Per kandidaat gecontroleerd:**
  - een bestaande revisie (`reviseert_id`): bij geen van de kandidaten;
  - een stemtoets-oordeel (`stem_toetsen`): bij geen van de kandidaten. Alleen #2168 en #10319 hebben `neutraal`.
- **Indiening:** per gemerged argument met een oordeel of etiket in eigen stem precies één revisie via `POST /api/arguments/<id>/revisie`.

| Oud | Verband | Wat in eigen stem stond | Revisie |
|---|---|---|---|
| #2291 | 1537 MinBuZa Saudi-Arabië → Clingendael | "— buitenlandse-staatsfinanciering van een 'onafhankelijk' duidingsinstituut" | **#11235** |
| #2292 | 1538 Royal Dutch Shell → Clingendael | "(structureel financier)" en "— grote industriële/financiële bedrijven financieren zo het buitenlandpolitieke duidingsinstituut" | **#11236** |
| #2293 | 1539 ASML → Clingendael | idem | **#11237** |
| #2294 | 1540 Tata Steel Nederland → Clingendael | idem | **#11238** |
| #2295 | 1541 ING → Clingendael | idem | **#11239** |
| #3466 | 285 NAVO → Clingendael | "onderstreept dat Clingendael niet slechts een externe duider is maar institutioneel verweven met de NAVO" | **#11240** |
| #3472 | 285 NAVO → Clingendael | "volgens de NAVO zelf uitdrukkelijk"; "Als publieksdiplomatie-instrument … NAVO-draagvlakapparaat, niet louter in de rol van onafhankelijke duider" | **#11241** |
| #2534 | 1753 De Hoop Scheffer – Clingendael | "de dominante NL-veiligheidsdenktank"; "(belangenverstrengeling in de expert-legitimatie)" | **#11242** |
| #3471 | 2042 MSC – Clingendael | "het trans-Atlantische veiligheids-eliteforum MSC" | **#11243** |
| #2540 | 1759 Middendorp – Clingendael | "— een denktank-inbedding naast zijn media-optredens". Daarnaast een tweede feit (speciaal gezant) dat bij een ander verband hoort | **#11244** |

**Nieuwe claims:**
- **#11235:** "Het ministerie van Buitenlandse Zaken van Saudi-Arabië staat in de klantenlijst over 2024 van het Clingendael Instituut, in de staffel €10.000–€50.000."
  - Het citaat is gecorrigeerd. Het oude citaat ("Ministry of Foreign Affairs of Saud") staat niet letterlijk in de pdf.
  - De pdf zegt "Ministry of Foreign Affairs of the Kingdom of Saud" (p. 3, afgebroken in de pdf zelf).
  - De staffel komt uit dezelfde lijst.
- **#11236–#11239:** "<bedrijf> stond in december 2022 op de pagina 'Join our Corporate Members' van het Clingendael Instituut bij de 'Current members' van zijn Corporate Membership Programme."
- **#11240:** "Tijdens de NAVO-top in Den Haag (24-25 juni 2025) waren de NAVO en de Nederlandse regering gastheer van het NATO Public Forum, samen met de Atlantische Commissie, het Clingendael Instituut en The Hague Centre for Strategic Studies."
- **#11241:** "Volgens de NAVO was het NATO Public Forum, dat de NAVO in juni 2025 in Den Haag samen met onder meer het Clingendael Instituut organiseerde, bedoeld om het publieke begrip van het beleid en de doelen van de NAVO en van de topbesluiten te vergroten, via dialoog met een brede groep belanghebbenden."
- **#11242:** "Oud-NAVO-secretaris-generaal Jaap de Hoop Scheffer is sinds 1 oktober 2022 voorzitter van de Raad van Toezicht van het Clingendael Instituut." Parlement.com noemt beide functies.
- **#11243:** "De Munich Security Conference (MSC) en het Clingendael Instituut tekenden in mei 2025, in de marge van de Munich Leaders Meeting in Washington DC, een Memorandum of Understanding om tijdens de NAVO-top in Den Haag (24-25 juni 2025) samen de dialooghub 'NATO in the Huis' in Sociëteit De Witte te organiseren." Het MSC-bericht is gedateerd 23 mei 2025.
- **#11244:** "Volgens zijn profiel bij het ICCT is Tom Middendorp Associate Fellow bij het Clingendael Instituut."

De citaties zijn bij alle revisies overgenomen, behalve bij #11235 (gecorrigeerd citaat). Alle nieuwe teksten gaven geen treffer in `validation.eigen_stem_treffers`, streng noch ruim.

### "Structureel financier" (#2292–#2295)

De bron (#1272, Wayback 2 december 2022) zegt dit niet. Wat er wel staat:
- de lijst "Current members: …";
- "Our Corporate Membership Programme is open to top-tier companies that value the Clingendael Institute's role in delivering independent, rigorous, and evidence based analysis …";
- "As part of our Corporate Network we are providing you with analyses, inspiration, advise and high-level exchanges for strategic decision-making …".

Over geld, contributie of financiering zegt de pagina niets. Daarom is "structureel financier" weggelaten.

**Wat de inkomstentabellen zeggen:**
- "Tata Steel Nederland BV" staat in de tabel over 2017 (€ 1,500) en in die over 2018.
- "Shell International" staat in de tabel over 2023 (€ 2.500 – € 5.000).
- ASML en ING staan in geen van de tabellen die ik las (2016, 2017, 2018, 2021, 2023, 2024).
- In 2017 staan Royal IHC, Royal Philips, Tata Steel en Van Oord, allemaal leden van de lijst, elk op € 1,500. Dat past bij een vaste contributie, maar geen bron zegt dat. Het staat dus niet in het model.

### Niet gereviseerd: ander soort probleem (alleen gemeld)

- **"Vaste" of "terugkerende" duider zonder bron voor de regelmaat:** #2297, #2301, #2417 en #2445. De bronchecker gaf al `twijfel` of `klopt-niet`, dus deze lopen via de bronzoeker.
- **Specificiteit.** Argumenten op Clingendael → persoon (`personeel`) die vooral over een media-optreden gaan: #2445, #2446, #2448–#2451, #2453 en #2517. Op rel. 36 (→ NOS) noemt #36 (legacy) de NOS niet.
- **Mild:**
  - #2138 noemt BZ "een van de belangrijkste financiers". BZ staat in de hoogste staffel van de tabellen, dus de omvang heeft een bron.
  - #3086 zegt "rechtstreeks".
- **#287 (legacy, betwist):** volgens de opdracht laten staan.
- **Beschrijvingen van verbanden (geen argumenten):**
  - Rel. 285: "NAVO-financiering beïnvloedt Clingendael-output".
  - Rel. 2042: "… het trans-Atlantische veiligheids-eliteforum …".
  - Stap 10b (stemtoets-veeg) kan seed- en agentbeschrijvingen herschrijven.

## B. Rel. 285 NAVO → Clingendael

Rel. 285 heeft type `beinvloeding`, mechanisme #8 `expert_framing` (denktank → mediaorganisatie), start 1983, en is goedgekeurd (seed). De beschrijving zegt "NAVO-financiering beïnvloedt Clingendael-output". Geen bestaand mechanisme past bij 285 zoals het getypeerd is. Daarom heb ik geen aspect-argument `mechanism` ingediend. Wel gedocumenteerd zijn drie andere banden.

**1. Mede-gastheer van het NATO Public Forum 2025.** Ja, volgens de NAVO-pagina 235800 (#2125): "During the summit in The Hague, NATO and the Government of the Netherlands hosted the NATO Public Forum together with the Atlantic Commission of the Netherlands, the Clingendael Institute and The Hague Centre for Strategic Studies." De kop van de pagina is "24-25 June 2025".

**2. Opdrachtgever.** Ja.

| Jaar | NAVO-vermeldingen | Staffel of bedrag | Bron |
|---|---|---|---|
| 2024 | "NATO" | € 50.000 – € 150.000 | Klantenlijst (#1271), p. 3 |
| 2023 | "NATO Defense Capacity Building fund" | € 100.000 – € 500.000 | Income Table (#831), p. 3 |
| 2023 | "NATO Communications and Information Agency" | € 10.000 – € 50.000 | Income Table (#831), p. 2 |
| 2021 | NCIA | €10,000–€50,000 | Income Table |
| 2021 | "NATO Emerging Security Challenges Division" | €100,000–€500,000 | Income Table |
| 2018 | "Shape Finance & Acquisition Directorate (Nato)" | €1,000–5,000 | Income Table |
| 2018 | "NATO HQ" | €5,000–10,000 | Income Table |
| 2018 | ESCD | €10,000–50,000 | Income Table |
| 2017 | "NATO" | € 2,250 | Income Table |
| 2017 | "Shape Finance" | € 4,320 | Income Table |
| 2016 | geen NAVO-onderdeel | — | Income Table |

In de tabel over 2016 staat alleen "Netherlands Permanent Representation NATO" (€ 2,400), en dat is de Nederlandse Staat.

Let op bij de tabel "2021" (bestand `Clingendael Income Table 2021.pdf`): p. 1 heeft de kop "Income 2021", maar p. 2–5 hebben de kop "The Clingendael Institute Income 2020". De NAVO-regels (p. 4–5) en de FOSI-regel (p. 4) kunnen dus over 2020 gaan. Ik gebruik dit bestand nergens als citaat, alleen in de redenering van #11232 en in de motivatie van RfC #116 ("inkomstentabellen over 2021"; daar is 2021 de bestandsnaam). De sessie van vandaag (`2026-10-16_assistent_clingendael-looptijd-1983.md`) kwam voor 285 ook op 2017 uit.

**3. NATO SPS.** Eén geval gevonden.
- **Het verslag van het ICCT:** "From 6 to 7 October 2015, the International Centre for Counter-Terrorism (ICCT), Al-Ahram Center for Political and Strategic Studies (ACPSS) and Netherlands Institute of International Relations 'Clingendael' convened a NATO Advanced Research Workshop in Brussels. This workshop was titled '(Counter-)terrorism in the post-Arab Spring context' and supported by the NATO Science for Peace and Security Programme."
- **Bijlage C van het Clingendael-jaarverslag 2015** noemt als organisatie "Clingendael / International Centre for Counter-Terrorism (ICCT) / Al-Ahram / NATO".
- **Wat de bronnen niet zeggen:** welke organisator de SPS-steun ontving.
- **Verder:** geen andere SPS-subsidie aan Clingendael gevonden.

**Ingediend.** Drie verbanden, alle `voorgesteld`, met mechanisme en looptijd:

| Verband | Type | Mechanisme | Looptijd | Argumenten | Precedent |
|---|---|---|---|---|---|
| **#8483** NAVO → Clingendael | `financiering` | #52 | `active_from` 2017 | **#11230**, **#11231**, **#11232** | NAVO → HCSS (#40), → ICCT (#2091), → Atlantic Council (#1729), → GMF (#1747) |
| **#8484** NAVO → Clingendael | `financiering` | #52 | 2015-10 t/m 2015-10 | **#11233** | NAVO → TU Delft (#2063, SPS-project) |
| **#8485** NAVO – Clingendael | `alliantie` (richtingloos) | #135 `elite_kennisnetwerk` | 2025-06 t/m 2025-06 | **#11234** | MSC – Clingendael (#2042), 'NATO in the Huis' op dezelfde top |

- **#8484** is een aparte, afgesloten band. Ze overlapt niet met #8483. Volgens `opschonen.py` zijn twee aparte termijnen twee feiten.

**De argumenten:**
- **#11230:** "De NAVO ('NATO') staat in de klantenlijst over 2024 van het Clingendael Instituut, in de staffel €50.000–€150.000." Bron #1271.
- **#11231:** "Het 'NATO Defense Capacity Building fund' van de NAVO staat in de inkomstentabel over 2023 van het Clingendael Instituut, in de staffel €100.000–€500.000." Bron #831.
- **#11232:** "De NAVO ('NATO') staat met € 2.250 in de inkomstentabel over 2017 van het Clingendael Instituut." Dit is een looptijd-aspect (`property=active_from`, `property_value=2017`). Bron #3235, citaten "The Clingendael Institute Income 2017" en "NATO" (p. 2). De redenering verwijst naar de tabellen van 2016, 2018 en 2021.
- **#11233:** "Het Science for Peace and Security-programma van de NAVO ondersteunde de NATO Advanced Research Workshop '(Counter-)terrorism in the post-Arab Spring context', die het ICCT, het Al-Ahram Center for Political and Strategic Studies en het Clingendael Instituut van 6 tot 7 oktober 2015 in Brussel organiseerden." Bron #3236. De redenering zegt dat de ontvanger van de steun niet genoemd wordt.
- **#11234:** "Tijdens de NAVO-top in Den Haag (24-25 juni 2025) waren de NAVO en de Nederlandse regering gastheer van het NATO Public Forum, samen met de Atlantische Commissie, het Clingendael Instituut en The Hague Centre for Strategic Studies." Bron #2125, citaten van de forumzin en "24-25 June 2025".

**Besluiten voor een maintainer:**
- **Rel. 285:** type `beinvloeding`, mechanisme #8 en start 1983 kloppen niet. Bijvoorbeeld afwijzen zodra #8483 en #8485 goedgekeurd zijn, of omtypen.
  - Afwijzen neemt de argumenten mee: #287 (legacy), #3466 en #3472, en de revisies #11240 en #11241.
  - Dezelfde feiten staan dan op #8485.
- **Rel. 64:** NAVO → Clingendael, `financiering`, #52, 1983. Op 2026-10-14 afgewezen als "zonder bron". Laten liggen: #8483 vervangt het met het gedocumenteerde begin. Wordt 64 toch heraangemeld, dan is het een dubbel van #8483 en klopt 1983 niet.

## C. Open Society Foundations (#161) en FOSI (#838)

**Juridisch.** FOSI is de Zwitserse stichting "Stiftung Open Society Institute":
- zetel Zug, CHE-109.466.351, rechtsvorm Stiftung, status existierend;
- bron: Zefix-API, firma 322688. De SHAB-publicaties 2017–2025 gaan over wisselingen in de Stiftungsrat;
- het Grants Management Manual van OSF (Wayback 2024-07-22) zegt: "OSF consists of a number of different legal entities, including … Zug, Switzerland-based Foundation Open Society Institute (FOSI, or OSI-Zug) …".

FOSI is dus een rechtspersoon binnen het OSF-netwerk. In het model is #161 dat netwerk.

**Subsidies van OSF aan Clingendael** (database `grants/past?filter_keyword=Clingendael`):

| Kenmerk | Jaar | Bedrag | Looptijd | Funder |
|---|---|---|---|---|
| OR2019-56824 | 2019 | $305,568 | 2 jaar | niet vermeld |
| OR2019-65214 | 2019 | $14,550 (top-up) | 2 jaar | niet vermeld |
| OR2022-87333 | 2023 | $30,000 | 7 maanden | niet vermeld |
| OR2023-90012 | 2023 | $280,000 | 3 jaar | "Foundation to Promote Open Society" |

**Wie verleende de subsidie van 2019?** De toelichting bij de database zegt over het veld Funder: "where not listed, the grant has been made by independent European members of the Open Society Foundations network". Welk Europees lid het was, zegt de database niet. Clingendaels eigen tabellen noemen "Foundation Open Society Institute":
- 2021: € 50,000 – € 100,000 (volgens de bestandsnaam; de paginakop zegt 2020, zie B);
- 2023: € 100.000 – € 500.000;
- 2024: € 50.000 – € 150.000.

In 2016, 2017 en 2018 staat de stichting er niet in. Dat past bij FOSI als verlener, maar het blijft een afleiding.

**Granulariteit.** FOSI heeft één verband: financiering van Clingendael (#52). Dat mechanisme werkt op het niveau van de financier (OSF), niet van de Zwitserse rechtspersoon. Eén knoop volstaat.

**Ingediend:**
- **RfC #116** (`samenvoegen`, `element_type` `entiteit`, `oud_ids` [838], doel `{"bestaand_id": 161}`):
  - herbevestigd: relaties [1536], geen argumenten, instantiaties of padclaims;
  - de payload is vooraf gevalideerd met `voorstellen.valideer_payload` (geen fouten);
  - `aanhangsels(838)` levert alleen rel. 1536 op.
- **Revisie #11253** van #2290: "De Foundation Open Society Institute (FOSI), een stichting in Zug die deel uitmaakt van de Open Society Foundations, staat in de klantenlijst over 2024 van het Clingendael Instituut, in de staffel €50.000–€150.000."
  - Citaten uit #1271 en uit #3237 (OSF-manual).
  - "(Soros)" stond niet in de geciteerde bron en is weggelaten.
  - Zo gaat het argument na de samenvoeging ook over OSF – Clingendael (bronchecker v3).

**Wat `_voer_samenvoegen_uit` doet en wat dat betekent:**
- Alleen wat in `herbevestigd` staat, verhuist.
- **Rel. 1536:** de bron gaat van 838 naar 161. Type, mechanisme, status (`goedgekeurd`, door maxime) en datums (geen) blijven. Haar argumenten (#2290, #11253) hangen aan de relatie en gaan mee.
- **#838:** `_verhuis_identiteit` vindt niets: geen externe id's, rollen, bestuurslaag of metadata. Daarna `vervangen = 1` en een lineage-regel `samenvoegen` 838 → 161 (voorstel #116).
- **1536 en 8407:** daarna zijn beide Open Society Foundations → Clingendael, `financiering`, #52. 8407 is `voorgesteld` met 2019, 1536 is `goedgekeurd` zonder datum.
- **Stap 8b na goedkeuring van 8407** (stap 10, na merge van #11050):
  - 1536 is door een mens goedgekeurd en blijft.
  - Voor 8407 is 1536 de kandidaat. Draagt een levend steunend argument met een echte bron 1536 (laatste A1 niet `klopt-niet`), dan wint 1536 op id.
  - 8407 wordt dan afgewezen als "dubbel verband", #11050 gaat naar 1536, en 1536 krijgt `active_from` 2019.
- **Kanttekening:** draagt geen argument 1536 meer (A1 `klopt-niet` op #2290 én #11253), dan laat 8b beide staan. Dan beslist een maintainer.
- **Als RfC #116 wordt afgewezen:** 1536 (FOSI, 2024) en 8407 (OSF, 2019) blijven apart. Het bewijs van 2019 staat dan op OSF, en dat klopt met de database, die het aan het netwerk toeschrijft.

Niet aangeraakt: rel. 8397–8477 van de andere sessie, ook 8407 en #11050.

## Ingediend (overzicht, alles `voorgesteld`)

- **Bronnen** (classificatie als voorstel):
  - **#3235** Clingendael Income Table 2017: url + archive_url (#5753).
  - **#3236** ICCT, "Report: NATO Workshop on Counter-Terrorism in the MENA Region": url + archive_url (#5755, Wayback-snapshot 20261016120706, vandaag aangevraagd).
  - **#3237** OSF Grants Management Manual, introductie: alleen archive_url, want de live pagina staat achter een login.
  - **Locatie #5757:** live url van de klantenlijst 2024 bij #1271. De bronchecker kreeg op de Wayback-kopie HTTP 429.
- **Verbanden:** #8483, #8484, #8485.
- **Argumenten:** #11230–#11234.
- **Revisies:** #11235–#11244 en #11253.
- **RfC:** #116.
- **Bijgeschaafd:** de redenering van mijn eigen voorstel #11232 (`PATCH`, alleen `reasoning`), zodat die de dubbelzinnige paginakop van het bestand "2021" noemt.

## Queries

Tijden bij benadering (CEST). De zoekopdrachten zelf staan er letterlijk.

**WebSearch:**
- `Clingendael "Income Table" 2022 pdf`
- `Clingendael transparency funding client list income table site:clingendael.org`
- `"Clingendael" "Income 2022" OR "Income Table 2022" OR "Income 2019" OR "Income 2020" clients NATO`
- `Clingendael annual report 2017 income table clients pdf`
- `NATO "Science for Peace and Security" Clingendael grant project`
- `"Clingendael" NATO SPS "Science for Peace and Security" project OR workshop OR "advanced research workshop"` (extended)
- `Clingendael "Income 2015" OR "annual report 2015" income table clients Clingendael Institute transparency`
- `NATO Advanced Research Workshop "post-Arab Spring" counter-terrorism 2015 Brussels Clingendael ICCT Al-Ahram SPS` (extended)
- `"Foundation Open Society Institute" Zug Switzerland foundation register`
- `Open Society Foundations financials "Foundation Open Society Institute" FOSI network entities`

**Opgehaalde documenten (curl/WebFetch):**
- **Clingendael-pdf's:**
  - Clientlist 2024: Wayback 20260517093237 en live.
  - Income Table 2023: Wayback 20251104124337 en live.
  - Income Table 2021: live.
  - Income Table 2018: live.
  - Income Table 2017: Wayback 20220307202433 en live.
  - Income Table 2016: live, clingendael.nl.
- **Jaarverslag 2015, bijlagen A–D:** Wayback 2019.
- **Corporate Members-pagina:** Wayback 20221202024139. Live geeft 403.
- **Overige pagina's:**
  - nato.int/cps/en/natohq/235800.htm;
  - securityconference.org/en/news/full/nato-in-the-huis/;
  - parlement.com (De Hoop Scheffer);
  - icct.nl: publicatie- en evenementpagina;
  - clingendael.org/event/expert-meeting-…: Wayback 2020; live geeft 403.
- **OSF:**
  - opensocietyfoundations.org/grants/past?filter_keyword=Clingendael en /grants/past/about;
  - osf.screenstepslive.com, introductie: live stuurt door naar een login, Wayback 20240722180427 werkt.
- **Zefix:** API `firm/search.json` ("Open Society Institute") en `firm/322688.json`.
- **Wayback-CDX:** voor de inkomstentabellen, de transparantiepagina (node/21) en de ICCT-pagina's. Daarnaast de save-aanvraag voor het ICCT-verslag.

**DB (read-only):**
- relaties met bron of doel 43;
- argumenten, citaties, `immuun_oordelen`, `stem_toetsen` en `looptijd_onderzoek` op die relaties;
- `edit_log` van rel. 64, 285, 1536 en 8407 en van entiteit 838;
- mechanismen rond de rollen `denktank` en `elite_forum`;
- precedenten van NAVO-financiering en van mechanisme 202;
- RfC-precedenten `samenvoegen`;
- de entiteiten 161 en 838 met hun aanhangsels;
- de broncode van `create_argument`, `revise_argument`, `create_relation`, `voorstellen.py`, `opschonen.py`, `_stemrevisie` en `_semantisch_duplicaat`.

## Negatieve resultaten (alleen hier, niet in het model)

- **NATO SPS:** behalve de workshop van 2015 geen SPS-subsidie of -project met Clingendael gevonden. De bron van 2015 noemt de ontvanger van de steun niet.
- **Inkomstentabellen 2015, 2019, 2020 en 2022:** niet gevonden. Gezocht via Wayback-CDX (prefix- en urlkey-filters), varianten van de url en web search.
- **Transparantiepagina** (clingendael.org/node/21): geeft 403 en staat niet in de CDX onder de geprobeerde url's.
- **"Structureel financier":** staat niet in de bron #1272, en ook geen bedrag of contributie.
- **ASML en ING:** staan in geen van de gelezen inkomstentabellen.
- **Kantonaal handelsregister Zug:** het uittreksel is een JavaScript-app zonder leesbare tekst. Ik gebruikte de Zefix-API.
- **OSF-database:** noemt de Europese verlener van de subsidies van 2019 niet bij naam.

## Stance-balans

- 16 steun: 5 nieuwe roots (waarvan 1 looptijd-aspect) en 11 revisies.
- 0 tegen.
- 0 context.

**Toelichting:**
- De revisies brengen geen nieuwe bewering binnen. Ze halen oordelen weg en verzwakken claims (geen "structureel financier", geen typering).
- De bevindingen die tegen een claim pleiten, staan in de redenering van de argumenten en hierboven:
  - de bron zegt geen financiering (#2292–#2295);
  - de SPS-ontvanger is onbekend;
  - 2016 heeft geen NAVO;
  - ASML en ING ontbreken in de tabellen.
- Dit zijn grenzen van het bewijs, geen tegenbewijs voor de verbanden. Daarom heb ik geen contradicting-root ingediend.
- Op eigen of andermans argumenten heb ik niet gereageerd (geen replies).

## Alleen voor een maintainer (niet uitgevoerd)

1. **Rel. 285:** besluit over type, mechanisme en start (zie B).
2. **Rel. 1538–1541:** het type `financiering` rust op een vermelding als "Current member" van een bedrijvenprogramma. De bron noemt geen geld.
   - Omtypen naar `lidmaatschap` (richtingloos) of `financiering` aanvullen met inkomstenbewijs.
   - Bewijs bestaat voor Tata Steel (2017, 2018) en Shell International (2023), niet voor ASML en ING.
3. **Beschrijvingen van rel. 285 en rel. 2042:** eigen stem, zie A. Stap 10b of een maintainer-PATCH.
4. **Als stap 8b 1536 en 8407 niet ontdubbelt** (zie de kanttekening bij C): een van de twee afwijzen.
5. **RfC #116:** beslist de uurronde (rfc-toetser en rfc-criticus), of een maintainer.
