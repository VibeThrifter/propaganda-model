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

## Zustermeter: bereik (publiek per jaar)

Deze overlay draagt óók de **bereikmeter** — een parallelle, gesourcete overlay per
media-entiteit: het **publieksbereik per jaar**. Codeer een bereik-signaal met
`property='bereik'`, `property_value='<maat>:<aantal>:<jaar>'`, waarbij `<maat>` ∈
`bereik.MATEN` (kijkers/luisteraars/oplage/bereik_totaal/online/invullers/volgers) en het
**jaar verplicht** is (de tijdreeks is het punt). Regels als bij `doelgroepklasse`: één
signaal = één cijfer uit één bron (geen gewogen gemiddelde; een fout cijfer weerleg je met
een ondergraving), bron-gepoort (400 zonder echte citatie), telt in **niets** mee
(`ASPECT_PROPERTIES`). Per jaar wint de **grootste publieksmaat** de weergave. Zie
`bereik.py`, `/api/bereik`, de viz-grootte-maat **Mediabereik** en het detailpaneel
**Bereik (publiek)**; report `scripts/bereik_meter.py`. Bereik-cijfers komen uit NOM/NMO,
SKO, NLO, jaarverslagen en mediakits.

## Cadans (onbewaakt, C1)

Deze overlay (welstand + bereik) draait onbewaakt op een lage cadans — **maandelijks** —
via de scheduler (`scripts/agent_runner.py --agent assistent --label doelgroep`; timer
launchd via `agent_schedule.py`, standaard uit en aan te zetten op `/beheer`), onder het staande
account `assistent`. De runner injecteert de voorregel (eerst
`GET /api/agent/reeds_gereageerd`, sla die id's over) en tee't de ronde naar
`missies/logs/`.

**Exit-condities.** Lege oogst (geen outlet met citeerbaar klasse-/bereik-materiaal) →
afronden en loggen; een outlet **onbepaald** laten is correcter dan een geleende score.
Rate-limit **429** of andere 4xx → een lus stoppen en loggen.

**Logging-plicht per ronde.** `missies/logs/YYYY-MM-DD_doelgroep_<ronde>.md` met de
brief-blob-hash, élke query, per signaal het entity-/source-/argument-id + as/klasse/jaar
+ bron, de negatieve resultaten en de balans; de runner voegt exit-code/duur/oogst als
footer toe. Alles blijft `voorgesteld`, eigen token, geen statuswijzigingen.

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
- **Classificaties**: de as of klasse staat in `property_value`; de bewering zelf zegt wat de
  partij deed, zei of publiceerde (met bron), niet hoe de database haar noemt.

## Looptijd: zonder jaartal geen verband (eigenaarsbesluit 2026-10-09)

Elk verband dat je indient of onderbouwt, krijgt zijn looptijd: begin (`active_from`) en, als het
voorbij is, einde (`active_until`), zo precies als de bron geeft (`JJJJ`, `JJJJ-MM`, `JJJJ-MM-DD`),
met een citaat dat het jaartal noemt. Het begin van dít verband (benoeming, toetreding), niet de
oprichting van de organisatie of de datum van het artikel. Vind je het echt niet: zeg waar je
zocht (`zonder_jaar`) of laat het verband weg — nooit een geraden jaartal; de datumzoeker zoekt
verder. Een datum bij een bestaand verband: een aspect-argument (`property` `active_from`/
`active_until`, `property_value` de datum). Zie missies/README.md § Looptijd.

