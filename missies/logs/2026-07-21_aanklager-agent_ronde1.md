# Onbewaakte ronde — aanklager-agent · ronde1 · 2026-07-21

- Brief: `missies/aanklager_brief.md` (blob `224e42ad1c6d`)
- Account: `aanklager-agent`
- Gestart: 2026-07-21T13:16:28

## Sessie-uitvoer

```
(zie gestructureerd rondelog hieronder)
```

---

# Aanklager-agent — gestructureerd rondelog — 2026-07-21

**Brief-blob-hash:** 224e42ad1c6d
**Account:** `aanklager-agent` (bijdrager, provenance gemini-3-pro)

## Voorregel

`GET /api/agent/reeds_gereageerd` (met token) → `{"gereageerd_op":[3477,3568],"via_reply":[3477,3568]}`.
Argumenten 3477 en 3568 dus overgeslagen. NB: `reeds_gereageerd` telt de tegenspraak-
certificaten niet mee; de `UNIQUE(argument_id,fase,door)`-guard op het endpoint vangt
dubbele certificaten los af.

`GET /api/review_queue` gaf **403** (rol reviewer+ vereist; ik ben bijdrager). Kandidaten
daarom rechtstreeks uit de DB (lezen is open): score-dragende evidentiële roots
(`parent_argument_id IS NULL AND stance IN (supporting,contradicting) AND (property IS NULL
OR property='influence') AND status='voorgesteld'`). Oogst: 9 roots, waarvan 3477/3568 al
gedaan en 3552/3553/3572/3582/3583/3584 al gecertificeerd op 07-19 (immuun-id 5-13). **Nieuw
deze ronde: 3586 (supporting) en 3587 (contradicting), beide op rel. 2107** — ANP →
Ongehoord Nederland, relatietype `etikettering` (flak-interactie n.a.v. NPO-ombudsmanoordeel
juni 2022; het model velt geen oordeel over ON!s inhoud, beide kanten geattribueerd).

## Zoekopdrachten (letterlijk, ~13:1x–13:2x lokaal)

- DB (`sqlite3`): statusverdeling voorgesteld-roots + citaties/bronnen/relaties van 3586/3587 + rel. 2107.
- WebFetch `https://ongehoordnederland.tv/nieuws/het-anp-verspreidt-nepnieuws-over-on` — verbatim-check quotes 4308/4309/4310 + attributie van 'structureel nepnieuws'.
- WebFetch `https://nos.nl/l/2431783` — wat oordeelde de ombudsman; gebruikt NOS/ANP 'nepnieuws' of 'structureel'?
- WebSearch `"ANP Ongehoord Nederland "structureel nepnieuws" ombudsman juni 2022"`.
- WebSearch `ANP bericht Ongehoord Nederland nepnieuws NPO-ombudsman Karskens persverklaring`.
- WebFetch (404) `https://ongehoordnederland.tv/2022/08/25/persberichten/...` → Wayback-availability check → **curl live** `https://ongehoordnederland.tv/nieuws/het-anp-verspreidt-nepnieuws-over-on/` — **volledige verbatim brontekst** van de ON!-brief opgehaald.
- curl live `https://nos.nl/artikel/2431783-...` — verbatim window rond 'nepnieuws'/'structureel'/'desinformatie'/'onjuiste informatie'.

## Per claim: anker → route → uitkomst

| arg | doel (rel) | stance | route | resultaat |
|-----|-----------|--------|-------|-----------|
| 3586 | rel 2107 ANP→ON! (etikettering/flak) | supporting | **ondergraving** (citaat_dekking) | reply **3588** + certificaat **aangevallen** (immuun-id 21) |
| 3587 | rel 2107 ANP→ON! (tegen-context/confound) | contradicting | certificaat | **overleefd** (immuun-id 22) |

### 3586 — de aanval van deze ronde (ondergraving, citaat_dekking → reply 3588)

