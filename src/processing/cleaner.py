"""
Data Cleaning Pipeline.

Cleans and validates all raw datasets before feature engineering.
Handles duplicates, missing values, data type issues, and outliers.
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DATA_RAW, DATA_PROCESSED
from src.utils.helpers import save_csv, load_csv, logger


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate pharma sales data."""
    initial = len(df)
    df = df.drop_duplicates()
    df = df.dropna(subset=["drug_name", "revenue"])
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df = df.dropna(subset=["sale_date"])
    df["revenue"] = df["revenue"].clip(lower=0)
    df["units_sold"] = df["units_sold"].clip(lower=0)
    logger.info(f"Sales: {initial} → {len(df)} rows ({initial - len(df)} removed)")
    return df


def clean_hcp_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate HCP master data."""
    initial = len(df)
    df = df.drop_duplicates(subset=["hcp_id"])
    df["years_experience"] = df["years_experience"].clip(lower=0, upper=60)
    df["specialty"] = df["specialty"].fillna("General Practice")
    df["tier"] = df["tier"].fillna("Tier 3")
    logger.info(f"HCP: {initial} → {len(df)} rows")
    return df


def clean_territory_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate territory mapping data."""
    df = df.drop_duplicates(subset=["territory_id"])
    df["annual_quota"] = df["annual_quota"].clip(lower=0)
    df["assigned_rep_count"] = df["assigned_rep_count"].clip(lower=0)
    logger.info(f"Territories: {len(df)} rows")
    return df


def clean_rep_activity(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate rep activity data."""
    initial = len(df)
    df = df.drop_duplicates()
    df["activity_date"] = pd.to_datetime(df["activity_date"], errors="coerce")
    df = df.dropna(subset=["activity_date", "rep_id"])
    df["duration_minutes"] = df["duration_minutes"].clip(lower=0, upper=480)
    df["samples_left"] = df["samples_left"].clip(lower=0)
    logger.info(f"Rep activity: {initial} → {len(df)} rows")
    return df


def clean_prescriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate prescription data."""
    initial = len(df)
    df = df.drop_duplicates(subset=["prescription_id"])
    df["prescription_date"] = pd.to_datetime(df["prescription_date"], errors="coerce")
    df = df.dropna(subset=["prescription_date", "hcp_id", "drug_name"])
    df["quantity"] = df["quantity"].clip(lower=1)
    df["total_value"] = (df["quantity"] * df["unit_price"]).round(2)
    logger.info(f"Prescriptions: {initial} → {len(df)} rows")
    return df


def clean_promotions(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate promotion campaign data."""
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["budget"] = df["budget"].clip(lower=0)
    df["hcps_reached"] = df[["hcps_reached", "hcps_targeted"]].min(axis=1)
    logger.info(f"Promotions: {len(df)} rows")
    return df


def clean_all() -> dict:
    """
    Run the full cleaning pipeline on all raw datasets.
    Saves cleaned data to data/processed/.
    """
    logger.info("=" * 60)
    logger.info("Starting data cleaning pipeline")
    logger.info("=" * 60)

    results = {}

    # Load and clean each dataset
    datasets = {
        "pharma_sales": ("pharma_sales.csv", clean_sales_data),
        "hcp_master": ("hcp_master.csv", clean_hcp_data),
        "territories": ("territory_mapping.csv", clean_territory_data),
        "rep_activity": ("rep_activity.csv", clean_rep_activity),
        "prescriptions": ("prescription_data.csv", clean_prescriptions),
        "promotions": ("promotion_campaigns.csv", clean_promotions),
    }

    for name, (filename, cleaner) in datasets.items():
        filepath = os.path.join(DATA_RAW, filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            continue

        df = load_csv(filepath)
        df = cleaner(df)
        save_csv(df, os.path.join(DATA_PROCESSED, filename), f"cleaned {name}")
        results[name] = df

    logger.info("=" * 60)
    logger.info("Data cleaning complete!")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    results = clean_all()
    print("\n📊 Cleaning Summary:")
    for name, df in results.items():
        print(f"  {name:20s} → {len(df):>8,} rows")
