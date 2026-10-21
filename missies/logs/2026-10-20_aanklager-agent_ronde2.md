# aanklager-agent — 2026-10-20 — ronde 2

- **Brief:** `missies/aanklager_brief.md`, blob-hash `b985acb45edc` (volledig `b985acb45edc9d0af679d9f1a084a709d59cf207`)
- **Account:** `aanklager-agent` (Bearer-token; geen secrets in dit log)
- **Omgeving:** de shell faalde deze ronde herhaaldelijk met `fork failed: resource temporarily unavailable` (proceslimiet van de machine). Daardoor liep de ronde traag; webonderzoek liep via WebSearch/WebFetch.

## Voorregel

- `GET /api/agent/reeds_gereageerd` → 79 argument-id's (hoogste 11217). Geen van de hieronder behandelde argumenten staat erin.

## Wachtrij

- `python3 scripts/automatische_beoordeling.py --open-a2` → lange lijst (11734 … 7840; nieuwste eerst). De laatste vier (10365, 9741, 9740, 7949, 7840) zijn eigen werk van `aanklager-agent` → overgeslagen (geen zelfcertificering).
- Keuze (hooguit 12): de elf oudste wachtende argumenten van anderen (11180–11233, ingediend 2026-10-16) plus 11728 (VNO-NCW, 2026-10-20) omdat die bij lezing al een specificiteitsprobleem toonde. 11234 en de rest blijven voor een volgende ronde.

## Databasezoekopdrachten (alleen lezen)

- `--open-a2` (zie boven)
- per argument: `select … from arguments where id=?`, het verband (`relations` ⨝ `entities` ⨝ `mechanisms`), het aantal levende argumenten op het verband, en de citaties met bron en vindplaatsen — voor 11728 11180 11182 11184 11212 11213 11215 11216 11219 11225 11231 11233 11234 11692 11674 11338 11318.

## Webzoekopdrachten (letterlijk)

1. WebSearch `Follow the Money 2018 dividendbelasting onderzoek opdrachtgever VNO-NCW Shell Unilever`
2. WebFetch `https://www.taxence.nl/nieuws/kamer-wil-opheldering-over-onderzoek-afschaffen-dividendbelasting/` — "opdrachtgevers van het onderzoek, datum, wat de Kamer vroeg"
3. WebSearch `Villamedia 2014 CIDI persreis Joustra Elsevier 2009` (verkennend, 11318/11338; niet in deze ronde behandeld)
4. WebSearch `Clingendael jaarverslag 2023 inkomsten "Defence Capacity Building" NATO fund`
5. WebSearch `antwoord Kamervragen Van der Staaij Segers CIDI brief Durban IV Kaag juli 2021` (verkennend, 11692; niet behandeld)
6. WebSearch `NRC augustus 2014 CIDI reis journalisten Israël buitenlandchef Elsevier` (verkennend; niet behandeld)
7. WebFetch `https://nos.nl/artikel/2385144-donatie-van-1-2-miljoen-aan-cda-door-ondernemer-van-der-wind-roept-vragen-op` — rol Van der Wind
8. WebFetch `https://www.nibud.nl/over-het-nibud/financiering/` — financiering door het Rijk, SZW, onafhankelijk
9. WebFetch `https://web.archive.org/web/20211218203857/https://www.mikebloomberg.com/news/…build-back-better/` — mislukt (web.archive.org niet bereikbaar voor de fetcher)
10. WebFetch `https://www.clingendael.org/sites/default/files/2024-09/Clingendael_Income_Table_2023.pdf` — pdf binair, tekst niet uit te lezen (lokale extractie mislukte door de shellstoring)
11. WebFetch `https://www.bloomberg.org/press/bloomberg-philanthropies-to-help-six-global-cities-harness-digital-innovation-to-build-back-better/` — 403
12. WebFetch `https://www.opensocietyfoundations.org/grants/past?filter_keyword=Netherlands&filter_year=2022` — NHC
13. WebFetch `https://www.opensocietyfoundations.org/grants/past?filter_keyword=Netherlands&filter_year=2019` — Justice and Peace
14. WebFetch `https://www.opensocietyfoundations.org/grants/past?filter_keyword=Netherlands&filter_year=2016` — COC
15. WebSearch `Bloomberg Philanthropies June 2021 six cities innovation teams Amsterdam "Build Back Better" digital innovation`
16. WebFetch `https://www.fondsenwerving.nl/nieuws/bericht/2014/11/12/Minister-president-Rutte-ontvangt-Bill-Gates` — volledige tekst
17. WebSearch `Bill Gates Rutte Torentje 13 november 2014 ontwikkelingshulp gesprek`
18. WebSearch `Adessium Foundation opgericht 2005 Gerard van Vliet`

