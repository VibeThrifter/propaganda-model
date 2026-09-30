# Missielog — NPO-toezicht-draaideur (juli 2026-benoemingen)

**Datum:** 2026-07-22 · **Account:** `assistent` (bijdrager) · **Aanleiding:** eigenaar leverde een
nieuwsartikel (aggregator, mét ingebedde NieuwRechts-"Gesponsord"-ad) over twee nieuwe NPO-RvT-leden;
opdracht: "maak hier zoveel mogelijk verbanden van". Behandeld als **grijze lead** → primair geverifieerd
vóór modelleren.

## Verificatie (primair, vóór indienen)
Alle kernclaims verifiëren tegen betrouwbare/primaire bronnen — géén vals NieuwRechts-frame:

| Claim | Bron |
|---|---|
| Aalbersberg → voorzitter RvT NPO per 15-7-2026, opvolger Joustra | spreekbuis.nl (21-7-2026, verbatim), npo.nl, marketingreport, villamedia |
| Bredenoord → lid RvT NPO per 15-7-2026, opvolger **Vletter-van Dort** (entiteit 547) | spreekbuis.nl (verbatim), parlement.com |
| Letschert = minister OCW (D66), media in portefeuille, sinds 23-2-2026 | rijksoverheid.nl (verbatim "Partij: D66"), villamedia (verbatim mediabeleid) |
| Slob → voorzitter RvT EO (was zélf mediaminister CU 2017-2022) | eo.nl/bestuur (verbatim "Arie Slob (voorzitter)" + loopbaanzin) |
| Ter Horst → lid RvT Omroep ZWART vanaf dec-2021 | parlement.com (verbatim) — *omroepzwart.nl/rvt bevestigt NIET meer (ze is per 01-01-2026 van de board; vertrek dec-2025)* |
| Sjoerdsma → lid RvT BNNVARA (mediaportefeuille), aangetreden jan-2024 | spreekbuis.nl (23-1-2024, verbatim) |
| Bredenoord voorzitter CvB EUR sinds 1-9-2024 (rector 2021-2024) | eur.nl (verbatim) |
| Bredenoord D66 EK 2015-2023, fractievoorzitter vanaf 2019 | parlement.com (verbatim) |
| Spit/Vrij Nederland 2023: NPO-top vol Haagse insiders | onderzoekscollectiefspit.nl (17-8-2023, "verscheen eerder bij Vrij Nederland"; verbatim kernzin) |

## Ingediend (alles `voorgesteld`, wacht op reviewer-merge)
**Bronnen (10):** id 2226-2234 nieuw + hergebruikt 71 (Spit/VN). Alle met url-locator; classificatie
*voorgesteld* (adviserend).
**Entiteiten (5, persoon, rol-suggestie 33 politicus):** Bredenoord 1186 · Letschert 1187 · Slob 1188 ·
Ter Horst 1189 · Sjoerdsma 1190.
**Relaties (16):** rel 2156-2171.
- NPO-benoemingen: Aalbersberg(1158)→NPO draaideur/m18 (2156) + bestuurder/m137 (2157);
  Bredenoord→NPO draaideur/m95 (2158) + bestuurder/m137 (2159); Letschert→NPO cooptatie/m99 (2160).
- Affiliaties/partij-bruggen: D66→Bredenoord (2161), D66→Letschert (2162), Bredenoord→EUR (2163),
  Letschert→OCW (2164).
- Overige omroep-draaideurs: Slob→EO draaideur/m96 (2165), Slob→OCW bestuurder/m18 (2166),
  Ter Horst→Omroep ZWART draaideur/m96 (2167), PvdA→Ter Horst (2168), Sjoerdsma→BNNVARA draaideur/m96
  (2169), D66→Sjoerdsma (2170), ChristenUnie(379)→Slob (2171).
**Argumenten (17, supporting, sourced):** arg 3646-3661 (één per relatie, verbatim citaties) +
arg 3662 op **mechanisme 95** (Spit/VN-generalisatie: doorstroom is structureel, niet incidenteel).

Afgeleide bruggen die hierdoor vanzelf verschijnen (niet opgeslagen): NCTV↔NPO (via Aalbersbergs
Politie→NCTV→NPO-pad), D66↔NPO (Letschert + Bredenoord + Rijxman).

## Bewust NIET ingediend (discipline)
- **NVJ/Bruning-quote** ("aanwezigheid bij omroepen van de politiek … echt ongewenst"): alleen verbatim
  vindbaar op **NieuwRechts** (grijze doorgeefbron), toegeschreven aan De Telegraaf (paywall, primair niet
  te verifiëren). NPO Radio 1 / nvj.nl droegen de exacte quote niet. → **geschrapt** i.p.v. witwassen via
  een grijze bron. De onderliggende NVJ-kritiek is reëel maar zonder verifieerbare primaire quote gaat ze
  het model niet in.
- **Martin Wijnen → Rijkswaterstaat**: geen media-invloedslijn (RWS ≠ media). Enkel hier genoteerd, niet
  als `contextual` modelknoop (dat zou schijnzekerheid fabriceren).
- **Schoof→MP, Akerboom**: al gemodelleerd (rel 2080-2086). Artikel refereert er slechts aan als patroon.
- **Org→org-verwevenheid** (NCTV→NPO, D66→NPO): nooit opgeslagen — bruggen zijn afgeleid uit de
  persoon→org-affiliaties. Enige gerichte "richting-NPO"-edge = Letschert(minister)→NPO cooptatie (benoemingsdaad).
- **Bas Paternotte "stelletje pannenkoeken"**: opinie/duiding, geen structureel feit.
- **omroepzwart.nl-RvT-pagina** als Ter Horst-bron: vervangen door parlement.com (pagina is niet meer actueel voor haar).

## Openstaand / vervolg
- Eigenaar merget de batch (reviewer+): via `/overleg` of "via admin".
- Latere optie (bewust nu niet): RfC voor een eigen "veiligheidsapparaat → publieke-omroep-toezicht"-
  mechanisme zodra er méér media-instanties zijn dan alleen Aalbersberg.
