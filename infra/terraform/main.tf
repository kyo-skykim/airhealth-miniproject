# GCP infrastructure for the AirHealth cloud backend (BACKEND=bigquery).
# Provisions the GCS raw landing bucket and the BigQuery raw + analytics datasets.
# Apply:  terraform init && terraform apply -var project_id=YOUR_PROJECT

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "location" {
  type    = string
  default = "US"
}

resource "google_storage_bucket" "raw" {
  name                        = "${var.project_id}-airhealth-raw"
  location                    = var.location
  uniform_bucket_level_access = true
  force_destroy               = true

  lifecycle_rule {
    condition { age = 90 }
    action { type = "Delete" }
  }
}

resource "google_bigquery_dataset" "raw" {
  dataset_id  = "airhealth_raw"
  location    = var.location
  description = "AirHealth raw landing tables."
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id  = "airhealth_analytics"
  location    = var.location
  description = "AirHealth dbt staging/intermediate/marts."
}

output "raw_bucket" {
  value = google_storage_bucket.raw.name
}

output "bq_datasets" {
  value = [google_bigquery_dataset.raw.dataset_id, google_bigquery_dataset.analytics.dataset_id]
}

# Managed Airflow (Cloud Composer) is optional and incurs ongoing cost.
# Uncomment to provision; otherwise run the docker-compose Airflow locally.
#
# resource "google_composer_environment" "airflow" {
#   name   = "airhealth"
#   region = var.region
#   config {
#     software_config { image_version = "composer-2-airflow-2" }
#   }
# }
