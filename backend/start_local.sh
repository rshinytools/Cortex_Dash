#!/bin/bash
# ABOUTME: Quick start script for local development
# ABOUTME: Sets up and runs the backend API server with all dependencies

echo "🚀 Clinical Dashboard Backend - Local Development Setup"
echo "======================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL connection..."
if ! python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='changethis'
    )
    conn.close()
    print('✅ PostgreSQL is running')
except:
    print('❌ PostgreSQL is not running')
    print('   Please run: docker-compose -f ../docker-compose.local.yml up -d postgres')
    exit(1)
" 2>/dev/null; then
    echo "⚠️  PostgreSQL is not accessible. Starting Docker services..."
    cd .. && docker-compose -f docker-compose.local.yml up -d postgres redis
    cd backend
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if ! python -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379)
    r.ping()
    print('✅ Redis is running')
except:
    print('❌ Redis is not running')
    print('   Please run: docker-compose -f ../docker-compose.local.yml up -d redis')
" 2>/dev/null; then
    echo "⚠️  Redis is not accessible. Starting Redis..."
    cd .. && docker-compose -f docker-compose.local.yml up -d redis
    cd backend
    sleep 2
fi

# Create database if it doesn't exist
echo "📊 Setting up database..."
python -c "
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='changethis'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Check if database exists
    cur.execute(\"SELECT 1 FROM pg_database WHERE datname='clinical_dashboard'\")
    exists = cur.fetchone()
    
    if not exists:
        cur.execute('CREATE DATABASE clinical_dashboard')
        print('✅ Database created')
    else:
        print('✅ Database already exists')
    
    cur.close()
    conn.close()
except Exception as e:
    print(f'❌ Database setup failed: {e}')
"

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Initialize database with superuser
echo "👤 Initializing database..."
python -c "
from app.core.db import init_db
from sqlmodel import Session, create_engine
from app.core.config import settings

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
with Session(engine) as session:
    init_db(session)
print('✅ Database initialized')
"

# Start the server
echo ""
echo "🎉 Starting FastAPI server..."
echo "==============================="
echo "📍 API URL: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "📊 ReDoc: http://localhost:8000/redoc"
echo "🔑 Default login: admin@example.com / changethis"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000