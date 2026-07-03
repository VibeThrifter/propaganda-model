# Missielog: opleidingsniveau — School voor Journalistiek + koppel opleiding↔instelling

**Datum:** 2026-07-03 · **Account:** `assistent` · **Aanleiding:** vraag van de eigenaar
("universiteiten/hogescholen zitten erin — moeten opleidingen er ook bij, of is dat te triviaal?").

## Modelleerbesluit (granulariteit)

Opleidingen zijn **geen** categorie om generiek toe te voegen; een opleiding wordt alleen
een eigen knoop als het mechanisme op dát niveau grijpt. Voor journalistiek-opleidingen is
dat zo: `academische_socialisatie` (het vormen en leveren van journalisten aan redacties)
werkt op opleidingsniveau — de faculteit tandheelkunde socialiseert geen journalisten.
Financiering (`denktank_financiering_bias`), flak (`publieke_aanval`) en
`expert_legitimatie` werken op instellingsniveau en blijven daar. Bestaand precedent:
rel. 303/304 (UvA Journalistiek → NOS / de Volkskrant) stonden al op opleidingsniveau.

## Zoekopdrachten (alle gelogd, incl. verificatie)

1. WebSearch: `School voor Journalistiek Utrecht opgericht 1966 eerste journalistiekopleiding Nederland geschiedenis` → Wikipedia + Villamedia-50-jaar-artikel.
2. WebSearch: `School voor Journalistiek Hogeschool Utrecht grootste journalistiekopleiding alumni NOS RTL kweekvijver` → HU-opleidingspagina's, Villamedia.
3. WebSearch: `uva.nl master journalistiek media opleiding Universiteit van Amsterdam` → duale master Journalistiek en media (Mediastudies) + carrièrepagina.
4. Verbatim-verificatie van élke quote via curl + tekstextractie op de vier bronpagina's
   (les van de PAX-misattributie): alle quotes letterlijk teruggevonden.

**Negatief resultaat:** geen bron gevonden die SvJ-alumni kwantitatief aan specifieke
redacties koppelt (à la de UvA-carrièrepagina); de SvJ→NOS-edge leunt daarom op de
algemene opleidingsclaim (Villamedia) + concreet alumnus-voorbeeld (Wikipedia:
Jeroen Overbeek, nieuwslezer NOS Journaal). Een edge SvJ→RTL Nieuws is bewust **niet**
ingediend: RTL kwam alleen als lijstvermelding zonder citeerbare onderbouwing voor.

## Ingediend (alles `voorgesteld`; een mens beslist)

Bronnen (met url-locators + voorgestelde classificatie, adviserend):
- **315** Wikipedia "School voor Journalistiek" (grijs / nl_systeem)
- **316** Villamedia "School voor Journalistiek Utrecht vandaag precies 50 jaar" (regulier / nl_systeem)
- **317** UvA "Duale master Journalistiek en media" hoofdpagina (primair / nl_systeem)
- **318** UvA carrièreperspectief-pagina (primair / nl_systeem)

Entiteit:
- **336** School voor Journalistiek (`onderwijsinstelling`, rol-suggestie `kennisinstituut`, active_from 1966-10-03)

Relaties:
- **703** School voor Journalistiek → NOS (`beinvloeding`, mechanisme `academische_socialisatie`)
- **704** Hogeschool Utrecht → School voor Journalistiek (`eigendom`, **kandidaat** — bewust
  mechanisme-loos: het rol-paar instelling→opleiding heeft nog geen theorie-element;
  beschrijvende koppel, geen invloedsclaim)
- **705** Universiteit van Amsterdam → UvA Journalistiek (`eigendom`, **kandidaat**, idem) —
  lost de bestaande inconsistentie op dat UvA Journalistiek (104) en de UvA (311) los van
  elkaar zweefden.

Argumenten (supporting roots, elk met echte citaties):
- **A1** op rel. 703: SvJ als socialisatiekanaal naar de NOS (Villamedia-quote + Wikipedia-alumnus).
- **A2** op rel. 704: SvJ onderdeel van HU (Wikipedia-quote).
- **A3** op rel. 705: UvA Journalistiek = duale master van de UvA (uva.nl-quote).
- **A4** op bestaande rel. 303 (UvA Journalistiek → NOS): UvA-carrièrecijfers (75% journalistiek,
  25% omroep; NOS met naam genoemd) — bonus-bewijs uit het bronnenonderzoek.
