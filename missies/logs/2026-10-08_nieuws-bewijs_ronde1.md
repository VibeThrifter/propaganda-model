# Onbewaakte ronde — nieuws-bewijs · ronde1 · 2026-10-08

- Brief: `missies/nieuws_bewijs_brief.md` (blob `a18d04acb03b`)
- Account: `nieuws-bewijs`
- Gestart: 2026-10-08T09:07:30

## Sessie-uitvoer

```

# Ronde-log nieuws-bewijs · ronde1 · 2026-10-08

- **Brief:** `missies/nieuws_bewijs_brief.md`, blob `a18d04acb03b`
- **Account:** `nieuws-bewijs`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `[2322]`. Dat argument hoort bij geen van beide doelen.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` gaf doel #96 (`relatie:260`) en doel #80 (`relatie:1579`).
- Geen 409, geen 429. LinkedIn niet gebruikt: dit is bronnenonderzoek naar redacties, geen loopbaanonderzoek.
- Indienscript: `data/scout/bewijs-2026-10-08-r1.py` (directe API-calls, omdat bron #1305 hergebruikt werd); resultaat `data/scout/bewijs-2026-10-08-r1.resultaat.json`.

## Doel #80: `relatie:1579`, RIVM → Nieuwsuur (`expert_framing`, #8) → **klaar**

**Wat het model beweert:** het RIVM levert experts die Nieuwsuur als neutrale autoriteit opvoert. Dat pleit vóór: een patroon van RIVM-deskundigen zonder tegenstem bij Nieuwsuur. Dat pleit tegen: Nieuwsuur bevraagt het RIVM kritisch of laat andere deskundigen het weerspreken.

**Bestaande argumenten:**
- #2339 (supporting, `ongecontroleerd`, assistent): "Van Dissel was de dominante geciteerde autoriteit bij Nieuwsuur/NOS tijdens corona (16 dec 2021)". Eén citatie (bron #1306): de uitspraak "Helaas hebben we geleerd dat we het te vaak optimistisch inschatten." De quote staat er. De bron draagt "dominant" niet → **ondergraving #7847**.
- #3934 (bronzoeker, revisie van #2339): op 2026-10-07 `verworpen` door de automatische beoordeling om dezelfde reden. Geen reactie: het is verworpen.

**Neutrale zoekvraag:** *"Hoe bracht Nieuwsuur het RIVM als deskundige bron (corona, westnijlvirus)? Kwamen andere deskundigen of kritiek aan bod?"*

| Bron | Argument | Stance |
|---|---|---|
| #1305 (bestond al): Nieuwsuur, 11-2-2022, "Ministerie bemoeide zich met OMT-adviezen" | **#7848**: volgens Nieuwsuur nam het RIVM tekstsuggesties van VWS over in OMT-conceptadviezen, zonder OMT-leden te raadplegen | tegen |
| **#2458 (nieuw)**: Nieuwsuur, 4-6-2026, Holdert/Van Hest, "Dringend advies aan het RIVM …" (cluster `nos_nieuwsuur`, voorstel `kwaliteitsjournalistiek`/`nl_systeem`) | **#7849**: Nieuwsuur zette onjuist gebleken RIVM-uitspraken op een rij, met andere deskundigen (o.a. Coutinho) | tegen |
| **#2459 (nieuw)**: NOS, 10-5-2021, "Nieuwsuur wint journalistieke prijs voor onderzoek naar RIVM-richtlijnen ouderenzorg" (cluster `nos_nieuwsuur`) | **#7850**: Nieuwsuur-onderzoek: RIVM-richtlijnen brachten zorgmedewerkers in onveilige situaties | tegen |
| — | **#7851**: aspect `mechanism` = 6 (`bron_afhankelijkheid`); het RIVM is een overheidsinstituut, geen gesponsorde denktank; rel. 221/222 gebruiken ook #6 | aspect |
| (#1306, bestond al) | **#7847**: ondergraving op #2339 | ondergraving |

Alle drie de nieuwe tegen-argumenten vallen in één broncluster (`nos_nieuwsuur`). Ze laten wel een patroon over jaren zien (2021, 2022, 2026). Alle quotes zijn letterlijk teruggevonden op de pagina (na het samenvoegen van witruimte).

## Doel #96: `relatie:260`, Pieter Omtzigt → De Telegraaf (`politicus_als_bron`, #49) → **klaar**

**Wat het model beweert:** "Omtzigt dwong aandacht af voor Toeslagenaffaire ook in Telegraaf". Mechanisme #49: politici zijn primaire bronnen, journalisten hangen van hun goodwill af. Dat pleit vóór: De Telegraaf bracht Omtzigt als bron over de toeslagenaffaire. Dat pleit tegen: De Telegraaf bracht hem kritisch of via anonieme tegenbronnen.

**Bestaand argument #262** (supporting, `betwist`, legacy) heeft geen citatie. De maintainer zette het op 2026-07-07 op betwist ("Geen bron dat Omtzigt de toeslagenaffaire in de Telegraaf afdwong; Telegraaf-berichtgeving ging vooral over interne CDA-strijd"). Er was geen bron om te toetsen, dus geen ondergraving.

**Neutrale zoekvraag:** *"Hoe gebruikte De Telegraaf Pieter Omtzigt als bron (toeslagenaffaire en daarna), en hoe bracht de krant hem?"*

| Bron | Argument | Stance |
|---|---|---|
| **#2460 (nieuw)**: ANP via Welingelichte Kringen, 4-3-2024, "Omtzigt herkent zich niet in beeld over emotionele toestand" (cluster `anp`, voorstel `regulier`/`nl_systeem`) | **#7852**: volgens het ANP bracht De Telegraaf in de formatie kritische berichten over Omtzigts optreden aan de onderhandelingstafel; Omtzigt herkende zich er niet in | tegen |

Smaad-hold: 0 (de claim gaat over de berichtgeving van De Telegraaf; het beeld wordt aan De Telegraaf toegeschreven, niet door het model beweerd).

**Voor de mens:** een gesprek tussen Omtzigt en Telegraaf-columnist/oud-informateur Plasterk (dienstauto, NOS 18-5-2024) en Telegraaf-podcast "Afhameren" (De Winther) kwamen langs. Die vond ik alleen in opiniebronnen (Joop) en heb ik niet ingediend.

## Zoekopdrachten, letterlijk

**Database (alleen-lezen) en API:**
- de relatie-query uit de brief voor `r.id = 260` en `r.id = 1579`
- `curl /api/arguments?relation_id=260` en `?relation_id=1579`
- `SELECT * FROM edit_log WHERE table_name='arguments' AND record_id IN (262,2339,3934)`
- `SELECT id,name,filter,description FROM mechanisms WHERE name IN (…) OR name LIKE '%bron%' OR name LIKE '%expert%' OR name LIKE '%politic%'`
- `source_locations` LIKE `%2416816%`/`%2416821%`/`%2617095%`/`%2380204%`/`%2403300%`/`%2343078%`/`%welingelichtekringen%omtzigt%` → alleen #1305 bestond
- cluster_keys LIKE `%nos%`/`%nieuwsuur%`/`%anp%`/`%welingelicht%`

**Web (WebSearch):**
1. `Nieuwsuur RIVM westnijlvirus 2026`
2. `Nieuwsuur kritisch RIVM onderzoek corona Van Dissel uitzending kritiek`
3. `inhoudsanalyse NOS Nieuwsuur coronaberichtgeving bronnen experts OMT RIVM onderzoek`
4. `ombudsman Margo Smit analyse coronaberichtgeving NOS 2020 bronnenonderzoek RIVM Van Dissel aandeel Nieuwsuur`
5. `Nieuwsuur reconstructie OMT-adviezen aangepast op verzoek ministerie VWS`
6. `nos.nl nieuwsuur westnijlvirus muggen RIVM deskundige`
7. `Nieuwsuur coronaberichtgeving te volgzaam RIVM OMT kritiek mediakritiek Villamedia "Nieuwsuur"`
8. `Nieuwsuur Van Dissel interview tafelgast RIVM vaste gast corona Nieuwsuur 2020 2021 OMT-voorzitter`
9. `Telegraaf Omtzigt toeslagenaffaire interview 2020 Telegraaf`
10. `Omtzigt Telegraaf kritisch hoofdredactie commentaar Omtzigt NSC Telegraaf relatie pers`
11. `onderzoek mediaberichtgeving toeslagenaffaire kranten bronnen Omtzigt Leijten Trouw RTL inhoudsanalyse`
12. `Telegraaf Afhameren Wouter de Winther Omtzigt kritiek Villamedia OR NRC OR Volkskrant 2024`
13. `"Omtzigt" "tegen De Telegraaf" toeslagen ouders Belastingdienst 2020 OR 2021`
14. `telegraaf.nl Omtzigt toeslagenaffaire` (allowed_domains telegraaf.nl) → API-fout 400: domein niet toegankelijk
15. `Telegraaf anonieme bronnen Omtzigt formatie 2024 "De Telegraaf" Omtzigt huilbuien kritiek journalistiek`
16. `"zegt Omtzigt tegen De Telegraaf"`
17. `"Omtzigt" "in De Telegraaf" interview toeslagen OR Belastingdienst OR "functie elders"`
18. `nos.nl Omtzigt herkent zich niet in beeld emotionele toestand Telegraaf anoniem formatie`
19. `Telegraaf 2019 2020 toeslagenaffaire berichtgeving Omtzigt Kamerlid CDA "Telegraaf" onthulling kinderopvangtoeslag Omtzigt reageert`

**Opgehaald (curl):**
- nos.nl 2617095 (Nieuwsuur 4-6-2026): quote van #7849 letterlijk
- nos.nl 2416816 (via collectie/13889 en /nieuwsuur/artikel/): quote van #7848 letterlijk (bron #1305)
- nos.nl 2380204 (Tegel 2021): quote van #7850 letterlijk
- nos.nl 2403300 (verantwoording reconstructie 2021): methode, geen bruikbare claim over het RIVM als bron
- nos.nl 2343078 (ombudsman NOS 2020): gaat over NOS Nieuws in het algemeen, niet over Nieuwsuur
- nos.nl 2633251 (westnijlvirus, 1-10-2026, uit de doelcontext)
- nos.nl 2520895 (Omtzigt/Plasterk, 18-5-2024) en 2490789 (Omtzigt/Buitenhof, 17-9-2023): geen bewijs voor dit verband
- welingelichtekringen.nl (ANP, 4-3-2024): beide gecontroleerde quotes letterlijk
- hartvannederland.nl, "Omtzigt over emotionele uitbarstingen …" (2-9-2024): De Telegraaf op basis van anonieme ingewijden. Niet ingediend: het ANP-stuk volstaat en dit stuk herhaalt persoonlijke kwalificaties uit anonieme bron.

## Negatieve resultaten (alleen in dit log)

- **Vóór, rel. 1579:** geen bron gevonden die een patroon van RIVM-deskundigen als onbevraagde autoriteit bij Nieuwsuur laat zien. Er is geen inhoudsanalyse van het bronaandeel per programma. De ombudsman-analyse uit 2020 gaat over NOS Nieuws als geheel.
- **Westnijlvirus (doelcontext):** het NOS-bericht van 1-10-2026 brengt het RIVM als enige bron, maar het is een NOS Nieuws-bericht en geen Nieuwsuur-bericht. Ik vond geen Nieuwsuur-item over het westnijlvirus. Niet ingediend.
- **Vóór, rel. 260:** geen bron gevonden die laat zien dat De Telegraaf Omtzigt over de toeslagenaffaire (2019–2021) als bron bracht. telegraaf.nl is voor WebSearch afgesloten (400) en gaf in eerdere rondes een 403. De onthulling lag bij Trouw (Kleinnijenhuis) en RTL (Klein).
- **Overwogen maar niet ingediend:** Joop-stukken over Telegraaf-berichtgeving over Omtzigt (opinie, geen primaire bron); de Hart van Nederland-weergave van het Telegraaf-bericht van september 2024 (persoonlijke kwalificaties uit anonieme bron, voegt niets toe aan #7852).

## Stance-balans

**0 steun / 4 tegen / 0 context / 1 ondergraving** (+ 1 aspect-argument `mechanism`)
- rel. 1579: tegen #7848, #7849, #7850; ondergraving #7847 (op #2339); aspect #7851 (→ mechanisme #6)
- rel. 260: tegen #7852
- Nieuwe bronnen: #2458, #2459, #2460. Hergebruikt: #1305.
