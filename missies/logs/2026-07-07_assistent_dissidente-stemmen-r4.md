# Missielog — dissidente stemmen, ronde 4 (breed uitgekamd, 3 onderzoeksgolven)

**Datum:** 2026-07-07
**Account:** `assistent` (bijdrager) voor indienen; merge via admin (`maxime`-maintainer-token) op expliciete opdracht eigenaar ("Zoek nog 50 van dit soort gevallen uit" → keuze *kwaliteit boven aantal* + *via admin, in batches*).
**Sluit aan op:** `2026-07-05_...flak-dissidente-stemmen.md` en `2026-07-07_...dissidente-stemmen-r3.md`.

## Opdracht & werkwijze
Eigenaar vroeg ~50 extra flakcasussen van het type "publieke stem tegen de establishment-consensus wordt uitgesloten/gecancelled/gedebanked/vervolgd". Twee door de eigenaar gekozen randvoorwaarden: **kwaliteit boven aantal** (geen padding, echt aantal rapporteren) en **via admin, in batches**.

Aanpak: **drie onderzoeksgolven** met in totaal 14 parallelle research-agents (Explore), elk op een aparte flak-dimensie, met de volledige dedup-lijst en de scope-regel meegegeven. Elke teruggemelde casus is door mijzelf **verbatim geverifieerd via WebFetch** vóór indiening (mis-attributie-discipline; Wikipedia enkel als vindplaats → door naar de onderliggende bron). Indienen via `scripts/scout_indienen.py` (bron+locator → entiteit → relatie mét `mechanism_id` → argument mét citaat); mergen via scoped admin-scripts (`maxime`); `validate --strict` per batch.

## Resultaat: 20 nieuwe, geverifieerde, in-scope, niet-duplicerende flakrelaties
Alle drie batches gemerged; `validate_model.py --strict` **EXIT 0**, golden snapshot groen, geen fouten boven baseline. Confounds consequent gemodelleerd als **contradicting root mét bron** (weerlegging, geen ondergraving) — 9 van de 20 relaties dragen zo'n eerlijk tegenargument.

