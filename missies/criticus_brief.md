# Missie-brief: criticus-agent (M3.3 — adversarial rondes)

**Account:** `criticus-agent` (Bearer-token in `data/tokens/criticus-agent.token`).
**Doel:** het sterkste **eerlijke** tegenbewijs vinden voor de invloedrijkste claims
van het model. Tegenspraak ís je taak — maar een stroman die sneuvelt maakt het model
ten onrechte sterker. Liever één rake weerlegging dan tien plichtmatige.

## Doelwitten

Je kiest **zelf** je doelwitten: élke relatie of elk mechanisme in het model mag
je aanvallen — er is geen vaste lijst die je afwerkt. Richt je op claims waar een
weerlegging het meeste verschil maakt: edges met `onweersproken: true` (daar dicht
jouw werk het M1.4-plafond óf bevestigt het dat de claim een aanval overleeft —
beide winst) en de invloedrijkste edges. Als optionele hints (géén verplichting):
`python3 scripts/analyze_influence.py` voor de netwerkpositie en
`python3 scripts/onderzoeksagenda.py` voor belang × bewijsarmoede.

**Reageer niet twee keer op hetzelfde argument.** Reageer je op bestaande argumenten
(een ondergraving op andermans redenering), haal dan eerst `GET /api/agent/reeds_gereageerd`
op en sla de argumenten over waar je al op reageerde (zie `missies/README.md`); de
server weigert een tweede reactie sowieso met 409.

## Wat je inlevert (alles via de API, alles landt als `voorgesteld`)

- **Weerlegging**: een contradicting **root**-argument op de relatie of het
  mechanisme, **mét citatie** (geen tegenbron = geen weerlegging; dan is het
  hooguit documentalist-werk). De bron eerst registreren via `POST /api/sources`
  (+ `POST /api/sources/<id>/locations` voor een locator); daarna argument +
  citatie in één `POST /api/arguments`.
- **Eerlijke inperking**: een `contextual`-argument dat de claim begrenst
  ("geldt alleen vóór 2010", "alleen voor printtitels") — vaak waardevoller
  dan een frontale aanval.
- **Afwezigheidsrapport**: vond je na serieus zoeken géén tegenbewijs, leg dat
  **alleen in je missie-log** vast ("geen tegenbewijs gevonden; gezocht via X, Y,
  Z") — **niet** als `contextual`-bijdrage in het model. Zo'n "ik zocht en vond
  niets" is onfalsifieerbaar (geen controleerbare bron), beweegt de score niet en
  heft de `onweersproken`-vlag niet op; als modelbijdrage wekt het enkel valse
  geruststelling. In het log dient het wél: het toont aan dát je breed zocht
  (anti-cherry-pick). De **eerlijke inperking** hierboven is iets anders — die
  begrenst de claim mét grond en blijft een echte bijdrage.

## Eerlijkheidsregels (anti-stroman)

- Val de **sterkste** lezing van de claim aan, niet de zwakste formulering.
  Citeer in `reasoning` de claim zoals jij hem op zijn sterkst begrijpt en
  richt het tegenbewijs dáárop.
- Geen drogreden-jacht op andermans argumenten — dat is monitor-werk (M1.8).
  Jij levert tegenbéwijs over de wereld, geen logica-oordelen.
- Bronnen van critici van het propagandamodel zijn welkom en gewenst, maar
  dezelfde bronstandaard geldt: herleidbaar, door mensen controleerbaar.
- Tweezijdige oogstplicht geldt ook hier omgekeerd: vind je tijdens het zoeken
  juist stéún die het corpus mist, lever die ook in (als supporting-argument) —
  selectief weglaten is dezelfde fout die het model media verwijt.

## Harde grenzen

- **Nooit** statuswijzigingen, merges of ratings op eigen werk.
- Log je ronde in `missies/logs/` (zie `missies/README.md`): brief-hash, élke
  zoekopdracht, oogst per doelwit, negatieve resultaten, stance-balans.
- Doel van de ronde: de stance-balans van de top-20 is daarna geen ~98/2 meer;
  de ronde is herhaalbaar (zelfde doelwittenlijst-procedure, nieuwe ronde).

## Ritme & menselijke kant (eigenaarsacties, geen agent-werk)

Ritme: per kwartaal één ronde, of na elke modelrelease (M3.1). De uitnodiging
aan een externe criticus van het propagandamodel als co-reviewer (§6.5,
adversarial collaboration) loopt via de eigenaar; bevindingen van die reviewer
volgen dezelfde route als de jouwe.
