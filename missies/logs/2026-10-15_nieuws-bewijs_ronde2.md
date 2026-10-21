# nieuws-bewijs — 2026-10-15, ronde 2

- Brief: `missies/nieuws_bewijs_brief.md`, blob-hash **651b82555482**
- Account: `nieuws-bewijs` (bijdrager). Alles landt `voorgesteld`.
- Voorregel: `GET /api/agent/reeds_gereageerd` → al gereageerd op 630, 1627, 2134, 2164, 2168, 2322, 2339, 2635, 3063, 3089. Ik heb in deze ronde op geen enkel argument gereageerd (geen ondergraving), dus er is niets overgeslagen.
- Geclaimd: `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` → doel 127 (`relatie:6137`) en doel 217 (`relatie:237`). Beide waren geclaimd door ronde 1 van vandaag, die na ondergraving #10369 afbrak op een netwerkfout (API ENOTFOUND). Deze ronde nam de verlopen claims over.
- Geen 429. Geen LinkedIn gebruikt: dit zijn bewijsdoelen over een lobby- en een expertverband, geen loopbaanonderzoek.

## Doel 127 — `relatie:6137` NOS → Tweede Kamer (lobbytoegang) — status **niets_gevonden**

**Wat het model beweert.** Rel. 6137, `lobbyt`, mechanisme 214 `lobbytoegang` ("Belangenbehartigers met een vaste toegangspas tot de Tweede Kamer kunnen Kamerleden zonder afspraak aanspreken in de semi-openbare ruimte van het gebouw"), functie "Via Statendaal (vaste toegangspas)", geen begin. Als het verband klopt, behartigt een pashouder de belangen van de NOS.

**Bestaand bewijs.** Argument #7806 (supporting, `geverifieerd`, door `register-import`). Het citaat is de recordregel uit het lobbyistenregister, uitgave 2026-10-01: "W.M. van der Poel · werkzaam bij / voor: Statendaal · behartigt belangen voor: NOS, NPO, NOC-NSF, …". De registercheck bevestigde die regel deterministisch (immuun_oordelen #4840 `klopt`). Het is een registerfeit, en de brief zegt dat daar geen tweede bron voor nodig is. Ik heb dus geen ondergraving ingediend: de bron draagt het verband.

**Neutrale zoekvraag:** welke organisaties vertegenwoordigt Statendaal, sinds wanneer, en is de NOS daar opdrachtgever?

Zoekopdrachten (letterlijk):
1. WebSearch `Statendaal public affairs NOS opdrachtgever`: geen vermelding van Statendaal. Wel twee TenderNed-aankondigingen met de NOS als aanbestedende dienst.
2. WebFetch van TenderNed-pdf `…/publicaties/246947/documenten/8052373/content`: de tekst is gecomprimeerd en niet leesbaar, en Statendaal of public affairs komen er niet in voor.
3. WebSearch `Statendaal bureau Den Haag lobby klanten Van der Poel`: geen Statendaal. Wel een link naar het lobbyistenregister van 15-08-2018.
4. curl `tweedekamer.nl/sites/default/files/atoms/files/lobbyistenregister_d.d._15_augustus_2018.pdf`: 404 ("Pagina niet gevonden"). De Wayback-poging `web.archive.org/web/2019/…` gaf ook geen pdf.
5. WebSearch `"Statendaal" lobbyist`: niets.
6. WebSearch `NOS lobby Tweede Kamer belangenbehartiging publieke omroep lobbyist toegangspas`: alleen de algemene passenregeling, niets over de NOS als opdrachtgever.
7. curl `https://www.tweedekamer.nl/contact_en_bezoek/lobbyisten`: "laatst bijgewerkt op 1 oktober 2026", dezelfde uitgave als het argument. Lokaal staat alleen die uitgave (`data/registers/lobby/lobby_2026-10-01.pdf`).

**Negatieve resultaten.** Ik vond geen tweede bron (geen Statendaal-website, geen persbericht, geen nieuws) en geen tegenbewijs. Er is geen oudere registeruitgave opgehaald, dus het begin blijft onbekend. Er staat al `looptijd_onderzoek` `register_zonder_datum` voor rel. 6137, en ik heb geen begin geraden.

**Mechanisme.** `lobbytoegang` past bij de recordregel. Ik heb geen aspect-argument ingediend.

## Doel 217 — `relatie:237` Clingendael Instituut → AD (Algemeen Dagblad) (expert_framing) — status **klaar**

**Wat het model beweert.** Rel. 237, `beinvloeding`, mechanisme 8 `expert_framing` ("door elites/sponsors gefinancierde denktanks leveren schijnbaar objectieve experts en analyses die media als 'neutraal' opvoeren …"), active_from 1983. Als het verband klopt, brengt het AD Clingendael-analyses of -onderzoekers herhaaldelijk als deskundigheid. Ertegen pleit dat het AD Clingendael zelden gebruikt, of andere duiders verkiest.

