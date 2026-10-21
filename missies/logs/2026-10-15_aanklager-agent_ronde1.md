# Onbewaakte ronde — aanklager-agent · ronde1 · 2026-10-15

- Brief: `missies/aanklager_brief.md` (blob `b985acb45edc`)
- Account: `aanklager-agent`
- Gestart: 2026-10-15T10:02:54

## Sessie-uitvoer

```
# Logboek aanklager-agent · 2026-10-15 · ronde1

- Brief: `missies/aanklager_brief.md`, blob `b985acb45edc`
- Account: `aanklager-agent`
- Ik schrijf dit logboek niet zelf naar het bestand. De runner heeft `missies/logs/2026-10-15_aanklager-agent_ronde1.md` al in append-modus open en zet deze sessie-uitvoer erin.

## Voorregel en werklijst

- **Voorregel (10:03):** `GET /api/agent/reeds_gereageerd` gaf 61 id's, van 3477 tot en met 10137. Geen van de claims die ik behandelde stond erop.
- **Werklijst (10:03):** `python3 scripts/automatische_beoordeling.py --open-a2` gaf 36 claims.
- **Overgeslagen, eigen werk van dit account** (dat zou zelfcertificering zijn, 403): 9741, 9740, 7949 en 7840.
- **Behandeld:** de 12 oudste claims van anderen, het maximum per ronde: 9835, 9836, 9959, 10157, 10158, 10180, 10182, 10184, 10211, 10212, 10242 en 10243.
- **Doorgeschoven naar een volgende ronde:** 10244, 10271, 10272, 10299, 10337, 10338, 10341 en de NPO-reeks 10347–10360.

## Zoekopdrachten, letterlijk

**Database** (sqlite3, alleen lezen, 10:03–10:05). Voor elk van de 12 argumenten:
- `select * from arguments where id=?`
- de relatie, met join op `entities` en `mechanisms`, of de entiteit
- de citaties: `citations` join `sources` plus `group_concat(location)` uit `source_locations`
- `select fase,verdict,door,detail from immuun_oordelen where argument_id=?`
- de reacties: `select … from arguments where parent_argument_id=?`

Daarnaast:
- De `politieke_positie`-argumenten op de entiteiten 974, 1055, 276, 118 en 176, met hun bron-id's.
- `reviseert_id` en `vervangen` van 9930, 9932, 10165, 9840, 9843, 8099, 9731, 10183 en van de 12 claims.
- De status van de originelen 2909, 2939, 782, 1108, 1116 en 1943.
- `select argument_id, source_id from citations where argument_id in (1943,2909,2939,782,1108,1116,9835)`
- De argumenten op de relaties 1963, 1403, 168, 363 en 378.
- Het lot van mijn ondergravingen uit de vorige ronde, 10149–10156: `immuun_oordelen` en `edit_log`.
- `grep "Feitelijke versie"` in `scripts/`, en `sed -n 640,760p scripts/automatische_beoordeling.py`.
- `grep dedup|per bron|source_id|cluster politiek.py`
- `sed -n 1,140p missies/ideoloog_brief.md`

**Web** (10:05–10:07):
- WebFetch `https://nos.nl/artikel/2582876-wilders-kritisch-over-migratie-partijen-verwijten-hem-gebrek-aan-daadkracht`
- WebSearch `Shula Rijxman onderzoek privérelatie Hammersma conclusie 2022 geen belangenverstrengeling`
- WebSearch `NOS interview Wilders tien jaar PVV februari 2016 kritiek reactie hoofdredactie`
- WebSearch `Groene Amsterdammer UvA nos.nl asiel 72 procent migratieartikelen asielcrisis onderzoek`
- WebFetch `https://nos.nl/artikel/2088385-wilders-geen-concessies-over-terugdringen-islam`
- WebSearch `Kamerbrief Dijkgraaf ADR rapport Hammersma Rijxman "misbruik of vermenging van belangen"`
- WebFetch `https://nos.nl/l/2446183`. De zin over "misbruik of vermenging van belangen" staat niet in het NOS-bericht.
- WebFetch en curl `https://www.nhnieuws.nl/nieuws/309044/minister-vriendschap-rijxman-en-hammersma-had-schijn-van-belangenverstrengeling`. Het citaat staat er letterlijk in.
- WebSearch `René Cuperus column Volkskrant 2013 "Wiardi Beckman Stichting" medewerker columnist`
- curl `https://www.wbs.nl/sites/default/files/2017-09/wbs_jaarverslag_2013.pdf`, gelezen met PDFKit: de context van de zin "op persoonlijke titel".
- WebSearch `EO NPO bezuinigingen 2018 Arjan Lock juridische stappen uitkomst levensbeschouwelijke programma's`

