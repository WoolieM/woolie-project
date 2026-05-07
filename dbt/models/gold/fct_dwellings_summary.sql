{{ config(
    materialized='incremental',
    unique_key='daily_summary_pk'
) }}


SELECT 
    CONCAT_WS(
        '-',
        census_year,
        region,
        type_
    ) AS daily_summary_pk,
    census_year,
    region,
    type_,
    SUM(number_) AS total_sum,
    MAX(ingestion_datetime_aest) AS ingestion_datetime_aest
FROM 
    {{ ref('int_dwellings') }}
{% if is_incremental() %}
WHERE 
    DATE(ingestion_datetime_aest) >= (
        SELECT 
            DATE_SUB(MAX(ingestion_datetime_aest), 1) 
        FROM 
            {{ this }}
)
{% endif %}
GROUP BY ALL
