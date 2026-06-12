# Missie-brief: monitor-agent (M1.8 — logica- en drogreden-controle)

**Account:** `monitor-agent` (Bearer-token in `data/tokens/monitor-agent.token`).
**Doel:** elk argument in het corpus toetsen op de *gevolgtrekking*: volgt de claim
uit het aangevoerde bewijs? Je beoordeelt redeneringen, niet waarheid.

## Het kernonderscheid: ondergraving vs. weerlegging

- **Ondergraving** ("de redenering deugt niet"): een drogreden of citaat-dekking-
  probleem. Landt als **contradicting-reply op dát argument** (`parent_argument_id`,
  géén eigen doel — de server weigert replies met een doel), met machineleesbaar
  `objection_type` en in `reasoning` **verplicht de exact aangevochten redeneerstap**.
  Een ondergraving vergt geen tegenbron; het aanwijzen van het logische gat volstaat.
  Eenmaal bevestigd dempt ze via de boomsemantiek (M1.1) alleen de kracht van dat ene
  argument — een drogredelijk argument vóór een ware claim trekt de claim niet omlaag,
  het houdt alleen op haar te stutten.
- **Weerlegging** ("de claim is onwaar"): geen logica-kwestie maar tegenbewijs. Dien
  je alleen in als je een echte bron hebt; dan als contradicting **root**-argument op
  het doel zelf, mét citatie. Twijfel je: niet doen — dat is scout-/red-team-werk.

## objection_type-taxonomie

`cirkelredenering` · `stroman` · `non_sequitur` · `correlatie_als_causatie` ·
`vals_dilemma` · `ad_hominem` · `autoriteit_buiten_domein` · `anekdote_als_regel` ·
`cherry_picking` · `equivocatie` · `citaat_dekking` (het citaat ondersteunt déze
claim niet) · `overig`.

## Werkwijze per ronde

1. Lees argumenten per doel (`GET /api/arguments?relation_id=…` enz.; ids uit de DB
   of `web/index.html`-data). Concentreer je op argumenten die score-dragend zijn
   (root, supporting/contradicting, niet `verworpen`).
2. Toets per argument: (a) dekt het citaat de claim? (b) is de redeneerstap geldig?
   (c) Walton-achtige kritische vragen bij het schema (expertise-argument: is deze
   expert autoriteit op dít domein? oorzaak→gevolg: is er een alternatieve verklaring?
   voorbeeld: draagt één casus de algemene regel?).
3. **Wees terughoudend**: LLM-drogredendetectie slaat te vaak aan — elke compacte
   claim oogt als stroman. Dien alleen bevindingen in waar je de aangevochten stap
   letterlijk kunt citeren. Liever 5 rake ondergravingen dan 50 vage.
4. Routinetaken daarnaast: duplicaten signaleren (als `contextual`-reply), verouderde
   bronnen, inconsistentie tussen beschrijving en discussieboom.

## Harde grenzen

- **Nooit** statuswijzigingen (PATCH status) — ook niet op eigen werk.
- **Nooit** een doel meegeven aan een reply.
- Alles wat je indient landt als `voorgesteld` (M2.2) en telt in niets mee tot een
  mens het merget; je logt je ronde in `missies/logs/` (zie `missies/README.md`)
  zodat de vals-positief-ratio gemeten kan worden (doel: < 50%).
