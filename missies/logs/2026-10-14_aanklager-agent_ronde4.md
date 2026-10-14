# Onbewaakte ronde — aanklager-agent · ronde4 · 2026-10-14

- Brief: `missies/aanklager_brief.md` (blob `b985acb45edc`)
- Account: `aanklager-agent`
- Gestart: 2026-10-14T17:14:42

## Sessie-uitvoer

```
# Logboek aanklager-agent · 2026-10-14 · ronde4

- Brief: `missies/aanklager_brief.md`, blob `b985acb45edc`
- **Voorregel** (17:14): `GET /api/agent/reeds_gereageerd` gaf 53 id's (3477 … 8097). Geen van de claims die ik behandelde stond erop.
- **Werklijst** (17:14): `python3 scripts/automatische_beoordeling.py --open-a2` gaf 20 claims.
  - **9741, 9740, 7949 en 7840** heb ik overgeslagen. Dat is werk van dit account zelf, en zelfcertificering is verboden (403).
  - Van de 16 claims van anderen heb ik er 12 behandeld; dat is het maximum per ronde.
  - **Doorgeschoven naar een volgende ronde:** 10133 (Argos), 9927 (SPIT), 9926 (Investico) en 9959 (NPO → EO, intekensturing).
- Ik heb dit logboek niet zelf naar het bestand geschreven. De runner heeft het bestand al in append-modus open en zet deze sessie-uitvoer erin, net als in ronde1 en ronde3.

## Zoekopdrachten (letterlijk)

**Database** (sqlite3, alleen lezen, 17:14–17:16):
- Per argument (10140, 10137, 10134, 10133, 10132, 10123, 10122, 10121, 9960, 9959, 9938, 9936, 9934, 9927, 9926, 9924):
  - `select * from arguments where id=?`
  - de entiteit of de relatie, met join op `entities`/`mechanisms`
  - de citaties: `citations` join `sources`, plus `group_concat(location)` uit `source_locations`
- `select … from arguments where parent_argument_id=?`: dat gaf geen bestaande reacties op deze 16 claims of op hun originelen.
- `select fase,verdict,door,detail from immuun_oordelen where argument_id=?`: alle 16 hebben de bronchecker-v3-uitslag `klopt`.
- `grep -n -i "waakhond\|establishment" missies/ideoloog_brief.md` en `sed -n 30,100p missies/ideoloog_brief.md`, voor de as-regels.
- `select id,name,description from mechanisms where name in ('intekensturing','bestelsturing','zelfcensuur','etikettering')`
- `select id,name,type,description from entities where name like 'NOS-hoofdredactie%'`
- De wortelargumenten op relatie 1907 en relatie 2107.
- De `politieke_positie`-argumenten op de entiteiten 22, 200, 188, 248, 206, 139, 142 en 309, met bron-id's. Dat was voor de dubbeltelregel.
- De claim en het citaat van de originelen 847, 851, 852, 853, 1007, 1014, 1186 en 1187.

**Web** (17:16–17:18):
- `Jelle Postma Buitenhof Justice for Prosperity extreemrechts`
- `NPO coördinerende taak NTR media-aanbod Staatsblad 2021 297`
- `ERT European Round Table for Industry about us cooperation policymakers`
- `De Andere Krant over ons gevestigde orde medialandschap uniform eenzijdig`
- `"progressieve, niet-elitaire omroep" BNNVARA`
- `NOS Sport hoofdredactie treedt terug grensoverschrijdend gedrag zelfcensuur redactie`
- WebFetch `https://www.vpro.nl/buitenhof/artikelen/buitenhof-3-mei-2026`. De pagina bevestigt dat Postma in die uitzending zat.

## Per claim: anker, route en id

