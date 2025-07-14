import unittest
import pandas as pd
from smc_analysis import detect_fvgs, detect_order_blocks

def make_htf_df_with_fvg_and_ob():
    # Crea un DataFrame semanal artificial con una vela que genera FVG y otra que genera OB
    data = [
        # timestamp, open, high, low, close, volume
        ["2025-01-01", 100, 110, 90, 105, 1000],   # normal
        ["2025-01-08", 105, 120, 104, 119, 1200],  # FVG (gap up)
        ["2025-01-15", 119, 130, 118, 129, 1300],  # OB (bullish engulf)
        ["2025-01-22", 129, 135, 125, 130, 1100],  # normal
    ]
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df

class TestHTFIndicatorsForced(unittest.TestCase):
    def test_forced_fvg_and_ob(self):
        df = make_htf_df_with_fvg_and_ob()
        fvg = detect_fvgs(df)
        ob = detect_order_blocks(df)
        print("\nFORCED TEST DATAFRAME:")
        print(df)
        print("\nFVG DETECTED:")
        print(fvg)
        print("\nOB DETECTED:")
        print(ob)
        # Debe haber al menos un FVG válido
        self.assertTrue(fvg[["Top", "Bottom"]].notna().all(axis=1).any())
        # Debe haber al menos un OB válido
        if hasattr(ob, 'Top') and hasattr(ob, 'Bottom'):
            self.assertTrue(ob[["Top", "Bottom"]].notna().all(axis=1).any())
        else:
            self.assertTrue(False, "OB DataFrame no tiene columnas Top/Bottom")

if __name__ == "__main__":
    unittest.main()
