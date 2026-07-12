# Ronde 10 — grote sweep ontbrekende verbanden (assistent)

**Datum:** 2026-07-03 · **Account:** assistent (bijdrager) · alles `voorgesteld`.
**Opdracht eigenaar:** "Doe een uitgebreide ronde verbanden en entiteiten zoeken, zoek er 200" +
**"Wikipedia is geen bron, gebruik dan op zijn minst Wikipedia's eigen bronnen."**

## Werkwijze
6 parallelle research-subagents (later +2) over de dunne ruggengraat; per vondst de
**onderliggende, niet-Wikipedia** bron met verbatim quote. Ik heb elke dragende quote
zélf via WebFetch geverifieerd vóór indiening. Veel voorgestelde edges bleken **al te
bestaan** (dedup-check vooraf) — die zijn overgeslagen of alleen met een nieuw argument
versterkt. Kwantiteit nooit boven kwaliteit: onbronbaar/alleen-Wikipedia → niet ingediend.

## Wikipedia-regel — hoe toegepast
Geen enkele geciteerde bron is Wikipedia. Waar Wikipedia het startpunt was, doorgelopen
naar: parlement.com (PDC Universiteit Leiden), officiële org-pagina's (klm.com, ert.eu,
nidv.eu, energie-nederland.nl, epceurope.eu, dsm-firmenich, umicore.com), ACM-besluiten,
SEC/IR-pagina's, eerstekamer.nl, en kwaliteitsmedia (Consultancy.nl, Villamedia, NOS,
Advocatie, Mr. Online). Ronde-9-Wikipedia-citaties (BNR/Criel) staan op de lijst om bij
een volgende passage door de onderliggende bron te vervangen.

## Ingediend — cluster 1: draaideur-politici (mech 18) — 27 relaties, rel #799–825
Persoon→org loopbaan-/bestuursbruggen, gedateerd; org↔partij-brug verschijnt afgeleid.
Nieuwe entiteiten: **Huawei (375)**, **MKB-Nederland (376)**, **Hague Corporate Affairs (377)**.
Kroes→Uber(adviseur), Eurlings→KLM, Balkenende→EY + →ING, Bos→Shell, Jack de Vries→Hill+Knowlton,
Heemskerk→Royal HaskoningDHV/ERT/ASML/ABN AMRO, Hillen→NIDV, Hermans→MKB-NL/Hague Corporate/WNL,
Bruins→NPO, Knops→NIDV/Nederlandse Loterij, Van Nieuwenhuizen→Energie-Nederland,
Ollongren→Postcode Loterij, De Liefde→Uber, Schaart→Microsoft/Huawei, Bruins Slot→NPO,
Van der Burg→NTR, Eenhoorn→EY/WNL, Wolffensperger→NPO(NOS-rechtsvoorganger).
(Relatietype `commissaris` bestaat niet in de enum → RvC/RvT als `bestuurder` ingediend.)

## Ingediend — cluster 2: DPG/SDM-bestuur interlocks (mech 18) — 6 relaties, rel #826–831
Nieuwe entiteit: **Oxfam Novib (378)**. Alleen net-nieuw naar bestaande orgs:
Christian Van Thillo→DPG(executive chairman) + →Groupe Bruxelles Lambert(media↔kapitaal),
Thomas Leysen→Mediahuis, Frederieke Leeflang→ABN AMRO, Shula Rijxman→Gemeente Amsterdam(D66-draaideur),
Farah Karimi→Oxfam Novib. (Al bestaand & overgeslagen: Leysen→dsm/Umicore/KBC, Van Thillo→EPC,
Karimi→PAX, Venema→SDM/EPP, SVDJ-bestuur, Zonderop→Clingendael. Directory-only leads
Criel/Sevinga→DPG niet ingediend — nog niet aan primaire bron verankerd.)

