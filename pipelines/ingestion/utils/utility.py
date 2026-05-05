from pyspark.sql import SparkSession
import os, sys



def get_spark() -> SparkSession:
    """Smart Detection: Local (Connect) vs Cloud (Native).
    
    Detects the environment based on DATABRICKS_RUNTIME_VERSION. If running 
    natively in the cloud, returns a standard SparkSession. If running locally, 
    returns a serverless DatabricksSession via databricks-connect.
    
    Returns:
        SparkSession: The active Spark session.
    """
    # Databricks always sets this variable when running natively in the cloud
    if "DATABRICKS_RUNTIME_VERSION" in os.environ:
        print("☁️ Running natively in Databricks Cloud")
        return SparkSession.builder.getOrCreate()
    else:
        print("🔌 Running locally via Databricks Connect")
        from databricks.connect import DatabricksSession
        # Use .serverless() when bridging from local VM
        return DatabricksSession.builder.serverless().getOrCreate()

def sync_to_bronze(
    spark: SparkSession,
    env: str,
    table_name: str
) -> None:
    """Registers native dlt Delta tables into Unity Catalog as an External Table.
    
    Args:
        spark (SparkSession): The active Spark session.
        env (str): The current deployment environment (e.g., 'local_dev', 'prd').
        table_name (str): The name of the dlt table to register.
    """
    
    print(f"🔄 Syncing {table_name} into Catalog: '{env}' | Schema: 'bronze'")

    # 1. Path Definitions
    # Data is landed by dlt here:
    source_data_path = f"gs://woolie-project-lakehouse/{env}/bronze/dlt/{table_name}"
    
    # 2. UC Table Name (e.g., local_dev.bronze.family_profile)
    full_uc_target = f"{env}.bronze.{table_name}"

    # 3. Register as External Delta Table (Zero-Copy)
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {full_uc_target}
        USING DELTA
        LOCATION '{source_data_path}'
    """)

    print(f"✅ Sync Complete: {full_uc_target}")