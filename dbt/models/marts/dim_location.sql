-- Location dimension: metro reference data enriched with county demographics.
with metros as (
    select * from {{ ref('metros') }}
),
demo as (
    select * from {{ ref('stg_demographics') }}
)
select
    m.metro_key,
    m.metro_name,
    m.state,
    m.lat,
    m.lon,
    m.county_fips,
    d.population,
    d.median_age,
    d.median_income
from metros m
left join demo d
    on m.county_fips = d.county_fips
