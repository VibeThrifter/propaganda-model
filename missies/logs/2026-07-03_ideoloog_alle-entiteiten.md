# Missielog — ideoloog-ronde: alle entiteiten langs de politieke kleurmeter

**Datum:** 2026-07-03  
**Agent:** ideoloog (account `assistent`, bijdrager)  
**Uitvoering:** Claude Code met 18 parallelle onderzoeks-subagenten + 5 verificatie-subagenten

## Opdracht
Alle entiteiten in het model langs de methode van de politieke kleurmeter (`missies/ideoloog_brief.md`): per entiteit de gedocumenteerde ideologische positie op de drie assen (economisch links↔rechts, cultureel progressief↔conservatief, establishment anti↔pro) onderbouwen met **gesourcete richting-signalen** — of eerlijk **onbepaald** laten. Alleen entiteiten zonder signaal op een as zijn onderzocht; de partijen met CHES-metingen en al gedekte assen zijn overgeslagen.

## Werkwijze (drietraps, overfit-bestendig)
1. **Onderzoek** — 18 subagenten met een neutrale missievraag ('wat is de gedocumenteerde positie van X?'), verbatim-citaat verplicht, één bron → max één signaal per as, tweezijdig oogsten, structureel-≠-ideologisch, twijfel → onbepaald.
2. **Verificatie** — 5 subagenten hebben elk kandidaat-citaat **letterlijk** tegen de bronpagina gecontroleerd (curl → WebFetch → Wayback), inclusief attributiecheck tegen quote-mining.
3. **Modelleerdiscipline vooraf** — 9 kandidaat-signalen zijn vóór verificatie al geschrapt omdat ze de harde regel *structureel ≠ ideologisch* of *retoriek ≠ substantie* schonden (zie hieronder).

## Resultaat
- **Entiteiten met ≥1 signaal:** 134
- **Signalen ingediend (alle `voorgesteld`):** 182
- **Entiteiten onbepaald gelaten:** 166

### Poolbalans van de ingediende signalen
- economisch:links: 44
- economisch:rechts: 21
- cultureel:progressief: 41
- cultureel:conservatief: 18
- establishment:anti-establishment: 35
- establishment:establishment: 23

