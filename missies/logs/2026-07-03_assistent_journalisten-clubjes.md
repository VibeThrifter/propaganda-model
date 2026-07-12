# Mission-log: journalisten-clubjes (assistent) — 2026-07-03

**Account:** `assistent` (bijdrager, rate-exempt). Alles landt `voorgesteld`.
**Opdracht eigenaar:** "journalisten en alle journalisten clubjes zoeken" — breedste scope
(incl. informele kringen), incl. LinkedIn. Plan: `/Users/macbook/.claude/plans/nested-marinating-matsumoto.md`.
**Bronnen:** publiek/redactioneel primair (club-eigen sites), verbatim geverifieerd via WebFetch
vóór indienen.

## Batch 1 — drie complete clubs + besturen (tweezijdig)

Elke bestuurslid = `persoon → club` `bestuurder`/`lidmaatschap`/`adviseur`, **mechanisme-loze
kandidaat** (mechanism_id leeg → landt voorgesteld, telt in niets). Elke relatie draagt een
`supporting`-root met verbatim citatie (poort 400 zonder — allemaal gehaald). Elke club draagt
een entiteit-argument over haar karakter.

### 1. Nieuwspoort (elite-mengkamer) — entity 390, `elite_netwerk`/elite_forum
Bron 613 (nieuwspoort.nl over-ons + organisatie, institutioneel/nl_systeem).
RvT-leden (bestuurder-kandidaten) — de compositie ís de menging pers×politiek×voorlichting×lobby:
- Remco Meijer (391, journalist) → rel 888 — RvT-voorzitter, politiek redacteur de Volkskrant
- Paul van Meenen (392, politicus) → rel 889 — RvT-lid, Eerste Kamer
- Avinash Bhikhie (393, journalist) → rel 890 — namens Parlementaire Persvereniging
- Friso Fennema (394, voorlichter) → rel 891 — namens Voorlichtingsraad
- Andre Bosman (395, lobbyist) → rel 892 — Corporate Communication & Government Relations
- NVJ (69) → rel 893 `lidmaatschap` — NVJ-kwaliteitszetel in de RvT (instelling leent stem uit → directe edge)
Args 1318 (karakter/Nieuwspoortcode) + 1319–1324.

### 2. Nederlands Genootschap van Hoofdredacteuren (gatekeepers) — entity 396, `elite_netwerk`/elite_forum
Bron 614 (genootschapvanhoofdredacteuren.nl organisatie + home). Bestuur (allen hoofdredacteur):
- Corine de Vries (397, voorzitter, Regionale dagbladen) → rel 894
- Kamran Ullah (398, secretaris, De Telegraaf) → rel 895
- Perry Feenstra (399, penningmeester, FD) → rel 896
- Ilse Openneer (400, RTL Nieuws) → rel 897
- Edwin de Kort (401, Omroep Zeeland) → rel 898
- Hilmar Mulder (402, Libelle) → rel 899
- Giselle van Cann (403, NOS Nieuws) → rel 900
Args 1325 (karakter) + 1326–1332.

### 3. VVOJ — Vereniging van Onderzoeksjournalisten (tegenmacht) — entity 404, `vakbond`/vakbond_media
Bron 615 (vvoj.org over-de-vereniging). Bestuur (allen onderzoeksjournalist):
- Débora Votquenne (405, voorzitter, VRT NWS) → rel 901
- Willemijn Sneep (406, vicevoorzitter, Vers Beton) → rel 902
- Marcia Nieuwenhuis (407, RTL Nieuws) → rel 903
- Mira Sys (408, Follow the Money) → rel 904
- Margo Smit (409, adviseur/ombudsman) → rel 905
- **Crossover:** Mira Sys (408) → Follow the Money (257) `personeel` → rel 906 — leidt de brug VVOJ↔FTM af.
Args 1333 (karakter) + 1334–1339.

## Balans & controle
- **Tweezijdig:** Nieuwspoort (elite-menging) + Genootschap (eigenaars-/redactietop) vs VVOJ +
  FTM-crossover (tegenmacht). Niet eenzijdig pro-elite.
- **Nieuwheid:** 3 nieuwe clubs (Nieuwspoort/Genootschap/VVOJ ontbraken), 17 nieuwe personen,
  19 relaties (allen kandidaat), 22 argumenten, 3 bronnen (613–615, auto-cluster).
- **Verbatim geverifieerd** (WebFetch): Nieuwspoort 6/6, Genootschap 7/7, VVOJ-bestuur bevestigd.
- `validate_model.py --strict`: **EXIT 0**, geen fouten boven baseline; scoring golden-snapshot groen.
- Alle nieuwe items `voorgesteld` — mens beslist (merge via `/overleg` → Voorstellen, of "via admin").

