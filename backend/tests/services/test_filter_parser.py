# ABOUTME: Unit tests for SQL filter parser service
# ABOUTME: Tests tokenization, parsing, and AST generation

import pytest
from app.services.filter_parser import (
    FilterParser, Lexer, Parser, TokenType,
    ColumnNode, LiteralNode, BinaryOpNode, UnaryOpNode,
    InNode, BetweenNode, LikeNode, IsNullNode
)


class TestLexer:
    """Test the lexer/tokenizer"""
    
    def test_simple_comparison(self):
        """Test tokenizing simple comparisons"""
        lexer = Lexer("AESER = 'Y'")
        tokens = lexer.tokenize()
        
        assert len(tokens) == 4  # AESER, =, 'Y', EOF
        assert tokens[0].type == TokenType.COLUMN
        assert tokens[0].value == "AESER"
        assert tokens[1].type == TokenType.EQ
        assert tokens[2].type == TokenType.STRING
        assert tokens[2].value == "Y"
    
    def test_numeric_comparison(self):
        """Test tokenizing numeric comparisons"""
        lexer = Lexer("AGE >= 18")
        tokens = lexer.tokenize()
        
        assert tokens[0].value == "AGE"
        assert tokens[1].type == TokenType.GTE
        assert tokens[2].type == TokenType.NUMBER
        assert tokens[2].value == 18
    
    def test_boolean_operators(self):
        """Test tokenizing AND/OR operators"""
        lexer = Lexer("AESER = 'Y' AND AETERM IS NOT NULL")
        tokens = lexer.tokenize()
        
        # Find AND token
        and_token = next(t for t in tokens if t.type == TokenType.AND)
        assert and_token is not None
        
        # Find IS NOT token
        is_not_token = next(t for t in tokens if t.type == TokenType.IS_NOT)
        assert is_not_token is not None
    
    def test_in_operator(self):
        """Test tokenizing IN operator"""
        lexer = Lexer("COUNTRY IN ('USA', 'UK', 'CANADA')")
        tokens = lexer.tokenize()
        
        assert tokens[1].type == TokenType.IN
        assert any(t.type == TokenType.LPAREN for t in tokens)
        assert any(t.type == TokenType.COMMA for t in tokens)
    
    def test_like_operator(self):
        """Test tokenizing LIKE operator"""
        lexer = Lexer("AETERM LIKE '%headache%'")
        tokens = lexer.tokenize()
        
        assert tokens[1].type == TokenType.LIKE
        assert tokens[2].value == "%headache%"
    
    def test_between_operator(self):
        """Test tokenizing BETWEEN operator"""
        lexer = Lexer("AGE BETWEEN 18 AND 65")
        tokens = lexer.tokenize()
        
        assert any(t.type == TokenType.BETWEEN for t in tokens)
        assert sum(1 for t in tokens if t.type == TokenType.AND) == 1


class TestParser:
    """Test the parser"""
    
    def test_simple_equality(self):
        """Test parsing simple equality"""
        lexer = Lexer("AESER = 'Y'")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == TokenType.EQ
        assert isinstance(ast.left, ColumnNode)
        assert ast.left.name == "AESER"
        assert isinstance(ast.right, LiteralNode)
        assert ast.right.value == "Y"
    
    def test_and_expression(self):
        """Test parsing AND expressions"""
        lexer = Lexer("AESER = 'Y' AND AGE >= 18")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == TokenType.AND
        assert isinstance(ast.left, BinaryOpNode)
        assert isinstance(ast.right, BinaryOpNode)
    
    def test_or_expression(self):
        """Test parsing OR expressions"""
        lexer = Lexer("AESER = 'Y' OR AESIDAT IS NOT NULL")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == TokenType.OR
    
    def test_parentheses(self):
        """Test parsing expressions with parentheses"""
        lexer = Lexer("(AESER = 'Y' AND AGE >= 18) OR COUNTRY = 'USA'")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == TokenType.OR
        assert isinstance(ast.left, BinaryOpNode)
        assert ast.left.operator == TokenType.AND
    
    def test_not_operator(self):
        """Test parsing NOT operator"""
        lexer = Lexer("NOT AESER = 'Y'")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, UnaryOpNode)
        assert ast.operator == TokenType.NOT
        assert isinstance(ast.operand, BinaryOpNode)
    
    def test_in_operator(self):
        """Test parsing IN operator"""
        lexer = Lexer("COUNTRY IN ('USA', 'UK')")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, InNode)
        assert ast.column.name == "COUNTRY"
        assert len(ast.values) == 2
        assert ast.values[0].value == "USA"
        assert ast.negate is False
    
    def test_not_in_operator(self):
        """Test parsing NOT IN operator"""
        lexer = Lexer("STATUS NOT IN ('WITHDRAWN', 'FAILED')")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, InNode)
        assert ast.negate is True
    
    def test_like_operator(self):
        """Test parsing LIKE operator"""
        lexer = Lexer("AETERM LIKE '%headache%'")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, LikeNode)
        assert ast.column.name == "AETERM"
        assert ast.pattern == "%headache%"
        assert ast.negate is False
    
    def test_between_operator(self):
        """Test parsing BETWEEN operator"""
        lexer = Lexer("AGE BETWEEN 18 AND 65")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, BetweenNode)
        assert ast.column.name == "AGE"
        assert ast.lower.value == 18
        assert ast.upper.value == 65
    
    def test_is_null(self):
        """Test parsing IS NULL"""
        lexer = Lexer("AESIDAT IS NULL")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, IsNullNode)
        assert ast.column.name == "AESIDAT"
        assert ast.negate is False
    
    def test_is_not_null(self):
        """Test parsing IS NOT NULL"""
        lexer = Lexer("AETERM IS NOT NULL")
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, IsNullNode)
        assert ast.column.name == "AETERM"
        assert ast.negate is True


