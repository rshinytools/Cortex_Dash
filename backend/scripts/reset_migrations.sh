#!/bin/bash
# ABOUTME: Script to reset migrations and create a single clean migration
# ABOUTME: Preserves model structure while fixing migration conflicts

set -e

echo "🔄 Resetting migrations..."

# 1. Remove all existing migrations except __init__.py
echo "📁 Backing up migrations..."
mkdir -p ../migration_backup_$(date +%Y%m%d_%H%M%S)
cp -r app/alembic/versions/* ../migration_backup_$(date +%Y%m%d_%H%M%S)/ || true

echo "🗑️  Removing old migrations..."
find app/alembic/versions -name "*.py" -not -name "__init__.py" -delete

# 2. Create a single new migration with all current models
echo "📝 Creating fresh migration..."
alembic revision --autogenerate -m "initial_schema_all_models"

echo "✅ Migration reset complete!"
echo "📌 Next steps:"
echo "   1. Review the generated migration in app/alembic/versions/"
echo "   2. Run 'alembic upgrade head' to apply"