## Bewust NIET ingediend (naar log, geen onbronde knopen)
- Nieuwspoort RvT-expertisezetels (Marianne van Kimmenade=Financiën, Inge Brakman=Governance) en
  gemeentezetel Robert Wester: lagere modelrelevantie + onduidelijke structurele rol → overgeslagen.
- Nieuwspoort-directeur Jurgen Pijpers (sinds 2026): governance, maar geen scherpe filter-rol → overgeslagen.
- Koos Maarleveld als persoon: alleen als NVJ-zetelhouder gesourcet, dagfunctie onbekend → NVJ→Nieuwspoort
  als institutionele edge i.p.v. persoonsknoop.

## Batch 2 — uitgevers-lobby + leiding bestaande tegenmacht-knopen

Zelfde discipline (kandidaat-relaties, verbatim citaties, WebFetch-geverifieerd).

### 4. NDP Nieuwsmedia (uitgevers-/eigenaarslobby, Eigendom-kant) — entity 423, `lobbygroep`/belanghebbende
Bron 621 (ndpnieuwsmedia.nl over + bestuur). Bestuur + outlet-affiliatie (leidt NDP↔uitgever-brug af):
- Marjolein van der Linden (424, hoofdredacteur) → NDP rel 922 (vicevoorzitter) + RTL Nieuws (88) rel 923
- Philippe Remarque (425, hoofdredacteur) → NDP rel 924 + DPG Media (1) rel 925
- Jeroen van Dijk (426, directie) → NDP rel 926 + FD Mediagroep (350) rel 927
- Cornell Heutink (427, directie) → NDP rel 928 (Erdee — geen outlet-knoop, overgeslagen)
Args 1355 (karakter) + 1356–1362. (Voorzittersstoel NDP: op de live pagina géén voorzitter getoond;
oud-voorzitter Rien van Beemen (2020) bewust NIET als huidig ingevoerd.)

### 5. Follow the Money (bestaand, 257) — huidige leiding
Bron 622 (ftm.nl/medewerkers). Harry Lensink (428, hoofdredacteur) → rel 929; Jan-Willem Sanders
(429, directie, uitgever/zakelijk directeur) → rel 930. Args 1363–1364. (Adjunct-hoofdredacteuren
uit een Villamedia-artikel jan-2025 stonden NIET op de live medewerkerspagina → overgeslagen.)

### 6. Investico (bestaand, 258) — governance
Bron 623 (platform-investico.nl/over-ons). Pieter Elshout (430, directie, directeur-bestuurder) →
rel 931; Thomas Muntz (431, hoofdredacteur) → rel 932; RvT: Hans Laroes (432, oud-hoofdredacteur NOS)
→ rel 933; Xandra Schutte (433, hoofdredacteur De Groene) → rel 934. Args 1365–1368.
(Overige RvT — Jones-Bos/Ferrier/Steensma/Wermuth — non-journalistiek/onduidelijke rol → overgeslagen.)

**Batch 2 controle:** 11 nieuwe personen/org, 13 relaties (allen kandidaat), 14 argumenten, 3 bronnen
(621–623). WebFetch-geverifieerd: NDP-bestuur 4/4 + karakter, FTM-leiding, Investico-governance.
`validate_model.py --strict`: EXIT 0; scoring golden-snapshot groen.

## Batch 3 — terugkerende kringen die netwerk-/ideologie-uitwisseling faciliteren

Insluitcriteria eigenaar: (1) terugkerend/blijvend, (2) faciliteert aantoonbaar netwerk- of
ideologie-uitwisseling. Géén eenmalige borrels; géén puur-administratieve organen.

### 7. Parlementaire Persvereniging (PPV) — entity 434, `elite_netwerk`/elite_forum
Bron 630 (NOS), 631 (Villamedia). Avinash Bhikhie (393, bestaand) → PPV rel 952 (voorzitter);
PPV → Nieuwspoort (390) rel 953 (kwaliteitszetel RvT). Args 1386 (karakter) + 1387–1388.

### 8. De Tegel — Stichting Jaarprijzen voor de Journalistiek — entity 435, `stichting`/belanghebbende
Bron 632 (detegel.info). **Establishment-convergentie:** oprichters NDP(423)/NVJ(69)/Genootschap(396)/
NOS(11)/RTL Nederland(8) → De Tegel `alliantie` rel 954–958. Bestuur: Martha Riemsma (436, voorzitter)
rel 959; **interlock** Edwin de Kort (401) rel 960 + Ilse Openneer (400) rel 961 — beiden óók Genootschap-
bestuur → brug Genootschap↔De Tegel. Args 1389 (karakter) + 1390–1397.

