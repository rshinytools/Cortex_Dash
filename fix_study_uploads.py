#!/usr/bin/env python3
import json
import psycopg2
from pathlib import Path

# Database connection
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='clinical_dashboard',
    user='postgres',
    password='changethis'
)

study_id = '521b4b98-87ec-4643-9103-eae78e2dad79'
upload_dir = Path('/c/Users/amuly/OneDrive/AetherClinical/Cortex_Dash/data/studies/5d955318-0776-45b6-b0da-f6532e386a90/521b4b98-87ec-4643-9103-eae78e2dad79/source_data/20250818_203614')

# Build file list from existing files
uploaded_files = []
for sas_file in upload_dir.glob('*.sas7bdat'):
    uploaded_files.append({
        "name": sas_file.name,
        "path": str(sas_file),
        "size": sas_file.stat().st_size,
        "type": "sas7bdat",
        "uploaded_at": "2025-08-18T20:36:00"
    })

print(f"Found {len(uploaded_files)} SAS files")

with conn.cursor() as cur:
    # Update initialization_steps to add pending_uploads
    cur.execute('''
        UPDATE study
        SET initialization_steps = initialization_steps || %s::jsonb
        WHERE id = %s
    ''', (json.dumps({"pending_uploads": uploaded_files}), study_id))
    
    conn.commit()
    print(f"Updated study with {len(uploaded_files)} pending uploads")

conn.close()
