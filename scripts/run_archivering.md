# Wayback-archivering op schema (C3)

`scripts/archiveer_bronnen.py` geeft elke URL-bron een onveranderlijke Wayback-kopie
(`archive_url`-locatie in `source_locations`). Dat is een prerequisite voor A1
(bron-herverificatie tegen een stabiele kopie) en voor de "linkrot-vrij"-claim van
het portal (B4/E1). Dit bestand beschrijft de **gebatchte cadans**; de timer zelf
(systemd/cron) hoort bij de deploy-/C1-lane.

## Waarom batchen

- Save Page Now (SPN) is traag en rate-gelimiteerd: het script pauzeert
  `SAVE_PAUZE_S = 8`s per aanvraag. Met ~2.000 onarchiveerde bronnen is een volledige
  `--save`-pass ≈ 2.000 × 8s ≈ **4,5 uur** — te lang voor één interactieve run.
- Ook de CDX-lookup-API (bestaande snapshots opzoeken) is rate-gelimiteerd: te snel
  achter elkaar bevragen levert **HTTP 429**. Het script paced daarom elke CDX-call
  (`CDX_PAUZE_S = 2`s) en backt af op een 429 (`CDX_BACKOFF_S`, exponentieel).

## Twee fasen (bewust ontkoppeld)

1. **Goedkope CDX-pass, zónder `--save`** — registreert alleen *reeds bestaande*
   snapshots. Geen SPN-quota verspild aan bronnen die al gearchiveerd zijn.

   ```bash
   python3 scripts/archiveer_bronnen.py            # hele achterstand langslopen (CDX-only)
   ```

2. **Gebatchte `--save`-runs** — vraagt verse snapshots aan voor wat na fase 1 nog
   open staat. Eén `--limit N` per run, meerdere runs over de dagen. Idempotent:
   bronnen met een `archive_url` worden overgeslagen, dus een herdraai archiveert
   nooit dubbel.

   ```bash
   python3 scripts/archiveer_bronnen.py --save --limit 10   # één dag-batch
   ```

## Handige losse commando's

```bash
python3 scripts/archiveer_bronnen.py --tel              # alleen het percentage (geen netwerk)
python3 scripts/archiveer_bronnen.py --dry-run --limit 5  # preview, schrijft niets
```

## Cadans op de scheduler (deploy-/C1-lane)

Een dagelijkse timer draait één gebatchte `--save`-run; de achterstand slinkt
geleidelijk zonder de rate-limit uit te hongeren. Richtgetal: `--limit 200` per dag
werkt ~2.000 bronnen in ~10 dagen weg (200 × 8s ≈ 27 min/run). Voorbeeld (systemd,
hoort in `deploy/`, hier alleen ter illustratie):

```ini
# archiveer.service  (ExecStart)
/usr/bin/python3 /opt/propaganda-model/scripts/archiveer_bronnen.py --save --limit 200
# archiveer.timer    (OnCalendar=daily)
```

## Voortgang & audit

- **Stand:** `python3 scripts/archiveer_bronnen.py --tel` toont
  `gearchiveerd/totaal (pct%)`. Elke echte run print een `Voor:`/`Na:`-regel.
- **Batch-log:** elke schrijvende run appendt één JSON-regel aan
  `data/archiveer_log.jsonl` (datum, modus, behandelde source-ids, gevonden/
  aangevraagd/open, pct vóór/na). Dat is de dag-batch-audit voor C4-toezicht.
  (`data/` is gitignored; de log is een lokaal/host-artefact.)

## Dogfood-regel

Archivering schrijft `archive_url`-**bron-metadata**, geen inhoud — net als
`scripts/register_source.py` valt dit buiten de dogfood-regel (M0.6). Het is een
OS-/schema-taak, niet het agent-bijdragepad; geen Bearer-token, geen `voorgesteld`.
