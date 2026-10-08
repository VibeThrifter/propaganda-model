# Missie-brief: nieuws-bewijs (dun bewijs — verbanden uit het nieuws toetsen)

**Account:** `nieuws-bewijs` (Bearer-token in `data/tokens/nieuws-bewijs.token`, rol bijdrager).
**Opdrachtgever:** de wachtrij `nieuws_doelen`, soort `relatie`, gevuld door de
nieuws-aggregator (account `nieuws-agent`, Story 14.13 "dun bewijs").
**Doel:** per doel uitzoeken **wat er werkelijk vóór en tegen één verband pleit**. Dat
voorstel je via het gewone bijdragepad. Een lezer van de nieuws-app moet zien waarop het
verband rust.

Waar dit vandaan komt: de nieuws-app toont bij elk nieuwsbericht "Wie zit erachter?",
met verbanden uit dit model tussen de partijen in het nieuws en de media die erover
schrijven. Veel van die verbanden rusten op één argument met één bron. Soms is die bron
het persbericht van de partij zelf, die laat zien wat de partij zegt en niet wat het medium
ermee deed. Soms is niets gecontroleerd. De app toont zo'n verband als **dun bewijs**,
zet het als doel in deze wachtrij en meldt de lezer "wordt uitgezocht".

> **Je bewijst het verband niet; je toetst het.** "Dun" kan twee kanten op uitvallen:
> steviger dan nu, of zwakker. Beide uitkomsten zijn even waardevol. Een verband dat na
> een brede zoektocht op één persbericht blijft rusten, is óók een uitkomst.

**Lees eerst volledig:**
- `missies/documentalist_brief.md`: het anti-overfit-protocol, verplicht. Neutrale
  zoekvraag, gelogde queries, tweezijdige oogst, negatieve resultaten alleen in het log.
- `missies/monitor_brief.md`: het verschil tussen **ondergraving** en **weerlegging**.
- De agent-contract-sectie van `CLAUDE.md`: stance volgt het effect op de claim, elke
  supporting/contradicting root heeft een echte citatie, geen Wikipedia als bron.

Alles daaruit geldt onverkort. Deze brief voegt alleen de wachtrij en de afbakening toe.

## De ronde

**Maximaal 2 doelen per ronde.** Bewijsonderzoek is zwaarder dan een naam opzoeken.

1. **Claimen.** Doe `POST /api/nieuws/doelen/claim_volgende?soort=relatie&limit=2` met
   je Bearer-token. Je krijgt `{"doelen": [...]}` terug. Is de lijst leeg, log dan
   "geen open doelen" en rond af; een lege oogst is prima. Elk doel heeft:
   - `sleutel` (`relatie:<id>`), `relation_id` en `naam` (het verband als zin, zoals
     de lezer het ziet);
   - `context`:
     - `events` en `artikelen`: de nieuwsberichten waarin de lezer het verband zag,
       met url, bron, titel en datum. Die zijn vaak het beste startpunt.
     - `bewijs`: de huidige onderbouwing in één regel, bv. "1 bron: persbericht van
       PBL zelf · niet gecontroleerd".
     - `ontbreekt`: wat de app mist, bv. "een onafhankelijke bron", "controle".
2. **Werk elk doel af** met de stappen hieronder.
3. **Sluit elk doel af** met een PATCH (stap 6), ook bij `niets_gevonden` of `twijfel`.
   Een geclaimd doel dat je niet afmaakt (tijd op, fout) zet je op `fout` met een
   korte reden. Blijft het `bezig`, dan komt het na 3 uur vanzelf terug.

> De runner-prompt zegt "je zet NOOIT statussen". Dat gaat over **modelstatussen**:
> mergen, goedkeuren, afwijzen, classificeren. De status van een **wachtrij-doel**
> (`PATCH /api/nieuws/doelen/<id>`) is procesadministratie en hoort bij deze missie.

### Stap 1 — Wat beweert het model precies?

Lees het verband en de hele discussieboom:

