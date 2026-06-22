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
   gezocht via X, Y, Z"). Dat rapport dien je in als `contextual`-argument op het
   doel — het telt mee in de bewijsdekking.
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

## Harde grenzen

- Nooit statuswijzigingen; nooit theorielaag-schrijven (dat is RfC-werk, M2.3).
- Stance-balans en nieuwheid (nieuwe bronclusters vs. hercitaties) van je ronde
  komen in het log — een documentalist die alleen bevestiging binnenbrengt is meetbaar kapot.
