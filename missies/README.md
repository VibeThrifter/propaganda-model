# Agent-missies (verbeterplan §6.2, M1.8/M1.9)

Alle agent-rollen draaien als Claude Code (background) sessies — geen aparte integratie.
Ze gebruiken exact dezelfde REST-API als menselijke gebruikers en authenticeren met het
Bearer-token van hun agent-account (`data/tokens/<naam>.token`, aangemaakt via
`scripts/create_user.py`). De ene regel die overal geldt: **een agent telt als
gebruiker, maar verdient zijn gewicht** — provenance verplicht, elke claim herleidbaar
naar een door mensen controleerbare bron, nooit directe statuswijzigingen.

## Een missie starten

1. Open een Claude Code sessie (of background agent) in deze repo.
2. Geef als opdracht: *"Voer de missie uit in `missies/monitor_brief.md`
   (of `scout_brief.md`), als agent-account `monitor-agent`/`scout-agent`."*
3. De agent logt zijn ronde in `missies/logs/` (zie hieronder) en dient alle
   bevindingen in via de API; een mens reviewt daarna.

## Logging (auditbaar, M1.9-blind-zoekprotocol)

Per missie één logbestand: `missies/logs/YYYY-MM-DD_<agent>_<ronde>.md` met:

- **Brief**: welke brief, welke versie (git-hash van het briefbestand).
- **Queries**: élke zoekopdracht (web of database) letterlijk gelogd, met tijdstip —
  bevooroordeeld zoeken is dan achteraf aantoonbaar.
- **Oogst**: per bevinding/bron het argument-id dat via de API is aangemaakt.
- **Negatieve resultaten**: zoektochten die niets opleverden ("geen tegenbewijs
  gevonden; gezocht via X, Y, Z") — dit register is zelf een `contextual`-bijdrage
  en telt mee in de bewijsdekking.
- **Stance-balans van de ronde**: n steun / n tegen / n context (tweezijdige
  oogstplicht; een scout die alleen bevestiging binnenbrengt is meetbaar kapot).

De logs zijn werkmateriaal en worden ingecheckt (géén tokens of secrets erin).

## Accounts

| Account | Rol | Brief | Mag niet |
|---|---|---|---|
| `monitor-agent` | bijdrager | `monitor_brief.md` | statussen zetten; alleen bevindingen indienen |
| `scout-agent` | bijdrager | `scout_brief.md` | rechtstreeks de score in; alles wacht op review |
