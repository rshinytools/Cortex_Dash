# ABOUTME: SQL WHERE clause parser for widget filtering
# ABOUTME: Converts SQL expressions to AST for validation and execution

import re
from typing import Dict, List, Optional, Union, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Token types for SQL expression parsing"""
    # Literals
    STRING = "STRING"
    NUMBER = "NUMBER"
    NULL = "NULL"
    BOOLEAN = "BOOLEAN"
    
    # Identifiers
    COLUMN = "COLUMN"
    
    # Operators
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    # Comparison operators
    EQ = "="
    NEQ = "!="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    
    # Special operators
    IN = "IN"
    NOT_IN = "NOT IN"
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    IS = "IS"
    IS_NOT = "IS NOT"
    BETWEEN = "BETWEEN"
    
    # Grouping
    LPAREN = "("
    RPAREN = ")"
    COMMA = ","
    
    # End of expression
    EOF = "EOF"


@dataclass
class Token:
    """Represents a token in the SQL expression"""
    type: TokenType
    value: Any
    position: int


class Lexer:
    """Tokenizes SQL WHERE clause expressions"""
    
    def __init__(self, expression: str):
        self.expression = expression
        self.position = 0
        self.tokens: List[Token] = []
        
    def tokenize(self) -> List[Token]:
        """Convert expression to tokens"""
        while self.position < len(self.expression):
            self._skip_whitespace()
            
            if self.position >= len(self.expression):
                break
                
            # Check for operators and keywords
            if self._check_keyword():
                continue
            elif self._check_operator():
                continue
            elif self._check_string():
                continue
            elif self._check_number():
                continue
            elif self._check_column():
                continue
            elif self._check_grouping():
                continue
            else:
                raise ValueError(f"Unexpected character at position {self.position}: {self.expression[self.position]}")
                
        self.tokens.append(Token(TokenType.EOF, None, self.position))
        return self.tokens
    
    def _skip_whitespace(self):
        """Skip whitespace characters"""
        while self.position < len(self.expression) and self.expression[self.position].isspace():
            self.position += 1
    
    def _check_keyword(self) -> bool:
        """Check for SQL keywords"""
        remaining = self.expression[self.position:].upper()
        
        # Check multi-word keywords first
        keywords = {
            "IS NOT": TokenType.IS_NOT,
            "NOT LIKE": TokenType.NOT_LIKE,
            "NOT IN": TokenType.NOT_IN,
            "AND": TokenType.AND,
            "OR": TokenType.OR,
            "NOT": TokenType.NOT,
            "NULL": TokenType.NULL,
            "TRUE": TokenType.BOOLEAN,
            "FALSE": TokenType.BOOLEAN,
            "IN": TokenType.IN,
            "LIKE": TokenType.LIKE,
            "IS": TokenType.IS,
            "BETWEEN": TokenType.BETWEEN,
        }
        
        for keyword, token_type in keywords.items():
            if remaining.startswith(keyword):
                # Check if it's a complete keyword (not part of a column name)
                next_pos = self.position + len(keyword)
                if next_pos >= len(self.expression) or not self.expression[next_pos].isalnum():
                    value = keyword if token_type != TokenType.BOOLEAN else (keyword == "TRUE")
                    if keyword == "NULL":
                        value = None
                    self.tokens.append(Token(token_type, value, self.position))
                    self.position += len(keyword)
                    return True
        
        return False
    
    def _check_operator(self) -> bool:
        """Check for comparison operators"""
        remaining = self.expression[self.position:]
        
        operators = {
            "!=": TokenType.NEQ,
            "<=": TokenType.LTE,
            ">=": TokenType.GTE,
            "=": TokenType.EQ,
            "<": TokenType.LT,
            ">": TokenType.GT,
        }
        
        for op, token_type in operators.items():
            if remaining.startswith(op):
                self.tokens.append(Token(token_type, op, self.position))
                self.position += len(op)
                return True
        
        return False
    
    def _check_string(self) -> bool:
        """Check for string literals"""
        if self.expression[self.position] in ("'", '"'):
            quote = self.expression[self.position]
            start = self.position + 1
            self.position += 1
            
            value = ""
            while self.position < len(self.expression):
                if self.expression[self.position] == quote:
                    # Check for escaped quote
                    if self.position + 1 < len(self.expression) and self.expression[self.position + 1] == quote:
                        value += quote
                        self.position += 2
                    else:
                        self.position += 1
                        break
                else:
                    value += self.expression[self.position]
                    self.position += 1
            
            self.tokens.append(Token(TokenType.STRING, value, start - 1))
            return True
        
        return False
    
    def _check_number(self) -> bool:
        """Check for numeric literals"""
        if self.expression[self.position].isdigit() or self.expression[self.position] == '.':
            start = self.position
            has_dot = False
            
            while self.position < len(self.expression):
                char = self.expression[self.position]
                if char.isdigit():
                    self.position += 1
                elif char == '.' and not has_dot:
                    has_dot = True
                    self.position += 1
                else:
                    break
            
            value_str = self.expression[start:self.position]
            value = float(value_str) if has_dot else int(value_str)
            self.tokens.append(Token(TokenType.NUMBER, value, start))
            return True
        
        return False
    
    def _check_column(self) -> bool:
        """Check for column identifiers"""
        if self.expression[self.position].isalpha() or self.expression[self.position] == '_':
            start = self.position
            
            while self.position < len(self.expression):
                char = self.expression[self.position]
                if char.isalnum() or char in ('_', '.'):
                    self.position += 1
                else:
                    break
            
            value = self.expression[start:self.position]
            self.tokens.append(Token(TokenType.COLUMN, value, start))
            return True
        
        return False
    
    def _check_grouping(self) -> bool:
        """Check for grouping characters"""
        char = self.expression[self.position]
        
        if char == '(':
            self.tokens.append(Token(TokenType.LPAREN, char, self.position))
            self.position += 1
            return True
        elif char == ')':
            self.tokens.append(Token(TokenType.RPAREN, char, self.position))
            self.position += 1
            return True
        elif char == ',':
            self.tokens.append(Token(TokenType.COMMA, char, self.position))
            self.position += 1
            return True
        
        return False


@dataclass
class ASTNode:
    """Base class for AST nodes"""
    pass


@dataclass
class ColumnNode(ASTNode):
    """Represents a column reference"""
    name: str


@dataclass
class LiteralNode(ASTNode):
    """Represents a literal value"""
    value: Any


@dataclass
class BinaryOpNode(ASTNode):
    """Represents a binary operation"""
    operator: TokenType
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOpNode(ASTNode):
    """Represents a unary operation"""
    operator: TokenType
    operand: ASTNode


@dataclass
class InNode(ASTNode):
    """Represents IN/NOT IN operation"""
    column: ColumnNode
    values: List[LiteralNode]
    negate: bool = False


@dataclass
class BetweenNode(ASTNode):
    """Represents BETWEEN operation"""
    column: ColumnNode
    lower: LiteralNode
    upper: LiteralNode


@dataclass
class LikeNode(ASTNode):
    """Represents LIKE/NOT LIKE operation"""
    column: ColumnNode
    pattern: str
    negate: bool = False


@dataclass
class IsNullNode(ASTNode):
    """Represents IS NULL/IS NOT NULL operation"""
    column: ColumnNode
    negate: bool = False


class Parser:
    """Parses tokenized SQL expression into AST"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        self.current_token = tokens[0] if tokens else Token(TokenType.EOF, None, 0)
    
    def parse(self) -> ASTNode:
        """Parse tokens into AST"""
        if not self.tokens or self.current_token.type == TokenType.EOF:
            raise ValueError("Empty expression")
        
        return self._parse_or()
    
    def _advance(self):
        """Move to next token"""
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
    
    def _peek(self, offset: int = 1) -> Optional[Token]:
        """Look ahead at next token"""
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def _parse_or(self) -> ASTNode:
        """Parse OR expressions (lowest precedence)"""
        left = self._parse_and()
        
        while self.current_token.type == TokenType.OR:
            op = self.current_token.type
            self._advance()
            right = self._parse_and()
            left = BinaryOpNode(op, left, right)
        
        return left
    
    def _parse_and(self) -> ASTNode:
        """Parse AND expressions"""
        left = self._parse_not()
        
        while self.current_token.type == TokenType.AND:
            op = self.current_token.type
            self._advance()
            right = self._parse_not()
            left = BinaryOpNode(op, left, right)
        
        return left
    
    def _parse_not(self) -> ASTNode:
        """Parse NOT expressions"""
        if self.current_token.type == TokenType.NOT:
            self._advance()
            operand = self._parse_comparison()
            return UnaryOpNode(TokenType.NOT, operand)
        
        return self._parse_comparison()
    
    def _parse_comparison(self) -> ASTNode:
        """Parse comparison expressions"""
        # Handle parentheses
        if self.current_token.type == TokenType.LPAREN:
            self._advance()
            node = self._parse_or()
            if self.current_token.type != TokenType.RPAREN:
                raise ValueError(f"Expected closing parenthesis at position {self.current_token.position}")
            self._advance()
            return node
        
        # Parse column or literal
        left = self._parse_primary()
        
        # Check for comparison operators
        if self.current_token.type in (TokenType.EQ, TokenType.NEQ, TokenType.LT, 
                                       TokenType.LTE, TokenType.GT, TokenType.GTE):
            op = self.current_token.type
            self._advance()
            right = self._parse_primary()
            return BinaryOpNode(op, left, right)
        
        # Check for IN/NOT IN
        elif self.current_token.type in (TokenType.IN, TokenType.NOT_IN):
            if not isinstance(left, ColumnNode):
                raise ValueError("IN/NOT IN requires column on left side")
            
            negate = self.current_token.type == TokenType.NOT_IN
            self._advance()
            
            if self.current_token.type != TokenType.LPAREN:
                raise ValueError("Expected opening parenthesis after IN")
            self._advance()
            
            values = []
            while self.current_token.type != TokenType.RPAREN:
                values.append(self._parse_primary())
                if self.current_token.type == TokenType.COMMA:
                    self._advance()
                elif self.current_token.type != TokenType.RPAREN:
                    raise ValueError("Expected comma or closing parenthesis in IN list")
            
            self._advance()  # Skip closing paren
            return InNode(left, values, negate)
        
        # Check for LIKE/NOT LIKE
        elif self.current_token.type in (TokenType.LIKE, TokenType.NOT_LIKE):
            if not isinstance(left, ColumnNode):
                raise ValueError("LIKE requires column on left side")
            
            negate = self.current_token.type == TokenType.NOT_LIKE
            self._advance()
            
            pattern_node = self._parse_primary()
            if not isinstance(pattern_node, LiteralNode) or not isinstance(pattern_node.value, str):
                raise ValueError("LIKE requires string pattern")
            
            return LikeNode(left, pattern_node.value, negate)
        
        # Check for IS NULL/IS NOT NULL
        elif self.current_token.type == TokenType.IS_NOT:
            if not isinstance(left, ColumnNode):
                raise ValueError("IS NOT NULL requires column on left side")
            
            self._advance()
            
            if self.current_token.type != TokenType.NULL:
                raise ValueError("IS NOT must be followed by NULL")
            self._advance()
            
            return IsNullNode(left, True)
        
        elif self.current_token.type == TokenType.IS:
            if not isinstance(left, ColumnNode):
                raise ValueError("IS NULL requires column on left side")
            
            self._advance()
            
            if self.current_token.type != TokenType.NULL:
                raise ValueError("IS must be followed by NULL")
            self._advance()
            
            return IsNullNode(left, False)
        
        # Check for BETWEEN
        elif self.current_token.type == TokenType.BETWEEN:
            if not isinstance(left, ColumnNode):
                raise ValueError("BETWEEN requires column on left side")
            
            self._advance()
            lower = self._parse_primary()
            
            if self.current_token.type != TokenType.AND:
                raise ValueError("BETWEEN requires AND")
            self._advance()
            
            upper = self._parse_primary()
            return BetweenNode(left, lower, upper)
        
        return left
    
    def _parse_primary(self) -> ASTNode:
        """Parse primary expressions (columns and literals)"""
        if self.current_token.type == TokenType.COLUMN:
            node = ColumnNode(self.current_token.value)
            self._advance()
            return node
        
        elif self.current_token.type in (TokenType.STRING, TokenType.NUMBER, 
                                         TokenType.NULL, TokenType.BOOLEAN):
            node = LiteralNode(self.current_token.value)
            self._advance()
            return node
        
        else:
            raise ValueError(f"Unexpected token at position {self.current_token.position}: {self.current_token.type}")


