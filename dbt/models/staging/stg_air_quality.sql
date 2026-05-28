with src as (
    select * from {{ source('raw', 'air_quality') }}
)
select
    cast(metro_key as varchar)   as metro_key,
    cast(date as date)           as observed_date,
    lower(cast(parameter as varchar)) as parameter,
    cast(value as double)        as value,
    cast(unit as varchar)        as unit
from src
where value is not null
