"""Validation report for regenerated pharma data."""
import sys, os
import pandas as pd
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sales = pd.read_csv('data/raw/pharma_sales.csv')
hcp = pd.read_csv('data/raw/hcp_master.csv')
rx = pd.read_csv('data/raw/prescription_data.csv')
rep = pd.read_csv('data/raw/rep_activity.csv')
terr = pd.read_csv('data/raw/territory_mapping.csv')
promo = pd.read_csv('data/raw/promotion_campaigns.csv')

print("=" * 70)
print("  VALIDATION REPORT - Regenerated Pharma Data")
print("=" * 70)

# 1. Row counts
print("\n[1] ROW COUNTS")
print(f"  territory_mapping.csv:    {len(terr):>8}")
print(f"  hcp_master.csv:           {len(hcp):>8}")
print(f"  pharma_sales.csv:         {len(sales):>8}")
print(f"  prescription_data.csv:    {len(rx):>8}")
print(f"  rep_activity.csv:         {len(rep):>8}")
print(f"  promotion_campaigns.csv:  {len(promo):>8}")

# 2. Referential integrity
print("\n[2] REFERENTIAL INTEGRITY")
# Sales territory_id -> territory_mapping
sales_terr = set(sales['territory_id'].unique())
valid_terr = set(terr['territory_id'].unique())
orphan_sales = sales_terr - valid_terr
print(f"  Sales territory_id FK:    {'PASS' if not orphan_sales else 'FAIL - ' + str(orphan_sales)}")

# HCP territory_id -> territory_mapping
hcp_terr = set(hcp['territory_id'].unique())
orphan_hcp = hcp_terr - valid_terr
print(f"  HCP territory_id FK:      {'PASS' if not orphan_hcp else 'FAIL - ' + str(orphan_hcp)}")

# Rx hcp_id -> hcp_master
rx_hcps = set(rx['hcp_id'].unique())
valid_hcps = set(hcp['hcp_id'].unique())
orphan_rx = rx_hcps - valid_hcps
print(f"  Rx hcp_id FK:             {'PASS' if not orphan_rx else 'FAIL - ' + str(len(orphan_rx)) + ' orphans'}")

# Rx drug_name -> sales drug_name
rx_drugs = set(rx['drug_name'].unique())
sales_drugs = set(sales['drug_name'].unique())
missing_drugs = rx_drugs - sales_drugs
print(f"  Rx drug_name consistency: {'PASS' if not missing_drugs else 'FAIL - ' + str(missing_drugs)}")

# Rep territory_id -> territory_mapping
rep_terr = set(rep['territory_id'].unique())
orphan_rep = rep_terr - valid_terr
print(f"  Rep territory_id FK:      {'PASS' if not orphan_rep else 'FAIL - ' + str(orphan_rep)}")

# Rep hcp_id -> hcp_master
rep_hcps = set(rep['hcp_id'].unique())
orphan_rep_hcp = rep_hcps - valid_hcps
print(f"  Rep hcp_id FK:            {'PASS' if not orphan_rep_hcp else 'FAIL - ' + str(len(orphan_rep_hcp)) + ' orphans'}")

# Promo drug_name -> sales drug_name
promo_drugs = set(promo['drug_name'].unique())
missing_promo = promo_drugs - sales_drugs
print(f"  Promo drug_name FK:       {'PASS' if not missing_promo else 'FAIL - ' + str(missing_promo)}")

# 3. Monthly revenue distribution
print("\n[3] MONTHLY REVENUE DISTRIBUTION")
sales['sale_date'] = pd.to_datetime(sales['sale_date'])
sales['month'] = sales['sale_date'].dt.to_period('M')
monthly = sales.groupby('month')['revenue'].sum()
print(f"  {'Month':<10} {'Revenue':>16} {'MoM Change':>12}")
print(f"  {'-'*38}")
prev = None
for m, r in monthly.items():
    if prev is not None:
        change = ((r - prev) / prev) * 100
        print(f"  {str(m):<10} {r:>16,.0f} {change:>+11.1f}%")
    else:
        print(f"  {str(m):<10} {r:>16,.0f}           --")
    prev = r

# 4. Territory distribution
print("\n[4] TERRITORY REVENUE DISTRIBUTION")
terr_rev = sales.groupby('territory_id')['revenue'].sum().sort_values(ascending=False)
for tid, r in terr_rev.items():
    pct = r / terr_rev.sum() * 100
    print(f"  {tid}: {r:>14,.0f} ({pct:.1f}%)")

# 5. Drug pricing realism
print("\n[5] DRUG PRICING (unit_price ranges)")
drug_prices = sales.groupby('drug_name')['unit_price'].agg(['min', 'mean', 'max']).round(0)
for drug, row in drug_prices.iterrows():
    print(f"  {drug:<12} min={row['min']:>8,.0f}  avg={row['mean']:>8,.0f}  max={row['max']:>8,.0f}")

# 6. HCP segmentation readiness
print("\n[6] HCP TIER DISTRIBUTION")
print(hcp['tier'].value_counts().to_string())

# 7. Rep performance variation
print("\n[7] REP PERFORMANCE VARIATION")
rep_stats = rep.groupby('rep_id').agg(
    activities=('activity_type', 'count'),
    unique_hcps=('hcp_id', 'nunique'),
    positive_rate=('outcome', lambda x: (x == 'Positive').mean()),
).reset_index()
print(f"  Activities - min: {rep_stats['activities'].min()}, median: {rep_stats['activities'].median():.0f}, max: {rep_stats['activities'].max()}")
print(f"  Unique HCPs - min: {rep_stats['unique_hcps'].min()}, median: {rep_stats['unique_hcps'].median():.0f}, max: {rep_stats['unique_hcps'].max()}")
print(f"  Positive rate - min: {rep_stats['positive_rate'].min():.1%}, median: {rep_stats['positive_rate'].median():.1%}, max: {rep_stats['positive_rate'].max():.1%}")

# HCP penetration
total_hcps = len(hcp)
visited_hcps = rep['hcp_id'].nunique()
print(f"\n  HCP Penetration: {visited_hcps}/{total_hcps} = {visited_hcps/total_hcps:.1%}")

# 8. Promotion campaign outcomes
print("\n[8] PROMOTION CAMPAIGN OUTCOMES")
promo['roi'] = (promo['revenue_after'] - promo['revenue_before']) / promo['budget']
promo['rx_lift'] = ((promo['prescriptions_after'] - promo['prescriptions_before']) / promo['prescriptions_before'] * 100).round(1)
for _, c in promo.iterrows():
    status = 'SUCCESS' if c['roi'] > 0.5 else ('NEUTRAL' if c['roi'] > -0.1 else 'FAILED')
    print(f"  {c['campaign_id']}: {c['drug_name']:<12} | ROI={c['roi']:>+.2f} | Rx Lift={c['rx_lift']:>+.1f}% | {status}")

great = (promo['roi'] > 0.5).sum()
moderate = ((promo['roi'] > -0.1) & (promo['roi'] <= 0.5)).sum()
failed = (promo['roi'] <= -0.1).sum()
print(f"\n  Summary: {great} successful, {moderate} neutral, {failed} failed")

print("\n" + "=" * 70)
print("  VALIDATION COMPLETE")
print("=" * 70)
