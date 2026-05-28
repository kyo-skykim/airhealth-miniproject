with src as (
    select * from {{ source('raw', 'health') }}
)
select
    cast(county_fips as varchar)     as county_fips,
    upper(cast(measure as varchar))  as measure,
    cast(prevalence_pct as double)   as prevalence_pct
from src
