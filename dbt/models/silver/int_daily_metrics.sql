-- Align air quality and weather onto the metro/day grain (the time-series spine).
with aq as (
    select * from {{ ref('int_air_quality_daily') }}
),
wx as (
    select * from {{ ref('stg_weather') }}
)
select
    aq.metro_key,
    aq.observed_date,
    aq.pm25,
    aq.pm10,
    aq.no2,
    aq.o3,
    wx.temp_c,
    wx.humidity_pct,
    wx.wind_kph,
    wx.precip_mm
from aq
left join wx
    on aq.metro_key = wx.metro_key
   and aq.observed_date = wx.observed_date
