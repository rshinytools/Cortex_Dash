# Email Settings Feature Plan

## Overview
Implement a comprehensive email settings system for the Clinical Dashboard with configurable SMTP settings and templates for various system events.

## Current State Analysis
### Existing Implementation:
- **Email Service**: Basic email sending via `app/utils.py` using `emails` library
- **SMTP Config**: Settings in environment variables (SMTP_HOST, SMTP_PORT, etc.)
- **Templates**: 3 existing MJML templates (new_account, reset_password, test_email)
- **Backup Emails**: Custom email service for backup operations

### Limitations:
- SMTP settings are hardcoded in environment variables
- No UI for configuring email settings
- Limited email templates
- No email queue or retry mechanism
- No email history/audit trail

## Proposed Email System Architecture

### 1. Email Events to Support
#### User Management
- ✅ **Account Created**: When admin creates a new user account
- ✅ **Password Reset**: When user requests password reset
- **Password Changed**: When user successfully changes password
- **Account Activated**: When user activates their account
- **Account Deactivated**: When admin deactivates a user
- **Role Changed**: When user's role is modified

#### Study Management
- **Study Created**: When a new study is created
- **Study Data Uploaded**: When new data is uploaded to a study
- **Study Shared**: When a study is shared with a user
- **Study Deleted**: When a study is deleted
- **Pipeline Completed**: When a data pipeline finishes processing
- **Pipeline Failed**: When a data pipeline fails

#### System Events
- ✅ **Backup Created**: When backup is successfully created
- ✅ **Backup Restored**: When system is restored from backup
- ✅ **Backup Deleted**: When backup is deleted
- **System Maintenance**: Scheduled maintenance notifications
- **Security Alert**: Failed login attempts, suspicious activity
- **Data Export**: When data export is completed

#### Compliance & Audit
- **Audit Report**: Weekly/Monthly audit summaries
- **Compliance Alert**: 21 CFR Part 11 related notifications
- **Data Integrity Check**: Results of scheduled integrity checks
- **Electronic Signature**: When documents are e-signed

### 2. Database Schema

```sql
-- Email configuration table
CREATE TABLE email_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    smtp_host VARCHAR(255) NOT NULL,
    smtp_port INTEGER NOT NULL DEFAULT 587,
    smtp_username VARCHAR(255),
    smtp_password VARCHAR(255), -- Encrypted
    smtp_from_email VARCHAR(255) NOT NULL,
    smtp_from_name VARCHAR(255),
    smtp_use_tls BOOLEAN DEFAULT TRUE,
    smtp_use_ssl BOOLEAN DEFAULT FALSE,
    smtp_timeout INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    test_recipient_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id)
);

-- Email templates table
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_key VARCHAR(100) UNIQUE NOT NULL, -- e.g., 'user_created', 'study_shared'
    template_name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    html_template TEXT NOT NULL,
    plain_text_template TEXT,
    variables JSONB, -- List of available variables
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id)
);

-- Email queue table
CREATE TABLE email_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    subject VARCHAR(500) NOT NULL,
    html_content TEXT NOT NULL,
    plain_text_content TEXT,
    template_id UUID REFERENCES email_templates(id),
    priority INTEGER DEFAULT 5, -- 1-10, 1 being highest
    status VARCHAR(50) DEFAULT 'pending', -- pending, sending, sent, failed
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB, -- Additional context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Email history/audit table
CREATE TABLE email_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID REFERENCES email_queue(id),
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    template_used VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    bounced BOOLEAN DEFAULT FALSE,
    bounce_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email notification preferences per user
CREATE TABLE user_email_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) UNIQUE,
    receive_study_updates BOOLEAN DEFAULT TRUE,
    receive_system_alerts BOOLEAN DEFAULT TRUE,
    receive_backup_notifications BOOLEAN DEFAULT TRUE,
    receive_audit_reports BOOLEAN DEFAULT FALSE,
    receive_marketing BOOLEAN DEFAULT FALSE,
    digest_frequency VARCHAR(50) DEFAULT 'immediate', -- immediate, daily, weekly
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. API Endpoints

```python
# Email Settings Management
GET    /api/v1/email/settings          # Get current email settings
PUT    /api/v1/email/settings          # Update email settings
POST   /api/v1/email/settings/test     # Test email configuration
GET    /api/v1/email/settings/status   # Check email service status

