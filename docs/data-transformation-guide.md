# Data Transformation Guide

## Overview

The Data Transformation feature allows you to create derived datasets using Python scripts during the study initialization process. This powerful feature enables you to:

- Generate analysis datasets (ADSL, ADAE, etc.) from SDTM data
- Create custom aggregations and summaries
- Apply complex business logic to your data
- Merge multiple datasets into unified views
- Calculate derived variables and metrics

## Architecture

### Security Model

All transformation scripts run in a sandboxed environment with the following restrictions:

- **No file system access**: Scripts cannot read or write files
- **No network access**: Scripts cannot make HTTP requests or access external resources
- **No imports**: Only pre-approved libraries (pandas, numpy) are available
- **Resource limits**: Memory (512MB), CPU time (5 minutes), and output size (100MB) are limited
- **Namespace isolation**: Scripts run in a restricted namespace with limited built-ins

### Execution Flow

1. **Script Validation**: Scripts are validated for security violations before execution
2. **Data Loading**: Input datasets are loaded from the study's parquet files
3. **Script Execution**: The transformation runs in an isolated environment
4. **Output Validation**: Results are validated for structure and size
5. **Data Storage**: Output is saved as a new parquet file in the transformed directory

## Writing Transformations

### Available Variables

Within your transformation script, you have access to:

- `df`: The primary dataframe (first input dataset or merged result)
- `pd`: Pandas library for data manipulation
- `np`: NumPy library for numerical operations
- Individual dataset names (e.g., `dm`, `ae`, `lb`) when multiple inputs are selected

### Basic Examples

#### 1. Simple Calculated Column
```python
# Add BMI calculation to demographics
df['bmi'] = df['WEIGHT'] / (df['HEIGHT'] / 100) ** 2
```

#### 2. Age Categorization
```python
# Create age groups
df['age_group'] = pd.cut(df['AGE'], 
                         bins=[0, 18, 65, 100], 
                         labels=['Pediatric', 'Adult', 'Elderly'])
```

#### 3. Merging Datasets
```python
# When selecting both 'dm' and 'ae' as inputs
# The datasets are available as separate variables
merged = pd.merge(dm, ae, on='USUBJID', how='left')
df = merged.copy()
df['has_ae'] = ~df['AETERM'].isna()
```

## Advanced Examples

### Creating ADSL (Subject-Level Analysis Dataset)

```python
# Start with demographics
adsl = dm.copy()

# Add treatment information if available
if 'ex' in locals():
    # Get first and last dose dates
    first_dose = ex.groupby('USUBJID')['EXSTDTC'].min().reset_index()
    first_dose.columns = ['USUBJID', 'TRTSDT']
    
    last_dose = ex.groupby('USUBJID')['EXENDTC'].max().reset_index()
    last_dose.columns = ['USUBJID', 'TRTEDT']
    
    adsl = pd.merge(adsl, first_dose, on='USUBJID', how='left')
    adsl = pd.merge(adsl, last_dose, on='USUBJID', how='left')

# Add safety population flag
adsl['SAFFL'] = 'Y'  # All subjects who received at least one dose

# Add ITT population flag
adsl['ITTFL'] = 'Y'  # All randomized subjects

# Calculate age at enrollment
if 'BRTHDT' in adsl.columns:
    adsl['AGE'] = (pd.to_datetime(adsl['RFSTDTC']) - pd.to_datetime(adsl['BRTHDT'])).dt.days / 365.25

# Add baseline characteristics from vital signs
if 'vs' in locals():
    baseline_vs = vs[vs['VISIT'] == 'BASELINE']
    
    # Pivot vital signs to wide format
    baseline_wide = baseline_vs.pivot_table(
        index='USUBJID',
        columns='VSTESTCD',
        values='VSORRES',
        aggfunc='first'
    ).reset_index()
    
    # Rename columns with baseline prefix
    baseline_wide.columns = ['USUBJID'] + [f'BASE{col}' for col in baseline_wide.columns[1:]]
    
    adsl = pd.merge(adsl, baseline_wide, on='USUBJID', how='left')

# Add adverse event summary flags
if 'ae' in locals():
    # Any AE flag
    ae_subjects = ae['USUBJID'].unique()
    adsl['AEFL'] = adsl['USUBJID'].isin(ae_subjects).map({True: 'Y', False: 'N'})
    
    # Serious AE flag
    sae_subjects = ae[ae['AESER'] == 'Y']['USUBJID'].unique()
    adsl['SAEFL'] = adsl['USUBJID'].isin(sae_subjects).map({True: 'Y', False: 'N'})
    
    # Treatment-related AE flag
    rel_ae_subjects = ae[ae['AEREL'].isin(['RELATED', 'POSSIBLY RELATED'])]['USUBJID'].unique()
    adsl['RELAEFL'] = adsl['USUBJID'].isin(rel_ae_subjects).map({True: 'Y', False: 'N'})

# Set final dataframe
df = adsl
```

### Creating ADAE (Adverse Event Analysis Dataset)

