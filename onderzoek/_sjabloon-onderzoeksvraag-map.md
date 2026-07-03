# Sjabloon — een (sub)onderzoeksvraag als map

Kopieer dit naar de `README.md` van een **nieuwe onderzoeksmap** (een streng of een submap). De regel:
**een map = één onderzoeksvraag**, met een eigen README + eigen werkdocumenten + eventueel weer submappen
(recursief, onbeperkt diep). Dit sjabloon is voor de *map-README*; voor een losse notitie ín de map gebruik
je `_sjabloon-onderzoeksnotitie.md` (naast dit sjabloon, in de top van `onderzoek/` — gedeeld door alle strengen).

Vervang alles tussen `<…>` en verwijder de uitleg-regels (`>`-citaten).

---

```markdown
# <Streng N — / Submap —> <Titel van de onderzoeksvraag>

> Eén zin context: welk groter geheel hangt hierboven? Link naar de ouder-README (`../README.md`) en de
> zustervragen.

**Onderzoeksvraag:** <de ene, scherpe vraag die deze map beantwoordt — neutraal: "wat is gedocumenteerd
over X?", nooit "zoek bewijs dat X waar is".>

**Antwoord in het kort:** <2–4 zinnen met de stand van zaken / het voorlopige antwoord, of "nog open".>

## Mappenstructuur
\```
<mapnaam>/
├── README.md                       ← dit bestand
├── 00_<…>.md                       ← <werkdocument>
├── 01_<…>.md
└── <subvraag>/                     ← (optioneel) submap = eigen onderzoeksvraag (eigen README)
\```

## Leeswijzer
1. `00_<…>.md` — <wat hier staat>
2. `01_<…>.md` — <…>

## Hoe je dit uitbreidt (recursief)
- Nieuwe **notitie** → kopieer `onderzoek/_sjabloon-onderzoeksnotitie.md`, oplopend nummer.
- Nieuwe **subonderzoeksvraag** → eigen **submap** met een README volgens dít sjabloon + eigen
  werkdocumenten. Promoveer een notitie tot submap zodra ze een eigen deelvraag + eigen bronnen krijgt.
- **Index bijwerken** in de boom hierboven én in de ouder-README.

## Eerlijkheidsregels (hard — gedeeld met heel `onderzoek/`)
- Quotes verbatim of een ⚠️-vlag; nooit fabriceren/mis-attribueren; onvindbaar = hiaat.
- Onderscheid hard (gemeten/structureel) van aannemelijk (frame/geduid); dateer wat snel verandert.
- Structureel/emergent, geen complot. Vrije-vorm onderzoek, géén modelinhoud (bijdragen via `assistent`,
  alles `voorgesteld`).

## Relatie met de rest van `onderzoek/`
- <link naar ouder-streng + zustervragen + relevante andere strengen>

_Laatst bijgewerkt: <JJJJ-MM-DD>._
```

---

**Wanneer een nieuwe streng (top-niveau) vs. een submap?** Een nieuwe **streng** (`4_…/`) is een vraag van
gelijke orde als "welke elites / wie beïnvloed / welk mechanisme". Bijna alles anders is een **submap**
binnen een bestaande streng (bv. een extra filter onder streng 3, of een deelpubliek onder streng 2).
