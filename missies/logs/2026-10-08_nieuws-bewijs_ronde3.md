# Onbewaakte ronde — nieuws-bewijs · ronde3 · 2026-10-08

- Brief: `missies/nieuws_bewijs_brief.md` (blob `a18d04acb03b`)
- Account: `nieuws-bewijs`
- Gestart: 2026-10-08T13:18:51

## Sessie-uitvoer

```
# Ronde-log nieuws-bewijs · ronde3 · 2026-10-08

- **Brief:** `missies/nieuws_bewijs_brief.md`, blob `a18d04acb03b`
- **Account:** `nieuws-bewijs`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `[2134, 2322, 2339]`. Geen van deze id's hoort bij de doelen van deze ronde.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` gaf doel #82 (`relatie:1169`) en doel #83 (`relatie:1799`). De meegegeven context (artikelen over het overlijden van Jeffrey Archer) heeft niets met deze twee verbanden te maken, dus ik heb hem niet gebruikt.
- Er kwam geen 409, 429 of 400 terug. LinkedIn heb ik niet gebruikt: dit onderzoek gaat over hoe de NOS haar bronnen gebruikt, niet over iemands loopbaan.
- **Indienscript:** `data/scout/bewijs-2026-10-08-r3.py`. Het doet directe API-calls (bron #1498 en #2389 zijn hergebruikt) en controleert elk citaat vooraf letterlijk tegen de live pagina (9/9 OK). Het resultaat staat in `data/scout/bewijs-2026-10-08-r3.resultaat.json`.

## Doel #82: `relatie:1169`, CBS → NOS (`bron_afhankelijkheid`, #6) → **klaar**

**Wat het model beweert:** "Het CBS is via kwartaalpersconferenties en de hoofdeconoom een structurele officiële bron voor het economische nieuws van de NOS." Volgens #6 leunt de NOS routinematig op het CBS, en levert het CBS daarmee ook het frame.
- **Wat ervoor zou pleiten:** de NOS brengt de CBS-cijfers over meerdere jaren met de CBS-duiding en zonder tegenstem.
- **Wat ertegen zou pleiten:** de NOS bevraagt het CBS kritisch of laat andere economen aan het woord.

**Bestaande argumenten:**
- #1627 (supporting, `ongecontroleerd`, A1 `twijfel`) rust op één NOS-bericht van 2 mei 2026. Het citaat staat er letterlijk in. Maar "structureel" en "vaste duider" zijn een generalisatie uit dat ene bericht → **ondergraving #7890**.
- #3933 (bronzoeker) is `verworpen`. Daar heb ik niet op gereageerd.

**Neutrale zoekvraag:** *"Hoe brengt de NOS de CBS-cijfers over economie en inflatie, over meerdere jaren? Wie duidt ze, en komen andere stemmen of kritiek op het CBS aan bod?"*

| Bron | Argument | Stance |
|---|---|---|
| #2478 NOS 15-11-2022, #2479 NOS 15-5-2024, #2480 NOS 14-2-2025 (nieuw, cluster `nos`) | **#7891**: in drie NOS-berichten over CBS-groeicijfers licht CBS-hoofdeconoom Van Mulligen telkens de cijfers toe | steun |
| #2481 NOS 30-9-2022 "Opnieuw recordinflatie …, maar discussie over meetmethode" (nieuw) | **#7892** (`property=influence`): de NOS bracht het cijfer met de kanttekening dat er discussie was over de CBS-meetmethode | tegen |
| (#797, bestond al) | **#7890**: ondergraving op #1627 | ondergraving |

## Doel #83: `relatie:1799`, Peter Hein van Mulligen → NOS (`expert_legitimatie`, #87) → **klaar**

**Wat het model beweert:** Van Mulligen duidt bij de NOS de maandelijkse inflatiecijfers en geeft de berichtgeving zo de legitimiteit van een deskundige. Volgens #87 blijven de institutionele inbedding en de aannames van zo'n deskundige buiten beeld.

**Bestaande argumenten:**
- #3938 (`geverifieerd`, A1 `klopt`, A2 `overleefd`): het citaat en de inhoud kloppen. Het gaat om één bericht. Geen ondergraving.
- #2635 (`ongecontroleerd`, A1 `twijfel`: citaat niet gevonden). Ik heb het bericht zelf opgehaald. De citatie plakt twee zinnen aan elkaar die in het bericht gescheden zijn door de toeschrijving "zegt hoofdeconoom van het CBS Peter Hein van Mulligen". Bovendien draagt één bericht "maandelijks" niet → **ondergraving #7893**.
- #3931 is `verworpen`. Daar heb ik niet op gereageerd.

**Neutrale zoekvraag:** *"Hoe brengt de NOS Van Mulligen: als CBS-hoofdeconoom of als neutrale expert? En komen de aannames achter de CBS-cijfers in beeld?"*

| Bron | Argument | Stance |
|---|---|---|
| #2481 (nieuw), #1498 en #2389 (bestonden al) | **#7894**: Van Mulligen lichtte als CBS-hoofdeconoom bij de NOS de inflatiecijfers toe van september 2022, september 2025 en augustus 2026 | steun |
| #2481 | **#7895** (`property=influence`): in 2022 kwam de aanname achter het cijfer in beeld (de discussie over de meetmethode); Van Mulligen zei dat het gemiddelde voor een grote groep mensen niet aansloot op de werkelijke beleving | tegen |
| #2482 CBS 23-6-2020 "CBS-hoofdeconoom ontkracht mythes in nieuw boek" (nieuw, voorstel `primair`) | **#7896** (`property=mechanism`, 6): `bron_afhankelijkheid` past mogelijk beter. De NOS noemt hem telkens CBS-hoofdeconoom, en hij noemt zichzelf "gezicht van het CBS". Dat verband bestaat al als rel. 1169 | aspect |

**Voor de mens:**
- Rel. 1561 (CBS → NOS, `expert_framing`) lijkt hetzelfde verband als 1169, maar onder een mechanisme dat over door sponsors betaalde denktanks gaat.
- Rel. 1562 (Van Mulligen → CBS, `denktank_levert_expert`) heeft hetzelfde probleem. Het CBS is geen denktank.
- Niet van mijn doelen. Ik heb er niets op ingediend.

## Zoekopdrachten, letterlijk

**Database (alleen-lezen) en API:**
- de relatie-query uit de brief voor `r.id = 1169` en `r.id = 1799`
- `curl /api/arguments?relation_id=1169` en `?relation_id=1799`
- `SELECT * FROM immuun_oordelen WHERE argument_id IN (1627,3933,2635,3931,3938)`
- mechanismen met `name LIKE '%woordvoer%'/'%expert%'/'%bron%'/'%statist%'/'%officie%'/'%cijfer%'` of `description LIKE '%woordvoerder%'`, met de rollen van #6/#87/#91
- relaties met entiteit 600 of 602 als bron of doel
- `source_locations.location LIKE` de NOS-artikelnummers 2452486/2520553/2555791/2446533/2584743/2629224 en de CBS-pagina uit 2020
- `bronchecker.py bronnen_van` (gelezen: hoe meerdere citaties beoordeeld worden)

**Web (WebSearch):**
1. `CBS inflatie berekening energieprijzen kritiek economen nieuwe methode NOS`
2. `Peter Hein van Mulligen hoofdeconoom CBS media gezicht profiel interview`
3. `CBS jaarverslag media aandacht vermeldingen nieuws aantal publicaties persberichten`
4. `onderzoek economische berichtgeving Nederlandse media bronnen CBS CPB DNB inhoudsanalyse`
5. `"Van Mulligen" "woordvoerder" CBS economie arbeidsmarkt`
6. `nos.nl CBS hoofdeconoom Van Mulligen economie groei krimp recessie 2023 2024`
7. `NOS kritiek CBS cijfers fout correctie statistiek economen twijfel CBS-cijfer`

**Opgehaald (curl):**
- nos.nl/artikel/2612710 (bron #797): citaat letterlijk; Van Mulligen is daar de hoofdstem
- nos.nl/artikel/2584743 (bron #1498): het citaat van #2635 staat er niet aaneengesloten in
- nos.nl/l/2446533, 2452486, 2475310, 2520553, 2555791, 2576909, 2629224 (geteld: Van Mulligen, andere economen, CPB/DNB/banken)
- nos.nl/artikel/2445151 (koopkrachtcijfer, 2022)
- cbs.nl/…/corporate/2020/26/cbs-hoofdeconoom-ontkracht-mythes-in-nieuw-boek
- cbs.nl/…/podcast/2021/43/aflevering-8 (geen bruikbare passage)

## Negatieve resultaten (alleen in dit log)

- Geen onafhankelijke inhoudsanalyse gevonden van het aandeel CBS-bronnen in het economienieuws van de NOS. Zoekopdracht 4 gaf alleen ESB en een EUR-scriptie over krantenberichtgeving in het algemeen.
- In het CBS-jaarverslag vond ik via zoekopdracht 3 geen mediacijfers.
- **Eigen telling, niet ingediend** (eigen synthese, geen bron): in 7 NOS-berichten (2022–2026) over CBS-groei- en inflatiecijfers komt Van Mulligen in alle 7 voor.
  - Andere economische stemmen zijn schaars. In het bericht van november 2022 staat een verwijzing naar transactiedata van ABN Amro en Rabobank. In mei 2023 en mei 2024 gaat het alleen om links naar verwante berichten.
- Het NOS-stuk over het koopkrachtcijfer (2445151) gaat over het CPB, niet over het CBS. Niet gebruikt.
- De ESB-stukken over meetfouten en revisies van het CBS (zoekopdracht 7) gaan niet over de NOS-berichtgeving. Niet gebruikt.
- Een expliciete vermelding van Van Mulligen als "woordvoerder economie en arbeidsmarkt" kwam alleen naar voren in de samenvatting van de zoekmachine. Op een pagina heb ik hem niet kunnen controleren, dus niet gebruikt.

## Stance-balans

**2 steun / 2 tegen / 0 context / 2 ondergraving / 1 aspect**
- rel. 1169: steun #7891, tegen #7892 (influence), ondergraving #7890 (op #1627)
- rel. 1799: steun #7894, tegen #7895 (influence), ondergraving #7893 (op #2635), aspect #7896 (mechanism → 6)
- **Nieuwe bronnen:** #2478, #2479, #2480, #2481, #2482. Hergebruikt: #1498, #2389.
- **Wachtrij:** doel #82 → `klaar`, doel #83 → `klaar`.

---

Ronde 3 is klaar. Ik heb beide bewijsdoelen afgewerkt en op `klaar` gezet: vijf nieuwe bronnen en zeven argumenten. Alles staat op `voorgesteld` en telt nergens in mee tot de automatische beoordeling het heeft gecontroleerd.

- **CBS → NOS (rel. 1169):**
  - Het bestaande argument #1627 trekt uit één bericht de conclusie "structureel" (ondergraving #7890).
  - Drie NOS-berichten uit 2022, 2024 en 2025 geven het patroon: telkens licht Van Mulligen de CBS-cijfers toe (steun #7891).
  - Daartegenover meldde de NOS in 2022 zelf dat er discussie was over hoe het CBS de inflatie meet (tegen #7892).
- **Van Mulligen → NOS (rel. 1799):**
  - Bij argument #2635 staat het citaat niet letterlijk in de bron (ondergraving #7893).
  - Het patroon in de inflatieberichten 2022–2026 steunt het verband (steun #7894).
  - Tegen het mechanisme pleit dat de NOS hem altijd als CBS-hoofdeconoom aanduidt en in 2022 de aannames achter het cijfer liet zien (tegen #7895).
  - Daarom stel ik voor dit verband onder `bron_afhankelijkheid` te laten vallen (aspect #7896). Het CBS → NOS-verband bestaat al als rel. 1169.
- **Voor de mens:** rel. 1561 en 1562 gebruiken mechanismen die over denktanks gaan, terwijl het CBS een officieel statistiekbureau is. Ik heb daar niets op ingediend.

Dit log gaat via de runner naar `missies/logs/2026-10-08_nieuws-bewijs_ronde3.md`.

De Gmail- en Google Calendar-koppelingen van claude.ai moeten nog geautoriseerd worden, via de connector-instellingen op claude.ai. Tot dan zijn ze niet beschikbaar. Voor deze ronde waren ze niet nodig.

```

## Runner-metadata

- Exit-code: 0
- Duur: 350.3 s
- Oogst (edit_log-delta van `nieuws-bewijs`): 12
- Beëindigd: 2026-10-08T13:24:41
