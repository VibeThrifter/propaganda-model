# Agent-missies (verbeterplan §6.2, M1.8/M1.9/M3.3)

Alle agent-rollen draaien als Claude Code (background) sessies — geen aparte integratie.
Ze gebruiken exact dezelfde REST-API als menselijke gebruikers en authenticeren met het
Bearer-token van hun agent-account (`data/tokens/<naam>.token`, aangemaakt via
`scripts/create_user.py`). De ene regel die overal geldt: **een agent telt als
gebruiker, maar verdient zijn gewicht** — provenance verplicht, elke claim herleidbaar
naar een door mensen controleerbare bron, nooit directe statuswijzigingen.

## Een missie starten — onbewaakt, op cadans (C1)

De missies draaien **onbewaakt op een vaste cadans**, niet met de hand. launchd roept
de wrapper `scripts/agent_runner.py` aan; die
laadt het agent-token, bouwt de missie-prompt (verwijzing naar de brief + het account
+ de vaste voorregel hieronder) en start **één headless `claude -p`-sessie** per ronde,
die naar `missies/logs/` tee't. De agent *is* een Claude Code-sessie, dus "schedulen"
= per ronde één headless invocatie plannen — geen aparte daemon.

- **Cadans & installatie:** `agent_schedule.py` is de enige lijst van wat er draait (op
  deze Mac via launchd: `deploy/launchd/genereer_launchd.py --geen-server --laden`). Sinds 2026-10-07 draaien alleen de automatische beoordeling (elk
  uur; zij start de aanklager zelf), `nieuws-scout` en `nieuws-bewijs`. LinkedIn-scrapen heeft geen eigen timer; onbewaakt gebruik (alleen
  door de `nieuws-scout`) loopt uitsluitend achter de snelheidsrem
  `tools/linkedin/snelheidsrem.py` (beleid J4, gewijzigd 2026-09-30).
- **Droogloop (post niets):**
  `python3 scripts/agent_runner.py --agent monitor-agent --brief missies/monitor_brief.md --dry-run`
  toont het exacte `claude`-commando + tokenpad.
- **Handmatig één ronde forceren** kan met hetzelfde commando zónder `--dry-run`.

Elke ronde: de agent logt in `missies/logs/` (zie hieronder) en dient alle
bevindingen in via de API; de automatische beoordeling beslist daarna, elk uur, met
onafhankelijke controles (niemand beoordeelt met de hand, eigenaarsbesluit 2026-10-06). De runner voegt exit-code,
duur en oogst (edit_log-delta) als footer aan het log toe en schrijft een run-record
naar `data/agent_runs.jsonl` (gitignored, C4-toezicht).

**Exit-condities (elke agent).** Lege oogst → afronden en loggen, geen vulling
indienen. Rate-limit **429** (bijdrager 30/min) → ronde stoppen en loggen, niet in een
lus herproberen. Dode LinkedIn-sessie (`⚠ LINKEDIN-SESSIE VERLOPEN`) → stoppen, het
login-commando relayen aan de eigenaar, niet herproberen — de runner detecteert die
exit apart.

**Stuck-detectie & toezicht (C4).** Elke `.service` heeft een harde
`TimeoutStartSec=` die een vastgelopen ronde doodt; `scripts/monitor_agents.py`
(read-only) toont per agent de delta sinds de vorige run met een afwijkingssignaal
(0 inzendingen = mogelijk vastgelopen/lege ronde; boven de drempel = mogelijk op-hol).

## Reageer niet twee keer op hetzelfde argument

Van elke soort agent draait er maar één tegelijk, dus gelijktijdig botsen kan niet —
maar dezelfde agent komt later terug. Reageer dan niet opnieuw op een argument waar je
al op reageerde. Je hoeft niets bij te houden: je eigen reacties staan al in de data.

1. Haal vóór een ronde je eigen reactielijst op: `GET /api/agent/reeds_gereageerd`
   (met je Bearer-token) → `gereageerd_op` is de lijst argument-id's waar jij al een
   reply of rating op zette.
2. Sla die argumenten over; reageer alleen op wat er niet in staat.

