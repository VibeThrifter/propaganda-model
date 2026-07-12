#!/usr/bin/env python3
"""
Trap 2 — in kaart brengen: genormaliseerd profiel-JSON → voorstellen in het model.

Dit is de schone, testbare helft. Ze leest het JSON dat trap 1 (of welke scraper dan
ook) schreef en dient via de REST-API voorstellen in, exact als een menselijke scout:
alles landt als `voorgesteld`, telt in niets, en wacht op een menselijke reviewer.
Ze raakt de database nooit rechtstreeks aan om te schrijven — alleen lezen (id's opzoeken,
zoals de scout-brief toestaat).

Modelleerdiscipline (CLAUDE.md, PAX-draaideurdiscussie):
  * Een loopbaan = een reeks **gedateerde persoon→organisatie-affiliaties**
    (personeel/bestuurder/adviseur/woordvoerder_van), instanties van
    `draaideurconstructie`. De org↔org-band is de **vanzelf afgeleide brug** — die
    slaan we NOOIT als edge op.
  * Opleidingen → persoon→onderwijsinstelling (`lidmaatschap`), mechanisme-loos =
    **kandidaat** (incubeert; een reviewer beslist of het `academische_socialisatie`
    instantieert — dat werkt alleen op opleidingsniveau voor journalisten).
  * Clubs/lidmaatschappen → persoon→org (`lidmaatschap`), óók kandidaat.
  * Assen guilty-until-proven: we zetten géén certainty/influence (de 0,05-vloer valt
    vanzelf in); de score komt uit het bewijs.
  * Bron = het LinkedIn-profiel zelf: **zelf-gerapporteerd**, dus voorgestelde
    betrouwbaarheid 'grijs'. We classificeren niet gezaghebbend (reviewerwerk).

Gebruik:
    # Droogloop (schrijft niets — laat zien wat er zou worden voorgesteld):
    python3 tools/linkedin/linkedin_naar_model.py data/linkedin/<slug>.json

    # Echt indienen (alles 'voorgesteld', onder het scout-account):
    python3 tools/linkedin/linkedin_naar_model.py data/linkedin/<slug>.json --indienen

Opties: --volledig (ook opleidingen+lidmaatschappen), --met-opleiding, --met-lidmaatschappen,
--alles-kandidaat (geen mechanisme toewijzen), --persoon-rol <naam>, --api, --token.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import normalize  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "propaganda_model.db"
DEFAULT_TOKEN = ROOT / "data" / "tokens" / "scout-agent.token"

# Structureel entiteittype per herkomst (schema.sql). Bewust conservatief: een reviewer
# corrigeert het type bij de review; de mapper mag niet gokken naar functie.
TYPE_ERVARING = "bedrijf"            # werkgever — vaak, niet altijd, een bedrijf
TYPE_OPLEIDING = "onderwijsinstelling"
TYPE_LIDMAATSCHAP = "stichting"      # generieke vereniging/stichting; te bevestigen


class Api:
    """Dunne REST-client (stdlib). Alleen nodig bij --indienen."""

    def __init__(self, basis: str, token: str | None):
        self.basis = basis.rstrip("/")
        self.token = token

    def _call(self, method: str, pad: str, body: dict | None = None):
        # Bij een rate-limit (bijdrager = 30 schrijfacties/min) even wachten en opnieuw,
        # zodat een groot profiel niet halverwege afbreekt.
        for poging in range(5):
            status, res = self._eenmalig(method, pad, body)
            geraakt = status == 429 or "rate limit" in str(res.get("error", "")).lower()
            if geraakt and poging < 4:
                print("    ⏳ rate limit bereikt — 62s wachten en opnieuw…")
                time.sleep(62)
                continue
            return status, res
        return status, res

    def _eenmalig(self, method: str, pad: str, body: dict | None):
        url = f"{self.basis}{pad}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode() or "{}")
            except Exception:
                return e.code, {"error": str(e)}
        except urllib.error.URLError as e:
            sys.exit(f"Kan de API niet bereiken op {self.basis} ({e}). "
                     f"Draai de server: python3 server.py")

    def get(self, pad):
        return self._call("GET", pad)

    def post(self, pad, body):
        return self._call("POST", pad, body)


def laad_entiteiten() -> dict[str, int]:
    """Naam → id voor álle entiteiten (elke status), zodat we duplicaten vermijden en
    bestaande knopen hergebruiken. Alleen-lezen — schrijven gaat altijd via de API."""
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT name, id FROM entities").fetchall()
    finally:
        conn.close()
    return {naam: eid for naam, eid in rows}


def laad_relaties() -> set:
    """(source_id, target_id, relation_type)-set van álle bestaande relaties, zodat een
    herstart (bv. na een rate-limit) geen dubbele relaties aanmaakt. Alleen-lezen."""
    if not DB_PATH.exists():
        return set()
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT source_id, target_id, relation_type FROM relations").fetchall()
    finally:
        conn.close()
    return {tuple(r) for r in rows}


def draaideur_mechanisme_id() -> int | None:
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT id FROM mechanisms WHERE name = 'draaideurconstructie'").fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def rol_id_voor_naam(api: Api, naam: str) -> int | None:
    status, rollen = api.get("/api/roles")
    if status != 200 or not isinstance(rollen, list):
        return None
    naam_l = naam.strip().lower()
    for r in rollen:
        if str(r.get("name", "")).lower() == naam_l:
            return r.get("id")
    return None


class Planner:
    """Bouwt de lijst voorstellen op en voert ze (bij --indienen) in de juiste volgorde
    uit: bron → entiteit → relatie → argument. In droogloop print 'ie alleen het plan."""

    def __init__(self, api: Api | None, bestaand: dict[str, int], draaideur_id: int | None,
                 indienen: bool, alles_kandidaat: bool, persoon_rol_id: int | None):
        self.api = api
        self.bestaand = dict(bestaand)          # naam → id (groeit tijdens de run)
        self.bestaande_relaties = laad_relaties()  # (bron,doel,type) — voorkomt dubbele edges
        self.draaideur_id = draaideur_id
        self.indienen = indienen
        self.alles_kandidaat = alles_kandidaat
        self.persoon_rol_id = persoon_rol_id
        self.regels: list[str] = []
        self.telling = {"bron": 0, "entiteit": 0, "relatie": 0, "argument": 0,
                        "overgeslagen": 0, "fout": 0}

    def log(self, regel: str):
        self.regels.append(regel)
        print(regel)

    # -- lage-niveau helpers -----------------------------------------------------
    def _bron(self, naam: str, url: str | None) -> int | None:
        titel = f"LinkedIn-profiel: {naam}"
        if not self.indienen:
            self.log(f"  [bron]      «{titel}» (website, grijs){' → ' + url if url else ''}")
            self.telling["bron"] += 1
            return -1
        body = {"title": titel, "source_type": "website",
                "reliability_voorgesteld": "grijs", "onderwerp_voorgesteld": "onbepaald"}
        if url:
            body["location"] = {"type": "url", "value": url}
        status, res = self.api.post("/api/sources", body)
        if status in (200, 201) and res.get("id"):
            hergebruikt = " (hergebruikt)" if res.get("hergebruikt") else ""
            self.log(f"  [bron #{res['id']}] «{titel}»{hergebruikt}")
            self.telling["bron"] += 1
            return res["id"]
        self.log(f"  [bron FOUT] {res.get('error')}")
        self.telling["fout"] += 1
        return None

    def _entiteit(self, naam: str, etype: str, beschrijving: str,
                  rol_id: int | None = None) -> int | None:
        if naam in self.bestaand:
            self.log(f"  [entiteit]  «{naam}» bestaat al (#{self.bestaand[naam]})")
            return self.bestaand[naam]
        if not self.indienen:
            self.log(f"  [entiteit+] «{naam}» ({etype})")
            self.telling["entiteit"] += 1
            self.bestaand[naam] = -1
            return -1
        body = {"name": naam, "type": etype, "description": beschrijving}
        if rol_id:
            body["primary_role_id"] = rol_id
        status, res = self.api.post("/api/entities", body)
        if status == 201 and res.get("id"):
            self.log(f"  [entiteit+ #{res['id']}] «{naam}» ({etype})")
            self.telling["entiteit"] += 1
            self.bestaand[naam] = res["id"]
            return res["id"]
        # Bestond toch al (UNIQUE) → resolve uit een verse DB-lezing.
        if status == 400 and "bestaat al" in str(res.get("error", "")):
            eid = laad_entiteiten().get(naam)
            if eid:
                self.bestaand[naam] = eid
                self.log(f"  [entiteit]  «{naam}» bestond al (#{eid})")
                return eid
        self.log(f"  [entiteit FOUT] «{naam}»: {res.get('error')}")
        self.telling["fout"] += 1
        return None

    def _relatie(self, bron_id: int, doel_id: int, rtype: str, mechanism_id: int | None,
                 beschrijving: str, van: str | None, tot: str | None) -> int | None:
        soort = "kandidaat" if mechanism_id is None else f"mech#{mechanism_id}"
        periode = f" [{van or '?'}–{tot or 'heden'}]" if (van or tot) else ""
        # Dedup: bestaat deze edge (bron,doel,type) al, sla 'm (en z'n argument) over —
        # zo maakt een herstart na een rate-limit geen dubbele relaties.
        if self.indienen and (bron_id, doel_id, rtype) in self.bestaande_relaties:
            self.log(f"  [relatie]   {rtype} ({soort}){periode} bestaat al — overgeslagen")
            self.telling["overgeslagen"] += 1
            return None
        if not self.indienen:
            self.log(f"  [relatie+]  {rtype} ({soort}){periode}")
            self.telling["relatie"] += 1
            return -1
        body = {"source_id": bron_id, "target_id": doel_id, "relation_type": rtype,
                "description": beschrijving}
        if mechanism_id is not None:
            body["mechanism_id"] = mechanism_id
        if van:
            body["active_from"] = van
        if tot:
            body["active_until"] = tot
        status, res = self.api.post("/api/relations", body)
        if status == 201 and res.get("id"):
            self.log(f"  [relatie+ #{res['id']}] {rtype} ({soort}){periode}")
            self.telling["relatie"] += 1
            self.bestaande_relaties.add((bron_id, doel_id, rtype))
            return res["id"]
        self.log(f"  [relatie FOUT] {res.get('error')}")
        self.telling["fout"] += 1
        return None

    def _argument(self, relatie_id: int, claim: str, bron_id: int, quote: str | None):
        if not self.indienen:
            self.log(f"  [argument+] {claim[:88]}…")
            self.telling["argument"] += 1
            return
        citatie = {"source_id": bron_id}
        if quote:
            citatie["quote"] = quote[:600]
        body = {"claim": claim, "stance": "supporting", "relation_id": relatie_id,
                "citations": [citatie]}
        status, res = self.api.post("/api/arguments", body)
        if status in (200, 201) and res.get("id"):
            self.log(f"  [argument+ #{res['id']}] ok")
            self.telling["argument"] += 1
        elif status == 409:
            self.log("  [argument]  duplicaat, overgeslagen")
            self.telling["overgeslagen"] += 1
        else:
            self.log(f"  [argument FOUT] {res.get('error')}")
            self.telling["fout"] += 1

    # -- hoog-niveau: één affiliatie (ervaring/opleiding/lidmaatschap) ------------
    def _affiliatie(self, persoon_id: int, persoon_naam: str, bron_id: int,
                    org_naam: str, org_type: str, org_desc: str,
                    rtype: str, mechanism_id: int | None,
                    van: str | None, tot: str | None,
                    claim: str, quote: str | None):
        doel_id = self._entiteit(org_naam, org_type, org_desc)
        if not doel_id:
            return
        # In droogloop zijn id's -1; sla de POST-afhankelijke stappen dan symbolisch over.
        rel_id = self._relatie(persoon_id, doel_id, rtype, mechanism_id,
                               f"Afgeleid uit LinkedIn: {claim}", van, tot)
        if rel_id:
            self._argument(rel_id, claim, bron_id, quote)

    def verwerk(self, profiel: dict, met_opleiding: bool, met_lidmaatschappen: bool):
        pers = profiel.get("persoon") or {}
        naam = pers.get("naam") or (profiel.get("bron", {}).get("linkedin_url") or "onbekend")
        url = (profiel.get("bron") or {}).get("linkedin_url")

        self.log(f"\n=== {naam} ===")
        bron_id = self._bron(naam, url)
        if not bron_id:
            return

        over = (pers.get("over") or pers.get("kop") or "")
        p_desc = (f"Persoon; afgeleid uit LinkedIn. {over}"[:400]).strip()
        persoon_id = self._entiteit(naam, "persoon", p_desc, rol_id=self.persoon_rol_id)
        if not persoon_id:
            return

        # 1) Ervaringen → gedateerde persoon→org-affiliaties (instanties van draaideur).
        for erv in profiel.get("ervaringen", []):
            org = erv["organisatie"]
            functie = erv.get("functie")
            rtype = normalize.relatietype_voor_functie(functie)
            mech = None if self.alles_kandidaat else self.draaideur_id
            periode = f"({erv.get('van') or '?'}–{erv.get('tot') or 'heden'})"
            functie_tekst = functie or "verbonden"
            claim = (f"{naam} was volgens het eigen LinkedIn-profiel {functie_tekst} "
                     f"bij {org} {periode}. Zelf-gerapporteerd (LinkedIn), lage betrouwbaarheid.")
            self._affiliatie(persoon_id, naam, bron_id, org, TYPE_ERVARING,
                             f"Werkgever/organisatie van {naam} volgens LinkedIn; "
                             f"structureel type te bevestigen door reviewer.",
                             rtype, mech, erv.get("van"), erv.get("tot"),
                             claim, erv.get("beschrijving"))

        # 2) Opleidingen → persoon→onderwijsinstelling (kandidaat).
        if met_opleiding:
            for opl in profiel.get("opleidingen", []):
                inst = opl["instelling"]
                graad = opl.get("graad")
                periode = f"({opl.get('van') or '?'}–{opl.get('tot') or '?'})"
                graad_tekst = f"{graad} " if graad else ""
                claim = (f"{naam} studeerde volgens het eigen LinkedIn-profiel {graad_tekst}"
                         f"aan {inst} {periode}. Zelf-gerapporteerd (LinkedIn).")
                self._affiliatie(persoon_id, naam, bron_id, inst, TYPE_OPLEIDING,
                                 f"Onderwijsinstelling; opleiding van {naam} volgens LinkedIn. "
                                 f"Reviewer beoordeelt of dit op opleidingsniveau "
                                 f"academische_socialisatie instantieert.",
                                 "lidmaatschap", None, opl.get("van"), opl.get("tot"),
                                 claim, opl.get("beschrijving"))

        # 3) Lidmaatschappen/clubs → persoon→org (kandidaat).
        if met_lidmaatschappen:
            for lid in profiel.get("lidmaatschappen", []):
                org = lid["organisatie"]
                claim = (f"{naam} is/was volgens het eigen LinkedIn-profiel verbonden aan "
                         f"{org} ({lid.get('herkomst', 'lidmaatschap')}). Zelf-gerapporteerd (LinkedIn).")
                self._affiliatie(persoon_id, naam, bron_id, org, TYPE_LIDMAATSCHAP,
                                 f"Organisatie/club waar {naam} lid van is volgens LinkedIn; "
                                 f"structureel type te bevestigen.",
                                 "lidmaatschap", None, None, None,
                                 claim, None)

    def samenvatting(self):
        t = self.telling
        modus = "INGEDIEND" if self.indienen else "DROOGLOOP (niets geschreven)"
        print(f"\n— {modus} — bronnen: {t['bron']}, entiteiten: {t['entiteit']}, "
              f"relaties: {t['relatie']}, argumenten: {t['argument']}, "
              f"overgeslagen: {t['overgeslagen']}, fouten: {t['fout']}")
        if not self.indienen:
            print("  Voeg --indienen toe om deze voorstellen echt in te dienen "
                  "(alles landt als 'voorgesteld' en wacht op een reviewer).")


