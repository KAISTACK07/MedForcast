"""
Feature Engineering Module.

Creates features for three ML models:
  1. Demand Forecasting: temporal, lag, and rolling features
  2. HCP Segmentation: RFM (Recency, Frequency, Monetary) features
  3. Rep Effectiveness: productivity and coverage features
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DATA_RAW, DATA_PROCESSED, DATA_OUTPUT
from src.utils.helpers import save_csv, load_csv, logger


# ══════════════════════════════════════════════════════════════════════════════
#  1. DEMAND FORECASTING FEATURES
# ══════════════════════════════════════════════════════════════════════════════

def create_demand_features(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create time-series features for XGBoost demand forecasting.

    Features:
      - Temporal: month, quarter, year, day_of_week, is_quarter_end
      - Lag: lag_1, lag_3, lag_6 (units sold)
      - Rolling: rolling_mean_3, rolling_std_3
      - Categorical: drug encoded, territory encoded
    """
    logger.info("Creating demand forecasting features...")

    # Aggregate to monthly drug-territory level
    df = sales_df.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["year_month"] = df["sale_date"].dt.to_period("M")

    monthly = df.groupby(["year_month", "drug_name", "territory_id"]).agg(
        units_sold=("units_sold", "sum"),
        revenue=("revenue", "sum"),
        n_transactions=("revenue", "count"),
        avg_unit_price=("unit_price", "mean"),
    ).reset_index()

    monthly["year_month"] = monthly["year_month"].dt.to_timestamp()

    # Temporal features
    monthly["month"] = monthly["year_month"].dt.month
    monthly["quarter"] = monthly["year_month"].dt.quarter
    monthly["year"] = monthly["year_month"].dt.year
    monthly["day_of_week"] = monthly["year_month"].dt.dayofweek
    monthly["is_quarter_end"] = monthly["year_month"].dt.is_quarter_end.astype(int)

    # Sort for lag computation
    monthly = monthly.sort_values(["drug_name", "territory_id", "year_month"])

    # Lag features (per drug-territory combination)
    group_cols = ["drug_name", "territory_id"]
    for lag in [1, 3, 6]:
        monthly[f"lag_{lag}"] = (
            monthly.groupby(group_cols)["units_sold"].shift(lag)
        )

    # Rolling features
    monthly["rolling_mean_3"] = (
        monthly.groupby(group_cols)["units_sold"]
        .transform(lambda x: x.rolling(3, min_periods=1).mean())
    )
    monthly["rolling_std_3"] = (
        monthly.groupby(group_cols)["units_sold"]
        .transform(lambda x: x.rolling(3, min_periods=1).std())
    )
    monthly["rolling_std_3"] = monthly["rolling_std_3"].fillna(0)

    # Encode categorical variables
    monthly["drug_encoded"] = monthly["drug_name"].astype("category").cat.codes
    monthly["territory_encoded"] = monthly["territory_id"].astype("category").cat.codes

    # Drop rows with NaN lags (first few months per group)
    monthly = monthly.dropna(subset=["lag_1"])

    logger.info(f"Demand features: {len(monthly)} rows, {len(monthly.columns)} columns")
    return monthly


def load_kaggle_monthly_sales() -> pd.DataFrame:
    """
    Load Kaggle monthly sales data for demand forecasting.

    This source is intentionally separate from pharma_sales.csv, which is
    transactional warehouse data for SQL analytics and Power BI dashboards.
    """
    filepath = os.path.join(DATA_RAW, "pharma-sales-data", "salesmonthly.csv")
    df = load_csv(filepath)
    df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
    df = df.dropna(subset=["datum"])

    monthly = df.melt(
        id_vars=["datum"],
        var_name="drug_name",
        value_name="units_sold",
    )
    monthly["territory_id"] = "KAGGLE-MONTHLY"
    monthly["sale_date"] = monthly["datum"]
    monthly["unit_price"] = 1.0
    monthly["revenue"] = monthly["units_sold"].clip(lower=0)

    return monthly[["sale_date", "drug_name", "territory_id", "units_sold", "unit_price", "revenue"]]


