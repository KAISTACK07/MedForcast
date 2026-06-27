"""
Database Loader — loads processed CSV data into PostgreSQL.

Loads tables in dependency order to satisfy foreign key constraints.
Supports both 'replace' and 'append' modes.
"""
import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DB_URI, DATA_RAW, DATA_OUTPUT
from src.utils.helpers import logger

# ── Table load order (respects foreign key dependencies) ───────────────────────
LOAD_ORDER = [
    ("drug_reference", os.path.join(DATA_RAW, "drug_reference.csv")),
    ("territories", os.path.join(DATA_RAW, "territory_mapping.csv")),
    ("hcp_master", os.path.join(DATA_RAW, "hcp_master.csv")),
    ("pharma_sales", os.path.join(DATA_RAW, "pharma_sales.csv")),
    ("rep_activity", os.path.join(DATA_RAW, "rep_activity.csv")),
    ("prescriptions", os.path.join(DATA_RAW, "prescription_data.csv")),
    ("promotion_campaigns", os.path.join(DATA_RAW, "promotion_campaigns.csv")),
]

# Optional output tables (loaded after ML pipeline runs)
OUTPUT_TABLES = [
    ("demand_forecasts", os.path.join(DATA_OUTPUT, "demand_forecasts.csv")),
    ("hcp_segments", os.path.join(DATA_OUTPUT, "hcp_segments.csv")),
    ("rep_scorecard", os.path.join(DATA_OUTPUT, "rep_scorecard.csv")),
    ("territory_kpis", os.path.join(DATA_OUTPUT, "territory_kpis.csv")),
    ("promotion_kpis", os.path.join(DATA_OUTPUT, "promotion_kpis.csv")),
]


def get_engine():
    """Create SQLAlchemy engine."""
    return create_engine(DB_URI)


def load_table(engine, table_name: str, filepath: str,
               if_exists: str = "append") -> int:
    """
    Load a single CSV file into a PostgreSQL table.
    Returns the number of rows loaded.
    """
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath} — skipping {table_name}")
        return 0

    df = pd.read_csv(filepath)

    # Handle date columns
    date_cols = [c for c in df.columns if "date" in c.lower()]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df.to_sql(table_name, engine, if_exists=if_exists, index=False, method="multi")
    logger.info(f"✅ Loaded {len(df):>8,} rows into {table_name}")
    return len(df)


def load_all_raw_tables() -> dict:
    """Load all raw data tables into PostgreSQL."""
    engine = get_engine()
    results = {}

    logger.info("=" * 60)
    logger.info("Loading raw data into PostgreSQL")
    logger.info("=" * 60)

    for table_name, filepath in LOAD_ORDER:
        rows = load_table(engine, table_name, filepath)
        results[table_name] = rows

    return results


def load_output_tables() -> dict:
    """Load ML output tables into PostgreSQL (run after ML pipeline)."""
    engine = get_engine()
    results = {}

    logger.info("=" * 60)
    logger.info("Loading ML output tables into PostgreSQL")
    logger.info("=" * 60)

    for table_name, filepath in OUTPUT_TABLES:
        rows = load_table(engine, table_name, filepath)
        results[table_name] = rows

    return results


def validate_load(engine) -> pd.DataFrame:
    """Run validation queries against loaded data."""
    query = """
    SELECT 'drug_reference' AS tbl, COUNT(*) AS cnt FROM drug_reference
    UNION ALL SELECT 'territories', COUNT(*) FROM territories
    UNION ALL SELECT 'hcp_master', COUNT(*) FROM hcp_master
    UNION ALL SELECT 'pharma_sales', COUNT(*) FROM pharma_sales
    UNION ALL SELECT 'rep_activity', COUNT(*) FROM rep_activity
    UNION ALL SELECT 'prescriptions', COUNT(*) FROM prescriptions
    UNION ALL SELECT 'promotion_campaigns', COUNT(*) FROM promotion_campaigns
    ORDER BY tbl;
    """
    with engine.connect() as conn:
        result = pd.read_sql(text(query), conn)
    logger.info(f"\nTable row counts:\n{result.to_string(index=False)}")
    return result


def check_referential_integrity(engine) -> bool:
    """Verify foreign key relationships are intact."""
    checks = [
        ("HCP → Territory", """
            SELECT COUNT(*) AS orphans FROM hcp_master h
            LEFT JOIN territories t ON h.territory_id = t.territory_id
            WHERE t.territory_id IS NULL
        """),
        ("Sales → Territory", """
            SELECT COUNT(*) AS orphans FROM pharma_sales s
            LEFT JOIN territories t ON s.territory_id = t.territory_id
            WHERE s.territory_id IS NOT NULL AND t.territory_id IS NULL
        """),
        ("Rep → Territory", """
            SELECT COUNT(*) AS orphans FROM rep_activity r
            LEFT JOIN territories t ON r.territory_id = t.territory_id
            WHERE r.territory_id IS NOT NULL AND t.territory_id IS NULL
        """),
        ("Rx → HCP", """
            SELECT COUNT(*) AS orphans FROM prescriptions p
            LEFT JOIN hcp_master h ON p.hcp_id = h.hcp_id
            WHERE h.hcp_id IS NULL
        """),
        ("Rep → HCP", """
            SELECT COUNT(*) AS orphans FROM rep_activity r
            LEFT JOIN hcp_master h ON r.hcp_id = h.hcp_id
            WHERE r.hcp_id IS NOT NULL AND h.hcp_id IS NULL
        """),
    ]

    all_valid = True
    with engine.connect() as conn:
        for name, query in checks:
            result = conn.execute(text(query)).fetchone()
            orphans = result[0]
            if orphans > 0:
                logger.error(f"❌ {name}: {orphans} orphan records found")
                all_valid = False
            else:
                logger.info(f"✅ {name}: OK")

    return all_valid


if __name__ == "__main__":
    results = load_all_raw_tables()
    engine = get_engine()
    validate_load(engine)
    check_referential_integrity(engine)

    total = sum(results.values())
    print(f"\n📊 Total rows loaded: {total:,}")
