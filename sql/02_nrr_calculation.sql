-- ─────────────────────────────────────────────────────────────────────────────
-- 02_nrr_calculation.sql
-- Net Revenue Retention (NRR) calculation by month and by plan.
-- NRR = (existing_mrr + expansion - contraction - churn) / existing_mrr_prev × 100
-- ─────────────────────────────────────────────────────────────────────────────

-- Monthly MRR by event type
SELECT
    month,
    event,
    SUM(mrr)          AS total_mrr,
    COUNT(customer_id) AS customers
FROM subscription_events
WHERE event IN ('new','expansion','contraction','churn','active')
GROUP BY month, event
ORDER BY month, event;


-- Monthly NRR approximation
WITH monthly AS (
    SELECT
        month,
        SUM(CASE WHEN event IN ('active','expansion') THEN mrr ELSE 0 END) AS active_mrr,
        SUM(CASE WHEN event = 'new'         THEN mrr ELSE 0 END)           AS new_mrr,
        SUM(CASE WHEN event = 'expansion'   THEN mrr ELSE 0 END)           AS expansion_mrr,
        SUM(CASE WHEN event = 'churn'       THEN mrr ELSE 0 END)           AS churned_mrr,
        SUM(CASE WHEN event = 'contraction' THEN mrr ELSE 0 END)           AS contraction_mrr
    FROM subscription_events
    GROUP BY month
),
with_existing AS (
    SELECT
        month,
        active_mrr,
        new_mrr,
        expansion_mrr,
        churned_mrr,
        contraction_mrr,
        active_mrr - new_mrr AS existing_mrr
    FROM monthly
)
SELECT
    w.month,
    ROUND(w.existing_mrr, 0)                                           AS existing_mrr,
    ROUND(w.expansion_mrr, 0)                                          AS expansion_mrr,
    ROUND(w.churned_mrr, 0)                                            AS churned_mrr,
    ROUND(w.contraction_mrr, 0)                                        AS contraction_mrr,
    ROUND(
        (w.existing_mrr + w.expansion_mrr + w.churned_mrr + w.contraction_mrr)
        / NULLIF(LAG(w.existing_mrr) OVER (ORDER BY w.month), 0) * 100,
        2
    )                                                                  AS nrr_pct
FROM with_existing w
ORDER BY w.month;


-- NRR summary by plan (lifetime approximation)
WITH plan_mrr AS (
    SELECT
        c.plan,
        SUM(CASE WHEN e.event = 'expansion'   THEN e.mrr ELSE 0 END) AS total_expansion,
        SUM(CASE WHEN e.event = 'churn'       THEN ABS(e.mrr) ELSE 0 END) AS total_churn_mrr,
        SUM(CASE WHEN e.event = 'contraction' THEN ABS(e.mrr) ELSE 0 END) AS total_contraction,
        SUM(CASE WHEN e.event IN ('active','expansion') THEN e.mrr ELSE 0 END) AS total_active_mrr,
        SUM(CASE WHEN e.event = 'new'         THEN e.mrr ELSE 0 END) AS total_new_mrr
    FROM subscription_events e
    JOIN customers c ON e.customer_id = c.customer_id
    GROUP BY c.plan
)
SELECT
    plan,
    ROUND(total_active_mrr - total_new_mrr, 0)  AS existing_mrr,
    ROUND(total_expansion, 0)                    AS expansion_mrr,
    ROUND(total_churn_mrr, 0)                    AS churned_mrr,
    ROUND(
        (total_active_mrr - total_new_mrr + total_expansion - total_churn_mrr - total_contraction)
        / NULLIF(total_active_mrr - total_new_mrr, 0) * 100,
        2
    )                                            AS approx_nrr_pct
FROM plan_mrr
ORDER BY approx_nrr_pct DESC;
