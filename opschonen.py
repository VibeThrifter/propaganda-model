"""Opschonen: deterministische regels voor dubbel werk in de praktijklaag (eigenaarsakkoord
2026-10-09, "data opschonen ... via de eigen routes van het model"). Alleen stdlib. De server
neemt het besluit (``/api/beoordeling/dubbel/<id>`` en ``/api/beoordeling/bron_dubbel/<id>``,
merge-service); de automatische beoordeling vraagt het elke ronde aan, wat het nieuws toont eerst.

Dubbele verbanden. Een goedgekeurd verband is dubbel als een ander levend, goedgekeurd verband
hetzelfde feit draagt, in een periode die overlapt (twee aparte termijnen zijn twee feiten):
  1. hetzelfde paar, type en mechanisme;
  2. een ambt naast een algemene band (bestuurder, lidmaatschap, personeel, draaideur) van
     dezelfde persoon met dezelfde organisatie en hetzelfde mechanisme (of de band heeft er geen):
     het ambt wint (type en functie uit het register zijn preciezer, en de registers-sync houdt
     het bij);
  3. dezelfde tweezijdige band in beide richtingen met hetzelfde mechanisme: de richting die het
     mechanisme het vaakst heeft.
Een band met een ander mechanisme is een ander feit (bv. een draaideur naar een ambt: wie waar
vandaan kwam) en blijft; of dat mechanisme klopt, is een vraag voor de agents, geen regel hier.
Het blijvende verband moet zelf gedragen zijn (een eigen bron, of een registerregel). Een
registerfeit gaat voor, dan wat een bron draagt, dan het oudste. Wat een mens goedkeurde, blijft
staan. Het dubbele verband wordt afgewezen; zijn discussieboom gaat mee (terug te halen), en een
begindatum die het blijvende verband mist, neemt dat over.

Dubbele bronnen. Twee bronnen met dezelfde url (zonder schema, www, slash op het eind, fragment
en tracking-parameters) zijn één bron: de oudste blijft, citaties, vermeldingen, locaties en
oordelen verhuizen, de dubbele verdwijnt. Eén pagina telt zo nooit als meer onafhankelijke
bewijslijnen (M1.2). ``POST /api/sources`` hergebruikt een bron met dezelfde url voortaan.
"""
from __future__ import annotations

import json
from urllib.parse import parse_qsl, urlencode, urlsplit

# Banden die niets anders zeggen dan dat een persoon ergens bij hoort of voor werkt
ALGEMENE_BAND = ("bestuurder", "lidmaatschap", "personeel", "draaideur")
# Richtingloze banden (web/template.html TWEEZIJDIG_TYPES): beide richtingen = één feit
TWEEZIJDIG = ("lidmaatschap", "bestuurder", "adviseur", "draaideur", "personeel", "alliantie")
REGISTER_CLUSTER = "register:"
TRACKING = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid", "ref_src")
DUBBEL_REDEN = "automatische beoordeling: dubbel verband"
BRON_REDEN = "automatische beoordeling: dubbele bron"


# ------------------------------------------------------------------ verbanden
def _datum(waarde, eind) -> str | None:
    """'2019' / '2019-06' / '2019-06-01' → een volledige datum (begin of eind van de periode)."""
    if not waarde:
        return None
    w = str(waarde)[:10]
    if len(w) == 4:
        return w + ("-12-31" if eind else "-01-01")
    if len(w) == 7:
        return w + ("-31" if eind else "-01")
    return w


def _overlapt(a, b) -> bool:
    """Overlappen de looptijden echt (een onbekende grens overlapt altijd; twee termijnen die
    op elkaar aansluiten, niet)?"""
    a_van, a_tot = _datum(a["active_from"], False), _datum(a["active_until"], True)
    b_van, b_tot = _datum(b["active_from"], False), _datum(b["active_until"], True)
    if a_tot and b_van and a_tot <= b_van:
        return False
    if b_tot and a_van and b_tot <= a_van:
        return False
    return True


