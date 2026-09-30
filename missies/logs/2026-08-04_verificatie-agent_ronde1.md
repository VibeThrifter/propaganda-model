# Onbewaakte ronde — verificatie-agent · ronde1 · 2026-08-04

- Brief: `missies/verificatie_agent_brief.md` (blob `969fa0aa4939`)
- Account: `verificatie-agent`
- Gestart: 2026-08-04T17:15:29

## Sessie-uitvoer

**Taak:** A1 — onafhankelijke bron-herverificatie van `voorgesteld` supporting/contradicting-roots.

### Voorregel & wachtrij

- `GET /api/agent/reeds_gereageerd` (eigen token) → `{"door":"verificatie-agent","gereageerd_op":[],"via_reply":[]}` — leeg, zoals elke ronde: dat spoor is afgeleid van replies/ratings, niet van `immuun_oordelen`. De echte dubbel-check draait daarom op de procestabel (hieronder).
- `GET /api/review_queue` (met token) → **403** `"Rol 'reviewer' of hoger vereist (jouw rol: bijdrager)"`. Wachtrij daarom rechtstreeks uit de DB gelezen — toegestaan per agent-contract ("find target ids straight from the DB").
- DB-query (letterlijk):
  ```sql
  SELECT a.id, a.stance, COALESCE(a.property,'—'), a.contributed_by, substr(a.claim,1,70)
  FROM arguments a
  WHERE a.status='voorgesteld' AND a.parent_argument_id IS NULL
    AND a.stance IN ('supporting','contradicting')
    AND (a.property IS NULL OR a.property='influence')
    AND COALESCE(a.vervangen,0)=0
    AND a.id NOT IN (SELECT argument_id FROM immuun_oordelen
                     WHERE fase='herverificatie' AND door='verificatie-agent')
  ORDER BY a.id;
  ```
- Reeds door mij beoordeeld in eerdere rondes: **77** `herverificatie`-rijen (3477 … 3729). Allemaal overgeslagen; geen argument dubbel beoordeeld.
- **Netto deze ronde: 1 evidentiële root** — arg **#3730**, `contradicting`, ingediend door `aanklager-agent` op 2026-07-27. Geen zelf-verificatie-conflict (ander account).
- Aanvullende DB-queries: `SELECT … FROM arguments WHERE id=3730` (claim/reasoning/doel), `… FROM citations c JOIN sources s …` (3 citaties, alle op bron **2274**), `… FROM source_locations WHERE source_id=2274` (2 url-locators, **geen** `archive_url`-locator), `SELECT id,name,type,status FROM entities WHERE id=1215` (NieuwRechts, mediaorganisatie, voorgesteld).

### Anker

| veld | waarde |
|---|---|
| argument | **#3730** · `contradicting` · doel = entiteit **1215** (NieuwRechts) · property NULL |
| indiener | `aanklager-agent` (2026-07-27 11:42) |
| claim | NieuwRechts.nl haalt náást lidmaatschappen/donaties óók advertentie-inkomsten: ads.txt met `MANAGERDOMAIN=refinery89.com` + tientallen programmatische verkopers; homepage bevat in-article AdSense en opmaak voor gesponsorde ('native') artikelen |
| richt zich tegen | arg #3716 (verdienmodel-claim: inkomsten bij de lezersschare "in plaats van bij adverteerders of publieke financiering") |
| bron | **2274** — "NieuwRechts.nl — ads.txt … en advertentie-integratie in de paginabron" (website, reliability `onbeoordeeld`) |
| citaties | 4485 (OWNERDOMAIN/MANAGERDOMAIN), 4486 (vier RESELLER-regels), 4487 (`<app-adsense-presentation …`) — alle drie `methode='verbatim_quote'` |

### Fetch-log (archief eerst, conform brief; alle tijden UTC)

