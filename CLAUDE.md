# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A research database modelling the structural mechanisms that filter and shape Dutch news media, based on Herman & Chomsky's propaganda model (*Manufacturing Consent*, 1988) applied to the Netherlands. The domain — entities, roles, mechanisms, argument text, and all documentation — is in **Dutch**. Match that language when adding seed data, API messages, or docs. `DOCUMENTATIE.md` is the authoritative domain spec (the five filters, scoring rubric, entity/relation types, schema reference).

It is a research/analysis model, not a conspiracy theory: it describes pro-elite bias as an *emergent* property of structural forces. Keep that framing in any generated content.

## Stack & commands

Plain Python 3 + SQLite + Flask. No build step, no test suite, no linter, no `requirements.txt`. Flask is the only third-party dependency (`pip install flask`); everything else is stdlib.

```bash
# Build the database from scratch (order matters — schema, then theory, then instances)
rm -f data/propaganda_model.db
python3 scripts/init_db.py              # create tables from schema.sql
python3 scripts/seed_theoretical_model.py   # roles + mechanisms (layer 1)
python3 scripts/seed_from_ai_source.py      # entities + relations (layer 2)

# Run the web app (discussieboom API + visualisation) at http://localhost:5000
python3 server.py

# Regenerate the static D3 visualisation after data changes
python3 scripts/generate_viz.py
```

Register an academic source: `python3 scripts/register_source.py "Title" <type> "Author" "Publisher" "YYYY-MM-DD"`.

## Architecture: three layers in one SQLite DB

The whole model lives in `data/propaganda_model.db` (gitignored). Understanding the layering is the key to working here:

1. **Theoretical model (abstract, no names)** — `roles` (functions like `mediaeigenaar`, `gatekeeper`) and `mechanisms` (processes like `pakketjournalistiek`, `zelfcensuur`). Each mechanism maps to one of the five filters (Eigendom, Advertentie, Sourcing, Flak, Ideologie) or `overig`.
2. **Instance model (concrete, named)** — `entities` (DPG Media, specific people) each linked to roles via `primary_role_id` and the `entity_roles` join; `relations` between entities, each optionally tied to a `mechanism_id`. Every relation carries **two independent scores**: `certainty` ("does this relation exist?") and `influence` ("how strongly does it shape coverage?"). A relation can be certain but low-influence (passive shareholding) or uncertain but high-influence (self-censorship). See `DOCUMENTATIE.md` for the scoring rubric.
3. **Evidence / discussieboom** — `sources` (+ `source_locations` for url/doi/isbn/etc.), `arguments`, and `citations`. `arguments` form a **tree**: `parent_argument_id` NULL = root, otherwise a reply; each argument targets either a `relation_id` or an `entity_id` (at least one required) and has a `stance` of `supporting` / `contradicting` / `contextual`. `citations` attach quotes from sources to arguments. `edit_log` audits argument creation and status changes.

## The web layer

- `server.py` — Flask app serving the discussieboom REST API (`/api/arguments` GET/POST, `/api/arguments/<id>/status` PATCH, `/api/sources`, `/api/citations` POST) plus the visualisation at `/`. Opens a fresh SQLite connection per request with `PRAGMA foreign_keys = ON`. Argument creation is logged to `edit_log`.
- `web/template.html` is the **source** for the visualisation. `web/index.html` (~580 KB) is **generated** by `scripts/generate_viz.py`, which injects the DB data as JSON into the template. **Do not hand-edit `web/index.html`** — edit `template.html` (or the generator) and regenerate.

## Scripts conventions

All scripts resolve paths relative to the repo root via `Path(__file__).parent.parent` and assume `data/propaganda_model.db` exists (except `init_db.py`). Two families:

- `seed_*` — insert fresh data extracted from `sources/AI/*.md`.
- `migrate_*` / `enrich_*` — evolve an existing DB. Migration scripts copy the DB to `data/propaganda_model_backup_<timestamp>.db` before altering it (hence the backup files in `data/`). When changing the schema, follow this backup-then-migrate pattern rather than editing `schema.sql` alone, since real data already lives in the DB.

`sources/` holds raw research material (the `AI/` analyses are the primary extraction input); see `sources/README.md` for the `YYYY-MM-DD_speaker_topic.txt` naming convention.