def gedragen_door(conn, rid):
    """Het id van een levend steunend argument met een echte bron dat het verband draagt
    (gemerged, niet verworpen of verouderd, en het nieuwste A1-oordeel is niet 'klopt-niet'),
    of None. (De server gebruikt dit ook voor 'zonder bron'.)"""
    rij = conn.execute("""
        SELECT a.id FROM arguments a
        WHERE a.relation_id = ? AND a.parent_argument_id IS NULL AND NOT a.vervangen
          AND a.stance = 'supporting' AND COALESCE(a.property, 'existence') = 'existence'
          AND a.status IN ('ongecontroleerd', 'geverifieerd', 'betwist')
          AND EXISTS (SELECT 1 FROM citations c WHERE c.argument_id = a.id AND (
                TRIM(COALESCE(c.quote, '')) <> ''
                OR EXISTS (SELECT 1 FROM source_locations sl WHERE sl.source_id = c.source_id)))
          AND COALESCE((SELECT o.verdict FROM immuun_oordelen o WHERE o.argument_id = a.id
                          AND o.fase = 'herverificatie' ORDER BY o.created_at DESC, o.id DESC
                          LIMIT 1), '') <> 'klopt-niet'
        ORDER BY a.id LIMIT 1""", (rid,)).fetchone()
    return rij[0] if rij else None


def _registerfeit(conn, rid) -> bool:
    """Draagt een registerregel dit verband (Uitbreiding C)?"""
    return conn.execute("""
        SELECT 1 FROM arguments a JOIN citations c ON c.argument_id = a.id
        JOIN sources s ON s.id = c.source_id
        WHERE a.relation_id = ? AND a.parent_argument_id IS NULL AND NOT a.vervangen
          AND a.stance = 'supporting' AND a.status <> 'verworpen'
          AND c.methode = 'officieel_register_scrape' AND s.cluster_key LIKE ?
        LIMIT 1""", (rid, REGISTER_CLUSTER + "%")).fetchone() is not None


def _door_mens_goedgekeurd(conn, rid) -> str | None:
    rij = conn.execute("""
        SELECT l.changed_by FROM edit_log l JOIN users u ON u.username = l.changed_by
        WHERE l.table_name = 'relations' AND l.record_id = ? AND u.kind = 'mens'
          AND l.new_value LIKE '%goedgekeurd%' ORDER BY l.id DESC LIMIT 1""", (rid,)).fetchone()
    return rij["changed_by"] if rij else None


def _richting_telt(conn, mech_id, bron_is_persoon) -> int:
    """Hoe vaak heeft dit mechanisme een goedgekeurd verband met een persoon (of juist geen
    persoon) als bron?"""
    return conn.execute("""
        SELECT COUNT(*) FROM relations r JOIN entities s ON s.id = r.source_id
        WHERE r.mechanism_id IS ? AND r.status = 'goedgekeurd' AND NOT r.vervangen
          AND (s.type = 'persoon') = ?""", (mech_id, 1 if bron_is_persoon else 0)).fetchone()[0]


def dubbel_kandidaten(conn, rid):
    """Levende, goedgekeurde verbanden die met verband ``rid`` hetzelfde feit kunnen dragen,
    met de regel die het zegt: [(rij, regel)]."""
    rel = conn.execute("SELECT * FROM relations WHERE id = ?", (rid,)).fetchone()
    if rel is None:
        return rel, []
    uit = []
    for r in conn.execute("""
            SELECT r.*, s.type AS bron_type FROM relations r JOIN entities s ON s.id = r.source_id
            WHERE r.id <> ? AND r.status = 'goedgekeurd' AND NOT r.vervangen
              AND ((r.source_id = ? AND r.target_id = ?) OR (r.source_id = ? AND r.target_id = ?))""",
                          (rid, rel["source_id"], rel["target_id"], rel["target_id"],
                           rel["source_id"])):
        if not _overlapt(rel, r):
            continue
        zelfde_richting = r["source_id"] == rel["source_id"]
        if (zelfde_richting and r["relation_type"] == rel["relation_type"]
                and r["mechanism_id"] == rel["mechanism_id"]):
            uit.append((r, "zelfde paar, type en mechanisme"))
        elif zelfde_richting and r["bron_type"] == "persoon" and (
                {r["relation_type"], rel["relation_type"]} & {"ambt"}
                and {r["relation_type"], rel["relation_type"]} - {"ambt"} <= set(ALGEMENE_BAND)
                and r["relation_type"] != rel["relation_type"]
                and (r["mechanism_id"] == rel["mechanism_id"]
                     or None in (r["mechanism_id"], rel["mechanism_id"]))):
            uit.append((r, "een ambt naast een algemene band met dezelfde organisatie"))
        elif (not zelfde_richting and r["relation_type"] == rel["relation_type"]
              and rel["relation_type"] in TWEEZIJDIG and r["mechanism_id"] == rel["mechanism_id"]):
            uit.append((r, "dezelfde tweezijdige band in beide richtingen"))
    return rel, uit


