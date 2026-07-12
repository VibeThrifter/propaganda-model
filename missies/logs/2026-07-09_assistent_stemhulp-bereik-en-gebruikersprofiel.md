# Missielog — bereik (hoeveel) + gebruikersprofiel (door wie) van de stemhulpen

**Datum:** 2026-07-09 · **Account:** assistent (bijdrager) · **Opdracht eigenaar:** "we moeten ook weten hoeveel de wijzers worden gebruikt en door wie" → **"dien alles in als admin"**. Gemerged via `maxime`.

## Cijfers (verbatim gesourcet)
- **StemWijzer TK2023: 9,1 miljoen keer** volledig ingevuld (ProDemos, record; 2021: 7,8 mln; 2025: ruim 8 mln).
- **Kieskompas TK2023: ~3 miljoen** (NOS: "De eerste telde 9 miljoen hulpvragen, de tweede 3 miljoen" → samen 12 mln).
- Context: ~10,4 mln geldige stemmen bij TK2023 → stemhulpgebruik zit in de orde van het hele electoraat. **Voorbehoud:** "keer ingevuld" = gebruiksaantal, geen unieke personen.
- **Door wie:** Van de Pol e.a. (2014/2018), via UvA-DARE: "mannen vaker gebruik maken van stemhulpen dan vrouwen" + "bezoekers gemiddeld hoger opgeleid en meer politiek geïnteresseerd dan de gemiddelde burger" (~60% al politiek onderlegd, maar flinke minderheid niet). Gebruikers zijn dus géén doorsnede → disproportioneel de al-betrokken/hoogopgeleide kiezer.

## Gemodelleerd (voorgesteld → gemerged via admin) — bronnen #1567-1569
- **Nieuwe edge rel #1859: ProDemos/StemWijzer #288 → Nederlandse kiezers #1046** (mechanisme meningsspectrum_beperking #197). Supporting root #2716 (9,1 mln) + `property='influence'`-arg #2717 (bereik → magnitude boven de vloer).
- **Bestaande edge Kieskompas #872 → kiezers (rel #1858):** `property='influence'`-arg #2718 (3 mln).
- **"Door wie"** als contextuele duiding op Kieskompas #872 (#2719) én ProDemos #288 (#2720): gebruikersprofiel-scheefheid (Van de Pol).

## Waarom hier
Bereik = het bewijs dat de `influence`-as van een stemhulp→publiek-edge van de 0,05-vloer tilt (schuldig-tot-bewezen; INVLOED-PRIOR-poort). Het gebruiksaantal is dus letterlijk het juiste bewijstype op de juiste plek. Mechanisme #197 heeft nu twee geïnstantieerde, gesourcete, hoog-bereik edges (Kieskompas + StemWijzer → kiezer).

## Ontwerplijn (bevestigd in gesprek, juli 2026)
- **Kiezer = één generieke knoop** (Nederlandse kiezers #1046). GEEN klasse-knopen en GEEN klasse-incidentie-as — dat is valse precisie (klassen zijn fuzzy/overlappend; binnen een klasse zit brahmin-left én merchant-right → politiek en klasse kruisen).
- **Klasse-asymmetrie** leest af uit `koopkrachtselectie` #176 + de welstandsmeter; **politiek × klasse-kruising** uit kleurmeter + hypothesenregister 00c. De kruising hoort in de analyselaag, niet in de graaf.
- **"Wie wordt beïnvloed"** = doelrol (`publiek`/`politicus`), niet demografie; differentiatie via bron-overlays (welstandsmeter/kleurmeter/bereik).

## Totaal
3 bronnen, 1 relatie, 5 argumenten. Alles gemerged; golden-snapshot groen, geen fouten boven de baseline.
