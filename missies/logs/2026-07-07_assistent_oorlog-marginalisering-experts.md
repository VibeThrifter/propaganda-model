# Missielog — marginalisering van anti-NAVO/anti-oorlog-experts (praktijkmodel)

**Datum:** 2026-07-07 · **Account:** `assistent` (bijdrager) · **Alles landt `voorgesteld`.**
**Opdracht (eigenaar):** *"expliciet onderzoek naar het niet serieus nemen, cancellation, of het niet uitnodigen van experts die tegen het dominante NAVO- en oorlogsnarratief ingaan"* — vlaggenschip **Ad Verbrugge** (onderbroken op *Nieuws van de Dag*), "maar ook vele andere voorbeelden voor de praktijk". Oekraïne/Rusland primair.
**Randvoorwaarden:** bronlat = **"ook fringe als vindplaats"** (optie B): fringe mag als vindplaats, mits doorlopen naar een **verifieerbaar primair fragment/transcript** én elk confound-geval een **verplichte `contradicting` root**. Indienen onder `assistent`; **mergen = mensenwerk** (alleen op expliciet "via admin").

Vervolg op [[2026-07-07_assistent_oorlog-navo-selectie-cancelling]]. Kernbevinding daar bevestigd: de **cancelling/marginaliserings-kant is confound-zwaar**; de schone oogst zit in **betrouwbare mediakritiek** (De Groene, Joop/BNNVARA), niet in fringe-incidenten.

## Kernspanning (leidend)

"Expert X werd onderbroken/niet uitgenodigd" is een **echte** marginalisering (het gebeurde), maar de onderbreking kan **terechte feitelijke tegenspraak** zijn i.p.v. onderdrukking van een geldige stem. Het model legt béíde vast: de edge/arg + een verplichte **confound-`contradicting` root**. Zo lift de `onweersproken`-vlag eerlijk en manufacturet het model géén vals slachtofferschap.

## Ingediend (2 batches) — 5 bronnen · 1 entiteit · 2 relaties · 6 argumenten

### Batch 1 — Verbrugge-vlaggenschip + De Groene-mechanisme-argumenten
- **bron #1124** DNW #2157 (transcript-fragment van *Nieuws van de Dag*, SBS6, 18 dec 2025; hergepubliceerd op YouTube 21 dec 2025) — `nl_systeem`, `grijs`. *Verbatim uit auto-ondertiteling geverifieerd via `youtube_transcript_api` (vid gAbfjo8Le84).*
- **bron #1125** Nieuw Wij, Theo de Wit, "Met 'De Nieuwe Wereld' naar de oude machtspolitiek" (27 jan 2026) — `nl_systeem`, `opinie` (confound-bron).
- **bron #1126** De Groene Amsterdammer, Lidija Zelović, "Of het nu Oekraïne is of de Balkan…" (6 apr 2022, slug *gekluisterd-aan-het-vijandbeeld*) — `nl_systeem`, `opinie`.
- **entiteit #799** *Nieuws van de Dag (SBS6)* — mediaorganisatie, rol 34 (redactie), active_from 2025. Spiegelt de programmaknoop-conventie (HLF8 #679, De Oranjewinter #747).
- **relatie #1468** Nieuws van de Dag → SBS6 (#525), `mediaplatform`, mech **160** — structureel (spiegelt rel. 1278/1386).
- **relatie #1469** Nieuws van de Dag → Ad Verbrugge (#411), `censuur`, mech **17 (schijndebat)**, active_from 2025.
  - **arg #2115 (supporting)** — Verbrugge gaf op *Nieuws van de Dag* (18 dec 2025) de burgeroorlog-/2014-context; werd meteen onderbroken (host Sander Janson) en door de tafel overruled zodat hij zijn punt niet kon afmaken. Quote (verbatim, met ellips voor de onderbreking): *"Er is een burgeroorlog gaande. […] Dat is toch niet goed te praten om een ander land binnen te vallen."*
  - **arg #2116 (contradicting = CONFOUND)** — de onderbreking is deels terechte feitelijke tegenspraak: Verbrugge's 'burgeroorlog'-frame bagatelliseert de Russische inval (feb 2022) en zijn eigen eenzijdigheid wordt door mainstream-critici als erger beoordeeld. Quote: *"De eenzijdigheid die Verbrugge de klassieke media verwijt, is op z'n eigen DNW-kanaal vele malen erger."* (Nieuw Wij)
