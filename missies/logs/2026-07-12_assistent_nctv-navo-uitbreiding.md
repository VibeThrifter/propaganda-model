# Missielog — NCTV/NAVO-uitbreiding + Agema-claim (6 subagenten)

**Datum:** 2026-07-12 · **Account:** `assistent` (indienen) · `maxime` (merge, op "via admin").
**Aanleiding eigenaar:** "Vind nog veel meer elementen met verschillende subagents.. ook over de nctv" + "En de navo" + "zoek navo → nctv → media en beleidssturing bewijzen" + "met corona" + "fleur agema zei dat via nctv via navo van alles werd bepaald naar VWS".

## Aanpak
Zes gedecorreleerde onderzoekssubagenten (general-purpose), elk met volle discipline (primair + verbatim, twee-niveau-neutraliteit, confounds, alleen nieuwe elementen, corona extra-streng op neutraliteit): (1) NCTV corona-framing; (2) corona-bronmonopolie RIVM/OMT; (3) ICCT US/NAVO-knoop; (4) NCTV-breedte + draaideur; (5) NAVO-beleidssturing; (6) NAVO-publieksdiplomatie. Plus een 7e subagent op de Agema-claim. Dragende quotes door de hoofdsessie zelf verbatim geverifieerd (parlement.com, ICCT AR2022-PDF-tekst geëxtraheerd via pypdf, Kamerstuk 28676-504, nctv.nl DTN 57, NOS 2525035, De Groene).

## Agema-claim: BEWUST NIET gemodelleerd (neutraliteit)
Primaire bron (Handelingen VWS-begroting 23-24 okt 2024, verbatim via regeringsantwoord Bruijn 23-9-2025) toont: Agema sprak over **toekomstige** pandemische paraatheid/weerbare zorg "onder regie van de NCTV en Defensie" in NAVO-context (post-2023 Resilience Objectives) — **niet** dat de coronacrisis via NAVO/NCTV werd aangestuurd. Het "via NAVO"-frame is een interpretatie van De Andere Krant; Agema noemde het zelf "echt hele grote onzin" (LighthouseTV, 3-11-2025). Structuur: OVV legt corona-eigenaarschap bij VWS; NCTV coördineert (ICCb), MCCb besluit; NAVO's COVID-rol = EADRCC-logistiek; NAVO-Resilience-Objectives dateren van ná de pandemie en zijn niet-afdwingbaar. Regering (Agema/Jansen/Bruijn) + 2 factcheckers weerleggen de "NAVO/NCTV stuurde corona"-lezing. → geen edge gebouwd; dat zou de complot-val in eigen stem zijn.

## Eerlijke nulbevinding NAVO→NCTV
Directe NAVO→NCTV-lijn niet documenteerbaar (NCTV noemt zelf EU/VN/GCTF; NAVO-CT loopt via COE-DAT/MIVD-militair kanaal). NAVO-invloed op de NL-CT-wereld loopt via ICCT (gemodelleerd) en Defensie/beleid (gemodelleerd).

## Ingediend & gemerged (via admin) — 0 mislukt
**Entiteiten (4):** #1157 Dick Schoof · #1158 Pieter-Jaap Aalbersberg · #1159 US Department of Homeland Security · #1160 USAID.
**Relaties (13):**
- Draaideur-carrousel (mech 18): Schoof→NCTV/AIVD/J&V/AZ (#2080-83); Akerboom(#924)→NCTV/Defensie/Politie (#2084-86); Aalbersberg→Politie/NCTV (#2087-88). Gedateerd; bruggen afgeleid. Drie opeenvolgende NCTV-coördinatoren met AIVD-lijn.
- ICCT-financiering (mech 52): US-DHS→ICCT (#2089), USAID→ICCT (#2090), NAVO→ICCT (#2091) + confound (Sahel/re-integratie/guidebook binden de knoop, sturen NL-analyse niet).
- NAVO→Defensie (mech 86, beinvloeding, #2092): NDPP-capaciteitsdoelen = beleidssturing (Kamerstuk 28676-504).
**Argumenten (18):** #3534-3551. Elke draaideur/financiering-edge een supporting-root met verbatim citatie; + op bestaande NCTV→NOS #427 een corona-framing-arg (DTN 57 "anti-overheidsextremisme ← coronaprotest") + confound (NCTV: "kritisch ≠ complotdenken"); + op NAVO→NOS #63 een norm-framing-arg + confound (De Groene "waarom vijf procent").

## Status
- `validate_model.py --strict`: **groen** (136 fouten, exact op baseline; golden snapshot byte-identiek).
- Zichtbaar in de viz na pagina-ververs.

## Openstaande leads
- Outlet-breedte NCTV→NU.nl/Telegraaf/RTL/AD (zoek-index-quotes, on-page bevestigen).
- Marc Kuipers (AIVD→NCTV, 2026) — benoemingsbron nog te verifiëren.
- "Alleen samen"-campagne (€18,7 mln 2021, primair Jaarevaluatie); corona-bronmonopolie RIVM/OMT grotendeels al in model (#676 e.a.).
- NAVO PDD co-sponsorship-grants met concreet recent NL-bedrag; ICCT-experts→andere media (attributie meest via Leiden ISGA).
- Datakwaliteit: dubbele VWS-entiteit #586/#820 → samenvoeg-kandidaat (M2.6).
- Neutrale optie-op-verzoek: NCTV als coördinator nationale crisisstructuur (ICCb) als gesourcet structureel feit.
