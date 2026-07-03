# Missielog — funding-edges & inkomstensamenstelling (assistent, 2026-07-02)

**Aanleiding.** De eigenaar miste de inkomstenbron-donut bij PAX en andere organisaties.
Twee sporen: (1) codewijziging — het paneel wordt nu al zichtbaar zodra een entiteit een
inkomende `financiering`-edge heeft, ook zonder gemeten aandeel ("?%", zie
`scoring.compute_income_composition`, veld `onbekend`); (2) de ontbrekende funding-edges
zelf aanmaken, gesourcet, via het bijdragepad.

## Onderzoek (webresearch, 2 rondes + 1 herstart)

- **NPO-keten** — NPO Jaarverslag 2024 (PDF, direct geëxtraheerd), Mediabegrotingsbrief
  2026 (OCW, 14-11-2025), Rijksoverheid "Welke omroepen zijn er?".
- **FPU/PAX** — FPU Annual and Financial Report 2024 (percentage 40,5% staat in de bron
  zelf), PAX Jaarverslag & jaarrekening 2024 (noot 18 + staat van baten en lasten).
- **Wfpp-partijsubsidies** — eerste poging strandde op een sessielimiet; herstart loopt
  (edges BZK→partijen en partij→wetenschappelijk bureau volgen zodra bronnen binnen zijn).

## Ingediend (alles `voorgesteld`, account `assistent`)

- **Bronnen 305–309**: NPO Jaarverslag 2024, Mediabegrotingsbrief 2026, Rijksoverheid
  "Welke omroepen", FPU Annual Report 2024, PAX Jaarverslag 2024 (alle met url-locator +
  classificatievoorstel).
- **Relatie 678** OCW→NPO (`financiering`, **kandidaat** — geen bestaand mechanisme dekt
  "staat financiert omroepkoepel"; t.z.t. RfC `rijksmediafinanciering` of adoptie
  overwegen). Argumenten 914 (bewijs: €988,0 mln OCW-vergoedingen 2024) en 915
  (`inkomensaandeel` **92:2024** — eigen berekening 988,0/1.073,6 mln, beide bedragen
  verbatim in de bron).
- **Relaties 679–690** NPO→{NOS, NTR, AVROTROS, BNNVARA, EO, KRO-NCRV, Omroep MAX, VPRO,
  WNL, PowNed, Ongehoord Nederland, Omroep ZWART} (`financiering`, mechanisme
  `bestelsturing`; ON/ZWART met `active_from` 2022-01-01). Argumenten 916–927, elk met
  het GoS-verdeelcitaat uit het NPO-jaarverslag; ON/ZWART extra met het
  "voorlopige erkenning"-citaat van Rijksoverheid.nl.
- **Relatie 691** BuZa→Free Press Unlimited (`financiering`, mechanisme
  `denktank_financiering_bias`, consistent met BuZa→PAX rel. 469). Argumenten 928
  (bewijs: langjarig donor, Power of Voices → Reporters Respond), 929 (financiële
  afhankelijkheid; herschreven — zie correctie hieronder) en 931 (`inkomensaandeel`
  **40.5:2024**, percentage uit de bron zelf).
- **Argument 930** op bestaande rel. 469 (BuZa→PAX): `inkomensaandeel` **53.6:2024**
  (BuZa-direct: PoV + WPS + ambassades = €9.496.297 op €17.725.173; alle
  overheidssubsidies samen 83,6%).

**Correctie tijdens de missie:** argument 929 was bedoeld als aandeel-argument maar het
script vergat `property` mee te geven; het property-type ligt vast na aanmaak, dus 929 is
per PATCH herschreven tot gewoon bewijsargument en het aandeel is opnieuw ingediend als
931. Leerpunt voor volgende indienscripts: property-velden verifiëren in de response.

## Eerlijke meldingen (niet hard te maken / voorbehouden)

- De letterlijke wettekst van **Mediawet art. 2.152** (raad van bestuur verdeelt de
  budgetten) is niet verbatim geverifieerd (bron onbereikbaar); de jaarverslag-citaten
  dragen de claim zelfstandig.
- Het **PAX-jaarverslag 2024** draagt een concept-watermerk; het CBF-paspoort wijkt ±0,2%
  af op de totalen. In het argument zelf gemeld.
- **FPU 40,5%** betreft de donorcategorie "Dutch Government" (BuZa-HQ + Nederlandse
  ambassades — ambassades vallen onder BuZa). In het argument zelf gemeld.
- De **92%** (OCW→NPO) betreft de NPO-exploitatierekening; eigen leden-inkomsten van
  omroepverenigingen lopen daar niet doorheen. In het argument zelf gemeld.
