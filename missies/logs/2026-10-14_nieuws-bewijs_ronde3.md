# nieuws-bewijs — 2026-10-14, ronde 3

- Brief: `missies/nieuws_bewijs_brief.md`, blob-hash **08fb9268298d**
- Account: `nieuws-bewijs` (bijdrager). Alles landt `voorgesteld`.
- Voorregel: `GET /api/agent/reeds_gereageerd` → al gereageerd op 630, 1627, 2134, 2322, 2339, 2635, 3089. Geen van de geraakte parents (2164, 3063) staat erin.
- Geclaimd: `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` → doel 216 (`relatie:168`) en doel 126 (`relatie:1963`).
- Geen 429, geen LinkedIn gebruikt (bewijsdoelen over media-verbanden, geen loopbaanonderzoek).

## Doel 216 — `relatie:168` Wiardi Beckman Stichting → de Volkskrant (expert_framing) — status **klaar**

**Wat het model beweert.** Rel. 168, `beinvloeding`, mechanisme 8 `expert_framing` ("door elites/sponsors gefinancierde denktanks leveren schijnbaar objectieve experts … die media als 'neutraal' opvoeren"), active_from 1945. Als het verband klopt, moet de Volkskrant WBS-analyses of -medewerkers als neutrale deskundigheid brengen, en dat herhaaldelijk. Ertegen pleit dat de Volkskrant de WBS als partijbureau aanduidt, of dat het om losse berichten gaat.

**Bestaand bewijs.** Arg. #2164 (supporting, geverifieerd, A1 `klopt` v3): bron #1166 = de pagina "Van Waarde in de media" op wbs.nl. Het citaat "Denktank van de PvdA wil nieuw politiek kompas" staat er letterlijk (een Volkskrant-kop van 14-02-2013). Op de pagina staan ook twee andere Volkskrant-items uit februari 2013: "De PvdA wil linksere koers" en een opiniestuk van Emile Roemer.

**Neutrale zoekvraag:** hoe bracht de Volkskrant de Wiardi Beckman Stichting en haar medewerkers, over meerdere jaren?

Zoekopdrachten (letterlijk):
1. WebFetch `https://www.wbs.nl/publicaties/van-waarde-de-media`: de pagina met het citaat van #2164.
2. WebSearch `Wiardi Beckman Stichting volkskrant.nl`: geen Volkskrant-artikelen, alleen WBS-documenten.
3. WebSearch `"Wiardi Beckman Stichting" Volkskrant rapport directeur`: geen Volkskrant-artikelen. Wel een verwijzing naar het WBS-jaarverslag 2013.
4. WebSearch `volkskrant "Wiardi Beckman Stichting" wetenschappelijk bureau PvdA` (allowed_domains volkskrant.nl): **400**, het domein is niet toegankelijk voor de zoekdienst.
5. WebSearch `volkskrant WBS denktank PvdA` (allowed_domains volkskrant.nl): **400**, idem.
6. WebSearch `"Volkskrant" "Wiardi Beckman" denktank PvdA opinie 2024`: geen Volkskrant-stuk uit 2024.
7. WebSearch `wetenschappelijke bureaus politieke partijen media aandacht onderzoek denktanks Nederland`: geen inhoudsanalyse van mediagebruik van partijbureaus.
8. Download en tekstextractie van de WBS-jaarverslagen 2023 (`wbs.nl/.../Jaarverslag 2023 WBS definitief.pdf`) en 2013 (`wbs.nl/sites/default/files/2017-09/wbs_jaarverslag_2013.pdf`), gezocht op "volkskrant"/"media". Het jaarverslag 2023 noemt de Volkskrant niet. Het jaarverslag 2013 noemt de column van Cuperus, een opiniestuk van Hurenkamp in de Volkskrant (22-10-2013), een Volkskrant-recensie van een WBS-boek en een stuk van Marcel van Dam.
9. WebSearch `René Cuperus column Volkskrant Wiardi Beckman Stichting medewerker`: een Joop-stuk uit 2026 over een Volkskrant-column van Cuperus. Die column is van na zijn WBS-tijd, dus niet gebruikt.
10. WebSearch `"Wiardi Beckman Stichting" site:volkskrant.nl` (extended): geen Volkskrant-hits.
11. WebSearch `"Monika Sie" Volkskrant interview WBS directeur PvdA kritiek`: geen Volkskrant-interview gevonden.

