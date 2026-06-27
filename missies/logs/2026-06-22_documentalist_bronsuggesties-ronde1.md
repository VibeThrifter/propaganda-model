# Documentalist — bron-suggesties voor probleem-argumenten, ronde 1

**Datum:** 2026-06-22
**Brief:** `missies/documentalist_brief.md` (sectie "Bron-suggesties voor probleem-argumenten")
**Uitvoer:** `data/bron_suggesties.json` (adviserend, telt nergens mee; vervangt het eerdere demo-bestand)
**Account:** geen schrijf-API gebruikt — alleen het advies-bestand geschreven + read-only DB/queue gelezen.

## Doelwitten (opgehaald)

Bronloze ingediende roots (`ongesourcet_root`, uit `/api/review_queue`): #542, #543.
Afgewezen argumenten (status verworpen): #536, #537, #540, #541. Alle zes gaan over PAX.

## Queries (webonderzoek)

WebSearch:
1. `PAX vredesorganisatie financiering ministerie Buitenlandse Zaken subsidie jaarverslag`
2. `"Don't Bank on the Bomb" PAX rapport pensioenfonds nieuws NRC Volkskrant`
3. `PAX conflictanalist geciteerd NRC NOS Nieuwsuur expert duiding`
4. `PAX vredesorganisatie draaideur personeel ministerie Buitenlandse Zaken ngo overheid`
5. `oud-PAX medewerker Tweede Kamer politiek GroenLinks D66 overstap`
6. `PAX expert Nieuwsuur NOS Journaal conflict analyse bezuinigingen ontwikkelingssamenwerking`

WebFetch (verificatie vóór opname):
- wyniasweek.nl (PAX-financiering) → bevestigd: ±80% overheidssubsidie, onafhankelijkheid betwist.
- banken.nl/…/27059 (DBotB) → bevestigd: neemt DBotB-data over, citeert PAX-onderzoeker A. Muñoz.
- nos.nl/artikel/2537765 (OS-bezuinigingen) → bestaat, maar **citeert PAX niet** (wel Partos/Sargentini) → niet opgenomen bij #543.
- paxvoorvrede.nl/nieuws/pax-in-de-media → bevestigd: optredens NRC (F-35, feb 2024), NPO Radio 1 (mei 2025), NOS (aug 2024).
- paxvoorvrede.nl/…/voorkom-de-kaalslag-voor-ontwikkelingssamenwerking → bevestigd: PAX agendeert de bezuinigingen.
- paxvoorvrede.nl/…/dont-bank-on-the-bomb → bevestigd: jaarlijks onderzoeksprogramma.

## Oogst (suggesties geschreven)

- **#542** (PAX als 'onafhankelijke' analist + staatsfinanciering): Wynia's Week (financiering, check=klopt) + PAX-in-de-media (analist-optredens, check=klopt).
- **#543** (PAX bij NOS/NPO + agendering OS-bezuinigingen): PAX 'Voorkom de kaalslag' (agendering, check=klopt) + PAX-in-de-media (NPO Radio 1, check=twijfel — specifieke NOS/Nieuwsuur-uitzending met PAX nog niet gevonden).
- **#536** (media nemen PAX-data over; DBotB in financiële pers): banken.nl (check=klopt) + PAX DBotB-programmapagina (check=klopt).

## Negatieve resultaten (eerlijk: niets bruikbaars gevonden → niet opgenomen)

- **#537** (draaideur PAX ↔ ministerie van Buitenlandse Zaken): geen concrete bron over *personeelscirculatie* gevonden. Wel het algemene financierings-/afhankelijkheidsdebat ("verlengstuk van BuZa"), maar dat staaft de personeels-claim niet. Niet opgenomen.
- **#540** (PAX-medewerkers → politiek, m.n. GroenLinks-PvdA): geen concrete namen/bron gevonden. Niet opgenomen.
- **#541** (PAX-medewerkers → D66): idem, geen concrete bron. Niet opgenomen.
- **'Sintrin-data'** (genoemd in #536): niet teruggevonden; in de reden bij #536 gevlagd voor de admin.

## Opmerking

Alle opgenomen URL's zijn echte, op het web gevonden en (via WebFetch) geverifieerde bronnen.
Bij #542/#543 zijn enkele bronnen PAX' eigen perslijst — bruikbaar als wegwijzer, maar voor een
citatie in het model is het onderliggende NRC-/NOS-artikel zelf nodig (genoteerd in de check).
Niets is in het model ingediend; dit is beslissteun voor de admin.
