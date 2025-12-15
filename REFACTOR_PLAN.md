# Unified Pipeline Refactoring Plan

## Current State Analysis

### Root Project (olist_transform)
- ✅ Kaggle data extraction (`src/extract/kaggle_extract.py`)
- ✅ Meltano configuration for CSV → BigQuery
- ⚠️  Basic dbt models (incomplete, uses JSON parsing)
- ❌ No orchestration
- ❌ No visualization

### Module_2_Brazilian-sales
- ✅ Complete dbt project with staging + marts
- ✅ Economic indicators integration (BCB API)
- ✅ Dagster orchestration
- ✅ Streamlit dashboard (bilingual)
- ✅ Docker deployment
- ✅ Comprehensive documentation
- ❌ Assumes PostgreSQL source (not Kaggle/CSV)

## Unified Architecture

```
brazilian-sales-analytics/
├── pipeline/
│   ├── extract/
│   │   ├── kaggle_extract.py        # Extract from Kaggle
│   │   └── bcb_extract.py            # Extract BCB economic data
│   ├── load/
│   │   └── meltano.yml               # Meltano ELT config
│   └── transform/
│       └── dbt/                      # dbt models (from Module_2)
│           ├── models/
│           │   ├── staging/
│           │   └── marts/
│           ├── tests/
│           └── dbt_project.yml
├── orchestration/
│   └── dagster/                      # Dagster orchestration
│       ├── assets.py
│       ├── definitions.py
│       └── dagster.yaml
├── visualization/
│   └── streamlit_dashboard.py        # Interactive dashboard
├── deployment/
│   ├── docker-compose.yml
│   └── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   └── PRESENTATION.md
├── scripts/
│   ├── run_full_pipeline.py          # Master orchestration script
│   ├── setup_environment.sh
│   └── verify_data.py
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Implementation Steps

### Phase 1: Consolidate dbt Models
1. Move Module_2 dbt project to `pipeline/transform/dbt/`
2. Update source configurations for BigQuery raw tables
3. Ensure all models reference correct datasets
4. Add missing staging models (sellers, payments, geolocation)

### Phase 2: Unify Extraction Layer
1. Keep `kaggle_extract.py` as primary data source
2. Add `bcb_extract.py` for economic indicators
3. Create unified extraction orchestrator

### Phase 3: Reorganize Structure
1. Move Dagster to `orchestration/dagster/`
2. Move Streamlit to `visualization/`
3. Create `scripts/` for utility scripts
4. Consolidate documentation in `docs/`

### Phase 4: Create Master Pipeline Script
1. `run_full_pipeline.py` that executes:
   - Extract (Kaggle + BCB)
   - Load (Meltano → BigQuery)
   - Transform (dbt run + dbt test)
   - Validate (data quality checks)
2. Support for partial runs (--extract-only, --transform-only, etc.)

### Phase 5: Documentation
1. Updated README with quick start
2. Architecture diagram
3. Presentation guide for class demo
4. Setup instructions

### Phase 6: Testing
1. End-to-end pipeline test
2. dbt model tests
3. Data quality validation

## Benefits for Presentation

1. **Clear Structure**: Logical organization by pipeline stage
2. **Complete Pipeline**: Extract → Load → Transform → Visualize
3. **Modern Stack**: Kaggle + Meltano + dbt + Dagster + Streamlit
4. **Production-Ready**: Docker deployment, orchestration, monitoring
5. **Documented**: Comprehensive docs for demo and questions
6. **Reproducible**: Single command to run entire pipeline
