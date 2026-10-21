# Onbewaakte ronde — aanklager-agent · ronde3 · 2026-10-15

- Brief: `missies/aanklager_brief.md` (blob `b985acb45edc`)
- Account: `aanklager-agent`
- Gestart: 2026-10-15T17:26:05

## Sessie-uitvoer

```
# Logboek aanklager-agent · 2026-10-15 · ronde3

- Brief: `missies/aanklager_brief.md`, blob `b985acb45edc`
- Account: `aanklager-agent`
- Dit logboek schrijf ik niet zelf naar het bestand. De runner heeft `missies/logs/2026-10-15_aanklager-agent_ronde3.md` open in append-modus en zet deze sessie-uitvoer erin, net als in ronde1 en ronde2.

## Voorregel en werklijst

- **Voorregel (17:26):** `GET /api/agent/reeds_gereageerd` gaf 66 id's, van 3477 tot en met 10337. Daar stond geen van de claims die ik behandelde tussen.
- **Werklijst (17:26):** `python3 scripts/automatische_beoordeling.py --open-a2` gaf 17 claims.
- **Overgeslagen, omdat dit account ze zelf schreef** (een certificaat daarop zou zelfcertificering zijn en geeft 403): 10365, 9741, 9740, 7949 en 7840.
- **Behandeld:** alle 12 claims van anderen. Dat is precies het maximum per ronde: 10535, 10420, 10419, 10416, 10360, 10359, 10358, 10357, 10356, 10355, 10354 en 10352.

## Zoekopdrachten, letterlijk

**Database** (sqlite3, alleen lezen, 17:26–17:27). Voor elk van de 12 claims:
- `select * from arguments where id=?`
- de relatie, met join op `entities` en `mechanisms`
- de andere niet-vervangen argumenten op dezelfde relatie
- de citaties: `citations` join `sources` plus `group_concat(location)` uit `source_locations`
- `select fase,verdict,door,detail from immuun_oordelen where argument_id=?`
- bij een revisie het origineel (`reviseert_id`), en de reacties (`parent_argument_id=?`)

Daarnaast `select … from relations … where s.name like '%Buitenlandse Zaken%' … and t.name='PAX'`. Dat gaf twee relaties: rel 469 (financiering, `denktank_financiering_bias`) en rel 482 (zelfcensuur).

**Web** (17:27–17:28):
- WebSearch `Voor Ons Nederland Dijkhoff campagne niet tegen partijen PVV reactie`
- WebSearch `Zomergasten Vrije Geluiden NPO reactie VPRO keuze bezuiniging december 2025`
- WebSearch `NPO Kassa Radar minder afleveringen besluit teruggedraaid 2021`
- WebFetch en curl `https://nieuws.nl/algemeen/powned-niet-meer-te-zien-op-tv`. Ik heb de volledige tekst letterlijk gelezen.
- WebFetch `https://www.villamedia.nl/artikel/commissariaat-adviseert-slob-rondom-budget-en-prestatieovereenkomst-npo`
- WebFetch van de Wayback-kopie van maxvandaag.nl lukte niet (web.archive.org niet bereikbaar). Ik heb daarom curl gebruikt op `https://www.maxvandaag.nl/?p=176507` en de tekst letterlijk gelezen.

## Per claim: anker, route en id

| Claim | Doel · stance | Route | Aanval | Certificaat |
|---|---|---|---|---|
| 10420 PAX kreeg in 2022 bijna 14 mln van de overheid (70%), plus de BuZa-nota | rel 482 (BuZa → PAX, zelfcensuur) · steun | **ondergraving** (non_sequitur): het bedrag hoort bij rel 469 (financiering). De bron zegt "de overheid", niet BuZa. De bewering bevat twee feiten en de afleiding van #549 is verdwenen | **#10565** | 9847 aangevallen |
| 10419 Menno Swart in Wynia's Week: de VON-campagne is "overduidelijk gericht" tegen PVV en FvD | rel 511 (VON → PVV, oppositie) · steun | **ondergraving** (non_sequitur): dit is de lezing van een derde. Volgens dezelfde bron noemt VON geen partij, en het origineel zei "expliciet" | **#10566** | 9848 aangevallen |
| 10358 NPO-plan van april 2015: omroepverenigingen krijgen minder zeggenschap | rel 366 (NPO → AVROTROS, intekensturing) · steun | **ondergraving** (non_sequitur): een concept-plan is een voornemen, geen uitgeoefende sturing. Het gaat over alle verenigingen | **#10567** | 9849 aangevallen |
| 10535 Mediahuis, dentsu en PubMatic: WK-campagne voor Albert Heijn (juni 2026) | rel 95 · steun | certificaat | — | 9850 overleefd |
| 10416 NTR krijgt per programma geld van de NPO (Rekenkamer 2019) | rel 680 · steun | certificaat | — | 9851 overleefd |
| 10360 NPO stelt programmabudget vast na intekening (Kst 32827-201) | rel 365 · steun | certificaat | — | 9852 overleefd |
| 10359 NPO wilde in 2021 Kassa en Radar bijna halveren | rel 364 · steun | certificaat | — | 9853 overleefd |
| 10357 VPRO: de NPO bezuinigt Zomergasten en Vrije Geluiden weg | rel 367 · steun | certificaat (het ANP-bericht bevestigt de keuze van de NPO) | — | 9854 overleefd |
| 10356 Garantiebudgetten van HUMAN, WNL en PowNed van 3,5 naar 12,1 mln | rel 369 · steun | certificaat (de bron spreekt van "interne garantiebudgetten" in de NPO-begroting) | — | 9855 overleefd |
| 10355 Slagter: de NPO verdeelt het geld en besloot welke MAX-titels vervallen | rel 368 · steun | certificaat (de bewering is aan hem toegeschreven) | — | 9856 overleefd |
| 10354 NPO: PowNews Flits keert niet terug (jan. 2018) | rel 370 · steun | certificaat (bron: "Per programma maakt NPO voortdurend de afweging…") | — | 9857 overleefd |
| 10352 NPO financiert via garantie- en programmaversterkingsbudget, verdeling volgens geld-op-schema | rel 682 · steun | certificaat | — | 9858 overleefd |

