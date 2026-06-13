#!/usr/bin/env python3
"""
Golden-snapshot-test voor de scoringsketen v2 (verbeterplan M1.1/M1.2/M1.3/M1.4/M1.5/M1.7).

Twee lagen:
1. Wiskunde-tests met HANDBEREKENDE verwachtingswaarden (dezelfde voorbeelden staan
   doorgerekend in DOCUMENTATIE.md § "Scores"): DF-QuAD-propagatie, clusteraggregatie,
   Beta-interval, tegenspraak-plafond, invloed-verschuiving.
2. Een fixture-DB (in-memory uit schema.sql, mét de seed-rollen/-mechanismen) waarvan de
   eindscores exact vastliggen. Verandert iemand een constante of formule in scoring.py,
   dan faalt deze test — scores mogen alleen BEWUST verschuiven (golden snapshot).

Draait mee in `scripts/validate_model.py --strict` (CI-poort).
Gebruik: python3 scripts/test_scoring.py
"""
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import scoring  # noqa: E402

SCHEMA = (ROOT / "schema.sql").read_text()


def fixture_db():
    """In-memory DB met een klein, volledig handdoorrekenbaar model.

    schema.sql levert de tabellen + seed-rollen/-mechanismen (mechanisme 1 =
    eigendomsconcentratie). Daarbovenop: 2 entiteiten, 2 relaties, 3 bronnen
    (waarvan 2 in hetzelfde cluster), een discussieboom met ondergraving en
    versterking, een weerlegging, een invloed-argument, een mechanisme-
    literatuurargument en een emergent veld met compositieclaim.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    conn.execute("INSERT INTO entities (id, name, type) VALUES (1, 'TestHolding', 'bedrijf')")
    conn.execute("INSERT INTO entities (id, name, type) VALUES (2, 'TestKrant', 'mediaorganisatie')")
    # R1: het doorgerekende voorbeeld; R2: alleen een handmatige prior (plafond-test)
    conn.execute("""INSERT INTO relations (id, source_id, target_id, relation_type,
                    mechanism_id, certainty, influence) VALUES (1, 1, 2, 'eigendom', 1, 0.9, 0.6)""")
    conn.execute("""INSERT INTO relations (id, source_id, target_id, relation_type,
                    certainty, influence) VALUES (2, 2, 1, 'bron_van', 0.9, 0.3)""")
    conn.execute("""INSERT INTO instantiations (mechanism_id, relation_id, exemplarity)
                    VALUES (1, 1, 0.8)""")

    # Bronnen: S1 en S3 delen cluster 'chomsky' (M1.2); S2 is institutioneel cluster 'wrr'
    conn.execute("""INSERT INTO sources (id, title, source_type, reliability, cluster_key)
                    VALUES (1, 'Boek A', 'boek', 'academisch', 'chomsky')""")
    conn.execute("""INSERT INTO sources (id, title, source_type, reliability, cluster_key)
                    VALUES (2, 'Rapport B', 'rapport', 'institutioneel', 'wrr')""")
    conn.execute("""INSERT INTO sources (id, title, source_type, reliability, cluster_key)
                    VALUES (3, 'Boek C', 'boek', 'academisch', 'chomsky')""")

    def arg(aid, stance, weight, status, *, rel=None, ent=None, mech=None, eff=None,
            parent=None, prop=None, cite=None):
        conn.execute("""INSERT INTO arguments
            (id, relation_id, entity_id, mechanism_id, emergent_effect_id,
             parent_argument_id, property, stance, claim, weight, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (aid, rel, ent, mech, eff, parent, prop, stance, f"claim {aid}", weight, status))
        if cite:
            conn.execute("INSERT INTO citations (argument_id, source_id) VALUES (?, ?)",
                         (aid, cite))

    # Discussieboom op R1 (zie DOCUMENTATIE.md voor de doorrekening). De opgeslagen
    # `weight` telt sinds de neutralisatie NIET mee: τ = statusfactor · bronfactor
    # (neutraal gewicht 1,0). De weight-argumenten hieronder zijn dus illustratief —
    # ze beïnvloeden de score niet meer (tot bridging ze objectief invult).
    #   A1 (voor, τ=1,0·1,0=1,0) ← B1 (ondergraving, τ=1,0·0,3=0,30) ← C1 (versterking, τ=0,5·0,3=0,15)
    #   A2 (voor, τ=1,0; zelfde broncluster als A1 → telt niet op)
    #   D1 (weerlegging mét bron, τ=0,895 → overwogen tegenspraak, geen plafond)
    arg(1, "supporting", 0.8, "geverifieerd", rel=1, cite=1)         # τ = 1,0·1,0 = 1,0
    arg(2, "contradicting", 0.5, "geverifieerd", parent=1)           # τ = 1,0·0,3 = 0,30
    arg(3, "supporting", 0.6, "ongecontroleerd", parent=2)           # τ = 0,5·0,3 = 0,15
    arg(4, "supporting", 0.6, "geverifieerd", rel=1, cite=3)         # τ = 1,0 (cluster chomsky)
    arg(5, "contradicting", 0.7, "geverifieerd", rel=1, cite=2)      # τ = 1,0·0,895 = 0,895
    # Invloed-as (M1.7): bewijs dat de invloed sterk is
    arg(6, "supporting", 1.0, "geverifieerd", rel=1, prop="influence", cite=2)  # τ = 0,895
    # Literatuurlijn mechanisme 1 (eigendomsconcentratie)
    arg(7, "supporting", 0.9, "geverifieerd", mech=1, cite=1)        # lit = 1,0/2,0 = 0,5
    # Emergent veld met literatuur- én compositielijn (M1.5)
    conn.execute("""INSERT INTO emergent_effects (id, name, label, description, effect)
                    VALUES (1, 'test_veld', 'Testveld', 'd', 'e')""")
    arg(8, "supporting", 0.8, "geverifieerd", eff=1, cite=2)               # lit: τ = 0,895
    arg(9, "supporting", 0.7, "geverifieerd", eff=1, prop="compositie", cite=1)  # comp: τ = 1,0

    conn.commit()
    return conn


