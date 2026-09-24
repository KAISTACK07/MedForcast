import numpy as np

def naive_forecast(series):
    """Predict t from t-1. Aligns with actual[1:]."""
    series = np.array(series, dtype=float)
    if len(series) < 2:
        return np.array([], dtype=float)
    return np.array(series[:-1], dtype=float)

def moving_average_forecast(series, window=3):
    """Predict t from moving average of past `window` periods. Aligns with actual[window:]."""
    s = np.array(series, dtype=float)
    if len(s) <= window:
        return np.array([], dtype=float)
    out = []
    for i in range(window, len(s)):
        out.append(s[i - window : i].mean())
    return np.array(out, dtype=float)

def seasonal_naive_forecast(series, season=12):
    """Predict t from t-season (e.g. lag 12 for annual seasonality). Aligns with actual[season:]."""
    s = np.array(series, dtype=float)
    if len(s) <= season:
        return np.array([], dtype=float)
    return np.array(s[:-season], dtype=float)
