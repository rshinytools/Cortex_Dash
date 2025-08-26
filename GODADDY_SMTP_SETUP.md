# GoDaddy SMTP Setup for sagarmatha.ai

## 📧 Quick Setup Guide

### Step 1: Verify Your GoDaddy Email Type

Log into GoDaddy and check which email service you have:
- **Workspace Email** (older, common)
- **Microsoft 365 Email** (newer)
- **cPanel Email** (if using hosting)

### Step 2: SMTP Settings by Type

#### For GoDaddy Workspace Email:
```
SMTP Host: smtpout.secureserver.net
SMTP Port: 587 (or 465 for SSL)
Security: TLS (for port 587) or SSL (for port 465)
Username: your-email@sagarmatha.ai (full email address)
Password: Your email password
```

#### For Microsoft 365 (via GoDaddy):
```
SMTP Host: smtp.office365.com
SMTP Port: 587
Security: STARTTLS/TLS
Username: your-email@sagarmatha.ai
Password: Your email password
```

#### For cPanel Email:
```
SMTP Host: mail.sagarmatha.ai (or your server hostname)
SMTP Port: 587
Security: TLS
Username: your-email@sagarmatha.ai
Password: Your email password
```

### Step 3: Configure in Clinical Dashboard

1. **Navigate to Email Settings**
   ```
   http://localhost:3000/admin/email
   ```

2. **Enter Configuration** (Example for Workspace Email):
   - SMTP Host: `smtpout.secureserver.net`
   - SMTP Port: `587`
   - Username: `noreply@sagarmatha.ai`
   - Password: `[your password]`
   - From Email: `noreply@sagarmatha.ai`
   - From Name: `Sagarmatha AI`
   - Use TLS: ✅ Yes
   - Use SSL: ❌ No
   - Timeout: `30`
   - Max Retries: `3`
   - Retry Delay: `300`

3. **Save Settings**

4. **Test Email**
   - Click on "Testing" tab
   - Enter your email: `amulyabista@yahoo.com`
   - Click "Send Test Email"
   - Check your Yahoo inbox!

## 🚨 Troubleshooting

### If emails don't send:

#### 1. Check Authentication
- Some GoDaddy accounts require full email as username
- Try: `noreply@sagarmatha.ai` (not just `noreply`)

#### 2. Try Alternative Ports
- Port 587 with TLS (recommended)
- Port 465 with SSL (alternative)
- Port 25 (usually blocked, not recommended)

#### 3. Check GoDaddy Email Limits
- Workspace Email: 250 emails per day
- Microsoft 365: 10,000 recipients per day
- Exceeding limits will block sending

#### 4. Verify DNS Settings
Your domain should have these DNS records:
- MX records pointing to GoDaddy mail servers
- SPF record to authorize sending
- Optional: DKIM for better deliverability

### Common Error Messages:

#### "Authentication Failed"
- Double-check username (use full email)
- Verify password is correct
- Check if account is locked

#### "Connection Refused"
- Try different port (587, 465)
- Check firewall settings
- Verify SMTP host is correct

#### "Relay Access Denied"
- Must authenticate with valid GoDaddy email
- Cannot use different "from" domain

## 📊 Testing Checklist

Before going to production:

- [ ] Create dedicated email account (e.g., `noreply@sagarmatha.ai`)
- [ ] Configure SMTP settings in dashboard
- [ ] Send test email to yourself
- [ ] Verify email arrives with correct formatting
- [ ] Test all email templates
- [ ] Check spam folder (adjust if needed)
- [ ] Monitor daily sending limits

## 🔒 Security Best Practices

1. **Use Dedicated Email Account**
   - Create `system@sagarmatha.ai` or `noreply@sagarmatha.ai`
   - Don't use personal email for SMTP

2. **Strong Password**
   - Use complex password for email account
   - Store securely (it's encrypted in database)

3. **Monitor Usage**
   - Check email history regularly
   - Watch for unusual activity

4. **Set up SPF Record**
   Add to DNS to improve deliverability:
   ```
   v=spf1 include:secureserver.net ~all
   ```

## 📝 Example Test Process

1. **First Test with Mailcatcher** (Safe)
   - Keep current settings
   - Test all templates
   - Verify formatting

2. **Switch to GoDaddy SMTP**
   - Update settings as above
   - Test with your own email first

3. **Production Testing**
   - Send to multiple email providers
   - Check spam scores
   - Verify delivery rates

## 💡 Pro Tips

1. **Start with Low Volume**
   - Test thoroughly before bulk sending
   - Build reputation gradually

2. **Use Reply-To Header**
   - Set different reply-to address if needed
   - Helps with user responses

3. **Monitor Bounces**
   - Check email history for failures
   - Clean email lists regularly

4. **Consider Email Service**
   - For high volume, consider SendGrid/Mailgun
   - Better analytics and deliverability

## 📞 GoDaddy Support

If you need help with SMTP settings:
- GoDaddy Support: 1-480-505-8877
- Live Chat: Available 24/7
- Help Article: https://www.godaddy.com/help/server-and-port-settings-for-workspace-email-6949

## ✅ Ready to Go!

Once configured, your Clinical Dashboard will send real emails through your sagarmatha.ai domain!