- Uitkomst van de aangekondigde ON-evaluatie (voorjaar 2026) niet gevonden; de erkenning
  is in elk geval niet ingetrokken (besluit dec. 2023 + vermelding als voorlopig erkend).

## Ronde 2: Wfpp-partijsubsidies (zelfde dag, na herstart van de onderzoeksagent)

- **Bronnen 310–313**: Dashboard partijfinanciering (BZK, gelanceerd 20-05-2026), Wfpp
  (BWBR0033004, geldend 2025-01-01), Over de WBS (wbs.nl), parlement.com
  "Wetenschappelijk bureau politieke partij".
- **Relaties 692–699** BZK→{VVD, D66, NSC, GroenLinks, PvdA, CDA, SP, FvD}
  (`financiering`, **kandidaat** — mechanisme `partijfinanciering` (112) dekt privégiften,
  niet staatssubsidie; t.z.t. RfC overwegen). Argumenten 932–939 met per partij het
  uitgekeerde 2024-bedrag uit het BZK-dashboard + Wfpp art. 7 (ledeneis) als grondslag.
- **Relaties 700–701** VVD→Teldersstichting en PvdA→Wiardi Beckman Stichting
  (`financiering`, mechanisme `denktank_financiering_bias`). Argumenten 940–941 met
  Wfpp art. 8 lid 1 sub b (geoormerkt bedrag) + art. 9 lid 1 (doorbetaalplicht) +
  WBS-eigen-opgave resp. parlement.com-koppeling.
- **Negatief resultaat (bewust NIET ingediend):** (1) géén BZK→PVV-edge — de PVV voldoet
  niet aan de 1000-ledeneis en ontbreekt in de subsidietabel (ProDemos/Montesquieu:
  ~€2 mln/jaar misgelopen); (2) de aanname "FvD zag in 2021 af van subsidie" bleek na
  ~10 gerichte zoekopdrachten onvindbaar én weerlegd door het BZK-dashboard (FvD ontving
  €1,73/€1,84/€1,75 mln in 2022/2023/2024) — die claim is dus geschrapt, FvD kreeg een
  gewone subsidie-edge. (3) De wet-art.-8-bedragen zijn geïndexeerd; de geciteerde versie
  is de geldende per 2025-01-01.

## Review-ronde (2026-07-03, `maxime` via admin — op expliciete aanwijzing van de eigenaar: "review het zelf maar met admin")

- **Steekproef vooraf:** de twee webfetch-gemarkeerde quotes zijn tegen de live bron
  naverifieerd — Wfpp art. 7 (wetten.overheid.nl) en "Er zijn nu 2 omroepen met een
  voorlopige erkenning: Ongehoord Nederland en Omroep Zwart" (rijksoverheid.nl): beide
  verbatim correct. De PDF-quotes waren al direct geëxtraheerd door de onderzoeksagent.
- **Gemerged:** argumenten 914–941 (status `ongecontroleerd` — gesourcet, nog niet
  onafhankelijk gecontroleerd).
- **Goedgekeurd:** relaties 679–691 (NPO→omroepen, BuZa→FPU), 700–701
  (partij→wetenschappelijk bureau) — alle met mechanisme + gesourcet root-argument.
- **Bewust `voorgesteld` gelaten (kandidaten):** 678 (OCW→NPO) en 692–699
  (BZK→partijen) — de orphan-poort weigert goedkeuring terecht zolang er geen
  theorie-element voor staatssubsidie bestaat. Vervolgstap: RfC `staatssubsidie`
  (of vergelijkbaar) die deze negen adopteert.
- **Bronclassificaties bevestigd (305–313)** met één correctie op het voorstel van
  `assistent`: jaarverslagen (305, 308, 309) en de WBS-site (312) als `institutioneel`
  i.p.v. `primair` — de type↔klasse-poort staat `primair` alleen toe op
  dataset/wetgeving/transcript/interview/persbericht/overig, niet op rapport/website.
  Wettekst (311) wél `primair`; parlement.com (313) `regulier`; alles `nl_systeem`.
- Golden snapshot en `validate_model.py --strict` na afloop groen.

## Openstaand
- Aandeel-argumenten voor de overige "?%"-financiers (o.a. SVDJ→De Groene/Vrij
  Nederland/Vers Beton/Bureau Spotlight/Spot On Stories, SDM→ontvangers, ministeries→
  Clingendael/HCSS, EIB/Google→DPG) — zelfde recept: jaarverslag zoeken, percentage
  berekenen of citeren, `inkomensaandeel`-argument op de edge.
