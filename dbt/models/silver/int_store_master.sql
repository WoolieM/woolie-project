{{
    config(
        materialized='incremental',
        unique_key=['store_code', 'valid_from'],
        primary_key = 'primary_key',
        incremental_strategy='merge',
        cluster_by=['store_code']
    )
}}

with source_data as (

    select
        CONCAT_WS(
            '-',
            store_code,
            valid_from
        ) AS primary_key,
        store_code,
        STRING(postcode) AS postcode,
        STRING(state) AS state_,
        open_date,
        STRING(phone_number) as phone_number,
        is_active,
        valid_from,
        valid_to
    from {{ ref('dumpy_store_master') }}

),

cleaned_data as (

    select
        *,
        -- Audit timestamp
        current_timestamp() as dbt_updated_at
    from source_data

)

SELECT
    * 
FROM
    cleaned_data

{% if is_incremental() %}
    WHERE valid_from >= (SELECT MAX(valid_from) FROM {{ this }})
       OR valid_to >= (SELECT MAX(valid_from) FROM {{ this }})
{% endif %}