# Onbewaakte ronde — aanklager-agent · ronde1 · 2026-10-20

- Brief: `missies/aanklager_brief.md` (blob `b985acb45edc`)
- Account: `aanklager-agent`
- Gestart: 2026-10-20T08:04:40

## Sessie-uitvoer

```
```

## Rondeverslag (aanklager-agent, door de sessie zelf geschreven)

- Brief-blob-hash: `b985acb45edc`
- Voorregel: `GET /api/agent/reeds_gereageerd` (08:05) → 79 id's; geen van de behandelde argumenten stond erin.
- Werkvoorraad: `python3 scripts/automatische_beoordeling.py --open-a2` (08:05) → 154 argumenten, waarvan 5 van mezelf (10365, 9741, 9740, 7949, 7840 — overgeslagen, geen zelf-certificering). Gekozen: de 12 oudste (aangemaakt 2026-10-16 10:17, het dichtst bij de opruimtermijn van 14 dagen).

### Zoekopdrachten (letterlijk, met tijdstip)

| tijd | soort | opdracht |
|---|---|---|
| 08:05 | db | `--open-a2`, gesorteerd op `created_at` |
| 08:05 | db | `select a.id, a.claim, … from arguments a join relations r … where a.id in (11211,11209,11205,11204,11202,11201,11197,11193,11191,11189,11187,11185)` |
| 08:05 | db | `select c.argument_id, c.quote, c.methode, s.id, s.title, (locaties) from citations c join sources s … where c.argument_id in (…)` |
| 08:05 | web | download `https://www.bellingcat.com/app/uploads/2022/05/Bellingcat-Annual-Accounts-2021-pw.pdf` en `…/2021/05/Bellingcat-Annual-Accounts-2020-1.pdf`, tekst via macOS PDFKit |
| 08:06 | lokaal | `grep "Democratie en Media"` (2021), `grep -i "rausing\|Adessium"`, `grep "Income from other"` (2020), `grep "2021 – 2023\|1.000.000"`, `grep "Limelight"` (2021) |
| 08:07 | web | WebSearch: `Stem voor Nederland Open Society Foundations 200.000 euro Oekraïne-referendum geld teruggestort OR afgezien` |
| 08:07 | web | WebSearch: `Bits of Freedom Luminate funding 2022 2023 Litigating Big Tech` |
| 08:08 | web | WebFetch `https://2022.bitsoffreedom.nl/finances` (alle zinnen met Luminate) |

### Per claim

| arg | doel | stance | route | resultaat |
|---|---|---|---|---|
| 11185 | rel 8476 OSF → COC Nederland | supporting | certificaat `overleefd` | citaat uit OSF-grantdatabase (A1-geverifieerd); geen tegenbron |
| 11187 | rel 8477 OSF → Stem voor Nederland | supporting | certificaat `overleefd` | NOS bevestigt; gezocht naar teruggave/afzien: niets. Kanttekening: mechanisme `externe_mediafinanciering` past slecht (campagnestichting, geen medium) — zaak van de mechanisme-indeling, geen aanval op dit argument |
| 11189 | rel 8478 Sigrid Rausing Trust → Bellingcat | supporting | certificaat `overleefd` | jaarrekening 2020 noot 15 zelf gelezen: SRT onder "Income from other non-profit organizations", Actuals 2020 |
| 11191 | rel 8479 Limelight → Bellingcat | supporting | certificaat `overleefd` | jaarrekening 2021 zelf gelezen: 60.000 onder "Grants received in advance" |
| 11193 | rel 8480 Stichting Democratie en Media → Bellingcat | supporting | certificaat `overleefd` | jaarrekening 2021 noot 12 zelf gelezen: "Obligations current projects", restricted funds; kop staat in de bron, niet in het citaat — geen dekkingsgat |
| 11197 | rel 8481 Luminate → EDRi | supporting | certificaat `overleefd` | EDRi-financieringspagina; geen tegenbron |
| 11201 | rel 8403 OSF → Bellingcat | supporting | certificaat `overleefd` | jaarrekening 2019 niet zelf geopend; steunt op het A1-geverifieerde citaat; geen tegenbron |
| 11202 | rel 2066 Postcode Loterij → Bellingcat | supporting | certificaat `overleefd` | jaarrekening 2020 noot 14 (zelf gelezen) zegt hetzelfde: 500.000 voor 2019–2020 |
| 11204 | rel 2066 | supporting | certificaat `overleefd` | jaarrekening 2021 zelf gelezen (r. 511): toezegging 1.000.000 voor 2021–2023 |
| 11205 | rel 2066 | supporting | certificaat `overleefd` | jaarrekening 2024 niet zelf geopend; claim zegt "ontving bericht", geen sprong naar betaling |
| 11209 | rel 8410 Luminate → Bits of Freedom | supporting | certificaat `overleefd` | BoF-jaarverslag 2022 nagelezen. Kanttekening: rel. 8410 heeft `active_from` 2024, deze bron toont financiering in 2022 (begin te laat; de datumzoeker overschrijft geen gevuld veld — voor de eigenaar) |
| 11211 | rel 751 OSF → EDRi | supporting | certificaat `overleefd` | EDRi-financieringspagina; kanttekening: rel. 751 heeft geen `active_from` |

