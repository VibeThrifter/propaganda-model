# Missielog: literatuur-mining (Bergman-referenties + aanraders), fase 1

**Datum:** 2026-07-10 · **Account:** `assistent` (bijdrager) · **Opdracht eigenaar:** "Ga al
deze literatuur minen naar praktijkmodel, misschien theoriemodel en /onderzoek elementen."

## Ontwerpregel (uit scoring.py, bepalend)

Het cluster van een argument = het cluster van zijn zwaarste échte citatie; daarom citeert
**elk argument in deze missie uitsluitend één werk** (geen gemengde citaties met Bergman
#1448). Zo vormt elk werk een eigen bewijslijn die via noisy-OR stapelt op de bestaande
Bergman-argumenten. Alle citaten zijn verbatim gecontroleerd tegen de gedownloade teksten
(scratchpad `lit/*.txt`); OCR-koppeltekens/spaties genormaliseerd naar de gedrukte vorm.

## Fase 1 — acht vrij toegankelijke werken gemined (alles `voorgesteld`)

**Bronnen geregistreerd (1600–1606, elk met url-locator + classificatievoorstel):**
1600 *Gevaarlijk spel* (Prenger e.a., AMB 2011, ISBN 9789079700301; SVDJ-PDF) ·
1601 *Het persbureau in perspectief* (Vermaas & Janssen, SVDJ 2009) ·
1602 *Zijn de persbureaus te verslaan?* (Rutten & Slot, TNO 2011) ·
1603 *Journalistiek in diskrediet* (Ummelen red., AMB 2009, ISBN 9789079700141; bevat het
Hijmans/Buijs/Schafraad-hoofdstuk pp. 41-66) · 1604 *The Propaganda Model Today*
(Pedro-Carañana/Broudy/Klaehn red., UWP 2018, DOI 10.16997/book27, open access) ·
1605 *Mediamonitor 2025* (CvdM) · 1606 *Digital News Report 2025, NL-hoofdstuk* (Reuters
Institute).

**Nieuwe entiteiten:** Aldi (1049), Bette Dam (1050).
**Nieuwe relaties (elk met gesourcet arg):** 1865 Aldi→Wegener (`advertentiedruk`;
advertentieboycot na vouwfiets-test), 1866 Ministerie van Defensie→Bette Dam
(`publieke_aanval`; Beeksma/Middel-intimidatie, Uruzgan), 1867 RVD→de Volkskrant
(`publieke_aanval`; De Horsten-'vendetta', nov. 2010).

**Argumenten (27):**
- *Gevaarlijk spel* (2757–2765): rel 1865/1866/1867; advertentiedruk #3 (FD-getuigenis +
  zelfcensuurmechaniek); publieke_aanval #11 (38%-enquête + spindoctor-methode — **was 0
  steunclusters**); zelfcensuur #14 (80% hoofdredacteuren-klachten, >helft geeft toe);
  citaatautorisatie #150 (65% wijzigingen doorgevoerd, ⅓ citaten); pr_subsidie #9 (VNR's
  zonder bronvermelding + 'halve krant'); veld voorlichtingsovermacht #11 (135-156k vs
  10-15k; 940 persberichten/dag; relatiemedia 10:1; 'spreekbuis'-conclusie; Boom: 'zij
  hebben gewonnen').
- *Vermaas & Janssen* (2766–2769): rel 219 ANP→Metro (60-90%); persbureau_brongebondenheid
  #97 (NL-bureaus 80-90% op internationale bureaus); intermedia_agendering #157 ('pas
  nieuws als het ANP erover bericht'); entiteit ANP (3000 klanten/20 kranten; Shell- en
  Fortis-selecties).
- *Rutten & Slot* (2770–2773): commerciele_afhankelijkheid #4 (NL uniek: geen enkele
  overheids-/mediabetrokkenheid bij het persbureau; wereldwijd 75% staatssteun);
  pakketjournalistiek #7 (24%→28% dagbladartikelen op ANP); pr_subsidie #9 ("een APS'je is
  een begrip"); entiteit ANP (40% meer output, 'kritische grens').
- *Ummelen/Hijmans* (2774–2776): rel 1217 ANP→De Gelderlander (68% geheel/84% derden;
  'geen bron maar eindproduct'); pakketjournalistiek #7 (Cardiff-replicatie: 32%/52%
  voorverpakt, geen ANP-bronvermelding in 3 van 4 kranten); commerciele_afhankelijkheid #4
  (Van Ginneken: advertentiegeld bepaalt bestaansrecht redactionele formule).
- *Propaganda Model Today* (2777–2778): veld fabricage_van_instemming #1 (filters 'stronger
  influence than in the past' + Herman: model 'holds quite well in Britain, Germany and
  other countries'); platform_advertentie_concentratie #40 (Fuchs: Google/Facebook als
  grootste advertentiebureaus; eigendom = algoritme-controle).
- *Mediamonitor 2025* (2779–2782): eigendomsconcentratie #1 (dagbladen C2=94%; online
  C3=91%; DPG enige top-3-speler op álle markten; 4→3 commerciële aanbieders); rel 9
  DPG→RTL (ACM-goedkeuring 27-6-2025, 1,1 mrd, stichting-remedies);
  platform_advertentie_concentratie #40 (80% digitale reclame naar Meta/Alphabet, was 54%
  in 2015); algoritmische_filtering #21 (AI-overzichten als poortwachter + uitgeversklacht).
- *DNR 2025* (2783): koopkrachtselectie #176 (17% betaalt voor online nieuws; DPG+Mediahuis
  >90% van de kranten).

