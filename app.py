import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="SaaS Cohort Retention",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent
TEAL, ORANGE, NAVY, YELLOW, GRAY = "#2a9d8f","#e76f51","#264653","#e9c46a","#8d9db6"
PLAN_COLORS = {"starter": YELLOW, "pro": TEAL, "enterprise": NAVY}
MRR_MAP     = {"starter": 29, "pro": 79, "enterprise": 199}


@st.cache_data
def load():
    cust   = pd.read_csv(ROOT/"data"/"customers.csv")
    events = pd.read_csv(ROOT/"data"/"subscription_events.csv")

    # Cohort table
    active = events[events["event"].isin(["active","expansion","new"])].copy()
    active = active.merge(cust[["customer_id","acquisition_month"]], on="customer_id")

    def ci(row):
        acq = pd.Period(row["acquisition_month"],"M")
        cur = pd.Period(row["month"],"M")
        return (cur - acq).n

    active["cohort_index"] = active.apply(ci, axis=1)
    ct = (active.groupby(["acquisition_month","cohort_index"])["customer_id"]
          .nunique().reset_index())
    pivot = ct.pivot(index="acquisition_month", columns="cohort_index", values="customer_id")
    sizes = pivot[0]
    logo_ret = pivot.divide(sizes, axis=0).mul(100)

    # Monthly MRR waterfall
    wf = (events.groupby(["month","event"])["mrr"].sum()
          .reset_index().pivot(index="month", columns="event", values="mrr").fillna(0))

    # NRR
    active_mrr = wf.get("active",0) + wf.get("expansion",0) + wf.get("new",0)
    new_mrr    = wf.get("new",0)
    existing   = active_mrr - new_mrr
    ending     = existing + wf.get("expansion",0) + wf.get("churn",0) + wf.get("contraction",0)
    nrr        = (ending / existing.shift(1) * 100).clip(70, 140)

    return cust, events, logo_ret, wf, active_mrr, nrr


cust, events, logo_ret, wf, active_mrr, nrr = load()

with st.sidebar:
    st.markdown("## 📈 SaaS Retention")
    st.caption("B2B SaaS · 3 plans · 24 months · 1 600 customers")
    st.divider()
    page = st.radio("Go to",
        ["Overview","Cohort Heatmap","MRR Waterfall","Plan Analysis"],
        label_visibility="collapsed")
    st.divider()
    st.caption("Stack: Python · SQL · Streamlit · Plotly")


# ── OVERVIEW ─────────────────────────────────────────────────────────────────
if page == "Overview":
    st.header("SaaS Retention Overview")

    last_month = events["month"].max()
    active_last = events[(events["month"]==last_month) &
                         events["event"].isin(["active","expansion"])]["customer_id"].nunique()
    mrr_last    = active_mrr.iloc[-1]
    avg_nrr     = nrr.mean()
    total_churn = events[events["event"]=="churn"]["customer_id"].nunique()
    churn_rate  = total_churn / len(cust) * 100

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Active Customers",  f"{active_last:,}")
    c2.metric("MRR",               f"${mrr_last:,.0f}")
    c3.metric("Total Acquired",    f"{len(cust):,}")
    c4.metric("Avg NRR",           f"{avg_nrr:.1f}%")
    c5.metric("Cumulative Churn",  f"{churn_rate:.1f}%")

    st.divider()
    l, r = st.columns(2)

    with l:
        st.subheader("MRR Growth")
        fig = px.area(x=active_mrr.index, y=active_mrr.values,
                      labels={"x":"","y":"MRR ($)"},
                      color_discrete_sequence=[TEAL])
        fig.update_traces(line_width=2, fillcolor="rgba(42,157,143,0.15)")
        fig.update_layout(margin=dict(l=0,r=0,t=20,b=0),
                          yaxis_tickprefix="$", yaxis_tickformat=",")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    with r:
        st.subheader("Net Revenue Retention")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=nrr.index, y=nrr.values,
                                 line=dict(color=NAVY, width=2.5),
                                 mode="lines+markers", marker_size=5))
        fig.add_hline(y=100, line_dash="dash", line_color=TEAL,
                      annotation_text="100% baseline")
        fig.add_hline(y=110, line_dash="dot", line_color=GRAY,
                      annotation_text="World-class 110%")
        fig.update_layout(yaxis_range=[75, 125], yaxis_ticksuffix="%",
                          margin=dict(l=0,r=0,t=20,b=0))
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Customers by Plan")
    plan_dist = cust["plan"].value_counts().reset_index()
    plan_dist.columns = ["plan","count"]
    fig = px.pie(plan_dist, names="plan", values="count", hole=0.5,
                 color="plan", color_discrete_map=PLAN_COLORS)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=10,b=0), height=280)
    st.plotly_chart(fig, use_container_width=True)


