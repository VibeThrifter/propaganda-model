# Red-team-agent — ronde 1 — 2026-06-19

**Brief:** `missies/redteam_brief.md`, git-hash **41c92ce** (laatste commit op het briefbestand: `41c92ced27eec3cf3450810030ee914c95cb6fe7`). Repo-HEAD bij uitvoering: `6af4f97`.
**Account:** `redteam-agent` (bijdrager). Alle schrijfacties via REST-API met eigen Bearer-token; alles landde als `voorgesteld`.
**API:** http://localhost:5000 — health geverifieerd = 200.
**Doelwitten (M3.3):** top-3 van `redteam_top20` in `data/onderzoeksagenda.json` (ververst met `python3 scripts/onderzoeksagenda.py`): relaties **360, 413, 415** — alle drie `onweersproken: true`, 0 voor / 0 tegen vóór deze ronde.

Vooraf gecontroleerd dat er geen bestaande argumenten op de doelen stonden (`GET /api/arguments?relation_id=<id>` → `[]` voor alle drie). De claims zijn op hun sterkst gelezen uit de relatie-`description` + gekoppeld mechanisme in de DB, zodat ik geen stroman aanviel.

## Queries (tijdstip ~lokaal)

| Tijd | Type | Query |
|---|---|---|
| 23:30 | DB | `GET /api/arguments?relation_id=360 / 413 / 415` (alle leeg) |
| 23:30 | DB | relaties + entiteiten + mechanismen 85/109/83 uitgelezen voor de sterkste lezing |
| 23:31 | web | `Unilever dividendbelasting afschaffing 2018 Rutte ingetrokken hoofdkantoor Londen vertrek` |
| 23:31 | web | `Stichting Democratie en Media DPG invloed redactie kostenbesparingen kritiek effectiviteit` |
| 23:31 | webfetch | NOS 15-10-2018: afschaffing dividendbelasting definitief van tafel |
| 23:31 | web | `FTM DPG Media redactiestatuut onafhankelijkheid stichting prioriteitsaandeel grenzen invloed` |
| 23:32 | webfetch | NOS 27-06-2025: DPG mag RTL overnemen onder strikte voorwaarden (ACM) |
| 23:32 | web | `Stichting Democratie en Media kritiek minderheidsbelang machteloos DPG bezuinigingen redactie ontslagen` |
| 23:32 | webfetch | Netkwesties 06-07-2025 (Buitelaar & Olsthoorn) — twee artikelen, kritiek op effectiviteit borging |
| 23:33 | web | `PCM uitgevers Apax Partners 2004 2007 schulden uitgehold sanering SDM Het Parool` |
| 23:33 | web | `Unilever hoofdkantoor Londen 2020 enkelvoudige structuur Nederland verlaten dividendbelasting` |

## Geregistreerde bronnen (via `POST /api/sources`, eigen token)

- **104** — Buitelaar & Olsthoorn, "Gratis en zelfstandig RTL Nieuws en Nu.nl redden de democratie niet", Netkwesties, 2025-07-06 (url).
- **105** — NOS, "DPG mag RTL overnemen, wel onder strikte voorwaarden", 2025-06-27 (url).
- **106** — NOS, "Afschaffing dividendbelasting definitief van tafel, geld naar bedrijfsleven", 2018-10-15 (url).
- **107** — Wikipedia, "De Persgroep Nederland" (PCM-saneringsperiode onder Apax 2004-2007), 2010 (url).
- **108** — NOS, "Unilever vanaf vandaag niet meer Nederlands, maar alleen nog Brits", 2020-11-30 (url).

## Oogst per doelwit

### Relatie 360 — Stichting Democratie en Media → DPG Media (eigendom / onafhankelijkheidsborging, filter tegenmacht)
Sterkste lezing: SDM's prioriteitsaandeel is een *effectieve* structurele rem op eigenaarsinvloed.

- **WEERLEGGING — arg. #573 (contradicting root, bronnen 104 + 107).** De borging is in de praktijk een veel zwakkere/papieren rem: historisch hield de stichtingsconstructie de uitholling van PCM door private-equityfonds Apax (2004-2007) niet tegen — eigen vermogen +268 mln → −55 mln, hof Amsterdam oordeelde in 2010 wanbeleid. Buitelaar & Olsthoorn noemen de stichtingen "toetsloos" en de garanties "papieren tijgers". Aanval richt zich op de **invloed/effectiviteit-as**, niet op het bestaan van de relatie.
- **STEUN — arg. #574 (supporting root, bron 105) — omgekeerde oogstplicht.** De ACM versterkte SDM's formele vetorecht in 2025 juist: geen landelijke nieuwstitel verkoopbaar/op te heffen zonder SDM-goedkeuring + redactiestatuten die budgetsnijden inperken. Dit miste het corpus; eerlijkheidshalve ingeleverd.

### Relatie 413 — Stichting Democratie en Media → NU.nl (eigendom / continuiteitsborging, post-2025)
Sterkste lezing: het SDM-veto borgt de continuiteit/het zelfstandig voortbestaan van NU.nl.

