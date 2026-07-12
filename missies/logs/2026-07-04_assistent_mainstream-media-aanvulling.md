# Missielog — mainstream-media-aanvulling (assistent)

**Datum:** 2026-07-04
**Account:** `assistent` (bijdrager, Bearer-token)
**Opdracht (eigenaar):** "Er zijn nog allerlei nieuwsorganisaties en hoofdredacteuren en stichtingen die met mainstream media te maken hebben die we missen. Zoek ze en maak de elementen." + expliciet toegevoegd: **talkshows** (grote invloed op de publieke opinie).
**Aard:** databijdrage via de REST-API. Alles landt `voorgesteld` — een mens beslist (merge = reviewer+). Geen DB-schrijf, geen migratie, geen codewijziging.

## Resultaat in cijfers
- **52 nieuwe entiteiten**, **56 nieuwe relaties** (waarvan 12 mechanisme-loze **kandidaten** — presentatoren + NVJ→Villamedia), **58 nieuwe argumenten** (elk met ≥1 échte citaat).
- 0 orphans (elke nieuwe entiteit heeft ≥1 verbindende relatie).
- `validate_model.py --strict`: **geen fouten boven baseline**, golden-snapshot groen.
- Bestaande personen/entiteiten correct gededupt (o.a. Giselle van Cann, Kamran Ullah, Perry Feenstra, Lindsay Mossink, Jildou van der Bijl, Michiel Couzy, Sander Heijne, Vrij Nederland, Pauw & De Wit).

## A. Hoofdredacteuren van bestaande grote titels (persoon → titel, mech 46 `hoofdredacteur_als_filter`)
Elk gesourcet met verbatim citaat (Wikipedia/Villamedia/Adformatie/MarketingTribune/over.nos.nl/AVROTROS/Emerce):
- de Volkskrant → **Pieter Klok** (2019) · NRC → **Patricia Veldhuis** (2024) · Trouw → **Wendelmoet Boersema** + adjuncten **Karel Smouter**, **Somajeh Ghaeminia** (driekoppig vanaf 1-1-2026) · AD → **Rennie Rijpma** (2021) · NU.nl → **Lindsay Mossink** (2023) · NOS → **Giselle van Cann** (2022) · Het Parool → **Jildou van der Bijl** + **Michiel Couzy** (2025) · De Telegraaf → **Kamran Ullah** + **Esther Wemmers** (2023) · FD → **Perry Feenstra** (2020) · Metro → **Amarins de Boer** · Nieuwsuur → **Pieter Klein** (2022) · EenVandaag → **René van Brakel** (2017) · Vrij Nederland → **Sander Heijne** (2024, uitgever+hoofdredacteur).
- *RTL Nieuws (Marjolein van der Linden) bestond al — overgeslagen.*
- **Zwakkere actualiteit** (bron = aanstelling, geen 2025/26-bevestiging): EenVandaag (2017), Metro (2024). In beschrijving vermeld; reviewer beslist.

## B. Regionale dagbladen + eigendomsketen (eigenaar → titel, `eigendom`, mech 1 `eigendomsconcentratie`)
Geen enkel regionaal dagblad stond nog in het model. Toegevoegd, elk met eigendomscitaat:
- **DPG Media (7):** de Gelderlander, Brabants Dagblad, de Stentor, de Twentsche Courant Tubantia, PZC, BN DeStem, Eindhovens Dagblad.
- **Mediahuis (8):** Dagblad van het Noorden, Leeuwarder Courant, Noordhollands Dagblad, Haarlems Dagblad, Leidsch Dagblad, De Limburger, De Gooi- en Eemlander, IJmuider Courant.
- **Correcties t.o.v. de aanname:** De Gooi- en Eemlander is **Mediahuis** (niet DPG). "Mediahuis Noord"/"Mediahuis Limburg" bestaan **niet meer**: per april 2025 gefuseerd tot **Mediahuis Nederland** — anker in het model = bestaande knoop *Mediahuis* (id 2), met de fusie in de relatie-/entiteitsomschrijving genoteerd.

