"""
Synthetic Commercial Data Generator.

Generates interlinked synthetic datasets for the pharma analytics platform:
  - HCP Master (doctors)
  - Territory Mapping
  - Rep Activity (visits, calls, meetings, samples)
  - Prescription Data (HCP prescribing history)
  - Promotion Campaigns

All data is internally consistent: HCP IDs, territory IDs, and drug names
are shared across tables to maintain referential integrity.
"""
import os
import sys
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import (
    DATA_RAW, RANDOM_STATE, N_TERRITORIES, N_HCPS, N_REPS
)
from src.utils.helpers import save_csv, logger

# ── Setup ──────────────────────────────────────────────────────────────────────
fake = Faker()
Faker.seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)
random.seed(RANDOM_STATE)

# ── Shared Constants ───────────────────────────────────────────────────────────
SPECIALTIES = [
    "Cardiology", "Oncology", "Neurology", "Endocrinology",
    "Pulmonology", "Gastroenterology", "Dermatology", "Psychiatry",
    "Rheumatology", "Nephrology",
]

TIERS = ["Tier 1", "Tier 2", "Tier 3"]
TIER_WEIGHTS = [0.1, 0.3, 0.6]

REGIONS = [
    "North",
    "South",
    "East",
    "West",
    "Central"
]

STATES = [
    "Maharashtra",
    "Delhi",
    "Karnataka",
    "Tamil Nadu",
    "Gujarat",
    "Telangana",
    "West Bengal",
    "Rajasthan",
    "Punjab",
    "Kerala",
    "Uttar Pradesh",
    "Haryana",
    "Madhya Pradesh",
    "Bihar",
    "Odisha",
    "Andhra Pradesh",
    "Chhattisgarh",
    "Jharkhand",
    "Assam",
    "Uttarakhand"
]

ACTIVITY_TYPES = ["Visit", "Phone Call", "Virtual Meeting", "Sample Drop", "Conference"]
ACTIVITY_WEIGHTS = [0.35, 0.25, 0.15, 0.15, 0.10]

OUTCOMES = [
    "Positive",
    "Neutral",
    "Follow-up Required",
    "No Show",
    "Declined Meeting"
]

DRUG_NAMES = [
    "Lipitor", "Crestor", "Nexium", "Advair", "Humira",
    "Enbrel", "Remicade", "Avastin", "Herceptin", "Rituxan",
    "Lantus", "Januvia", "Lyrica", "Copaxone", "Neulasta",
    "Gleevec", "Revlimid", "Tecfidera", "Opdivo", "Keytruda",
]

THERAPEUTIC_CLASSES = {
    "Lipitor": "Cardiovascular", "Crestor": "Cardiovascular",
    "Nexium": "Gastroenterology", "Advair": "Respiratory",
    "Humira": "Immunology", "Enbrel": "Immunology",
    "Remicade": "Immunology", "Avastin": "Oncology",
    "Herceptin": "Oncology", "Rituxan": "Oncology",
    "Lantus": "Diabetes", "Januvia": "Diabetes",
    "Lyrica": "Neurology", "Copaxone": "Neurology",
    "Neulasta": "Oncology", "Gleevec": "Oncology",
    "Revlimid": "Oncology", "Tecfidera": "Neurology",
    "Opdivo": "Oncology", "Keytruda": "Oncology",
}

CAMPAIGN_CHANNELS = ["Email", "Webinar", "Conference", "Journal Ad", "Rep Visit", "Digital"]


# ══════════════════════════════════════════════════════════════════════════════
#  Generator Functions
# ══════════════════════════════════════════════════════════════════════════════

def generate_territory_mapping(n_territories: int = N_TERRITORIES) -> pd.DataFrame:
    """Generate territory mapping with region assignments and quotas."""
    records = []
    STATE_REGION_MAP = {
        "Maharashtra": "West",
        "Delhi": "North",
        "Karnataka": "South",
        "Tamil Nadu": "South",
        "Gujarat": "West",
        "Telangana": "South",
        "West Bengal": "East",
        "Rajasthan": "North",
        "Punjab": "North",
        "Kerala": "South",
        "Uttar Pradesh": "North",
        "Haryana": "North",
        "Madhya Pradesh": "Central",
        "Bihar": "East",
        "Odisha": "East",
        "Andhra Pradesh": "South",
        "Chhattisgarh": "Central",
        "Jharkhand": "East",
        "Assam": "East",
        "Uttarakhand": "North"
    }
    for i in range(n_territories):
        region = STATE_REGION_MAP[STATES[i]]
        state_pool = [s for s in STATES if hash(s + region) % 5 == i % 5] or STATES[:3]
        coverage = random.sample(state_pool, min(random.randint(1, 3), len(state_pool)))

        target_hcp_count = random.randint(20, 60)
        assigned_rep_count = random.randint(1, 6)

        records.append({
            "territory_id": f"TER-{i+1:02d}",
            "territory_name": STATES[i],
            "region": region,
            "state_coverage": ", ".join(coverage),
            "assigned_rep_count": assigned_rep_count,
            "target_hcp_count": target_hcp_count,
            "annual_quota": round(target_hcp_count * random.uniform(25000, 45000),2),  # noqa: E501
        })

    df = pd.DataFrame(records)
    logger.info(f"Generated {len(df)} territories across {len(REGIONS)} regions")
    return df


