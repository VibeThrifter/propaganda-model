# Data-dictionary — de licentieerbare data-feed (E1)

Deze data-dictionary beschrijft het **verkoopbare dataproduct**: de geversioneerde
export van de structuur-, eigendoms- en geldstroomgraaf van het Nederlandse
mediasysteem (het propagandamodel, Herman & Chomsky toegepast op Nederland).

Het product is *het model als data*, niet de website. Twee vormen, dezelfde inhoud:

- **CSV-export** — `python3 scripts/export_dataset.py` schrijft één CSV per tabel in
  `releases/dataset-v<X.Y.Z>/` (het geversioneerde zusje van het scores-snapshot
  `releases/model-v<X.Y.Z>.json`).
- **Feed-API** — `GET /api/feed/graph` (JSON) en `GET /api/feed/export/<tabel>.csv`,
  achter een API-key + lees-quotum. De publieke `GET /api/graph_data` blijft open en
  ongemeterd (de portal-loader hangt eraan). Zie `docs/openapi.yaml`.

Beide vormen putten uit **één bouwer** (`export_dataset.verzamel`), zodat de
afbakening op precies één plek zit.

---

## Wat er NIET in zit (bewust uitgesloten — neutraliteit + juridisch)

Twee lagen worden **mechanisch** uit elke export en uit de feed-doc gefilterd:

1. **De politieke-positie-laag** — `politiek.py` / `kleurmeter` in `GET /api/graph_data` /
   `arguments.property='politieke_positie'`. Dit is **art. 9-AVG-data** (politieke
   opvattingen per natuurlijk persoon): het gevoeligste onderdeel en commercieel een
   last. Zit in geen enkele verkochte kolom of rij.
2. **`machtsvalentie`** — de contra-hegemonie-as (`tegenmacht.py` /
   `machtsvalentie` in `GET /api/graph_data` / `property='machtsvalentie'`). Deels politiek geframed →
   grensgeval → **standaard uitgesloten** uit de betaalde feed.

