"""
openFDA Drug Reference Data Loader.

Fetches drug metadata (brand names, generic names, therapeutic classes,
manufacturers, routes) from the openFDA API and creates a drug reference table.
Falls back to a curated synthetic drug reference if the API is unreachable.
"""
import os
import sys
import time
import requests
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DATA_RAW
from src.utils.helpers import save_csv, logger

# ── Constants ──────────────────────────────────────────────────────────────────
OPENFDA_URL = "https://api.fda.gov/drug/drugsfda.json"
OUTPUT_FILE = os.path.join(DATA_RAW, "drug_reference.csv")
MAX_RECORDS = 500  # openFDA limit per request is 99; we paginate


def fetch_from_openfda(total: int = MAX_RECORDS, per_page: int = 99) -> pd.DataFrame:
    """
    Fetch drug metadata from the openFDA drugsfda endpoint.
    Paginates through results and extracts key fields.
    """
    records = []
    skip = 0

    while skip < total:
        limit = min(per_page, total - skip)
        params = {"limit": limit, "skip": skip}

        try:
            resp = requests.get(OPENFDA_URL, params=params, timeout=30)
            resp.raise_for_status()
            results = resp.json().get("results", [])
        except Exception as e:
            logger.warning(f"openFDA API error at skip={skip}: {e}")
            break

        if not results:
            break

        for r in results:
            openfda = r.get("openfda", {})
            for product in r.get("products", [{}]):
                brand = product.get("brand_name", "")
                generic = openfda.get("generic_name", [None])
                manufacturer = openfda.get("manufacturer_name", [None])
                pharm_class = openfda.get("pharm_class_epc", [None])
                route = product.get("route", "")

                records.append({
                    "brand_name": brand if brand else None,
                    "generic_name": generic[0] if generic else None,
                    "manufacturer": manufacturer[0] if manufacturer else None,
                    "product_type": product.get("dosage_form", None),
                    "route": route if isinstance(route, str) else (route[0] if route else None),
                    "pharm_class": pharm_class[0] if pharm_class else None,
                })

        skip += limit
        time.sleep(0.3)  # respect rate limits

    df = pd.DataFrame(records)
    if df.empty:
        logger.info("Fetched 0 drug records from openFDA")
        return df

    # Deduplicate by brand_name
    df = df.drop_duplicates(subset=["brand_name"]).dropna(subset=["brand_name"])
    logger.info(f"Fetched {len(df)} drug records from openFDA")
    return df


