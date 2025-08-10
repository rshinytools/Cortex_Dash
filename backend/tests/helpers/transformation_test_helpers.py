# ABOUTME: Helper utilities for transformation testing
# ABOUTME: Provides test data generation and validation helpers

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import tempfile
import os
from datetime import datetime, timedelta
import random
import string


class TransformationTestDataGenerator:
    """Generate test data for transformation testing."""
    
    @staticmethod
    def create_demographics_data(num_subjects: int = 100) -> pd.DataFrame:
        """Create mock demographics dataset."""
        return pd.DataFrame({
            'USUBJID': [f'SUBJ{str(i).zfill(3)}' for i in range(1, num_subjects + 1)],
            'AGE': np.random.randint(18, 80, num_subjects),
            'SEX': np.random.choice(['M', 'F'], num_subjects),
            'RACE': np.random.choice(['WHITE', 'BLACK', 'ASIAN', 'OTHER'], num_subjects),
            'COUNTRY': np.random.choice(['USA', 'GBR', 'JPN', 'DEU'], num_subjects),
            'WEIGHT': np.random.normal(70, 15, num_subjects),
            'HEIGHT': np.random.normal(170, 10, num_subjects),
            'SITEID': np.random.choice([f'SITE{i:03d}' for i in range(1, 11)], num_subjects)
        })
    
    @staticmethod
    def create_adverse_events_data(num_subjects: int = 100, events_per_subject: int = 5) -> pd.DataFrame:
        """Create mock adverse events dataset."""
        ae_terms = ['Headache', 'Nausea', 'Fatigue', 'Dizziness', 'Rash', 
                    'Fever', 'Cough', 'Vomiting', 'Diarrhea', 'Pain']
        severities = ['MILD', 'MODERATE', 'SEVERE']
        
        data = []
        for i in range(1, num_subjects + 1):
            subject_id = f'SUBJ{str(i).zfill(3)}'
            num_events = np.random.randint(0, events_per_subject + 1)
            
            for j in range(num_events):
                start_date = datetime(2024, 1, 1) + timedelta(days=np.random.randint(0, 365))
                end_date = start_date + timedelta(days=np.random.randint(1, 30))
                
                data.append({
                    'USUBJID': subject_id,
                    'AETERM': np.random.choice(ae_terms),
                    'AESEV': np.random.choice(severities),
                    'AESER': np.random.choice(['Y', 'N'], p=[0.1, 0.9]),
                    'AESTDTC': start_date.strftime('%Y-%m-%d'),
                    'AEENDTC': end_date.strftime('%Y-%m-%d'),
                    'AEREL': np.random.choice(['RELATED', 'NOT RELATED', 'UNLIKELY'])
                })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def create_laboratory_data(num_subjects: int = 100, tests_per_subject: int = 10) -> pd.DataFrame:
        """Create mock laboratory dataset."""
        lab_tests = [
            ('ALT', 'Alanine Aminotransferase', 'U/L', 10, 40),
            ('AST', 'Aspartate Aminotransferase', 'U/L', 10, 35),
            ('BILI', 'Bilirubin', 'mg/dL', 0.3, 1.2),
            ('CREAT', 'Creatinine', 'mg/dL', 0.7, 1.3),
            ('HGB', 'Hemoglobin', 'g/dL', 12, 16),
            ('WBC', 'White Blood Cells', '10^9/L', 4, 11)
        ]
        
        visits = ['BASELINE', 'WEEK 2', 'WEEK 4', 'WEEK 8', 'WEEK 12']
        
        data = []
        for i in range(1, num_subjects + 1):
            subject_id = f'SUBJ{str(i).zfill(3)}'
            
            for visit in visits:
                for test_code, test_name, unit, low_norm, high_norm in lab_tests:
                    # Generate value with some outliers
                    if np.random.random() < 0.1:  # 10% chance of abnormal
                        value = np.random.choice([
                            np.random.uniform(0, low_norm),  # Below normal
                            np.random.uniform(high_norm, high_norm * 2)  # Above normal
                        ])
                    else:
                        value = np.random.uniform(low_norm, high_norm)
                    
                    data.append({
                        'USUBJID': subject_id,
                        'LBTESTCD': test_code,
                        'LBTEST': test_name,
                        'LBORRES': round(value, 2),
                        'LBORRESU': unit,
                        'VISIT': visit,
                        'LBNRIND': 'NORMAL' if low_norm <= value <= high_norm else 
                                  ('HIGH' if value > high_norm else 'LOW')
                    })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def create_test_study_data(study_path: str) -> Dict[str, str]:
        """Create a complete set of test study data files."""
        os.makedirs(study_path, exist_ok=True)
        
        # Generate datasets
        dm = TransformationTestDataGenerator.create_demographics_data(100)
        ae = TransformationTestDataGenerator.create_adverse_events_data(100)
        lb = TransformationTestDataGenerator.create_laboratory_data(100)
        
        # Save to parquet files
        file_paths = {}
        file_paths['dm'] = os.path.join(study_path, 'dm.parquet')
        file_paths['ae'] = os.path.join(study_path, 'ae.parquet')
        file_paths['lb'] = os.path.join(study_path, 'lb.parquet')
        
        dm.to_parquet(file_paths['dm'])
        ae.to_parquet(file_paths['ae'])
        lb.to_parquet(file_paths['lb'])
        
        return file_paths


