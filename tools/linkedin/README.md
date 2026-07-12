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

## ⚠️ Voorwaarden, risico & reikwijdte

- Geautomatiseerd scrapen **schendt LinkedIn's gebruiksvoorwaarden** en kan je account
  (tijdelijk) blokkeren. Gebruik dit **gericht** (een handvol relevante profielen), met
  mate, onder je eigen sessie — niet als bulk-crawler. De tool draait daarom standaard
  *headful* (zichtbaar venster) met een menselijke login.
- Dit is voor **legitiem onderzoek** naar de structuur van het Nederlandse mediaveld.
  Verwerk alleen wat mensen zelf publiek op hun profiel zetten; het blijft
  persoonsgegevens — behandel het zorgvuldig (`data/linkedin/` is gitignored).
- LinkedIn-data is **zelf-gerapporteerd**: lage betrouwbaarheid. De mapper stelt daarom
  bronklasse `grijs` voor en zet géén certainty/influence. Elk verband wacht op een
  menselijke reviewer voordat het meetelt.

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
| `--token <pad>` | ander Bearer-token (default `data/tokens/scout-agent.token`) |
| `--api <url>` | andere API-basis (default `http://localhost:5000`) |

De mapper kan zonder browser worden getest tegen de meegeleverde fixture:

```bash
python3 tools/linkedin/linkedin_naar_model.py tools/linkedin/fixtures/voorbeeld_persoon.json --volledig
```

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
| `scrape_profile.py` | trap 1 — Playwright-scrape → genormaliseerd JSON (+ `login`) |
| `linkedin_naar_model.py` | trap 2 — mapper → API-voorstellen (droogloop default) |
| `fixtures/voorbeeld_persoon.json` | fictief profiel om de mapper zonder browser te testen |
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

De missie-brief voor een agent staat in [`../../missies/linkedin_scout_brief.md`](../../missies/linkedin_scout_brief.md).
