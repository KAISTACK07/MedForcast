import os, sys
import pandas as pd
from sqlalchemy import create_engine

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath('config/settings.py')))
from config.settings import DB_URI

engine = create_engine(DB_URI)

def upload_csv_to_db(filepath, table_name, engine):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath} - File not found.")
        return
        
    print(f"Uploading {filepath} to table '{table_name}'...")
    df = pd.read_csv(filepath)
    
    # Upload to PostgreSQL, replacing the table if it already exists
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    
    # Verify upload
    with engine.connect() as conn:
        count = pd.read_sql(f"SELECT COUNT(*) FROM {table_name}", conn).iloc[0,0]
        print(f"  SUCCESS: '{table_name}' now has {count} rows in PostgreSQL.\n")

files_to_sync = [
    # Cleaned Raw Data (Replacing dirty DB tables)
    ('data/raw/pharma_sales.csv', 'pharma_sales'),
    ('data/raw/drug_reference.csv', 'drug_reference'),
    
    # New Feature Data
    ('data/raw/demand_features.csv', 'demand_features'),
    ('data/raw/hcp_rfm_features.csv', 'hcp_rfm_features'),
    ('data/raw/rep_features.csv', 'rep_features'),
    
    # New ML Output Data (So Power BI can query them directly from Postgres)
    ('data/output/demand_forecasts.csv', 'demand_forecasts'),
    ('data/output/territory_forecasts.csv', 'territory_forecasts'),
    ('data/output/hcp_segments.csv', 'hcp_segments'),
    ('data/output/segment_summary.csv', 'segment_summary'),
    ('data/output/feature_importance.csv', 'public_feature_importance')
]

print("Starting PostgreSQL Sync...\n" + "="*50)
for filepath, table_name in files_to_sync:
    try:
        upload_csv_to_db(filepath, table_name, engine)
    except Exception as e:
        print(f"  FAILED to upload {filepath}: {e}\n")

print("="*50 + "\nSync Complete!")
