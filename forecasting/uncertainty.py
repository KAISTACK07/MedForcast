"""Uncertainty quantification via residual bootstrap."""
import numpy as np
import pandas as pd

def bootstrap_intervals(point_preds, val_residuals, n=1000, lo=5, hi=95, seed=42):
    """
    Computes (lo, hi) percentile prediction intervals using residual bootstrap.
    Default lo=5, hi=95 produces a 90% prediction interval with seed=42.
    """
    rng = np.random.default_rng(seed)
    res = np.array(val_residuals, dtype=float)
    point_preds = np.array(point_preds, dtype=float)
    if len(res) == 0:
        return point_preds, point_preds
    sims = point_preds[:, None] + rng.choice(res, size=(len(point_preds), n))
    # Demand cannot be negative
    sims = np.clip(sims, 0, None)
    lower = np.percentile(sims, lo, axis=1)
    upper = np.percentile(sims, hi, axis=1)
    return lower, upper

def compute_uncertainty_metrics(df_eval):
    """
    Evaluates empirical coverage (fraction of actuals in [lower_bound, upper_bound])
    and average interval width.
    Also breaks down coverage by territory and by month.
    """
    df = df_eval.copy()
    inside = (df["actual"] >= df["lower_bound"]) & (df["actual"] <= df["upper_bound"])
    df["inside_interval"] = inside
    df["interval_width"] = df["upper_bound"] - df["lower_bound"]

    overall_coverage = float(inside.mean() * 100)
    avg_width = float(df["interval_width"].mean())
    median_width = float(df["interval_width"].median())

    by_territory = None
    if "territory_id" in df.columns:
        by_territory = df.groupby("territory_id").agg(
            coverage_pct=("inside_interval", lambda x: float(x.mean() * 100)),
            avg_width=("interval_width", "mean"),
            n=("actual", "count"),
        ).reset_index()
        by_territory["coverage_pct"] = by_territory["coverage_pct"].round(2)
        by_territory["avg_width"] = by_territory["avg_width"].round(2)

    by_month = None
    if "year_month" in df.columns:
        by_month = df.groupby("year_month").agg(
            coverage_pct=("inside_interval", lambda x: float(x.mean() * 100)),
            avg_width=("interval_width", "mean"),
            n=("actual", "count"),
        ).reset_index()
        by_month["coverage_pct"] = by_month["coverage_pct"].round(2)
        by_month["avg_width"] = by_month["avg_width"].round(2)

    return {
        "overall_coverage_pct": round(overall_coverage, 2),
        "target_coverage_pct": 90.0,
        "average_width": round(avg_width, 2),
        "median_width": round(median_width, 2),
        "by_territory": by_territory,
        "by_month": by_month,
        "df_with_intervals": df,
    }
