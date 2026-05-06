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
                census_year,
                base_property_id
            ORDER BY
                DOUBLE(_dlt_load_id) DESC
        ) AS rn
    FROM
        {{ source('bronze', 'dwellings') }}
    {% if is_incremental() %}
    WHERE   
        CAST(_dlt_load_id AS DOUBLE) >= (SELECT MAX(_dlt_load_id_num) FROM {{ this }})
    {% endif %}
),
deduplicated AS (
    SELECT 
        CONCAT_WS('-', census_year, base_property_id) AS primary_key,
        INT(census_year) AS census_year,
        INT(block_id) AS block_id,
        INT(property_id) AS property_id,
        INT(base_property_id) AS base_property_id,
        building_address AS address_,
        clue_small_area AS region,
        dwelling_type AS type_,
        dwelling_number AS number_,
        longitude,
        latitude,
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