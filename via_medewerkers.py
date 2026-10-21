"""Via medewerkers: de route instituut ⇢ doel via zijn mensen (eigenaarsbesluit 2026-10-19).

De eigenaar: "denktank of instituut zoals clingendael en universiteit stuurt experts naar de
media … ook de experts zelf zou in het propaganda model moeten komen … invloed gaat wss van
clingendael via die expert naar media … beide erin zetten?" — en daarna "voer uit".

Eén optreden staat op precies één verband (DOCUMENTATIE.md § "Instituut of persoon"):
  * spreekt het instituut zelf (rapport, cijfers, peiling, persbericht, standpunt,
    mediapartnerschap, of iemand die in een officiële functie het product of standpunt van het
    instituut presenteert), dan instituut → medium;
  * geeft een persoon eigen duiding met het instituut als herkomst ("Clingendael-onderzoeker Bob
    Deen"), dan persoon → medium met ``relations.namens_id`` = het instituut;
  * een oud-medewerker of iemand met een andere pet: persoon → medium zonder namens_id.

De route instituut ⇢ medium via die persoon wordt hier afgeleid en niet opgeslagen, zoals het
partijnetwerk (partijen.py): beschrijvend, telt nergens mee, geen invloedsbewering. Dat is ook
het eigen principe van het model ("indirectheid is een eigenschap van een pad"). Een route telt
alleen als:
  1. het verband persoon → doel goedgekeurd is, met namens_id = de organisatie;
  2. de persoon een goedgekeurde band met die organisatie heeft (een richtingloos type:
     personeel, dienstverband, bestuurder, adviseur, lidmaatschap, woordvoerder_van, draaideur,
     ambt);
  3. de looptijden elkaar niet uitsluiten (een open grens sluit niets uit): wie al weg was, trad
     niet meer namens de organisatie op.

Alleen stdlib; gedeeld door de server (``GET /api/via_medewerkers/<id>``), de viz en
validation.py (NAMENS-ONGELDIG, NAMENS-ZONDER-BAND, INSTITUUT-VIA-PERSOON).
"""
from __future__ import annotations

import re

import looptijd
import vocab

# Banden waarmee iemand bij een organisatie hoort (alliantie is tussen organisaties)
BAND_TYPES = tuple(sorted(vocab.RICHTINGLOZE_TYPES - {"alliantie"}))
MEDIA_TYPES = ("mediaorganisatie", "omroep", "persbureau", "platform")
# Mechanismen waarmee een organisatie of persoon als bron of expert in een medium verschijnt
EXPERT_MECHANISMEN = ("expert_framing", "expert_legitimatie", "bron_afhankelijkheid",
                      "institutioneel_gezag", "ngo_levert_expert", "denktank_naar_persbureau")
# Woorden die zeggen dat het instituut zelf spreekt (zijn product of officiële stem): dan hoort
# het optreden juist op instituut → medium (INSTITUUT-VIA-PERSOON vlagt het niet)
INSTITUTIONEEL = ("rapport", "cijfer", "peiling", "raming", "prognose", "doorrekening", "onderzoek van",
                  "persbericht", "woordvoerder", "directeur", "president", "voorzitter",
                  "hoofdeconoom", "mediapartner", "partnerschap", "standpunt", "barometer",
                  "monitor", "namens het", "namens de")
_GENERIEK = ("Instituut", "Stichting", "Universiteit van", "Universiteit", "Hogeschool")


def naamvormen(naam, afkorting=None) -> set[str]:
    """Herkenbare vormen van een organisatienaam: de naam, het deel tussen haakjes, de afkorting
    en de naam zonder generiek woord ('Clingendael Instituut' → 'Clingendael')."""
    naam = (naam or "").strip()
    vormen = {naam}
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", naam)
    if m:
        vormen |= {m.group(1).strip(), m.group(2).strip()}
    if afkorting:
        vormen.add(afkorting.strip())
    for v in list(vormen):
        for w in _GENERIEK:
            if v.startswith(w + " "):
                vormen.add(v[len(w) + 1:].strip())
            if v.endswith(" " + w):
                vormen.add(v[: -len(w) - 1].strip())
    return {v for v in vormen if len(v) >= 3}


