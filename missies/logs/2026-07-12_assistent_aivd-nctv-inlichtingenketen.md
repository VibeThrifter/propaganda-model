# Missielog — Inlichtingenketen NSA/SSEUR → AIVD/MIVD/NCTV → NL-media

**Datum:** 2026-07-12 · **Account:** `assistent` (bijdrager) voor indienen; **`maxime`** (mens-maintainer) voor de merge op expliciete "via admin".
**Aanleiding eigenaar:** "Kan je ook wat vinden van navo of amerikaanse geheime diensten die invloed hebben op de aivd en nctv EN aivd en nctv weer op onze media — wordt natuurlijk gebruikt als directe bron (institutie)."

## Aanpak
Drie parallelle onderzoekssubagenten (general-purpose), elk met de volledige modelleerdiscipline (primaire bron + verbatim, geen fabricatie, Wikipedia = vindplaats, twee-niveau-neutraliteit, confounds expliciet, richting VS→NL vs NL→VS onderscheiden):
1. **Bovenste hop SIGINT** — NSA/Five Eyes/SSEUR ↔ AIVD/MIVD (Snowden, CTIVD, JSCU, metadata-affaire, Cozy Bear).
2. **Bovenste hop CT** — VS (DHS/State/GCTF) ↔ NCTV + historisch CIA↔BVD.
3. **Onderste hop** — AIVD/NCTV als institutionele "primary definer"-bron voor NL-media + tegenmacht-confound.

Alle 11 uiteindelijk gebruikte quotes zijn door de hoofdsessie **zelf verbatim langs de live-URL gelegd** (WebFetch) vóór indienen. Manifest: `data/scout/aivd-nctv-intel.json` → `scout_indienen.py --indienen` (assistent). certainty/influence nergens gezet.

## Ingediend & gemerged (via admin, maxime) — alles goedgekeurd, 0 mislukt
Baseline vóór: ent≤1153, rel≤2072, arg≤3520, src≤2151.

**Entiteiten (3):** #1154 NSA · #1155 MIVD · #1156 SIGINT Seniors Europe (SSEUR / "14 Eyes").

**Relaties (7):**
- **#2073 NSA → AIVD** (`bron_van`, mech 168 institutionele_gezagsketen) — bovenste hop, bilateraal.
- **#2074 AIVD → SSEUR** · **#2075 MIVD → SSEUR** (`lidmaatschap`, mech 168) — NL SIGINT ingebed in NSA-geleid netwerk.
- **#2076 AIVD → NCTV** (`bron_van`, mech 6 bron_afhankelijkheid) — de brug; sluit de keten NSA→AIVD→NCTV→media.
- **#2077 AIVD → NOS** (`bron_van`, mech 86 institutioneel_gezag) — jaarverslag-duiding wordt nieuwsframe.
- **#2078 MIVD → NOS** (`bron_van`, mech 173 crisis_bronmonopolie) — OPCW/GRU-attributie 2018.
- **#2079 NRC → NCTV** (`oppositie`, mech 78 onafhankelijk_medium_tegenwicht) — tegenmacht (nepaccounts-onthulling).

**Argumenten (12):** #3521–3532. Supporting-roots met verbatim citatie op elke relatie; plus 3 **contextual**-confounds als aparte nodes (#3522 CTIVD/"vier sloten"; #3523 Cozy Bear NL→VS; #3530 internationale corroboratie OPCW) en #3532 versterkt de bestaande NCTV→NOS #427 met het DTN-niveau.

**Bronnen (10, server-dedup):** #2152–2161 — NOS (buitenlandse intel 2017, Cozy Bear 2018, MIVD-OPCW 2018, DTN 2024, NCTV-nepaccounts 2021, AIVD-jaarverslag 2025), The Intercept (SSEUR, Snowden-docs), AIVD ("vier sloten", JSCU-persbericht), NCTV (DTN-methode).

## Modelleerkeuzes (expliciet)
1. **Twee-niveau-neutraliteit**: structureel feit = supporting; tegencontext = aparte `contextual` node (CTIVD-toezicht begrenst de afhankelijkheid; NL is actieve capabele partner, verwevenheid tweezijdig; OPCW-attributie internationaal gecorroboreerd). Model wijst geen winnaar aan.
2. **NCTV-upstream bewust transitief** (NSA→AIVD→NCTV), géén geforceerde directe VS→NCTV-edge — het onderzoek vond de directe NCTV-upstream vooral op BuZa/V&J-niveau en het DTN redelijk eigenstandig; een directe "VS stuurt het DTN"-pijl zou over-asserten.
3. **`institutionele_gezagsketen` (#168)** voor de inter-dienst-koppeling is een keuze: geen perfect bestaand mechanisme voor bondgenootschappelijke SIGINT-afhankelijkheid; #168 (gezagsinstituten koppelen formeel en landen als één blok in de berichtgeving) is de best verdedigbare match. Puriteiner alternatief bewaard als optie: de 3 bovenste-hop-edges als mechanisme-loze **kandidaten** + RfC voor een eigen mechanisme (`bondgenootschappelijke_inlichtingenafhankelijkheid`).

## Status
- `validate_model.py --strict`: **groen** (136 fouten, exact op baseline; golden snapshot byte-identiek). Invloed op de 0,05-vloer, geen orphans.
- Zichtbaar in de viz na een pagina-ververs (graaf via `/api/graph_data`).

## Bewust niet gemodelleerd (leads)
- **CIA ↔ BVD** (Koude Oorlog, project-A telefoontaps CIA-gefinancierd; bron Engelen *De BVD in de twintigste eeuw*) — instituut-/tijdbreuk met de AIVD; hooguit losse historische context.
- **ICCT co-gefinancierd door NAVO/US-DHS/USAID** (ICCT AR 2022 + NATO Guidebook) — de gedeelde knoop met de bestaande NCTV→ICCT #1621; vergt een US-DHS-entiteit. Sterke lead.
- **GCTF** (VS+Turkije oprichters, NL oprichtend lid, admin-unit Den Haag) — BuZa-niveau, niet NCTV.
- **PCSC-databandeling US-DHS → NL V&J** (biometrie, 2010) — moederministerie-laag, niet direct NCTV.
- **"1,8 miljoen metadata"-affaire** (NSO→NSA, 2014) — verwevenheid NL→VS.
- DTN noemt "informatie van buitenlandse partners" als expliciete input (NCTV-methode) — nu gedekt via de transitieve keten.
