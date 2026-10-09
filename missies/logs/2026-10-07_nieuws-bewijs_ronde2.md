# Ronde-log nieuws-bewijs · ronde2 · 2026-10-07

- **Brief:** `missies/nieuws_bewijs_brief.md`, blob `f4945ac5b576`
- **Account:** `nieuws-bewijs`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `[2322]` terug. Dat argument hoort bij geen van beide doelen.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` leverde doel #77 (`relatie:221`) en doel #78 (`relatie:222`) op.
- Er waren geen 409's en geen 429. LinkedIn was niet nodig: dit is bronnenonderzoek naar redacties, geen loopbaanonderzoek.

## Doel #77: `relatie:221`, RIVM → De Telegraaf (`bron_afhankelijkheid`) → **klaar**

**Wat het model beweert:** "RIVM-communicatie werd door Telegraaf overgenomen als gezaghebbend." Mechanisme #6 zegt: wie de routinebron levert, levert ook het frame.
- Daar pleit vóór: De Telegraaf neemt de RIVM-lijn over zonder tegenstem.
- Daar pleit tegen: De Telegraaf bevraagt het RIVM kritisch of geeft andere deskundigen en critici ruimte.

**Bestaand argument #223** (supporting, `betwist`, legacy) heeft geen citatie. De maintainer zette het op 2026-07-07 op betwist met de reden "geen per-outlet-bron met verbatim citaat". Er is dus geen bron om te toetsen, en ik diende geen ondergraving in.

**Neutrale zoekvraag:** *"Hoe ging De Telegraaf in de coronacrisis om met het RIVM als bron? Kwamen er andere stemmen of kritiek aan bod?"*

| Bron | Argument | Stance |
|---|---|---|
| **#2398 (nieuw)**: NRC, 22-6-2020, Bart Hinke, "Hoofdredacteuren blikken terug. 'Corona heeft ook ons overspoeld'" (cluster `nrc`, voorgesteld `kwaliteitsjournalistiek`/`nl_systeem`) | **#3953**: volgens NRC kraakte een stevig Telegraaf-commentaar ("Van het RIVM mag beter worden verwacht") enkele dagen na 16-3-2020 de 'frame'-opmerking van Van Dissel en de sussende RIVM-toon in februari | tegen |
| #2398 | **#3954**: volgens NRC gaf De Telegraaf critici een aantal keer als eerste een landelijk podium, voordat zij elders verschenen | tegen |

**Voor de mens:** Jansen zegt in hetzelfde NRC-stuk dat De Telegraaf "vanuit kabinetskringen het verzoek kreeg het RIVM 'een beetje heel' te laten". Dat gaat over een mogelijke kabinet → Telegraaf-beïnvloeding, niet over dit verband. Ik heb daarom geen argument en geen relatie ingediend. Het staat wel in het verslag.

## Doel #78: `relatie:222`, RIVM → AD (`bron_afhankelijkheid`) → **klaar**

**Wat het model beweert:** "AD nam RIVM-persberichten en data routinematig over."

**Bestaand argument #224** (supporting, `betwist`, legacy) heeft geen citatie. De maintainer zette het op 2026-07-07 op betwist omdat het niet te sourcen was. Ik diende geen ondergraving in.

**Neutrale zoekvraag:** *"Hoe gebruikte het AD in de coronacrisis het RIVM als bron? Bracht het andere deskundigen of eigen kritiek?"*

| Bron | Argument | Stance |
|---|---|---|
| #1611 (De Vrieze, "Lessen van de coronapandemie deel 2", 2023; bestond al) | **#3955**: het AD koos bewust voor een diversiteit aan geluiden naast OMT/RIVM (Rijpma noemt De Hond en een kritische ondervraging van Engel) | tegen |

Argument #3955 diende ik rechtstreeks in via `POST /api/arguments` met `source_id` 1611, met de citatie-methode `verbatim_quote`. Het manifestscript kan geen bestaande bron hergebruiken.

## Zoekopdrachten, letterlijk

**Database (alleen-lezen) en API:**
- de relatie-query uit de brief, `WHERE r.id IN (221,222)`
- `curl /api/arguments?relation_id=221` en `?relation_id=222`
- `SELECT * FROM edit_log WHERE table_name='arguments' AND record_id IN (223,224)`
- `arguments` en `citations` van #3941–#3947 (ronde 1), plus `sources` en `source_locations` van 1611 en 2394
- `source_locations WHERE location LIKE '%a4003640%' OR '%overspoeld%' OR '%857516161%'`: leeg, de NRC-bron was nieuw
- relaties van De Telegraaf met kabinet, Rutte, RIVM, VWS of Rijksoverheid: alleen rel. 221

**Web (WebSearch):**
1. `Telegraaf coronaberichtgeving RIVM kritisch hoofdredacteur Paul Jansen corona verantwoording`
2. `inhoudsanalyse Telegraaf corona berichtgeving bronnen RIVM OMT onderzoek kranten vergelijking`
3. `AD Algemeen Dagblad RIVM kritiek onthulling corona cijfers onderzoek AD 2020 2021`
4. `ad.nl RIVM coronacijfers "meldt het RIVM" dagelijks overzicht besmettingen`
5. `AD onderzoek onthult RIVM kritiek ad.nl "RIVM" onthulling Rijpma hoofdredacteur corona terugblik`
6. `De Telegraaf coronaberichtgeving Villamedia OR "De Nieuwe Reporter" kritisch kabinet RIVM Telegraaf rol coronacrisis analyse`
7. `Algemeen Dagblad coronacrisis berichtgeving RIVM bron volgzaam OR kritisch AD redactie Villamedia ombudsman`

**Opgehaald (curl/WebFetch):**
- jopdevrieze.nl, deel 2 (bron 1611): de AD-passages; De Telegraaf komt er niet in voor
- Joop, "De fluwelen zetels van de coalitie" (opinie, Containment Nu): alleen gebruikt als vindplaats, en die leidde naar NRC
- NRC `a4003640`: beide quotes letterlijk teruggevonden na het samenvoegen van witruimte. De quote van #3953 begint bewust ná de link om de kop, zodat ze niet over een tag-grens loopt.
- telegraaf.nl/watuzegt/857516161 (het commentaar zelf): WebFetch geweigerd, curl gaf een 403 (Cloudflare). Daarom citeer ik NRC als secundaire bron.
- archive.org/wayback/available gaf een 429 voor zowel NRC als Telegraaf. Dat is een externe dienst en niet onze API.
- EUR-scriptie Holleman (pdf): gaat over avondklok-framing en meet geen RIVM-bronaandeel per titel
- VWS-mediamonitor OVV-rapport (Woo 1ef48c38): gaat over het OVV-rapport uit 2022 en niet over het RIVM als bron

## Negatieve resultaten (alleen in dit log)

- **Vóór, Telegraaf:** geen bron gevonden die per titel laat zien dat De Telegraaf RIVM-communicatie routinematig als gezaghebbend overnam. Er is ook geen inhoudsanalyse van het bronaandeel per krant.
- **Vóór, AD:** geen bron gevonden die routinematige overname van RIVM-persberichten of -data door het AD als patroon documenteert. De zoekopdrachten naar dagcijfers leverden alleen Hart van Nederland, NOS, nieuws.nl en DutchNews op. Een dagelijks cijferbericht "RIVM meldt …" zou trouwens nog geen frame-afhankelijkheid bewijzen.
- **Overwogen maar niet ingediend:**
  - Rijpma (De Vrieze, r. 76–77): het AD bleef weg bij tegengeluid over avondklok, mondkapjes en vaccinaties omdat dat "naar het extreme neigde", en de twijfel van de middengroep kreeg te weinig aandacht. Dat gaat over critici van overheidsbeleid, niet over het RIVM als bron. Ik hield dezelfde lijn aan als in ronde 1.
  - Jansen, NRC: "ik had achteraf gezien de redactie er meer op moeten wijzen te blijven onderzoeken". Dat gaat over de crisiscommunicatie van het kabinet, niet over het RIVM.
- **Geen AD-onthulling over het RIVM gevonden** die vergelijkbaar is met de Volkskrant-ventilatieonthulling uit ronde 1.

## Stance-balans

**0 steun / 3 tegen / 0 context / 0 ondergraving**
- rel. 221: tegen #3953, #3954 (bron #2398)
- rel. 222: tegen #3955 (bron #1611)

Beide verbanden rusten na deze ronde nog op geen enkele geldige bron vóór. Dat is ook een uitkomst. De concern- en titelvraag uit ronde 1 (rel. 145 tegenover 220/221/222) blijft open voor een mens.

Manifest: `data/scout/bewijs-relatie-221-222.json`; resultaat: `data/scout/bewijs-relatie-221-222.resultaat.json`.
