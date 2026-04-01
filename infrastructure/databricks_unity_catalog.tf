# 1. Create the UC Storage Credential 
# This triggers Databricks to generate its own unique GCP Service Account
resource "databricks_storage_credential" "external_gcs" {
  name = "woolie_gcs_credential"
  databricks_gcp_service_account {}
}

# 2. THE HANDSHAKE: Grant IAM access to the UC-generated Service Account
# This is separate from the 'databricks_sa' you already created
resource "google_storage_bucket_iam_member" "uc_managed_access" {
  bucket = google_storage_bucket.woolie_lake.name
  role   = "roles/storage.admin"

  # Accessing the auto-generated email from the resource above
  member = "serviceAccount:${databricks_storage_credential.external_gcs.databricks_gcp_service_account[0].email}"
}

# 3. Create the External Location
# This tells Serverless Compute that this GCS path is authorized
resource "databricks_external_location" "lakehouse_location" {
  name            = "woolie_lakehouse"
  url             = "gs://${google_storage_bucket.woolie_lake.name}"
  credential_name = databricks_storage_credential.external_gcs.name

  depends_on = [google_storage_bucket_iam_member.uc_managed_access]
}

# 4. Grant your identity access to use this location
resource "databricks_grants" "location_grants" {
  external_location = databricks_external_location.lakehouse_location.id

  grant {
    principal  = "wooliterchen@gmail.com"
    privileges = ["ALL_PRIVILEGES"]
  }
}