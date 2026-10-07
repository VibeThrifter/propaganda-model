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
| `nl.propaganda.agent-automatische-beoordeling` | elk uur | de ronde die alles beslist (bronzoeker, bronchecker, smaadtoets, aanklager, immuunpoort, verificatie, mechanismen, RfC's, bronklassen, goedkeuren, opruimen, archiveren) |
| `nl.propaganda.agent-nieuws-scout` | elke 2 uur (max 6/dag, 08–22) | namen uit het nieuws uitzoeken |
| `nl.propaganda.agent-nieuws-bewijs` | elke 2 uur (max 3/dag, 08–22) | bewijs voor dun onderbouwde verbanden uit het nieuws |

Opgeschoond 2026-10-07: de losse verificatie-agent, de dagelijkse aanklager, documentalist,
reviewbeoordelaar, archiveer en nieuws-autokeur zijn vervangen door stappen van de
automatische beoordeling; monitor, scout, criticus, ideoloog, doelgroep en de voorspellingen
staan uit (aan te zetten op `/beheer`). `agent_schedule.py` is de enige lijst.

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

Het **mergen** gebeurt in de automatische beoordeling (stap 5, account `merge-service`);
de env-noodrem `PROPAGANDA_AUTO_MERGE=0` op de server-plist zet het uit.

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
