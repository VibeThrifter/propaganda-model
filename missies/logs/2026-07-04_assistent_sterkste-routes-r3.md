# Scout-ronde: sterkste routes r3 — talkshow-/expertecosysteem (Sourcing)

- **Datum:** 2026-07-04 · **Account:** assistent · **Git-hash:** de441f1
- **Opdracht:** eigenaar — "100 relaties/entiteiten langs de sterkste routes"; dit is het
  talkshow-deel van de Sourcing-route (smalle expertpool als 'primary definers' op tv).
- **Tooling:** `scripts/scout_indienen.py` + `data/scout/sterkste-routes-r3.json`.

## Queries (letterlijk, research-agent — 20 stuks)
NRC onderzoek talkshowgasten 2021 gesloten ecosysteem 1300 gasten zeven talkshows · meest gevraagde
talkshowgast corona Gommers Op1 Jinek telling 2020 · NRC "talkshows" coronajaar gasten geteld
journalisten 310 experts · nrc.nl artikel talkshows 2021 "wie er aanschoven" OF "talkshowtafel"
gasten onderzoek corona · "Sven Kockelmann" 54 keer talkshow NRC gast coronajaar · Diederik Gommers
Marion Koopmans meest gevraagde talkshowgasten telling optredens Op1 Jinek Beau 2020 2021 ·
OMT-leden Van Dissel voorzitter Gommers Koopmans Outbreak Management Team samenstelling RIVM ·
Ab Osterhaus viroloog hoogleraar Erasmus MC emeritus affiliatie Op1 vaste gast corona · Jaap van
Dissel talkshows Op1 Nieuwsuur optredens weigert talkshow RIVM briefing · Rob de Wijk HCSS vaste
duider talkshow Oekraïne "geopolitiek" tv-optredens · Mart de Kruif ex-generaal vaste tafelgast
Oekraïne duiding talkshow Op1 Beau · talkshows oorlog Oekraïne 2022 oud-generaals militaire duiders
"altijd dezelfde" analyse tv-experts · "Rob de Wijk" "vaste gast" OR "veelgevraagd" talkshow
Nieuwsuur Op1 Goedemorgen Nederland commentator · "Peter Wijninga" HCSS defensiespecialist tv duider
talkshow Oekraïne analist · "Victor Vlam" OF "Willem Post" Amerika-deskundige vaste gast tv talkshow
Amerikaanse verkiezingen duider · "Ko Colijn" defensiespecialist Clingendael Nieuwsuur NOVA vaste
commentator jarenlang · "Danny Pronk" Clingendael duider tv talkshow Nieuwsuur Oekraïne
veiligheidsexpert · site:nrc.nl talkshows gasten coronajaar onderzoek 2021 journalisten aanschuiven ·
NRC maart 2021 artikel talkshows "een jaar corona" gasten tafel onderzoek Erasmus mannen journalisten
titel · "Raymond Mens" Amerikadeskundige vaste duider WNL talkshow historicus commentator

## Geoogst (7 entiteiten #603-609, 17 relaties #1170-1186, 26 argumenten, 15 bronnen #798-812)

| Persoon | node | Affiliatie/OMT | Talkshow-anker (m87) |
|---|---|---|---|
| Diederik Gommers | #603 | Erasmus MC (1170), OMT (1171) | Op1 (1172), Nieuwsuur (1173) |
| Marion Koopmans | #604 | Erasmus MC (1174), OMT (1175) | Op1 (1176) |
| Ab Osterhaus | #605 | Erasmus MC tot 2013 (1177) | Op1, 33 afl. — vaakst aangeschoven expert (1178) |
| Jaap van Dissel | #606 | RIVM (1179), OMT-voorzitter (1180) | **géén** — weigerde talkshows (contextual arg op 1180) |
| Mart de Kruif | #607 | (generaal b.d., geen instituut) | Pauw & De Wit 8× in H1-2026 (1181), Eva (1182) |
| Peter Wijninga | #608 | HCSS (1183) | Nieuwsuur e.a. — "weinig omroepen waar ik dit jaar niet ben geweest" (1184) |
| Raymond Mens | #609 | (zelfstandig) | Vandaag Inside, vaste gast sinds 2022 (1185) |
| Rob de Wijk (bestond, #62) | — | — | Pauw & De Wit, 7× H1-2026 (1186) |

Losse argumenten theorielaag:
- mech 161 mediageniekheidsselectie ×3: gastengroepen-telling (310/258/184/159, Villamedia/EUR),
  Kockelmann 54× + top-10 één vrouw (ANP/nieuws.nl), "gesloten ecosysteem" (Joop, **opinie**-klasse).
- mech 124 omroepsignatuur: politieke kleur gasten volgt omroep (EUR: BNNVARA ⅔ links, WNL-Op1 31% VVD).
- entiteit 383 Erasmus MC: virologen domineerden talkshows (Erasmus Magazine).
- entiteit 44 HCSS: HCSS-deskundigen kleuren de Oekraïne-duiding; Clingendael veel minder zichtbaar (AD).

## Modelleerkeuzes
- Expert→talkshow = `expert_legitimatie` (87); expert→instituut = mechanisme-loze kandidaat;
  OMT-lidmaatschap = `lidmaatschap`-kandidaat (Van Dissel `bestuurder` als voorzitter).
- **Van Dissel bewust zonder talkshow-edge**: hij weigerde structureel (Villamedia) — dat contrast
  is als `contextual` duiding op rel 1180 vastgelegd, niet als m87-edge verzonnen.
- "Gesloten ecosysteem"-typering hangt aan de juiste bron: het Joop-opiniestuk (2025) over het
  NRC-spreektijdonderzoek, klasse-voorstel `opinie` — niet aan de 2021-telling toegeschreven.
- TVblik/robdewijk.nl (uitzenddossiers, zelfrapportage) klasse-voorstel `grijs`; frequentieclaims
  daaruit met locator, alleen de Eva-aankondiging als quote.

## Negatief / niet ingediend
- **Jaap van Dissel als talkshowgast: weerlegd** (weigerde structureel) — alleen contextual arg.
- **Ko Colijn** (TVblik stopt 2015) en **Danny Pronk** (geen frequentie-signaal): geen bewijs van
  vaste rol 2022-2026 — niet opgenomen.
- **Willem Post**: enige bron is een sprekersbureau-bio (zelfpresentatie) — te zwak; wél interessant
  historisch ijkpunt (eerste vaste tv-Amerikadeskundige, 1996) voor een vervolgronde.
- **Victor Vlam**: Wikipedia zegt "bekend van optredens" maar niet "vaste gast" — onder de lat.
- **~1.300-gasten-totaal**: in geen bereikbare bron verbatim — alleen de deeltellingen gebruikt.
- **NRC-originelen** (2021-telling, 2025-spreektijd): paywall — gedekt via Villamedia/ANP/EUR/Joop.
- **Bijvangst voor vervolgronde**: Jan Kluytmans (OMT-lid, regelmatig te gast — Villamedia);
  Han ten Broeke (HCSS politiek directeur, ex-VVD — draaideur-signaal, eigen tv-frequentie niet los
  onderbouwd); Bob Deen (Clingendael, medium bewijs).
