# Review-advies — ronde 1 (2026-06-21)

**Agent:** reviewbeoordelaar (alleen-lezen, geen token) · **Brief:** `missies/reviewbeoordelaar_brief.md`
**Wachtrij:** 32 voorgestelde argumenten · 4 voorgestelde relaties · 6 open RfC's.
**Aard van dit stuk:** advies voor de admin. Niets hieronder is in het model geschreven; jij beslist en merget.

> **Stance-balans van wat ik adviseer te mergen:** 10 supporting · 7 contradicting · 2 contextual.
> Tweezijdig in balans — de contradicting-kant wordt niet strenger beoordeeld dan de supporting-kant.

---

## ✅ MERGE-KLAAR (19 argumenten + 3 relaties)

Poort gehaald (echt citaat of bron-met-locator), stance klopt, geen duplicaat.

**Gezonde steun/tegen-paren (redteam — voorbeeldig tweezijdig):**
- **#573** contradicting · rel.360 (SDM→DPG, onafhankelijkheidsborging) — 2 citaten mét quote (Apax/PCM-uitholling, hof-wanbeleid). Sterke lezing aangevallen op de invloed-as. ✔
- **#574** supporting · rel.360 — citaat mét quote (ACM-voorwaarde 2025, veto op verkoop). ✔
- **#575** supporting · rel.413 (SDM→NU.nl, continuiteitsborging) — citaat mét quote (ACM-remedie). ✔
- **#576** contradicting · rel.413 — citaat mét quote ("zacht als boter, halfwaardetijd"). ✔
- **#578** contradicting · rel.415 (Unilever→VNO-NCW) — 2 citaten mét quote (dividendbelasting van tafel, hoofdkantoor→Londen). Begrenst de invloed-as, niet het lidmaatschap — netjes gescheiden. ✔

**Bestel / ledeneis (scout):**
- **#577** supporting · mech.121 (ledeneis) — 2 quotes (OCW-verkenning: stroming onmeetbaar → ledental beslissend). ✔
- **#582** contradicting · mech.121 — 2 quotes (partijen hebben nóg minder leden; ledeneis = zwakke proxy). ✔
- **#583** contextual · mech.121 — afwezigheidsrapport mét gelogde zoekwegen. Telt als bewijsdekking; exact wat de tweezijdigheidsplicht vraagt. ✔
- **#579** supporting · mech.123 (erkenningverlening) — 2 quotes (eenrichtingspoort, "onbeheersbaar"). ✔
- **#580** contradicting · mech.124 (omroepsignatuur) — 2 quotes (Verlind: macht gecentraliseerd bij NPO). ✔

**Ondergravingen (monitor — sterk, geen tegenbron nodig):**
- **#571** contradicting-reply op #426 · `correlatie_als_causatie` — wijst de aangevochten stap exact aan (Build Back Better was al VN-term sinds 2015 → co-occurrence ≠ frame-synchronisatie). ✔
- **#572** contradicting-reply op #368 · `citaat_dekking` — citaat dekt bron-afhankelijkheid, niet de *onderlinge concurrentie* die mech.153 onderscheidt. ✔

**Funding/academia & overig (mét echte quote):**
- **#545** supporting · rel.478 (OCW→Radboud) — Rathenau-quote (26% ongewenste invloed) + derde-geldstroom-%. ✔ *(zie cluster-kanttekening onder)*
- **#550** supporting · rel.483 (NWO→Radboud, zelfcensuur) — Rathenau-quote. ✔ *(KNAW-tegenbewijs verdient t.z.t. een eigen contradicting-root)*
- **#581** contextual · rel.415 — begrenst het tegenbewijs van #578. `contextual` is vrijgesteld van de bronplicht en telt in de zekerheidsbalans niet mee, dus laag risico. *Kanttekening: bevat feitclaims (1,4–2 mrd, regeerakkoord) zonder citaat — vraag eventueel een bron, maar geen blokker.*
- **#584** supporting · rel.476 (PAX→NOS, expert_legitimatie) — 2 Nieuwsuur-items waarin PAX als expert wordt opgevoerd. ✔ ⚠️ **Check eerst waarom voorganger #543 op ditzelfde doel is *verworpen*** voordat je merget.

