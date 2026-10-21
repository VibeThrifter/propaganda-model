# Registers → model: het openbaar bestuur in het netwerk

Uitbreiding C (eigenaarsbesluit 2026-10-07, `VOORSTEL_besluitvorming-als-categorieen.md`): naast
de media komt de besluitvorming in hetzelfde netwerk. Het skelet daarvan (wie mag besluiten, wie
zit waar, wie heeft welk belang) staat in openbare registers. Deze map leest die registers in,
**zonder AI en zonder mens**, en een deterministische controle (`scripts/registercheck.py`) geeft
het onafhankelijke A1-oordeel.

```
 register (open data) ──(1: haal)──► bewaarde uitgave + sha256 ──(2: lees)──► records met een recordregel
   oo.py / tk.py                      data/registers/<bron>/        oo.lees / tk.lees   (de regel = het citaat)
                                                                         │
                                       (3: naar het model, REST onder `register-import`)
                                       naar_model.py / tk_naar_model.py  ▼
                                                     entiteiten + verbanden + één argument per verband
                                                                         │
                         (4: registercheck, account `registercheck`, stap 2b van de uurronde)
                                                                         ▼
                      record bestaat in de uitgave, sha256 klopt, regel = citaat, eindpunten horen erbij
                                         → 'klopt' → A7 (structuurpad) → goedkeuren (registerplafond)
```

## Bronnen