- **A5** op bestaande rel. 304 (→ de Volkskrant): "Bij de dagbladen springen NRC Handelsblad
  en de Volkskrant eruit" — idem.

Stance-balans: 5× supporting, 0× contradicting — verdedigbaar: dit was een gerichte
structuurronde op verifieerbare organisatorische feiten (bestaan/inbedding van opleidingen),
geen claim-toetsronde. Invloed is nergens boven de 0,05-vloer gezet (geen
`property='influence'`-argument ingediend; de carrièrecijfers zouden daarvoor kandidaat
zijn — aan de reviewer).

## Open eindjes voor de reviewer

1. Rel. 704/705 zijn kandidaten: goedkeuren kan pas als het rol-paar instelling→opleiding
   een theorie-element krijgt (RfC), óf de koppel blijft bewust als incubant staan.
2. Overweging: `relation_type` `eigendom` gekozen voor de inbedding (precedent DPG→titels);
   als dat te sterk "bezit" connoteert is een alternatief bespreekbaar.
3. De granulariteitsregel zelf is vastgelegd in `missies/scout_brief.md` (§ Granulariteit),
   CLAUDE.md (modelleerdiscipline, litmus-punt 2) en het Claude-geheugen.

## Ronde 2 (zelfde dag) — Fontys Hogeschool Journalistiek + goedkeuring ronde 1

Op aanwijzing van de eigenaar ("keur goed als admin en zoek nog meer van deze verbanden"):

**Goedgekeurd (ronde 1, als `maxime`/admin):** entiteit 336 + rel. 703 (SvJ→NOS) met
instantiaties; argumenten 942–946 gemerged; bronnen 315–318 geclassificeerd
(315 grijs, 316 regulier, 317/318 institutioneel — `primair` botste met brontype
`website`, dus institutioneel). Rel. 704/705 blijven bewust **voorgesteld** als kandidaat
(mechanisme-loos; de orphan-poort blokkeert goedkeuren tot een RfC ze adopteert).

**Nieuwe zoekronde.** Zoekopdrachten (gelogd):
- `Fontys Hogeschool Journalistiek ... alumni journalisten omroep krant` → Wikipedia + FHJ-mediacafé.
- `Fontys ... Astrid Kersseboom NOS Bram Vermeulen alumni` → verbatim-koppeling gevonden.
- `Rijksuniversiteit Groningen master Journalistiek ... redacties` → **niet ingediend**:
  de RUG-master socialiseert wel journalisten, maar geen bron noemt specifieke redacties
  (stage "bij een nieuwsorganisatie" is generiek). Zonder outlet-niveau-bron geen
  gesourcete socialisatie-edge → zou een trivia-knoop zijn (alleen een koppel naar RUG,
  geen mechanisme-edge). Kandidaat voor later mét betere bron. RUG-instelling (284)
  bestaat al; de opleiding is dus bewust níét als losse knoop toegevoegd.
- (Windesheim-zoekopdracht door de eigenaar onderbroken; niet uitgevoerd.)

Verbatim geverifieerd (curl + tekstextractie): Wikipedia "De Fontys Journalistiek (FJ) in
Tilburg werd in 1980 opgericht als Academie voor de Journalistiek."; FHJ-mediacafé "Drie
Fontys-alumni, Astrid Kersseboom (NOS), Bram Vermeulen (VPRO) en Sinan Can (BNNVARA), ...".

**Ingediend én goedgekeurd (als admin):**
- Bronnen **341** (Wikipedia Fontys, grijs) + **342** (FHJ-mediacafé, regulier), beide nl_systeem.
- Entiteit **341** Fontys Hogeschool Journalistiek (`onderwijsinstelling`, rol `kennisinstituut`, active_from 1980).
- Relaties (alle `beinvloeding`, mechanisme `academische_socialisatie`, mét instantiatie):
  **724** Fontys→NOS (Kersseboom), **725** Fontys→VPRO (Vermeulen), **726** Fontys→BNNVARA (Can).
- Argumenten **967–969** (supporting roots, mediacafé- + Wikipedia-citaat), gemerged.
- **Geen koppel opleiding↔instelling**: de moederinstelling Fontys is geen knoop en heeft
  geen instellingsniveau-mechanisme in het model — conform de granulariteitsregel voeg je
  dan alléén de opleiding toe (waar het mechanisme grijpt), niet de instelling erbij.

Stance-balans ronde 2: 3× supporting (organisatorische socialisatiefeiten). Invloed op de
0,05-vloer gelaten.
