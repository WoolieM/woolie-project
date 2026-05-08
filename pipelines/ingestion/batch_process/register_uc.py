import click
import sys
import os
# Databricks spark_python_task does not define __file__ because it uses exec().
# However, the full path to this script is always passed as sys.argv[0].
script_path = __file__ if '__file__' in globals() else sys.argv[0]

current_dir = os.path.dirname(os.path.abspath(script_path))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))

# Add to Python path if it's not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from pipelines.ingestion.utils.utility import get_spark, sync_to_bronze

@click.command()
@click.option('--env', default='local_dev', help='Target environment (e.g., local_dev, dev, prd)')
def run_metadata_aware_sync(env: str) -> None:
    """Scans the DLT destination directory and registers tables in Unity Catalog.
    
    Uses Databricks SQL `LIST` to identify dynamically generated Delta tables in 
    the Bronze layer, skipping internal metadata folders (e.g., `_delta_log`, `init`).
    The target environment can be passed as a command-line option (defaults to 'local_dev').
    """
    spark = get_spark()
    
    # Root path where dlt lands everything
    dlt_root_path = f"gs://woolie-project-lakehouse/{env}/bronze/dlt"
    
    print(f"Directory Search: Looking for tables in {dlt_root_path}...")

    try:
        # 1. List items via Databricks SQL to bypass Connect's dbutils limits for gs://
        # This command runs on the cluster and leverages Unity Catalog's External Location
        files = spark.sql(f"LIST '{dlt_root_path}'").collect()
        
        # 2. Filter: Must be a directory AND name must NOT start with '_'
        tables_to_sync = []
        for f in files:
            name = f["name"]
            clean_name = name.rstrip('/')
            # In Databricks SQL LIST, directories typically end with '/' or have no file extension
            if not clean_name.startswith('_') and clean_name != 'init' and (name.endswith('/') or '.' not in clean_name):
                tables_to_sync.append(clean_name)

        if not tables_to_sync:
            print("📭 No data tables found to sync.")
            return

        print(f"🔍 Found {len(tables_to_sync)} tables: {tables_to_sync}")

        # 3. Loop through and register each
        for table in tables_to_sync:
            sync_to_bronze(
                spark=spark,
                env=env,
                table_name=table
            )
            
    except Exception as e:
        print(f"❌ Error listing directory: {e}")
        print("Check if the path exists or if GCS permissions are correct.")

if __name__ == "__main__":
    # standalone_mode=False prevents click from calling sys.exit()
    # which stops Databricks/IPython from throwing the exit warning.
    run_metadata_aware_sync(standalone_mode=False)