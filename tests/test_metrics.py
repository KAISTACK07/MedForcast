"""Tests for forecasting metrics."""
import pytest
import numpy as np
from forecasting.metrics import mape, mae, rmse, r2, all_metrics

def test_mape_known_values():
    y = [100.0, 200.0]
    yhat = [110.0, 190.0]
    # |(100-110)/100| = 0.10, |(200-190)/200| = 0.05. Mean = 0.075 -> 7.5%
    assert mape(y, yhat) == pytest.approx(7.5, rel=1e-5)

def test_mae_known_values():
    y = [10.0, 20.0, 30.0]
    yhat = [12.0, 19.0, 33.0]
    # errors: 2, 1, 3. Mean = 2.0
    assert mae(y, yhat) == pytest.approx(2.0, rel=1e-5)

def test_rmse_known_values():
    y = [10.0, 20.0]
    yhat = [13.0, 16.0]
    # sq errors: 9, 16. Mean = 12.5. sqrt(12.5) = 3.5355339
    assert rmse(y, yhat) == pytest.approx(np.sqrt(12.5), rel=1e-5)

def test_r2_perfect_score():
    y = [10.0, 20.0, 30.0]
    yhat = [10.0, 20.0, 30.0]
    assert r2(y, yhat) == pytest.approx(1.0, rel=1e-5)

def test_all_metrics_output():
    y = [10.0, 20.0]
    yhat = [11.0, 19.0]
    res = all_metrics(y, yhat)
    assert set(res.keys()) == {"MAPE", "MAE", "RMSE", "R2"}
    assert all(isinstance(v, float) for v in res.values())
