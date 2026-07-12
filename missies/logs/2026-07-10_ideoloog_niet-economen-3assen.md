# Ideoloog-ronde: ideologie niet-economen (opiniemakers/eigenaren/experts/politici, 3 assen)

- **Datum:** 2026-07-10
- **Account:** assistent (bijdrager) — alles landt `voorgesteld`
- **Git-hash bij aanvang:** de441f1
- **Brief:** `missies/ideoloog_brief.md` (richting-signalen `property='politieke_positie'`, bron-gepoort,
  één bron→één as, alleen coderen bij een verbatim as-eigen uiting, structureel≠establishment,
  rechts-populisme-valkuil) + eigenaarsopdracht: ideologie van de niet-economen coderen (vervolg op de
  economen-ronde van 2026-07-09).
- **Scope (gekozen):** de ideologisch-rijkste niet-economen zónder enig signaal: **169 doelwitten** —
  gezagsexperts (niet-economen, 83), politici (32), media-eigenaren (29, incl. holdings/families), en
  columnist/opiniemakers (25). Journalisten & hoofdredacteuren (~116, vaak professioneel-neutraal)
  bewust buiten deze tranche gehouden.
- **Methode:** multi-agent workflow (`ideologie-niet-economen`, run `wf_ca7cf2a8-f18`): 25 onderzoeks-
  batches (alle 3 assen, neutrale zoekvraag) → **adversariële verificatie per signaal** (verbatim?
  attributie? **as_correct** volgens de scherpe asdefinities incl. structureel≠establishment en de
  rechts-populisme-valkuil? geen Wikipedia?). Daarna een **salvage-ronde** (`wf_8159eb95-112`) voor de
  14 twijfel/klopt-niet-afgekeurde signalen. 141 agents totaal, 0 errors.

## Oogst — 87 signalen over 80 entiteiten (ids #2820–2911)

Van 169 doelwitten kregen **80 een signaal**; **89 bleven onbepaald** (geen citeerbare uiting — correcter
dan een geleende score). Elk signaal draagt één verbatim-gecheckte bron. Verdeling over de assen:

| as | pool-verdeling |
|---|---|
| **establishment** (31) | **22 establishment / 9 anti-establishment** |
| **cultureel** (29) | 15 conservatief / 14 progressief |
| **economisch** (27) | 16 links / 11 rechts |

### Kernbevinding — de establishment-scheefte (22 : 9)

De establishment-as leunt sterk naar **establishment**, en dat is bijna volledig de **defensie-/NAVO-
expertcluster**: Rob Bauer, Jaap de Hoop Scheffer, Peter van Uhm, Pieter Cobelens, Peter Wijninga,
Frank van Kappen, Arend Jan Boekestijn, Han ten Broeke, Patrick Cammaert, Frans Osinga, Martijn Kitzen,
Rem Korteweg, Timo Koster, Patrick Bolder, Rob Bertholee — pro-NAVO/Atlantisch, systeem-affirmerend. De
**anti-establishment**-kant is spiegelbeeldig de covid-kritische/dissidente cluster: Ira Helsloot, Jaap
Hanekamp, Ronald Meester, Meent van der Sluis, Pepijn van Houwelingen, Jolle Demmers, Evelien Peeters,
Peter Knoope. Dit reproduceert de model-thesis: de gevestigde expert-toevoer is overwegend systeem-affirmerend,
met de tegenmacht als kleinere, marginale cluster.

### Culturele as (15 conservatief / 14 progressief)
- **conservatief:** Baudet, Van Meijeren, Wynia, Derksen, Ruud Koopmans, Fidan Ekiz, Laurens Buijs,
  Plasterk, Harbers, Aboutaleb, Mart de Kruif, Erdee Media Groep (reformatorisch), Romme(*), Cuperus.
- **progressief:** Hirsi Ali (secularisme/emancipatie), Geert Mak, Akwasi, Goedele Liekens, Jelle van Buuren,
  Petra Stienen, Naema Tahir, Paul van Meenen (D66), Wieke Paulusma (D66), Sylvana Simons, Rémy Limpach, NCDO.

### Economische as (16 links / 11 rechts)
- **links:** Prem Radhakishun, Hugo Borst (ouderenzorg), Sylvana Simons, Ad Verbrugge, René Cuperus,
  Hugo de Jonge ("minder markt in de zorg"), Marcel Levi, Diederik Gommers, Marc Chavannes, Attje Kuiken.
- **rechts:** Gerrit Zalm, Halbe Zijlstra, Maxime Verhagen, Jort Kelder, Syp Wynia, John de Mol,
  Thomas Leysen, Wybren van Haga, Helma Lodders, Stientje van Veldhoven, Ab Klink.

## Afgekeurd / salvage

- Eerste ronde: **14 afgekeurd** (quote niet strikt verbatim, of toegeschreven aan interviewer/biograaf —
  bv. de TMG-quote bleek van mediahistoricus Wijfjes; de Romme-quote uit een biografie *over* hem).
- **Salvage herstelde 4** met een strikt-verbatim quote, waarvan **2 as-correcties**: Ad Verbrugge en
  Hugo de Jonge — eerst geprobeerd als *cultureel:conservatief*, maar hun schone verbatim-uiting is een
  markt-kritiek → **economisch:links** (publiek belang boven marktlogica). Ook Cuperus (economisch:links)
  en Van Buuren (cultureel:progressief) hersteld.
- **Niet hersteld → blijven onbepaald:** Wilders, Pim Fortuyn, Cliteur, Sheila Sitalsing, Beatrice de Graaf,
  TMG, Madeleine Klinkhamer, Menno Snel, C.P.M. Romme. (Voor Wilders/Fortuyn/Cliteur is de cultureel-
  conservatieve lean evident, maar er kwam binnen deze ronde geen schone verbatim self-quote uit — bewust
  níét geforceerd. Follow-up bij een volgende ronde.)

## Discipline-naleving

- Alleen gecodeerd bij een **verbatim, as-eigen** uiting; technische/objectieve uitspraken niet als lean geteld
  (Menno Snel afgewezen: zijn "marktvertrouwen"-zin was een premisse die hij zelf ondergroef).
- **Structureel ≠ establishment:** een bestuurszetel/rang telde nooit als establishment-signaal; alleen een
  citeerbare *houding* (pro-NAVO/systeem-affirmatie uit een uiting).
- Rechts-populisme-valkuil bewaakt: anti-(cultureel-linkse)-elite-toon op de **culturele** as, niet als anti-establishment.
- Holdings/families zonder ideologisch standpunt → onbepaald (veel media-eigenaar-entiteiten).
- Tweezijdig geoogst; Wikipedia alleen als vindplaats (doorgelopen naar de primaire bron).

## Status & vervolg

- **87 signalen `voorgesteld`** (contributed_by=assistent, elk met citatie), ids #2820–2911, wachten op
  menselijke review in `/overleg` → *Voorstellen* + `/werkbank`. `validate_model.py --strict` groen.
- **Openstaand:** 89 onbepaalde doelwitten (geen citeerbare uiting); de 9 niet-herstelde afgekeurden
  (Wilders/Fortuyn/Cliteur e.a.) verdienen een gerichte follow-up met een schone verbatim-quote. De
  journalisten/hoofdredacteuren-tranche (~116) is nog niet aangeraakt.