def _voorkeur(conn, rij, regel):
    """Sorteersleutel: wat blijft (laagste wint)."""
    if regel.startswith("een ambt"):
        eerst = 0 if rij["relation_type"] == "ambt" else 1
    elif regel.startswith("dezelfde tweezijdige"):
        bron_is_persoon = conn.execute("SELECT type FROM entities WHERE id = ?",
                                       (rij["source_id"],)).fetchone()["type"] == "persoon"
        eerst = -_richting_telt(conn, rij["mechanism_id"], bron_is_persoon)
    else:
        eerst = 0
    return (eerst, 0 if _registerfeit(conn, rij["id"]) else 1,
            0 if gedragen_door(conn, rij["id"]) else 1, rij["id"])


def dubbel_besluit(conn, rid):
    """Mag de automatische beoordeling verband ``rid`` afwijzen als dubbel? → (ok, redenen
    waarom niet, motivatie, blijvend verband of None)."""
    rel, kandidaten = dubbel_kandidaten(conn, rid)
    if rel is None:
        return False, ["niet gevonden"], None, None
    redenen = []
    if rel["status"] != "goedgekeurd" or rel["vervangen"]:
        redenen.append(f"status is '{rel['status']}' — alleen goedgekeurde verbanden")
    if not kandidaten:
        redenen.append("geen ander verband draagt hetzelfde feit")
    if redenen:
        return False, redenen, None, None
    mens = _door_mens_goedgekeurd(conn, rid)
    for blijvend, regel in kandidaten:
        if not (gedragen_door(conn, blijvend["id"]) or _registerfeit(conn, blijvend["id"])):
            continue
        if mens and not _door_mens_goedgekeurd(conn, blijvend["id"]):
            # Een besluit van een mens blijft staan, tenzij een mens hetzelfde feit ook in
            # het blijvende verband goedkeurde (dan blijft zijn besluit daar staan)
            continue
        ik = _voorkeur(conn, rel, regel)
        hij = _voorkeur(conn, blijvend, regel)
        if hij < ik:
            motivatie = (f"{DUBBEL_REDEN}: {regel} als #{blijvend['id']} "
                         f"({blijvend['relation_type']}) — dat verband blijft")
            return True, [], motivatie, blijvend
    return False, ["dit is het verband dat blijft (of het andere is niet gedragen, of alleen dit "
                   "verband keurde een mens goed)"], None, None


def dubbele_verbanden(conn, limiet=None) -> list[int]:
    """Goedgekeurde verbanden die mogelijk dubbel zijn (de server beslist): kandidaat-paren
    met hetzelfde paar in een richting of beide richtingen."""
    rijen = conn.execute("""
        SELECT DISTINCT r.id FROM relations r JOIN relations o
          ON o.id <> r.id AND o.status = 'goedgekeurd' AND NOT o.vervangen
         AND ((o.source_id = r.source_id AND o.target_id = r.target_id)
              OR (o.source_id = r.target_id AND o.target_id = r.source_id))
        WHERE r.status = 'goedgekeurd' AND NOT r.vervangen
        ORDER BY r.id DESC""").fetchall()
    ids = [r[0] for r in rijen]
    return ids[:limiet] if limiet else ids


# ------------------------------------------------------------------ bronnen
def url_sleutel(url: str | None) -> str | None:
    """Dezelfde pagina, ongeacht schema, www, hoofdletters in de host, een slash op het eind,
    het fragment of tracking-parameters."""
    if not url or not url.strip():
        return None
    try:
        d = urlsplit(url.strip())
    except ValueError:
        return None
    if not d.netloc:
        return None
    host = d.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    pad = d.path.rstrip("/") or ""
    query = urlencode(sorted((k, v) for k, v in parse_qsl(d.query, keep_blank_values=True)
                             if not k.lower().startswith(TRACKING)))
    return host + pad + (f"?{query}" if query else "")


