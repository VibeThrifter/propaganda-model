# Monetisatie & agent-native herinrichting van het propaganda-model

*Compleet, zelfstandig leesbaar plan — juli 2026.*

---

## 1. Context

Het project is een volwassen, zwaar-gesourcete kennisgraaf van de Nederlandse media-machtsstructuur,
gebouwd op Herman & Chomsky's propagandamodel. Doel van dit plan: het project **monetiseren** en daarbij
de multi-user community-opzet verlaten ten gunste van een **solo + agents**-machine die grotendeels
onbewaakt draait.

**Drie richtingsbesluiten zijn genomen (zie §6):** gefaseerd met het portal eerst; alles publiek /
maximale dekking; en auto-merge aan.

**Bedoelde uitkomst:** een zelfdraaiende, agent-gevoede, juridisch-verdedigbare
media-transparantie-machine met een publiek, adverteerbaar SEO-portal als eerste inkomstenbron, een
data-feed als opt-in tweede bron, en een epistemisch proces dat vertrouwen haalt uit bron-verificatie,
tegenspraak en kalibratie in plaats van uit menselijke consensus.

---

## 2. De assets (wat er écht is)

**Content — de kennisgraaf (live DB, 9 MB SQLite):**

| Asset | Omvang |
|---|---|
| Entiteiten | 1.115 |
| Relaties | 1.973 (1.938 met mechanisme) |
| Argumenten | 3.386 (94% met een citaat, 92% quote-niveau) |
| Bronnen | 2.121 (99% met locator; **slechts 3% Wayback-gearchiveerd**) |
| Citaties | 3.656 |

Rijkste sub-assets: **831 gedateerde persoon↔org-banden** (draaideur-/netwerkgraaf — de kroonjuweel,
hoogste moat), 439 politieke-positie-signalen over 308 entiteiten, 175 financieringsedges, 149
eigendomsedges, 270 bereikcijfers over de tijd, welstandsklassen, inkomenssamenstelling. 13
voorspellingen — **0 opgelost** (nog geen bewijskracht).

**Motor — de infrastructuur:** ~80–85% domein-onafhankelijk. Het "propagandamodel" zit als *data* in
tabellen, niet in de logica. `scoring.py` is ~95% generieke pure functies. De collectie-laag
(LinkedIn → gedateerde persoon→org-banden → afgeleide bruggen) is al de juiste vorm voor een
due-diligence/transparantie-product. ~45 van de ~85 endpoints zijn puur multi-mens-coördinatie.

**De flessenhals:** het is nu géén zelfdraaiende machine. `maxime` merget álles handmatig (2.449 merges),
wachtrij ~640 voorstellen; de "autonome" agents draaiden nauwelijks onbewaakt (84% is
eigenaar-gesuperviseerde `assistent`-sessies).

---

## 3. De drie oorspronkelijke ideeën, eerlijk gewogen

- **Idee 2 (monitoring-SaaS) — afgeraden als hoofdroute.** Tegelijk het verst weg (geen ingestion-/
  alertloop; "wat verandert er" = *modelbewerkingen*, niet gebeurtenissen in de media — die motor bouw je
  from scratch) én het slechtst passend bij "geen menselijke factor": B2B-SaaS is juist het meest
  contact-intensieve model (sales/demo/onboarding/support), markt met Meltwater/Cision/Coosto.
- **Idee 1 (data-feed) — technisch het dichtst bij klaar** (`/api/graph_data` + 7 metriek-endpoints zijn
  al schone, open JSON; `releases/` is al een versie-mechanisme), maar de kopersmarkt voor een
  Nederlandstalige media-machtsgraaf is klein en licentieverkoop kost tóch acquisitie. → Tweede,
  opportunistische stroom (§Deel E), niet het anker. Verkoop de netwerk/eigendom/geldstroom-laag, niet
  de politieke-positie-laag.
