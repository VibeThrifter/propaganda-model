# Scout-rondes r4–r7 — oprichters, omroepdirecteuren, journalisten/columnisten, persbureaus

- **Datum:** 2026-07-04
- **Account:** assistent (bijdrager)
- **Git-hash bij aanvang:** de441f1
- **Tooling:** `scripts/scout_personen.py` + `data/scout/ronde{4,6,7}.json`. Alles `voorgesteld`.

## r4 — oprichter/oud-hoofdredacteur + omroepdirecteuren + draaideur/founders (6 nieuw, 2 hergebruikt)

| Persoon | Org | Rel | mech | bron |
|---|---|---|---|---|
| Rob Wijnberg (oprichter/oud-hoofdred. 2013–2026) | De Correspondent (13) | personeel | — | nl.wikipedia |
| Lonneke van der Zee (alg. dir.) | BNNVARA (139) | bestuurder | — | pers.bnnvara.nl |
| Arie Koornneef (directievoorzitter, 2025) | KRO-NCRV (140) | bestuurder | — | kro-ncrv.nl |
| Taco Zimmerman (alg. dir., 2024) | AVROTROS (141) | bestuurder | — | pers.avrotros.nl |
| Arjan Lock (voorz. RvB, 2008) | EO (138) | bestuurder | — | eo.nl/bestuur |
| **Kees Berghuis** (hoofdred.) | WNL (144) | personeel | **draaideur (18)** | Villamedia |
| **Kees Berghuis** (hoofd voorlichting VVD, 2015) | VVD (53) | woordvoerder_van | **draaideur (18)** | Villamedia |

- **Berghuis = echte draaideur** politiek/PR→journalistiek (VVD politiek assistent Zalm → chef RTL Nieuws →
  hoofd voorlichting VVD → hoofdredacteur WNL). Beide edges dragen `draaideurconstructie` (mechanisme 18),
  dus de brug VVD↔WNL leidt vanzelf af. Bert Huisjes (omstreden vertrek/terugkeer) bewust NIET toegevoegd.
- Dominique Weesie (#208) + Romke Spierdijk (#421): PowNed/GeenStijl-oprichter-edges bestonden al (andere
  bijdrager) → dedup sloeg ze over.

## r6 — notabele politieke journalisten/columnisten (4 nieuw; curatie, niet uitputtend)

| Persoon | Org | Rel | mech | bron |
|---|---|---|---|---|
| Sheila Sitalsing (columnist 2011–2022) | de Volkskrant (4) | personeel | — | nl.wikipedia |
| **Frits Wester** (parl. verslaggever RTL) | RTL Nieuws (88) | personeel | **draaideur (18)** | en.wikipedia |
| **Frits Wester** (woordvoerder Brinkman/CDA) | CDA (54) | woordvoerder_van | **draaideur (18)** | en.wikipedia |
| Wouter de Winther (pol. commentator/columnist) | De Telegraaf (9) | personeel | — | nl.wikipedia |
| Xander van der Wulp (pol. verslaggever 2008–25, nu hoofdred. NOS Sport) | NOS (11) | personeel | — | over.nos.nl |

- **Frits Wester = tweede echte draaideur** (CDA-woordvoering Elco Brinkman → RTL Nieuws); brug CDA↔RTL Nieuws
  leidt vanzelf af.
- Sitalsing-column verbatim gedateerd 2011–2022 (bron dekt die periode; mogelijk sindsdien hervat — reviewer
  kan verlengen). Bewust niet current-tense verder geclaimd dan de bron draagt.

## r7 — persbureaus (1 nieuw)

| Persoon | Org | Rel | bron |
|---|---|---|---|
| Freek Staps (hoofdred. sinds 2019) | ANP (12) | personeel | Villamedia |

- **Reuters/AP/AFP**: internationaal; geen zinvolle NL-hoofdredactie-node — hun invloed loopt via de
  wire-/pakketjournalistiek-afhankelijkheid, niet via een persoon. Bewust overgeslagen (geen fabricage).
- **Novum Nieuws** (#337): in 2015 opgegaan in het ANP (37 van 52 banen weg) — de facto defunct. Geen
  persoonsnode toegevoegd. Optionele structurele follow-up: ANP→Novum `eigendom` (overname 2015).

## Verificatie
- `scripts/validate_model.py --strict`: zie afsluitende run in de sessie.
- Twee sterke draaideur-instanties toegevoegd (Berghuis, Wester) — precies het propaganda-model-relevante
  materiaal (politiek/PR ↔ journalistiek).