### 9. Buitenlandse Persvereniging (BPV/FPA) — entity 437, `elite_netwerk`/elite_forum (perifeer)
Bron 633 (bpv-fpa.nl). Imane Rachidi (438, president) rel 962; Annette Birschel (439, vice/penningm.)
rel 963. Args 1398 + 1399–1400. (Perifeer: buitenlandse correspondenten, minder NL-publiek-gericht — minimaal gehouden.)

### Grijs-inbedding (n.a.v. tegenmacht-discussie)
Eigenaar: "houd de rol `onderzoeksjournalist`, maar maak 't grijs — geen zwart-wit tegenmacht-frame."
Concreet: VVOJ-bestuurslid Marcia Nieuwenhuis (407) → RTL Nieuws (88) `personeel` rel 964 — toont dat
de VVOJ-top is ingebed in de reguliere/commerciële media, niet extern. Rollen VVOJ ongewijzigd (per keuze).
Voortaan: "tegenmacht" niet als moreel label; inbedding (financiering/socialisatie/bronafhankelijkheid)
altijd meemodelleren waar bronbaar.

### Bewust NIET opgenomen (Batch 3)
- **Nederlandse Sport Pers (NSP):** faalt criterium (2) — overwegend administratief (accreditatie/kaarten),
  geen bron voor norm-/netwerkuitwisseling.
- **De Loep:** = activiteit van de VVOJ, geen aparte entiteit.
- **Commentator-/talkshow-pool:** gemeten fenomeen, geen georganiseerde club → niet gereïficeerd
  (mogelijk later als bewijs bij `sociologische_homogeniteit`/duiding; Wierd Duk (bestaand) komt erin voor).
- Zwolse/regionale persclub, journalistiek-alumni-netwerk: NIET GEVONDEN met citeerbare bron.

**Batch 3 controle:** 6 nieuwe entiteiten (4 clubs + 2 personen; 2 interlock-leden herbruikt), 13 relaties
(kandidaat), 16 argumenten, 4 bronnen (630–633). Verbatim geverifieerd (WebFetch): De Tegel-initiatief +
bestuur, BPV-bestuur. `validate_model.py --strict`: EXIT 0.

## Batch 4 — LinkedIn (gericht, gecureerd; betrouwbaarheid grijs)

Sessie leefde; ik draaide zelf trap 1 (scrape) én trap 2 (indienen via pm_api). 4 profielen
gescrapet (Broertjes, Remarque, Laroes, Smit — allen reeds bestaande knopen). **Niet bulk-gemapt:**
LinkedIn mist vaak de journalistieke loopbaan en voegt civiele ruis toe → alleen model-relevante,
gedateerde affiliaties ingediend, bron = het profiel (grijs).

- **Remarque (425)** → de Volkskrant (4) `personeel` 1996–2019 (correspondent/politiek redacteur/
  hoofdredacteur) — rel 965, arg 1402. (DPG-band bestond al: rel 925 uit Batch 2 → overgeslagen.)
- **Smit (409)** → VVOJ (404) `bestuurder` 2005–2015 (voorzitter→directeur) rel 966; → NOS (11)
  `personeel` 2015–2016 (ombudsman) rel 967. Args 1403–1404.
- **Broertjes (184)** → Gemeente Hilversum (440, nieuw) `personeel` 2011–2022 (burgemeester) rel 968,
  arg 1405 — de media→politiek-draaideur.
- **Laroes: OVERGESLAGEN.** De scrape-JSON was corrupt door de gegroepeerde-rollen-parser (org "EBU"
  fout toegewezen aan Free Press Unlimited/Raad voor de Journalistiek/Global Editors Network). Niet
  ingediend; zijn Investico-band staat al in het model (Batch 2). Bronbestanden in `data/linkedin/`.

Bronnen 634–636 (LinkedIn, grijs). `validate_model.py --strict`: EXIT 0.

## Let op — gelijktijdige, aparte `assistent`-missie (niet dit werk)

Tijdens deze sessie liep onder hetzelfde `assistent`-account een **aparte** achtergrond-scout
(tijdstippen 20:02–20:11 en 20:40–20:41; mijn batches zijn 20:10/20:16/20:42/20:49). Onderwerp =
**politieke/corporate/alt-media-draaideuren** (o.a. Novum→AP, Ad Verbrugge→De Nieuwe Wereld,
Akwasi Ansah→Omroep ZWART, Spierdijk→GeenStijl, CDA→Jack de Vries, VVD→Cora van Nieuwenhuizen;
entiteiten als Deloitte/KPN/Agis/Victor Pinchuk Foundation). **Niet mijn journalisten-clubjes-werk.**
Enige botsing: een **lege dubbele** "Genootschap van Hoofdredacteuren" (entity 410, `ngo`, 0 relaties)
naast mijn rijke 396 (`elite_netwerk`, 7 bestuursleden) → 410 kan als duplicaat weg/afgewezen.

