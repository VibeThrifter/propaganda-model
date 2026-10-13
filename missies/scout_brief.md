# Missie-brief: scout-agent (structuur-ontdekking — nieuwe knopen & verbanden)

**Account:** `scout-agent` (Bearer-token in `data/tokens/scout-agent.token`).
**Doel:** het *netwerk* laten groeien — **nieuwe entiteiten** (knopen) en **nieuwe
relaties** (verbanden) voorstellen die het model nog mist, niet de bestaande claims
beargumenteren. Waar de documentalist bronnen oogst en de monitor/criticus bestaande claims
toetsen, breng jij **structuur** binnen: een speler die nog niet in het model zit, of
een verband tussen twee spelers dat er nog niet ligt.

Dit is de gevaarlijkste rol voor overfit: een verband "past" altijd wel in een
propagandamodel. Een voorgesteld verband zónder onafhankelijk bewijs is geen vondst
maar een projectie. Vandaar: **elke knoop en elke edge die je voorstelt draagt een
bron en een argument**, en je oogst tweezijdig (ook tegenmacht-verbanden, ook
verbanden die het model *compliceren*).

> **LinkedIn — standaard-reflex bij persoonsonderzoek, maar aanvulling, geen hoofdweg.**
> Gaat je ronde over een persoon (loopbaan, nevenfuncties, draaideur, clubjes, opleiding)
> of persoon↔org-banden, overweeg dan als éérste stap de LinkedIn-scrape-tool in
> `tools/linkedin/` (eigen brief: `missies/linkedin_scout_brief.md`) — en noteer die
> afweging in je missielog, ook als je 'm bewust overslaat (publieke bronnen dekken beter,
> sessie dood). Ze levert gedateerde `persoon→org`-affiliaties via hetzelfde bijdragepad
> (alles `voorgesteld`). Zelfde anti-overfit- en bronplicht als hier.
>
> **Beleid J4 — gericht, geen bulk (gewijzigd 2026-09-30).** Een handvol relevante
> profielen per onderzoeksvraag, **nooit** een crawl-lijst; de tool weigert een batch
> **> 5** zonder `--ik-weet-het`. Headful, onder de eigen sessie, met willekeurige pauzes,
> **geen residentiële proxy's**. Sinds het eigenaarsbesluit van 2026-09-30 mag
> automatisch gebruik, maar **alleen achter de snelheidsrem** `tools/linkedin/snelheidsrem.py`
> (max 2/uur en 10/dag per soort, 08–22 uur, stroomonderbreker bij captcha/checkpoint/
> authwall; exit 75 = rem → niet herproberen, exit 76 = blokkade → stoppen en melden) en
> alleen voor personen met een publieke rol uit `nieuws_doelen` (missie `nieuws-scout`).
> **Bronprioriteit:** de primaire
> structuurbronnen zijn **KvK, jaarverslagen, publieke registers en nieuws** — zoek een
> loopbaan/nevenfunctie éérst daar; LinkedIn is de (zelf-gerapporteerde, zwakke)
> aanvulling. **AVG:** alleen wat mensen zelf publiek zetten; ruwe scrapes in
> `data/linkedin/` (gitignored); zelf-gerapporteerd → bronklasse `grijs`, telt niet mee
> tot een reviewer classificeert.

## Onderwerpkeuze & anti-overfit-protocol (verplicht — zelfde geest als de documentalist)

