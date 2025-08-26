# Email Testing Guide

## 📧 Email Testing Setup

The system is already configured with **Mailcatcher** - a local SMTP server that catches all emails for testing.

### ✅ What's Already Set Up

1. **Mailcatcher Container** - Running on port 1025 (SMTP) and 1080 (Web UI)
2. **SMTP Settings** - Already configured to use Mailcatcher
3. **Email Templates** - 5 templates ready to use
4. **Queue System** - Processing emails automatically

## 🚀 How to Test Emails

### Method 1: Test SMTP Connection (Simplest)

1. **Go to Email Settings**
   - Navigate to: http://localhost:3000/admin/email
   - Click on the "Testing" tab

2. **Send Test Email**
   - Enter your test email address (any email, it won't actually send)
   - Click "Send Test Email"
   - You should see "Test Successful" message

3. **View in Mailcatcher**
   - Open: http://localhost:1080
   - You'll see all test emails here
   - Click any email to view its content

### Method 2: Test Through API

```bash
# Get auth token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@sagarmatha.ai&password=adadad123" | \
  sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')

# Send test email
curl -X POST "http://localhost:8000/api/v1/email/settings/test" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "test_connection": true
  }'
```

### Method 3: Queue Email with Template

```bash
# Queue an email using a template
curl -X POST "http://localhost:8000/api/v1/email/queue" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "newuser@example.com",
    "template_key": "user_created",
    "variables": {
      "user_name": "John Doe",
      "user_email": "john.doe@example.com",
      "temp_password": "TempPass123!",
      "user_role": "Study Manager",
      "organization": "Test Org",
      "created_by": "Admin",
      "login_url": "http://localhost:3000/login"
    }
  }'
```

### Method 4: Send Direct Email

```bash
# Send email directly without template
curl -X POST "http://localhost:8000/api/v1/email/send" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "subject": "Test Email",
    "html_content": "<h1>Hello World</h1><p>This is a test email</p>",
    "plain_content": "Hello World\n\nThis is a test email"
  }'
```

## 📨 Viewing Test Emails

### Mailcatcher Web UI
1. Open browser: http://localhost:1080
2. All emails sent by the system appear here
3. Features:
   - View HTML and plain text versions
   - See email headers
   - Download as .eml file
   - Clear all messages

### Check Email Queue
1. Go to: http://localhost:3000/admin/email/queue
2. See pending, processing, and sent emails
3. Click "Process Queue" to manually trigger sending

### Check Email History
1. Go to: http://localhost:3000/admin/email/history
2. View all sent emails with status
3. Filter by status or search by recipient

## 🔧 Current SMTP Configuration

```json
{
  "smtp_host": "mailcatcher",
  "smtp_port": 1025,
  "smtp_from_email": "noreply@clinical-dashboard.ai",
  "smtp_from_name": "Clinical Dashboard System",
  "smtp_use_tls": false,
  "smtp_use_ssl": false,
  "is_active": true
}
```

## 📝 Available Email Templates

1. **user_created** - Welcome email for new users
2. **password_reset** - Password reset instructions
3. **study_created** - Study creation notification
4. **backup_completed** - Backup success notification
5. **pipeline_completed** - Data pipeline completion

## 🧪 Testing Scenarios

### Test 1: New User Creation
```javascript
// Simulate user creation email
{
  "template_key": "user_created",
  "variables": {
    "user_name": "Test User",
    "user_email": "test@example.com",
    "temp_password": "TempPass123!",
    "user_role": "Researcher",
    "organization": "Test Organization",
    "created_by": "System Admin",
    "login_url": "http://localhost:3000/login"
  }
}
```

### Test 2: Password Reset
```javascript
{
  "template_key": "password_reset",
  "variables": {
    "user_name": "Test User",
    "reset_url": "http://localhost:3000/reset-password?token=abc123",
    "expiry_hours": "24",
    "request_time": "2024-01-26 10:00:00",
    "request_ip": "192.168.1.1"
  }
}
```

### Test 3: Backup Notification
```javascript
{
  "template_key": "backup_completed",
  "variables": {
    "backup_filename": "backup_20240126_100000.zip",
    "backup_size": "125.5",
    "backup_type": "Full System Backup",
    "created_at": "2024-01-26 10:00:00",
    "created_by": "Automated System",
    "checksum": "abc123def456..."
  }
}
```

## 🚨 Troubleshooting

### Emails Not Sending?
1. Check if Mailcatcher is running:
   ```bash
   docker ps | grep mailcatcher
   ```
2. Check email queue: http://localhost:3000/admin/email/queue
3. Check Celery workers:
   ```bash
   docker logs cortex_dash-celery-worker-1 --tail 20
   ```

### Can't See Emails in Mailcatcher?
1. Make sure you're looking at: http://localhost:1080
2. Click "Reload" in Mailcatcher UI
3. Check if emails are in queue (not yet processed)

### Process Queue Button Not Working?
- The endpoint has been added and should work after backend restart
- If still not working, emails are processed automatically every minute by Celery

## 🎯 Quick Test

To quickly test if everything is working:

1. Go to: http://localhost:3000/admin/email
2. Click "Testing" tab
3. Enter any email (e.g., test@test.com)
4. Click "Send Test Email"
5. Check http://localhost:1080 - you should see the test email!

## 📊 Email System Status

- **SMTP**: Connected to Mailcatcher ✅
- **Templates**: 5 templates available ✅
- **Queue**: Processing automatically every minute ✅
- **History**: Tracking all sent emails ✅
- **Mailcatcher UI**: http://localhost:1080 ✅

## Important Notes

- **No Real Emails**: Mailcatcher catches all emails - nothing is sent to real email addresses
- **Perfect for Testing**: Test all email features without worrying about sending real emails
- **Data Persistence**: Emails in Mailcatcher are lost when container restarts
- **Production**: For production, configure real SMTP server (Gmail, SendGrid, AWS SES, etc.)

The email system is fully configured and ready for testing!