| Bron | Module | Uitgave | Wat erin komt |
|---|---|---|---|
| Register van overheidsorganisaties (`organisaties.overheid.nl/archive/exportOO.xml`, namespace 2.6.13) | `oo.py` → `naar_model.py` | `data/registers/oo/exportOO_<datum>.xml` | ministeries met directoraten-generaal, agentschappen, zbo's, adviescolleges, inspecties, Hoge Colleges, rechtspraak, gemeenten, provincies en waterschappen (`zeggenschap`, `adviseur`); bewindspersonen, SG's, DG's, burgemeesters, wethouders, CdK's en dijkgraven (`ambt` met de ambtstitel in `relations.functie`) en hun partij (`lidmaatschap`/`partijlijn`). Sinds 2026-10-13 ook gedeputeerden (`lokaal_bestuursmandaat`), gemeente- en provinciesecretarissen, de secretaris-directeur van een waterschap en het bestuur van zbo's, adviescolleges en gerechten (`ambtelijke_leiding`), en lokale partijen als eigen partijknoop (`oo.lokale_partij`: de plaats tussen haakjes tenzij de naam haar noemt en uniek is; niet 'Onafhankelijk', niet een afdeling of combinatie van een landelijke partij). Staatsraden wachten op een mechanisme (`STAATSRAAD_MECH`); gewone collegeleden en raadsleden niet. Contactgegevens van medewerkers worden nooit gelezen. |
| Tweede Kamer, open data (`gegevensmagazijn.tweedekamer.nl/OData/v4/2.0`) | `tk.py` → `tk_naar_model.py` | `data/registers/tk/tk_<datum>.json` | de zittende Kamerleden (`ambt`/`kamerzetel` met de Tweede Kamer, fractie als `lidmaatschap`/`partijlijn`; een fractie die geen landelijke partij is, zoals 'Groep Markuszower', als eigen partijknoop met `DatumActief`), hun vaste commissiezetels in de controlerende commissies (`ambt`/`kamerzetel` met '<commissie> (Tweede Kamer)', Van/TotEnMet; geen contactgroepen en delegaties), hun lopende nevenfuncties (`nevenfunctie_verstrengeling`), hun loopbaan (`draaideurconstructie`), reizen die een ander betaalde en geschenken (`geschenk`/`geschenk_en_gastvrijheid`, sinds 2023-11-22) |
| Europees Parlement, open data (`data.europarl.europa.eu/api/v2`) | `ep.py` → `ep_naar_model.py` | `data/registers/ep/ep_<datum>.json` | de zittende Nederlandse Europarlementariërs (`ambt`/`kamerzetel` met het Europees Parlement, externe id `ep_mep`; het parlement zelf heeft wikidata:Q8889) en hun nationale partij (`lidmaatschap`/`partijlijn`) |
| SER, "Wie zitten er in de SER?" (`ser.nl`, html) | `ser.py` → `ser_naar_model.py` | `data/registers/ser/ser_<datum>.html` | de werkgevers- en werknemersorganisaties met zetels (`lidmaatschap`/`polderoverleg` → SER, het aantal zetels als functie, rol `sociale_partner` erbij). Geen personen: de pagina noemt geen datum per persoon. Geen begin: `register_zonder_datum`. Nieuwe organisatie alleen met de hand getypeerd (`koppelingen.json`, `ser_organisaties`: de VCP). |
| Wikidata SPARQL (`query.wikidata.org`) | `wikidata.py` → `wikidata_namen.py` (droogloop), `naar_model.py` | `data/registers/wikidata/wikidata_<datum>.json` | geen feiten, alleen naam en QID: burgemeesters en wethouders (P39 met een ambt onder Q13423499/Q20748682, P1001 gemeente, P382 CBS-code). Een registernaam met alleen een achternaam koppelt bij precies één passende persoon (zelfde gemeente, functie, achternaam, ambt loopt); `wikidata_namen.py` meldt welke voorletternamen eenduidig een volledige naam krijgen; met `--indienen` hangt `register-import` de QID aan de knoop en met `--hernoemen` vraagt hij de naam aan via `POST /api/entities/<id>/registernaam` (zie hieronder). |
| CBS, "Gebieden in Nederland <jaar>" (`opendata.cbs.nl`, OData; 2026: tabel 86247NED) | `cbs.py` → `cbs_naar_model.py` | `data/registers/cbs/cbs_<datum>.json` (tabelinfo, kolommen en rijen van de API in één bestand) | per gemeente de provincie waarin ze ligt: `controle` van de provincie naar de gemeente, mechanisme `interbestuurlijk_toezicht` (Gedeputeerde Staten houden toezicht op de gemeenten in hun provincie; Gemeentewet). De gemeente koppelt via haar tooi-code (gm0225), of waar het register van overheidsorganisaties er geen heeft (de heringedeelde van 2018–2019) via de oo-id in `koppelingen.json` (`cbs_gemeenten`); de provincie via haar oo-id (`cbs.PROVINCIES`). Een provincie die het model nog niet had (Utrecht, Noord-Brabant) komt erbij zoals `naar_model.py` haar zou maken. Geen begin: `register_zonder_datum`. Zolang het mechanisme er niet is (RfC), plant de import niets. |
| Lobbyistenregister van de Tweede Kamer (pdf op `tweedekamer.nl/contact_en_bezoek/lobbyisten`) | `lobby.py` → `lobby_naar_model.py` | `data/registers/lobby/lobby_<bijgewerkt>.pdf` | elke organisatie met een vaste toegangspas, en de opdrachtgevers die al in het model staan (`lobbyt` → Tweede Kamer, `lobbytoegang`). De tabel wordt gelezen uit de woordposities (PyMuPDF); de lobbyisten zelf worden geen knoop. Werkgevers zonder rechtsvorm in de naam zijn met de hand getypeerd in `koppelingen.json` (`lobby_organisaties`). |
| Openbare agenda's van bewindspersonen (rijksoverheid.nl `/actueel/agenda/…-week-<n>`, via de sitemap; de achterstand aug. 2023 – juni 2026 eenmalig uit Open Lobby van de Open State Foundation) | `agenda.py` → `agenda_naar_model.py` | `data/registers/agenda/agenda_<datum>.json` (alleen nieuwe afspraken per uitgave; recordsleutel = datum + bewindspersoon + tekst) | gesprekken, ontvangsten en werkbezoeken met een organisatie die al in het model staat (geen overheid, partij, rechter, toezichthouder of medium): `lobbyt` → het ministerie van de bewindspersoon (`departementale_lobby`; koepels van mede-overheden `interbestuurlijk_overleg`) vanaf afspraken op 2 dagen, of een extra argument op een bestaand `lobbyt`-verband. Hooguit 5 nieuwe argumenten per verband per run. Rapport `analyse.md`: score = dagen × log2(lift), zodat wie iedereen spreekt (VNG, VNO-NCW) niet bovenaan staat. Wekelijks via `agent_schedule.py` (`agenda-sync`, standaard uit). |
| Nevenfunctieregister Rechtspraak, via Open Rechtspraak (openrechtspraak.nl, `/api/v1/person` + `/person/<id>`) | `rechtspraak.py` → `rechtspraak_naar_model.py` | `data/registers/rechtspraak/rechtspraak_<datum>.json` | zittende rechters (externe id `rechtspraak`); lopende nevenbetrekkingen bij organisaties in het model of opvallende nieuwe met rechtsvorm (`nevenfunctie_verstrengeling`), loopbaan buiten de rechtspraak (`draaideurconstructie`); een extra bron op bestaande verbanden. Ruisfilter en score (organisatiesoort × functie × bezoldiging × zeldzaamheid) in het script, `rapport_<datum>.json`. Wekelijks via `agent_schedule.py` (`rechtspraak-sync`, standaard uit). |
| Inspraak bij Kamercommissies (gegevensmagazijn Tweede Kamer, OData v4: `Activiteit` met de genodigden in `Agendapunt.Noot`, en `Zaak` soort 'Position paper') | `tk_inspraak.py` → `tk_inspraak_naar_model.py` | `data/registers/tk_inspraak/tk_inspraak_<datum>.json` | position papers, genodigden en tegenpartijen van rondetafelgesprekken, hoorzittingen, technische briefings, gesprekken en petities: een organisatie die al in het model staat → de voortouwcommissie (`lobbyt` via `lobbyist_naar_politicus`; adviescollege `adviseur` via `institutioneel_advies`, denktank via `denktank_naar_politiek`), vanaf 2 keer gehoord. Overheid, universiteiten, media en privépersonen niet; deskundigen op eigen titel horen bij de persoonsroute (`namens_id`). Rapport `analyse.md`: score = keren × log2(lift). |
| Benoemingen in de Staatscourant (SRU-API `repository.overheid.nl/sru`, type 'benoeming of ontslag' sinds 2023) | `staatscourant.py` → `staatscourant_naar_model.py` | `data/registers/staatscourant/staatscourant_<datum>.json` | benoemingen, herbenoemingen en ontslagen bij Kroon of minister: `ambt` (`ambtelijke_leiding`/`kroonbenoeming`) of `bestuurder` (`commissarisbenoeming`) met begin en eind uit het besluit; een extra bron op bestaande verbanden. Tucht-, klacht- en examencommissies zijn ruis; woonplaats en geboortedatum worden uit het citaat gehaald; naamgenoten via `koppelingen.json` (`staatscourant_personen`). Rapport `analyse.md`. |
| Giften aan politieke partijen (Wfpp, BZK-overzichten als ods op rijksoverheid.nl; wat alleen op open.overheid.nl staat, downloadt een mens en neemt `giften.py voeg-toe` op, want robots.txt weert daar elke bot behalve Googlebot) | `giften.py` → `giften_naar_model.py` | `data/registers/giften/giften_<reeks>_<versie>.ods` (+ `.json` met vindplaats) | organisatie → partij (`donor`, `partijfinanciering`) met bedragen per jaar en de eerste en laatste gift; extra bron op bestaande donorverbanden; natuurlijke personen alleen als ze al met een donorverband naar dezelfde partij in het model staan; persoonlijke vennootschappen en afdrachten niet; adres, woonplaats en UBO nooit in een record. Rapport `rapport_<datum>.json`/`rapport.md`. Wekelijks via `agent_schedule.py` (`giften-sync`, standaard uit). |
| Netwerk van Nederlandse Europarlementariërs (EP Open Data `data.europarl.europa.eu/api/v2`: leden, commissies, verklaringen over belangenconflicten; europarl.europa.eu: belangenopgaven (DPI), deelnameverklaringen (DoP) en de vergaderingen-CSV; XML-export van het EU-transparantieregister; robots.txt per host, Crawl-delay 2) | `ep_netwerk.py` → `ep_netwerk_naar_model.py` | `data/registers/ep_netwerk/ep_netwerk_<datum>.json` | commissiezetels (`ambt`); lobbyvergaderingen op ≥2 dagen (`lobbyt`, `lobbyist_naar_politicus`/`denktank_naar_politiek`; score = dagen × log2(lift) × rapporteursgewicht); lopende en eerdere functies (`nevenfunctie_verstrengeling`, `draaideurconstructie`); betaalde deelnames (`geschenk_en_gastvrijheid`). Koppeling van het lid via `ep_mep`. Assistenten, contactgegevens en DPI-rubrieken F/G nooit. Parltrack niet: robots.txt weert ClaudeBot. Rapport `rapport_<datum>.json`/`.md`. |
| AFM-meldingenregisters: substantiële deelnemingen, bestuurders/commissarissen (art. 5:48 Wft), transacties leidinggevenden (MAR art. 19) (`afm.nl/export.aspx?type=<guid>&format=xml`; robots.txt staat het toe; bronvermelding verplicht) | `afm.py` → `afm_naar_model.py` | `data/registers/afm/afm_<datum>.json` (sleutels `sd:`/`bc:`/`mar:<meldingid>`; nauw gelieerden niet bewaard) | bij een onderneming in het model: `eigendom` houder → onderneming (`strategische_zeggenschap` bij ≥ 20% reëel stemrecht of ≥ 5% bij ≤ 5 belangen, `certificaatconstructie` voor een administratiekantoor, anders `systemisch_eigenaarschap`; begin = eerste melding boven de drempel, einde = melding eronder; kapitaal zonder stemrecht alleen in het rapport); `bestuurder` persoon — onderneming (`directiebenoeming`/`commissarisbenoeming`) bij een MAR-functie in bestuur of toezicht; extra argumenten (max. 3) op bestaande verbanden. Rapport `analyse.md`: score = reëel belang × log2(instellingen ÷ breedte). Wekelijks via `agent_schedule.py` (`afm-sync`, standaard uit). |

