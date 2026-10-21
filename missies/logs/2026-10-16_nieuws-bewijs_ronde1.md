# nieuws-bewijs — 2026-10-16, ronde 1

- Brief: `missies/nieuws_bewijs_brief.md`, blob `651b82555482`
- Account: `nieuws-bewijs`
- Voorregel: `GET /api/agent/reeds_gereageerd` gaf 630, 1627, 2134, 2164, 2168, 2322, 2339, 2635, 3063 en 3089. Geen van die argumenten kwam deze ronde aan de beurt.
- Geclaimd: `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` gaf doel 220 en doel 113.
- Geen 429. LinkedIn niet gebruikt: beide doelen gaan over een verband tussen organisaties, niet over een loopbaan.

## Doel 220 — `relatie:1402` Albert Heijn → RTL Nieuws (koopkrachtselectie) — status **klaar**

**De claim.** Albert Heijn adverteert bij RTL Nieuws. Volgens het mechanisme `koopkrachtselectie` (#176) stuurt een adverteerder het medium naar koopkrachtig publiek. Als het verband klopt, moet ten minste blijken dat Albert Heijn bij of rond RTL Nieuws adverteert. Tegen het verband zou pleiten dat er geen advertentierelatie is, of dat ze niets met RTL Nieuws te maken heeft. Het verband heeft geen `active_from`.

**Bestaande argumenten.**
- #1941 (supporting, ongecontroleerd, A1 `twijfel`). Bron #2 is Manufacturing Consent, met als locator https://en.wikipedia.org/wiki/Manufacturing_Consent. Het citaat is "evaluating audience segments in proportion to usage levels of advertisers' products and services". Het is een algemene passage die Albert Heijn en RTL Nieuws niet noemt.
- #10308 (verworpen). Dat was de neutrale versie van #1941 en is overgeslagen.

**Toets van het bestaande bewijs.** De bron draagt het verband niet: het is algemene theorie met een Wikipedia-locator. Daarom heb ik **ondergraving #11023** ingediend op #1941.

**Neutrale zoekvraag:** adverteert of sponsort Albert Heijn bij RTL (Nieuws), en sinds wanneer?

**Zoekopdrachten (letterlijk).**
1. DB: `SELECT … FROM relations … WHERE r.id = 1402`, `GET /api/arguments?relation_id=1402` en `immuun_oordelen` voor relatie 1402
2. WebSearch: `Albert Heijn grootste adverteerder televisie RTL reclamebestedingen`
3. WebSearch: `"Albert Heijn" "RTL Nieuws" reclame sponsor adverteerder`
4. WebSearch: `Albert Heijn reclame RTL 4 sponsoring programma Ad Alliance`
5. WebSearch (tegenkant): `RTL Nieuws onderzoek Albert Heijn prijzen kritisch`

**Vondsten.** Ondergraving #11023, zonder bron. Er is geen nieuwe bron aangemaakt.

**Negatieve resultaten.**
- Ik vond geen bron die een advertentie- of sponsorrelatie tussen Albert Heijn en RTL Nieuws (of RTL Nederland) laat zien.
- Emerce ("Albert Heijn grootste adverteerder in 2022", gebaseerd op Adfact) gaat over alle media en splitst niet uit per zender. Het artikel zit achter een betaalmuur en is niet ingediend, omdat het RTL niet noemt.
- De NOS meldde in 2020 dat AH zijn reclame rond Veronica Inside stopte. Dat ging over Talpa en Veronica, niet over RTL, en hoort dus bij een ander verband. Niet ingediend.
- Tegenbewijs: ik vond geen RTL Nieuws-berichtgeving over Albert Heijn in de zoekresultaten, alleen berichten van de Consumentenbond en Omroep Brabant. Niet ingediend.
- Looptijd: ik vond geen begindatum.

**Mechanisme.** Zolang niet blijkt dat er een advertentierelatie is, valt niet te toetsen of `koopkrachtselectie` past. Er is geen aspect-argument ingediend.

## Doel 113 — `relatie:252` PVV → AD (Algemeen Dagblad) (publieke aanval) — status **klaar**

**De claim.** De PVV brengt het AD of een AD-journalist publiekelijk in diskrediet, of dreigt met maatregelen (mechanisme `publieke_aanval`, #11). Het relatietype is `censuur` en `active_from` staat op 2006. Als het verband klopt, is er een uitspraak of maatregel van de PVV die op het AD gericht is. Tegen het verband pleit dat er alleen algemene uitspraken over "journalisten" zijn.

**Bestaande argumenten.**
- #254 (verouderd).
- #2189 (supporting, `bronvermelding_nodig`, A1 `klopt-niet`). Bron #1186 is een Villamedia-bericht van 13-12-2023. Het citaat "Journalisten zijn - uitzonderingen daargelaten - gewoon tuig van de richel." staat er letterlijk in en is een tweet van Wilders van 5 juni 2021. Het AD wordt nergens genoemd; dat heb ik met WebFetch gecontroleerd.
- #7979 (verworpen). Dat was de neutrale versie en is overgeslagen.

**Toets van het bestaande bewijs.** De bron gaat over journalisten in het algemeen en niet over het AD, dus ze draagt het verband niet. Daarom heb ik **ondergraving #11024** ingediend op #2189.

**Neutrale zoekvraag:** heeft de PVV of Wilders zich publiekelijk uitgelaten over het AD of een AD-journalist, en wanneer?

**Zoekopdrachten (letterlijk).**
1. DB: `SELECT … FROM relations … WHERE r.id = 252`, `GET /api/arguments?relation_id=252` en `immuun_oordelen` voor relatie 252
2. WebSearch: `Wilders Algemeen Dagblad kritiek op AD artikel PVV`
3. WebSearch: `Wilders tweet AD journalist "Algemeen Dagblad" PVV boycot`
4. WebSearch (extended): `Wilders noemt AD "nepnieuws" OR "leugens" OR "smerig" artikel Algemeen Dagblad reactie`
5. WebSearch (villamedia.nl, nvj.nl, denieuwereporter.nl): `PVV Wilders AD verslaggever aanval Villamedia`
6. WebFetch: villamedia.nl "Haagse speldenprikjes richting pers worden steeds kwaadaardiger" (17-03-2025), met de vraag of het AD erin staat
7. WebFetch: villamedia.nl "Wilders en Baudet nemen journalisten op de korrel" (07-06-2021), met de vraag of het AD erin staat
8. WebSearch: `Wilders reageert AD-onderzoek PVV "het AD" Wilders tweet krant`
9. WebFetch: de bron van #2189, met de vraag of het AD erin staat en of het citaat letterlijk is

**Vondsten.** Ondergraving #11024, zonder bron. Er is geen nieuwe bron aangemaakt.

**Negatieve resultaten.**
- Ik vond geen uitspraak of maatregel van de PVV of Wilders die op het AD of een AD-journalist gericht is.
- Villamedia van 17-03-2025 noemt het AD één keer, in verband met Mona Keijzer en niet met de PVV.
- Villamedia van 07-06-2021 noemt het AD niet.
- In het Wildersproces (NOS, 2016) vroeg de verdediging om onderzoek naar hoe de pleitnota bij het AD terechtkwam. Dat is een verzoek van de advocaat over een lek en geen publieke aanval van de PVV op het AD. Niet ingediend.
- Uit 2009 (DutchNews) komt een AD-bericht over imam Khalid Yasin, waarop de PVV reageerde tegen de imam en niet tegen het AD. Niet ingediend.
- De Trouw/Bosma-zaak hoort bij een ander verband (PVV → Trouw). Niet ingediend.
- Looptijd: ik vond geen bron voor het begin in 2006.

**Mechanisme.** Zolang er geen op het AD gericht incident is, valt niet te toetsen of het mechanisme past. Er is geen aspect-argument ingediend.

## Stance-balans van de ronde

0 steun / 0 tegen (root) / 0 context / 2 ondergravingen (#11023, #11024). Er zijn geen nieuwe bronclusters en geen hercitaties. Bij beide doelen vond ik geen bewijs voor het verband, maar ook geen tegenbewijs.
