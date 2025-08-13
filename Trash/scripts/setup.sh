#!/bin/bash
# ABOUTME: Initial system setup script for Clinical Dashboard Platform
# ABOUTME: Configures the host system, installs dependencies, and prepares for first deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to log messages
log() {
    echo -e "${2:-}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        log "✓ $1" "$GREEN"
    else
        log "✗ $1 failed" "$RED"
        exit 1
    fi
}

# Function to prompt for input
prompt() {
    local var_name=$1
    local prompt_text=$2
    local default_value=${3:-}
    
    if [ -n "$default_value" ]; then
        read -p "$(echo -e ${BLUE}${prompt_text} [${default_value}]: ${NC})" value
        value=${value:-$default_value}
    else
        read -p "$(echo -e ${BLUE}${prompt_text}: ${NC})" value
    fi
    
    eval "$var_name='$value'"
}

# Function to generate secure random string
generate_secret() {
    openssl rand -hex 32
}

log "Clinical Dashboard Platform - Initial Setup" "$GREEN"
log "=========================================" "$GREEN"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   log "Please do not run this script as root. Use sudo where needed." "$RED"
   exit 1
fi

# Step 1: System requirements check
log "Checking system requirements..." "$YELLOW"

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    log "Operating System: $NAME $VERSION"
else
    log "Warning: Cannot determine OS version" "$YELLOW"
fi

# Check required commands
REQUIRED_COMMANDS="docker git curl openssl"
for cmd in $REQUIRED_COMMANDS; do
    if command -v $cmd &> /dev/null; then
        log "✓ $cmd is installed" "$GREEN"
    else
        log "✗ $cmd is not installed" "$RED"
        exit 1
    fi
done

# Step 2: Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log "Installing Docker Compose..." "$YELLOW"
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    check_success "Docker Compose installed"
fi

# Step 3: Create required directories
log "Creating directory structure..." "$YELLOW"

# Create directories with proper permissions
DIRECTORIES=(
    "/var/log/clinical-dashboard"
    "/var/log/clinical-dashboard/deployments"
    "/opt/clinical-dashboard/backups"
    "/opt/clinical-dashboard/data"
    "/opt/clinical-dashboard/ssl"
)

for dir in "${DIRECTORIES[@]}"; do
    sudo mkdir -p "$dir"
    sudo chown $USER:$USER "$dir"
    check_success "Created $dir"
done

# Step 4: Configure environment
log "Configuring environment..." "$YELLOW"

cd "$PROJECT_ROOT"

# Check if .env already exists
if [ -f .env ]; then
    log "Found existing .env file" "$YELLOW"
    prompt OVERWRITE "Do you want to overwrite it? (y/N)" "N"
    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        log "Keeping existing .env file"
    else
        cp .env ".env.backup.$(date +%Y%m%d%H%M%S)"
        log "Backed up existing .env file" "$GREEN"
    fi
else
    OVERWRITE="Y"
fi

if [ "$OVERWRITE" = "y" ] || [ "$OVERWRITE" = "Y" ]; then
    log "Setting up environment configuration..." "$YELLOW"
    
    # Copy template
    cp .env.example .env
    
    # Prompt for configuration values
    prompt DOMAIN "Enter your domain name" "dashboard.example.com"
    prompt PROJECT_NAME "Enter project name" "Clinical Dashboard Platform"
    prompt FIRST_SUPERUSER "Enter admin email" "admin@example.com"
    prompt POSTGRES_DB "Enter database name" "clinical_dashboard"
    prompt POSTGRES_USER "Enter database user" "clinical_user"
    
    # Generate secrets
    log "Generating secure secrets..." "$YELLOW"
    SECRET_KEY=$(generate_secret)
    POSTGRES_PASSWORD=$(generate_secret)
    NEXTAUTH_SECRET=$(generate_secret)
    PHI_ENCRYPTION_KEY=$(generate_secret)
    FIRST_SUPERUSER_PASSWORD=$(generate_secret)
    
    # Update .env file
    sed -i "s|DOMAIN=.*|DOMAIN=$DOMAIN|" .env
    sed -i "s|PROJECT_NAME=.*|PROJECT_NAME=\"$PROJECT_NAME\"|" .env
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
    sed -i "s|FIRST_SUPERUSER=.*|FIRST_SUPERUSER=$FIRST_SUPERUSER|" .env
    sed -i "s|FIRST_SUPERUSER_PASSWORD=.*|FIRST_SUPERUSER_PASSWORD=$FIRST_SUPERUSER_PASSWORD|" .env
    sed -i "s|POSTGRES_DB=.*|POSTGRES_DB=$POSTGRES_DB|" .env
    sed -i "s|POSTGRES_USER=.*|POSTGRES_USER=$POSTGRES_USER|" .env
    sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|" .env
    sed -i "s|NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=$NEXTAUTH_SECRET|" .env
    sed -i "s|PHI_ENCRYPTION_KEY=.*|PHI_ENCRYPTION_KEY=$PHI_ENCRYPTION_KEY|" .env
    sed -i "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=https://$DOMAIN|" .env
    sed -i "s|NEXTAUTH_URL=.*|NEXTAUTH_URL=https://$DOMAIN|" .env
    sed -i "s|BACKEND_CORS_ORIGINS=.*|BACKEND_CORS_ORIGINS=[\"https://$DOMAIN\"]|" .env
    
    check_success "Environment configured"
    
    # Save credentials
    cat > credentials.txt <<EOF
