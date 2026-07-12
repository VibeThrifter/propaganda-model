# Missielog — flak op gegronde beleidscritici (De Hond, Helsloot, Meester, Hanekamp), ronde 2

- **Datum:** 2026-07-07
- **Account:** `assistent` (bijdrager) — alles `voorgesteld`
- **Opdracht:** aanvullende narratief-selectieve flak op gegronde/geloofwaardige beleidscritici; neutraal mét confound
  ([[flak-betwist-doelwit-neutraal-confound]]). Vier parallelle research-agents + zelf verbatim geverifieerd.

## Kernbevinding (eerlijk)

Het sterke "gegronde critici zijn breed onderdrukt"-beeld bleek **niet schoon te staven**: gegronde *inhoudelijke*
kritiek werd doorgaans serieus geëngageerd (dat is confound, geen flak); de duidelijke flak zit in **persoonsgerichte
diskreditering** en **media-gatekeeping**. Daarom kwaliteit boven kwantiteit, geen padding.

## Ingediend (`voorgesteld`)

Nieuwe entiteiten #801 Propaganda (KRO-NCRV, mediaorg), #802 Jaap Hanekamp (persoon, gezagsexpert).
Bronnen #1152–1159 (+ herbruik Pointer #886). 4 nieuwe edges + 2 augmentatie-argumenten:

- **#1471 Propaganda (KRO-NCRV) → Maurice de Hond** (publieke_aanval) — aflevering 28-01-2021 (privérekening/Hummel-
  sponsoring; ventilatie simplistisch). *Confound:* Omroepombudsman (17-09-2021): onderzoek "gezien zijn rol en positie
  te rechtvaardigen". **(eigenaar-lead)**
- **#1472 De Correspondent → Maurice de Hond** (publieke_aanval) — gecoördineerde reconstructie mét KRO-NCRV.
  *Confound:* Casper Albers (Pointer): De Hond maakt "valide punten" maar "slaat vaak de plank mis". **(eigenaar-lead)**
- **#1473 NRC → Jaap Hanekamp** (publieke_aanval) — guilt-by-association met Trump-verkiezingsfraude (Tom-Jan Meeus,
  06-09-2024). *Confound:* commissie-Hordijk keurde AERIUS deels af (Hanekamp deels vindicated).
- **#1474 RIVM → Jaap Hanekamp** (statelijke_tegenwerking) — institutionele afwijzing van zijn peer-reviewed AERIUS/OPS-
  kritiek (16-08-2022). *Confound:* Hordijk "schijnzekerheid" + het is een inhoudelijk-wetenschappelijke reactie.
- **rel #1257 (Op1 → Ira Helsloot)** aangevuld: +supporting (EO-terugblik noemt hem als geweerde criticus) +confound
  (Nieuwscheckers/Leiden: zijn "twee miljoen per levensjaar"-claim "niet hard te maken en waarschijnlijk overdreven").

## Bewust NIET ingediend

- **Ronald Meester** — zijn *zuivere* PCR-/modelkritiek werd juist serieus behandeld (NPO Radio 2), geen flak. De flak
  ("antivax-hoogleraar", Keulemans/de Volkskrant) hangt aan zijn véél betwistere **oversterfte**-claims, mét inhoudelijke
  weerlegging (Kloptdatwel). Bovendien: X/Twitter-quotes **niet verifieerbaar** (HTTP 402). → geen modelknoop, log-only.
- **De Hond — wetenschappelijke afwijzing** (Bonten "verwarring", Rosendaal, Albers): overwegend gemengd/legitiem debat
  dat samenviel met de toenmalige WHO-consensus (druppels vs. aerosolen, later gekanteld). Niet als aparte flak-edges
  opgeblazen; de persoonsgerichte laag (Propaganda/De Correspondent) is wél ingediend.
- **Helsloot — QALY-kritiek** (Canoy/Pomp): inhoudelijk meningsverschil = confound, geen aparte flak-edge.
- **Hanekamp — WUR "snijdt geen hout" / VN / NCTV**: WUR = wetenschappelijk debat (confound); VN/NCTV-koppeling liep
  te veel via Hanekamps eigen blogs → niet als harde quote ingediend.

## Verificatie

`validate_model.py --strict` → **EXIT 0** (golden snapshot groen; citatie-achterstand daalde 187→183 door de goed-
gesourcete toevoegingen). Alles `voorgesteld`. Elke quote verbatim gecheckt; NRC-quote via Headliner-mirror geverifieerd,
als NRC-bron geregistreerd.
