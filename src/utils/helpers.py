"""
Utility helper functions for the Pharma Analytics platform.
"""
import os
import json
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("pharma_analytics")


def save_csv(df: pd.DataFrame, filepath: str, description: str = "") -> None:
    """Save a DataFrame to CSV with logging."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(df)} rows to {filepath} {f'({description})' if description else ''}")


def load_csv(filepath: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame with logging."""
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    return df


def save_json(data: dict, filepath: str) -> None:
    """Save a dictionary to JSON."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved JSON to {filepath}")


def load_json(filepath: str) -> dict:
    """Load a JSON file into a dictionary."""
    with open(filepath, "r") as f:
        return json.load(f)


def calculate_growth(df: pd.DataFrame, date_col: str = "sale_date",
                     value_col: str = "revenue", period: str = "M") -> float:
    """
    Calculate period-over-period growth rate.
    Returns the average growth rate across periods.
    """
    periodic = df.set_index(date_col).resample(period)[value_col].sum()
    if len(periodic) < 2:
        return 0.0
    growth_rates = periodic.pct_change().dropna()
    return round(growth_rates.mean() * 100, 2)
