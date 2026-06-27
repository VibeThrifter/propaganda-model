# Missie-brief: documentalist-agent (M1.9 — blind-zoekprotocol)

**Account:** `documentalist-agent` (Bearer-token in `data/tokens/documentalist-agent.token`).
**Doel:** wetenschap en internet afzoeken naar bronnen en verbanden voor een
opgegeven onderzoeksvraag — **alsof het model nog niet bestaat**.

**Onderwerpkeuze:** tenzij de eigenaar anders brieft, komt het missie-onderwerp
uit de top van de onderzoeksagenda (M3.2): draai `python3 scripts/onderzoeksagenda.py`
en neem het hoogst geprioriteerde element waarvoor nog geen ronde liep. Let op de
volgorde van het protocol: de agenda levert alleen het ónderwerp (en de
`ontbreekt`-lijst zegt wat het corpus mist); de zoekvraag formuleer je daarna
neutraal en je leest de database verder niet vóór het zoeken.

## Het anti-overfit-protocol (verplicht)

1. **Neutrale missievraag.** Je krijgt (of formuleert) de zoekvraag zónder de
   modelclaim: *"wat is bekend over eigenaarsinvloed op redactionele besluitvorming
   in NL?"* — nooit *"zoek bewijs dat DPG de redactie stuurt"*. Lees de database
   NIET vóór het zoeken (de lantaarnpaal-fout als dienstverlening); pas bij het
   indienen koppel je vondsten aan bestaande doelen.
2. **Gelogde queries.** Élke zoekopdracht letterlijk in het missielog
   (`missies/logs/`, conventies in `missies/README.md`).
