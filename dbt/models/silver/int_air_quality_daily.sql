-- Pivot the long air-quality table to one row per metro/day with a column per pollutant.
with aq as (
    select * from {{ ref('stg_air_quality') }}
)
select
    metro_key,
    observed_date,
    avg(case when parameter = 'pm25' then value end) as pm25,
    avg(case when parameter = 'pm10' then value end) as pm10,
    avg(case when parameter = 'no2'  then value end) as no2,
    avg(case when parameter = 'o3'   then value end) as o3
from aq
group by 1, 2
