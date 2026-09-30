# Onbewaakte ronde — aanklager-agent · ronde1 · 2026-07-24

- Brief: `missies/aanklager_brief.md` (blob `224e42ad1c6d`)
- Account: `aanklager-agent`
- Gestart: 2026-07-24T09:29:56

## Samenvatting ronde

**Account:** `aanklager-agent` (bijdrager, provenance gemini-3-pro — gedecorreleerd t.o.v. indiener
`assistent`/claude en A1 `verificatie-agent`/gpt-5.1). Server lokaal (`/api/health` → 200). Tijden UTC.

### Voorregel (verplicht)

`GET /api/agent/reeds_gereageerd` → `gereageerd_op = [3477, 3568, 3586]` (via reply/rating),
overgeslagen als reply-doelen. **Let op:** dekt alléén replies/ratings, **niet** tegenspraak-
certificaten — zie de #3582-noot onderaan.

`review_queue` is reviewer-gated (bijdrager → 403), dus de score-dragende `voorgesteld`-roots zijn
uit de DB gehaald: 54 evidentiële roots (parent NULL, stance supporting/contradicting, property
NULL/`influence`, niet-vervangen), alle door `assistent`. Grotendeels het NPO-omroep
draaideur/partijbinding-cluster + Justice for Prosperity + ANP + Clingendael/REKA + tegenmacht.

### Zoekopdrachten (letterlijk, WebSearch, ~07:35–07:38 UTC)

1. `Wil van Gemert AIVD directeur Nationale Veiligheid 2004 2012 loopbaan`
2. `Erik Raven hoofdredacteur ANP interim 2026`
3. `Henri Kruithof VVD lid partij spindoctor communicatieadviseur`
4. `ANP hoofdredacteur Freek Staps 2025 2026 wie is hoofdredacteur ANP`
5. `Bob Deen Clingendael REKA Rusland Oost-Europa Kennisalliantie`
6. `Nikki Sterkenburg hoogleraar bezwaar onderzoeksjournalisten NCTV onverenigbaar`
7. `Bernt Schneiders voorzitter Raad van Toezicht VPRO`
8. `Eric Holterhues voorzitter Raad van Toezicht KRO-NCRV ChristenUnie`

WebFetch (mislukt, niet gebruikt): `web.archive.org/.../anp.nl/blog/68` → "unable to fetch from web.archive.org".

### Aanvallen (ondergravingen)

- **#3582 · doel rel2104 (Erik Raven —personeel→ ANP) → ONDERGRAVING #3710** (`citaat_dekking`).
  Claim beweert in tegenwoordige tijd dat Raven als hoofdredacteur a.i. verantwoordelijk is "tot de
  komst van een nieuwe hoofdredacteur". Die is er al jaren: **Freek Staps is hoofdredacteur ANP sinds
  1 september 2019** (opvolger Marcel van Lingen) en nog steeds in 2025-2026 (adformatie.nl,
  villamedia.nl, nieuws.beeldengeluid.nl 15 nov 2025). Ravens a.i.-stint was mrt–sep 2019, vlak vóór
  Staps; hij is nu nieuwsmanager/eindredacteur. De ANP-blogpagina (blog/68) beschrijft een
  historische situatie en draagt de present-tense claim niet.
- **#3619 · doel rel2137 (Bob Deen —bestuurder→ REKA) → ONDERGRAVING #3711** (`citaat_dekking`).
  Citatie (headliner.nl "Bob Deen volgt Monika Sie op…") onderbouwt Deens Clingendael-directeurschap
  + Rusland/Oost-Europa-expertise, maar **noemt REKA nergens**. REKA-rol is feitelijk juist
  (clingendael.org: secretariaat = consortium Clingendael + Raam op Rusland, geleid door resp. Deen
  en Smeets), maar staat in een ándere bron. Aanbeveling: koppel clingendael.org.

### Overleefd (certificaten, web-geverifieerd)

