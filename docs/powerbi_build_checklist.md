# Power BI Build Checklist: Pharma Sales Forecasting & HCP Intelligence

**Role:** Senior BI Engineer  
**Target Audience:** Student Analyst  
**Objective:** Provide a step-by-step implementation guide to build out the 6 core dashboards using the validated PostgreSQL warehouse and generated data science outputs.

> **General Prerequisites:** 
> - Load the `DimDate` table (Auto-generate via Power Query or DAX).
> - Set up connections to the local PostgreSQL `pharma_analytics` database.
> - Load the CSV outputs (`hcp_segments.csv`, `territory_forecasts.csv`, `demand_forecasts.csv`) from the `data/output` directory.

---

## 1. Executive Summary Dashboard

1. **Exact tables required:** 
   - `pharma_sales`
   - `DimDate`
2. **Exact relationships required:**
   - `DimDate[Date]` (1) ➔ `pharma_sales[sale_date]` (*)
3. **DAX measures required:**
   - `Total Revenue = SUM(pharma_sales[revenue])`
   - `Total Units Sold = SUM(pharma_sales[units_sold])`
   - `Revenue MoM % = DIVIDE([Total Revenue] - CALCULATE([Total Revenue], DATEADD(DimDate[Date], -1, MONTH)), CALCULATE([Total Revenue], DATEADD(DimDate[Date], -1, MONTH)))`
   - `Brand Share % = DIVIDE([Total Revenue], CALCULATE([Total Revenue], ALL(pharma_sales[drug_name])))`
4. **Visual build order:**
   - **Step 1:** Build Multi-row KPI Cards for top-line metrics.
   - **Step 2:** Build the Dual-axis MoM Line Chart.
   - **Step 3:** Build the Brand Share Sorted Bar Chart.
5. **Estimated build time:** 1.0 hour.
6. **Common implementation mistakes:**
   - Failing to mark `DimDate` as a "Date Table," which causes the `DATEADD` Time Intelligence function in the `Revenue MoM %` measure to fail.
7. **Validation checks after implementation:**
   - Ensure `Total Revenue` exactly equals **$1,087,677,214.46**.
   - Ensure the transaction count equals **23,955**.

---

## 2. Territory Performance Dashboard

1. **Exact tables required:** 
   - `territories` (Dimension)
   - `hcp_master` (Dimension)
   - `pharma_sales` (Fact)
   - `prescriptions` (Fact)
   - `rep_activity` (Fact)
2. **Exact relationships required:**
   - `territories[territory_id]` (1) ➔ `pharma_sales[territory_id]` (*)
   - `territories[territory_id]` (1) ➔ `hcp_master[territory_id]` (*)
   - `hcp_master[hcp_id]` (1) ➔ `prescriptions[hcp_id]` (*)
   - `hcp_master[hcp_id]` (1) ➔ `rep_activity[hcp_id]` (*)
3. **DAX measures required:**
   - `Rx Value per HCP = DIVIDE(SUM(prescriptions[total_value]), DISTINCTCOUNT(hcp_master[hcp_id]))`
   - `Target Penetration % = DIVIDE(DISTINCTCOUNT(rep_activity[hcp_id]), DISTINCTCOUNT(hcp_master[hcp_id]))`
4. **Visual build order:**
   - **Step 1:** Scorecard Matrix (Revenue, Units, Rx Value).
   - **Step 2:** Target Penetration Clustered Bar Chart.
   - **Step 3:** Scatter Plot (HCP Count vs Rx Value per HCP).
   - **Step 4:** Specialty Mix Stacked Bar Chart.
5. **Estimated build time:** 1.5 hours.
6. **Common implementation mistakes:**
   - Creating bidirectional many-to-many relationships. Stick to the defined star schema where `territories` filters `hcp_master` and the fact tables.
   - Using the flawed `territories[target_hcp_count]` field as the denominator for penetration (as flagged in the KPI audit). Always use `DISTINCTCOUNT(hcp_master[hcp_id])`.
7. **Validation checks after implementation:**
   - Check that `Target Penetration %` never exceeds 100% for any territory.
   - Confirm all 20 territories are present.

---

## 3. Rep Productivity Dashboard

1. **Exact tables required:** 
   - `rep_activity` (Fact)
   - `hcp_master` (Dimension)
   - `pharma_sales` (Fact)
   - `territories` (Dimension)
2. **Exact relationships required:**
   - `territories[territory_id]` (1) ➔ `rep_activity[territory_id]` (*)
   - `territories[territory_id]` (1) ➔ `pharma_sales[territory_id]` (*)
   - `hcp_master[hcp_id]` (1) ➔ `rep_activity[hcp_id]` (*)
3. **DAX measures required:**
   - `Positive Outcome Rate % = DIVIDE(CALCULATE(COUNTROWS(rep_activity), rep_activity[outcome] = "Positive"), COUNTROWS(rep_activity))`
   - `HCP Coverage % = DIVIDE(DISTINCTCOUNT(rep_activity[hcp_id]), CALCULATE(COUNTROWS(hcp_master), ALLEXCEPT(hcp_master, hcp_master[territory_id])))`
   - `Avg Duration = AVERAGE(rep_activity[duration_minutes])`
4. **Visual build order:**
   - **Step 1:** Ranked Table of Reps (Total Activities, Positive Outcome %).
   - **Step 2:** Scatter Plot (Territory Sales vs. Positive Outcome Rate by Rep).
   - **Step 3:** Sample Drop Combo Chart.
   - **Step 4:** HCP Coverage % Gauge or Horizontal Bar Chart.
