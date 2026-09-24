"""
Single entry point for the MedForcast research layer experiment.

Runs the full Steps 6-14 pipeline: leakage audit, expanding-window temporal
CV, model comparison (XGBoost vs Naive vs MA3 vs SeasonalNaive), stability
analysis, residual analysis, statistical analysis, uncertainty estimation,
database persistence (with graceful offline fallback to CSV), and report
generation.

Usage:
    python run_forecasting_experiment.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forecasting.experiment import run_experiment


def main():
    results = run_experiment()

    print("\n" + "=" * 70)
    print("  MEDFORCAST RESEARCH LAYER — RUN COMPLETE")
    print("=" * 70)

    stability_df = results["stability_df"]
    if not stability_df.empty:
        print("\nModel comparison (mean over folds/series):")
        print(stability_df[["model", "MAPE_mean", "MAE_mean", "RMSE_mean", "R2_mean"]]
              .to_string(index=False))

    uncertainty_metrics = results["uncertainty_metrics"]
    if uncertainty_metrics:
        print(f"\nUncertainty: coverage={uncertainty_metrics.get('overall_coverage_pct')}% "
              f"(target 90%), avg width={uncertainty_metrics.get('average_width')}")

    print(f"\nDatabase status: {results['db_status']}")
    print(f"Report written to: {results['report_path']}")

    return results


if __name__ == "__main__":
    main()
