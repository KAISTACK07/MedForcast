-- ============================================================================
-- Sales Rep KPIs
-- Pharma Sales Forecasting & HCP Intelligence Platform
-- ============================================================================

-- KPI 9
-- Business question:
-- Which reps are most productive across activity volume, reach, and quality of
-- interaction?
--
-- Explanation of the SQL:
-- Aggregates core field metrics by rep, including unique HCP reach, average call
-- duration, and positive outcome rate.
--
-- Why executives care:
-- This is the base performance view for coaching, incentives, and capacity
-- planning.
--
-- Recommended Power BI visual:
-- Ranked table with conditional formatting or bubble chart.
SELECT
    rep_id,
    rep_name,
    territory_id,
    COUNT(*) AS total_activities,
    COUNT(DISTINCT hcp_id) AS unique_hcps_touched,
    ROUND(AVG(duration_minutes), 1) AS avg_duration_minutes,
    SUM(CASE WHEN activity_type = 'Visit' THEN 1 ELSE 0 END) AS visits,
    SUM(CASE WHEN activity_type = 'Phone Call' THEN 1 ELSE 0 END) AS phone_calls,
    SUM(CASE WHEN activity_type = 'Virtual Meeting' THEN 1 ELSE 0 END) AS virtual_meetings,
    ROUND(
        100.0 * SUM(CASE WHEN outcome = 'Positive' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        2
    ) AS positive_outcome_rate_pct
FROM rep_activity
GROUP BY rep_id, rep_name, territory_id
ORDER BY total_activities DESC, positive_outcome_rate_pct DESC;


-- KPI 10
-- Business question:
-- Which reps control the strongest commercial territories, based on territory
-- sales and prescription value?
--
-- Explanation of the SQL:
-- Uses territory as the join path between rep activity, sales, and prescriptions.
-- This is a territory-attributed revenue proxy because direct rep-to-sale keys do
-- not exist in the warehouse.
--
-- Why executives care:
-- Leadership needs to separate rep execution from territory potential.
--
-- Recommended Power BI visual:
-- Scatter plot of territory sales vs positive outcome rate by rep.
WITH territory_sales AS (
    SELECT
        territory_id,
        SUM(revenue) AS territory_sales_revenue
    FROM pharma_sales
    WHERE sale_date >= '2024-01-01' AND sale_date < '2026-01-01'
    GROUP BY territory_id
),
territory_rx AS (
    SELECT
        h.territory_id,
        SUM(p.total_value) AS territory_rx_value
    FROM hcp_master h
    JOIN prescriptions p
        ON h.hcp_id = p.hcp_id
    GROUP BY h.territory_id
),
rep_base AS (
    SELECT
        rep_id,
        rep_name,
        territory_id,
        COUNT(*) AS total_activities,
        ROUND(
            100.0 * SUM(CASE WHEN outcome = 'Positive' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0),
            2
        ) AS positive_outcome_rate_pct
    FROM rep_activity
    GROUP BY rep_id, rep_name, territory_id
)
SELECT
    r.rep_id,
    r.rep_name,
    r.territory_id,
    r.total_activities,
    r.positive_outcome_rate_pct,
    ROUND(COALESCE(ts.territory_sales_revenue, 0), 2) AS territory_sales_revenue,
    ROUND(COALESCE(trx.territory_rx_value, 0), 2) AS territory_rx_value
FROM rep_base r
LEFT JOIN territory_sales ts
    ON r.territory_id = ts.territory_id
LEFT JOIN territory_rx trx
    ON r.territory_id = trx.territory_id
ORDER BY territory_sales_revenue DESC, positive_outcome_rate_pct DESC;


-- KPI 11
-- Business question:
-- Are sample drops generating quality outcomes, and which reps are most efficient
-- with sample deployment?
--
-- Explanation of the SQL:
-- Filters to sample-drop activities and measures both volume and the share of
-- positive outcomes per rep.
--
-- Why executives care:
-- Sampling is expensive and should be tied to measurable field effectiveness.
--
-- Recommended Power BI visual:
-- Combo chart of samples distributed and positive sample outcome rate.
SELECT
    rep_id,
    rep_name,
    territory_id,
    COUNT(*) AS sample_drop_events,
    SUM(samples_left) AS total_samples_distributed,
    ROUND(AVG(samples_left), 2) AS avg_samples_per_drop,
    ROUND(
        100.0 * SUM(CASE WHEN outcome = 'Positive' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        2
    ) AS positive_sample_outcome_rate_pct
FROM rep_activity
WHERE activity_type = 'Sample Drop'
GROUP BY rep_id, rep_name, territory_id
ORDER BY total_samples_distributed DESC, positive_sample_outcome_rate_pct DESC;


-- KPI 12
-- Business question:
-- How fully is each rep covering the HCP universe in their assigned territory?
--
-- Explanation of the SQL:
-- Compares each rep's distinct HCP reach against the total HCP base of the same
-- territory.
--
-- Why executives care:
-- Coverage gaps typically precede future sales weakness and missed launch
-- opportunities.
--
-- Recommended Power BI visual:
-- Gauge or horizontal bar chart of HCP coverage % by rep.
WITH territory_hcp AS (
    SELECT
        territory_id,
        COUNT(*) AS territory_hcp_count
    FROM hcp_master
    GROUP BY territory_id
),
rep_hcp_coverage AS (
    SELECT
        rep_id,
        rep_name,
        territory_id,
        COUNT(DISTINCT hcp_id) AS hcp_covered
    FROM rep_activity
    WHERE hcp_id IS NOT NULL
    GROUP BY rep_id, rep_name, territory_id
)
SELECT
    r.rep_id,
    r.rep_name,
    r.territory_id,
    h.territory_hcp_count,
    r.hcp_covered,
    ROUND(100.0 * r.hcp_covered / NULLIF(h.territory_hcp_count, 0), 2) AS hcp_coverage_pct
FROM rep_hcp_coverage r
JOIN territory_hcp h
    ON r.territory_id = h.territory_id
ORDER BY hcp_coverage_pct DESC, hcp_covered DESC;
