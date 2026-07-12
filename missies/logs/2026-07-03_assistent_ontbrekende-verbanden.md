# Missielog: ontbrekende verbanden — rondes 1 & 2 (Tier A)

**Datum:** 2026-07-03 · **Account:** `assistent` (bijdrager) · **Missie:** systematische sweep over alle entiteiten om gedocumenteerde maar ontbrekende verbanden te vinden (plan: `we-missen-nog-heel-ethereal-wolf`).

Uitgangssituatie: 321 goedgekeurde entiteiten, 604 goedgekeurde relaties; ~130 entiteiten met 0–1 verbanden. Alle onderstaande inzendingen landden als `voorgesteld`; quotes zijn vóór indiening verbatim geverifieerd via WebFetch.

## Ronde 1 — programma-platform + holdings + FTM-tegenmacht (11 relaties)

| Rel | Verband | Mechanisme | Bron |
|---|---|---|---|
| 702 | VPRO → Argos (eigendom, 1992–) | omroepsignatuur | argos.vpro.nl |
| 706 | Talpa Network → Vandaag Inside (eigendom, 2022–) | eigendomsconcentratie | Wikipedia |
| 707 | NPO → Op1 (beïnvloeding, 2020–2024) | intekensturing | NPO-persbericht 23-12-2019 |
| 708 | KRO-NCRV → Brandpunt (eigendom, 2015–2018) | omroepsignatuur | Wikipedia |
| 709 | BNNVARA → Pauw & De Wit (eigendom, 2025–) | omroepsignatuur | bnnvara.nl + Wikipedia — **gecorrigeerde richting van afgewezen rel. 518** (eigenaar→bezit-conventie) |
| 710 | DPG Media → Wegener (eigendom, 2015–) | acquisitiestrategie | Omroep Brabant (ACM-goedkeuring 11-2-2015); formeel via moederbedrijf Mecom |
| 711 | PCM Uitgevers → NRC (eigendom, 1995–2010) | eigendomsconcentratie | Wikipedia (NDU-overname 1995; verkoop Egeria/Het Gesprek maart 2010) |
| 712 | TMG → Metro (eigendom, 2012–2017) | eigendomsconcentratie | Wikipedia |
| 713 | John de Mol → TMG (investering, jan–dec 2017) | acquisitiestrategie | Wikipedia + MarketingTribune (mislukte overnamestrijd, belang ~30%, verkocht aan Mediahuis 1-12-2017) |
| 714 | FTM → ING (oppositie, 2018) | onderzoeksjournalist_doorbraak | FTM 1-11-2018 (balanscorrectie 185 mld → Kamervragen Omtzigt/Ronnes) |
| 715 | FTM → Belastingdienst (oppositie, 2023) | onderzoeksjournalist_doorbraak | Kamerstuk 2023D50518 (Kamer vraagt kabinetsreactie op FTM-artikel bij naam) |

Argumenten 947–957; bronnen 314, 319–331.

## Ronde 2 — persbureau-structuur + borging + fondsen (4 entiteiten, 8 relaties, 1 extra argument)

Nieuwe entiteiten (alle `voorgesteld`, met rol-suggestie): **Novum Nieuws** (337, persbureau, tot 2015), **NCDO** (338, stichting/uitgever OneWorld tot 2018), **Stichting Groene Beheer** (339, borgingsstichting), **Pluralis B.V.** (340, vermogensbeheerder, Amsterdam 2021).

