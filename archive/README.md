# Archive Directory

This directory contains the original module structures that were combined into the unified project structure.

## Original Modules

### Module 1: `olist_transform/`

**Purpose**: Basic ELT pipeline for Olist Brazilian E-Commerce data

**Components**:
- 7 dbt models (4 staging, 3 marts)
- Basic transformations
- Meltano configuration for loading

**Key Features**:
- First iteration of the pipeline
- Foundational data models
- Simple fact and dimension tables

**Status**: Archived - Models migrated to unified `transform/` directory

---

### Module 2: `Module_2_Brazilian-sales/`

**Purpose**: Production-grade analytics platform with economic context

**Components**:
- 10 dbt models (5 staging, 5 marts including v2 versions)
- Dagster orchestration
- Streamlit dashboard
- BCB API integration
- Comprehensive documentation

**Key Features**:
- Economic indicator integration
- Advanced mart models with v2 iterations
- Automated orchestration
- Interactive visualization
- Dual-language support

**Status**: Archived - Components migrated to unified structure

---

## Migration Details

**Date**: December 15, 2025

**Unified Structure**:
```
DS3-Project-Team/
├── extract/          # Combined extraction scripts from both modules
├── transform/        # Best models from both modules
├── orchestration/    # Dagster from Module 2
├── dashboard/        # Streamlit from Module 2
└── config/           # Centralized configuration
```

**Migration Decisions**:
- **Staging models**: Used Module 2's superior models (better SAFE_CAST, more fields)
- **Mart models**: Used Module 2's v2 versions (improved performance)
- **Reviews model**: Kept unique model from Module 1
- **Orchestration**: Adopted Dagster from Module 2
- **Visualization**: Used English version of dashboard from Module 2

---

## Reference Information

### Why Archive?

These modules are preserved for:
- **Historical reference**: Understanding the evolution of the project
- **Comparison**: Seeing improvements from v1 to v2
- **Learning**: Reviewing different approaches to same problems
- **Backup**: Safety net if unified structure needs adjustments

### Do Not Use

❌ **Do not** use these archived modules for active development
❌ **Do not** run these pipelines (may conflict with unified structure)
❌ **Do not** update dependencies here

✅ **Do** refer to them for understanding design decisions
✅ **Do** compare implementations
✅ **Do** use for documentation purposes

---

## Migration History

**Phase 1-6** (Completed):
- Security & cleanup
- New directory structure
- Code consolidation
- Environment variable migration
- Requirements merge

**Phase 7-9** (Completed):
- Documentation
- Helper scripts
- Archiving

**Result**:
- Single unified codebase
- Production-ready structure
- Presentation-ready documentation

---

## For More Information

See the main [README.md](../README.md) for the unified project structure and usage instructions.

---

**Last Updated**: December 2025
**Archive Purpose**: Reference and historical preservation
**Active Project**: See parent directory
