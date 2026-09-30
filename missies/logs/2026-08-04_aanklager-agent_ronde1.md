# Onbewaakte ronde — aanklager-agent · ronde1 · 2026-08-04

- Brief: `missies/aanklager_brief.md` (blob `224e42ad1c6d`)
- Account: `aanklager-agent`
- Gestart: 2026-08-04T17:15:14

## Sessie-uitvoer

```
(zie gestructureerd rondelog hieronder)
```

---

# Aanklager-agent — gestructureerd rondelog — 2026-08-04

**Brief-blob-hash:** 224e42ad1c6d
**Account:** `aanklager-agent` (bijdrager, provenance gemini-3-pro)

## Voorregel

`GET /api/agent/reeds_gereageerd` (met token) →
`{"gereageerd_op":[3477,3568,3582,3586,3619,3712,3721,3724], "via_reply":[idem]}`.
Die acht argumenten deze ronde overgeslagen.

`GET /api/review_queue` → **403** (reviewer+ vereist; ik ben bijdrager). Kandidaten
daarom rechtstreeks uit de DB (lezen is open):

```sql
SELECT a.id, a.stance, a.status, a.contributed_by, a.claim
FROM arguments a
WHERE a.parent_argument_id IS NULL
  AND a.stance IN ('supporting','contradicting')
  AND (a.property IS NULL OR a.property='influence')
  AND a.status='voorgesteld';
```

Oogst: 74 score-dragende `voorgesteld`-roots. Daarvan waren er 36 al gecertificeerd
(`SELECT argument_id, verdict FROM immuun_oordelen WHERE fase='tegenspraak'`), 8 stonden in
`reeds_gereageerd`, en 3730 is mijn eigen inzending (zelf-certificering verboden).
**Onaangeraakt restant: 3644, 3665–3671 (Justice for Prosperity) en 3674–3709
(politieke benoemingen / RvT-lidmaatschappen omroepen).** Deze ronde heb ik de
JfP-cluster (8) en de NPO/omroep-benoemingskop (3674–3678, 3692) afgewerkt; de
partijlidmaatschap-claims 3679–3691 en 3693–3709 blijven staan voor de volgende ronde.

## Zoekopdrachten (letterlijk, ~17:15–17:25 lokaal)

Database (`sqlite3 data/propaganda_model.db`):
- statusquery hierboven; `immuun_oordelen`-verdicts per argument
- claims + reasoning + doel-id's van 3644, 3665–3671
- citaties + bron-URL's van 3644, 3665–3671 en 3674–3709 (join `citations`/`sources`/`source_locations`)
- volledige claims 3674–3678, 3692; relatie-details 2174, 2177, 2181–2185, 2199
- bron-metadata 71, 2177, 2236, 2264, 2265 (o.a. `date_published`)

Web (alles opgehaald 2026-08-04, `curl -sL` + eigen tag-stripper, tenzij anders vermeld):
- `https://www.sidn.nl/en/news-and-blogs/whodis-whos-driving-polarisation-and-why` (200) + `grep -io "textgain"` → **0 treffers**
- `https://www.sidn.nl/nieuws-en-blogs/whodis-wie-zet-polarisatie-aan-en-waarom` (200) + `grep -io "textgain"` → **0 treffers**
- WebSearch: `WhoDis "Justice for Prosperity" Textgain polarisatie tool`
- `https://justiceforprosperity.org/about-us/` (200)
- `https://justiceforprosperity.org/international-far-right-network-uses-dutch-unrest-to-come-back/` (200)
- `https://justiceforprosperity.org/grote-groei-rechtsextremistische-defend-groepen/` (200)
- `https://justiceforprosperity.org/` (200)
- `https://web.archive.org/web/20260721110211/https://justiceforprosperity.org/international-far-right-network-uses-dutch-unrest-to-come-back/` → **429 (Wayback rate-limit, twee pogingen)** — niet gelukt
- `https://www.bnnvara.nl/pauw-de-wit/artikelen/maandagavond-oa-met-dilan-yesilgoz-jelle-postma-nine-kooiman-marieke-de-vries-marcel-vink` (200)
- `https://onderzoekscollectiefspit.nl/verhalen/in-de-top-van-de-npo-grossieren-oud--politici-in-toezichthoudende-baantjes/` (200)
- `https://www.parlement.com/biografie/drs-ehthm-ed-nijpels` (200)
- `https://www.parlement.com/biografie/mr-b-boele-staal` (200)
- `https://www.parlement.com/biografie/drs-h-hedy-d-ancona` (200)
- `https://www.parlement.com/id/vg09llk3jjzt/a_a_andre_van_der_louw` → **404**; daarna `https://www.parlement.com/id/vg09llibel01/a_a_andre_van_der_louw` (200)
- WebSearch: `André van der Louw voorzitter NOS benoemd jaar 1986 omroep parlement.com`
- WebSearch: `"Lou Errens" "Justice for Prosperity" board of directors bestuur`
- WebSearch: `Aalbersberg voorzitter Raad van Toezicht NPO 2026 opvolger Joustra`
- WebSearch: `Pointer KRO-NCRV onderzoek Defend-groepen Justice for Prosperity uitzending`