Daarnaast is de vrije-tekst `description` van entiteiten en relaties **niet**
meegeleverd: dat is de model-eigen redactionele prose (de neutraliteits-risicolaag,
waar het model in zijn eigen stem spreekt) en kan data-afhankelijk naar de
uitgesloten analyse-lagen verwijzen. Het product is de **structuur** (types, rollen,
mechanismen, scores, bronnen); de duiding blijft op de live site (`/methode`, per-
element-pagina's).

Verificatie van de uitsluiting is onderdeel van de release-discipline:

```bash
grep -rc "politieke_positie\|machtsvalentie" releases/dataset-v*/   # → 0 in elk bestand
```

---

## De twee-assen-score (lees dit vóór je een getal gebruikt)

Elke relatie draagt **twee onafhankelijke scores**; verwar ze niet, en lees ze niet
als een exacte meting:

| As | Vraag | Voorbeeld van de dissociatie |
|----|-------|------------------------------|
| **`certainty`** | *Bestaat deze relatie?* | Passief aandeelhouderschap kan zeker zijn (hoge certainty) maar de berichtgeving nauwelijks sturen (lage influence). |
| **`influence`** | *Hoe sterk stuurt ze de berichtgeving?* | Zelfcensuur kan onzeker zijn (lage certainty) maar, als ze speelt, sterk sturend (hoge influence). |

**De 0,05-vloer (guilty-until-proven).** Een prior die (nog) niet door bewijs in de
discussieboom is onderbouwd, wordt niet op 0 maar op **0,05** gezet — voor *beide*
assen. Dat is een bewuste ondergrens, geen meting: hij houdt de topologie meetbaar
(`influence.py` kan het pad nog wegen) terwijl de magnitude minimaal blijft tot er
bewijs is. **Een waarde van 0,05 betekent dus "onbewezen", niet "gemeten als zwak".**
De afgeleide `*_detail`-scores (uit `GET /api/scores`) dragen daarnaast 95%-
intervallen en vlaggen (`onweersproken` = geen gesourcete tegenspraak, cap 0,70);
lees die mee voordat je een cijfer citeert.

Meer achtergrond: `DOCUMENTATIE.md` § "Scores: van discussieboom naar theorie" en de
publieke methodepagina `/methode`.

---

## Verversschema / cadans

- **Versie** = semver, gelijk aan de nieuwste model-release (`releases/model-v*.json`).
  `export_dataset.py` leidt de versie standaard af uit die release; expliciet kan met
  `python3 scripts/export_dataset.py <X.Y.Z>`.
- **Cadans (aanbevolen):** maandelijks + on-demand, samen met een model-release.
  `scripts/release_model.py` schrijft het scores-snapshot; draai er
  `scripts/export_dataset.py` naast met **dezelfde versie**, zodat
  `releases/model-v<X.Y.Z>.json` en `releases/dataset-v<X.Y.Z>/` samen bewegen. (De
  koppeling is bewust een losse tweede stap gehouden i.p.v. in `release()` gebakken —
  zie de OWNER-ACTION-notitie onderaan.)

---

## Formaat: CSV standaard, Parquet alleen opt-in

**CSV is de default** — stdlib (`csv`), geen build step, geen dependency; dat is de
projectregel ("plain Python 3 + SQLite + Flask, geen zware deps"). Alle waarden zijn
UTF-8, komma-gescheiden, met een kopregel.

**Parquet is een spanning met die regel** (`pyarrow`/`pandas` = zware deps) en zit
daarom **niet** in de kern-app. Wie kolomgeoriënteerd Parquet wil, draait de conversie
achter een **geïsoleerde venv** — precies het patroon van `tools/linkedin/.venv` +
`requirements.txt` — nooit in de hoofdomgeving. Bijvoorbeeld:

```bash
python3 -m venv .venv-parquet && . .venv-parquet/bin/activate
pip install pandas pyarrow
python3 -c "import pandas as pd, glob, os; [pd.read_csv(f).to_parquet(f[:-4]+'.parquet') for f in glob.glob('releases/dataset-v*/*.csv')]"
```

CSV blijft het geleverde formaat; Parquet is een lokale opt-in conversie.

---

## API-keys aanmaken (feed-toegang)

De feed-namespace (`/api/feed/*`) zit achter een API-key met een lees-quotum per
minuut per tier: `proef` (20), `feed` (240), `onbeperkt` (geen limiet) — zie
`FEED_QUOTA` in `server.py`. Sleutel-opslag **spiegelt `data/tokens/`**: één JSON-
bestand per key in `data/api_keys/`, waarin **alléén de sha256-hash** staat (de
plaintext-key zie je één keer bij het minten en bewaar je zelf). Geen tabel, geen
migratie, geen schema-wijziging.

Een key minten (de eigenaar, eenmalig — het patroon hergebruikt `auth`):

```bash
python3 - <<'PY'
import json, secrets, hashlib, pathlib
key = "pmk_" + secrets.token_urlsafe(32)          # dit is de plaintext — bewaar 'm nu
naam, tier = "proef-klant", "feed"                # kies naam + tier
d = pathlib.Path("data/api_keys"); d.mkdir(parents=True, exist_ok=True)
(d / f"{naam}.json").write_text(json.dumps({
    "naam": naam, "tier": tier,
    "key_hash": hashlib.sha256(key.encode()).hexdigest(),
}, indent=2))
print("API-key (één keer getoond):", key)
PY
```

Gebruik daarna: `Authorization: Bearer <key>` óf `?key=<key>`. Een key intrekken =
het JSON-bestand verwijderen. `data/` is gitignored, dus keys lekken niet in git.

---

## De tabellen

Kolomtypes en enum-waarden zijn gegrond in `schema.sql`. Alle geëxporteerde rijen
zijn `status='goedgekeurd' AND NOT vervangen` (de `voorgesteld`/`afgewezen`/
`vervangen`-rijen en de smaad_hold-firewall blijven eruit).

### `entities.csv` — de knopen

| Kolom | Betekenis |
|-------|-----------|
| `id` | Stabiele primaire sleutel (referentiepunt in `relations`, `income_composition`, …). |
| `name` | Unieke naam (organisatie of natuurlijk persoon/familie). |
| `type` | Structurele **vorm** (`schema.sql` :154–189), niet de functie. Organisaties: `mediaorganisatie`, `bedrijf`, `partij`, `denktank`, `overheidsinstelling`, `toezichthouder`, `ngo`, `vakbond`, `omroep`, `elite_netwerk`, `vermogensbeheerder`, `pr_bureau`, `platform`, `stichting`, … Personen: altijd `persoon`. (Enkele legacy-rolachtige types kunnen in oudere data voorkomen.) |
| `primary_role_id` | FK naar de rol (theorielaag) die als hoofdrol is toegekend. *Let op:* de in de viz **getoonde** primaire rol is afgeleid (argmax-filter over de relaties); dit veld is de toegekende fallback. |
| `primary_role` | Naam van die rol (bv. `mediaeigenaar`, `gatekeeper`). |
| `active_from` / `active_until` | Looptijd (jaar of datum); leeg = onbegrensd voor zover bekend. |
| `active` | 1/0 — of de entiteit als actueel geldt. |
| `bestuurslaag` | Alleen bij overheidsorganisaties (Uitbreiding C, 2026-10-07): `eu`, `rijk`, `provincie`, `gemeente`, `waterschap`, `caribisch` of `regio`; leeg voor de rest. |

### `relations.csv` — de gerichte banden

| Kolom | Betekenis |
|-------|-----------|
| `id` | Primaire sleutel. |
| `source_id` / `source_name` | Uitgaande knoop (de bron van de invloed). |
| `target_id` / `target_name` | Inkomende knoop. |
| `relation_type` | Aard van de band (`schema.sql`): o.a. `eigendom`, `financiering`, `adverteerder`, `lidmaatschap`, `bestuurder`, `draaideur`, `bron_van`, `framing`, `lobbyt`, `flak`, `intimidatie`, `regulering`, `zelfcensuur`, `cooptatie`, `algoritmische_filtering`, en sinds Uitbreiding C (2026-10-07) `ambt` (persoon → overheidsorganisatie), `zeggenschap` (organisatie → organisatie), `controle` en `geschenk`. |
| `mechanism_id` / `mechanism_name` | Het theorie-mechanisme waarvan deze relatie een instantie is (leeg = nog geen mechanisme; zo'n relatie is dan geen goedgekeurde instantie). |
| `filter` | De primaire categorie van dat mechanisme: een van de vijf filters (`eigendom`, `advertentie`, `sourcing`, `flak`, `ideologie`), `tegenmacht`, `overig`, `cross_filter`, of een van de vijf categorieën van de besluitvorming (Uitbreiding C, 2026-10-07): `formele_macht`, `belangen`, `kennis_advies`, `polder`, `werving`. |
| `certainty` | As 1 — *bestaat de relatie?* 0,0–1,0. 0,05 = onbewezen prior (zie boven). |
| `influence` | As 2 — *hoe sterk stuurt ze berichtgeving?* 0,0–1,0. 0,05 = onbewezen prior. |
| `active_from` / `active_until` | Looptijd; leeg = onbegrensd voor zover bekend. |
| `functie` | De ambtstitel of functie zoals het register hem geeft (bv. "Secretaris-generaal", "Kamerlid, fractievoorzitter", "Vaste toegangspas (…)"); meestal bij `ambt`, verder leeg. |
| `namens_id` / `namens_name` | De hoedanigheid (sinds 2026-10-19): bij een verband van een persoon de organisatie namens of vanuit welke hij optrad, zoals de bron hem aankondigt ("Clingendael-onderzoeker Bob Deen" → Clingendael). Leeg = eigen titel, oud-medewerker of een andere pet. De route organisatie → medium via haar medewerkers is hieruit af te leiden (`GET /api/via_medewerkers/<id>`); zo'n optreden staat bewust niet óók als verband organisatie → medium in de data. |

### `sources.csv` — de bronnenlijst (bibliografisch)

| Kolom | Betekenis |
|-------|-----------|
| `id` | Primaire sleutel (gerefereerd door `source_locations`). |
| `title`, `author`, `publisher`, `date_published`, `language` | Bibliografische velden. |
| `source_type` | `boek`, `academisch_artikel`, `rapport`, `nieuwsartikel`, `transcript`, `interview`, `dataset`, `wetgeving`, `persbericht`, `website`, `overig`. |
| `reliability` | Betrouwbaarheids-/rigueurklasse (`schema.sql` :331–341): `primair`, `academisch`, `institutioneel`, `kwaliteitsjournalistiek`, `regulier`, `opinie`, `grijs`, `eigen_synthese` (weegt 0), `onbeoordeeld`. |
| `onderwerp` | Relevantie-as: `nl_systeem` (weegt zwaarder), `algemeen`, `buitenlands` (lichter), `onbepaald`. |
| `cluster_key` | Bron-cluster (M1.2): bronnen met dezelfde auteur/uitgever/onderliggende data zijn géén onafhankelijke bewijslijnen. Leeg = eigen cluster. |

### `source_locations.csv` — vindplaatsen per bron

| Kolom | Betekenis |
|-------|-----------|
| `id` | Primaire sleutel. |
| `source_id` | FK naar `sources.id`. |
| `location_type` | `url`, `file`, `doi`, `isbn`, `arxiv`, `handle`, `archive_url` (Wayback-snapshot). |
| `location` | De URL/DOI/ISBN/het pad zelf. |
| `accessed_at` | Bezoekdatum (voor URLs). |

### `income_composition.csv` — de geldstroom-"pie" (afgeleid)

Afgeleid uit `scoring.compute_income_composition`: per outlet de inkomende financier-
edges met een gesourcet aandeel, plus de ongemeten financiers. Eén rij per bijdrage.

| Kolom | Betekenis |
|-------|-----------|
| `outlet_id` / `outlet` | De ontvangende nieuwsoutlet. |
| `soort` | `aandeel` (gemeten %) of `onbekend` (financier-edge zonder gemeten aandeel). |
| `bron_id` / `bron` | De financier (source-knoop van de geldstroom-edge). |
| `relation_type` | Type geldstroom-edge (bv. `financiering`, `donor`). |
| `relation_id` | FK naar `relations.id`. |
| `share_pct` | Gemeten aandeel in % (leeg bij `onbekend`). |
| `jaar` | Jaar van het gemeten aandeel (leeg bij `onbekend`). |
| `som_institutioneel` | Som van alle gemeten institutionele aandelen van deze outlet. |
| `residu_pct` | Afgeleid restpart eigen/markt-inkomsten = max(0, 100 − som). |

### `bereik.csv` — publieksbereik per jaar (afgeleid)

Uit `bereik.compute_bereik`: per media-entiteit de gesourcete bereikcijfers. Eén rij
per signaal (per stuk zichtbaar; per jaar wint in de viz de grootste maat).

| Kolom | Betekenis |
|-------|-----------|
| `entity_id` / `entity` / `type` | De media-entiteit. |
| `maat` | Publieksmaat: `kijkers`, `luisteraars`, `oplage`, `bereik_totaal`, `online`, `invullers`, `volgers`. |
| `aantal` | Het cijfer (personen/exemplaren). |
| `jaar` | Meetjaar (verplicht — de tijdreeks is het punt). |
| `arg_id` | Het onderliggende discussieboom-argument (met verbatim bron-citaat). |
| `status` | Reviewstatus van het signaal. |

### `doelgroep.csv` — getargette welstandsklasse per outlet (afgeleid)

Uit `doelgroep.compute_doelgroepmeter`: per outlet de bron-gewogen getargette
marketing-/welstandsklasse (hoog A ↔ laag D). Eén rij per outlet.

| Kolom | Betekenis |
|-------|-----------|
| `outlet_id` / `outlet` / `type` | De nieuwsoutlet. |
| `positie` | Bron-gewogen positie op de welstands-as (−1 laag … +1 hoog). |
| `klasse_label` | Afgeleide klasse (A / B1 / B2 / C / D), of `onbepaald`. |
| `as_soort` | `meting` (≥1 externe NOM/NMO-index) of `opgave` (mediakit e.d.). |
| `vertrouwen` | α = w/(w+K): vertrouwen in de positie (meer/betere bronnen → hoger). |
| `n_signalen` | Aantal onderliggende gesourcete signalen. |

---

## Licentie & attributie

Gebruik van deze data valt onder `docs/LICENSE-DATA.md`: **bronvermelding verplicht,
geen doorverkoop**, met verwijzing naar de neutraliteits-/methodologieverantwoording
op `/methode`. De uitgesloten politieke laag zit er sowieso niet in.

---

## OWNER-ACTION — cadans in `release_model.py` bakken (optioneel)

De koppeling dataset↔release is nu een **bewuste losse tweede stap** (draai
`export_dataset.py <versie>` na `release_model.py <versie>`), niet ingebouwd in
`release()`. Dat is om E1 niet-invasief te houden. Wil je het één commando maken, roep
dan `export_dataset.export(versie)` aan het eind van `release()` aan — dat is een
kleine, veilige toevoeging, maar valt buiten de E1-bestand-lane en is daarom hier als
OWNER-ACTION gelaten.
