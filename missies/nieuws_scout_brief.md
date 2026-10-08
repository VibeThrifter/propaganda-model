# Missie-brief: nieuws-scout (wie is dit? — namen uit het nieuws uitzoeken)

**Account:** `nieuws-scout` (Bearer-token in `data/tokens/nieuws-scout.token`, rol bijdrager).
**Opdrachtgever:** de wachtrij `nieuws_doelen`, gevuld door de nieuws-aggregator
(account `nieuws-agent`, Epic 12 "Wie is dit?").
**Doel:** per doel uitzoeken **wie iemand is en welke publieke rol hij/zij heeft**, en de
neutrale **structuurfeiten** daarachter (partij, werkgever, bestuursfunctie,
woordvoerderschap, medium) via het gewone bijdragepad voorstellen — zodat de nieuws-app
bij een aangetikte naam het netwerk kan tonen.

Dit is een verbijzondering van de scout-missie. **Lees eerst volledig**
`missies/scout_brief.md` (anti-overfit, bron → knoop → verband → argument, stance volgt
het bewijs, geen theorielaag, geen duplicaten) en `missies/linkedin_scout_brief.md`
(LinkedIn-discipline). Alles daaruit geldt hier onverkort; deze brief voegt alleen de
wachtrij, de afbakening en de snelheidsrem toe.

> **Wat hier anders is (eigenaarsbesluit 2026-09-30).**
> 1. Je onderwerp komt niet uit de onderzoeksagenda maar uit de wachtrij: **één naam per
>    doel**, met context uit het nieuws (artikelen, organisaties, rolzinnen).
> 2. **LinkedIn mag onbewaakt**, maar alleen achter de snelheidsrem
>    (`tools/linkedin/snelheidsrem.py`: max 2/uur en 10/dag per soort, 08–22 uur,
>    stroomonderbreker). Zie stap 4.
> 3. Alles wat je indient landt `voorgesteld`, net als altijd. Daarna beslist de
>    **automatische beoordeling** (elk uur, andere accounts — **niet jij**): de bronchecker
>    haalt je bron op en zoekt je citaat letterlijk terug, en draagt de bron je bewering,
>    dan gaan neutrale structuurfeiten (`personeel`, `dienstverband`, `bestuurder`,
>    `adviseur`, `woordvoerder_van`, `lidmaatschap`, `eigendom`, `draaideur`) en hun
>    entiteiten de graaf in; draagt ze die niet volledig, dan zoekt de bronzoeker een betere
>    bron of wordt je voorstel verworpen. Dat verandert niets aan jouw discipline: **schrijf
>    alsof een mens elk voorstel leest** — een letterlijk citaat dat je bewering draagt is
>    het enige dat telt, en twijfel hoort op `twijfel`, niet op `klaar`.

## Wie wel, wie nooit

- **Wel, in deze volgorde:** politici en bestuurders van overheden (Kamerleden,
  ministers, wethouders, burgemeesters, gedeputeerden), topambtenaren (secretarissen-generaal,
  directeuren-generaal, inspecteurs-generaal) en bestuurders van zbo's, agentschappen en
  adviescolleges (besluitvorming hoort sinds 2026-10-07 in hetzelfde netwerk), journalisten/hoofdredacteuren,
  woordvoerders/voorlichters, bestuurders/commissarissen/directeuren van organisaties;
  daarna organisaties en experts (hoogleraren, analisten, denktankmedewerkers).
- **Nooit:** privépersonen — bewoners, ooggetuigen, slachtoffers, verdachten,
  nabestaanden, "Henk (61)", een willekeurige burger die in een artikel geciteerd wordt,
  ook als de nieuws-app ze per ongeluk aanbiedt. Geen publieke rol aantoonbaar → het doel
  is `overgeslagen` en je dient **niets** in. Ook niets over familie, woonplaats,
  gezondheid, geloof of andere privézaken van publieke personen.