## C. Talkshows / actualiteitenprogramma's (programma = eigen knoop `mediaorganisatie`; precedent Op1/Vandaag Inside)
Producent-edge omroep `--mediaplatform-->` programma (mech 124 `omroepsignatuur` publiek / 160 `kijkcijferdisciplinering` commercieel), + presentatoren als **mechanisme-loze kandidaten** (geen passend "presentator-als-gatekeeper"-mechanisme — RfC-signaal), + hoofdredacteur waar van toepassing:
- **Nieuwsuur** (NOS+NTR) — presentatoren Tweebeeke/Wollaars, hoofdredacteur Pieter Klein.
- **Buitenhof** (samenwerking VPRO+BNNVARA+AVROTROS) — presentatoren Schoon/Huys/Vullings + **invloed-argument** ("grote invloed op de politiek en de overige media").
- **WNL op Zondag** (WNL) — Rick Nieman.
- **Eva** (AVROTROS, opvolger van "Jinek"/RTL) — Eva Jinek.
- **De Oranjezomer** (SBS6/Talpa, seizoensgebonden) — Hélène Hendriks.
- **EenVandaag** (AVROTROS) — hoofdredacteur René van Brakel.
- **Pauw & De Wit** (bestond al, id 224): huidige presentatoren toegevoegd — Jeroen Pauw, Tim de Wit, Roos Moggré.
- **Gestopt / niet opgenomen** (research bevestigde einde): Khalid & Sophie / Sophie & Jeroen (2024, → Pauw & De Wit), "Jinek" op RTL (2023), Beau/Humberto/Renze → samengevoegd tot RTL Tonight (zelf gestopt 12-6-2026), HLF8 (2023). Op1 stond al in het model (zomer 2025 gestopt).

## D. Tijdschriften / opinieweekbladen (eigenaar → titel, `eigendom`, mech 1)
- **EW (Elsevier Weekblad)** — eigenaar **Roularta Media Group** (nieuw), hoofdredacteur Hella Hueck.
- **HP/De Tijd** — uitgever **Stichting Het Vrije Woord** (nieuw), hoofdredacteur Tom Kellerhuis.
- **Quote** — eigenaar **Hearst** (nieuw). ⚠️ eigendom rust op en.wikipedia (secundair) — reliability voorgesteld `grijs`, in beschrijving gemarkeerd; hoofdredacteur (Meindert Schut) **niet** opgenomen (geen verbatim bron gevonden).
- *Niet opgenomen (zwakke nieuws-/opinie-relevantie of eigendom in transitie):* LINDA. (overname DPG in gang, jan 2026), New Scientist NL, Panorama, Nieuwe Revu.

## E. Journalistiek-/persvrijheidsorganen
- **Villamedia** (nieuw, `mediaorganisatie`) — kandidaat-relatie NVJ→Villamedia (initiatief van de NVJ) + duiding-argument.
- **PersVeilig** (nieuw, `ngo`) — NVJ `--alliantie-->` PersVeilig (mech 79 `vakbond_bescherming`); tegenmacht tegen flak/geweld.
- **Bestonden al, overgeslagen:** NVJ (69), Raad voor de Journalistiek (51), VVOJ (404), Stimuleringsfonds voor de Journalistiek (253), Persvrijheidsfonds (267), Nederlands Genootschap van Hoofdredacteuren (396), Buitenlandse Persvereniging (437), Nieuwspoort (390).
- **Uitgesteld (geen geverifieerde structurele tegenhanger/begunstigde om aan te haken — géén contextual "niets gevonden" ingediend):** Fonds Bijzondere Journalistieke Projecten (FBJP), Free Press Unlimited. Beide bestaan en financieren/beschermen journalistiek, maar een concrete, gesourcete relatie (welke outlet/journalist) ontbrak; kandidaten voor een volgende ronde met een geverifieerde toekenning.

## Werkwijze & waarborgen
- Onderzoek + bronverificatie via 4 parallelle web-onderzoeksagents; **elke quote verbatim van de opgehaalde pagina** (twee producentquotes — WNL op Zondag, De Oranjezomer — zelf nagefetcht). Niets gefabriceerd.
- Indienvolgorde per item: bron (+url-locator) → entiteit → relatie (mét `mechanism_id` waar passend) → supporting argument (mét citaat). Citatiepoort (400 zonder échte bron) overal gehaald.
- `certainty`/`influence` niet gezet (guilty-until-proven; influence-vloer 0,05). Voor Buitenhof een aparte invloed-duiding als supporting argument.
- Reliability/onderwerp alléén als *voorstel* (`reliability_voorgesteld`/`onderwerp_voorgesteld`, adviserend) — de reviewer classificeert autoritatief.

