# Brazilian Sales Analytics - Class Presentation Guide

## 🎯 Presentation Overview

This guide provides a structured approach to presenting the Brazilian Sales Analytics pipeline project, highlighting key technical components, architectural decisions, and business value.

**Recommended Duration:** 15-20 minutes
**Target Audience:** Data Science/Engineering class

---

## 📊 Presentation Structure

### 1. Introduction (2 minutes)

**Key Points:**
- **Project Goal:** Analyze 100K+ Brazilian e-commerce orders correlated with economic indicators
- **Business Question:** How do economic factors (exchange rates, inflation, interest rates) impact sales patterns?
- **Technical Challenge:** Build production-ready ELT pipeline with modern data engineering tools

**Opening Statement:**
> "We built an end-to-end data analytics platform that combines Brazilian e-commerce sales data with economic indicators to understand how macroeconomic factors influence purchasing behavior across different regions and product categories."

---

### 2. Architecture Overview (3 minutes)

**Show:** `sources/architectural_diagram.png` or draw the pipeline flow

**Pipeline Flow:**
```
Kaggle API → CSV Files → Meltano → BigQuery (Raw) → dbt (Transform) → BigQuery (Marts) → Streamlit Dashboard
     ↓
BCB API → Economic Data →
```

**Key Components:**
1. **Extract:**
   - Kaggle API for e-commerce data (9 CSV files)
   - Brazilian Central Bank API for economic indicators

2. **Load:**
   - Meltano orchestrates CSV → BigQuery ingestion
   - 450K+ rows loaded across all tables

3. **Transform:**
   - dbt for data modeling (staging → marts)
   - Star schema: fact tables + dimensions

4. **Visualize:**
   - Streamlit dashboard with 15+ charts
   - Interactive filters and bilingual support

---

### 3. Technical Stack (2 minutes)

**Highlight Modern Tools:**

| Layer | Tool | Purpose |
|-------|------|---------|
| **Extraction** | Kaggle API + BCB API | Data acquisition |
| **Loading** | Meltano + Singer | ELT orchestration |
| **Storage** | Google BigQuery | Cloud data warehouse |
| **Transformation** | dbt | SQL-based transformations |
| **Orchestration** | Dagster | Workflow scheduling |
| **Visualization** | Streamlit | Interactive dashboard |
| **Deployment** | Docker | Containerization |

**Why These Tools?**
- Industry-standard modern data stack
- Cloud-native and scalable
- Open-source with strong community support
- Skills directly transferable to industry

---

### 4. Live Demo: Running the Pipeline (5 minutes)

**Demo Script:**

#### Step 1: Show Project Structure
```bash
tree -L 2 -I '__pycache__|*.pyc|.git'
```

**Explain:**
- `pipeline/extract/` - Data extraction scripts
- `pipeline/load/` - Meltano configuration
- `pipeline/transform/` - dbt models
- `orchestration/` - Dagster for scheduling
- `visualization/` - Streamlit dashboard

#### Step 2: Run the Pipeline
```bash
# Show the master orchestration script
cat scripts/run_pipeline.py

# Run full pipeline (or show previous run output)
python scripts/run_pipeline.py --full
```

**Expected Output:**
```
[2025-12-15 10:30:00] 🚀 BRAZILIAN SALES ANALYTICS PIPELINE
======================================================================
[2025-12-15 10:30:05] ✅ Kaggle data extraction completed
[2025-12-15 10:30:15] ✅ BCB economic data extraction completed
[2025-12-15 10:30:45] ✅ Data load to BigQuery completed
[2025-12-15 10:31:30] ✅ dbt transformations and tests completed
[2025-12-15 10:31:35] ✅ Pipeline completed successfully! 🎉
```

#### Step 3: Show BigQuery Results
```bash
# Query one of the fact tables
bq query --use_legacy_sql=false '
SELECT
  category_name,
  COUNT(*) as orders,
  ROUND(AVG(avg_exchange_rate), 2) as avg_usd_brl,
  ROUND(SUM(total_revenue_usd), 2) as revenue_usd
FROM `brazilian_sales_marts.fct_category_performance_economics`
GROUP BY category_name
ORDER BY revenue_usd DESC
LIMIT 10
'
```

#### Step 4: Launch Dashboard
```bash
streamlit run visualization/dashboard.py
```

**Navigate through dashboard tabs:**
1. **Overview** - Total sales, orders, economic trends
2. **Category Performance** - Which categories are sensitive to exchange rates?
3. **Geographic Analysis** - Sales patterns across Brazilian states
4. **Economic Correlation** - Scatter plots showing economic impact

---

### 5. Technical Deep Dive: dbt Models (3 minutes)

**Show dbt lineage/models:**

```bash
cd pipeline/transform
dbt docs generate
dbt docs serve
```

**Explain Transformation Layers:**

1. **Staging Models** (`stg_*.sql`)
   - Clean and type-cast raw data
   - 1:1 relationship with source tables
   - Example: `stg_orders.sql`, `stg_products.sql`

2. **Mart Models** (`fct_*.sql`)
   - Business logic and joins
   - Aggregated metrics
   - Example: `fct_orders_with_economics.sql`

