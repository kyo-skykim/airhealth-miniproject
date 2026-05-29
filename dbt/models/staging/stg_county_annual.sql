with src as (
    select * from {{ source('raw', 'county_annual') }}
)
select
    cast(county_fips as {{ dbt.type_string() }})            as county_fips,
    cast(state as {{ dbt.type_string() }})                  as state,
    cast(avg_pm25 as {{ dbt.type_float() }})                as avg_pm25,
    cast(avg_no2 as {{ dbt.type_float() }})                 as avg_no2,
    cast(median_income as {{ dbt.type_float() }})           as median_income,
    cast(median_age as {{ dbt.type_float() }})              as median_age,
    cast(pop_density as {{ dbt.type_float() }})             as pop_density,
    cast(asthma_prevalence_pct as {{ dbt.type_float() }})   as asthma_prevalence_pct,
    cast(copd_prevalence_pct as {{ dbt.type_float() }})     as copd_prevalence_pct
from src
