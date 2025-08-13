# Docker Services Documentation

This document describes all the Docker containers used in the Clinical Dashboard Platform and their purposes.

## Container Architecture Overview

The platform uses a microservices architecture with the following containers:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│                     cortex_dash-frontend-1                       │
│                         Port: 3000                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                      Backend API (FastAPI)                       │
│                      cortex_dash-backend-1                       │
│                         Port: 8000                               │
└──────┬──────────────┬───────────────┬───────────────┬───────────┘
       │              │               │               │
┌──────┴──────┐ ┌────┴────┐ ┌───────┴───────┐ ┌────┴────────┐
│  PostgreSQL │ │  Redis  │ │ Celery Worker │ │ Celery Beat │
│cortex_dash- │ │cortex_  │ │cortex_dash-   │ │cortex_dash- │
│    db-1     │ │dash-    │ │celery-        │ │celery-      │
│ Port: 5432  │ │redis-1  │ │worker-1       │ │beat-1       │
└─────────────┘ │Port:6379│ └───────────────┘ └─────────────┘
                └─────────┘
```

## Core Services

### 1. **cortex_dash-backend-1** (FastAPI Backend)
- **Purpose**: Main API server handling all business logic
- **Port**: 8000
- **Key Features**:
  - RESTful API endpoints
  - Authentication & authorization
  - Database operations
  - File handling
  - WebSocket support for real-time updates
- **Dependencies**: PostgreSQL, Redis
- **Healthcheck**: HTTP GET /health

### 2. **cortex_dash-frontend-1** (Next.js Frontend)
- **Purpose**: React-based web application UI
- **Port**: 3000
- **Key Features**:
  - Server-side rendering (SSR)
  - Dashboard builder interface
  - Widget rendering
  - Real-time updates
- **Dependencies**: Backend API
- **Build**: Production build with optimizations

### 3. **cortex_dash-db-1** (PostgreSQL Database)
- **Purpose**: Primary data storage
- **Port**: 5432
- **Key Features**:
  - Stores all application data
  - Study configurations
  - User data and permissions
  - Dashboard templates
  - Clinical trial data
- **Volume**: Persistent data storage
- **Version**: PostgreSQL 15+
- **Healthcheck**: pg_isready

### 4. **cortex_dash-redis-1** (Redis Cache)
- **Purpose**: In-memory data store for caching and queuing
- **Port**: 6379
- **Key Features**:
  - Session storage
  - Cache for frequently accessed data
  - Message broker for Celery
  - Real-time pub/sub for WebSocket
- **Persistence**: Optional RDB snapshots
- **Healthcheck**: redis-cli ping

## Background Processing

### 5. **cortex_dash-celery-worker-1** (Celery Worker)
- **Purpose**: Asynchronous task processing
- **Key Tasks**:
  - Data pipeline execution
  - Large file processing
  - Report generation
  - Email sending
  - Data transformations
  - API data fetching
- **Concurrency**: 4 workers by default
- **Queue**: Uses Redis as message broker

### 6. **cortex_dash-celery-beat-1** (Celery Beat Scheduler)
- **Purpose**: Scheduled task management
- **Key Tasks**:
  - Periodic data refreshes
  - Scheduled report generation
  - Cleanup tasks
  - Health monitoring
  - Automated backups
- **Schedule**: Defined in celerybeat-schedule
- **Dependencies**: Redis, Celery Worker

## Development & Monitoring Tools

### 7. **cortex_dash-flower-1** (Celery Monitoring)
- **Purpose**: Web-based tool for monitoring Celery tasks
- **Port**: 5555
- **Features**:
  - Real-time task monitoring
  - Worker status
  - Task history and results
  - Performance metrics
  - Task management (revoke, restart)
- **URL**: http://localhost:5555

### 8. **cortex_dash-adminer-1** (Database Management)
- **Purpose**: Web-based database management interface
- **Port**: 8080
- **Features**:
  - Browse database tables
  - Execute SQL queries
  - Import/export data
  - Database schema visualization
- **Supports**: PostgreSQL, MySQL, SQLite
- **URL**: http://localhost:8080

### 9. **cortex_dash-mailcatcher-1** (Email Testing)
- **Purpose**: Catches emails sent by the application in development
- **Ports**: 
  - SMTP: 1025
  - Web UI: 1080
- **Features**:
  - Intercepts all outgoing emails
  - Web interface to view emails
  - Prevents accidental email sending in dev
- **URL**: http://localhost:1080

### 10. **cortex_dash-prestart-1** (Database Initialization)
- **Purpose**: One-time container for database setup
- **Lifecycle**: Runs once and exits
- **Tasks**:
  - Check database connectivity
  - Run Alembic migrations
  - Create initial admin user
  - Load seed data
- **Exit**: Container stops after completion

## Container Management

### Starting Services
```bash
# Start all services
make up

# Start specific service
docker-compose up -d backend

# Start with rebuild
make restart-all
```

### Viewing Logs
```bash
# All services
make logs

# Specific service
docker logs cortex_dash-backend-1 -f

# Last 100 lines
docker logs cortex_dash-celery-worker-1 --tail 100
```

### Health Checks
```bash
# Check all services
make status

# Individual health
docker ps
docker inspect cortex_dash-backend-1 | grep -i health
```

### Scaling Services
```bash
# Scale Celery workers
docker-compose up -d --scale celery-worker=3
```

## Environment Variables

Each container uses environment variables defined in:
- `.env` - Common variables
- `.env.local` - Local overrides (not in git)

Key variables:
- `POSTGRES_*` - Database connection
- `REDIS_URL` - Redis connection
- `CELERY_*` - Celery configuration
- `SMTP_*` - Email settings
- `FRONTEND_URL` - Frontend URL for CORS

## Networking

All containers are on the same Docker network (`cortex_dash_default`) allowing internal communication using container names as hostnames.

Internal URLs:
- Backend: http://backend:8000
- Database: postgresql://db:5432
- Redis: redis://redis:6379

## Data Persistence

Persistent volumes:
- `postgres_data` - Database files
- `redis_data` - Redis persistence (optional)
- `./data` - Application file uploads

## Security Considerations

1. **Production Deployment**:
   - Change default passwords
   - Use secrets management
   - Enable SSL/TLS
   - Restrict port exposure

2. **Development Tools**:
   - Adminer, Flower, and Mailcatcher should be disabled in production
   - Use proper authentication for monitoring tools

3. **Network Security**:
   - Use Docker networks for isolation
   - Only expose necessary ports
   - Use reverse proxy for SSL termination

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs cortex_dash-backend-1

# Check configuration
docker-compose config

# Rebuild image
docker-compose build backend
```

### Database Connection Issues
```bash
# Test connection
docker exec cortex_dash-backend-1 python -c "from app.core.db import engine; print('Connected!')"

# Check migrations
docker exec cortex_dash-backend-1 alembic current
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Increase resources in docker-compose.yml
# Add under service:
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

## Maintenance

### Backup
```bash
# Database backup
docker exec cortex_dash-db-1 pg_dump -U postgres app > backup.sql

# Full backup
make backup
```

### Updates
```bash
# Update images
docker-compose pull

# Rebuild and restart
make restart-all
```

### Cleanup
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Full cleanup (WARNING: removes data)
make clean
```