"""
Synthetic SaaS subscription dataset generator.

Scenario: B2B SaaS product with 3 pricing tiers.
Produces 2 CSV files used across all notebooks and the Streamlit app.

Run: python data/generate_saas_data.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)
OUT = Path(__file__).parent

# ── Plan configuration ────────────────────────────────────────────────────────
PLANS = {
    "starter":    {"mrr": 29,  "monthly_churn": 0.082, "expansion_prob": 0.04,
                   "expansion_to": "pro",     "weight": 0.58},
    "pro":        {"mrr": 79,  "monthly_churn": 0.048, "expansion_prob": 0.06,
                   "expansion_to": "enterprise", "weight": 0.32},
    "enterprise": {"mrr": 199, "monthly_churn": 0.018, "expansion_prob": 0.0,
                   "expansion_to": None,        "weight": 0.10},
}

CHANNELS = ["organic", "paid_search", "referral", "content"]
CHANNEL_W = [0.35, 0.30, 0.20, 0.15]

MONTHS = pd.date_range("2022-01-01", periods=24, freq="MS")

# Monthly new customer volume with growth trend + Q4 spike
BASE_NEW = 40
new_per_month = []
for i, m in enumerate(MONTHS):
    growth = BASE_NEW * (1.04 ** i)
    seasonal = 1.30 if m.month in (10, 11) else 0.85 if m.month in (1, 2) else 1.0
    n = int(growth * seasonal + np.random.normal(0, 3))
    new_per_month.append(max(n, 15))

# ── Generate customers ────────────────────────────────────────────────────────
customers = []
cid = 1000
for i, (m, n) in enumerate(zip(MONTHS, new_per_month)):
    plans_chosen = np.random.choice(
        list(PLANS), size=n,
        p=[PLANS[p]["weight"] for p in PLANS]
    )
    channels_chosen = np.random.choice(CHANNELS, size=n, p=CHANNEL_W)
    for plan, channel in zip(plans_chosen, channels_chosen):
        customers.append({
            "customer_id":        cid,
            "acquisition_month":  m.strftime("%Y-%m"),
            "plan":               plan,
            "channel":            channel,
        })
        cid += 1

cust_df = pd.DataFrame(customers)
cust_df.to_csv(OUT / "customers.csv", index=False)
print(f"customers.csv: {len(cust_df):,} rows")

# ── Generate monthly subscription events ─────────────────────────────────────
events = []
active = {}   # customer_id → {"plan": ..., "active": bool}

for m in MONTHS:
    # Onboard new customers this month
    new_this_month = cust_df[cust_df["acquisition_month"] == m.strftime("%Y-%m")]
    for _, row in new_this_month.iterrows():
        active[row["customer_id"]] = {"plan": row["plan"], "churned": False}
        events.append({
            "month":       m.strftime("%Y-%m"),
            "customer_id": row["customer_id"],
            "plan":        row["plan"],
            "event":       "new",
            "mrr":         PLANS[row["plan"]]["mrr"],
        })

    # Process existing active customers
    for cid_k, state in list(active.items()):
        if state["churned"]:
            continue
        plan = state["plan"]
        cfg  = PLANS[plan]

        # Skip customers who just joined this month (already recorded above)
        if cust_df[cust_df["customer_id"] == cid_k]["acquisition_month"].values[0] == m.strftime("%Y-%m"):
            continue

        # Churn
        if np.random.rand() < cfg["monthly_churn"]:
            active[cid_k]["churned"] = True
            events.append({
                "month":       m.strftime("%Y-%m"),
                "customer_id": cid_k,
                "plan":        plan,
                "event":       "churn",
                "mrr":         -cfg["mrr"],
            })
            continue

        # Expansion
        if cfg["expansion_to"] and np.random.rand() < cfg["expansion_prob"]:
            new_plan = cfg["expansion_to"]
            active[cid_k]["plan"] = new_plan
            mrr_delta = PLANS[new_plan]["mrr"] - cfg["mrr"]
            events.append({
                "month":       m.strftime("%Y-%m"),
                "customer_id": cid_k,
                "plan":        new_plan,
                "event":       "expansion",
                "mrr":         mrr_delta,
            })
            continue

        # Contraction (rare: 2% of Enterprise downgrade to Pro)
        if plan == "enterprise" and np.random.rand() < 0.015:
            new_plan = "pro"
            active[cid_k]["plan"] = new_plan
            mrr_delta = PLANS[new_plan]["mrr"] - cfg["mrr"]
            events.append({
                "month":       m.strftime("%Y-%m"),
                "customer_id": cid_k,
                "plan":        new_plan,
                "event":       "contraction",
                "mrr":         mrr_delta,
            })
            continue

        # Active (no change)
        events.append({
            "month":       m.strftime("%Y-%m"),
            "customer_id": cid_k,
            "plan":        plan,
            "event":       "active",
            "mrr":         PLANS[plan]["mrr"],
        })

ev_df = pd.DataFrame(events)
ev_df.to_csv(OUT / "subscription_events.csv", index=False)
print(f"subscription_events.csv: {len(ev_df):,} rows")

# ── Summary ───────────────────────────────────────────────────────────────────
last_month = MONTHS[-1].strftime("%Y-%m")
active_last = ev_df[(ev_df["month"]==last_month) & (ev_df["event"]=="active")]
mrr_last = ev_df[(ev_df["month"]==last_month) & ev_df["event"].isin(["active","expansion"])]["mrr"].sum()
total_churned = ev_df[ev_df["event"]=="churn"]["customer_id"].nunique()

print(f"\nActive customers (end): {len(active_last) + ev_df[(ev_df['month']==last_month)&(ev_df['event']=='expansion')].shape[0]:,}")
print(f"Total acquired:         {len(cust_df):,}")
print(f"Total churned:          {total_churned:,}")
print(f"MRR (last month):       ${mrr_last:,.0f}")

new_mrr = ev_df[ev_df["event"]=="new"]["mrr"].sum()
exp_mrr = ev_df[ev_df["event"]=="expansion"]["mrr"].sum()
churn_mrr = abs(ev_df[ev_df["event"]=="churn"]["mrr"].sum())
print(f"\n24-month cumulative:")
print(f"  New MRR       : +${new_mrr:,.0f}")
print(f"  Expansion MRR : +${exp_mrr:,.0f}")
print(f"  Churned MRR   : -${churn_mrr:,.0f}")