Aangemaakt: geen bronnen, entiteiten, relaties of argumenten; 12 certificaten (`immuun_oordelen`, fase tegenspraak) op de argumenten hierboven.

### Negatieve resultaten (alleen hier)

- Geen bericht gevonden dat Stem voor Nederland de 200.000 euro van OSF terugstortte of weigerde.
- Geen tegenbron voor de Luminate-financiering van Bits of Freedom; de websearch vond Luminate's eigen grantdatabase niet, het BoF-jaarverslag 2022 zelf draagt de claim.
- Voor de overige tien: de bron (jaarrekening, funderspagina, grantdatabase) is het eigen document van gever of ontvanger; geen tegenbron, geen inferentiegat.

### Stance-balans

0 weerleggingen / 0 ondergravingen / 12 `overleefd` / 0 `onbeslist` — 0 steun, 0 tegen, 0 context ingediend.

Dit is een milde ronde, en dat hoort zo vermeld: de 12 oudste waren allemaal enkelvoudige financieringsfeiten uit het eigen jaarverslag of de eigen funderslijst van de partij, zonder duiding of invloedsbewering. Daar viel niets aan te vallen. De volgende ronde moet de inferentie-zwaardere items aanpakken: theorie-argumenten 11245–11251 en 11413, en 11241 (doel van het NATO Public Forum).
Ik heb deze ronde de 12 oudste argumenten op de A2-lijst een tegenspraak-certificaat gegeven. Alle 12 kregen `overleefd`; ik plaatste geen weerleggingen of ondergravingen.

- **Werkvoorraad:** op de lijst stonden 154 argumenten. Vijf daarvan waren van mezelf; die heb ik overgeslagen. Uit de voorregel kwamen 79 id's, en geen van de behandelde argumenten stond erin. Ik nam de 12 die op 2026-10-16 binnenkwamen, omdat die het dichtst bij de opruimtermijn van 14 dagen zitten.
- **Wat ik naliep:** het waren allemaal losse financieringsfeiten, elk uit het eigen document van gever of ontvanger:
  - de jaarrekeningen van Bellingcat;
  - de financieringspagina van EDRi;
  - het jaarverslag 2022 van Bits of Freedom;
  - de grantdatabase van de Open Society Foundations (OSF);
  - een NOS-artikel over OSF en Stem voor Nederland.

  De jaarrekeningen 2020 en 2021 van Bellingcat heb ik zelf gelezen. Ze dragen de beweerde posten, ook waar de kop van een post niet in het citaat staat (#11193). Twee claims zocht ik op het web na: of Stem voor Nederland het OSF-geld terugstortte, en of er tegenbewijs is voor de Luminate-financiering van Bits of Freedom. Ik vond voor geen van beide een tegenbron.
- **Niet zelf nagelezen:** voor #11201 (jaarrekening 2019) en #11205 (jaarrekening 2024) heb ik het document niet geopend. Daar steun ik op het citaat dat de bronchecker al op `klopt` zette. Het staat zo in het log.
- **Drie punten voor de eigenaar** (staan in de certificaten en het log, het zijn geen aanvallen op deze argumenten):
  - Rel. 8410 (Luminate → Bits of Freedom) heeft `active_from` 2024, maar de bron toont financiering al in 2022. De datumzoeker overschrijft geen gevuld veld, dus dit moet met de hand.
  - Rel. 8477 (OSF → Stem voor Nederland) heeft het mechanisme `externe_mediafinanciering`, terwijl Stem voor Nederland een campagnestichting is en geen medium.
  - Rel. 751 (OSF → EDRi) heeft geen `active_from`.
- **Stance-balans:** 0 steun, 0 tegen, 0 context ingediend. Dat is een milde ronde, en het log zegt dat ook. Deze feiten boden geen inferentie om aan te vallen. De volgende ronde zou de items met meer redenering moeten nemen: de theorie-argumenten #11245–11251 en #11413, en #11241.

Er kwam geen 429 en LinkedIn heb ik niet gebruikt. Het log staat in `missies/logs/2026-10-20_aanklager-agent_ronde1.md`.

```

## Runner-metadata

- Exit-code: 0
- Duur: 188.5 s
- Oogst (edit_log-delta van `aanklager-agent`): 12
- Beëindigd: 2026-10-20T08:07:48
