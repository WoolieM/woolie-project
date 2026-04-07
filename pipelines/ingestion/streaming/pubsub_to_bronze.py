import os, json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp
from databricks.sdk.runtime import dbutils

import os
from pyspark.sql import SparkSession

def get_spark():
    """Smart Detection: Local (Connect) vs Cloud (Native)"""
    
    # Databricks always sets this variable when running natively in the cloud
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        print("☁️ Running natively in Databricks Cloud")
        return SparkSession.builder.getOrCreate()
    else:
        print("🔌 Running locally via Databricks Connect")
        from databricks.connect import DatabricksSession
        # Use .serverless() when bridging from local VM
        return DatabricksSession.builder.serverless().getOrCreate()

def run_ingestion():
    spark = get_spark()
    env = os.getenv("DATABRICKS_BUNDLE_TARGET", "dev")

    print(f"🚀 Starting Ingestion for environment: {env}")

    # 2. GCP Identity
    gcp_json_key = dbutils.secrets.get(scope="gcp-auth", key="databricks-workspace-sa-json")
    gcp_auth = json.loads(gcp_json_key)

    # 4. Read Stream
    df_raw = (
        spark.readStream
        .format("pubsub")
        .option("projectId", "woolie-project")
        .option("subscriptionId", "bitcoin-price-sub")
        .option("topicId", "bitcoin-price-topic") 
        .option("clientEmail", gcp_auth["client_email"])
        .option("clientId", gcp_auth["client_id"])
        .option("privateKey", gcp_auth["private_key"])
        .option("privateKeyId", gcp_auth["private_key_id"])
        .load()
    )

    # 5. Transform
    df_bronze = (
        df_raw
        .select(
            col("messageId").alias("message_id"),
            col("payload").cast("string").alias("raw_payload"),
            col("publishTimestampInMillis").cast("timestamp").alias("source_published_at"),
            current_timestamp().alias("_ingested_at")
        )
    )

    # 6. Write Stream
    checkpoint_path = f"/Volumes/{env}/bronze/checkpoints/bitcoin_prices"
    table_name = f"{env}.bronze.bitcoin_prices"

    query = (
        df_bronze.writeStream
        .format("delta")
        .outputMode("append")
        .trigger(availableNow=True) # "Sips" all available data and stops
        .option("checkpointLocation", checkpoint_path)
        .toTable(table_name)
    )

    query.awaitTermination()
    print("✅ Ingestion complete.")

# --- THE SENIOR ENTRY POINT ---
if __name__ == "__main__":
    run_ingestion()