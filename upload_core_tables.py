import sys, os
import pandas as pd
from sqlalchemy import create_engine, text

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath('config/settings.py')))
from config.settings import DB_URI

engine = create_engine(DB_URI)

# Drop all FK constraints first, then reload in dependency order
with engine.connect() as conn:
    # Drop FK constraints
    constraints = conn.execute(text("""
        SELECT tc.constraint_name, tc.table_name
        FROM information_schema.table_constraints tc
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
    """)).fetchall()
    
    for constraint_name, table_name in constraints:
        conn.execute(text(f'ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}'))
        print(f"  Dropped FK: {table_name}.{constraint_name}")
    conn.commit()

print("\nFK constraints removed. Uploading tables...")

# Upload in dependency order: parent tables first
files = [
    ('data/raw/territory_mapping.csv', 'territories'),
    ('data/raw/hcp_master.csv', 'hcp_master'),
    ('data/raw/prescription_data.csv', 'prescriptions'),
    ('data/raw/rep_activity.csv', 'rep_activity'),
    ('data/raw/promotion_campaigns.csv', 'promotion_campaigns'),
]

for filepath, table_name in files:
    df = pd.read_csv(filepath)
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    with engine.connect() as conn:
        count = pd.read_sql(f"SELECT COUNT(*) FROM {table_name}", conn).iloc[0,0]
        print(f"  {table_name}: {count} rows uploaded")

print("\nAll core tables synced to PostgreSQL!")