```python
# Start with adverse events
adae = ae.copy()

# Merge with demographics for baseline characteristics
adae = pd.merge(adae, dm[['USUBJID', 'AGE', 'SEX', 'RACE']], on='USUBJID', how='left')

# Calculate duration of AE
adae['AESTDT'] = pd.to_datetime(adae['AESTDTC'])
adae['AEENDT'] = pd.to_datetime(adae['AEENDTC'])
adae['AEDUR'] = (adae['AEENDT'] - adae['AESTDT']).dt.days + 1

# Add treatment emergent flag
if 'ex' in locals():
    # Get first dose date per subject
    first_dose = ex.groupby('USUBJID')['EXSTDTC'].min().reset_index()
    first_dose.columns = ['USUBJID', 'TRTSDT']
    first_dose['TRTSDT'] = pd.to_datetime(first_dose['TRTSDT'])
    
    adae = pd.merge(adae, first_dose, on='USUBJID', how='left')
    
    # Treatment emergent = AE started on or after first dose
    adae['TRTEMFL'] = (adae['AESTDT'] >= adae['TRTSDT']).map({True: 'Y', False: 'N'})
else:
    adae['TRTEMFL'] = 'Y'  # Default if no exposure data

# Standardize severity
severity_map = {
    'MILD': 1,
    'MODERATE': 2,
    'SEVERE': 3
}
adae['AESEVN'] = adae['AESEV'].map(severity_map)

# Add analysis flags
adae['ANL01FL'] = 'Y'  # Include in primary analysis
adae['ANL02FL'] = adae['TRTEMFL']  # Include in TEAE analysis

# Create preferred term categories
# This would normally use MedDRA coding
adae['AEBODSYS'] = 'PLACEHOLDER BODY SYSTEM'  # Would map from AEDECOD
adae['AESOC'] = 'PLACEHOLDER SOC'  # System Organ Class

# Add time to event variables
if 'TRTSDT' in adae.columns:
    adae['ASTDY'] = (adae['AESTDT'] - adae['TRTSDT']).dt.days + 1
    adae['AENDY'] = (adae['AEENDT'] - adae['TRTSDT']).dt.days + 1

# Set final dataframe
df = adae
```

### Laboratory Data Analysis

```python
# Analyze laboratory results
lab_analysis = lb.copy()

# Convert results to numeric
lab_analysis['LBSTRESN'] = pd.to_numeric(lab_analysis['LBORRES'], errors='coerce')

# Calculate change from baseline
baseline = lab_analysis[lab_analysis['VISIT'] == 'BASELINE'][['USUBJID', 'LBTESTCD', 'LBSTRESN']]
baseline.columns = ['USUBJID', 'LBTESTCD', 'BASE']

lab_analysis = pd.merge(lab_analysis, baseline, on=['USUBJID', 'LBTESTCD'], how='left')
lab_analysis['CHG'] = lab_analysis['LBSTRESN'] - lab_analysis['BASE']
lab_analysis['PCHG'] = (lab_analysis['CHG'] / lab_analysis['BASE']) * 100

# Flag clinically significant abnormalities
# Define normal ranges (example values)
normal_ranges = {
    'ALT': (10, 40),
    'AST': (10, 35),
    'BILI': (0.3, 1.2),
    'CREAT': (0.7, 1.3)
}

def check_abnormal(row):
    if row['LBTESTCD'] in normal_ranges:
        low, high = normal_ranges[row['LBTESTCD']]
        if pd.notna(row['LBSTRESN']):
            if row['LBSTRESN'] < low:
                return 'LOW'
            elif row['LBSTRESN'] > high:
                return 'HIGH'
    return 'NORMAL'

lab_analysis['ANRIND'] = lab_analysis.apply(check_abnormal, axis=1)

# Identify worst post-baseline value per subject/test
post_baseline = lab_analysis[lab_analysis['VISIT'] != 'BASELINE']
worst_values = post_baseline.loc[post_baseline.groupby(['USUBJID', 'LBTESTCD'])['LBSTRESN'].idxmax()]

df = lab_analysis
```

### Complex Aggregations

```python
# Create summary statistics by visit and treatment
if 'ex' in locals() and 'vs' in locals():
    # Assign treatment groups based on exposure
    trt_groups = ex.groupby('USUBJID')['EXTRT'].first().reset_index()
    trt_groups.columns = ['USUBJID', 'TRT01P']
    
    # Merge with vital signs
    vs_trt = pd.merge(vs, trt_groups, on='USUBJID', how='left')
    
    # Calculate summary statistics
    summary = vs_trt.groupby(['TRT01P', 'VISIT', 'VSTESTCD'])['VSORRES'].agg([
        'count', 'mean', 'std', 'min', 'max'
    ]).reset_index()
    
    # Add categorical summaries for abnormal values
    abnormal_counts = vs_trt[vs_trt['VSSTAT'] == 'ABNORMAL'].groupby(
        ['TRT01P', 'VISIT', 'VSTESTCD']
    ).size().reset_index(name='n_abnormal')
    
    summary = pd.merge(summary, abnormal_counts, 
                       on=['TRT01P', 'VISIT', 'VSTESTCD'], 
                       how='left')
    summary['n_abnormal'] = summary['n_abnormal'].fillna(0)
    
    df = summary
```

