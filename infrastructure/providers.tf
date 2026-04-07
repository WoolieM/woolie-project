terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
  backend "gcs" {
    bucket = "woolie-project-metadata"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Standard Databricks Provider using your PAT
provider "databricks" {
  host  = var.databricks_host
  token = var.databricks_token
}