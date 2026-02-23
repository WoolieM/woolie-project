variable "gcp_project_id" {
  description = "My GCP Project ID"
  type        = string
  default     = "woolie-project"
}

variable "gcp_region" {
  description = "The region for BigQuery (Sydney)"
  default     = "australia-southeast1"
}

variable "lake_location" {
  description = "The region for GCS Lake (US for Always Free Tier)"
  default     = "australia-southeast1"
}

variable "databricks_region" {
  description = "The Processing Brain (Free Edition)"
  default     = "us-east-2" # US East (Ohio)
}

variable "databricks_host" {
  type        = string
  description = "The Workspace URL for your US-East-2 Ohio instance"
}

variable "databricks_token" {
  type        = string
  description = "The Personal Access Token (PAT) from Databricks User Settings"
  sensitive   = true
  default     = null
}

variable "databricks_workspace_id" {
  type        = string
  description = "The ID found after ?o= in your browser URL"
}
