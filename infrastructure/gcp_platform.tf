# Enable Pub/Sub API
resource "google_project_service" "pubsub_api" {
  project            = var.gcp_project_id
  service            = "pubsub.googleapis.com"
  disable_on_destroy = false
}

# 1. THE LANDING ZONE (Bronze Lake)
resource "google_storage_bucket" "woolie_lake" {
  name          = "${var.gcp_project_id}-lakehouse"
  location      = var.gcp_region
  force_destroy = true # Allows terraform to delete the bucket even if it has files

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# 2. THE WAREHOUSE (BigQuery)
# This is where your dbt models will eventually live
resource "google_bigquery_dataset" "woolie_warehouse" {
  dataset_id                 = "woolie_bigquery"
  friendly_name              = "Woolie Warehouse"
  description                = "Final Dataset for Analytics and BI tools"
  location                   = var.gcp_region
  delete_contents_on_destroy = true
}

# 3. METADATA (Optional but recommended)
# A bucket for your Watermarks (to track your incremental loads)
resource "google_storage_bucket" "metadata" {
  name                        = "${var.gcp_project_id}-metadata"
  location                    = var.gcp_region
  uniform_bucket_level_access = true
  force_destroy               = true
}


# The "Bitcoin Price" Mailbox
resource "google_pubsub_topic" "bitcoin_prices" {
  name = var.pubsub_topic_name

  labels = {
    environment = var.app_env
    data_source = "coingecko"
  }

  depends_on = [google_project_service.pubsub_api]
}

# The Subscription (Ohio will "pull" from here)
resource "google_pubsub_subscription" "bitcoin_sub" {
  name  = "bitcoin-price-sub"
  topic = google_pubsub_topic.bitcoin_prices.name

  # Wait 20 seconds before giving up on an unacknowledged message
  ack_deadline_seconds = 20

  # Keep unacknowledged messages for 7 days
  message_retention_duration = "604800s"
}



# Enable the Artifact Registry API automatically
resource "google_project_service" "artifact_registry_api" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false # Prevents accidentally locking yourself out
}

resource "google_artifact_registry_repository" "woolie_bitcoin_repo" {
  location      = var.gcp_region
  repository_id = "bitcoin-project-repo"
  description   = "Registry for Bitcoin Ingestion Images"
  format        = "Docker"
  depends_on    = [google_project_service.artifact_registry_api]
  cleanup_policies {
    id     = "keep-tagged-release"
    action = "KEEP"
    condition {
      tag_prefixes = ["dev", "v"] #Keep anything starting with dev or v
    }
  }
  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "86400s" #1 day in seconds
    }
  }
}


# Enable Cloud Run API
resource "google_project_service" "cloudrun_api" {
  service            = "run.googleapis.com"
  project            = var.gcp_project_id
  disable_on_destroy = false
}

resource "google_cloud_run_v2_job" "woolie_bitcoin_ingest_job" {
  name                = "woolie-bitcoin-ingest-${var.app_env}"
  location            = var.gcp_region
  deletion_protection = false

  labels = {
    "environment" = var.app_env
    "managed-by"  = "terraform"
    "project"     = "woolie-bitcoin"
  }

  template {
    template {
      # Explicitly attach your dedicated service account here
      service_account = google_service_account.ingest_sa.email
      containers {
        # Point to the image you just pushed!
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.woolie_bitcoin_repo.repository_id}/bitcoin-ingest:${var.image_tag}"

        # This is where your 'click' options come in
        args = ["--minutes", var.ingestion_minutes]

        env {
          name = "COINGECKO_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.coingecko_key.secret_id
              version = "latest"
            }
          }
        }
        env {
          name  = "GCP_PROJECT_ID"
          value = var.gcp_project_id
        }
        env {
          name  = "GCP_PUB_SUB_TOPIC"
          value = var.pubsub_topic_name
        }
        env {
          name  = "ENV"
          value = var.app_env
        }
      }
    }
  }

  # Prevent race conditions: Cloud Run checks Secret Manager IAM at deployment time.
  depends_on = [
    google_secret_manager_secret_iam_member.secret_access,
    google_project_service.cloudrun_api,
    google_secret_manager_secret_version.coingecko_key_v1
  ]
}

# Enable Secret Manager API
resource "google_project_service" "secretmanager_api" {
  project            = var.gcp_project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_secret_manager_secret" "coingecko_key" {
  secret_id = "coingecko-api-key"

  replication {
    auto {} # Let Google handle the geo-redundancy
  }

  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret_version" "coingecko_key_v1" {
  secret      = google_secret_manager_secret.coingecko_key.id
  secret_data = var.coingecko_api_key # This comes from my terraform.tfvars
}



# Grant Cloud Run (default compute service account) access to read the secret
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.coingecko_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ingest_sa.email}"
}


# Create a dedicated "Identity"
resource "google_service_account" "ingest_sa" {
  account_id   = "bitcoin-ingest-sa"
  display_name = "Bitcoin Ingestion Service Account"
}

resource "google_pubsub_topic_iam_member" "ingest_publisher" {
  topic  = google_pubsub_topic.bitcoin_prices.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.ingest_sa.email}"
}


# B. Explicitly give YOURSELF permission to the bucket via code
# (This ensures you never get locked out again)
resource "google_storage_bucket_iam_member" "admin_access" {
  bucket = google_storage_bucket.metadata.name
  role   = "roles/storage.admin"
  member = "user:wooliterchen@gmail.com"
}