import unittest
from utils_htf import get_htf_gaps_and_obs

class TestHTFZones(unittest.TestCase):
    def test_get_htf_gaps_and_obs_weekly(self):
        symbol = "BTC/USDT"
        fvg_zones, ob_zones, ltf_df = get_htf_gaps_and_obs(symbol, htf="1w", ltf="4h")
        print("Weekly FVG zones:", fvg_zones)
        print("Weekly OB zones:", ob_zones)
        self.assertIsInstance(fvg_zones, list)
        self.assertIsInstance(ob_zones, list)
        # Al menos debe devolver una lista (puede estar vacía si no hay zonas)
        self.assertTrue(isinstance(ltf_df, object))

    def test_get_htf_gaps_and_obs_monthly(self):
        symbol = "BTC/USDT"
        fvg_zones, ob_zones, ltf_df = get_htf_gaps_and_obs(symbol, htf="1M", ltf="4h")
        print("Monthly FVG zones:", fvg_zones)
        print("Monthly OB zones:", ob_zones)
        self.assertIsInstance(fvg_zones, list)
        self.assertIsInstance(ob_zones, list)
        self.assertTrue(isinstance(ltf_df, object))

if __name__ == "__main__":
    unittest.main()