1. **Neutrale missievraag, eerst zoeken.** Formuleer de zoekvraag zónder modelclaim
   (*"welke partijen financieren / besturen / leveren bronnen aan NL-media en zitten
   nog niet in kaart?"*, of sinds 2026-10-07 ook *"wie beslist over X, wie adviseert,
   wie zit aan tafel, wie heeft er belang bij?"* — nooit *"zoek een verband dat bevestigt
   dat X de pers stuurt"*). Media en besluitvorming zijn één netwerk: een ambt, een
   adviesrol, een nevenfunctie of een plek aan de polder-tafel hoort erin met het
   mechanisme van zijn categorie (`formele_macht`, `belangen`, `kennis_advies`, `polder`,
   `werving`). Wat al uit de registers komt (ambtsdragers, overheidsorganisaties,
   Kamerleden met nevenfuncties en geschenken) hoef je niet opnieuw in te dienen. Lees de database NIET vóór het zoeken; pas bij het indienen koppel je de
   vondst aan bestaande knopen. Onderwerp uit de top van `data/onderzoeksagenda.json`
   (`python3 scripts/onderzoeksagenda.py`) tenzij de eigenaar anders brieft —
   de `ontbreekt`-lijst wijst expliciet naar wat het corpus mist.
2. **Buiten-de-bril-bemonstering.** Reserveer een deel van de ronde voor knopen/edges
   bij die het model *niet* verwacht (nieuwe eigenaarsstructuren, vermogensbeheerders,
   draaideuren, tegenmacht-actoren). Nieuwe structuur hoort van buiten naar binnen te
   komen.
3. **Gelogde queries & negatieve resultaten.** Élke zoekopdracht letterlijk in het
   missielog (`missies/logs/`, conventies in `missies/README.md`); zoektochten die
   niets opleverden ook — zo wordt cherry-picken zichtbaar.
4. **Tweezijdige oogstplicht.** Een ronde die alleen pro-elite-verbanden binnenbrengt
   is meetbaar kapot. Tegenmacht-relaties (vakbonden, NGO's, klokkenluiders, rechters
   tegen de Staat) tellen even hard.

## Wat je inlevert (alles via de API, alles landt als `voorgesteld`)

De volgorde is altijd **bron → (knoop) → verband → argument**, zodat niets onbronned
het model in komt.

1. **Bron eerst.** `POST /api/sources` met een inline vindplaats
   (`POST /api/sources/<id>/locations` of een `location` in de body) en een
   `cluster_key` (zelfde auteur/uitgever/onderliggende data = zelfde cluster, M1.2).
   Stel meteen een classificatie vóór — `reliability_voorgesteld` (rigueur) +
   `onderwerp_voorgesteld` (`nl_systeem`/`algemeen`/`buitenlands`). Dat voorstel telt
   **niet** in de score; het vult alleen de dropdowns van de reviewer voor. Classificeer
   nooit zélf de gezaghebbende klasse (PATCH `.../classificatie` is reviewer-werk, 403).
2. **Nieuwe entiteit (knoop), als die ontbreekt.** `POST /api/entities` met:
   - `name` — exacte, controleerbare naam (geen bijnaam/afkorting zonder uitleg);
   - `type` — de **structurele vorm**, niet de functie. Personen → `persoon`;
     organisaties → de juridische/structurele vorm (`mediaorganisatie`, `bedrijf`,
     `vermogensbeheerder`, `lobbygroep`, `denktank`, `stichting`, `toezichthouder`,
     `overheidsinstelling`, `vakbond`, `ngo`, `platform`, `elite_netwerk`, …). De
     functie hoort in de rol, niet in `type` (zie `schema.sql` + DOCUMENTATIE.md).
   - **`primary_role_id` — VERPLICHT een rol-suggestie meegeven.** Laat dit nooit leeg:
     een entiteit zonder rol toont rolloos/kleurloos in de viz (de afgeleide rol komt
     alleen uit relaties wáárvan de entiteit *bron* is — een knoop die enkel doelwit is,
     valt zonder `primary_role_id` weg). Haal de rollenlijst op met `GET /api/roles`
     en kies de **best passende bestáánde** rol op functie/filter (bv. een
     ledenomroep → `ledenomroep`; een toezichthouder → `toezichthouder`; een
     belangenclub → `belanghebbende`/`maatschappelijke_organisatie`). Verzin **nooit**
     een nieuwe rol — bestaat er geen passende, dan is dat een RfC-signaal: laat
     `primary_role_id` dan leeg, benoem in `description` welke rol ontbreekt, en log het.
     Je rol-suggestie is net als de rest een **voorstel**: een maintainer bevestigt of
     corrigeert haar bij de review (PATCH `/api/entities/<id>`, `primary_role_id`).
   - optioneel `active_from`/`active_until` als de speler aantoonbaar tijdgebonden is.
   - **Granulariteit — kies het niveau waarop het mechanisme grijpt**, niet het niveau
     waarop de werkelijkheid administratief is onderverdeeld. Een subeenheid (opleiding,
     afdeling, redactie-binnen-een-concern) wordt alleen een eigen knoop als een
     mechanisme op dát niveau werkt. IJkvoorbeeld onderwijs (juli 2026):
     journalistiek-opleidingen (School voor Journalistiek, UvA Journalistiek) zijn eigen
     knopen omdat `academische_socialisatie` op opleidingsniveau werkt — de opleiding
     vormt en levert de journalisten, niet de instelling als geheel. Financiering, flak
     en `expert_legitimatie` werken juist op instellingsniveau (universiteit/hogeschool)
     en blijven daar. Andere opleidingen (rechten, economie, …) krijgen **geen** eigen
     knoop: hun invloed loopt al via de instelling of de individuele expert. Bestaan
     beide niveaus als knoop, leg dan de koppel vast: één beschrijvende
     `eigendom`-relatie instelling→opleiding (mechanisme-loos = kandidaat), zodat de
     graaf ziet dat het één huis is (precedent: rel. 704/705).

   De entiteit landt als `voorgesteld` (onzichtbaar in viz/scores tot een reviewer
   haar goedkeurt). Stel **alleen** een knoop voor die je met een bron kunt staven;
   dubbelcheck eerst of 'ie al bestaat (anders 400 op de UNIQUE-naam — dan is het geen
   nieuwe knoop maar een hercitatie).