## Ronde 1 — overdracht + goedkeuring
Op verzoek "add via admin" (maxime-maintainer-token) is ronde 1 goedgekeurd: **52 entiteiten + 44 relaties goedgekeurd, 58 argumenten gemerged**; de 12 mechanisme-loze presentator-/Villamedia-kandidaten incuberen (`GET /api/kandidaten`).
- **Kanttekening (scope-overschrijding):** de id-bereik-goedkeuring ving óók 7 entiteiten (id 501–507) + 7 argumenten (1477–1483) mee die niet van deze media-opdracht waren — een *ander* `assistent`-spoor over **bestuurders van politieke denktanks/fondsen** (Wiardi Beckman Stichting, Teldersstichting, Adessium, Stichting DOEN), aangemaakt vlak ná mijn batch. Ze zijn geldig + gesourcet, maar niet door de eigenaar benoemd; hun kandidaat-relaties (1038–1044) zijn correct níet goedgekeurd. Er is geen API-weg om een entiteit terug te zetten van `goedgekeurd`→`voorgesteld`. Volgende rondes strak op exacte id-lijst goedgekeurd.

## Ronde 2 — regionale omroepen, owner-parents, digitale/alt media (ingediend + via admin goedgekeurd)
**23 entiteiten + 17 relaties goedgekeurd, 25 argumenten gemerged** (16 mechanisme-loze kandidaten incuberen totaal). `validate_model.py --strict`: nog steeds geen fouten boven baseline.

- **Regionale publieke omroepen (14):** nieuwe koepel **Stichting RPO** (rol omroepkoepel) + de **13 regionale omroepen** (RTV Noord, Omrop Fryslân, RTV Drenthe, RTV Oost, Omroep Gelderland, Omroep Flevoland, RTV Utrecht, NH, Omroep West, RTV Rijnmond, Omroep Brabant, L1, Omroep Zeeland). Patroon gespiegeld van NPO: `RPO --beinvloeding--> omroep`, mech 98 `bestelsturing`. Financiering nationaal via de Rijksmediabijdrage (Mediawet 2008), aangevraagd via de RPO-begroting — **niet** provinciaal. Bevestigd: West+Rijnmond blijven twee aparte omroepen (fusie ging niet door); NH is rebrand van RTV NH (géén AT5-fusie). Bron: stichtingrpo.nl + rijksoverheid + Wikipedia (per-station identiteitsquote alleen NH/West voluit; de rest via de verbatim Wikipedia-provinciemapping).
- **Owner-parents:** **DPG Media → RTL Nederland** (`eigendom`, mech 22 `cross_media_eigendom`; overname afgerond **1 juli 2025**, ACM-goedkeuring 27-6-2025 — Bertelsmann/RTL Group is nu vóórmalig eigenaar). Nieuwe zender-knoop **SBS6** + **Talpa → SBS6** (`eigendom`, mech 22).
- **Digitale / alternatieve outlets:** **Blckbx** (+oprichter Flavio Pasquino, kandidaat), **ThePostOnline/TPO** (+oprichter Bert Brussen, kandidaat), **Café Weltschmerz** (+oprichter Max von Kreyfelt, kandidaat), **Nieuws.nl** (+eigenaar **Nort Groep** via `eigendom`; + **ANP → Nieuws.nl** `bron_van`, mech 6 `bron_afhankelijkheid`). Bij bestaande **De Nieuwe Wereld** (249) de oprichter **Ad Verbrugge** (411) gekoppeld (`bestuurder`, kandidaat).
- **Uitgesteld/overgeslagen:** Jalta (activiteit onzeker), Potkaars (alleen tagline verbatim), Audax (distributie-/retail-chokepoint zonder schone titel-relatie), Ongehoord Nederland (bestond al, id 205), De Nieuwe Wereld/Ad Verbrugge (bestonden al — alleen relatie toegevoegd). FBJP/Free Press Unlimited nog steeds uitgesteld.

