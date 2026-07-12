# Missielog — Advertentie-filter verdiepen (3 assen)

**Datum:** 2026-07-07
**Account:** `assistent` (bijdrager)
**Aanleiding:** eigenaar vroeg "wat kunnen we nog meer voor verbanden/entiteiten vinden?" → dekkingsanalyse
wees Advertentie aan als dunste kernfilter (10 adverteerders, alle retail/loterij). Eigenaar koos drie assen.
Alles ingediend als `voorgesteld` (instantielaag → één menselijke reviewer). Geen RfC's — alles hangt onder
bestaande mechanismen.

## As 2 — Staat als top-adverteerder
- **Bron 989:** DPC *Jaarevaluatie campagnes Rijksoverheid 2024* (21 mei 2025, ref. 8236301), open.overheid.nl.
  Verbatim: "De totale mediabestedingen aan publieksvoorlichting bedroegen in 2024 € 35,3 miljoen."
- **Relatie 1395:** Ministerie van Algemene Zaken → DPG Media, `commerciele_afhankelijkheid` (#4).
- **Arg 1920 (supporting):** de staat is met €35,3 mln campagne-inkoop zelf een substantiële adverteerder.
- **Arg 1921 (contradicting/confound):** hefboom op dagbladredactie begrensd — leeuwendeel naar online
  (€17,6 mln) en radio/tv (€9 mln), slechts €1,5 mln naar print. Zelfde DPC-bron (media-typeverdeling).
- **Modelbeslissing:** `staatsreclame_exploitatie` (#101) bleek NIET te passen (filter eigendom,
  belanghebbende→omroepkoepel, Ster→OCW-opbrengstenlus). Gecorrigeerd naar #4. DPC niet als aparte entiteit
  (granulariteits-litmus: het advertentie-mechanisme grijpt op staatsniveau → AZ volstaat). Géén "top-adverteerder"-
  ranking geclaimd: NDP/Nielsen lijsten zijn bruto rate-card, appels/peren met DPC's netto €35 mln.

## As 3 — Adverteerdersdruk-incidenten (twee gecontrasteerde gevallen)
**Geval A — GeenStijl/Dumpert-boycot (mei 2017), advertentiedruk die WERKT tegen een kleine outlet:**
- **Bron 990:** MarketingTribune, "Adverteerders boycotten seksistisch GeenStijl" (4 mei 2017).
- **Bron 991:** NOS, "Ministers steunen boycot GeenStijl" (7 mei 2017).
- **Entiteit 755:** Koninklijke Grolsch (grote vaste adverteerder; HAK/WNF/KWF/De Persgroep in de argumenttekst).
- **Relatie 1396:** Grolsch → GeenStijl, `advertentiedruk` (#3).
- **Arg 1922 (supporting):** boycot om DumpertReeten (MarketingTribune, verbatim adverteerdersnamen).
- **Arg 1923 (contradicting/confound):** content was aantoonbaar seksistisch → deels legitieme brand-safety,
  geen viewpoint-onderdrukking (begrenst de flak-lezing).
- **Arg 1924 (contextual/duiding):** ministeriële steun (Bussemaker/Schultz) — advertentiedruk viel samen met
  establishment/flak-druk. Contextual = telt niet in de score, maar legt de dimensie eerlijk vast.

**Geval B — #StopHateForProfit Facebook-boycot (juli 2020), advertentiedruk die MISLUKT tegen een platform:**
- **Bron 992:** NOS, #StopHateForProfit (29 juni 2020). **Bron 993:** Adformatie, "Maand van Facebook-boycot
  voorbij" (3 aug 2020).
- **Relatie 1397:** Unilever → Meta, `advertentiedruk` (#3). (Unilever + Meta bestonden al.)
- **Arg 1925 (supporting):** merken (Unilever/Coca-Cola/Starbucks/North Face) trokken terug om racisme/haatzaaien.
- **Arg 1926 (contradicting/confound):** boycot vrijwel effectloos — FB-advertentie-inkomsten +~10% j-o-j,
  Zuckerberg weigerde contentbeleid te wijzigen. **Contrast met geval A:** de hefboom bijt bij een kleine outlet,
  niet bij een platform-monopolie.

## As 1 — Advertentie-infrastructuur (media-buying/brand-safety-laag)
- **Bron 994:** AdExchanger, "Keyword Blocking Demonetized More Than Half Of Reuters' Brand-Safe Stories"
  (6 apr 2026). Verbatim: 54% van veilige Reuters-nieuws-URL's zou een blocklist triggeren; Stagwell-studie
  schatte $2,8 mld schade voor Amerikaanse uitgevers (2019).
- **Entiteit 756:** GroupM (WPP; grootste mediabureau ter wereld). Buying-oligopolie (Publicis/Dentsu/Omnicom/
  Havas) in de argumenttekst.
- **Relatie 1398:** GroupM → DPG Media, `supportive_selling_environment` (#5).
- **Arg 1927 (supporting):** brand-safety-keyword-blocklists demonetiseren harde nieuwscontent op grote schaal;
  dezelfde programmatic-keten raakt NL commerciële nieuwssites.
- **Arg 1928 (contradicting/confound):** industrie verschuift naar contextuele/AI-tools (IAS) die onterecht
  geblokkeerd nieuws terugwinnen — disciplinering reëel maar niet statisch.
- **Bron-eerlijkheid:** cijfers zijn US/globaal (onderwerp `algemeen`); claim eerlijk geframed als een globale
  ad-tech-dynamiek die ook NL programmatic-inventory raakt.

## Negatieve / niet-ingediende resultaten (bewijs van brede search)
- **Meetlaag (SKO/NMO) NIET ingediend:** al gemodelleerd via **NMO (entity 177)** met de volledige joint-
  industry-structuur (NPO/DPG/RTL/Talpa/Unilever/AS Watson → NMO als bestuurder) en kijkcijfer-edges
  (`kijkcijferdisciplinering` #160, publiek→redactie). SKO aanmaken zou dupliceren.
- **Overige mediabureaus (Dentsu/Publicis/Havas/Omnicom) niet als losse entiteiten:** één coördinatie-/
  systeem-fenomeen → géén N bijna-identieke edges (proliferatie-discipline). GroupM als vlaggenschip; de rest
  in prozatekst. Een reviewer kan later besluiten de oligopolie voller te representeren.
- **Andere NL-adverteerdersboycots (2020-2022) tegen binnenlandse outlets:** search leverde vooral de
  GeenStijl-casus (2017) en de Facebook-boycot (2020, platform) op; geen tweede hard-gesourcet geval van een
  adverteerder die budget terugtrok bij een *Nederlandse* krant/omroep om redactionele inhoud. Niet ingediend.

## Verificatie
`scripts/validate_model.py --strict` → EXIT 0, golden snapshot groen, geen fouten boven baseline (alles
`voorgesteld`, telt in niets). Elk supporting/contradicting-root draagt ≥1 echte citatie (quote); geen
`ongesourcet_root`. Wacht op menselijke review/merge.

**Update — alle drie assen gemerged via admin (maxime):** entiteiten 755/756, relaties 1395–1398, argumenten
1920–1928. Validatie na merge groen.

## Vervolgronde — koopkrachtselectie (#176) als klasse-bias (op verzoek eigenaar)
Eigenaar: "koopkrachtselectie + SCP-klassen is heel belangrijk, mits het klopt — hier moet wél bewijs voor zijn."
Mechanisme #176 had **0 argumenten**. Nu gegrond (gemerged via admin):
- **M1 (arg 1937):** H&C, *Manufacturing Consent* (bron 2, hergebruik) — "audiences with buying power... affluent
  audiences", "a voting system weighted by income", adverteerders = "de facto licensing authority".
- **M2 (arg 1938):** empirie Daily Herald (Curran & Seaton via openDemocracy/Sinclair, bron 1016) — 4,7 mln
  lezers, 8,1% oplage, maar 3,5% advertentie-inkomsten → failliet want publiek "little purchasing power".
- **Instanties (AH → outlet, #176):** Metro (rel 1400, historisch tot 2023-10, bron TMG 1017), NU.nl (1401),
  RTL Nieuws (1402); NU.nl/RTL geciteerd op H&C.
- **/onderzoek:** voorspelling **#6** (deadline 2027-12-31, verankerd aan #176): NL-nieuws bedient onderste
  inkomens-/opleidingsklassen onder hun bevolkingsaandeel; meetcriterium ≥10 procentpunt (SCP/Reuters/inhoudsanalyse).
- Resultaat: #176 geloofwaardigheid 0 → ~0,47 (literatuur 0,41; 3 instanties, 2 bronnen). `validate --strict`
  EXIT 0, agenda hergenereerd. **Openstaand:** NL-specifiek uitkomstbewijs (SCP) ontbreekt nog — dát is de
  onderzoeksvraag (voorspelling #6), niet gefabriceerd als model-claim.
- **Metro-nuance:** doelgroep was jóng/forens (advertentie-lucratief), niet expliciet 'rijk'; de klasse-bias
  zelf leunt op H&C + Herald, niet op Metro.

### Aanvulling 2 (zelfde ronde) — NL-affluentie-instantie + scope-begrenzing (gemerged via admin)
- **NRC-instantie (rel 1412, arg 1956):** AH → NRC (#176), bron = NRC-mediakit (1027, primair): *"De NRC-lezer is
  hoogopgeleid en kapitaalkrachtig en bevindt zich bovengemiddeld vaak in sociale klasse AB1."* Repareert Metro's
  zwakte: de kwaliteitspers floreert dóór welgesteld publiek te selecteren (keerzijde van de arme-massa-outlet).
- **Scope-begrenzing (contextual arg 1957 op #176):** publieke omroep (NPO ~92% OCW) ontsnapt aan koopkracht-
  selectie → klasse-brede tegenkracht. Contextual = doet niets in de score, dampt het mechanisme dus niet (correct:
  het mechanisme is wáár waar het geldt; dit begrenst enkel de scope). #176 nu 4 instanties, geloofw. ~0,48.
- **Niet ingediend (eerlijk):** Reuters DNR NL / SCP nieuwsgebruik-naar-opleiding — CvdM-bron gaf socket-hang-ups,
  géén verbatim → niet gefabriceerd; hoort bij het toetsen van voorspelling #6. `validate --strict` EXIT 0.
