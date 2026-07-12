# Voorstel — tegenmacht van universele categorie naar gerichte edge-valentie

*Status: **doorgevoerd** (juli 2026, tak `modelreview-eigendom-tegenmacht`). De capability staat er — de spec-herkadering (DOCUMENTATIE.md § "Uitbreiding B: Tegenmacht"), het `machtsvalentie`-aspect (property + CHECK + poort + `ASPECT_PROPERTIES`), de afleiding `tegenmacht.py` + `GET /api/machtsvalentie`, de validator-backstop en `scripts/test_machtsvalentie.py`. **Viz-overlay nu óók gebouwd:** `tegenmacht.py` levert naast de actor-aggregatie een netto valentie per relatie én mechanisme (`teken` +1 opent / −1 sluit / 0), `viz_data.py`/`GET /api/graph_data` exporteert `machtsvalentie` (actoren + relaties + mechanismen), de viz heeft (1) een **detailpaneel-overlay** per actor (contra-hegemonie-balken per as + verantwoordt-chips, naast de kleurmeter) en (2) een **edge-selectie** in 'Systemische effecten' — checkboxes *Positief — opent* (groen), *Negatief — sluit* (rood), *Verantwoording* (blauw) tonen alléén die edges in valentie-kleur (werkt in beide modellen). Nog niet gebouwd: de eerste inhoudelijke `machtsvalentie`-signalen (content → via het `assistent`-pad, `voorgesteld`, mét bron). Geen data-sloop: de 17 bestaande tegenmacht-mechanismen behielden hun filter.*

## Kernprobleem

`tegenmacht` is nu een **filter-waarde** (naast eigendom/advertentie/sourcing/flak/ideologie), dus een *universele categorie* die je op een mechanisme — en via de afgeleide primaire rol impliciet op een entiteit — plakt. Maar tegenmacht is intrinsiek een **tweeplaatsig predicaat**: `tegenmacht(X, doel)`. Je kunt het niet aflezen zonder het doel te noemen, want in een veld van meerdere machtsblokken *dient* het tegenwerken van blok B vaak blok A — dezelfde kracht is dan tegelijk tegenmacht én promacht, afhankelijk van de as.

Het model erkent de multipolariteit al elders: emergent veld `consensuscalibratie` (14) maakt de *mate van onderlinge consensus tussen meerdere machtscentra* tot regelknop op de filters, en `schijnpluriformiteit` (6) zegt dat de resterende pluriformiteit begrensd is. Alleen bij `tegenmacht` is die multipolariteit niet doorgetrokken: daar leeft nog het bipolaire "elite vs. de-goede-tegenkracht"-frame.

De huidige 17 tegenmacht-mechanismen (toezicht, klokkenluider, onderzoeksjournalistiek, redactiestatuut, parlementaire controle, ledenraad, vakbond, borgingsstichting…) voelen tóch coherent, omdat ze allemaal één impliciet doel delen: **de verantwoording van geconcentreerde macht**. Die coherentie is *geleend* van dat gedeelde doel en verdampt zodra het doel varieert — precies wat gebeurt als je "tegenmacht" wil uitbreiden naar factie-insurgentie (FvD c.s.).

## De sleutel: het conflateert twee verschillende "tegen"-relaties

| | **1. Verantwoording** | **2. Contra-hegemonie** |
|---|---|---|
| Tegen wát | een **filter-machtsconcentratie** (eigendom, flak, …) | een **genaturaliseerde positie op een politieke as** (de consensusvloer) |
| Voorbeeld | borgingsstichting → eigendomsconcentratie; toezichthouder → holdingconcentratie; NVJ → flak | FvD betwist EU/institutionele legitimiteit → establishment-as |
| Wie | de 17 huidige mechanismen | insurgente bewegingen, ook reactionaire/elite-gesteunde |
| Hallin | verschuift de grens van binnenuit (accountability) | duwt iets van **consensus → legitieme controverse** |

