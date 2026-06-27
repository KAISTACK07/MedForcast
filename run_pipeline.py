"""
Full ML Pipeline Runner for Power BI Dashboard Data.

Runs the complete pipeline:
  1. Data Cleaning (raw -> processed)
  2. Feature Engineering (processed -> features)
  3. HCP Segmentation (K-Means -> hcp_segments.csv)
  4. Demand Forecasting (XGBoost -> demand_forecasts.csv, territory_forecasts.csv)
"""
import os
import sys

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.processing.cleaner import clean_all
from src.processing.feature_engineer import engineer_all_features
from src.models.hcp_segmenter import run_hcp_segmentation
from src.models.demand_forecaster import run_demand_forecasting


def main():
    print("=" * 70)
    print("  PHARMA ANALYTICS -- FULL ML PIPELINE")
    print("=" * 70)

    # Step 1: Clean raw data -> data/processed/
    print("\n[STEP 1/4] Cleaning raw data...")
    cleaned = clean_all()
    print(f"   Done. Cleaned {len(cleaned)} datasets")
    for name, df in cleaned.items():
        print(f"      {name:20s} -> {len(df):>8,} rows")

    # Step 2: Feature engineering -> data/processed/ (features)
    print("\n[STEP 2/4] Engineering features...")
    features = engineer_all_features()
    print(f"   Done. Created features for {len(features)} models")
    for name, df in features.items():
        print(f"      {name:20s} -> {len(df):>8,} rows, {len(df.columns):>3} columns")

    # Step 3: HCP Segmentation -> data/output/hcp_segments.csv
    print("\n[STEP 3/4] Running HCP K-Means segmentation...")
    hcp_results = run_hcp_segmentation()
    print(f"   Done. Segmented {hcp_results['metrics']['total_hcps']} HCPs into {hcp_results['metrics']['n_clusters']} segments")
    print(f"      Silhouette Score: {hcp_results['metrics']['silhouette_score']}")
    print(f"\n   Segment Summary:")
    print(hcp_results['summary'].to_string(index=False))

    # Step 4: Demand Forecasting -> data/output/demand_forecasts.csv
    print("\n[STEP 4/4] Running XGBoost demand forecasting...")
    demand_results = run_demand_forecasting()
    print(f"   Done. Demand forecasting complete")
    print(f"      MAE:               {demand_results['metrics']['mae']}")
    print(f"      MAPE:              {demand_results['metrics']['mape_pct']}%")
    print(f"      R2:                {demand_results['metrics']['r2']}")
    print(f"      Forecast Accuracy: {demand_results['metrics']['forecast_accuracy_pct']}%")

    # Summary
    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE -- Output Files for Power BI")
    print("=" * 70)

    output_dir = os.path.join(PROJECT_ROOT, "data", "output")
    for f in sorted(os.listdir(output_dir)):
        fpath = os.path.join(output_dir, f)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"   {f:45s}  ({size_kb:.1f} KB)")

    print("\nAll output files generated. Import them into Power BI!")
    print("   Page 3 (HCP Intelligence): data/output/hcp_segments.csv")
    print("   Page 5 (Promotion ROI):    data/raw/promotion_campaigns.csv (already exists)")
    print("   Page 6 (Forecasting):      data/output/demand_forecasts.csv + territory_forecasts.csv")


if __name__ == "__main__":
    main()
