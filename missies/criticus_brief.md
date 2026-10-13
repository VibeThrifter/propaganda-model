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

## Eigen stem en specificiteit (eigenaarsbesluit 2026-10-08)

"'Ondermijnt zo het vertrouwen in de journalistiek' … deze taal moeten we niet overnemen, dit is
duidelijk een politiek spelletje … waak hier streng voor"; "PVV censureert AD … niet van belang".
Voor alles wat je als bewering (claim), beschrijving of herformulering indient:

- **Eigen stem = wat er gebeurde**: wie deed of zei wat, wanneer, waar, in welke functie. Geen
  oordeel over gevolgen of motieven ("ondermijnt het vertrouwen", "bedreiging voor de
  persvrijheid", "om journalisten te intimideren"), geen etiket ("rechts-populistisch",
  "extreemrechts", "linkse media", "mainstream", "neoliberale consensus", "omstreden") en geen
  retoriek van één kant. Zo'n oordeel alleen als citaat, met de naam van wie het uitsprak ("De
  NVJ noemde de uitspraak …"). De stemtoets (`scripts/stemtoets.py`, account `stemtoets`) toetst
  elk voorstel; wat niet neutraal is, merget niet en komt in neutrale vorm opnieuw binnen.
- **Over dát verband**: een argument over een verband noemt beide partijen, en de bron ook. Een
  uitspraak over "de pers", "journalisten" of "de media" draagt geen verband met één genoemd
  medium; de bronchecker (v3) zegt dan `klopt-niet` ("gaat niet over …").
- **Eén feit per argument**: een bestuursfunctie en een kandidatuur zijn twee argumenten, elk met
  een eigen bron die dát feit draagt. Een feit over een ánder verband hoort bij dat verband.

## Looptijd: zonder jaartal geen verband (eigenaarsbesluit 2026-10-09)

Elk verband dat je indient of onderbouwt, krijgt zijn looptijd: begin (`active_from`) en, als het
voorbij is, einde (`active_until`), zo precies als de bron geeft (`JJJJ`, `JJJJ-MM`, `JJJJ-MM-DD`),
met een citaat dat het jaartal noemt. Het begin van dít verband (benoeming, toetreding), niet de
oprichting van de organisatie of de datum van het artikel. Vind je het echt niet: zeg waar je
zocht (`zonder_jaar`) of laat het verband weg — nooit een geraden jaartal; de datumzoeker zoekt
verder. Een datum bij een bestaand verband: een aspect-argument (`property` `active_from`/
`active_until`, `property_value` de datum). Zie missies/README.md § Looptijd.

## Harde grenzen

- **Nooit** statuswijzigingen, merges of ratings op eigen werk.
- Log je ronde in `missies/logs/` (zie `missies/README.md`): brief-hash, élke
  zoekopdracht, oogst per doelwit, negatieve resultaten, stance-balans.
- Doel van de ronde: de stance-balans van de top-20 is daarna geen ~98/2 meer;
  de ronde is herhaalbaar (zelfde doelwittenlijst-procedure, nieuwe ronde).

## Cadans (onbewaakt, C1)

Deze missie draait onbewaakt op een vaste cadans — **per kwartaal** (8 jan/apr/jul/okt),
of na een modelrelease (M3.1) — via de scheduler (`scripts/agent_runner.py`;
`deploy/systemd/agent-criticus.{service,timer}` en `deploy/crontab`). De runner start
één headless `claude`-sessie onder `criticus-agent`, injecteert de voorregel (eerst
`GET /api/agent/reeds_gereageerd`, sla die id's over) en tee't de ronde naar
`missies/logs/`.

**Exit-condities.** Lege oogst (na serieus zoeken géén eerlijk tegenbewijs) →
afwezigheidsrapport in het log, nooit als `contextual` modelknoop. Rate-limit **429** →
ronde stoppen en loggen, niet herproberen.

**Logging-plicht per ronde.** `missies/logs/YYYY-MM-DD_criticus-agent_<ronde>.md` met
de brief-blob-hash, élke zoekopdracht, de oogst per doelwit, de negatieve resultaten en
de stance-balans; de runner voegt exit-code/duur/oogst als footer toe (C4-toezicht).
Doel: de stance-balans van de top-20 is daarna geen ~98/2 meer; de ronde is
herhaalbaar. Alles blijft `voorgesteld`, eigen token, geen statuswijzigingen.

## Menselijke kant (eigenaarsactie, geen agent-werk)

De uitnodiging aan een externe criticus van het propagandamodel als co-reviewer (§6.5,
adversarial collaboration) loopt via de eigenaar; bevindingen van die reviewer volgen
dezelfde route als de jouwe.
