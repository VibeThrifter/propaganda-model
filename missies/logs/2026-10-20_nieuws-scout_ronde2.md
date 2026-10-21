# Onbewaakte ronde — nieuws-scout · ronde2 · 2026-10-20

- Brief: `missies/nieuws_scout_brief.md` (blob `d8091c4ce188`)
- Account: `nieuws-scout`
- Gestart: 2026-10-20T18:00:32

## Sessie-uitvoer

```
# Ronde-log: nieuws-scout, ronde 2, 20 oktober 2026

- **Brief:** `missies/nieuws_scout_brief.md` (blob `d8091c4ce188`)
- **Account:** `nieuws-scout`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []` en `via_reply: []`, dus er hoefde niets overgeslagen te worden. Deze ronde bevat geen reacties op bestaande argumenten.
- **LinkedIn-rem bij de start:** `mag zoek` gaf exit 0 en `mag profiel` gaf exit 0. Ik heb daarom geclaimd met `claim_volgende?limit=3&linkedin=1`.
- **Uitkomst:** drie doelen geclaimd. Eén doel is `klaar` met 8 ingediende verbanden, twee zijn `overgeslagen`. Ik kreeg geen 429 en geen LinkedIn-melding.

## Per doel

| id | sleutel | status | reden |
|---|---|---|---|
| 261 | `person:jimmy-kimmel` | `overgeslagen` | Buitenland, geen Nederlandse rol. Hij is een Amerikaanse tv-presentator en comedian. |
| 262 | `person:eric-kemperman` | `klaar` | Eerste Kamerlid en lid van Provinciale Staten Gelderland. Ik heb 8 verbanden ingediend (details hieronder). |
| 263 | `person:robert-f-kennedy` | `overgeslagen` | Buitenland, geen Nederlandse rol. Hij is de Amerikaanse minister van Volksgezondheid. |

## Zoekopdrachten (letterlijk)

**Database (alleen-lezen, `file:data/propaganda_model.db?mode=ro`):**
- `SELECT id,name,type,status,primary_role_id FROM entities WHERE name LIKE '%Kemperman%' OR name LIKE '%Kimmel%' OR name LIKE '%Kennedy%';` gaf #3562 "E. Kemperman (kamerlid Eerste Kamer)". Over Kimmel en Kennedy staat niets in het model.
- `SELECT id,name,type,status FROM entities WHERE name LIKE '%Forum voor Democratie%' OR name LIKE 'FVD%' OR name LIKE 'FvD%' OR name LIKE '%Eerste Kamer%' OR name LIKE '%Provincie Gelderland%' OR name LIKE '%Provinciale Staten%Gelderland%' OR name LIKE 'Gelderland%' OR name='Epe' OR name LIKE 'Gemeente Epe%';` gaf #218 FvD, #380 Eerste Kamer, #1431 Gemeente Epe en #3864 Provincie Gelderland.
- `SELECT r.id,… FROM relations r … WHERE r.source_id=3562 OR r.target_id=3562;` gaf twee registerfeiten:
  - #5382: ambt Eerste Kamer, `active_from` 2025-09-09;
  - #5383: lidmaatschap FvD, `active_from` 2025-09-09.
- `SELECT * FROM externe_ids WHERE entity_id=3562;` gaf `oo` `m:30352950`. In `nieuws_doelen` staan geen eerdere verslagen over Kemperman.
- `SELECT id,name,type,status FROM entities WHERE name LIKE '%BoerBurger%' OR name LIKE 'BBB%' OR name LIKE '%Woonforte%' OR name LIKE '%Laurentius%' OR name LIKE '%Studenten Huisvesting%' OR name LIKE '%SSH%' OR name LIKE '%Jachtopleiding%' OR name LIKE '%KNJV%' OR name LIKE '%Jagers%' OR name LIKE '%Faunabeheer%' OR name LIKE '%Provinciale Staten%';` gaf alleen #1080 BBB. De zes organisaties ontbraken.
- `SELECT id,name,aard FROM mechanisms WHERE name IN ('kamerzetel','partijlijn','nevenfunctie_verstrengeling','lokaal_bestuursmandaat','partijbinding');` gaf 211, 210, 216, 163 en 92. Voor draaideurconstructie is het id 18.
- Precedenten:
  - Statenleden met mechanisme 211: #8717 en #8722 (`ambt`, functie "lid Provinciale Staten").
  - BBB-lidmaatschappen: #1927 en #2978.
  - Nevenfuncties met mechanisme 216, verdeeld over entiteittype en rol: meestal stichting met maatschappelijke_organisatie.
  - Typering: LTO staat als lobbygroep met rol lobbyist.

**Web:**
- WebSearch `Eric Kemperman FVD Eerste Kamer Provinciale Staten Gelderland parlement.com`
- WebFetch `https://www.trouw.nl/politiek/ondanks-het-succes-bij-lokale-verkiezingen-lijkt-fvd-overal-buiten-de-coalitie-te-vallen~bd33d800/`: niet op te halen (geblokkeerd).
- curl en WebFetch `https://www.parlement.com/id/vm0mjqc84fjv/e_eric_kemperman`: ik heb alle citaten letterlijk teruggevonden in de html.
- curl `https://www.eerstekamer.nl/persoon/drs_e_kemperman_mba_fvd`: het nevenfunctieregister en de fractiegeschiedenis staan erop, en de citaten staan er letterlijk.

