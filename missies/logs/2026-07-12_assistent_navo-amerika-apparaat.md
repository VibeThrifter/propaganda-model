# Missielog — NAVO/Amerika-beïnvloedingsapparaat op Nederland

**Datum:** 2026-07-12
**Account:** `assistent` (bijdrager) voor indienen; **via admin** (`maxime`-maintainer-token) gemerged op expliciete opdracht eigenaar ("alles via admin in praktijkmodel, ook in /onderzoek een stuk over de navo en amerika beinvloeding").
**Opdracht:** uitgebreid onderzoek naar hoe de NAVO precies op NL-beleid en -opinie inwerkt (van wie naar wie, rond het Rusland-/vijandbeeld-frame). Sluit aan op `2026-07-07_...oorlog-navo-selectie-cancelling.md`, `2026-07-08_...transatlantische-pers-en-defensie-content.md` en `onderzoek/.../transnationaal-naar-bias/`.

## Werkwijze
Deep-research-harnas startte maar de Fable-subagents raakten door credits heen (0 bronnen). Daarna zelf gedaan: parallelle WebSearch over 8 gap-hoeken → **kern-quotes verbatim via WebFetch geverifieerd** (LIMC/defensie.nl, StratCom-COE/stratcomcoe.org, Public Forum/nato.int, NVJ) → manifest `data/scout/navo-amerika-r1.json` → droogloop → `scout_indienen.py --indienen` (assistent) → goedkeuren/mergen via `maxime` → `validate --strict` EXIT 0 (136 fouten, onder baseline; golden snapshot groen).

## Ingediend + via admin gemerged (5 schone routes)
Bronnen #2125-2129, entiteit #1131, relaties #2040-2041, argumenten #3464-3470.

1. **NATO Public Forum 2025 (Den Haag)** — co-host-band NAVO+regering+denktanks. Args #3466 (→Clingendael #285), #3467 (→HCSS #284), #3468 (→AtlCom #1967). Verbatim nato.int: *"NATO and the Government of the Netherlands hosted the NATO Public Forum together with the Atlantic Commission of the Netherlands, the Clingendael Institute and The Hague Centre for Strategic Studies."*
2. **NATO StratCom COE Riga** — nieuwe entiteit #1131 (denktank) + relatie #2040 Defensie→COE (financiering, mech 52) + arg #3464. Verbatim: NL sinds 2016 sponsornatie; *"staffed and financed by its sponsoring nations."*
3. **LIMC** — arg #3470 op bestaande entiteit #1061. Verbatim commissie-Brouwer: onrechtmatig, ontbrekende rechtsbasis.
4. **BuZa→Atlantische Commissie publieksdiplomatie** — arg #3469 op bestaande rel #1552. IOB-ToR als bron-met-locator (PDF niet zelf verbatim uit te lezen; €1,86 mln 2006-2009 uit twee consistente indexeringen — als paraphrase, geen geciteerde verbatim).
5. **Draaideur Rutte premier→NAVO-SG** — relatie #2041 Rutte(#1105)→NAVO(#81) (draaideur, mech 18, active_from 2024-10-01) + arg #3465.

## /onderzoek
Nieuw stuk `onderzoek/3_mechanismes-van-beinvloeding/transnationaal-naar-bias/03_navo-amerika-apparaat.md` (4 sporen + confound), toegevoegd aan de README-mappenstructuur. Zusterstuk van `02_geopolitiek-frame-en-denktanks.md`.

## Bewust NIET ingediend (log-only)
- **NATO PDD co-sponsorship-grant** aan NL-organisatie: programma hard, geen NL-naam+bedrag.
- **StratCom-COE-rapport in NL-media**: geen concreet NL-artikel gevonden → alleen de financiering/mede-eigendom-edge (NL→COE), niet een bewezen media-invloed.
- **Bellingcat** (NED/Postcodeloterij-geld): confound-zwaar; complotduiding komt van onbetrouwbare pro-Russische outlets → niet overgenomen (twee-niveau-regel).
- **EUvsDisinfo-rectificatie 2018** (3 NL-outlets ten onrechte gelabeld → parlementaire kritiek → EEAS-verwijdering): het schone tegenvoorbeeld/confound, in het onderzoeksstuk verwerkt, niet als modelknoop.
- **JASON Institute**, **NATO Science for Peace → NL-uni**, **IGO-doctrine** (extern gericht), **ANP-churnalism-NAVO**: leads/context.

## Neutraliteit
Geen object-niveau-oordeel over Rusland/Oekraïne. Elke asymmetrie/claim als vaststelling van de externe/primaire bron; de confound (waar NL-instituties het frame-apparaat corrigeren) expliciet meegenomen. Structuur = de winst; scores blijven op de 0,05-vloer tot verder bewijs.