3. **Nieuw verband (edge).** `POST /api/relations` met `source_id`, `target_id`,
   `relation_type` (uit de lijst in `schema.sql`: `eigendom`, `financiering`,
   `bron_van`, `bestuurder`, `draaideur`, `lobbyt`, `alliantie`, `oppositie`, …),
   optioneel `mechanism_id` (een **bestaand** mechanisme; een *nieuw* mechanisme is
   theorie-werk → RfC, niet jouw pad). Zet **geen** hoge `certainty`/`influence` mee:
   beide assen zijn *guilty-until-proven* — laat ze leeg (de invloed-vloer 0.05 valt
   vanzelf in) en laat de score uit het **bewijs** komen, niet uit jouw cijfer.
4. **Argument + citatie, in één keer.** `POST /api/arguments` met een `supporting`
   **root** op de nieuwe relatie (`relation_id`) **mét** inline `citations` (citaat +
   vindplaats) — een supporting/contradicting root zónder echte citatie wordt door de
   poort geweigerd (400). Dit argument is wat het verband echt draagt; de edge zonder
   argument is een lege bewering.
   - Wil je de **invloed** onderbouwen (niet alleen dat het verband bestaat, maar hoe
     sterk het de berichtgeving vormt)? Voeg een aparte root toe met
     `property='influence'` (M1.7) — die verschuift de invloed-as boven de vloer.

## Stance volgt het bewijs, niet je sympathie

Counter-bewijs tegen een verband is een **eigen contradicting argument op dat
verband**, nooit een "maar let op"-zin in een supporting argument (de DF-QuAD-engine
telt alleen losse knopen; een caveat in een steun-argument duwt de claim juist
omhóóg). Hetzelfde feit kan tegengesteld werken op verschillende doelen — kies de vorm
naar wat het bewijs ís (zie `missies/monitor_brief.md`).

## Eigen stem en specificiteit (eigenaarsbesluit 2026-10-08)

"'Ondermijnt zo het vertrouwen in de journalistiek' … deze taal moeten we niet overnemen, dit is
duidelijk een politiek spelletje … waak hier streng voor"; "PVV censureert AD … niet van belang".
Voor alles wat je als bewering (claim), beschrijving of herformulering indient:

- **Eigen stem = wat er gebeurde**: wie deed of zei wat, wanneer, waar, in welke functie. Geen
  oordeel over gevolgen of motieven ("ondermijnt het vertrouwen", "bedreiging voor de
  persvrijheid", "om journalisten te intimideren"), geen etiket ("rechts-populistisch",
  "extreemrechts", "linkse media", "mainstream", "neoliberale consensus", "omstreden") en geen
  retoriek van één kant. Zo'n oordeel alleen als citaat, met de naam van wie het uitsprak ("De
  NVJ noemde de uitspraak …"). De stemtoets (`scripts/stemtoets.py`, account `stemtoets`) toetst
  elk voorstel; wat niet neutraal is, merget niet en komt in neutrale vorm opnieuw binnen.
- **Over dát verband**: een argument over een verband noemt beide partijen, en de bron ook. Een
  uitspraak over "de pers", "journalisten" of "de media" draagt geen verband met één genoemd
  medium; de bronchecker (v3) zegt dan `klopt-niet` ("gaat niet over …").
- **Eén feit per argument**: een bestuursfunctie en een kandidatuur zijn twee argumenten, elk met
  een eigen bron die dát feit draagt. Een feit over een ánder verband hoort bij dat verband.

## Looptijd: zonder jaartal geen verband (eigenaarsbesluit 2026-10-09)

