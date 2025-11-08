# app.py
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import chardet

# ==========================================
# PAGE CONFIG & CLEAN LAYOUT STYLING
# ==========================================
st.set_page_config(page_title="EV Growth — Oil Demand — Air Pollution", layout="wide")

st.markdown("""
    <style>
    /* Remove white margins (top/left/right) */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #e6f2ff !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stHeader"] {
        display: none; /* Removes Streamlit top white bar */
    }
    .block-container {
        padding-top: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
    }
    [data-testid="stSidebar"] {
        background-color: #f2f6fa !important;
    }
    h1, h2, h3 {
        color: #08306B;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# LOAD CSV FILE
# ==========================================
file_name = "ev_oil_pollution_region.csv"
if not os.path.exists(file_name):
    st.error("❌ CSV file not found! Please place 'ev_oil_pollution_region.csv' in the same directory.")
    st.stop()

with open(file_name, "rb") as f:
    enc = chardet.detect(f.read())["encoding"] or "utf-8"
df = pd.read_csv(file_name, encoding=enc)
df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

mapping = {
    "year": "Year", "month": "Month", "region": "Region",
    "ev_share_pct": "EV_Share_pct", "oil_demand_mbd": "Oil_Demand_mbd",
    "global_pm25_ug_m3": "Global_PM25_ug_m3"
}
for c in df.columns:
    if c.lower() in mapping:
        df.rename(columns={c: mapping[c.lower()]}, inplace=True)

df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
df["Month"] = pd.to_numeric(df["Month"], errors="coerce").astype("Int64")
df["Region"] = df["Region"].astype(str).str.strip()
for c in ["EV_Share_pct", "Oil_Demand_mbd", "Global_PM25_ug_m3"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# ==========================================
# MEDIUM HEIGHT HEADER BAR
# ==========================================
st.markdown("""
    <style>
        .main > div:first-child {
            padding-top: 0rem !important;
        }
    </style>

    <div style="
        background: linear-gradient(90deg, #00b4db, #0083b0);
        padding: 16px 0;            /* medium height */
        text-align: center;
        color: white;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        margin-bottom: 0;
    ">
        <h1 style="margin:0;font-size:28px;">🌍 EV Growth — Oil Demand — Air Pollution Dashboard</h1>
        <p style="margin:4px 0 0 0;font-size:16px;">
            🎯 Aim: Analyzing the relationship between EV growth, oil demand, and global pollution trends over time.
        </p>
    </div>
""", unsafe_allow_html=True)



# ==========================================
# SIDEBAR CONTROLS
# ==========================================
st.sidebar.header("⚙️ Visualization Controls")

years = sorted(df["Year"].dropna().unique())
regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
metrics_available = ["EV_Share_pct", "Oil_Demand_mbd", "Global_PM25_ug_m3"]

year_sel = st.sidebar.selectbox("Select Year", years, index=0)
region_sel = st.sidebar.selectbox("Select Region", regions, index=0)
metrics_sel = st.sidebar.multiselect("Select Metrics", metrics_available, default=["EV_Share_pct"])

chart_type = st.sidebar.selectbox("Chart Type", ["Line", "Bar", "Area", "Scatter", "Pie", "Heatmap"])
show_data = st.sidebar.checkbox("Show Filtered Dataset")
generate = st.sidebar.button("🚀 Generate Visualization")

# ==========================================
# FILTER DATA
# ==========================================
df_filtered = df[df["Year"] == year_sel]
if region_sel != "All":
    df_filtered = df_filtered[df_filtered["Region"] == region_sel]

if df_filtered.empty:
    st.warning("No data for this selection.")
    st.stop()

# ==========================================
# GENERATE VISUALIZATION
# ==========================================
if generate:

    # METRICS
    col1, col2, col3 = st.columns(3)
    col1.metric("EV Share (avg)", f"{df_filtered['EV_Share_pct'].mean():.2f}%")
    col2.metric("Oil Demand (avg Mb/d)", f"{df_filtered['Oil_Demand_mbd'].mean():.2f}")
    col3.metric("PM2.5 (avg µg/m³)", f"{df_filtered['Global_PM25_ug_m3'].mean():.2f}")

    st.markdown("---")

    for metric in metrics_sel:
        st.markdown(f"### 📊 {chart_type} Chart — {metric} ({year_sel})")

        fig = None
        if chart_type == "Line":
            fig = px.line(df_filtered.sort_values("Month"), x="Month", y=metric, color="Region", markers=True)
        elif chart_type == "Bar":
            fig = px.bar(df_filtered, x="Region", y=metric, color="Region", barmode="group")
        elif chart_type == "Area":
            fig = px.area(df_filtered.sort_values("Month"), x="Month", y=metric, color="Region")
        elif chart_type == "Scatter":
            fig = px.scatter(df_filtered, x="Month", y=metric, size=metric, color="Region")
        elif chart_type == "Pie":
            avg = df_filtered.groupby("Region")[[metric]].mean().reset_index()
            fig = px.pie(avg, names="Region", values=metric, title=f"{metric} by Region")
        elif chart_type == "Heatmap":
            corr = df_filtered.select_dtypes(include="number").corr()
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
            st.pyplot(fig)
            fig = None

        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # INSIGHTS
    # ==========================================
    st.markdown("### 🔍 Insights")

    ev_avg = df_filtered["EV_Share_pct"].mean()
    oil_avg = df_filtered["Oil_Demand_mbd"].mean()
    pm_avg = df_filtered["Global_PM25_ug_m3"].mean()

    insights = []
    if ev_avg > 10:
        insights.append("⚡ EV adoption is showing strong growth.")
    else:
        insights.append("🚗 EV growth remains gradual.")
    if oil_avg > 70:
        insights.append("🛢️ Oil demand is still high, reflecting fossil dependency.")
    else:
        insights.append("⬇️ Oil demand is declining, possibly due to EV adoption.")
    if pm_avg > 25:
        insights.append("🌫️ Air pollution levels remain high — cleaner transition needed.")
    else:
        insights.append("🌤️ Air quality is improving steadily.")

    st.markdown(
        f"<div style='background:#DCEEFB;padding:12px;border-radius:10px;'>{'<br>'.join(insights)}</div>",
        unsafe_allow_html=True
    )

    if show_data:
        st.markdown("### 📄 Filtered Dataset")
        st.dataframe(df_filtered)
