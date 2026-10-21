# Missielog: looptijd van de Clingendael-banden met `active_from = 1983`

- **Datum:** 2026-10-16
- **Account:** `assistent` (bijdrager). Alles is ingediend via de REST-API op `localhost:5000` en landt `voorgesteld`. Ik heb niets gemerged, geen status gewijzigd en niets in de DB geschreven. De DB is alleen read-only gelezen.
- **Opdracht:** op goedgekeurde banden van Clingendael Instituut (#43) staat `active_from = 1983`. Per band nagaan of dat het begin van *dít* verband is of alleen het oprichtingsjaar van Clingendael. CLAUDE.md § "Looptijd: zonder jaartal geen verband" en § "Bestaan begrenst", en `missies/README.md` § Looptijd.

## Herkomst van de 1983

Geen enkel argument of citaat op deze banden noemt 1983. Er staan geen looptijd-aspectargumenten op en de `edit_log` heeft geen regel die de datum zette. De waarde komt uit `scripts/set_temporal_data.py` (toegevoegd in commit `b0d4ccd` van 2026-06-02, verwijderd in `efc2ad8` van 2026-10-13). Dat script gaf Clingendael een hardgecodeerd oprichtingsjaar `("1983", None, True)`. Daarna zette het op elk verband zonder begin `MAX(active_from)` van bron en doel:

> "Een relatie kan niet bestaan vóór beide betrokken entiteiten: neem het laatste (max) active_from van bron en doel."

Daarom staat er 1983 op 36, 153, 154, 236, 237 en 285. Rel. 235 (→ RTL Nederland, afgewezen) kreeg zo 1989, het "oprichtingsjaar" van RTL.

**Volledige lijst** (`relations` met bron of doel 43 en `active_from = 1983`):
- **Goedgekeurd:** 36, 153, 154, 236, 237 en 285.
- **Afgewezen, niet behandeld:** 64 (NAVO → Clingendael, financiering), 161 (→ de Volkskrant) en 162 (→ De Telegraaf). Rel. 235 (→ RTL, 1989) is ook afgewezen. Worden deze ooit heraangemeld, dan dragen ze dezelfde afgeleide datum.

**Bestaan van Clingendael.** De oprichting in 1983 klopt. Dat staat in de Kamerbrief van 19-03-2009 en in het IOB-rapport nr. 318 (zie onder). Clingendael zegt het zelf ook: "The Netherlands Institute of International Relations 'Clingendael' was founded in 1983" (clingendael.org/history, via Wayback 2026-08-30). De wettelijke grondslag is Stb. 1982, 752, de Wet van 29 december 1982 "houdende machtiging tot mede-oprichting van de Stichting Nederlands Instituut voor Internationale Betrekkingen «Clingendael»", met als artikel 1: "Onze Minister van Defensie wordt gemachtigd mede op te richten de Stichting …". Geen Clingendael-band kan dus vóór 1983 beginnen.

## Uitkomst per band

| Rel. | Verband | Huidig | Bevinding | Voorstel | Ingediend |
|---|---|---|---|---|---|
| 154 | Min. Buitenlandse Zaken → Clingendael (financiering) | 1983 | Bevestigd: basissubsidie sinds de oprichting in 1983 | 1983 laten staan | arg. **#11226** (bron #3226) |
| 153 | Min. Defensie → Clingendael (financiering) | 1983 | Bevestigd: dezelfde zin. De minister van Defensie kreeg bovendien bij wet de machtiging om Clingendael mede op te richten (Stb. 1982, 752) | 1983 laten staan | arg. **#11227** (bron #3226) |
| 237 | Clingendael → AD (beinvloeding, expert_framing) | 1983 | Bevestigd: het AD haalde in 1983 al Clingendael-onderzoek aan (25-03-1983 en 26-11-1983) | 1983 laten staan | arg. **#11228** (bron #3228) |
| 236 | Clingendael → NRC (beinvloeding, expert_framing) | 1983 | Bevestigd: NRC Handelsblad 25-01, 13-05, 29-08 en 21-10-1983. Geen enkele 1983-tekst noemt het jaartal zelf | 1983 laten staan (klopt) | niets: de poort eist een citaat met het jaartal |
| 36 | Clingendael → NOS (beinvloeding, expert_framing) | 1983 | 1983 is niet gedocumenteerd. Vroegst gevonden: NOS *Panoramiek* van 15-01-1984 | **1983 → 1984** (bron geeft 1984-01-15) | niets (zou botsen met het gevulde veld) |
| 285 | NAVO → Clingendael ("NAVO-financiering beïnvloedt Clingendael-output") | 1983 | 1983 is niet gedocumenteerd. Vroegste NAVO-betaling: inkomstentabel 2017. Die van 2016 noemt geen NAVO-onderdeel | **1983 → 2017**, of 2025 als de band als NATO Public Forum-partnerschap bedoeld is | niets (zou botsen met het gevulde veld) |

**Extra:** arg. **#11229** op entiteit #43 bevestigt de oprichting: `active_from` 1983, bron #3226. Stap 10c merget een gelijke datum zonder iets te wijzigen. Daarna is de oprichtingsdatum beschermd en begrenst ze alle Clingendael-banden aantoonbaar.

Ik heb #11226–#11229 read-only gecontroleerd met `server.looptijd_besluit`. Alle vier geven `al: True` (bevestiging) en wachten alleen nog op A1 (bronchecker) en de stemtoets. Met de functies van de bronchecker zelf (`haal_url` en `zoek_citaat`) is elk citaat letterlijk teruggevonden: de Kamerbrief-pdf via PDFKit en de AD-tekst via resolver.kb.nl.

## Ingediend (alles `voorgesteld`)

**Bronnen.** De classificatie is een voorstel en adviserend.
- **#3226:** Kamerbrief "IOB-evaluatie van het Instituut Clingendael, met de beleidsreactie" (WRA-02/09, 19-03-2009), van minister Verhagen (BZ) en minister Van Middelkoop (Defensie). Type `overig`, voorstel `primair`/`nl_systeem`. Locaties:
  - #5730 https://www.iob-evaluatie.nl/site/binaries/site-content/collections/documents/2008/10/01/clingendael-subsidieovereenkomst/Beleidsreactie+-+Subsidieovereenkomst+Clingendael.pdf
  - #5734 de IOB-landingspagina
- **#3227:** IOB Evaluaties nr. 318, *Samenwerking met Clingendael* (oktober 2008). Type `rapport`, voorstel `institutioneel`/`nl_systeem`. Locaties:
  - #5731 …/Rapport+-+Subsidieovereenkomst+Clingendael.pdf
  - #5735 de IOB-landingspagina
  - Deze bron wordt niet geciteerd (zie "Let op").
- **#3228:** Algemeen Dagblad 26-11-1983, "Acht u de kans groot op het uitbreken …" (peilingoverzicht). Type `nieuwsartikel`, voorstel `regulier`/`nl_systeem`. Locaties:
  - #5732 https://resolver.kb.nl/resolve?urn=KBPERS01:003010023:mpeg21:a00408:ocr (OCR-tekst; de bronchecker leest die)
  - #5733 dezelfde URN zonder `:ocr`, die doorstuurt naar de Delpher-viewer

**Argumenten.** Alle vier zijn `supporting`, met `property=active_from` en `property_value=1983`. De citaties zijn `verbatim_quote`.
- **#11226** (rel. 154) en **#11227** (rel. 153), bron #3226 p. 1: "De ministeries van Buitenlandse Zaken en Defensie verstrekken sinds de oprichting van het instituut Clingendael in 1983 een basissubsidie aan dit instituut." Het IOB-rapport (p. 15, Terms of Reference p. 1) zegt hetzelfde. De ToR voegen toe: "gezamenlijk een basissubsidie … steeds verstrekt voor een periode van vier jaar".
- **#11228** (rel. 237), bron #3228: "Verwacht u een kernoorlog te overleven? (Nipo voor het Instituut Clingendael, september 1983): 72% nee, 3% ja, 25% weet niet." In de redenering staat ook het vroegere AD-stuk van 25-03-1983 (https://resolver.kb.nl/resolve?urn=KBPERS01:002999022:mpeg21:a00076:ocr): "Tot deze conclusie komt drs. J. W. van der Meulen in een rapport van het Nederlands Instituut voor Internationale betrekkingen en ”Clingendael”." Die tekst noemt het jaartal niet, en daarom is ze niet als citaat gebruikt.
- **#11229** (entiteit 43), bron #3226, met hetzelfde citaat als #11226.

## Voorgestelde correcties (maintainerwerk, niet ingediend)

1. **Rel. 36 (Clingendael → NOS):** `active_from` van 1983 naar **1984**. De bron noemt de dag (1984-01-15). Vroeger vond ik niets.
   - **Bron:** Beeld en Geluid-catalogus, NOS *Panoramiek*, uitzending 15-01-1984 (PID URN:NBN:NL:IN:20-PGM129670). https://zoeken.beeldengeluid.nl/program/urn:vme:default:program:2101608050038706131. Machineleesbaar: https://zoeken-api.beeldengeluid.nl/gp/api/v1/model/programs/urn:vme:default:program:2101608050038706131/metadata (velden `nisv.sortdate` / `publication.begindate` = "1984-01-15").
   - **Citaat** (nisv.summary): "STUDIO-INTERVIEW (alleen op Umatic) van Dirk Dragstra met Huib Hendrikse, Rusland-deskundige Clingendael, over de positie van de USSR tov China en de VS die werken aan een verbeterde relatie."
   - **Volgende gevonden uitzendingen:**
     - *Panoramiek* "Vakature Kremlin" van 12-02-1984, urn …2101608050038969731: "STUDIO-INTERVIEW - van Dirk Dragstra met Huib Hendrikse, Sovjetexpert van het Instituut Clingendael".
     - *Het Capitool* van 19-01-1986 (C.J. Visser, Instituut Clingendael). Dat staat ook in de tv-gidsen van NRC, de Volkskrant en Nieuwsblad van het Noorden van 18-01-1986.
   - **Kanttekening:** de catalogus is voor 1983 niet volledig (Journaal-items zijn selectief beschreven). Het werkelijke begin ligt tussen 1983 en 15-01-1984. 1984 is de vroegste gedocumenteerde waarde, 1983 is een afgeleide gok.
2. **Rel. 285 (NAVO → Clingendael):** `active_from` van 1983 naar **2017**.
   - **Bron:** *The Clingendael Institute, Income 2017* (bijlage bij het jaarverslag 2017), https://web.archive.org/web/20220307202433/https://www.clingendael.org/pub/2018/clingendael-annual-report-2017/_/pdf/Clingendael-Income-Table.pdf. Letterlijk staan in de schijf "€1,000 - €5,000" de regels "NATO" "€ 2,250" en "Shape Finance" "€ 4,320". De paginakop is "The Clingendael Institute Income 2017".
   - **2016** (https://www.clingendael.nl/pub/2017/clingendael_annual_report_2016/_/pdf/Clingendael-Income-Table.pdf) noemt geen NAVO-onderdeel. Wel "Netherlands Permanent Representation NATO" voor € 2,400, maar dat is de Nederlandse Staat.
   - **2018** (Wayback 20211020055510, …/2019-10/Clingendael-Income-Table-2018.pdf) noemt "NATO HQ", "Shape Finance & Acquisition Directorate (Nato)" en "NATO Emerging Security Challenges Division".
   - **Kanttekening:** de tabellen beginnen bij 2016, dus over eerdere jaren is niets openbaar. Het gaat om kleine bedragen, waarschijnlijk betalingen voor opdrachten of cursussen. De twee geverifieerde argumenten op deze band (#3466, #3472) gaan over het NATO Public Forum van 24–25 juni 2025. Leest de maintainer de band als dat partnerschap, dan is het begin 2025.
3. **Rel. 236 (Clingendael → NRC):** 1983 klopt, geen correctie. Het jaartal staat in geen enkele tekst, dus de poort `looptijd_besluit` ("geen citaat noemt het jaar") laat een bevestigend argument niet toe. De bronnen (KB-OCR):
   - **25-01-1983**, opiniestuk in NRC Handelsblad (https://resolver.kb.nl/resolve?urn=KBNRC01:000027590:mpeg21:a0078:ocr): "D. W. Baron van Lynden was van 1974 tot 1982 ambassadeur te Bonn en is thans voorzitter van het Bestuur van het Nederlandse Instituut voor Internationale Betrekkingen "Clingendael"."
   - **13-05-1983**, opiniestuk (…KBNRC01:000027613:mpeg21:a0086:ocr): "Drs. J. G. Siccama is wetenschappelijk medewerker aan het Nederlands instituut voor internationale betrekkingen Clingendael."
   - **21-10-1983**, nieuwsbericht van de diplomatieke redacteur, "Volgens Nipo wijst 38 pct. Nederlanders raketten af" (…KBNRC01:000027879:mpeg21:a0044:ocr): "aldus een onderzoek dat het Nipo op 26 en 27 september onder 960 Nederlanders heeft uitgevoerd in opdracht van het Instituut voor Internationale-betrekkingen Clingendael in Den Haag."
   - Het Siccama-stuk noemt wel "december 1983", maar dat gaat over de onderhandelingen tussen de VS en de Sovjet-Unie en niet over dit verband. Ik heb het niet gebruikt.

## Let op (eigen fout)

Ik heb de IOB-landingspagina (https://www.iob-evaluatie.nl/documenten/2008/10/01/clingendael-subsidieovereenkomst) als tweede url aan **zowel #3226 als #3227** gehangen (locaties #5734 en #5735). Stap 8b (`opschonen.bron_dubbel_besluit`) voegt een bron met een gedeelde url samen met de oudste. Waarschijnlijk gaat #3227 dus op in #3226.
- **Waarom het onschadelijk is:** #3227 heeft geen citaties. Bij een samenvoeging krijgt #3226 de rapport-pdf als extra locatie, en de eerste url (de Kamerbrief-pdf, die de bronchecker leest) blijft gelijk. Om die reden is #3227 nergens geciteerd en gebruikt #11229 de Kamerbrief.
- **Herstel:** een bijdrager kan geen locatie verwijderen. Moeten de twee documenten apart blijven, dan kan een maintainer locatie #5735 weghalen.

## Bredere bevinding (niet behandeld)

Dezelfde afleiding zit waarschijnlijk op veel meer verbanden. Read-only telling: **184 goedgekeurde verbanden** hebben een `active_from` (alleen jaartal) die precies gelijk is aan het oprichtingsjaar van het jongste eindpunt. Bij **177** daarvan staat geen looptijd-argument en geen `edit_log`-regel die de datum zette: 141 zijn aangemaakt in juni 2026, 35 in juli en 1 in oktober. `RELATIE-ZONDER-JAAR` ziet ze niet, omdat ze een jaartal hebben. Sommige kloppen toevallig, zoals BZ en Defensie hier. Ze zijn wel allemaal ongebronde afleidingen. Een gerichte datumzoeker-ronde of een maintainerbesluit (leegmaken, zodat de datumzoeker ze oppakt) zou dit oplossen.

Query (read-only):
```sql
WITH r AS (SELECT r.id, r.status, r.active_from, CASE WHEN CAST(s.active_from AS INTEGER) >= CAST(IFNULL(t.active_from,0) AS INTEGER) THEN s.active_from ELSE t.active_from END AS maxa
  FROM relations r JOIN entities s ON s.id=r.source_id JOIN entities t ON t.id=r.target_id
  WHERE r.active_from IS NOT NULL AND NOT r.vervangen)
SELECT status, COUNT(*) FROM r WHERE active_from = maxa AND length(active_from)=4
  AND NOT EXISTS (SELECT 1 FROM arguments a WHERE a.relation_id=r.id AND a.property='active_from')
  AND NOT EXISTS (SELECT 1 FROM edit_log e WHERE e.table_name='relations' AND e.record_id=r.id AND e.new_value LIKE '%active_from%')
GROUP BY status;
```

## Waar gezocht (queries)

**Web (WebSearch/WebFetch):**
- `Clingendael Instituut opgericht 1983 geschiedenis`
- `Clingendael Institute history founded 1983 Ministry of Foreign Affairs funding`
- `"Clingendael" subsidie ministerie van Buitenlandse Zaken en Defensie sinds oprichting`. Deze vond de IOB-documenten en Stb. 1982, 752.
- `"IOB-evaluatie van het Instituut Clingendael" 2009 Kamerbrief`
- `"basissubsidie" Clingendael 1983 Buitenlandse Zaken Defensie officielebekendmakingen`
- `nrc.nl/nieuws/1983 Clingendael Nipo kruisraketten` en `site:nrc.nl Clingendael 1983`. Er is geen NRC-archiefpagina uit 1983 online.
- `Clingendael "NATO Public Diplomacy Division" …`, `Clingendael income table NATO …`, `"Clingendael" "Income Table" 2017 OR 2018 OR 2019 pdf` en `"Clingendael" "financial support" OR "funded by" … NATO`
- `Beeld en Geluid catalogus open data API SPARQL …`

**KB-krantenarchief.** Ik gebruikte de SRU-API (`jsru.kb.nl/sru`, collectie `DDD_artikel`) en `resolver.kb.nl` voor de OCR, niet de Delpher-website. Beide gaven 200. De bronchecker kan resolver.kb.nl-OCR lezen; dat heb ik getest met `haal_url`.
- `Clingendael AND papertitle="NRC Handelsblad"` voor 1983–1984, en met `1983` erbij voor 1983 en 1984–1986. Ook `Clingen*` en `"internationale betrekkingen"`.
- `Clingendael AND papertitle="Algemeen Dagblad"` voor 1983–1985, en met `1983` erbij.
- `Clingendael AND (NOS | journaal | Panoramiek | Capitool | "oog op morgen" | "Den Haag vandaag" | NOS-journaal | NOS-laat | NOS-radio | "Radio 1" | "Nederland 1/2" | "Ned. 1/2" | Hilversum | televisie | radio)` voor 1983–1986.
- `Clingendael AND (NAVO OR NATO)` voor 1983–1985. Daarnaast een scan van 76 artikelen (1983–1995) op NAVO-financiering van Clingendael: geen treffer. Het dichtstbij komt de Volkskrant van 16-03-1989, over een leerstoel voor Neuman gefinancierd door de Stichting voor Strategische Studies, niet door de NAVO.

**Beeld en Geluid.** Ik gebruikte `zoeken-api.beeldengeluid.nl/gp/api/v1/search/refine`, `/model/programs/<urn>` en `/metadata`. De SPARQL-endpoint `cat.apis.beeldengeluid.nl` heeft geen tekstindex (time-out).
- `q=Clingendael`: 2959 treffers. Ik bekeek de oudste 100, en die dekken alles vóór 19-11-1990. In 1983 alleen AVRO *Televizier*, TROS *Aktua* en NTR. NOS voor het eerst op 15-01-1984.
- `q="Instituut voor Internationale Betrekkingen"`: NOS voor het eerst op 21-10-1984 (*Panoramiek*).
- `q=Clingendaal`: niets van de NOS.

**Clingendael-inkomstentabellen.** Live 2016 en 2021. Via Wayback 2017, 2018, 2019 en 2023. 2020 en 2022 gaven een Wayback-verbindingsfout en zijn niet nodig voor het begin.

**DB (read-only):** de relaties met bron of doel 43, de argumenten en citaties op 36/153/154/236/237/285 en 64/161/162/235, de `edit_log` op die relaties en op entiteit 43, `looptijd_onderzoek`, en bestaande bronnen met iob-evaluatie, resolver.kb.nl of beeldengeluid in de url.

**Niet gelukt of niet gebruikt:**
- clingendael.org gaf 403 aan curl en WebFetch. Ik las het via Wayback.
- De oude NATO-sponsorpagina (`nato.int/structur/oip/sponsors/sem-prog.htm`) gaf 404. De Wayback-versie van 2002 noemt Clingendael niet.
- Delpher zelf heb ik niet nodig gehad.
- Wikipedia alleen als vindplaats. Het is niet geciteerd.