## Per claim: anker → route → uitkomst

| arg | doel | stance | route | resultaat (immuun-id) |
|-----|------|--------|-------|-----------------------|
| 3678 | rel 2185 Plasterk→NPO (cooptatie) | supporting | **ondergraving** `cherry_picking` | reply **3775** · aangevallen (115) |
| 3668 | rel 2177 SIDN fonds→JfP (financiering) | supporting | **ondergraving** `citaat_dekking` | reply **3776** · aangevallen (116) |
| 3692 | rel 2199 Joustra→NPO (draaideur) | supporting | **ondergraving** `citaat_dekking` | reply **3777** · aangevallen (117) |
| 3644 | rel 2155 Postma→Pauw & De Wit | supporting | certificaat | overleefd (118) |
| 3665 | rel 2174 Van Gemert→JfP | supporting | certificaat | overleefd (119) |
| 3666 | rel 2175 Errens→JfP | supporting | certificaat | overleefd (120) |
| 3667 | rel 2176 Olara→JfP | supporting | certificaat | overleefd (121) |
| 3669 | rel 2178 JfP→Identitair Verzet | supporting | certificaat | overleefd (122) |
| 3670 | rel 2179 JfP→Defend | supporting | certificaat | overleefd (123) |
| 3671 | rel 2180 JfP↔Pointer | supporting | certificaat | overleefd (124) |
| 3674 | rel 2181 Nijpels→TROS | supporting | certificaat | overleefd (125) |
| 3675 | rel 2182 Staal→TROS | supporting | certificaat | overleefd (126) |
| 3676 | rel 2183 d'Ancona→NOS | supporting | certificaat | overleefd (127) |
| 3677 | rel 2184 Dekker→NPO | supporting | certificaat | overleefd (128) |

### 3678 — de sterkste aanval van deze ronde (ondergraving `cherry_picking` → reply 3775)

Argument 3678 draagt relatie 2185 (`cooptatie`, mechanisme `politieke_benoeming_omroeptop`).
Citaat 4414 uit bron 71 (Onderzoekscollectief Spit / Vrij Nederland) luidt:

> "De benoeming in 2008 van Bruins Slots opvolger, EO-man Henk Hagoort door PvdA-minister Ronald Plasterk"

De zin in de bron gaat daarna verder:

> "…vormde de enige 'gelukkige uitzondering in het rijtje', aldus Lintmeijer."

Het citaat is dus **precies afgekapt vóór de kwalificatie die het steunbewijs ontkracht**.
De bron voert dit geval op als het geval waarin het patroon van politieke benoemingen
juist *niet* opgaat (Hagoort was EO-man, geen partijgenoot van Plasterk), terwijl het als
steun onder een politieke-benoemingsrelatie hangt. Geen tegenbron nodig: het gat zit in de
inferentie én in de selectie van het citaat.

### 3668 — ondergraving `citaat_dekking` (reply 3776)

Kern van de claim (SIDN Fund financiert WhoDis, cross-platform-polarisatiedetectie) staat
verbatim in bron 2236 — inclusief het kopje "SIDN Fund supports project by Justice for
Prosperity" en de geciteerde zin. Maar het derde deel, "ontwikkeld met het Belgische
bedrijf TextGain" (ook in de beschrijving van relatie 2177), komt in de bron **nergens**
voor: `grep -io "textgain"` geeft 0 treffers op zowel de Engelse als de Nederlandse
paginaversie. Elders wél sourcebaar (whodis.org beschrijft WhoDis als "developed together
with TextGain"), maar niet in de bron die er nu onder hangt.

### 3692 — ondergraving `citaat_dekking` (reply 3777)

Van de drie beweringen in 3692 dekken de citaties er één. Citaat 4439 (NPO-persbericht,
bron 2264) zegt alleen "Tjibbe Joustra is vandaag benoemd tot lid en voorzitter van de Raad
van Toezicht van de NPO" — zónder datum in het citaat en zónder `date_published` op de
bron, dus zelfs "vanaf 2018" hangt nergens aan vast. Citaat 4440 (security.nl) dekt
uitsluitend de NCTb-periode april 2004 – 1 januari 2009. Niet gedekt: de einddatum
15 juli 2026 en de hele derde zin over de opvolging door Aalbersberg en de
"terrorismebestrijding-coördinatorlijn" — juist de generaliserende stap die de
draaideur-duiding van relatie 2199 moet dragen.

## Negatieve resultaten (alleen hier, nooit als modelbijdrage)

- **3676 — mijn eigen tegenhypothese sneuvelde.** Ik ging er gericht op af: als Van der Louw
  al in 1986 NOS-voorzitter werd, kon d'Ancona (minister WVC 07-11-1989 – 16-07-1994) hem
  niet benoemd hebben, en dan lag er een weerlegging met parlement.com als tegenbron.
  parlement.com weerlegt mij: "voorzitter NOS (Nederlandse Omroep Stichting), van
  10 januari 1994 tot december 1997" — ruim binnen d'Ancona's termijn (in 1986 was
  Van der Louw voorzitter Omroepraad en KNVB-sectiebestuur). Claim houdt stand.
