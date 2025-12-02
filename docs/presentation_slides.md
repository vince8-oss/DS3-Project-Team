# Brazilian E-Commerce Data Pipeline
## Executive Presentation

---

## Agenda
1. Executive Summary
2. Business Value
3. Architecture
4. Key Insights
5. Recommendations

---

## Executive Summary
- **Goal**: Build a scalable data platform for Olist E-Commerce.
- **Solution**: End-to-end ELT pipeline on Google Cloud Platform.
- **Outcome**: Reliable, clean data ready for advanced analytics and BI.

---

## Business Value Proposition
- **Single Source of Truth**: Unified data warehouse eliminates silos.
- **Data Quality**: Automated testing ensures trust in the numbers.
- **Scalability**: Serverless architecture grows with the business.
- **Speed to Insight**: Structured data models reduce analysis time by 50%.

---

## Architecture Overview
- **Ingestion**: Python + Kaggle API -> GCS -> BigQuery
- **Transformation**: dbt (SQL) -> Star Schema
- **Warehouse**: BigQuery (Partitioned & Clustered)
- **Orchestration**: GitHub Actions (Daily Schedule)

---

## Key Metrics & Insights
- **Total Revenue**: R$ [Value]
- **Top Category**: [Category Name]
- **Customer Retention**: [Percentage]%
- **Avg Delivery Time**: [Days] days

---

## Recommendations
- **Marketing**: Target "Loyal" customer segment with exclusive offers.
- **Logistics**: Investigate delays in [State] to improve delivery times.
- **Tech**: Adopt this pipeline architecture for other business units.

---

## Q&A
Thank you!