class FilterParser:
    """Main filter parser service"""
    
    def __init__(self):
        self.logger = logger
    
    def parse(self, expression: str) -> Dict[str, Any]:
        """
        Parse SQL WHERE clause expression into AST
        
        Args:
            expression: SQL WHERE clause expression
            
        Returns:
            Dictionary containing:
            - ast: The parsed AST
            - columns: List of columns referenced
            - is_valid: Whether parsing succeeded
            - error: Error message if parsing failed
        """
        try:
            # Tokenize
            lexer = Lexer(expression)
            tokens = lexer.tokenize()
            
            # Parse to AST
            parser = Parser(tokens)
            ast = parser.parse()
            
            # Extract columns
            columns = self._extract_columns(ast)
            
            return {
                "ast": ast,
                "columns": columns,
                "is_valid": True,
                "error": None,
                "expression": expression
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse filter expression: {str(e)}")
            return {
                "ast": None,
                "columns": [],
                "is_valid": False,
                "error": str(e),
                "expression": expression
            }
    
    def _extract_columns(self, node: ASTNode) -> List[str]:
        """Extract all column references from AST"""
        columns = []
        
        if isinstance(node, ColumnNode):
            columns.append(node.name)
        elif isinstance(node, BinaryOpNode):
            columns.extend(self._extract_columns(node.left))
            columns.extend(self._extract_columns(node.right))
        elif isinstance(node, UnaryOpNode):
            columns.extend(self._extract_columns(node.operand))
        elif isinstance(node, InNode):
            columns.append(node.column.name)
        elif isinstance(node, BetweenNode):
            columns.append(node.column.name)
        elif isinstance(node, LikeNode):
            columns.append(node.column.name)
        elif isinstance(node, IsNullNode):
            columns.append(node.column.name)
        
        return list(set(columns))  # Remove duplicates
    
    def ast_to_dict(self, node: ASTNode) -> Dict[str, Any]:
        """Convert AST to dictionary for serialization"""
        if isinstance(node, ColumnNode):
            return {"type": "column", "name": node.name}
        
        elif isinstance(node, LiteralNode):
            return {"type": "literal", "value": node.value}
        
        elif isinstance(node, BinaryOpNode):
            return {
                "type": "binary_op",
                "operator": node.operator.value,
                "left": self.ast_to_dict(node.left),
                "right": self.ast_to_dict(node.right)
            }
        
        elif isinstance(node, UnaryOpNode):
            return {
                "type": "unary_op",
                "operator": node.operator.value,
                "operand": self.ast_to_dict(node.operand)
            }
        
        elif isinstance(node, InNode):
            return {
                "type": "in",
                "column": node.column.name,
                "values": [v.value for v in node.values],
                "negate": node.negate
            }
        
        elif isinstance(node, BetweenNode):
            return {
                "type": "between",
                "column": node.column.name,
                "lower": node.lower.value,
                "upper": node.upper.value
            }
        
        elif isinstance(node, LikeNode):
            return {
                "type": "like",
                "column": node.column.name,
                "pattern": node.pattern,
                "negate": node.negate
            }
        
        elif isinstance(node, IsNullNode):
            return {
                "type": "is_null",
                "column": node.column.name,
                "negate": node.negate
            }
        
        return {}