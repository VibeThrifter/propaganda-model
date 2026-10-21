# nieuws-scout — ronde1 — 2026-10-19

- **Brief:** `missies/nieuws_scout_brief.md`, blob-hash `3a6cca5f46b6` (geverifieerd: `git hash-object` → `3a6cca5f46b6fb3b…`)
- **Account:** `nieuws-scout`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` → `gereageerd_op: []`, `via_reply: []`. Er zijn geen reacties ingediend, dus geen overlap.
- **LinkedIn-rem bij de start:** `snelheidsrem.py mag zoek` → exit 0, `mag profiel` → exit 0. Ik claimde met `&linkedin=1`.
- **LinkedIn-rem aan het eind** (`snelheidsrem.py status`): profiel uur 0/2, dag 0/10; zoek uur 0/2, dag 0/10. Ik heb LinkedIn niet gebruikt.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` → doelen 246, 143, 124.

## Doel 246 — `org:nec` (NEC) → `overgeslagen`

- Uit de context: drie sportartikelen (RTL Nieuws, Trouw, NU.nl) over wedstrijden in de Europa League en de Eredivisie. Er staan geen organisaties of rolzinnen in.
- NEC is een betaaldvoetbalclub en heeft geen rol in het netwerk (brief § "Wie wel, wie nooit"). Ik heb niets ingediend.
- DB-zoekopdracht (alleen-lezen): `select id,name,type,status,primary_role_id from entities where name like '%Kortzorg%' or name like '%Kassa%' or name like '%BNNVARA%' or name like '%BNN%VARA%' or name like '%NEC%Nijmegen%' or name like '%Insoumise%' or name like '%Mélenchon%' or name like 'NEC%' or name like '%LFI%';` → geen NEC-knoop.

## Doel 143 — `org:lfi` (LFI) → `overgeslagen`

- LFI is La France Insoumise, een Franse partij (de rolzin noemt Jean-Luc Mélenchon). De artikelen gaan over Franse scholierenprotesten.
- Brief: "buitenland, geen NL-rol". Ik heb niets ingediend. Dezelfde DB-zoekopdracht als hierboven → geen LFI- of Mélenchon-knoop.

## Doel 124 — `person:amber-kortzorg` (Amber Kortzorg) → `klaar`

**Identiteit en rol:** presentator bij BNNVARA. Ze presenteert sinds 2017 in Kassa (rubriek Belbus) en is sinds januari 2020 vaste presentator. De artikelen gaan over het einde van Kassa op tv en de online doorstart.

**DB-zoekopdrachten (alleen-lezen):**
- De entities-zoekopdracht hierboven → BNNVARA #139, Kassa (consumentenprogramma) #574, Ledenraad BNNVARA #1111. Er is geen Kortzorg-knoop.
- `select r.id,... from relations r ... where (r.source_id in (574) or r.target_id in (574));` → alleen rel. 1117 BNNVARA → Kassa (`mediaplatform`, omroepsignatuur).
- Precedenten voor presentatoren: `select ... where (es.type='persoon' or et.type='persoon') and (r.functie like '%presentat%' or r.description like '%presentat%') limit 25;` → het patroon is persoon → programma, `personeel`, `draaideurconstructie` (Renze Klamer → RTL Tonight, Wilfred Genee → Vandaag Inside, Herman van der Zandt → NOS).
- `select id,name from mechanisms where name in ('draaideurconstructie','dienstverband'); select id,name from roles where name in (...)` → mechanisme 18 en rol `journalist` 26. Rol 26 heeft ook de precedenten Klamer, Genee en Van der Zandt.

**Webzoekopdrachten:**
1. `Amber Kortzorg presentatrice Kassa sinds BNNVARA` → leverde de aankondiging van BNNVARA op.
2. `Amber Kortzorg presentator Op1 BNNVARA presentatieduo` → leverde Hart van Nederland (21-06-2023) op.

**Opgehaalde pagina's** (curl, citaat letterlijk teruggevonden):
- https://www.bnnvara.nl/kassa/artikelen/amber-kortzorg-wordt-de-nieuwe-presentator-van-kassa (05-12-2019)
- https://www.bnnvara.nl/seizoenspresentatie2020/npoeen (Kortzorg wordt er niet genoemd)
- https://www.hartvannederland.nl/entertainment/artikelen/talkshow-op1-stopt-vanwege-verschil-van-inzicht

**LinkedIn:** bewust overgeslagen. De werkgever (BNNVARA) beschrijft de functie zelf in een primaire bron. De doelvraag is de huidige publieke rol, en die is daarmee gedekt; een scrape zou alleen rem-budget kosten.

**Ingediend** (manifest `data/scout/nieuws-person-amber-kortzorg.json`, alles `voorgesteld`):
- Bron #3254: "Amber Kortzorg wordt de nieuwe presentator van Kassa" (BNNVARA, 2019-12-05, url-locator; voorgesteld: institutioneel, nl_systeem).
- Entiteit #4944: Amber Kortzorg (persoon, rol-suggestie journalist 26).
- Relatie #8492: Amber Kortzorg → Kassa (consumentenprogramma) #574, `personeel`, mechanisme 18 `draaideurconstructie`, functie "presentator", `active_from` 2017. Het jaartal staat in het citaat.
  - Argument #11299 (steun): "Amber Kortzorg presenteert sinds 2017 in het BNNVARA-programma Kassa, eerst als presentator van de rubriek Belbus." Citaat: "Amber Kortzorg is sinds 2017 in Kassa te zien als presentator van de Belbus."
  - Argument #11300 (steun): "Amber Kortzorg is per januari 2020 de vaste presentator van Kassa geworden, als opvolger van Brecht van Hulten." Citaat: "Amber Kortzorg wordt per januari 2020 de nieuwe presentator van Kassa. Vanaf het nieuwe jaar vervangt ze Brecht van Hulten, die het programma de afgelopen negen jaar presenteerde."
- Er was geen 409 en geen 400.

**Negatieve resultaten** (staan alleen in dit log):
- Op1: volgens Hart van Nederland (21-06-2023) presenteerde Kortzorg Op1 op vrijdag namens BNNVARA, samen met Natasja Gibbs. BNNVARA stopte per 1 augustus 2023 met Op1. Het begin van háár Op1-presentatie staat in geen enkele gevonden bron ("sinds begin 2020" gaat over het programma, niet over haar). Het einde volgt alleen afgeleid uit het vertrek van BNNVARA. Ik heb deze band daarom niet ingediend. Het is een mogelijk vervolg voor een latere ronde, met een bron die haar begin noemt.
- Kassa stopt op 5 december 2026 als wekelijks tv-programma en gaat online verder (VARAgids, via de zoekresultaten). De band loopt dus nog en krijgt geen `active_until`.
- Seizoenspresentatie 2020 van BNNVARA: Kortzorg wordt niet genoemd.

## Stance-balans van de ronde

2 steun / 0 tegen / 0 context.

## Afsluiting

- PATCH 246 → `overgeslagen`; 143 → `overgeslagen`; 124 → `klaar` (entity_id 4944, resultaat {entity 4944, relation 8492, source 3254, arguments 11299, 11300}, vervolg null).
- Geen 429, geen LinkedIn-sessiemelding, geen rem-weigering.
