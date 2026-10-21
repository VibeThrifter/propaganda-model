# nieuws-bewijs — 2026-10-15, ronde 3

- Brief: `missies/nieuws_bewijs_brief.md`, blob `651b82555482`
- Account: `nieuws-bewijs`
- Voorregel: `GET /api/agent/reeds_gereageerd` gaf 630, 1627, 2134, 2164, 2168, 2322, 2339, 2635, 3063, 3089. Geen van die argumenten kwam in deze ronde aan de beurt.
- Geclaimd: `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` → doel 218 en 219.
- Geen 429, geen LinkedIn gebruikt (het gaat om bewijs bij een verband, niet om een loopbaan).

## Doel 218 — `relatie:1140` Sylvester Eijffinger → De Telegraaf (expert_legitimatie) — status **klaar**

**De claim.** Eijffinger wordt door De Telegraaf als deskundige gebracht. Volgens de definitie van het mechanisme wordt hij als neutrale autoriteit opgevoerd, terwijl zijn institutionele inbedding buiten beeld blijft. Waar zou tegenbewijs uit bestaan? Weinig Telegraaf-optredens, of Telegraaf-berichten die zijn banden noemen of hem tegenspreken.

**Bestaande argumenten.**
- #1598 (supporting, ongecontroleerd). Bron #779: MA-scriptie Tuk (Universiteit Leiden, 2014), Wayback-pdf. Het citaat ("Absolute 'winnaar' is Sylvester Eijffinger …") staat letterlijk in de pdf, maar noemt De Telegraaf niet.
- #10288 (supporting, verworpen). Dat was de neutrale versie van #1598 zonder het Telegraaf-deel.

**Toets van het bestaande bewijs.** De pdf heb ik via PDFKit omgezet naar tekst. Op p. 20 staat: "Metro, … De Telegraaf, 88 experts verdeeld over 1049 artikelen en Sp!ts, … vertonen de grootste afwijkingen. Bij die drie titels krijgt met name Sylvester Eijffinger de ruimte zijn verhaal te delen". De bron draagt de Telegraaf-claim van #1598 dus wél, alleen het gekozen citaat niet. Ik heb geen ondergraving ingediend, maar een nieuw argument met de passage die het wel zegt. De "20" achter "delen" is het paginanummer en geen voetnoot.

**Neutrale zoekvraag:** hoe bracht De Telegraaf Sylvester Eijffinger als econoom, en met welke context?

**Zoekopdrachten (letterlijk).**
1. DB: `SELECT … FROM relations … WHERE r.id = 1140` en `GET /api/arguments?relation_id=1140`
2. pdf-tekst #779: zoeken naar `Telegraaf` in combinatie met `Eijffinger`; `nevenfunct`, `belangen`, `onafhankelijk`, `neutr`; secties "Matteüseffect en onafhankelijke expertise" en "vijf meest aangevoerde hoogleraren"
3. WebSearch: `Sylvester Eijffinger De Telegraaf econoom`
4. WebSearch: `Groene Amsterdammer 2013 Haegens Bijman hoogleraren economie banden financiële instellingen Eijffinger`
5. WebSearch: `telegraaf.nl Eijffinger hoogleraar Tilburg`
6. WebSearch (allowed_domains telegraaf.nl): `Eijffinger telegraaf.nl` → API-fout, het domein is niet toegankelijk
7. WebSearch: `"Eijffinger" "De Telegraaf" ECB kritiek econoom interview`
8. Boekfragment https://download.boekhuis.nl/9789462406339_fragm-docb.pdf (afscheidsboek): zoeken naar `Telegraaf`, `journalist`, `media`, `column`

**Vondsten.**
- Bron #779 (bestaand, door `POST /api/sources` op url hergebruikt) → **argument #10995** (supporting). Daarin het letterlijke citaat van p. 20 over De Telegraaf, Metro, Sp!ts en Eijffinger. Het is een hercitatie van hetzelfde broncluster (`yoshi_tuk`), geen nieuw cluster.

**Negatieve resultaten.**
- Ik vond geen tweede, onafhankelijke bron (studie of mediakritiek) over Eijffinger in De Telegraaf. De De Groene-publicatie die de scriptie aanhaalt (Haegens & Bijman, 2013) heb ik niet gevonden.
- Ik vond geen Telegraaf-berichten na 2013: telegraaf.nl is voor de zoektool geblokkeerd en de zoekresultaten gaven geen Telegraaf-artikelen.
- Ik vond geen tegenbewijs: geen Telegraaf-berichten die zijn banden noemen of hem tegenspreken, en geen studie die het tegendeel vindt.
- Het boekfragment noemt Eijffinger "voor menig journalist … de stem naar buiten", zonder De Telegraaf te noemen. Niet gebruikt.
- De algemene bevinding van de scriptie dat negen van de tien meestgevraagde economen banden met commerciële instellingen hebben, noemt geen medium. Volgens de specificiteitsregel heb ik die niet ingediend.
- De tabel per dagblad (bijlage 3, figuur 14) is in de tekstlaag onleesbaar; er is geen letterlijk citaat van te maken.

**Mechanisme.** `expert_legitimatie` past. Er is geen aspect-argument ingediend.

**Looptijd.** Het verband heeft geen `active_from`. De periode 2008-2013 is de meetperiode van de scriptie en geen begin van het verband. Ik heb niets ingediend; dat staat in het verslag, en de datumzoeker kan verder zoeken.

