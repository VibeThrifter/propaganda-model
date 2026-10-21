# Onbewaakte ronde — aanklager-agent · ronde4 · 2026-10-21

- Brief: `missies/aanklager_brief.md` (blob `b985acb45edc`)
- Account: `aanklager-agent`
- Gestart: 2026-10-21T12:57:38

## Sessie-uitvoer

```

## Ronde-log (aanklager-agent, ronde 4, 2026-10-21)

- Brief-blob-hash: `b985acb45edc`
- Voorregel: `GET /api/agent/reeds_gereageerd` (12:58) → 92 id's (t/m #11939). Geen van de twaalf gekozen argumenten stond erin. Overgeslagen als eigen werk: #11799.

### Zoekopdrachten (letterlijk, in volgorde, 12:58–13:02)

Database / lokaal:
1. `python3 scripts/automatische_beoordeling.py --open-a2` → 115 open. Gekozen: de twaalf nieuwste die niet van mij zijn: #11692, #11691, #11690, #11688, #11687, #11686, #11685, #11680, #11677, #11675, #11674, #11673.
2. SQL per relatie (8765, 8766, 8768, 8770): `select r.id, es.name, et.name, r.relation_type, m.name, r.active_from, r.active_until, r.status, r.description from relations r … where r.id=?`.
3. SQL per argument: `select id,claim,reasoning,stance,property,property_value,relation_id from arguments where id=?` + citaties met bron en `source_locations.location`, + `select … from arguments where parent_argument_id=?` (geen bestaande reacties).
4. SQL: `select id,stance,property,status,substr(claim,1,140) from arguments where relation_id in (8770,8765,8766,8768) and parent_argument_id is null` (broers: #11667–#11693) en de reacties daarop (geen).

Web (curl op Wayback `id_`-kopieën, WebFetch op web.archive.org wordt geweigerd):
5. `https://web.archive.org/web/20261020005322id_/https://www.nrc.nl/nieuws/2026/10/19/hoe-de-voedingsindustrie-ruim-baan-krijgt-om-tegen-de-kindermarketingwet-te-lobbyen-a4938878` → grep `fnli|hartstichting|gezondheidsfonds|gezonde generatie|online|economische zaken|herhaling|30 juni|VBZ|ontmoeting`; alle citaten van #11673/#11674/#11675/#11680 letterlijk teruggevonden; FNLI-mails over productielijnen/kosten; "De feitelijke invloed van de FNLI-lobby is moeilijk vast te stellen"; VWS: "onvolledig beeld … ook mondelinge contacten".
6. `https://web.archive.org/web/20240604022450id_/https://nos.nl/artikel/2300867-minister-kaag-betreurt-weigering-gasten-bij-cidi-bijeenkomst` → citaat #11685 letterlijk; "Ze overwoog de bijeenkomst af te zeggen, maar besloot dat niet te doen, zodat de weigering in de bijeenkomst aangekaart kon worden."
7. `https://web.archive.org/web/20241218183342id_/https://www.nrc.nl/nieuws/2019/09/08/28120175-a3972594` → citaten #11686/#11687 letterlijk; "het CIDI organiseert het gesprek"; BZ: uitsluiting "principieel onjuist"; Hamburger: "politieke inschatting".
8. `https://web.archive.org/web/20260615071851id_/https://jonet.nl/minister-kaag-trok-uitnodigingen-terug-na-druk-van-het-cidi/` → citaat #11688 letterlijk.
9. `https://web.archive.org/web/20210630075923id_/https://jonet.nl/cidi-in-open-brief-tegen-kaag-ga-niet-naar-durban-iv/` → 30 juni 2021, citaat #11690 letterlijk.
10. `https://web.archive.org/web/20261019234720id_/https://www.tweedekamer.nl/kamerstukken/kamervragen/detail?id=2021Z12808&did=2021D28064` (gzip) → ingezonden 6 juli 2021, antwoord 7 juli 2021; citaten #11691/#11692 letterlijk; CIDI niet als reden genoemd. (Vraag 3 noemt dat NL ook Durban II en III oversloeg — geen influence-claim op dat punt in de boom, dus niets ingediend.)
11. WebFetch `https://www.foodwatch.org/nl/current-nieuws/ministerie-gaf-voedingsindustrie-vooraf-al-inzage-tekst-wet-tegen-kindermarkering` → 14-10-2026; citaat #11677 staat erin; het stuk noemt EZ/mkb/regeldruk niet; VBZ alleen bij de toezending van de wettekst.

### Per claim: anker, route, resultaat

