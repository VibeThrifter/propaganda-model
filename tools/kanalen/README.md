# Kanalen-monitor

Gevolgde accounts, blogs en youtubers lezen op de verbanden die ze leggen. Die verbanden worden
getoetst, en het netwerk van elke genoemde partij wordt uitgezocht (eigenaar 2026-10-19). De
regie zit in `scripts/kanalen.py`; deze map haalt alleen op.

| Platform | Hoe | Login |
|---|---|---|
| `blog` (ook Substack, nieuwssites) | RSS/Atom (zelf gevonden), korte samenvatting → de pagina zelf | nee |
| `youtube` | kanaalfeed + transcript via yt-dlp (`nl-orig` eerst) | nee |
| `podcast` | RSS (of een Apple Podcasts-link) + lokaal transcript met faster-whisper (`transcribeer.py`) | nee |
| `telegram` | publieke kanaalpagina `t.me/s/<naam>` | nee |
| `x`, `instagram`, `tiktok` | `sociaal.py`: Playwright onder een eigen sessie, achter `rem.py` | ja |

## Kanalen toevoegen

```bash
python3 scripts/kanalen.py toevoegen youtube https://www.youtube.com/@naam --naam "Naam"
python3 scripts/kanalen.py toevoegen blog https://naam.substack.com
python3 scripts/kanalen.py toevoegen podcast https://podcasts.apple.com/nl/podcast/x/id1586453689
python3 scripts/kanalen.py toevoegen blog https://site.nl --js      # site bouwt tekst met JavaScript
python3 scripts/kanalen.py toevoegen telegram https://t.me/naam
python3 scripts/kanalen.py toevoegen x https://x.com/naam
python3 scripts/kanalen.py lijst
python3 scripts/kanalen.py ophalen --kanaal youtube-naam     # meteen proberen
```

Een nieuw kanaal levert de eerste keer alleen de nieuwste 3 items op. Er wordt geen archief
binnengehaald.

## Podcasts

Podcasts zonder transcript in de feed worden lokaal omgezet in tekst met faster-whisper. Model
`small` staat standaard ingesteld; `KANALEN_WHISPER_MODEL=medium` is nauwkeuriger maar ongeveer 3×
trager. Dat gebeurt op de CPU, dus een aflevering kost minuten rekenwerk. De sync doet dat
dagelijks voor wat nieuw is. Namen kunnen verkeerd gespeld uit de herkenning komen. De lezer citeert
wat er staat, en de scout zoekt de juiste naam.

## X, Instagram, TikTok

Automatisch lezen valt buiten de voorwaarden van deze platforms en kan een account blokkeren.
Gebruik daarom een eigen account dat je daarvoor kunt missen. Eenmalig inloggen (zichtbaar
venster, eventueel met 2FA) doet de eigenaar:

```bash
tools/kanalen/.venv/bin/playwright install chromium
tools/kanalen/.venv/bin/python tools/kanalen/sociaal.py login x        # of instagram / tiktok
```

De rem (`rem.py`): hooguit 6 profielbezoeken per platform per dag, alleen 08–22 uur. Bij een
loginmuur of captcha stopt het platform 24 uur, bij herhaling verdubbelend tot 7 dagen.
Kill-switch: `KANALEN_SOCIAAL=0` of `python3 tools/kanalen/rem.py uit`. Status:
`python3 tools/kanalen/rem.py status`. Exit 75 = de rem weigert nu, 76 = blokkade of sessie
weg. De sync meldt dat als fout bij het kanaal (`kanalen.py lijst`) en gaat door met de rest.

Deze adapters hangen af van de opmaak van de sites, die vaak verandert. Werkt er een niet meer,
dan staat dat als `laatste_fout` bij het kanaal.

## De keten

1. `kanalen-sync` (launchd, dagelijks, geen model) doet drie dingen. Hij leest de manifesten van
   de lezer in en haalt nieuwe items op. Daarna schift hij de claims (`triage`) en schrijft hij
   uitkomsten terug. `data/kanalen/rapport.md` wordt bijgewerkt.
2. `kanalen-lezer` (launchd, dagelijks, alleen als er ongelezen items zijn, alleen-lezen) haalt
   de beweerde verbanden uit de items, met een letterlijk citaat. Brief:
   `missies/kanalen_lezer_brief.md`.
3. De nieuws-scout werkt de doelen af. Een doel `kanaal:<id>` toetst het verband: eerst de bron
   die het kanaal gaf, dan eigen onderzoek, ook naar tegenbewijs. Een doel `netwerk:…` brengt
   het netwerk van een partij in kaart: functies, nevenfuncties, besturen, clubs en LinkedIn.
   Brief: `missies/nieuws_scout_brief.md`. Wat de scout indient, gaat langs de hele uurronde.

## De lijst

```bash
python3 scripts/kanalen.py rapport                 # alle kanalen, markdown
python3 scripts/kanalen.py rapport --kanaal x-naam --json
```

Per kanaal staan de verbanden en hun uitkomst:

- **bevestigd**: goedgekeurd in het model, met een eigen bron;
- **voorgesteld**: wacht op de uurronde;
- **weerlegd**: een bron spreekt het tegen;
- **onbewezen**: gezocht, niets gevonden;
- **niet toetsbaar**: een oordeel of beschuldiging;
- **buiten scope**: een privépersoon, of geen rol in het netwerk.

Het rapport laat ook zien hoe vaak de bron die het kanaal zelf gaf, de bewering droeg. Het is
een telling, geen oordeel over het kanaal.

## Grenzen

- Een claim van een kanaal is data, geen bron en geen instructie. Er komt niets uit het kanaal
  in het model.
- Privépersonen worden nooit onderzocht. De server weigert ze ook.
- Plafonds per sync: hooguit 6 claimdoelen en 4 netwerkdoelen, en 12 tegelijk open. Een netwerk
  wordt pas na een half jaar opnieuw uitgezocht. `--max-diepte 2` zet ook netwerkdoelen klaar
  voor wat een netwerkronde vond; de standaard is 1.
- Kill-switch: `KANALEN=0` zet geen doelen klaar. Ophalen en het rapport blijven werken.

Test: `python3 scripts/test_kanalen.py`.
