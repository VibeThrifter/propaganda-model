# Missielog — actuele eigendomsrelaties nieuwsmedia

- **Datum:** 2026-09-30
- **Account:** `assistent` (bijdrager; alles `voorgesteld`)
- **Aanleiding:** eigenaar: "Zet de ontbrekende actuele eigendomsrelaties met bronnen klaar als 'voorgesteld'; ik keur ze goed." Aanleiding was dat de nieuwsaggregator-bronnen (AD, de Volkskrant, Trouw, NU.nl, De Telegraaf, NOS, RTL Nieuws, GeenStijl, de andere krant, NieuwRechts, NineForNews, Een Blik op de NOS) in de goedgekeurde graaf geen of alleen historische eigendomsrelaties hadden.
- **Brief/discipline:** CLAUDE.md § "Elementvoorstellen op verzoek" (blob `ee9a6d9`) + `missies/scout_brief.md` (blob `dcce63e`) als procedure (bron → knoop → verband → argument).
- **Pad:** de gewone REST-endpoints (`POST /api/sources`, `/api/entities`, `/api/relations`, `/api/arguments`) met het `assistent`-token. Omdat er geen server draaide, zijn ze in-process aangeroepen via `server.app.test_client()` (zelfde patroon als `scripts/test_*.py`), zodat poorten, dedup en `edit_log`-attributie gewoon golden. Eerst een droogloop op een kopie; `validation.run_all` gaf daar geen nieuwe `fout`, alleen +11 `BRON-ARCHIEF` (nieuwe URL-bronnen zonder Wayback-locator).
- **Backup vooraf:** `data/propaganda_model_backup_20260930_145341.db` (sqlite-backup-API, integrity ok).

## Ingediend (alles `voorgesteld`)

**Relaties** (`eigendom`, allemaal met mechanisme en gesourcete argumenten):

| Rel | Bron → doel | Mechanisme | active_from | Argumenten |
|---|---|---|---|---|
| #2264 | DPG Media (1) → AD (3) | eigendomsconcentratie | 2009 | #3824, #3825 |
| #2265 | DPG Media (1) → de Volkskrant (4) | eigendomsconcentratie | 2009 | #3826, #3827 |
| #2266 | DPG Media (1) → Trouw (5) | eigendomsconcentratie | 2009 | #3828, #3829 |
| #2267 | DPG Media (1) → NU.nl (7) | eigendomsconcentratie | 2020-04-20 | #3830, #3831 |
| #2268 | Mediahuis Nederland (579) → De Telegraaf (9) | eigendomsconcentratie | 2019-11-05 | #3832, #3833 |
| #2269 | GS Magenta B.V. (1244) → GeenStijl (342) | holdingconstructie | 2018-11-01 | #3834, #3835 |
| #2270 | NR B.V. (1245) → NieuwRechts (1215) | holdingconstructie | onbekend | #3836 |

**Entiteiten:** #1244 GS Magenta B.V. (bedrijf, rolsuggestie overnamevehikel; arg #3837), #1245 NR B.V. (bedrijf, rolsuggestie overnamevehikel; arg #3838).

**Nieuwe bronnen** (classificatievoorstel adviserend): #2328 NMa-persbericht 01-07-2009 (primair), #2329 Villamedia-overzicht 17-01-2022 (regulier), #2330 Sanoma-beursbericht 20-04-2020 (primair), #2331 Villamedia 05-11-2019 (regulier), #2332 inct 05-11-2019 (regulier), #2333 Mediahuis Nederland "Onze organisatie" (primair), #2334 Mediahuis-merkpagina De Telegraaf (primair), #2335 Retriever 01-11-2018 (regulier), #2336 Villamedia 24-09-2018 (regulier), #2337 voettekst GeenStijl.nl (primair), #2338 algemene voorwaarden NieuwRechts.nl (primair). **Hergebruikt:** #1605 Mediamonitor 2025 (CvdM), #945 SDM-geschiedenis, #944 ACM Sanoma-besluit, #2268 NieuwRechts "wie zijn wij".

Alle 51 citaties zijn `verbatim_quote`, en elke quote is vóór het indienen letterlijk teruggevonden in de live paginabron of in de PDF-tekst (Mediamonitor: p. 12, 14, 17 en 19).

## Queries (letterlijk)

