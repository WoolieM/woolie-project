{{ config(
    materialized='incremental',
    unique_key='daily_summary_pk'
) }}

WITH silver_data AS (
    SELECT 
        *
    FROM 
        {{ ref('int_bitcoin_prices') }}
    
    {% if is_incremental() %}
    -- 1. Look back 1 day to catch late-arriving updates near midnight
    WHERE 
        DATE(event_time_aest) >= (
            SELECT 
                DATE_ADD(MAX(trade_date), -1) 
            FROM 
                {{ this }}
    )
    {% endif %}
),

daily_aggregates AS (
    SELECT
        -- 2. Group by the localized Melbourne date
        DATE(event_time_aest) AS trade_date,
        asset,
        currency,
        
        -- 3. Calculate core financial metrics
        MIN(price) AS daily_low,
        MAX(price) AS daily_high,
        AVG(price) AS daily_avg,
        
        -- 4. Databricks Superpower: Get the exact Open and Close prices
        MIN_BY(price, event_time_aest) AS daily_open,
        MAX_BY(price, event_time_aest) AS daily_close,
        
        -- Since CoinGecko volume is a rolling 24h metric, we take the peak of the day
        MAX(volume) AS peak_24h_volume,
        
        -- Keep track of how many API pings made up this day's data
        COUNT(message_id) AS tick_count
    FROM silver_data
    GROUP BY 
        1, 2, 3
)

SELECT
    -- 5. Generate a clean Primary Key for the Gold table
    {{ dbt_utils.generate_surrogate_key(['trade_date', 'asset', 'currency']) }} AS daily_summary_pk,
    trade_date,
    asset,
    currency,
    daily_open,
    daily_high,
    daily_low,
    daily_close,
    daily_avg,
    peak_24h_volume,
    tick_count,
    CURRENT_TIMESTAMP() AS _transformed_at_utc
FROM daily_aggregates