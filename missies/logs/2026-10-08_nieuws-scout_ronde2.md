# Onbewaakte ronde — nieuws-scout · ronde2 · 2026-10-08

- Brief: `missies/nieuws_scout_brief.md` (blob `3681aaefcec1`)
- Account: `nieuws-scout`
- Gestart: 2026-10-08T11:10:05

## Sessie-uitvoer

```
# nieuws-scout, ronde 2 (2026-10-08)

Ik heb drie doelen geclaimd. Twee staan nu op `klaar`: FVD (#92) en Aran Bade (#93). Apple (#91) staat op `overgeslagen`. Ik heb 4 bronnen, 3 entiteiten, 4 relaties (alle met een mechanisme) en 4 steunende argumenten ingediend, allemaal `voorgesteld`. Er kwam geen 429, geen 409 en geen melding dat de LinkedIn-sessie verlopen was. Ik heb geen statussen of klassen in het model aangeraakt; alleen de status van de drie wachtrij-doelen heb ik afgesloten. Deze uitvoer is het log: de runner zet hem in `missies/logs/2026-10-08_nieuws-scout_ronde2.md`.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `3681aaefcec1`. `git hash-object` gaf hetzelfde.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []` en `via_reply: []`. Ik heb op geen enkel bestaand argument gereageerd.
- **LinkedIn-rem:** `mag zoek` en `mag profiel` gaven allebei exit 0. Aan het begin én aan het eind stonden profiel en zoek op uur 0/2 en dag 0/10. Ik heb LinkedIn niet gebruikt, dus er kwam geen exit 75 of 76.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` gaf drie doelen: #91 `org:apple`, #92 `org:fvd` en #93 `person:aran-bade`.

## Zoekopdrachten in de database (alleen-lezen, letterlijk)
1. `SELECT id,name,type,status,primary_role_id FROM entities WHERE name LIKE '%Apple%' OR name LIKE '%Forum voor Democratie%' OR name LIKE '%FVD%' OR name LIKE '%FvD%' OR name LIKE '%Bade%' OR name LIKE '%RTL Boulevard%' OR name LIKE '%Shownieuws%' OR name LIKE '%SBS%' OR name LIKE 'RTL%';`
   - Apple, Aran Bade en RTL Boulevard staan niet in het model. FVD is #218, RTL Nederland #8.
2. `SELECT r.id,s.name,t.name,r.relation_type,r.mechanism_id,r.status FROM relations r … WHERE (r.source_id=218 OR r.target_id=218)`
   - FVD heeft 4 goedgekeurde verbanden. Er staan nog 10 partijbanden van Kamerleden voorgesteld, ingediend door `register-import`.
3. `SELECT id,name,… FROM entities WHERE name LIKE '%Baudet%' OR name LIKE '%de Vos%' OR name LIKE '%Lidewij%'`
   - Thierry Baudet staat erin (#665), maar zonder partijband met FVD. Lidewij de Vos staat er niet in.
4. `SELECT r.id,… WHERE r.source_id=665 OR r.target_id=665`
   - Baudet heeft alleen flak- en etiketteringsrelaties.
5. `SELECT … FROM entities WHERE name LIKE '%Vos%' OR name LIKE '%Frederik Jansen%' OR name LIKE '%Oetelaar%'`, en de relaties van Al Biyati.
   - Lidewij de Vos staat niet in het model, ook niet in registerschrijfwijze.
6. Het register `data/registers/tk/tk_2026-10-08.json` doorzocht op Biyati, Vos en Baudet.
   - Al Biyati heeft een zetel `Van 2026-09-01`. De Vos en Baudet hebben nu geen Kamerzetel.
7. Precedenten bekeken:
   - Partijbanden met mechanisme 92 (`partijlijn`) en 163 (`partijbinding`, rel. 2280).
   - De programma's RTL Tonight en RTL Late Night: hoe ze aan RTL Nederland hangen (eigendom, mechanisme 1, rel. 2001/2002) en met welke bron.
   - Journalist-precedent: RTL Nieuws → persoon, `dienstverband`, mechanisme 192.
8. Bestaande bronnen opgezocht op fvd.nl, Parlement.com, aranbade.nl en adalliance.
   - Geen bruikbare bron om te hergebruiken.

## Zoekopdrachten op het web, en wat ik ophaalde
- WebSearch `Thierry Baudet partijleider Forum voor Democratie parlement.com`
  - Gaf alleen oude NOS-stukken uit 2020, die ik niet gebruikte.
- WebSearch `Aran Bade verslaggever RTL Boulevard`
- WebSearch `Lidewij de Vos verlof vervanging Iem Al Biyati Tweede Kamer 2026`
- WebSearch `"Aran Bade" "RTL Boulevard" verslaggever`
- WebSearch `RTL Nederland persbericht "RTL Boulevard" programma RTL 4 2025`
- WebFetch en curl op deze pagina's:
  - `fvd.nl`
  - `fvd.nl/mensen/bestuur`: Baudet staat er als "Partijvoorzitter".
  - `fvd.nl/mensen/tweede-kamer`: De Vos staat er als "Fractievoorzitter Tweede Kamer".
  - `fvd.nl/mensen/thierry-baudet`
  - de Parlement.com-biografie van De Vos
  - het Parlement.com-nieuwsbericht van augustus 2026 over Dekker en Al Biyati
- `rtl.nl` (artikel en video): kon ik niet lezen, want de pagina's worden met JavaScript opgebouwd.
- tvgids.nl, twee artikelen: noemen het programma niet expliciet, dus niet gebruikt.
- nl.wikipedia, alleen als vindplaats. Via de voetnoten kwam ik bij `aranbade.nl/bio/` en een nu.nl-stuk; dat laatste was leeg.
- PDF `adalliance.nl/…/RTL-4-zendersheet-2025.pdf`.
- **Citaatcontrole:** alle vier de citaten heb ik nagelopen met `bronchecker.haal_url` en `zoek_citaat`, dus met dezelfde normalisatie als de bronchecker. Alle vier vond hij exact terug.

## Per doel
- **#91 Apple → overgeslagen.** Apple is een buitenlands bedrijf zonder rol in het Nederlandse netwerk. Het artikel in de context gaat over de veiling van een Apple-1. Ik heb niets ingediend.
- **#92 FVD → klaar** (entity_id 218, bestond al)
  - bron #2463: fvd.nl, bestuurspagina van Baudet
  - bron #2464: Parlement.com, biografie van De Vos
  - relatie #6150: FVD (#218) → Thierry Baudet (#665), `lidmaatschap`, mechanisme 163 (`partijbinding`). Hij is partijvoorzitter en heeft geen Kamerzetel.
  - argument #7860 (steun), citaat: "Thierry Baudet Partijvoorzitter"
  - entiteit #3923: Lidewij de Vos, type persoon, rol 33 (`politicus`)
  - relatie #6151: FVD → Lidewij de Vos, `lidmaatschap`, mechanisme 92 (`partijlijn`)
  - argument #7861 (steun), citaat: "politiek leider FVD, vanaf 12 januari 2026"
  - Let op: De Vos zit nu niet in de registerimport van de Tweede Kamer, omdat Al Biyati haar tijdelijk vervangt. Komt ze terug in het register, dan kan de import een tweede knoop voor haar maken ("L.G. de Vos …"). Die twee knopen moeten dan samengevoegd worden. De reden van haar afwezigheid heb ik als privézaak bewust niet vastgelegd.
- **#93 Aran Bade → klaar** (entity_id 3925)
  - bron #2465: aranbade.nl/bio. Die is zelf-gerapporteerd, daarom voorgesteld als `grijs`.
  - bron #2466: RTL 4-zendersheet 2025 van Ad Alliance
  - entiteit #3924: RTL Boulevard, type mediaorganisatie, rol 34 (`redactie`)
  - entiteit #3925: Aran Bade, type persoon, rol 26 (`journalist`)
  - relatie #6152: RTL Nederland (#8) → RTL Boulevard, `eigendom`, mechanisme 1. Dat volgt het precedent van RTL Tonight.
  - argument #7862 (steun), citaat: "De vooravond met ‘Editie NL’, ‘RTL Boulevard’, ‘RTL Nieuws & Weer’ en ‘Goede Tijden, Slechte Tijden’ staat als een huis en is altijd actueel."
  - relatie #6153: RTL Boulevard → Aran Bade, `dienstverband`, mechanisme 192
  - argument #7863 (steun), citaat: "werkzaam als entertainment verslaggever bij het programma RTL Boulevard (RTL4)"
  - Zwakke plek: de zendersheet noemt RTL Boulevard op RTL 4, maar zegt niet met zoveel woorden dat RTL 4 van RTL Nederland is. Het precedent van RTL Tonight leunt op hetzelfde soort bron.
- **LinkedIn:** voor De Vos en Bade heb ik het bewust overgeslagen. Parlement.com en de eigen biografie dekken hun publieke rol al.

Alle drie de PATCH-verzoeken op de doelen gaven 200. De manifesten en resultaatbestanden staan in `data/scout/nieuws-org-fvd{,.resultaat}.json` en `data/scout/nieuws-person-aran-bade{,.resultaat}.json`.

## Negatieve resultaten (alleen in dit log)
- Op `rtl.nl` was niets te lezen, omdat de pagina's met JavaScript worden opgebouwd.
- Ik vond geen persbericht van RTL Nederland dat RTL Boulevard expliciet als programma van RTL Nederland noemt.
- De twee tvgids.nl-artikelen noemen het programma van Bade niet expliciet.
- Op parlement.com vond ik geen biografie van Baudet: het geraden adres gaf 404.
- `fvd.nl/mensen/bestuur` noemt Frederik Jansen "Tweede Kamerlid voor FVD", maar hij staat niet bij de zetels in het register. Dat valt buiten dit doel en heb ik niet verder uitgezocht.
- De bio op fvd.nl meldt nog "Sinds 2017 is hij fractievoorzitter". Die zin is verouderd en heb ik niet gebruikt.

## Stance-balans
4 steun, 0 tegen, 0 context.

**Noot voor de eigenaar:** de koppelingen met Gmail en Google Calendar op claude.ai zijn niet geautoriseerd. Deze missie had ze niet nodig. Wil je ze gebruiken, zet ze dan aan via de connector-instellingen op claude.ai.

Bronnen:
- [fvd.nl — Thierry Baudet (bestuur)](https://www.fvd.nl/mensen/thierry-baudet)
- [fvd.nl — Bestuur](https://www.fvd.nl/mensen/bestuur)
- [fvd.nl — Tweede Kamer](https://www.fvd.nl/mensen/tweede-kamer)
- [Parlement.com — L.G. (Lidewij) de Vos](https://www.parlement.com/id/vmjxmd233yqw/biografie/l_g_lidewij_de_vos)
- [Parlement.com — Ralf Dekker tijdelijk fractievoorzitter FVD en Iem al Biyati vervangt tijdelijk De Vos](https://www.parlement.com/nieuws/202608/ralf-dekker-tijdelijk-fractievoorzitter-fvd-en-iem-al-biyati-vervangt-tijdelijk-de)
- [aranbade.nl — Biografie](https://www.aranbade.nl/bio/)
- [Ad Alliance — RTL 4 zendersheet 2025](https://adalliance.nl/wp-content/uploads/RTL-4-zendersheet-2025.pdf)
- [TVgids.nl — Aran Bade onthult… (niet gebruikt)](https://www.tvgids.nl/nieuws/reality/aran-bade-onthult-makers-b-and-b-vol-liefde-pesten-deelnemers-met-mismatches)

```

## Runner-metadata

- Exit-code: 0
- Duur: 368.9 s
- Oogst (edit_log-delta van `nieuws-scout`): 15
- Beëindigd: 2026-10-08T11:16:14
