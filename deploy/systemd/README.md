# Onbewaakte agent-cadans — systemd-timers (C1)

OS-native timers maken van de handmatig gestarte missie-agents een **zelfdraaiende
machine**: elke agent draait op een vast schema onder zijn eigen token, zonder dat de
eigenaar elke ronde met de hand start. Geen nieuwe dependency (de projectregel: plain
Python 3 + SQLite + Flask); de timer roept enkel de dunne stdlib-wrapper
`scripts/agent_runner.py` aan, die één headless `claude -p`-sessie start, naar
`missies/logs/` tee't en een run-record wegschrijft.

Dit sluit aan op B1 (`gunicorn` + `systemd`-unit, zie `../propaganda.service`). Een
frictieloze terugval zonder systemd staat in `../crontab`.

## Installeren (OWNER-ACTION)

De units gaan uit van `WorkingDirectory=/opt/propaganda-model`, een service-account
`propaganda` en een venv op `/opt/propaganda-model/.venv`. Pas dat aan naar je host
(dezelfde velden als `../propaganda.service`), plus:

- Zorg dat `claude` (de Claude Code CLI) op het `PATH` van het service-account staat,
  of geef `--claude-bin /pad/naar/claude` mee in de `ExecStart`.
- Leg de agent-tokens klaar in `data/tokens/<account>.token` (gitignored; via
  `scripts/create_user.py`). De alleen-lezen agents (`reviewbeoordelaar`,
  `voorspelling-resolutie`) draaien `--geen-token`.

```bash
sudo cp deploy/systemd/agent-*.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
# Zet de timers aan die je wilt draaien, bv.:
sudo systemctl enable --now agent-monitor.timer agent-verificatie.timer agent-aanklager.timer
sudo systemctl list-timers 'agent-*'          # controleer de volgende looptijden
```

## Cadans (uit de briefs)

| Timer | Account | Brief | Cadans (`OnCalendar`) |
|---|---|---|---|
| `agent-verificatie` | `verificatie-agent` | `verificatie_agent_brief.md` | dagelijks 02:00 |
| `agent-aanklager` | `aanklager-agent` | `aanklager_brief.md` | dagelijks 02:30 |
| `agent-monitor` | `monitor-agent` | `monitor_brief.md` | wekelijks (ma 03:00) |
| `agent-documentalist` | `documentalist-agent` | `documentalist_brief.md` | wekelijks (wo 03:30) |
| `agent-scout` | `scout-agent` | `scout_brief.md` | per kwartaal (1 jan/apr/jul/okt 04:00) |
| `agent-criticus` | `criticus-agent` | `criticus_brief.md` | per kwartaal (8 jan/apr/jul/okt 04:00) |
| `agent-ideoloog` | `assistent` | `ideoloog_brief.md` | maandelijks (5e 05:00) |
| `agent-doelgroep` | `assistent` | `doelgroep_brief.md` (welstand + bereik) | maandelijks (6e 05:00) |
| `agent-reviewbeoordelaar` | — (alleen-lezen) | `reviewbeoordelaar_brief.md` | dagelijks 06:00, meebewegend met de wachtrij |
| `agent-resolutie` | — (alleen-lezen) | `voorspelling_resolutie_brief.md` | maandelijks (2e 05:30) |
| `agent-archiveer` | — (kaal script) | `scripts/archiveer_bronnen.py` | dagelijks 01:00 |
| `agent-voorspellingen-regen` | — (kaal script) | `scripts/voorspellingen.py` | wekelijks (ma 06:30) |

**LinkedIn staat bewust NIET op een timer** (beleid J4). De scrape-trap
(`tools/linkedin/scrape_profile.py`) blijft eigenaar-getriggerd/gericht — headful,
eigen sessie, geen 24/7-schema; de interactieve login is mensenwerk. De scout-agent
draait de LinkedIn-mapper alleen op verzoek, zolang `tools/linkedin/session.json` leeft.

## Stuck-detectie & toezicht (koppelt aan C4)

- Elke `.service` heeft een harde `TimeoutStartSec=` (1800–3600 s): een ronde die
  vastloopt wordt met SIGKILL gedood en de unit faalt zichtbaar
  (`systemctl status agent-<naam>`, `journalctl -u agent-<naam>`).
- `agent_runner.py` schrijft per ronde exit-code + duur + oogst (edit_log-delta van het
  account) naar de log-footer én naar `data/agent_runs.jsonl`.
- De ingebouwde flood-rem blijft de per-account rate-limit (bijdrager 30/min → 429);
  alleen `maintainer` en `assistent` zijn vrij, dus een op-hol-geslagen
  `scout-agent`/`monitor-agent`-lus botst vanzelf op 429.
- Draai na een cyclus `python3 scripts/monitor_agents.py` (read-only): het toont de
  per-ronde-delta per agent + een afwijkingssignaal (0 inzendingen = mogelijk
  vastgelopen/lege ronde; boven de drempel = mogelijk op-hol).

## Droogloop

Test een unit zonder iets te posten:

```bash
python3 scripts/agent_runner.py --agent monitor-agent --brief missies/monitor_brief.md --dry-run
```