def noemt(vormen, tekst) -> bool:
    """Noemt de tekst een van deze vormen als woord? Een koppelteken telt als grens:
    'Clingendael-onderzoeker' noemt Clingendael, 'CBS-hoofdeconoom' noemt het CBS."""
    for v in vormen:
        if re.search(rf"(?<!\w){re.escape(v)}(?!\w)", tekst or "", flags=re.I):
            return True
    return False


def _banden(conn) -> dict:
    """{(persoon_id, organisatie_id): [band, …]} — goedgekeurde, levende banden."""
    uit: dict = {}
    for r in conn.execute(f"""
            SELECT r.id, r.source_id, r.target_id, r.relation_type, r.functie, r.active_from,
                   r.active_until, s.type AS s_type, t.type AS t_type
            FROM relations r JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
            WHERE r.status = 'goedgekeurd' AND NOT r.vervangen
              AND r.relation_type IN ({','.join('?' * len(BAND_TYPES))})
              AND (s.type = 'persoon') <> (t.type = 'persoon')""", BAND_TYPES):
        p, o = (r["source_id"], r["target_id"]) if r["s_type"] == "persoon" else (r["target_id"], r["source_id"])
        uit.setdefault((p, o), []).append(dict(r))
    return uit


def _past(band, van, tot) -> bool:
    return looptijd.overlapt(van, tot, band["active_from"], band["active_until"])


def routes(conn, entity_id=None) -> list[dict]:
    """Alle afgeleide routes (of alleen die waarin ``entity_id`` instituut, persoon of doel is),
    elk met de band die haar draagt. Gesorteerd op instituut, doel, persoon."""
    filt, params = "", []
    if entity_id is not None:
        filt = " AND (r.namens_id = ? OR r.source_id = ? OR r.target_id = ?)"
        params = [entity_id] * 3
    banden = _banden(conn)
    uit = []
    for r in conn.execute(f"""
            SELECT r.id, r.source_id, r.target_id, r.namens_id, r.relation_type, r.functie,
                   r.active_from, r.active_until, m.name AS mechanisme,
                   p.name AS persoon, d.name AS doel, d.type AS doel_type,
                   i.name AS instituut, i.type AS instituut_type
            FROM relations r
            JOIN entities p ON p.id = r.source_id AND p.type = 'persoon'
                           AND p.status = 'goedgekeurd' AND NOT p.vervangen
            JOIN entities d ON d.id = r.target_id AND d.status = 'goedgekeurd' AND NOT d.vervangen
            JOIN entities i ON i.id = r.namens_id AND i.type <> 'persoon'
                           AND i.status = 'goedgekeurd' AND NOT i.vervangen
            LEFT JOIN mechanisms m ON m.id = r.mechanism_id
            WHERE r.status = 'goedgekeurd' AND NOT r.vervangen AND r.namens_id IS NOT NULL{filt}
            ORDER BY i.name, d.name, p.name, r.id""", params):
        passend = [b for b in banden.get((r["source_id"], r["namens_id"]), [])
                   if _past(b, r["active_from"], r["active_until"])]
        if not passend:
            continue
        band = sorted(passend, key=lambda b: (b["active_from"] is None, b["active_from"] or "", b["id"]))[0]
        uit.append({
            "relation_id": r["id"], "relation_type": r["relation_type"], "mechanisme": r["mechanisme"],
            "functie": r["functie"], "van": r["active_from"], "tot": r["active_until"],
            "persoon_id": r["source_id"], "persoon": r["persoon"],
            "doel_id": r["target_id"], "doel": r["doel"], "doel_type": r["doel_type"],
            "instituut_id": r["namens_id"], "instituut": r["instituut"],
            "instituut_type": r["instituut_type"],
            "band_id": band["id"], "band_type": band["relation_type"],
            "band_functie": band["functie"], "band_van": band["active_from"],
            "band_tot": band["active_until"],
        })
    return uit


