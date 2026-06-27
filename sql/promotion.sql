-- ============================================================================
-- Promotion KPIs
-- Pharma Sales Forecasting & HCP Intelligence Platform
-- ============================================================================

-- KPI 13
-- Business question:
-- Which campaigns generated the strongest prescription lift and revenue return?
--
-- Explanation of the SQL:
-- Calculates before/after deltas, lift percentages, and return on promotional
-- spend for each campaign.
--
-- Why executives care:
-- This is the clearest read on whether marketing investment is compounding or
-- wasting budget.
--
-- Recommended Power BI visual:
-- Sorted bar chart or waterfall chart by incremental revenue.
SELECT
    campaign_id,
    campaign_name,
    drug_name,
    channel,
    ROUND(budget, 2) AS budget,
    prescriptions_before,
    prescriptions_after,
    prescriptions_after - prescriptions_before AS incremental_prescriptions,
    ROUND(
        100.0 * (prescriptions_after - prescriptions_before)
        / NULLIF(prescriptions_before, 0),
        2
    ) AS prescription_lift_pct,
    ROUND(revenue_before, 2) AS revenue_before,
    ROUND(revenue_after, 2) AS revenue_after,
    ROUND(revenue_after - revenue_before, 2) AS incremental_revenue,
    ROUND(
        (revenue_after - revenue_before) / NULLIF(budget, 0),
        2
    ) AS revenue_roi_multiple
FROM promotion_campaigns
ORDER BY incremental_revenue DESC, prescription_lift_pct DESC;


-- KPI 14
-- Business question:
-- Which promotional channels deliver the best aggregate return?
--
-- Explanation of the SQL:
-- Rolls campaign results up to channel level and measures incremental revenue,
-- ROI, and average reach efficiency.
--
-- Why executives care:
-- Channel mix decisions drive media allocation and brand planning.
--
-- Recommended Power BI visual:
-- Clustered bar chart by channel with ROI multiple as a label.
SELECT
    channel,
    COUNT(*) AS campaign_count,
    ROUND(SUM(budget), 2) AS total_budget,
    ROUND(SUM(revenue_after - revenue_before), 2) AS incremental_revenue,
    SUM(prescriptions_after - prescriptions_before) AS incremental_prescriptions,
    ROUND(
        SUM(revenue_after - revenue_before) / NULLIF(SUM(budget), 0),
        2
    ) AS channel_roi_multiple,
    ROUND(AVG(hcps_reached::numeric / NULLIF(hcps_targeted, 0)) * 100, 2) AS avg_reach_rate_pct
FROM promotion_campaigns
GROUP BY channel
ORDER BY channel_roi_multiple DESC, incremental_revenue DESC;


-- KPI 15
-- Business question:
-- Which campaigns are most efficient at converting budget into HCP reach and
-- incremental value?
--
-- Explanation of the SQL:
-- Measures cost per HCP reached, incremental revenue per reached HCP, and
-- budget efficiency per campaign.
--
-- Why executives care:
-- This identifies scalable campaign designs and exposes expensive low-yield
-- programs.
--
-- Recommended Power BI visual:
-- Scatter plot of cost per HCP reached vs incremental revenue.
SELECT
    campaign_id,
    campaign_name,
    drug_name,
    channel,
    ROUND(budget, 2) AS budget,
    hcps_targeted,
    hcps_reached,
    ROUND(budget / NULLIF(hcps_reached, 0), 2) AS cost_per_hcp_reached,
    ROUND((revenue_after - revenue_before), 2) AS incremental_revenue,
    ROUND((revenue_after - revenue_before) / NULLIF(hcps_reached, 0), 2) AS incremental_revenue_per_hcp,
    ROUND(
        100.0 * hcps_reached / NULLIF(hcps_targeted, 0),
        2
    ) AS reach_rate_pct
FROM promotion_campaigns
ORDER BY incremental_revenue_per_hcp DESC, cost_per_hcp_reached ASC;
