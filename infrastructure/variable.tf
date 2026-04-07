variable "gcp_project_id" {
  description = "My GCP Project ID"
  type        = string
  default     = "woolie-project"
}

variable "gcp_region" {
  description = "The primary region (Melbourne)"
  default     = "australia-southeast2"
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

variable "pubsub_topic_name" {
  description = "The name of the Pub/Sub topic for ingestion"
  type        = string
  default     = "bitcoin-price-topic"
}

variable "app_env" {
  description = "Application Environment (dev, test, or prod)"
  type        = string
  default     = "dev"
}

variable "image_tag" {
  description = "The Docker image tag to deploy"
  type        = string
  default     = "dev" # Change this to "v2" or "prod" when ready
}

variable "ingestion_minutes" {
  description = "How long the ingestion loop runs (default 5 for budget safety)"
  type        = string # Cloud Run args are passed as strings
  default     = "5"
}

variable "coingecko_api_key" {
  description = "CoinGecko API Key - Marked sensitive so it won't show in logs"
  type        = string
  sensitive   = true
}