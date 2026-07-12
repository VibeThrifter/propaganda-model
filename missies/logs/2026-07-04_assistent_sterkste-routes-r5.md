# Scout-ronde: sterkste routes r5 — transnationaal, alleen het NL-harde deel

- **Datum:** 2026-07-04 · **Account:** assistent · **Git-hash:** de441f1
- **Scope:** wire-doorvoer + denktank-cofinanciering; frame-claims uitsluitend als NL-gemeten
  (Pointer/EUR) of peer-reviewed (Bergman) — analogie-materiaal (Zollmann/Aday) bewust NIET ingediend.
- **Tooling:** `scripts/scout_indienen.py` + `data/scout/sterkste-routes-r5.json`.

## Queries (research-agent)
Rob de Wijk hoogleraar internationale betrekkingen Universiteit Leiden emeritus · Clingendael
jaarverslag 2024 financiering ministeries subsidie inkomsten · Pointer Nel Ruigrok Koude Oorlog frame
kranten 24,1 procent artikelen · Bergman "Following Washington's Lead" International Communication
Gazette 2014 Dutch press Iraq · Clingendael "annual report" 2024 OR 2023 pdf income ministries funding
— plus directe fetches: TNO-rapport blg-142848.pdf (83 p., integraal geëxtraheerd), Aanhangsel
Handelingen ah-tk-20222023-2998, hcss.nl/finance-transparency + Client Overviews 2022-2025 (PDF),
Clingendael Annual Report 2024 + Income Table 2023 (PDF via curl), universiteitleiden.nl, rechtspraak-
en frame-bronnen.

## Geoogst (2 entiteiten #614-615, 5 relaties #1193-1197, 12 argumenten, 8 bronnen)

| Relatie | mech | rel-id | bron |
|---|---|---|---|
| Rob de Wijk → Universiteit Leiden (personeel, 2000-emeritaat) | kandidaat | 1193 | Leiden-profiel + Wikipedia |
| Min. BuZa → HCSS (financiering) — **mét contradicting**: HCSS' eigen onafhankelijkheidsclaim | denktank_financiering_bias (52) | 1194 | Aanhangsel Handelingen 2998 (PROGRESS €2 mln/jr, 40/60) + hcss.nl |
| Europese Commissie → Clingendael (financiering, EU-delegatie Thailand €100-500k) | 52 | 1195 | Clingendael Income Table 2023 |
| RVO → Clingendael (financiering, hoogste staffel >€500k) | 52 | 1196 | Income Table 2023 |
| Politie → HCSS (financiering, hoogste staffel >€500k-2mln, 2025) | 52 | 1197 | HCSS Client Overview 2025 |

Losse argumenten: PROGRESS-quotes als extra supporting op bestaande rels 152/153/154
(Defensie/BuZa→HCSS/Clingendael); NAVO-klantfeit 2023-2025 als supporting op rel 40; Pointer
Koude-Oorlog-frame (24,1%, 1500 artikelen, 5 dagbladen) + Bergman (NL-pers volgde Washington vóór
Irak 2003, alleen DOI-locator — paywall) als supporting op mechanisme 156 (indexering).

## Modelleerkeuzes & correcties op de missievoorbereiding
- **PROGRESS-verdeling is 40/60 (HCSS/Clingendael), niet 60/40** — Kamerantwoord verbatim gevolgd;
  bedragen tijdgebonden aan het Kamerstuk (2023, "PROGRESS 2.0").
- **HCSS-onafhankelijkheidsclaim als contradicting** op de nieuwe BuZa→HCSS-edge: financiering ≠
  aangetoonde inhoudelijke sturing; claims geformuleerd als klant-/financieringsfeiten.
- Staffelbedragen zijn omzetklassen — claims als "in staffel X", nooit als exact bedrag.

## Negatief / niet ingediend (belangrijk — corrigeert bestaand beeld)
- **DPA→ANP, Belga→ANP, AP→ANP: NIET gestaafd door TNO 2011.** AP loopt sinds 2007 exclusief via
  Novum; Belga is ANP-*klant* (nachtwerk uitbesteed aan ANP), geen leverancier. Sterker: ook een
  generieke AFP→ANP- of Reuters→ANP-nieuwsfeed staat NIET in het rapport — alleen de financieel/
  beursnieuws-samenwerking Reuters↔ANP voor businessklanten. **Als de bestaande relaties 425/426
  (AFP→ANP, Reuters→ANP) op dit rapport leunen is dat mis-attributie; reviewer-check aanbevolen.**
- **EU-instellingen als HCSS-klant:** niet aangetroffen (Hybrid CoE Helsinki is intergouvernementeel,
  géén EU) — daarom géén EU→HCSS-edge; wél EC→Clingendael (Income Table).
- **Clingendael-staatsaandeel als percentage:** niet gepubliceerd in het jaarverslag 2024 — de oude
  ~75%-claim blijft verworpen en is niet heringediend.
- **De vijf onderzochte dagbladen (Pointer):** nergens bij naam genoemd — claim houdt het op "de vijf
  grootste dagbladen".
- **Rob de Wijk emeritaatsjaar:** niet hard — alleen active_from gezet.