19. WebFetch `https://www.quotenet.nl/zakelijk/a169165/hoe-de-familie-van-puijenbroek-probeert-haar-belang-in-tmg-te-redden-169165/` — zinnen over Boekhoorn
20. WebFetch `https://nos.nl/artikel/2235474-kamer-wil-opheldering-over-door-shell-betaald-onderzoek-dividendbelasting` — zinnen over VNO-NCW, contact met de Kamer
21. WebSearch `NATO Advanced Research Workshop 2015 "post-Arab Spring" counter-terrorism co-director grant ICCT Clingendael`
22. WebFetch `https://icct.nl/project/nato-advanced-research-workshops-countering-terrorism` — wie organiseerde, namens wie
23. WebFetch `https://icct.nl/publication/report-nato-workshop-counter-terrorism-mena-region` — ontvanger van de NAVO-steun?
24. WebFetch `https://www.adessium.org/en/about-us/` — oprichting
25. WebSearch `Clingendael Academy NATO Defence Capacity Building trust fund training 2023`
26. WebSearch `Open Society Foundations grant Netherlands Helsinki Committee 2022 general support`
27. WebFetch `https://www.nato.int/cps/en/natohq/topics_132756.htm` — DCB Trust Fund

## UITKOMST: niets ingediend (technische storing)

Vanaf het indienmoment kon de shell geen enkel proces meer starten (`fork failed: resource temporarily unavailable`, daarna stille exit 1 bij zelfs `true`). Ruim twintig pogingen, ook op de achtergrond, liepen allemaal stuk vóór de eerste regel van het indienscript. Daardoor is **geen enkel argument en geen enkel certificaat gepost**: geen ondergraving, geen `tegenspraak`-oordeel, geen 429 en geen 409. De twaalf argumenten staan dus nog onveranderd op `--open-a2`. Bij een herstart van de shell lus ik niet door; de volgende ronde pakt ze op.

Het indienscript met de exacte teksten staat klaar in `/tmp/aanklager_r2/indienen.py` (buiten git, kan verdwijnen). De voorgenomen oordelen staan hieronder, zodat de volgende ronde ze opnieuw kan toetsen. Het zijn **geen** modelbijdragen.

## Per claim (voorgenomen route, niet ingediend)