| # | tijd | doel | resultaat |
|---|---|---|---|
| 1 | 15:16:51 | `archive.org/wayback/available?url=nieuwrechts.nl/ads.txt` | **mislukt — HTTP 429** ("Too Many Requests", archive.org-zijde) |
| 2 | 15:16:51 | `archive.org/wayback/available?url=nieuwrechts.nl` | **mislukt — HTTP 429** |
| 3 | 15:17:03 | `https://web.archive.org/web/2026/https://nieuwrechts.nl/ads.txt` | OK — HTTP 200, redirect naar snapshot **20260201061930**; inhoud = één regel |
| 4 | 15:17:21 | **live** `https://nieuwrechts.nl/ads.txt` | OK — HTTP 200, 12.715 B, 340 regels |
| 5 | 15:17:44 | **live** `https://nieuwrechts.nl/` (geserveerde HTML) | OK — HTTP 200, 99.527 B → blijkt Angular-**shell** (`<title>Loading...</title>`, alleen `app-root` + menu geprerenderd) |
| 6 | 15:18:18 | `https://nieuwrechts.nl/main-KGVVLL3Z.js` (70 kB) + `scripts-JGZ6I4U3.js` (1,04 MB) | OK, maar 0 ad-markers → lazy-loaded chunks |
| 7 | 15:20:58 | `web.archive.org/cdx/search/cdx?url=nieuwrechts.nl&from=20260701&to=20260804` | **mislukt — HTTP 429** (nginx). Niet herhaald: geen retry-lus op archive.org |
| 8 | ~15:19–15:22 | headless Chrome `--dump-dom https://nieuwrechts.nl/` (`--virtual-time-budget=25000`) | OK — 437.244 B gerenderde DOM |
| 9 | 15:22 | `web.archive.org/web/20260201061930/…/ads.txt` (volledige inhoud) | OK — 1 regel |

**Waarom live i.p.v. archief:** bron 2274 heeft géén `archive_url`-locator (alleen twee `url`-locators), en de Wayback-lookup-API's gaven 429. De enige gevonden snapshot (2026-02-01) dateert van vóór de indiening en toont een ánder, veel ouder ads.txt — bruikbaar als corroboratie, niet als reproductie van de quotes.

### Verbatim-check

**Citaat 4485 — byte-identiek ✓** (r. 8–9 van het live-bestand, onder de kop `# Refinery89` + contactgegevens, precies zoals de context zegt):

```
OWNERDOMAIN=Nieuwrechts.nl
MANAGERDOMAIN=refinery89.com
```

**Citaat 4486 — alle vier de regels byte-identiek ✓** (`grep -x -F`, elk exact 1 treffer):

```
rubiconproject.com,19116,RESELLER,0bfd66d529a55807
pubmatic.com,159110,RESELLER,5d62403b186f2ace
openx.com,538959099,RESELLER,6a698e2ec38604c6
appnexus.com,13099,RESELLER
```

Ze staan niet aaneengesloten in het bestand, maar de context claimt dat ook niet ("vier van de tientallen RESELLER-regels"). Omvang: **208 RESELLER-** en **60 DIRECT-regels**. De overige in de claim genoemde verkopers staan er eveneens in: magnite (1), triplelift (7), sharethrough (13), rubicon (25), pubmatic (27), openx (16), appnexus (9).

**Citaat 4487 — reproduceerbaar, maar niet in de HTML-*bron* ⚠︎.** De geserveerde HTML bevat 0 treffers op `app-adsense-presentation`, `adsbygoogle`, `sponsored`, `googlesyndication`; ook de JS-bundels niet. In de **gerenderde DOM** staat het er wél, 4×:

```
<app-adsense-presentation _ngcontent-ng-c4056682387="" data-component="site-base" adlayout="in-article" adformat="fluid" _nghost-ng-c2518754401=""
```

Twee afwijkingen t.o.v. de quote, beide verklaarbaar als build-artefact van 8 dagen later:
1. de Angular-contenthash is geroteerd: `_ngcontent-ng-c221564423` → `_ngcontent-ng-c4056682387` (de hash uit de quote komt vandaag nergens meer voor; de huidige shell draait op c3071009340/c3983883882);
2. er is een attribuut `data-component="site-base"` bijgekomen.

De dragende attributen `adlayout="in-article"` en `adformat="fluid"` zijn identiek. Ook de twee context-strings vond ik letterlijk terug: `ins.adsbygoogle.loaded[data-ad-status=unfilled]` en `.article.sponsored.native`, inclusief een daadwerkelijk toegepaste `class="article image-left-sm small-intro sponsored native"`.

Kanttekening voor de reviewer: de context van 4487 zegt "verbatim uit de HTML-**bron**", terwijl de string alleen in de **gerenderde DOM** bestaat. Dat is een provenance-onnauwkeurigheid in de citatie-context, geen onjuiste quote.

### Citaat-dekking