**Vondsten en indieningen**
- Bron **#2790**: WBS-jaarverslag 2013 (primair voor wat de WBS over haar eigen medewerkers zegt; voorgesteld `primair`/`nl_systeem`, cluster `wbs`).
- Argument **#10179**: ondergraving (contradicting reply) op #2164. Het geciteerde Volkskrant-kopje noemt de WBS juist "denktank van de PvdA", en expert_framing vraagt dat het medium haar als neutraal opvoert. Verder is het één bericht uit 2013 (geen patroon), en de bron is de WBS-persoverzichtpagina zelf.
- Argument **#10180**: supporting root op rel. 168. Volgens het jaarverslag 2013 schreef senior wetenschappelijk medewerker René Cuperus in 2013 tweewekelijks een column voor de Volkskrant, op persoonlijke titel. Citaat letterlijk uit de pdf: "René Cuperus schrijft tweewekelijks op persoonlijke titel een column voor de Volkskrant."

**Negatieve resultaten.** Ik vond geen Volkskrant-artikel waarin de WBS of een WBS-medewerker als neutrale of onafhankelijke deskundige wordt opgevoerd. Ik vond ook geen tegenbewijs in Volkskrant-berichtgeving zelf, zoals kritische berichtgeving over de WBS. Het Volkskrant-domein was voor de zoekdienst geblokkeerd (400), en het archief is niet doorzocht. Ik vond geen inhoudsanalyse naar het mediagebruik van partijbureaus.

**Mechanisme.** expert_framing ("als 'neutraal' opvoeren", sponsor-gefinancierd) past slecht bij een openlijk aan een partij verbonden bureau. Ik zag geen bestaand mechanisme dat duidelijk beter past, en heb daarom geen aspect-argument ingediend. Dit staat in het verslag.

## Doel 126 — `relatie:1963` Geert Wilders → NOS (politicus_als_ideoloog) — status **klaar**

**Wat het model beweert.** Rel. 1963, `framing`, mechanisme 66 `politicus_als_ideoloog` ("politici presenteren beleidsopties als de enige realistische keuze (TINA); dat frame neemt de verslaggever over als gezaghebbende politieke realiteit"), active_from 2015. Als het verband klopt, neemt de NOS Wilders' frame (asiel als crisis) over zonder toeschrijving of tegenstem. Ertegen pleit berichtgeving die zijn woorden toeschrijft en tegenstemmen opvoert.

**Bestaand bewijs.** Arg. #3063 (supporting, ongecontroleerd; A1 v2 `twijfel`: "de causale lijn naar nos.nl ontbreekt"). Bron #1814 is De Groene/UvA, "Van probleem naar 'crisis'" (22-10-2025). Ik las de Wayback-kopie: de vier citaten staan er letterlijk. Hetzelfde artikel citeert oud-NRC-ombudsman De Jong: Wilders heeft "de laatste jaren juist minder greep op de media". NOS-hoofdredacteur Van Cann zegt er: "Dat is wat de journalistiek doet, en zeker de NOS: wij vertellen wat er gebeurt."

**Neutrale zoekvraag:** hoe bracht de NOS Wilders' asielstandpunten en het woord "asielcrisis"? Met of zonder toeschrijving, en met of zonder tegenstem?

