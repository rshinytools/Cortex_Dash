# Production Deployment Guide

## Overview

This guide explains how to deploy updates to production without disrupting users.

## Key Principles

1. **Data Persistence**: All user data is stored in Docker volumes that persist between deployments
2. **Zero Downtime**: Use rolling updates to maintain service availability
3. **Database Migrations**: Always run through Alembic to preserve data integrity
4. **Feature Flags**: Consider using feature flags for gradual rollouts

## Deployment Scenarios

### 1. Full Restart (Development Only)
```bash
make restart-all-prod
```
- ⚠️ **WARNING**: This stops all services temporarily
- ✅ Use only in development or during maintenance windows
- All data is preserved in Docker volumes

### 2. Rolling Update (Production Recommended)
```bash
./scripts/production-update.sh
```
- ✅ Zero downtime deployment
- ✅ Updates services one by one
- ✅ Maintains user sessions where possible

### 3. Adding New Features
```bash
# For new widgets
./scripts/add-new-widget.sh metrics_card

# For database schema changes
docker exec <backend-container> alembic upgrade head
```

### 4. Quick Code Updates
```bash
# Update only backend
docker-compose -f docker-compose.prod.yml up -d --no-deps backend

# Update only frontend
docker-compose -f docker-compose.prod.yml up -d --no-deps frontend
```

## Data Persistence

### What Persists:
- PostgreSQL database (in `postgres_data` volume)
- Uploaded files (in `app_data` volume)
- User configurations
- Study data and transformations

### What Doesn't Persist:
- Redis cache (rebuilds automatically)
- Active sessions (users may need to log in again)
- In-progress background jobs

## Production Checklist

Before deploying:
- [ ] Test changes in development
- [ ] Create database backup: `docker exec <db-container> pg_dump -U postgres app > backup.sql`
- [ ] Review migration scripts
- [ ] Notify users of maintenance (if needed)
- [ ] Monitor logs during deployment

After deploying:
- [ ] Verify application health endpoint
- [ ] Check critical features
- [ ] Monitor error logs
- [ ] Confirm new features are available

## Backup and Recovery

### Backup Database
```bash
# Create backup
docker exec $(docker ps -qf "name=db") pg_dump -U postgres app > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker exec -i $(docker ps -qf "name=db") psql -U postgres app < backup.sql
```

### Backup Files
```bash
# Backup uploaded files
docker run --rm -v cortex_dash_app_data:/data -v $(pwd):/backup alpine tar czf /backup/files_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

## Monitoring

- Health endpoint: `http://localhost/api/health`
- Logs: `docker-compose -f docker-compose.prod.yml logs -f backend`
- Database: `docker exec -it $(docker ps -qf "name=db") psql -U postgres app`

## Emergency Rollback

If something goes wrong:
```bash
# Stop the problematic service
docker-compose -f docker-compose.prod.yml stop backend

# Restore from previous image
docker-compose -f docker-compose.prod.yml up -d --no-deps backend

# Or full rollback with git
git checkout <previous-version>
make restart-all-prod
```