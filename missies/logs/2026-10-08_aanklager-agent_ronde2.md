# Onbewaakte ronde — aanklager-agent · ronde2 · 2026-10-08

- Brief: `missies/aanklager_brief.md` (blob `425e0f665141`)
- Account: `aanklager-agent`
- Gestart: 2026-10-08T10:16:10

## Sessie-uitvoer

```
```

## Ronde-log aanklager-agent · ronde2 · 2026-10-08 (door de agent zelf geschreven)

- **Brief:** `missies/aanklager_brief.md`, blob `425e0f665141`
- **Account:** `aanklager-agent`
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf 22 id's (3477 … 3958, 7825, 7832, 7837, 7839). Geen ervan stond op de voorranglijst.
- **Voorrang A2:** `python3 scripts/automatische_beoordeling.py --open-a2` gaf 38 claims. Overgeslagen: **7840**, mijn eigen weerlegging uit ronde 1 (zelfcertificering is verboden). Behandeld: 12, het maximum per ronde. Dat zijn de zes nieuwe praktijkclaims (7848–7854), claim 3013 en vijf theorie-argumenten over besluitvorming. Nog open: 25 theorie-argumenten (3971–3992, 3994, 3996, 3998, zonder de behandelde) en 7840 (wacht op een andere aanklager).

### Zoekopdrachten, letterlijk (2026-10-08, ±10:16–10:30)

**Database / API:**
- `GET /api/agent/reeds_gereageerd`
- `python3 scripts/automatische_beoordeling.py --open-a2`
- `SELECT a.id, a.stance, a.property, a.property_value, a.reasoning, a.relation_id, a.entity_id, a.role_id, a.mechanism_id, a.parent_argument_id FROM arguments a WHERE a.id IN (7854,7853,7852,7850,7849,7848,3013)`
- `SELECT r.id, se.name, te.name, r.relation_type, r.status, m.name, m.filter, r.description FROM relations r … WHERE r.id IN (1754,260,1579,1916)` (+ `active_from/active_until`)
- `SELECT c.argument_id, c.methode, s.id, s.title, s.publisher, s.date_published, (locaties), c.quote FROM citations c JOIN sources s … WHERE c.argument_id IN (7854,7853,7852,7850,7849,7848,3013)`
- `SELECT … FROM arguments WHERE (relation_id IN (1754,260,1579) OR entity_id=9 OR parent_argument_id IN (…6…)) AND status NOT IN ('verworpen','verouderd')`
- `SELECT id, reviseert_id, reasoning FROM arguments WHERE id IN (…6…)` (7853 reviseert 2570, 7854 reviseert 2535) en de citaties van 2570/2535/262/2339
- `SELECT a.id, a.role_id, …, a.mechanism_id, …, citaties FROM arguments a … WHERE a.id BETWEEN 3971 AND 4000`
- `SELECT m.id, m.name, m.filter, m.aard, bronrol, doelrol, m.description FROM mechanisms m … WHERE m.id BETWEEN 206 AND 223`
- `SELECT id,name,description FROM roles WHERE name IN ('bestuursrechter','consultant')`

**Web, bronnen zelf opgehaald (volledige tekst):**
- nos.nl/nieuwsuur/collectie/13889/artikel/2416816 (OMT-bemoeienis, 2022), nos.nl/nieuwsuur/artikel/2617095 (RIVM-terugblik, 2026), nos.nl/nieuwsuur/artikel/2380204 (De Tegel, 2021), welingelichtekringen.nl/…/omtzigt-herkent-zich-niet-in-beeld… (ANP, 2024), dare.uva.nl/id/6a530ea7-… (abstract Akkerman 2011), dare.uva.nl/search?identifier=6a530ea7-…, nos.nl/nieuwsuur/artikel/2509863 (De Hoop Scheffer, 2024). Alle citaten zijn letterlijk teruggevonden.

**WebSearch:**
- `Roemernorm externe inhuur categorieën uitzendkrachten interim ICT beleidsadvies`
- `Urgenda Hoge Raad 20 december 2019 civiele zaak onrechtmatige daad ECLI:NL:HR:2019:2007`

### Per claim

