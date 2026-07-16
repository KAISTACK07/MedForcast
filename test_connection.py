import os
import sys
from sqlalchemy import create_engine, text

# Add project root to path so we can import config
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import DB_URI

def test_azure_connection():
    print(f"Attempting to connect with URI: {DB_URI.replace(os.getenv('DB_PASSWORD', 'secret'), '***')}")
    try:
        engine = create_engine(DB_URI)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).fetchone()
            print("\nAzure PostgreSQL connection successful!")
            print(f"Server version: {result[0]}")
            
            # List tables
            print("\nExisting tables in database:")
            tables = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchall()
            
            if not tables:
                print("  (No tables found. The database is empty.)")
            else:
                for table in tables:
                    print(f"  - {table[0]}")
                    
    except Exception as e:
        print(f"\nConnection failed: {e}")

if __name__ == "__main__":
    test_azure_connection()
