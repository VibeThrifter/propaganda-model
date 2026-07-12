# Scout-ronde: sterkste routes r7 — slotronde (gaten dichten tot 100)

- **Datum:** 2026-07-04 · **Account:** assistent · **Git-hash:** de441f1
- **Scope:** restanten uit het al geverifieerde r1-r6-materiaal die de teller van 82 naar >100
  relaties brengen — geen nieuwe research, wél dezelfde bewijslat.
- **Tooling:** `scripts/scout_indienen.py` + `data/scout/sterkste-routes-r7.json`.

## Geoogst (8 entiteiten #629-636, 19 relaties #1206-1224, 19 argumenten; bronnen hergebruikt + 2 nieuw)

| Cluster | Relaties |
|---|---|
| Talkshow-experts (m87/kandidaat) | Kluytmans→OMT (1206), Kluytmans→Op1 (1207), Wijninga→Op1 (1210), Blom→Op1 (1220), De Wijk→WNL op Zondag (1221), De Kruif→WNL op Zondag (1222) |
| Draaideur (m18/92/93/94) | Ten Broeke→HCSS (1208, politiek directeur na VVD-Kamerlidmaatschap), Ten Broeke→VVD (1209), Verhagen→Bouwend Nederland (1211), Klink→VGZ (1212, m93 bedrijfsleven), Schouw→Ver. Innovatieve Geneesmiddelen (1213) — bron FtM-draaideuroverzicht 2015 (locators) |
| ANP→regionale abonnee-kranten (m7 pakketjournalistiek) | →Dagblad v/h Noorden (1214), →Leeuwarder Courant (1215), →De Limburger (1216), →de Gelderlander (1217) — bron Boumans e.a., 'A Gatekeeper among Gatekeepers' (Journalism Studies; 50-75% politiek nieuws) |
| Econoom-affiliaties (rest r1) | Phlippen→RUG (1218, bijz. hoogleraar 2023), Teulings→UvA (1219, deeltijd 2013-2017) |
| Flak (rest r4, m10) | Pretium→AD (1223), Pretium→de Volkskrant (1224) — elk 2 zaken uit het Netkwesties-overzicht |

Nieuwe entiteiten: Jan Kluytmans #629 (gezagsexpert), Han ten Broeke #630 (politicus), Maxime
Verhagen #631, Ab Klink #633, Gerard Schouw #635 (politici), Bouwend Nederland #632, Vereniging
Innovatieve Geneesmiddelen #636 (lobbygroepen), Coöperatie VGZ #634 (bedrijf).

## Modelleerkeuzes
- FtM-2015-gevallen (Verhagen/Klink/Schouw): bron-met-locator zonder quote (het artikel is gefetcht
  en de gevallen zijn er hard in gedocumenteerd, maar er waren geen verbatim zinnen per casus
  beschikbaar) — claims conservatief geformuleerd, geen datums gegokt.
- Klink→VGZ op mechanisme 93 (draaideur_politiek_bedrijfsleven), Verhagen/Schouw op 94
  (draaideur_politiek_lobby) — het doel bepaalt het mechanisme.
- ANP→regionale titels: alleen de vier grote zelfstandige regionale abonnee-kranten; de
  AD-regiotitels lopen al via ANP→AD.

## Missie-totaal na r7 (sterkste-routes r1-r7)
- **Relaties: 101** (r1: 32, r2: 14, r3: 17, r4: 6, r5: 5, r6: 8, r7: 19) — alle `voorgesteld`.
- **Entiteiten: 56** (#581-636) — alle `voorgesteld`.
- **Argumenten: ~145** waarvan 10 contradicting en 2 contextual op eigen werk (tegenbewijs zit vooral
  in r4/r5/r6: rechterlijke begrenzing flak, HCSS-onafhankelijkheidsclaim, afgeschaft persembargo,
  Van Os-kilte, draaideurwet 2026); plus theorielaag-onderbouwing op mechanismen 6, 9, 10, 14, 48,
  87, 91, 94, 124, 156, 161.
- **Dedup onderweg:** 1 bestaande relatie (Knops→NIDV) en 2 bestaande bronnen automatisch hergebruikt;
  0 mislukte POSTs, 0 duplicaat-409's.