- **arg #2117 (supporting) → mechanisme 193 (vijandbeeld)** — Joegoslavië: Servisch én Kroatisch journaal toonden dezelfde vermoorde dorpelingen, elk als 'eigen' slachtoffers (asymmetrische slachtofferweging). Quote uit De Groene/Zelović.
- **arg #2118 (supporting) → mechanisme 35 (spectrum_bewaking)** — wie de bredere context / eigen verantwoordelijkheid noemt, wordt "in het FvD-hoekje geduwd". Quote uit De Groene/Zelović.

### Batch 2 — vredesbeweging gemarginaliseerd (crisis-bronmonopolie), betrouwbare bron
- **bron #1127** Joop/BNNVARA, Giep Hagoort, "De armetierige eenzijdigheid van de publieke talkshows" (15 apr 2022) — `nl_systeem`, `opinie`.
- **bron #1128** Joop/BNNVARA, Nico Kussendrager, "Vredesbeweging nog amper gehoord…" (13 dec 2024) — `nl_systeem`, `opinie`.
- **arg #2119 (supporting) → mechanisme 173 (crisis_bronmonopolie)** — oud-militairen/veiligheidsanalisten domineren de talkshowtafel; vredesbeweging/wetenschappers/diplomaten structureel afwezig. Quote: *"Oud-commandanten der Nederlandse strijdkrachten, analisten van het Geopolitiek Adviescomplex en getrainde Kremlinologen nemen prominente posities in"* (Hagoort).
- **arg #2120 (supporting) → mechanisme 173** — redactionele sturing expliciet: een opinieredacteur gaf als reden om vredesstemmen niet te platformen: *"wij vinden dat Oekraïne moet winnen"* (Kussendrager).

**Dekking:** alle vier H&C-marginaliseringsmechanismen nu met een betrouwbaar-gesourcet argument — schijndebat (17), spectrum_bewaking (35), vijandbeeld (193), crisis_bronmonopolie (173) — plus één concrete vlaggenschip-edge (Verbrugge) + programmaknoop.

**Validatie:** `validate_model.py --strict` EXIT 0 na beide batches (187 fouten baseline, golden snapshot groen, geen fouten boven baseline).

## Bewust wéggelaten (met reden)

- **Karel van Wolferen** — géén schoon, specifiek gedocumenteerd uitsluitings-/onderbrekingsincident; zwaar confound (oprichter complotkrant *Gezond Verstand* 2020, UvA distantieerde zich). Zijn De Groene-essay "Het Atlantische geloof" (2014) is bovendien *van zijn eigen hand* → geen onafhankelijke mediakritiek. Niet ingediend.
- **Kees van der Pijl** — buiten scope (UK, Sussex, geen Nederlandse media) + antisemitisme/9-11-confound; het is geen Oekraïne-marginaliseringsincident maar een emeritaat-opzegging na een antisemitische tweet. Niet ingediend.
- **Baudet/FvD** — pro-Rusland-peer-confound, buiten scope (lijn uit ronde 4 gehandhaafd).
- **Fringe-outlets zelf** (ninefornews, frontnieuws) — alleen als *vindplaats* toegestaan; geen enkel concreet incident bleef er verbatim + schoon van over dat niet al via een betrouwbare bron liep. Niets als bron ingediend.

## Modelbeslissingen (voor hergebruik)

- Talkshow die een token-dissenter binnenhaalt en overrulet = **schijndebat (17)**-edge programmaknoop → persoon, relation_type `censuur` (marginalisering-door-overrulen; conventie, spiegelt rel. 65). Confound = verplichte `contradicting` root op dezelfde relatie.
- Diffuse uitsluiting zonder één benoembare poortwachter (vredesbeweging niet uitgenodigd) → **mechanisme-argument** op crisis_bronmonopolie (173), géén verzonnen specifieke edge.
- Auto-ondertiteling is een bruikbaar-maar-imperfect transcript → citeer alleen de **schone, ondubbelzinnige** zinnen verbatim; garbled fragmenten paraphraseren in de claim, nooit als quote.

