with products as (
    select * from {{ ref('stg_products') }}
),
translations as (
    select
        json_value(data, '$.product_category_name') as product_category_name,
        json_value(data, '$.product_category_name_english') as product_category_name_english
    from {{ source('olist_raw', 'raw_product_category_name_translation') }}
)
select
    p.product_id,
    coalesce(t.product_category_name_english, p.product_category_name) as category_name
from products p
left join translations t
    on p.product_category_name = t.product_category_name