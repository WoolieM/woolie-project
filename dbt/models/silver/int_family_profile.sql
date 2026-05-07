{{
    config(
        materialized = 'incremental',
        unique_key = 'primary_key',
        incremental_strategy = 'merge'
    )
}}

WITH source AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY
                profile,
                sub_category
            ORDER BY
                DOUBLE(_dlt_load_id) DESC
        ) AS rn
    FROM
        {{ source('bronze', 'family_profile') }}
    {% if is_incremental() %}
    WHERE   
        DOUBLE(_dlt_load_id) >= (SELECT MAX(_dlt_load_unix_time) FROM {{ this }})
    {% endif %}
),
deduplicated AS (
    SELECT 
        CONCAT_WS('-', profile, sub_category) AS primary_key,
        profile,
        INT(census_year) AS census_year,
        category,
        sub_category,
        sub_order,
        value AS value_,
        DOUBLE(_dlt_load_id) AS _dlt_load_unix_time,
        DATE_FORMAT(
            FROM_UTC_TIMESTAMP(
                TIMESTAMP_SECONDS(DOUBLE(_dlt_load_id)), 
                'Australia/Melbourne'
            ), 
            'yyyy-MM-dd HH:mm:ss'
        ) AS ingestion_datetime_aest
    FROM
        source
    WHERE
        rn = 1
)

SELECT
    *
FROM
    deduplicated