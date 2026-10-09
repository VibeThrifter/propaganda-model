# Onbewaakte ronde — nieuws-bewijs · ronde1 · 2026-10-09

- Brief: `missies/nieuws_bewijs_brief.md` (blob `a18d04acb03b`)
- Account: `nieuws-bewijs`
- Gestart: 2026-10-09T09:24:46

## Sessie-uitvoer

```
# Ronde-log nieuws-bewijs · ronde1 · 2026-10-09

- **Brief:** `missies/nieuws_bewijs_brief.md`, blob `a18d04acb03b`
- **Account:** `nieuws-bewijs`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `[1627, 2134, 2322, 2339, 2635]`. Geen van deze id's hoort bij de doelen van deze ronde.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` gaf doel #109 (`relatie:129`) en doel #112 (`relatie:127`).
- Er kwam geen 409, 429 of 400 terug.
- LinkedIn heb ik niet gebruikt. Dit onderzoek gaat over hoe media met hun bronnen omgaan, niet over iemands loopbaan.
- **Indienscript:** `data/scout/bewijs-2026-10-09-r1.py`. Het controleert elk citaat vooraf met `bronchecker.zoek_citaat` tegen de live pagina of de pdf (PDFKit), en alle 7 citaten werden letterlijk teruggevonden. Het resultaat staat in `data/scout/bewijs-2026-10-09-r1.resultaat.json`.

## Doel #112: `relatie:127`, PVV → De Telegraaf (`politicus_als_bron`, #49) → **klaar**

**Wat het model beweert:** volgens het mechanisme zijn politici primaire bronnen en zijn journalisten afhankelijk van hun goodwill. De relatie heeft type `alliantie` en de beschrijving "PVV en Telegraaf delen regelmatig framing op immigratie en veiligheid".
- **Wat ervoor zou pleiten:** De Telegraaf krijgt toegang tot de PVV die andere media niet krijgen.
- **Wat ertegen zou pleiten:** De Telegraaf besteedt weinig aandacht aan de PVV, of is er kritisch over.

**Bestaand argument:** #129 (supporting, legacy) heeft geen bron. De maintainer zette het eerder op `betwist` (edit_log 9218: "biasduiding, geen structureel te sourcen feit"). Ik heb er geen ondergraving op gezet, want het oordeel staat er al met reden.

**Neutrale zoekvraag:** *"Hoe verhouden de PVV/Wilders en De Telegraaf zich als bron en medium: wie krijgt toegang, hoeveel aandacht krijgt de PVV, en hoe beoordeelt de krant de partij?"*

| Bron (nieuw) | Argument | Stance |
|---|---|---|
| #2532 Welingelichte Kringen 31-12-2010 (voorstel `grijs`), #2531 NOS 16-3-2017, #2530 Damstra & Vliegenthart, *Hard to get and hard to neglect* (voorstel `academisch`) | **#7952**: Wilders sprak met De Telegraaf in 2010 en 2017. Volgens Damstra & Vliegenthart weigerde hij intussen verzoeken van de Volkskrant, NRC, DWDD, Jinek en Pauw steeds vaker en uiteindelijk structureel | steun |
| #2530 | **#7953** (`property=influence`): in 2004–2017 besteedde De Telegraaf van drie kranten de minste aandacht aan Wilders/PVV: 1,33%, tegen 2,93% bij de Volkskrant en 3,08% bij NRC | tegen |
| #2533 DutchNews.nl 21-3-2014 | **#7954** (`property=influence`): De Telegraaf veroordeelde in maart 2014 in een redactioneel webcommentaar Wilders' uitspraken over Marokkanen | tegen |