Deze twee onder één `tegenmacht`-vlag stoppen is de categoriefout. Kind 1 is redelijk als (enge) categorie; kind 2 is geen categorie maar een *gerichte beweging relatief aan een as*, en hoort niet als actor-kleur maar als edge-valentie.

## Anker: Hallin's drie sferen

Daniel C. Hallin, *The Uncensored War* (1986), geeft de exacte woordenschat, en die mapt 1-op-1 op wat het model al heeft:

- **Sfeer van consensus** = de *consensusvloer* (alle blokken eens) → fabricage van instemming is hier totaal; `consensuscalibratie` draait de filters strak.
- **Sfeer van legitieme controverse** = de *betwiste as* (concurrerende elite-facties, cultureel vooral) → begrensde pluriformiteit; `schijnpluriformiteit`.
- **Sfeer van deviantie** = het uitgeslotene (uitdagingen aan de vloer zélf + de ~34% onderkant uit het SCP-werk) → marginalisering, flak-terrein.

**Herdefinitie van tegenmacht (contra-hegemonisch):** een kracht die de grens van de consensussfeer verschuift — die iets van consensus naar legitieme controverse duwt. Zo hangt het label aan de *beweging/edge relatief aan een doel-as*, nooit aan de actor. Op FvD toegepast: je labelt niet de partij, maar drie losse bewegingen — EU/legitimiteit betwisten = contra-hegemoniaal op de establishment-as; trollenleger tegen journalisten = flak; pro-markt = géén tegenmacht op de economische as.

---

## Deel A — DOCUMENTATIE.md-herkadering (drop-in tekst)

### A1. Vervang de sectie "Uitbreiding B: Tegenmacht" (regel ~125)

> ### Uitbreiding B: Tegenmacht — een gerichte valentie, geen universele categorie
>
> Het model modelleert óók de krachten die het filtersysteem begrenzen of doorbreken. Maar "tegenmacht" is **geen eigenschap van een actor** en zelfs niet van een losse edge zonder meer: het is een **tweeplaatsig predicaat**, `tegenmacht(X, doel)`. In een veld van meerdere machtsblokken dient het tegenwerken van het ene blok vaak het andere; dezelfde actor kan dus tegenmacht zijn op de ene as en promacht op de andere. Een universeel "tegenmacht"-stempel (op een knoop, of als kleur van een entiteit) is daarom een categoriefout — de valentie hangt altijd aan een **edge relatief aan een benoemd doel**.
>
> Het model onderscheidt twee soorten "tegen" die niet op één hoop mogen:
>
> 1. **Verantwoording** — tegenwicht tegen een *filter-machtsconcentratie* (de borgingsstichting tegen eigendomsconcentratie, de toezichthouder tegen holdingconcentratie, de vakbond/NVJ tegen flak). Dit zijn de institutionele accountability-mechanismen hieronder. Ze delen één doel — de verantwoording van geconcentreerde mediamacht — en ontlenen daaraan hun samenhang. Let op: ze zijn dubbel — parlementaire controle *checkt* macht én *legitimeert* de institutionele orde (consensusvloer-versterking).
> 2. **Contra-hegemonie** — een kracht die de grens van de **consensussfeer** verschuift (Hallin 1986): die een onderwerp van de sfeer van consensus naar die van legitieme controverse duwt. Dit is *niet* hetzelfde als verantwoording, en het is *niet* aan een actor te binden: een insurgente beweging kan contra-hegemoniaal zijn op de establishment-as en tegelijk reactionair/elite-gesteund op de economische as. Contra-hegemonie wordt daarom geclassificeerd als **edge-valentie per as** (zie [Deel B / machtsvalentie]), niet als filter of actor-kleur.
>
> **Rollen (verantwoording):** `onderzoeksjournalist`, `klokkenluider`, `parlementair_controleur`, `toezichthouder`, `vakbond_media`, `burgerinitiatief`, `borgingsstichting`, `alternatief_medium`
> **Mechanismen (verantwoording):** `onderzoeksjournalist_doorbraak`, `klokkenluider_doorbraak`, `onafhankelijk_medium_tegenwicht`, `parlementaire_controle`, `toezichthouder_interventie`, `toezicht_tandeloosheid`, `vakbond_bescherming`, `burgerinitiatief_druk`, `onafhankelijkheidsborging`, `redactiestatuut_borging`, `continuiteitsborging`, `afgedwongen_borging`, `projectfinanciering_journalistiek`
>
> Deze mechanismen houden `filter='tegenmacht'` — de filter-waarde markeert nu expliciet **soort 1 (verantwoording)**. Factie-insurgentie krijgt géén `tegenmacht`-filter; ze wordt gemodelleerd als wat ze is (flak/ideologie-edges tussen blokken), plus, waar ze de vloer zelf betwist, een `machtsvalentie`-annotatie op de betreffende as.
>
> *(De bestaande borgingsstichting-alinea blijft ongewijzigd hieronder staan.)*

