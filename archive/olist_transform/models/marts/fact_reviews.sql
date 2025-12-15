select
    r.review_id,
    r.order_id,
    r.review_score,
    o.order_purchased_at,
    date_diff(o.order_delivered_at, o.order_purchased_at, DAY) as delivery_days
from {{ ref('stg_reviews') }} r
join {{ ref('stg_orders') }} o using (order_id)
where o.order_delivered_at is not null