- **Idee 3 (publiek portal + advertenties) — beste match met de randvoorwaarden.** Al een open publieke
  site; nul klantcontact; passief; speelt naar de bouw-hyperfocus; onderwerp met natuurlijk publiek en
  deelbare haakjes. Bouw is *medium* (crawlbare per-entiteit-pagina's ontbreken), opbrengst *bescheiden
  maar echt* en traag opbouwend. → **Het anker (Fase 1).**

---

## 4. Strategische herkadering

- **Twee scheidbare assets:** de *content* (NL-media-graaf) en de *motor* (herbruikbaar). Monetiseer
  eerst de content via het portal; hou motor-hergebruik als Fase 2-optie.
- **Rebrand de publieke voorkant** weg van "Propagandamodel — Nederlandse Politiek & Media" naar een
  neutrale media-transparantie-naam ("wie bezit de Nederlandse media — eigendom, geldstromen & netwerk,
  gesourcet"). Het propagandamodel wordt de *methodologie*-pagina, niet de voordeur. Reden: het frame is
  een onderzoeks-deugd maar een commerciële last (schrikt adverteerders af, juridisch spannender).
- **Eerlijke omzetverwachting:** het portal is bescheiden en traag (NL-niche, lage advertentie-RPM, SEO
  6–18 mnd). De data-feed is lumpig. Het echte plafond zit in de motor-op-een-commercieel-domein
  (Deel E2) — bewust nu geparkeerd.

---

## 5. De motor is herbruikbaar (repoint-punchlist, voor Deel E2)

Geen herbouw, wél een reseed + reconfigure: seed nieuwe rollen/mechanismen (data); edit de
CHECK-enum-vocabulaires in `schema.sql`; ~4 constant-tuples (`server.py:823`, `voorstellen.py:58–63`,
`tegenmacht.py:45`); de influence-sinks (`influence.py:67,290`); herconfigureer de collectie-mapper +
herschrijf de `missies/*.md`-prose. De argumentatie/bewijs/interval-wiskunde, graaf-centraliteit,
REST/CRUD, auth, viz-assemblage en agent+scraper-ingestie dragen ongewijzigd over.

---

## 6. De drie genomen besluiten

1. **Gefaseerd, portal eerst.** Eerst passief verdienen aan wat er al is; daarna feed en/of tweede domein.
2. **Alles publiek, maximale dekking** — inclusief persoon-niveau politieke posities. Uitgevoerd als de
   *meest verdedigbare* versie (§Deel Juridisch), niet afgezwakt.
3. **Auto-merge aan** — de handmatige merge-flessenhals wordt vervangen door een geautomatiseerde,
   geverifieerde merge-poort met de mens op de uitzonderingen.

---

## Deel A — Epistemische herinrichting voor een agent-native systeem (de ruggengraat)

*Antwoord op "is de argumentenboom ook goed voor agents, of kan het beter?": hou de boom — die past zelfs
beter bij agents dan bij de mensen-community waarvoor 'ie is gebouwd — maar draai het vertrouwensmodel om.*

De boom is maar een *datastructuur*. De vraag is welk *epistemisch proces* 'm vult. Voor mensen kwam
vertrouwen uit **diverse mensen die het eens worden** (bridging/rating, Community-Notes-stijl). Bij agents
stort die aanname in: tien Claude-agents die het eens zijn is geen tien onafhankelijke bevestigingen —
ze delen training, priors én blinde vlekken. **Agreement-counting bij agents is nep-bewijs.** Haal
vertrouwen daarom uit drie dingen die agents wél betrouwbaar kunnen en die mensen nooit opschaalden:

- **A1 — Onafhankelijke bron-herverificatie (nieuwe verplichte fase).** Elke `voorgesteld`
  supporting/contradicting root wordt her-geverifieerd door een *andere* agent dan de indiener: haal de
  bron (+ archiefkopie) opnieuw op, check dat de quote **verbatim** matcht en dat 'ie de claim steunt.
  Gestructureerd verdict (`klopt/twijfel/klopt-niet`, mirror van `missies/reviewbeoordelaar_brief.md`).
  Dit is de agent-vervanger van menselijke review: niet "vindt een mens dit ook", maar "bevestigt een
  blinde tweede agent het tegen de echte bron".
- **A2 — Verplichte tegenspraak (red team als lopende band, niet optioneel).** Agents die "zoek
  steunbewijs" krijgen, produceren een confirmatie-cascade. Elke claim passeert een 'aanklager'-agent
  (andere rol/prompt, liefst ander modelfamilie, blind voor de steun-redenering) die een tegenbron zoekt,
  de inferentie aanvalt, of certificeert dat 'ie de aanval overleefde. Alleen wat overleeft stijgt in
  vertrouwen. De boom ondersteunt dit al (ondergraving dempt parent, M1.1/M1.4); het *proces* moet het
  garanderen. Bouwt voort op de red-team-rol in `missies/monitor_brief.md` — nu occasioneel, wordt
  conveyor-belt.
- **A3 — Schrap de mens-diversiteit-laag.** `bridging.py`, `argument_ratings`, `kalibratie_agents.py`,
  `scripts/bridging.py` en de nuttig/ondergraving-ratings — zinloos zonder diverse mensenpool en bij n=1
  al inert. `scoring.py` `bridged_weights` valt terug op neutrale 1.0.
- **A4 — Voorspellingsregister als hoeksteen (self-resolving kalibratie-motor).** Nu 13 voorspellingen,
  0 opgelost = belofte, geen bewijs. Maak er een doorlopende motor van: agents registreren falsifieerbare
  voorspellingen (`POST /api/predictions`), een scheduler resolvet ze op hun deadline, Brier-score wordt
  bijgehouden (`scripts/voorspellingen.py` bestaat al). Het enige externe, onomkoopbare ijkpunt én het
  externe verkoopverhaal ("gekalibreerd model, Brier X").
- **A5 — Provenance-methode-tier (voor scraping).** Naast `reliability`/`onderwerp` een *methode*-
  dimensie op citaties/bronnen: `verbatim_quote` (sterk) > `officieel_register_scrape` (KvK/jaarverslag,
  medium) > `llm_samenvatting_van_pagina` (zwak). `scoring.py` `bronfactor` weegt scraped data eerlijk
  lager, zodat een volume-scrape zich niet voordoet als hard bewijs.
- **A6 — Semantische dedup.** De difflib-dedup op roots (`server.py`) aanvullen met embedding-match, zodat
  bijna-duplicaten niet "veel bewijs" faken. Belangrijker naarmate scraping opschaalt.
- **A7 — De auto-merge-poort = A1 ∧ A2 ∧ A6 ∧ citatiepoort.** Een root auto-merget alleen als:
  citatiepoort gehaald (`_echte_citatie`) **+** quote onafhankelijk geverifieerd (A1) **+** aanval
  overleefd (A2) **+** geen semantisch duplicaat (A6) **+** jury-confidence hoog. Anders → steekproef-/
  uitzonderingswachtrij. Hergebruikt `merge_argument` (`server.py:1508`) onder een reviewer-tier
  *systeemaccount*; theorie-laag (RfC) blijft mens. Expliciet documenteren: auto-merge verdunt
  provenance-zuiverheid, dus beperkt tot citatie-gepoorte, jury-goedgekeurde, niet-theorie claims +
  volledige `edit_log`-audit + eigenaars-veto.
- **A8 (optioneel, later) — DF-QuAD → likelihood-ratio's.** Evolueer de heuristische aggregatie naar
  expliciete P(bewijs|claim waar) vs P(bewijs|claim onwaar) per bewijsstuk, zodat confidence koppelt aan
  de Brier-lus (A4). Zelfde knopen, betere wiskunde; `scoring.py` is ~95% pure functies, dus de
  aggregatiefunctie is inwisselbaar zonder herbouw.

> **Rode draad:** hoe meer je mensen wegtrekt en scraping opschaalt, hoe harder je dit immuunsysteem
> nodig hebt — één kapotte scraper vergiftigt duizenden rijen.

---

## Deel B — Monetisatie-surface: het portal (Fase 1)

- **B1 — Deploy/hosting (nu afwezig).** `gunicorn` + `systemd`-unit of `Dockerfile`, achter Caddy/nginx
  met HTTPS op een goedkope VPS. Prerequisite voor alles.
- **B2 — Rebrand publieke voorkant.** Nieuwe `<title>`/meta/merk in `web/template.html` +
  `web/huisstijl.css`/`web/huisstijl.js`; propagandamodel wordt methodologie-pagina.
- **B3 — Publiek/privé-splitsing.** Redactie-/agent-werkbank (`/overleg`, `/beheer`, `/werkbank`,
  `/login`, `/account` — nu via `send_file`, `server.py:201–239`) achter een `require_user`-gate
  (`server.py:176`) of interne poort/subdomein. Publieke leessurface (`/`, per-entiteit-pagina's,
  `GET /api/graph_data`) blijft open.
- **B4 — Programmatic-SEO-pagina's (de eigenlijke SEO-motor; "medium" bouw).** Eén crawlbare pagina per
  entiteit/persoon/mechanisme/relatie met unieke `<title>`/meta/canonical/OG/H1, server-gerenderde prose,
  interne links, `sitemap.xml` + `robots.txt`. De per-entiteit *data* bestaat al in
  `viz_data.export_data()` (`viz_data.py:45–397`); de render-*logica* zit als JS in `template.html` en
  moet naar SSR-routes (`/entiteit/<slug>`, `/persoon/<slug>`, `/mechanisme/<slug>`) of een
  static-generator (uitbreiding van `scripts/generate_viz.py`, dat nu alleen één 9.9 MB-bundel bakt).
  Voeg stabiele slugs toe (nu alleen hash-deeplinks `#sel=entity:42`).
- **B5 — Content-diepte via AI-prose.** Per pagina een korte natuurlijke-taal-samenvatting uit de
  relaties/scores (LLM-stap op genereer-tijd, gecachet) — zet de graaf om in leesbare, indexeerbare copy
  die Google's helpful-content-updates belonen i.p.v. straffen. Hier zijn AI-tokens goed besteed.
- **B6 — Advertentie/affiliate.** Ad-slots in het pagina-template (start AdSense/Google Ad Manager, groei
  naar Ezoic/Mediavine bij volume). De interactieve viz blijft het vlaggenschip; de per-entiteit-pagina's
  zijn de SEO-longtail die er verkeer naartoe voert.

---

## Deel C — Zelfdraaiende machine (autonomie)

- **C1 — Geplande onbewaakte agent-runs.** Missie-agents (scout/monitor/documentalist/ideoloog/doelgroep/
  bereik/linkedin, `missies/*.md`) schedulen (cron/systemd-timers of de `schedule`/`loop`-harness) onder
  hun eigen tokens. Spend = AI-tokens.
- **C2 — De auto-merge-service.** Achtergrond-loop over de `voorgesteld`-wachtrij die A7 uitvoert.
- **C3 — Wayback-archivering wordt dragend.** `scripts/archiveer_bronnen.py --save` op schema — nu 3%
  gearchiveerd; A1-verificatie én de "linkrot-vrij"-claim vereisen een onveranderlijke kopie.
- **C4 — Eigenaarsrol verschuift.** Van "alles mergen" (flessenhals) naar kalibratie-toezicht: steekproef
  van auto-merges, door jury/aanklager gevlagde twijfel-/hoog-inzet-items, voorspellingen resolven,
  drempels tunen. Mens op de meta-laag, niet de doorvoer — dít is "nauwelijks mensen in de loop" goed
  gedaan.

---

## Deel D — Community-machinerie afbouwen, bijdrage openhouden (solo + agents)

Ná Fase 1–2 (niet destabiliseren tijdens de geld-bouw). **Kernonderscheid:** weg met de multi-mens
*governance* (consensus, onderhandeling, moderatie-arbeid), maar de *bijdrage-intake blijft open* — voor
**onbetrouwbare voorstellers**, niet mede-bestuurders. Deel A ontpersoonlijkt vertrouwen (bron-
herverificatie + tegenspraak i.p.v. "wie is het eens"), dus je kunt de voordeur juist wíjder openzetten
omdat je de deur niet meer vertrouwt: elke inzending — agent of vreemde — moet dezelfde loopgraaf door.

### D1 — Wat gaat / wat blijft

- **Weg:** multi-user account-beheer vóór vreemden (`server.py:337–503`), de RfC-twee-akkoorden-governance
  (`voorstellen.py`, ~1080 regels → eigenaar-beslist), ratings/bridging/watchlists (A3), de menselijke
  review-queue-als-sociale-ruimte (vervangen door A7-auto-merge + uitzonderingswachtrij).
  `web/overleg.html`/`web/beheer.html` verdwijnen als *publieke* surface maar **blijven als privé
  redactie-tool** achter de B3-gate.
- **Blijft:** alle CRUD; de score/influence/viz-motor; sources/citations/argumentenboom-discipline (de
  moat); één eigenaar-account + agent-tokens; `edit_log` (audit); `lineage` (versionering); predictions;
  **en een dunne, niet-interactieve publieke bijdrage-intake (D2).**

### D2 — De publieke intake: open, niet-interactief, misbruikbestendig

Ontwerpregel: **een publieke inzending is een *tip/lead*, geen *claim*.** Ze schrijft nooit rechtstreeks
in de bewijs-structuur. Ze landt in een aparte, lager-vertrouwde baan (`herkomst='publiek'`), telt in
niets, en is **standaard uitgesloten van auto-merge**. Een *agent* pikt de lead op en doet z'n eigen
onafhankelijke sourcing (A1: bron ophalen, quote verbatim checken); pas als dat klopt maakt de *agent* het
echte `voorgesteld` argument onder z'n eigen account, dat dan de normale A1/A2/A7-pijplijn in gaat. Het
publiek mag dus *wijzen*, alleen geverifieerde her-afleiding *telt*. Dat neutraliseert in één klap
gefabriceerde bronnen, sock-puppets én prompt-injectie: de agent leidt alles vers af en de publieke tekst
is nooit bewijs, alleen een pointer.

Verdediging in lagen — **goedkope filters strikt vóór dure** (nooit een verificatie-token aan iets besteden
dat een regel/rate-limit had kunnen droppen; A1/A2 kosten echt geld per claim, dus een junk-flood is een
*denial-of-wallet*-aanval op het tokenbudget):

- **Laag 0 — kosteloze poort (vóór de wachtrij, vóór elke agent).** Cloudflare Turnstile of proof-of-work
  op het formulier (gratis, geen PII, past bij niet-interactief) + honeypot-velden + tijd-heuristiek
  (formulier < 2 s ingevuld = bot). Strak per-IP/per-sessie rate-limit op de *publieke* intake — veel
  strakker dan de agent-limieten (handvol per uur/dag; hergebruik `server.py:79–97`). Bron-URL langs een
  spam-domein-blocklist; velden gemaximeerd op lengte, HTML/script gestript (geen stored-XSS, schone
  wachtrij). De citatiepoort geldt al: een link-spam-inzending zónder verifieerbare locator/quote komt niet
  eens als supporting root binnen.
- **Laag 1 — lead-quarantaine (de structurele isolatie hierboven).** Publiek = aparte baan, telt in niets,
  nooit auto-merge, agent-corroboratie verplicht. 1000 sock-puppets die dezelfde lead pushen vallen samen
  tot één agent-geverifieerde claim (of nul): agreement-counting onder indieners is per ontwerp waardeloos
  — dezelfde regel als "agreement onder agents is nep-bewijs", nu op het publiek toegepast. Volume kan geen
  consensus fabriceren, want consensus verdient hier geen vertrouwen.
- **Laag 2 — immuunsysteem (A1/A2), gehard tegen injectie.** Verificatie-agents behandelen ingezonden
  tekst én opgehaalde brontekst als **data, nooit als instructie** (afgebakend; het systeem-prompt stelt
  dat expliciet); het verdict is *gestructureerd* (`klopt/twijfel/klopt-niet` + verbatim span), niet vrije
  tekst, wat de injectie-hefboom wegneemt. Circulaire-bron-check: A5 downweegt zelf-gepubliceerde/lage-
  autoriteit bronnen al; expliciet weigeren dat de bron het eigen domein van de indiener of een
  vers-geregistreerde site is. Buitengewone claims over een *genoemd persoon* vergen een onafhankelijke,
  autoritatieve bron — een lage-`reliability`-bron tilt een persoons-claim nooit over de auto-merge-lat.
- **Laag 3 — de smaad-firewall (niet-onderhandelbaar).** Elke inzending met een **negatieve feitelijke
  claim over een genoemd natuurlijk persoon** (niet een organisatie) wordt **nooit** auto-gemerged en
  **nooit** publiek gerenderd zonder eigenaars-akkoord — hoe schoon de bron ook is. Hoogste ernst, laagste
  volume: goedkoop om hard dicht te zetten. De neutraliteitsregels (gesourcete feiten + geattribueerde
  meningen, nooit een eigen beschuldiging) gelden a fortiori; de agent die een lead tot claim herschrijft,
  wast 'm door diezelfde discipline.
- **Laag 4 — vangnet, continu.** De rectificatieflow (art. 16/21) ís dezelfde widget ("meld onjuistheid /
  stel bron voor" = één intake). Anomalie-monitoring: alarm bij bursts (piek over één entiteit / uit één
  IP-range / één narratief-richting) → voedt C4 (eigenaar-toezicht); als `validation.py`-check. Niets wordt
  verwijderd (bestaande discipline): geweigerde tips krijgen een statusvlag + `edit_log`, dus patronen zijn
  auditeerbaar en een herhaal-misbruiker is retroactief te blocklisten.

**Token-budget-grens (dwars door alles):** geen agent-token wordt aan een publieke inzending besteed vóór
ze Laag 0 (gratis filters) + Laag 1 (welgevormde, niet-duplicate lead met resolvbare, niet-geblokte bron)
haalt. Publieke leads staan achter de agent-pijplijnen in de wachtrij, gedekt door een dag-plafond op
verificatie-spend, zodat een flood het echte werk niet kan uithongeren.

Alles blijft **eenrichting**: CAPTCHA, rate-limit, blocklist, lead-quarantaine, agent-corroboratie,
eigenaars-veto en rectificatie-intake vergen geen enkel *gesprek* met de indiener. Precies de menselijke
factor die je wilde elimineren — de bijdrage blijft, het onderhandelen erover niet.

---

## Deel E — Optioneel: tweede inkomstenbron & tweede domein (Fase 2)

- **E1 — Data-feed.** Formaliseer `releases/` (nu 1 verouderde snapshot) tot een gedocumenteerd,
  geversioneerd, licentieerbaar dataproduct: schema/data-dictionary, CSV/Parquet-export van de
  netwerk/eigendom/geldstroom-tabellen (de veilige, verkoopbare slice), een cadans, OpenAPI-doc tegen de
  stabiele `/api/*`-vormen, API-key-gating + lees-metering (hergebruik het write-side rate-limit-patroon,
  `server.py:79–97`). Doelgroep: onderzoekers/journalisten/AI-grounding.
- **E2 — Motor op een commercieel sterker domein (het echte plafond).** Repoint-punchlist in §5.
  Kandidaat-domeinen met échte kopers: bedrijfs-eigendom/lobby/due-diligence-transparantie.

---

## Juridische inrichting (gegeven "alles publiek")

Geen afzwakking van de dekking — wél de competente, verdedigbare uitvoering ervan:
- **Opereer als journalistiek/onderzoek (UAVG art. 43-exemptie).** Neutraal, gesourcet, publiek-belang;
  geen eigen waardeoordeel (het model dwingt dit al af — houden als harde productregel). Hoofdschild voor
  het publiceren van art. 9-data (politieke posities per persoon).
- **Prominente rectificatie-/verwijderflow (AVG art. 16/21).** Per pagina een "feitelijke onjuistheid
  melden / bezwaar maken"-contact + gedocumenteerd proces. Grootste risico-reductie voor de laagste
  kosten. **Dit is dezelfde niet-interactieve intake-widget als de publieke bijdrage (Deel D2):** melden
  en bijdragen delen één eenrichtings-wachtrij.
- **Smaad/onrechtmatige daad staat los van AVG en geldt altijd.** Publiceer gesourcete feiten en
  geattribueerde meningen, nooit een eigen beschuldiging. De neutraliteitsregels dekken dit — bewaken.
  Voor publieke inzendingen is het mechanisch afgedwongen door de smaad-firewall (Deel D2, Laag 3):
  negatieve claims over genoemde personen mergen nooit automatisch en renderen nooit zonder eigenaars-akkoord.
- **Scraping: gericht, geen bulk** (de enige plek waar ik binnen "max dekking" de lijn hou). Bulk-
  LinkedIn/proxy-scraping is onevenredig risico (ToS, account-ban, AVG) voor weinig SEO-winst; de
  bestaande mapper is bewust gericht/rate-limited (`tools/linkedin/`). Focus op KvK, jaarverslagen,
  publieke registers, nieuws.

---

## Investering & hosting right-sizing

Géén "krachtige thuisserver" (DB = 9 MB; goedkope VPS draait alles). De echte uitgave is **AI-tokens voor
agent-doorvoer + verificatie** (A1/A2 verdubbelen het tokengebruik per claim — bewust, dat is de
kwaliteitskost). Kleine posten: VPS + CDN + backups + domeinnaam. 24/7 residentiële-proxy-scraping:
niet nodig, hoog risico — overslaan.

---

## Fasering / roadmap (aanbevolen volgorde)

1. **Fundament:** B1 (deploy) + B2 (rebrand) + B3 (publiek/privé-split) + C3 (archivering aanzetten).
2. **Immuunsysteem:** A1 + A2 + A5 + A6 (verificatie, tegenspraak, provenance-tier, dedup) — vóór
   auto-merge, want auto-merge zonder immuunsysteem schaalt fouten op.
3. **Autonomie:** A7 + C1 + C2 (auto-merge-poort + geplande runs) + A4/C4 (kalibratie-motor + eigenaar als
   toezichthouder).
4. **Monetiseren:** B4 + B5 + B6 (SEO-pagina's + AI-prose + advertenties). Verkeer bouwt 6–18 mnd op.
5. **Opruimen & openhouden:** Deel D — governance afbouwen (D1) én de misbruikbestendige publieke intake
   (D2) bouwen als vervanger (lead-quarantaine + Laag 0–4 + smaad-firewall). Niet louter slopen: de
   bijdrage blijft, alleen ontpersoonlijkt en eenrichting.
6. **Optioneel later:** E1 (feed) en/of E2 (tweede domein), A8 (Bayesiaanse score-evolutie).

---

## Kritieke bestanden

- **Motor (blijft, evolueert):** `scoring.py` (A5/A7/A8), `influence.py`, `viz_data.py` (B4-databron),
  `validation.py` (consistentie-checks/immuunsysteem), `server.py` (auth-gate B3, merge/citatiepoort A7
  rond `:1508`/`:176`, feed-gating E1).
- **Nieuw:** verificatie-agent-service (A1, mirror van `missies/reviewbeoordelaar_brief.md`),
  aanklager-agent-brief (A2, uit `missies/monitor_brief.md`), auto-merge-loop (A7/C2), SSR/static
  per-entiteit-generator (B4, uit `scripts/generate_viz.py`), deploy-config (B1).
- **Weg / privé (Deel D1):** `voorstellen.py` (RfC-governance), `scripts/bridging.py`,
  `scripts/kalibratie_agents.py`, ratings/watchlist/review-queue-endpoints; `web/overleg.html`/
  `web/beheer.html` verhuizen van publiek naar privé (achter B3), niet verwijderd.
- **Nieuw (Deel D2 — publieke intake):** publiek bijdrage-/rectificatie-endpoint (eenrichting) + de
  `herkomst='publiek'` lead-quarantaine-baan; Laag 0-poort (Cloudflare Turnstile/proof-of-work + honeypot +
  strak rate-limit op het `server.py:79–97`-patroon + spam-domein-blocklist + HTML-strip); anomalie-burst-
  check in `validation.py`; agent-brief "corroboreer publieke lead" (afgeleide van A1-verificatie).
- **Agent-briefs:** `missies/*.md` (herschrijven voor onbewaakte cadans C1) + `missies/README.md`.

---

## Verificatie (end-to-end)

- **A1–A2 immuunsysteem:** dien via de REST-API (account `assistent`) een bewust *fout* argument in
  (verkeerde quote) → verificatie-agent geeft 'klopt-niet', auto-merge weigert; dien een correct gesourcet
  argument in → verifieert, overleeft de aanval, auto-merget. Log in `missies/logs/`.
- **A7 auto-merge:** `python3 scripts/test_scoring.py` (golden snapshot mag alleen bewust wijzigen) +
  `python3 scripts/validate_model.py --strict`. Nieuwe test `scripts/test_auto_merge.py`
  (poort = citatie ∧ verificatie ∧ geen-duplicaat).
- **A4 kalibratie:** `python3 scripts/voorspellingen.py` → registeroverzicht + Brier; resolveer een
  test-voorspelling, controleer de Brier-update.
- **D2 misbruikbestendigheid (nieuwe `scripts/test_publieke_intake.py`):** een bot-flood botst op Laag 0
  (rate-limit/Turnstile/honeypot, 0 tokens besteed); een lead met gefabriceerde quote overleeft
  agent-corroboratie niet (Laag 1–2); een prompt-injectie in het quote-veld verandert het gestructureerde
  verdict niet (Laag 2); een negatieve claim over een genoemd persoon komt nooit door auto-merge en rendert
  niet zonder eigenaars-akkoord (Laag 3); een burst over één entiteit vlagt de anomalie-check (Laag 4).
- **B3/B4 portal:** start `python3 server.py`; `/overleg`/`/beheer` geven 401/redirect, `/` +
  `/entiteit/<slug>` zijn publiek met unieke `<title>`/meta; valideer `sitemap.xml` en één
  per-entiteit-pagina in een crawler / Google Rich Results.
- **Regressie/attributie:** `python3 scripts/test_fresh_build.py` en `python3 scripts/test_auth_smoke.py`
  na Deel D-sloop; `validate_model.py --strict` als CI-gate op elke stap.

---

## Open beslissingen (voor later)

- Merknaam/domein voor de publieke voorkant.
- Advertentienetwerk-keuze en drempels (AdSense → Ezoic → Mediavine).
- Wel/niet een tweede modelfamilie inzetten als onafhankelijke jury (A2/A7) — kost extra, koopt echte
  decorrelatie.
- Publieke intake (Deel D2): volledig anoniem/no-login vs. lichtgewicht wegwerp-identiteit, en Turnstile
  vs. proof-of-work als Laag 0-challenge — afweging tussen drempel-hoogte en frictie/PII.
- Timing en domeinkeuze voor E2 (motor-hergebruik) — het grootste omzetplafond, grootste bouw.