### A2. Nieuwe passage bij de emergente velden (naast `consensuscalibratie`)

Toe te voegen waar `consensuscalibratie`/`schijnpluriformiteit` worden besproken (§ Scores / emergente velden of de aard-sectie):

> **De drie sferen (Hallin 1986) als referentiekader.** De multipolariteit die `consensuscalibratie` codeert, valt samen met Hallins drie sferen: de **sfeer van consensus** (alle machtsblokken eens → filters strak, fabricage totaal — dit ís de regelknop van `consensuscalibratie`), de **sfeer van legitieme controverse** (concurrerende elite-facties, vooral op de culturele as → begrensde pluriformiteit, `schijnpluriformiteit`) en de **sfeer van deviantie** (uitdagingen aan de vloer zelf + de structureel uitgesloten onderkant → marginalisering/flak). Het model gaat dus **niet** uit van één monolithische elite: de emergente pro-elite bias is het sterkst op de *overlap* van de blokken (de vloer) en zwak/pluralistisch op de *betwiste* as. Tegenmacht in de contra-hegemonische zin = een kracht die die grens verschuift.

---

## Deel B — de structurele schakel: edge-valentie ↔ kleurmeter-assen

De kleurmeter (`politiek.py`) berekent al per actor een positie op drie assen (economisch/cultureel/establishment) uit richting-signalen (`property='politieke_positie'`, `property_value='<as>:<pool>'`). Die laag praat nu **niet** met de filter/edge-classificatie. De ontbrekende schakel maakt "tegenmacht tegen wie, op welke as" **afleesbaar uit data** in plaats van uit een vast label — precies gespiegeld op het kleurmeter-patroon.

### B1. Nieuwe argument-property `machtsvalentie` (aspect)

Een argument op een **relatie** (`relation_id`) of **mechanisme** (`mechanism_id`), stance `contextual`, dat de valentie van die edge codeert. Twee waarde-vormen (één property, flexibele `property_value`, net als `politieke_positie`):

```
property = 'machtsvalentie'
property_value:
  'filter:<eigendom|advertentie|sourcing|flak|ideologie>'      # soort 1: verantwoording — checkt die concentratie
  'as:<economisch|cultureel|establishment>:<opent|sluit>'      # soort 2: contra-hegemonie op die as
```

- `opent` = de edge duwt het onderwerp van consensus → legitieme controverse (contra-hegemoniaal op die as).
- `sluit` = de edge verstrakt de consensus (pro-hegemoniaal).
- Eén edge mag meerdere dragen (max. één per as, net als de kleurmeter: één signaal per as).

### B2. Behandeling (identiek aan `politieke_positie`)

