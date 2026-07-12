# Scout-ronde: economische expertise-toevoer → media → financiering (uitputtende sweep)

- **Datum:** 2026-07-09
- **Account:** assistent (bijdrager) — alles landt `voorgesteld`
- **Git-hash bij aanvang:** de441f1
- **Brief:** `missies/scout_brief.md` (structuur-ontdekking; bron→knoop→verband→argument) + eigenaarsopdracht:
  *"Zoek alle economische denktanks, instituties, banken, universiteiten en alles af die experts
  afleveren aan de gevestigde media, de experts ook, in welke media. Ook hoe zij gefinancierd zijn."*
- **Scope:** vult de Sourcing-schakel *expert-legitimatie* verder in (dossier
  `onderzoek/3_mechanismes-van-beinvloeding/sourcing-naar-bias/05_denktank-expert-legitimatie.md`).
  De klassieke media-economen-elite (Tuk 2014) + bank-hoofdeconomen stonden al in het model
  (sterkste-routes-r1); deze ronde breidt uit naar bank-/toezicht-/commerciële/werkgevers-/
  universitaire economie én, tweezijdig verplicht, de **kritische/heterodoxe economen**.
- **Methode:** multi-agent workflow (`econ-expertise-sweep`, run `wf_51cfaef6-ff6`): 7 parallelle
  onderzoeksagenten (één per categorie, neutrale zoekvraag, WebSearch/WebFetch), gevolgd door
  **adversariële bron-verificatie per vondst** (aparte skeptische agent: quote verbatim? attributie
  correct? géén Wikipedia/tertiair?). Alleen `verdict='klopt'` ging door. Indienen daarna serieel &
  idempotent via de REST-API onder het `assistent`-token (submit-script; dedup op naam + rol-paar).
  73 agents, 0 errors, ~3,28 M tokens.

## Oogst (66 ruwe verbanden → 65 doorgelaten, 1 afgekeurd)

- **Bronnen #1491–1549** (65) · **Entiteiten #1008–1040** (33 nieuw) · **Relaties #1790–1845** (56;
  9 vondsten hercinteerden een bestaand rol-paar en kregen alleen hun argument) · **Argumenten
  #2626–2690** (65, elk met verbatim-gecheckte citatie, alle `contributed_by=assistent`).
- Alles `voorgesteld` geverifieerd in de DB; `validate_model.py --strict` groen (score/baseline
  onbewogen — `voorgesteld` telt in niets), golden-snapshot groen.

