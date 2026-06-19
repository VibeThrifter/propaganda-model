# Monitor-agent — ronde 1 — 2026-06-19

- **Brief:** `missies/monitor_brief.md`, git-hash `41c92ce`.
- **Account:** `monitor-agent` (bijdrager). Alle schrijfacties via Bearer-token; geen statuswijzigingen, geen ratings, geen merges.
- **Server:** `GET /api/health` -> 200 (gecontroleerd 23:28:29).
- **Taak:** logica- & drogreden-controle (M1.8) op score-dragende, niet-`verworpen` root-argumenten (supporting/contradicting). Doel: terughoudend; alleen ondergravingen waarvan de aangevochten redeneerstap letterlijk te citeren is.

## Queries (letterlijk, met tijdstip)

Alle DB-queries via lokale SQLite (`data/propaganda_model.db`), API-leesqueries via `GET`.

- 23:28:29 — `curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/api/health` -> `200`.
- 23:28:29 — `git log -1 --format=%h -- missies/monitor_brief.md` -> `41c92ce`.
- ~23:29 — DB: `SELECT status, COUNT(*) FROM arguments GROUP BY status` -> ongecontroleerd 493, voorgesteld 20, geverifieerd 8, verworpen 1.
- ~23:29 — DB: stance-telling roots -> contextual 7, contradicting 7, supporting 508; 522 roots, 0 replies (vóór deze ronde).
- ~23:29 — DB: score-dragende kandidaat-roots per doeltype/property (parent NULL, stance in supporting/contradicting, status NOT IN (verworpen,voorgesteld), vervangen=0):
  - relation (geen) 375, relation existence 3, relation influence 1
  - mechanism (geen) 86
  - emergent (geen) 12
  - role indirecte_invloed_op 18
- ~23:30 — DB: dump van alle 474 score-dragende args (property NULL of 'influence') met claim + citaat-quotes + brontitels + doelbeschrijving -> `/tmp/allargs.json`.
- ~23:30 — Split: 142 args met quote (citaat-dekking toetsbaar), 332 zonder quote (citaat-dekking niet toetsbaar — overgeslagen voor citaat_dekking-oordeel).
- ~23:31 — `GET /api/arguments?mechanism_id=19` (parent-controle 426): 426 supporting ongecontroleerd, 427 contextual.
- ~23:32 — `GET /api/arguments?mechanism_id=153` (parent-controle 368): 368 supporting ongecontroleerd.
- 23:32:20 — `POST /api/arguments` ondergraving op 426 -> 200, nieuw argument **#571**.
- 23:32:25 — `POST /api/arguments` ondergraving op 368 -> 200, nieuw argument **#572**.

## Oogst (ingediende ondergravingen)

Beide als **contradicting-reply** (`parent_argument_id`, geen doel, geen property, verplichte `reasoning`), status `voorgesteld`.

1. **#571** — ondergraving op **#426** (MECH 19 `ideologische_synchronisatie`).
   - `objection_type: correlatie_als_causatie`.
   - Aangevochten stap: de gevolgtrekking dat de co-occurrence van de slogan "build back better" na juni 2020 (WEF 3 juni -> OESO 5 juni -> Biden/Johnson/Trudeau) frame-synchronisatie via elite-fora aantoont. De eigen eerste bron van #426 (Sendai Framework 2015, prioriteit 4) laat zien dat de exacte term al sinds 2015 een VN-term was — een alternatieve verklaring (onafhankelijke overname van een ingeburgerde term) die de causale stap niet uitsluit.

2. **#572** — ondergraving op **#368** (MECH 153 `primeurconcurrentie`).
   - `objection_type: citaat_dekking`.
   - Aangevochten stap: de brug van het citaat ("Journalisten zijn ... afhankelijk van de goodwill van politici en hun woordvoerders") naar de distinctieve claim "de onderlinge concurrentie disciplineert het hele corps". Het citaat dekt bron-afhankelijkheid, niet de onderlinge wedloop tussen journalisten die dit mechanisme onderscheidt van bron_afhankelijkheid/woordvoerdersregie.