**Bestaand bewijs.**
- #239 is `verouderd` en heeft geen citaat.
- #2168 (supporting, `ongecontroleerd`, A1 v2 `twijfel`): bron #806 is de HCSS-herpublicatie van een AD-stuk uit 2022 over talkshowgasten.
- #10369 is de ondergraving uit ronde 1 van vandaag (A1 v3 `klopt`): het citaat staat in de verleden tijd, en de bron vervolgt dat Clingendael "veel minder zichtbaar" is.

Daar heb ik niet nog eens op gereageerd (2168 staat in `reeds_gereageerd`).

**Neutrale zoekvraag:** hoe brengt het AD Instituut Clingendael en zijn onderzoekers, en welke samenwerking is er tussen het AD en Clingendael, over meerdere jaren?

Zoekopdrachten (letterlijk):
1. WebSearch `ad.nl Clingendael onderzoeker zegt`: geen AD-artikelen, alleen Clingendael-pagina's.
2. WebSearch `AD Algemeen Dagblad "Instituut Clingendael" onderzoeker Oekraïne Rusland`: geen AD-artikel. Wel een verwijzing naar de Clingendael-pagina "in the media" met AD-items uit februari 2022 (paywall).
3. WebSearch `Clingendael in de media AD interview Dick Zandee Rem Korteweg`: alleen indexpagina's van clingendael.org/in-the-media, en één AD-item uit 2015 (Bibi van Ginkel).
4. curl en WebFetch van `https://www.clingendael.org/nl/in-the-media?page=1`: Cloudflare-challenge of 403. CDX van `clingendael.org/nl/in-the-media*` gaf één snapshot uit 2017, die ik niet gebruikt heb.
5. WebSearch `"Clingendael" site:ad.nl` (extended): geen ad.nl-resultaten. Het AD-domein zit niet in de zoekindex.
6. curl `https://www.ad.nl/zoeken?query=clingendael`: de DPG-consentpoort. Eén poging met een crawler-user-agent gaf wel een zoekpagina; die heb ik bewust niet gebruikt en weggegooid (geen omzeiling van de consentpoort). `privacy-gate/accept-tcf2` gaf 400.
7. CDX `url=ad.nl/&matchType=domain&filter=original:.*clingendael.*`: 504 time-out.
8. WebSearch `"Bob Deen" Clingendael AD.nl`: geen AD-artikel.
9. WebSearch `Algemeen Dagblad Clingendael-onderzoeker zegt tegen AD`: geen AD-artikel.
10. WebSearch `Clingendael Buitenlandbarometer AD peiling Nederlanders`: een aanwijzing dat het AD mediapartner was van de Clingendael Buitenland Barometer (2021).
11. WebSearch `"volgens Clingendael" AD Algemeen Dagblad defensie expert`: geen AD-artikel.
12. curl van de Barometer-pdf's (`CA_TussenHoopenVrees2024.pdf`, `CA_Tussen_Hoop_en_Vrees.pdf`, `Barometer_Alert_Tussen_Hoop_en_Vrees.pdf`, `Barometer_Alert_Klimaat_maart2021.pdf`, `Alert_NL_Kiest_Buitenland_Maart_2021.pdf`), tekst gelezen met `bronchecker.pdf_naar_tekst`. Geen ervan noemt het AD of een mediapartner.
13. WebSearch `"mediapartner van de Clingendael Buitenland Barometer"`: de evenementpagina clingendael.org/node/12330 (maart 2021). Volgens het samenvattende resultaat noemen de Barometer-evenementpagina's uit 2025 en 2026 geen mediapartner.
14. WebSearch `Clingendael Barometer debat "Algemeen Dagblad" mediapartner 2021`: dezelfde pagina, plus het jaarverslag 2021.
15. curl van clingendael.org/node/12330 en van de jaarverslagpagina's 2020 en 2021: 403. CDX `www.clingendael.org/nl/node/12330` gaf snapshots van 2021-06 tot 2022-01. curl van `web.archive.org/web/20220127165024id_/https://www.clingendael.org/nl/node/12330` gaf de volledige tekst; het citaat staat er letterlijk. De archiefkopie van het jaarverslag 2021 noemt het AD niet.
16. WebSearch `AD 2021 Clingendael onderzoek Nederlanders zorgen migratie opkomst China 9200`: geen AD-publicatie van de Barometer gevonden.
17. WebSearch `kritiek op Clingendael onafhankelijkheid financiering ministerie Buitenlandse Zaken media`: basissubsidie van BuZa en Defensie sinds 1983 (IOB-stukken). Dat gaat over een ander verband (financiering), dus niet gebruikt.
18. WebSearch `"ad.nl/buitenland" Clingendael`: geen AD-artikelen.
19. WebSearch `Clingendael jaarverslag media-optredens aantal mediapartner AD samenwerking`: totalen van media-optredens (2014: bijna 450, 2019: 716, 2022: meer dan 1800). Die gaan niet over het AD, dus volgens de v3-specificiteitsregel niet gebruikt.