class TransformationTestValidator:
    """Validate transformation outputs for testing."""
    
    @staticmethod
    def validate_output_structure(df: pd.DataFrame, expected_columns: List[str]) -> bool:
        """Validate that output has expected columns."""
        return all(col in df.columns for col in expected_columns)
    
    @staticmethod
    def validate_no_data_loss(input_df: pd.DataFrame, output_df: pd.DataFrame, key_column: str) -> bool:
        """Validate that no records were lost during transformation."""
        input_keys = set(input_df[key_column].unique())
        output_keys = set(output_df[key_column].unique())
        return input_keys == output_keys
    
    @staticmethod
    def validate_calculations(df: pd.DataFrame, calculation_checks: Dict[str, Any]) -> List[str]:
        """Validate calculated fields meet expectations."""
        errors = []
        
        for column, checks in calculation_checks.items():
            if column not in df.columns:
                errors.append(f"Missing column: {column}")
                continue
            
            if 'min' in checks and df[column].min() < checks['min']:
                errors.append(f"{column} has values below minimum {checks['min']}")
            
            if 'max' in checks and df[column].max() > checks['max']:
                errors.append(f"{column} has values above maximum {checks['max']}")
            
            if 'unique_values' in checks:
                actual_values = set(df[column].dropna().unique())
                expected_values = set(checks['unique_values'])
                if not actual_values.issubset(expected_values):
                    errors.append(f"{column} has unexpected values: {actual_values - expected_values}")
        
        return errors


class TransformationSecurityTester:
    """Test security aspects of transformations."""
    
    # Malicious scripts to test security
    MALICIOUS_SCRIPTS = [
        # File system access attempts
        "open('/etc/passwd', 'r').read()",
        "with open('/tmp/test.txt', 'w') as f: f.write('test')",
        "os.listdir('/')",
        "pathlib.Path('/').iterdir()",
        
        # Import attempts
        "import os",
        "from subprocess import call",
        "__import__('os')",
        "importlib.import_module('os')",
        
        # Execution attempts
        "exec('print(123)')",
        "eval('1+1')",
        "compile('x=1', 'string', 'exec')",
        
        # Network attempts
        "import requests",
        "import urllib",
        "socket.socket()",
        
        # Process/system attempts
        "subprocess.run(['ls'])",
        "os.system('ls')",
        "multiprocessing.Process()",
    ]
    
    @staticmethod
    def generate_obfuscated_imports() -> List[str]:
        """Generate obfuscated import attempts."""
        return [
            "globals()['__builtins__']['__import__']('os')",
            "getattr(__builtins__, '__import__')('os')",
            "vars(__builtins__)['__import__']('os')",
            f"{'__import__'}('os')",  # String concatenation
            "eval(chr(95)*2 + 'import' + chr(95)*2)('os')",  # Using chr()
        ]
    
    @staticmethod
    def generate_resource_exhaustion_scripts() -> List[str]:
        """Generate scripts that attempt resource exhaustion."""
        return [
            # Memory exhaustion
            "df = pd.DataFrame({'x': range(10**9)})",
            "large_list = [0] * (10**9)",
            "while True: df = pd.concat([df, df])",
            
            # CPU exhaustion
            "while True: pass",
            "for i in range(10**9): x = i ** i",
            
            # Infinite recursion
            "def recurse(): recurse()\nrecurse()",
        ]


# Test fixtures for transformation scenarios
TRANSFORMATION_TEST_SCENARIOS = {
    'simple_calculation': {
        'script': "df['bmi'] = df['WEIGHT'] / (df['HEIGHT'] / 100) ** 2",
        'input_datasets': ['dm'],
        'expected_columns': ['bmi'],
        'validation': {
            'bmi': {'min': 10, 'max': 50}
        }
    },
    'merge_datasets': {
        'script': """
merged = pd.merge(dm, ae, on='USUBJID', how='left')
df = merged.copy()
df['has_ae'] = ~df['AETERM'].isna()
""",
        'input_datasets': ['dm', 'ae'],
        'expected_columns': ['has_ae', 'AGE', 'AETERM'],
        'validation': {
            'has_ae': {'unique_values': [True, False]}
        }
    },
    'aggregation': {
        'script': """
ae_counts = ae.groupby('USUBJID').size().reset_index(name='ae_count')
df = pd.merge(dm, ae_counts, on='USUBJID', how='left')
df['ae_count'] = df['ae_count'].fillna(0)
""",
        'input_datasets': ['dm', 'ae'],
        'expected_columns': ['ae_count'],
        'validation': {
            'ae_count': {'min': 0}
        }
    },
    'complex_transformation': {
        'script': """
# Multiple transformations
df = dm.copy()

# Age categorization
df['age_group'] = pd.cut(df['AGE'], 
                         bins=[0, 30, 50, 65, 100], 
                         labels=['Young', 'Middle', 'Senior', 'Elderly'])

# BMI calculation and categorization
df['bmi'] = df['WEIGHT'] / (df['HEIGHT'] / 100) ** 2
df['bmi_category'] = pd.cut(df['bmi'], 
                            bins=[0, 18.5, 25, 30, 100], 
                            labels=['Underweight', 'Normal', 'Overweight', 'Obese'])

# Risk scoring
df['risk_score'] = 0
df.loc[df['AGE'] > 65, 'risk_score'] += 1
df.loc[df['bmi'] > 30, 'risk_score'] += 1
df.loc[df['SEX'] == 'M', 'risk_score'] += 0.5
""",
        'input_datasets': ['dm'],
        'expected_columns': ['age_group', 'bmi', 'bmi_category', 'risk_score'],
        'validation': {
            'age_group': {'unique_values': ['Young', 'Middle', 'Senior', 'Elderly']},
            'bmi_category': {'unique_values': ['Underweight', 'Normal', 'Overweight', 'Obese']},
            'risk_score': {'min': 0, 'max': 2.5}
        }
    }
}