# Scout-ronde: sterkste routes r2 — officiële bronnen & voorlichtingsmacht (Sourcing)

- **Datum:** 2026-07-04
- **Account:** assistent (bijdrager)
- **Git-hash bij aanvang:** de441f1
- **Opdracht:** eigenaar — "Doe gedegen onderzoek en probeer 100 relaties en entiteiten te
  vinden gebaseerd op de sterkste routes" (Sourcing veruit sterkst per `onderzoek/`).
- **Scope r2:** de voorlichtingsmacht van de Rijksoverheid als structurele nieuwsbron: RVD,
  VoRa, ministeries (Financiën/J&V/VWS/LNV/AZ), OM, WODC.
- **Tooling:** `scripts/scout_indienen.py` (nieuw; generieke manifest-orkestratie, geen inhoud)
  + manifest `data/scout/sterkste-routes-r2.json`. Alles via REST-API, alles `voorgesteld`.
- **Werkwijze:** webresearch-agent (queries hieronder) → quotes verbatim geverifieerd via fetch
  (kernquotes 851,7 fte / OM-Aanwijzing / VWS-Nieuwsuur nogmaals eigenhandig herfetcht) →
  manifest → droogloop → indienen.

## Queries (letterlijk, research-agent)

1. Binnenlands Bestuur communicatiekorps Rijksoverheid 852 fte woordvoerders
2. RVD mediacode koninklijk huis sancties berichtgeving
3. Voorlichtingsraad VoRa coördinatie overheidscommunicatie ministeries
4. Prinsjesdag embargo stukken media Ministerie van Financiën afgeschaft
5. persofficier OM misdaadjournalistiek afhankelijkheid persberichten politie onderzoek
6. koninklijkhuis.nl tekst mediacode Rijksvoorlichtingsdienst "mediacode"
7. Mirjam Prenger "Gevaarlijk spel" voorlichting journalistiek AMB 2010
8. VWS Wob-verzoeken corona journalisten dwangsom rechter traag
9. embargoregeling Prinsjesdag 2024 2025 journalisten miljoenennota vrijdag onder embargo
10. OM "Aanwijzing voorlichting opsporing en vervolging" persvoorlichting persofficier media
11. ministerie Justitie en Veiligheid Woo-verzoeken traagste journalisten NVJ kritiek afscherming
12. WODC-affaire Nieuwsuur ministerie Justitie beïnvloedde onderzoek 2017
13. "Gevaarlijk spel" Prenger aantal voorlichters communicatieprofessionals tegenover journalisten verhouding
14. ministerie LNV stikstof documenten achtergehouden journalisten Woo
15. ministerie EZK Groningen gaswinning documenten Woo journalisten Follow the Money achtergehouden
16. lockup journalisten Prinsjesdag ministerie Financiën technische briefing embargo stukken ochtend
17. ministerie SZW "Infrastructuur en Waterstaat" journalisten Woo-verzoek traineren kritiek voorlichting

## Geoogst (9 entiteiten, 14 relaties, 23 argumenten, 14 bronnen waarvan 1 hergebruikt)

