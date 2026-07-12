# Missielog — Toeslagenaffaire: sentiment-scharnier + Trouw/Kleinnijenhuis + reversal-voorspelling

- **Account:** `assistent` (bijdrager) — alles `voorgesteld`, telt in niets tot een mens merget.
- **Datum:** 2026-07-08 (vervolg op `2026-07-08_assistent_correspondent-establishment.md`).
- **Vraag eigenaar:** meer mineerbare elementen uit de toeslagenaffaire? Outlets met pro-elite bias? Hoe is het sentiment omgekeerd? → gekozen scope: **alles** (#1 scharnier + #2 Trouw + #3 reversal-volgorde), plus de gevraagde bevinding over rel 171.

## Bevinding vooraf — rel 171 (Brandpunt→Belastingdienst)

Rel 171 draagt mechanisme **74 `onderzoeksjournalist_doorbraak`**, maar arg 173 beschrijft de **Bulgarenfraude-scoop (2013)** van Brandpunt/RTL Nieuws. Die scoop was journalistiek een echte onthulling, maar het **machts-effect** was consensus-*sluitend*: ze versterkte het 'fraude'-frame en joeg het fraudejacht-klimaat aan — het tegendeel van een "doorbraak" die de staat blootlegt. Dit is dezelfde spanning als DC rel 88 (doorbraak-mechanisme, sluit-valentie).

**Aanpak (model-honest, geen herclassificatie):** een `machtsvalentie=as:establishment:sluit`-annotatie op rel 171 lost het legibel op — *mechanisme = wát voor daad (onderzoeksdaad); machtsvalentie = welke kant het macht-effect op wijst (sluit)*. Ik codeer **niet** zelf om; of de mens rel 171 alsnog wil herclassificeren of een expliciete tijdlabel wil, is een menselijk oordeel. Aanbeveling: **niet herclassificeren** — de machtsvalentie draagt het, net als bij DC.

## Uitgevoerde queries (incl. betwiste keten)

| # | Query / bron | Uitkomst |
|---|---|---|
| Q1 | Villamedia/NOS/NPO — Journalist van het Jaar 2019 | ✅ **Pieter Klein (RTL) + Jan Kleinnijenhuis (Trouw)**, voor toeslagen-onderzoek. Jury (Villamedia, unaniem): "een grote maatschappelijke misstand blootgelegd" · "vasthoudend, met open vizier". |
| Q2 | HUMAN Medialogica *Het toeslagendrama in drie aktes* (bron **#289**, bestaat al) | ✅ **Verbatim** fase-2-kern: *"Als Trouw journalist Jan Kleinnijenhuis in september 2018 een rechtszaak van González Pérez bijwoont, constateert hij met eigen ogen hoe de Belastingdienst belangrijke stukken achterhoudt voor de rechter. Dat is het moment dat hij besluit om zich vast te bijten in dit dossier."* + *"Later sluit ook Pieter Klein van RTL Nieuws aan."* + fase-1: *"Brandpunt en RTL Nieuws onthullen hoe Oost-Europese bendes misbruik maken van het Nederlandse toeslagenstelsel."* |
| Q3 | Bulgarenfraude → strenge wet → affaire (causale keten) | ⚠ **Betwist.** Stichting Beroepseer: de strengere fraudewet trad al **1 jan 2013** in werking, vóór de Bulgarenfraude (**april 2013**) publiek werd → **katalysator/versneller, niet de enige oorzaak**. Meegenomen als geattribueerde nuance in de sluit-annotatie (rel 171) — niet monocausaal geclaimd. |
| Q4 | Pieter Klein / Kleinnijenhuis al in model? | ✅ **Pieter Klein = entiteit #473** (bestaat al, gekoppeld aan Nieuwsuur — niet aangeraakt). **Kleinnijenhuis ontbrak** → toegevoegd. |

**Wikipedia:** alleen als vindplaats (Bulgarenfraude-datering); ingediende bronnen zijn HUMAN Medialogica + (impliciet) de jury-berichtgeving, niet het lemma.

## Wat er al stond (niet gedupliceerd)

- **Fase 1 (pro-elite frame-adoptie):** rel 42/86/254/255 (Belastingdienst→Volkskrant/Telegraaf/AD/RTL, `pr_subsidie`) + rel 677 (Belastingdienst→NOS, `crisis_bronmonopolie`, "fraudeframe-episode 2013-2019") + rel 65 (NOS→BOinK, `schijndebat`). **Bewust géén machtsvalentie** hierop: dit zijn geen tegenmacht-edges maar plain Sourcing/beïnvloeding — de valentie-vraag ("opent of sluit deze tegenmacht?") is niet van toepassing.
- **Fase 2 (doorbraak):** rel 88 DC · rel 172 RTL Nieuws · rel 715 FtM · rel 171 Brandpunt (=Bulgarenfraude, zie bevinding).

## Ingediend (alles `voorgesteld`)

**Entiteit:** #990 **Jan Kleinnijenhuis** (persoon, rol 36 = onderzoeksjournalist — bewust wél 36, i.t.t. Frederik #818/rol 26: Kleinnijenhuis' werk legde de staat juist bloot).

**Relaties:**
- #1768 Kleinnijenhuis→Trouw(5) `personeel` mech 18 (draaideur), active_from 2018 + supporting-arg #2555 (citaat HUMAN #289).
- #1769 Trouw(5)→Belastingdienst(52) `oppositie` mech 74 (doorbraak), active_from 2018 + supporting-arg #2556 (citaat HUMAN #289) → geeft **Trouw z'n eigen fase-2-doorbraak-edge** (dicht de asymmetrie: Trouw stond eerder alleen in arg 2186 op rel 172 genoemd).

**Machtsvalentie-annotaties (aspect, tellen in niets) — het scharnier:**
- #2557 rel 1769 Trouw → `as:establishment:opent`
- #2558 rel 171 Brandpunt (Bulgarenfraude 2013) → `as:establishment:sluit` (met Beroepseer-nuance)
- #2559 rel 172 RTL Nieuws (fase 2) → `as:establishment:opent`
- #2560 rel 715 FtM (fraude-algoritmen) → `as:establishment:opent`

**Voorspelling:** #10 (`open`, deadline 2028-06-30, anker mech 173 `crisis_bronmonopolie`) — "politiek/rechter leidt de omslag, media volgen met vertraging", meetbaar via gecodeerde inhoudsanalyse.

## Verificatie (uitgevoerd)

`tegenmacht.py --preview`, edge-niveau:

| edge | richting |
|---|---|
| rel 171 Brandpunt (Bulgarenfraude 2013) | **sluit** |
| rel 88 De Correspondent (Frederik-reconstructie) | **sluit** |
| rel 172 RTL Nieuws (2017-19) | **opent** |
| rel 715 Follow the Money (algoritmen) | **opent** |
| rel 1769 Trouw (Kleinnijenhuis) | **opent** |

→ Het **sentiment-scharnier is legibel**: dezelfde tegenmacht-tegen-de-Belastingdienst sloot de consensus in 2013 (Bulgarenfraude) en opende haar in 2017-2019 (RTL/Trouw/FtM). DC is binnen fase 2 de **uitzondering** (`sluit`): de vrijpleit-reconstructie versus de blootleggende onthulling. (Mechanisme-74-aggregatie blijft leeg — machtsvalentie-args dragen bewust geen `mechanism_id`, zelfde conventie als de DC-ronde; edge/actor-niveau zijn wat de viz gebruikt.)

## Discipline-checks

Geen org→org-structuur · geen caveat ingevouwen (nuance rel 171 geattribueerd, niet monocausaal) · fase-1-edges bewust géén machtsvalentie (geen tegenmacht) · Pieter Klein (#473) niet aangeraakt · certainty/influence niet gezet (0,05-vloer) · quotes verbatim uit HUMAN #289 · betwiste causale keten (Q3) expliciet als nuance opgenomen i.p.v. weggelaten.

## Openstaand voor de mens

1. **Rel 171** — herclassificeren uit `onderzoeksjournalist_doorbraak`, of de `sluit`-annotatie laten staan (aanbeveling: laten staan)?
2. **Merge-beslissingen** per item (of "via admin").
3. Eventueel: de fase-1 frame-adoptie (rel 42/86/254/255) verder verrijken met tijdlabels of extra bron — nu niet gedaan (was al gemodelleerd).
