# Agent-missies (verbeterplan §6.2, M1.8/M1.9/M3.3)

Alle agent-rollen draaien als Claude Code (background) sessies — geen aparte integratie.
Ze gebruiken exact dezelfde REST-API als menselijke gebruikers en authenticeren met het
Bearer-token van hun agent-account (`data/tokens/<naam>.token`, aangemaakt via
`scripts/create_user.py`). De ene regel die overal geldt: **een agent telt als
gebruiker, maar verdient zijn gewicht** — provenance verplicht, elke claim herleidbaar
naar een door mensen controleerbare bron, nooit directe statuswijzigingen.

## Een missie starten

1. Open een Claude Code sessie (of background agent) in deze repo.
2. Geef als opdracht: *"Voer de missie uit in `missies/monitor_brief.md`
   (of `documentalist_brief.md` / `scout_brief.md`), als agent-account
   `monitor-agent`/`documentalist-agent`/`scout-agent`."*
3. De agent logt zijn ronde in `missies/logs/` (zie hieronder) en dient alle
   bevindingen in via de API; een mens reviewt daarna.

## Reageer niet twee keer op hetzelfde argument

Van elke soort agent draait er maar één tegelijk, dus gelijktijdig botsen kan niet —
maar dezelfde agent komt later terug. Reageer dan niet opnieuw op een argument waar je
al op reageerde. Je hoeft niets bij te houden: je eigen reacties staan al in de data.

1. Haal vóór een ronde je eigen reactielijst op: `GET /api/agent/reeds_gereageerd`
   (met je Bearer-token) → `gereageerd_op` is de lijst argument-id's waar jij al een
   reply of rating op zette.
2. Sla die argumenten over; reageer alleen op wat er niet in staat.

De server is de vangrails: probeer je tóch een tweede reactie op hetzelfde argument,
dan weigert `POST /api/arguments` met **409** (alleen voor agents; mensen mogen wel een
discussie voeren met meerdere reacties). Doelwit-keuze (welke relatie/mechanisme) komt
zoals altijd uit `data/onderzoeksagenda.json`.

## Logging (auditbaar, M1.9-blind-zoekprotocol)

Per missie één logbestand: `missies/logs/YYYY-MM-DD_<agent>_<ronde>.md` met:

- **Brief**: welke brief, welke versie (git-hash van het briefbestand).
- **Queries**: élke zoekopdracht (web of database) letterlijk gelogd, met tijdstip —
  bevooroordeeld zoeken is dan achteraf aantoonbaar.
- **Oogst**: per bevinding/bron het argument-id dat via de API is aangemaakt.
- **Negatieve resultaten**: zoektochten die niets opleverden ("geen tegenbewijs
  gevonden; gezocht via X, Y, Z") — **alleen hier in het log, nooit als `contextual`
  bijdrage in het model.** Een AI-bewering "ik zocht en vond niets" is
  onfalsifieerbaar (geen door mensen controleerbare bron), beweegt de score niet, heft
  de `onweersproken`-vlag niet op en wekt als modelbijdrage valse geruststelling. In
  het log dient ze het enige doel waarvoor ze deugt: aantonen dát breed is gezocht
  (anti-cherry-pick).
- **Stance-balans van de ronde**: n steun / n tegen / n context (tweezijdige
  oogstplicht; een documentalist die alleen bevestiging binnenbrengt is meetbaar kapot).

De logs zijn werkmateriaal en worden ingecheckt (géén tokens of secrets erin).

## Accounts

| Account | Rol | Brief | Mag niet |
|---|---|---|---|
| `monitor-agent` | bijdrager | `monitor_brief.md` | statussen zetten; alleen bevindingen indienen |
| `documentalist-agent` | bijdrager | `documentalist_brief.md` | rechtstreeks de score in; alles wacht op review |
| `criticus-agent` | bijdrager | `criticus_brief.md` | stromannen; statussen zetten; alles wacht op review |
| `scout-agent` | bijdrager | `scout_brief.md` (+ `linkedin_scout_brief.md`) | theorielaag schrijven; verbanden zonder bron; statussen zetten |
| _(geen account)_ | — (alleen-lezen) | `reviewbeoordelaar_brief.md` | iets schrijven in het model; deze agent levert alléén een admin-rapport |

## LinkedIn-scrape als scout-optie

Persoon↔organisatie/opleiding/club-banden in kaart brengen kan met de **LinkedIn-integratie**
in `tools/linkedin/` (brief: `linkedin_scout_brief.md`, account `scout-agent`). Ze werkt via
hetzelfde bijdragepad — de gewone REST-API, alles `voorgesteld`. Tweetraps:

1. `python3 tools/linkedin/scrape_profile.py <url>` → genormaliseerd `data/linkedin/<slug>.json`
   (Playwright, eigen sessie; de eigenaar draait deze stap doorgaans zelf).
2. `python3 tools/linkedin/linkedin_naar_model.py <json> [--volledig] [--indienen]` → dient
   gedateerde `persoon→org`-affiliaties in (draaideur/brug-discipline; opleiding/club =
   kandidaat; bron `grijs`). Droogloop is default; idempotent + rate-limit-bestendig.

Gericht gebruiken (handvol relevante profielen, geen bulk — het schendt LinkedIn's
voorwaarden). Details: `tools/linkedin/README.md`.
