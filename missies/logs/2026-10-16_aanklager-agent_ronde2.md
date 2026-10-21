# Onbewaakte ronde — aanklager-agent · ronde2 · 2026-10-16

- Brief: `missies/aanklager_brief.md` (blob `b985acb45edc`)
- Account: `aanklager-agent`
- Gestart: 2026-10-16T10:24:04

## Sessie-uitvoer

```
# Aanklager-agent · ronde 2 · 2026-10-16

Op de wachtrij stonden drie argumenten van een ander account. Twee heb ik aangevallen met een ondergraving: 11025 en 11027. Eén houdt stand: 11026.

- **Brief:** `missies/aanklager_brief.md` (blob `b985acb45edc`).
- **Account:** `aanklager-agent`. De ronde liep van 10:24 tot 10:26.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf 69 id's. Geen daarvan stond op de lijst van deze ronde.
- **Logboek:** ik heb niet zelf in het bestand geschreven. De runner voegt deze sessie-uitvoer toe aan `missies/logs/2026-10-16_aanklager-agent_ronde2.md`.

## Wachtrij

`python3 scripts/automatische_beoordeling.py --open-a2` gaf 8 argumenten.
- **Behandeld (3):** 11027, 11026 en 11025, alle drie van de bronzoeker.
- **Overgeslagen (5):** 10365, 9741, 9740, 7949 en 7840. Die zijn van dit account zelf; zelf-certificering geeft 403.

## Zoekopdrachten, letterlijk

**Database (alleen lezen, 10:24):**
- `select a.id,a.stance,a.reasoning,a.property,a.relation_id,r.relation_type,r.description,r.active_from,r.active_until,r.mechanism_id,m.name,es.name,et.name from arguments a join relations r … where a.id in (11025,11026,11027)`
- `select c.argument_id,c.quote,c.methode,s.id,s.title,group_concat(sl.location) from citations c … where c.argument_id in (11025,11026,11027) group by c.id`
- `select id,claim,stance,status,parent_argument_id,contributed_by from arguments where relation_id in (1707,1750,1765) or parent_argument_id in (…)`

**Bronnen opgehaald (10:24):**
- https://zoek.officielebekendmakingen.nl/kst-31125-131.html
- https://zoek.officielebekendmakingen.nl/kst-28676-100.html
- https://web.archive.org/web/20240527130805/https://www.ftm.nl/artikelen/defensie-trekt-aan-de-touwtjes-van-de-verslaggeving

**Web (10:25):**
- `Dienst Publiek en Communicatie Algemene Zaken mediainkoop rijksoverheid alle ministeries`
- `Berenschot NLDTIB onderzoek 2024 opdracht EZK aanbesteding 2023`
- `Atlantische Commissie subsidie Defensie beëindigd`

## Per claim

| Anker | Doel | Route | Nieuw id |
|---|---|---|---|
| **11027**, supporting | rel 1707, EZK → Berenschot | ondergraving (`citaat_dekking`) | argument **11032**; certificaat `aangevallen` (oordeel 10637) |
| **11025**, supporting | rel 1765, Defensie → RTL Nederland | ondergraving (`equivocatie`) | argument **11033**; certificaat `aangevallen` (oordeel 10638) |
| **11026**, supporting | rel 1750, Defensie → Atlantische Commissie | certificaat | `overleefd` (oordeel 10639) |

**11027.** De bewering zegt dat EZK de opdracht "in 2024" verleende, maar de Kamerbrief noemt dat jaar niet.
- 27 mei 2024 is de datum van de brief. De brief zegt alleen dat het onderzoek "in februari en maart van dit jaar" werd uitgevoerd.
- Ik heb in de ondergraving een formulering voorgesteld die de bron wel draagt.

**11025.** De bewering presenteert een totaalbedrag van Algemene Zaken als uitgave van Defensie. Dat staat niet in de bron.
- Follow the Money noemt 558.053 euro (2014) en gemiddeld 437.464 euro per jaar (2011-2014). Dat is wat het departement van Algemene Zaken aan RTL betaalde.
- Via de Dienst Publiek en Communicatie van Algemene Zaken loopt de media-inkoop van alle ministeries. Het artikel splitst het bedrag niet uit naar Defensie.
- In dezelfde alinea staat de reactie van RTL: "niets te hebben ontvangen" van Defensie voor zendtijd van de gesponsorde programma's.
- Het geciteerde zinnetje bevat de bedragen niet.
- Het verband zelf kan op een ander feit uit hetzelfde artikel steunen: een recruitmentcommercial van de Luchtmacht die op RTL 7 en RTL 5 werd uitgezonden.

**11026.** Het citaat staat letterlijk in Kamerstuk 28676, nr. 100 (2010), en de bewering zegt niet meer dan de bron.

## Opmerkingen voor andere stappen

- **Looptijd ontbreekt:** relaties 1765 en 1750 hebben geen `active_from`. Dat is werk voor de datumzoeker.
- **Weerlegging overwogen voor rel 1765:** ik heb de reactie van RTL bewust niet als contradicting root op het verband ingediend. Die ontkenning gaat alleen over zendtijd van de gesponsorde programma's. Hetzelfde artikel beschrijft een Defensie-commercial op RTL 7 en RTL 5, dus de reactie is geen tegenbewijs tegen het verband als geheel.
- **Certificaat 10638 is te ruim geformuleerd:** daarin staat "RTL ontkent in hetzelfde artikel betaling van Defensie voor zendtijd". Volgens de bron ging het alleen om zendtijd van de gesponsorde programma's. Het certificaat is alleen procesmetadata en telt niet in de score.

## Negatieve resultaten (alleen in dit logboek)

- **Opdracht aan Berenschot:** ik vond geen aanbesteding of ander stuk dat het jaar noemt waarin EZK de NLDTIB-opdracht aan Berenschot gaf. Het jaartal blijft dus onbekend.
- **Subsidie aan de Atlantische Commissie:** ik vond geen bron dat Defensie de subsidie heeft beëindigd. Ik vond alleen de motie-Frentrop uit 2022. Die ging over iets anders, subsidie aan organisaties die campagne voeren tegen beleggen in de defensie-industrie, en de Eerste Kamer verwierp haar.
- Er was geen 429. LinkedIn heb ik niet gebruikt, omdat er geen loopbaanvraag was.

## Stance-balans van de ronde

- **Certificaten:** 2 aangevallen, 1 overleefd, 0 onbeslist.
- **Aanvallen:** 0 weerleggingen en 2 ondergravingen.
- **Nieuwe bijdragen aan het model:** 0 steun, 2 tegen (de ondergravingen 11032 en 11033), 0 context.
- **Bronnen, entiteiten, relaties:** niets nieuws aangemaakt. Ik heb ook geen status gewijzigd, niets gemerged, niets geclassificeerd en niets verwijderd.

Bronnen:
- [Kamerstuk 31125, nr. 131](https://zoek.officielebekendmakingen.nl/kst-31125-131.html)
- [Kamerstuk 28676, nr. 100](https://zoek.officielebekendmakingen.nl/kst-28676-100.html)
- [Follow the Money (Wayback), 10 maart 2017](https://web.archive.org/web/20240527130805/https://www.ftm.nl/artikelen/defensie-trekt-aan-de-touwtjes-van-de-verslaggeving)
- [Rijksoverheid: Dienst Publiek en Communicatie](https://www.rijksoverheid.nl/contact/contactgids/dienst-publiek-en-communicatie)
- [Staatscourant 2004: regeling media-inkoop](https://zoek.officielebekendmakingen.nl/stcrt-2004-219-p17-SC67309.html)
- [Eerste Kamer, plenair Frentrop, 12 juli 2022](https://www.eerstekamer.nl/plenair/20220712/frentrop_2)
- [TenderNed-publicatie 336834](https://www.tenderned.nl/papi/tenderned-rs-tns/v2/publicaties/336834/pdf)

```

## Runner-metadata

- Exit-code: 0
- Duur: 127.4 s
- Oogst (edit_log-delta van `aanklager-agent`): 5
- Beëindigd: 2026-10-16T10:26:11
