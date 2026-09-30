# Onbewaakte agent-cadans op macOS — launchd (C1)

Het macOS-equivalent van de systemd-timers in `../systemd/`. Maakt van de handmatig
gestarte missie-agents een **zelfdraaiende machine op je Mac**, zonder VPS: elke agent
draait op een vast schema onder zijn eigen token, als een headless `claude -p`-sessie
(de missies *zijn* Claude Code-sessies — zie `missies/README.md`).

Geen nieuwe dependency (projectregel: plain Python 3 + SQLite + Flask). De generator
gebruikt alleen stdlib `plistlib` + `launchctl`.

## Wat het installeert

Eén LaunchAgent-plist per agent in `~/Library/LaunchAgents/`, met dezelfde cadans als
de systemd-set, plus een **KeepAlive-plist voor de Flask-server** (de agents POSTen
ernaar, dus die moet draaien).

| Label | Cadans | Wat |
|---|---|---|
| `nl.propaganda.server` | KeepAlive (altijd aan) | `server.py` op `127.0.0.1:5000` |
| `nl.propaganda.agent-verificatie` | elke 1 dag | A1 herverificatie |
| `nl.propaganda.agent-aanklager` | elke 1 dag | A2 tegenspraak |
| `nl.propaganda.agent-monitor` | elke 7 dagen | drogreden-/logica-controle |
| `nl.propaganda.agent-documentalist` | elke 7 dagen | bron-suggesties |
| `nl.propaganda.agent-scout` | elke 90 dagen | nieuwe entiteiten/relaties |
| `nl.propaganda.agent-criticus` | elke 90 dagen | red team |
| `nl.propaganda.agent-ideoloog` | elke 30 dagen | politieke kleurmeter |
| `nl.propaganda.agent-doelgroep` | elke 30 dagen | welstand + bereik |
| `nl.propaganda.agent-reviewbeoordelaar` | elke 1 dag | review-advies (alleen-lezen) |
| `nl.propaganda.agent-resolutie` | elke 30 dagen | voorspelling-resolutie (alleen-lezen) |
| `nl.propaganda.agent-archiveer` | elke 1 dag | Wayback-archivering (C3) |
| `nl.propaganda.agent-voorspellingen-regen` | elke 7 dagen | Brier-kalibratie |

Het schema is een **interval** (launchd `StartInterval`): elke X minuten/uur/dagen. Dit
zijn de defaults — bewerk ze per agent op `/beheer` (zie hieronder). launchd vuurt elke
N seconden vanaf het laden; slaapt de Mac, dan draait de gemiste job één keer bij het
ontwaken.

**caffeinate (belangrijk).** De claude-agents draaien onder `caffeinate -i` zodat de Mac
**niet in slaap valt tijdens een ronde** — anders breekt een ~10-min sessie halverwege af
(`API Error: Connection closed mid-response` → exit 1). claude's eigen caffeinate stopt na
5 min; onze wrapper houdt de assertion de héle ronde vast. Dit lost **idle-sleep** op; een
**dichtgeklapt deksel** slaapt alsnog (clamshell) — dat blijft VPS-terrein.

Let op: LaunchAgents draaien in het **GUI-domein** en vuren alleen als je bent
**ingelogd** (niet op het inlogscherm). Voor een altijd-aan machine is dat het juiste
model voor een persoonlijke Mac; wil je echt 24/7 zonder ingelogde sessie, dan hoort
het op de VPS (`../systemd/`).

## Installeren

```bash
# 1. Bekijk droog wat er komt (schrijft niets):
python3 deploy/launchd/genereer_launchd.py --lijst

# 2. Schrijf de plists (nog niet laden):
python3 deploy/launchd/genereer_launchd.py

# 3. Schrijf + laad ineens (launchctl bootstrap):
python3 deploy/launchd/genereer_launchd.py --laden

# Al een server met de hand aan? Sla de KeepAlive-server over:
python3 deploy/launchd/genereer_launchd.py --laden --geen-server
```

