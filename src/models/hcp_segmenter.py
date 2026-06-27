"""
HCP Segmentation Model — K-Means Clustering.

Segments Healthcare Providers into 5 behavioral groups based on
RFM (Recency, Frequency, Monetary) features:
  - Champions: High-value, frequent prescribers
  - Loyal HCPs: Consistent, moderate-high prescribers
  - High Potential: Emerging prescribers with growth signals
  - At Risk: Previously active, now declining
  - Low Value: Infrequent, low-value prescribers

Outputs:
  - Trained K-Means model (.pkl)
  - HCP segment assignments
  - Segment summary with revenue contribution
  - Elbow and silhouette analysis
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DATA_PROCESSED, DATA_OUTPUT, RANDOM_STATE, N_HCP_SEGMENTS
from src.utils.helpers import save_csv, load_csv, save_json, logger

# ── Feature columns for clustering ────────────────────────────────────────────
CLUSTER_FEATURES = [
    "recency", "frequency", "monetary", "avg_rx_value", "unique_drugs", "total_quantity"
]


def prepare_clustering_data(rfm_df: pd.DataFrame):
    """Scale RFM features for K-Means clustering."""
    available = [c for c in CLUSTER_FEATURES if c in rfm_df.columns]
    X = rfm_df[available].fillna(0).copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    logger.info(f"Prepared {len(X)} HCPs with {len(available)} features for clustering")
    return X_scaled, scaler, available


def find_optimal_k(X_scaled, k_range=range(2, 10)) -> pd.DataFrame:
    """
    Evaluate K-Means for a range of K values.
    Uses both Elbow (inertia) and Silhouette methods.
    """
    results = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels)
        results.append({
            "k": k,
            "inertia": km.inertia_,
            "silhouette": round(sil, 4),
        })

    results_df = pd.DataFrame(results)

    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(results_df["k"], results_df["inertia"], "bo-", linewidth=2)
    ax1.set_xlabel("Number of Clusters (K)")
    ax1.set_ylabel("Inertia")
    ax1.set_title("Elbow Method")
    ax1.axvline(x=N_HCP_SEGMENTS, color="red", linestyle="--", alpha=0.7, label=f"K={N_HCP_SEGMENTS}")
    ax1.legend()

    ax2.plot(results_df["k"], results_df["silhouette"], "ro-", linewidth=2)
    ax2.set_xlabel("Number of Clusters (K)")
    ax2.set_ylabel("Silhouette Score")
    ax2.set_title("Silhouette Analysis")
    ax2.axvline(x=N_HCP_SEGMENTS, color="blue", linestyle="--", alpha=0.7, label=f"K={N_HCP_SEGMENTS}")
    ax2.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(DATA_OUTPUT, "hcp_optimal_k_analysis.png"), dpi=150)
    plt.close()
    logger.info("Saved optimal K analysis chart")

    return results_df


def train_kmeans(X_scaled, k: int = N_HCP_SEGMENTS):
    """Train K-Means model with the chosen K."""
    km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    labels = km.fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, labels)
    logger.info(f"K-Means trained with K={k}, Silhouette={sil:.4f}")
    return km, labels, sil


def label_segments(rfm_df: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """
    Assign business-meaningful segment names based on cluster centroids.
    Automatically maps clusters by analyzing centroid characteristics.
    """
    df = rfm_df.copy()
    df["cluster"] = labels

    # Compute cluster centroids (on original scale)
    centroids = df.groupby("cluster")[CLUSTER_FEATURES].mean()

    # Scoring: higher frequency + monetary = better; higher recency = worse
    centroids["score"] = (
        centroids.get("frequency", 0) * 0.3
        + centroids.get("monetary", 0) / centroids.get("monetary", 1).max() * 0.4
        - centroids.get("recency", 0) / centroids.get("recency", 1).max() * 0.3
    )
    centroids = centroids.sort_values("score", ascending=False)

    # Map top-to-bottom scored clusters to segment names
    segment_names = ["Champions", "Loyal HCPs", "High Potential", "At Risk", "Low Value"]
    ordered_clusters = centroids.index.tolist()

    segment_map = {}
    for i, cluster_id in enumerate(ordered_clusters):
        if i < len(segment_names):
            segment_map[cluster_id] = segment_names[i]
        else:
            segment_map[cluster_id] = f"Segment {i+1}"

    df["segment"] = df["cluster"].map(segment_map)

    logger.info(f"Segment distribution:\n{df['segment'].value_counts().to_string()}")
    return df


def generate_segment_summary(segmented_df: pd.DataFrame) -> pd.DataFrame:
    """Generate summary statistics for each segment."""
    summary = segmented_df.groupby("segment").agg(
        hcp_count=("hcp_id", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        avg_rx_value=("avg_rx_value", "mean"),
        total_revenue=("monetary", "sum"),
        avg_unique_drugs=("unique_drugs", "mean"),
    ).reset_index()

    summary["revenue_contribution_pct"] = (
        summary["total_revenue"] / summary["total_revenue"].sum() * 100
    ).round(2)

    summary["hcp_pct"] = (
        summary["hcp_count"] / summary["hcp_count"].sum() * 100
    ).round(2)

    # Round numeric columns
    for col in ["avg_recency", "avg_frequency", "avg_monetary", "avg_rx_value", "avg_unique_drugs"]:
        summary[col] = summary[col].round(2)
    summary["total_revenue"] = summary["total_revenue"].round(2)

    summary = summary.sort_values("total_revenue", ascending=False)
    return summary


def plot_segments(segmented_df: pd.DataFrame) -> None:
    """Visualize segments in RFM space."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Segment distribution (donut chart)
    seg_counts = segmented_df["segment"].value_counts()
    colors = ["#4CAF50", "#2196F3", "#FF9800", "#F44336", "#9E9E9E"]
    axes[0].pie(seg_counts, labels=seg_counts.index, colors=colors[:len(seg_counts)],
                autopct="%1.1f%%", startangle=90, pctdistance=0.85)
    centre = plt.Circle((0, 0), 0.60, fc="white")
    axes[0].add_patch(centre)
    axes[0].set_title("HCP Segment Distribution")

    # Revenue by segment
    seg_rev = segmented_df.groupby("segment")["monetary"].sum().sort_values(ascending=True)
    axes[1].barh(seg_rev.index, seg_rev.values, color=colors[:len(seg_rev)])
    axes[1].set_xlabel("Total Revenue ($)")
    axes[1].set_title("Revenue by Segment")

    # Frequency vs Monetary scatter
    for i, (seg, group) in enumerate(segmented_df.groupby("segment")):
        axes[2].scatter(group["frequency"], group["monetary"],
                       label=seg, alpha=0.5, s=20,
                       color=colors[i % len(colors)])
    axes[2].set_xlabel("Prescription Frequency")
    axes[2].set_ylabel("Total Monetary Value ($)")
    axes[2].set_title("HCP Value Matrix")
    axes[2].legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(DATA_OUTPUT, "hcp_segmentation_charts.png"), dpi=150)
    plt.close()
    logger.info("Saved segmentation charts")


