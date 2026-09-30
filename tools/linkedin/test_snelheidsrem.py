#!/usr/bin/env python3
"""
Test van de LinkedIn-snelheidsrem (Epic 12, story 12.2) — zonder netwerk, zonder
browser: een nep-klok en een tijdelijk toestandsbestand. Plus de pure parsers uit
extract.py (people-search + blokkadedetectie) tegen fixtures.

Dekt: uur- en dagmaximum per soort (apart geteld), actieve uren 08–22, stroomonderbreker
(24u → verdubbeling → max 7 dagen, reset na een geslaagde dag), env-overrides (alleen
strenger), kill-switch (env + persistent), de exacte status-JSON-vorm, persistentie via
het bestand (tweede instantie ziet dezelfde toestand), de weiger-/blokkademeldingen.

Gebruik: python3 tools/linkedin/test_snelheidsrem.py
Exit-code 0 = alles groen.
"""
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import extract  # noqa: E402
import snelheidsrem as sr  # noqa: E402


def eis(conditie, melding):
    if not conditie:
        sys.exit(f"FAAL: {melding}")
    print(f"  ok — {melding}")


class Klok:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t

    def plus(self, **kw):
        self.t = self.t + dt.timedelta(**kw)


def maak(tmp, klok, env=None, naam="rem.json"):
    return sr.Snelheidsrem(pad=Path(tmp) / naam, klok=klok, env=env or {})


