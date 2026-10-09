# Onbewaakte ronde — nieuws-bewijs · ronde1 · 2026-10-07

- Brief: `missies/nieuws_bewijs_brief.md` (blob `f4945ac5b576`)
- Account: `nieuws-bewijs`
- Gestart: 2026-10-07T10:24:01

## Sessie-uitvoer

```
# Ronde-log nieuws-bewijs · ronde1 · 2026-10-07

Ik heb twee doelen geclaimd en beide afgesloten op **`klaar`**. Ik diende 1 nieuwe bron en 7 argumenten in; alles staat op `voorgesteld`. Er waren geen 409's, geen 429 en geen LinkedIn-melding (LinkedIn was niet nodig: dit is bronnenonderzoek naar redacties, geen loopbaanonderzoek).

- **Brief:** `missies/nieuws_bewijs_brief.md`, blob `f4945ac5b576`
- **Account:** `nieuws-bewijs`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `[2322]` terug. Dat argument hoort bij geen van beide doelen, dus ik hoefde niets over te slaan.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` leverde doel #75 (`relatie:145`) en doel #76 (`relatie:220`) op.

## Doel #76: `relatie:220`, RIVM → de Volkskrant (`bron_afhankelijkheid`) → **klaar**

**Wat het model beweert:** het RIVM is voor de Volkskrant een routinematige officiële bron die ook het frame levert.
- Daar pleit vóór: de Volkskrant neemt de RIVM-lijn over als gezaghebbend.
- Daar pleit tegen: de Volkskrant bevraagt het RIVM kritisch, laat andere deskundigen aan het woord of brengt eigen onthullingen.

**Bestaand argument #222** (supporting, `betwist`) heeft **geen citatie**. Maintainer `maxime` zette het op 2026-07-07 al op betwist omdat het niet te sourcen was. Er is dus geen bron om te toetsen. Ik diende **geen ondergraving** in, omdat die het bestaande oordeel alleen zou herhalen.

**Neutrale zoekvraag:** *"Hoe ging de Volkskrant tijdens en vóór de coronacrisis om met het RIVM als bron, en kwamen er andere stemmen of eigen kritische bevindingen aan bod?"*

| Bron | Argument | Stance |
|---|---|---|
| #1611 (Jop de Vrieze, "Lessen van de coronapandemie deel 2", Villamedia 2023; bestond al) | **#3943**: Klok verdedigde op 19-3-2020 in het Mediaforum van NPO Radio 1 de lijn "met één mond", omdat het RIVM erachter stond | steun |
| #1611 | **#3944**: na de stikstofkritiek had de redactie als uitgangspunt dat kritiek op het RIVM niet onweersproken gepubliceerd mocht worden | steun |
| **#2394 (nieuw)**: Volkskrant, 5-8-2020, "Vertrouwelijk RIVM-rapport: ventilatiesysteem verspreidde virus in verpleeghuis" (cluster `volkskrant`, voorgesteld `kwaliteitsjournalistiek`/`nl_systeem`) | **#3941**: de Volkskrant onthulde op basis van een vertrouwelijk RIVM-rapport dat het RIVM de ventilatierichtlijn stil had herzien | tegen |
| #1611 | **#3945**: aspect `mechanism` → `crisis_bronmonopolie` (#173) | steun (aspect) |

**Mechanisme:** de bronnen beschrijven een episode in een crisis: het pleidooi van maart 2020, de eigen onthulling in augustus 2020 en de latere terugblik van Klok. Die beschrijving past bij de definitie van #173, met precedent RIVM → NOS (rel. 676). Het stikstof-uitgangspunt van de redactie past wel bij de structurele lezing van `bron_afhankelijkheid`. Een mens beslist.

## Doel #75: `relatie:145`, RIVM → DPG Media (`bron_afhankelijkheid`) → **klaar**

**Bestaand argument #147** (supporting, `betwist`) heeft **geen citatie**. De maintainer zette het op 2026-07-07 op betwist: het SCP-onderzoek gaat over framing en niet over deze claim. Ook hier diende ik om dezelfde reden geen ondergraving in.