De server is de vangrails: probeer je tóch een tweede reactie op hetzelfde argument,
dan weigert `POST /api/arguments` met **409** (alleen voor agents; mensen mogen wel een
discussie voeren met meerdere reacties). Doelwit-keuze (welke relatie/mechanisme) komt
zoals altijd uit `data/onderzoeksagenda.json`.

## Logging (auditbaar, M1.9-blind-zoekprotocol)

Per missie één logbestand: `missies/logs/YYYY-MM-DD_<agent>_<ronde>.md` met:

- **Brief**: welke brief, welke versie (git-hash van het briefbestand).
- **Queries**: élke zoekopdracht (web of database) letterlijk gelogd, met tijdstip —
  bevooroordeeld zoeken is dan achteraf aantoonbaar.
- **Oogst**: per bevinding/bron het argument-id dat via de API is aangemaakt.
- **Negatieve resultaten**: zoektochten die niets opleverden ("geen tegenbewijs
  gevonden; gezocht via X, Y, Z") — **alleen hier in het log, nooit als `contextual`
  bijdrage in het model.** Een AI-bewering "ik zocht en vond niets" is
  onfalsifieerbaar (geen door mensen controleerbare bron), beweegt de score niet, heft
  de `onweersproken`-vlag niet op en wekt als modelbijdrage valse geruststelling. In
  het log dient ze het enige doel waarvoor ze deugt: aantonen dát breed is gezocht
  (anti-cherry-pick).
- **Stance-balans van de ronde**: n steun / n tegen / n context (tweezijdige
  oogstplicht; een agent die alleen bevestiging binnenbrengt is meetbaar kapot).

De logs zijn werkmateriaal en worden ingecheckt (géén tokens of secrets erin).

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

## Looptijd: elk verband krijgt zijn jaartallen (eigenaarsbesluit 2026-10-09)

"Vul bij alles de goede jaartallen in he want het model kijkt gewoon per tijdsvak wat de
relaties zijn.. zorg ook dat dit overal wordt gehandhaafd en dat alle agents dit weten want wordt
vaak overgeslagen." De tijdbalk, de nieuws-app en de routes lezen een verband per periode: een
verband zonder begin staat altijd en overal "aan".

- **Elk verband krijgt zijn looptijd**: `active_from` (begin) en, als het voorbij is,
  `active_until` (einde), zo precies als de bron geeft (`JJJJ`, `JJJJ-MM` of `JJJJ-MM-DD`; nooit
  preciezer dan de bron). Met bron: het citaat noemt het jaartal. **Zonder jaartal geen
  verband.**
- **Het begin van dít verband**: de benoeming, de toetreding, de eerste opdracht. Niet de
  oprichting van de organisatie, niet de publicatiedatum van het artikel, niet een ander ambt van
  dezelfde persoon. "In 2019 was hij al …" is geen begin.
- **Voorbij = einde invullen**: een vertrek, een afgelopen termijn, een opgeheven organisatie.
  Een verband dat niet meer loopt zonder einde, is een fout in de tijdbalk.
- **Vind je echt geen begin**: dien het verband in met `zonder_jaar` (scripts/scout_indienen.py:
  waar je zocht) of laat het weg; nooit een geraden jaartal. De goedkeurpoort (`looptijd_reden`)
  laat een verband zonder begin pas door nadat de datumzoeker (`scripts/datumzoeker.py`, account
  `datumzoeker`) aantoonbaar zocht en niets vond (`looptijd_onderzoek`); de controle
  `RELATIE-ZONDER-JAAR` (geratchet) houdt dat bij.
- **Een datum bij een bestaand verband**: een aspect-argument (`property` `active_from` of
  `active_until`, `property_value` de datum, letterlijk citaat dat het jaartal noemt). De
  bronchecker toetst het; de automatische beoordeling zet de datum alleen in een leeg veld.
- **Registers** geven hun datums zelf (`scripts/registers_looptijd.py`): noemt een register geen
  begin, dan staat dat vastgelegd en wordt er niets verzonnen.
- **Binnen het bestaan (2026-10-13)**: een verband loopt nooit buiten het bestaan van zijn
  eindpunten. Een band van vóór de oprichting of van ná de opheffing van een organisatie hoort bij
  haar voorganger of opvolger: geen VARA-band uit 1986 op BNNVARA (2014), geen PvdA-band die na
  1 juli 2026 begint (dan PRO). De goedkeurpoort (`bestaan_reden`) houdt zo'n verband tegen en
  noemt de opvolger. Ontbreekt de voorganger, dien die dan in als eigen entiteit.
- **Bestaan van een organisatie**: `active_from` = oprichting, `active_until` = opheffing of fusie.
  Het aspect-argument staat op de entiteit (`entity_id`, `property` `active_from`/`active_until`) en
  stap 10c zet het in een leeg veld. **Een persoon draagt geen functieperiode als looptijd**: "sinds
  2020 CEO" hoort op het verband met het bedrijf, niet in `active_from` van de persoon.
- **Fusie of opheffing**: twee aspect-argumenten op de opgeheven organisatie, elk met een letterlijk
  citaat. (1) `active_until` met de datum. (2) `property` `opgegaan_in` met als `property_value` het
  id van de opvolger; de bewering noemt de opvolger bij naam. Nooit samenvoegen (M2.6): de banden van
  de voorganger blijven van haar. De viz en `/partijen` tonen de stamboom zelf. Een lid gaat alleen
  over naar de opvolger als een bron dat voor die persoon zegt. Bestaat de voorganger nog niet in het model, dien
  haar dan in als entiteit, zonder datums bij het aanmaken, met de twee argumenten erbij. Haar fusie
  laat haar goedkeuren; stap 10d hangt daarna de oude banden die het bewijs aan haar toeschrijft aan
  haar.
- **Een verkeerde organisatiedatum**: dien de juiste in als aspect-argument met een letterlijk citaat.
  Een onbeschermde datum (geen mens, geen register, geen gemerged argument) wordt dan verfijnd of
  verruimd. Een datum die het bestaan verkort, blijft staan tot een mens beslist.

## Accounts

| Account | Rol | Brief | Mag niet |
|---|---|---|---|
| `monitor-agent` | bijdrager | `monitor_brief.md` | statussen zetten; alleen bevindingen indienen |
| `criticus-agent` | bijdrager | `criticus_brief.md` | stromannen; statussen zetten; alles wacht op review |
| `scout-agent` | bijdrager | `scout_brief.md` (+ `linkedin_scout_brief.md`) | theorielaag schrijven; verbanden zonder bron; statussen zetten |
| `aanklager-agent` | bijdrager | `aanklager_brief.md` | eigen claim certificeren (403); twee keer op dezelfde parent reageren (409); statussen zetten |
| `nieuws-scout` | bijdrager | `nieuws_scout_brief.md` (Epic 12) | privépersonen onderzoeken; LinkedIn buiten de snelheidsrem; modelstatussen zetten (alleen de status van zijn eigen wachtrij-doel); meer dan 3 doelen per ronde |
| `nieuws-bewijs` | bijdrager | `nieuws_bewijs_brief.md` (nieuws-aggregator Story 14.13) | knopen of verbanden aanmaken; modelstatussen zetten (alleen de status van zijn eigen bewijsdoel); namen claimen; meer dan 2 doelen per ronde; negatieve resultaten als modelbijdrage |
| `bronchecker` | bijdrager | — (script `scripts/bronchecker.py`, automatische beoordeling 2026-10-06) | iets indienen in het model; alleen A1-oordelen (`/herverificatie`) schrijven; nooit eigen werk |
| `smaadtoets` | bijdrager | — (script `scripts/smaadtoets.py`, Opus, agents doen alles 2026-10-06) | iets indienen in het model; alleen smaadtoetsen (`/smaadtoets`) schrijven; nooit eigen werk |
| `rfc-toetser` | bijdrager | — (script `scripts/rfc_beoordeling.py`, Opus) | iets anders dan RfC-reviews schrijven; een RfC zonder concrete, controleerbare motivatie beoordelen |
| `rfc-criticus` | bijdrager | — (script `scripts/rfc_beoordeling.py`, Sonnet) | idem; wijst alleen af met een concrete reden |
| `bronzoeker` | bijdrager | — (script `scripts/bronzoeker.py`, agents doen alles 2026-10-06) | iets anders schrijven dan bronnen en revisies; een citaat dat het script niet letterlijk in de bron terugvindt; Wikipedia/sociale media/dit model als bron; een herformulering zonder de partijen zelf; statussen zetten |
| _(geen account)_ | — (alleen-lezen) | `voorspelling_resolutie_brief.md` | een voorspelling scoren (`PATCH …/uitkomst` = reviewer+ én mensenwerk); levert alléén resolutie-*voorstellen* in `data/voorspelling_voorstellen.json` |

**Het immuunsysteem (A1/A2, Deel A).** Elke `voorgesteld` supporting/contradicting-root
wordt onafhankelijk her-verifieerd tegen de echte bron (+ archiefkopie): quote verbatim,
dekt de bron de claim. Dat doet het script `scripts/bronchecker.py` (account `bronchecker`)
in de automatische beoordeling; het schrijft een `klopt/twijfel/klopt-niet`-verdict via
`POST /api/arguments/<id>/herverificatie`. De `aanklager-agent` is de gedecorreleerde
tegenstander: hij zoekt een tegenbron (weerlegging-root), valt de inferentie aan
(ondergraving-reply), of certificeert dat de claim de aanval `overleefde` via
`POST /api/arguments/<id>/tegenspraak`; de ronde start hem zelf als er werk voor hem is.
Beide oordelen leven in de procestabel `immuun_oordelen`, tellen **nergens** in de score,
en voeden alléén de auto-merge-poort (A7). Vertrouwen komt hier niet uit consensus maar uit
**onafhankelijkheid**: indiener, A1 en aanklager draaien elk onder een eigen account, met
een eigen prompt, en de bron wordt opnieuw opgehaald (decorrelatie).

**Opgeheven missies.** De briefs van de `verificatie-agent` (→ `bronchecker` in de ronde),
de `documentalist-agent` (→ `bronzoeker`; het anti-overfit-protocol staat nu in
`nieuws_bewijs_brief.md`), de alleen-lezen reviewbeoordelaar (→ de ronde beslist zelf) en
de nooit aangemaakte `lead-corroboratie-agent` (publieke lead-intake, D2.2) staan in
`archief/`. Ze draaien niet meer.

## LinkedIn-scrape als scout-optie

Persoon↔organisatie/opleiding/club-banden in kaart brengen kan met de **LinkedIn-integratie**
in `tools/linkedin/` (brief: `linkedin_scout_brief.md`, account `scout-agent`). Ze werkt via
hetzelfde bijdragepad — de gewone REST-API, alles `voorgesteld`. Tweetraps:

1. `python3 tools/linkedin/scrape_profile.py <url>` → genormaliseerd `data/linkedin/<slug>.json`
   (Playwright, eigen sessie; de eigenaar draait deze stap doorgaans zelf).
2. `python3 tools/linkedin/linkedin_naar_model.py <json> [--volledig] [--indienen]` → dient
   gedateerde `persoon→org`-affiliaties in (draaideur/brug-discipline; opleiding/club =
   kandidaat; bron `grijs`). Droogloop is default; idempotent + rate-limit-bestendig.

**Gericht, geen bulk (beleid J4, gewijzigd 2026-09-30):** een handvol relevante profielen
per onderzoeksvraag, nooit een crawl-lijst — de tool weigert een batch > 5 zonder
`--ik-weet-het`. Headful, eigen sessie, willekeurige pauzes, geen proxy's. Automatisch
gebruik mag alleen achter de snelheidsrem (2/uur, 10/dag, 08–22 uur, stroomonderbreker;
exit 75 = rem, 76 = blokkade) en alleen voor personen met een publieke rol uit
`nieuws_doelen` (`nieuws_scout_brief.md`).
LinkedIn is **aanvulling**: de primaire structuurbronnen zijn KvK/jaarverslagen/publieke
registers/nieuws; zelf-gerapporteerd → bronklasse `grijs`, `data/linkedin/` gitignored.
Details: `tools/linkedin/README.md` § Scraping-beleid.
