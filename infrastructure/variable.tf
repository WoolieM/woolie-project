variable "project_id" {
  description = "My GCP Project ID (must be unique across all of GCP)"
  type        = string
  default     = "woolie-project"
}

variable "region" {
  description = "The region for BigQuery (Sydney)"
  default     = "australia-southeast1"
}

variable "lake_location" {
  description = "The region for GCS Lake (US for Always Free Tier)"
  default     = "australia-southeast1"
}