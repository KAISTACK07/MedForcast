import os, sys
import pandas as pd
from sqlalchemy import create_engine

sys.path.insert(0, os.path.dirname(os.path.abspath('config/settings.py')))
from config.settings import DB_URI

try:
    engine = create_engine(DB_URI)
    with engine.connect() as conn:
        tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'", conn)
        if tables.empty:
            print("No tables found in PostgreSQL 'public' schema.")
        else:
            print("Tables in PostgreSQL:")
            for t in tables['table_name']:
                count = pd.read_sql(f"SELECT COUNT(*) FROM {t}", conn).iloc[0,0]
                print(f"  - {t}: {count} rows")
except Exception as e:
    print(f"Connection error: {e}")
