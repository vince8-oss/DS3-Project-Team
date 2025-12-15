with source as (
    select * from {{ source('olist_raw', 'raw_products') }}
)
select
    json_value(data, '$.product_id') as product_id,
    json_value(data, '$.product_category_name') as product_category_name
from source