## Niet ingediend (te vaag / te hoog vals-positief-risico)

Bewust achtergehouden onder de terughoudendheidsregel — vermoeden bestond, maar de aangevochten stap was niet hard genoeg letterlijk te citeren, of het citaat kon redelijkerwijs als losse dekking gelden:

- **#369** (MECH 150 `citaatautorisatie`): claim gaat specifiek over het vooraf autoriseren van citaten; het citaat noemt generiek "ongeschreven regels" zonder citaatautorisatie te benoemen. Borderline citaat_dekking — "ongeschreven regels" kan door een redelijke reviewer als losse dekking gelden. Niet ingediend.
- **#366** (MECH 148 `media_agendering`): citaat dekt alleen lobbyist->Kamervragen; de claim bruggt naar media_agendering (media zet de agenda) en "geplante verhalen". Borderline; niet ingediend.
- **#371 / #373 / #374** (MECH 152/51/83): herbruiken het generieke "functioneren als één stam"-citaat voor specifiekere mechanisme-claims. Vermoeden van losse dekking, maar het brondocument (Luyendijk) dekt de claims waarschijnlijk elders; het gekozen citaat is generiek maar niet aantoonbaar tegenstrijdig. Te zwak voor een harde citaat_dekking. Niet ingediend.
- **#538** (REL 472 PAX tegenmacht): claim noemt de F-35-rechtszaak; het inline-citaat dekt alleen "Don't Bank on the Bomb", maar de rechtszaak-bron staat wél in de bronnenlijst (zonder quote). Geen schone citaat_dekking — de feitenclaim heeft een bron. Niet ingediend.
- 332 args zonder enige quote: citaat-dekking niet toetsbaar (geen quote om te lezen). Geen ondergraving op grond van ontbrekende quote — dat is een bronplicht-/merge-poortkwestie, geen logicafout.

## Negatieve resultaten

- Geen circulaire redeneringen (`cirkelredenering`) gevonden in de 142 geciteerde args.
- Geen stromannen (`stroman`): de getuigenis-args (Muusse/Vlam, ids 461-476) parafraseren de bron getrouw; claims blijven binnen wat de transcript-quotes zeggen.
- Geen `autoriteit_buiten_domein`: experts worden binnen hun domein opgevoerd (Chomsky/H&C theorie, juristen bij EHRM-zaken, CTIVD bij inlichtingen).
- Geen `vals_dilemma`, `ad_hominem`, `equivocatie`, `anekdote_als_regel` aangetroffen die de letterlijk-citeerbaar-drempel haalden.
- De factuele eigendoms-/adverteerders-/persbureau-roots (ids 1-48 e.a., zonder quote) zijn simpele bestaanssituaties; geen logicafout in de gevolgtrekking, alleen ontbrekende citaties (poort-/bronplichtkwestie, buiten mijn mandaat).

## Stance-balans van de ronde

- Steun (supporting): 0
- Tegen (contradicting / ondergraving): 2 (#571, #572)
- Context (contextual): 0

Monitor-werk produceert per definitie alleen ondergravingen (contradicting replies) of contextuele kanttekeningen; deze ronde 2 ondergravingen. Beoordeeld: 142 geciteerde score-dragende root-args integraal op citaat-dekking + redeneerstap; 332 niet-geciteerde args op gevolgtrekking (citaat-dekking n.v.t.). Vals-positief-discipline: 5 concrete vermoedens overwogen en bewust niet ingediend omdat de aangevochten stap niet hard genoeg te citeren was — ingediend alleen waar de bron-eigen tegenspraak (#571: Sendai 2015) of de citaat-claim-mismatch (#572) letterlijk aanwijsbaar is.
