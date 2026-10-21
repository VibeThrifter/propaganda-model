# Onbewaakte ronde — nieuws-scout · ronde1 · 2026-10-15

- Brief: `missies/nieuws_scout_brief.md` (blob `8b8cdf8efbf5`)
- Account: `nieuws-scout`
- Gestart: 2026-10-15T15:01:46

## Sessie-uitvoer

```
# Ronde-log: nieuws-scout, ronde 1, 15 oktober 2026

Ik heb drie doelen geclaimd en alle drie staan op `klaar`. Ingediend: 3 nieuwe personen, 5 verbanden, 8 argumenten en 5 bronnen. Alles staat op `voorgesteld`. Er kwam geen 409 en geen 429. De LinkedIn-zoekactie voor Van der Gaag liep vast op een time-out en heb ik niet herhaald. De sessie was niet verlopen en de stroomonderbreker sprong niet.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `8b8cdf8efbf5`
- **Account:** `nieuws-scout`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []`. Er was dus niets over te slaan, en ik heb geen reacties ingediend.
- **LinkedIn-rem:** `mag zoek` en `mag profiel` gaven allebei exit 0. Ik heb daarom geclaimd met `&linkedin=1`. Na de ronde gaf `status` voor zowel profiel als zoek 0/2 per uur en 0/10 per dag; de mislukte zoekactie telt niet mee.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` gaf drie doelen:
  - 221 `person:tim-hofman`
  - 222 `person:koen-schuiling`
  - 223 `person:marijn-van-der-gaag`

## Zoekopdrachten

**Web (WebSearch):**
1. `parlement.com Koen Schuiling burgemeester Groningen Den Helder VVD`
2. `Marijn van der Gaag bestuurder FNV streekvervoer`
3. `Tim Hofman BOOS BNNVARA presentator sinds`
4. `"Marijn van der Gaag" FNV`
5. `"Van der Gaag" FNV Streekvervoer bestuurder 2019 OR 2020 OR "nieuwe bestuurder" OR "in dienst"`

**Pagina's die ik zelf ophaalde (WebFetch en curl) om de citaten letterlijk te controleren:**
- binnenlandsbestuur.nl: koen-schuiling-vvd-nieuwe-burgemeester-groningen (17 juni 2019), personalia-week-49-2009 en burgemeester-schuiling-van-groningen-vertrekt-eind-oktober (ANP, 4 september 2024)
- nos.nl/l/2535780 (4 september 2024)
- fnv.nl: woensdag-14-oktober-stakingen-streekvoer (9 oktober 2026)
- cnv.nl: persbericht over Keolis (26 augustus 2021)
- bnnvara.nl: tim-hofman-wint-de-televizier-ring-presentator-2024 (niet gebruikt, draagt de functie niet)
- vrt.be: portret-tim-hofman-boos (19 januari 2022)

**LinkedIn:** `scrape_profile.py zoek "Marijn van der Gaag" --context "FNV" --max 5` liep vast op een Playwright-time-out (`Page.goto: Timeout 30000ms`). Ik heb het niet herhaald en geen profiel gescrapet.

**Database (alleen-lezen):**
- Entiteiten op de namen Hofman, Schuiling, Gaag, BOOS, BNNVARA, FNV, CNV, Groningen, Den Helder en VVD.
- De mechanismen dienstverband, lokaal_bestuursmandaat, partijlijn, partijbinding, draaideurconstructie, kroonbenoeming en podiumverlening.
- Rollen en hun definities (onder meer 70 `sociale_partner`).
- Precedenten: verbanden van personen met FNV en CNV, verbanden van personen met BNNVARA, `dienstverband`-relaties (mechanisme 192), en burgemeesters met `ambt` en een einddatum.

## Per doel

### 222 `person:koen-schuiling` → klaar
Het nieuws ging over een strafzaak. Volgens de brief heb ik alleen zijn publieke bestuursrol vastgelegd en niets over die zaak.
- **Bronnen:** 2903 (ANP via Binnenlands Bestuur, 4 september 2024) en 2904 (NOS, 4 september 2024).
- **Nieuwe entiteit:** 4885 Koen Schuiling (rol `lokale_bestuurder`).
- **Rel. 7994:** Schuiling → Gemeente Den Helder (1340), `ambt` Burgemeester, mechanisme 210, van 2010 tot 2019. Argument 10378.
- **Rel. 7995:** Schuiling → Gemeente Groningen (1332), `ambt` Burgemeester, mechanisme 210, van 2019 tot 2024-10-23. Argumenten 10379 en 10380.
- **Rel. 7996:** VVD (53) → Schuiling, `lidmaatschap`, mechanisme 92. Argument 10381 (VVD-fractievoorzitter in Groningen in 1996). Ik vond geen begindatum van het lidmaatschap en heb het verband daarom met `zonder_jaar` ingediend.

### 221 `person:tim-hofman` → klaar
- **Bron:** 2905 (VRT NWS, 19 januari 2022).
- **Nieuwe entiteit:** 4886 Tim Hofman (rol `journalist`).
- **Rel. 7997:** BNNVARA (139) → Hofman, `dienstverband`, mechanisme 192, functie "presentator BOOS", vanaf 2016. Argumenten 10382 en 10383.

### 223 `person:marijn-van-der-gaag` → klaar, met `vervolg: "linkedin"`
- **Bronnen:** 2906 (FNV-persbericht, 9 oktober 2026) en 2907 (CNV-persbericht, 26 augustus 2021).
- **Nieuwe entiteit:** 4887 Marijn van der Gaag (rol `sociale_partner`, rol 70). Die rol is gedefinieerd voor organisaties; ik heb hem gekozen omdat de persoon namens een sociale partner onderhandelt.
- **Rel. 7998:** Van der Gaag → FNV (873), `personeel`, mechanisme 18, functie "bestuurder FNV Streekvervoer". Argumenten 10384 en 10385. Het verband staat op `zonder_jaar`: de vroegste vermelding is uit augustus 2021, maar een startdatum vond ik niet.

## Negatieve resultaten (alleen in dit log)
- **Van der Gaag:** geen begin van de functie bij FNV gevonden in de FNV- en CNV-berichten (2021, 2022, 2026) en de twee webzoekopdrachten. LinkedIn liep op een time-out.
- **Schuiling:** geen begindatum van het VVD-lidmaatschap gevonden. Er is ook geen biografie op Parlement.com. Wethouder en raadslid in Groningen heb ik niet ingediend, omdat de bronnen daar geen jaartallen bij noemen (alleen raadslid vanaf 1994).
- **Hofman:** het BNNVARA-artikel over de Televizier-Ring 2024 noemt zijn functie niet en heb ik niet gebruikt.

## Stance-balans
8 steun, 0 tegen, 0 context.

```

## Runner-metadata

- Exit-code: 0
- Duur: 686.5 s
- Oogst (edit_log-delta van `nieuws-scout`): 21
- Beëindigd: 2026-10-15T15:13:12
