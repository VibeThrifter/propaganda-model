# Onbewaakte ronde — nieuws-scout · ronde3 · 2026-10-14

- Brief: `missies/nieuws_scout_brief.md` (blob `12c7e43ee2f4`)
- Account: `nieuws-scout`
- Gestart: 2026-10-14T17:57:36

## Sessie-uitvoer

```
# nieuws-scout, ronde 3 (2026-10-14)

Ik heb drie redactieleiding-doelen geclaimd en alle drie staan op `klaar`: #128 `redactieleiding:nos`, #129 `redactieleiding:rtl-nieuws` en #130 `redactieleiding:nu-nl`. Ik heb 10 bronnen, 7 personen, 11 relaties (alle met mechanisme 18) en 18 steunende argumenten ingediend, allemaal `voorgesteld`. Partijbanden heb ik bij geen van de drie media gevonden, dus het zijn alleen functies. Er kwam geen 429, geen 409 en geen dode LinkedIn-sessie. Ik heb geen modelstatussen of bronklassen aangeraakt; alleen de drie wachtrij-doelen heb ik afgesloten (PATCH gaf drie keer 200).

- **Brief:** `missies/nieuws_scout_brief.md`, blob `12c7e43ee2f4` (`git hash-object` gaf dezelfde).
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []`. Ik heb op geen enkel bestaand argument gereageerd.
- **LinkedIn-rem:** `mag zoek` en `mag profiel` gaven allebei exit 0. Aan het eind stond de status op uur 0/2 en dag 0/10 voor beide. Ik heb LinkedIn bewust niet gebruikt: dit zijn aankondigingen van functies bij media, en die dekken de NOS-, Villamedia- en Hart van Nederland-berichten beter.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` gaf de doelen #128, #129 en #130.

## Zoekopdrachten in de database (alleen-lezen)
1. `SELECT id,name,type,status FROM entities WHERE id IN (11,146,88,235,7);`
2. Alle niet-vervangen relaties tussen personen en de entiteiten 11, 146, 88, 235 en 7. Daaruit blijkt het precedent: persoon → medium, `personeel`, mechanisme 18 (Van Cann, Mossink, Berghuis, Klein, Wester).
3. `SELECT id,name,filter,… FROM mechanisms WHERE id IN (18,192,70,95,92) OR name IN ('podiumverlening','partijbinding','partijlijn','draaideurconstructie','dienstverband') OR name LIKE '%podium%';`
4. De relaties van Kamran Ullah, Kees Berghuis en Frits Wester (de precedenten).
5. Bestaat de persoon al? `name LIKE` op Gelauff, Wilma Haan, Waagmeester, ter Horst, Leferink, Marijn de Koning, Borgman, Noorlander, Fons Lambie, Bremer, Hoekman, Wouter Bax, Bolhuis, Pieter Klein en Taselaar. Daarna nog op Openneer, van Ark, Lindeboom, Karina en Haan.
   - Wel aanwezig: Ilse Openneer (#400), Floor Bremer (#715), Wimar Bolhuis (#1040) en Pieter Klein (#473).
   - De rest bestond niet. Guusje ter Horst (#1189) is een andere persoon.
6. De relaties van Bremer, Bolhuis en Klein, plus de argumenten op de relaties 1841, 2037, 923 en 964, en de bron van argument 2679 (bron #1538).
7. De mediaplatform-precedenten en `functie LIKE '%column%'`: personeel/18 komt 3× voor.
8. De rollen (29 `hoofdredacteur`) en de toegestane waarden voor reliability en source_type.
9. Of de bron-urls al bestonden: alleen #1538 (wimarbolhuis.nl).

## Zoekopdrachten op het web (WebSearch, letterlijk)
- `NOS hoofdredactie adjunct-hoofdredacteur benoemd`
- `NOS politiek verslaggever eerder voorlichter partij overstap`
- `RTL Nieuws nieuwe hoofdredacteur benoemd`
- `NU.nl nieuwe hoofdredacteur benoemd`
- `"NOS" journalist kandidaat Tweede Kamer kandidatenlijst oud-verslaggever NOS Journaal politiek`
- `RTL Nieuws politiek verslaggever wordt woordvoerder minister vertrekt naar ministerie`
- `NU.nl politiek redacteur wordt woordvoerder partij fractie overstap Villamedia`
- `Marcel Gelauff hoofdredacteur NOS Nieuws sinds benoemd 2010`
- `Wimar Bolhuis column RTL Nieuws econoom columnist`
- `hoofdredacteur RTL Nieuws 2024 OR 2025 Harm Taselaar opvolger`
- `rtl.nl "Wimar Bolhuis" column`
- `"hoofdredacteur van RTL Nieuws" benoemd Villamedia`
- `"hoofdredacteur van NU.nl" 2024 OR 2025 OR 2026`
- `nieuws.nl hoofdredacteur RTL Nieuws stopt opvolger` (extended)
- `"Ilse Openneer" hoofdredacteur RTL Nieuws per 2022 begint`
- `Villamedia Alies Lindeboom adjunct-hoofdredacteur RTL Nieuws Mireille van Ark`
- `Floor Bremer RTL Nieuws politiek verslaggever vertrekt naar`
- `oud-journalist NU.nl wordt woordvoerder minister OR Kamerfractie OR partij`
- `"NOS" verslaggever wordt woordvoerder ministerie OR minister-president "Transfer Thursday"`
- `"adjunct-hoofdredacteur" NU.nl benoemd Mossink hoofdredactie`
- `NU.nl politiek verslaggever Den Haag redactie politiek chef NU.nl`
- `"Wilma Haan" NOS 2025 OR 2026`
- `"Lucas Waagmeester" NOS adjunct-hoofdredacteur 2025 OR 2026`
- `"Gert-Jaap Hoekman" NOS Sport hoofdredacteur 2025 OR 2026`

**Opgehaald met `bronchecker.haal_url`:**
- nos.nl: artikel 2430792, 2338356, l/2455713, l/2477817, l/2436821 en artikel 2410389
- mediacourant.nl: de Taselaar-melding van 2021-05
- villamedia.nl: de Taselaar-melding, de Van Luling-melding, de Van Ark-melding, de Lindeboom-melding en de overzichtspagina `/over/RTL+Nieuws`
- hartvannederland.nl: de melding dat Hoekman stopt
- over.nos.nl: het governance-register (pdf) van 9 november 2023
- bnnvara.nl: het VARAgids-interview met Floor Bremer
- wimarbolhuis.nl: `/wimar-bolhuis/` en `/columns/`
- parlement.com en tweedekamer.nl: de biografie van Bolhuis

**Citaatcontrole:** alle 18 citaten zijn met `zoek_citaat` exact teruggevonden.

## Per doel

**#130 NU.nl → klaar** (entity 7)
- bronnen: #2794 (NOS, 5 juni 2023), #2795 (Hart van Nederland, 15 november 2024), #2796 (NOS, 24 juni 2020)
- entiteit #4875 Gert-Jaap Hoekman
  - relatie #7964: Hoekman → NU.nl, `personeel`, mechanisme 18, hoofdredacteur, 2012–2023
  - argumenten #10185 en #10186
- entiteit #4876 Wilma Haan
  - relatie #7965: Haan → NU.nl, `personeel`, adjunct-hoofdredacteur, tot 2015
  - Het begin heb ik niet gevonden. Ik heb het verband ingediend met `zonder_jaar`; de datumzoeker zoekt verder.
  - argument #10187
- Lindsay Mossink stond al in het model, dus die heb ik niet dubbel ingediend.

**#128 NOS → klaar** (entity 11)
- bronnen: #2797 (Gelauff), #2798 (de adjuncten); hergebruikt: #2796 en #2795
- entiteit #4877 Marcel Gelauff
  - relatie #7966: van 2003 tot 2022-09-01, hoofdredacteur vanaf 2011
  - argumenten #10188 en #10189
- Wilma Haan (#4876)
  - relatie #7967: adjunct sinds 2020-09-01
  - argument #10190
- entiteit #4878 Karina ter Horst
  - relatie #7968: adjunct sinds 2023-02-01
  - argumenten #10191 en #10192
- entiteit #4879 Lucas Waagmeester
  - relatie #7969: adjunct sinds 2023-03-01
  - argumenten #10193 en #10194
- Gert-Jaap Hoekman (#4875)
  - relatie #7970: hoofdredacteur NOS Sport, van 2023-09 tot 2024-11
  - argumenten #10195 en #10196

**#129 RTL Nieuws → klaar** (entity 88)
- bronnen: #2799 (NOS, Openneer), #2800 (Villamedia, Van Ark), #2801 (Villamedia, Lindeboom); hergebruikt: #1538 (de eigen site van Bolhuis)
- Ilse Openneer (#400)
  - relatie #7971: hoofdredacteur sinds 2021-12
  - argument #10197
- entiteit #4880 Mireille van Ark
  - relatie #7972: van 2022-09 tot 2025-11
  - argumenten #10198 en #10199
- entiteit #4881 Alies Lindeboom
  - relatie #7973: bij RTL Nieuws sinds 2019, adjunct sinds februari 2026
  - argumenten #10200 en #10201
- Bolhuis (`column_als_deskundige`)
  - relatie #7974: Bolhuis → RTL Nieuws, `personeel`, functie columnist, mechanisme 18
  - ingediend met `zonder_jaar`; de bestaande relatie 1841 blijft staan
  - argument #10202
  - De bron is zelf-gerapporteerd (bronklasse grijs).

## Negatieve resultaten (alleen in dit log)
- **Partijbanden:** voor alle drie de media niet gevonden. Gezocht via de WebSearches hierboven en het NOS-nevenfunctieregister van november 2023. In dat register heb ik gezocht op partij, VVD, CDA, D66, PvdA, GroenLinks, gemeenteraad, fractie, wethouder, ministerie en Haag. Alleen een onbezoldigde OCW-coördinatie en de functie bij het Persvrijheidsfonds kwamen naar boven; geen van beide is een partijband.
- **Harm Taselaar** was hoofdredacteur van RTL Nieuws sinds 1999 (Mediacourant en Villamedia). Zijn einddatum heb ik niet gevonden, dus ik heb hem niet ingediend: een verband dat voorbij is maar geen einde heeft, zou in de tijdbalk nog lopen.
- **Zonder begindatum gevonden, dus niet ingediend:** Bart Leferink, Dennis van Luling, Sibe Sietsma en Floor Bremer. Ook de eerdere RTL-functie van Gelauff valt hieronder.
- **Bolhuis:** geen periode voor zijn column gevonden; rtl.nl is niet te lezen omdat de site met JavaScript wordt opgebouwd.
- **NU.nl:** ik heb niet gevonden wie nu adjunct is of wie de politieke verslaggevers zijn.

## Stance-balans
18 steun, 0 tegen, 0 context.

Nieuw: 7 knopen en 11 verbanden, geen hercitaties.

Noot: `scripts/scout_indienen.py` wacht bij een 429 zelf 62 seconden en probeert dan opnieuw. Dat botst met de regel uit de brief: bij een 429 stop je. In deze ronde kwam er geen 429.

Sources:
- [NOS: Marcel Gelauff stopt als hoofdredacteur](https://nos.nl/artikel/2430792-marcel-gelauff-stopt-als-hoofdredacteur-van-nos-nieuws)
- [NOS: Waagmeester en Ter Horst nieuwe adjuncten](https://nos.nl/l/2455713)
- [NOS: Wilma Haan nieuwe adjunct-hoofdredacteur](https://nos.nl/artikel/2338356-wilma-haan-nieuwe-adjunct-hoofdredacteur-nos-nieuws)
- [NOS: Hoekman nieuwe hoofdredacteur NOS Sport](https://nos.nl/l/2477817)
- [Hart van Nederland: Hoekman stopt bij NOS Sport](https://www.hartvannederland.nl/entertainment/tv/artikelen/gert-jaap-hoekman-stopt-als-hoofdredacteur-van-nos-sport)
- [NOS: Ilse Openneer nieuwe hoofdredacteur RTL Nieuws](https://nos.nl/artikel/2410389)
- [Villamedia: Mireille van Ark stapt uit hoofdredactie](https://www.villamedia.nl/artikel/mireille-van-ark-stapt-uit-hoofdredactie-rtl-nieuws)
- [Villamedia: Nieuwe adjunct-hoofdredacteur RTL Nieuws](https://www.villamedia.nl/artikel/nieuwe-adjunct-hoofdredacteur-voor-rtl-nieuws)
- [Wimar Bolhuis: over Wimar](https://wimarbolhuis.nl/wimar-bolhuis/)
- Niet gebruikt:
  - [Mediacourant: Taselaar](https://www.mediacourant.nl/2021/05/harm-taselaar-stopt-na-22-jaar-als-hoofdredacteur-rtl-nieuws/)
  - [Villamedia: Taselaar](https://www.villamedia.nl/artikel/harm-taselaar-stopt-binnen-jaar-als-hoofdredacteur-rtl-nieuws)
  - [Villamedia: Van Luling](https://www.villamedia.nl/artikel/dennis-van-luling-stopt-als-adjunct-hoofdredacteur-rtl-nieuws)
  - [NOS-register 2023](https://over.nos.nl/wp-content/uploads/2023/11/Governance-openbaar-register-NOS-9-november-2023-1.pdf)
  - [VARAgids: Floor Bremer](https://www.bnnvara.nl/varagids/artikelen/interview-met-floor-bremer)
  - [Parlement.com: Bolhuis](https://www.parlement.com/biografie/dr-wd-wimar-bolhuis)

```

## Runner-metadata

- Exit-code: 0
- Duur: 865.6 s
- Oogst (edit_log-delta van `nieuws-scout`): 44
- Beëindigd: 2026-10-14T18:12:02
