# Onbewaakte ronde — nieuws-scout · ronde1 · 2026-10-06

- Brief: `missies/nieuws_scout_brief.md` (blob `af01853c2435`)
- Account: `nieuws-scout`
- Gestart: 2026-10-06T11:20:40

## Sessie-uitvoer

```
# nieuws-scout, ronde 1 (2026-10-06)

Van de drie doelen heb ik er één ingediend (Tom de Nooijer, op `klaar`) en twee overgeslagen. Alles wat ik indiende staat op `voorgesteld`. Ik kreeg geen 429 en geen 409. Twee bronnen gaven een 400; die heb ik in dezelfde ronde hersteld (zie hieronder). LinkedIn heb ik niet gebruikt, dus de sessie is ook niet getest. Net als in de vorige rondes is deze uitvoer het log: de runner zet hem onder de kop die al in `missies/logs/2026-10-06_nieuws-scout_ronde1.md` staat.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `af01853c2435`. Gecontroleerd met `git hash-object`: `af01853c2435c1ced30d5fe51d3355d30818ba0a`.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []` en `via_reply: []`. Ik heb op geen bestaand argument gereageerd.
- **LinkedIn-rem:** `mag zoek` en `mag profiel` gaven allebei exit 0. Vóór en na de ronde stond de teller op 0/2 per uur en 0/10 per dag, voor zowel profielen als zoeken. Er was geen exit 75 of 76.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` leverde #62 `org:google-favoriethet`, #63 `person:tom-de-nooijer` en #64 `person:brian-may` op.

## Zoekopdrachten in de database (alleen-lezen, letterlijk)
1. `SELECT id,name,type,status,primary_role_id FROM entities WHERE name LIKE '%Nooijer%' OR name LIKE '%Oldebroek%' OR name LIKE '%SGP%' OR name LIKE '%ChristenUnie%';`
   - Alleen SGP #1072 en ChristenUnie #379. De Nooijer en Oldebroek staan er niet in.
2. `SELECT id,sleutel,naam,status,entity_id FROM nieuws_doelen WHERE naam LIKE '%Nooijer%' OR naam LIKE '%Oldebroek%';`
   - Alleen doel #63 zelf.
3. `SELECT id,name FROM roles WHERE name IN ('politicus','wethouder','bestuurder','lokale_overheid');`
   - `politicus` is rol 33.
4. `SELECT id,name,type,status FROM entities WHERE type='overheidsinstelling' AND (name LIKE 'Gemeente%');`
   - Bestaande gemeenten: Amsterdam #229, Hilversum #440 en Arnhem #1257.
5. Relaties van en naar #229, #440, #1257 en #1072.
   - Precedent wethouder: persoon → gemeente als `bestuurder` met mechanisme 18 (Moorman #2272, Halsema #2303, Marcouch #2298).
   - Precedent partijlid: SGP → persoon als `lidmaatschap` met mechanisme 163 (#1912 en #1913).
6. `SELECT id,name,source_role_id,target_role_id FROM mechanisms WHERE id IN (18,163);`
7. De rollen van de gemeente- en partijknopen: een gemeente krijgt rol 41 `gezagsinstituut`, een partij rol 45.
8. Bestaande bronnen met `title`/`location` LIKE `%Oldebroek%`/`%Nooijer%`: geen treffers.
9. `entities WHERE name LIKE '%Ongehoord%' OR '%Christelijk Verbond%' OR '%CVO%' OR '%Algemeen Belang%'`
   - Alleen Ongehoord Nederland #205 (omroep).
   - Bij de relaties van #205 staan de precedenten #512–#514.
10. `mechanisms WHERE name IN ('dienstverband','partijlijn','partijbinding','draaideurconstructie')`
    - `dienstverband` is #192 (rol 2 naar rol 26).
11. Goedgekeurde `dienstverband`-relaties
    - Precedent journalist: medium → persoon met mechanisme 192 (Duk #1383, Castricum #1384, Smid #2313–#2315).
12. `roles WHERE id IN (2,26,32,33,41,45,47,49)`.

## Zoekopdrachten op het web (letterlijk)
- Opgehaald met curl:
  - `https://www.oldebroek.nl`, daarna `/Bestuur_en_organisatie`, `/Bestuur_en_organisatie/College_van_B_W` en `…/Samenstelling_en_taken_college`. Daar staat "Wethouder Tom de Nooijer".
  - `…/Samenstelling_en_taken_college/Tom_de_Nooijer`. Dit is de primaire bron: portefeuille en nevenfuncties.
  - `https://nieuwrechts.nl/113460-…` en `https://nieuwrechts.nl/113494-…`. Beide geven alleen context; ik heb ze niet als bron gebruikt.
  - `https://www.cvo-oldebroek.nl`, `https://cvo-oldebroek.nl` en `https://www.cvooldebroek.nl` gaven alle drie geen verbinding (000).
