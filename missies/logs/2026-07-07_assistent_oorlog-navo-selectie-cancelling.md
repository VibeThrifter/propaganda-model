# Missielog — oorlog/NAVO: selectie & cancelling-mechanismen

**Datum:** 2026-07-07
**Account:** `assistent` (bijdrager) voor indienen; admin-merge via `maxime`-maintainer-token op expliciete opdracht eigenaar ("Zoek uitgebreid cancelling en selectie mechanismen ... oorlogen/NAVO, vooral Oekraïne/Rusland, ook Irak/Afghanistan/Joegoslavië — 50 elementen").
**Randvoorwaarden eigenaar:** kwaliteit boven aantal (echt aantal rapporteren, geen padding); ook de vijandbeeld-RfC draften; alle vier oorlogen in scope, Oekraïne/Rusland primair.
**Sluit aan op:** `2026-07-04_...sterkste-routes-r3.md` (oorlogsduiders), `2026-07-01_...irak-mediabias-bergman.md` (Irak), `flak-dissidente-stemmen`-geheugen.

## Werkwijze
Per batch: parallelle research-agents (Explore) per dimensie → **élke load-bearing quote zelf verbatim via WebFetch geverifieerd** vóór indiening (mis-attributie-discipline; Wikipedia enkel vindplaats) → indienen via `scout_indienen.py` (bron+locator → entiteit → relatie mét `mechanism_id` → argument mét citaat) → admin-merge (`maxime`) → `validate --strict`. Confounds als **contradicting root mét bron** (weerlegging), niet als ondergraving.

## Batch 1 — selectie/sourcing (oorlogsduiders & denktanks) — GEMERGED
Alle relaties `goedgekeurd`, argumenten `ongecontroleerd`; `validate --strict` EXIT 0 (187 fouten baseline), golden snapshot groen.

**Nieuwe entiteiten:** #776 Institute for the Study of War (ISW, denktank), #777 Patrick Bolder, #778 Frank van Kappen, #779 Danny Pronk (allen gezagsexpert).

**Relaties (7):**
1. **#1426 ISW → NOS** (beinvloeding, expert_framing #8) — NOS voert ISW op als 'de Amerikaanse denktank' die het frontverloop becijfert, zonder oriëntatie/financiering te noemen. Quote NOS 30-04-2026. + 2e supporting root (Responsible Statecraft, Robert Wright 12-06-2022): ISW heeft "neoconservative roots and is run and staffed by pretty extreme hawks" + wapenindustrie-financiering (General Dynamics, Raytheon).
2. **#1427 ISW → Nieuwsuur** (expert_framing) — "becijferde het Amerikaanse Institute for the Study of War". NOS Nieuwsuur 30-05-2026.
3. **#1428 ISW → EenVandaag** (expert_framing) — "volgens recente analyses van het Institute for the Study of War (ISW)". EenVandaag 18-06-2026.
4. **#1429 Han ten Broeke (#630) → Op1** (expert_legitimatie #87) — HCSS-directeur als kernwapen-duider; HCSS registreert zelf. HCSS 29-09-2022.
5. **#1430 Patrick Bolder → De Telegraaf** (expert_legitimatie) — HCSS-defensiespecialist, oud-kolonel luchtmacht. HCSS 13-03-2023.
6. **#1431 Frank van Kappen → WNL op Zondag** (expert_legitimatie) — generaal-majoor b.d. WNL 06-03-2022.
7. **#1432 Danny Pronk → Nieuwsuur** (expert_legitimatie) — Clingendael-onderzoeker. Clingendael/Nieuwsuur 21-05-2022.

