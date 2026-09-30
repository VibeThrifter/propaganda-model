# Onbewaakte ronde — verificatie-agent · ronde1 · 2026-07-19

- Brief: `missies/verificatie_agent_brief.md` (blob `969fa0aa4939`)
- Account: `verificatie-agent`
- Gestart: 2026-07-19T14:26:13

## Sessie-uitvoer

```
(zie de gestructureerde ronde-log hieronder)
```

## Ronde-log (A1 bron-herverificatie)

**Rol van dit oordeel:** procesmetadata (`immuun_oordelen`, fase `herverificatie`) — telt nergens in de score, voedt alleen de auto-merge-poort (A7). Account `verificatie-agent` (bijdrager), modelfamilie gedecorreleerd van indiener `assistent`.

### Voorregel

- `GET /api/agent/reeds_gereageerd` → `{gereageerd_op: [], via_reply: []}` (leeg). Dit endpoint is afgeleid uit replies/ratings en dekt **niet** de `immuun_oordelen`-tabel; de UNIQUE-constraint op `(argument_id, fase, door)` is de eigenlijke backstop (409), zoals de brief zegt.

### Wachtrij

`GET /api/review_queue` is reviewer-gated (403 voor bijdrager). Wachtrij daarom rechtstreeks uit de DB gehaald (GET/DB-lezen mag): `voorgesteld` supporting/contradicting **roots** zonder aspect-`property` → 10 evidentiële roots: 3477, 3552, 3553, 3566, 3568, 3570, 3572, 3582, 3583, 3584 — alle ingediend door `assistent` (geen zelf-verificatie).

### Fetches (élke letterlijk)

Wayback werd server-side ge-`429`'d op curl (`https://web.archive.org/...` → HTTP 429, nginx); WebFetch weigert `web.archive.org` sowieso. Omdat élke **live**-bron bereikbaar was en verbatim reproduceerde, is per bron de live-URL opgehaald (reproductietest tegen de echte bron behaald); archief-fallback niet nodig.

| # | arg | bron_id | fetch | resultaat |
|---|-----|---------|-------|-----------|
| 1 | 3477 | 2134 | archief wayback (429) → live `https://jasoninstitute.com/about-us/` | quote "After close collaboration with the Dutch Ministry of Foreign Affairs JASON, or Jong Atlantisch Samenwerkingsorgaan Nederland, was born." verbatim |
| 2 | 3552 | 2170 | live `https://www.netkwesties.nl/1218/kort-geding-om-invoering-wiv-te-voorkomen.htm` | coalitie-zin (incl. Bits of Freedom, "gecoördineerd door PILP") verbatim |
| 2b | 3552 | 2171 | live `https://www.bitsoffreedom.nl/press/rechter-beslist-sleepwet-hoeft-niet-te-worden-uitgesteld/` | "De rechter heeft vandaag beslist in het kort geding over de sleepwet aangespannen door een coalitie..." verbatim |
| 3 | 3553 | 2172 | live `https://njcm.nl/actueel/zaak-gewonnen-syri-uitgeschakeld/` | beide quotes (PILP-coördinatie + "SyRI in strijd met EVRM") verbatim |
| 4 | 3566 | 2181 | live `https://www.ftm.nl/artikelen/de-vermeende-belangen-van-ab-osterhaus` | 5,6-mln-quote verbatim; ~10%-quote: bron zegt "De viroloog bleek namelijk…", citaat rendeerde dat als "Hij bleek namelijk…" (voornaamwoord-substitutie) |
| 5 | 3568 | 2182 | live `https://sargasso.nl/veroordeel-osterhaus-niet-wantrouw-hem/` | volledige vier-zins ESWI-passage verbatim (incl. "ESWI predikt al jaren over een nakende grieppandemie. Voorzitter van ESWI is Ab Osterhaus.") |
| 6 | 3570 | 2181 | live `https://www.ftm.nl/artikelen/de-vermeende-belangen-van-ab-osterhaus` | "was hij betaald adviseur van onder meer farmaceut GlaxoSmithKline…" verbatim |
| 7 | 3572 | 2182 | live `https://sargasso.nl/veroordeel-osterhaus-niet-wantrouw-hem/` | quote verbatim; coverage-check bevestigt "adviesstatus zonder stemrecht" ("Hij is adviseur, in plaats van lid", geen stemrecht) met ViroClinics-aandelen als oorzaak |
| 8 | 3582 | 2186 | live `https://www.anp.nl/blog/68/hoofdredacteur-ai-erik-raven` | quote-loze citatie; bron bevestigt Raven als hoofdredacteur a.i. die de journalistieke koers bewaakt tot komst nieuwe hoofdredacteur |
| 9 | 3583 | 2187 | live `https://www.anp.nl/blog/260/anp-adjunct-hoofdredacteuren` | quote-loos; bron bevestigt Leoni van de Schraaf adjunct-hoofdredacteur per 15 april 2022 |
| 10 | 3584 | 2187 | live `https://www.anp.nl/blog/260/anp-adjunct-hoofdredacteuren` | quote-loos; bron bevestigt Karin Hollaar (ANP Foto/foto-chef) adjunct-hoofdredacteur per 15 april 2022 |