## Per claim: anker, route en id

| Claim | Doel · stance | Route | Aanval | Certificaat |
|---|---|---|---|---|
| 10182 kritiek van partijleiders in NOS-bericht 17-9-2025 | rel 1963 (Wilders → NOS, framing) · tegen | ondergraving (non_sequitur): volgens de bron ging de kritiek over het uitblijven van resultaten ("niets mee gedaan", "gebrek aan daadkracht"), niet over de framing van migratie als asielkwestie | **#10366** | 9590 aangevallen |
| 10180 Cuperus-column in het WBS-jaarverslag 2013 | rel 168 (WBS → Volkskrant, expert_framing) · steun | ondergraving (citaat_dekking): de bron zegt "op persoonlijke titel", dus niet namens de WBS; het citaat draagt de band Cuperus–Volkskrant | **#10367** | 9589 aangevallen |
| 9836 Rijxman meldde de privérelatie met de OCW-top niet | rel 378 (Rijxman → OCW, cooptatie) · steun | de claim zelf overleeft; de andere kant staat als **weerlegging-root** op rel 378: Kamerbrief Dijkgraaf, ADR vond "geen misbruik of vermenging van belangen" (bron **2864**, NH Nieuws/AT5 27-9-2022, verbatim) | **#10365** (root; `smaad_hold=1`, wacht op de smaadtoets) | 9582 overleefd |
| 9835 YouTube verwijst naar regels tegen complottheorieën | rel 1403 · tegen (confound) | certificaat | — | 9581 overleefd |
| 9959 EO overwoog juridische stappen tegen de NPO (2018) | rel 363 · steun | certificaat | — | 9583 overleefd |
| 10184 Joop: geen kritische vragen aan Wilders (2016) | rel 1963 · steun | certificaat: het NOS-artikel 2088385 zelf bevat geen tegenwerpingen | — | 9591 overleefd |
| 10212 NOS 22-4-2024: 'Asielcrisis' tussen aanhalingstekens | rel 1963 · tegen | certificaat | — | 9592 overleefd |
| 10157 Cuperus · economisch:links | ent 974 · steun | dubbeltelling met het levende #2909 (zelfde bron 1681, zelfde as) | — | 9584 onbeslist |
| 10158 Scholte · anti-establishment | ent 1055 · context | dubbeltelling met het levende #2939 (bron 1743) | — | 9585 onbeslist |
| 10211 Comvalius · cultureel:progressief | ent 276 · steun | dubbeltelling met #782 (bron 228); het citaat is bovendien een functiefeit en geen uiting | — | 9586 onbeslist |
| 10242 Van den Brink · establishment | ent 118 · steun | dubbeltelling met #1108 (bron 459); het citaat gaat bovendien over toon en niet over substantie | — | 9587 onbeslist |
| 10243 Muusse · anti-establishment | ent 176 · steun | dubbeltelling met #1116 (bron 466) | — | 9588 onbeslist |

## Fout in de beoordeling, voor de eigenaar

**Wat er gebeurt.**
- `stap_feitelijke_versies` → `feitelijke_versie()` (`scripts/automatische_beoordeling.py:663`) dient een "Feitelijke versie van #X" in als gewoon nieuw argument, zonder `reviseert_id`.
- Is #X zelf een neutrale versie (een revisie van een gemerged argument Y), dan raakt de opvolging kwijt. Y blijft levend naast de nieuwe versie.

**Gevolg.**
- Bij een merge staan er twee `politieke_positie`-signalen uit dezelfde bron op dezelfde as.
- `politiek.py` ontdubbelt niet per bron, dus die bron telt dubbel.
- Dat raakt de vijf signalen 10157, 10158, 10211, 10242 en 10243. Daarom gaf ik ze `onbeslist` en niet `overleefd`.

**Bij relatie-argumenten is het minder erg.**
- Daar ontdubbelt de score per bron (M1.2).
- Wel blijft #1943 levend, met "(medische) misinformatie" erin, wat volgens de smaadtoets niet in de bron staat.