def generate_hcp_master(territory_df: pd.DataFrame,
                        n_hcps: int = N_HCPS) -> pd.DataFrame:
    """Generate HCP (doctor) master data linked to territories."""
    territory_ids = territory_df["territory_id"].tolist()
    records = []

    for i in range(n_hcps):
        territory = random.choice(territory_ids)
        tier = random.choices(TIERS, weights=TIER_WEIGHTS, k=1)[0]

        records.append({
            "hcp_id": f"HCP-{i+1:04d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "specialty": random.choice(SPECIALTIES),
            "tier": tier,
            "years_experience": random.randint(3, 35),
            "hospital_affiliation": fake.company() + " Hospital",
            "city": fake.city(),
            "state": random.choice(STATES),
            "territory_id": territory,
            "npi_number": fake.unique.random_number(digits=10, fix_len=True),
        })

    df = pd.DataFrame(records)
    logger.info(f"Generated {len(df)} HCPs across {df['territory_id'].nunique()} territories")
    return df


def generate_rep_activity(hcp_df: pd.DataFrame,
                          n_reps: int = N_REPS,
                          months: int = 12) -> pd.DataFrame:
    """
    Generate sales rep activity logs (visits, calls, meetings, samples).
    Each rep is assigned to a territory and interacts with HCPs in that territory.
    """
    territory_ids = hcp_df["territory_id"].unique().tolist()
    records = []

    # Pre-build territory→HCP lookup
    territory_hcps = hcp_df.groupby("territory_id")["hcp_id"].apply(list).to_dict()

    # Generate rep assignments
    rep_assignments = {}
    for rep_id in range(1, n_reps + 1):
        territory = territory_ids[(rep_id - 1) % len(territory_ids)]
        rep_assignments[rep_id] = {
            "territory": territory,
            "name": fake.name(),
        }

    for rep_id, info in rep_assignments.items():
        territory = info["territory"]
        hcps = territory_hcps.get(territory, [])

        for month in range(1, months + 1):
            year = 2024 if month <= 12 else 2025
            m = month if month <= 12 else month - 12

            n_activities = int(np.random.lognormal(mean=3.0, sigma=0.6))
            n_activities = max(5, min(n_activities, 80))
            for _ in range(n_activities):
                activity = random.choices(ACTIVITY_TYPES, weights=ACTIVITY_WEIGHTS, k=1)[0]
                day = random.randint(1, 28)

                records.append({
                    "rep_id": f"REP-{rep_id:03d}",
                    "rep_name": info["name"],
                    "territory_id": territory,
                    "hcp_id": random.choice(hcps) if hcps else None,
                    "activity_type": activity,
                    "activity_date": f"{year}-{m:02d}-{day:02d}",
                    "duration_minutes": random.randint(10, 90),
                    "samples_left": random.randint(0, 20) if activity == "Sample Drop" else 0,
                    "outcome": random.choices(OUTCOMES,weights=[0.45, 0.25, 0.15, 0.10, 0.05],k=1)[0],
                })

    df = pd.DataFrame(records)
    df["activity_date"] = pd.to_datetime(df["activity_date"])
    logger.info(f"Generated {len(df)} rep activities for {n_reps} reps over {months} months")
    return df


def generate_prescription_data(hcp_df: pd.DataFrame,
                               months: int = 12) -> pd.DataFrame:
    """
    Generate HCP prescription history. Higher-tier HCPs prescribe more.
    Each HCP prescribes 1-4 drugs consistently over time.
    """
    tier_multiplier = {"Tier 1": 3.0, "Tier 2": 1.5, "Tier 3": 0.7}
    records = []

    for _, hcp in hcp_df.iterrows():
        n_drugs = random.randint(1, 4)
        prescribed_drugs = random.sample(DRUG_NAMES, n_drugs)
        mult = tier_multiplier.get(hcp["tier"], 1.0)

        for month in range(1, months + 1):
            year = 2024 if month <= 12 else 2025
            m = month if month <= 12 else month - 12

            for drug in prescribed_drugs:
                base_qty = np.random.randint(3, 80)
                qty = max(1, int(base_qty * mult * np.random.lognormal(0, 0.3)))
                unit_price = round(random.uniform(15, 450), 2)

                day = random.randint(1, 28)
                records.append({
                    "prescription_id": f"RX-{len(records)+1:06d}",
                    "hcp_id": hcp["hcp_id"],
                    "drug_name": drug,
                    "therapeutic_class": THERAPEUTIC_CLASSES.get(drug, "General"),
                    "prescription_date": f"{year}-{m:02d}-{day:02d}",
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total_value": round(qty * unit_price, 2),
                })

    df = pd.DataFrame(records)
    df["prescription_date"] = pd.to_datetime(df["prescription_date"])
    logger.info(f"Generated {len(df)} prescriptions for {hcp_df['hcp_id'].nunique()} HCPs")
    return df


