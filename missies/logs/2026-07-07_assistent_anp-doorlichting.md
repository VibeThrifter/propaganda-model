# ANP-doorlichting — assistent — 2026-07-07

**Opdracht (eigenaar):** zoek *alles* over het ANP en alle verbanden/mogelijke elementen die —
ook indirect, via welk mechanisme dan ook — de nieuwsbias kunnen beïnvloeden, voor het praktijkmodel.

## Bevinding vooraf (drie parallelle onderzoeksslagen)

- **Het ANP is al dicht gemodelleerd** (entiteit 12, rol 8 `persbureau`, 36 goedgekeurde relaties,
  eigen mechanisme-subcluster 7/97/106/107/120 + emergent veld 6 `schijnpluriformiteit`).
- **De churnalism-/poortwachterclaims zijn al gesourcet** (m7: args 394/420/450/1919; veld 6: arg 489).
  Bewust NIET opnieuw ingediend.
- **De echte leemte is de bewijs- én invloedslaag**, niet ontbrekende edges. De *verbanden* zijn
  vrijwel compleet; er ontbreekt geen betekenisvolle, SOLID-te-sourcen én bias-relevante pijl.
  → geen nieuwe theorie, geen RfC; alleen bijdragepad-inhoud onder `assistent`, alles `voorgesteld`.

## Ingediend (alles `voorgesteld`)

Bronnen: **1044** NOS Talpa→Oomen (2382644) · **1045** NOS/Nieuwsuur Oomen-quotes (2382728) ·
**1046** ANP "Over ons" · **1047** ANP Business "95% van de Nederlandse media". Classificatie-
*voorstellen* (adviserend) op bestaande bronnen 890/891/334/956.

Argumenten:
- **1979** — `property='influence'` op mechanisme **m7 pakketjournalistiek**: ANP als zwaarste
  sourcingknoop (~66% webnieuws 2014 / 24→28% krantenartikelen 2006–08). Citaties 891 (Boumans) + 890
  (Nieuwsmonitor). *Kern van de opdracht:* de invloed-as van het ANP-kanaal stond volledig op de
  0,05-vloer — geen enkele influence-bijdrage raakte een ANP-relatie. Dit is ook de voorwaarde
  voor eventuele afgeleide (indirecte) ANP→publiek-pijlen.
- **1980** — m97 `persbureau_brongebondenheid`: ANP Business/Pers Support verkoopt commercieel
  persbericht-distributie ("95% van de Nederlandse media") — informatiesubsidie op het chokepoint.
  Citaties 1047 + 1046.
  - **1981** — eerlijke ondergraving (contradicting reply op 1980): ANP's firewall-claim ("staat los
    van onze onafhankelijke redactie") — de stap 'verkoopt distributie'→'buigt de selectie' mist een
    schakel. `reasoning` verplicht ingevuld; resolutielus `open`. Citatie 1046.
- **1982** — m106 `klantvraag_persbureau` (was dormant): ANP als commerciële leverancier wier output
  meebeweegt met klant-titels. Citatie 1046. Structureel, niet gekwantificeerd (klantconcentratie THIN).
- **1983** — rel 17 (Oomen→ANP, Eigendom): sinds 2021 één particuliere eigenaar die winst afzweert —
  hoge zekerheid eigenaarschap, lage commerciële druk (Eigendom = zwakke route). Citaties 1045.
- **1984** — rel 717 (ANP→Novum, `acquisitiestrategie`): overname Novum 2015, 37/52 banen weg —
  concentratie verkleint onafhankelijke capaciteit, verdiept één-bron-afhankelijkheid. Citaties 334.
- **1985** — rel 1121 (ANP→Hollandse Hoogte, Eigendom): chokepoint strekt zich uit naar nieuwsbeeld;
  NVJ/NVF: "wie met het ANP in conflict raakt, heeft niet langer een alternatief." Citatie 956.

## Bewust NIET ingediend (eerlijkheid, geen `contextual` "niets gevonden")

