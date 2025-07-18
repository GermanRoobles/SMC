import unittest
from utils_htf import get_htf_gaps_and_obs

class TestHTFIndicators(unittest.TestCase):
    def test_htf_fvg_and_ob(self):
        symbol = "BTC/USDT"
        # Probar para weekly y monthly
        for htf in ["1w", "1M"]:
            fvg_zones, ob_zones, ltf_df = get_htf_gaps_and_obs(symbol, htf=htf, ltf="4h")
            print(f"\nHTF: {htf}")
            print(f"FVG zones: {fvg_zones}")
            print(f"OB zones: {ob_zones}")
            self.assertIsInstance(fvg_zones, list)
            self.assertIsInstance(ob_zones, list)
            # Al menos debe devolver listas (pueden estar vacías si no hay zonas)
            self.assertTrue(isinstance(fvg_zones, list))
            self.assertTrue(isinstance(ob_zones, list))
            # Si hay zonas, deben tener top y bottom
            for zone in fvg_zones + ob_zones:
                self.assertIn("top", zone)
                self.assertIn("bottom", zone)

if __name__ == "__main__":
    unittest.main()
