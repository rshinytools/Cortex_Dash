#!/bin/bash
# ABOUTME: Startup script for backend container
# ABOUTME: Ensures database is initialized and ready before starting the application

set -e

echo "Starting Cortex Dashboard Backend..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Function to check if database is initialized
check_db_initialized() {
    python -c "
from sqlmodel import Session, select
from app.core.db import engine
from app.models import Organization
try:
    with Session(engine) as session:
        org = session.exec(select(Organization).limit(1)).first()
        if org:
            print('Database already initialized')
            exit(0)
        else:
            exit(1)
except Exception as e:
    print(f'Database not initialized: {e}')
    exit(1)
"
}

# Check if database needs initialization
if ! check_db_initialized; then
    echo "Database not initialized. Running setup..."
    
    # Initialize database with tables
    echo "Initializing database tables..."
    python scripts/init_db.py || {
        echo "Database initialization failed!"
        exit 1
    }
    
    # Run post-installation setup
    echo "Running post-installation setup..."
    python scripts/post_install_setup.py || {
        echo "Post-install setup failed, trying alternative method..."
        python scripts/create_default_org.py || true
    }
    
    echo "Database initialization complete!"
    
    # Initialize RBAC data
    echo "Initializing RBAC system..."
    python scripts/init_rbac_data.py || echo "RBAC initialization failed or already exists"
    
    # Initialize Widget definitions
    echo "Initializing widget definitions..."
    python scripts/create_widgets.py || echo "Widget initialization failed or already exists"
else
    echo "Database already initialized, checking for pending migrations..."
    alembic upgrade head || echo "No pending migrations or migration check failed"
    
    # Check and initialize RBAC data if needed
    python scripts/init_rbac_data.py 2>/dev/null || true
    
    # Check and initialize Widget definitions if needed
    python scripts/create_widgets.py 2>/dev/null || true
fi

# Verify admin user and organization are properly configured
python -c "
from sqlmodel import Session, select
from app.core.db import engine
from app.models import User, Organization
from app.core.security import get_password_hash

with Session(engine) as session:
    # Ensure organization has proper JSON fields
    org = session.exec(select(Organization).limit(1)).first()
    if org:
        if org.features is None:
            org.features = {}
        if hasattr(org, 'compliance_settings') and org.compliance_settings is None:
            org.compliance_settings = {}
        session.add(org)
        session.commit()
    
    # Ensure admin user exists and is configured properly
    admin = session.exec(select(User).where(User.email == 'admin@sagarmatha.ai')).first()
    if not admin:
        # Create admin if doesn't exist
        admin = User(
            email='admin@sagarmatha.ai',
            hashed_password=get_password_hash('adadad123'),
            full_name='System Administrator',
            is_active=True,
            is_superuser=True,
            org_id=org.id if org else None,
            role='system_admin'
        )
        session.add(admin)
        session.commit()
        print('Created admin user')
    else:
        # Fix existing admin user
        if admin.org_id is None and org:
            admin.org_id = org.id
        if admin.role != 'system_admin':
            admin.role = 'system_admin'
        session.add(admin)
        session.commit()
        print('Admin user configured correctly')
" || true

echo "Starting FastAPI application in production mode..."
# Start the application with gunicorn for production
exec gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000