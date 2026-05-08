import json, sys
from pyspark.sql.functions import col, current_timestamp
from databricks.sdk.runtime import dbutils
import os


# Databricks spark_python_task does not define __file__ because it uses exec().
# However, the full path to this script is always passed as sys.argv[0].
script_path = __file__ if '__file__' in globals() else sys.argv[0]

current_dir = os.path.dirname(os.path.abspath(script_path))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))

# Add to Python path if it's not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from pipelines.ingestion.utils.utility import get_spark

def run_ingestion():
    spark = get_spark()
    
    env = sys.argv[1] if len(sys.argv) > 1 else "local_dev"

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
    checkpoint_path = f"gs://woolie-project-lakehouse/{env}/bronze/_checkpoints/bitcoin_prices"
    table_name = f"{env}.bronze.bitcoin_prices"

    # This ensures the DATA also lives in bucket, not just the checkpoint
    data_path = f"gs://woolie-project-lakehouse/{env}/bronze/bitcoin_prices"

    query = (
        df_bronze.writeStream
        .format("delta")
        .outputMode("append")
        .trigger(availableNow=True) # "Sips" all available data and stops
        .option("checkpointLocation", checkpoint_path)
        .option("path", data_path)
        .toTable(table_name)
    )

    query.awaitTermination()
    print("✅ Ingestion complete.")

if __name__ == "__main__":
    run_ingestion()