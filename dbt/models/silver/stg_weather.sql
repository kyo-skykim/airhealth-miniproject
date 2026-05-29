with src as (
    select * from {{ source('bronze', 'weather') }}
)
select
    cast(metro_key as {{ dbt.type_string() }}) as metro_key,
    cast(date as date)                         as observed_date,
    cast(temp_c as {{ dbt.type_float() }})     as temp_c,
    cast(humidity_pct as {{ dbt.type_float() }}) as humidity_pct,
    cast(wind_kph as {{ dbt.type_float() }})   as wind_kph,
    cast(precip_mm as {{ dbt.type_float() }})  as precip_mm
from src
