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
