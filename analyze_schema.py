import sys, os
import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load all files
sales = pd.read_csv('data/raw/pharma_sales.csv')
hcp = pd.read_csv('data/raw/hcp_master.csv')
rx = pd.read_csv('data/raw/prescription_data.csv')
rep = pd.read_csv('data/raw/rep_activity.csv')
terr = pd.read_csv('data/raw/territory_mapping.csv')
promo = pd.read_csv('data/raw/promotion_campaigns.csv')

print("=== DRUG NAMES (20 unique) ===")
print(sorted(sales['drug_name'].unique()))

print("\n=== TERRITORY IDS & NAMES ===")
for _, r in terr.iterrows():
    print(f"  {r['territory_id']}: {r['territory_name']} | Region: {r['region']} | State: {r['state_coverage']}")

print("\n=== REGIONS ===")
print(sorted(terr['region'].unique()))

print("\n=== HCP SPECIALTIES ===")
print(sorted(hcp['specialty'].unique()))

print("\n=== HCP TIERS ===")
print(hcp['tier'].value_counts().to_string())

print("\n=== HCP STATES ===")
print(sorted(hcp['state'].unique()))

print("\n=== REP IDS (sample) ===")
rep_info = rep.groupby('rep_id').agg(
    name=('rep_name', 'first'),
    territory=('territory_id', 'first')
).reset_index()
print(rep_info.head(10).to_string(index=False))
print(f"Total reps: {len(rep_info)}")

print("\n=== ACTIVITY TYPES ===")
print(rep['activity_type'].value_counts().to_string())

print("\n=== OUTCOMES ===")
print(rep['outcome'].value_counts().to_string())

print("\n=== THERAPEUTIC CLASSES ===")
print(sorted(rx['therapeutic_class'].unique()))

print("\n=== PROMOTION CHANNELS ===")
print(sorted(promo['channel'].unique()))

print("\n=== DATE RANGES ===")
sales['sale_date'] = pd.to_datetime(sales['sale_date'])
rx['prescription_date'] = pd.to_datetime(rx['prescription_date'])
rep['activity_date'] = pd.to_datetime(rep['activity_date'])
print(f"  Sales: {sales['sale_date'].min()} to {sales['sale_date'].max()}")
print(f"  Prescriptions: {rx['prescription_date'].min()} to {rx['prescription_date'].max()}")
print(f"  Rep Activity: {rep['activity_date'].min()} to {rep['activity_date'].max()}")

print("\n=== MONTHLY REVENUE TREND ===")
sales['month'] = sales['sale_date'].dt.to_period('M')
monthly_rev = sales.groupby('month')['revenue'].sum()
for m, r in monthly_rev.items():
    print(f"  {m}: {r:>14,.2f}")

print("\n=== FK: HCPs per territory ===")
print(hcp['territory_id'].value_counts().sort_index().to_string())

print("\n=== FK: Reps per territory ===")
print(rep_info['territory'].value_counts().sort_index().to_string())