- **STEUN — arg. #575 (supporting root, bron 105).** De ACM-voorwaarden (27-06-2025) verankeren dit expliciet: NU.nl moet gratis + afzonderlijk blijven bestaan, geen verkoop/beeindiging zonder SDM, aparte toezichtstichting. Directe bevestiging van de claim (die op active_from 2025-07-01 staat).
- **WEERLEGGING — arg. #576 (contradicting root, bron 104).** Dezelfde remedies zijn volgens Buitelaar & Olsthoorn "zacht als boter", beperkt houdbaar en niet handhaafbaar; een verkoopveto beschermt het formele bestaan maar niet tegen sluipende uitkleding (budget/redactie). Begrenst de **effectiviteit** van de continuiteitsborging.

### Relatie 415 — Unilever → VNO-NCW (lidmaatschap / belangenbehartiging, filter sourcing)
Sterkste lezing: Unilever is een agendabepalend zwaargewicht waarvan het belang structureel doordringt in beleid/mediabeeld; de dividendbelasting-casus is het aangevoerde bewijs.

- **WEERLEGGING — arg. #578 (contradicting root, bronnen 106 + 108).** In exact die casus *faalde* de lobby: de afschaffing van de dividendbelasting ging in oktober 2018 definitief van tafel en Unilever verhuisde zijn hoofdkantoor in 2020 alsnog naar Londen i.p.v. Rotterdam. Begrenst de **sterkte/effectiviteit** van de invloed (niet het lidmaatschap zelf — zekerheid 0,9 staat niet ter discussie).
- **EERLIJKE INPERKING — arg. #581 (contextual root, geen citatie).** Begrenzing bij mijn eigen weerlegging: het mislukte *einddoel* schaft de agendabepalende *toegang* niet af — de miljardenmaatregel stond in geen verkiezingsprogramma maar belandde wel in het regeerakkoord op aandringen van het georganiseerde bedrijfsleven. Het tegenbewijs begrenst de sterkte van de invloed, niet het mechanisme van bevoorrechte toegang. (Voorkomt dat #578 als stroman gaat werken.)

## Negatieve resultaten

- Géén bron gevonden die ontkent dát Unilever lid/zwaargewicht is bij VNO-NCW (de relatie zélf, certainty 0,9, blijft overeind) — gezocht via de twee Unilever-queries hierboven; alle treffers bevestigen het lidmaatschap. De aanval kon daarom alleen de *effectiviteit* in de dividendcasus raken, niet het bestaan.
- Géén bron gevonden dat het SDM-veto op NU.nl ná medio-2025 al concreet is gefaald of teruggedraaid (constructie is recent, active_from 2025-07-01); het tegenbewijs op #413 is daarom principieel/structureel (papieren-tijger-kritiek + historische analogie), niet een al-gerealiseerd falen specifiek voor NU.nl.

## Stance-balans van de ronde

- **3 weerleggingen** (contradicting roots, mét citatie): #573, #576, #578
- **2 steun** (supporting roots, omgekeerde oogstplicht): #574, #575
- **1 inperking** (contextual root): #581

Totaal **6 argumenten** over 3 doelwitten. Elk doelwit (360, 413, 415) is van de `0 voor / 0 tegen`-status afgehaald en heeft nu zowel steun als tegenspraak — de onweersproken-vlag van deze drie kan na review verdwijnen. Tweezijdige oogstplicht gehaald: niet alleen aanval, ook gevonden steun ingeleverd.

## Eerlijk oordeel: overleefden de onweersproken-claims de aanval?

- **#360 (SDM→DPG):** Gedeeltelijk. De *certainty* (de relatie/het mechanisme bestaat) is robuust en werd in 2025 zelfs formeel versterkt (arg. #574). Maar de impliciete *effectiviteits*-lezing ("structurele rem") krijgt een serieuze, herleidbare deuk: het PCM/Apax-precedent is hard historisch tegenbewijs dat de borging uitholling niet tegenhield. Per saldo: de relatie overleeft, de sterkte-claim wankelt.
- **#413 (SDM→NU.nl):** Overleeft op zekerheid (ACM heeft het expliciet verankerd, arg. #575). De effectiviteits-claim is alleen op principiële/structurele gronden aangevochten (arg. #576) — geen al-gerealiseerd falen voor NU.nl beschikbaar, want de constructie is te jong. Zwakste van de drie aanvallen.
- **#415 (Unilever→VNO-NCW):** De sterkste aanval. De casus die het corpus als *bewijs* voor lobbymacht gebruikt, is bij nadere inspectie een casus waarin die macht haar einddoel verloor (#578). Dat is geen stroman maar een eerlijke herlezing van precies het aangevoerde voorbeeld. Tegelijk (arg. #581) blijft het toegangs-/agenda-mechanisme overeind. Netto: de relatie blijft, maar het ingeleverde "bewijs" is dubbelzinniger dan gepresenteerd.

Geen van de drie claims is volledig onderuitgehaald — bij geen ervan vond ik bewijs dat de relatie niet bestaat. Wel is bij alle drie de *onweersproken*-status terecht doorbroken en is bij #360 en #415 reëel tegenbewijs over de *effectiviteit/sterkte* aangedragen. Mensen beslissen via review.
