import pandas as pd

def get_htf_gaps_and_obs(symbol, htf="1w", ltf="4h"):
    """
    Detecta FVGs y Order Blocks en high timeframe (1w o 1M)
    Proyecta esas zonas sobre el low timeframe (4h)
    """

    from fetch_data import get_ohlcv_with_cache
    from datetime import datetime, timedelta
    # Rango amplio para HTF y LTF
    now = datetime.utcnow()
    htf_start = now - timedelta(days=90)
    ltf_start = now - timedelta(days=30)
    htf_df = get_ohlcv_with_cache(symbol, htf, htf_start, now)
    ltf_df = get_ohlcv_with_cache(symbol, ltf, ltf_start, now)

    print(f"\n[DEBUG][HTF] DataFrame {htf} para {symbol}:")
    print(htf_df.head(10))
    print(htf_df.tail(5))
    print(f"Columnas: {list(htf_df.columns)}  |  Filas: {len(htf_df)}")

    from smc_analysis import detect_fvgs, detect_order_blocks
    htf_fvg = detect_fvgs(htf_df)
    htf_ob = detect_order_blocks(htf_df)

    # Filtrado automático: solo zonas válidas (sin NaN, top != bottom, sin valores nulos)
    def filter_valid_zones(df):
        if df is None or len(df) == 0:
            return df
        df = df.copy()
        # Para FVG y OB, columnas pueden ser Top/Bottom o high/low
        top_col = 'Top' if 'Top' in df.columns else ('high' if 'high' in df.columns else None)
        bottom_col = 'Bottom' if 'Bottom' in df.columns else ('low' if 'low' in df.columns else None)
        if top_col and bottom_col:
            df = df[df[top_col].notna() & df[bottom_col].notna()]
            df = df[df[top_col] != df[bottom_col]]
        return df

    htf_fvg_valid = filter_valid_zones(htf_fvg)
    htf_ob_valid = filter_valid_zones(htf_ob)

    print(f"[DEBUG][HTF] FVG válidos: {htf_fvg_valid.head(5)}")
    print(f"[DEBUG][HTF] OB válidos: {htf_ob_valid.head(5)}")

    projected_fvg = project_zones_to_ltf(htf_fvg_valid, ltf_df)
    projected_ob = project_zones_to_ltf(htf_ob_valid, ltf_df)

    return projected_fvg, projected_ob, ltf_df

def project_zones_to_ltf(zones, ltf_df):
    """
    Mapea zonas de HTF sobre el índice de tiempo del LTF para dibujarlas correctamente
    """
    projected = []
    for _, row in zones.iterrows():
        zone = {
            "top": row["Top"] if "Top" in row else row.get("high", None),
            "bottom": row["Bottom"] if "Bottom" in row else row.get("low", None),
            "id": row.get("id", f"zone_{_}")
        }
        projected.append(zone)
    return projected

def monitor_fvg_alerts(price, fvg_zones, alerted):
    alerts = []
    for zone in fvg_zones:
        top = zone["top"]
        bottom = zone["bottom"]
        id = zone["id"]
        if price > top and not alerted.get(f"{id}_opened"):
            alerts.append(f"🔔 FVG opened: price above {top}")
            alerted[f"{id}_opened"] = True
        if bottom <= price <= top and not alerted.get(f"{id}_filled"):
            alerts.append(f"✅ FVG filled: price entered zone {bottom}-{top}")
            alerted[f"{id}_filled"] = True
    return alerts

def monitor_ob_alerts(price, ob_zones, alerted):
    alerts = []
    for zone in ob_zones:
        high = zone["top"] if "top" in zone else zone.get("high", None)
        low = zone["bottom"] if "bottom" in zone else zone.get("low", None)
        id = zone["id"]
        if low <= price <= high and not alerted.get(f"{id}_mitigated"):
            alerts.append(f"⚠️ Order Block mitigated at zone {low}-{high}")
            alerted[f"{id}_mitigated"] = True
    return alerts

def detect_sfp(df, threshold=1.5):
    """
    Detecta SFPs: mecha que rompe swing anterior pero el cierre revierte.
    """
    sfps = []
    for i in range(2, len(df) - 1):
        high = df['high'].iloc[i]
        prev_high = df['high'].iloc[i - 2]
        # Bullish SFP (trampa bajista)
        if high > prev_high and df['close'].iloc[i] < prev_high:
            sfps.append({
                'timestamp': df.index[i],
                'type': 'Bearish SFP',
                'level': prev_high,
                'price': df['close'].iloc[i]
            })
        # Bearish SFP (trampa alcista)
        low = df['low'].iloc[i]
        prev_low = df['low'].iloc[i - 2]
        if low < prev_low and df['close'].iloc[i] > prev_low:
            sfps.append({
                'timestamp': df.index[i],
                'type': 'Bullish SFP',
                'level': prev_low,
                'price': df['close'].iloc[i]
            })
    return sfps
