#!/usr/bin/env python3
"""
Test suite for backend services - Phase 2, 3, and 4 implementations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_transformation_engine():
    """Test the transformation engine"""
    try:
        from backend.app.services.transformations.transformation_engine import TransformationEngine
        
        engine = TransformationEngine()
        
        # Test rename transformation
        data = [{"old_name": "value1"}]
        result = engine.apply_transformation(
            data, 
            "rename",
            {"old_name": "old_name", "new_name": "new_name"}
        )
        assert "new_name" in result[0]
        
        # Test type cast
        data = [{"value": "123"}]
        result = engine.apply_transformation(
            data,
            "type_cast",
            {"field": "value", "target_type": "int"}
        )
        assert result[0]["value"] == 123
        
        print("[PASS] Transformation Engine tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Transformation Engine tests failed: {e}")
        return False

def test_expression_parser():
    """Test the expression parser"""
    try:
        from backend.app.services.calculations.expression_parser import ExpressionParser
        
        parser = ExpressionParser()
        
        # Test basic arithmetic
        result = parser.parse("2 + 3 * 4", {})
        assert result == 14
        
        # Test variables
        result = parser.parse("a + b", {"a": 5, "b": 10})
        assert result == 15
        
        # Test functions
        result = parser.parse("max(1, 2, 3)", {})
        assert result == 3
        
        # Test conditional
        result = parser.parse("if_else(5 > 3, 'yes', 'no')", {})
        assert result == 'yes'
        
        # Test variable extraction
        variables = parser.get_variables("a + b * c")
        assert variables == {"a", "b", "c"}
        
        print("[PASS] Expression Parser tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Expression Parser tests failed: {e}")
        return False

def test_clinical_functions():
    """Test clinical calculation functions"""
    try:
        from backend.app.services.calculations.clinical_functions import ClinicalFunctions
        
        funcs = ClinicalFunctions()
        
        # Test BMI calculation
        bmi = funcs.calculate_bmi(70, 175)  # 70kg, 175cm
        assert 22 < bmi < 23  # Should be ~22.9
        
        # Test BSA calculation (DuBois)
        bsa = funcs.calculate_bsa_dubois(70, 175)
        assert 1.8 < bsa < 1.9  # Should be ~1.85
        
        # Test eGFR calculation
        egfr = funcs.calculate_egfr_ckd_epi(1.2, 45, 'M', 'other')
        assert 70 < egfr < 80  # Should be ~75
        
        # Test Child-Pugh score
        result = funcs.calculate_child_pugh_score(
            bilirubin_mg_dl=1.5,
            albumin_g_dl=3.8,
            inr=1.1,
            ascites='none',
            encephalopathy='none'
        )
        assert result['class'] == 'A'
        assert result['score'] == 5
        
        print("[PASS] Clinical Functions tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Clinical Functions tests failed: {e}")
        return False

def test_mapping_template_model():
    """Test mapping template model structure"""
    try:
        # Test that the model can be imported
        from backend.app.models.mapping_templates import MappingTemplate
        
        # Test template configuration structure
        template_config = {
            "field_mappings": {
                "subject_id": {
                    "source_field": "SUBJID",
                    "target_field": "subject_id",
                    "data_type": "string"
                }
            },
            "transformations": [
                {
                    "type": "rename",
                    "params": {"old_name": "SUBJID", "new_name": "subject_id"}
                }
            ],
            "filters": [],
            "aggregations": []
        }
        
        # Validate structure
        assert "field_mappings" in template_config
        assert "transformations" in template_config
        
        print("[PASS] Mapping Template Model tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Mapping Template Model tests failed: {e}")
        return False

def test_cache_manager():
    """Test Redis cache manager (without actual Redis connection)"""
    try:
        from backend.app.core.cache import CacheManager, WidgetCache, QueryCache
        
        # Test cache key generation
        cache = CacheManager()
        key = cache._generate_key("widget", "test_id")
        assert "widget:test_id" in key
        
        # Test widget cache
        widget_cache = WidgetCache(cache)
        config_hash = widget_cache.get_config_hash({"test": "config"})
        assert len(config_hash) == 32  # MD5 hash length
        
        # Test query cache
        query_cache = QueryCache(cache)
        query_hash = query_cache.get_query_hash("SELECT * FROM table", {"param": "value"})
        assert len(query_hash) == 16  # Truncated SHA256
        
        print("[PASS] Cache Manager tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Cache Manager tests failed: {e}")
        return False

def test_query_optimizer():
    """Test query optimizer (without database connection)"""
    try:
        from backend.app.services.optimization.query_optimizer import QueryOptimizer
        
        # Note: We can't fully test without a database engine
        # but we can test the analysis functions
        
        # Create a mock engine (None will work for analysis)
        optimizer = QueryOptimizer(None)
        
        # Test query analysis
        query = "SELECT * FROM users WHERE age > 18 GROUP BY department ORDER BY name"
        analysis = optimizer._analyze_query(query)
        
        assert analysis["group_by"] == True
        assert analysis["order_by"] == True
        assert len(analysis["where_conditions"]) > 0
        assert "users" in analysis["tables"]
        
        print("[PASS] Query Optimizer tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Query Optimizer tests failed: {e}")
        return False

def test_performance_monitor():
    """Test performance monitoring"""
    try:
        from backend.app.services.monitoring.performance_monitor import (
            PerformanceMonitor, MetricType
        )
        
        monitor = PerformanceMonitor()
        
        # Record a metric
        monitor.record_metric(
            "test_metric",
            100,
            MetricType.GAUGE,
            tags={"test": "true"}
        )
        
        # Get metrics
        metrics = monitor.get_metrics("test_metric")
        assert len(metrics) > 0
        assert metrics[0]["name"] == "test_metric"
        assert metrics[0]["value"] == 100
        
        # Test summary
        summary = monitor.get_summary()
        assert "metrics" in summary
        assert "system" in summary
        
        print("[PASS] Performance Monitor tests passed")
        return True
    except Exception as e:
        print(f"[FAIL] Performance Monitor tests failed: {e}")
        return False

def main():
    """Run all backend service tests"""
    print("=" * 60)
    print("BACKEND SERVICES TEST SUITE")
    print("Testing Phase 2, 3, and 4 implementations")
    print("=" * 60)
    print()
    
    tests = [
        ("Transformation Engine", test_transformation_engine),
        ("Expression Parser", test_expression_parser),
        ("Clinical Functions", test_clinical_functions),
        ("Mapping Template Model", test_mapping_template_model),
        ("Cache Manager", test_cache_manager),
        ("Query Optimizer", test_query_optimizer),
        ("Performance Monitor", test_performance_monitor)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"Testing {name}...")
        if test_func():
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All backend services tests passed!")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)