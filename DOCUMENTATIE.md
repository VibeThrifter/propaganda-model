# Propagandamodel Nederlandse Politiek & Media

## Doel

Dit project modelleert de structurele mechanismen waarmee nieuws in Nederland wordt gefilterd en gevormd voordat het het publiek bereikt. Het is gebaseerd op het propagandamodel van Herman & Chomsky (*Manufacturing Consent*, 1988), toegepast op de Nederlandse context met behulp van het werk van Tabe Bergman, Joris Luyendijk, Kees van der Pijl en anderen.

Het model is geen complottheorie. Het beschrijft hoe structurele krachten — eigendom, economische druk, bronafhankelijkheid, disciplinering en ideologie — leiden tot een systematische pro-elite bias als *emergente eigenschap* van het systeem, zonder dat er sprake hoeft te zijn van centrale sturing.

---

## Architectuur: twee lagen

Het systeem onderscheidt twee lagen:

### Laag 1: Theoretisch model (abstract, zonder namen)

Beschrijft de structuur: welke **rollen** bestaan er in het medialandschap en via welke **mechanismen** oefenen ze invloed uit?

- **Rollen** — abstracte functies die actoren kunnen vervullen (bijv. `mediaeigenaar`, `adverteerder`, `gatekeeper`)
- **Mechanismen** — processen waarmee de ene rol de andere beïnvloedt (bijv. `pakketjournalistiek`, `etikettering`, `zelfcensuur`)

Elk mechanisme is gekoppeld aan een van de vijf filters van het propagandamodel, plus een categorie `overig` voor moderne fenomenen zoals algoritmische filtering.

### Laag 2: Instantiemodel (concreet, met namen)

De echte entiteiten en relaties in Nederland:

- **Entiteiten** — concrete actoren met naam en toenaam (bijv. DPG Media, Thomas Leysen, Bilderberg Groep)
- **Relaties** — concrete verbanden tussen entiteiten (bijv. DPG Media bezit de Volkskrant)

Elke entiteit is gekoppeld aan een of meer rollen uit het theoretisch model. Elke relatie is optioneel gekoppeld aan een mechanisme.

---

## De vijf filters + uitbreidingen

### Filter 1: Eigendom
De eigendomsstructuur bepaalt de institutionele context van nieuwsproductie. In Nederland bestaat een duopolie: DPG Media en Mediahuis bezitten samen >90% van de online commerciële nieuwsmarkt. De eigenaren (families Van Thillo, Leysen, Baert, Van Puijenbroek) behoren tot de transnationale kapitaalklasse.

**Rollen:** `mediaeigenaar`, `mediaorganisatie_rol`, `aandeelhouder`, `institutioneel_belegger`
**Mechanismen:** `eigendomsconcentratie`, `winstmaximalisatie`

### Filter 2: Advertentie
Media zijn financieel afhankelijk van adverteerders, wat een structurele voorkeur creëert voor content die het consumentistische wereldbeeld bevestigt.

**Rollen:** `adverteerder`, `mediaverkoper`
**Mechanismen:** `advertentiedruk`, `commerciele_afhankelijkheid`, `supportive_selling_environment`

### Filter 3: Sourcing
Economische druk dwingt redacties tot afhankelijkheid van een beperkt aantal routineuze bronnen: het ANP, de overheid, en door de elite gefinancierde denktanks.

**Rollen:** `officiele_bron`, `persbureau`, `expert_bron`, `pr_machine`
**Mechanismen:** `bron_afhankelijkheid`, `pakketjournalistiek`, `expert_framing`, `pr_subsidie`

### Filter 4: Flak
Disciplineringsmechanismen die journalisten ontmoedigen om van de geaccepteerde lijn af te wijken: juridische dreiging, publieke aanvallen, etikettering, en interne zelfcensuur.

**Rollen:** `flak_producent`, `flak_doelwit`
**Mechanismen:** `juridische_dreiging`, `publieke_aanval`, `deplatforming`, `etikettering`, `zelfcensuur`, `geweld_intimidatie`

