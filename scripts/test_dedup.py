"""Unit-tests voor dedup.gelijkenis (story A6).

Bewijst de meerwaarde boven difflib: parafrase-paren (zelfde betekenis, andere
bewoording/volgorde) komen boven de drempel terwijl difflib eronder blijft.

    python3 scripts/test_dedup.py
"""

import sys
import unittest
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dedup import DREMPEL, gelijkenis  # noqa: E402


def difflib_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


# Parafrase-paren: zelfde claim, andere bewoording/woordvolgorde. Verwachting:
# gelijkenis >= DREMPEL, terwijl difflib eronder (< 0.85 server-drempel) blijft.
PARAFRASE_PAREN = [
    (
        "DPG Media bezit meerdere landelijke dagbladen in Nederland.",
        "In Nederland bezit DPG Media meerdere landelijke dagbladen.",
    ),
    (
        "De redactie ondervindt druk van de grote adverteerders.",
        "Van de grote adverteerders ondervindt de redactie druk.",
    ),
    (
        "Journalisten passen zelfcensuur toe uit angst voor ontslag.",
        "Uit angst voor ontslag passen journalisten zelfcensuur toe.",
    ),
]

# Echt-verschillend paar: moet ruim onder de drempel scoren.
VERSCHILLEND_PAAR = (
    "DPG Media bezit meerdere landelijke dagbladen in Nederland.",
    "Het weer in juli was uitzonderlijk warm langs de kust.",
)


class TestGelijkenis(unittest.TestCase):
    def test_identiek_is_ongeveer_een(self):
        s = "De publieke omroep wordt gefinancierd door de staat."
        self.assertGreaterEqual(gelijkenis(s, s), 0.999)

    def test_parafrase_boven_drempel_en_difflib_eronder(self):
        for a, b in PARAFRASE_PAREN:
            sem = gelijkenis(a, b)
            dif = difflib_ratio(a, b)
            with self.subTest(paar=(a, b)):
                self.assertGreaterEqual(
                    sem, DREMPEL,
                    f"parafrase te laag: gelijkenis={sem:.3f} < {DREMPEL}",
                )
                # De meerwaarde: difflib mist deze parafrase (< 0.85).
                self.assertLess(
                    dif, 0.85,
                    f"difflib pakt dit al ({dif:.3f}); geen meerwaarde-bewijs",
                )
                self.assertGreater(sem, dif)

    def test_verschillend_ruim_onder_drempel(self):
        a, b = VERSCHILLEND_PAAR
        sem = gelijkenis(a, b)
        self.assertLess(sem, 0.40, f"onterecht hoog: {sem:.3f}")

    def test_score_altijd_in_bereik(self):
        for a, b in PARAFRASE_PAREN + [VERSCHILLEND_PAAR]:
            for x, y in ((a, b), (b, a)):
                s = gelijkenis(x, y)
                self.assertGreaterEqual(s, 0.0)
                self.assertLessEqual(s, 1.0)

    def test_symmetrisch(self):
        for a, b in PARAFRASE_PAREN:
            self.assertAlmostEqual(gelijkenis(a, b), gelijkenis(b, a), places=9)

    def test_lege_en_none_invoer(self):
        self.assertEqual(gelijkenis("", ""), 1.0)
        self.assertEqual(gelijkenis("iets", ""), 0.0)
        self.assertEqual(gelijkenis(None, "iets"), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
