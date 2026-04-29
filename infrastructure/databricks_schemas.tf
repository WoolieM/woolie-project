# =====================================================================
# 1. SCHEMA BLUEPRINTS
# =====================================================================
locals {
  # Define the configurations for each schema type
  schema_configs = {
    bronze  = { storage_suffix = "/bronze", comment = "Raw ingestion layer backed by GCP Bucket" }
    silver  = { storage_suffix = null,      comment = "Cleaned layer (Managed Storage)" }
    gold    = { storage_suffix = null,      comment = "Reporting layer (Managed Storage)" }
    sandbox = { storage_suffix = null,      comment = "Test Data and basic exploration" }
    audit   = { storage_suffix = null,      comment = "Audit and metadata layer (dbt_project_evaluator)" }
  }

  # This matrix automatically generates dev_bronze, test_bronze, dev_silver, etc.
  schema_matrix = {
    for pair in setproduct(var.environments, keys(local.schema_configs)) :
    "${pair[0]}_${pair[1]}" => {
      env            = pair[0]
      schema_name    = pair[1]
      # Only Bronze gets the GCS path; others get null (Managed Storage)
      storage_root   = local.schema_configs[pair[1]].storage_suffix != null ? "gs://${google_storage_bucket.woolie_lake.name}/${pair[0]}${local.schema_configs[pair[1]].storage_suffix}" : null
      comment        = "${local.schema_configs[pair[1]].comment} for ${pair[0]}"
    }
  }
}

# =====================================================================
# 2. CREATE SCHEMAS
# =====================================================================
resource "databricks_schema" "lakehouse_layers" {
  for_each     = local.schema_matrix
  
  catalog_name = databricks_catalog.envs[each.value.env].name
  name         = each.value.schema_name
  storage_root = each.value.storage_root
  comment      = each.value.comment
}

# =====================================================================
# 3. CREATE EXTERNAL VOLUME (Checkpoints)
# =====================================================================
resource "databricks_volume" "streaming_checkpoints" {
  for_each = toset(var.environments)

  name         = "checkpoints"
  catalog_name = databricks_catalog.envs[each.value].name
  # Attach it to the Bronze schema created above
  schema_name  = databricks_schema.lakehouse_layers["${each.value}_bronze"].name
  
  volume_type      = "EXTERNAL"
  # Placed adjacent to bronze to avoid UC overlap paths
  storage_location = "gs://${google_storage_bucket.woolie_lake.name}/${each.value}/checkpoints"
  comment          = "Storage for streaming checkpoints in GCP for ${each.value}"
}

# =====================================================================
# 4. GRANTS (Crucial: Transferring ownership/rights to the CI pipeline)
# =====================================================================
resource "databricks_grants" "schema_grants" {
  for_each = local.schema_matrix
  schema   = databricks_schema.lakehouse_layers[each.key].id

  grant {
    principal  = "wooliterchen@gmail.com"
    privileges = ["ALL_PRIVILEGES"]
  }

  grant {
    principal  = databricks_service_principal.github_actions[each.value.env].application_id
    privileges = ["ALL_PRIVILEGES"]
  }
}

resource "databricks_grants" "volume_grants" {
  for_each = toset(var.environments)
  volume   = databricks_volume.streaming_checkpoints[each.value].id

  grant {
    principal  = "wooliterchen@gmail.com"
    privileges = ["ALL_PRIVILEGES"]
  }

  grant {
    principal  = databricks_service_principal.github_actions[each.value].application_id
    privileges = ["ALL_PRIVILEGES"]
  }
}