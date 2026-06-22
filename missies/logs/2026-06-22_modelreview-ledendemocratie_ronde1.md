# Modelreview ledendemocratie — missie-ronde 1

- **Datum:** 2026-06-22
- **Account:** `modelreview-ledendemocratie-2026-06` (bijdrager, agent; provenance `claude-opus-4-8`)
- **Contract:** `CLAUDE.md` (dogfood-regel + agent-contract) @ git `0cb647383b6270ac2ebccf3bd2417ed8506ea639`
- **Doel:** een gat in de **theorielaag** dichten dat in gesprek naar voren kwam — de
  ledenraad van een omroepvereniging als interne, van onderaf gekozen tegenmacht over de
  eigen omroeptop. Vergelijking ledenraad (omroep) vs. raad van bestuur (NPO) liet zien
  dat de top-down kant goed gedekt is, de bottom-up ledendemocratie niet.

## Bevinding (vóór indienen)

De NPO-sturing zit er goed in: rol `omroepkoepel` (46) + mechanismen `bestelsturing` (98),
`intekensturing` (122), `erkenningverlening` (123), `politieke_benoeming_omroeptop` (99).
De **ledenraad als bestuurlijk/tegenmacht-orgaan ontbreekt**: leden komen alleen voor als
kwantitatieve drempel (`ledeneis` 121, eigendom) en als zuil-identiteit (`omroepverzuiling`
100 / `omroepsignatuur` 124, ideologie). Veelzeggende asymmetrie: het personeels-equivalent
bestaat wél als tegenmacht (`redactieraad_instemming` 139), het leden-equivalent niet.

## Neutrale missievraag

"Welke statutaire bevoegdheden heeft de ledenraad van een Nederlandse omroepvereniging —
stelt die de begroting/jaarrekening vast en benoemt/controleert die het bestuur en de raad
van toezicht?" — geen modelclaim ingebakken.

## Queries + bronnen (web, 2026-06-22)

- WebSearch: ledenraad omroepvereniging statuten begroting jaarrekening RvT benoemen BNNVARA
- WebSearch: KRO-NCRV ledenraad bevoegdheden statuten verenigingsraad vaststellen jaarrekening
- WebFetch: `kro-ncrv.nl/raad-van-toezicht` → "De Ledenraad benoemt de leden van de Raad van
  Toezicht"; ledenraad stelt jaarrekening + bestuursverslag en strategisch beleidsplan vast.
- WebFetch: statuten-PDF KRO-NCRV (per 30-12-2024) → ledenraad = hoogste orgaan; stelt
  jaarrekening/bestuursverslag, jaarplan met begroting en beleidsplan vast; benoemt/schorst/
  ontslaat de RvT. (Reviewer verifieert de exacte artikelnummers.)
- WebFetch: `bnnvara.nl/leden/de-vereniging` → ledenraad "adviseert en controleert het
  bestuur"; bespreekt jaarrekening/-verslag, programmabeleid en jaarplan met begroting.
- `kro-ncrv.nl/ledenraad` → HTTP 403 (niet gebruikt).

## Bijdragen via de API (alles `voorgesteld` / adviserend; mens beslist)

- **Bron 119** geregistreerd: "Statuten KRO-NCRV (doorlopende tekst per 30-12-2024)",
  type `overig`, url-locator; classificatie-voorstel `primair` / `nl_systeem` (adviserend —
  reviewer bevestigt via `PATCH /api/sources/119/classificatie`).
- **Bron 120** geregistreerd: "BNNVARA — De vereniging", type `website`, url-locator;
  classificatie-voorstel `institutioneel` / `nl_systeem`.
- **RfC #12** ingediend (`POST /api/voorstellen`, soort `nieuw_theorie_element`):
  nieuw **mechanisme `ledenraad_zeggenschap`**, filter `tegenmacht`, aard `direct`.
  Sjabloon compleet: definitie, effect, afgrenzing (vs. 121/100/124/139/98/99/80/76),
  falsificatiecriterium, freeze-test (→ direct), 3 instantiaties (KRO-NCRV, BNNVARA,
  generalisatie), 3 bronnen. `benodigde_akkoorden: 2` (twee menselijke reviewers, indiener
  uitgesloten).

## Open vervolg (ná aanname)

De **praktijk-encodering** (een entiteit `ledenraad` of een entity_role op de omroep + de
relatie ledenraad → bestuur/RvT) is bewust niet meegenomen: dat loopt via het verbinder-pad
zodra het theorie-element is aangenomen. Ook open: verdient de ledenraad een eigen **rol**
naast `ledenomroep` (47)? — apart te bespreken, niet in deze RfC gebundeld.