# ── COHORT HEATMAP ───────────────────────────────────────────────────────────
elif page == "Cohort Heatmap":
    st.header("Cohort Retention Heatmap")

    tab1, tab2 = st.tabs(["Logo Retention (%)", "Avg Retention Curve"])

    with tab1:
        heat_data = logo_ret.iloc[:, :13].round(1)
        fig = px.imshow(
            heat_data,
            text_auto=".0f",
            color_continuous_scale="RdYlGn",
            zmin=0, zmax=100,
            labels={"x":"Months Since Acquisition","y":"Cohort","color":"Retention %"},
            aspect="auto",
        )
        fig.update_layout(height=580, margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Green = high retention · Red = high churn · Row 0 always 100% (cohort size)")

    with tab2:
        avg = logo_ret.mean().dropna()
        fig = go.Figure()
        for cohort in logo_ret.index[:12]:
            row = logo_ret.loc[cohort].dropna()
            fig.add_trace(go.Scatter(x=row.index, y=row.values,
                                     mode="lines", opacity=0.2,
                                     line=dict(color=NAVY, width=1),
                                     showlegend=False))
        fig.add_trace(go.Scatter(x=avg.index, y=avg.values, name="Average",
                                  line=dict(color=TEAL, width=3),
                                  mode="lines+markers"))
        fig.update_layout(
            xaxis_title="Months Since Acquisition",
            yaxis_title="Retention (%)",
            yaxis_ticksuffix="%",
            margin=dict(l=0,r=0,t=30,b=0),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Average Retention by Month")
        avg_df = avg.reset_index()
        avg_df.columns = ["Month","Avg Retention (%)"]
        avg_df["Avg Retention (%)"] = avg_df["Avg Retention (%)"].round(1)
        st.dataframe(avg_df, use_container_width=True, hide_index=True)


# ── MRR WATERFALL ────────────────────────────────────────────────────────────
elif page == "MRR Waterfall":
    st.header("MRR Waterfall")

    new_v = wf.get("new",   pd.Series(0, index=wf.index))
    exp_v = wf.get("expansion", pd.Series(0, index=wf.index))
    chu_v = wf.get("churn", pd.Series(0, index=wf.index))
    con_v = wf.get("contraction", pd.Series(0, index=wf.index))

    fig = go.Figure()
    fig.add_bar(x=wf.index, y=new_v, name="New MRR",       marker_color=TEAL)
    fig.add_bar(x=wf.index, y=exp_v, name="Expansion MRR", marker_color=NAVY)
    fig.add_bar(x=wf.index, y=chu_v, name="Churned MRR",   marker_color=ORANGE)
    fig.add_bar(x=wf.index, y=con_v, name="Contraction",   marker_color=YELLOW)
    fig.update_layout(
        barmode="relative",
        xaxis_tickangle=45,
        yaxis_tickprefix="$", yaxis_tickformat=",",
        yaxis_title="MRR Change ($)",
        margin=dict(l=0,r=0,t=30,b=0),
        height=440,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total New MRR",       f"+${new_v.sum():,.0f}")
    c2.metric("Total Expansion MRR", f"+${exp_v.sum():,.0f}")
    c3.metric("Total Churned MRR",   f"-${abs(chu_v.sum()):,.0f}")
    c4.metric("Net MRR Change",      f"${(new_v+exp_v+chu_v+con_v).sum():,.0f}")

    st.divider()
    st.subheader("Cumulative MRR")
    fig2 = px.line(x=active_mrr.index, y=active_mrr.values,
                   labels={"x":"","y":"MRR ($)"},
                   color_discrete_sequence=[NAVY])
    fig2.update_traces(line_width=2.5)
    fig2.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",",
                       margin=dict(l=0,r=0,t=20,b=0))
    fig2.update_xaxes(tickangle=45)
    st.plotly_chart(fig2, use_container_width=True)


# ── PLAN ANALYSIS ─────────────────────────────────────────────────────────────
elif page == "Plan Analysis":
    st.header("Retention by Plan")

    l, r = st.columns(2)

    with l:
        st.subheader("Churn Rate by Plan")
        churned = events[events["event"]=="churn"].merge(
            cust[["customer_id","plan"]], on="customer_id")
        plan_stats = (cust.groupby("plan").size().rename("total")
                      .reset_index()
                      .merge(churned.groupby("plan")["customer_id"].nunique()
                             .rename("churned").reset_index(), on="plan", how="left")
                      .fillna(0))
        plan_stats["churn_pct"] = plan_stats["churned"] / plan_stats["total"] * 100
        plan_stats = plan_stats.sort_values("churn_pct")
        fig = px.bar(plan_stats, x="churn_pct", y="plan", orientation="h",
                     color="plan", color_discrete_map=PLAN_COLORS,
                     labels={"churn_pct":"Cumulative Churn (%)","plan":""},
                     text=plan_stats["churn_pct"].round(1).astype(str)+"%")
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with r:
        st.subheader("MRR Contribution by Plan")
        plan_mrr = (events[events["event"].isin(["active","expansion"])]
                    .merge(cust[["customer_id","plan"]], on="customer_id")
                    .groupby(["month","plan"])["mrr"].sum().reset_index())
        fig = px.area(plan_mrr, x="month", y="mrr", color="plan",
                      color_discrete_map=PLAN_COLORS,
                      labels={"month":"","mrr":"MRR ($)","plan":""},
                      line_group="plan")
        fig.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",",
                          margin=dict(l=0,r=0,t=20,b=0))
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Retention by Acquisition Channel")
    ch_stats = (cust.groupby("channel").size().rename("total").reset_index()
                .merge(churned.groupby(
                    churned.merge(cust[["customer_id","channel"]], on="customer_id")
                    .groupby("channel")["customer_id"].nunique()
                    .rename("churned").reset_index()
                ), on="channel", how="left").fillna(0))
    ch_stats["retention"] = (1 - ch_stats["churned"]/ch_stats["total"]) * 100
    ch_stats = ch_stats.sort_values("retention", ascending=False)
    fig = px.bar(ch_stats,
                 x="channel", y="retention",
                 labels={"channel":"","retention":"24-Month Retention (%)"},
                 color_discrete_sequence=[TEAL],
                 text=ch_stats["retention"].round(1).astype(str)+"%")
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_range=[55, 80], margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "**Key insight:** Enterprise customers churn at ~18% over 24 months vs ~80% for Starter. "
        "Every Starter → Pro upgrade reduces churn risk by ~40% AND adds $50 MRR. "
        "Referral channel delivers the best long-term retention."
    )
