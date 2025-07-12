# Transformation Script Template & Guidelines

## Script Interface Requirements

### Basic Script Structure
Every transformation script should follow this template:

```python
"""
Script: ADSL.py
Description: Creates Subject-Level Analysis Dataset
Inputs: DM, DS
Outputs: ADSL
Author: system.admin@study.com
Version: 1.0
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

def main(context):
    """
    Main transformation function
    
    Args:
        context: Dictionary containing:
            - source_data_path: Path to latest source data
            - transformed_data_path: Path to latest transformed data
            - output_path: Where to save the output
            - study_id: Current study ID
            - run_timestamp: Current run timestamp
    
    Returns:
        dict: Metadata about the transformation
    """
    try:
        # Load source datasets
        logger.info("Loading DM dataset...")
        dm = pd.read_parquet(f"{context['source_data_path']}/DM.parquet")
        
        logger.info("Loading DS dataset...")
        ds = pd.read_parquet(f"{context['source_data_path']}/DS.parquet")
        
        # Perform transformations
        logger.info("Creating ADSL dataset...")
        
        # Example: Merge demographics with disposition
        adsl = dm.merge(
            ds[ds['DSCAT'] == 'DISPOSITION'],
            on='USUBJID',
            how='left'
        )
        
        # Add derived variables
        adsl['SAFFL'] = 'Y'  # Safety population flag
        adsl['ITTFL'] = np.where(adsl['RANDOMIZED'] == 'Y', 'Y', 'N')
        
        # Save output
        output_file = f"{context['output_path']}/ADSL.parquet"
        adsl.to_parquet(output_file, index=False)
        logger.info(f"Saved ADSL with {len(adsl)} records")
        
        # Return metadata
        return {
            'status': 'success',
            'records_processed': len(adsl),
            'columns': list(adsl.columns),
            'output_file': output_file
        }
        
    except Exception as e:
        logger.error(f"Error in transformation: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


# Script must have a main function that accepts context
if __name__ == "__main__":
    # This allows testing the script locally
    test_context = {
        'source_data_path': './test_data/source',
        'transformed_data_path': './test_data/transformed',
        'output_path': './test_data/output',
        'study_id': 'TEST-001',
        'run_timestamp': datetime.now().isoformat()
    }
    result = main(test_context)
    print(result)
```

## Script Guidelines

### 1. Required Elements
- **Docstring**: Must include Script name, Description, Inputs, Outputs
- **main() function**: Entry point that accepts context dictionary
- **Logging**: Use the provided logger for progress and errors
- **Error handling**: Wrap in try/except and return error status
- **Return metadata**: Always return status and relevant metadata

### 2. Context Dictionary
The system provides these paths and info:
```python
context = {
    'source_data_path': '/data/studies/{study_id}/source_data/{latest}/processed',
    'transformed_data_path': '/data/studies/{study_id}/transformed_data/{latest}',
    'output_path': '/data/studies/{study_id}/transformed_data/{new_timestamp}',
    'study_id': 'STUDY-001',
    'run_timestamp': '2024-01-10T15:30:00'
}
```

### 3. Accessing Other Transformed Datasets
```python
# If your script depends on another transformed dataset:
adsl = pd.read_parquet(f"{context['transformed_data_path']}/ADSL.parquet")
```

### 4. Available Libraries
These libraries are pre-installed in the execution environment:
- pandas
- numpy
- scipy
- datetime
- pyarrow
- Standard Python libraries (os, json, etc.)

### 5. Restrictions
- No network access
- No file system access outside provided paths
- No system command execution
- 10-minute execution timeout
- 8GB memory limit

### 6. Best Practices
1. **Log progress** for long-running transformations
2. **Validate inputs** before processing
3. **Handle missing data** gracefully
4. **Document complex logic** with comments
5. **Return meaningful errors** for debugging

### 7. Example Scripts

#### Simple Aggregation (SUMM.py)
```python
"""
Script: SUMM.py
Description: Creates summary statistics dataset
Inputs: ADSL, ADAE
Outputs: SUMM
"""

def main(context):
    adsl = pd.read_parquet(f"{context['transformed_data_path']}/ADSL.parquet")
    adae = pd.read_parquet(f"{context['source_data_path']}/AE.parquet")
    
    # Calculate summary statistics
    summ = adsl.groupby('ARM').agg({
        'USUBJID': 'count',
        'AGE': ['mean', 'std', 'min', 'max']
    }).reset_index()
    
    # Add AE counts
    ae_counts = adae.groupby('ARM')['USUBJID'].nunique().reset_index()
    ae_counts.columns = ['ARM', 'AE_SUBJECTS']
    
    summ = summ.merge(ae_counts, on='ARM', how='left')
    
    summ.to_parquet(f"{context['output_path']}/SUMM.parquet", index=False)
    
    return {
        'status': 'success',
        'records_processed': len(summ)
    }
```

#### Complex Derivation (ADEFF.py)
```python
"""
Script: ADEFF.py
Description: Creates efficacy analysis dataset
Inputs: ADSL, EFF
Outputs: ADEFF
"""

def main(context):
    adsl = pd.read_parquet(f"{context['transformed_data_path']}/ADSL.parquet")
    eff = pd.read_parquet(f"{context['source_data_path']}/EFF.parquet")
    
    # Merge with ADSL to get treatment info
    adeff = eff.merge(adsl[['USUBJID', 'ARM', 'ITTFL']], on='USUBJID')
    
    # Calculate change from baseline
    baseline = adeff[adeff['VISIT'] == 'BASELINE'][['USUBJID', 'PARAMCD', 'AVAL']]
    baseline.columns = ['USUBJID', 'PARAMCD', 'BASE']
    
    adeff = adeff.merge(baseline, on=['USUBJID', 'PARAMCD'], how='left')
    adeff['CHG'] = adeff['AVAL'] - adeff['BASE']
    adeff['PCHG'] = (adeff['CHG'] / adeff['BASE']) * 100
    
    adeff.to_parquet(f"{context['output_path']}/ADEFF.parquet", index=False)
    
    return {
        'status': 'success',
        'records_processed': len(adeff)
    }
```