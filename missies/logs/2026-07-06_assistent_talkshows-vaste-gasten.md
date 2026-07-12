# Missielog — Talkshows + vaste opiniemakers/experts

**Datum:** 2026-07-06
**Account:** `assistent` (bijdrager) — alles ingediend als `voorgesteld`
**Opdracht:** Nederlandse opinie-/actualiteitentalkshows als knopen opnemen, mét hun
presentatoren (hosts, als directe edge) en zo breed mogelijk hun vaste
opiniemakers/experts. Huidig + historisch dominant; entertainers buiten scope.

## Aanpak

Bestaand modelpatroon hergebruikt (geen nieuwe theorie/RfC):
- Talkshow = entiteit `type=mediaorganisatie`, rol `redactie` (34).
- Programma → omroep = `mediaplatform`; mech 124 (`omroepsignatuur`) publiek, mech 160
  (`kijkcijferdisciplinering`) commercieel.
- **Host → programma = directe edge** `personeel` + mech 18 (`draaideurconstructie`,
  aard=direct) — conform precedent Eva Jinek → Eva (rel. 1022).
- Vaste gast/expert/duider → programma = `beinvloeding` + mech 87 (`expert_legitimatie`).
- `certainty`/`influence` niet gezet (0,05-vloer; guilty-until-proven). Influence bewust
  níét boven de vloer getild (geen bronnen over invloed-magnitude) → INVLOED-PRIOR-check
  blijft 0.

Alle feiten verbatim geverifieerd via WebFetch op de Nederlandse Wikipedia-pagina's
(betrouwbaarheid voorgesteld `grijs`, onderwerp `nl_systeem`). Quotes letterlijk
gecontroleerd; waar geen nette prozazin bestond (bv. Beau-zender, Vandaag Inside-host)
leunt de citatie op de URL-locator i.p.v. een gefabriceerde quote.

## Ingediend

