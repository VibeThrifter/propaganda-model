# Ronde 11 — politici koppelen aan hun partij (assistent)

**Datum:** 2026-07-03 · **Account:** assistent (bijdrager) · alles `voorgesteld`.
**Aanleiding eigenaar:** "politici zoals Kajsa Ollongren moeten ook een connectie
hebben met hun partij, natuurlijk."

## Bevinding vooraf
Ollongren heeft die connectie al: rel 493 (`personeel → D66`, mech 92). Van de ~34
persoon-entiteiten met primaire rol *politicus* bleken er slechts **vijf** met NUL
partij-edge — de rest zat al gekoppeld (vaak uit eerdere rondes). Die vijf zijn
gevuld; niets bijverzonnen.

## Mechanisme & vorm
Relatietype `lidmaatschap`, richting persoon→partij (zoals Ollongrens eigen edge),
mechanisme **92 (partijlijn, partij↔politicus)**. Elke edge draagt een supporting
root-argument met verbatim citaat uit de **parlement.com**-biografie (Parlementair
Documentatie Centrum, Universiteit Leiden) — zelf geverifieerd 2026-07-03, **geen
Wikipedia**.

## Ingediend — 1 entiteit, 5 relaties, 5 argumenten
Nieuwe entiteit: **ChristenUnie (379)** — partij (rol 45), was nog niet in het model.

| Rel | Persoon | Partij | Bron-quote (verbatim) |
|-----|---------|--------|------------------------|
| 856 | Ernst Kuipers (167) | D66 (152) | "Ernst Kuipers is lid van D66." |
| 857 | Frank Heemskerk (115) | PvdA (56) | "Uit het bankwezen afkomstige PvdA-politicus (een krant betitelde hem als 'rode bankier')" |
| 858 | Jet Bussemaker (168) | PvdA (56) | "Getalenteerde, nogal serieuze PvdA-politica … al snel een prominent Tweede Kamerlid werd." |
| 859 | Gert-Jan Segers (225) | ChristenUnie (379) | "Tweede Kamerlid voor de ChristenUnie en van 10 november 2015 tot 17 januari 2023 fractievoorzitter en politiek leider" |
| 860 | Jack de Vries (110) | CDA (54) | "CDA-politicus die als voorlichter en persoonlijk assistent van Jan Peter Balkenende …" |

Bronnen #584–588 (parlement.com-biografieën). Argumenten #1286–1290.

## Opmerkingen
- **Modelconsistentie (voor de eigenaar).** De bestaande politicus↔partij-edges zijn
  qua *relatietype* niet uniform: sommige zijn `lidmaatschap` (Omtzigt), andere
  `personeel` (Ollongren, Kroes, Bos, Balkenende — met mech 92). Ik heb voor de nieuwe
  vijf `lidmaatschap` gekozen (accurater: een minister is geen partij-*personeel*).
  Géén bestaande edges aangeraakt — dat is admin/opruimwerk, niet gevraagd.
- **Borderline overwogen, niet ingediend:** Afke Schaart heeft al een VVD-edge (rel
  356). Karel Beckman / Willem Oltmans / Harold Rimmelzwaan / Maike Olij zijn geen
  partijpolitici (journalist/overig) → géén partij-edge.
- Alles staat `voorgesteld`; wacht op review (mens / `via admin`).
