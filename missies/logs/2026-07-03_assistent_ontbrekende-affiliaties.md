# Missielog — ontbrekende affiliaties/entiteiten uit entiteitsbeschrijvingen

**Datum:** 2026-07-03 · **Account:** `assistent` (bijdrager) · **Aanleiding:** Paul Rosenmöller (190) had
alleen edges naar GroenLinks en IKON, terwijl zijn beschrijving óók Tweede Kamer, VO-raad en Eerste
Kamer noemt (twee tegenknopen bestonden niet). Survey vond dit patroon breed. Alles ingediend via de
REST-API, **alles `voorgesteld`** (ik stel voor, een mens beslist). Elke edge draagt een geverifieerde bron.

## Aangemaakt (mijn bijdrage)

**Entiteiten (23):** 380 Eerste Kamer, 381 VO-raad, 382 Deloitte, 383 Erasmus MC, 384 TU Delft,
385 KPN, 386 Agis Zorgverzekeringen, 387 Zorgbelang Nederland, 388 Victor Pinchuk Foundation,
389 Azor, 410 Genootschap van Hoofdredacteuren *(zie dubbel-vlag)*, 411–422 oprichters
(Ad Verbrugge, Paul van Liempt, David van Overbeek, Madeleine Klinkhamer, Rens van der Bulck,
Akwasi Ansah, Gianni Lieuw-A-Soe, Eric Smit, Mark Koster, Arne van der Wal, Romke Spierdijk, Arne Biesma).

**Relaties (42):** 861–887 (blok A/B/C) + 907–921 (blok D/E). 39 met mechanisme (draaideurconstructie 18
of partijbinding 163), 3 mechanisme-loze **kandidaten** (org→org: 907 Novum→AP, 908 NVJ→Persvrijheidsfonds,
909 Genootschap→Persvrijheidsfonds). Elke relatie heeft één `supporting` root-argument met echte citaat.

### A. Rosenmöller (190)
- 861 → Tweede Kamer (107) lidmaatschap 1989–2003 · 862 → Eerste Kamer (380) lidmaatschap vanaf 2019 ·
  863 → VO-raad (381) bestuurder 2013–2021. Bron: parlement.com-biografie (verbatim datums).

### B. Drop-in edges (tegenknoop bestond al)
- de Vries (110)→CDA(54), Heemskerk(115)→PvdA(56), Sneijder(119)→PvdA(56) [draaideur journalistiek→politiek],
  Hillen(109)→Defensie(85), Kroes(114)→Europese Commissie(155), Bussemaker(168)→OCW(132)+PvdA(56),
  Ollongren(202)→Defensie(85), Knops(117)→BZK(156), Joustra(135)→NCTV(172), Segers(225)→ChristenUnie(379),
  Compagner(250)→KnowledgeMatters(254), Beckman(251)→FD(195), Criel(237)→DPG Media Group(233)+DPG Media(1),
  Sevinga(238)→DPG Media(1). Bronnen: parlement.com / Wikipedia / Management Scope / The Globalist.

### C. Nieuwe tegenknoop-org + edge
- Leeflang(134)→Deloitte(382), Kuipers(167)→Erasmus MC(383)+TU Delft(384), Schaart(120)→KPN(385),
  van der Veen(121)→Agis(386)+Zorgbelang(387), Pinchuk(204)→Victor Pinchuk Foundation(388),
  Rijkeboer(255)→Azor(389).

### D. Org→org (kandidaten, geen mechanisme)
- Novum(337)→AP(170) alliantie · NVJ(69)→Persvrijheidsfonds(267) alliantie · Genootschap(410)→267 alliantie.

### E. Oprichters (bestuurder, mech 18)
- De Nieuwe Wereld(249): Verbrugge/van Liempt/van Overbeek · de andere krant(248): Klinkhamer/van der Bulck ·
  Omroep ZWART(206): Akwasi Ansah/Lieuw-A-Soe · Follow the Money(257): Smit/Koster/van der Wal ·
  GeenStijl(342): Spierdijk/Biesma.