## Merge (via admin, `maxime`) — 2026-07-07

Op expliciete aanwijzing "via admin" gemerged: entiteit #799, rel. #1468 + #1469 → `goedgekeurd`; arg. #2115, #2116, #2117, #2118, #2119, #2120, #2125 → `ongecontroleerd` (gemerged, tellen mee; bronclassificatie nog reviewer-te-bevestigen). `validate --strict` EXIT 0 — foutental daalde 187 → **183** (de confound-`contradicting` root #2116 lichtte een `onweersproken`-vlag; de gesourcete edges ruimden orphan-vlaggen op).

**Correctie bij merge (attributie-discipline):** de relatie #1468 (mediaplatform→SBS6) faalde eerst de bron-poort → een **KIJK/SBS6-programmapagina** als bron toegevoegd (bron #1133, locator) + arg #2125. Verder bleek de **presentator-naam niet te verifiëren**: het web geeft Thomas van Groningen als vaste host (sinds aug 2025), niet "Sander". De naam **"Sander Janson" is daarom uit de omschrijvingen van entiteit #799 en relatie #1469 verwijderd** — de onderbreking/overrulen blijkt hoe dan ook uit het transcript, ongeacht wie de tafel leidde. Nooit een onbevestigde attributie laten staan.

## Ronde 2 — brede sweep (opdracht "zoek nog 50") — 2026-07-07