Elk verband dat je indient of onderbouwt, krijgt zijn looptijd: begin (`active_from`) en, als het
voorbij is, einde (`active_until`), zo precies als de bron geeft (`JJJJ`, `JJJJ-MM`, `JJJJ-MM-DD`),
met een citaat dat het jaartal noemt. Het begin van dít verband (benoeming, toetreding), niet de
oprichting van de organisatie of de datum van het artikel. Vind je het echt niet: zeg waar je
zocht (`zonder_jaar`) of laat het verband weg — nooit een geraden jaartal; de datumzoeker zoekt
verder. Een datum bij een bestaand verband: een aspect-argument (`property` `active_from`/
`active_until`, `property_value` de datum). Zie missies/README.md § Looptijd.

## Harde grenzen

- **Nooit** statuswijzigingen, merges, goedkeuringen, source-classificaties of
  verwijderingen — allemaal reviewer+/maintainer én mensenwerk. Jij stelt voor, een
  mens beslist; alles wat je indient blijft `voorgesteld`.
- **Geen nieuwe theorielaag.** Nieuwe *rollen*, *mechanismen* of *emergente velden*
  ontstaan alleen via een RfC (`POST /api/voorstellen`, soort `nieuw_theorie_element`,
  twee menselijke reviewer-akkoorden). Jij werkt op de **instantielaag**: nieuwe
  entiteiten + relaties die bestáánde rollen/mechanismen instantiëren. Mis je een
  mechanisme om een verband aan te haken? Haak het **niet** geforceerd aan het verkeerde
  mechanisme. Dien het in als **kandidaat** (bottom-up): een relatie *zonder*
  `mechanism_id`. Ze landt `voorgesteld`, telt in niets en incubeert; `GET /api/kandidaten`
  groepeert kandidaten op rol-paar (A→B), zodat een mens afleest wanneer een rol-paar
  genoeg instanties heeft om er via een RfC een mechanisme van te maken (die de kandidaten
  dan adopteert). Een los signaal dat (nog) geen verband is, blijft in je log.
- **Geen duplicaten.** Bestaat de entiteit of het verband al, dan is het een
  hercitatie op het bestaande element, geen nieuwe knoop/edge. Difflib-detectie op
  argumenten geeft 409 met kandidaten; respecteer dat.
- Log je ronde in `missies/logs/`: brief-hash, élke zoekopdracht, per vondst de
  aangemaakte source-/entity-/relation-/argument-id's, negatieve resultaten,
  stance-balans en de nieuwheid (nieuwe knopen/edges vs. hercitaties).

## Cadans (onbewaakt, C1)

Deze missie draait onbewaakt op een vaste cadans — **per kwartaal** (1 jan/apr/jul/okt),
of na een modelrelease (M3.1) wanneer de onderzoeksagenda verschuift — via de scheduler
(`scripts/agent_runner.py`; `deploy/systemd/agent-scout.{service,timer}` en
`deploy/crontab`). De runner start één headless `claude`-sessie onder `scout-agent`,
injecteert de voorregel (eerst `GET /api/agent/reeds_gereageerd`, sla die id's over) en
tee't de ronde naar `missies/logs/`. Onderwerp uit de top van
`data/onderzoeksagenda.json` (`python3 scripts/onderzoeksagenda.py`).

**Exit-condities.** Lege oogst (geen nieuwe, staafbare knoop/edge) → afronden en
loggen, geen projectie indienen. Rate-limit **429** → ronde stoppen en loggen, niet
herproberen. **LinkedIn draait alleen binnen de snelheidsrem** (beleid J4, gewijzigd
2026-09-30; weigert de rem met exit 75, ga dan door zonder LinkedIn); draai je de LinkedIn-mapper en is de sessie dood
(`⚠ LINKEDIN-SESSIE VERLOPEN`) → stoppen, het login-commando
`python3 tools/linkedin/scrape_profile.py login` relayen aan de eigenaar, niet
herproberen (`missies/linkedin_scout_brief.md`).

**Logging-plicht per ronde.** `missies/logs/YYYY-MM-DD_scout-agent_<ronde>.md` met de
brief-blob-hash, élke query letterlijk, per vondst de aangemaakte
source-/entity-/relation-/argument-id's, de negatieve resultaten (alléén in het log),
de stance-balans én de nieuwheid (nieuwe knopen/edges vs. hercitaties). Doel van een
ronde: het netwerk is meetbaar rijker geworden, zónder dat de stance-balans scheef is
getrokken. Niets aan het agent-contract verandert: alles blijft `voorgesteld`, eigen
token, geen statuswijzigingen.
