-- ─────────────────────────────────────────────────────────────────────────────
-- 01_cohort_table.sql
-- Builds logo (customer) cohort retention table using window functions.
-- Tables: customers(customer_id, acquisition_month, plan, channel)
--         subscription_events(month, customer_id, plan, event, mrr)
-- ─────────────────────────────────────────────────────────────────────────────

-- Step 1: Active customers per cohort per calendar month
WITH cohort_activity AS (
    SELECT
        c.acquisition_month                                     AS cohort_month,
        e.month                                                 AS activity_month,
        e.customer_id,
        -- Cohort index: months since acquisition
        (
            (CAST(SUBSTR(e.month, 1, 4) AS INT) - CAST(SUBSTR(c.acquisition_month, 1, 4) AS INT)) * 12
            + CAST(SUBSTR(e.month, 6, 2) AS INT) - CAST(SUBSTR(c.acquisition_month, 6, 2) AS INT)
        ) AS cohort_index
    FROM subscription_events e
    JOIN customers c ON e.customer_id = c.customer_id
    WHERE e.event IN ('active', 'expansion', 'new')
),

-- Step 2: Count unique active customers per cohort × month
cohort_counts AS (
    SELECT
        cohort_month,
        cohort_index,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM cohort_activity
    GROUP BY cohort_month, cohort_index
),

-- Step 3: Cohort sizes (month 0)
cohort_sizes AS (
    SELECT cohort_month, active_customers AS cohort_size
    FROM cohort_counts
    WHERE cohort_index = 0
)

-- Step 4: Retention rate
SELECT
    cc.cohort_month,
    cc.cohort_index,
    cc.active_customers,
    cs.cohort_size,
    ROUND(100.0 * cc.active_customers / cs.cohort_size, 2) AS retention_pct
FROM cohort_counts cc
JOIN cohort_sizes cs ON cc.cohort_month = cs.cohort_month
ORDER BY cc.cohort_month, cc.cohort_index;


-- Average retention by cohort index across all cohorts
WITH cohort_activity AS (
    SELECT
        c.acquisition_month AS cohort_month,
        e.customer_id,
        ((CAST(SUBSTR(e.month,1,4) AS INT) - CAST(SUBSTR(c.acquisition_month,1,4) AS INT))*12
         + CAST(SUBSTR(e.month,6,2) AS INT) - CAST(SUBSTR(c.acquisition_month,6,2) AS INT)) AS cohort_index
    FROM subscription_events e
    JOIN customers c ON e.customer_id = c.customer_id
    WHERE e.event IN ('active','expansion','new')
),
counts AS (
    SELECT cohort_month, cohort_index, COUNT(DISTINCT customer_id) AS n
    FROM cohort_activity GROUP BY cohort_month, cohort_index
),
sizes AS (
    SELECT cohort_month, n AS size FROM counts WHERE cohort_index = 0
)
SELECT
    c.cohort_index,
    ROUND(AVG(100.0 * c.n / s.size), 2) AS avg_retention_pct,
    COUNT(*)                             AS cohorts_with_data
FROM counts c JOIN sizes s ON c.cohort_month = s.cohort_month
GROUP BY c.cohort_index
ORDER BY c.cohort_index;
