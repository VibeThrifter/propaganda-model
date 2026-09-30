# Onbewaakte ronde — verificatie-agent · ronde1 · 2026-07-27

- Brief: `missies/verificatie_agent_brief.md` (blob `969fa0aa4939`)
- Account: `verificatie-agent`
- Gestart: 2026-07-27T13:36:27

## Sessie-uitvoer

**Taak:** A1 — onafhankelijke bron-herverificatie van `voorgesteld` supporting/contradicting-roots.

### Voorregel & wachtrij

- `GET /api/agent/reeds_gereageerd` (met eigen token) → `{"gereageerd_op": [], "via_reply": []}` — leeg, want dat spoor is afgeleid van replies/ratings, niet van `immuun_oordelen`.
- `GET /api/review_queue` → **403** ("Rol 'reviewer' of hoger vereist (jouw rol: bijdrager)"). Wachtrij daarom rechtstreeks uit de DB gelezen (toegestaan per agent-contract: "find target ids straight from the DB").
- Query: `status='voorgesteld' AND parent_argument_id IS NULL AND NOT vervangen AND stance IN (supporting,contradicting) AND (property IS NULL OR property='influence')`, minus de argument-id's waar ik al een `herverificatie`-oordeel op gaf → **17 evidentiële roots** (3712–3729, ingediend door `assistent` op 2026-07-26).
- Reeds beoordeeld in eerdere rondes: 60 `herverificatie`-rijen — geen daarvan overlapt met deze 17. Geen enkel argument dubbel beoordeeld.
- Drie clusters: (1) Sophie Straat / flak, (2) NieuwRechts als redactie-entiteit, (3) redactiesamenstelling → berichtgeving (SVDJ / NPO Radio 1 / NOS / twee peer-reviewed papers).

### Fetch-log (archief eerst, conform brief)

Alle zes web-bronnen hadden een Wayback-snapshot (`archive.org/wayback/available` gecheckt vóór elke fetch); **de archiefkopie is in alle zes gevallen gebruikt**, niet de live-URL. Tijdstip: 13:38–13:52 lokaal.

| Bron | Opgehaald | Resultaat |
|---|---|---|
| src2266 (NOS, Sophie Straat) | `web.archive.org/web/20260726024805/https://nos.nl/artikel/2624161-…` | OK (6.708 tekens) |
| src2267 (VRT NWS, Gentse Feesten) | `web.archive.org/web/20260724092734/https://www.vrt.be/vrtnws/nl/2026/07/21/sophie-straat-ophef-gentse-feesten/` | OK (5.089) |
| src2268 (NieuwRechts, /wie-zijn-wij) | `web.archive.org/web/20260215135126/https://nieuwrechts.nl/wie-zijn-wij` | OK (3.085) |
| src2268 (idem, **live** ter controle) | `https://nieuwrechts.nl/wie-zijn-wij` | OK (2.789) — tekst identiek aan het archief |
| src2269 (SVDJ) | `web.archive.org/web/20260118052233/https://www.svdj.nl/nieuws/politieke-kleur-op-de-redactie-…/` | OK (10.554) |
| src2270 (NPO Radio 1) | `web.archive.org/web/20210515235311/https://www.nporadio1.nl/cultuur-media/29225-…` | OK (4.985) |
| src2271 (over.nos.nl) | `web.archive.org/web/20260517174833/https://over.nos.nl/nieuws/de-scherpe-discussie-over-diversiteit/` | OK (7.108) |
| src2272 (DOI 10.1080/10584609.2026.2621169) | `api.crossref.org/works/10.1080/10584609.2026.2621169` + `api.openalex.org/works/doi:…` | OK — metadata + volledige abstract |
| src2273 (DOI 10.1126/sciadv.aay9344) | `api.crossref.org/works/10.1126/sciadv.aay9344` + `api.openalex.org/works/doi:…` | OK — metadata + volledige abstract |

Extra controlefetches (fair-play richting de indiener, om te kijken of een niet-teruggevonden quote elders op hetzelfde domein stond):

- `https://nieuwrechts.nl/` → og:description = "NieuwRechts.nl - Nieuws voor rechtsdenkend Nederland"; de opgegeven quote staat er niet.
- `https://nieuwrechts.nl/nieuwsbrief` → "DÉ NIEUWSBRIEF VOOR RECHTSDENKEND NEDERLAND" — dus *nieuwsbrief*, niet *nieuwswebsite*. "Word lid … Start je gratis maand" nergens in de HTML (vermoedelijk JS-knoplabel).

