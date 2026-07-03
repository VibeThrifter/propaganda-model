# 2026-07-02 — Uitsluitingscases: Van Rossem gecorrigeerd, Oltmans toegevoegd

**Aanleiding.** Vraag eigenaar: klopt de Van Rossem-casus (NOS weerde hem na kritiek) in het
model, en zijn er meer van zulke gevallen?

## Bevindingen webonderzoek (verbatim geverifieerd tegen ruwe HTML)

- **Van Rossem**: rel. 47 (NOS→Van Rossem, deplatforming, 2003–2010, "jarenlang na kritische
  Irak-analyse") is **vervormd**. Werkelijk: vijf gedocumenteerde cancel-episodes (NPO Radio 1,
  05-10-2023): 1989 (inauguratie-commentaar), 2001 (9/11-relativering bij **NOVA**; chef
  actualiteiten NOS Lars Andersson had het "nu wel even gehad", Van Rossem: **"drie maanden
  niet uitgenodigd"** — Maartenonline), 2003 (Irak-standpunt bij **TweeVandaag**, niet NOS),
  2021 (corona-vaccinatie), 2022 (Op1/Oekraïne). Episodisch patroon: echt; doorlopende
  NOS-ban 2003–2010: nergens gedocumenteerd; trigger was 9/11-relativering, niet Irak.
- **Rel. 66** (NOS→Van Rossem, etikettering): het dragende argument 66 ("wappie",
  "complotdenker") is een **anachronisme** — coronavocabulaire op een 2003–2010-relatie,
  bronloos, en Van Rossem is nooit zo geëtiketteerd.
- **Willem Oltmans**: hét gedocumenteerde Nederlandse staats-flak-geval — ruim veertig jaar
  (vanaf 1956/57) tegengewerkt door Buitenlandse Zaken; bemiddelingscommissie kende in 2000
  **8 miljoen gulden** schadevergoeding toe, door de Staat aanvaard (Villamedia). Ontbrak
  volledig in het model.

## Ingediend (bijdragerspad, `assistent`, alles `voorgesteld`)

Bronnen: **302** (NPO Radio 1, vijf-keer-gecanceld, url), **303** (Maartenonline-profiel, url),
**304** (Villamedia Oltmans-schadevergoeding, url).

| id | wat | doel |
|---|---|---|
| arg. 910 | **contradicting root** — weerlegging tijdvenster/trigger/afzender van rel. 47 | rel. 47 |
| arg. 911 | **supporting root** — de kern (episodische toegang-als-disciplinering) mét bron | rel. 47 |
| arg. 912 | **ondergraving** (reply) op het anachronistische arg. 66 | arg. 66 |
| ent. 335 | **Willem Oltmans** (persoon, rol journalist, 1925–2004) | — |
| rel. 675 | **Min. van Buitenlandse Zaken → Oltmans** (flak, 1957–2000, bewezen einde: schikking) | **kandidaat** (mechanisme-loos) |
| arg. 913 | supporting root: erkenning + compensatie door de Staat zelf | rel. 675 |

Rel. 675 is bewust een **kandidaat**: geen bestaand flak-mechanisme dekt
gezagsinstituut→journalist-tegenwerking (`statelijke_bronnenjacht` = bronnen achterhalen,
`deplatforming` = redactie sluit uit, `publieke_aanval` = politicus valt openlijk aan; dit was
heimelijke, decennialange broodroof). Verzamelt het rol-paar meer kandidaten (bv. latere
gevallen van staats-tegenwerking), dan is een RfC `statelijke_tegenwerking` de route.

## Admin-ronde (zelfde dag, expliciete delegatie eigenaar: "je kan als admin beslissen, dat mag van mij nu")

Uitgevoerd met het `maxime`-token:

- **Merges**: arg. 910, 911, 912, 913 (gesourcete correctie/onderbouwing → `ongecontroleerd`).
- **Entiteit 335 (Oltmans)**: goedgekeurd.
- **Rel. 47 herdateerd**: 2003–2010 → **2001–open**, omschrijving nu episodisch (9/11-trigger,
  "drie maanden", geen doorlopende ban, geen "Irak-analyse").
- **RfC #17** ingediend (bijdragerspad, `assistent`): mechanisme **`statelijke_tegenwerking`**
  (flak, direct, gezagsinstituut→journalist) — heimelijke staats-flak op de bestaansbasis van
  een journalist; adopteert kandidaat-rel. 675; bronnen: Villamedia (304) + Herman & Chomsky
  (2). Wacht op 2 akkoorden (maintainer-akkoord = quorum in opbouwfase; besluit blijft mens).
- **Validator-opschoning** (strict stond boven baseline door ouder werk, niet door deze ronde):
  instantiations-rijen aangevuld voor rel. 664/665/667/671 (CIDI/SVDJ, KOPPEL-REL-INST),
  rol gezet op ent. 195 Het Financieele Dagblad (KOPPEL-ENT-ROL), en de PAX-org→org-relaties
  **471/473/474 verwijderd** (in juni al "horen weg" verklaard — foute conclusies, zie
  CLAUDE.md-voorbeeld). Viz geregenereerd.

**Resterend boven baseline (eigenaarskeuze, bewust niet aangeraakt):**
1. `KOPPEL-REL-MECH` +2: rel. **494** (Pinchuk —bestuurder→ Yalta European Strategy) en
   **495** (Shell —lidmaatschap→ Energie-Nederland) zijn goedgekeurd zónder mechanisme
   (van vóór de orphan-poort). Voor de hand liggend: 494 → `belang_elite_netwerk` (103),
   495 → `belangenbehartiging` (83). `mechanism_id` is niet PATCH-baar via de API — vergt
   een klein structuurscript of een bewuste baseline-verhoging.
2. `BEWIJS-CITATIE` +1: arg. **912** is een bronloze **ondergraving** — beleidsconform
   (M1.1: ondergravingen mogen bronloos), maar de validator-check telt álle voor/tegen-args
   zonder citatie. Opties: check verfijnen (replies uitzonderen) of baseline +1.

**Status:** Van Rossem-set en Oltmans-basis zijn door review; rel. 675 incubeert als kandidaat
tot RfC #17 beslist is; RfC #16 (crisis_bronmonopolie) en de Irak-inzendingen van 1 juli
wachten nog op review.

**Naschrift (2026-07-02, opgelost op aanwijzing eigenaar):** beide restpunten zijn dezelfde dag
verholpen. (1) `mechanism_id` is nu maintainer-patchbaar via `PATCH /api/relations/<id>`
(admin-CLI: `scripts/admin.py edit-rel <id> --mechanisme <mid>`; instantiatie-koppeling beweegt
mee, losmaken kan niet op een goedgekeurde relatie) — rel. 494 → `belang_elite_netwerk` (103) en
rel. 495 → `belangenbehartiging` (83) via admin toegewezen (`edit_log`: maxime). (2) De
`BEWIJS-CITATIE`-check telt alleen nog **roots** (replies/ondergravingen zijn beleidsconform
bronloos) — arg. 912 telt niet meer mee. Strict is weer groen op de bestaande baseline (306/6).