def voor_entiteit(conn, entity_id) -> dict | None:
    """Voor het detailpaneel en de nieuws-app: de routes waarin deze entiteit instituut (via
    zijn mensen naar welke doelen), doel (welke instituten achter de experts) of persoon (namens
    wie) is. None als de entiteit geen goedgekeurde, levende entiteit is."""
    e = conn.execute("SELECT id, name, type FROM entities WHERE id = ? AND status = 'goedgekeurd' "
                     "AND NOT vervangen", (entity_id,)).fetchone()
    if e is None:
        return None
    alle = routes(conn, entity_id)
    als_instituut = [x for x in alle if x["instituut_id"] == entity_id]
    als_doel = [x for x in alle if x["doel_id"] == entity_id]
    als_persoon = [x for x in alle if x["persoon_id"] == entity_id]

    def groepeer(rij, sleutel, naam):
        groepen: dict = {}
        for x in rij:
            g = groepen.setdefault(x[sleutel], {"id": x[sleutel], "naam": x[naam], "routes": []})
            g["routes"].append(x)
        return sorted(groepen.values(), key=lambda g: (-len(g["routes"]), g["naam"] or ""))

    return {
        "entiteit": {"id": e["id"], "naam": e["name"], "type": e["type"]},
        "als_instituut": groepeer(als_instituut, "doel_id", "doel"),
        "als_doel": groepeer(als_doel, "instituut_id", "instituut"),
        "als_persoon": als_persoon,
        "aantal": {"als_instituut": len(als_instituut), "als_doel": len(als_doel),
                   "als_persoon": len(als_persoon)},
    }


# ── Controles (validation.py) ───────────────────────────────

def ongeldig(conn) -> list[str]:
    """NAMENS-ONGELDIG: een levend verband met een namens_id die niet kan. De API houdt dit
    tegen (server._namens_fout); dit vangt wat langs een andere weg binnenkwam."""
    uit = []
    for r in conn.execute("""
            SELECT r.id, r.relation_type, r.source_id, r.target_id, r.namens_id,
                   s.name AS bron, s.type AS bron_type, t.name AS doel,
                   n.name AS namens, n.type AS namens_type, n.vervangen AS namens_weg
            FROM relations r JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
            LEFT JOIN entities n ON n.id = r.namens_id
            WHERE r.namens_id IS NOT NULL AND NOT r.vervangen
              AND r.status IN ('goedgekeurd', 'voorgesteld') ORDER BY r.id"""):
        fout = namens_fout(r["bron_type"], r["relation_type"], r["source_id"], r["target_id"],
                           r["namens_id"], r["namens_type"], r["namens_weg"])
        if fout:
            uit.append(f"relatie #{r['id']}: {r['bron']} — {r['relation_type']} — {r['doel']} "
                       f"(namens {r['namens'] or '#' + str(r['namens_id'])}): {fout}")
    return uit


def namens_fout(bron_type, relation_type, source_id, target_id, namens_id, namens_type,
                namens_vervangen=False) -> str | None:
    """Waarom deze hoedanigheid niet kan (None = in orde). Gedeeld met de API."""
    if namens_type is None:
        return f"entiteit #{namens_id} bestaat niet"
    if namens_vervangen:
        return f"entiteit #{namens_id} is vervangen; kies de opvolger"
    if namens_type == "persoon":
        return "namens is een organisatie, geen persoon"
    if bron_type != "persoon":
        return "alleen een persoon treedt namens een organisatie op (de bron is geen persoon)"
    if namens_id in (source_id, target_id):
        return "namens is een derde organisatie, niet de bron of het doel van het verband zelf"
    if relation_type in vocab.RICHTINGLOZE_TYPES:
        return (f"een '{relation_type}'-band is zelf de band met een organisatie; namens hoort "
                "bij wat iemand doet (een optreden, advies, lobby)")
    return None