| arg | verband | stance | voorgenomen route | kern |
|---|---|---|---|---|
| 11728 | #416 VNO-NCW → Tweede Kamer (lobbyt, `lobbyist_naar_politicus`) | supporting | **ondergraving** (`non_sequitur`) | Het NOS-bericht van 7-6-2018 noemt VNO-NCW als opdrachtgever van het onderzoek achter een *kabinets*besluit. De Kamer komt er alleen in voor als partij die het kabinet om opheldering vraagt. Het bericht beschrijft geen contact van VNO-NCW met de Kamer; WebFetch bevestigt dat. Daarnaast bundelt de bewering twee feiten. |
| 11225 | #8444 Boekhoorn → TMG (investering vanaf 2008-05) | supporting | **ondergraving** (`non_sequitur`) | Het citaat gaat over een verkoop in 2015 die anonieme marktpartijen hem toeschrijven, in de voorwaardelijke wijs. Dat draagt de investering uit 2008 niet. Let op: hetzelfde Quote-artikel noemt de investering wél ('Boekhoorn meerde in mei 2008 … aan'), maar die zin is niet geciteerd en niet beweerd. De zin over Van Puijenbroek gaat over een ander verband. |
| 11233 | #8484 NAVO → Clingendael (financiering) | supporting | **ondergraving** (`citaat_dekking`) | De bron zegt dat de NAVO de workshop steunde die drie organisaties samen organiseerden, niet aan wie het geld ging. De ICCT-projectpagina zegt 'ICCT organised two Advanced Research Workshops on behalf of the NATO Science for Peace and Security Programme'. De indiener schrijft zelf dat de ontvanger onbekend is. |
| 11180 | #8474 OSF → Netherlands Helsinki Committee | supporting | overleefd | OSF-database 2022: $432,000, 'to provide general support', 4 months. Opnieuw opgehaald, klopt. |
| 11182 | #8475 OSF → Justice and Peace NL | supporting | overleefd | OSF-database 2019: $25,000, educational activities, 1 year. Klopt. |
| 11184 | #8476 OSF → COC Nederland | supporting | overleefd | OSF-database 2016: $49,960, 'Support for WPATH 2016 Symposium'. Klopt; de claim noemt het geoormerkte doel zelf. |
| 11212 | #8417 Bill Gates → Rutte (lobbyt) | supporting | overleefd | De bewering blijft bij de RVD-aankondiging. Bezoek en onderwerp (ontwikkelingssamenwerking) bevestigd door de bron en door websearch. |
| 11213 | #8450 Van der Wind → CDA (donor) | supporting | overleefd | NOS 15-6-2021: 1,2 miljoen euro, en 'ook voorzitter van de commissie fondsenwerving'. Volledig gedekt. |
| 11215 | #8445 Gerard van Vliet → Adessium (donor) | supporting | overleefd | Alliance: 'established in 2005 by … Gerard van Vliet'. adessium.org: 'founded in 2005 by the Van Vliet family'. Geen tegenspraak. |
| 11216 | #8470 Bloomberg Philanthropies → Gemeente Amsterdam (kandidaat, geen mechanisme) | supporting | overleefd | Persbericht 29-6-2021: zes steden waaronder Amsterdam, driejarige grants (bevestigd via doorplaatsingen; bloomberg.org gaf 403, web.archive.org was niet bereikbaar). |
| 11219 | #1570 SZW → Nibud (financiering) | supporting | overleefd | nibud.nl: 'Ongeveer een derde … door het Rijk', 'onder andere van het Ministerie van Sociale Zaken en Werkgelegenheid', 'onafhankelijke stichting zonder winstoogmerk'. Gedekt. |
| 11231 | #8483 NAVO → Clingendael (financiering) | supporting | overleefd | Primaire bron: de inkomstentabel van Clingendael. Ik kon de pdf zelf niet uitlezen; A1 vond het citaat terug. De DCB Trust Fund is een NAVO-fonds (nato.int), gevoed door bondgenoten en partners. Geen tegenbron. |

Verkend maar niet behandeld (volgende ronde): 11692 (contextueel, Kaag/Durban IV; citaat klopt), 11674 (contradicting influence-argument, citaat klopt), 11318/11338. Bij die laatste twee is er spanning: Villamedia noemt Joustra als deelnemer in 2009, NRC 'de buitenlandchef'. Het zijn al tegengestelde argumenten op #8507, en een derde bron vond ik niet.

## Negatieve resultaten (alleen hier, nooit als modelbijdrage)

- 11180/11182/11184: geen bron gevonden die de OSF-bedragen of -ontvangers tegenspreekt (WebSearch 26 vond de grant niet buiten de OSF-database, wat een dekkingsgat is en geen tegenbewijs).
- 11212, 11213, 11215, 11216, 11219, 11231: geen tegenbron gevonden.
- 11231: geen bron gevonden die zegt welke Clingendael-activiteit in 2023 uit de DCB Trust Fund betaald werd (zoekopdrachten 4, 25).
- 11233: geen bron gevonden die Clingendael als ontvanger van SPS-geld noemt (zoekopdrachten 21–23).

## Stance-balans van de ronde

- **Ingediend:** 0 steun / 0 tegen / 0 context; 0 certificaten (technische storing, zie boven).
- **Voorgenomen:** 0 weerleggingen / 3 ondergravingen (11728, 11225, 11233) / 9 `overleefd` / 0 `onbeslist`.

## Exit

Geen 429, geen LinkedIn gebruikt. De ronde stopt op de proceslimiet van de machine. De eigenaar kan nagaan wat de proceslimiet opvreet: zelfs `true` kon niet starten. Mogelijk lopen er te veel gelijktijdige `claude`- of agent-processen.

_Noot: dit bestand is met de Write-tool opnieuw geschreven. De kop die de runner bij de start schreef ('Onbewaakte ronde — aanklager-agent · ronde2 · 2026-10-20', brief, account, starttijd) kan daarbij verloren zijn gegaan. De runner-footer volgt hieronder, als die nog in dit bestand terechtkomt._