## Doel 219 — `relatie:158` DPG Media → RTL Nieuws (eigendomsconcentratie) — status **klaar**

**De claim.** DPG Media is eigenaar van RTL Nieuws, via RTL Nederland. Tegenbewijs zou zijn: geen eigendom, of een eigendom dat begrensd is.

**Bestaande argumenten.**
- #160 (verouderd). Bron #105 (NOS, 27-06-2025).
- #10298 (supporting, geverifieerd). Bron #2823 (mena.nl, 27 juni 2025). Het citaat "DPG Media heeft de overname van RTL Nederland officieel afgerond." staat letterlijk op de pagina, die ook de gescheiden redacties van RTL Nieuws en NU.nl noemt. De bron draagt de claim, dus geen ondergraving.

**Afwijking.** Het verband staat op `active_from` 2019; dat is een seedwaarde zonder edit_log. De overname werd in december 2023 aangekondigd en op 1 juli 2025 afgerond. De verwante verbanden #9, #20, #329 en #1061 (DPG/ACM → RTL Nederland) staan al op 2025-07-01.

**Neutrale zoekvraag:** wanneer werd RTL Nederland, met RTL Nieuws, eigendom van DPG Media, en onder welke voorwaarden?

**Zoekopdrachten (letterlijk).**
1. DB: `SELECT … FROM relations … WHERE r.id = 158`, `GET /api/arguments?relation_id=158`, de verwante verbanden tussen entiteit 1, 8 en 88, en de argumenten met citaten op relaties 9, 20, 77, 329 en 1061
2. DB: precedenten voor mechanismen bij `relation_type='eigendom'` (goedgekeurd): eigendomsconcentratie 76, systemisch_eigenaarschap 27, …
3. WebSearch: `DPG Media overname RTL Nederland afgerond datum`
4. Fetch: https://mena.nl/mededinging/dpg-media-rond-overname-rtl-nederland-af
5. Fetch: https://nos.nl/artikel/2572676-dpg-mag-rtl-overnemen-wel-onder-strikte-voorwaarden
6. WebSearch: `"1 juli 2025" DPG Media RTL Nederland overname`
7. Fetch: https://www.bertelsmann.com/de/media/nachrichten/verkauf-von-rtl-nederland-an-dpg-media-genehmigt.html (de afronding staat er alleen als verwachting: "expects to close … 1 July 2025")
8. Fetch: https://www.vrt.be/vrtnws/nl/2025/06/27/dpg-mag-rtl-nederland-overnemen-onder-stricte-voorwaarden/ (geen bruikbare tekst)
9. WebSearch: `RTL Group completes sale of RTL Nederland to DPG Media July 2025`
10. WebSearch: `RTL Nederland vanaf vandaag officieel onderdeel van DPG Media`
11. Fetch: https://www.acm.nl/nl/publicaties/dpg-media-krijgt-vergunning-voor-overname-rtl-nederland-eindmededeling (vergunning 27 juni 2025, geen afronding)
12. Fetch: https://adalliance.nl/over-ad-alliance/nieuws/rtl-nederland-vanaf-1-juli-2025-onderdeel-van-dpg-media/
13. pdf: https://www.cvdm.nl/documents/10801/84454-CvdM-Mediamonitor_2025-TG_PAC_PDFA.pdf, zoeken naar `1 juli 2025` en naar `RTL Nieuws` in combinatie met `DPG`

**Vondsten.**
- Bron #1605 (Mediamonitor 2025, CvdM; bestaand, op url hergebruikt) → **argument #10996** (supporting, `property=active_from`, `property_value=2025-07-01`). Citaat: "Per 1 juli 2025 nam DPG Media RTL Nederland over van RTL Group."
- Bron #1605 → **argument #10997** (contradicting, `property=influence`). Citaat: "Voorwaarden zijn onder andere dat RTL Nieuws en NU.nl onafhankelijke stichtingen krijgen met een prioriteitsaandeel. Ook moeten de websites en apps van RTL Nieuws en NU.nl voor consumenten gratis toegankelijk blijven en als afzonderlijke nieuwsmerken blijven bestaan."
- Kanttekening: stap 10c overschrijft geen bestaande datum. De 2019 blijft dus staan tot een mens hem vervangt. Dat staat in het verslag.

**Negatieve resultaten.**
- Ik vond geen bron waarin de afronding met jaartal én RTL Nieuws in één zin staan. De Mediamonitor noemt beide op dezelfde pagina's, maar niet in één zin.
- Ik vond niets dat het eigendom zelf tegenspreekt.
- De persmededeling van RTL Group (via Bertelsmann) geeft 1 juli 2025 alleen als verwachte datum. Niet gebruikt.

**Mechanisme.** `eigendomsconcentratie` volgt het dominante precedent, met 76 goedgekeurde eigendomsrelaties. Ik heb geen aspect-argument ingediend.

## Stance-balans van de ronde

- Steun: **2**. Daarvan is #10995 bewijs en #10996 een looptijd-aspect.
- Tegen (roots met bron): **1** (#10997, invloed)
- Context: **0**
- Ondergraving: **0**
- Nieuwe bronclusters: **0**. Hercitaties: 2 (`yoshi_tuk` #779, `commissariaat_voor_de_media` #1605). Beide bronnen bestonden al; `POST /api/sources` hergebruikte ze op url, dus `resultaat.source_ids` is leeg.
- 409/400 bij het indienen: geen.
- Wachtrij: doel 218 en 219 → `klaar` (`PATCH /api/nieuws/doelen/<id>`).
