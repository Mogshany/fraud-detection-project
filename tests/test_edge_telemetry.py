"""
tests/test_edge_telemetry.py
============================
Unit tests for all Role 1 computational techniques.

Run with:  python -m unittest discover tests/ -v
       or: python tests/test_edge_telemetry.py
"""

import time, math, unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.edge_telemetry import (
    DeviceFingerprintEngine, GeoLocationRiskEngine, SIMLifecycleEngine,
    StatisticalAnomalyEngine, EdgeRiskScorer, EdgeTelemetryModule,
)

class TestDeviceFingerprintEngine(unittest.TestCase):
    def setUp(self): self.engine = DeviceFingerprintEngine()

    def test_same_data_same_hash(self):
        d = {"model": "Samsung", "os": "Android 13"}
        self.assertEqual(self.engine.generate_fingerprint(d), self.engine.generate_fingerprint(d))

    def test_different_data_different_hash(self):
        self.assertNotEqual(self.engine.generate_fingerprint({"a":1}), self.engine.generate_fingerprint({"a":2}))

    def test_hamming_identical(self): self.assertEqual(self.engine.hamming_distance("a"*64, "a"*64), 0)
    def test_hamming_opposite(self):  self.assertEqual(self.engine.hamming_distance("0"*64, "f"*64), 256)

    def test_new_device_suspicious(self):
        r = self.engine.analyze({"model": "X"}, None)
        self.assertTrue(r["is_new_device"]); self.assertEqual(r["risk_flag"], "SUSPICIOUS")

    def test_same_device_no_risk(self):
        d = {"model": "Samsung", "os": "Android 13"}
        fp = self.engine.generate_fingerprint(d)
        r = self.engine.analyze(d, fp)
        self.assertEqual(r["risk_flag"], "NONE"); self.assertEqual(r["similarity_score"], 1.0)

class TestGeoLocationRiskEngine(unittest.TestCase):
    def setUp(self): self.engine = GeoLocationRiskEngine()

    def test_same_point_zero(self):
        self.assertAlmostEqual(self.engine.haversine_distance(-1.286,36.817,-1.286,36.817), 0.0, places=1)

    def test_nairobi_to_lagos(self):
        d = self.engine.haversine_distance(-1.286389,36.817223,6.5244,3.3792)
        self.assertTrue(3700 < d < 3900)

    def test_nairobi_in_safe_zone(self): self.assertEqual(self.engine.is_in_safe_zone(-1.286389,36.817223), "Nairobi")
    def test_lagos_not_safe_zone(self):  self.assertIsNone(self.engine.is_in_safe_zone(6.5244,3.3792))

    def test_impossible_travel_high(self):
        r = self.engine.analyze(-1.286389,36.817223,6.5244,3.3792,300)
        self.assertEqual(r["risk_flag"],"HIGH")

    def test_normal_move_low(self):
        r = self.engine.analyze(-1.286389,36.817223,-1.268,36.805,3600)
        self.assertEqual(r["risk_flag"],"NONE")

    def test_no_prev_suspicious(self):
        r = self.engine.analyze(-1.286389,36.817223,None,None,3600)
        self.assertEqual(r["risk_flag"],"SUSPICIOUS")

class TestSIMLifecycleEngine(unittest.TestCase):
    def setUp(self): self.engine = SIMLifecycleEngine()

    def test_stable_no_risk(self):
        r = self.engine.analyze("123","123",None,time.time(),0)
        self.assertEqual(r["risk_flag"],"NONE")

    def test_change_in_window_high(self):
        now = time.time()
        r = self.engine.analyze("NEW","OLD",now-120,now,1)
        self.assertEqual(r["risk_flag"],"HIGH")

    def test_many_changes_high(self):
        r = self.engine.analyze("NEW","OLD",None,time.time(),3)
        self.assertEqual(r["risk_flag"],"HIGH")

    def test_change_outside_window_suspicious(self):
        now = time.time()
        r = self.engine.analyze("NEW","OLD",now-3600,now,1)
        self.assertEqual(r["risk_flag"],"SUSPICIOUS")

class TestStatisticalAnomalyEngine(unittest.TestCase):
    def setUp(self): self.engine = StatisticalAnomalyEngine()

    def test_z_normal(self):
        z = self.engine.z_score(10,[9,10,9,11,10,9,10,9])
        self.assertLess(abs(z),1.0)

    def test_z_anomalous(self):
        z = self.engine.z_score(3,[9,10,9,11,10,9,10,9])
        self.assertGreater(abs(z),2.0)

    def test_normal_hour_low(self):
        r = self.engine.analyze_login_hour(10,[9,10,9,11,10,9,10])
        self.assertEqual(r["risk_flag"],"NONE")

    def test_anomalous_hour_flagged(self):
        r = self.engine.analyze_login_hour(3,[9,10,9,11,10,9,10,9,10])
        self.assertIn(r["risk_flag"],("SUSPICIOUS","HIGH"))

    def test_velocity_normal(self):
        r = self.engine.analyze_transaction_velocity([10,12,11,10,11,10,11])
        self.assertEqual(r["risk_flag"],"NONE")

    def test_velocity_spike_flagged(self):
        r = self.engine.analyze_transaction_velocity([10,10,10,10,10,10,50])
        self.assertIn(r["risk_flag"],("SUSPICIOUS","HIGH"))

class TestEdgeRiskScorer(unittest.TestCase):
    def setUp(self): self.scorer = EdgeRiskScorer()

    def test_all_none_low(self):
        r = self.scorer.score("NONE","NONE","NONE","NONE")
        self.assertEqual(r["risk_level"],"LOW"); self.assertEqual(r["risk_score"],0.0)

    def test_all_high(self):
        r = self.scorer.score("HIGH","HIGH","HIGH","HIGH")
        self.assertEqual(r["risk_level"],"HIGH"); self.assertEqual(r["risk_score"],1.0)

    def test_device_sim_high(self):
        r = self.scorer.score("HIGH","HIGH","NONE","NONE")
        self.assertGreaterEqual(r["risk_score"],0.65)

class TestIntegration(unittest.TestCase):
    def setUp(self): self.module = EdgeTelemetryModule()

    def _base_payload(self):
        return {
            "user_id":"T001","device_attributes":{"model":"Samsung","os":"Android 13"},
            "previous_fingerprint":None,"current_lat":-1.286389,"current_lon":36.817223,
            "previous_lat":-1.286389,"previous_lon":36.817223,"time_since_last_login_seconds":86400,
            "current_imsi":"63902123456789","previous_imsi":"63902123456789",
            "imsi_change_count_24h":0,"login_hour_history":[10,10,9,11,10],
        }

    def test_output_has_required_fields(self):
        r = self.module.process(self._base_payload())
        for key in ("metadata","analyses","risk_assessment","forward_to_role2"):
            self.assertIn(key, r)

    def test_high_risk_blocked(self):
        now = time.time()
        p = self._base_payload()
        p.update({"current_lat":6.5244,"current_lon":3.3792,"previous_lat":-1.286389,
                   "previous_lon":36.817223,"time_since_last_login_seconds":120,
                   "current_imsi":"NEW","previous_imsi":"OLD",
                   "imsi_change_timestamp":now-60,"imsi_change_count_24h":3})
        r = self.module.process(p)
        self.assertEqual(r["risk_assessment"]["risk_level"],"HIGH")
        self.assertFalse(r["forward_to_role2"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