def bronnen_per_url(conn) -> dict[str, list[int]]:
    """{url-sleutel: [bron-ids, oudste eerst]} voor elke url met meer dan één bron."""
    groepen: dict[str, set[int]] = {}
    for sid, loc in conn.execute("""SELECT source_id, location FROM source_locations
                                    WHERE location_type = 'url'"""):
        sleutel = url_sleutel(loc)
        if sleutel:
            groepen.setdefault(sleutel, set()).add(sid)
    return {k: sorted(v) for k, v in groepen.items() if len(v) > 1}


def bron_met_url(conn, url) -> int | None:
    """Een bestaande bron met dezelfde url (de oudste), of None."""
    sleutel = url_sleutel(url)
    if not sleutel:
        return None
    for sid, loc in conn.execute("""SELECT source_id, location FROM source_locations
                                    WHERE location_type = 'url' ORDER BY source_id"""):
        if url_sleutel(loc) == sleutel:
            return sid
    return None


def bron_dubbel_besluit(conn, sid):
    """Is bron ``sid`` een latere kopie van een andere bron met dezelfde url? → (ok, redenen,
    blijvende bron-id)."""
    if conn.execute("SELECT 1 FROM sources WHERE id = ?", (sid,)).fetchone() is None:
        return False, ["niet gevonden"], None
    eigen = {url_sleutel(r[0]) for r in conn.execute(
        "SELECT location FROM source_locations WHERE source_id = ? AND location_type = 'url'",
        (sid,))} - {None}
    if not eigen:
        return False, ["bron heeft geen url"], None
    for groep in bronnen_per_url(conn).items():
        sleutel, ids = groep
        if sleutel in eigen and ids[0] != sid:
            return True, [], ids[0]
    return False, ["geen oudere bron met dezelfde url"], None


def voeg_bron_samen(conn, dubbel, blijvend) -> dict:
    """Verhuis alles van bron ``dubbel`` naar ``blijvend`` en verwijder ``dubbel``. → wat er
    verhuisde, plus de oude rij (voor edit_log, terug te zetten)."""
    oud = dict(conn.execute("SELECT * FROM sources WHERE id = ?", (dubbel,)).fetchone())
    oud["locaties"] = [dict(r) for r in conn.execute(
        "SELECT location_type, location FROM source_locations WHERE source_id = ?", (dubbel,))]
    uit = {"citaties": 0, "citaties_dubbel": 0, "vermeldingen": 0, "oordelen": 0, "locaties": 0}
    for c in conn.execute("SELECT * FROM citations WHERE source_id = ?", (dubbel,)).fetchall():
        al = conn.execute("""SELECT id, quote FROM citations WHERE argument_id = ? AND source_id = ?""",
                          (c["argument_id"], blijvend)).fetchone()
        if al and (al["quote"] or "").strip() == (c["quote"] or "").strip():
            # hetzelfde citaat uit dezelfde pagina: één citatie is genoeg
            conn.execute("DELETE FROM citations WHERE id = ?", (c["id"],))
            uit["citaties_dubbel"] += 1
        else:
            conn.execute("UPDATE citations SET source_id = ? WHERE id = ?", (blijvend, c["id"]))
            uit["citaties"] += 1
    for m in conn.execute("SELECT * FROM source_mentions WHERE source_id = ?", (dubbel,)).fetchall():
        conn.execute("INSERT OR IGNORE INTO source_mentions (source_id, entity_id, context) "
                     "VALUES (?, ?, ?)", (blijvend, m["entity_id"], m["context"]))
        uit["vermeldingen"] += 1
    conn.execute("DELETE FROM source_mentions WHERE source_id = ?", (dubbel,))
    uit["oordelen"] = conn.execute("UPDATE immuun_oordelen SET bron_id = ? WHERE bron_id = ?",
                                   (blijvend, dubbel)).rowcount
    bestaand = {(r[0], r[1]) for r in conn.execute(
        "SELECT location_type, location FROM source_locations WHERE source_id = ?", (blijvend,))}
    for loc in oud["locaties"]:
        if (loc["location_type"], loc["location"]) not in bestaand:
            conn.execute("INSERT INTO source_locations (source_id, location_type, location) "
                         "VALUES (?, ?, ?)", (blijvend, loc["location_type"], loc["location"]))
            uit["locaties"] += 1
    conn.execute("DELETE FROM source_locations WHERE source_id = ?", (dubbel,))
    conn.execute("DELETE FROM sources WHERE id = ?", (dubbel,))
    return {"verhuisd": uit, "oud": json.loads(json.dumps(oud, default=str))}
