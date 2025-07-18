import unittest
from datetime import datetime, timedelta
from fetch_data import get_ohlcv_with_cache
from smc_analysis import detect_fvgs, detect_order_blocks

class TestHTFIndicatorsReal(unittest.TestCase):
    def test_real_htf_fvg_and_ob(self):
        symbol = "BTC/USDT"
        htf = "1w"
        end = datetime.utcnow()
        start = end - timedelta(days=365)  # Último año
        df = get_ohlcv_with_cache(symbol, htf, start, end)
        print(f"\n[REAL DATA] {symbol} {htf} desde {start.date()} hasta {end.date()} - {len(df)} filas")
        print(df.head())
        fvg = detect_fvgs(df)
        ob = detect_order_blocks(df)
        print("\nFVG DETECTED:")
        print(fvg)
        print("\nOB DETECTED:")
        print(ob)
        # Debe haber al menos un FVG válido en el año
        self.assertTrue(fvg[["Top", "Bottom"]].notna().all(axis=1).any(), "No se detectó ningún FVG válido en el año")
        # Debe haber al menos un OB válido en el año
        if hasattr(ob, 'Top') and hasattr(ob, 'Bottom'):
            self.assertTrue(ob[["Top", "Bottom"]].notna().all(axis=1).any(), "No se detectó ningún OB válido en el año")
        else:
            self.assertTrue(False, "OB DataFrame no tiene columnas Top/Bottom")

if __name__ == "__main__":
    unittest.main()