**Negatieve resultaten (alleen hier, nooit als modelbijdrage):** geen enkele bron was onbereikbaar; `tandfonline.com` en `science.org` zijn bewust niet benaderd omdat Crossref + OpenAlex de titel, auteurs, jaar én de volledige abstract leverden — voldoende voor zowel de verbatim- als de dekkingscheck.

Verbatim-check mechanisch uitgevoerd: HTML → platte tekst, beide zijden genormaliseerd (lowercase, diakrieten gevouwen, interpunctie weg, witruimte gecollapst), daarna exacte substring-test + langste-gemeenschappelijke-blok als de test faalde.

### Oordelen per argument

| arg | doel/onderwerp | stance | bron | verdict | kern |
|---|---|---|---|---|---|
| 3712 | Derksen diskwalificeert Straat | supporting | 2266 | **twijfel** | Beide quotes staan verbatim in de NOS-tekst, maar de NOS **citeert Straats Instagram-bericht waarin zíj Derksen citeert** — tweedehands attributie, de NOS registreert de uitspraak niet zelf (anders dan de reasoning stelt). |
| 3713 | Golf haatberichten/bedreigingen | supporting | 2267 (+2266) | **twijfel** | Beide quotes verbatim ✓, maar **de datering klopt niet**: beide bronnen leggen de golf bij de eerste uitspraak (Best Kept Secret, vorige maand) — NOS: "Sinds de eerste uitspraak kreeg Straat een stortvloed aan online haat" — niet bij de Gentse Feesten (21-07-2026), waar ze de oproep herhaalde. |
| 3715 | NieuwRechts-positionering | supporting | 2268 | **twijfel** | **Geen van beide quotes staat op de pagina**, terwijl `methode='verbatim_quote'` is opgegeven. De claim wordt wél gedekt door de echte zin ("NieuwRechts.nl is een nieuwswebsite voor rechts en conservatief denkend Nederland"). Citaten moeten vervangen. |
| 3716 | Ledenabonnementen/subsidievrij | supporting | 2268 | **twijfel** | Quote niet in de HTML. Wél letterlijk: "Steunt u ons onafhankelijke, kritische en bovenal **subsidievrije** geluid?" en "Doet u liever een vrijblijvende **donatie**?" — 'ledenabonnementen' wordt op deze pagina niet expliciet. |
| 3717 | Reijmerink hoofdredacteur | supporting | 2268 | **twijfel** | Quote is parafrase ("Het kernteam bestaat uit…") van "De nieuwsredactie van NieuwRechts bestaat uit drie redacteuren (v.l.n.r.: …)". Feit zelf volledig gedekt. |
| 3718 | Nubé redacteur + omroep-reeks | supporting | 2268 | **twijfel** | Zelfde parafrase, én de **tweede claimhelft** (zij schrijft de reeks over partijdigheid/overheidsbanden bij de publieke omroep) staat niet op `/wie-zijn-wij` — vergt een citatie naar de artikelen zelf. |
| 3719 | De Liever redacteur | supporting | 2268 | **twijfel** | Zelfde parafrase; feit gedekt. |
| 3720 | Worlds of Journalism Study | supporting | 2269 | **klopt** | Beide quotes verbatim; ook "elke vier jaar" en "ongeveer zeshonderd Nederlandse journalisten" exact; attributie aan Merel Borger (Windesheim) klopt. |
| 3721 | Interne peiling DvhN/LC | supporting | 2269 | **twijfel** | Quote geconstrueerd. **Materiële afwijking:** de bron zegt "Van de 160 medewerkers deden er **110** mee" — de 60% is dus het aandeel van 110 respondenten, niet van 160. Zelfselectie groter dan de claim suggereert. |
| 3722 | Borger: stap is een aanname | contradicting | 2269 | **twijfel** | Quote staat niet in de bron (samenvattende zin). De bron zegt het sterker: "Een interessante vraag is volgens Borger of linkse journalisten ook per se linkse inhoud maken. 'Dat is alleen een veronderstelling.'" Claim inhoudelijk volledig gedekt. |
| 3723 | Non-respons rechtse journalisten | contradicting | 2269 | **twijfel** (auto-verlaagd, zie hieronder) | Quote wél verbatim teruggevonden en correct toegeschreven. Kanttekening voor de reviewer: "meetartefact" en "vertekent naar links" zijn de eigen gevolgtrekking van de indiener, geen bronbewering. |
| 3724 | Driekwart hoofdredacteuren | supporting | 2270 | **twijfel** | Getal klopt ("Ongeveer driekwart zegt diversiteit van belang te vinden"), maar het **scharnier** van de claim — de *expliciete grond* dat eenzijdige samenstelling blinde vlekken in de berichtgeving oplevert — staat niet in de bron. De geciteerde quote is bovendien een **advies van onderzoeker Klein**, niet een uitspraak van een hoofdredacteur. |
| 3725 | NOS-hoofdredacteur koppelt samenstelling↔berichtgeving | supporting | 2271 | **twijfel** | Alle drie quotes zijn ingekorte parafrases (o.a. "Dat lukt niet als onze redacteuren overwegend uit de Randstad komen"). Inhoudelijk dekt Gelauff de claim volledig; alleen de citaten moeten letterlijk. |
| 3726 | Systematische onder-representatie | supporting | 2271 | **twijfel** | Kernquote verbatim ✓, vrouwelijke experts en provincie-spreiding ook gedekt. Maar "**ondanks cursussen, jaarplannen** en beleid" staat niet in de bron — die zegt "ondanks alle goeie bedoelingen". Toegevoegd detail. |
| 3727 | Riedl e.a., subjectiviteit | supporting | 2272 | **twijfel** | Methodecijfers exact ("n = 3,539" + "survey of 160 journalists who authored 626 of those items"). Quote niet letterlijk: genitief omgezet t.o.v. "the left-right political orientation of journalists affects the use of subjectivity in reporting". |
| 3728 | Riedl e.a., tegengestelde richting | contradicting | 2272 | **twijfel** | Quote **plakt twee zinnen samen** en herschrijft er één ("There is only a tentative impact…" → "with only a tentative impact…"). Inhoud, inclusief de correctie-these ("may act as 'correctives'"), volledig gedekt. |
| 3729 | Hassell e.a., geen selectie-bias | contradicting | 2273 | **klopt** | Quote = de artikeltitel, letterlijk. Correspondentie-experiment en de scope-beperking tot storyselectie staan in de abstract zelf, niet toegevoegd door de indiener. |

