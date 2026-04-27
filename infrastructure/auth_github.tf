# =====================================================================
# 1. GLOBALS & LOCALS
# =====================================================================
locals {
  # The three tier environments
  environments = ["dev", "test", "prd"]

  # Automatically extracts "woolie-project" from "WoolieM/woolie-project"
  repo_name = split("/", var.github_repository)[1]
}

# =====================================================================
# 2. GCP WORKLOAD IDENTITY FEDERATION (The Handshake)
# =====================================================================
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  attribute_mapping = {
    "google.subject"        = "assertion.sub"
    "attribute.repository"  = "assertion.repository"
    "attribute.environment" = "assertion.environment"
  }
  # The "Condition" MUST use the key defined in the attribute_mapping above
  attribute_condition = "assertion.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Create 3 (or 4) separate identities in GCP
resource "google_service_account" "env_sas" {
  for_each     = toset(local.environments)
  account_id   = "github-actions-${replace(each.key, "_", "-")}" # GCP IDs can't have underscores
  display_name = "GitHub Actions SA for ${each.key}"
}

resource "google_service_account_iam_member" "wif_impersonation" {
  for_each           = toset(local.environments)
  service_account_id = google_service_account.env_sas[each.key].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.environment/${each.key}"
}

# =====================================================================
# 3. GITHUB AUTOMATION (Environments & Variables)
# =====================================================================

# Creates Dev, Test, and Prd environments in GitHub automatically
resource "github_repository_environment" "env" {
  for_each    = toset(local.environments)
  repository  = local.repo_name
  environment = each.value
}



# --- GLOBAL REPOSITORY VARIABLES ---
# These are shared across all environments (dev, test, prd)
resource "github_actions_variable" "global_configs" {
  for_each = tomap({
    "GCP_PROJECT_ID"   = var.gcp_project_id
    "GCP_REGION"       = var.gcp_region
    "GCP_WIF_PROVIDER" = google_iam_workload_identity_pool_provider.github_provider.name
    "GAR_REPOSITORY"   = google_artifact_registry_repository.woolie_bitcoin_repo.repository_id
  })

  repository    = local.repo_name
  variable_name = each.key
  value         = each.value
}




# Injects the Service Account email into all 3 environments
resource "github_actions_environment_variable" "gcp_wif_sa" {
  for_each      = toset(local.environments)
  repository    = local.repo_name
  environment   = github_repository_environment.env[each.key].environment
  variable_name = "GCP_WIF_SERVICE_ACCOUNT"

  # This dynamically picks the correct SA from the map we created above
  value = google_service_account.env_sas[each.key].email
}


# 1. Allow GitHub to push Docker images to my Artifact Registry
resource "google_artifact_registry_repository_iam_member" "github_pusher" {
  for_each   = toset(local.environments)
  location   = var.gcp_region
  repository = google_artifact_registry_repository.woolie_bitcoin_repo.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.env_sas[each.key].email}"
}

# 2. Allow GitHub to update/deploy Cloud Run jobs
resource "google_project_iam_member" "github_run_admin" {
  for_each = toset(local.environments)
  project  = var.gcp_project_id
  role     = "roles/run.admin"
  member   = "serviceAccount:${google_service_account.env_sas[each.key].email}"
}

# 3. CRITICAL: Allow GitHub to "pass" the ingest_sa to Cloud Run
# Without this, the deployment will fail with an "IAM_PERMISSION_DENIED" 
# because GitHub isn't allowed to tell Cloud Run to "act as" ingest_sa.
resource "google_service_account_iam_member" "github_sa_user" {
  for_each           = toset(local.environments)
  service_account_id = google_service_account.ingest_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.env_sas[each.key].email}"
}


# Allow the GitHub SAs to manage the Data Lake (GCS)
resource "google_project_iam_member" "github_storage_admin" {
  for_each = toset(local.environments)
  project  = var.gcp_project_id
  role     = "roles/storage.admin" # Or "roles/viewer" if you only want to list
  member   = "serviceAccount:${google_service_account.env_sas[each.key].email}"
}

# --- REPOSITORY LEVEL SECRETS --- 
# No more Token
# resource "github_actions_secret" "databricks_token" {
#   repository      = local.repo_name
#   secret_name     = "DATABRICKS_TOKEN"
#   plaintext_value = var.databricks_token
# }


# Injects "dev", "test", or "prd" into each environment context
resource "github_actions_environment_variable" "env_tag" {
  for_each      = toset(local.environments)
  repository    = local.repo_name
  environment   = github_repository_environment.env[each.key].environment
  variable_name = "ENV"
  value         = each.key # This will be 'dev', 'test', or 'prd'
}


# Injects the specific Databricks Service Principal UUID into dev, test, and prd
resource "github_actions_environment_variable" "databricks_client_id" {
  for_each      = toset(local.environments)
  repository    = local.repo_name
  environment   = github_repository_environment.env[each.key].environment
  variable_name = "DATABRICKS_CLIENT_ID"

  # This magically pulls the UUID generated in databricks_resources.tf!
  value = databricks_service_principal.github_actions[each.key].application_id
}


resource "github_actions_variable" "pubsub_config" {
  repository    = local.repo_name
  variable_name = "GCP_PUB_SUB_TOPIC"
  value         = google_pubsub_topic.bitcoin_prices.name # Points to your single topic
}