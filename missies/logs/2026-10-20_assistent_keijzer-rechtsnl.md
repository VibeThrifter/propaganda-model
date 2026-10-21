# 2026-10-20 — assistent — Mona Keijzer (#3733), lead RechtsNL-carrousel "Keijzer × Israël"

Brief: opdracht van de eigenaar (grijs lead via krispijnpunt). Het frame van de carrousel
("Israëlische invloed … exposed") is de conclusie van RechtsNL en is niet overgenomen. Alleen de
structuurschil is ingediend; de uitspraken van Keijzer zijn haar meningen (geen verband, geen
waarheidsoordeel).

## Queries (web, letterlijk)
- `parlement.com Mona Keijzer` → biografie https://www.parlement.com/biografie/mcg-mona-keijzer (curl, citaten letterlijk teruggevonden in de html)
- `Mona Keijzer aangifte groepsbelediging Sophie & Jeroen OM seponeert juli 2024`
- `CIDI 50 jaar jubileum mei 2025 Mona Keijzer ambassadeur`
- `cidi.nl Mona Keijzer`; `CIDI stemmonitor BBB 97 procent moties Israël`; `"Keijzer" "CIDI" 2025` (extended)
- `CIDI Keijzer herdenking 7 oktober 2025 BBB minister Keijzer toespraak`
- `RTL Nieuws Keijzer brief Israël druk kabinet augustus 2025 ingewijden`; `rtl.nl Keijzer Veldkamp maatregelen Israël ministerraad 22 augustus 2025`
- `BBB visiestuk "Een antwoord op islamitisch extremisme" Keijzer oktober 2025`
- `Mona Keijzer naturalisatie bestaansrecht Israël erkennen WNL`
- `Mona Keijzer October 8 film Tuschinski toespraak`
- `Mona Keijzer reis Israël uitnodiging CIDI geschenkenregister Tweede Kamer`
- ministerie VRO: `ministerie van Volkshuisvesting en Ruimtelijke Ordening opgericht 2 juli 2024 …`, `… ingesteld besluit 2024 Staatscourant`, `parlement.com "Ministerie van Volkshuisvesting en Ruimtelijke Ordening" 2024 ingesteld`
- DB (alleen lezen): relaties van #3733, #333/#666/#4964; precedenten ambt/mech 206/210/211, lidmaatschap mech 92; OO-uitgave 2026-10-08 (ministerie VRO, mnre1171, eindDatum classificaties 2026-02-23, niet als knoop in het model).

## Oogst (alles voorgesteld, account assistent)
Bronnen: #3428 (Parlement.com biografie Keijzer), #3429 (Parlement.com ministerie VRO).
Entiteiten: #5059 Ministerie van Volkshuisvesting en Ruimtelijke Ordening, #5060 Project2029.
Relaties en argumenten:
- 8786 Keijzer — CDA lidmaatschap (92) 1991 – 2023-08: arg 11756
- 8787 Keijzer — BBB lidmaatschap (92) 2023-09-01 – 2026-03-28: arg 11757, 11758
- 8788 Keijzer — Min. EZ ambt (206) staatssecretaris EZK 2017-10-26 – 2021-09-25: arg 11759, 11760 (ontslag na Telegraaf-uitspraak coronatoegangsbewijs)
- 8789 Keijzer — Min. VRO ambt (206) minister + viceminister-president 2024-07-02 – 2026-02-23: arg 11761, 11762 (derde arg 409 als duplicaat, overgeslagen)
- 8790 Keijzer — Gemeente Purmerend ambt (210) wethouder 2007-11-05 – 2012-07-12: arg 11763
- 8791 Keijzer — Gemeente Waterland ambt (210) wethouder 1998-04 – 2005-01: arg 11764
- 8792 Keijzer — Project2029 bestuurder (18) initiatiefnemer vanaf 2026-08-27: arg 11765
- 8793/8794/8795/8796 Keijzer — Tweede Kamer ambt (211): 2012-09-20–2017-10-26 (CDA), 2021-03-31–2021-09-27 (CDA), 2023-12-06–2024-07-02 (BBB), 2025-11-12–2026-02-23 (BBB; sluit aan op #5651 vanaf 2026-02-24): arg 11766, 11767, 11768, 11769, 11770
- entiteit #5059: active_until 2026 (arg 11771), opgegaan_in #821 BZK (arg 11772; eerste poging 409 op gelijkenis met 11771, opnieuw met negeer_duplicaten omdat het een ander aspect is)

## Negatieve resultaten / niet ingediend
- **Flak via aangifte**: aangevers zijn niet bij naam bekend (OM: "Zestien personen"; Hart van Nederland 24-05-2024: "Een groep van tien juristen en een historicus", vertegenwoordigd door advocaat Reinout Sterk). Geen aangever-knoop → geen flak-verband. OM-sepot 12-07-2024 (om.nl) is een beslissing, geen flak.
- **CIDI → Keijzer / CIDI → BBB**: Jonet (19-05-2025) bevestigt alleen "Vicepremier Mona Keijzer (BBB) kwam namens de regering" naar de CIDI-jubileumdag (18-05-2025). Aanwezigheid namens het kabinet is geen lobbybewijs. CIDI-nieuwsbrief okt. 2025 (stemmonitor, herdenkingen) is niet leesbaar (Cloudflare 403, ook de enige Wayback-snapshot is 403): niet te staven. Een stemmonitor is bovendien CIDI's eigen product en draagt geen lobbyverband. Geen tegenbewijs gezocht dat iets oplevert; geen verband ingediend.
- **Ambassade van Israël ↔ Keijzer**: geen bron gevonden voor een gesprek met de ambassadeur op 18-05-2025 (NOS 2567751 en Jonet noemen geen ambassadeur). Niets ingediend.
- **Geschenk/reis**: niets gevonden over een door CIDI of de ambassade betaalde reis.
- **RTL 22-08-2025 (brief Israël)**: RTL-bron niet gevonden; wel bevestigd dat Veldkamp na de ministerraad van 22-08-2025 opstapte en BBB tegen verdere maatregelen was (NOS 2579482, nltimes). Anonieme ingewijde, mening/besluitvorming in de ministerraad: geen verband.
- **Uitspraken** (Sophie & Jeroen 17-05-2024, WNL okt. 2025, naturalisatie/bestaansrecht Israël, toespraak October 8 Tuschinski, BBB-visiestuk 15-10-2025): meningen van Keijzer, niet als verband gemodelleerd. Visiestuk bevestigd in hoofdlijn (Hart van Nederland); WNL/naturalisatie en Tuschinski niet teruggevonden.
- **Ministerie VRO active_from**: geen citaat gevonden dat de oprichtingsdatum (2 juli 2024) van het ministerie zelf noemt; laat de datumzoeker zoeken.
- Duplicaat CIDI #666 naast #333: alleen gemeld.

## Stance-balans
16 steun / 0 tegen / 0 context (structuurfeiten uit één biografische bron; geen betwiste claims ingediend).
