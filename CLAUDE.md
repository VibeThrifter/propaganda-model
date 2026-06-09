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

1. **Theoretical model (abstract, no names)** — `roles` (functions like `mediaeigenaar`, `gatekeeper`) and `mechanisms` (processes like `pakketjournalistiek`, `zelfcensuur`). Each mechanism has a primary `filter` (Eigendom, Advertentie, Sourcing, Flak, Ideologie, `tegenmacht`, `overig`) plus optional extra filters (`mechanism_filters`) and cross-cutting themes (`mechanism_themes`), and an **`aard`** that says how real a dyadic edge is — see "Derived layers" below.
2. **Instance model (concrete, named)** — `entities` (DPG Media, specific people) each linked to roles via `primary_role_id` and the `entity_roles` join; `relations` between entities, each optionally tied to a `mechanism_id`. Every relation carries **two independent scores**: `certainty` ("does this relation exist?") and `influence` ("how strongly does it shape coverage?"). A relation can be certain but low-influence (passive shareholding) or uncertain but high-influence (self-censorship). See `DOCUMENTATIE.md` for the scoring rubric.
3. **Evidence / discussieboom** — `sources` (+ `source_locations` for url/doi/isbn/etc.), `arguments`, and `citations`. `arguments` form a **tree**: `parent_argument_id` NULL = root, otherwise a reply; each argument targets either a `relation_id` or an `entity_id` (at least one required) and has a `stance` of `supporting` / `contradicting` / `contextual`. `citations` attach quotes from sources to arguments. `edit_log` audits argument creation and status changes.

## Derived layers: scores, influence graph & the `aard` visual vocabulary

Two pure-stdlib modules at the repo root turn the raw model into derived numbers; both are shared by `generate_viz.py` and the `/api/scores` endpoint.

- **`scoring.py`** — credibility & strength of theory elements, built bottom-up from the discussieboom (argument evidence → per-relation/-entity practice score → per-role/-mechanism theory score, combined with literature via noisy-OR). See `DOCUMENTATIE.md` § "Scores: van discussieboom naar theorie".
- **`influence.py`** — a directed, weighted influence graph (`source --influence--> target`). Measures structural *position* (direct / transitive / reach / influence-on-public), not intent. `scripts/analyze_influence.py` gives rankings and `--path "A" "B"` traces the strongest (max-product) cascade between two entities — each hop multiplies a weight <1, so a mediated chain comes out small (the "small systemic effect").

**`mechanisms.aard`** (relations inherit it) classifies how real a dyadic edge is, and drives **both** the influence math and how the edge is drawn. Four edge kinds + a separate hyperedge:

| aard | meaning | drawn as (theory model) | influence math |
|---|---|---|---|
| `direct` | local fact; cause *is* the two endpoints | solid line **+ arrowhead**, filter colour | normal edge |
| `indirect` | directed but **mediated** (A→B via intermediary nodes) | dashed line **+ arrowhead**, filter colour, in a background layer **behind** the gold fields | normal edge — the damping sits in the (lower) influence value |
| `veld_instantiatie` | dyad = sample from a field regularity; endpoints substitutable | dashed **fan, no arrowhead**, violet | one damped contribution per source (fan-out / k) |
| `veld_eigenschap` | no real external source; a property *of* the node | **halo** around the node | not an outgoing edge |
| `emergent_effects` (hyperedge; own tables `emergent_effects` + `_members`) | a system property of a *group* of roles | translucent gold **field** around the members + label | n/a (not a 1:1 relation) |

Visual grammar: **arrowhead = directed; solid = immediate, dashed = mediated/diffuse.** The viz toggle **"Indirecte & systemische effecten"** (`state.showFieldEffects`) shows/hides everything that isn't `direct`; off = clean dyadic graph and node size ignores these effects. They are **theory-model only** — in the instance/practice model every relation draws as a normal edge (emergence belongs in the theory layer). When adding a mechanism, set `aard` deliberately (default `direct`). Migrations: `migrate_add_mechanism_aard.py` (the three field levels), `migrate_add_indirect_aard.py` (the `indirect` level), `migrate_add_emergent_effects.py` (the hyperedge). The live DB's `aard` column has **no CHECK** (added via `ALTER TABLE`); the CHECK lives only in `schema.sql`, so widening the enum is a plain `UPDATE` in a migration plus a `schema.sql` edit for fresh builds.

## The web layer

- `server.py` — Flask app serving the discussieboom REST API (`/api/arguments` GET/POST, `/api/arguments/<id>/status` PATCH, `/api/sources`, `/api/citations` POST) plus the visualisation at `/`. Opens a fresh SQLite connection per request with `PRAGMA foreign_keys = ON`. Argument creation is logged to `edit_log`.
- `web/template.html` is the **source** for the visualisation. `web/index.html` (~580 KB) is **generated** by `scripts/generate_viz.py`, which injects the DB data as JSON into the template. **Do not hand-edit `web/index.html`** — edit `template.html` (or the generator) and regenerate.

## Scripts conventions

All scripts resolve paths relative to the repo root via `Path(__file__).parent.parent` and assume `data/propaganda_model.db` exists (except `init_db.py`). Two families:

- `seed_*` — insert fresh data extracted from `sources/AI/*.md`.
- `migrate_*` / `enrich_*` — evolve an existing DB. Migration scripts copy the DB to `data/propaganda_model_backup_<timestamp>.db` before altering it (hence the backup files in `data/`). When changing the schema, follow this backup-then-migrate pattern rather than editing `schema.sql` alone, since real data already lives in the DB.

`sources/` holds raw research material (the `AI/` analyses are the primary extraction input); see `sources/README.md` for the `YYYY-MM-DD_speaker_topic.txt` naming convention.