class TestDFQuAD(unittest.TestCase):
    """M1.1: boomsemantiek — handberekende voorbeelden."""

    def test_blad_houdt_tau(self):
        self.assertEqual(scoring.dfquad_strength(0.8, [], []), 0.8)

    def test_ondergraving_dempt(self):
        # σ = 0,8 · (1 − 0,15) = 0,68
        self.assertAlmostEqual(scoring.dfquad_strength(0.8, [], [0.15]), 0.68)

    def test_versterking_tilt(self):
        # σ = 0,15 + (1 − 0,15) · 0,09 = 0,2265
        self.assertAlmostEqual(scoring.dfquad_strength(0.15, [0.09], []), 0.2265)

    def test_balans_houdt_tau(self):
        self.assertAlmostEqual(scoring.dfquad_strength(0.5, [0.3], [0.3]), 0.5)

    def test_propagatie_drie_niveaus(self):
        # A1 ← B1 (tegen) ← C1 (voor B1): σ_B1 = 0,2265; σ_A1 = 0,8·(1−0,2265) = 0,6188
        taus = {1: 0.8, 2: 0.15, 3: 0.09}
        parents = {1: None, 2: 1, 3: 2}
        stances = {1: "supporting", 2: "contradicting", 3: "supporting"}
        sigma = scoring.propagate_sigma(taus, parents, stances)
        self.assertAlmostEqual(sigma[3], 0.09)
        self.assertAlmostEqual(sigma[2], 0.2265)
        self.assertAlmostEqual(sigma[1], 0.6188)

    def test_contextual_reply_doet_niets(self):
        taus = {1: 0.8, 2: 0.5}
        sigma = scoring.propagate_sigma(taus, {1: None, 2: 1}, {1: "supporting", 2: "contextual"})
        self.assertAlmostEqual(sigma[1], 0.8)