class TestFilterParser:
    """Test the main FilterParser service"""
    
    def test_simple_filter(self):
        """Test parsing simple filter"""
        parser = FilterParser()
        result = parser.parse("AESER = 'Y'")
        
        assert result["is_valid"] is True
        assert result["error"] is None
        assert "AESER" in result["columns"]
        assert len(result["columns"]) == 1
    
    def test_complex_filter(self):
        """Test parsing complex filter"""
        parser = FilterParser()
        expression = "(AESER = 'Y' AND AETERM IS NOT NULL) OR (AGE >= 65 AND COUNTRY IN ('USA', 'UK'))"
        result = parser.parse(expression)
        
        assert result["is_valid"] is True
        assert set(result["columns"]) == {"AESER", "AETERM", "AGE", "COUNTRY"}
    
    def test_invalid_syntax(self):
        """Test parsing invalid syntax"""
        parser = FilterParser()
        result = parser.parse("AESER ==== 'Y'")
        
        assert result["is_valid"] is False
        assert result["error"] is not None
        assert result["ast"] is None
    
    def test_empty_expression(self):
        """Test parsing empty expression"""
        parser = FilterParser()
        result = parser.parse("")
        
        assert result["is_valid"] is False
        assert result["error"] is not None
    
    def test_ast_to_dict(self):
        """Test AST to dictionary conversion"""
        parser = FilterParser()
        result = parser.parse("AESER = 'Y' AND AGE >= 18")
        
        assert result["is_valid"] is True
        ast_dict = parser.ast_to_dict(result["ast"])
        
        assert ast_dict["type"] == "binary_op"
        assert ast_dict["operator"] == "AND"
        assert ast_dict["left"]["type"] == "binary_op"
        assert ast_dict["right"]["type"] == "binary_op"
    
    def test_all_operators(self):
        """Test all supported operators"""
        parser = FilterParser()
        
        test_cases = [
            ("COL = 'value'", True),
            ("COL != 'value'", True),
            ("COL < 10", True),
            ("COL <= 10", True),
            ("COL > 10", True),
            ("COL >= 10", True),
            ("COL IN ('A', 'B')", True),
            ("COL NOT IN ('A', 'B')", True),
            ("COL LIKE '%pattern%'", True),
            ("COL NOT LIKE '%pattern%'", True),
            ("COL IS NULL", True),
            ("COL IS NOT NULL", True),
            ("COL BETWEEN 1 AND 10", True),
            ("COL1 = 'A' AND COL2 = 'B'", True),
            ("COL1 = 'A' OR COL2 = 'B'", True),
            ("NOT COL = 'A'", True),
        ]
        
        for expression, expected_valid in test_cases:
            result = parser.parse(expression)
            assert result["is_valid"] == expected_valid, f"Failed for: {expression}"
    
    def test_column_extraction(self):
        """Test column extraction from complex expressions"""
        parser = FilterParser()
        
        test_cases = [
            ("AESER = 'Y'", ["AESER"]),
            ("AESER = 'Y' AND AETERM IS NOT NULL", ["AESER", "AETERM"]),
            ("COL1 IN ('A') OR COL2 LIKE '%B%' OR COL3 BETWEEN 1 AND 10", ["COL1", "COL2", "COL3"]),
            ("(A = 1 AND B = 2) OR (C = 3 AND D = 4)", ["A", "B", "C", "D"]),
        ]
        
        for expression, expected_columns in test_cases:
            result = parser.parse(expression)
            assert set(result["columns"]) == set(expected_columns), f"Failed for: {expression}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])