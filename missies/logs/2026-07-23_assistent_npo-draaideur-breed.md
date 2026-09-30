# Missielog — bredere politiek↔publieke-omroep-draaideur (batch 2)

**Datum:** 2026-07-23 · **Account:** `assistent` (bijdrager) · **Aanleiding:** eigenaar vroeg "zoek veel
meer dan deze verbanden en entiteiten uit" (vervolg op de NPO-toezicht-batch van 2026-07-22).

## Methode
Vier parallelle onderzoekstromen (subagents, primair-gesourcet, mét dedupe-lijst):
1. Spit/Vrij Nederland 2023-roster ("In de top van de NPO grossieren (oud-)politici in toezichthoudende
   baantjes", 17-8-2023) volledig uitgemijnd.
2. Huidige NPO RvT/RvB + Ster + CvdM + RPO + NLPO (2026).
3. Omroepbesturen (EO, WNL, AVROTROS, KRO-NCRV, MAX, BNNVARA, PowNed, Omroep ZWART, HUMAN, VPRO).
4. Veiligheid/inlichtingen/Defensie → media/communicatie/bestuur-doorstroom.
Plus een aparte parlement.com-verificatiestroom voor datering/partij.

## Kritische dedupe-correctie
De eerste dedupe-lijst miste de doelen NOS/KRO-NCRV/NTR/VPRO/HUMAN → een tweede, naam-brede dedupe wees uit
dat véél kandidaten al in het model stonden: van der Louw(185), van der Burg(181), Ferrier(148), van
Gijzel(150), Sterk(178), Plasterk(735), Vliegenthart(880), én de héle militaire-duider-cluster (de Kruif
607, van Uhm 781, Berlijn 780, Wijninga 608). Die zijn overgeslagen om dubbel werk te voorkomen.

## Ingediend (alles `voorgesteld`, wacht op reviewer-merge)
**Bronnen:** id 2240-2265 (parlement.com-bio's, omroep-/koepel-bestuurspagina's, partij-registers,
villamedia/binnenlands bestuur) + hergebruik 71 (Spit) en 2232 (EO-bestuur). URL-locator per bron.
**Entiteiten (16):** TROS(1198, historische omroep) + 15 personen (1199-1213): Nijpels, Staal, d'Ancona,
Dekker, Asante, Ganzevoort, van Delft, Peetoom, Sweet, Kruithof, Paffen-Zeenni, Holterhues, Deldjou Fard,
Schneiders, Meijer.
**Relaties (36):** rel 2181-2216.
- Draaideur toezicht (m96 omroep / m95 koepel-regulator): Nijpels→TROS, Staal→TROS, Asante→CvdM,
  Ganzevoort→RPO + →KRO-NCRV, van Delft→NLPO, Peetoom→EO, Sweet→EO, Kruithof→WNL, Paffen→WNL,
  Holterhues→KRO-NCRV, Deldjou→Omroep ZWART, Schneiders→VPRO, Meijer→VPRO, Vliegenthart(880)→HUMAN.
- Coöptatie (benoemer→omroeptop, m99): d'Ancona→NOS (van der Louw), Dekker→NPO (Bruins 2015),
  Plasterk(735)→NPO (Hagoort 2008).
- Veiligheids-doorstroom: Joustra(135)→NPO draaideur m18 (NCTb→NPO-RvT-voorzitter 2018-2026; parallel aan
  opvolger Aalbersberg — twee NPO-toezichtvoorzitters uit de terrorismebestrijding-lijn).
- Partijbinding (m163): 17 lidmaatschap-edges naar VVD/CDA/PvdA/SP/D66/GroenLinks/ChristenUnie.
**Argumenten (36):** arg 3674-3709, één sourced supporting-root per relatie. Spit-quotes verbatim uit de
bron; parlement.com/org-quotes gemarkeerd `methode=llm_samenvatting_van_pagina` (subagent-geëxtraheerd,
niet char-voor-char verbatim) — de verificatie-agent kan ze later naar verbatim tillen.

## Bewust NIET ingediend (discipline)
- **Militaire media-duiders** (de Kruif, van Uhm, Berlijn, Wijninga, Vliegenthart-als-expert): cluster staat
  al in het model (oorlog/NAVO-werk) → geen dubbele edges. Alleen Vliegenthart→HUMAN (governance) toegevoegd.
- **Sipke Spoelstra (EO)**: ChristenUnie-koppeling berust op naamsmatch, niet hard geverifieerd → niet
  ingediend (geen naamsmatch modelleren).
- **Henk Hagoort**: "gelukkige uitzondering" (omroepman, geen partijpoliticus); CDA-claim alleen secundair/
  Wikipedia → niet als draaideur-politicus gemodelleerd.
- **Andra Leurdijk (NLPO), Eric Kaarsemaker (NLPO)**: OCW-band alleen secundair resp. niet-partijgebonden
  griffier → overgeslagen.
- **Governance-cases zonder media-lijn** (Docters van Leeuwen→AFM, Wilma van Dijk→Dunea, Bertholee→AP):
  geen media-invloedslijn → overgeslagen.
- **van Riessen (crime-duider) / Wilting (regionaal-entertainment) / Bindt (MIVD→HCSS)**: lagere
  opinievorming-relevantie resp. mogelijk al via HCSS-expert-edges gedekt → open follow-up, niet in deze batch.
- **FTM-COI-publicatie** (oud-CDS'en als "onafhankelijk expert" met defensie-industrie-banden): waardevol
  als geattribueerde confound op de bestaande expert-edges, maar hoort bij het al-bestaande militaire cluster
  → aparte vervolgstap, niet hier.

## Openstaand / vervolg
- Eigenaar merget de batch (reviewer+, "via admin").
- Actualiteitssignalen uit het onderzoek: BNNVARA-RvT is in 2025 vrijwel volledig ververst; KRO-NCRV mogelijk
  Sterk vervangen — controleer of het model geen verouderde samenstellingen aanhoudt.
- Spit-vervolgstuk "Van boten tot salarisconstructies..." nog niet uitgemijnd (mogelijk extra namen).