class TestClustersEnBalans(unittest.TestCase):
    """M1.2: binnen een cluster telt alleen het sterkste argument."""

    def test_zelfde_cluster_telt_niet_op(self):
        roots = [
            {"stance": "supporting", "sigma": 0.6188, "cluster": "chomsky", "n_citaties": 1, "status": "geverifieerd"},
            {"stance": "supporting", "sigma": 0.6, "cluster": "chomsky", "n_citaties": 1, "status": "geverifieerd"},
        ]
        bal = scoring.balance_from_roots(roots, 1.0)
        self.assertAlmostEqual(bal["steun"], 0.6188)   # max, niet som
        self.assertEqual(bal["n_steun_clusters"], 1)

    def test_zonder_bron_pseudocluster(self):
        roots = [
            {"stance": "supporting", "sigma": 0.5, "cluster": scoring.ZONDER_BRON_CLUSTER, "n_citaties": 0, "status": "ongecontroleerd"},
            {"stance": "supporting", "sigma": 0.4, "cluster": scoring.ZONDER_BRON_CLUSTER, "n_citaties": 0, "status": "ongecontroleerd"},
        ]
        bal = scoring.balance_from_roots(roots, 1.0)
        self.assertAlmostEqual(bal["steun"], 0.5)      # bronloze steun stapelt niet

    def test_overwogen_tegenspraak_vergt_bron(self):
        bronloos = [{"stance": "contradicting", "sigma": 0.3, "cluster": scoring.ZONDER_BRON_CLUSTER,
                     "n_citaties": 0, "status": "ongecontroleerd"}]
        self.assertFalse(scoring.balance_from_roots(bronloos, 1.0)["overwogen_tegenspraak"])
        met_bron = [{"stance": "contradicting", "sigma": 0.3, "cluster": "wrr",
                     "n_citaties": 1, "status": "ongecontroleerd"}]
        self.assertTrue(scoring.balance_from_roots(met_bron, 1.0)["overwogen_tegenspraak"])


class TestIntervalEnPlafond(unittest.TestCase):
    """M1.3 (Beta-interval) en M1.4 (tegenspraak-plafond)."""

    def test_interval_smaller_bij_meer_bewijs(self):
        lo1, hi1 = scoring.beta_interval(0.5, 0.0, 1.0)
        lo2, hi2 = scoring.beta_interval(10.0, 0.0, 1.0)
        self.assertLess(hi1 - lo1, 1.0)
        self.assertLess(hi2 - lo2, hi1 - lo1)
        self.assertGreater(lo2, 0.6)   # Beta(10,5; 1,5): 2,5%-kwantiel ≈ 0,647

    def test_plafond_op_prior_zonder_tegenspraak(self):
        d = scoring.instance_detail([], prior_certainty=0.9)
        self.assertEqual(d["score"], scoring.CAP_ONWEERSPROKEN)
        self.assertTrue(d["onweersproken"] and d["capped"])
        self.assertEqual(d["bron"], "prior")

    def test_geen_plafond_met_overwogen_tegenspraak(self):
        roots = [
            {"stance": "supporting", "sigma": 0.9, "cluster": "a", "n_citaties": 1, "status": "geverifieerd"},
            {"stance": "contradicting", "sigma": 0.05, "cluster": "b", "n_citaties": 1, "status": "geverifieerd"},
        ]
        d = scoring.instance_detail(roots)
        self.assertFalse(d["onweersproken"])
        self.assertFalse(d["capped"])


class TestInvloedAs(unittest.TestCase):
    """M1.7: invloed-argumenten verschuiven de prior."""

    def test_geen_bewijs_houdt_prior(self):
        d = scoring.derived_influence(0.6, [])
        self.assertEqual(d["score"], 0.6)
        self.assertFalse(d["verschoven"])

    def test_bewijs_verschuift(self):
        # τ = 0,895 → balans 0,4723; gewicht 0,895/2,895 = 0,3092
        # afgeleid = 0,6·0,6908 + 0,4723·0,3092 = 0,5605
        roots = [{"stance": "supporting", "sigma": 0.895, "cluster": "wrr",
                  "n_citaties": 1, "status": "geverifieerd"}]
        d = scoring.derived_influence(0.6, roots)
        self.assertAlmostEqual(d["score"], 0.5605, places=4)
        self.assertTrue(d["verschoven"])