def generate_promotion_campaigns(n_campaigns: int = 15) -> pd.DataFrame:
    """
    Generate promotional campaign data with budget, reach, and lift metrics.
    """
    records = []

    for i in range(n_campaigns):
        drug = random.choice(DRUG_NAMES)
        channel = random.choice(CAMPAIGN_CHANNELS)
        start = fake.date_between(start_date="-12m", end_date="-2m")
        end = start + timedelta(days=random.randint(14, 90))

        hcps_targeted = random.randint(50, 300)
        hcps_reached = random.randint(int(hcps_targeted * 0.4), hcps_targeted)
        rx_before = random.randint(200, 1000)
        # Campaigns have 5-40% lift on average
        lift_pct = random.uniform(0.05, 0.40)
        rx_after = int(rx_before * (1 + lift_pct))
        budget = round(random.uniform(10_000, 500_000), 2)

        avg_rx_value = random.uniform(50, 300)
        rev_before = round(rx_before * avg_rx_value, 2)
        rev_after = round(rx_after * avg_rx_value, 2)

        records.append({
            "campaign_id": f"CAMP-{i+1:03d}",
            "campaign_name": f"{channel} Campaign - {drug}",
            "drug_name": drug,
            "channel": channel,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "budget": budget,
            "hcps_targeted": hcps_targeted,
            "hcps_reached": hcps_reached,
            "prescriptions_before": rx_before,
            "prescriptions_after": rx_after,
            "revenue_before": rev_before,
            "revenue_after": rev_after,
        })

    df = pd.DataFrame(records)
    logger.info(f"Generated {len(df)} promotion campaigns")
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  Data Validation
# ══════════════════════════════════════════════════════════════════════════════

def validate_data_consistency(territory_df, hcp_df, rep_df, rx_df) -> bool:
    """Verify referential integrity across all synthetic datasets."""
    valid = True

    # Check HCP territory references
    valid_territories = set(territory_df["territory_id"])
    hcp_territories = set(hcp_df["territory_id"])
    orphans = hcp_territories - valid_territories
    if orphans:
        logger.error(f"HCPs reference invalid territories: {orphans}")
        valid = False

    # Check rep territory references
    rep_territories = set(rep_df["territory_id"])
    orphans = rep_territories - valid_territories
    if orphans:
        logger.error(f"Reps reference invalid territories: {orphans}")
        valid = False

    # Check prescription HCP references
    valid_hcps = set(hcp_df["hcp_id"])
    rx_hcps = set(rx_df["hcp_id"])
    orphans = rx_hcps - valid_hcps
    if orphans:
        logger.error(f"Prescriptions reference invalid HCPs: {len(orphans)} orphans")
        valid = False

    # Check rep HCP references
    rep_hcps = set(rep_df["hcp_id"].dropna())
    orphans = rep_hcps - valid_hcps
    if orphans:
        logger.error(f"Rep activities reference invalid HCPs: {len(orphans)} orphans")
        valid = False

    if valid:
        logger.info("✅ All referential integrity checks passed!")
    return valid


# ══════════════════════════════════════════════════════════════════════════════
#  Main Entry Point
# ══════════════════════════════════════════════════════════════════════════════

def generate_all_synthetic_data() -> dict:
    """
    Generate all synthetic datasets and save them to data/raw/.
    Returns a dictionary of DataFrames.
    """
    logger.info("=" * 60)
    logger.info("Starting synthetic data generation")
    logger.info("=" * 60)

    # Generate in dependency order
    territory_df = generate_territory_mapping()
    hcp_df = generate_hcp_master(territory_df)
    rep_df = generate_rep_activity(hcp_df)
    rx_df = generate_prescription_data(hcp_df)
    promo_df = generate_promotion_campaigns()

    # Validate
    validate_data_consistency(territory_df, hcp_df, rep_df, rx_df)

    # Save all
    save_csv(territory_df, os.path.join(DATA_RAW, "territory_mapping.csv"), "territory mapping")
    save_csv(hcp_df, os.path.join(DATA_RAW, "hcp_master.csv"), "HCP master")
    save_csv(rep_df, os.path.join(DATA_RAW, "rep_activity.csv"), "rep activity")
    save_csv(rx_df, os.path.join(DATA_RAW, "prescription_data.csv"), "prescription data")
    save_csv(promo_df, os.path.join(DATA_RAW, "promotion_campaigns.csv"), "promotion campaigns")

    logger.info("=" * 60)
    logger.info("Synthetic data generation complete!")
    logger.info("=" * 60)

    return {
        "territory": territory_df,
        "hcp": hcp_df,
        "rep_activity": rep_df,
        "prescriptions": rx_df,
        "promotions": promo_df,
    }


if __name__ == "__main__":
    data = generate_all_synthetic_data()

    print("\n📊 Synthetic Data Summary:")
    for name, df in data.items():
        print(f"  {name:20s} → {len(df):>8,} rows, {len(df.columns):>3} columns")
