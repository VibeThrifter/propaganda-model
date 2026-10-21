# Onbewaakte ronde — nieuws-scout · ronde2 · 2026-10-19

- Brief: `missies/nieuws_scout_brief.md` (blob `d8091c4ce188`)
- Account: `nieuws-scout`
- Gestart: 2026-10-19T14:30:40

## Sessie-uitvoer

```

## Missielog (agent) — nieuws-scout · ronde2 · 2026-10-19

- **Brief:** `missies/nieuws_scout_brief.md`, blob-hash `d8091c4ce188` (`git hash-object` → `d8091c4ce188…`)
- **Account:** `nieuws-scout`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` → `gereageerd_op: []`, `via_reply: []`. Ik diende geen reacties in.
- **LinkedIn-rem bij de start:** `snelheidsrem.py mag zoek` → exit 75 ("uurmaximum bereikt (2/2 zoek in het afgelopen uur)", volgende kans 14:58); `mag profiel` → exit 75 (2/2 profiel, volgende kans 14:59). Ik claimde zonder `&linkedin=1` en gebruikte LinkedIn niet.
- **LinkedIn-rem aan het eind** (`snelheidsrem.py status`): profiel uur 2/2 · dag 2/10; zoek uur 2/2 · dag 2/10; volgende kans 2026-10-19T14:59:21.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3` → doelen 125, 144, 236.

### Doel 125 — `person:presentatrice-amber` ("Presentatrice Amber") → `overgeslagen`
- De artikelen (RTL Nieuws, AD, De Telegraaf, 7–8 okt 2026) gaan over Kassa en Amber Kortzorg. Het doel is een verminkte naam en een dubbel van doel 124 (ronde1 vandaag), dus ik heb het niet opnieuw onderzocht.
- DB (alleen-lezen): `select id,name,type,status,primary_role_id from entities where name like '%Genemans%' or name like '%Kops%' or name like '%Kortzorg%' or name like 'Videoland%' or name like 'RTL 4%' or name like 'RTL Nederland%' or name like 'BNN%' or name like '%Jacht op de sterren%' or name like 'EWOUT%' or name like 'RTL Group%' or name like 'DPG Media';` → Amber Kortzorg #4944 (goedgekeurd). Ik zette #4944 als `entity_id` op het doel en diende niets in.

### Doel 144 — `person:jade-kops` (Jade Kops) → `overgeslagen`
- Web: `Jade Kops Emma Kok Renze Klamer` → socialemediapersoonlijkheid, in april 2026 op 19-jarige leeftijd overleden aan een zeldzame vorm van kanker (nieuws.nl, Hart van Nederland, welingelichtekringen.nl in de zoekresultaten). Ze had geen publieke functie in politiek, media, bestuur of een organisatie, dus geen rol in het netwerk (brief § "Wie wel, wie nooit"). De rolzin "Zus Jade Kops" gaat over familie.
- DB: dezelfde zoekopdracht als hierboven → geen Kops-knoop (alleen Alexander Kops #3748, Elise Moeskops #2179: andere personen). Ik heb niets ingediend.

### Doel 236 — `person:ewout-genemans` (Ewout Genemans) → `klaar`, vervolg `linkedin`
**Identiteit en rol:** televisiepresentator en programmamaker bij RTL Nederland (RTL 4/RTL 5/Videoland). De context gaat over zijn reportageseries (Thailand undercover, Hollywood, Bureau Groningen). Ik behandelde hem als mediapresentator volgens het precedent van ronde1 (Kortzorg) en de presentatoren Klamer, Genee en Simons.

**DB-zoekopdrachten (alleen-lezen):**
- De entities-zoekopdracht hierboven → RTL Nederland #8 (omroep), Videoland #3929, BNN #3931, BNNVARA #139. Er is geen Genemans-knoop.
- `select r.id,es.name,r.relation_type,et.name,r.mechanism_id,r.functie,r.active_from,r.active_until,r.status from relations r … where (r.source_id in (3929,3931,8) or r.target_id in (3929,3931,8)) and (es.type='persoon' or et.type='persoon') limit 40;` → precedent rel. 1926 Sylvana Simons → RTL Nederland, `personeel`, mechanisme 18.
- `select id,name,type,status,primary_role_id from entities where name like '%Fremantle%' or name like '%No Pictures%' or name like 'RTL Group%' or name like 'Bertelsmann%' or name like '%Karthaus%';` → leeg.
- `select id,name,type,status from entities where name like '%RTL%' or name like '%Talpa%' or name like '%productie%' or name like '%Endemol%' or name like '%Banijay%' or name like '%Skyhigh%' limit 40;` en de eigendomsrelaties van #8 → RTL Nederland is sinds 2025-07-01 van DPG Media (rel. 9, 1061).
- `select id,name from roles where id in (26,18) or name in ('journalist','presentator','programmamaker');` → rol `journalist` 26.

**Webzoekopdrachten:**
1. `Ewout Genemans overstap BNNVARA naar RTL Videoland` → alleen Wikipedia en aggregators; BNNVARA wordt nergens genoemd.
2. `Ewout Genemans tekent bij RTL contract` → tvgids.nl en linda.nl; geen contractbericht.
3. `"Genemans" RTL 5 AVRO overstap 2013 presentator` → tvgids, speakersacademy, Wikipedia: een AVRO-contract in 2011, producties voor RTL 5 via zijn bedrijf in 2012–2016, en volgens een niet-gebronde Wikipedia-zin "sinds 2017" presentator bij RTL. Dat gebruikte ik niet.
- Vindplaats (geen bron): https://nl.wikipedia.org/wiki/Ewout_Genemans. Ik volgde de voetnoten naar RTL Boulevard (Verslaafd), nu.nl (overname door Fremantle) en broadcastmagazine.nl.

**Opgehaalde pagina's (curl):**
- https://www.rtlboulevard.nl/…/5216652/ewout-genemans-wordt-nieuwe-presentator-verslaafd → toestemmingsmuur van DPG. Via de Wayback-kopie https://web.archive.org/web/20210511204943/… heb ik beide citaten letterlijk teruggevonden.
- https://www.tvgids.nl/nieuws/shownieuws/ewout-genemans-ik-maak-nu-betere-programmas-dan-tien-jaar-geleden (4-11-2019, Bureau Burgwallen "zijn nieuwe RTL4-serie"). Bevestigt de RTL-band in 2019; ik heb de pagina niet als bron ingediend.
- https://www.rtl.nl/boulevard/artikel/5659014/… (contextartikel) → toestemmingsmuur, niet gelezen.

**LinkedIn:** de rem weigerde (exit 75, uurmaximum). Ik heb het niet herprobeerd en zette `vervolg: "linkedin"` op het doel.

**Ingediend** (manifest `data/scout/nieuws-person-ewout-genemans.json`, alles `voorgesteld`):
- Bron #3374: "Ewout Genemans wordt nieuwe presentator Verslaafd" (RTL Boulevard / RTL Nederland, 2021-02-25, url-locator; voorgesteld: regulier, nl_systeem).
- Entiteit #5042: Ewout Genemans (persoon, rol-suggestie journalist 26).
- Relatie #8757: Ewout Genemans → RTL Nederland #8, `personeel`, mechanisme 18 `draaideurconstructie`, functie "presentator", `active_from` 2019. Het jaartal staat in het citaat van #11637.
  - Argument #11636 (steun): "Ewout Genemans is in februari 2021 de vaste presentator geworden van het RTL-programma Verslaafd, als opvolger van Peter van der Vorst." Citaat: "Ewout Genemans (36) is definitief de nieuwe presentator van het RTL-programma 'Verslaafd'. Hij vervangt daarbij Peter van der Vorst."
  - Argument #11637 (steun): "Ewout Genemans presenteerde in 2019 een seizoenshelft van het RTL-programma Verslaafd." Citaat: "In 2019 namen Ewout en Peter ieder al een seizoenshelft van Verslaafd voor hun rekening, dus Ewout is al een beetje warmgelopen."
- Er was geen 409 en geen 400.

**Negatieve resultaten en wat ik bewust wegliet** (staat alleen in dit log):
- Het begin van zijn band met RTL vóór 2019 is niet gestaafd. "Sinds 2017 presentator bij RTL Nederland" staat zonder voetnoot op Wikipedia; zijn producties voor RTL 5 in 2012–2016 liepen via zijn eigen bedrijf, en dat is een ander soort verband. Het begin blijft daarom 2019, het vroegste jaar uit de bron. De datumzoeker kan het verfijnen.
- No Pictures Please (productiebedrijf, sinds 1-10-2015 onderdeel van FremantleMedia volgens nu.nl) en zijn latere rol als Creative Lead bij Fremantle (broadcastmagazine.nl, 2020) heb ik niet ingediend. Geen van die knopen staat in het model, en het gaat om perifere feiten over het eigendom van een productiebedrijf zonder lijn naar opinievorming (laagste prioriteit). Het is een mogelijk vervolg als RTL Group/Fremantle ooit in kaart komt.
- Het AVRO-contract (1-12-2011) staat zonder voetnoot op Wikipedia. Niet gezocht en niet ingediend.

### Stance-balans van de ronde
2 steun / 0 tegen / 0 context.

### Afsluiting
- PATCH 125 → `overgeslagen` (entity_id 4944); 144 → `overgeslagen`; 236 → `klaar` (entity_id 5042, resultaat {entity 5042, relation 8757, source 3374, arguments 11636, 11637}, vervolg `linkedin`).
- Geen 429, geen melding over de LinkedIn-sessie, geen blokkade. De rem weigerde LinkedIn bij de start (exit 75).
Ronde 2 van de nieuws-scout is klaar. Ik claimde drie doelen; uit één daarvan kwam een nieuw voorstel, de andere twee vielen af. Alles wat ik indiende staat op `voorgesteld` en wacht op de uurronde.

- **Doel 125, "Presentatrice Amber"** → `overgeslagen`. Het is een verminkte naam van Amber Kortzorg, die al in het model staat (#4944) na ronde 1 van vandaag. Ik heb niets ingediend.
- **Doel 144, Jade Kops** → `overgeslagen`. Ze was een socialemediapersoonlijkheid die in april 2026 overleed, zonder publieke rol in het netwerk. Ik heb niets ingediend.
- **Doel 236, Ewout Genemans** → `klaar`, met `vervolg: linkedin`. Hij is presentator en programmamaker bij RTL Nederland. Ingediend:
  - bron #3374 (RTL Boulevard, 25-02-2021);
  - entiteit #5042, met rol-suggestie journalist;
  - relatie #8757: Genemans → RTL Nederland, `personeel`, mechanisme `draaideurconstructie`, functie presentator, begin 2019;
  - twee steunende argumenten, #11636 en #11637. Beide citaten heb ik letterlijk teruggevonden in de Wayback-kopie, omdat de live pagina achter een toestemmingsmuur zit.

**Wat ik bewust wegliet:**
- Een eerder begin bij RTL dan 2019. Het jaar 2017 staat alleen zonder bron op Wikipedia; in 2012–2016 produceerde hij voor RTL via zijn eigen bedrijf, en dat is een ander soort verband.
- Zijn productiebedrijf No Pictures Please, sinds 2015 onderdeel van Fremantle. Dat is een perifeer eigendomsfeit en geen van die knopen staat in het model.

LinkedIn heb ik deze ronde niet gebruikt: de snelheidsrem weigerde bij de start, want het uurmaximum was al bereikt. Er was geen 429 en geen sessie- of blokkademelding.

Stance-balans: 2 steun / 0 tegen / 0 context. Het volledige log staat in `missies/logs/2026-10-19_nieuws-scout_ronde2.md`, achter de kop die de runner schreef.

```

## Runner-metadata

- Exit-code: 0
- Duur: 252.7 s
- Oogst (edit_log-delta van `nieuws-scout`): 5
- Beëindigd: 2026-10-19T14:34:56
