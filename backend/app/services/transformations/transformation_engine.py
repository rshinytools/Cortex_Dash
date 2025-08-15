# ABOUTME: Transformation engine for applying data transformations to widget data
# ABOUTME: Executes transformation pipelines defined in mapping templates

import re
import math
import statistics
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import ast
import operator
from functools import reduce

from app.models.mapping_templates import TransformationType


class TransformationEngine:
    """Engine for executing data transformations"""
    
    def __init__(self):
        self.transformations = {
            TransformationType.FIELD_RENAME: self.transform_field_rename,
            TransformationType.VALUE_MAPPING: self.transform_value_mapping,
            TransformationType.CALCULATION: self.transform_calculation,
            TransformationType.DATE_FORMAT: self.transform_date_format,
            TransformationType.UNIT_CONVERSION: self.transform_unit_conversion,
            TransformationType.AGGREGATION: self.transform_aggregation,
            TransformationType.CONDITIONAL: self.transform_conditional,
            TransformationType.REGEX_EXTRACT: self.transform_regex_extract,
            TransformationType.CONCATENATION: self.transform_concatenation,
            TransformationType.SPLIT: self.transform_split,
            TransformationType.CUSTOM_SCRIPT: self.transform_custom_script,
        }
        
        # Safe operators for calculations
        self.safe_operators = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '//': operator.floordiv,
            '%': operator.mod,
            '**': operator.pow,
            '==': operator.eq,
            '!=': operator.ne,
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
        }
        
        # Safe functions for calculations
        self.safe_functions = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'len': len,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'mean': statistics.mean,
            'median': statistics.median,
            'stdev': statistics.stdev,
        }
    
    def apply_transformation(
        self,
        data: Union[Dict, List[Dict]],
        transformation_type: TransformationType,
        config: Dict[str, Any],
        source_fields: List[str],
        target_field: str,
        on_error: str = "skip",
        default_value: Any = None
    ) -> Union[Dict, List[Dict]]:
        """Apply a transformation to data"""
        
        transform_func = self.transformations.get(transformation_type)
        if not transform_func:
            raise ValueError(f"Unknown transformation type: {transformation_type}")
        
        # Handle both single record and list of records
        if isinstance(data, list):
            return [
                self._apply_to_record(
                    record, transform_func, config, source_fields, 
                    target_field, on_error, default_value
                )
                for record in data
            ]
        else:
            return self._apply_to_record(
                data, transform_func, config, source_fields,
                target_field, on_error, default_value
            )
    
    def _apply_to_record(
        self,
        record: Dict,
        transform_func: Callable,
        config: Dict,
        source_fields: List[str],
        target_field: str,
        on_error: str,
        default_value: Any
    ) -> Dict:
        """Apply transformation to a single record"""
        try:
            # Extract source values
            source_values = [record.get(field) for field in source_fields]
            
            # Apply transformation
            result = transform_func(source_values, config)
            
            # Set target field
            record[target_field] = result
            
        except Exception as e:
            if on_error == "fail":
                raise
            elif on_error == "default":
                record[target_field] = default_value
            # If on_error == "skip", do nothing
        
        return record
    
    def transform_field_rename(self, values: List[Any], config: Dict) -> Any:
        """Rename a field (simple pass-through of value)"""
        return values[0] if values else None
    
    def transform_value_mapping(self, values: List[Any], config: Dict) -> Any:
        """Map values based on a mapping dictionary"""
        value = values[0] if values else None
        mapping = config.get("mapping", {})
        default = config.get("default_value")
        
        if value in mapping:
            return mapping[value]
        elif str(value) in mapping:
            return mapping[str(value)]
        else:
            return default if default is not None else value
    
    def transform_calculation(self, values: List[Any], config: Dict) -> Any:
        """Perform calculation on values"""
        expression = config.get("expression", "")
        
        if not expression:
            return None
        
        # Create context with values
        context = {}
        for i, value in enumerate(values):
            context[f"v{i}"] = value
            if i < len(config.get("field_names", [])):
                context[config["field_names"][i]] = value
        
        # Add safe functions to context
        context.update(self.safe_functions)
        
        # Parse and evaluate expression safely
        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            
            # Validate that only safe operations are used
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id not in context:
                    raise ValueError(f"Unknown variable: {node.id}")
            
            # Evaluate the expression
            result = eval(compile(tree, '<string>', 'eval'), {"__builtins__": {}}, context)
            return result
            
        except Exception as e:
            raise ValueError(f"Calculation error: {str(e)}")
    
    def transform_date_format(self, values: List[Any], config: Dict) -> Any:
        """Transform date format"""
        value = values[0] if values else None
        
        if not value:
            return None
        
        input_format = config.get("input_format", "%Y-%m-%d")
        output_format = config.get("output_format", "%Y-%m-%d")
        
        try:
            # Parse date
            if isinstance(value, str):
                dt = datetime.strptime(value, input_format)
            elif isinstance(value, (datetime, date)):
                dt = value
            else:
                return None
            
            # Format output
            return dt.strftime(output_format)
            
        except Exception:
            return None
    
    def transform_unit_conversion(self, values: List[Any], config: Dict) -> Any:
        """Convert units"""
        value = values[0] if values else None
        
        if value is None:
            return None
        
        try:
            value = float(value)
        except (ValueError, TypeError):
            return None
        
        from_unit = config.get("from_unit")
        to_unit = config.get("to_unit")
        
        # Define conversion factors (sample - extend as needed)
        conversions = {
            ("kg", "lb"): 2.20462,
            ("lb", "kg"): 0.453592,
            ("cm", "in"): 0.393701,
            ("in", "cm"): 2.54,
            ("C", "F"): lambda c: c * 9/5 + 32,
            ("F", "C"): lambda f: (f - 32) * 5/9,
        }
        
        conversion_key = (from_unit, to_unit)
        if conversion_key in conversions:
            conversion = conversions[conversion_key]
            if callable(conversion):
                return conversion(value)
            else:
                return value * conversion
        
        return value
    
    def transform_aggregation(self, values: List[Any], config: Dict) -> Any:
        """Aggregate multiple values"""
        agg_type = config.get("aggregation_type", "sum")
        
        # Filter out None values
        valid_values = [v for v in values if v is not None]
        
        if not valid_values:
            return None
        
        try:
            if agg_type == "sum":
                return sum(valid_values)
            elif agg_type == "avg" or agg_type == "mean":
                return statistics.mean(valid_values)
            elif agg_type == "min":
                return min(valid_values)
            elif agg_type == "max":
                return max(valid_values)
            elif agg_type == "count":
                return len(valid_values)
            elif agg_type == "median":
                return statistics.median(valid_values)
            elif agg_type == "stdev":
                return statistics.stdev(valid_values) if len(valid_values) > 1 else 0
            else:
                return None
        except Exception:
            return None
    
    def transform_conditional(self, values: List[Any], config: Dict) -> Any:
        """Apply conditional logic"""
        conditions = config.get("conditions", [])
        default_value = config.get("default_value")
        
        value = values[0] if values else None
        
        for condition in conditions:
            operator_type = condition.get("operator")
            compare_value = condition.get("value")
            return_value = condition.get("return_value")
            
            if self._evaluate_condition(value, operator_type, compare_value):
                return return_value
        
        return default_value
    
    def _evaluate_condition(self, value: Any, operator_type: str, compare_value: Any) -> bool:
        """Evaluate a single condition"""
        try:
            if operator_type == "equals":
                return value == compare_value
            elif operator_type == "not_equals":
                return value != compare_value
            elif operator_type == "greater_than":
                return float(value) > float(compare_value)
            elif operator_type == "less_than":
                return float(value) < float(compare_value)
            elif operator_type == "greater_or_equal":
                return float(value) >= float(compare_value)
            elif operator_type == "less_or_equal":
                return float(value) <= float(compare_value)
            elif operator_type == "contains":
                return str(compare_value) in str(value)
            elif operator_type == "starts_with":
                return str(value).startswith(str(compare_value))
            elif operator_type == "ends_with":
                return str(value).endswith(str(compare_value))
            elif operator_type == "is_null":
                return value is None
            elif operator_type == "is_not_null":
                return value is not None
            elif operator_type == "in":
                return value in compare_value
            elif operator_type == "not_in":
                return value not in compare_value
            else:
                return False
        except Exception:
            return False
    
    def transform_regex_extract(self, values: List[Any], config: Dict) -> Any:
        """Extract value using regex"""
        value = values[0] if values else None
        
        if not value:
            return None
        
        pattern = config.get("pattern")
        group = config.get("group", 0)
        
        if not pattern:
            return value
        
        try:
            match = re.search(pattern, str(value))
            if match:
                if group == 0:
                    return match.group()
                elif group <= len(match.groups()):
                    return match.group(group)
            return None
        except Exception:
            return None
    
    def transform_concatenation(self, values: List[Any], config: Dict) -> Any:
        """Concatenate multiple values"""
        separator = config.get("separator", "")
        prefix = config.get("prefix", "")
        suffix = config.get("suffix", "")
        skip_null = config.get("skip_null", True)
        
        if skip_null:
            values = [str(v) for v in values if v is not None]
        else:
            values = [str(v) if v is not None else "" for v in values]
        
        result = separator.join(values)
        return f"{prefix}{result}{suffix}" if result else None
    
    def transform_split(self, values: List[Any], config: Dict) -> Any:
        """Split a value into parts"""
        value = values[0] if values else None
        
        if not value:
            return None
        
        delimiter = config.get("delimiter", ",")
        index = config.get("index")  # Which part to return
        max_split = config.get("max_split", -1)
        
        try:
            parts = str(value).split(delimiter, max_split)
            
            if index is not None:
                if 0 <= index < len(parts):
                    return parts[index].strip()
                return None
            else:
                return parts
        except Exception:
            return None
    
    def transform_custom_script(self, values: List[Any], config: Dict) -> Any:
        """Execute custom Python script (sandboxed)"""
        script = config.get("script", "")
        
        if not script:
            return None
        
        # Create safe context
        context = {
            "values": values,
            "math": math,
            "statistics": statistics,
            "datetime": datetime,
            "re": re,
        }
        
        # Add safe functions
        context.update(self.safe_functions)
        
        try:
            # Execute script in sandboxed environment
            exec_globals = {"__builtins__": {}}
            exec_locals = context.copy()
            
            # Execute the script
            exec(script, exec_globals, exec_locals)
            
            # Return the result (script should set 'result' variable)
            return exec_locals.get("result")
            
        except Exception as e:
            raise ValueError(f"Script execution error: {str(e)}")
    
    def apply_transformation_pipeline(
        self,
        data: Union[Dict, List[Dict]],
        transformations: List[Dict[str, Any]]
    ) -> Union[Dict, List[Dict]]:
        """Apply a pipeline of transformations in sequence"""
        
        result = data
        
        for transformation in transformations:
            result = self.apply_transformation(
                data=result,
                transformation_type=TransformationType(transformation["transformation_type"]),
                config=transformation.get("config", {}),
                source_fields=transformation.get("source_fields", []),
                target_field=transformation.get("target_field", ""),
                on_error=transformation.get("on_error", "skip"),
                default_value=transformation.get("default_value")
            )
        
        return result