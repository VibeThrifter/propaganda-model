# Scout-ronde: sterkste routes r4 — flak-casussen (bestaan sterk, sturing begrensd)

- **Datum:** 2026-07-04 · **Account:** assistent · **Git-hash:** de441f1
- **Opdracht:** eigenaar — "100 relaties/entiteiten langs de sterkste routes"; Flak-route conform
  het onderzoeksverdict: *bestaan sterk, sturing door de rechtsstaat begrensd* — beide kanten even
  hard gesourcet (tweezijdige oogstplicht).
- **Tooling:** `scripts/scout_indienen.py` + `data/scout/sterkste-routes-r4.json`.

## Queries (letterlijk, research-agent — 22 stuks)
Pretium Telecom rechtszaken journalisten media Netkwesties 120 procedures · Pretium Olsthoorn
rechtszaak journalist gewonnen · Willem Blijdorp Financieele Dagblad SLAPP rechtszaak 150.000 euro ·
Hof Den Haag 22 december 2015 Pretium Tros Radar verborgen camera artikel 10 EVRM dwangsom
vernietigd · ECLI:NL:HR:2019:1044 Pretium cassatie · ECLI Gerechtshof Den Haag 22-12-2015 Pretium
AVROTROS afgifte beeldmateriaal verborgen camera uitspraak · Peter Olsthoorn Pretium LinkedIn
rechtszaak vragen journalist 2009 · Blijdorp FD vonnis rechtbank Amsterdam 2024 hoger beroep
rectificatie Iran · Clare Locke Follow the Money advocatenkantoor dreigbrief Amnesty Wordt Vervolgd ·
PersVeilig onderzoek juridische bedreiging journalisten 2024 SLAPP helft zelfcensuur · "Blijdorp" FD
hoger beroep 2025 OR 2024 gerechtshof smaad B&S · RSF World Press Freedom Index 2025 Netherlands
ranking third place · Villamedia Raad voor de Journalistiek klachten Follow the Money afgewezen juni
2020 · Olsthoorn Pretium "vijf" rechtszaken webboek gewonnen dossier · Rijksoverheid wetsvoorstel
anti-SLAPP richtlijn 2024/1069 implementatie internetconsultatie april 2025 · Transparency
International Nederland "Lifting the lid on lobbying" 44% bewindspersonen lobbyist draaideur · Free
Press Unlimited "minimalistisch" anti-SLAPP wetsvoorstel consultatie reactie november 2024 · SLAPP
Nederland 2025 rechtszaak tegen journalist smaadzaak medium recente zaken · Follow the Money kort
geding politieke partij China banden publicatieverbod afgewezen september 2025 · rechtszaak
journalist Nederland 2026 SLAPP smaad eis mediabedrijf onderzoeksjournalist · persvrijheidsindex 2026
Nederland tweede plaats RSF · Leeuwarder Courant "op de Hoek" vastgoed kort geding ingetrokken

## Geoogst (4 entiteiten #610-613, 6 relaties #1187-1192, 16 argumenten, 13 bronnen #813-825)

Conform de flak-regel (memory): **één relatie per eiser→doelwit**, incidenten en afloop als aparte
argumenten op die relatie; rechterlijk tegenbewijs als `contradicting` op dezelfde edge.

| Relatie (allemaal `flak`, mech juridische_dreiging 10) | rel-id | supporting | contradicting |
|---|---|---|---|
| Pretium → AVROTROS (Radar, 16 zaken) | 1187 | Netkwesties 126 disputen | Hof 2015: art. 10 EVRM, dwangsom (€10k/dag, max €500k) vernietigd (ECLI:NL:GHDHA:2015:3532) |
| Pretium → Peter Olsthoorn (5 zaken) | 1188 | Villamedia: 5 zaken | won 4/5 (hof: geen feitelijke onjuistheden) + HR verwerpt cassatie (ECLI:NL:HR:2019:1044) |
| Pretium → BNNVARA (Kassa, 12 zaken) | 1189 | Netkwesties | — |
| Pretium → De Telegraaf (4 zaken) | 1190 | Kamermotie 2016 (⅔ vóór; VVD/PVV tegen) | — |
| Blijdorp → FD (€150k-bodemprocedure 2023) | 1191 | FPU/MFRR/CASE: SLAPP-kwalificatie | Rb A'dam 2024: kern gestrand, één deelrectificatie |
| Clare Locke → Follow the Money (dreigbrieven 2025) | 1192 | Amnesty: Lensink "regie kwijtraken" | — |

Nieuwe entiteiten: Pretium Telecom #610 (belanghebbende), Willem Blijdorp #611 (belanghebbende),
Clare Locke #612 (belanghebbende, VS-lasterkantoor), Peter Olsthoorn #613 (onderzoeksjournalist).

Losse argumenten op de theorielaag (stance-balans bewust tweezijdig):
- mech 10 **supporting**: PersVeilig 2024 (helft journalisten juridisch bedreigd; herkomst overwegend
  privaat: 54/30/41/>10%) + Leeuwarder Courant-SLAPP (zeven advocaten, ingetrokken kort geding; eiser
  geanonimiseerd → incident als mechanisme-argument, geen edge).
- mech 14 zelfcensuur **supporting**: PersVeilig — kwart vermijdt risico's (6% past aan, 4% ziet af).
- mech 10 **contradicting**: Advocatenblad (7/9 advocaten zien géén toename; 1-2 brieven/maand) +
  NOS/RSF 2026 (NL #2 persvrijheidsindex).
- mech 10 **contextual**: anti-SLAPP-implementatiewet aangenomen juli 2026 (volledige proceskosten
  voor verliezende SLAPP-eiser) — regulering als structurele rem.

Stance-balans r4: 9 supporting, 6 contradicting, 1 contextual.

## Modelleerkeuzes
- "Flak stúúrt de berichtgeving structureel" nergens geclaimd — alleen bestaan/omvang (PersVeilig,
  casussen) en de begrenzing (rechterlijke uitspraken, advocatuur, RSF, wet).
- Datum HR-arrest: 28-06-2019 (rechtspraak.nl authoritatief; Villamedia's "3 mei" is vermoedelijk de
  A-G-conclusie).
- "€500k dwangsom" correct geformuleerd als *maximum* van de vernietigde dwangsom (€10.000/dag).
- PersVeilig-herkomstcijfers exact overgenomen; "bedrijven 41%" apart van "advocaat van bedrijf 38%".

## Negatief / niet ingediend
- **Shell Papers en Chemours**: geen flak (Woo-tegenwerking resp. schikkingsstrategie) — bewust buiten.
- **NL Plan → FtM** (kort geding sept 2025, ECLI:NL:RBAMS:2025:6822, afgewezen): partijnaam alleen via
  niet-gefetchte secundaire bron — geen entiteit aangemaakt; kandidaat voor vervolgronde na verificatie.
- **Uitzendbureau → FtM** (2024, rectificatie geweigerd) en **incassobedrijf → FtM** (RvdJ wijst af,
  2020): eisers geanonimiseerd/te vaag voor een edge; tegenbewijs-strekking zit al in de mechanisme-args.
- **Blijdorp hoger beroep 2024-2026**: niet gevonden — laatste stand is het vonnis + rectificatie.
- **Pretium↔Olsthoorn "LinkedIn-zaak"**: bestaat niet in de bronnen (missie-aanname klopte niet).
- **FPU-woord "minimalistisch"**: staat niet letterlijk op de gefetchte EN-pagina; substantie (alleen
  grensoverschrijdende zaken gedekt) wél hard, maar de wet is inmiddels aangescherpt — alleen de
  actuele stand ingediend.
