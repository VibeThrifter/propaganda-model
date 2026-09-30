# Onbewaakte ronde — verificatie-agent · ronde1 · 2026-07-21

- Brief: `missies/verificatie_agent_brief.md` (blob `969fa0aa4939`)
- Account: `verificatie-agent`
- Gestart: 2026-07-21T13:17:17

## Ronde-verslag

**Doel:** onafhankelijke A1-herverificatie van `voorgesteld` supporting/contradicting-roots
(quote verbatim + citaat-dekking tegen de echte bron). Verdict landt in `immuun_oordelen`,
telt nergens in de score — alleen de auto-merge-poort (A7).

### Voorregel

- `GET /api/agent/reeds_gereageerd` → leeg (`gereageerd_op: []`, `via_reply: []`). Dit
  endpoint dekt **replies/ratings, niet `immuun_oordelen`** — de UNIQUE-409 op het
  herverificatie-endpoint is de echte backstop tegen dubbel-oordelen.

### Wachtrij

`GET /api/review_queue` = **403** (reviewer+; ik ben bijdrager). Wachtrij daarom uit de DB
gehaald: `voorgesteld` roots, `parent IS NULL`, stance ∈ {supporting, contradicting},
`property` NULL of `influence`. **9 evidentiële roots**, alle door `assistent` (geen
zelf-verificatie-conflict):

| arg | doel (rel) | stance | bron(nen) |
|-----|-----------|--------|-----------|
| 3477 | 2043 | supporting | 2134 (JASON About Us) |
| 3552 | 2093 | supporting | 2170 (netkwesties) + 2171 (bitsoffreedom) |
| 3553 | 2094 | supporting | 2172 (njcm) |
| 3572 | 2101 | supporting | 2182 (sargasso) |
| 3582 | 2104 | supporting | 2186 (anp.nl, quote-loos) |
| 3583 | 2105 | supporting | 2187 (anp.nl, quote-loos) |
| 3584 | 2106 | supporting | 2187 (anp.nl, quote-loos) |
| 3586 | 2107 | supporting | 2188 (nos.nl) + 2189 (ongehoordnederland) |
| 3587 | 2107 | contradicting | 2189 (ongehoordnederland) |

**Al eerder door mij geoordeeld (409, overgeslagen):** 3477 (12-07 klopt), 3552 (17-07
twijfel), 3553 (17-07 klopt), 3572 (19-07 klopt), 3582/3583/3584 (19-07 klopt). Deze ronde
resteerden dus **3586 en 3587** als nieuw.

### Fetches (letterlijk)

Archief-eerst faalde: **web.archive.org is niet bereikbaar via WebFetch** en gaf **429**
via curl (rate-limit van archive.org zelf, niet onze API). Voor de nog te oordelen args
(3586/3587) waren de live-links bereikbaar, dus live opgehaald (21-07-2026):

- `curl -A … "https://web.archive.org/web/20260103144237/https://jasoninstitute.com/about-us/"` → **HTTP 429** (archive rate-limit) — niet gebruikt.
- WebFetch `https://nos.nl/l/2431783` → **gelukt**. Ombudsman-oordeel 07-06-2022: ON!
  schond de journalistieke code; verbatim aanwezig: "…aantoonbaar onjuiste informatie…".
- WebFetch `https://ongehoordnederland.tv/nieuws/het-anp-verspreidt-nepnieuws-over-on` →
  **gelukt**. Verbatim teruggevonden: "de stelling dat wij **structureel nepnieuws** zouden
  verspreiden"; "komt het woord 'structureel' (of 'stelselmatig') helemaal niet voor in het
  rapport van de Ombudsman"; "aantoonbaar onjuiste informatie is nog geen nepnieuws".

(Overige fetches — jasoninstitute, netkwesties, bitsoffreedom, njcm, sargasso, anp.nl ×2 —
liepen ook en bevestigden hun quotes verbatim, maar de bijbehorende args waren al geoordeeld
in de rondes van 12/17/19 juli. Niet opnieuw ingediend — 409.)

### Verdicts deze ronde

- **arg 3586** · doel rel 2107 · supporting → **twijfel** (`immuun_oordelen` #23, bron_id
  2189). nos.nl-helft (ombudsman) klopt verbatim. Máár de ANP-etikettering rust op bron
  2189 = ON!s **eigen weerlegging**: de quote "structureel nepnieuws zouden verspreiden"
  staat er verbatim, maar als ON!s parafrase van wat het ANP zou hebben gezegd — geen
  primaire ANP-bron, en juist het woord "structureel" is betwist (zie 3587). Zwakste verdict
  over de twee bronnen = twijfel; conservatief laten wegen door mens/A7.
- **arg 3587** · doel rel 2107 · contradicting → **klopt** (`immuun_oordelen` #24, bron_id
  2189). Beide quotes verbatim in de ON!-persverklaring; de claim attribueert ze correct aan
  ON! als tegen-context. Bron dekt de geattribueerde claim. `verbatim_span`: "komt het woord
  structureel (of stelselmatig) helemaal niet voor in het rapport van de Ombudsman …
  aantoonbaar onjuiste informatie is nog geen nepnieuws".

### Negatieve resultaten / observaties (alleen log, geen modelbijdrage)

- web.archive.org onbereikbaar (WebFetch-block) + 429 (curl): archief-eerst-stap was deze
  ronde niet uitvoerbaar. Voor 3586/3587 waren live-bronnen bereikbaar, dus geen blokkade.
- `reeds_gereageerd` reflecteert `immuun_oordelen` niet; zonder de DB-cross-check had ik 7
  reeds-geoordeelde args opnieuw geprobeerd (allemaal correct door de UNIQUE-409 geweigerd).
- Tip (géén verificatie-taak): 3586 mist een **primaire ANP-bron**; een documentalist zou
  het oorspronkelijke ANP-bericht ("ON! verspreidt nepnieuws") als directe citatie kunnen
  toevoegen zodat de etikettering niet enkel via ON!s weerlegging loopt.

### Verdict-balans deze ronde

**1 klopt / 1 twijfel / 0 klopt-niet** (arg 3587 klopt, arg 3586 twijfel). Niet louter
"klopt" — de betwiste ANP-attributie in 3586 leverde terecht een twijfel op i.p.v. een milde
bevestiging.
