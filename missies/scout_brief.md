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

## Onderwerpkeuze & anti-overfit-protocol (verplicht — zelfde geest als de documentalist)

1. **Neutrale missievraag, eerst zoeken.** Formuleer de zoekvraag zónder modelclaim
   (*"welke partijen financieren / besturen / leveren bronnen aan NL-media en zitten
   nog niet in kaart?"* — nooit *"zoek een verband dat bevestigt dat X de pers
   stuurt"*). Lees de database NIET vóór het zoeken; pas bij het indienen koppel je de
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

## Ritme

Per kwartaal één ronde, of na een modelrelease (M3.1) wanneer de onderzoeksagenda
verschuift. Doel van een ronde: het netwerk is meetbaar rijker geworden (n nieuwe
knopen + n nieuwe edges, elk met bron), zónder dat de stance-balans is scheefgetrokken.
