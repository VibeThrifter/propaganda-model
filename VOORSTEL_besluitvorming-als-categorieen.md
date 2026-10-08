# Voorstel — besluitvorming als categorieën in hetzelfde netwerk

*Status: **eigenaarsbesluit 2026-10-07**, in uitvoering (plan: dit document + DOCUMENTATIE.md § "Uitbreiding C:
Besluitvorming"). Geen data-sloop: alle bestaande filters, mechanismen en relaties blijven staan.*

## Aanleiding

De eigenaar (2026-10-07): *"Propagandamodel uitbreiden met meer politieke lagen, hoge ambtenaren, ngo's en
bedrijven etc. zodat alle besluitvorming ook in de kaart komt behalve alleen media gerelateerd."* En daarna:
*"Dit moet hetzelfde netwerk zijn als het propagandamodel … alleen dit zijn andere categorieën en categorieën
kunnen ook overlappen … het moet in hetzelfde model want het is in de echte wereld deel van hetzelfde
netwerk."* De theorielaag mag op dezelfde manier groeien: *"precies hetzelfde als propagandamodel alleen echt
een uitbreiding erop met wellicht nieuwe categorieën."*

Tot nu toe stond de staat alleen in het model als **bron, flak of tegenmacht van de media**: 81
overheidsinstellingen, geen enkele secretaris-generaal of directeur-generaal, en de mechanisme-toewijzer wees
bestuursverbanden af als "buiten het model" (onder meer de benoeming van de Kiesraad-voorzitter, het Presidium
van de Tweede Kamer, bestuurders van AWVN en CNV).

## Kernbesluit: één netwerk, extra categorieën

1. **Eén model, één netwerk.** Een minister is tegelijk bron voor de NOS (sourcing) én hoofd van een
   departement (formele macht). Twee aparte modellen zouden precies de verbanden doorknippen die het model wil
   laten zien.
2. **Vijf nieuwe categorieën naast de vijf filters**, in hetzelfde veld (`mechanisms.filter`,
   `mechanism_filters`, `roles.category`): `formele_macht`, `belangen`, `kennis_advies`, `polder`,
   `werving`. Een mechanisme mag in meerdere categorieën vallen (de bestaande many-to-many
   `mechanism_filters`); `draaideurconstructie` krijgt er bijvoorbeeld `werving` bij.
3. **Controle = tegenmacht.** De bestaande categorie `tegenmacht` betekent al "soort 1: verantwoording"
   (`parlementaire_controle` staat er onder). Zij krijgt nu ook de bestuurscategorieën als doel
   (`tegenmacht.FILTER_DOELEN`). Bewuste gevolgen, gedocumenteerd in DOCUMENTATIE.md: een controle-edge telt —
   zoals elke tegenmacht-edge — negatief in de directe invloed en kleurt geen knoop.
4. **Besluiten zelf worden geen knoop** (eigenaar: "alleen wie besluit"). Het model toont wie bevoegd is en
   langs welke kanalen besluiten gevormd worden, niet elk wetsvoorstel of elke motie.
5. **Diepte: Rijk + alle bestuurders.** Ministeries tot op DG-niveau, SG's/DG's/IG's, beide Kamers, zbo's,
   adviescolleges, toezichthouders, inspecties, Hoge Colleges, provincies, waterschappen en alle gemeenten met
   burgemeester en wethouders. Raadsleden alleen wanneer ze in het nieuws komen (via de nieuws-pijplijn).

## Theoretische grond

G. William Domhoff (*Who Rules America?*) onderscheidt vier netwerken waarlangs een machtselite overheidsbeleid
vormt. Het vierde — het **opinion-shaping process** — is het terrein van Herman & Chomsky en dus van de vijf
bestaande filters. De andere drie worden categorieën:

| Domhoff | Categorie |
|---|---|
| special-interest process (lobby, toegang, gunsten) | `belangen` |
| policy-planning process (denktanks, adviesorganen, elite-fora) | `kennis_advies` |
| candidate-selection process (partijen, werving, benoeming) | `werving` |
| opinion-shaping process | de vijf filters (Herman & Chomsky) |

Twee Nederlandse lagen komen erbij, omdat Domhoff ze voor de VS niet nodig had:

- **`formele_macht`** — wie formeel bevoegd is: de ministeriële verantwoordelijkheid, de vaste ambtelijke top
  (de ABD; onderzoek 1.4), verzelfstandiging (zbo's op afstand), decentrale overheden en de doorwerking van
  EU-regels. Meerlagig bestuur wordt een eigen kolom (`entities.bestuurslaag`: eu, rijk, provincie, gemeente,
  waterschap, caribisch, regio).
- **`polder`** — het Nederlandse corporatisme (onderzoek 3.4): SER, Stichting van de Arbeid, overlegtafels en
  akkoorden die de uitkomst vastleggen voordat het parlement spreekt.

Zo krijgen ook de vier theorie-gaten uit onderzoek 3.8 §D een thuis: topambtenarij (`topambtenaar`,
`ambtelijke_leiding`), juridificering (`bestuursrechter`, `beleid_via_rechter`), akkoord-preëmptie
(`akkoord_preemptie`) en consultancy (`consultant`, `inhuur_consultancy`).

## Wat er verandert

- **Schema** (`scripts/migrate_add_besluitvorming.py`): de vijf categorie-waarden; relatietypes `ambt`,
  `zeggenschap`, `controle`, `geschenk`; kolommen `entities.bestuurslaag` en `relations.functie`; tabel
  `externe_ids` (tooi, oo, tk_persoon, wikidata, ep_mep). Entiteittypes blijven gelijk: het type is de
  structuurvorm, de rol de functie.
- **Theorie**: de basisrollen en -mechanismen gaan erin zoals de basis van het propagandamodel erin ging — in
  de opbouwfase via de maintainer-route, gelogd als betwistbaar, elk met een steunend argument mét bron. Wat
  daarna komt, gaat via RfC's die de agents beslissen.
- **Praktijk**: open registers (register van overheidsorganisaties, Tweede Kamer, Wikidata, Europees
  Parlement, lobbyistenregister) via `tools/registers/` en het REST-pad onder account `register-import`. Een
  deterministische `registercheck` (geen LLM) toetst elk registerfeit aan de bewaarde registeruitgave.
- **Agents**: de reikwijdte in hun prompts wordt "het Nederlandse media- en bestuurssysteem, één netwerk";
  `buiten_model` betekent voortaan: buiten media én besluitvorming.

## Wat niet verandert

- De vijf filters, hun mechanismen en hun relaties; de scoringswiskunde; de neutraliteits- en smaadregels.
- Niets wordt automatisch geduid: een registerfeit is een letterlijke registerregel, geen beschuldiging.
- Privépersonen blijven buiten het model; raadsleden komen er niet in bulk in.
