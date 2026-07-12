# Ideoloog-ronde: economische ideologie-positie van economen (politieke kleurmeter)

- **Datum:** 2026-07-09
- **Account:** assistent (bijdrager) — alles landt `voorgesteld`
- **Git-hash bij aanvang:** de441f1
- **Brief:** `missies/ideoloog_brief.md` (richting-signalen `property='politieke_positie'`, bron-gepoort,
  één bron→één as, alleen coderen bij een verbatim as-eigen uiting) + eigenaarsopdracht:
  *"Ga ook op zoek naar de ideologieën van alle personen, vooral op economisch gebied."*
- **Scope (gekozen):** economen-focus. Van de 131 gezagsexpert-personen misten er 130 een economische-as-
  signaal; daaruit gefilterd op **echte economen** (bank-/planbureau-/universitaire/werkgevers-/vakbonds-
  economen + de kritische economen) → **45 doelwitten**. Niet-economen in de gezagsexpert-rol (virologen,
  militairen, juristen) bewust uitgesloten: hun *economische* ideologie is niet citeerbaar.
- **Methode:** multi-agent workflow (`econ-ideologie-kleurmeter`, run `wf_8b34f20e-7df`): 7 onderzoeks-
  batches (neutrale zoekvraag, WebSearch/WebFetch) → **adversariële verificatie per signaal** (verbatim?
  attributie? **as_correct** volgens de scherpe asdefinities? geen Wikipedia?). Daarna een **salvage-ronde**
  (`wf_29409deb-485`) voor 7 twijfel-afgekeurde signalen (quote niet strikt verbatim). Indienen serieel via
  de API onder `assistent` (`property='politieke_positie'`, `property_value='<as>:<pool>'`, verbatim citatie).
  52 agents totaal, 0 errors.

## Oogst — 31 economische-as-signalen (ids #2721–2751)

Alleen de **economische** as gecodeerd (conform "vooral op economisch gebied"); geen cultureel/establishment
uitgesmeerd. Pool-balans **17 links / 14 rechts** — tweezijdig. Elk signaal draagt één verbatim-gecheckte bron.

**economisch RECHTS (14):** Lans Bovenberg (profijtbeginsel/eigen bijdragen), Lex Hoogduin (Oostenrijkse
School, minimale overheid), Mathijs Bouman (begrotingsdiscipline), Arnoud Boot (pro-private-equity),
Klaas Knot (staatsschuld-hek/soberheid), Olaf Sleijpen (DNB), Raymond Gradus, Ivo Arnold, Han de Jong,
Edin Mujagić, Ingrid Thijssen (VNO-NCW, lagere bedrijfslasten/vestigingsklimaat), Jacco Vonhof (MKB),
Raymond Puts + Anne Megens (AWVN — werkgevers).

**economisch LINKS (17):** Sylvester Eijffinger (marktcorrectie), Sweder van Wijnbergen (anti-austerity),
Coen Teulings, Sandra Phlippen (arbeidsmarkt-tweedeling/ongelijkheid), Carsten Brzeski, Ewald Engelen,
Dirk Bezemer, Rens van Tilburg, Harald Benink (bankregulering/hoger eigen vermogen), Dirk Schoenmaker
(markt levert niet wat nodig is), Wimar Bolhuis, Arjan Vliegenthart + Mattias Gijsbertsen (Nibud),
Piet Fortuin + Hans van den Heuvel (CNV), Tuur Elzinga + Zakaria Boufangacha (FNV — vakbonden).

> **Validatie van de as-discipline:** de werkgevers-organisaties (VNO-NCW/MKB/AWVN) komen consequent
> **rechts** uit, de vakbonden (CNV/FNV) consequent **links** — de verwachte arbeids-/kapitaalsplitsing,
> onafhankelijk per persoon gesourcet. Binnen één bank verschillen personen (ABN AMRO: Phlippen links,
> Han de Jong rechts) — het signaal volgt de *uiting*, niet de werkgever.

## Onbepaald gelaten (13) — correcter dan een geleende score

Voor deze economen is géén citeerbare economische *lean* gevonden; hun publieke output is technisch-
analytisch (prognoses, cijferduiding), niet normatief. Conform de brief blijven ze **onbepaald**:
- **Statistiek/prognose (professioneel neutraal):** Peter Hein van Mulligen (CBS), Philip Bokeloh (ABN AMRO),
  Maurice van Sante (ING Research), Otto Raspe + Stefan Groot (RaboResearch), Bas ter Weel + Arjan Heyma (SEO),
  Luc Aben (Van Lanschot), Marieke Blom (ING).
- **Peilers:** Peter Kanne + Sjoerd van Heck (Ipsos I&O) — beschrijvende opinie-analyse, geen eigen lean.
- **Transitie/technocratisch:** Marko Hekkert (PBL), Bas Jacobs (optimale-belastingtheorie — technocratisch,
  geen eenduidige pool binnen deze ronde).

## Afgekeurd door verificatie

- **Eerste ronde:** 7 signalen kregen `twijfel` (quote niet strikt verbatim / as_correct-twijfel) → niet ingediend.
- **Salvage-ronde herstelde er 6** met een strikt-verbatim quote (Boot, Knot, Thijssen, Elzinga, Boufangacha,
  Brzeski). **Belangrijke correctie:** Arnoud Boot ging van *links* → **rechts** — de eerste coder leunde op
  een louter beschrijvende financialisering-diagnose (geen lean); zijn as-eigen uiting is pro-private-equity.
- **Barbara Baarsma** bleef als enige onherstelbaar (geen schone verbatim-quote met eenduidige pool) → **onbepaald**.

## Discipline-naleving (kleurmeter-as-regels)

- Alleen gecodeerd waar een **verbatim, as-eigen** uiting de lean draagt; technische/objectieve uitspraken
  ("inflatie is 4%") niet als lean geteld; bestuurszetels **nooit** als establishment-signaal.
- "Publiek belang boven bedrijfsbelang" / marktcorrectie consequent als **economisch links** geteld (niet cultureel).
- Eén bron → één as (geen dubbeltellen). Geen Wikipedia als bron (doorgelopen naar het onderliggende interview/opiniestuk).
- Tweezijdig geoogst (17 links / 14 rechts). Negatieve resultaten (onbepaald) staan hier, niet als modelknoop.

## Zoekopdrachten (letterlijk)

Per persoon een neutrale "wat is de gedocumenteerde economische positie van X?"-zoektocht + WebFetch van het
onderliggende opiniestuk/interview/programma. Bron-URL's staan in de citaties van de 31 argumenten
(#2721–2751). Volledige query-lijst in het workflow-journaal (`wf_8b34f20e-7df` / `wf_29409deb-485`).

## Status & vervolg

- 31 signalen `voorgesteld` (contributed_by=assistent, elk met citatie), wachten op menselijke review in
  `/overleg` → *Voorstellen* + `/werkbank`. `validate_model.py --strict` groen (voorgesteld telt in niets).
- Na merge leidt `politiek.py` per econoom de economische positie af; organisaties (VNO-NCW/FNV/CNV/AWVN)
  krijgen hun positie deels afgeleid uit deze bestuurders/leden.
- **Openstaand:** 13 onbepaalde economen (technisch-neutrale output) — geen actie tenzij later een normatieve
  uiting opduikt. Baarsma bij een volgende ronde opnieuw proberen met een schone verbatim-quote.
