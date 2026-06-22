# Review-advies — ronde 2 (2026-06-21)

**Agent:** reviewbeoordelaar (alleen-lezen, geen token) · **Brief:** `missies/reviewbeoordelaar_brief.md`
**Wachtrij (vers afgeleid uit `/api/review_queue`):** 32 voorgestelde argumenten · 4 voorgestelde relaties · 6 open RfC's · 0 entiteiten · 0 herkeuring.
**Aard van dit stuk:** advies voor de admin. Niets hieronder is in het model geschreven; jij beslist en merget. Machineleesbaar advies staat in `data/review_advies.json` (rechts van elk wachtrij-item op `/overleg`).

**Nieuw sinds ronde 1:** de draaideur-trits (#562–#566, NIDV/Energie-NL/YES) en twee extra rel.482-roots (#567, #568) zijn bijgekomen. De zes RfC's en de vier relaties (496–499) zijn ongewijzigd; mijn inhoudelijke oordeel daarop is bevestigd, niet herzien.

> **Stance-balans van wat ik adviseer te mergen** (merge-klaar + context-met-kanttekening): **16 supporting · 7 contradicting · 2 contextual.**
> Van de schone `merge-klaar`-set: 11 supporting · 7 contradicting · 1 contextual. De contradicting-kant (alle redteam/scout/monitor-tegenargumenten plus de gezonde steun/tegen-paren) wordt niet strenger beoordeeld dan de supporting-kant; de oververtegenwoordiging van supporting komt doordat de verbinder- en draaideur-batches per definitie steun-instantiaties zijn. Geen tweezijdigheids-scheefgroei in de beoordeling zelf.

---

## ✅ MERGE-KLAAR (19 argumenten)

Poort gehaald (echt citaat of bron-met-locator), stance klopt, geen duplicaat.

**Gezonde steun/tegen-paren (redteam — voorbeeldig tweezijdig):**
- **#573** contradicting · rel.360 (SDM→DPG, onafhankelijkheidsborging) — 2 quotes (Apax/PCM-uitholling, hof-wanbeleid), invloed-as. ✔
- **#574** supporting · rel.360 — quote (ACM-voorwaarde 2025, veto op verkoop). ✔
- **#575** supporting · rel.413 (SDM→NU.nl, continuiteitsborging) — quote (ACM-remedie). ✔
- **#576** contradicting · rel.413 — quote ("zacht als boter, halfwaardetijd"). ✔
- **#578** contradicting · rel.415 (Unilever→VNO-NCW) — 2 quotes (dividendbelasting van tafel okt 2018, hoofdkantoor→Londen). Begrenst de invloed-as, niet het lidmaatschap. ✔

**Bestel / ledeneis (scout):**
- **#577** supporting · mech.121 (ledeneis) — 2 quotes (OCW-verkenning: stroming onmeetbaar → ledental beslissend). ✔
- **#582** contradicting · mech.121 — 2 quotes (partijen hebben naar verhouding nóg minder leden; ledeneis = zwakke proxy). ✔
- **#583** contextual · mech.121 — afwezigheidsrapport mét gelogde zoekwegen; telt als bewijsdekking. ✔
- **#579** supporting · mech.123 (erkenningverlening) — 2 quotes (eenrichtingspoort, "onbeheersbaar"). ✔
- **#580** contradicting · mech.124 (omroepsignatuur) — 2 quotes (Verlind: macht gecentraliseerd bij NPO). ✔

**Ondergravingen (monitor — vorm + reasoning correct, geen tegenbron nodig):**
- **#571** contradicting-reply op #426 · `correlatie_als_causatie` — wijst de stap exact aan (Build Back Better was VN-term sinds 2015 → co-occurrence ≠ frame-synchronisatie). ✔
- **#572** contradicting-reply op #368 · `citaat_dekking` — citaat dekt bron-afhankelijkheid, niet de onderlinge concurrentie die mech.153 onderscheidt. ✔

**Draaideur-trits (claude-code — NIEUW deze ronde):**
- **#562** supporting · rel.485 (Van Nieuwenhuizen→Energie-Nederland) — 2 NL-locatorbronnen (NOS + FTM): overstap + lobbyverbod + bemoeienis. ✔
- **#563** supporting · rel.487 (Hillen→NIDV) — defensie-magazinebron dekt het voorzitterschap. ✔
- **#564** supporting · rel.488 (Eijsink→NIDV) — NIDV-persbericht (2017). ✔
- **#565** supporting · rel.489 (Knops→NIDV) — NIDV-persbericht (2023). ✔
  > Voor #562–#565: alle quotes leeg maar de URL-locators passeren de poort en dekken de enkelvoudige feitclaims. Een quote zou natrekken versnellen — niet blokkerend.

**Funding/academia & verbinder (mét echte quote):**
- **#545** supporting · rel.478 (OCW→Radboud) — Rathenau-quote (26% ongewenste invloed) + derde-geldstroom-%. ✔ *(zie quote-recycling onder)*
- **#550** supporting · rel.483 (NWO→Radboud, zelfcensuur) — Rathenau-quote. ✔ *(KNAW-tegenbewijs verdient t.z.t. een eigen contradicting-root)*
- **#584** supporting · rel.476 (PAX→NOS, expert_legitimatie) — 2 Nieuwsuur-items met quote. ✔ Voorganger #543 op dit doel is verworpen ("geen bron"); #584 lost dat op met dragende citaten.

---

## 🟡 CONTEXT — mergebaar, maar zet eerst één veld (9)

Op zichzelf passeert het de poort; los de kanttekening op vóór of bij de merge.

**Verbinder-relaties met `certainty = None` (instance-laag, 1 menselijke reviewer):**
- **rel.496** OCW→Ongehoord Nederland (erkenningverlening, eigendom, direct) + **#585** (Uslu-besluit nov 2023, 2 quotes) — zet bij de merge een `certainty`, anders valt de relatie buiten de scoring.
- **rel.497** CvdM→Ongehoord Nederland (ledeneis, eigendom, direct) + **#586** (50.000-drempel) — idem `certainty`.
- **rel.498** CvdM→Omroep ZWART (ledeneis, eigendom, direct) + **#587** (parallel aan rel.497) — idem `certainty`.

**Structureel veld ontbreekt op de relatie:**
- **#588** supporting · rel.499 (NPO→Ongehoord Nederland) — sterk argument met quote (boete €132k, intrekkingsverzoek). De relatie zelf (`relatie:499`) staat als **verbeteren**: zonder mechanisme/filter/aard + `certainty` valt ze buiten classificatie/scoring/viz.

**Draaideur — zwakste fit:**
- **#566** supporting · rel.492 (Ollongren→Yalta European Strategy) — feit gedekt via Wikipedia-locator, maar YES is een internationaal beleidsforum, geen NL-branchelobby met direct media-/beleidsbelang. NL-mediasysteem-relevantie dunner dan de NIDV-trits; mergebaar maar weeg laag.

**Contextual met onbronnde feitclaims (vrijgesteld van bronplicht):**
- **#581** contextual · rel.415 — begrenst het tegenbewijs van #578 (afschaffing stond wél in regeerakkoord, ~1,4–2 mrd). Telt niet in de zekerheidsbalans; bevat feitclaims zonder citaat — vraag eventueel een bron, geen blokker.

---

## ⚠️ VERBETEREN (8 — terug naar de auteur, niet afwijzen)

**Stance-fout op rel.482 (zelfcensuur Min. BuZa→PAX) — de belangrijkste bevinding, en hij is deze ronde erger geworden.**
rel.482 (`aard=veld_eigenschap`, halo) heeft nu **drie supporting-roots (#549, #567, #568) en géén enkele contradicting-root**. CLAUDE.md noemt dit letterlijk als voorbeeld: de F-35-rechtszaak *supports* de tegenmacht-relatie (rel.472) maar *contradicts* de zelfcensuur-relatie (rel.482). Nu zit dat tegenbewijs **begraven als "te wegen tegen-evidentie" binnen supporting-argumenten**. DF-QuAD telt die nuance áls steun (duwt rel.482 omhóóg) en laat de relatie vals `onweersproken`, zodat het M1.4-plafond nooit opgeheven wordt.
- **#549** supporting · rel.482 — splits de F-35-nuance af naar een **contradicting-root** op rel.482 (mét de PAX/F-35-bron); voeg een quote toe aan bron 83 (lege quote, locator wel aanwezig).
- **#567** supporting · rel.482 — alignment-hypothese mét ingebouwde tegen-evidentie (F-35, interne verdeeldheid, eerdere anti-VS-positie); de tegenkant hoort als eigen contradicting-root.
- **#568** supporting · rel.482 — dit ís een weerlegging van het F-35-tegenbewijs ("bounds of debate"/`spectrum_bewaking`). Hoort als **reply (ondergraving) onder de F-35 contradicting-root**, niet als supporting-root.
  > Praktische volgorde: maak eerst één contradicting-root op rel.482 die het F-35-tegenbewijs draagt; hang #568 daaronder; merge #549/#567 pas als hun caveat eruit is.

**Citaat-dekking te dun (poort technisch gehaald via locator, maar quote dekt de kernclaim niet):**
- **#544** supporting · rel.477 (PAX→FD) — het citaat beschrijft alleen *wat* "Don't Bank on the Bomb" is; de overname-claim ("FD neemt snel/ongecontroleerd over") is niet gedekt. Vraag een FD-artikel.
- **#546** supporting · rel.479 (NWO→Radboud) — NWA-bron (89) heeft lege quote; de 26%-quote is dezelfde generieke Rathenau-recycling. De "NWO/NWA stuurt de agenda"-claim mist een dragende quote.
- **#547** supporting · rel.480 (Radboud→NOS) — alleen locator-bron, lege quote; een sterke theoretische claim verdient een dragend citaat.
- **#548** supporting · rel.481 (Tweede Kamer→Radboud, flak) — alle quotes leeg, en de buitenlandse voorbeelden (CEU/Florida/Bolsonaro, `buitenlands`) staan ver van flak-op-Radboud. Trim naar de NL-casus (Schoof-bezuiniging) of voeg dragende quotes toe.

**Structureel gat op een relatie:**
- **rel.499** NPO→Ongehoord Nederland — geen mechanisme, geen filter, geen aard (`None/None/None`) + `certainty=None`. `type=oppositie` wijst op tegenmacht; ken een mechanisme + `aard` (+ `certainty`) toe vóór de merge. Het steunargument #588 zelf is prima.

---

## ❌ AFWIJZEN

Geen. Bij twijfel is het advies "verbeteren", niet afwijzen (conform brief).

---

## 📋 RfC's / open voorstellen (6) — inhoudelijk oordeel

Geen procesnoten. Kritiek op de merites.

- **#5 toetredingsdrempel (eigendom, halo) — ✅ steun, sterkste van de zes.** Freeze-test (bevries elke eigenaar → kostenstructuur blijft = onpersoonlijke staande conditie → halo) en afgrenzing (foto vs tourniquet t.o.v. eigendomsconcentratie #1; acquisitiestrategie #23; schijnpluriformiteit #6) zijn voorbeeldig; NL-instantiaties concreet (Correspondent/FtM). *Aanscherp:* invloed op de vloer tot een `property='influence'`-argument; bevestig halo-op-`alternatief_medium` boven een markt-breed veld.
- **#6 koopkrachtselectie (advertentie, direct) — ✅ steun.** Onderscheidende claim (koopkracht i.p.v. kijkertal) sterk, afgrenzing schoon (vs advertentiedruk #3 / supportive_selling #5 / kijkcijferdisciplinering #160), instantiaties NL-concreet (FD/NRC-mediakits). *Aanscherp:* houd het gedocumenteerde deel (mediakit-/tariefpremie) los van het effect-deel (welvaartsbias in de agenda) — dat laatste verdient eigen bewijs.
- **#3 academische_doorlichting (tegenmacht) — 🔧 aanscherpen.** Definitie/afgrenzing schoon (wetenschap onderzoekt de media zelf, vs onderzoeksjournalistiek/socialisatie), maar de tegenmacht staat of valt met effectiviteit en het eigen falsificatiecriterium wijst eerder ríchting loos. Start de invloed op de vloer; vraag één concrete NL-casus waarin academisch onderzoek een redactie/persbureau aantoonbaar tot correctie dwong (Boumans→ANP?). De bronnen zijn nu stub-titels.
- **#4 belanghebbende_als_adviseur (sourcing) — 🔧 aanscherpen.** Afgrenzing vs lobbyen/draaideur scherp, maar de enige instantiatie (BlackRock→Europese Commissie) is EU/buitenlands financieel toezicht, niet het NL-mediasysteem; de relevantie-as weegt zwaarder voor het NL-onderwerp. Voeg een NL-relevante casus toe waarin belanghebbende-advies de berichtgeving aantoonbaar kleurde — nu blijft de schakel naar het nieuws een bewering.
- **#7 begrotingsorthodoxie (ideologie, halo) — 🔧 aanscherpen.** Freeze-test exemplarisch (anti-dubbeltel-redenering netjes: actieve plaatsers — CPB/Financiën/denktanks — hebben al eigen gerichte schakels). Hoofdpunt vóór akkoord: dit is een specialisatie ván `elite_referentiekader` (#20) — verdedig waarom het een eigen halo verdient en borg dat twee halo's op dezelfde knoop de ideologie-kracht niet dubbel tellen. Houd de toon beschrijvend (naturalisatie), niet MMT-partijdig.
- **#9 lezersfinanciering_isolatie (tegenmacht) — ⛔ bezwaar.** Lezersfinanciering oefent geen tegenmacht úít — het haalt de hefboom van Filter 2 wég. Een positieve tegenmacht-edge publiek→media modelleert de áfwezigheid van een kracht als een kracht; dat botst met de negatieve telling van tegenmacht en dreigt dubbel te tellen met de advertentiefilter. Overweeg een **moderator op de advertentie-relaties** i.p.v. een los mechanisme. Bovendien te dun: één instantiatie (De Correspondent) + een bron-stub ("vindplaats toe te voegen door de reviewer").

---

## Systemische kanttekeningen voor de admin

1. **rel.482 `onweersproken`-val** (zie boven) — hoogste prioriteit en deze ronde verder verslechterd (drie supporting-roots, nul contradicting). Los dit op vóór je #549/#567/#568 merget; maak eerst de F-35 contradicting-root.
2. **Lege quotes bij locator-bronnen.** Veel `claude-code`-argumenten (#547, #548, #549, #546 deels, en de hele draaideur-trits #562–#566) leunen op bronnen mét locator maar **zonder quote**. De poort laat ze door (locator = echte citatie), maar de citaat-dekking is dan niet in één blik te controleren. Overweeg quotes te eisen vóór merge — voor de draaideur-feiten (#562–#565) is dat licht werk en maakt het natrekken triviaal.
3. **Generieke quote-recycling.** De Rathenau-26%-quote (bron 88) draagt #545, #546 én #550 op drie verschillende relaties. Op losse doelen telt elk mee, maar het is één bevinding die breed wordt uitgesmeerd — weeg het gewicht navenant.
4. **Vier voorgestelde relaties, vier structuur-gaten.** rel.496/497/498 hebben `certainty = None`; rel.499 mist mechanisme/filter/aard én `certainty`. Zet die velden bij de merge, anders missen de relaties in de scoring/classificatie/viz.
