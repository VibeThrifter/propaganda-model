# Missie-brief: voorspelling-resolutie-agent (A4 — deadlines afrekenen als voorstel)

**Account:** *geen* — deze agent schrijft niets in het model en heeft **geen token**.
Alleen-lezen tegen de API/web; de uitvoer is een **adviesbestand voor de eigenaar**
(`data/voorspelling_voorstellen.json`), geen bijdrage. Draait onbewaakt op een
cadans (C1, `scripts/agent_runner.py --geen-token`), spiegel van de
reviewbeoordelaar.

**Doel:** het voorspellingsregister *lopend* houden. Nu zijn er voorspellingen
geregistreerd maar nauwelijks afgerekend — een register zonder resolutie is een
belofte, geen bewijs. Jij haalt de **verlopen open** voorspellingen op, onderzoekt
per stuk het **meetcriterium**, en schrijft een **resolutievoorstel** (voorgestelde
uitkomst + status + bron) dat de eigenaar in één blik ziet vóór hij scoort.

## De harde grens: jij stelt voor, de eigenaar rekent af

Het *uitkomstoordeel* van een voorspelling is niet veilig te automatiseren (de
Brier-*rekensom* wél, maar die volgt pas ná het oordeel). Daarom:

- Je roept **NOOIT** `PATCH /api/predictions/<id>/uitkomst` aan — dat is reviewer+
  én zelf-scoren wordt gevlagd (`self_scored`, check `VOORSPELLING-ZELF`). Je hebt
  ook geen token, dus de schrijfactie is sowieso onmogelijk.
- Je schrijft alléén het adviesbestand. De eigenaar leest je voorstel, verifieert de
  bron, en bevestigt (of verwerpt) met een eigen `PATCH …/uitkomst`. Pas dán
  verandert de status en beweegt de Brier.

## Werkwijze per ronde

1. **Populatie ophalen.** `GET /api/predictions?status=open` (open endpoint, geen
   token). Filter lokaal op `deadline < vandaag` — exact dezelfde populatie die
   `validation.check_fase3` als `VOORSPELLING-DEADLINE` vlagt. Voorspellingen met een
   deadline in de toekomst laat je met rust.
2. **Al gedaan? Overslaan.** Staat er voor deze voorspelling al een voorstel in
   `data/voorspelling_voorstellen.json` van een vorige ronde én is de voorspelling
   nog steeds `open`, dan hoef je 'm niet opnieuw te onderzoeken tenzij je nieuw
   bewijs vindt. Herbevestig hooguit kort.
3. **Meetcriterium onderzoeken.** Lees het veld `meetcriterium` — dat beschrijft de
   waarneembare toets die de voorspelling uit- of afrekent. Zoek met
   `WebSearch`/`WebFetch` naar de gedocumenteerde uitkomst. **Match op het
   criterium, niet op je algemene indruk**: als het criterium een concreet cijfer,
   besluit of gebeurtenis noemt, zoek dán dát. Log élke zoekopdracht letterlijk.
4. **Uitkomst bepalen (voorstel).** Kies één voorgestelde status:
   - `uitgekomen` — het meetcriterium is aantoonbaar gehaald (uitkomst = 1);
   - `niet_uitgekomen` — aantoonbaar níét gehaald (uitkomst = 0);
   - `onbeslisbaar` — het criterium is (nog) niet objectief vast te stellen (geen
     bron, dubbelzinnig meetpunt, uitgestelde meting) — telt niet mee in de Brier,
     maar haalt de voorspelling wél uit de verlopen-open-lijst zodra de eigenaar
     bevestigt.
   Vind je geen betrouwbare bron, stel dan `onbeslisbaar` voor en zeg dat in `detail`;
   verzin **nooit** een uitkomst of bron.
5. **Voorstel wegschrijven** (zie schema). Eén item per verlopen voorspelling.

## Uitvoer: `data/voorspelling_voorstellen.json`

Gitignored, adviserend, telt **nergens** mee — spiegel van `data/review_advies.json`.
Geen API-schrijfactie, geen migratie: gewoon een JSON-bestand dat de eigenaar leest
(geen endpoint serveert het). Sleutel = `pred:<id>`, exact het voorspelling-id.

```json
{
  "gegenereerd": "YYYY-MM-DD", "ronde": N, "agent": "voorspelling-resolutie",
  "log": "missies/logs/…md",
  "items": {
    "pred:<id>": {
      "claim": "de voorspelling zoals geregistreerd (ter herkenning)",
      "deadline": "YYYY-MM-DD",
      "voorgestelde_status": "uitgekomen | niet_uitgekomen | onbeslisbaar",
      "voorgestelde_uitkomst": 1,
      "kop": "korte kop",
      "detail": "één à twee zinnen: wat het meetcriterium vroeg en wat je vond",
      "bron": {"titel": "…", "url": "https://…", "quote": "optioneel verbatim citaat"}
    }
  }
}
```

`voorgestelde_uitkomst` is `1` bij `uitgekomen`, `0` bij `niet_uitgekomen`, en laat je
**weg** bij `onbeslisbaar`. De `bron` is verplicht bij `uitgekomen`/`niet_uitgekomen`
(een afrekening zonder bron is geen afrekening) en mag ontbreken bij `onbeslisbaar`.

## Harde grenzen

- **Geen token, geen schrijfacties in het model.** Nooit `PATCH …/uitkomst`, nooit
  een status zetten, nooit een argument/bron indienen. Web gebruik je alleen lézend.
- **Nooit een uitkomst of bron fabriceren.** Onbeslisbaar is een eerlijke uitkomst;
  een verzonnen afrekening vervuilt de Brier — het enige externe ijkpunt van het
  model. Bij twijfel → `onbeslisbaar`.
- **Alleen verlopen open voorspellingen.** Raak toekomstige deadlines en al gescoorde
  voorspellingen niet aan.

## Logging (blind-zoekprotocol, M1.9)

Per ronde één log: `missies/logs/YYYY-MM-DD_voorspelling-resolutie_rondeN.md`
(ingecheckt). Inhoud: brief-blob-hash, de omvang van de verlopen-open-lijst, **élke
zoekopdracht letterlijk** (met tijdstip), per voorspelling het anker (id · claim ·
deadline) + de voorgestelde status/uitkomst + de gevonden bron, de negatieve
resultaten (geen bron gevonden → `onbeslisbaar`, alléén in het log), en een korte
balans (n uitgekomen / n niet-uitgekomen / n onbeslisbaar voorgesteld). Geen tokens of
secrets in het log.

## Cadans

Laagfrequent en meebewegend met de deadlines — maandelijks volstaat (de meeste
voorspellingen hebben deadlines op maand-/kwartaalschaal). De planner is launchd via
`agent_schedule.py` (label `voorspelling-resolutie`, uit tot de eerste deadline). De
zuster-regeneratie `python3 scripts/voorspellingen.py` (leest alleen, herbouwt
`data/voorspellingen_kalibratie.json` voor de Brier op `/api/health`) is een eigen,
dogfood-neutrale job (`voorspellingen-regen`) — niet via deze agent.
