# Onbewaakte ronde — nieuws-bewijs · ronde1 · 2026-10-06

- Brief: `missies/nieuws_bewijs_brief.md` (blob `73e8fae17985`)
- Account: `nieuws-bewijs`
- Gestart: 2026-10-06T00:50:44

## Sessie-uitvoer

```
# Ronde-log nieuws-bewijs · ronde1 · 2026-10-06

Doel #74 (PBL → NOS, `relatie:1564`) is afgerond op **`klaar`**. Ik diende 6 bronnen en 8 argumenten in; alles staat op `voorgesteld` tot een mens het beoordeelt. Er was maar één open doel. Er kwamen geen 409, 429 of LinkedIn-meldingen.

- **Brief:** `missies/nieuws_bewijs_brief.md`, blob `73e8fae17985`
- **Account:** `nieuws-bewijs`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf een lege lijst; ik hoefde niets over te slaan.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` leverde dit ene doel op.

## Doel #74: `relatie:1564`, PBL → NOS (`expert_framing`) → **klaar**

**Wat het model beweert:** relatie 1564 (`beinvloeding`, goedgekeurd, invloed 0,05) zegt dat de NOS de analyses van het PBL als gezaghebbend en neutraal brengt.
- Daar pleit vóór: de NOS brengt PBL-uitkomsten herhaaldelijk zonder tegenstem.
- Daar pleit tegen: de NOS bevraagt of corrigeert het PBL, of laat critici aan het woord.

**Bestaand argument #2322** (supporting, `ongecontroleerd`) heeft één citatie, uit bron #1291: het persbericht van het PBL zelf over de KEV 2024.
- Het citaat staat er **letterlijk** in; ik haalde de pagina op met curl en vergeleek de tekst exact.
- Maar de bron laat alleen zien wat het PBL zegt, niet hoe de NOS het bracht. Daarom diende ik **ondergraving #3912** in.

**Neutrale zoekvraag:** *"Hoe bracht de NOS de Klimaat- en Energieverkenningen van het PBL van 2019 tot 2026, en kwam er een tegenstem aan het woord?"*

### Zoekopdrachten, letterlijk

**Database:**
- `SELECT r.id, s.name, t.name, r.relation_type, r.status, m.id, m.name, m.description, r.description, r.certainty, r.influence … WHERE r.id = 1564`
- `curl /api/arguments?relation_id=1564`
- mechanismen: `WHERE name IN ('expert_framing','expert_legitimatie','bron_afhankelijkheid',…) OR name LIKE '%expert%' OR name LIKE '%bron%'`
- PBL-, CPB- en planbureau-relaties: `WHERE s.name LIKE '%Planbureau%' OR s.name LIKE '%CPB%' …`
- bestaande NOS-bronnen: `WHERE sl.location LIKE '%nos.nl%' AND (title LIKE '%PBL%' OR '%klimaat%' OR '%Planbureau%')`
- `SELECT … FROM mechanisms WHERE name='institutioneel_gezag'`
- argumenten op rel. 1986, 146 en 1515 (de precedenten)
- `source_type`-telling en het NOS-`cluster_key`

**Web:**
- WebSearch (nos.nl): `NOS Klimaat- en Energieverkenning PBL 2024 klimaatdoel 2030`
- WebSearch (nos.nl): `NOS PBL Klimaat- en Energieverkenning 2023 klimaatdoel`
- WebSearch: `kritiek op PBL klimaatverkenning rekenmodel NOS`
- WebSearch (nos.nl): `kritiek op Planbureau voor de Leefomgeving berekening`
- WebSearch: `PBL doorrekening klimaatakkoord kritiek wetenschappers "planbureau" onterecht`
- WebSearch: `inhoudsanalyse bronnengebruik NOS planbureaus deskundigen klimaatberichtgeving onderzoek`

