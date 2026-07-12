# Scout-ronde: ontbrekende personen r2 — bestuurders/directie van stichtingen/fondsen/denktanks

- **Datum:** 2026-07-04
- **Account:** assistent (bijdrager)
- **Git-hash bij aanvang:** de441f1
- **Scope:** directeuren/bestuurders van stichtingen/fondsen/denktanks zonder persoonsedge
  (hoog-signaal voor eigendom/financiering/ideologie).
- **Tooling:** `scripts/scout_personen.py` + `data/scout/ronde2.json`. Alles `voorgesteld`.

## Geoogst (7 nieuw, 1 hergebruikt — relaties bestuurder, mechanisme-loze kandidaten)

| Persoon | Org | node | bron (verbatim) |
|---|---|---|---|
| Rogier van Vliet (voorzitter) | Adessium Foundation (317) | nieuw | adessium.org/en/team |
| Rogier van der Weerd (managing dir.) | Adessium Foundation (317) | nieuw | adessium.org/en/team |
| Carol Gribnau (directeur) | Stichting DOEN (318) | nieuw | fondsenwerving.nl 2021-01-26 |
| Annemarieke Nierop (directeur) | Wiardi Beckman Stichting (47) | nieuw | wbs.nl |
| Marjolein Moorman (voorz. curatorium) | Wiardi Beckman Stichting (47) | nieuw | wbs.nl |
| Marc Ernst (algemeen directeur) | TeldersStichting (46) | nieuw | teldersstichting.nl/over-ons |
| Patrick van Schie (wetensch. directeur) | TeldersStichting (46) | nieuw | teldersstichting.nl/over-ons |

- **Nienke Venema → SDM**: al aanwezig (#274 + bestaande bestuurder-edge). SDM had dus al een edge —
  ten onrechte in het manifest gezet; dedup ving het (overgeslagen). Geen dubbele data.
- Rollen: directeur → `directie` (49); voorzitter RvT/curatorium → `raad_van_commissarissen` (48).
- De owner (`maxime`) heeft de argumenten van deze ronde direct gemerged (edit_log 19:42:51) →
  status `ongecontroleerd`. De onderliggende relaties blijven `voorgesteld`-kandidaat (mechanisme-loos;
  goedkeuring vergt een mechanisme/RfC). Human-in-the-loop werkt.

## Overgeslagen / gedeferreerd (blijft in log)
- Obscure/kleine stichtingen zonder duidelijk hoog-signaal (Bureau Spotlight, Spot On Stories, SPIT,
  Stichting Groene Beheer, NCDO, Persvrijheidsfonds, borgingsstichtingen de Volkskrant/NU.nl/RTL/
  Het Nieuwe Parool/Weekbladpers): bestuur vaak = dezelfde management-/redactieleden; lagere prioriteit,
  later gericht sourcen.

## Volgende (r3)
- Bij de grote outlets is de huidige hoofdredacteur intussen grotendeels al toegevoegd door andere
  bijdragers (AD→Rijpma, Volkskrant→Klok, NRC→Veldhuis, Trouw→Boersema, NOS→Van Cann, De Telegraaf→
  Ullah/Wemmers, FD→Feenstra, FTM→Lensink). Resterende prominente gaten: **De Correspondent** (geen
  hoofdredacteur), **De Morgen**. Persbureaus Reuters/AP/AFP/Novum: internationaal, gedeferreerd.