- WebSearch:
  - `CVO Oldebroek partij Tom de Nooijer wethouder`
  - `Tom de Nooijer geïnstalleerd wethouder Oldebroek juli 2026`
  - `Tom de Nooijer presentator Ongehoord Nederland gestopt`
- Daarna opgehaald met curl:
  - `https://www.cvoldebroek.nl/tom-de-nooijer-voorgedragen-als-kandidaat-wethouder-cvo/`. Het bevestigt de voordracht; ik heb het niet als bron gebruikt.
  - `villamedia.nl/artikel/ongehoord-nederland-presentator-wordt-wethouder-in-oldebroek`
  - `gld.nl/nieuws/8482586/…`
  - `oldebroek.nl/…/Juli_2026/Wethouders_CVO_SGP_en_ABO_ge_nstalleerd_voor_nieuwe_bestuursperiode`
  - `gld.nl/nieuws/8451023/tom-de-nooijer-stopt-als-presentator-ongehoord-nederland`
- Alle zes de quotes heb ik met een script verbatim gecontroleerd op de opgehaalde pagina's: 6 van de 6 gaven `True`.
- Wikipedia (`nl.wikipedia.org/wiki/Tom_de_Nooijer`) heb ik alleen als vindplaats gebruikt en niet geciteerd.
- **LinkedIn heb ik bewust overgeslagen.** De collegepagina en het installatiebericht van de gemeente Oldebroek (primaire bronnen), samen met het nieuws van Omroep Gelderland en Villamedia/ANP, dekken zijn hele publieke loopbaan: SGP, CVO, ON en wethouder. Er was geen zoek- of scrape-actie en er is geen profiel-URL.

## Per doel
**#63 Tom de Nooijer → klaar** (entity_id 1272, rol-suggestie: politicus, 33)
- Nieuwe entiteiten:
  - #1272 Tom de Nooijer (persoon, rol 33)
  - #1273 Gemeente Oldebroek (overheidsinstelling, rol 41)
  - #1274 Christelijk Verbond Oldebroek (partij, rol 45)
- Bronnen:
  - #2381: gemeente Oldebroek, De Nooijer-pagina; voorgesteld als `primair`.
  - #2382: gemeente Oldebroek, installatiebericht van 9 juli 2026; voorgesteld als `primair`.
  - #2383: Omroep Gelderland, 20 maart 2026; voorgesteld als `regulier`.
  - #2384: Villamedia/ANP, 5 juni 2026; voorgesteld als `regulier`.
- Relatie #2329: De Nooijer naar Gemeente Oldebroek, `bestuurder`, mechanisme 18, vanaf 2026-07-09.
  - Argument #3920, supporting: "Tom de Nooijer is wethouder en 1e locoburgemeester van de gemeente Oldebroek."
  - Argument #3921, supporting: "…zijn Tom de Nooijer (CVO), Erik Doornwaard (SGP) en Martijn Kerkmans (ABO) beëdigd als wethouders…"
- Relatie #2330: CVO naar De Nooijer, `lidmaatschap`, mechanisme 163.
  - Argument #3922, supporting: "Voorzitter CVO (onbezoldigd)".
  - Argument #3923, supporting: "…is lijsttrekker van Christelijk Verbond Oldebroek…"
- Relatie #2331: Ongehoord Nederland naar De Nooijer, `dienstverband`, mechanisme 192, tot 2026-03-20.
  - Argument #3924, supporting: "Tom de Nooijer stopt bij Ongehoord Nederland om zich volledig op de lokale politiek te richten."
  - Argument #3925, supporting: "Tom de Nooijer, tot voor kort presentator bij de omroep Ongehoord Nederland…"