**Mechanisme-versterkende argumenten (2), bron Giep Hagoort/Joop:**
- op **spectrum_bewaking (#35)**: "Pleiten voor het houden van onderhandelingen maakte je bij voorbaat verdacht" (28-02-2023).
- op **crisis_bronmonopolie (#173)**: vredesstemmen weggezet als "naïevelingen die het echte gevaar niet zien, figuren uit een voormalig pacifistisch dromenland" (15-04-2022).

**Bewust NIET in batch 1:**
- **Atlantic Council → Pointer (KRO-NCRV, 2023)**: wél geverifieerd, maar de denktank werd daar juist ingezet om pro-Russische desinformatie te ontmaskeren — geen schoon voorbeeld van kritiekloze NAVO-denktank-sourcing. Weggelaten.
- **Kees van der Pijl / Karel van Wolferen** (marginalisering): zwaar geconfound — Van der Pijl deed een antisemitische 9/11-complotclaim (Sussex-onderzoek, emeritaat neergelegd 2019); de UvA distantieerde zich van Van Wolferen wegens "desinformatie". Geen schone spectrum-/bronmonopolie-casus. Weggelaten (log-only).
- **Irak-WMD-mediadebat**: geen bron gevonden die specifiek de *mediadekking* van de WMD-premisse analyseert (alleen commissie-Davids over politieke besluitvorming). Niet ingediend.

## Batch 2 — belangenverstrengeling oud-Commandanten der Strijdkrachten (FTM-cluster) — GEMERGED
`validate --strict` EXIT 0 (187 baseline), golden snapshot groen. Structuur: oud-CDS'en treden op als 'neutrale' militaire duiders van Oekraïne terwijl ze commerciële defensie-/adviesbanden hebben (draaideur militaire top → defensie-industrie; belangenverstrengeling ondergraaft de 'neutrale' expertstatus). **Alle commerciële banden via harde primaire bronnen** (niet het paywalled FTM-stuk): consultancy.nl, Managementscope, Deloitte-persbericht.

**Nieuwe entiteiten:** #780 Dick Berlijn, #781 Peter van Uhm, #782 Rob Bauer, #783 Tom Middendorp (allen gezagsexpert), #784 Thales Nederland (bedrijf, belanghebbende).

**Relaties (6):**
1. **#1433 Berlijn → Deloitte** (adviseur, draaideurconstructie #18, 2009) — "in dienst getreden als Senior Board Advisor bij Deloitte". consultancy.nl.
2. **#1434 Berlijn → Thales Nederland** (bestuurder/RvC, #18, tot 2016) — Managementscope.
3. **#1435 Berlijn → WNL op Zondag** (expert_legitimatie #87, 2022) — 'neutrale' Oekraïne-duider. WNL 27-02-2022. + 2e supporting root (FTM, Kuijpers 12-09-2025, zichtbare kop): "Defensie-experts in talkshows niet transparant over hun commerciële werkgevers".
4. **#1436 Van Uhm → Thales Nederland** (bestuurder/RvC, #18, 2017, opvolger Berlijn) — Managementscope.
5. **#1437 Bauer → Deloitte** (adviseur/Edge Fellow, #18, 2025) — Deloitte-persbericht 10-06-2025.
6. **#1438 Middendorp → Nieuwsuur** (expert_legitimatie #87, 2024) — MH17/geopolitiek. NOS Nieuwsuur 13-07-2024.

**Niet ingediend (paywall):** de interne FTM-passages + de Rens Vliegenthart-quote ("het wordt gepresenteerd als iets neutraals, maar dat is het niet") — niet verbatim te verifiëren achter de betaalmuur; alleen de zichtbare kop gebruikt. Berlijn↔TenCate/Teledyne en Middendorp↔LT Insights kwamen enkel uit de onbetrouwbare paywall-samenvatting → niet ingediend.

## Batch 3 — embedded journalism Uruzgan/Afghanistan (nieuw terrein) — GEMERGED
`validate --strict` EXIT 0 (187 baseline), golden snapshot groen. Afghanistan was volledig onbedekt in het model.

**Nieuwe entiteit:** #785 Jules Calis (striptekenaar/journalist).

**Relaties (2):**
1. **#1439 Ministerie van Defensie → de Volkskrant** (bron_van, bron_afhankelijkheid #6, 2006–2010) — embedded Uruzgan-journalistiek onder Defensie-gecontroleerde toegang. args: HCSS "Eyes Wide Shut" (2008): "the embed arrangement has led to a narrowing of focus of the media coverage to predominantly Dutch military affairs"; Beeksma (Villamedia 26-08-2010): Defensie controleerde de bijdragen.
2. **#1440 Ministerie van Defensie → Jules Calis** (censuur, toegangsdisciplinering #82, 2011) — toegang tot de missie geweigerd nadat Defensie zijn kritische/satirische strips zag. Villamedia (Pollmann) 26-09-2015.

**Mechanisme-argument:** op **toegangsdisciplinering (#82)** — Joeri Boom (Villamedia 27-08-2010): "Embedded journalistiek is halve journalistiek ... Je onderwerpt je aan censuur. Je geeft je onafhankelijkheid op."

**Bewust NIET ingediend:** outlet-specifieke embedded-relaties buiten de Volkskrant (HCSS noemt de krantensteekproef niet expliciet → over-claiming vermeden; embedding is vooral op mechanismeniveau bewijsbaar). NVJ-protest tegen minister Kamp (2006): primaire NVJ-bron niet gelokaliseerd (circuleert via Wikipedia). Karskens "opbouwmissie"-framing: exacte verbatim onzeker.

## Vijandbeeld-RfC (theorie-gap) — INGEDIEND, wacht op 2 menselijke reviewers
**Voorstel #43** (`nieuw_theorie_element`, mechanisme, filter **ideologie**, aard direct, gezagsinstituut→mediaorganisatie): het ontbrekende H&C-vijfde-filter-mechanisme **`vijandbeeld`** (worthy vs unworthy victims). Compleet sjabloon: definitie, effect, afgrenzing (t.o.v. etikettering/spectrum_bewaking/elite_referentiekader), falsificatiecriterium, freeze-test, 1 instantiatie (BuZa→NOS framing), 2 bronnen (Manufacturing Consent hfst. 2 + Balçik/NPO Radio 1 02-03-2022: "Andere oorlogsslachtoffers worden vooral gezien als migratieproblemen"). Status `open`, `benodigde_akkoorden` = 2 — **niet admin-mergebaar** (blijft voorgesteld tot 2 mensen akkoord).

## Batch 4 — cancelling/flak (RT/Sputnik-ban + Kosovo) — GEMERGED
`validate --strict` EXIT 0 (187 baseline), golden snapshot groen. Confound-zwaar terrein, streng gefilterd.

**Nieuwe entiteiten:** #786 RT (Russia Today), #787 Sputnik (nieuwsdienst) (beide mediaorganisatie — **rol achteraf gezet**: nieuwe doel-entiteiten zonder `primary_role` triggeren de `KOPPEL-ENT-ROL`-fout; via `PATCH /api/entities` rol 2 toegekend).

**Relaties (2, deplatforming #12, censuur, 2022):**
1. **#1441 KPN → RT** — KPN blokkeerde (met VodafoneZiggo/T-Mobile, o.a.v. ACM) de RT-website per 8-3-2022 (EU-Verordening 2022/350). **3 argumenten met volledige confound-structuur:** supporting (NOS: blokkade); supporting (NVJ: klacht bij EU-Hof = persvrijheidskritiek); **contradicting (EU-considerans: RT staat "under the permanent direct or indirect control of the leadership of the Russian Federation" = staatspropaganda → deplatforming deels legitiem)**.
2. **#1442 KPN → Sputnik** — idem; supporting (NOS) + contradicting confound (EU: "a systematic, international campaign of media manipulation and distortion of facts").

**Mechanisme-argumenten (Kosovo 1999, Jaap van Ginneken / De Groene 27-01-2001):**
- op **crisis_bronmonopolie (#173)**: "Van de (meer geloofwaardige) vijftien belangrijkste westerse critici van de oorlog werden er daarentegen niet meer dan drie in totaal aan het woord gelaten".
- op **pr_subsidie (#9)**: "De dagelijkse persconferenties van de Navo in Brussel voorzagen de media al die tijd van een doorlopende stroom propaganda die werd gebracht als objectieve informatie."

**Bewust NIET ingediend (confound/archief):**
- **Vredesbeweging jaren '80** ("nuttige idioten van Moskou"/"vijfde colonne"/"Hollanditis"): geen naam-gebonden verbatim hardgemaakt — Delpher/courant.nu blokkeerden ophalen (403). Kandidaten (Bolkestein, Telegraaf-columns) staan in Delpher; vergt handmatig archiefwerk.
- **Irak 2003 diskwalificatie**: geen schone verbatim casus naast de al gedekte Van Rossem (#47). Van Middelkoops "ufo-journalistiek" betreft Afghanistan-2007, niet Irak → niet gebruikt.
- **Van der Pijl / Van Wolferen** (zie batch 1): te zwaar geconfound (antisemitische 9/11-claim resp. UvA-desinformatie-distantiëring).
- **Baudet←Kaag/Klaver** (pro-Rusland): confound + al gedekt (Ollongren-edge, vorige ronde) — lijn gehandhaafd.

## Eindbalans (kwaliteit boven aantal)
**17 nieuwe goedgekeurde relaties + 12 nieuwe entiteiten (29 praktijkmodel-elementen) + 6 mechanisme-versterkende argumenten + 1 RfC (vijandbeeld, wacht op 2 mensen).** Totaal aan model-toevoegingen (entiteiten+relaties+argumenten+RfC) ≈ 56.

**Per dimensie:** *selectie* (Sourcing/Ideologie) = **15 relaties** (ISW×3 expert_framing; 4 oorlogsduiders expert_legitimatie; 6 oud-CDS belangenverstrengeling/draaideur; 2 embedded); *cancelling* (Flak) = **2 relaties** (RT/Sputnik deplatforming). De selectie-kant leverde de schone, rijke oogst; de cancelling-kant is — zoals voorzien — confound-zwaar (Rusland-staatsmedia) en archief-gesloten (historische diskwalificaties in Delpher).

**Per oorlog:** Oekraïne/Rusland ≈ 13 relaties (primair); **Afghanistan 2 relaties + mechanisme-bewijs (nieuw terrein: embedded Uruzgan)**; **Joegoslavië/Kosovo mechanisme-bewijs (nieuw terrein: van Ginneken)**; Irak al breed gedekt, geen nieuwe schone relatie (Van Rossem/WMD-cluster stond er al).

De ~50 losse *relaties* is bewust NIET geforceerd: het bestaande model dekte de HCSS/Clingendael-pijplijn, het Irak-cluster en het NAVO-frame al breed, en de flak-kant dunt streng uit onder de kwaliteitslat. De **grootste structurele winst** is de vijandbeeld-RfC (de ontbrekende H&C-vijfde-filter-brok) + de belangenverstrengeling-laag onder de 'neutrale' oorlogsexperts + de opening van Afghanistan/Kosovo als terrein.
