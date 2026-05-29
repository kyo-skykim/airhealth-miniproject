with src as (
    select * from {{ source('raw', 'air_quality') }}
)
select
    cast(metro_key as {{ dbt.type_string() }})   as metro_key,
    cast(date as date)                            as observed_date,
    lower(cast(parameter as {{ dbt.type_string() }})) as parameter,
    cast(value as {{ dbt.type_float() }})         as value,
    cast(unit as {{ dbt.type_string() }})         as unit
from src
where value is not null
