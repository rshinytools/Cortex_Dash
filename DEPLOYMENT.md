# Production Deployment Guide

## Prerequisites

### VM Requirements
- **OS**: Ubuntu 22.04 LTS or similar
- **CPU**: Minimum 4 cores (8 recommended)
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 100GB+ SSD
- **Network**: Public IP with ports 80, 443 open

### Software Requirements
- Docker 24.0+
- Docker Compose 2.20+
- Git

## Quick Start Deployment

### 1. Initial VM Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installations
docker --version
docker compose version
```

### 2. Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/cortex-dash.git
cd cortex-dash
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.prod.template .env.prod

# Generate secure keys
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env.prod
echo "NEXTAUTH_SECRET=$(openssl rand -hex 32)" >> .env.prod
echo "REDIS_PASSWORD=$(openssl rand -hex 20)" >> .env.prod
echo "POSTGRES_PASSWORD=$(openssl rand -hex 20)" >> .env.prod

# Edit configuration
nano .env.prod
# Update:
# - DOMAIN_NAME (your domain)
# - FIRST_SUPERUSER_PASSWORD
# - SSL_EMAIL
# - Any other settings as needed
```

### 4. Setup SSL Certificates

```bash
# Make scripts executable
chmod +x scripts/init-ssl.sh
chmod +x scripts/backup.sh

# Initialize SSL (replace with your domain and email)
sudo ./scripts/init-ssl.sh dashboard.sagarmatha.ai admin@sagarmatha.ai

# For testing, use staging certificates:
# sudo ./scripts/init-ssl.sh dashboard.sagarmatha.ai admin@sagarmatha.ai 1
```

### 5. Build and Start Services

```bash
# Load environment variables
export $(grep -v '^#' .env.prod | xargs)

# Build images
docker compose -f docker-compose.prod.yml build

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

### 6. Initialize Database

```bash
# Run database migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# The superuser is created automatically on first startup
# Login with the credentials from .env.prod
```

### 7. Configure Email Settings

1. Access the dashboard at `https://your-domain.com`
2. Login with superuser credentials
3. Navigate to Admin → Email Settings
4. Configure your SMTP settings:
   - Host: smtpout.secureserver.net (for GoDaddy)
   - Port: 587
   - Username: your-email@domain.com
   - Password: your-email-password
   - Use TLS: Yes

## Management Commands

### Service Management

```bash
# Start services
docker compose -f docker-compose.prod.yml up -d

# Stop services
docker compose -f docker-compose.prod.yml down

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend

# View logs
docker compose -f docker-compose.prod.yml logs -f [service-name]

# Execute command in container
docker compose -f docker-compose.prod.yml exec backend bash
```

### Database Management

```bash
# Create backup manually
docker compose -f docker-compose.prod.yml exec backup /backup.sh

# Restore from backup
docker compose -f docker-compose.prod.yml exec postgres bash
psql -U postgres -d clinical_dashboard < /backups/postgres/backup_TIMESTAMP.sql.gz

# Access database
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d clinical_dashboard
```

### Updates and Deployment

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Run migrations if needed
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Monitoring

### Health Checks

```bash
# Check all services
curl https://your-domain.com/health
curl https://your-domain.com/api/v1/utils/health-check/

# Check individual services
docker compose -f docker-compose.prod.yml ps
```

### Logs

```bash
# Application logs
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend

# Nginx logs
docker compose -f docker-compose.prod.yml exec nginx tail -f /var/log/nginx/cortex_access.log
docker compose -f docker-compose.prod.yml exec nginx tail -f /var/log/nginx/cortex_error.log

# Celery logs
docker compose -f docker-compose.prod.yml logs celery-worker
```

### Celery Monitoring

Access Flower at `http://localhost:5555` (tunneled via SSH):
```bash
ssh -L 5555:localhost:5555 user@your-server
```

## Security Considerations

### Firewall Setup

```bash
# Install UFW
sudo apt install ufw -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSL Certificate Renewal

Certificates auto-renew via the certbot container. To manually renew:

```bash
docker compose -f docker-compose.prod.yml exec certbot certbot renew
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Secrets Management

- **Never commit** `.env.prod` to version control
- Store backups of `.env.prod` securely
- Rotate passwords regularly
- Use strong, unique passwords

## Backup Strategy

### Automated Backups

Backups run daily at 2 AM (configurable in `.env.prod`):
- Database dumps to `/backups/postgres/`
- 30-day retention by default
- Compressed with gzip

### Manual Backup

```bash
# Database backup
docker compose -f docker-compose.prod.yml exec backup /backup.sh

# Full data backup (including uploaded files)
tar -czf cortex_data_$(date +%Y%m%d).tar.gz data/ backups/
```

### Restore Procedure

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Restore database
gunzip -c backups/postgres/backup_TIMESTAMP.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d clinical_dashboard

# Restore data files
tar -xzf cortex_data_TIMESTAMP.tar.gz

# Start services
docker compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   sudo lsof -i :80
   sudo lsof -i :443
   
   # Kill process or change ports in docker-compose.prod.yml
   ```

2. **Database Connection Failed**
   ```bash
   # Check postgres is running
   docker compose -f docker-compose.prod.yml ps postgres
   
   # Check logs
   docker compose -f docker-compose.prod.yml logs postgres
   ```

3. **SSL Certificate Issues**
   ```bash
   # Re-run SSL setup
   sudo ./scripts/init-ssl.sh your-domain.com your-email@domain.com
   
   # Check certificate
   docker compose -f docker-compose.prod.yml exec nginx \
     openssl x509 -in /etc/letsencrypt/live/your-domain/cert.pem -text -noout
   ```

4. **Email Not Sending**
   - Check Email Settings in admin panel
   - Verify SMTP credentials
   - Check Celery worker logs
   - Test connection from admin panel

### Reset Everything

```bash
# Warning: This will delete all data!
docker compose -f docker-compose.prod.yml down -v
rm -rf data/ backups/ certbot/
# Then start from step 3
```

## Performance Tuning

### Environment Variables

Adjust in `.env.prod`:
- `WEB_CONCURRENCY`: Number of worker processes (default: 4)
- `MAX_WORKERS`: Maximum worker threads (default: 4)
- `POSTGRES_MAX_CONNECTIONS`: Database connections (default: 100)

### Resource Limits

Add to `docker-compose.prod.yml` services:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

## Support

- Check logs first: `docker compose -f docker-compose.prod.yml logs`
- Documentation: `/docs` directory
- Issues: GitHub Issues

## Quick Commands Reference

```bash
# Start everything
docker compose -f docker-compose.prod.yml up -d

# Stop everything
docker compose -f docker-compose.prod.yml down

# View all logs
docker compose -f docker-compose.prod.yml logs -f

# Restart backend
docker compose -f docker-compose.prod.yml restart backend

# Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Create backup
docker compose -f docker-compose.prod.yml exec backup /backup.sh

# Access database
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d clinical_dashboard
```