## Ingediend — cluster 3: Tier A structuur (versterking + toezicht) — 3 nieuwe relaties + 5 args
- **Argumenten op bestaande edges:** DPG→RTL Nederland (rel 9): ACM-vergunning 27-6-2025 +
  effectuering 1-7-2025 (arg #1257–1258). Clingendael→NOS (rel 36): twee concrete expert-
  instanties Stijnman + Van Schaik (arg #1259–1260). CvdM→Ongehoord Nederland (rel 497):
  Mediawet-boete €40k (arg #1261).
- **Nieuwe toezicht-edges (tegenmacht, mech 76):** DNB→ABN AMRO (bonusverbod-boete €15 mln,
  rel #832), Autoriteit Persoonsgegevens→DPG Media (AVG-boete €525k, rel #833),
  Raad voor de Journalistiek→NRC (klacht gegrond, rel #834). Verbindt drie tot dusver
  vrijwel losse toezichthouders (DNB, AP, RvJ).
- **Overgeslagen (al bestaand):** alle NPO→ledenomroep-bestel-edges; persbureau→NL-media
  loopt via ANP (geen schone directe edge — enkel AFP/Reuters/AP→ANP, die al bestaan).

## Ingediend — cluster 4: systemisch eigenaarschap BlackRock/Vanguard (mech 25) — 12 relaties, rel #835–846
Zes bedrijven die de indexbeleggers-lus nog niet hadden: dsm-firmenich, ABN AMRO, KBC,
Umicore, Uber, Adidas — elk BlackRock + Vanguard. Percentages als momentopname (peildata
2025-2026), primair waar mogelijk (KBC via GlobeNewswire-transparantiemelding, Umicore via
eigen IR; overige via investing.com institutional-ownership, géén Wikipedia). Invloed op de
vloer (klein systemisch effect). Shell/ING/ASML/Philips/Unilever/P&G hadden beide beleggers al.

## Tussenstand na cluster 1–4
- **Nieuwe relaties: 48** (27 + 6 + 3 + 12). **Nieuwe entiteiten: 4** (375–378).
- **Nieuwe argumenten: ~53** (#1224–1276). **Nieuwe bronnen: ~45** (#530–574).
- Validator `--strict`: **groen** (geen fouten boven baseline; golden snapshot groen).

## Bewust NIET ingediend (kwaliteit > kwantiteit)
- Directory-only (managementscope.nl) leads Criel/Sevinga→DPG, Broertjes→NDC/RTV Utrecht,
  Nijboer↔PwC, De Bethune↔Vandewiele, Zonderop↔FD Mediagroep — verbatim-primair ontbreekt.
- Van Thillo→Mediahuis: **fout** (Mediahuis is Leysens vehikel, niet DPG) — niet ingediend.
- Epifin/Berlingske (Criel/Emmanuel Van Thillo/Convent): intra-concern eigendom, geen externe draaideur.
- Jelle van Baardewijk→NPO (Filosofisch Kwintet): citatie te zwak (affiliatie-quote dekt de
  optreden-claim niet) — in log, niet in model.
- HCSS→BNR (Boekestijn & De Wijk-podcast): bnr.nl blokkeert; geen citeerbare directe bron.

## Ingediend — cluster 5: resterende dunne personen (mech 18) — 4 relaties, rel #847–850
Na dedup bleek het gros van agent-7's 33 vondsten **al te bestaan** (voorgesteld uit
eerdere rondes — de graad-telling onderschatte hoe verbonden deze personen al zijn).
Net-nieuw: Weesie→De Telegraaf(verslaggever), Bauke Geersing→NOS(directeur; naamcorrectie
'Bauke' i.p.v. 'Bouke' bij id 214 nog nodig), Huffnagel→Gemeente Amsterdam(wethouder),
Choho→Gemeente Amsterdam(wethouder).

## Ingediend — cluster 6: elite-forum + denktank→NOS — 5 relaties, rel #851–855
Alleen **zelf-verifieerbare** vondsten. WEF-deelnames (lidmaatschap, mech 103): Balkenende
(Davos 2008), Van Nieuwenhuizen (2019), Ollongren (2022) — via officieel WEF-Flickr /
Nederlands overheidsplatform. Denktank/gezagsinstituut→NOS (expert_framing, mech 8):
De Nederlandsche Bank→NOS (Knot), Transnational Institute→NOS (Jelsma).

## BEWUST NIET ingediend — elite-netwerk (verificatiediscipline)
Bilderberg-lidmaatschappen (Kroes, Balkenende, Leysen, Ollongren) en Leysen→Trilaterale
Commissie / →ERT: de agent leverde officiële-deelnemerslijst-URL's + verbatim quotes, maar
**ik kon ze niet zélf verifiëren** — bilderbergmeetings.org blokkeert fetches, web.archive.org
is onbereikbaar vanuit deze omgeving, en de Trilateral-/ERT-PDF's waren onleesbaar. Juist in
dit complot-gevoelige domein houdt het model zich strikt aan zelf-geverifieerd bewijs, dus
deze blijven buiten het model (hier gelogd voor menselijke controle, mét bronnen):
- Kroes→Bilderberg (2008/2010/2011/2012); Balkenende→Bilderberg (2008); Leysen→Bilderberg
  (2011–2026, bijna continu); Ollongren→Bilderberg (2016/2025).
- Leysen→Trilaterale Commissie (2022, EU-ledenlijst); Leysen→ERT (~2015–2020, InfluenceMap-snapshot).
- Kroes→WEF (2013, WEF-PDF, niet fetchbaar). Timmermans/Van Beurden/Wijers: niet in model.

## EINDTOTAAL ronde 10
- **Nieuwe relaties: 57** (voorgesteld) — cluster 1: 27, 2: 6, 3: 3, 4: 12, 5: 4, 6: 5.
- **Nieuwe entiteiten: 4** — Huawei (375), MKB-Nederland (376), Hague Corporate Affairs (377), Oxfam Novib (378).
- **Nieuwe argumenten: 62** (#1224–1285), incl. 5 versterkings-args op bestaande edges
  (DPG→RTL, Clingendael→NOS ×2, CvdM→ON).
- **Nieuwe bronnen: 54** (#530–583).
- Validator `--strict`: **groen** (310 fouten = ongewijzigde baseline DDL-drift; golden snapshot groen).

## Belangrijkste les van deze ronde
De ~200-ambitie botste op een verrassing: het model is al véél dichter verbonden dan de
graad-verdeling (110 knopen op graad 1) suggereerde — heel veel kandidaat-edges stonden al
`voorgesteld` uit eerdere rondes. Consequente **dedup-vooraf** hield ~90 duplicaten buiten
(NPO-bestel compleet, persbureau-afname via ANP, Shell/ING/Philips-indexbelangen, Leysen/
Karimi/SVDJ-banden, het gros van de journalist/politicus-affiliaties). De 57 zijn dus schoon
net-nieuw. Kwantiteit is nergens boven kwaliteit gegaan: elke dragende quote zelf verbatim
geverifieerd, geen Wikipedia geciteerd, en niet-verifieerbaar bewijs (Bilderberg, directory-
only leads) bewust buiten het model gehouden.

## Openstaande verbeterpunten voor de eigenaar
- Naamcorrectie entiteit 214: 'Bouke' → 'Bauke' Geersing.
- Ronde-9 Wikipedia-citaties (BNR, Criel) vervangen door onderliggende bron.
- Directory-only leads (Criel/Sevinga→DPG, Broertjes→NDC/RTV Utrecht, Nijboer↔PwC) verankeren
  aan een primaire bron vóór eventuele invoer.
- 57 nieuwe voorstellen wachten op review (mens/`via admin`).
