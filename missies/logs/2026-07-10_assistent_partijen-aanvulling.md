# Missielog — partijen-aanvulling (front A van de bijvul-campagne)

- **Datum:** 2026-07-10
- **Account:** `assistent` (via drie parallelle Claude Code-subagenten)
- **Opdracht:** de dekkingsaudit toonde maar 14 partij-entiteiten; BBB, JA21, Volt, DENK, PvdD, SGP, 50PLUS en BIJ1 ontbraken volledig, plus geen GL-PvdA-fusie-entiteit. Alle negen toegevoegd met partijbinding-edges (mech. 163, partij→persoon, `lidmaatschap`) en waar bronbaar media-banden. Alles `voorgesteld`.

## Oogst (samenvatting; details in de agent-rapporten)

**Bronnen 1776–1798 (23 st.):** overwegend DNPP/RUG-partijgeschiedenissen (institutioneel), Parlement.com-biografieën, NOS/Joop/Netkwesties-nieuwsstukken, GL-PvdA-persbericht (primair). Alle citaten verbatim geverifieerd tegen de live pagina's.

**Entiteiten 1064–1089 (23 st.):** partijen BBB (1080), JA21 (1081), 50PLUS (1082), Volt (1064), DENK (1065), BIJ1 (1066), PvdD (1071), SGP (1072), GroenLinks-PvdA (1073); pr_bureau ReMarkAble Communicatie (1083); personen Van der Plas, Vermeer, Eerdmans, Nanninga, Nagel, Krol, Dassen, Van Lanschot, Kuzu, Van Baarle, Thieme, Ouwehand, Van der Staaij, Stoffer, Timmermans, Klaver. Hergebruikt: Sylvana Simons (712), NRC (10), RTL Nederland (8), Reformatorisch Dagblad (566), GroenLinks (153), PvdA (56), ThePostOnline (528), WNL (144), VARA (995).

**Relaties 1910–1937 (28 st.), argumenten 3004–3034:** per partij ≥2 partijbinding-edges naar leiders/prominenten; daarnaast de inhoudelijk interessantste vondsten:

| rel | verband | mechanisme |
|---|---|---|
| 1928 | ReMarkAble → BBB, donor (174.000 euro giften in natura, enige financier TK2021) | **112 partijfinanciering — eerste instantie ooit** |
| 1930 | Henk Vermeer → ReMarkAble, bestuurder (personele brug bureau↔partij; org→org bewust niet opgeslagen) | 18 draaideur |
| 1925 | DENK → NRC, flak ("heksenjacht"-video na trollen-onthulling, 2017) | 11 publieke_aanval |
| 1926 | Sylvana Simons → RTL, personeel (media→politiek-draaideur) | 18 draaideur |
| 1933/1934/1937 | Nanninga→ThePostOnline, Eerdmans→WNL, Nagel→VARA (gedateerde media-affiliaties) | 18 draaideur |
| 1914 | SGP → Reformatorisch Dagblad, alliantie (verzuilingsband refozuil) | **mechanisme-loos kandidaat** |
| 1915/1916 | GroenLinks-PvdA → GroenLinks / PvdA, alliantie ("fusieverband/gezamenlijke lijst") | mechanisme-loos kandidaat |

## Eerlijk niet ingediend

- Simons' "PowNed-verleden" (uit de opdracht): niet staafbaar — het was NPS/TMF/SBS/RTL; opdracht gecorrigeerd i.p.v. gevolgd.
- Veelgeciteerde RD-zin ("geen krant … zo'n hechte band") bleek nergens verbatim te staan → vervangen door wél geverifieerde passages.
- Flak-incidenten rond BBB/JA21/50PLUS: niets dat de lat haalde; DENK-persweren (verkiezingsavond 2017): geen primaire bron met citeerbare zin.
- PvdD- en Volt-media-banden: geen structurele band gevonden; alleen partijbinding gemodelleerd.

## Open eindjes (backlog)

- Eerdmans→PowNed (gesourcet in bio, klaar om in te dienen); Nanninga↔Jalta.nl (entiteit ontbreekt); Van der Plas→Agrio/Pig Business (entiteit ontbreekt); Öztürk en Azarkan (DENK) als personen; Wim Groot Koerkamp (BBB/ReMarkAble).
- RD-hoofdredactie↔SGP-lidmaatschap (bv. C.S.L. Janse) zou van kandidaat 1914 een echte mech-163-instantie maken; RfC-idee "verzuilingsband/zuilkrant" als er meer partij↔krant-paren komen.
- GL-PvdA: fusie wordt 2026 geformaliseerd → `active_until` op GroenLinks/PvdA wordt dan relevant.
- LinkedIn-scrape-kandidaten: Vermeer, Groot Koerkamp, Dassen (ABN AMRO), Van Lanschot. Scraper in deze golf bewust niet gebruikt (publieke bronnen dekten beter; parallelle sessies botsen).

## Balans

35 writes zonder fouten of 409's; stance-balans: overwegend supporting (bestaansclaims), 1 flak-edge; tegenspraak-kandidaten genoteerd in backlog.
