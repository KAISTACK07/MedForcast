import os, sys
import pandas as pd
from sqlalchemy import create_engine

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath('config/settings.py')))
from config.settings import DB_URI

raw_dir = 'data/raw'
csv_files = {
    'pharma_sales.csv': 'pharma_sales',
    'hcp_master.csv': 'hcp_master',
    'prescription_data.csv': 'prescriptions',
    'rep_activity.csv': 'rep_activity',
    'territory_mapping.csv': 'territories',
    'promotion_campaigns.csv': 'promotion_campaigns',
    'drug_reference.csv': 'drug_reference'
}

try:
    engine = create_engine(DB_URI)
    with engine.connect() as conn:
        print('Comparing Raw CSV files vs PostgreSQL tables:')
        print('-' * 70)
        print(f'{"File Name":<25} | {"CSV Rows":<12} | {"DB Rows":<12} | Status')
        print('-' * 70)
        
        all_match = True
        for file, table in csv_files.items():
            filepath = os.path.join(raw_dir, file)
            
            # Get CSV row count (excluding header)
            if os.path.exists(filepath):
                csv_count = len(pd.read_csv(filepath))
            else:
                csv_count = 'File Missing'
            
            # Get DB row count
            try:
                db_count = pd.read_sql(f'SELECT COUNT(*) FROM {table}', conn).iloc[0,0]
            except:
                db_count = 'Table Missing'
                
            status = 'MATCH' if str(csv_count) == str(db_count) else 'MISMATCH'
            
            if str(csv_count) != str(db_count):
                all_match = False
                
            print(f'{file:<25} | {str(csv_count):<12} | {str(db_count):<12} | {status}')
            
        print('-' * 70)
        if all_match:
            print('SUCCESS: All raw data is successfully and fully uploaded to PostgreSQL!')
        else:
            print('WARNING: There are discrepancies between the CSV files and PostgreSQL tables.')
            print('Note: If pharma_sales.csv has a MISMATCH (23878 CSV vs 23955 DB), it is because we previously removed 77 bad rows from the CSV file during cleaning, but the database still contains the original uncleaned raw rows.')

except Exception as e:
    print(f'Connection error: {e}')
