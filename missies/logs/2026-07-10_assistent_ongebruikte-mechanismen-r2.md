# Missielog — ongebruikte mechanismen r2: sourcing, tegenmacht, D66/PVV (golf 2 bijvul-campagne)

- **Datum:** 2026-07-10
- **Account:** `assistent` (via vier parallelle Claude Code-subagenten; zie r1 voor de opzet)
- **Scope golf 2:** de resterende mechanismen zonder instantie (sourcing 11, tegenmacht 6, advertentie/eigendom 9) + verdieping D66/PVV.

## Sourcing — 11/11 geïnstantieerd (rel. 1983–1994, args 3085–3096, bronnen 1845–1852)

| mech | instantie |
|---|---|
| 48 voorlichter_informatiefilter | RVD → NOS (mediacode/mediamomenten; bestaande bron 768) |
| 54 denktank_naar_politiek | Clingendael → Tweede Kamer (position paper rondetafel, Kamerstuk primair) |
| 56 journalist_bronrelatie | Parlementaire Persvereniging → RVD (primeur-ruilrelatie; De Groene + Luyendijk) |
| 86 institutioneel_gezag | CPB → NOS (ramingen als gezaghebbend feit) |
| 97 persbureau_brongebondenheid | Tweede Kamer → ANP (SVDJ "Persbureau in Perspectief") |
| 106 klantvraag_persbureau | DPG Media → ANP (grootste betalende klant; verlenging 2020, primair) |
| 150 citaatautorisatie | RVD → Parlementaire Persvereniging (Track Changes-casus, 129 wijzigingen) |
| 151 draaideur_journalistiek_voorlichting | Gerard van der Wulp (nieuw, 1115) → RVD (NOS Journaal-hoofdredacteur → DG RVD 2004; + affiliatie-rel. 1990) |
| 152 pr_inhuur | Tata Steel → Edelman (nieuw pr_bureau, 1116; FTM-onderzoek) |
| 156 indexering | Tweede Kamer → NOS-hoofdredactie (Medialogica-toeslagenaffaire als ijkcasus) |
| 161 mediageniekheidsselectie | Op1 → Ab Osterhaus (33 afleveringen in één coronajaar; bestaande bron 798) |

Reviewer-aandachtspunten van de agent zelf: bij 97 loopt het rolpaar losjes (Kamer als bron i.p.v. voorlichter); bij 150/56 staat RVD pars pro toto voor de Haagse voorlichterij (alternatief anker: VoRa, 583); bij 156 staat de NOS-hoofdredactie pars pro toto voor de Haagse redacties. Eigen-geheugen-correctie: "DPG zegt ANP op" bleek onjuist — het tegendeel (verlenging) werd de bron.

## Tegenmacht — 6/6 geïnstantieerd (rel. 1977–1982, args 3079–3084, bronnen 1835–1844)

| mech | instantie |
|---|---|
| 43 klokkenluider_doorbraak | Ad Bos (nieuw, 1109) → Zembla (bouwfraude 2001) |
| 108 redactiestatuut_borging | Stichting Democratie en Media → Trouw (prioriteitsaandeel art. 13.2; ACM-verbintenissenvoorstel DPG/RTL 2025, primair) |
| 114 projectfinanciering_journalistiek | Fonds BJP (nieuw, 1113) → Ivo van Woerden (nieuw, 1114) |
| 139 redactieraad_instemming | NRC-redactieraad (nieuw, 1110) → NRC Media (benoeming Veldhuis 2024: raad selecteert, directie benoemt formeel) |
| 172 ledenraad_zeggenschap | Ledenraad BNNVARA (nieuw, 1111) → BNNVARA |
| 178 lezersfinanciering_isolatie | Leden van De Correspondent (nieuw, 1112) → De Correspondent (advertentievrij, volledig ledengeld) |

Vlag voor review: bestaande SVDJ-edges rel. 560–573 staan op mech 115 (publieke_groeifinanciering) waar 114 logischer oogt — mogelijke mis-toewijzing, niets aangepast.

## D66/PVV-verdieping (rel. 1970–1976, args 3072–3078, bronnen 1824–1834)

PVV → Wilders (partijbinding ontbrak nog!; Vossen-éénledenpartij-onderzoek + Nieuwsuur), PVV → Ongehoord Nederland (alliantie, `politicus_als_bron`, spiegelt PVV→Telegraaf), PVV → NVJ (flak, publieke_aanval, "tuig van de richel"-confrontatie), D66 → Mr. Hans van Mierlo Stichting (nieuw, 1108; `denktank_financiering_bias`, spiegelt VVD→Telders/PvdA→WBS), D66-partijbindingen Snel/Van Veldhoven/Schouw (completeren bestaande draaideur-edges 1198/1199/1213). Nuance-punt: beschrijving rel. 1972 koppelt NVJ-verzoek en Wilders' weigering iets te direct (auteur-PATCH op relaties = 403); argument 3074 is wél precies — reviewer kan de beschrijving gladstrijken bij merge.

## NIET afgerond: advertentie/eigendom-batch (9 mechanismen)

De subagent voor mech 40, 69, 102 (advertentie) en 44, 45, 72, 105, 129, 144 (eigendom) strandde op de **sessielimiet** (reset 23:30) ná het onderzoek/de quote-verificatie maar vóór het indienen — er is niets van geland. Deze batch staat open voor een vervolgronde (r3). Mech 112 (partijfinanciering) kreeg zijn instantie al in golf 1 (ReMarkAble→BBB, rel. 1928).

## Open eindjes (aanvulling op r1-backlog)

- ACM-verbintenissenvoorstel (bron 1837) is een rijke ader: SDM-prioriteitsrecht wordt uitgebreid naar alle DPG-landelijke titels incl. RTL Nieuws/NU.nl + twee nieuwe titel-stichtingen (toekomstige 108/139-instanties); DPG's "tien principes" = kandidaat-edge per titel.
- Tweede instanties: Stephan Schrover (ANP→RVD, mech 151; LinkedIn-scrape-kandidaat), Arthur Gotlieb/toeslagenaffaire (mech 43), Ongehoord NL→PVV omgekeerd (framing), Reinette Klever (PVV↔ON-draaideur), D66→BZK Wfpp-financiering VMS (patroon rel. 700/701).
- `scripts/archiveer_bronnen.py` draaien voor de ~40 nieuwe url-bronnen.

## Balans

Golf 2: 3 van 4 agents afgerond, 0 API-fouten, 0 409's bij de gelande batches; 24 nieuwe relaties, 25 argumenten, 8 nieuwe entiteiten, 21 bronnen.
