with src as (
    select * from {{ source('raw', 'health') }}
)
select
    cast(county_fips as {{ dbt.type_string() }})        as county_fips,
    upper(cast(measure as {{ dbt.type_string() }}))     as measure,
    cast(prevalence_pct as {{ dbt.type_float() }})      as prevalence_pct
from src
