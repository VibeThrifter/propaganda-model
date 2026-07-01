# Ideoloog-ronde — landelijke media + partij-denktanks (2026-06-27)

**Brief:** `missies/ideoloog_brief.md` (bestand nog niet in git op moment van uitvoeren;
HEAD `722342e`). Account: `assistent` (bijdrager, Bearer-token). Alles ingediend als
`voorgesteld` — een mens beslist.

**Scope:** entiteiten zonder bestaand `politieke_positie`-signaal; landelijke nieuwsmedia
+ partij-gelieerde wetenschappelijke bureaus. Bewust NIET aangeraakt: de partijen (CHES) en
Ernestine Comvalius (twee andere lopende rondes).

**Vooraf geverifieerd (sqlite):** geen van de doelwitten (3, 6, 9, 13, 43, 44, 46, 47, 100,
195, 257, 264) en evenmin de Volkskrant (4) droeg al een `politieke_positie`-root.

## Queries (web + database)

DB-queries vooraf:
- `SELECT id,name FROM entities WHERE id IN (9,100,3,195,6,264,13,257,46,47,43,44)` → alle 12 bestaan.
- `SELECT entity_id,property_value FROM arguments WHERE property='politieke_positie' AND entity_id IN (...)` → leeg (geen bestaande signalen).
- `SELECT id,name FROM entities WHERE name LIKE '%Volkskrant%'...` → de Volkskrant = id 4 (+ Stichting de Volkskrant 230). Geen signaal op 4/230.

WebSearch / WebFetch (chronologisch):
1. WS "Teldersstichting wetenschappelijk bureau VVD liberalisme over ons" → vondst.
2. WS "Wiardi Beckman Stichting wetenschappelijk bureau PvdA sociaaldemocratie over ons" → vondst.
3. WF https://www.teldersstichting.nl/over-ons/ → verbatim missie.
4. WF https://www.wbs.nl/publicaties/over-de-wbs → verbatim missie.
5. WS "Het Financieele Dagblad FD redactionele uitgangspunten over ons vrije markt ondernemers" → merkpagina.
6. WS "De Groene Amsterdammer over ons missie onafhankelijk progressief links opinieblad" → over-ons.
7. WF https://www.groene.nl/over → verbatim (tegen kolonialisme / algemeen kiesrecht / tegen totalitair denken).
8. WF https://fdmg.nl/merken/fd/ → verbatim doelgroep/oogpunt.
9. WS "Follow the Money over ons missie onderzoeksjournalistiek macht ..." → over-ftm.
10. WS "De Correspondent over ons missie manifest tegengif waan ..." → manifest.
11. WF https://www.ftm.nl/over-ftm → **403 Forbidden** (geen verbatim te citeren).
12. WF https://decorrespondent.nl/manifest → verbatim principes (zie afweging hieronder).
13. WF https://nl.wikipedia.org/wiki/Follow_the_Money → geen verbatim FTM-eigen missie-citaat.
14. WF https://www.ftm.nl/artikelen/doemee → **403 Forbidden**.
15. WS "De Telegraaf signatuur rechts-populistisch ... wakker Nederland conservatief" → vnl. kritische bronnen (BNNVARA/Groene).
16. WS "NRC Handelsblad signatuur liberaal over ons progressief-liberaal" → NL-Wikipedia.
17. WF https://en.wikipedia.org/wiki/De_Telegraaf → verbatim "conservative and populist style".
18. WF https://nl.wikipedia.org/wiki/NRC_(krant) → verbatim "liberale signatuur" + Lux et Libertas.
19. WS "de Volkskrant signatuur over ons links progressief ..." → EN-Wikipedia.
20. WS "Het Parool signatuur Amsterdams dagblad progressief links over ons" → EN-Wikipedia.
21. WF https://en.wikipedia.org/wiki/De_Volkskrant → verbatim "centre-left".
22. WF https://en.wikipedia.org/wiki/Het_Parool → **geen** verbatim eigen-signatuur (alleen lezerspubliek "liberal and left-wing").
23. WS "Algemeen Dagblad AD signatuur politieke kleur over ons midden onafhankelijk" → zelfbeschrijving "neutraal", derden "iets rechts van midden".

## Oogst (ingediend — alles `voorgesteld`)

