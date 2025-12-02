with source as (
    select * from {{ source('raw', 'sellers_raw') }}
),

cleaned as (
    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state
    from source
)

select * from cleaned
