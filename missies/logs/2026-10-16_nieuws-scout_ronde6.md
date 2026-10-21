# Onbewaakte ronde — nieuws-scout · ronde6 · 2026-10-16

- Brief: `missies/nieuws_scout_brief.md` (blob `3a6cca5f46b6`)
- Account: `nieuws-scout`
- Gestart: 2026-10-16T18:52:48

## Sessie-uitvoer

```
# Ronde-log: nieuws-scout, ronde 6, 16 oktober 2026

Ik claimde drie organisatiedoelen. Eén ervan (ANWB) staat op `klaar`: twee personen met vier gedateerde verbanden, alles `voorgesteld`. De andere twee staan op `overgeslagen`. Er kwam geen 429 en geen 409, en ik heb LinkedIn niet gebruikt.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `3a6cca5f46b6`. **Account:** `nieuws-scout`.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []`. Ik hoefde niets over te slaan en heb geen reacties ingediend.
- **LinkedIn-rem:** `mag zoek` en `mag profiel` gaven allebei exit 0, dus ik claimde met `&linkedin=1`. Na de ronde gaf `status` voor profiel en zoek allebei uur 0/2 en dag 0/10, binnen de actieve uren.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` gaf 123 `org:provinciale-staten`, 141 `org:ad-media-podcast` en 232 `org:anwb`.

## Per doel
| Doel | Status | Ingediend |
|---|---|---|
| 232 ANWB | klaar (`entity_id` 1835) | 4 bronnen, 2 knopen, 4 verbanden, 5 argumenten |
| 123 "Provinciale Staten!" | overgeslagen (geen eenduidige actor) | niets |
| 141 AD Media Podcast | overgeslagen (geen eigen actor) | niets |

### 232 ANWB
De ANWB stond al in het model als knoop 1835, "Koninklijke Nederlandse Toeristenbond ANWB". Die knoop komt uit het register van overheidsorganisaties (zbo), met de relatie I&W → ANWB (`zeggenschap`). Ik heb de knoop hergebruikt en de leiding toegevoegd.

- **Bronnen:**
  - #3241 ANWB, "Structuur en bestuur"
  - #3242 ANWB, pdf "Samenstelling Raad van Toezicht 2025"
  - #3243 ANWB-nieuwsbericht "Marga de Jager nieuwe CEO ANWB" (29 maart 2021)
  - #3244 Parlement.com, "L.B. (Lucas) Vos"
- **Knopen:**
  - #4942 Lucas Vos (persoon, rol-suggestie `raad_van_commissarissen`)
  - #4943 Marga de Jager (persoon, rol-suggestie `directie`)
- **Verbanden en argumenten (alle argumenten steunend):**

| Verband | Type, mechanisme, functie | Looptijd | Argumenten |
|---|---|---|---|
| #8486 Lucas Vos → ANWB | `bestuurder`, `draaideurconstructie`, "voorzitter raad van toezicht" | vanaf 2025-04 | #11263 (citaat "dhr. L. (Lucas) Vos, voorzitter per april 2025") en #11264 (RvT-pdf: "L.B. (Lucas) Vos 1967 … Voormalig: President Stolt Tankers") |
| #8487 Lucas Vos → Eerste Kamer | `ambt`, `kamerzetel`, "Kamerlid" | 2022-01-18 tot 2023-06-13 | #11265 |
| #8488 VVD → Lucas Vos | `lidmaatschap`, `partijlijn`, "Eerste Kamerlid" | 2022-01-18 tot 2023-06-13 | #11266 |
| #8489 Marga de Jager → ANWB | `bestuurder`, `directiebenoeming`, "CEO" | vanaf 2021-04-01 | #11267 |

- **Identiteit van Lucas Vos:** de ANWB-voorzitter is dezelfde persoon als het oud-VVD-Eerste Kamerlid. Twee bronnen vallen samen op het geboortejaar 1967, "President Stolt Tankers" en het voorzitterschap van de RvT van het Aidsfonds: de ANWB-pdf en Parlement.com.
- **VVD-band:** Parlement.com noemt alleen de fractieperiode. Daarom heeft de VVD-band de periode van de zetel, net als de precedenten uit het register.
- **Citaten:** alle citaten heb ik vóór het indienen letterlijk teruggevonden, met `bronchecker.zoek_citaat` op de opgehaalde html en pdf.

### 123 "Provinciale Staten!"
Dit is een verzamelnaam voor de twaalf Statenvergaderingen. Hij kwam uit de kop van een Volkskrant-recensie ("Britt for President") en twee politieke artikelen zonder rolzinnen of organisaties. De provincies staan al uit het register in het model.

### 141 AD Media Podcast
Dit is een wekelijkse podcast van het AD over de mediawereld, met Angela de Jong en mediaverslaggevers. Hij werd genoemd bij artikelen over het Televizier-Ring Gala. Het AD (3) en Angela de Jong (1277) staan al in het model, en de AD-redactie was al afgehandeld in `redactieleiding:ad` (klaar).

## Zoekopdrachten (letterlijk)
- **Web (WebSearch):**
  - `ANWB algemeen directeur benoemd`
  - `"AD Media Podcast" presentatoren`
  - `Marga de Jager CEO ANWB benoemd bondsraad`
  - `Lucas Vos voorzitter ANWB raad van toezicht 2025`
  - `"Lucas Vos" ANWB voorzitter FloraHolland OR Maersk OR Stolt`
  - `"Marga de Jager" ANWB "1 april 2021" CEO Frits van Bruggen`
- **Opgehaald (WebFetch/curl):**
  - anwb.nl/over-anwb/vereniging-en-bedrijf/organisatie/organisatiestructuur/bestuur-en-structuur
  - anwb.nl/nieuws/maand/2/jaar/2021 (WebFetch gaf 404, de variant met een punt aan het eind werkte wel)
  - anwb.nl/over-anwb/nieuws/2021/maart/marga-de-jager-nieuwe-ceo-anwb
  - merk.anwb.nl/…/Samenstelling-Raad-van-Toezicht-2025.pdf
  - merk.anwb.nl/…/Rooster-van-aan-en-aftreden-RvC-d-d-26-03-2026.pdf
  - parlement.com/biografie/lb-lucas-vos
- **Database (alleen-lezen):**
  - `select … from entities where name like '%Provinciale Staten%' or name like '%ANWB%' or name like '%Media Podcast%' or name like '%podcast%' or name like 'AD%' …`
  - `select … from nieuws_doelen where sleutel like 'org:%staten%' or … 'org:kamer%' …`
  - de relaties van entiteit 1835
  - `externe_ids` voor 1835 (oo 28143350)
  - de precedenten voor `bestuurder`/`ambt` bij een zbo (draaideurconstructie 12×, commissarisbenoeming 8×, directiebenoeming 3×)
  - de precedenten voor Eerste Kamer en VVD-lidmaatschap
  - `entities where name like '%Vos%' or '%Jager%'` (geen L.B. Vos, geen Marga de Jager)
  - `entities where name like '%Angela de Jong%' …` (1277)
  - bronnen op parlement.com/anwb.nl (geen bestaande)
- **Registers:** `grep -il anwb data/registers/lobby/*` gaf geen treffer in de lobby-pdf.
- **LinkedIn:** geen zoekactie en geen scrape. De primaire bronnen (ANWB en Parlement.com) stelden de identiteit en de functies al vast.

## Negatieve resultaten (alleen in dit log)
- De ANWB-pagina's noemen De Kampioen niet als mediabezit. Het verband ANWB → De Kampioen heb ik daarom niet onderzocht of ingediend.
- De ANWB staat niet in het lobbyregister (pdf van 2026-10-01).
- **Niet ingediend, mogelijk later:**
  - de KPN-commissariaat van Marga de Jager (2023)
  - de overige RvT-leden: Korthout (APG/BNG), Wenselaar (oud-Menzis), Leurs (oud-Rabobank), Kimmels, Schellekens (KLM)
  - de VVD-kandidaatstellingscommissie 's-Gravenhage (vanaf mei 2018) van Lucas Vos
- **Voor de eigenaar:** de nieuws-aggregator biedt nog steeds verzamelnamen ("Provinciale Staten!") en producten (een podcast) aan als organisatie.
- **Opmerking over het type:** de ANWB-knoop heeft type `overheidsinstelling` uit het OO-register (zbo). Het is een vereniging met een zbo-taak. Ik heb dat niet gewijzigd, want het type komt uit het register.

## Stance-balans
5 steun, 0 tegen, 0 context.

```

## Runner-metadata

- Exit-code: 0
- Duur: 452.8 s
- Oogst (edit_log-delta van `nieuws-scout`): 15
- Beëindigd: 2026-10-16T19:00:21