De balans is per as tweezijdig bezet; het lichte overwicht links/progressief/anti-establishment volgt uit welke entiteiten überhaupt een citeerbare politiek-normatieve zelfuiting hebben (activistische ngo's, onderzoeksjournalistiek, ledenomroepen) — bedrijven, staatsorganen en stille bestuurders bleven massaal onbepaald.

## Geschrapt vóór indienen (modelleerdiscipline)
Deze kandidaten haalden het niet — de regel staat erbij:
- **CIDI** (establishment): bron cidi.nl niet verbatim controleerbaar (Cloudflare + herschreven missietekst) → niet ingediend (onbronbaar = niet indienen).
- **Krispijnpunt (219)** (anti-establishment): entiteitsbeschrijving ('lokaal medium Dordrecht') matcht niet met het gevonden kanaal van Jonathan Krispijn — identiteits-twijfel, geen geleende score.
- **X/Twitter (159)**, **Cora van Nieuwenhuizen (198)**: establishment-signaal enkel op *toon*/retoriek gebaseerd → retoriek ≠ substantie.
- **Raymond Knops (117)**, **Angelien Eijsink (201)** (establishment): uiting gedaan vanuit hun NIDV-*functie* → structureel ≠ ideologisch (een bestuursrol is geen houding-uiting).
- **Bas Erlings (211)** (establishment): FVD-verbodspleidooi via NieuwRechts.nl, te dun/partijdig als enige bron voor deze pool.
- **Teldersstichting (46)**, **ProDemos (288)** (establishment): rechtsorde-affirmatie resp. 'spelregels uitleggen' te generiek — geen onderscheidende houding.
- **NRC Media (100)** (cultureel): dubbel met het al bestaande NRC-signaal; de holding draagt geen eigen lijn.

## Citaatcorrecties uit de verificatiewave
6 signalen droegen een licht afwijkend citaat; alle zijn met de **letterlijke** brontekst gecorrigeerd (de claim bleef in alle gevallen gedragen): Renske Leijten, Rosenmöller, Jet Bussemaker, Maike Olij (woordvolgorde/parafrase), Bilderberg en Christophe Convent (herformulering). Claim-bijstellingen: André van der Louw ('mede-auteur' → 'leidende figuur van Nieuw Links'), Bauke Geersing (naam).

## Ingediende signalen per entiteit

| entity_id | entiteit | as:pool | arg_id | bron |
|---|---|---|---|---|
| 306 | ABN AMRO | cultureel:progressief | 1086 | ABN Amro maakt excuses voor slavernijverleden |
| 317 | Adessium Foundation | cultureel:progressief | 1072 | Adessium Foundation — About us (missiepagina) |
| 185 | André van der Louw | economisch:links | 1139 | Nieuw Links in de PvdA (1965-1971) |
| 185 | André van der Louw | establishment:anti-establishment | 1140 | Nieuw Links in de PvdA (1965-1971) |
| 334 | Argos (onderzoeksjournalistiek radioprogramma) | establishment:anti-establishment | 1005 | Over Argos — Wij zijn Argos (missiepagina) |
| 149 | Arjan el Fassed | economisch:links | 1152 | Arjan el Fassed (OpenState): "De overheid weet alles va |
| 149 | Arjan el Fassed | establishment:anti-establishment | 1153 | Arjan el Fassed (OpenState): "De overheid weet alles va |
| 213 | Arnold Karskens | cultureel:conservatief | 1098 | Ongehoord Nederland-voorzitter Arnold Karskens: 'Alles  |
| 116 | Bart de Liefde | economisch:rechts | 1151 | Kamerlid Bart de Liefde: 'Ik heb me niet over sector ui |
| 183 | Bas Eenhoorn | economisch:rechts | 1148 | Liberale rijmpjes |
| 20 | Bilderberg Groep | establishment:establishment | 1018 | Bilderberg Meetings — About Bilderberg Meetings (offici |
| 310 | Bits of Freedom | economisch:links | 1025 | Bits of Freedom — homepage/missietekst |
| 310 | Bits of Freedom | establishment:anti-establishment | 1026 | Bits of Freedom — homepage/missietekst |
| 29 | BlackRock | establishment:establishment | 1091 | The Power of Capitalism, Larry Fink's 2022 Letter to CE |
| 214 | Bouke Geersing | cultureel:conservatief | 1109 | NPO moet breken met eenzijdigheid en woke-propaganda |
| 87 | Brandpunt (voormalig KRO-actualiteitenprogramma) | cultureel:progressief | 1006 | Brandpunt — B&G Wiki (Beeld & Geluid) |
| 180 | Bruno Bruins | economisch:links | 1146 | Bam! Minister Bruins dreigt farmaceuten aan de schandpa |
| 326 | Bureau Clara Wichmann | cultureel:progressief | 1050 | Bureau Clara Wichmann — Over ons |
| 261 | Bureau Spotlight (lokale onderzoeksjournalistiek) | establishment:anti-establishment | 1188 | Bureau Spotlight — Over ons (missie) |
| 18 | Chris Oomen (DSW, financier) | establishment:anti-establishment | 1159 | DSW-directeur Chris Oomen: 'De zorgmarkt zit op een doo |
| 14 | Christian Van Thillo (DPG Media) | economisch:rechts | 1158 | Van Thillo: 'Gratis nieuws op NPO-websites is oneerlijk |
| 239 | Christophe Convent (Epifin) | establishment:establishment | 1160 | Hebben we nieuwe politieke spelregels nodig? Christophe |
| 330 | Controle Alt Delete | cultureel:progressief | 1051 | Controle Alt Delete — Over ons (missie) |
| 330 | Controle Alt Delete | establishment:anti-establishment | 1052 | Controle Alt Delete — Over ons (missie) |
| 248 | de andere krant | establishment:anti-establishment | 1004 | De Andere Krant — Over ons |
| 13 | De Correspondent | cultureel:progressief | 1033 | De Correspondent — Manifest (10 uitgangspunten) |
| 13 | De Correspondent | economisch:links | 1034 | Een progressief verhaal, hoe klinkt dat dan wel? |
| 264 | De Groene Amsterdammer | economisch:links | 1039 | Sander Heijne over het nieuwe Vrij Nederland: 'Streetwi |
| 264 | De Groene Amsterdammer | establishment:anti-establishment | 1040 | De Groene Amsterdammer — Geschiedenis (over-pagina) |
| 89 | De Morgen | cultureel:progressief | 1041 | De Morgen bestaat niet meer |
| 89 | De Morgen | economisch:links | 1042 | De Morgen — Wikipedia (NL) |
| 307 | De Nederlandsche Bank (DNB) | cultureel:progressief | 1096 | De Nederlandsche Bank biedt excuses aan voor slavernijv |
| 249 | De Nieuwe Wereld | establishment:anti-establishment | 1043 | De Nieuwe Wereld — Over ons |
| 9 | De Telegraaf | cultureel:conservatief | 1037 | Hoofdredacteur van De Telegraaf Kamran Ullah: 'Ik ben t |
| 9 | De Telegraaf | cultureel:conservatief | 1038 | Tussen feministische bijlagen en rechtse koppen: wat ma |
| 4 | de Volkskrant | cultureel:progressief | 1027 | Nieuw redactiestatuut voor de Volkskrant |
| 208 | Dominique Weesie | cultureel:conservatief | 1099 | Dominique Weesie: 'Ik vind Francisco van Jole een ongel |
| 1 | DPG Media | economisch:rechts | 1032 | Kees Lunshoflezing 2024 door Christian Van Thillo (voll |
| 162 | ECB (Europese Centrale Bank) | economisch:rechts | 1093 | ECB — Monetary policy: Introduction (mandaat-uitleg) |
| 199 | Energie-Nederland | economisch:rechts | 1013 | Energie-Nederland — Standpunt marktwerking elektricitei |
| 147 | EO-redactie | cultureel:conservatief | 1044 | EO — Missie & ons verhaal (Over de EO) |
| 181 | Eric van der Burg | cultureel:conservatief | 1145 | Eric van der Burg in 'politiek café' VVD: 'toestaan ill |
| 181 | Eric van der Burg | cultureel:progressief | 1144 | Eric van der Burg (VVD): 'linkse' wethouder neemt 'een  |
| 167 | Ernst Kuipers | economisch:links | 1167 | Minister Ernst Kuipers: "We moeten afstappen van de boo |
| 167 | Ernst Kuipers | economisch:rechts | 1168 | Interview minister Kuipers: 'Ik ben geen voorstander va |
| 279 | European Broadcasting Union (EBU) | economisch:links | 1053 | EBU — About the EBU |
| 328 | European Digital Rights (EDRi) | cultureel:progressief | 1056 | EDRi — About us / Who we are (mission & vision) |
| 328 | European Digital Rights (EDRi) | economisch:links | 1054 | EDRi — About us / Who we are (mission & vision) |
| 328 | European Digital Rights (EDRi) | establishment:anti-establishment | 1055 | EDRi — About us / Who we are (mission & vision) |
| 24 | European Publishers Council | economisch:rechts | 1019 | European Publishers Council — homepage (missie en core  |
| 22 | European Round Table of Industrialists | economisch:rechts | 1020 | ERT — About us (missiepagina) |
| 22 | European Round Table of Industrialists | establishment:establishment | 1021 | ERT — About us (missiepagina) |
| 227 | Farah Karimi | economisch:links | 1141 | GroenLinks-PvdA — Onze mensen: Farah Karimi (profielpag |
| 257 | Follow the Money | establishment:anti-establishment | 1035 | Follow the Money — Over FTM |
| 115 | Frank Heemskerk | economisch:rechts | 1149 | Interview met Frank Heemskerk - Staatssecretaris Econom |
| 115 | Frank Heemskerk | establishment:establishment | 1150 | Interview met Frank Heemskerk - Staatssecretaris Econom |
| 151 | Frits Huffnagel | cultureel:conservatief | 1156 | Frits Huffnagel (VVD) bukt diep voor diversiteitsdramme |
| 151 | Frits Huffnagel | economisch:rechts | 1155 | Smaakmakers over de formatie: Frits Huffnagel (VVD) (De |
| 229 | Gemeente Amsterdam | cultureel:progressief | 1094 | Burgemeester Halsema biedt excuses aan voor slavernijve |
| 225 | Gert-Jan Segers | cultureel:conservatief | 1124 | 7 uitspraken van Gert-Jan Segers over de 'verweesde' sa |
| 225 | Gert-Jan Segers | economisch:links | 1123 | Inzet Segers bij volgende formatie is drastisch hervorm |
| 90 | Gezond Verstand | establishment:anti-establishment | 1045 | Gezond Verstand — Over ons |
| 109 | Hans Hillen | cultureel:conservatief | 1138 | Opheldring over het conservatisme |
| 44 | HCSS (The Hague Centre for Strategic Studies) | establishment:establishment | 1009 | HCSS — About HCSS (missiepagina) |
| 6 | Het Parool | economisch:links | 1030 | Het Parool — Wikipedia (NL) |
| 295 | Humanity in Action | cultureel:progressief | 1057 | Stichting Democratie en Media — Humanity in Action Nede |
| 188 | IKON (voormalige interkerkelijke omroep) | cultureel:progressief | 1007 | Interkerkelijke Omroep Nederland — Wikipedia (EN) |
| 188 | IKON (voormalige interkerkelijke omroep) | economisch:links | 1008 | Lejo Schenk over de moord op de IKON-journalisten in El |
| 314 | ILP Lab (Information, Law & Policy Lab) | economisch:links | 1010 | ILP Lab — homepage/missietekst |
| 258 | Investico (platform voor onderzoeksjournalistiek) | economisch:links | 1073 | Investico — Over ons (missie) |
| 258 | Investico (platform voor onderzoeksjournalistiek) | establishment:anti-establishment | 1189 | Investico — Over ons (missie) |
| 242 | Jan Louis Burggraaf (advocaat/commissaris) | cultureel:conservatief | 1161 | Pijngrens van elastiek |
| 112 | Jan Peter Balkenende | cultureel:conservatief | 1128 | Balkenende: met normen en waarden terug naar de macht i |
| 112 | Jan Peter Balkenende | economisch:links | 1127 | DSGC-voorzitter presenteert boek over verantwoord kapit |
| 255 | Jan Rijkeboer | establishment:anti-establishment | 1169 | Jan Rijkeboer (Azor): 'Laten we deze totale waanzin sto |
| 252 | Jelle van Baardewijk | cultureel:conservatief | 1113 | Waarom we minder vrij zijn dan we denken — interview Je |
| 252 | Jelle van Baardewijk | economisch:links | 1112 | Filosoof Jelle van Baardewijk: kapitalisme met een mens |
| 168 | Jet Bussemaker | cultureel:progressief | 1136 | Jet Bussemaker: 'Altijd emoties bij discussies over vro |
| 168 | Jet Bussemaker | economisch:links | 1135 | Jet Bussemaker: hoogleraar en voorzitter |
| 215 | Jonathan Krispijn | establishment:anti-establishment | 1118 | 'De waarheid verdeelt altijd' — interview Jonathan Kris |
| 202 | Kajsa Ollongren | cultureel:progressief | 1133 | NOS — Ollongren: Baudet gaat verder waar Wilders ophoud |
| 202 | Kajsa Ollongren | establishment:establishment | 1134 | EenVandaag — Defensieminister Kajsa Ollongren stelt 'ge |
| 251 | Karel Beckman | economisch:rechts | 1111 | Lockdown? De democratie is een lockdown |
| 251 | Karel Beckman | establishment:anti-establishment | 1110 | Lockdown? De democratie is een lockdown |
| 148 | Kathleen Ferrier | cultureel:progressief | 1142 | Kathleen Ferrier: "Als vrouw van Surinaamse afkomst sta |
| 148 | Kathleen Ferrier | establishment:establishment | 1143 | Kathleen Ferrier: "Besef wat een groot goed onze democr |
| 212 | Klaas Dijkhoff | cultureel:conservatief | 1126 | Liberalisme dat werkt voor mensen (discussiestuk) |
| 212 | Klaas Dijkhoff | economisch:rechts | 1125 | Liberalisme dat werkt voor mensen (discussiestuk) |
| 125 | KLM | economisch:rechts | 1087 | Dutch air passenger tax to be over eight times higher t |
| 182 | Loek Hermans | economisch:rechts | 1147 | Loek Hermans: “Ook met kleine bijdragen de dingen iets  |
| 303 | LOSON (Landelijk Overlegorgaan Surinamers) | cultureel:progressief | 1060 | Wikipedia — Landelijk Overleg van Surinaamse Organisati |
| 303 | LOSON (Landelijk Overlegorgaan Surinamers) | economisch:links | 1059 | Wikipedia — Landelijk Overleg van Surinaamse Organisati |
| 303 | LOSON (Landelijk Overlegorgaan Surinamers) | establishment:anti-establishment | 1058 | Wikipedia — Landelijk Overleg van Surinaamse Organisati |
| 61 | Maarten van Rossem | economisch:links | 1102 | Maarten van Rossem: 'Het neoliberalisme dient eindelijk |
| 61 | Maarten van Rossem | establishment:establishment | 1103 | Interview Maarten van Rossem — Historisch Nieuwsblad |
| 269 | Maike Olij | economisch:links | 1171 | 5 vragen aan Maike Olij |
| 191 | Marcel van Dam | economisch:links | 1115 | Marcel van Dam (oud-PvdA-minister en grijze rebel): 'De |
| 266 | Media Development Investment Fund (MDIF) | establishment:anti-establishment | 1092 | MDIF — Mission statement |
| 329 | Meld Islamofobie | cultureel:progressief | 1061 | Meld Islamofobie — homepage/missietekst |
| 128 | Microsoft | cultureel:progressief | 1089 | DREAMers make our country and communities stronger (Mic |
| 178 | Mirjam Sterk | economisch:links | 1157 | Mirjam Sterk: 'herstart CDA broodnodig' — interview in  |
| 81 | NAVO | establishment:establishment | 1095 | The North Atlantic Treaty (officiële verdragtekst, prea |
| 280 | Nederlands Uitgeversverbond (NUV) | economisch:rechts | 1015 | Mediafederatie — Doelstelling en activiteiten |
| 114 | Neelie Kroes | economisch:rechts | 1130 | Crazy court decision to ban Uber in Brussels. Show your |
| 323 | New Urban Collective | cultureel:progressief | 1062 | New Urban Collective — Over ons (missie en visie) |
| 200 | NIDV (Stichting Nederlandse Industrie voor Defensie en Veiligheid) | establishment:establishment | 1014 | NIDV — Over NIDV (missiepagina) |
| 274 | Nienke Venema | economisch:links | 1173 | Directeur Stichting Democratie en Media: 'Big tech heef |
| 274 | Nienke Venema | establishment:anti-establishment | 1172 | Directeur Stichting Democratie en Media: 'Big tech heef |
| 10 | NRC | cultureel:progressief | 1031 | 'NRC Handelsblad is niet links en niet rechts' (redacti |
| 69 | NVJ (Nederlandse Vereniging van Journalisten) | economisch:links | 1070 | NVJ steunt ultimatum van FNV en andere vakbonden tegen  |
| 260 | Onderzoekscollectief SPIT | economisch:links | 1075 | Onderzoekscollectief Spit — Over Spit (missie) |
| 260 | Onderzoekscollectief SPIT | establishment:anti-establishment | 1190 | Onderzoekscollectief Spit — Over Spit (missie) |
| 327 | OneWorld | cultureel:progressief | 1046 | Journalistiek die kleur bekent (Linkse protestmedia sch |
| 327 | OneWorld | economisch:links | 1047 | Sinds OneWorld zelfstandig werd groeit het aantal 'vrie |
| 161 | Open Society Foundations | cultureel:progressief | 1063 | Open Society Foundations — Who We Are |
| 161 | Open Society Foundations | establishment:anti-establishment | 1175 | Open Society Foundations — What We Do |
| 331 | Open State Foundation | economisch:links | 1176 | Open State Foundation — Over ons |
| 331 | Open State Foundation | establishment:anti-establishment | 1064 | Open State Foundation — Over ons |
| 278 | Ot van Daalen | establishment:anti-establishment | 1174 | De gebroken belofte van het internet |
| 190 | Paul Rosenmöller | cultureel:progressief | 1132 | Plenaire bijdrage Rosenmöller bij debat over parlementa |
| 190 | Paul Rosenmöller | economisch:links | 1131 | Plenaire bijdrage Rosenmöller (GroenLinks) bij Algemene |
| 119 | Paul Sneijder | economisch:links | 1106 | Journalist Paul Sneijder was journalist én politicus: ' |
| 119 | Paul Sneijder | establishment:establishment | 1107 | Journalist Paul Sneijder was journalist én politicus: ' |
| 224 | Pauw & De Wit | cultureel:progressief | 1048 | Analyse NRC: 'Rechts domineert talkshowtafels' |
| 194 | PAX | economisch:links | 1177 | PAX — Wie wij zijn |
| 194 | PAX | establishment:anti-establishment | 1065 | PAX — Wie wij zijn |
| 60 | Peter R. de Vries | cultureel:progressief | 1104 | Peter R. de Vries: 'Zaak blokkeerfriezen zonde van geld |
| 60 | Peter R. de Vries | establishment:anti-establishment | 1105 | Peter R. de Vries, misdaadjournalist die voor niets of  |
| 58 | Pieter Omtzigt | cultureel:conservatief | 1120 | Denken in oplossingen — HJ Schoo-lezing 2024 |
| 58 | Pieter Omtzigt | economisch:links | 1119 | Denken in oplossingen — HJ Schoo-lezing 2024 |
| 332 | Public Interest Litigation Project (PILP) | establishment:anti-establishment | 1178 | PILP — Over PILP (missie en zaken) |
| 299 | Read my World | cultureel:progressief | 1179 | Read My World — About Read My World (missiepagina) |
| 59 | Renske Leijten | economisch:links | 1121 | Renske Leijten (SP): 'Onze kritiek op het kapitalisme i |
| 59 | Renske Leijten | establishment:anti-establishment | 1122 | Renske Leijten: 'Ik ben periodes heel boos geweest' |
| 62 | Rob de Wijk (HCSS-oprichter, geopolitiek commentator) | establishment:establishment | 1162 | Column Rob de Wijk: Europa reageert veel te lauw op Tru |
| 150 | Rob van Gijzel | economisch:links | 1154 | Oud-burgemeester Rob van Gijzel kijkt terug |
| 312 | Root Legal | economisch:links | 1090 | Nieuw lid raad van toezicht Ot van Daalen: "Technologie |
| 250 | Sander Compagner | establishment:anti-establishment | 1170 | Wat is De Andere Krant en wat staat erin? |
| 308 | SER Topvrouwen | cultureel:progressief | 1180 | Over SER Topvrouwen (over-ons-pagina) |
| 308 | SER Topvrouwen | establishment:establishment | 1067 | Over SER Topvrouwen (over-ons-pagina) |
| 75 | Shell | economisch:rechts | 1085 | Position paper Shell Nederland BV t.b.v. hoorzitting/ro |
| 136 | Shula Rijxman (ex-NPO, D66-wethouder) | economisch:links | 1166 | Shula Rijxman: "Publieke omroep verdient blijvende steu |
| 230 | Stichting de Volkskrant | cultureel:progressief | 1078 | Media Stichtingen — Stichting De Volkskrant |
| 130 | Stichting Democratie en Media | establishment:anti-establishment | 1076 | Stichting Democratie en Media — Geschiedenis (citaat st |
| 325 | Stichting Keti Koti Tafel | cultureel:progressief | 1181 | Stichting Keti Koti Tafel — homepage (missietekst) |
| 254 | Stichting KnowledgeMatters | establishment:anti-establishment | 1077 | De Andere Krant — Over ons |
| 321 | Stichting Platform Islamitische Organisaties Rijnmond (SPIOR) | cultureel:progressief | 1182 | SPIOR — Islamofobie melden (stellingname-pagina) |
| 322 | Stichting Stem op een Vrouw | cultureel:progressief | 1183 | Stichting Democratie en Media — initiatiefpagina Stem o |
| 234 | Stichting ter Bevordering van de Christelijke Pers in Nederland | cultureel:conservatief | 1079 | Media Stichtingen — Stichting ter Bevordering van de Ch |
| 176 | Talitha Muusse | economisch:links | 1117 | Purpose People: waarom millennials geen egocentrische g |
| 176 | Talitha Muusse | establishment:anti-establishment | 1116 | Talitha Muusse: 'Op1 zit te veel op schoot bij de polit |
| 298 | The Black Archives (Amsterdam) | cultureel:progressief | 1184 | The Black Archives — Over ons |
| 259 | The Investigative Desk | establishment:anti-establishment | 1080 | The Investigative Desk — homepage/missie |
| 301 | Theater Rotterdam | cultureel:progressief | 1185 | Theater Rotterdam — Manifest |
| 220 | Thom de Graaf | cultureel:progressief | 1137 | 'Een behoudzuchtig volkje, zeker op democratisch vlak' |
| 118 | Tijs van den Brink | establishment:establishment | 1108 | CDA — kandidaatpagina Tijs van den Brink (Tweede Kamerv |
| 135 | Tjibbe Joustra (topambtenaar/bestuurder) | economisch:links | 1164 | Oud-topambtenaar Tjibbe Joustra: overheid dient niet ef |
| 135 | Tjibbe Joustra (topambtenaar/bestuurder) | establishment:establishment | 1165 | Oud-topambtenaar Tjibbe Joustra: positie ambtenaren sta |
| 324 | Transnational Institute (TNI) | economisch:links | 1011 | Transnational Institute — About TNI |
| 324 | Transnational Institute (TNI) | establishment:anti-establishment | 1012 | Transnational Institute — About TNI |
| 21 | Trilaterale Commissie | establishment:establishment | 1022 | Trilateral Commission — About (missiepagina) |
| 5 | Trouw | cultureel:progressief | 1029 | (Podcast) Hoofdredacteur Cees van der Laan: profiel Tro |
| 5 | Trouw | economisch:links | 1028 | (Podcast) Hoofdredacteur Cees van der Laan: profiel Tro |
| 126 | Uber | economisch:rechts | 1088 | uberPOP stopt in Nederland |
| 36 | Unilever | economisch:rechts | 1084 | Topman Unilever: 'Goed dat Nederland dividendtaks afsch |
| 311 | Universiteit van Amsterdam | cultureel:progressief | 1097 | UvA — Missie en visie Centrale Diversity Office |
| 175 | Vandaag Inside | cultureel:conservatief | 1049 | Analyse NRC: 'Rechts domineert talkshowtafels' |
| 263 | Vers Beton (Rotterdams online magazine) | cultureel:progressief | 1081 | Vers Beton — Missie: Onafhankelijke journalistiek voor  |
| 263 | Vers Beton (Rotterdams online magazine) | economisch:links | 1082 | Vers Beton — Missie: Onafhankelijke journalistiek voor  |
| 204 | Viktor Pinchuk (Oekraïense oligarch, Yalta European Strategy) | establishment:establishment | 1163 | "HOW TO END THE WAR?". The Yalta European Strategy (YES |
| 164 | VNO-NCW | economisch:rechts | 1016 | VNO-NCW — Wat is VNO-NCW? (missiepagina) |
| 164 | VNO-NCW | establishment:establishment | 1017 | VNO-NCW — Wat is VNO-NCW? (missiepagina) |
| 217 | Voor Ons Nederland | establishment:establishment | 1083 | Voor Ons Nederland — missiepagina (homepage) |
| 265 | Vrij Nederland | cultureel:progressief | 1036 | Sander Heijne over het nieuwe Vrij Nederland: 'Streetwi |
| 210 | Wierd Duk | cultureel:conservatief | 1101 | Wierd Duk: 'We gooien weg wat ons tot Nederlander maakt |
| 210 | Wierd Duk | economisch:links | 1100 | Wierd Duk: 'Als ik al iets ben, dan is het sociaaldemoc |
| 335 | Willem Oltmans | establishment:anti-establishment | 1114 | Willem Oltmans (1925-2004): onafhankelijk persmuskiet |
| 309 | Women in Financial Services (WIFS) | cultureel:progressief | 1186 | WIFS — homepage (missie en ambitie) |
| 309 | Women in Financial Services (WIFS) | establishment:establishment | 1187 | WIFS — homepage (missie en ambitie) |
| 23 | World Economic Forum | establishment:establishment | 1023 | World Economic Forum — Our Mission |
| 111 | Wouter Bos | economisch:links | 1129 | Binnenlands Bestuur — Wouter Bos tegen participatiesame |
| 203 | Yalta European Strategy | establishment:establishment | 1024 | Yalta European Strategy — About YES |

## Onbepaald gelaten entiteiten
Voor deze 166 entiteiten is gezocht maar géén citeerbare, verbatim verifieerbare politiek-normatieve zelfuiting gevonden — onbepaald is hier de correcte uitkomst (geen geleende of functie-afgeleide score). Verwacht patroon: commerciële bedrijven, staats-/toezichtsorganen, persbureaus (neutraliteitsmissie), juridische houdsterstichtingen en publiciteitsarme bestuurders.

- **A.S. Watson (Kruidvat)** (37) — Alleen duurzaamheidsverslagen, samenwerking met voedselbanken/Armoedefonds en een 'Inclusion Council' voor assortiment (zonnebrand/make-up voor donker
- **Aartie Hoeblal** (277) — Alleen assen economisch en establishment onderzocht (cultureel al gedekt). SDM-interview gefetcht: haar uitspraken ('Er is zo'n kloof tussen arm en ri
- **Abdeluheb Choho** (179) — Gezocht naar eigen uitspraken als wethouder duurzaamheid, als bestuursvoorzitter VluchtelingenWerk en als RVO-directeur. Alles wat verifieerbaar is (A
- **ACM (Autoriteit Consument & Markt)** (48) — Missie ('markten goed laten werken voor mensen en bedrijven') en de nuance dat marktwerking geen doel op zich is maar middel tegen marktfalen, is toez
- **AD (Algemeen Dagblad)** (3) — Het AD-redactiestatuut formuleert de krant expliciet als onafhankelijk medium zonder binding aan een politieke partij of levensbeschouwelijke organisa
- **Adidas** (95) — Adidas deed in 2020 een publieke BLM-verklaring ('time to own up to our silence') met een investeringsbelofte, maar het dossier is gemengd en deels te
- **Afke Schaart** (120) — Gezocht in interviews, opiniestukken en persberichten. De enige gevonden directe citaten zijn GSMA-persberichten (2018-2019) waarin zij als 'VP & Head
- **AFP (Agence France-Presse)** (171) — AFP werkt onder het wettelijke statuut van 1957 dat onafhankelijkheid van politieke en economische invloeden vastlegt — een geïnstitutionaliseerde neu
- **AIVD** (173) — De AIVD-missie en het inlichtingenwoordenboek beschrijven uitsluitend de wettelijke taak (dreigingsonderzoek t.b.v. nationale veiligheid); de dienst b
- **Albert Heijn** (32) — Alleen duurzaamheids-/missietaal (Voedseltransitie Adviesraad, B Corp, 'beter eten bereikbaar voor iedereen') en een public-affairs-functieomschrijvin
- **Allard Pierson (erfgoedinstelling UvA)** (292) — De eigen missietekst is neutraal-institutioneel: 'Het Allard Pierson verzamelt, beheert, ontsluit, onderzoekt en presenteert waardevol en relevant cul
- **Anita Nijboer** (245) — Interviews gevonden (Stadszaken, PONT Omgeving, Rechtencircuit) bevatten uitsluitend vakinhoudelijke uitspraken over omgevingsrecht en haar werkstijl 
- **Annetje Ottow** (246) — Interviews (Universiteit Leiden, Mr. Online, ToeZine, DUB) bevatten professioneel-academische uitspraken over toezicht en bestuurscultuur ('Goed toezi
- **ANP** (12) — Het ANP presenteert zich als 'onafhankelijke bron die op transparante wijze betrouwbaar nieuws levert' — een expliciete neutraliteits-/onpartijdigheid
- **AP (Associated Press)** (170) — AP hanteert een Statement of News Values gericht op feitelijke, niet-partijdige verslaggeving — een neutraliteitsmissie, geen pool-signaal; geen citee
- **ASML** (77) — Wennink uitte kritiek op versobering van de 30%-regeling en het vestigingsklimaat ('kloof tussen bedrijfsleven en politiek'), maar dit is consistent g
- **Autoriteit Persoonsgegevens** (316) — Voorzitter Wolfsen waarschuwt in blogs en het jaarverslag scherp voor surveillancestaat, 'datahonger' van de overheid en Big Tech-macht, maar dat is p
- **AVROTROS** (141) — Missie-/historiepagina (gefetcht) claimt expliciet neutraliteit: 'De TROS hoort niet bij een geloof. Niet bij een politieke stroming.' en 'We leggen m
- **banken.nl** (228) — banken.nl presenteert zich als onafhankelijk informatieplatform van/over de bankensector (nieuws, trends, vacatures) dat samenwerkt met banken en fint
- **Belastingdienst** (52) — Missie/visie-pagina's bevatten alleen taakomschrijving ('eerlijk en zorgvuldig belastingen heffen en innen') en uitvoeringsprincipes. Geen citeerbare 
- **Bernadette de Bethune (DPG-commissaris)** (240) — Alleen biografische en zakelijke informatie gevonden (Vandewiele Group, CV bij Atenor, KU Leuven-verleden); geen interviews of citeerbare eigen uitspr
- **Bijlmer Parktheater** (297) — De organisatietekst profileert het theater als 'hét theater van het nieuwe Nederland', 'deskundigen op het gebied van intercultureel programmeren' met
- **BOinK (Belangenvereniging van Ouders in de Kinderopvang)** (70) — De over-ons-pagina bevat alleen neutrale belangenbehartigingstaal ('kwalitatief goede en betaalbare kinderopvang', 'heldere, eenduidige regelgeving') 
- **Bol.com** (34) — Bol.com weerde producten met stereotype Zwarte Piet-afbeeldingen en voert inclusie-taal ('inclusieve samenleving met gelijke kansen'), maar dat zijn a
- **Camiel Eurlings** (113) — Gezocht naar eigen ideologische uitingen (interviews, opiniestukken, EP-periode incl. Turkije-rapporteurschap). Gevonden materiaal is loopbaan-/schand
- **Clingendael Instituut** (43) — Missietekst opgehaald en gelezen (via Wayback-snapshot van de eigen about-pagina, footer © 2026): 'Our independent research, training programmes and e
- **Concentra** (28) — De katholieke en Vlaamsgezinde inspiratie van huistitel Het Belang van Limburg is in de Encyclopedie van de Vlaamse Beweging (pagina opgehaald) uitslu
- **CPB (Centraal Planbureau)** (83) — Het CPB positioneert zichzelf uitdrukkelijk als onafhankelijk en dienend aan het primaat van de politiek. Kritiek dat CPB-modellen impliciet normatiev
- **CvdM (Commissariaat voor de Media)** (50) — Missie (democratische functies van media beschermen, eerlijk speelveld, redactionele vrijheid respecteren) is de Mediawet-toezichtstaak. Geen normatie
- **De Brauw Blackstone Westbroek** (315) — Pro-bonopraktijk, UNICEF-partnerschap en rule-of-law-taal ('access to justice', 'public debate is an essential ingredient of the rule of law') zijn be
- **De Persgroep (voorloper DPG)** (108) — Gevonden uitspraken (Van Thillo: 'een uitgever moet zich niet bemoeien met het wat van de krant, wel met het hoe'; kwaliteit/journalistiek als mantra)
- **Dijkhoff & Segers** (226) — De podcastbeschrijving (Podimo/Apple Podcasts) formuleert alleen een format ('ongefilterde blik', 'vrij van fractiediscipline, spindoctors en persoonl
- **DPG Media Group NV** (233) — Gezocht naar missie-/beginselteksten en uitspraken van de groep. Gevonden: commerciële missietaal en een governance-claim over redactionele onafhankel
- **DPG Media Services NV** (236) — Puur operationele dochtervennootschap (voortzetting De Persgroep Publishing, advertentie- en uitgeefactiviteiten in Antwerpen). Geen eigen missie- of 
- **dsm-firmenich** (79) — Alleen purpose-/duurzaamheidstaal ('progress to life') op de eigen site gevonden; geen enkele citeerbare politiek-normatieve stellingname.
- **ECP | Platform voor de InformatieSamenleving** (289) — ECP presenteert zichzelf expliciet als 'een onafhankelijk en neutraal platform' dat 'overheid, wetenschap, bedrijfsleven, onderwijs en maatschappelijk
- **Eeke van der Veen** (121) — De artikelen met zijn bekende marktwerking-uitspraken (Zorgvisie 8-6-2010, Medisch Contact) staan achter een paywall en konden niet met WebFetch gever
- **EIB (Europese Investeringsbank)** (154) — De EIB profileert zich als 'EU-klimaatbank', maar dat is uitvoering van EU-beleid (Green Deal) — mandaatvolgend, geen eigen ideologische stellingname.
- **Emmanuel Van Thillo (Epifin)** (241) — Twee zoekrondes leverden uitsluitend bedrijfsregisters (jaarrekening.be, FinCheck, Companies House) en stukken over de familieholding op; geen enkel i
- **EO** (138) — Alleen de economische as onderzocht (cultureel/establishment al gedekt). De EO-missie is evangelisatie; EO Metterdaad doet armoedehulpwerk (charitatie
- **Epifin (Van Thillo-familieholding)** (26) — Financiële familieholding (99,6% DPG Media Group, aandeelhouders achter een STAK). Bronnen beschrijven uitsluitend structuur en dividenden; er bestaat
- **Erik Roddenhof (DPG-CEO)** (247) — Zijn vindbare uitspraken zijn bedrijfsstrategisch: samenwerking DPG–NPO tegen de dominantie van internationale techplatforms, 'Google is gewoon niet e
- **Ernestine Comvalius** (276) — Alleen assen economisch en establishment onderzocht (cultureel al gedekt). Haar spoken-word-bijdrage op sdm.nl en het SDM-toezichthouder-interview gaa
- **Ernst & Young** (124) — EY's 'Building a better working world' en public-policy-teksten (vertrouwen in kapitaalmarkten, transparantie) zijn bedrijfs-/CSR-taal, geen ideologis
- **European Communication Research and Education Association (ECREA)** (286) — De about-/missiepagina bleek niet direct bereikbaar; de wel vindbare sectie-doelstellingen (Crisis Communication, Television Studies, Communication La
- **European Press Prize** (268) — Eigen missietekst gevonden en geverifieerd: 'The European Press Prize exists to recognise, honour, and encourage quality journalism across Europe – em
- **Europese Commissie** (155) — De integratiebevorderende rol van de Commissie is haar verdragstaak; gevonden teksten over 'ever closer union' zijn externe analyses of taakbeschrijvi
- **Familie Baert (Mediahuis-aandeelhouders)** (16) — Gevonden materiaal (Apache-dossier 'Concentra, een katholiek bolwerk', Trends 'stille fortuinen van Vlaanderen') karakteriseert de familie van buitena
- **Familie Van Puijenbroek (TMG/VP Exploitatie)** (17) — Vondsten betreffen vooral de TMG-overname (2017, zakelijk) en een FD-partnerinterview (gesponsorde ING-content) waarin Guus van Puijenbroek over impac
- **Frederieke Leeflang (NPO-bestuursvoorzitter)** (134) — Geverifieerde citaten (Villamedia, mei 2024) zijn bestuurlijk-managerieel en gemengd: ze accepteert de bezuiniging van 100 miljoen mits het bestel wor
- **Free Press Unlimited** (68) — De eigen missie ('People deserve to know'; 'to ensure that independent news and information remains available to everyone, especially people in countr
- **Gerrit-Jan Wolffensperger** (186) — Drie zoekrondes en drie paginafetches (De Groene Amsterdammer-profiel 1995, NieuwNieuws-archief over zijn Volkskrant-brief 2022, parlement.com-biograf
- **Google** (40) — Missie ('organize the world's information') en 'Ten Things We Know to Be True' zijn product-/bedrijfsfilosofie, geen pool-codeerbare politieke stellin
- **Groupe Bruxelles Lambert** (25) — Eigen site gelezen: uitsluitend investeringstaal ('an established investment holding company', 'focused on long-term value creation', 'attractive divi
- **Harm Bruins Slot** (187) — Drie zoekopdrachten leverden vrijwel uitsluitend biografische feiten op (ARP/CDA-achtergrond, burgemeesterschappen, SG OCW, NPO-voorzitterschap 2003-2
- **Harold Rimmelzwaan** (270) — Gevonden materiaal (Onderwijs van Morgen over gepersonaliseerd leren, benoemingsberichten NUV/Malmberg) bevat uitsluitend vakinhoudelijke uitspraken o
- **Henk Kummeling** (221) — FTM-interview (juli 2024) gefetcht en gelezen: zijn uitspraken ('Efficiency is veel meer de key driver geworden, de kern van overheidsfunctioneren') z
- **Het Financieele Dagblad** (195) — Het FD presenteert zich als onafhankelijke zakenkrant; de eigen 'over het FD'-pagina zit achter een paywall (402) en de gevonden externe typeringen ('
- **Hill+Knowlton** (122) — H+K positioneert zich als dienstverlener voor klanten over het hele politieke spectrum; geen eigen gepubliceerde ideologische stellingname gevonden. K
- **Hiphophuis (Rotterdam)** (300) — De eigen missietekst is community-empowerment-taal: 'hip-hop brings the ideas about equality, ownership, creativity and innovation that are needed in 
- **Hogeschool Utrecht** (283) — De HU heeft wel een D&I-visiedocument (maart 2022), maar de inhoud is integraal generieke inclusietaal ('elk talent telt', 'afspiegeling van de maatsc
- **Hugo Jansen** (256) — Journalistiek gedocumenteerd (Zuidwest Update, Chris Klomp, NOS) als financier/garantsteller van De Andere Krant, plaatser van pro-Poetin-billboards e
- **IBS Capital Allies** (319) — Maatschappelijk-verantwoord-beleggen-taal (UN Global Compact, richtlijnen Goede Doelen Nederland) is CSR-taal, geen expliciete politiek-normatieve ste
- **Ieko Sevinga (Mediahuis-commissaris)** (238) — Vindbare interviews (VG Visie, 2023/2024) gaan over vastgoedonderhoud en verduurzaming van corporatiewoningen in zijn rol als CEO van NOK.5; de passag
- **Imerys** (102) — Frans industrieel mineralenconcern. Alle gevonden zelfuitingen (SustainAgility, 'Every Person Matters', diversity/equity/inclusion als HR-beleid) zijn
- **ING** (76) — ING publiceert een 'diversity manifest' en heeft medewerkersnetwerken (Rainbow Lions e.d.), maar de motivering is expliciet de business case ('zonder 
- **Internationaal Instituut voor Sociale Geschiedenis (IISG)** (291) — Missiepagina gelezen: het IISG beschrijft zijn onderzoeks- en collectiescope ('labour and social movements', 'work, labour relations and social inequa
- **Jack de Vries** (110) — Alle gevonden citaten van De Vries gaan over campagnetechniek en mediastrategie ('het CDA is de Volvo van de Nederlandse politiek', analyse van anderm
- **Jan van Dun** (244) — Interviews (Villamedia over freelancetarieven bij huis-aan-huisbladen, Nederlands MediaNieuws over folders) bevatten bedrijfseconomische uitspraken ov
- **Jeanine van der Vlist** (243) — Gevonden interviews (Computable CEO van het Jaar, Managementscope, vakpers) bevatten uitsluitend zakelijk-professionele uitspraken over ICT en leiders
- **John de Mol (Talpa)** (19) — Geverifieerde citaten (Folia/Room for Discussion, 2017) zijn persoonlijk-zakelijk ('Er is maar een machthebber, en dat is de kijker. Mijn rapportcijfe
- **KBC Groep** (73) — De katholiek-coöperatieve wortels (Kredietbank, CERA, Boerenbond/MRBB) zijn structureel-historische feiten, geen zelfuiting van KBC. Actuele KBC-commu
- **Kiesraad** (222) — Centraal stembureau en kiesrecht-adviseur; alle gevonden uitingen betreffen onafhankelijkheid en betrouwbaarheid van het verkiezingsproces — de kern v
- **Koningshuis** (71) — De positie van het staatshoofd is grondwettelijk vastgelegd en de ministeriële verantwoordelijkheid maakt uitingen van de Koning staatsrechtelijk rege
- **Koninklijke Bibliotheek (KB)** (290) — De missiepagina (via WebFetch geverifieerd) bevat taakomschrijving ('collectie zichtbaar, bruikbaar en houdbaar voor alle Nederlanders') — dat is de w
- **KPMG** (123) — Missie ('inspire trust and empower change') en waarden zijn beroepsethische/CSR-taal (integriteit, duurzaamheid, klimaat) zonder expliciete politiek-n
- **KRO-NCRV** (140) — Alleen de economische as onderzocht (cultureel/establishment al gedekt). De missie 'de wereld groener, eerlijker en vriendelijker maken' is waarden-/C
- **Lidl** (33) — Gevonden: productbeleid (stoppen met sigarettenverkoop, meer plantaardig aanbod) en rechtszaken. Productbeleid is geen citeerbare politiek-normatieve 
- **Lily Knibbeler** (273) — Alleen assen economisch en establishment onderzocht (cultureel al gedekt). In het SVDJ-dubbelinterview (nov 2024) zegt zij 'De onafhankelijke journali
- **Ludwig Criel (DPG-bestuurder)** (237) — Enige vindbare citaten zijn corporate mededelingen (benoemingspersberichten over de managementstructuur van DPG). Geen interviews of opiniestukken met
- **Malmberg (educatieve uitgever)** (281) — De katholieke oorsprong (1885, roomse schoolboeken) is een historisch feit beschreven door derden; de huidige missie ('leraren ondersteunen met waarde
- **Martijn Bennis** (272) — SVDJ-dubbelinterview (nov 2024) gefetcht: uitspraken als 'Er zijn op deze wereld nog zo'n 30 echte democratieën, en die hebben in ieder geval gemeen d
- **McKinsey** (80) — McKinsey presenteert zichzelf expliciet als politiek neutraal ('We do execution, not policy' — geciteerd in kritische journalistiek). Zelfverklaarde n
- **Mediahuis** (2) — Geen codeerbare politiek-normatieve uiting van het concern gevonden op enige as. De eigen missietaal ('onvoorwaardelijk geloof in onafhankelijke journ
- **Mediahuis Partners** (93) — Holding van de stichtende families (Leysen, Baert e.a.) boven Mediahuis. Bronnen behandelen alleen eigendomsstructuur, waardering en dividenden; geen 
- **Meta (Facebook/Instagram)** (41) — Overwogen: de 'More Speech and Fewer Mistakes'-verklaring (jan 2025, einde factcheckprogramma, 'restore free expression'). Dat is echter een moderatie
- **Metro** (101) — Metro is een gratis, volledig advertentie-gefinancierd forenzendagblad zonder gedocumenteerde eigen ideologische lijn; bronnen typeren gratis kranten 
- **Ministerie van Binnenlandse Zaken** (156) — De missie ('samen leven en wonen, in een democratische rechtsstaat') en het borgen van grondrechten zijn de wettelijke taak van BZK. Geen eigen ideolo
- **Ministerie van Buitenlandse Zaken** (86) — Het bevorderen van de internationale rechtsorde is een grondwettelijke opdracht (art. 90 Gw) en begrotingsartikel — taakomschrijving, geen eigen ideol
- **Ministerie van Defensie** (85) — Het 'verhaal van Defensie' ('wij vechten voor een wereld waarin mensen in vrijheid en veiligheid kunnen leven') is missieretoriek binnen de wettelijke
- **Ministerie van OCW** (132) — Het emancipatiebeleid (gelijke rechten voor vrouwen en lhbtiq+-personen) is toegewezen kabinetsbeleid en begrotingsartikel — beleid van de zittende re
- **MN (pensioenuitvoerder)** (304) — MN's 'leidende beginselen' voor verantwoord beleggen (ESG verweven in beleid, bijdragen aan oplossen maatschappelijke problemen) zijn institutionele M
- **Nationaal Media Onderzoek (NMO)** (177) — Eigen over-pagina geverifieerd: 'Het Nationaal Media Onderzoek (NMO) biedt inzicht in wat Nederland via alle media, platforms en devices leest, luiste
- **Nationale DenkTank** (45) — Eigen missieteksten gelezen: 'Jonge denk- en daadkracht voor een betere samenleving', 'Als netwerkorganisatie bundelen we de kracht van jong talent me
- **NCTV** (172) — De dreigingsbeelden (incl. 'anti-institutioneel extremisme') zijn uitvoering van de wettelijke coördinatietaak; de NCTV benadrukt zelf dat ruimte voor
- **Nederlandse Loterij** (38) — CEO Blok pleit publiek voor verlaging van de kansspelbelasting en is voorstander van verzelfstandiging, maar de framing is consequent kanalisatie/cons
- **Nederlandse Toneeljury (VSCD)** (302) — De Nederlandse Toneeljury is een vakjury die nominaties en winnaars van de VSCD Toneelprijzen aanwijst ('de mooiste, meest opvallende en indrukwekkend
- **Nederlandse Unesco Commissie** (296) — Mensenrechten, vrede en vrije media als uitgangspunt zijn het statutaire UNESCO-mandaat dat de commissie uitdraagt — taakomschrijving, geen eigen stel
- **Northern Trust** (320) — Northern Trust verklaart expliciet geen politieke donaties te doen en beperkt public-policy-posities tot 'safety and soundness of the financial system
- **NOS** (11) — Onderzocht op de assen economisch en cultureel (establishment was al gedekt). Geen codeerbare richting gevonden: het wettelijk neutraliteitsmandaat wo
- **NOS-hoofdredactie** (146) — De enige gedocumenteerde eigen uiting is een expliciete neutraliteitsclaim (hoofdredacteur Gelauff: als redactie 'over nieuwsfeiten geen mening' hebbe
- **NPO (Nederlandse Publieke Omroep, koepel)** (131) — Eigen 'waar we voor staan'-pagina geverifieerd: 'De publieke omroep wil er voor iedereen in Nederland zijn', 'Iedereen hoort erbij, vinden we bij de p
- **NTR** (137) — De NTR is een ledenloze taakomroep met een wettelijke opdracht; kernwaarden zijn 'onafhankelijk, onpartijdig, objectief, betrouwbaar' — een expliciet 
- **NU.nl** (7) — NU.nl profileert zich in interviews met hoofdredacteur Hoekman uitdrukkelijk als neutraal en meningloos; een neutraliteitsclaim is geen richting-signa
- **NWO** (196) — Zoeksnippets suggereerden een expliciete antiracisme-verklaring ('Inclusive science matters'), maar die pagina gaf 404 en de wel opgehaalde D&I-pagina
- **Omroep MAX** (143) — MAX' missie is belangenbehartiging van 50-plussers (Meldpunt, MAX Ombudsman, MAX Maakt Mogelijk) — doelgroep-/servicetaal, geen politiek-normatieve st
- **Omroep ZWART** (206) — Alleen de economische as onderzocht (cultureel/establishment al gedekt). De zoekresultaten troffen vooral het 'Zwart Manifest' — een andere organisati
- **OMT (Outbreak Management Team)** (106) — Het OMT adviseert uitdrukkelijk beperkt tot de medische invalshoek van een epidemie; discussie over rolvermenging en aangepaste adviezen is externe kr
- **Ongehoord Nederland** (205) — Alleen de economische as onderzocht (andere assen al gedekt). De zoekronde leverde geen fetch-verifieerbare eigen uiting van ON! met een expliciet eco
- **Op1** (174) — Op1 is per format een programma met 'wisselende signatuur': roulerende presentatieduo's van omroepen met uiteenlopende kleur (BNNVARA, EO, MAX, WNL). 
- **Optimix Vermogensbeheer** (305) — UN PRI/Global Compact-ondertekening en duurzaam-beleggen-taal zijn CSR; geen expliciete politiek-normatieve stellingname gevonden. Onbepaald.
- **PCM Uitgevers (historisch)** (96) — PCM's statutaire kern was 'bevordering van de pluriformiteit van de pers' en het behoud van de identiteit van uiteenlopende identiteitskranten (progre
- **Philips** (78) — CEO Jakobs uit in interviews kritiek op Europese regeldruk en lastendruk, maar dat is generieke vestigingsklimaat-taal in (deels betaalde) interviews;
- **Pieter Broertjes** (184) — Broertjes' PvdA-lidmaatschap en burgemeesterschap zijn structurele feiten, geen signalen. In de fetchbare bronnen (Villamedia-artikel over zijn PvdA-l
- **Politie** (84) — 'Waakzaam en dienstbaar' en het diversiteits-/inclusiebeleid zijn taak- en organisatietaal (legitimiteit, personeelsbeleid) — HR-/CSR-achtig, geen exp
- **Postcode Loterij** (39) — De eigen site formuleert het doel als steun aan 'goede doelen die zich inzetten voor een rechtvaardige, gezonde en groene wereld' — liefdadigheids-fra
- **PowNed** (145) — De eigen missiepagina (gefetcht) claimt expliciet 'geen binding met links of rechts' en 'liberaal-kritisch' — een neutraliteitsclaim, geen pool-signaa
- **Prins Bernhard Cultuurfonds** (294) — Eigen over-ons-pagina geverifieerd: 'Cultuur verbindt ons. We hebben elkaar nodig. Want zonder ons geen cultuur. En zonder cultuur geen ons.' plus inv
- **Procter & Gamble** (35) — OpenSecrets documenteert generieke lobby-uitgaven en een PAC, maar geen citeerbare publieke politiek-normatieve stellingname van het bedrijf zelf over
- **Raad van State** (223) — De jaarverslag-beschouwingen over de rechtsstaat ('onderhoud de dijken van de rechtsstaat', constitutionele geletterdheid) zijn normatief van toon maa
- **Raad voor de Journalistiek** (51) — Orgaan voor journalistieke zelfregulering; het standpunt dat zelfregulering en volledige vrijheid en onafhankelijkheid de beste vorm zijn voor journal
- **Radboud Universiteit** (103) — Er is een strategisch DEI-plan 2021-2026, maar de opgehaalde pagina bevat uitsluitend generieke HR-taal ('equal opportunities for all', 'everyone feel
- **Rechtbank Den Haag** (313) — Rechterlijke instantie; bekende maatschappelijk gevoelige vonnissen (Urgenda-lijn, RBV/F-35) zijn rechtspraak — de wettelijke taak — geen normatieve z
- **Reuters** (169) — De Trust Principles (1941) verplichten Reuters tot 'integrity, independence, and freedom from bias' — een expliciete onpartijdigheidsmissie; een neutr
- **Rijksuniversiteit Groningen** (284) — Het D&I-beleid is overwegend procedureel-generiek ('thuis voelen', 'gelijke kansen', monitoringsysteem); de sterkste zin ('bewustzijn van... het besta
- **RIVM** (82) — Het RIVM positioneert zich als onafhankelijk wetenschappelijk kennisinstituut met wettelijk verankerde onafhankelijkheid; missieteksten blijven binnen
- **Ron Fresen** (63) — Gezocht naar eigen uitspraken (interviews VARAgids/BNNVARA 2025, NOS-afscheidsstukken 2022). Fresen weigert in het VARAgids-interview expliciet een po
- **Royal HaskoningDHV** (127) — 'Enhancing Society Together' plus SDG-/ESG-commitments is klassieke CSR-taal die per instructie niet telt als ideologisch signaal. Geen politiek-norma
- **RTL Nederland** (8) — Commercieel mediabedrijf; het Journalistiek Charter en de redactiestatuten (rond de DPG-overname) borgen redactionele onafhankelijkheid — neutraliteit
- **RTL Nieuws** (88) — RTL Nieuws werkt onder een redactiestatuut dat onafhankelijkheid en onpartijdigheid borgt — een neutraliteitsclaim, geen pool-signaal. Geen citeerbare
- **Rutger Castricum** (209) — Zoek-snippets suggereerden zelfbeschrijvingen ('anarchistisch', 'Ik pak net zo lief de liberalen aan; mijn politieke voorkeur houd ik buiten mijn werk
- **RVS (Raad voor Volksgezondheid en Samenleving)** (166) — Strategisch en onafhankelijk adviesorgaan; missie en adviezen (agenderen, informeren, richting geven aan debat) vallen volledig binnen de wettelijke a
- **Sanoma Nederland (historisch)** (97) — Fins-commerciële tijdschriftenuitgever (Libelle, Margriet, Donald Duck). Missietaal ('informeren, inspireren en entertainen'; 'objectiviteit en onafha
- **Sarah Bakker** (207) — Zoeken op de naam levert vrijwel uitsluitend de PowNed-journalist/presentator Sarah Bakker op, die niet overtuigend matcht met de entiteitsomschrijvin
- **Snapchat** (160) — Spiegels uitspraken (steun voor 'thoughtful regulation', niet-promoten van Trump-content in 2020) zijn incidentele moderatiebesluiten en compliance-ta
- **Spot On Stories** (262) — De eigen site was onbereikbaar (verbinding geweigerd), dus geen enkel citaat kon fetch-geverifieerd worden. Uit zoekresultaten (SVDJ-projectpagina, ni
- **Ster (reclame-exploitant publieke omroep)** (133) — Eigen over-pagina geverifieerd: commerciële en infrastructurele taal (reclame-exploitatie, opbrengst voor de publieke omroep, bijdrage aan 'informeren
- **Stichting Administratiekantoor Epifin** (129) — Geen eigen website of missietekst; het is een STAK (administratiekantoor) die de aandelen/zeggenschap rond DPG Media administreert — een puur juridisc
- **Stichting DOEN** (318) — De eigen site doen.nl blokkeert elke fetch (403, ook via alternatieve paden) en het webarchief was onbereikbaar, zodat geen citaat verbatim geverifiee
- **Stichting Het Nieuwe Parool** (231) — Geen eigen website of gepubliceerde missie-/statutentekst gevonden. SDM's geschiedenis-pagina noemt haar uitsluitend als 'de speciaal hiervoor opgeric
- **Stichting Jaarlijkse Literatuurprijs** (293) — Onafhankelijke stichting achter de Boekenbon Literatuurprijs (eerder BookSpot/ECI/AKO). Doelstelling is literatuurbevordering en leescultuur — geen po
- **Stichting Nederlandse Lokale Publieke Omroepen** (285) — Sector- en coördinatieorgaan voor lokale publieke omroepen; missie is 'versterken van de lokale democratie via een onafhankelijk, professioneel en maa
- **Stichting NU.nl** (232) — In 2025 opgerichte beschermstichting (ACM-voorwaarde bij de RTL-overname). Kerntaak is het bewaken van redactionele vrijheid, identiteit en vrije toeg
- **Stichting Persvrijheidsfonds** (267) — Fonds (2007, NVJ + Genootschap van Hoofdredacteuren) dat principiële rechtszaken voor de journalistieke beroepsgroep financiert en persvrijheid monito
- **Stichting RTL Nieuws** (235) — In 2025 opgerichte beschermstichting (ACM-voorwaarde bij de RTL-overname door DPG). Doelstelling is bescherming van redactionele vrijheid, identiteit 
- **Stimuleringsfonds voor de Journalistiek (SVDJ)** (253) — Missie (onafhankelijke, pluriforme, toekomstbestendige journalistiek voor een goed functionerende democratie) is de letterlijke Mediawet-taak van dit 
- **Sue & The Alchemists (pr-bureau)** (216) — Opgericht door o.a. VVD-strategen Klaas Dijkhoff en Bas Erlings — maar een oprichtersbiografie is een structureel feit, geen ideologische uiting van h
- **Talpa Network** (31) — Talpa's missiepagina ('we laten verhalen reizen, dwars door Nederland'; ondernemerschap, creativiteit, 'authentieke Nederlandse verhalen') is commerci
- **Thomas Leysen (Mediahuis-voorzitter)** (15) — Leysen heeft een publiek profiel als 'groene industrieel' (duurzaam kapitalisme, debat met degrowth-econoom Hickel), maar de fetchbare eigen uitsprake
- **TikTok** (42) — TikTok positioneert zich expliciet apolitiek (verbod op politieke advertenties sinds 2019, ontmoedigt politieke content); zelfverklaarde neutraliteit 
- **TMG (Telegraaf Media Groep)** (99) — TMG's gepubliceerde missie is commercieel ('consumenten 24/7 voorzien van hoogwaardige en relevante content op het gebied van nieuws, sport en enterta
- **Tweede Kamer** (107) — Het instituut zelf (volksvertegenwoordiging, wetgeving, controle op de regering) is per definitie de arena waarin ideologieën strijden, niet een drage
- **Umicore** (74) — Umicore's zelfpresentatie (transformatie naar materiaaltechnologie/'groene economie', duurzaamheidsverslagen) is CSR-taal; het persoonlijke milieu-eng
- **Unibet** (72) — Gevonden: vergunningsgeschiedenis, massaclaims en illegaal aanbod vóór 2021, maar geen citeerbare publieke politiek-normatieve stellingname van Unibet
- **Use The News** (287) — Onafhankelijke non-profitstichting (ANBI) voor nieuwswijsheid onder jongeren; werkt met journalisten, scholen en wetenschappers tegen desinformatie en
- **UvA Journalistiek (opleiding)** (104) — De duale master Journalistiek en media profileert zich op journalistieke vakbekwaamheid, wetenschappelijke reflectie en kwaliteitsjournalistiek — een 
- **Vanguard** (30) — Vanguard framet zijn stembeleid expliciet als politiek neutraal ('voting on enterprise value... not ideology') en trok zich onder juridische druk teru
- **VNU Media (historisch)** (98) — VNU ontstond in 1964/65 uit de katholieke uitgeverijen Cebema en De Spaarnestad — een structureel-historisch feit, beschreven door derden. Geen citeer
- **VP Exploitatie (Van Puijenbroek-holding)** (27) — Investeringsvehikel van de familie Van Puijenbroek. De VP Capital-site spreekt van 'positive change for planet and society' — CSR-/marketingtaal, per 
- **VPRO** (142) — Alleen de economische as onderzocht (cultureel/establishment al gedekt). De missie draait om vrijzinnigheid, eigenzinnigheid en creatieve kwaliteit; d
- **Wegener** (282) — Wegener was een concern van regionale dagbladen die als lokale informatievoorziening functioneerden, zonder gedocumenteerde uitgesproken politieke sig
- **WHO (Wereldgezondheidsorganisatie)** (165) — De normatieve lading ('health for all', gezondheid als fundamenteel mensenrecht, equity) staat in de WHO-constitutie van 1948 — dat is het oprichtings
- **Wiardi Beckman Stichting** (47) — Alleen de assen cultureel en establishment onderzocht (economisch al gedekt). De eigen over-pagina beschrijft de WBS uitsluitend als 'het wetenschappe
- **WRR (Wetenschappelijke Raad voor het Regeringsbeleid)** (49) — Onafhankelijk wetenschappelijk adviesorgaan; rapporten en missie ('onafhankelijk, multidisciplinair, sectoroverstijgend') blijven binnen de wettelijke
- **Yael de Haan** (271) — Interviews en oratie (Spreekbuis, Trajectum, SvJ) bevatten vakwetenschappelijke uitspraken over lokale journalistiek, transparantie en sociale cohesie
- **Yvonne Zonderop** (275) — Alleen assen economisch en establishment onderzocht (cultureel al gedekt). Vrijwel al het vindbare materiaal betreft haar cultuurchristelijke religie-

## Noten voor de reviewer
- Alle signalen staan `voorgesteld` en tellen in niets tot een mens ze merget (ik stel voor, jij beslist).
- Zwakkere bronnen (reliability-voorstel `grijs`/`opinie`, o.a. Wikipedia-afgeleide signalen bij Het Parool, De Morgen, IKON, LOSON) zijn als zodanig gemarkeerd — kandidaten om bij review te laten vallen of met een primaire bron te vervangen.
- Enkele bronnen zijn alleen via Wayback verifieerbaar (VNO-NCW, WEF, HCSS, ERT, TNI, EBU) omdat de live pagina achter Cloudflare/JS zit — overweeg een `archive_url` toe te voegen.
- Entiteitsbeschrijvingen die niet kloppen met de werkelijkheid: **Krispijnpunt (219)** en **Voor Ons Nederland (217)** (is de Dijkhoff/Erlings-actiegroep, niet ON-gerelateerd) — scout-werk, geen ideologie-werk.