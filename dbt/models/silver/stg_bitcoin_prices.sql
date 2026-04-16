{{
    config(
        materialized = 'incremental',
        unique_key = 'primary_key',
        incremental_strategy = 'merge'
    )
}}

WITH source AS (
    SELECT
        message_id,
        raw_payload,
        _ingested_at AS _ingested_at_utc,
        ROW_NUMBER() OVER (
            PARTITION BY
                message_id
            ORDER BY
                _ingested_at DESC
        ) AS rn
    FROM
        {{ source('bronze', 'bitcoin_prices') }}
    {% if is_incremental() %}
    WHERE   
        _ingested_at > (SELECT MAX(_ingested_at_utc) FROM {{ this }})
    {% endif %}
),
parsed_json AS (
    SELECT
        message_id,
        FROM_JSON(
            raw_payload, 
            'data STRUCT<
                asset: STRING, 
                price_aud: DOUBLE, 
                price_usd: DOUBLE, 
                volume_aud: DOUBLE, 
                volume_usd: DOUBLE, 
                source_timestamp: LONG
            >'
        ) AS parsed,
        _ingested_at_utc
    FROM
        source
    WHERE
        rn = 1
),
unpivoted AS (
    SELECT
        message_id,
        _ingested_at_utc,
        parsed.data.asset,
        FROM_UTC_TIMESTAMP(
            TO_TIMESTAMP(parsed.data.source_timestamp),
            'Australia/Melbourne'
        ) AS event_time_aest,
        STACK(
            2,
            'AUD', parsed.data.price_aud, parsed.data.volume_aud,
            'USD', parsed.data.price_usd, parsed.data.volume_usd
        ) AS (currency, price, volume)
    FROM
        parsed_json
)

SELECT
    CONCAT(message_id, currency) AS primary_key,
    *
FROM
    unpivoted