#!/bin/bash
# ABOUTME: Initialize SSL certificates with Let's Encrypt
# ABOUTME: Run this once before starting the production stack

set -e

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo or as root"
    exit 1
fi

# Configuration
DOMAIN=${1:-dashboard.sagarmatha.ai}
EMAIL=${2:-admin@sagarmatha.ai}
STAGING=${3:-0} # Set to 1 for testing with Let's Encrypt staging

echo "================================================"
echo "SSL Certificate Setup for Cortex Dashboard"
echo "================================================"
echo "Domain: ${DOMAIN}"
echo "Email: ${EMAIL}"
echo "Staging: ${STAGING}"
echo ""

# Create required directories
echo "Creating directories..."
mkdir -p certbot/conf
mkdir -p certbot/www

# Check if certificates already exist
if [ -d "certbot/conf/live/${DOMAIN}" ]; then
    echo "Certificates already exist for ${DOMAIN}"
    read -p "Do you want to renew/recreate them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing certificates"
        exit 0
    fi
fi

# Download recommended TLS parameters
echo "Downloading recommended TLS parameters..."
mkdir -p certbot/conf
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > certbot/conf/options-ssl-nginx.conf
curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > certbot/conf/ssl-dhparams.pem

# Create dummy certificate for initial nginx startup
echo "Creating dummy certificate..."
CERT_PATH="certbot/conf/live/${DOMAIN}"
mkdir -p "${CERT_PATH}"
docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    --entrypoint "/bin/sh" \
    certbot/certbot \
    -c "openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout '/etc/letsencrypt/live/${DOMAIN}/privkey.pem' \
        -out '/etc/letsencrypt/live/${DOMAIN}/fullchain.pem' \
        -subj '/CN=localhost'"

# Copy dummy cert for chain
cp "certbot/conf/live/${DOMAIN}/fullchain.pem" "certbot/conf/live/${DOMAIN}/chain.pem"

echo "Starting nginx with dummy certificate..."
docker-compose -f docker-compose.prod.yml up -d nginx

echo "Waiting for nginx to start..."
sleep 5

# Delete dummy certificate
echo "Deleting dummy certificate..."
rm -rf "certbot/conf/live/${DOMAIN}"
rm -rf "certbot/conf/archive/${DOMAIN}"
rm -rf "certbot/conf/renewal/${DOMAIN}.conf"

# Request Let's Encrypt certificate
echo "Requesting Let's Encrypt certificate..."

if [ ${STAGING} -eq 1 ]; then
    STAGING_ARG="--staging"
    echo "Using Let's Encrypt staging environment (for testing)"
else
    STAGING_ARG=""
    echo "Using Let's Encrypt production environment"
fi

docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    --network cortex_dash_cortex_network \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email ${EMAIL} \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    ${STAGING_ARG} \
    -d ${DOMAIN}

# Check if certificate was obtained successfully
if [ $? -eq 0 ]; then
    echo "Certificate obtained successfully!"
    
    # Reload nginx with real certificate
    echo "Reloading nginx with real certificate..."
    docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
    
    echo ""
    echo "================================================"
    echo "SSL setup completed successfully!"
    echo "================================================"
    echo ""
    echo "Your site should now be accessible at:"
    echo "https://${DOMAIN}"
    echo ""
    echo "Certificate will auto-renew via the certbot service"
    echo ""
else
    echo "Failed to obtain certificate!"
    echo "Check the error messages above"
    exit 1
fi