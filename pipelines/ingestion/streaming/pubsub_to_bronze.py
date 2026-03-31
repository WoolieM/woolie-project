from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
from databricks.sdk.runtime import dbutils
import os, tempfile, json

# --- THE NEW SENIOR PATTERN ---
from pyspark.sql import SparkSession

# 1. Initialize Spark (Smart Detection: Local vs Cloud)
try:
    # Try to use the Databricks Connect bridge (For VS Code)
    from databricks.connect import DatabricksSession
    spark = DatabricksSession.builder.serverless().getOrCreate()
    print("🔌 Running locally via Databricks Connect")
except ImportError:
    # If the bridge isn't there, we are natively in the Cloud Job!
    spark = SparkSession.builder.getOrCreate()
    print("☁️ Running natively in Databricks Cloud")


env = os.getenv("DATABRICKS_BUNDLE_TARGET", "dev")

# 2. Re-establish GCP Identity (Parse the JSON directly)
gcp_json_key = dbutils.secrets.get(scope="gcp-auth", key="databricks-workspace-sa-json")
gcp_auth = json.loads(gcp_json_key)

# 3. Define the Schema (Based on your Ethereum payload)
payload_schema = StructType([
    StructField("metadata", StructType([
        StructField("source", StringType()),
        StructField("ingested_at", StringType()),
        StructField("environment", StringType())
    ])),
    StructField("data", StructType([
        StructField("asset", StringType()),
        StructField("price_aud", DoubleType()),
        StructField("price_usd", DoubleType()),
        StructField("volume_aud", DoubleType()),
        StructField("volume_usd", DoubleType()),
        StructField("source_timestamp", LongType())
    ]))
])


# 4. Read the Stream from Pub/Sub with Explicit Credentials
df_raw = (spark.readStream
    .format("pubsub")
    .option("projectId", "woolie-project")
    .option("subscriptionId", "bitcoin-price-sub")
    # You MUST include the topic ID if you haven't yet
    .option("topicId", "YOUR_TOPIC_NAME") 
    
    # Pass the authentication explicitly for Serverless
    .option("clientEmail", gcp_auth["client_email"])
    .option("clientId", gcp_auth["client_id"])
    .option("privateKey", gcp_auth["private_key"])
    .option("privateKeyId", gcp_auth["private_key_id"])
    .load())

# 5. Transform: Parse JSON and add Audit Columns
df_bronze = (df_raw
    .select(
        col("messageId").alias("message_id"), # Keep the Pub/Sub message ID for deduplication later
        col("payload").cast("string").alias("raw_payload"), # Keep the exact JSON string
        col("publishTimestampInMillis").cast("timestamp").alias("source_published_at"),
        current_timestamp().alias("_ingested_at")
    )
)

# 6. Write the Stream to Bronze Delta Table
# Construct the path dynamically
checkpoint_path = f"/Volumes/{env}/bronze/checkpoints/bitcoin_prices"
table_name = f"{env}.bronze.bitcoin_prices"

query = (df_bronze.writeStream
    .format("delta")
    .outputMode("append")
    .trigger(availableNow=True)
    .option("checkpointLocation", checkpoint_path)
    .toTable(table_name))

# --- Wait for the stream to finish ---
# With trigger(availableNow=True), the stream will process one batch of all
# available data and then stop on its own. We just need to wait for it to complete.
print("🚀 Stream started. Processing all available data from Pub/Sub as a single batch...")

query.awaitTermination()

print("✅ Stream finished processing available data.")