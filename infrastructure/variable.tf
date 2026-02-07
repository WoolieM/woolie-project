variable "project_id" {
  description = "Your Google Cloud Project ID"
  type        = string
  default     = "PASTE_YOUR_PROJECT_ID_HERE" 
}

variable "region" {
  description = "The region for BigQuery (Sydney)"
  default     = "australia-southeast1"
}

variable "lake_location" {
  description = "The region for GCS Lake (US for Always Free Tier)"
  default     = "US-CENTRAL1"
}