- **Alleen wie relevant is voor het netwerk:** een publieke rol in politiek, media,
  bedrijfsleven, overheid, wetenschap of een belangen-/maatschappelijke organisatie (incl.
  tegenmacht: vakbonden, ngo's, klokkenluiders, activisten met een organisatie). Bekende
  Nederlanders zonder zo'n rol — artiesten, sporters, tv-persoonlijkheden, verdachten of
  veroordeelden in strafzaken, leden van het Koninklijk Huis — zijn `overgeslagen`
  (verslag: "geen rol in het netwerk"), ook als ze vaak in het nieuws staan. Twijfel je
  (een sporter die ook bestuurder is), onderzoek dan alleen die bestuursrol.
- **Buitenlandse personen** zonder rol in het Nederlandse netwerk (buitenlandse politici,
  staatshoofden, bestuurders van buitenlandse organisaties die niets met Nederlandse media,
  politiek of bedrijfsleven te maken hebben) zijn `overgeslagen` ("buitenland, geen NL-rol").
  Wel onderzoeken: buitenlandse eigenaren/investeerders van Nederlandse media en
  buitenlanders met een aantoonbare Nederlandse functie.
- **Geen actor** (fotocredit, naslagwerk zoals "Wikimedia Commons") of een verminkte naam
  ("Heinen van Financiën" = dubbel van Eelco Heinen) → `overgeslagen`; onderzoek het dubbel niet
  opnieuw.

## De ronde

**Maximaal 3 doelen per ronde.**

1. **Claim:** kijk eerst of LinkedIn nu mag: `python3 tools/linkedin/snelheidsrem.py mag zoek
   && python3 tools/linkedin/snelheidsrem.py mag profiel` (exit 0 = ja). Claim dan
   `POST /api/nieuws/doelen/claim_volgende?limit=3` — met `&linkedin=1` als LinkedIn mag
   (Bearer-token) → `{"doelen": [...]}`. Leeg → log "geen open doelen" en rond af (lege
   oogst is prima).
   Elk doel heeft `sleutel`, `naam`, `soort` (`persoon`|`organisatie`), `rol_categorie`,
   `rol_hint`, `context` (`events`, `artikelen` met url/bron/datum/titel, `organisaties`,
   `rolzinnen`), `entity_id` (bestaande pm-entiteit of null), `vervolg`, en bij een
   heropend doel het eerdere `verslag`/`resultaat`.
2. **Werk elk doel af** volgens de zes stappen hieronder.
3. **LinkedIn-vervolg:** een geclaimd doel met `vervolg: "linkedin"` én een bestaand
   `resultaat` is al onderzocht; alleen de LinkedIn-stap ontbrak (de rem weigerde toen).
   Doe dan alleen stap 4 (LinkedIn) en het indienen van wat dat oplevert, en PATCH daarna
   `status: "klaar"`, `vervolg: null`, het eerdere `verslag` aangevuld met één zin over
   LinkedIn, en `resultaat` = de oude id's plus de nieuwe (samengevoegd, niets weglaten).
   Weigert de rem alsnog (exit 75): PATCH `status: "klaar"` met `vervolg: "linkedin"`
   ongewijzigd. Levert LinkedIn niets bruikbaars op: `vervolg: null` en noteer dat.
3. **Sluit elk doel af** met een PATCH (stap 6) — ook bij `overgeslagen`/`twijfel`/
   `niets_gevonden`. Een doel dat je claimde maar niet afmaakt (tijd op, fout), zet je
   op `fout` met een korte reden; blijft het `bezig`, dan komt het na 3 uur vanzelf terug.

> De runner-prompt zegt "je zet NOOIT statussen". Dat gaat over **modelstatussen**
> (mergen, goedkeuren, afwijzen, classificeren). De status van een **wachtrij-doel**
> (`PATCH /api/nieuws/doelen/<id>`) is procesadministratie en hoort juist bij deze missie.

### Stap 1 — Identiteit en publieke rol vaststellen

- Lees de context: welke organisatie, welke functie, welke gemeente/partij noemen de
  artikelen? Open de artikel-URL's zelf; de rolzinnen zijn een samenvatting, geen bewijs.
- Stel vast **wie** dit is en **welke publieke rol** de persoon nu heeft (of had in de
  periode van de artikelen). Leg de doorslaggevende bron vast.
- **Privépersoon of geen publieke rol aantoonbaar** → `overgeslagen`, niets indienen.
- **Naamgenoten die je niet betrouwbaar kunt scheiden** (twee "Jan de Vries"-bestuurders,
  een LinkedIn-profiel dat net niet klopt) → `twijfel`, niets indienen of alleen wat
  ondubbelzinnig vaststaat; beschrijf in het verslag wat de twijfel is.
- Organisatie-doelen: stel de juiste juridische/structurele vorm vast (KvK, eigen site).

### Stap 2 — Het model raadplegen en precedenten volgen

- Bestaat de naam al? Kijk in `GET /api/graph_data` (of alleen-lezen in de DB:
  `sqlite3 "file:data/propaganda_model.db?mode=ro"`), ook op spelvarianten, tussenvoegsels
  en afkortingen. Bestaat de entiteit al → hergebruik haar (manifest: DB-id als int),
  maak nooit een tweede knoop. `entity_id` in het doel is een hint, geen garantie.
- Welke organisatie-knopen bestaan al (partij, gemeente, ministerie, medium, bedrijf)?
  Koppel aan de **bestaande** knoop; maak een org alleen aan als ze ontbreekt en je haar
  met een bron kunt staven.
- **Registers eerst.** Het openbaar bestuur staat er al uit de officiële registers (account
  `register-import`): ministeries met hun directoraten-generaal, zbo's, agentschappen,
  adviescolleges, inspecties, gemeenten, provincies en waterschappen; bewindspersonen, SG's,
  DG's, burgemeesters, wethouders, CdK's, dijkgraven en de 150 Kamerleden met hun fractie,
  nevenfuncties, loopbaan en geschenken. Zoek een ambtsdrager dus eerst in het model (ook op
  externe id: `GET /api/externe_ids?stelsel=tk_persoon|oo&waarde=…`). Burgemeesters en
  wethouders staan er vaak met voorletters en een toevoeging ("B.C.M. Vostermans (burgemeester
  Peel en Maas)"): kloppen achternaam, voorletter, functie en plaats, dan is het die knoop —
  hergebruik hem en maak geen tweede (noem in het verslag dat de volledige naam ontbreekt).
  Een registerfeit (ambt, fractie, nevenfunctie) hoef je niet opnieuw in te dienen.
- **Volg de precedenten van vergelijkbare actoren** — kijk hoe het model soortgelijke
  personen al modelleert en doe het net zo. Richtinggevend (controleer altijd in het
  model; ids via `GET /api/roles` en de mechanismen in `graph_data`):

  | Actor | Relatie (richting) | Mechanisme (bestaand) | Rol-suggestie persoon |
  |---|---|---|---|
  | Politicus ↔ partij | `partij → persoon`, `lidmaatschap` | `partijlijn` | `politicus` |
  | Partijlid zonder politiek mandaat (bestuurder, journalist) ↔ partij | `partij → persoon`, `lidmaatschap` | `partijbinding` (niet `partijlijn`: dat is fractiediscipline van politici) | naar functie |
  | Bewindspersoon ↔ ministerie | `persoon → ministerie`, `ambt` | `ministeriele_verantwoordelijkheid` | `bewindspersoon` |
  | Topambtenaar (SG, DG, IG) ↔ ministerie of onderdeel | `persoon → org`, `ambt` | `ambtelijke_leiding` | `topambtenaar` |
  | Burgemeester, wethouder, CdK, dijkgraaf ↔ gemeente, provincie, waterschap | `persoon → org`, `ambt` | `lokaal_bestuursmandaat` | `lokale_bestuurder` |
  | Kamerlid, Statenlid, raadslid ↔ Kamer, provincie, gemeente | `persoon → org`, `ambt` | `kamerzetel` | `politicus` |
  | Zbo of agentschap ↔ ministerie | `ministerie → org`, `zeggenschap` | `verzelfstandigd_bestuur` (zbo) / `hierarchische_aansturing` (agentschap, DG) | org: `uitvoeringsorganisatie` |
  | Adviescollege, planbureau ↔ ministerie | `adviescollege → ministerie`, `adviseur` | `institutioneel_advies` | org: `adviesorgaan` |
  | Organisatie met toegang tot de Kamer ↔ Tweede Kamer | `org → Tweede Kamer`, `lobbyt` | `lobbytoegang` | — |
  | Nevenfunctie van een ambtsdrager ↔ organisatie | `persoon → org`, `bestuurder`/`adviseur`/`lidmaatschap` | `nevenfunctie_verstrengeling` | — |
  | Geschenk of betaalde reis ↔ ambtsdrager | `gever → persoon`, `geschenk` | `geschenk_en_gastvrijheid` | — |
  | Benoeming door Kroon of minister (burgemeester, CdK, SG/DG, zbo-voorzitter, staatsraad) | `bewindspersoon → persoon` | `kroonbenoeming` (alleen met een bron voor de benoeming zelf) | naar functie |
  | Journalist ↔ medium | `mediaorganisatie → persoon`, `dienstverband` | `dienstverband` | `journalist` (of `hoofdredacteur`) |
  | Woordvoerder ↔ organisatie | `persoon → org`, `woordvoerder_van` | `woordvoerdersregie` (of `draaideurconstructie` bij een loopbaanstap) | `voorlichter` |
  | Bestuurder/commissaris ↔ organisatie | `persoon → org`, `bestuurder` | `draaideurconstructie` (loopbaan), `directiebenoeming`/`commissarisbenoeming` waar het model dat al zo doet | `directie` / `raad_van_commissarissen` |
  | Medewerker ↔ organisatie | `persoon → org`, `personeel` | `draaideurconstructie` | naar functie |
  | Expert ↔ denktank | `persoon → denktank`, `personeel` | `denktank_levert_expert` | `gezagsexpert` |

- **Zet ALTIJD een `mechanism_id` als een bestaand mechanisme past** — een relatie
  zonder mechanisme is een kandidaat en kan niet worden goedgekeurd (door niemand).
  Past er echt geen, forceer dan niets: dien een kandidaat in (zonder `mechanism_id`) en
  zeg dat in het verslag.
- Geef elke nieuwe entiteit een **rol-suggestie** (`primary_role_id`) uit de bestaande
  rollen; `type` = de structurele vorm (`persoon`, `partij`, `overheidsinstelling`,
  `mediaorganisatie`, `bedrijf`, …), nooit de functie.

### Stap 3 — Primaire bronnen eerst

- **Politici:** tweedekamer.nl / eerstekamer.nl, parlement.com, de site van de gemeente/
  provincie (college, raad), rijksoverheid.nl, de partijsite (kandidatenlijst).
- **Bestuurders & woordvoerders:** de eigen site van de organisatie (bestuur, directie,
  persvoorlichting), het jaarverslag, KvK-/registergegevens, officiële persberichten.
- **Journalisten:** colofon, auteurspagina of redactiepagina van het medium.
- **De nieuwsartikelen uit `context`** zelf: een artikel dat iemand als "wethouder van X"
  of "woordvoerder van Y" opvoert is een bruikbare (secundaire) bron — citeer de zin.
- **Wikipedia is géén bron**, alleen een vindplaats: loop door naar de voetnoten en
  citeer de onderliggende bron.
- Controleer elke quote **verbatim** op de pagina zelf. Nooit fabriceren; niet te staven
  = niet indienen.

### Stap 4 — LinkedIn (personen): standaard-reflex, maar achter de rem

Bij een persoon is LinkedIn de standaard-reflex voor loopbaan en huidige functie —
naast (niet in plaats van) de primaire bronnen. Onder de venv (`tools/linkedin/.venv`):

```bash
tools/linkedin/.venv/bin/python tools/linkedin/scrape_profile.py zoek "<naam>" --context "<organisatie uit de context>" --max 5
tools/linkedin/.venv/bin/python tools/linkedin/scrape_profile.py "https://www.linkedin.com/in/<slug>/"
```

- **Identiteit moet kloppen** vóór je een profiel gebruikt: naam **én** een organisatie
  of rol uit de context moeten overeenkomen. Geen match → niet scrapen (of niet
  gebruiken) en dat noteren. Hooguit één of twee profielen per doel.
- **Exit 75 — `⏳ LINKEDIN-SNELHEIDSREM — volgende kans HH:MM`:** de rem weigert nu
  (uur/dag vol, buiten 08–22 uur of uitgezet). Niet herproberen, niet wachten: zet bij
  de PATCH `"vervolg": "linkedin"` en werk het doel af met de andere bronnen.
- **Exit 76 — `⛔ LINKEDIN-BLOKKADE`:** de stroomonderbreker is gesprongen (captcha/
  checkpoint/authwall). Stop met LinkedIn voor de rest van de ronde, noteer het in het
  log en in de verslagen, en laat de melding letterlijk in je uitvoer staan (de runner
  detecteert haar voor de eigenaar).
- **`⚠ LINKEDIN-SESSIE VERLOPEN`:** stop met LinkedIn, relay letterlijk
  `python3 tools/linkedin/scrape_profile.py login` aan de eigenaar, niet herproberen.
- LinkedIn is **zelf-gerapporteerd**: gebruik het profiel als bron met
  `reliability_voorgesteld: grijs`; een primaire bron gaat voor. De ruwe scrape blijft in
  `data/linkedin/` (gitignored). Een loopbaan mag je via
  `tools/linkedin/linkedin_naar_model.py <json> --token data/tokens/nieuws-scout.token`
  (eerst droog!) of in je eigen manifest verwerken — beperk je tot wat relevant is voor
  de publieke rol, geen volledige cv's.

### Stap 5 — Indienen (alles `voorgesteld`)

Via een manifest voor `scripts/scout_indienen.py` (bron → entiteit → relatie mét
mechanisme → supporting argument met een **verbatim** quote uit een bron met URL):

```bash
python3 scripts/scout_indienen.py data/scout/nieuws-<sleutel>.json                        # droog
python3 scripts/scout_indienen.py data/scout/nieuws-<sleutel>.json --indienen \
    --token data/tokens/nieuws-scout.token --resultaat-json data/scout/nieuws-<sleutel>.resultaat.json
```

`--resultaat-json` schrijft precies de id's die je voor de PATCH nodig hebt.

- **Neutrale formulering.** Structuurfeiten in de vorm "X is wethouder van Y (sinds …)",
  "X is woordvoerder van Y" — **geen** waarderende of beschuldigende taal over personen,
  geen motieven, geen "omstreden", "dubieus", "spilfiguur". De smaad-firewall houdt een
  negatieve persoonsclaim toch tegen; dien hem dus niet in.
- Certainty/influence niet zetten (0,05-vloer). Datum (`active_from`/`active_until`)
  alleen als de bron hem geeft.
- **Sourcing-/invloedsverbanden** (iemand levert als expert aan media, lobbyt bij, …)
  alleen met een **gedocumenteerd patroon** (meerdere bronnen, niet één optreden); die
  blijven altijd mensenwerk (de autokeur raakt ze niet).
- Een 409 (duplicaat) of 400 is informatie: log hem en ga door; nooit
  `negeer_duplicaten` om er doorheen te duwen.

### Stap 6 — Het doel afsluiten + loggen

```bash
curl -s -X PATCH http://localhost:5000/api/nieuws/doelen/<id> \
  -H "Authorization: Bearer $(cat data/tokens/nieuws-scout.token)" -H "Content-Type: application/json" \
  -d '{"status": "klaar", "verslag": "<kort, neutraal>", "entity_id": <pm-id of null>,
       "resultaat": {"entity_ids": [..], "relation_ids": [..], "source_ids": [..], "argument_ids": [..]},
       "vervolg": null}'
```

| Status | Wanneer |
|---|---|
| `klaar` | Identiteit + publieke rol staan vast en je hebt ≥1 gesourcet structuurfeit ingediend (of de persoon bestond al en je vulde aan). Alléén dan kijkt de autokeur ernaar. |
| `niets_gevonden` | Publieke rol aannemelijk, maar geen staafbare bron gevonden — niets ingediend. |
| `overgeslagen` | Privépersoon of geen publieke rol — niets ingediend. |
| `twijfel` | Naamgenoten/identiteit niet sluitend — een mens kijkt. |
| `fout` | Technisch vastgelopen (API-fout, tijd op). |

- **`verslag`**: 1–4 zinnen, neutraal, wat je vaststelde en op welke bron dat rust
  ("Wethouder Economie gemeente Dijkerhoven sinds 2022 (bron: gemeente-site); partij X
  (parlement.com). LinkedIn: rem, vervolg=linkedin."). Geen oordeel over de persoon.
- **`entity_id`**: de pm-entiteit van de persoon/organisatie zelf (nieuw of bestaand).
- **`resultaat`**: de id's die jíj in deze ronde aanmaakte. Bij een **heropend** doel:
  voeg de eerdere `resultaat`-id's samen met de nieuwe (de PATCH vervangt de lijst).
- **Log de ronde** in het logbestand dat de runner noemt (`missies/logs/<datum>_nieuws-scout_<ronde>.md`,
  conventies in `missies/README.md`): brief-hash, per doel de sleutel + status, élke
  zoekopdracht letterlijk (web, DB, LinkedIn-zoek), gescrapete profiel-URL's, per vondst
  de aangemaakte source-/entity-/relation-/argument-id's, negatieve resultaten (alleen in
  het log), de LinkedIn-remstatus (`python3 tools/linkedin/snelheidsrem.py status`) en
  de stance-balans.

## Harde grenzen

- Nooit mergen, goedkeuren, afwijzen, classificeren of verwijderen in het model — ook
  niet "omdat het toch automatisch goedgekeurd wordt". Je hebt er ook het token niet voor.
- Nooit een privépersoon onderzoeken of iets over privézaken indienen.
- Geen nieuwe rollen/mechanismen (theorielaag = RfC). Geen org→org-conclusies.
- Nooit meer dan 3 doelen per ronde; nooit LinkedIn buiten de rem om (geen
  `--ik-weet-het`, geen tweede sessie, geen headless-trucs, geen proxy's).
- Rate-limit **429** op een inhouds-endpoint → ronde stoppen en loggen (de
  wachtrij-endpoints zelf hebben geen rate limit).
