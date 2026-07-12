# Missielog — flak tegen het Artsen(Covid)Collectief, ronde 1

- **Datum:** 2026-07-07
- **Account:** `assistent` (bijdrager) — alles `voorgesteld`, telt in niets tot een mens merget
- **Opdracht eigenaar:** alle coronatijd-flak (kranten, politici, instituties) op het Artsen Covid
  Collectief in het praktijkmodel. Gekozen benadering (plan-goedkeuring): **neutrale flak-edges mét
  confound**, reikwijdte "zo volledig mogelijk"; élke citatie verbatim geverifieerd vóór indiening.

## Neutraliteitskader

De eigenaar stelde dat het "echte artsen zijn die geen misinformatie verspreiden maar gegronde kritiek
hadden". Het onderzoek wees uit dat de **mainstream-medische positie het tegenovergestelde is**
(Kackadorisprijs, KNMG/IGJ, Medisch Contact, Zorgvisie, Kloptdatwel bestempelen diverse claims als
desinformatie). Het model blijft neutraal: elke flak-edge registreert dát er druk was, en waar de kritiek
inhoudelijk gegrond was staat de weerlegging als **contradicting root** op diezelfde relatie (patroon
[[flak-een-relatie-per-voorbeeld-argument]]). De betwiste premisse "geen misinformatie" is **niet** als
modelfeit gecodeerd.

## Onderzoek

Vier parallelle research-agents (staat/instituut · pers · fact-checkers/vakkritiek · platform/werkgever);
élke verbatim quote daarna zelf via WebFetch gecontroleerd op de primaire bronpagina.

## Ingediend (alles `voorgesteld`)

Nieuwe entiteiten #788–798: Stichting Artsen Covid Collectief (stichting, rol maatschappelijke_organisatie),
Hugo de Jonge, Attje Kuiken, Wieke Paulusma, IGJ, Vereniging tegen de Kwakzalverij, Stichting Skepsis
(Kloptdatwel), Medisch Contact, Zorgvisie, Evelien Peeters, UMC Utrecht. Hergebruikt: Ernst Kuipers (167),
LinkedIn (757). Bronnen #1112–1123 (12, alle NL-primair/institutioneel/opinie, onderwerp `nl_systeem`).

11 flak-relaties #1457–1467 (21 argumenten #2094–2114), elk verbatim gesourcet:

| rel | edge | mechanisme | supp/contra | kern-quote (verbatim) |
|-----|------|-----------|-----|-----|
| 1457 | IGJ → ACC | beroepssanctie_uiting | 2/2 | "…ongeveer vijftig keer een corrigerende brief…evident onjuiste informatie…" (De Jonge, Kamerantwoord 215) |
| 1458 | Hugo de Jonge → ACC | publieke_aanval | 1/1 | "Ik vind zulke advertenties zeer onverantwoord." |
| 1459 | Ernst Kuipers → ACC | publieke_aanval | 1/0 | "…brengt Stichting Artsen Covid Collectief zowel aanstaande moeders als hun ongeboren kinderen in gevaar." |
| 1460 | Wieke Paulusma (D66) → ACC | publieke_aanval | 1/1 | Kamervraag 2021Z14873 (noemt collectief bij naam, oppert BIG-intrekking) |
| 1461 | Attje Kuiken (PvdA) → ACC | publieke_aanval | 1/0 | idem 2021Z14873 |
| 1462 | Vereniging tegen de Kwakzalverij → ACC | etikettering | 1/1 | "…heeft…het medisch beroep in diskrediet gebracht" (Kackadorisprijs 2021) |
| 1463 | Stichting Skepsis (Kloptdatwel) → ACC | publieke_aanval | 1/1 | "…is daarom een grove leugen." (Pepijn van Erp) |
| 1464 | Medisch Contact → ACC | publieke_aanval | 1/0 | "…gebruikt daarbij eenzijdige argumenten. Bovendien gaat het collectief niet in discussie…" |
| 1465 | Zorgvisie → ACC | publieke_aanval | 1/1 | "…berichtgeving soms eenzijdig, onprofessioneel en misleidend. Ook pertinente onwaarheden…" (o.a. viroloog Spaan) |
| 1466 | UMC Utrecht → Evelien Peeters | werkgeverssanctie_uiting | 1/1 | "…standpunten van het ACC niet meer verenigbaar…met haar functie als medisch specialist…" |
| 1467 | LinkedIn → ACC | deplatforming | 1/1 | "Vorige week is het account van het Artsen Covid Collectief (ACC) op LinkedIN verwijderd." (bevestigd door criticus Leenstra) |

8 van de 11 dragen een confound als contradicting root; bij 1459/1461/1464 zit de gegronde basis al
in de supporting-quote zelf (ministerieel/parlementair standpunt resp. inhoudelijke vakkritiek) — een
reviewer kan er desgewenst een expliciete confound aan toevoegen.

## Bewust NIET ingediend (buiten scope / onverifieerbaar → alleen hier gelogd)

- **NRC** (04-09-2021 "corona-scepsis in een witte jas"; 28-08-2021 "Wie zitten er achter die advertentie
  tegen kindervaccinatie?"): noemen het collectief bij naam maar staan achter een **paywall** — geen
  verbatim bodyquote te lezen. Niet indienen (nooit een onbevestigde quote; [[argumenten-vereisen-echte-bron]]).
- **De Groene Amsterdammer / Pointer (KRO-NCRV)** "John Birch Society / complotdenkers" (dec 2020–jan 2021):
  verbatim leesbaar, maar betreffen de **brandbrief/Elke de Klerk-kring** (voorloper), niet de Stichting
  bij naam → mis-attributie. De RvdJ (2021/30) achtte de John Birch-koppeling deels onzorgvuldig. Niet indienen.
- **YouTube/ECLI:NL:RBAMS:2020:4435** (sept 2020): huisarts/Café Weltschmerz, vóór de oprichting van het
  collectief → NIET het collectief. Geen YouTube-edge.
- **Tuchtzaak Rob Elens** (berisping): niet als bevestigd kernlid-in-rol te koppelen + geen verbatim uit de
  uitspraak. Niet ingediend.
- **VWS "Denktank Desinformatie" ↔ collectief**: alleen via collectief-eigen/complot-sites op Wob-basis;
  geen neutrale primaire bron met verifieerbare aan de Denktank toe te schrijven quote. Niet indienen.

## Verificatie

`python3 scripts/validate_model.py --strict` → **EXIT 0** (golden snapshot groen; geen fouten boven baseline).
Geen dubbele bronnen (`/api/sources` dedupt op titel). Alles `voorgesteld`.

## Voor de reviewer

- Mergen (reviewer+/"via admin") tilt relaties + argumenten uit `voorgesteld`. Ik stel voor, jij beslist.
- Overweeg voor 1459/1461/1464 een expliciete confound-root voor volledige symmetrie.
- Relatietype/mechanisme is per edge te herzien (bv. Medisch Contact/Zorgvisie tussen `publieke_aanval` en
  `etikettering`).
