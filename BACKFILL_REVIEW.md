# Backfill-review M0.4 (juni 2026)

Werklijst van `scripts/migrate_backfill_koppelingen.py` (verbeterplan M0.4): alle
koppelingen die de migratie heeft gezet, ter review door de eigenaar. Elke gezette
koppeling is herkenbaar aan de tag **`backfill-M0.4 (agent; review eigenaar)`** in
`instantiations.notes`, `entity_roles.notes` en `edit_log`. Backfill-instantiaties
kregen exemplariteit **0,8** (bewust onder de 1,0-norm: nog niet handmatig gewogen —
bij review ophogen of verlagen).

Reviewen = per blok steekproefsgewijs controleren; afkeuren = `mechanism_id` weer op
NULL + instantiatie verwijderen (of beter: ander mechanisme kiezen). Zodra M0.6 staat,
lopen correcties via het bijdragepad.

## 1. Relatie → mechanisme (108 koppelingen)

| Mechanisme | Relatie-ids | Motivering |
|---|---|---|
| `eigendomsconcentratie` | 12, 14, 17, 159, 195–199 | aandeelhouderschap/eigendom van nieuwsmedia: duopolie-aandeelhouders, ANP-eigendom, consolidatietrail PCM/Sanoma/TMG |
| `familiezeggenschap` | 18, 74, 75, 156 | persoon/familie controleert het eigendomsvehikel (Talpa, Concentra, VP Exploitatie, Mediahuis Partners) |
| `systemisch_eigenaarschap` | 70–72, 160, 182–185, 200, 289–293 | BlackRock/Vanguard/GBL als stille aandeelhouder in (adverterende) concerns |
| `denktank_financiering_bias` | 40, 41, 44, 45, 64, 152–154 | belanghebbende financiert/stuurt denktank of wetenschappelijk bureau (NAVO/ministeries → HCSS/Clingendael; partijen → eigen bureaus) |
| `belang_elite_netwerk` | 60–62, 331–334 | bedrijfstop in Bilderberg-fora — **let op: 60–62 zijn omgekeerde duplicaten van 333/332/331** (M2.6-samenvoegkandidaat) |
| `partijlijn` | 125, 126, 131, 336, 343, 345, 347, 349, 352, 354, 356, 379, 381, 383, 385, 387, 393 | partijlidmaatschap/-functie van politici; bij de persoon→partij-gevallen is de instantierichting omgekeerd t.o.v. het mechanisme (partij→politicus) |
| `parlementaire_controle` | 49, 50, 256–258 | Kamerleden/parlement als controleurs (Toeslagenaffaire) |
| `politicus_als_bron` | 103, 104, 127, 259–262 | politicus voedt media als bron / dwingt agendering af |
| `vakbond_bescherming` | 137–139, 319–322 | NVJ/Free Press Unlimited beschermen journalisten (doelen zijn outlets, mechanisme mikt op journalist — outlet-granulariteit) |
| `politieke_synchronisatie` | 287, 288 | CDA/VVD volgen de Atlantische consensus; richting omgekeerd t.o.v. mechanisme (elite_forum→politicus) |
| `externe_mediafinanciering` | 408 | OSF financiert Stichting Democratie en Media (doel is borgingsstichting, geen mediaorganisatie — eventueel later eigen mechanisme) |
| `toezicht_tandeloosheid` | 117–119, 122, 123 | CvdM signaleert zonder in te grijpen; RvdJ kan niet sanctioneren |
| `toezichthouder_interventie` | 124, 330, 372 | ACM-mededingingstoezicht, NU.nl-borgingsstichting, Mediawet-handhaving |
| `expert_framing` | 120, 121 | WRR-rapporten sturen het mediadebat |
| `academische_socialisatie` | 303, 304 | UvA Journalistiek vormt en levert redactiepersoneel |
| `expert_legitimatie` | 325, 326 | Van Rossem als vaste commentator |
| `geweld_intimidatie` | 48 | moord op Peter R. de Vries |
| `onderzoeksjournalist_doorbraak` | 88, 171, 172 | De Correspondent/Brandpunt/RTL Nieuws braken Toeslagenaffaire/Bulgarenfraude open (doel is hier het onderzochte instituut i.p.v. het publicerende medium) |
| `burgerinitiatief_druk` | 90 | BOinK agendeerde de problemen jaren eerder |
| `onafhankelijk_medium_tegenwicht` | 263, 264, 305, 306 | De Correspondent/Gezond Verstand tegenover de mainstream-consensus |
| `denktank_levert_expert` | 38 | De Wijk als HCSS-directeur (richting omgekeerd) |
| `draaideur_politiek_institutie` | 341 | Jack de Vries als staatssecretaris Defensie |
| `pakketjournalistiek` | 425, 426 | AFP/Reuters als groothandel achter het ANP-buitenlandnieuws |

