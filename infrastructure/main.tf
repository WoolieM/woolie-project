# 1. THE LANDING ZONE (Bronze Lake)
resource "google_storage_bucket" "woolie_lake" {
  name          = "${var.project_id}-lakehouse"
  location      = var.lake_location
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
  location                   = var.region # Sydney
  delete_contents_on_destroy = true
}

# 3. METADATA (Optional but recommended)
# A bucket for your Watermarks (to track your incremental loads)
resource "google_storage_bucket" "metadata" {
  name     = "${var.project_id}-metadata"
  location = var.lake_location
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0" # This pulls the latest stable 2026 version
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}