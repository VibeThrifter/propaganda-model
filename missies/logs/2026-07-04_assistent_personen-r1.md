# Scout-ronde: ontbrekende personen r1 — hoofdredacteuren van outlets zonder persoonsedge

- **Datum:** 2026-07-04
- **Account:** assistent (bijdrager)
- **Git-hash bij aanvang:** de441f1
- **Opdracht:** eigenaar — "we hebben super veel stichtingen en media-organisaties met edges naar
  journalisten/hoofdredacteuren en die nodes missen; ga ze af en vul relaties + nodes aan."
- **Scope r1:** huidige hoofdredacteur/directie van media-outlets die nul persoonsedges hadden.
- **Tooling:** `scripts/scout_personen.py` (nieuw; dunne POST-orkestratie, geen inhoud) +
  manifest `data/scout/ronde1.json`. Alles via REST-API, alles `voorgesteld`.

## Geoogst (9 personen, 8 outlets — alle relaties mechanisme-loze kandidaten, personeel/bestuurder)

| Persoon | Outlet | Rel | node | rel-id | arg-id | bron (verbatim gecheckt) |
|---|---|---|---|---|---|---|
| Jildou van der Bijl | Het Parool (6) | personeel | #441 | 973 | 1410 | Villamedia 2025-04-03 |
| Michiel Couzy | Het Parool (6) | personeel | #442 | 974 | 1411 | Villamedia 2025-04-03 |
| Lindsay Mossink | NU.nl (7) | personeel | #443 | 975 | 1412 | Villamedia 2023-09-08 |
| Xandra Schutte | De Groene Amsterdammer (264) | personeel | **#433 (bestond al)** | 976 | 1413 | nl.wikipedia (verbatim) |
| Marc Adriani | BNR Nieuwsradio (351) | personeel | #444 | 977 | 1414 | Villamedia |
| Sander Heijne | Vrij Nederland (265) | personeel | #445 | 978 | 1415 | vn.nl 2024 |
| Sarah Sylbing | VPRO (142) | personeel | #446 | 979 | 1416 | vpro.nl/info/organisatie |
| Seada Nourhussen | OneWorld (327) | personeel | #447 | 980 | 1417 | Villamedia 2017-12-28 |
| Jan Slagter | Omroep MAX (143) | bestuurder | #448 | 981 | 1418 | omroepmax.nl directie |

Samenvatting-teller: personen_nieuw 8, hergebruikt 1, relaties 9, bronnen 9, argumenten 9.
Alles `voorgesteld`; certainty leeg / influence 0,05-vloer (guilty-until-proven); mechanisme NULL
(kandidaat) behalve waar een reviewer later `academische_socialisatie`/gatekeeping kan toewijzen.

## Modelleerkeuze
- Hoofdredacteur bij z'n **eigen** outlet = `personeel` (volgt de bestaande conventie: Remarque→de
  Volkskrant, Van der Linden→RTL Nieuws, Lensink→Follow the Money). `bestuurder` alleen bij echte
  governance (Jan Slagter = statutair algemeen directeur Omroep MAX).
- Geen mechanisme opgelegd — zuivere aanstelling is geen filter; laat de reviewer beslissen.

## Overgeslagen / niet ingediend (blijft in dit log, niet als model-node)
- **Omroep MAX "hoofdredacteur"**: geen eenduidige nieuws-hoofdredacteur (MAX Magazine heeft Peter
  Contant; mediadirecteur Nicolette de Wolf). Alleen Jan Slagter (directie) ingediend.
- **Reuters/AP/AFP, Novum Nieuws**: internationale persbureaus — geen duidelijke NL-hoofdredactie
  gevonden die de nodegap zinvol vult; uitgesteld tot gerichte research.
- **Metro, banken.nl, Gezond Verstand, Vandaag Inside, Brandpunt, Argos, NOS-hoofdredactie,
  De Morgen, EO-redactie**: nog niet behandeld (volgende ronde / lagere prioriteit of fuzzy).

## Volgende
- r2: bestuurders/directie van stichtingen/denktanks/fondsen zonder edge (SDM, Adessium, DOEN,
  borgingsstichtingen, WBS, Teldersstichting, NMO, Ster).
- r3: aanvullen bij outlets die al wél een edge hebben maar hun hoofdredacteur missen.
