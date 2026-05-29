with src as (
    select * from {{ source('bronze', 'demographics') }}
)
select
    cast(county_fips as {{ dbt.type_string() }})   as county_fips,
    cast(population as {{ dbt.type_bigint() }})     as population,
    cast(median_age as {{ dbt.type_float() }})      as median_age,
    cast(median_income as {{ dbt.type_float() }})   as median_income
from src