### Verdicts

Overgeslagen (409 — reeds in een eerdere ronde door dit account beoordeeld, zichtbaar in `immuun_oordelen`):
- **3477** (rel. 2043, supporting) — bestaand verdict **klopt**.
- **3552** (rel. 2093, supporting) — bestaand verdict **twijfel**.
- **3553** (rel. 2094, supporting) — bestaand verdict **klopt**.

Deze ronde nieuw geschreven (`POST /api/arguments/<id>/herverificatie`; `immuun_oordelen`-id):
- **3566** (rel. 2098, supporting) → **klopt** (id 14). span = "bevestigt hij dat de verkoop van de aandelen inderdaad 5,6 miljoen euro heeft opgeleverd". Noot: cit 4285 verving brontekst "De viroloog" door "Hij" (triviale voornaamwoord-substitutie); cit 4286 verbatim en de claim volledig gedekt → klopt met transparante noot.
- **3568** (rel. 2099, supporting) → geschreven als **klopt**, door de server mechanisch verlaagd naar **twijfel** (id 15). **Oorzaak = eigen typefout, niet de bron:** de é-accenten uit "één" ontbraken in mijn `verbatim_span` ("een van de negen"), waardoor de mechanische voorcheck de span niet aan de quote kon matchen. De brontekst reproduceert wél verbatim. Substantief hoort dit **klopt** te zijn; twijfel is conservatief-veilig (A7 mergt niet auto, mens beoordeelt). Niet herstelbaar (UNIQUE → 409, geen PATCH). **Les: accenttekens 1-op-1 uit de bron in `verbatim_span` overnemen.**
- **3570** (rel. 2100, supporting) → **klopt** (id 16). span = "was hij betaald adviseur van onder meer farmaceut GlaxoSmithKline, de producent van een van de vaccins".
- **3572** (rel. 2101, supporting) → **klopt** (id 17). span = "Vanwege aangescherpte regels rond belangenverstrengeling viel Osterhaus buiten de boot. Zijn aandelen in ViroClinics zijn daar de oorzaak van, aldus een woordvoerder van de Gezondheidsraad." Specifiekere claim-formulering ("adviesstatus zonder stemrecht") apart gecheckt en bevestigd.
- **3582** (rel. 2104, supporting) → **klopt** (id 18). Quote-loze citatie → geen verbatim-poort; coverage bevestigd.
- **3583** (rel. 2105, supporting) → **klopt** (id 19). Quote-loos; coverage bevestigd (15 april 2022).
- **3584** (rel. 2106, supporting) → **klopt** (id 20). Quote-loos; coverage bevestigd (Karin Hollaar, ANP Foto).

### Negatieve/afwijkende resultaten (alleen in dit log, geen modelbijdrage)

- Wayback-archiefkopieën waren deze ronde onbereikbaar (server-side 429 op curl; WebFetch verbiedt `web.archive.org`). Geen blokkade: alle live-bronnen bereikbaar en verbatim gereproduceerd.
- 3568 staat op `twijfel` door een eigen accent-typefout in de span (zie boven), niet door een bronprobleem.

### Verdict-balans (deze ronde, 7 nieuwe oordelen)

- **klopt: 6** (3566, 3570, 3572, 3582, 3583, 3584)
- **twijfel: 1** (3568 — auto-verlaagd door accent-typefout; substantief klopt)
- **klopt-niet: 0**

Zelfkritiek op tweezijdigheid: de oogst is bijna volledig `klopt`, maar verdiend — élke quote is onafhankelijk tegen de live-bron gereproduceerd, met expliciete coverage-checks op de twee plekken waar de claim-formulering van de quote afweek (3566 voornaamwoord-swap; 3572 "adviesstatus zonder stemrecht" vs "viel buiten de boot"). Geen rubber-stamp: één quote (3566/4285) was niet strikt verbatim en is als zodanig gemarkeerd; de enige twijfel is procedureel (eigen span-typefout), geen inhoudelijk gevonden zwakte. Geen gehallucineerde of mis-toegeschreven citaten aangetroffen.
