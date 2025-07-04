# ABOUTME: Script to generate Alembic migration for clinical models
# ABOUTME: Creates migration for Organization, Study, ActivityLog, and DataSource models

"""
Generate initial migration for clinical models
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models to ensure they're registered
from app import models

print("Creating migration for clinical models...")
print("\nTo generate the migration, run these commands:")
print("\n1. Install dependencies:")
print("   pip install -r requirements.txt")
print("\n2. Set up PostgreSQL database:")
print("   createdb clinical_dashboard")
print("\n3. Generate migration:")
print("   cd backend")
print("   alembic revision --autogenerate -m 'Add clinical models - Organization, Study, ActivityLog, DataSource'")
print("\n4. Apply migration:")
print("   alembic upgrade head")
print("\nNote: Make sure PostgreSQL is running and the database connection in .env is correct.")