**Opgehaald met curl:**
- het PBL-persbericht (bron #1291)
- NOS-artikelen 2541919, 2541956, 2444480, 2491051, 2582721, 2630979, 2272706, 2322799 en 2272779
- `over.nos.nl/nieuws/over-onze-klimaatberichtgeving/`
- `omroepombudsman.nl/…/uitspraak-onderzoek-klimaatberichtgeving-nos-nieuws`

Elke ingediende quote heb ik verbatim gecontroleerd op de opgehaalde pagina, na het samenvoegen van witruimte.

### Vondsten en ingediende id's

Alle zes NOS-bronnen vallen in cluster `nos`. Voorgesteld: `kwaliteitsjournalistiek` / `nl_systeem`.

| Bron | Datum | Argument | Stance |
|---|---|---|---|
| #2375 (NOS 2541919, KEV 2024) | 2024-10-24 | #3913: PBL-berekening als kop, PBL/Hekkert enige deskundige | steun |
| #2376 (NOS 2582721, KEV 2025) | 2025-09-16 | #3914: NOS toetst de ramingen van het ministerie aan het PBL-cijfer ("Nu blijkt …") | steun |
| #2377 (NOS 2630979, rapport 2026) | 2026-09-14 | #3915: opent met PBL-conclusies, naast het PBL alleen de minister aan het woord | steun |
| #2378 (NOS 2272706) | 2019-02-20 | #3916: NOS brengt kritiek van CDA en GL op de PBL-rekenmodellen | tegen |
| #2379 (NOS 2322799) | 2020-02-13 | #3917: NOS brengt de Aedes-kritiek op de PBL-kostenberekening | tegen |
| #2380 (NOS 2444480) | 2022-09-13 | #3918: NOS neemt de kanttekening van een kabinetsbron over de PBL-berekening op | tegen |
| (#2375) | — | #3919: aspect `mechanism` → `institutioneel_gezag` (#86) | steun (aspect) |
| (#1291) | — | #3912: ondergraving op #2322 (de bron draagt de NOS-claim niet) | ondergraving |

**Mechanisme:** `expert_framing` gaat over denktanks die sponsors betalen. Het PBL is een overheidsplanbureau, en `institutioneel_gezag` past op de definitie. Het precedent is CPB → NOS, rel. 1986. Een mens beslist; ik heb geen relatie aangemaakt of gewijzigd.

**Status:** de PATCH op `/api/nieuws/doelen/74` gaf `klaar` terug, met `source_ids` 2375–2380 en `argument_ids` 3912–3919.

## Negatieve resultaten (alleen in dit log)

- **NOS-verantwoording:** `over.nos.nl/…/over-onze-klimaatberichtgeving/` gaat over de keuze van klimaatwetenschappers (KNMI, IPCC). Het PBL komt er niet in voor; niet gebruikt.
- **Ombudsman:** de uitspraak over de klimaatberichtgeving van de NOS (2019 en 2021) noemt het PBL en planbureaus niet; niet gebruikt.
- **Inhoudsanalyses:** geen inhoudsanalyse gevonden naar hoe vaak de NOS het PBL citeert. Er was alleen een scriptie over klimaatsceptici in de krant, en een studeersnel-document dat geen bron is.
- **Ook niet gebruikt:**
  - NOS 2541956 (24-10-2024, reacties): veel stemmen over het beleid, maar niemand betwist het PBL-cijfer zelf. Het past niet zuiver in één stance.
  - NOS 2491051 (KEV 2023): hetzelfde patroon als bij #3913–#3915 en hetzelfde cluster.
  - NOS 2272779 (2019): overlapt met #3916.
  - climategate.nl en Sargasso: opinieblogs, geen bron voor wat de NOS deed.

## Stance-balans

**3 steun / 3 tegen / 0 context / 1 ondergraving**, plus 1 mechanisme-aspect.

Manifest: `data/scout/bewijs-relatie-1564.json`; resultaat: `data/scout/bewijs-relatie-1564.resultaat.json`.

```

## Runner-metadata

- Exit-code: 0
- Duur: 213.7 s
- Oogst (edit_log-delta van `nieuws-bewijs`): 14
- Beëindigd: 2026-10-06T00:54:17