5. **Estimated build time:** 1.5 hours.
6. **Common implementation mistakes:**
   - Joining `rep_activity` directly to `pharma_sales`. Since they are at different grains, filtering must pass through the `territories` dimension table.
   - Ignoring the date range mismatch (Sales data covers 2022-2023, while Rep Activity covers 2023-only). Sales filtering should be localized to 2023 when comparing Rep performance.
7. **Validation checks after implementation:**
   - Ensure the total distinct number of reps equals **50**.
   - Verify `Avg Duration` falls within the logical 10 to 90 minute bounds.

---

## 4. HCP Intelligence Dashboard

1. **Exact tables required:** 
   - `hcp_segments` (Loaded from ML outputs CSV)
   - `prescriptions`
2. **Exact relationships required:**
   - `hcp_segments[hcp_id]` (1) ➔ `prescriptions[hcp_id]` (*)
3. **DAX measures required:**
   - `HCP Count by Segment = CALCULATE(DISTINCTCOUNT(hcp_segments[hcp_id]))`
   - `Revenue Contribution % = DIVIDE(SUM(hcp_segments[monetary]), CALCULATE(SUM(hcp_segments[monetary]), ALL(hcp_segments)))`
   - `Avg Frequency = AVERAGE(hcp_segments[frequency])`
4. **Visual build order:**
   - **Step 1:** Segment KPI Cards (Count, Revenue).
   - **Step 2:** Segment Distribution Donut Chart.
   - **Step 3:** Revenue by Segment Horizontal Bar Chart.
   - **Step 4:** HCP Value Matrix Scatter Plot.
5. **Estimated build time:** 1.0 hour.
6. **Common implementation mistakes:**
   - Attempting to rebuild the complex K-Means clustering algorithm purely via DAX instead of just importing the pre-processed `hcp_segments` table.
7. **Validation checks after implementation:**
   - Ensure exactly 5 distinct segments exist: Champions, Loyal HCPs, High Potential, At Risk, Low Value.
   - Total HCP count across segments must exactly equal **500**.

---

## 5. Promotion ROI Dashboard

1. **Exact tables required:** 
   - `promotion_campaigns`
2. **Exact relationships required:**
   - None strictly required for cross-filtering. Connect `DimDate` to `start_date` if temporal filtering is desired.
3. **DAX measures required:**
   - `Incremental Revenue = SUM(promotion_campaigns[revenue_after]) - SUM(promotion_campaigns[revenue_before])`
   - `ROI Multiple = DIVIDE([Incremental Revenue], SUM(promotion_campaigns[budget]))`
   - `Cost per HCP Reached = DIVIDE(SUM(promotion_campaigns[budget]), SUM(promotion_campaigns[hcps_reached]))`
   - `Reach Rate % = DIVIDE(SUM(promotion_campaigns[hcps_reached]), SUM(promotion_campaigns[hcps_targeted]))`
4. **Visual build order:**
   - **Step 1:** Summary KPI Cards (ROI, Budget, Lift).
   - **Step 2:** Incremental Lift Waterfall Chart by Campaign.
   - **Step 3:** Channel ROI Clustered Bar Chart.
   - **Step 4:** Cost vs. Revenue Efficiency Scatter Plot.
5. **Estimated build time:** 45 minutes.
6. **Common implementation mistakes:**
   - Taking the metrics as actual historical fact. As per the audit, campaign dates are set in 2026 and represent planning estimates. Include a text box caveat on the dashboard to warn end-users.
7. **Validation checks after implementation:**
   - Ensure the `Reach Rate %` never exceeds 100%.
   - The Waterfall chart total column must equal the overall `Incremental Revenue` card.

---

## 6. Forecasting Dashboard

1. **Exact tables required:** 
   - `territory_forecasts` (Loaded from ML outputs CSV)
   - `demand_forecasts` (Loaded from ML outputs CSV)
   - `territories` (Dimension)
2. **Exact relationships required:**
   - `territories[territory_id]` (1) ➔ `territory_forecasts[territory_id]` (*)
3. **DAX measures required:**
   - `Forecasted Revenue = SUM(territory_forecasts[total_forecasted_revenue])`
   - `Forecasted Units = SUM(territory_forecasts[total_forecasted_units])`
   - `Variance to Actuals = SUM(demand_forecasts[predicted]) - SUM(demand_forecasts[actual])`
4. **Visual build order:**
   - **Step 1:** Model Accuracy Summary Cards (MAPE, MAE, R²).
   - **Step 2:** Feature Importance Bar Chart.
   - **Step 3:** Forecast vs. Actuals Line Chart.
   - **Step 4:** Territory-level Forecast Matrix Table.
5. **Estimated build time:** 1.0 hour.
6. **Common implementation mistakes:**
   - Trying to aggregate Mean Absolute Percentage Error (MAPE) by calculating the `AVERAGE(mape)` at higher hierarchical levels. MAPE must not be averaged; standard metrics should just display the pre-calculated model score text.
   - Plotting feature importance as an absolute scalar rather than relative gain.
7. **Validation checks after implementation:**
   - Ensure the total `Forecasted Units` visually matches the aggregate output produced by the Python XGBoost regressor log.
   - Check that forecast lines seamlessly connect to historical actuals.
