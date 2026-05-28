-- Date dimension derived from the observed date range in the daily fact.
with dates as (
    select distinct observed_date as date_day
    from {{ ref('int_daily_metrics') }}
)
select
    date_day,
    extract(year   from date_day)  as year,
    extract(month  from date_day)  as month,
    extract(day    from date_day)  as day_of_month,
    extract(dow    from date_day)  as day_of_week,
    extract(doy    from date_day)  as day_of_year,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend,
    case
        when extract(month from date_day) in (12, 1, 2)  then 'winter'
        when extract(month from date_day) in (3, 4, 5)   then 'spring'
        when extract(month from date_day) in (6, 7, 8)   then 'summer'
        else 'fall'
    end as season
from dates