**Verbinder-relaties + hun steunargument (instance-laag, 1 menselijke reviewer):**
- **rel.497** CvdM→Ongehoord Nederland (ledeneis) + **#586** — quotes (50.000-drempel, twee nieuwkomers). ✔
- **rel.498** CvdM→Omroep ZWART (ledeneis) + **#587** — zelfde bron, parallelle instantie. ✔
- **rel.496** OCW→Ongehoord Nederland (erkenningverlening) + **#585** — quotes (Uslu-besluit nov. 2023). ✔ ⚠️ **`certainty` staat op `None`** — zet bij de merge een zekerheidswaarde (anders valt de relatie buiten de scoring).

---

## ⚠️ VERBETEREN (8 — terug naar de auteur, niet afwijzen)

**Stance-fout op rel.482 (zelfcensuur Min. BuZa→PAX) — dit is de belangrijkste bevinding.**
De relatie heeft **alleen supporting-roots** (#549, #567, #568) en **geen enkele contradicting-root**, terwijl de F-35-rechtszaak tégen deze relatie pleit. CLAUDE.md noemt dit letterlijk als voorbeeld: de F-35-zaak *supports* de tegenmacht-relatie (rel.472) maar *contradicts* de zelfcensuur-relatie (rel.482). Nu zit dat tegenbewijs **begraven als "te wegen tegen-evidentie" binnen supporting-argumenten** — precies de fout uit de brief: DF-QuAD telt die nuance áls steun (duwt de claim omhóóg) en laat rel.482 vals `onweersproken`, zodat het M1.4-plafond nooit opgeheven wordt.
- **#549** supporting · rel.482 — splits de F-35-nuance af naar een **contradicting-root** op rel.482 (mét de PAX/F-35-bron). Bovendien: citaat-quote leeg (bron 83 heeft wél locator, dus poort haalt het, maar voeg een quote toe).
- **#567** supporting · rel.482 — idem: het PAX-conformeert-aan-NAVO-deel is een hypothese mét ingebouwde tegen-evidentie; de tegenkant hoort als eigen contradicting-root.
- **#568** supporting · rel.482 — dit ís inhoudelijk een weerlegging van het tegenbewijs ("bounds of debate"). Hoort als **reply (ondergraving) op de F-35 contradicting-root**, niet als supporting-root. Als root duwt het de claim onterecht omhoog.

> Praktische volgorde: maak eerst één contradicting-root op rel.482 die het F-35-tegenbewijs draagt; hang #568 daaronder; merge #549/#567 pas als hun caveat eruit is.

**Citaat-dekking te dun (poort technisch gehaald via locator, maar quote dekt de kernclaim niet):**
- **#544** supporting · rel.477 (PAX→FD) — het citaat beschrijft alleen *wat* "Don't Bank on the Bomb" is; de claim is dat het FD het "snel en ongecontroleerd overneemt". Die overname-claim is niet gedekt — vraag een bron die FD-berichtgeving toont.
- **#546** supporting · rel.479 (NWO→Radboud) — de NWA-bron (bron 89) heeft een **lege quote**; de 26%-quote is generiek (zelfde Rathenau-cijfer als #545/#550). De specifieke "NWO/NWA stuurt de agenda"-claim is niet met een quote gedekt.
- **#547** supporting · rel.480 (Radboud→NOS) — **geen quote**, alleen een locator-bron; een sterke theoretische claim (expertrol reproduceert consensus als neutraal frame) verdient een dragend citaat.
- **#548** supporting · rel.481 (Tweede Kamer→Radboud, flak) — bronnen relevant en mét locator (poort haalt het), maar **alle quotes leeg**, en de buitenlandse voorbeelden (CEU/Florida/Bolsonaro, `buitenlands`) staan ver van flak-op-Radboud. Trim naar de NL-casus of voeg dragende quotes toe.

**Structureel gat op een relatie:**
- **rel.499** NPO→Ongehoord Nederland + **#588** — de **relatie heeft geen mechanisme, geen filter, geen aard** (`None/None/None`). `type=oppositie` wijst op tegenmacht; ken een mechanisme + `aard` toe vóór de merge, anders valt de relatie buiten classificatie/scoring/viz. Het argument #588 zelf is prima (NPO-intrekkingsverzoek, mét quote).

---

## ❌ AFWIJZEN

Geen. Bij twijfel is het advies "verbeteren", niet afwijzen (conform brief).

---

## 📋 RfC's / open voorstellen (6) — inhoudelijk oordeel

Geen procesnoten (dat de indiener niet zelf goedkeurt is bekend) — kritiek op de merites.

- **#5 toetredingsdrempel (eigendom, halo) — ✅ steun, sterkste van de zes.** Freeze-test (bevries elke eigenaar → kostenstructuur blijft = onpersoonlijke staande conditie → halo) en afgrenzing (foto vs tourniquet t.o.v. eigendomsconcentratie #1; acquisitiestrategie #23; schijnpluriformiteit #6) zijn voorbeeldig. Akkoord-waardig. *Aanscherp:* invloed op de vloer tot een `property='influence'`-argument; bevestig halo-op-`alternatief_medium` boven een markt-breed veld.
- **#6 koopkrachtselectie (advertentie) — ✅ steun.** Onderscheidende claim (koopkracht i.p.v. kijkertal) sterk, afgrenzing schoon (vs advertentiedruk #3 / supportive_selling #5 / kijkcijferdisciplinering #160), instantiaties NL-concreet (FD/NRC-mediakits). *Aanscherp:* houd het gedocumenteerde deel (mediakit-/tariefpremie) los van het effect-deel (welvaartsbias in de agenda) — dat laatste verdient eigen bewijs.
- **#3 academische_doorlichting (tegenmacht) — 🔧 aanscherpen.** Definitie/afgrenzing schoon, maar de tegenmacht staat of valt met effectiviteit en het eigen falsificatiecriterium wijst eerder ríchting loos. Start de invloed op de vloer; vraag één concrete casus waarin academisch onderzoek een redactie/persbureau aantoonbaar tot correctie dwong (Boumans→ANP?).
- **#4 belanghebbende_als_adviseur (sourcing) — 🔧 aanscherpen.** Afgrenzing vs lobbyen/draaideur scherp, maar de enige instantiatie (BlackRock→Europese Commissie) is EU/buitenlands financieel toezicht, niet het NL-mediasysteem. Voeg een NL-relevante casus toe waarin belanghebbende-advies de berichtgeving aantoonbaar kleurde; nu blijft de schakel naar het nieuws een bewering.
- **#7 begrotingsorthodoxie (ideologie, halo) — 🔧 aanscherpen.** Freeze-test exemplarisch (anti-dubbeltel-redenering netjes). Hoofdpunt vóór akkoord: dit is een specialisatie ván `elite_referentiekader` (#20) — verdedig waarom het een eigen halo verdient en borg dat twee halo's op dezelfde knoop de ideologie-kracht niet dubbel tellen. Houd de toon beschrijvend (naturalisatie), niet MMT-partijdig.
- **#9 lezersfinanciering_isolatie (tegenmacht) — ⛔ bezwaar** (mijn eigen voorstel). Lezersfinanciering oefent geen tegenmacht úít — het haalt de hefboom van Filter 2 wég. Een positieve tegenmacht-edge publiek→media modelleert de áfwezigheid van een kracht als een kracht; dat botst met de negatieve telling van tegenmacht en dreigt dubbel te tellen met de advertentiefilter. Overweeg een **moderator op de advertentie-relaties** i.p.v. een los mechanisme. Bovendien te dun: één instantiatie + een bron-stub.

---

## Systemische kanttekeningen voor de admin

1. **rel.482 `onweersproken`-val** (zie boven) — de hoogste prioriteit; los dit op vóór je de supporting-roots merget.
2. **Lege quotes bij locator-bronnen.** Veel `claude-code`-argumenten (#547, #548, #549, #546, deels #545) leunen op bronnen mét locator maar **zonder quote**. De poort laat ze door (locator = echte citatie), maar de citaat-dekking is dan niet in één blik te controleren. Overweeg quotes te eisen vóór merge.
3. **Generieke quote-recycling.** De Rathenau-26%-quote (bron 88) draagt #545, #546 én #550 op drie verschillende relaties. Op losse doelen telt elk mee, maar het is één bevinding die breed wordt uitgesmeerd — weeg het gewicht navenant.
4. **Drie verbinder-relaties met `certainty = None`** (rel.496/497/498) — zet bij de merge een zekerheidswaarde, anders missen ze in de scoring.