```bash
sqlite3 "file:data/propaganda_model.db?mode=ro" "SELECT r.id, s.name, t.name, r.relation_type, \
  m.id, m.name, m.description, r.description FROM relations r JOIN entities s ON s.id = r.source_id \
  JOIN entities t ON t.id = r.target_id LEFT JOIN mechanisms m ON m.id = r.mechanism_id WHERE r.id = <id>"
curl -s "http://localhost:5000/api/arguments?relation_id=<id>"
```

- Formuleer de claim in één zin, met de definitie van het mechanisme ernaast: wat moet
  er waar zijn als het verband klopt? Wat zou ertegen pleiten?
- Noteer per bestaand argument de claim, de status, de bronnen en de quotes.

### Stap 2 — Toets het bestaande bewijs

Doe dit voor elk **supporting** root-argument, behalve de id's uit
`GET /api/agent/reeds_gereageerd`:

- Open elke bron en controleer of het citaat er **letterlijk** staat.
- Vraag je vervolgens af of de bron de claim draagt. Een veelvoorkomend gat: de bron laat
  zien wat partij X zegt (een persbericht, een rapport), terwijl de claim gaat over wat
  medium Y deed (X als gezaghebbend brengen, zonder tegenstem).
- Draagt de bron de claim niet, of staat het citaat er niet, dien dan een
  **ondergraving** in: een `contradicting` reactie op dat argument, met `reasoning` die
  precies de stap noemt die niet klopt. Bijvoorbeeld: "de bron is het persbericht van PBL
  zelf; het laat niet zien hoe NOS het bracht". Een tegenbron hoeft niet. Op elk argument
  reageer je hooguit één keer.

### Stap 3 — Zoek bewijs vóór én tegen

Formuleer de zoekvraag neutraal: *"Hoe bracht NOS de klimaatverkenningen van het PBL?"*,
niet *"zoek bewijs dat NOS PBL napraat"*. Besteed evenveel moeite aan de andere kant.

- **Primair bewijs voor sourcing- en expertverbanden.** Begin bij de berichtgeving van het
  medium zelf, over meerdere jaren en niet één optreden:
  - Wordt X als gezaghebbende bron gebracht?
  - Komt er een andere deskundige of tegenstem aan het woord?
  - Gaat het om een kop of een kernbron?

  De `artikelen` uit de context zijn een startpunt, geen steekproef. Zoek ook verder dan
  het huidige nieuws. Daarnaast tellen:
  - inhoudsanalyses en ander wetenschappelijk onderzoek naar het bronnengebruik van het
    medium;
  - rapporten van de ombudsman (NPO, de Volkskrant, NRC, …);
  - mediakritiek (Villamedia, De Nieuwe Reporter);
  - voor structurele afhankelijkheid: jaarverslagen, contracten, abonnementen (bv. op ANP).
- **Een patroon, geen anekdote.** Eén bericht is geen sourcing-patroon. Een
  invloedsclaim heeft een gedocumenteerd patroon nodig: meerdere onafhankelijke
  berichten of jaren, of een studie. Verschillende berichten van hetzelfde medium tellen
  als één broncluster (`cluster`).
- **Tegenbewijs.** Zoek bijvoorbeeld:
  - berichten waarin het medium X kritisch bevraagt of corrigeert;
  - berichten waarin andere deskundigen het oneens zijn met X;
  - studies die geen afhankelijkheid vinden;
  - ombudsmanoordelen die het medium vrijpleiten.
- **De eigen woorden van X** (persbericht, jaarverslag) zijn bewijs van wat X zegt of
  doet. Ze zijn géén bewijs van wat het medium doet. Gebruik ze alleen waarvoor ze
  bewijzen.
- Wikipedia is alleen een vindplaats: citeer de onderliggende bron. Controleer elke quote
  letterlijk op de pagina zelf. Nooit fabriceren; wat je niet kunt staven, dien je niet in.

### Stap 4 — Past het mechanisme?

Lees de definitie van het mechanisme in het model. Twee voorbeelden waarbij een ander,
**bestaand** mechanisme beter kan passen:
- `expert_framing` beschrijft experts van denktanks die door sponsors betaald worden; een
  planbureau van de overheid is iets anders.
