# Fresh Installation Setup Guide

This guide ensures all database configurations are properly set up after a fresh installation.

## Prerequisites

- Docker and Docker Compose installed
- Project cloned from repository
- Environment variables configured

## Setup Steps

### 1. Initial Setup

```bash
# Start the services
docker compose -f docker-compose.local-prod.yml up -d

# Wait for services to be ready (about 30 seconds)
sleep 30
```

### 2. Run Database Migrations

```bash
# Apply all database migrations
docker compose -f docker-compose.local-prod.yml exec backend alembic upgrade head
```

### 3. Run Post-Installation Setup

```bash
# Create default organization and configure admin user
docker compose -f docker-compose.local-prod.yml exec backend python scripts/post_install_setup.py
```

### 4. Verify Setup

```bash
# Check that organization exists
docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT id, name FROM organization;"

# Check admin user has organization
docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT email, org_id FROM \"user\" WHERE is_superuser = true;"

# Check enum values are correct
docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT enum_range(NULL::studystatus);"
```

## Expected Database State After Setup

### 1. Organization
- At least one organization exists (default: "Sagarmatha AI")
- Admin user is assigned to an organization

### 2. Study Status Enum
- Values: `DRAFT`, `PLANNING`, `SETUP`, `ACTIVE`, `PAUSED`, `COMPLETED`, `ARCHIVED`
- All uppercase

### 3. Template Status Enum  
- Values: `PUBLISHED`, `DEPRECATED`, `ARCHIVED`
- No DRAFT status (all templates are published by default)
- All uppercase

### 4. Study Table Columns
All the following columns should exist:
- `initialization_status`
- `initialization_progress`
- `initialization_steps`
- `template_applied_at`
- `data_uploaded_at`
- `mappings_configured_at`
- `activated_at`
- `last_transformation_at`
- `transformation_status`
- `transformation_count`
- `derived_datasets`
- `transformation_errors`

## Troubleshooting

### If migrations fail

1. Check current migration status:
```bash
docker compose -f docker-compose.local-prod.yml exec backend alembic current
```

2. If needed, downgrade and upgrade again:
```bash
docker compose -f docker-compose.local-prod.yml exec backend alembic downgrade -1
docker compose -f docker-compose.local-prod.yml exec backend alembic upgrade head
```

### If enum values are incorrect

The migration `ff71440d9654_fix_enum_values_and_add_missing_columns.py` should fix all enum issues automatically. If problems persist:

1. Check enum values:
```bash
docker compose -f docker-compose.local-prod.yml exec postgres psql -U postgres -d clinical_dashboard -c "SELECT enum_range(NULL::studystatus);"
```

2. Manually run the post-install setup:
```bash
docker compose -f docker-compose.local-prod.yml exec backend python scripts/post_install_setup.py
```

### If admin user has no organization

Run the create_default_org script:
```bash
docker compose -f docker-compose.local-prod.yml exec backend python scripts/create_default_org.py
```

## Development vs Production

For development, use `docker-compose.local-prod.yml` as shown above.

For production deployment, replace with your production compose file and ensure:
1. Proper environment variables are set
2. Database backups are configured
3. SSL certificates are in place
4. Monitoring is enabled