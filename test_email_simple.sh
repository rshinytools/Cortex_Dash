#!/bin/bash

# Get auth token
TOKEN=$(curl -s -X POST "http://localhost:8000/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@sagarmatha.ai&password=adadad123" | \
  grep -o '"access_token":"[^"]*' | \
  sed 's/"access_token":"//')

echo "Token obtained: ${TOKEN:0:20}..."

# Test email settings endpoint
echo -e "\n1. Testing GET /email/settings (expecting 404 for first run):"
curl -s -X GET "http://localhost:8000/api/v1/email/settings" \
  -H "Authorization: Bearer $TOKEN" | head -c 200

# Create email settings
echo -e "\n\n2. Creating email settings:"
curl -s -X POST "http://localhost:8000/api/v1/email/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "smtp_host": "mailcatcher",
    "smtp_port": 1025,
    "smtp_from_email": "noreply@sagarmatha.ai",
    "smtp_from_name": "Clinical Dashboard",
    "smtp_use_tls": false,
    "smtp_use_ssl": false
  }' | head -c 300

# Test SMTP connection
echo -e "\n\n3. Testing SMTP connection:"
curl -s -X POST "http://localhost:8000/api/v1/email/settings/test" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@sagarmatha.ai",
    "test_connection": true
  }' | head -c 300

echo -e "\n\nTest complete!"