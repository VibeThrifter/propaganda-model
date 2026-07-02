# Webapp-stories — simpel, strak, stijlvol, overzichtelijk

**Status:** spoor 1 (huisstijl-fundament) afgerond op 1 juli 2026 · spoor 2 (visualisatie: eenvoud door gelaagdheid) afgerond op 2 juli 2026 · spoor 3 (overleg als uitnodigende werkplek) afgerond op 2 juli 2026 · spoor 4 (mobiel bruikbaar) + follow-up W3.2b afgerond op 2 juli 2026 · spoor 5 (lichter & levend, W5.1) afgerond op 2 juli 2026 — **alle sporen af**; rest = de doorlopende poets-backlog onderaan.
**Herkomst:** UX-audit 1 juli 2026 — code-doorlichting van alle zeven pagina's plus screenshots op desktop- en telefoonformaat. Kerncijfers uit die audit staan bij de stories, zodat elke story meetbaar is.

---

## Kwaliteitslat & werkwijze (geldt voor élke story)

De lat, in de woorden van de eigenaar: **simpel maar goed werken; simpel, strak, stijlvol en overzichtelijk ogen; aantrekkelijk om mee te werken.**

Definition of done voor iedere story:

1. **Visueel getoetst** met headless-Chrome-screenshots: desktop 1680×1050 én mobiel 390×844 (server draait op `:5000`; commando staat in het Claude-geheugen en is triviaal: `--headless --screenshot=… --window-size=…`).
2. **Geen console-errors; niets kwijt.** Bestaande functionaliteit blijft bereikbaar, tenzij de story expliciet zegt dat iets vervalt.
3. **Gedeeld = huisstijl.** Stijl of gedrag dat twee of meer pagina's raakt hoort in `web/huisstijl.css`/`web/huisstijl.js`, nooit gekopieerd per pagina. `alert()`/`confirm()`/`prompt()` blijven verboden — gebruik `melding()`, `bevestig()`, `vraagTekst()`.
4. **Template gewijzigd → regenereren:** na een edit aan `web/template.html` altijd `python3 scripts/generate_viz.py` (nooit `web/index.html` met de hand aanraken).
5. **Geen nieuwe dependencies, geen build step.** Plain Flask + statische bestanden.
6. **Afspraken veranderd → CLAUDE.md bijwerken** (zoals de huisstijl-paragraaf dat nu al doet).

Rollen in de stories: **bezoeker** (leest anoniem), **bijdrager** (ingelogd; mensen én agents), **reviewer**, **maintainer**, **mobiele gebruiker**.

Omvang: S = uurtje, M = dagdeel, L = dag of meer.

---

## ✅ Spoor 1 — Huisstijl-fundament *(afgerond 1 juli 2026)*

Eén gedeelde huisstijl (`web/huisstijl.css` + `web/huisstijl.js`, zelf-gehost Inter in `web/fonts/`), topbal-navigatie op alle pagina's (Werkbank en Beheer eindelijk vindbaar), alle 37 native browserdialogen vervangen door toasts en nette dialogen (inclusief de verplichte afwijs-motivatie), automatische toetsenbord-bedienbaarheid + zichtbare focus, `prefers-reduced-motion`, en gelijkgetrokken kleursemantiek: **blauw = actief/interactief, goud = telling/open werk, groen/rood = oordeel.** Details: CLAUDE.md § *Huisstijl (gedeelde UI-laag)*.

---

## ✅ Spoor 2 — De visualisatie: eenvoud door gelaagdheid *(afgerond 2 juli 2026)*

Alle vijf stories gebouwd; de audit-cijfers (~30–40 controls, 55 title-only tooltips, rauwe database-namen, dode admin-laag) zijn weggewerkt:

