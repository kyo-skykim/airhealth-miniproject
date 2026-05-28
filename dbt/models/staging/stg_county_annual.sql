with src as (
    select * from {{ source('raw', 'county_annual') }}
)
select
    cast(county_fips as varchar)            as county_fips,
    cast(state as varchar)                  as state,
    cast(avg_pm25 as double)                as avg_pm25,
    cast(avg_no2 as double)                 as avg_no2,
    cast(median_income as double)           as median_income,
    cast(median_age as double)              as median_age,
    cast(pop_density as double)             as pop_density,
    cast(asthma_prevalence_pct as double)   as asthma_prevalence_pct,
    cast(copd_prevalence_pct as double)     as copd_prevalence_pct
from src
