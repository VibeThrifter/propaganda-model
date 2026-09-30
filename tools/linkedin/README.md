# LinkedIn → model: gerichte netwerk-ontdekking

Een **tweetraps, ontkoppelde** integratie om vanaf LinkedIn-profielen de banden tussen
personen en organisaties/opleidingen/clubs in het model te brengen — precies wat de
draaideur/brug-discipline van dit project vraagt: een loopbaan is een reeks gedateerde
`persoon→organisatie`-affiliaties, en de org↔org-verwevenheid rolt er als *afgeleide
brug* vanzelf uit.

```
  LinkedIn-profiel ──(trap 1: scrape)──► genormaliseerd JSON ──(trap 2: mapper)──► REST-API (voorstellen)
     scrape_profile.py                    data/linkedin/*.json    linkedin_naar_model.py     alles 'voorgesteld'
     Playwright, fragiel, ToS-gevoelig    het contract           pure stdlib, getest        een mens beslist
```

De twee helften zijn **bewust losgekoppeld via een JSON-contract** (`normalize.py`).
Waarom: de scrape-kant leunt op een externe bibliotheek (`linkedin_scraper`) die tegen
LinkedIn's voorwaarden werkt en per versie kan breken. De model-kant is de waardevolle,
volledig testbare helft. Breekt de scraper, dan lever je met wat dan ook hetzelfde JSON
aan en de mapper werkt ongewijzigd door.

## ⚠️ Scraping-beleid (gericht, geen bulk) — J4, gewijzigd 2026-09-30

Dit is **beleid, niet alleen advies**: een deel ervan zit als machinale rem in de tool
(de profiel-cap én de snelheidsrem hieronder). LinkedIn-scrapen is bewust *gericht* —
bulk/proxy-scrapen is onevenredig risico (ToS-schending, account-ban, AVG) voor weinig
opbrengst. De regels:

1. **Harde bovengrens per run én per uur/dag: een handvol relevante profielen, nooit een
   crawl-lijst.** De tool weigert een batch **> 5 profielen** in één run (`PROFIEL_CAP`,
   geldt voor zowel `scrape_profile.py` als `linkedin_naar_model.py`); de override
   `--ik-weet-het` bestaat alleen voor uitzonderlijk, aantoonbaar gericht onderzoek —
   níét om er een bulk-crawl mee te draaien. Daarbovenop staat sinds 2026-09-30 de
   **snelheidsrem** (`snelheidsrem.py`, zie § Snelheidsrem): **max 2 per uur en 10 per
   dag**, apart geteld voor profiel-scrapes en zoekacties, alleen **08:00–22:00**, met
   willekeurige pauzes en een **stroomonderbreker** (24 uur stop bij
   captcha/checkpoint/authwall, verdubbelend bij herhaling tot max 7 dagen). Die rem geldt
   voor élke run — ook een handmatige. Kies profielen per **onderzoeksvraag**, niet per
   lijst.
2. **Headful, onder je eigen sessie.** De scraper draait standaard *headful* (zichtbaar
   venster) met een handmatige login; geen headless bot-farm. De opgeslagen sessie is die
   van de eigenaar zelf.
3. **Pauze tussen requests.** Tussen twee profielen pauzeert de tool (menselijk tempo,
   minder botdetectie); een rate-limit van de eigen API wordt netjes afgewacht
   (`time.sleep(62)`).
4. **Geen residentiële proxy's, geen IP-rotatie, geen bot-netwerk.** Bewust niet
   ingebouwd en bewust niet toe te voegen — dat is precies de onevenredig-risicovolle lijn
   die J4 uitsluit.