def zonder_band(conn) -> list[str]:
    """NAMENS-ZONDER-BAND: een goedgekeurd verband namens een organisatie terwijl het model geen
    goedgekeurde band tussen persoon en organisatie kent, of alleen een band die in die periode
    niet liep. Dan ontbreekt de band (laat de scout hem zoeken) of klopt de pet niet."""
    banden = _banden(conn)
    uit = []
    for r in conn.execute("""
            SELECT r.id, r.source_id, r.namens_id, r.active_from, r.active_until,
                   s.name AS bron, t.name AS doel, n.name AS namens
            FROM relations r JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
            JOIN entities n ON n.id = r.namens_id
            WHERE r.namens_id IS NOT NULL AND r.status = 'goedgekeurd' AND NOT r.vervangen
            ORDER BY r.id"""):
        lijst = banden.get((r["source_id"], r["namens_id"]), [])
        if not lijst:
            uit.append(f"relatie #{r['id']}: {r['bron']} → {r['doel']} namens {r['namens']}: "
                       "geen goedgekeurde band tussen persoon en organisatie")
        elif not any(_past(b, r["active_from"], r["active_until"]) for b in lijst):
            perioden = ", ".join(f"#{b['id']} {b['active_from'] or '…'}–{b['active_until'] or ''}"
                                 for b in lijst)
            uit.append(f"relatie #{r['id']}: {r['bron']} → {r['doel']} namens {r['namens']} "
                       f"({r['active_from'] or '…'}–{r['active_until'] or ''}) valt buiten de band "
                       f"({perioden})")
    return uit


def instituut_via_persoon(conn) -> list[str]:
    """INSTITUUT-VIA-PERSOON: een goedgekeurd verband organisatie → medium met een expert- of
    bronmechanisme waarvan elk levend steunend argument over een optreden van één van haar
    mensen gaat, zonder dat het instituut zelf spreekt (geen rapport, cijfers, woordvoerder,
    directeur, partnerschap …). Dat optreden hoort op persoon → medium (met namens_id)."""
    banden = _banden(conn)
    mensen: dict = {}
    for (p, o) in banden:
        mensen.setdefault(o, set()).add(p)
    namen = {r["id"]: r["name"] for r in conn.execute(
        "SELECT id, name FROM entities WHERE type = 'persoon' AND NOT vervangen")}
    uit = []
    for r in conn.execute(f"""
            SELECT r.id, r.source_id, s.name AS bron, t.name AS doel, m.name AS mechanisme
            FROM relations r JOIN entities s ON s.id = r.source_id JOIN entities t ON t.id = r.target_id
            JOIN mechanisms m ON m.id = r.mechanism_id
            WHERE r.status = 'goedgekeurd' AND NOT r.vervangen AND s.type <> 'persoon'
              AND t.type IN ({','.join('?' * len(MEDIA_TYPES))})
              AND m.name IN ({','.join('?' * len(EXPERT_MECHANISMEN))})
            ORDER BY r.id""", (*MEDIA_TYPES, *EXPERT_MECHANISMEN)):
        claims = [a[0] or "" for a in conn.execute("""
            SELECT claim FROM arguments WHERE relation_id = ? AND parent_argument_id IS NULL
              AND NOT vervangen AND stance = 'supporting' AND COALESCE(property, 'existence') = 'existence'
              AND status IN ('ongecontroleerd', 'geverifieerd', 'betwist', 'bronvermelding_nodig')""",
            (r["id"],))]
        if not claims:
            continue
        personen = set()
        for claim in claims:
            genoemd = {p for p in mensen.get(r["source_id"], ())
                       if namen.get(p) and noemt({namen[p]}, claim)}
            if not genoemd or any(w in claim.lower() for w in INSTITUTIONEEL):
                break
            personen |= genoemd
        else:
            uit.append(f"relatie #{r['id']}: {r['bron']} → {r['doel']} ({r['mechanisme']}): het bewijs "
                       "gaat over optredens van " + ", ".join(sorted(namen[p] for p in personen)))
    return uit