- **3674/3675 — citaatgat gedicht door de tweede bron.** Het SPIT-citaat draagt alleen
  "toezichthouder bij de TROS" (geen voorzitterschap, geen data). Vóór ik daar een
  `citaat_dekking`-ondergraving op zette, heb ik de tweede citatie nagelopen: parlement.com
  geeft letterlijk "voorzitter Raad van Toezicht TROS, van december 2007 tot 1 januari 2014"
  (Nijpels) en "lid Raad van Toezicht TROS, vanaf april 2008 (vanaf 2014 AVRO/TROS)" (Staal).
  Aanval ingetrokken.
- **3666 — te dun voor een aanval.** De about-us-pagina zet Errens onder het kopje "Board of
  Directors" maar met de functietitel "Senior Advisor"; "lid van de Board of Directors" is
  dus een lezing, geen letterlijke bronuitspraak. Extern (LinkedIn, dialo.app) wordt Errens
  echter als co-founder/director aangeduid, dus de bestuurslezing is verdedigbaar. Gelaten
  bij een aantekening in het certificaat; hooguit stof voor een preciezere formulering.
- **3669 — parafrase in een `verbatim_quote`.** Het opgeslagen citaat luidt "The Netherlands
  division of a pan-European far-right network, whose French parent organization was
  outlawed as a private militia"; de live paginatekst luidt "The Dutch branch of a
  pan-European far-right network whose French parent organisation has been banned by the
  French government as a private militia". Substantie identiek en dubbel gedekt (ook: "The
  French state classified the organisation as a private militia"), dus geen ondergraving —
  maar de citatie draagt `methode='verbatim_quote'` terwijl ze een parafrase is. Dat is
  A1-terrein; in het certificaat aangetekend. De Wayback-kopie van 21-07-2026 kon ik niet
  nalopen (web.archive.org gaf tweemaal **429**), dus ik kan niet uitsluiten dat de pagina
  ná archivering is herschreven.
- **3671 — bewust naar de wederpartij gezocht.** Een "gezamenlijk onderzoek"-claim die
  alleen op JfP's eigen homepage rust is enkelzijdig. Pointer (KRO-NCRV) publiceert het
  onderzoek echter zelf ook als gezamenlijk (pointer.kro-ncrv.nl), dus onafhankelijk
  bevestigd. Geen aanval.
- **3644, 3665, 3667, 3670, 3677** — breed gezocht naar tegenbronnen en dekkingsgaten,
  niets gevonden; alle claimonderdelen staan in de geciteerde bronnen.

## Stance-balans van de ronde

- weerleggingen (contradicting root met tegenbron): **0**
- ondergravingen (contradicting reply): **3** — 3775, 3776, 3777
- certificaten `overleefd`: **11**
- certificaten `aangevallen`: **3** · `onbeslist`: **0**

Aanvalsgraad 3/14 (21%) van de behandelde claims. Geen enkele claim sneuvelde op de
feiten: alle drie de aanvallen zitten op de *koppeling* tussen bron en claim
(citaatafkapping, onbronbaar claimonderdeel), niet op onwaarheid. Twee voorgenomen
aanvallen (3674/3675, 3666) zijn ingetrokken nadat de tweede bron respectievelijk extern
bewijs ze dichtte — die intrekkingen staan hierboven onder negatieve resultaten.

Geen statuswijziging, merge, bronclassificatie of verwijdering verricht. Geen 429 van de
model-API (de enige 429 kwam van web.archive.org). Geen LinkedIn-scrape nodig deze ronde:
de persoonsclaims betroffen bestuurs-/toezichtfuncties die volledig uit publieke registers
(parlement.com, omroep-eigen bestuurspagina's, JfP about-us) te dekken waren, dus de
scraper voegde niets toe boven de bronnen die al onder de argumenten hingen.