- Churnalism-prevalentie — al gesourcet (dubbel indienen vermeden).
- 80–90% buitenland-wire-afhankelijkheid — herkomst te zwak.
- ANP-omzet / klantconcentratie / overheidscontract-afhankelijkheid — niet te sourcen (jaarcijfers
  niet openbaar/opgehaald).
- Redactiestatuut-tekst ANP — niet opgehaald (alleen NVJ-principe).
- Opinie-controverses (Spreekbuis "PR-bureau voor Talpa", Netkwesties) — te zwak/opinie.
- Auteursrecht-trol (Visual Rights Group) — geen bias-lijn.

## Verificatiediscipline (belangrijk)

Alle quotes verbatim tegen de bron gecheckt vóór indienen. Twee **gefabriceerde quotes** van de
onderzoeks-subagent onderschept en gecorrigeerd:
- "monopolistische trekken" (Hollandse Hoogte) — bestaat NIET in het artikel; vervangen door de
  echte NVJ/NVF-quote over "geen alternatief".
- "sterke concentratie op de Nederlandse fotomarkt" — ook niet verbatim; niet als citaat gebruikt,
  in eigen woorden geparafraseerd.

## Opschoon-kandidaten voor de maintainer (niet zelf verwijderd)

- Bronnen **890/891** zijn ongebruikte duplicaten van al-geciteerde studies (bron 28 e.a.).
- **Freek Staps→ANP** `personeel` staat dubbel: rel **1081** én **1091** (draaideurconstructie).
- Directie-datum: **Martha Riemsma is directeur sinds okt 2024** (niet 2019); zij volgde **Martijn
  Bennis** op (die door de Oomen-overname 2021 heen zat). Entiteit-beschrijving t.z.t. bijwerken.

## Update — per-edge invloed + merge via admin (zelfde dag)

Op verzoek "in praktijkmodel per edge.. mergen via admin":

**Per-edge invloed-bewijs** (assistent, `property='influence'`) op de edges die de bronnen bij
naam noemen — géén NOS (niet in de studies genoemd; alleen edges met een edge-specifieke bron):
- **2043** rel 30 ANP→de Volkskrant · **2044** rel 35 ANP→NU.nl · **2045** rel 31 ANP→De Telegraaf
  — Boumans/UvA "66% ... volkskrant.nl, nu.nl en telegraaf.nl" (bron 891).
- **2046** rel 219 ANP→Metro — Nieuwsmonitor "Metro (53%) ... meer dan de helft" (bron 890).

**Gemerged via admin** (`maxime`-maintainer-token, `scripts/admin.py merge`): alle 11 argumenten
1979/1980/1981/1982/1983/1984/1985 + 2043/2044/2045/2046 → status `ongecontroleerd`.

**Effect (geverifieerd via `scoring.compute_all_scores`):**
- Afgeleide invloed per edge: rel 30/35/31/219 van 0,05 → **0,0609**; NOS (rel 32, geen arg) blijft 0,05.
  Bewust conservatief: M1.7 "weinig bewijs verschuift weinig" (w = massa/(massa+K); één vers argument
  = kleine verschuiving). Groeit met meer bewijs/ratings.
- m7 `pakketjournalistiek`: sterkte 0,062, `sterkte_bewijs_args=1` (invloed-lijn nu geregistreerd).
- m106 `klantvraag_persbureau`: literatuur-geloofwaardigheid 0 → **0,168** — **niet langer dormant**.
- m97: geloofwaardigheid 0,398 (2 bronnen).
- Firewall-ondergraving werkt: arg 1980 σ 0,16 < τ 0,20 (gedempt door reply 1981) — bezwaarlus `open`.

**Nog steeds op stored-vloer (bewust niet aangeraakt):** `influence.py` (graaf-rankings +
afgeleide/indirecte pijlen) leest de **opgeslagen** `relations.influence` (0,05), niet de afgeleide.
De per-edge afgeleide invloed toont nu wél in de edge-weergave/mechanisme-sterkte; de topologische
graaf + indirecte ANP→publiek-pijlen bewegen pas als een maintainer de *opgeslagen* invloed licht —
een expliciete magnitude-beslissing, niet zelf verzonnen. Aangeboden als vervolg, niet gedaan.