Nog te doen (plan fase 3f): subsidies (de download van Rijksfinanciën geeft nu 404);
gemeenschappelijke regelingen (veiligheidsregio's, GGD's, omgevingsdiensten: het register heeft
de deelnemers met toetredingsdatum, maar er is nog geen mechanisme voor gemeente → regeling).

## Gebruik

```bash
python3 tools/registers/oo.py haal          # nieuwe uitgave ophalen (+ .sha256)
python3 tools/registers/naar_model.py       # droogloop: aantallen, koppelingen, wat overgeslagen wordt
python3 tools/registers/naar_model.py --indienen

python3 tools/registers/tk.py haal
python3 tools/registers/tk_naar_model.py    # droogloop; koppelingen_<uitgave>.json en overgeslagen_<uitgave>.json ter controle
python3 tools/registers/tk_naar_model.py --indienen

python3 tools/registers/ep.py haal && python3 tools/registers/ep_naar_model.py [--indienen]
python3 tools/registers/lobby.py haal && python3 tools/registers/lobby_naar_model.py [--indienen]
python3 tools/registers/ser.py haal && python3 tools/registers/ser_naar_model.py [--indienen]
python3 tools/registers/cbs.py haal && python3 tools/registers/cbs_naar_model.py [--indienen]
python3 tools/registers/agenda.py haal && python3 tools/registers/agenda_naar_model.py [--indienen]   # + rapport analyse.md
python3 tools/registers/rechtspraak_naar_model.py [--haal] [--indienen]   # + rapport_<datum>.json
python3 tools/registers/tk_inspraak.py haal && python3 tools/registers/tk_inspraak_naar_model.py [--indienen]   # + analyse.md
python3 tools/registers/staatscourant_naar_model.py [--haal] [--indienen]   # + rapport_<datum>.json, analyse.md
python3 tools/registers/giften_naar_model.py [--haal] [--indienen]   # + rapport_<datum>.json, rapport.md
python3 tools/registers/giften.py voeg-toe <ods> --url <vindplaats> [--titel …]   # zelf gedownload overzicht
python3 tools/registers/ep_netwerk_naar_model.py [--haal] [--indienen]   # + rapport_<datum>.json/.md
python3 tools/registers/afm_naar_model.py [--haal] [--indienen]   # + analyse.md/analyse.json
python3 tools/registers/kruisrapport.py   # afgeleid, alleen lezen: per organisatie de registers en kanalen per beleidsdomein → data/registers/kruisrapport.md/.json; telt nergens mee, geen invloedsbewering

python3 tools/registers/wikidata.py haal     # namen en QID's (geen feiten); naar_model.py gebruikt de nieuwste
python3 tools/registers/wikidata_namen.py    # droogloop: welke voorletternamen eenduidig een volledige naam krijgen
python3 tools/registers/wikidata_namen.py --indienen [--hernoemen]   # QID's (en namen) via de REST-API

python3 scripts/registercheck.py [--droog]  # draait ook elk uur als stap 2b van de automatische beoordeling
python3 scripts/test_registers.py           # verse DB + fixtures, de hele keten (exit 0 = groen)
```

