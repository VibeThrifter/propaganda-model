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
| Wikidata SPARQL (`query.wikidata.org`) | `wikidata.py` → `wikidata_namen.py` (droogloop), `naar_model.py` | `data/registers/wikidata/wikidata_<datum>.json` | geen feiten, alleen naam en QID: burgemeesters en wethouders (P39 met een ambt onder Q13423499/Q20748682, P1001 gemeente, P382 CBS-code). Een registernaam met alleen een achternaam koppelt bij precies één passende persoon (zelfde gemeente, functie, achternaam, ambt loopt); `wikidata_namen.py` meldt welke voorletternamen eenduidig een volledige naam krijgen (hernoemen = maintainer). |
| Lobbyistenregister van de Tweede Kamer (pdf op `tweedekamer.nl/contact_en_bezoek/lobbyisten`) | `lobby.py` → `lobby_naar_model.py` | `data/registers/lobby/lobby_<bijgewerkt>.pdf` | elke organisatie met een vaste toegangspas, en de opdrachtgevers die al in het model staan (`lobbyt` → Tweede Kamer, `lobbytoegang`). De tabel wordt gelezen uit de woordposities (PyMuPDF); de lobbyisten zelf worden geen knoop. Werkgevers zonder rechtsvorm in de naam zijn met de hand getypeerd in `koppelingen.json` (`lobby_organisaties`). |

Nog te doen (plan fase 3f): subsidies (de download van Rijksfinanciën geeft nu 404); de
hernoeming van voorletternamen naar hun Wikidata-naam (een maintainer, zie `wikidata_namen.py`);
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

python3 tools/registers/wikidata.py haal     # namen en QID's (geen feiten); naar_model.py gebruikt de nieuwste
python3 tools/registers/wikidata_namen.py    # droogloop: welke voorletternamen eenduidig een volledige naam krijgen

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
- **Privacy.** Alleen publieke ambtsdragers; geen raadsleden in bulk; privépersonen nooit; geen
  adressen of telefoonnummers.

## Bekende gaten

- Het register van overheidsorganisaties noemt voor vijf provincies (Gelderland, Limburg,
  Noord-Brabant, Utrecht, Zeeland) geen CdK; zonder verband laat `naar_model.py` een organisatie
  weg. `tk_naar_model.py` maakt zo'n overheidsorganisatie alsnog aan (met haar `oo`-id en dezelfde
  naam en rol) zodra een Kamerfeit haar nodig heeft.
- Dubbele ministeries in het model (BZK #156/#821, VWS #586/#820) wachten op een
  samenvoegen-RfC; `koppelingen.json` wijst het register naar #821 en #586.
