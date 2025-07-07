#!/usr/bin/env python3
# ABOUTME: Test script for widget data execution engine
# ABOUTME: Creates sample widgets and tests data retrieval

import asyncio
import uuid
from datetime import datetime

from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.models import Study, WidgetDefinition, DashboardTemplate
from app.services.widget_data_executor import (
    WidgetDataRequest, WidgetDataExecutorFactory, WidgetCategory
)
from app.services.redis_cache import cache


async def test_widget_data_execution():
    """Test widget data execution with mock data"""
    
    # Create a database session
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    with Session(engine) as db:
        # Get a test study
        stmt = select(Study).limit(1)
        study = db.execute(stmt).scalars().first()
        
        if not study:
            print("No study found in database. Please create a study first.")
            return
        
        print(f"Using study: {study.name} (ID: {study.id})")
        
        # Create or get widget definitions
        widget_definitions = []
        
        # 1. Metric widget
        metric_widget = db.execute(
            select(WidgetDefinition).where(WidgetDefinition.code == "metric_card")
        ).scalars().first()
        
        if not metric_widget:
            metric_widget = WidgetDefinition(
                code="metric_card",
                name="Metric Card",
                description="Display a single metric value",
                category=WidgetCategory.METRICS,
                config_schema={
                    "type": "object",
                    "properties": {
                        "aggregation": {"type": "string", "enum": ["count", "sum", "avg", "min", "max"]},
                        "field": {"type": "string"},
                        "dataset": {"type": "string"},
                        "label": {"type": "string"}
                    }
                },
                created_by=uuid.uuid4()  # Replace with actual user ID
            )
            db.add(metric_widget)
            db.commit()
            db.refresh(metric_widget)
        
        widget_definitions.append(metric_widget)
        
        # 2. Chart widget
        chart_widget = db.execute(
            select(WidgetDefinition).where(WidgetDefinition.code == "line_chart")
        ).scalars().first()
        
        if not chart_widget:
            chart_widget = WidgetDefinition(
                code="line_chart",
                name="Line Chart",
                description="Display data as a line chart",
                category=WidgetCategory.CHARTS,
                config_schema={
                    "type": "object",
                    "properties": {
                        "chart_type": {"type": "string", "enum": ["line", "bar", "pie"]},
                        "x_axis_field": {"type": "string"},
                        "y_axis_field": {"type": "string"},
                        "dataset": {"type": "string"}
                    }
                },
                created_by=uuid.uuid4()  # Replace with actual user ID
            )
            db.add(chart_widget)
            db.commit()
            db.refresh(chart_widget)
        
        widget_definitions.append(chart_widget)
        
        # 3. Table widget
        table_widget = db.execute(
            select(WidgetDefinition).where(WidgetDefinition.code == "data_table")
        ).scalars().first()
        
        if not table_widget:
            table_widget = WidgetDefinition(
                code="data_table",
                name="Data Table",
                description="Display data in a table format",
                category=WidgetCategory.TABLES,
                config_schema={
                    "type": "object",
                    "properties": {
                        "columns": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string"},
                                    "label": {"type": "string"},
                                    "type": {"type": "string"}
                                }
                            }
                        },
                        "dataset": {"type": "string"}
                    }
                },
                created_by=uuid.uuid4()  # Replace with actual user ID
            )
            db.add(table_widget)
            db.commit()
            db.refresh(table_widget)
        
        widget_definitions.append(table_widget)
        
        # Connect to Redis
        await cache.connect()
        
        # Test each widget type
        print("\n=== Testing Widget Data Execution ===\n")
        
        # 1. Test Metric Widget
        print("1. Testing Metric Widget...")
        metric_request = WidgetDataRequest(
            widget_id="metric_1",
            widget_config={
                "aggregation": "count",
                "field": "USUBJID",
                "dataset": "ADSL",
                "label": "Total Subjects"
            }
        )
        
        metric_executor = WidgetDataExecutorFactory.create_executor(db, study, metric_widget)
        metric_response = await metric_executor.execute(metric_request)
        
        print(f"   Result: {metric_response.data}")
        print(f"   Execution time: {metric_response.execution_time_ms}ms")
        
        # 2. Test Chart Widget
        print("\n2. Testing Chart Widget...")
        chart_request = WidgetDataRequest(
            widget_id="chart_1",
            widget_config={
                "chart_type": "line",
                "x_axis_field": "VISITDT",
                "y_axis_field": "SUBJCOUNT",
                "dataset": "ADSL"
            }
        )
        
        chart_executor = WidgetDataExecutorFactory.create_executor(db, study, chart_widget)
        chart_response = await chart_executor.execute(chart_request)
        
        print(f"   Chart type: {chart_response.data['chart_type']}")
        print(f"   Series count: {len(chart_response.data['series'])}")
        print(f"   Data points: {chart_response.metadata['data_points']}")
        
        # 3. Test Table Widget
        print("\n3. Testing Table Widget...")
        table_request = WidgetDataRequest(
            widget_id="table_1",
            widget_config={
                "columns": [
                    {"field": "USUBJID", "label": "Subject ID", "type": "string"},
                    {"field": "AGE", "label": "Age", "type": "number"},
                    {"field": "SEX", "label": "Sex", "type": "string"},
                    {"field": "COUNTRY", "label": "Country", "type": "string"}
                ],
                "dataset": "ADSL"
            },
            pagination={"page": 1, "page_size": 10}
        )
        
        table_executor = WidgetDataExecutorFactory.create_executor(db, study, table_widget)
        table_response = await table_executor.execute(table_request)
        
        print(f"   Total rows: {table_response.data['total_rows']}")
        print(f"   Page: {table_response.data['page']} of {table_response.data['total_pages']}")
        print(f"   Rows returned: {len(table_response.data['rows'])}")
        
        # Test caching
        print("\n=== Testing Cache ===\n")
        
        # Cache the metric data
        cache_key = f"widget_data:{study.id}:metric_1:dashboard_1"
        await cache.set(cache_key, metric_response.model_dump(mode="json"), ttl=300)
        
        # Retrieve from cache
        cached_data = await cache.get(cache_key)
        if cached_data:
            print("✓ Successfully cached and retrieved widget data")
            print(f"  Cached value: {cached_data['data']['value']}")
        else:
            print("✗ Cache test failed")
        
        # Test cache invalidation
        await cache.delete(cache_key)
        deleted_data = await cache.get(cache_key)
        if deleted_data is None:
            print("✓ Successfully invalidated cache")
        else:
            print("✗ Cache invalidation failed")
        
        # Disconnect from Redis
        await cache.disconnect()
        
        print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_widget_data_execution())