# Propagandamodel Nederlandse Politiek & Media

## Doel

Dit project modelleert de structurele mechanismen waarmee nieuws in Nederland wordt gefilterd en gevormd voordat het het publiek bereikt. Het is gebaseerd op het propagandamodel van Herman & Chomsky (*Manufacturing Consent*, 1988), toegepast op de Nederlandse context met behulp van het werk van Tabe Bergman, Joris Luyendijk, Kees van der Pijl en anderen.

Het model is geen complottheorie. Het beschrijft hoe structurele krachten — eigendom, economische druk, bronafhankelijkheid, disciplinering en ideologie — leiden tot een systematische pro-elite bias als *emergente eigenschap* van het systeem, zonder dat er sprake hoeft te zijn van centrale sturing.

---

## Architectuur: twee lagen

Het systeem onderscheidt twee lagen:

### Laag 1: Theoretisch model (abstract, zonder namen)

Beschrijft de structuur: welke **rollen** bestaan er in het medialandschap en via welke **mechanismen** oefenen ze invloed uit?

- **Rollen** — abstracte functies die actoren kunnen vervullen (bijv. `mediaeigenaar`, `adverteerder`, `hoofdredacteur`)
- **Mechanismen** — processen waarmee de ene rol de andere beïnvloedt (bijv. `pakketjournalistiek`, `etikettering`, `zelfcensuur`)

Elk mechanisme is gekoppeld aan een van de vijf filters van het propagandamodel, plus de uitbreidingen `cross_filter` (moderne, filteroverschrijdende mechanismen zoals algoritmische filtering en de draaideur) en `tegenmacht` (krachten die het systeem begrenzen).

### Laag 2: Instantiemodel (concreet, met namen)

De echte entiteiten en relaties in Nederland:

- **Entiteiten** — concrete actoren met naam en toenaam (bijv. DPG Media, Thomas Leysen, Bilderberg Groep)
- **Relaties** — concrete verbanden tussen entiteiten (bijv. DPG Media bezit de Volkskrant)

Elke entiteit is gekoppeld aan een of meer rollen uit het theoretisch model. Elke relatie is optioneel gekoppeld aan een mechanisme.

---

## De vijf filters + uitbreidingen

Elk mechanisme is gekoppeld aan één filter; elke rol aan één categorie. Naast de vijf klassieke filters van Herman & Chomsky kent het model drie uitbreidingen die het hedendaagse Nederlandse landschap vangen: **cross-filter** (systemische en moderne mechanismen die meerdere filters overspannen), **tegenmacht** (krachten die het filtersysteem begrenzen of doorbreken) en **systeemactoren** (structurele spelers die in alle filters tegelijk opereren).

### Filter 1: Eigendom
De eigendomsstructuur bepaalt de institutionele context van nieuwsproductie. In Nederland bestaat een duopolie: DPG Media en Mediahuis bezitten samen >90% van de online commerciële nieuwsmarkt. De eigenaren (families Van Thillo, Leysen, Baert, Van Puijenbroek) behoren tot de transnationale kapitaalklasse.