class TestGoldenSnapshot(unittest.TestCase):
    """Volledige keten op de fixture-DB: deze einduitkomsten liggen vast.

    Verandert een constante of formule in scoring.py, dan verschuiven ze en
    faalt deze test — wijzig de verwachtingen alleen bij een BEWUSTE
    score-wijziging (en documenteer die in het verbeterplan/changelog).
    """

    @classmethod
    def setUpClass(cls):
        cls.conn = fixture_db()
        cls.scores = scoring.compute_all_scores(cls.conn)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_sigma_propagatie(self):
        a = self.scores["argument_scores"]
        self.assertAlmostEqual(a[1]["tau"], 1.0)        # weight genegeerd: τ = status·bron
        self.assertAlmostEqual(a[1]["sigma"], 0.595)    # 1,0·(1−0,405), gedempt door B1
        self.assertAlmostEqual(a[2]["sigma"], 0.405)    # 0,30 + (1−0,30)·0,15, versterkt door C1
        self.assertAlmostEqual(a[5]["sigma"], 0.895)    # weerlegging D1, blad

    def test_relatie_1(self):
        d = self.scores["relations_detail"][1]
        # steun: max(0,595; 1,0) = 1,0 (zelfde cluster chomsky!); tegen: 0,895
        # score = 1,0 / (1,0 + 0,895 + 1) = 0,3454
        self.assertAlmostEqual(d["score"], 0.3454, places=4)
        self.assertEqual(d["bron"], "bewijs")
        self.assertEqual(d["n_steun_clusters"], 1)
        self.assertTrue(d["spof"])
        self.assertFalse(d["onweersproken"])            # D1 is een echte weerlegging
        self.assertLess(d["lo"], d["score"])
        self.assertGreater(d["hi"], d["score"])

    def test_relatie_2_plafond(self):
        d = self.scores["relations_detail"][2]
        self.assertEqual(d["score"], scoring.CAP_ONWEERSPROKEN)   # prior 0,9 → plafond 0,7
        self.assertTrue(d["onweersproken"] and d["capped"])

    def test_invloed_relatie_1(self):
        self.assertAlmostEqual(self.scores["relations_influence"][1], 0.5605, places=4)

    def test_mechanisme_1(self):
        m = self.scores["mechanisms"][1]
        self.assertAlmostEqual(m["literatuur_geloofw"], 0.5, places=4)      # 1,0/2,0
        self.assertAlmostEqual(m["praktijk_geloofw"], 0.0476, places=3)     # 0,3454·0,8/5,8
        self.assertAlmostEqual(m["geloofwaardigheid"], 0.5238, places=4)    # noisy-OR
        self.assertAlmostEqual(m["sterkte"], 0.5605, places=4)              # afgeleide invloed R1
        self.assertTrue(m["onweersproken"])
        self.assertTrue(m["spof"])

    def test_emergent_veld(self):
        e = self.scores["emergent_effects"][1]
        self.assertAlmostEqual(e["literatuur_geloofw"], 0.4723, places=4)   # 0,895/1,895
        self.assertAlmostEqual(e["compositie_geloofw"], 0.5, places=4)      # 1,0/2,0
        # noisy-OR(0,4723; 0,5) = 0,7362 > plafond 0,70 zonder tegenspraak (M1.4) → gecapt
        self.assertAlmostEqual(e["geloofwaardigheid"], scoring.CAP_ONWEERSPROKEN, places=4)
        self.assertTrue(e["capped"] and e["onweersproken"])
        self.assertFalse(e["zonder_compositieclaim"])

    def test_compositieplafond(self):
        # Zelfde veld zonder compositieclaim: plafond 0,50
        e = scoring.emergent_scores(
            [{"stance": "supporting", "sigma": 0.9, "cluster": "a", "n_citaties": 1,
              "status": "geverifieerd"}], [])
        self.assertTrue(e["zonder_compositieclaim"])
        self.assertLessEqual(e["geloofwaardigheid"], scoring.CAP_ZONDER_COMPOSITIE)

    def test_weight_genegeerd_bridging_overschrijft(self):
        # Zelf-gerapporteerd weight telt niet mee (τ = status·bron, neutraal gewicht 1,0).
        # Een bridged rating (M2.5) vult het gewicht alsnog objectief in: hier zakt
        # arg1 van τ=1,0 naar 0,25·1,0·1,0 = 0,25.
        conn = fixture_db()
        s = scoring.compute_all_scores(conn, bridged_weights={1: 0.25})
        self.assertAlmostEqual(s["argument_scores"][1]["tau"], 0.25)
        self.assertAlmostEqual(s["argument_scores"][4]["tau"], 1.0)   # geen rating → neutraal
        conn.close()

    def test_reply_check_weigert_eigen_doel(self):
        # Doelregel (M1.1) als DB-CHECK: een reply met eigen doel is ongeldig
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("""INSERT INTO arguments
                (relation_id, parent_argument_id, stance, claim)
                VALUES (1, 1, 'supporting', 'reply met doel')""")


if __name__ == "__main__":
    unittest.main(verbosity=2)