Web:
- `DPG Media merken AD de Volkskrant Trouw Het Parool NU.nl dpgmediagroup.com`
- `De Persgroep overname PCM Uitgevers afgerond 2009 NMa goedkeuring`
- `"Persgroep" "PCM" overname rond 2009 Volkskrant Trouw AD nieuwe eigenaar`
- `NMa besluit De Persgroep PCM Uitgevers 2009 concentratie zaak`
- `Telegraaf Media Groep naam gewijzigd Mediahuis Nederland 2020`
- `GeenStijl eigenaar 2018 onafhankelijk verkocht Mediahuis wie is eigenaar GeenStijl B.V.`
- `NineForNews eigenaar oprichter ninefornews.nl`
- `"Een Blik op de NOS" oprichter stichting website`
- `DPG Media overname Sanoma Media Nederland afgerond april 2020 NU.nl`
- `Sanoma completed divestment Sanoma Media Netherlands DPG Media stock exchange release April 2020`
- `GeenStijl eigenaren Pritt Bart Nijman GeenStijl B.V. 2024 OR 2025`
- `NieuwRechts.nl eigenaar "NR B.V." OR oprichter nieuwswebsite NieuwRechts opgericht`
- `2009 Persgroep PCM AD Nieuwsmedia Wegener belang overgenomen Algemeen Dagblad volledig`
- `Mediahuis VP Exploitatie bod TMG gestand gedaan 2017 datum afwikkeling aandelen`
- `"gestand" bod TMG Mediahuis VP Exploitatie juni 2017 persbericht 61,4`
- `"Persgroep" PCM overname afgerond juli 2009 NMa toestemming NRC verkopen`
- `"GS Magenta B.V."`
- `"GeenStijl is van ons" bekendmaking 2018 Pritt Van Rossem Mediahuis 1 november`
- `NieuwRechts nieuwssite gelanceerd opgericht jaar "NieuwRechts.nl"`

Opgehaalde pagina's: sdm.nl/geschiedenis, acm.nl (publicatie 6389 en het Sanoma-besluit), villamedia.nl (4 artikelen), sanoma.com, inct.nl, retriever.nl, mediahuis.nl (organisatie + merkpagina), geenstijl.nl (home + /adverteren), nieuwrechts.nl (wie-zijn-wij, algemene-voorwaarden, contact), ninefornews.nl (over-ons, privacy, contact, disclaimer, colofon), de Mediamonitor 2025-PDF, en nl.wikipedia (De Persgroep, GeenStijl), die alleen als vindplaats zijn gebruikt en niet geciteerd. dpgmedia.nl/merken zat achter een consent-wall en telegraaf.nl gaf 403.

DB-queries: eigendoms- en overige relaties op de doelentiteiten 1, 2, 3–11, 88, 99, 248, 342, 579, 1130 en 1215, plus bestaande bronnen op acm/sdm/villamedia/cvdm/mediahuis/geenstijl/nieuwrechts.

## Negatieve resultaten (alleen hier, geen modelbijdrage)

- **NineForNews:** geen uitgevers- of eigenaarsvermelding op de eigen site. Nieuwe Revu (2017) noemt een eigenaar, maar een actuele (2026) bevestiging is niet gevonden. Er is geen entiteit of relatie ingediend.
- **Een Blik op de NOS:** alleen sociale-media-accounts. Een eigenaar, uitgever of rechtsvorm is niet vindbaar, dus er is niets ingediend.
- **NOS:** publieke taakomroep zonder eigenaar. De bestelsturing (NPO → NOS) staat al in het model, dus hier is niets ingediend.
- **de andere krant:** de uitgever (Stichting KnowledgeMatters → de andere krant, rel #561) staat al goedgekeurd in het model, dus niets ingediend.
- **RTL Nieuws / RTL Nederland:** DPG Media → RTL Nederland per 2025-07-01 staat al goedgekeurd (#9, #1061). Niets ingediend (zie de afwijkingen hieronder).
- **GS Magenta B.V.:** wie er in 2026 aandeelhouder is, is niet publiek verifieerbaar. Wikipedia noemt een mede-eigenaar vanaf december 2024, maar zonder bron, dus dat is niet overgenomen.
- **NR B.V.:** aandeelhouders en startdatum van de site zijn niet gevonden.

## Gesignaleerde afwijkingen in goedgekeurde relaties (niet aangepast; ter beoordeling eigenaar)

- #7 DPG Media → Het Parool heeft `active_from` 2019. Volgens SDM/Villamedia verwierf De Persgroep in 2003 een belang en in 2005 een meerderheid.
- #158 DPG Media → RTL Nieuws heeft `active_from` 2019. De overname van RTL Nederland werd per 1 juli 2025 afgerond.
- #191 Mediahuis → TMG heeft `active_from` 2020. Mediahuis zelf zegt dat TMG in 2017 onderdeel werd van de groep.
- #199 TMG → De Telegraaf heeft `active_until` 2020. De naamswijziging naar Mediahuis Nederland ging in op 5 november 2019.
- De entiteiten TMG #99 en #1130 zijn dubbel.

## Balans

Stance: 15 steun / 0 tegen / 0 context. Er is geen tegenbewijs tegen deze eigendomsfeiten gevonden (zie de negatieve resultaten). Nieuwheid: 2 nieuwe knopen en 7 nieuwe edges, allemaal opvolgers van historische eigendomsrelaties. Er zijn geen hercitaties ingediend.
