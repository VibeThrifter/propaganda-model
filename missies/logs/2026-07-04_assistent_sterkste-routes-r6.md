# Scout-ronde: sterkste routes r6 — lobby & draaideur (Sourcing-aanvulling)

- **Datum:** 2026-07-04 · **Account:** assistent · **Git-hash:** de441f1
- **Scope:** verse draaideur-casussen politiek→lobby (2018-2026), de systemische 44%-claim, GRECO,
  en het verplichte tegenwicht (Van Os, Uber Files, de nieuwe wet). Alleen structurele feiten —
  nergens "lobby stuurt de nieuwsinhoud" (dat is per het onderzoek dun/deels weerlegd).
- **Tooling:** `scripts/scout_indienen.py` + `data/scout/sterkste-routes-r6.json`.

## Queries (research-agent — 29 stuks, verkort)
HUMAN Mediastorm "Lobbypraktijken" Eline Huisman Jack de Vries talkshow · TI-NL "Lifting the lid on
lobbying" 44% · Stientje van Veldhoven World Resources Institute · GRECO vijfde evaluatieronde
Nederland lobbyregister afkoelperiode · Halbe Zijlstra VolkerWessels · Sander Dekker nieuwe baan ·
Menno Snel NOGEPA Element NL · Raymond Knops NIDV · NOS Van Veldhoven kritiek Kamervragen · Pieter
van Os "In de oorschelp van het Binnenhof" · Uber Files Investico Trouw FD Neelie Kroes · Wet regels
gewezen bewindspersonen stand 2025 · Grapperhaus advocaat 2022 · Arno Rutte VIG · Helma Lodders
voorzitter branchevereniging · oud-bewindslieden voorzitter branchevereniging 2024 2025 · Ank
Bijleveld · Van der Maat · verplicht lobbyregister kabinet 2025 2026 · GRECO fifth round evaluation
revolving doors · Kamervragen Van Veldhoven subsidie · Jack de Vries talkshow "politieke duiding" ·
coalitieakkoord 2026 lobbyregister · "Jack de Vries" DWDD · Dennis Wiersma · Van der Maat Platform
Spoorgoederenvervoer · Bruno Bruins na aftreden · Melanie Schultz · Mark Harbers 2024 2025

## Geoogst (13 entiteiten #616-628, 8 relaties #1198-1205, 14 argumenten, 14 bronnen)

| Draaideur (mech 94) | rel-id | bron |
|---|---|---|
| Menno Snel → Element NL/NOGEPA (2021-2023) | 1198 | NOS 2021 |
| ~~Knops → NIDV~~ — **bestond al** (dedup-skip) | — | — |
| Van Veldhoven → World Resources Institute (2021-2026; terug als minister 2026) | 1199 | TTM + ANP/Barendrechts |
| Min. I&W → WRI (financiering €1,7 mln, mech 52) | 1200 | ANP/Barendrechts |
| Lodders → VNLOK (2021, was Kamerlid-kansspelen) | 1201 | Joop |
| Bruins (#180) → ABU (2026) | 1202 | Skipr |
| Harbers → Techniek Nederland (2025) | 1203 | Industrielinqs |
| Zijlstra → VolkerWessels (2018) | 1204 | Oost NL |
| Jack de Vries (#110) → BNNVARA (talkshowduiding zonder lobbyvermelding, mech 87) | 1205 | HUMAN/Mediastorm |

Losse argumenten theorielaag:
- mech 94 **supporting**: TI-NL 44% ex-bewindslieden wordt lobbyist + GRECO-aanbeveling 2019.
- mech 94 **contradicting**: Wet regels vervolgfuncties bewindspersonen (lobby-/draaideurverbod 2 jr,
  in werking feb 2026) — regulering als structurele rem.
- mech 56 **contradicting**: Van Os (De Groene) — Binnenhof is "kil", niet "klef"; tegenwicht op het
  symbiose-frame.
- mech 74 **supporting** (tegenmacht, tweezijdige oogstplicht): Uber Files — NL-onderzoeksmedia
  onthulden zelf de Kroes/Uber-lobby.

Stance-balans r6: 11 supporting, 3 contradicting.

## Modelleerkeuzes
- Persoon→org-affiliaties, gedateerd; de org↔org-brug (bv. D66↔WRI via Van Veldhoven + partijbinding)
  is afgeleid, nooit opgeslagen (litmus).
- Zijlstra→VolkerWessels kreeg m94; **m93 (draaideur_politiek_bedrijfsleven) past mogelijk beter**
  (VolkerWessels is bedrijf, geen lobbygroep) — reviewer mag verhangen.
- Van Veldhoven: de terugkeer-2026 (minister Klimaat en Groene Groei) zit in beschrijving/argument;
  geen eigen edge (dat ministerie is geen entiteit).

## Negatief / niet ingediend
- **Sander Dekker, Ank Bijleveld, Melanie Schultz, Arno Rutte→VIG:** géén lobbyfunctie gevonden.
- **Grapperhaus→Deloitte Legal, Wiersma→Galan Groep, Van der Maat→spoorplatform:** vervolgfuncties,
  geen belangenbehartiging — buiten scope gehouden.
- **Coalitieakkoord-passage lobbyregister:** PDF niet tekstueel leesbaar; alleen via TI-NL-reactie —
  niet als eigen claim ingediend.
- **DWDD-afleveringen Jack de Vries:** gastenarchief bewijst tafelgast-zijn, geen data/frequentie —
  claim op HUMAN-quote gehouden, BNNVARA als omroep-target.
- **FtM-draaideuroverzicht 2015** (Zalm, Wijn, Atsma, Schouw, Verhagen, Klink): historisch —
  de drie sterkste gevallen volgen in r7.
