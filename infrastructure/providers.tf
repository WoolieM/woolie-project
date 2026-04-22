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
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }

  # This stores My 'memory' in the cloud
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

provider "github" {
  # Dynamically extracts 'WoolieM' from 'WoolieM/woolie-project'
  owner = split("/", var.github_repository)[0]
}