{% snapshot snap_dummy_store %}

{{
    config(
        target_schema='bronze',
        unique_key='store_code',
        strategy='check',
        check_cols=[
            'postcode',
            'state_',
            'open_date',
            'phone_number'
        ]
    )
}}

SELECT
    store_code,
    postcode,
    state AS state_,
    open_date,
    phone_number
FROM 
    {{ ref('dummpy_store_scd2') }}
WHERE
    is_active IS true
{% endsnapshot %}