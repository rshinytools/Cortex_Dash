# Widget System Complete Workflow Summary

## Quick Reference Guide

### 🎯 System Overview
```
Widget Library → Dashboard Template → Study Initialization → Live Dashboard
     ↓                   ↓                    ↓                    ↓
Define Widget       Place Widgets      Configure Data        View Metrics
Capabilities        on Canvas          Map to Datasets       Auto-refresh
```

## 📊 Phase 1: Widget Library (Admin)

### Create MetricCard Widget Definition
```
Widget: MetricCard
├── Capabilities:
│   ├── Aggregations: COUNT, COUNT DISTINCT, SUM, AVG, MIN, MAX, MEDIAN
│   ├── Filters: Complex AND/OR logic
│   ├── Comparisons: vs Previous Extract
│   └── Formats: Number, Percentage, Currency
└── No data mapping yet - just capabilities!
```

## 🎨 Phase 2: Dashboard Template (Admin)

### Design Dashboard Structure
```
Safety Dashboard Template
├── Overview (Menu Type: Dashboard Page)
│   ├── Total Screened [MetricCard]
│   ├── Total AEs [MetricCard]
│   └── SAEs [MetricCard]
├── Safety Monitoring (Menu Type: Group)
│   ├── AE Details (Dashboard Page)
│   └── SAE Analysis (Dashboard Page)
└── Resources (Menu Type: Group)
    └── Protocol (External Link)
```

**Key Point**: Only configure display properties (title, position) - NO data mapping!

## 🔧 Phase 3: Study Initialization (System Admin)

### Step 1: Data Source Upload
```
Upload: study_data.zip
         ↓
Extract: DM.sas7bdat, AE.sas7bdat, DS.csv...
         ↓
Convert: DM.parquet, AE.parquet, DS.parquet...
         ↓
Store:   /data/studies/STUDY-001/source_data/2024-01-10_143000/processed/
```

### Step 2: Data Pipeline (Optional)
```
Upload Scripts:
├── ADSL.py (uses: DM, DS → creates: ADSL)
└── ADAE.py (uses: AE, ADSL → creates: ADAE)
         ↓
Version: v1 (pending activation)
         ↓
Admin: Review & Activate v1
         ↓
Run: Execute scripts
         ↓
Output: /transformed_data/2024-01-10_145000/
```

### Step 3: Widget Data Mapping
For each widget in template:

```
Widget: "Total AEs"
├── Dataset: AE (from source_data)
├── Aggregation: COUNT
├── Filters:
│   └── AETERM is not null
├── Unique By: [not selected]
└── Comparison: Enable (vs last extract)
```

```
Widget: "Total Subjects with AEs"
├── Dataset: AE
├── Aggregation: COUNT DISTINCT
├── Unique By: USUBJID
├── Filters:
│   └── AETERM is not null
└── Comparison: Enable
```

## 📈 Phase 4: Live Dashboard

### Automatic Data Flow
```
New Data Upload → Convert to Parquet → Scripts Auto-run → Widgets Refresh
                                                ↓
                                    Admin activates new version
```

### Widget Display
```
┌─────────────────────┐
│   Total AEs         │
│     4,332           │
│   +1.93% ▲          │
│   vs last month     │
└─────────────────────┘
```

## 🔄 Data Update Workflow

### Monthly Data Update Process
1. **Admin uploads new data**: `study_data_month2.zip`
2. **System converts**: Creates new timestamped folder
3. **Validation**: Check if mapped columns exist
4. **If columns missing**: 
   - Alert admin
   - Show missing columns
   - Admin fixes mapping or uploads correct data
5. **Widgets auto-refresh**: Point to latest data version
6. **Comparisons calculate**: Current vs previous extract

## 📁 Folder Structure Summary
```
/data/studies/STUDY-001/
├── source_data/
│   ├── 2024-01-10_143000/    # First upload
│   │   ├── raw/
│   │   └── processed/
│   └── 2024-02-10_143000/    # Monthly update
│       ├── raw/
│       └── processed/
├── pipelines/
│   ├── scripts/
│   │   ├── v1/               # Initial scripts
│   │   └── v2/               # Updated scripts
│   └── active_version.json
└── transformed_data/
    ├── 2024-01-10_145000/    # From v1 scripts
    └── 2024-02-10_145000/    # From v2 scripts
```

## 🚀 Key Features

### For Widget Creation
- ✅ No SDTM/ADaM constraints
- ✅ Works with any column names
- ✅ Flexible aggregations
- ✅ Complex filter logic

### For Data Management
- ✅ Version controlled scripts
- ✅ Manual activation (controlled)
- ✅ Automatic widget refresh
- ✅ Full audit trail

### For Performance
- ✅ Parquet format (fast queries)
- ✅ Redis caching
- ✅ Background processing
- ✅ Handles 100k+ rows

## 🛠️ Admin Controls
- Only system admin can:
  - Upload data
  - Create/edit transformation scripts
  - Activate script versions
  - Configure widget mappings
  - Update data sources

## ⚡ Quick Commands

### Check Study Data Status
```python
GET /api/v1/studies/{study_id}/data-source/status
```

### Run Pipeline
```python
POST /api/v1/studies/{study_id}/pipeline/run
```

### Test Widget Mapping
```python
POST /api/v1/studies/{study_id}/widgets/test
{
  "dataset": "AE",
  "aggregation": "COUNT",
  "filters": [...]
}
```

### Refresh All Widgets
```python
POST /api/v1/studies/{study_id}/widgets/refresh-all
```

## 📋 Next Steps
1. Start with Phase 1 implementation
2. Build MetricCard widget
3. Test with sample data
4. Iterate based on feedback