| Rel | Verband | Mechanisme | Bron |
|---|---|---|---|
| arg 958 | AFP → ANP (bestaande rel. 425): exclusiviteits­argument — exclusief contract AFP-foto's + sinds 2018 AFP-video | — | Villamedia 5-1-2018 |
| 716 | AP → Novum (bron_van, 2007–2015) | pakketjournalistiek | Wikipedia Novum (agent AP; NL-redactie-overname) |
| 717 | ANP → Novum (eigendom, 2015–) | acquisitiestrategie | Villamedia 18-9-2014 ("de enige concurrent") |
| 718 | AP → ANP (bron_van, 2015–) | pakketjournalistiek | anp.nl (beeldpartner) + Villamedia; kanttekening in beschrijving: actueel tekstcontract niet aangetoond |
| 719 | NCDO → OneWorld (eigendom, tot 2018) | eigendomsconcentratie | Wikipedia OneWorld |
| 720 | BuZa → NCDO (financiering, tot 2017) | externe_mediafinanciering | Wikipedia OneWorld |
| 721 | Stichting Groene Beheer → De Groene Amsterdammer (eigendom) | onafhankelijkheidsborging | groene.nl (vacature 2014 + /over) |
| 722 | MDIF → Pluralis (adviseur/beheer) | **kandidaat** (geen passend mechanisme; fondsbeheer) | pluralis.media + MDIF-persbericht |
| 723 | Mediahuis → Pluralis (investering) | **kandidaat** | MDIF-persbericht 1-2-2024 (aandeelhouderslijst) |

Argumenten 958–966; bronnen 332–340.

## Negatieve resultaten & correcties op agent-vondsten

- **AP→krant-edges (Volkskrant, NRC, Telegraaf e.a., 2007–2015) NIET ingediend.** De research-agent las het TNO/OCW-rapport (2011, p. 27) als "deze titels hadden AP-abonnementen", maar de volledige context zegt: de titellijst betreft Novum-basisdienst-klanten en slechts voor "enkele van deze klanten" was Novum "louter agent voor het abonnement op de Engelstalige dienst van AP". Per titel is een AP-abonnement dus niet te staven.
- **Actuele rechtstreekse Reuters/AP/AFP-abonnementen van RTL, Volkskrant, NRC, Telegraaf, FD:** geen bron gevonden (colofons geblokkeerd/paywalled; artikel-bronvermelding bewijst geen abonnement). Niet ingediend.
- **Reuters/AFP → Trouw (2001, rechtstreekse telexen):** enkel één tijdschriftbron (Filter, 2001) over de werkvloer; te dun en te gedateerd voor een edge — alleen hier gelogd.
- **MDIF:** geen eigen NL-kantoor of NL-bestuurslid; NL-aanwezigheid loopt via Pluralis B.V. (wel ingediend).
- **Mislukt Talpa-bod op TMG:** bewust als *gedateerde investering* (belang ~30%, jan–dec 2017) gemodelleerd, niet als eigendom.

## Vlaggen voor de beheerder

- **De Persgroep (entiteit 108, 0 relaties) is een duplicaat van DPG Media (1)** — oude naam. Samenvoegen (M2.6-voorstel) of verwijderen; er geen edges aan toevoegen.
- Rel. 518 (Pauw & De Wit → BNNVARA, afgewezen wegens omgekeerde richting) is vervangen door rel. 709 in de juiste richting; 518 kan hard-deleted worden.
- Validator na ronde 1+2: **0 fouten** (`validate_model.py --json`).

## Volgende stappen

Tier A-rest: funding-stichtingen (Adessium, Stichting DOEN, OSF, Postcode Loterij), Vrij Nederland/WPG-eigendom, IKON→EO, NMO-eigenaren. Daarna Tier B (bestuurders-nevenfuncties, mediapersonen), Tier C, Tier D.

---

## Ronde 3 — GeenStijl-cluster + mediapersonen (1 entiteit, 6 relaties)

Nieuwe entiteit: **GeenStijl** (342, mediaorganisatie, 2003–) — belangrijke ontbrekende knoop.

| Rel | Verband | Mechanisme | Bron |
|---|---|---|---|
| 728 | TMG → GeenStijl (eigendom, 2008–2017) | acquisitiestrategie | Wikipedia (40% 2006, 100% aug 2008) |
| 729 | Mediahuis → GeenStijl (eigendom, 2017–2018) | eigendomsconcentratie | NOS 24-6-2017 (eigenaar stoot af op redactioneel-ethisch criterium) + Wikipedia |
| 730 | Weesie → GeenStijl (bestuurder/oprichter, 2003–2009) | draaideurconstructie | Villamedia 27-5-2009 — **brug** naar bestaande Weesie→PowNed |
| 731 | Castricum → GeenStijl (personeel, 2006–2010) | draaideurconstructie | Wikipedia + eigen site — **brug** naar Castricum→PowNed |
| 732 | Wierd Duk → AD (personeel, 2016–2017) | draaideurconstructie | Wikipedia — **brug** naar Duk→De Telegraaf |
| 733 | Talitha Muusse → Op1 (personeel/presentatie namens KRO-NCRV, 2021) | draaideurconstructie | Wikipedia |

