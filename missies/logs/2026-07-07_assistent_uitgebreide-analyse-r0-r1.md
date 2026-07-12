# Missielog — Uitgebreide analyse: Ronde 0 (klasse/consumptie) + Ronde 1 (Sourcing)

**Datum:** 2026-07-07 · **Account:** `assistent` (alles `voorgesteld`) · Plan: klasse-cluster diep + brede onderzoeksagenda-sweep, RfC's toegestaan.
Werkwijze: parallelle onderzoeks-agents → **ik verifieer élke quote zelf via WebFetch/WebSearch** → manifest → `scout_indienen.py`.

## Ronde 0 — Klasse/consumptie/advertentie-cluster (manifest `ronde0-klasse-consumptie.json`)

Beantwoordt "lezen C/D wel nieuws, of alleen entertainment/sport?" → **niet (a) maar (b)**: modaliteitskloof.

**Argumenten op `koopkrachtselectie` #176** (bronnen 1084-1087):
- #2062 *supporting* — MODALITEITSKLOOF (SCP Media:Tijd, geverifieerd via WebSearch): *"Nieuws via televisie is voor
  laagopgeleiden een populaire informatiebron, terwijl hoogopgeleiden juist relatief vaak nieuwssites/-apps bezoeken
  en nieuwsradio beluisteren."*
- #2063 *contextual* — GEDEELDE KERN / begrenzing (NOS over SCP-WRR *Gescheiden werelden?* 2014): *"Beide
  opleidingsgroepen noemen het NOS Journaal als belangrijkste nieuwsbron."* (tempert overclaiming — NL ≠ VS).
- #2064 *contextual* — KENNISKLOOF-STAART (de Bruin e.a., *Journalism Studies* 2024, geverifieerd): 'Nieuwsbuitenstaanders'
  24,7%, lager opgeleid, nieuws "te moeilijk".

**Welstandsmeter — C/D-kant + neutrale kern** (`doelgroepklasse`, SCP-verankerd, geen mediakit):
- #2065 **SBS6 → welstand:C** (Joop/BNNVARA over SCP): *"Laagopgeleiden kijken wel veel televisie, in het bijzonder
  commerciële en ook regionale zenders."*
- #2066 **NOS → welstand:meting:0.0** (klasse-neutrale gedeelde kern).

**RfC #44 — nieuw emergent veld `kenniskloof`** (informatie-ongelijkheid naar klasse; leden: adverteerder/mediaorganisatie/
publiek; afgrenzing ≠ medialogica/toeschouwersdemocratie; falsificatiecriterium + 2 instantiaties + SCP/de Bruin-bronnen).
Wacht op **2 menselijke reviewer-akkoorden**.

**Voorspelling** — modaliteitskloof blijft/neemt toe t/m 2028 (SKO/NOM/Reuters-meetcriterium, anker #176, kans 0,8).

## Ronde 1 — Sourcing (manifest `ronde1-sourcing.json`, 11 argumenten 2067-2077)

Alle quotes verbatim door mij geverifieerd (bij de SVDJ-Kamervragen bleek de agent-parafrase "66%/83,3%" onjuist →
échte verbatim gebruikt: "Tweederde ... 1183 sets" / PVV "83 procent").

- **bron_afhankelijkheid #6:** #2067 ANP-copy 24→28% + Metro 53%/Sp!ts 61% (Scholten & Ruigrok/Nieuwsmonitor 2009);
  #2068 online ~66% ANP, integrale overname (proefschrift Boumans UvA 2016 via Adformatie); **#2069 *contradicting*** —
  eerlijk tegenwicht: géén aantoonbare toename (Vliegenthart 2016) → hoog-maar-stabiel, niet groeiend.
- **pakketjournalistiek #7:** #2070 'papegaaiencircuit' (Ruigrok, *Uitvoeringsorganisaties in het nieuws* 2022).
- **intermedia_agendering #157:** #2071 berichtgeving elders = nieuwswaarde-trigger (Ruigrok 2022).
- **media_agendering #148:** #2072 ⅔ van 1.183 Kamervragen uit media-aandacht, PVV 83% (SVDJ 2021); #2073 agenda-setting
  definitie (Ruigrok & van Atteveldt, *Medialogica in Campagnetijd* 2012).
- **mediageniekheidsselectie #161:** #2074 "Nieuws is geen gegeven, maar een keuze" (Ruigrok 2022).
- **pr_subsidie #9:** #2075 CBS 149.000 communicatieprofessionals vs ~18.000 journalisten (Villamedia/Oremus 2018);
  #2076 Rijksoverheid 936,5 fte communicatie 2023 (primaire overheidsbron).
- **inlichtingen_cooptatie #133:** #2077 voorlichters van 'toelichten' → 'overtuigen', schermen bewindslieden af
  (Bloemendaal in De Groene, *Roernalistiek* 2009).

`validate --strict` groen (alles `voorgesteld` → scores onveranderd). Entiteiten ANP (#12) en RVD (#581) bestaan al —
concrete ANP→outlet / RVD→outlet instantiatie-relaties zijn een mogelijke vervolgstap.

## Openstaand
- **Ronde 2 (Flak & Ideologie)** loopt: zelfcensuur/kijkcijferdisciplinering + etikettering/spectrum_bewaking/schijndebat.
- **Ronde 3** (draaideur/partij + literatuur-args op laag-scorende emergente velden) daarna.
- Mergen = mens (via admin); RfC #44 + de voorspelling wachten op menselijke beoordeling.
- Negatieve zoekresultaten (bv. geen schone NL nep-persbericht-casus; geen Telegraaf/NRC-intermedia-cijfer) bewust
  **niet** ingediend — alleen hier gelogd.