Zoekopdrachten (letterlijk):
1. curl `https://www.groene.nl/artikel/van-probleem-naar-crisis`: paywall. Daarna curl van de Wayback-kopie `web.archive.org/web/20260104143740/...`: volledige tekst.
2. WebSearch `NOS term asielcrisis gebruik redactie uitleg woordkeuze`: NOS-berichten 2517804, 2537060, 2615463 en Nieuwsuur 2517931.
3. WebSearch `onderzoek berichtgeving NOS over Wilders PVV aandacht inhoudsanalyse`: alleen EUR-scripties over kranten en NOVA/Netwerk, geen NOS-specifieke inhoudsanalyse.
4. WebSearch `NOS asieltsunami Wilders aanhalingstekens`: geen bron die laat zien dat de NOS "asieltsunami" overnam. Wel een Joop-stuk uit 2016 over een NOS-interview met Wilders.
5. WebSearch `NOS factcheck Wilders asiel cijfers klopt`: geen NOS-factcheck van Wilders' asielcijfers. Wel NOS 2582876 (Algemene Politieke Beschouwingen 2025).
6. curl van NOS 2517931 (Nieuwsuur, 23-04-2024, deskundigen twijfelen aan het crisisplan): noemt de PVV, maar niet Wilders, dus niet gebruikt (v3-specificiteit).
7. curl van NOS 2537060 (14-09-2024, kabinetsplan asielcrisis): noemt Wilders en de PVV niet, dus niet gebruikt.
8. curl van NOS 2517804 (22-04-2024), NOS 2582876 (17-09-2025) en Joop 2016.
9. curl van NOS Nieuwsuur 2159181 (feiten en cijfers immigratie): geen bruikbare tekst opgehaald.

**Vondsten en indieningen**
- Bron **#2791**: NOS, "Wilders kritisch over migratie, partijen verwijten hem gebrek aan daadkracht" (17-09-2025), cluster `nos`.
- Bron **#2792**: NOS, "Plan op formatietafel: 'Asielcrisis' uitroepen om strengere maatregelen" (22-04-2024), cluster `nos`.
- Bron **#2793**: Joop (BNNVARA), "NOS durft geen kritische vraag aan Wilders te stellen" (22-02-2016), voorgesteld `opinie`, cluster `joop`.
- Argument **#10181**: ondergraving op #3063. De bron schrijft de asielnadruk en het woord "asielcrisis" toe aan politici en media in het algemeen, en legt geen lijn van Wilders naar de NOS. Het citaat van de hoofdredacteur gaat over "de politiek". Het mechanisme vraagt een TINA-frame. Dezelfde bron citeert De Jong over "minder greep op de media".
- Argument **#10182**: contradicting root. In het NOS-bericht van 17-09-2025 over Wilders' betoog kwamen de kritiek van Jetten, Timmermans en Dijk aan het woord.
- Argument **#10183**: contradicting root. De NOS bracht op 22-04-2024 'asielcrisis' tussen aanhalingstekens als plan van de formerende partijen (onder wie de PVV van Wilders), toegeschreven aan "bronnen rond de formatie".
- Argument **#10184**: supporting root. Volgens Joop (22-02-2016) stelde de NOS Wilders in een exclusief interview geen kritische vragen (toegeschreven opinie).

**Negatieve resultaten.** Ik vond geen NOS-bericht waarin "asieltsunami" of "asielcrisis" zonder toeschrijving als eigen woord van de NOS met Wilders als herkomst staat. Ik vond geen inhoudsanalyse specifiek naar NOS-berichtgeving over Wilders, en geen NOS-ombudsmanoordeel over deze kwestie. Ook niet doorzocht: het archief van het NOS Journaal (video), en Delpher en LexisNexis (niet toegankelijk).

**Mechanisme.** politicus_als_ideoloog beschrijft TINA-framing ("geen alternatief"). Het asiel-als-crisis-frame van een oppositieleider is in de bronnen geen TINA-frame. Ik zag geen bestaand mechanisme dat duidelijk beter past (politicus_als_bron gaat over bronafhankelijkheid, media_agendering loopt de andere kant op). Daarom heb ik geen aspect-argument ingediend. Dit staat in het verslag.

## Stance-balans van de ronde

- Steun: **2** (#10180, #10184)
- Tegen (roots met bron): **2** (#10182, #10183)
- Context: **0**
- Ondergraving: **2** (#10179, #10181)
- Nieuwe bronclusters: **3** (`wbs` met het jaarverslag 2013, `nos`, `joop`). De twee NOS-berichten vallen in één cluster. Hercitaties: 0.
- 409/400 bij het indienen: geen. Wel twee keer 400 van de zoekdienst (volkskrant.nl geblokkeerd).
