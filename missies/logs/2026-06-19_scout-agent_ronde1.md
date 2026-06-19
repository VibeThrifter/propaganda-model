# Scout-missie — ronde 1 — 2026-06-19

- **Agent-account:** `scout-agent` (bijdrager)
- **Brief:** `missies/scout_brief.md`, git-hash `41c92ced27eec3cf3450810030ee914c95cb6fe7`
- **API-base:** http://localhost:5000 (health → 200 geverifieerd om 23:16 CEST)
- **Tijdzone log:** CEST (server stempelt argumenten in UTC, +2u verschil)

## Onderwerpkeuze (M3.2)

Hoogst geprioriteerde agenda-element uit `data/onderzoeksagenda.json` (gegenereerd
2026-06-19T23:16): **`ledeneis`** (mechanisme id 121, prioriteit 0,3149), gelijk met
`erkenningverlening` (123) en `omroepsignatuur` (124) — het publieke-omroepbestel-cluster.
Geen eerdere scout-ronde liep hiervoor (logs/ bevatte alleen README.md). De `ontbreekt`-lijst
voor alle drie: *geen overwogen tegenspraak (M1.4-plafond actief)*, *drijft op één broncluster*,
*geen praktijk-instanties*. Doel van deze ronde: nieuwe clusters + tweezijdig bewijs (om het
M1.4-plafond op te lichten).

**Neutrale missievraag:** *"Wat is bekend over de ledeneis en erkenningseisen in het Nederlandse
publieke-omroepbestel en de effecten daarvan op programmering en pluriformiteit?"* — bewust
geformuleerd zónder modelclaim. De database is NIET vóór het zoeken gelezen (lantaarnpaal-fout);
koppeling aan doel-id's gebeurde pas bij het indienen.

## Queries (letterlijk, met tijdstip)

| # | Tijd (CEST) | Tool | Query |
|---|---|---|---|
| Q1 | 23:21 | WebSearch | `ledeneis publieke omroep erkenningseisen Mediawet effect pluriformiteit programmering` |
| Q2 | 23:21 | WebSearch | `Commissariaat voor de Media erkenningsverlening omroepverenigingen ledental rapport` |
| Q3 | 23:23 | WebSearch | `ledeneis publieke omroep kritiek "kunstmatige leden" gratis lidmaatschap omroepen ledenwerving` |
| Q4 | 23:23 | WebSearch | `WRR Raad voor Cultuur externe pluriformiteit omroepbestel ledenmodel proefschrift mediastudies` (buiten-de-bril) |
| Q5 | 23:26 | WebFetch | tweedekamer.nl/downloads/document?id=2021D43440 (AEF-verkenning) — eerst mislukt (binaire PDF), daarna lokaal opgehaald + via pypdf geëxtraheerd |
| Q6 | 23:26 | WebFetch | spreekbuis.nl/representatiekritiek-...-politieke-partijen-hebben-nog-minder-leden/ (Van Dijk) |
| Q7 | 23:27 | WebFetch | rijksoverheid.nl/.../aan-welke-eisen-moet-een-omroepvereniging-voldoen (officiële drempels) |
| Q8 | 23:30 | WebSearch | `omroepbestel ledenmodel diversiteit programma-aanbod empirisch onderzoek "interne pluriformiteit" versus "externe pluriformiteit"` (buiten-de-bril) |
| Q9 | 23:30 | WebSearch | `afschaffen ledeneis publieke omroep nieuw bestel kabinet 2024 2025 omroephuizen gevolgen` |
| Q10 | 23:31 | WebFetch | rijksoverheid.nl/.../hervorming-publieke-omroep-... (hervorming 2025) |
| Q11 | 23:31 | WebFetch | nos.nl/l/2435413 (bestel "niet beheersbaar") |
| Q12 | 23:32 | WebFetch | thesis.eur.nl/pub/57266 (Erasmus mediastudies-thesis) — **timeout, niets geoogst** |
| Q13 | 23:32 | WebSearch | `omroepvereniging leden weinig invloed redactie programmering autonomie eindredacteur "leden bepalen niet"` |
| Q14 | 23:33 | WebFetch | spreekbuis.nl/het-omroepbestel-is-stuk-gemaakt/ (Verlind) |

## Geregistreerde bronnen

Alle vier nieuw geregistreerd via `POST /api/sources` met URL-locator; `reliability` = `onbeoordeeld`
(classificatie is reviewer-gated mensenwerk).

