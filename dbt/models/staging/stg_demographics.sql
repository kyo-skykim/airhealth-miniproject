with src as (
    select * from {{ source('raw', 'demographics') }}
)
select
    cast(county_fips as varchar)   as county_fips,
    cast(population as bigint)      as population,
    cast(median_age as double)     as median_age,
    cast(median_income as double)  as median_income
from src
