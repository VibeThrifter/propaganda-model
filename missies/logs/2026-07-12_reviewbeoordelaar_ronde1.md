# Onbewaakte ronde — reviewbeoordelaar · ronde1 · 2026-07-12

- Brief: `missies/reviewbeoordelaar_brief.md` (blob `0bbf39f10b7b`)
- Account: `(geen — alleen-lezen)`
- Gestart: 2026-07-12T23:45:57

## Sessie-uitvoer

```

== REVIEWBEOORDELAAR — RONDE 1 — 2026-07-12 ==
Brief-blob-hash: 0bbf39f10b7b | account: geen (alleen-lezen) | uitvoer: data/review_advies.json (31 items) + dit log
Niets in het model gewijzigd (geen token, geen schrijfacties).

## Omvang van de wachtrij
Gereconstrueerd uit data/propaganda_model.db (de /api/review_queue is reviewer-gated; zonder
token direct uit de DB gelezen — GET/DB-lezen is toegestaan).
- voorgestelde argumenten:            3   -> beoordeeld
- voorgestelde relaties:             26   -> beoordeeld
- voorgestelde entiteiten:            0
- open RfC's / voorstellen:           2   -> beoordeeld
- betwist (herkeuring):             125   -> buiten scope (zie noot)

NOOT over de 125 betwiste argumenten: alle 125 zijn `legacy`-seed-argumenten (created
2026-06-01) die de eigenaar (maxime) op 2026-07-07 in EEN batch op `betwist` zette met de
reden "Onvoldoende te sourcen (workflow-onderzoek): ...". Bewuste eigenaars-herkeuring van
ongesourcete seed-claims, elk met een eigen per-item dispute-reden in het edit_log — geen
anomalie/bug. De brief-scope noemt voorgesteld-args + voorgesteld-relaties/-entiteiten +
open RfC's, niet de herkeuring-lijst; die items dragen al de eigenaars-motivatie. Daarom
NIET per item van advies voorzien; ze wachten op her-sourcing (documentalist) of afwijzing.

## Adviezen per bucket (merge-klaar bovenaan)

--- MERGE-KLAAR (18) ---
Argumenten:
- arg 3477 · rel 2043 · supporting — JASON-oprichtingsband. Poort gehaald; citaat VERBATIM
  webgeverifieerd. Claim netjes tot "de oprichting" begrensd. Let-op: certificeert een
  overreikende relatie (zie relatie:2043 / arg 3533).
- arg 3520 · reply op arg 516 · contradicting (ondergraving) — sterke non-sequitur:
  PvdA-burgemeester WORDEN in 2011 bewijst geen lidmaatschap TIJDENS het hoofdredacteurschap
  (1995-2010). Welgevormd, reasoning benoemt de stap. Dempt terecht een eigen-seed-argument
  van maxime — gedecorreleerde kritiek.
Relaties (officieel/primair gesourcet, quote dekt de claim):
- rel 705 UvA->UvA Journalistiek (uva.nl)
- rel 1718 Sandmann->Clintel financiering (Clintel + DeSmog; + contextual confound 2490)
- rel 1719 Delphi->CFGSEC 1,2M (FTM + Pointer, TNO-bevestigd)
- rel 1765/1766/1767 Defensie->RTL/De Telegraaf/SBS6 betaalde content (FTM, bedragen
  verbatim) — tevens instantiaties RfC 49
- rel 1817 Puts->AWVN (awvn.nl) · rel 1818 Fortuin->CNV (cnv.nl) · rel 1820 Van den
  Heuvel->CNV (NOS)
- rel 1874 Rijpma->RvdJ · rel 1875 Boersema->RvdJ (beide rvdj.nl)
- rel 1914 SGP->Reformatorisch Dagblad (De Groene + NPO Kennis)
- rel 1915/1916 GroenLinks-PvdA->GroenLinks/PvdA fusie (parlement.com + groenlinkspvda.nl)
- rel 2038 Vletter-van Dort->Erasmus dienstverband (eur.nl)
RfC:
- voorstel 52 — Samenvoegen De Persgroep (108) -> DPG Media (1). Schone dedup: 108 heeft 0
  relaties / 0 argumenten, pre-2019-naam, geen hertriage nodig. Housekeeping-winst.

--- VERBETEREN (10) ---
Kale beweringen (0 argumenten/citaties -> orphan-poort blokkeert goedkeuring):
- rel 1714 Berkhout->Delphi Consortium · rel 1715 Berkhout->CFGSEC · rel 1716
  Berkhout->Clintel · rel 1717 Crok->Clintel — plus certainty-prior 0,8/0,9 ZONDER bewijs
  (hoort op vloer 0,05). Feiten bekend/triviaal te sourcen, maar de relatie draagt nog geen
  gesourcet argument.
- rel 1909 Tweede Kamer->Presidium · rel 1860 ProDemos->StemWijzer — idem, geen bewijs.
Bron-/vorm-gebreken:
- rel 704 HU->School voor Journalistiek — enige citatie is WIKIPEDIA (geen bron, alleen
  vindplaats). Feit klopt; vervang door primaire HU-bron.
- rel 526 De Graaf->Kummeling — LEEG citaat (alleen locator, geen quote) EN de
  "cooptatie"-duiding van een reguliere KB-benoeming is een inferentiesprong.
- rel 2043 BuZa->JASON — bron dekt alleen de oprichting (1975); type='alliantie' met open
  active_until reikt 51 jaar verder. Time-box naar 1975 / hertypeer (zie arg 3533).
RfC:
- voorstel 49 — nieuw mechanisme `betaalde_content`. STEUN op hoofdlijnen (scherpe
  definitie, correcte direct/freeze-test, wortel-vs-stok-afgrenzing tegen advertentiedruk
  #3, falsifieerbaar, NL-relevante instantiaties). Aanscherpen voor akkoord: (1) grens ook
  af tegen de naaste advertentie-buren mech 5 supportive_selling_environment en mech 102
  adverteren_als_belang (nu niet benoemd); (2) empirische basis smal — alle 3 instantiaties
  uit EEN FTM-onderzoek (2017) + EEN koper (Defensie); breng een niet-Defensie-instantie in;
  (3) verankering leunt op EEN journalistieke bron — voeg een media-studies/H&C-bron over
  advertorials/native advertising toe.

--- CONTEXT (3, let-op bij verder mergebaar item) ---
- arg 3533 · reply op arg 3477 · contradicting (aanklager) — valide citaat-dekkingspunt
  (About-quote dekt 1975-oprichting, niet 51 jaar alliantie). Beste resolutie: niet arg
  3477 dempen maar relatie 2043 time-boxen; dan vervalt de grond.
- rel 1831 ESB->FD Mediagroep — dekking klopt ("gehuisvest bij de FD Mediagroep"), maar
  type='lidmaatschap' voor een huisvestings-/inbeddingsband is wat los.
- rel 1894 Defensie->LIMC — bron dekt de onrechtmatige trendanalyses, niet rechtstreeks de
  "eigendom"-claim (LIMC = onderdeel landmacht). Overweeg een dekkende quote.

--- AFWIJZEN (0) ---
Geen. Bij twijfel -> verbeteren (conform brief: terughoudend afwijzen).

## Webcontroles (gescoped op citaat-integriteit) — elke zoekopdracht letterlijk
Eén gerichte controle deze ronde (zelf-gepubliceerde bron bij een sterke, al-aangevochten claim):
1. WebFetch -> https://jasoninstitute.com/about-us/
   prompt: bevat de pagina de exacte zin over "close collaboration with the Dutch Ministry
   of Foreign Affairs ... was born", en welk oprichtingsjaar/1975 staat er?
   RESULTAAT: pagina LEEG teruggekomen (JS-gerenderd/geblokkeerd), niet beoordeelbaar.
2. WebSearch -> JASON "close collaboration with the Dutch Ministry of Foreign Affairs"
   "Jong Atlantisch Samenwerkingsorgaan" was born
   RESULTAAT: treffer bevestigt de zin VERBATIM ("After close collaboration with the Dutch
   Ministry of Foreign Affairs, JASON, or Jong Atlantisch Samenwerkingsorgaan Nederland, was
   born.") EN oprichting in 1975 door Rio Praaning en Willem van Eekelen. -> Citaat van arg
   3477 is ECHT, niet gehallucineerd; oprichtingsjaar door dezelfde bron gedekt. Bevestigt
   ook dat de bron alleen het oprichtingsmoment staaft, niet de doorlopende "alliantie".
Bron: https://jasoninstitute.com/about-us/

## Documentalist bron-suggesties (data/bron_suggesties.json)
Bestand ongewijzigd sinds 2026-06-22 (documentalist), reeds voorzien van mijn eerdere
check-verdicts. De drie betrokken argumenten zijn intussen afgehandeld: arg 622 (verworpen),
arg 542 (gemerged/ongecontroleerd), arg 536 (bestaat niet meer, hard-deleted). Geen verse
documentalist-ronde -> niets nieuws te checken; bestand niet herschreven.

## Negatieve resultaten / observaties (alleen log, geen modelbijdrage)
- Geen verzonnen of verkeerd-toegeschreven citaten aangetroffen; de JASON-quote (het grootste
  hallucinatie-risico deze ronde) hield stand.
- Geen INVLOED-PRIOR-schendingen: alle 26 voorgestelde relaties staan op invloed-vloer 0,05.
  Wel vier certainty-priors zonder bewijs (rel 1714-1717, 0,8/0,9) — als verbeter-punt
  meegegeven, geen afwijsgrond.
- Geen semantische duplicaten binnen de voorgesteld-wachtrij opgemerkt die difflib zou missen.

## Stance-balans
Beoordeelde voorgestelde argumenten (3): 1 steun (arg 3477) · 2 tegen (arg 3520, arg 3533,
beide ondergravingen) · 0 context-root.
Wat ik adviseer te mergen (argumenten): 1 steun + 1 tegen (arg 3520 dempt een
eigen-seed-argument van de eigenaar). De derde ondergraving (arg 3533, aanklager) staat als
CONTEXT — inhoudelijk valide, maar beter opgelost via een time-box op relatie 2043 dan via
demping. Beide contradicting-inzendingen op hun merites behandeld; geen systematische
strengheid richting de tegen-kant.
De 26 relaties zijn instantielaag-feiten (affiliatie/financiering/eigendom) zonder
stance-tweezijdigheid in de gebruikelijke zin; daar weegt bron-dekking, niet stance-balans.

## Exit
Wachtrij afgehandeld: 3/3 args, 26/26 relaties, 2/2 RfC's. Geen 429 (mijn server reageerde
200), geen dode LinkedIn-sessie, geen vulling ingediend (geen token). Ronde afgerond.
Ronde afgerond. Samenvatting van deze onbewaakte reviewbeoordelaar-ronde (alleen-lezen, geen token, niets in het model gewijzigd):

## Wat er in de wachtrij stond
- **3 voorgestelde argumenten**, **26 voorgestelde relaties**, **2 open RfC's** → alle beoordeeld.
- **125 `betwist`-argumenten** (herkeuring): een bewuste eigenaars-batch (maxime, 2026-07-07, "onvoldoende te sourcen") van legacy-seed-claims, elk met eigen dispute-reden — buiten de brief-scope, dus gekarakteriseerd in het log, niet per item.

## Twee uitvoeren geschreven
1. **`data/review_advies.json`** — 31 items (sleutels matchen exact de `review_queue`-ids): **18 merge-klaar · 10 verbeteren · 3 context · 0 afwijzen** (terughoudend, conform brief).
2. **Ronde-log** in `missies/logs/2026-07-12_reviewbeoordelaar_ronde1.md` (in het `Sessie-uitvoer`-blok dat de runner afsluit + van metadata voorziet).

## Kernbevindingen
- **Webcontrole (gescoped):** het JASON-citaat van `arg 3477` (zelf-gepubliceerd + al aangevochten) is **verbatim geverifieerd** — echt, niet gehallucineerd; oprichting 1975 door dezelfde bron gedekt. Wél bevestigt dat de bron enkel het oprichtingsmoment staaft, niet de open-einde "alliantie" (grond voor de verbeter-noot op `rel 2043`).
- **Zes kale relaties** (Berkhout/Crok-cluster, ProDemos→StemWijzer, Tweede Kamer→Presidium) hebben 0 argumenten/citaties → kunnen niet naar goedgekeurd; vier dragen bovendien een certainty-prior 0,8/0,9 zonder bewijs.
- **`rel 704`** citeert **Wikipedia** (geen bron) → vervangen door primaire HU-bron.
- **RfC 49 `betaalde_content`**: sterk (scherpe definitie, correcte freeze-test, wortel-vs-stok tegenover advertentiedruk), maar drie aanscherpingen — afgrenzen tegen mech 5/102, smalle empirische basis (alle instantiaties uit één FTM-onderzoek/één koper), en één journalistieke bron zonder theoretische verankering.
- **RfC 52** (De Persgroep→DPG Media dedup): schone housekeeping-winst → merge-klaar.

**Stance-balans:** van de te-mergen argumenten 1 steun + 1 tegen (`arg 3520` dempt terecht een eigen-seed-argument van de eigenaar); de aanklager-ondergraving `arg 3533` als context met een fix-route. Geen systematische strengheid richting de tegen-kant.

Geen 429, geen dode LinkedIn-sessie, geen vulling ingediend.

```

## Runner-metadata

- Exit-code: 0
- Duur: 841.3 s
- Oogst (edit_log-delta van `—`): 0
- Beëindigd: 2026-07-12T23:59:58
