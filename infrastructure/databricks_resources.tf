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