-- ─────────────────────────────────────────────────────────────────────────────
-- 03_mrr_waterfall.sql
-- MRR movement analysis: New / Expansion / Contraction / Churn / Net.
-- Standard SaaS board-level reporting metric.
-- ─────────────────────────────────────────────────────────────────────────────

-- Monthly MRR waterfall
SELECT
    month,
    ROUND(SUM(CASE WHEN event = 'new'         THEN mrr  ELSE 0 END), 2) AS new_mrr,
    ROUND(SUM(CASE WHEN event = 'expansion'   THEN mrr  ELSE 0 END), 2) AS expansion_mrr,
    ROUND(SUM(CASE WHEN event = 'contraction' THEN mrr  ELSE 0 END), 2) AS contraction_mrr,
    ROUND(SUM(CASE WHEN event = 'churn'       THEN mrr  ELSE 0 END), 2) AS churned_mrr,
    ROUND(SUM(CASE WHEN event NOT IN ('active') THEN mrr ELSE 0 END), 2) AS net_new_mrr,
    ROUND(SUM(CASE WHEN event IN ('active','expansion','new') THEN mrr ELSE 0 END), 2) AS ending_mrr
FROM subscription_events
GROUP BY month
ORDER BY month;


-- Cumulative MRR growth
WITH monthly AS (
    SELECT
        month,
        ROUND(SUM(CASE WHEN event IN ('active','expansion','new') THEN mrr ELSE 0 END), 2) AS mrr
    FROM subscription_events
    GROUP BY month
)
SELECT
    month,
    mrr,
    LAG(mrr) OVER (ORDER BY month)                          AS prev_mrr,
    ROUND(mrr - LAG(mrr) OVER (ORDER BY month), 2)          AS mrr_change,
    ROUND(
        (mrr / NULLIF(LAG(mrr) OVER (ORDER BY month), 0) - 1) * 100,
        2
    )                                                        AS mrr_growth_pct
FROM monthly
ORDER BY month;


-- Churn analysis: customers churned per month and MRR lost
SELECT
    e.month,
    c.plan,
    COUNT(DISTINCT e.customer_id)   AS customers_churned,
    ROUND(ABS(SUM(e.mrr)), 2)       AS mrr_lost
FROM subscription_events e
JOIN customers c ON e.customer_id = c.customer_id
WHERE e.event = 'churn'
GROUP BY e.month, c.plan
ORDER BY e.month, mrr_lost DESC;


-- Expansion wins by plan (which plan generates most upgrade revenue)
SELECT
    e.month,
    c.plan                          AS upgraded_to,
    COUNT(DISTINCT e.customer_id)   AS customers_expanded,
    ROUND(SUM(e.mrr), 2)            AS expansion_mrr
FROM subscription_events e
JOIN customers c ON e.customer_id = c.customer_id
WHERE e.event = 'expansion'
GROUP BY e.month, c.plan
ORDER BY e.month, expansion_mrr DESC;