**Neutrale zoekvraag:** *"Hoe gingen DPG-titels (Volkskrant, AD, Trouw, Parool) in de coronacrisis om met het RIVM als bron?"*

| Bron | Argument | Stance |
|---|---|---|
| #1611 | **#3946**: de hoofdredacteur van DPG-titel de Volkskrant verdedigde op 19-3-2020 de RIVM-lijn | steun |
| #1611 | **#3947**: volgens De Vrieze koos het AD bewust voor geluiden naast OMT/RIVM (Rijpma noemt De Hond en een kritisch interview met Engel) | tegen |
| #2394 | **#3942**: de Volkskrant-onthulling over het vertrouwelijke RIVM-rapport | tegen |

**Voor de mens:** rel. 145 is een **concernrelatie**. De redactionele bronkeuze gebeurt per titel, en er bestaan al titelrelaties (220 Volkskrant, 222 AD). Het is de moeite waard om na te gaan of de concernrelatie dubbel telt. Ik heb geen relatie aangemaakt of gewijzigd.

## Zoekopdrachten, letterlijk

**Database (alleen-lezen) en API:**
- de relatie-query uit de brief, `WHERE r.id IN (145,220)`
- `curl /api/arguments?relation_id=145` en `?relation_id=220`
- `edit_log WHERE (table_name='arguments' AND record_id IN (147,222)) OR (table_name='relations' AND record_id IN (145,220))`
- alle RIVM-relaties: `WHERE s.name LIKE '%RIVM%' OR t.name LIKE '%RIVM%'`
- `/api/arguments` voor rel. 143, 144, 221, 222 en 676
- bronnen: `source_locations WHERE location LIKE '%jopdevrieze%' OR '%bdc4943d%' OR '%villamedia%corona%'`
- citaties van bron 1611
- mechanismen `crisis_bronmonopolie`, `institutioneel_gezag`, `bron_afhankelijkheid`, `expert_legitimatie` en `LIKE '%gezag%'`, plus hun relaties

**Web (WebSearch):**
1. `inhoudsanalyse coronaberichtgeving Nederlandse kranten RIVM bronnen Volkskrant AD onderzoek`
2. `Volkskrant kritisch RIVM aerosolen coronabeleid onderzoek journalistiek`
3. `"Volkskrant" lezersredacteur corona berichtgeving te weinig kritisch RIVM`
4. `Pieter Klok Volkskrant maart 2020 RIVM "één lijn" verstandig volgen`
5. `"Klok" Volkskrant "niet de juiste woorden" RIVM corona hoofdredacteur`
6. `"Langzaam verdampt de heilige status van de corona-experts" Volkskrant`
7. `Pieter Klok "één lijn" RIVM villamedia OR "de nieuwe reporter" Volkskrant corona kritiek`
8. `"als land één lijn te trekken" Klok` (extended)
9. `"Pieter Klok" coronavirus RIVM 2020 interview hoofdredacteur kritische geluiden podium`
10. `volkskrant.nl "Pieter Klok" corona verantwoording lezers RIVM kritiek "van de hoofdredactie"`
11. `onderzoek welke experts het vaakst geciteerd in Nederlandse kranten coronacrisis Van Dissel RIVM aandeel bronnen`
12. `Volkskrant RIVM kritiek mondkapjes ventilatie onthulling 2020 Keulemans`
13. `Pieter Klok hoofdredacteur Volkskrant 19 maart 2020 radio "RIVM" lijn steunen "heel instituut"` (extended)
14. `AD.nl RIVM onthulling kritiek coronacijfers fout RIVM 2020 2021 AD onderzoek`
15. `Volkskrant "volgens het RIVM" dagelijkse coronacijfers overzicht 2020 volkskrant.nl RIVM meldt`

