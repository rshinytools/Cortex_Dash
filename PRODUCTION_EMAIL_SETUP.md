# Production Email Setup Guide

## 🚀 Production Deployment Checklist

### 1. Environment Variables Required

Add these to your production `.env` file:

```bash
# Email Encryption Key (CRITICAL - Keep this secret!)
ENCRYPTION_KEY=SZHqT7JYLsFghGNdnJO5lFjA3XvILUFOHMKoId8NzLE0x1kXq9hR7KfzYDJfFsw=

# Optional: Set if you want to use environment-based SMTP (not recommended)
# The system uses database-driven SMTP configuration which is more flexible
```

### 2. Docker Compose Updates

Both `docker-compose.local-prod.yml` and your production docker-compose files have been updated with:

```yaml
environment:
  - ENCRYPTION_KEY=SZHqT7JYLsFghGNdnJO5lFjA3XvILUFOHMKoId8NzLE0x1kXq9hR7KfzYDJfFsw=
```

This has been added to:
- ✅ Backend service
- ✅ Celery Worker service  
- ✅ Celery Beat service

### 3. Database Migration

The email system tables will be automatically created when the backend starts, but ensure migrations run:

```bash
docker exec cortex_dash-backend-1 alembic upgrade head
```

### 4. Configure SMTP Settings

After deployment, configure your production SMTP:

1. Navigate to: `https://yourdomain.com/admin/email`
2. Enter production SMTP settings:
   - **For GoDaddy (sagarmatha.ai)**:
     - Host: `smtpout.secureserver.net`
     - Port: `587`
     - Username: `admin@sagarmatha.ai`
     - Password: Your GoDaddy email password
     - Use TLS: ✅
   
3. Test the configuration using the Testing tab

### 5. Security Considerations

#### ⚠️ IMPORTANT: Encryption Key

1. **Never commit the real ENCRYPTION_KEY to git**
2. Generate a new key for production:
   ```python
   from cryptography.fernet import Fernet
   import base64
   key = base64.urlsafe_b64encode(Fernet.generate_key()).decode()
   print(key)
   ```

3. Store the key securely:
   - Use environment variables
   - Use a secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.)
   - Keep a secure backup

#### Password Security

- SMTP passwords are encrypted in the database using the ENCRYPTION_KEY
- If you lose the ENCRYPTION_KEY, you'll need to:
  1. Generate a new key
  2. Clear all SMTP passwords
  3. Re-enter passwords in the UI

### 6. Email Templates

Default templates are automatically created for:
- User account creation
- Password reset
- Study creation
- Backup notifications
- System alerts

Customize these at: `https://yourdomain.com/admin/email/templates`

### 7. Production Email Providers

For better deliverability in production, consider:

#### Option A: Keep GoDaddy SMTP
- Simple setup
- Good for low volume (<250 emails/day)
- Use current settings

#### Option B: Use SendGrid/Mailgun (Recommended for scale)
- Better deliverability
- Advanced analytics
- Higher volume support

Example SendGrid settings:
```
Host: smtp.sendgrid.net
Port: 587
Username: apikey
Password: [Your SendGrid API Key]
Use TLS: Yes
```

### 8. Monitoring & Maintenance

#### Email Queue Monitoring
- Check queue status: `https://yourdomain.com/admin/email/queue`
- View sent history: `https://yourdomain.com/admin/email/history`

#### Background Jobs
Celery processes the email queue every 5 minutes. Monitor with:
```bash
# View Celery logs
docker logs cortex_dash-celery-worker-1

# Access Flower UI (Celery monitoring)
http://yourdomain.com:5555
```

### 9. Backup Considerations

The email system stores:
- SMTP configuration (encrypted passwords)
- Email templates
- Email history (audit trail)
- User preferences

Ensure these tables are included in backups:
- `email_settings`
- `email_templates`
- `email_queue`
- `email_history`
- `user_email_preferences`

### 10. Compliance (21 CFR Part 11)

The email system maintains audit trails:
- All emails sent are logged in `email_history`
- Configuration changes are tracked with timestamps and user IDs
- Failed attempts are recorded for security monitoring

### 11. Testing in Production

After deployment:

1. **Send Test Email**:
   ```bash
   curl -X POST "https://yourdomain.com/api/v1/email/test" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"to_email": "test@example.com"}'
   ```

2. **Check Email Queue**:
   ```bash
   curl "https://yourdomain.com/api/v1/email/queue" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **Process Queue Manually**:
   ```bash
   curl -X POST "https://yourdomain.com/api/v1/email/queue/process" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

### 12. Troubleshooting

#### If emails aren't sending:
1. Check Docker logs: `docker logs cortex_dash-backend-1`
2. Verify SMTP settings in database
3. Check Celery worker is running
4. Test SMTP connection from Testing tab
5. Check firewall rules (port 587 or 465)

#### If password decryption fails:
1. Ensure ENCRYPTION_KEY is set in all services
2. Restart all containers after setting key
3. Clear and re-enter SMTP password

### 13. Migration from Development

When moving from development to production:

1. **Generate new ENCRYPTION_KEY** (don't reuse dev key)
2. **Update docker-compose** with new key
3. **Re-enter SMTP password** in production UI
4. **Test thoroughly** before enabling for users

## ✅ Ready for Production

Once all steps are complete, your email system will be:
- Secure (encrypted passwords)
- Scalable (queue-based processing)
- Compliant (full audit trail)
- Monitored (Flower, logs, UI)
- Reliable (retry logic, error handling)