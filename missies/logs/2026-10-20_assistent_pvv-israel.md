# 2026-10-20 — assistent — RechtsNL-carrousel "PVV exposed" (DepDiGiDRaH, grijs lead)

**Opdracht:** van de eigenaar, als vervolg op de Keijzer-ronde. De beweringen uit de post zijn nagegaan bij primaire en secundaire bronnen. De carrousel is een vindplaats, geen bron. Het frame ("× Israël / EXPOSED") is niet overgenomen.
**Account:** assistent (bijdrager). Alles is `voorgesteld`.

## Queries (letterlijk)
- DB (alleen lezen): entiteiten Wilders (640), PVV (55), Markuszower (3779), Kortenoeven (4947), Likud (4956), Samaria Regional Council (4957), David Horowitz Freedom Center (4958), Middle East Forum (4959), Robert Shillman (4960), Stichting Ondersteuning Tweede Kamerfractie PVV (5022), AIVD (173), plus hun relaties. Mechanismen met screening/naslag/benoeming. Missielog 2026-10-19 (cidi-reizen-israel-lobby).
- WebSearch: "Markuszower AIVD kandidaat-minister teruggetrokken 2024 antecedentenonderzoek"; "Markuszower 2010 AIVD kandidatenlijst PVV teruggetrokken Israëlische ambassade".
- Opgehaald (curl, citaten letterlijk teruggevonden): nos.nl/artikel/159060 (2010-05-22), nos.nl/artikel/2146037 (2016-12-02), nos.nl/artikel/2524553 (2024-06-14), vrt.be (2024-06-13, Belga), parlement.com/biografie/g-gidi-markuszower.

## Al in het model (ronde 2026-10-19, niet opnieuw ingediend)
- Likud → Wilders `geschenk`, reis 8–10 dec 2024: relatie 8512 (goedgekeurd), reizenregister.
- Samaria Regional Council → Wilders `geschenk`, reis 24–28 juli 2026: relatie 8513 (voorgesteld, arg 11727 geverifieerd).
- David Horowitz Freedom Center → PVV `donor`, 2014–2015 (€18.000 + €108.244,24): relatie 8514 (voorgesteld, arg 11325). In de post staat "Stichting Vrienden van de PVV"; de bron (giftenopgave via DutchNews) noemt de PVV.
- Middle East Forum → Wilders `financiering`, juridische verdediging 2010–2011: relatie 8515 (arg 11326, Reuters/Pipes).
- Robert Shillman → Wilders `financiering`, 2017: relatie 8516 (arg 11327, FTM 2021). Dat de betaling niet in het geschenkenregister stond, is niet apart nagegaan.
- Kortenoeven: CIDI 2000–2010 (8498), Tweede Kamer 2010–2012 (8499), PVV-fractie (8500).

## Oogst (nieuw)
Bronnen #3434 (NOS 2010), #3435 (NOS 2016), #3436 (NOS 2024). Hergebruikt: #3339 (Parlement.com Markuszower).
- Relatie **#8797** AIVD (173) → Gidi Markuszower (3779), `controle`, zonder mechanisme (kandidaat: er is geen mechanisme voor de naslag of het screenen van kandidaten), 2010 – 2024-06.
  - steunend 11821 (2010, NOS 2016), 11822 (juni 2024, Parlement.com);
  - context 11823 (Markuszower noemde de beschuldigingen "zo absurd", NOS 2010), 11824 (De Jonge: de AIVD rapporteert aan de formateur, NOS 2024);
  - looptijd 11825 (active_from 2010), 11826 (active_until 2024-06).
- Relatie **#8798** AIVD (173) → Geert Wilders (640), `controle`, kandidaat, 2009 – 2010.
  - steunend 11827 (volgens de Volkskrant via de NOS);
  - context 11828 (Plasterk: "We praten nooit over wat de AIVD onderzoekt of weet"; AIVD en Bouman reageerden niet);
  - looptijd 11829 (active_from 2009), 11830 (active_until 2010; eerst een 409 op gelijkenis met 11829, opnieuw ingediend met negeer_duplicaten omdat het een ander aspect is).
- Smaad: beide raken een persoon. De claims zijn geattribueerd ("volgens de NOS/Parlement.com/de Volkskrant"), zonder eigen oordeel; de smaadtoets beslist. Wat de AIVD precies vond, staat er niet in: dat is niet openbaar.

## Niet ingediend, met reden
- **"Mossad", "rekrutering", "opdrachten uit Israël"** (Tervoort, verklaring Kwint-de Roos 2010): beschuldigingen die aan één bron worden toegeschreven en niet toetsbaar zijn. De vermoedens over Israël en de Mossad in NRC/Volkskrant zijn bronnen die "vermoeden"; ze zijn niet als feit opgenomen.
- **Wilders op moshav Tomer (1980–82):** biografie, geen verband met een passend type.
- **Shillman "niet in het geschenkenregister":** niet nagegaan in deze ronde; de relatie staat al (8516).

## Stance-balans
3 steun / 0 tegen / 4 context / 4 looptijd-aspect. Er is geen tegenbron tegen het bestaan van de naslaguitkomsten gevonden: De Jonge en Parlement.com bevestigen 2024 en Markuszower zelf erkende de brief van 2010. De tegenkant (hij noemt de aantijgingen absurd, de AIVD zegt niets) staat als context.
