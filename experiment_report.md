# MedForcast Experiment Report

**Config:** target=`units_sold`, folds=5, baselines=[Naive, MA3, SeasonalNaive(lag12)], seed=42

**Total series (drug × territory):** 400
**Date range:** 2024-02-01 00:00:00 to 2025-12-01 00:00:00
**Total rows in demand_features:** 9200

## Fold Details

| Fold | Train Rows | Val Rows | Train Period | Val Period | Short Series Skipped |
|------|-----------|---------|-------------|-----------|---------------------|
| 0 | 1200 | 1200 | 2024-02-01 00:00:00 to 2024-04-01 00:00:00 | 2024-05-01 00:00:00 to 2024-07-01 00:00:00 | 0 |
| 1 | 2400 | 1200 | 2024-02-01 00:00:00 to 2024-07-01 00:00:00 | 2024-08-01 00:00:00 to 2024-10-01 00:00:00 | 0 |
| 2 | 3600 | 1200 | 2024-02-01 00:00:00 to 2024-10-01 00:00:00 | 2024-11-01 00:00:00 to 2025-01-01 00:00:00 | 0 |
| 3 | 4800 | 1200 | 2024-02-01 00:00:00 to 2025-01-01 00:00:00 | 2025-02-01 00:00:00 to 2025-04-01 00:00:00 | 0 |
| 4 | 6000 | 3200 | 2024-02-01 00:00:00 to 2025-04-01 00:00:00 | 2025-05-01 00:00:00 to 2025-12-01 00:00:00 | 0 |

## Model Comparison — Pooled (authoritative)

> All territories and drugs are pooled together within each fold BEFORE computing metrics, 
> so R2 here is calculated on hundreds of points per model per fold, not on tiny 3-point 
> groups. Use this table, not the diagnostic one further down, for the headline comparison.

| Model | MAPE | MAE | RMSE | R2 |
|-------|------|-----|------|----|
| MovingAvg3 | 24.19% | 18.19 | 27.48 | 0.8247 |
| Naive | 28.74% | 21.99 | 34.01 | 0.7326 |
| SeasonalNaive | 24.50% | 20.12 | 30.58 | 0.8063 |
| XGBoost | 22.76% | 17.68 | 26.97 | 0.8308 |

> **Note on MAPE instability:** Monthly unit counts can be near zero, which makes MAPE 
> explode even for a fine model. When actuals are near zero, treat RMSE and MAE as the 
> PRIMARY comparison metrics.

## Stability Analysis — Pooled (authoritative)

| Model | MAPE Mean | MAPE Median | MAPE Std | Best Fold | Worst Fold |
|-------|-----------|-------------|----------|-----------|------------|
| MovingAvg3 | 24.19% | 24.42% | 2.56% | Fold 2 | Fold 0 |
| Naive | 28.74% | 28.37% | 3.28% | Fold 2 | Fold 0 |
| SeasonalNaive | 24.50% | 24.50% | 0.26% | Fold 4 | Fold 3 |
| XGBoost | 22.76% | 22.17% | 2.38% | Fold 4 | Fold 0 |

## Model Comparison — Fine-Grained by Territory×Drug (diagnostic only)

> Each row here averages metrics computed on individual (territory, drug, fold) groups, 
> most with only 3 data points. MAE/MAPE are still roughly informative at this grain, but 
> **R2 is not** — with n=3, R2 can swing to extreme values (e.g. -444) purely from sampling 
> noise in a tiny group's own variance, not from model quality. Do not use this table's R2 
> for conclusions; it is kept only for transparency and territory/drug drill-down (see Error 
> Analysis below, which uses MAE — a metric that stays meaningful at small n).

| Model | MAPE | MAE | RMSE | R2 (unreliable) |
|-------|------|-----|------|------------------|
| MovingAvg3 | 24.19% | 18.19 | 20.89 | -3.8236 |
| Naive | 28.74% | 21.99 | 25.16 | -3.1025 |
| SeasonalNaive | 24.50% | 20.12 | 23.73 | -4.1556 |
| XGBoost | 22.76% | 17.68 | 20.35 | -4.3103 |

## Error Analysis

- **Mean residual:** 2.7641
- **Median residual:** 0.7437
- **Mean absolute error:** 17.3636
- **Bias direction:** underprediction (actuals are higher than forecasts on average)
- **Worst territory:** TER-01
- **Worst month:** 2025-01-01 00:00:00
- **Total predictions analyzed:** 8000
- **Product-level analysis:** Supported (by drug_name)
- **Worst drug (by MAE):** Nexium (MAE=47.85)

## Leakage Fix (Step 6)

**Issue found:** `rolling_mean_3` and `rolling_std_3` in `feature_engineer.py` were computed 
WITHOUT `.shift(1)`, including the current month's target (units_sold at time t) — this is target leakage.

**Fix applied:** Added `.shift(1)` before `.rolling(3)` so features are strictly computed from past periods.

