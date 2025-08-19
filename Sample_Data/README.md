# Sample Data Structure for Clinical Dashboard

## Directory Structure

```
Sample_Data/
├── Medidata_Rave/          # Medidata Rave EDC exports
│   ├── demographics.csv    # DM domain - Subject demographics
│   ├── adverse_events.csv  # AE domain - Adverse events
│   ├── lab_results.csv     # LB domain - Laboratory results
│   └── vital_signs.csv     # VS domain - Vital signs
│
├── Veeva_Vault/            # Veeva Vault EDC exports
│   ├── subjects.csv        # Subject enrollment data
│   ├── sae_log.csv        # Serious Adverse Events
│   ├── protocol_deviations.csv
│   └── enrollment_status.csv
│
└── README_FILES/           # Documentation
    ├── data_dictionary.xlsx
    └── mapping_rules.json
```

## Expected File Formats

### Medidata Rave Files (CDISC SDTM-like)
These files should follow CDISC SDTM naming conventions:

#### demographics.csv
Required columns:
- USUBJID (Unique Subject Identifier)
- SUBJID (Subject ID)
- SITEID (Site ID)
- AGE (Age at enrollment)
- SEX (M/F)
- RACE
- ARM (Treatment Arm)
- ARMCD (Arm Code)

#### adverse_events.csv
Required columns:
- USUBJID
- AETERM (Adverse Event Term)
- AESEV (Severity: MILD/MODERATE/SEVERE)
- AESER (Serious: Y/N)
- AESTDTC (Start Date)
- AEENDTC (End Date)

#### lab_results.csv
Required columns:
- USUBJID
- LBTEST (Lab Test Name)
- LBORRES (Original Result)
- LBORRESU (Original Units)
- VISITNUM (Visit Number)
- LBDTC (Date/Time of Collection)

### Veeva Vault Files
These files may have custom naming:

#### subjects.csv
Expected columns:
- subject_id
- site_id
- enrollment_date
- status (ENROLLED/COMPLETED/DISCONTINUED)
- discontinuation_reason

#### sae_log.csv
Expected columns:
- subject_id
- event_description
- onset_date
- severity
- outcome
- relationship_to_study

## Data Volume Guidelines

For testing different scenarios:
- **Small Dataset**: 100-500 subjects (for quick testing)
- **Medium Dataset**: 1,000-10,000 subjects (typical study)
- **Large Dataset**: 100,000+ rows (stress testing)

## Sample Data Generation

If you need sample data for testing, use this Python script:

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Generate sample demographics
def generate_demographics(n_subjects=100):
    data = {
        'USUBJID': [f'STUDY001-{i:04d}' for i in range(1, n_subjects+1)],
        'SUBJID': [f'{i:04d}' for i in range(1, n_subjects+1)],
        'SITEID': [f'SITE{random.randint(1,5):02d}' for _ in range(n_subjects)],
        'AGE': np.random.normal(45, 12, n_subjects).astype(int),
        'SEX': np.random.choice(['M', 'F'], n_subjects),
        'RACE': np.random.choice(['WHITE', 'BLACK', 'ASIAN', 'OTHER'], n_subjects),
        'ARM': np.random.choice(['TREATMENT', 'PLACEBO'], n_subjects),
        'ARMCD': np.random.choice(['TRT', 'PBO'], n_subjects)
    }
    return pd.DataFrame(data)

# Save to CSV
df = generate_demographics(100)
df.to_csv('Sample_Data/Medidata_Rave/demographics.csv', index=False)
```

## KPI Priority Metrics

Based on requirements, focus on these KPIs first:

1. **Enrollment Rate**
   - Data source: demographics.csv or subjects.csv
   - Calculation: COUNT(USUBJID) by enrollment_date

2. **SAE Count**
   - Data source: adverse_events.csv or sae_log.csv
   - Calculation: COUNT(AESER='Y') or COUNT(severity='SERIOUS')

## Auto-Mapping Patterns

The system will automatically detect these patterns:
- USUBJID, subject_id → Subject Identifier
- AESER='Y', severity='SERIOUS' → Serious Adverse Event
- enrollment_date, RFSTDTC → Enrollment Date
- ARM, treatment_group → Treatment Assignment

Place your EDC export files in the appropriate folders and the system will automatically:
1. Detect the file format
2. Map fields to standard names
3. Create appropriate visualizations
4. Generate KPI metrics