# Scout-ronde: ontbrekende personen r3 — resterende prominente hoofdredacteur-gaten

- **Datum:** 2026-07-04
- **Account:** assistent (bijdrager)
- **Git-hash bij aanvang:** de441f1
- **Scope:** hoofdredacteur-gaten bij prominente outlets die al edges hadden maar hun (adjunct-)
  hoofdredacteur misten.
- **Tooling:** `scripts/scout_personen.py` + `data/scout/ronde3.json`. Alles `voorgesteld`.

## Geoogst (3 nieuw — relaties personeel, mechanisme-loze kandidaten)

| Persoon | Outlet | node | bron (verbatim) |
|---|---|---|---|
| Remy Amkreutz (hoofdredacteur) | De Morgen (89) | #508 | Villamedia 2022-03-30 |
| Roland Duong (adjunct-hoofdredacteur) | De Correspondent (13) | #509 | Villamedia 2026-05-29 |
| Lise Straatsma (adjunct-hoofdredacteur) | De Correspondent (13) | #510 | Villamedia 2026-05-29 |

- De Correspondent had **geen** hoofdredacteur-edge; Rob Wijnberg vertrok, de opvolging was in mei 2026
  nog vacant. De twee adjunct-hoofdredacteuren dragen nu de redactie → toegevoegd (rol hoofdredacteur).
- **Rob Wijnberg** (oprichter/oud-hoofdredacteur De Correspondent, ex-NRC.next) is een voor de hand
  liggende volgende toevoeging (ideologische stichter; gedateerde affiliatie met active_until, mogelijk
  draaideur NRC→De Correspondent). Bewust nog niet ingediend — makkelijke follow-up.

## Bevinding: de grote outlets zijn intussen grotendeels gedekt
Andere bijdragers hebben tijdens deze klus de huidige hoofdredacteur van de meeste nationale titels al
toegevoegd (AD→Rijpma, de Volkskrant→Klok, NRC→Veldhuis, Trouw→Boersema, NOS→Van Cann, De Telegraaf→
Ullah/Wemmers, FD→Feenstra, FTM→Lensink, Metro→De Boer, RTL Nieuws→Van der Linden). De grootste
node-gaten zaten dus bij de kleinere/onafhankelijke titels (r1) en de stichtingen/fondsen (r2).

## Verificatie (hele klus)
- `scripts/validate_model.py --strict`: **geen fouten boven de baseline**, golden snapshot groen, exit 0.
- Owner (`maxime`) keurde tijdens de run al goed: r2-nodes #501–507 → `goedgekeurd`; diverse argumenten
  gemerged (`ongecontroleerd`). r1/r3 wachten nog op review.

## Overgeslagen / gedeferreerd
- Persbureaus Reuters/AP/AFP/Novum: internationaal, geen zinvolle NL-hoofdredactie-node zonder gerichte
  bron. Publieke omroepverenigingen (BNNVARA/KRO-NCRV/AVROTROS/NTR/EO/WNL/PowNed): "hoofdredacteur" is
  minder eenduidig (nieuws loopt via NOS); eerder directeuren — aparte gerichte ronde.
- Notabele journalisten/columnisten per outlet (de tweede helft van de opdracht): grotere, fuzzier
  laag; op verzoek als volgende fase.
