# Deployment Quick Reference Guide

## 🚀 Common Deployment Scenarios

### 1. Regular Updates (Bug Fixes, Small Changes)
```bash
# Zero downtime update
make update-prod

# Or update specific services
make update-backend    # Backend only
make update-frontend   # Frontend only
```

### 2. Adding New Features

#### New Widget
```bash
# Add a single widget
make add-widget WIDGET=metrics_card

# Add all widgets
make seed-widgets
```

#### Database Schema Changes
```bash
# Create migration
make add-migration MSG="add_new_field_to_studies"

# Or just run existing migrations
make run-migrations
```

### 3. Major Updates (Breaking Changes)
```bash
# Full deployment with backup
make deploy-major

# This will:
# 1. Create full backup
# 2. Stop services (downtime!)
# 3. Deploy new version
# 4. Run migrations
# 5. Seed new data
# 6. Health check
```

### 4. Emergency Procedures

#### Quick Rollback
```bash
# Rollback to previous Git version
make rollback

# Or manual rollback
git checkout v1.2.3
make deploy-patch
```

#### Emergency Stop
```bash
make emergency-stop     # Stop all services
make emergency-restart  # Force restart
```

## 📊 Backup Commands

### Create Backups
```bash
make backup-all    # Complete backup (recommended)
make backup-db     # Database only
make backup-files  # Files only
```

### Restore Backups
```bash
# Restore database
make restore-db FILE=backups/db/backup_20240115_120000.sql

# Restore files
make restore-files FILE=files_backup_20240115_120000.tar.gz
```

### Automated Backups
```bash
make schedule-backup        # Daily at 2 AM
make cleanup-old-backups   # Remove >30 days old
```

## 🔍 Monitoring & Debugging

### Health Checks
```bash
make health-check   # Check all services
make prod-stats     # Resource usage
make prod-logs      # View logs
```

### Debug Access
```bash
make debug-backend  # Shell into backend
make debug-db       # PostgreSQL console
make analyze-db     # Database statistics
```

## 📋 Deployment Workflows

### Patch Deployment (5 min, no downtime)
```bash
make deploy-patch
# Includes: backup → update → health check
```

### Minor Update (10 min, no downtime)
```bash
make deploy-minor
# Includes: full backup → update → seed data → health check
```

### Major Update (30 min, with downtime)
```bash
make deploy-major
# Includes: full backup → stop → deploy → migrate → seed → health check
```

## 🎯 Quick Decision Tree

**Which command should I use?**

1. **Code fix only?** → `make update-backend` or `make update-frontend`
2. **New widget/feature?** → `make add-widget WIDGET=name` + `make update-prod`
3. **Database changes?** → `make run-migrations` + `make update-backend`
4. **Major release?** → `make deploy-major` (schedule downtime)
5. **Something broken?** → `make rollback` or `make emergency-restart`

## ⚡ Performance Tips

### Scale Services
```bash
# Add more backend workers
make scale-backend REPLICAS=3

# Check current scale
docker-compose -f docker-compose.prod.yml ps
```

### Clear Caches
```bash
make clear-cache  # Clear Redis cache
```

### Fix Common Issues
```bash
make fix-permissions  # File permission errors
make health-check     # Diagnose problems
```

## 📝 Pre-Deployment Checklist

Before any deployment:
- [ ] Code reviewed and tested
- [ ] Database migrations ready
- [ ] Backup command prepared
- [ ] Downtime window scheduled (if needed)
- [ ] Team notified
- [ ] Rollback plan ready

## 🔐 Security Notes

1. **Always backup before major changes**
2. **Test migrations on staging first**
3. **Keep `.env` files secure**
4. **Rotate secrets regularly**
5. **Monitor logs after deployment**

## 📞 Quick Commands Reference

| Task | Command | Downtime | Time |
|------|---------|----------|------|
| Update backend | `make update-backend` | No | 2 min |
| Update frontend | `make update-frontend` | No | 2 min |
| Add widget | `make add-widget WIDGET=name` | No | 1 min |
| Run migrations | `make run-migrations` | No | 1-5 min |
| Full update | `make update-prod` | No | 5 min |
| Major update | `make deploy-major` | Yes | 30 min |
| Backup all | `make backup-all` | No | 5-10 min |
| Health check | `make health-check` | No | 10 sec |
| View logs | `make prod-logs` | No | - |
| Emergency stop | `make emergency-stop` | Yes | 10 sec |

## 🆘 Troubleshooting

**Backend not responding:**
```bash
make prod-logs-backend
make debug-backend
make emergency-restart
```

**Database issues:**
```bash
make debug-db
make analyze-db
```

**High memory usage:**
```bash
make prod-stats
make scale-backend REPLICAS=1  # Reduce replicas
```

**Permission errors:**
```bash
make fix-permissions
```