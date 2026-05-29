-- County-level cross-section joining annual pollution exposure, demographics and
-- respiratory-health prevalence. This is the training table for the asthma-
-- prevalence regression model (one row per county).
with county as (
    select * from {{ ref('stg_county_annual') }}
)
select
    county_fips,
    state,
    avg_pm25,
    avg_no2,
    median_income,
    median_age,
    pop_density,
    -- engineered features the regression consumes
    (75000 - median_income) / 75000.0 as income_deprivation_index,
    ln(pop_density)                    as log_pop_density,
    asthma_prevalence_pct,
    copd_prevalence_pct
from county