- **W2.1 Eenvoudige standaardstand** — de zijbalk toont default alleen Kleuring (praktijkmodel), Filters en Tijdlijn (theoriemodel: 2 secties); Thema's, Drempelwaarden, Systemische effecten, Layout, Node-grootte en Modelgezondheid zitten achter de **Geavanceerd**-schakelaar onderin (sticky; `localStorage` `pm-geavanceerd`; puur visueel — alle toggles houden hun stand).
- **W2.2 Klikbare uitleg** — gedeeld popover-component in de huisstijl: `<button class="uitleg" data-uitleg="…">ⓘ</button>` + `.hs-popover` (één tegelijk; Esc/klik-buiten/nogmaals-klikken sluit; capture-fase zodat een ⓘ in een label of inklapkop niets omzet). Alle 18 sidebar-ⓘ's en de lange `title=`-teksten zijn omgezet; alleen korte actie-hints bleven als `title`. Herbruikbaar op /overleg voor W3.3.
- **W2.3 Leesbare namen** — `weergaveNaam()` + uitzonderingen-map `NAAM_WEERGAVE` in `web/shared_vocab.js` (spelling: "Media-eigenaar", trema's als "Commerciële afhankelijkheid"/"Inlichtingen-coöptatie", afkortingen als "PR-inhuur"/"STAK-stemzeggenschap"/"Woo-obstructie"; betekenis: "Draaideur politiek ↔ media", "Raad van commissarissen (RvC)"). De viz hernoemt in-memory (`.key` bewaart de ruwe sleutel; zoeken matcht beide), /overleg en /werkbank wrappen index-labels, doel-badges, rol-dropdowns en mechanisme-vermeldingen. API/scores onveranderd.
- **W2.4 Model-schakelaar-intro** — eenmalige toelichting onder de schakelaar (tekst = DOCUMENTATIE.md § "Architectuur: twee lagen"); sluit met Begrepen-knop, Esc of de schakelaar zelf; daarna nooit meer (`pm-model-intro`); pijltje blijft naar de schakelaar wijzen bij rand-klemming.
- **W2.5 Admin-laag aangesloten** — `initAuth` zet `setAdminMode(true)` voor een ingelogde maintainer; de verwijder-/ontkoppelknoppen (met `bevestig({gevaar:true})` sinds spoor 1) volgen dus de accountrol; het `pm-admin`-localStorage-restje en de dode `#adminToggle`-verwijzing zijn verwijderd. Server blijft de echte poort.

Geverifieerd met headless-Chrome-screenshots (desktop 1680×1050 + mobiel 390×844; verse bezoeker, geavanceerde stand, praktijkmodel, popover open, rol-thread op /overleg) en nul console-errors op /, /overleg en /werkbank. NB: oud headless rapporteert `innerWidth` minimaal 500 — mobiele klem-logica is daarom op de code geverifieerd, niet op de capture.

---

## ✅ Spoor 3 — Overleg als uitnodigende werkplek *(afgerond 2 juli 2026; W3.2b afgerond bij spoor 4)*

Alle vier stories gebouwd; de audit-punten (leeg rechtervlak, ~8–9 knoppen per argument, `5·3`-geheimtaal, drie gestapelde filterlagen) zijn weggewerkt:

- **W3.1 Warme start** — zonder hash-permalink toont het rechtervlak een startkaart: wachtrij-tellingen per soort (Argumenten/Theorie/Herkeuring/Praktijk, klikbaar naar de juiste Voorstellen-lijst; reviewers zien ze bovenaan, anderen eerst de activiteit), threads met lopende bezwaren (resolutielus 'open'/'herzien'), en de zes recentste argumenten (nieuw/gemerged, klikbaar naar hun thread), plus de bestaande éénregel-uitleg. Geen nieuw endpoint: `/api/recent_changes` verrijkt argument-regels met claim + thread-anker (via `_wortel_doel`), `/api/discussion_index` draagt `n_bezwaar` per thread (recursieve CTE), en de review_queue-fetch wordt gedeeld met de tab-badge. Deeplinks werken exact als voorheen; terug naar hash-loos (browser-terug) toont de startkaart weer.
- **W3.2 Rustige argument-knopen** — gekozen patroon: één **⋯-menu** per knoop (consequent, ook touch/toetsenbord). In rust toont een argument alleen inhoud + oordeel-paar (✓/✗) + saldo + ⋯ (= 3 interactieve elementen, was ~8–9). In het menu: Bewijs vóór/tegen, bewerk/merge/afwijzen, reviseer/herkeuren, de bezwaar-resolutielus-acties en de afgewezen-context-acties (verbeteren/heropenen) — zelfde rolpoorten als voorheen; de bezwaar-badge bleef als pure status. Het menu-component is gedeeld: `hsMenu(anker, items)` in de huisstijl (één tegelijk, toggle, Esc sluit met focus terug, klik-buiten/scroll sluit, ↑/↓ lopen door items, `gevaar`-variant, `'---'`-scheiding).
- **W3.3 Tellingen die zichzelf uitleggen** — de `.t-n`-badge telt **root-argumenten · waarvan nog 'voorgesteld'**; dat staat nu in een expliciete title per badge én een legenda bij de lijstkop ("7·2 = 7 argumenten · 2 open" + ⓘ-popover). De `X/Y akkoord`-meta op voorstel-kaarten kreeg een ⓘ-popover (quorum, indiener telt niet, agent = advies, maintainer-quorum in de opbouwfase). Goud = open werk bleef consequent.
- **W3.4 Eén filterbalk** — de drie gestapelde lagen zijn één `#oBalk` in exact twee rijen: rij 1 = zoekveld + `● open`-chip, rij 2 = soort-select + filter-select (met kleurdot die het gekozen filter spiegelt). Zelfde state/gedrag (`actiefSoort`/`actiefFilter`/`alleenOpen`); de accordeons in de lijst bleven; mobiel wrapt zonder horizontale scroll.

Geverifieerd met headless-Chrome-screenshots (desktop 1680×1050 + mobiel 390×844; startkaart anoniem én als reviewer, thread met open ⋯-menu via een wegwerp-testkopie met ME-stub op `/static/`) en nul console-regels op /, /overleg en /werkbank. `scripts/test_fase2.py` weer groen gemaakt: de test was gerot t.o.v. twee eerdere commits (harde bronplicht 6af4f97, kandidaat-adoptie 0cb6473) — bijgewerkt mét behoud van elke testbedoeling (de zachte merge-poort wordt nu via een legacy-DB-rij getest; de harde creatiepoort kreeg een eigen assert).

### ✅ W3.2b — Viz-discussieboom volgt het ⋯-patroon *(afgerond 2 juli 2026, meegenomen in de spoor-4-regeneratieslag)*

`renderArgNode` toont per knoop nu alleen inhoud + oordeel-paar (✓/✗) + één ⋯; "↩ Reageer" werd "＋ Bewijs vóór… / － Bewijs tegen…" en de bezwaar-resolutie-linkjes werden menu-items (zelfde identiteitsregels; `bezwaarRegel` houdt de pure statusbadge) — alles via het gedeelde `hsMenu`. De ⋯-ankerknopstijl is nu een huisstijl-klasse **`.hs-menu-knop`** (gedeeld door /overleg en de viz; overleg's lokale kopie is opgeruimd). Anoniem toont de viz-boom geen ⋯ meer (zoals /overleg; het reply-formulier kon anoniem tóch nooit posten).

---

## ✅ Spoor 4 — Mobiel bruikbaar *(afgerond 2 juli 2026)*

Alle drie stories gebouwd; de audit-punten (zijbalk volledig weg onder 900 px, detailkolom-sliver op 390 px, paneel/modal met vaste breedtes) zijn weggewerkt:

- **W4.3 Overleg: lijst → detail met terugknop** — onder 800 px zijn index en gesprek twee schermen: `#oDetail` zit in een nieuwe wrapper `#oPaneel` met een mobiele terugbalk ("← Alle threads"); item-tik of hash-permalink opent het gesprek-scherm (`.m-detail` op `#tab-overleg`, desktop negeert de klasse), de terugknop wist de hash en toont de lijst weer. Startkaart blijft desktop-gedrag; mobiel begint bij de lijst. Geen kolom < 200 px meer; Voorstellen/Bronnen-tabs wrappen zoals voorheen.
- **W4.1 Viz: zijbalk als overlay** — de oude `display:none`-media-query is vervangen: onder 900 px opent een ☰-knop (eerste element in de topbar) de zijbalk als overlay-paneel van links (backdrop; sluit met ×-rij "Weergave & filters", Esc en tap-buiten; `visibility` haalt haar dicht ook uit de tab-volgorde). Inhoud identiek aan desktop, incl. Geavanceerd. De topbar wrapt mobiel naar meerdere rijen (subtitle/stats verborgen) en een `ResizeObserver` meet de echte hoogte terug in `--topbar-h` zodat zijbalk/detail/backdrop/graaf blijven aansluiten. `body{overflow:hidden}` = geen horizontale scroll; graaf pan/zoombaar bij dicht paneel.
- **W4.2 Viz: detail als sheet + passende modal + Esc** — onder 700 px wordt `#detail` een full-screen sheet (100 vw) met sticky ×-sluitknop die bovenaan blijft bij intern scrollen; verse selectie begint bovenaan (`scrollTop = 0`, ook desktop). De add-modal paste al qua breedte (`width:100%; max-width:460px`) en kreeg kleinere overlay-padding op smal scherm. **Esc sluit nu gelaagd, ook op desktop:** add-modal → zijbalk-overlay → detailpaneel, in een capture-fase-handler die een open hs-menu/-popover/-dialoog of de model-intro voorrang geeft (die sluiten zichzelf) en een gefocust invoerveld eerst blurt (geen dataverlies bij typen).

Geverifieerd met headless-Chrome-screenshots (desktop 1680×1050 ongewijzigd; mobiel 390×844 + 500×900 — de echte headless-viewportbreedte — voor lijst/gesprek-met-terugknop, ☰-topbar, open overlay-paneel, detail-sheet, open ⋯-menu in de viz-boom en op /overleg (ME-stub-testkopie), add-modal) en nul console-regels op /, /overleg, /werkbank en de testkopieën (capture-sanity via proefballon; `--screenshot=/dev/null` bleek de console-capture te breken — echte bestandsnaam gebruiken). De terugknop-lus is functioneel bewezen met een auto-click-testkopie (deeplink → gesprek → klik ← → lijst).

---

## ✅ Spoor 5 — Lichter & levend *(afgerond 2 juli 2026)*

*Audit was: `index.html` woog 2,8 MB — data + app-code in één inline scriptblok; elke datawijziging vergde hergenereren; review-flows toonden daarom overal "regenereer de viz"-instructies.*

### ✅ W5.1 — Data via endpoint, dunne pagina

Gekozen architectuur (vastgelegd in CLAUDE.md § web layer):

- **`/` serveert `web/template.html` direct** (~345 KB < 400 KB) — geen aparte opvolger-pagina. De databouw verhuisde naar repo-root **`viz_data.py`** (`export_data(conn)` + `laatste_release()`, patroon van `scoring.py`), gedeeld door het nieuwe **`GET /api/graph_data`** (compacte JSON ~2,0 MB, mtime-cache op DB + `bridging.json` + nieuwste release: koud ~0,9 s, warm ~10 ms) en de statische export.
- **Boot-loader zonder herstructurering:** het app-script (6000+ regels) staat inert als `type="text/plain" id="appScript"`; een klein bootscript toont een **laadscherm** (spinner + tekst; foutstaat met "Probeer opnieuw"-knop en fallback-kleuren als zelfs huisstijl.css ontbreekt), haalt de data en evalueert het app-script daarna als klassiek script — alle declaraties blijven globaal, dus alle inline `onclick=`-handlers bleven werken zonder één regel app-code te herschrijven. `shared_vocab.js` laadt als `/static/`-script i.p.v. de oude inline-placeholder.
- **Statische export blijft:** `scripts/generate_viz.py` bakt dezelfde data in de `"%%DATA%%"`-sentinel van de boot-loader (+ vocab inline) → `web/index.html`, bereikbaar als `/static/index.html`; de loader slaat de fetch dan over. Bewust verlies vastgelegd: `file://` is definitief dood (de loader toont dan netjes de foutstaat).
- **Regenereer-ritueel weg:** `/api/regenerate`, de auto-regen na merges en `PROPAGANDA_AUTO_REGEN` zijn verwijderd (met `subprocess`/`threading`/`sys`-imports); de /overleg-teksten zeggen nu "Nu in de graaf." — goedgekeurd werk is meteen zichtbaar.

Geverifieerd: graaf rendert op desktop 1680×1050 én mobiel 500×900; deeplink `/#sel=mechanism:19` opent het detailpaneel (bewijst volledige app-boot incl. hash-flows); nul console-regels op `/`, `/overleg`, `/werkbank` én `/static/index.html` (proefballon-sanity); foutstaat-capture via `file://`. Tests: `test_fresh_build.py` kreeg checks op `/` (dunne pagina + sentinel) en `/api/graph_data`; onderweg bleken `test_fresh_build.py` en `test_auth_smoke.py` al gerot t.o.v. de harde bronplicht (6af4f97, zelfde rot als eerder in `test_fase2.py`) — gerepareerd mét behoud van elke testbedoeling (bronplicht-asserts toegevoegd; merge-poort nu via legacy-DB-fixture) — beide groen.

---

## Doorlopende poets-backlog (klein spul, meenemen waar je toch bent)

- [ ] Inline hexcodes → tokens (`#3ddc84`→`var(--ok)`, `#e0635f`→`var(--fout)`, `#e0a23a`→`var(--warn)`, `#5bc8c2`→`var(--info)`) in de render-strings van overleg/werkbank/template — werkt ook in inline `style=`.
- [ ] Tekst onder 10 px opschalen waar het echt lezen is (kleurmeter-aslabels staan op 8 px; audit telde 48 gevallen < 11 px) en `--text-muted` niet voor dragende tekst gebruiken (contrast).
- [x] Ondertitel-capitalisatie gelijkgetrokken (2 juli 2026, meegenomen met W5.1): viz-topbar zegt nu ook "NL politiek & media".
- [ ] `web/account.html`: lokale `const melding` hernoemen (schaduwt de globale toast-functie; nu onschuldig, ooit een valkuil).
- [ ] Login-voettekst: `scripts/create_user.py`-verwijzing vriendelijker ("vraag de beheerder om een account", technische hint in een title).
- [ ] Viz-inputs (`.search-box input`, `.arg-form`): `outline: none` vervangen door het huisstijl-focuspatroon.
- [ ] `bronsug`-teal en andere restkleuren in overleg-CSS op tokens zetten.

---

## Volgorde-advies

1. ~~Spoor 2 (W2.1–W2.5)~~ — ✅ afgerond 2 juli 2026.
2. ~~Spoor 3 (W3.1–W3.4)~~ — ✅ afgerond 2 juli 2026.
3. ~~Spoor 4 (W4.3 → W4.1 → W4.2) + W3.2b~~ — ✅ afgerond 2 juli 2026.
4. ~~W5.1~~ — ✅ afgerond 2 juli 2026. **Alle sporen af**; wat rest is de doorlopende poets-backlog hierboven (klein spul, meenemen waar je toch bent).