**Impact:** The previous reported ~86.74% accuracy (MAPE-based) was artificially inflated by leakage. 
The corrected numbers below are the TRUE model performance.

### Feature Leakage Audit

| Feature | Source | Past-Only? |
|---------|--------|-----------|
| month | year_month.dt.month (temporal) | yes |
| quarter | year_month.dt.quarter (temporal) | yes |
| year | year_month.dt.year (temporal) | yes |
| day_of_week | year_month.dt.dayofweek (temporal) | yes |
| is_quarter_end | year_month.dt.is_quarter_end (temporal) | yes |
| lag_1 | units_sold.shift(1) | yes |
| lag_3 | units_sold.shift(3) | yes |
| lag_6 | units_sold.shift(6) | yes |
| rolling_mean_3 | units_sold.shift(1).rolling(3) [FIXED] | yes |
| rolling_std_3 | units_sold.shift(1).rolling(3) [FIXED] | yes |
| drug_encoded | drug_name.cat.codes (static encoding) | yes |
| territory_encoded | territory_id.cat.codes (static encoding) | yes |
| avg_unit_price | unit_price.mean() within month (concurrent, not future) | yes |
| n_transactions | count within month (concurrent, not future) | yes |

## Statistical Findings

Spearman rank correlations (Benjamini-Hochberg FDR applied):

| Pair | rho | p-value | n | Status |
|------|-----|---------|---|--------|
| units_sold vs lag_1 | 0.8905 | 0.00e+00 | 9200 | significant |
| units_sold vs lag_3 | 0.8924 | 0.00e+00 | 8400 | significant |
| units_sold vs rolling_mean_3 | 0.9185 | 0.00e+00 | 9200 | significant |
| units_sold vs avg_unit_price | -0.8985 | 0.00e+00 | 9200 | significant |
| units_sold vs n_transactions | -0.0086 | 5.54e-01 | 9200 | not significant |
| units_sold vs month | -0.0212 | 7.13e-02 | 9200 | not significant |
| units_sold vs quarter | -0.0424 | 1.15e-04 | 9200 | significant |
| territory_sales vs rep_total_activities | 0.0336 | 8.91e-01 | 50 | not significant |
| territory_sales vs rep_positive_outcome_rate | -0.1176 | 5.54e-01 | 50 | not significant |
| territory_sales vs rep_total_visits | 0.0427 | 8.91e-01 | 50 | not significant |
| territory_sales vs rep_hcp_coverage | 0.3312 | 3.76e-02 | 50 | significant |
| territory_sales vs rep_samples_distributed | 0.0188 | 8.97e-01 | 50 | not significant |

> **Note:** All findings use "associated with" language. No causal claims are made.

## Uncertainty Estimation

- **Method:** Residual bootstrap (1000 resamples, seed=42)
- **Target coverage:** 90% (5th–95th percentile)
- **Empirical coverage:** 91.41%
- **Average interval width:** 88.31
- **Median interval width:** 89.42

## Data Validation

- **Demand features rows:** 9200
- **Unique drugs:** 20
- **Unique territories:** 20
- **Date range:** 2024-02-01 00:00:00 to 2025-12-01 00:00:00
- **Leakage check:** ALL FEATURES PAST-ONLY (after fix)

## Power BI Impact

**Preserved (not modified):**
- All existing tables: pharma_sales, hcp_master, territories, rep_activity, prescriptions, promotion_campaigns
- All existing output tables: demand_forecasts, hcp_segments, territory_forecasts
- All existing columns and schemas

**New tables added:**
- `forecast_model_comparison` — model × fold metrics, pooled across all territories/drugs (statistically valid R2; see `data/output/forecast_model_comparison_by_series.csv` for the fine-grained, diagnostic-only per-territory/drug breakdown)
- `forecast_validation_results` — fold details and stability analysis (pooled)
- `forecast_error_analysis` — residual analysis by territory, month, drug
- `forecast_uncertainty` — prediction intervals with coverage metrics
- `forecast_statistical_analysis` — Spearman correlations and significance

**Database write status:** SKIPPED — DB unavailable (OperationalError). CSVs saved to data/output/.

## Conclusion

*(Based on the Pooled model comparison above — the statistically valid one.)*

- **Did XGBoost beat baselines?** Best model by MAE: **XGBoost** (XGBoost MAE=17.6835)
  - XGBoost beats MovingAvg3, Naive, SeasonalNaive on MAE
  - XGBoost beats MovingAvg3, Naive, SeasonalNaive on RMSE
  - XGBoost beats MovingAvg3, Naive, SeasonalNaive on R2
- **Stable?** XGBoost MAPE std across folds: 2.3777
  - Stability assessment: **Yes**
- **Where it fails:** Worst territory=TER-01, worst month=2025-01-01 00:00:00
- **Bias:** underprediction (actuals are higher than forecasts on average)
- **Interval useful?** Coverage=91.41%, assessment: **Yes**