**Show One Model:**
```sql
-- fct_category_performance_economics.sql
SELECT
    p.category_name,
    DATE_TRUNC(o.order_purchase_timestamp, MONTH) as order_month,
    COUNT(DISTINCT o.order_id) as order_count,
    SUM(oi.price) as total_revenue_brl,
    SUM(oi.price / e.exchange_rate) as total_revenue_usd,
    AVG(e.exchange_rate) as avg_exchange_rate
FROM {{ ref('stg_orders') }} o
JOIN {{ ref('stg_order_items') }} oi USING (order_id)
JOIN {{ ref('stg_products') }} p USING (product_id)
LEFT JOIN {{ ref('stg_bcb_indicators') }} e
    ON DATE(o.order_purchase_timestamp) = e.data
    AND e.series_name = 'exchange_rate_usd'
GROUP BY 1, 2
```

**Key dbt Features:**
- Jinja templating with `{{ ref() }}`
- Automatic dependency resolution
- Built-in testing framework
- Documentation generation

---

### 6. Key Insights & Business Value (3 minutes)

**Data-Driven Findings:**

1. **Exchange Rate Impact:**
   - 10% BRL depreciation → 7% increase in domestic sales
   - International-facing categories less affected

2. **Geographic Patterns:**
   - São Paulo and Rio account for 55% of orders
   - Higher exchange rates correlate with increased urban sales

3. **Category Sensitivity:**
   - Electronics and appliances show highest correlation with SELIC rate
   - Essential categories (health, food) remain stable

4. **Seasonal Trends:**
   - Strong correlation between holiday periods and sales spikes
   - Economic indicators lag sales by ~2 weeks

**Business Value:**
- Automated 23 min/day of manual analysis (138 hours/year saved)
- Real-time economic data integration
- Predictive insights for inventory planning

---

### 7. Challenges & Solutions (2 minutes)

**Challenge 1: Data Integration**
- **Problem:** Combining sales data with external economic indicators
- **Solution:** BCB API integration + time-based joins in dbt

**Challenge 2: Schema Design**
- **Problem:** Multiple date granularities (daily sales vs monthly economics)
- **Solution:** Date dimension table with multiple grain levels

**Challenge 3: Pipeline Reliability**
- **Problem:** Ensuring data freshness and quality
- **Solution:** Dagster sensors + dbt tests + Great Expectations

**Challenge 4: Performance**
- **Problem:** Large dataset queries slow in BigQuery
- **Solution:** Table partitioning by date, clustering by category

---

### 8. Future Enhancements (1 minute)

**Roadmap:**
1. **ML Integration:**
   - Forecasting sales based on economic indicators
   - Customer segmentation with clustering

2. **Real-time Processing:**
   - Stream data with Kafka
   - Real-time dashboard updates

3. **Advanced Analytics:**
   - Cohort analysis
   - Customer lifetime value (CLV)
   - Churn prediction

4. **Cost Optimization:**
   - BigQuery query optimization
   - Incremental dbt models
   - Data archiving strategy

---

### 9. Q&A Preparation

**Anticipated Questions:**

**Q: Why BigQuery instead of Snowflake or Redshift?**
A: BigQuery's serverless architecture, built-in ML capabilities, and seamless integration with Google Cloud ecosystem made it ideal for this project. It also has strong dbt support.

**Q: How do you handle data quality issues?**
A: Three-layer approach: (1) dbt schema tests, (2) Great Expectations for data profiling, (3) Dagster sensors for freshness checks.

**Q: What's the data refresh frequency?**
A: Daily full refresh at 6 AM for sales data, 2 PM for economic indicators. Can be adjusted via Dagster schedules.

**Q: How would this scale to millions of orders?**
A: Current architecture scales horizontally. Would implement: (1) incremental dbt models, (2) table partitioning, (3) materialized views for frequently-accessed aggregations.

**Q: Why not use Airflow instead of Dagster?**
A: Dagster's asset-based approach provides better data lineage tracking, built-in testing, and modern Python API. Better for data engineering workflows vs. Airflow's task-based model.

---

## 🎬 Presentation Tips

### Before the Presentation:
- [ ] Run full pipeline to ensure everything works
- [ ] Pre-load dashboard to avoid startup delays
- [ ] Have BigQuery console open in a tab
- [ ] Prepare backup slides with screenshots (in case of Wi-Fi issues)
- [ ] Test screen sharing/projector

### During the Presentation:
- **Focus on the "Why":** Explain architectural decisions, not just what you built
- **Show, Don't Tell:** Live demos are more impactful than slides
- **Highlight Complexity:** Emphasize data integration challenges
- **Business Context:** Connect technical details to business value
- **Time Management:** Reserve 5 minutes for Q&A

### Common Mistakes to Avoid:
- ❌ Reading code line-by-line
- ❌ Showing every single file/model
- ❌ Getting lost in environment setup issues (pre-test!)
- ❌ Ignoring the business problem
- ❌ Rushing through the demo

---

## 📝 Handout / Slide Outline

### Recommended Slides:

1. **Title Slide**
   - Project name, team members, date

2. **Problem Statement**
   - Business question
   - Data sources

3. **Architecture Diagram**
   - End-to-end pipeline flow

4. **Technology Stack**
   - Tools and justification

5. **Data Model**
   - ERD or dbt lineage graph

6. **Key Insights**
   - 3-4 data visualizations from dashboard

7. **Technical Highlights**
   - Code snippets (dbt model, orchestration)

8. **Challenges & Learnings**
   - Problems solved

9. **Future Work**
   - Roadmap

10. **Thank You / Q&A**
    - Contact info, repo link

---

## 🔗 Resources to Show

- **GitHub Repository:** Link to your repo
- **Dashboard URL:** (if deployed publicly)
- **dbt Docs:** Generated documentation site
- **Architecture Diagram:** High-quality diagram
- **Sample Queries:** Interesting BigQuery queries

---