## 2. Kandidatenlijst nieuwe mechanismen (restgroep, M2.3-input)

Zes relaties passen op geen bestaand mechanisme; ze blijven bewust ongekoppeld
(`KOPPEL-REL-MECH` in de validator houdt ze zichtbaar) tot er via een theorie-RfC
(M2.3) een mechanisme voor bestaat — of tot review ze verwijdert:

| Relatie | Inhoud | Voorstel |
|---|---|---|
| #409 ECB —financiering→ EIB | Eurosysteem koopt EIB-obligaties; EIB financiert vervolgens DPG | nieuw mechanisme *publieke kapitaalketen* (eigendom/financiering, belanghebbende→belanghebbende), of accepteren dat deze upstream-schakel buiten het mediamodel valt |
| #225 OMT —alliantie→ RIVM | adviesorgaan gekoppeld aan gezagsinstituut | nieuw mechanisme *institutionele gezagsketen* (sourcing, gezagsinstituut→gezagsinstituut) |
| #242 Radboud Universiteit —oppositie→ ANP | academisch onderzoek legt mediamechanisme bloot | nieuw mechanisme *academische doorlichting* (tegenmacht, kennisinstituut→mediaorganisatie) |
| #411 BlackRock —adviseur→ Europese Commissie | belanghebbende als ingehuurd adviseur van regelgever | nieuw mechanisme *belanghebbende als adviseur* (sourcing, belanghebbende→gezagsinstituut) |
| #327 Chris Oomen —beinvloeding→ NOS | "beïnvloedt **indirect** via persbureau" | dit is een opgeslagen afgeleide pijl; de keten Oomen→ANP→NOS bestaat al. Advies: **verwijderen** (afgeleiden worden ter plekke berekend, niet opgeslagen) |
| #328 John de Mol —beinvloeding→ RTL | "was via Talpa verbonden", historisch en vaag | advies: **verwijderen** of herformuleren tot een concrete eigendoms-/draaideurrelatie met datering |

## 3. Entiteit → rol (11 toekenningen)

| Entiteit | Rol | Motivering |
|---|---|---|
| #52 Belastingdienst | `gezagsinstituut` | uitvoeringsmacht met informatiemonopolie (Toeslagenaffaire) |
| #71 Koningshuis | `gezagsinstituut` | staatsinstituut; aanwezig in elite-fora |
| #80 McKinsey | `belanghebbende` | consultancy met beleidsbelangen; sponsor Nationale DenkTank |
| #103 Radboud Universiteit | `kennisinstituut` | universiteit; onderzocht ANP-afhankelijkheid |
| #104 UvA Journalistiek | `kennisinstituut` | journalistiekopleiding |
| #122 Hill+Knowlton | `lobbyist` | PR-/lobbybureau, defensielobby |
| #123 KPMG | `belanghebbende` | Big Four met overheidsopdrachten |
| #124 Ernst & Young | `belanghebbende` | Big Four met overheidsopdrachten |
| #126 Uber | `belanghebbende` | platformbedrijf als lobby-actor |
| #127 Royal HaskoningDHV | `belanghebbende` | adviesbureau als lobby-actor |
| #128 Microsoft | `belanghebbende` | techconcern als EU-lobby-actor (functie in dít model; structureel ook `techplatform` verdedigbaar) |
| #107 Tweede Kamer | `parlementair_controleur` | had alleen een losse `politicus`-rol; primaire rol nu consistent met relatie #256 (`parlementaire_controle`). De oude rol blijft als extra rij staan |
| #125 KLM | `belanghebbende` | had alleen een losse rol zonder primaire; staatsgesteund bedrijf met mediabelang |

Daarnaast kregen álle entiteiten met een primaire rol maar zonder instantiatie een
rol-instantiatie (exemplariteit 0,8) en álle gekoppelde relaties zonder
instantiations-rij een mechanisme-instantiatie — mechanisch, geen oordeel.

## 4. Richting-mismatches (systematisch, voor M2.6)

Een terugkerend patroon in de mapping: de **instantierichting** is soms omgekeerd aan
de roltopologie van het mechanisme (persoon→partij vs. partij→politicus; medium→
Belastingdienst vs. journalist→mediaorganisatie). Dat is geen koppelfout maar een
datamodel-kwestie: `instantiations` kent geen richtingstoets. Aanbeveling: bij M1.7/M2.6
een validator-check toevoegen die de bron-/doelrollen van de relatie-eindpunten
vergelijkt met de mechanisme-rollen, en de gevallen hierboven dan herbeoordelen.
