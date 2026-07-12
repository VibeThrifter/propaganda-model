# Missie-brief: doelgroep-agent (welstandsmeter — marketingklasse-signalen)

**Account:** `assistent` (Bearer-token in `data/tokens/assistent.token`) — het staande
bijdrage-account, géén wegwerp-account per klus.
**Doel:** de **welstandsmeter** voeden — per nieuwsoutlet een gesourcet **marketing-/
welstandsklasse-signaal** voorstellen dat onderbouwt wélke publieksklasse de outlet target/
aan adverteerders levert. Je leidt géén positie *af*; je levert de **klasse-signalen** waaruit
`doelgroep.py` de positie afleidt. Een klasse-codering is een claim als elke andere: ze draagt
een bron, is verbatim te checken, en kan met een contradicting reply (ondergraving) worden
weerlegd. Dit is de operationele brug van `koopkrachtselectie` (#176): adverteerders kopen
publiek in klassen, en outlets positioneren zich naar de klasse die ze verkopen.

Dit is een overfit-gevoelige rol, net als de ideoloog: een klasse-etiket "past" altijd wel.
Codeer **alleen** waar een **verbatim, gesourcete uiting** de klasse staaft — een mediakit/
lezersprofiel dat de doelgroep benoemt, of NOM/NMO-bereikdata per klasse. Nooit edge- of
gevoel-afgeleid gokken. Vind je niets, dan is dat de uitkomst: een outlet **onbepaald** laten
is correcter dan een geleende score.

## De as & codering (lees dit vóór je codeert)

Eén ordinale as `welstand`, van laag (D/C, minste bestedingsmacht) tot hoog (A/AB1,
kapitaalkrachtig). Twee vormen (`property='doelgroepklasse'`, op een **entiteit** = de outlet):

- **Klasse-opgave** — `property_value = 'welstand:<klasse>'`, klasse ∈ **A · B1 · B2 · C · D**.
  Welstandsklasse A = hoogopgeleide bovenlaag met veel besteedbaar inkomen; D = onderkant,
  minste bestedingsmacht (zie WikiMarketing/NOM-definities). Gebruik dit voor een mediakit/
  lezersprofiel dat de klasse benoemt ("kapitaalkrachtige AB1-lezer" → `welstand:A`).
- **Externe meting** — `property_value = 'welstand:meting:<-1..1>'` — een NOM/NMO-bereikindex
  per klasse (of een vergelijkbare dataset), waarbij +1 = zuiver hoog (A), −1 = zuiver laag (D).
  Alleen als het getal uit een dataset komt, niet uit een mens.

De **positie** is een bron-gewogen gemiddelde van de opgaven/metingen — de autoriteit zit in de
bronbetrouwbaarheid (een NOM-rapport weegt zwaarder dan een zelf-verkopende mediakit), niet in
een zelf-gekozen magnitude. Het vertrouwen α blijft laag bij één dun signaal.

## Regels

- **Eén bron → één klasse-signaal per outlet** (geen dubbeltelling uit dezelfde bron).
- **Bron verplicht** (bron-gepoort, net als `politieke_positie`): `POST /api/arguments` weigert
  een `doelgroepklasse`-root zonder echte citatie (quote óf bron met vindplaats) met **400**.
  Indienvolgorde: **bron (+locator) → argument (mét citatie)**. Alles landt `voorgesteld`.
- **Mediakit = primaire, maar zelf-verkopende bron** → betrouwbaarheid `primair`/`grijs` voorstellen;
  een onafhankelijke NOM/NMO-meting of academische studie weegt zwaarder (`institutioneel`/`academisch`).
- **Tweezijdig oogsten** (hoog én laag): zoek expliciet ook outlets die de onderkant bedienen
  (gratis/populair/regionaal), niet alleen de kwaliteitspers — anders overschat je de spreiding.
- **Negatief resultaat → missielog**, nooit als model-node ("gezocht, niets gevonden" is geen bijdrage).
- **Alleen outlets** (media-organisatie/omroep); de property hoort bij een entiteit (`entity_id`).

## Werkvoorbeeld (gemerged)

NRC → `welstand:A`, bron = NRC-mediakit: *"De NRC-lezer is hoogopgeleid en kapitaalkrachtig en
bevindt zich bovengemiddeld vaak in sociale klasse AB1."* Zie ook het mechanisme-argument op #176
(MRS: social grade = de "common currency" van de reclame-industrie).

Zie `doelgroep.py` (afleiding), `/api/doelgroep` (meter), en de viz-kleurmodus **Doelgroep** +
detailpaneel **Welstandsmeter**. Log elke ronde in `missies/logs/`.