- **Herstelde fout:** de eerste indienrun gaf bij de twee nieuwsbronnen een 400 ("Ongeldige reliability_voorgesteld"), omdat ik `secundair` had opgegeven.
  - Daardoor sloeg het script drie argumenten over.
  - Een tweede manifest (`data/scout/nieuws-person-tom-de-nooijer-b.json`) heeft ze ingediend op de bestaande relaties #2330 en #2331, met `regulier` als betrouwbaarheid. Er is niets dubbel aangemaakt.
- Bij de controle in de database staat alles op `voorgesteld`, met `smaad_hold=0`.
- Bewust niet ingediend:
  - Zijn SGP-raadslidmaatschap (2018 tot ca. 2021/2022). Er is geen betrouwbare einddatum, en een open relatie zou ten onrechte een huidig lidmaatschap suggereren.
  - De nevenfunctie als kerkorganist (privé/geloof, verboden door de brief).
  - De Trouw-column en de reactie van Jetten (NieuwRechts). Dat zijn losse incidenten, geen structuurfeit en geen gedocumenteerd patroon.

**#62 "Google-favorietHet" → overgeslagen** (geen actor). Het is een verminkt tekstfragment uit drie ongerelateerde RTL-artikelen. Ik heb niets ingediend.

**#64 Brian May → overgeslagen** (artiest, buitenland, geen rol in het NL-netwerk). Ik heb niets ingediend.

## Negatieve resultaten (alleen in dit log)
- Drie gegokte CVO-domeinen gaven geen verbinding (`cvo-oldebroek.nl`, `www.cvo-oldebroek.nl`, `www.cvooldebroek.nl`). Het echte domein is `cvoldebroek.nl`.
- De collegepagina van Oldebroek noemt zelf geen ingangsdatum. Die komt uit het installatiebericht.

## Stance-balans
6 steun, 0 tegen, 0 context.

De resultaat-id's staan in `data/scout/nieuws-person-tom-de-nooijer.resultaat1.json` en `….resultaat2.json` (samengevoegd in de PATCH van doel #63). De manifesten zijn `data/scout/nieuws-person-tom-de-nooijer.json` en `…-b.json`.

Bronnen (web):
- [gemeente Oldebroek – Wethouder Tom de Nooijer](https://www.oldebroek.nl/Bestuur_en_organisatie/College_van_B_W/Samenstelling_en_taken_college/Tom_de_Nooijer)
- [gemeente Oldebroek – Wethouders geïnstalleerd](https://www.oldebroek.nl/Bestuur_en_organisatie/Actueel/Nieuwsberichten/Juli_2026/Wethouders_CVO_SGP_en_ABO_ge_nstalleerd_voor_nieuwe_bestuursperiode)
- [Omroep Gelderland – De Nooijer stopt als presentator ON](https://www.gld.nl/nieuws/8451023/tom-de-nooijer-stopt-als-presentator-ongehoord-nederland)
- [Villamedia – ON-presentator wordt wethouder](https://www.villamedia.nl/artikel/ongehoord-nederland-presentator-wordt-wethouder-in-oldebroek)
- [Omroep Gelderland – voorgedragen als wethouder](https://www.gld.nl/nieuws/8482586/ex-presentator-ongehoord-nederland-tom-de-nooijer-voorgedragen-als-wethouder-in-oldebroek)
- [CVO – voordracht kandidaat-wethouder](https://www.cvoldebroek.nl/tom-de-nooijer-voorgedragen-als-kandidaat-wethouder-cvo/)

Noot voor de eigenaar: de MCP-servers claude.ai Gmail en Google Calendar zijn niet geautoriseerd. Deze missie had ze niet nodig. Wil je ze gebruiken, autoriseer ze dan via de connector-instellingen op claude.ai.

```

## Runner-metadata

- Exit-code: 0
- Duur: 237.9 s
- Oogst (edit_log-delta van `nieuws-scout`): 16
- Beëindigd: 2026-10-06T11:24:38
