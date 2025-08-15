# ABOUTME: Expression parser for complex calculations in widgets
# ABOUTME: Parses and evaluates mathematical and logical expressions safely

import ast
import operator
import re
from typing import Any, Dict, List, Optional, Union, Set
from datetime import datetime, date, timedelta
from decimal import Decimal
import math
import statistics


class ExpressionParser:
    """Safe expression parser for widget calculations"""
    
    def __init__(self):
        # Safe operators
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.And: operator.and_,
            ast.Or: operator.or_,
            ast.Not: operator.not_,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        # Safe built-in functions
        self.functions = {
            # Math functions
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'len': len,
            'sqrt': math.sqrt,
            'pow': pow,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'ceil': math.ceil,
            'floor': math.floor,
            
            # Statistical functions
            'mean': statistics.mean,
            'median': statistics.median,
            'mode': statistics.mode,
            'stdev': statistics.stdev,
            'variance': statistics.variance,
            
            # Type conversions
            'int': int,
            'float': float,
            'str': str,
            'bool': bool,
            
            # Conditional
            'if_else': lambda cond, true_val, false_val: true_val if cond else false_val,
        }
        
        # Constants
        self.constants = {
            'PI': math.pi,
            'E': math.e,
            'TRUE': True,
            'FALSE': False,
            'NULL': None,
        }
    
    def parse(self, expression: str, context: Dict[str, Any] = None) -> Any:
        """
        Parse and evaluate an expression safely.
        
        Args:
            expression: The expression string to evaluate
            context: Dictionary of variables available in the expression
            
        Returns:
            The result of the expression evaluation
        """
        if not expression:
            return None
        
        context = context or {}
        
        try:
            # Parse the expression into an AST
            tree = ast.parse(expression, mode='eval')
            
            # Validate the AST for safety
            self._validate_ast(tree, context)
            
            # Evaluate the expression
            return self._eval_node(tree.body, context)
            
        except SyntaxError as e:
            raise ValueError(f"Syntax error in expression: {e}")
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")
    
    def _validate_ast(self, tree: ast.AST, context: Dict[str, Any]):
        """Validate that the AST only contains safe operations"""
        for node in ast.walk(tree):
            # Check for forbidden node types
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Exec, 
                                ast.Global, ast.Nonlocal, ast.ClassDef,
                                ast.FunctionDef, ast.AsyncFunctionDef,
                                ast.Lambda, ast.ListComp, ast.DictComp,
                                ast.SetComp, ast.GeneratorExp)):
                raise ValueError(f"Forbidden operation: {node.__class__.__name__}")
            
            # Check for attribute access (prevent accessing __methods__)
            if isinstance(node, ast.Attribute):
                if node.attr.startswith('_'):
                    raise ValueError(f"Cannot access private attributes: {node.attr}")
            
            # Validate function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id not in self.functions:
                        raise ValueError(f"Unknown function: {node.func.id}")
    
    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """Recursively evaluate an AST node"""
        
        # Literals
        if isinstance(node, ast.Constant):
            return node.value
        
        # Variables
        elif isinstance(node, ast.Name):
            name = node.id
            if name in context:
                return context[name]
            elif name in self.constants:
                return self.constants[name]
            elif name in self.functions:
                return self.functions[name]
            else:
                raise ValueError(f"Unknown variable: {name}")
        
        # Binary operations
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op_func = self.operators.get(type(node.op))
            if op_func:
                return op_func(left, right)
            else:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
        
        # Unary operations
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            op_func = self.operators.get(type(node.op))
            if op_func:
                return op_func(operand)
            else:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
        
        # Comparisons
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)
                op_func = self.operators.get(type(op))
                if op_func:
                    if not op_func(left, right):
                        return False
                    left = right
                else:
                    raise ValueError(f"Unsupported comparison: {type(op).__name__}")
            return True
        
        # Boolean operations
        elif isinstance(node, ast.BoolOp):
            op_func = self.operators.get(type(node.op))
            if isinstance(node.op, ast.And):
                for value in node.values:
                    result = self._eval_node(value, context)
                    if not result:
                        return False
                return True
            elif isinstance(node.op, ast.Or):
                for value in node.values:
                    result = self._eval_node(value, context)
                    if result:
                        return True
                return False
            else:
                raise ValueError(f"Unsupported boolean operation: {type(node.op).__name__}")
        
        # Function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.functions:
                    func = self.functions[func_name]
                    args = [self._eval_node(arg, context) for arg in node.args]
                    kwargs = {
                        kw.arg: self._eval_node(kw.value, context)
                        for kw in node.keywords
                    }
                    return func(*args, **kwargs)
                else:
                    raise ValueError(f"Unknown function: {func_name}")
            else:
                raise ValueError("Complex function calls not supported")
        
        # Conditional expressions (ternary operator)
        elif isinstance(node, ast.IfExp):
            test = self._eval_node(node.test, context)
            if test:
                return self._eval_node(node.body, context)
            else:
                return self._eval_node(node.orelse, context)
        
        # Lists
        elif isinstance(node, ast.List):
            return [self._eval_node(elem, context) for elem in node.elts]
        
        # Dictionaries
        elif isinstance(node, ast.Dict):
            return {
                self._eval_node(k, context): self._eval_node(v, context)
                for k, v in zip(node.keys, node.values)
            }
        
        # Subscript (indexing)
        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, context)
            if isinstance(node.slice, ast.Index):
                # Python 3.8 compatibility
                index = self._eval_node(node.slice.value, context)
            else:
                index = self._eval_node(node.slice, context)
            return value[index]
        
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")
    
    def get_variables(self, expression: str) -> Set[str]:
        """Extract all variable names from an expression"""
        if not expression:
            return set()
        
        try:
            tree = ast.parse(expression, mode='eval')
            variables = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    name = node.id
                    # Exclude functions and constants
                    if name not in self.functions and name not in self.constants:
                        variables.add(name)
            
            return variables
            
        except SyntaxError:
            return set()
    
    def validate_expression(self, expression: str) -> tuple[bool, Optional[str]]:
        """
        Validate an expression without evaluating it.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not expression:
            return False, "Empty expression"
        
        try:
            tree = ast.parse(expression, mode='eval')
            self._validate_ast(tree, {})
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Invalid expression: {e}"


class CalculationBuilder:
    """Helper class for building calculations"""
    
    @staticmethod
    def build_aggregation(field: str, agg_type: str) -> str:
        """Build an aggregation expression"""
        agg_map = {
            'sum': f'sum({field})',
            'avg': f'mean({field})',
            'min': f'min({field})',
            'max': f'max({field})',
            'count': f'len({field})',
            'count_distinct': f'len(set({field}))',
            'median': f'median({field})',
            'stdev': f'stdev({field})',
        }
        return agg_map.get(agg_type, field)
    
    @staticmethod
    def build_conditional(condition: str, true_val: str, false_val: str) -> str:
        """Build a conditional expression"""
        return f'({true_val}) if ({condition}) else ({false_val})'
    
    @staticmethod
    def build_date_diff(date1: str, date2: str, unit: str = 'days') -> str:
        """Build a date difference expression"""
        if unit == 'days':
            return f'({date1} - {date2}).days'
        elif unit == 'months':
            return f'(({date1} - {date2}).days / 30.44)'
        elif unit == 'years':
            return f'(({date1} - {date2}).days / 365.25)'
        else:
            return f'({date1} - {date2}).{unit}'
    
    @staticmethod
    def build_percentage(numerator: str, denominator: str) -> str:
        """Build a percentage calculation"""
        return f'(({numerator}) / ({denominator}) * 100) if ({denominator}) != 0 else 0'
    
    @staticmethod
    def build_ratio(value1: str, value2: str) -> str:
        """Build a ratio calculation"""
        return f'({value1}) / ({value2}) if ({value2}) != 0 else NULL'