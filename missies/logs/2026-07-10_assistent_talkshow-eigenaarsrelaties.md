# Missielog — ontbrekende inkomende eigenaar-edges bij talkshows

**Datum:** 2026-07-10 · **Account:** `assistent` · **Aanleiding:** melding eigenaar: "Nieuws van de Dag mist inkomende eigenaarsrelaties" + "wellicht nog meer talkshows?"

## Audit

Vergeleken met het bestaande patroon (Talpa→Vandaag Inside `eigendom`/`eigendomsconcentratie`; AVROTROS→Buitenhof, NOS→Nieuwsuur, AVROTROS→EenVandaag, WNL→WNL op Zondag `mediaplatform`/`omroepsignatuur`) misten de volgende programma-entiteiten elke inkomende eigenaar-/omroep-edge:

- Nieuws van de Dag (799), HLF8 (679), De Oranjewinter (747) — geen Talpa-edge
- Renze (676), Beau (677), Jinek (681), RTL Late Night (742), RTL Tonight (678) — geen RTL-edge
- Op1 (174) — geen enkele omroep→show-edge (alleen NPO-intekensturing)

## Ingediend (alles `voorgesteld`)

Bronnen 1853–1855, 1866–1871 (+ hergebruik 1734, Talpa-persbericht NvdD). Relaties 1995–2006 met gesourcete supporting-argumenten 3097–3108 (verbatim quotes, web-geverifieerd):

- Talpa Network → NvdD / HLF8 / De Oranjewinter (`eigendom`, eigendomsconcentratie); bronnen: Talpa-persberichten, NOS, FCUpdate
- RTL Nederland → Renze / Beau / Jinek (RTL-periode 2020-01–2023-06) / RTL Late Night / RTL Tonight (`eigendom`, eigendomsconcentratie); bronnen: Mediacourant, NOS
- BNNVARA / EO / MAX / WNL → Op1 (`mediaplatform`, omroepsignatuur), gedateerd per NPO-persbericht 23-12-2019; BNNVARA eruit zomer 2023, Op1 gestopt sept. 2024 (NOS 06-12-2023)

## Bijvangst voor de eigenaar (niet zelf gefixt)

1. **Richting-inconsistentie:** rel. 1258, 1283, 1285, 1288, 1377 lopen show→omroep met mechanisme `omroepsignatuur`, terwijl dat mechanisme ledenomroep→redactie loopt (vgl. Buitenhof/Nieuwsuur die omroep→show staan). Omdraaien = maintainer-werk.
2. **Op1-entiteit (174) mist `active_until`** — Op1 stopte september 2024 (NOS). Entity-patch = maintainer.
3. Webonderzoek-agent voor RTL/Op1 sneuvelde op een sessielimiet; onderzoek daarna inline afgemaakt. Jinek bleek al **januari 2020** (niet 2021) naar RTL — datering gecorrigeerd vóór indienen.
