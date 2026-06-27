-- ============================================================================
-- Territory KPIs
-- Pharma Sales Forecasting & HCP Intelligence Platform
-- ============================================================================

-- KPI 5
-- Business question:
-- How does each territory perform across revenue, units, prescription value, HCP
-- base, and field activity?
--
-- Explanation of the SQL:
-- Builds a single territory scorecard by combining sales, prescriptions, HCP
-- counts, and rep activity using territory_id as the common grain.
--
-- Why executives care:
-- Territory leaders need one view that balances commercial output and coverage.
--
-- Recommended Power BI visual:
-- Matrix or territory scorecard table with conditional formatting.
WITH sales AS (
    SELECT
        territory_id,
        SUM(revenue) AS sales_revenue,
        SUM(units_sold) AS units_sold
    FROM pharma_sales
    GROUP BY territory_id
),
rx AS (
    SELECT
        h.territory_id,
        SUM(p.total_value) AS prescription_value,
        COUNT(p.prescription_id) AS prescription_count
    FROM hcp_master h
    LEFT JOIN prescriptions p
        ON h.hcp_id = p.hcp_id
    GROUP BY h.territory_id
),
hcp AS (
    SELECT
        territory_id,
        COUNT(*) AS hcp_count
    FROM hcp_master
    GROUP BY territory_id
),
activity AS (
    SELECT
        territory_id,
        COUNT(*) AS activity_count,
        COUNT(DISTINCT rep_id) AS active_reps
    FROM rep_activity
    GROUP BY territory_id
)
SELECT
    t.territory_id,
    t.territory_name,
    t.region,
    ROUND(COALESCE(s.sales_revenue, 0), 2) AS sales_revenue,
    COALESCE(s.units_sold, 0) AS units_sold,
    ROUND(COALESCE(rx.prescription_value, 0), 2) AS prescription_value,
    COALESCE(rx.prescription_count, 0) AS prescription_count,
    COALESCE(hcp.hcp_count, 0) AS hcp_count,
    COALESCE(activity.activity_count, 0) AS activity_count,
    COALESCE(activity.active_reps, 0) AS active_reps
FROM territories t
LEFT JOIN sales s
    ON t.territory_id = s.territory_id
LEFT JOIN rx
    ON t.territory_id = rx.territory_id
LEFT JOIN hcp
    ON t.territory_id = hcp.territory_id
LEFT JOIN activity
    ON t.territory_id = activity.territory_id
ORDER BY sales_revenue DESC, prescription_value DESC;


-- KPI 6
-- Business question:
-- Which territories are most efficient at converting their HCP base into
-- prescription revenue?
--
-- Explanation of the SQL:
-- Divides total prescription value and prescription count by HCP count to show
-- value per HCP and scripts per HCP.
--
-- Why executives care:
-- This separates territory scale from territory productivity.
--
-- Recommended Power BI visual:
-- Scatter plot with HCP count on X and Rx value per HCP on Y.
WITH territory_hcp AS (
    SELECT
        territory_id,
        COUNT(*) AS hcp_count
    FROM hcp_master
    GROUP BY territory_id
),
territory_rx AS (
    SELECT
        h.territory_id,
        SUM(p.total_value) AS total_rx_value,
        COUNT(p.prescription_id) AS total_prescriptions
    FROM hcp_master h
    JOIN prescriptions p
        ON h.hcp_id = p.hcp_id
    GROUP BY h.territory_id
)
SELECT
    t.territory_id,
    t.territory_name,
    t.region,
    hcp.hcp_count,
    ROUND(COALESCE(rx.total_rx_value, 0), 2) AS total_rx_value,
    COALESCE(rx.total_prescriptions, 0) AS total_prescriptions,
    ROUND(COALESCE(rx.total_rx_value, 0) / NULLIF(hcp.hcp_count, 0), 2) AS rx_value_per_hcp,
    ROUND(COALESCE(rx.total_prescriptions, 0)::numeric / NULLIF(hcp.hcp_count, 0), 2) AS prescriptions_per_hcp
FROM territories t
LEFT JOIN territory_hcp hcp
    ON t.territory_id = hcp.territory_id
LEFT JOIN territory_rx rx
    ON t.territory_id = rx.territory_id
ORDER BY rx_value_per_hcp DESC NULLS LAST, prescriptions_per_hcp DESC NULLS LAST;


-- KPI 7
-- Business question:
-- What specialty mix drives prescription value inside each territory?
--
-- Explanation of the SQL:
-- Aggregates prescription value by territory and physician specialty, then ranks
-- specialties within each territory.
--
-- Why executives care:
-- Specialty concentration informs targeting, messaging, and sales force design.
--
-- Recommended Power BI visual:
-- Stacked bar chart or decomposition tree by territory and specialty.
WITH specialty_territory_rx AS (
    SELECT
        h.territory_id,
        h.specialty,
        COUNT(DISTINCT h.hcp_id) AS hcp_count,
        COUNT(p.prescription_id) AS prescription_count,
        SUM(p.total_value) AS prescription_value
    FROM hcp_master h
    LEFT JOIN prescriptions p
        ON h.hcp_id = p.hcp_id
    GROUP BY h.territory_id, h.specialty
)
SELECT
    territory_id,
    specialty,
    hcp_count,
    prescription_count,
    ROUND(COALESCE(prescription_value, 0), 2) AS prescription_value,
    ROUND(
        100.0 * COALESCE(prescription_value, 0)
        / NULLIF(SUM(COALESCE(prescription_value, 0)) OVER (PARTITION BY territory_id), 0),
        2
    ) AS territory_value_share_pct,
    RANK() OVER (
        PARTITION BY territory_id
        ORDER BY COALESCE(prescription_value, 0) DESC
    ) AS specialty_rank_in_territory
FROM specialty_territory_rx
ORDER BY territory_id, specialty_rank_in_territory;


-- KPI 8
-- Business question:
-- Which territories are underpenetrated versus target HCP coverage plans?
--
-- Explanation of the SQL:
-- Compares target HCP count in the territory master against HCPs actually engaged
-- by reps, then calculates coverage gap and penetration rate.
--
-- Why executives care:
-- This exposes execution gaps even where revenue has not yet declined.
--
-- Recommended Power BI visual:
-- Funnel or clustered bar chart of target vs engaged HCPs.
WITH engaged_hcps AS (
    SELECT
        territory_id,
        COUNT(DISTINCT hcp_id) AS engaged_hcp_count
    FROM rep_activity
    WHERE hcp_id IS NOT NULL
    GROUP BY territory_id
)
SELECT
    t.territory_id,
    t.territory_name,
    t.region,
    t.target_hcp_count,
    COALESCE(e.engaged_hcp_count, 0) AS engaged_hcp_count,
    t.target_hcp_count - COALESCE(e.engaged_hcp_count, 0) AS hcp_gap_to_target,
    ROUND(
        100.0 * COALESCE(e.engaged_hcp_count, 0)
        / NULLIF(t.target_hcp_count, 0),
        2
    ) AS target_penetration_pct
FROM territories t
LEFT JOIN engaged_hcps e
    ON t.territory_id = e.territory_id
ORDER BY target_penetration_pct ASC NULLS LAST, hcp_gap_to_target DESC;
