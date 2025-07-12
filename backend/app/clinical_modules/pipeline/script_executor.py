# ABOUTME: Secure script executor for user-defined transformation scripts
# ABOUTME: Implements sandboxing, resource limits, and safe execution environment

import ast
import hashlib
import pandas as pd
import numpy as np
import re
import json
import io
import sys
import traceback
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager
import resource
import signal
import multiprocessing
from functools import wraps
import builtins

# Allowed built-in functions in the sandbox
SAFE_BUILTINS = {
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'chr', 'dict', 
    'divmod', 'enumerate', 'filter', 'float', 'format', 'frozenset',
    'hash', 'hex', 'int', 'isinstance', 'issubclass', 'iter', 'len',
    'list', 'map', 'max', 'min', 'oct', 'ord', 'pow', 'range',
    'repr', 'reversed', 'round', 'set', 'slice', 'sorted', 'str',
    'sum', 'tuple', 'type', 'zip'
}

# Allowed modules and their safe attributes
SAFE_MODULES = {
    'pandas': ['DataFrame', 'Series', 'read_csv', 'read_parquet', 'merge', 'concat', 'pivot_table', 'groupby'],
    'numpy': ['array', 'zeros', 'ones', 'mean', 'std', 'sum', 'min', 'max', 'median', 'percentile'],
    'datetime': ['datetime', 'date', 'time', 'timedelta'],
    're': ['match', 'search', 'findall', 'sub', 'compile'],
    'json': ['loads', 'dumps'],
    'math': ['ceil', 'floor', 'sqrt', 'log', 'exp', 'sin', 'cos', 'tan'],
}

class SecurityError(Exception):
    """Raised when script violates security constraints"""
    pass

class ResourceLimitError(Exception):
    """Raised when script exceeds resource limits"""
    pass

