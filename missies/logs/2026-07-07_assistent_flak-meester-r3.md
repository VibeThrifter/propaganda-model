# Missielog — flak op Ronald Meester (oversterfte-hypothese), ronde 3

- **Datum:** 2026-07-07 · **Account:** `assistent` (bijdrager) · alles `voorgesteld`
- **Aanleiding (eigenaar):** het opwerpen van de oversterfte-hypothese is legitiem; onevenredige persoonsgerichte
  flak daarop is establishment-flak — los van of de specifieke methode standhield ([[flak-betwist-doelwit-neutraal-confound]]).

## Bijstelling t.o.v. r2

In r2 liet ik Meester vallen omdat (a) zijn zuivere modelkritiek serieus werd behandeld en (b) de Keulemans-quotes
op X een HTTP 402 gaven. Op aanwijzing van de eigenaar herzien: de flak op de **oversterfte-tak** is juist de
relevante establishment-flak. Verificatie alsnog gelukt: de tweettekst staat **verbatim in de zoekindex** (X-directe
fetch blijft 402). Kloptdatwel bestempelt Meester expliciet **niet** als "antivax" — die engageren de méthode; dat is
dus de zuivere confound, de "Antivaxman"-labeling van Keulemans is de flak.

## Ingediend (`voorgesteld`)

- Entiteiten #803 **Ronald Meester** (persoon, gezagsexpert), #804 **Maarten Keulemans** (persoon, journalist).
- Bronnen #1171–1173 (2 Keulemans-tweets, `grijs`; Kloptdatwel, `opinie`).
- **rel #1475 Maarten Keulemans → Ronald Meester** (etikettering, mech 13):
  - supporting #2169: "Antivaxman Ronald Meester heeft z'n trusted medium @mariannezw en @rickvanv opgetrommeld ivm z'n nieuwe rapport, over oversterfte en vaccins."
  - supporting #2170: "Lang verhaal kort: stuk zit vol fouten, verdraaiingen en mallotige aannames."
  - confound #2171 (Kloptdatwel, compensatie-aanname): inhoudelijke methodekritiek zónder "antivax"-label = legitiem debat.

## Verificatie

`validate_model.py --strict` → **EXIT 0**. Attacker gemodelleerd als de persoon Keulemans (het zijn zijn tweets),
met in de beschrijving zijn de-Volkskrant-functie zodat het establishment-media-karakter legibel blijft.