Argumenten 971–976; bronnen 344–349. De GeenStijl↔PowNed-band verschijnt vanzelf als brug via Weesie + Castricum (geen org→org draaideur-edge — conform de modelleerdiscipline).

## Ronde 4 — systemisch eigenaarschap techplatforms (7 relaties)

BlackRock/Vanguard waren al mede-eigenaar van de industriëlen (Shell, ING, Philips…); deze ronde sluit dezelfde indexbelegger-lus rond de platforms in het model. Percentages als momentopname geframed; bronnen zijn financiële aggregators (klasse-voorstel `grijs`, onderwerp `buitenlands`).

| Rel | Verband (~aandeel, peildatum) | Mechanisme |
|---|---|---|
| 734 | BlackRock → Meta (~7,7%, sep-2025) | systemisch_eigenaarschap |
| 735 | Vanguard → Meta (~8,9%, sep-2025) | systemisch_eigenaarschap |
| 736 | BlackRock → Alphabet/Google (~6,55%, nov-2025) | systemisch_eigenaarschap |
| 737 | Vanguard → Alphabet/Google (~7,73%, nov-2025) | systemisch_eigenaarschap |
| 738 | BlackRock → Microsoft (~8,1%, mrt-2026) | systemisch_eigenaarschap |
| 739 | Vanguard → Microsoft (~9,6%, mrt-2026) | systemisch_eigenaarschap |
| 740 | Vanguard → Procter & Gamble (~9,6%, jan-2024) | systemisch_eigenaarschap |

Argumenten 977–983; bronnen 350–353.

## Extra negatieve resultaten / bewust niet ingediend (ronde 3-4)

- **GeenStijl → PowNed als org→org oprichtingsedge:** bewust NIET gedaan; via de twee persoon-bruggen (Weesie, Castricum) verschijnt de band vanzelf, conform de discipline (geen org→org-conclusie).
- **Bits of Freedom → EDRi (lidmaatschap):** geverifieerd (EDRi-ledenlijst) maar te perifeer voor het mediabias-model; alleen gelogd.
- **Karskens' overige oprichters van Ongehoord Nederland** (Berckmoes-Duindam ex-VVD, Niemöller, Van der Heyden) + Nieuwe Revu: entiteiten bestaan niet in het model; Berckmoes als politiek↔media-draaideur is interessant maar buiten scope van deze sweep — gelogd, niet ingediend.
- **Wierd Duk → Elsevier/EW:** Elsevier is geen entiteit in het model; niet ingediend.

## Ronde 5 — DPG-bestuur ↔ controlestructuur & McKinsey (Tier B, 4 relaties)

Kern van het Eigendom-filter: de DPG-bestuurders verbonden met de Van Thillo-controleholding en het elite-consultancynetwerk. Alleen edges naar organisaties die al in het model zitten.

| Rel | Verband | Mechanisme | Bron |
|---|---|---|---|
| 741 | Ludwig Criel → Epifin (voorzitter RvB, 2015–) | draaideurconstructie | Apache 21-10-2015 |
| 742 | Ludwig Criel → STAK Epifin (bestuurder, 2015–) | draaideurconstructie | Apache (stemzeggenschap-laag) |
| 743 | Christophe Convent → Epifin (bestuurder, 2015–) | draaideurconstructie | Apache (schoonbroer Van Thillo) |
| 744 | Ieko Sevinga → McKinsey (consultant, 1993–1998) | draaideurconstructie | Consultancy.nl |

Argumenten 984–987; bronnen 354–355.

### Bewust NIET ingediend (Tier B) + org-suggesties voor de beheerder

