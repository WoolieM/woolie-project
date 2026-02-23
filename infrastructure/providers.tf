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
}

# GCP Provider - Locked to Sydney
provider "google" {
  project = var.gcp_project_id
  region  = "australia-southeast1"
}

# Databricks Provider
provider "databricks" {
  host = var.databricks_host
  token = var.databricks_token
}