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
  project = var.project_id
  region  = "australia-southeast1"
}

# Databricks Provider
# Terraform will use your 'databricks-sdk' from the environment.yml to auth
provider "databricks" {
  host = var.databricks_host
}