import numpy as np

def mape(y, yhat):
    y, yhat = np.array(y, dtype=float), np.array(yhat, dtype=float)
    mask = y != 0
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs((y[mask] - yhat[mask]) / y[mask])) * 100)

def mae(y, yhat):
    return float(np.mean(np.abs(np.array(y, dtype=float) - np.array(yhat, dtype=float))))

def rmse(y, yhat):
    return float(np.sqrt(np.mean((np.array(y, dtype=float) - np.array(yhat, dtype=float)) ** 2)))

def r2(y, yhat):
    y, yhat = np.array(y, dtype=float), np.array(yhat, dtype=float)
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot else 0.0

def all_metrics(y, yhat):
    return {
        "MAPE": mape(y, yhat),
        "MAE": mae(y, yhat),
        "RMSE": rmse(y, yhat),
        "R2": r2(y, yhat),
    }
