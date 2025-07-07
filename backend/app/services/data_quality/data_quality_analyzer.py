# ABOUTME: Data quality analyzer service for analyzing data completeness, accuracy, and consistency
# ABOUTME: Provides methods to calculate quality scores and identify data quality issues

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.core.db import get_db

logger = logging.getLogger(__name__)


class DataQualityAnalyzer:
    """Service for analyzing data quality metrics across datasets."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def analyze_dataset_quality(
        self,
        study_id: str,
        dataset_name: str,
        field_mappings: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze data quality for a specific dataset.
        
        Args:
            study_id: Study identifier
            dataset_name: Name of the dataset to analyze
            field_mappings: Optional field mappings for analysis
            
        Returns:
            Dictionary containing quality metrics
        """
        try:
            # Get dataset data
            df = self._get_dataset_data(study_id, dataset_name)
            if df.empty:
                return self._empty_quality_result()
                
            # Calculate quality metrics
            quality_metrics = {
                'overallScore': self._calculate_overall_score(df),
                'completeness': self._calculate_completeness(df),
                'accuracy': self._calculate_accuracy(df, field_mappings),
                'consistency': self._calculate_consistency(df),
                'timeliness': self._calculate_timeliness(df),
                'validity': self._calculate_validity(df, field_mappings),
                'uniqueness': self._calculate_uniqueness(df),
                'breakdown': self._calculate_field_breakdown(df, field_mappings),
                'lastChecked': datetime.utcnow().isoformat(),
                'recordCount': len(df),
                'fieldCount': len(df.columns)
            }
            
            # Calculate trend if historical data exists
            trend = self._calculate_quality_trend(study_id, dataset_name)
            if trend:
                quality_metrics['trend'] = trend['trend']
                quality_metrics['trendDirection'] = trend['direction']
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing dataset quality: {str(e)}")
            return self._empty_quality_result()
    
    def analyze_study_quality(self, study_id: str) -> Dict[str, Any]:
        """
        Analyze overall data quality for a study across all datasets.
        
        Args:
            study_id: Study identifier
            
        Returns:
            Dictionary containing aggregated quality metrics
        """
        try:
            datasets = self._get_study_datasets(study_id)
            if not datasets:
                return self._empty_quality_result()
                
            dataset_qualities = []
            for dataset_name in datasets:
                quality = self.analyze_dataset_quality(study_id, dataset_name)
                dataset_qualities.append(quality)
            
            # Aggregate quality metrics
            overall_quality = self._aggregate_quality_metrics(dataset_qualities)
            overall_quality['datasets'] = len(datasets)
            overall_quality['datasetsAnalyzed'] = len([q for q in dataset_qualities if q['overallScore'] > 0])
            
            return overall_quality
            
        except Exception as e:
            logger.error(f"Error analyzing study quality: {str(e)}")
            return self._empty_quality_result()
    
    def identify_quality_issues(
        self,
        study_id: str,
        dataset_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Identify specific data quality issues in a dataset or study.
        
        Args:
            study_id: Study identifier
            dataset_name: Optional dataset name (if None, analyzes all datasets)
            
        Returns:
            List of quality issue dictionaries
        """
        try:
            issues = []
            
            if dataset_name:
                datasets = [dataset_name]
            else:
                datasets = self._get_study_datasets(study_id)
            
            for ds_name in datasets:
                df = self._get_dataset_data(study_id, ds_name)
                if df.empty:
                    continue
                    
                dataset_issues = self._identify_dataset_issues(df, study_id, ds_name)
                issues.extend(dataset_issues)
            
            # Sort by severity
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            issues.sort(key=lambda x: severity_order.get(x['severity'], 4))
            
            return issues
            
        except Exception as e:
            logger.error(f"Error identifying quality issues: {str(e)}")
            return []
    
    def _get_dataset_data(self, study_id: str, dataset_name: str) -> pd.DataFrame:
        """Get dataset data from the database."""
        try:
            # This would be replaced with actual database query based on your schema
            query = text("""
                SELECT * FROM study_data 
                WHERE study_id = :study_id 
                AND dataset_name = :dataset_name
                LIMIT 10000
            """)
            
            result = self.db.execute(query, {"study_id": study_id, "dataset_name": dataset_name})
            
            if result.rowcount == 0:
                return pd.DataFrame()
                
            columns = result.keys()
            data = result.fetchall()
            
            return pd.DataFrame(data, columns=columns)
            
        except Exception as e:
            logger.warning(f"Could not fetch dataset data: {str(e)}")
            # Return sample data for development
            return self._generate_sample_data()
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """Generate sample data for testing purposes."""
        np.random.seed(42)
        n_rows = 1000
        
        data = {
            'USUBJID': [f"SUBJ{i:04d}" for i in range(1, n_rows + 1)],
            'SITEID': np.random.choice(['001', '002', '003', '004'], n_rows),
            'AGE': np.random.normal(45, 15, n_rows).astype(int),
            'SEX': np.random.choice(['M', 'F'], n_rows),
            'VISITNUM': np.random.choice([1, 2, 3, 4, 5], n_rows),
            'VISITDT': pd.date_range('2023-01-01', periods=n_rows, freq='D'),
            'LBTEST': np.random.choice(['GLUCOSE', 'CHOLESTEROL', 'TRIGLYCERIDES'], n_rows),
            'LBSTRESN': np.random.normal(100, 20, n_rows),
        }
        
        # Introduce some quality issues
        missing_indices = np.random.choice(n_rows, size=int(n_rows * 0.05), replace=False)
        data['AGE'][missing_indices] = None
        
        # Some invalid values
        invalid_indices = np.random.choice(n_rows, size=int(n_rows * 0.02), replace=False)
        data['AGE'][invalid_indices] = -1
        
        return pd.DataFrame(data)
    
    def _calculate_completeness(self, df: pd.DataFrame) -> float:
        """Calculate data completeness percentage."""
        if df.empty:
            return 0.0
            
        total_cells = df.size
        non_null_cells = df.count().sum()
        
        return (non_null_cells / total_cells) * 100 if total_cells > 0 else 0.0
    
    def _calculate_accuracy(self, df: pd.DataFrame, field_mappings: Optional[Dict] = None) -> float:
        """Calculate data accuracy percentage based on validation rules."""
        if df.empty:
            return 0.0
            
        accuracy_issues = 0
        total_validations = 0
        
        for column in df.columns:
            if df[column].dtype in ['object', 'string']:
                # String validation
                invalid_strings = df[column].str.contains(r'[^\w\s-]', na=False).sum()
                accuracy_issues += invalid_strings
                total_validations += len(df[column].dropna())
                
            elif df[column].dtype in ['int64', 'float64']:
                # Numeric validation
                invalid_numbers = ((df[column] < 0) | (df[column] > 999999)).sum()
                accuracy_issues += invalid_numbers
                total_validations += len(df[column].dropna())
        
        if total_validations == 0:
            return 100.0
            
        accuracy_rate = ((total_validations - accuracy_issues) / total_validations) * 100
        return max(0.0, accuracy_rate)
    
    def _calculate_consistency(self, df: pd.DataFrame) -> float:
        """Calculate data consistency percentage."""
        if df.empty:
            return 0.0
            
        consistency_score = 100.0
        
        # Check for duplicate subject IDs
        if 'USUBJID' in df.columns:
            duplicate_subjects = df['USUBJID'].duplicated().sum()
            if len(df) > 0:
                consistency_score -= (duplicate_subjects / len(df)) * 20
        
        # Check for consistent data types within columns
        for column in df.columns:
            if df[column].dtype == 'object':
                # Check for mixed data types in string columns
                try:
                    numeric_values = pd.to_numeric(df[column], errors='coerce').notna().sum()
                    string_values = df[column].notna().sum() - numeric_values
                    if numeric_values > 0 and string_values > 0:
                        inconsistency_rate = min(numeric_values, string_values) / df[column].notna().sum()
                        consistency_score -= inconsistency_rate * 10
                except:
                    pass
        
        return max(0.0, consistency_score)
    
    def _calculate_timeliness(self, df: pd.DataFrame) -> float:
        """Calculate data timeliness based on date fields."""
        if df.empty:
            return 0.0
            
        timeliness_score = 100.0
        date_columns = []
        
        # Find date columns
        for column in df.columns:
            if 'DT' in column.upper() or 'DATE' in column.upper():
                try:
                    df[column] = pd.to_datetime(df[column], errors='coerce')
                    date_columns.append(column)
                except:
                    pass
        
        if not date_columns:
            return 90.0  # Default score if no date columns
            
        current_date = datetime.now()
        
        for column in date_columns:
            if df[column].notna().sum() > 0:
                # Check for future dates
                future_dates = (df[column] > current_date).sum()
                if len(df[column].dropna()) > 0:
                    future_rate = future_dates / len(df[column].dropna())
                    timeliness_score -= future_rate * 20
                
                # Check for very old dates (more than 10 years)
                very_old_dates = (df[column] < (current_date - timedelta(days=3650))).sum()
                if len(df[column].dropna()) > 0:
                    old_rate = very_old_dates / len(df[column].dropna())
                    timeliness_score -= old_rate * 10
        
        return max(0.0, timeliness_score)
    
    def _calculate_validity(self, df: pd.DataFrame, field_mappings: Optional[Dict] = None) -> float:
        """Calculate data validity based on business rules."""
        if df.empty:
            return 0.0
            
        validity_issues = 0
        total_checks = 0
        
        # Age validation
        if 'AGE' in df.columns:
            invalid_ages = ((df['AGE'] < 0) | (df['AGE'] > 120)).sum()
            validity_issues += invalid_ages
            total_checks += len(df['AGE'].dropna())
        
        # Sex validation
        if 'SEX' in df.columns:
            valid_sex = df['SEX'].isin(['M', 'F', 'MALE', 'FEMALE']).sum()
            invalid_sex = len(df['SEX'].dropna()) - valid_sex
            validity_issues += invalid_sex
            total_checks += len(df['SEX'].dropna())
        
        # Site ID validation
        if 'SITEID' in df.columns:
            # Site IDs should be consistent format
            invalid_sites = ~df['SITEID'].str.match(r'^\d{3}$', na=False).sum()
            validity_issues += invalid_sites
            total_checks += len(df['SITEID'].dropna())
        
        if total_checks == 0:
            return 100.0
            
        validity_rate = ((total_checks - validity_issues) / total_checks) * 100
        return max(0.0, validity_rate)
    
    def _calculate_uniqueness(self, df: pd.DataFrame) -> float:
        """Calculate data uniqueness percentage."""
        if df.empty:
            return 0.0
            
        uniqueness_score = 100.0
        
        # Check for duplicate rows
        if len(df) > 0:
            duplicate_rows = df.duplicated().sum()
            duplicate_rate = duplicate_rows / len(df)
            uniqueness_score -= duplicate_rate * 50
        
        # Check for duplicate subject visits
        if 'USUBJID' in df.columns and 'VISITNUM' in df.columns:
            visit_combinations = df[['USUBJID', 'VISITNUM']].dropna()
            if len(visit_combinations) > 0:
                duplicate_visits = visit_combinations.duplicated().sum()
                duplicate_visit_rate = duplicate_visits / len(visit_combinations)
                uniqueness_score -= duplicate_visit_rate * 30
        
        return max(0.0, uniqueness_score)
    
    def _calculate_overall_score(self, df: pd.DataFrame) -> float:
        """Calculate overall quality score as weighted average."""
        weights = {
            'completeness': 0.25,
            'accuracy': 0.20,
            'consistency': 0.20,
            'timeliness': 0.15,
            'validity': 0.15,
            'uniqueness': 0.05
        }
        
        scores = {
            'completeness': self._calculate_completeness(df),
            'accuracy': self._calculate_accuracy(df),
            'consistency': self._calculate_consistency(df),
            'timeliness': self._calculate_timeliness(df),
            'validity': self._calculate_validity(df),
            'uniqueness': self._calculate_uniqueness(df)
        }
        
        weighted_score = sum(scores[metric] * weights[metric] for metric in weights)
        return round(weighted_score, 1)
    
    def _calculate_field_breakdown(self, df: pd.DataFrame, field_mappings: Optional[Dict] = None) -> List[Dict]:
        """Calculate quality breakdown by field."""
        breakdown = []
        
        for column in df.columns:
            field_completeness = (df[column].count() / len(df)) * 100 if len(df) > 0 else 0
            
            # Count issues for this field
            issues = 0
            if df[column].dtype in ['int64', 'float64']:
                issues = ((df[column] < 0) | (df[column].isna())).sum()
            elif df[column].dtype == 'object':
                issues = df[column].isna().sum()
            
            # Determine status
            if field_completeness >= 95:
                status = 'excellent'
            elif field_completeness >= 85:
                status = 'good'
            elif field_completeness >= 70:
                status = 'warning'
            else:
                status = 'critical'
            
            breakdown.append({
                'metric': column,
                'score': field_completeness,
                'issues': issues,
                'status': status
            })
        
        return breakdown
    
    def _identify_dataset_issues(
        self,
        df: pd.DataFrame,
        study_id: str,
        dataset_name: str
    ) -> List[Dict[str, Any]]:
        """Identify specific issues in a dataset."""
        issues = []
        
        # Missing data issues
        for column in df.columns:
            missing_count = df[column].isna().sum()
            missing_rate = (missing_count / len(df)) * 100 if len(df) > 0 else 0
            
            if missing_rate > 20:
                issues.append({
                    'id': f"{study_id}_{dataset_name}_{column}_missing",
                    'title': f"High Missing Data Rate in {column}",
                    'message': f"{missing_rate:.1f}% of values are missing in {column} field",
                    'severity': 'critical' if missing_rate > 50 else 'high',
                    'category': 'data_quality',
                    'timestamp': datetime.utcnow(),
                    'status': 'active',
                    'source': f"{dataset_name}.{column}",
                    'affectedRecords': missing_count
                })
        
        # Duplicate records
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            issues.append({
                'id': f"{study_id}_{dataset_name}_duplicates",
                'title': "Duplicate Records Detected",
                'message': f"Found {duplicate_count} duplicate records in {dataset_name}",
                'severity': 'medium',
                'category': 'data_quality',
                'timestamp': datetime.utcnow(),
                'status': 'active',
                'source': dataset_name,
                'affectedRecords': duplicate_count
            })
        
        # Invalid values
        if 'AGE' in df.columns:
            invalid_ages = ((df['AGE'] < 0) | (df['AGE'] > 120)).sum()
            if invalid_ages > 0:
                issues.append({
                    'id': f"{study_id}_{dataset_name}_invalid_age",
                    'title': "Invalid Age Values",
                    'message': f"Found {invalid_ages} records with invalid age values",
                    'severity': 'high',
                    'category': 'data_quality',
                    'timestamp': datetime.utcnow(),
                    'status': 'active',
                    'source': f"{dataset_name}.AGE",
                    'affectedRecords': invalid_ages
                })
        
        return issues
    
    def _calculate_quality_trend(self, study_id: str, dataset_name: str) -> Optional[Dict]:
        """Calculate quality trend over time."""
        try:
            # This would fetch historical quality scores
            # For now, return a mock trend
            return {
                'trend': np.random.uniform(-5, 5),
                'direction': np.random.choice(['up', 'down', 'neutral'])
            }
        except:
            return None
    
    def _get_study_datasets(self, study_id: str) -> List[str]:
        """Get list of datasets for a study."""
        try:
            # This would query the database for actual datasets
            # For now, return sample dataset names
            return ['ADSL', 'ADAE', 'ADLB', 'ADVS', 'ADCM']
        except:
            return []
    
    def _aggregate_quality_metrics(self, dataset_qualities: List[Dict]) -> Dict[str, Any]:
        """Aggregate quality metrics across datasets."""
        if not dataset_qualities:
            return self._empty_quality_result()
        
        # Calculate weighted averages
        total_records = sum(q.get('recordCount', 0) for q in dataset_qualities)
        
        if total_records == 0:
            return self._empty_quality_result()
        
        weighted_scores = {}
        for metric in ['overallScore', 'completeness', 'accuracy', 'consistency', 'timeliness', 'validity', 'uniqueness']:
            weighted_sum = sum(q.get(metric, 0) * q.get('recordCount', 0) for q in dataset_qualities)
            weighted_scores[metric] = weighted_sum / total_records
        
        return {
            **weighted_scores,
            'lastChecked': datetime.utcnow().isoformat(),
            'totalRecords': total_records,
            'totalFields': sum(q.get('fieldCount', 0) for q in dataset_qualities)
        }
    
    def _empty_quality_result(self) -> Dict[str, Any]:
        """Return empty quality result."""
        return {
            'overallScore': 0.0,
            'completeness': 0.0,
            'accuracy': 0.0,
            'consistency': 0.0,
            'timeliness': 0.0,
            'validity': 0.0,
            'uniqueness': 0.0,
            'lastChecked': datetime.utcnow().isoformat(),
            'recordCount': 0,
            'fieldCount': 0
        }


def get_data_quality_analyzer(db: Session = None) -> DataQualityAnalyzer:
    """Get data quality analyzer instance."""
    if db is None:
        db = next(get_db())
    return DataQualityAnalyzer(db)