class ScriptValidator:
    """Validates Python scripts for security issues"""
    
    def __init__(self, allowed_imports: List[str] = None):
        self.allowed_imports = allowed_imports or list(SAFE_MODULES.keys())
    
    def validate(self, script: str) -> Tuple[bool, List[str]]:
        """
        Validate a script for security issues
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            tree = ast.parse(script)
        except SyntaxError as e:
            return False, [f"Syntax error: {str(e)}"]
        
        # Check for dangerous constructs
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.allowed_imports:
                        errors.append(f"Import '{alias.name}' is not allowed")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module not in self.allowed_imports:
                    errors.append(f"Import from '{node.module}' is not allowed")
            
            # Check for dangerous functions
            elif isinstance(node, ast.Name):
                if node.id in ['eval', 'exec', 'compile', '__import__', 'open', 'file']:
                    errors.append(f"Use of '{node.id}' is not allowed")
            
            # Check for attribute access to dangerous methods
            elif isinstance(node, ast.Attribute):
                if node.attr in ['__globals__', '__code__', '__class__', '__bases__', '__subclasses__']:
                    errors.append(f"Access to '{node.attr}' is not allowed")
        
        return len(errors) == 0, errors

class SandboxedEnvironment:
    """Creates a sandboxed execution environment"""
    
    def __init__(self, allowed_modules: Dict[str, List[str]] = None, 
                 allowed_builtins: set = None,
                 resource_limits: Dict[str, Any] = None):
        self.allowed_modules = allowed_modules or SAFE_MODULES
        self.allowed_builtins = allowed_builtins or SAFE_BUILTINS
        self.resource_limits = resource_limits or {
            'max_memory_mb': 1024,
            'max_execution_time_seconds': 300,
            'max_cpu_percent': 80
        }
    
    def create_safe_globals(self) -> Dict[str, Any]:
        """Create a safe global namespace for script execution"""
        safe_globals = {}
        
        # Add safe builtins
        safe_builtins = {name: getattr(builtins, name) 
                        for name in self.allowed_builtins 
                        if hasattr(builtins, name)}
        safe_globals['__builtins__'] = safe_builtins
        
        # Add allowed modules with restricted attributes
        for module_name, allowed_attrs in self.allowed_modules.items():
            try:
                module = __import__(module_name)
                safe_module = type(module_name, (), {})()
                
                for attr in allowed_attrs:
                    if hasattr(module, attr):
                        setattr(safe_module, attr, getattr(module, attr))
                
                safe_globals[module_name] = safe_module
            except ImportError:
                pass  # Module not available
        
        return safe_globals

    @contextmanager
    def resource_limited_execution(self):
        """Context manager for resource-limited execution"""
        # Set memory limit
        if sys.platform != 'win32':  # Resource limits not available on Windows
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            resource.setrlimit(resource.RLIMIT_AS, 
                             (self.resource_limits['max_memory_mb'] * 1024 * 1024, hard))
        
        # Set up timeout
        def timeout_handler(signum, frame):
            raise ResourceLimitError("Script execution timeout")
        
        if sys.platform != 'win32':
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.resource_limits['max_execution_time_seconds'])
        
        try:
            yield
        finally:
            if sys.platform != 'win32':
                signal.alarm(0)  # Cancel alarm
                resource.setrlimit(resource.RLIMIT_AS, (soft, hard))  # Reset memory limit

class TransformationScriptExecutor:
    """Executes transformation scripts in a sandboxed environment"""
    
    def __init__(self):
        self.validator = ScriptValidator()
        self.sandbox = SandboxedEnvironment()
    
    def execute_script(self, script: str, input_data: pd.DataFrame, 
                      parameters: Dict[str, Any] = None,
                      allowed_imports: List[str] = None,
                      resource_limits: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Execute a transformation script on input data
        
        Args:
            script: Python script to execute
            input_data: Input DataFrame
            parameters: Additional parameters available to the script
            allowed_imports: List of allowed module imports
            resource_limits: Resource limits for execution
            
        Returns:
            Tuple of (output_dataframe, execution_metadata)
        """
        # Validate script
        if allowed_imports:
            self.validator.allowed_imports = allowed_imports
        
        is_valid, errors = self.validator.validate(script)
        if not is_valid:
            raise SecurityError(f"Script validation failed: {'; '.join(errors)}")
        
        # Update sandbox settings
        if resource_limits:
            self.sandbox.resource_limits.update(resource_limits)
        
        # Prepare execution environment
        safe_globals = self.sandbox.create_safe_globals()
        safe_globals['df'] = input_data.copy()  # Prevent modification of original
        safe_globals['parameters'] = parameters or {}
        safe_globals['output'] = None
        
        # Capture output
        output_buffer = io.StringIO()
        
        # Execute script
        start_time = datetime.utcnow()
        execution_metadata = {
            'start_time': start_time.isoformat(),
            'input_rows': len(input_data),
            'input_columns': len(input_data.columns),
            'logs': []
        }
        
        try:
            with self.sandbox.resource_limited_execution():
                # Redirect stdout to capture print statements
                old_stdout = sys.stdout
                sys.stdout = output_buffer
                
                try:
                    exec(script, safe_globals, safe_globals)
                finally:
                    sys.stdout = old_stdout
                
                # Get output
                output_df = safe_globals.get('output')
                if output_df is None:
                    output_df = safe_globals.get('df')  # Use modified df if no explicit output
                
                if not isinstance(output_df, pd.DataFrame):
                    raise ValueError("Script must produce a pandas DataFrame as output")
                
                end_time = datetime.utcnow()
                execution_metadata.update({
                    'end_time': end_time.isoformat(),
                    'duration_seconds': (end_time - start_time).total_seconds(),
                    'output_rows': len(output_df),
                    'output_columns': len(output_df.columns),
                    'logs': output_buffer.getvalue().split('\n') if output_buffer.getvalue() else [],
                    'success': True
                })
                
                return output_df, execution_metadata
                
        except ResourceLimitError as e:
            execution_metadata.update({
                'error': str(e),
                'error_type': 'resource_limit',
                'success': False
            })
            raise
            
        except Exception as e:
            execution_metadata.update({
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc(),
                'success': False
            })
            raise

    def hash_script(self, script: str) -> str:
        """Generate SHA256 hash of script for integrity checking"""
        return hashlib.sha256(script.encode()).hexdigest()
    
    def execute_sql_transform(self, sql_query: str, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Execute SQL transformation using pandas
        
        Args:
            sql_query: SQL query to execute
            datasets: Dictionary of dataset name -> DataFrame
            
        Returns:
            Result DataFrame
        """
        # Register datasets as temporary tables
        for name, df in datasets.items():
            # Use pandasql or duckdb for SQL execution
            # For now, return a placeholder
            pass
        
        # This would use a SQL engine like DuckDB or pandasql
        # Placeholder implementation
        return list(datasets.values())[0] if datasets else pd.DataFrame()

# Example transformation scripts
EXAMPLE_SCRIPTS = {
    'standardize_columns': '''
# Standardize column names
df.columns = [col.lower().replace(' ', '_') for col in df.columns]
output = df
''',
    
    'filter_by_date': '''
# Filter data by date range
from datetime import datetime
start_date = parameters.get('start_date', '2024-01-01')
end_date = parameters.get('end_date', '2024-12-31')

df['date'] = pandas.to_datetime(df['date'])
output = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
''',
    
    'aggregate_by_group': '''
# Aggregate data by group
group_cols = parameters.get('group_by', ['category'])
agg_funcs = parameters.get('aggregations', {'value': 'sum'})

output = df.groupby(group_cols).agg(agg_funcs).reset_index()
''',
    
    'derive_calculated_field': '''
# Create calculated fields
df['bmi'] = df['weight'] / (df['height'] / 100) ** 2
df['age_group'] = pandas.cut(df['age'], bins=[0, 18, 35, 50, 65, 100], 
                            labels=['<18', '18-35', '35-50', '50-65', '65+'])
output = df
'''
}