Een tweede run maakt niets dubbel (externe id's, bestaande verbanden worden overgeslagen).

## Regels die de import afdwingt

- **Nooit koppelen op naam alleen.** Een organisatie koppelt via haar externe id (`externe_ids`:
  `oo`, `tooi`, `tk_persoon`, …) of via `koppelingen.json` (met de hand nagelopen). Een persoon
  koppelt via een externe id, `koppelingen.json`, of een volledige naam plus een passende rol.
  Een naam met alleen voorletters koppelt alleen als hij in de hele uitgave uniek is, er precies
  één kandidaat met passende rol is en die kandidaat de plaats of functie in zijn beschrijving
  heeft; anders een nieuwe knoop met toevoeging, bv. "B.C.M. Vostermans (burgemeester Peel en
  Maas)". Het geval "Mw. A. van Dam ≠ Marcel van Dam" staat in de test.
- **Organisaties uit vrije tekst** (Kamerregisters) alleen onder hun naam in het model, of nieuw
  als de rechtsvorm in de naam staat (Stichting, Vereniging, Coöperatie, B.V., N.V., Universiteit,
  Hogeschool). Bij een nevenfunctie moet de rest van de zin uit functiewoorden bestaan
  ("Voorzitter Vrienden van het Rijksmuseum" wordt dus niet het Rijksmuseum); bij een geschenk moet
  de organisatie als gever genoemd zijn. Uit de loopbaan komt een nieuwe organisatie alleen bij een
  leidende of adviserende functie. Partij-eigen stichtingen en fracties, de Kamer zelf, de eigen
  partij als gever, de overheid als betaler van een reis en politieke ambten in de loopbaan tellen
  niet. Schrijfwijzen die afwijken ("Toqueville stichting") staan in `koppelingen.json`
  (`tk_namen`); de registercheck gebruikt dezelfde lijst.
