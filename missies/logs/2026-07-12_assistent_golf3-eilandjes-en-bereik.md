# Missielog — golf 3: eilandjes + advertentie/eigendom (deels gestrand op credits)

- **Datum:** 2026-07-12
- **Account:** `assistent` (vijf parallelle Claude Code-subagenten)
- **Uitkomst:** alle vijf agents zijn vroegtijdig gestorven — vier op *"You're out of usage credits"* (Fable-quota op), één (advertentie/eigendom) had daarvoor al op de sessielimiet gestaan in golf 2. Er is dus **gedeeltelijk en deels off-brief** werk geland. Dit log legt de werkelijke DB-stand vast.

## Wat er wél landde (allemaal `voorgesteld`)

**Entiteiten 1117–1121 (5):** NDC mediagroep, Dienst Publiek en Communicatie (DPC), Sylvia Witteman, STAK TMG, Raad van Commissarissen TMG.

**Relaties 1995–2006 (12) — mét supporting argument, mergebaar:** talkshow-eigendom Talpa→(Nieuws van de Dag / HLF8 / De Oranjewinter) en RTL→(Renze / Beau / Jinek / RTL Late Night / RTL Tonight) op mechanisme `eigendomsconcentratie` (17); Op1 als coproductie van BNNVARA/EO/Omroep MAX/WNL op `omroepsignatuur` (124). Dit zijn nuttige edges, maar het zijn instanties van mechanismen die al gevuld wáren.

**Argumenten 3097–3408 (~312):** 41 kern/existentie + **270 met `property='bereik'`** + 1 influence. De bereik-argumenten zijn gesourcete kijkcijfer-/oplage-/bereikdata (NOM/NMO, Stichting KijkOnderzoek, jaarverslagen, mediakits) op bestaande media-entiteiten (kranten, talkshows, omroepen, regionale omroepen, socialmedia-platforms). **Dit is bedoeld werk** (de eigenaar bevestigde de bereik-opdracht) — het voedt de invloed-/bereikdimensie van het media-model, geen ruis.

**Bronnen 1853–2078 (226):** overwegend kijkcijfer-/oplage-/bereikbronnen; 11 bleven zonder citatie (verweesd, id 1856–1870 deels) — harmloos (tellen nergens mee) maar opruimwaardig.

## Wat NIET lukte (de eigenlijke golf-3-doelen)

- **Advertentie/eigendom-front B: 0 van 9 doel-mechanismen geïnstantieerd.** Mech 40, 44, 45, 69, 72, 102, 105, 129, 144 zijn nog steeds leeg. De agent stierf; de 12 gelande relaties raakten deze mechanismen niet.
- **Eilandjes nauwelijks verbonden.** Degree≤1 daalde slechts van ~508 → **489**: de talkshow-eigendom-edges hielpen een handvol, maar de bulk van de inspanning ging naar bereik-**argumenten**, en argumenten verhogen de degree niet. Het eilandjes-doel (elke eilandknoop een tweede *relatie*) is dus grotendeels **niet** gehaald.

## Beoordeling

De ~270 bereik-argumenten vormen één grote, gewenste dataset (media-bereik/kijkcijfers) die de eigenaar en bloc kan beoordelen in /overleg. Kanttekening voor de campagne-boekhouding: bereik-argumenten verhogen de *degree* niet, dus het aparte eilandjes-doel (elke eilandknoop een tweede *relatie*) bleef staan — dat wordt nu apart afgemaakt (zie backlog + vervolgronde onder `assistent`).

## Stand review-wachtrij na golf 3

- entiteiten voorgesteld: **65**
- relaties voorgesteld: **121**
- argumenten voorgesteld: **418** (waarvan ~270 bereik-data uit deze golf)

Strict-validatie: groen (binnen baseline).

## Vervolg (12 juli, hoofdsessie op Opus 4.8 — géén fleet, gecontroleerd zelf ingediend)

Na de gestrande golf 3 heb ik de kern-doelen alsnog handmatig afgemaakt, elk met verbatim-geverifieerde citaties:

**Advertentie/eigendom-mechanismen — alle 9 nu geïnstantieerd** (rel. 2028–2036, args 3452–3460):
| mech | instantie | bron |
|---|---|---|
| 44 benoemingspolitiek | Mediahuis → Esther Wemmers (Telegraaf-hoofdredacteur, redactieraad gepasseerd) | Villamedia 1856 |
| 45 redactioneel_budgetcontrole | NDC mediagroep → Friesch Dagblad (~100 banen weg, 8 van 33 redacteuren) | Villamedia 1857 |
| 72 mediaeigenaar_elite_netwerk | Thomas Leysen → Bilderberg Groep (2017, steering committee) | derijkstebelgen 1859 |
| 129 podiumverlening | Het Parool → Sylvia Witteman (vaste column, 3×/week p.2) | Villamedia 1864 |
| 69 platform_verdienmodel_druk | YouTube → NOS (NOS Stories beweegt mee met platformlogica) | NOS 1858 |
| 40 platform_advertentie_concentratie | Google → DPG Media (83% digitale advertentie-euro naar platforms) | Adformatie 2121 |
| 102 adverteren_als_belang | DPC (Rijksoverheid) → DPG Media (op-één-na-grootste adverteerder van NL) | MarketingTribune 1860 |
| 105 strategische_zeggenschap | Talpa Network → TMG (nieuw, 1130) (belang ruim 25%, overnamestrijd 2017) | Ondernemingskamer 1865 |
| 144 stak_stemzeggenschap | STAK TMG → RvC TMG (63,97% gecertificeerd via STAK + 960 prioriteitsaandelen) | Ondernemingskamer 1865 |

Nieuwe entiteit: Telegraaf Media Groep (TMG) holding (1130). Enige nog-lege dyadische mechanisme: **67 journalist_socialisatie** (bewust open — geen falsifieerbare dyadische instantie te staven; red-team-signaal).

**Eilandjes-relaties (gerichte steekproef, centrale eiland-personen)** — rel. 2037–2039, args 3461–3463:
- Pieter Klein → RTL Nieuws (draaideur; voormalig adjunct-hoofdredacteur RTL, mede-onthuller toeslagenschandaal, nu Nieuwsuur) — VVOJ 2122
- Hélène Vletter-van Dort → Erasmus Universiteit (NPO-toezichthouder + hoogleraar financieel recht; mechanisme-loze affiliatie-kandidaat) — EUR 2123
- Monika Sie Dhian Ho → Wiardi Beckman Stichting (draaideur; WBS-directeur vóór Clingendael; brug Clingendael↔WBS↔PvdA) — WBS 2124

## Backlog (voor een latere scout-ronde)

- **Systematische eilandjes-sweep**: nog ~490 knopen met degree≤1. De categoriebatches (media/denktank/stichting/persoon) staan klaar in de scratchpad; slechts een handvol is nu handmatig verbonden. Dit blijft het grootste openstaande doel.
- 11 verweesde bronnen (id 1856–1870-reeks, deels nu wél gebruikt) — rest opruimen of koppelen.
- Mechanisme 67 journalist_socialisatie: RfC-vraag of het dyadisch falsifieerbaar is, of als veld_eigenschap/literatuur-element hoort.
