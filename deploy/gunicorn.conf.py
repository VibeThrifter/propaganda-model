"""Gunicorn-config voor de productie-deploy (B1).

Start:  gunicorn -c deploy/gunicorn.conf.py server:app

De WSGI-callable is `app` in server.py (doel `server:app`). Draai dit achter een
reverse-proxy die TLS termineert (zie deploy/Caddyfile) — gunicorn bindt bewust
alleen op localhost.
"""
import os

# Alleen localhost: de reverse-proxy (Caddy/nginx) praat met deze poort en doet TLS.
bind = os.environ.get("PROPAGANDA_BIND", "127.0.0.1:5000")

# Start klein: de DB-schrijf is agent-gedreven en laag-volume. Let op (bekend gedrag,
# geen bug): _graph_cache en _rate_emmers in server.py leven per worker-proces —
# met N workers wordt de graafdata tot N× herberekend (onschadelijk, mtime-gesleuteld)
# en is de rate-limit effectief N× per account (acceptabel; maintainer + 'assistent'
# zijn tóch vrijgesteld). Wil je later >2 workers of een tweede appserver, dan is een
# gedeelde cache/limiter nodig — nu bewust NIET (zware dependency).
workers = int(os.environ.get("PROPAGANDA_WORKERS", "2"))
worker_class = "sync"
timeout = 60

# Graceful herstart en nette logging.
graceful_timeout = 30
accesslog = os.environ.get("PROPAGANDA_ACCESSLOG", "-")   # '-' = stdout (journald vangt het)
errorlog = os.environ.get("PROPAGANDA_ERRORLOG", "-")
loglevel = os.environ.get("PROPAGANDA_LOGLEVEL", "info")
