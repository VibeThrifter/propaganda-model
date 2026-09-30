# Missielog — expert-ecosysteem & grootkapitaal (assistent)

**Datum:** 2026-07-12
**Account:** assistent (bijdrager) — indienen; goedkeuring via `maxime` (admin, op expliciete aanwijzing "doe alles, via admin")
**Aanleiding:** eigenaar leverde een AI-synthese-schema aan ("Wie mag de feiten bepalen?" — expert-ecosysteem, ideologische draaideur, kadering, flak/kapitaalvlucht). Vraag: welke elementen vallen eruit te halen. Bestaand model dekte het expert-ecosysteem al grotendeels; vier extractiesporen bleken nieuw.

## Werkwijze
Vier parallelle web-onderzoeksagents (Opus) leverden verbatim-geverifieerde bronnen. Paywall-/niet-verifieerbare routes bewust **niet** ingediend. Wikipedia niet als bron gebruikt. Indienvolgorde: bronnen(+locators) → entiteiten → relaties → argumenten, alles `voorgesteld`, daarna admin-goedkeuring.

## Ingediend & goedgekeurd (praktijklaag, via admin)
- **Spoor C — draaideur Financiën/EZ ↔ bedrijfsleven.** 7 entiteiten (Joop Wijn, Hans Wijers, DSB Bank, Adyen, AkzoNobel, Boston Consulting Group, Heineken), 11 bronnen, **12 gedateerde `draaideurconstructie`-affiliaties** (rel. 2007–2018) elk met gesourcet supporting-argument. Loopbaanstappen van Zalm/Wijn/Wijers; bruggen Financiën↔ABN AMRO en EZ↔ING/AkzoNobel/Heineken verschijnen afgeleid.
  - Dijsselbloem: na brede zoektocht **géén** bedrijfsdraaideur (alleen publieke functies) — eerlijk negatief resultaat, niet gemodelleerd.
- **Spoor B — ontbrekende `expert_framing`-edges.** 5 nieuwe edges (rel. 2019–2023): ING Research→FD, ING Research→BNR, ABN AMRO Group Economics→BNR, ABN AMRO Group Economics→Nieuwsuur, VNO-NCW→FD — elk met 2–3 verbatim-gesourcete argumenten. Paywall-routes (ABN→FD, Rabo→FD, VNO→BNR) niet ingediend.
- **Spoor D — mediakritische meta-bronnen op bestaande theorie.** Engelen/De Groene "Organische intellectuelen" (2021) op `expert_framing`; FTM Fernandez & Bieckmann (2018) op `meningsspectrum_beperking`.

Totaal goedgekeurd: 8 entiteiten, 17 relaties, 34 argumenten gemerged. `validate_model.py --strict` groen (na rol-toewijzing `belanghebbende` aan de 6 nieuwe org-entiteiten).

## Ingediend, incuberend (spoor A — kapitaalvluchtdreiging)
- 4 **kandidaat-relaties** bedrijf→ministerie (mechanisme-loos → `voorgesteld`, rel. 2024–2027): ASML→EZ (Project Beethoven 2024), Boskalis→EZ (IMVO 2023), Shell→Financiën (dividendbelasting 2017–2021), Unilever→Financiën. Met gesourcete argumenten, een **confound** (MVO Nederland noemt Boskalis-dreiging zwak argument — neutraliteit) en een academisch **patroon-anker** (Huijzer, StukRoodVlees — structural power of capital).
- **RfC #53** — nieuw mechanisme `kapitaalvluchtdreiging` (belanghebbende→politicus, filter `ideologie`, aard direct, mechanisme #198), adopteert de 4 kandidaten. Eerst niet zelf doorgezet (beschermd niveau: ik stel voor, eigenaar beslist); na expliciet "via admin" **geaccepteerd** (`admin.py voorstel-akkoord 53`) en de vier edges (rel. 2024–2027) via admin goedgekeurd. Kapitaalvlucht-edges nu live; strict-gate groen.

## Aandachtspunt
Tijdens deze sessie draaide een tweede `assistent`-missie gelijktijdig (args 3425–3429, over Defensie/Adessium — niet van deze missie); bij de admin-goedkeuring strikt op eigen id's gefilterd.