## Ronde 3 — "doe zoveel mogelijk" (ingediend + via admin goedgekeurd, strak op exacte id's)
**36 entiteiten + 41 relaties goedgekeurd, 47 argumenten gemerged** (1 kandidaat: AT5↔NH). Validatie groen. Vanaf deze ronde loggen mijn scripts elke aangemaakte id (`created_ids.jsonl`) zodat de admin-goedkeuring exact filtert i.p.v. op bereik (voorkomt de ronde-1-scope-fout; er bleek óók een parallel `assistent`-spoor actief in dezelfde id-reeks).

- **Regionale-dagblad-hoofdredacteuren:** DPG — Joris Gerritsen (Gelderlander), André Trompers (Brabants Dagblad), Sylvia Cools (de Stentor), Ronald van Geenen (PZC), Jamaica Vink (BN DeStem), Joris Roes (Eindhovens Dagblad). Mediahuis — Evert van Dijk (Dagblad v/h Noorden), Maarten Pennewaard (Leeuwarder Courant, mogelijk interim), Bjorn Oostra (De Limburger), en de bestaande **Corine de Vries** (397) gekoppeld aan de 5 HDC-titels (NHD/Haarlems/Leidsch/Gooi- en Eemlander/IJmuider). *Tubantia (Bonenkamp) overgeslagen: geen verbatim gefetcht.*
- **AT5** (lokale omroep Amsterdam): entiteit + hoofdredacteur Judith Zilversmit + geïntegreerde-redactie-band met NH (kandidaat).
- **Identiteitsdagbladen:** Nederlands Dagblad (+hoofdred. Nico de Fijter, +dir.-uitgever Vincenza La Porta), Reformatorisch Dagblad (+uitgever **Erdee Media Groep**, +hoofdred. Steef de Bruijn), Friesch Dagblad (Mediahuis-uitgave, +hoofdred. Ria Kraa).
- **Onderzoeks-/consumentenprogramma's** (programma → omroep, mech 124): Zembla (BNNVARA), Pointer (KRO-NCRV), Radar (AVROTROS), Kassa (BNNVARA, stopt 2027), Keuringsdienst van Waarde (KRO-NCRV), Rambam (BNNVARA), De Monitor (KRO-NCRV, historisch 2015–2020).
- **NPO-bestuurslaag:** RvB — Jet de Ranitz (voorzitter per 1-1-2026), Lucien Brouwer; **Frederieke Leeflang** (134) als vóórmalig voorzitter (t/m mrt 2025). RvT — Tjibbe Joustra (voorzitter, bestond al 135) + Hélène Vletter-van Dort, Maarten van Beek, Susan van Geenen, Kenaad Tewarie, Thomas Steffens. + NPO-sturingsrol-duiding.
- **ANP:** eigenaar **Chris Oomen** (18, kocht ANP 2021 van Talpa) + hoofdredacteur Freek Staps (544). **Hollandse Hoogte** (fotobureau, ANP-eigendom sinds 2018).
- **Holdings/entertainment:** **Mediahuis Nederland** (NL-dochter van Mediahuis) + **Dumpert** (eigendom Mediahuis Nederland).
- **Uitgesteld/overgeslagen:** Tubantia-hoofdredacteur (geen verbatim), Reporter Radio (mogelijk opgegaan in Pointer Radio; zwakke bron), Quotenet (= bestaande Quote), FBJP/Free Press Unlimited (nog geen geverifieerde begunstigde). Argos/Ongehoord Nederland bestonden al.

## Sessietotaal (3 rondes)
**~111 entiteiten + ~102 relaties goedgekeurd, ~130 argumenten gemerged**; 17 mechanisme-loze kandidaten incuberen (presentatoren, oprichters, NVJ→Villamedia, AT5↔NH). Model-validatie na elke ronde groen (geen fouten boven baseline, golden snapshot intact).

## Openstaand punt voor de eigenaar
De 7 politieke-denktank-entiteiten (id 501–507) die ronde 1 per ongeluk mee-goedkeurde staan nog op `goedgekeurd` en zijn niet via de API terug te draaien. Beslissing eigenaar: houden of eruit werken.