Vier parallelle onderzoekssporen (subagenten) + eigen verbatim-verificatie van elke dragende quote. **Kernbevinding van de sweep (bevestigd door alle vier sporen):** het zuivere "token-dissenter op mainstream-tv overreden"-moment is in verifieerbare vorm **zeldzaam**, omdat de meeste NAVO-critici naar **eigen kanalen** migreerden (De Nieuwe Wereld, Blckbx, Café Weltschmerz) — dát is het filter-effect zelf: **selectie vóór de uitzending**, niet onderbreking tíjdens. Verbrugge is juist bijzonder omdat hij wél binnen was. Baudet/Van Wolferen/Van der Pijl vielen af op zware confound (Rusland-banden / complot / antisemitisme). Delpher/courant.nu blokkeren automatisch ophalen → historische krantencitaten (jaren-'80 "vijfde colonne") niet hard te maken.

**Ingediend (`voorgesteld`) — 6 bronnen · 1 entiteit · 1 edge · 7 argumenten:**
- **Concrete flak-casus Jolle Demmers** (hoogleraar Conflictstudies UU, LAAG confound): entiteit **#800**; edge **#1470** EW (#491) → Demmers (`etikettering`, mech **13**). Arg **#2141** (supporting) — EW/EWPodium-kop *"Hoe een Utrechtse hoogleraar het Kremlin napapegaait"*; arg **#2142** (contradicting/balans) — De Groene/Van der Hoeven: haar onderhandelingsvoorstellen worden óók inhoudelijk betwist (*"performances om de eigen morele positie te beschermen"*), dus niet louter flak. Bronnen #1147 (EW), #1148 (De Groene "Vredeskamp").
- **Mechanisme-argumenten (betrouwbare bronnen), verbatim geverifieerd:**
  - **#2143 → vijandbeeld #193** — De Groene/Frank van Vree "Onzichtbare oorlog" (bron #1149): asymmetrische beeldweging Afghanistan/Irak (*"…zachtgekleurde voorstelling die de geallieerden sinds 2003…"*).
  - **#2144 → schijndebat #17** — NVJ/Step Vaessen, EFJ-congres (bron #1150): twijfelaars *"afgeschilderd als pro-Rusland"*.
  - **#2145 → spectrum_bewaking #35** — De Groene/Karabulut "Escalatiespiraal" (bron #1151): *"weggezet als zwak of naïef"* / appeasement-label.
  - **#2146 → spectrum_bewaking #35** — Pointer/EUR-contentanalyse (bestaande bron #832, geen dubbel): diplomatie krijgt *"minder ruimte"*.
  - **#2158 → spectrum_bewaking #35** — De Groene/Overbeek "Zo simpel werkt de wereld niet" (bron #1160): *"diplomatie gelijkgesteld wordt aan capitulatie"*.

**Overlap vermeden:** Casus Irak (#301), Pointer (#832), FTM-defensie-experts (#1072) bestonden al → niet gedupliceerd (Casus Irak/FTM overgeslagen, Pointer hergebruikt). **Validatie:** `validate --strict` EXIT 0 (183 baseline, golden groen).

**Eerlijke telling.** Ronde 2 = **15 elementen** (niet 50). Samen met ronde 1 (16) ≈ **31 elementen** voor dit marginaliserings-thema. 50 *schone, concrete* gevallen is in dit hoekje niet haalbaar zonder padding (confound-zwaar; critici op eigen kanalen; archief gesloten). Het schoonste pad naar méér is **door-de-eigenaar-aangewezen clips** (zoals Verbrugge) + handmatig Delpher-archiefwerk.

## Casus Kees van der Pijl — neutrale flak-registratie + CLAUDE.md-nuance (2026-07-07)

Op verzoek van de eigenaar de flak op Van der Pijl vastgelegd. Aanleiding was een discussie over neutraliteit die tot een **nuance in CLAUDE.md § "What this is"** leidde: het "geen complottheorie"-principe geldt voor wat het model **in eigen stem beweert**, niet voor de meningen van de gedocumenteerde actoren. Twee niveaus: (1) object-niveau — wat iemand gelooft (9/11, MH17) → het model/de bijdrager velt **géén** waar/onwaar-oordeel; neutraal genoteerd als díéns opvatting; (2) structureel — dát iemand **flak krijgt voor een afwijkende mening** is bewijsbaar en hoort in het model, ongeacht of die mening waar is. Modelleren op niveau (2): mening neutraal + gesourcete flak + gesourcete tegen-context (confound = de andere gedocumenteerde kant, geattribueerd), scoring + mensen wegen. Géén waardeoordeel van de bijdrager, géén beroep op consensus/autoriteit (ook niet Chomsky) als "beslissend".

**Ingediend (`voorgesteld`, neutrale vorm — géén antisemitisme-stempel, géén drogreden-stempel van het model):**
- **entiteit #805** Kees van der Pijl (publieke_stem; standpunten neutraal beschreven als de zijne) · **#806** De Vrijdagavond · **#807** Andreas Umland.
- **edge #1476** De Vrijdagavond → Van der Pijl (`etikettering`, mech 13): *supporting #2180* — de labeling als "complotdenker" (verbatim De Vrijdagavond); *contradicting #2181* — het label rust volgens de aanklagers op zijn specifieke 9/11-claim (verbatim), wat de lezing "louter pretext" betwist.
- **edge #1477** Andreas Umland → Van der Pijl (`intimidatie`, mech 10): *supporting #2182* — druk-campagne op de uitgever van zijn MH17-boek + geen NL-uitgever (Sargasso, locator); *contradicting #2183* — peer-reviewer Taras Kuzio (Oekraïens politicoloog, Europe-Asia Studies 2019) beoordeelt de these als leunend op Russische desinformatie (locator).
- **contextual #2184** op #805 — zijn eigen 9/11-standpunt verbatim, neutraal als díéns opvatting.
- Bronnen #1178 (De Vrijdagavond), #1179 (Sargasso), #1180 (Kuzio), #1181 (zijn tweet). `validate --strict` EXIT 0 (183 baseline).

**Modelbeslissing (belangrijk):** een betwiste/omstreden dissident mag de graaf in mits **beide gedocumenteerde kanten** erin staan en het model geen winnaar aanwijst. `relation_type` voor juridische dreiging = **`intimidatie`** (mech 10 juridische_dreiging); "juridische_dreiging" is een mechanisme-naam, geen relation_type.

## Open/optioneel (aan de eigenaar)

- Vlaggenschip-edge is **confound-zwaar** (de onderbreking was deels feitelijk juist) — bewust zo gemodelleerd (edge + confound-root). Merge is mensenwerk.
- Meer concrete voorbeelden vergen door-de-eigenaar-aangewezen clips (zoals de Verbrugge-clip) — dat is in dit fringe-gedomineerde hoekje het schoonste pad. Optioneel vervolg: *De Nieuwe Vredesbeweging* als entiteit + edge zodra een benoemde poortwachter gedocumenteerd is.