| Arg | Doel (relatie) | Stance | Route | Aangemaakt |
|---|---|---|---|---|
| #11686 | rel 8770 CIDI → Kaag (lobbyt, lobbyist_naar_politicus), property influence | supporting | **ondergraving** (`non_sequitur`): gastheer weert gasten bij eigen bijeenkomst ≠ invloed op beslissing van de minister | reply **#11950**, certificaat `aangevallen` (#11992) |
| #11677 | rel 8766 VBZ → VWS (departementale_lobby), property influence | supporting | **ondergraving** (`correlatie_als_causatie`): citaat noemt de branche, niet de VBZ; NRC noemt ook de EZ/mkb-route | reply **#11951**, certificaat `aangevallen` (#11993) |
| #11692 | rel 8770 | contextual | overleefd | certificaat #11994 |
| #11691 | rel 8770 | supporting | overleefd | certificaat #11995 |
| #11690 | rel 8770 | supporting | overleefd | certificaat #11996 |
| #11688 | rel 8770 | contextual | overleefd | certificaat #11997 |
| #11687 | rel 8770 | contextual | overleefd (NOS: voorzitter, NRC: directeur — geen inhoudelijk verschil) | certificaat #11998 |
| #11685 | rel 8770 | supporting | overleefd | certificaat #11999 |
| #11680 | rel 8768 Hartstichting → VWS | supporting | overleefd | certificaat #12000 |
| #11675 | rel 8766 VBZ → VWS | supporting | overleefd | certificaat #12001 |
| #11674 | rel 8765 FNLI → VWS, property influence | contradicting | overleefd | certificaat #12002 |
| #11673 | rel 8765 FNLI → VWS, property influence | supporting | overleefd (tegenroute staat al als #11674) | certificaat #12003 |

Geen nieuwe bronnen, entiteiten of relaties aangemaakt. Geen 429. LinkedIn niet gebruikt (geen persoons- of loopbaanonderzoek nodig: de claims gaan over gedocumenteerde contacten, de bronnen zijn krant en Kamerstuk).

### Negatieve resultaten (alleen hier)
- WebFetch op web.archive.org geweigerd; curl op de `id_`-kopieën wel gelukt.
- Geen tegenbron gevonden voor de tien gecertificeerde claims (data, citaten en partijen kloppen in alle bronnen).

### Stance-balans van de ronde
0 weerleggingen / 2 ondergravingen / 10 `overleefd` / 0 `onbeslist`. Als modelbijdrage: 0 steun / 2 tegen / 0 context.
Volgende ronde: verder op de open A2-lijst vanaf #11665 (resterend ≈102).
Ronde 4 is klaar. Van de open tegenspraaklijst (115 open) heb ik de twaalf nieuwste behandeld: twee kregen een ondergraving, tien het certificaat `overleefd`. Mijn eigen #11799 heb ik overgeslagen. Geen van de twaalf stond in de lijst van argumenten waarop ik al reageerde. Alles wat ik indiende staat op `voorgesteld`. Ik heb geen statussen gezet en niets gemerged.

**Ondergravingen** (certificaat `aangevallen`):
- **#11950 op #11686**, verband 8770 (CIDI → Kaag), bezwaar `non_sequitur`. Het CIDI organiseerde de bijeenkomst van 8 september 2019 zelf en weerde vier gasten van de minister. Het ministerie wees die uitsluiting af en Kaag ging toch, om de weigering daar aan te kaarten (NRC en NOS). Dat het CIDI als gastheer zijn gastenlijst bepaalde, zegt niets over invloed op een beslissing of standpunt van de minister.
- **#11951 op #11677**, verband 8766 (VBZ → VWS), bezwaar `correlatie_als_causatie`. Het VWS-citaat bij Foodwatch noemt de bakkerijen en chocoladeproducenten, niet de VBZ. NRC schrijft bovendien dat VWS via Economische Zaken gewaarschuwd werd voor de regeldruk voor het mkb. De genoemde reden past dus ook bij die andere route.

**`overleefd`**: #11692, #11691, #11690, #11688, #11687 en #11685 (CIDI → Kaag), #11680 (Hartstichting → VWS), #11675 (VBZ → VWS), en #11674 en #11673 (FNLI → VWS). Bij alle tien heb ik de bron zelf gelezen: NRC van 2019 en 2026, NOS, twee Jonet-artikelen, het Kamerantwoord 2021Z12808 en Foodwatch. Elk citaat staat er letterlijk in, en ook de datums en partijen kloppen.

Ik heb geen nieuwe bronnen, entiteiten of relaties aangemaakt, geen 429 gekregen en LinkedIn niet gebruikt. WebFetch weigert web.archive.org; de archiefkopieën heb ik met curl opgehaald.

**Stance-balans:** 0 weerleggingen, 2 ondergravingen, 10 `overleefd`, 0 `onbeslist`. Als modelbijdrage is dat 0 steun, 2 tegen, 0 context.

Het log staat in `missies/logs/2026-10-21_aanklager-agent_ronde4.md`. De volgende ronde begint bij #11665; er staan dan nog ongeveer 102 argumenten open.

```

## Runner-metadata

- Exit-code: 0
- Duur: 259.3 s
- Oogst (edit_log-delta van `aanklager-agent`): 14
- Beëindigd: 2026-10-21T13:01:57
