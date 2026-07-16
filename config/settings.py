"""
Central configuration for the Pharma Analytics platform.
Loads settings from environment variables and provides defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED = DATA_RAW  # Consolidated: processed data lives in data/raw/
DATA_OUTPUT = os.path.join(BASE_DIR, "data", "output")

# Create directories if they don't exist
for d in [DATA_RAW, DATA_PROCESSED, DATA_OUTPUT]:
    os.makedirs(d, exist_ok=True)

# ── Database ───────────────────────────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pharma_analytics")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
from urllib.parse import quote_plus

DB_URI = (
    f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
)

# ── Azure ────────────────────────────────────────────────────────────────────────
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "pharma-analytics-data")

# ── Kaggle ─────────────────────────────────────────────────────────────────────
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "")

# ── Model Parameters ──────────────────────────────────────────────────────────
RANDOM_STATE = 42
TEST_SIZE = 0.2
N_HCP_SEGMENTS = 5
N_TERRITORIES = 20
N_HCPS = 500
N_REPS = 50
FORECAST_MONTHS = 3
