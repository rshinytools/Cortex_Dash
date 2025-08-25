# ABOUTME: Test script for widget filtering integration
# ABOUTME: Tests end-to-end filtering functionality

import asyncio
import pandas as pd
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Study
from app.services.widget_data_executor_real import RealWidgetExecutor, WidgetDataRequest
from app.models.widget import WidgetDefinition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_filter_integration():
    """Test the filter integration with widget executor"""
    
    # Setup database connection
    database_url = f"postgresql://postgres:changethis@postgres:5432/clinical_dashboard"
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get the demo study
        study = db.query(Study).filter(Study.name == "Demo Study").first()
        if not study:
            logger.error("Demo study not found")
            return
        
        logger.info(f"Found study: {study.name} (ID: {study.id})")
        
        # Create a mock widget definition
        widget_def = WidgetDefinition(
            id="test-widget",
            name="Test Widget",
            category="metrics",
            widget_type="kpi"
        )
        
        # Initialize the executor
        executor = RealWidgetExecutor(db, study, widget_def)
        
        # Test 1: Execute without filter
        logger.info("\n=== Test 1: Execute without filter ===")
        request = WidgetDataRequest(
            widget_id="subjects_enrolled_value",
            widget_config={
                "id": "subjects_enrolled_value",
                "title": "Subjects Enrolled"
            }
        )
        
        result = await executor.execute(request)
        logger.info(f"Result without filter: {result.data}")
        
        # Test 2: Add a filter to the study
        logger.info("\n=== Test 2: Add filter configuration ===")
        study.field_mapping_filters = {
            "subjects_enrolled_value": {
                "expression": "AGE >= 18",
                "enabled": True
            }
        }
        db.add(study)
        db.commit()
        
        # Re-initialize executor with updated study
        executor = RealWidgetExecutor(db, study, widget_def)
        
        # Test 3: Execute with filter
        logger.info("\n=== Test 3: Execute with filter ===")
        result_filtered = await executor.execute(request)
        logger.info(f"Result with filter: {result_filtered.data}")
        
        # Compare results
        if result.data and result_filtered.data:
            original_value = result.data.get("value", 0)
            filtered_value = result_filtered.data.get("value", 0)
            logger.info(f"\nComparison:")
            logger.info(f"  Original count: {original_value}")
            logger.info(f"  Filtered count: {filtered_value}")
            logger.info(f"  Reduction: {original_value - filtered_value}")
        
        # Clean up - remove filter
        study.field_mapping_filters = {}
        db.add(study)
        db.commit()
        
        logger.info("\n✅ Filter integration test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def test_filter_parser():
    """Test the filter parser directly"""
    from app.services.filter_parser import FilterParser
    
    parser = FilterParser()
    
    test_cases = [
        "AGE >= 18",
        "AESER = 'Y' AND AETERM IS NOT NULL",
        "(AGE >= 65 AND COUNTRY = 'USA') OR AESEV IN ('SEVERE', 'LIFE THREATENING')",
        "VISITNUM BETWEEN 1 AND 5",
        "AETERM LIKE '%headache%'"
    ]
    
    logger.info("\n=== Testing Filter Parser ===")
    for expression in test_cases:
        result = parser.parse(expression)
        logger.info(f"\nExpression: {expression}")
        logger.info(f"  Valid: {result['is_valid']}")
        logger.info(f"  Columns: {result['columns']}")
        if not result['is_valid']:
            logger.info(f"  Error: {result['error']}")


def test_filter_executor():
    """Test the filter executor directly"""
    from app.services.filter_executor import FilterExecutor
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import tempfile
    
    # Create test data
    df = pd.DataFrame({
        'USUBJID': ['001', '002', '003', '004', '005'],
        'AGE': [25, 45, 65, 17, 70],
        'AESER': ['Y', 'N', 'Y', 'N', 'Y'],
        'COUNTRY': ['USA', 'UK', 'USA', 'CANADA', 'UK']
    })
    
    # Save to temporary parquet file
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        df.to_parquet(f.name)
        temp_path = f.name
    
    try:
        # Setup database connection
        database_url = f"postgresql://postgres:changethis@postgres:5432/clinical_dashboard"
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        executor = FilterExecutor(db)
        
        logger.info("\n=== Testing Filter Executor ===")
        
        # Test different filters
        filters = [
            "AGE >= 18",
            "AESER = 'Y'",
            "AGE >= 18 AND AESER = 'Y'",
            "COUNTRY IN ('USA', 'UK')"
        ]
        
        for filter_expr in filters:
            result = executor.execute_filter(
                study_id="test",
                widget_id="test",
                filter_expression=filter_expr,
                dataset_path=temp_path,
                track_metrics=False
            )
            
            logger.info(f"\nFilter: {filter_expr}")
            logger.info(f"  Original rows: {result['original_count']}")
            logger.info(f"  Filtered rows: {result['row_count']}")
            logger.info(f"  Reduction: {result['reduction_percentage']}%")
            
            if "error" in result:
                logger.error(f"  Error: {result['error']}")
        
        db.close()
        
    finally:
        # Clean up
        Path(temp_path).unlink()


if __name__ == "__main__":
    # Run tests
    logger.info("Starting filter integration tests...\n")
    
    # Test individual components
    test_filter_parser()
    test_filter_executor()
    
    # Test full integration
    asyncio.run(test_filter_integration())