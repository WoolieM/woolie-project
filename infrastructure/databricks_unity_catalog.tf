# 1. Create the UC Storage Credential 
resource "databricks_storage_credential" "external_gcs" {
  name = "woolie_gcs_credential"
  databricks_gcp_service_account {}
}

# 2. THE HANDSHAKE: Grant IAM access to the UC-generated Service Account
resource "google_storage_bucket_iam_member" "uc_managed_access" {
  bucket = google_storage_bucket.woolie_lake.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${databricks_storage_credential.external_gcs.databricks_gcp_service_account[0].email}"
}

# 3. Create the External Location
# This authorizes Databricks to use the bucket
resource "databricks_external_location" "lakehouse_location" {
  name            = "woolie_lakehouse"
  url             = "gs://${google_storage_bucket.woolie_lake.name}"
  credential_name = databricks_storage_credential.external_gcs.name

  depends_on = [google_storage_bucket_iam_member.uc_managed_access]
}

# 4. Create the 3 Catalogs (Managed by Terraform)
variable "environments" {
  type    = list(string)
  default = ["local_dev", "dev", "test", "prd"]
}

resource "databricks_catalog" "envs" {
  for_each = toset(var.environments)
  name     = each.value
  comment  = "Catalog for ${each.value} environment. Silver/Gold use managed storage."

  # The Catalog's "Managed" root folder.
  storage_root = "gs://${google_storage_bucket.woolie_lake.name}/${each.value}/managed"

  # Protect production data from being accidentally destroyed
  force_destroy = each.value != "prd"

  # Wait for the bucket to be authorized via External Location first
  depends_on = [databricks_external_location.lakehouse_location]
}

# 5. Grant yourself access to the catalogs and external location
resource "databricks_grants" "location_grants" {
  # If you have one location per env, keep your for_each here
  # for_each = databricks_external_location.envs 
  external_location = databricks_external_location.lakehouse_location.id

  # 1. Your manual access
  grant {
    principal  = "wooliterchen@gmail.com"
    privileges = ["ALL_PRIVILEGES"]
  }

  # 2. Dynamic loop for GitHub Actions
  dynamic "grant" {
    # Only iterate over SPs that exist AND match an environment in our list
    for_each = {
      for env, sp in databricks_service_principal.github_actions : 
      env => sp if contains(var.environments, env) && env != "local_dev"
    }

    content {
      # In this loop, 'grant.value' is the Service Principal object
      principal  = grant.value.application_id
      privileges = ["CREATE_EXTERNAL_TABLE", "CREATE_EXTERNAL_VOLUME", "READ_FILES", "WRITE_FILES"]
    }
  }
}

resource "databricks_grants" "catalog_grants" {
  for_each = toset(var.environments)
  catalog  = databricks_catalog.envs[each.value].name
  grant {
    principal  = "wooliterchen@gmail.com"
    privileges = ["ALL_PRIVILEGES"]
  }
  
  dynamic "grant" {
    for_each = contains(keys(databricks_service_principal.github_actions), each.value) ? [1] : []
    content {
      principal  = databricks_service_principal.github_actions[each.value].application_id
      privileges = ["ALL_PRIVILEGES"]
    }
  }
}