- **Annetje Ottow → ACM: NIET gedaan (mis-attributie vermeden).** Zij was géén ACM-bestuurslid maar collegelid van voorloper OPTA (2006–2013) + strateeg bij de OPTA/NMa/CA-fusie tot ACM. OPTA zit niet in het model; een Ottow→ACM-edge zou onjuist zijn. Haar DPG-commissariaat via SDM staat al (rel. 543).
- **Feitcorrecties op de opdracht-hypothesen:** Criel is géén "CFO De Persgroep" (wel bestuurder/voorzitter); Nijboer was fiscaal partner bij **PwC**, niet KPMG/EY; De Bethune–KBC-link niet gevonden.
- **Zwaarwegende ontbrekende organisaties (kandidaten voor een aparte scout-ronde, niet nu aangemaakt om thin-node-inflatie te vermijden):** PwC (Nijboer, 20+ jr partner), Allen & Overy (Burggraaf, 2000–2019 partner), Rabobank (Sevinga, groepsdirectie 2017–2021), Van Lanschot Kempen (Sevinga, RvB 2007–2015), Bank Degroof Petercam (Criel, 2015–2021), Universiteit Leiden & Utrecht (Ottows academisch-bestuurlijke as), Vattenfall/Nuon (Roddenhof, 2002–2012). Elk zou een DPG-bestuur↔elite-brug opleveren; besluit aan de eigenaar.
- **Ottow-SDM-voordracht** is dubbel gestaafd (managementscope + font-versleutelde NOS-PDF); niet als losse edge nodig want rel. 543 bestaat al.

## Ronde 6 — filantropische financiers & Vrij Nederland-structuur (Tier C, 1 entiteit, 9 relaties)

Nieuwe entiteit: **Stichting Weekbladpers** (343, borgingsstichting). Conventie: journalistiek-ontvanger → mechanisme 113; zuivere advocacy-NGO → kandidaat (zoals bestaande SDM-edges).

| Rel | Verband | Mechanisme | Bron |
|---|---|---|---|
| 745 | Postcode Loterij → Free Press Unlimited (financiering, ~€900k/jr, sinds 2011) | externe_mediafinanciering | postcodeloterij.nl |
| 746 | Postcode Loterij → PAX (donor, €3,2M/5jr, sinds 2011) | **kandidaat** | postcodeloterij.nl |
| 747 | Adessium → Investico (financiering) | externe_mediafinanciering | adessium.org (grantee) |
| 748 | Adessium → PILP (financiering, €225k-toezegging 2019) | **kandidaat** | NJCM/PILP-jaarrekening 2021 (PDF, lokaal geverifieerd) |
| 749 | OSF → Bits of Freedom (kernfinanciering, t/m 2024) | **kandidaat** | BoF-jaarverslag 2023 |
| 750 | OSF → PILP (2× $150k, 2019–2023) | **kandidaat** | NJCM/PILP-jaarrekening 2021 (PDF) |
| 751 | OSF → EDRi (financiering) | **kandidaat** | edri.org/funding |
| 752 | OSF → TNI (core grant $992.500, 2022/23) | **kandidaat** | TNI Annual Report 2022 (PDF, lokaal geverifieerd) |
| 753 | Stichting Weekbladpers → Vrij Nederland (eigendom) | onafhankelijkheidsborging | SVDJ |

Argumenten 988–996; bronnen 356–363.

## Ronde 7 — NMO-bestuur: wie de bereiksmeting bezit (Tier C, 7 relaties)

De gevestigde mediapartijen + adverteerders besturen samen de Stichting NMO — de kijk-/luister-/leescijfermeting die via `kijkcijferdisciplinering` alle redacties disciplineert. Eén gezaghebbende bron (MMA), 7 bestuurszetel-edges (kandidaten).

| Rel | Verband | Bron |
|---|---|---|
| 754–758 | NPO / Mediahuis / DPG Media / Talpa Network / RTL Nederland → NMO (bestuurder, mediazijde) | MMA 24-7-2023 |
| 759–760 | Unilever / A.S. Watson → NMO (bestuurder, adverteerderszijde) | MMA 24-7-2023 |

Argumenten 997–1003; bron 364. Alle als kandidaat (mede-governance van een branche-JV past bij geen bestaand mechanisme).

## Negatieve resultaten Tier C (bewust niet ingediend)