**Batch A — skelet (manifest `talkshows_r1_skelet.json`):** 10 nieuwe show-entiteiten
(#673–682), 21 nieuwe persoon-entiteiten (hosts), 33 relaties + 33 argumenten, 10 bronnen.

| Show | id | Omroep-edge | Time-box |
|------|----|-----|-----|
| Khalid & Sophie | 673 | BNNVARA | 2021-08-30 – 2024-06-01 |
| Bar Laat | 674 | BNNVARA | 2024-08-26 – 2025-05-22 |
| Goedenavond Nederland | 675 | WNL | 2025-05-26 – … |
| Renze | 676 | RTL | 2022-07-04 – … (herstart 2026) |
| Beau | 677 | RTL | 2019-09-02 – 2025-04-11 |
| RTL Tonight | 678 | RTL | 2025-08-31 – 2026-06-12 |
| HLF8 | 679 | SBS6 | 2021-09-06 – 2023-04-07 |
| De Wereld Draait Door | 680 | VARA/BNNVARA | 2005-10-10 – 2020-03-27 |
| Jinek | 681 | KRO-NCRV + RTL (2 edges) | 2013-09-09 – 2023-06-23 |
| Pauw & Witteman | 682 | VARA/BNNVARA | 2006-09-04 – 2014-05-23 |

Hosts o.a.: Sophie Hilbrand, Khalid Kasem, Jeroen Pauw, Tim de Wit, Welmoed Sijtsma,
Sam Hagens, Renze Klamer, Beau van Erven Dorens, Humberto Tan, Leonie ter Braak,
Johnny de Mol, Hélène Hendriks, Matthijs van Nieuwkerk, Eva Jinek, Paul Witteman.

**Batch B — vaste gasten/experts (manifest `talkshows_r3_gasten.json`):** 31 nieuwe
persoon-entiteiten, 49 relaties + 49 argumenten, 8 bronnen (hergebruikt). Plus de
ontbrekende **host-edge Wilfred Genee → Vandaag Inside** en Derksen/Van der Gijp als
vaste tafelgenoten.

- Goedenavond Nederland: Fidan Ekiz, Jort Kelder, Tom Staal, Mats Akkerman, Tessa van Viegen.
- Renze: Jaïr Ferwerda, Gijs Rademaker, Anna Gimbrère.
- Beau: Jaïr Ferwerda.
- RTL Tonight: Ahmed Aboutaleb, Albert Verlinde, Michiel Vos, Saskia Belleman, Anna Gimbrère.
- DWDD: Maarten van Rossem, Prem Radhakishun, Jort Kelder, Hugo Borst, Özcan Akyol,
  Rosanne Hertzberger, Jan Mulder, Martin Bril, Sylvana Simons, Gerdi Verbeet, Fidan Ekiz,
  + huisdichter Nico Dijkshoorn.
- Jinek: Floor Bremer, Wouter de Winther, Gijs Rademaker, Ernst Kuipers, Marcel Levi,
  Diederik Gommers, Özcan Akyol.
- Pauw & Witteman: Peter R. de Vries, Frits Wester.
- Vandaag Inside (#175): Genee (host), Derksen, Van der Gijp, Valentijn Driessen,
  Job Knoester, Wierd Duk, Pieter Cobelens, Wouter de Winther, Jort Kelder,
  Rutger Castricum, Goedele Liekens, Nico Dijkshoorn, Tina Nijkamp, Renske Leijten.

Verificatie: `validate_model.py --strict` → exit 0 (geen fouten boven baseline,
golden-snapshot groen). 71 `voorgesteld`-relaties naar de talkshows.

## Bewust NIET ingediend (log, geen modelknoop)

**Buiten scope "opiniemakers en experts" — pure entertainers/muzikanten/acteurs** (wel vaste
gast, maar geen duider/expert; als knoop zouden ze de sourcing-lezing vertroebelen):
- DWDD-tafelgasten: Ali B, Akwasi, Candy Dulfer, André van Duin, Paul de Leeuw,
  Theo Maassen, Halina Reijn, Giel Beelen, Tygo Gernandt, Georgina Verbaan, e.a.
  (+ de roterende seizoens-huisbands: Racoon, Moke, Typhoon, Chef'Special, …).
- Beau: Jeffrey Wirtz (comedian-sidekick), Marc-Marie Huijbregts (cabaretier).
- Renze: Vivienne van den Assem (actrice-sidekick).
- HLF8: Dominee Gremdaat (satirisch typetje), Noa Vahle (sport), Dries Roelvink (zanger)
  — geen actualiteiten-duiders; HLF8 leverde daardoor geen expert-edge op.
- Jinek/Pauw & Witteman: Marc-Marie Huijbregts (cabaretier), Bart Chabot (schrijver/performer).

**Onbronbaar op vaste-gast-niveau** (in bron niet als vaste gast/huisexpert bevestigd,
alleen "in meerdere afleveringen te zien"): de HLF8-"meermaals verschenen"-lijst
(Frits Barend, Mona Keijzer, René Mioch, Bastiaan Ragas, Jan Versteegh, e.a.). Niet ingediend.

**Goedenavond Nederland — sidekick-opsomming zonder prozabron:** Marianne van den Anker,
Klaas Dijkhoff, Roxane Knetemann, Rick Nieman, Menen Seijkens stonden in een lijst-sectie,
niet in de geverifieerde prozazin. Alleen de vijf uit de prozazin ingediend.

## Correcties t.o.v. eerste inschatting

- **Khalid & Sophie** en **Bar Laat** zijn *gestopt* (2024 resp. 2025), niet actueel;
  Bar Laat's opvolger *Pauw & De Wit* bestond al (#224). Beide als time-boxed opgenomen.
- **Frank van Leeuwen** (Goedenavond Nederland vanaf 2026) nog niet opgenomen — geen
  aparte losse node zonder edge; volgende ronde met bron.

## Ronde 2 — vaste gasten bestaande shows (manifest `talkshows_r4_bestaande.json`)

17 nieuwe personen, 33 relaties + 33 argumenten, 9 bronnen. Alle dragende quotes zelf
verbatim geverifieerd (Wikipedia + Adformatie + Mediacourant + HCSS/Volkskrant + TVgids).

- **Op1** (#174): Joost Vullings, Xander van der Wulp (Adformatie: 37/31 keer), Thomas van
  Groningen (WNL-duider), Rob de Wijk (veiligheidsexpert), Marcel van Roosmalen (columnist).
- **Jinek** (#681): Joost Vullings (Wikipedia: "geregeld te gast bij Op1 en Jinek").
- **Eva** (#482): Wouter de Winther (vaste gast, 51×), Özcan Akyol (26×), Jort Kelder (24×),
  Laila Frank (22×), Joost Vullings (22×), Marleen de Rooy (20×), Tom van 't Einde (20×)
  — frequenties uit Mediacourant/VARAgids-onderzoek.
- **Buitenhof** (#476): historische columnisten Max Pam, Naema Tahir (t/m 2012), Jos de Beus,
  Désanne van Brederode, Syp Wynia, Ronald Plasterk (t/m 2007), + rubriek 'Schuim en as'
  (2012-2013): Maarten Asscher, Wim Pijbes, Petra Stienen. Time-boxed.
- **De Oranjezomer** (#484): vaste weekgasten Özcan Akyol, Rutger Castricum, Fidan Ekiz,
  Jeroen Pauw; roulerende pool Raymond Mens, Job Knoester, Pieter Cobelens, Victor Vlam,
  Sam Hagens, Merel Ek.
- **Goedenavond Nederland** (#675): host-edge Frank van Leeuwen (vanaf 2026).

Validatie na indienen: `validate_model.py --strict` → exit 0, golden-snapshot groen.

### Bewust NIET in ronde 2

- **Pauw & De Wit** (#224) en **WNL op Zondag** (#480): structureel géén vaste opiniemakers/
  duiders — beide draaien op roterende experts (zelf een gebrond gegeven, geen ontbrekende
  data). De P&DW-verslaggevers (Terpstra/Van Ruijven/Van Dorp) stonden alleen op Wikikids
  (te zwakke bron) → niet ingediend.
- **Nieuwsuur/Mathijs Bouman**: "vaste economische duider" (NOS), maar Bouman heeft al een
  `personeel`-edge naar Nieuwsuur (#472) → niet gedubbeld met een tweede edge.
- **Beatrice de Graaf** (Nieuwsuur, veiligheid): geen bron die haar als *vaste* duider
  bevestigt (alleen losse verschijning) → niet ingediend.
- Buitenhof-columnisten uit Beeld&Geluid-wiki (Zijderveld, Cliteur, Philipse, Livestro):
  niet op nl.wikipedia verbatim bevestigd → overgeslagen, alleen de Wikipedia-9 ingediend.
- De Oranjezomer sport/entertainment (Youri Mulder, Jack van Gelder, Doornbos, Polman,
  Slagter, De Kramer): buiten scope.

## Ronde 3 — extra historisch dominante + satirische opinieshows (manifest `talkshows_r5_extra.json`)

4 nieuwe show-entiteiten + Arjen Lubach, 9 relaties + 9 argumenten, 4 bronnen (Wikipedia,
verbatim geverifieerd). Validatie na indienen: exit 0, golden-snapshot groen.

- **RTL Late Night** (RTL 4, 2013-2019) — hosts Humberto Tan (2013-2018), Twan Huys (2018-2019).
- **Pauw** (BNNVARA/VARA, 2014-2019) — host Jeroen Pauw (de solo-talkshow tussen
  Pauw & Witteman en Pauw & De Wit).
- **De Avondshow met Arjen Lubach** (VPRO, NPO 1, 2022-2024) — host Arjen Lubach.
- **Zondag met Lubach** (VPRO, 2014-2021) — host Arjen Lubach.

De Lubach-shows doen prominente opinie via satire → als knoop opgenomen; hun vaste
*comedy*-bijdragers (Diederik Smit, Tex de Wit, Jonathan van het Reve, Steye van Dam e.a.)
en de RTL Late Night-sidekicks (Luuk Ikink, Marieke Elsinga) zijn **niet** opgenomen —
entertainers/tekstschrijvers, geen duiders/experts (buiten scope). **M** (KRO-NCRV,
Margriet van der Linden) niet toegevoegd: geen bruikbare Wikipedia-pagina gevonden.

## Ronde 4 — completer + MERGE (manifest `talkshows_r6_completer.json`)

Op verzoek eigenaar. 4 nieuwe entiteiten + 6 relaties:
- **De Oranjewinter** (SBS6, Hélène Hendriks) — winter-tegenhanger De Oranjezomer.
- **Even tot hier** (BNNVARA, NPO 1, sinds 2019) — satirisch, duo Van der Laan & Woe
  (hosts Niels van der Laan, Jeroen Woe).
- **Talitha Muusse cancelling (flak):** KRO-NCRV → Talitha Muusse (`censuur`, mech
  `bestuurlijke_redactiedruk` 169). Zij stopte apr 2021 per direct als Op1-presentatrice
  nadat KRO-NCRV haar de eis oplegde niet meer over politiek aan tafel te praten — botste
  met haar activistische opiniemaker-profiel. Gebrond (Mediacourant, verbatim). Illustreert
  de flak-/redactiedruk-filter op een opiniemaker binnen een talkshow.

**MERGE (via admin, maxime-token).** Op expliciete opdracht van de eigenaar de volledige
talkshow-bijdrage goedgekeurd: **78 entiteiten → goedgekeurd, 130 relaties → goedgekeurd,
130 argumenten → merged**. Scope strikt afgebakend via `edit_log` (assistent, vandaag);
3 niet-gerelateerde pre-existing voorgesteld-relaties (#526, #704, #705) bewust
uitgesloten. Parallelle niet-talkshow assistent-relaties van vandaag (2× `censuur`
Op1→Ira Helsloot / NPO→Ongehoord Nederland, 2× `dienstverband`) waren niet van deze
opdracht en zijn niet door deze merge geraakt (apart door de eigenaar afgehandeld).
`validate_model --strict` na de merge: exit 0, golden-snapshot groen.

## Openstaand / vervolg

- Bestaande shows (Op1, Nieuwsuur, Buitenhof, Eva, Pauw & De Wit, WNL op Zondag,
  De Oranjezomer) niet verder aangevuld met extra gasten deze ronde — kan later.
- Alles staat `voorgesteld`; een menselijke reviewer beslist over merge (evt. "via admin").
- Overweeg per host/kern-expert een `property='influence'`-argument als er een bron is die
  de sturende invloed onderbouwt (nu bewust op de vloer gelaten).