**LinkedIn:** geen zoekactie en geen scrape. Ik heb dat bewust overgeslagen: het officiële nevenfunctieregister van de Eerste Kamer en Parlement.com dekken loopbaan en nevenfuncties beter, met datums.

## Aangemaakt (doel 262, alles `voorgesteld`)

- **Bronnen:**
  - #3425: Eerste Kamer, persoonspagina met nevenfunctieregister (voorstel: `institutioneel`);
  - #3426: Parlement.com, biografie (voorstel: `regulier`).
- **Entiteiten:**
  - #5053 Stichting Woonforte
  - #5054 Woningcorporatie Laurentius
  - #5055 Stichting Studenten Huisvesting (SSH)
  - #5056 Stichting Jachtopleidingen Nederland
  - #5057 Stichting Nationaal Kenniscentrum Faunabeheer (rol kennisinstituut)
  - #5058 Koninklijke Nederlandse Jagers Vereniging (KNJV) (lobbygroep, rol lobbyist)

  De eerste vier zijn stichtingen met rol maatschappelijke_organisatie.
- **Verbanden en argumenten:**

| relatie | verband | mechanisme | looptijd | argument(en) | bron |
|---|---|---|---|---|---|
| #8778 | #3562 → Provincie Gelderland, `ambt` (lid Provinciale Staten) | kamerzetel (211) | 2023-03-29 – | #11746 | #3426 |
| #8779 | BBB → #3562, `lidmaatschap` (BBB-fractie Eerste Kamer) | partijlijn (92) | 2023-06-13 – 2025-05-19 | #11747 | #3425 |
| #8780 | #3562 → Stichting Woonforte, `bestuurder` (commissaris) | nevenfunctie_verstrengeling (216) | 2019-09-01 – | #11748 (voorzitter RvC 2019–2025), #11749 (lid RvC sinds 2025-10-01) | #3425 |
| #8781 | #3562 → Woningcorporatie Laurentius, `bestuurder` (lid RvC) | 216 | 2020-06-01 – 2026-06-01 | #11750 | #3425 |
| #8782 | #3562 → SSH, `bestuurder` (voorzitter RvC) | 216 | 2021-09-01 – 2025-08-31 | #11751 | #3425 |
| #8783 | #3562 → Stichting Jachtopleidingen Nederland, `bestuurder` (directeur-bestuurder) | 216 | 2020-05-01 – | #11752 | #3425 |
| #8784 | #3562 → Kenniscentrum Faunabeheer, `bestuurder` (voorzitter) | 216 | 2022-11-01 – 2025-05-17 | #11753 | #3426 |
| #8785 | #3562 → KNJV, `bestuurder` (lid RvT) | draaideurconstructie (18) | 2018 – 2020-05-01 | #11754 | #3426 |

Het KNJV-verband krijgt draaideurconstructie in plaats van nevenfunctie_verstrengeling, omdat het helemaal vóór zijn eerste mandaat valt.

## Opmerkingen en negatieve resultaten (alleen in dit log)

- **Afwijkende startdatum Statenlidmaatschap:** eerstekamer.nl noemt 23 maart 2023, Parlement.com 29 maart 2023. Ik heb 29 maart gebruikt, met het citaat van Parlement.com.
- **Registerfeit #5382 (ambt Eerste Kamer):** begint op 2025-09-09. Dat is het begin van zijn huidige FvD-pet; zijn zetel loopt sinds 13 juni 2023 ("Lid Eerste Kamer … vanaf 9 september 2025, eerder vanaf 20 mei 2025 tot 9 september 2025 en vanaf 13 juni 2023 tot 20 mei 2025"). Ik heb geen correctie ingediend, omdat stap 10c een registerdatum nooit overschrijft.
- **Niet ingediend:**
  - informateur collegevorming gemeente Epe (2 tot 24 april 2026): geen passend mechanisme voor zo'n kortlopende opdracht;
  - eenmansfractie-Kemperman (2025);
  - commissievoorzitterschappen in de Eerste Kamer;
  - PCO Kennis BV en Kemperman Holding (eigen bedrijf);
  - docentschap Public Academy;
  - vrijwilligerswerk.

  Dat zijn kleinere banden of banden zonder passend mechanisme; ze zijn hier alleen vastgelegd als mogelijk vervolg.
- **Kimmel en Kennedy:** ze staan niet in het model. Er is geen Nederlandse rol, en ik heb niet verder gezocht.

## LinkedIn-remstatus aan het einde

Automatisch: aan, actieve uren 08:00–22:00 (nu actief). Profiel: 0/2 per uur, 0/10 per dag. Zoeken: 0/2 per uur, 0/10 per dag.

## Stance-balans

9 steun / 0 tegen / 0 context

```

## Runner-metadata

- Exit-code: 0
- Duur: 263.6 s
- Oogst (edit_log-delta van `nieuws-scout`): 25
- Beëindigd: 2026-10-20T18:04:56