De bron dekt de claim volledig. Een ads.txt met `MANAGERDOMAIN` + 208 RESELLER-regels ís de IAB-machtiging om advertentievoorraad te verkopen, en de in-article AdSense-eenheden + `sponsored native`-opmaak staan in de artikelstroom. De claim is bovendien correct afgebakend: hij weerlegt uitsluitend de *adverteerders*-uitsluiting uit #3716 en laat het "subsidievrije" deel expliciet staan — geen overreach. Doel-entiteit is een `mediaorganisatie`, geen `persoon`; smaad-firewall niet aan de orde.

**Zijdelingse corroboratie (archief):** de Wayback-kopie van 2026-02-01 bevat een ads.txt van één regel — `google.com, pub-6959296204820634, DIRECT, f08c47fec0942fa0`. Dat is precies de AdSense-uitgevers-id die de indiener in de context van 4487 noemt, dus advertentie-exploitatie is niet nieuw; inmiddels is die eigen DIRECT-regel vervangen door Refinery89-beheer (de live google.com-regels dragen andere pub-id's; `6959296204820634` komt niet meer voor).

### Verdict

`POST /api/arguments/3730/herverificatie` → **HTTP 200**, `immuun_oordelen` **id 114**, `verdict='klopt'`, `bron_id=2274`. `verbatim_span` = het `# Refinery89` / OWNERDOMAIN / MANAGERDOMAIN / RESELLER-blok uit het live-bestand. De mechanische voorcheck van de server liet `klopt` staan (de span bevat citaat 4485 letterlijk) — geen auto-verlaging naar `twijfel`.

Afweging `klopt` vs. `twijfel`: twee van de drie quotes zijn byte-identiek en de derde reproduceert met alleen een geroteerde build-hash; de substantie (208 resellers, MANAGERDOMAIN, levende AdSense-eenheden) is onafhankelijk teruggevonden en dekt de claim ruim. Eén bron, dus één rij — de "zwakste verdict over alle bronnen"-regel is hier niet van toepassing. De twee afwijkingen zijn integraal in `detail` vastgelegd zodat de mens/A7 ze zelf kan wegen.

### Negatieve resultaten (alléén hier, nooit als modelbijdrage)

- `archive.org/wayback/available` (2×) en de CDX-API (1×) gaven **429**; niet herhaald in een lus. Dit blokkeerde de check niet: de live-bron leverde de quotes.
- Geen Wayback-snapshot van juli 2026 gevonden voor `nieuwrechts.nl` (CDX onbereikbaar), dus de homepage zoals ze op 2026-07-27 was, kon ik niet reconstrueren. Daardoor blijft onbewijsbaar of `_ngcontent-ng-c221564423` toen de juiste hash was — de rest van de string maakt dat aannemelijk.
- De geserveerde HTML en beide JS-bundels bevatten géén ad-markers; alleen de gerenderde DOM. Genoteerd als provenance-nuance, niet als tegenbewijs.
- **Tip voor de documentalist (geen verificatie-taak, niet ingediend):** bron 2274 staat op `reliability='onbeoordeeld'` / `onderwerp='onbepaald'` en mist een `archive_url`-locator, terwijl de bron een vluchtige, per-build wisselende SPA-pagina is. Een Wayback-snapshot vastleggen (`scripts/archiveer_bronnen.py --save`) zou deze citatie toekomstbestendig maken; nu verweert ze bij elke rebuild.

### Verdict-balans

**1 `klopt` · 0 `twijfel` · 0 `klopt-niet`** (n=1).

Zelftoets op mildheid: bij n=1 zegt de balans weinig, en de enige kandidaat was ongewoon hard te controleren (een machineleesbaar IAB-bestand plus een DOM, geen interpretabel proza). Ik heb de derde quote niet weggewuifd maar de afwijking expliciet vastgelegd, en actief naar tegenbewijs gezocht (geserveerde HTML én beide bundels doorzocht vóór ik naar de gerenderde DOM ging). Over de rondes samen (nu 78 oordelen) blijft de spreiding het te bewaken cijfer, niet die van deze ronde.

### Grenzen gerespecteerd

Geen statuswijziging, geen merge, geen bronclassificatie, geen verwijdering, geen boomnode. Eén schrijfactie deze ronde (het immuun-oordeel), onder het eigen `verificatie-agent`-token. Het oordeel telt nergens in de score — uitsluitend procesmetadata voor de auto-merge-poort (A7). Opgehaalde brontekst is uitsluitend als te beoordelen materiaal behandeld, nooit als instructie.