| entity | as:pool | source_id | arg_id | bron (verbatim-kern) |
|---|---|---|---|---|
| 46 Teldersstichting | economisch:rechts | 258 | **858** | teldersstichting.nl/over-ons — "liberale denktank ... wetenschappelijk onderzoeksbureau van de VVD ... bevordering van het liberale gedachtegoed" |
| 47 Wiardi Beckman Stichting | economisch:links | 259 | **859** | wbs.nl/over-de-wbs — "wetenschappelijk bureau van de sociaal-democratie ... analyseren vanuit een sociaal-democratische gezindheid" |
| 264 De Groene Amsterdammer | cultureel:progressief | 260 | **860** | groene.nl/over — "tegen kolonialisme ... pleitbezorger van algemeen kiesrecht ... tegen totalitair denken" (post-materiële/emancipatoire waarden) |
| 195 Het Financieele Dagblad | economisch:rechts | 261 | **861** | fdmg.nl/merken/fd — "nieuwsmerk van ... Ondernemers, bestuurders en professionals ..." (zakelijk-ondernemende oriëntatie) |
| 9 De Telegraaf | cultureel:conservatief | 262 | **862** | en.wikipedia "conservative and populist style" (woord: conservative) |
| 9 De Telegraaf | establishment:anti-establishment | 262 | **863** | zelfde quote (woord: populist) — andere as, andere dimensie (dubbeltel-regel: 1 signaal per as) |
| 100 NRC Media | economisch:rechts | 263 | **864** | nl.wikipedia "liberale signatuur" + Lux et Libertas "vrijheid ... liberale grondhouding" |
| 4 de Volkskrant | economisch:links | 264 | **865** | en.wikipedia "leading centre-left Catholic broadsheet" |

## Onbepaald gelaten (met reden — geen modelknoop, conform brief)

- **257 Follow the Money** — missiepagina's (over-ftm, doemee) gaven **403** op WebFetch;
  Wikipedia leverde geen verbatim FTM-eigen ideologisch citaat. Onbronbaar verbatim →
  niet ingediend. (Vermoedelijke lean: economisch:links "99 procent" + anti-establishment
  waakhond — maar zonder geverifieerde quote niet codeerbaar.)
- **13 De Correspondent** — manifest is methode-/waarden-georiënteerd ("tegengif tegen de
  waan van de dag", "niet sensationeel maar fundamenteel"). De enige as-achtige quote
  (kritiek op commerciële advertentie-media) is bovendien expliciet verzacht ("Wij
  beschouwen onszelf niet als de oplossing voor alles wat er mis is in 'de media'").
  Coderen zou projectie zijn → onbepaald.
- **6 Het Parool** — EN-Wikipedia karakteriseert alleen het *lezerspubliek* als "liberal
  and left-wing", niet de redactionele lijn zelf. "Sociaal-democratisch karakter" uit een
  zoeksamenvatting was niet verbatim te bevestigen op een fetchbare pagina → onbepaald
  (geen mis-attributie).
- **3 AD (Algemeen Dagblad)** — zelfbeschrijving expliciet "neutraal, geen politieke of
  religieuze voorkeur"; derden plaatsen het mild "iets rechts van midden" (betwist).
  Geen schoon, eenduidig signaal → onbepaald.
- **43 Clingendael / 44 HCSS** — buitenlands-/veiligheidsbeleid-instituten; output is
  internationaal (onderwerp buitenlands), geen verifieerbare binnenlands-ideologische
  zelfpositionering gevonden → onbepaald.

## Balans van de ronde

- **Stance:** 9 × supporting, 0 contradicting, 0 contextual.
- **Pool-balans (9 signalen):**
  - economisch: **rechts ×3** (46, 195, 100) — **links ×2** (47, 4)
  - cultureel: **progressief ×1** (264) — **conservatief ×1** (9)
  - establishment: **anti-establishment ×1** (9) — establishment ×0
- Lichte rechts-overweging op de economische as, maar tweezijdig (links én rechts, progressief
  én conservatief gevoed). De rechts-tilt komt deels doordat de twee schoonst-citeerbare
  bronnen (FD-merkpagina, NRC liberale signatuur) rechts leunen; FTM/Parool die mogelijk links
  zouden balanceren bleven onbepaald wegens onbronbaarheid.

## Twijfelgevallen voor de menselijke reviewer

1. **NRC (arg 864, economisch:rechts):** "liberale signatuur" is ambigu (markt-liberaal vs
   cultureel-liberaal); dezelfde Wikipedia citeert een journalist die de krant "verschoven
   naar links-liberaal" noemt. Pool/as narekenen — eventueel afzwakken of een tweede
   (cultureel/links) signaal afwegen.
2. **de Volkskrant (arg 865, economisch:links):** "centre-left" is historisch/origineel;
   de bron noemt verzachting sinds 1980 naar "centrist". Actualiteit narekenen.
3. **FD (arg 861, economisch:rechts):** gebaseerd op doelgroep/oogpunt-positionering
   (ondernemers/financieel-economisch), niet op een expliciete vrije-markt-/deregulerings-
   uitspraak. Zwakker dan een programmatisch standpunt; reviewer weegt of dit voldoende is.
4. **De Telegraaf (args 862/863):** twee signalen uit één quote, op twee verschillende
   assen (conservative→cultureel, populist→establishment). Conform dubbeltel-regel (1 per
   as), maar de reviewer kan vinden dat een neutrale Wikipedia-karakterisering zwakker weegt
   dan een zelfpositionering.
