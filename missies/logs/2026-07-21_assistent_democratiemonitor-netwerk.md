# Missielog — Democratiemonitor & SDM-netwerk (assistent, 2026-07-21)

**Opdracht (eigenaar).** De Stichting Democratie Monitor (democratiemonitor.nl) bracht rapporten uit over de staat van de democratie; eigenaar wil de organisatie, haar financier, de betrokken personen, hun ideologieën, gedeelde clubjes en politieke partijen in het model. LinkedIn expliciet toegestaan ("sowieso, maar alleen relevante connecties rapporteren").

**Neutraliteitsdiscipline (leidend).** Alles is als *neutrale structurele feiten* gemodelleerd. Het model beweert **niet** dat het rapport "links/elitair/pro-macht bevooroordeeld" is — die eigenaars-lezing is geen modelfeit en er is geen gepubliceerde criticus die het rapport partijdig noemt (dus ook niet als geattribueerde flak inbrengbaar). Politieke lean wordt uitgedrukt via **gesourcete affiliatie-edges** (bv. naar een partij), niet via een eigen-stem-oordeel of een verzonnen kleurmeter-score. Alles landt `voorgesteld` — mens beslist.

## Ingediend (account `assistent`, alles `voorgesteld`)

**Bronnen (7):** 2190 DM-over-ons · 2191 DM-rapport-juli-2026 · 2192 SDM-initiatiefpagina (funding) · 2193 DM-briefing-Tweede-Kamer · 2194 NOS/NPO Radio 1 (13-6-2025) · 2195 LinkedIn Bas Bijlsma (grijs, zelfrapport) · 2196 website Pieter van Boheemen (grijs, zelfrapport).

**Entiteiten (9):** 1172 Stichting Democratie Monitor (denktank) · 1173 Bas Bijlsma · 1174 Pieter van Boheemen · 1175 Mariken van der Velden · 1176 Matthijs Rooduijn · 1177 Bert Bakker · 1178 Data for Peace and Security · 1179 Fossil Free Football · 1180 Stichting Post-X Society. *Hergebruikt (niet gedupliceerd):* SDM 130, Tweede Kamer 107, UvA 311, VU 864, GroenLinks-PvdA 1073, Rathenau 828.

**Relaties (18, elk met mechanisme):**
- Kern: 2108 SDM→DM *financiering* (m52) · 2109 DM→Bijlsma *denktank_levert_expert* (m118) · 2110 DM→Tweede Kamer *denktank_naar_politiek* (m54) · 2111 DM→NPO Radio 1 *expert_framing* (m8).
- Team/adviesraad-affiliaties (draaideur m18): 2112 Bijlsma→DM · 2113 van Boheemen→DM · 2114–2116 adviesraad (Velden/Rooduijn/Bakker)→DM · 2117 Velden→VU · 2118 Rooduijn→UvA · 2119 Bakker→UvA.
- Bijlsma-netwerk (draaideur m18): **2120 Bijlsma→GroenLinks-PvdA** (voorzitter commissie buitenland, 2021-11–2025-07) · 2121 Bijlsma→UvA (advisory council GSSS) · 2122 Bijlsma→Data for Peace and Security · 2123 Bijlsma→Fossil Free Football.
- van Boheemen-netwerk (draaideur m18): 2124 van Boheemen→Post-X Society · 2125 van Boheemen→Rathenau Instituut.

**Argumenten (18):** 3589–3606, elk een `supporting` root met verbatim citatie op de bijbehorende relatie.

## Onderzoek & negatieve resultaten (blijven in dit log, niet in het model)
- **Bas Bijlsma** — LinkedIn (sessie door eigenaar vernieuwd, toen gescraped) bevestigt identiteit én loopbaan: directeur DM (2024-08), **voorzitter commissie buitenland GroenLinks-PvdA 2021–2025**, Data for Peace and Security (oprichter), Fossil Free Football (voorzitter), UvA advisory council; opleiding UvA (Human Geography BSc, Int. Development Studies MSc cum laude). De eerder gevonden `pvda.nl/politici/bas-bijlsma` (301 → progressiefnederland.nl) is hiermee als dezelfde persoon bevestigd — mis-attributie uitgesloten.
- **Pieter van Boheemen** — géén partij-/kandidatuur gevonden (biotechnoloog/Waag; directeur Post-X Society; ex-Rathenau). Wel de relevante brug DM↔Post-X (dubbeldirecteurschap) → gemodelleerd.
- **Matthijs Rooduijn, Bert Bakker, Mariken van der Velden** — academici (populisme/politieke communicatie, UvA/VU); géén partijaffiliatie gevonden → **geen** `politieke_positie`-signaal (onbepaald is correcter dan een structurele proxy; conform ideoloog-discipline "structureel ≠ ideologisch").
- **Kleurmeter:** bewust **geen** axis-signalen toegekend. Een partijfunctie is een structureel feit, geen as-geframede uiting; de politieke tie zit in edge 2120, niet in een verzonnen persoonsscore.
- **BNR-artikel** ("democratie niet door APK") kon niet verbatim geverifieerd worden (403) → géén DM→BNR-edge (anti-overfit: één edge per geverifieerd artikel; alleen NPO Radio 1 gemodelleerd).

