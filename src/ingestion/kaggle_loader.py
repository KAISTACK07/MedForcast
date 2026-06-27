"""
Kaggle Pharma Sales Data Loader.

Downloads and standardizes pharmaceutical sales data from Kaggle.
If the Kaggle API is not configured, falls back to generating a realistic
sales dataset synthetically so the pipeline can still run end-to-end.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DATA_RAW, RANDOM_STATE
from src.utils.helpers import save_csv, logger

# ── Constants ──────────────────────────────────────────────────────────────────
KAGGLE_DATASET = "milanzdravkovic/pharma-sales-data"
OUTPUT_FILE = os.path.join(DATA_RAW, "pharma_sales.csv")

# Drug names to use in synthetic fallback (realistic pharma products)
DRUG_NAMES = [
    "Lipitor", "Crestor", "Nexium", "Advair", "Humira",
    "Enbrel", "Remicade", "Avastin", "Herceptin", "Rituxan",
    "Lantus", "Januvia", "Lyrica", "Copaxone", "Neulasta",
    "Gleevec", "Revlimid", "Tecfidera", "Opdivo", "Keytruda",
]

TERRITORIES = [f"TER-{i+1:02d}" for i in range(20)]


def download_from_kaggle() -> pd.DataFrame:
    """Attempt to download pharma sales data from Kaggle."""
    try:
        import kaggle
        kaggle.api.dataset_download_files(
            KAGGLE_DATASET, path=DATA_RAW, unzip=True
        )
        # Find the downloaded CSV
        csv_files = [f for f in os.listdir(DATA_RAW) if f.endswith(".csv")]
        if csv_files:
            df = pd.read_csv(os.path.join(DATA_RAW, csv_files[0]))
            logger.info(f"Downloaded Kaggle dataset: {csv_files[0]} ({len(df)} rows)")
            return df
    except Exception as e:
        logger.warning(f"Kaggle download failed: {e}. Falling back to synthetic generation.")
    return None


def generate_synthetic_sales(n_months: int = 24, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """
    Generate a realistic synthetic pharma sales dataset.
    Includes seasonality, trend, and territory-level variation.
    """
    np.random.seed(seed)
    random.seed(seed)

    records = []
    base_date = datetime(2024, 1, 1)

    for month_offset in range(n_months):
        current_date = base_date + timedelta(days=30 * month_offset)
        month = current_date.month

        # Seasonal multiplier (flu season boost in winter)
        seasonal = 1.0 + 0.15 * np.sin(2 * np.pi * (month - 1) / 12)

        for drug in DRUG_NAMES:
            # Each drug has a base demand level
            drug_base = hash(drug) % 500 + 200

            for territory in TERRITORIES:
                # Territory-level variation
                territory_mult = 0.6 + (hash(territory + drug) % 100) / 100 * 0.8
                trend = 1.0 + month_offset * 0.005  # slight upward trend

                units = int(drug_base * territory_mult * seasonal * trend
                            * np.random.lognormal(0, 0.5))
                unit_price = round(np.random.uniform(15, 450), 2)
                revenue = round(units * unit_price, 2)

                # Generate 1-4 sale records per month per drug-territory
                n_records = random.randint(1, 4)
                for _ in range(n_records):
                    day = random.randint(1, 28)
                    sale_date = current_date.replace(day=day)
                    portion_units = max(1, units // n_records + random.randint(-5, 5))
                    portion_revenue = round(portion_units * unit_price, 2)

                    records.append({
                        "sale_date": sale_date.strftime("%Y-%m-%d"),
                        "drug_name": drug,
                        "territory_id": territory,
                        "units_sold": portion_units,
                        "unit_price": unit_price,
                        "revenue": portion_revenue,
                    })

    df = pd.DataFrame(records)
    logger.info(f"Generated synthetic sales data: {len(df)} rows")
    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to a consistent schema.
    Handles both Kaggle and synthetic column formats.
    """
    # Common rename mappings for Kaggle datasets
    rename_map = {
        "datum": "sale_date",
        "date": "sale_date",
        "Date": "sale_date",
        "product": "drug_name",
        "Product": "drug_name",
        "Drug": "drug_name",
        "quantity": "units_sold",
        "Quantity": "units_sold",
        "amount": "revenue",
        "Amount": "revenue",
        "Sales": "revenue",
        "region": "territory_id",
        "Region": "territory_id",
        "Territory": "territory_id",
    }

    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Ensure required columns exist
    required = ["sale_date", "drug_name", "units_sold", "revenue"]
    for col in required:
        if col not in df.columns:
            logger.warning(f"Missing column '{col}' — will need manual mapping")

    # Parse dates
    if "sale_date" in df.columns:
        df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")

    # Add territory_id if missing
    if "territory_id" not in df.columns:
        df["territory_id"] = np.random.choice(TERRITORIES, size=len(df))

    # Add unit_price if missing
    if "unit_price" not in df.columns and "revenue" in df.columns and "units_sold" in df.columns:
        df["unit_price"] = (df["revenue"] / df["units_sold"].clip(lower=1)).round(2)

    return df


def load_pharma_sales() -> pd.DataFrame:
    """
    Generate transactional pharma sales data for the PostgreSQL warehouse.

    Kaggle monthly sales data is reserved for the demand forecasting pipeline;
    it is not transformed into the pharma_sales warehouse table.
    """
    df = generate_synthetic_sales()
    df = standardize_columns(df)
    save_csv(df, OUTPUT_FILE, "pharma sales data")

    return df


if __name__ == "__main__":
    df = load_pharma_sales()
    print(f"\nPharma Sales Data Summary:")
    print(f"  Shape: {df.shape}")
    print(f"  Date range: {df['sale_date'].min()} to {df['sale_date'].max()}")
    print(f"  Drugs: {df['drug_name'].nunique()}")
    print(f"  Territories: {df['territory_id'].nunique()}")
    print(f"  Total Revenue: ${df['revenue'].sum():,.2f}")
