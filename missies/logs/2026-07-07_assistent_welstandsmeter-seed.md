# Missielog — Welstandsmeter: feature + eerste klasse-signalen

**Datum:** 2026-07-07 · **Account:** `assistent` (signalen) + `maxime` (merge via admin)

Nieuwe **welstandsmeter**-laag gebouwd (code direct; zie geheugen `welstandsmeter` + CLAUDE.md): per outlet
een afgeleide marketing-/welstandsklasse uit gesourcete `doelgroepklasse`-signalen — operationele brug van
`koopkrachtselectie` (#176). Spiegelt de politieke kleurmeter. `validate --strict` groen, `test_doelgroep.py`
groen, `test_fresh_build` (schema==migratie) draait de verse build correct.

## Eerste data (voorgesteld via assistent → gemerged via admin)
- **Bron 1041 (MRS social grade):** mechanisme-arg op #176 (arg 1974) — social grade = de *"common currency"*
  van de reclame-industrie; adverteerders kopen publiek in klassen. Grondt het klassensysteem.
- **NRC → welstand:A** (arg 1975, bron 1027 NRC-mediakit): *"De NRC-lezer is hoogopgeleid en kapitaalkrachtig…
  sociale klasse AB1."* → positie 1,0, label "A (kapitaalkrachtig)".
- **De Telegraaf → welstand:B2** (arg 1976, bron 1042 Cebuco/NDP): *"het enige écht landelijke dagblad, met
  lezers binnen alle sociale klassen"* → positie 0,0, label "B2/C (standaard)". Contrast met NRC.

Meter (`GET /api/doelgroep`): NRC=A (pos 1,0), De Telegraaf=B2 (pos 0,0), elk α 0,224 (één bron). Viz-kleurmodus
**Doelgroep** (goud=hoog/koopkrachtig ↔ grijs=laag) + detailpaneel **Welstandsmeter** tonen het.

## Openstaand (voor de doelgroep-missie)
- Tweezijdig verder oogsten, m.n. de **onderkant** (gratis/populair/regionaal → C/D) — alleen mét verbatim
  mediakit/NOM-bron. Nu leunt de spreiding op de bovenkant (A) + midden (B2).
- **Pre-existing, niet van deze feature:** `scripts/test_fresh_build.py` faalt op `GET /api/review_queue (401)`
  (read-endpoint reviewer-gated geraakt op de branch; test stuurt geen token). Niet gepatcht — buiten scope.