## Best Practices

### 1. Data Validation

Always validate your inputs and handle missing data:

```python
# Check for required columns
required_cols = ['USUBJID', 'AGE', 'SEX']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

# Handle missing values appropriately
df['AGE'] = pd.to_numeric(df['AGE'], errors='coerce')
df['AGE_CAT'] = pd.cut(df['AGE'].fillna(df['AGE'].median()), 
                       bins=[0, 65, 100], 
                       labels=['<65', '>=65'])
```

### 2. Memory Efficiency

Work with large datasets efficiently:

```python
# Use categorical data types for repeated strings
df['VISIT'] = df['VISIT'].astype('category')
df['SEX'] = df['SEX'].astype('category')

# Process in chunks if needed
chunk_size = 10000
processed_chunks = []
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    # Process chunk
    processed_chunks.append(process_chunk(chunk))
df = pd.concat(processed_chunks)
```

### 3. Error Handling

Include appropriate error handling:

```python
try:
    # Attempt merge
    df = pd.merge(dm, ae, on='USUBJID', how='left')
except KeyError as e:
    # Handle missing key column
    print(f"Merge failed: {e}")
    df = dm.copy()  # Fallback to demographics only
except Exception as e:
    # Handle other errors
    print(f"Unexpected error: {e}")
    raise
```

### 4. Documentation

Document your transformations:

```python
# TRANSFORMATION: Create ADSL dataset
# Purpose: Generate subject-level analysis dataset for statistical analysis
# Input: dm (demographics), ae (adverse events), ex (exposure)
# Output: One record per subject with analysis flags and derived variables
# Version: 1.0
# Date: 2024-01-15

# Step 1: Initialize with demographics
adsl = dm.copy()

# Step 2: Add treatment information
# ... rest of transformation
```

## Common Patterns

### 1. First/Last Observation
```python
# Get first and last values per subject
first_value = df.sort_values(['USUBJID', 'VISITNUM']).groupby('USUBJID').first()
last_value = df.sort_values(['USUBJID', 'VISITNUM']).groupby('USUBJID').last()
```

### 2. Window Functions
```python
# Calculate running averages
df['ROLLING_AVG'] = df.groupby('USUBJID')['VALUE'].transform(
    lambda x: x.rolling(window=3, min_periods=1).mean()
)
```

### 3. Pivot Operations
```python
# Reshape data from long to wide
wide_df = df.pivot_table(
    index='USUBJID',
    columns='VISIT',
    values='LBSTRESN',
    aggfunc='mean'
).reset_index()
```

### 4. Date Calculations
```python
# Calculate days between dates
df['START_DATE'] = pd.to_datetime(df['START_DATE'])
df['END_DATE'] = pd.to_datetime(df['END_DATE'])
df['DURATION_DAYS'] = (df['END_DATE'] - df['START_DATE']).dt.days
```

## Troubleshooting

### Common Errors

1. **KeyError**: Column not found
   - Check column names match exactly (case-sensitive)
   - Verify the input dataset contains expected columns

2. **MemoryError**: Dataset too large
   - Process data in chunks
   - Drop unnecessary columns early
   - Use more efficient data types

3. **Security Violation**: Forbidden operation
   - Remove import statements
   - Don't access file system
   - Use only approved functions

4. **Timeout**: Script took too long
   - Optimize loops and operations
   - Reduce dataset size if possible
   - Simplify complex calculations

### Performance Tips

1. **Vectorize operations** instead of loops:
   ```python
   # Good
   df['new_col'] = df['col1'] * 2 + df['col2']
   
   # Avoid
   for i in range(len(df)):
       df.loc[i, 'new_col'] = df.loc[i, 'col1'] * 2 + df.loc[i, 'col2']
   ```

2. **Filter early** to reduce data size:
   ```python
   # Filter before merge
   filtered_ae = ae[ae['AESER'] == 'Y']
   result = pd.merge(dm, filtered_ae, on='USUBJID')
   ```

3. **Use built-in functions** when possible:
   ```python
   # Use pandas built-ins
   df['MAX_VALUE'] = df.groupby('USUBJID')['VALUE'].transform('max')
   ```

## Integration with Study Workflow

1. **Data Upload**: Upload your source SDTM datasets
2. **Transformation**: Create derived datasets using this feature
3. **Mapping**: Map both source and derived datasets to dashboard requirements
4. **Publishing**: Publish the study with all transformations in place

Transformations are re-run automatically when:
- Source data is updated
- Transformation script is modified
- Manual re-run is triggered

## Security Considerations

The transformation environment is designed with security as the top priority:

- **No External Access**: Scripts cannot access external resources
- **Resource Limits**: Prevents resource exhaustion attacks
- **Input Validation**: All inputs are validated before execution
- **Output Validation**: Results are checked for size and structure
- **Audit Trail**: All transformations are logged with user and timestamp

Remember: While the system prevents malicious code execution, always review transformation scripts before running them on sensitive data.