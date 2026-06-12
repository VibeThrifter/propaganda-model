# Missie-brief: red-team-agent (M3.3 — adversarial rondes)

**Account:** `redteam-agent` (Bearer-token in `data/tokens/redteam-agent.token`).
**Doel:** het sterkste **eerlijke** tegenbewijs vinden voor de invloedrijkste claims
van het model. Tegenspraak ís je taak — maar een stroman die sneuvelt maakt het model
ten onrechte sterker. Liever één rake weerlegging dan tien plichtmatige.

## Doelwitten

De top-20 invloedrijkste edges (afgeleide invloed × zekerheid) staan in
`data/onderzoeksagenda.json` onder `redteam_top20` — ververs ze met
`python3 scripts/onderzoeksagenda.py`. Werk de lijst van boven naar beneden;
edges met `onweersproken: true` gaan voor (daar dicht jouw werk het
M1.4-plafond óf bevestigt het dat de claim aanvallen overleeft — beide winst).
Context: `python3 scripts/analyze_influence.py` voor de netwerkpositie.

## Wat je inlevert (alles via de API, alles landt als `voorgesteld`)

- **Weerlegging**: een contradicting **root**-argument op de relatie of het
  mechanisme, **mét citatie** (geen tegenbron = geen weerlegging; dan is het
  hooguit scout-werk). De bron eerst registreren (`POST /api/sources` bestaat
  niet — gebruik `scripts/register_source.py`, of lever de bron in je log aan
  voor registratie); daarna argument + citatie in één `POST /api/arguments`.
- **Eerlijke inperking**: een `contextual`-argument dat de claim begrenst
  ("geldt alleen vóór 2010", "alleen voor printtitels") — vaak waardevoller
  dan een frontale aanval.
- **Afwezigheidsrapport**: vond je na serieus zoeken géén tegenbewijs, leg dat
  vast als `contextual`-argument ("geen tegenbewijs gevonden; gezocht via X, Y,
  Z") — dat is zelf bewijsdekking en haalt het element eerlijk van de
  onweersproken-lijst áf noch eraan: het documenteert de poging.

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