def main():
    p = argparse.ArgumentParser(description="LinkedIn-profiel-JSON → modelvoorstellen.",
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=__doc__)
    p.add_argument("json", type=Path, help="genormaliseerd profiel-JSON (uit scrape_profile.py)")
    p.add_argument("--indienen", action="store_true", help="daadwerkelijk indienen (default: droogloop)")
    p.add_argument("--volledig", action="store_true", help="ook opleidingen én lidmaatschappen")
    p.add_argument("--met-opleiding", action="store_true", help="ook opleidingen meenemen")
    p.add_argument("--met-lidmaatschappen", action="store_true", help="ook clubs/lidmaatschappen")
    p.add_argument("--alles-kandidaat", action="store_true",
                   help="ken géén mechanisme toe (alle relaties als kandidaat)")
    p.add_argument("--persoon-rol", help="rol-naam voor de persoon-knoop (bv. 'journalist')")
    p.add_argument("--api", default="http://localhost:5000", help="basis-URL van de API")
    p.add_argument("--token", type=Path, default=DEFAULT_TOKEN, help="pad naar het Bearer-token")
    args = p.parse_args()

    if not args.json.exists():
        sys.exit(f"Bestand niet gevonden: {args.json}")
    profiel = json.loads(args.json.read_text(encoding="utf-8"))
    if profiel.get("type") != "persoon":
        sys.exit("Dit script verwacht een persoonsprofiel (type='persoon').")

    # Herken een 'kapotte scrape' (meestal: verlopen LinkedIn-sessie). Dan bevat het JSON
    # geen loopbaan en heet de persoon vaak naar de authwall ('Aanmelden'/'Sign Up'). Zonder
    # deze check zou de mapper stil 0 voorstellen doen; nu geeft 'ie de agent — en die de
    # eigenaar — het exacte login-commando door (dat de eigenaar niet hoeft te onthouden).
    naam = ((profiel.get("persoon") or {}).get("naam") or "").strip()
    geen_loopbaan = not profiel.get("ervaringen") and not profiel.get("opleidingen")
    authwall_naam = (not naam) or bool(re.search(
        r"aanmelden|sign\s*up|word lid|join linkedin|log\s*in|^linkedin$", naam, re.I))
    if geen_loopbaan and authwall_naam:
        sys.exit(normalize.sessie_verlopen_bericht(
            f"Het gescrapete JSON ({args.json.name}) bevat geen loopbaan en de naam "
            f"('{naam or '—'}') lijkt op de LinkedIn-authwall — de scrape is vermoedelijk "
            f"mislukt door een verlopen sessie."))
    if geen_loopbaan:
        print(f"⚠ Geen ervaringen én geen opleidingen in {args.json.name}. Is het profiel "
              f"echt zo leeg, of is de LinkedIn-sessie verlopen? Zo ja, laat de eigenaar "
              f"draaien: {normalize.SESSIE_LOGIN_COMMANDO}")

    met_opleiding = args.volledig or args.met_opleiding
    met_lidmaatschappen = args.volledig or args.met_lidmaatschappen

    api = None
    persoon_rol_id = None
    if args.indienen:
        if not args.token.exists():
            sys.exit(f"Token niet gevonden: {args.token}. Maak een scout-account met "
                     f"scripts/create_user.py of wijs met --token naar een bestaand token.")
        api = Api(args.api, args.token.read_text().strip())
    else:
        api = Api(args.api, None)  # alleen voor GET /api/roles bij --persoon-rol

    if args.persoon_rol:
        persoon_rol_id = rol_id_voor_naam(api, args.persoon_rol)
        if persoon_rol_id is None:
            print(f"⚠ rol '{args.persoon_rol}' niet gevonden; persoon-knoop krijgt geen rol.")

    planner = Planner(api=api, bestaand=laad_entiteiten(),
                      draaideur_id=draaideur_mechanisme_id(),
                      indienen=args.indienen, alles_kandidaat=args.alles_kandidaat,
                      persoon_rol_id=persoon_rol_id)
    if not met_opleiding:
        print("(opleidingen overgeslagen — voeg --met-opleiding of --volledig toe)")
    if not met_lidmaatschappen:
        print("(lidmaatschappen overgeslagen — voeg --met-lidmaatschappen of --volledig toe)")
    planner.verwerk(profiel, met_opleiding, met_lidmaatschappen)
    planner.samenvatting()


if __name__ == "__main__":
    main()
