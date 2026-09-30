# Onbewaakte ronde — verificatie-agent · ronde1 · 2026-07-24

- Brief: `missies/verificatie_agent_brief.md` (blob `969fa0aa4939`)
- Account: `verificatie-agent`
- Gestart: 2026-07-24T09:29:56

## Sessie-uitvoer

**Taak:** A1 — onafhankelijke bron-herverificatie van `voorgesteld` supporting/contradicting-roots.

### Voorregel & wachtrij

- `GET /api/agent/reeds_gereageerd` → `gereageerd_op: []`, `via_reply: []` (leeg — dat spoor is afgeleid van replies/ratings, niet van `immuun_oordelen`).
- `/api/review_queue` vereist reviewer+ (403 voor bijdrager) → wachtrij rechtstreeks uit de DB gehaald (toegestaan per agent-contract: "find target ids straight from the DB").
- Kandidaten: `status='voorgesteld' AND parent IS NULL AND NOT vervangen AND stance IN (supporting,contradicting) AND (property IS NULL OR property='influence')` → **54 roots**.
- Al eerder door mij beoordeeld (`immuun_oordelen`, fase=herverificatie): 3477, 3552, 3553, 3582, 3583, 3584 → overgeslagen.
- **Netto deze ronde: 48 roots** (id 3618–3709), drie clusters: REKA/Clingendael, Justice for Prosperity, en de NPO/omroep-toezichthouders-benoemingen (oud-politici in RvT's).

### Fetch-log (alle live; archief eerst geprobeerd)

`web.archive.org` gaf voor de Wayback-kopieën van src71 en src2177 telkens *"Claude Code is unable to fetch from web.archive.org"* → conform brief teruggevallen op de **live-URL** (een onbereikbaar archief blokkeert de check niet zolang de live-bron de quote levert). Alle onderstaande fetches slaagden live (tijdstip ~09:30–09:45 lokaal).

| Bron | URL | resultaat |
|---|---|---|
| src71 (spit.nl) | onderzoekscollectiefspit.nl/verhalen/in-de-top-van-de-npo-grossieren… | 4 quotes verbatim ✓ |
| src2177 (JfP About us) | justiceforprosperity.org/about-us/ | van Gemert (Supervisory Board) / Errens (Board, Senior Advisor) / Olara (Vice Chair) ✓ |
| src2209 (REKA) | rekanetwork.org/news | BuZa-overeenkomst-quote verbatim ✓ |
| src2208 (Bob Deen) | denhaag.headliner.nl/item/bob-deen-volgt-monika-sie-op… | 'specialismen…Rusland/Oost-Europa' + 'hoofd Security Unit' ✓ (REKA niet genoemd) |
| src2218 (netkwesties) | netkwesties.nl/1940/conflict-over-aanstelling-hoogleraar.htm | 'onverenigbaar met het bedoelde hoogleraarschap' verbatim ✓ |
| src2223 (BNNVARA) | bnnvara.nl/pauw-de-wit/artikelen/maandagavond-oa… | gastenlijst 22-09-2025, Postma naast Yeşilgöz ✓ |
| src2224 (FTM) | ftm.nl/artikelen/ftm-interviewt-jelle-postma | 'confrontatie aan met VVD-partijleider Dilan Yeşilgöz' verbatim ✓ |
| src2236 (SIDN) | sidn.nl/en/news-and-blogs/whodis… | 'detect cross-platform polarisation' verbatim ✓ (Belgisch bedrijf niet genoemd) |
| src2237 (JfP IDV) | justiceforprosperity.org/international-far-right-network… | substantie ✓, opgegeven quote = parafrase |
| src2238 (JfP Defend) | justiceforprosperity.org/grote-groei-rechtsextremistische-defend-groepen/ | beheerder-quote verbatim (afgekapt) ✓ |
| src2239 (JfP homepage) | justiceforprosperity.org/ | 'JfP and Pointer (KRO-NCRV) jointly investigated…' verbatim ✓ |
| src2245 (Asante) | parlement.com/id/…/a_a_amma_asante | Commissariaat-quote + PvdA-verleden ✓ |
| src2246 (Ganzevoort) | parlement.com/biografie/profdr-rr-ruard-ganzevoort | GL-EK 2011-2023 + KRO-NCRV RvT 2014-2022 ✓ |
| src2262 (Vliegenthart) | parlement.com/biografie/dr-arjan-vliegenthart | EK SP 2007-2014 + SP-wethouder Amsterdam ✓ |
| src2250 (Peetoom) | parlement.com/biografie/drs-gr-ruth-peetoom | 'voorzitter CDA, 2 april 2011 – 9 februari 2019' verbatim ✓ |
| src2255 (Holterhues) | parlement.com/id/…/f_w_j_eric_holterhues | 'sinds 13 juni 2023 lid ChristenUnie-fractie Eerste Kamer' ✓ |
| src2243 (Dekker) | parlement.com/biografie/drs-s-sander-dekker | VVD + staatssecretaris OCW (media) ✓ |
| src2240 (Nijpels) | parlement.com/biografie/drs-ehthm-ed-nijpels | 'voorzitter RvT TROS, dec 2007 – 1 jan 2014' + VVD/VROM ✓ |
| src2241 (Staal) | parlement.com/biografie/mr-b-boele-staal | 'lid RvT TROS, vanaf april 2008 (vanaf 2014 AVRO/TROS)' + D66 EK/CvdK ✓ |
| src2232 (EO RvT) | eo.nl/bestuur | Peetoom + Sweet als RvT-leden ✓ |
| src2252 (WNL RvT) | wnl.tv/over-wnl/organisatie | Kruithof + Paffen-Zeenni als RvT-leden ✓ |
| src2256 (KRO-NCRV RvT) | kro-ncrv.nl/…/raad-van-toezicht | 'Eric Holterhues is voorzitter' ✓ |
| src2260 (VPRO RvT) | vpro.nl/info/raad-van-toezicht | 'Bernt Schneiders (voorzitter)' + Marjolein Meijer ✓ |
| src2263 (HUMAN RvT) | human.nl/info/raad-van-toezicht | 'Arjan Vliegenthart (Chair)', benoemd 19-06-2022 ✓ |
| src2258 (ZWART RvT) | omroepzwart.nl/over-ons/raad-van-toezicht | Melody Deldjou Fard (termijn 2026-2030) ✓ |
| src2247 (RPO) | stichtingrpo.nl/ruard-ganzevoort-nieuwe-voorzitter… | Ganzevoort voorzitter RvT RPO per KB 07-07-2026 ✓ |
| src2248 (NLPO) | nlpo.nl/nieuws/yvonne-van-delft-nieuwe-voorzitter… | Van Delft voorzitter NLPO per 01-12-2025 + wethouder-quote ✓ |
| src2264 (NPO) | npo.nl/pers/…/npo-tjibbe-joustra-nieuwe-voorzitter… | 'Joustra … benoemd tot lid en voorzitter van de RvT van de NPO' verbatim ✓ |
| src2265 (security.nl) | security.nl/posting/19056 | 'Joustra vertrekt op 1 januari 2009 als NCTb … sinds april 2004' verbatim ✓ |
| src2251 (Sweet) | noordholland.pvda.nl/nieuws/elvira-sweet-bezoekt-hoorn-en-enkhuizen/ | 'PvdA-Gedeputeerde van Noord-Holland Elvira Sweet' verbatim ✓ |
| src2259 (Schneiders) | binnenlandsbestuur.nl/carriere/bernt-schneider-pvda-pleegt-partijverraad | 'De oud-burgemeester van Haarlem, Bernt Schneiders (PvdA)' verbatim ✓ |
| src2261 (Meijer) | groenlinks.nl/nieuws/marjolein-meijer-verkozen-tot-partijvoorzitter-groenlinks | titel verbatim ✓ (verkozen apr 2016) |
| src2253 (Kruithof) | villamedia.nl/artikel/annemarie-van-gaal-en-henri-kruithof… | 'voormalig VVD-spindoctor Henri Kruithof' verbatim ✓ |
| src2254 (Paffen) | amersfoort.nl/wethouder-micheline-paffen-zeenni-cda | 'Wethouder Micheline Paffen-Zeenni (CDA)' verbatim ✓ |
| src2257 (GL Utrecht) | utrecht.groenlinks.nl/nieuws/…kandidaat-lijsttrekkers… | 'Melody Deldjou Fard (46 jaar) … gemeenteraadslid voor de GroenLinks fractie' verbatim ✓ |
| src2249 (GL Leiden) | leiden.groenlinks.nl/onze-mensen/yvonne-van-delft-wethouder | GroenLinks-wethouder Leiden ✓ |

### Verdicten (48 rijen, alle `POST …/herverificatie` → 201)

**twijfel (3):**
- **#3619** (rel 2137, supporting) — 'specialismen…Rusland/Oost-Europa' + 'hoofd Security Unit' verbatim ✓, **maar de headliner-bron noemt REKA niet**; de "boegbeeld/uitvoerder van REKA"-koppeling is inferentieel, niet door deze bron gedekt.
- **#3668** (rel 2177, supporting) — 'detect cross-platform polarisation' verbatim ✓ + SIDN-fonds financierde WhoDis van JfP ✓, **maar 'ontwikkeld met het Belgische bedrijf' staat niet in deze bron** (kern gedekt, dat detail niet).
- **#3669** (rel 2178, supporting) — substantie klopt (IDV = Dutch branch of Generation Identity; Frans moederorg. in 2021 verboden en 'classified as a private militia'), **maar de opgegeven quote is een parafrase/synthese**, niet verbatim.

**klopt (45):** 3618, 3631, 3644, 3664, 3665, 3666, 3667, 3670, 3671, 3674, 3675, 3676, 3677, 3678, 3679, 3680, 3681, 3682, 3683, 3684, 3685, 3686, 3687, 3688, 3689, 3690, 3691, 3692, 3693, 3694, 3695, 3696, 3697, 3698, 3699, 3700, 3701, 3702, 3703, 3704, 3705, 3706, 3707, 3708, 3709 — bron live opgehaald, quote (of de dragende parlement.com-/omroep-RvT-vindplaats) verbatim teruggevonden en de claim gedekt. Detail per rij in `immuun_oordelen.detail`.

### Negatieve resultaten / kanttekeningen (alléén hier, geen modelbijdrage)

- **web.archive.org onbereikbaar** voor de twee gearchiveerde bronnen (src71, src2177); live-fetch was de fallback en leverde de quotes verbatim. Geen verdict-verlaging (brief: onbereikbaar archief blokkeert niet zolang de bron elders de quote geeft).
- **#3619 / #3668**: kern-quotes kloppen verbatim, maar telkens dekt de aangehaalde bron één losse claim-toevoeging niet (REKA-boegbeeld resp. het Belgische ontwikkelbedrijf). Tip voor documentalist/aanklager — géén verificatie-taak, dus niet als boomnode ingebracht.
- **#3669**: bewering inhoudelijk juist; een auteur-revisie die de quote vervangt door de verbatim-zin ('IDV is the Dutch branch of Generation Identity (GI), a pan-European identitarian movement whose French parent organisation, Génération Identitaire, was banned by the French government in 2021') tilt dit naar 'klopt'. Tip, geen bijdrage.

### Verdict-balans

- **klopt 45 / twijfel 3 / klopt-niet 0** (van 48).
- Mildheids-toets (brief): hoge `klopt`-ratio is verdedigbaar — overwegend de NPO/omroep-toezichthouders-cluster (publiek-registerfeiten: parlement.com-biografieën, officiële omroep-RvT-pagina's, partij-persberichten) die woordelijk reproduceerbaar zijn. Niet weggekeken: waar een bron een sub-claim of de exacte quote níét dekte → bewust `twijfel` (3×), niet `klopt`. Geen `klopt-niet`: geen enkele quote bleek gehallucineerd of verkeerd toegeschreven.
- Geen 429; wachtrij deze ronde volledig afgewerkt.
```