## Bevindingen voor de beoordeling en de datumzoeker

Ik heb hier niets voor ingediend.
- **10355:** de bewering noemt Slagter "voorzitter". Op de bronpagina staat "oprichter-directeur van Omroep MAX". In de pers heet hij ook vaak voorzitter, dus ik heb dit niet aangevallen.
- **10354:** volgens de NPO stopte PowNews Flits "in wederzijds overleg". De bewering laat dat weg. In dezelfde bron staat ook de zin over de afweging per programma, en die steunt het verband.
- **Rel 364–370, 680, 682, 482, 511:** geen van deze relaties heeft een `active_from`.
- **Rel 482:** de beschrijving zegt "~80% afhankelijkheid", maar de NOS-bron in #10420 noemt 70 procent voor 2022.

## Negatieve resultaten (alleen in dit logboek)

- **10419:** ik vond geen uitspraak van Voor Ons Nederland of Dijkhoff die de PVV bij naam noemt. In de bronnen gaat het om "populistische en antidemocratische krachten" (NOS).
- **10357:** ik vond geen NPO-reactie die de VPRO-lezing tegenspreekt.
- **10359:** ik vond niet dat het voornemen van 2021 helemaal werd teruggedraaid. Volgens TVGids leverde Radar later 14 afleveringen in.
- **10535, 10416, 10360, 10352:** geen tegenbron gezocht naast de database-lezing, omdat er geen aanwijzing voor een fout was.
- Geen 429. LinkedIn niet gebruikt.

## Stance-balans van de ronde

- **Certificaten:** 3 aangevallen, 9 overleefd, 0 onbeslist.
- **Aanvallen:** 0 weerleggingen en 3 ondergravingen (#10565, #10566, #10567).
- **Nieuwe bijdragen aan het model:** 0 steun, 3 tegen, 0 context.
- Ik heb geen bronnen, entiteiten of relaties aangemaakt, en geen status gewijzigd, niets gemerged en niets geclassificeerd.

---

Ronde 3 is klaar: ik heb alle 12 claims van anderen op de lijst behandeld. Drie heb ik met een ondergraving aangevallen en negen houden stand; ze zijn allemaal hierboven gelogd.

Sources:
- [NOS: Dijkhoff richt denktank op voor 'milde meerderheid'](https://nos.nl/l/2571547)
- [Welingelichte Kringen: Dijkhoff start actiegroep](https://www.welingelichtekringen.nl/samenleving/klaas-dijkhoff-start-actiegroep-om-democratie-te-versterken)
- [Welingelichte Kringen: Zomergasten stopt na 37 jaar](https://www.welingelichtekringen.nl/samenleving/zomergasten-stopt-na-37-jaar-om-bezuinigingen)
- [NOS: VPRO stopt met Zomergasten](https://nos.nl/l/2592928)
- [TVGids: discussie Hertsenberg en Frans Klein](https://www.tvgids.nl/nieuws/shownieuws/discussie-antoinette-hertsenberg-tv-directeur-npo-frans-klein-de-vooravond)
- [nieuws.nl: PowNed niet meer te zien op tv](https://nieuws.nl/algemeen/powned-niet-meer-te-zien-op-tv)
- [Villamedia: Commissariaat adviseert Slob](https://www.villamedia.nl/artikel/commissariaat-adviseert-slob-rondom-budget-en-prestatieovereenkomst-npo)
- [MAX Vandaag: Jan Slagter](https://www.maxvandaag.nl/?p=176507)

```

## Runner-metadata

- Exit-code: 0
- Duur: 207.1 s
- Oogst (edit_log-delta van `aanklager-agent`): 15
- Beëindigd: 2026-10-15T17:29:32