def generate_synthetic_drug_reference() -> pd.DataFrame:
    """
    Create a curated drug reference table when the API is unavailable.
    Uses real drug names and realistic therapeutic classes.
    """
    drugs = [
        {"brand_name": "Lipitor", "generic_name": "Atorvastatin", "manufacturer": "Pfizer",
         "product_type": "Tablet", "route": "Oral", "pharm_class": "HMG-CoA Reductase Inhibitor"},
        {"brand_name": "Crestor", "generic_name": "Rosuvastatin", "manufacturer": "AstraZeneca",
         "product_type": "Tablet", "route": "Oral", "pharm_class": "HMG-CoA Reductase Inhibitor"},
        {"brand_name": "Nexium", "generic_name": "Esomeprazole", "manufacturer": "AstraZeneca",
         "product_type": "Capsule", "route": "Oral", "pharm_class": "Proton Pump Inhibitor"},
        {"brand_name": "Advair", "generic_name": "Fluticasone/Salmeterol", "manufacturer": "GSK",
         "product_type": "Inhaler", "route": "Inhalation", "pharm_class": "Corticosteroid/Beta-Agonist"},
        {"brand_name": "Humira", "generic_name": "Adalimumab", "manufacturer": "AbbVie",
         "product_type": "Injection", "route": "Subcutaneous", "pharm_class": "TNF Blocker"},
        {"brand_name": "Enbrel", "generic_name": "Etanercept", "manufacturer": "Amgen",
         "product_type": "Injection", "route": "Subcutaneous", "pharm_class": "TNF Blocker"},
        {"brand_name": "Remicade", "generic_name": "Infliximab", "manufacturer": "Janssen",
         "product_type": "Injection", "route": "Intravenous", "pharm_class": "TNF Blocker"},
        {"brand_name": "Avastin", "generic_name": "Bevacizumab", "manufacturer": "Genentech",
         "product_type": "Injection", "route": "Intravenous", "pharm_class": "VEGF Inhibitor"},
        {"brand_name": "Herceptin", "generic_name": "Trastuzumab", "manufacturer": "Genentech",
         "product_type": "Injection", "route": "Intravenous", "pharm_class": "HER2 Inhibitor"},
        {"brand_name": "Rituxan", "generic_name": "Rituximab", "manufacturer": "Genentech",
         "product_type": "Injection", "route": "Intravenous", "pharm_class": "CD20 Antibody"},
        {"brand_name": "Lantus", "generic_name": "Insulin Glargine", "manufacturer": "Sanofi",
         "product_type": "Injection", "route": "Subcutaneous", "pharm_class": "Insulin"},
        {"brand_name": "Januvia", "generic_name": "Sitagliptin", "manufacturer": "Merck",
         "product_type": "Tablet", "route": "Oral", "pharm_class": "DPP-4 Inhibitor"},
        {"brand_name": "Lyrica", "generic_name": "Pregabalin", "manufacturer": "Pfizer",
         "product_type": "Capsule", "route": "Oral", "pharm_class": "Anticonvulsant"},
        {"brand_name": "Copaxone", "generic_name": "Glatiramer Acetate", "manufacturer": "Teva",
         "product_type": "Injection", "route": "Subcutaneous", "pharm_class": "Immunomodulator"},
        {"brand_name": "Neulasta", "generic_name": "Pegfilgrastim", "manufacturer": "Amgen",
         "product_type": "Injection", "route": "Subcutaneous", "pharm_class": "Colony Stimulating Factor"},
        {"brand_name": "Gleevec", "generic_name": "Imatinib", "manufacturer": "Novartis",
         "product_type": "Tablet", "route": "Oral", "pharm_class": "Kinase Inhibitor"},
        {"brand_name": "Revlimid", "generic_name": "Lenalidomide", "manufacturer": "Celgene",
         "product_type": "Capsule", "route": "Oral", "pharm_class": "Immunomodulator"},
        {"brand_name": "Tecfidera", "generic_name": "Dimethyl Fumarate", "manufacturer": "Biogen",
         "product_type": "Capsule", "route": "Oral", "pharm_class": "Immunomodulator"},
        {"brand_name": "Opdivo", "generic_name": "Nivolumab", "manufacturer": "BMS",
         "product_type": "Injection", "route": "Intravenous", "pharm_class": "PD-1 Inhibitor"},
        {"brand_name": "Keytruda", "generic_name": "Pembrolizumab", "manufacturer": "Merck",
         "product_type": "Injection", "route": "Intravenous", "pharm_class": "PD-1 Inhibitor"},
    ]
    df = pd.DataFrame(drugs)
    logger.info(f"Generated synthetic drug reference: {len(df)} drugs")
    return df


def load_drug_reference() -> pd.DataFrame:
    """
    Main entry point: load drug reference from openFDA or generate synthetic.
    """
    df = fetch_from_openfda()

    if df is None or len(df) < 5:
        logger.info("Using synthetic drug reference as fallback")
        df = generate_synthetic_drug_reference()

    save_csv(df, OUTPUT_FILE, "drug reference data")
    return df


if __name__ == "__main__":
    df = load_drug_reference()
    print(f"\nDrug Reference Summary:")
    print(f"  Total drugs: {len(df)}")
    print(f"  Therapeutic classes: {df['pharm_class'].nunique()}")
    print(f"  Manufacturers: {df['manufacturer'].nunique()}")
    print(df.head(10).to_string(index=False))
