"""
Demand Forecasting Model — XGBoost Regressor.

Predicts future drug demand at the territory level using:
  - Temporal features (month, quarter, day_of_week)
  - Lag features (1, 3, 6 month lags)
  - Rolling statistics (3-month mean and std)

Outputs:
  - Trained model (.pkl)
  - Territory-level forecasts
  - Feature importance analysis
  - Evaluation metrics (MAE, MAPE, R²)
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from xgboost import XGBRegressor
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.settings import DATA_PROCESSED, DATA_OUTPUT, RANDOM_STATE, TEST_SIZE
from src.utils.helpers import save_csv, load_csv, save_json, logger

# ── Feature columns ───────────────────────────────────────────────────────────
FEATURE_COLS = [
    "month", "quarter", "year", "day_of_week", "is_quarter_end",
    "lag_1", "lag_3", "lag_6",
    "rolling_mean_3", "rolling_std_3",
    "drug_encoded", "territory_encoded",
    "avg_unit_price", "n_transactions",
]

TARGET_COL = "units_sold"


def prepare_data(df: pd.DataFrame):
    """Split data into train/test sets (time-aware: no shuffle)."""
    available_features = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available_features].copy()
    y = df[TARGET_COL].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, shuffle=False, random_state=RANDOM_STATE
    )

    logger.info(f"Train: {len(X_train)} rows, Test: {len(X_test)} rows")
    return X_train, X_test, y_train, y_test, available_features


def train_model(X_train, y_train) -> XGBRegressor:
    """Train XGBoost Regressor for demand forecasting."""
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, verbose=False)
    logger.info("XGBoost demand model trained")
    return model


def evaluate_model(model, X_test, y_test) -> dict:
    """Evaluate model performance."""
    predictions = model.predict(X_test)
    predictions = np.clip(predictions, 0, None)  # demand can't be negative

    mae = mean_absolute_error(y_test, predictions)
    mape = mean_absolute_percentage_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    metrics = {
        "mae": round(mae, 2),
        "mape": round(mape, 4),
        "mape_pct": round(mape * 100, 2),
        "r2": round(r2, 4),
        "forecast_accuracy_pct": round((1 - mape) * 100, 2),
    }

    logger.info(f"Demand Model — MAE: {mae:.2f}, MAPE: {mape:.2%}, R²: {r2:.4f}")
    return predictions, metrics


def plot_feature_importance(model, feature_names: list) -> None:
    """Generate and save feature importance chart."""
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(range(len(sorted_idx)), importances[sorted_idx], color="#2196F3")
    ax.set_yticks(range(len(sorted_idx)))
    ax.set_yticklabels([feature_names[i] for i in sorted_idx])
    ax.set_xlabel("Feature Importance (Gain)")
    ax.set_title("Demand Forecasting — Feature Importance")
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_OUTPUT, "demand_feature_importance.png"), dpi=150)
    plt.close()
    logger.info("Saved feature importance chart")

def export_feature_importance(model, feature_names: list) -> pd.DataFrame:
    """Extract and save feature importance to CSV."""
    importances = model.feature_importances_
    
    # Optional: convert to percentages
    importances = (importances * 100).round(2)
    
    df = pd.DataFrame({
        "feature_name": feature_names,
        "importance": importances
    })
    
    # Sort descending
    df = df.sort_values("importance", ascending=False).reset_index(drop=True)
    
    # Save
    out_path = os.path.join(DATA_OUTPUT, "feature_importance.csv")
    save_csv(df, out_path, "feature importance")
    logger.info("Saved feature importance CSV")
    
    return df



def plot_actual_vs_forecast(y_test, predictions) -> None:
    """Generate actual vs forecast comparison chart."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(range(len(y_test)), y_test.values, label="Actual", color="#1976D2", alpha=0.8)
    ax.plot(range(len(predictions)), predictions, label="Forecast", color="#FF5722",
            alpha=0.8, linestyle="--")
    ax.set_xlabel("Observation")
    ax.set_ylabel("Units Sold")
    ax.set_title("Demand Forecast — Actual vs Predicted")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_OUTPUT, "demand_actual_vs_forecast.png"), dpi=150)
    plt.close()
    logger.info("Saved actual vs forecast chart")


def generate_territory_forecasts(model, df: pd.DataFrame,
                                 feature_cols: list) -> pd.DataFrame:
    """
    Generate aggregated territory-level forecasts.
    Uses the last available data point per territory-drug to forecast.
    """
    latest = df.sort_values("year_month").groupby(
        ["drug_name", "territory_id"]
    ).tail(1).copy()

    X = latest[feature_cols]
    latest["forecasted_units"] = np.clip(model.predict(X), 0, None).astype(int)
    latest["forecasted_revenue"] = (
        latest["forecasted_units"] * latest["avg_unit_price"]
    ).round(2)

    # Aggregate to territory level
    territory_forecast = latest.groupby("territory_id").agg(
        total_forecasted_units=("forecasted_units", "sum"),
        total_forecasted_revenue=("forecasted_revenue", "sum"),
        n_drugs=("drug_name", "nunique"),
    ).reset_index()

    territory_forecast["rank"] = (
        territory_forecast["total_forecasted_revenue"]
        .rank(ascending=False, method="dense")
        .astype(int)
    )

    return territory_forecast


def run_demand_forecasting() -> dict:
    """
    Full demand forecasting pipeline.
    """
    logger.info("=" * 60)
    logger.info("Running Demand Forecasting Pipeline")
    logger.info("=" * 60)

    # Load features
    df = load_csv(os.path.join(DATA_PROCESSED, "demand_features.csv"))

    # Prepare data
    X_train, X_test, y_train, y_test, feature_names = prepare_data(df)

    # Train
    model = train_model(X_train, y_train)

    # Evaluate
    predictions, metrics = evaluate_model(model, X_test, y_test)

    # Visualize and Export Feature Importance
    plot_feature_importance(model, feature_names)
    export_feature_importance(model, feature_names)
    plot_actual_vs_forecast(y_test, predictions)

    # Territory-level forecasts
    territory_forecast = generate_territory_forecasts(model, df, feature_names)

    # Build full forecast output
    forecast_df = pd.DataFrame({
        "actual": y_test.values,
        "predicted": predictions.astype(int),
        "residual": (y_test.values - predictions).round(2),
    })

    # Save outputs
    save_csv(forecast_df, os.path.join(DATA_OUTPUT, "demand_forecasts.csv"), "demand forecasts")
    save_csv(territory_forecast, os.path.join(DATA_OUTPUT, "territory_forecasts.csv"),
             "territory forecasts")
    save_json(metrics, os.path.join(DATA_OUTPUT, "demand_model_metrics.json"))
    joblib.dump(model, os.path.join(DATA_OUTPUT, "demand_model.pkl"))
    logger.info("Saved demand model and forecasts")

    return {
        "model": model,
        "metrics": metrics,
        "forecasts": forecast_df,
        "territory_forecasts": territory_forecast,
    }


if __name__ == "__main__":
    results = run_demand_forecasting()
    print("\n📊 Demand Forecasting Results:")
    for k, v in results["metrics"].items():
        print(f"  {k:25s} → {v}")
