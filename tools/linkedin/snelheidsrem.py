#!/usr/bin/env python3
"""
LinkedIn-snelheidsrem — de harde rem onder het AUTOMATISCHE LinkedIn-gebruik
(Epic 12 "Wie is dit?", eigenaarsbesluit 2026-09-30; wijzigt beleid J4).

De eigenaar stond automatisch LinkedIn-gebruik toe (voor de nieuws-scout), maar alléén
achter deze rem. Pure stdlib; gedeeld door `scrape_profile.py` (profiel-scrapes en
people-searches) en leesbaar voor de nieuws-backend (`status --json`).

Regels (per soort, apart geteld voor `profiel` en `zoek`):
  * max 2 per uur (glijdend venster van 60 min) en max 10 per dag (lokale kalenderdag);
  * alleen tussen 08:00 en 22:00 lokale tijd;
  * stroomonderbreker: bij een captcha/checkpoint/authwall stopt ALLES 24 uur; bij
    herhaling verdubbelt dat (48u, 96u, …) tot maximaal 7 dagen. Het niveau zakt terug
    naar 0 na een geslaagde dag (24 uur zonder nieuwe blokkade sinds de eerste
    geslaagde actie ná het verlopen van de blokkade);
  * kill-switch: env `LINKEDIN_AUTOMATISCH=0` of `snelheidsrem.py uit` → alles geweigerd.
Env-overrides `LINKEDIN_MAX_PER_UUR`, `LINKEDIN_MAX_PER_DAG`, `LINKEDIN_ACTIEF_VAN`,
`LINKEDIN_ACTIEF_TOT` mogen de rem alleen STRENGER maken (het eigenaarsplafond — 2/uur,
10/dag, 08–22 — is hard; ruimer vergt een bewuste code-wijziging).

Toestand: `data/linkedin/_snelheidsrem.json` (gitignored), vergrendeld met fcntl zodat
gelijktijdige processen elkaar niet overschrijven. De klok is injecteerbaar (tests).

CLI:
    python3 tools/linkedin/snelheidsrem.py status [--json]
    python3 tools/linkedin/snelheidsrem.py mag profiel|zoek     # exit 0 = mag, 75 = rem
    python3 tools/linkedin/snelheidsrem.py reset-blokkade       # eigenaar: na handmatige controle
    python3 tools/linkedin/snelheidsrem.py uit|aan              # persistente kill-switch

`status --json` geeft precies:
    {"automatisch": true, "actief_nu": true, "geblokkeerd_tot": null, "reden": null,
     "profiel": {"uur": 0, "dag": 0, "max_uur": 2, "max_dag": 10},
     "zoek": {"uur": 0, "dag": 0, "max_uur": 2, "max_dag": 10},
     "volgende_kans": null}
`volgende_kans` = het vroegste moment waarop zowel een zoekactie als een profiel-scrape
mag (null als dat nu al kan, of als automatisch gebruik uit staat).
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import fcntl
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PAD = ROOT / "data" / "linkedin" / "_snelheidsrem.json"

SOORTEN = ("profiel", "zoek")

# Eigenaarsplafond (2026-09-30) — env mag alleen strenger.
MAX_PER_UUR = 2
MAX_PER_DAG = 10
ACTIEF_VAN = 8     # uur (inclusief)
ACTIEF_TOT = 22    # uur (exclusief): om 22:00 stopt het
BLOKKADE_BASIS_UUR = 24
BLOKKADE_MAX_UUR = 7 * 24

EXIT_REM = 75        # EX_TEMPFAIL: later opnieuw proberen
EXIT_BLOKKADE = 76   # stroomonderbreker gesprongen


def _iso(t):
    return t.isoformat(timespec="seconds") if t else None


def _van_iso(s):
    if not s:
        return None
    try:
        return _dt.datetime.fromisoformat(s)
    except ValueError:
        return None


class Snelheidsrem:
    """De rem. Alle tijden zijn naïef-lokaal (zoals de klok van de Mac)."""

    def __init__(self, pad=None, klok=None, env=None):
        self.pad = Path(pad) if pad else DEFAULT_PAD
        self.klok = klok or _dt.datetime.now
        omg = os.environ if env is None else env
        # Env-overrides: alleen strenger dan het eigenaarsplafond.
        def lees(naam, default):
            w = omg.get(naam)
            if w is None or not str(w).strip():
                return default
            try:
                return int(w)
            except ValueError:
                return default
        self.max_per_uur = max(0, min(MAX_PER_UUR, lees("LINKEDIN_MAX_PER_UUR", MAX_PER_UUR)))
        self.max_per_dag = max(0, min(MAX_PER_DAG, lees("LINKEDIN_MAX_PER_DAG", MAX_PER_DAG)))
        self.actief_van = max(ACTIEF_VAN, min(24, lees("LINKEDIN_ACTIEF_VAN", ACTIEF_VAN)))
        self.actief_tot = min(ACTIEF_TOT, max(0, lees("LINKEDIN_ACTIEF_TOT", ACTIEF_TOT)))
        self.env_automatisch = str(omg.get("LINKEDIN_AUTOMATISCH", "1")).strip() != "0"

    # ── toestand (vergrendeld lezen/schrijven) ────────────────────────────
    @staticmethod
    def _leeg():
        return {"versie": 1, "automatisch": True,
                "gebeurtenissen": {s: [] for s in SOORTEN},
                "blokkade": {"tot": None, "reden": None, "sinds": None, "niveau": 0,
                             "eerste_succes_na": None}}

    def _lees(self):
        try:
            st = json.loads(self.pad.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return self._leeg()
        basis = self._leeg()
        if not isinstance(st, dict):
            return basis
        basis["automatisch"] = st.get("automatisch", True) is not False
        for s in SOORTEN:
            lijst = (st.get("gebeurtenissen") or {}).get(s) or []
            basis["gebeurtenissen"][s] = [x for x in lijst if isinstance(x, str)]
        if isinstance(st.get("blokkade"), dict):
            basis["blokkade"].update({k: st["blokkade"].get(k) for k in basis["blokkade"]})
            basis["blokkade"]["niveau"] = int(basis["blokkade"].get("niveau") or 0)
        return basis

    @contextlib.contextmanager
    def _vergrendeld(self):
        """Exclusieve fcntl-lock rond lees-wijzig-schrijf; schrijft atomair terug."""
        self.pad.parent.mkdir(parents=True, exist_ok=True)
        lockpad = self.pad.with_name(self.pad.name + ".lock")
        with open(lockpad, "a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                st = self._lees()
                yield st
                self._opruimen(st)
                tmp = self.pad.with_name(self.pad.name + ".tmp")
                tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(self.pad)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _opruimen(self, st):
        """Bewaar alleen gebeurtenissen van de laatste 48 uur (genoeg voor uur + dag)."""
        grens = self.klok() - _dt.timedelta(hours=48)
        for s in SOORTEN:
            st["gebeurtenissen"][s] = [x for x in st["gebeurtenissen"][s]
                                       if (_van_iso(x) or grens) > grens]

    def _herstel_niveau(self, st, nu):
        """Stroomonderbreker-niveau terug naar 0 na een geslaagde dag."""
        b = st["blokkade"]
        eerste = _van_iso(b.get("eerste_succes_na"))
        if b.get("niveau") and eerste and nu - eerste >= _dt.timedelta(hours=24):
            b.update({"niveau": 0, "eerste_succes_na": None, "tot": None, "reden": None,
                      "sinds": None})

    # ── rekenwerk ──────────────────────────────────────────────────────────
    def _actief_op(self, t):
        return self.actief_van <= t.hour < self.actief_tot

    def _volgende_start(self, t):
        """Vroegste moment ≥ t binnen de actieve uren."""
        if self._actief_op(t):
            return t
        start = t.replace(hour=0, minute=0, second=0, microsecond=0) + _dt.timedelta(
            hours=self.actief_van)
        if t < start:
            return start
        return start + _dt.timedelta(days=1)

    def _tellingen(self, st, soort, t):
        tijden = sorted(filter(None, (_van_iso(x) for x in st["gebeurtenissen"][soort])))
        uur = [x for x in tijden if t - _dt.timedelta(hours=1) < x <= t]
        dag = [x for x in tijden if x.date() == t.date() and x <= t]
        return uur, dag

    def _vroegst(self, st, soort, nu):
        """Vroegste moment ≥ nu waarop `soort` mag (los van de kill-switch)."""
        t = nu
        tot = _van_iso(st["blokkade"].get("tot"))
        if self.max_per_uur == 0 or self.max_per_dag == 0 or self.actief_van >= self.actief_tot:
            return None  # rem staat (via env) dicht: nooit
        for _ in range(50):
            vorig = t
            if tot and t < tot:
                t = tot
            t = self._volgende_start(t)
            uur, dag = self._tellingen(st, soort, t)
            if len(dag) >= self.max_per_dag:
                t = self._volgende_start(t.replace(hour=0, minute=0, second=0, microsecond=0)
                                         + _dt.timedelta(days=1))
                continue
            if len(uur) >= self.max_per_uur:
                # het venster zakt onder het maximum zodra de oudste meetellende valt
                t = uur[len(uur) - self.max_per_uur] + _dt.timedelta(hours=1, seconds=1)
                continue
            if t == vorig:
                return t
        return t

    # ── publieke API ───────────────────────────────────────────────────────
    def automatisch(self, st=None):
        st = st or self._lees()
        return self.env_automatisch and st.get("automatisch", True) is not False

    def mag_nu(self, soort):
        """→ (ok, reden, volgende_kans). ok=False met reden + het vroegste moment waarop
        het wel mag (None als automatisch gebruik uit staat of de rem dicht staat)."""
        if soort not in SOORTEN:
            raise ValueError(f"onbekende soort '{soort}' (kies uit {SOORTEN})")
        nu = self.klok()
        with self._vergrendeld() as st:
            self._herstel_niveau(st, nu)
            if not self.automatisch(st):
                return (False, "automatisch LinkedIn-gebruik staat uit (kill-switch "
                               "LINKEDIN_AUTOMATISCH=0 of 'snelheidsrem.py uit')", None)
            vroegst = self._vroegst(st, soort, nu)
            if vroegst is not None and vroegst <= nu:
                return (True, None, None)
            b = st["blokkade"]
            tot = _van_iso(b.get("tot"))
            if tot and nu < tot:
                reden = f"stroomonderbreker: {b.get('reden') or 'blokkade'} (tot {_iso(tot)})"
            elif not self._actief_op(nu):
                reden = (f"buiten de actieve uren ({self.actief_van:02d}:00–"
                         f"{self.actief_tot:02d}:00)")
            else:
                uur, dag = self._tellingen(st, soort, nu)
                if len(dag) >= self.max_per_dag:
                    reden = f"dagmaximum bereikt ({len(dag)}/{self.max_per_dag} {soort} vandaag)"
                elif len(uur) >= self.max_per_uur:
                    reden = (f"uurmaximum bereikt ({len(uur)}/{self.max_per_uur} {soort} in "
                             "het afgelopen uur)")
                else:
                    reden = "rem staat dicht (env-override)"
            return (False, reden, vroegst)

    def registreer(self, soort):
        """Tel één uitgevoerde actie van `soort` (na elk profiel / elke zoekactie)."""
        if soort not in SOORTEN:
            raise ValueError(f"onbekende soort '{soort}' (kies uit {SOORTEN})")
        nu = self.klok()
        with self._vergrendeld() as st:
            st["gebeurtenissen"][soort].append(_iso(nu))
            b = st["blokkade"]
            tot = _van_iso(b.get("tot"))
            if b.get("niveau") and not b.get("eerste_succes_na") and (tot is None or nu >= tot):
                b["eerste_succes_na"] = _iso(nu)
            self._herstel_niveau(st, nu)

    def blokkeer(self, reden):
        """Stroomonderbreker: stop alles 24u × 2^(niveau-1), max 7 dagen. → tot (datetime)."""
        nu = self.klok()
        with self._vergrendeld() as st:
            self._herstel_niveau(st, nu)
            b = st["blokkade"]
            niveau = int(b.get("niveau") or 0) + 1
            uren = min(BLOKKADE_MAX_UUR, BLOKKADE_BASIS_UUR * (2 ** (niveau - 1)))
            tot = nu + _dt.timedelta(hours=uren)
            b.update({"tot": _iso(tot), "reden": str(reden)[:300], "sinds": _iso(nu),
                      "niveau": niveau, "eerste_succes_na": None})
            return tot

    def reset_blokkade(self):
        """Eigenaar: hef de blokkade op én zet het niveau terug (na handmatige controle)."""
        with self._vergrendeld() as st:
            st["blokkade"] = self._leeg()["blokkade"]

    def zet_automatisch(self, aan):
        with self._vergrendeld() as st:
            st["automatisch"] = bool(aan)

    def status(self):
        """De contract-vorm (zie moduledocstring)."""
        nu = self.klok()
        with self._vergrendeld() as st:
            self._herstel_niveau(st, nu)
            automatisch = self.automatisch(st)
            tot = _van_iso(st["blokkade"].get("tot"))
            geblokkeerd = bool(tot and nu < tot)
            uit = {"automatisch": automatisch, "actief_nu": self._actief_op(nu),
                   "geblokkeerd_tot": _iso(tot) if geblokkeerd else None,
                   "reden": st["blokkade"].get("reden") if geblokkeerd else None}
            kansen = []
            for s in SOORTEN:
                uur, dag = self._tellingen(st, s, nu)
                uit[s] = {"uur": len(uur), "dag": len(dag), "max_uur": self.max_per_uur,
                          "max_dag": self.max_per_dag}
                kansen.append(self._vroegst(st, s, nu))
            if not automatisch or any(k is None for k in kansen):
                volgende = None
            else:
                volgende = max(kansen)
                volgende = None if volgende <= nu else volgende
            uit["volgende_kans"] = _iso(volgende)
            return uit

    def niveau(self):
        return int(self._lees()["blokkade"].get("niveau") or 0)


def pauze(basis=1.0, spreiding=0.6):
    """Willekeurige pauze-duur rond `basis` seconden (menselijk tempo, geen vast ritme):
    basis × U(1-spreiding/2, 1+spreiding) + U(0, 0.25·basis)."""
    basis = max(0.0, float(basis))
    return basis * random.uniform(1 - spreiding / 2, 1 + spreiding) + random.uniform(
        0, 0.25 * basis)


def rem_bericht(reden, volgende, nu=None):
    """De vaste weigermelding (de runner detecteert 'LINKEDIN-SNELHEIDSREM')."""
    nu = nu or _dt.datetime.now()
    if volgende is None:
        kop = "⏳ LINKEDIN-SNELHEIDSREM — geen automatische kans (rem dicht)"
    else:
        kop = f"⏳ LINKEDIN-SNELHEIDSREM — volgende kans {volgende:%H:%M}"
        if volgende.date() != nu.date():
            kop += f" ({volgende:%Y-%m-%d})"
    return (f"{kop}\n   reden: {reden}\n   Niet herproberen in een lus: zet het doel op "
            "vervolg=linkedin en ga verder met andere bronnen.")


def blokkade_bericht(reden, tot):
    """De vaste stroomonderbreker-melding (de runner detecteert 'LINKEDIN-BLOKKADE')."""
    return (f"⛔ LINKEDIN-BLOKKADE — {reden}\n"
            f"   Stroomonderbreker gesprongen: automatisch LinkedIn-gebruik stopt tot "
            f"{tot:%Y-%m-%d %H:%M}.\n"
            "   Eigenaar: controleer het account in een gewone browser (captcha/checkpoint "
            "afhandelen); daarna eventueel:\n"
            "       python3 tools/linkedin/snelheidsrem.py reset-blokkade\n"
            "   Een agent stopt nu met LinkedIn en meldt dit — niet herproberen.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="LinkedIn-snelheidsrem (Epic 12, J4-wijziging).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("status", help="toon tellingen, blokkade en volgende kans")
    p.add_argument("--json", action="store_true", help="machineleesbaar (contract-vorm)")
    p = sub.add_parser("mag", help="mag deze soort nu? exit 0 = ja, 75 = rem")
    p.add_argument("soort", choices=SOORTEN)
    sub.add_parser("reset-blokkade", help="eigenaar: blokkade + niveau opheffen")
    sub.add_parser("uit", help="persistente kill-switch: automatisch gebruik uit")
    sub.add_parser("aan", help="automatisch gebruik weer aan (env LINKEDIN_AUTOMATISCH blijft gelden)")
    args = ap.parse_args(argv)
    rem = Snelheidsrem()

    if args.cmd == "status":
        st = rem.status()
        if args.json:
            print(json.dumps(st, ensure_ascii=False))
            return 0
        print(f"Automatisch: {'aan' if st['automatisch'] else 'UIT (kill-switch)'} · "
              f"actieve uren {rem.actief_van:02d}:00–{rem.actief_tot:02d}:00 "
              f"({'nu actief' if st['actief_nu'] else 'nu buiten'})")
        if st["geblokkeerd_tot"]:
            print(f"⛔ Geblokkeerd tot {st['geblokkeerd_tot']} — {st['reden']} "
                  f"(niveau {rem.niveau()})")
        for s in SOORTEN:
            d = st[s]
            print(f"  {s:<8} uur {d['uur']}/{d['max_uur']} · dag {d['dag']}/{d['max_dag']}")
        if not st["automatisch"]:
            print("Volgende kans: — (automatisch gebruik staat uit)")
        else:
            print(f"Volgende kans: {st['volgende_kans'] or 'nu'}")
        return 0
    if args.cmd == "mag":
        ok, reden, volgende = rem.mag_nu(args.soort)
        if ok:
            print(f"✓ {args.soort}: mag nu")
            return 0
        print(rem_bericht(reden, volgende))
        return EXIT_REM
    if args.cmd == "reset-blokkade":
        rem.reset_blokkade()
        print("✓ Blokkade opgeheven en stroomonderbreker-niveau op 0 gezet.")
        return 0
    if args.cmd in ("uit", "aan"):
        rem.zet_automatisch(args.cmd == "aan")
        print(f"✓ Automatisch LinkedIn-gebruik: {args.cmd}"
              + ("" if rem.env_automatisch else " (let op: env LINKEDIN_AUTOMATISCH=0 houdt het uit)"))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
