# Onbewaakte ronde — nieuws-scout · ronde3 · 2026-10-03

- Brief: `missies/nieuws_scout_brief.md` (blob `af01853c2435`)
- Account: `nieuws-scout`
- Gestart: 2026-10-03T11:47:18

## Sessie-uitvoer

```
## Ronde 3 van nieuws-scout (2026-10-03)

Alle drie de doelen zijn afgesloten. "Pro" (#33) staat op `klaar`, "BBC" (#32) en "UEFA" (#34) op `overgeslagen`. Er kwam geen 429, 409 of 400. Ook was er geen LinkedIn-exit 75 of 76 en de sessie is niet verlopen. De runner zet deze uitvoer in `missies/logs/2026-10-03_nieuws-scout_ronde3.md`, dus dit verslag is het log.

**Eén punt voor de eigenaar:** ik heb **hernoem-voorstel #63** ingediend: "GroenLinks-PvdA" wordt "Progressief Nederland (PRO)". Het staat open en wacht op één menselijke reviewer. Ik heb het niet zelf doorgevoerd.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `af01853c2435`. Gecontroleerd met `git hash-object`: `af01853c2435c1ced30d5fe51d3355d30818ba0a`.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []` en `via_reply: []`. Ik heb alleen root-argumenten ingediend.
- **LinkedIn-rem vooraf:** `snelheidsrem.py mag zoek` en `mag profiel` gaven allebei exit 0.
  - Status vóór en na de ronde was gelijk: profiel 1 van 2 per uur en 1 van 10 per dag, zoeken 0 van 2 en 0 van 10.
  - LinkedIn is niet gebruikt, want alle drie de doelen zijn organisaties.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` leverde #32 `org:bbc`, #33 `org:pro` en #34 `org:uefa` op.

### Zoekopdrachten in de database (alleen-lezen, letterlijk)
1. `SELECT id,name,type,status FROM entities WHERE name LIKE '%BBC%' OR name LIKE '%UEFA%' OR name LIKE 'Pro %' OR name LIKE 'PRO%' OR name LIKE '%Partij voor Rechtsstaat%' OR name LIKE '%(PRO)%' OR name='Pro';`
   - Gevonden: alleen Procter & Gamble (35), ProDemos (288), PZC (453) en Propaganda (801).
   - Er is geen knoop voor BBC, UEFA of Pro.
2. `SELECT id,name,type,status,primary_role_id,description FROM entities WHERE name LIKE '%GroenLinks%' OR name LIKE '%PvdA%' OR name LIKE '%Partij van de Arbeid%' OR name LIKE '%Hamer%' OR name LIKE '%Spekman%' OR name LIKE '%Lahlah%' OR name LIKE '%Klaver%' OR name LIKE '%Raad voor het Openbaar Bestuur%';`
   - Gevonden: **GroenLinks-PvdA (1073)**, PvdA (56), GroenLinks (153), Attje Kuiken (790), Jesse Klaver (1079) en Madeleine Klinkhamer (414, vangst van het `%Klaver%`-patroon, niet relevant).
3. Een controle op al bestaande bronnen, op locator `%2616935%` / `%groenlinks-pvda-wordt-progressief%` en op titel. Er waren er geen.
4. De argumenten op entiteit 1073. Er was er één, #3006 (ongecontroleerd, over de fusie).
5. De bestaande voorstellen op 1073. Er waren er geen.
6. Het precedent voor een hernoeming van een entiteit: voorstel #51 (Propaganda, geaccepteerd).

### Zoekopdrachten op het web (letterlijk) en opgehaalde pagina's
- Opgehaald met curl:
  - de drie artikelen uit de context van #33: [NieuwRechts](https://nieuwrechts.nl/113388-pro-kopstuk-leidt-onafhankelijke-bestuursraad-die-het-kabinet-adviseert), [NOS l/2633453](https://nos.nl/l/2633453) en [GeenStijl](https://www.geenstijl.nl/5192274/box-3-box-3-box-3/)
  - Alle drie gebruiken "PRO/Pro" als naam van een politieke partij: "oppositiepartij Pro" en "lijsttrekker van PRO voor de Eerste Kamer".
- WebSearch: `GroenLinks-PvdA nieuwe partijnaam PRO`
- Opgehaald met curl (allebei 200), de quotes letterlijk op de pagina gecontroleerd:
  - [NOS: GL-PvdA mag Pro gaan heten](https://nos.nl/artikel/2616935-gl-pvda-mag-pro-gaan-heten-raad-van-state-wijst-bezwaren-lokale-partijen-af)
  - [Binnenlands Bestuur: GroenLinks-PvdA wordt Progressief Nederland](https://www.binnenlandsbestuur.nl/bestuur-en-organisatie/groenlinks-pvda-wordt-progressief-nederland-roepnaam-pro)
- Wikipedia kwam in de zoekresultaten voor, maar alleen als vindplaats. Ik heb het niet als bron gebruikt.

### #33 Pro → klaar (entiteit 1073, hergebruikt)
**Wat ik heb vastgesteld:** Pro is Progressief Nederland, de nieuwe naam van GroenLinks-PvdA. Het is dezelfde partij, dus ik heb geen tweede knoop gemaakt.

**Bronnen** (allebei voorgesteld als `regulier`, onderwerp `nl_systeem`):
- #2363: Binnenlands Bestuur, 26 maart 2026
- #2364: NOS, 3 juni 2026

**Argumenten** (allebei `supporting` op entiteit 1073, status `voorgesteld`, geen `smaad_hold`):
- **#3892** (bron #2363), quote: "GroenLinks-PvdA gaat verder onder de naam Progressief Nederland. In het dagelijks gebruik kiest de partij voor de roepnaam ‘Pro’."
- **#3893** (bron #2364), quote: "GroenLinks-PvdA mag verder onder de naam Pro (Progressief Nederland). Dat oordeelt de Raad van State."

**Voorstel #63** (`hernoemen`, status open):
- 1073 wordt "Progressief Nederland (PRO)". De oude naam blijft via lineage terug te vinden.
- In de motivatie stel ik voor om ook de beschrijving bij te werken. Die spreekt nu nog van "fusieverband".
- Het manifest staat in `data/scout/nieuws-org-pro.json`, de resultaten in `.resultaat.json`.

**Bewust niet ingediend:** Mariëtte Hamer (ROB-voorzitter en lijsttrekker van PRO voor de Eerste Kamer, volgens NieuwRechts). Dat valt buiten dit doel en NieuwRechts is een grijze bron. Het blijft een mogelijke lead voor later, als er een primaire bron voor is.

### #32 BBC → overgeslagen
De BBC is een Britse omroep. De context gaat over buitenlandnieuws: olifanten in Kenia, Netanyahu en het staatsbezoek van Charles aan Trump. Er is geen Nederlands eigendom of Nederlandse functie, dus geen NL-rol. Niets ingediend.

### #34 UEFA → overgeslagen
De UEFA is de Europese voetbalbond en de context is sportnieuws. Er is geen rol in het netwerk. Niets ingediend.

### Negatieve resultaten (alleen in dit log)
- Er bestaat geen modelknoop voor BBC, UEFA of "Pro" als losse naam.
- Er bestond nog geen bron over de naamswijziging.

### Stance-balans
2 steun / 0 tegen / 0 context. Daarnaast 1 hernoem-voorstel (#63), 2 bronnen, 0 entiteiten en 0 relaties.

```

## Runner-metadata

- Exit-code: 0
- Duur: 160.0 s
- Oogst (edit_log-delta van `nieuws-scout`): 5
- Beëindigd: 2026-10-03T11:49:58