**/onderzoek:** geen nieuwe voorspellingen nodig uit fase 1 — wél meetbases: Rutten & Slot +
Vermaas & Janssen operationaliseren voorspelling #4 (ANP-steekproef), DNR 2025 (17% betaalt)
is het nulpunt voor voorspelling #7, en Mediamonitor 2025 levert de concentratie-baseline
voor voorspelling #1. **Theorielaag:** geen RfC nodig; PMT-2018-materiaal landde als
literatuur-args (veld #1, mech #40).

## Clusterhygiëne-meldingen (reviewer-werk)

- Bronnen 1600–1606: classificatievoorstellen (reliability + onderwerp) wachten op
  bevestiging via `PATCH /api/sources/<id>/classificatie`.
- 1603 (Ummelen-boek) kreeg cluster `bert_ummelen_red`, maar de Hijmans-hoofdstuk-argumenten
  (2774–2776) delen auteurs met bron 1490 (`ellen_hijmans`, TvC-artikel 2011). Op géén doel
  staan beide naast elkaar (bewust), maar structureel zouden 1603-hoofdstukcitaties en 1490
  in één cluster horen — reviewer-besluit.
- Eerder gemeld: cluster-splitsing `bergman` (3/299/300) vs `tabe_bergman` (833/1448).

## Fase 2 — aanschaf-/leenlijst voor de eigenaar (besluit 9 juli: eigenaar regelt toegang)

| Werk | Route | Doel in het model |
|---|---|---|
| Prenger (red.) 2007, *Een selectieve blik* (Het Spinhuis) | fysiek/antiquariaat; geen OA | zelfcensuur #14: onafhankelijke bron voor het hoofdredacteuren-telefoontjes-bewijs |
| Vasterman & Aerden 1995, *De context van het nieuws* (Wolters-Noordhoff, ISBN 9789001909734) | fysiek/bibliotheek | rel 1770 Cannon→Het Parool (2e cluster), bestuurlijke_redactiedruk #169 (SPOF) |
| Wijfjes 2004, *Journalistiek in Nederland 1850-2000* (Boom, ISBN 9789053529492) | fysiek/antiquariaat | statelijke_inhoudsmoderatie #132, rel 1772/1773 (2e cluster), historische laag |
| Van den Berg & Van der Veer 1986, *Ideologie en massamedia* (VU Uitgeverij) | fysiek/UB VU | elite_referentiekader #20 (Akzo-frame, 2e cluster) |
| Werkgroep Perskoncentratie 1972 (SUN) | fysiek/KDC Nijmegen | eigendomsconcentratie #1 historisch + mediakritiek_marginalisering #196-instanties |
| Hamelink 1978, *De mythe van de vrije informatie* (In den Toren, ISBN 9060744942) | fysiek; DARE heeft alleen record | #196-instanties, vroege NL politieke economie |
| Rietman 1988 (doctoraalscriptie RU) | Radboud-archief of mailcontact Rietman | Herman-replicatie El Salvador/Nicaragua |
| Deprez e.a. 2011 (TvC 39(1), DOI 10.5117/2011.039.001.021) | paywall AUP/UGent | Israël-cluster (confound-regime) |
| Prenger & Van Vree 2003, *Schuivende grenzen* | ResearchGate/Academia-account | commerciele_afhankelijkheid #4, hoofdredacteur_als_filter #46 |
| Luyendijk 2006, *Het zijn net mensen* | archive.org-leenaccount (hetzijnnetmensen0000luye) of fysiek | persbureau_brongebondenheid #97, crisis_bronmonopolie #173 |
| Davies 2008, *Flat Earth News* | archive.org-leenaccount (flatearthnewsawa0000davi) of fysiek | pakketjournalistiek/pr_subsidie internationale literatuur |
| Wijnberg 2013, *De nieuwsfabriek* (ISBN 9789023477587) | archive.org-leenaccount (denieuwsfabriekh0000wijn) of fysiek | nieuwswaardenroutine #158 (SPOF), mediageniekheidsselectie #161 |
| De Landtsheer e.a. 2002 (TvS 23(3-4), pp. 403-438) | **open**, maar achter Anubis-botfilter: download in de browser via openjournals.ugent.be/sociologos/article/id/86560/ en lever de PDF aan | Kosovo: vijandbeeld #193-cluster |

Archive.org search-inside is zonder login getest en geweigerd ("Item not available") —
leenaccount van de eigenaar is voor die drie boeken echt nodig.

## Afhandeling (10 juli, "via admin")

Eigenaar gaf "via admin": Bergman-tranche 3 (2613–2623) én de 27 fase-1-args (2757–2783)
gemerged; entiteiten 1049/1050 en relaties 1865–1867 goedgekeurd; bronclassificaties
1481, 1488–1490 en 1600–1606 bevestigd (1600/1606 als `institutioneel` — de klasse-poort
weigert 'academisch' bij brontype rapport). `test_scoring.py` + `--strict` groen.

Clusterwinst gemeten na merge: citaatautorisatie #150 2→3, eigendomsconcentratie #1 2→3,
commerciele_afhankelijkheid #4 2→4, persbureau_brongebondenheid #97 2→3,
pakketjournalistiek #7 5→7, platform_advertentie_concentratie #40 →2, publieke_aanval #11
0→1 (nog SPOF — fase-2/Wijfjes). Relaties 1770–1772 blijven SPOF tot fase 2.

**Nagekomen (voorgesteld, wacht op merge):** arg 2784 — het ontbrekende stéunargument op
mechanisme #196 (Lexis-Nexis-nultelling + Niemantsverdriet-marginalisering, bron 1448):
na de merge van het Grunberg-tegenargument (2623) stond #196 anders scheef (alleen
tegenbewijs op het mechanisme zelf; geloofw. 0,06). Citaties verbatim gecorrigeerd na
eerste indiening (PATCH in-place, eigen voorgesteld argument).