5. **Automatisch mag — alleen achter de snelheidsrem en alleen voor de nieuws-wachtrij
   (eigenaarsbesluit 2026-09-30).** Tot september 2026 was scrapen eigenaar-getriggerd
   (geen onbewaakte runs). De eigenaar heeft dat bewust gewijzigd: de missie-agent
   `nieuws-scout` mag de tool nu **onbewaakt** gebruiken, maar uitsluitend (a) achter de
   snelheidsrem hierboven, (b) gericht op personen **met een publieke rol**
   (politici, journalisten, woordvoerders, bestuurders; daarna experts) die als doel in
   de wachtrij `nieuws_doelen` staan — nooit privépersonen, nooit een lijst — en (c) in
   een zichtbaar venster onder de eigen sessie van de eigenaar. Nog steeds **geen strak
   24/7-schema**: buiten 08–22 uur weigert de rem, en boven 2/uur of 10/dag ook.
   Kill-switch: `LINKEDIN_AUTOMATISCH=0` (env) of `python3 tools/linkedin/snelheidsrem.py uit`.

**Bronprioriteit — LinkedIn is aanvulling, geen hoofdweg.** Primaire structuurbronnen
zijn de risicoarme, gezaghebbende registers: **KvK, jaarverslagen, publieke registers
(handelsregister, ANBI, toezichthouders), en nieuws**. LinkedIn vult die aan waar een
loopbaan/nevenfunctie er niet uit blijkt — het is *zelf-gerapporteerd* en zwak. Voor
due-diligence (E2) worden register-mappers de hoofdweg; LinkedIn blijft secundair.

**AVG-zorgvuldigheid.** Verwerk alleen wat mensen zelf publiek op hun profiel zetten; het
blijft persoonsgegevens — behandel het zorgvuldig. De ruwe scrapes staan in
`data/linkedin/` (**gitignored**, verlaten het apparaat niet). LinkedIn-data is
**zelf-gerapporteerd → lage betrouwbaarheid**: de mapper stelt bronklasse `grijs` voor en
zet géén certainty/influence. Elk verband landt `voorgesteld` en wacht op een menselijke
reviewer voordat het meetelt.

## Installatie (alleen voor trap 1 — scrapen)

De kern-app blijft pure stdlib + Flask; deze deps staan geïsoleerd in een eigen venv:

```bash
python3 -m venv tools/linkedin/.venv
source tools/linkedin/.venv/bin/activate
pip install -r tools/linkedin/requirements.txt
playwright install chromium
```

Trap 2 (de mapper) heeft **niets** hiervan nodig — die draait op de gewone `python3`.

## Gebruik

**1. Eenmalig inloggen** (opent een venster; log handmatig in, sessie wordt bewaard):

```bash
python3 tools/linkedin/scrape_profile.py login
```

> **Sessie verlopen?** De opgeslagen cookies leven doorgaans dagen–weken. Is de sessie
> verlopen, dan controleert de scraper dat vóór het scrapen (`is_logged_in` op `/feed/`)
> en stopt met een duidelijke fout — je krijgt géén misleidend-leeg profiel. Draai
> gewoon opnieuw `… login` om de sessie te verversen.

**2. Een profiel scrapen** → genormaliseerd JSON in `data/linkedin/`:

```bash
python3 tools/linkedin/scrape_profile.py "https://www.linkedin.com/in/<slug>/"
python3 tools/linkedin/scrape_profile.py --bedrijf "https://www.linkedin.com/company/<slug>/"
```

**2b. Een persoon zoeken** (people-search in de ingelogde sessie) → JSON-lijst op stdout,
om het juiste profiel te vinden vóór je scrapet (naamgenoten!):

```bash
python3 tools/linkedin/scrape_profile.py zoek "Anouk Verbeek" --context "Gemeente Dijkerhoven" --max 5
# → [{"naam": "...", "kop": "...", "locatie": "...", "url": "https://www.linkedin.com/in/<slug>/"}, ...]
```

De parser leest de gerenderde tekst + de profiel-links (`a[href*='/in/']`), niet de
geobfusceerde CSS-klassen. Een zoekactie telt onder soort `zoek` in de snelheidsrem.
Gebruik een resultaat alleen als naam **én** organisatie/rol overeenkomen met de context.

**3. In kaart brengen** — eerst droogloop (schrijft niets), dan echt indienen:

