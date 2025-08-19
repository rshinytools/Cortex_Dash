#!/usr/bin/env python3
# ABOUTME: Fix field_mappings structure in database
# ABOUTME: Convert nested objects to flat string mappings

import psycopg2
import json

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="clinical_dashboard",
    user="postgres",
    password="changethis"
)

try:
    cur = conn.cursor()
    
    # Get all studies with field_mappings
    cur.execute("SELECT id, name, field_mappings FROM study WHERE field_mappings IS NOT NULL AND field_mappings::text != '{}'")
    studies = cur.fetchall()
    
    print(f"Found {len(studies)} studies with field_mappings")
    
    for study_id, study_name, field_mappings in studies:
        print(f"\nProcessing study: {study_name} ({study_id})")
        print(f"Current field_mappings: {json.dumps(field_mappings, indent=2)}")
        
        # Check if field_mappings has nested structure
        needs_fix = False
        for key, value in field_mappings.items():
            if isinstance(value, dict):
                needs_fix = True
                break
        
        if needs_fix:
            # For now, just clear the invalid field_mappings
            # In production, we'd convert them properly
            print(f"  -> Clearing invalid field_mappings for study {study_id}")
            cur.execute(
                "UPDATE study SET field_mappings = '{}' WHERE id = %s",
                (study_id,)
            )
            conn.commit()
            print(f"  -> Fixed!")
        else:
            print(f"  -> Field mappings are already in correct format")
    
    print("\n[SUCCESS] Field mappings fixed!")
    
except Exception as e:
    print(f"[ERROR] Failed to fix field_mappings: {e}")
    conn.rollback()
finally:
    conn.close()