| Claim | Doel · stance | Route | Aanval | Certificaat |
|---|---|---|---|---|
| 10122 BNNVARA → establishment | ent 139 · steun | ondergraving (non_sequitur): het citaat "niet-elitair" draagt het pool establishment niet; het origineel #852 leunde op de positie in het bestel | **#10149** | 8824 aangevallen |
| 10121 VPRO → establishment | ent 142 · steun | ondergraving (non_sequitur): "tegen de stroom in" is geen systeem-affirmerende uiting; het origineel #851 leunde op de A-status | **#10150** | 8825 aangevallen |
| 9924 WIFS → establishment | ent 309 · steun | ondergraving (non_sequitur): het citaat gaat over toon en gender (de culturele as); het is retoriek, geen substantie | **#10151** | 8826 aangevallen |
| 10137 NIDV → establishment | ent 200 · steun | ondergraving (non_sequitur): het citaat is een functieomschrijving, en een functie is volgens de brief geen houding | **#10152** | 8827 aangevallen |
| 10134 IKON → cultureel:progressief | ent 188 · steun | ondergraving (citaat_dekking): de enige bron is het Engelstalige Wikipedia-lemma, en Wikipedia is geen bron | **#10153** | 8828 aangevallen |
| 10123 Omroep ZWART → anti-establishment | ent 206 · steun | ondergraving (non_sequitur): de representatiekritiek valt op de culturele as en is al gedekt door #847 uit dezelfde bron, dus dubbeltel | **#10154** | 8829 aangevallen |
| 9936 ON! betwist ANP-formulering | rel 2107 · tegen | ondergraving (non_sequitur): de betwisting veronderstelt juist dat het ANP het etiket gebruikte; de stance volgt niet uit de bron | **#10155** | 8830 aangevallen |
| 9934 NOS Sport-meldingen | rel 1907 (zelfcensuur) · steun | ondergraving (non_sequitur): gedrag op de redactie is geen zelfcensuur, en NOS Sport-hoofdredactie ≠ NOS-hoofdredactie (#146) | **#10156** | 8831 aangevallen |
| 10140 ERT → establishment | ent 22 · steun | certificaat: het citaat is een uiting over samenwerking met beleidsmakers; geen tegenbron | — | 8832 overleefd |
| 10132 De Andere Krant → anti-establishment | ent 248 · steun | certificaat: expliciete kritiek op de gevestigde orde, bevestigd door de eigen site en NOS/BNNVARA | — | 8833 overleefd |
| 9960 NPO → NTR (bestelsturing) | rel 362 · steun | certificaat: de bewering blijft binnen Stb. 2021, 297 en het advies van de Raad van State | — | 8834 overleefd |
| 9938 Postma → Buitenhof (expert_legitimatie) | rel 2144 · steun | certificaat: het optreden is bevestigd door de Buitenhof-pagina van 3 mei 2026 | — | 8835 overleefd |

## Negatieve resultaten (alleen in dit logboek)

- Ik vond geen tegenbron voor de ERT-zelfbeschrijving, de over-ons-tekst van De Andere Krant, de NPO-coördinatie in Stb. 2021, 297 of Postma's optreden in Buitenhof.
- **NOS Sport:** de zoektocht vond niets over zelfcensuur of over inhoudelijke keuzes in de berichtgeving. De bronnen gaan alleen over grensoverschrijdend gedrag en het terugtreden van de hoofdredactie in maart 2023.
- **BNNVARA-citaat:** de zoektocht noemt directeur Suzanne Kunzeler als spreker. De bronchecker schreef het citaat toe aan Karin van Gilst. Het argument noemt geen spreker, dus dit raakt de claim niet; ik noteer het hier voor de volledigheid.
- **Gaten in de looptijd**, voor de datumzoeker en niet door mij ingediend:
  - Relatie 2144 (Postma → Buitenhof) heeft geen `active_from`. Uit deze ronde is de enige datum het optreden van 3 mei 2026 (vpro.nl/buitenhof). Of dat het begin van het verband is, weet ik niet.
  - Relaties 362 en 363 hebben ook geen `active_from`.
- Geen 429, geen LinkedIn gebruikt. Ik heb geen bronnen, entiteiten of relaties aangemaakt.

## Stance-balans van de ronde

- 0 weerleggingen, 8 ondergravingen, 4 keer `overleefd`, 0 keer `onbeslist`.
- Nieuwe modelbijdragen: 0 steun, 8 tegen (allemaal reacties), 0 context.
- Zes van de acht aanvallen raken nieuwe, neutrale versies van `politieke_positie`-signalen. In die versies heeft de stemtoets de oude redenering geschrapt: positie in het bestel, A-status of sectorframing. Wat overblijft is een citaat dat het gekozen pool niet meer draagt. Bij BNNVARA wijst het citaat zelfs de andere kant op.

---

Ronde 4 is klaar: ik heb 12 claims van anderen beoordeeld. Acht vielen niet goed en heb ik aangevallen, vier hielden stand. Vier eigen claims heb ik overgeslagen, en vier andere schuiven door naar de volgende ronde. Ik heb niets goedgekeurd of samengevoegd en geen status gewijzigd.

- **Zes politieke etiketten** heb ik aangevallen (#10149–#10154):
  - Bij BNNVARA en de VPRO wijst het citaat de andere kant op: BNNVARA noemt zichzelf "niet-elitair", de VPRO werkt "tegen de stroom in".
  - Bij de NIDV beschrijft het citaat alleen haar functie, en bij WIFS gaat het om de toon over het gender-thema, niet om een houding.
  - De IKON-claim leunt alleen op Wikipedia.
  - Bij Omroep ZWART telt dezelfde opmerking een tweede keer, nu op een andere as.
- **Twee claims over verbanden** zijn ook aangevallen:
  - **#10155:** het bezwaar van Ongehoord Nederland tegen het ANP-etiket bevestigt juist dat het ANP dat etiket gebruikte, dus het is geen tegenbewijs.
  - **#10156:** de meldingen over grensoverschrijdend gedrag bij NOS Sport zeggen niets over zelfcensuur door de NOS-hoofdredactie.
- **Hielden stand:** ERT, De Andere Krant, NPO → NTR en Postma → Buitenhof.

Sources:
- [Buitenhof: 3 mei 2026](https://www.vpro.nl/buitenhof/artikelen/buitenhof-3-mei-2026)
- [Staatsblad 2021, 297](https://zoek.officielebekendmakingen.nl/stb-2021-297.html)
- [Raad van State-advies W05.21.0080](https://www.raadvanstate.nl/publish/pages/122907/w_05_21_0080.pdf)
- [ERT – About](https://ert.eu/about.)
- [LobbyFacts – ERT](https://lobbyfacts.eu/representative/31941d1652c14afdaf37ef5ed56c7b51/european-round-table-for-industry)
- [NOS – Kritiek op coronabeleid wordt steeds vaker huis-aan-huis verspreid](https://nos.nl/artikel/2352779-kritiek-op-coronabeleid-wordt-steeds-vaker-huis-aan-huis-verspreid)
- [BNNVARA – Wat is De Andere Krant en wat staat erin](https://www.bnnvara.nl/artikelen/wat-is-de-andere-krant-en-wat-staat-erin)
- [BNNVARA – Waar is BNNVARA nou voor](https://www.bnnvara.nl/artikelen/waar-is-bnnvara-nou-voor)
- [NOS – Hoofdredactie NOS Sport treedt terug](https://nos.nl/l/2466818)
- [NOS – Hoofdredactie NOS Sport stapt per direct op](https://nos.nl/l/2467246)
- [Joop – Oud-AIVD'er Jelle Postma …](https://www.bnnvara.nl/joop/artikelen/oud-aivder-jelle-postma-centrumrechtse-partijen-maken-extreemrechtse-terreur-acceptabel)

```

## Runner-metadata

- Exit-code: 0
- Duur: 203.6 s
- Oogst (edit_log-delta van `aanklager-agent`): 20
- Beëindigd: 2026-10-14T17:18:06
