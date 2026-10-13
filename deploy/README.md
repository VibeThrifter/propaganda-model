# Deploy — van `flask run` naar een productie-VPS (B1)

De aanbevolen opstelling is **systemd + gunicorn achter Caddy** (geen Docker). De app is
plain Python 3 + SQLite + Flask; de enige extra deploy-dependency is `gunicorn`. Er is
géén build step — `pip install -r requirements.txt` volstaat.

Stappen gemarkeerd met **OWNER-ACTION** vergen jouw host/creds/DNS en kan ik niet voor je
uitvoeren; de overige stappen zijn kant-en-klaar.

## Artefacten in deze map
- `../requirements.txt` — `flask==3.1.3` + `gunicorn==23.0.0`.
- `gunicorn.conf.py` — bind `127.0.0.1:5000`, 2 sync-workers, target `server:app`.
- `propaganda.service` — systemd-unit (auto-herstart na crash én reboot).
- `Caddyfile` — reverse-proxy + automatische Let's Encrypt-HTTPS.

## 1. VPS + gebruiker (OWNER-ACTION)
Een kleine VPS volstaat (de DB is ~9 MB SQLite; de echte kost zit in AI-tokens, niet in
hardware). Maak een non-root service-account, bijv. `propaganda`, en zet de repo op
`/opt/propaganda-model` (of pas de paden in de unit/Caddyfile aan).

```bash
sudo adduser --system --group propaganda
sudo git clone <repo-url> /opt/propaganda-model
sudo chown -R propaganda:propaganda /opt/propaganda-model
```

## 2. Virtualenv + dependencies
```bash
cd /opt/propaganda-model
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 3. Database + data-volume
`data/` bevat de DB, de sessiesleutel (`secret_key`) en de tokens — alles gitignored en
**persistent + gebackupt** houden. Bouw de DB verse of kopieer een bestaande over:

```bash
# Verse build (volgorde telt):
.venv/bin/python scripts/init_db.py
.venv/bin/python scripts/seed_theoretical_model.py
.venv/bin/python scripts/seed_from_ai_source.py
# …of kopieer een bestaande data/propaganda_model.db naar de VPS.
```

De app zet zelf `PRAGMA journal_mode = WAL` + `busy_timeout` op elke connectie, dus
gelijktijdig lezen-tijdens-schrijven (bezoekers + de auto-merge-service) is veilig onder
meerdere workers. De sessiesleutel op schijf (`data/secret_key`) wordt door alle workers
gelezen, zodat inloggen over workers heen én na een herstart blijft werken — geen
code-wijziging nodig, alleen `data/` persistent houden.

Env-overrides (optioneel, defaults = de repo-root):
`PROPAGANDA_DATA_DIR` (verplaatst DB + secret_key + tokens), `PROPAGANDA_DB_PATH`,
`PROPAGANDA_SECRET_KEY_PATH`, `PROPAGANDA_WEB_PATH`, `PROPAGANDA_BIND`,
`PROPAGANDA_WORKERS`.

Rooktest lokaal op de VPS (identiek aan `python3 server.py`):
```bash
.venv/bin/gunicorn -c deploy/gunicorn.conf.py server:app
curl -sI http://127.0.0.1:5000/                 # 200, text/html
curl -s  http://127.0.0.1:5000/api/graph_data | head -c 200   # geldige JSON
```

## 4. systemd-service
Pas in `propaganda.service` de **OWNER-ACTION**-regels aan (User/Group, WorkingDirectory,
venv-pad, PROPAGANDA_DATA_DIR). Dan:

```bash
sudo cp deploy/propaganda.service /etc/systemd/system/propaganda.service
sudo systemctl daemon-reload
sudo systemctl enable --now propaganda
systemctl status propaganda          # groen?
```

De unit herstart automatisch na crash (`Restart=always`) en na reboot
(`WantedBy=multi-user.target`).

### Achtergrond-agents
Deze unit draait alleen de webserver. De agents (de uurronde `automatische-beoordeling`,
`nieuws-scout`, `nieuws-bewijs`, `registers-sync`) plant op de Mac launchd, met
`agent_schedule.py` als enige lijst (`deploy/launchd/README.md`). De oude systemd-timers
en `deploy/crontab` plantten agents die niet meer bestaan en zijn weg (zie
git-geschiedenis vóór 2026-10-13); voor een VPS moet je die vier jobs zelf plannen.

## 5. DNS (OWNER-ACTION)
Zet een A- (en AAAA-)record van je domein naar het VPS-IP **vóór** je Caddy start —
anders faalt de automatische certificaat-uitgifte.

## 6. Caddy — reverse-proxy + HTTPS
Vervang `voorbeeld.tld` in `Caddyfile` door je echte domein (**OWNER-ACTION**), plaats het
en herstart Caddy. Caddy haalt en vernieuwt zelf een Let's Encrypt-cert en redirect
`http://` → `https://`.

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Vervang ook het placeholder-domein `voorbeeld.tld` in de OG/canonical-meta in
`web/template.html` (B2) door je echte domein.

## 7. Verificatie
```bash
curl -sI https://<domein>/                        # 200 + geldig cert, http→https redirect
curl -s  https://<domein>/api/graph_data | head   # geldige JSON
curl -sI https://<domein>/overleg                 # 302 → /login (redactie-gate, B3)
sudo systemctl restart propaganda && sleep 2 && curl -sf https://<domein>/api/health
# Twee gelijktijdige schrijvers → geen 'database is locked' (bewijst WAL + busy_timeout).
```

## 8. Backups (OWNER-ACTION)
Dagelijkse cron die `data/propaganda_model.db` (doe eerst een WAL-checkpoint),
`data/tokens/` en `data/secret_key` naar off-VPS opslag wegschrijft. De DB is klein, dus
triviaal.

```bash
# WAL-checkpoint vóór de kopie:
.venv/bin/python -c "import sqlite3; sqlite3.connect('data/propaganda_model.db').execute('PRAGMA wal_checkpoint(TRUNCATE)')"
```

## Open beslissing (B3): redactie-subdomein
Nu staan de redactie-pagina's (`/overleg`, `/beheer`, `/werkbank`) achter een login-gate
(302 → `/login`). Optioneel later: een intern subdomein `redactie.<domein>` met
IP-allowlist/basic-auth op de proxy (zie het uitgecommentarieerde blok in de `Caddyfile`).
Aanbeveling: gate nu, subdomein optioneel later.

## Docker-alternatief (niet de default)
Wil je liever Docker: bouw een image op `python:3-slim` met
`pip install -r requirements.txt`, `COPY .`, en
`CMD ["gunicorn","-c","deploy/gunicorn.conf.py","server:app"]`, met een volume-mount voor
`data/`. Kies systemd **óf** Docker, niet beide.
