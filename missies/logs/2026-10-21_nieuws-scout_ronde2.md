# Onbewaakte ronde — nieuws-scout · ronde2 · 2026-10-21

- Brief: `missies/nieuws_scout_brief.md` (blob `d8091c4ce188`)
- Account: `nieuws-scout`
- Gestart: 2026-10-21T11:42:53

## Sessie-uitvoer

```
# Nieuws-scout · ronde2 · 2026-10-21

Alle drie de doelen vielen buiten de afbakening. Ik heb niets in het model ingediend en ze afgesloten als `overgeslagen`.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `d8091c4ce188` (volledig: `d8091c4ce188a5f4b9356bf378e558834e415b37`)
- **Account:** `nieuws-scout`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []` en `via_reply: []`. Er was dus niets over te slaan, en ik heb ook geen reacties ingediend.
- **LinkedIn-rem bij de start:** `snelheidsrem.py mag zoek` gaf exit 0 en `mag profiel` ook. Daarom heb ik geclaimd met `&linkedin=1`.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` gaf drie doelen: 266, 267 en 268.

## Per doel

| doel | sleutel | uitkomst | waarom |
|---|---|---|---|
| 266 | `person:cornald-maas` | `overgeslagen` | Geen rol in het netwerk. Hij is tv-presentator en was Songfestival-commentator bij AVROTROS. Uit de context en het model blijkt geen bestuurs- of redactionele functie. Het model koppelt AVROTROS alleen aan bestuurders (Zimmerman, Nijpels, Huffnagel), niet aan presentatoren van amusement. |
| 267 | `person:gert-verhulst` | `overgeslagen` | Buitenland, geen NL-rol. Hij is Belgisch presentator en medeoprichter en aandeelhouder van Studio 100, een Belgisch bedrijf voor amusement en kinderproducties. Het heeft geen rol in Nederlandse nieuwsmedia, politiek of bestuur. De artikelen zijn boulevardberichten. |
| 268 | `person:laurent-nunez` | `overgeslagen` | Buitenland, geen NL-rol. Hij is Frans minister van Binnenlandse Zaken, en de artikelen gaan over onlusten in Frankrijk. |

Elk doel is afgesloten met een PATCH (`status: overgeslagen`, lege `resultaat`, `vervolg: null`, `entity_id: null`). De server bevestigde alle drie.

## Zoekopdrachten (letterlijk)

**Database (alleen-lezen):**
- `SELECT id,name,type,status FROM entities WHERE name LIKE '%Maas%' OR name LIKE '%Verhulst%' OR name LIKE '%Studio 100%' OR name LIKE '%Nu_ez%' OR name LIKE '%AVROTROS%' OR name LIKE '%Songfestival%' OR name LIKE '%Eurovisie%' OR name LIKE '%Jan Smit%';`
  - Geen Cornald Maas, Gert Verhulst, Studio 100 of Nuñez.
  - Wel AVROTROS (#141). De naamgenoten (L.J. Verhulst, burgemeester Ede; diverse Maas-knopen) zijn niet dezelfde personen.
- `SELECT r.id,r.relation_type,e1.name,e2.name,r.functie,r.status FROM relations r JOIN entities e1 ON e1.id=r.source_id JOIN entities e2 ON e2.id=r.target_id WHERE (r.source_id=141 OR r.target_id=141) AND (e1.type='persoon' OR e2.type='persoon');`
  - Gaf 3 rijen, alleen bestuurders en een draaideur: #386 Huffnagel, #1072 Zimmerman, #2230 Nijpels.
- `grep -n "Cornald\|Verhulst\|Nuñez\|Nunez" -r missies/logs/` vond geen eerder onderzoek naar deze personen.

**Web:**
- `WebFetch https://www.nu.nl/songfestival/6413357/cornald-maas-gaat-eurovisie-songfestival-definitief-niet-van-commentaar-voorzien.html` mislukte: "unable to fetch from www.nu.nl".
- `WebFetch https://www.rtl.nl/boulevard/artikel/5659812/gert-verhulst-reageert-op-verkoopgeruchten-studio-100-ik-kan-het-me-maar` mislukte: "unable to fetch from www.rtl.nl".
- Ik heb niet verder gezocht. De context van de nieuws-app (de rolzinnen, de titels en de soort artikelen) liet al zien dat alle drie buiten de afbakening vallen.

**LinkedIn:** geen zoekactie en geen scrape, bewust. Bij personen die we niet onderzoeken, wordt de stap niet gebruikt.

## Aangemaakt

Niets: geen bronnen, entiteiten, relaties of argumenten.

## Negatieve resultaten (alleen in dit log)

- Geen van de drie staat in het model.
- Er bleek geen Nederlandse netwerkrol uit de context: geen functie bij een nieuwsredactie, de politiek of het bestuur, en geen Nederlands media-eigendom. Ik heb daarom niets ingediend, ook geen `contextual` bijdrage.

## LinkedIn-remstatus aan het einde

Automatisch aan, actieve uren 08:00–22:00 (nu actief). Profiel: uur 0/2, dag 0/10. Zoeken: uur 0/2, dag 0/10. Volgende kans: nu.

## Stance-balans

0 steun / 0 tegen / 0 context

Er was geen rate-limit (429) en geen verlopen LinkedIn-sessie.

```

## Runner-metadata

- Exit-code: 0
- Duur: 126.3 s
- Oogst (edit_log-delta van `nieuws-scout`): 0
- Beëindigd: 2026-10-21T11:44:59