def run_hcp_segmentation() -> dict:
    """
    Full HCP segmentation pipeline.
    """
    logger.info("=" * 60)
    logger.info("Running HCP Segmentation Pipeline")
    logger.info("=" * 60)

    # Load RFM features
    rfm_df = load_csv(os.path.join(DATA_PROCESSED, "hcp_rfm_features.csv"))

    # Prepare data
    X_scaled, scaler, feature_names = prepare_clustering_data(rfm_df)

    # Find optimal K
    k_analysis = find_optimal_k(X_scaled)

    # Train model
    model, labels, silhouette = train_kmeans(X_scaled)

    # Label segments
    segmented_df = label_segments(rfm_df, labels)

    # Summary
    summary = generate_segment_summary(segmented_df)

    # Visualize
    plot_segments(segmented_df)

    # Metrics
    metrics = {
        "n_clusters": N_HCP_SEGMENTS,
        "silhouette_score": round(silhouette, 4),
        "total_hcps": len(segmented_df),
        "segments": summary.set_index("segment")["hcp_count"].to_dict(),
    }

    # Save
    save_csv(segmented_df, os.path.join(DATA_OUTPUT, "hcp_segments.csv"), "HCP segments")
    save_csv(summary, os.path.join(DATA_OUTPUT, "segment_summary.csv"), "segment summary")
    save_json(metrics, os.path.join(DATA_OUTPUT, "segmentation_metrics.json"))
    joblib.dump(model, os.path.join(DATA_OUTPUT, "hcp_segmentation_model.pkl"))
    joblib.dump(scaler, os.path.join(DATA_OUTPUT, "hcp_segmentation_scaler.pkl"))

    logger.info("=" * 60)
    logger.info("HCP Segmentation complete!")
    logger.info("=" * 60)

    return {
        "model": model,
        "segmented_df": segmented_df,
        "summary": summary,
        "metrics": metrics,
    }


if __name__ == "__main__":
    results = run_hcp_segmentation()
    print("\n📊 HCP Segmentation Summary:")
    print(results["summary"].to_string(index=False))
