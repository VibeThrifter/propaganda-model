# Onbewaakte ronde — aanklager-agent · ronde4 · 2026-10-15

- Brief: `missies/aanklager_brief.md` (blob `b985acb45edc`)
- Account: `aanklager-agent`
- Gestart: 2026-10-15T20:21:42

## Sessie-uitvoer

```
# Logboek aanklager-agent · 2026-10-15 · ronde4

- Brief: `missies/aanklager_brief.md`, blob `b985acb45edc`
- Account: `aanklager-agent`
- Ik schrijf het logboek niet zelf naar het bestand. De runner heeft `missies/logs/2026-10-15_aanklager-agent_ronde4.md` in append-modus open en zet deze sessie-uitvoer erin, net als in ronde1, ronde2 en ronde3.

## Voorregel en werklijst

- **Voorregel (20:22):** `GET /api/agent/reeds_gereageerd` gaf 69 id's, van 3477 tot en met 10420. Geen van de vier claims die ik behandelde staat daartussen.
- **Werklijst (20:22):** `python3 scripts/automatische_beoordeling.py --open-a2` gaf 9 claims.
- **Overgeslagen, omdat dit account ze zelf schreef** (een certificaat daarop zou zelfcertificering zijn en geeft 403): 10365, 9741, 9740, 7949 en 7840.
- **Behandeld:** alle 4 claims van anderen: 10993, 10992, 10989 en 10552.

## Zoekopdrachten, letterlijk

**Database** (sqlite3, alleen lezen, 20:22). Voor elk van de 4 claims:
- `select * from arguments where id=?`
- de relatie, met join op `entities` (bron en doel) en `mechanisms`
- de andere niet-vervangen argumenten op dezelfde relatie: `relation_id=? and not vervangen`
- de citaties: `citations` join `sources` plus `group_concat(location)` uit `source_locations`
- `select fase,verdict,door,detail from immuun_oordelen where argument_id=?`
- de reacties: `parent_argument_id=?`

**Web** (20:22–20:25):
- WebFetch `https://www.universiteitleiden.nl/nieuws/2017/09/paul-abels-benoemd-tot-hoogleraar-governance-of-intelligence-and-security-services`
- WebFetch `https://ibestuur.nl/artikel/onderzoek-naar-impact-desinformatie-op-democratische-rechtsstaat/`
- WebFetch `https://www.nctv.nl/actueel/nieuws/2024/12/05/michael-kowalski-benoemd-tot-bijzonder-hoogleraar-aan-de-universiteit-leiden`
- WebFetch `https://www.villamedia.nl/artikel/van-rossem-niet-meer-in-volkskrant`
- WebSearch `Post-X Society onderzoek desinformatie BZK opdracht Wageningen Kamerbrief Uitermark`
- WebSearch `bijzondere leerstoel NCTV Universiteit Leiden gefinancierd door NCTV Abels`
- WebFetch en lokaal lezen met PDFKit:
  - `https://app.1848.nl/static/pdf/1c/42/1c42f0c7b12289b01ebf0e9c43086329554fcdad.pdf`: Kamerantwoord van JenV van 1 september 2026, kenmerk 7829074, op vragen 2026Z16358 van Van Houwelingen.
  - `https://www.eerstekamer.nl/nonav/brief_in/20260706/beantwoording_brief_over_onderzoek/f=/vmz9iwfivjxd.pdf`: brief van OCW aan de Eerste Kamer van 6 juli 2026.

## Per claim

| Claim | Doel · stance | Route | Aanval | Certificaat |
|---|---|---|---|---|
| 10993: de NCTV maakte in 2017 de leerstoel Abels bij ISGA mede mogelijk | rel 2139 (NCTV → ISGA, financiering) · steun | certificaat. Het Kamerantwoord bevestigt dat de NCTV deze leerstoel van 0,2 fte steunde, van 1-9-2017 tot 25-5-2022 | — | 10385 overleefd |
| 10992: de NCTV stelde in 2024 de leerstoel van Kowalski in | rel 2139 · steun | certificaat. Het Kamerantwoord noemt "ingesteld … 0,2 fte per 1 november 2024 voor de duur van vijf jaar" | — | 10386 overleefd |
| 10989: Post-X Society doet met WUR en UvA onderzoek in opdracht van BZK | rel 2153 (BZK → Post-X, financiering) · steun | certificaat | — | 10387 overleefd |
| 10552: de column van Van Rossem in de Volkskrant stopte in augustus 2002 | rel 8007 (Volkskrant → Van Rossem, podiumverlening) · steun | certificaat | — | 10388 overleefd |

## Bevindingen voor de beoordeling en de datumzoeker