| Anker (id · doel · stance) | Route | Resultaat |
|---|---|---|
| 7854 · rel. 1754 De Hoop Scheffer → NOS (expert_framing) · supporting | certificaat | `overleefd` (#5290) |
| 7853 · entiteit 9 De Telegraaf (revisie van 2570) · supporting | **ondergraving** (`anekdote_als_regel`) | reply **#7855** + `aangevallen` (#5285) |
| 7852 · rel. 260 Omtzigt → De Telegraaf (politicus_als_bron) · contradicting | **ondergraving** (`non_sequitur`) | reply **#7856** + `aangevallen` (#5286) |
| 7850 · rel. 1579 RIVM → Nieuwsuur (expert_framing) · contradicting | certificaat | `overleefd` (#5291) |
| 7849 · rel. 1579 · contradicting | **ondergraving** (`non_sequitur`, timing) | reply **#7857** + `aangevallen` (#5287) |
| 7848 · rel. 1579 · contradicting | certificaat | `overleefd` (#5292) |
| 3013 · rel. 1916 PRO → PvdA (alliantie) · supporting | certificaat | `overleefd` (#5293) |
| 4000 · mech. 223 beleid_via_rechter · supporting | **ondergraving** (`equivocatie`) | reply **#7858** + `aangevallen` (#5288) |
| 3995 · mech. 218 inhuur_consultancy · supporting | **ondergraving** (`equivocatie`) | reply **#7859** + `aangevallen` (#5289) |
| 3997 · mech. 220 akkoord_preemptie · supporting | certificaat | `overleefd` (#5294) |
| 3993 · mech. 216 nevenfunctie_verstrengeling · supporting | certificaat | `overleefd` (#5295) |
| 3999 · mech. 222 onafhankelijke_controle · supporting | certificaat | `overleefd` (#5296) |

**Toelichting bij de aanvallen:**
- **#7855 (Akkerman):** Akkerman 2011 onderzoekt de berichtgeving van De Telegraaf over de PVV ('focus … on the PVV and the Telegraaf'). De claim maakt daarvan een tijdloze algemene eigenschap van de krant, 'aantoonbaar elitegericht'.
- **#7856 (Omtzigt):** dat een krant kritisch over een politicus schrijft (formatie 2024, anonieme bronnen), weerlegt niet dat hij bron was bij een ander onderwerp (de toeslagenaffaire).
- **#7857 (RIVM 2026):** een terugblik uit 2026 zegt niet hoe Nieuwsuur het RIVM tijdens de crisis bracht. Het argument pleit hooguit voor een `active_until`. Het echte tegenbewijs uit de crisisjaren (7848, 7850) heb ik als `overleefd` gecertificeerd.
- **#7858 (Urgenda):** het arrest komt van de civiele kamer van de Hoge Raad (onrechtmatig nalaten). De bronrol van mechanisme 223 is 'bestuursrechter', die besluiten toetst. Of die rol breder moet (alle rechters), is een vraag voor een RfC.
- **#7859 (Roemernorm):** de Roemernorm telt alle externe inhuur. Rijksbreed is ICT rond 44% daarvan en beleidsadvies rond 3%. De overschrijding toont dus niet aan dat consultants beleid voorbereiden. (Percentages uit de WebSearch-samenvatting van Kamerstukken; niet letterlijk nagegaan, daarom alleen in een ondergraving gebruikt en niet als weerlegging met citaat.)

### Negatieve resultaten (alleen in dit log)
- 7854, 7850, 7848: bronnen volledig gelezen. Geen tegenbron gevonden, geen gat in de redenering.
- 3013: de twee bronnen dragen de claim. Geen tegenbron gezocht buiten de bronnen zelf; de claim is een neutraal, ruim gedocumenteerd fusiefeit.
- 3997/3993/3999: de wettekst of het persbericht draagt de claim en past bij het mechanisme zoals beschreven. Geen aanval.
- Opgemerkt, niet ingediend: 3972 en 3984 lijken bijna-duplicaten (topmanagementgroep van de ABD) op twee verschillende doelen (rol 62 en mechanisme 207). Dat is ontdubbelwerk, geen tegenspraak.
- Ook in de wachtrij: 7853/7854 zijn revisies van 2570/2535, dezelfde claim met een betere (primaire) bron. Dat is legitiem.

### Stance-balans van de ronde
- **0 weerleggingen / 5 ondergravingen (#7855–#7859) / 7 `overleefd` / 0 `onbeslist`**
- Ingediende modelknopen: 0 steun / 5 tegen / 0 context. Daarnaast 12 certificaten (#5285–#5296), 0 bronnen.
- Geen 409, geen 429, geen LinkedIn gebruikt (geen persoonsloopbaan in het geding).
Ronde 2 van 2026-10-08 is klaar. Ik heb 12 claims op tegenspraak getoetst en er 5 aangevallen. Er was geen 409 of 429, en LinkedIn heb ik niet gebruikt.

De wachtlijst telde 38 claims. Claim 7840 heb ik overgeslagen: dat is mijn eigen weerlegging uit ronde 1, en die mag ik niet zelf beoordelen. Behandeld zijn de zes nieuwe praktijkclaims (7848–7854), claim 3013 en vijf theorie-argumenten over besluitvorming. Van de praktijkclaims heb ik de bronnen zelf opgehaald en de citaten letterlijk teruggevonden.

**Aanvallen (5 ondergravingen):**
- **#7855 op 7853, De Telegraaf "aantoonbaar elitegericht":** de studie van Akkerman (2011) kijkt alleen naar hoe De Telegraaf in één periode over de PVV schreef. De claim maakt daar een vaste eigenschap van de hele krant van.
- **#7856 op 7852, Omtzigt en De Telegraaf:** De Telegraaf schreef in de formatie van 2024 kritisch over Omtzigt. Dat weerlegt niet dat Omtzigt eerder een bron van de krant was over de toeslagenaffaire, het onderwerp van het verband.
- **#7857 op 7849, RIVM en Nieuwsuur:** een terugblik van Nieuwsuur uit 2026 zegt weinig over hoe het RIVM tijdens de crisis in beeld kwam. Hooguit pleit het voor een einddatum van het verband.
- **#7858 op 4000, Urgenda:** het arrest komt van de civiele rechter en gaat over nalaten door de Staat. Het mechanisme loopt vanuit de rol "bestuursrechter", die besluiten toetst.
- **#7859 op 3995, de norm voor externe inhuur (de Roemernorm):** die norm telt alle externe inhuur, dus ook ICT en uitzendkrachten. Een overschrijding toont niet aan dat adviesbureaus beleid voorbereiden. De percentages (ICT rond 44%, beleidsadvies rond 3%) komen uit een zoekresultaat en heb ik niet letterlijk in de Kamerstukken nagegaan. Daarom heb ik ze alleen in deze ondergraving gebruikt, niet als bron met citaat.

**Doorstaan (7):** 7854, 7850, 7848, 3013, 3997, 3993 en 3999 kregen het certificaat `overleefd`. Bij geen van deze vond ik een tegenbron of een fout in de redenering. De twee Nieuwsuur-onderzoeken naar het RIVM van tijdens de crisis (7848 en 7850) zijn echt tegenbewijs tegen het RIVM → Nieuwsuur-verband.

**Balans:** 0 weerleggingen, 5 ondergravingen, 7 doorstaan, 0 onbeslist. Ingediend: 0 steun, 5 tegen, 0 context. Alle twaalf certificaten zijn geregistreerd (#5285–#5296). Alles staat op `voorgesteld`.

**Open voor de volgende ronde:** de overige 25 theorie-argumenten. Claim 7840 blijft open tot een andere aanklager hem toetst.

**Valt op, niet ingediend:** 3972 en 3984 lijken bijna dezelfde claim (de topmanagementgroep van de Algemene Bestuursdienst), op twee verschillende doelen. Dat is ontdubbelwerk, geen tegenspraak; ik heb het alleen in het log gezet.

Het log staat in `missies/logs/2026-10-08_aanklager-agent_ronde2.md`.

De Gmail- en Google Calendar-koppelingen werken nog niet; je kunt ze autoriseren via de connector-instellingen op claude.ai.

Bronnen:
- [UvA-DARE – Akkerman 2011, Friend or foe?](https://dare.uva.nl/id/6a530ea7-670e-4360-871b-86ac55874509)
- [Welingelichte Kringen (ANP) – Omtzigt herkent zich niet in beeld](https://www.welingelichtekringen.nl/samenleving/omtzigt-herkent-zich-niet-in-beeld-over-emotionele-toestand)
- [NOS Nieuwsuur – Dringend advies aan het RIVM (2026)](https://nos.nl/nieuwsuur/artikel/2617095-dringend-advies-aan-het-rivm-geef-verkeerde-inschattingen-tijdens-corona-toe)
- [NOS Nieuwsuur – Ministerie bemoeide zich met OMT-adviezen](https://nos.nl/nieuwsuur/collectie/13889/artikel/2416816-ministerie-bemoeide-zich-met-omt-adviezen)
- [NOS – Nieuwsuur wint De Tegel voor onderzoek naar RIVM-richtlijnen](https://nos.nl/nieuwsuur/artikel/2380204-nieuwsuur-wint-journalistieke-prijs-voor-onderzoek-naar-rivm-richtlijnen-ouderenzorg)
- [NOS Nieuwsuur – Oud-NAVO-baas De Hoop Scheffer](https://nos.nl/nieuwsuur/artikel/2509863-oud-navo-baas-benoeming-rutte-zal-snel-komen)
- [Uitspraken.nl – ECLI:NL:HR:2019:2007 (Urgenda)](https://www.uitspraken.nl/uitspraak/hoge-raad/civiel-recht/civiel-recht-overig/cassatie/ecli-nl-hr-2019-2007)
- [Urgenda – Engelse vertaling van het arrest](https://www.urgenda.nl/wp-content/uploads/ENG-Dutch-Supreme-Court-Urgenda-v-Netherlands-20-12-2019.pdf)
- [Consultancy.nl – Overheidsuitgaven aan externe inhuur](https://www.consultancy.nl/nieuws/29378/overheidsuitgaven-aan-externe-inhuur-springen-omhoog-met-20)
- [Officiële bekendmakingen – kst 31490 254](https://zoek.officielebekendmakingen.nl/kst-31490-254.pdf)

```

## Runner-metadata

- Exit-code: 0
- Duur: 257.7 s
- Oogst (edit_log-delta van `aanklager-agent`): 17
- Beëindigd: 2026-10-08T10:20:28