Clinical Dashboard Platform - Initial Credentials
================================================
Domain: https://$DOMAIN
Admin Email: $FIRST_SUPERUSER
Admin Password: $FIRST_SUPERUSER_PASSWORD

Database Name: $POSTGRES_DB
Database User: $POSTGRES_USER
Database Password: $POSTGRES_PASSWORD

IMPORTANT: Save these credentials securely and delete this file!
EOF
    
    chmod 600 credentials.txt
    log "Credentials saved to credentials.txt - SAVE THESE SECURELY!" "$RED"
fi

# Step 5: SSL Certificate setup
log "Setting up SSL certificates..." "$YELLOW"

if [ ! -f "/opt/clinical-dashboard/ssl/cert.pem" ]; then
    prompt SSL_TYPE "Do you have SSL certificates? (y/N)" "N"
    
    if [ "$SSL_TYPE" = "y" ] || [ "$SSL_TYPE" = "Y" ]; then
        prompt CERT_PATH "Enter path to certificate file"
        prompt KEY_PATH "Enter path to private key file"
        
        sudo cp "$CERT_PATH" /opt/clinical-dashboard/ssl/cert.pem
        sudo cp "$KEY_PATH" /opt/clinical-dashboard/ssl/key.pem
        sudo chmod 644 /opt/clinical-dashboard/ssl/cert.pem
        sudo chmod 600 /opt/clinical-dashboard/ssl/key.pem
    else
        log "Generating self-signed certificate for development..." "$YELLOW"
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /opt/clinical-dashboard/ssl/key.pem \
            -out /opt/clinical-dashboard/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
        check_success "Self-signed certificate generated"
        log "WARNING: Using self-signed certificate. Replace with proper SSL certificate for production!" "$RED"
    fi
fi

# Create symlink to SSL directory
ln -sf /opt/clinical-dashboard/ssl "$PROJECT_ROOT/ssl"

# Step 6: Configure firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    log "Configuring firewall..." "$YELLOW"
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    log "Firewall rules added (not enabled automatically)" "$GREEN"
fi

# Step 7: Set up systemd service
log "Setting up systemd service..." "$YELLOW"

sudo tee /etc/systemd/system/clinical-dashboard.service > /dev/null <<EOF
[Unit]
Description=Clinical Dashboard Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_ROOT
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
ExecReload=/usr/bin/docker compose -f docker-compose.prod.yml restart
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable clinical-dashboard.service
check_success "Systemd service configured"

# Step 8: Set up log rotation
log "Configuring log rotation..." "$YELLOW"

sudo tee /etc/logrotate.d/clinical-dashboard > /dev/null <<EOF
/var/log/clinical-dashboard/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $USER $USER
}
EOF

check_success "Log rotation configured"

# Step 9: Create backup cron job
log "Setting up automated backups..." "$YELLOW"

(crontab -l 2>/dev/null; echo "0 2 * * * $SCRIPT_DIR/backup.sh") | crontab -
check_success "Backup cron job created"

# Step 10: Initialize git hooks
log "Setting up git hooks..." "$YELLOW"

cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
# Run tests before commit
echo "Running pre-commit checks..."

# Check for debug code
if grep -r "console.log\|debugger\|pdb.set_trace\|print(" --include="*.py" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" . | grep -v node_modules | grep -v ".git"; then
    echo "Debug code found. Please remove before committing."
    exit 1
fi

# Run linting
cd frontend && npm run lint
cd ../backend && python -m flake8 app/
EOF

chmod +x .git/hooks/pre-commit
check_success "Git hooks configured"

# Step 11: System optimization
log "Applying system optimizations..." "$YELLOW"

# Increase file descriptor limits
if ! grep -q "clinical-dashboard" /etc/security/limits.conf 2>/dev/null; then
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
fi

# Docker daemon configuration
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2"
}
EOF

sudo systemctl restart docker
check_success "System optimizations applied"

# Final summary
log "=========================================" "$GREEN"
log "Setup completed successfully!" "$GREEN"
log "=========================================" "$GREEN"
log ""
log "Next steps:" "$YELLOW"
log "1. Review and update the .env file if needed"
log "2. Replace self-signed SSL certificate with proper certificate"
log "3. Run: ./scripts/deploy.sh to deploy the application"
log "4. Check credentials.txt for admin login (DELETE AFTER SAVING!)"
log ""
log "Useful commands:" "$BLUE"
log "- Start services: sudo systemctl start clinical-dashboard"
log "- Stop services: sudo systemctl stop clinical-dashboard"
log "- View logs: docker compose -f docker-compose.prod.yml logs -f"
log "- Backup database: ./scripts/backup.sh"
log ""

exit 0