| source_id | Titel | Auteur | Uitgever | Datum | cluster_key | type |
|---|---|---|---|---|---|---|
| 109 | Verkenning naar legitimatiecriteria voor publieke omroepen | AEF (Colenbrander, Van Eijk, Etty, Van 't Klooster, Van Zoest-Hommema) | Andersson Elffers Felix i.o.v. OCW | 2021-10-28 | `andersson_elffers_felix_legitimatiecriteria` | rapport |
| 110 | NPO: huidig omroepbestel niet beheersbaar, kabinet wil andere criteria | NOS | NOS | 2022-07-05 | `nos_omroepbestel` | nieuwsartikel |
| 111 | Het omroepbestel is stuk gemaakt | Ton Verlind | Spreekbuis.nl | 2021-07-09 | `spreekbuis_verlind` | website |
| 112 | Representatiekritiek op omroepverenigingen ... politieke partijen hebben nog minder leden | Walter van Dijk | Spreekbuis.nl | 2025-03-22 | `spreekbuis_vandijk_representatie` | website |

## Oogst (ingediende argumenten — alle `voorgesteld`)

| arg-id | doel | stance | bron | kern |
|---|---|---|---|---|
| 577 | mechanisme 121 `ledeneis` | supporting | 109 | Stromingsvereiste onmeetbaar → ledental is de facto toegangspoort tot het bestel |
| 579 | mechanisme 123 `erkenningverlening` | supporting | 110 | Eenrichtings-poort (omroepen komen erbij, verdwijnen niet) → versnippering, "niet beheersbaar" |
| 580 | mechanisme 124 `omroepsignatuur` | **contradicting** | 111 | Tegenbewijs: inhoudelijke macht gecentraliseerd bij NPO; eigen signatuur stuurt minder dan de wet suggereert |
| 582 | mechanisme 121 `ledeneis` | **contradicting** | 112 | Tegenbewijs: ledental is zwakke/selectieve proxy voor draagvlak (politieke partijen hebben nog minder leden) |
| 583 | mechanisme 121 `ledeneis` | contextual | 109 | **Afwezigheidsrapport**: geen direct empirisch onderzoek gevonden voor de causale schakel ledental→programmering |

Niet-geforceerde doelkoppeling: alle vondsten pasten op bestaande theorie-doelen (121/123/124).
Geen nieuwe theorie-elementen voorgesteld (zou RfC-werk zijn); geen praktijk-instanties aangemaakt
(de gevonden bronnen onderbouwen het mechanisme-niveau, niet een specifieke entiteit-relatie).

## Negatieve-resultatenregister

- **Q12 (Erasmus thesis-repository, thesis.eur.nl/pub/57266):** WebFetch-timeout na 60s; niets
  geoogst. Niet opnieuw geprobeerd binnen het volumeplafond van de ronde.
- **Q8 (buiten-de-bril, empirie interne-vs-externe pluriformiteit ↔ programma-aanbod):** géén
  direct empirisch onderzoek gevonden dat de causale schakel *ledental → programmering/pluriformiteit*
  meet. Bestaande bronnen (AEF-verkenning, CvdM-pluriformiteitsmonitor) meten de pluriformiteit van
  de OUTPUT, niet die causale schakel. → ingediend als afwezigheidsrapport (arg 583).
- **Q4 (buiten-de-bril, WRR/Raad voor Cultuur/proefschriften):** leverde beleidsdocumenten en oudere
  adviezen, maar geen recent, citeerbaar empirisch werk binnen het bereik van deze ronde dat de
  bestaande dekking wezenlijk versterkt; niet apart ingediend.

## Nieuwheid

Vier nieuwe bronclusters t.o.v. de bestaande dekking (was: `rijksoverheid` + `wetenschappelijke_raad_voor_het_regeringsbeleid`):
`andersson_elffers_felix_legitimatiecriteria`, `nos_omroepbestel`, `spreekbuis_verlind`,
`spreekbuis_vandijk_representatie`. Géén hercitaties van bestaande bronnen. Dit adresseert het
agenda-signaal "drijft op één broncluster" voor 121/123/124.

## Stance-balans van de ronde

- **Steun (supporting):** 2 (577, 579)
- **Tegen (contradicting):** 2 (580, 582)
- **Context (contextual / afwezigheidsrapport):** 1 (583)

Tweezijdige oogstplicht gehaald: evenveel steun als tegenbewijs, plus een eerlijk afwezigheidsrapport.
De twee contradicting-roots (580, 582) zijn bedoeld om het M1.4-onweersproken-plafond op
121 en 124 op te lichten — mits een reviewer ze merget. Niets is zelf gemerged/geraat/geclassificeerd;
alles wacht op menselijke review (ik stel voor, jij beslist).
