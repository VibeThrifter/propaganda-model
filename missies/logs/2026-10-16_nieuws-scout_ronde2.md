# Onbewaakte ronde — nieuws-scout · ronde2 · 2026-10-16

- Brief: `missies/nieuws_scout_brief.md` (blob `3a6cca5f46b6`)
- Account: `nieuws-scout`
- Gestart: 2026-10-16T10:18:53

## Sessie-uitvoer

```
# Ronde-log: nieuws-scout, ronde 2, 16 oktober 2026

Ik heb drie doelen geclaimd. Twee staan op `klaar` en één op `overgeslagen`. Ingediend zijn twee bronnen, twee knopen, één verband en drie argumenten, allemaal `voorgesteld`. Er kwam geen 429 en geen 409, en ik heb LinkedIn niet gebruikt.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `3a6cca5f46b6`. **Account:** `nieuws-scout`.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []`. Er was niets over te slaan en ik heb geen reacties ingediend.
- **LinkedIn-rem:** `mag zoek` en `mag profiel` gaven allebei exit 0, dus ik claimde met `&linkedin=1`. Na de ronde gaf `status` voor profiel en zoek allebei uur 0/2 en dag 0/10, binnen de actieve uren.
  - Ik heb LinkedIn bewust niet gebruikt. Twee doelen zijn organisaties, en het derde doel heb ik overgeslagen.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` gaf 148 `person:maarten-van-der-weijden`, 139 `org:knvb` en 140 `org:vrt`.

## Per doel
| Doel | Status | Ingediend |
|---|---|---|
| 148 Maarten van der Weijden | overgeslagen | niets |
| 139 KNVB | klaar | knoop **4898** Koninklijke Nederlandse Voetbalbond (KNVB) (`ngo`, rol 39 belanghebbende, `active_from` 1889-12-08); bron **3099** (knvb.nl Historie); argument **11031** (`active_from` 1889-12-08 op de knoop) |
| 140 VRT | klaar | knoop **4897** VRT (Vlaamse publieke omroep) (`omroep`, rol 2 mediaorganisatie); relatie **8396** (VRT ↔ NPO 131, `alliantie`, kandidaat zonder mechanisme, `active_from` 2022-10-12); bron **3098** (persbericht vrt.be, 12-10-2022); argumenten **11029** (bekendmaking door de NPO-raad van bestuur en de VRT-directie) en **11030** (`active_from` 2022-10-12) |

- **Van der Weijden:** hij is sporter. Zijn enige bestuursrol is bij zijn eigen goededoelenstichting, en daarmee stopt hij volgens de artikelen. Die rol heeft geen band met media, politiek of besluitvorming, dus valt hij onder "geen rol in het netwerk".
- **KNVB:** volgens de dossiers van de Tweede Kamer (`data/registers/tk/overgeslagen_2026-10-13.json`) bleven 55 geschenken van de KNVB aan Kamerleden liggen met de reden "geen bekende gever".
  - De importer (`tk_naar_model.py`) zoekt gevers onder alle knopen die niet `afgewezen` zijn. Met knoop 4898 erbij koppelt de volgende registers-sync (wekelijks, de laatste was op 13-10) die geschenken als registerfeiten.
  - Zelf heb ik die geschenken niet ingediend: het zijn registerfeiten, en die doet de registers-sync.
  - Er is een risico. Komt die koppeling niet binnen 14 dagen, dan wijst stap 11 knoop 4898 af omdat er geen verband aan hangt.
- **VRT:** geen bestaand mechanisme dekt een programmasamenwerking tussen twee omroepen. Ik heb daarom niets geforceerd; stap 7 (de mechanisme-toewijzer) beslist.
  - Gekeken en verworpen: `pakketjournalistiek` (EBU-precedent, rel. 727), `intermedia_agendering` (AT5–NH, rel. 1106) en `cross_media_eigendom`.
  - De rolzin uit het nieuws (VRT als bron over een Belgisch hof) is geen structuurfeit.

### Wat misging tijdens het indienen
- **Gat in `scripts/scout_indienen.py` (al gemeld in ronde 1).** Losse `argumenten` lossen nog steeds geen manifest-sleutels op (`"entity_id": "knvb"`).
- **Omweg.** Ik heb in twee runs ingediend (`nieuws-org-knvb-1.json`, daarna `-2.json` met id 4898). Bron 3099 werd daarbij hergebruikt via dezelfde url.

## Zoekopdrachten (letterlijk)
- **Web:**
  - `VRT NPO samenwerking coproductie akkoord publieke omroepen Vlaanderen Nederland`
  - `KNVB NOS uitzendrechten Oranje contract verlengd`
  - `KNVB opgericht 8 december 1889 Koninklijke Nederlandse Voetbalbond over de KNVB organisatie`
- **Opgehaald:**
  - rtl.nl/boulevard/artikel/5657840 (Hein): de fetch-tool kan rtl.nl niet ophalen
  - vrt.be/nl/over-de-vrt/nieuws/2022/10/12/npo-en-vrt-gaan-intensief-samenwerken-om-impact-te-vergroten/ (WebFetch en curl; citaten letterlijk teruggevonden)
  - vrt.be/nl/over-de-vrt/nieuws/2023/11/15/publieke-omroepen-bundelen-krachten-vrt-en-npo-gaan-structureel/
  - vrt.be/nl/over-de-vrt/onze-organisatie/geschiedenis/ en vrt.be/nl/over-ons/onze-organisatie/geschiedenis/
  - knvb.nl/node/432 (= /over-ons/over-de-knvb/historie, citaat letterlijk), /node/22178 en /node/37463
- **Database (alleen-lezen):**
  - entiteiten op `%Weijden%`, `%KNVB%`, `%voetbal%`, `%VRT%`, `%Vlaamse Radio%`, `%Eredivisie%`, `%Ketnet%`, `%Hein%` en `%Canal%`; geen van de drie bestond
  - de NPO-knopen en alle relaties van NPO 131
  - `alliantie`-relaties per mechanisme en de kandidaten daarbij
  - de volledige mechanismelijst, de rollen 2, 39, 46, 47 en 58, en de CHECK op het entiteitstype
  - KNVB in `data/registers/tk/tk_2026-10-13.json` en `overgeslagen_2026-10-13.json`
  - `tk_naar_model.py` (de gever-matching), `common.namen_van` en `agent_schedule.py` (de registers-sync)

## Negatieve resultaten (alleen in dit log)
- **KNVB:**
  - Geen actuele bron gevonden voor de uitzendrechten van Oranje bij de NOS (de zoekresultaten waren oud). Daarom is er geen KNVB↔NOS-verband ingediend.
  - Geen inschrijving van de KNVB in het lobbyistenregister gevonden in de lokale data.
- **VRT:**
  - De geschiedenispagina van vrt.be noemt geen oprichtingsdatum, dus knoop 4897 heeft geen `active_from`. De meter `ORGANISATIE-ZONDER-BESTAAN` en de datumzoeker pakken dat op.
  - Het RTL-artikel over Hein kon ik niet openen, dus ik weet niet of VRT bij Hein betrokken is.
- **Van der Weijden:** niet onderzocht buiten de context, want hij valt buiten het netwerk.

## Stance-balans
3 steun, 0 tegen, 0 context.

**Nieuwheid:** twee nieuwe knopen (4897, 4898), één nieuw verband (8396) en geen hercitaties.

```

## Runner-metadata

- Exit-code: 0
- Duur: 382.9 s
- Oogst (edit_log-delta van `nieuws-scout`): 8
- Beëindigd: 2026-10-16T10:25:16
