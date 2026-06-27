-- ============================================================================
-- Executive KPIs
-- Pharma Sales Forecasting & HCP Intelligence Platform
-- ============================================================================

-- KPI 1
-- Business question:
-- How large is the commercial business today in terms of revenue, unit volume,
-- transaction count, active territories, and active brands?
--
-- Explanation of the SQL:
-- Aggregates the full pharma_sales table into one executive scorecard. This is
-- the fastest way to anchor every other KPI in the warehouse.
--
-- Why executives care:
-- This is the top-line operating snapshot used in business reviews and board
-- summaries.
--
-- Recommended Power BI visual:
-- Multi-row KPI card.
SELECT
    ROUND(SUM(revenue), 2) AS total_revenue,
    SUM(units_sold) AS total_units_sold,
    COUNT(*) AS sales_transactions,
    COUNT(DISTINCT territory_id) AS active_territories,
    COUNT(DISTINCT drug_name) AS active_brands,
    ROUND(AVG(unit_price), 2) AS avg_unit_price
FROM pharma_sales;


-- KPI 2
-- Business question:
-- How is revenue trending month over month, and where is growth accelerating or
-- slowing?
--
-- Explanation of the SQL:
-- Buckets transactional sales into monthly periods, then calculates month-over-
-- month revenue and unit growth using window functions.
--
-- Why executives care:
-- This shows whether demand momentum is improving, flat, or deteriorating.
--
-- Recommended Power BI visual:
-- Dual-axis line chart for revenue and MoM growth %.
WITH monthly_sales AS (
    SELECT
        date_trunc('month', sale_date)::date AS sales_month,
        SUM(revenue) AS revenue,
        SUM(units_sold) AS units_sold
    FROM pharma_sales
    GROUP BY 1
)
SELECT
    sales_month,
    ROUND(revenue, 2) AS revenue,
    units_sold,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY sales_month))
        / NULLIF(LAG(revenue) OVER (ORDER BY sales_month), 0),
        2
    ) AS revenue_mom_growth_pct,
    ROUND(
        100.0 * (units_sold - LAG(units_sold) OVER (ORDER BY sales_month))
        / NULLIF(LAG(units_sold) OVER (ORDER BY sales_month), 0),
        2
    ) AS units_mom_growth_pct
FROM monthly_sales
ORDER BY sales_month;


-- KPI 3
-- Business question:
-- Which brands drive the majority of revenue, and how concentrated is the
-- portfolio?
--
-- Explanation of the SQL:
-- Sums revenue by brand, ranks brands by contribution, and calculates each
-- brand's share of total company revenue.
--
-- Why executives care:
-- Portfolio concentration drives pricing risk, promotion focus, and supply
-- prioritization.
--
-- Recommended Power BI visual:
-- Sorted bar chart with data labels for revenue share %.
WITH brand_revenue AS (
    SELECT
        drug_name,
        SUM(revenue) AS revenue
    FROM pharma_sales
    GROUP BY drug_name
)
SELECT
    drug_name,
    ROUND(revenue, 2) AS revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2) AS revenue_share_pct,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM brand_revenue
ORDER BY revenue DESC;


-- KPI 4
-- Business question:
-- Which territories are ahead or behind annual quota, and what is the enterprise
-- attainment picture?
--
-- Explanation of the SQL:
-- Joins territory quotas to realized sales and calculates attainment %, gap to
-- quota, and a performance band for each territory.
--
-- Why executives care:
-- Quota attainment is the operating signal for resource allocation and field
-- leadership accountability.
--
-- Recommended Power BI visual:
-- Horizontal bar chart or bullet chart by territory.
WITH territory_sales AS (
    SELECT
        territory_id,
        SUM(revenue) AS actual_revenue
    FROM pharma_sales
    WHERE sale_date >= '2023-01-01' AND sale_date < '2024-01-01'
    GROUP BY territory_id
)
SELECT
    t.territory_id,
    t.territory_name,
    t.region,
    ROUND(COALESCE(ts.actual_revenue, 0), 2) AS actual_revenue,
    ROUND(t.annual_quota, 2) AS annual_quota,
    ROUND(COALESCE(ts.actual_revenue, 0) - t.annual_quota, 2) AS quota_gap,
    ROUND(100.0 * COALESCE(ts.actual_revenue, 0) / NULLIF(t.annual_quota, 0), 2) AS quota_attainment_pct,
    CASE
        WHEN COALESCE(ts.actual_revenue, 0) >= t.annual_quota THEN 'At/Above Quota'
        WHEN COALESCE(ts.actual_revenue, 0) >= t.annual_quota * 0.9 THEN 'Near Quota'
        ELSE 'Below Quota'
    END AS attainment_band
FROM territories t
LEFT JOIN territory_sales ts
    ON t.territory_id = ts.territory_id
ORDER BY quota_attainment_pct DESC NULLS LAST, actual_revenue DESC;
