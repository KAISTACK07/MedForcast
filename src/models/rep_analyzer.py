"""
Sales Rep Effectiveness Analyzer.

Evaluates sales representative productivity through:
  - Composite productivity scoring (weighted metrics)
  - Performance tier classification (quantile-based)
  - Prescription lift analysis
  - Top vs Bottom performer comparison

Outputs:
  - Rep scorecard with productivity scores
  - Performance tier assignments
  - Top vs Bottom comparison table
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DATA_PROCESSED, DATA_OUTPUT
from src.utils.helpers import save_csv, load_csv, save_json, logger

# ── Scoring weights ───────────────────────────────────────────────────────────
SCORE_WEIGHTS = {
    "total_activities_score": 0.15,
    "unique_hcps_covered_score": 0.20,
    "positive_outcome_rate_score": 0.20,
    "est_rx_lift_per_visit_score": 0.25,
    "territory_rx_revenue_score": 0.20,
}

# Metrics to normalize into 0-100 scores
SCORE_METRICS = [
    "total_activities",
    "unique_hcps_covered",
    "positive_outcome_rate",
    "est_rx_lift_per_visit",
    "territory_rx_revenue",
]


def normalize_metrics(rep_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize each metric to a 0-100 scale."""
    df = rep_df.copy()

    for col in SCORE_METRICS:
        if col not in df.columns:
            df[f"{col}_score"] = 50  # neutral score if metric missing
            continue

        col_min = df[col].min()
        col_max = df[col].max()
        if col_max == col_min:
            df[f"{col}_score"] = 50
        else:
            df[f"{col}_score"] = (
                (df[col] - col_min) / (col_max - col_min) * 100
            ).round(2)

    return df


def compute_productivity_score(rep_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute weighted composite productivity score for each rep.
    """
    df = normalize_metrics(rep_df)

    # Weighted score
    df["productivity_score"] = sum(
        df.get(col, 50) * weight for col, weight in SCORE_WEIGHTS.items()
    ).round(2)

    logger.info(f"Productivity scores: min={df['productivity_score'].min():.1f}, "
                f"max={df['productivity_score'].max():.1f}, "
                f"mean={df['productivity_score'].mean():.1f}")
    return df


def classify_performance(rep_df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify reps into performance tiers using quantiles.
    """
    df = rep_df.copy()

    df["performance_tier"] = pd.qcut(
        df["productivity_score"],
        q=4,
        labels=["Underperformer", "Average", "Above Average", "Top Performer"],
        duplicates="drop",
    )

    tier_counts = df["performance_tier"].value_counts()
    logger.info(f"Performance tiers:\n{tier_counts.to_string()}")
    return df


def top_vs_bottom_analysis(rep_df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Compare top N vs bottom N performers across key metrics.
    """
    top = rep_df.nlargest(n, "productivity_score")
    bottom = rep_df.nsmallest(n, "productivity_score")

    metrics_to_compare = [
        ("Avg Activities", "total_activities"),
        ("Avg HCPs Covered", "unique_hcps_covered"),
        ("Avg Visits", "total_visits"),
        ("Positive Outcome Rate", "positive_outcome_rate"),
        ("Avg Duration (min)", "avg_duration"),
        ("Productivity Score", "productivity_score"),
    ]

    rows = []
    for label, col in metrics_to_compare:
        if col in rep_df.columns:
            rows.append({
                "Metric": label,
                "Top Performers (avg)": round(top[col].mean(), 2),
                "Bottom Performers (avg)": round(bottom[col].mean(), 2),
                "Difference": round(top[col].mean() - bottom[col].mean(), 2),
            })

    comparison = pd.DataFrame(rows)
    return comparison


def plot_rep_performance(rep_df: pd.DataFrame) -> None:
    """Generate rep performance visualizations."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Productivity score distribution
    axes[0].hist(rep_df["productivity_score"], bins=20, color="#2196F3",
                 edgecolor="white", alpha=0.8)
    axes[0].set_xlabel("Productivity Score")
    axes[0].set_ylabel("Number of Reps")
    axes[0].set_title("Rep Productivity Distribution")

    # Performance tiers (pie)
    if "performance_tier" in rep_df.columns:
        tier_counts = rep_df["performance_tier"].value_counts()
        colors = ["#F44336", "#FF9800", "#4CAF50", "#1976D2"]
        axes[1].pie(tier_counts, labels=tier_counts.index, colors=colors[:len(tier_counts)],
                    autopct="%1.1f%%", startangle=90)
        axes[1].set_title("Performance Tier Distribution")

    # Top 10 reps bar chart
    top10 = rep_df.nlargest(10, "productivity_score")
    axes[2].barh(
        range(len(top10)),
        top10["productivity_score"],
        color="#4CAF50", edgecolor="white",
    )
    axes[2].set_yticks(range(len(top10)))
    axes[2].set_yticklabels(top10["rep_id"])
    axes[2].set_xlabel("Productivity Score")
    axes[2].set_title("Top 10 Reps by Productivity")
    axes[2].invert_yaxis()

    plt.tight_layout()
    plt.savefig(os.path.join(DATA_OUTPUT, "rep_performance_charts.png"), dpi=150)
    plt.close()
    logger.info("Saved rep performance charts")


def run_rep_analysis() -> dict:
    """
    Full rep effectiveness analysis pipeline.
    """
    logger.info("=" * 60)
    logger.info("Running Rep Effectiveness Analysis")
    logger.info("=" * 60)

    # Load rep features
    rep_df = load_csv(os.path.join(DATA_PROCESSED, "rep_features.csv"))

    # Compute productivity scores
    scored_df = compute_productivity_score(rep_df)

    # Classify into tiers
    scored_df = classify_performance(scored_df)

    # Top vs Bottom comparison
    comparison = top_vs_bottom_analysis(scored_df)

    # Visualize
    plot_rep_performance(scored_df)

    # Summary metrics
    metrics = {
        "total_reps": len(scored_df),
        "avg_productivity_score": round(scored_df["productivity_score"].mean(), 2),
        "top_performer_count": int((scored_df["performance_tier"] == "Top Performer").sum()),
        "underperformer_count": int((scored_df["performance_tier"] == "Underperformer").sum()),
        "avg_hcp_coverage": round(scored_df["unique_hcps_covered"].mean(), 1),
    }

    # Save
    save_csv(scored_df, os.path.join(DATA_OUTPUT, "rep_scorecard.csv"), "rep scorecard")
    save_csv(comparison, os.path.join(DATA_OUTPUT, "rep_top_vs_bottom.csv"), "top vs bottom")
    save_json(metrics, os.path.join(DATA_OUTPUT, "rep_metrics.json"))

    logger.info("=" * 60)
    logger.info("Rep Effectiveness Analysis complete!")
    logger.info("=" * 60)

    return {
        "scorecard": scored_df,
        "comparison": comparison,
        "metrics": metrics,
    }


if __name__ == "__main__":
    results = run_rep_analysis()
    print("\n📊 Rep Effectiveness Summary:")
    for k, v in results["metrics"].items():
        print(f"  {k:30s} → {v}")
    print("\n📊 Top vs Bottom Comparison:")
    print(results["comparison"].to_string(index=False))
