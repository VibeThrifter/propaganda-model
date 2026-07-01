# 2026-07-01 — Tijd-correctie incident-grenzen + RfC crisis_bronmonopolie

**Aanleiding.** Audit van de 56 gesloten tijdvensters (`active_until` gezet) op 493 goedgekeurde
praktijkrelaties wees uit dat een deel van de grenzen niet het einde van de *relatie* dateerde
maar het einde van een *incident* (toeslagenaffaire, COVID-piek, Irak-episode). Principe: een
incident bewijst dat de relatie op dat moment bestond — een punt bínnen de looptijd, geen grens.
Een grens blijft alleen staan als ze echt is (oprichting/bestaan van de entiteit, of een bewezen
einde: verkoop, vertrek, opheffing, overlijden). Eigenaar koos reikwijdte "alle incident-fouten"
+ RfC-concept voor het onderliggende algemene mechanisme.

## 1. Tijd-correctie (admin-pad, `maxime`-token, expliciete opdracht eigenaar)

18 relaties gepatcht via `PATCH /api/relations/<id>` (motivatie per groep in `edit_log`):

| groep | relaties | wijziging |
|---|---|---|
| Affaire-tegenmacht | 88, 90, 65 | `active_until` 2021 → NULL (relatie loopt door; start blijft: 2013 = oprichting De Correspondent, 2010/2001 gedocumenteerd begin) |
| RTL-onderzoek | 172 | beide → NULL (2013 = CAF-feiten, niet het begin van RTL's onderzoeksrelatie) |
| Belastingdienst→media (pr_subsidie) | 42, 86, 87, 254, 255 | beide (2013–2019) → NULL (frame-incident; dienst doet doorlopend PR) |
| RIVM→media (bron_afhankelijkheid) | 143, 144, 145 | beide (2020–2022) → NULL (COVID-piek; RIVM is doorlopend mediabron) |
| CDA→media (Irak) | 98, 99, 100, 105 | `active_until` 2003 → 2012 (bewezen einde = einde regeringsdeelname, val Rutte I) |
| Twijfelgevallen | 49 (Omtzigt) | `active_until` 2021 → NULL (zit nog in de Kamer) |
| | 50 (Leijten) | `active_until` 2021 → 2023 (bewezen einde: Kamer-vertrek) |

Blijven ongemoeid (bewezen einde): eigendomsoverdrachten (PCM, Sanoma, Talpa, TMG), rol-eindes
(Karimi, Van Nieuwenhuizen, CDA→Omtzigt), opheffing/overlijden (OMT, Peter R. de Vries), en
rel. 256 (Tweede Kamer→Belastingdienst, 1815–open, al correct).

Naspel: `generate_viz.py` geregenereerd; `validate_model.py --strict` groen (golden snapshot ok).

## 2. RfC #16 — mechanisme `crisis_bronmonopolie` (bijdragerspad, `assistent`)

De drie gecorrigeerde episode-groepen delen één patroon dat de theorielaag nog mist: de
**episodische verheviging** van `bron_afhankelijkheid` tot een tijdelijk quasi-monopolie
(indexing/sferen-van-consensus). Ingediend als `nieuw_theorie_element` (mechanisme, Sourcing,
direct, gezagsinstituut→mediaorganisatie) met freeze-test, afgrenzing (o.a. waarom niet als
influence-argument op bestaande relaties), falsificatiecriterium (bronvermeldingsanalyse
crisis- vs. routineperiodes), twee tijd-geboxte instantiaties (RIVM→NOS 2020–2022;
Belastingdienst→NOS 2013–2019) en bronnen Bennett 1990 (id 55), Hallin 1986 (id 48),
Herman & Chomsky 1988 (id 2). Sinds de tijd-correctie leven episodes nergens meer als gedateerd
verschijnsel; dit mechanisme geeft ze een eigen, tijd-geboxte plek naast de staande relatie.

**Status: wacht op 2 menselijke reviewer-akkoorden** (agent-reviews tellen niet). Bij acceptatie
landen de twee instantiaties als `voorgesteld` en vergen ze elk nog een aparte merge.