```bash
# Laat zien wat er zou worden voorgesteld:
python3 tools/linkedin/linkedin_naar_model.py data/linkedin/<slug>.json

# Dien in (alles landt 'voorgesteld', onder het scout-account):
python3 tools/linkedin/linkedin_naar_model.py data/linkedin/<slug>.json --indienen --volledig
```

Opties van de mapper:

| Optie | Effect |
|---|---|
| *(geen `--indienen`)* | **droogloop** — print het plan, schrijft niets (default) |
| `--indienen` | dient de voorstellen echt in via de API |
| `--volledig` | ook opleidingen én lidmaatschappen (default: alleen loopbaan) |
| `--met-opleiding` / `--met-lidmaatschappen` | een van beide los aanzetten |
| `--alles-kandidaat` | ken géén mechanisme toe (alle relaties als kandidaat) |
| `--persoon-rol journalist` | rol-suggestie voor de persoon-knoop |
| `--ik-weet-het` | override de profiel-cap (>5 JSON's in één run); alleen voor aantoonbaar gericht onderzoek, nooit bulk |
| `--token <pad>` | ander Bearer-token (default `data/tokens/scout-agent.token`) |
| `--api <url>` | andere API-basis (default `http://localhost:5000`) |

Beide tools nemen **meerdere** profielen aan in één run (`scrape_profile.py <url> <url> …`,
`linkedin_naar_model.py <json> <json> …`), maar weigeren een batch **> 5** zonder
`--ik-weet-het` — de machinale rem achter het "gericht, geen bulk"-beleid hierboven.

De mapper kan zonder browser worden getest tegen de meegeleverde fixture:

```bash
python3 tools/linkedin/linkedin_naar_model.py tools/linkedin/fixtures/voorbeeld_persoon.json --volledig
```

## Snelheidsrem (`snelheidsrem.py`, Epic 12)

Pure stdlib; toestand in `data/linkedin/_snelheidsrem.json` (gitignored, fcntl-vergrendeld).
`scrape_profile.py` vraagt vóór élk profiel en élke zoekactie toestemming en telt ná afloop.

```bash
python3 tools/linkedin/snelheidsrem.py status          # tellingen, blokkade, volgende kans
python3 tools/linkedin/snelheidsrem.py status --json   # machineleesbaar (nieuws-backend)
python3 tools/linkedin/snelheidsrem.py mag profiel     # exit 0 = mag, 75 = rem
python3 tools/linkedin/snelheidsrem.py uit             # persistente kill-switch (…) aan
python3 tools/linkedin/snelheidsrem.py reset-blokkade  # eigenaar, na controle in de browser
```

| Situatie | Melding | Exit | Wat een agent doet |
|---|---|---|---|
| Rem weigert (uur/dag vol, buiten 08–22, kill-switch) | `⏳ LINKEDIN-SNELHEIDSREM — volgende kans HH:MM` | 75 | doel `vervolg=linkedin`, door met andere bronnen, niet herproberen |
| Captcha/checkpoint/authwall na een navigatie | `⛔ LINKEDIN-BLOKKADE — …` | 76 | stoppen met LinkedIn, melden; eigenaar controleert het account |
| Sessie verlopen (ongewijzigd) | `⚠ LINKEDIN-SESSIE VERLOPEN` | 1 | login-commando relayen aan de eigenaar |

Env-overrides `LINKEDIN_MAX_PER_UUR`, `LINKEDIN_MAX_PER_DAG`, `LINKEDIN_ACTIEF_VAN`,
`LINKEDIN_ACTIEF_TOT` mogen de rem alleen **strenger** maken; het eigenaarsplafond
(2/uur, 10/dag, 08–22) verruimen vergt een bewuste code-wijziging. Stroomonderbreker:
24 uur → 48 → 96 → max 168 uur (7 dagen); het niveau zakt terug naar 0 na een geslaagde
dag. Test (geen netwerk, nep-klok + fixtures): `python3 tools/linkedin/test_snelheidsrem.py`.

## Hoe het op het model afbeeldt (de discipline)

| LinkedIn | Model | Mechanisme |
|---|---|---|
| Ervaring (baan/bestuur/advies/woordvoering) | `persoon → organisatie`, gedateerd, type uit `BRUG_AFFILIATIE` | `draaideurconstructie` |
| Opleiding | `persoon → onderwijsinstelling` (`lidmaatschap`) | **kandidaat** (reviewer beoordeelt `academische_socialisatie` op opleidingsniveau) |
| Club/lidmaatschap | `persoon → organisatie` (`lidmaatschap`) | **kandidaat** |
| Verwevenheid tussen twee organisaties | *niet opgeslagen* — de **brug** wordt afgeleid uit de gedeelde persoon | — |

Vaste regels (uit `CLAUDE.md`):

- **Nooit** een `organisatie → organisatie`-draaideur/verwevenheids-edge opslaan. De
  band tussen twee organisaties is de afgeleide brug (ongericht, beschrijvend).
- Assen zijn *guilty-until-proven*: geen `certainty`/`influence` meegeven (de 0,05-vloer
  valt vanzelf in); de score komt uit het bewijs.
- Elke affiliatie krijgt een `supporting`-argument mét citatie naar het profiel; de bron
  krijgt een URL-vindplaats zodat de citatiepoort (M0.3) hem accepteert.
- Structureel entiteittype is een **gok** die de mapper conservatief invult
  (`bedrijf`/`onderwijsinstelling`/`stichting`) en die de reviewer bevestigt/corrigeert.

## Bestanden

| Bestand | Rol |
|---|---|
| `normalize.py` | het JSON-contract + `functie→relatietype` + datum-normalisatie (pure stdlib) |
| `extract.py` | **eigen, robuuste persoon-extractie** via de LinkedIn-detailpagina's (`/details/experience/`, `/details/education/`) — leest de gestructureerde tekst, niet de geobfusceerde CSS-klassen |
| `scrape_profile.py` | trap 1 — Playwright-scrape → genormaliseerd JSON (+ `login`, + `zoek`) |
| `snelheidsrem.py` | harde rem onder (automatisch) gebruik: 2/uur, 10/dag, 08–22, stroomonderbreker, kill-switch |
| `test_snelheidsrem.py` | test van de rem + de zoek-/blokkadeparsers (fixtures, geen netwerk) |
| `linkedin_naar_model.py` | trap 2 — mapper → API-voorstellen (droogloop default) |
| `fixtures/voorbeeld_persoon.json` | fictief profiel om de mapper zonder browser te testen |
| `fixtures/zoek_personen_*`, `fixtures/checkpoint_nl.txt` | fictieve zoekpagina + controlepagina voor de parsertests |
| `requirements.txt` | geïsoleerde deps (alleen trap 1) |

> **Waarom een eigen `extract.py`?** De `linkedin_scraper`-bibliotheek (v3.1.2) zoekt naar
> `h1`/`#experience`-selectors die op de huidige LinkedIn niet meer bestaan (nu `h2` +
> gehashte klassen), dus levert ze "Unknown" + 0 ervaringen. `extract.py` omzeilt dat door
> de **detailpagina's** te lezen, waar de volledige loopbaan als schone tekst rendert — óók
> voor niet-connecties. Het:
> - **scrollt tot de pagina niet meer groeit** (infinite scroll; er is géén 'toon meer'-knop
>   op de detailpagina — die zit alleen op de hoofdpagina en linkt hierheen). Getest tot 16
>   rollen terug tot 1995.
> - verwerkt **gegroepeerde rollen** (meerdere functies bij één werkgever: bedrijf-kop +
>   totale-duurregel, dan `[functie, datum]` per rol) én losse entries. De datumregel is het
>   anker; zonder de groep-logica werd de locatie als functie gelezen.
>
> De **company-scrape** (`--bedrijf`) draait nog op de bibliotheek en kan dezelfde
> selector-veroudering hebben.

De missie-brief voor een agent staat in [`../../missies/linkedin_scout_brief.md`](../../missies/linkedin_scout_brief.md);
de onbewaakte nieuws-variant in [`../../missies/nieuws_scout_brief.md`](../../missies/nieuws_scout_brief.md).