def main():
    with tempfile.TemporaryDirectory() as tmp:
        print("1. Uur- en dagmaximum (per soort apart)")
        klok = Klok(dt.datetime(2026, 9, 30, 9, 0, 0))
        rem = maak(tmp, klok)
        ok, reden, volgende = rem.mag_nu("profiel")
        eis(ok and reden is None and volgende is None, "eerste profiel om 09:00 mag")
        rem.registreer("profiel")
        klok.plus(minutes=10)
        eis(rem.mag_nu("profiel")[0], "tweede profiel binnen het uur mag (2/uur)")
        rem.registreer("profiel")
        klok.plus(minutes=5)
        ok, reden, volgende = rem.mag_nu("profiel")
        eis(not ok and "uurmaximum" in reden, f"derde binnen het uur geweigerd ({reden})")
        eis(volgende == dt.datetime(2026, 9, 30, 10, 0, 1),
            f"volgende kans = oudste + 1 uur ({volgende})")
        eis(rem.mag_nu("zoek")[0], "zoek telt apart: mag nog")
        klok.t = dt.datetime(2026, 9, 30, 10, 0, 1)
        eis(rem.mag_nu("profiel")[0], "na het glijdende uur mag het weer")
        # Vul de dag: tot 10 profielen (steeds 2 per uur).
        klok.t = dt.datetime(2026, 9, 30, 10, 5)
        for _ in range(8):
            ok, _, volgende = rem.mag_nu("profiel")
            if not ok:
                klok.t = volgende
            rem.registreer("profiel")
            klok.plus(minutes=1)
        st = rem.status()
        eis(st["profiel"]["dag"] == 10, f"10 profielen vandaag geteld ({st['profiel']})")
        ok, reden, volgende = rem.mag_nu("profiel")
        eis(not ok and "dagmaximum" in reden and volgende == dt.datetime(2026, 10, 1, 8, 0),
            f"11e geweigerd, volgende kans morgen 08:00 ({reden}; {volgende})")

        print("2. Actieve uren 08–22")
        klok2 = Klok(dt.datetime(2026, 9, 30, 7, 59))
        rem2 = maak(tmp, klok2, naam="uren.json")
        ok, reden, volgende = rem2.mag_nu("zoek")
        eis(not ok and "actieve uren" in reden and volgende == dt.datetime(2026, 9, 30, 8, 0),
            f"07:59 geweigerd, kans 08:00 ({volgende})")
        klok2.t = dt.datetime(2026, 9, 30, 21, 59)
        eis(rem2.mag_nu("zoek")[0], "21:59 mag")
        klok2.t = dt.datetime(2026, 9, 30, 22, 0)
        ok, _, volgende = rem2.mag_nu("zoek")
        eis(not ok and volgende == dt.datetime(2026, 10, 1, 8, 0),
            f"22:00 geweigerd, kans morgen 08:00 ({volgende})")

        print("3. Stroomonderbreker: 24u, verdubbeling, max 7 dagen, reset na geslaagde dag")
        klok3 = Klok(dt.datetime(2026, 9, 30, 12, 0))
        rem3 = maak(tmp, klok3, naam="blok.json")
        tot = rem3.blokkeer("checkpoint")
        eis(tot == dt.datetime(2026, 10, 1, 12, 0) and rem3.niveau() == 1,
            f"eerste blokkade: 24 uur ({tot})")
        ok, reden, volgende = rem3.mag_nu("profiel")
        eis(not ok and "stroomonderbreker" in reden and volgende == tot,
            f"tijdens blokkade alles geweigerd ({reden})")
        eis(not rem3.mag_nu("zoek")[0], "ook zoek geweigerd tijdens blokkade")
        st = rem3.status()
        eis(st["geblokkeerd_tot"] == "2026-10-01T12:00:00" and st["reden"] == "checkpoint",
            "status toont geblokkeerd_tot + reden")
        klok3.t = tot
        eis(rem3.mag_nu("profiel")[0], "na afloop mag het weer")
        rem3.registreer("profiel")              # eerste geslaagde actie na de blokkade
        klok3.plus(hours=2)
        tot2 = rem3.blokkeer("captcha")         # herhaling vóór een geslaagde dag
        eis(rem3.niveau() == 2 and tot2 - klok3.t == dt.timedelta(hours=48),
            f"herhaling: verdubbeld naar 48 uur (niveau {rem3.niveau()})")
        for verwacht in (96, 168, 168):
            klok3.t = rem3._vroegst(rem3._lees(), "profiel", klok3.t)  # na afloop
            nu = klok3.t
            t = rem3.blokkeer("authwall")
            eis(t - nu == dt.timedelta(hours=verwacht),
                f"niveau {rem3.niveau()}: {verwacht} uur (max 7 dagen)")
        # Geslaagde dag → niveau terug naar 0.
        klok3.t = rem3._vroegst(rem3._lees(), "profiel", klok3.t)
        rem3.registreer("profiel")
        klok3.plus(hours=23)
        rem3.registreer("zoek")
        eis(rem3.niveau() == 5, "na 23 uur nog geen reset")
        klok3.plus(hours=1, minutes=1)
        rem3.status()
        eis(rem3.niveau() == 0, "na een geslaagde dag (24 uur) is het niveau terug op 0")
        t = rem3.blokkeer("checkpoint")
        eis(t - klok3.t == dt.timedelta(hours=24), "nieuwe blokkade begint weer op 24 uur")
        rem3.reset_blokkade()
        eis(rem3.niveau() == 0 and rem3.status()["geblokkeerd_tot"] is None,
            "reset-blokkade (eigenaar) heft blokkade + niveau op")

        print("4. Env-overrides (alleen strenger) + kill-switch")
        klok4 = Klok(dt.datetime(2026, 9, 30, 12, 0))
        rem4 = maak(tmp, klok4, env={"LINKEDIN_MAX_PER_UUR": "1", "LINKEDIN_MAX_PER_DAG": "3",
                                     "LINKEDIN_ACTIEF_VAN": "9", "LINKEDIN_ACTIEF_TOT": "18"},
                    naam="env.json")
        eis((rem4.max_per_uur, rem4.max_per_dag, rem4.actief_van, rem4.actief_tot)
            == (1, 3, 9, 18), "strengere env-waarden worden overgenomen")
        rem4.registreer("zoek")
        eis(not rem4.mag_nu("zoek")[0], "LINKEDIN_MAX_PER_UUR=1 → tweede zoek geweigerd")
        klok4.t = dt.datetime(2026, 9, 30, 18, 30)
        eis(not rem4.mag_nu("profiel")[0], "LINKEDIN_ACTIEF_TOT=18 → 18:30 geweigerd")
        rem5 = maak(tmp, klok4, env={"LINKEDIN_MAX_PER_UUR": "50", "LINKEDIN_MAX_PER_DAG": "500",
                                     "LINKEDIN_ACTIEF_VAN": "0", "LINKEDIN_ACTIEF_TOT": "24"},
                    naam="ruim.json")
        eis((rem5.max_per_uur, rem5.max_per_dag, rem5.actief_van, rem5.actief_tot)
            == (2, 10, 8, 22), "ruimere env-waarden worden begrensd op het eigenaarsplafond")
        rem6 = maak(tmp, klok4, env={"LINKEDIN_AUTOMATISCH": "0"}, naam="kill.json")
        klok4.t = dt.datetime(2026, 9, 30, 12, 0)
        ok, reden, volgende = rem6.mag_nu("profiel")
        eis(not ok and "kill-switch" in reden and volgende is None,
            f"LINKEDIN_AUTOMATISCH=0 → geweigerd, geen volgende kans ({reden})")
        st = rem6.status()
        eis(st["automatisch"] is False and st["volgende_kans"] is None,
            "status: automatisch false, volgende_kans null")
        rem7 = maak(tmp, klok4, naam="kill2.json")
        rem7.zet_automatisch(False)
        eis(not rem7.mag_nu("zoek")[0], "persistente kill-switch ('uit') weigert")
        rem7.zet_automatisch(True)
        eis(rem7.mag_nu("zoek")[0], "'aan' zet het weer aan")

        print("5. Status-JSON-vorm (contract) + persistentie")
        klok8 = Klok(dt.datetime(2026, 9, 30, 12, 0))
        rem8 = maak(tmp, klok8, naam="status.json")
        st = rem8.status()
        eis(set(st) == {"automatisch", "actief_nu", "geblokkeerd_tot", "reden", "profiel",
                        "zoek", "volgende_kans"}, f"exacte sleutels ({sorted(st)})")
        eis(st["profiel"] == {"uur": 0, "dag": 0, "max_uur": 2, "max_dag": 10}
            and st["zoek"] == {"uur": 0, "dag": 0, "max_uur": 2, "max_dag": 10},
            "per soort: uur/dag/max_uur/max_dag")
        eis(st["automatisch"] is True and st["actief_nu"] is True
            and st["geblokkeerd_tot"] is None and st["reden"] is None
            and st["volgende_kans"] is None, "verse toestand: alles mag nu (volgende_kans null)")
        json.dumps(st)  # serialiseerbaar
        rem8.registreer("profiel")
        rem8.registreer("profiel")
        tweede = maak(tmp, klok8, naam="status.json")   # ander proces, zelfde bestand
        st2 = tweede.status()
        eis(st2["profiel"]["uur"] == 2 and st2["volgende_kans"] == "2026-09-30T13:00:01",
            f"tweede instantie leest dezelfde toestand; volgende_kans ISO ({st2['volgende_kans']})")
        eis((Path(tmp) / "status.json").exists()
            and json.loads((Path(tmp) / "status.json").read_text())["gebeurtenissen"]["profiel"],
            "toestand staat op schijf (JSON)")
        klok8.plus(hours=49)
        tweede.registreer("zoek")
        eis(json.loads((Path(tmp) / "status.json").read_text())["gebeurtenissen"]["profiel"] == [],
            "oude gebeurtenissen (> 48 uur) worden opgeruimd")

        print("6. Meldingen (door de runner herkend)")
        m = sr.rem_bericht("uurmaximum", dt.datetime(2026, 9, 30, 13, 5),
                           nu=dt.datetime(2026, 9, 30, 12, 0))
        eis(m.startswith("⏳ LINKEDIN-SNELHEIDSREM — volgende kans 13:05"), m.splitlines()[0])
        m = sr.blokkade_bericht("checkpoint", dt.datetime(2026, 10, 1, 12, 0))
        eis(m.startswith("⛔ LINKEDIN-BLOKKADE — checkpoint") and "reset-blokkade" in m,
            m.splitlines()[0])
        eis(sr.EXIT_REM == 75 and sr.EXIT_BLOKKADE == 76, "exit-codes 75/76")
        p = sr.pauze(4.0)
        eis(0 < p < 12, f"pauze() is willekeurig maar begrensd ({p:.2f}s)")

    print("7. Parser people-search (fixtures, geen netwerk)")
    tekst = (HIER / "fixtures" / "zoek_personen_nl.txt").read_text(encoding="utf-8")
    links = json.loads((HIER / "fixtures" / "zoek_personen_links.json").read_text(encoding="utf-8"))
    res = extract.parse_zoekresultaten(tekst, links, max_n=5)
    eis([r["url"] for r in res] == ["https://www.linkedin.com/in/anouk-verbeek-12ab34/",
                                    "https://www.linkedin.com/in/averbeek/",
                                    "https://www.linkedin.com/in/bram-de-wit-9x/"],
        f"drie profielen in paginavolgorde, zonder dubbelen/anoniem/bedrijfslink ({len(res)})")
    eis(res[0] == {"naam": "Anouk Verbeek",
                   "kop": "Wethouder Economie en Energie bij Gemeente Dijkerhoven",
                   "locatie": "Dijkerhoven, Groningen, Nederland",
                   "url": "https://www.linkedin.com/in/anouk-verbeek-12ab34/"},
        "eerste kaart: naam/kop/locatie correct")
    eis(res[1]["kop"] == "Beleidsadviseur duurzaamheid | fotografie"
        and res[1]["locatie"] == "Utrecht en omgeving",
        "naamgenoot krijgt z'n eigen kaart (niet die van de eerste)")
    eis(res[2]["naam"] == "Bram de Wit" and res[2]["kop"] == "Woordvoerder bij NordVind B.V.",
        "naam uit Engelse linktekst ('View … profile')")
    eis(len(extract.parse_zoekresultaten(tekst, links, max_n=1)) == 1, "--max begrenst")
    eis(extract.parse_zoekresultaten("", [], max_n=5) == [], "lege pagina → lege lijst")

    print("8. Blokkadedetectie (fixtures)")
    cp = (HIER / "fixtures" / "checkpoint_nl.txt").read_text(encoding="utf-8")
    eis(extract.blokkade_reden("https://www.linkedin.com/checkpoint/challenge/AgF") is not None,
        "URL /checkpoint → blokkade")
    eis(extract.blokkade_reden("https://www.linkedin.com/feed/", "LinkedIn", cp) is not None,
        "beveiligingscontrole-tekst → blokkade")
    eis(extract.blokkade_reden("https://www.linkedin.com/authwall?trk=x") is not None,
        "authwall midden in de sessie → blokkade")
    eis(extract.blokkade_reden("https://www.linkedin.com/authwall?trk=x",
                               authwall_is_blokkade=False) is None,
        "authwall op /feed/ = dode sessie (geen blokkade; oude melding blijft)")
    lang = ("Ervaring\n" + "Functie bij organisatie\n" * 200 + "unusual activity monitoring")
    eis(extract.blokkade_reden("https://www.linkedin.com/in/x/details/experience/",
                               "Jan | LinkedIn", lang) is None,
        "gewone profieltekst (trefwoord diep in de tekst) → geen vals alarm")

    print("\nALLE SNELHEIDSREM-TESTS GESLAAGD")


if __name__ == "__main__":
    main()
