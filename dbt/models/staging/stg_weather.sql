with src as (
    select * from {{ source('raw', 'weather') }}
)
select
    cast(metro_key as varchar) as metro_key,
    cast(date as date)         as observed_date,
    cast(temp_c as double)     as temp_c,
    cast(humidity_pct as double) as humidity_pct,
    cast(wind_kph as double)   as wind_kph,
    cast(precip_mm as double)  as precip_mm
from src
