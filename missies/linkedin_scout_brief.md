# Missie-brief: linkedin-scout (netwerk-ontdekking via LinkedIn)

**Account:** `scout-agent` (Bearer-token in `data/tokens/scout-agent.token`).
**Tool:** `tools/linkedin/` (zie de README daar).
**Doel:** de banden tussen personen en organisaties/opleidingen/clubs in kaart brengen
door gerichte LinkedIn-profielen te scrapen en om te zetten naar **gedateerde
persoon→organisatie-affiliaties** — waaruit de org↔org-bruggen vanzelf volgen.

Dit is een verbijzondering van de gewone scout-missie (`scout_brief.md`): dezelfde
anti-overfit-plicht, dezelfde "ik stel voor, een mens beslist"-regel, maar met LinkedIn
als (zwakke, zelf-gerapporteerde) bron. Lees eerst `scout_brief.md`.

## Voorwaarden & grenzen (lees dit eerst)

- Geautomatiseerd scrapen schendt LinkedIn's voorwaarden en kan een account blokkeren.
  **Gericht** werken: een handvol relevante profielen per ronde, niet bulk. Headful,
  onder de sessie van de eigenaar. **De agent mag/kan zowel trap 1 (scrape) als trap 2
  (mapper) zelf draaien via Bash** — zolang de opgeslagen sessie leeft, is er geen
  mens nodig om te scrapen of in te dienen. **Alléén de interactieve login**
  (`scrape_profile.py login`, headful + 2FA/CAPTCHA) is mensenwerk; is de sessie verlopen,
  relay dan dat ene commando (zie hieronder) en wacht — nooit blijven herproberen.
- LinkedIn is **zelf-gerapporteerd** → betrouwbaarheid `grijs` (voorgesteld, telt niet in
  de score tot een reviewer classificeert). Nooit gezaghebbend classificeren.
- Alles landt `voorgesteld`. Geen statuswijzigingen, merges, classificaties, verwijderingen.
- **De login is eigenaarswerk — een agent kan 'm niet.** De LinkedIn-sessie
  (`session.json`) verloopt na dagen–weken. Is 'ie verlopen, dan stoppen zowel de scraper
  als de mapper met de melding *"⚠ LINKEDIN-SESSIE VERLOPEN"* en het exacte commando
  `python3 tools/linkedin/scrape_profile.py login`. Een agent kan dat commando **niet zelf
  draaien** (handmatige, headful login met evt. 2FA/CAPTCHA) — **geef het letterlijk door
  aan de eigenaar** en wacht tot die opnieuw heeft ingelogd. Nooit blijven herproberen of
  een lege scrape als "niets gevonden" indienen.

## Werkwijze

1. **Onderwerpkeuze — neutraal, tweezijdig.** Kies profielen die het netwerk
   *aantoonbaar* missen (uit `data/onderzoeksagenda.json`, `ontbreekt`-lijst), en oogst
   tweezijdig: óók tegenmacht-actoren (vakbondsbestuurders, NGO-directeuren, rechters,
   klokkenluiders), niet alleen draaideur-elite. Een ronde die alleen pro-elite-banden
   binnenbrengt is meetbaar kapot.
2. **Scrape gericht** (trap 1, eigenaar): `scrape_profile.py <url>` →
   `data/linkedin/<slug>.json`. Log elke gescrapete URL.
3. **Controleer vóór indienen.** Open het JSON. Kloppen de organisatienamen met
   *bestaande* knopen (anders krijg je duplicaten met een net andere schrijfwijze)?
   Is dit echt dezelfde persoon? LinkedIn-zelfrapportage kan onjuist/opgeblazen zijn.
4. **Droogloop** (trap 2): `linkedin_naar_model.py <json>` — lees het plan, corrigeer
   namen/types waar nodig in het JSON, en dien dan in met `--indienen`.
5. **Log de ronde** in `missies/logs/` (zie `README.md`): brief-hash, elke gescrapete
   URL, per profiel de aangemaakte source-/entity-/relation-/argument-id's, en de
   stance-/nieuwheidsbalans.

## Modelleerdiscipline (hard — uit CLAUDE.md)

- **Loopbaan = gedateerde `persoon→org`-affiliaties** (personeel/bestuurder/adviseur/
  woordvoerder_van), instanties van `draaideurconstructie`. De org↔org-band is de
  **afgeleide brug** — sla die NOOIT als edge op. Geen `org→org`-draaideur.
- **Opleiding → `persoon→onderwijsinstelling`** (`lidmaatschap`), mechanisme-loos =
  kandidaat. Alleen een reviewer beslist of het op opleidingsniveau
  `academische_socialisatie` instantieert (geldt voor journalistiekopleidingen, niet
  voor elke studie). Geef een subeenheid (opleiding) alleen een eigen knoop als een
  mechanisme op dát niveau grijpt.
- **Club/lidmaatschap → `persoon→org`** (`lidmaatschap`), kandidaat.
- **Assen guilty-until-proven:** geen `certainty`/`influence` zetten. Score uit bewijs.
- **Type is een gok:** de mapper vult conservatief in (`bedrijf`/`onderwijsinstelling`/
  `stichting`); de reviewer bevestigt/corrigeert het structurele type en de rol.
- **Bron verplicht, verbatim.** Elke affiliatie draagt een `supporting`-argument met een
  citatie naar het profiel. Fabriceer geen quotes; gebruik de eigen tekst van het profiel.

## Wat de mapper NIET doet (bewust)

- Geen `interests` (bedrijven die iemand *volgt*) als lidmaatschap — volgen ≠ lid zijn.
- Geen gerichte org→org-invloedspijlen verzinnen; verwevenheid = de afgeleide brug.
- Geen mechanismen aanmaken (theorielaag = RfC, mensenwerk).
