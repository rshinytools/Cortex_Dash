#!/bin/bash

# ABOUTME: Script to add new widgets to a running production system
# ABOUTME: Use this when adding new features without full restart

set -e

WIDGET_NAME=${1:-"metrics_card"}

echo "➕ Adding new widget: $WIDGET_NAME"

# Find the backend container
BACKEND_CONTAINER=$(docker ps -qf "name=backend" | head -1)

if [ -z "$BACKEND_CONTAINER" ]; then
    echo "❌ Backend container not found. Is the system running?"
    exit 1
fi

# Run the widget seeding
echo "🌱 Seeding widget into database..."
docker exec $BACKEND_CONTAINER python -m app.db.seed_${WIDGET_NAME}_widget

echo "✅ Widget added successfully!"
echo "🔄 Users may need to refresh their browser to see the new widget."