Het eigendom wordt zelden direct uitgeoefend maar via een keten van constructies (`holdingconstructie`): gestapelde investeringsvehikels (`overnamevehikel`: Epifin, Mediahuis Partners, VP Exploitatie) en vaak een **Stichting Administratiekantoor (STAK)** die de aandelen certificeert — zeggenschap wordt zo gescheiden van economisch belang, geconcentreerd bij de familie, en de uiteindelijke eigenaren blijven buiten beeld (boven Epifin/DPG zit zo'n STAK). Daartegenover staat als tegenkracht de **borgingsstichting**: een onafhankelijkheidsstichting met een prioriteitsaandeel of vetorecht die de redactionele koers beschermt (zie *Tegenmacht*, `onafhankelijkheidsborging`).

**Rollen:** `mediaeigenaar`, `mediaorganisatie_rol`, `aandeelhouder`, `institutioneel_belegger`, `hoofdredacteur`, `overnamevehikel`
**Mechanismen:** `eigendomsconcentratie`, `winstmaximalisatie`, `cross_media_eigendom`, `holdingconstructie`, `acquisitiestrategie`, `aandeelhouder_druk`, `systemisch_eigenaarschap`, `benoemingspolitiek`, `hoofdredacteur_als_filter`, `redactioneel_budgetcontrole`

### Filter 2: Advertentie
Media zijn financieel afhankelijk van adverteerders, wat een structurele voorkeur creëert voor content die het consumentistische wereldbeeld bevestigt.

**Rollen:** `adverteerder`
**Mechanismen:** `advertentiedruk`, `commerciele_afhankelijkheid`, `supportive_selling_environment`, `commerciele_content_druk`, `stakeholder_capitalism_frame`

### Filter 3: Sourcing
Economische druk dwingt redacties tot afhankelijkheid van een beperkt aantal routineuze bronnen: het ANP, de overheid, en door de elite gefinancierde denktanks. Toegang (*access*) is hierbij zelf een schaarse hulpbron: wie aan tafel mag krijgt een podium, wie fundamenteel afwijkt verliest die toegang geruisloos (`toegangsdisciplinering`).

Achter de bronnen zitten **principalen** die de sourcing-stroom voeden via instrumenten — dezelfde logica, twee gedaanten. Corporate: een `belanghebbende` (bedrijf/sector/branche) zet zijn belang om in mediabeeld via lobbyisten, brancheorganisaties en denktanks (`belangenbehartiging`); de soorten lobby verschillen (corporate-sectoraal, branche/koepel, ideologisch/NGO) en goed georganiseerde belangen zijn structureel oververtegenwoordigd. Politiek: een partij/bewindspersoon **óf een ministerie/instituut** (Rijksvoorlichtingsdienst) levert via de voorlichter één afgestemde boodschap (`gecoordineerde_voorlichting`). De voorlichter en de politicus zijn bewust *aparte* rollen — de toegangs-poortwachter versus de bron — en het smeermiddel is *access*: de off-the-record Nieuwspoort-code "je hebt het niet van mij, maar..." (Luyendijk), die zelfcensuur wekt omdat niemand hem durft te breken.

Naast deze principalen gelden officiële instituties zelf als gezaghebbende routinebron: een `gezagsinstituut` (CPB, DNB, CBS, RIVM, WRR, ministerie, OM) is een **primaire definieerder** (Hall) wiens cijfers en rapporten als neutraal feit gelden en de agenda zetten (`institutioneel_gezag`); de `gezagsexpert` (de "onafhankelijke" hoogleraar/econoom/deskundige) legitimeert de consensus (`expert_legitimatie`).

**Rollen:** `persbureau`, `journalist`, `voorlichter`, `lobbyist`, `denktank`, `belanghebbende`, `gezagsinstituut`, `gezagsexpert`
**Mechanismen:** `bron_afhankelijkheid`, `pakketjournalistiek`, `expert_framing`, `pr_subsidie`, `haagse_stam`, `toegangsdisciplinering`, `belangenbehartiging`, `gecoordineerde_voorlichting`, `institutioneel_gezag`, `expert_legitimatie`, `journalist_bronrelatie`, `politicus_als_bron`, `voorlichter_informatiefilter`, `pr_naar_journalist`, `persbureau_naar_redactie`, `lobby_informatievoorziening`, `lobbyist_naar_journalist`, `lobbyist_naar_politicus`, `denktank_legitimatie`, `denktank_financiering_bias`, `denktank_naar_media`, `denktank_naar_politiek`

### Filter 4: Flak
Disciplineringsmechanismen die journalisten ontmoedigen om van de geaccepteerde lijn af te wijken: juridische dreiging, publieke aanvallen, etikettering, en interne zelfcensuur. De hedendaagse *cancelling* — een gast die iets onwelgevalligs zegt en niet meer wordt uitgenodigd — valt hier onder via `deplatforming`.

**Rollen:** `alternatief_medium`
**Mechanismen:** `juridische_dreiging`, `publieke_aanval`, `deplatforming`, `etikettering`, `zelfcensuur`, `geweld_intimidatie`, `slapp_tegen_journalist`, `politieke_flak`, `elite_forum_flak`, `morele_chantage`, `onevenwichtig_debat`, `redactioneel_conformisme`, `sociologische_homogeniteit`, `chilling_effect_geweld`, `online_intimidatie_journalist`, `woo_obstructie`, `alternatieve_uitdaging`

### Filter 5: Ideologie
Het overkoepelende filter: een denkkader dat als "gezond verstand" wordt gepresenteerd (Gramsci's culturele hegemonie). In de Nederlandse context is die hegemonie een specifieke combinatie — **cultureel links-progressief** (een *politics of recognition*: diversiteit, identiteit) én **economisch neoliberaal**, pro-Atlantisch: wat Nancy Fraser "progressief neoliberalisme" noemt. Elite-fora synchroniseren dit wereldbeeld, en **universiteiten en journalistiekopleidingen** (`kennisinstituut`) reproduceren het als neutrale, wetenschappelijke vanzelfsprekendheid (`academische_socialisatie`). Afwijking verschijnt niet als ander standpunt maar als gebrek aan kennis of als "activisme". (De *academisch criticus die het filtersysteem blootlegt* is bewust geen aparte rol: in NL een marginaal, niet-bepalend verschijnsel — de relevante academische kracht is juist hegemonie-*dragend*.)

**Rollen:** `elite_forum`, `columnist_opiniemaker`, `kennisinstituut`
**Mechanismen:** `overton_bewaking`, `false_balance`, `ideologische_synchronisatie`, `hegemonische_naturalisatie`, `spectrum_bewaking`, `emergente_bias`, `systemische_homeostase`, `journalist_socialisatie`, `academische_socialisatie`, `politicus_als_ideoloog`, `columnist_als_hegemon`, `elite_forum_ideologie`

### Uitbreiding A: Cross-filter (systemisch & modern)
Mechanismen die niet in één filter passen maar meerdere filters tegelijk aandrijven of overbruggen — vooral techplatforms, de draaideur en economische terugkoppeling. Dit vervangt de oude losse categorie "Overig (modern)" uit het oorspronkelijke model. De **draaideur** (`draaideurconstructie`) hoort hier thuis en niet onder ideologie: personeel circuleert tussen vier domeinen — politiek, bedrijfsleven, media/journalistiek en lobby/PR — en verbindt zo eigendom, sourcing én ideologie. Alle richtingen komen voor: minister → corporate bestuur (Eurlings → KLM), politiek ↔ omroep (Hillen, Van den Brink), journalist → woordvoering, lobbyist ↔ overheid/bedrijf.

**Mechanismen:** `algoritmische_filtering`, `algoritmische_socialisatie`, `platform_nieuwsselectie`, `platform_verdienmodel_druk`, `platform_advertentie_concentratie`, `draaideurconstructie`, `draaideur_journalistiek_politiek`, `economische_feedback_loop`, `mediaeigenaar_elite_netwerk`

### Uitbreiding B: Tegenmacht
Het model is niet deterministisch: het modelleert óók de krachten die het filtersysteem begrenzen of doorbreken. Zulke doorbraken zijn mogelijk, maar vaak incidenteel en onder druk (zie ook `toezicht_tandeloosheid`).

**Rollen:** `onderzoeksjournalist`, `klokkenluider`, `parlementair_controleur`, `toezichthouder`, `vakbond_media`, `burgerinitiatief`, `borgingsstichting`
**Mechanismen:** `onderzoeksjournalist_doorbraak`, `klokkenluider_doorbraak`, `onafhankelijk_medium_tegenwicht`, `parlementaire_controle`, `parlementaire_doorbraak`, `toezichthouder_interventie`, `toezicht_tandeloosheid`, `vakbond_bescherming`, `burgerinitiatief_druk`, `onafhankelijkheidsborging`

De `borgingsstichting` (onafhankelijkheidsstichting met prioriteitsaandeel/vetorecht, bv. Stichting Democratie en Media bij DPG) is de tegenpool van het STAK-controlevehikel uit Filter 1: ze biedt een structurele rem op eigenaarsinvloed, maar geen ijzeren garantie (een minderheidsbelang naast de winstgedreven meerderheid).

### Systeemactoren
Structurele spelers die in meerdere filters tegelijk opereren en daarom een eigen rolcategorie vormen (zij vervullen geen eigen filter maar voeden er meerdere).

**Rollen:** `politicus`, `publiek`, `redactie`, `techplatform`, `belanghebbende`

---

## Databaseschema

### Overzicht tabellen

```
THEORETISCH MODEL          INSTANTIEMODEL              BEWIJS
┌──────────┐               ┌──────────┐                ┌──────────┐
│  roles   │◄──────────────│ entities │                │ sources  │
└──────────┘   primary_     ├──────────┤                ├──────────┤
               role_id      │entity_   │                │source_   │
┌──────────┐               │roles     │                │locations │
│mechanisms│◄──────────────┤          │                └────┬─────┘
└──────────┘   mechanism_   └────┬─────┘                     │
               id                │                           │
                           ┌─────┴─────┐               ┌────┴─────┐
                           │ relations │──────────────►│arguments │
                           └───────────┘               ├──────────┤
                             certainty                 │citations │
                             influence                 └──────────┘
```

### Theoretisch model

| Tabel | Beschrijving | Velden |
|---|---|---|
| `roles` | Abstracte rollen in het medialandschap | name, category (`eigendom`/`advertentie`/`sourcing`/`flak`/`ideologie`/`systeemactor`/`tegenmacht`/`overig`), description, examples |
| `mechanisms` | Processen waarmee rollen invloed uitoefenen | name, filter (vijf filters + `cross_filter`/`tegenmacht`/`overig`), mechanism_type (`structureel`/`procedureel`/`psychologisch`/`economisch`/`juridisch`/`technologisch`/`discursief`), description, effect, source_role_id, target_role_id |

### Instantiemodel

| Tabel | Beschrijving | Velden |
|---|---|---|
| `entities` | Concrete actoren (personen, organisaties, partijen) | name, type, primary_role_id, description, metadata (JSON), active_from/active_until/active (temporeel) |
| `entity_roles` | Koppeltabel: entiteit kan meerdere rollen vervullen | entity_id, role_id, notes |
| `relations` | Concrete relaties tussen entiteiten | source_id, target_id, relation_type, mechanism_id, description, certainty, influence, bidirectional, active_from/active_until/active (temporeel) |
| `source_mentions` | Welke entiteiten worden in welke bronnen genoemd | source_id, entity_id, context |

### Bronnen (academisch)

| Tabel | Beschrijving | Velden |
|---|---|---|
| `sources` | Academische bronnen (boeken, artikelen, rapporten) | title, author, source_type, publisher, date_published, language, summary, reliability (`primair`/`academisch`/`institutioneel`/…), processed |
| `source_locations` | Meerdere toegangspunten per bron | source_id, location_type (url/file/doi/isbn/arxiv/handle/archive_url), location, accessed_at, notes |

### Argumenten & citaties (discussieboom)

| Tabel | Beschrijving | Velden |
|---|---|---|
| `arguments` | Discussieboom: argumenten op relaties of entiteiten, met nesting | relation_id (optioneel), entity_id (optioneel), parent_argument_id (NULL=root), property/property_value (optioneel: argument over een specifieke eigenschap), stance, claim, reasoning, weight, status (`ongecontroleerd` default), contributed_by |
| `citations` | Bronvermeldingen per argument | argument_id, source_id, quote, page, section, context |
| `edit_log` | Auditlog van wijzigingen (aanmaak, statuswijziging) | table_name, record_id, action (`created`/`updated`/`deleted`/`verified`/`disputed`), changed_by, old_value, new_value, reason |

Argumenten vormen een boomstructuur:
- **Root-argumenten** (`parent_argument_id = NULL`) hangen direct aan een relatie of entiteit
- **Reacties** (`parent_argument_id = <id>`) reageren op een ander argument
- Elk argument kan gericht zijn op een **relatie** (`relation_id`) of een **entiteit** (`entity_id`), minstens één is verplicht

---

## Scores op relaties

Elke relatie heeft twee onafhankelijke scores:

### Certainty (zekerheid): "Bestaat deze relatie?"

| Score | Betekenis | Voorbeeld |
|---|---|---|
| 0.9 - 1.0 | Gedocumenteerd feit | DPG Media bezit de Volkskrant |
| 0.7 - 0.89 | Sterk bewijs | ANP-pakketjournalistiek bij dagbladen |
| 0.5 - 0.69 | Waarschijnlijk | WEF-invloed op NOS-framing |
| 0.3 - 0.49 | Mogelijk | Specifieke SLAPP-dreiging door GBL |
| < 0.3 | Speculatief | — |

### Influence (invloed): "Hoe sterk werkt het door in de berichtgeving?"

| Score | Betekenis | Voorbeeld |
|---|---|---|
| 0.9 - 1.0 | Bepalend | DPG→Volkskrant eigendom (bepaalt budget, hoofdredacteur) |
| 0.7 - 0.89 | Sterk | ANP→NU.nl pakketjournalistiek (bulk van het nieuws) |
| 0.5 - 0.69 | Matig | Clingendael→NOS expert framing |
| 0.3 - 0.49 | Beperkt | Eén adverteerder van velen |
| < 0.3 | Marginaal | BlackRock→Shell (passief bezit) |

Een relatie kan zeker bestaan maar weinig impact hebben (Vanguard→Shell: feit, maar passief). Of onzeker zijn maar potentieel groot effect hebben (zelfcensuur op redacties: moeilijk te bewijzen, maar systemisch).

---

## Argumentstructuur per relatie

Elke relatie kan meerdere argumenten hebben die voor, tegen of nuancerend zijn. Elk argument kan onderbouwd worden met meerdere citaties uit verschillende bronnen.

```
Relatie: DPG Media → RTL Nederland [winstmaximalisatie]
  certainty: 0.85  |  influence: 0.70
  │
  ├── [+] SUPPORTING: "ACM moest voorwaarden stellen..."
  │     ├── Citatie → AI-analyse rapport (lokaal bestand)
  │     │
  │     └── [−] CONTRADICTING: "ACM-voorwaarden beperken winstmaximalisatie"
  │           ├── Citatie → ACM besluit (2023)
  │           │
  │           └── [+] SUPPORTING: "Voorwaarden zijn niet afdwingbaar na fusie"
  │                 └── Citatie → FTM onderzoek (2024)
  │
  └── [~] CONTEXTUAL: "Redactiestatuten bieden geen ijzerharde garanties"
        ├── Citatie → Bergman (2014), Hoofdstuk 1
        └── Citatie → Herman & Chomsky (1988), pp. 3-14

Entiteit: DPG Media
  │
  ├── [+] SUPPORTING: "DPG heeft een dominante marktpositie in online nieuws"
  │     └── Citatie → ACM marktanalyse (2023)
  │
  └── [−] CONTRADICTING: "Marktaandeel alleen zegt niets over redactionele invloed"
        └── Citatie → NVJ rapport (2022)
```

### Stances

| Stance | Symbool | Betekenis |
|---|---|---|
| `supporting` | + | Bewijs dat de relatie bevestigt |
| `contradicting` | - | Bewijs dat de relatie tegenspreekt |
| `contextual` | ~ | Nuancering, noch voor noch tegen |

---

## Entiteittypes

De volledige toegestane lijst staat in de `CHECK`-constraint van `entities` in `schema.sql`. De belangrijkste:

**Personen:** `politicus`, `journalist`, `columnist`, `voorlichter`, `lobbyist`, `academicus`, `mediaeigenaar`, `toezichthouder_persoon`, `advocaat`, `klokkenluider`, `persoon`

**Organisaties:**

| Type | Beschrijving | Voorbeelden |
|---|---|---|
| `mediaorganisatie` | Nieuwsproducent of -distributeur (pers/online) | DPG Media, de Volkskrant, De Telegraaf, NRC |
| `omroep` | Publieke of commerciële omroep | NOS, RTL Nederland |
| `persbureau` | Persbureau / nieuwsgroothandel | ANP |
| `bedrijf` | Commercieel bedrijf | Shell, Albert Heijn, McKinsey |
| `adverteerder` | Bedrijf in adverteerdersrol | (grote landelijke adverteerders) |
| `vermogensbeheerder` | Institutionele belegger | BlackRock, Vanguard |
| `elite_netwerk` | Besloten elite-/coördinatieforum | Bilderberg Groep, World Economic Forum |
| `denktank` | Onderzoeks-/beleidsinstituut | Clingendael, HCSS |
| `overheidsinstelling` | Overheidsorgaan | Belastingdienst, WRR |
| `toezichthouder` | Toezichthoudend orgaan | ACM, Commissariaat voor de Media |
| `partij` | Politieke partij | VVD, CDA, PVV |
| `platform` | Digitaal platform | Google, Meta, TikTok |
| `pr_bureau` | Communicatie-/PR-bureau | — |
| `ngo`, `vakbond`, `onderwijsinstelling`, `burgerinitiatief`, `rechterlijke_macht`, `lobbygroep` | Maatschappelijke en tegenmacht-actoren | NVJ, vakbonden, universiteiten |

## Relatietypes

De volledige lijst staat in de `CHECK`-constraint van `relations` in `schema.sql`, gegroepeerd:

| Groep | Types |
|---|---|
| **Eigendom & financiën** | `eigendom`, `financiering`, `adverteerder`, `donor`, `investering` |
| **Organisatorisch** | `lidmaatschap`, `personeel`, `bestuurder`, `adviseur`, `woordvoerder_van`, `draaideur` |
| **Informatiestromen** | `bron_van`, `mediaplatform`, `framing`, `citeert` |
| **Macht & druk** | `lobbyt`, `censuur`, `flak`, `intimidatie`, `regulering`, `zelfcensuur` |
| **Politiek & ideologisch** | `alliantie`, `oppositie`, `beinvloeding`, `cooptatie`, `etikettering` |
| **Algoritmisch** | `algoritmische_filtering` |

Meest gebruikt: `beinvloeding` (151), `eigendom` (51), `adverteerder` (40), `lidmaatschap` (24), `personeel` (16), `draaideur` (14).

---

## Projectstructuur

```
propaganda-model/
├── schema.sql                          # Databaseschema (alle tabellen)
├── DOCUMENTATIE.md                     # Dit bestand
├── server.py                           # Flask: discussieboom-API + visualisatie op /
├── .gitignore                          # Negeert data/*.db, __pycache__, etc.
│
├── data/
│   └── propaganda_model.db             # SQLite database (niet in git)
│
├── web/
│   ├── template.html                   # BRON van de D3-visualisatie (handmatig bewerken)
│   └── index.html                      # GEGENEREERD door generate_viz.py (niet bewerken)
│
├── scripts/
│   ├── init_db.py                      # Database aanmaken vanuit schema.sql
│   ├── seed_theoretical_model.py       # Basis: rollen + mechanismen (laag 1)
│   ├── seed_from_ai_source.py          # Basis: entiteiten + relaties (laag 2)
│   ├── seed_draaideur_relaties.py      # Extra draaideur-relaties
│   ├── enrich_*.py                     # Verrijken van een bestaande DB (theorie + instanties)
│   ├── migrate_*.py                    # Schema-/datamigraties (backup-then-migrate)
│   ├── set_temporal_data.py            # Vult active_from/active_until op entiteiten/relaties
│   ├── generate_viz.py                 # Regenereert web/index.html uit de DB
│   └── register_source.py              # Registreer een academische bron via CLI
│
└── sources/                            # Bronmateriaal (teksten, transcripts)
    ├── README.md                       # Uitleg over bronmateriaal en naamgeving
    ├── AI/                             # AI-gegenereerde analyses
    │   └── propagandsmodel2.md         # Hoofdbron: "De Onzichtbare Architecten"
    ├── transcripts/                    # Uitgeschreven audio/video
    ├── articles/                       # Nieuwsartikelen, columns
    └── interviews/                     # Interview-transcripts
```

> De `seed_*`-scripts leggen de basis; de huidige DB-inhoud is daarna uitgebreid via de `enrich_*`- en `migrate_*`-scripts. Een volledige reconstructie draait dus seed → enrich → migrate (de migratiescripts maken telkens een backup `data/propaganda_model_backup_<timestamp>.db`).

---

## Gebruik

### Database opzetten

```bash
# Database aanmaken (verwijder eerst bestaande als je wilt herbeginnen)
rm -f data/propaganda_model.db
python3 scripts/init_db.py

# Theoretisch model laden (rollen + mechanismen)
python3 scripts/seed_theoretical_model.py

# Entiteiten en relaties laden uit bronanalyse
python3 scripts/seed_from_ai_source.py
```

### Bronnen registreren

```bash
python3 scripts/register_source.py \
    "Manufacturing Consent" \
    boek \
    "Herman, E.S. & Chomsky, N." \
    "Pantheon Books" \
    "1988-01-01"
```

### Queries

```sql
-- Alle relaties van een entiteit met scores
SELECT e1.name, r.relation_type, e2.name, r.certainty, r.influence
FROM relations r
JOIN entities e1 ON r.source_id = e1.id
JOIN entities e2 ON r.target_id = e2.id
WHERE e1.name = 'DPG Media'
ORDER BY r.influence DESC;

-- Alle argumenten bij een relatie, met citaties
SELECT a.stance, a.claim, a.weight, s.author, s.title, c.quote, c.page
FROM arguments a
LEFT JOIN citations c ON c.argument_id = a.id
LEFT JOIN sources s ON c.source_id = s.id
WHERE a.relation_id = 5
ORDER BY a.stance;

-- Meest verbonden entiteiten
SELECT e.name, e.type, COUNT(DISTINCT r.id) as relaties
FROM entities e
LEFT JOIN relations r ON e.id = r.source_id OR e.id = r.target_id
GROUP BY e.id
ORDER BY relaties DESC
LIMIT 10;

-- Relaties per filter/mechanisme
SELECT m.filter, m.name, COUNT(r.id) as aantal
FROM relations r
JOIN mechanisms m ON r.mechanism_id = m.id
GROUP BY m.filter, m.name
ORDER BY m.filter, aantal DESC;

-- Onzekere relaties met hoge invloed (onderzoeksprioriteit)
SELECT e1.name, r.relation_type, e2.name, r.certainty, r.influence
FROM relations r
JOIN entities e1 ON r.source_id = e1.id
JOIN entities e2 ON r.target_id = e2.id
WHERE r.certainty < 0.75 AND r.influence >= 0.55
ORDER BY r.influence DESC;

-- Alle bronnen met hun locaties
SELECT s.title, s.author, sl.location_type, sl.location
FROM sources s
LEFT JOIN source_locations sl ON sl.source_id = s.id
ORDER BY s.author;
```

---

## Huidige inhoud

| Onderdeel | Aantal |
|---|---|
| Rollen (theoretisch) | 30 |
| Mechanismen (theoretisch) | 85 |
| Entiteiten (concreet) | 121 |
| Relaties (concreet) | 337 |
| Argumenten | 316 |
| Citaties | 3 |
| Bronnen | 5 |
| Bronlocaties | 3 |

> Let op: de meeste argumenten zijn automatisch gegenereerde `supporting`-onderbouwingen met status `ongecontroleerd` en nog grotendeels zonder citatie. Het aanvullen van citaties en het controleren van argumentstatus is openstaand werk.

### Top 10 meest verbonden entiteiten

| Entiteit | Type | Relaties |
|---|---|---|
| DPG Media | mediaorganisatie | 46 |
| NOS | omroep | 43 |
| Mediahuis | mediaorganisatie | 34 |
| RTL Nederland | omroep | 33 |
| de Volkskrant | mediaorganisatie | 28 |
| De Telegraaf | mediaorganisatie | 24 |
| AD (Algemeen Dagblad) | mediaorganisatie | 17 |
| ANP | persbureau | 16 |
| Bilderberg Groep | elite_netwerk | 15 |
| World Economic Forum | elite_netwerk | 15 |

---

## Hoe het model uitbreiden

### Nieuwe bron toevoegen

1. Plaats het bestand in `sources/` (juiste submap)
2. Registreer de bron: `python3 scripts/register_source.py "Titel" type "Auteur"`
3. Voeg locaties toe (URL, DOI, ISBN) via SQL of een script
4. Analyseer de tekst en voeg entiteiten, relaties en argumenten toe

### Argument toevoegen aan een relatie

```sql
-- 1. Root-argument op een relatie
INSERT INTO arguments (relation_id, stance, claim, reasoning, weight)
VALUES (42, 'contradicting',
        'De Volkskrant publiceerde kritisch Shell-dossier',
        'Als zelfcensuur dominant was, zou dit dossier niet gepubliceerd zijn.',
        0.40);

-- 2. Voeg citatie(s) toe
INSERT INTO citations (argument_id, source_id, quote, page, section)
VALUES (last_insert_rowid(), 3,
        'Het onderzoeksteam werkte zes maanden aan het dossier',
        'pp. 12-15',
        'Redactioneel verantwoording');
```

### Reactie op een bestaand argument (discussieboom)

```sql
-- Tegenargument op argument #15
INSERT INTO arguments (relation_id, parent_argument_id, stance, claim, reasoning, weight)
VALUES (42, 15, 'supporting',
        'Dit was een uitzondering die de regel bevestigt',
        'Het Shell-dossier was het enige kritische stuk in 5 jaar. Structurele zelfcensuur sluit incidentele doorbraken niet uit.',
        0.55);
```

### Argument over een entiteit

```sql
-- Bewering over een entiteit (bijv. "Is DPG Media een monopolist?")
INSERT INTO arguments (entity_id, stance, claim, reasoning, weight)
VALUES (1, 'supporting',
        'DPG bezit >60% van de online commerciële nieuwsmarkt',
        'Volgens ACM marktanalyse 2023 is DPG de dominante speler.',
        0.80);
```

### Certainty herberekenen

De `certainty` op een relatie kan periodiek worden herberekend als gewogen balans van alle supporting vs contradicting argumenten:

```sql
-- Voorbeeld: gemiddelde weight per stance voor een relatie
SELECT
    relation_id,
    AVG(CASE WHEN stance = 'supporting' THEN weight END) as avg_support,
    AVG(CASE WHEN stance = 'contradicting' THEN weight END) as avg_contra,
    COUNT(CASE WHEN stance = 'supporting' THEN 1 END) as n_support,
    COUNT(CASE WHEN stance = 'contradicting' THEN 1 END) as n_contra
FROM arguments
GROUP BY relation_id
HAVING n_contra > 0;
```

---

## Theoretische basis

| Werk | Auteur | Bijdrage |
|---|---|---|
| *Manufacturing Consent* (1988) | Herman & Chomsky | De vijf filters van het propagandamodel |
| *De Nederlandse Nieuwsfabriek* (2014) | Tabe Bergman | Toepassing op het Nederlandse medialandschap |
| *Je hebt het niet van mij, maar...* (2010) | Joris Luyendijk | Etnografie van de Haagse "stam" (Filter 3) |
| *The Making of an Atlantic Ruling Class* (1984) | Kees van der Pijl | Transnational Capitalist Class theorie |
| *Quaderni del Carcere* (1935) | Antonio Gramsci | Culturele hegemonie (Filter 5) |
| *Aandacht voor media* (2024) | WRR | Institutionele erkenning van de crisis |