## Correcties t.o.v. de oorspronkelijke survey (bron-verificatie)
- **Leeflang**: geverifieerde rol = *managing partner Deloitte Legal* (jan 2020), **niet** "bestuursvoorzitter Deloitte Nederland" (onjuist gebleken).
- **Sevinga → DPG Media Group NV**: **niet** te staven — enkel commissaris DPG Media Nederland (→ entiteit 1). Group-NV-zetel overgeslagen.
- **Kuipers → TU Delft**: benoeming per **1 sept 2025** (recent, geen historische band).
- **De Nieuwe Wereld**: opgericht 2018 (niet 2019/2020). **de andere krant**: derde initiatiefnemer is Compagner (bestond al, 250). **FTM**: "eind 2009".

## Overgeslagen / niet ingediend (geen fabricage)
- **Zonderop (275) → FD Mediagroep (350)**: haar beschrijving zegt "commissaris FD Mediagroep", maar de bestaande
  edge 587 wijst naar 195 (de krant). Geen verse webbron met verbatim datering gevonden → **geen edge aangemaakt**.
  *Aanbeveling eigenaar:* heroverweeg edge 587 (patchen van een goedgekeurde relatie = maintainer-werk).
- **NTU Singapore** (Kuipers): buitenlands, laag signaal → overgeslagen.

## ⚠ Samenloop met een tweede `assistent`-sessie
Tijdens deze ronde draaide een **tweede `assistent`-proces** mee dat rond 20:10 entiteiten 390–409
aanmaakte (Nieuwspoort, VVOJ, "Nederlands Genootschap van Hoofdredacteuren" (396) + leden, diverse
journalisten) + relaties 888–906. **Dat is niet mijn werk** en staat hierboven niet in mijn telling.
- **Dubbel-vlag:** mijn *Genootschap van Hoofdredacteuren* (410, ngo) overlapt met hun rijkere
  *Nederlands Genootschap van Hoofdredacteuren* (396, elite_netwerk, mét bestuursleden). Beide `voorgesteld`.
  *Aanbeveling reviewer:* dedupliceer — waarschijnlijk 410 (+ relatie 909) laten vervallen ten gunste van 396.

## Naronde — partij-edges voor politici (richtingscorrectie)
Op instructie "de politici moeten een edge naar hun partij hebben". Ontdekking: de **conventie is
`partij → persoon`** (21 goedgekeurde edges; mech 92 `partijlijn` en 163 `partijbinding` zijn beide
gedefinieerd `partij → politicus/directie`). Mijn eerdere 4 partij-edges (blok B) én de 4 van de
tweede `assistent`-sessie (857–860) stonden **omgekeerd** (`persoon → partij`).

**Toegevoegd (17 nieuwe `partij → persoon` lidmaatschap-edges, mech 163, `voorgesteld`, rel 935–951):**
de Vries, Heemskerk, Bussemaker, Segers, Sneijder, Hillen, Ollongren, Kroes, Knops, Schaart,
van der Veen, Eijsink, de Liefde, Erlings, Eurlings, van Nieuwenhuizen, Bos — elk met parlement.com-
(of Adformatie-)bron. Na deze ronde heeft **geen enkele politicus-entiteit** nog een ontbrekende partij-edge.

**Op te schonen (omgekeerde, nu redundante `persoon → partij` edges, alle `voorgesteld`):**
mijn 865/869/870/871 + de tweede sessie 857/858/859/860. *Vergen maintainer-verwijdering ("via admin").*
Mijn Sneijder-`draaideur` 872 (journalistiek→politiek) laat ik staan als aparte overstap-claim.
Losse aandacht: Paul van Meenen (392, D66, entiteit van de tweede sessie, `voorgesteld`) mist nog een partij-edge.

## Verificatie
- `python3 scripts/validate_model.py --strict` → **geen fouten boven de baseline**; golden-snapshot scoring.py groen.
- Alle 23 entiteiten en 42 relaties `voorgesteld`; 3 org→org-kandidaten mechanisme-loos (incuberen via `/api/kandidaten`).
- Niets gemerged/goedgekeurd — dat blijft mensenwerk.