## Eindtotaal (mijn 4 batches, alles `voorgesteld`)
- **Clubs/knopen:** 8 nieuw (Nieuwspoort, Genootschap, VVOJ, NDP, PPV, De Tegel, BPV, Gemeente
  Hilversum) + 2 bestaande verrijkt (Follow the Money, Investico).
- **Personen:** ~30 nieuw; **relaties:** ~49 (mechanisme-loze kandidaten); **argumenten:** ~56
  (verbatim citaties); **bronnen:** 13.
- Verbatim geverifieerd via onafhankelijke WebFetch; `--strict` EXIT 0, scoring-snapshot groen.

## Merge via admin (maxime-maintainer, op verzoek eigenaar)
- **38 entiteiten** (mijn clubs + personen) → `goedgekeurd`; **57 argumenten** → `ongecontroleerd`.
- **52 relaties blijven kandidaat** (`voorgesteld`): allemaal mechanisme-loos → orphan-poort weigert
  goedkeuring (bevestigd op rel 888). Ze incuberen tot een mechanisme via RfC (theorie-werk, mensen).
- **Regressie gevangen & hersteld:** goedkeuren maakte 2 rolloze entiteiten tot een KOPPEL-ENT-ROL-fout.
  Rollen toegewezen via admin: Martha Riemsma (436) → `directie` (algemeen directeur ANP, ex-hoofdred.
  Tubantia); Gemeente Hilversum (440) → `gezagsinstituut`. Daarna `--strict` echt EXIT 0 (KOPPEL-ENT-ROL 0),
  scoring-snapshot groen.
- Genootschap-duplicaat (410) eerder al opgeruimd; het co-oprichter-feit (Persvrijheidsfonds) staat op 396.

## Vervolg op verzoek: Riemsma→ANP + RfC-mechanisme
- **Riemsma (436) → ANP (12)** `personeel` (rel 972, kandidaat) — algemeen directeur ANP; bron 638 (RPO).
- **RfC voorstel 22** (`open`): nieuw mechanisme **`beroepsnetwerk_lidmaatschap`** (filter ideologie, aard
  direct) dat de persoonlijke journalisten-club-lidmaatschappen een theoretisch huis geeft — de dyadische
  instantie ónder het emergente veld `ideologische_homofilie`. Beoogde instantiaties (adoptie van kandidaten):
  rel 894 (de Vries→Genootschap), 901 (Votquenne→VVOJ), 952 (Bhikhie→PPV), 959 (Riemsma→De Tegel),
  888 (Meijer→Nieuwspoort). Vergt **2 menselijke reviewer-akkoorden** (indiener + agent-reviews tellen niet).
  Bij acceptatie krijgen die kandidaten hun mechanisme → dán goedkeurbaar. Reviewen: `/overleg` → Voorstellen.

## Theorie→praktijk volledig geïntegreerd via admin ("voeg alles toe via admin")
Theorielaag-audit (kandidaten gegroepeerd op rol-paar) wees één echt gat aan; de rest valt onder
bestaande theorie of incubeert. Uitgevoerd met maxime:
- **Nieuwe rol 59 `journalistiek_beroepsnetwerk`** (categorie ideologie) — RfC voorstel 24, geaccepteerd
  (maintainer-quorum). Verving `elite_forum`/`vakbond_media`/`belanghebbende` als club-rol (over-eliten weg).
- **Nieuw mechanisme 179 `beroepsnetwerk_lidmaatschap`** (filter ideologie, aard direct, `source 59 → target
  journalist 26`) — voorstel 22 ingetrokken (rolloos) en opnieuw als voorstel 25 mét eindpunt-rollen, geaccepteerd.
- **6 club-entiteiten** (Nieuwspoort 390, Genootschap 396, VVOJ 404, PPV 434, De Tegel 435, BPV 437) → rol 59.
- **26 club-lidmaatschappen** goedgekeurd onder mech 179; **19 loopbaan-/dienstverband-relaties** onder het
  bestaande mech 18 `draaideurconstructie` (Remarque→Volkskrant, Smit→NOS, Broertjes→Hilversum, FTM/Investico-
  leiding, NDP-bestuurders→uitgevers, Riemsma→ANP, …).
- **6 org→prijs/fonds-edges (alliantie)** bewust **kandidaat gelaten** (incuberen): De Tegel-oprichters
  954–958 + Genootschap→Persvrijheidsfonds 969 — geen passend mechanisme, te dun om te abstraheren.
- Controle: `validate_model.py --strict` **EXIT 0** (echte exitcode), golden scoring-snapshot **groen** (23 tests).
  De 4 `KOPPEL-REL-MECH`-vlaggen zijn niet van mij (OMT/Oomen/de Mol/ECB, binnen baseline).
- Aparte concurrent `assistent`-scout (politieke draaideuren, o.a. D66→van Meenen 970/971) onaangeroerd gelaten.
