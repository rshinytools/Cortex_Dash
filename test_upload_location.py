#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="clinical_dashboard",
    user="postgres",
    password="changethis"
)

study_id = '521b4b98-87ec-4643-9103-eae78e2dad79'

with conn.cursor(cursor_factory=RealDictCursor) as cur:
    # Get the study data
    cur.execute("""
        SELECT id, name, config, initialization_steps
        FROM studies
        WHERE id = %s
    """, (study_id,))
    
    study = cur.fetchone()
    if study:
        print(f"Study: {study['name']}")
        print(f"\nConfig keys:")
        if study['config']:
            for key in study['config'].keys():
                print(f"  - {key}")
                if key in ['uploaded_files', 'pending_uploads']:
                    files = study['config'][key]
                    print(f"    Found {len(files)} files in config.{key}")
        
        print(f"\nInitialization_steps keys:")
        if study['initialization_steps']:
            for key in study['initialization_steps'].keys():
                print(f"  - {key}")
                if key in ['uploaded_files', 'pending_uploads', 'wizard_state']:
                    if key == 'wizard_state':
                        wizard_state = study['initialization_steps'][key]
                        if 'data' in wizard_state and 'uploaded_files' in wizard_state['data']:
                            files = wizard_state['data']['uploaded_files']
                            print(f"    Found {len(files)} files in wizard_state.data.uploaded_files")
                    else:
                        files = study['initialization_steps'][key]
                        print(f"    Found {len(files)} files in initialization_steps.{key}")

conn.close()