## Update 2 — gap-analyse "alle ANP-relaties + andere outlets" ("alles", zelfde dag)

Dekkingsanalyse (94 echte outlets): eigenaar-edge bijna compleet (79/94); ANP-consumptie slechts
17/94 (maar veel outlets *horen* geen ANP-edge te hebben — alt-media/onderzoeksredacties churnen niet);
advertentiefilter vrijwel leeg. Twee bron-agents ingezet; alles verbatim nagecheckt.

**Ingediend (assistent, `voorgesteld`) — SOLID gesourcet:**
- Bronnen **1081** svdj "Media grijpen meer naar het ANP" (2021) · **1082** De Groene "Journalistiek
  of mediamaken?" (2024) · **1083** rd.nl ANP-auteurspagina.
- **Churn-waaier: 13 nieuwe ANP→outlet-edges** (rel 1444–1456, `bron_van`/m7), elk met sourced arg
  (2047–2059): 6 DPG-regionaal (BN DeStem, Brabants Dagblad, Eindhovens Dagblad, PZC, de Stentor,
  Tubantia) + 6 Mediahuis-regionaal (Gooi-/Eemlander, Haarlems, IJmuider, Leidsch, Noordhollands,
  Friesch Dagblad) — gegrond op svdj-quote "nieuwe langlopende contracten … met DPG en Mediahuis";
  + Reformatorisch Dagblad (566) **per-titel** gegrond op rd.nl.
- **Schijnpluriformiteit (veld 6):** arg **2060** (svdj — afhankelijkheid ná 2021 toegenomen,
  verschraling in de regio) + **2061** (De Groene — DPG's centrale redactie ADR Nieuwsmedia = tweede
  homogeniseringskanaal naast het persbureau).

**Bewust NIET ingediend (eerlijk gerapporteerd, geen fabricatie):**
- **dpa→ANP:** redistributie alleen blog-gesourcet (bouwenaanbeter); ANP's eigen site noemt dpa niet;
  Emerce-bron gaat over het *ANP Agenda*-platform, niet wire-copy. THIN → niet ingediend.
- **RVD/overheidsvoorlichting→ANP:** alleen blog (2018) + RD-artikel (1985) dat ANP juist als
  *selecterend* ("geen doorgeefluik") neerzet; geen afhankelijkheidsonderzoek. THIN. (Min Fin + OM
  dekken het gezagsinstituut-feeder-patroon al.)
- **FD / Nederlands Dagblad per-titel:** geen verbatim per-titel bron (FD paywalled). Niet ingediend.
- **Adverteerder-laag:** advertentiedruk is *diffuus* (hoort in mechanisme/certainty, niet als
  pijlenwaaier); geen gedocumenteerd incident opgedoken deze ronde → niets ingediend, geen mesh verzonnen.

**Boumans-nuance (belangrijk, als caveat — NIET als modelknoop):** de thesis (UvA 2016, PDF verbatim
geëxtraheerd) stelt *"Literal copy-paste practices have not been found."* — máár dat betreft zijn
**churnalism-index over persberichten**, niet ANP-wire-overname; zijn 66%-cijfer betreft juist de
**agency-agenda-share** (dat *steunt* de ANP-bijdragen). Het als "tegenargument" op de ANP-churn
plakken zou mis-attributie zijn → gerapporteerd, niet ingediend.

**Opschoon-kandidaten (maintainer):** Staps→ANP dubbel (rel 1081/1091 — let op: bron-id 1081 ≠
relatie-id 1081); John de Mol (19) zonder edge; overweeg ANP→DPG/Mediahuis op holding-niveau i.p.v.
losse titels als de waaier te fijnmazig is.

Niet gemerged (geen "via admin" deze ronde) — staat in de queue.