**Eigen fout, transparant gelogd:** bij 3723 diende ik `klopt` in, maar in mijn `verbatim_span` tikte ik "rechtsgeorienteerde" zonder trema. `_normaliseer_tekst` in `server.py` vouwt alléén lowercase + witruimte (geen diakrieten), dus de mechanische voorcheck vond de quote niet in mijn span en verlaagde het verdict automatisch naar `twijfel` (oordeel 102, detail draagt het `[auto]`-voorvoegsel). De poort deed precies wat hij moet doen; herindienen kan niet (`UNIQUE(argument_id, fase, door)` → 409). Het effect is conservatief, dus onschadelijk — maar het feitelijke bevinding was `klopt`.

### Geschreven oordelen

17 × `POST /api/arguments/<id>/herverificatie` (allemaal **201**), `immuun_oordelen`-rijen **92–103** en **109–113** (fase `herverificatie`, `model_familie` uit de account-provenance). Geen 429, geen 403, geen 409. Geen enkele statuswijziging, merge, bronclassificatie of verwijdering — en geen enkele `contextual` "niets gevonden"-modelbijdrage.

### Verdict-balans

**2 × klopt · 15 × twijfel · 0 × klopt-niet** (3723 was inhoudelijk een derde `klopt`, auto-verlaagd door mijn eigen trema-fout).

Zelfcontrole op mildheid: dit is géén milde ronde — 15 van de 17 kregen een kanttekening. Het dominante patroon is systematisch en het melden waard: **de citaatvelden bevatten grotendeels LLM-samenvattingen in plaats van letterlijke passages** (11 van de 17 quotes waren niet verbatim), terwijl de onderliggende claims in bijna alle gevallen wél door de bron gedekt worden. De uitzonderingen waar de *claim* zelf schuurt — en die een mens moet wegen — zijn:

1. **3721** — 110 van de 160, niet 160 (noemer verkeerd).
2. **3724** — de causale grond, het scharnier van het argument, staat niet in de bron; de quote is van de onderzoeker, niet van een hoofdredacteur.
3. **3713** — golf gekoppeld aan het verkeerde optreden.
4. **3712** — tweedehands attributie (NOS citeert Straat die Derksen citeert).
5. **3726** — "cursussen, jaarplannen" toegevoegd aan wat de bron zegt.

Geen `klopt-niet`: in geen enkel geval sprak de bron de claim tegen of bleek een feit verzonnen — het gaat consequent om citeerdiscipline en om enkele te ver doorgetrokken formuleringen.

**Tip voor andere missies (geen verificatietaak, dus niet ingediend):** voor 3718 ontbreekt een citatie naar de NieuwRechts-artikelen van Nubé zelf; voor 3716 zou een citatie naar de lidmaatschaps-/donatiepagina de "ledenabonnementen"-helft afdekken.