- `bron_afhankelijkheid` gaat over structureel leunen op één bron, niet over één keer
  citeren.
- Sinds 2026-10-07 hoort ook de besluitvorming in het model (categorieën `formele_macht`,
  `belangen`, `kennis_advies`, `polder`, `werving`, naast de vijf filters): een ambt, een
  nevenfunctie, een adviesrol of een benoeming heeft een eigen mechanisme
  (`lokaal_bestuursmandaat`, `nevenfunctie_verstrengeling`, `institutioneel_advies`,
  `kroonbenoeming`, …) en is geen reden om een verband "buiten het model" te noemen.
  Een registerfeit (citaat = recordregel, methode `officieel_register_scrape`) is al
  deterministisch gecontroleerd; daar hoef je geen tweede bron voor te zoeken.

Past een ander mechanisme beter, dien dan een **aspect-argument** in op de relatie:
`property: "mechanism"`, `property_value` = het id van dat mechanisme, en een `reasoning`
die het verschil met de definitie noemt. Het telt niet in de zekerheid; een mens beslist.
Verzin nooit een nieuw mechanisme: de theorielaag loopt via een RfC.

### Stap 5 — Indienen (alles `voorgesteld`)

Gebruik een manifest voor `scripts/scout_indienen.py`, met alleen `bronnen` en
`argumenten`. Je maakt **geen** entiteiten of relaties aan.

```json
{
  "bronnen": [{"key": "nos-2024-kev", "titel": "...", "type": "nieuwsartikel",
               "publisher": "NOS", "datum": "2024-10-24", "url": "https://nos.nl/...",
               "cluster": "nos", "onderwerp": "nl_systeem",
               "betrouwbaarheid": "kwaliteitsjournalistiek"}],
  "argumenten": [
    {"doel": {"relation_id": 1564}, "stance": "supporting", "claim": "...",
     "bron": "nos-2024-kev", "quote": "<letterlijk>"},
    {"doel": {"relation_id": 1564}, "stance": "contradicting", "claim": "...",
     "bron": "...", "quote": "<letterlijk>"},
    {"doel": {"parent_argument_id": 2322}, "stance": "contradicting",
     "claim": "De bron draagt de claim niet", "reasoning": "<de precieze stap>"},
    {"doel": {"relation_id": 1564}, "stance": "supporting", "property": "mechanism",
     "property_value": 123, "claim": "...", "reasoning": "..."}
  ]
}
```

```bash
python3 scripts/scout_indienen.py data/scout/bewijs-relatie-<id>.json                       # droog
python3 scripts/scout_indienen.py data/scout/bewijs-relatie-<id>.json --indienen \
    --token data/tokens/nieuws-bewijs.token --resultaat-json data/scout/bewijs-relatie-<id>.resultaat.json
```

- `betrouwbaarheid` en `onderwerp` zijn een **voorstel** (`reliability_voorgesteld`/
  `onderwerp_voorgesteld`): eerlijk invullen, de reviewer beslist. Klassen staan in
  `RELIABILITY_KLASSEN` (server.py); het eigen persbericht van een partij is `primair`
  voor wat die partij zegt.
- **De stance volgt het effect op de claim van het verband**, niet je sympathie.
  Tegenbewijs is een eigen `contradicting` root mét bron, en nooit een "maar"-zin in een
  supporting argument.
- **Gaat het bewijs over hoe sterk de invloed is** (en niet over of het verband bestaat)?
  Gebruik dan `property: "influence"`.
- **Formuleer neutraal en met attributie.** Goed: "NOS bracht de KEV 2024 met PBL als
  enige geciteerde deskundige (3 van 3 berichten op 24 oktober)", "Volgens de
  ombudsman …". Geen eigen oordeel, geen motieven, geen "napraten" of "spreekbuis".
  Nooit een negatieve claim over een **persoon**: de smaad-firewall houdt die toch tegen.
- Zet geen certainty of influence (0,05-vloer). Een 409 (duplicaat) of 400 is
  informatie: log hem en ga door. Gebruik nooit `negeer_duplicaten` om er doorheen te
  duwen.

### Stap 6 — Het doel afsluiten en loggen