**Opgehaald (curl/WebFetch):**
- wyniasweek.nl, "Hoe een krant wegdraait van de eigen volgzaamheid" (pdf)
- de twee Joop-artikelen "de publieke omroep is te weinig kritisch…" en "vertrouwelijk RIVM-rapport…"
- het Volkskrant-artikel `~bdc4943d` (achter de DPG-consentmuur, opgehaald met consent-cookies)
- jopdevrieze.nl, deel 2
- archive.org/wayback/available gaf een 429; dat is een externe dienst en niet onze API

Alle zes ingediende quotes heb ik **letterlijk** teruggevonden op de opgehaalde pagina's, na het samenvoegen van witruimte. De lead-zin van de Volkskrant ("Dat blijkt uit een vertrouwelijke RIVM-rapportage…") stond alleen in de meta-omschrijving. Die heb ik daarom niet als quote gebruikt.

## Negatieve resultaten (alleen in dit log)

- **Inhoudsanalyses:** ik vond geen inhoudsanalyse die per titel (Volkskrant, AD) het aandeel van het RIVM als bron meet. Er kwamen alleen EUR-scripties (Jordaans 2020, Van der Spek) en VWS-mediamonitors uit de Woo-dossiers naar boven, en die meten niet per titel hoe vaak het RIVM als bron dient. Ik heb ze niet gebruikt.
- **Primaire uitzending van Klok:** de uitzending van Spraakmakers van 19-3-2020 heb ik niet primair gevonden. Ik citeer daarom de terugblik van De Vrieze, waarin Klok zelf geïnterviewd wordt.
- **Ook niet gebruikt:**
  - Wynia's Week (Hekkens, 2020): een opinieblog en een tweedehands weergave van hetzelfde citaat.
  - containmentnu.nl, ninefornews.nl, wanttoknow.nl: activistische of complotgerelateerde sites, geen bron.
  - Het Volkskrant-stuk van 31-7-2020, "Langzaam verdampt de heilige status van de corona-experts": de primaire versie niet gevonden.
  - De zoekopdrachten naar AD-onthullingen en Volkskrant-cijferoverzichten leverden alleen andere media op (DutchNews, Hart van Nederland, NOS).
  - Rijpma's uitspraak dat "de journalistiek overwegend in de groep zat die grotendeels achter het overheidsbeleid stond" gaat over overheidsbeleid, niet over het RIVM als bron. Ik heb haar niet ingediend.
- **Niet onderzocht:** de context-artikelen van doel #75 (westnijlvirus, 2026) zijn van NOS, RTL en buitenlandse media, niet van DPG-titels. Ik heb niet gezocht hoe DPG-titels het RIVM in 2026 over het westnijlvirus brengen. Daar zit een gat voor een volgende ronde.
- **Bijvangst voor een mens:**
  - Het event-label in de context van doel #75 luidt "Negenduizend doden door westnijlvirus in Nederland", terwijl de artikelen over vier nieuwe doden gaan. Dat lijkt een fout in de nieuws-aggregator.
  - Argument #2805 citeert Klok over het RIVM, maar hangt aan rel. 464 (PvdA → Marcel van Dam). Dat lijkt verkeerd gekoppeld; ik heb er niets aan veranderd.

## Stance-balans

**3 steun / 3 tegen / 0 context / 0 ondergraving**, plus 1 mechanisme-aspect.
- rel. 220: steun #3943, #3944 · tegen #3941 · aspect #3945
- rel. 145: steun #3946 · tegen #3942, #3947

Manifest: `data/scout/bewijs-relatie-220-145.json` (bron #2394 met #3941/#3942); resultaat: `data/scout/bewijs-relatie-220-145.resultaat.json`. Argumenten #3943–#3947 citeren de bestaande bron #1611. Ik heb ze rechtstreeks via `POST /api/arguments` ingediend, omdat het manifestscript geen bestaande `source_id` kan hergebruiken; zo voorkwam ik een dubbele bron.

```

## Runner-metadata

- Exit-code: 0
- Duur: 335.7 s
- Oogst (edit_log-delta van `nieuws-bewijs`): 8
- Beëindigd: 2026-10-07T10:29:38