### Filter 5: Ideologie
Het overkoepelende filter: een neoliberaal, pro-Atlantisch denkkader dat als "gezond verstand" wordt gepresenteerd (Gramsci's culturele hegemonie). Elite-fora synchroniseren dit wereldbeeld buiten het democratisch proces om.

**Rollen:** `ideoloog`, `gatekeeper`, `elite_forum`
**Mechanismen:** `overton_bewaking`, `false_balance`, `draaideurconstructie`, `ideologische_synchronisatie`, `hegemonische_naturalisatie`

### Overig (modern)
Fenomenen die niet in het originele model van 1988 voorkomen maar essentieel zijn voor het huidige medialandschap.

**Rollen:** `techplatform`, `toezichthouder`, `burger`, `klokkenluider`
**Mechanismen:** `algoritmische_filtering`

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
| `roles` | Abstracte rollen in het medialandschap | name, category (filter), description, examples |
| `mechanisms` | Processen waarmee rollen invloed uitoefenen | name, filter, description, effect, source_role_id, target_role_id |

### Instantiemodel

| Tabel | Beschrijving | Velden |
|---|---|---|
| `entities` | Concrete actoren (personen, organisaties, partijen) | name, type, primary_role_id, description, metadata (JSON) |
| `entity_roles` | Koppeltabel: entiteit kan meerdere rollen vervullen | entity_id, role_id, notes |
| `relations` | Concrete relaties tussen entiteiten | source_id, target_id, relation_type, mechanism_id, certainty, influence |
| `source_mentions` | Welke entiteiten worden in welke bronnen genoemd | source_id, entity_id, context |

### Bronnen (academisch)

| Tabel | Beschrijving | Velden |
|---|---|---|
| `sources` | Academische bronnen (boeken, artikelen, rapporten) | title, author, source_type, publisher, date_published, language |
| `source_locations` | Meerdere toegangspunten per bron | source_id, location_type (url/file/doi/isbn/arxiv/handle/archive_url), location |

### Argumenten & citaties (discussieboom)

| Tabel | Beschrijving | Velden |
|---|---|---|
| `arguments` | Discussieboom: argumenten op relaties of entiteiten, met nesting | relation_id (optioneel), entity_id (optioneel), parent_argument_id (NULL=root), stance, claim, reasoning, weight |
| `citations` | Bronvermeldingen per argument | argument_id, source_id, quote, page, section, context |

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

| Type | Beschrijving | Voorbeelden |
|---|---|---|
| `mediaorganisatie` | Nieuwsproducent of -distributeur | DPG Media, NOS, ANP, De Telegraaf |
| `persoon` | Individu met specifieke rol | Christian Van Thillo, Thomas Leysen, Tabe Bergman |
| `bedrijf` | Commercieel bedrijf | BlackRock, Shell, Albert Heijn, McKinsey |
| `lobbygroep` | Belangenorganisatie of elite-forum | Bilderberg Groep, WEF, NAVO |
| `denktank` | Onderzoeks-/beleidsinstituut | Clingendael, HCSS, Teldersstichting |
| `overheidsinstelling` | Overheidsorgaan of toezichthouder | ACM, WRR, Belastingdienst |
| `partij` | Politieke partij | VVD, CDA, PVV |
| `politicus` | Individueel politicus | Pieter Omtzigt, Renske Leijten |
| `journalist` | Individueel journalist | Peter R. de Vries, Ron Fresen |
| `platform` | Digitaal platform | Google, Meta, TikTok, NU.nl |
| `ngo` | Non-gouvernementele organisatie | Free Press Unlimited, NVJ, BOinK |

## Relatietypes

| Type | Beschrijving |
|---|---|
| `eigendom` | A bezit B |
| `financiering` | A financiert B |
| `lidmaatschap` | A is lid van B (of B van A) |
| `adverteerder` | A adverteert bij B |
| `beinvloeding` | A beïnvloedt B (structureel) |
| `censuur` | A censureert/onderdrukt B |
| `personeel` | A is in dienst/bestuur van B |
| `alliantie` | A en B werken samen |
| `oppositie` | A en B staan tegenover elkaar |
| `draaideur` | Personeel wisselt tussen A en B |
| `framing` | A bepaalt het frame waarmee B wordt begrepen |
| `lobbyt` | A lobbyt bij B |
| `adviseur` | A adviseert B |
| `donor` | A doneert aan B |
| `mediaplatform` | A gebruikt B als mediakanaal |

---

## Projectstructuur

```
propaganda-model/
├── schema.sql                          # Databaseschema (alle tabellen)
├── DOCUMENTATIE.md                     # Dit bestand
├── .gitignore                          # Negeert data/*.db, __pycache__, etc.
│
├── data/
│   └── propaganda_model.db             # SQLite database (niet in git)
│
├── scripts/
│   ├── init_db.py                      # Database aanmaken vanuit schema.sql
│   ├── seed_theoretical_model.py       # Laad 19 rollen en 21 mechanismen
│   ├── seed_from_ai_source.py          # Laad 81 entiteiten en 105 relaties uit AI-analyse
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
| Rollen (theoretisch) | 19 |
| Mechanismen (theoretisch) | 21 |
| Entiteiten (concreet) | 81 |
| Relaties (concreet) | 105 |
| Argumenten | 107 |
| Citaties | 108 |
| Bronnen | 6 |
| Bronlocaties | 4 |

### Top 10 meest verbonden entiteiten

| Entiteit | Type | Relaties |
|---|---|---|
| DPG Media | mediaorganisatie | 25 |
| NOS | mediaorganisatie | 17 |
| Mediahuis | mediaorganisatie | 14 |
| ANP | mediaorganisatie | 10 |
| Thomas Leysen | persoon | 7 |
| Bilderberg Groep | lobbygroep | 7 |
| Belastingdienst | overheidsinstelling | 7 |
| de Volkskrant | mediaorganisatie | 6 |
| RTL Nederland | mediaorganisatie | 5 |
| Christian Van Thillo | persoon | 4 |

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
