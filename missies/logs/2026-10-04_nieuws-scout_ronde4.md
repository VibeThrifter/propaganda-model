# Onbewaakte ronde — nieuws-scout · ronde4 · 2026-10-04

- Brief: `missies/nieuws_scout_brief.md` (blob `af01853c2435`)
- Account: `nieuws-scout`
- Gestart: 2026-10-04T20:17:18

## Sessie-uitvoer

```
Ronde 4 is af: van de drie doelen heb ik er één ingediend en twee overgeslagen. Alles staat op `voorgesteld`. Er kwam geen 429, 409 of 400 terug, en de LinkedIn-sessie leeft nog. Net als in de vorige rondes is deze uitvoer het log: de runner zet hem onder de kop die al in `missies/logs/2026-10-04_nieuws-scout_ronde4.md` staat.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `af01853c2435`. Gecontroleerd met `git hash-object`: `af01853c2435c1ced30d5fe51d3355d30818ba0a`.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []` en `via_reply: []`. Ik heb op geen bestaand argument gereageerd.
- **LinkedIn-rem:**
  - `snelheidsrem.py mag zoek` en `mag profiel` gaven allebei exit 0.
  - Vóór de ronde stond hij op 1/2 per uur en 1/10 per dag, voor zowel profielen als zoeken.
  - Na de ronde staat hij op 2/2 per uur en 2/10 per dag. Volgende kans: 2026-10-04T20:49:50.
  - Er was geen exit 75 of 76 en de sessie is niet verlopen.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` leverde #44 `person:mitchell-esajas`, #45 `org:dat` en #46 `org:fox-news` op.

### Zoekopdrachten in de database (alleen-lezen, letterlijk)
1. `SELECT id,name,type,status,primary_role_id FROM entities WHERE name LIKE '%Esajas%' OR name LIKE '%Black Archives%' OR name LIKE '%Fox%' OR name LIKE '%New Urban Collective%' OR name LIKE '%Kick Out Zwarte Piet%' OR name LIKE '%Black%';`
   - Esajas bestond nog niet.
   - Bestaande knopen: The Black Archives #298 en New Urban Collective #323.
   - Fox News en Kick Out Zwarte Piet bestaan niet.
2. `SELECT id,name FROM roles WHERE name LIKE '%activ%' OR … '%directie%' …`: directie is 49, maatschappelijke_organisatie 58 en publieke_stem 60.
3. Relaties van en naar #298 en #323. Precedent: rel. 618 is Ernestine Comvalius → The Black Archives, `bestuurder` met mechanisme 18 (`draaideurconstructie`).
4. Precedenten persoon → ngo, goedgekeurd: `bestuurder` met mechanisme 18 komt het vaakst voor (12 keer, bij Zorgbelang).
5. Rollen 48 en 49 opgezocht en mechanisme 18 gecontroleerd: `draaideurconstructie`, 33→32.
6. Bestaande bronnen gezocht op `%Black Archives%`/`%Esajas%`: #199 (Openresearch), en #228 en #421, allebei `theblackarchives.nl/over-ons.html`. Ik hergebruik #228 en heb geen dubbele bron aangemaakt.
   - Eerste versie van de query mislukte op de kolom `sl.locator_type`. De juiste naam is `location_type`.

### Zoekopdrachten op het web en LinkedIn (letterlijk)
- Opgehaald met curl:
  - `https://nos.nl/l/2633429`. NOS noemt hem "antiracismeactivist … bekend van Kick Out Zwarte Piet en de Black Lives Matter-protesten", maar zegt daar niets over The Black Archives.
  - Het AD-artikel uit de context gaf een JS-stub van 8 KB zonder de tekst.
  - `theblackarchives.nl/about-us.html` en `/over-ons.html` (HTTP 200). Dit is de primaire bron.
  - De NOS-link uit 2023 (`nos.nl/artikel/2473965-…`). Daarin roemt Halsema hem "als initiatiefnemer van … The Black Archives". Ik heb dat alleen ter bevestiging gebruikt en niet ingediend.
- De quote "The Black Archives wordt op dagelijkse basis geleid door Mitchell Esajas (algemeen management)" staat letterlijk één keer op de over-ons-pagina.
- LinkedIn:
  - Zoeken: `scrape_profile.py zoek "Mitchell Esajas" --context "The Black Archives" --max 5` gaf één treffer: "Co-founder New Urban Collective, The Black Archives & Ongekende Talenten".
  - Gescrapet: https://www.linkedin.com/in/mitchellesajas/. Naam en organisatie kloppen.

### Per doel
**#44 Mitchell Esajas → klaar** (rol-suggestie: directie, 49)
- Bronnen: #228 (bestaand) en #2372, het nieuwe LinkedIn-profiel, voorgesteld als `grijs`.
- Entiteit #1270.
- Relatie #2325 van Esajas naar The Black Archives: `bestuurder`, mechanisme 18, vanaf 2015-06. Dat volgt het precedent van rel. 618.
- Argumenten:
  - #3906, supporting, met de verbatim quote uit #228.
  - #3907, supporting, op basis van LinkedIn.
- **Bewust niet ingediend:**
  - Op LinkedIn noemt hij zich "Co-founder & Chairman" van New Urban Collective. Volgens de primaire over-ons-pagina bestaat het NUC-bestuur sinds 2020 uit anderen, dus die claim is niet sluitend.
  - Zijn bestuursfunctie bij Meldpunt Discriminatie Regio Amsterdam (2017–2020) staat los van de rol uit het nieuws.
  - De oudere UvA-functies.
  - De lintje-controverse. Dat is geen structuurfeit, en een persoonsclaim daarover hoort hier niet.

**#45 "Dat" → overgeslagen**
- Dit is geen actor maar een parse-fout: een woord uit RTL Boulevard- en NOS-koppen. Ik heb niets ingediend.

**#46 Fox News → overgeslagen** (buitenland, geen NL-rol)
- Een Amerikaanse zender die in de context alleen voorkomt in berichten over Netanyahu. Ik heb niets ingediend.

### Negatieve resultaten (alleen in dit log)
- Het AD-artikel bleek niet leesbaar (JS-stub).
- Het NOS-artikel van 2026 vermeldt The Black Archives niet.
- De rol bij NUC is niet sluitend te staven.

### Stance-balans
2 steun, 0 tegen, 0 context.

De resultaat-id's staan in `data/scout/nieuws-person-mitchell-esajas.resultaat.json`. Ik heb rechtstreeks via de API ingediend in plaats van via `scout_indienen.py`, omdat dat script geen bestaande bron-id kan hergebruiken.

```

## Runner-metadata

- Exit-code: 0
- Duur: 201.6 s
- Oogst (edit_log-delta van `nieuws-scout`): 5
- Beëindigd: 2026-10-04T20:20:39