### Per categorie
- **bank-economen** — 8 verbanden; nieuw: Luc Aben (Van Lanschot Kempen), Carsten Brzeski (ING,
  Global Head of Macro), Han de Jong (oud-hoofdeconoom ABN AMRO → Wynia's Week/eigen site),
  Edin Mujagić + Hoofbosch (beleggingsfonds dat hij beheert).
- **planbureaus-toezicht** — 7 verbanden; nieuw: AFM. Alle planbureau-financierings- en
  directeur-dienstverband-edges (CPB/DNB/CBS/SCP/PBL) bestonden al — niet gedupliceerd.
- **commerciele-bureaus** — 8 verbanden; nieuw: Ecorys, Panteia, Decisio, Oxford Economics +
  hun **opdrachtgevers** als financier-knopen (NVDE, Netbeheer Nederland, TLN, evofenedex,
  NDP Nieuwsmedia — instanties van `denktank_financiering_bias`: belanghebbende → onderzoeksbureau).
- **werkgevers-vakbonden** — 9 verbanden; nieuw: AWVN, CNV + hun bestuurders/economen
  (Anne Megens, Raymond Puts, Piet Fortuin, Hans van den Heuvel). Tegenmacht-kant (vakbond) meegenomen.
- **universitaire-economie** — 10 verbanden; nieuw: Erasmus Universiteit Rotterdam, Nyenrode,
  **ESB** (Economisch Statistische Berichten, als vak-outlet/denktank), + hoogleraren Ivo Arnold,
  Dirk Schoenmaker, Bas Jacobs, Raymond Gradus.
- **kritische-economen (tegenmacht, verplicht)** — 12 verbanden; nieuw: Ewald Engelen, Dirk Bezemer,
  Bas Jacobs, Rens van Tilburg + **Sustainable Finance Lab**, Harald Benink, Raymond Gradus,
  Wimar Bolhuis. Hun kritische positie zit in de *claim*; het feit dát ze optreden is supporting.
- **financiering-compleet** — 11 verbanden; financier→instituut-edges voor bestaande economische
  bureaus (Rabobank→RaboResearch, ING Groep→ING Research, ABN AMRO→Group Economics, Nibud←Rijk, enz.).

## Modelleerkeuzes (conform CLAUDE.md-discipline)

- expert↔instituut = `personeel`+m118 (`denktank_levert_expert`); expert→medium = `beinvloeding`+m87
  (`expert_legitimatie`); instituut→medium = `beinvloeding`+m8 (`expert_framing`); institutioneel
  cijfer = `bron_van`+m6; financier→instituut = `financiering`+m52 (`denktank_financiering_bias`).
- **Opdrachtgever-bias** bij commerciële bureaus als financier→bureau-edge (belanghebbende → denktank),
  precies zoals NAVO→HCSS. De lobbygroepen zijn alleen *financier*, geen op-zichzelf-media-actor.
- **Granulariteit:** géén aparte economie-faculteit-knopen — `expert_legitimatie`/`denktank_levert_expert`
  grijpen op instellings-/persoonsniveau; dus instelling (Erasmus/VU) + individuele hoogleraar.
- **Draaideur-brug niet als org→org-edge:** van Geest→AFM zou samen met van Geest→CPB automatisch de
  CPB↔AFM-brug geven (geen aparte draaideur-relatie) — maar deze edge is *niet* ingediend (zie afgekeurd).
- Geen `certainty`/`influence` meegestuurd (guilty-until-proven; invloed-vloer 0,05 valt vanzelf in).

## Afgekeurd door verificatie (1)

- **Laura van Geest → AFM** (draaideur CPB→AFM, m118): attributie klopte, bron was een echt
  NOS-artikel, maar de opgegeven quote was niet strikt verbatim ("CPB-directeur" stond alleen in de
  kop, niet in de geciteerde zin). Bewust *niet* ingediend. **Follow-up:** herindienen met de
  verbatim-zin *"Centraal Planbureau-directeur Laura van Geest stapt over naar de Autoriteit
  Financiële Markten. Ze wordt daar bestuursvoorzitter."* — dan verschijnt de CPB↔AFM-brug.

## Stance-balans & tweezijdigheid

Alle 65 verbanden zijn `supporting` (dat een expert/instituut optreedt of gefinancierd wordt is een
*feit*, geen betwiste claim). Tweezijdigheid zit in de **actor-selectie**: 12 verbanden betreffen
kritische/heterodoxe economen (Engelen/Bezemer/Jacobs/Van Tilburg/Benink/Gradus/Bolhuis + SFL) en de
werkgevers-/vakbondscategorie brengt óók de vakbondskant (CNV) binnen — pluriformiteit, geen
eenzijdige pro-elite-oogst.

## Negatieve resultaten (bewijs van brede, niet-cherry-picked zoektocht)

Structureel patroon: **BNR-pagina's en eigen bankdomeinen blokkeren WebFetch (HTTP 403/503)** en
FD/Volkskrant zijn paywalled — waar een BNR-/paywall-optreden niet verbatim te staven was, is de edge
*weggelaten* (of via een wél-fetchbare, verifieerbare bron gestaafd), nooit gefabriceerd.

- **Bank-economen:** verzekeraars (NN/Achmea/ASN/Knab) hebben geen media-prominente hoofdeconoom-duider
  → niets ingediend. Wim Boonstra / Elwin de Groot (RaboResearch): geen fetchbare outletpagina met
  verbatim quote → weggelaten (RaboResearch bestaat al). Bert Colijn: naamsvermelding niet schoon
  herverifieerbaar → gedropt.
- **Planbureaus/toezicht:** **AFM/DNB worden sinds 1-1-2015 volledig door de onder toezicht staande
  sector betaald** (Wet bekostiging financieel toezicht; rijksbijdrage vervallen) — structureel zeer
  relevant, maar de financier ("de sector") is diffuus zonder entiteitsknoop → géén vage edge gemaakt;
  **verdient een aparte modelnotitie** (toezichthouder gefinancierd door wie hij controleert). Geen
  verbatim bedrag/aandeel voor CPB/CBS/SCP/PBL/DNB-financiering gevonden → `inkomensaandeel` leeg.
- **Commerciële bureaus:** Roland Berger / SEOR / Rebel Group: aanhalingen alleen in vakpers, niet in
  de gemodelleerde outlet-lijst → geen knoop (liever niets dan een zwakke edge). NDP→SEO bleek na
  verificatie een OCW-opdracht (mis-attributie vermeden). LNV→Ecorys: geen verbatim koppelzin → te zwak.
- **Universitaire economie:** geen verbatim NOS/Nieuwsuur-optreden van een Erasmus-hoogleraar gevonden;
  tweede Nyenrode-econoom naast Arnold niet vindbaar met bron. Casper de Vries overwogen, niet gestaafd.
- **Kritische economen:** BNR-optredens van Jacobs/Gradus (403) en Benink-FD-opinie (paywall) niet
  verbatim te staven → media-edge weggelaten, alleen affiliatie ingediend, of via wél-verifieerbare
  bron (Vrij Nederland-auteurspagina, Nieuwsuur-fragment). Sander Heijne (bestaat, journalist): géén
  `expert_legitimatie`-edge — hij ís mediaproducent, geen extern expert-duider (geen verkeerd mechanisme forceren).
- **Financiering-compleet:** SEO (diverse opdrachtgevers, geen isoleerbare financier) en Peil.nl
  (diffuse betalende opdrachtgevers) → geen edge. Nibud: Rijk bekostigt "ongeveer een derde", maar het
  SZW-aandeel is niet isoleerbaar → `inkomensaandeel_pct` niet gezet.

## Volledige zoekopdrachten (letterlijk, per categorie)

> Zie ook het workflow-journaal (run `wf_51cfaef6-ff6`). De verbatim query-strings per categorie:

**bank-economen:** Luc Aben hoofdeconoom Van Lanschot Kempen · Carsten Brzeski ING chief economist BNR ·
Edin Mujagić hoofdeconoom columnist Telegraaf · Han de Jong oud-hoofdeconoom ABN AMRO / Crystal Clear
Economics / Wynia's Week · Wim Boonstra RaboResearch Telegraaf column · Elwin de Groot RaboResearch ECB ·
NN Group/Achmea hoofdeconoom · Brzeski NOS Duitse economie (+ diverse site:-varianten).

**planbureaus-toezicht:** CPB jaarverslag financiering Min. EZ · AFM financiering doorberekening sector ·
DNB bankenbelasting overheidsbijdrage · Laura van Geest AFM (oud-CPB) · CBS ZBO statistiekwet · Wet
bekostiging financieel toezicht 2015 · Knot/Sleijpen/Hasekamp/Hekkert/van Oudenhoven media-optredens.

**commerciele-bureaus:** Ecorys/Panteia/Decisio/Rebel/Oxford Economics "in opdracht van" + outlet-varianten ·
Ecorys warmtenetten Netbeheer Nederland · Panteia kostenindex wegvervoer TLN/evofenedex · Decisio NDP
Nieuwsmedia NPO-advertenties · Shell "Oxford Economics" "commissioned by".

**werkgevers-vakbonden:** AWVN loonruimte cao NOS · Raymond Puts/Anne Megens AWVN · CNV Piet Fortuin/
Hans van den Heuvel koopkracht · AWVN cao-lonen FD/nu.nl · Anne Megens NPO Radio 1 zzp.

**universitaire-economie:** ESB hoofdredacteur/uitgever · Bas Jacobs VU · Ivo Arnold Nyenrode/Erasmus/ESB ·
Raymond Gradus VU · Dirk Schoenmaker RSM · + WebFetch van universiteits- en ESB-auteursprofielen.

**kritische-economen:** Ewald Engelen UvA/De Groene · Dirk Bezemer RUG/FTM · Bas Jacobs VU · Rens van
Tilburg Sustainable Finance Lab/Utrecht · Harald Benink Tilburg · Raymond Gradus VU · Wimar Bolhuis ·
+ WebFetch van UvA/RUG/VU/Tilburg-profielen, groene.nl/ftm.nl/vn.nl-auteurspagina's, uu.nl-persbericht.

**financiering-compleet:** Nibud subsidie SZW · SEO opdrachtgevers/UvA · RaboResearch⊂Rabobank ·
ING Research⊂ING Groep · ABN AMRO Group Economics · Kieskompas VU-spin-off · Ipsos I&O / Peil.nl
opdrachtgevers · hoofdeconoom-benoemingen Phlippen/Blom/van Mulligen.

## Vervolg (voor de reviewer / eigenaar)

- Review-queue: `/overleg` → *Voorstellen* + `/werkbank` (assistent). 33 knopen + 56 edges + 65
  argumenten wachten op menselijke merge.
- **RfC-signaal:** *toezichthouder gefinancierd door de sector die hij controleert* (AFM/DNB sinds 2015)
  is een structureel motief zonder passende bestaande knoop — kandidaat voor een aparte modelnotitie of
  een diffuse-financier-modellering.
- **Near-miss:** van Geest→AFM herindienen met de verbatim-zin → CPB↔AFM-draaideurbrug.
