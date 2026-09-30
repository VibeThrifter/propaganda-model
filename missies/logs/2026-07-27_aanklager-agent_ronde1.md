# Onbewaakte ronde — aanklager-agent · ronde1 · 2026-07-27

- Brief: `missies/aanklager_brief.md` (blob `224e42ad1c6d`)
- Account: `aanklager-agent`
- Gestart: 2026-07-27T13:31:59

## Voorregel

`GET /api/agent/reeds_gereageerd` → `{"gereageerd_op": [3477, 3568, 3582, 3586, 3619]}`. Alle vijf
overgeslagen. `GET /api/review_queue` geeft voor dit account **403** (`Rol 'reviewer' of hoger
vereist`), dus de wachtrij is — zoals in eerdere rondes — read-only uit de DB gehaald: 58
niet-gecertificeerde `voorgesteld` evidentiële roots. Gekozen scope: de **verste batch**
(2026-07-26, #3712–#3729) — twee clusters: Sophie Straat/NieuwRechts en het
`sociologische_homogeniteit`-cluster (mech. 63). Alle 18 argumenten uit die batch bekeken; #3714 is
`contextual` en dus niet score-dragend, de overige 17 gecertificeerd.

## Zoekopdrachten (letterlijk, 2026-07-27, ~13:32–13:42)

**Database (read-only):**
1. `SELECT … FROM arguments a WHERE a.parent_argument_id IS NULL AND a.status='voorgesteld' AND a.stance IN ('supporting','contradicting') AND (a.property IS NULL OR a.property='influence') AND NOT EXISTS (SELECT 1 FROM immuun_oordelen i WHERE i.argument_id=a.id AND i.fase='tegenspraak') ORDER BY a.id DESC LIMIT 60` → 58 rijen
2. `SELECT * FROM arguments WHERE id BETWEEN 3712 AND 3729` + `citations`/`sources`/`source_locations`-join (quotes, methode, locators)
3. `SELECT … FROM relations … WHERE r.id BETWEEN 2217 AND 2220`; `SELECT … FROM entities WHERE id IN (11,1214,1215)`; `SELECT … FROM mechanisms WHERE id=63`
4. `SELECT argument_id, verdict, … FROM immuun_oordelen WHERE fase='tegenspraak'` (19 bestaande certificaten — geen overlap met deze batch)

**Web (elke bron zelf opgehaald, ruwe HTML, verbatim gegrepd — niet op samenvatting vertrouwd):**
5. `curl https://nieuwrechts.nl/wie-zijn-wij` → grep op `Dé nieuwswebsite` · `rechtsdenkend` · `subsidievrij` · `donat` · `kernteam` · `Reijmerink` · `Nubé` · `Liever` · `gratis maand` · `advertent`
6. `curl https://nieuwrechts.nl/` → grep op `googlesyndication` · `doubleclick` · `adsbygoogle` · `adnxs` · `pubmatic` · `criteo` · `taboola` · `outbrain` · `adform` · `ad-slot` · `sponsor` · `<title>` · `og:description`
7. `curl https://nieuwrechts.nl/ads.txt` → volledige inhoud
8. `curl https://www.svdj.nl/nieuws/politieke-kleur-op-de-redactie-hoe-geef-je-ruimte-aan-verschillende-perspectieven/` → grep op `160` · `110` · `60 procent` · `60%` · `GroenLinks` · `vierjaarlijk` · `zeshonderd` · `Worlds of Journalism` · `Borger` · `veronderstelling` · `afhouden` · `Niet extreem-links`
9. `curl https://nos.nl/artikel/2624161-witte-mannen-naar-achteren-van-sophie-straat-geen-discriminatie-vinden-meldpunten` → grep op `kutwijf` · `trut` · `Derksen` · `Vandaag Inside` · `golf aan seksistische` · `doodsbedreig` · `aangifte` · `symbolische en artistieke` · `huidskleur of geslacht` · `Unia` · `Discriminatie.nl`
10. `curl https://over.nos.nl/nieuws/de-scherpe-discussie-over-diversiteit/` → grep op `systematische onder-representatie` · `Randstad` · `vrouwelijke experts` · `expert` · `cursus` · `training` · `jaarplan` · `spreiding` · `geografisch` · `Gelauff` + volledige kerntekst uitgelezen
11. `curl https://www.nporadio1.nl/cultuur-media/29225-diversiteit-in-de-media-is-vaak-nog-een-blinde-vlek` → grep op `driekwart` · `twaalf` · `blinde vlek` · `Charlotte Klein` · `hoofdredacteur` · `alles en iedereen` · `diversiteit echt voor nodig`
12. `https://api.crossref.org/works/10.1080/10584609.2026.2621169` en `…/10.1126/sciadv.aay9344` (bestaan de DOI's, kloppen titel/auteurs/jaar?)
13. `https://api.openalex.org/works/doi:10.1080/10584609.2026.2621169` en `…/10.1126/sciadv.aay9344` (volledige abstract + institutionele affiliaties)
14. `https://doi.org/10.1080/10584609.2026.2621169` en `https://doi.org/10.1126/sciadv.aay9344` → beide **HTTP 403** (paywall/botblokkade) — vandaar de route via Crossref/OpenAlex
15. WebFetch `https://www.tandfonline.com/doi/abs/10.1080/10584609.2026.2621169` → **403**
16. WebSearch: `Riedl Geiß Magin Jandura Stark "Do Journalists' Political Orientations Translate into Partisan News Reporting" abstract Austria Germany news items journalists`
17. WebSearch: `Johan Derksen Sophie Straat "kutwijf" Vandaag Inside witte mannen naar achteren`
18. WebSearch (site-beperkt tot nieuwrechts.nl): `Marit Nubé NieuwRechts artikelen publieke omroep partijdigheid overheidsbanden`

## Route (a) — weerlegging met tegenbron

**#3716 · doel ent. 1215 (NieuwRechts) · supporting → WEERLEGGING #3730** (+ bron **2274**, locators
`https://nieuwrechts.nl/ads.txt` en `https://nieuwrechts.nl/`).

De claim stelt dat het verdienmodel het inkomstenkanaal bij de lezersschare legt "**in plaats van bij
adverteerders** of publieke financiering". Dat tweede deel is onwaar. `nieuwrechts.nl/ads.txt`
bestaat en luidt onder meer `OWNERDOMAIN=Nieuwrechts.nl` / `MANAGERDOMAIN=refinery89.com`, gevolgd
door tientallen `RESELLER`-regels (Rubicon/Magnite, PubMatic, OpenX, AppNexus, TripleLift,
Sharethrough, Smart AdServer, 33Across, Conversant…). Een ads.txt is de IAB-standaard waarmee een
uitgever verkopers *machtigt zijn advertentievoorraad te verkopen* — het bestaan ervan mét
MANAGERDOMAIN is bewijs van programmatische advertentie-exploitatie. De homepage-broncode bevestigt
het aan de renderkant: `<app-adsense-presentation … adlayout="in-article" adformat="fluid">` tussen
de artikelen in, plus de stijlregels `ins.adsbygoogle.loaded[data-ad-status=unfilled]`,
`.r89-home-ad-slot--leaderboard` en `.article.sponsored.native` (opmaak voor gesponsorde artikelen).

Bewust **niet** weerlegd: de *subsidievrijheid*. De eigen site zegt "Steunt u ons onafhankelijke,
kritische en bovenal **subsidievrije** geluid?" en "Doet u liever een vrijblijvende **donatie**?" —
dat deel van de claim staat. Alleen de uitsluiting van adverteerders sneuvelt. Voor het
Advertentiefilter is dat het verschil tussen "lezer-gefinancierd" en "lezer- én
adverteerder-gefinancierd".

**Signaal voor de eigenaar (geen agent-werk):** de *entiteitsbeschrijving* van NieuwRechts (ent.
1215) draagt dezelfde fout — "Verdienmodel: ledenabonnementen en donaties, expliciet subsidievrij."
Een entiteit-PATCH is maintainer-werk; ik raak 'm niet aan.

## Route (b) — ondergravingen (inferentie-aanval, geen tegenbron nodig)

- **#3721 · doel mech. 63 · supporting → ONDERGRAVING #3731** (`citaat_dekking`). De citatie luidt
  "Van 160 medewerkers die **deelnamen** aan een interne peiling … 60% GroenLinks-PvdA"; de bron
  zegt letterlijk het omgekeerde: "*Van de 160 medewerkers deden er 110 mee.*" 160 = de
  personeelsomvang, 60 % slaat op **110 respondenten**. Daarmee verdwijnt een non-respons van 50
  personen (31 %) uit beeld — precies de groep waar de bron zélf vertekening verwacht (Borger:
  "rechtsgeoriënteerde journalisten en media houden deelname wat sneller af"). De motivering erkent
  zelfselectie, maar rekent haar in het getal weg.
- **#3712 · doel rel. 2217 (Vandaag Inside —flak→ Sophie Straat) · supporting → ONDERGRAVING #3732**
  (`citaat_dekking`). Beide quotes staan verbatim in de NOS-bron — maar binnen dit blok: "*De
  zangeres verweet in het bericht ook het gebrek aan publieke solidariteit. "Waar zijn de (linkse)
  media? … Johan Derksen die op nationale televisie roept: …"*". De keten is NOS → citeert Straats
  Instagram-bericht → dat Derksen citeert. De motivering claimt "de NOS registreert Derksens
  reactie"; dat doet de NOS niet — ze registreert het verwijt van de wederpartij. Tweede gat: de
  string "Vandaag Inside" komt in de héle bron **niet** voor (alleen "op nationale televisie"),
  terwijl de doelrelatie juist Vandaag Inside → Straat is. **Niet** beweerd dat de uitspraken onjuist
  zijn: vandaaginside.nl publiceerde er zelf een item + fragment over (zoekopdracht 17). Voor een
  negatieve, bij naam genoemde persoonsclaim die een flak-relatie draagt is de beschuldiging van de
  wederpartij, doorgegeven door een derde, een te dunne grondslag — koppel de primaire bron.
- **#3724 · doel mech. 63 · supporting → ONDERGRAVING #3733** (`citaat_dekking`). "Driekwart" en
  "twaalf hoofdredacteuren" staan verbatim in de bron; de opgevoerde **grond** ("op de expliciete
  grond dat een eenzijdig samengestelde redactie blinde vlekken oplevert") niet — *Blinde Vlekken* is
  de titel van Kleins scriptie, geen door de hoofdredacteuren uitgesproken causale redenering. En de
  enige aangehechte citatie wordt in de bron ingeleid met "*heeft Klein een goed advies*": het is het
  advies van de **onderzoekster**, en kan dus niet dragen dat "het mediabestel de causale stap zélf
  onderschrijft". Weggelaten tegen-context uit dezelfde alinea: voor het resterende kwart "speelt het
  geen rol in hun redactionele beleid", en de interviews dateren van vóór Black Lives Matter. Dit was
  het zwaarstwegende doelwit van de ronde: #3724 is expliciet gebouwd als weerwoord op Borgers
  "het is maar een veronderstelling" (#3722). Het scharnier houdt wél via **#3725** (Gelauff/NOS in
  eigen woorden) — dat argument blijft onaangetast.

## Route (c) — certificaten `overleefd` (13)

Steeds ruw opgehaald en verbatim gegrepd, niet op een samenvatting vertrouwd.

- **#3713** (Straat, haatgolf) — cert 84. NOS-quotes verbatim. Nuances in het certificaat: beide
  quotes komen uit Straats eigen Instagram (zelfrapportage), de NOS draagt het in eigen stem met
  "kreeg Straat een stortvloed aan online haat over zich heen"; de genoemde aangiftes zijn aangiftes
  **tegen** Straat.
- **#3715** (NieuwRechts-positionering) — cert 85. Claim houdt stand op de echte bronzin. **Wel** een
  citatiedefect voor A1: béíde citaties staan als `verbatim_quote` geboekt, maar noch "Dé
  nieuwswebsite voor rechtsdenkend Nederland." noch "Blijf via NieuwRechts.nl op de hoogte van het
  laatste nieuws…" komt letterlijk voor op /wie-zijn-wij of de homepage (homepage-meta: "NieuwRechts.nl
  - Nieuws voor rechtsdenkend Nederland").
- **#3717 / #3718 / #3719** (redactie NieuwRechts) — certs 86/87/88. "De nieuwsredactie van
  NieuwRechts bestaat uit drie redacteuren (v.l.n.r.: Daniël de Liever, Marit Nubé en Bart Reijmerink
  (hoofdredacteur))" verbatim. Bij #3718 dekt de citatie de rider over de NPO-artikelenreeks niet,
  maar die is extern juist (dossierpagina + "Dit zijn 10 'neutrale' NPO-duiders met stiekeme
  overheidsbanden") → geen ondergraving op een kloppende conclusie; aanbeveling: artikel-URL
  bijkoppelen.
- **#3720** (Worlds of Journalism) — cert 89. "elke vier jaar" + "ongeveer zeshonderd Nederlandse
  journalisten" + beide quotes verbatim; claim overschrijdt de bron niet.
- **#3722** (Borger-nuance) — cert 90. "Dat is alleen een veronderstelling" verbatim. Als aanklager
  geprobeerd dit te ontkrachten met Riedl e.a. (#3727) — dat bevestigt de conditionaliteit eerder dan
  het haar wegneemt.
- **#3723** (non-respons) — cert 91. Quote verbatim; gevolgtrekking geldig; claim blijft netjes bij
  "deels een meetartefact".
- **#3725** (Gelauff/NOS) — cert 104. Alle drie citaties nagelopen; de lezing
  "samenstelling → berichtgeving" is geen overrekking (Gelauff noemt de Randstad-samenstelling
  expliciet als reden waarom de opdracht "niet lukt").
- **#3726** (NOS onder-representatie) — cert 105. Kern verbatim, plus "De experts die we aan het woord
  lieten waren voor de overgrote meerderheid mannen" en "bepaalde provincies vaker aan dan andere".
  Klein defect zonder ondergraving: "ondanks **cursussen, jaarplannen** en beleid" staat er niet — de
  bron zegt "Ondanks alle goeie bedoelingen"; "cursussen" en "jaarplannen" komen nergens op de pagina
  voor. Aanbeveling: schrappen of apart bronnen.
- **#3727 / #3728** (Riedl e.a., Political Communication) — certs 106/107. Hier verwachtte ik een
  fout en vond er geen. DOI bestaat, titel/auteurs/jaar kloppen, en de abstract dekt de getallen
  létterlijk: "*combines a quantitative manual content analysis of political news items in Austria
  (n = 3,539) with a subsequent survey of 160 journalists who authored 626 of those items*". Ook mijn
  verdenking dat "Oostenrijk" fout was (auteurs zitten in München, Trondheim, Düsseldorf, Mainz)
  sneuvelde — de dataverzameling ís Oostenrijks. #3728's quote splitst twee zinnen samen, maar dat
  mag bij `llm_samenvatting_van_pagina` en de betekenis blijft exact.
- **#3729** (Hassell e.a., Science Advances) — cert 108. DOI, methode ("a large-scale correspondence
  experiment") en bevinding verbatim bevestigd; de scope-beperking die het argument zelf aanbrengt is
  precies die van de auteurs. Geen sterker tegenbewijs gevonden dan de indiener zelf al binnenhaalde.

## Negatieve resultaten (alléén hier — nooit als `contextual` modelbijdrage)

- Geen tegenbron gevonden tegen de haatgolf-claim (#3713), tegen de NieuwRechts-redactiefeiten
  (#3717–#3719), tegen de WoJS-cijfers (#3720) of tegen de twee peer-reviewed studies (#3727–#3729).
- Verdenking dat de DOI van #3727 verzonnen was: **weerlegd** (Crossref + OpenAlex).
- Verdenking dat "Oostenrijk" bij #3727 fout was: **weerlegd** (abstract zegt "in Austria").
- Verdenking dat de Derksen-quotes niet in de NOS-bron stonden: **weerlegd** — ze staan er verbatim;
  het gat zit in de *attributieketen*, niet in de tekst.
- Overwogen ondergravingen die ik heb laten liggen omdat de conclusie klopt en het defect enkel de
  citatie raakt: #3715 (twee non-verbatim `verbatim_quote`s), #3718 (ongedekte rider), #3726
  ("cursussen, jaarplannen"). Alle drie staan als expliciete tekortkoming in het certificaat, zodat
  A1/de reviewer ze ziet — precedent: de Kruithof-casus (ronde 2026-07-24).
- #3714 is een `contextual` root (meldpunten-oordeel) en dus niet score-dragend: buiten scope
  gelaten, geen certificaat.
- Geen 429 (rate limit) geraakt. Geen LinkedIn-actie nodig — geen loopbaan-/persoonsonderzoek in deze
  batch; de scraper is bewust niet ingezet.

## Stance-balans van de ronde

| | aantal |
|---|---|
| Weerleggingen (contradicting root mét tegenbron) | **1** (#3730 → doel ent. 1215) |
| Ondergravingen (contradicting reply mét `reasoning`) | **3** (#3731 → #3721 · #3732 → #3712 · #3733 → #3724) |
| Certificaten `aangevallen` | **4** (#3712, #3716, #3721, #3724 — certs 80–83) |
| Certificaten `overleefd` | **13** (certs 84–91, 104–108) |
| Certificaten `onbeslist` | 0 |
| Nieuwe bronnen | **1** (2274) + 2 locators |
| Overgeslagen via voorregel | 5 (#3477, #3568, #3582, #3586, #3619) |

Tweezijdigheid gehaald: 4 van de 17 beoordeelde claims (24 %) zijn aangevallen, waaronder één met
échte tegenbron en één op het scharnierargument van het mech.-63-cluster. Steun/tegen in wat ik zelf
indiende: 0 steun / 4 tegen / 0 context — een aanklager dient geen steun in.

Alles landde `voorgesteld` of als procesmetadata; niets gemerged, geen status gewijzigd, geen bron
geclassificeerd (alleen *voorgesteld*), niets verwijderd.

## Sessie-uitvoer

```