# Email Templates
GET    /api/v1/email/templates         # List all templates
GET    /api/v1/email/templates/{key}   # Get specific template
PUT    /api/v1/email/templates/{key}   # Update template
POST   /api/v1/email/templates/preview # Preview template with sample data
POST   /api/v1/email/templates/reset   # Reset to default template

# Email Queue
GET    /api/v1/email/queue             # List queued emails
POST   /api/v1/email/queue/{id}/retry  # Retry failed email
DELETE /api/v1/email/queue/{id}        # Cancel queued email

# Email History
GET    /api/v1/email/history           # Get email history
GET    /api/v1/email/history/stats     # Get email statistics

# User Preferences
GET    /api/v1/users/{id}/email-preferences    # Get user's email preferences
PUT    /api/v1/users/{id}/email-preferences    # Update preferences
```

### 4. Email Service Architecture

```python
# Core email service structure
class EmailService:
    - load_settings()           # Load from database
    - send_email()              # Send immediate email
    - queue_email()             # Add to queue
    - process_queue()           # Process pending emails (Celery task)
    - retry_failed()            # Retry failed emails
    - validate_smtp()           # Test SMTP connection
    
class EmailTemplateEngine:
    - render_template()         # Render with variables
    - validate_template()       # Check syntax
    - get_available_variables() # List variables per template type
    - preview_template()        # Preview with sample data

class EmailNotificationService:
    - notify_user_created()
    - notify_password_reset()
    - notify_study_created()
    - notify_pipeline_complete()
    - notify_backup_complete()
    # ... other notification methods
```

### 5. UI Components

#### Admin Email Settings Page
- **SMTP Configuration**
  - Server settings (host, port, encryption)
  - Authentication credentials
  - From email/name
  - Test connection button
  - Send test email functionality

- **Template Management**
  - List of all templates
  - Visual template editor with preview
  - Variable insertion helpers
  - Reset to default option
  - A/B testing capabilities

- **Email Queue Monitor**
  - Real-time queue status
  - Failed email management
  - Retry controls
  - Performance metrics

- **Email Analytics Dashboard**
  - Sent/Failed/Pending counts
  - Delivery rate graphs
  - Template performance
  - User engagement metrics

#### User Email Preferences
- Notification categories toggle
- Digest frequency selection
- Unsubscribe options

### 6. Implementation Phases

#### Phase 1: Core Infrastructure (Week 1)
- [ ] Create database tables
- [ ] Build EmailSettings model
- [ ] Create basic CRUD APIs
- [ ] Implement settings encryption

#### Phase 2: Email Service Refactor (Week 1-2)
- [ ] Create centralized EmailService
- [ ] Implement database-based settings
- [ ] Add email queue with Celery
- [ ] Build retry mechanism

#### Phase 3: Template System (Week 2)
- [ ] Create template management APIs
- [ ] Build template rendering engine
- [ ] Convert existing templates
- [ ] Add new event templates

#### Phase 4: Admin UI (Week 3)
- [ ] Build settings configuration page
- [ ] Create template editor
- [ ] Add queue monitor
- [ ] Implement test email feature

#### Phase 5: Event Integration (Week 3-4)
- [ ] Integrate with user creation
- [ ] Add study event notifications
- [ ] Connect pipeline events
- [ ] Update backup notifications

#### Phase 6: Analytics & Monitoring (Week 4)
- [ ] Add email tracking
- [ ] Build analytics dashboard
- [ ] Create audit reports
- [ ] Performance optimization

### 7. Security Considerations

- **Encryption**: SMTP passwords encrypted using Fernet
- **Rate Limiting**: Prevent email bombing
- **SPF/DKIM**: Configuration guidance for deliverability
- **Input Sanitization**: Prevent XSS in templates
- **Audit Trail**: All email operations logged
- **Access Control**: Role-based permissions for settings

### 8. Testing Strategy

- **Unit Tests**: Service methods, template rendering
- **Integration Tests**: SMTP connection, queue processing
- **End-to-End Tests**: Full email flow
- **Load Tests**: Queue performance
- **Security Tests**: Injection prevention

### 9. Migration Plan

1. Deploy new schema alongside existing
2. Migrate existing SMTP settings to database
3. Run both systems in parallel
4. Gradually migrate to new system
5. Deprecate old email code

### 10. Success Metrics

- Email delivery rate > 95%
- Failed email rate < 2%
- Queue processing time < 30 seconds
- User engagement rate > 40%
- Zero security incidents

## Next Steps

1. Review and approve plan with Sagarmatha AI
2. Create detailed technical specifications
3. Set up development environment
4. Begin Phase 1 implementation