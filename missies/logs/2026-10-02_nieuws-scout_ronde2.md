# Onbewaakte ronde — nieuws-scout · ronde2 · 2026-10-02

- Brief: `missies/nieuws_scout_brief.md` (blob `af01853c2435`)
- Account: `nieuws-scout`
- Gestart: 2026-10-02T14:39:05

## Sessie-uitvoer

```
## Rondeverslag (nieuws-scout, ronde2, 2026-10-02)

Alle drie de doelen zijn afgerond met status `klaar`. Wat ik indiende staat op `voorgesteld`, met `smaad_hold` = 0. Er kwam geen 429, geen 409 en geen 400, en ik heb LinkedIn niet gebruikt.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `af01853c2435`, vooraf gecontroleerd met `git hash-object`.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []` en `via_reply: []`. Er was dus niets over te slaan. Ik heb alleen root-argumenten ingediend en nergens op gereageerd.
- **LinkedIn-rem vooraf:** `snelheidsrem.py mag zoek` gaf exit 0 en `mag profiel` ook exit 0.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` leverde #17 `org:artsen-zonder-grenzen`, #18 `person:ursula-von-der-leyen` en #19 `org:europees-parlement` op.

### Zoekopdrachten in de database (alleen-lezen)
- `SELECT id,name,type,status,primary_role_id FROM entities WHERE name LIKE '%Artsen%' OR '%MSF%' OR '%Leyen%' OR '%Europe%' OR '%EU%' OR '%Brussel%' OR '%Commissie%' OR '%Parlement%' OR '%EVP%' OR '%LUMC%'`
  - Er was geen knoop voor AZG, Von der Leyen of het Europees Parlement.
  - De Europese Commissie bestaat al als knoop 155.
- De relaties van 155 en 1153 heb ik bekeken. Daar staat Neelie Kroes → EC als `personeel` met mechanisme 18.
- `… WHERE name LIKE '%Postcode%' OR '%Tweede Kamer%' OR '%PAX%' …` gaf twee precedenten:
  - Postcode Loterij (39) → PAX: `donor`, mechanisme 180 (`ngo_financiering_bias`), rel. 746.
  - Tweede Kamer (rol 23) → Belastingdienst/EUvsDisinfo: `oppositie`, mechanisme 80 (`parlementaire_controle`).
- Mechanismen 18, 80 en 180 heb ik ook gecontroleerd op hun rolparen. De CHECK in `schema.sql` op `source_type` heb ik nagekeken.

### Zoekopdrachten op het web
- `Postcode Loterij Artsen zonder Grenzen bijdrage goed doel`
- `Ursula von der Leyen herkozen voorzitter Europese Commissie Europees Parlement persbericht`
- `Europees Parlement bevoegdheden democratische controle Commissie motie van afkeuring europarl.europa.eu`

De drie bronpagina's heb ik als platte tekst opgehaald. Alle zes de quotes staan er letterlijk in (gecontroleerd met `in`).

### #17 Artsen zonder Grenzen → klaar (entiteit 1254)
- **Bron #2349:** artsenzondergrenzen.nl, "Artsen zonder Grenzen en de Postcode Loterij". Voorgestelde betrouwbaarheid `primair`, onderwerp `nl_systeem`.
- **Entiteit #1254:** type `ngo`, rol-suggestie 58 (`maatschappelijke_organisatie`).
- **Relatie #2295:** Postcode Loterij (39) → AZG, `donor`, mechanisme 180, vanaf 1993. Dit volgt het PAX-precedent.
- **Argumenten #3865 en #3866:** sinds 1993 begunstigde, en € 13,5 miljoen in 2024.
- De besmette medewerker uit de context is een privépersoon. Die heb ik niet onderzocht.

### #18 Ursula von der Leyen → klaar (entiteit 1255)
- **Waarom in scope:** de Europese Commissie heeft in het model al directe edges in het Nederlandse netwerk: DSA-moderatie van platforms en financiering van Clingendael. De uitzondering in de brief voor "buitenland, geen NL-rol" past daarom niet. Dit is een afweging; een reviewer kan hem terugdraaien.
- **Bron #2350:** persbericht van het Europees Parlement van 18-07-2024. Voorgestelde betrouwbaarheid `primair`.
- **Entiteit #1255:** type `persoon`, rol-suggestie 33 (`politicus`).
- **Relatie #2296:** Von der Leyen → Europese Commissie (155), `bestuurder`, mechanisme 18, vanaf 2019. Dit volgt het precedent Van Weel → J&V.
- **Argumenten #3867 en #3868:** voorzitter sinds 2019, en herkozen op 18 juli 2024 met 401 stemmen.
- **LinkedIn:** bewust overgeslagen, omdat de primaire EP-bron haar functie volledig dekt.

### #19 Europees Parlement → klaar (entiteit 1256)
- **Bron #2351:** EP-factsheet "Het Europees Parlement: bevoegdheden". Voorgestelde betrouwbaarheid `institutioneel`.
- **Entiteit #1256:** type `overheidsinstelling`, rol-suggestie 23 (`parlementair_controleur`). Dit volgt het precedent van de Tweede Kamer.
- **Relatie #2297:** EP → Europese Commissie (155), `oppositie`, mechanisme 80 (`parlementaire_controle`).
- **Argumenten #3869 en #3870:** de motie van afkeuring (art. 17 lid 8 VEU en art. 234 VWEU) en het collectieve ontslag dat daarop volgt.
- **De autokeur pakt dit niet op.** `oppositie` staat niet in de autokeur-lijst, dus deze relatie heeft altijd een menselijke reviewer nodig.

### Negatieve resultaten (alleen in het log)
- De rolzin "mede-initiatiefnemer Democracy Shield" voor het EP heb ik niet geverifieerd. Ik heb hem niet ingediend.
- Een EP → Von der Leyen-relatie (de verkiezing van de Commissievoorzitter) heb ik niet ingediend, omdat er geen passend mechanisme voor is.
- Haar CDU/EVP-lidmaatschap heb ik niet ingediend: geen van beide heeft een knoop in het model, en het is buiten het Nederlandse netwerk.

### LinkedIn-rem na afloop (`snelheidsrem.py status`)
De automatische modus staat aan en is nu actief. Gebruikt: profiel 0 van 2 per uur en 0 van 10 per dag, zoeken 0 van 2 per uur en 0 van 10 per dag. LinkedIn is niet gebruikt: geen exit 75 of 76 en geen verlopen sessie.

### Stance-balans
**6 steun / 0 tegen / 0 context** (argumenten #3865 t/m #3870). Het zijn allemaal neutrale structuurfeiten uit primaire of institutionele bronnen.

**Voor de eigenaar:** de connectoren voor Gmail en Google Calendar moeten nog geautoriseerd worden in de connector-instellingen van claude.ai. Tot dan zijn ze niet bruikbaar; deze ronde had ze niet nodig.

Bronnen:
- [Artsen zonder Grenzen – Artsen zonder Grenzen en de Postcode Loterij](https://www.artsenzondergrenzen.nl/over-ons/nationale-postcode-loterij/)
- [Europees Parlement – Parlement herverkiest Ursula von der Leyen als Voorzitter Europese Commissie](https://www.europarl.europa.eu/news/nl/press-room/20240710IPR22812/parlement-herverkiest-ursula-von-der-leyen-als-voorzitter-europese-commissie)
- [Europees Parlement – Het Europees Parlement: bevoegdheden](https://www.europarl.europa.eu/factsheets/nl/sheet/19/het-europees-parlement-bevoegdheden)
- Gevonden maar niet gebruikt: [postcodeloterij.nl tbc-project](https://www.postcodeloterij.nl/goede-doelen/bijzondere-projecten/artsen-zonder-grenzen-doorbraak-voor-tbc), [EP 2019 verkiezing](https://www.europarl.europa.eu/news/nl/press-room/20190711IPR56824/het-parlement-kiest-ursula-von-der-leyen-als-commissievoorzitter), [EUR-Lex samenvatting EP](https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=LEGISSUM:european_parliament), [Joop/BNNVARA](https://www.bnnvara.nl/joop/artikelen/ursula-von-der-leyen-herkozen-als-voorzitter-europese-commissie-vvd-en-nsc-waren-voor-pvv-tegen)

```

## Runner-metadata

- Exit-code: 0
- Duur: 171.8 s
- Oogst (edit_log-delta van `nieuws-scout`): 15
- Beëindigd: 2026-10-02T14:41:57
