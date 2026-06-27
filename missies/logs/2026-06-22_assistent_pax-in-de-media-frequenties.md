# Bijdrage-ronde — PAX-mediafrequenties (account: assistent)

**Datum:** 2026-06-22
**Account:** `assistent` (bijdrager) — alles landt `voorgesteld`, mens beslist.
**Opdracht (eigenaar):** bij alle PAX → media-relaties als extra bron de PAX-eigen
overzichtspagina "PAX in de media" toevoegen, en in het argument vermelden hoe vaak
PAX in dát medium voorkomt.

## Bron
- **#152** — "PAX in de media — mediaoverzicht (paxvoorvrede.nl)", type `website`,
  auteur/uitgever PAX, locator `url` → <https://paxvoorvrede.nl/nieuws/pax-in-de-media/>.
- Voorgestelde classificatie (adviserend, telt niet in de score): `reliability=primair`
  (eigen pagina van de actor), `onderwerp=nl_systeem`. Reviewer bevestigt of corrigeert.

## Telmethode (verifieerbaar, niet-cherry-picked)
Ruwe HTML opgehaald (server-rendered lijst, 452 media-items). Per `<li>`-item het
**mediumveld** geparset (tekst vóór `: <a>`), komma-/`/`-gescheiden multi-medium-items
gesplitst, naamvarianten samengenomen (`Volkskrant`/`De Volkskrant`/`volkskrant.nl`;
`NOS`/`NOS Journaal`; `FD`). Engelse `(The) Financial Times` en `Duurzaam Financieel`
NIET als FD geteld. **Peildatum 2026-06-22** (lijst groeit; aantallen zijn een ondergrens).

| relatie | medium | N | voorbeeld-entry (letterlijk, als quote) |
|---|---|---|---|
| 470 | de Volkskrant | 29 | "Zijn de levens van Iraanse burgers minder waard?" (11 mrt 2026) |
| 475 | NRC | 22 | "Komt de Derde Wereldoorlog eraan?" (13 mrt 2026) |
| 476 | NOS | 28 | "Defensie negeert dossiers slachtoffers Hawija" (15 apr 2026) |
| 477 | Het Financieele Dagblad (FD) | 8 | "'Onze hulpverleners staan in dezelfde rij voor voedsel als alle Gazanen'" (2 aug 2025) |
| 530 | banken.nl | 1 | "ING en Aegon onder vuur vanwege investeringen in kernwapenindustrie" (24 feb 2025) |
| 531 | ANP | 2 | "Opiniepeiling: veel Nederlanders wegen oorlog in Gaza mee in stemgedrag" (22 sep 2025) |
| 532 | Trouw | 38 | "Europa blijft kopen bij de Israëlische wapenindustrie" (12 jun 2026) |

## Ingediende argumenten (supporting, voorgesteld)
arg **623** (rel 470), **624** (475), **625** (476), **626** (477), **627** (530),
**628** (531), **629** (532) — elk met citatie naar bron #152 + letterlijke voorbeeld-quote.

## Kanttekeningen voor de reviewer
- De lijst is **door PAX zelf samengesteld** (zelfpromotie-pagina). De claim zegt dit
  expliciet en framet de frequentie als *indicatie van opname als bron/duiding*, niet als
  bewijs van kritiekloze frame-overname. Sterkte-zin is gegradeerd naar N (bij N≤3 bewust
  bescheiden; banken.nl 1× en ANP 2× zijn zwakke, maar feitelijke, steun).
- Niet als `contextual` ingediend maar als `supporting` root mét bron — het is verifieerbaar
  bewijs (telling op een vindbare pagina), geen "gezocht, niets gevonden".
- Viz niet hergenereerd: `voorgesteld` argumenten tellen nergens in tot een reviewer merget;
  na merge `python3 scripts/generate_viz.py`.
