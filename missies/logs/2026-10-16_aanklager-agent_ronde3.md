# Onbewaakte ronde — aanklager-agent · ronde3 · 2026-10-16

- Brief: `missies/aanklager_brief.md` (blob `b985acb45edc`)
- Account: `aanklager-agent`
- Gestart: 2026-10-16T12:07:05

## Sessie-uitvoer

```
# Ronde-log aanklager-agent · ronde3 · 2026-10-16

- **Brief:** `missies/aanklager_brief.md`, blob `b985acb45edc`.
- **Voorregel:** ik heb `GET /api/agent/reeds_gereageerd` vóór het indienen opgehaald. Geen van de behandelde id's stond erin, en geen enkele inzending gaf een 409.
- **Wachtrij:** `scripts/automatische_beoordeling.py --open-a2` gaf 39 argumenten. Daarvan waren er 6 van mijzelf, die ik oversloeg (eigen werk, 403). Ik behandelde de 12 oudste van anderen: 11034–11036 en 11041–11049. De andere 21 (11050–11102) zijn voor de volgende ronde.

## Zoekopdrachten (letterlijk)

**Database:**
1. `scripts/automatische_beoordeling.py --open-a2`
2. `SELECT … arguments/relations/citations/source_locations/immuun_oordelen` voor de 33 open-A2-id's van anderen
3. `select id,name,type,active_from,active_until from entities where name in ('Bellingcat','ProDemos','Kieskompas','Open Society Foundations','Nederlandse Defensie Academie (NLDA)','ICCT …','The Investigative Desk','Open State Foundation')`
4. `select … from arguments where relation_id in (1638, 1621, 1626)`

**Web:**
- WebFetch `nos.nl/artikel/2125938-soros-leaks-…`: ProDemos en KiesKompas staan erin. Er staat geen bedrag of jaar per ontvanger in, en er staat geen reactie van de organisaties in.
- WebFetch `rijksoverheid.nl/…/tk-aanbieding-rapport-schimmige-scheidslijnen`: "op verzoek van de … (NCTV), in opdracht van het … (WODC)". Over financiering staat er niets.
- WebFetch `defensie.nl/onderwerpen/d/defensieacademie/leiderschap`: "De NLDA valt onder het Defensie Ondersteuningscommando". Een budget of financiering noemt de pagina niet.
- WebSearch `ProDemos Open Society Foundations subsidie Soros reactie project`
- WebSearch `Kieskompas Open Society Foundations grant`
- WebFetch van de OSF-grantdatabase (`grants/past?filter_keyword=`) met de zoekwoorden `Bellingcat`, `Stichting Vredesbeweging`, `Onderzoeksredactie`, `Free Press Unlimited` en `Open State Foundation`
- WebFetch `uva.nl/…/waardering-van-het-nederlandse-ondernemingsklimaat-daalt-opnieuw.html`
- WebFetch `opensocietyfoundations.org/who-we-are/leadership`
- WebSearch `Open Society Fund established 1979 Soros New York history Open Society Foundations`

## Per claim

| Anker (supporting) | Doel | Route | Nieuw id |
|---|---|---|---|
| 11034 | rel 1638 Defensie → NLDA (financiering) | ondergraving (`equivocatie`) | argument **11167**, certificaat `aangevallen` (10735) |
| 11036 | rel 1621 NCTV → ICCT (financiering) | ondergraving (`citaat_dekking`) | argument **11168**, certificaat `aangevallen` (10736) |
| 11035 | rel 1626 EZK → SEO | certificaat | `overleefd` (10737) |
| 11041 | rel 8399 Soros → OSF | certificaat | `overleefd` (10738) |
| 11042 | rel 8400 OSF → ProDemos | certificaat | `overleefd` (10739) |
| 11043 | rel 8401 OSF → Kieskompas | certificaat | `overleefd` (10740) |
| 11044 | rel 8402 OSF → The Investigative Desk | certificaat | `overleefd` (10741) |
| 11045 | rel 8403 OSF → Bellingcat | certificaat | `overleefd` (10742) |
| 11046 | rel 8403 OSF → Bellingcat | certificaat | `overleefd` (10743) |
| 11047 | rel 8404 OSF → Free Press Unlimited | certificaat | `overleefd` (10744) |
| 11048 | rel 8405 OSF → Open State Foundation | certificaat | `overleefd` (10745) |
| 11049 | rel 8406 OSF → PAX | certificaat | `overleefd` (10746) |

**Waarom de twee ondergravingen:**
- **11034:** dat de NLDA onder het DOSCO valt, is een organisatorische inbedding binnen het ministerie. Het is geen geldstroom van Defensie naar de NLDA, en de bron noemt geen geld.
- **11036:** de Kamerbrief noemt het WODC als opdrachtgever en de NCTV als de partij die om het onderzoek vroeg. Dat de NCTV het ICCT betaalde, staat er niet in.

## Opmerkingen voor andere stappen

- **Rel 8399 valt buiten het bestaan van OSF.** De entiteit OSF heeft `active_from` 1993, maar het verband Soros → OSF begint in 1979. Het Open Society Fund bestond al in 1979, dus waarschijnlijk is de oprichtingsdatum van de entiteit te laat. Dit is werk voor de bestaanscontrole of de datumzoeker.
- **Rel 8400 en 8401 hebben geen eigen looptijd.** De looptijd 2009–2014 is de periode van de gelekte documenten, niet het begin en einde van deze specifieke banden.
- **Ontvanger bij rel 8403 in 2016.** De subsidie van 2016 ging naar Bellingcat Ltd. (VK), de voorloper van de stichting.

## Negatieve resultaten (alleen in dit logboek)

- Ik vond geen reactie van ProDemos of Kieskompas op het OSF-geld, en geen OSF-subsidie op naam van Kieskompas in de zoekresultaten.
- Ik vond geen bron die een betaling van de NCTV voor het onderzoek "Schimmige scheidslijnen" noemt, en geen bron over een budget van Defensie voor de NLDA.
- Er kwam geen 429. LinkedIn heb ik niet gebruikt, omdat geen claim over een loopbaan ging.

## Stance-balans

- **Certificaten:** 2 aangevallen, 10 overleefd, 0 onbeslist.
- **Aanvallen:** 0 weerleggingen en 2 ondergravingen.
- **Nieuwe bijdragen aan het model:** 0 steun, 2 tegen (11167 en 11168), 0 context.
- **Wat ik niet deed:** ik maakte geen bronnen, entiteiten of relaties aan, wijzigde geen status, mergede niets, classificeerde geen bronnen en verwijderde niets.

Bronnen:
- [NOS: Soros Leaks](https://nos.nl/artikel/2125938-soros-leaks-zeker-4-9-miljoen-euro-naar-nederlandse-organisaties)
- [Kamerbrief Schimmige scheidslijnen](https://www.rijksoverheid.nl/documenten/kamerstukken/2025/12/02/tk-aanbieding-rapport-schimmige-scheidslijnen)
- [Defensie: Defensieacademie](https://www.defensie.nl/onderwerpen/d/defensieacademie/leiderschap)
- [UvA-persbericht 9 december 2024](https://www.uva.nl/content/nieuws/persberichten/2024/12/waardering-van-het-nederlandse-ondernemingsklimaat-daalt-opnieuw.html)
- [OSF Leadership](https://www.opensocietyfoundations.org/who-we-are/leadership)
- [OSF: our history](https://www.opensocietyfoundations.org/our-history)
- [georgesoros.com: philanthropy](https://www.georgesoros.com/philanthropy/)
- OSF-grantdatabase, met de zoekwoorden [Bellingcat](https://www.opensocietyfoundations.org/grants/past?filter_keyword=Bellingcat), [PAX](https://www.opensocietyfoundations.org/grants/past?filter_keyword=Stichting%20Vredesbeweging), [Onderzoeksredactie](https://www.opensocietyfoundations.org/grants/past?filter_keyword=Onderzoeksredactie), [Free Press Unlimited](https://www.opensocietyfoundations.org/grants/past?filter_keyword=Free%20Press%20Unlimited) en [Open State Foundation](https://www.opensocietyfoundations.org/grants/past?filter_keyword=Open%20State%20Foundation)
- [NLTimes](https://nltimes.nl/node/30378)

```

## Runner-metadata

- Exit-code: 0
- Duur: 184.0 s
- Oogst (edit_log-delta van `aanklager-agent`): 14
- Beëindigd: 2026-10-16T12:10:09