- **Aspect-property**: opgenomen in `ASPECT_PROPERTIES` (scoring.py) → telt **niet** in de certainty-balans en is **vrijgesteld** van de citatiepoort (zoals `filter`/`mechanism`/`compositie`/`indirecte_invloed_op`/`politieke_positie`).
- **Voedt geen score.** Puur een classificatie-/overlay-laag, net als de kleurmeter. Valentie is interpretatief, geen bewijs-magnitude — het mag `entity_primary_filter` (die op magnitude classificeert) niet verstoren.
- **Afleiding** in een kleurmeter-nabije functie (uitbreiding van `politiek.py` of een dun `tegenmacht.py`): per edge en geaggregeerd per actor een **valentie-per-as**, zodat de viz kan tonen *"FvD: opent op establishment + cultureel, neutraal/sluit op economisch"* in plaats van één `tegenmacht`-kleur.

### B3. Gewerkt voorbeeld

- **Borgingsstichting → eigendomsconcentratie** (rel. bestaand): `machtsvalentie = 'filter:eigendom'`. Soort 1: blijft `filter='tegenmacht'`, doel nu expliciet.
- **FvD betwist EU/institutionele legitimiteit** (edge → establishment): `machtsvalentie = 'as:establishment:opent'`. Géén tegenmacht-filter; contra-hegemoniaal op één as.
- **FvD-trollenleger → journalist**: gewone flak-edge, `machtsvalentie` optioneel `'as:establishment:opent'` als het de institutionele legitimiteit betwist; de intimidatie zelf blijft flak.
- **FvD pro-markt** (edge → economisch): geen `machtsvalentie` (of expliciet `'as:economisch:sluit'`) — géén tegenmacht op die as.

### B4. Platform-casus (waarom dit nodig is)

Een platform is tegelijk **consensusvloer-versterkend** (eigendom/advertentie — `machtsvalentie='filter:eigendom'`-tegenpool, pro-markt/pro-eigen-regulering) én **betwiste-as-versterkend** (engagement blaast factie-insurgentie op → `'as:establishment:opent'` op de content-edges). In het huidige één-filterlabel-schema moet je één kant kiezen en verlies je de andere; met per-as-valentie kan het zonder tegenspraak naast elkaar staan. Dit is meteen het sterkste bestaansargument voor de schakel.

---

## Deel C — impact & migratie

- **Geen data-sloop.** De 17 tegenmacht-mechanismen behouden `filter='tegenmacht'`; de betekenis verengt naar "soort 1 (verantwoording)" — een doc-herkadering, geen kolomwijziging.
- **Schema:** geen nieuwe tabel. `machtsvalentie` is een `arguments.property`-waarde; alleen `ASPECT_PROPERTIES` (scoring.py) + de aspect-vrijstellingen in `server.py` (citatiepoort, reply-property-verbod-uitzondering) uitbreiden, plus de validatie-check die `property_value`-vorm bewaakt (spiegel van de `politieke_positie`-parser).
- **Viz:** een per-as valentie-overlay (nieuw), naast de bestaande kleurmeter. `entity_primary_filter` (kleur/categorie) blijft ongewijzigd.
- **Backwards:** bestaande data heeft geen `machtsvalentie`; alles blijft werken, de overlay is leeg tot signalen worden toegevoegd (zoals de kleurmeter dat was).

## Open beslispunten (jouw keuze)

1. **Property-naam:** `machtsvalentie` (voorstel) vs. `tegenmacht_doel` vs. iets anders.
2. **Reikwijdte soort 1:** de bestaande 17 mechanismen retroactief van een `machtsvalentie='filter:…'` voorzien, of alleen nieuwe edges annoteren en de oude impliciet laten?
3. **Waarde-vorm:** één flexibele property met twee vormen (voorstel) vs. twee aparte properties (`machtsvalentie_filter` / `machtsvalentie_as`).
4. **`politiek.py` uitbreiden** met de valentie-afleiding, of een apart dun `tegenmacht.py` naast de kleurmeter?
5. **Doorvoeren nu** (ik edit DOCUMENTATIE.md + schrijf de scoring/server/validatie-schakel + een `test_*`) of eerst alleen de DOCUMENTATIE.md-herkadering (spec-first, data later)?