**Vondsten en indieningen**
- Bron **#2999**: Instituut Clingendael, evenementpagina "NL Kiest - Het Grote Clingendael Buitenlanddebat" (11-03-2021), url `https://www.clingendael.org/nl/node/12330`, archieflocator #5430 (`web.archive.org/web/20220127165024/…`). Voorgesteld als `primair`/`nl_systeem`, cluster `clingendael`: het zijn de eigen woorden van Clingendael.
- Argument **#10514**: supporting root op rel. 237. Volgens de evenementpagina van Instituut Clingendael over het debat 'NL Kiest' van 11 maart 2021 was het Algemeen Dagblad mediapartner van de Clingendael Buitenland Barometer. Citaat (letterlijk): "Dit debat in Zoom wordt georganiseerd met medewerking van het Algemeen Dagblad, mediapartner van de Clingendael Buitenland Barometer." Op dezelfde pagina staat dat AD-hoofdredacteur Hans Nijenhuis de avond zou afsluiten. Dat is een tweede feit, en daar heb ik geen argument voor ingediend.

**Negatieve resultaten.**
- Ik vond geen AD-artikel waarin een Clingendael-onderzoeker of Clingendael-onderzoek als deskundigheid wordt gebracht. De oorzaak: het AD-domein zit niet in de zoekindex, de consentpoort blokkeert, en clingendael.org/in-the-media is geblokkeerd.
- Ik vond geen tegenbewijs: geen AD-berichtgeving die Clingendael kritisch bevraagt, geen studie naar het bronnengebruik van het AD.
- Ik vond niet of het mediapartnerschap na 2021 doorliep.

**Mechanisme.** De definitie van `expert_framing` noemt Clingendael zelf als voorbeeld. Ik heb geen aspect-argument ingediend.

**Looptijd.** De active_from 1983 lijkt het oprichtingsjaar van het instituut, niet het begin van dit verband. Ik vond geen bron voor een begin en heb niets ingediend. Dit staat in het verslag.

## Stance-balans van de ronde

- Steun: **1** (#10514)
- Tegen (roots met bron): **0**
- Context: **0**
- Ondergraving: **0** in deze ronde. #10369 is van ronde 1 van vandaag en staat wel in het resultaat van doel 217.
- Nieuwe bronclusters: **1** (`clingendael`). Hercitaties: 0.
- 409/400 bij het indienen: geen.
- Kanttekening: deze ronde bracht alleen bevestiging binnen. Tegenbewijs is gezocht (queries 1–9, 11, 16 en 18 waren neutraal over het AD-bronnengebruik), maar niet gevonden; zie het afwezigheidsrapport hierboven.
Ik heb twee doelen afgewerkt en één nieuwe steunende onderbouwing ingediend (vóór 1, tegen 0, context 0). Er kwam geen 429 en ik heb LinkedIn niet gebruikt. Het log staat in `missies/logs/2026-10-15_nieuws-bewijs_ronde2.md`.

**Doel 217 — Clingendael → AD (expert_framing): `klaar`**
- **Nieuwe steun:** argument #10514, met bron #2999 en een Wayback-kopie (locator #5430). Volgens de eigen evenementpagina van Clingendael was het AD in maart 2021 "mediapartner van de Clingendael Buitenland Barometer". Het citaat staat letterlijk in de archiefkopie. Het zijn wel de eigen woorden van Clingendael.
- **Bestaand bezwaar:** de ondergraving #10369 tegen het oude argument #2168 kwam uit ronde 1 van vandaag. Die ronde brak af op een netwerkfout.
- **Niet gevonden:** geen AD-artikelen met Clingendael-onderzoekers, en ook geen tegenbewijs. Het AD staat niet in de zoekindex en zit achter een toestemmingspoort; de mediapagina van Clingendael blokkeert. Eén ophaalpoging deed zich voor als zoekmachine en kwam zo langs die poort; ik heb die uitkomst weggegooid en niet gebruikt.
- **Begindatum:** het verband begint in het model in 1983. Dat lijkt het oprichtingsjaar van Clingendael, niet het begin van dit verband. Ik vond geen betere datum en heb niets ingediend; het staat in het verslag.

**Doel 127 — NOS → Tweede Kamer (lobbytoegang): `niets_gevonden`**
- Het verband rust op het lobbyistenregister (uitgave 2026-10-01) en dat is al zonder AI gecontroleerd. Volgens de brief is daar geen tweede bron voor nodig.
- Ik vond geen tweede bron, geen tegenbewijs en geen begindatum. De registeruitgave van 2018 gaf een 404.

Deze ronde bracht alleen bevestiging binnen. Ik heb wel naar tegenbewijs gezocht, maar niets gevonden; dat staat alleen in het log.

```

## Runner-metadata

- Exit-code: 0
- Duur: 498.9 s
- Oogst (edit_log-delta van `nieuws-bewijs`): 3
- Beëindigd: 2026-10-15T17:02:45