- **Elk feit is letterlijk.** Het argument citeert de recordregel (`methode`
  `officieel_register_scrape`, `section` = recordsleutel, `page` = `<bron>/<uitgave>`), de bron
  heeft `cluster_key` `register:<bron>`, en de bewering is die regel zonder duiding. Daarom volgt
  een registerfeit het structuurpad (geen A2, geen smaadtoets) en telt het tegen een eigen
  dagplafond (`PROPAGANDA_REGISTER_PLAFOND`, 5000). De bronchecker en de bronzoeker slaan
  registerargumenten over (`registercheck.REGISTER_ARG_SQL`).
- **Bestaan begrenst** (2026-10-13, `looptijd.py`). Elk gepland verband valt binnen het bestaan
  van zijn eindpunten (`common.klem_relaties`): het begin wordt het laatste van het recordbegin en
  het begin van bron en doel (OO-record én model, het strengste), het einde het vroegste. Een
  ministerie in zijn huidige vorm (EZK 2010-10-14) stuurt een ouder agentschap dus pas vanaf 2010
  aan. Een ontbrekend begin blijft ontbreken. De droogloop telt wat geklemd is en wat de
  bestaanspoort nog zou weigeren (`bestaan: …`).
- **Afkortingen** (eigenaarsbesluit 2026-10-14). Het model heeft geen aliassen; de afkorting uit
  het register gaat als `metadata.afkorting` mee (`/register` met `afkorting`, of `metadata` bij een
  nieuwe knoop), zodat het nieuws RWS, IND of CJIB vindt. Alleen een echte afkorting die nog niet in
  de naam staat (`common.geen_afkorting`; niet bij gemeenten, die hun naam als afkorting hebben, en
  niet de provinciecodes), alleen als de knoop er nog geen heeft, en nooit als ze botst met een
  andere levende knoop: haar naam, een afkorting tussen haakjes of haar eigen afkorting
  (`common.afkorting_botst`: AP = 'AP (Associated Press)', RvS ~ 'RVS (…)'). Twee organisaties in
  één uitgave met dezelfde afkorting (SBB) krijgen haar geen van beide. De server toetst hetzelfde
  en meldt wat hij overslaat (`overgeslagen.afkorting`). Wie op naam matcht, leest haar mee:
  `common.namen_van`/`noemt` (vanaf drie tekens), `tk_naar_model.py`, de bronzoeker en
  datumzoeker, `scripts/scout_indienen.py`, de parkeercheck van de automatische beoordeling
  ("zelfde naam als de afkorting van …") en de zoekbalk van de viz (`graph_data`).