```bash
curl -s -X PATCH http://localhost:5000/api/nieuws/doelen/<id> \
  -H "Authorization: Bearer $(cat data/tokens/nieuws-bewijs.token)" -H "Content-Type: application/json" \
  -d '{"status": "klaar", "verslag": "<kort, neutraal>",
       "resultaat": {"source_ids": [..], "argument_ids": [..]}}'
```

| Status | Wanneer |
|---|---|
| `klaar` | Je diende ≥1 argument of ondergraving in, vóór of tegen. |
| `niets_gevonden` | Breed gezocht (queries in het log), niets wat te staven is. Niets ingediend. |
| `twijfel` | Het bewijs spreekt elkaar tegen of het verband is onduidelijk; een mens moet kijken (zeg in het verslag waarom). |
| `overgeslagen` | Het verband bestaat niet meer, is vervangen of valt buiten het model. |
| `fout` | Technisch vastgelopen (API-fout, tijd op). |

- **`verslag`**: 1–4 zinnen, neutraal. Wat houdt stand, wat niet, en waarop rust dat?
  Bijvoorbeeld: "Argument #2322 rust op het persbericht van PBL zelf (ondergraving #…).
  Gevonden: 3 NOS-berichten 2023–2024 met PBL als enige deskundige (steun #…), 2 met
  kritiek van CPB/TNO (tegen #…). Mechanisme past mogelijk beter bij … (#…)." De
  nieuws-app toont dit verslag niet. Het is voor de mens die beoordeelt.
- **`resultaat`**: alleen `source_ids` en `argument_ids`, dus wat jíj in deze ronde
  aanmaakte. Nooit `entity_ids`/`relation_ids`: je maakt geen knopen of verbanden aan.
- **Log de ronde** in het logbestand dat de runner noemt
  (`missies/logs/<datum>_nieuws-bewijs_<ronde>.md`). Zet erin:
  - de brief-hash, en per doel de sleutel en de status;
  - de neutrale zoekvraag, en élke zoekopdracht letterlijk;
  - per vondst het source-/argument-id;
  - de **negatieve resultaten** (alleen hier, nooit als modelbijdrage);
  - de stance-balans (n steun / n tegen / n context / n ondergraving).

## Wat er daarna gebeurt

Alles wat je indient landt `voorgesteld`. Direct na je ronde beslist de **automatische
beoordeling** (`scripts/automatische_beoordeling.py`, eigenaarsbesluit 2026-10-06: niemand
beoordeelt met de hand):

1. de **bronchecker** haalt elke bron opnieuw op, zoekt je citaat letterlijk terug en laat een
   model oordelen of de bron je bewering *zoals jij die formuleerde* draagt;
2. de **aanklager** probeert elke invloedsclaim te weerleggen;
3. wat beide doorstaat, merget de immuunpoort. Wat de bron niet draagt, wordt verworpen. Wat
   na 14 dagen niet te bevestigen is, wordt opgeruimd.

Pas daarna ziet de lezer van de nieuws-app je bewijs. **Schrijf dus voor die controle:**
- het citaat staat letterlijk op de pagina van de url;
- de bewering zegt niet meer dan de bron. "De kop noemt PBL", terwijl de kop dat niet doet,
  wordt "twijfel" en telt niet;
- één bewering per argument.

## Harde grenzen

- Nooit mergen, goedkeuren, afwijzen, classificeren of verwijderen. Je hebt er het token
  ook niet voor.
- Geen entiteiten en geen relaties aanmaken. Hoort er volgens je een ander verband bij,
  zet dat dan in het verslag.
- Geen nieuwe rollen of mechanismen; de theorielaag loopt via een RfC.
- Nooit meer dan 2 doelen per ronde.
- Op elk argument reageer je hooguit één keer (`reeds_gereageerd`; de server geeft 409).
- Negatieve resultaten komen alleen in het log, nooit als `contextual`-bijdrage.
- Niets over privézaken van personen.
- Rate-limit **429** op een inhouds-endpoint: stop de ronde en log het. De
  wachtrij-endpoints zelf hebben geen rate limit.
