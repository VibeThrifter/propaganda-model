# Missielog — machtsvalentie: verantwoording-ronde (soort 1)

**Datum:** 2026-07-10 · **Account:** `assistent` (bijdrager) · **Status:** afgerond — zie Uitkomst onderaan

## Doel

De verantwoording-kant van de machtsvalentie-laag vullen: per tegenmacht-mechanisme één
`machtsvalentie`-annotatie `filter:<doel>` (soort 1 — welke filter-machtsconcentratie
checkt dit mechanisme-type). Principe uit het ontwerpgesprek (juli 2026): **verantwoording
is definitioneel → theorielaag** (type-niveau, erft naar instanties zoals `aard`);
opent/sluit blijft casus-niveau en erft niet. *Structuur erf je, effect bewijs je.*

## Ingediend (16 annotaties, contextual roots op mechanismen)

| arg | mech | mechanisme | doel-filter | bron |
|---|---|---|---|---|
| 2944 | 43 | klokkenluider_doorbraak | sourcing | — |
| 2945 | 74 | onderzoeksjournalist_doorbraak | sourcing | 289 (Medialogica toeslagendrama) |
| 2946 | 75 | burgerinitiatief_druk | sourcing | — |
| 2947 | 76 | toezichthouder_interventie | eigendom | 1014 (ACM-voorwaarden DPG–RTL) |
| 2948 | 78 | onafhankelijk_medium_tegenwicht | eigendom | 390 (Correspondent-manifest) |
| 2949 | 79 | vakbond_bescherming | flak | 616 (Persvrijheidsfonds/NVJ) |
| 2950 | 80 | parlementaire_controle | sourcing | 289 |
| 2951 | 85 | onafhankelijkheidsborging | eigendom | 430 (SDM statutaire doelstelling) |
| 2952 | 108 | redactiestatuut_borging | eigendom | 1014 |
| 2953 | 109 | continuiteitsborging | eigendom | 430 |
| 2954 | 110 | afgedwongen_borging | eigendom | 559 (ACM eindmededeling DPG–RTL) |
| 2955 | 114 | projectfinanciering_journalistiek | advertentie | 170 (SvdJ-subsidies) |
| 2956 | 139 | redactieraad_instemming | eigendom | 385 (redactiestatuut Volkskrant) |
| 2957 | 170 | academische_doorlichting | ideologie | 47 (Persbureau in perspectief) |
| 2958 | 172 | ledenraad_zeggenschap | eigendom | 120 (BNNVARA ledenraad) |
| 2959 | 178 | lezersfinanciering_isolatie | advertentie | 2 (Manufacturing Consent) |

Verdeling doelen: eigendom 8 · sourcing 4 · advertentie 2 · flak 1 · ideologie 1.

## Bewust overgeslagen

- **mech. 42 `toezicht_tandeloosheid`** — documenteert het *uitblijven* van
  verantwoording (toezichthouders signaleren maar kunnen/willen niet ingrijpen). Een
  verantwoording-valentie zou onwaar zijn. De annotatie-ronde werkt hier als audit: dit
  mechanisme past niet in de tegenmacht-bak waarin het zit; bij de eventuele
  arena×valentie-herindeling (horizonstap) verdient het een eigen behandeling.

## Werkwijze & poorten

- Sjabloon = bestaande gemergde signalen (contextual root + `property='machtsvalentie'`).
  Aspect-property: telt in geen enkele score, bron niet verplicht (interpretatie/structuur,
  zelfde klasse als `filter`/`mechanism`-classificaties).
- Bronnen: uitsluitend hergebruik van bestaande DB-bronnen mét locator, alléén waar de
  bron de doel-claim inhoudelijk dekt; geen quotes gefabriceerd (citaties zijn kale
  bron-verwijzingen). Waar geen dekkende bron bestond: bronloos ingediend en hier gemeld
  (2944, 2946).
- Alle 16 → HTTP 201, geen duplicaat-409's. Rate limit n.v.t. (`assistent` vrijgesteld).

## Bijbehorende structuurstap (zelfde dag, code)

`tegenmacht.py`: verantwoording-annotaties op een mechanisme **erven** nu naar zijn
niet-vervangen instanties (relatie + bron-actor), geteld als `n_geerfd` naast eigen
`n_annotaties`; opent/sluit erft niet. Test: `scripts/test_machtsvalentie.py`
(`test_overerving_verantwoording`). Viz toont geërfde chips met herkomst-tekst in het
detailpaneel. Effect wordt pas definitief zichtbaar ná menselijke merge van de
annotaties (de viz preview't voorgesteld werk als 'voorlopig', net als de kleurmeter).

## Uitkomst (2026-07-10, "via admin" — besluit eigenaar)

Alle 16 annotaties (2944–2959) op expliciete aanwijzing van de eigenaar ("doe alles via
admin") gemerged met het `maxime`-maintainer-token → status `ongecontroleerd`.
Bijvangst van de afronding: mechanisme 172 (`ledenraad_zeggenschap`) bleek géén
rol-eindpunten te hebben (edge tekende niet in het theoriemodel — vooraf bestaand gat);
via maintainer-PATCH gezet op publiek → ledenomroep, conform eigen beschrijving en het
zusterpatroon `lezersfinanciering_isolatie`. Theoriemodel toont nu Verantwoording (16),
praktijkmodel 51 zichtbaar / 54 totaal (overerving). `validate_model.py --strict` groen.
