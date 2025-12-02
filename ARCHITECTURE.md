# Brazilian E-Commerce Data Pipeline - Architecture Documentation

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Data Flow Architecture](#data-flow-architecture)
3. [dbt Model Lineage](#dbt-model-lineage)
4. [Dagster Orchestration Flow](#dagster-orchestration-flow)
5. [BigQuery Schema Design](#bigquery-schema-design)
6. [Infrastructure Architecture](#infrastructure-architecture)
7. [Security Architecture](#security-architecture)

---

## System Architecture Overview

### High-Level Architecture

```mermaid
graph TB
    subgraph "Data Source"
        A[Kaggle API<br/>Brazilian E-Commerce<br/>Dataset]
    end

    subgraph "Ingestion Layer"
        B[Python Scripts]
        B1[kaggle_downloader.py]
        B2[gcs_uploader.py]
        B3[bigquery_loader.py]
    end

    subgraph "Storage Layer"
        C[Google Cloud Storage<br/>Raw Data Archive<br/>Optional]
        D[BigQuery<br/>staging dataset<br/>9 Raw Tables]
    end

    subgraph "Transformation Layer"
        E[dbt Core]
        E1[Staging Models<br/>7 Views]
        E2[Warehouse Models<br/>6 Tables]
    end

    subgraph "Data Warehouse"
        F[BigQuery Datasets]
        F1[dev_warehouse_staging<br/>Views]
        F2[dev_warehouse_warehouse<br/>Tables]
    end

    subgraph "Analytics Layer"
        G[Jupyter Notebooks<br/>Python Analytics]
        H[Looker Studio<br/>Dashboards<br/>Future]
    end

    subgraph "Orchestration"
        I[Dagster<br/>Pipeline Scheduler<br/>& Monitor]
    end

    A -->|Download CSV| B1
    B1 -->|9 CSV Files| B2
    B2 -->|Upload| C
    B1 -->|Load| B3
    B3 -->|Create Tables| D
    D -->|Source Data| E1
    E1 -->|Transform| E2
    E1 -->|Create Views| F1
    E2 -->|Create Tables| F2
    F2 -->|Query Data| G
    F2 -.->|Future| H
    I -->|Orchestrate| B
    I -->|Orchestrate| E

    style A fill:#e1f5ff
    style D fill:#fff4e1
    style F fill:#e8f5e9
    style I fill:#f3e5f5
```

### Technology Stack

```mermaid
graph LR
    subgraph "Languages & Frameworks"
        A1[Python 3.9+]
        A2[SQL]
        A3[YAML]
    end

    subgraph "Data Processing"
        B1[Pandas]
        B2[SQLAlchemy]
    end

    subgraph "Cloud Platform"
        C1[Google Cloud Platform]
        C2[BigQuery]
        C3[Cloud Storage]
    end

    subgraph "Data Engineering"
        D1[dbt-bigquery]
        D2[Dagster]
        D3[Kaggle API]
    end

    subgraph "Analytics"
        E1[Jupyter]
        E2[Matplotlib]
        E3[Seaborn]
    end

    A1 --> B1
    A1 --> D2
    A2 --> D1
    B1 --> C2
    D1 --> C2
    D2 --> D1
    D3 --> B1
    E1 --> B1

    style C1 fill:#4285f4,color:#fff
    style C2 fill:#669df6,color:#fff
    style C3 fill:#aecbfa
```

---

## Data Flow Architecture

### End-to-End Data Pipeline

```mermaid
flowchart TD
    Start([Start Pipeline]) --> Download

    subgraph "Stage 1: Ingestion"
        Download[Download from Kaggle<br/>9 CSV Files<br/>~100k orders]
        Archive[Archive to GCS<br/>Optional]
        Load[Load to BigQuery<br/>MD5 Deduplication]
    end

    subgraph "Stage 2: Raw Layer"
        Raw1[orders_raw<br/>customers_raw<br/>products_raw]
        Raw2[order_items_raw<br/>payments_raw<br/>sellers_raw]
        Raw3[reviews_raw<br/>geolocation_raw<br/>translations_raw]
        Meta[_load_metadata<br/>Audit Trail]
    end

    subgraph "Stage 3: Staging Layer"
        Stg1[stg_orders<br/>Type Casting<br/>Date Parsing]
        Stg2[stg_customers<br/>stg_products<br/>stg_sellers]
        Stg3[stg_order_items<br/>stg_payments<br/>stg_reviews]
    end

    subgraph "Stage 4: Warehouse Layer"
        Dim[Dimensions<br/>SCD Type 1]
        Dim1[dim_customer<br/>dim_product]
        Dim2[dim_seller<br/>dim_date]
        Fact[Facts<br/>Incremental]
        Fact1[fact_orders<br/>fact_order_items]
    end

    subgraph "Stage 5: Consumption"
        Query[SQL Queries]
        Notebook[Jupyter Analysis]
        Dashboard[Dashboards]
    end

    Download --> Archive
    Download --> Load
    Load --> Raw1
    Load --> Raw2
    Load --> Raw3
    Load --> Meta

    Raw1 --> Stg1
    Raw2 --> Stg2
    Raw3 --> Stg3

    Stg1 --> Dim1
    Stg2 --> Dim1
    Stg2 --> Dim2

    Stg1 --> Fact1
    Stg3 --> Fact1
    Dim1 --> Fact1
    Dim2 --> Fact1

    Fact1 --> Query
    Fact1 --> Notebook
    Fact1 --> Dashboard
    Dim1 --> Query

    Query --> End([End])

    style Download fill:#4285f4,color:#fff
    style Load fill:#669df6,color:#fff
    style Stg1 fill:#81c784
    style Dim1 fill:#ffb74d
    style Fact1 fill:#e57373
```

### Data Quality & Idempotency Flow

```mermaid
flowchart TD
    A[New CSV File] --> B{Calculate MD5 Hash}
    B --> C{Check _load_metadata}
    C -->|Hash Exists| D[Skip - Already Loaded]
    C -->|New Hash| E[Load to BigQuery]
    E --> F[Insert into Raw Table]
    F --> G[Record in _load_metadata]
    G --> H[dbt Run]
    H --> I{dbt Tests}
    I -->|Pass| J[Data Ready]
    I -->|Fail| K[Alert & Rollback]
    K --> L[Fix Data Issues]
    L --> H
    D --> M[Pipeline Complete]
    J --> M

    style B fill:#fff176
    style C fill:#81c784
    style I fill:#ff8a65
    style J fill:#4db6ac
```

---

## dbt Model Lineage

### Complete dbt DAG

```mermaid
graph TB
    subgraph "Sources: staging dataset"
        S1[(orders_raw)]
        S2[(customers_raw)]
        S3[(products_raw)]
        S4[(order_items_raw)]
        S5[(payments_raw)]
        S6[(sellers_raw)]
        S7[(reviews_raw)]
        S8[(product_category_<br/>name_translation_raw)]
    end

    subgraph "Staging Layer: dev_warehouse_staging"
        ST1[stg_orders<br/>VIEW]
        ST2[stg_customers<br/>VIEW]
        ST3[stg_products<br/>VIEW]
        ST4[stg_order_items<br/>VIEW]
        ST5[stg_payments<br/>VIEW]
        ST6[stg_sellers<br/>VIEW]
        ST7[stg_reviews<br/>VIEW]
    end

    subgraph "Warehouse Dimensions: dev_warehouse_warehouse"
        D1[dim_customer<br/>TABLE<br/>SCD Type 1]
        D2[dim_product<br/>TABLE<br/>SCD Type 1]
        D3[dim_seller<br/>TABLE<br/>SCD Type 1]
        D4[dim_date<br/>TABLE<br/>Generated]
    end

    subgraph "Warehouse Facts: dev_warehouse_warehouse"
        F1[fact_orders<br/>TABLE<br/>INCREMENTAL<br/>Partitioned]
        F2[fact_order_items<br/>TABLE<br/>INCREMENTAL<br/>Partitioned]
    end

    S1 --> ST1
    S2 --> ST2
    S3 --> ST3
    S4 --> ST4
    S5 --> ST5
    S6 --> ST6
    S7 --> ST7
    S8 --> ST3

    ST1 --> D1
    ST2 --> D1
    ST1 --> F1
    ST5 --> F1

    ST3 --> D2
    ST4 --> D2

    ST6 --> D3
    ST4 --> D3

    ST1 --> D4

    D1 --> F1
    D2 --> F2
    D3 --> F2
    D4 --> F1
    D4 --> F2

    ST4 --> F2
    F1 --> F2

    style ST1 fill:#81c784
    style ST2 fill:#81c784
    style ST3 fill:#81c784
    style ST4 fill:#81c784
    style ST5 fill:#81c784
    style ST6 fill:#81c784
    style ST7 fill:#81c784

    style D1 fill:#ffb74d
    style D2 fill:#ffb74d
    style D3 fill:#ffb74d
    style D4 fill:#ffb74d

    style F1 fill:#e57373
    style F2 fill:#e57373
```

### Staging Layer Details

```mermaid
graph LR
    subgraph "stg_orders Transformations"
        A1[orders_raw] -->|Cast timestamps| A2[order_purchase_timestamp]
        A1 -->|Parse dates| A3[order_delivered_date]
        A1 -->|Normalize status| A4[order_status]
        A2 --> A5[stg_orders]
        A3 --> A5
        A4 --> A5
    end

    subgraph "stg_products Transformations"
        B1[products_raw] -->|Join translations| B2[category_english]
        B3[translations_raw] -->|Lookup| B2
        B1 -->|Cast dimensions| B4[product_weight_g]
        B2 --> B5[stg_products]
        B4 --> B5
    end

    style A5 fill:#81c784
    style B5 fill:#81c784
```

### Warehouse Layer Details

```mermaid
graph TB
    subgraph "dim_customer Logic"
        C1[stg_customers] -->|Join| C2[Customer Demographics]
        C3[stg_orders] -->|Aggregate| C4[total_orders<br/>total_spent]
        C4 -->|Segment| C5[customer_segment<br/>Loyal/Repeat/One-time]
        C2 --> C6[dim_customer]
        C5 --> C6
    end

    subgraph "fact_orders Logic"
        F1[stg_orders] -->|Calculate| F2[total_order_value]
        F3[stg_payments] -->|Sum| F2
        F1 -->|Calculate| F4[delivery_time_days]
        F1 -->|Flag| F5[is_late_delivery]
        F2 --> F6[fact_orders]
        F4 --> F6
        F5 --> F6
        D1[dim_customer] -->|FK| F6
        D2[dim_date] -->|FK| F6
    end

    style C6 fill:#ffb74d
    style F6 fill:#e57373
```

---

## Dagster Orchestration Flow

### Asset Dependency Graph

```mermaid
graph TB
    Start([Dagster Schedule<br/>Daily at 00:00]) --> A

    A[Asset: kaggle_dataset<br/>Download CSV files<br/>Duration: ~2 min]
    B[Asset: gcs_raw_data<br/>Upload to GCS<br/>Duration: ~30 sec<br/>OPTIONAL]
    C[Asset: bigquery_raw_tables<br/>Load to BigQuery<br/>Duration: ~2 min]
    D[Asset: dbt_staging<br/>Create staging views<br/>Duration: ~10 sec]
    E[Asset: dbt_warehouse<br/>Build dimensions & facts<br/>Duration: ~20 sec]
    F[Asset: dbt_tests<br/>Run data quality tests<br/>Duration: ~15 sec]

    A -->|Success| B
    A -->|Success| C
    B -->|Success| C
    C -->|Success| D
    D -->|Success| E
    E -->|Success| F
    F -->|Success| End([Complete<br/>Total: ~5 min])

    A -.->|Failure| Retry1[Retry 3x]
    C -.->|Failure| Retry2[Retry 3x]
    E -.->|Failure| Alert[Send Alert]
    F -.->|Tests Fail| Alert

    Retry1 -.->|All Failed| Alert
    Retry2 -.->|All Failed| Alert

    style A fill:#4285f4,color:#fff
    style C fill:#669df6,color:#fff
    style E fill:#81c784
    style F fill:#ff8a65
    style Alert fill:#e57373,color:#fff
```

### Dagster Asset Materialization

```mermaid
sequenceDiagram
    participant UI as Dagster UI
    participant Dag as Dagster Engine
    participant Kag as Kaggle API
    participant GCS as Cloud Storage
    participant BQ as BigQuery
    participant dbt as dbt Core

    UI->>Dag: Materialize All Assets
    Dag->>Kag: Download dataset
    Kag-->>Dag: CSV files (9 files)

    par Optional GCS Upload
        Dag->>GCS: Upload raw files
        GCS-->>Dag: Upload complete
    end

    Dag->>BQ: Load CSV to raw tables
    BQ-->>Dag: Tables created (9 tables + metadata)

    Dag->>dbt: dbt run --select staging
    dbt->>BQ: Create staging views
    BQ-->>dbt: 7 views created
    dbt-->>Dag: Staging complete

    Dag->>dbt: dbt run --select warehouse
    dbt->>BQ: Create warehouse tables
    BQ-->>dbt: 6 tables created
    dbt-->>Dag: Warehouse complete

    Dag->>dbt: dbt test
    dbt->>BQ: Validate data quality
    BQ-->>dbt: Test results
    dbt-->>Dag: 30+ tests passed

    Dag-->>UI: All assets materialized ✓
```

### Job Execution Timeline

```mermaid
gantt
    title Pipeline Execution Timeline (Typical Run)
    dateFormat  HH:mm
    axisFormat %H:%M

    section Ingestion
    Download from Kaggle    :active, download, 00:00, 2m
    Upload to GCS (optional):        upload, after download, 30s
    Load to BigQuery        :crit,   load, after download, 2m

    section Transformation
    dbt Staging Models      :active, staging, after load, 10s
    dbt Warehouse Models    :        warehouse, after staging, 20s

    section Validation
    dbt Tests               :crit,   tests, after warehouse, 15s

    section Completion
    Pipeline Complete       :milestone, done, after tests, 0s
```

---

## BigQuery Schema Design

### Star Schema Architecture

```mermaid
erDiagram
    DIM_CUSTOMER ||--o{ FACT_ORDERS : "customer_key"
    DIM_DATE ||--o{ FACT_ORDERS : "date_key"
    DIM_CUSTOMER ||--o{ FACT_ORDER_ITEMS : "via fact_orders"
    DIM_PRODUCT ||--o{ FACT_ORDER_ITEMS : "product_key"
    DIM_SELLER ||--o{ FACT_ORDER_ITEMS : "seller_key"
    DIM_DATE ||--o{ FACT_ORDER_ITEMS : "date_key"
    FACT_ORDERS ||--o{ FACT_ORDER_ITEMS : "order_key"

    DIM_CUSTOMER {
        int customer_key PK
        string customer_id UK
        string customer_city
        string customer_state
        int total_orders
        decimal total_spent
        string customer_segment
        date first_order_date
        date last_order_date
    }

    DIM_PRODUCT {
        int product_key PK
        string product_id UK
        string product_category_english
        int total_quantity_sold
        decimal total_revenue
        string product_sales_tier
    }

    DIM_SELLER {
        int seller_key PK
        string seller_id UK
        string seller_city
        string seller_state
        int total_items_sold
        decimal total_revenue
        string seller_volume_tier
    }

    DIM_DATE {
        date date_key PK
        date date_day
        int date_month
        int date_year
        string day_of_week
        string month_name
        int quarter
        bool is_weekend
    }

    FACT_ORDERS {
        int order_key PK
        int customer_key FK
        date date_key FK
        string order_id UK
        string order_status
        timestamp order_purchase_date
        date delivery_date
        decimal total_order_value
        decimal freight_value
        int payment_count
        int item_count
        int delivery_time_days
        int estimated_delivery_days
        bool is_late_delivery
    }

    FACT_ORDER_ITEMS {
        int order_item_key PK
        int order_key FK
        int product_key FK
        int seller_key FK
        string order_id
        int order_item_id
        decimal price
        decimal freight_value
        timestamp shipping_limit_date
    }
```

### Dataset Organization

```mermaid
graph TB
    subgraph "BigQuery: staging dataset"
        R1[orders_raw<br/>100k rows]
        R2[customers_raw<br/>100k rows]
        R3[products_raw<br/>32k rows]
        R4[order_items_raw<br/>112k rows]
        R5[payments_raw<br/>103k rows]
        R6[sellers_raw<br/>3k rows]
        R7[reviews_raw<br/>99k rows]
        R8[geolocation_raw<br/>1M rows]
        R9[translations_raw<br/>71 rows]
        R10[_load_metadata<br/>Audit table]
    end

    subgraph "BigQuery: dev_warehouse_staging dataset"
        S1[stg_orders<br/>VIEW]
        S2[stg_customers<br/>VIEW]
        S3[stg_products<br/>VIEW]
        S4[stg_order_items<br/>VIEW]
        S5[stg_payments<br/>VIEW]
        S6[stg_sellers<br/>VIEW]
        S7[stg_reviews<br/>VIEW]
    end

    subgraph "BigQuery: dev_warehouse_warehouse dataset"
        W1[dim_customer<br/>TABLE<br/>96k rows]
        W2[dim_product<br/>TABLE<br/>32k rows]
        W3[dim_seller<br/>TABLE<br/>3k rows]
        W4[dim_date<br/>TABLE<br/>1.8k rows]
        W5[fact_orders<br/>TABLE<br/>PARTITIONED<br/>96k rows]
        W6[fact_order_items<br/>TABLE<br/>PARTITIONED<br/>112k rows]
    end

    R1 --> S1
    R2 --> S2
    R3 --> S3
    R4 --> S4
    R5 --> S5
    R6 --> S6
    R7 --> S7

    S1 --> W1
    S2 --> W1
    S3 --> W2
    S6 --> W3
    S1 --> W4
    S1 --> W5
    S4 --> W6

    style R1 fill:#fff4e1
    style R2 fill:#fff4e1
    style R3 fill:#fff4e1
    style S1 fill:#e8f5e9
    style S2 fill:#e8f5e9
    style W1 fill:#e3f2fd
    style W5 fill:#fce4ec
    style W6 fill:#fce4ec
```

### Table Partitioning & Clustering

```mermaid
graph TB
    subgraph "fact_orders Optimization"
        A[fact_orders]
        A -->|Partitioned by| B[order_purchase_date<br/>Daily partitions]
        A -->|Clustered by| C[customer_key<br/>order_status]
        B --> D[Efficient date range queries]
        C --> E[Fast customer lookups<br/>Status filtering]
    end

    subgraph "fact_order_items Optimization"
        F[fact_order_items]
        F -->|Partitioned by| G[shipping_limit_date<br/>Daily partitions]
        F -->|Clustered by| H[product_key<br/>seller_key]
        G --> I[Efficient date range queries]
        H --> J[Fast product/seller lookups]
    end

    style B fill:#4285f4,color:#fff
    style C fill:#669df6,color:#fff
    style G fill:#4285f4,color:#fff
    style H fill:#669df6,color:#fff
```

---

## Infrastructure Architecture

### GCP Resource Architecture

```mermaid
graph TB
    subgraph "Google Cloud Project"
        subgraph "IAM & Security"
            SA[Service Account<br/>ds3-pipeline-sa<br/>BigQuery Admin<br/>Storage Admin]
            KEY[JSON Key File<br/>Credentials]
        end

        subgraph "BigQuery"
            DS1[Dataset: staging<br/>Raw Tables<br/>Region: US]
            DS2[Dataset: dev_warehouse_staging<br/>Staging Views<br/>Region: US]
            DS3[Dataset: dev_warehouse_warehouse<br/>Warehouse Tables<br/>Region: US]
            SLOT[BigQuery Slots<br/>On-Demand Pricing]
        end

        subgraph "Cloud Storage - Optional"
            BUCKET[GCS Bucket<br/>Raw Data Archive<br/>Standard Storage<br/>Region: US]
        end

        subgraph "Monitoring - Future"
            LOG[Cloud Logging]
            MON[Cloud Monitoring]
            ALERT[Alerting Policies]
        end
    end

    subgraph "Local Development"
        DEV[Developer Machine<br/>Python Environment<br/>dbt CLI<br/>Dagster]
    end

    subgraph "External Services"
        KAG[Kaggle API<br/>Dataset Source]
    end

    DEV -->|Authenticate| SA
    SA -->|Access| DS1
    SA -->|Access| DS2
    SA -->|Access| DS3
    SA -->|Access| BUCKET
    DEV -->|Download| KAG
    DEV -->|Upload| BUCKET
    DEV -->|Query| DS1

    DS1 -->|Transform| DS2
    DS2 -->|Transform| DS3

    DS1 -.->|Log| LOG
    DS2 -.->|Log| LOG
    DS3 -.->|Log| LOG
    LOG -.->|Metrics| MON
    MON -.->|Trigger| ALERT

    style SA fill:#4285f4,color:#fff
    style DS1 fill:#669df6,color:#fff
    style DS2 fill:#81c784
    style DS3 fill:#ffb74d
```

### Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        D1[Local Machine]
        D2[Git Repository]
        D3[Feature Branch]
    end

    subgraph "CI/CD - Future"
        C1[GitHub Actions]
        C2[dbt Tests]
        C3[Dagster Deploy]
    end

    subgraph "Production Environment - Future"
        P1[Cloud Run<br/>Dagster Server]
        P2[Cloud Scheduler<br/>Cron Trigger]
        P3[BigQuery<br/>Production Datasets]
        P4[Looker Studio<br/>Dashboards]
    end

    D1 -->|Commit| D2
    D2 -->|Push| D3
    D3 -->|PR| C1
    C1 -->|Test| C2
    C2 -->|Pass| C3
    C3 -->|Deploy| P1
    P2 -->|Trigger| P1
    P1 -->|Execute| P3
    P3 -->|Visualize| P4

    style C1 fill:#4285f4,color:#fff
    style C2 fill:#81c784
    style P1 fill:#669df6,color:#fff
```

---

## Security Architecture

### Authentication & Authorization Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Env as .env File
    participant SA as Service Account
    participant IAM as GCP IAM
    participant BQ as BigQuery
    participant GCS as Cloud Storage

    Dev->>Env: Load credentials
    Env->>SA: JSON Key File
    SA->>IAM: Authenticate
    IAM-->>SA: Token granted

    Dev->>BQ: Query request
    BQ->>IAM: Verify permissions
    IAM->>IAM: Check BigQuery Admin role
    IAM-->>BQ: Authorized
    BQ-->>Dev: Query results

    Dev->>GCS: Upload request
    GCS->>IAM: Verify permissions
    IAM->>IAM: Check Storage Admin role
    IAM-->>GCS: Authorized
    GCS-->>Dev: Upload complete
```

### Security Layers

```mermaid
graph TB
    subgraph "Network Security"
        N1[HTTPS Only]
        N2[VPC Future]
    end

    subgraph "Authentication"
        A1[Service Account]
        A2[JSON Key File]
        A3[Environment Variables]
    end

    subgraph "Authorization"
        Z1[IAM Roles]
        Z2[BigQuery Admin]
        Z3[Storage Admin]
        Z4[Least Privilege]
    end

    subgraph "Data Security"
        DS1[Encryption at Rest<br/>Google-managed]
        DS2[Encryption in Transit<br/>TLS 1.3]
        DS3[Access Logs]
        DS4[Audit Trail<br/>_load_metadata]
    end

    subgraph "Secret Management"
        S1[.env File<br/>Gitignored]
        S2[File Permissions<br/>chmod 600]
        S3[Secret Manager<br/>Future]
    end

    N1 --> A1
    A1 --> A2
    A2 --> A3
    A3 --> Z1
    Z1 --> Z2
    Z1 --> Z3
    Z2 --> DS1
    DS1 --> DS2
    DS2 --> DS3
    A2 --> S1
    S1 --> S2

    style A1 fill:#4285f4,color:#fff
    style Z2 fill:#669df6,color:#fff
    style DS1 fill:#81c784
    style S1 fill:#ff8a65
```

### Data Access Patterns

```mermaid
graph LR
    subgraph "Public Access"
        P1[Kaggle API<br/>Public Dataset]
    end

    subgraph "Authenticated Access"
        A1[Developer<br/>Service Account Auth]
        A2[dbt<br/>Service Account Auth]
        A3[Dagster<br/>Service Account Auth]
        A4[Jupyter<br/>Service Account Auth]
    end

    subgraph "Protected Resources"
        R1[BigQuery Tables<br/>IAM Protected]
        R2[Cloud Storage<br/>IAM Protected]
    end

    P1 -->|Public API| A1
    A1 -->|Authorized| R1
    A1 -->|Authorized| R2
    A2 -->|Authorized| R1
    A3 -->|Authorized| R1
    A4 -->|Authorized| R1

    style P1 fill:#81c784
    style R1 fill:#e57373
    style R2 fill:#e57373
```

---

## Performance Optimization

### Query Performance Strategy

```mermaid
graph TB
    subgraph "BigQuery Optimization"
        O1[Partitioning<br/>Time-based partitions<br/>on date columns]
        O2[Clustering<br/>4 clustering columns<br/>for common filters]
        O3[Incremental Models<br/>Only process new data<br/>in dbt]
        O4[Materialized Tables<br/>Pre-aggregated dimensions<br/>& facts]
    end

    subgraph "Performance Impact"
        I1[Reduced Query Cost<br/>70-90% savings]
        I2[Faster Query Time<br/>10-100x speedup]
        I3[Lower Data Processing<br/>Incremental only]
        I4[Efficient Joins<br/>Clustering benefits]
    end

    O1 --> I1
    O1 --> I2
    O2 --> I2
    O2 --> I4
    O3 --> I3
    O4 --> I2
    O4 --> I4

    style O1 fill:#4285f4,color:#fff
    style O2 fill:#669df6,color:#fff
    style O3 fill:#81c784
    style I1 fill:#ffb74d
    style I2 fill:#ffb74d
```

### Data Processing Pipeline

```mermaid
graph LR
    subgraph "Batch Processing"
        B1[Daily Schedule<br/>00:00 UTC]
        B2[Full Refresh<br/>Dimensions]
        B3[Incremental Load<br/>Facts]
        B4[Parallel Execution<br/>dbt threads: 4]
    end

    subgraph "Performance Metrics"
        M1[Ingestion: 2-3 min]
        M2[dbt Run: 30 sec]
        M3[Total: 5 min]
        M4[Data Freshness: Daily]
    end

    B1 --> B2
    B1 --> B3
    B2 --> B4
    B3 --> B4
    B4 --> M1
    M1 --> M2
    M2 --> M3
    M3 --> M4

    style B1 fill:#4285f4,color:#fff
    style M3 fill:#81c784
```

---

## Scalability Considerations

```mermaid
graph TB
    subgraph "Current Scale"
        C1[100k orders]
        C2[112k order items]
        C3[100k customers]
        C4[5 min pipeline]
    end

    subgraph "Future Scale 10x"
        F1[1M orders]
        F2[1.1M order items]
        F3[1M customers]
        F4[10-15 min pipeline]
    end

    subgraph "Future Scale 100x"
        F5[10M orders]
        F6[11M order items]
        F7[10M customers]
        F8[30-60 min pipeline]
    end

    subgraph "Scaling Strategies"
        S1[Increase dbt threads<br/>4 → 8 → 16]
        S2[Partition by month<br/>Instead of day]
        S3[Add more clustering<br/>columns]
        S4[Use dbt snapshots<br/>for SCD Type 2]
        S5[Implement data marts<br/>for aggregations]
        S6[Add Cloud Run<br/>for distributed processing]
    end

    C1 -->|10x growth| F1
    F1 -->|Apply| S1
    F1 -->|Apply| S2

    F1 -->|10x growth| F5
    F5 -->|Apply| S3
    F5 -->|Apply| S4
    F5 -->|Apply| S5
    F5 -->|Apply| S6

    style C1 fill:#81c784
    style F1 fill:#ffb74d
    style F5 fill:#e57373
```

---

## Summary: Architecture Principles

### Design Principles

1. **Modularity**: Each component (ingestion, transformation, analytics) is independent and reusable
2. **Idempotency**: All operations can be safely re-run without duplicating data
3. **Scalability**: BigQuery and dbt scale horizontally with data growth
4. **Maintainability**: Clear separation of concerns, comprehensive testing
5. **Cost Efficiency**: Optimized with partitioning, clustering, and incremental models
6. **Data Quality**: Automated testing at every layer, audit trails
7. **Cloud Native**: Leverages managed services (BigQuery, GCS) for reliability

### Key Technologies Justification

| Technology | Why Chosen | Alternative |
|------------|-----------|-------------|
| **BigQuery** | Serverless, scales automatically, no infrastructure | Snowflake, Redshift |
| **dbt** | SQL-based, version control, testing framework | Custom Python, Dataform |
| **Dagster** | Modern orchestration, asset-based, great UI | Airflow, Prefect |
| **Python** | Rich ecosystem, GCP SDKs, data processing | Scala, Java |
| **GCS** | Native integration with BigQuery, cheap storage | S3, Azure Blob |

---

## Diagram Legend

**Node Colors:**
- 🔵 Blue: External services, ingestion
- 🟡 Yellow: Raw data, sources
- 🟢 Green: Staging, intermediate processing
- 🟠 Orange: Dimensions, analytics-ready
- 🔴 Red: Facts, final data products
- 🟣 Purple: Orchestration, monitoring

**Line Types:**
- Solid arrow (→): Data flow, dependencies
- Dashed arrow (⇢): Optional flow, future enhancements
- Bold arrow (⟹): Critical path

---

## Additional Resources

**Interactive Diagrams:**
- dbt docs: Run `dbt docs serve` for interactive lineage
- Dagster UI: http://localhost:3000 for live asset graph
- BigQuery Console: Visual query execution plans

**Documentation:**
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [BigQuery Schema Design](https://cloud.google.com/bigquery/docs/best-practices-performance-overview)
- [Dagster Concepts](https://docs.dagster.io/concepts)

---

## Architecture Review Checklist

- [x] Clear separation of raw, staging, and warehouse layers
- [x] Star schema design with proper surrogate keys
- [x] Partitioning and clustering for performance
- [x] Incremental models for efficient updates
- [x] Comprehensive data quality testing
- [x] Idempotent ingestion with audit trails
- [x] Service account with least privilege access
- [x] Version controlled transformations (dbt + Git)
- [x] Orchestrated pipeline with dependency management
- [x] Scalable architecture for future growth
