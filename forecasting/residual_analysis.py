"""Residual analysis module."""
import numpy as np
import pandas as pd

def analyze_residuals(df_preds):
    """
    Computes residual = actual - predicted, abs_error = |residual|.
    Calculates overall, territory, month, and product level summaries.
    Determines bias direction in plain words.
    """
    df = df_preds.copy()
    if "residual" not in df.columns:
        df["residual"] = df["actual"] - df["predicted"]
    if "absolute_error" not in df.columns:
        df["absolute_error"] = np.abs(df["residual"])

    mean_res = float(df["residual"].mean())
    median_res = float(df["residual"].median())
    mean_abs_err = float(df["absolute_error"].mean())
    median_abs_err = float(df["absolute_error"].median())

    if mean_res > 1e-4:
        bias_direction = "underprediction (actuals are higher than forecasts on average)"
    elif mean_res < -1e-4:
        bias_direction = "overprediction (forecasts are higher than actuals on average)"
    else:
        bias_direction = "unbiased (mean residual is approximately zero)"

    overall = {
        "mean_residual": round(mean_res, 4),
        "median_residual": round(median_res, 4),
        "mean_absolute_error": round(mean_abs_err, 4),
        "median_absolute_error": round(median_abs_err, 4),
        "bias_direction": bias_direction,
        "n_predictions": len(df),
    }

    # Grouped by territory
    by_territory = None
    if "territory_id" in df.columns:
        by_territory = df.groupby("territory_id").agg(
            mean_residual=("residual", "mean"),
            median_residual=("residual", "median"),
            mae=("absolute_error", "mean"),
            count=("residual", "count"),
        ).reset_index()
        by_territory["mean_residual"] = by_territory["mean_residual"].round(4)
        by_territory["median_residual"] = by_territory["median_residual"].round(4)
        by_territory["mae"] = by_territory["mae"].round(4)

    # Grouped by month
    by_month = None
    if "year_month" in df.columns:
        by_month = df.groupby("year_month").agg(
            mean_residual=("residual", "mean"),
            median_residual=("residual", "median"),
            mae=("absolute_error", "mean"),
            count=("residual", "count"),
        ).reset_index()
        by_month["mean_residual"] = by_month["mean_residual"].round(4)
        by_month["median_residual"] = by_month["median_residual"].round(4)
        by_month["mae"] = by_month["mae"].round(4)

    # Grouped by product
    by_product = None
    if "drug_name" in df.columns:
        by_product = df.groupby("drug_name").agg(
            mean_residual=("residual", "mean"),
            median_residual=("residual", "median"),
            mae=("absolute_error", "mean"),
            count=("residual", "count"),
        ).reset_index()
        by_product["mean_residual"] = by_product["mean_residual"].round(4)
        by_product["median_residual"] = by_product["median_residual"].round(4)
        by_product["mae"] = by_product["mae"].round(4)
    else:
        product_note = "product-level: NOT SUPPORTED at current grain"

    worst_territory = None
    if by_territory is not None and len(by_territory) > 0:
        worst_territory = by_territory.sort_values("mae", ascending=False).iloc[0]["territory_id"]

    worst_month = None
    if by_month is not None and len(by_month) > 0:
        worst_month = str(by_month.sort_values("mae", ascending=False).iloc[0]["year_month"])

    return {
        "overall": overall,
        "by_territory": by_territory,
        "by_month": by_month,
        "by_product": by_product,
        "worst_territory": worst_territory,
        "worst_month": worst_month,
        "bias_direction": bias_direction,
        "df_with_residuals": df,
    }
