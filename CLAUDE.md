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

**`mechanisms.aard`** (relations inherit it) classifies *how real* a dyadic edge is, and drives **both** the influence math and how the edge is drawn. **Guiding rule: an edge between two nodes is `direct`** — "indirectness" is a property of a *path*, not of a single edge. The live model has only two edge kinds — `direct`, and the `veld_eigenschap` **halo** (a property of the *target* node, drawn as a ring, not counted as outgoing influence; `source_role_id` may be `NULL`) — plus the separate `emergent_effects` **hyperedge** (a translucent gold field over a *group* of roles; own tables `emergent_effects` + `_members`). Two older kinds, `indirect` and `veld_instantiatie`, are **deprecated and empty**; their viz rendering is gone, so a mechanism set to those now just draws as a plain direct edge. The full conceptual definitions, influence math, and worked examples live in `DOCUMENTATIE.md` § "Aard: direct & systemisch" — that is the single source of truth; don't duplicate it here.

**Afgeleide (indirecte) pijlen** are never stored: the viz derives them at node-selection time and shows one only if (1) every hop clears the support gate, (2) every hop has its own discussieboom arguments, and (3) the *composition* is backed by a **padclaim** — an `arguments` row with `role_id` = source role, `property='indirecte_invloed_op'`, `property_value` = target role name (excluded from role scores by `scoring.py`; practice layer matches via the entities' roles). Per-hop support does not imply the composite claim. See `DOCUMENTATIE.md` § "Afgeleide (indirecte) pijlen & padclaims".

**When adding a mechanism, choose `aard` in this order:**
1. Standing *state of one node* with no attributable live sender (causes may exist but are diffuse/overdetermined; the state keeps operating without live input — e.g. self-censorship)? → `veld_eigenschap` (`target_role_id` = that node; `source_role_id` the diffuse origin or `NULL`). Never re-model it as an (incoming) edge: its causes already have their own edges, so that would double-count the same force.
2. Property of a *group* of roles with no single sender — including feedback loops between multiple roles, where every link is both cause and effect? → an `emergent_effects` hyperedge, not a mechanism row.
3. Otherwise a relation between two specific nodes → `direct` — even when the influence is **mediated** (draw the intermediary chain; `influence.py`'s max-product damping makes the net effect small) or **diffuse/uncertain** (encode that in the `certainty` score, not a dashed line).
4. Don't reach for `indirect`/`veld_instantiatie`.

Viz/code notes: the **"Systemische effecten"** panel has separate toggles per layer: gold emergent fields (`state.showFieldEffects`) and halos (`state.showHalos`, also switches node size to the `_veld` variant) are theory-model only (the practice model draws every relation as a normal edge); derived arrows (`state.showDerived`) and direct edges (`state.showDirect`, drawing only — nodes/derived paths/stats keep following the real filters) work in both models. The live DB's `aard` column has **no CHECK** (added via `ALTER TABLE`); the CHECK lives only in `schema.sql` (it still lists all four values — the two deprecated ones retained for migration replay), so changing the enum is a plain `UPDATE` in a migration plus a `schema.sql` edit for fresh builds. Migration trail that collapsed everything to the live set: `migrate_reclassify_indirect_to_direct.py`, `migrate_field_to_direct_dyads.py`, `migrate_reshape_hegemonische_to_frame_export.py`, `migrate_genericize_elite_frames.py`, `migrate_sociologische_homogeniteit_halo.py`, `migrate_frame_export_to_halo.py`, `migrate_tier_herindeling.py` (tier audit: duplicate halos/dyad absorbed by their hyperedges; feedback loop → hyperedge).

## The web layer

- `server.py` — Flask app serving the discussieboom REST API (`/api/arguments` GET/POST, `/api/arguments/<id>/status` PATCH, `/api/sources`, `/api/citations` POST) plus the visualisation at `/`. Opens a fresh SQLite connection per request with `PRAGMA foreign_keys = ON`. Argument creation is logged to `edit_log`.
- `web/template.html` is the **source** for the visualisation. `web/index.html` (~580 KB) is **generated** by `scripts/generate_viz.py`, which injects the DB data as JSON into the template. **Do not hand-edit `web/index.html`** — edit `template.html` (or the generator) and regenerate.

## Scripts conventions

All scripts resolve paths relative to the repo root via `Path(__file__).parent.parent` and assume `data/propaganda_model.db` exists (except `init_db.py`). Two families:

- `seed_*` — insert fresh data extracted from `sources/AI/*.md`.
- `migrate_*` / `enrich_*` — evolve an existing DB. Migration scripts copy the DB to `data/propaganda_model_backup_<timestamp>.db` before altering it (hence the backup files in `data/`). When changing the schema, follow this backup-then-migrate pattern rather than editing `schema.sql` alone, since real data already lives in the DB.

`sources/` holds raw research material (the `AI/` analyses are the primary extraction input); see `sources/README.md` for the `YYYY-MM-DD_speaker_topic.txt` naming convention.
