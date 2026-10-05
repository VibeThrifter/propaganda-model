"""Canonieke definitie van de onbewaakte achtergrond-agents + hun schema.

Eén bron van waarheid, gedeeld door:
  * `deploy/launchd/genereer_launchd.py` (bouwt de macOS LaunchAgent-plists);
  * `server.py` (toont het agents-paneel + de schema-editor op /beheer).

Het **schema** is bewust simpel: een **interval** — elke X minuten, uur of dagen (of
'uit'). Per agent een dict:

    {"eenheid": "minuut", "elke": 30, "aan": true} # elke 30 minuten
    {"eenheid": "uur", "elke": 6, "aan": true}     # elke 6 uur
    {"eenheid": "dag", "elke": 2, "aan": true}     # elke 2 dagen
    {"eenheid": "dag", "elke": 1, "aan": false}    # uit

`interval_seconden()` vertaalt dat naar een launchd `StartInterval` (seconden), of None
bij 'uit'. Overrides leven in `data/agent_schedules.json` (per label); ontbreekt dat
bestand of een key, dan geldt de default hieronder. Stdlib-only.

launchd's `StartInterval` vuurt elke N seconden vanaf het laden (niet klok-gebonden);
slaapt de Mac, dan draait de gemiste job één keer bij het ontwaken. Elke keer dat je
het schema opslaat + toepast wordt de teller opnieuw gezet — bij zeldzame edits geen
punt.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEDULES_PATH = ROOT / "data" / "agent_schedules.json"

# Model + reasoning-effort voor de claude-agents (eigenaarskeuze juli 2026: Opus + high
# voor allemaal). De generator geeft dit door als `--model`/`--effort` aan agent_runner;
# de kale scripts (archiveer/voorspellingen) draaien geen claude en negeren dit.
AGENT_MODEL = "opus"
AGENT_EFFORT = "high"

EENHEDEN = ["minuut", "uur", "dag"]          # + 'uit' via aan=False
SECONDEN = {"minuut": 60, "uur": 3600, "dag": 86400}
MAX_ELKE = {"minuut": 1440, "uur": 168, "dag": 365}   # bovengrens per eenheid (defensief)
MIN_ELKE_MINUUT = 5   # onder de 5 min: een ronde (≈10 min claude) is niet eens klaar

# Canonieke agent-lijst. `label` = de naam in data/agent_runs.jsonl én de config-key.
# `soort`: runner (token-agent) | leesagent (--geen-token) | script (kaal, geen claude).
AGENTS = [
    {"naam": "verificatie", "label": "verificatie-agent", "soort": "runner",
     "spec": ["--agent", "verificatie-agent", "--label", "verificatie-agent",
              "--brief", "missies/verificatie_agent_brief.md"], "timeout": 1800,
     "omschrijving": "A1 herverificatie — quote verbatim tegen de bron + Wayback",
     "default": {"eenheid": "dag", "elke": 1, "aan": True}},
    {"naam": "aanklager", "label": "aanklager-agent", "soort": "runner",
     "spec": ["--agent", "aanklager-agent", "--label", "aanklager-agent",
              "--brief", "missies/aanklager_brief.md"], "timeout": 1800,
     "omschrijving": "A2 tegenspraak — verplichte tegenstander",
     "default": {"eenheid": "dag", "elke": 1, "aan": True}},
    {"naam": "monitor", "label": "monitor-agent", "soort": "runner",
     "spec": ["--agent", "monitor-agent", "--label", "monitor-agent",
              "--brief", "missies/monitor_brief.md"], "timeout": 1800,
     "omschrijving": "Drogreden-/logica-controle",
     "default": {"eenheid": "dag", "elke": 7, "aan": True}},
    {"naam": "documentalist", "label": "documentalist-agent", "soort": "runner",
     "spec": ["--agent", "documentalist-agent", "--label", "documentalist-agent",
              "--brief", "missies/documentalist_brief.md"], "timeout": 2400,
     "omschrijving": "Bron-suggesties voor probleemargumenten",
     "default": {"eenheid": "dag", "elke": 7, "aan": True}},
    {"naam": "scout", "label": "scout-agent", "soort": "runner",
     "spec": ["--agent", "scout-agent", "--label", "scout-agent",
              "--brief", "missies/scout_brief.md"], "timeout": 2400,
     "omschrijving": "Nieuwe entiteiten/relaties uit de onderzoeksagenda",
     "default": {"eenheid": "dag", "elke": 90, "aan": True}},
    {"naam": "criticus", "label": "criticus-agent", "soort": "runner",
     "spec": ["--agent", "criticus-agent", "--label", "criticus-agent",
              "--brief", "missies/criticus_brief.md"], "timeout": 2400,
     "omschrijving": "Red team — valt de zwakste claims aan",
     "default": {"eenheid": "dag", "elke": 90, "aan": True}},
    {"naam": "ideoloog", "label": "ideoloog", "soort": "runner",
     "spec": ["--agent", "assistent", "--label", "ideoloog",
              "--brief", "missies/ideoloog_brief.md"], "timeout": 1800,
     "omschrijving": "Politieke kleurmeter — richting-signalen",
     "default": {"eenheid": "dag", "elke": 30, "aan": True}},
    {"naam": "doelgroep", "label": "doelgroep", "soort": "runner",
     "spec": ["--agent", "assistent", "--label", "doelgroep",
              "--brief", "missies/doelgroep_brief.md"], "timeout": 1800,
     "omschrijving": "Welstandsmeter + bereikmeter",
     "default": {"eenheid": "dag", "elke": 30, "aan": True}},
    {"naam": "reviewbeoordelaar", "label": "reviewbeoordelaar", "soort": "leesagent",
     "spec": ["--geen-token", "--label", "reviewbeoordelaar",
              "--brief", "missies/reviewbeoordelaar_brief.md"], "timeout": 1800,
     "omschrijving": "Review-advies (alleen-lezen, adviesbestand)",
     "default": {"eenheid": "dag", "elke": 1, "aan": True}},
    {"naam": "resolutie", "label": "voorspelling-resolutie", "soort": "leesagent",
     "spec": ["--geen-token", "--label", "voorspelling-resolutie",
              "--brief", "missies/voorspelling_resolutie_brief.md"], "timeout": 1800,
     "omschrijving": "Voorspelling-resolutie-voorstellen (alleen-lezen)",
     "default": {"eenheid": "dag", "elke": 30, "aan": True}},
    {"naam": "archiveer", "label": "archiveer", "soort": "script",
     "spec": ["scripts/archiveer_bronnen.py"], "timeout": 3600,
     "omschrijving": "Wayback-archivering (C3, geen claude)",
     "default": {"eenheid": "dag", "elke": 1, "aan": True}},
    {"naam": "voorspellingen-regen", "label": "voorspellingen-regen", "soort": "script",
     "spec": ["scripts/voorspellingen.py"], "timeout": 600,
     "omschrijving": "Brier-kalibratie herrekenen (geen claude)",
     "default": {"eenheid": "dag", "elke": 7, "aan": True}},
    # Epic 12 "Wie is dit?" (eigenaarsbesluit 2026-09-30): de nieuws-pijplijn.
    # nieuws-scout draait alleen als er open nieuws_doelen zijn (anders exit 0 zonder
    # claude), hooguit 4 rondes per dag en alleen 08–22 uur; één ronde tegelijk (lock).
    {"naam": "nieuws-scout", "label": "nieuws-scout", "soort": "runner",
     "spec": ["--agent", "nieuws-scout", "--label", "nieuws-scout",
              "--brief", "missies/nieuws_scout_brief.md", "--alleen-bij-open-doelen",
              "--max-rondes-per-dag", "4", "--actieve-uren", "8-22"], "timeout": 2400,
     "omschrijving": "Wie is dit? — namen uit het nieuws uitzoeken (wachtrij nieuws_doelen)",
     "default": {"eenheid": "uur", "elke": 2, "aan": True}},
    # Nieuws-aggregator Story 14.13 ("dun bewijs"): bewijs vóór én tegen zoeken voor dun
    # onderbouwde verbanden die lezers in het nieuws zien (wachtrij nieuws_doelen, soort
    # 'relatie'). Alles landt 'voorgesteld'; de autokeur raakt het nooit. Standaard UIT:
    # de nieuws-backend start de rondes zelf binnen haar budget (NIEUWS_BEWIJS_*); zet
    # deze launchd-taak alleen aan als je rondes ook zonder de nieuws-backend wilt.
    {"naam": "nieuws-bewijs", "label": "nieuws-bewijs", "soort": "runner",
     "spec": ["--agent", "nieuws-bewijs", "--label", "nieuws-bewijs",
              "--brief", "missies/nieuws_bewijs_brief.md", "--alleen-bij-open-doelen",
              "--doel-soort", "relatie", "--max-rondes-per-dag", "2",
              "--actieve-uren", "8-22"], "timeout": 2700,
     "omschrijving": "Dun bewijs — bewijs vóór en tegen voor verbanden uit het nieuws",
     "default": {"eenheid": "uur", "elke": 4, "aan": False}},
    {"naam": "nieuws-autokeur", "label": "nieuws-autokeur", "soort": "script",
     "spec": ["scripts/nieuws_autokeur_service.py", "--once"], "timeout": 600,
     "omschrijving": "Automatisch goedkeuren van neutrale structuurfeiten (geen claude)",
     "default": {"eenheid": "minuut", "elke": 30, "aan": True}},
]

AGENT_BY_LABEL = {a["label"]: a for a in AGENTS}


def interval_seconden(schema):
    """Vriendelijk schema → launchd StartInterval (int seconden) of None bij 'uit'."""
    if not schema or not schema.get("aan", True):
        return None
    eenheid = schema.get("eenheid", "dag")
    if eenheid not in SECONDEN:
        return None
    elke = int(schema.get("elke", 1) or 1)
    return max(1, elke) * SECONDEN[eenheid]


def cadans_tekst(schema):
    """Mensleesbare samenvatting, bv. 'elke 6 uur', 'elke 2 dagen' of 'uit'."""
    if not schema or not schema.get("aan", True):
        return "uit"
    eenheid = schema.get("eenheid", "dag")
    if eenheid not in SECONDEN:
        return "uit"
    elke = int(schema.get("elke", 1) or 1)
    if eenheid == "minuut":
        return f"elke {elke} minuut" if elke == 1 else f"elke {elke} minuten"
    if eenheid == "uur":
        return f"elke {elke} uur"
    return f"elke {elke} dag" if elke == 1 else f"elke {elke} dagen"


def _valideer(schema):
    """Normaliseer + begrens een ingediend schema (defensief; UI kan van alles sturen)."""
    if not isinstance(schema, dict):
        return {"eenheid": "dag", "elke": 1, "aan": False}
    eenheid = schema.get("eenheid")
    if eenheid not in EENHEDEN:
        eenheid = "dag"
    try:
        elke = int(schema.get("elke", 1))
    except (TypeError, ValueError):
        elke = 1
    ondergrens = MIN_ELKE_MINUUT if eenheid == "minuut" else 1
    elke = max(ondergrens, min(MAX_ELKE[eenheid], elke))
    aan = bool(schema.get("aan", True))
    return {"eenheid": eenheid, "elke": elke, "aan": aan}


def laad_overrides(path=SCHEDULES_PATH):
    """Lees data/agent_schedules.json (label → schema). Leeg/kapot = {}."""
    try:
        p = Path(path)
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def effectief_schema(label, overrides=None):
    """Default van de agent, overschreven door de config voor dat label."""
    if overrides is None:
        overrides = laad_overrides()
    a = AGENT_BY_LABEL.get(label, {})
    schema = dict(a.get("default", {"eenheid": "dag", "elke": 1, "aan": False}))
    if label in overrides and isinstance(overrides[label], dict):
        schema.update(overrides[label])
    return schema


def alle_effectief(overrides=None):
    """Lijst van alle agents met hun effectieve schema + meta (voor de UI/generator)."""
    if overrides is None:
        overrides = laad_overrides()
    uit = []
    for a in AGENTS:
        schema = effectief_schema(a["label"], overrides)
        uit.append({**a, "schema": schema, "cadans": cadans_tekst(schema)})
    return uit


def schrijf_overrides(nieuwe, path=SCHEDULES_PATH):
    """Valideer + schrijf de per-label overrides. Alleen bekende labels; genormaliseerd."""
    schoon = {}
    for label, schema in (nieuwe or {}).items():
        if label in AGENT_BY_LABEL:
            schoon[label] = _valideer(schema)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(schoon, ensure_ascii=False, indent=2), encoding="utf-8")
    return schoon
