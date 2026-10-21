# Onbewaakte ronde — nieuws-scout · ronde1 · 2026-10-16

- Brief: `missies/nieuws_scout_brief.md` (blob `3a6cca5f46b6`)
- Account: `nieuws-scout`
- Gestart: 2026-10-16T08:07:54

## Sessie-uitvoer

```
# Ronde-log: nieuws-scout, ronde 1, 16 oktober 2026

Ik heb drie doelen geclaimd en alle drie op `klaar` gezet. Daarvoor heb ik zes bronnen, twee knopen, drie verbanden en zeven argumenten ingediend, allemaal `voorgesteld`. Er kwam geen 429 en na de ronde geen 409. LinkedIn heb ik niet gebruikt.

- **Brief:** `missies/nieuws_scout_brief.md`, blob `3a6cca5f46b6`. **Account:** `nieuws-scout`.
- **Voorregel:** `GET /api/agent/reeds_gereageerd` gaf `gereageerd_op: []`. Er was niets over te slaan en ik heb geen reacties ingediend.
- **LinkedIn-rem:** `mag zoek` en `mag profiel` gaven allebei exit 0, dus ik claimde met `&linkedin=1`. Na de ronde gaf `status` voor profiel en zoek allebei uur 0/2 en dag 0/10, binnen de actieve uren.
  - Ik heb LinkedIn bewust overgeslagen. Bij Kottelenberg en Van der Horst dekten het register, de vakpers en het officiële CV van de gemeente de loopbaan beter. Bij Mens dekten de vakmedia de rol. De sessie is dus niet getest.
- **Claim:** `POST /api/nieuws/doelen/claim_volgende?limit=3&linkedin=1` gaf 73 `person:jan-kottelenberg`, 120 `person:melanie-van-der-horst` en 226 `person:harry-mens`.

## Per doel
| Doel | Status | Ingediend |
|---|---|---|
| 73 Jan Kottelenberg (knoop 2819) | klaar | relatie **8393** (Kottelenberg ↔ Gemeente Lochem, `ambt`, mech 210, functie Wethouder, vanaf 2006), bron **3087** (Binnenlands Bestuur, Personalia 03-2017), argument **11012** |
| 120 Melanie van der Horst (knoop 2180) | klaar | bronnen **3088** (interview Vervoerregio Amsterdam, Wayback) en **3089** (De Westkrant, 25 mei 2022, Wayback); argument **11010** (`active_from` 2001 op D66-lidmaatschap 3089) en **11011** (`active_from` 2022 op wethoudersambt 3088) |
| 226 Harry Mens | klaar | knopen **4895** Harry Mens (persoon, rol journalist) en **4896** Business Class (televisieprogramma) (mediaorganisatie, rol redactie, vanaf 1997); relaties **8394** (Mens ↔ Business Class, `personeel`, mech 18, Presentator, vanaf 1997) en **8395** (RTL Nederland → Business Class, `mediaplatform`, mech 160, zonder beginjaar); bronnen **3090** (Spreekbuis), **3091** (Broadcast Magazine), **3092** (Mediacourant); argumenten **11013**, **11014** (`active_from` 1997), **11015** en **11016** (op knoop 4896: commerciële partijen kopen er tegen betaling zendtijd in) |

Bij Mens heb ik de precedenten van de RTL Tonight-presentatoren gevolgd (rel. 1276, 1273). Hij is een persoon met een publieke mediarol: presentator van een programma op RTL 7.

### Wat misging tijdens het indienen
- **Ongeldige bronklasse.** De eerste run gaf 400 omdat ik bronklasse `secundair` had opgegeven, en die bestaat niet. Daardoor zijn de relaties 8393, 8394 en 8395 en de knopen 4895 en 4896 eerst zonder argumenten aangemaakt.
- **Herstel.** Ik heb de klasse veranderd in `regulier` (`institutioneel` voor de Vervoerregio) en de argumenten daarna als losse argumenten op de echte id's ingediend. Alle zeven hebben een citaat en geen ervan staat op `smaad_hold`.
- **Gaten in `scripts/scout_indienen.py`.** Losse argumenten lossen geen manifest-sleutels op. Bij een tweede run hangt het script ook geen argumenten aan relaties die al bestaan.

## Zoekopdrachten (letterlijk)
- **Web:**
  - `Melanie van der Horst wethouder Amsterdam D66 geïnstalleerd 2022`
  - `Jan Kottelenberg burgemeester Neder-Betuwe benoemd CDA loopbaan`
  - `Harry Mens Business Class RTL 7 sinds presentator programma betalen bedrijven`
  - `"Kottelenberg" geïnstalleerd burgemeester Neder-Betuwe 2017 wethouder Lochem`
  - `Kottelenberg beëdigd burgemeester Neder-Betuwe april 2017 afscheid wethouder Lochem`
  - `Lochem nieuwe wethouder opvolger Kottelenberg 2017`
  - `"Kottelenberg" Neder-Betuwe burgemeester "Lochem" afscheid 2017 Gelderlander`
  - `"Melanie van der Horst" nieuwe wethouder Verkeer Amsterdam 2022 D66 college beëdigd`
  - `amsterdam.nl wethouder Melanie van der Horst sinds juni 2022 D66 lijsttrekker`
  - `Melanie van der Horst wethouder Amsterdam loopbaan voor wethouderschap fractievoorzitter D66 gemeenteraad`
  - `Amsterdam nieuwe wethouders geïnstalleerd 1 juni 2022 Van der Horst Verkeer Melanie D66`
  - `"Van der Horst" D66 wethouder verkeer Amsterdam juni 2022 Parool nieuw college Halsema` (extended)
  - `"2022-2026" wethouder "Verkeer en Vervoer" "Melanie van der Horst" CV`
  - `"Business Class" Harry Mens RTL 7 programma presentator sinds 1993 televisieprogramma`
  - `Business Class Harry Mens gasten betalen voor optreden zendtijd RTL gekocht` (extended)
- **Opgehaald:**
  - binnenlandsbestuur.nl Personalia 18-2016 en 03-2017
  - organisaties.overheid.nl/20265917
  - Wikidata Q29212053 (P39: geen einddatum voor Lochem)
  - nl.wikipedia (Van der Horst, Business Class, Harry Mens), alleen als vindplaats voor de voetnoten
  - het gemeente-CV (pdf en Wayback 2023)
  - de Wayback-kopieën van het Vervoerregio-interview, de D66 West-pagina, amsterdam.nl en raadsinformatie 01-06-2022
  - vervoerregio.nl (5 juli 2022), De Westkrant (Wayback), Spreekbuis, Broadcast Magazine, Mediacourant (2024 en 2026)
- **Database (alleen-lezen):**
  - entiteiten en relaties rond 2819 en 2180
  - Lochem, Provincie Gelderland, Vervoerregio, Choho
  - RTL-knopen en presentator-precedenten (`functie like '%presentat%'`)
  - mechanismen advertentie/eigendom
  - `edit_log` en `looptijd_onderzoek` voor 3088, 3089, 4159 en 4160 (alle vier `register_zonder_datum`)

## Negatieve resultaten (alleen in dit log)
- **Kottelenberg:**
  - Geen bron voor het einde van zijn wethouderschap in Lochem, dus 8393 heeft geen `active_until`. De datumzoeker zoekt verder.
  - Geen bron voor het begin van zijn CDA-lidmaatschap.
  - Statenlid Gelderland ("ruim twaalf jaar") zonder jaartallen, dus niet ingediend.
- **Van der Horst:**
  - Geen bron die haar naam combineert met de exacte datum 1 juni 2022, dus de begindatum staat op jaarprecisie.
  - De knoop heet "M. van der Horst (wethouder Amsterdam)"; de volledige naam ontbreekt (registernaam-route).
  - Mogelijk vervolg: voorzitter van het dagelijks bestuur van de Vervoerregio Amsterdam sinds juli 2022 (vervoerregio.nl). Niet ingediend, omdat de Vervoerregio niet in het model staat.
- **Mens:**
  - Geen bron voor het beginjaar van de uitzending op een RTL-zender (8395 `zonder_jaar`).
  - Niet ingediend: partijbanden (KVP-raadslid Lisse, VVD) en sponsoring van Fortuyn. Daarvoor vond ik geen primaire bron. Ook privézaken en de OM-schikking niet: die zijn geen structuurfeit.
  - Lead voor later: wie zendtijd koopt (adverteerder → Business Class), met meerdere bronnen (Rambam 2011, Mediacourant 2026).

## Stance-balans
7 steun, 0 tegen, 0 context.

```

## Runner-metadata

- Exit-code: 0
- Duur: 658.4 s
- Oogst (edit_log-delta van `nieuws-scout`): 18
- Beëindigd: 2026-10-16T08:18:53
