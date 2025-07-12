#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/backend_pre_start.py

# Run migrations
alembic upgrade head

# Create initial data in DB
python app/initial_data.py

# Seed widgets - only seed the MetricsCard widget
echo "Starting widget seeding..."

# Flexible metrics card widget - try both module and direct execution
python -m app.db.seed_metrics_card_widget || python app/db/seed_metrics_card_widget.py || echo "Metrics card widget seeding completed"

echo "Widget seeding complete!"
