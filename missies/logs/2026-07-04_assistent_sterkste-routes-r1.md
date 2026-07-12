# Scout-ronde: sterkste routes r1 — de media-economen-elite (Sourcing)

- **Datum:** 2026-07-04
- **Account:** assistent (bijdrager)
- **Git-hash bij aanvang:** de441f1
- **Opdracht:** eigenaar — "100 relaties en entiteiten langs de sterkste routes"; dit is het
  economen-deel van de Sourcing-route (onderzoek: smalle expert-/economen-elite = 'primary definers').
- **Scope r1:** de klassieke top-5 media-economen (Tuk 2014, 2008-2013) + de actuele generatie
  (bank-hoofdeconomen en institutionele duiders, 2020-2026), met affiliaties en partijbanden.
- **Tooling:** `scripts/scout_indienen.py` + manifest `data/scout/sterkste-routes-r1.json`.
- **Kernbron:** Tuk-scriptie-PDF (115 p.) via Wayback gedownload en integraal tekst-geëxtraheerd
  (pypdf); quotes verbatim uit de PDF. Wikipedia geldt als vindplaats (klasse-voorstel grijs);
  primaire bronnen (DNPP, NOS, uitgevers) waar beschikbaar.

## Queries (letterlijk, research-agent)

WebSearch: (1) Yoshi Tuk "media-economen" scriptie Leiden · (2) "dominante elite van media-economen" Tuk ·
(3) Tuk media-economen "28 procent" Eijffinger Bovenberg Hoogduin Boot Wijnbergen nevenfuncties ·
(4) Lex Hoogduin Wikipedia DNB directeur hoogleraar Groningen · (5) Eijffinger CDA lid
verkiezingsprogramma commissie · (6) "Eijffinger" "CDA-econoom" OF "CDA'er Eijffinger" ·
(7) Marieke Blom hoofdeconoom ING sinds media · (8) Coen Teulings columnist column krant FD NRC ·
(9) Teulings FD column 2025 · (10) dnpprepo Eijffinger CDA rapport wetenschappelijk instituut ·
(11) "Van Mulligen" "Met ons gaat het nog altijd goed" boek hoofdeconoom CBS · (12) Arnoud Boot BNR
vaste gast economenpanel · (13) "Macro met Boot en Mujagić" podcast wekelijks BNR beschrijving ·
(14) site:nos.nl "hoofdeconoom" "Van Mulligen" CBS · (15) Sandra Phlippen hoofdeconoom ABN AMRO 2026
column AD · (16) Lex Hoogduin EW-blog wekelijks OF BNR vaste econoom 2025. Plus Wayback-CDX-queries
voor de verdwenen yoshituk.nl-PDF.

## Geoogst (13 entiteiten #590-602, 32 relaties #1138-1169, 35 argumenten, 19 bronnen #779-797)

**Kern-bevinding (Tuk 2014, 11 dagbladen 2008-2013, 12.828 vermeldingen):** 5 economen = 28% van de
artikelen met een academisch econoom; 12 = 51%; 9 van de 10 populairste had commerciële/politieke
banden. Als losse supporting args op mechanisme 87 (expert_legitimatie) gezet.

| Persoon | node | Affiliaties (rel-ids) | Media-anker | Partijband |
|---|---|---|---|---|
| Sylvester Eijffinger | #590 | Tilburg U (1138, tot 2020) | De Telegraaf (1140), Metro (1141), m87 | CDA (1139, partijlijn; Tuk + WI-CDA-rapport DNPP) |
| Lans Bovenberg | #591 | Tilburg U (1142) | — (Tuk-vermeldingen) | CDA (1143, partijlijn) |
| Sweder van Wijnbergen | #592 | UvA (1144) | — | PvdA tot 2015 (1145) |
| Lex Hoogduin | #593 | DNB-directie tot 2011 (1146), RUG (1147) | — (EW-blogs: paywall, niet gestaafd) | geen |
| Arnoud Boot | #594 | UvA (1148), WRR 2013-23 (1149), DNB-Bankraad (1150) | BNR 'Macro' (1151, m87) | geen |
| Mathijs Bouman | #595 | — | FD-column (1152), Nieuwsuur-redacteur (1153), RTL Z (1154, m87) | geen |
| Barbara Baarsma | #596 | UvA (1155), Rabobank 2016-23 (1156), PwC (1157) | Op1 e.a. talkshows (1158, m87) | geen |
| Coen Teulings | #597 | CPB 2006-13 (1159) | NRC-column 2013-17 (1161) | PvdA-beginselprogramma 2004 (1160, adviseur) |
| Sandra Phlippen | #598 | ABN AMRO (1162), **RvC NRC Media (1164)** | AD-column (1163) | geen |
| Marieke Blom | #599 | ING (1165) | Nieuwsuur/Jinek/Op1 (1166, m87) | PvdA-adviseur, verleden (1167) |
| Peter Hein van Mulligen | #600 | CBS (1168) | via CBS→NOS (1169, m6) | geen |

Nieuwe org-nodes: Tilburg University #601 (kennisinstituut), CBS #602 (gezagsinstituut).
Structurele bijvangst: **Phlippen (hoofdeconoom ABN AMRO) in de RvC van NRC Media** (rel 1164,
managementscope-locator) — direct bank↔krant-verband, apart onderzoek waard.

## Modelleerkeuzes
- Affiliaties mechanisme-loos (kandidaat), conform personen-r1-conventie; partijbanden op
  `partijlijn` (92, precedent rel 336); media-optredens als expert = `expert_legitimatie` (87,
  precedent rel 325 Van Rossem→Volkskrant); columnist/redacteur bij eigen outlet = `personeel`.
- Van Mulligen bewust géén m87-edge naar NOS: hij spreekt als institutionele woordvoerder van het
  CBS — dat is bron_afhankelijkheid (CBS→NOS, rel 1169, m6), een ander Sourcing-subtype.
- Richting-waarschuwing gerespecteerd: partijbanden zijn feiten over personen (CDA×2, PvdA×3 in
  wisselende periodes), geen "media zijn links/rechts"-claim.
- Baarsma-Rabobank en Phlippen-RvC-NRC: bron-met-locator zonder quote (parafrase in bron, geen
  verbatim zin beschikbaar) — de citatiepoort accepteert een locator; quotes nooit gefabriceerd.

## Negatief / niet ingediend
- **Eijffinger CDA-lidmaatschap uit een directe niet-Tuk-bron:** nd.nl/rtl.nl-bevestigingen niet
  fetchbaar; gestaafd via Tuk-PDF + WI-CDA-rapport (DNPP).
- **Teulings als actuele FD-columnist (2020-2026):** fd.nl-auteurspagina achter paywall — alleen de
  NRC-periode (TPO-bron) ingediend.
- **Hoogduin structureel EW-anker:** alles achter Roularta-paywall; niet ingediend.
- **Blom als krantencolumnist / Phlippen vaste RTL Z-rol / Bovenberg CPB-verleden:** niet gestaafd.
- **Universiteit Utrecht (Teulings), Netspar, SEO:** entiteiten weggelaten — geen mechanisme grijpt
  daar aantoonbaar (granulariteits-litmus); CPB-affiliatie is de dragende.

## Twijfelgevallen (bewust conservatief gemodelleerd)
- Hoogduin DNB-startjaar (2008 of 2009): alleen einddatum (1-7-2011) gezet.
- Van Mulligen "sinds 2012" (Managementboek verbatim) boven "sinds 2010" (Wikipedia-parafrase).
- Baarsma "voorzitter Bankraad DNB": te zwak gedocumenteerd — weggelaten.
