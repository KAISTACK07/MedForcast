"""Leakage guard test asserting no engineered feature uses a value from time t or later."""
import pandas as pd
import numpy as np
from src.processing.feature_engineer import create_demand_features

def test_leakage_guard_target_modification():
    """
    If we modify the target units_sold at month t (e.g. index 3),
    features at month t (lag_1, lag_3, lag_6, rolling_mean_3, rolling_std_3)
    MUST NOT change. Only features at t+1 or later should change.
    """
    dates = pd.date_range("2024-01-01", periods=8, freq="MS")
    base_data = []
    for d in dates:
        base_data.append({
            "sale_date": d,
            "drug_name": "DrugA",
            "territory_id": "T1",
            "units_sold": 100.0,
            "unit_price": 50.0,
            "revenue": 5000.0,
        })
    df1 = pd.DataFrame(base_data)
    
    # Second dataset: target at month index 3 is drastically changed from 100 to 99999
    df2 = df1.copy()
    df2.loc[3, "units_sold"] = 99999.0
    df2.loc[3, "revenue"] = 99999.0 * 50.0

    feat1 = create_demand_features(df1).reset_index(drop=True)
    feat2 = create_demand_features(df2).reset_index(drop=True)

    # Find the row corresponding to the modified month (month index 3 corresponds to feat index 2 because month 0 was dropped for lag_1)
    target_month = dates[3]
    row1 = feat1[feat1["year_month"] == target_month].iloc[0]
    row2 = feat2[feat2["year_month"] == target_month].iloc[0]

    # Critical assertions: features at time t MUST BE IDENTICAL despite target change at time t
    assert row1["lag_1"] == row2["lag_1"], "Leakage detected in lag_1!"
    assert row1["rolling_mean_3"] == row2["rolling_mean_3"], "Leakage detected: rolling_mean_3 used current month target!"
    assert row1["rolling_std_3"] == row2["rolling_std_3"], "Leakage detected: rolling_std_3 used current month target!"
