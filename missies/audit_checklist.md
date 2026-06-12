# Jaarlijkse audit (verbeterplan M3.5)

**Ritme:** jaarlijks, in juni. **Eerstvolgende audit: juni 2027.**
**Precedent:** de tier-audit van juni 2026 (duplicaat-halo's en een dyade
geabsorbeerd door hun hyperedges, feedback-loop → hyperedge —
`migrate_tier_herindeling.py`), toen als maintainer-migratie uitgevoerd.
**Sinds M2.6 loopt elke structuuringreep die eruit volgt via het voorstelpad**
(splitsen/samenvoegen/hernoemen, `POST /api/voorstellen`), niet meer als migratie.

De audit is een leesronde met checklist, geen automatische run; de validator en
de analysescripts leveren de werklijsten. Uitvoerder: de eigenaar + waar mogelijk
een tweede menselijke reviewer (de helft van de checks is een oordeel, geen meting).

## A. Aard & tiers (theorielaag)

- [ ] Elk mechanisme langs de aard-beslisregels van CLAUDE.md ("When adding a
      mechanism, choose `aard` in this order"): is elke `direct`-edge nog echt
      een dyade, elke halo (`veld_eigenschap`) nog een staande toestand zonder
      aanwijsbare levende zender (freeze-test), elk samenspel een hyperedge?
- [ ] Geen gebruik van de deprecated waarden `indirect`/`veld_instantiatie`.
- [ ] Hyperedge-ledenlijsten nog kloppend (pars pro toto voor het apex-veld;
      geen leden die inmiddels vervangen zijn).
- [ ] Padclaims: routes nog doorlatend (validator PADCLAIM-checks groen) en de
      claims zelf nog actueel — een padclaim is óók een claim die veroudert.
- [ ] Dubbelingen/granulariteit: `python3 scripts/analyse_granulariteit.py`
      draaien; kandidaten wegen en zo nodig als voorstel indienen (M2.6).

## B. Bronclassificaties

- [ ] Reliability-klassen herbeoordelen (Wikipedia's perennial-sources-les):
      is een bron sindsdien gezaghebbender of juist omstreden geworden?
      Beslislog bijwerken (wie herclassificeerde, waarom).
- [ ] Clustertoekenning (`cluster_key`) nasteken: nieuwe bronnen van dezelfde
      auteur/uitgever/dataset in hetzelfde cluster? (validator CLUSTER-BRON;
      precedent-werklijst: `BRONCLUSTER_REVIEW.md`).
- [ ] Linkrot: `python3 scripts/validate_model.py --network`; ontbrekende
      `archive_url`-locaties aanvullen.
- [ ] `eigen_synthese`-regel intact: geen projectmateriaal dat als bewijs telt.

## C. Halo-criteria & scoringsconstanten

- [ ] Halo's: bestaat er inmiddels wél een aanwijsbare zender voor een
      veld-eigenschap? Dan ommodelleren naar een edge (voorstelpad).
- [ ] Scoringsconstanten (K_AGG, caps, brongewichten) tegen de nieuwste
      gevoeligheidsanalyse leggen (`python3 scripts/analyse_gevoeligheid.py`);
      het M1.4-plafond herijken zodra er echte tegenspraak in het corpus zit.

## D. Proces & provenance

- [ ] Heraudit-lijsten: alle `self_merged`-merges en `self_scored`-voorspellingen
      (validator VOORSPELLING-ZELF) — zodra er onafhankelijke reviewers zijn,
      hier beginnen.
- [ ] Agent-kalibratie bijwerken (`python3 scripts/kalibratie_agents.py`):
      verdienen agent-ratings nog hun (gecapte) gewicht?
- [ ] Verlopen voorspellingen scoren (validator VOORSPELLING-DEADLINE) en het
      kalibratierapport draaien (`python3 scripts/voorspellingen.py`).
- [ ] Afsluiten met een modelrelease (M3.1) waarvan de changelog de
      auditbevindingen samenvat.

## Verslaglegging

Per audit één verslag `missies/logs/YYYY-MM_audit.md`: wat is nagelopen, wat is
gewijzigd (met voorstel-id's), wat is bewust gelaten en waarom. De audit van
juni 2026 geldt als nulmeting; het eerste verslag in deze vorm is juni 2027.