# ══════════════════════════════════════════════════════════════════════════════
#  2. HCP SEGMENTATION FEATURES (RFM)
# ══════════════════════════════════════════════════════════════════════════════

def create_hcp_rfm_features(rx_df: pd.DataFrame,
                            hcp_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Create RFM (Recency, Frequency, Monetary) features for HCP segmentation.

    Features:
      - recency: days since last prescription
      - frequency: total number of prescriptions
      - monetary: total prescription revenue
      - avg_rx_value: average value per prescription
      - unique_drugs: number of distinct drugs prescribed
      - total_quantity: total units prescribed
      - prescription_span: days between first and last prescription
    """
    logger.info("Creating HCP RFM features...")

    rx_df["prescription_date"] = pd.to_datetime(rx_df["prescription_date"])
    reference_date = rx_df["prescription_date"].max()

    rfm = rx_df.groupby("hcp_id").agg(
        recency=("prescription_date", lambda x: (reference_date - x.max()).days),
        frequency=("prescription_id", "count"),
        monetary=("total_value", "sum"),
        avg_rx_value=("total_value", "mean"),
        unique_drugs=("drug_name", "nunique"),
        total_quantity=("quantity", "sum"),
        first_rx_date=("prescription_date", "min"),
        last_rx_date=("prescription_date", "max"),
    ).reset_index()

    # Prescription span in days
    rfm["prescription_span"] = (rfm["last_rx_date"] - rfm["first_rx_date"]).dt.days
    rfm = rfm.drop(columns=["first_rx_date", "last_rx_date"])

    # Round monetary columns
    rfm["monetary"] = rfm["monetary"].round(2)
    rfm["avg_rx_value"] = rfm["avg_rx_value"].round(2)

    # Merge with HCP master for additional features
    if hcp_df is not None:
        rfm = rfm.merge(
            hcp_df[["hcp_id", "specialty", "tier", "years_experience", "territory_id"]],
            on="hcp_id",
            how="left",
        )

    logger.info(f"HCP RFM features: {len(rfm)} HCPs, {len(rfm.columns)} features")
    return rfm


# ══════════════════════════════════════════════════════════════════════════════
#  3. REP EFFECTIVENESS FEATURES
# ══════════════════════════════════════════════════════════════════════════════

def create_rep_features(rep_df: pd.DataFrame,
                        rx_df: pd.DataFrame,
                        hcp_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Create sales rep productivity and effectiveness features.

    Features:
      - total_activities, total_visits, total_calls, total_meetings
      - unique_hcps_covered
      - avg_duration
      - total_samples_distributed
      - positive_outcome_rate
      - prescription_lift (estimated from HCP Rx before/after visits)
      - revenue_generated (from HCPs in rep's territory)
    """
    logger.info("Creating rep effectiveness features...")

    rep_df["activity_date"] = pd.to_datetime(rep_df["activity_date"])

    # Base activity metrics
    rep_metrics = rep_df.groupby("rep_id").agg(
        rep_name=("rep_name", "first"),
        territory_id=("territory_id", "first"),
        total_activities=("activity_type", "count"),
        total_visits=("activity_type", lambda x: (x == "Visit").sum()),
        total_calls=("activity_type", lambda x: (x == "Phone Call").sum()),
        total_meetings=("activity_type", lambda x: (x == "Virtual Meeting").sum()),
        total_sample_drops=("activity_type", lambda x: (x == "Sample Drop").sum()),
        unique_hcps_covered=("hcp_id", "nunique"),
        avg_duration=("duration_minutes", "mean"),
        total_samples=("samples_left", "sum"),
        positive_outcomes=("outcome", lambda x: (x == "Positive").sum()),
        followup_outcomes=("outcome", lambda x: (x == "Follow-up Required").sum()),
        active_days=("activity_date", "nunique"),
    ).reset_index()

    # Derived metrics
    rep_metrics["positive_outcome_rate"] = (
        rep_metrics["positive_outcomes"] / rep_metrics["total_activities"]
    ).round(4)
    rep_metrics["avg_activities_per_day"] = (
        rep_metrics["total_activities"] / rep_metrics["active_days"].clip(lower=1)
    ).round(2)
    rep_metrics["avg_duration"] = rep_metrics["avg_duration"].round(1)

    # Calculate revenue generated from rep's territory HCPs
    rx_df["prescription_date"] = pd.to_datetime(rx_df["prescription_date"])
    if hcp_df is not None:
        # Map HCPs to territories
        hcp_territory = hcp_df.set_index("hcp_id")["territory_id"].to_dict()
        rx_df["territory_id"] = rx_df["hcp_id"].map(hcp_territory)

    territory_revenue = rx_df.groupby("territory_id")["total_value"].sum().reset_index()
    territory_revenue.columns = ["territory_id", "territory_rx_revenue"]

    rep_metrics = rep_metrics.merge(territory_revenue, on="territory_id", how="left")
    rep_metrics["territory_rx_revenue"] = rep_metrics["territory_rx_revenue"].fillna(0).round(2)

    # Estimate prescription lift per visit (simplified)
    # Higher-activity reps in territories with more Rx revenue get higher lift scores
    rep_metrics["est_rx_lift_per_visit"] = (
        rep_metrics["territory_rx_revenue"]
        / rep_metrics["total_visits"].clip(lower=1)
        * rep_metrics["positive_outcome_rate"]
    ).round(2)

    # HCP coverage percentage
    if hcp_df is not None:
        territory_hcp_counts = hcp_df.groupby("territory_id")["hcp_id"].count().to_dict()
        rep_metrics["territory_total_hcps"] = (
            rep_metrics["territory_id"].map(territory_hcp_counts).fillna(0).astype(int)
        )
        rep_metrics["hcp_coverage_pct"] = (
            rep_metrics["unique_hcps_covered"]
            / rep_metrics["territory_total_hcps"].clip(lower=1)
            * 100
        ).round(2)

    logger.info(f"Rep features: {len(rep_metrics)} reps, {len(rep_metrics.columns)} features")
    return rep_metrics


# ══════════════════════════════════════════════════════════════════════════════
#  Main Entry Point
# ══════════════════════════════════════════════════════════════════════════════

def engineer_all_features() -> dict:
    """
    Run the full feature engineering pipeline.
    """
    logger.info("=" * 60)
    logger.info("Starting feature engineering pipeline")
    logger.info("=" * 60)

    # Load cleaned data
    sales_df = load_csv(os.path.join(DATA_PROCESSED, "pharma_sales.csv"))
    hcp_df = load_csv(os.path.join(DATA_PROCESSED, "hcp_master.csv"))
    rx_df = load_csv(os.path.join(DATA_PROCESSED, "prescription_data.csv"))
    rep_df = load_csv(os.path.join(DATA_PROCESSED, "rep_activity.csv"))

    # Create features
    demand_features = create_demand_features(sales_df)
    hcp_rfm = create_hcp_rfm_features(rx_df, hcp_df)
    rep_features = create_rep_features(rep_df, rx_df, hcp_df)

    # Save
    save_csv(demand_features, os.path.join(DATA_PROCESSED, "demand_features.csv"), "demand features")
    save_csv(hcp_rfm, os.path.join(DATA_PROCESSED, "hcp_rfm_features.csv"), "HCP RFM features")
    save_csv(rep_features, os.path.join(DATA_PROCESSED, "rep_features.csv"), "rep features")

    logger.info("=" * 60)
    logger.info("Feature engineering complete!")
    logger.info("=" * 60)

    return {
        "demand_features": demand_features,
        "hcp_rfm": hcp_rfm,
        "rep_features": rep_features,
    }


if __name__ == "__main__":
    import os as _os
    results = engineer_all_features()
    print("\n📊 Feature Engineering Summary:")
    for name, df in results.items():
        print(f"  {name:20s} → {len(df):>8,} rows, {len(df.columns):>3} columns")
