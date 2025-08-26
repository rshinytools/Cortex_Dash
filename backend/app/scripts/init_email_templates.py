#!/usr/bin/env python3
"""
Initialize default email templates for the Clinical Dashboard
Run this script after setting up the database to create standard templates
"""

from datetime import datetime
from uuid import uuid4
from sqlmodel import Session, select
from app.core.db import engine
from app.models.email_settings import EmailTemplate


DEFAULT_TEMPLATES = [
    {
        "template_key": "user_created",
        "template_name": "New User Account Created",
        "subject": "Welcome to Clinical Dashboard - Your Account Has Been Created",
        "category": "account",
        "is_system": True,
        "html_template": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }
        .content { background-color: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; border-top: none; }
        .credentials { background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .button { display: inline-block; padding: 12px 30px; background-color: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Clinical Dashboard!</h1>
        </div>
        <div class="content">
            <h2>Hello {{ user_name }},</h2>
            <p>Your account has been successfully created by {{ created_by }}. You now have access to the Clinical Dashboard system.</p>
            
            <div class="credentials">
                <h3>Your Login Credentials:</h3>
                <p><strong>Email:</strong> {{ user_email }}</p>
                <p><strong>Temporary Password:</strong> {{ temp_password }}</p>
                <p><strong>Role:</strong> {{ user_role }}</p>
                <p><strong>Organization:</strong> {{ organization }}</p>
            </div>
            
            <p><strong>Important:</strong> Please change your password upon first login for security purposes.</p>
            
            <a href="{{ login_url }}" class="button">Login to Dashboard</a>
            
            <h3>What You Can Do:</h3>
            <ul>
                <li>Access clinical study data and reports</li>
                <li>View real-time dashboards and analytics</li>
                <li>Export data in various formats</li>
                <li>Collaborate with team members</li>
            </ul>
            
            <div class="footer">
                <p>This is an automated message from the Clinical Dashboard system.</p>
                <p>If you did not request this account or have questions, please contact your administrator.</p>
                <p>© 2024 Clinical Dashboard - Sagarmatha AI. All rights reserved.</p>
            </div>
        </div>
    </div>
</body>
</html>
        """,
        "plain_text_template": """
Welcome to Clinical Dashboard!

Hello {{ user_name }},

Your account has been successfully created by {{ created_by }}. You now have access to the Clinical Dashboard system.

Your Login Credentials:
Email: {{ user_email }}
Temporary Password: {{ temp_password }}
Role: {{ user_role }}
Organization: {{ organization }}

Important: Please change your password upon first login for security purposes.

Login URL: {{ login_url }}

What You Can Do:
- Access clinical study data and reports
- View real-time dashboards and analytics
- Export data in various formats
- Collaborate with team members

This is an automated message from the Clinical Dashboard system.
If you did not request this account or have questions, please contact your administrator.

© 2024 Clinical Dashboard - Sagarmatha AI. All rights reserved.
        """,
        "variables": {
            "user_name": "Full name of the new user",
            "user_email": "Email address of the new user",
            "temp_password": "Temporary password",
            "user_role": "Assigned role",
            "organization": "Organization name",
            "created_by": "Name of the admin who created the account",
            "login_url": "URL to login page"
        }
    },
    {
        "template_key": "password_reset",
        "template_name": "Password Reset Request",
        "subject": "Password Reset Request - Clinical Dashboard",
        "category": "account",
        "is_system": True,
        "html_template": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 30px; border-radius: 10px 10px 0 0; }
        .content { background-color: #ffffff; padding: 30px; border: 1px solid #dee2e6; border-top: none; }
        .button { display: inline-block; padding: 12px 30px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <h2>Hello {{ user_name }},</h2>
            <p>We received a request to reset your password for the Clinical Dashboard.</p>
            
            <p>Click the button below to reset your password:</p>
            
            <a href="{{ reset_url }}" class="button">Reset Password</a>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 5px;">{{ reset_url }}</p>
            
            <div class="warning">
                <strong>⚠️ Important:</strong>
                <ul>
                    <li>This link will expire in {{ expiry_hours }} hours</li>
                    <li>If you didn't request this reset, please ignore this email</li>
                    <li>Your password won't change until you create a new one</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>This is an automated security message from the Clinical Dashboard.</p>
                <p>Request details:</p>
                <p>Time: {{ request_time }}</p>
                <p>IP Address: {{ request_ip }}</p>
                <p>If you did not make this request, please contact your administrator immediately.</p>
            </div>
        </div>
    </div>
</body>
</html>
        """,
        "plain_text_template": """
Password Reset Request

Hello {{ user_name }},

We received a request to reset your password for the Clinical Dashboard.

To reset your password, click the following link:
{{ reset_url }}

Important:
- This link will expire in {{ expiry_hours }} hours
- If you didn't request this reset, please ignore this email
- Your password won't change until you create a new one

Request details:
Time: {{ request_time }}
IP Address: {{ request_ip }}

If you did not make this request, please contact your administrator immediately.

This is an automated security message from the Clinical Dashboard.
        """,
        "variables": {
            "user_name": "User's full name",
            "reset_url": "Password reset URL",
            "expiry_hours": "Hours until link expires",
            "request_time": "Time of reset request",
            "request_ip": "IP address of requester"
        }
    },
    {
        "template_key": "study_created",
        "template_name": "New Study Created",
        "subject": "New Study Created: {{ study_name }}",
        "category": "study",
        "is_system": True,
        "html_template": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #0088FE 0%, #00C49F 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }
        .content { background-color: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; border-top: none; }
        .study-info { background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .button { display: inline-block; padding: 12px 30px; background-color: #0088FE; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Clinical Study Created</h1>
        </div>
        <div class="content">
            <h2>Hello {{ user_name }},</h2>
            <p>A new clinical study has been created in your organization.</p>
            
            <div class="study-info">
                <h3>Study Details:</h3>
                <p><strong>Study Name:</strong> {{ study_name }}</p>
                <p><strong>Protocol Number:</strong> {{ protocol_number }}</p>
                <p><strong>Phase:</strong> {{ study_phase }}</p>
                <p><strong>Sponsor:</strong> {{ sponsor }}</p>
                <p><strong>Created By:</strong> {{ created_by }}</p>
                <p><strong>Creation Date:</strong> {{ creation_date }}</p>
            </div>
            
            <a href="{{ study_url }}" class="button">View Study</a>
            
            <p>You have been granted access to this study with the following permissions:</p>
            <ul>
                {{ permissions_list }}
            </ul>
            
            <p>If you have any questions about this study or your access level, please contact your study administrator.</p>
        </div>
    </div>
</body>
</html>
        """,
        "variables": {
            "user_name": "Recipient's name",
            "study_name": "Name of the study",
            "protocol_number": "Study protocol number",
            "study_phase": "Clinical trial phase",
            "sponsor": "Study sponsor",
            "created_by": "Name of user who created the study",
            "creation_date": "Date study was created",
            "study_url": "URL to access the study",
            "permissions_list": "HTML list of user permissions"
        }
    },
    {
        "template_key": "backup_completed",
        "template_name": "Backup Completed Successfully",
        "subject": "✅ Backup Completed - {{ backup_filename }}",
        "category": "system",
        "is_system": True,
        "html_template": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #28a745; color: white; padding: 30px; border-radius: 10px 10px 0 0; }
        .content { background-color: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; border-top: none; }
        .details { background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Backup Completed Successfully</h1>
        </div>
        <div class="content">
            <p>The system backup has been completed successfully.</p>
            
            <div class="details">
                <h3>Backup Details:</h3>
                <p><strong>Filename:</strong> {{ backup_filename }}</p>
                <p><strong>Size:</strong> {{ backup_size }} MB</p>
                <p><strong>Type:</strong> {{ backup_type }}</p>
                <p><strong>Created At:</strong> {{ created_at }}</p>
                <p><strong>Created By:</strong> {{ created_by }}</p>
                <p><strong>Checksum:</strong> <code style="font-size: 11px;">{{ checksum }}</code></p>
            </div>
            
            <p><strong>Next Steps:</strong></p>
            <ul>
                <li>The backup has been stored securely in the backup directory</li>
                <li>Checksum verification has been completed</li>
                <li>You can download this backup from the admin panel</li>
                <li>This backup will be retained according to the retention policy</li>
            </ul>
            
            <div class="footer">
                <p>This is an automated notification from the Clinical Dashboard Backup System.</p>
                <p>For 21 CFR Part 11 compliance, all backup operations are logged and tracked.</p>
            </div>
        </div>
    </div>
</body>
</html>
        """,
        "variables": {
            "backup_filename": "Name of the backup file",
            "backup_size": "Size in MB",
            "backup_type": "Type of backup (full/database/files)",
            "created_at": "Timestamp of creation",
            "created_by": "User who initiated backup",
            "checksum": "SHA-256 checksum"
        }
    },
    {
        "template_key": "pipeline_completed",
        "template_name": "Data Pipeline Completed",
        "subject": "Pipeline Completed: {{ pipeline_name }}",
        "category": "pipeline",
        "is_system": True,
        "html_template": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }
        .content { background-color: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; border-top: none; }
        .stats { display: flex; justify-content: space-around; background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .stat { text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #667eea; }
        .stat-label { font-size: 12px; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Data Pipeline Completed</h1>
        </div>
        <div class="content">
            <h2>Pipeline Execution Summary</h2>
            <p>The data pipeline <strong>{{ pipeline_name }}</strong> has completed successfully.</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{{ records_processed }}</div>
                    <div class="stat-label">Records Processed</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{{ duration }}</div>
                    <div class="stat-label">Duration</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{{ status }}</div>
                    <div class="stat-label">Status</div>
                </div>
            </div>
            
            <h3>Pipeline Details:</h3>
            <ul>
                <li><strong>Study:</strong> {{ study_name }}</li>
                <li><strong>Start Time:</strong> {{ start_time }}</li>
                <li><strong>End Time:</strong> {{ end_time }}</li>
                <li><strong>Data Source:</strong> {{ data_source }}</li>
                <li><strong>Output Location:</strong> {{ output_location }}</li>
            </ul>
            
            {{ error_section }}
            
            <p>You can view the complete pipeline logs and results in the dashboard.</p>
        </div>
    </div>
</body>
</html>
        """,
        "variables": {
            "pipeline_name": "Name of the pipeline",
            "records_processed": "Number of records processed",
            "duration": "Execution duration",
            "status": "Success/Failed/Warning",
            "study_name": "Associated study",
            "start_time": "Pipeline start time",
            "end_time": "Pipeline end time",
            "data_source": "Data source used",
            "output_location": "Where results are stored",
            "error_section": "HTML section with errors if any"
        }
    }
]


def init_templates():
    """Initialize default email templates"""
    
    with Session(engine) as session:
        created = 0
        skipped = 0
        
        for template_data in DEFAULT_TEMPLATES:
            # Check if template already exists
            statement = select(EmailTemplate).where(
                EmailTemplate.template_key == template_data["template_key"]
            )
            existing = session.exec(statement).first()
            
            if existing:
                print(f"⏭️  Template '{template_data['template_key']}' already exists, skipping...")
                skipped += 1
                continue
            
            # Create new template
            template = EmailTemplate(
                **template_data,
                id=uuid4(),
                is_active=True,
                version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(template)
            print(f"✅ Created template: {template_data['template_key']}")
            created += 1
        
        session.commit()
        
        print(f"\n📧 Email Template Initialization Complete!")
        print(f"   Created: {created}")
        print(f"   Skipped: {skipped}")
        print(f"   Total: {len(DEFAULT_TEMPLATES)}")
        
        return created


if __name__ == "__main__":
    print("🚀 Initializing email templates...")
    init_templates()