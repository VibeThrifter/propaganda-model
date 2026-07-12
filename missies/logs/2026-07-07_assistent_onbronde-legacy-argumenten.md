# Campagne: onbronde legacy-argumenten sourcen — assistent — 2026-07-07

**Aanleiding.** Eigenaar spotte in de viz een mager, bronloos argument (arg 220 "Zelfs onafhankelijke
media gebruiken ANP als basismateriaal", op rel 218 ANP→De Correspondent). Analyse: het is 1 van
**184 legacy supporting-roots** (`contributed_by='legacy'`, `ongecontroleerd`) **zonder enige citatie**
— allemaal op relaties. De `[nn-nn]` in `reasoning` is een seed-regelverwijzing, geen echte bron.
Doel: elk sourcen met een **echte verbatim citatie + herschreven claim (revisie)** die laat zien hóe
het uit de bron volgt; onbronbaar/onjuist → herkeuring/afwijzing (geen nepbron).

## Methode (kwaliteitslat)
- Sourceable & waar → `POST /api/arguments/<id>/revisie` (nieuwe `voorgesteld`, `reviseert_id`=oud;
  supersedet op merge). Verbatim quote zelf nagecheckt vóór indienen.
- Niet sourceable / feitelijk mis → herkeuring (`betwist`) of afwijzen/verwijderen. Géén fabricatie.
- Alles `voorgesteld`; merge/afwijzing = mens (hier op expliciete "via admin").

## Pilot (4 items) — afgerond
| arg | rel | claim | uitkomst | bron (verbatim) |
|----|----|-------|----------|-----------------|
| 40 | NAVO→HCSS | NAVO financiert HCSS | ✅ revisie **2122** (gemerged) | HCSS Client Overview 2024: "NATO HQ Supreme Allied Command Transformation" / "NATO Defense College" + About HCSS "…Foreign Affairs and Defence are among our regular customers." |
| 39 | HCSS→RTL | HCSS levert experts aan RTL | ✅ revisie **2123** (gemerged) | HCSS-post RTL Nieuws (Mertens, verbatim) |
| 41 | McKinsey→Nat. DenkTank | McKinsey sponsor | ✅ revisie **2124** (gemerged) | consultancy.nl "…betrokken als supporter en kennispartner." |
| 55 | ERT→Leysen | Leysen lid ERT | ⚠️ **THIN** → `betwist` (herkeuring) | ERT noemde hem "member" (2022) maar niet op huidige roster (2026); zetel → dsm-firmenich-CEO |

Bronnen geregistreerd: 1129 (HCSS Client Overview 2024, primair), 1130 (About HCSS, primair),
1131 (HCSS RTL-post, grijs), 1132 (consultancy.nl, regulier). Oude args 39/40/41 → `verouderd`+`vervangen`.

**Admin (maxime, "via admin"):** revisies 2122/2123/2124 gemerged; **rel 218 verwijderd** (ANP→De
Correspondent — feitelijk fout: De Correspondent draait geen ANP-copy; arg 220 mee-gecascadeerd);
arg 55 → `betwist`.

## Verificatiediscipline
Twee niet-verbatim quotes van de onderzoeks-agent onderschept: (1) de Mertens/RTL-zin (vervangen door
de echte quote van de HCSS-pagina); (2) de HCSS Client Overview PDF was Cloudflare-geblokkeerd voor
curl — via WebFetch de binaire PDF opgehaald en lokaal met pdfminer geëxtraheerd om "NATO"-vermeldingen
verbatim te bevestigen. Niets op onbevestigde quote ingediend.

## Aanpak gekozen: B (parallelle onderzoeks-agents per batch; quotes zelf verbatim geverifieerd)

Verdeling resterende 179 onbronde legacy-roots naar filter: sourcing 70, advertentie 32, ideologie 30,
tegenmacht 18, flak 15, eigendom 11, cross_filter 3. Sourcing eerst (hoogste opinievorming-waarde).

### Batch 1 — sourcing/denktank/officiële-bronnen (20 claims, 3 agents)
**7 SOLID → revisie ingediend (`voorgesteld`):**
- 145 RIVM→NOS (rev 2134) — Medialogica/HUMAN: "…land in crisistijd wordt geleid door virologen met het RIVM voorop."
- 148 CPB→NOS (rev 2135) — De Groene (Hasekamp: "…invloed op het politieke discours is nergens zo groot als in Nederland") + NOS-doorrekening.
- 154 Defensie→HCSS · 155 Defensie→Clingendael · 156 BuZa→Clingendael (rev 2136/2137/2138) —
  **Kamervragen Aanhangsel 2022/23 nr. 3175** (PROGRESS: BZ+Defensie elk €1 mln/jr, 60–40% Clingendael/HCSS).
- 165 HCSS→Volkskrant (rev 2139) · 166 HCSS→Telegraaf/De Wijk (rev 2140) — HCSS' eigen mediapagina's.
Bronnen 1141–1146. Verbatim zelf gecheckt; twee agent-quotes gecorrigeerd (Kamervragen "bestellen" i.p.v.
"besteden"; De Wijk-column = Trouw, niet Telegraaf).

**2 uitgesteld (clingendael.org geeft 403):** 163 Clingendael→Volkskrant, 164 Clingendael→Telegraaf —
waarschijnlijk waar/sourceable, andere bronroute nodig. Nog niet ingediend (geen onbevestigde quote).

**11 THIN → herkeuring-kandidaten** (per-outlet overclaim, niet-sourcebaar of deels weerlegd):
146, 147 (RIVM→RTL/DPG) · 149, 150 (CPB→Volkskrant/Telegraaf) · 151, 152, 153 (Politie→NOS/Telegraaf/RTL) ·
86 (Belastingdienst→Telegraaf, alleen aggregaat) · **87 (Belastingdienst→NOS — deels WEERLEGD**: retrospectieven
crediteren NOS/Nieuwsuur juist met onthullen) · 167 (NDT→NOS, zelf-gerapporteerd; NOS-item crediteert JOB) ·
64 (NAVO→Clingendael, geen verbatim). → wachten op "via admin" (status `betwist`).

**Belangrijk campagne-inzicht:** een groot deel van de legacy-per-outlet-claims **overclaimt** — de structurele
mechanisme-claim klopt vaak, maar de specifieke outlet-toewijzing/bias-lezing is niet gesourcet. Die horen
naar herkeuring, niet opgepoetst met een generieke citatie.

### Batch 2 — sourcing: denktank→media, OMT/corona, Omtzigt/toeslagen, Irak/WMD (22 claims, 3 agents)
Eigenaar: "herkeur via admin en ga door met batch 2, via subagents" (staande via-admin voor herkeuring).

**10 SOLID → revisie (`voorgesteld`, rev 2159–2168):**
- 225 OMT→NOS · 226 OMT→RTL · 227 OMT→RIVM (Erasmus Magazine; Villamedia; RIVM-OMT-pagina).
- 261 Omtzigt→NOS — NOS zelf: "…na vragen van CDA-Kamerlid Pieter Omtzigt."
- 168 NDT→Volkskrant · 170 WBS→Volkskrant (WBS/NDT eigen media-overzichten).
- 240 HCSS→NRC · 241 HCSS→AD · 238 Clingendael→NRC · 239 Clingendael→AD (HCSS' eigen fetchbare mediapagina's
  die de NRC/AD-content verbatim reproduceren; nrc.nl/ad.nl/clingendael.org blokkeren de fetcher). Bronnen 1161–1170.

**12 THIN → herkeuring (`betwist`):** 234, 235, 236 (ministerie→outlet, alleen generiek) · 262, 263 (Omtzigt→
Telegraaf/NRC, geen per-outlet-bewijs) · 99, 100, 105 (Irak, alleen aggregaat/edge-mismatch) · 169
(Teldersstichting→VK, geen artikel) · 237 (Clingendael→RTL, alleen geblokkeerde route). **2 afwijs-kandidaten
(feitelijk onjuist):** 264 (De Correspondent/Frederik werkte JUIST niet met Omtzigt) · 98 (WMD-"3x"-cijfer =
verzonnen, geen inhoudsanalyse).

## Voortgang
- **179 totaal → 42 behandeld** (17 revisie · 23 herkeuring · 2 uitgesteld: 163/164 Clingendael→VK/Telegraaf).
- **~137 resterend.** Volgende: rest sourcing (~28: o.a. NAVO→denktank output-steering, VVD/PVV-framing,
  RIVM/CPB/Politie→meer-outlets [grotendeels THIN], Van Rossem, Koningshuis/RVD), dan ideologie (30), flak (15),
  tegenmacht (18), advertentie (32); Bilderberg-elite-netwerk (61/333–336) als laatste (herkeuring-materiaal).
- **Terugkerend patroon:** think-tank-/officiële-actor-claims zijn goed te sourcen via de actor's eigen
  media-/financieringsopenbaarmaking; **per-outlet-reproductie- en bias-lezingen zijn meestal THIN** → herkeuring.
  Twee afwijs-kandidaten per batch die feitelijk onjuist blijken (87 toeslagen-NOS; 264 Correspondent; 98 WMD-3x).

### Batch 3 — orchestratie-workflow over álle 139 resterende claims
Eigenaar: "ga door, draai alle batches parallel in meerdere sub agents". `Workflow` (`source_wf.js`): 20 subagents
parallel, elk ~7 claims, gestructureerde output (SOLID/THIN/FALSE + verbatim quote + bron). Research-only; ík
verifieerde elk SOLID-citaat verbatim vóór indienen. (Eerste run faalde stil: `args` kwam als string binnen → script robuust gemaakt.)

Uitslag: **48 SOLID · 86 THIN · 5 FALSE**.
- **86 THIN + 5 FALSE → bulk-herkeuring** (`betwist`). 5 FALSE als afwijs-kandidaat: 43 (Fresen richtte géén denktank
  op), 47 (Van Rossem-Irak causaal onjuist), 244 ("Radboud-ANP-onderzoek" bestaat niet — was Nieuwsmonitor/Boumans),
  257 (RTL nam géén frame over — onthulde juist), 317 (Volkskrant is bewust NIET op TikTok).
- **16 peripheral SOLID → herkeuring** (verifieerbaar maar perifeer: passieve aandeelhoudersbelangen
  Vanguard/BlackRock/GBL, Bilderberg/WEF-aanwezigheid — geen invloedslijn op nieuwsbias). + 141 (FPU→NOS generiek),
  286 (NAVO→HCSS overlap/interpretatie), 118 (enige bron = activisten-campagnesite, onverifieerd).
- **30 bias-relevante SOLID → revisie** (elk citaat verbatim geverifieerd; ~6 workflow-URL's fout → opnieuw gezocht;
  VVD- en HCSS-PDF lokaal met pdfminer bevestigd): o.a. DPG/Mediahuis↔Google/Meta ("aan het infuus"), TikTok→NOS/NU.nl/RTL,
  DPG+Mediahuis-**duopolie bijna 95%** (svdj), ACM-stichtingen RTL/NU.nl + ACM-Mediahuis/TMG, NVJ-cao's, BOinK +
  RTL/Trouw toeslagen-doorbraak + De Correspondent, Talpa→ANP (De Mol), Metro↔Mediahuis, DPG↔VNU, P&G top-adverteerder,
  Wilders "tuig van de richel" + NRC-aanval, VVD/CDA↔NAVO, Van Rossem-column, Koningshuis↔RVD, Gezond Verstand.

## Eindstand campagne (184 onbronde legacy-roots)
- **~50 gerevideerd** (bron + herschreven claim): 3 gemerged (pilot), **47 `voorgesteld` — wachten op merge**.
- **~133 herkeuring** (`betwist`). DB: 132 legacy-roots betwist.
- **1 verwijderd** (arg 220 + rel 218, ANP→De Correspondent, feitelijk fout).
- **2 uitgesteld** (163/164 Clingendael→VK/Telegraaf; clingendael.org 403).
- Verbatim-discipline: talrijke gefabriceerde/onnauwkeurige agent-quotes onderschept; niets onbevestigds ingediend.

## Openstaand
- De **47 revisies staan `voorgesteld`** — pas na merge vervangen ze de oude onbronde versies. Merge = mens / "via admin".
- De **132 betwiste** roots wachten op herformulering-met-bron of definitieve afwijzing (m.n. de afwijs-kandidaten + perifere).
