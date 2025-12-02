{{ config(materialized='table') }}

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2016-01-01' as date)",
        end_date="cast('2020-01-01' as date)"
    ) }}
),

final as (
    select
        date_day,
        extract(year from date_day) as year,
        extract(quarter from date_day) as quarter,
        extract(month from date_day) as month,
        extract(week from date_day) as week_of_year,
        extract(dayofweek from date_day) as day_of_week,
        format_date('%B', date_day) as month_name,
        format_date('%A', date_day) as day_name,
        case when extract(dayofweek from date_day) in (1, 7) then true else false end as is_weekend
    from date_spine
)

select * from final