**Mechanisme:** `politicus_als_bron` past op de selectieve toegang. De mechanismen `gecoordineerde_voorlichting` (#84) en `woordvoerdersregie` (#149) hebben als doelrol de voorlichter, niet het medium. Daarom heb ik geen aspect-argument ingediend.

**Voor de mens:** geen enkele gevonden bron draagt de relatiebeschrijving "delen framing" of het type `alliantie`.

## Doel #109: `relatie:129`, VVD → DPG Media (`bron_afhankelijkheid`, #6) → **niets_gevonden**

**Wat het model beweert:** "VVD als langdurige regeringspartij is routineuze officiële bron voor media". Dat staat in argument #131 (legacy, geen bron). De maintainer zette het op `betwist` (edit_log 9219: "per-outlet-attributie ontbreekt").

**Neutrale zoekvraag:** *"Welke rol speelt de VVD (als regeringspartij of via de premier) als bron in de berichtgeving van de DPG-titels? En is er onderzoek dat die afhankelijkheid wel of niet vindt?"*

**Uitkomst:** ik heb geen bron gevonden die de VVD specifiek als routinebron van DPG-titels documenteert, en dus niets ingediend.

**Negatieve en niet-specifieke resultaten (alleen in dit log):**
- Thesen, Green-Pedersen & Mortensen, "From bonus to burden" (EJPR 2024, doi 10.1111/1475-6765.12670). Zij vinden in Nederlandse kranten 2000–2018 een *incumbency bonus*: regeringspartijen domineren het nieuws in 96–99% van de maanden. Daarnaast vinden ze een *incumbency burden*: de toon over regeringspartijen is negatiever. Dit gaat over alle regeringspartijen, niet over de VVD of DPG. Welke Nederlandse kranten in de steekproef zitten, heb ik niet kunnen nagaan. Het past eerder als argument op mechanisme #6 dan op deze org→org-edge, en staat daarom in het verslag.
- Er is geen Nieuwsmonitor-rapport gevonden dat per DPG-titel laat zien hoeveel aandacht de VVD krijgt.

## Zoekopdrachten, letterlijk

**Database (alleen-lezen) en API:**
- de relatie-query uit de brief voor `r.id = 129` en `r.id = 127`
- `curl /api/arguments?relation_id=129` en `?relation_id=127`
- argumenten, immuun-oordelen en citaties bij relatie 127/129
- `edit_log` voor arguments 129/131 en relations 127/129
- mechanismen met `name LIKE '%toegang%'/'%exclusie%'/'%goodwill%'/'%politic%'/'%partij%'` of `description LIKE '%toegang%'`, met de rollen van #49/#82/#84/#149
- entiteiten PVV, De Telegraaf, Geert Wilders, VVD, DPG Media
- relaties PVV/Wilders → Telegraaf en VVD → DPG
- `source_locations LIKE` de URL's van de vier nieuwe bronnen (geen hergebruik mogelijk)

**Web (WebSearch):**
1. `Nieuwsmonitor aandacht politieke partijen kranten Volkskrant AD Trouw VVD premier meest zichtbaar`
2. `Wilders De Telegraaf interview exclusief PVV relatie krant onderzoek berichtgeving`
3. `incumbency bonus Dutch newspapers coverage governing parties content analysis Netherlands`
4. `telegraaf.nl interview Geert Wilders "in gesprek met De Telegraaf"`
5. `Wilders geeft interviews alleen aan De Telegraaf mijdt andere media PVV persbeleid`
6. `"Wilders" "zegt hij tegen De Telegraaf" OR "zei hij tegen De Telegraaf" PVV`
7. `Wilders interview De Telegraaf 2023 verkiezingen PVV-leider in gesprek krant`
8. `Nieuwsmonitor verkiezingen 2021 media-aandacht partijen Rutte VVD meeste aandacht kranten de Volkskrant AD Trouw NU.nl`
9. `regeringspartijen krijgen meer aandacht in Nederlandse kranten onderzoek "incumbency bonus" Volkskrant Algemeen Dagblad Trouw`
10. `onderzoek bronnengebruik Nederlandse kranten aandeel officiële bronnen overheid politici Volkskrant AD inhoudsanalyse`
11. `"From bonus to burden" Thesen supporting information Netherlands newspapers Volkskrant NRC Telegraaf`
12. `Telegraaf hoofdredactioneel commentaar keert zich tegen Wilders PVV maart 2014 "minder Marokkanen"`

**Opgehaald (curl):**
- het Damstra & Vliegenthart-hoofdstuk (pdf, via PDFKit)
- nos.nl/artikel/2163409
- hartvannederland.nl, NVJ over Wilders: geen Telegraaf-specifiek gegeven
- dutchnews.nl 2012 "footsie": geen inhoud opgehaald
- nltimes.nl/node/83828: leeg
- welingelichtekringen.nl: 2010-interview, 2014 "campagne tegen Wilders" (opiniërend; vervangen door DutchNews als bron) en 2025 "krantje maken" (alle partijen, dus niet PVV-specifiek, niet gebruikt)
- bnnvara/joop "pvv kamerlid woedend": leeg
- PMC9702915: captcha
- Cambridge core-reader "From bonus to burden"

## Stance-balans

- **Ingediend:** 1 steun / 2 tegen / 0 context / 0 ondergraving. Alles `voorgesteld`.
- **Nieuwe bronnen:** #2530, #2531, #2532, #2533.
- **Nieuwe argumenten:** #7952, #7953, #7954.
- **Wachtrij:** doel #112 → `klaar`, doel #109 → `niets_gevonden`.

---

Ronde 1 is klaar. Van de twee bewijsdoelen leverde één nieuw bewijs op; het andere niet.

- **PVV → De Telegraaf (rel. 127):**
  - Steun (#7952): Wilders sprak in 2010 en 2017 met De Telegraaf, terwijl hij verzoeken van andere media steeds vaker en uiteindelijk structureel weigerde.
  - Tegen (#7953): van drie onderzochte kranten besteedde De Telegraaf in 2004–2017 de minste aandacht aan Wilders/PVV.
  - Tegen (#7954): in 2014 veroordeelde De Telegraaf in een redactioneel commentaar Wilders' uitspraken over Marokkanen.
  - Geen bron draagt de relatiebeschrijving "delen framing".
- **VVD → DPG Media (rel. 129):** niets gevonden dat de VVD specifiek als routinebron van DPG-titels documenteert. Dat sluit aan bij de eerdere betwisting door de maintainer.
  - Wel gevonden: een studie waaruit blijkt dat regeringspartijen in Nederlandse kranten meer aandacht krijgen, maar met een negatievere toon. Die gaat niet over de VVD of DPG specifiek, dus ik heb haar alleen in het verslag gezet.

Dit log gaat via de runner naar `missies/logs/2026-10-09_nieuws-bewijs_ronde1.md`.

De Gmail- en Google Calendar-koppelingen van claude.ai moeten nog geautoriseerd worden, via de connector-instellingen op claude.ai. Tot dan werken ze niet. Voor deze ronde waren ze niet nodig.

```

## Runner-metadata

- Exit-code: 0
- Duur: 455.9 s
- Oogst (edit_log-delta van `nieuws-bewijs`): 7
- Beëindigd: 2026-10-09T09:32:22