## Balanscontext voor de reviewer (niet als modelargument ingediend)
DM omschrijft zichzelf als **politiek neutraal**: verbatim (over-ons) *"We zijn politiek neutraal, maar nemen wel duidelijk stelling voor het belang van de democratische rechtsstaat."* Dit hoort bij de tweezijdige weging bij de merge-beoordeling.

## Status / handoff
Golden-snapshot + `validate_model.py --strict`: groen, geen fouten boven baseline (alle bijdragen `voorgesteld`, dus buiten de score/viz tot review). Geen `smaad_hold` (alle persoonsclaims neutraal-biografisch). Te reviewen via `/overleg` → review_queue / `/werkbank` (assistent). Ik stel voor; de eigenaar merget/weegt.

---

## Ronde 2 — netwerkverdieping (2026-07-21, alles gemerged via admin/maxime)

Bronnen: research-subagent (publieke sweep) + LinkedIn (Mariken van der Velden, dun) + eigen fetches. Nieuw gemodelleerd (goedgekeurd + argumenten met verbatim citaties):

**Entiteiten (3):** 1181 Hot Politics Lab (UvA) · 1182 Nederlandse Democratie Coalitie · 1183 Stichting Weerbare Democratie. *Hergebruikt:* PAX 194, Transparency International NL 627, Post-X 1180.

**Relaties (8):**
- Gedeeld academisch clubje: 2126 Rooduijn→Hot Politics Lab · 2127 Bakker→Hot Politics Lab · 2128 van der Velden→Hot Politics Lab (lidmaatschap, m18). Alle drie DM-adviesraadleden zitten in hetzelfde UvA-lab (cross-institutioneel: van der Velden zit op de VU).
- Democratie-coalitie: 2129 DM→NDC (partner) · 2130 SDM→NDC (financiering, m180) · 2131 PAX→NDC (initieerde, m179). NDC = door PAX geïnitieerd, door SDM gesteund, coördinator programmabureau Niesco Dubbelboer.
- Tweede DM-financier: 2133 Stichting Weerbare Democratie→DM (financiering, m52).
- Gedeelde financier: 2134 SDM→Post-X Society (financiering, m52). **SDM financiert zowel DM als Post-X; van Boheemen runt beide** — de kern-"clubje".

**Argumenten:** 3609–3616, elk verbatim gesourcet.

### Bewust NIET gemodelleerd (eerlijk, discipline)
- **Partijlidmaatschap academici:** Rooduijn, Bakker, van der Velden — géén partijlidmaatschap/kandidatuur gevonden (schone negatieve uitkomst). Bakker heeft überhaupt geen niet-academische functies.
- **Rooduijn ↔ Wiardi Beckman Stichting (PvdA-bureau):** Rooduijn publiceert herhaaldelijk in *S&D* (WBS, entity 47). Dat is **auteurschap, geen lidmaatschap** → niet als structurele edge gemodelleerd (zou de band overdrijven). Wel vermeldenswaard als intellectuele band met de PvdA-sfeer.
- **Ministerie BZK → Post-X (staatsfinanciering):** BZK staat als financier op de Post-X-site (alt "Ministerie van Binnenlandse Zaken logo") — relevant (staat financiert de election-integrity-observatory) maar er is **geen goedgekeurd overheidssubsidie-mechanisme** (RfC's #55/#56 staan open) → niet als edge ingediend; kandidaat voor een RfC.
- **TI→NDC:** niet verbatim te bevestigen → edge weer verwijderd (2132) i.p.v. mis-attributie.
- **SDM-bestuur-kruisverbanden** (Venema→European Press Prize, Comvalius→The Black Archives, van Daalen→Bits of Freedom, Zonderop→Clingendael): stonden al in het model — bevestigd, niets toegevoegd.

Strict-gate groen; KOPPEL-ENT-ROL 0; golden snapshot groen; nieuwe knopen live in de viz.

---

## Ronde 3 — op eigenaarsverzoek "via admin" (2026-07-21)

- **RfC #56 goedgekeurd** (via admin/maxime = quorum) → nieuw mechanisme **`overheidssubsidie_denktank` (202)**, filter sourcing (staat financiert 'onafhankelijke' expert). Uitvoering schoon, geen edge-migratie. *(RfC #55 overheidssubsidie_ngo blijft open — niet nodig voor deze casus.)*
- **Ministerie BZK (821) → Post-X Society (1180)** financiering, mech 202 (rel 2153, arg 3642). Bron: Post-X-financierspagina (BZK-logo). Staatsfinanciering van de election-integrity-observatory nu correct gemodelleerd i.p.v. geleend op #52.
- **Matthijs Rooduijn (1176) → Wiardi Beckman Stichting (47)** `bron_van`, mech 135 elite_kennisnetwerk (rel 2154, arg 3643). Bron: wbs.nl (S&D-artikel "Vrolijke noodzaak…", 08-06-2022). **Expliciet gelabeld: auteurschap/kennisnetwerk, GÉÉN partijlidmaatschap** — de band met de PvdA-sfeer via publiceren in het partijblad, niet overdreven tot lidmaatschap.

Alles gemerged via admin; strict-gate groen; KOPPEL-ENT-ROL 0; golden snapshot groen.
