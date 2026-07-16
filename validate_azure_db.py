import sys, os
import pandas as pd
from sqlalchemy import create_engine, text

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath('config/settings.py')))
from config.settings import DB_URI

def print_section(title):
    print(f"\n{'-'*60}")
    print(f"  {title.upper()}")
    print(f"{'-'*60}")

def run_validation():
    try:
        engine = create_engine(DB_URI)
        with engine.connect() as conn:
            
            # 1. Row counts
            print_section("Database Validation")
            tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name", conn)
            
            if tables.empty:
                print("No tables found!")
                return
                
            for t in tables['table_name']:
                count = pd.read_sql(f"SELECT COUNT(*) FROM {t}", conn).iloc[0,0]
                print(f"✓ {t:25s} ...... {count} rows")

            # 2. Relationship Verification (Sanity Checks)
            print_section("Relationship Verification")
            
            # Check reps matching territories
            q1 = "SELECT COUNT(*) FROM rep_activity r LEFT JOIN territories t ON r.territory_id = t.territory_id WHERE t.territory_id IS NULL"
            unmatched_reps = pd.read_sql(q1, conn).iloc[0,0]
            print(f"Orphaned rep_activity records (no territory): {unmatched_reps}")
            
            # Check HCPs matching territories
            q2 = "SELECT COUNT(*) FROM hcp_master h LEFT JOIN territories t ON h.territory_id = t.territory_id WHERE t.territory_id IS NULL"
            unmatched_hcps = pd.read_sql(q2, conn).iloc[0,0]
            print(f"Orphaned hcp_master records (no territory): {unmatched_hcps}")
            
            # Check prescriptions matching HCPs
            q3 = "SELECT COUNT(*) FROM prescriptions p LEFT JOIN hcp_master h ON p.hcp_id = h.hcp_id WHERE h.hcp_id IS NULL"
            unmatched_rx = pd.read_sql(q3, conn).iloc[0,0]
            print(f"Orphaned prescriptions (no HCP): {unmatched_rx}")

            # 3. Sample Data Queries
            print_section("Sample Data: territories")
            print(pd.read_sql("SELECT * FROM territories LIMIT 3", conn).to_string(index=False))
            
            print_section("Sample Data: hcp_segments")
            print(pd.read_sql("SELECT hcp_id, segment, total_revenue FROM hcp_segments LIMIT 3", conn).to_string(index=False))
            
            print_section("Sample Data: demand_forecasts")
            print(pd.read_sql("SELECT territory_id, drug_name, month, forecast_sales FROM demand_forecasts LIMIT 3", conn).to_string(index=False))

    except Exception as e:
        print(f"Validation failed: {e}")

if __name__ == "__main__":
    run_validation()
