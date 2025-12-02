with source as (
    select * from {{ source('raw', 'order_payments_raw') }}
),

cleaned as (
    select
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        cast(payment_value as float64) as payment_value
    from source
)

select * from cleaned