- **Adessium → FTM (indirect via stichting Muckraker):** geldstroom loopt via een niet-gemodelleerde tussenstichting; conform de discipline (geen afgeleide/indirecte edge als element) niet ingediend. FTM wordt "voor het grootste deel" door leden gefinancierd (FTM-verantwoording).
- **Stichting DOEN → OneWorld / Correspondent / Vers Beton / BoF / FPU:** geen harde financieringsbron; OneWorld-band lijkt betaald content-partnerschap (achter Cloudflare, geen quote); Vers Beton wordt door SVDJ + Fred Foundation gefinancierd (niet DOEN); BoF-doorstart 2009 door Internet4all (niet DOEN). Niet ingediend.
- **Adessium/DOEN → De Correspondent:** institutionele partij is SDM (10% aandeelhouder), niet deze fondsen. Niet ingediend.
- **OSF → FPU:** slechts €34.228 (2022), nul in 2023 — de-minimis, geen structurele financier. Niet ingediend.
- **IKON → EO:** nuance uit onderzoek — IKON hield 1-1-2016 op te bestaan en de EO nam "slechts enkele programmatitels" over (geen fusie). Te zwak voor een schone eigendoms-/opgaan-in-edge; alleen gelogd.

## EINDBALANS (rondes 1–7)

- **Ingediend deze missie (alles `voorgesteld`, wacht op menselijke review):** 7 nieuwe entiteiten (Novum Nieuws, NCDO, Stichting Groene Beheer, Pluralis B.V., GeenStijl, Stichting Weekbladpers, + EBU-edge losstaand), **55 relaties** (id ≥ 702), ~57 argumenten (id 947–1003, elk met ≥1 verbatim geverifieerde citatie), ~50 bronnen (id 314–364).
- **Relatiegraad:** `voorgesteld`-relaties van 46 → 101; entiteiten met **nul** relaties van 5 → **1** (alleen het duplicaat *De Persgroep* 108, dat bewust geen edges kreeg).
- **Validator:** 0 fouten boven baseline na elke ronde.
- **Kernwinst:** programma→omroep-laag compleet; holdings-eigendomsketen (Wegener/PCM/TMG/Metro/GeenStijl) gesloten; persbureau-concentratie (Novum→ANP) toegevoegd; systemisch eigenaarschap rond de techplatforms (BlackRock/Vanguard→Meta/Google/Microsoft) gesloten; DPG-bestuur gekoppeld aan de Van Thillo-controlestructuur; het filantropische financieringsweb rond de maatschappelijke/tegenmacht-organisaties in kaart; en de gedeelde NMO-meetstandaard als bezit van de gevestigde partijen.

### Openstaand voor de beheerder
- **De Persgroep (108)** samenvoegen met/omleiden naar DPG Media (1) — duplicaat, oude naam.
- **Rel. 518** (afgewezen Pauw & De Wit → BNNVARA) hard-deletebaar; vervangen door rel. 709.
- **Kandidaat-org's voor een aparte scout-ronde** (elite-interlock DPG-bestuur): PwC, Allen & Overy, Rabobank, Van Lanschot Kempen, Bank Degroof Petercam, Univ. Leiden/Utrecht, Vattenfall/Nuon.
- **Berckmoes-Duindam** (ex-VVD → ON-oprichter) als politiek↔media-draaideur, indien gewenst als persoon-entiteit.

## Ronde 8 — scout: elite-interlock DPG-bestuur ↔ financiële/consultancysector (5 entiteiten, 5 relaties)

Nieuwe org-entiteiten (rol 39 belanghebbende, zoals McKinsey/KPMG/EY): **PwC** (344), **Allen & Overy** (345), **Rabobank** (346), **Van Lanschot Kempen** (347), **Bank Degroof Petercam** (348). Elke edge is een gedateerde draaideur-brug die het DPG-bestuur aan de high-finance-/advocatuur-elite koppelt.

