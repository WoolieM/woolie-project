{{
    config(
        unique_key = 'message_id'
    )
}}

WITH source AS (
    SELECT
        message_id,
        raw_payload,
        _ingested_at
    FROM
        {{ source('bronze', 'bitcoin_prices') }}
    {% if is_incremental() %}
    WHERE   
        _ingested_at > (SELECT MAX(_ingested_at) FROM {{ this }})
    {% endif %}
),

parsed_json AS (
    SELECT
        message_id,
        from_json(raw_payload, 'data STRUCT<asset: STRING, price_aud: DOUBLE, price_usd: DOUBLE, volume_aud: DOUBLE, volume_usd: DOUBLE, source_timestamp: LONG>') AS parsed,
        _ingested_at
    FROM
        source
)

SELECT
    *
FROM
    parsed_json