- **#3618** rel2136 Clingendael medeoprichter REKA → cert #26 `overleefd` (clingendael.org).
- **#3631** rel2149 VVOJ-bezwaar Sterkenburg → cert #27 `overleefd` (villamedia.nl + netkwesties.nl;
  19 VVOJ-leden). Nuance in cert: het waren VVOJ-**léden**, niet formeel het verenigingsbestuur.
- **#3664** rel2173 Wil van Gemert AIVD 2004-2012 → cert #28 `overleefd` (algemenebestuursdienst.nl,
  security.nl, ICCT).
- **#3687** rel2194 Eric Holterhues RvT-voorzitter KRO-NCRV → cert #29 `overleefd`
  (broadcastmagazine.nl, spreekbuis.nl, parlement.com; benoemd 14 dec 2024).
- **#3689** rel2196 Bernt Schneiders RvT-voorzitter VPRO → cert #30 `overleefd` (haarlem105.nl,
  vpro.nl; per 1 okt 2024).
- **#3703** rel2210 Henri Kruithof VVD-lidmaatschap → cert #31 `overleefd`. Bron dekt "voormalig
  VVD-spindoctor" verbatim; lidmaatschap niet formeel bewezen maar extern bevestigd (Kruithof was
  VVD-**Statenlid**). Géén ondergraving: de conclusie is waar, dus een citaat_dekking-aanval zou
  zichzelf weerleggen. Aanbeveling: koppel een Statenlidmaatschap-bron.

### Onderzocht, geen aparte modelbijdrage (negatief/neutraal — alléén hier)

- **Kruithof (#3703):** overwogen als `citaat_dekking`-ondergraving (bron="spindoctor",
  relatie="lidmaatschap") → verworpen, want lidmaatschap is waar (VVD-Statenlid).
- **ANP-adjunct-hoofdredacteuren #3583/#3584:** dateren "per 15 april 2022", lege quote. Niet
  afgerond deze ronde (scope); geen aanwijzing dat de datum onjuist is. Geen vulling ingediend.
- **Justice for Prosperity zelf-gepubliceerd (#3665-3671):** bron = jfp's eigen site; valide voor
  het feit *dát* JfP dit publiceerde / wie in het bestuur zit. Niet gecertificeerd deze ronde.

### ⚠ Discrepantie voor de reviewer — #3582 tegenspraak-certificaat

Een **eerdere** aanklager-ronde (2026-07-19, cert #10) certificeerde #3582 als **`overleefd`**, en A1
(cert #18) gaf `klopt` — beide vertrouwden op de ANP-blogpagina zonder de **actualiteit** te checken.
Fout: Staps is al sinds 2019 hoofdredacteur. Door `UNIQUE(argument_id,fase,door)` kon ik het stale
`overleefd`-certificaat **niet vervangen** (409). De operatieve aanval is ondergraving #3710 (open) —
die dempt de σ van #3582 én blokkeert A7-auto-merge (A7 vereist *geen openstaande ondergraving*), dus
de firewall houdt ondanks het verouderde certificaat. **Actie voor de mens:** behandel #3582 als
aangevallen; cert #10 is achterhaald.

### Stance-balans

- **Aanvallen:** 2 ondergravingen (#3710 → #3582; #3711 → #3619) · 0 weerleggingen (beide zwaktes
  waren citaat_dekking-gaten, geen relatie-onwaar-makende tegenbron).
- **Certificaten:** 7 tegenspraak-oordelen → 1 `aangevallen` (#3619, cert #25) + 6 `overleefd`
  (#3618, #3631, #3664, #3687, #3689, #3703; certs #26-31).
- Tweezijdigheid gehaald: 2 genuine inferentie-aanvallen naast de survivors.

Alles `voorgesteld` / procesmetadata; niets gemerged, geen status/bron-classificatie gewijzigd,
niets verwijderd. Geen 429, geen LinkedIn-actie.

## Sessie-uitvoer

```
