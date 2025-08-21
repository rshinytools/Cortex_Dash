# ABOUTME: Advanced filter parser with support for date ranges and subqueries
# ABOUTME: Extends base parser with relative dates and complex nested conditions

from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta, date
from dataclasses import dataclass
import re
import logging
from .filter_parser import (
    FilterParser, ASTNode, ColumnNode, LiteralNode, 
    BinaryOpNode, TokenType, Parser, Lexer
)

logger = logging.getLogger(__name__)


@dataclass
class DateRangeNode(ASTNode):
    """Represents a date range filter with relative dates"""
    column: ColumnNode
    range_type: str  # 'last_n_days', 'this_month', 'this_year', etc.
    value: Optional[int] = None  # For 'last_n_days'
    
    def to_absolute_range(self) -> tuple[datetime, datetime]:
        """Convert relative date range to absolute dates"""
        now = datetime.now()
        
        if self.range_type == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            
        elif self.range_type == 'yesterday':
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            
        elif self.range_type == 'last_n_days':
            if not self.value:
                raise ValueError("last_n_days requires a value")
            start = (now - timedelta(days=self.value)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
            
        elif self.range_type == 'this_week':
            # Start from Monday
            days_since_monday = now.weekday()
            start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
            
        elif self.range_type == 'last_week':
            days_since_monday = now.weekday()
            last_monday = now - timedelta(days=days_since_monday + 7)
            start = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = (last_monday + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
            
        elif self.range_type == 'this_month':
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
            
        elif self.range_type == 'last_month':
            first_day_this_month = now.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            start = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = last_day_last_month.replace(hour=23, minute=59, second=59, microsecond=999999)
            
        elif self.range_type == 'this_quarter':
            quarter = (now.month - 1) // 3
            start_month = quarter * 3 + 1
            start = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
            
        elif self.range_type == 'last_quarter':
            current_quarter = (now.month - 1) // 3
            if current_quarter == 0:
                # Previous year Q4
                start = datetime(now.year - 1, 10, 1)
                end = datetime(now.year - 1, 12, 31, 23, 59, 59, 999999)
            else:
                start_month = (current_quarter - 1) * 3 + 1
                end_month = start_month + 2
                start = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
                # Get last day of end month
                if end_month == 12:
                    end = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
                else:
                    next_month = now.replace(month=end_month + 1, day=1)
                    end = (next_month - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
                    
        elif self.range_type == 'this_year':
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
            
        elif self.range_type == 'last_year':
            start = datetime(now.year - 1, 1, 1)
            end = datetime(now.year - 1, 12, 31, 23, 59, 59, 999999)
            
        else:
            raise ValueError(f"Unknown date range type: {self.range_type}")
            
        return start, end


@dataclass
class SubqueryNode(ASTNode):
    """Represents a subquery in filter expression"""
    column: ColumnNode
    operator: str  # 'IN', 'NOT IN', 'EXISTS', 'NOT EXISTS'
    query: str  # The subquery SQL
    dataset: Optional[str] = None  # Dataset to query from


@dataclass
class GroupNode(ASTNode):
    """Represents a grouped condition (AND/OR group)"""
    operator: TokenType  # AND or OR
    conditions: List[ASTNode]


class AdvancedFilterParser(FilterParser):
    """Enhanced filter parser with advanced features"""
    
    # Date range patterns
    DATE_RANGE_PATTERNS = {
        r'last (\d+) days?': ('last_n_days', True),
        r'past (\d+) days?': ('last_n_days', True),
        r'today': ('today', False),
        r'yesterday': ('yesterday', False),
        r'this week': ('this_week', False),
        r'last week': ('last_week', False),
        r'this month': ('this_month', False),
        r'last month': ('last_month', False),
        r'this quarter': ('this_quarter', False),
        r'last quarter': ('last_quarter', False),
        r'this year': ('this_year', False),
        r'last year': ('last_year', False),
    }
    
    def parse(self, expression: str) -> Dict[str, Any]:
        """
        Enhanced parse method with support for date ranges and subqueries
        """
        try:
            # Pre-process for date ranges
            expression, date_ranges = self._preprocess_date_ranges(expression)
            
            # Pre-process for subqueries
            expression, subqueries = self._preprocess_subqueries(expression)
            
            # Use base parser
            result = super().parse(expression)
            
            if result['is_valid']:
                # Post-process to inject date ranges and subqueries
                result['ast'] = self._inject_special_nodes(
                    result['ast'], 
                    date_ranges, 
                    subqueries
                )
                
                # Re-extract columns
                result['columns'] = self._extract_columns(result['ast'])
                
                # Add metadata
                result['has_date_ranges'] = len(date_ranges) > 0
                result['has_subqueries'] = len(subqueries) > 0
                result['date_ranges'] = date_ranges
                result['subqueries'] = subqueries
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse advanced filter expression: {str(e)}")
            return {
                "ast": None,
                "columns": [],
                "is_valid": False,
                "error": str(e),
                "expression": expression
            }
    
    def _preprocess_date_ranges(self, expression: str) -> tuple[str, Dict[str, DateRangeNode]]:
        """
        Find and replace date range expressions with placeholders
        """
        date_ranges = {}
        placeholder_counter = 0
        
        # Look for date range patterns
        for pattern, (range_type, has_value) in self.DATE_RANGE_PATTERNS.items():
            matches = re.finditer(f'\\b{pattern}\\b', expression, re.IGNORECASE)
            
            for match in matches:
                placeholder = f"__DATE_RANGE_{placeholder_counter}__"
                
                if has_value:
                    # Extract numeric value
                    value = int(match.group(1))
                    date_ranges[placeholder] = {
                        'range_type': range_type,
                        'value': value,
                        'original': match.group(0)
                    }
                else:
                    date_ranges[placeholder] = {
                        'range_type': range_type,
                        'value': None,
                        'original': match.group(0)
                    }
                
                # Replace in expression
                expression = expression[:match.start()] + placeholder + expression[match.end():]
                placeholder_counter += 1
        
        return expression, date_ranges
    
    def _preprocess_subqueries(self, expression: str) -> tuple[str, Dict[str, SubqueryNode]]:
        """
        Find and replace subqueries with placeholders
        """
        subqueries = {}
        placeholder_counter = 0
        
        # Look for subquery patterns (simplified - in production would need full SQL parser)
        # Pattern: column IN (SELECT ... FROM ...)
        subquery_pattern = r'(\w+)\s+(IN|NOT\s+IN)\s*\(\s*SELECT\s+.*?\s+FROM\s+.*?\)'
        
        matches = re.finditer(subquery_pattern, expression, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            placeholder = f"__SUBQUERY_{placeholder_counter}__"
            
            column = match.group(1)
            operator = match.group(2).upper().replace('  ', ' ')
            query = match.group(0)[match.group(0).index('SELECT'):-1]  # Extract SELECT statement
            
            subqueries[placeholder] = {
                'column': column,
                'operator': operator,
                'query': query,
                'original': match.group(0)
            }
            
            # Replace in expression with a placeholder that looks like valid SQL
            expression = expression[:match.start()] + f"{column} = '{placeholder}'" + expression[match.end():]
            placeholder_counter += 1
        
        return expression, subqueries
    
    def _inject_special_nodes(self, node: ASTNode, date_ranges: Dict, subqueries: Dict) -> ASTNode:
        """
        Replace placeholders with special nodes in AST
        """
        if isinstance(node, BinaryOpNode):
            # Check if this is a date range comparison
            if isinstance(node.right, LiteralNode) and isinstance(node.right.value, str):
                if node.right.value in date_ranges:
                    dr = date_ranges[node.right.value]
                    return DateRangeNode(
                        column=node.left,
                        range_type=dr['range_type'],
                        value=dr.get('value')
                    )
                elif node.right.value in subqueries:
                    sq = subqueries[node.right.value]
                    return SubqueryNode(
                        column=node.left,
                        operator=sq['operator'],
                        query=sq['query']
                    )
            
            # Recursively process children
            node.left = self._inject_special_nodes(node.left, date_ranges, subqueries)
            node.right = self._inject_special_nodes(node.right, date_ranges, subqueries)
            
        elif isinstance(node, UnaryOpNode):
            node.operand = self._inject_special_nodes(node.operand, date_ranges, subqueries)
            
        return node
    
    def _extract_columns(self, node: ASTNode) -> List[str]:
        """
        Extended column extraction including special nodes
        """
        columns = super()._extract_columns(node)
        
        if isinstance(node, DateRangeNode):
            columns.append(node.column.name)
        elif isinstance(node, SubqueryNode):
            columns.append(node.column.name)
        elif isinstance(node, GroupNode):
            for condition in node.conditions:
                columns.extend(self._extract_columns(condition))
        
        return list(set(columns))
    
    def ast_to_dict(self, node: ASTNode) -> Dict[str, Any]:
        """
        Extended AST to dict conversion
        """
        if isinstance(node, DateRangeNode):
            start, end = node.to_absolute_range()
            return {
                "type": "date_range",
                "column": node.column.name,
                "range_type": node.range_type,
                "value": node.value,
                "absolute_range": {
                    "start": start.isoformat(),
                    "end": end.isoformat()
                }
            }
        
        elif isinstance(node, SubqueryNode):
            return {
                "type": "subquery",
                "column": node.column.name,
                "operator": node.operator,
                "query": node.query,
                "dataset": node.dataset
            }
        
        elif isinstance(node, GroupNode):
            return {
                "type": "group",
                "operator": node.operator.value,
                "conditions": [self.ast_to_dict(c) for c in node.conditions]
            }
        
        # Fall back to base implementation
        return super().ast_to_dict(node)
    
    def parse_grouped_conditions(self, expression: str) -> GroupNode:
        """
        Parse expression with explicit grouping support
        Example: "(status = 'Active' AND age > 18) OR (status = 'Pending' AND age > 21)"
        """
        # This is already handled by parentheses in the base parser
        # But we can add explicit group node creation for clarity
        result = self.parse(expression)
        
        if result['is_valid']:
            # Wrap in a group node if it's a complex expression
            if isinstance(result['ast'], BinaryOpNode):
                if result['ast'].operator in (TokenType.AND, TokenType.OR):
                    # Convert to GroupNode for clearer structure
                    conditions = self._flatten_conditions(result['ast'], result['ast'].operator)
                    return GroupNode(
                        operator=result['ast'].operator,
                        conditions=conditions
                    )
            
        return result['ast']
    
    def _flatten_conditions(self, node: ASTNode, operator: TokenType) -> List[ASTNode]:
        """
        Flatten nested AND/OR conditions into a list
        """
        conditions = []
        
        if isinstance(node, BinaryOpNode) and node.operator == operator:
            # Same operator, flatten
            conditions.extend(self._flatten_conditions(node.left, operator))
            conditions.extend(self._flatten_conditions(node.right, operator))
        else:
            # Different operator or leaf node, add as-is
            conditions.append(node)
        
        return conditions


# Example usage and testing
if __name__ == "__main__":
    parser = AdvancedFilterParser()
    
    # Test date range
    result = parser.parse("visit_date in last 30 days AND status = 'Active'")
    print("Date range test:", result)
    
    # Test subquery (simplified)
    result = parser.parse("patient_id IN (SELECT patient_id FROM ae WHERE severity = 'Serious')")
    print("Subquery test:", result)
    
    # Test complex grouping
    result = parser.parse("(status = 'Active' AND age > 18) OR (status = 'Pending' AND age > 21)")
    print("Grouping test:", result)
    
    # Test advanced operators
    result = parser.parse("site_id IN ('001', '002', '003') AND value BETWEEN 10 AND 100")
    print("Advanced operators test:", result)