| Relatie | Mechanisme | rel-id | Kernbron |
|---|---|---|---|
| Min. AZ → RVD (eigendom) | kandidaat | 1124 | koninklijkhuis.nl (#767) |
| RVD → Koningshuis (woordvoerder_van) | kandidaat | 1125 | koninklijkhuis.nl, KB 1965 (#767) |
| RVD → VoRa (bestuurder: DG RVD = voorzitter) | kandidaat | 1126 | rijksoverheid.nl (#766) |
| Min. Financiën → NOS (bron_van) | bron_afhankelijkheid (6) | 1127 | parlement.com embargo (#769) + Villamedia 2013 (#770); óók contradicting: persembargo sinds 2011 afgeschaft (#1578) |
| Min. Financiën → ANP (bron_van) | bron_afhankelijkheid (6) | 1128 | parlement.com (#769) |
| Min. Financiën → FD (bron_van) | bron_afhankelijkheid (6) | 1129 | parlement.com (#769) |
| Min. J&V → Nieuwsuur (intimidatie) | statelijke_bronnenjacht (159) | 1130 | NOS/Nieuwsuur WODC-tap (#771) |
| Min. J&V → WODC (beinvloeding) | institutionele_gezagsketen (168) | 1131 | NOS/Nieuwsuur (#771) |
| Min. VWS → Nieuwsuur (censuur) | woo_obstructie (32) | 1132 | NOS (#773, rechter: werkwijze onwettig) + Villamedia €677k dwangsommen (#772) |
| Min. LNV → NRC (beinvloeding, 'smoor-check') | kandidaat | 1133 | SchipholWatch (#774, **grijs**; kracht zit in Woo-stukken open.overheid.nl) |
| OM → NOS / De Telegraaf / AD / ANP (bron_van) | bron_afhankelijkheid (6) | 1134–1137 | OM-Aanwijzing 2020A004 (#775, primair) |

Entiteiten: RVD #581 (rol voorlichter), Min. AZ #582, VoRa #583 (voorlichter), Min. Financiën #584,
Min. J&V #585, Min. VWS #586, Min. LNV #587, OM #588 (allen gezagsinstituut), WODC #589 (kennisinstituut).

Losse argumenten op de theorielaag (NL-onderbouwing):
- mech 91 institutionele_voorlichting: 851,7 fte 2022, +34% in 5 jaar (#1590, Binnenlands Bestuur #777)
  + **influence-argument**: 942,1 fte per 1-1-2026 (#1591, Rijksoverheid #778).
- mech 9 pr_subsidie: PR-sector orde van grootte groter dan journalistiek (#1592, Villamedia #33,
  hergebruikte bron; claim bewust als *ordegrootte* geformuleerd — de precieze 10-op-1-ratio is betwist).
- mech 48 voorlichter_informatiefilter: RVD-mediacode = toegang in ruil voor volgzaamheid (#1593, #768).
- mech 6 bron_afhankelijkheid: misdaadjournalisten over persberichten als sturingsinstrument (#1594, VVOJ #776).

Stance-balans deze ronde: 22 supporting, 1 contradicting (persembargo afgeschaft, #1578 op rel 1127).
De tegenbewijs-zware flak-ronde (r4) compenseert de balans missie-breed.

## Modelleerkeuzes
- **Granulariteits-litmus RVD:** eigen knoop want voorlichtingsmechanismen (48/149/91) grijpen op
  RVD-niveau; AZ→RVD als beschrijvende `eigendom`-kandidaat (precedent rel 704/705 instelling→opleiding).
- Ministerie→media-edges volgen de bestaande huisconventie (RIVM→NOS-reeks): arrangement-niveau bewijs
  (embargo, Aanwijzing) op de 2-4 outlets waar het domein aantoonbaar loopt; geen bredere fan-out.
- Financiën-embargo eerlijk gemodelleerd: supporting (50 jaar geïnstitutionaliseerd) én contradicting
  (sinds 2011 afgeschaft) op dezelfde relatie — de DF-QuAD-boom weegt beide.
- VWS-edge kreeg `censuur` als relatietype (informatie-achterhouden); mechanisme woo_obstructie (32) is
  leidend, reviewer kan het type verfijnen.
- Geen certainty/influence gezet (0,05-vloer); wél één property='influence'-argument (mech 91).

## Negatief / niet ingediend (alleen hier, niet als modelinhoud)
- **EZK, SZW, I&W:** geen hard bewijs van bronmacht-richting-media gevonden (queries 15/17); de best
  vindbare EZK-casus documenteert juist coöperatieve Woo-afhandeling. Niet opgevoerd.
- **J&V als "traagste Woo-ministerie":** niet als losse claim te staven; J&V-bronmacht loopt via de
  WODC-affaire.
- **Prinsjesdag-lockup voor journalisten (2024–2026):** niet te staven; persembargo is sinds 2011 weg
  (de aanname "afgeschaft in 2021" uit de missievoorbereiding klopte niet — het was 2011).
- **Prenger "Gevaarlijk spel" (SVDJ-PDF):** PDF niet tekst-leesbaar; het kerncijfer is via Villamedia
  2018 (#33) gestaafd, de PDF-locator laten liggen voor de documentalist.
- **Mediacode-tekstpagina koninklijkhuis.nl:** 404 bij fetch; sanctie-quote gestaafd via het officiële
  2005-nieuwsbericht (#768).
- **Aantallen voorlichters pér ministerie:** uitsplitsing zit in een niet-leesbare bijlage (2026-overzicht).

## Vervolg
- r1 (media-economen) wacht op research-agent; r3 (talkshows), r4 (flak), r5 (transnationaal),
  r6 (draaideur) zijn onderzocht en volgen als eigen manifests + logs.