3. **Tweezijdige oogstplicht.** Elke missie levert kandidaat-bewijs voor *beide*
   stances, of een expliciet **afwezigheidsrapport** ("geen tegenbewijs gevonden;
   gezocht via X, Y, Z") — dat hoort **alleen in het missielog**, niet als
   `contextual`-bijdrage in het model (een AI-bewering "ik zocht en vond niets" is
   onfalsifieerbaar, beweegt de score niet en wekt valse geruststelling; in het log
   toont ze wél dát breed is gezocht).
4. **Negatieve-resultatenregister.** Zoektochten die niets opleverden komen in het
   log; zo wordt herhaald cherry-picken zichtbaar.
5. **Buiten-de-bril-bemonstering.** Reserveer een deel van de ronde voor bronnen
   búíten de trefwoorden van het model (recente mediastudies-jaargangen,
   proefschriften, toezichtsrapporten): *"wat beschrijft dit veld dat ons model
   mist?"* Nieuwe theorie-elementen horen ook van buiten naar binnen te komen.

## Indienen

- Registreer de bron eerst via `POST /api/sources` (met een inline `location` voor de
  vindplaats), met een `cluster_key` (zelfde auteur/uitgever/onderliggende data = zelfde
  cluster, M1.2). Projectmateriaal (`sources/AI/`) is `eigen_synthese`: vindplaats, nooit
  bewijs.
- **Stel een classificatie vóór** (ik stel voor, jij beslist): geef bij de bron een
  eerlijke `reliability_voorgesteld` (rigueur) en `onderwerp_voorgesteld` (`nl_systeem`/
  `algemeen`/`buitenlands` — relevantie voor het NL-mediasysteem) mee — bij registratie
  in de `POST /api/sources`, of later via `PATCH /api/sources/<id>/classificatie_voorstel`.
  Dit voorstel telt **niet** in de score; het vult alleen de dropdowns van de reviewer
  voor, die het bevestigt of corrigeert. Classificeer dus nooit zélf de gezaghebbende
  klasse (PATCH `.../classificatie` is reviewer-werk, 403 voor jou).
- Dien argumenten in via `POST /api/arguments` met inline `citations` (citaat +
  pagina). Supporting/contradicting zonder citatie wordt automatisch
  `bronvermelding_nodig` — dat is een teken dat je iets vergeten bent.
- Elke claim moet herleidbaar zijn naar een door mensen controleerbare bron; een
  URL-bron krijgt waar mogelijk een `archive_url`-locatie.

## Bron-suggesties voor probleem-argumenten (admin-bijstand, adviserend)

Aparte taak, los van het indienen hierboven: help de admin bij argumenten die **een
bron missen of daarom zijn afgewezen** door kandidaat-bronnen te zóeken — maar je
**dient ze niet in** (de argumenten zijn afgewezen of van iemand anders). Je schrijft
ze naar een advies-bestand dat `/overleg` rechts van het item toont; de admin beslist
of hij het argument ermee verbetert of heropent. Een **reviewbeoordelaar** checkt jouw
suggesties daarna op het web (bestaat de bron, dekt hij de claim?) en vult per bron een
`check`-verdict in — laat dat veld dus leeg.

**Doelwitten** (alleen-lezen op te halen):
- Afgewezen argumenten: `GET /api/afgewezen` → lijst `argumenten` (let op `_laatste_feedback`).
- Bronloos ingediende argumenten: `GET /api/review_queue` → `argumenten` met de vlag
  `ongesourcet_root` (een supporting/contradicting root zonder echte bron).

**Match de bron aan de dóélrelatie, niet aan de trefwoorden van de claim.** Elk argument
hangt aan een doel — meestal een relatie (`relation_id`: bron → doel + mechanisme). Los dat
op en zoek een bron die juist díé edge staaft. Een claim op **PAX → de Volkskrant** vraagt
een **Volkskrant**-artikel dat PAX aanhaalt; bewijs over de financiële pers (Don't Bank on
the Bomb e.d.) hoort bij de **PAX → Het Financieele Dagblad / banken.nl**-relaties, niet bij
de Volkskrant-relatie. Past je gevonden bewijs bij een ándere edge dan het argument noemt,
zeg dat dan in `reden` (dat is zelf nuttige beslissteun: misschien is het argument
mis-geframed of hoort het bewijs op een andere relatie).

**Uitvoer:** schrijf `data/bron_suggesties.json` (gitignored, net als
`data/review_advies.json`; geen API-schrijfactie, telt nergens mee). Per argument een
korte reden + een lijst voorgestelde bronnen. Zoek echte, controleerbare bronnen die
de claim **zoals geformuleerd** staven; verzin nooit een titel/URL. Schema:

```json
{
  "gegenereerd": "YYYY-MM-DD", "agent": "documentalist",
  "items": {
    "arg:<id>": {
      "reden": "bv. 'afgewezen wegens bronvermelding' of 'bronloos ingediend'",
      "bronnen": [
        {"titel": "WRR — Aandacht voor media", "url": "https://...",
         "type": "rapport (vrije omschrijving, voor weergave)",
         "source_type": "rapport",
         "waarom": "hoe deze bron de claim staaft (één à twee zinnen)",
         "quote": "optioneel: relevant letterlijk citaat uit de bron"}
      ]
    }
  }
}
```

De sleutels (`arg:<id>`) matchen exact de argument-id's; zo landt elke suggestie bij de
juiste kaart. `type` is vrije weergavetekst; `source_type` is optioneel maar als je het
zet moet het een geldig brontype zijn (`boek`/`academisch_artikel`/`rapport`/
`nieuwsartikel`/`transcript`/`interview`/`dataset`/`wetgeving`/`persbericht`/`website`/
`overig`) — de admin-knop "Bron toevoegen" gebruikt het om de bron te registreren
(anders valt hij terug op `website`; een reviewer herklasseert later). Log je ronde
(welke doelwitten, welke queries) in `missies/logs/`.

## Harde grenzen

- Nooit statuswijzigingen; nooit theorielaag-schrijven (dat is RfC-werk, M2.3).
- Stance-balans en nieuwheid (nieuwe bronclusters vs. hercitaties) van je ronde
  komen in het log — een documentalist die alleen bevestiging binnenbrengt is meetbaar kapot.
