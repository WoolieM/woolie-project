# 1. Create the dedicated Service Account (The "Muscle")
resource "google_service_account" "databricks_sa" {
  account_id   = "databricks-workspace-sa"
  display_name = "Databricks Workspace Access Account"
}

# 2. Grant permission to PULL from the Melbourne Pub/Sub
resource "google_pubsub_subscription_iam_member" "databricks_subscriber" {
  subscription = google_pubsub_subscription.bitcoin_sub.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_service_account.databricks_sa.email}"
}

# 3. Grant permission to VIEW the topic
resource "google_pubsub_topic_iam_member" "databricks_viewer" {
  topic  = google_pubsub_topic.bitcoin_prices.name
  role   = "roles/pubsub.viewer"
  member = "serviceAccount:${google_service_account.databricks_sa.email}"
}

# 4. Generate a secure JSON key for this Service Account
resource "google_service_account_key" "databricks_sa_key" {
  service_account_id = google_service_account.databricks_sa.name
}

# 5. Create a Secret Scope inside your REAL Databricks Workspace
resource "databricks_secret_scope" "gcp_credentials" {
  name = "gcp-auth"
}

# 6. Inject the JSON key securely into Databricks
resource "databricks_secret" "sa_key_secret" {
  key = "databricks-workspace-sa-json"
  # The key is base64 encoded by GCP, so we decode it before saving to Databricks
  string_value = base64decode(google_service_account_key.databricks_sa_key.private_key)
  scope        = databricks_secret_scope.gcp_credentials.name
}


# The "Engine" for dbt - Serverless starts in < 10 seconds
resource "databricks_sql_endpoint" "dbt_warehouse" {
  name           = "Woolie Serverless"
  cluster_size   = "2X-Small" # Smallest is usually plenty for dbt logic
  auto_stop_mins = 10         # Serverless stops fast, saving money

  enable_serverless_compute = true
  warehouse_type            = "PRO" # Required for Serverless

  tags {
    custom_tags {
      key   = "Owner"
      value = "Woolie"
    }
  }
}

# Export the connection details for your dbt profile
output "dbt_http_path" {
  value = databricks_sql_endpoint.dbt_warehouse.odbc_params[0].path
}

output "dbt_hostname" {
  value = var.databricks_host
}

# =====================================================================
# 7. REGISTER DATABRICKS-NATIVE SERVICE PRINCIPALS (For GitHub OIDC)
# =====================================================================

# 1. Create native Service Principals 
# We DO NOT provide an email address here. Databricks will generate a UUID.
resource "databricks_service_principal" "github_actions" {
  for_each = toset(["dev", "test", "prd"])

  display_name          = "GitHub Actions (${each.key})"
  workspace_access      = true
  databricks_sql_access = true
}

# 2. Grant Permissions to the Warehouse
resource "databricks_permissions" "warehouse_usage" {
  sql_endpoint_id = databricks_sql_endpoint.dbt_warehouse.id

  dynamic "access_control" {
    for_each = toset(["dev", "test", "prd"])
    content {
      # We use application_id (the Databricks UUID) instead of the GCP email
      service_principal_name = databricks_service_principal.github_actions[access_control.key].application_id
      permission_level       = "CAN_USE"
    }
  }
}

# =====================================================================
# 8. OUTPUTS FOR GITHUB & ACCOUNT CONSOLE
# =====================================================================
# You need these UUIDs to set up the trust in the Databricks Account Console!

output "github_client_id_dev" {
  value       = databricks_service_principal.github_actions["dev"].application_id
  description = "UUID for GitHub Actions Dev Environment"
}

output "github_client_id_test" {
  value       = databricks_service_principal.github_actions["test"].application_id
  description = "UUID for GitHub Actions Test Environment"
}

output "github_client_id_prd" {
  value       = databricks_service_principal.github_actions["prd"].application_id
  description = "UUID for GitHub Actions Prd Environment"
}