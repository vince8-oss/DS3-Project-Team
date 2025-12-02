# Brazilian E-Commerce Data Pipeline Project Report

## 1. Executive Summary
This project implements a robust, scalable data engineering pipeline for the Olist Brazilian E-Commerce dataset. The solution leverages modern cloud-native technologies (Google BigQuery, dbt) to transform raw transactional data into a high-performance Star Schema data warehouse, enabling deep business insights into sales trends, customer behavior, and logistics performance.

## 2. Architecture Overview
The pipeline follows a standard ELT (Extract, Load, Transform) pattern:
1.  **Ingestion**: Python scripts download data from Kaggle and load it idempotently into BigQuery via GCS.
2.  **Transformation**: dbt (data build tool) cleans, normalizes, and models the data into Dimensions and Facts.
3.  **Storage**: Google BigQuery serves as the serverless data warehouse.
4.  **Quality**: Automated testing via dbt ensures data integrity (null checks, referential integrity, business rules).
5.  **Orchestration**: GitHub Actions schedules the pipeline to run daily.
6.  **Analytics**: Jupyter Notebooks and BI tools consume the modeled data for reporting.

## 3. Design Decisions & Schema Justification
### Star Schema
We chose a Star Schema design for the data warehouse to optimize for analytical query performance and usability.
-   **Fact Tables**: `FactOrders` and `FactOrderItems` capture the core business events (transactions). They are partitioned by date to minimize query costs.
-   **Dimension Tables**: `DimCustomer`, `DimProduct`, `DimSeller`, and `DimDate` provide context. They are denormalized (Type 1 SCD) to reduce joins during analysis.

### Tools
-   **BigQuery**: Chosen for its serverless scalability and separation of storage/compute.
-   **dbt**: Selected for its ability to bring software engineering best practices (version control, testing, modularity) to SQL.
-   **Python**: Used for flexible data ingestion and advanced analysis.

## 4. Data Lineage
Raw Data (`raw.*`) -> Staging Views (`stg_*`) -> Warehouse Tables (`dim_*`, `fact_*`) -> Analysis

## 5. Challenges & Assumptions
-   **Assumption**: The dataset is static (historical), but the pipeline is designed to handle incremental updates.
-   **Challenge**: Data quality issues in the raw source (e.g., inconsistent state codes) were handled in the staging layer.

## 6. Key Insights
-   **Sales Trends**: [Insert findings from analysis]
-   **Customer Segmentation**: [Insert findings from analysis]
-   **Delivery Performance**: [Insert findings from analysis]

## 7. Future Recommendations
-   Implement a CI/CD pipeline for dbt models.
-   Add more sophisticated data quality checks with Great Expectations.
-   Build a real-time dashboard using Looker Studio.