| Rel | Verband | Bron |
|---|---|---|
| 761 | Anita Nijboer → PwC (belastingpartner ~20 jr) | ECP-sprekerspagina (PwC bij naam; DPG-commissaris geverifieerd, niet de gelijknamige KvdL-jurist) |
| 762 | Jan Louis Burggraaf → Allen & Overy (partner 2000–2019) | janlouisburggraaf.nl |
| 763 | Ieko Sevinga → Rabobank (groepsdirectie 2017–2021) | Management Scope |
| 764 | Ieko Sevinga → Van Lanschot Kempen (RvB 2007–2015; eerder Kempen & Co) | Management Scope |
| 765 | Ludwig Criel → Bank Degroof Petercam (bestuurder 2015, voorzitter 2018–2021) | Wikipedia |

Argumenten 1066–1074; bronnen 416–427. Alle mechanisme 18 (draaideurconstructie). Validator: 0 fouten.

**Bruggen die hierdoor verschijnen:** PwC↔DPG, Allen & Overy↔DPG, Rabobank↔DPG, Van Lanschot Kempen↔DPG, Degroof Petercam↔DPG-top — de verankering van het DPG-bestuur in de financiële/juridische elite.

**Nog niet aangemaakt (bewust, lagere media-relevantie; gelogd voor eventuele latere ronde):** Universiteit Leiden/Utrecht (Ottows academisch-bestuurlijke as) en Vattenfall/Nuon (Roddenhof 2002–2012).

## Ronde 9 — scout: eigendomsketen achter Het Financieele Dagblad & BNR (3 entiteiten, 4 relaties)

Gat: FD (195) had géén eigenaar-edge; **BNR Nieuwsradio** (het enige commerciële nieuwsradiostation van NL) ontbrak volledig; en de holding **FD Mediagroep** + haar eigenaar **HAL** stonden niet in het model. Alle quotes zelf verbatim geverifieerd (niet alleen door de research-agent).

Nieuwe entiteiten: **HAL Investments** (349, rol 3 aandeelhouder — uitvoerende arm van HAL Trust, Bermuda/Euronext, familie Van der Vorm), **FD Mediagroep** (350, rol 1 mediaeigenaar), **BNR Nieuwsradio** (351, rol 2 mediaorganisatie).

| Rel | Verband | Mech | Bron (zelf verbatim gecheckt) |
|---|---|---|---|
| 766 | HAL Investments → FD Mediagroep (eigenaar ~99–100%, sinds 1997) | 1 eigendomsconcentratie | halinvestments.nl ("Shareholding 100%", "Investment since 1997") + Euromedia Ownership Monitor 2025 ("99% owned by Hal Investments … HAL Trust … Bermuda") |
| 767 | FD Mediagroep → Het Financieele Dagblad (eigendom) | 1 | fdmg.nl/over-ons (kernmerken) + Euromedia 2025 |
| 768 | FD Mediagroep → BNR Nieuwsradio (eigendom, sinds 2003) | 1 | fdmg.nl/over-ons + nl.wikipedia ("Sinds 2003 is BNR onderdeel van de FD Mediagroep") |
| 769 | ANP → BNR Nieuwsradio (pakketjournalistiek; gezamenlijke nachtbulletins sinds 2004) | 7 pakketjournalistiek | Villamedia 2004 ("ANP Multimedia en BNR … gezamenlijk nieuwsbulletins … nachtelijke uren") |

Argumenten 1191–1194; bronnen 523–527. Validator: `--strict` groen, geen fouten boven baseline; golden-snapshot groen.

**Bruggen/keten die hierdoor verschijnt:** HAL → FD Mediagroep → {FD, BNR} — dezelfde eigenaar (HAL) achter zowel de zakenkrant als het enige commerciële nieuwsradiostation; plus BNR's persbureau-afhankelijkheid van het ANP.

**Bewust weggelaten:** Reuters/Bloomberg → FD (fd.nl/auteur-pagina's bestaan, maar fd.nl zit achter een paywall/HTTP 402 — kon de byline niet zélf verbatim verifiëren, dus niet ingediend). Programma's (Nieuwsuur, EenVandaag, Buitenhof) niet als eigen knoop toegevoegd — granulariteits-litmus: geen mechanisme dat op programmaniveau grijpt.

### Bijgewerkte eindbalans (t/m ronde 9)
- **15 nieuwe entiteiten**, **64 relaties** (`voorgesteld`: 46 → 110), ~66 argumenten, ~60 bronnen — alles `voorgesteld`, 0 validatorfouten boven baseline.
