-- Date dimension derived from the observed date range in the daily fact.
-- Date-part extraction differs per engine, so branch on the dbt target type:
--   * duckdb  : extract(dow|doy ...)  -> dow is 0=Sun..6=Sat
--   * bigquery: extract(dayofweek|dayofyear ...) -> dayofweek is 1=Sun..7=Sat
--   * spark/databricks: dayofweek()/dayofyear() -> dayofweek is 1=Sun..7=Sat
with dates as (
    select distinct observed_date as date_day
    from {{ ref('int_daily_metrics') }}
)
select
    date_day,
    extract(year  from date_day)  as year,
    extract(month from date_day)  as month,
    extract(day   from date_day)  as day_of_month,
{% if target.type == 'duckdb' %}
    extract(dow from date_day)    as day_of_week,
    extract(doy from date_day)    as day_of_year,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend,
{% elif target.type == 'bigquery' %}
    extract(dayofweek from date_day) as day_of_week,
    extract(dayofyear from date_day) as day_of_year,
    case when extract(dayofweek from date_day) in (1, 7) then true else false end as is_weekend,
{% else %}  {# spark / databricks #}
    dayofweek(date_day)           as day_of_week,
    dayofyear(date_day)           as day_of_year,
    case when dayofweek(date_day) in (1, 7) then true else false end as is_weekend,
{% endif %}
    case
        when extract(month from date_day) in (12, 1, 2)  then 'winter'
        when extract(month from date_day) in (3, 4, 5)   then 'spring'
        when extract(month from date_day) in (6, 7, 8)   then 'summer'
        else 'fall'
    end as season
from dates
