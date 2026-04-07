# Real-Time Cryptocurrency Data Pipeline

[![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![Databricks](https://img.shields.io/badge/Databricks-FF3621?style=for-the-badge&logo=databricks&logoColor=white)](https://databricks.com/)
[![dbt](https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white)](https://www.getdbt.com/)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

## 📌 Project Overview
This project is an end-to-end modern data engineering pipeline designed to ingest, process, and model real-time Bitcoin data. It showcases a scalable, event-driven architecture utilizing Google Cloud Platform (GCP) for data ingestion and storage, and the Databricks Lakehouse for stream processing and data modeling.

The entire infrastructure is defined as code (IaC) to ensure reproducibility and seamless deployments.

## 🏗️ Architecture

```mermaid
graph LR
    subgraph External_Source [External]
        API([Bitcoin API])
    end

    subgraph GCP_Platform [Google Cloud Platform]
        Prod[Python Producer]
        PS{Pub/Sub Topic}
        GCS[(GCS Bucket: Bronze)]
    end

    subgraph Databricks_Lakehouse [Databricks & Unity Catalog]
        Spark[Spark Structured Streaming]
        DBT[dbt Core / Serverless]
        Silver[(Silver: Flattened)]
        Gold[(Gold: Aggregated)]
        DAB[Databricks Asset Bundles]
    end

    subgraph Infra [Infrastructure Layer]
        TF[Terraform - Infra as Code]
    end

    API -->|REST| Prod
    Prod -->|Publish| PS
    PS -.->|ReadStream| Spark
    Spark -->|Write| GCS
    GCS -->|External Table| DBT
    DBT -->|Transform| Silver
    Silver -->|dbt Run| Gold
    
    TF -->|Provision & Manage| GCP_Platform
    TF -->|Provision & Manage| Databricks_Lakehouse
    DAB -->|Manage Schema & Orchestration| DBT

    style GCS fill:#f9f,stroke:#333,stroke-width:2px
    style Silver fill:#bbf,stroke:#333
    style Gold fill:#dfd,stroke:#333
    style TF fill:#ace,stroke:#333,stroke-width:2px
    style DAB fill:#afa,stroke:#333,stroke-width:1px
```

🛠️ Technology Stack & Responsibilities
Data Ingestion (GCP): A Python producer fetches live data from a REST API and publishes payloads to Cloud Pub/Sub for decoupled, high-throughput messaging.

Stream Processing (Databricks): Spark Structured Streaming subscribes to the Pub/Sub topic and writes raw, append-only records to a Google Cloud Storage (GCS) Bronze layer.

Data Transformation (dbt): dbt handles the ELT process, transforming raw JSON arrays into a flattened Silver layer, and building aggregated business metrics in the Gold layer.

Orchestration: Databricks Asset Bundles (DAB) manage the deployment and scheduling of the data workflows.

Infrastructure as Code: Terraform is used to provision all GCP resources (Pub/Sub, GCS) and Databricks workspaces/clusters, ensuring a robust and version-controlled environment.

🚀 Getting Started
Prerequisites
Google Cloud SDK (gcloud) authenticated

Terraform installed (>= v1.0.0)

Databricks CLI configured

Python 3.11+

Infrastructure Setup
Navigate to the terraform directory:

Bash
cd terraform/
Initialize and apply the infrastructure:

Bash
terraform init
terraform plan
terraform apply
Running the Pipeline
Start the Producer:

Bash
python src/producer.py
Deploy the Databricks Workflow:

Bash
databricks bundle deploy
databricks bundle run [woolie_streaming_job]
Execute dbt Models:

Bash
cd dbt_project/
dbt run
📈 Future Enhancements
Implement a robust CI/CD pipeline for automated testing and deployment of dbt models and Python code.

Add comprehensive data quality tests using dbt test to ensure lineage integrity.

Integrate a BI tool (like Power BI) directly to the Gold layer for real-time dashboarding.

✉️ Contact
Wooliter Chen Data Engineer
