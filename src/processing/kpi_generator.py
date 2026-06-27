"""
KPI Generation Module.

Computes all dashboard KPIs from processed data:
  - Executive Summary KPIs
  - Territory KPIs
  - Promotion KPIs
  - HCP Segment KPIs
  - Rep Productivity KPIs
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DATA_PROCESSED, DATA_OUTPUT
from src.utils.helpers import save_csv, save_json, load_csv, logger, calculate_growth


def generate_executive_kpis(sales_df: pd.DataFrame,
                            rx_df: pd.DataFrame,
                            hcp_df: pd.DataFrame) -> dict:
    """Generate executive summary KPIs."""
    sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"])

    kpis = {
        "total_revenue": round(sales_df["revenue"].sum(), 2),
        "revenue_growth_pct": calculate_growth(sales_df, "sale_date", "revenue"),
        "active_hcps": int(rx_df["hcp_id"].nunique()),
        "total_hcps": int(hcp_df["hcp_id"].nunique()),
        "total_prescriptions": int(len(rx_df)),
        "total_units_sold": int(sales_df["units_sold"].sum()),
        "avg_revenue_per_territory": round(
            sales_df.groupby("territory_id")["revenue"].sum().mean(), 2
        ),
        "top_drug_by_revenue": (
            sales_df.groupby("drug_name")["revenue"].sum()
            .sort_values(ascending=False).index[0]
        ),
        "top_territory_by_revenue": (
            sales_df.groupby("territory_id")["revenue"].sum()
            .sort_values(ascending=False).index[0]
        ),
        "n_drugs": int(sales_df["drug_name"].nunique()),
        "n_territories": int(sales_df["territory_id"].nunique()),
    }

    logger.info(f"Executive KPIs: {len(kpis)} metrics computed")
    return kpis


def generate_territory_kpis(sales_df: pd.DataFrame,
                            territory_df: pd.DataFrame) -> pd.DataFrame:
    """Generate territory-level performance KPIs."""
    sales_df["sale_date"] = pd.to_datetime(sales_df["sale_date"])

    territory_rev = sales_df.groupby("territory_id").agg(
        total_revenue=("revenue", "sum"),
        total_units=("units_sold", "sum"),
        n_transactions=("revenue", "count"),
        n_drugs=("drug_name", "nunique"),
    ).reset_index()

    # Merge with territory master
    kpis = territory_rev.merge(territory_df, on="territory_id", how="left")

    # Calculate KPIs
    kpis["quota_attainment"] = (kpis["total_revenue"] / kpis["annual_quota"].clip(lower=1)).round(4)
    kpis["rank"] = kpis["total_revenue"].rank(ascending=False, method="dense").astype(int)
    kpis["revenue_contribution_pct"] = (
        kpis["total_revenue"] / kpis["total_revenue"].sum() * 100
    ).round(2)
    kpis["untapped_potential"] = (kpis["annual_quota"] - kpis["total_revenue"]).clip(lower=0).round(2)

    # Sort by rank
    kpis = kpis.sort_values("rank")

    logger.info(f"Territory KPIs: {len(kpis)} territories")
    return kpis


def generate_promotion_kpis(promo_df: pd.DataFrame) -> pd.DataFrame:
    """Generate promotion effectiveness KPIs."""
    kpis = promo_df.copy()

    kpis["rx_lift"] = kpis["prescriptions_after"] - kpis["prescriptions_before"]
    kpis["rx_lift_pct"] = (
        kpis["rx_lift"] / kpis["prescriptions_before"].clip(lower=1) * 100
    ).round(2)
    kpis["revenue_uplift"] = (kpis["revenue_after"] - kpis["revenue_before"]).round(2)
    kpis["roi"] = (kpis["revenue_uplift"] / kpis["budget"].clip(lower=1)).round(4)
    kpis["cost_per_rx_lift"] = (
        kpis["budget"] / kpis["rx_lift"].clip(lower=1)
    ).round(2)
    kpis["hcp_reach_pct"] = (
        kpis["hcps_reached"] / kpis["hcps_targeted"].clip(lower=1) * 100
    ).round(2)

    # Rank by ROI
    kpis["roi_rank"] = kpis["roi"].rank(ascending=False, method="dense").astype(int)

    logger.info(f"Promotion KPIs: {len(kpis)} campaigns")
    return kpis


def generate_all_kpis() -> dict:
    """Run the full KPI generation pipeline."""
    logger.info("=" * 60)
    logger.info("Starting KPI generation")
    logger.info("=" * 60)

    # Load cleaned data
    sales_df = load_csv(os.path.join(DATA_PROCESSED, "pharma_sales.csv"))
    hcp_df = load_csv(os.path.join(DATA_PROCESSED, "hcp_master.csv"))
    rx_df = load_csv(os.path.join(DATA_PROCESSED, "prescription_data.csv"))
    territory_df = load_csv(os.path.join(DATA_PROCESSED, "territory_mapping.csv"))
    promo_df = load_csv(os.path.join(DATA_PROCESSED, "promotion_campaigns.csv"))

    # Generate KPIs
    exec_kpis = generate_executive_kpis(sales_df, rx_df, hcp_df)
    territory_kpis = generate_territory_kpis(sales_df, territory_df)
    promo_kpis = generate_promotion_kpis(promo_df)

    # Save
    save_json(exec_kpis, os.path.join(DATA_OUTPUT, "executive_kpis.json"))
    save_csv(territory_kpis, os.path.join(DATA_OUTPUT, "territory_kpis.csv"), "territory KPIs")
    save_csv(promo_kpis, os.path.join(DATA_OUTPUT, "promotion_kpis.csv"), "promotion KPIs")

    logger.info("=" * 60)
    logger.info("KPI generation complete!")
    logger.info("=" * 60)

    return {
        "executive": exec_kpis,
        "territory": territory_kpis,
        "promotions": promo_kpis,
    }


if __name__ == "__main__":
    results = generate_all_kpis()
    print("\n📊 Executive KPIs:")
    for k, v in results["executive"].items():
        print(f"  {k:35s} → {v}")
