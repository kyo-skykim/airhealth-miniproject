"""AirHealth Streamlit dashboard (the Data Analysis layer).

Reads the GOLD Delta tables (+ DS prediction tables) from Databricks via the
Databricks SQL connector and presents:
  * daily PM2.5 trends and AQI category mix per metro
  * weather vs. air-quality relationships
  * the county-level asthma vs. pollution cross-section
  * model results (forecast actual-vs-predicted, regression drivers)

Connects with env vars DATABRICKS_HOST / DATABRICKS_HTTP_PATH / DATABRICKS_TOKEN.
(Can also be hosted on Databricks Apps.)  Run:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import streamlit as st

from ingestion.common.config import settings

st.set_page_config(page_title="AirHealth", layout="wide")

GOLD = f"{settings.dbx_catalog}.{settings.dbx_gold_schema}"


def _query(sql: str) -> pd.DataFrame:
    from databricks import sql

    with sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"].replace("https://", ""),
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
    ) as conn, conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall_arrow().to_pandas()


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return _query(f"SELECT * FROM {GOLD}.{name}")


def table_exists(name: str) -> bool:
    df = _query(
        f"SELECT 1 FROM {settings.dbx_catalog}.information_schema.tables "
        f"WHERE table_schema='{settings.dbx_gold_schema}' AND table_name='{name}'"
    )
    return not df.empty


st.title("🌬️ AirHealth — Air Quality & Respiratory Health")
st.caption("Public-health/climate analytics platform · Databricks (Delta) + dbt + scikit-learn")

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