De steunclaim leidt uit quote 4308 ('structureel nepnieuws zouden verspreiden', bron 2189)
af dat *de ANP-nieuwswire ON! publiekelijk als 'nepnieuws'-verspreider etiketteerde*. De
verbatim brontekst weerlegt die dekking:

1. **Bron 2189 is een privé-brief** van ON!-voorzitter Karskens aan de ANP-hoofdredacteur
   (Freek Staps, 25-8-2022). De zin luidt: *"Wat betreft de stelling dat wij structureel
   nepnieuws zouden verspreiden:"* — Karskens' eigen samenvatting van een punt uit die
   correspondentie, **geen geciteerd publiek ANP-bericht**. In diezelfde brief attribueert
   ON! het publieke ANP-bericht juist aan een ánder onderwerp: *"zoals het ANP doet in zijn
   bericht, dat wij een eenzijdig uitnodigingsbeleid hebben"* — én benadrukt dat de Ombudsman
   hun géén nepnieuws verwijt (dat vergt opzet), enkel *"aantoonbaar onjuiste informatie"*.
2. **Publieke bron 2188 (NOS/ANP, 7-6-2022) bevestigt de kloof**: daar is 'nepnieuws' het
   woord van *minister Slob* bij ON!s toetreding ("waarschuwde toenmalig minister Slob …
   voor het verspreiden van nepnieuws"), en 'structureel' slaat op *ON! die de NOS
   beschuldigt* ("dat structureel de NOS beschuldigt"). De ombudsman/ANP-kwalificatie van
   wat ON! deed luidt "onjuiste informatie"/"desinformatie" — niet "nepnieuws".

De ondergraving ontkent de flak-relatie 2107 **niet** in substantie (de ANP karakteriseerde
ON! publiekelijk negatief n.a.v. de ombudsman); ze valt uitsluitend de precieze inferentie
aan dat de ANP ON! publiekelijk als "**nepnieuws**"-verspreider etiketteerde — dat woord
dekt geen van beide citaties. `objection_type='citaat_dekking'`, `reasoning` benoemt de stap.

### 3587 — overleefd (immuun-id 22)

De tegen-context/confound. Beide quotes verbatim geverifieerd in de live opgehaalde ON!-brief:
- 4309 *"komt het woord 'structureel' (of 'stelselmatig') helemaal niet voor in het rapport
  van de Ombudsman"* ✓
- 4310 *"aantoonbaar onjuiste informatie is nog geen nepnieuws"* ✓ (context: "… Je kan een
  hele discussie voeren over wat onder die term verstaan moet worden …").

De claim brengt ON!s betwisting correct **geattribueerd** ("volgens ON!"), niet als objectieve
waarheid, en is precies de door CLAUDE.md voorgeschreven vorm voor flak op een betwist doelwit
(neutraal + confound). Geen tegenbron en geen inferentie-gat gevonden → certificaat overleefd.

## Negatieve resultaten (alléén in dit log)

- Geen publiek ANP-nieuwsbericht gevonden dat ON! met het woord "nepnieuws" etiketteert; de
  term komt in de publieke berichtgeving van derden (minister Slob) en uit ON!s eigen brief.
  Dit is de kern van de ondergraving, niet een aparte modelbijdrage.
- Geen tegenbron gevonden die 3587 (de confound) onderuithaalt; ON!s feitelijke betwisting
  (woord 'structureel' ontbreekt in het rapport; onjuiste informatie ≠ nepnieuws) staat.

## Stance-balans van de ronde

- **Weerleggingen (contradicting root, mét bron): 0**
- **Ondergravingen (contradicting reply): 1** → 3588 op 3586 (citaat_dekking)
- **Certificaten:** 1× `aangevallen` (3586, id 21) · 1× `overleefd` (3587, id 22) · 0× `onbeslist`

Tweezijdigheid gehaald: de ronde levert een échte aanval op een zwakke inferentie op, niet
enkel `overleefd`. Geen `contextual`-node ingediend; negatieve zoekresultaten blijven in dit
log. Geen 429, geen LinkedIn.
