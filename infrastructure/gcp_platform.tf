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
  name     = "${var.gcp_project_id}-metadata"
  location = var.gcp_region
}


# The "Bitcoin Price" Mailbox
resource "google_pubsub_topic" "bitcoin_prices" {
  name = "bitcoin-price-topic"

  labels = {
    environment = "dev"
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