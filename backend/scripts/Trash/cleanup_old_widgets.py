#!/usr/bin/env python3
# ABOUTME: Script to remove all old widgets and keep only MetricsCard
# ABOUTME: Used to clean up widget library from old approach

from sqlmodel import Session, select
from app.core.db import engine
from app.models import WidgetDefinition

def cleanup_old_widgets():
    """Remove all widgets except metrics_card_flexible"""
    session = Session(engine)
    
    try:
        # Get all widgets except metrics_card_flexible
        old_widgets = session.exec(
            select(WidgetDefinition).where(WidgetDefinition.code != 'metrics_card_flexible')
        ).all()
        
        print(f"Found {len(old_widgets)} old widgets to remove:")
        for widget in old_widgets:
            print(f"  - {widget.code}: {widget.name}")
        
        # Delete all old widgets using raw SQL to avoid cascade issues
        if old_widgets:
            widget_ids = [widget.id for widget in old_widgets]
            
            # Delete widgets directly using SQL
            from sqlalchemy import text
            session.exec(text(
                "DELETE FROM widget_definitions WHERE id = ANY(:ids)"
            ).params(ids=widget_ids))
            session.commit()
            print(f"\n✅ Removed {len(old_widgets)} old widgets")
        else:
            print("\n✅ No old widgets to remove")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        session.rollback()
        raise
    
    # Verify only MetricsCard remains
    remaining = session.exec(select(WidgetDefinition)).all()
    print(f"\n📋 Remaining widgets:")
    for widget in remaining:
        print(f"  - {widget.code}: {widget.name}")
    
    session.close()

if __name__ == "__main__":
    cleanup_old_widgets()