# 🚀 Quick Start Guide - Brazilian Sales Analytics

**For class presentation preparation**

---

## ⚡ 5-Minute Setup

```bash
# 1. Clone and navigate to project
cd DS3-Project-Team

# 2. Create environment file
cp .env.example .env
# Edit .env with your credentials (GCP, Kaggle)

# 3. Run setup script
bash scripts/setup_environment.sh

# 4. Test the pipeline
python scripts/run_pipeline.py --extract    # Test extraction
python scripts/run_pipeline.py --full       # Run full pipeline

# 5. Launch dashboard
streamlit run visualization/dashboard.py
```

---

## 📊 Project Structure Overview

```
brazilian-sales-analytics/
│
├── pipeline/
│   ├── extract/         # Data extraction (Kaggle + BCB)
│   ├── load/            # Meltano → BigQuery
│   └── transform/       # dbt models
│
├── orchestration/       # Dagster scheduling
├── visualization/       # Streamlit dashboard
├── scripts/             # Utility scripts
└── docs/                # Documentation
```

---

## 🎯 Essential Commands

### Run Complete Pipeline
```bash
python scripts/run_pipeline.py --full
```

### Run Individual Stages
```bash
# Extract data
python scripts/run_pipeline.py --extract

# Load to BigQuery
python scripts/run_pipeline.py --load

# Run dbt transformations
python scripts/run_pipeline.py --transform
```

### dbt Commands
```bash
cd pipeline/transform

# Run models
dbt run --profiles-dir .

# Run tests
dbt test --profiles-dir .

# Generate documentation
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

### Dashboard
```bash
streamlit run visualization/dashboard.py
# Visit http://localhost:8501
```

### Dagster Orchestration
```bash
dagster dev -f orchestration/dagster/dagster_definitions.py
# Visit http://localhost:3000
```

---

## 📝 For Presentation

**Must-Read Documents:**
1. `README_UNIFIED.md` - Complete project overview
2. `docs/PRESENTATION_GUIDE.md` - Step-by-step presentation walkthrough
3. `REFACTORING_SUMMARY.md` - What was changed and why

**Demo Checklist:**
- [ ] Environment configured (`.env`)
- [ ] Pipeline runs successfully
- [ ] BigQuery tables populated
- [ ] Dashboard launches
- [ ] Talking points prepared

---

## 🆘 Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements_unified.txt
```

### "Meltano command not found"
```bash
cd pipeline/load
meltano install
```

### "dbt compilation error"
```bash
# Check environment variables in .env
# Verify GCP credentials are valid
cd pipeline/transform
dbt debug --profiles-dir .
```

### "BigQuery authentication failed"
```bash
# Verify GOOGLE_APPLICATION_CREDENTIALS in .env
# Check service account has BigQuery permissions
```

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `scripts/run_pipeline.py` | Master orchestration script |
| `pipeline/extract/kaggle_extract.py` | Kaggle data extraction |
| `pipeline/extract/bcb_extract.py` | Economic data extraction |
| `pipeline/load/meltano.yml` | Meltano configuration |
| `pipeline/transform/dbt_project.yml` | dbt configuration |
| `visualization/dashboard.py` | Streamlit dashboard |
| `.env` | Environment configuration |

---

## 🎓 Presentation Flow

1. **Introduction** (2 min)
   - Show architecture diagram
   - Explain business problem

2. **Live Demo** (5 min)
   - Run pipeline: `python scripts/run_pipeline.py --full`
   - Show BigQuery results
   - Launch dashboard

3. **Technical Deep Dive** (3 min)
   - Show dbt model
   - Explain transformation logic
   - Highlight code quality

4. **Insights** (3 min)
   - Navigate dashboard
   - Show economic correlations
   - Discuss business value

5. **Q&A** (5 min)
   - Use `docs/PRESENTATION_GUIDE.md` for answers

---

## ✅ Pre-Presentation Checklist

**30 Minutes Before:**
- [ ] Test full pipeline run
- [ ] Verify dashboard loads
- [ ] Open BigQuery console
- [ ] Review presentation guide
- [ ] Prepare backup screenshots

**During Presentation:**
- [ ] Focus on "why" not just "what"
- [ ] Show live demos when possible
- [ ] Connect technical details to business value
- [ ] Keep to time (15-20 minutes)

---

## 🔗 Useful Links

- **BigQuery Console:** https://console.cloud.google.com/bigquery
- **Kaggle Dataset:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **BCB API Docs:** https://www.bcb.gov.br/api/servico/sitebcb
- **dbt Docs:** https://docs.getdbt.com/
- **Dagster Docs:** https://docs.dagster.io/

---

**You're ready to present! Good luck! 🎉**
