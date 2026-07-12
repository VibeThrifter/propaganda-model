# Data-licentie — de propagandamodel-feed

Deze licentie geldt voor het **verkoopbare dataproduct**: de CSV-export in
`releases/dataset-v<X.Y.Z>/` en de feed-API (`/api/feed/*`). Ze geldt **niet** voor
de broncode van de applicatie (die kent een eigen licentie) en **niet** voor de open,
ongemeterde portal-reads (`/api/graph_data` e.d.), die onder de gebruiksvoorwaarden
van de site vallen.

## Wat je mag

- De data **inzien, analyseren en verwerken** in je eigen onderzoek, journalistiek of
  (AI-)model, mits met bronvermelding (zie hieronder).
- Afgeleide analyses, grafieken en bevindingen **publiceren**, mits met bronvermelding
  en met de methodologische kanttekeningen (zie "Neutraliteit & methode").

## Wat je niet mag

- **Doorverkopen of herdistribueren** van de dataset (of een substantieel deel ervan)
  als data-product, database of feed — al dan niet bewerkt. De feed is per licentie-
  houder; deel je key niet.
- De data presenteren als een **meting, ranglijst of beschuldiging**. De scores zijn
  afgeleide, onzekerheidsdragende schattingen met een guilty-until-proven ondergrens
  van 0,05 (zie `docs/DATA_DICTIONARY.md`), geen feitelijk oordeel over personen of
  organisaties.
- De data **combineren met of verrijken tot** de bewust uitgesloten lagen (politieke
  positie per natuurlijk persoon — art. 9-AVG — en machtsvalentie) en die als onderdeel
  van dit product presenteren.

## Bronvermelding (verplicht)

Vermeld bij elk publiek gebruik de bron en de versie, bijvoorbeeld:

> Bron: Propagandamodel — NL-mediamachtsgraaf, dataset v<X.Y.Z>. Methode en
> verantwoording: <site>/methode.

## Neutraliteit & methode

Het model beschrijft pro-elite bias als een **emergente eigenschap van structurele
krachten**, niet als een complot. Het spreekt in zijn eigen stem alléén gesourcete
feiten en geattribueerde meningen. De volledige verantwoording — de vijf filters, de
scoring-/bewijsdiscipline, de twee-assen-score, de 0,05-vloer en de
neutraliteitsverklaring — staat op de publieke methodepagina **`/methode`** (kruis-
verwijzing J1) en in `docs/DATA_DICTIONARY.md`. Wie de data gebruikt, wordt geacht die
kanttekeningen mee te nemen.

## Gevoelige data uitgesloten

De feed bevat **geen** politieke-positie-laag (art. 9-AVG) en **geen** machtsvalentie.
De uitsluiting is mechanisch en verifieerbaar:

```bash
grep -rc "politieke_positie\|machtsvalentie" releases/dataset-v*/   # → 0
```

## Geen garantie

De data wordt geleverd "as is", zonder garantie op volledigheid of juistheid. Het is
een levend onderzoeksmodel; relaties en scores wijzigen tussen versies.
