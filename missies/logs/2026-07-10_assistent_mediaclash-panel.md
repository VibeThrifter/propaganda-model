# Missielog: entiteiten & verbanden uit panel "De Grote Mediaclash" (DNW #2358)

- **Datum:** 2026-07-10
- **Account:** `assistent` (bijdrager; alles geland als `voorgesteld`)
- **Aanleiding:** eigenaar leverde het transcript van het panel *Nieuwe tijd, nieuwe media* (De Nieuwe Wereld
  Zomerfestival "De Verheffing", Fort de Batterijen Nieuwegein, 4 juli 2026; gepubliceerd als
  "De Grote Mediaclash" #2358, YouTube 7 juli 2026) met de opdracht: maak er zoveel mogelijk entiteiten van en
  zet subagents in op alles wat verder uitgezocht moet worden.
- **Methode:** 8 parallelle onderzoeks-subagents (websearch + verbatim-verificatie), daarna één indien-script via
  de REST-API. LinkedIn-reflex expliciet overwogen en overgeslagen: alle personen zijn publieke mediafiguren
  wier loopbanen/incidenten beter gedekt zijn door nieuws- en primaire bronnen dan door zelfgerapporteerde
  profielen.

## Panelbron

Bron **1717**: transcript "De Grote Mediaclash …" (De Nieuwe Wereld TV, 2026-07-07) + YouTube-locator.
Deelnemers: Talitha Muusse (gespreksleiding), Wierd Duk (Telegraaf), Bob Scholte (Left Laser),
Sander Compagner (De Andere Krant).

## Nieuwe entiteiten (alle `voorgesteld`)

| id | naam | rol-suggestie |
|---|---|---|
| 1055 | Bob Scholte | journalist |
| 1056 | Willem Wagenaar | gezagsexpert |
| 1057 | Anne Frank Stichting | kennisinstituut |
| 1058 | Medialogica | mediaorganisatie |
| 1059 | HUMAN (omroep) | ledenomroep |
| 1060 | Vincent Verweij | onderzoeksjournalist |
| 1061 | LIMC (Land Information Manoeuvre Centre) | gezagsinstituut (2020, tijdgebonden) |
| 1062 | Robert Jensen | publieke_stem |
| 1063 | De Balie | maatschappelijke_organisatie |

## Nieuwe relaties (alle `voorgesteld`; args met verbatim citaties eronder)

- **1888** Scholte →personeel→ Left Laser (draaideurconstructie #18) — oprichter/gezicht; redactiestatuut-bron.
- **1889** Wagenaar →personeel→ Anne Frank Stichting (#18).
- **1890** HUMAN →mediaplatform→ Medialogica (omroepsignatuur #124).
- **1891** Medialogica →flak→ Wierd Duk (publieke_aanval #11) — aflevering "De zaak Thomas D." (30-06-2026);
  contextual met Duks weerwoord.
- **1892** Duk →flak→ Wagenaar (#11) — Kedichem-aanval (X 2018 verbatim; DDS 2026). Twee-niveaus-regel toegepast:
  contextual-confound benoemt dat de veroordeling (6 mnd, 3 voorwaardelijk, 1987) gedocumenteerd is maar
  "aanstichter" niet onafhankelijk bevestigd, en dat AFS/ombudsvrouw achter Wagenaar staan.
- **1893** AFS →bron_van→ Medialogica (expert_legitimatie #87).
- **1894** Defensie →eigendom→ LIMC (mechanisme-loos, kandidaat — structuurkoppeling).
- **1895** LIMC →flak→ De Andere Krant (statelijke_tegenwerking #174) — NOS-verbatim: distributiepunten in kaart
  gebracht; commissie-Brouwer: onrechtmatig.
- **1896** LIMC →flak→ Robert Jensen (#174).
- **1897** Verweij →personeel→ Zembla (#18, sinds 1996).
- **1898** Verweij →personeel→ NVJ (beroepsnetwerk_lidmaatschap #179) — docent cursus Onderzoeksjournalistiek
  ná "Online hufters".
- **1899** Blckbx →oppositie→ Zembla (onafhankelijk_medium_tegenwicht #78) — blckbx-onthulling dwong
  zelfcorrectie af; contextual nuanceert "framen"-intentie + baanverlies-claim.
- **1900** Mediahuis →alliantie→ Nieuws van de Dag (cross_media_eigendom #22) — Talpa-persbericht verbatim.
- **1901** Duk →beinvloeding→ Nieuws van de Dag (#87) — vaste "opiniemaker"; panel-transcript als tweede citaat.
- **1902** Nieuws van de Dag →etikettering→ FvD (#13) — "extreemrechtse uitspraken"-kop, Zijlstra-uitspraak,
  Van Groningen-erkenning; contextual-confound: kritisch interview ≠ flak, uitspraak kwam van tafelgast.
- **1903** Albrecht →intimidatie→ Left Laser (#11) — Balie-incident 25-05-2023 (NOS/NH verbatim); contextual:
  excuses daags erna, "op de vuist" (panel) is zwaarder dan de bronnen dragen.
- **1904** Albrecht →bestuurder→ De Balie (#18).
- **1905** de Volkskrant →etikettering→ De Andere Krant (#13) — "complotkrant" verbatim in nieuwskolom (Epstein,
  23-02-2026) én column (Keulemans, 12-01-2024).

## Argumenten op bestaande elementen

- **2937** contextual op rel. 1721 (accreditatiepoort Left Laser): versoepeling maart 2026 na NVJ-steun en
  Kamervragen (Villamedia-tweeluik) — poort bleek onder druk beweegbaar.
- **2924/2925** op mechanisme statelijke_tegenwerking (#174): NCTV-nepaccounts (NOS/NRC 2021) + CTIVD-begrenzing
  (rapport 83, feb 2026: kritiek alléén was voor AIVD/MIVD nooit onderzoeksreden).
- **2942** contextual op rel. 555 (NRC →etikettering→ DAK): Compagners "NRC gaat nooit met ons in gesprek".
- **2943** contextual op entiteit DAK: "enige krant met groeiend ledenbestand" alleen houdbaar in enge lezing
  (Mediahuis 1 mln digitale abonnees 2025).
- **Citatie 3559** op bestaand Klok-argument 2804: primaire Mediaforum-transcriptie (ContainmentNu, 19-03-2020).
- **Kleurmeter:** Scholte economisch:links + establishment:anti-establishment (Paraat!-interview, één bron →
  één signaal per as); Left Laser economisch:links (redactiestatuut "communistisch wereldbeeld").

## Bewust NIET ingediend (negatieve resultaten horen hier, niet in het model)

- **Telegraaf →etikettering→ DAK ("complotbode"):** het woord komt op het open web nergens voor; alleen
  Compagners eigen typering in het panel. Eén Telegraaf-artikel ("complotkanalen…", mei 2023) zit achter een
  paywall met onverifieerbare snippet → geen edge.
- **NOS nam Jettens "verbindende wedstrijd"-frame over:** Jettens uitspraak (X @MinPres) en de gelijktijdige
  rellen (NOS zelf) zijn hard gesourcet, maar een NOS-artikel dat de uitspraak overneemt is niet gevonden →
  geen relatie; het transcript-verwijt blijft ongestaafd.
- **Pieter Klok-uitspraak:** al gedekt door args 2803–2805; alleen de primaire transcriptie als extra citatie
  toegevoegd. De vaak geciteerde frase "met één mond" is deels parafrase — niet als verbatim ingediend.
- **"Op de vuist" (Albrecht):** geen bron beschrijft een wederzijds gevecht; als confound gedocumenteerd.
- **Thomas Bruning, Lidewij de Vos, Rob Jetten, MIVD, Grapperhaus als entiteiten:** genoemd in het panel maar
  zonder eigen mechanisme-dragende rol in de gevonden verbanden (model-focus: geen perifere knopen).
- **AIVD/MIVD ronselen journalisten:** al gedekt door args 350/351/456/457 op mechanisme #133 — niet gedupliceerd.
- **Zembla-transcriptclaim "om iemand te framen":** intentie-interpretatie; Zembla noemde het zelf "een verkeerde
  journalistieke keuze"; baanverlies-claim berust op de betrokkene zelf — als contextual-confound vastgelegd.

## Open eindjes voor een volgende ronde

1. Het Volkskrant-artikel van 4 juli 2026 zelf ("vandaag stond in de Volkskrant de complotkrant") — nog niet
   geïndexeerd/bereikbaar; zodra vindbaar als extra citaat op rel. 1905.
2. FD-artikel Rob de Lange (17-12-2018) als sterkste mainstream-bron voor de Wagenaar-veroordeling — paywall;
   registreren + Wayback zodra bereikbaar.
3. Wiv-herzieningsconsultatie (verwacht augustus 2026, Bits of Freedom) — kandidaat voor het
   voorspellingsregister.
4. `scripts/archiveer_bronnen.py` draaien voor Wayback-snapshots van de 28 nieuwe bronnen.