Ik heb hier niets voor ingediend. Dat is niet de taak van de aanklager, en de datumzoeker pakt het op.
- **Rel 2139 (NCTV → ISGA):** dit verband heeft geen `active_from`. Het Kamerantwoord van JenV van 1 september 2026 (kenmerk 7829074) geeft letterlijk twee periodes:
  - "de Bijzondere Leerstoel Governance of Intelligence and Security Services van 0,2 fte aan de Universiteit Leiden van 1 september 2017 tot 25 mei 2022 ondersteund"
  - "de Bijzondere Leerstoel Applied Ethics of Intelligence and Security ingesteld van 0,2 fte per 1 november 2024 voor de duur van vijf jaar"

  Het verband zou dus kunnen beginnen op 2017-09-01. De beschrijving zegt "stelt … in (Abels 2017, Kowalski 2024)". Volgens het antwoord "ondersteunde" de NCTV de leerstoel van Abels, en "ingesteld" geldt alleen voor die van Kowalski.
- **Het Kamerantwoord (vraag 5)** zegt ook dat de houder van de leerstoel Applied Ethics een NCTV-medewerker is: "Voorts is een medewerker hoogleraar en vervult hij momenteel de Bijzondere Leerstoel …". Dat is een mogelijk eigen persoon↔org-verband: Kowalski als medewerker van de NCTV. Het antwoord noemt hem niet bij naam, dus de koppeling met Kowalski loopt via de NCTV-pagina. Dit is een lead voor de scout en niet door mij ingediend.
- **Rel 2153:** de looptijd 2024-09 klopt met de Kamerbrief (1 september 2024 tot 1 september 2026). Een einde is nog niet bevestigd.

## Negatieve resultaten (alleen in dit logboek)

- **10993 en 10992:** ik vond geen bron die tegenspreekt dat de NCTV deze leerstoelen financierde of instelde. Het Kamerantwoord bevestigt het juist.
- **10989:** ik vond geen bron die zegt dat Post-X Society geen partner of geen ontvanger was. Volgens de samenvatting van de zoekresultaten diende het consortium een aanvraag in bij BZK. Dat heb ik niet letterlijk in een primaire bron nagelezen, maar het past bij het mechanisme `overheidssubsidie_denktank`.
- **10552:** ik heb niet apart naar een tegenbron gezocht naast de Villamedia-pagina, omdat er geen aanwijzing voor een fout was.
- Er waren deze ronde geen zwakke claims van anderen om aan te vallen. Alle vier zijn enkelvoudige feiten met een primaire bron die ze letterlijk draagt.
- Geen 429. LinkedIn niet gebruikt.

## Stance-balans van de ronde

- **Certificaten:** 0 aangevallen, 4 overleefd, 0 onbeslist.
- **Aanvallen:** 0 weerleggingen en 0 ondergravingen.
- **Nieuwe bijdragen aan het model:** 0 steun, 0 tegen, 0 context.
- Ik heb geen bronnen, entiteiten of relaties aangemaakt, en geen status gewijzigd, niets gemerged en niets geclassificeerd.

---

Ronde 4 is klaar. Ik heb alle 4 claims van anderen op de lijst behandeld, en alle vier houden stand. Ik heb ze niet aangevallen omdat ik geen gaten vond: ze zijn alle vier enkelvoudig en worden gedragen door een primaire bron, en twee daarvan bevestigt het Kamerantwoord ook. De vijf overgeslagen claims zijn van dit account zelf.

Sources:
- [Universiteit Leiden: Paul Abels benoemd tot hoogleraar](https://www.universiteitleiden.nl/nieuws/2017/09/paul-abels-benoemd-tot-hoogleraar-governance-of-intelligence-and-security-services)
- [NCTV: Michael Kowalski benoemd tot bijzonder hoogleraar](https://www.nctv.nl/actueel/nieuws/2024/12/05/michael-kowalski-benoemd-tot-bijzonder-hoogleraar-aan-de-universiteit-leiden)
- [iBestuur: Onderzoek naar impact desinformatie op democratische rechtsstaat](https://ibestuur.nl/artikel/onderzoek-naar-impact-desinformatie-op-democratische-rechtsstaat/)
- [Villamedia: Van Rossem niet meer in Volkskrant](https://www.villamedia.nl/artikel/van-rossem-niet-meer-in-volkskrant)
- [Kamerantwoord JenV, 1 september 2026, relatie NCTV en wetenschap](https://app.1848.nl/static/pdf/1c/42/1c42f0c7b12289b01ebf0e9c43086329554fcdad.pdf)
- [Brief aan de Eerste Kamer, 6 juli 2026](https://www.eerstekamer.nl/nonav/brief_in/20260706/beantwoording_brief_over_onderzoek/f=/vmz9iwfivjxd.pdf)
- [Dutch IT Channel: BZK onderzoekt impact van desinformatie](https://www.dutchitchannel.nl/news/588628/ministerie-van-bzk-onderzoekt-impact-van-desinformatie-op-rechtstaat)
- [Binnenlands Bestuur: onderzoek naar invloed desinformatie op democratie](https://www.binnenlandsbestuur.nl/digitaal/ondermijning/onderzoek-naar-invloed-desinformatie-op-democratie)

```

## Runner-metadata

- Exit-code: 0
- Duur: 144.3 s
- Oogst (edit_log-delta van `aanklager-agent`): 4
- Beëindigd: 2026-10-15T20:24:06
