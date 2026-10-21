# Onbewaakte ronde — aanklager-agent · ronde1 · 2026-10-19

- Brief: `missies/aanklager_brief.md` (blob `b985acb45edc`)
- Account: `aanklager-agent`
- Gestart: 2026-10-19T12:16:37

## Ronde-verslag (door de sessie geschreven)

- **Brief:** `missies/aanklager_brief.md`, blob `b985acb45edc`.
- **Account:** `aanklager-agent`.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` opgehaald om 12:16. Er stonden 73 id's in (t/m 11036); geen van de behandelde id's stond erin. Geen 409, geen 429.
- **Wachtrij:** `python3 scripts/automatische_beoordeling.py --open-a2` gaf 90 argumenten. 5 daarvan zijn van mijzelf (7840, 7949, 9740, 9741, 10365) en sloeg ik over (eigen werk → 403). Ik behandelde de 12 oudste van andere auteurs: 11053, 11056, 11057, 11092–11097, 11101, 11102 en 11127. De overige 73 (11128 t/m 11288) zijn voor een volgende ronde.

### Zoekopdrachten (letterlijk)

**Database (12:16–12:18):**
1. `python3 scripts/automatische_beoordeling.py --open-a2`
2. `GET /api/agent/reeds_gereageerd`
3. `select a.id, a.stance, a.property, a.property_value, a.claim, a.reasoning, r.id, es.name, et.name, r.relation_type, m.name, r.active_from, r.active_until, r.description, r.status from arguments a left join relations r … where a.id in (11053,11056,11057,11092,11093,11094,11095,11096,11097,11101,11102,11127)`
4. `select c.argument_id, c.quote, s.id, s.title, (select group_concat(location,' ') from source_locations …) from citations c join sources s … where c.argument_id in (…dezelfde 12…)`
5. `select argument_id, fase, verdict, door from immuun_oordelen where argument_id in (…)` en `select id, parent_argument_id, contributed_by, stance from arguments where parent_argument_id in (…)`: alleen A1 `klopt` van `bronchecker`, nog geen certificaten of reacties.
6. `select … from arguments where contributed_by='aanklager-agent' and parent_argument_id is not null order by id desc limit 2` (vorm van eerdere ondergravingen).

**Web (12:18–12:21, curl → tekst):**
- `nos.nl/artikel/2160892-facebook-gaat-ook-in-nederland-nepnieuws-aanpakken`: 2 maart 2017; Patrick Walker (hoofd media Facebook Europa) zegt dat NU.nl en Nieuwscheckers gaan factchecken.
- `nos.nl/l/2328458`: 26 maart 2020; AFP en DPA leveren Nederlandse factcheckers; "Nu.nl ging tot november vorig jaar door".
- `nos.nl/artikel/2584891-rechter-instagram-en-facebook-moeten-algoritmevrije-optie-krijgen`: 2 oktober 2025; zaak aangespannen door Bits of Freedom; dwangsom 100.000 euro per dag, max 5 miljoen.
- `consumentenbond.nl/nieuws/2023/consumentenbond-en-dps-winnen-baanbrekende-privacyzaak-tegen-facebook-en-starten-nieuwe-zaak`: 15 maart 2023; "De Consumentenbond en DPS starten een tweede rechtszaak tegen Facebook."
- `dutchnews.nl/2008/05/free_paper_owner_invests_in_te/`: 28 mei 2008; citaat letterlijk terug.
- `nieuws.nl/algemeen/20210304/techondernemer-schenkt-d66-miljoen-euro-pvdd-krijgt-35-ton`: 4 maart 2021 (ANP); beide bedragen letterlijk terug.
- `2024.bitsoffreedom.nl/en/supporters-and-finances/`: citaat over Luminate letterlijk terug.
- `rechtspraak.nl/…/gerechtshof-amsterdam/nieuws/2026/03/dwangsommen-tot-10-miljoen-euro-voor-aanpassing-facebook-en-instagram`: 10 maart 2026; "verhoogt het maximum van de dwangsommen naar 10 miljoen euro … Het hof achtte deze prikkel onvoldoende".
- `gatesfoundation.org/about/committed-grants/2021/11/inv031631`: OCTOBER 2021, 37 maanden, $4,627,240.
- curl `gatesfoundation.org/-/media/files/bmgf-grants.csv`, dan `grep -i "European Journalism Centre"`: OPP1066334 (2012-11) is de vroegste EJC-grant.

### Per claim

| Anker (supporting) | Doel | Route | Aangemaakt |
|---|---|---|---|
| 11127 | rel 8442 Bits of Freedom → Meta (oppositie) | **ondergraving** (`citaat_dekking`) | argument **11291**; certificaat `aangevallen` 11152 |
| 11053 | rel 8410 Luminate → Bits of Freedom | `overleefd` | 11153 |
| 11056 | rel 8412 Gates Foundation → European Journalism Centre | `overleefd` | 11154 |
| 11057 | rel 8412 Gates Foundation → European Journalism Centre | `overleefd` | 11155 |
| 11092 | rel 8439 Meta → NU.nl | `overleefd` | 11156 |
| 11093 | rel 8440 Meta → AFP | `overleefd` | 11157 |
| 11094 | rel 8441 Meta → DPA | `overleefd` | 11158 |
| 11095 | rel 8442 Bits of Freedom → Meta | `overleefd` | 11159 |
| 11096 | rel 8443 Consumentenbond → Meta | `overleefd` | 11160 |
| 11097 | rel 8444 Marcel Boekhoorn → TMG | `overleefd` | 11161 |
| 11101 | rel 8448 Steven Schuurman → D66 | `overleefd` | 11162 |
| 11102 | rel 8449 Steven Schuurman → Partij voor de Dieren | `overleefd` | 11163 |

**Ondergraving 11291 (op 11127):** de bewering zegt dat Meta Ierland "dwangsommen tot maximaal 10 miljoen euro moet betalen". Dat leunt op de openingszin van het persbericht; dezelfde pagina zegt dat het hof het *maximum* van de dwangsommen verhoogde van 5 naar 10 miljoen euro als prikkel om de uitspraak na te komen. Een dwangsom is alleen verschuldigd bij niet-naleving; de bron noemt geen bedrag dat Meta betaalde of moet betalen.

**Waarom geen aanval op de andere elf:** elk is één feit uit een gedateerde primaire of nieuwsbron (grantdatabase, jaarverslag, persbericht, NOS/ANP/DutchNews), het citaat stond letterlijk op de pagina en de bewering gaat niet verder dan de bron. Ik vond geen tegenbron en geen sprong die een ondergraving rechtvaardigt.

### Negatieve resultaten (alleen hier)
- Voor geen van de elf `overleefd`-claims vond ik een tegenbron of een bron die een ander bedrag, een andere datum of een andere partij noemt.

### Opmerkingen voor andere stappen (geen modelbijdrage)
- **Rel 8439 (Meta → NU.nl) mist een einde.** NOS (26 maart 2020): "Nu.nl ging tot november vorig jaar door" → einde 2019-11. Het citaat noemt het jaartal niet zelf; werk voor de datumzoeker.
- **Rel 8442 (Bits of Freedom → Meta, oppositie) begint op de datum van de uitspraak** (2025-10-02), niet op het aanspannen van de zaak. Werk voor de datumzoeker.
- **Rel 8443 (Consumentenbond → Meta) begint in 2023-03**, het begin van de *tweede* zaak; de eerste zaak (gewonnen in maart 2023) liep al eerder. Werk voor de datumzoeker.
- **Rel 8410 (Luminate → Bits of Freedom) begint in 2024**, maar dezelfde pagina noemt een meerjarige overeenkomst met Luminate die in 2025 afloopt; het begin ligt mogelijk eerder.

### Stance-balans van de ronde
0 weerleggingen / 1 ondergraving / 11 `overleefd` / 0 `onbeslist` (modelbijdragen: 0 steun / 1 tegen / 0 context). Geen 429, geen LinkedIn gebruikt.

## Sessie-uitvoer

```
