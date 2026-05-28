"""AirHealth Streamlit dashboard (the Data Analysis layer).

Reads the dbt marts + DS prediction tables from the warehouse and presents:
  * daily PM2.5 trends and AQI category mix per metro
  * weather vs. air-quality relationships
  * the county-level asthma vs. pollution cross-section
  * model results (forecast actual-vs-predicted, regression drivers)

Run:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from ingestion.common.config import settings

st.set_page_config(page_title="AirHealth", layout="wide")


@st.cache_data
def load(name: str) -> pd.DataFrame:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        return con.execute(f"SELECT * FROM analytics.{name}").df()
    finally:
        con.close()


def table_exists(name: str) -> bool:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    try:
        rows = con.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='analytics' AND table_name=?",
            [name],
        ).fetchall()
        return bool(rows)
    finally:
        con.close()


st.title("🌬️ AirHealth — Air Quality & Respiratory Health")
st.caption("Public-health/climate analytics platform · DuckDB + dbt + scikit-learn")

fact = load("fact_air_quality_daily")
fact["observed_date"] = pd.to_datetime(fact["observed_date"])
loc = load("dim_location")
health = load("mart_health_air_quality")

metros = sorted(fact["metro_key"].unique())
sel = st.sidebar.multiselect("Metros", metros, default=metros)
fdf = fact[fact["metro_key"].isin(sel)]

c1, c2, c3 = st.columns(3)
c1.metric("Avg PM2.5 (µg/m³)", f"{fdf['pm25'].mean():.1f}")
c2.metric("Days observed", f"{fdf['observed_date'].nunique()}")
c3.metric("Counties (health model)", f"{health['county_fips'].nunique()}")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Air quality trends", "🌡️ Weather vs AQ", "🫁 Health cross-section", "🤖 Model results"]
)

with tab1:
    st.subheader("Daily PM2.5 by metro")
    fig = px.line(fdf, x="observed_date", y="pm25", color="metro_key")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("AQI category mix")
    mix = fdf.groupby(["metro_key", "pm25_aqi_category"]).size().reset_index(name="days")
    st.plotly_chart(px.bar(mix, x="metro_key", y="days", color="pm25_aqi_category"), use_container_width=True)

with tab2:
    st.subheader("Temperature vs PM2.5")
    st.plotly_chart(
        px.scatter(fdf, x="temp_c", y="pm25", color="metro_key", trendline="ols", opacity=0.5),
        use_container_width=True,
    )

with tab3:
    st.subheader("County asthma prevalence vs PM2.5 exposure")
    st.plotly_chart(
        px.scatter(
            health, x="avg_pm25", y="asthma_prevalence_pct",
            size="pop_density", color="median_income",
            color_continuous_scale="Viridis", trendline="ols",
            labels={"avg_pm25": "Avg PM2.5 (µg/m³)", "asthma_prevalence_pct": "Asthma prevalence (%)"},
        ),
        use_container_width=True,
    )

with tab4:
    if table_exists("mart_pm25_forecast"):
        fc = load("mart_pm25_forecast")
        fc["observed_date"] = pd.to_datetime(fc["observed_date"])
        fc = fc[fc["metro_key"].isin(sel)]
        st.subheader("PM2.5 forecast — actual vs predicted (hold-out)")
        long = fc.melt(
            id_vars=["metro_key", "observed_date"],
            value_vars=["pm25_actual", "pm25_predicted"],
            var_name="series", value_name="pm25",
        )
        st.plotly_chart(px.line(long, x="observed_date", y="pm25", color="series", facet_row="metro_key", height=900), use_container_width=True)
    else:
        st.info("Run `python -m ds.run_models` to populate model predictions.")

    if table_exists("mart_asthma_predictions"):
        ap = load("mart_asthma_predictions")
        st.subheader("Asthma regression — predicted vs actual (cross-validated)")
        st.plotly_chart(
            px.scatter(ap, x="asthma_actual", y="asthma_predicted", color="state", trendline="ols"),
            use_container_width=True,
        )
