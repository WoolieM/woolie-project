{{
    config(
        materialized='incremental',
        primary_key = 'primary_key',
        incremental_strategy='merge'
    )
}}


WITH today AS (
    SELECT
        store_code,
        STRING(postcode) AS postcode,
        STRING(state) AS state_,
        open_date,
        STRING(phone_number) as phone_number
    FROM
        {{ ref('dummpy_store_scd2') }}
    WHERE
        is_active IS TRUE
)

{% if is_incremental()%}
,
yesterday AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY
                store_code
            ORDER BY
                dbt_updated_at DESC
        ) AS row_id
    FROM
        {{this}}
)
{% endif %}

SELECT
    today.*,
    CONCAT_WS(
        '-',
        today.store_code,
        current_timestamp()
    ) AS primary_key,
    current_timestamp AS valid_from,
    current_timestamp() AS dbt_updated_at
FROM
    today
{%if is_incremental()%}

LEFT JOIN
    yesterday
ON
    today.store_code = yesterday.store_code
AND
    yesterday.row_id = 1
WHERE
    --New Data
    yesterday.store_code IS NULL
OR
    today.postcode <> yesterday.postcode
OR
    today.state_ <> yesterday.state_
OR
    today.open_date <> yesterday.open_date
OR
    today.phone_number <> yesterday.phone_number

{% endif %}