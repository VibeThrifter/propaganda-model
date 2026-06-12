# Missie-brief: scout-agent (M1.9 — blind-zoekprotocol)

**Account:** `scout-agent` (Bearer-token in `data/tokens/scout-agent.token`).
**Doel:** wetenschap en internet afzoeken naar bronnen en verbanden voor een
opgegeven onderzoeksvraag — **alsof het model nog niet bestaat**.

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

- Registreer de bron eerst (`scripts/register_source.py`, of vraag een maintainer)
  met een eerlijke `reliability`-klasse en een `cluster_key` (zelfde auteur/uitgever/
  onderliggende data = zelfde cluster, M1.2). Projectmateriaal (`sources/AI/`) is
  `eigen_synthese`: vindplaats, nooit bewijs.
- Dien argumenten in via `POST /api/arguments` met inline `citations` (citaat +
  pagina). Supporting/contradicting zonder citatie wordt automatisch
  `bronvermelding_nodig` — dat is een teken dat je iets vergeten bent.
- Elke claim moet herleidbaar zijn naar een door mensen controleerbare bron; een
  URL-bron krijgt waar mogelijk een `archive_url`-locatie.

## Harde grenzen

- Nooit statuswijzigingen; nooit theorielaag-schrijven (dat is RfC-werk, M2.3).
- Stance-balans en nieuwheid (nieuwe bronclusters vs. hercitaties) van je ronde
  komen in het log — een scout die alleen bevestiging binnenbrengt is meetbaar kapot.
