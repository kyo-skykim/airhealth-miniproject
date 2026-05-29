-- Grain: one row per metro per day. The central fact for time-series analysis
-- and the source for the PM2.5 forecasting model.
with metrics as (
    select * from {{ ref('int_daily_metrics') }}
)
select
    {{ surrogate_key(['metro_key', 'observed_date']) }} as air_quality_key,
    metro_key,
    observed_date,
    pm25,
    pm10,
    no2,
    o3,
    temp_c,
    humidity_pct,
    wind_kph,
    precip_mm,
    -- US EPA AQI category for PM2.5 (24h), useful for the dashboard.
    case
        when pm25 <= 12.0  then 'Good'
        when pm25 <= 35.4  then 'Moderate'
        when pm25 <= 55.4  then 'Unhealthy (Sensitive)'
        when pm25 <= 150.4 then 'Unhealthy'
        else 'Very Unhealthy'
    end as pm25_aqi_category
from metrics