**Mogelijke oplossing:** de feitelijke versie indienen als revisie van `orig.reviseert_id`, als het origineel er een heeft. Dit heb ik niet zelf aangepast; het valt buiten de missie.

**Op welke ondergravingen de beoordeling afwijst.**
- Alle 7 ondergravingen uit ronde4 die over de indeling op een as gingen (10149–10155), zijn afgewezen.
- Reden van de bronchecker: "het bezwaar gaat over de duiding, niet over de feitelijke inhoud."
- Alleen ondergravingen over de vraag of de bron over *dat verband* gaat, houden stand.
- Gevolg: A2-bezwaren tegen de as-indeling van politieke signalen kunnen in de huidige beoordeling niet winnen.

## Negatieve resultaten (alleen in dit logboek)

- **9835 (YouTube/Lange Frans):** geen tegenbron gevonden.
- **9959 (EO):** geen tegenbron gevonden. De uitkomst van het geschil uit 2018 vond ik ook niet; dat is geen tegenbewijs.
- **10184:** geen reactie van de NOS-hoofdredactie op de Joop-kritiek gevonden.
- **10212:** het Groene/UvA-onderzoek (72%) vond ik via zoeken niet terug. Ik kon dus niet nagaan of het woorden tussen aanhalingstekens meetelt.
- **10180:** geen Volkskrant-byline gevonden die Cuperus als WBS-medewerker noemt.
- **Ontbrekende looptijd**, voor de datumzoeker:
  - Rel 378 (Rijxman → OCW) en rel 363 (NPO → EO) hebben geen `active_from`.
  - Rel 168 (WBS → Volkskrant) heeft `active_from` 1945. Dat is de oprichting van de WBS, niet het begin van dit verband.
- Geen 429. LinkedIn niet gebruikt.

## Stance-balans van de ronde

- **Certificaten:** 2 aangevallen, 5 overleefd, 5 onbeslist.
- **Aanvallen:** 1 weerlegging en 2 ondergravingen.
- **Nieuwe bijdragen aan het model:** 0 steun, 3 tegen (#10365 root, #10366 en #10367 reacties), 0 context.
- **Nieuwe bron:** 2864.
- Ik heb geen entiteiten of relaties aangemaakt, en geen status gewijzigd, niets gemerged en niets geclassificeerd.

---

Ronde 1 is klaar: ik heb 12 claims van anderen behandeld. Twee heb ik met een ondergraving aangevallen, en bij één verband heb ik een gesourcete weerlegging gezet. Vijf claims houden stand.

Vijf politieke signalen blokkeer ik voorlopig (`onbeslist`), omdat ze bij een merge dubbel zouden tellen. Dat komt door een fout in de beoordeling: de "feitelijke versie" vervangt het origineel niet. Die fout moet in de code opgelost worden en staat hierboven beschreven.

Sources:
- [NOS 17-9-2025, Wilders kritisch over migratie](https://nos.nl/artikel/2582876-wilders-kritisch-over-migratie-partijen-verwijten-hem-gebrek-aan-daadkracht)
- [NH Nieuws/AT5 27-9-2022, Rijxman en Hammersma](https://www.nhnieuws.nl/nieuws/309044/minister-vriendschap-rijxman-en-hammersma-had-schijn-van-belangenverstrengeling)
- [NOS 27-9-2022, Dijkgraaf over de melding van de klokkenluider](https://nos.nl/l/2446183)
- [NOS 22-2-2016, Wilders-interview](https://nos.nl/artikel/2088385-wilders-geen-concessies-over-terugdringen-islam)
- [WBS-jaarverslag 2013](https://www.wbs.nl/sites/default/files/2017-09/wbs_jaarverslag_2013.pdf)
- [NOS 2-7-2018, EO dreigt NPO met juridische stappen](https://nos.nl/artikel/2239587-eo-dreigt-npo-met-juridische-stappen-om-bezuinigingen)
- [nieuws.nl, Bezuinigingen dreigen EO hard te raken](https://nieuws.nl/entertainment/bezuinigingen-dreigen-eo-hard-te-raken)
- [Joop 22-2-2016](https://www.bnnvara.nl/joop/artikelen/nos-durft-geen-kritische-vraag-aan-wilders-te-stellen)

```

## Runner-metadata

- Exit-code: 0
- Duur: 356.9 s
- Oogst (edit_log-delta van `aanklager-agent`): 17
- Beëindigd: 2026-10-15T10:08:51
