# SaaS Cohort Retention Analysis

Portfolio data analytics project demonstrating SaaS retention metrics: cohort heatmaps, Net Revenue Retention (NRR), MRR waterfall, and churn analysis by plan tier and acquisition channel.

## Business Problem

A B2B SaaS company with 3 pricing tiers (Starter $29, Pro $79, Enterprise $199) needs to understand: which customer cohorts retain best, where the biggest churn happens, and how to grow NRR above 100%.

## Key Metrics

| Metric | Value |
| --- | ---: |
| Customers acquired (24 mo) | 1,600 |
| Active customers (end) | 903 |
| MRR (final month) | $87,635 |
| Avg Net Revenue Retention | ~97% |
| Total Expansion MRR | +$32,050 |
| Total Churned MRR | -$32,771 |

## The Core Insight

> **Logo retention ≠ Revenue retention.**
> 37% of customers churned over 24 months, yet MRR barely declined because Pro→Enterprise upgrades nearly offset churn in dollar terms. This is why NRR is the defining SaaS metric — not raw churn rate.

## Live Dashboard

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Repository Structure

```text
.
├── app.py                            # Streamlit dashboard (4 pages)
├── data/
│   ├── customers.csv                 # Customer metadata (plan, channel, acquisition month)
│   ├── subscription_events.csv       # Monthly events: new/active/expansion/contraction/churn
│   └── generate_saas_data.py         # Reproducible data generator
├── notebooks/
│   ├── 01_logo_retention.ipynb       # Customer cohort heatmap + retention curves
│   ├── 02_revenue_retention.ipynb    # NRR, MRR waterfall, NRR by plan
│   └── 03_churn_analysis.ipynb       # Churn by plan, channel, monthly trend
├── sql/
│   ├── 01_cohort_table.sql           # Cohort table with window functions
│   ├── 02_nrr_calculation.sql        # NRR by month and by plan
│   └── 03_mrr_waterfall.sql          # MRR movements: new/expansion/contraction/churn
└── images/                           # Exported charts
```

## Retention by Plan

| Plan | Monthly Price | Monthly Churn | 24-mo Retention | NRR Contribution |
| --- | ---: | ---: | ---: | --- |
| Starter | $29 | 8.2% | ~18% | Drag |
| Pro | $79 | 4.8% | ~36% | Neutral |
| Enterprise | $199 | 1.8% | ~65% | Expansion engine |

## Skills Demonstrated

- SaaS cohort retention analysis (logo and revenue retention)
- Net Revenue Retention (NRR) calculation and interpretation
- MRR waterfall: new / expansion / contraction / churn decomposition
- Cohort heatmap visualization (Plotly imshow + seaborn heatmap)
- Churn segmentation by plan tier and acquisition channel
- SQL window functions for cohort table and cumulative metrics
- Synthetic SaaS data generation with realistic churn/expansion dynamics
- Streamlit dashboard with multi-tab views and plan-level drilldown
