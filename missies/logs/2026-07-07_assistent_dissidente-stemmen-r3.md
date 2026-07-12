# Missielog — dissidente stemmen, ronde 3 (platform-deplatforming, cordon sanitaire, cancelling)

**Datum:** 2026-07-07
**Account:** `assistent` (bijdrager) voor indienen; merge via admin (`maxime`-maintainer-token) op expliciete opdracht eigenaar ("dien zoveel mogelijk in via admin als er bronnen zijn").
**Sluit aan op:** `2026-07-05_assistent_flak-dissidente-stemmen.md` (rol `publieke_dissident` #60, mechanismen `debanking`/`strafvervolging_uiting`) en de talkshow-ronde (`2026-07-06`, o.a. de Talitha Muusse-redactiedruk).

## Aanleiding
Eigenaar vroeg om **meer dissidente-stem-casussen**, ook minder bekende, en of er meer te vinden is in bronnen zoals Mediacourant. Bevinding vooraf: het model dekt de grote zaken al breed (27 dissident-entiteiten; debanking- en strafvervolging-instanties + redactiedruk). Nieuwe waarde zit in een **nog niet gedekte flak-dimensie**: *platform-deplatforming* (een platform verwijdert zelf de content/het kanaal van een dissidente stem) naast financieel debanking, plus het historische ur-voorbeeld (cordon sanitaire) en een cancelling-casus.

## Mediacourant-oordeel (antwoord op de meta-vraag)
Bruikbaar als **vindplaats**, niet als zelfstandige bron: tabloid-achtige aggregator (betrouwbaarheid `grijs`/`regulier`) → altijd doorlopen naar de primaire bron. Bovendien is de oogst grotendeels **buiten scope**: de meeste "presentator ontslagen"-stukken zijn entertainment/gossip (dronken gast, kijkcijfers, contractruzie), geen mening-tegen-de-consensus. Talitha was een zeldzame schone. Betere jachtgronden voor dit thema: Villamedia/NVJ (redactieconflicten), rechtspraak.nl/OM, de betrokkene's eigen verklaring, en rechterlijke uitspraken.

## Ingediend + gemerged (alles goedgekeurd; `validate --strict` groen, geen fouten boven baseline)

**Bronnen** (#964–#967): ICTRecht-blog (m.b.t. ECLI:NL:RBAMS:2020:4435), De Nieuwe Wereld (X-post 2020-05-27), Hart van Nederland (Douwe Bob/Lukkassen 2022), StukRoodVlees (cordon sanitaire CP/CD). Alle met url-locator + verbatim geverifieerd citaat.

**Entiteiten** (#751–#754): YouTube (`platform`, rol `techplatform` 18), Sid Lukkassen (`persoon`, rol `publieke_dissident` 60), Douwe Bob (`persoon`, rol `publiek` 35), Hans Janmaat (`persoon`, rol `publieke_dissident` 60, 1982–1998).

**Relaties** (#1391–#1394), alle mechanisme `deplatforming` (#12, flak):
- **#1391 YouTube → Café Weltschmerz** (censuur, 2020). Supporting (#1913): YouTube verwijderde twee interviews (huisarts over hydroxychloroquine). **Contradicting (#1914):** de rechtbank (ECLI:NL:RBAMS:2020:4435) oordeelde dat verwijdering terecht was wegens potentieel schadelijke desinformatie — confound expliciet gemodelleerd, net als bij OM→Wilders.
- **#1392 YouTube → De Nieuwe Wereld** (censuur, mei 2020). Supporting (#1915): video met Kees de Kort & Ad Verbrugge over economische coronagevolgen verwijderd; kanaal tekende bezwaar aan.
- **#1393 Tweede Kamer → Hans Janmaat** (censuur, 1984–1998). Supporting (#1916): cordon sanitaire — geen samenwerking, niet gedebatteerd. **Contradicting (#1917):** tweemaal veroordeeld in de jaren '90 → uitsluiting mede reactie op strafbaar geoordeelde uitingen (confound).
- **#1394 Douwe Bob → Sid Lukkassen** (flak, 2022). Supporting (#1918): boekpresentatie *Wees Afgrondelijk!* afgeblazen na onderzoek van diens radicaal-rechtse werk. **NB in de relatiebeschrijving:** particuliere keuze van één ondernemer, geen institutionele flak → bewust gemarkeerd als zwakke, niet-structurele instantie (eigenaar wilde 'm er toch in met bron).

## Modelleerkeuzes
- **Geen nieuw mechanisme (geen RfC):** platform-verwijdering valt onder het bestaande `deplatforming` (#12, "uitsluiten van een stem / cancelling"). Een aparte `platform_inhoudsmoderatie` zou zuiverder zijn maar vergt twee menselijke reviewers; buiten deze ronde gehouden.
- **Confounds als contradicting root mét bron** (weerlegging, geen ondergraving), conform de monitor-discipline: counter-evidence met bron → contradicting root op het doel. Zo lift de `onweersproken`-vlag correct en blijft het beeld eerlijk.
- **Douwe Bob-caveat** in de beschrijving i.p.v. een ondergraving-reply (manifest ondersteunt geen replies); structurele zwakte is zo wél zichtbaar.

## Bewust NIET ingediend
- **Elsbeth Etty ↔ NRC** (2010, column ingetrokken): buiten scope — establishment-links columnist, geen dissidente stem tégen de consensus.
- Diverse Mediacourant-hits (Venderbos, Khalid Kasem e.d.): entertainment/gossip, geen opinie-tegen-establishment.
- Overige YouTube/Blckbx-verwijderingen zonder schone primaire bron: niet gefabriceerd; blijven kandidaat voor een volgende ronde met betere bron.
