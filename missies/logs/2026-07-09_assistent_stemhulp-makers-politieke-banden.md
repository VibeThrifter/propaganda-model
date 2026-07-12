# Missielog — makers van stemhulpen & hun politieke banden

**Datum:** 2026-07-09 · **Account:** assistent (bijdrager) · **Opdracht eigenaar:** "wie maken kieskompas/stemwijzer en wat zijn hun politieke banden?" → vervolg: "de politieke banden van de mensen die ze samenstellen/managen; desnoods LinkedIn-scrape; clubjes/draaideur." Merge: **via admin (maxime)**.

## Methode
Drie parallelle onderzoeksagenten (Krouwel / ProDemos-directie+RvT / Kieskompas-team+andere stemhulpen), daarna **LinkedIn-scrape** (`tools/linkedin/`, sessie leefde nog) van 6 profielen voor de draaideur/loopbaan. Alle externe kern-quotes zelf verbatim herverifieerd via WebFetch (ProDemos-directie/RvT/missie, parlement.com Bijleveld & Van Raak, PvdA-Katwijk, RD) vóór indienen.

## Kernbeeld
- **Kieskompas** = commercieel + academisch bureau. Oprichter/mede-eigenaar **André Krouwel** (VU; oud-PvdA-deelraadslid Amsterdam). Directeur **Willem Blanken** komt uit de **reclamewereld** (Signum/FHV-BBDO) — géén partijband (LinkedIn corrigeert web: directeur al sinds 2016). Methode: het bureau plaatst zélf de partijen.
- **ProDemos** (StemWijzer/StemmenTracker) = **staats-instituut in de praktijk**: directeur **Eric Stokkink** stapte rechtstreeks van **BZK** (de financier) over; RvT-voorzitter **Ank Bijleveld** (CDA, oud-min. Defensie + oud-staatssecr. BZK); RvT-lid **Ronald van Raak** (SP-top); RvT-lid **Martijn Bennis** (oud-ANP, stond al in model). Élke RvT-benoeming vergt goedkeuring van de minister BZK. Programmaleider **Matthijs van Tuijl** = PvdA-wethouder Katwijk.

## Ingediend + gemerged (via admin, maxime) — validator groen
Bronnen #1550-1557. Nieuwe personen #1041-1045 (Stokkink, Blanken, Van Raak, Bijleveld, Van Tuijl). Relaties #1846-1857 (arg #2691-2702), alle affiliaties als `draaideurconstructie` #18, financier als `denktank_financiering_bias` #52:
- Stokkink→ProDemos (bestuurder), Stokkink→**BZK** (draaideur, financier).
- Blanken→Kieskompas (bestuurder; bron LinkedIn).
- Van Raak→ProDemos (RvT), Van Raak→**SP** (lidmaatschap).
- Bijleveld→ProDemos (RvT-vz), Bijleveld→**CDA**, Bijleveld→**Defensie** (draaideur oud-minister).
- Van Tuijl→ProDemos (personeel), Van Tuijl→**PvdA**.
- Krouwel (bestaand #891)→**PvdA** (lidmaatschap, deelraad).
- **BZK→ProDemos** (financiering) — de financier-edge; brug ProDemos↔BZK verschijnt vanzelf via Stokkink + de subsidie.

## Reeds in model (niet gedupliceerd)
Krouwel #891 (→Kieskompas, →VU), Bennis #272 (→ProDemos-RvT, →ANP), Kieskompas #872 (→NOS, →Trouw).

## Niet ingediend / eerlijke bevindingen
- **Clubjes/lidmaatschappen via LinkedIn:** alle 6 profielen gaven **0 lidmaatschappen** — Bilderberg-achtige netwerken niet via LinkedIn te staven; niet verzonnen.
- **Krouwel-LinkedIn** gaf 0 (é-slug brak de detailpagina's); web dekt hem al.
- **Anne Valkering "oud-raadslid":** LinkedIn weerlegt dit (junior webredacteur Gemeente Amsterdam, géén raadszetel/partij) → niet als partijband gemodelleerd.
- **Kutiyski / Kroon / Valkering:** geen partij-/machtslijn → niet als aparte knoop gemodelleerd (model-focus).
- **Datering affiliaties:** LinkedIn geeft exacte start/eind; niet als active_from/until opgeslagen (kandidaat voor vervolg → draaideur-gantt).
- **Stemhulp→publiek mechanisme** (stemhulp kanaliseert kiezerskeuze) + **AP-waarschuwing AI-chatbots als stemhulp** (okt 2025, "stofzuigereffect") + **DPG-verwevenheid** (Trouw mede-oprichter Kieskompas; VK/AD/Parool/NU.nl eigen stemhulpen): structureel sterk maar vergt een theorie-element/RfC → kandidaat voor vervolg, niet in deze instantielaag-batch.

## Totaal
8 bronnen, 5 entiteiten, 12 relaties, 12 argumenten. Alles gemerged via admin; golden-snapshot groen, geen fouten boven de baseline.