## Schema's aanpassen vanuit de app

De cadans is **bewerkbaar op `/beheer`** (maintainer) — sectie *Agent-schema's*: per
agent een frequentie (elk uur … per kwartaal, of *uit*) + tijd, met een live preview.
"Opslaan & toepassen" schrijft `data/agent_schedules.json` en herlaadt de launchd-jobs
meteen (`--geen-server --laden`, zodat de draaiende server zichzelf niet herstart).

De canonieke agent-lijst + default-schema's wonen in `agent_schedule.py` (gedeeld door
deze generator én de server). Endpoints: `GET/PATCH /api/agents/schedules` +
`POST /api/agents/herlaad` (alle maintainer-only). Een agent op *uit* wordt ge-bootout
en z'n plist verwijderd. `data/agent_schedules.json` is machine-lokaal (gitignored);
ontbreekt 'ie, dan gelden de defaults.

## Aan / uit / status

```bash
# Status van alle jobs:
launchctl list | grep nl.propaganda

# Eén agent NU draaien (test, wacht niet op de klok):
launchctl kickstart -k gui/$(id -u)/nl.propaganda.agent-monitor

# Eén agent tijdelijk uit / weer aan:
launchctl bootout   gui/$(id -u)/nl.propaganda.agent-scout
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/nl.propaganda.agent-scout.plist

# Alles verwijderen (uitladen + plists weg):
python3 deploy/launchd/genereer_launchd.py --verwijderen
```

De **auto-merge** is een aparte schakelaar (niet in deze set): de env-noodrem
`PROPAGANDA_AUTO_MERGE=0` op de server-plist, en de C2-loop
(`scripts/auto_merge_service.py`) draai je apart. Zet die pas aan met een
eigenaars-sign-off — draai eerst een tijd met de agents en beoordeel de wachtrij met
de hand op `/overleg`.

## Waarom `--skip-permissions`

Een onbewaakte `claude -p`-sessie zou blokkeren op tool-permissieprompts
(WebFetch/Bash/Write) — precies wat je bij een handmatige run ziet. De generator geeft
daarom `--dangerously-skip-permissions` mee aan `agent_runner.py`. Dat is verantwoord
op een **vertrouwde eigen machine**: de blast radius blijft begrensd door (1) de
missie-brief en (2) de API-poorten — alles wat een agent indient landt `voorgesteld`,
het agent-token kan niets mergen/verwijderen/classificeren. Draai het niet op een
gedeelde of onvertrouwde machine.

## Logs & toezicht

- launchd's eigen stdout/stderr per job: `data/launchd/<naam>.{out,err}.log` (gitignored).
- Het inhoudelijke ronde-log schrijft `agent_runner.py` zelf naar `missies/logs/`.
- Per-ronde run-record: `data/agent_runs.jsonl`.
- Afwijkingssignaal na een cyclus: `python3 scripts/monitor_agents.py` (read-only).
- Meta-toezicht: `/beheer` (toezicht-paneel, C4) + `/api/toezicht`.

## Randvoorwaarden

- `claude` (Claude Code CLI) op het PATH — de plists zetten
  `/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin` en geven `--claude-bin` expliciet mee.
- Ingelogd bij `claude` (dezelfde auth als je interactieve sessie; `~/.claude`).
- Agent-tokens in `data/tokens/<account>.token` (gitignored; via `scripts/create_user.py`).
  De alleen-lezen agents (`reviewbeoordelaar`, `voorspelling-resolutie`) draaien `--geen-token`.
- Flask geïnstalleerd voor de gebruikte Python (`sys.executable`); de server draait al
  onder diezelfde interpreter.

**LinkedIn staat bewust NIET op een timer** (beleid J4): de scrape-trap blijft
eigenaar-getriggerd/gericht (headful, eigen sessie, interactieve login = mensenwerk).