### Batch 1 (rel. #1403–1411, entiteiten #757–766, bronnen #1018–1026, argumenten #1942–1955)
1. **YouTube → Lange Frans** (deplatforming, 2020) — kanaal (59 video's) verwijderd; confound: YouTube-regels tegen "schadelijke complottheorieën". NOS.
2. **LinkedIn → Wybren van Haga** (deplatforming, 2020) — account verwijderd na corona-uitingen; confound: gebruiksvoorwaarden. NOS.
3. **YouTube → Blckbx** (demonetisatie, 2021→uitspraak 2024) — uit Partner Program; confound: rechter achtte weigering rechtmatig (ECLI:NL:RBAMS:2024:4917).
4. **PayPal → Stichting Voorzij** (debanking, 2022) — cross-provider patroon naast de bestaande Bunq-edge. Eigen verklaring (grijs).
5. **Gerrit Zalm → Pim Fortuyn** (etikettering, 2002) — "een gevaarlijke man" (17 mrt 2002). DNPP/RUG.
6. **Regionaal Tuchtcollege → huisarts** (beroepssanctie, 2025) — berisping mede om corona-uitlatingen; confound: ~25× off-label ivermectine. ECLI:NL:TGZRZWO:2025:69.
7. **Ministerie J&V → Yasmina Haifi** (werkgeverssanctie, 2014) — voorwaardelijk ontslag om privétweet; rechter: te zwaar, viel onder vrijheid van meningsuiting. Omroep West.
8. **Ferris van H. → Leeuwarder Courant** (SLAPP/juridische_dreiging, ~2023) — 7 advocaten, miljoenenclaims. Amnesty NL.
9. **Stichting FIO → De Telegraaf** (civiele_inperking, 2025) — kort geding om column Marbe; confound: rechter vond onrechtmatige FIO-Hamas-suggestie. Villamedia.

### Batch 2 (rel. #1414–1421, entiteiten #767–772, bronnen #1030–1037, argumenten #1960–1969)
10. **Meta (Facebook) → Stichting Viruswaarheid** (deplatforming, 2020) — pagina's 'Nee tegen 1.5 meter'/'viruswaanzin' verwijderd; confound: rechter achtte verwijdering toegestaan (ECLI:NL:RBAMS:2020:4966).
11. **Thuiszorg Naborgh → Follow the Money** (SLAPP, 2019) — publicatieverbod + dwangsommen geëist; alle vorderingen afgewezen. FTM/vonnis.
12. **Rabee Hammi (Accuraat) → Follow the Money** (SLAPP) — sommatie + kort geding; FTM won. Villamedia.
13. **TaXeCo → NRC** (SLAPP, 2022) — rectificatie-eis afgewezen (ECLI:NL:RBAMS:2022:6753). IT en Recht.
14. **Kajsa Ollongren → Thierry Baudet** (etikettering, 2018) — "gaat verder waar Wilders ophoudt" (Daleslezing). NOS.
15. **Marcel van Dam → Pim Fortuyn** (etikettering, 1997) — "een buitengewoon minderwaardig mens" (Het Lagerhuis). HP/De Tijd.
16. **Openbaar Ministerie → Gerard Reve** (strafvervolging_uiting, 1966–1968) — Ezelproces (godslastering), vrijgesproken; de vervolging zelf was de flak. Literatuurmuseum.
17. **De Waalboog → zorgmedewerkster** (werkgeverssanctie, 2021) — ontbinding na corona-/vaccinatieposts; confound: rechter onderscheidde beschermde algemene waarschuwingen van beledigende posts ("genocide"/"oorlogsmisdadigers"). ECLI:NL:RBGEL:2021:4701.

### Batch 3 (rel. #1422–1424, entiteiten #773–775, bronnen #1038–1040, argumenten #1970–1973)
18. **Paul Rosenmöller → Pim Fortuyn** (etikettering, 2002) — "Dit is niet gewoon rechts, maar extreem-rechts" (11 feb 2002). DNPP/RUG (citeert NRC).
19. **Geert Mak → Ayaan Hirsi Ali** (etikettering, 2005) — Submission vergeleken met Goebbels' *Der Ewige Jude*; confound: Mak positioneerde het pamflet zelf als waarschuwing tégen demonisering. DBNL (primaire tekst).
20. **NL PLAN → Follow the Money** (SLAPP, 2025) — verwijdering/rectificatie geëist over China-artikel; vorderingen afgewezen (ECLI:NL:RBAMS:2025:6822).

### Verdeling per dimensie
Platform-deplatforming (4), debanking (1), etikettering/publieke_aanval (5), beroepssanctie (1), werkgeverssanctie (2), SLAPP/juridische_dreiging (5), civiele inperking (1), strafvervolging_uiting (1) = **20**.

## Eerlijke bevinding over het aantal (kwaliteit boven aantal)
De ~50 is **niet** gehaald, en dat is de juiste uitkomst binnen de gekozen kwaliteitslat. Het model dekte de dissident-stem-flak al breed (85→nu 105 flakrelaties). Elke golf leverde dalende, sterker geconfoundde oogst: veel populaire "cancel"/"censuur"-claims blijken bij verificatie **buiten scope** (wangedrag/#MeToo/geweld/ordeverstoring), **zelf-terugtrekking** i.p.v. drop, **niet-Nederlands**, of **al gedekt**. Padding met zwakke of geconfoundde gevallen is bewust nagelaten; de 20 hierboven zijn de casussen die de verbatim-verificatie én de scope-toets doorstonden.

## Bewust NIET ingediend (met reden)
- **Cultuur-/kunstsector:** vrijwel niets schoon buiten het al gedekte — Douwe Bob/Fresku/Tim Douwsma/Goldband/Pim Lammers = zelf-terugtrekking; Appa/Boef/Akwasi/Lil Kleine = wangedrag/haatuitingen; Yohay Sponder/Azealia Banks/Lahav Shani = niet-Nederlands.
- **AIVD/NCTV → "anti-institutionele beweging"** (aangehouden): zwaar confound (dienst dekt zich in met indirect-geweldsargument) + diffuus doel (geen schone entiteit) — het archetypische propagandamodel-mechanisme, maar niet als schoon knooppunt te modelleren.
- **Baudet ← Kaag / Klaver / Sjoerdsma** (2022): geopolitieke confound (pro-Rusland-standpunt) + peer-parlementair debat; doel bovendien al gedekt (Ollongren-edge).
- **GeenStijl-adverteerdersboycot** (2017): trigger was seksisme/aanstootgevende toon, niet een mening-tegen-consensus; atypische machtsverhouding (aangejaagd door gevestigde kranten) → buiten scope.
- **Diverse deplatformings met zware confound:** ~90 QAnon-accounts/Twitter (diffuus + QAnon-coördinatie), Identitair Verzet/Voorpost ("gewelddadig extremisme"), Baudet/TikTok (betaald bereik).
- **SLAPP-dubbels/onverifieerbaar:** Dulkadir→FTM/Parool/AT5 (amnesty-bron al geregistreerd, source-dup), Max van der Werff→De Groene (omgekeerde richting: activist klaagt pers aan).
- **Historisch zonder mainstream-verbatim:** Bolkestein←Van Mierlo (bracket-fragment, geen schoon citaat), Melkert→Fortuyn "charlatan" (alleen partijdig archief), vredesbeweging jaren '80 "vijfde colonne" (geen naam-gebonden verbatim — vergt Delpher), Grapperhaus "wappie" (alleen parafrase).

## Kansrijke vervolgroutes (indien later gewenst)
Delpher-krantenarchief (naam-gebonden verbatims: vredesbeweging '80, Bolkestein '91), lokale gemeenteraden die gesubsidieerde optredens schrappen (raadsvragen als vindplaats), Grapperhaus-"wappie" via het corona-enquête-transcript. Een zuiverder mechanisme `platform_inhoudsmoderatie` (i.p.v. `deplatforming` #12 hergebruiken) blijft mogelijk via RfC (twee menselijke reviewers).