- **Volledige namen uit Wikidata** (2026-10-14, "via de routes"). Een hernoemen-RfC per persoon zou
  de RfC-agents (± 3 per uur) weken bezetten. `POST /api/entities/<id>/registernaam` (alleen
  `register-import`) wijzigt een voorletternaam deterministisch: de QID hangt al aan de knoop, de
  knoop is een ambtsdrager uit het register (`oo` `m:…`), de bewaarde Wikidata-uitgave is
  ongewijzigd (sha256), het label draagt de achternaam en voorletters uit het register en Wikidata
  kent de persoon in hetzelfde ambt in dezelfde gemeente (niet geëindigd vóór het begin uit het
  register). De toevoeging "(burgemeester …)" blijft alleen staan als de volledige naam al van een
  andere knoop is (een nagegane naamgenoot, `wikidata_namen.NAAMGENOTEN`); een duplicaat gaat via
  een samenvoegen-RfC. Gelogd in `edit_log` (`registernaam: wikidata Q…`), terug te draaien met
  `{"terug": true, "reden": …}`. Zonder `PROPAGANDA_REGISTERNAAM=1` op de server een droogloop;
  sinds 2026-10-14 staat de vlag aan in de launchd-plist van de server (eigenaarsbesluit). De registercheck blijft kloppen (hij toetst de achternaam en `m:…`).
- **Privacy.** Alleen publieke ambtsdragers; geen raadsleden in bulk; privépersonen nooit; geen
  adressen of telefoonnummers.

## Bekende gaten

- Het register van overheidsorganisaties noemt voor vijf provincies (Gelderland, Limburg,
  Noord-Brabant, Utrecht, Zeeland) geen CdK; zonder verband laat `naar_model.py` een organisatie
  weg. `tk_naar_model.py` en `cbs_naar_model.py` maken zo'n overheidsorganisatie alsnog aan (met
  haar `oo`-id en dezelfde naam en rol) zodra een feit haar nodig heeft.
- Het register noemt bij een gemeente alleen de provincie van een adres (`<provincie>` in
  `<adres>`); dat is geen bestuurlijk gegeven. Welke provincie toezicht houdt, komt uit de
  gemeentelijke indeling van het CBS (`cbs.py`).
- Dubbele ministeries in het model (BZK #156/#821, VWS #586/#820) wachten op een
  samenvoegen-RfC; `koppelingen.json` wijst het register naar #821 en #586.
